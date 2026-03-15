"""Workforce scheduling 领域的 tools。"""

from .. import BaseToolsHandler
from ..base import Messages


class WorkforceToolsHandler(BaseToolsHandler):
    """Workforce 领域工具总 handler。"""

    domain = "workforce"

    def __init__(self):
        super().__init__()
        self.tools.update({
            "query_workforce_slot_candidates": self.query_workforce_slot_candidates,
            "get_workforce_item_info": self.get_workforce_item_info,
            "check_workforce_row_constraints": self.check_workforce_row_constraints,
            "check_workforce_col_constraints": self.check_workforce_col_constraints,
            "check_workforce_global_constraints": self.check_workforce_global_constraints,
        })

    def query_workforce_slot_candidates(self, row: int, col: int) -> Messages:
        """Return candidate ids, names, and departments for a workforce slot.

        row: Row index as an integer.
        col: Column index as an integer.
        """
        return self._query_slot_candidates(row, col, summary_fields=["name", "department"])

    def get_workforce_item_info(self, ids: list[str]) -> Messages:
        """Return full workforce item information for up to three ids.

        ids: List of workforce item ids as strings, with at most 3 items.
        """
        return self._get_item_info(ids, max_items=3)

    def check_workforce_row_constraints(self, row: int) -> Messages:
        """Check whether a row satisfies the workforce row constraints.

        row: Row index as an integer.
        """
        return self._check_row_constraints(row)

    def check_workforce_col_constraints(self, col: int) -> Messages:
        """Check whether a column satisfies the workforce column constraints.

        col: Column index as an integer.
        """
        return self._check_col_constraints(col)

    def check_workforce_global_constraints(self) -> Messages:
        """Check whether the current workforce grid satisfies the global constraints."""
        return self._check_global_constraints()
