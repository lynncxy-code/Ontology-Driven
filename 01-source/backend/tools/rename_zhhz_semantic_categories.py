"""Apply a reviewed ZHHZ semantic type/instance rename plan to ProjectStore."""

from __future__ import annotations

import argparse
import json

from project_store import ProjectStore


def apply(plan_path: str, dry_run: bool = False) -> dict:
    with open(plan_path, "r", encoding="utf-8") as stream:
        plan = json.load(stream)
    type_names = plan.get("type_names") or {}
    instance_names = plan.get("instance_names") or {}
    hierarchy_paths = plan.get("instance_hierarchy_paths") or {}
    if len(type_names) != 43 or len(instance_names) != 66 or len(hierarchy_paths) != 16:
        raise ValueError("Semantic rename plan must contain 43 types, 66 instances and 16 paths")

    store = ProjectStore()
    if store.get_active_id() != plan.get("dataset_id"):
        raise RuntimeError(f"Unexpected active dataset: {store.get_active_id()}")
    active = store.get_active()
    if not active:
        raise RuntimeError("No active ZHHZ project")
    object_types = dict(store.get_object_types())
    instances = active.get("instances") or {}

    missing_types = sorted(set(type_names) - set(object_types))
    missing_instances = sorted(set(instance_names) - set(instances))
    if missing_types or missing_instances:
        raise RuntimeError(f"Rename targets missing: types={missing_types}, instances={missing_instances}")
    for instance_id in instance_names:
        rid = instances[instance_id].get("object_type_rid")
        if rid not in type_names:
            raise RuntimeError(f"Instance {instance_id} has unexpected type {rid}")

    changes = {
        "dataset_id": store.get_active_id(),
        "type_renames": len(type_names),
        "instance_renames": len(instance_names),
        "hierarchy_path_updates": len(hierarchy_paths),
        "dry_run": dry_run,
    }
    if dry_run:
        print(json.dumps(changes, ensure_ascii=False, indent=2))
        return changes

    for rid, new_name in type_names.items():
        object_types[rid]["name"] = new_name
    for instance_id, new_name in instance_names.items():
        instance = instances[instance_id]
        instance["display_name"] = new_name
        instance["object_type_name"] = type_names[instance["object_type_rid"]]
        if instance_id in hierarchy_paths:
            instance["hierarchy_path"] = hierarchy_paths[instance_id]

    dataset = active.get("dataset") or {}
    graph_data = dataset.get("graph_data") or {}
    updated_graph_nodes = 0
    for node in graph_data.get("nodes") or []:
        rid = node.get("rid") or node.get("id")
        if rid in type_names:
            node["name"] = type_names[rid]
            updated_graph_nodes += 1
    if updated_graph_nodes != len(type_names):
        raise RuntimeError(f"Expected {len(type_names)} graph nodes, found {updated_graph_nodes}")

    store.set_object_types(object_types)
    active["instances"] = instances
    store._save_current()
    changes["graph_node_renames"] = updated_graph_nodes
    print(json.dumps(changes, ensure_ascii=False, indent=2))
    return changes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply(args.plan, args.dry_run)
