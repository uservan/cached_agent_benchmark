import json
import random
from typing import Any, Callable

from .agent import Agent
from .task import Task, RunResult


class CacheEnv:
    """CacheEnv 负责遍历 dataset、调用 agent，并基于 task 做评估。"""

    def __init__(
        self,
        dataset_objects: list,
        max_steps: int = 1000,
        tool_failure_rates: list[float] | None = None,
        num_trials: int = 1,
        tools_domain_only: bool = True,
        seed: int = 42,
        hidden_rates: list[float] | None = None,
    ):
        self.dataset_objects = dataset_objects
        self.max_steps = max_steps
        self.tool_failure_rates = tool_failure_rates or [0.0]
        self.num_trials = num_trials
        self.tools_domain_only = tools_domain_only
        self.hidden_rates = hidden_rates or [0.1, 0.3, 0.5, 0.7, 0.9]
        random.seed(seed)
        self.seeds = [random.randint(0, 1000000) for _ in range(num_trials)]

    def get_total_runs(self) -> int:
        return (
            len(self.dataset_objects)
            * len(self.hidden_rates)
            * len(self.tool_failure_rates)
            * len(self.seeds)
        )

    def run_task(self, task: Task, agent: Agent) -> RunResult:
        """
        执行单个 task，拿到 messages，用 task.eval 打分，并把分数追加到 messages。
        """
        run_result: RunResult = agent.generate(task)
        score = task.eval()
        run_result.set_score(score)

        return run_result

    def run(
        self,
        agent: Agent,
        save_path: str,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ):
        """
        遍历 dataset_objects，执行全部 task，汇总结果并保存到 JSON 文件。
        """
        total_runs = self.get_total_runs()
        run_index = 0
        for dataset_obj in self.dataset_objects:
            for hidden_rate in self.hidden_rates:
                for tool_failure_rate in self.tool_failure_rates:
                    for trial_index, seed in enumerate(self.seeds, start=1):
                        run_index += 1
                        task = Task(
                            dataset_object=dataset_obj,
                            hidden_rate=hidden_rate,
                            max_steps=self.max_steps,
                            tool_failure_rate=tool_failure_rate,
                            tools_domain_only=self.tools_domain_only,
                            seed=seed,
                        )
                        if progress_callback is not None:
                            progress_callback(
                                {
                                    "stage": "start",
                                    "run_index": run_index,
                                    "total_runs": total_runs,
                                    "domain": dataset_obj.domain,
                                    "instance_id": getattr(dataset_obj, "instance_id", ""),
                                    "hidden_rate": hidden_rate,
                                    "tool_failure_rate": tool_failure_rate,
                                    "trial_index": trial_index,
                                    "num_trials": self.num_trials,
                                    "seed": seed,
                                    "save_path": save_path,
                                }
                            )
                        run_result = self.run_task(task, agent)
                        if progress_callback is not None:
                            progress_callback(
                                {
                                    "stage": "finish",
                                    "run_index": run_index,
                                    "total_runs": total_runs,
                                    "domain": dataset_obj.domain,
                                    "instance_id": getattr(dataset_obj, "instance_id", ""),
                                    "hidden_rate": hidden_rate,
                                    "tool_failure_rate": tool_failure_rate,
                                    "trial_index": trial_index,
                                    "num_trials": self.num_trials,
                                    "seed": seed,
                                    "status": run_result.status,
                                    "score": run_result.score,
                                    "save_path": save_path,
                                }
                            )

    def _extract_numeric_score(self, score: Any) -> float | None:
        if isinstance(score, (int, float)):
            return float(score)
        if isinstance(score, dict):
            for key in ("score", "final_score", "value"):
                value = score.get(key)
                if isinstance(value, (int, float)):
                    return float(value)
        return None
