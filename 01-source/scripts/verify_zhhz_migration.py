"""Read-only end-to-end verification for the ZHHZ assembly_v1 migration."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import urllib.request


TYPE_NAMES = {
    "fixed_wing_aircraft": "固定翼航空器",
    "rotorcraft": "旋翼航空器",
    "unmanned_new_aircraft": "无人/新型航空器",
    "aviation_weapon": "航空武器/弹药",
    "avionics_sensor": "航电/传感器/对抗设备",
    "cockpit_simulator": "座舱/模拟训练系统",
    "display_control_terminal": "显示与操控终端",
    "aircraft_component": "航空部件/子系统",
}

HIERARCHY_NAMES = {
    "fixed_wing_aircraft": "固定翼航空器",
    "rotorcraft": "旋翼航空器",
    "unmanned_new_aircraft": "无人及新型航空器",
    "aviation_weapon": "航空武器与弹药",
    "avionics_sensor": "航电、传感器与对抗设备",
    "cockpit_simulator": "座舱与模拟训练系统",
    "display_control_terminal": "显示与操控终端",
    "aircraft_component": "航空部件与子系统",
}


def _normalize_guid(value):
    return "".join(
        character for character in str(value or "").upper()
        if character in "0123456789ABCDEF"
    )


def _instance_id(guid):
    return "ue_" + re.sub(r"[^0-9A-Za-z_-]", "", str(guid))


def _get_json(base_url, path, headers=None):
    request = urllib.request.Request(base_url.rstrip("/") + path, headers=headers or {})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _assert_close(actual, expected, context):
    if not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=1e-7):
        raise AssertionError(f"{context}: expected {expected!r}, got {actual!r}")


def verify(base_url, export_path, selection_path, classification_path, result_path):
    with open(export_path, "r", encoding="utf-8") as stream:
        export = json.load(stream)
    actors = export.get("actors") or []
    with open(selection_path, "r", encoding="utf-8-sig", newline="") as stream:
        selection = list(csv.DictReader(stream))
    with open(classification_path, "r", encoding="utf-8-sig", newline="") as stream:
        classification = list(csv.DictReader(stream))
    with open(result_path, "r", encoding="utf-8") as stream:
        result = json.load(stream)

    selected_by_guid = {
        _normalize_guid(row.get("ue_guid")): row for row in selection
    }
    if len(selected_by_guid) != len(selection):
        raise AssertionError("Selection contains invalid or duplicate UE GUIDs")
    actors_by_instance = {}
    for actor in actors:
        guid = _normalize_guid(actor.get("ext_guid"))
        selected = selected_by_guid.get(guid)
        if selected is None:
            raise AssertionError(f"Export Actor absent from selection: {actor.get('ext_guid')}")
        actors_by_instance[_instance_id(actor["ext_guid"])] = (actor, selected)
    if len(actors_by_instance) != len(actors) or len(actors) != len(selection):
        raise AssertionError("Export, selection, and instance identifiers are not one-to-one")

    expected_count = len(actors)
    datasets = _get_json(base_url, "/api/v2/ontology/datasets")
    active = [dataset for dataset in datasets if dataset.get("is_active")]
    if len(active) != 1 or active[0].get("id") != "ds_1784694647848":
        raise AssertionError(f"Unexpected active dataset: {active!r}")
    if active[0].get("type_count") != len(TYPE_NAMES):
        raise AssertionError(f"Unexpected dataset type count: {active[0].get('type_count')}")
    if active[0].get("instance_count") != expected_count:
        raise AssertionError(
            f"Unexpected dataset instance count: {active[0].get('instance_count')}"
        )

    types = _get_json(base_url, "/api/v2/ontology/types")
    expected_types = {f"zhhz.{key}": value for key, value in TYPE_NAMES.items()}
    actual_types = {entry.get("rid"): entry for entry in types}
    if set(actual_types) != set(expected_types):
        raise AssertionError(
            f"Object type IDs differ: expected {sorted(expected_types)}, got {sorted(actual_types)}"
        )
    for rid, name in expected_types.items():
        entry = actual_types[rid]
        if entry.get("name") != name:
            raise AssertionError(f"{rid} display name differs: {entry.get('name')!r}")
        required_interfaces = {
            "I3D_Representable",
            "I3D_Spatial",
        }
        actual_interfaces = set(entry.get("injected_interfaces") or [])
        if not required_interfaces.issubset(actual_interfaces):
            raise AssertionError(
                f"{rid} is missing required interfaces: "
                f"required={sorted(required_interfaces)}, actual={sorted(actual_interfaces)}"
            )

    instances = _get_json(base_url, "/api/v2/instances")
    actual_instance_ids = {entry.get("id") for entry in instances}
    if actual_instance_ids != set(actors_by_instance):
        raise AssertionError("Instance API IDs differ from the reviewed export")

    headers = {
        "X-OntoTwin-UE-Project-Id": "ueproj_ZHHZ",
        "X-OntoTwin-UE-Project-Name": "ZHHZ",
    }
    snapshots = _get_json(base_url, "/api/v2/state/snapshots", headers)
    snapshots_by_id = {snapshot.get("instanceId"): snapshot for snapshot in snapshots}
    if len(snapshots_by_id) != expected_count or set(snapshots_by_id) != set(actors_by_instance):
        raise AssertionError("Snapshot API does not contain exactly the migrated instances")

    total_parts = 0
    total_sources = 0
    mirrored_sources = 0
    type_counts = {key: 0 for key in TYPE_NAMES}
    for instance_id, (actor, selected) in actors_by_instance.items():
        snapshot = snapshots_by_id[instance_id]
        business_type = selected["business_type"]
        type_rid = f"zhhz.{business_type}"
        type_name = TYPE_NAMES[business_type]
        hierarchy_name = HIERARCHY_NAMES[business_type]
        type_counts[business_type] += 1
        if snapshot.get("objectTypeRid") != type_rid:
            raise AssertionError(f"{instance_id} has wrong type RID")
        if snapshot.get("objectTypeName") != type_name:
            raise AssertionError(f"{instance_id} has wrong type name")
        if snapshot.get("hierarchyPath") != ["航空展馆", hierarchy_name]:
            raise AssertionError(f"{instance_id} has wrong hierarchy path")
        if snapshot.get("classificationStatus") != "confirmed":
            raise AssertionError(f"{instance_id} is not confirmed")
        required_interfaces = {
            "I3D_Representable",
            "I3D_Spatial",
        }
        snapshot_interfaces = set(snapshot.get("injected_interfaces") or [])
        if not required_interfaces.issubset(snapshot_interfaces):
            raise AssertionError(
                f"{instance_id} is missing required injected interfaces: "
                f"required={sorted(required_interfaces)}, actual={sorted(snapshot_interfaces)}"
            )

        interfaces = snapshot.get("interfaces") or {}
        representable = interfaces.get("I3D_Representable") or {}
        spatial = interfaces.get("I3D_Spatial") or {}
        if representable.get("assembly_signature") != actor.get("assembly_signature"):
            raise AssertionError(f"{instance_id} assembly signature differs")
        if representable.get("render_parts") != (actor.get("render_parts") or []):
            raise AssertionError(f"{instance_id} render parts differ from UE export")
        transform = actor.get("transform") or {}
        for field, source_field, default in (
            ("translation_x", "tx", 0.0),
            ("translation_y", "ty", 0.0),
            ("translation_z", "tz", 0.0),
            ("rotation_x", "rx", 0.0),
            ("rotation_y", "ry", 0.0),
            ("rotation_z", "rz", 0.0),
            ("scale_x", "sx", 1.0),
            ("scale_y", "sy", 1.0),
            ("scale_z", "sz", 1.0),
        ):
            _assert_close(
                spatial.get(field),
                transform.get(source_field, default),
                f"{instance_id}.{field}",
            )

        total_parts += len(actor.get("render_parts") or [])
        total_sources += len(actor.get("source_actor_guids") or [])
        mirrored_sources += sum(
            bool(source.get("has_mirrored_scale"))
            for source in actor.get("source_actors") or []
            if isinstance(source, dict)
        )

    if len(classification) != expected_count:
        raise AssertionError("Classification CSV row count differs")
    if any(row.get("classification_status") != "confirmed" for row in classification):
        raise AssertionError("Classification CSV includes an unconfirmed row")
    if any(row.get("action") != "create_experimental" for row in classification):
        raise AssertionError("Classification CSV includes an unexpected action")
    if result.get("schema_version") != "assembly_v1":
        raise AssertionError("Migration result is not assembly_v1")
    if len(result.get("instances") or {}) != expected_count:
        raise AssertionError("Migration result instance mapping count differs")
    if len(result.get("delete_actor_guids") or []) != total_sources:
        raise AssertionError("Migration result cleanup GUID count differs from the export")
    if result.get("blocked_actors"):
        raise AssertionError("Migration result contains blocked Actors")

    summary = {
        "status": "PASS",
        "dataset_id": active[0]["id"],
        "object_types": len(types),
        "instances": expected_count,
        "snapshots": len(snapshots),
        "source_actors": total_sources,
        "render_parts": total_parts,
        "mirrored_source_actors": mirrored_sources,
        "cleanup_guids_in_manifest": len(result.get("delete_actor_guids") or []),
        "business_type_counts": type_counts,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--export", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--classification", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    verify(
        args.base_url,
        args.export,
        args.selection,
        args.classification,
        args.result,
    )
