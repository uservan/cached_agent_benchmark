from data_generation.domains import DOMAIN_SPECS
from data_generation.generation.constraints import item_matches_slot_constraint
from data_generation.valid.utils import build_constraint_maps


def validate_dataset_structure(
    dataset,
    *,
    candidates_per_slot,
    valid_options,
    validate_row_constraints,
    validate_col_constraints,
    validate_global_constraints,
):
    domain = dataset["domain"]
    spec = DOMAIN_SPECS[domain]
    item_pool = dataset["item_pool"]
    truth_solution = dataset["truth_solution"]
    rows = dataset["meta"]["rows"]
    cols = dataset["meta"]["cols"]
    slot_map, _, _ = build_constraint_maps(dataset)

    for row_index in range(rows):
        for col_index in range(cols):
            truth_id = truth_solution[row_index][col_index]
            if truth_id not in item_pool:
                return False
            slot_entry = slot_map[(row_index, col_index)]
            if slot_entry["truth_id"] != truth_id:
                return False
            if len(slot_entry["candidate_ids"]) != candidates_per_slot:
                return False
            if len(set(slot_entry["candidate_ids"])) != len(slot_entry["candidate_ids"]):
                return False
            valid_candidate_ids = slot_entry.get("valid_candidate_ids")
            if valid_candidate_ids is None or len(set(valid_candidate_ids)) != len(valid_candidate_ids):
                return False
            if truth_id not in slot_entry["candidate_ids"] or truth_id not in valid_candidate_ids:
                return False
            if any(candidate_id not in slot_entry["candidate_ids"] for candidate_id in valid_candidate_ids):
                return False
            if any(candidate_id not in item_pool for candidate_id in slot_entry["candidate_ids"]):
                return False
            if any(
                not item_matches_slot_constraint(
                    item_pool[candidate_id],
                    slot_entry["slot_constraints"],
                    spec["slot_rules"],
                )
                for candidate_id in slot_entry["candidate_ids"]
            ):
                return False

            computed_valid_ids = []
            for candidate_id in slot_entry["candidate_ids"]:
                trial_solution = [row[:] for row in truth_solution]
                trial_solution[row_index][col_index] = candidate_id
                row_ok, _ = validate_row_constraints(
                    trial_solution,
                    domain,
                    row_index,
                    dataset["row_constraints"],
                    item_pool,
                    dataset["slots"],
                )
                if not row_ok:
                    continue
                col_ok, _ = validate_col_constraints(
                    trial_solution,
                    domain,
                    col_index,
                    dataset["col_constraints"],
                    item_pool,
                    dataset["slots"],
                )
                if not col_ok:
                    continue
                global_ok, _ = validate_global_constraints(
                    trial_solution,
                    domain,
                    dataset["global_constraints"],
                    item_pool,
                    dataset["slots"],
                )
                if global_ok:
                    computed_valid_ids.append(candidate_id)
            if set(computed_valid_ids) != set(valid_candidate_ids):
                return False
            if len(computed_valid_ids) != valid_options:
                return False

    for row_index in range(rows):
        row_ok, _ = validate_row_constraints(
            truth_solution,
            domain,
            row_index,
            dataset["row_constraints"],
            item_pool,
            dataset["slots"],
        )
        if not row_ok:
            return False

    for col_index in range(cols):
        col_ok, _ = validate_col_constraints(
            truth_solution,
            domain,
            col_index,
            dataset["col_constraints"],
            item_pool,
            dataset["slots"],
        )
        if not col_ok:
            return False

    global_ok, _ = validate_global_constraints(
        truth_solution,
        domain,
        dataset["global_constraints"],
        item_pool,
        dataset["slots"],
    )
    return global_ok
