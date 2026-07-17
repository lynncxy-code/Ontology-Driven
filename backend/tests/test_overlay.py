import json
import os
import sys
import tempfile
import unittest

from flask import Flask


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from overlay.api import register_overlay_routes
from overlay.service import OverlayService, resolve_overlay_interface
from project_store import CURRENT_SCHEMA_VERSION, ProjectStore


def overlay_config(template_id="title_metrics"):
    slots = {
        "title": {
            "required": True,
            "binding": {"source": "instance", "path": "display_name"},
            "format": {"empty_text": "--"},
        }
    }
    if template_id == "title_metrics":
        slots["metrics"] = [{
            "id": "temperature",
            "label": "温度",
            "required": False,
            "binding": {"source": "raw_state", "path": "temperature"},
            "format": {"precision": 1, "unit": "°C", "empty_text": "--"},
        }]
    return {
        "enabled": True,
        "template_id": template_id,
        "display_mode": "selected",
        "anchor": {"strategy": "bounds_top", "offset_cm": {"x": 0, "y": 0, "z": 20}},
        "slots": slots,
    }


class OverlayTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.projects_dir = os.path.join(self.temp.name, "projects")
        self.active_file = os.path.join(self.temp.name, "active.json")
        self.store = ProjectStore(self.projects_dir, self.active_file)
        self.store.create_project(
            "Overlay Test",
            project_id="overlay_test",
            object_types={
                "machine": {
                    "rid": "machine",
                    "name": "Machine",
                    "properties": [{"name": "temperature", "label": "温度", "type": "number"}],
                    "injected_interfaces": ["I3D_Representable", "I3D_Overlay"],
                }
            },
        )
        self.store.spawn("machine_01", "machine")
        self.store.update_raw_state("machine_01", {"temperature": 36.54}, persist=True)
        self.service = OverlayService(self.store)

    def tearDown(self):
        self.temp.cleanup()

    def test_new_project_uses_current_schema(self):
        self.assertEqual(CURRENT_SCHEMA_VERSION, self.store.get_active_copy()["schema_version"])

    def test_unversioned_project_migrates_on_activation(self):
        self.store.deactivate()
        legacy = {
            "id": "legacy",
            "name": "Legacy",
            "created_at": "2026-01-01 00:00:00",
            "object_types": {},
            "instances": {},
        }
        os.makedirs(self.projects_dir, exist_ok=True)
        with open(os.path.join(self.projects_dir, "legacy.json"), "w", encoding="utf-8") as handle:
            json.dump(legacy, handle)
        self.assertTrue(self.store.activate("legacy"))
        self.assertEqual(CURRENT_SCHEMA_VERSION, self.store.get_active_copy()["schema_version"])
        with open(os.path.join(self.projects_dir, "legacy.json"), "r", encoding="utf-8") as handle:
            migrated = json.load(handle)
        self.assertNotIn("schema_version", migrated)

        self.store.set_scene_interactions(self.store.get_scene_interactions())
        with open(os.path.join(self.projects_dir, "legacy.json"), "r", encoding="utf-8") as handle:
            migrated = json.load(handle)
        self.assertEqual(CURRENT_SCHEMA_VERSION, migrated["schema_version"])
        self.assertEqual(0, migrated["scene_interactions"]["revision"])
        self.assertFalse(migrated["scene_interactions"]["roaming"]["enabled"])

    def test_type_save_and_resolved_snapshot(self):
        saved = self.service.save_type("machine", overlay_config(), 0)
        self.assertEqual(1, saved["revision"])
        project = self.store.get_active_copy()
        object_type = project["object_types"]["machine"]
        instance = project["instances"]["machine_01"]
        payload = resolve_overlay_interface(object_type, instance)
        self.assertEqual("t1-i0", payload["config_revision"])
        self.assertEqual("36.5 °C", payload["resolved_slots"]["metrics"][0]["display_value"])

    def test_instance_override_and_restore_inheritance(self):
        self.service.save_type("machine", overlay_config(), 0)
        saved = self.service.save_instance(
            "machine_01",
            {"slots": {"title": {
                "required": True,
                "binding": {"source": "literal", "value": "一号设备"},
                "format": {"empty_text": "--"},
            }}},
            0,
        )
        self.assertEqual(1, saved["revision"])
        context = self.service.context(instance_id="machine_01")
        self.assertEqual("一号设备", context["preview"]["resolved_slots"]["title"]["display_value"])
        cleared = self.service.clear_instance("machine_01", 1)
        self.assertEqual(2, cleared["revision"])
        context = self.service.context(instance_id="machine_01")
        self.assertEqual("machine_01", context["preview"]["resolved_slots"]["title"]["display_value"])

    def test_batch_is_atomic_on_revision_conflict(self):
        self.store.spawn("machine_02", "machine")
        self.service.save_type("machine", overlay_config(), 0)
        with self.assertRaises(Exception):
            self.service.batch_instances(
                "machine",
                ["machine_01", "machine_02"],
                {"enabled": False},
                {"machine_01": 0, "machine_02": 99},
            )
        project = self.store.get_active_copy()
        for instance_id in ("machine_01", "machine_02"):
            env = project["instances"][instance_id].get("render_config", {}).get("interface_overrides", {})
            self.assertNotIn("I3D_Overlay", env)

    def test_http_revision_conflict(self):
        app = Flask(__name__)
        register_overlay_routes(app, self.store)
        client = app.test_client()
        first = client.put("/api/v2/overlays/object-types/machine", json={
            "expected_revision": 0,
            "config": overlay_config(),
        })
        self.assertEqual(200, first.status_code)
        conflict = client.put("/api/v2/overlays/object-types/machine", json={
            "expected_revision": 0,
            "config": overlay_config(),
        })
        self.assertEqual(409, conflict.status_code)


if __name__ == "__main__":
    unittest.main()
