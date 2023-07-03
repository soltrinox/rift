import asyncio
from dataclasses import dataclass
from abc import ABC
from typing import ClassVar, Dict
from rift.lsp import LspServer as BaseLspServer, rpc_method


@dataclass
class AgentTask(ABC):
    ...


@dataclass
class AgentRunParams(ABC):
    ...


@dataclass
class AgentRunResult(ABC):
    ...


@dataclass
class AgentState(ABC):
    ...


@dataclass
class Agent:
    state: AgentState
    tasks: Dict[str, AgentTask]
    server: BaseLspServer
    id: int
    active_task_id: Optional[str] = None

    @property
    def task(self):
        if self.active_task_id is None:
            return None
        else:
            return self.tasks.get(self.active_task_id)

    def __str__(self):
        return f"<{type(self).__name__}> {self.id}"

    async def run(self, params: AgentRunParams) -> AgentRunResult:
        ...

    def cancel(self, msg):
        logger.info(f"{self} cancel run: {msg}")
        # if self.task is not None:
        #     self.task.cancel(msg)
        for _, task in tasks.items():
            if task is not None:
                task.cancel()

    async def request_input(self, msg: str) -> asyncio.Task[str]:
        """
        sends a message to the frontend and returns a future to the response
        """
        request_input_id: int = get_id()
        t = Task(..., request_input_id: int) # t can be notified when the LspServer receives a response with notifyId = request_input_id
        # t needs to be placed into a Dict[str, Task] owned by the server
        # server listens on one of its rpc methods to set the result of the task
        return t

    async def request_chat(self) -> ...: # don't have a way to send a message back, unless if the request_chat_callback attaches another callback
        ...

    async def send_progress(self) -> ...:
        ...

    async def send_result(self) -> ...:
        ...
