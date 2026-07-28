import ast
import csv
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_migration_module():
    project_store = types.ModuleType("project_store")
    project_store.ProjectStore = object
    project_store._default_raw_state = lambda rid, name, position: {
        "object_type_rid": rid,
        "name": name,
        "translation_x": position["x"],
        "translation_y": position["y"],
        "translation_z": position["z"],
    }
    project_store.apply_instance_metadata = lambda rec, metadata: rec.update(metadata)

    db = types.ModuleType("db")
    db.pg = types.SimpleNamespace(ping=lambda: True)

    binding = types.ModuleType("ue_project_binding")
    binding.bind_active_dataset = lambda *args: (True, {})

    previous = {
        name: sys.modules.get(name)
        for name in ("project_store", "db", "ue_project_binding")
    }
    sys.modules.update({
        "project_store": project_store,
        "db": db,
        "ue_project_binding": binding,
    })
    try:
        return _load_module(
            "test_migrate_ue_actors",
            BACKEND / "tools" / "migrate_ue_actors.py",
        )
    finally:
        for name, old_module in previous.items():
            if old_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old_module


def _load_app_helpers(*function_names):
    source_path = BACKEND / "app.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    wanted = set(function_names)
    nodes = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted
    ]
    if {node.name for node in nodes} != wanted:
        raise AssertionError(f"app helpers not found: {wanted - {node.name for node in nodes}}")
    namespace = {}
    helper_module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(helper_module, str(source_path), "exec"), namespace)
    return namespace


MIGRATION = _load_migration_module()
CLASSIFICATION = _load_module(
    "test_generate_migration_classification_csv",
    BACKEND / "tools" / "generate_migration_classification_csv.py",
)
APP_HELPERS = _load_app_helpers(
    "_is_assembly_render_config",
    "_resolve_instance_render_assets",
    "_build_representable_interface",
)


class MigrationAssemblyTests(unittest.TestCase):
    def test_assembly_signature_is_primary_classification_key(self):
        actor = {
            "assembly_signature": "sha256:assembly-a",
            "static_mesh_asset": "/Game/WrongSingleAsset.WrongSingleAsset",
        }
        expected = "assembly_signature:sha256:assembly-a"
        self.assertEqual(MIGRATION._classification_key(actor), expected)
        self.assertEqual(CLASSIFICATION._group_key(actor), expected)

        unsigned = {"render_parts": [{"asset_path": "/Game/A.A"}]}
        fallback = "render_part.asset_path:/Game/A.A"
        self.assertEqual(MIGRATION._classification_key(unsigned), fallback)
        self.assertEqual(CLASSIFICATION._group_key(unsigned), fallback)

    def test_render_config_preserves_assembly_payload(self):
        parts = [{
            "asset_path": "/Game/Equipment/SM_A.SM_A",
            "relative_transform": {"tx": 1.25, "ry": 30.0, "sz": 0.5},
        }]
        unsupported = [{"component_type": "NiagaraComponent", "count": 2}]
        actor = {
            "source_actor_guids": ["mother", "child"],
            "render_parts": parts,
            "assembly_signature": "sig-a",
            "unsupported_components": unsupported,
        }

        config = MIGRATION._render_config_from_actor(
            actor,
            ["I3D_Representable", "I3D_Spatial"],
            "/Game/Equipment/SM_A.SM_A",
        )

        self.assertIs(config["render_parts"], parts)
        self.assertIs(config["unsupported_components"], unsupported)
        self.assertEqual(config["source_actor_guids"], ["mother", "child"])
        self.assertEqual(config["assembly_signature"], "sig-a")
        self.assertEqual(config["ue_asset_path"], "/Game/Equipment/SM_A.SM_A")

    def test_source_actor_deletion_set_includes_mother_and_deduplicates(self):
        actor = {
            "ext_guid": "mother",
            "source_actor_guids": ["mother", "child-a", "child-a", "child-b"],
        }
        self.assertEqual(
            MIGRATION._source_actor_guids(actor),
            ["mother", "child-a", "child-b"],
        )

    def test_result_has_canonical_fields_and_legacy_guid_aliases(self):
        result = MIGRATION._build_migration_result(
            {"mother": "ue_mother"},
            ["mother", "child"],
            {"mother": "ue_mother", "child": "ue_mother"},
        )
        self.assertEqual(result["schema_version"], "assembly_v1")
        self.assertEqual(result["instances"], {"mother": "ue_mother"})
        self.assertEqual(result["delete_actor_guids"], ["mother", "child"])
        self.assertEqual(result["blocked_actors"], [])
        self.assertEqual(result["mother"], "ue_mother")
        self.assertEqual(result["child"], "ue_mother")

    def test_dry_run_migrates_one_mother_as_one_composite_instance(self):
        class FakeStore:
            latest = None

            def __init__(self):
                self.active = {
                    "name": "ZHHZ",
                    "dataset": {},
                    # Keep this mapping truthy so migrate's dry-run path mutates
                    # the same in-memory collection that the fake store exposes.
                    "instances": {
                        "existing": {
                            "ext_guid": "existing",
                            "object_type_rid": "existing.type",
                        },
                    },
                }
                FakeStore.latest = self

            def get_active_id(self):
                return "zhhz"

            def get_active(self):
                return self.active

            def get_object_types(self):
                return {}

        actor = {
            "ext_guid": "mother",
            "name": "Group001",
            "source_actor_guids": ["mother", "child-a", "child-b"],
            "render_parts": [
                {"asset_path": "/Game/A.A", "relative_transform": {"tx": 0}},
                {"asset_path": "/Game/B.B", "relative_transform": {"tx": 5}},
            ],
            "assembly_signature": "sig-a",
            "unsupported_components": ["NiagaraComponent"],
            "transform": {"tx": 100, "rz": 45},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.json"
            mapping_path = Path(temp_dir) / "mapping.json"
            input_path.write_text(json.dumps({"actors": [actor]}), encoding="utf-8")
            mapping_path.write_text("{}", encoding="utf-8")
            old_store = MIGRATION.ProjectStore
            MIGRATION.ProjectStore = FakeStore
            try:
                result = MIGRATION.migrate(
                    str(input_path),
                    str(mapping_path),
                    dry_run=True,
                    allow_unsupported=True,
                )
            finally:
                MIGRATION.ProjectStore = old_store

        self.assertEqual(result["instances"], {"mother": "ue_mother"})
        self.assertEqual(result["delete_actor_guids"], ["mother", "child-a", "child-b"])
        self.assertEqual(result["child-a"], "ue_mother")
        instances = FakeStore.latest.active["instances"]
        self.assertIn("ue_mother", instances)
        config = instances["ue_mother"]["render_config"]
        self.assertEqual(config["render_parts"], actor["render_parts"])
        self.assertEqual(config["assembly_signature"], "sig-a")
        self.assertEqual(config["ue_asset_path"], "/Game/A.A")

    def test_unsupported_assembly_is_blocked_and_never_added_to_cleanup(self):
        class FakeStore:
            def __init__(self):
                self.active = {
                    "name": "ZHHZ",
                    "dataset": {},
                    "instances": {"existing": {"ext_guid": "existing"}},
                }

            def get_active_id(self):
                return "zhhz"

            def get_active(self):
                return self.active

            def get_object_types(self):
                return {}

        actor = {
            "ext_guid": "unsafe-mother",
            "name": "UnsafeGroup",
            "source_actor_guids": ["unsafe-mother", "unsafe-child"],
            "render_parts": [{"asset_path": "/Game/A.A"}],
            "unsupported_components": [{"kind": "instanced_static_mesh"}],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.json"
            mapping_path = Path(temp_dir) / "mapping.json"
            input_path.write_text(json.dumps({"actors": [actor]}), encoding="utf-8")
            mapping_path.write_text("{}", encoding="utf-8")
            old_store = MIGRATION.ProjectStore
            MIGRATION.ProjectStore = FakeStore
            try:
                result = MIGRATION.migrate(
                    str(input_path),
                    str(mapping_path),
                    dry_run=True,
                )
            finally:
                MIGRATION.ProjectStore = old_store

        self.assertEqual(result["instances"], {})
        self.assertEqual(result["delete_actor_guids"], [])
        self.assertNotIn("unsafe-mother", result)
        self.assertEqual(result["blocked_actors"][0]["ext_guid"], "unsafe-mother")

    def test_skip_classification_action_excludes_non_device(self):
        self.assertEqual(MIGRATION._classification_action({"action": " SKIP "}), "skip")
        self.assertEqual(MIGRATION._classification_action(None), "")

    def test_classification_csv_groups_assemblies_and_exposes_risks(self):
        actors = [
            {
                "ext_guid": "mother-a",
                "actor_label": "Group001",
                "assembly_signature": "same-geometry",
                "source_actor_guids": ["mother-a", "child-a"],
                "render_parts": [
                    {"asset_path": "/Game/A.A"},
                    {"asset_path": "/Game/B.B"},
                ],
                "unsupported_components": [
                    {"component_type": "NiagaraComponent", "count": 2},
                ],
            },
            {
                "ext_guid": "mother-b",
                "actor_label": "Group002",
                "assembly_signature": "same-geometry",
                "source_actor_guids": ["mother-b", "child-b"],
                "render_parts": [
                    {"asset_path": "/Game/A.A"},
                    {"asset_path": "/Game/B.B"},
                ],
            },
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.json"
            output_path = Path(temp_dir) / "classification.csv"
            input_path.write_text(json.dumps({"actors": actors}), encoding="utf-8")
            CLASSIFICATION.build(str(input_path), str(output_path))
            with output_path.open("r", encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["group_key"], "assembly_signature:same-geometry")
        self.assertEqual(row["count"], "2")
        self.assertEqual(row["render_part_count"], "2")
        self.assertEqual(row["total_render_part_count"], "4")
        self.assertEqual(row["source_actor_count"], "2")
        self.assertEqual(row["unsupported_component_count"], "2")
        self.assertEqual(row["unsupported_component_types"], "NiagaraComponent")
        self.assertIn("composite_assembly", row["risk_flags"])
        self.assertIn("unsupported_components", row["risk_flags"])

    def test_snapshot_representable_passes_assembly_fields_unchanged(self):
        parts = [{
            "asset_path": "/Game/A.A",
            "relative_transform": {"tx": 3.0, "rz": -90.0},
        }]
        config = {"render_parts": parts, "assembly_signature": "sig-a"}
        payload = APP_HELPERS["_build_representable_interface"](
            "/Game/A.A",
            "/Game/A.A",
            True,
            config,
        )
        self.assertIs(payload["render_parts"], parts)
        self.assertEqual(payload["assembly_signature"], "sig-a")
        self.assertTrue(APP_HELPERS["_is_assembly_render_config"](config))

        legacy = APP_HELPERS["_build_representable_interface"](
            "/Game/Legacy.Legacy",
            "/Game/Legacy.Legacy",
            True,
            {"asset_id": "/Game/Legacy.Legacy"},
        )
        self.assertNotIn("render_parts", legacy)
        self.assertNotIn("assembly_signature", legacy)

    def test_assembly_instance_assets_override_type_default(self):
        resolve = APP_HELPERS["_resolve_instance_render_assets"]
        raw = {"asset_id": "/Game/Raw.Raw"}
        object_type = {
            "asset_id": "type-model.glb",
            "ue_asset_path": "/Game/TypeDefault.TypeDefault",
        }
        config = {
            "asset_id": "/Game/AssemblyPrimary.AssemblyPrimary",
            "ue_asset_path": "/Game/AssemblyPrimary.AssemblyPrimary",
            "render_parts": [{"asset_path": "/Game/Part.Part"}],
        }
        self.assertEqual(
            resolve(raw, config, object_type, {}),
            (
                "/Game/AssemblyPrimary.AssemblyPrimary",
                "/Game/AssemblyPrimary.AssemblyPrimary",
            ),
        )
        self.assertEqual(
            resolve(raw, {"asset_id": "/Game/Old.Old"}, object_type, {}),
            ("type-model.glb", "/Game/TypeDefault.TypeDefault"),
        )


if __name__ == "__main__":
    unittest.main()
