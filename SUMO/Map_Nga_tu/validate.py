"""Validate the full continuous intersection or its finite movement diagnostic."""
from pathlib import Path
import argparse
import subprocess
import math
import json
from itertools import combinations
from collections import Counter, defaultdict
import xml.etree.ElementTree as E

R = Path(__file__).resolve().parent


def base_kind(kind):
    return kind.removesuffix('_left').removesuffix('_straight')


def rectangle_gaps(a, b):
    """Signed longitudinal/lateral clearance of road-aligned body rectangles."""
    return max(a[0]-b[1], b[0]-a[1]), max(a[2]-b[3], b[2]-a[3])


# A side-by-side pair is valid; a pair overlapping on both axes is not.
assert math.isclose(rectangle_gaps((0,2,0,.8), (0,2,1.4,2.2))[1], .6)
assert all(gap < 0 for gap in rectangle_gaps((0,2,0,.8), (1,3,.4,1.2)))
assert rectangle_gaps((0,2,0,.8), (2.5,4.5,0,.8))[0] == .5

parser = argparse.ArgumentParser(description=__doc__)
mode = parser.add_mutually_exclusive_group()
mode.add_argument('--diagnostic', action='store_true', help='Check the separate 40-vehicle diagnostic')
mode.add_argument('--continuous', action='store_true', help='Alias for the default full simulation')
parser.add_argument('--output-dir', default='validation', help='Evidence directory inside Map_Nga_tu')
args = parser.parse_args()
config_path = 'config/movement_test.sumocfg' if args.diagnostic else 'config/intersection.sumocfg'
prefix = 'movement_' if args.diagnostic else ''
out = (R / args.output_dir).resolve()
if not out.is_relative_to(R):
    parser.error('output-dir must stay inside Map_Nga_tu')
out.mkdir(parents=True, exist_ok=True)
def output(name):
    return (out / (prefix + name)).relative_to(R).as_posix()

dump = E.Element('additional')
E.SubElement(dump, 'timedEvent', type='SaveTLSStates', source='J', dest=prefix+'tls_states.xml')
E.ElementTree(dump).write(R / output('tls_dump.add.xml'))
command = ['sumo','-c',config_path,'--additional-files',
           'config/traffic_light.add.xml,config/environment.add.xml,'+output('tls_dump.add.xml'),
           '--tripinfo-output',output('tripinfo.xml'),'--summary-output',output('summary.xml'),
           '--fcd-output',output('fcd.xml'),'--fcd-output.attributes','id,x,y,angle,type,speed,pos,lane,posLat',
           '--lanechange-output',output('lanechanges.xml'),
           '--log',output('sumo.log'),'--no-step-log','true','--duration-log.statistics','true']
subprocess.run(command,cwd=R,check=True)
net = E.parse(R / 'network/intersection.net.xml').getroot()
roads = [edge for edge in net.findall('edge') if edge.get('function') != 'internal']
assert len(roads) == 8
for edge in roads:
    assert len(edge.findall('lane')) == 2
    for lane in edge:
        assert float(lane.get('length')) == 250 and float(lane.get('width')) == 3.25
        assert not lane.get('allow') and not lane.get('disallow'), 'No class-exclusive lanes'
assert len(net.findall("junction[@type='traffic_light_right_on_red']")) == 1
links = [c for c in net.findall('connection') if c.get('tl') == 'J']
assert len(links) == 16
movements = {'N':{'r':'W','s':'S','l':'E'}, 'E':{'r':'N','s':'W','l':'S'},
             'S':{'r':'E','s':'N','l':'W'}, 'W':{'r':'S','s':'E','l':'N'}}
actual = {(c.get('from'),c.get('to'),int(c.get('fromLane')),int(c.get('toLane')),int(c.get('linkIndex')),c.get('dir')) for c in links}
expected = {(arm+'_in',movements[arm][direction]+'_out',lane,lane,i*4+j,direction)
            for i,arm in enumerate('NESW') for j,(direction,lane) in enumerate([('r',0),('s',0),('s',1),('l',1)])}
assert actual == expected
link_by_index = {int(c.get('linkIndex')):c for c in links}
# Left turns contain a second internal segment; map both segments to their signal.
internal_next = {c.get('from')+'_'+c.get('fromLane'):c.get('via') for c in net.findall('connection') if c.get('via')}
via_index = {}
for c in links:
    lane = c.get('via')
    while lane:
        via_index[lane] = int(c.get('linkIndex'))
        lane = internal_next.get(lane)
phases = E.parse(R / 'config/traffic_light.add.xml').findall('.//phase')
expected_phases = []
for green,left in [({0,1,2,3,8,9,10,11},{3,11}),({4,5,6,7,12,13,14,15},{7,15})]:
    for suffix,seconds,light in [(' start',3,'G'),('',48,'G'),(' yellow',3,'y'),(' clearance',3,'r')]:
        state = ''.join(('g' if i in left else 'G') if light == 'G' and i in green
                        else light if i in green
                        else ('s' if light == 'G' and not suffix and i in {0,4,8,12} else 'r')
                        for i in range(16))
        expected_phases.append((seconds,state))
assert [(float(p.get('duration')),p.get('state')) for p in phases] == expected_phases
cycle = sum(float(p.get('duration')) for p in phases)
assert cycle == 114
junction = net.find("junction[@id='J']")
internal = junction.get('intLanes').split()
for phase in phases:
    state = phase.get('state')
    for request in junction.findall('request'):
        i = int(request.get('index'))
        for j,foe in enumerate(reversed(request.get('foes'))):
            if foe == '1':
                assert not (state[via_index[internal[i]]] == 'G' and state[via_index[internal[j]]] == 'G'), (state,i,j)
                if state[via_index[internal[i]]] == 'g' and state[via_index[internal[j]]] == 'G':
                    assert request.get('response')[::-1][j] == '1', ('Permissive left must yield',i,j)
                if state[via_index[internal[i]]] == 's' and state[via_index[internal[j]]] in 'Gg':
                    assert request.get('response')[::-1][j] == '1', ('Right-on-red must yield',i,j)
tls = {round(float(s.get('time')),1):s for s in E.parse(R / output('tls_states.xml')).getroot()}
for time,state in tls.items():
    assert state.get('programID') == 'test'
    remaining = time % cycle
    for phase in phases:
        duration = float(phase.get('duration'))
        if remaining < duration:
            assert state.get('state') == phase.get('state'), time
            break
        remaining -= duration
config = E.parse(R / config_path).getroot()
route_path = (R / config_path).parent / config.find('input/route-files').get('value')
routes = E.parse(route_path).getroot()
types = {v.get('id'):v for v in routes.findall('vType')}
assert all(float(v.get('jmStopSignWait')) == 1 for v in types.values())
assert all(v.get('impatience') == ('0.3' if kind.endswith('_left') else 'off')
           and float(v.get('jmStoplineGapMinor')) == 1 for kind,v in types.items())
base_types = {base_kind(kind) for kind in types}
assert all(types[kind + '_straight'].get('jmAdvance') == '0'
           and types[kind + '_straight'].get('jmExtraGap') == '1' for kind in base_types)
route_edges = {r.get('id'):r.get('edges').split() for r in routes.findall('route')}
vehicles = {v.get('id'):v for v in routes.findall('vehicle')}
flows = routes.findall('flow')
flow_by_id = {f.get('id'):f for f in flows}
assert not (vehicles and flows), 'The full simulation must not also load diagnostic vehicles'
assert len(flow_by_id) == len(flows), 'Duplicate flows'
entry_lanes = Counter()
previous, crossed, stopped = {}, {}, set()
queue_max = defaultdict(int)
minimum_gap = math.inf
stopped_gaps = defaultdict(list)
lateral_vehicles = defaultdict(set)
parallel_stopped = set()
stop_run, stop_best = defaultdict(float), defaultdict(float)
right_on_red = []
for _,step in E.iterparse(R / output('fcd.xml'),events=('end',)):
    if step.tag != 'timestep':
        continue
    time = round(float(step.get('time')),1)
    lane_vehicles = defaultdict(list)
    road_vehicles = defaultdict(list)
    footprints = {}
    for v in step:
        vid,lane = v.get('id'),v.get('lane')
        old = previous.get(vid,'')
        if lane.startswith(':') and '_in_' in old:
            index = via_index[lane]
            # FCD movement and TLS output both describe this step, including green onset.
            signal = tls[time].get('state')[index]
            assert signal in 'GgyYs', (vid,time,index)
            if signal == 's':
                assert index in {0,4,8,12}, ('Only right turns may use s',vid,index)
                assert stop_best[vid] >= .99, ('Right-on-red requires a 1 s stop near the line',vid,time,stop_best[vid])
                right_on_red.append((vid,time,index,round(stop_best[vid],1)))
            c = link_by_index[index]
            spec = vehicles[vid] if vehicles else flow_by_id[vid.rsplit('.',1)[0]]
            source,target = route_edges[spec.get('route')]
            assert c.get('from') == source and c.get('to') == target
            direction = spec.get('route')[-1]
            kind = base_kind(spec.get('type'))
            incoming_index = int(c.get('fromLane'))
            entry_lanes[(kind,direction,incoming_index)] += 1
            expected_lane = 1 if direction == 'l' or (direction == 's' and kind != 'motorcycle') else 0
            if vehicles or direction != 's':
                assert incoming_index == (int(spec.get('departLane')) if vehicles and direction == 's' else expected_lane), (vid,c.attrib)
            crossed[vid] = index
        if '_in_' in lane:
            lane_vehicles[lane].append(v)
            if float(v.get('pos')) > 200 and float(v.get('speed')) < .1:
                stopped.add(vid)
            if float(v.get('pos')) >= 248 and float(v.get('speed')) < .1:
                stop_run[vid] += .1
                stop_best[vid] = max(stop_best[vid],stop_run[vid])
            else:
                stop_run[vid] = 0
        if not lane.startswith(':'):
            road_vehicles[lane.rsplit('_',1)[0]].append(v)
            assert v.get('posLat') is not None, 'Lateral position must be recorded for 2D checks'
            lateral = int(lane.rsplit('_',1)[1])*3.25 + float(v.get('posLat'))
            width = float(types[base_kind(v.get('type'))].get('width'))
            position = float(v.get('pos'))
            footprints[vid] = (position-float(types[base_kind(v.get('type'))].get('length')),position,lateral-width/2,lateral+width/2)
            assert lateral-width/2 >= -1.625-.03 and lateral+width/2 <= 4.875+.03, (time,vid,'outside road')
            if abs(float(v.get('posLat'))) > .2:
                lateral_vehicles[base_kind(v.get('type'))].add(vid)
        previous[vid] = lane
    for lane,items in lane_vehicles.items():
        queued = [v for v in items if float(v.get('speed')) < .1 and float(v.get('pos')) > 180]
        queue_max[lane] = max(queue_max[lane],len(queued))
    # All pairs across both lanes: side-by-side is legal only without lateral overlap.
    for edge,items in road_vehicles.items():
        items.sort(key=lambda v:float(v.get('pos')),reverse=True)
        for leader,follower in combinations(items,2):
            gap,side_gap = rectangle_gaps(footprints[leader.get('id')],footprints[follower.get('id')])
            assert gap >= -.03 or side_gap >= -.03, (time,edge,leader.attrib,follower.attrib,gap,side_gap)
            both_stopped = max(float(leader.get('speed')),float(follower.get('speed'))) < .1
            if side_gap < -.03:
                minimum_gap = min(minimum_gap,gap)
                if both_stopped:
                    assert gap >= float(types[follower.get('type')].get('minGap')) - .03, (time,edge,gap)
                    stopped_gaps[follower.get('type')].append(gap)
            elif gap < -.03 and both_stopped and '_in' in edge and leader.get('lane') == follower.get('lane') and leader.get('type') == follower.get('type') == 'motorcycle':
                parallel_stopped.add(tuple(sorted([leader.get('id'),follower.get('id')])))
    step.clear()
trips = E.parse(R / output('tripinfo.xml')).getroot().findall('tripinfo')
expected_count = len(vehicles) if vehicles else sum(math.ceil((float(f.get('end'))-float(f.get('begin')))*float(f.get('vehsPerHour'))/3600-1e-9) for f in flows)
assert len(trips) == len(crossed) == expected_count
assert {base_kind(t.get('vType')) for t in trips} == {'motorcycle','car','bus'}
assert all(float(t.get('arrival')) > 0 for t in trips)
max_delay = max(float(t.get('departDelay')) for t in trips)
assert max_delay <= (0 if vehicles else cycle), 'Persistent insertion delay exceeds one cycle'
trips_by_flow = defaultdict(list)
for trip in trips:
    vid = trip.get('id')
    spec = vehicles[vid] if vehicles else flow_by_id[vid.rsplit('.',1)[0]]
    source,target = route_edges[spec.get('route')]
    assert trip.get('departLane') == source+'_'+spec.get('departLane')
    assert trip.get('arrivalLane').startswith(target+'_')
    if not vehicles:
        trips_by_flow[spec.get('id')].append(trip)
assert stopped and max(queue_max.values()) >= 2
changes = E.parse(R / output('lanechanges.xml')).getroot().findall('change')
for change in changes:
    for side in ['leader','follower']:
        gap,secure = change.get(side+'Gap'),change.get(side+'SecureGap')
        if gap != 'None' and secure != 'None':
            assert float(gap) >= float(secure) - .03, change.attrib
if vehicles:
    assert len(vehicles) == 40 and len(route_edges) == 12
    coverage = {(v.get('id')[0],base_kind(v.get('type')),v.get('route')[-1]) for v in vehicles.values()}
    assert coverage == {(arm,kind,direction) for arm in 'NESW' for kind in base_types for direction in 'rsl'}
    for arm in 'NESW':
        assert any(c.get('id') == arm+'_motorcycle_filter' and c.get('from') == arm+'_in_0' and c.get('to') == arm+'_in_1' for c in changes)
    assert {vid.split('_')[1] for vid,_,_,_ in right_on_red} == base_types, 'Diagnostic must exercise stop-and-yield for all types'
else:
    assert len(route_edges) == 12 and len(flows) == 36
    assert {index for _,_,index,_ in right_on_red} == {0,4,8,12}, 'Exercise right-on-red on all four approaches'
    diagnostic_types = {v.get('id'):v.attrib for v in E.parse(R / 'routes/movement_test.rou.xml').getroot().findall('vType')}
    assert {kind:v.attrib for kind,v in types.items()} == diagnostic_types
    coverage = {(flow.get('id')[0],base_kind(flow.get('type')),flow.get('route')[-1]) for flow in flows}
    assert coverage == {(arm,kind,direction) for arm in 'NESW' for kind in base_types for direction in 'rsl'}
    assert {(index//4,index%4) for index in crossed.values()} == {(i,j) for i in range(4) for j in range(4)}
    shares = {'motorcycle':.8,'car':.17,'bus':.03}
    counts = Counter(base_kind(t.get('vType')) for t in trips)
    total_rate = sum(float(f.get('vehsPerHour')) for f in flows)
    for kind,share in shares.items():
        rate = sum(float(f.get('vehsPerHour')) for f in flows if base_kind(f.get('type')) == kind)
        assert math.isclose(rate/total_rate,share,abs_tol=1e-10)
        # Finite periodic streams round their counts at the interval boundaries.
        assert abs(counts[kind]/len(trips)-share) < .03
    for direction,share in [('s',.6),('l',.2),('r',.2)]:
        rate = sum(float(f.get('vehsPerHour')) for f in flows if f.get('route').endswith('_'+direction))
        assert math.isclose(rate/total_rate,share,abs_tol=1e-10)
    for arm in 'NESW':
        rate = sum(float(f.get('vehsPerHour')) for f in flows if f.get('route').startswith(arm+'_'))
        assert math.isclose(rate/total_rate,.25,abs_tol=1e-10)
    for kind in base_types:
        preferred = 0 if kind == 'motorcycle' else 1
        straight_total = sum(count for (k,d,lane),count in entry_lanes.items() if k == kind and d == 's')
        # Preference is soft: straight traffic may use either legal lane around queues.
        assert entry_lanes[(kind,'s',preferred)] > straight_total / 2
    for flow in flows:
        preferred = 1 if flow.get('route').endswith('_l') or (flow.get('route').endswith('_s') and base_kind(flow.get('type')) != 'motorcycle') else 0
        assert flow.get('departLane') == str(preferred)
        selected = trips_by_flow[flow.get('id')]
        scheduled = sorted(float(t.get('depart'))-float(t.get('departDelay')) for t in selected)
        period = 3600/float(flow.get('vehsPerHour'))
        assert abs(scheduled[0]-float(flow.get('begin'))) < .11
        assert scheduled[-1] >= float(flow.get('end')) - period - .11
        assert all(abs(b-a-period) < .11 for a,b in zip(scheduled,scheduled[1:]))
    assert max(float(t.get('depart')) for t in trips) > 146.4
    duration = max(float(f.get('end')) for f in flows)
    for arm in 'NESW':
        departures = sorted(float(t.get('depart')) for t in trips if t.get('id').startswith(arm+'_'))
        # The dominant motorcycle stream alone must provide regular arrivals.
        dominant = flow_by_id[arm+'_motorcycle_s']
        period = 3600/float(dominant.get('vehsPerHour'))
        assert departures[-1] > duration-period-.11
        assert max(b-a for a,b in zip(departures,departures[1:])) <= period + max_delay + .11
summary = E.parse(R / output('summary.xml')).getroot().findall('step')
assert all(int(s.get('collisions','0')) == 0 and int(s.get('teleports','0')) == 0 for s in summary)
assert int(summary[-1].get('running')) == int(summary[-1].get('waiting')) == 0
log = (R / output('sumo.log')).read_text()
assert 'Warning:' not in log and 'Error:' not in log
(R / output('right_on_red.json')).write_text(json.dumps([
    dict(vehicle=vid,time=time,link=index,stop_seconds=stop) for vid,time,index,stop in right_on_red
],indent=2))
report = (f'PASS: 8 road edges, 16 road lanes (250 m x 3.25 m), 16 controlled links; all classes permitted.\n'
          f'PASS: {len(route_edges)} routes; fixed {cycle:g} s cycle; runtime states and stop/yield priorities verified; no conflicting priority greens.\n'
          f'PASS: {len(trips)}/{expected_count} arrivals; no unauthorized red entry, collisions, teleports or warnings.\n'
          f'Departure delay: maximum {max_delay:g} s; mean {sum(float(t.get("departDelay")) for t in trips)/len(trips):.2f} s.\n'
          f'Types: {dict(Counter(t.get("vType") for t in trips))}.\n'
          f'Movements: {dict(Counter(link_by_index[index].get("dir") for index in crossed.values()))}.\n'
          f'Entry lanes (type,movement,lane): {dict(entry_lanes)}.\n'
          f'Last departure: {max(float(t.get("depart")) for t in trips):g} s.\n'
          f'Stopped near junction: {len(stopped)}; maximum queue by incoming lane: {dict(queue_max)}.\n'
          f'Lane changes: {len(changes)}; all recorded leader/follower safety gaps respected.\n'
          f'Minimum road longitudinal gap where lateral footprints overlap: {minimum_gap:.2f} m.\n'
          f'Minimum stopped following gaps by type (m): { {kind:round(min(gaps),2) for kind,gaps in stopped_gaps.items()} }.\n'
          f'Vehicles observed off-center by more than 0.2 m: { {kind:len(ids) for kind,ids in lateral_vehicles.items()} }.\n'
          f'Unique stopped motorcycle pairs side-by-side within one incoming lane: {len(parallel_stopped)}.\n'
          f'Right-on-red entries: {len(right_on_red)}; all stopped near line at least 1 s.\n'
          f'Right-on-red types: {dict(Counter(vid.split("_")[1] for vid,_,_,_ in right_on_red))}.\n'
          f'Final arrival: {max(float(t.get("arrival")) for t in trips):g} s.\n'
          'Command: '+subprocess.list2cmdline(command)+'\n')
(R / output('results.txt')).write_text(report)
print(report)
