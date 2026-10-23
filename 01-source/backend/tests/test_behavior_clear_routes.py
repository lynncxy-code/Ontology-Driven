"""Run production route bodies with in-memory dependencies; never touch ProjectStore."""
import ast
import copy
from pathlib import Path
from types import SimpleNamespace
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from presentation_routing import profile_from_object_type, build_presentation


class ClearRouteTests(unittest.TestCase):
    def test_both_delete_routes_clear_all_compatibility_copies(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'app.py').read_text(encoding='utf-8-sig'))
        names = {'_store_behavior_profile', 'manage_behavior_config', 'manage_presentation_profile'}
        bodies = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        for node in bodies:
            node.decorator_list = []
        for route in names - {'_store_behavior_profile'}:
            with self.subTest(route=route):
                old = {'channels':{'animation':{'resource_id':'ot.motion.rotate','source':'ontotwin_common'}}}
                obj = {'presentation_profile':copy.deepcopy(old), 'interface_configs':{
                    'I3D_Behavioral':{'presentation_profile':copy.deepcopy(old)},
                    'I3D_Presentation':{'presentation_profile':copy.deepcopy(old)},
                    'I3D_Overlay':{'keep':True}}}
                writes = []
                ns = {'copy':copy, '_object_types':{'type':obj}, 'request':SimpleNamespace(method='DELETE'),
                      'jsonify':lambda x:x, '_persist_active_project':lambda:writes.append(True),
                      'profile_from_object_type':profile_from_object_type}
                exec(compile(ast.Module(body=bodies, type_ignores=[]), 'app.py', 'exec'),ns)
                result = ns[route]('type')
                profile = profile_from_object_type(obj)
                self.assertEqual(result['presentation_profile'],profile)
                self.assertEqual({},profile['channels'])
                self.assertEqual(profile,obj['interface_configs']['I3D_Behavioral']['presentation_profile'])
                self.assertEqual(profile,obj['interface_configs']['I3D_Presentation']['presentation_profile'])
                self.assertTrue(obj['interface_configs']['I3D_Overlay']['keep'])
                self.assertEqual(1,len(writes))
                self.assertEqual('safe.idle',build_presentation('test',{'status':'running'},profile)['resolution']['channels']['animation']['behavior_id'])


if __name__ == '__main__':
    unittest.main()
