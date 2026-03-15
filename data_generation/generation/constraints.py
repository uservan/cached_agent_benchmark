import random

from data_generation.domains import DOMAIN_SPECS


def get_rule_candidates(item, rule):
    candidates = []
    observed_value = item[rule["attr"]]

    for candidate in rule["candidates"]:
        if rule["kind"] == "max" and candidate >= observed_value:
            candidates.append(candidate)
        if rule["kind"] == "min" and candidate <= observed_value:
            candidates.append(candidate)

    if not candidates:
        candidates.append(observed_value)

    return candidates


def item_matches_slot_constraint(item, slot_constraint, slot_rules):
    for rule in slot_rules:
        value = slot_constraint[rule["name"]]
        observed = item[rule["attr"]]
        if rule["kind"] == "max" and observed > value:
            return False
        if rule["kind"] == "min" and observed < value:
            return False
    return True


def count_matching_items(domain, item_pool, slot_constraint):
    slot_rules = DOMAIN_SPECS[domain]["slot_rules"]
    return sum(1 for item in item_pool if item_matches_slot_constraint(item, slot_constraint, slot_rules))


def generate_slot_constraints(domain, item_pool, truth_solution, item_lookup, rows, cols):
    spec = DOMAIN_SPECS[domain]
    slot_constraints = []
    pool_bounds = {}
    for rule in spec["slot_rules"]:
        values = [item[rule["attr"]] for item in item_pool]
        if rule["kind"] == "max":
            pool_bounds[rule["name"]] = max(values)
        else:
            pool_bounds[rule["name"]] = min(values)

    for row_index in range(rows):
        for col_index in range(cols):
            constraint = {"row": row_index, "col": col_index}
            for rule in spec["slot_rules"]:
                constraint[rule["name"]] = pool_bounds[rule["name"]]
            slot_constraints.append(constraint)

    return slot_constraints


def repeat_max(items, key):
    counts = {}
    for item in items:
        value = item[key]
        counts[value] = counts.get(value, 0) + 1
    return max(counts.values()) if counts else 0


def evaluate_aggregate_rule(rule, items, truth_solution=None, item_lookup=None):
    rule_type = rule["type"]

    if rule_type in ("sum_min", "sum_max"):
        return sum(item[rule["attr"]] for item in items)

    if rule_type == "max_cap":
        return max(item[rule["attr"]] for item in items)

    if rule_type == "repeat_max":
        return repeat_max(items, rule["attr"])

    if rule_type == "count_min":
        return sum(1 for item in items if item[rule["predicate_key"]] == rule["predicate_value"])

    if rule_type == "count_min_threshold":
        return sum(1 for item in items if item[rule["attr"]] >= rule["threshold"])

    if rule_type == "max_row_sum":
        row_totals = []
        rows = len(truth_solution)
        cols = len(truth_solution[0])
        for row_index in range(rows):
            row_total = 0
            for col_index in range(cols):
                item_id = truth_solution[row_index][col_index]
                row_total += item_lookup[item_id][rule["attr"]]
            row_totals.append(row_total)
        return max(row_totals)

    raise ValueError(f"Unsupported rule type: {rule_type}")


def build_constraint_value(rule, observed, group_size):
    rule_type = rule["type"]

    if rule_type == "sum_min":
        return random.randint(max(rule.get("floor", 0), observed - rule["slack"]), observed)

    if rule_type == "sum_max":
        upper_cap = group_size * rule["per_item_cap"]
        return random.randint(observed, min(upper_cap, observed + rule["slack"]))

    if rule_type == "max_cap":
        return random.randint(observed, rule["cap"])

    if rule_type == "repeat_max":
        return random.randint(observed, group_size)

    if rule_type in ("count_min", "count_min_threshold"):
        return random.randint(max(0, observed - rule["slack"]), observed)

    raise ValueError(f"Unsupported rule type: {rule_type}")


def make_aggregate_constraints(rule_specs, items, prefix_key, prefix_value, truth_solution=None, item_lookup=None, cols=None):
    constraints = {prefix_key: prefix_value}
    group_size = len(items)

    for rule in rule_specs:
        observed = evaluate_aggregate_rule(rule, items, truth_solution=truth_solution, item_lookup=item_lookup)
        if rule["type"] == "max_row_sum":
            upper_cap = cols * rule["per_item_cap"]
            constraints[rule["name"]] = random.randint(observed, min(upper_cap, observed + rule["slack"]))
        else:
            constraints[rule["name"]] = build_constraint_value(rule, observed, group_size)

    return constraints


def build_loose_constraints(rule_specs, item_pool, prefix_key, prefix_value, group_size, cols=None):
    constraints = {prefix_key: prefix_value}

    for rule in rule_specs:
        if rule["type"] == "sum_min":
            constraints[rule["name"]] = rule.get("floor", 0)
        elif rule["type"] == "sum_max":
            max_value = max(item[rule["attr"]] for item in item_pool)
            constraints[rule["name"]] = group_size * max_value
        elif rule["type"] == "max_cap":
            constraints[rule["name"]] = max(item[rule["attr"]] for item in item_pool)
        elif rule["type"] == "repeat_max":
            constraints[rule["name"]] = group_size
        elif rule["type"] in ("count_min", "count_min_threshold"):
            constraints[rule["name"]] = 0
        elif rule["type"] == "max_row_sum":
            max_value = max(item[rule["attr"]] for item in item_pool)
            constraints[rule["name"]] = cols * max_value
        else:
            raise ValueError(f"Unsupported rule type: {rule['type']}")

    return constraints


def generate_row_constraints(domain, truth_solution, item_lookup, item_pool, rows, cols):
    rule_specs = DOMAIN_SPECS[domain]["row_rules"]
    row_constraints = []

    for row_index in range(rows):
        row_constraints.append(
            build_loose_constraints(rule_specs, item_pool, "row", row_index, cols, cols=cols)
        )

    return row_constraints


def generate_col_constraints(domain, truth_solution, item_lookup, item_pool, rows, cols):
    rule_specs = DOMAIN_SPECS[domain]["col_rules"]
    col_constraints = []

    for col_index in range(cols):
        col_constraints.append(
            build_loose_constraints(rule_specs, item_pool, "col", col_index, rows, cols=cols)
        )

    return col_constraints


def generate_global_constraints(domain, truth_solution, item_lookup, item_pool, rows, cols):
    rule_specs = DOMAIN_SPECS[domain]["global_rules"]
    return build_loose_constraints(rule_specs, item_pool, "global", "global", rows * cols, cols=cols)


def aggregate_constraint_satisfied(rule, constraint_value, items, truth_solution=None, item_lookup=None):
    observed = evaluate_aggregate_rule(rule, items, truth_solution=truth_solution, item_lookup=item_lookup)
    rule_type = rule["type"]

    if rule_type in ("sum_max", "max_cap", "repeat_max", "max_row_sum"):
        return observed <= constraint_value

    if rule_type in ("sum_min", "count_min", "count_min_threshold"):
        return observed >= constraint_value

    raise ValueError(f"Unsupported rule type: {rule_type}")
