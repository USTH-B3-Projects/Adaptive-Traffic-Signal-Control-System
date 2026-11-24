"""V2 report generator: aggregate episode totals over matched held-out seeds."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from DRL.artifacts import ROOT, REPORT, output_path, write_csv
from DRL.metrics import SCENARIOS, METRICS, aggregate_episodes, episode_summary

METHODS = ('fixed_time', 'rule_based', 'drl_ppo', 'drl_ppo_final')


def read_metrics(path):
    with Path(path).open(encoding='utf-8', newline='') as stream:
        return [{k: (float(v) if k in (*METRICS, 'simulation_time') else v)
                 for k, v in row.items()} for row in csv.DictReader(stream)]


def load_episodes(evaluation_root, seeds):
    episodes = []
    for method in METHODS[:2]:
        for seed in seeds:
            for scenario in SCENARIOS:
                path = evaluation_root/'baselines'/method/f'seed{seed}'/f'metrics_{scenario}_seed{seed}.csv'
                episodes.append(checked_episode(read_metrics(path), method, scenario, seed))
    for folder, method in (('best', 'drl_ppo'), ('final', 'drl_ppo_final')):
        groups = {}
        for row in read_metrics(evaluation_root/folder/'metrics.csv'):
            groups.setdefault((row['scenario'], int(row['seed'])), []).append(row)
        expected = {(scenario, seed) for scenario in SCENARIOS for seed in seeds}
        if set(groups) != expected:
            raise ValueError(f'Unexpected evaluation seed/scenario coverage: {folder}')
        for scenario, seed in sorted(expected):
            episodes.append(checked_episode(groups[scenario, seed], method, scenario, seed))
    return episodes


def checked_episode(rows, method, scenario, seed):
    if len(rows) != 720 or any(abs(row['simulation_time'] - 5*(i+1)) > 1e-6
                               for i, row in enumerate(rows)):
        raise ValueError(f'Expected 720 post-step samples at 5..3600: {method}/{scenario}/{seed}')
    if any(row['method'] != method or row['scenario'] != scenario or int(row['seed']) != seed for row in rows):
        raise ValueError('Metric identity mismatch')
    # arrived_count is incremental per decision interval: SUM, never mean.
    result = episode_summary(rows)
    result['seed'] = int(result['seed'])
    return result


def comparison_plot(summary, output):
    output = output_path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    lookup = {(r['method'], r['scenario']): r for r in summary}
    fig, axes = plt.subplots(3, 2, figsize=(15, 12), constrained_layout=True)
    positions = np.arange(4)
    labels = ('Fixed-Time', 'Rule-Based', 'PPO best', 'PPO final (secondary)')
    for axis, metric in zip(axes.flat, METRICS):
        for index, (method, label) in enumerate(zip(METHODS, labels)):
            rows = [lookup[method, scenario] for scenario in SCENARIOS]
            axis.bar(positions+(index-1.5)*0.2,
                     [r[metric+'_mean'] for r in rows], 0.2,
                     yerr=[r[metric+'_std'] for r in rows], capsize=2, label=label)
        axis.set_xticks(positions, SCENARIOS)
        axis.set_title(metric)
        axis.grid(axis='y', alpha=0.25)
    axes.flat[-1].axis('off')
    axes.flat[0].legend(fontsize=8)
    fig.savefig(output, dpi=150)
    plt.close(fig)


def build_report(summary, metadata, timings, seeds, dry_run=False):
    lookup = {(r['method'], r['scenario']): r for r in summary}
    def cell(method, scenario, metric):
        row = lookup[method, scenario]
        return f'{row[metric+"_mean"]:.2f} ± {row[metric+"_std"]:.2f}'
    lines = [
        '# DRL Seed100 — V2 experimental report',
        '',
        '**DRY-RUN / PREFLIGHT ONLY — not a 600k experiment.**' if dry_run else
        '**Completed V2 seed100 experiment; results below are measured artifacts.**',
        '',
        '## Configuration and execution',
        '',
        f'- Training seed: 100; requested/actual steps: {metadata["requested_timesteps"]:,} / {metadata["actual_timesteps"]:,}.',
        f'- GPU: {metadata["gpu"]}; fixed validation seed999; held-out evaluation seeds: {list(seeds)}.',
        '- Training seeds sampled only from [1000,999999]; shuffled cycles cover all four scenarios.',
        '- 12D directional observations clipped to [0,1]; MLP actor/critic [128,128].',
        '- Reward = clip(-[Q_NS+Q_EW+0.05(W_NS+W_EW)+0.02(Q_NS-Q_EW)^2]/100,-10,0).',
        '- SUMO step0.1s; decision5s; min/max green15/75s; yellow/all-red3/3s.',
        '- PPO: n_steps2880, batch96, epochs5, gamma0.99, GAE0.95, clip0.2, entropy0.01, vf0.5, grad_norm0.5, target_KL0.02.',
        '- LR linearly decreases 3e-4→1e-5; CUDA; advantage normalization enabled.',
        '- Best model selected ONLY by mean reward on four seed999 validation episodes; held-out seeds never select the model.',
        f'- Timings in seconds: {json.dumps(timings, ensure_ascii=False)}',
        '',
        '## Fair multi-seed traffic results',
        '',
        'Mean ± sample Std (ddof=1) over evaluation seeds; single-seed preflight reports Std=0, not an uncertainty estimate.',
        'Queue/wait/speed/network count: means of 720 post-step snapshots at t=5..3600s.',
        'Arrivals: SUM of incremental arrivals over every 0.1s substep for the full episode.',
        'Speed: vehicle-count-weighted over the same eight incoming lanes for all methods.',
        'Same SUMO seeds and input files are passed directly to all methods; controlled trajectories may differ.',
        '',
        '| Scenario | Metric | Fixed-Time | Rule-Based | PPO best | PPO final (secondary) |',
        '|---|---|---:|---:|---:|---:|',
    ]
    for scenario in SCENARIOS:
        for metric in METRICS:
            lines.append('| '+scenario+' | '+metric+' | '+
                         ' | '.join(cell(m, scenario, metric) for m in METHODS)+' |')
    lines += ['', '![V2 comparison](../seed100/plots/seed100_baseline_comparison.png)',
              '', '## Historical V1 → V2 context', '',
              'Descriptive comparison only: V1 used different timing (min green30s), unmatched traffic seeds,',
              'and faulty arrivals/speed definitions. Do not attribute changes solely to the neural network.',
              '', '| Scenario | V1 PPO107 waiting | V1 PPO710 waiting | V2 PPO best waiting |',
              '|---|---:|---:|---:|']
    historical = {}
    for seed in (107, 710):
        path = ROOT/f'results/seed{seed}/summary_final.csv'
        if path.is_file():
            with path.open(encoding='utf-8') as stream:
                historical[seed] = {r['scenario']: r for r in csv.DictReader(stream) if r['method'] == 'drl_ppo'}
    for scenario in SCENARIOS:
        values = [f'{float(historical[s][scenario]["waiting_time"]):.2f}'
                  if s in historical else 'N/A' for s in (107, 710)]
        lines.append(f'| {scenario} | {values[0]} | {values[1]} | {cell("drl_ppo", scenario, "waiting_time")} |')
    lines += ['', '## Interpretation and limitations', '',
              'Waiting is the time-mean of the sum of current lane waiting times, not mean trip delay.',
              'Evaluation stops at3600s; remaining vehicles are reported; completed-trip delay is not inferred.',
              'Collision warnings are retained in subprocess.log; low queue/wait does not establish collision-free operation.',
              'Normalization clips queue>60, vehicles>80 and waiting>1500 per axis; saturation and imbalance penalty can trade throughput against balance.',
              'Only three held-out seeds support this comparison; no guarantee of superiority or convergence is implied.',
              'V1 models, evaluations, results, event logs and existing comparison Markdown files were preserved.',
              '', 'Sources: per-step metrics.csv, per-episode episodes.csv, summary_final.csv, pipeline_timings.json,',
              'training_metadata.json and the preserved V1 seed107/seed710 summaries.']
    return '\n'.join(lines)+'\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evaluation-root', type=Path, default=ROOT/'evaluation/seed100')
    parser.add_argument('--result-dir', type=Path, default=ROOT/'results/seed100')
    parser.add_argument('--model-root', type=Path, default=ROOT/'models/seed100')
    parser.add_argument('--output', type=Path, default=REPORT)
    parser.add_argument('--seeds', type=int, nargs='+', default=[101, 102, 103])
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    result_dir = output_path(args.result_dir)
    output = output_path(args.output)
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite report: {output}')
    episodes = load_episodes(args.evaluation_root, args.seeds)
    summary = aggregate_episodes(episodes)
    write_csv(result_dir/'episodes.csv', episodes)
    write_csv(result_dir/'summary_final.csv', summary)
    plot = result_dir/'plots/seed100_baseline_comparison.png'
    comparison_plot(summary, plot)
    metadata = json.loads((args.model_root/'training_metadata.json').read_text())
    timings = json.loads((result_dir/'pipeline_timings.json').read_text())
    output.parent.mkdir(parents=True, exist_ok=True)
    # Use a relative plot link for dry-run paths as well.
    import os
    report = build_report(summary, metadata, timings, args.seeds, args.dry_run)
    report = report.replace('../seed100/plots/seed100_baseline_comparison.png',
                            Path(os.path.relpath(plot, output.parent)).as_posix())
    with output.open('x', encoding='utf-8') as stream:
        stream.write(report)
    print(f'Generated V2 summary, plot, report: {output}', flush=True)


if __name__ == '__main__':
    main()
