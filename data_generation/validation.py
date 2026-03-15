import json

try:
    from .config import (
        DEFAULT_CANDIDATES_PER_SLOT,
        DEFAULT_VALID_OPTIONS,
    )
    from .constraints import aggregate_constraint_satisfied, item_matches_slot_constraint
    from .domains import DOMAIN_SPECS
except ImportError:
    from config import (
        DEFAULT_CANDIDATES_PER_SLOT,
        DEFAULT_VALID_OPTIONS,
    )
    from constraints import aggregate_constraint_satisfied, item_matches_slot_constraint
    from domains import DOMAIN_SPECS


def build_constraint_maps(dataset):
    slot_map = {(slot["row"], slot["col"]): slot for slot in dataset["slots"]}
    row_map = {constraint["row"]: constraint for constraint in dataset["row_constraints"]}
    col_map = {constraint["col"]: constraint for constraint in dataset["col_constraints"]}
    return slot_map, row_map, col_map


def row_items(truth_solution, item_lookup, row_index):
    return [item_lookup[item_id] for item_id in truth_solution[row_index]]


def col_items(truth_solution, item_lookup, col_index):
    return [item_lookup[truth_solution[row_index][col_index]] for row_index in range(len(truth_solution))]


def global_items(truth_solution, item_lookup):
    return [item_lookup[item_id] for row in truth_solution for item_id in row]


def candidate_is_valid(dataset, row_index, col_index, candidate_id):
    domain = dataset["domain"]
    spec = DOMAIN_SPECS[domain]
    item_lookup = dataset["item_pool"]
    truth_solution = [row[:] for row in dataset["truth_solution"]]
    slot_map, row_map, col_map = build_constraint_maps(dataset)
    slot_entry = slot_map[(row_index, col_index)]
    candidate = item_lookup[candidate_id]

    if not item_matches_slot_constraint(candidate, slot_entry["slot_constraints"], spec["slot_rules"]):
        return False

    truth_solution[row_index][col_index] = candidate_id
    row_group = row_items(truth_solution, item_lookup, row_index)
    row_ok = all(
        aggregate_constraint_satisfied(rule, row_map[row_index][rule["name"]], row_group)
        for rule in spec["row_rules"]
    )
    if not row_ok:
        return False

    col_group = col_items(truth_solution, item_lookup, col_index)
    col_ok = all(
        aggregate_constraint_satisfied(rule, col_map[col_index][rule["name"]], col_group)
        for rule in spec["col_rules"]
    )
    if not col_ok:
        return False

    global_group = global_items(truth_solution, item_lookup)
    return all(
        aggregate_constraint_satisfied(
            rule,
            dataset["global_constraints"][rule["name"]],
            global_group,
            truth_solution=truth_solution,
            item_lookup=item_lookup,
        )
        for rule in spec["global_rules"]
    )


def count_candidates_for_slot(dataset, row_index, col_index):
    slot_map, _, _ = build_constraint_maps(dataset)
    return len(slot_map[(row_index, col_index)]["candidate_ids"])


def count_valid_options_for_slot(dataset, row_index, col_index):
    slot_map, _, _ = build_constraint_maps(dataset)
    candidate_ids = slot_map[(row_index, col_index)]["candidate_ids"]
    return sum(1 for candidate_id in candidate_ids if candidate_is_valid(dataset, row_index, col_index, candidate_id))


def validate_truth_solution(dataset):
    rows = dataset["meta"]["rows"]
    cols = dataset["meta"]["cols"]
    item_lookup = dataset["item_pool"]
    truth_solution = dataset["truth_solution"]
    slot_map, row_map, col_map = build_constraint_maps(dataset)
    domain = dataset["domain"]
    spec = DOMAIN_SPECS[domain]

    for row_index in range(rows):
        for col_index in range(cols):
            truth_id = truth_solution[row_index][col_index]
            if truth_id not in item_lookup:
                return False
            slot_entry = slot_map[(row_index, col_index)]
            if slot_entry["truth_id"] != truth_id:
                return False
            if truth_id not in slot_entry["candidate_ids"]:
                return False
            if truth_id not in slot_entry.get("valid_candidate_ids", []):
                return False
            if not item_matches_slot_constraint(item_lookup[truth_id], slot_entry["slot_constraints"], spec["slot_rules"]):
                return False

    for row_index in range(rows):
        row_group = row_items(truth_solution, item_lookup, row_index)
        for rule in spec["row_rules"]:
            if not aggregate_constraint_satisfied(rule, row_map[row_index][rule["name"]], row_group):
                return False

    for col_index in range(cols):
        col_group = col_items(truth_solution, item_lookup, col_index)
        for rule in spec["col_rules"]:
            if not aggregate_constraint_satisfied(rule, col_map[col_index][rule["name"]], col_group):
                return False

    global_group = global_items(truth_solution, item_lookup)
    for rule in spec["global_rules"]:
        if not aggregate_constraint_satisfied(
            rule,
            dataset["global_constraints"][rule["name"]],
            global_group,
            truth_solution=truth_solution,
            item_lookup=item_lookup,
        ):
            return False

    return True


def validate_dataset(
    dataset,
    candidates_per_slot=DEFAULT_CANDIDATES_PER_SLOT,
    valid_options=DEFAULT_VALID_OPTIONS,
):
    if not validate_truth_solution(dataset):
        return False

    rows = dataset["meta"]["rows"]
    cols = dataset["meta"]["cols"]
    valid_counts = []

    for row_index in range(rows):
        for col_index in range(cols):
            slot_map, _, _ = build_constraint_maps(dataset)
            slot_entry = slot_map[(row_index, col_index)]

            if len(slot_entry["candidate_ids"]) != candidates_per_slot:
                return False
            if len(set(slot_entry["candidate_ids"])) != len(slot_entry["candidate_ids"]):
                return False
            valid_candidate_ids = slot_entry.get("valid_candidate_ids")
            if valid_candidate_ids is None:
                return False
            if len(set(valid_candidate_ids)) != len(valid_candidate_ids):
                return False
            if any(candidate_id not in slot_entry["candidate_ids"] for candidate_id in valid_candidate_ids):
                return False
            if any(candidate_id not in dataset["item_pool"] for candidate_id in slot_entry["candidate_ids"]):
                return False
            if any(
                not item_matches_slot_constraint(
                    dataset["item_pool"][candidate_id],
                    slot_entry["slot_constraints"],
                    DOMAIN_SPECS[dataset["domain"]]["slot_rules"],
                )
                for candidate_id in slot_entry["candidate_ids"]
            ):
                return False

            valid_count = count_valid_options_for_slot(dataset, row_index, col_index)
            computed_valid_ids = [
                candidate_id
                for candidate_id in slot_entry["candidate_ids"]
                if candidate_is_valid(dataset, row_index, col_index, candidate_id)
            ]
            if set(computed_valid_ids) != set(valid_candidate_ids):
                return False
            if valid_count != valid_options:
                return False
            valid_counts.append(valid_count)
    return all(count == valid_options for count in valid_counts)


def summarize_dataset(dataset):
    rows = dataset["meta"]["rows"]
    cols = dataset["meta"]["cols"]
    candidate_counts = []
    valid_counts = []

    for row_index in range(rows):
        for col_index in range(cols):
            candidate_counts.append(count_candidates_for_slot(dataset, row_index, col_index))
            valid_counts.append(count_valid_options_for_slot(dataset, row_index, col_index))

    return {
        "instance_id": dataset.get("instance_id"),
        "min_candidates": min(candidate_counts),
        "max_candidates": max(candidate_counts),
        "avg_candidates": round(sum(candidate_counts) / len(candidate_counts), 2),
        "min_valid_options": min(valid_counts),
        "max_valid_options": max(valid_counts),
        "avg_valid_options": round(sum(valid_counts) / len(valid_counts), 2),
    }


def validate_payload(
    payload,
    candidates_per_slot=DEFAULT_CANDIDATES_PER_SLOT,
    valid_options=DEFAULT_VALID_OPTIONS,
):
    summaries = []
    for dataset in payload["instances"]:
        if not validate_dataset(
            dataset,
            candidates_per_slot=candidates_per_slot,
            valid_options=valid_options,
        ):
            return False, []
        summaries.append(summarize_dataset(dataset))
    return True, summaries


def validate_dataset_file(
    path,
    candidates_per_slot=DEFAULT_CANDIDATES_PER_SLOT,
    valid_options=DEFAULT_VALID_OPTIONS,
):
    with open(path, "r", encoding="utf-8") as input_file:
        payload = json.load(input_file)
    return validate_payload(
        payload,
        candidates_per_slot=candidates_per_slot,
        valid_options=valid_options,
    )
