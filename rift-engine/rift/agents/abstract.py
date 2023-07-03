from dataclasses import dataclass
from abc import ABC


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

    async def run(self, params: AgentRunParams) -> AgentRunResult:
        ...

    async def request_input(self) -> ...:
        ...

    async def report_progress(self) -> ...:
        ...

    async def report_result(self) -> ...:
        ...


class MockAgent(Agent):
    def run(self):
        ...
