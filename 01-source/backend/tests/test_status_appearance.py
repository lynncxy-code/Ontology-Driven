"""NEW-07: grey and wireframe status appearances in the behavior library."""
import unittest

from presentation_catalog import list_resources, validate_selection
from presentation_routing import build_presentation

GRAY = 'ot.industrial.gray_material'
WIREFRAME = 'ot.industrial.wireframe_material'


class StatusAppearanceTests(unittest.TestCase):
    def test_selectable_for_any_state_without_a_default(self):
        for state in ('normal', 'offline', 'fault', 'planned'):
            ids = {r['resource_id'] for r in list_resources(source='ontotwin_common', channel='visual', state=state)}
            self.assertTrue({GRAY, WIREFRAME} <= ids, state)
        # No default: an unconfigured type never routes to them.
        for status in ('offline', 'stopped', 'fault'):
            visual = build_presentation('unit', {'status': status}, {'behavior_library': 'none', 'channels': {}})
            self.assertNotIn(visual['resolution']['channels']['visual']['behavior_id'],
                             ('industrial.visual.gray', 'industrial.visual.wireframe'))

    def test_chosen_state_routes_to_ue_and_clears_on_exit(self):
        for rid, behavior in ((GRAY, 'industrial.visual.gray'), (WIREFRAME, 'industrial.visual.wireframe')):
            with self.subTest(rid=rid):
                item = next(r for r in list_resources(source='ontotwin_common', channel='visual', state='offline')
                            if r['resource_id'] == rid)
                self.assertTrue(item['available'])
                selection = dict(resource_id=rid, source=item['source'], slot=item['slot'])
                self.assertTrue(validate_selection(selection, channel='visual')[0])
                profile = {'behavior_library': 'none',
                           'channels': {'visual': {'states': {'status:offline': selection}}}}
                route = build_presentation('unit', {'status': 'offline'}, profile)['resolution']['channels']['visual']
                self.assertEqual(behavior, route['behavior_id'])
                back = build_presentation('unit', {'status': 'running'}, profile)['resolution']['channels']['visual']
                self.assertEqual('safe.visible', back['behavior_id'])


if __name__ == '__main__':
    unittest.main()
