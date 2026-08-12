import copy
import os
import sys
import tempfile
import unittest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from material_writeback import apply_material_writeback
from project_store import ProjectMismatch, ProjectStore


def render_config(signature, material_a, material_b="/Game/Materials/M_B.M_B"):
    return {
        "render_mode": "assembly_v1",
        "assembly_signature": signature,
        "render_parts": [
            {
                "part_index": 0,
                "asset_path": "/Game/Meshes/SM_A.SM_A",
                "source_actor_guid": "guid-a",
                "source_component_name": "MeshA",
                "material_paths": [material_a],
            },
            {
                "part_index": 1,
                "asset_path": "/Game/Meshes/SM_B.SM_B",
                "source_actor_guid": "guid-b",
                "source_component_name": "MeshB",
                "material_paths": [material_b],
            },
        ],
    }


def part_change(
    index,
    asset,
    guid,
    component,
    expected,
    desired,
):
    return {
        "part_index": index,
        "asset_path": asset,
        "source_actor_guid": guid,
        "source_component_name": component,
        "expected_material_paths": [expected],
        "material_paths": [desired],
    }


class MaterialWritebackTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.projects_dir = os.path.join(self.temp.name, "projects")
        self.active_file = os.path.join(self.temp.name, "active.json")
        self.store = ProjectStore(self.projects_dir, self.active_file)
        self.store.create_project(
            "Material writeback",
            project_id="material_project",
            object_types={"ot:test": {"name": "Test Device"}},
        )
        self.old_a = "/Game/Materials/M_OldA.M_OldA"
        self.old_b = "/Game/Materials/M_OldB.M_OldB"
        self.new_a = "/Game/Materials/M_NewA.M_NewA"
        self.new_b = "/Game/Materials/M_NewB.M_NewB"
        self.store.spawn(
            "a", "ot:test", render_config=render_config("sig-a", self.old_a)
        )
        self.store.spawn(
            "b", "ot:test", render_config=render_config("sig-b", self.old_b)
        )

        def attach_components(project):
            for instance_id in ("a", "b"):
                component_id = f"component-{instance_id}"
                instance = project["instances"][instance_id]
                instance["component_id"] = component_id
                project.setdefault("components", {})[component_id] = {
                    "id": component_id,
                    "render_config": copy.deepcopy(instance["render_config"]),
                }

        self.store.transact_active(attach_components)

    def tearDown(self):
        self.temp.cleanup()

    def change_a(self):
        return {
            "instance_id": "a",
            "expected_assembly_signature": "sig-a",
            "parts": [
                part_change(
                    0,
                    "/Game/Meshes/SM_A.SM_A",
                    "guid-a",
                    "MeshA",
                    self.old_a,
                    self.new_a,
                )
            ],
        }

    def change_b(self, expected=None):
        return {
            "instance_id": "b",
            "expected_assembly_signature": "sig-b",
            "parts": [
                part_change(
                    0,
                    "/Game/Meshes/SM_A.SM_A",
                    "guid-a",
                    "MeshA",
                    expected or self.old_b,
                    self.new_b,
                )
            ],
        }

    def material_at(self, instance_id):
        project = self.store.get_active_copy()
        return project["instances"][instance_id]["render_config"]["render_parts"][0][
            "material_paths"
        ][0]

    def component_material_at(self, instance_id):
        project = self.store.get_active_copy()
        component_id = project["instances"][instance_id]["component_id"]
        return project["components"][component_id]["render_config"]["render_parts"][0][
            "material_paths"
        ][0]

    def test_success_updates_instance_component_and_persistence(self):
        ok, info, status = apply_material_writeback(
            self.store,
            [self.change_a()],
            expected_project_id="material_project",
        )

        self.assertTrue(ok)
        self.assertEqual(200, status)
        self.assertEqual(1, info["instance_count"])
        self.assertEqual(1, info["part_count"])
        self.assertEqual(1, info["component_sync_count"])
        self.assertEqual(self.new_a, self.material_at("a"))
        self.assertEqual(self.new_a, self.component_material_at("a"))

        reopened = ProjectStore(self.projects_dir, self.active_file)
        persisted = reopened.get_active_copy()
        self.assertEqual(
            self.new_a,
            persisted["instances"]["a"]["render_config"]["render_parts"][0][
                "material_paths"
            ][0],
        )

    def test_identity_fallback_accepts_stale_array_index(self):
        change = self.change_a()
        change["parts"][0]["part_index"] = 99

        ok, info, status = apply_material_writeback(self.store, [change])

        self.assertTrue(ok)
        self.assertEqual(200, status)
        self.assertEqual([0], info["results"][0]["part_indices"])
        self.assertEqual(self.new_a, self.material_at("a"))

    def test_material_conflict_rolls_back_entire_batch(self):
        ok, info, status = apply_material_writeback(
            self.store,
            [self.change_a(), self.change_b(expected="/Game/Materials/Stale.Stale")],
        )

        self.assertFalse(ok)
        self.assertEqual(409, status)
        self.assertEqual("material_conflict", info["error"])
        self.assertEqual(self.old_a, self.material_at("a"))
        self.assertEqual(self.old_b, self.material_at("b"))
        self.assertEqual(self.old_a, self.component_material_at("a"))

    def test_component_conflict_rolls_back_instance_change(self):
        def make_component_stale(project):
            project["components"]["component-a"]["render_config"]["render_parts"][0][
                "material_paths"
            ] = ["/Game/Materials/ComponentStale.ComponentStale"]

        self.store.transact_active(make_component_stale)

        ok, info, status = apply_material_writeback(self.store, [self.change_a()])

        self.assertFalse(ok)
        self.assertEqual(409, status)
        self.assertEqual("material_conflict", info["error"])
        self.assertEqual(self.old_a, self.material_at("a"))

    def test_expected_project_guard_is_propagated(self):
        with self.assertRaises(ProjectMismatch):
            apply_material_writeback(
                self.store,
                [self.change_a()],
                expected_project_id="another-project",
            )


if __name__ == "__main__":
    unittest.main()
