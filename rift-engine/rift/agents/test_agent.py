"""
This module provides a minimal implementation of the Agent API defined in rift.agents.abstract.
"""

from dataclasses import dataclass
from typing import Optional, ClassVar, Any

import rift.llm.openai_types as openai
from rift.agents.abstract import Agent, AgentState, RequestChatRequest, AgentParams
from rift.lsp.types import TextDocumentIdentifier


@dataclass(frozen=True)
class TestAgentParams(AgentParams):
    textDocument: TextDocumentIdentifier
    instructionPrompt: Optional[str] = None


@dataclass(frozen=True)
class TestAgentState(AgentState):
    params: TestAgentParams
    messages: list[openai.Message]


"""uncomment this to register the agent and access it from the Rift extension"""
# @agent(
#     agent_description="Test agent for testing purposes",
#     display_name="Test Agent"
# )


@dataclass
class TestAgent(Agent):
    """
    TestAgent is a minimal implementation of the Agent API.
    It is used for testing purposes.
    """

    state: Optional[TestAgentState] = None
    agent_type: str = "test_agent"
    params_cls: ClassVar[Any] = TestAgentParams

    async def run(self):
        # Send an initial update
        await self.send_update("test")

        # Enter a loop to continuously interact with the user
        while True:
            # Request a chat response from the user
            user_response_t = self.add_task(
                "get user response", self.request_chat, [RequestChatRequest(self.state.messages)]
            )

            # Send a progress update
            await self.send_progress()

            # Wait for the user's response
            user_response = await user_response_t.run()

            # Append the user's response to the state's messages
            self.state.messages.append(openai.Message.user(user_response))

            # Append a test response from the assistant to the state's messages
            self.state.messages.append(openai.Message.assistant("test"))

    @classmethod
    async def create(cls, params: TestAgentParams, server):
        # Convert the parameters to a TestAgentParams object

        # Create the initial state
        state = TestAgentState(
            params=params,
            messages=[openai.Message.assistant("test")],
        )

        # Create the TestAgent object
        obj = cls(
            state=state,
            agent_id=params.agent_id,
            server=server,
        )

        # Return the TestAgent object
        return obj
