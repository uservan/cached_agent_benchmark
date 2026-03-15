import random

from data_generation.domains import DOMAIN_BUILDERS, DOMAIN_SPECS
from data_generation.generation.constants import DEFAULT_SLOT_CANDIDATE_RETRIES
from data_generation.generation.constraint_plan import active_rules, col_items, global_items, row_items
from data_generation.generation.constraints import (
    aggregate_constraint_satisfied,
    item_matches_slot_constraint,
)


def build_slot_constraint(domain, row_index, col_index, candidate_ids, item_pool):
    spec = DOMAIN_SPECS[domain]
    constraint = {"row": row_index, "col": col_index}

    for rule in spec["slot_rules"]:
        values = [item_pool[candidate_id][rule["attr"]] for candidate_id in candidate_ids]
        if rule["kind"] == "max":
            constraint[rule["name"]] = max(values)
        else:
            constraint[rule["name"]] = min(values)

    return constraint


def generate_target_valid_counts(rows, cols, valid_options):
    return [valid_options for _ in range(rows * cols)]


def candidate_status(
    domain,
    truth_solution,
    item_lookup,
    row_constraints,
    col_constraints,
    global_constraints,
    row_index,
    col_index,
    candidate_id,
):
    spec = DOMAIN_SPECS[domain]
    trial_solution = [row[:] for row in truth_solution]
    trial_solution[row_index][col_index] = candidate_id

    row_group = row_items(trial_solution, item_lookup, row_index)
    row_ok = all(
        aggregate_constraint_satisfied(rule, row_constraints[row_index][rule["name"]], row_group)
        for rule in active_rules(spec["row_rules"], row_constraints[row_index])
    )

    col_group = col_items(trial_solution, item_lookup, col_index)
    col_ok = all(
        aggregate_constraint_satisfied(rule, col_constraints[col_index][rule["name"]], col_group)
        for rule in active_rules(spec["col_rules"], col_constraints[col_index])
    )

    global_group = global_items(trial_solution, item_lookup)
    global_ok = all(
        aggregate_constraint_satisfied(
            rule,
            global_constraints[rule["name"]],
            global_group,
            truth_solution=trial_solution,
            item_lookup=item_lookup,
        )
        for rule in active_rules(spec["global_rules"], global_constraints)
    )

    return row_ok, col_ok, global_ok


def build_slot_entry(
    domain,
    truth_solution,
    item_pool,
    row_constraints,
    col_constraints,
    global_constraints,
    row_index,
    col_index,
    target_valid_count,
    candidates_per_slot,
    next_index,
):
    spec = DOMAIN_SPECS[domain]
    builder = DOMAIN_BUILDERS[domain]
    id_key = spec["id_key"]
    truth_id = truth_solution[row_index][col_index]
    item_lookup = item_pool

    valid_ids = [truth_id]
    distractor_ids = []

    for _ in range(DEFAULT_SLOT_CANDIDATE_RETRIES):
        if len(valid_ids) >= target_valid_count and len(valid_ids) + len(distractor_ids) >= candidates_per_slot:
            break

        candidate = builder(next_index)
        next_index += 1
        candidate_id = candidate[id_key]
        if candidate_id in item_pool:
            continue

        trial_lookup = dict(item_lookup)
        trial_lookup[candidate_id] = candidate
        row_ok, col_ok, global_ok = candidate_status(
            domain,
            truth_solution,
            trial_lookup,
            row_constraints,
            col_constraints,
            global_constraints,
            row_index,
            col_index,
            candidate_id,
        )

        if row_ok and col_ok and global_ok:
            if len(valid_ids) < target_valid_count:
                item_pool[candidate_id] = candidate
                valid_ids.append(candidate_id)
        elif (not row_ok or not col_ok) and len(valid_ids) + len(distractor_ids) < candidates_per_slot:
            item_pool[candidate_id] = candidate
            distractor_ids.append(candidate_id)

    if len(valid_ids) < target_valid_count or len(valid_ids) + len(distractor_ids) < candidates_per_slot:
        return None, next_index

    candidate_ids = valid_ids + distractor_ids[: candidates_per_slot - len(valid_ids)]
    random.shuffle(candidate_ids)
    slot_constraints = build_slot_constraint(domain, row_index, col_index, candidate_ids, item_pool)

    if not all(
        item_matches_slot_constraint(item_pool[candidate_id], slot_constraints, spec["slot_rules"])
        for candidate_id in candidate_ids
    ):
        return None, next_index

    return {
        "row": row_index,
        "col": col_index,
        "truth_id": truth_id,
        "slot_constraints": slot_constraints,
        "candidate_ids": candidate_ids,
        "valid_candidate_ids": valid_ids[:],
    }, next_index
