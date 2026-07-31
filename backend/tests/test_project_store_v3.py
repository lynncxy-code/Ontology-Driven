import json
import os
import sys
import tempfile
import unittest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.environ["ONTOTWIN_STORE"] = "json"

from project_store import CURRENT_SCHEMA_VERSION, ProjectStore, UnsupportedProjectSchemaError


class ProjectStoreSchemaTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.projects_dir = os.path.join(self.temp.name, "projects")
        self.active_file = os.path.join(self.temp.name, "active.json")
        self.store = ProjectStore(self.projects_dir, self.active_file)

    def tearDown(self):
        self.temp.cleanup()

    def _write_project(self, project_id, payload):
        os.makedirs(self.projects_dir, exist_ok=True)
        path = os.path.join(self.projects_dir, f"{project_id}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        return path

    def test_new_project_has_disabled_scene_interactions(self):
        self.store.create_project("Scene Test", project_id="scene_test")
        project = self.store.get_active_copy()
        self.assertEqual(CURRENT_SCHEMA_VERSION, project["schema_version"])
        self.assertEqual({
            "revision": 0,
            "roaming": {"enabled": False, "auto_enter": False},
            "routes": [],
        }, project["scene_interactions"])
        self.assertEqual({
            "revision": 0,
            "mode": "inherit_platform",
            "allowed_hosts": [],
            "http_exceptions": [],
        }, project["media_policy"])

    def test_v2_project_migrates_without_inventing_resources(self):
        path = self._write_project("v2_project", {
            "schema_version": 2,
            "id": "v2_project",
            "name": "V2",
            "object_types": {},
            "instances": {},
        })
        self.assertTrue(self.store.activate("v2_project"))
        project = self.store.get_active_copy()
        self.assertEqual(CURRENT_SCHEMA_VERSION, project["schema_version"])
        self.assertEqual({"enabled": False, "auto_enter": False}, project["scene_interactions"]["roaming"])
        self.assertEqual([], project["scene_interactions"]["routes"])
        self.assertNotIn("character_id", project["scene_interactions"]["roaming"])
        with open(path, "r", encoding="utf-8") as handle:
            persisted = json.load(handle)
        self.assertEqual(2, persisted["schema_version"])

        # Loading is read-safe: migration lands only on the next ordinary save.
        self.store.set_scene_interactions(project["scene_interactions"])
        with open(path, "r", encoding="utf-8") as handle:
            persisted = json.load(handle)
        self.assertEqual(CURRENT_SCHEMA_VERSION, persisted["schema_version"])

    def test_v3_project_adds_empty_routes_and_unconfirmed_ground_height(self):
        path = self._write_project("v3_project", {
            "schema_version": 3,
            "id": "v3_project",
            "name": "V3",
            "object_types": {},
            "instances": {},
            "scene_interactions": {
                "revision": 2,
                "roaming": {"enabled": False, "auto_enter": False},
            },
            "spatial_profile": {
                "unit": "mm",
                "ue_transform": {"scale_to_cm": 0.1},
                "floor_table": [{"floor": 1, "z_base_mm": 0.0}],
            },
        })
        self.assertTrue(self.store.activate("v3_project"))
        project = self.store.get_active_copy()
        self.assertEqual(CURRENT_SCHEMA_VERSION, project["schema_version"])
        self.assertEqual([], project["scene_interactions"]["routes"])
        floor = project["spatial_profile"]["floor_table"][0]
        self.assertEqual("floor-1", floor["floor_id"])
        self.assertIsNone(floor["ue_ground_z_cm"])
        with open(path, "r", encoding="utf-8") as handle:
            self.assertEqual(3, json.load(handle)["schema_version"])

    def test_v4_project_adds_inherited_media_policy(self):
        path = self._write_project("v4_project", {
            "schema_version": 4,
            "id": "v4_project",
            "name": "V4",
            "object_types": {},
            "instances": {},
            "scene_interactions": {
                "revision": 0,
                "roaming": {"enabled": False, "auto_enter": False},
                "routes": [],
            },
        })
        self.assertTrue(self.store.activate("v4_project"))
        project = self.store.get_active_copy()
        self.assertEqual(CURRENT_SCHEMA_VERSION, project["schema_version"])
        self.assertEqual("inherit_platform", project["media_policy"]["mode"])
        self.assertEqual([], project["media_policy"]["allowed_hosts"])
        with open(path, "r", encoding="utf-8") as handle:
            self.assertEqual(4, json.load(handle)["schema_version"])

    def test_scene_interactions_round_trip(self):
        self.store.create_project("Round Trip", project_id="round_trip")
        config = {
            "revision": 4,
            "roaming": {
                "enabled": True,
                "auto_enter": False,
                "character_id": "character.observer.base",
            },
        }
        self.store.set_scene_interactions(config)
        self.assertEqual(config, self.store.get_scene_interactions())

        self.store.deactivate()
        self.assertTrue(self.store.activate("round_trip"))
        self.assertEqual(config, self.store.get_scene_interactions())

    def test_get_returns_detached_copy(self):
        self.store.create_project("Detached", project_id="detached")
        scene = self.store.get_scene_interactions()
        scene["revision"] = 999
        self.assertEqual(0, self.store.get_scene_interactions()["revision"])

    def test_all_datasets_excludes_project_metadata_and_normalizes_graph_entries(self):
        self.store.create_project(
            "Binding Only",
            project_id="binding_only",
            dataset={
                "id": "binding_only",
                "name": "Binding Only",
                "bound_ue_project_id": "ue_binding_only",
            },
        )
        self.store.create_project(
            "Graph Project",
            project_id="graph_project",
            dataset={
                "id": "graph_project",
                "graph_data": {
                    "nodes": [{"id": "node_1"}],
                    "links": [],
                    "categories": [],
                },
            },
        )

        datasets = self.store.all_datasets()

        self.assertEqual(1, len(datasets))
        self.assertEqual("graph_project", datasets[0]["id"])
        self.assertEqual("Graph Project", datasets[0]["name"])
        self.assertTrue(datasets[0]["created_at"])
        self.assertEqual(1, datasets[0]["node_count"])
        self.assertEqual(0, datasets[0]["link_count"])

    def test_remove_component_preserves_minted_instance(self):
        self.store.create_project(
            "Component Delete",
            object_types={"test.rotor": {"rid": "test.rotor", "name": "旋翼航空器"}},
            project_id="component_delete",
        )
        self.store.set_components({
            "cmp_test": {
                "id": "cmp_test",
                "object_type_rid": "test.rotor",
                "bound_instance_id": "vehicle_01",
            }
        })
        self.store.spawn("vehicle_01", "test.rotor")

        removed = self.store.remove_component("cmp_test")

        self.assertEqual("vehicle_01", removed["bound_instance_id"])
        self.assertEqual({}, self.store.get_components())
        self.assertEqual(["vehicle_01"], [item["id"] for item in self.store.list_all()])
        self.assertIsNone(self.store.remove_component("cmp_test"))

    def test_newer_schema_is_rejected_without_writeback(self):
        path = self._write_project("future", {
            "schema_version": CURRENT_SCHEMA_VERSION + 1,
            "id": "future",
            "name": "Future",
            "future_field": {"keep": True},
        })
        with self.assertRaises(UnsupportedProjectSchemaError):
            self.store.activate("future")
        with open(path, "r", encoding="utf-8") as handle:
            persisted = json.load(handle)
        self.assertEqual(CURRENT_SCHEMA_VERSION + 1, persisted["schema_version"])
        self.assertEqual({"keep": True}, persisted["future_field"])


if __name__ == "__main__":
    unittest.main()
