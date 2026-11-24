"""Replay the saved best policy for an isolated, measured action audit.
Never trains or writes original evaluation artifacts. Exactly 12 production episodes.
"""
from pathlib import Path
import csv
import hashlib
import json
import logging
import math
import os
import statistics
import sys
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

SCENARIOS = ('low', 'medium', 'high', 'imbalance')
SEEDS = (101, 102, 103)
METRICS = ('queue_length', 'waiting_time', 'average_speed', 'arrived_count', 'vehicles_in_network')
OUTPUT = ROOT / 'evaluation/seed100/action_audit'
MODEL = ROOT / 'models/seed100/best_model/best_model.zip'
MUTABLE_PLOTS = {
    '01_learning_curves_reward_and_val.png', '02_tensorboard_losses_and_diagnostics.png',
    '03_action_decision_and_override_matrix.png', '04_timeseries_3600s_all_scenarios.png',
    '07_v1_to_v2_progression_comparison.png', 'README.md', 'quality_checks.json',
}
REPORTS = [ROOT / f'results/comparison_result/drl_seed100_comprehensive_report_{lang}.md'
           for lang in ('en', 'vi')]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def unchanged_report_part(text):
    # These are the only user-authorized report regions.
    import re
    text = re.sub(r'(?ms)^### 3\.3 .*?(?=^## 4\.)', '<AUTHORIZED_3_3>\n\n', text, count=1)
    text = re.sub(r'(?ms)^### 6\.1 .*?(?=^### 6\.2 )', '<AUTHORIZED_6_1>\n\n', text, count=1)
    return text


def preservation_snapshot():
    files = set()
    for folder in ('DRL', 'RuleBased', 'FixedTime', 'SUMO', 'evaluation/seed100', 'results/seed100'):
        for path in (ROOT / folder).rglob('*'):
            if not path.is_file() or '__pycache__' in path.parts:
                continue
            if OUTPUT == path or OUTPUT in path.parents:
                continue
            if path.parent == ROOT / 'results/seed100/plots/detailed_analysis' and path.name in MUTABLE_PLOTS:
                continue
            files.add(path)
    files.update(p for p in (ROOT / 'results/comparison_result').glob('*.md') if p not in REPORTS)
    files.update((MODEL, ROOT / 'models/seed100/training_metadata.json'))
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(files)}


def verify_preservation(manifest, report_parts):
    assert all(digest(ROOT / p) == sha for p, sha in manifest.items()), 'Protected artifact changed'
    for path in REPORTS:
        text = path.read_text(encoding='utf-8')
        assert digest_text(unchanged_report_part(text)) == report_parts[path.name], path


def digest_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def outcome(executed, reason):
    if reason == 'max_green':
        return 'forced_max_green'
    if reason == 'min_green':
        return 'blocked_min_green'
    if executed == 'NOOP':
        assert reason == 'in_transition'
        return 'transition_noop'
    assert executed in ('KEEP', 'SWITCH')
    return executed


def main():
    # Inventory schemas before adding any audit records.
    inventory = []
    required = {'requested_action', 'executed_action', 'override_reason', 'phase_id', 'green_elapsed'}
    for folder in ('evaluation/seed100', 'results/seed100'):
        for path in (ROOT / folder).rglob('*.csv'):
            if OUTPUT in path.parents:
                continue
            with path.open(encoding='utf-8-sig', newline='') as stream:
                header = next(csv.reader(stream), [])
            found = sorted(required & set(header))
            inventory.append({'file': path.relative_to(ROOT).as_posix(), 'behavior_columns': found})
    assert not any(row['behavior_columns'] for row in inventory), 'Behavior logs already exist; inspect before replay'
    OUTPUT.mkdir(exist_ok=False)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                        handlers=[logging.StreamHandler(sys.stdout),
                                  logging.FileHandler(OUTPUT/'audit_progress.log', encoding='utf-8')])
    manifest = preservation_snapshot()
    report_parts = {p.name: digest_text(unchanged_report_part(p.read_text(encoding='utf-8'))) for p in REPORTS}
    (OUTPUT/'preservation_manifest.json').write_text(json.dumps({
        'protected_files_sha256': manifest, 'reports_outside_authorized_sections_sha256': report_parts
    }, indent=2), encoding='utf-8')
    (OUTPUT/'archive_inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')

    import torch
    from stable_baselines3 import PPO
    from DRL.gym_env import TrafficSignalEnv
    from DRL.metrics import episode_summary
    from DRL.core.scenario_loader import load_settings
    from DRL.core.simulation import _binary
    import subprocess

    settings = load_settings()
    expected = dict(simulation_step=.1, decision_interval=5, min_green=15,
                    max_green=75, yellow_time=3, all_red_time=3, gui=False)
    assert all(settings[k] == v for k, v in expected.items()), settings
    assert torch.cuda.is_available(), 'Original evaluation used CUDA'
    gpu = torch.cuda.get_device_name(0)
    assert 'Quadro RTX 3000' in gpu
    binary = _binary(settings)
    version = subprocess.run([binary, '--version'], capture_output=True, text=True, check=True).stdout
    (OUTPUT/'runtime.json').write_text(json.dumps({
        'model_sha256': digest(MODEL), 'gpu': gpu, 'torch': torch.__version__,
        'sumo_binary': binary, 'sumo_version': version, 'settings': expected,
        'seeds': SEEDS, 'scenarios': SCENARIOS, 'deterministic': True,
        'requested_episodes': 12, 'training': False
    }, indent=2), encoding='utf-8')
    model = PPO.load(MODEL, device='cuda')
    assert model.observation_space.shape == (12,)
    reference = {(r['scenario'], int(r['seed'])): r
                 for r in read_csv(ROOT/'evaluation/seed100/best/episodes.csv')}
    ref_steps = {}
    for r in read_csv(ROOT/'evaluation/seed100/best/metrics.csv'):
        ref_steps.setdefault((r['scenario'], int(r['seed'])), []).append(r)
    all_steps, all_episodes, switches = [], [], []
    comparisons, step_checks = [], 0
    for seed in SEEDS:
        for scenario in SCENARIOS:
            logging.info('START %s seed=%d', scenario, seed)
            env = TrafficSignalEnv(scenario)
            traffic, rows = [], []
            try:
                obs, reset_info = env.reset(seed=seed)
                signals = env._environment.signals
                raw_next, raw_request = signals._next, signals.request
                context = {'origin': 'automatic', 'request_results': {}}
                local_switches = []

                def traced_next(tls, now):
                    signal = signals._signals[tls]
                    index = signal['index']
                    old_mask = signal['masks'][index]
                    next_index = (index + 1) % len(signal['phases'])
                    if old_mask and signal['masks'][next_index] != old_mask:
                        elapsed = signals.snapshot(tls, now)['green_elapsed']
                        assert 15 - 1e-7 <= elapsed <= 75 + 1e-7, elapsed
                        event = dict(scenario=scenario, seed=seed,
                                     decision_index=len(rows)+1, tls_id=tls,
                                     switch_time=now, phase_id_before=index,
                                     phase_id_after=next_index, green_elapsed=elapsed,
                                     switch_reason='policy_request' if context['origin']=='request' else 'max_green')
                        local_switches.append(event)
                        switches.append(event)
                    return raw_next(tls, now)

                def traced_request(actions, now):
                    context['origin'] = 'request'
                    try:
                        result = raw_request(actions, now)
                        context['request_results'] = {tls: dict(value) for tls, value in result.items()}
                        return result
                    finally:
                        context['origin'] = 'automatic'

                signals._next, signals.request = traced_next, traced_request
                while True:
                    before_time = env._environment.connection.simulation.getTime()
                    before = signals.snapshot('J', before_time)
                    action, _ = model.predict(obs, deterministic=True)
                    switch_offset = len(local_switches)
                    obs, reward, terminated, truncated, info = env.step(int(action))
                    trow = dict(method='drl_ppo', scenario=scenario, seed=seed,
                                simulation_time=info['sim_time'], **{k: info[k] for k in METRICS})
                    traffic.append(trow)
                    original = ref_steps[scenario,seed][len(rows)]
                    for key in ('simulation_time',)+METRICS:
                        assert float(trow[key]) == float(original[key]), (scenario,seed,len(rows)+1,key,trow[key],original[key])
                        step_checks += 1
                    requested = info['requested_action']['J']
                    executed = info['executed_action']['J']
                    reason = info['override_reason']['J'] or ''
                    initial = context['request_results']['J']
                    row = dict(**trow, decision_index=len(rows)+1, decision_start=before_time,
                               requested_action=int(action), requested_action_label=requested,
                               executed_action=executed, override_reason=reason,
                               outcome=outcome(executed, reason),
                               request_executed_action=initial['executed_action'],
                               request_override_reason=initial['override_reason'] or '',
                               pre_phase_id=before['phase_id'], pre_green_elapsed=before['green_elapsed'],
                               pre_in_transition=int(before['in_transition']),
                               phase_id=info['phase_id']['J'], green_elapsed=info['green_elapsed']['J'],
                               reward=reward,
                               green_switch_events=json.dumps(local_switches[switch_offset:], separators=(',',':')),
                               automatic_events=json.dumps(info['automatic_events'], separators=(',',':')))
                    rows.append(row)
                    if len(rows) % 120 == 0:
                        logging.info('PROGRESS %s seed=%d steps=%d/720', scenario, seed, len(rows))
                    if terminated or truncated:
                        break
                assert len(rows) == 720 and traffic[-1]['simulation_time'] == 3600
                episode = episode_summary(traffic)
                for metric in METRICS:
                    actual, target = float(episode[metric]), float(reference[scenario,seed][metric])
                    comparisons.append(dict(scenario=scenario,seed=seed,metric=metric,
                                            actual=actual,reference=target,exact_match=actual==target))
                    assert actual == target, comparisons[-1]
                episode.update(requested_keep=sum(r['requested_action']==0 for r in rows),
                               requested_switch=sum(r['requested_action']==1 for r in rows),
                               executed_keep=sum(r['executed_action']=='KEEP' for r in rows),
                               executed_switch=sum(r['executed_action']=='SWITCH' for r in rows),
                               transition_noop=sum(r['executed_action']=='NOOP' for r in rows),
                               blocked_min_green=sum(r['outcome']=='blocked_min_green' for r in rows),
                               forced_max_green=sum(r['outcome']=='forced_max_green' for r in rows),
                               startup_override=sum(r['request_override_reason']=='startup_phase' for r in rows),
                               completed_green_intervals=len(local_switches),reproducibility='exact')
                all_episodes.append(episode)
                all_steps.extend(rows)
                # Append verified cohorts only. Partial failed runs remain explicitly incomplete.
                for filename, batch in (('action_steps.csv',rows),('action_episodes.csv',[episode]),
                                        ('action_switches.csv',local_switches)):
                    path=OUTPUT/filename
                    with path.open('a',encoding='utf-8',newline='') as stream:
                        writer=csv.DictWriter(stream,fieldnames=list(batch[0]))
                        if stream.tell()==0:writer.writeheader()
                        writer.writerows(batch)
                logging.info('MATCH %s seed=%d: all 5 episode metrics and 720 step records identical',scenario,seed)
            finally:
                env.close()
                assert env._environment.connection is None
                assert env._environment.simulation._process is None
    assert len(all_episodes)==12 and len(all_steps)==8640 and len(comparisons)==60
    verify_preservation(manifest, report_parts)
    proof = dict(status='passed',completed_episodes=12,decision_records=len(all_steps),
                 episode_metric_checks=len(comparisons),episode_metric_exact_matches=sum(c['exact_match'] for c in comparisons),
                 step_metric_and_time_exact_checks=step_checks,max_absolute_episode_difference=0.0,
                 completed_green_intervals=len(switches),
                 outcome_counts=dict(Counter(r['outcome'] for r in all_steps)),
                 request_override_counts=dict(Counter(r['request_override_reason'] or 'no_override' for r in all_steps)),
                 protected_files_unchanged=len(manifest),comparisons=comparisons)
    (OUTPUT/'reproducibility_check.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    text = [
        '# Seed 100 best-model action audit', '',
        'Exactly 12 deterministic replays: seeds 101,102,103 by low,medium,high,imbalance.',
        'No training and no original evaluation modification. CUDA model prediction; original environment/controller.',
        '', f'- Decision records: {len(all_steps)}',
        f'- Episode traffic checks: {len(comparisons)}/60 exact float equality; max absolute difference 0.',
        f'- Step/time checks: {step_checks} exact equalities (720 samples × 12 × 6 fields).',
        f'- Completed green intervals: {len(switches)}','',
        '| Outcome | Count | Fraction of all decisions (%) |','| --- | --- | --- |'
    ]
    for name,count in proof['outcome_counts'].items():
        text.append(f'| {name} | {count} | {100*count/len(all_steps):.6f} |')
    text += ['', 'Matrix categories are exclusive: max-green override, min-green block, transition NOOP, plain KEEP/SWITCH.',
             'Startup-phase overrides, if any, remain KEEP and are separately counted; they are not relabelled min-green.',
             'Panel B excludes NOOP from the KEEP/SWITCH denominator; panel A includes every decision.',
             'Panel C uses pre-transition green_elapsed observed at the actual controller _next boundary, including automatic substeps.',
             'No duration is inferred as phase runs × 5 s. Unfinished green at episode end is right-censored and excluded.',
             'Runtime wrappers only record calls and delegate unchanged to original bound controller methods.',
             'action_steps.csv retains pre/post state, request-time execution, interval execution and exact transition JSON.',
             'action_switches.csv contains every completed green interval. Arrivals remain episode SUM, other metrics remain time means.',
             '', 'Protected-input hashes and report-region hashes are in preservation_manifest.json.',
             'Detailed exact traffic checks are in reproducibility_check.json.']
    (OUTPUT/'action_audit_summary.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    logging.info('ACTION AUDIT PASSED: %s',json.dumps({k:v for k,v in proof.items() if k!='comparisons'}))

if __name__ == '__main__':
    main()

