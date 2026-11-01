"""Generate demand-only H4 scenarios; never rebuild the shared network."""
import argparse
import copy
import hashlib
import math
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parent
SCENARIOS = {
    'Map_Low': dict(N=300, S=300, E=300, W=300),
    'Map_Medium': dict(N=750, S=750, E=750, W=750),
    'Map_High': dict(N=1350, S=1350, E=1350, W=1350),
    'Map_Imbalance': dict(N=1800, S=1800, E=300, W=300),
}
TYPE_SHARES = {'motorcycle': .80, 'car': .17, 'bus': .03}
TURN_SHARES = {'s': .70, 'l': .15, 'r': .15}
NETWORK = ROOT / 'network/intersection.net.xml'


def save(path, root):
    path.parent.mkdir(parents=True, exist_ok=True)
    E.indent(root)
    E.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def generate(seed):
    before = hashlib.sha256(NETWORK.read_bytes()).digest()
    net = E.parse(NETWORK).getroot()
    source = E.parse(ROOT / 'routes/test_routes.rou.xml').getroot()
    types = {v.attrib['id']: v for v in source.findall('vType')}
    for kind in TYPE_SHARES:
        assert types[kind].get('impatience') == 'off'
        straight = types[kind + '_straight']
        assert straight.get('jmAdvance') == '0' and straight.get('jmExtraGap') == '1'
        assert {k: v for k, v in straight.attrib.items() if k not in {'id', 'jmAdvance', 'jmExtraGap'}} == {
            k: v for k, v in types[kind].attrib.items() if k != 'id'}
        left = types[kind + '_left']
        assert left.get('impatience') == '0.3'
        assert {k: v for k, v in left.attrib.items() if k not in {'id', 'impatience'}} == {
            k: v for k, v in types[kind].attrib.items() if k not in {'id', 'impatience'}}
    edges = {e.attrib['id']: e for e in net.findall('edge')}
    connections = net.findall('connection')
    assert math.isclose(sum(TYPE_SHARES.values()), 1)
    assert math.isclose(sum(TURN_SHARES.values()), 1)
    # These direction labels were verified against junction coordinates, not edge names alone.
    incoming = {'N': 'N_in', 'S': 'S_in', 'E': 'E_in', 'W': 'W_in'}
    movements = {}
    for arm, edge in incoming.items():
        movements[arm] = {}
        for turn in TURN_SHARES:
            choices = [c for c in connections if c.get('from') == edge and c.get('dir') == turn]
            assert choices, f'Missing {arm}/{turn}; review turning shares before regenerating'
            targets = {c.attrib['to'] for c in choices}
            assert len(targets) == 1
            movements[arm][turn] = (targets.pop(), choices)
    for name, demand in SCENARIOS.items():
        assert set(demand) == set(incoming)
        routes = E.Element('routes')
        for kind in TYPE_SHARES:
            routes.append(copy.deepcopy(types[kind]))
            routes.append(copy.deepcopy(types[kind + "_left"]))
            routes.append(copy.deepcopy(types[kind + "_straight"]))
        for arm, turns in movements.items():
            for turn, (target, choices) in turns.items():
                E.SubElement(routes, 'route', id=f'{arm}_{turn}', edges=f'{incoming[arm]} {target}')
        for arm, rate in demand.items():
            assert math.isfinite(rate) and rate >= 0
            probabilities = []
            for kind, share in TYPE_SHARES.items():
                for turn, turn_share in TURN_SHARES.items():
                    probability = rate * share * turn_share / 3600
                    assert 0 <= probability <= 1, 'Demand exceeds Bernoulli flow limit'
                    probabilities.append(probability)
                    target, choices = movements[arm][turn]
                    lane = '1' if turn == 'l' or (turn == 's' and kind != 'motorcycle') else '0'
                    candidates = [c for c in choices if c.get('fromLane') == lane]
                    assert candidates, f'Invalid departure lane: {arm}/{kind}/{turn}'
                    cls = types[kind].get('vClass', 'passenger')
                    for c in candidates:
                        for edge, index in [(incoming[arm], lane), (target, c.attrib['toLane'])]:
                            lane_xml = edges[edge].findall('lane')[int(index)]
                            assert cls not in lane_xml.get('disallow', '').split()
                            assert 'allow' not in lane_xml.attrib or cls in lane_xml.get('allow').split()
                    if probability:
                        E.SubElement(routes, 'flow', id=f'{arm}_{kind}_{turn}', type=(kind + '_left' if turn == 'l' else kind + '_straight' if turn == 's' else kind),
                                     route=f'{arm}_{turn}', begin='0', end='3600',
                                     probability=f'{probability:.17g}', departLane=lane, departSpeed='0')
            assert math.isclose(sum(probabilities) * 3600, rate, abs_tol=1e-9)
        config = E.parse(ROOT / 'config/intersection.sumocfg').getroot()
        config.find('input/route-files').set('value', 'traffic.rou.xml')
        config.find('input/additional-files').set('value', '../config/traffic_light.add.xml,../config/environment.add.xml')
        config.find('time/end').set('value', '3600')
        config.find('time/step-length').set('value', '0.1')
        config.find('random_number/seed').set('value', str(seed))
        config.find('gui_only/gui-settings-file').set('value', '../config/gui.view.xml')
        directory = ROOT / name
        save(directory / 'traffic.rou.xml', routes)
        save(directory / 'simulation.sumocfg', config)
        # Read back actual outputs and resolve paths relative to each config.
        E.parse(directory / 'traffic.rou.xml')
        parsed = E.parse(directory / 'simulation.sumocfg')
        for key in ['input/net-file', 'input/route-files', 'input/additional-files', 'gui_only/gui-settings-file']:
            for value in parsed.find(key).get('value').split(','):
                assert (directory / value).is_file(), value
        print(f'{name}: {sum(demand.values())} veh/h; static checks passed')
    assert hashlib.sha256(NETWORK.read_bytes()).digest() == before


def validate():
    executable = shutil.which('sumo')
    if not executable:
        raise SystemExit('SUMO unavailable: static checks passed; runtime checks not executed')
    # Only validation outputs are written here; scenario inputs remain unchanged.
    output = ROOT / 'validation/scenarios'
    output.mkdir(parents=True, exist_ok=True)
    failed = False
    for name in SCENARIOS:
        log = output / f'{name}.log'
        summary = output / f'{name}.summary.xml'
        result = subprocess.run([executable, '-c', str(ROOT / name / 'simulation.sumocfg'),
                                 '--no-step-log', 'true', '--duration-log.statistics', 'true',
                                 '--summary-output', str(summary)], capture_output=True, text=True)
        log.write_text(result.stdout + result.stderr, encoding='utf-8')
        warnings = sum(line.startswith('Warning:') for line in result.stderr.splitlines())
        errors = sum(line.startswith('Error:') for line in result.stderr.splitlines())
        print(f'  warnings={warnings}, errors={errors}')
        failed |= result.returncode != 0
        print(f'{name}: exit={result.returncode}; log={log.relative_to(ROOT)}')
        if result.returncode == 0:
            step = E.parse(summary).getroot().findall('step')[-1]
            print({k: step.get(k) for k in ['time', 'inserted', 'ended', 'waiting', 'running', 'teleports', 'collisions']})
    if failed:
        raise SystemExit('SUMO runtime validation failed; inspect logs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=42, help='SUMO random seed (default: 42)')
    parser.add_argument('--validate', action='store_true', help='Also run all four scenarios with SUMO and save logs')
    args = parser.parse_args()
    generate(args.seed)
    if args.validate:
        validate()
