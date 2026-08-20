import copy
import os
import tempfile
import unittest


os.environ["ONTOTWIN_STORE"] = "json"

import app as app_module
from project_store import ProjectStore


class FloorProfileServiceTestCase(unittest.TestCase):
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

        def seed(working):
            working["components"] = {
                "c1": {
                    "id": "c1",
                    "object_type_rid": "PE16A",
                    "type_name": "溶铜槽",
                    "bound_instance_id": "DW-001",
                    "floor": 1,
                    "canonical_xy": [0.0, 0.0],
                    "canonical_z": 25.0,
                    "ue_xy": [0.0, 0.0],
                    "ue_z": 2.5,
                    "render_config": {},
                },
                "c2": {
                    "id": "c2",
                    "object_type_rid": "PE16A",
                    "type_name": "溶铜槽",
                    "bound_instance_id": "DW-002",
                    "floor": 1,
                    "canonical_xy": [10.0, 10.0],
                    "canonical_z": 0.0,
                    "ue_xy": [1.0, 1.0],
                    "ue_z": 0.0,
                    "render_config": {},
                },
            }

        self.store.transact_active(seed)
        self.store.mint_instances()
        self.previous_project_store = app_module.project_store
        self.previous_instance_store = app_module.instance_store
        app_module.project_store = self.store
        app_module.instance_store = self.store
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def tearDown(self):
        app_module.project_store = self.previous_project_store
        app_module.instance_store = self.previous_instance_store
        self.temp.cleanup()

    def test_floor_list_returns_scale_derived_height_and_usage(self):
        response = self.client.get("/api/v2/spatial/floors")

        self.assertEqual(200, response.status_code, response.get_json())
        payload = response.get_json()
        self.assertEqual("p_test", payload["project_id"])
        self.assertEqual(0.1, payload["scale_to_cm"])
        floor = payload["floors"][0]
        self.assertEqual(1, floor["floor"])
        self.assertEqual(0.0, floor["default_component_ue_z_cm"])
        self.assertEqual(2, floor["usage"]["components"])
        self.assertEqual(2, floor["usage"]["bound_instances"])

    def test_floor_base_change_rebases_components_and_bound_instances(self):
        response = self.client.put(
            "/api/v2/spatial/floors/1",
            json={
                "expected_project_id": "p_test",
                "z_base_mm": 4500,
                "ue_ground_z_cm": None,
            },
        )

        self.assertEqual(200, response.status_code, response.get_json())
        payload = response.get_json()
        self.assertTrue(payload["changed"]["z_base_mm"])
        self.assertEqual({"components": 2, "bound_instances": 2}, payload["affected"])
        project = self.store.get_active_copy()
        self.assertEqual(4525.0, project["components"]["c1"]["canonical_z"])
        self.assertEqual(452.5, project["components"]["c1"]["ue_z"])
        self.assertEqual(4500.0, project["components"]["c2"]["canonical_z"])
        self.assertEqual(450.0, project["components"]["c2"]["ue_z"])
        self.assertEqual(452.5, project["instances"]["DW-001"]["raw_state"]["translation_z"])
        self.assertEqual(450.0, project["instances"]["DW-002"]["raw_state"]["translation_z"])

    def test_ground_only_change_does_not_move_components(self):
        before = copy.deepcopy(self.store.get_active_copy()["components"])

        response = self.client.put(
            "/api/v2/spatial/floors/1",
            json={
                "expected_project_id": "p_test",
                "z_base_mm": 0,
                "ue_ground_z_cm": 20,
            },
        )

        self.assertEqual(200, response.status_code, response.get_json())
        payload = response.get_json()
        self.assertEqual(
            {"z_base_mm": False, "ue_ground_z_cm": True}, payload["changed"]
        )
        self.assertEqual({"components": 0, "bound_instances": 0}, payload["affected"])
        self.assertEqual(before, self.store.get_active_copy()["components"])
        self.assertEqual(
            20.0, self.store.get_spatial_profile()["floor_table"][0]["ue_ground_z_cm"]
        )

    def test_new_floor_uses_zero_as_old_base_and_preserves_component_offset(self):
        def update(working):
            working["components"]["c1"].update({
                "floor": 2,
                "canonical_z": 25.0,
                "ue_z": 2.5,
            })

        self.store.transact_active(update)

        response = self.client.put(
            "/api/v2/spatial/floors/2",
            json={"expected_project_id": "p_test", "z_base_mm": 4500},
        )

        self.assertEqual(200, response.status_code, response.get_json())
        component = self.store.get_active_copy()["components"]["c1"]
        self.assertEqual(4525.0, component["canonical_z"])
        self.assertEqual(452.5, component["ue_z"])

    def test_floor_update_rejects_project_switch_without_mutation(self):
        before = copy.deepcopy(self.store.get_active_copy())

        response = self.client.put(
            "/api/v2/spatial/floors/1",
            json={"expected_project_id": "other-project", "z_base_mm": 4500},
        )

        self.assertEqual(409, response.status_code)
        self.assertEqual(before, self.store.get_active_copy())

    def test_floor_update_rejects_non_numeric_height(self):
        response = self.client.put(
            "/api/v2/spatial/floors/1",
            json={"expected_project_id": "p_test", "z_base_mm": "4500"},
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual("height_invalid", response.get_json()["error"])

    def test_profile_display_only_update_does_not_move_components(self):
        before = copy.deepcopy(self.store.get_active_copy()["components"])

        response = self.client.put(
            "/api/v2/spatial/profile",
            json={
                "expected_project_id": "p_test",
                "ue_transform": {"display": {"rotation_deg": 90, "flip": False}},
            },
        )

        self.assertEqual(200, response.status_code, response.get_json())
        self.assertEqual(
            {"components": 0, "bound_instances": 0}, response.get_json()["affected"]
        )
        self.assertEqual(before, self.store.get_active_copy()["components"])

    def test_mint_uses_component_ue_z_instead_of_floor_base(self):
        def update(working):
            working["instances"].pop("DW-001", None)
            working["components"]["c1"].update({
                "canonical_z": 125.0,
                "ue_z": 12.5,
            })

        self.store.transact_active(update)
        self.store.mint_instances()

        instance = self.store.get_active_copy()["instances"]["DW-001"]
        self.assertEqual(12.5, instance["raw_state"]["translation_z"])


if __name__ == "__main__":
    unittest.main()
