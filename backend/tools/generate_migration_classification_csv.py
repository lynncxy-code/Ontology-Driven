"""
Generate an editable CSV classification sheet from a UE migration export.

Workflow:
  1. UE exports Saved/OntoTwinMigration/ue_actors_export.json.
  2. Run this tool to group actors by blueprint/skeletal/static mesh/folder.
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
    return "", ""


def _group_key(actor):
    key, value = _best_asset(actor)
    if value:
        return f"{key}:{value}"
    folder = actor.get("source_folder_path") or ""
    if folder:
        return f"folder:{folder}"
    return f"name:{actor.get('actor_label') or actor.get('name') or 'unknown'}"


def _split_folder(folder):
    return [p.strip() for p in str(folder or "").replace("\\", "/").split("/") if p.strip()]


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
        rows.append({
            "group_key": gkey,
            "count": len(actors),
            "sample_actor_labels": "|".join(x for x in labels if x),
            "source_folder_path": folder,
            "asset_path": asset,
            "actor_class_path": first.get("actor_class_path") or first.get("actor_class") or "",
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
            "actor_class_path", "suggested_object_type_rid", "suggested_object_type_name",
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
