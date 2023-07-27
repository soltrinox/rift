import time
import asyncio
import logging
import uuid
from asyncio import Future
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Dict, Optional

import typer

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
from rift.util import file_diff
from rift.util.TextStream import TextStream

try:
    import gpt_engineer
    import gpt_engineer.chat_to_files
    import gpt_engineer.db

except ImportError:
    raise Exception("`gpt_engineer` not found. Try `pip install gpt-engineer`")

SEEN = set()

import json
import threading

from gpt_engineer.ai import AI, fallback_model
from gpt_engineer.collect import collect_learnings
from gpt_engineer.db import DB, DBs, archive
from gpt_engineer.learning import collect_consent
from gpt_engineer.steps import STEPS
from gpt_engineer.steps import Config as StepsConfig

import rift.llm.openai_types as openai

logger = logging.getLogger(__name__)

def _fix_windows_path(path: str) -> str:
    """
    Replace a windows path represented as "/c%3A"... with "c:"...

    :param path: Original path
    :return: Usable windows path, or original path if not a windows path
    """
    pattern = r'^/(.)%3A'

    match = re.match(pattern, path)

    if match:
        drive_letter = match.group(1)
        return path.replace(f"/{drive_letter}%3A", f"{drive_letter}:")
    else:
        return path

# async def _popup_input(prompt: str) -> str:
#     await INPUT_PROMPT_QUEUE.put(prompt)
#     while True:
#         try:
#             resp = await asyncio.wait_for(INPUT_RESPONSE_QUEUE.get(), timeout=1.0)
#             break
#         except:
#             continue
#     return resp


# def _popup_input_wrapper(prompt: str="") -> str:
#     try:
#         loop = asyncio.get_running_loop()
#         result_future = loop.create_future()

#         tsk = loop.create_task(_popup_input(prompt))
#         tsk.add_done_callback(
#             lambda t: result_future.set_result(t.result())
#         )

#         while not result_future.done():
#             loop.run_until_complete(asyncio.sleep(0.1))

#         return result_future.result()
#     except:
#         return asyncio.run(_popup_input(prompt))

# async def _popup_chat(prompt: str="NONE", end=""):
#     # await OUTPUT_CHAT_QUEUE.put(prompt)
#     response_stream.feed_data(prompt)

from asyncio import Lock

response_lock = Lock()

# dataclass for representing the result of the code completion agent run
@dataclass
class EngineerRunResult(AgentRunResult):
    ...


@dataclass
class EngineerAgentParams(AgentRunParams):
    instructionPrompt: Optional[str] = None


@dataclass
class EngineerProgress(
    AgentProgress
):  # reports what tasks are active and responsible for reporting new tasks
    response: Optional[str] = None
    done_streaming: bool = False


@dataclass
class EngineerAgentState(AgentState):
    model: AbstractCodeCompletionProvider
    params: EngineerAgentParams
    messages: list[openai.Message]
    change_futures: Dict[str, Future] = field(default_factory=dict)


# decorator for creating the code completion agent
@agent(
    agent_description="Specify what you want it to build, the AI asks for clarification, and then builds it.",
    display_name="GPT Engineer",
)
@dataclass
class EngineerAgent(Agent):
    state: EngineerAgentState
    agent_type: ClassVar[str] = "engineer"

    async def _main(
        self,
        prompt: Optional[str] = None,
        project_path: str = "",
        model: str = "gpt-4",
        temperature: float = 0.1,
        steps_config: StepsConfig = StepsConfig.DEFAULT,
        verbose: bool = typer.Option(False, "--verbose", "-v"),
        **kwargs,
    ) -> DBs:

        loop = asyncio.get_event_loop()        
        def _popup_chat_wrapper(prompt: str="NONE", end=""):
            def _worker():
                self.response_stream.feed_data(prompt)
            loop.call_soon_threadsafe(_worker)

        def _popup_input_wrapper(prompt=""):
            return "c"
            # self.state.messages.append(openai.Message.assistant(prompt))
            # t: asyncio.Task = loop.create_task(self.request_chat(RequestChatRequest(messages=self.state.messages)))
            # while not t.done():
            #     # loop.run_until_complete(asyncio.sleep(0.1))
            #     logger.info("LOOPINg")
            #     time.sleep(0.25)
            # return t.result()
        #     # result_future = loop.create_future()
        #     # return asyncio.get_event_loop().call_soon_threadsafe()

        gpt_engineer.ai.print = _popup_chat_wrapper
        gpt_engineer.steps.print = _popup_chat_wrapper
        gpt_engineer.steps.input = _popup_input_wrapper
        self.response_stream = TextStream()

        UPDATES_QUEUE = asyncio.Queue()
        INPUT_PROMPT_QUEUE = asyncio.Queue()
        INPUT_RESPONSE_QUEUE = asyncio.Queue()
        TASK_QUEUE = asyncio.Queue()
        OUTPUT_CHAT_QUEUE = asyncio.Queue()

        STEPS_AGENT_TASKS_NAME_QUEUE = asyncio.Queue()
        STEPS_AGENT_TASKS_EVENT_QUEUE = asyncio.Queue()    
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

        if prompt and not os.path.exists(os.path.join(input_path, "prompt")):
            with open(os.path.join(input_path, "prompt"), "w") as f:
                f.write(prompt)

        memory_path = os.path.join(gpteng_path, "memory")
        workspace_path = os.path.join(input_path) # pipe files directly into the workspace
        archive_path = os.path.join(gpteng_path, "archive")

        dbs = DBs(
            memory=DB(memory_path),
            logs=DB(os.path.join(memory_path, "logs")),
            input=DB(workspace_path),
            workspace=DB(workspace_path, in_memory_dict={}),  # in_memory_dict={}),
            preprompts=DB(Path(gpt_engineer.__file__).parent / "preprompts"),
            archive=DB(archive_path),
        )

        # if steps_config not in [
        #     StepsConfig.EXECUTE_ONLY,
        #     StepsConfig.USE_FEEDBACK,
        #     StepsConfig.EVALUATE,
        # ]:
        #     archive(dbs)

        steps = STEPS[steps_config]
        from concurrent import futures

            # Add all steps to task list
        steps = STEPS[steps_config]
        from concurrent import futures

        step_events: Dict[int, asyncio.Event] = dict()
        for i, step in enumerate(steps):
            event = asyncio.Event()
            step_events[i] = event
            async def _step_task(event: asyncio.Event):
                await event.wait()
            _ = self.add_task(AgentTask(description=step.__name__, task=_step_task, args=[event]))    

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
                    await self.server.apply_workspace_edit(lsp.ApplyWorkspaceEditParams(file_diff.edits_from_file_changes([file_diff.get_file_change(
                        file_path, new_contents
                    ) for file_path, new_contents in updates], user_confirmation=True)))
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


    async def _run_chat_thread(self):
        print("Started handler thread")
        response = ""
        while True:
            try:
                async for delta in self.response_stream:
                    if delta != "NONE":
                        response += delta
                        async with response_lock:
                            await self.send_progress(EngineerProgress(response=response))
                    else:
                        await self.send_progress(EngineerProgress(response=response, done_streaming=True))

                        async with response_lock:
                            self.state.messages.append(openai.Message.assistant(content=response))
            except AttributeError:
                await asyncio.sleep(1)
                continue

    @classmethod
    def create(cls, params: EngineerAgentParams, model, server):
        state = EngineerAgentState(
            model=model,
            params=params,
            messages=[openai.Message.assistant("What do you want to build?")],

        )
        obj = cls(
            state=state,
            agent_id=params.agent_id,
            server=server,
        )

                

        # async def _run_popup_thread(obj):
        #     while True:
        #         try:
        #             prompt = await asyncio.wait_for(INPUT_PROMPT_QUEUE.get(), timeout=1.0)
        #             if prompt != "":
        #                 await asyncio.wait_for(OUTPUT_CHAT_QUEUE.put(prompt), timeout=1.0)
        #             response = await obj.request_chat(RequestChatRequest(messages=obj.state.messages))
        #             async with response_lock:
        #                 obj.state.messages.append(openai.Message.user(content=response))
        #             await INPUT_RESPONSE_QUEUE.put(response)

        #         except asyncio.TimeoutError:
        #             continue

        # async def _run_create_task_thread(obj: EngineerAgent):
        #     while True:
        #         try:
        #             # Wait till we get the name of a new task to spawn
        #             task_name = await asyncio.wait_for(STEPS_AGENT_TASKS_NAME_QUEUE.get(), timeout=1.0)
        #             # Create an event to trigger when the task is complete
        #             event = asyncio.Event()
        #             # Put the event object on the queue so that it can be triggered
        #             await STEPS_AGENT_TASKS_EVENT_QUEUE.put(event)
        #             # Setup the function that will be waiting on the event
        #             async def _event_wait():
        #                 await event.wait()
        #                 return True

        #             _ = asyncio.get_running_loop().create_task(obj.add_task(AgentTask(task_name, _event_wait)).run())

        #             await obj.send_progress()
        #         except asyncio.TimeoutError:
        #             continue

        # asyncio.create_task(_run_create_task_thread(obj))
        # asyncio.create_task(_run_chat_thread(obj))
        # asyncio.create_task(_run_popup_thread(obj))

        return obj


    async def run(self) -> AgentRunResult:  # main entry point
        await self.send_progress()
        asyncio.create_task(self._run_chat_thread())

        async def get_prompt():
            prompt = await self.request_chat(RequestChatRequest(messages=self.state.messages))
            self.state.messages.append(openai.Message.user(prompt))
            return prompt

        get_prompt_task = self.add_task(AgentTask("Get prompt for workspace", get_prompt))
        prompt = await get_prompt_task.run()
        
        await asyncio.create_task(self._main(prompt=prompt, project_path=self.state.params.workspaceFolderPath))
        # counter = 0
        # while (not main_t.done()) or (UPDATES_QUEUE.qsize() > 0):
        #     counter += 1
        #     try:
        #         updates = await asyncio.wait_for(UPDATES_QUEUE.get(), 1.0)
        #         for file_path, new_contents in updates:
        #             await self.server.apply_workspace_edit(lsp.ApplyWorkspaceEditParams(file_diff.edits_from_file_change(file_diff.get_file_change(
        #                 file_path, new_contents
        #             ))))


        #     except asyncio.TimeoutError:
        #         continue
