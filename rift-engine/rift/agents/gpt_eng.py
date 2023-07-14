import asyncio
import typing
try:
    import gpt_engineer
except ImportError:
    raise Exception("`gpt_engineer` not found. Try `pip install gpt-engineer`")

import rift.agents.cli_agent as agent
import rift.util.file_diff as file_diff
import rift.lsp.types as lsp


from dataclasses import dataclass

import json
import logging

from pathlib import Path

import typer

from gpt_engineer.ai import AI, fallback_model
from gpt_engineer.collect import collect_learnings
from gpt_engineer.db import DB, DBs, archive
from gpt_engineer.learning import collect_consent
from gpt_engineer.steps import STEPS, Config as StepsConfig

to_update = []
def me(res):
    to_update.add(res)

def _main(
    project_path: str = typer.Argument("projects/example", help="path"),
    model: str = typer.Argument("gpt-4", help="model id string"),
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
        workspace=DB(workspace_path), #in_memory_dict={}),
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
    for step in steps:
        messages = step(ai, dbs)
        dbs.logs[step.__name__] = json.dumps(messages)

    # if collect_consent():
    #     collect_learnings(model, temperature, steps, dbs)

    # dbs.logs["token_usage"] = ai.format_token_usage_log()
    return dbs.workspace

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

        # Create a queue for updates.
        queue = asyncio.Queue()

        # Assign a new to_files function that passes updates to the queue.
        gpt_engineer.chat_to_files.to_files = lambda chat, workspace: to_files(chat, workspace, queue)

        # Run main function and send updates from the queue.
        try:
            main_task = asyncio.create_task(_main(**params_dict))
            while not main_task.done():
                workspace = await queue.get()
                yield [file_diff.get_file_change(file_path, new_contents) 
                    for file_path, new_contents in workspace.items()]
        finally:
            # Cleanup: cancel the main_task if it is still running.
            if not main_task.done():
                main_task.cancel()
                try:
                    await main_task
                except asyncio.CancelledError:
                    pass

if __name__ == "__main__":
    agent.launcher(GPTEngineerAgent, GPTEngineerAgentParams)
