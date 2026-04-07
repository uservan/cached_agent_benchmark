"""Functions related to tool invocation."""

import random
from typing import Any

from .base import ErrorType, Messages
from .config import DOMAIN_HANDLERS
from agent.task import Task

def get_saved_dataset_tool_schemas(domain: str | None = None) -> list[Any]:
    """Get the handler for the given domain, call get_tools(), and return its values as a list.
    If domain is None, return tools for all domains. Deduplicated by tool name (e.g. done appears in multiple domains; only one is kept)."""
    if domain is None:
        handlers = list(DOMAIN_HANDLERS.values())
    else:
        if domain not in DOMAIN_HANDLERS:
            raise ValueError(f"Unsupported domain for tools: {domain}")
        handlers = [DOMAIN_HANDLERS[domain]]

    seen: dict[str, Any] = {}
    for h in handlers:
        for name, tool in h.get_tools().items():
            if name not in seen:
                seen[name] = tool
    return list(seen.values())


def call_saved_dataset_tool(
    task: Task,
    tool_name: str,
    tool_args: dict[str, Any],
    tool_failure_rate: float = 0.0,
    **kwargs: Any,
) -> dict[str, Any]:
    """Call a tool and return JSON-formatted data from Messages.to_dict()."""
    if tool_failure_rate and random.random() < tool_failure_rate:
        msg = Messages.build_failure_message(ErrorType.TOOL_FAILURE)
        return msg.to_dict()

    domain = getattr(task.dataset_object, "domain", None)
    if domain not in DOMAIN_HANDLERS:
        msg = Messages.build_failure_message(ErrorType.WRONG_DOMAIN, f"Unsupported domain: {domain}")
        return msg.to_dict()

    handler = DOMAIN_HANDLERS[domain]
    result = handler.handle(task, tool_name, tool_args or {}, **kwargs)
    if isinstance(result, Messages):
        return result.to_dict()
    msg = Messages.build_success_message(result if isinstance(result, dict) else {"result": result})
    return msg.to_dict()
