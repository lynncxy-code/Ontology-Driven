import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flask import Flask
from instance_labels import label_config, resolve_label, register_label_routes


class LabelTests(unittest.TestCase):
    def setUp(self):
        self.obj = {"injected_interfaces":["I3D_Visual"], "properties":[{"name":"status"}],
                    "interface_configs":{"I3D_Overlay":{"enabled":True}, "I3D_Visual":{"other":"keep"}}}
        self.app = Flask(__name__)
        self.app.testing = True
        self.writes = []
        register_label_routes(self.app, lambda: {"type":self.obj}, lambda: self.writes.append(True))
        self.client = self.app.test_client()

    def save(self, **kw):
        config = {**label_config(self.obj), **kw}
        return self.client.put("/api/v2/ontology/types/type/label-config", json=config)

    def test_default_hidden_ignores_legacy_raw_text(self):
        self.assertEqual("", resolve_label(self.obj, {"id":"one"}, {"ui_label_content":"old text"}))

    def test_save_name_field_fixed_and_disable_without_touching_panel(self):
        self.assertEqual(200, self.save(enabled=True).status_code)
        self.assertEqual("Device A", resolve_label(self.obj, {"id":"one","display_name":"Device A"}, {}))
        self.assertEqual(200, self.save(source="field", field="status").status_code)
        self.assertEqual("0", resolve_label(self.obj, {}, {"status":0}))
        self.assertEqual("", resolve_label(self.obj, {}, {}))
        self.assertEqual(200, self.save(source="fixed", text="Hello").status_code)
        self.assertEqual("Hello", resolve_label(self.obj, {}, {"ui_label_content":"stale"}))
        self.assertEqual(200, self.save(enabled=False, text="").status_code)
        self.assertEqual("", resolve_label(self.obj, {}, {}))
        self.assertTrue(self.obj["interface_configs"]["I3D_Overlay"]["enabled"])
        self.assertEqual("keep", self.obj["interface_configs"]["I3D_Visual"]["other"])
        self.assertEqual(4,len(self.writes))

    def test_invalid_requests_never_write(self):
        before = copy.deepcopy(self.obj)
        for config in ({"enabled":"true"}, {"enabled":True,"source":[]},
                       {"enabled":True,"source":"field","field":"missing"},
                       {"enabled":True,"source":"fixed","text":""}):
            self.assertEqual(400,self.client.put("/api/v2/ontology/types/type/label-config",json=config).status_code)
        self.assertEqual(before,self.obj)
        self.assertEqual([],self.writes)

    def test_removed_visual_capability_stops_label(self):
        self.save(enabled=True,source="fixed",text="text")
        self.obj["injected_interfaces"] = ["I3D_Behavioral"]
        self.assertEqual("",resolve_label(self.obj,{},{}))
        self.assertEqual(400,self.save(enabled=True).status_code)


if __name__ == "__main__":
    unittest.main()
