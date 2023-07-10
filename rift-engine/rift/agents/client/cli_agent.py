import tqdm.asyncio
import inspect
from typing import Optional, ClassVar, Dict
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
from rift.agents.client.util import stream_string, stream_string_ascii


@dataclass
class ClientParams:
    port: int
    debug: bool = False


@dataclass
class CliAgent:
    name: str
    run_params: ClientParams
    splash: Optional[str] = None
    console: Console = field(default_factory=Console)

    async def run(self, *args, **kwargs) -> AsyncIterable[List[file_diff.FileChange]]:
        """
        Emits batches of `file_diff.FileChange`s.
        """
        ...


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
            inspect.Parameter(
                name=field.name,
                kind=inspect.Parameter.POSITIONAL_ONLY,
                default=None,
                annotation=field.type,
            )
            for field in attributes
        ]

        return attributes

    attributes = get_attributes(cls)

    def function(*args):
        """A function whose signature is set to be the dataclass's attributes."""
        return cls(*args)

    function.__signature__ = inspect.Signature(parameters=attributes)
    return function


def launcher(param_cls: Type[ClientParam]):
    import fire

    params = fire.Fire(get_dataclass_function(param_cls))
    asyncio.run(main(params=params), debug=params.debug)
