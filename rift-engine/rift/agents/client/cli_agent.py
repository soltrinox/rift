from typing import Optional
import pickle as pkl
import os
import json
from dataclasses import dataclass
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

@dataclass
class SendUpdateParams:
    msg: str


def splash(name: str):
    _splash = art.text2art(name, font="smslant")

    def stream_string(string):
        for char in string:
            print(char, end="", flush=True)
            time.sleep(0.0015)
            # print('\r', end='')

    stream_string(_splash)


# class RiftClient(RpcServer):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         time.sleep(1)
#         smol_splash()

#     @rpc_request("morph/send_update")
#     async def run(self, params: SendUpdateParams) -> None:
#         ...

#     @rpc_request("initialize")
#     async def initialize(self, params: InitializeParams) -> lsp.InitializeResult:
#         ...

#     @rpc_request("morph/applyWorkspaceEdit")
#     async def apply_workspace_edit(params: lsp.ApplyWorkspaceEditParams) -> lsp.ApplyWorkspaceEditResponse:
#         ...

#     @rpc_request("morph/loadFiles")
#     async def load_files(params: server.LoadFilesParams) -> server.LoadFilesResult:
#         ...


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
    name: str = "smol"
    run_params: Type[SmolAgentRunParams] = SmolAgentRunParams
    splash: str = """

   __                                 __
  / /   but make it...           __   \ \
 | |             ___ __ _  ___  / /    | |
 | |            (_-</  ' \\/ _ \\/ /     | |
 | |           /___/_/_/_/\\___/_/      | |
 | |                                   | |
  \_\                                 /_/



    """

    async def run(params):
        await ainput("\n> Press any key to continue.\n")

        with open(params.prompt_file, "r") as f:
            prompt = f.read()

        logger.info("Starting smol-dev with prompt:")
        console.print(prompt, markup=True, highlight=True)

        await ainput("\n> Press any key to continue.\n")

        def stream_handler(chunk):
            def stream_string(string):
                for char in string:
                    print(char, end="", flush=True)
                    time.sleep(0.0012)

            stream_string(chunk.decode("utf-8"))

        plan = smol_dev.plan(prompt, streamHandler=stream_handler)

        logger.info("Running with plan:")

        console.print(plan, emoji=True, markup=True)

        await ainput("\n> Press any key to continue.\n")

        file_paths = smol_dev.specify_filePaths(prompt, plan)

        logger.info("Got file paths:")
        console.print(json.dumps(file_paths, indent=2), markup=True)

        file_changes = []

        await ainput("\n> Press any key to continue.\n")

        for file_path in file_paths:
            logger.info(f"Generating code for {file_path}")
            code = smol_dev.generate_code(prompt, plan, file_path, streamHandler=stream_handler)
            console.print(
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
    asyncio.sleep(1)
    splash(params.name)

    agent = SmolAgent()

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

@dataclass
class SmolClientParams(ClientParams):
    prompt_file: str

def _main(param_cls):
    params = fire.Fire(param_cls)
    asyncio.run(main(params=params), debug=params.debug)


if __name__ == "__main__":
    import fire

    fire.Fire(ClientParams)
