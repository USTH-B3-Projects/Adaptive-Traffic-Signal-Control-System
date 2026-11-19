import json
import argparse
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent

CONTROLLERS = {
    "fixed_time": ROOT / "FixedTime" / "logs_ochodua",
    "rule_based": ROOT / "RuleBased" / "logs_ochodua",
}

SCENARIOS = ["ocd_low", "ocd_medium", "ocd_high", "ocd_imbalance"]


def load_log(path: Path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def total_queue(record) -> float:
    if record.get("queues_total") is not None:
        return float(record["queues_total"])
    q = record.get("queues") or {}
    if "total" in q:
        return float(q["total"])
    if any(str(k).startswith("S") for k in q):
        return float(sum(q.values()))
    if "NS" in q and "EW" in q:
        return float(q["NS"] + q["EW"])
    raise KeyError(f"No queue field in record: {list(record.keys())}")


def normalize(records):
    out = []
    for r in records:
        tw = r.get("total_waiting_time")
        if tw is None:
            continue
        out.append({
            "time": r["simulation_time"],
            "total_queue": total_queue(r),
            "total_waiting_time": float(tw),
        })
    return out


def metrics(records):
    qs = [r["total_queue"] for r in records]
    ws = [r["total_waiting_time"] for r in records]
    return {
        "mean_queue": mean(qs),
        "max_queue": max(qs),
        "mean_total_waiting_time": mean(ws),
        "max_total_waiting_time": max(ws),
    }


def reduction(base, cand):
    if base == 0:
        return None
    return (base - cand) / base * 100.0


def compare_one(scenario: str, seed: int):
    fixed_path = (
        CONTROLLERS["fixed_time"]
        / f"seed{seed}"
        / f"fixed_time_{scenario}_seed{seed}.jsonl"
    )
    rule_path = (
        CONTROLLERS["rule_based"]
        / f"seed{seed}"
        / f"rule_based_{scenario}_seed{seed}.jsonl"
    )
    if not fixed_path.is_file():
        raise FileNotFoundError(fixed_path)
    if not rule_path.is_file():
        raise FileNotFoundError(rule_path)

    fixed = normalize(load_log(fixed_path))
    rule = normalize(load_log(rule_path))
    if not fixed or not rule:
        raise ValueError(f"Empty log after normalize: {scenario} seed{seed}")

    fm, rm = metrics(fixed), metrics(rule)
    print(f"\n=== {scenario} | seed {seed} ===")
    print(f"  records fixed={len(fixed)} rule={len(rule)}")
    print(f"  Fixed-time: {fm}")
    print(f"  Rule-based: {rm}")

    rows = []
    for m in fm:
        red = reduction(fm[m], rm[m])
        print(f"  {m}: reduction = {red:.2f}%" if red is not None else f"  {m}: N/A")
        rows.append({
            "scenario": scenario,
            "seed": seed,
            "metric": m,
            "baseline": "fixed_time",
            "candidate": "rule_based",
            "baseline_value": fm[m],
            "candidate_value": rm[m],
            "reduction_percent": red,
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description="Compare FT vs RB on O Cho Dua")
    parser.add_argument("--scenario", choices=SCENARIOS, default=None)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    scenarios = [args.scenario] if args.scenario else SCENARIOS
    results = []
    for sc in scenarios:
        results.extend(compare_one(sc, args.seed))

    out_dir = ROOT / "results" / "o_cho_dua" / f"seed{args.seed}"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.scenario:
        out_name = f"baseline_comparison_{args.scenario}_seed{args.seed}.jsonl"
    else:
        out_name = f"baseline_comparison_seed{args.seed}.jsonl"
    out_path = out_dir / out_name

    with open(out_path, "w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    if args.scenario is None:
        by_sc = {}
        for row in results:
            by_sc.setdefault(row["scenario"], []).append(row)
        for sc, rows in by_sc.items():
            p = out_dir / f"baseline_comparison_{sc}_seed{args.seed}.jsonl"
            with open(p, "w", encoding="utf-8") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\nSaved -> {out_path}")


if __name__ == "__main__":
    main()