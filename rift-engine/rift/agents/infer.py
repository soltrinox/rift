import asyncio
import json
import os
from dataclasses import dataclass
from typing import AsyncIterable, ClassVar, List, Optional, Type, Dict
import rift.util.file_diff as file_diff
from rift.agents.cli_agent import Agent, ClientParams, launcher
from rift.agents.util import ainput
from rift.IR.ir import language_from_file_extension
from textwrap import dedent
import openai

@dataclass
class InferClientParams(ClientParams):
    build: Optional[str] = None  # build command

@dataclass
class Bug:
    type: str
    file: str
    line: int
    column: int
    description: str
    across_files: bool

class BugfixPrompt:
    @staticmethod
    def mk_user_msg(function: str, bug:str, code:str) -> str: return dedent(f"""
        Fix the error reported by static analysis in function `{function}` as: "{bug}"

        The code is:
        {code}
        """).lstrip()

    @staticmethod
    def create_from_bug(bug: Bug, files: Dict[str, str]) -> List[Dict[str, str]]:
        system_msg = dedent("""
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
            """).lstrip()
        return [
            dict(role="system", content=system_msg),
            dict(role= "user", content=BugfixPrompt.mk_user_msg(bug.file, bug.description, files[bug.file])),
        ]

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
        absolute_report_path = os.path.join(os.getcwd(), report_path)
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
        # Keep a db of file contenst: for each file name, the content of the file
        files : Dict[str, str] = {}
        bugs : List[Bug] = []
        def read_file(file_path: str) -> None:
            if file_path not in files:
                with open(file_path, "r") as f:
                    files[file_path] = f.read()
        with open(absolute_report_path, "r") as report:
            report_json = json.loads(report.read())
            for issue in report_json:
                file = issue["file"]
                bug_trace = issue["bug_trace"]
                across_files = False
                for bug_trace_item in bug_trace:
                    if bug_trace_item["filename"] != file:
                        across_files = True
                        break
                read_file(file)
                bug = Bug(type=issue["bug_type"],
                          file=file,
                          line=issue["line"],
                          column=issue["column"],
                          description=issue["qualifier"],
                          across_files=across_files)
                bugs.append(bug)
                # self.console.print(f"Issue (across files:{issue_is_across_files}):\n{json.dumps(issue, indent=4)}\n")
        self.console.print(f"bugs:\n{bugs}\n")
        self.console.print(f"files:\n{files}\n")

        await ainput("\n> Press any key to continue.\n")

        prompts: List[List[Dict[str, str]]] = []
        for bug in bugs:
            if not bug.across_files: # TODO: handle across files
                prompts.append(BugfixPrompt.create_from_bug(bug, files))

        self.console.print(f"prompts:\n{prompts}\n")

        file_changes: List[file_diff.FileChange] = []
        if len(prompts) > 0:
            # Try to fix the first bug
            messages = prompts[0]
            api_key = os.environ["OPENAI_API_KEY"]
            if api_key is None:
                raise Exception("OPENAI_API_KEY environment variable not set")
            openai.api_key = api_key
            res = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            # check if res has type dict
            if not isinstance(res, dict):
                raise Exception(f"Unexpected type for res: {type(res)}")
            response = res['choices'][0]['message']
            self.console.print(f"response:\n{response}\n")
            from rift.IR.ir import Language
            from rift.llm.response import extract_blocks_from_response, replace_functions_from_code_blocks
            code_blocks = extract_blocks_from_response(response["content"])
            self.console.print(f"code_blocks:\n{code_blocks}\n")
            bug0 = bugs[0]
            document = files[bug0.file]
            language = language_from_file_extension(bug0.file)
            if language is not None:
                new_document = replace_functions_from_code_blocks(code_blocks=code_blocks, document=document, language=language)
                self.console.print(f"new_document:\n{new_document}\n")
                path = os.path.join(os.getcwd(), bug0.file)
                file_change = file_diff.get_file_change(path=path, new_content=new_document)
                self.console.print(f"file_change:\n{file_change}\n")
                file_changes.append(file_change)
        await ainput("\n> Press any key to continue.\n")

        yield file_changes

if __name__ == "__main__":
    launcher(InferAgent, InferClientParams)
