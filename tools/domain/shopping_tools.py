"""Grocery shopping 领域的 tools。"""

from .. import BaseToolsHandler
from ..base import Messages


class ShoppingToolsHandler(BaseToolsHandler):
    """Shopping 领域工具总 handler。"""

    domain = "shopping"

    def __init__(self):
        super().__init__()
        self.tools.update({
            "query_shopping_slot_candidates": self.query_shopping_slot_candidates,
            "get_shopping_item_info": self.get_shopping_item_info,
            "check_shopping_row_constraints": self.check_shopping_row_constraints,
            "check_shopping_col_constraints": self.check_shopping_col_constraints,
            "check_shopping_global_constraints": self.check_shopping_global_constraints,
        })

    def query_shopping_slot_candidates(self, row: int, col: int) -> Messages:
        """Return candidate ids, names, and categories for a shopping slot.

        row: Row index as an integer.
        col: Column index as an integer.
        """
        return self._query_slot_candidates(row, col, summary_fields=["name", "category"])

    def get_shopping_item_info(self, ids: list[str]) -> Messages:
        """Return full shopping item information for up to three ids.

        ids: List of shopping item ids as strings, with at most 3 items.
        """
        return self._get_item_info(ids, max_items=3)

    def check_shopping_row_constraints(self, row: int) -> Messages:
        """Check whether a row satisfies the shopping row constraints.

        row: Row index as an integer.
        """
        return self._check_row_constraints(row)

    def check_shopping_col_constraints(self, col: int) -> Messages:
        """Check whether a column satisfies the shopping column constraints.

        col: Column index as an integer.
        """
        return self._check_col_constraints(col)

    def check_shopping_global_constraints(self) -> Messages:
        """Check whether the current shopping grid satisfies the global constraints."""
        return self._check_global_constraints()
