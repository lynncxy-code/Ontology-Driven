import os
import tempfile
import unittest

try:
    from backend.project_store import ProjectStore as RuntimeProjectStore
    from backend.representation_container.service import (
        RepresentationContainerError,
        RepresentationContainerService,
        resolve_effective_container,
    )
except ModuleNotFoundError:
    from project_store import ProjectStore as RuntimeProjectStore
    from representation_container.service import (
        RepresentationContainerError,
        RepresentationContainerService,
        resolve_effective_container,
    )


ProjectStore = (
    RuntimeProjectStore.__mro__[1]
    if RuntimeProjectStore.__name__ == "ProjectStorePG"
    else RuntimeProjectStore
)


class RepresentationContainerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = self.temp_dir.name
        self.store = ProjectStore(
            os.path.join(root, "projects"),
            os.path.join(root, "active.json"),
        )
        self.types = {
            "ri.machine": {
                "name": "Machine",
                "asset_id": "/Game/Machine/SM_A.SM_A",
                "ue_asset_path": "/Game/Machine/SM_A.SM_A",
                "injected_interfaces": ["I3D_Representable", "I3D_Spatial"],
            },
            "ri.no-model": {
                "name": "No Model",
                "asset_id": "",
                "ue_asset_path": "",
                "injected_interfaces": ["I3D_Representable"],
            },
            "ri.no-capability": {
                "name": "No Capability",
                "asset_id": "/Game/Machine/SM_B.SM_B",
                "ue_asset_path": "/Game/Machine/SM_B.SM_B",
                "injected_interfaces": [],
            },
        }
        self.store.create_project("P", self.types, project_id="project-a")
        self.store.spawn("machine-a", "ri.machine", render_config={})
        self.store.spawn("assembly-a", "ri.no-model", render_config={
            "render_parts": [{"asset_path": "/Game/Part.Part"}],
            "assembly_signature": "sig-a",
        })
        self.changed = []
        self.service = RepresentationContainerService(
            self.store,
            on_object_types_changed=lambda: self.changed.append(True),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_clear_type_container(self):
        result = self.service.save("ri.machine", {
            "expected_project_id": "project-a",
            "container_blueprint_id": "/Game/SCC/BP_Item.BP_Item",
            "container_slot": "primary",
        })
        self.assertTrue(result["enabled"])
        self.assertEqual(result["mode"], "type_default")
        persisted = self.store.get_object_types()["ri.machine"]
        self.assertEqual(
            persisted["container_blueprint_id"],
            "/Game/SCC/BP_Item.BP_Item",
        )

        cleared = self.service.clear("ri.machine", {
            "expected_project_id": "project-a",
        })
        self.assertFalse(cleared["enabled"])
        self.assertNotIn(
            "container_blueprint_id",
            self.store.get_object_types()["ri.machine"],
        )
        self.assertEqual(len(self.changed), 2)

    def test_expected_project_guard_is_required(self):
        with self.assertRaises(RepresentationContainerError) as missing:
            self.service.save("ri.machine", {
                "container_blueprint_id": "/Game/SCC/BP_Item.BP_Item",
            })
        self.assertEqual(missing.exception.code, "expected_project_id_required")

        with self.assertRaises(RepresentationContainerError) as changed:
            self.service.save("ri.machine", {
                "expected_project_id": "other",
                "container_blueprint_id": "/Game/SCC/BP_Item.BP_Item",
            })
        self.assertEqual(changed.exception.status, 409)

    def test_assembly_conflict_is_rejected(self):
        with self.assertRaises(RepresentationContainerError) as caught:
            self.service.save("ri.no-model", {
                "expected_project_id": "project-a",
                "container_blueprint_id": "/Game/SCC/BP_Item.BP_Item",
            })
        self.assertEqual(caught.exception.code, "assembly_container_conflict")

    def test_batch_updates_only_eligible_asset_types(self):
        result = self.service.apply_batch({
            "expected_project_id": "project-a",
            "container_blueprint_id": "/Game/SCC/BP_Item.BP_Item",
            "container_slot": "primary",
        })
        self.assertEqual(result["affected_object_type_rids"], ["ri.machine"])
        reasons = {item["object_type_rid"]: item["reason"] for item in result["skipped"]}
        self.assertEqual(reasons["ri.no-model"], "missing_type_model")
        self.assertEqual(reasons["ri.no-capability"], "missing_representable")

    def test_resolver_uses_live_type_then_frozen_fallback(self):
        frozen = {
            "container_blueprint_id": "/Game/Frozen.BP_Frozen",
            "container_slot": "legacy",
        }
        live = {
            "container_blueprint_id": "/Game/Live.BP_Live",
            "container_slot": "primary",
        }
        resolved = resolve_effective_container(frozen, live, {"mode": "type_default"})
        self.assertEqual(resolved["mode"], "type_default")
        self.assertEqual(resolved["container_blueprint_id"], "/Game/Live.BP_Live")

        cleared_live = resolve_effective_container(frozen, {"name": "Live"}, {"mode": "type_default"})
        self.assertEqual(cleared_live["mode"], "direct")

        moved = resolve_effective_container(frozen, {}, {"mode": "legacy_frozen"})
        self.assertEqual(moved["mode"], "frozen")

    def test_assembly_suppresses_container(self):
        resolved = resolve_effective_container(
            {"container_blueprint_id": "/Game/Frozen.BP_Frozen"},
            {"container_blueprint_id": "/Game/Live.BP_Live"},
            {"mode": "original_assembly"},
        )
        self.assertFalse(resolved["enabled"])
        self.assertEqual(resolved["mode"], "suppressed_assembly")


if __name__ == "__main__":
    unittest.main()
