"""Isolated V2 overnight pipeline; --dry-run exercises every stage at 5760 steps."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from DRL.artifacts import ROOT, REPORT, OUTPUT_ROOTS, output_path
from DRL.metrics import SCENARIOS, HELD_OUT_SEEDS


def historical_manifest():
    files = [p for root in ('models', 'evaluation', 'results', 'runs')
             for p in (ROOT/root).rglob('*') if p.is_file()
             and not any(base == p or base in p.parents for base in OUTPUT_ROOTS)
             and p != REPORT]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)}


def sumo_pids():
    if os.name != 'nt':
        return set()
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq sumo.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True, check=True)
    return {int(row[1]) for row in csv.reader(result.stdout.splitlines())
            if row and row[0].lower() == 'sumo.exe'}


def run(command, log_path, timings, name):
    started = time.perf_counter()
    logging.info('START %s: %s', name, subprocess.list2cmdline(command))
    process = None
    try:
        with log_path.open('a', encoding='utf-8') as stream:
            stream.write('\nSTAGE ' + name + '\n')
            stream.flush()
            process = subprocess.Popen(command, cwd=ROOT,
                                       env=dict(os.environ, PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1', MPLBACKEND='Agg'),
                                       stdout=stream, stderr=subprocess.STDOUT)
            while True:
                try:
                    code = process.wait(timeout=30)
                    break
                except subprocess.TimeoutExpired:
                    logging.info('RUNNING %s (%.0fs); details: %s', name, time.perf_counter()-started, log_path)
        if code:
            raise RuntimeError(f'{name} failed with exit {code}; see {log_path}')
    finally:
        if process is not None and process.poll() is None:
            # Only this child and its descendants; never kill all system SUMO processes.
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
            else:
                process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        timings[name] = time.perf_counter()-started
    logging.info('DONE %s in %.2fs', name, timings[name])


def verify_dry_run(model_root, evaluation_root, result_root, run_root):
    import numpy as np
    metadata = json.loads((model_root/'training_metadata.json').read_text())
    if metadata['actual_timesteps'] != 5760:
        raise AssertionError('Dry-run did not complete two full rollouts')
    episodes = [json.loads(line) for line in (run_root/'training_episodes.jsonl').read_text().splitlines()]
    for start in (0, 4):
        if {row['scenario'] for row in episodes[start:start+4]} != set(SCENARIOS):
            raise AssertionError('Training shuffled-cycle coverage failed')
    if not all(1000 <= row['sumo_seed'] <= 999999 for row in episodes):
        raise AssertionError('Training/held-out seed separation failed')
    validation = np.load(evaluation_root/'validation/evaluations.npz')
    if validation['timesteps'].tolist() != [5760] or validation['results'].shape != (1, 4):
        raise AssertionError('EvalCallback was not exercised over four scenarios')
    if not np.all(validation['ep_lengths'] == 720):
        raise AssertionError('Validation episodes do not have full 720 decisions')
    with (evaluation_root/'validation/episodes.monitor.csv').open(encoding='utf-8') as stream:
        next(stream)
        validation_rows = list(csv.DictReader(stream))
    if len(validation_rows) != 4 or any(row['sumo_seed'] != '999' for row in validation_rows):
        raise AssertionError('Validation seed isolation failed')
    for start in (0,):
        if [row['scenario'] for row in validation_rows[start:start+4]] != list(SCENARIOS):
            raise AssertionError('Validation scenario order failed')
    for path in (model_root/'best_model/best_model.zip', model_root/'ppo_seed100_final.zip',
                 result_root/'summary_final.csv', result_root/'plots/seed100_baseline_comparison.png'):
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f'Missing artifact: {path}')
    with (result_root/'summary_final.csv').open() as stream:
        summary = list(csv.DictReader(stream))
    if len(summary) != 16 or any(row['n_seeds'] != '1' for row in summary):
        raise AssertionError('Dry-run aggregate coverage failed')
    return dict(actual_timesteps=5760, rollouts=2, completed_training_episodes=8,
                validation_evaluations=1, validation_episodes=4,
                held_out_seeds=[101], evaluation_scenarios=4, summary_rows=len(summary),
                checkpoint_callback=True, eval_callback=True, csv_plot_report=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='5760-step GPU run; isolated temporary artifacts are removed only after successful checks')
    parser.add_argument('--reuse-baselines', type=Path,
                        help='Dry-run recovery only: reuse already verified seed101 baseline CSVs')
    args = parser.parse_args()
    if args.reuse_baselines and not args.dry_run:
        parser.error('--reuse-baselines is only allowed for preflight; production always runs all baselines')
    if args.reuse_baselines:
        args.reuse_baselines = output_path(args.reuse_baselines)
    from DRL.train_multiscenario import require_cuda
    gpu = require_cuda()
    results_base = output_path(ROOT/'results/seed100')
    results_base.mkdir(parents=True, exist_ok=True)
    old_hashes = historical_manifest()
    before_pids = sumo_pids()
    temporary = None
    if args.dry_run:
        temporary = Path(tempfile.mkdtemp(prefix='_dry_run_', dir=results_base)).resolve()
        model_root, evaluation_root, result_root, run_root = (temporary/p for p in ('models', 'evaluation', 'results', 'runs'))
        report_path = result_root/'drl_seed100_v2_report.md'
        seeds, timesteps, callback_freq = [101], 5760, 2880
    else:
        model_root, evaluation_root = ROOT/'models/seed100', ROOT/'evaluation/seed100'
        result_root, run_root, report_path = results_base, ROOT/'runs/ppo_seed100', REPORT
        seeds, timesteps, callback_freq = list(HELD_OUT_SEEDS), 600000, 28800
    for directory in (model_root, evaluation_root, run_root):
        output_path(directory)
        if directory.exists() and any(directory.iterdir()):
            raise FileExistsError(f'Refusing to reuse existing V2 run: {directory}')
    result_root.mkdir(parents=True, exist_ok=True)
    if report_path.exists() or (result_root/'pipeline.log').exists():
        raise FileExistsError('Existing V2 report/log: choose a fresh run; no artifacts were overwritten')
    handler = logging.FileHandler(result_root/'pipeline.log', mode='x', encoding='utf-8')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[handler, logging.StreamHandler(sys.stdout)], force=True)
    sublog = result_root/'subprocess.log'
    with sublog.open('x', encoding='utf-8'):
        pass
    (result_root/'v1_preservation.json').write_text(json.dumps(old_hashes, indent=2), encoding='utf-8')
    versions = {p: importlib.metadata.version(p) for p in
                ('torch', 'stable-baselines3', 'gymnasium', 'numpy', 'PyYAML', 'tensorboard', 'matplotlib')}
    from DRL.core.scenario_loader import load_settings
    (result_root/'run_config.json').write_text(json.dumps(dict(version='V2', seed=100,
        timesteps=timesteps, evaluation_seeds=seeds, validation_seed=999,
        settings=load_settings(), versions=versions, gpu=gpu,
        reused_baselines_from=str(args.reuse_baselines) if args.reuse_baselines else None), indent=2), encoding='utf-8')
    started, timings, success = time.perf_counter(), {}, False
    executable = [sys.executable, '-u', '-B']
    try:
        for method, script in (('fixed_time', 'FixedTime/run_fixed_time.py'), ('rule_based', 'RuleBased/run_rule_based.py')):
            for seed in seeds:
                for scenario in SCENARIOS:
                    if args.reuse_baselines:
                        from generate_final_report import read_metrics, checked_episode
                        from DRL.artifacts import write_csv
                        stem = f'{scenario}_seed{seed}'
                        source = args.reuse_baselines/'baselines'/method/f'seed{seed}'/f'metrics_{stem}.csv'
                        rows = read_metrics(source)
                        episode = checked_episode(rows, method, scenario, seed)
                        target = evaluation_root/'baselines'/method/f'seed{seed}'
                        write_csv(target/f'metrics_{stem}.csv', rows)
                        write_csv(target/f'episode_{stem}.csv', [episode])
                        logging.info('REUSED verified baseline %s/%s/seed%s from %s', method, scenario, seed, source)
                        continue
                    run(executable+[str(ROOT/script), '--scenario', scenario, '--seed', str(seed),
                        '--output-dir', str(evaluation_root/'baselines'/method/f'seed{seed}')],
                        sublog, timings, f'{method}_{scenario}_seed{seed}')
        run(executable+['-m', 'DRL.train_multiscenario', '--seed', '100', '--timesteps', str(timesteps),
            '--device', 'cuda', '--model-root', str(model_root), '--log-dir', str(run_root),
            '--validation-dir', str(evaluation_root/'validation'), '--eval-freq', str(timesteps if args.dry_run else callback_freq),
            '--checkpoint-freq', str(callback_freq)], sublog, timings, 'drl_training')
        for folder, method, model in (('best', 'drl_ppo', model_root/'best_model/best_model.zip'),
                                     ('final', 'drl_ppo_final', model_root/'ppo_seed100_final.zip')):
            run(executable+['-m', 'DRL.evaluate', '--model', str(model), '--output-dir', str(evaluation_root/folder),
                '--method', method, '--seeds', *map(str, seeds)], sublog, timings, f'drl_evaluation_{folder}')
        timings['pipeline_through_evaluation'] = time.perf_counter()-started
        (result_root/'pipeline_timings.json').write_text(json.dumps(timings, indent=2), encoding='utf-8')
        command = executable+[str(ROOT/'generate_final_report.py'), '--evaluation-root', str(evaluation_root),
            '--result-dir', str(result_root), '--model-root', str(model_root), '--output', str(report_path),
            '--seeds', *map(str, seeds)]
        run(command+(['--dry-run'] if args.dry_run else []), sublog, timings, 'report_generation')
        checks = verify_dry_run(model_root, evaluation_root, result_root, run_root) if args.dry_run else {}
        if historical_manifest() != old_hashes:
            raise AssertionError('Historical artifact preservation check failed')
        if sumo_pids() - before_pids:
            raise RuntimeError('Unexpected SUMO process remains after pipeline; inspect owned processes')
        timings['total_pipeline'] = time.perf_counter()-started
        (result_root/'pipeline_timings.json').write_text(json.dumps(timings, indent=2), encoding='utf-8')
        if args.dry_run:
            # Retain only the preflight evidence, never miniature production models/results.
            checks.update(gpu=gpu, versions=versions, timings=timings, v1_artifacts_unchanged=len(old_hashes),
                          baselines_reused_verified=bool(args.reuse_baselines),
                          owned_sumo_processes_remaining=0, status='passed')
            (results_base/'preflight_check.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
        success = True
        logging.info('PIPELINE COMPLETED: %s (%.2fs)', 'DRY-RUN' if args.dry_run else 'V2 seed100', timings['total_pipeline'])
    except BaseException:
        logging.exception('Pipeline failed; completed artifacts retained for diagnosis')
        raise
    finally:
        logging.shutdown()
        if success and temporary:
            # Resolve and verify the exact recursive-deletion target before deleting it.
            target = temporary.resolve()
            if target.parent != results_base.resolve() or not target.name.startswith('_dry_run_'):
                raise RuntimeError(f'Unsafe dry-run cleanup target: {target}')
            shutil.rmtree(target)
            print(f'Preflight passed; dry-run artifacts removed: {target}', flush=True)
        print('Overnight command: & "'+sys.executable+'" -u run_pipeline_seed100.py', flush=True)


if __name__ == '__main__':
    main()
