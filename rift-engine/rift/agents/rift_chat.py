import asyncio
import logging
import uuid
from asyncio import Future
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, Optional, List

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
    RequestChatRequest,
)
import rift.agents.abstract as agents
import rift.llm.openai_types as openai
from rift.agents.agenttask import AgentTask
from rift.llm.abstract import (
    AbstractCodeCompletionProvider,
    InsertCodeResult,
    AbstractChatCompletionProvider,
)
from rift.lsp import LspServer as BaseLspServer
from rift.lsp.document import TextDocumentItem
from rift.server.selection import RangeSet
from rift.agents.agenttask import AgentTask

logger = logging.getLogger(__name__)


@dataclass
class ChatRunResult(AgentRunResult):
    ...


@dataclass
class ChatAgentParams(AgentRunParams):
    textDocument: lsp.TextDocumentIdentifier
    position: Optional[lsp.Position]


@dataclass
class ChatProgress(
    AgentProgress
):  # reports what tasks are active and responsible for reporting new tasks
    response: Optional[str] = None
    done_streaming: bool = False


@dataclass
class ChatAgentState(AgentState):
    model: AbstractChatCompletionProvider
    messages: list[openai.Message]
    document: lsp.TextDocumentItem
    params: ChatAgentParams


@agent(
    agent_description="Ask questions about your code.",
    display_name="Rift Chat",
)
@dataclass
class ChatAgent(Agent):
    state: ChatAgentState
    agent_type: ClassVar[str] = "rift_chat"

    @classmethod
    def create(cls, params: ChatAgentParams, model, server):
        state = ChatAgentState(
            model=model,
            messages=[openai.Message.assistant("Hello! How can I help you today?")],
            document=server.documents[params.textDocument.uri],
            params=params,
        )
        obj = cls(
            state=state,
            agent_id=params.agent_id,
            server=server,
        )
        return obj

    async def run(self) -> AgentRunResult:
        logger.info(f"[{self.agent_type}] starting ChatAgent.run()")
        from asyncio import Lock

        response_lock = Lock()

        async def get_user_response() -> str:
            logger.info("getting user response")
            return await self.request_chat(RequestChatRequest(messages=self.state.messages))

        async def generate_response(user_response: str):
            response = ""
            doc_text = self.state.document.text

            stream = await self.state.model.run_chat(
                doc_text, self.state.messages, user_response, cursor_offset=None
            )
            async for delta in stream.text:
                response += delta
                async with response_lock:
                    await self.send_progress(ChatProgress(response=response))
            await self.send_progress(ChatProgress(response=response, done_streaming=True))
            logger.info(f"{self} finished streaming response.")
            return response

        while True:
            logger.info("entering loop")
            get_user_response_task = AgentTask("Get user response", get_user_response)
            logger.info("created get_user_response_task")
            sentinel_f = asyncio.get_running_loop().create_future()

            async def generate_response_task_args():
                return [await sentinel_f]

            logger.info("created future")
            generate_response_task = AgentTask(
                "Generate response", generate_response, args=generate_response_task_args
            )
            self.set_tasks([get_user_response_task, generate_response_task])
            await self.send_progress()
            user_response_task = asyncio.create_task(get_user_response_task.run())
            user_response_task.add_done_callback(lambda f: sentinel_f.set_result(f.result()))
            logger.info("got user response task future")
            await user_response_task
            await self.send_progress()
            assistant_response = await generate_response_task.run()

            await self.send_progress()

            async with response_lock:
                self.state.messages.append(openai.Message.assistant(content=assistant_response))

            await self.send_progress()
