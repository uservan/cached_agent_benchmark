import argparse
import json
import os
import random
import sys
from itertools import product

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data_generation.generation.constants import (
    DEFAULT_CANDIDATES_PER_SLOT,
    DEFAULT_COLS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_NUM_INSTANCES,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_ROWS,
    DEFAULT_VALID_OPTIONS,
)
from data_generation.domains import SUPPORTED_DOMAINS
from data_generation.generation.dataset_io import (
    build_output_filename,
    normalize_dimension_values,
    print_validation_report,
    validate_dataset_file,
    validate_payload,
)
from data_generation.generation.instance_builder import build_instance
from data_generation.validation import validate_dataset
from utils.console_display import ConsoleDisplay


def generate_dataset(
    domain="course",
    num_instances=DEFAULT_NUM_INSTANCES,
    rows=DEFAULT_ROWS,
    cols=DEFAULT_COLS,
    output_dir=DEFAULT_OUTPUT_DIR,
    candidates_per_slot=DEFAULT_CANDIDATES_PER_SLOT,
    valid_options=DEFAULT_VALID_OPTIONS,
    seed=None,
):
    if domain not in SUPPORTED_DOMAINS:
        raise ValueError(f"Unsupported domain: {domain}")
    if candidates_per_slot < valid_options:
        raise ValueError("candidates_per_slot must be greater than or equal to valid_options")
    row_values = normalize_dimension_values(rows)
    col_values = normalize_dimension_values(cols)
    if seed is not None:
        random.seed(seed)

    instances = []
    for row_count, col_count in product(row_values, col_values):
        for instance_index in range(num_instances):
            dataset = None
            for _ in range(DEFAULT_MAX_RETRIES):
                candidate = build_instance(
                    domain,
                    rows=row_count,
                    cols=col_count,
                    candidates_per_slot=candidates_per_slot,
                    valid_options=valid_options,
                )
                if candidate is None:
                    continue
                if validate_dataset(
                    candidate,
                    candidates_per_slot=candidates_per_slot,
                    valid_options=valid_options,
                ):
                    dataset = candidate
                    break
            if dataset is None:
                raise RuntimeError(
                    f"Failed to build a valid dataset for domain '{domain}' with rows={row_count}, cols={col_count}"
                )

            dataset["instance_id"] = f"{domain}_r{row_count}_c{col_count}_{instance_index:03d}"
            instances.append(dataset)

    os.makedirs(output_dir, exist_ok=True)
    output_filename = build_output_filename(
        domain=domain,
        num_instances=len(instances),
        rows=row_values,
        cols=col_values,
        candidates_per_slot=candidates_per_slot,
        valid_options=valid_options,
        seed=seed,
    )
    output_path = os.path.join(output_dir, output_filename)
    payload = {
        "domain": domain,
        "num_instances": len(instances),
        "instances": instances,
    }

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, indent=2)

    is_valid, _ = validate_payload(
        payload,
        candidates_per_slot=candidates_per_slot,
        valid_options=valid_options,
    )
    if not is_valid:
        raise RuntimeError(f"Generated dataset failed validation: {output_path}")

    return payload


def generate_all_datasets(
    domains=SUPPORTED_DOMAINS,
    num_instances=DEFAULT_NUM_INSTANCES,
    rows=DEFAULT_ROWS,
    cols=DEFAULT_COLS,
    output_dir=DEFAULT_OUTPUT_DIR,
    candidates_per_slot=DEFAULT_CANDIDATES_PER_SLOT,
    valid_options=DEFAULT_VALID_OPTIONS,
    seed=None,
):
    results = {}
    for domain in domains:
        results[domain] = generate_dataset(
            domain=domain,
            num_instances=num_instances,
            rows=rows,
            cols=cols,
            output_dir=output_dir,
            candidates_per_slot=candidates_per_slot,
            valid_options=valid_options,
            seed=seed,
        )
    return results


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Generate or validate planning datasets.")
    parser.add_argument("--domain", choices=SUPPORTED_DOMAINS, help="Generate a single domain dataset.")
    parser.add_argument("--all-domains", action="store_true", help="Generate datasets for all supported domains.")
    parser.add_argument("--num-instances", type=int, default=DEFAULT_NUM_INSTANCES, help="Number of instances per domain.")
    parser.add_argument("--rows", type=int, nargs="+", default=[DEFAULT_ROWS], help="One or more grid row counts.")
    parser.add_argument("--cols", type=int, nargs="+", default=[DEFAULT_COLS], help="One or more grid column counts.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory for generated dataset files.")
    parser.add_argument(
        "--candidates-per-slot",
        type=int,
        default=DEFAULT_CANDIDATES_PER_SLOT,
        help="Number of visible candidate ids stored for each slot.",
    )
    parser.add_argument(
        "--valid-options",
        type=int,
        default=DEFAULT_VALID_OPTIONS,
        help="Exact number of row/col-valid candidates required per slot.",
    )
    parser.add_argument("--seed", type=int, help="Optional random seed for reproducible generation.")
    parser.add_argument("--validate-file", help="Validate an existing dataset JSON file instead of generating.")
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()
    row_values = normalize_dimension_values(args.rows)
    col_values = normalize_dimension_values(args.cols)

    if args.candidates_per_slot < args.valid_options:
        raise SystemExit("--candidates-per-slot must be greater than or equal to --valid-options")

    if args.seed is not None:
        random.seed(args.seed)

    if args.validate_file:
        is_valid, summaries = validate_dataset_file(
            args.validate_file,
            candidates_per_slot=args.candidates_per_slot,
            valid_options=args.valid_options,
        )
        if not is_valid:
            raise SystemExit(f"Validation failed: {args.validate_file}")
        ConsoleDisplay.print_kv_panel(
            title="[bold green]File Validation[/bold green]",
            items=[
                ("File", args.validate_file),
                ("Status", "[green]PASS[/green]"),
            ],
            border_style="green",
        )
        print_validation_report("file", summaries)
        return

    if args.all_domains:
        payloads = generate_all_datasets(
            num_instances=args.num_instances,
            rows=row_values,
            cols=col_values,
            output_dir=args.output_dir,
            candidates_per_slot=args.candidates_per_slot,
            valid_options=args.valid_options,
            seed=args.seed,
        )
        for domain, payload in payloads.items():
            _, summaries = validate_payload(
                payload,
                candidates_per_slot=args.candidates_per_slot,
                valid_options=args.valid_options,
            )
            print_validation_report(domain, summaries)
        return

    domain = args.domain or "course"
    payload = generate_dataset(
        domain=domain,
        num_instances=args.num_instances,
        rows=row_values,
        cols=col_values,
        output_dir=args.output_dir,
        candidates_per_slot=args.candidates_per_slot,
        valid_options=args.valid_options,
        seed=args.seed,
    )
    _, summaries = validate_payload(
        payload,
        candidates_per_slot=args.candidates_per_slot,
        valid_options=args.valid_options,
    )
    print_validation_report(domain, summaries)


if __name__ == "__main__":
    main()
