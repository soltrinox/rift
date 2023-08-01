import re
from concurrent import futures

try:
    import aider
    import aider.coders
    import aider.coders.base_coder
    import aider.io
    import aider.main
    from aider.coders.base_coder import ExhaustedContextWindow
except ImportError:
    raise Exception(
        "`aider` not found. Try `pip install -e 'rift-engine[aider]'` from the Rift root directory."
    )

import asyncio
import dataclasses
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path, PurePath
from typing import Any, AsyncIterable, ClassVar, Dict, List, Literal, Optional, Type

from rich.text import Text

import rift.agents.abstract as agent
import rift.llm.openai_types as openai
import rift.lsp.types as lsp
import rift.util.file_diff as file_diff
from rift.util.ofdict import ofdict
from rift.util.TextStream import TextStream

logger = logging.getLogger(__name__)

response_lock = asyncio.Lock()


@dataclass
class AiderRunResult(agent.AgentRunResult):
    """
    A data class representing the results of an Aider agent run.
    This class extends from the base class `AgentRunResult` defined in the `rift.agents.abstract` module.
    """


@dataclass
class AiderAgentParams(agent.AgentRunParams):
    """
    A data class that holds parameters for running an Aider agent.
    This class extends from the base class `AgentRunParams` defined in the `rift.agents.abstract` module.
    """


@dataclass
class AiderAgentState(agent.AgentState):
    """
    A data class that holds the state of an Aider agent.
    It has the following attributes:
    - params (AiderAgentParams) : The parameters associated with the Aider agent.
    - messages (List[openai.Message]) : A list of messages communicated with the openai API during the agent's run.
    """

    params: AiderAgentParams
    messages: list[openai.Message]


@agent.agent(agent_description="Request codebase-wide edits through chat", display_name="Aider")
@dataclass
class Aider(agent.Agent):
    agent_type: str = "aider"
    run_params: Type[AiderAgentParams] = AiderAgentParams
    splash: Optional[
        str
    ] = """
   __    ____  ____  ____  ____
  /__\  (_  _)(  _ \( ___)(  _ \\
 /(__)\  _)(_  )(_) ))__)  )   /
(__)(__)(____)(____/(____)(_)\_)

"""

    @classmethod
    async def create(cls, params: AiderAgentParams, server):
        """
        Class method to create an instance of the Aider class.
        :param params: Parameters for the Aider agent.
        :param server: The server where the Aider agent is running.
        :return: An instance of the Aider class.
        """
        params = ofdict(AiderAgentParams, params)
        state = AiderAgentState(
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
        """
        Apply file changes to the workspace.
        :param updates: The updates to be applied.
        :return: The response from applying the workspace edit.
        """
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
        Run the chat thread for the Aider agent.
        :param response_stream: The stream of responses from the chat.
        """

        before, after = response_stream.split_once("感")
        try:
            async with response_lock:
                async for delta in before:
                    self.RESPONSE += delta
                    await self.send_progress({"response": self.RESPONSE})
            await asyncio.sleep(0.1)
            await self._run_chat_thread(after)
        except Exception as e:
            logger.info(f"[_run_chat_thread] caught exception={e}, exiting")

    async def run(self) -> AiderRunResult:
        """
        Run the Aider agent.
        :return: The result of running the Aider agent.
        """
        await self.send_progress()
        self.RESPONSE = ""

        response_stream = TextStream()

        run_chat_thread_task = asyncio.create_task(self._run_chat_thread(response_stream))

        loop = asyncio.get_running_loop()

        def send_chat_update_wrapper(prompt: str = "NONE", end="", eof=False):
            def _worker():
                response_stream.feed_data(prompt)

            loop.call_soon_threadsafe(_worker)

        def request_chat_wrapper(prompt: Optional[str] = None):
            async def request_chat():
                # logger.info("acquiring response lock")
                response_stream.feed_data("感")
                await asyncio.sleep(0.1)
                await response_lock.acquire()
                # logger.info("acquired response lock")
                await self.send_progress(dict(response=self.RESPONSE, done_streaming=True))
                # logger.info(f"{self.RESPONSE=}")
                self.state.messages.append(openai.Message.assistant(content=self.RESPONSE))
                self.RESPONSE = ""
                if prompt is not None:
                    self.state.messages.append(openai.Message.assistant(content=prompt))
                # logger.info(f"MESSAGE HISTORY BEFORE REQUESTING: {self.state.messages}")

                resp = await self.request_chat(
                    agent.RequestChatRequest(messages=self.state.messages)
                )
                try:
                    resp = re.sub(
                        f"uri://{self.state.params.workspaceFolderPath}/" r"(\S+)", r"`\1`", resp
                    )
                except:
                    pass
                self.state.messages.append(openai.Message.user(content=resp))
                response_lock.release()
                return resp

            t = asyncio.run_coroutine_threadsafe(request_chat(), loop)
            futures.wait([t])
            result = t.result()
            return result

        def confirm_ask(self, question, default="y"):
            # print(f"[confirm_ask] question={question}")
            self.num_user_asks += 1

            if self.yes is True:
                res = "yes"
            elif self.yes is False:
                res = "no"
            else:
                res = request_chat_wrapper(str(question) + " (y/n)")
                # res = "yes"

            hist = f"{question.strip()} {res.strip()}"

            # TODO: modify agent state chat history here
            self.append_chat_history(hist, linebreak=True, blockquote=True)
            if self.yes in (True, False):
                self.tool_output(hist)

            if not res or not res.strip():
                return
            return res.strip().lower().startswith("y")

        aider.io.InputOutput.confirm_ask = confirm_ask

        def get_input(self, root, rel_fnames, addable_rel_fnames, commands):
            try:
                rel_fnames = list(rel_fnames)
                show = None
                if len(rel_fnames) > 0:
                    show = "[aider] Current context:\n" + "\n".join(rel_fnames)

                inp = ""
                multiline_input = False

                while True:
                    if multiline_input:
                        show = ". "

                    session_kwargs = {
                        "message": show,
                        "reserve_space_for_menu": 4,
                        "input": self.input,
                        "output": self.output,
                    }
                    line = request_chat_wrapper(show)

                    if line and line[0] == "{" and not multiline_input:
                        multiline_input = True
                        inp += line[1:] + "\n"
                        continue
                    elif line and line[-1] == "}" and multiline_input:
                        inp += line[:-1] + "\n"
                        break
                    elif multiline_input:
                        inp += line + "\n"
                    else:
                        inp = line
                        break

                self.user_input(inp)
                return inp
            except Exception as e:
                print(f"EXCEPTION={e}")
                raise e

        aider.io.InputOutput.get_input = get_input

        def prompt_ask(self, question, default=None):
            self.num_user_asks += 1

            if self.yes is True:
                res = "yes"
            elif self.yes is False:
                res = "no"
            else:
                res = request_chat_wrapper(question)

            hist = f"{question.strip()} {res.strip()}"
            self.append_chat_history(hist, linebreak=True, blockquote=True)
            if self.yes in (True, False):
                self.tool_output(hist)

            return res

        aider.io.InputOutput.prompt_ask = prompt_ask

        def tool_error(self, message):
            self.num_error_outputs += 1

            if message.strip():
                hist = f"{message.strip()}"
                self.append_chat_history(hist, linebreak=True, blockquote=True)

            message = Text(message)
            style = dict(style=self.tool_error_color) if self.tool_error_color else dict()
            send_chat_update_wrapper(str(message))
            send_chat_update_wrapper("\n")

        aider.io.InputOutput.tool_error = tool_error

        def tool_output(self, *messages, log_only=False):
            hist = None
            if messages:
                hist = " ".join(messages)
                hist = f"{hist.strip()}"
                self.append_chat_history(hist, linebreak=True, blockquote=True)

            if not log_only:
                messages = list(map(Text, messages))
                style = dict(style=self.tool_output_color) if self.tool_output_color else dict()
                if hist:
                    # print(f"{hist=}")
                    send_chat_update_wrapper(hist + "\n")

        aider.io.InputOutput.tool_output = tool_output

        def show_send_output_stream(self, completion, silent):
            for chunk in completion:
                if chunk.choices[0].finish_reason == "length":
                    raise ExhaustedContextWindow()

                try:
                    func = chunk.choices[0].delta.function_call

                    for k, v in func.items():
                        if k in self.partial_response_function_call:
                            self.partial_response_function_call[k] += v
                        else:
                            self.partial_response_function_call[k] = v
                except AttributeError:
                    pass

                try:
                    text = chunk.choices[0].delta.content
                    if text:
                        self.partial_response_content += text
                except AttributeError:
                    pass

                if silent:
                    continue

                send_chat_update_wrapper(text)

        aider.coders.base_coder.Coder.show_send_output_stream = show_send_output_stream

        ##### PATCHES

        params = self.run_params
        import threading

        file_changes_lock = threading.Lock()
        file_changes: List[file_diff.FileChange] = []
        event = asyncio.Event()
        event2 = asyncio.Event()

        # This is called every time aider writes a file
        # Instead of writing, this stores the file change in a list
        def on_write(filename: str, new_content: str):
            if isinstance(filename, PurePath):
                filename = filename.__fspath__()
            file_change = file_diff.get_file_change(path=filename, new_content=new_content)
            file_changes.append(file_change)

        # This is called when aider wants to commit after writing all the files
        # This is where the user should accept/reject the changes

        def on_commit():
            loop.call_soon_threadsafe(lambda: event.set())
            while True:
                if not event2.is_set():
                    time.sleep(0.25)
                    continue
                break

        with futures.ThreadPoolExecutor(1) as pool:
            aider_fut = loop.run_in_executor(pool, aider.main.main, [], on_write, on_commit)
            logger.info("Aider thread running")

            while True:
                await event.wait()
                # while True:
                #     try:
                #         await asyncio.wait_for(event.wait(), 1)
                #         break
                #     except asyncio.TimeoutError:
                #         if self.task.cancelled:
                #             raise asyncio.CancelledError
                #         continue
                if len(file_changes) > 0:
                    await self.apply_file_changes(file_changes)
                    file_changes = []
                event2.set()
                event.clear()
            await aider_fut
        await self.send_update("Aider finished")
