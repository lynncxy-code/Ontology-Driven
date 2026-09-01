"""Atomic, scoped model replacement for the test0316 OntoTwin dataset.

The script runs inside the OntoTwin backend container (ProjectStorePG).  It
replaces only live records whose source is ``ue_migrated`` and preserves manual
or realtime records (for example AGV and roaming-person records).  It never
touches UE maps or source Actors.  Without ``--apply`` it is a pure dry-run.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import time
from pathlib import Path

# When invoked by absolute path Python puts the nested tools directory first on
# sys.path; add the backend root so the normal ProjectStore modules resolve.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from project_store import _clean_hierarchy_path, _default_raw_state, apply_instance_metadata
from project_store_pg import ProjectStorePG


def _sha(obj: object) -> str:
    encoded = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _id_hash(ids: list[str]) -> str:
    return _sha("\n".join(sorted(ids)))


def _load(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _safe_iid(guid: str) -> str:
    return "ue_" + re.sub(r"[^0-9A-Za-z_-]", "", str(guid))


def _path(value: str) -> list[str]:
    return [p.strip() for p in str(value or "").replace("\\", "/").split("/") if p.strip()]


def _node(ot: dict) -> dict:
    return {
        "id": ot.get("rid"),
        "rid": ot.get("rid"),
        "name": ot.get("name") or ot.get("rid"),
        "category": ot.get("category") or "UE Migration",
        "description": ot.get("description") or "",
        "injected_interfaces": list(ot.get("injected_interfaces") or []),
        "color": ot.get("color") or "#8a8a8a",
        "properties": list(ot.get("properties") or []),
    }


def _new_record(actor: dict, type_specs: dict, now: float) -> dict:
    guid = str(actor.get("ext_guid") or "").strip()
    asset = str(actor.get("static_mesh_asset") or actor.get("mesh_asset") or "").strip()
    # The offline planner stores the type RID in a deterministic field on the
    # actor only indirectly; derive it from the same SHA rule used by the planner.
    rid = "ri.obj.test0316_" + hashlib.sha256(asset.encode("utf-8")).hexdigest()[:24]
    ot = type_specs[rid]
    tf = actor.get("transform") or {}
    iid = _safe_iid(guid)
    raw = _default_raw_state(rid, actor.get("actor_label") or actor.get("name") or iid,
                             {"x": tf.get("tx", 0), "y": tf.get("ty", 0), "z": tf.get("tz", 0)})
    raw.update({
        "rotation_x": float(tf.get("rx", 0)),
        "rotation_y": float(tf.get("ry", 0)),
        "rotation_z": float(tf.get("rz", 0)),
        "scale_x": float(tf.get("sx", 1)),
        "scale_y": float(tf.get("sy", 1)),
        "scale_z": float(tf.get("sz", 1)),
        "asset_id": asset,
    })
    rec = {
        "id": iid,
        "object_type_rid": rid,
        "object_type_name": ot.get("name") or rid,
        "source": "ue_migrated",
        "ext_guid": guid,
        "display_name": actor.get("actor_label") or actor.get("name") or iid,
        "hierarchy_path": _clean_hierarchy_path(
            _path(actor.get("hierarchy_path")) or _path(actor.get("source_folder_path")) or ["工厂", "可移动物"],
            [ot.get("name") or rid],
        ),
        "source_folder_path": actor.get("source_folder_path") or "",
        "source_asset_path": asset,
        "classification_status": "confirmed",
        "classification_key": "static_mesh_asset:" + asset,
        "status": "online",
        "created_at": now,
        "last_seen": now,
        "render_config": {
            "injected_interfaces": list(ot.get("injected_interfaces") or ["I3D_Representable", "I3D_Spatial"]),
            "asset_id": asset,
            "ue_asset_path": asset,
            "source_actor_guids": [guid],
            "render_parts": copy.deepcopy(actor.get("render_parts") or []),
            "assembly_signature": actor.get("assembly_signature") or "",
            "unsupported_components": [],
        },
        "raw_state": raw,
    }
    apply_instance_metadata(rec)
    return rec


def build_plan(store: ProjectStorePG, project_id: str, input_payload: dict, type_specs: dict) -> tuple[dict, dict]:
    declared_pid = str(input_payload.get("project_id") or "").strip()
    if declared_pid and declared_pid != project_id:
        raise SystemExit(f"project_id_mismatch:{declared_pid}!={project_id}")
    project = store.read_project(project_id)
    if not project:
        raise SystemExit(f"project_not_found:{project_id}")
    dataset = project.get("dataset") or {}
    expected_ue = str(input_payload.get("ue_project_id") or "").strip()
    expected_name = str(input_payload.get("ue_project_name") or "").strip()
    bound_ue = str(dataset.get("bound_ue_project_id") or "").strip()
    bound_name = str(dataset.get("bound_ue_project_name") or "").strip()
    if expected_ue and bound_ue != expected_ue:
        raise SystemExit(f"binding_mismatch:{bound_ue}!={expected_ue}")
    if expected_name and bound_name != expected_name:
        raise SystemExit(f"binding_name_mismatch:{bound_name}!={expected_name}")

    current = project.get("instances") or {}
    replace_ids = sorted(
        iid for iid, rec in current.items()
        if isinstance(rec, dict) and str(rec.get("source") or "") == "ue_migrated"
    )
    preserve_ids = sorted(iid for iid in current if iid not in set(replace_ids))
    now = time.time()
    new_records = {}
    for actor in input_payload.get("actors") or []:
        rec = _new_record(actor, type_specs, now)
        if rec["id"] in new_records:
            raise SystemExit(f"duplicate_instance_id:{rec['id']}")
        new_records[rec["id"]] = rec

    # Keep types needed by preserved runtime/manual records and their component
    # bindings.  Old migration-only types are intentionally not carried forward.
    keep_rids = {str((current[iid] or {}).get("object_type_rid") or "") for iid in preserve_ids}
    for value in (project.get("components") or {}).values():
        if isinstance(value, dict):
            rid = str(value.get("object_type_rid") or "")
            if rid:
                keep_rids.add(rid)
    old_types = project.get("object_types") or {}
    object_types = {rid: copy.deepcopy(old_types[rid]) for rid in keep_rids if rid in old_types}
    object_types.update(copy.deepcopy(type_specs))

    instances = {iid: copy.deepcopy(current[iid]) for iid in preserve_ids}
    instances.update(new_records)
    live_component_refs = []
    for cid, component in (project.get("components") or {}).items():
        if not isinstance(component, dict):
            continue
        bound = str(component.get("bound_instance_id") or "").strip()
        if bound and bound not in instances:
            live_component_refs.append({"component_id": cid, "bound_instance_id": bound})
    roster_refs = []
    for row in project.get("instance_roster") or []:
        if isinstance(row, dict):
            bound = str(row.get("instance_id") or "").strip()
            if bound and bound not in instances:
                roster_refs.append({"instance_id": bound, "row": row})

    out_project = copy.deepcopy(project)
    out_project["object_types"] = object_types
    out_project["instances"] = instances
    graph = copy.deepcopy(dataset.get("graph_data") or {})
    graph["nodes"] = [_node(object_types[rid]) for rid in sorted(object_types)]
    graph["links"] = [
        link for link in (graph.get("links") or [])
        if isinstance(link, dict)
        and str(link.get("source") or link.get("source_rid") or "") in object_types
        and str(link.get("target") or link.get("target_rid") or "") in object_types
    ]
    graph["categories"] = [{"name": name} for name in sorted({n.get("category") for n in graph["nodes"] if n.get("category")})]
    out_project["dataset"] = copy.deepcopy(dataset)
    out_project["dataset"]["graph_data"] = graph
    out_project["dataset"]["node_count"] = len(graph["nodes"])
    out_project["dataset"]["link_count"] = len(graph["links"])

    manifest = {
        "schema_version": "test0316_model_replacement_v1",
        "project_id": project_id,
        "ue_project_id": expected_ue,
        "ue_project_name": expected_name,
        "target_map": input_payload.get("target_map") or "",
        "input_actor_count": len(input_payload.get("actors") or []),
        "new_instance_count": len(new_records),
        "new_type_count": len(type_specs),
        "final_instance_count": len(instances),
        "final_type_count": len(object_types),
        "replaced_live_instance_ids": replace_ids,
        "preserved_live_instance_ids": preserve_ids,
        "new_instance_ids_hash": _id_hash(list(new_records)),
        "final_instance_ids_hash": _id_hash(list(instances)),
        "stale_component_bindings": live_component_refs,
        "stale_roster_bindings": roster_refs,
        "source_actor_guids": sorted(str(a.get("ext_guid") or "") for a in input_payload.get("actors") or []),
        "project_before_digest": _sha(project),
        "project_after_digest": _sha(out_project),
    }
    return out_project, manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-id", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--types", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--expected-manifest", default="",
                     help="dry-run manifest to compare before an apply")
    args = ap.parse_args()
    payload = _load(args.input)
    types = _load(args.types)
    store = ProjectStorePG()
    project, manifest = build_plan(store, args.project_id, payload, types)
    if args.apply and args.expected_manifest:
        expected = _load(args.expected_manifest)
        checks = {
            "project_before_digest": expected.get("project_before_digest"),
            "new_instance_ids_hash": expected.get("new_instance_ids_hash"),
            "new_instance_count": expected.get("new_instance_count"),
            "new_type_count": expected.get("new_type_count"),
        }
        for key, value in checks.items():
            if value is not None and manifest.get(key) != value:
                raise SystemExit(f"apply_gate_mismatch:{key}:{manifest.get(key)}!={value}")
    if args.apply:
        store.write_project(args.project_id, project)
        manifest["applied"] = True
    else:
        manifest["applied"] = False
    Path(args.manifest).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
