import asyncio
import json
import logging
import os
import random
from asyncio import Future
from concurrent import futures
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional

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
from rift.util.context import contextual_prompt, resolve_inline_uris
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


@agent(
    agent_description="Quickly generate a workspace with smol_dev.",
    display_name="Smol Developer",
)
@dataclass
class SmolAgent(Agent):
    state: SmolAgentState
    agent_type: ClassVar[str] = "smol_dev"

    @classmethod
    async def create(cls, params: SmolAgentParams, server):
        from rift.util.ofdict import ofdict

        params = ofdict(SmolAgentParams, params)
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
        prompt = await self.request_chat(RequestChatRequest(messages=self.state.messages))
        documents = resolve_inline_uris(prompt, self.server)
        prompt = contextual_prompt(prompt)
        self.state.messages.append(openai.Message.user(prompt))  # update messages history

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
            return smol_dev.prompts.plan(
                prompt, stream_handler=stream_handler, model="gpt-3.5-turbo"
            )

        plan = await self.add_task(description="Generate plan", task=get_plan).run()

        with futures.ThreadPoolExecutor(1) as executor:

            async def get_file_paths():
                return smol_dev.prompts.specify_file_paths(
                    prompt,
                    plan,
                    model="gpt-3.5-turbo",
                )

            file_paths = await self.add_task(
                description="Generate file paths", task=get_file_paths
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
                code_future = asyncio.ensure_future(
                    smol_dev.generate_code(prompt, plan, file_path, model="gpt-3.5-turbo")
                )
                done = False
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
                            description=f"Generate code for {fp}",
                            task=generate_code_for_filepath,
                            kwargs=dict(file_path=fp, position=i),
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

    async def send_result(self, result):
        ...  # unreachable
