import json
import re
from pathlib import Path

import unreal


LEVEL_PACKAGE = "/Game/AVIC_Show/Art/Maps/L_AS_Arch"
TARGETS = {
    "8A76BDD64BBFA5479552FA8D0781F136": {
        "label": "LTypeStair012",
        "mesh": "/Game/AVIC_Show/Art/A03_ParkLevel/0713/Geometries/LTypeStair012.LTypeStair012",
    },
    "BF2215204C34C4D667F758A2158DA3F9": {
        "label": "Rectangle2133396258",
        "mesh": "/Game/AVIC_Show/Art/A03_ParkLevel/0713/Geometries/Rectangle2133396258.Rectangle2133396258",
    },
    "8276C34749E5EA9128A92783D7914AF3": {
        "label": "Rectangle2133396242",
        "mesh": "/Game/AVIC_Show/Art/A03_ParkLevel/0713/Geometries/Rectangle2133396242.Rectangle2133396242",
    },
    "5A44CC254C9EA5D94A0D24A5A706B906": {
        "label": "Rectangle2133396246",
        "mesh": "/Game/AVIC_Show/Art/A03_ParkLevel/0713/Geometries/Rectangle2133396246.Rectangle2133396246",
    },
    "507939144E8162AAA00FE48B08BF6F07": {
        "label": "Line2144961944",
        "mesh": "/Game/AVIC_Show/Art/A03_ParkLevel/0713/Geometries/Line2144961944.Line2144961944",
    },
}


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


def actor_meshes(actor):
    paths = []
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        try:
            mesh = component.get_editor_property("static_mesh")
        except Exception:
            mesh = None
        if mesh:
            paths.append(mesh.get_path_name())
    return sorted(set(paths))


def main():
    if not unreal.EditorLoadingAndSavingUtils.load_map(LEVEL_PACKAGE):
        raise RuntimeError("Could not load " + LEVEL_PACKAGE)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    found = {}
    for actor in subsystem.get_all_level_actors():
        guid = actor_guid(actor)
        if guid not in TARGETS:
            continue
        target = TARGETS[guid]
        label = actor.get_actor_label()
        meshes = actor_meshes(actor)
        if label != target["label"]:
            raise RuntimeError(
                "Target label mismatch for {}: expected {}, got {}".format(
                    guid, target["label"], label
                )
            )
        if target["mesh"] not in meshes:
            raise RuntimeError(
                "Target mesh mismatch for {}: expected {}, got {}".format(
                    guid, target["mesh"], meshes
                )
            )
        if guid in found:
            raise RuntimeError("Duplicate target GUID in loaded level: " + guid)
        found[guid] = actor

    missing = sorted(set(TARGETS) - set(found))
    if missing:
        raise RuntimeError("Static residue cleanup aborted; missing targets: " + ", ".join(missing))

    deleted = []
    for guid in sorted(found):
        actor = found[guid]
        deleted.append(
            {
                "guid": guid,
                "label": actor.get_actor_label(),
                "meshes": actor_meshes(actor),
            }
        )
        if not subsystem.destroy_actor(actor):
            raise RuntimeError("Could not destroy target actor " + guid)

    remaining = []
    for actor in subsystem.get_all_level_actors():
        guid = actor_guid(actor)
        if guid in TARGETS:
            remaining.append(guid)
    if remaining:
        raise RuntimeError("Targets still exist after deletion: " + ", ".join(sorted(remaining)))

    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError("Could not save the cleaned level package")

    output = (
        Path(unreal.Paths.project_saved_dir())
        / "OntoTwinMigration"
        / "confirmed_static_residue_cleanup.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "level": LEVEL_PACKAGE,
                "deleted_count": len(deleted),
                "deleted": deleted,
                "remaining_target_count": 0,
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )
    unreal.log("OntoTwin confirmed static residue cleanup deleted {} actors".format(len(deleted)))


if __name__ == "__main__":
    main()
