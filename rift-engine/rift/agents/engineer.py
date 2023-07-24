import asyncio
import logging
import uuid
from asyncio import Future
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, Optional


import rift.lsp.types as lsp
from rift.agents.abstract import (
    Agent,
    AgentProgress,  # AgentTask,
    AgentRunParams,
    AgentRunResult, 
    AgentState,
    RequestInputRequest,
    RunAgentParams,
    agent,
)
import typer
from pathlib import Path

from rift.agents.agenttask import AgentTask
from rift.llm.abstract import AbstractCodeCompletionProvider, InsertCodeResult
from rift.lsp import LspServer as BaseLspServer
from rift.lsp.document import TextDocumentItem
from rift.server.selection import RangeSet

try:
    import gpt_engineer
    import gpt_engineer.chat_to_files
    import gpt_engineer.db

except ImportError:
    raise Exception("`gpt_engineer` not found. Try `pip install gpt-engineer`")

UPDATES_QUEUE = asyncio.Queue()
INPUT_PROMPT_QUEUE = asyncio.Queue()
INPUT_RESPONSE_QUEUE = asyncio.Queue()
OUTPUT_CHAT_QUEUE = asyncio.Queue()
SEEN = set()

from gpt_engineer.ai import AI, fallback_model
from gpt_engineer.collect import collect_learnings
from gpt_engineer.db import DB, DBs, archive
from gpt_engineer.learning import collect_consent
from gpt_engineer.steps import STEPS
from gpt_engineer.steps import Config as StepsConfig
import threading
import json
import rift.llm.openai_types as openai

logger = logging.getLogger(__name__)

def __popup_input(prompt: str) -> str:
    #sends request for popup
    asyncio.run(INPUT_PROMPT_QUEUE.put(prompt))
    #waits till we get a popup
    while INPUT_RESPONSE_QUEUE.empty():
        pass
    #loads reponse and returns
    resp = asyncio.run(INPUT_RESPONSE_QUEUE.get())
    return resp


gpt_engineer.steps.input = __popup_input

def __popup_chat(prompt: str="NONE", end=""):
    asyncio.run(OUTPUT_CHAT_QUEUE.put(prompt))

gpt_engineer.ai.print = __popup_chat
gpt_engineer.steps.print = __popup_chat


async def _main(
    project_path: str = "/Users/jwd2488/gpt-engineer/benchmark/file_explorer",
    model: str = "gpt-4",
    temperature: float = 0.1,
    steps_config: StepsConfig = StepsConfig.DEFAULT,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    **kwargs,
) -> DBs:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    model = fallback_model(model)
    ai = AI(
        model=model,
        temperature=temperature,
    )

    input_path = Path(project_path).absolute()
    memory_path = input_path / "memory"
    workspace_path = input_path / "workspace"
    archive_path = input_path / "archive"

    dbs = DBs(
        memory=DB(memory_path),
        logs=DB(memory_path / "logs"),
        input=DB(input_path),
        workspace=DB(workspace_path, in_memory_dict={}),  # in_memory_dict={}),
        preprompts=DB(Path(gpt_engineer.__file__).parent / "preprompts"),
        archive=DB(archive_path),
    )

    if steps_config not in [
        StepsConfig.EXECUTE_ONLY,
        StepsConfig.USE_FEEDBACK,
        StepsConfig.EVALUATE,
    ]:
        archive(dbs)

    steps = STEPS[steps_config]

    from concurrent import futures

    with futures.ThreadPoolExecutor(1) as pool:
        for step in steps:
            await asyncio.sleep(0.1)
            messages = await asyncio.get_running_loop().run_in_executor(pool, step, ai, dbs)
            await asyncio.sleep(0.1)
            dbs.logs[step.__name__] = json.dumps(messages)
            items = list(dbs.workspace.in_memory_dict.items())
            if len([x for x in items if x[0] not in SEEN]) > 0:
                await UPDATES_QUEUE.put([x for x in items if x[0] not in SEEN])
                for x in items:
                    if x[0] in SEEN:
                        pass
                    else:
                        SEEN.add(x[0])
            await asyncio.sleep(0.5)


# dataclass for representing the result of the code completion agent run
@dataclass
class EngineerRunResult(AgentRunResult):
    ...


# dataclass for representing the progress of the code completion agent
@dataclass
class EngineerProgress(AgentProgress):
    response: Optional[str] = None
    thoughts: Optional[str] = None
    textDocument: Optional[lsp.TextDocumentIdentifier] = None
    cursor: Optional[lsp.Position] = None
    ranges: Optional[RangeSet] = None


# dataclass for representing the parameters of the code completion agent
@dataclass
class EngineerAgentParams(AgentRunParams):
    textDocument: lsp.TextDocumentIdentifier
    position: Optional[lsp.Position]
    instructionPrompt: Optional[str] = None


@dataclass
class ChatProgress(
    AgentProgress
):  # reports what tasks are active and responsible for reporting new tasks
    response: Optional[str] = None
    done_streaming: bool = False

# dataclass for representing the state of the code completion agent
@dataclass
class EngineerAgentState(AgentState):
    model: AbstractCodeCompletionProvider
    document: lsp.TextDocumentItem
    cursor: lsp.Position
    params: EngineerAgentParams
    messages: list[openai.Message]
    ranges: RangeSet = field(default_factory=RangeSet)
    change_futures: Dict[str, Future] = field(default_factory=dict)



# decorator for creating the code completion agent
@agent(
    agent_description="Generate code following an and ask clarifying questions.",
    display_name="GPT Engineer",
)
@dataclass
class EngineerAgent(Agent):
    state: EngineerAgentState
    agent_type: ClassVar[str] = "engineer"

    @classmethod
    def create(cls, params: EngineerAgentParams, model, server):
        state = EngineerAgentState(
            model=model,
            document=server.documents[params.textDocument.uri],
            cursor=params.position,
            ranges=RangeSet(),
            params=params,
            messages=[openai.Message.assistant("Hello! What can I help you build today?")],

        )
        obj = cls(
            state=state,
            agent_id=params.agent_id,
            server=server,
        )
        def __run_chat_thread():
            print("Started handler thread")
            while True:
                while OUTPUT_CHAT_QUEUE.empty():
                    pass
                toSend = asyncio.run(OUTPUT_CHAT_QUEUE.get());
                print(toSend)
                response = ""
                for delta in toSend:
                    print(delta)
                    response += delta
                    asyncio.run( 
                        obj.send_progress(ChatProgress(response=response))
                        
                    )
                asyncio.run( obj.send_progress(ChatProgress(response=response, done_streaming=True)))
                asyncio.run(obj.send_progress())

        def __run_popup_thread():
            while True:
                while INPUT_PROMPT_QUEUE.empty():
                    pass
                prompt = asyncio.run(INPUT_PROMPT_QUEUE.get())
                asyncio.run(obj.send_progress())
                response = asyncio.run(obj.request_input(
                    RequestInputRequest(
                        msg=prompt,
                        place_holder="Write your input here.",
                    )
                ))
                asyncio.run(INPUT_RESPONSE_QUEUE.put(response))

        threading.Thread(target=__run_popup_thread).start()
        threading.Thread(target=__run_chat_thread).start()


        return obj
    

    async def run(self) -> AgentRunResult:  # main entry point
        await self.send_progress()
        from asyncio import Lock

        response_lock = Lock()        
        #instructionPrompt = self.state.params.instructionPrompt or (
        #    await self.request_input(
        #        RequestInputRequest(
        #            msg="Describe what you want me to implement",
        #            place_holder="Please write me a game of pong in python",
        #        )
        #    )
        #)

        self.server.register_change_callback(self.on_change, self.state.document.uri)
        print("Create task")
        response = ""
        
        await _main()
        print("STARTED")






        async def generate_explanation():
            all_deltas = []

            if stream.thoughts is not None:
                async for delta in stream.thoughts:
                    all_deltas.append(delta)
                    await asyncio.sleep(0.01)

            await self.send_progress()
            return "".join(all_deltas)

        # function to asynchronously generate the code
        async def generate_code():
            try:
                all_deltas = []
                async for delta in stream.code:
                    all_deltas.append(delta)
                    assert len(delta) > 0
                    attempts = 10
                    while True:
                        if attempts <= 0:
                            logger.error(f"too many edit attempts for '{delta}' dropped")
                            return
                        attempts -= 1
                        cf = asyncio.get_running_loop().create_future()
                        self.state.change_futures[delta] = cf
                        x = await self.server.apply_insert_text(
                            self.state.document.uri,
                            self.state.cursor,
                            delta,
                            self.state.document.version,
                        )
                        if x.applied == False:
                            logger.debug(f"edit '{delta}' failed, retrying")
                            await asyncio.sleep(0.1)
                            continue
                        try:
                            await asyncio.wait_for(cf, timeout=2)
                            break
                        except asyncio.TimeoutError:
                            # [todo] this happens when an edit occured that clobbered this, try redoing.
                            logger.error(f"timeout waiting for change '{delta}', retry the edit")
                        finally:
                            del self.state.change_futures[delta]
                            pass
                    with lsp.setdoc(self.state.document):
                        added_range = lsp.Range.of_pos(self.state.cursor, len(delta))
                        self.state.cursor += len(delta)
                        self.state.ranges.add(added_range)
                all_text = "".join(all_deltas)
                logger.info(f"{self} finished streaming {len(all_text)} characters")
                await self.send_progress()
                return all_text

            except asyncio.CancelledError as e:
                logger.info(f"{self} cancelled: {e}")
                await self.cancel()
                return EngineerRunResult()

            except Exception as e:
                logger.exception("worker failed")
                # self.status = "error"
                return EngineerRunResult()

            finally:
                self.server.change_callbacks[self.state.document.uri].discard(self.on_change)
                await self.send_progress(
                    EngineerProgress(
                        response=None,
                        textDocument=self.state.document,
                        cursor=self.state.cursor,
                        ranges=self.state.ranges,
                    )
                )

        await self.send_progress(
            EngineerProgress(
                response=None,
                textDocument=self.state.document,
                cursor=self.state.cursor,
                ranges=self.state.ranges,
            )
        )

        code_task = self.add_task(AgentTask("Generate code", generate_code))

        await self.send_progress(
            EngineerProgress(
                response=None,
                textDocument=self.state.document,
                cursor=self.state.cursor,
                ranges=self.state.ranges,
            )
        )

        explanation_task = self.add_task(AgentTask("Explain code edit", generate_explanation))

        await self.send_progress(
            EngineerProgress(
                response=None,
                textDocument=self.state.document,
                cursor=self.state.cursor,
                ranges=self.state.ranges,
            )
        )

        await code_task.run()
        await self.send_progress()

        explanation = await explanation_task.run()
        await self.send_progress()

        await self.send_update(explanation)

        return EngineerRunResult()

    async def on_change(
        self,
        *,
        before: lsp.TextDocumentItem,
        after: lsp.TextDocumentItem,
        changes: lsp.DidChangeTextDocumentParams,
    ):
        if self.task.status != "running":
            return
        """
        [todo]
        When a change happens:
        1. if the change is before our 'working area', then we stop the completion request and run again.
        2. if the change is in our 'working area', then the user is correcting something that
        3. if the change is after our 'working area', then just keep going.
        4. if _we_ caused the change, then just keep going.
        """
        assert changes.textDocument.uri == self.state.document.uri
        self.state.document = before
        for c in changes.contentChanges:
            fut = self.state.change_futures.get(c.text)
            if fut is not None:
                # we caused this change
                fut.set_result(None)
            else:
                # someone else caused this change
                # [todo], in the below examples, we shouldn't cancel, but instead figure out what changed and restart the insertions with the new information.
                with lsp.setdoc(self.state.document):
                    self.state.ranges.apply_edit(c)
                if c.range is None:
                    await self.cancel("the whole document got replaced")
                else:
                    if c.range.end <= self.state.cursor:
                        # some text was changed before our cursor
                        if c.range.end.line < self.state.cursor.line:
                            # the change is occurring on lines strictly above us
                            # so we can adjust the number of lines
                            lines_to_add = (
                                c.text.count("\n") + c.range.start.line - c.range.end.line
                            )
                            self.state.cursor += (lines_to_add, 0)
                        else:
                            # self.cancel("someone is editing on the same line as us")
                            pass  # temporarily disabled
                    elif self.state.cursor in c.range:
                        await self.cancel("someone is editing the same text as us")

        self.state.document = after

    async def send_result(self, result):
        ...  # unreachable

    async def accept(self):
        logger.info(f"{self} user accepted result")
        if self.task.status not in ["error", "done"]:
            logger.error(f"cannot accept status {self.task.status}")
            return
        # self.status = "done"
        await self.send_progress(
            payload="accepted",
            payload_only=True,
        )

    async def reject(self):
        # [todo] in this case we need to revert all of the changes that we made.
        logger.info(f"{self} user rejected result")
        # self.status = "done"
        with lsp.setdoc(self.state.document):
            if self.state.ranges.is_empty:
                logger.error("no ranges to reject")
            else:
                edit = lsp.TextEdit(self.state.ranges.cover(), "")
                params = lsp.ApplyWorkspaceEditParams(
                    edit=lsp.WorkspaceEdit(
                        documentChanges=[
                            lsp.TextDocumentEdit(
                                textDocument=self.state.document.id,
                                edits=[edit],
                            )
                        ]
                    )
                )
                x = await self.server.apply_workspace_edit(params)
                if not x.applied:
                    logger.error("failed to apply rejection edit")
            await self.send_progress(
                payload="rejected",
                payload_only=True,
            )
