from __future__ import annotations

from typing import Any

from .error_type import ErrorType


class Messages:
    """Tools 统一返回的消息类。"""

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
        """根据 ErrorType 构建对应的失败消息。"""
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
