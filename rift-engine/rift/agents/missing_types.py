import asyncio
from dataclasses import dataclass, field
import functools
import openai
import os
from textwrap import dedent
from typing import AsyncIterable, ClassVar, List, Optional, Type, Dict

from rift.agents.cli_agent import Agent, ClientParams, launcher
from rift.agents.util import ainput
from rift.IR.ir import IR, Code, CodeEdit, Language, language_from_file_extension
from rift.IR.parser import FileMissingTypes, MissingType, files_missing_types_in_project, functions_missing_types_in_ir, parse_code_block
from rift.IR.response import extract_blocks_from_response, replace_functions_from_code_blocks
import rift.util.file_diff as file_diff


class Config:
    temperature = 0

    model = "gpt-3.5-turbo-0613"  # ["gpt-3.5-turbo-0613", "gpt-3.5-turbo-16k"]

    @classmethod
    def root_dir(cls) -> str:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(script_dir) + "/llm"


@dataclass
class MissingTypesParams(ClientParams):
    pass


Message = Dict[str, str]
Prompt = List[Message]


class MissingTypePrompt:
    @staticmethod
    def mk_user_msg(missing_types: List[MissingType], code: Code) -> str:
        missing_str = ""
        n = 0
        for mt in missing_types:
            n += 1
            missing_str += f"{n}. {mt}\n"
        return dedent(f"""
        Add missing types for the following functions:
        {missing_str}

        The code is:
        ```
        {code}
        ```
        """).lstrip()

    @staticmethod
    def code_for_missing_types(missing_types: List[MissingType]) -> Code:
        bytes = b""
        for mt in missing_types:
            bytes += mt.function_declaration.get_substring()
            bytes += b"\n"
        return Code(bytes)

    @staticmethod
    def create_prompt_for_file(missing_types: List[MissingType]) -> Prompt:
        code = MissingTypePrompt.code_for_missing_types(missing_types)
        system_msg = dedent("""
            Act as an expert software developer.
            For each function to modify, give an *edit block* per the example below.

            You MUST format EVERY code change with an *edit block* like this:

            ```python
                def mul(a: t1, b : t2) -> t3
                    ...
            ```

            Every *edit block* must be fenced with ```...``` with the correct code language.
            Edits to different functions each need their own *edit block*.
            Give all the required changes at once in the reply.
            """).lstrip()
        return [
            dict(role="system", content=system_msg),
            dict(role="user", content=MissingTypePrompt.mk_user_msg(
                missing_types=missing_types, code=code)),
        ]


@dataclass
class FileProcess:
    file_missing_types: FileMissingTypes
    edits: List[CodeEdit] = field(default_factory=list)
    file_change: Optional[file_diff.FileChange] = None
    new_num_missing: Optional[int] = None


def count_missing(missing_types: List[MissingType]) -> int:
    return sum([int(mt) for mt in missing_types])


def get_num_missing_in_code(code: Code, language: Language) -> int:
    ir = IR()
    parse_code_block(ir, code, language)
    return count_missing(functions_missing_types_in_ir(ir))


@dataclass
class MissingTypesAgent(Agent):
    name: ClassVar[str] = "missing_types"
    run_params: Type[MissingTypesParams] = MissingTypesParams
    splash: Optional[
        str
    ] = "--MISSING TYPES--\n"
    debug: bool = False
    root_dir: str = Config.root_dir()

    def process_response(self, document: Code, language: Language,  missing_types: List[MissingType], response: str) -> List[CodeEdit]:
        if self.debug:
            self.console.print(f"response:\n{response}\n")
        code_blocks = extract_blocks_from_response(response)
        if self.debug:
            self.console.print(f"code_blocks:\n{code_blocks}\n")
        filter_function_ids = [
            mt.function_declaration.get_qualified_id() for mt in missing_types]
        edits = replace_functions_from_code_blocks(
            code_blocks=code_blocks, document=document,
            filter_function_ids=filter_function_ids, language=language, replace_body=False)
        return edits

    async def code_edits_for_missing_files(self, document: Code, language: Language,  missing_types: List[MissingType]) -> List[CodeEdit]:
        loop = asyncio.get_event_loop()
        prompt = MissingTypePrompt.create_prompt_for_file(
            missing_types=missing_types)
        func = functools.partial(
            openai.ChatCompletion.create, model=Config.model,
            messages=prompt, temperature=Config.temperature)
        completion = await loop.run_in_executor(None, func)
        if not isinstance(completion, dict):
            raise Exception(
                f"Unexpected type for completion: {type(completion)}")
        response: str = completion['choices'][0]['message']['content']
        edits = self.process_response(
            document=document, language=language, missing_types=missing_types, response=response)
        return edits

    async def process_file(self, file_process: FileProcess) -> None:
        fmt = file_process.file_missing_types
        self.console.print(
            f"Fetching types for `{fmt.path_from_root}`")
        api_key = os.environ["OPENAI_API_KEY"]
        if api_key is None:
            raise Exception("OPENAI_API_KEY environment variable not set")
        openai.api_key = api_key

        language = fmt.language
        document = fmt.code
        missing_types = fmt.missing_types

        new_edits = await self.code_edits_for_missing_files(document, language, missing_types)

        file_process.edits += new_edits
        new_document = fmt.code.apply_edits(file_process.edits)
        old_num_missing = count_missing(
            file_process.file_missing_types.missing_types)
        new_num_missing = get_num_missing_in_code(new_document, fmt.language)
        self.console.print(
            f"Received types for `{fmt.path_from_root}` ({new_num_missing}/{old_num_missing} missing)")
        if self.debug:
            self.console.print(f"new_document:\n{new_document}\n")
        path = os.path.join(self.root_dir, fmt.path_from_root)
        file_change = file_diff.get_file_change(
            path=path, new_content=str(new_document))
        if self.debug:
            self.console.print(f"file_change:\n{file_change}\n")
        file_process.file_change = file_change
        file_process.new_num_missing = new_num_missing

    async def run(self) -> AsyncIterable[List[file_diff.FileChange]]:
        def print_missing(fmt: FileMissingTypes) -> None:
            self.console.print(f"File: {fmt.path_from_root}")
            for mt in fmt.missing_types:
                self.console.print(f"  {mt}")
            self.console.print()

        file_processes: List[FileProcess] = []
        tot_num_missing = 0
        files_missing_types = files_missing_types_in_project(self.root_dir)
        for fmt in files_missing_types:
            print_missing(fmt)
            tot_num_missing += count_missing(fmt.missing_types)
            file_processes.append(FileProcess(
                file_missing_types=fmt))

        await ainput("\n> Press any key to continue.\n")

        tasks: List[asyncio.Task] = [
            asyncio.create_task(self.process_file(file_processes[i]))
            for i in range(len(files_missing_types))
        ]
        await asyncio.gather(*tasks)

        file_changes: List[file_diff.FileChange] = []
        tot_new_missing = 0
        for fp in file_processes:
            if fp.file_change is not None:
                file_changes.append(fp.file_change)
            if fp.new_num_missing is not None:
                tot_new_missing += fp.new_num_missing
            else:
                tot_new_missing += count_missing(
                    fp.file_missing_types.missing_types)
        self.console.print(
            f"Missing types: {tot_new_missing}/{tot_num_missing} ({tot_new_missing/tot_num_missing*100:.2f}%)")
        yield file_changes


if __name__ == "__main__":
    launcher(MissingTypesAgent, MissingTypesParams)