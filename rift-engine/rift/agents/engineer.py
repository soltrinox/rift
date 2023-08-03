import asyncio
import functools
import logging
import os
import re
import time
from asyncio import Future
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Dict, Optional

import typer

import rift.lsp.types as lsp
from rift.agents.abstract import AgentProgress  # AgentTask,
from rift.agents.abstract import (
    Agent,
    AgentParams,
    AgentRunResult,
    AgentState,
    RequestChatRequest,
    agent,
)
from rift.util import file_diff
from rift.util.context import contextual_prompt, resolve_inline_uris
from rift.util.TextStream import TextStream

SEEN = set()

STEPS_AGENT_TASKS_NAME_QUEUE = asyncio.Queue()
STEPS_AGENT_TASKS_EVENT_QUEUE = asyncio.Queue()

SEEN = set()

import json

import rift.llm.openai_types as openai

logger = logging.getLogger(__name__)


def __fix_windows_path(path: str) -> str:
    """
    Replace a windows path represented as "/c%3A"... with "c:"...

    :param path: Original path
    :return: Usable windows path, or original path if not a windows path
    """
    pattern = r"^/(.)%3A"

    match = re.match(pattern, path)

    if match:
        drive_letter = match.group(1)
        return path.replace(f"/{drive_letter}%3A", f"{drive_letter}:")
    else:
        return path


def _fix_windows_path(path: str) -> str:
    """
    Replace a windows path represented as "/c%3A"... with "c:"...

    :param path: Original path
    :return: Usable windows path, or original path if not a windows path
    """
    pattern = r"^/(.)%3A"

    match = re.match(pattern, path)

    if match:
        drive_letter = match.group(1)
        return path.replace(f"/{drive_letter}%3A", f"{drive_letter}:")
    else:
        return path


response_lock = asyncio.Lock()


# dataclass for representing the result of the code completion agent run
@dataclass
class EngineerRunResult(AgentRunResult):
    ...


@dataclass
class EngineerAgentParams(AgentParams):
    instructionPrompt: Optional[str] = None


@dataclass
class EngineerProgress(
    AgentProgress
):  # reports what tasks are active and responsible for reporting new tasks
    response: Optional[str] = None
    done_streaming: bool = False


@dataclass
class EngineerAgentState(AgentState):
    params: EngineerAgentParams
    messages: list[openai.Message]
    change_futures: Dict[str, Future] = field(default_factory=dict)
    _done: bool = False


# decorator for creating the code completion agent
@agent(
    agent_description="Specify what you want it to build, the AI asks for clarification, and then builds it.",
    display_name="GPT Engineer",
)
@dataclass
class EngineerAgent(Agent):
    state: EngineerAgentState
    agent_type: ClassVar[str] = "engineer"
    params_cls: ClassVar[Any] = EngineerAgentParams

    async def _main(
        self,
        prompt: Optional[str] = None,
        project_path: str = "",
        model: str = "gpt-4",
        temperature: float = 0.1,
        steps_config: Any = None,
        verbose: bool = typer.Option(False, "--verbose", "-v"),
        **kwargs,
    ):
        """
        Main function for the EngineerAgent. It initializes the AI model and starts the engineering process.

        :param prompt: The initial prompt for the AI.
        :param project_path: The path to the project directory.
        :param model: The AI model to use.
        :param temperature: The temperature for the AI model's output.
        :param steps_config: The configuration for the engineering steps.
        :param verbose: Whether to output verbose logs.
        :param kwargs: Additional parameters.
        """
        loop = asyncio.get_event_loop()

        try:
            import gpt_engineer
            import gpt_engineer.chat_to_files
            import gpt_engineer.db
            from gpt_engineer.ai import AI, fallback_model
            from gpt_engineer.collect import collect_learnings
            from gpt_engineer.db import DB, DBs, archive
            from gpt_engineer.learning import collect_consent
            from gpt_engineer.steps import STEPS
            from gpt_engineer.steps import Config as StepsConfig

        except ImportError:
            raise Exception(
                '`gpt_engineer` not found. Try `pip install -e "rift-engine[gpt-engineer]"` from the repository root directory.'
            )

        def _popup_chat_wrapper(prompt: str = "NONE", end=""):
            async def _worker():
                await self.response_stream.feed_data(prompt)

            asyncio.run_coroutine_threadsafe(_worker(), loop)

        def _popup_input_wrapper(prompt="", loop=None):
            asyncio.set_event_loop(loop)
            # print("SET EVENT LOOP")
            self.state.messages.append(openai.Message.assistant(prompt))

            async def request_chat():
                async with response_lock:
                    await self.send_progress(
                        EngineerProgress(response=self.RESPONSE, done_streaming=True)
                    )
                    self.state.messages.append(openai.Message.assistant(content=self.RESPONSE))

                    self.RESPONSE = ""
                    return await self.request_chat(RequestChatRequest(messages=self.state.messages))

            t = loop.create_task(request_chat())
            while not t.done():
                time.sleep(1)
            return t.result()

        gpt_engineer.ai.print = _popup_chat_wrapper
        gpt_engineer.steps.print = _popup_chat_wrapper
        gpt_engineer.steps.input = functools.partial(_popup_input_wrapper, loop=loop)
        gpt_engineer.learning.input = functools.partial(_popup_input_wrapper, loop=loop)
        # TODO: more coverage
        logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
        model = fallback_model(model)
        ai = AI(
            model=model,
            temperature=temperature,
        )

        input_path = _fix_windows_path(project_path)

        gpteng_path = os.path.join(input_path, ".gpteng")

        if not os.path.exists(gpteng_path):
            os.makedirs(gpteng_path)

        if prompt:
            with open(os.path.join(input_path, "prompt"), "w") as f:
                f.write(prompt)

        memory_path = os.path.join(gpteng_path, "memory")
        workspace_path = os.path.join(input_path)  # pipe files directly into the workspace
        archive_path = os.path.join(gpteng_path, "archive")

        dbs = DBs(
            memory=DB(memory_path),
            logs=DB(os.path.join(memory_path, "logs")),
            input=DB(workspace_path),
            workspace=DB(workspace_path, in_memory_dict={}),  # in_memory_dict={}),
            preprompts=DB(Path(gpt_engineer.__file__).parent / "preprompts"),
            archive=DB(archive_path),
        )

        steps_config = StepsConfig.DEFAULT

        # if steps_config not in [
        #     StepsConfig.EXECUTE_ONLY,
        #     StepsConfig.USE_FEEDBACK,
        #     StepsConfig.EVALUATE,
        # ]:
        #     archive(dbs)

        steps = STEPS[steps_config]

        # Add all steps to task list
        steps = STEPS[steps_config]
        from concurrent import futures

        step_events: Dict[int, asyncio.Event] = dict()
        for i, step in enumerate(steps):
            event = asyncio.Event()
            step_events[i] = event

            async def _step_task(event: asyncio.Event):
                await event.wait()

            _ = asyncio.create_task(
                self.add_task(description=step.__name__, task=_step_task, args=[event]).run()
            )

        # # Add all steps to task list
        # for step in steps:
        #     await STEPS_AGENT_TASKS_NAME_QUEUE.put(step._name_)

        counter = 0
        with futures.ThreadPoolExecutor(1) as pool:
            for i, step in enumerate(steps):
                await asyncio.sleep(0.1)
                messages = await loop.run_in_executor(pool, step, ai, dbs)
                await asyncio.sleep(0.1)
                dbs.logs[step.__name__] = json.dumps(messages)
                items = list(dbs.workspace.in_memory_dict.items())
                updates = [x for x in items if x[0] not in SEEN]
                if len(updates) > 0:
                    # for file_path, new_contents in updates:
                    await self.server.apply_workspace_edit(
                        lsp.ApplyWorkspaceEditParams(
                            file_diff.edits_from_file_changes(
                                [
                                    file_diff.get_file_change(file_path, new_contents)
                                    for file_path, new_contents in updates
                                ],
                                user_confirmation=True,
                            )
                        )
                    )
                    for x in items:
                        if x[0] in SEEN:
                            pass
                        else:
                            SEEN.add(x[0])

                # Mark this step as complete
                # # event = await STEPS_AGENT_TASKS_EVENT_QUEUE.get()
                # event.set()
                step_events[i].set()
                await asyncio.sleep(0.5)
                counter += 1

    async def _run_chat_thread(self, response_stream):
        # logger.info("Started handler thread")
        self.RESPONSE = ""
        before, after = response_stream.split_once("NONE")

        try:
            async with response_lock:
                async for delta in before:
                    self.RESPONSE += delta
                    await self.send_progress(EngineerProgress(response=self.RESPONSE))
            await asyncio.sleep(0.1)
            await self._run_chat_thread(after)
        except Exception as e:
            logger.info(f"[_run_chat_thread] caught exception={e}, exiting")

    @classmethod
    async def create(cls, params: EngineerAgentParams, server):
        state = EngineerAgentState(
            params=params,
            messages=[openai.Message.assistant("What do you want to build?")],
        )
        obj = cls(
            state=state,
            agent_id=params.agent_id,
            server=server,
        )

        return obj

    async def run(self) -> AgentRunResult:  # main entry point
        self.response_stream = TextStream()
        await self.send_progress()
        asyncio.create_task(self._run_chat_thread(self.response_stream))

        async def get_prompt():
            prompt = await self.request_chat(RequestChatRequest(messages=self.state.messages))
            self.state.messages.append(openai.Message.user(prompt))
            return prompt

        get_prompt_task = self.add_task("Get prompt for workspace", get_prompt)
        prompt = await get_prompt_task.run()

        documents = resolve_inline_uris(prompt, self.server)
        prompt = contextual_prompt(prompt, documents)

        await asyncio.create_task(
            self._main(prompt=prompt, project_path=self.state.params.workspaceFolderPath)
        )
