import argparse
import json
import random

from agent.agent import Agent
from agent.cache_env import CacheEnv
from load_datasets.loader import DEFAULT_DATA_DIR, load_all_dataset_objects


HIDDEN_RATE_CHOICES = [0.1, 0.3, 0.5, 0.7, 0.9]
DOMAIN_CHOICES = ["course", "shopping", "travel", "workforce", "meal", "pc_build"]
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_SEED = 42
DEFAULT_AGENT_PARAMS = "{}"
DEFAULT_MAX_STEPS = 1000
DEFAULT_TOOL_FAILURE_RATES = "[0.0]"
DEFAULT_NUM_TRIALS = 1
DEFAULT_TOOLS_DOMAIN_ONLY = True
DEFAULT_SAVE_PATH = "output.json"
DEFAULT_DOMAIN = ["all"]
DEFAULT_DOMAIN_FALLBACK = ["course"]


def parse_list_arg(value, item_type):
    if value is None:
        return None

    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [item_type(item) for item in parsed]
    except json.JSONDecodeError:
        pass

    return [item_type(item.strip()) for item in value.split(",") if item.strip()]


def set_seed(seed: int) -> None:
    """设置随机种子，保证可复现性。"""
    random.seed(seed)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL, help="模型名称")
    parser.add_argument(
        "--agent-params",
        default=DEFAULT_AGENT_PARAMS,
        help="Agent 额外参数, JSON 字符串",
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help="数据集文件夹路径",
    )
    parser.add_argument(
        "--domain",
        nargs="+",
        choices=DOMAIN_CHOICES + ["all"],
        default=DEFAULT_DOMAIN,
        help=f"领域列表，可多选: {', '.join(DOMAIN_CHOICES)}，或 all 表示全部领域",
    )
    parser.add_argument(
        "--hidden-rates",
        nargs="+",
        type=float,
        choices=HIDDEN_RATE_CHOICES,
        default=HIDDEN_RATE_CHOICES,
        help=f"隐藏率列表，可选: {HIDDEN_RATE_CHOICES}",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=DEFAULT_MAX_STEPS,
        help="单个 task 最大步数",
    )
    parser.add_argument(
        "--tool-failure-rates",
        default=DEFAULT_TOOL_FAILURE_RATES,
        help="tool 调用失败率列表，支持 JSON 或逗号分隔，如 [0,0.1,0.5]",
    )
    parser.add_argument(
        "--num-trials",
        dest="num_trials",
        type=int,
        default=DEFAULT_NUM_TRIALS,
        help="每个 task 的重复运行次数",
    )
    parser.add_argument(
        "--tools-all-domains",
        dest="tools_domain_only",
        action="store_false",
        default=DEFAULT_TOOLS_DOMAIN_ONLY,
        help="tool 展示全部 domain；不指定时仅展示当前 domain",
    )
    parser.add_argument(
        "--save-path",
        default=DEFAULT_SAVE_PATH,
        help="结果 JSON 输出路径",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="随机种子",
    )
    return parser.parse_args()


def main(
    model,
    domain,
    data_dir=None,
    agent_params=None,
    hidden_rates=None,
    max_steps=DEFAULT_MAX_STEPS,
    tool_failure_rates=None,
    num_trials=DEFAULT_NUM_TRIALS,
    tools_domain_only=DEFAULT_TOOLS_DOMAIN_ONLY,
    save_path=DEFAULT_SAVE_PATH,
    seed=DEFAULT_SEED,
):
    """
    组装 dataset、agent、cache env，并执行完整流程。
    """
    set_seed(seed)
    data_dir = data_dir or DEFAULT_DATA_DIR
    all_objects = load_all_dataset_objects(data_dir=data_dir)
    dataset_objects = [obj for obj in all_objects if obj.domain in domain]

    cache_env = CacheEnv(
        dataset_objects=dataset_objects,
        max_steps=max_steps,
        tool_failure_rates=tool_failure_rates or [0.0],
        num_trials=num_trials,
        tools_domain_only=tools_domain_only,
        seed=seed,
        hidden_rates=hidden_rates,
    )
    agent = Agent(model=model, **(agent_params or {}))

    return cache_env.run(agent=agent, save_path=save_path)

if __name__ == "__main__":
    args = parse_args()
    domain = DOMAIN_CHOICES if "all" in args.domain else (args.domain or DEFAULT_DOMAIN_FALLBACK)
    main(
        model=args.model,
        save_path=args.save_path,
        domain=domain,
        agent_params=json.loads(args.agent_params),
        hidden_rates=args.hidden_rates,
        max_steps=args.max_steps,
        tool_failure_rates=parse_list_arg(args.tool_failure_rates, float),
        num_trials=args.num_trials,
        tools_domain_only=args.tools_domain_only,
        data_dir=args.data_dir,
        seed=args.seed,
    )
