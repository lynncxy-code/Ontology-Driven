#!/usr/bin/env python3
"""Build the Git-tracked ontology registry for the ZHHZ UE migration.

The shared properties and I3D interface identities are copied from the
existing OntoTwin registry.  ZHHZ object/property identities are UUIDv5 so a
clean rebuild produces the same RIDs without depending on database state.

Run from any directory after this file is deployed under ``backend/tools``::

    python -m tools.build_zhhz_migration_registry

By default the two artifacts are written to ``backend/ontology_registry`` and
validated with the unmodified vendored Lingshu generator before publication.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Iterable


DATASET_ID = "ds_1784694647848"
TEMPLATE_DATASET_ID = "ds_1783048237433"
REGISTRY_VERSION = "ontotwin-3.4.0"
SOURCE = "ue_migration:ZHHZ"
ORIGIN = "ontotwin"

# A namespace owned by this migration generator.  The namespace and name
# formats below are persistence contracts: changing either would reissue RIDs.
RID_NAMESPACE = uuid.UUID("64d740ec-56ca-5f7d-8c71-331bf90c19b7")

INTERFACE_API_NAMES = (
    "i3d_representable",
    "i3d_spatial",
)

# (block id, registry api_name, Chinese display name)
ZHHZ_TYPES = (
    ("zhhz.fixed_wing_aircraft", "zhhz_fixed_wing_aircraft", "固定翼航空器"),
    ("zhhz.rotorcraft", "zhhz_rotorcraft", "旋翼航空器"),
    ("zhhz.unmanned_new_aircraft", "zhhz_unmanned_new_aircraft", "无人/新型航空器"),
    ("zhhz.aviation_weapon", "zhhz_aviation_weapon", "航空武器/弹药"),
    ("zhhz.avionics_sensor", "zhhz_avionics_sensor", "航电/传感器/对抗设备"),
    ("zhhz.cockpit_simulator", "zhhz_cockpit_simulator", "座舱/模拟训练系统"),
    ("zhhz.display_control_terminal", "zhhz_display_control_terminal", "触控与操作终端"),
    ("zhhz.aircraft_component", "zhhz_aircraft_component", "航空部件/子系统"),
)


def _backend_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def default_template_path() -> Path:
    return (
        _backend_dir()
        / "ontology_registry"
        / f"ontotwin.{TEMPLATE_DATASET_ID}.ontology.json"
    )


def default_output_dir() -> Path:
    return _backend_dir() / "ontology_registry"


def default_lingshu_dir() -> Path:
    return _backend_dir() / "tools" / "lingshu"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"registry root must be an object: {path}")
    return value


def _index_by_api_name(
    section: dict[str, Any], section_name: str
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for rid, value in section.items():
        if not isinstance(value, dict):
            raise ValueError(f"{section_name}.{rid} must be an object")
        api_name = value.get("api_name")
        if not isinstance(api_name, str) or not api_name:
            raise ValueError(f"{section_name}.{rid} has no api_name")
        if api_name in index:
            raise ValueError(f"duplicate {section_name} api_name: {api_name}")
        index[api_name] = value
    return index


def _uuid5_rid(prefix: str, identity: str) -> str:
    return f"{prefix}{uuid.uuid5(RID_NAMESPACE, identity)}"


def object_rid(block_id: str) -> str:
    return _uuid5_rid("ri.obj.", f"{DATASET_ID}:object:{block_id}")


def property_rid(block_id: str, property_api_name: str) -> str:
    return _uuid5_rid(
        "ri.prop.",
        f"{DATASET_ID}:object:{block_id}:property:{property_api_name}",
    )


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _select_i3d_contract(
    template: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    shared_section = template.get("shared_property_types")
    interface_section = template.get("interface_types")
    if not isinstance(shared_section, dict) or not isinstance(interface_section, dict):
        raise ValueError("template must contain shared_property_types and interface_types")

    shared_by_api = _index_by_api_name(shared_section, "shared_property_types")
    interfaces_by_api = _index_by_api_name(interface_section, "interface_types")

    try:
        instance_id = shared_by_api["instance_id"]
        selected_interfaces = [interfaces_by_api[name] for name in INTERFACE_API_NAMES]
    except KeyError as exc:
        raise ValueError(f"template is missing required I3D contract entry: {exc.args[0]}") from exc

    selected_interface_rids = {entry["rid"] for entry in selected_interfaces}
    for entry in selected_interfaces:
        parent_rids = entry.get("extends_interface_type_rids", [])
        if not isinstance(parent_rids, list):
            raise ValueError(
                f"interface {entry.get('api_name')} extends_interface_type_rids must be a list"
            )
        missing_parents = set(parent_rids) - selected_interface_rids
        if missing_parents:
            raise ValueError(
                f"selected interface {entry.get('api_name')} depends on omitted interface(s): "
                + ", ".join(sorted(missing_parents))
            )

    needed_shared_rids = _dedupe(
        [instance_id["rid"]]
        + [
            rid
            for interface in selected_interfaces
            for rid in interface.get("required_shared_property_type_rids", [])
        ]
    )
    missing_shared_rids = [rid for rid in needed_shared_rids if rid not in shared_section]
    if missing_shared_rids:
        raise ValueError(
            "template interface references unknown shared property RID(s): "
            + ", ".join(missing_shared_rids)
        )

    selected_shared = {
        rid: copy.deepcopy(shared_section[rid]) for rid in needed_shared_rids
    }
    selected_interface_map = {
        entry["rid"]: copy.deepcopy(entry) for entry in selected_interfaces
    }
    return selected_shared, selected_interface_map, needed_shared_rids


def build_registry(template: dict[str, Any]) -> dict[str, Any]:
    """Return the ZHHZ registry without mutating *template*."""

    shared, interfaces, required_shared_rids = _select_i3d_contract(template)
    shared_by_rid = shared
    interface_by_api = {
        entry["api_name"]: entry for entry in interfaces.values()
    }
    implemented_interface_rids = [
        interface_by_api[name]["rid"] for name in INTERFACE_API_NAMES
    ]

    objects: dict[str, Any] = {}
    for block_id, api_name, display_name in ZHHZ_TYPES:
        rid = object_rid(block_id)
        properties: dict[str, Any] = {}
        for shared_rid in required_shared_rids:
            shared_property = shared_by_rid[shared_rid]
            property_api_name = shared_property["api_name"]
            prop_rid = property_rid(block_id, property_api_name)
            properties[property_api_name] = {
                "rid": prop_rid,
                "api_name": property_api_name,
                "display_name": shared_property["display_name"],
                "lifecycle_status": "ACTIVE",
                "data_type": shared_property["data_type"],
                "inherit_from_shared_property_type_rid": shared_rid,
            }

        objects[rid] = {
            "rid": rid,
            "api_name": api_name,
            "display_name": display_name,
            "description": (
                f"ZHHZ UE 历史场景设备迁移类型（{block_id}）；"
                "人工验收前保持 EXPERIMENTAL。"
            ),
            "lifecycle_status": "EXPERIMENTAL",
            "property_types": properties,
            "implements_interface_type_rids": implemented_interface_rids,
            "primary_key_property_type_rids": [properties["instance_id"]["rid"]],
        }

    return {
        "version": template.get("version", REGISTRY_VERSION),
        "shared_property_types": shared,
        "interface_types": interfaces,
        "object_types": objects,
        "link_types": {},
        "action_types": {},
    }


def build_extensions_cypher(registry: dict[str, Any]) -> str:
    object_by_api = {
        value["api_name"]: value
        for value in registry.get("object_types", {}).values()
    }
    statements = [
        "// OntoTwin ZHHZ UE 迁移扩展属性（x_ 前缀）；官方生成器重灌不会覆盖",
        "",
    ]
    for block_id, api_name, _display_name in ZHHZ_TYPES:
        obj = object_by_api[api_name]
        statements.extend(
            [
                f"MATCH (n:ObjectType {{rid: {json.dumps(obj['rid'])}}})",
                "SET n.x_block_name = %s, n.x_source = %s, n.x_origin = %s;"
                % (
                    json.dumps(block_id, ensure_ascii=False),
                    json.dumps(SOURCE, ensure_ascii=False),
                    json.dumps(ORIGIN, ensure_ascii=False),
                ),
                "",
            ]
        )
    return "\n".join(statements).rstrip() + "\n"


def validate_with_lingshu(registry_path: Path, lingshu_dir: Path) -> None:
    """Run the vendored, unmodified validator/generator against an artifact."""

    generator = lingshu_dir / "generate_ontology_cypher.py"
    schema = lingshu_dir / "ontology.schema.json"
    rules = lingshu_dir / "ontology_rules.py"
    missing = [path for path in (generator, schema, rules) if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "vendored Lingshu toolchain is incomplete: "
            + ", ".join(str(path) for path in missing)
        )

    with tempfile.TemporaryDirectory(prefix="zhhz-lingshu-") as temp_dir:
        generated_cypher = Path(temp_dir) / "generated.cypher"
        process = subprocess.run(
            [
                sys.executable,
                str(generator),
                str(registry_path),
                "--schema",
                str(schema),
                "--output",
                str(generated_cypher),
            ],
            cwd=str(lingshu_dir),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        if process.returncode != 0:
            details = (process.stderr or process.stdout).strip()
            raise RuntimeError(f"Lingshu validation failed:\n{details}")
        if not generated_cypher.is_file() or generated_cypher.stat().st_size == 0:
            raise RuntimeError("Lingshu generator succeeded without producing Cypher")


def generate_artifacts(
    template_path: Path,
    output_dir: Path,
    lingshu_dir: Path | None,
) -> tuple[Path, Path]:
    """Build, validate, and atomically publish both registry artifacts."""

    template = _load_json(template_path)
    registry = build_registry(template)
    extensions = build_extensions_cypher(registry)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_name = f"ontotwin.{DATASET_ID}.ontology.json"
    extensions_name = f"ontotwin.{DATASET_ID}.extensions.cypher"
    final_json = output_dir / json_name
    final_extensions = output_dir / extensions_name

    with tempfile.TemporaryDirectory(prefix=".zhhz-registry-", dir=output_dir) as temp_dir:
        temp_root = Path(temp_dir)
        temp_json = temp_root / json_name
        temp_extensions = temp_root / extensions_name
        temp_json.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temp_extensions.write_text(extensions, encoding="utf-8")
        if lingshu_dir is not None:
            validate_with_lingshu(temp_json, lingshu_dir)
        os.replace(temp_json, final_json)
        os.replace(temp_extensions, final_extensions)

    return final_json, final_extensions


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the ZHHZ UE migration ontology registry."
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=default_template_path(),
        help="source registry whose shared/interface RIDs are reused",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(),
        help="artifact directory (default: backend/ontology_registry)",
    )
    parser.add_argument(
        "--lingshu-dir",
        type=Path,
        default=default_lingshu_dir(),
        help="vendored tools/lingshu directory used for validation",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="publish without running the vendored validator (tests only)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        json_path, extensions_path = generate_artifacts(
            args.template.resolve(),
            args.output_dir.resolve(),
            None if args.skip_validation else args.lingshu_dir.resolve(),
        )
    except (FileNotFoundError, OSError, ValueError, RuntimeError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    registry = _load_json(json_path)
    print(
        f"项目 {DATASET_ID}: 共享属性 {len(registry['shared_property_types'])} | "
        f"接口 {len(registry['interface_types'])} | 类型 {len(registry['object_types'])}"
    )
    print(f"registry → {json_path}")
    print(f"扩展属性 → {extensions_path}")
    if not args.skip_validation:
        print("Lingshu schema/semantic validation → PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
