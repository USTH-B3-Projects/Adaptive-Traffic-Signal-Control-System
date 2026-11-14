import json
import argparse
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent

CONTROLLERS = {
    "fixed_time": ROOT / "FixedTime" / "logs",
    "rule_based": ROOT / "RuleBased" / "logs",
}

SCENARIOS = ["low", "medium", "high", "imbalance"]

def load_log(file_path):
    records = []

    with open(file_path, "r", encoding="utf-8") as log_file:
        for line in log_file:
            line = line.strip()
            if not line:
                continue
            load_line = json.loads(line)
            records.append(load_line)

    return records

def normalize_records(records):
    normalized = []

    for record in records:
        time = record["simulation_time"]
        queue_ns = record["queues"]["NS"]
        queue_ew = record["queues"]["EW"]
        total_queue = queue_ew + queue_ns
        total_waiting_time = record["total_waiting_time"]

        normalized.append({
            "time": time,
            "queue_ns": queue_ns,
            "queue_ew": queue_ew,
            "total_queue": total_queue,
            "total_waiting_time": total_waiting_time,
        })
    return normalized

"""# Test func
file_path = ROOT / "FixedTime" / "logs" / args.map_name / "fixed_time_low_seed42.jsonl"

records = load_log(file_path)
normalized = normalize_records(records)

print("no. Records:", len(normalized))
print("Second Record:", normalized[1])
"""

def validate_pair(fixed_records, rule_records):
    if not fixed_records or not rule_records:
        raise ValueError("Empty log")
    
    if len(fixed_records) != len(rule_records):
        raise ValueError("Different no. records")

    for fixed_record, rule_record in zip(fixed_records, rule_records):
        if fixed_record["time"] != rule_record["time"]:
            raise ValueError("Different time")

def calculate_metrics(records):
    queues = []
    waiting_times = []

    for record in records:
        queues.append(record["total_queue"])
        waiting_times.append(record["total_waiting_time"])

    return {
        "mean_queue": mean(queues),
        "max_queue": max(queues),
        "mean_total_waiting_time": mean(waiting_times),
        "max_total_waiting_time": max(waiting_times)
    }

"""
fixed_metrics = calculate_metrics(fixed_records)
rule_metrics = calculate_metrics(rule_records)

print("Fixed-time:", fixed_metrics)
print("Rule-based:", rule_metrics)
"""

def calculate_reduction(baseline_value, candidate_value):
    # baseline_value: fixed_time, or rule_based
    # candidate_value : rule_based, further: DRL
    if baseline_value == 0:
        return None
    return ((baseline_value - candidate_value) * 100) / baseline_value

"""
# Test func
reduction = calculate_reduction(
    fixed_metrics["mean_queue"],
    rule_metrics["mean_queue"]
)
if reduction is None:
    print("Mean queue reduction: N/A")
else:
    print(f"mean queue reduction: {reduction:.2f}%")
"""

def main():
    parser.add_argument(
        "--map",
        dest="map_name",
        choices=["simple_intersection", "o_cho_dua", "bigc_thang_long"],
        default="simple_intersection",
    )

    parser = argparse.ArgumentParser(
        description="Compare fixed-time and rule-based logs."
    )

    parser.add_argument(
        "--seed",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--scenario",
        choices=SCENARIOS,
        default=None,
    )

    args = parser.parse_args()

    selected_scenarios = (
        [args.scenario] if args.scenario is not None else SCENARIOS
    )

    results = []

    for scenario in selected_scenarios:
        print(f"\nScenario: {scenario}")

        fixed_path = (
            CONTROLLERS["fixed_time"] / args.map_name / f"seed{args.seed}" / f"fixed_time_{scenario}_seed{args.seed}.jsonl"
        )
        rule_path = (
            CONTROLLERS["rule_based"] / args.map_name / f"seed{args.seed}" / f"rule_based_{scenario}_seed{args.seed}.jsonl"
        )

        fixed_records = normalize_records(load_log(fixed_path))
        rule_records = normalize_records(load_log(rule_path))

        validate_pair(fixed_records, rule_records)

        fixed_metrics = calculate_metrics(fixed_records)
        rule_metrics = calculate_metrics(rule_records)

        print("Fixed-time: ", fixed_metrics)
        print("Rule-based: ", rule_metrics)

        for metric in fixed_metrics:
            baseline_value = fixed_metrics[metric]
            candidate_value = rule_metrics[metric]

            reduction = calculate_reduction(baseline_value, candidate_value)

            if reduction is None:
                print(f"{metric}: reduction = N/A")
            else:
                print(f"{metric}: reduction = {reduction:.2f}%")

            results.append({
                "map": args.map_name,
                "scenario": scenario,
                "seed": args.seed,
                "metric": metric,
                "baseline": "fixed_time",
                "candidate": "rule_based",
                "baseline_value": baseline_value,
                "candidate_value": candidate_value,
                "reduction_percent": reduction,
            })
        
    print("No. comparision results:", len(results))

    output_dir = ROOT / "results" / args.map_name / f"seed{args.seed}"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.scenario is None:
        output_name = f"baseline_comparison_seed{args.seed}.jsonl"
    else:
        output_name = (
            f"baseline_comparison_{args.scenario}_seed{args.seed}.jsonl"
        )
    output_path = output_dir / output_name

    with open(output_path, "w", encoding="utf-8") as output_file:
        for result in results:
            output_file.write(
                json.dumps(result, ensure_ascii=False) + "\n"
            )

    print(f"Saved {len(results)} results to: {output_path}")

if __name__ == "__main__":
    main()