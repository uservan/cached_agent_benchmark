"""基类定义。"""

from enum import Enum
from typing import Any, Callable, Dict

from agent.task import Task

from .utils import Tool, as_tool


class BaseToolsHandler:
    """各领域 handler 的基类。"""

    domain: str = ""
    STOP_TOKEN: str = "###STOP###"
    current_task: Task = None

    def __init__(self):
        self.tools: dict[str, Callable[..., Any]] = {
            "set_slot": self.set_slot,
            "check_all_slots": self.check_all_slots,
            "get_slot_id": self.get_slot_id,
            "done": self.done,
        }

    def handle(
        self,
        task: Task,
        tool_name: str,
        tool_args: dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        self.current_task = task
        """处理工具调用。task 为 Task 类实例。调用时暂存 task 到 self._current_task，工具函数仅接收 args。"""
        if tool_name not in self.tools:
            return Messages.build_failure_message(
                ErrorType.UNKNOWN_TOOL,
                f"'{tool_name}' for domain '{self.domain}'",
            )
        return self.tools[tool_name](**(tool_args or {}))

    def get_tools(self) -> Dict[str, Tool]:
        """Get the tools available in the ToolKit.
            Uses the `as_tool` to convert the functions to Tool objects.

            Returns:
                A dictionary of tools available in the ToolKit.
            """
        # NOTE: as_tool needs to get the function (self.foo), not the `foo(self, ...)`
        # Otherwise, the `self` will exists in the arguments.
        # Therefore, it needs to be called with getattr(self, name)
        my_tools = dict()
        for name, tool in self.tools.items():
            my_tools[name] = as_tool(tool)
        return my_tools

    def done(self) -> Messages:
        """Call this function when you are done with the task."""
        return Messages(status="success", messages=self.STOP_TOKEN, data={})

    def set_slot(self, row: int, col: int, id: str | None = None) -> Messages:
        """在指定 slot 填写或清空。

        row: 行索引
        col: 列索引
        id: 要填写的 id，传空或省略则清空该 slot
        """
        task = self.current_task
        if task is None:
            return Messages.build_failure_message(ErrorType.INVALID_ARGUMENTS, "No current task")
        try:
            row, col = int(row), int(col)
        except (TypeError, ValueError):
            return Messages.build_failure_message(ErrorType.INVALID_ARGUMENTS, "row and col must be integers")
        solution = task.agent_solution
        if row < 0 or row >= len(solution) or col < 0 or col >= len(solution[0]):
            return Messages.build_failure_message(ErrorType.INVALID_ARGUMENTS, f"Invalid slot (row={row}, col={col})")
        if id is not None and id != "":
            solution[row][col] = str(id)
        else:
            solution[row][col] = None
        return Messages.build_success_message({"row": row, "col": col, "id": solution[row][col]})

    def check_all_slots(self) -> Messages:
        """返回全部 slot 上的 id（当前 agent_solution 完整状态）。"""
        task = self.current_task
        if task is None:
            return Messages.build_failure_message(ErrorType.INVALID_ARGUMENTS, "No current task")
        return Messages.build_success_message({"slots": task.agent_solution})

    def get_slot_id(self, row: int, col: int) -> Messages:
        """查询某个 slot 的 id。

        row: 行索引
        col: 列索引
        """
        task = self.current_task
        if task is None:
            return Messages.build_failure_message(ErrorType.INVALID_ARGUMENTS, "No current task")
        try:
            row, col = int(row), int(col)
        except (TypeError, ValueError):
            return Messages.build_failure_message(ErrorType.INVALID_ARGUMENTS, "row and col must be integers")
        solution = task.agent_solution
        if row < 0 or row >= len(solution) or col < 0 or col >= len(solution[0]):
            return Messages.build_failure_message(ErrorType.INVALID_ARGUMENTS, f"Invalid slot (row={row}, col={col})")
        return Messages.build_success_message({"row": row, "col": col, "id": solution[row][col]})


class ErrorType(Enum):
    UNKNOWN_TOOL = "Unknown tool"
    INVALID_ARGUMENTS = "Invalid tool arguments"
    WRONG_DOMAIN = "This tool is from other domain, not this domain"
    TIMEOUT = "Timeout"
    TOOL_FAILURE = "Tool call failed"


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
        error_type: "ErrorType",
        detail: str = "",
        data: dict[str, Any] | None = None,
    ) -> "Messages":
        """根据 ErrorType 构建对应的失败消息。"""
        if detail:
            messages = f"{error_type.value}, {detail}"
        else:
            messages = f"{error_type.value}" 
        return cls(status="failed", messages=messages, data=data or {})

    @classmethod
    def build_success_message(cls, data: dict[str, Any] | None = None) -> "Messages":
        return cls(status="success", messages="Successfully executed tool", data=data or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "messages": self.messages,
            "data": self.data,
        }