from dataclasses import dataclass
from typing import List, Optional, Type

import rift.agents.abstract as agent
import rift.llm.openai_types as openai


@dataclass
class MentatAgentParams(agent.AgentRunParams):
    ...


@dataclass
class MentatAgentState(agent.AgentState):
    params: MentatAgentParams
    messages: list[openai.Message]


@agent.agent(agent_description="Request codebase-wide edits through chat", display_name="Mentat")
@dataclass
class Mentat(agent.Agent):
    agent_type: str = "mentat"
    run_params: Type[MentatAgentParams] = MentatAgentParams
    splash: Optional[
        str
    ] = """
mentat
"""

    @classmethod
    async def create(cls, params: MentatAgentParams, server):
        from rift.util.ofdict import ofdict

        params = ofdict(MentatAgentParams, params)
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

    async def run(self) -> MentatRunResult:
        self.RESPONSE = ""
        response_stream = TextStream()

        run_chat_thread_task = asyncio.create_task(self._run_chat_thread(response_stream))

        loop = asyncio.get_running_loop()

        def send_chat_update(prompt: str):
            def _worker():
                response_stream.feed_data(prompt)
                response_stream.feed_data("NONE")

            loop.call_soon_threadsafe(_worker)

        def send_chat_update_wrapper(prompt: str = "NONE", end=""):
            def _worker():
                response_stream.feed_data(prompt)

            loop.call_soon_threadsafe(_worker)

        def request_chat_wrapper(prompt: Optional[str] = None, loop=None):
            send_chat_update_wrapper()
            asyncio.set_event_loop(loop)

            async def request_chat():
                await asyncio.sleep(0.1)
                await response_lock.acquire()
                await self.send_progress({"response": self.RESPONSE, "done_streaming": True})
                self.state.messages.append(openai.Message.assistant(content=self.RESPONSE))
                self.RESPONSE = ""

                if prompt is not None:
                    self.state.messages.append(openai.Message.assistant(content=prompt))

                resp = await self.request_chat(
                    agent.RequestChatRequest(messages=self.state.messages)
                )
                self.state.messages.append(openai.Message.user(content=resp))
                response_lock.release()
                return resp

            t = loop.create_task(request_chat())
            while not t.done():
                time.sleep(1)
            return t.result()

        # Initialize necessary objects and variables
        config = ConfigManager()
        cost_tracker = CostTracker()
        conv = Conversation(config, cost_tracker)
        user_input_manager = UserInputManager(config)
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
