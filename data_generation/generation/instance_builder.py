from data_generation.generation.constants import (
    DEFAULT_CANDIDATES_PER_SLOT,
    DEFAULT_COLS,
    DEFAULT_ROWS,
    DEFAULT_VALID_OPTIONS,
)
from data_generation.generation.constraint_plan import build_truth_constraints
from data_generation.generation.items import generate_item_pool, generate_truth_solution
from data_generation.generation.slot_candidates import build_slot_entry, generate_target_valid_counts
from data_generation.generation.task_instruction import build_task_instruction_from_instance


def build_instance(
    domain,
    rows=DEFAULT_ROWS,
    cols=DEFAULT_COLS,
    candidates_per_slot=DEFAULT_CANDIDATES_PER_SLOT,
    valid_options=DEFAULT_VALID_OPTIONS,
):
    total_cells = rows * cols
    base_pool = generate_item_pool(
        domain,
        total_cells=total_cells,
        min_valid_options=valid_options,
        max_valid_options=valid_options,
    )
    truth_solution, base_lookup = generate_truth_solution(domain, base_pool, rows=rows, cols=cols)
    truth_ids = {item_id for row in truth_solution for item_id in row}
    item_pool = {item_id: base_lookup[item_id] for item_id in truth_ids}

    row_constraints, col_constraints, global_constraints = build_truth_constraints(
        domain,
        truth_solution,
        item_pool,
        rows,
        cols,
    )

    target_valid_counts = generate_target_valid_counts(
        rows,
        cols,
        valid_options,
    )

    slots = []
    next_index = len(base_pool)
    for slot_index in range(total_cells):
        row_index = slot_index // cols
        col_index = slot_index % cols
        slot_entry, next_index = build_slot_entry(
            domain,
            truth_solution,
            item_pool,
            row_constraints,
            col_constraints,
            global_constraints,
            row_index,
            col_index,
            target_valid_counts[slot_index],
            candidates_per_slot,
            next_index,
        )
        if slot_entry is None:
            return None
        slots.append(slot_entry)

    instance = {
        "domain": domain,
        "meta": {"rows": rows, "cols": cols},
        "global_constraints": global_constraints,
        "item_pool": item_pool,
        "truth_solution": truth_solution,
        "row_constraints": row_constraints,
        "col_constraints": col_constraints,
        "slots": slots,
    }
    instance["task_instruction"] = build_task_instruction_from_instance(instance)
    return instance
