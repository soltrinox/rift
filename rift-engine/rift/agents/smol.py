import asyncio
import json
import logging
import os
from concurrent import futures
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, List, Optional

import rift.llm.openai_types as openai
import rift.lsp.types as lsp
import rift.util.file_diff as file_diff
from rift.agents.abstract import AgentProgress  # AgentTask,
from rift.agents.abstract import (
    Agent,
    AgentParams,
    AgentRunResult,
    AgentState,
    RequestChatRequest,
    agent,
)
from rift.server.selection import RangeSet
from rift.util.context import contextual_prompt, resolve_inline_uris

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
class SmolAgentParams(AgentParams):
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
    params_cls: ClassVar[Any] = SmolAgentParams

    @classmethod
    async def create(cls, params: SmolAgentParams, server):
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

        try:
            import smol_dev
        except ImportError:
            raise Exception(
                f"`smol_dev` not found. Try `pip install -e 'rift-engine[smol_dev]' from the repository root directory.`"
            )
        await self.send_progress()
        prompt = await self.request_chat(RequestChatRequest(messages=self.state.messages))
        documents = resolve_inline_uris(prompt, self.server)
        prompt = contextual_prompt(prompt, documents)
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
            fut = asyncio.create_task(
                asyncio.coroutine(smol_dev.prompts.plan)(
                    prompt, stream_handler=stream_handler, model="gpt-3.5-turbo"
                )
            )

            fut.add_done_callback(
                lambda _: asyncio.run_coroutine_threadsafe(
                    self.send_progress(dict(done_streaming=True)), loop=loop
                )
            )

            return

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

            # Ask the user where the generated files should be placed
            self.state.messages.append(
                openai.Message.assistant("Where should the generated files be placed?")
            )
            location_prompt = await self.request_chat(
                RequestChatRequest(messages=self.state.messages)
            )
            self.state.messages.append(
                openai.Message.user(location_prompt)
            )  # update messages history

            # Parse any URIs from the user's response
            documents = resolve_inline_uris(location_prompt, self.server)
            if documents:
                # Use the parent directory of the first URI as the parent directory for the generated files
                parent_dir = os.path.dirname(documents[0].uri)
                if not os.path.isdir(parent_dir):
                    parent_dir = os.path.dirname(parent_dir)
            else:
                # If no URIs are found, default to the workspace folder
                parent_dir = self.state.params.workspaceFolderPath

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

            logger.info(f"generate code target dir: {self.state.params.workspaceFolderPath}")

            async def generate_code_for_filepath(
                file_path: str, position: int
            ) -> file_diff.FileChange:
                code_future = asyncio.ensure_future(
                    smol_dev.generate_code(prompt, plan, file_path, model="gpt-3.5-turbo")
                )
                done = False
                code = await code_future
                absolute_file_path = os.path.join(self.state.params.workspaceFolderPath, file_path)
                file_change = file_diff.get_file_change(path=absolute_file_path, new_content=code)
                return file_change

            fs = []
            loop = asyncio.get_running_loop()
            for i, fp in enumerate(file_paths):
                fut = asyncio.create_task(
                    self.add_task(
                        description=f"Generate code for {fp}",
                        task=generate_code_for_filepath,
                        kwargs=dict(file_path=fp, position=i),
                    ).run()
                )

                def done_cb(*args):
                    async def coro():
                        await self.send_progress()

                    asyncio.run_coroutine_threadsafe(coro(), loop=loop)

                fut.add_done_callback(done_cb)
                fs.append(fut)
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
