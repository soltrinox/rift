import contextlib
import contextvars
import re
from typing import Callable, TypeVar, List, Optional
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
    
    result =\
        "Visible files:\n" + '\n'.join('`' + doc.uri + '`\n===\n' + doc.document + '\n' for doc in documents) + "\n"f"{prompt}"
    return result
