from rift.agents.client.cli_agent import CliAgent, launcher
from rift.agents.client.util import ainput


@dataclass
class SmolAgentClientParams(ClientParams):
    prompt_file: str  # path to prompt file
    debug: bool = False


@dataclass
class SmolAgent(CliAgent):
    name: ClassVar[str] = "smol"
    run_params: Type[SmolAgentClientParams] = SmolAgentClientParams
    splash: Optional[
        str
    ] = """\


   __                                 __
  / /   but make it...           __   \ \      
 | |             ___ __ _  ___  / /    | |      
 | |            (_-</  ' \\/ _ \\/ /     | |      
 | |           /___/_/_/_/\\___/_/      | |      
 | |                                   | |      
  \_\                                 /_/       



    """

    async def run(self) -> AsyncIterable[List[file_diff.FileChange]]:
        params = self.run_params
        await ainput("\n> Press any key to continue.\n")

        with open(params.prompt_file, "r") as f:
            prompt = f.read()

        logger.info("Starting smol-dev with prompt:")
        self.console.print(prompt, markup=True, highlight=True)

        await ainput("\n> Press any key to continue.\n")

        def stream_handler(chunk):
            def stream_string(string):
                for char in string:
                    print(char, end="", flush=True)
                    time.sleep(0.0012)

            stream_string(chunk.decode("utf-8"))

        plan = smol_dev.plan(prompt, streamHandler=stream_handler)

        logger.info("Running with plan:")
        self.console.print(plan, emoji=True, markup=True)

        await ainput("\n> Press any key to continue.\n")

        file_paths = smol_dev.specify_filePaths(prompt, plan)

        logger.info("Got file paths:")
        self.console.print(json.dumps(file_paths, indent=2), markup=True)

        file_changes = []

        await ainput("\n> Press any key to continue.\n")

        @dataclass
        class PBarUpdater:
            pbars: Dict[int, Any] = field(default_factory=dict)
            dones: Dict[int, Any] = field(default_factory=dict)
            messages: Dict[int, Optional[str]] = field(default_factory=dict)
            lock: asyncio.Lock = asyncio.Lock()

            def update(self):
                for position, pbar in self.pbars.items():
                    if self.dones[position]:
                        pbar.display(self.messages[position])
                    else:
                        pbar.update()

        updater = PBarUpdater()

        async def generate_code_for_filepath(file_path: str, position: int) -> file_diff.FileChange:
            stream_handler = lambda chunk: pbar.update(n=len(chunk))
            code_future = asyncio.ensure_future(
                smol_dev.generate_code(prompt, plan, file_path, streamHandler=stream_handler)
            )
            with tqdm.asyncio.tqdm(position=position, unit=" chars", unit_scale=True) as pbar:
                async with updater.lock:
                    updater.pbars[position] = pbar
                    updater.dones[position] = False
                done = False
                waiter = asyncio.get_running_loop().create_future()

                def cb(fut):
                    waiter.cancel()

                code_future.add_done_callback(cb)

                async def spinner():
                    spinner_index: int = 0
                    steps = ["[⢿]", "[⣻]", "[⣽]", "[⣾]", "[⣷]", "[⣯]", "[⣟]", "[⡿]"]
                    while True:
                        c = steps[spinner_index % len(steps)]
                        pbar.set_description(f"{c} Generating code for {file_path}")
                        async with updater.lock:
                            updater.update()
                        spinner_index += 1
                        await asyncio.sleep(0.05)
                        if waiter.done():
                            # pbar.display(f"[✔️] Generated code for {file_path}")
                            async with updater.lock:
                                updater.dones[position] = True
                                updater.messages[position] = f"[✔️] Generated code for {file_path}"
                                pbar.set_description(f"[✔️] Generated code for {file_path}")
                                updater.update()
                            # async with updater.lock:
                            #     updater.pbars.pop(position)
                            return
                        # await asyncio.wait_for(waiter, 0.025)
                    # pbar.set_description(f"[✔️] Generating code for {file_path}")

                    # pbar.set_description(f"[✔️] Generating code for {file_path}")

                t = asyncio.create_task(spinner())
                code = await code_future
                # self.console.print(
                #     f"""```\
                #     {code}
                #     ```
                #     """,
                #     markup=True,
                # )
                absolute_file_path = os.path.join(os.getcwd(), file_path)
                # logger.info(f"Generating a diff for {absolute_file_path}")
                file_change = file_diff.get_file_change(path=absolute_file_path, new_content=code)
                return file_change

        fs = [
            asyncio.create_task(generate_code_for_filepath(fp, position=i))
            for i, fp in enumerate(file_paths)
        ]

        yield await asyncio.gather(*fs)


if __name__ == "__main__":
    launcher(SmolAgentClientParams)
