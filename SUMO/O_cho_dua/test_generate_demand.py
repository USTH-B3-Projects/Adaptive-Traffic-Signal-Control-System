"""Small checks for the approved mixed fleet and generator compatibility."""
import argparse
import math
import shutil
import tempfile
from unittest.mock import patch
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import generate_demand as demand


class MixedFleetTests(unittest.TestCase):
    def test_shares_and_straight_only_buses(self):
        for share,eligible in [(0,.75),(.8,.75),(.85,5/6),(1,.75)]:
            root = ET.Element('routes')
            demand.add_vehicle_types(root, share, eligible)
            mixes = {v.get('id'): dict(zip(v.get('vTypes').split(), map(float,v.get('probabilities').split()))) for v in root.findall('vTypeDistribution')}
            self.assertNotIn('bus',mixes['traffic_mix'])
            for mix in mixes.values():
                self.assertTrue(math.isclose(sum(mix.values()),1))
                self.assertTrue(all(p >= 0 for p in mix.values()))
            self.assertAlmostEqual(.5*eligible*mixes['traffic_mix_straight']['bus'],(1-share)*.15)
            self.assertAlmostEqual(.5*eligible*mixes['traffic_mix_straight']['passenger_car']+(1-.5*eligible)*mixes['traffic_mix']['passenger_car'],(1-share)*.85)

    def test_motorcycle_behavior_preserved(self):
        before = ET.parse(Path(__file__).parent/'fixtures/motorcycle.xml').getroot()
        root = ET.Element('routes')
        demand.add_vehicle_types(root,.8,.75)
        after = root.find('vType[@id="motorcycle"]')
        self.assertEqual({k:v for k,v in before.attrib.items() if k != 'probability'},
                         {k:v for k,v in after.attrib.items() if k != 'color'})


class DemandProfileTests(unittest.TestCase):
    def test_high_is_balanced_for_one_hour(self):
        profile = demand.make_profile('high', 5400, 3600, 42)
        self.assertEqual(profile[0][0], 0)
        self.assertEqual(profile[-1][1], 3600)
        for begin, end, weights in profile:
            self.assertGreater(end, begin)
            self.assertEqual(set(weights), set(demand.APPROACHES))
            for weight in weights.values():
                self.assertAlmostEqual(weight, .25)

    def test_imbalance_covers_three_hours_and_preserves_total(self):
        profile = demand.make_profile('imbalance', 4200, 10800, 42)
        self.assertEqual(len(profile), 360)
        for index, (begin, end, weights) in enumerate(profile):
            self.assertEqual((begin, end), (index * 30, (index + 1) * 30))
            self.assertEqual(set(weights), set(demand.APPROACHES))
            self.assertAlmostEqual(sum(weights.values()), 1)
            self.assertTrue(all(math.isfinite(w) and w > 0 for w in weights.values()))
        self.assertEqual({max(weights, key=weights.get) for _, _, weights in profile},
                         set(demand.APPROACHES))
        self.assertGreater(max(max(weights.values()) for _, _, weights in profile), .5)
        for previous, current in zip(profile, profile[1:]):
            self.assertLess(max(abs(previous[2][name] - current[2][name])
                                for name in demand.APPROACHES), .15)

    def test_generated_imbalance_preserves_demand_and_fleet_each_interval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'config').mkdir()
            for filename in ['base.sumocfg', 'output.add.xml']:
                shutil.copyfile(Path(demand.__file__).parent / 'config' / filename,
                                root / 'config' / filename)
            args = argparse.Namespace(rate=None, duration=None, seed=42,
                                      output=None, motorcycle_share=.8)
            with patch.object(demand, 'ROOT', root):
                demand.generate('imbalance', args)
            directory = root / 'scenarios/Imbalance'
            routes = ET.parse(directory / 'traffic.rou.xml').getroot()
            mixes = {mix.get('id'): dict(zip(mix.get('vTypes').split(),
                     map(float, mix.get('probabilities').split())))
                     for mix in routes.findall('vTypeDistribution')}
            intervals = {}
            for flow in routes.findall('flow'):
                interval = (int(flow.get('begin')), int(flow.get('end')))
                intervals.setdefault(interval, []).append(flow)
            self.assertEqual(sorted(intervals), [(i, i + 30) for i in range(0, 10800, 30)])
            for flows in intervals.values():
                self.assertEqual(len(flows), 12)
                probabilities = [float(flow.get('probability')) for flow in flows]
                self.assertTrue(all(0 <= probability <= 1 for probability in probabilities))
                total = sum(probabilities)
                self.assertAlmostEqual(total * 3600, 4200)
                for kind, expected in [('motorcycle', .8), ('passenger_car', .17), ('bus', .03)]:
                    actual = sum(probability * mixes[flow.get('type')].get(kind, 0)
                                 for flow, probability in zip(flows, probabilities)) / total
                    self.assertAlmostEqual(actual, expected)
            config = ET.parse(directory / 'simulation.sumocfg')
            route_path = directory / config.find('input/route-files').get('value')
            self.assertTrue(route_path.is_file())
            additional = config.find('input/additional-files').get('value').split(',')
            self.assertIn('output.add.xml', additional)
            self.assertIsNotNone(ET.parse(directory / 'output.add.xml').find('edgeData'))
            for output in config.findall('output/*'):
                self.assertTrue((directory / output.get('value')).parent.is_dir())

    def test_profile_seed_and_partial_interval(self):
        profile = demand.make_profile('imbalance', 4200, 10800, 42)
        self.assertEqual(profile, demand.make_profile('imbalance', 4200, 10800, 42))
        self.assertNotEqual(profile, demand.make_profile('imbalance', 4200, 10800, 43))
        short = demand.make_profile('imbalance', 4200, 65, 42)
        self.assertEqual([(begin, end) for begin, end, _ in short], [(0, 30), (30, 60), (60, 65)])


if __name__ == '__main__':
    unittest.main()
