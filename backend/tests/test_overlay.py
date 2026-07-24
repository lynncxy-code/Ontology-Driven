import json
import os
import sys
import tempfile
import threading
import time
import unittest
import uuid

from flask import Flask


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from overlay.api import register_overlay_routes
from overlay.schema import OverlayValidationError
from overlay.service import OverlayService, resolve_overlay_interface
from project_store import CURRENT_SCHEMA_VERSION, ProjectStore

try:
    from db import pg as pg_db
    from project_store_pg import ProjectStorePG
except (ImportError, ModuleNotFoundError):
    pg_db = None
    ProjectStorePG = None


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
            "emphasized": False,
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
        self.assertEqual("balanced", saved["values"]["presentation"]["quality_tier"])
        project = self.store.get_active_copy()
        object_type = project["object_types"]["machine"]
        instance = project["instances"]["machine_01"]
        payload = resolve_overlay_interface(object_type, instance)
        self.assertEqual("t1-i0", payload["config_revision"])
        self.assertEqual("balanced", payload["presentation"]["quality_tier"])
        self.assertEqual("36.5 °C", payload["resolved_slots"]["metrics"][0]["display_value"])
        self.assertEqual(36.54, payload["resolved_slots"]["metrics"][0]["numeric_value"])
        self.assertFalse(payload["resolved_slots"]["metrics"][0]["emphasized"])
        self.assertEqual("value", saved["values"]["presentation"]["metrics"]["style"])

    def test_gauge_contract_resolves_raw_numeric_value_and_range(self):
        config = overlay_config()
        config["presentation"] = {
            "quality_tier": "balanced",
            "metrics": {
                "style": "gauge",
                "primary_metric_id": "temperature",
                "gauge": {"min": 0, "max": 100, "clamp_visual": True},
            },
        }
        self.service.save_type("machine", config, 0)
        project = self.store.get_active_copy()
        payload = resolve_overlay_interface(
            project["object_types"]["machine"],
            project["instances"]["machine_01"],
            online=True,
        )
        self.assertEqual(36.54, payload["resolved_slots"]["metrics"][0]["numeric_value"])
        self.assertEqual({
            "style": "gauge",
            "primary_metric_id": "temperature",
            "range": {"min": 0, "max": 100, "clamp_visual": True},
        }, payload["resolved_slots"]["metrics_visual"])

    def test_gauge_rejects_invalid_primary_and_range(self):
        for presentation, expected_path in (
            ({"style": "gauge", "primary_metric_id": "missing", "gauge": {"min": 0, "max": 100, "clamp_visual": True}}, "presentation.metrics.primary_metric_id"),
            ({"style": "gauge", "primary_metric_id": "temperature", "gauge": {"min": 10, "max": 10, "clamp_visual": True}}, "presentation.metrics.gauge.max"),
        ):
            config = overlay_config()
            config["presentation"] = {"quality_tier": "balanced", "metrics": presentation}
            with self.assertRaises(OverlayValidationError) as raised:
                self.service.save_type("machine", config, 0)
            self.assertTrue(any(item.get("path") == expected_path for item in raised.exception.errors))

    def test_gauge_does_not_parse_numeric_display_strings(self):
        config = overlay_config()
        config["slots"]["metrics"][0]["binding"] = {"source": "literal", "value": "36.5"}
        config["presentation"] = {
            "quality_tier": "balanced",
            "metrics": {
                "style": "gauge",
                "primary_metric_id": "temperature",
                "gauge": {"min": 0, "max": 100, "clamp_visual": True},
            },
        }
        payload = resolve_overlay_interface(
            self.store.get_active_copy()["object_types"]["machine"],
            self.store.get_active_copy()["instances"]["machine_01"],
            config_override=config,
            online=True,
        )
        metric = payload["resolved_slots"]["metrics"][0]
        self.assertEqual("36.5 °C", metric["display_value"])
        self.assertNotIn("numeric_value", metric)

    def test_status_appearance_and_metric_emphasis_are_resolved(self):
        config = overlay_config("title_status_metrics")
        config["slots"]["status"] = {
            "required": True,
            "label_binding": {"source": "literal", "value": ""},
            "level_binding": {"source": "literal", "value": "normal"},
            "format": {"empty_text": ""},
            "appearance": {
                "normal": {"label": "运行中", "color": "cyan"},
            },
        }
        config["slots"]["metrics"] = [{
            "id": "temperature",
            "label": "温度",
            "required": False,
            "emphasized": True,
            "binding": {"source": "raw_state", "path": "temperature"},
            "format": {"precision": 1, "unit": "°C", "empty_text": "--"},
        }]
        self.service.save_type("machine", config, 0)
        project = self.store.get_active_copy()
        payload = resolve_overlay_interface(
            project["object_types"]["machine"],
            project["instances"]["machine_01"],
            online=True,
        )
        status = payload["resolved_slots"]["status"]
        self.assertEqual("运行中", status["display_value"])
        self.assertEqual("cyan", status["accent_token"])
        self.assertEqual("", status["detail_value"])
        self.assertTrue(payload["resolved_slots"]["metrics"][0]["emphasized"])

    def test_invalid_status_color_token_is_rejected(self):
        config = overlay_config("title_status_metrics")
        config["slots"]["status"] = {
            "required": True,
            "label_binding": {"source": "literal", "value": ""},
            "level_binding": {"source": "literal", "value": "normal"},
            "format": {"empty_text": ""},
            "appearance": {"normal": {"label": "在线", "color": "#00ff00"}},
        }
        with self.assertRaises(OverlayValidationError):
            self.service.save_type("machine", config, 0)

    def test_quality_tier_sparse_override_and_revision_resolution(self):
        type_config = overlay_config()
        type_config["presentation"] = {"quality_tier": "high"}
        saved_type = self.service.save_type("machine", type_config, 0)
        self.assertEqual(1, saved_type["revision"])

        saved_override = self.service.save_instance(
            "machine_01",
            {"presentation": {"quality_tier": "performance"}},
            0,
        )
        self.assertEqual(1, saved_override["revision"])
        self.assertEqual(
            {"presentation": {"quality_tier": "performance"}},
            saved_override["values"],
        )

        context = self.service.context(instance_id="machine_01")
        self.assertEqual("high", context["type_config"]["values"]["presentation"]["quality_tier"])
        self.assertEqual("performance", context["effective_config"]["presentation"]["quality_tier"])
        self.assertEqual("performance", context["preview"]["presentation"]["quality_tier"])
        self.assertEqual("preview-t1-i1", context["preview"]["config_revision"])

        type_config["presentation"]["quality_tier"] = "balanced"
        saved_type = self.service.save_type("machine", type_config, 1)
        self.assertEqual(2, saved_type["revision"])
        context = self.service.context(instance_id="machine_01")
        self.assertEqual("performance", context["effective_config"]["presentation"]["quality_tier"])
        self.assertEqual("preview-t2-i1", context["preview"]["config_revision"])

        cleared = self.service.clear_instance("machine_01", 1)
        self.assertEqual(2, cleared["revision"])
        context = self.service.context(instance_id="machine_01")
        self.assertEqual({}, context["instance_override"]["values"])
        self.assertEqual("balanced", context["effective_config"]["presentation"]["quality_tier"])
        self.assertEqual("preview-t2-i2", context["preview"]["config_revision"])

    def test_invalid_quality_tier_is_rejected_without_revision_change(self):
        invalid_type = overlay_config()
        invalid_type["presentation"] = {"quality_tier": "ultra"}
        with self.assertRaises(OverlayValidationError) as raised:
            self.service.save_type("machine", invalid_type, 0)
        self.assertTrue(any(
            item.get("path") == "presentation.quality_tier"
            for item in raised.exception.errors
        ))
        project = self.store.get_active_copy()
        self.assertNotIn("interface_configs", project["object_types"]["machine"])

        unsupported_trend = overlay_config()
        unsupported_trend["presentation"] = {
            "quality_tier": "balanced",
            "metrics": {"style": "trend"},
        }
        with self.assertRaises(OverlayValidationError) as raised:
            self.service.save_type("machine", unsupported_trend, 0)
        self.assertTrue(any(
            item.get("path") == "presentation.metrics.style"
            for item in raised.exception.errors
        ))

        self.service.save_type("machine", overlay_config(), 0)
        with self.assertRaises(OverlayValidationError):
            self.service.save_instance(
                "machine_01",
                {"presentation": {"quality_tier": "ultra"}},
                0,
            )
        project = self.store.get_active_copy()
        overrides = project["instances"]["machine_01"].get("render_config", {}).get(
            "interface_overrides", {}
        )
        self.assertNotIn("I3D_Overlay", overrides)

    def test_quality_tier_json_round_trip_preserves_sparse_envelopes(self):
        type_config = overlay_config()
        type_config["presentation"] = {"quality_tier": "high"}
        self.service.save_type("machine", type_config, 0)
        self.service.save_instance(
            "machine_01",
            {"presentation": {"quality_tier": "performance"}},
            0,
        )

        self.store.deactivate()
        self.assertTrue(self.store.activate("overlay_test"))
        project = self.store.get_active_copy()
        self.assertNotIn("presentation", project)
        self.assertNotIn("quality_tier", project)
        type_env = project["object_types"]["machine"]["interface_configs"]["I3D_Overlay"]
        override_env = project["instances"]["machine_01"]["render_config"][
            "interface_overrides"
        ]["I3D_Overlay"]
        self.assertEqual(1, type_env["revision"])
        self.assertEqual("high", type_env["values"]["presentation"]["quality_tier"])
        self.assertEqual(1, override_env["revision"])
        self.assertEqual(
            {"presentation": {"quality_tier": "performance"}},
            override_env["values"],
        )

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


class OverlayPostgresStorageTestCase(unittest.TestCase):
    """Exercise the same nested Overlay envelopes through PG's JSONB columns."""

    @classmethod
    def setUpClass(cls):
        if ProjectStorePG is None or pg_db is None or not pg_db.ping():
            raise unittest.SkipTest("PostgreSQL is unavailable")

    def setUp(self):
        self.project_id = f"overlay_pg_{uuid.uuid4().hex}"
        self.store = ProjectStorePG.__new__(ProjectStorePG)
        self.store._lock = threading.RLock()
        self.store._active_id = self.project_id
        self.store._dirty = False
        self.store._current = {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "id": self.project_id,
            "name": "Overlay PG Test",
            "created_at": "2026-07-23 00:00:00",
            "dataset": None,
            "object_types": {
                "machine": {
                    "rid": "machine",
                    "name": "Machine",
                    "injected_interfaces": ["I3D_Representable", "I3D_Overlay"],
                }
            },
            "instances": {
                "machine_01": {
                    "id": "machine_01",
                    "object_type_rid": "machine",
                    "object_type_name": "Machine",
                    "display_name": "Machine 01",
                    "render_config": {},
                    "created_at": time.time(),
                    "last_seen": time.time(),
                    "status": "online",
                    "raw_state": {},
                }
            },
            "components": {},
            "instance_roster": [],
            "calibration": None,
            "spatial_profile": {},
            "frames": [],
        }
        self.service = OverlayService(self.store)

    def tearDown(self):
        if pg_db is None:
            return
        with pg_db.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM project WHERE id = %s", (self.project_id,))

    def test_quality_tier_pg_round_trip_matches_json_envelope_shape(self):
        type_config = overlay_config()
        type_config["presentation"] = {"quality_tier": "high"}
        self.service.save_type("machine", type_config, 0)
        self.service.save_instance(
            "machine_01",
            {"presentation": {"quality_tier": "performance"}},
            0,
        )

        project = self.store._read_project(self.project_id)
        self.assertNotIn("presentation", project)
        self.assertNotIn("quality_tier", project)
        type_env = project["object_types"]["machine"]["interface_configs"]["I3D_Overlay"]
        override_env = project["instances"]["machine_01"]["render_config"][
            "interface_overrides"
        ]["I3D_Overlay"]
        self.assertEqual(1, type_env["revision"])
        self.assertEqual("high", type_env["values"]["presentation"]["quality_tier"])
        self.assertEqual(1, override_env["revision"])
        self.assertEqual(
            {"presentation": {"quality_tier": "performance"}},
            override_env["values"],
        )

        payload = resolve_overlay_interface(
            project["object_types"]["machine"],
            project["instances"]["machine_01"],
            online=True,
        )
        self.assertEqual("t1-i1", payload["config_revision"])
        self.assertEqual("performance", payload["presentation"]["quality_tier"])


if __name__ == "__main__":
    unittest.main()
