import copy
import os
import sys
import tempfile
import unittest


BACKEND = os.path.dirname(os.path.dirname(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)
os.environ["ONTOTWIN_STORE"] = "json"

from customer_edit_changes import CustomerEditError, SCHEMA, apply_customer_edit_changes  # noqa: E402
from project_store import ProjectStore  # noqa: E402


def transform(x=1, y=2, z=3):
    return {"tx": x, "ty": y, "tz": z, "rx": 0, "ry": 0, "rz": 0, "sx": 1, "sy": 1, "sz": 1}


def render(signature, asset="/Game/New.New", material="/Game/M.M"):
    return {
        "asset_id": asset,
        "ue_asset_path": asset,
        "assembly_signature": signature,
        "render_parts": [{
            "asset_path": asset,
            "source_actor_guid": "guid-new",
            "source_component_name": "StaticMeshComponent0",
            "material_paths": [material],
            "relative_transform": transform(0, 0, 0),
        }],
    }


class CustomerEditChangesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(
            projects_dir=os.path.join(self.temp.name, "projects"),
            active_file=os.path.join(self.temp.name, "active.json"),
        )
        self.store.create_project("test", project_id="p1")

        def seed(project):
            project["object_types"]["type.old"] = {
                "rid": "type.old", "name": "Old Type", "injected_interfaces": []
            }
            project["instances"]["old"] = {
                "id": "old", "object_type_rid": "type.old", "object_type_name": "Old Type",
                "display_name": "Keep Name", "semantic_note": "keep me",
                "render_config": {
                    **render("old-sig", "/Game/Old.Old", "/Game/OldMat.OldMat"),
                    "interface_overrides": {"I3D_Overlay": {"config": {"title": "keep UI"}}},
                    "model_override": {"asset_id": "/Game/Stale.Stale"},
                },
                "raw_state": {
                    "translation_x": 1.0, "translation_y": 2.0, "translation_z": 3.0,
                    "rotation_x": 0.0, "rotation_y": 0.0, "rotation_z": 0.0,
                    "scale_x": 1.0, "scale_y": 1.0, "scale_z": 1.0,
                    "ui_label_content": "keep UI state",
                },
            }
            project["components"]["c1"] = {
                "id": "c1", "bound_instance_id": "old",
                "render_config": copy.deepcopy(project["instances"]["old"]["render_config"]),
            }
            project["instance_roster"] = [{"instance_id": "old"}]

        self.store.transact_active(seed)

    def tearDown(self):
        self.temp.cleanup()

    def document(self, operations=None, overrides=None):
        return {"schema": SCHEMA, "project_id": "p1", "ue_project_id": "ueproj_demo",
                "instance_operations": operations or [], "overrides": overrides or []}

    def test_replace_preserves_semantics_ui_and_binding(self):
        document = self.document([{
            "op": "replace", "instance_id": "old",
            "expected_object_type_rid": "type.old", "expected_assembly_signature": "old-sig",
            "transform": transform(20, 30, 40), "render_config": render("new-sig"),
        }])
        result = apply_customer_edit_changes(
            self.store, document, commit=True, backup_dir=os.path.join(self.temp.name, "backups")
        )
        current = self.store.get_active_copy()
        instance = current["instances"]["old"]
        self.assertEqual(result["summary"]["replaced"], 1)
        self.assertTrue(os.path.isfile(result["backup_path"]))
        self.assertEqual(instance["object_type_rid"], "type.old")
        self.assertEqual(instance["semantic_note"], "keep me")
        self.assertEqual(instance["display_name"], "Keep Name")
        self.assertEqual(instance["raw_state"]["ui_label_content"], "keep UI state")
        self.assertEqual(instance["raw_state"]["translation_x"], 20)
        self.assertEqual(instance["render_config"]["assembly_signature"], "new-sig")
        self.assertNotIn("model_override", instance["render_config"])
        self.assertEqual(instance["render_config"]["interface_overrides"]["I3D_Overlay"]["config"]["title"], "keep UI")
        self.assertEqual(current["components"]["c1"]["bound_instance_id"], "old")
        self.assertEqual(current["components"]["c1"]["render_config"]["assembly_signature"], "new-sig")

    def test_delete_unbinds_component_and_removes_roster(self):
        document = self.document([{
            "op": "delete", "instance_id": "old",
            "expected_object_type_rid": "type.old", "expected_assembly_signature": "old-sig",
        }])
        apply_customer_edit_changes(
            self.store, document, commit=True, backup_dir=os.path.join(self.temp.name, "backups")
        )
        current = self.store.get_active_copy()
        self.assertNotIn("old", current["instances"])
        self.assertIsNone(current["components"]["c1"]["bound_instance_id"])
        self.assertEqual(current["instance_roster"], [])

    def test_unmatched_actor_creates_pending_generic_instance(self):
        document = self.document([{
            "op": "create", "instance_id": "ue_customer_abc", "display_name": "新增柜子",
            "transform": transform(), "render_config": render("created-sig"),
        }])
        apply_customer_edit_changes(
            self.store, document, commit=True, backup_dir=os.path.join(self.temp.name, "backups")
        )
        created = self.store.get_active_copy()["instances"]["ue_customer_abc"]
        self.assertEqual(created["object_type_rid"], "ontotwin.customer.added_model")
        self.assertEqual(created["classification_status"], "pending")

    def test_conflict_rejected_without_mutation(self):
        before = self.store.get_active_copy()
        document = self.document([{
            "op": "replace", "instance_id": "old",
            "expected_object_type_rid": "type.old", "expected_assembly_signature": "wrong",
            "transform": transform(), "render_config": render("new-sig"),
        }])
        with self.assertRaises(CustomerEditError):
            apply_customer_edit_changes(
                self.store, document, commit=True, backup_dir=os.path.join(self.temp.name, "backups")
            )
        self.assertEqual(self.store.get_active_copy(), before)

    def test_dry_run_does_not_mutate_or_write_backup(self):
        before = self.store.get_active_copy()
        backup_dir = os.path.join(self.temp.name, "backups")
        document = self.document([{
            "op": "replace", "instance_id": "old",
            "expected_object_type_rid": "type.old", "expected_assembly_signature": "old-sig",
            "transform": transform(), "render_config": render("new-sig"),
        }])
        result = apply_customer_edit_changes(self.store, document, backup_dir=backup_dir)
        self.assertEqual(result["mode"], "dry-run")
        self.assertEqual(self.store.get_active_copy(), before)
        self.assertFalse(os.path.exists(backup_dir))


if __name__ == "__main__":
    unittest.main()
