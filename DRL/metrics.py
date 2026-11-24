"""Shared directional observations and post-step traffic metric definitions."""
import statistics

SCENARIOS = ('low', 'medium', 'high', 'imbalance')
HELD_OUT_SEEDS = (101, 102, 103)
NS_LANES = ('N_in_0', 'N_in_1', 'S_in_0', 'S_in_1')
EW_LANES = ('E_in_0', 'E_in_1', 'W_in_0', 'W_in_1')
INCOMING_LANES = NS_LANES + EW_LANES
METRICS = ('queue_length', 'waiting_time', 'average_speed',
           'arrived_count', 'vehicles_in_network')


def directional(lanes, ids):
    selected = [lanes[lane] for lane in ids]
    queue = sum(lane['halting_count'] for lane in selected)
    vehicles = sum(lane['vehicle_count'] for lane in selected)
    waiting = sum(lane['waiting_time'] or 0.0 for lane in selected)
    speed = sum((lane['average_speed'] or 0.0) * lane['vehicle_count']
                for lane in selected) / vehicles if vehicles else 13.9
    return queue, vehicles, waiting, speed


def traffic_row(state, info, seed, method):
    totals = state['tls']['J']['totals']
    return dict(method=method, scenario=state['scenario'], seed=seed,
                simulation_time=info['sim_time'],
                queue_length=totals['halting_count'],
                waiting_time=totals['waiting_time'] or 0.0,
                average_speed=totals['average_speed'] or 0.0,
                arrived_count=int(info['arrived_count']),
                vehicles_in_network=info['vehicles_in_network'])


def episode_summary(rows):
    if not rows:
        raise ValueError('Episode has no post-step samples')
    summary = {k: rows[0][k] for k in ('method', 'scenario', 'seed')}
    summary.update({metric: (sum(r[metric] for r in rows) if metric == 'arrived_count'
                            else statistics.fmean(r[metric] for r in rows))
                    for metric in METRICS})
    summary.update(samples=len(rows), end_time=rows[-1]['simulation_time'])
    return summary


def aggregate_episodes(episodes):
    groups = {}
    for row in episodes:
        groups.setdefault((row['method'], row['scenario']), []).append(row)
    output = []
    for (method, scenario), rows in groups.items():
        seeds = [int(row['seed']) for row in rows]
        if len(set(seeds)) != len(seeds):
            raise ValueError(f'Duplicate evaluation seeds: {method}/{scenario}')
        result = dict(method=method, scenario=scenario, n_seeds=len(rows),
                      seeds=','.join(map(str, sorted(seeds))))
        for metric in METRICS:
            values = [float(row[metric]) for row in rows]
            result[metric + '_mean'] = statistics.fmean(values)
            result[metric + '_std'] = statistics.stdev(values) if len(values) > 1 else 0.0
        output.append(result)
    return output
