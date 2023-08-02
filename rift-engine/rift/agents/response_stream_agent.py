import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

import rift.agents.abstract as agent
import rift.llm.openai_types as openai
from rift.util.TextStream import TextStream

logger = logging.getLogger(__name__)

class ResponseStreamAgentState(agent.AgentState):
    """
    A subclass of AgentState for the ResponseStreamAgent.
    """

    def __init__(self, params: agent.AgentParams, messages: list[openai.Message]):
        super().__init__(params, messages)
        self.response_lock = asyncio.Lock()

class ResponseStreamAgent(agent.Agent, ABC):
    """
    An abstract class that implements a response_stream, a _response_buffer, and synchronous wrappers.
    """

    @abstractmethod
    async def _run_chat_thread(self, response_stream):
        """
        Run the chat thread.
        :param response_stream: The stream of responses from the chat.
        """
        pass

    @abstractmethod
    async def run(self) -> Any:
        """
        Run the agent.
        :return: The result of running the agent.
        """
        pass

    def __init__(self, state: ResponseStreamAgentState, agent_id: str, server):
        super().__init__(state, agent_id, server)
        self._response_buffer = ""
        self.response_stream = TextStream()
