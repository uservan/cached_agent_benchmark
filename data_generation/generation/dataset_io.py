import json

from data_generation.generation.constants import DEFAULT_CANDIDATES_PER_SLOT, DEFAULT_VALID_OPTIONS
from data_generation.validation import validate_dataset
from utils.console_display import ConsoleDisplay


def normalize_dimension_values(values):
    if isinstance(values, int):
        return [values]
    if not values:
        raise ValueError("dimension values must not be empty")
    return [int(value) for value in values]


def build_output_filename(
    domain,
    num_instances,
    rows,
    cols,
    candidates_per_slot,
    valid_options,
    seed=None,
):
    row_values = normalize_dimension_values(rows)
    col_values = normalize_dimension_values(cols)
    row_tag = "-".join(str(value) for value in row_values)
    col_tag = "-".join(str(value) for value in col_values)
    filename = (
        f"{domain}_dataset_"
        f"n{num_instances}_"
        f"r{row_tag}_"
        f"c{col_tag}_"
        f"cand{candidates_per_slot}_"
        f"valid{valid_options}"
    )
    if seed is not None:
        filename += f"_seed{seed}"
    return f"{filename}.json"


def summarize_dataset(dataset):
    candidate_counts = [len(slot["candidate_ids"]) for slot in dataset["slots"]]
    valid_counts = [len(slot.get("valid_candidate_ids", [])) for slot in dataset["slots"]]
    return {
        "instance_id": dataset.get("instance_id"),
        "avg_candidates": round(sum(candidate_counts) / len(candidate_counts), 2),
        "avg_valid_options": round(sum(valid_counts) / len(valid_counts), 2),
        "item_pool_size": len(dataset["item_pool"]),
    }


def validate_payload(payload, candidates_per_slot=DEFAULT_CANDIDATES_PER_SLOT, valid_options=DEFAULT_VALID_OPTIONS):
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


def validate_dataset_file(path, candidates_per_slot=DEFAULT_CANDIDATES_PER_SLOT, valid_options=DEFAULT_VALID_OPTIONS):
    with open(path, "r", encoding="utf-8") as input_file:
        payload = json.load(input_file)
    return validate_payload(
        payload,
        candidates_per_slot=candidates_per_slot,
        valid_options=valid_options,
    )


def print_validation_report(domain, summaries):
    ConsoleDisplay.print_dataset_summary_report(domain, summaries)
