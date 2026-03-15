from data_generation.generation.constraints import aggregate_constraint_satisfied


def partial_max_row_sum(solution, item_pool, attr):
    row_totals = []
    for row in solution:
        row_total = 0
        for item_id in row:
            if item_id is None:
                continue
            row_total += item_pool[item_id][attr]
        row_totals.append(row_total)
    return max(row_totals) if row_totals else 0


def rule_satisfied(rule, constraint_value, items, is_complete, solution, item_pool):
    if rule["type"] in ("sum_min", "count_min", "count_min_threshold") and not is_complete:
        return True
    if rule["type"] == "max_row_sum" and not is_complete:
        return partial_max_row_sum(solution, item_pool, rule["attr"]) <= constraint_value
    return aggregate_constraint_satisfied(
        rule,
        constraint_value,
        items,
        truth_solution=solution,
        item_lookup=item_pool,
    )
