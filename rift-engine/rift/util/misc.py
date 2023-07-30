import contextlib
import contextvars
import re
from typing import Callable, TypeVar
import logging
import rift.lsp.types as lsp

T = TypeVar("T")

logger = logging.getLogger(__name__)

def replace_chips(user_response, server):
    uri_pattern = r"uri://(.*)"
    matches = re.findall(uri_pattern, user_response)
    for match in matches:
        match = match.replace(" ", "")
        logger.info(f"[replace_chips] found {match=}")
        if ("file://" + match) in server.documents:
            logger.info(f"[replace_chips] found {match=} in documents")
            user_response = user_response.replace(
                f"uri://{match}", "```" + server.documents[("file://" + match)].text + "```"
            )
    return user_response

def resolve_chips(user_response, server) -> List[lsp.Document]:
    uri_pattern = r"uri://(.*)"
    matches = re.findall(uri_pattern, user_response)
    result = []
    for match in matches:
        match = match.replace(" ", "")
        lsp_uri = "file://" + match
        if lsp_uri in server.documents:
            logger.info(f"[replace_chips] found {match=} in documents")
            result.append(lsp.Document(f"uri://{match}", server.documents[lsp_uri].text))
    return result

def contextual_prompt(prompt, documents: List[lsp.Document], max_size: Optional[int] = None):

    if max_size is not None:
        # TODO add truncation logic
        ...
    
    return (
        "Visible files:\n"
        f"{'\n'.join('`' + doc.uri + '`\n===\n' + doc.document + '\n' for doc in documents)}"
        f"\n{prompt}"
    )

@contextlib.contextmanager
def set_ctx(context_variable: contextvars.ContextVar[T], value: T):
    """
    Set the given context variable to the provided value.

    Args:
        context_variable (contextvars.ContextVar): The context variable to set.
        value (T): The value to set the context variable to.
    """
    old_value = context_variable.set(value)
    try:
        yield value
    finally:
        context_variable.reset(old_value)


@contextlib.contextmanager
def map_ctx(context_variable: contextvars.ContextVar[T], mapper: Callable[[T], T]):
    """
    Map the value of the given context variable using the provided function.

    Args:
        context_variable (contextvars.ContextVar): The context variable to map.
        mapper (Callable[[T], T]): The function to apply to the context variable value.

    Yields:
        T: The mapped value of the context variable.
    """
    old_value = context_variable.get()
    new_value = mapper(old_value)
    with set_ctx(context_variable, new_value):
        yield new_value
