import asyncio
import dataclasses
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterable, ClassVar, Dict, List, Literal, Optional, Type

import rift.lsp.types as lsp
import rift.util.file_diff as file_diff

logger = logging.getLogger(__name__)
from rich.text import Text

# from rift.agents.cli.agent import Agent, ClientParams, launcher
# from rift.agents.cli.util import ainput
import rift.agents.abstract as agent
import rift.llm.openai_types as openai
from rift.util.TextStream import TextStream

try:
    import aider
    import aider.coders
    import aider.coders.base_coder
    import aider.io
    import aider.main
    from aider.coders.base_coder import ExhaustedContextWindow
except ImportError:
    raise Exception(
        "`aider` not found. Try `pip install -e rift-engine[aider]` from the Rift root directory."
    )

from prompt_toolkit.shortcuts import CompleteStyle, PromptSession, prompt

response_lock = asyncio.Lock()


@dataclass
class AiderRunResult(agent.AgentRunResult):
    ...


@dataclass
class AiderAgentParams(agent.AgentRunParams):
    # args: List[str] = field(default_factory=list)
    # debug: bool = False
    # def __post_init__(self):
    #     self.args = []
    ...


@dataclass
class AiderAgentState(agent.AgentState):
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
    def create(cls, params: AiderAgentParams, server):
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
        return await self.server.apply_workspace_edit(
            lsp.ApplyWorkspaceEditParams(
                file_diff.edits_from_file_changes(
                    updates,
                    user_confirmation=True,
                )
            )
        )

    async def _run_chat_thread(self, response_stream):
        # logger.info("Started handler thread")
        before, after = response_stream.split_once("NONE")
        try:
            async with response_lock:
                async for delta in before:
                    self.RESPONSE += delta
                    await self.send_progress({"response": self.RESPONSE})
                    # logger.info("sent progress")
            await asyncio.sleep(0.1)

            # await self.send_progress({"response": self.RESPONSE, "done_streaming": True})

            # logger.info("sent done")
            self.RESPONSE = ""
            await self._run_chat_thread(after)
        except Exception as e:
            logger.info(f"[_run_chat_thread] caught exception={e}, exiting")

    async def run(self) -> AiderRunResult:
        """
        Example use:
            python -m rift.agents.cli.aider --port 7797 --debug False --args '["--model", "gpt-3.5-turbo", "rift/agents/aider.py"]'
        """
        self.RESPONSE = ""
        # await self.send_progress()
        response_stream = TextStream()

        run_chat_thread_task = asyncio.create_task(self._run_chat_thread(response_stream))

        loop = asyncio.get_running_loop()

        def send_chat_update(prompt: str):
            def _worker():
                response_stream.feed_data(prompt)
                response_stream.feed_data("NONE")

            loop.call_soon_threadsafe(_worker)

        # send_chat_update("YEEHAW")

        # logger.info("YEEHAW")

        def send_chat_update_wrapper(prompt: str = "NONE", end=""):
            def _worker():
                response_stream.feed_data(prompt)

            loop.call_soon_threadsafe(_worker)

        def request_chat_wrapper(prompt: Optional[str] = None, loop=None):
            # logger.info("YEHLLO")
            send_chat_update_wrapper()
            asyncio.set_event_loop(loop)
            # print(f"inside request chat wrapper prompt={prompt} loop={loop}")
            # logger.info("yeehaw in wrapper")
            # if loop is not None:
            #     asyncio.set_event_loop(loop)
            #     print("SET EVENT LOOP")
            # if prompt is not None:
            #     self.state.messages.append(openai.Message.assistant(prompt))

            # logger.info("yeehaw wrapper")
            async def request_chat():
                await response_lock.acquire()
                # await asyncio.sleep(1)
                # async with response_lock:
                # logger.info("yeehaw")
                await self.send_progress(dict(response=self.RESPONSE, done_streaming=True))
                # logger.info("sent streaming done")
                self.state.messages.append(openai.Message.assistant(content=self.RESPONSE))
                self.RESPONSE = ""

                if prompt is not None:
                    # self.RESPONSE += prompt
                    self.state.messages.append(openai.Message.assistant(content=prompt))

                # logger.info("sending chat request")
                resp = await self.request_chat(
                    agent.RequestChatRequest(messages=self.state.messages)
                )
                self.state.messages.append(openai.Message.user(content=resp))
                response_lock.release()
                return resp

            # logger.info("[request_chat_wrapper] creating task")
            t = loop.create_task(request_chat())
            # logger.info("[request_chat_wrapper] created task")
            while not t.done():
                # print("sleeping")
                time.sleep(1)
            return t.result()

        # # - For interactions, need to intercept:
        # #       io.confirm_ask
        def confirm_ask(self, question, default="y"):
            # print(f"[confirm_ask] question={question}")
            self.num_user_asks += 1

            if self.yes is True:
                res = "yes"
            elif self.yes is False:
                res = "no"
            else:
                # time.sleep(5)
                # print("firing request")
                res = request_chat_wrapper(str(question) + " (y/n)", loop=loop)
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
                # if self.pretty:
                #     # style = dict(style=self.user_input_color) if self.user_input_color else dict()
                #     # self.console.rule(**style)
                # else:
                #     # print()
                #     pass

                rel_fnames = list(rel_fnames)
                # show = f"[aider {' '.join(rel_fnames)}] >"
                show = None
                if len(rel_fnames) > 0:
                    show = "[aider] Current context:\n" + "\n".join(rel_fnames)
                # show = ("Current context:" + "\n".join(rel_fnames) + "\n" if len(rel_fnames) > 0 else "\n") + "Awaiting input."
                # show =
                # if len(show) > 10:
                #     show += "\n"
                # show += "[aider] > "

                inp = ""
                multiline_input = False

                # if self.user_input_color:
                #     style = Style.from_dict(
                #         {
                #             "": self.user_input_color,
                #             "pygments.literal.string": f"bold italic {self.user_input_color}",
                #         }
                #     )
                # else:
                #     style = None

                while True:
                    # completer_instance = AutoCompleter(
                    #     root, rel_fnames, addable_rel_fnames, commands, self.encoding
                    # )
                    if multiline_input:
                        show = ". "

                    session_kwargs = {
                        "message": show,
                        # "completer": completer_instance,
                        "reserve_space_for_menu": 4,
                        # "complete_style": CompleteStyle.MULTI_COLUMN,
                        "input": self.input,
                        "output": self.output,
                        # "lexer": PygmentsLexer(MarkdownLexer),
                    }
                    # if style:
                    #     session_kwargs["style"] = style

                    # if self.input_history_file is not None:
                    #     session_kwargs["history"] = FileHistory(self.input_history_file)

                    # kb = KeyBindings()

                    # @kb.add("escape", "c-m", eager=True)
                    # def _(event):
                    #     event.current_buffer.insert_text("\n")

                    # # TODO: fire chat handler here
                    # session = PromptSession(key_bindings=kb, **session_kwargs)
                    # line = session.prompt()

                    # print(f"show={show}")
                    line = request_chat_wrapper(show, loop)
                    # print(f"line={line}")
                    # line = "hello"

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

                # print()
                self.user_input(inp)
                return inp
            except Exception as e:
                print(f"EXCEPTION={e}")
                raise e

        #       io.get_input
        aider.io.InputOutput.get_input = get_input

        def prompt_ask(self, question, default=None):
            self.num_user_asks += 1

            if self.yes is True:
                res = "yes"
            elif self.yes is False:
                res = "no"
            else:
                # res = prompt(question + " ", default=default)
                # res = ...
                res = request_chat_wrapper(question + " ", loop)
                # res = "yes"

            # print(f"got res={res}")

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
            # self.console.print(message, **style)
            send_chat_update_wrapper(str(message))
            send_chat_update_wrapper("\n")

        #       io.tool_error
        aider.io.InputOutput.tool_error = tool_error

        def tool_output(self, *messages, log_only=False):
            hist = None
            if messages:
                hist = " ".join(messages)
                hist = f"{hist.strip()}"
                self.append_chat_history(hist, linebreak=True, blockquote=True)
                # print("APPENDED")

            if not log_only:
                messages = list(map(Text, messages))
                style = dict(style=self.tool_output_color) if self.tool_output_color else dict()
                # self.console.print(*messages, **style)
                if hist:
                    send_chat_update_wrapper(hist)
                    send_chat_update_wrapper("\n")

        aider.io.InputOutput.tool_output = tool_output

        # logger.info("attempting imports")
        # import aider.coders
        # # print("ok")
        # import aider.coders.base_coder
        # # print("ok")
        # from aider.coders.base_coder import ExhautedcontextWindow
        # # print("ok")
        def show_send_output_stream(self, completion, silent):
            for chunk in completion:
                if chunk.choices[0].finish_reason == "length":
                    raise ExhaustedContextWindow()

                try:
                    func = chunk.choices[0].delta.function_call
                    # dump(func)
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

                # sys.stdout.write(text)
                # sys.stdout.flush()
                send_chat_update_wrapper(text)

        aider.coders.base_coder.Coder.show_send_output_stream = show_send_output_stream

        ##### PATCHES

        params = self.run_params
        file_changes: List[file_diff.FileChange] = []
        event = asyncio.Event()
        event2 = asyncio.Event()

        # This is called every time aider writes a file
        # Instead of writing, this stores the file change in a list
        def on_write(filename: str, new_content: str):
            file_changes.append(file_diff.get_file_change(path=filename, new_content=new_content))

        # This is called when aider wants to commit after writing all the files
        # This is where the user should accept/reject the changes
        # loop = asyncio.get_running_loop()

        def on_commit():
            loop.call_soon_threadsafe(lambda: event.set())
            while True:
                if not event2.is_set():
                    time.sleep(0.25)
                    continue
                break

        from concurrent import futures

        with futures.ThreadPoolExecutor(1) as pool:
            aider_fut = loop.run_in_executor(pool, aider.main.main, [], on_write, on_commit)
            # input_fut = loop.run_in_executor(pool, request_chat_wrapper, "yeehaw", loop)
            # print(await input_fut)

            # while True:
            await event.wait()
            await self.apply_file_changes(file_changes)
            file_changes = []
            event2.set()
            event.clear()
            await aider_fut
        await self.send_update("yeehaw")


# if __name__ == "__main__":
# launcher(Aider, AiderAgentParams)
