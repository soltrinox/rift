import uuid
import asyncio
from typing import List, Optional, Any
from dataclasses import dataclass, field
from abc import ABC
from typing import ClassVar, Dict, Literal
from rift.lsp import LspServer as BaseLspServer, rpc_method
from rift.llm.openai_types import Message as ChatMessage
from enum import Enum
from rift.agents.agenttask import AgentTask
import logging
logger = logging.getLogger(__name__)

class Status(Enum):
    running = "running"
    done = "done"
    error = "error"
    accepted = "accepted"
    rejected = "rejected"


@dataclass
class RequestInputRequest:
    msg: str


@dataclass
class RequestInputResponse:
    response: str


@dataclass
class RequestChatRequest:
    messages: List[ChatMessage]


@dataclass
class RequestChatResponse:
    message: ChatMessage  # TODO make this richer


AgentTaskId = str


# @dataclass
# class AgentTask:
#     description: str
#     status: Literal["running", "done", "error"] = "running"
#     subtasks: List[AgentTaskId] = field(default_factory=list)
#     parent: Optional[AgentTaskId] = None
#     id: Optional[str] = None

#     def __post_init__(self):
#         self.id = str(uuid.uuid4())[:8]


@dataclass
class AgentRunParams(ABC):
    agent_id: str

@dataclass
class RunAgentParams:
    agent_type: str
    agent_params: Any
    agent_id: Optional[str]


@dataclass
class AgentProgress:
    agent_type: Optional[str] = None
    agent_id: Optional[str] = None
    tasks: Optional[Dict[str, Any]] = None
    payload: Optional[Any] = None


@dataclass
class AgentRunResult(ABC):
    ...


@dataclass
class AgentState(ABC):
    ...


@dataclass
class Agent:
    """
    Agent base class.

    `agent_type` is defined in the source code.
    `agent_id` a unique identifier generated by convention in the lsp's handler for 'morph/run'
    `state` is a namespace encapsulating all special state for the agent
    `tasks` is a list of `AgentTask`s and is used to report progress
    `server` is a handle to the global language server
    """
    agent_type: str
    server: Optional[BaseLspServer] = None
    state: Optional[AgentState] = None
    agent_id: Optional[str] = None
    tasks: List[AgentTask] = field(default_factory=list)
    task: Optional[AgentTask] = None

    def __str__(self):
        return f"<{self.agent_type}> {self.agent_id}"

    @classmethod
    def create(cls, params: RunAgentParams, *args, **kwargs):
        """
        Factory function which is responsible for constructing the agent's state.
        """
        ...

    async def main(self):
        """
        Called by the LSP server to handle `morph/run`.
        """
        self.task = AgentTask(
            description=self.agent_type,
            task=asyncio.create_task(self.run())
        )

        return await self.task.run()

    async def run(self) -> AgentRunResult:
        ...

    def add_task(self, task: AgentTask):
        self.tasks.append(task)
        return task

    def cancel(self, msg: Optional[str] = None):
        logger.info(f"{self.agent_type} {self.agent_id} cancel run {msg or ''}")
        self.task.cancel()
        for task in self.tasks:
            if task is not None:
                task.cancel()

        self.send_progress()

    async def request_input(self, req: RequestInputRequest) -> asyncio.Future[RequestInputResponse]:
        ...


    async def notify(self, msg: str):
        await self.server.send_update(msg)


    async def request_chat(
        self,
    ) -> ...:
        ...

    async def send_progress(self, payload: Optional[Any] = None, payload_only: bool = False):
        if payload_only:
            tasks = None
        else:
            try:
                tasks = {
                    "task": {"description": self.task.description, "status": self.task.status}, "subtasks": (
                    [{"description": x.description, "status": x.status} for x in self.tasks]
                )
            }
            except Exception as e:
                logger.debug(f"Caught exception: {e}")
                tasks = None

        progress = AgentProgress(
            agent_type=self.agent_type,
            agent_id=self.agent_id,
            tasks=tasks,
            payload=payload,
        )

        await self.server.notify(f"morph/{self.agent_type}_{self.agent_id}_send_progress", progress)

    async def send_result(self) -> ...:
        ...
