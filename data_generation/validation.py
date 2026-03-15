import argparse
import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DEFAULT_VALIDATION_EXAMPLE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "course_dataset_n6_r5_c2-3-4-5-6-7_cand24_valid2_seed42.json",
)

try:
    from .domains import DOMAIN_SPECS
    from .generation.constants import DEFAULT_CANDIDATES_PER_SLOT, DEFAULT_VALID_OPTIONS
    from .valid.dataset_checks import validate_dataset_structure
    from .valid.scoped import validate_scope_constraints
    from .valid.utils import build_slot_map
    from utils.console_display import ConsoleDisplay
except ImportError:
    from domains import DOMAIN_SPECS
    from generation.constants import DEFAULT_CANDIDATES_PER_SLOT, DEFAULT_VALID_OPTIONS
    from valid.dataset_checks import validate_dataset_structure
    from valid.scoped import validate_scope_constraints
    from valid.utils import build_slot_map
    from utils.console_display import ConsoleDisplay


def validate_row_constraints(solution, domain, row_index, row_constraints, item_pool, slots):
    if row_index < 0 or row_index >= len(solution):
        return False, f"row {row_index} is out of range"

    row_ids = list(solution[row_index])
    positions = [(row_index, col_index, item_id) for col_index, item_id in enumerate(row_ids)]
    return validate_scope_constraints(
        solution=solution,
        domain=domain,
        index=row_index,
        ids=row_ids,
        positions=positions,
        constraint=row_constraints[row_index],
        rule_specs=DOMAIN_SPECS[domain]["row_rules"],
        item_pool=item_pool,
        slot_map=build_slot_map(slots),
        unknown_id_scope="row {index}",
        scope_text="row {index}",
    )


def validate_col_constraints(solution, domain, col_index, col_constraints, item_pool, slots):
    if not solution or col_index < 0 or col_index >= len(solution[0]):
        return False, f"column {col_index} is out of range"

    col_ids = [solution[row_index][col_index] for row_index in range(len(solution))]
    positions = [(row_index, col_index, item_id) for row_index, item_id in enumerate(col_ids)]
    return validate_scope_constraints(
        solution=solution,
        domain=domain,
        index=col_index,
        ids=col_ids,
        positions=positions,
        constraint=col_constraints[col_index],
        rule_specs=DOMAIN_SPECS[domain]["col_rules"],
        item_pool=item_pool,
        slot_map=build_slot_map(slots),
        unknown_id_scope="column {index}",
        scope_text="column {index}",
    )


def validate_global_constraints(solution, domain, global_constraints, item_pool, slots):
    global_ids = [item_id for row in solution for item_id in row]
    positions = [
        (row_index, col_index, item_id)
        for row_index, row in enumerate(solution)
        for col_index, item_id in enumerate(row)
    ]
    return validate_scope_constraints(
        solution=solution,
        domain=domain,
        index=None,
        ids=global_ids,
        positions=positions,
        constraint=global_constraints,
        rule_specs=DOMAIN_SPECS[domain]["global_rules"],
        item_pool=item_pool,
        slot_map=build_slot_map(slots),
        unknown_id_scope="the solution",
        scope_text="the whole grid",
    )


def validate_dataset(
    dataset,
    candidates_per_slot=DEFAULT_CANDIDATES_PER_SLOT,
    valid_options=DEFAULT_VALID_OPTIONS,
):
    return validate_dataset_structure(
        dataset,
        candidates_per_slot=candidates_per_slot,
        valid_options=valid_options,
        validate_row_constraints=validate_row_constraints,
        validate_col_constraints=validate_col_constraints,
        validate_global_constraints=validate_global_constraints,
    )


def _load_instance(path, instance_index):
    with open(path, "r", encoding="utf-8") as input_file:
        payload = json.load(input_file)

    if "instances" not in payload or not payload["instances"]:
        raise ValueError(f"Dataset file does not contain instances: {path}")
    if instance_index < 0 or instance_index >= len(payload["instances"]):
        raise IndexError(f"instance_index {instance_index} is out of range for {path}")
    return payload["instances"][instance_index]


def _replace_slot(solution, row_index, col_index, candidate_id):
    trial_solution = [row[:] for row in solution]
    trial_solution[row_index][col_index] = candidate_id
    return trial_solution


def _check_solution(dataset, solution):
    row_results = []
    for row_index in range(len(solution)):
        ok, reason = validate_row_constraints(
            solution,
            dataset["domain"],
            row_index,
            dataset["row_constraints"],
            dataset["item_pool"],
            dataset["slots"],
        )
        row_results.append({"row": row_index, "ok": ok, "reason": reason})

    col_results = []
    if solution:
        for col_index in range(len(solution[0])):
            ok, reason = validate_col_constraints(
                solution,
                dataset["domain"],
                col_index,
                dataset["col_constraints"],
                dataset["item_pool"],
                dataset["slots"],
            )
            col_results.append({"col": col_index, "ok": ok, "reason": reason})

    global_ok, global_reason = validate_global_constraints(
        solution,
        dataset["domain"],
        dataset["global_constraints"],
        dataset["item_pool"],
        dataset["slots"],
    )

    return {
        "rows": row_results,
        "cols": col_results,
        "global": {"ok": global_ok, "reason": global_reason},
    }


def _build_slot_examples(dataset, max_examples_per_slot=4):
    examples = []
    truth_solution = dataset["truth_solution"]

    for slot in dataset["slots"]:
        row_index = slot["row"]
        col_index = slot["col"]
        slot_examples = []

        for candidate_id in slot["candidate_ids"]:
            if candidate_id == slot["truth_id"]:
                continue

            trial_solution = _replace_slot(truth_solution, row_index, col_index, candidate_id)
            row_ok, row_reason = validate_row_constraints(
                trial_solution,
                dataset["domain"],
                row_index,
                dataset["row_constraints"],
                dataset["item_pool"],
                dataset["slots"],
            )
            col_ok, col_reason = validate_col_constraints(
                trial_solution,
                dataset["domain"],
                col_index,
                dataset["col_constraints"],
                dataset["item_pool"],
                dataset["slots"],
            )
            global_ok, global_reason = validate_global_constraints(
                trial_solution,
                dataset["domain"],
                dataset["global_constraints"],
                dataset["item_pool"],
                dataset["slots"],
            )

            slot_examples.append({
                "candidate_id": candidate_id,
                "is_valid_candidate": candidate_id in slot.get("valid_candidate_ids", []),
                "row_ok": row_ok,
                "row_reason": row_reason,
                "col_ok": col_ok,
                "col_reason": col_reason,
                "global_ok": global_ok,
                "global_reason": global_reason,
            })

            if len(slot_examples) >= max_examples_per_slot:
                break

        examples.append({
            "row": row_index,
            "col": col_index,
            "truth_id": slot["truth_id"],
            "valid_candidate_ids": slot.get("valid_candidate_ids", []),
            "examples": slot_examples,
        })

    return examples


def _print_solution_report(title, solution_report):
    ConsoleDisplay.print_solution_report(title, solution_report)


def _print_slot_examples(slot_examples):
    ConsoleDisplay.print_slot_examples(slot_examples)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Validate and inspect a generated dataset instance.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            f"  python data_generation/validation.py {DEFAULT_VALIDATION_EXAMPLE_PATH}\n"
            f"  python data_generation/validation.py {DEFAULT_VALIDATION_EXAMPLE_PATH} --instance-index 1 --max-examples-per-slot 2"
        ),
    )
    parser.add_argument(
        "dataset_path",
        nargs="?",
        default=DEFAULT_VALIDATION_EXAMPLE_PATH,
        help=f"Path to a generated dataset JSON file. Default example: {DEFAULT_VALIDATION_EXAMPLE_PATH}",
    )
    parser.add_argument(
        "--instance-index",
        type=int,
        default=0,
        help="Instance index in the dataset file. Default: 0.",
    )
    parser.add_argument(
        "--max-examples-per-slot",
        type=int,
        default=4,
        help="Maximum number of alternative candidate substitutions to print for each slot. Default: 4.",
    )
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    dataset = _load_instance(args.dataset_path, args.instance_index)
    is_valid = validate_dataset(dataset)
    ConsoleDisplay.print_validation_summary(
        dataset.get("instance_id", str(args.instance_index)),
        dataset["domain"],
        is_valid,
    )

    truth_report = _check_solution(dataset, dataset["truth_solution"])
    _print_solution_report("Truth solution report:", truth_report)

    slot_examples = _build_slot_examples(
        dataset,
        max_examples_per_slot=args.max_examples_per_slot,
    )
    _print_slot_examples(slot_examples)


if __name__ == "__main__":
    main()
