from __future__ import annotations

from typing import Any

from .error_type import ErrorType


class Messages:
    """Unified message class returned by all tools."""

    def __init__(
        self,
        status: str = "failed",
        messages: str = "",
        data: dict[str, Any] | None = None,
    ):
        self.status = status
        self.messages = messages
        self.data = data or {}

    @classmethod
    def build_failure_message(
        cls,
        error_type: ErrorType,
        detail: str = "",
        data: dict[str, Any] | None = None,
    ) -> Messages:
        """Build a failure message corresponding to the given ErrorType."""
        if detail:
            messages = f"{error_type.value}, {detail}"
        else:
            messages = f"{error_type.value}"
        return cls(status="failed", messages=messages, data=data or {})

    @classmethod
    def build_success_message(cls, data: dict[str, Any] | None = None) -> Messages:
        return cls(status="success", messages="Successfully executed tool", data=data or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "messages": self.messages,
            "data": self.data,
        }
