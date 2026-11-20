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
    if not records:
        raise ValueError("Empty log")

    normalized = []

    for record in records:
        if "total_queue" in record:
            total_queue = record["total_queue"]
        else:
            total_queue = (
                record["queues"]["NS"] + record["queues"]["EW"]
            )

        normalized.append({
            "time": record["simulation_time"],
            "total_queue": total_queue,
            "total_waiting_time": record["total_waiting_time"],
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
    parser = argparse.ArgumentParser(
        description="Summarize FT or compare FT and RB logs."
    )

    parser.add_argument(
        "--map",
        dest="map_name",
        choices=[
            "simple_intersection",
            "o_cho_dua",
            "bigc_thang_long",
        ],
        default="simple_intersection",
    )

    parser.add_argument("--seed", type=int, required=True)

    parser.add_argument(
        "--scenario",
        choices=SCENARIOS,
        default=None,
    )

    summary_group = parser.add_mutually_exclusive_group()

    summary_group.add_argument(
        "--ft-only",
        action="store_true",
        help="Summarize fixed-time logs only.",
    )

    summary_group.add_argument(
        "--rb-only",
        action="store_true",
        help="Summarize rule-based logs only.",
    )

    args = parser.parse_args()

    available_scenarios = SCENARIOS

    if (
        args.scenario is not None
        and args.scenario not in available_scenarios
    ):
        parser.error(
            f"{args.map_name} supports: {available_scenarios}"
        )

    selected_scenarios = (
        [args.scenario]
        if args.scenario is not None
        else available_scenarios
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

        if args.ft_only or args.rb_only:
            controller = (
                "fixed_time" if args.ft_only else "rule_based"
            )
            log_path = fixed_path if args.ft_only else rule_path

            records = normalize_records(load_log(log_path))
            metrics = calculate_metrics(records)

            print(f"{controller}:", metrics)

            for metric, value in metrics.items():
                results.append({
                    "map": args.map_name,
                    "scenario": scenario,
                    "seed": args.seed,
                    "controller": controller,
                    "metric": metric,
                    "value": value,
                    "sample_count": len(records),
                    "first_sample_time": records[0]["time"],
                    "last_sample_time": records[-1]["time"],
                })

            continue

        fixed_records = normalize_records(load_log(fixed_path))
        fixed_metrics = calculate_metrics(fixed_records)

        rule_records = normalize_records(load_log(rule_path))

        validate_pair(fixed_records, rule_records)

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

    if args.ft_only:
        prefix = "fixed_time_summary"
    elif args.rb_only:
        prefix = "rule_based_summary"
    else:
        prefix = "baseline_comparison"

    if args.scenario is None:
        output_name = f"{prefix}_seed{args.seed}.jsonl"
    else:
        output_name = (
            f"{prefix}_{args.scenario}_seed{args.seed}.jsonl"
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