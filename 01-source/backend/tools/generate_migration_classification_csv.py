"""
Generate an editable CSV classification sheet from a UE migration export.

Workflow:
  1. UE exports Saved/OntoTwinMigration/ue_actors_export.json.
  2. Run this tool to group actors by assembly signature, then asset/folder fallback.
  3. Edit the CSV in Excel: fill suggested_object_type_rid/name, hierarchy_path, action.
  4. Use build_migration_ontology_patch.py and migrate_ue_actors.py --classification-csv.
"""

import argparse
import csv
import json
import os


def _best_asset(actor):
    for key in ("blueprint_class_path", "skeletal_mesh_asset", "static_mesh_asset", "mesh_asset", "actor_class_path"):
        value = actor.get(key)
        if value:
            return key, value
    for part in actor.get("render_parts") or []:
        if not isinstance(part, dict):
            continue
        for key in ("asset_path", "ue_asset_path", "static_mesh_asset", "mesh_asset"):
            value = part.get(key)
            if value:
                return f"render_part.{key}", value
    return "", ""


def _group_key(actor):
    signature = actor.get("assembly_signature")
    if signature:
        return f"assembly_signature:{signature}"
    key, value = _best_asset(actor)
    if value:
        return f"{key}:{value}"
    folder = actor.get("source_folder_path") or ""
    if folder:
        return f"folder:{folder}"
    return f"name:{actor.get('actor_label') or actor.get('name') or 'unknown'}"


def _split_folder(folder):
    return [p.strip() for p in str(folder or "").replace("\\", "/").split("/") if p.strip()]


def _source_actor_count(actor):
    values = [actor.get("ext_guid")]
    source_guids = actor.get("source_actor_guids") or []
    if not isinstance(source_guids, (list, tuple, set)):
        source_guids = [source_guids]
    values.extend(source_guids)
    return len({str(value).strip() for value in values if str(value or "").strip()})


def _unsupported_component_count(actor):
    total = 0
    unsupported = actor.get("unsupported_components") or []
    if not isinstance(unsupported, (list, tuple, set)):
        unsupported = [unsupported]
    for item in unsupported:
        if isinstance(item, dict):
            try:
                total += max(1, int(item.get("count", 1)))
            except (TypeError, ValueError):
                total += 1
        else:
            total += 1
    return total


def _unsupported_component_types(actor):
    unsupported = actor.get("unsupported_components") or []
    if not isinstance(unsupported, (list, tuple, set)):
        unsupported = [unsupported]
    result = []
    for item in unsupported:
        if isinstance(item, dict):
            value = (
                item.get("component_type")
                or item.get("type")
                or item.get("class")
                or item.get("name")
                or json.dumps(item, ensure_ascii=False, sort_keys=True)
            )
        else:
            value = str(item)
        value = str(value or "").strip()
        if value and value not in result:
            result.append(value)
    return result


def _count_range(values):
    values = list(values)
    if not values:
        return "0"
    low, high = min(values), max(values)
    return str(low) if low == high else f"{low}-{high}"


def _risk_flags(actors, part_counts, unsupported_count):
    flags = []
    if any(count > 1 for count in part_counts):
        flags.append("composite_assembly")
    if len(set(part_counts)) > 1:
        flags.append("signature_shape_mismatch")
    if unsupported_count:
        flags.append("unsupported_components")
    if any(a.get("skeletal_mesh_asset") for a in actors):
        flags.append("skeletal_mesh")
    if any(a.get("blueprint_class_path") for a in actors):
        flags.append("blueprint")
    if any(not _best_asset(a)[1] and not (a.get("render_parts") or []) for a in actors):
        flags.append("missing_render_asset")
    if any(not a.get("assembly_signature") for a in actors):
        flags.append("missing_assembly_signature")
    return "|".join(flags)


def build(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    groups = {}
    for actor in payload.get("actors") or []:
        gkey = _group_key(actor)
        groups.setdefault(gkey, []).append(actor)

    rows = []
    for gkey, actors in sorted(groups.items()):
        first = actors[0]
        _, asset = _best_asset(first)
        folder = first.get("source_folder_path") or ""
        labels = [a.get("actor_label") or a.get("name") or a.get("ext_guid") or "" for a in actors[:5]]
        hierarchy = ["历史迁移"] + (_split_folder(folder) or ["未分类"])
        part_counts = [len(a.get("render_parts") or []) for a in actors]
        source_actor_counts = [_source_actor_count(a) for a in actors]
        unsupported_count = sum(_unsupported_component_count(a) for a in actors)
        unsupported_types = sorted({
            component_type
            for actor in actors
            for component_type in _unsupported_component_types(actor)
        })
        rows.append({
            "group_key": gkey,
            "count": len(actors),
            "sample_actor_labels": "|".join(x for x in labels if x),
            "source_folder_path": folder,
            "asset_path": asset,
            "actor_class_path": first.get("actor_class_path") or first.get("actor_class") or "",
            "assembly_signature": first.get("assembly_signature") or "",
            "render_part_count": _count_range(part_counts),
            "total_render_part_count": sum(part_counts),
            "source_actor_count": _count_range(source_actor_counts),
            "unsupported_component_count": unsupported_count,
            "unsupported_component_types": "|".join(unsupported_types),
            "risk_flags": _risk_flags(actors, part_counts, unsupported_count),
            "suggested_object_type_rid": "",
            "suggested_object_type_name": "",
            "hierarchy_path": "/".join(hierarchy),
            "classification_status": "needs_review",
            "action": "map_existing",
            "notes": "",
        })

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "group_key", "count", "sample_actor_labels", "source_folder_path", "asset_path",
            "actor_class_path", "assembly_signature", "render_part_count", "total_render_part_count",
            "source_actor_count", "unsupported_component_count", "unsupported_component_types",
            "risk_flags", "suggested_object_type_rid", "suggested_object_type_name",
            "hierarchy_path", "classification_status", "action", "notes",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"写出 {len(rows)} 个分类组: {output_path}")


if __name__ == "__main__":
    here = os.path.dirname(__file__)
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=os.path.join(here, "ue_actors_export.json"))
    ap.add_argument("--output", default=os.path.join(here, "ue_migration_classification.csv"))
    args = ap.parse_args()
    build(args.input, args.output)
