import asyncio
import json
import logging
import os
import random
from asyncio import Future
from concurrent import futures
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional
from rift.util.misc import replace_chips

import smol_dev

import rift.llm.openai_types as openai
import rift.lsp.types as lsp
import rift.util.file_diff as file_diff
from rift.agents.abstract import AgentProgress  # AgentTask,
from rift.agents.abstract import (
    Agent,
    AgentRunParams,
    AgentRunResult,
    AgentState,
    RequestChatRequest,
    RequestInputRequest,
    RunAgentParams,
    agent,
)
from rift.agents.agenttask import AgentTask
from rift.llm.abstract import AbstractCodeCompletionProvider, InsertCodeResult
from rift.lsp import LspServer as BaseLspServer
from rift.lsp.document import TextDocumentItem
from rift.server.selection import RangeSet
from rift.util.TextStream import TextStream

logger = logging.getLogger(__name__)


# dataclass for representing the result of the code completion agent run
@dataclass
class SmolRunResult(AgentRunResult):
    ...


# dataclass for representing the progress of the code completion agent
@dataclass
class SmolProgress(AgentProgress):
    response: Optional[str] = None
    thoughts: Optional[str] = None
    textDocument: Optional[lsp.TextDocumentIdentifier] = None
    cursor: Optional[lsp.Position] = None
    additive_ranges: Optional[RangeSet] = None
    negative_ranges: Optional[RangeSet] = None
    ready: bool = False


# dataclass for representing the parameters of the code completion agent
@dataclass
class SmolAgentParams(AgentRunParams):
    instructionPrompt: Optional[str] = None


# dataclass for representing the state of the code completion agent
@dataclass
class SmolAgentState(AgentState):
    params: SmolAgentParams
    _done: bool = False
    messages: List[openai.Message] = field(default_factory=list)


# decorator for creating the code completion agent
@agent(
    agent_description="Quickly generate a workspace with smol_dev.",
    display_name="Smol Developer",
)
@dataclass
class SmolAgent(Agent):
    state: SmolAgentState
    agent_type: ClassVar[str] = "smol_dev"

    @classmethod
    def create(cls, params: SmolAgentParams, server):
        state = SmolAgentState(
            params=params,
            _done=False,
            messages=[openai.Message.assistant("What do you want to build?")],
        )
        obj = cls(
            state=state,
            agent_id=params.agent_id,
            server=server,
        )
        return obj

    async def run(self) -> AgentRunResult:
        """
        run through smol dev chat loop:
            - get prompt from user via chat
            - generate plan
            - generate file structure
            - generate code (in parallel)
        """
        await self.send_progress()
        # await ainput("\n> Press any key to continue.\n")

        # if params.prompt_file is None:
        #     prompt = await ainput("\n> Prompt file not found. Please input a prompt.\n")
        # else:
        #     with open(params.prompt_file, "r") as f:
        #         prompt = f.read()

        # get the initial prompt
        prompt = await self.request_chat(RequestChatRequest(messages=self.state.messages))
        prompt = replace_chips(prompt, self.server)
        self.state.messages.append(openai.Message.user(prompt))  # update messages history

        # logger.info("Starting smol-dev with prompt:")
        # self.console.print(prompt, markup=True, highlight=True)

        # await ainput("\n> Press any key to continue.\n")

        RESPONSE = ""
        loop = asyncio.get_running_loop()

        FUTURES = dict()

        def stream_handler(chunk):
            try:
                chunk = chunk.decode("utf-8")
            except:
                pass
            nonlocal RESPONSE
            RESPONSE += chunk

            # def stream_string(string):
            #     for char in string:
            #         print(char, end="", flush=True)
            #         time.sleep(0.0012)

            # stream_string(chunk.decode("utf-8"))
            fut = asyncio.run_coroutine_threadsafe(
                self.send_progress(
                    SmolProgress(
                        response=RESPONSE,
                    )
                ),
                loop=loop,
            )
            FUTURES[RESPONSE] = asyncio.wrap_future(fut)

        async def get_plan():
            # return await asyncio.get_running_loop().run_in_executor(
            #     executor,
            #     smol_dev.prompts.plan,
            #     prompt,
            #     stream_handler=stream_handler,
            #     model="gpt-3.5-turbo",
            # )
            return smol_dev.prompts.plan(
                prompt, stream_handler=stream_handler, model="gpt-3.5-turbo"
            )

        plan = await self.add_task(AgentTask(description="Generate plan", task=get_plan)).run()
        logger.info(f"PLAN {plan=}")

        with futures.ThreadPoolExecutor(1) as executor:
            # await ainput("\n> Press any key to continue.\n")
            async def get_file_paths():
                # logger.info(f"{prompt=} {plan=}")
                return smol_dev.prompts.specify_file_paths(
                    prompt,
                    plan,
                    model="gpt-3.5-turbo",
                )

            file_paths = await self.add_task(
                AgentTask(description="Generate file paths", task=get_file_paths)
            ).run()

            logger.info(f"Got file paths: {json.dumps(file_paths, indent=2)}")

            file_changes = []

            @dataclass
            class PBarUpdater:
                pbars: Dict[int, Any] = field(default_factory=dict)
                dones: Dict[int, Any] = field(default_factory=dict)
                messages: Dict[int, Optional[str]] = field(default_factory=dict)
                lock: asyncio.Lock = asyncio.Lock()

                def update(self):
                    for position, pbar in self.pbars.items():
                        if self.dones[position]:
                            pbar.display(self.messages[position])
                        else:
                            pbar.update()

            updater = PBarUpdater()

            async def generate_code_for_filepath(
                file_path: str, position: int
            ) -> file_diff.FileChange:
                # stream_handler = lambda chunk: pbar.update(n=len(chunk))
                code_future = asyncio.ensure_future(
                    smol_dev.generate_code(prompt, plan, file_path, model="gpt-3.5-turbo")
                )
                # with tqdm.asyncio.tqdm(position=position, unit=" chars", unit_scale=True) as pbar:
                # async with updater.lock:
                #     updater.pbars[position] = pbar
                #     updater.dones[position] = False
                done = False
                # waiter = asyncio.get_running_loop().create_future()

                # def cb(fut):
                #     waiter.cancel()

                # code_future.add_done_callback(cb)

                # async def spinner():
                #     spinner_index: int = 0
                #     steps = ["[⢿]", "[⣻]", "[⣽]", "[⣾]", "[⣷]", "[⣯]", "[⣟]", "[⡿]"]
                #     while True:
                #         c = steps[spinner_index % len(steps)]
                #         pbar.set_description(f"{c} Generating code for {file_path}")
                #         async with updater.lock:
                #             updater.update()
                #         spinner_index += 1
                #         await asyncio.sleep(0.05)
                #         if waiter.done():
                #             # pbar.display(f"[✔️] Generated code for {file_path}")
                #             async with updater.lock:
                #                 updater.dones[position] = True
                #                 updater.messages[
                #                     position
                #                 ] = f"[✔️] Generated code for {file_path}"
                #                 pbar.set_description(f"[✔️] Generated code for {file_path}")
                #                 updater.update()
                #             return

                # t = asyncio.create_task(spinner())
                code = await code_future
                logger.info("folder uri:")
                logger.info(self.state.params.workspaceFolderPath)
                absolute_file_path = os.path.join(self.state.params.workspaceFolderPath, file_path)
                file_change = file_diff.get_file_change(path=absolute_file_path, new_content=code)
                return file_change

            fs = []
            for i, fp in enumerate(file_paths):
                fs.append(
                    asyncio.create_task(
                        self.add_task(
                            AgentTask(
                                description=f"Generate code for {fp}",
                                task=generate_code_for_filepath,
                                kwargs=dict(file_path=fp, position=i),
                            )
                        ).run()
                    )
                )
                stream_handler(f"Generating code for {fp}.\n")

            await asyncio.wait(FUTURES.values())

            await self.send_progress({"response": RESPONSE, "done_streaming": True})

            file_changes = await asyncio.gather(*fs)
            workspace_edit = file_diff.edits_from_file_changes(file_changes, user_confirmation=True)
            await self.server.apply_workspace_edit(
                lsp.ApplyWorkspaceEditParams(edit=workspace_edit, label="rift")
            )

    async def on_change(
        self,
        *,
        before: lsp.TextDocumentItem,
        after: lsp.TextDocumentItem,
        changes: lsp.DidChangeTextDocumentParams,
    ):
        if self.task.status != "running":
            return
        """
        [todo]
        When a change happens:
        1. if the change is before our 'working area', then we stop the completion request and run again.
        2. if the change is in our 'working area', then the user is correcting something that
        3. if the change is after our 'working area', then just keep going.
        4. if _we_ caused the change, then just keep going.
        """
        assert changes.textDocument.uri == self.state.document.uri
        self.state.document = before
        for c in changes.contentChanges:
            # logger.info(f"contentChange: {c=}")
            # fut = self.state.change_futures.get(c.text)
            fut = None
            for span, vfut in self.state.change_futures.items():
                if c.text in span:
                    fut = vfut

            if fut is not None:
                # we caused this change
                try:
                    fut.set_result(None)
                except:
                    pass
            else:
                # someone else caused this change
                # [todo], in the below examples, we shouldn't cancel, but instead figure out what changed and restart the insertions with the new information.
                with lsp.setdoc(self.state.document):
                    self.state.additive_ranges.apply_edit(c)
                if c.range is None:
                    await self.cancel("the whole document got replaced")
                else:
                    if c.range.end <= self.state.cursor:
                        # some text was changed before our cursor
                        if c.range.end.line < self.state.cursor.line:
                            # the change is occurring on lines strictly above us
                            # so we can adjust the number of lines
                            lines_to_add = (
                                c.text.count("\n") + c.range.start.line - c.range.end.line
                            )
                            self.state.cursor += (lines_to_add, 0)
                        else:
                            # self.cancel("someone is editing on the same line as us")
                            pass  # temporarily disabled
                    elif self.state.cursor in c.range:
                        await self.cancel("someone is editing the same text as us")

        self.state.document = after

    async def send_result(self, result):
        ...  # unreachable

    def accepted_diff_text(self, diff):
        result = ""
        for op, text in diff:
            if op == -1:  # remove
                pass
            elif op == 0:
                result += text
            elif op == 1:
                result += text
        return result

    async def accept(self):
        logger.info(f"{self} user accepted result")

        await self.server.apply_range_edit(
            self.state.document.uri, self.RANGE, self.accepted_diff_text(self.DIFF)
        )
        # if self.task.status not in ["error", "done"]:
        #     logger.error(f"cannot_ accept status {self.task.status}")
        #     return
        # self.status = "done"
        await self.send_progress(
            payload="accepted",
            payload_only=True,
        )
        self.state._done = True

    def rejected_diff_text(self, diff):
        result = ""
        for op, text in diff:
            if op == -1:  # remove
                result += text
            elif op == 0:
                result += text
            elif op == 1:
                pass
        return result

    async def reject(self):
        logger.info(f"{self} user rejected result")

        await self.server.apply_range_edit(
            self.state.document.uri, self.RANGE, self.rejected_diff_text(self.DIFF)
        )
        await self.send_progress(
            payload="rejected",
            payload_only=True,
        )
        self.state._done = True
