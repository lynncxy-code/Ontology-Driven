import copy
import importlib.util
import json
import tempfile
import unittest
import uuid
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
MODULE_PATH = BACKEND / "tools" / "build_zhhz_migration_registry.py"
SPEC = importlib.util.spec_from_file_location("build_zhhz_migration_registry", MODULE_PATH)
REGISTRY_BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REGISTRY_BUILDER)


def _shared(rid, api_name, display_name, data_type):
    return {
        "rid": rid,
        "api_name": api_name,
        "display_name": display_name,
        "description": "fixture",
        "lifecycle_status": "ACTIVE",
        "data_type": data_type,
    }


def _fixture_template():
    shared_specs = [
        ("00000000-0000-4000-8000-000000000001", "instance_id", "实例身份证号", "DT_STRING"),
        ("00000000-0000-4000-8000-000000000002", "asset_id", "资产唯一码", "DT_STRING"),
        ("00000000-0000-4000-8000-000000000003", "is_visible", "是否渲染", "DT_BOOLEAN"),
        ("00000000-0000-4000-8000-000000000004", "translation_x", "位置 X", "DT_DOUBLE"),
        ("00000000-0000-4000-8000-000000000005", "translation_y", "位置 Y", "DT_DOUBLE"),
        ("00000000-0000-4000-8000-000000000006", "translation_z", "位置 Z", "DT_DOUBLE"),
        ("00000000-0000-4000-8000-000000000007", "rotation_x", "旋转 X", "DT_DOUBLE"),
        ("00000000-0000-4000-8000-000000000008", "rotation_y", "旋转 Y", "DT_DOUBLE"),
        ("00000000-0000-4000-8000-000000000009", "rotation_z", "旋转 Z", "DT_DOUBLE"),
        ("00000000-0000-4000-8000-000000000010", "scale_x", "缩放 X", "DT_DOUBLE"),
        ("00000000-0000-4000-8000-000000000011", "scale_y", "缩放 Y", "DT_DOUBLE"),
        ("00000000-0000-4000-8000-000000000012", "scale_z", "缩放 Z", "DT_DOUBLE"),
        # This unrelated contract must not leak into the ZHHZ registry.
        ("00000000-0000-4000-8000-000000000013", "material_variant", "材质变体", "DT_STRING"),
    ]
    shared = {
        f"ri.shprop.{suffix}": _shared(
            f"ri.shprop.{suffix}", api_name, display_name, data_type
        )
        for suffix, api_name, display_name, data_type in shared_specs
    }
    by_api = {entry["api_name"]: entry["rid"] for entry in shared.values()}
    representable_rid = "ri.iface.00000000-0000-4000-8000-000000000101"
    spatial_rid = "ri.iface.00000000-0000-4000-8000-000000000102"
    visual_rid = "ri.iface.00000000-0000-4000-8000-000000000103"
    interfaces = {
        representable_rid: {
            "rid": representable_rid,
            "api_name": "i3d_representable",
            "display_name": "三维存在接口",
            "description": "fixture",
            "lifecycle_status": "ACTIVE",
            "category": "OBJECT_INTERFACE",
            "required_shared_property_type_rids": [
                by_api["asset_id"],
                by_api["is_visible"],
            ],
        },
        spatial_rid: {
            "rid": spatial_rid,
            "api_name": "i3d_spatial",
            "display_name": "空间变换接口",
            "description": "fixture",
            "lifecycle_status": "ACTIVE",
            "category": "OBJECT_INTERFACE",
            "required_shared_property_type_rids": [
                by_api[name]
                for name in (
                    "translation_x",
                    "translation_y",
                    "translation_z",
                    "rotation_x",
                    "rotation_y",
                    "rotation_z",
                    "scale_x",
                    "scale_y",
                    "scale_z",
                )
            ],
            "extends_interface_type_rids": [representable_rid],
        },
        visual_rid: {
            "rid": visual_rid,
            "api_name": "i3d_visual",
            "display_name": "视觉表达接口",
            "description": "fixture",
            "lifecycle_status": "ACTIVE",
            "category": "OBJECT_INTERFACE",
            "required_shared_property_type_rids": [by_api["material_variant"]],
            "extends_interface_type_rids": [representable_rid],
        },
    }
    return {
        "version": "ontotwin-3.4.0",
        "shared_property_types": shared,
        "interface_types": interfaces,
        "object_types": {},
        "link_types": {},
        "action_types": {},
    }


class ZhhzMigrationRegistryTests(unittest.TestCase):
    def setUp(self):
        self.template = _fixture_template()
        self.registry = REGISTRY_BUILDER.build_registry(self.template)

    def test_reuses_only_representable_and_spatial_contract_rids(self):
        selected_interfaces = self.registry["interface_types"]
        self.assertEqual(
            {entry["api_name"] for entry in selected_interfaces.values()},
            {"i3d_representable", "i3d_spatial"},
        )
        template_by_api = {
            entry["api_name"]: entry for entry in self.template["interface_types"].values()
        }
        for entry in selected_interfaces.values():
            self.assertEqual(entry, template_by_api[entry["api_name"]])

        self.assertEqual(len(self.registry["shared_property_types"]), 12)
        self.assertNotIn(
            "material_variant",
            {
                entry["api_name"]
                for entry in self.registry["shared_property_types"].values()
            },
        )

    def test_emits_eight_experimental_types_with_exact_display_names(self):
        objects = self.registry["object_types"]
        self.assertEqual(len(objects), 8)
        expected = {
            api_name: display_name
            for _block_id, api_name, display_name in REGISTRY_BUILDER.ZHHZ_TYPES
        }
        actual = {entry["api_name"]: entry["display_name"] for entry in objects.values()}
        self.assertEqual(actual, expected)
        self.assertTrue(
            all(entry["lifecycle_status"] == "EXPERIMENTAL" for entry in objects.values())
        )

    def test_object_and_property_rids_are_stable_uuid5(self):
        block_id = "zhhz.fixed_wing_aircraft"
        expected_object_uuid = uuid.uuid5(
            REGISTRY_BUILDER.RID_NAMESPACE,
            f"{REGISTRY_BUILDER.DATASET_ID}:object:{block_id}",
        )
        expected_property_uuid = uuid.uuid5(
            REGISTRY_BUILDER.RID_NAMESPACE,
            f"{REGISTRY_BUILDER.DATASET_ID}:object:{block_id}:property:instance_id",
        )
        rid = f"ri.obj.{expected_object_uuid}"
        self.assertIn(rid, self.registry["object_types"])
        obj = self.registry["object_types"][rid]
        self.assertEqual(
            obj["property_types"]["instance_id"]["rid"],
            f"ri.prop.{expected_property_uuid}",
        )
        self.assertEqual(self.registry, REGISTRY_BUILDER.build_registry(self.template))

    def test_each_type_has_contract_properties_and_instance_primary_key(self):
        required_api_names = {
            entry["api_name"]
            for entry in self.registry["shared_property_types"].values()
        }
        interface_rids = [
            next(
                entry["rid"]
                for entry in self.registry["interface_types"].values()
                if entry["api_name"] == api_name
            )
            for api_name in REGISTRY_BUILDER.INTERFACE_API_NAMES
        ]
        for obj in self.registry["object_types"].values():
            self.assertEqual(set(obj["property_types"]), required_api_names)
            self.assertEqual(obj["implements_interface_type_rids"], interface_rids)
            self.assertEqual(
                obj["primary_key_property_type_rids"],
                [obj["property_types"]["instance_id"]["rid"]],
            )

    def test_template_is_not_mutated(self):
        untouched = copy.deepcopy(self.template)
        REGISTRY_BUILDER.build_registry(self.template)
        self.assertEqual(self.template, untouched)

    def test_extensions_include_exact_business_ids_and_provenance(self):
        cypher = REGISTRY_BUILDER.build_extensions_cypher(self.registry)
        self.assertEqual(cypher.count("MATCH (n:ObjectType"), 8)
        self.assertEqual(cypher.count('n.x_source = "ue_migration:ZHHZ"'), 8)
        self.assertEqual(cypher.count('n.x_origin = "ontotwin"'), 8)
        for block_id, _api_name, _display_name in REGISTRY_BUILDER.ZHHZ_TYPES:
            self.assertIn(f'n.x_block_name = "{block_id}"', cypher)

    def test_generate_artifacts_uses_dataset_scoped_names(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template_path = root / "template.json"
            output_dir = root / "out"
            template_path.write_text(
                json.dumps(self.template, ensure_ascii=False), encoding="utf-8"
            )
            json_path, extensions_path = REGISTRY_BUILDER.generate_artifacts(
                template_path,
                output_dir,
                None,
            )
            self.assertEqual(
                json_path.name,
                "ontotwin.ds_1784694647848.ontology.json",
            )
            self.assertEqual(
                extensions_path.name,
                "ontotwin.ds_1784694647848.extensions.cypher",
            )
            self.assertEqual(
                json.loads(json_path.read_text(encoding="utf-8")), self.registry
            )


if __name__ == "__main__":
    unittest.main()
