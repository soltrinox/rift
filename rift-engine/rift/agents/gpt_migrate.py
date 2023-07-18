import asyncio
from collections import defaultdict
import inspect
import os
import threading
import time
import typing

from rift.agents.gpt_migrate_.ai import AI
from rift.agents.gpt_migrate_.main import Globals
from rift.agents.gpt_migrate_.steps.debug import debug_error, debug_testfile
from rift.agents.gpt_migrate_.steps.migrate import add_env_files, get_dependencies, write_migration
from rift.agents.gpt_migrate_.steps.setup import create_environment
from rift.agents.gpt_migrate_.steps.test import create_tests, run_dockerfile, run_test, validate_tests
from rift.agents.gpt_migrate_.utils import build_directory_structure, detect_language

UPDATES_QUEUE = asyncio.Queue()

# Assign a new to_files function that passes updates to the queue.
#gpt_engineer.chat_to_files.to_files = to_files

import json
import logging
import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from queue import Queue

import rift.agents.cli_agent as agent
import rift.lsp.types as lsp
import rift.util.file_diff as file_diff

SEEN = set()
async def _main(
    model = "gpt-4",
    temperature= 0,
    sourcelang= None,
    sourceentry = "app.py",
    targetlang= "rust",
    operating_system= "linux",
    testfiles= "app.py",
    sourceport= None,
    targetport = 8080,
    guidelines = "",
    step = "migrate",
    verbose = False,
    **kwargs,
):
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    ai = AI(
        model=model,
        temperature=temperature,
    )

    #TODO: replace /w rift
    sourcedir = "/Users/jwd2488/Documents/repos/rift/rift-engine/rift/agents/benchmarks/flask-rust/source"
    targetdir = "/Users/jwd2488/Documents/repos/rift/rift-engine/rift/agents/benchmarks/flask-rust/target"
    os.makedirs(targetdir, exist_ok=True)

    #detected_language = detect_language(sourcedir) if not sourcelang else sourcelang

    #if not sourcelang:
    #    if detected_language:
            #is_correct = typer.confirm(f"Is your source project a {detected_language} project?")
            #f is_correct:
    #            sourcelang = detected_language
    ##        else:
     #           sourcelang = typer.prompt("Please enter the correct language for the source project")
     #   else:
     #       sourcelang = typer.prompt("Unable to detect the language of the source project. Please enter it manually")

    source_directory_structure = build_directory_structure(sourcedir)
    globals = Globals(sourcedir, targetdir, sourcelang, targetlang, sourceentry, source_directory_structure, operating_system, testfiles, sourceport, targetport, guidelines, ai, {})

    logging.info(f"◐ Reading {sourcelang} project from directory '{sourcedir}', with entrypoint '{sourceentry}'.")
    #typer.echo(typer.style(f"◐ Reading {sourcelang} project from directory '{sourcedir}', with entrypoint '{sourceentry}'.", fg=typer.colors.BLUE))
    #time.sleep(0.3)
    logging.info(f"◑ Outputting {targetlang} project to directory '{targetdir}'.")
    #typer.echo(typer.style(f"◑ Outputting {targetlang} project to directory '{targetdir}'.", fg=typer.colors.BLUE))
    #time.sleep(0.3)
    logging.info(f"Source directory structure: \n\n" + source_directory_structure)
    logging.info(step)
    step='all'
    ''' 1. Setup '''
    if step in ['setup', 'all']:

        # Set up environment (Docker)
        create_environment(globals)
        items = list(globals.callback.items())
        if len([x for x in items if x[0] not in SEEN]) > 0:
            await UPDATES_QUEUE.put([x for x in items if x[0] not in SEEN])
            for x in items:
                if hash(x) in SEEN:
                    pass
                else:
                    SEEN.add(hash(x))
        await asyncio.sleep(0.5)
    

    ''' 2. Migration '''
    if step in ['migrate', 'all']:
        target_deps_per_file = defaultdict(list) 
        async def migrate(sourcefile, globals, parent_file=None):
            # recursively work through each of the files in the source directory, starting with the entrypoint.
            internal_deps_list, external_deps_list = get_dependencies(sourcefile=sourcefile,globals=globals)
            for dependency in internal_deps_list:
                await migrate(dependency, globals, parent_file=sourcefile)
            await asyncio.sleep(0.5)
            file_name = write_migration(sourcefile, external_deps_list, target_deps_per_file.get(sourcefile), globals)
            items = list(globals.callback.items())
            if len([x for x in items if x[0] not in SEEN]) > 0:
                    await UPDATES_QUEUE.put([x for x in items if x[0] not in SEEN])
                    for x in items:
                        if hash(x) in SEEN:
                            pass
                        else:
                            SEEN.add(hash(x))

            target_deps_per_file[parent_file].append(file_name)

        await migrate(sourceentry, globals)
        add_env_files(globals)
        if len([x for x in items if x[0] not in SEEN]) > 0:
            await UPDATES_QUEUE.put([x for x in items if x[0] not in SEEN])
            for x in items:
                if hash(x) in SEEN:
                    pass
                else:
                    SEEN.add(hash(x))

    ''' 3. Testing '''
    if step in ['test', 'all']:
        while True:
            result = run_dockerfile(globals)
            if result=="success": break
            debug_error(result,"",globals)
        for testfile in globals.testfiles.split(','):
            generated_testfile = create_tests(testfile,globals)
            if globals.sourceport:
                while True:
                    result = validate_tests(generated_testfile, globals)
                    time.sleep(0.3)
                    if result=="success": break
                    debug_testfile(result,testfile,globals)
            while True:
                result = run_test(generated_testfile, globals)
                if result=="success": break
                debug_error(result,globals.testfiles,globals)
                run_dockerfile(globals)
                time.sleep(1) # wait for docker to spin up
    
    typer.echo(typer.style("All tests complete. Ready to rumble. 💪", fg=typer.colors.GREEN))



@dataclass
class GPTMigrateAgentParams(agent.ClientParams):
    model = "gpt-4",
    temperature= 0,
    sourcelang= None,
    sourceentry = "app.py",
    targetlang= "rust",
    operating_system= "linux",
    testfiles= "app.py",
    sourceport= None,
    targetport = 8080,
    guidelines = "",
    step = "migrate",
    verbose = False,


@dataclass
class GPTMigrateAgent(agent.Agent):
    name: str = "gpt-migrate"
    run_params: typing.Type[agent.ClientParams] = GPTMigrateAgentParams
    splash :typing.Optional[
        str
    ] = """\


 .d8888b.  8888888b. 88888888888                                               
d88P  Y88b 888   Y88b    888                                                   
888    888 888    888    888                                                   
888        888   d88P    888                                                   
888  88888 8888888P"     888                                                   
888    888 888           888                                                   
Y88b  d88P 888           888                                                   
 "Y8888P88 888           888                                                   
                                                                               
                                                                               
                                                                               
888b     d888 8888888 .d8888b.  8888888b.         d8888 88888888888 8888888888 
8888b   d8888   888  d88P  Y88b 888   Y88b       d88888     888     888        
88888b.d88888   888  888    888 888    888      d88P888     888     888        
888Y88888P888   888  888        888   d88P     d88P 888     888     8888888    
888 Y888P 888   888  888  88888 8888888P"     d88P  888     888     888        
888  Y8P  888   888  888    888 888 T88b     d88P   888     888     888        
888   "   888   888  Y88b  d88P 888  T88b   d8888888888     888     888        
888       888 8888888 "Y8888P88 888   T88b d88P     888     888     8888888888 
                                                                               
                                                                               
                                                                               

    """

    async def run(self) -> typing.AsyncIterable[typing.List[file_diff.FileChange]]:
        from dataclasses import dataclass, fields

        def iter_fields(obj):
            for field in fields(obj):
                yield field.name, getattr(obj, field.name)

        params_dict = {k: v for k, v in iter_fields(self.run_params)}

        main_t = asyncio.create_task(_main(**params_dict))

        counter = 0
        while (not main_t.done()) or (UPDATES_QUEUE.qsize() > 0):
            counter += 1
            try:
                updates = await asyncio.wait_for(UPDATES_QUEUE.get(), 1.0)
                yield [
                    file_diff.get_file_change(file_path, new_contents, annotation_label=str(counter))
                    for file_path, new_contents in updates
                ]
            except asyncio.TimeoutError:
                continue


if __name__ == "__main__":
    agent.launcher(GPTMigrateAgent, GPTMigrateAgentParams)
