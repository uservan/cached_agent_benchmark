import importlib
import json
import pkgutil
import random
from typing import Any

DATASET_REGISTRY = {}

def register_dataset(name):
    def decorator(dataset_cls):
        DATASET_REGISTRY[name.lower()] = dataset_cls
        return dataset_cls

    return decorator

def get_dataset_class(name):
    return DATASET_REGISTRY[name.lower()]


def list_registered_datasets():
    return sorted(DATASET_REGISTRY.keys())


def build_dataset(dataset, dataset_kwargs=None):
    dataset_kwargs = dataset_kwargs or {}

    if isinstance(dataset, str):
        dataset_cls = get_dataset_class(dataset)
        return dataset_cls(**dataset_kwargs)

    if isinstance(dataset, type):
        return dataset(**dataset_kwargs)

    return dataset

class BaseDataset:
    def __init__(self, name):
        self.name = name

    def load_data(self):
        # 加载数据的逻辑
        pass

    def _build_combined_tasks(self, tasks, together_task_size):
        if together_task_size <= 1:
            return [MergedTask([task]) for task in tasks]

        combined_tasks = []
        for index, task in enumerate(tasks):
            other_tasks = tasks[:index] + tasks[index + 1:]
            sample_size = min(max(together_task_size - 1, 0), len(other_tasks))
            sampled_tasks = random.sample(other_tasks, sample_size) if sample_size else []
            combined_tasks.append(MergedTask([task] + sampled_tasks))
        return combined_tasks

class BaseTask:
    def __init__(self, task_name, initial_state, tools):
        self.task_name = task_name
        self.initial_state = initial_state
        self.tools = tools

    def call_tool(self, tool_name, tool_args, tool_failure_rate=0.0):
        # 具体的工具调用逻辑
        pass

    def eval(self, messages):
        # 评估消息的好坏
        pass

    def get_tool_schemas(self):
        # 返回工具的 schema 定义
        pass

    def get_user_prompt(self):
        # 返回用户提示
        pass

    def build_system_prompt(self):
        # 返回系统提示
        pass

class MergedTask(BaseTask):
    def __init__(self, sub_tasks):
        self.sub_tasks = sub_tasks
        self.main_task = sub_tasks[0]

    def call_tool(self, tool_name, tool_args, tool_failure_rate=0.0):
        for task in self.sub_tasks:
            if task.has_tool(tool_name):
                return task.call_tool(tool_name, tool_args, tool_failure_rate=tool_failure_rate)
        return {
            "status": "failed",
            "error": f"Unknown tool: {tool_name}",
        }  

    def get_user_prompt(self):
        pass

    def build_system_prompt(self):
        # 返回系统提示
        pass

    def get_tool_schemas(self):
        pass

    def eval(self, messages):   
        pass

    def build_initial_messages(self):
        pass

    def __len__(self):
        return len(self.sub_tasks)

class RunnableTask:
    """对原始 task 做一层包装，兼容 dict task 和对象 task。"""

    def __init__(self, raw_task):
        self.raw_task = raw_task
        self.dataset = self._get("dataset")
        self.domain = self._get("domain", "")
        self.task_name = self._get("task_name", self._get("task", ""))
        self.initial_state = self._get("initial_state", {})
        self.tools = self._get("tools", []) or []
        self.system_prompt = self._get("system_prompt", "")
        self.tool_responses = self._get("tool_responses", {}) or {}
        self.success_condition = self._get("success_condition")
        self.tool_failure_responses = self._get("tool_failure_responses", {}) or {}
        self.tool_failure_response = self._get("tool_failure_response")

    def build_messages(self):
        if hasattr(self.raw_task, "build_messages"):
            return self.raw_task.build_messages()

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        user_content = self.initial_state
        if not isinstance(user_content, str):
            user_content = json.dumps(user_content, ensure_ascii=False)
        messages.append({"role": "user", "content": user_content})
        return messages

    def call_tool(self, tool_name, tool_args, tool_failure_rate=0.0):
        if tool_failure_rate and random.random() < tool_failure_rate:
            return self._get_tool_failure_response(tool_name, tool_args)

        if hasattr(self.raw_task, "call_tool"):
            try:
                return self.raw_task.call_tool(
                    tool_name,
                    tool_args,
                    tool_failure_rate=tool_failure_rate,
                )
            except TypeError:
                try:
                    return self.raw_task.call_tool(tool_name, tool_args, tool_failure_rate)
                except TypeError:
                    return self.raw_task.call_tool(tool_name, tool_args)

        return self.tool_responses.get(
            tool_name,
            {
                "status": "failed",
                "error": f"Unknown tool: {tool_name}",
            },
        )

    def eval(self, messages):
        if hasattr(self.raw_task, "eval"):
            return self.raw_task.eval(messages)
        return self._eval_with_success_condition(messages)

    def has_tool(self, tool_name):
        for tool in self.tools:
            if self._get_tool_name(tool) == tool_name:
                return True
        return False

    def _get_tool_failure_response(self, tool_name, tool_args):
        if tool_name in self.tool_failure_responses:
            return self.tool_failure_responses[tool_name]
        if self.tool_failure_response is not None:
            return self.tool_failure_response
        return {
            "status": "failed",
            "tool_name": tool_name,
            "tool_args": tool_args,
        }

    def _eval_with_success_condition(self, messages):
        if self.success_condition is None:
            return {}

        assistant_text = "\n".join(
            message.get("content", "")
            for message in messages
            if message.get("role") == "assistant" and isinstance(message.get("content"), str)
        )

        if isinstance(self.success_condition, str):
            return {"score": float(self.success_condition in assistant_text)}

        if isinstance(self.success_condition, list):
            matched = all(
                isinstance(item, str) and item in assistant_text
                for item in self.success_condition
            )
            return {"score": float(matched)}

        if isinstance(self.success_condition, dict):
            matched = []
            for value in self.success_condition.values():
                if isinstance(value, str):
                    matched.append(value in assistant_text)
                elif isinstance(value, list):
                    matched.append(
                        all(isinstance(item, str) and item in assistant_text for item in value)
                    )
            if matched:
                return {"score": sum(matched) / len(matched)}

        return {}

    def _get(self, key, default=None):
        if isinstance(self.raw_task, dict):
            return self.raw_task.get(key, default)
        return getattr(self.raw_task, key, default)

    def _get_tool_name(self, tool):
        if isinstance(tool, dict):
            if "function" in tool:
                return tool["function"].get("name")
            return tool.get("name")
        return getattr(tool, "name", None)


class CombinedTask:
    """将多个 task 融合为一个可执行 task。"""

    def __init__(self, tasks):
        self.tasks = tasks
        self.dataset = tasks[0].dataset if tasks else None
        self.domain = " + ".join(task.domain for task in tasks if task.domain)
        self.task_name = " + ".join(task.task_name for task in tasks if task.task_name)
        self.initial_state = {"tasks": [task.initial_state for task in tasks]}
        self.tools = self._merge_tools(tasks)

    def build_messages(self):
        system_prompts = [task.system_prompt for task in self.tasks if task.system_prompt]
        messages = []
        if system_prompts:
            messages.append({"role": "system", "content": "\n\n".join(system_prompts)})

        user_content = {
            "tasks": [
                {
                    "task_name": task.task_name,
                    "initial_state": task.initial_state,
                }
                for task in self.tasks
            ]
        }
        messages.append(
            {
                "role": "user",
                "content": json.dumps(user_content, ensure_ascii=False),
            }
        )
        return messages

    def call_tool(self, tool_name, tool_args, tool_failure_rate=0.0):
        for task in self.tasks:
            if task.has_tool(tool_name):
                return task.call_tool(
                    tool_name,
                    tool_args,
                    tool_failure_rate=tool_failure_rate,
                )
        return {
            "status": "failed",
            "error": f"Unknown tool: {tool_name}",
        }

    def eval(self, messages):
        sub_scores = [task.eval(messages) for task in self.tasks]
        numeric_scores = [
            self._extract_numeric_score(score)
            for score in sub_scores
        ]
        numeric_scores = [score for score in numeric_scores if score is not None]

        result = {
            "sub_scores": sub_scores,
            "task_count": len(self.tasks),
        }
        if numeric_scores:
            result["score"] = sum(numeric_scores) / len(numeric_scores)
        return result

    def _merge_tools(self, tasks):
        merged_tools = []
        seen_names = set()
        for task in tasks:
            for tool in task.tools:
                tool_name = self._get_tool_name(tool)
                if tool_name and tool_name not in seen_names:
                    merged_tools.append(tool)
                    seen_names.add(tool_name)
        return merged_tools

    def _get_tool_name(self, tool):
        if isinstance(tool, dict):
            if "function" in tool:
                return tool["function"].get("name")
            return tool.get("name")
        return getattr(tool, "name", None)

    def _extract_numeric_score(self, score: Any):
        if isinstance(score, (int, float)):
            return float(score)
        if isinstance(score, dict):
            for key in ("score", "final_score", "value"):
                value = score.get(key)
                if isinstance(value, (int, float)):
                    return float(value)
        return None


def _auto_import_dataset_modules():
    for _, module_name, _ in pkgutil.walk_packages(__path__, prefix=f"{__name__}."):
        if module_name.endswith("_task"):
            importlib.import_module(module_name)


_auto_import_dataset_modules()
