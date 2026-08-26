import json
import os
import re
from pathlib import Path

import unreal


LEVEL_PACKAGE = os.environ.get(
    "ONTOTWIN_INVENTORY_LEVEL", "/Game/AVIC_Show/Art/Maps/L_AS_Arch"
)
OUTPUT_PATH = os.environ.get("ONTOTWIN_INVENTORY_OUTPUT", "")


def norm_guid(value):
    if value is None:
        return ""
    if hasattr(value, "to_string"):
        value = value.to_string()
    text = str(value).upper()
    match = re.search(
        r"([0-9A-F]{8})-([0-9A-F]{4})-([0-9A-F]{4})-([0-9A-F]{4})-([0-9A-F]{12})",
        text,
    )
    if match:
        return "".join(match.groups())
    words = re.findall(r"(?<![0-9A-F])[0-9A-F]{8}(?![0-9A-F])", text)
    if len(words) >= 4:
        return "".join(words[-4:])
    compact = "".join(character for character in text if character in "0123456789ABCDEF")
    return compact if len(compact) == 32 else ""


def actor_guid(actor):
    getter = getattr(actor, "get_actor_guid", None)
    if callable(getter):
        value = norm_guid(getter())
        if value:
            return value
    for name in ("actor_guid", "actor_instance_guid"):
        try:
            value = norm_guid(actor.get_editor_property(name))
        except Exception:
            continue
        if value:
            return value
    return ""


def object_paths(actor, component_class, property_name):
    paths = []
    try:
        components = actor.get_components_by_class(component_class)
    except Exception:
        components = []
    for component in components:
        try:
            value = component.get_editor_property(property_name)
        except Exception:
            value = None
        if value:
            paths.append(value.get_path_name())
    return paths


def transform_dict(actor):
    transform = actor.get_actor_transform()
    location = transform.translation
    rotation = transform.rotation.rotator()
    scale = transform.scale3d
    return {
        "tx": round(float(location.x), 5),
        "ty": round(float(location.y), 5),
        "tz": round(float(location.z), 5),
        "rx": round(float(rotation.roll), 5),
        "ry": round(float(rotation.pitch), 5),
        "rz": round(float(rotation.yaw), 5),
        "sx": round(float(scale.x), 6),
        "sy": round(float(scale.y), 6),
        "sz": round(float(scale.z), 6),
    }


def main():
    if not OUTPUT_PATH:
        raise RuntimeError("ONTOTWIN_INVENTORY_OUTPUT is required")
    if not unreal.EditorLoadingAndSavingUtils.load_map(LEVEL_PACKAGE):
        raise RuntimeError("Could not load " + LEVEL_PACKAGE)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    records = []
    for actor in subsystem.get_all_level_actors():
        try:
            label = actor.get_actor_label()
            record = {
                "guid": actor_guid(actor),
                "label": label,
                "name": actor.get_name(),
                "class": actor.get_class().get_path_name(),
                "path": actor.get_path_name(),
                "transform": transform_dict(actor),
                "static_meshes": sorted(
                    set(object_paths(actor, unreal.StaticMeshComponent, "static_mesh"))
                ),
                "skeletal_meshes": sorted(
                    set(
                        object_paths(
                            actor, unreal.SkeletalMeshComponent, "skeletal_mesh_asset"
                        )
                    )
                ),
            }
        except Exception as error:
            unreal.log_warning("Skipping actor inventory record: {}".format(error))
            continue
        records.append(record)
    records.sort(key=lambda value: (value["label"], value["guid"], value["path"]))
    output = Path(OUTPUT_PATH)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(
            {"level": LEVEL_PACKAGE, "actor_count": len(records), "actors": records},
            handle,
            ensure_ascii=False,
            indent=2,
        )
    unreal.log("OntoTwin actor inventory wrote {} records to {}".format(len(records), output))


if __name__ == "__main__":
    main()
