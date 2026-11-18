import math
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from motion_behaviors import motion_resources, normalize_motion_params
from presentation_catalog import list_resources, validate_selection
from presentation_routing import build_presentation, profile_fingerprint


class MotionTests(unittest.TestCase):
    def test_cleared_channel_does_not_resurrect_platform_defaults(self):
        profile = {'behavior_library':'none','channels':{'fx':{'states':{'status:running':{
            'resource_id':'ot.industrial.alarm_flash','source':'ontotwin_common'}}}}}
        routes = build_presentation('test', {'status':'running'}, profile)['resolution']['channels']
        self.assertEqual('safe.idle', routes['animation']['behavior_id'])
        self.assertEqual('industrial.fx.warning_flash', routes['fx']['behavior_id'])
        profile['channels'] = {}
        routes = build_presentation('test', {'status':'fault','battery_level':10}, profile)['resolution']['channels']
        self.assertEqual(['safe.idle','safe.visible','safe.none','safe.label'], [routes[k]['behavior_id'] for k in ('animation','visual','fx','label')])

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
        self.assertEqual(dict(selection['params'], target='model', pivot='center'), result['params'])
        self.assertEqual('platform', result['source'])
        selection['params']['speed'] = 120
        self.assertNotEqual(before, profile_fingerprint(profile))
        self.assertEqual(45, result['params']['speed'])

    def test_invalid_stored_params_safe_fallback(self):
        profile = {'channels':{'animation':{'resource_id':'ot.motion.rotate','params':{'speed':-20}}}}
        route = build_presentation('test', {}, profile)['resolution']['channels']['animation']
        self.assertEqual('safe.idle', route['behavior_id'])

    def test_bug26_rotation_presets_offer_pivot_defaulting_to_center(self):
        schemas = {r['resource_id']: r['parameter_schema'] for r in motion_resources()}
        for key in ('rotate', 'rotate_to', 'swing'):
            with self.subTest(preset=key):
                pivot = next(p for p in schemas['ot.motion.' + key] if p['key'] == 'pivot')
                self.assertEqual('center', pivot['default'])
                self.assertEqual(['center', 'origin'], [o['value'] for o in pivot['options']])
        for key in ('translate', 'pingpong', 'reset'):
            with self.subTest(preset=key):
                self.assertNotIn('pivot', [p['key'] for p in schemas['ot.motion.' + key]])

    def test_bug26_saved_rotation_without_pivot_turns_around_center(self):
        # Configurations saved before BUG-26 carry no pivot; they must not keep orbiting the file origin.
        profile = {'channels':{'animation':{'resource_id':'ot.motion.rotate','source':'ontotwin_common',
                                            'params':{'axis':'z','direction':'positive','speed':90}}}}
        route = build_presentation('test', {}, profile)['resolution']['channels']['animation']
        self.assertEqual('motion.rotate', route['behavior_id'])
        self.assertEqual('center', route['params']['pivot'])

    def test_bug26_origin_pivot_reaches_wire_and_invalid_pivot_rejected(self):
        profile = {'channels':{'animation':{'resource_id':'ot.motion.swing','source':'ontotwin_common',
                                            'params':{'pivot':'origin'}}}}
        route = build_presentation('test', {}, profile)['resolution']['channels']['animation']
        self.assertEqual('origin', route['params']['pivot'])
        for resource_id, params in (('ot.motion.rotate', {'pivot':'corner'}), ('ot.motion.translate', {'pivot':'center'})):
            with self.subTest(resource_id=resource_id):
                ok, error, _ = validate_selection({'resource_id':resource_id, 'params':params}, channel='animation')
                self.assertFalse(ok)
                self.assertTrue(error)

    def test_bug26_rotation_axis_labels_describe_rotation(self):
        schemas = {r['resource_id']: r['parameter_schema'] for r in motion_resources()}
        rotate_axis = next(p for p in schemas['ot.motion.rotate'] if p['key'] == 'axis')
        move_axis = next(p for p in schemas['ot.motion.translate'] if p['key'] == 'axis')
        self.assertEqual({'x', 'y', 'z'}, {o['value'] for o in rotate_axis['options']})
        self.assertEqual('z', rotate_axis['default'])
        labels = {o['value']: o['label'] for o in rotate_axis['options']}
        self.assertIn('绕竖直轴', labels['z'])
        self.assertIn('绕左右轴', labels['y'])
        self.assertIn('绕前后轴', labels['x'])
        self.assertNotEqual(labels, {o['value']: o['label'] for o in move_axis['options']})

    def test_belt_has_independent_material_channel(self):
        profile = {'channels':{'visual':{'resource_id':'ot.material.belt_scroll','source':'ontotwin_common','params':{'speed':-1}}}}
        route = build_presentation('test', {}, profile)['resolution']['channels']['visual']
        self.assertEqual('material.belt_scroll', route['behavior_id'])
        self.assertEqual({'target':'model','speed':-1}, route['params'])
        ok, _, _ = validate_selection(profile['channels']['visual'], channel='animation')
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main()
