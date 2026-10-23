"""Build the reviewed ZHHZ migration classification and instance manifest."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os


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

# hierarchy_path uses '/' as a structural separator, so labels must not contain
# that character even when the formal ObjectType display name does.
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


def _load_generator(path):
    spec = importlib.util.spec_from_file_location("zhhz_classification_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load classification generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build(export_path, selection_path, generator_path, classification_path, manifest_path):
    with open(export_path, "r", encoding="utf-8") as stream:
        payload = json.load(stream)
    actors = payload.get("actors") or []
    with open(selection_path, "r", encoding="utf-8-sig", newline="") as stream:
        selection = list(csv.DictReader(stream))

    selection_by_guid = {}
    for row in selection:
        guid = _normalize_guid(row.get("ue_guid"))
        if not guid or guid in selection_by_guid:
            raise ValueError(f"Invalid or duplicate selected UE GUID: {guid!r}")
        if row.get("business_type") not in TYPE_NAMES:
            raise ValueError(f"Unknown ZHHZ business type: {row.get('business_type')!r}")
        selection_by_guid[guid] = row

    actor_by_guid = {}
    actor_selection = {}
    signature_selection = {}
    for actor in actors:
        guid = _normalize_guid(actor.get("ext_guid"))
        if not guid or guid in actor_by_guid:
            raise ValueError(f"Invalid or duplicate export ext_guid: {guid!r}")
        selected = selection_by_guid.get(guid)
        if selected is None:
            raise ValueError(f"Exported Actor is absent from reviewed selection: {guid}")
        signature = str(actor.get("assembly_signature") or "").strip()
        if not signature:
            raise ValueError(f"Exported Actor lacks assembly_signature: {guid}")
        previous = signature_selection.get(signature)
        if previous and previous["business_type"] != selected["business_type"]:
            raise ValueError(f"Assembly signature spans multiple business types: {signature}")
        actor_by_guid[guid] = actor
        actor_selection[guid] = selected
        signature_selection[signature] = selected

    missing_exports = sorted(set(selection_by_guid) - set(actor_by_guid))
    if missing_exports:
        raise ValueError(
            "Reviewed UE mother Actors missing from export: " + ", ".join(missing_exports)
        )

    generator = _load_generator(generator_path)
    generator.build(export_path, classification_path)
    with open(classification_path, "r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fieldnames = reader.fieldnames
    if not fieldnames:
        raise ValueError("Classification generator produced no CSV header")

    seen_signatures = set()
    for row in rows:
        signature = str(row.get("assembly_signature") or "").strip()
        selected = signature_selection.get(signature)
        if selected is None:
            raise ValueError(f"Classification row has unknown assembly signature: {signature}")
        business_type = selected["business_type"]
        display_name = TYPE_NAMES[business_type]
        hierarchy_name = HIERARCHY_NAMES[business_type]
        row["suggested_object_type_rid"] = f"zhhz.{business_type}"
        row["suggested_object_type_name"] = display_name
        row["hierarchy_path"] = f"航空展馆/{hierarchy_name}"
        row["classification_status"] = "confirmed"
        row["action"] = "create_experimental"
        row["notes"] = (
            f"reviewed Datasmith handle={selected['handle']}; "
            f"selection_source={selected['selection_source']}"
        )
        seen_signatures.add(signature)
    missing_signatures = sorted(set(signature_selection) - seen_signatures)
    if missing_signatures:
        raise ValueError(
            "No classification rows for assembly signatures: " + ", ".join(missing_signatures)
        )

    with open(classification_path, "w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    manifest_fields = (
        "ext_guid",
        "actor_label",
        "datasmith_handle",
        "selection_source",
        "business_type",
        "business_type_name",
        "object_type_rid",
        "hierarchy_path",
        "source_actor_count",
        "render_part_count",
        "mirrored_source_actor_count",
        "assembly_signature",
        "ue_path",
    )
    manifest = []
    for guid, actor in sorted(actor_by_guid.items(), key=lambda item: item[1].get("actor_label") or ""):
        selected = actor_selection[guid]
        business_type = selected["business_type"]
        display_name = TYPE_NAMES[business_type]
        hierarchy_name = HIERARCHY_NAMES[business_type]
        source_actors = actor.get("source_actors") or []
        manifest.append({
            "ext_guid": actor.get("ext_guid") or "",
            "actor_label": actor.get("actor_label") or actor.get("name") or "",
            "datasmith_handle": selected.get("handle") or "",
            "selection_source": selected.get("selection_source") or "",
            "business_type": business_type,
            "business_type_name": display_name,
            "object_type_rid": f"zhhz.{business_type}",
            "hierarchy_path": f"航空展馆/{hierarchy_name}",
            "source_actor_count": len(actor.get("source_actor_guids") or []),
            "render_part_count": len(actor.get("render_parts") or []),
            "mirrored_source_actor_count": sum(
                bool(source_actor.get("has_mirrored_scale"))
                for source_actor in source_actors
                if isinstance(source_actor, dict)
            ),
            "assembly_signature": actor.get("assembly_signature") or "",
            "ue_path": selected.get("ue_path") or "",
        })
    os.makedirs(os.path.dirname(os.path.abspath(manifest_path)), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=manifest_fields)
        writer.writeheader()
        writer.writerows(manifest)

    print(json.dumps({
        "actors": len(actors),
        "classification_rows": len(rows),
        "manifest_rows": len(manifest),
        "business_type_counts": {
            key: sum(row["business_type"] == key for row in manifest)
            for key in TYPE_NAMES
        },
    }, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--generator", required=True)
    parser.add_argument("--classification", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    build(
        args.export,
        args.selection,
        args.generator,
        args.classification,
        args.manifest,
    )
