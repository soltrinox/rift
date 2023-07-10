import asyncio
from concurrent.futures import ThreadPoolExecutor
import fire
import fire.core


def _PrintResult(component_trace, verbose=False, serialize=None):
    result = component_trace.GetResult()
    if serialize:
        if not callable(serialize):
            raise fire.core.FireError(
                "The argument `serialize` must be empty or callable:", serialize
            )
        result = serialize(result)

    if fire.value_types.HasCustomStr(result):
        print(str(result))
        return

    if isinstance(result, (list, set, frozenset, types.GeneratorType)):
        for i in result:
            print(fire.core._OneLineResult(i))
    elif inspect.isgeneratorfunction(result):
        raise NotImplementedError
    elif isinstance(result, dict) and value_types.IsSimpleGroup(result):
        print(fire.core._DictAsString(result, verbose))
    elif isinstance(result, tuple):
        print(fire.core._OneLineResult(result))
    elif dataclasses._is_dataclass_instance(result):
        print(fire.core._OneLineResult(result))
    elif isinstance(result, value_types.VALUE_TYPES):
        if result is not None:
            print(result)
    else:
        help_text = fire.helptext.HelpText(result, trace=component_trace, verbose=verbose)
        output = [help_text]
        Display(output, out=sys.stdout)


fire.core._PrintResult = _PrintResult


def stream_string(string):
    for char in string:
        print(char, end="", flush=True)
        time.sleep(0.0015)


def stream_string_ascii(name: str):
    _splash = art.text2art(name, font="smslant")

    stream_string(_splash)


async def ainput(prompt: str = "") -> str:
    with ThreadPoolExecutor(1, "AsyncInput") as executor:
        return await asyncio.get_event_loop().run_in_executor(executor, input, prompt)
