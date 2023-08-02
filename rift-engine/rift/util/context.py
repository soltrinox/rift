import contextlib
import contextvars
import logging
import re
from typing import Callable, List, Optional, TypeVar

import rift.lsp.types as lsp

T = TypeVar("T")

logger = logging.getLogger(__name__)


def replace_inline_uris(user_response, server):
    uri_pattern = r"\[uri\]\((\S+)\)"
    matches = re.findall(uri_pattern, user_response)
    for match in matches:
        match = match.replace(" ", "")
        logger.info(f"[replace_inline_uris] found {match=}")
        if ("file://" + match) in server.documents:
            logger.info(f"[replace_inline_uris] found {match=} in documents")
            user_response = user_response.replace(
                f"uri://{match}", "```" + server.documents[("file://" + match)].text + "```"
            )
    return user_response


def resolve_inline_uris(user_response, server) -> List[lsp.Document]:
    uri_pattern = r"\[uri\]\((\S+)\)"
    matches = re.findall(uri_pattern, user_response)
    result = []
    for match in matches:
        match = match.replace(" ", "")
        lsp_uri = "file://" + match
        logger.info(f"[resolve_inline_uris] looking for {lsp_uri=}")
        if lsp_uri in server.documents:
            logger.info(f"[resolve_inline_uris] found {match=} in documents")
            result.append(
                lsp.Document(f"uri://{match}", lsp.DocumentContext(server.documents[lsp_uri].text))
            )
        else:
            try:
                with open(match, "r") as f:
                    result.append(lsp.Document(f"uri://{match}", lsp.DocumentContext(f.read())))
            except:
                pass

    return result


def contextual_prompt(prompt, documents: List[lsp.Document], max_size: Optional[int] = None):
    if max_size is not None:
        # TODO add truncation logic
        ...

    result = (
        "Visible files:\n"
        + "\n".join("`" + doc.uri + "`\n===\n" + doc.document + "\n" for doc in documents)
        + "\n"
        f"{prompt}"
    )
    return result
