import asyncio
import dataclasses
import json
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncIterable, ClassVar, Dict, List, Literal, Optional, Type
import rift.util.file_diff as file_diff

logger = logging.getLogger(__name__)
from rift.agents.cli_agent import Agent, ClientParams, launcher
from rift.agents.util import ainput

import aider_dev.aider.main as aider

@dataclass
class AiderAgentParams(ClientParams):
    args : List[str] = field(default_factory=list)
    debug: bool = False


@dataclass
class AiderAgent(Agent):
    name: ClassVar[str] = "aider"
    run_params: Type[AiderAgentParams] = AiderAgentParams
    splash: Optional[
        str
    ] = """
   __    ____  ____  ____  ____ 
  /__\  (_  _)(  _ \( ___)(  _ \\
 /(__)\  _)(_  )(_) ))__)  )   /
(__)(__)(____)(____/(____)(_)\_)

"""

    async def run(self) -> AsyncIterable[List[file_diff.FileChange]]:
        params = self.run_params

        logger.info(f"Aider: args: {params.args}")

        await ainput("\n> Press any key to continue.\n")
        logger.info("Running aider")

        from concurrent import futures
        with futures.ThreadPoolExecutor(1) as pool:
            res = await asyncio.get_running_loop().run_in_executor(pool, aider.main, params.args)

        await ainput("\n> Press any key to continue.\n")

        yield []


if __name__ == "__main__":
    launcher(AiderAgent, AiderAgentParams)
