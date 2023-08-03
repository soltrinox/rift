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

    async def _run_chat_thread(self, response_stream: TextStream) -> None:
        """
        Run the chat thread. This function is defined as asynchronous to enable it to wait for and process each response
        from the chat asynchronously. It is a recursive function that locks the async call, then processes the "before" part
        of the message and calls itself again with the "after" part of the message.

        :param response_stream: The stream of responses from the chat.
        :type response_stream: TextStream
        """
        # split the shared response stream into two parts around the first occurrence of the character "feeling"  
        before, after = response_stream.split_once("feeling")

        try:
            # acquire an asyncio lock to prevent the response stream from being accessed
            # by multiple threads simultaneously, protecting the integrity of the response data
            async with self.state.response_lock:
                # For each message 'delta' before the keyword, do the following processing
                async for delta in before:
                    # Append the 'delta' text to current '_response_buffer'
                    self._response_buffer += delta
                    # Send progress update after reading each line of the incoming stream
                    await self.send_progress({"response": self._response_buffer})
            # Some breathing space for the agent after processing the 'before' stream
            await asyncio.sleep(0.1)
            # call the function itself but now process the 'after' stream
            await self._run_chat_thread(after)
        except Exception as e:
            # if exception arises, log and move forward. This prevents stalls on unforeseen exceptional cases
            logger.info(f"[_run_chat_thread] caught exception={e}, exiting")

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
