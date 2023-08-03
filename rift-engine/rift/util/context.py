import contextlib
import contextvars
import logging
import re
from typing import Callable, List, Optional, TypeVar

import rift.lsp.types as lsp

T = TypeVar("T")

logger = logging.getLogger(__name__)


def extract_uris(user_response: str) -> List[str]:
    uri_pattern = r"\[uri\]\((\S+)\)"
    matches = re.findall(uri_pattern, user_response)
    return [match.replace(" ", "") for match in matches]


def lookup_match(match: str, server: "Server") -> str:
    lsp_uri = "file://" + match
    if lsp_uri in server.documents:
        return server.documents[lsp_uri].text
    else:
        try:
            if os.path.isdir(match):
                return ""
            else:
                with open(match, "r") as f:
                    return f.read()
        except:
            return ""


def replace_inline_uris(user_response: str, server: "Server") -> str:
    matches = extract_uris(user_response)
    for match in matches:
        logger.info(f"[replace_inline_uris] found {match=}")
        replacement = lookup_match(match, server)
        user_response = user_response.replace(f"uri://{match}", "```" + replacement + "```")
    return user_response


def resolve_inline_uris(user_response: str, server: "Server") -> List[lsp.Document]:
    matches = extract_uris(user_response)
    result = []
    for match in matches:
        logger.info(f"[resolve_inline_uris] looking for {match=}")
        replacement = lookup_match(match, server)
        result.append(lsp.Document(f"uri://{match}", lsp.DocumentContext(replacement)))
    return result


def contextual_prompt(
    prompt: str, documents: List[lsp.Document], max_size: Optional[int] = None
) -> str:
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