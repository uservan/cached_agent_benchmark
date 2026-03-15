from enum import Enum


class ErrorType(Enum):
    UNKNOWN_TOOL = "Unknown tool"
    INVALID_ARGUMENTS = "Invalid tool arguments"
    WRONG_DOMAIN = "This tool is from other domain, not this domain"
    TIMEOUT = "Timeout"
    TOOL_FAILURE = "Tool call failed"
