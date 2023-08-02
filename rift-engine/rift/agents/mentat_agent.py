import re
from concurrent import futures
import time
from dataclasses import dataclass, field
from typing import ClassVar, Optional, Type
import asyncio

import logging

logger = logging.getLogger(__name__)

import rift.agents.abstract as agent
import rift.llm.openai_types as openai
import rift.util.file_diff as file_diff
import rift.lsp.types as lsp
from rift.util.TextStream import TextStream
from mentat.config_manager import ConfigManager
from mentat.llm_api import CostTracker
from mentat.conversation import Conversation
from mentat.app import get_user_feedback_on_changes, warn_user_wrong_files
from mentat.code_file_manager import CodeFileManager
from mentat.user_input_manager import UserInputManager

@dataclass
class MentatAgentParams(agent.AgentParams):
    ...


@dataclass
class MentatAgentState(agent.AgentState):
    params: MentatAgentParams
    messages: list[openai.Message]
    response_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _response_buffer: str = ""

@dataclass
class MentatRunResult(agent.AgentRunResult):
    ...


@agent.agent(agent_description="Request codebase-wide edits through chat", display_name="Mentat")
@dataclass
class Mentat(agent.Agent):
    agent_type: ClassVar[str] = "mentat"
    run_params: Type[MentatAgentParams] = MentatAgentParams
    state: Optional[MentatAgentState] = None

    @classmethod
    async def create(cls, params: MentatAgentParams, server):
        state = MentatAgentState(
            params=params,
            messages=[],
        )
        obj = cls(
            state=state,
            agent_id=params.agent_id,
            server=server,
        )
        return obj

    async def apply_file_changes(self, updates) -> lsp.ApplyWorkspaceEditResponse:
        return await self.server.apply_workspace_edit(
            lsp.ApplyWorkspaceEditParams(
                file_diff.edits_from_file_changes(
                    updates,
                    user_confirmation=True,
                )
            )
        )

    async def _run_chat_thread(self, response_stream):
        """
        Run the chat thread.
        :param response_stream: The stream of responses from the chat.
        """

        before, after = response_stream.split_once("感")
        try:
            async with self.state.response_lock:
                async for delta in before:
                    self.state._response_buffer += delta
                    await self.send_progress({"response": self.state._response_buffer})
            await asyncio.sleep(0.1)
            await self._run_chat_thread(after)
        except Exception as e:
            logger.info(f"[_run_chat_thread] caught exception={e}, exiting")    

    async def run(self) -> MentatRunResult:
        response_stream = TextStream()

        run_chat_thread_task = asyncio.create_task(self._run_chat_thread(response_stream))

        loop = asyncio.get_running_loop()

        def send_chat_update_wrapper(prompt: str = "感", end="", eof=False):
            def _worker():
                response_stream.feed_data(prompt)

            loop.call_soon_threadsafe(_worker)

        def request_chat_wrapper(prompt: Optional[str] = None):
            async def request_chat():
                # logger.info("acquiring response lock")
                response_stream.feed_data("感")
                await asyncio.sleep(0.1)
                await self.state.response_lock.acquire()
                # logger.info("acquired response lock")
                await self.send_progress(dict(response=self._response_buffer, done_streaming=True))
                # logger.info(f"{self.RESPONSE=}")
                self.state.messages.append(openai.Message.assistant(content=self._response_buffer))
                self._response_buffer = ""
                if prompt is not None:
                    self.state.messages.append(openai.Message.assistant(content=prompt))
                # logger.info(f"MESSAGE HISTORY BEFORE REQUESTING: {self.state.messages}")

                resp = await self.request_chat(
                    agent.RequestChatRequest(messages=self.state.messages)
                )

                def refactor_uri_match(resp):
                    pattern = f"\[uri\]\({self.state.params.workspaceFolderPath}/(\S+)\)"
                    replacement = r"`\1`"
                    resp = re.sub(pattern, replacement, resp)
                    return resp

                try:
                    resp = refactor_uri_match(resp)
                except:
                    pass
                self.state.messages.append(openai.Message.user(content=resp))
                self.state.response_lock.release()
                return resp

            t = asyncio.run_coroutine_threadsafe(request_chat(), loop)
            futures.wait([t])
            result = t.result()
            return result

        # Initialize necessary objects and variables
        config = ConfigManager()
        cost_tracker = CostTracker()
        conv = Conversation(config, cost_tracker)
        user_input_manager = UserInputManager(config)
        def compute_paths():
            return []  # TODO
        paths = compute_paths()
        code_file_manager = CodeFileManager(paths, user_input_manager, config)

        # We set a flag that signals when we need a user request.
        need_user_request = True
        # We start an infinite loop, continually getting user input, modeling responses, and implementing changes.
        while True:
            # If we need a user request, we acquire one.
            if need_user_request:
                # We call a function to collect user input.
                user_response = user_input_manager.collect_user_input()
                # We add the user's input to our conversation object.
                conv.add_user_message(user_response)
            # We generate a model response and corresponding code changes based on the current state of the conversation and code files.
            explanation, code_changes = conv.get_model_response(code_file_manager, config)
            # We inform the user if their files seem incorrect based on the proposed code changes.
            warn_user_wrong_files(code_file_manager, code_changes)

            # If there are code changes, we prompt the user for feedback.
            if code_changes:
                need_user_request = get_user_feedback_on_changes(
                    config, conv, user_input_manager, code_file_manager, code_changes
                )
            else:
                # If there are no code changes, we flag that we need a new user request.
                need_user_request = True
                
