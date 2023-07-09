import inspect
from typing import Optional, ClassVar
import pickle as pkl
import os
import json
from dataclasses import dataclass, field
import dataclasses
import asyncio
import logging
from typing import Any, List, AsyncIterable, Type
import smol_dev

import rift.lsp.types as lsp
from rift.agents.abstract import AgentRegistryResult
from rift.lsp.types import InitializeParams
from rift.rpc.io_transport import AsyncStreamTransport
from rift.rpc.jsonrpc import RpcServer, rpc_method, rpc_request
from rift.server.core import CodeCapabilitiesServer, rift_splash
from rift.util.ofdict import todict
import rift.agents.file_diff as file_diff
from rift.server.core import rift_splash
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
import logging
import rift.server.lsp as server
import rift.server.core as core

logger = logging.getLogger(__name__)
import time
import art

import fire
import types

def _PrintResult(component_trace, verbose=False, serialize=None):
  result = component_trace.GetResult()
  if serialize:
    if not callable(serialize):
      raise fire.core.FireError(
          'The argument `serialize` must be empty or callable:', serialize)
    result = serialize(result)

  if fire.value_types.HasCustomStr(result):
    print(str(result))
    return

  if isinstance(result, (list, set, frozenset, types.GeneratorType)):
    for i in result:
      print(fire.core._OneLineResult(i))
  elif inspect.isgeneratorfunction(result):
    raise NotImplementedError
  elif isinstance(result, dict) and value_types.IsSimpleGroup(result):
    print(fire.core._DictAsString(result, verbose))
  elif isinstance(result, tuple):
    print(fire.core._OneLineResult(result))
  elif dataclasses._is_dataclass_instance(result):
    print(fire.core._OneLineResult(result))    
  elif isinstance(result, value_types.VALUE_TYPES):
    if result is not None:
      print(result)
  else:
    help_text = fire.helptext.HelpText(
        result, trace=component_trace, verbose=verbose)
    output = [help_text]
    Display(output, out=sys.stdout)

fire.core._PrintResult = _PrintResult


@dataclass
class SendUpdateParams:
    msg: str


def stream_string(string):
    for char in string:
        print(char, end="", flush=True)
        time.sleep(0.0015)    

def stream_string_ascii(name: str):
    _splash = art.text2art(name, font="smslant")

    stream_string(_splash)


async def main():
    reader, writer = await asyncio.open_connection("127.0.0.1", 7797)
    transport = AsyncStreamTransport(reader, writer)
    client = RiftClient(transport=transport)


import asyncio
from concurrent.futures import ThreadPoolExecutor


async def ainput(prompt: str = "") -> str:
    with ThreadPoolExecutor(1, "AsyncInput") as executor:
        return await asyncio.get_event_loop().run_in_executor(executor, input, prompt)

@dataclass
class CliAgent:
    name: str
    run_params: Any
    splash: Optional[str] = None
    console: Console = field(default_factory=Console)    

    async def run(self, *args, **kwargs) -> AsyncIterable[List[file_diff.FileChange]]:
        """
        Emits batches of `file_diff.FileChange`s.
        """
        ...

@dataclass
class SmolAgentRunParams:
    prompt_file: str # path to prompt file
    debug: bool = False


@dataclass
class SmolAgent(CliAgent):
    name: ClassVar[str] = "smol"
    run_params: Type[SmolAgentRunParams] = SmolAgentRunParams
    splash: Optional[str] = """\


   __                                 __
  / /   but make it...           __   \ \      
 | |             ___ __ _  ___  / /    | |      
 | |            (_-</  ' \\/ _ \\/ /     | |      
 | |           /___/_/_/_/\\___/_/      | |      
 | |                                   | |      
  \_\                                 /_/       



    """

    async def run(self):
        params = self.run_params
        await ainput("\n> Press any key to continue.\n")

        with open(params.prompt_file, "r") as f:
            prompt = f.read()

        logger.info("Starting smol-dev with prompt:")
        self.console.print(prompt, markup=True, highlight=True)

        await ainput("\n> Press any key to continue.\n")

        def stream_handler(chunk):
            def stream_string(string):
                for char in string:
                    print(char, end="", flush=True)
                    time.sleep(0.0012)

            stream_string(chunk.decode("utf-8"))

        plan = smol_dev.plan(prompt, streamHandler=stream_handler)

        logger.info("Running with plan:")

        self.console.print(plan, emoji=True, markup=True)

        await ainput("\n> Press any key to continue.\n")

        file_paths = smol_dev.specify_filePaths(prompt, plan)

        logger.info("Got file paths:")
        self.console.print(json.dumps(file_paths, indent=2), markup=True)

        file_changes = []

        await ainput("\n> Press any key to continue.\n")

        for file_path in file_paths:
            logger.info(f"Generating code for {file_path}")
            code = smol_dev.generate_code(prompt, plan, file_path, streamHandler=stream_handler)
            self.console.print(
                f"""```\
                {code}
                ```
                """,
                markup=True,
            )
            absolute_file_path = os.path.join(os.getcwd(), file_path)
            logger.info(f"Generating a diff for {absolute_file_path}")
            file_change = file_diff.get_file_change(path=absolute_file_path, new_content=code)
            yield [file_change]


async def main(params):
    FORMAT = "%(message)s"
    console = Console(stderr=True)
    logging.basicConfig(
        level=logging.DEBUG if params.debug else logging.INFO,
        format=FORMAT,
        datefmt="[%X]",
        handlers=[RichHandler(console=console)],
    )
    client: core.CodeCapabilitiesServer = core.create_metaserver(port=params.port)
    logger.info(f"started Rift server on port {params.port}")
    t = asyncio.create_task(client.run_forever())
    await asyncio.sleep(1)
    if SmolAgent.splash is not None:
        stream_string(SmolAgent.splash)
    else:
        stream_string_ascii(SmolAgent.name)

    agent = SmolAgent(run_params=params, console=console)

    async for file_changes in agent.run():
        await client.server.apply_workspace_edit(
            lsp.ApplyWorkspaceEditParams(
                file_diff.edits_from_file_changes(file_changes, user_confirmation=True),
                label="rift",
            )
        )

    await t


@dataclass
class ClientParams:
    port: int
    debug: bool = False

def get_dataclass_function(cls):
    """Returns a function whose signature is set to be a list of arguments
    which are precisely the dataclass's attributes.

    Args:
        dataclass: The dataclass to get the function for.

    Returns:
        The function whose signature is set to be a list of arguments
        which are precisely the dataclass's attributes.
    """

    def get_attributes(cls):
        attributes = []
        for field in dataclasses.fields(cls):
            if isinstance(field.type, cls):
                attributes.extend(dataclasses.fields(field.type).keys())
            else:
                attributes.append(field)

        attributes = [
            inspect.Parameter(name=field.name, kind=inspect.Parameter.POSITIONAL_ONLY, default=None, annotation=field.type)
            for field in attributes
        ]

        return attributes

    attributes = get_attributes(cls)

    def function(*args):
        """A function whose signature is set to be the dataclass's attributes."""
        return cls(*args)

    function.__signature__ = inspect.Signature(parameters=attributes)
    return function

@dataclass
class SmolClientParams(ClientParams):
    prompt_file: Optional[str] = None

    def __post_init__(self):
        assert self.prompt_file is not None

def _main(param_cls):
    params = fire.Fire(param_cls)
    asyncio.run(main(params=params), debug=params.debug)


if __name__ == "__main__":
    import fire
    params = fire.Fire(get_dataclass_function(SmolClientParams))
    asyncio.run(main(params=params), debug=params.debug)
    
