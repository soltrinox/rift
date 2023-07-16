import asyncio
import inspect
import threading
import typing

try:
    import gpt_engineer
    import gpt_engineer.chat_to_files
    import gpt_engineer.db
except ImportError:
    raise Exception("`gpt_engineer` not found. Try `pip install gpt-engineer`")

UPDATES_QUEUE = asyncio.Queue()
SEEN = set()


def to_files(chat, workspace: gpt_engineer.db.DB):
    workspace["all_output.txt"] = chat
    files = gpt_engineer.chat_to_files.parse_chat(chat)

    for file_name, file_content in files:
        workspace[file_name] = file_content

# Assign a new to_files function that passes updates to the queue.
gpt_engineer.chat_to_files.to_files = to_files

from gpt_engineer.ai import AI, fallback_model
from gpt_engineer.collect import collect_learnings
from gpt_engineer.db import DB, DBs, archive
from gpt_engineer.learning import collect_consent
from gpt_engineer.steps import STEPS
from gpt_engineer.steps import Config as StepsConfig

import json
import logging
import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from queue import Queue

import rift.agents.cli_agent as agent
import rift.lsp.types as lsp
import rift.util.file_diff as file_diff
import typer


async def _main(
    project_path: str,
    model: str,
    temperature: float = 0.1,
    steps_config: StepsConfig = typer.Option(
        StepsConfig.DEFAULT, "--steps", "-s", help="decide which steps to run"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    **kwargs,
) -> DBs:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    model = fallback_model(model)
    ai = AI(
        model=model,
        temperature=temperature,
    )

    input_path = Path(project_path).absolute()
    memory_path = input_path / "memory"
    workspace_path = input_path / "workspace"
    archive_path = input_path / "archive"

    dbs = DBs(
        memory=DB(memory_path),
        logs=DB(memory_path / "logs"),
        input=DB(input_path),
        workspace=DB(workspace_path, in_memory_dict={}),  # in_memory_dict={}),
        preprompts=DB(Path(gpt_engineer.__file__).parent / "preprompts"),
        archive=DB(archive_path),
    )

    if steps_config not in [
        StepsConfig.EXECUTE_ONLY,
        StepsConfig.USE_FEEDBACK,
        StepsConfig.EVALUATE,
    ]:
        archive(dbs)

    steps = STEPS[steps_config]
    # async def execute_steps():

    for step in steps:
        await asyncio.sleep(0.1)
        messages = step(ai, dbs) # when `step.__name__` == `gen_entrypoint`, this proposes another diff for the `run.sh` shell script that you will also want to accept
        # then all the files and `run.sh` should be SAVED before you accept the proposal to run the entrypoint
        await asyncio.sleep(0.1)
        dbs.logs[step.__name__] = json.dumps(messages)
        
        items = list(dbs.workspace.in_memory_dict.items())
        if len([x for x in items if x[0] not in SEEN]) > 0:
            await UPDATES_QUEUE.put([x for x in items if x[0] not in SEEN])
            for x in items:
                if x[0] in SEEN:
                    pass
                else:
                    SEEN.add(x[0])
        await asyncio.sleep(0.5)

        # TODO(pranav): uncomment this and increase the sleep duration as needed to make sure you can approve all the diffs before the entrypoint is generated --- this delays the appearance of the "run_entrypoint" step
        # if step.__name__ == "gen_entrypoint":
        #     await asyncio.sleep(3) # increase as needed

        # steps:
        # get the above flow working with the ugly ascii art
        # fix the ascii art somehow (better fonts, etc)
        # run it from top to bottom with the following script:
        # contents of `prompt` should be
        # write a reference implementation of order matching engine in Python
        # during the clarification stage, specify that the order matching engine should run behind an HTTP server with an endpoint called `place_order` which accepts an `order` argument where an `order` is a JSON message of the shape `{order_type: Literal["market", "limit"], amount: float}` and which returns a boolean `{order_placed: boolean}`

        # make sure that we run with gpt-4 for the camera ready

    # execute_steps_ = execute_steps()

    # if collect_consent():
    #     collect_learnings(model, temperature, steps, dbs)

    # dbs.logs["token_usage"] = ai.format_token_usage_log()
    # return dbs.workspace


@dataclass
class GPTEngineerAgentParams(agent.ClientParams):
    project_path: str = "projects/example"
    model: str = "gpt-4"
    temperature: float = 0.1
    steps_config: gpt_engineer.steps.Config = "default"
    verbose: bool = False


@dataclass
class GPTEngineerAgent(agent.Agent):
    name: str = "gpt-engineer"
    run_params: typing.Type[agent.ClientParams] = GPTEngineerAgentParams
    splash: typing.Optional[
        str
    ] = """\



                █████████          ██████  ██████  ████████
             █████   ████         ██       ██   ██    ██
           ████   ████      ██    ██   ███ ██████     ██
          ███    ███     ██████   ██    ██ ██         ██
          ███     █████████ ███    ██████  ██         ██
           ███      ████   ████
         ████             ███
      ████    █████████████       ███████ ███    ██  ██████
   █████    ████                  ██      ████   ██ ██
  ███     ████                    █████   ██ ██  ██ ██   ███
  ███   ███                       ██      ██  ██ ██ ██    ██
   ██████                         ███████ ██   ████  ██████




"""

    async def run(self) -> typing.AsyncIterable[typing.List[file_diff.FileChange]]:
        from dataclasses import dataclass, fields

        def iter_fields(obj):
            for field in fields(obj):
                yield field.name, getattr(obj, field.name)

        params_dict = {k: v for k, v in iter_fields(self.run_params)}

        main_t = asyncio.create_task(_main(**params_dict))

        counter = 0
        while (not main_t.done()) or (UPDATES_QUEUE.qsize() > 0):
            counter += 1
            try:
                updates = await asyncio.wait_for(UPDATES_QUEUE.get(), 1.0)
                yield [
                    file_diff.get_file_change(file_path, new_contents, annotation_label=str(counter))
                    for file_path, new_contents in updates
                ]
            except asyncio.TimeoutError:
                continue


if __name__ == "__main__":
    agent.launcher(GPTEngineerAgent, GPTEngineerAgentParams)
