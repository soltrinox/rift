import asyncio
from dataclasses import dataclass, field
import logging
from typing import ClassVar, Optional, List
from typing import Literal
from rift.lsp import LspServer as BaseLspServer, rpc_method
from rift.rpc import RpcServerStatus
import rift.lsp.types as lsp
from rift.llm.abstract import (
    AbstractCodeCompletionProvider,
    AbstractChatCompletionProvider,
)
from rift.llm.create import ModelConfig
from rift.server.agent import *
from rift.server.selection import RangeSet
from rift.llm.openai_types import Message

logger = logging.getLogger(__name__)


@dataclass
class RunChatParams:
    message: str
    messages: List[Message]
    position: Optional[lsp.Position]
    textDocument: lsp.TextDocumentIdentifier


ChatAgentLogs = AgentLogs


@dataclass
class AgentProgress:
    id: int
    textDocument: lsp.TextDocumentIdentifier
    status: Literal["running", "done", "error"]
    log: Optional[AgentLogs] = field(default=None)
    ranges: Optional[RangeSet] = field(default=None)
    cursor: Optional[lsp.Position] = field(default=None)


class LspLogHandler(logging.Handler):
    def __init__(self, server: "LspServer"):
        super().__init__()
        self.server = server
        self.tasks: set[asyncio.Task] = set()

    def emit(self, record: logging.LogRecord) -> None:
        if self.server.status != RpcServerStatus.running:
            return
        t_map = {
            logging.DEBUG: 4,
            logging.INFO: 3,
            logging.WARNING: 2,
            logging.ERROR: 1,
        }
        level = t_map.get(record.levelno, 4)
        if level > 3:
            return
        t = asyncio.create_task(
            self.server.notify(
                "window/logMessage",
                {
                    "type": level,
                    "message": self.format(record),
                },
            )
        )
        self.tasks.add(t)
        t.add_done_callback(self.tasks.discard)


class ChatAgent:
    count: ClassVar[int] = 0
    id: int
    cfg: RunChatParams
    running: bool
    server: "LspServer"
    change_futures: dict[str, asyncio.Future[None]]
    cursor: Optional[lsp.Position]
    """ The position of the cursor (where text will be inserted next). This position is changed if other edits occur above the cursor. """
    task: Optional[asyncio.Task]
    subtasks: set[asyncio.Task]

    @property
    def uri(self):
        return self.cfg.textDocument.uri

    def __str__(self):
        return f"<ChatAgent {self.id}>"

    def __init__(
        self,
        cfg: RunChatParams,
        model: AbstractChatCompletionProvider,
        server: "LspServer",
    ):
        ChatAgent.count += 1
        self.model = model
        self.id = Agent.count
        self.cfg = cfg
        self.server = server
        self.running = False
        self.change_futures = {}
        self.cursor = cfg.position
        self.document = server.documents[self.cfg.textDocument.uri]
        self.task = None
        self.subtasks = set()

    def cancel(self, msg):
        logger.info(f"{self} cancel run: {msg}")
        if self.task is not None:
            self.task.cancel(msg)

    async def run(self):
        self.task = asyncio.create_task(self.worker())
        self.running = True
        try:
            return await self.task
        except asyncio.CancelledError as e:
            logger.info(f"{self} run task got cancelled")
            return f"I stopped! {e}"
        finally:
            self.running = False

    async def send_progress(
        self,
        response: str = "",
        logs: Optional[ChatAgentLogs] = None,
        done: bool = False,
    ):
        await self.server.send_chat_agent_progress(
            self.id,
            response=response,
            log=logs,
            done=done,
            # textDocument=to_text_document_id(self.document),
            # cursor=self.cursor,
            # status="running" if self.running else "done",
        )

    async def worker(self):
        response = ""
        from asyncio import Lock

        response_lock = Lock()
        assert self.running
        async with response_lock:
            await self.send_progress(response)
        doc_text = self.document.text
        pos = self.cursor
        offset = None if pos is None else self.document.position_to_offset(pos)

        stream = await self.model.run_chat(doc_text, self.cfg.messages, self.cfg.message, offset)

        async for delta in stream.text:
            response += delta
            async with response_lock:
                await self.send_progress(response)
        logger.info(f"{self} finished streaming response.")

        self.running = False
        async with response_lock:
            await self.send_progress(response, done=True)


@dataclass
class ChatAgentProgress:
    id: int
    response: str = ""
    log: Optional[AgentLogs] = field(default=None)
    done: bool = False


@dataclass
class RunAgentResult:
    id: int


@dataclass
class RunAgentSyncResult:
    id: int
    text: str


class LspServer(BaseLspServer):
    active_agents: dict[int, Agent]
    active_chat_agents: dict[int, asyncio.Task]
    model_config: ModelConfig
    completions_model: Optional[AbstractCodeCompletionProvider] = None
    chat_model: Optional[AbstractChatCompletionProvider] = None

    def __init__(self, transport):
        super().__init__(transport)
        self.model_config = ModelConfig.default()
        self.capabilities.textDocumentSync = lsp.TextDocumentSyncOptions(
            openClose=True,
            change=lsp.TextDocumentSyncKind.incremental,
        )
        self.active_agents = {}
        self.active_chat_agents = {}
        self._loading_task = None
        self._chat_loading_task = None
        self.logger = logging.getLogger(f"rift")
        self.logger.addHandler(LspLogHandler(self))

    @rpc_method("workspace/didChangeConfiguration")
    async def on_workspace_did_change_configuration(self, params: lsp.DidChangeConfigurationParams):
        logger.info("workspace/didChangeConfiguration")
        await self.get_config()

    async def get_config(self):
        """This should be called whenever the user changes the model config settings.

        It should also be called immediately after initialisation."""
        if self._loading_task is not None:
            idx = getattr(self, "_loading_idx", 0) + 1
            logger.debug(f"Queue of set_model_config tasks: {idx}")
            self._loading_idx = idx
            self._loading_task.cancel()
            # give user typing in config some time to settle down
            await asyncio.sleep(1)
            try:
                await self._loading_task
            except (asyncio.CancelledError, TypeError):
                pass
            if self._loading_idx != idx:
                logger.debug(f"loading task {idx} was cancelled, but a new one was started")
                return
            # only the most recent request will make it here.
        settings = await self.get_workspace_configuration(section="rift")
        if not isinstance(settings, list) or len(settings) != 1:
            raise RuntimeError(f"Invalid settings:\n{settings}\nExpected a list of dictionaries.")
        settings = settings[0]
        config = ModelConfig.parse_obj(settings)
        if self.chat_model and self.completions_model and self.model_config == config:
            logger.debug("config unchanged")
            return
        self.model_config = config
        logger.info(f"{self} recieved model config {config}")
        for k, h in self.active_agents.items():
            h.cancel("config changed")
        self.completions_model = config.create_completions()
        self.chat_model = config.create_chat()

        self._loading_task = asyncio.gather(
            self.completions_model.load(),
            self.chat_model.load(),
        )
        try:
            await self._loading_task
        except asyncio.CancelledError:
            logger.debug("loading cancelled")
        else:
            logger.info(f"{self} finished loading")
        finally:
            self._loading_task = None

    async def send_agent_progress(
        self,
        id: int,
        textDocument: lsp.TextDocumentIdentifier,
        log: Optional[AgentLogs] = None,
        cursor: Optional[lsp.Position] = None,
        ranges: Optional[RangeSet] = None,
        status: Literal["running", "done", "error"] = "running",
    ):
        progress = AgentProgress(
            id=id,
            textDocument=textDocument,
            log=log,
            cursor=cursor,
            status=status,
            ranges=ranges,
        )
        await self.notify("morph/progress", progress)

    async def send_chat_agent_progress(
        self,
        id: int,
        response: str,
        log: Optional[ChatAgentLogs] = None,
        done: bool = False,
        # textDocument: lsp.TextDocumentIdentifier,
        # log: Optional[AgentLogs] = None,
        # cursor: Optional[lsp.Position] = None,
        # status: Literal["running", "done", "error"] = "running",
    ):
        progress = ChatAgentProgress(
            # id=id, textDocument=textDocument, log=log, cursor=cursor, status=status
            id=id,
            response=response,
            log=log,
            done=done,
        )
        await self.notify("morph/chat_progress", progress)

    async def ensure_completions_model(self):
        if self.completions_model is None:
            await self.get_config()
        assert self.completions_model is not None
        return self.completions_model

    async def ensure_chat_model(self):
        if self.chat_model is None:
            await self.get_config()
        assert self.chat_model is not None
        return self.chat_model

    @rpc_method("morph/run_agent")
    async def on_run_agent(self, params: RunAgentParams):
        model = await self.ensure_completions_model()
        try:
            agent = Agent(params, model=model, server=self)
        except LookupError:
            # [hack] wait a bit for textDocumentChanged notification to come in
            logger.debug("request too early: waiting for textDocumentChanged notification")
            await asyncio.sleep(3)
            agent = Agent(params, model=model, server=self)
        logger.debug(f"starting agent {agent.id}")
        # agent holds a reference to worker task
        agent.start()
        self.active_agents[agent.id] = agent
        return RunAgentResult(id=agent.id)

    @rpc_method("morph/run_chat")
    async def on_run_chat(self, params: RunChatParams):
        chat = await self.ensure_chat_model()
        chat_agent = ChatAgent(params, model=chat, server=self)
        logger.debug(f"starting chat agent {chat_agent.id}")
        task = asyncio.create_task(chat_agent.run())
        self.active_chat_agents[chat_agent.id] = task

    @rpc_method("morph/cancel")
    async def on_cancel(self, params: AgentIdParams):
        agent = self.active_agents.get(params.id)
        if agent is not None:
            agent.cancel()

    @rpc_method("morph/accept")
    async def on_accept(self, params: AgentIdParams):
        agent = self.active_agents.get(params.id)
        if agent is not None:
            await agent.accept()
            self.active_agents.pop(params.id, None)

    @rpc_method("morph/reject")
    async def on_reject(self, params: AgentIdParams):
        agent = self.active_agents.get(params.id)
        if agent is not None:
            await agent.reject()
            self.active_agents.pop(params.id, None)
        else:
            logger.error(f"no agent with id {params.id}")

    @rpc_method("hello_world")
    def on_hello(self, params):
        logger.debug("hello world")
        return "hello world"
