# debug.py - test the main entry point of cached_agent_benchmark

import os
import sys

os.environ["OPENAI_API_KEY"] = "EMPTY"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import main
from config import MODELS

if __name__ == "__main__":
    # sh command: 
    #   nohup python run/debug.py > run/debug_log/qwen35_9b.log 2>&1 &
    #   disown 
    cfg = MODELS["qwen35_9b"]
    main(
        model=cfg["model"],
        agent_params=cfg["agent_params"],
        domain=["course"], # "all",
        data_dir="data/5x7",
        max_steps=2000,
        tool_failure_rates=[0.0], # [0.0,0.1,0.3],
        save_path="cached_results/",
        max_workers=64,
        num_trials=1,
        max_query_ids=5,
        max_query_fields=5,
        tools_domain_only=True,
        overwrite_results=False,
        check_include_reason=False,
        global_check_alpha=-1,
        extra_query_num=-1,
        seed=42,
        hidden_slots=None,
        branch_budget=None,
        max_length_truncations=3,
    )
