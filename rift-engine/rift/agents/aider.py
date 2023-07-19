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

try:
    import aider
except ImportError:
    raise Exception("`aider` not found. Try `pip install aider-chat`")

@dataclass
class AiderAgentParams(ClientParams):
    prompt_file: Optional[str] = None  # path to prompt file
    debug: bool = False
    model: Literal["gpt-3.5-turbo-0613", "gpt-4-0613"] = "gpt-3.5-turbo-0613"


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
        await ainput("\n> Press any key to continue.\n")

        if params.prompt_file is None:
            prompt = await ainput("\n> Prompt file not found. Please input a prompt.\n")
        else:
            with open(params.prompt_file, "r") as f:
                prompt = f.read()

        logger.info("Starting aider with prompt:")
        self.console.print(prompt, markup=True, highlight=True)

        await ainput("\n> Press any key to continue.\n")

        yield []


if __name__ == "__main__":
    launcher(AiderAgent, AiderAgentParams)
