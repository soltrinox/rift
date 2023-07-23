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
        """
        Example use:
            python -m rift.agents.aider --port 7797 --debug False --args '["--model", "gpt-3.5-turbo", "rift/agents/aider.py"]'
        """
        params = self.run_params

        logger.info(f"Aider: args: {params.args}")

        await ainput("\n> Press any key to continue.\n")

        logger.info("Running aider")

        file_changes: List[file_diff.FileChange] = []

        # This is called every time aider writes a file
        # Instead of writing, this stores the file change in a list
        def on_write(filename: str, new_content: str):
            file_changes.append(file_diff.get_file_change(path=filename, new_content=new_content))
            logger.info(f"Intercepted Write to {filename}")

        # This is called when aider wants to commit after writing all the files
        # This is where the user should accept/reject the changes
        def on_commit():
            logger.info("Intercepted Commit")

        from concurrent import futures
        with futures.ThreadPoolExecutor(1) as pool:
            res = await asyncio.get_running_loop().run_in_executor(
                pool, aider.main, params.args, on_write, on_commit)

        await ainput("\n> Press any key to continue.\n")

        yield []


if __name__ == "__main__":
    launcher(AiderAgent, AiderAgentParams)
