"""Course scheduling 领域的 tools。"""

from .. import BaseToolsHandler
from ..base import Messages


class CourseToolsHandler(BaseToolsHandler):
    """Course 领域工具总 handler。"""

    domain = "course"

    def __init__(self):
        super().__init__()
        self.tools.update({
            "query_course_slot_candidates": self.query_course_slot_candidates,
            "get_course_item_info": self.get_course_item_info,
            "check_course_row_constraints": self.check_course_row_constraints,
            "check_course_col_constraints": self.check_course_col_constraints,
            "check_course_global_constraints": self.check_course_global_constraints,
        })

    def query_course_slot_candidates(self, row: int, col: int) -> Messages:
        """根据 slot 提供对应的 candidate 的 ids、name、category。

        row: 行索引
        col: 列索引
        """
        return self._query_slot_candidates(row, col, summary_fields=["name", "category"])

    def get_course_item_info(self, ids: list[str]) -> Messages:
        """根据 id 提供 item 的所有属性信息，一次性最多输入三个 id。

        ids: 要查询的 id 列表，最多 3 个
        """
        return self._get_item_info(ids, max_items=3)

    def check_course_row_constraints(self, row: int) -> Messages:
        """检查行坐标是否符合限制。

        row: 行索引
        """
        return self._check_row_constraints(row)

    def check_course_col_constraints(self, col: int) -> Messages:
        """检查列坐标是否符合限制。

        col: 列索引
        """
        return self._check_col_constraints(col)

    def check_course_global_constraints(self) -> Messages:
        """检查总限制是否符合。"""
        return self._check_global_constraints()
