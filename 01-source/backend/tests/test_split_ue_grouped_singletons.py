import importlib.util
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "test_split_ue_grouped_singletons",
    BACKEND / "tools" / "split_ue_grouped_singletons.py",
)
SPLITTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SPLITTER)


def _fixture():
    child = {
        "guid": "CHILD-GUID",
        "actor_label": "SM_Lamp_7",
        "actor_name": "StaticMeshActor_7",
        "folder_path": "Park",
        "parent_guid": "GROUP-GUID",
        "actor_class": "StaticMeshActor",
        "actor_class_path": "/Script/Engine.StaticMeshActor",
        "has_mirrored_scale": False,
    }
    part = {
        "asset_path": "/Game/Lamp.Lamp",
        "source_actor_guid": "CHILD-GUID",
        "source_actor_label": "SM_Lamp_7",
        "source_component_name": "StaticMeshComponent0",
        "source_component_class": "/Script/Engine.StaticMeshComponent",
        "relative_transform": {
            "tx": 25, "ty": -10, "tz": 2,
            "rx": 0, "ry": 0, "rz": 90,
            "sx": 1, "sy": 1, "sz": 1,
        },
        "material_paths": ["/Game/LampMat.LampMat"],
        "visible": True,
        "hidden_in_game": False,
        "cast_shadow": True,
        "collision_enabled": "QueryAndPhysics",
    }
    payload = {
        "actors": [{
            "ext_guid": "GROUP-GUID",
            "actor_label": "Lamp_Group",
            "source_folder_path": "ToMigrate",
            "transform": {
                "tx": 100, "ty": 200, "tz": 5,
                "rx": 0, "ry": 0, "rz": 0,
                "sx": 1, "sy": 1, "sz": 1,
            },
            "source_actor_guids": ["GROUP-GUID", "CHILD-GUID"],
            "source_actors": [
                {"guid": "GROUP-GUID", "actor_label": "Lamp_Group"},
                child,
            ],
            "render_parts": [part],
            "unsupported_components": [],
        }]
    }
    manifest = {
        "project_id": "project",
        "ue_project_id": "ueproj_park",
        "ue_project_name": "Park",
        "expected_object_type_count": 1,
        "expected_new_instance_count": 1,
        "expected_source_cleanup_count": 2,
        "groups": [{
            "source_container_guid": "GROUP-GUID",
            "old_instance_id": "ue_GROUP-GUID",
            "object_type_rid": "ri.obj.lamp",
            "object_type_name": "Lamp",
            "display_name_prefix": "Lamp",
            "hierarchy_path": ["Park", "Lighting"],
            "expected_instance_count": 1,
            "expected_asset_path": "/Game/Lamp.Lamp",
        }],
    }
    return payload, manifest


class SplitGroupedSingletonTests(unittest.TestCase):
    def test_single_mesh_child_becomes_spatial_instance(self):
        payload, manifest = _fixture()
        output, rows, audit = SPLITTER.split_export(payload, manifest)
        self.assertTrue(audit["success"])
        self.assertEqual(audit["new_instance_count"], 1)
        self.assertEqual(audit["source_cleanup_guid_count"], 2)
        actor = output["actors"][0]
        self.assertEqual(actor["ext_guid"], "CHILD-GUID")
        self.assertEqual(actor["name"], "Lamp 7")
        self.assertEqual(actor["transform"]["tx"], 125.0)
        self.assertEqual(actor["transform"]["ty"], 190.0)
        self.assertEqual(actor["transform"]["tz"], 7.0)
        self.assertEqual(actor["transform"]["rz"], 90.0)
        self.assertEqual(
            actor["render_parts"][0]["relative_transform"],
            SPLITTER.IDENTITY_TRANSFORM,
        )
        self.assertEqual(rows[0]["action"], "map_existing")
        self.assertEqual(rows[0]["suggested_object_type_rid"], "ri.obj.lamp")

    def test_rotated_group_requires_new_export(self):
        payload, manifest = _fixture()
        payload["actors"][0]["transform"]["rz"] = 10
        with self.assertRaisesRegex(ValueError, "rotated group root"):
            SPLITTER.split_export(payload, manifest)

    def test_multi_part_child_is_not_silently_split(self):
        payload, manifest = _fixture()
        payload["actors"][0]["render_parts"].append(
            dict(payload["actors"][0]["render_parts"][0])
        )
        manifest["groups"][0]["expected_instance_count"] = 2
        with self.assertRaisesRegex(ValueError, "multiple render parts"):
            SPLITTER.split_export(payload, manifest)


if __name__ == "__main__":
    unittest.main()
