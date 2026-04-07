"""
show.interaction - interactive logic.
"""

import os

DEFAULT_RESULTS_PATH = "results"


def _validate_dataset():
    """Validate the dataset. Logic to be added later."""
    print("\n[Validate Dataset] Feature not yet implemented.\n")


def _view_results(results_path: str) -> None:
    """View results."""
    if not os.path.isdir(results_path):
        print(f"\nPath does not exist or is not a directory: {results_path}\n")
        return
    # Can call plot_results or display a result list here later
    print(f"\n[View Results] Path: {results_path}")
    print("(Result display and plotting logic not yet implemented)\n")


def run_interactive() -> None:
    """Run the interactive main menu."""
    while True:
        print("\n" + "=" * 50)
        print("  Cached Agent Benchmark - Interactive Menu")
        print("=" * 50)
        print("  1. Validate dataset")
        print("  2. View results")
        print("  q. Quit")
        print("=" * 50)

        choice = input("Select [1/2/q]: ").strip().lower()

        if choice == "q":
            print("\nGoodbye.\n")
            break

        if choice == "1":
            _validate_dataset()
            continue

        if choice == "2":
            default_hint = f"(press Enter to use default: {DEFAULT_RESULTS_PATH})"
            path_input = input(f"\nEnter results path {default_hint}: ").strip()
            results_path = path_input if path_input else DEFAULT_RESULTS_PATH
            _view_results(results_path)
            continue

        print("\nInvalid option, please try again.\n")
