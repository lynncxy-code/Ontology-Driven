import json
import os
import traceback

import unreal


MAP_PATH = "/Game/SCC_W9/Art/Maps/L_SCC_W9_Main"
OUTPUT_PATH = r"D:\tmp\digital_twin_aircraft\migration_runs\w9_round1_20260727\00_input\w9_scene_inventory_round1.json"


def object_path(value):
    if value is None:
        return None
    try:
        return value.get_path_name()
    except Exception:
        return str(value)


def vector_dict(value):
    return {"x": value.x, "y": value.y, "z": value.z}


def rotator_dict(value):
    return {"pitch": value.pitch, "yaw": value.yaw, "roll": value.roll}


def safe_call(callback, default=None):
    try:
        return callback()
    except Exception:
        return default


def component_record(component):
    record = {
        "name": safe_call(component.get_name, ""),
        "class_path": object_path(safe_call(component.get_class)),
    }
    if isinstance(component, unreal.StaticMeshComponent):
        mesh = safe_call(lambda: component.get_editor_property("static_mesh"))
        record["static_mesh"] = object_path(mesh)
    if isinstance(component, unreal.SkeletalMeshComponent):
        mesh = safe_call(lambda: component.get_editor_property("skeletal_mesh_asset"))
        if mesh is None:
            mesh = safe_call(lambda: component.get_editor_property("skeletal_mesh"))
        record["skeletal_mesh"] = object_path(mesh)
    if isinstance(component, unreal.MeshComponent):
        material_count = safe_call(component.get_num_materials, 0) or 0
        record["materials"] = [
            object_path(safe_call(lambda index=index: component.get_material(index)))
            for index in range(material_count)
        ]
    if isinstance(component, unreal.ChildActorComponent):
        child_actor = safe_call(component.get_child_actor)
        record["child_actor"] = object_path(child_actor)
    return record


def actor_record(actor):
    transform = safe_call(actor.get_actor_transform)
    location = safe_call(actor.get_actor_location)
    rotation = safe_call(actor.get_actor_rotation)
    scale = safe_call(actor.get_actor_scale3d)
    bounds = safe_call(lambda: actor.get_actor_bounds(False, True))
    components = safe_call(lambda: actor.get_components_by_class(unreal.ActorComponent), []) or []
    parent = safe_call(actor.get_attach_parent_actor)
    guid_value = safe_call(lambda: actor.get_editor_property("actor_guid"))
    guid = safe_call(lambda: guid_value.to_string())
    folder = safe_call(lambda: str(actor.get_folder_path()), "")
    record = {
        "actor_label": safe_call(actor.get_actor_label, ""),
        "actor_name": safe_call(actor.get_name, ""),
        "actor_path": object_path(actor),
        "actor_guid": guid,
        "actor_class_path": object_path(safe_call(actor.get_class)),
        "level_package": safe_call(lambda: actor.get_level().get_outermost().get_name(), ""),
        "actor_package": safe_call(lambda: actor.get_outermost().get_name(), ""),
        "folder_path": folder,
        "attach_parent_path": object_path(parent),
        "tags": [str(tag) for tag in (safe_call(lambda: actor.tags, []) or [])],
        "hidden_in_game": safe_call(lambda: actor.is_hidden(), False),
        "component_count": len(components),
        "components": [component_record(component) for component in components],
    }
    if transform is not None:
        record["transform"] = str(transform)
    if location is not None:
        record["location"] = vector_dict(location)
    if rotation is not None:
        record["rotation"] = rotator_dict(rotation)
    if scale is not None:
        record["scale"] = vector_dict(scale)
        record["has_negative_scale"] = min(scale.x, scale.y, scale.z) < 0
    if bounds is not None and len(bounds) == 2:
        record["bounds_origin"] = vector_dict(bounds[0])
        record["bounds_extent"] = vector_dict(bounds[1])
    return record


def main():
    unreal.log("CODEX_W9_INSPECT_BEGIN")
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if world is None:
        raise RuntimeError("Failed to load map: " + MAP_PATH)

    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(subsystem.get_all_level_actors())
    streaming_levels = []
    for streaming_level in safe_call(lambda: world.get_streaming_levels(), []) or []:
        streaming_levels.append({
            "object_path": object_path(streaming_level),
            "world_asset_package_name": safe_call(streaming_level.get_world_asset_package_name, ""),
            "is_level_loaded": safe_call(streaming_level.is_level_loaded, False),
            "is_level_visible": safe_call(streaming_level.is_level_visible, False),
        })

    records = [actor_record(actor) for actor in actors]
    class_counts = {}
    level_counts = {}
    for record in records:
        class_counts[record["actor_class_path"]] = class_counts.get(record["actor_class_path"], 0) + 1
        level_counts[record["level_package"]] = level_counts.get(record["level_package"], 0) + 1

    payload = {
        "schema": "w9_scene_inventory_v1",
        "project_file": r"D:\SCC\SCC2\scc2\scc2.uproject",
        "requested_map": MAP_PATH,
        "loaded_world": object_path(world),
        "actor_count": len(records),
        "streaming_levels": streaming_levels,
        "level_actor_counts": dict(sorted(level_counts.items())),
        "class_actor_counts": dict(sorted(class_counts.items())),
        "actors": records,
        "read_only": True,
        "saved_assets": False,
    }
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    unreal.log("CODEX_W9_INSPECT_DONE actor_count={} output={}".format(len(records), OUTPUT_PATH))


try:
    main()
except Exception:
    unreal.log_error("CODEX_W9_INSPECT_FAILED\n" + traceback.format_exc())
    raise
