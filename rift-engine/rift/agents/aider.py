import time
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
        event = asyncio.Event()
        event2 = asyncio.Event()

        # Current state:
        # - Intercept writes and commits: this should take care of the file changes
        # - For interactions, need to intercept: 
        #       io.confirm_ask
        #       io.get_input
        #       io.prompt_ask
        #       io.tool_error
        #       io.tool_output
        #       io.user_input


        # This is called every time aider writes a file
        # Instead of writing, this stores the file change in a list
        def on_write(filename: str, new_content: str):
            file_changes.append(file_diff.get_file_change(path=filename, new_content=new_content))
            # loop.call_soon_threadsafe(lambda: event.set())
            # yield [file_diff.get_file_change(path=filename, new_content=new_content)]

            
            # logger.info(f"Intercepted Write to {filename}")
            
        # This is called when aider wants to commit after writing all the files
        # This is where the user should accept/reject the changes
        loop = asyncio.get_running_loop()

        def on_commit():
            loop.call_soon_threadsafe(lambda: event.set())
            while True:
                if not event2.is_set():
                    time.sleep(0.25)
                    continue
                break
            input("> Press any key to continue.\n")
            
            

        from concurrent import futures
        # asyncio.get_running_loop().set_default_executor(futures.ThreadPoolExecutor(8))
        # aider_fut = asyncio.to_thread(aider.main, params.args, on_write, on_commit)
        with futures.ThreadPoolExecutor(1) as pool:
            aider_fut = asyncio.get_running_loop().run_in_executor(
                pool, aider.main, params.args, on_write, on_commit
            )

        # await ainput("\n> Press any key to continue.\n")

            while True:
                await event.wait()
                yield file_changes
                file_changes = []
                event2.set()
                event.clear()


if __name__ == "__main__":
    launcher(AiderAgent, AiderAgentParams)
