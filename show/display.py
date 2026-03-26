"""Terminal display: matrices and single result using ConsoleDisplay."""
from typing import Any

from utils.console_display import ConsoleDisplay


def _fmt(v: float | None) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return f"{v:.2f}"
    return str(v)


def _fmt_pct(v: float | None) -> str:
    if v is None:
        return "-"
    return f"{v * 100:.2f}%"


def print_matrix(
    matrix: dict[tuple[int, int], float],
    hidden_list: list[int],
    branch_list: list[int],
    title: str,
    *,
    percent: bool = False,
) -> None:
    """Print matrix with branch_budget as rows, hidden_slots as columns."""
    if not hidden_list or not branch_list:
        ConsoleDisplay.console.print(f"[{title}] No data")
        return

    headers = ["b\\h"] + [str(h) for h in hidden_list]
    rows = []
    for b in branch_list:
        formatter = _fmt_pct if percent else _fmt
        row_vals = [formatter(matrix.get((h, b))) for h in hidden_list]
        rows.append([str(b)] + row_vals)

    ConsoleDisplay.print_table(
        title=title,
        headers=headers,
        rows=rows,
        panel_title=f"[bold blue]{title}[/bold blue]",
        border_style="blue",
    )


def print_average_matrices(
    avg_data: dict[str, dict[tuple[int, int], float]],
    hidden_list: list[int],
    branch_list: list[int],
) -> None:
    """Print matrices for score, completion_tokens, cost, time, tool_calls_num, step_num."""
    titles = {
        "score": "Average Score",
        "completion_tokens": "Average Completion Tokens",
        "cost": "Average Cost",
        "time": "Average Time (s)",
        "tool_calls_num": "Average Tool Calls",
        "step_num": "Average Steps",
    }
    for key, title in titles.items():
        m = avg_data.get(key, {})
        print_matrix(m, hidden_list, branch_list, title, percent=(key == "score"))


def print_overall_average(overall_avg: dict[str, float]) -> None:
    """Print overall averages across all hidden/branch runs."""
    items = [
        ("score", _fmt_pct(overall_avg.get("score"))),
        ("completion_tokens", _fmt(overall_avg.get("completion_tokens"))),
        ("cost", _fmt(overall_avg.get("cost"))),
        ("time (s)", _fmt(overall_avg.get("time"))),
        ("tool_calls_num", _fmt(overall_avg.get("tool_calls_num"))),
        ("step_num", _fmt(overall_avg.get("step_num"))),
    ]
    ConsoleDisplay.print_kv_panel(
        title="[bold green]All Average[/bold green]",
        items=items,
        border_style="green",
    )


def print_model_ranking(ranked_models: list[dict[str, Any]]) -> None:
    """Print overall model ranking by combined ordering."""
    rows = []
    for idx, model_info in enumerate(ranked_models, 1):
        overall_avg = model_info["overall_avg"]
        rows.append(
            [
                str(idx),
                model_info["model"],
                _fmt_pct(overall_avg.get("score")),
                _fmt(overall_avg.get("completion_tokens")),
                _fmt(overall_avg.get("cost")),
                _fmt(overall_avg.get("time")),
                _fmt(overall_avg.get("tool_calls_num")),
                _fmt(overall_avg.get("step_num")),
            ]
        )

    ConsoleDisplay.print_table(
        title="Overall Model Ranking",
        headers=[
            "Rank",
            "Model",
            "Score",
            "Completion Tokens",
            "Cost",
            "Time (s)",
            "Tool Calls",
            "Steps",
        ],
        rows=rows,
        panel_title="[bold blue]Model Comparison[/bold blue]",
        border_style="blue",
    )


def print_metric_ranking(metric: str, ranked_models: list[dict[str, Any]], *, descending: bool) -> None:
    """Print ranking for a single metric across models."""
    metric_titles = {
        "score": "Score Ranking",
        "completion_tokens": "Completion Tokens Ranking",
        "cost": "Cost Ranking",
        "time": "Time Ranking",
        "tool_calls_num": "Tool Calls Ranking",
        "step_num": "Steps Ranking",
    }
    metric_labels = {
        "score": "Score",
        "completion_tokens": "Completion Tokens",
        "cost": "Cost",
        "time": "Time (s)",
        "tool_calls_num": "Tool Calls",
        "step_num": "Steps",
    }
    formatter = _fmt_pct if metric == "score" else _fmt
    rows = []
    for idx, model_info in enumerate(ranked_models, 1):
        value = model_info["overall_avg"].get(metric)
        rows.append([str(idx), model_info["model"], formatter(value)])

    direction = "high to low" if descending else "low to high"
    ConsoleDisplay.print_table(
        title=metric_titles[metric],
        headers=["Rank", "Model", metric_labels[metric]],
        rows=rows,
        panel_title=f"[bold blue]{metric_titles[metric]} ({direction})[/bold blue]",
        border_style="blue",
    )


def print_model_section_title(model: str, rank: int) -> None:
    """Print section title for a model in comparison view."""
    ConsoleDisplay.console.print(
        f"\n[bold cyan]===== Rank {rank}: {model} =====[/bold cyan]"
    )


def print_single_result(extracted: dict[str, Any]) -> None:
    """Print single run: status, reason, score, completion_tokens, cost, tool_calls_num, step_num."""
    items = [
        ("status", extracted.get("status", "-")),
        ("reason", extracted.get("reason", "-")),
        ("score", extracted.get("score", "-")),
        ("completion_tokens", extracted.get("completion_tokens", "-")),
        ("cost", extracted.get("cost", "-")),
        ("tool_calls_num", extracted.get("tool_calls_num", "-")),
        ("step_num", extracted.get("step_num", "-")),
        ("time (s)", extracted.get("time", "-")),
    ]
    ConsoleDisplay.print_kv_panel(
        title="[bold green]Run Result[/bold green]",
        items=items,
        border_style="green",
    )
