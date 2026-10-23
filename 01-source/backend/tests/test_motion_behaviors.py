import math
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from motion_behaviors import motion_resources, normalize_motion_params
from presentation_catalog import list_resources, validate_selection
from presentation_routing import build_presentation, profile_fingerprint


class MotionTests(unittest.TestCase):
    def test_real_motion_choices_replace_indicators(self):
        resources = list_resources(channel='animation', source='ontotwin_common', state='normal')
        self.assertEqual(6, len(resources))
        self.assertTrue(all(r['resource_id'].startswith('ot.motion.') for r in resources))

    def test_defaults_all_presets(self):
        for resource in motion_resources():
            self.assertEqual({p['key']: p['default'] for p in resource['parameter_schema']}, normalize_motion_params(resource['resource_id']))

    def test_invalid_parameters_rejected(self):
        for params in ({'speed': float('nan')}, {'speed': True}, {'speed': 0}, {'speed': 721}, {'speed': '90'}, {'axis': 'q'}, {'asset_path':'/Game/Anything'}, []):
            with self.subTest(params=params):
                ok, error, _ = validate_selection({'resource_id':'ot.motion.rotate', 'params':params}, channel='animation')
                self.assertFalse(ok)
                self.assertTrue(error)

    def test_params_reach_wire_and_changes_invalidate_cache(self):
        selection = {'resource_id':'ot.motion.rotate', 'source':'ontotwin_common', 'params':{'axis':'x','direction':'negative','speed':45}}
        profile = {'channels':{'animation':{'states':{'status:normal':selection}}}}
        before = profile_fingerprint(profile)
        result = build_presentation('test', {'status':'normal'}, profile)['resolution']['channels']['animation']
        self.assertEqual('motion.rotate', result['behavior_id'])
        self.assertEqual(dict(selection['params'], target='model'), result['params'])
        self.assertEqual('platform', result['source'])
        selection['params']['speed'] = 120
        self.assertNotEqual(before, profile_fingerprint(profile))
        self.assertEqual(45, result['params']['speed'])

    def test_invalid_stored_params_safe_fallback(self):
        profile = {'channels':{'animation':{'resource_id':'ot.motion.rotate','params':{'speed':-20}}}}
        route = build_presentation('test', {}, profile)['resolution']['channels']['animation']
        self.assertEqual('safe.idle', route['behavior_id'])

    def test_belt_has_independent_material_channel(self):
        profile = {'channels':{'visual':{'resource_id':'ot.material.belt_scroll','source':'ontotwin_common','params':{'speed':-1}}}}
        route = build_presentation('test', {}, profile)['resolution']['channels']['visual']
        self.assertEqual('material.belt_scroll', route['behavior_id'])
        self.assertEqual({'target':'model','speed':-1}, route['params'])
        ok, _, _ = validate_selection(profile['channels']['visual'], channel='animation')
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main()
