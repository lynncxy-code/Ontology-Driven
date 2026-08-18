import os
import sys
import tempfile
import unittest

from flask import Flask


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from project_store import CURRENT_SCHEMA_VERSION, ProjectStore
from web_interaction import register_web_interaction_routes
from web_interaction.resolver import resolve_binding
from web_interaction.service import WebInteractionService
from web_interaction.validators import business_view_members, validate_config


def sample_config():
    return {
        "pages": [{
            "page_id": "page.s3", "name": "S3 楼宇", "enabled": True,
            "base_url": "http://localhost:5000/ue_hud/pages/s3-building.html",
            "param_mapping": {"zone_id": "space_id", "instance_id": "instance_id", "trigger": "trigger"},
            "declared_extra_params": ["event_id"],
            "scope_effects": {"zone": "web_and_scene", "business_view": "web_and_scene", "instance": "web_and_scene"},
        }],
        "business_views": [{
            "business_view_id": "bv.fire", "name": "消防", "enabled": True,
            "rule_groups": [{"zone_ids": ["building"], "object_type_rids": ["smoke"]}],
            "exclude_instance_ids": ["smoke_02"],
        }],
        "bindings": [
            {"binding_id": "bind.project", "name": "默认", "enabled": True, "trigger": "open_detail", "activation_mode": "explicit", "effect": "open_web", "scope": {}, "page_id": "page.s3"},
            {"binding_id": "bind.zone", "name": "楼层", "enabled": True, "trigger": "open_detail", "activation_mode": "explicit", "effect": "open_web", "scope": {"zone_id": "floor.5"}, "page_id": "page.s3"},
            {"binding_id": "bind.instance", "name": "实例", "enabled": True, "trigger": "open_detail", "activation_mode": "explicit", "effect": "open_web", "scope": {"instance_id": "smoke_01"}, "page_id": "page.s3"},
            {"binding_id": "bind.fire", "name": "消防", "enabled": True, "trigger": "business_view_activated", "activation_mode": "direct", "effect": "open_web", "scope": {"business_view_id": "bv.fire"}, "page_id": "page.s3"},
        ],
        "web_policy": {"allowed_hosts": ["localhost"]},
    }


class WebInteractionTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project(
            "Web 3.8", project_id="web_test",
            object_types={"smoke": {"rid": "smoke", "name": "烟感"}, "pump": {"rid": "pump", "name": "泵"}},
        )
        self.store.spawn("smoke_01", "smoke")
        self.store.spawn("smoke_02", "smoke")
        self.store.spawn("pump_01", "pump")
        self.store.spawn("always_on", "pump")
        self.store.assign_zone(["smoke_01", "smoke_02"], "floor.5")
        self.store.assign_zone(["pump_01"], "floor.6")

        def add_zones(project):
            project["zones"] = {
                "building": {"zone_id": "building", "name": "整栋楼", "parent_zone_id": None, "level": "building"},
                "floor.5": {"zone_id": "floor.5", "name": "5F", "parent_zone_id": "building", "level": "floor"},
                "floor.6": {"zone_id": "floor.6", "name": "6F", "parent_zone_id": "building", "level": "floor"},
            }
        self.store.transact_active(add_zones)
        self.service = WebInteractionService(self.store)
        app = Flask(__name__)
        register_web_interaction_routes(app, self.store)
        self.client = app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_project_schema_defaults_are_compatible(self):
        project = self.store.get_active_copy()
        self.assertEqual(CURRENT_SCHEMA_VERSION, project["schema_version"])
        self.assertEqual(0, project["web_interactions"]["revision"])
        self.assertEqual([], project["web_interactions"]["published"]["pages"])

    def test_validation_and_business_view_parent_zone_aggregation(self):
        result = validate_config(self.store.get_active_copy(), sample_config())
        self.assertTrue(result["valid"], result["errors"])
        view = sample_config()["business_views"][0]
        self.assertEqual({"smoke_01"}, business_view_members(self.store.get_active_copy(), view))
        self.assertTrue(any(item["code"] == "unzoned_instances" for item in result["warnings"]))

    def test_resolver_precedence_url_and_scene_scope(self):
        project = self.store.get_active_copy()
        result = resolve_binding(project, sample_config(), {
            "trigger": "open_detail", "context": {"instance_id": "smoke_01"},
            "extra_params": {"event_id": "evt-9"},
        })
        self.assertEqual("bind.instance", result["binding"]["binding_id"])
        self.assertIn("instance_id=smoke_01", result["final_url"])
        self.assertIn("event_id=evt-9", result["final_url"])
        self.assertEqual(["always_on", "smoke_01"], result["scene_scope"]["visible_instance_ids"])

        config = sample_config()
        config["bindings"][2]["enabled"] = False
        fallback = resolve_binding(project, config, {"trigger": "open_detail", "context": {"instance_id": "smoke_01"}})
        self.assertEqual("bind.zone", fallback["binding"]["binding_id"])

        config["bindings"].insert(2, {"binding_id": "block.smoke", "enabled": True, "trigger": "open_detail", "activation_mode": "explicit", "effect": "block", "scope": {"instance_id": "smoke_01"}})
        blocked = resolve_binding(project, config, {"trigger": "open_detail", "context": {"instance_id": "smoke_01"}})
        self.assertTrue(blocked["blocked"])

    def test_business_view_zone_intersection_and_zero_match_do_not_fallback(self):
        project = self.store.get_active_copy()
        result = resolve_binding(project, sample_config(), {
            "trigger": "business_view_activated",
            "context": {"business_view_id": "bv.fire", "zone_id": "floor.6"},
        })
        self.assertEqual("bind.fire", result["binding"]["binding_id"])
        self.assertEqual(0, result["scene_scope"]["matched_instance_count"])
        self.assertEqual(["always_on"], result["scene_scope"]["visible_instance_ids"])

    def test_dangerous_url_zone_cycle_and_non_leaf_binding_are_hard_errors(self):
        config = sample_config()
        config["pages"][0]["base_url"] = "javascript:alert(1)"
        project = self.store.get_active_copy()
        project["zones"]["building"]["parent_zone_id"] = "floor.5"
        project["instances"]["smoke_01"]["zone_id"] = "building"
        result = validate_config(project, config)
        codes = {item["code"] for item in result["errors"]}
        self.assertIn("dangerous_url_scheme", codes)
        self.assertIn("zone_cycle", codes)
        self.assertIn("instance_bound_to_non_leaf_zone", codes)

    def test_draft_publish_runtime_and_rollback_revision(self):
        saved = self.service.save_draft({"expected_revision": 0, "draft": sample_config()})
        self.assertEqual(0, saved["revision"])
        self.assertEqual([], self.service.runtime()["config"]["pages"])

        needs_confirmation = self.service.publish({"expected_revision": 0})
        self.assertEqual("warning_confirmation_required", needs_confirmation["status"])
        published = self.service.publish({"expected_revision": 0, "confirm_warnings": True})
        self.assertEqual(1, published["revision"])
        self.assertEqual("page.s3", self.service.runtime()["config"]["pages"][0]["page_id"])
        self.assertEqual("unchanged", self.service.runtime(1)["status"])

        changed = sample_config()
        changed["pages"][0]["name"] = "S3 新版"
        self.service.save_draft({"expected_revision": 1, "draft": changed})
        self.service.publish({"expected_revision": 1, "confirm_warnings": True})
        rolled = self.service.rollback({"expected_revision": 2})
        self.assertEqual(3, rolled["revision"])
        self.assertEqual("S3 楼宇", self.service.runtime()["config"]["pages"][0]["name"])

    def test_api_contract(self):
        saved = self.client.put("/api/v2/web-interactions/draft", json={"expected_revision": 0, "draft": sample_config()})
        self.assertEqual(200, saved.status_code)
        preview = self.client.post("/api/v2/web-interactions/resolve-preview", json={
            "trigger": "open_detail", "context": {"instance_id": "smoke_01"},
        })
        self.assertEqual("bind.instance", preview.get_json()["result"]["binding"]["binding_id"])
        conflict = self.client.put("/api/v2/web-interactions/draft", json={"expected_revision": 9, "draft": sample_config()})
        self.assertEqual(409, conflict.status_code)

    def test_single_page_apply_is_atomic_and_scene_behavior_is_preserved(self):
        config = sample_config()
        config["business_views"][0]["scene_behavior"] = "highlight"
        needs_confirmation = self.service.apply({"expected_revision": 0, "config": config})
        self.assertEqual("warning_confirmation_required", needs_confirmation["status"])
        applied = self.service.apply({
            "expected_revision": 0, "config": config, "confirm_warnings": True,
        })
        self.assertEqual(1, applied["revision"])
        self.assertEqual("highlight", self.service.get()["published"]["business_views"][0]["scene_behavior"])
        resolved = resolve_binding(self.store.get_active_copy(), applied["config"], {
            "trigger": "business_view_activated", "context": {"business_view_id": "bv.fire"},
        })
        self.assertEqual("highlight", resolved["scene_behavior"])
        self.assertEqual(["smoke_01"], resolved["scene_scope"]["matched_instance_ids"])


if __name__ == "__main__":
    unittest.main()
