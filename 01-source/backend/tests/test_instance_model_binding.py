import os
import tempfile
import time
import unittest

try:
    from backend.instance_model_binding.service import (
        InstanceModelBindingError,
        InstanceModelBindingService,
        resolve_effective_model,
    )
    from backend.project_store import ProjectStore as RuntimeProjectStore
except ModuleNotFoundError:
    from instance_model_binding.service import (
        InstanceModelBindingError,
        InstanceModelBindingService,
        resolve_effective_model,
    )
    from project_store import ProjectStore as RuntimeProjectStore


# The application may rebind ProjectStore to ProjectStorePG through ONTOTWIN_STORE.
# These tests must always use the JSON base class so their temporary directory is real.
ProjectStore = (
    RuntimeProjectStore.__mro__[1]
    if RuntimeProjectStore.__name__ == "ProjectStorePG"
    else RuntimeProjectStore
)


class FakeArtStudio:
    PREFIX = "artstudio:"

    def __init__(self):
        self.prefetched = []
        self.status = "preparing"

    def fetch_detail(self, asset_id):
        if asset_id == "404":
            return None
        return {
            "name": f"Asset {asset_id}",
            "version": 3,
            "files": [{"ext": "glb", "download_url": "https://example.test/a.glb"}],
        }

    @staticmethod
    def pick_glb_file(detail):
        return next((item for item in detail.get("files", []) if item["ext"] == "glb"), None)

    @staticmethod
    def make_stable_id(asset_id, version):
        return f"artstudio:{asset_id}:v{version}"

    @staticmethod
    def parse_stable_id(value):
        asset_id, _, version = value[len("artstudio:"):].rpartition(":v")
        return asset_id, int(version)

    @staticmethod
    def get_version(_asset_id):
        return 3

    def ensure_local_glb(self, asset_id, version):
        self.prefetched.append((asset_id, version))
        return None

    def local_glb_status(self, _asset_id, _version):
        return self.status


class InstanceModelBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = self.temp_dir.name
        self.projects_dir = os.path.join(root, "projects")
        self.active_file = os.path.join(root, "active.json")
        self.type_rid = "ri.obj.machine"
        self.types = {
            self.type_rid: {
                "name": "Machine",
                "asset_id": "type-a.glb",
                "ue_asset_path": "type-a.glb",
                "injected_interfaces": ["I3D_Representable", "I3D_Spatial"],
            }
        }
        self.store = ProjectStore(self.projects_dir, self.active_file)
        self.assertEqual(self.store.__class__.__name__, "ProjectStore")
        self.store.create_project("P", self.types, project_id="project-a")
        self.store.spawn("inst-a", self.type_rid, render_config={})
        self.store.spawn("inst-b", self.type_rid, render_config={})
        self.artstudio = FakeArtStudio()
        self.service = InstanceModelBindingService(self.store, {}, self.artstudio)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_changes_only_selected_instance_and_persists(self):
        result = self.service.save("inst-a", {
            "file_number": "123",
            "expected_project_id": "project-a",
        })
        self.assertEqual(result["effective_model"]["mode"], "instance_override")
        self.assertEqual(result["model_status"]["code"], "available")
        self.assertEqual(self.artstudio.prefetched, [])
        self.assertEqual(self.store.get_render_config("inst-b"), {})

        reopened = ProjectStore(self.projects_dir, self.active_file)
        override = reopened.get_render_config("inst-a")["model_override"]
        self.assertEqual(override["ue_asset_path"], "artstudio:123:v3")
        self.assertEqual(override["revision"], 1)

    def test_type_default_change_does_not_replace_override(self):
        self.service.save("inst-a", {"file_number": "local.glb"})
        updated_types = self.store.get_object_types()
        updated_types[self.type_rid]["ue_asset_path"] = "type-b.glb"
        updated_types[self.type_rid]["asset_id"] = "type-b.glb"
        self.store.set_object_types(updated_types)
        self.assertEqual(
            self.service.summary("inst-a")["effective_model"]["ue_asset_path"],
            "local.glb",
        )

    def test_my_assets_source_is_preserved(self):
        result = self.service.save("inst-a", {
            "file_number": "123",
            "source": "artstudio_mine",
        })
        self.assertEqual(result["instance_override"]["source"], "artstudio_mine")

    def test_clear_restores_latest_type_default(self):
        self.service.save("inst-a", {"file_number": "local.glb"})
        updated_types = self.store.get_object_types()
        updated_types[self.type_rid]["ue_asset_path"] = "type-b.glb"
        updated_types[self.type_rid]["asset_id"] = "type-b.glb"
        self.store.set_object_types(updated_types)
        result = self.service.clear("inst-a")
        self.assertEqual(result["effective_model"]["mode"], "type_default")
        self.assertEqual(result["effective_model"]["ue_asset_path"], "type-b.glb")

    def test_type_without_default_can_receive_override(self):
        updated_types = self.store.get_object_types()
        updated_types[self.type_rid]["asset_id"] = ""
        updated_types[self.type_rid]["ue_asset_path"] = ""
        self.store.set_object_types(updated_types)
        self.assertEqual(self.service.summary("inst-a")["effective_model"]["mode"], "placeholder")
        result = self.service.save("inst-a", {"file_number": "/Game/A.A"})
        self.assertEqual(result["effective_model"]["mode"], "instance_override")

    def test_capability_block_keeps_existing_override_but_rejects_new_save(self):
        self.service.save("inst-a", {"file_number": "local.glb"})
        updated_types = self.store.get_object_types()
        updated_types[self.type_rid]["injected_interfaces"] = ["I3D_Spatial"]
        self.store.set_object_types(updated_types)
        summary = self.service.summary("inst-a")
        self.assertIsNotNone(summary["instance_override"])
        self.assertEqual(summary["model_status"]["code"], "capability_blocked")
        with self.assertRaises(InstanceModelBindingError) as caught:
            self.service.save("inst-a", {"file_number": "other.glb"})
        self.assertEqual(caught.exception.code, "representable_capability_required")

    def test_type_default_wins_over_assembly_after_override_is_cleared(self):
        parts = [{"asset_path": "/Game/Part.Part", "relative_transform": {"tx": 2}}]

        def add_assembly(project):
            project["instances"]["inst-a"]["render_config"] = {
                "asset_id": "/Game/Base.Base",
                "ue_asset_path": "/Game/Base.Base",
                "render_parts": parts,
                "assembly_signature": "sig-a",
            }

        self.store.transact_active(add_assembly)
        overridden = self.service.save("inst-a", {"file_number": "replacement.glb"})
        self.assertEqual(overridden["effective_model"]["mode"], "instance_override")
        self.assertEqual(overridden["original_assembly"]["part_count"], 1)
        restored = self.service.clear("inst-a")
        self.assertEqual(restored["effective_model"]["mode"], "type_default")
        self.assertEqual(restored["effective_model"]["ue_asset_path"], "type-a.glb")
        self.assertEqual(self.store.get_render_config("inst-a")["render_parts"], parts)

    def test_assembly_is_restored_when_type_default_is_empty(self):
        parts = [{"asset_path": "/Game/Part.Part"}]

        def add_assembly_and_clear_type(project):
            project["object_types"][self.type_rid]["asset_id"] = ""
            project["object_types"][self.type_rid]["ue_asset_path"] = ""
            project["instances"]["inst-a"]["render_config"] = {
                "render_parts": parts,
                "assembly_signature": "sig-a",
                "model_override": {
                    "asset_id": "replacement.glb",
                    "ue_asset_path": "replacement.glb",
                },
            }

        self.store.transact_active(add_assembly_and_clear_type)
        restored = self.service.clear("inst-a")
        self.assertEqual(restored["effective_model"]["mode"], "original_assembly")
        self.assertEqual(restored["inherited_model"]["mode"], "original_assembly")

    def test_project_conflict_is_rejected(self):
        with self.assertRaises(InstanceModelBindingError) as caught:
            self.service.save("inst-a", {
                "file_number": "local.glb",
                "expected_project_id": "other",
            })
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(caught.exception.code, "active_project_changed")

    def test_offline_instance_waits_for_delivery(self):
        def make_offline(project):
            project["instances"]["inst-a"]["last_seen"] = time.time() - 10

        self.store.transact_active(make_offline)
        self.assertEqual(
            self.service.summary("inst-a")["delivery_status"]["code"],
            "waiting_for_instance",
        )

    def test_pure_resolver_precedence(self):
        config = {
            "model_override": {"asset_id": "override.glb", "ue_asset_path": "override.glb"},
            "render_parts": [{"asset_path": "/Game/Part.Part"}],
            "assembly_signature": "sig-a",
        }
        resolved = resolve_effective_model({}, config, self.types[self.type_rid], {})
        self.assertEqual(resolved["mode"], "instance_override")

        config.pop("model_override")
        resolved = resolve_effective_model({}, config, self.types[self.type_rid], {})
        self.assertEqual(resolved["mode"], "type_default")

        no_default = {**self.types[self.type_rid], "asset_id": "", "ue_asset_path": ""}
        resolved = resolve_effective_model({}, config, no_default, {})
        self.assertEqual(resolved["mode"], "original_assembly")

        resolved = resolve_effective_model({}, {}, no_default, {})
        self.assertEqual(resolved["mode"], "placeholder")

    def test_clear_type_default_preserves_instance_data_and_is_idempotent(self):
        self.service.save("inst-a", {"file_number": "override.glb"})
        before = self.store.get_render_config("inst-a")
        changed = []
        service = InstanceModelBindingService(
            self.store,
            {},
            self.artstudio,
            on_object_types_changed=lambda: changed.append(True),
        )

        first = service.clear_type_default(self.type_rid)
        second = service.clear_type_default(self.type_rid)
        object_type = self.store.get_object_types()[self.type_rid]
        self.assertEqual(object_type["asset_id"], "")
        self.assertEqual(object_type["ue_asset_path"], "")
        self.assertEqual(self.store.get_render_config("inst-a"), before)
        self.assertEqual(first["affected_instance_count"], 1)
        self.assertEqual(second["status"], "ok")
        self.assertEqual(len(changed), 2)

    def test_clear_unknown_type_is_rejected(self):
        with self.assertRaises(InstanceModelBindingError) as caught:
            self.service.clear_type_default("missing")
        self.assertEqual(caught.exception.status, 404)


if __name__ == "__main__":
    unittest.main()
