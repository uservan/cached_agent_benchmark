#!/usr/bin/env python3
"""show.py - Interactive eval result viewer. Run directly to enter the interface."""
from pathlib import Path

from utils.console_display import ConsoleDisplay

from show.view_results import (
    BACK,
    MAIN,
    get_domains,
    prompt_model,
    prompt_path,
    run_average_results,
    run_specific_results,
)


DEFAULT_DATASET_DIR = "data/5x10"


def validate_dataset() -> None:
    """Validate a dataset file using data_generation/validation.py."""
    from data_generation.validation import (
        _load_payload,
        _summarize_instance,
        _choose_representative_instances,
        _print_instance_summary,
        _build_truth_report,
        _print_decoy_stage_report,
        _print_truth_decoy_combination_stats,
        _print_representative_cases,
        validate_dataset as _validate_dataset,
    )

    while True:
        ConsoleDisplay.console.print(f"\n[bold]Enter dataset directory[/bold] [dim](default: {DEFAULT_DATASET_DIR})[/dim]")
        ConsoleDisplay.console.print("  [dim]0 = back[/dim]")
        inp = ConsoleDisplay.console.input("[bold cyan]> [/bold cyan]").strip()
        if inp == "0":
            return
        dir_path = Path(inp or DEFAULT_DATASET_DIR)

        if not dir_path.is_dir():
            ConsoleDisplay.console.print(f"[red]Directory not found: {dir_path}. Please try again.[/red]")
            continue

        json_files = sorted(dir_path.glob("*.json"))
        if not json_files:
            ConsoleDisplay.console.print(f"[red]No JSON files found in {dir_path}. Please try again.[/red]")
            continue

        while True:
            ConsoleDisplay.console.print(f"\n[bold]Select a dataset file[/bold] [dim]({dir_path})[/dim]")
            for i, f in enumerate(json_files, 1):
                ConsoleDisplay.console.print(f"  {i}. {f.name}")
            ConsoleDisplay.console.print("  [dim]0 = back[/dim]")

            sel = ConsoleDisplay.console.input("[bold cyan]> [/bold cyan]").strip()
            if sel == "0":
                break
            if not sel.isdigit() or not (1 <= int(sel) <= len(json_files)):
                ConsoleDisplay.console.print("[red]Invalid selection. Please try again.[/red]")
                continue

            path = json_files[int(sel) - 1]

            try:
                payload = _load_payload(str(path))
            except Exception as e:
                ConsoleDisplay.console.print(f"[red]Failed to load file: {e}. Please try again.[/red]")
                continue

            instances = payload["instances"]
            summaries = []
            failed = []
            for dataset in instances:
                summaries.append(_summarize_instance(dataset))
                if not _validate_dataset(dataset):
                    failed.append(dataset.get("instance_id", "-"))

            ConsoleDisplay.print_dataset_summary_report(payload["domain"], summaries)

            if failed:
                ConsoleDisplay.console.print(f"[red]Validation FAILED for instances: {', '.join(failed)}[/red]")
            else:
                ConsoleDisplay.console.print("[green]All instances passed validation.[/green]")

            for dataset in _choose_representative_instances(instances):
                ConsoleDisplay.print_validation_summary(
                    dataset.get("instance_id", "-"),
                    dataset["domain"],
                    True,
                )
                _print_instance_summary(dataset)
                ConsoleDisplay.print_solution_report("Truth solution report", _build_truth_report(dataset))
                _print_decoy_stage_report(dataset)
                _print_truth_decoy_combination_stats(dataset)
                _print_representative_cases(dataset)
            # validation done, return to file list


def view_eval_results() -> None:
    """Main flow for viewing eval results."""
    from show.view_results import _prompt_choice

    while True:
        base_path = prompt_path(default="results/5x7/ids5_fields5_eq-1_alpha-1")
        if base_path == MAIN:
            return

        while True:
            ConsoleDisplay.console.print("\n[bold]Select model:[/bold]")
            model = prompt_model(base_path)
            if model is None:
                break
            if model == MAIN:
                return
            if model == BACK:
                break

            while True:
                ConsoleDisplay.console.print("\n[bold]Choose action:[/bold]")
                ConsoleDisplay.console.print("  1. View average results")
                ConsoleDisplay.console.print("  2. View specific result")
                ConsoleDisplay.console.print("  [dim]0 = back, m = main menu[/dim]")
                inp = ConsoleDisplay.console.input("[bold cyan]> [/bold cyan]").strip().lower() or "1"

                if inp == "m":
                    return
                if inp == "0":
                    break
                if inp not in ("1", "2"):
                    ConsoleDisplay.console.print("[red]Invalid option. Please enter 1, 2, 0, or m.[/red]")
                    continue

                if inp == "2":
                    nav = run_specific_results(base_path, model)
                    if nav == MAIN:
                        return
                    if nav == BACK:
                        continue
                    continue

                # Average results
                model_path = Path(base_path) / model
                domains = get_domains(model_path)
                if not domains:
                    ConsoleDisplay.console.print("[red]No domain found.[/red]")
                    continue

                domain_options = ["all"] + domains
                ConsoleDisplay.console.print("\n[bold]Choose domain (all = aggregate all):[/bold]")
                chosen = _prompt_choice("[bold cyan]> [/bold cyan]", domain_options, "all")
                if chosen == MAIN:
                    return
                if chosen == BACK:
                    continue

                domain_filter = None if chosen == "all" else chosen
                run_average_results(base_path, model, domain_filter)
                continue
            continue


def main() -> None:
    """Interactive entry point."""
    while True:
        ConsoleDisplay.console.print("\n[bold green]=== Cached Agent Benchmark - Result Viewer ===[/bold green]\n")
        ConsoleDisplay.console.print("[bold]Choose an option:[/bold]")
        ConsoleDisplay.console.print("  1. Validate dataset")
        ConsoleDisplay.console.print("  2. View eval results")
        ConsoleDisplay.console.print("  3. Exit")
        inp = ConsoleDisplay.console.input("[bold cyan]> [/bold cyan]").strip() or "2"

        if inp == "3":
            ConsoleDisplay.console.print("[green]Goodbye.[/green]")
            break
        if inp == "1":
            validate_dataset()
        elif inp == "2":
            view_eval_results()
        else:
            ConsoleDisplay.console.print("[red]Invalid option. Please enter 1, 2, or 3.[/red]")


if __name__ == "__main__":
    main()
