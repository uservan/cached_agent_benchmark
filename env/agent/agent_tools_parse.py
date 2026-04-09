import json
import re
from typing import Any

from json_repair import repair_json


TOOL_CALL_BLOCK_PATTERN = re.compile(
    r"<tool_call>\s*<function=([^>]+)>(.*?)</function>\s*</tool_call>",
    re.DOTALL,
)
PARAMETER_PATTERN = re.compile(
    r"<parameter=([^>]+)>\s*(.*?)\s*</parameter>",
    re.DOTALL,
)
MCP_TOOL_NAME_PATTERN = re.compile(r"<tool_name>(.*?)</tool_name>", re.DOTALL)
MCP_ARGUMENTS_PATTERN = re.compile(r"<arguments>(.*?)</arguments>", re.DOTALL)

DSML_INVOKE_PATTERN = re.compile(
    r"<｜DSML｜invoke\s+name=\"([^\"]+)\">(.*?)</｜DSML｜invoke>",
    re.DOTALL,
)
DSML_PARAMETER_PATTERN = re.compile(
    r"<｜DSML｜parameter\s+name=\"([^\"]+)\"\s+string=\"(true|false)\">(.*?)</｜DSML｜parameter>",
    re.DOTALL,
)


def parse_tool_calls(model: str, response_message: Any) -> list[dict[str, str]]:
    normalized_model = model.lower()
    text = _build_message_text(response_message)
    direct_tool_calls = _parse_direct_tool_calls(response_message)

    if "qwen3.5" in normalized_model or "qwen3_5" in normalized_model:
        return deduplicate_tool_calls(
            direct_tool_calls + _parse_qwen3_5_tool_calls(text)
        )

    if "deepseek" in normalized_model:
        dsml_tool_calls = _parse_dsml_tool_calls(text)
        non_empty_direct = [tc for tc in direct_tool_calls if tc.get("arguments", "{}") != "{}"]
        return deduplicate_tool_calls(non_empty_direct or dsml_tool_calls)

    if "mirothinker" in normalized_model or "miro" in normalized_model:
        miro_tool_calls = _parse_miro_tool_calls(text)
        non_empty_direct = [tc for tc in direct_tool_calls if tc.get("arguments", "{}") != "{}"]
        return deduplicate_tool_calls(
            (non_empty_direct or miro_tool_calls)
        )

    return deduplicate_tool_calls(direct_tool_calls)


def _parse_direct_tool_calls(response_message: Any) -> list[dict[str, str]]:
    parsed_tool_calls: list[dict[str, str]] = []
    for tool_call in getattr(response_message, "tool_calls", None) or []:
        function_info = getattr(tool_call, "function", None)
        tool_name = getattr(function_info, "name", None)
        arguments = getattr(function_info, "arguments", None)
        if not tool_name:
            continue
        if isinstance(arguments, str):
            arguments_str = arguments
        else:
            arguments_str = json.dumps(arguments or {}, ensure_ascii=False)
        parsed_tool_calls.append(
            {
                "name": str(tool_name),
                "arguments": arguments_str,
            }
        )
    return parsed_tool_calls


def _parse_qwen3_5_tool_calls(content: str) -> list[dict[str, str]]:
    parsed_tool_calls: list[dict[str, str]] = []
    for function_name, function_body in TOOL_CALL_BLOCK_PATTERN.findall(content):
        tool_args = {
            parameter_name.strip(): parameter_value.strip()
            for parameter_name, parameter_value in PARAMETER_PATTERN.findall(function_body)
        }
        parsed_tool_calls.append(
            {
                "name": function_name.strip(),
                "arguments": json.dumps(tool_args, ensure_ascii=False),
            }
        )
    return parsed_tool_calls


def _parse_miro_tool_calls(content: str) -> list[dict[str, str]]:
    last = content.rfind("<use_mcp_tool>")
    if last == -1:
        return []
    block = content[last:]
    tool_name_match = MCP_TOOL_NAME_PATTERN.search(block)
    arguments_match = MCP_ARGUMENTS_PATTERN.search(block)
    if not tool_name_match:
        return []
    tool_name = tool_name_match.group(1).strip()
    if arguments_match:
        arguments_str = arguments_match.group(1).strip()
    else:
        args_start = block.find("<arguments>")
        arguments_str = block[args_start + len("<arguments>"):] if args_start != -1 else block
    try:
        json.loads(arguments_str)
    except json.JSONDecodeError:
        json_match = re.search(r"\{.*\}", arguments_str, re.DOTALL)
        raw = json_match.group(0) if json_match else arguments_str
        repaired = repair_json(raw)
        if not repaired or repaired == "{}":
            return []
        arguments_str = repaired
    return [{"name": tool_name, "arguments": arguments_str}]


def _parse_dsml_tool_calls(content: str) -> list[dict[str, str]]:
    parsed_tool_calls: list[dict[str, str]] = []
    for function_name, function_body in DSML_INVOKE_PATTERN.findall(content):
        tool_args = {}
        for param_name, is_string, param_value in DSML_PARAMETER_PATTERN.findall(function_body):
            value = param_value.strip()
            if is_string == "false":
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass
            tool_args[param_name.strip()] = value
        parsed_tool_calls.append(
            {
                "name": function_name.strip(),
                "arguments": json.dumps(tool_args, ensure_ascii=False),
            }
        )
    return parsed_tool_calls


def deduplicate_tool_calls(tool_calls: list[dict[str, str]]) -> list[dict[str, str]]:
    deduplicated: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for tool_call in tool_calls:
        key = (tool_call.get("name", ""), tool_call.get("arguments", ""))
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(tool_call)
    return deduplicated




def _build_message_text(response_message: Any) -> str:
    return (
        (getattr(response_message, "reasoning_content", None) or "")
        + " "
        + (getattr(response_message, "content", None) or "")
    ).strip()
