"""Small checks for the approved mixed fleet and generator compatibility."""
import math
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


if __name__ == '__main__':
    unittest.main()
