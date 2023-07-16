import asyncio
import json
import os
from dataclasses import dataclass
from typing import AsyncIterable, ClassVar, List, Optional, Type
import rift.util.file_diff as file_diff
from rift.agents.cli_agent import Agent, ClientParams, launcher
from rift.agents.util import ainput
from textwrap import dedent


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

system_msg = """
Act as an expert software developer.
Once you understand the bug report:
1. List the functions you need to change to fix the bug.
2. For each function to modify, give an *edit block* per the example below.

You MUST format EVERY code change with an *edit block* like this:

```python
    def mul(a,b)
        the fixed code
```

Every *edit block* must be fenced with ```...``` with the correct code language.
Edits to different functions each need their own *edit block*.
Give all the required changes at once in the reply.
"""

def mk_user_msg(function: str, bug:str, code:str) -> str: return f"""
Fix the error reported by static analysis in function `{function}` as: "{bug}"

The code is:
{code}
"""

def user() -> str:
    function = "main"
    bug = "pointer `x` last assigned on line 15 could be null and is dereferenced at line 16, column 3."
    code = dedent("""
        int aa() {
          return 0;
        }

        void foo(int **x) {
          *x = 0;
        }

        int bb() {
          return 0;
        }

        int main() {
          int *x;
          foo(&x);
          *x = 1;
          return 0;
        }
    """).lstrip()
    return mk_user_msg(function, bug, code)

if __name__ == "__main__":
    launcher(InferAgent, InferClientParams)
