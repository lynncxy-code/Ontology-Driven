import os
import sys
import tempfile
import unittest

from flask import Flask


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from project_store import ProjectStore
from zone_management import register_zone_management_routes
from zone_management.service import ZoneManagementService


class ZoneManagementTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project(
            "Zone Test",
            project_id="zone_test",
            object_types={"machine": {"rid": "machine", "name": "设备"}},
        )
        self.store.spawn("machine_01", "machine", {"x": 1, "y": 2, "z": 3})
        self.store.spawn("machine_02", "machine", {"x": 4, "y": 5, "z": 6})
        self.service = ZoneManagementService(self.store)
        app = Flask(__name__)
        register_zone_management_routes(app, self.store)
        self.client = app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_assign_and_unassign_zone_without_touching_state(self):
        before = self.store.get_active_copy()["instances"]["machine_01"]
        result = self.service.assign({
            "instance_ids": ["machine_01", "machine_02"],
            "zone_id": "plant/F02",
            "expected_project_id": "zone_test",
        })
        self.assertEqual(2, result["updated_count"])
        self.assertEqual("plant/F02", self.store.get_active_copy()["instances"]["machine_01"]["zone_id"])
        after = self.store.get_active_copy()["instances"]["machine_01"]
        self.assertEqual(before["raw_state"], after["raw_state"])
        self.assertEqual(before["render_config"], after["render_config"])

        cleared = self.service.assign({"instance_ids": ["machine_01"], "zone_id": None})
        self.assertEqual(1, cleared["updated_count"])
        self.assertNotIn("zone_id", self.store.get_active_copy()["instances"]["machine_01"])

    def test_summary_and_instance_list_include_zone(self):
        self.service.assign({"instance_ids": ["machine_01"], "zone_id": "plant/F01"})
        summary = self.service.summary()
        self.assertEqual([{
            "id": "plant/F01",
            "name": "plant/F01",
            "parent_zone_id": None,
            "level": "custom",
            "ue_level": "",
            "streaming": {},
            "instance_count": 1,
            "registered": False,
        }], summary["zones"])
        self.assertEqual(1, summary["unassigned_count"])
        listed = {item["id"]: item for item in self.store.list_all()}
        self.assertEqual("plant/F01", listed["machine_01"]["zone_id"])
        self.assertIsNone(listed["machine_02"]["zone_id"])

    def test_assignment_reports_missing_and_unchanged(self):
        self.service.assign({"instance_ids": ["machine_01"], "zone_id": "plant/F01"})
        result = self.service.assign({
            "instance_ids": ["machine_01", "missing"],
            "zone_id": "plant/F01",
        })
        self.assertEqual([], result["updated"])
        self.assertEqual(["machine_01"], result["unchanged"])
        self.assertEqual(["missing"], result["missing"])

    def test_api_rejects_invalid_request_and_project_switch(self):
        invalid = self.client.put("/api/v2/zones/assignments", json={"instance_ids": []})
        self.assertEqual(422, invalid.status_code)
        conflict = self.client.put("/api/v2/zones/assignments", json={
            "instance_ids": ["machine_01"],
            "zone_id": "plant/F01",
            "expected_project_id": "other_project",
        })
        self.assertEqual(409, conflict.status_code)

    def test_api_assigns_zone_and_lists_summary(self):
        assigned = self.client.put("/api/v2/zones/assignments", json={
            "instance_ids": ["machine_01"],
            "zone_id": "plant/F01",
            "expected_project_id": "zone_test",
        })
        self.assertEqual(200, assigned.status_code)
        self.assertEqual(1, assigned.get_json()["updated_count"])
        summary = self.client.get("/api/v2/zones")
        self.assertEqual(200, summary.status_code)
        self.assertEqual("plant/F01", summary.get_json()["zones"][0]["id"])

    def test_catalog_summary_marks_registered_and_preserves_metadata(self):
        saved = self.client.put("/api/v2/zones/catalog", json={
            "expected_project_id": "zone_test",
            "zones": [
                {
                    "zone_id": "zone_test_building",
                    "name": "测试楼栋",
                    "level": "building",
                    "parent_zone_id": None,
                    "ue_level": "/Game/Maps/Test",
                },
                {
                    "zone_id": "zone_test_floor_01",
                    "name": "一层",
                    "level": "floor",
                    "parent_zone_id": "zone_test_building",
                },
            ],
        })
        self.assertEqual(200, saved.status_code)
        summary = self.client.get("/api/v2/zones").get_json()
        floor = next(zone for zone in summary["zones"] if zone["id"] == "zone_test_floor_01")
        self.assertTrue(floor["registered"])
        self.assertEqual("一层", floor["name"])
        self.assertEqual("zone_test_building", floor["parent_zone_id"])

    def test_catalog_rejects_non_stable_zone_id_but_assignment_remains_compatible(self):
        invalid = self.client.put("/api/v2/zones/catalog", json={
            "zones": [{"zone_id": "能源区", "name": "能源区", "level": "area"}],
        })
        self.assertEqual(422, invalid.status_code)
        self.assertEqual("invalid_zone_id", invalid.get_json()["error"])

        assigned = self.client.put("/api/v2/zones/assignments", json={
            "instance_ids": ["machine_01"],
            "zone_id": "能源区",
        })
        self.assertEqual(200, assigned.status_code)


if __name__ == "__main__":
    unittest.main()
