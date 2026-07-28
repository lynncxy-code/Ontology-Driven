import json
import os
import re

import unreal


SNAPSHOT_PATH = r"C:\Users\ADMIN\Documents\zhhz\.codex_migration_work\audit\ue_snapshots_round2_semantic.json"
OUTPUT_DIR = r"D:\tmp\digital_twin_aircraft\.codex\artstudio_furniture_uploads"


def clean_asset_path(value):
    return "".join(str(value or "").split())


def ascii_code(name):
    match = re.search(r"(FUR-\d+)", name or "")
    return match.group(1) if match else "FUR-UNKNOWN"


with open(SNAPSHOT_PATH, "r", encoding="utf-8") as handle:
    snapshots = json.load(handle)

furniture_by_type = {}
for snapshot in snapshots:
    rid = snapshot.get("objectTypeRid", "")
    if rid.startswith("zhhz.furniture.") and rid not in furniture_by_type:
        furniture_by_type[rid] = snapshot

if len(furniture_by_type) != 10:
    raise RuntimeError("Expected 10 furniture types, found %d" % len(furniture_by_type))

os.makedirs(OUTPUT_DIR, exist_ok=True)
unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
world = unreal.EditorLevelLibrary.get_editor_world()
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
options = unreal.GLTFExportOptions()

manifest = []
for rid, snapshot in sorted(furniture_by_type.items()):
    type_name = snapshot.get("objectTypeName", rid)
    code = ascii_code(type_name)
    render_parts = snapshot["interfaces"]["I3D_Representable"]["render_parts"]
    spawned = []
    missing_assets = []

    for index, part in enumerate(render_parts):
        asset_path = clean_asset_path(part.get("asset_path"))
        mesh = unreal.load_asset(asset_path)
        if not mesh:
            missing_assets.append(asset_path)
            continue

        transform = part.get("relative_transform", {})
        location = unreal.Vector(
            float(transform.get("tx", 0.0)),
            float(transform.get("ty", 0.0)),
            float(transform.get("tz", 0.0)),
        )
        rotation = unreal.Rotator(
            pitch=float(transform.get("ry", 0.0)),
            yaw=float(transform.get("rz", 0.0)),
            roll=float(transform.get("rx", 0.0)),
        )

        actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
        actor.set_actor_label("%s_%04d" % (code, index + 1))
        actor.set_actor_scale3d(
            unreal.Vector(
                float(transform.get("sx", 1.0)),
                float(transform.get("sy", 1.0)),
                float(transform.get("sz", 1.0)),
            )
        )
        component = actor.static_mesh_component
        component.set_static_mesh(mesh)

        for material_index, material_path in enumerate(part.get("material_paths", [])):
            material_path = clean_asset_path(material_path)
            if not material_path:
                continue
            material = unreal.load_asset(material_path)
            if material:
                component.set_material(material_index, material)

        spawned.append(actor)

    if missing_assets:
        raise RuntimeError("%s has %d missing assets" % (code, len(missing_assets)))
    if not spawned:
        raise RuntimeError("%s produced no actors" % code)

    output_path = os.path.join(OUTPUT_DIR, "%s.glb" % code)
    ok = unreal.GLTFExporter.export_to_gltf(world, output_path, options, set(spawned))
    if not ok or not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError("Failed to export %s" % code)

    manifest.append(
        {
            "code": code,
            "title": type_name,
            "rid": rid,
            "file": output_path,
            "parts": len(render_parts),
            "bytes": os.path.getsize(output_path),
            "warnings": [],
        }
    )

    actor_subsystem.destroy_actors(spawned)

manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
with open(manifest_path, "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, ensure_ascii=False, indent=2)

unreal.log("ONTOTWIN_FURNITURE_EXPORT_OK count=%d manifest=%s" % (len(manifest), manifest_path))
