#!/usr/bin/env python3
"""Read-only audit of 3ds Max group heads in a Datasmith scene.

The tool deliberately does not decide what should be migrated or deleted.  It
collects enough structure and mesh metadata to review each Max GroupHead, then
adds conservative heuristic labels that can be filtered by a human.

Only the Python standard library is used.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


SCHEMA_VERSION = "zhhz_datasmith_group_audit_v1"
ACTOR_TAGS = {"Actor", "ActorMesh"}
PACKAGE_ID_RE = re.compile(
    r"(?i)3d66-(?:[^\-\s\"<>]+-)*?(\d{5,})(?=-|$)"
)
THREED66_GROUP_RE = re.compile(r"(?i)^3d66group\d+(?:_\d+)?$")
KNOWN_WRAPPER_RE = re.compile(
    r"(?i)^(?:3d|root|scene|world|model|all|objects?|geometry|container|"
    r"模型|场景|全部|总图|建筑|结构|外壳|场地|场馆|展馆|主体)$"
)


def _utc_iso(timestamp: float | None = None) -> str:
    if timestamp is None:
        value = datetime.now(timezone.utc)
    else:
        value = datetime.fromtimestamp(timestamp, timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _tag_values(element: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    for tag in element.findall("tag"):
        raw = tag.get("value", "")
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def _is_group_head(element: ET.Element) -> bool:
    return _tag_values(element).get("Max.isGroupHead", "").lower() == "true"


def _as_bool(value: str | None) -> bool:
    return (value or "").strip().lower() == "true"


def _sort_handles(values: Iterable[str]) -> list[str]:
    def key(value: str) -> tuple[int, int | str]:
        return (0, int(value)) if value.isdigit() else (1, value.casefold())

    return sorted(set(values), key=key)


def _sorted_strings(values: Iterable[str]) -> list[str]:
    return sorted({value for value in values if value}, key=str.casefold)


def _extract_package_ids(values: Iterable[str]) -> list[str]:
    found: set[str] = set()
    for value in values:
        found.update(PACKAGE_ID_RE.findall(value or ""))
    return _sort_handles(found)


def _child_actors(element: ET.Element) -> list[ET.Element]:
    children = element.find("children")
    if children is None:
        return []
    return [child for child in children if child.tag in ACTOR_TAGS]


def _descendant_actors(element: ET.Element) -> Iterable[ET.Element]:
    for child in _child_actors(element):
        yield child
        yield from _descendant_actors(child)


def _element_handle(element: ET.Element, tags: dict[str, str] | None = None) -> str:
    values = tags if tags is not None else _tag_values(element)
    return values.get("Max.handle") or element.get("name", "")


def _mesh_asset_catalog(root: ET.Element) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for static_mesh in root.findall("StaticMesh"):
        name = static_mesh.get("name", "")
        size_element = static_mesh.find("Size")
        hash_element = static_mesh.find("Hash")
        materials = [
            {"id": material.get("id", ""), "name": material.get("name", "")}
            for material in static_mesh.findall("Material")
        ]
        result[name] = {
            "name": name,
            "label": static_mesh.get("label", ""),
            "file": (
                static_mesh.find("file").get("path", "")
                if static_mesh.find("file") is not None
                else ""
            ),
            "size": dict(size_element.attrib) if size_element is not None else {},
            "hash": hash_element.get("value", "") if hash_element is not None else "",
            "materials": materials,
        }
    return result


def _actor_mesh_record(
    element: ET.Element, assets: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    tags = _tag_values(element)
    mesh_reference = element.find("mesh")
    asset_name = mesh_reference.get("name", "") if mesh_reference is not None else ""
    asset = assets.get(
        asset_name,
        {
            "name": asset_name,
            "label": "",
            "file": "",
            "size": {},
            "hash": "",
            "materials": [],
        },
    )
    transform = element.find("Transform")
    package_inputs = [element.get("label", ""), asset.get("label", "")]
    package_inputs.extend(material.get("name", "") for material in asset["materials"])
    return {
        "handle": _element_handle(element, tags),
        "name": element.get("name", ""),
        "label": element.get("label", ""),
        "layer": element.get("layer", ""),
        "parent_handle": tags.get("Max.parent.handle", ""),
        "asset_name": asset_name,
        "asset_label": asset.get("label", ""),
        "asset_file": asset.get("file", ""),
        "size": asset.get("size", {}),
        "hash": asset.get("hash", ""),
        "materials": asset.get("materials", []),
        "source_package_ids": _extract_package_ids(package_inputs),
        "transform": dict(transform.attrib) if transform is not None else {},
    }


def _geometry_signature(meshes: Sequence[dict[str, Any]]) -> str | None:
    """Return an order-independent signature of descendant mesh geometry.

    Datasmith's StaticMesh/Hash is stable for identical exported geometry.  A
    sorted multiset (duplicates retained) makes repeated assemblies cluster even
    when they have different world transforms.  The fallback is only used for a
    malformed export with a missing Hash.
    """

    if not meshes:
        return None
    tokens: list[str] = []
    for mesh in meshes:
        geometry_hash = mesh.get("hash", "")
        if geometry_hash:
            tokens.append(f"hash:{geometry_hash}")
            continue
        fallback = {
            "asset_name": mesh.get("asset_name", ""),
            "asset_label": mesh.get("asset_label", ""),
            "size": mesh.get("size", {}),
        }
        tokens.append(
            "fallback:"
            + json.dumps(fallback, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        )
    payload = "\n".join(sorted(tokens)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _initial_group_record(
    element: ET.Element,
    ancestors: Sequence[ET.Element],
    assets: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    tags = _tag_values(element)
    actor_ancestors = [ancestor for ancestor in ancestors if ancestor.tag in ACTOR_TAGS]
    group_ancestors = [ancestor for ancestor in actor_ancestors if _is_group_head(ancestor)]
    direct_actor_children = _child_actors(element)
    direct_groups = [child for child in direct_actor_children if _is_group_head(child)]
    recursive_actors = list(_descendant_actors(element))
    recursive_groups = [child for child in recursive_actors if _is_group_head(child)]
    direct_mesh_elements = [child for child in direct_actor_children if child.tag == "ActorMesh"]
    descendant_mesh_elements = [child for child in recursive_actors if child.tag == "ActorMesh"]
    meshes = [_actor_mesh_record(mesh, assets) for mesh in descendant_mesh_elements]

    def group_ref(group: ET.Element) -> dict[str, str]:
        return {
            "handle": _element_handle(group),
            "label": group.get("label", ""),
        }

    package_inputs = [element.get("label", "")]
    package_inputs.extend(mesh["label"] for mesh in meshes)
    package_inputs.extend(mesh["asset_label"] for mesh in meshes)
    for mesh in meshes:
        package_inputs.extend(material["name"] for material in mesh["materials"])

    materials = _sorted_strings(
        material["name"] for mesh in meshes for material in mesh["materials"]
    )
    hashes = _sorted_strings(mesh["hash"] for mesh in meshes)
    layers = _sorted_strings(
        [element.get("layer", "")]
        + [actor.get("layer", "") for actor in recursive_actors]
    )
    signature = _geometry_signature(meshes)
    transform = element.find("Transform")
    return {
        "handle": _element_handle(element, tags),
        "name": element.get("name", ""),
        "label": element.get("label", ""),
        "actor_tag": element.tag,
        "layer": element.get("layer", ""),
        "layers": layers,
        "parent_handle": tags.get("Max.parent.handle", ""),
        "is_group_member": _as_bool(tags.get("Max.isGroupMember")),
        "actor_depth": len(actor_ancestors),
        "group_depth": len(group_ancestors),
        "ancestor_handles": [_element_handle(ancestor) for ancestor in actor_ancestors],
        "ancestor_labels": [ancestor.get("label", "") for ancestor in actor_ancestors],
        "ancestor_group_handles": [_element_handle(group) for group in group_ancestors],
        "ancestor_group_labels": [group.get("label", "") for group in group_ancestors],
        "direct_group_count": len(direct_groups),
        "direct_groups": [group_ref(group) for group in direct_groups],
        "recursive_group_count": len(recursive_groups),
        "recursive_groups": [group_ref(group) for group in recursive_groups],
        "direct_mesh_count": len(direct_mesh_elements),
        "descendant_mesh_count": len(meshes),
        "mesh_labels": [mesh["label"] for mesh in meshes],
        "source_package_ids": _extract_package_ids(package_inputs),
        "materials": materials,
        "hashes": hashes,
        "geometry_signature": signature,
        "geometry_cluster_id": signature[:16] if signature else None,
        "duplicate_cluster_size": 0,
        "transform": dict(transform.attrib) if transform is not None else {},
        "heuristic_class": "unclassified",
        "heuristic_score": 0,
        "heuristic_reasons": [],
        "meshes": meshes,
    }


def _walk_actor_tree(
    element: ET.Element,
    ancestors: Sequence[ET.Element],
    assets: dict[str, dict[str, Any]],
    groups: list[dict[str, Any]],
) -> None:
    if _is_group_head(element):
        groups.append(_initial_group_record(element, ancestors, assets))
    next_ancestors = [*ancestors, element]
    for child in _child_actors(element):
        _walk_actor_tree(child, next_ancestors, assets, groups)


def _classify_groups(groups: list[dict[str, Any]]) -> None:
    wrapper_handles: set[str] = set()
    for group in groups:
        label = group["label"].strip()
        reasons: list[str] = []
        if KNOWN_WRAPPER_RE.fullmatch(label):
            reasons.append("名称命中常见场景包装层")
        if group["direct_group_count"] >= 8:
            reasons.append("直属母组数量较多")
        if group["recursive_group_count"] >= 20 and group["direct_mesh_count"] <= 2:
            reasons.append("主要用于容纳多层子组")
        if group["descendant_mesh_count"] >= 500:
            reasons.append("后代网格数量极大")
        if (
            group["descendant_mesh_count"] >= 100
            and group["direct_group_count"] >= 5
            and group["direct_mesh_count"] <= 2
        ):
            reasons.append("网格多且直属内容以子组为主")
        if reasons:
            wrapper_handles.add(group["handle"])
            group["heuristic_class"] = "wrapper_group"
            group["heuristic_score"] = -len(reasons)
            group["heuristic_reasons"] = reasons

    for group in groups:
        if group["heuristic_class"] == "wrapper_group":
            continue
        if group["descendant_mesh_count"] == 0:
            group["heuristic_class"] = "empty_group"
            group["heuristic_score"] = 0
            group["heuristic_reasons"] = ["没有后代网格"]
            continue

        reasons = []
        score = 0
        if THREED66_GROUP_RE.fullmatch(group["label"].strip()):
            score += 3
            reasons.append("名称符合 3d66Group 编号组")
        if group["source_package_ids"]:
            score += 2
            reasons.append("后代网格可追溯到 3d66 源包")
        if 1 <= group["descendant_mesh_count"] <= 200:
            score += 2
            reasons.append("后代网格数量处于设备组合常见范围")
        if group["recursive_group_count"] <= 2:
            score += 1
            reasons.append("内部子组层级较少")
        nearest_group_handle = (
            group["ancestor_group_handles"][-1]
            if group["ancestor_group_handles"]
            else ""
        )
        if nearest_group_handle in wrapper_handles:
            score += 1
            reasons.append("直属于启发式包装组")
        if group["group_depth"] >= 2:
            score -= 2
            reasons.append("嵌套在两层或更多母组内")
            group["heuristic_class"] = "nested_component_group"
        elif score >= 3:
            group["heuristic_class"] = "candidate_equipment_group"
        else:
            group["heuristic_class"] = "ambiguous_group"
            reasons.append("证据不足，需人工确认")
        group["heuristic_score"] = score
        group["heuristic_reasons"] = reasons


def analyze_datasmith(input_path: Path) -> dict[str, Any]:
    input_path = input_path.resolve()
    tree = ET.parse(input_path)
    root = tree.getroot()
    if root.tag != "DatasmithUnrealScene":
        raise ValueError(f"Expected DatasmithUnrealScene, got {root.tag!r}")

    assets = _mesh_asset_catalog(root)
    groups: list[dict[str, Any]] = []
    actor_roots = [child for child in root if child.tag in ACTOR_TAGS]
    for actor in actor_roots:
        _walk_actor_tree(actor, [], assets, groups)

    signature_counts = Counter(
        group["geometry_signature"]
        for group in groups
        if group["geometry_signature"] is not None
    )
    for group in groups:
        signature = group["geometry_signature"]
        group["duplicate_cluster_size"] = signature_counts.get(signature, 0)

    _classify_groups(groups)
    groups.sort(
        key=lambda group: (
            0 if str(group["handle"]).isdigit() else 1,
            int(group["handle"]) if str(group["handle"]).isdigit() else group["handle"],
        )
    )

    actor_count = 0
    actor_mesh_count = 0
    for actor in root.iter():
        if actor.tag in ACTOR_TAGS:
            actor_count += 1
            if actor.tag == "ActorMesh":
                actor_mesh_count += 1
    class_counts = Counter(group["heuristic_class"] for group in groups)
    layer_counts = Counter(group["layer"] for group in groups)
    source_packages = _sort_handles(
        package_id for group in groups for package_id in group["source_package_ids"]
    )
    duplicate_cluster_sizes = [count for count in signature_counts.values() if count > 1]
    input_stat = input_path.stat()
    application = root.find("Application")
    summary = {
        "static_mesh_asset_count": len(assets),
        "actor_count": actor_count,
        "actor_mesh_count": actor_mesh_count,
        "group_head_count": len(groups),
        "groups_with_meshes": sum(group["descendant_mesh_count"] > 0 for group in groups),
        "empty_group_count": sum(group["descendant_mesh_count"] == 0 for group in groups),
        "geometry_cluster_count": len(signature_counts),
        "duplicate_geometry_cluster_count": len(duplicate_cluster_sizes),
        "groups_in_duplicate_clusters": sum(duplicate_cluster_sizes),
        "largest_duplicate_cluster_size": max(duplicate_cluster_sizes, default=1),
        "heuristic_class_counts": dict(sorted(class_counts.items())),
        "group_layer_counts": dict(sorted(layer_counts.items(), key=lambda item: item[0].casefold())),
        "source_package_id_count": len(source_packages),
        "source_package_ids": source_packages,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_iso(),
        "read_only_audit": True,
        "decision_notice": (
            "heuristic_class is review assistance only; it does not authorize migration or deletion"
        ),
        "source": {
            "path": str(input_path),
            "bytes": input_stat.st_size,
            "modified_at_utc": _utc_iso(input_stat.st_mtime),
            "datasmith_version": root.findtext("Version", default=""),
            "sdk_version": root.findtext("SDKVersion", default=""),
            "host": root.findtext("Host", default=""),
            "application": dict(application.attrib) if application is not None else {},
            "resource_path": root.findtext("ResourcePath", default=""),
        },
        "summary": summary,
        "groups": groups,
    }


CSV_FIELDS = [
    "handle",
    "name",
    "label",
    "actor_tag",
    "layer",
    "layers",
    "parent_handle",
    "is_group_member",
    "actor_depth",
    "group_depth",
    "ancestor_handles",
    "ancestor_labels",
    "ancestor_group_handles",
    "ancestor_group_labels",
    "direct_group_count",
    "direct_groups",
    "recursive_group_count",
    "recursive_groups",
    "direct_mesh_count",
    "descendant_mesh_count",
    "mesh_labels",
    "source_package_ids",
    "materials",
    "sizes",
    "hashes",
    "geometry_signature",
    "geometry_cluster_id",
    "duplicate_cluster_size",
    "heuristic_class",
    "heuristic_score",
    "heuristic_reasons",
]


def _pipe(values: Iterable[Any]) -> str:
    return " | ".join(str(value) for value in values)


def _group_refs(values: Sequence[dict[str, str]]) -> str:
    return _pipe(f"{item['handle']}:{item['label']}" for item in values)


def _mesh_sizes(meshes: Sequence[dict[str, Any]]) -> str:
    rows = []
    for mesh in meshes:
        size = mesh["size"]
        rendered = ",".join(f"{key}={size[key]}" for key in ("a", "x", "y", "z") if key in size)
        rows.append(f"{mesh['handle']}:{mesh['label']}[{rendered}]")
    return _pipe(rows)


def _mesh_hashes(meshes: Sequence[dict[str, Any]]) -> str:
    return _pipe(f"{mesh['handle']}:{mesh['label']}={mesh['hash']}" for mesh in meshes)


def write_json(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def write_csv(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for group in report["groups"]:
            row = dict(group)
            for key in (
                "layers",
                "ancestor_handles",
                "ancestor_labels",
                "ancestor_group_handles",
                "ancestor_group_labels",
                "mesh_labels",
                "source_package_ids",
                "materials",
                "heuristic_reasons",
            ):
                row[key] = _pipe(group[key])
            row["direct_groups"] = _group_refs(group["direct_groups"])
            row["recursive_groups"] = _group_refs(group["recursive_groups"])
            row["sizes"] = _mesh_sizes(group["meshes"])
            row["hashes"] = _mesh_hashes(group["meshes"])
            writer.writerow(row)


SELF_TEST_XML = """<?xml version="1.0" encoding="utf-8"?>
<DatasmithUnrealScene>
  <Version>test</Version>
  <SDKVersion>test-sdk</SDKVersion>
  <StaticMesh name="mesh-a" label="3d66-Editable_Poly-22561678-001">
    <file path="fixture/a.udsmesh"/>
    <Size a="1" x="2" y="3" z="4"/>
    <Hash value="aaaaaaaa"/>
    <Material id="1" name="3d66-Standardmaterial-22561678-001"/>
  </StaticMesh>
  <StaticMesh name="mesh-b" label="3d66-Editable_Poly-22561678-002">
    <file path="fixture/b.udsmesh"/>
    <Size a="5" x="6" y="7" z="8"/>
    <Hash value="bbbbbbbb"/>
    <Material id="1" name="FixtureMaterial"/>
  </StaticMesh>
  <Actor name="100" label="3D" layer="0">
    <tag value="Max.handle: 100"/>
    <tag value="Max.isGroupHead: true"/>
    <tag value="Max.isGroupMember: false"/>
    <tag value="Max.parent.handle: 0"/>
    <children>
      <Actor name="200" label="3d66Group250" layer="Layer01">
        <tag value="Max.handle: 200"/>
        <tag value="Max.isGroupHead: true"/>
        <tag value="Max.isGroupMember: true"/>
        <tag value="Max.parent.handle: 100"/>
        <children>
          <ActorMesh name="201" label="3d66-Editable_Poly-22561678-001" layer="Layer01">
            <mesh name="mesh-a"/><tag value="Max.handle: 201"/>
            <tag value="Max.isGroupHead: false"/><tag value="Max.parent.handle: 200"/>
          </ActorMesh>
          <ActorMesh name="202" label="3d66-Editable_Poly-22561678-002" layer="Layer01">
            <mesh name="mesh-b"/><tag value="Max.handle: 202"/>
            <tag value="Max.isGroupHead: false"/><tag value="Max.parent.handle: 200"/>
          </ActorMesh>
        </children>
      </Actor>
      <Actor name="300" label="3d66Group251" layer="Layer01">
        <tag value="Max.handle: 300"/>
        <tag value="Max.isGroupHead: true"/>
        <tag value="Max.isGroupMember: true"/>
        <tag value="Max.parent.handle: 100"/>
        <children>
          <ActorMesh name="301" label="3d66-Editable_Poly-22561678-003" layer="Layer01">
            <mesh name="mesh-a"/><tag value="Max.handle: 301"/>
            <tag value="Max.isGroupHead: false"/><tag value="Max.parent.handle: 300"/>
          </ActorMesh>
          <ActorMesh name="302" label="3d66-Editable_Poly-22561678-004" layer="Layer01">
            <mesh name="mesh-b"/><tag value="Max.handle: 302"/>
            <tag value="Max.isGroupHead: false"/><tag value="Max.parent.handle: 300"/>
          </ActorMesh>
        </children>
      </Actor>
    </children>
  </Actor>
</DatasmithUnrealScene>
"""


def run_self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="zhhz-datasmith-selftest-") as directory:
        root = Path(directory)
        input_path = root / "fixture.udatasmith"
        json_path = root / "audit.json"
        csv_path = root / "audit.csv"
        input_path.write_text(SELF_TEST_XML, encoding="utf-8")
        report = analyze_datasmith(input_path)
        write_json(report, json_path)
        write_csv(report, csv_path)
        groups = {group["handle"]: group for group in report["groups"]}
        assert report["summary"]["group_head_count"] == 3
        assert groups["100"]["heuristic_class"] == "wrapper_group"
        assert groups["200"]["ancestor_labels"] == ["3D"]
        assert groups["200"]["source_package_ids"] == ["22561678"]
        assert groups["200"]["descendant_mesh_count"] == 2
        assert groups["200"]["geometry_signature"] == groups["300"]["geometry_signature"]
        assert groups["200"]["duplicate_cluster_size"] == 2
        assert groups["200"]["heuristic_class"] == "candidate_equipment_group"
        assert json.loads(json_path.read_text(encoding="utf-8"))["schema_version"] == SCHEMA_VERSION
        with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
            assert len(list(csv.DictReader(stream))) == 3
    print("self-test passed: hierarchy, 3d66 package extraction, signatures, JSON and CSV")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Max GroupHead assemblies in a Datasmith .udatasmith XML file."
    )
    parser.add_argument("--input", type=Path, help="Input .udatasmith XML (read only)")
    parser.add_argument("--output-json", type=Path, help="Detailed JSON audit output")
    parser.add_argument("--output-csv", type=Path, help="Flattened UTF-8 BOM CSV audit output")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run an isolated temporary-XML self-test and exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        run_self_test()
        return 0
    if args.input is None or args.output_json is None or args.output_csv is None:
        parser.error("--input, --output-json and --output-csv are required unless --self-test is used")
    input_path = args.input.resolve()
    output_json = args.output_json.resolve()
    output_csv = args.output_csv.resolve()
    if not input_path.is_file():
        parser.error(f"input file does not exist: {input_path}")
    if input_path in {output_json, output_csv}:
        parser.error("output path must not overwrite the input Datasmith file")

    report = analyze_datasmith(input_path)
    write_json(report, output_json)
    write_csv(report, output_csv)
    summary = report["summary"]
    print(
        "audit complete: "
        f"groups={summary['group_head_count']}, "
        f"meshes={summary['actor_mesh_count']}, "
        f"geometry_clusters={summary['geometry_cluster_count']}, "
        f"largest_duplicate_cluster={summary['largest_duplicate_cluster_size']}"
    )
    print(f"json: {output_json}")
    print(f"csv:  {output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
