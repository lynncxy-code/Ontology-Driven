import copy
import os
import sys
import tempfile
import unittest
from unittest import mock


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

import app as app_module  # noqa: E402
from project_store import ProjectMismatch, ProjectStore  # noqa: E402


class BindingAutoNumberTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            os.path.join(self.temp.name, "projects"),
            os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project(
            "测试厂",
            object_types={"PE16A": {"rid": "PE16A", "name": "溶铜槽"}},
            project_id="p_test",
        )
        self._add_components({
            "c1": {
                "id": "c1", "object_type_rid": "PE16A", "type_name": "溶铜槽",
                "bound_instance_id": "DW-001", "ue_xy": [0, 0], "render_config": {},
            },
            "c2": {
                "id": "c2", "object_type_rid": "PE16A", "type_name": "溶铜槽",
                "bound_instance_id": "DW-002", "ue_xy": [1, 1], "render_config": {},
            },
        })
        self.store_patch = mock.patch.object(app_module, "project_store", self.store)
        self.instance_store_patch = mock.patch.object(app_module, "instance_store", self.store)
        self.store_patch.start()
        self.instance_store_patch.start()
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def tearDown(self):
        self.instance_store_patch.stop()
        self.store_patch.stop()
        self.temp.cleanup()

    def _add_components(self, components):
        def update(project):
            project.setdefault("components", {}).update(components)

        self.store.transact_active(update)

    def test_preview_is_stable_and_read_only(self):
        self._add_components({
            "c_source_b": {
                "id": "c_source_b", "object_type_rid": "PE16A", "type_name": "溶铜槽",
                "source_label": "b.dxf", "floor": 1, "source_xy": [1, 1],
                "bound_instance_id": None,
            },
            "c_source_a": {
                "id": "c_source_a", "object_type_rid": "PE16A", "type_name": "溶铜槽",
                "source_label": "a.dxf", "floor": 1, "source_xy": [9, 9],
                "bound_instance_id": None,
            },
        })
        before = copy.deepcopy(self.store.get_active())

        result = self.store.auto_number_bind(dry_run=True)

        self.assertEqual(2, result["count"])
        self.assertEqual((1, 2), (result["start"], result["end"]))
        self.assertEqual(
            ["c_source_a", "c_source_b"],
            [item["component_id"] for item in result["pairs"]],
        )
        self.assertEqual(
            ["AUTO-0001", "AUTO-0002"],
            [item["instance_id"] for item in result["pairs"]],
        )
        self.assertEqual(before, self.store.get_active())

    def test_continues_after_highest_id_across_all_collections(self):
        self.store.add_roster_entries([{"instance_id": "auto-0001", "source": "manual"}])
        self.store.spawn("AUTO-0003", "PE16A")
        self._add_components({
            "c_bound_auto": {
                "id": "c_bound_auto", "object_type_rid": "PE16A", "type_name": "溶铜槽",
                "bound_instance_id": "AUTO-0004",
            },
            "c_new": {
                "id": "c_new", "object_type_rid": "PE16A", "type_name": "溶铜槽",
                "bound_instance_id": None,
            },
        })

        result = self.store.auto_number_bind(component_ids=["c_new"], dry_run=True)

        self.assertEqual(5, result["start"])
        self.assertEqual("AUTO-0005", result["pairs"][0]["instance_id"])

    def test_commit_writes_roster_and_binding_once_without_minting(self):
        self._add_components({
            "c_new": {
                "id": "c_new", "object_type_rid": "PE16A", "type_name": "溶铜槽",
                "source_label": "factory.dxf", "source_xy": [10, 20],
                "bound_instance_id": None,
            },
        })
        before_instances = copy.deepcopy(self.store.get_active()["instances"])

        with mock.patch.object(
            self.store, "_save_current", wraps=self.store._save_current
        ) as save_current:
            result = self.store.auto_number_bind(
                component_ids=["c_new"], dry_run=False, expected_project_id="p_test"
            )

        self.assertEqual(1, save_current.call_count)
        self.assertEqual("AUTO-0001", result["pairs"][0]["instance_id"])
        self.assertEqual("AUTO-0001", self.store.get_components()["c_new"]["bound_instance_id"])
        entry = next(item for item in self.store.get_roster() if item["instance_id"] == "AUTO-0001")
        self.assertEqual("auto", entry["source"])
        self.assertEqual("溶铜槽", entry["type"])
        self.assertEqual(before_instances, self.store.get_active()["instances"])

    def test_rejects_stale_bound_component_without_partial_write(self):
        self._add_components({
            "c_new": {
                "id": "c_new", "object_type_rid": "PE16A", "type_name": "溶铜槽",
                "bound_instance_id": None,
            },
        })
        before = copy.deepcopy(self.store.get_active())

        with self.assertRaisesRegex(ValueError, "已绑定"):
            self.store.auto_number_bind(component_ids=["c_new", "c1"], dry_run=False)

        self.assertEqual(before, self.store.get_active())

    def test_expected_project_mismatch_is_zero_write(self):
        self._add_components({
            "c_new": {
                "id": "c_new", "object_type_rid": "PE16A", "type_name": "溶铜槽",
                "bound_instance_id": None,
            },
        })
        before = copy.deepcopy(self.store.get_active())

        with self.assertRaises(ProjectMismatch):
            self.store.auto_number_bind(
                component_ids=["c_new"], dry_run=False,
                expected_project_id="another_project",
            )

        self.assertEqual(before, self.store.get_active())

    def test_api_preview_then_commit(self):
        self._add_components({
            "c_api": {
                "id": "c_api", "object_type_rid": "PE16A", "type_name": "溶铜槽",
                "bound_instance_id": None,
            },
        })
        body = {
            "prefix": "pump",
            "width": 3,
            "component_ids": ["c_api"],
            "expected_project_id": "p_test",
        }

        preview = self.client.post(
            "/api/v2/binding/auto-number", json={**body, "dry_run": True}
        )
        self.assertEqual(200, preview.status_code, preview.get_json())
        self.assertEqual("preview", preview.get_json()["status"])
        self.assertEqual("PUMP-001", preview.get_json()["pairs"][0]["instance_id"])
        self.assertIsNone(self.store.get_components()["c_api"]["bound_instance_id"])

        commit = self.client.post(
            "/api/v2/binding/auto-number", json={**body, "dry_run": False}
        )
        self.assertEqual(200, commit.status_code, commit.get_json())
        self.assertEqual("ok", commit.get_json()["status"])
        self.assertEqual("PUMP-001", self.store.get_components()["c_api"]["bound_instance_id"])

    def test_api_rejects_invalid_rules(self):
        cases = [
            {"prefix": "中文", "width": 4, "component_ids": ["c1"], "dry_run": True},
            {"prefix": "AUTO", "width": 1, "component_ids": ["c1"], "dry_run": True},
            {"prefix": "AUTO", "width": 4, "component_ids": ["c1"], "dry_run": "true"},
            {"prefix": "AUTO", "width": 4, "dry_run": True},
            {"prefix": "AUTO", "width": 4, "component_ids": [], "dry_run": True},
        ]
        for body in cases:
            with self.subTest(body=body):
                response = self.client.post("/api/v2/binding/auto-number", json=body)
                self.assertEqual(400, response.status_code, response.get_json())

    def test_api_project_mismatch_returns_409(self):
        self._add_components({
            "c_api": {
                "id": "c_api", "object_type_rid": "PE16A", "type_name": "溶铜槽",
                "bound_instance_id": None,
            },
        })
        before = copy.deepcopy(self.store.get_active())

        response = self.client.post("/api/v2/binding/auto-number", json={
            "component_ids": ["c_api"],
            "dry_run": False,
            "expected_project_id": "stale_project",
        })

        self.assertEqual(409, response.status_code, response.get_json())
        self.assertEqual("project changed", response.get_json()["error"])
        self.assertEqual(before, self.store.get_active())


if __name__ == "__main__":
    unittest.main()
