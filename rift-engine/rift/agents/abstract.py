from dataclasses import dataclass
from abc import ABC
from typing import ClassVar
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
    id: int = 0
    server: BaseLspServer

    def __str__(self):
        return f"<{type(self).__name__}> {self.id}"

    async def run(self, params: AgentRunParams) -> AgentRunResult:
        ...

    def cancel(self, msg):
        logger.info(f"{self} cancel run: {msg}")
        if self.task is not None:
            self.task.cancel(msg)

    async def request_input(self) -> ...:
        ...

    async def request_chat(self) -> ...:
        ...

    async def send_progress(self) -> ...:
        ...

    async def send_result(self) -> ...:
        ...
