import unittest
from device_effects import SCAN, HIGHLIGHT
from presentation_catalog import list_resources, validate_selection
from presentation_routing import build_presentation

class DeviceEffectsTests(unittest.TestCase):
    def test_combo_uses_existing_state_routes_and_clears_on_exit(self):
        selected = {'fx': (SCAN, {'style':'rehearsal','radius':12,'interval':2}),
                    'visual': (HIGHLIGHT, {'color':'blocked','duration':8})}
        profile = {'behavior_library':'none','channels':{}}
        for ch, (rid, params) in selected.items():
            opts = list_resources(source='ontotwin_common',channel=ch,state='normal')
            item = next(r for r in opts if r['resource_id']==rid)
            selection = dict(resource_id=rid, source=item['source'],slot=item['slot'],params=params)
            self.assertTrue(validate_selection(selection,channel=ch)[0]); profile['channels'][ch]={'states':{'status:active':selection}}
        def channels(state):return build_presentation('unit',{'status':state},profile)['resolution']['channels']
        for ch,(rid,params) in selected.items():
            route=channels('active')[ch]; self.assertEqual((rid,'platform',params),(route['behavior_id'],route['source'],route['params']))
        self.assertEqual([channels('idle')[c]['behavior_id'] for c in selected],['safe.none','safe.visible'])

    def test_reject_invalid_parameters_but_allow_one_shot_and_continuous_highlight(self):
        for rid,params in [(SCAN,{'interval':1.9}),(SCAN,{'radius':float('nan')}),(SCAN,{'finish':'invalid'}),
                           (HIGHLIGHT,{'duration':601}),(HIGHLIGHT,{'color':'blue'}),(SCAN,{'radius':True})]:
            with self.subTest(params=params):self.assertFalse(validate_selection(dict(resource_id=rid,params=params))[0])
        for rid,params in [(SCAN,{'interval':0}),(SCAN,{'interval':120}),(HIGHLIGHT,{'duration':0})]:
            self.assertTrue(validate_selection(dict(resource_id=rid,params=params))[0])
