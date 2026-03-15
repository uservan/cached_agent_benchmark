from data_generation.domains import DOMAIN_SPECS
from data_generation.generation.constraints import make_aggregate_constraints


def row_items(truth_solution, item_lookup, row_index):
    return [item_lookup[item_id] for item_id in truth_solution[row_index]]


def col_items(truth_solution, item_lookup, col_index):
    return [item_lookup[truth_solution[row_index][col_index]] for row_index in range(len(truth_solution))]


def global_items(truth_solution, item_lookup):
    return [item_lookup[item_id] for row in truth_solution for item_id in row]


def rule_attr_key(rule):
    if "attr" in rule:
        return rule["attr"]
    if "predicate_key" in rule:
        return rule["predicate_key"]
    return rule["name"]


def active_rules(rule_specs, constraint):
    return [rule for rule in rule_specs if rule["name"] in constraint]


def ordered_attr_keys(rule_specs):
    keys = []
    seen = set()
    for rule in rule_specs:
        key = rule_attr_key(rule)
        if key in seen:
            continue
        seen.add(key)
        keys.append(key)
    return keys


def pick_rule_for_attr(rule_specs, attr_key):
    for rule in rule_specs:
        if rule_attr_key(rule) == attr_key:
            return rule
    return None


def select_constraint_rule_sets(spec):
    row_rules = spec["row_rules"]
    col_rules = spec["col_rules"]
    global_rules = spec["global_rules"]

    global_attrs = ordered_attr_keys(global_rules)[: min(4, len(ordered_attr_keys(global_rules)))]
    row_attrs = ordered_attr_keys(row_rules)
    col_attrs = ordered_attr_keys(col_rules)

    row_shared = [attr for attr in global_attrs if attr in row_attrs][:2]
    col_shared = [attr for attr in global_attrs if attr in col_attrs][:2]

    row_extra = next((attr for attr in row_attrs if attr not in global_attrs), None)
    col_extra = next(
        (attr for attr in col_attrs if attr not in global_attrs and attr != row_extra),
        None,
    )
    if col_extra is None:
        col_extra = next((attr for attr in col_attrs if attr not in global_attrs), None)

    selected_row_attrs = []
    for attr in row_shared:
        if attr not in selected_row_attrs:
            selected_row_attrs.append(attr)
    if row_extra is not None and row_extra not in selected_row_attrs:
        selected_row_attrs.append(row_extra)
    for attr in row_attrs:
        if len(selected_row_attrs) >= min(3, len(row_attrs)):
            break
        if attr not in selected_row_attrs:
            selected_row_attrs.append(attr)

    selected_col_attrs = []
    for attr in col_shared:
        if attr not in selected_col_attrs:
            selected_col_attrs.append(attr)
    if col_extra is not None and col_extra not in selected_col_attrs:
        selected_col_attrs.append(col_extra)
    for attr in col_attrs:
        if len(selected_col_attrs) >= min(3, len(col_attrs)):
            break
        if attr not in selected_col_attrs:
            selected_col_attrs.append(attr)

    selected_row_rules = [pick_rule_for_attr(row_rules, attr) for attr in selected_row_attrs]
    selected_col_rules = [pick_rule_for_attr(col_rules, attr) for attr in selected_col_attrs]
    selected_global_rules = [pick_rule_for_attr(global_rules, attr) for attr in global_attrs]

    return (
        [rule for rule in selected_row_rules if rule is not None],
        [rule for rule in selected_col_rules if rule is not None],
        [rule for rule in selected_global_rules if rule is not None],
    )


def build_truth_constraints(domain, truth_solution, item_lookup, rows, cols):
    spec = DOMAIN_SPECS[domain]
    row_rule_specs, col_rule_specs, global_rule_specs = select_constraint_rule_sets(spec)
    row_constraints = []
    col_constraints = []

    for row_index in range(rows):
        row_constraints.append(
            make_aggregate_constraints(
                row_rule_specs,
                row_items(truth_solution, item_lookup, row_index),
                "row",
                row_index,
                cols=cols,
            )
        )

    for col_index in range(cols):
        col_constraints.append(
            make_aggregate_constraints(
                col_rule_specs,
                col_items(truth_solution, item_lookup, col_index),
                "col",
                col_index,
                cols=cols,
            )
        )

    global_constraints = make_aggregate_constraints(
        global_rule_specs,
        global_items(truth_solution, item_lookup),
        "global",
        "global",
        truth_solution=truth_solution,
        item_lookup=item_lookup,
        cols=cols,
    )

    return row_constraints, col_constraints, global_constraints
