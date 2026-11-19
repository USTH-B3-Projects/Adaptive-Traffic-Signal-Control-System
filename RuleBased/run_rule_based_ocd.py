from pathlib import Path
import sys
import json
import argparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "TraCI"))

from RuleBased.rule_based_controller_ocd import (
    choose_action,
    get_stage_queues,
    get_current_stage,
    get_total_queue,
    MAIN_TLS,
)
from core.environment import Environment

parser = argparse.ArgumentParser(description="Rule-based baseline on O Cho Dua")
parser.add_argument("--scenario", choices=["ocd_low","ocd_medium","ocd_high", "ocd_imbalance"], required=True)
parser.add_argument("--seed", type=int, required=True)
args = parser.parse_args()

END_TIME = {
    "ocd_low": 3600,
    "ocd_medium": 3600,
    "ocd_high": 3600,
    "ocd_imbalance": 10800,   
}
#TEST_DURATION = 300
max_seconds = END_TIME[args.scenario]
#max_seconds = TEST_DURATION

log_dir = ROOT / "RuleBased" / "logs_ochodua" / f"seed{args.seed}"
log_dir.mkdir(parents=True, exist_ok=True)

log_path = log_dir / f"rule_based_{args.scenario}_seed{args.seed}.jsonl"
print(f"Running rule-based O Cho Dua: scenario={args.scenario}, seed={args.seed}")
print(f"Log: {log_path}")

with Environment(
    settings={
        "gui": False,
        "max_episode_seconds": max_seconds,
        "simulation_step": 0.1,

    }
) as env:

    state = env.reset(args.scenario, seed=args.seed)
    if MAIN_TLS in state["tls"]:
        tls_id = MAIN_TLS
    else:
        tls_id = next(iter(state["tls"].keys()))
    print(f"Controlling TLS: {tls_id}")
        
    with open(log_path, "w", encoding="utf-8") as log_file:
        step = 0
        while True:
            action = choose_action(state)

            tls = state["tls"][tls_id]
            stage_queues = get_stage_queues(state)
            record = {
                "scenario": state["scenario"],
                "seed": args.seed,
                "controller": "rule_based",
                "simulation_time": state["simulation_time"],
                "tls_id": tls_id,
                "phase_id": tls["phase_id"],
                "stage": get_current_stage(state),
                "green_elapsed": tls.get("green_elapsed"),
                "queues": stage_queues,
                "queues_total": get_total_queue(state),
                "total_waiting_time": tls["totals"].get("waiting_time"),
                "chosen_action": action,
            }

            state, terminated, truncated, info = env.step(action)

            record["executed_action"] = info.get("executed_action", {}).get(tls_id)
            record["override_reason"] = info.get("override_reason", {}).get(tls_id)
            record["next_time"] = state["simulation_time"]

            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")

            step += 1
            if step % 12 == 0:  # ~ mỗi 60s (decision_interval=5)
                print(f"Progress: {state['simulation_time']:.0f}/{max_seconds} s")

            if terminated or truncated:
                print(f"Ended at {state['simulation_time']:.1f}s — {info.get('end_reason')}")
                break

print("Done.")