import asyncio
import json
import os
from dataclasses import dataclass
from typing import AsyncIterable, ClassVar, List, Optional, Type
import rift.util.file_diff as file_diff
from rift.agents.cli_agent import Agent, ClientParams, launcher
from rift.agents.util import ainput

@dataclass
class InferClientParams(ClientParams):
    build: Optional[str] = None  # path to file

@dataclass
class InferAgent(Agent):
    name: ClassVar[str] = "infer"
    run_params: Type[InferClientParams] = InferClientParams
    splash: Optional[
        str
    ] = "--INFER--\n"

    async def run(self) -> AsyncIterable[List[file_diff.FileChange]]:
        params = self.run_params

        # run shell command params.build and wait for completion
        command = ""
        if params.build is not None:
            command = params.build
        else:
            yield []

        report_path = "infer-out/report.json"
        absolute_file_path = os.path.join(os.getcwd(), report_path)
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        # self.console.print(f"stdout: {stdout}")
        # self.console.print(f"stderr: {stderr}")

        # check for error code when running shell command
        if process.returncode != 0:
            raise Exception(f"Error running command: {command}")
    
        new_content = ""
        with open(absolute_file_path, "r") as f:
            new_content = f.read()
            self.console.print(f"Analysis Report:\n{json.dumps(json.loads(new_content), indent=4)}\n")

        await ainput("\n> Press any key to continue.\n")

        file_change = file_diff.get_file_change(path=absolute_file_path, new_content=new_content)
        file_changes = [file_change]
        yield file_changes


if __name__ == "__main__":
    launcher(InferAgent, InferClientParams)
