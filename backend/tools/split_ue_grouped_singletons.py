"""Split organizational UE groups into independently movable OntoTwin instances.

This path is intentionally strict: every child must be one complete physical
StaticMesh object. Rotated/scaled group roots are rejected because old
assembly_v1 exports do not carry each child actor's world transform.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


IDENTITY_TRANSFORM = {
    "tx": 0.0, "ty": 0.0, "tz": 0.0,
    "rx": 0.0, "ry": 0.0, "rz": 0.0,
    "sx": 1.0, "sy": 1.0, "sz": 1.0,
}

CLASSIFICATION_FIELDS = [
    "group_key", "count", "sample_actor_labels", "source_folder_path",
    "asset_path", "actor_class_path", "assembly_signature",
    "render_part_count", "total_render_part_count", "source_actor_count",
    "unsupported_component_count", "unsupported_component_types", "risk_flags",
    "suggested_object_type_rid", "suggested_object_type_name", "hierarchy_path",
    "classification_status", "action", "notes",
]


def _read_json(path):
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _guid(value):
    return str(value or "").strip().upper()


def _number(transform, key, default):
    return float((transform or {}).get(key, default))


def _require_identity_group_transform(actor):
    transform = actor.get("transform") or {}
    rotation = [_number(transform, key, 0.0) for key in ("rx", "ry", "rz")]
    scale = [_number(transform, key, 1.0) for key in ("sx", "sy", "sz")]
    if any(abs(value) > 1.0e-6 for value in rotation):
        raise ValueError(
            f"{actor.get('actor_label')}: rotated group root requires a new child-world-transform export"
        )
    if any(abs(value - 1.0) > 1.0e-6 for value in scale):
        raise ValueError(
            f"{actor.get('actor_label')}: scaled group root requires a new child-world-transform export"
        )
    return transform


def _world_transform(group_transform, relative_transform):
    relative_transform = relative_transform or {}
    return {
        "tx": _number(group_transform, "tx", 0.0) + _number(relative_transform, "tx", 0.0),
        "ty": _number(group_transform, "ty", 0.0) + _number(relative_transform, "ty", 0.0),
        "tz": _number(group_transform, "tz", 0.0) + _number(relative_transform, "tz", 0.0),
        "rx": _number(relative_transform, "rx", 0.0),
        "ry": _number(relative_transform, "ry", 0.0),
        "rz": _number(relative_transform, "rz", 0.0),
        "sx": _number(relative_transform, "sx", 1.0),
        "sy": _number(relative_transform, "sy", 1.0),
        "sz": _number(relative_transform, "sz", 1.0),
    }


def _single_mesh_signature(part):
    canonical = {
        "asset_path": part.get("asset_path") or part.get("ue_asset_path") or "",
        "material_paths": list(part.get("material_paths") or []),
        "visible": bool(part.get("visible", True)),
        "hidden_in_game": bool(part.get("hidden_in_game", False)),
        "cast_shadow": bool(part.get("cast_shadow", True)),
        "collision_enabled": part.get("collision_enabled") or "",
    }
    encoded = json.dumps(
        canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "singleton_v1:" + hashlib.sha256(encoded).hexdigest()


def _display_name(prefix, actor_label, ordinal):
    match = re.search(r"_(\d+)$", actor_label or "")
    return f"{prefix} {match.group(1) if match else f'{ordinal:03d}'}"


def _instance_ids_hash(instance_ids):
    payload = "\n".join(sorted(instance_ids)).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def split_export(payload, manifest):
    actors = list(payload.get("actors") or [])
    actor_by_guid = {_guid(actor.get("ext_guid")): actor for actor in actors}
    groups = list(manifest.get("groups") or [])
    manifest_guids = {_guid(group.get("source_container_guid")) for group in groups}
    if not groups or set(actor_by_guid) != manifest_guids:
        raise ValueError("input group GUIDs do not exactly match the type manifest")

    output_actors = []
    classification_buckets = {}
    per_type_counts = defaultdict(int)
    old_instance_ids = []
    source_container_guids = []
    all_source_guids = set()
    display_names = set()

    for group_spec in groups:
        container_guid = _guid(group_spec.get("source_container_guid"))
        actor = actor_by_guid[container_guid]
        if actor.get("unsupported_components"):
            raise ValueError(f"{actor.get('actor_label')}: unsupported components present")
        root_transform = _require_identity_group_transform(actor)
        render_parts = list(actor.get("render_parts") or [])
        expected_count = int(group_spec.get("expected_instance_count") or 0)
        if len(render_parts) != expected_count:
            raise ValueError(
                f"{actor.get('actor_label')}: expected {expected_count} parts, got {len(render_parts)}"
            )

        source_actors = {
            _guid(source.get("guid")): source
            for source in actor.get("source_actors") or []
            if _guid(source.get("guid")) != container_guid
        }
        parts_by_source = defaultdict(list)
        for part in render_parts:
            parts_by_source[_guid(part.get("source_actor_guid"))].append(part)
        if set(parts_by_source) != set(source_actors):
            raise ValueError(f"{actor.get('actor_label')}: part/source GUID sets differ")
        if any(len(parts) != 1 for parts in parts_by_source.values()):
            raise ValueError(
                f"{actor.get('actor_label')}: a child has multiple render parts; review its physical boundary"
            )
        exported_guids = {_guid(value) for value in actor.get("source_actor_guids") or []}
        if exported_guids != set(source_actors) | {container_guid}:
            raise ValueError(f"{actor.get('actor_label')}: source GUID inventory differs")

        source_container_guids.append(container_guid)
        old_instance_ids.append(group_spec["old_instance_id"])
        ordered_sources = sorted(
            source_actors.items(),
            key=lambda item: ((item[1].get("actor_label") or ""), item[0]),
        )
        for ordinal, (source_guid, source) in enumerate(ordered_sources, start=1):
            if source.get("has_mirrored_scale"):
                raise ValueError(f"{source.get('actor_label')}: mirrored scale requires review")
            if source_guid in all_source_guids:
                raise ValueError(f"duplicate physical source GUID: {source_guid}")
            all_source_guids.add(source_guid)

            source_part = parts_by_source[source_guid][0]
            asset_path = source_part.get("asset_path") or ""
            if asset_path != group_spec.get("expected_asset_path"):
                raise ValueError(f"{source.get('actor_label')}: asset does not match manifest")
            signature = _single_mesh_signature(source_part)
            part = copy.deepcopy(source_part)
            part["relative_transform"] = dict(IDENTITY_TRANSFORM)
            source_label = source.get("actor_label") or source_guid
            display_name = _display_name(
                group_spec["display_name_prefix"], source_label, ordinal
            )
            if display_name in display_names:
                raise ValueError(f"duplicate display name: {display_name}")
            display_names.add(display_name)

            actor_class = source.get("actor_class") or "StaticMeshActor"
            actor_class_path = source.get("actor_class_path") or "/Script/Engine.StaticMeshActor"
            singleton = {
                "ext_guid": source_guid,
                "name": display_name,
                "actor_label": display_name,
                "actor_name": source.get("actor_name") or source_label,
                "source_folder_path": source.get("folder_path") or actor.get("source_folder_path") or "",
                "actor_class": actor_class,
                "actor_class_path": actor_class_path,
                "transform": _world_transform(root_transform, source_part.get("relative_transform")),
                "assembly_signature": signature,
                "source_actor_guids": [source_guid],
                "source_actors": [copy.deepcopy(source)],
                "render_parts": [part],
                "unsupported_components": [],
                "migration_warnings": [],
                "mesh_asset": asset_path,
                "static_mesh_asset": asset_path,
                "static_mesh_assets": [asset_path],
                "skeletal_mesh_asset": "",
                "skeletal_mesh_assets": [],
                "component_audit": {
                    "source_actor_count": 1,
                    "descendant_actor_count": 0,
                    "render_part_count": 1,
                    "unsupported_component_count": 0,
                    "static_mesh_components": 1,
                    "skeletal_mesh_components": 0,
                    "actor_classes": {actor_class: 1},
                    "component_classes": {
                        source_part.get("source_component_class")
                        or "/Script/Engine.StaticMeshComponent": 1
                    },
                },
            }
            singleton["component_summary"] = copy.deepcopy(singleton["component_audit"])
            output_actors.append(singleton)
            per_type_counts[group_spec["object_type_rid"]] += 1

            type_identity = (
                group_spec["object_type_rid"],
                group_spec["object_type_name"],
                tuple(group_spec["hierarchy_path"]),
            )
            bucket = classification_buckets.get(signature)
            if bucket and bucket["type_identity"] != type_identity:
                raise ValueError(f"signature {signature} maps to multiple ObjectTypes")
            if not bucket:
                bucket = {
                    "type_identity": type_identity,
                    "asset_path": asset_path,
                    "source_folder_path": singleton["source_folder_path"],
                    "actor_class_path": actor_class_path,
                    "labels": [],
                    "count": 0,
                }
                classification_buckets[signature] = bucket
            bucket["labels"].append(display_name)
            bucket["count"] += 1

    expected_total = int(manifest.get("expected_new_instance_count") or 0)
    if len(output_actors) != expected_total or len(all_source_guids) != expected_total:
        raise ValueError(f"expected {expected_total} unique new instances, got {len(output_actors)}")
    expected_type_count = int(manifest.get("expected_object_type_count") or 0)
    if len(per_type_counts) != expected_type_count:
        raise ValueError(f"expected {expected_type_count} ObjectTypes, got {len(per_type_counts)}")

    new_instance_ids = [
        "ue_" + re.sub(r"[^0-9A-Za-z_-]", "", actor["ext_guid"])
        for actor in output_actors
    ]
    cleanup_guids = sorted(all_source_guids | set(source_container_guids))
    expected_cleanup = int(manifest.get("expected_source_cleanup_count") or 0)
    if len(cleanup_guids) != expected_cleanup:
        raise ValueError(f"expected {expected_cleanup} cleanup GUIDs, got {len(cleanup_guids)}")

    output = {
        "schema_version": "assembly_v1",
        "ue_project_id": manifest["ue_project_id"],
        "ue_project_name": manifest["ue_project_name"],
        "project_id": manifest["project_id"],
        "actors": output_actors,
        "replacement": {
            "old_instance_ids": old_instance_ids,
            "source_container_guids": source_container_guids,
            "expected_old_instance_count": len(old_instance_ids),
            "expected_new_instance_count": expected_total,
            "new_instance_ids_hash": _instance_ids_hash(new_instance_ids),
            "expected_delete_actor_guid_count": expected_cleanup,
        },
    }

    rows = []
    for signature, bucket in sorted(classification_buckets.items()):
        rid, type_name, hierarchy = bucket["type_identity"]
        rows.append({
            "group_key": f"assembly_signature:{signature}",
            "count": bucket["count"],
            "sample_actor_labels": " | ".join(bucket["labels"][:3]),
            "source_folder_path": bucket["source_folder_path"],
            "asset_path": bucket["asset_path"],
            "actor_class_path": bucket["actor_class_path"],
            "assembly_signature": signature,
            "render_part_count": 1,
            "total_render_part_count": bucket["count"],
            "source_actor_count": bucket["count"],
            "unsupported_component_count": 0,
            "unsupported_component_types": "",
            "risk_flags": "organizational_group_split_reviewed",
            "suggested_object_type_rid": rid,
            "suggested_object_type_name": type_name,
            "hierarchy_path": "/".join(hierarchy),
            "classification_status": "confirmed",
            "action": "map_existing",
            "notes": "Each source StaticMeshActor is one complete movable physical object.",
        })

    audit = {
        "success": True,
        "source_group_count": len(groups),
        "object_type_count": len(per_type_counts),
        "new_instance_count": len(output_actors),
        "new_render_part_count": sum(len(actor["render_parts"]) for actor in output_actors),
        "classification_row_count": len(rows),
        "source_container_count": len(source_container_guids),
        "source_cleanup_guid_count": len(cleanup_guids),
        "new_instance_ids_hash": output["replacement"]["new_instance_ids_hash"],
        "per_type_instance_counts": dict(sorted(per_type_counts.items())),
        "old_instance_ids": old_instance_ids,
        "source_container_guids": source_container_guids,
    }
    return output, rows, audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--type-manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--classification-output", required=True)
    parser.add_argument("--audit-output", required=True)
    args = parser.parse_args()
    output, rows, audit = split_export(
        _read_json(args.input), _read_json(args.type_manifest)
    )
    output_path = Path(args.output)
    classification_path = Path(args.classification_output)
    audit_path = Path(args.audit_output)
    for path in (output_path, classification_path, audit_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    with classification_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CLASSIFICATION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
