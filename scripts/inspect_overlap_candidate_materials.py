import json
import re
from pathlib import Path

import unreal


LEVEL_PACKAGE = "/Game/AVIC_Show/Art/Maps/L_AS_Arch"
OVERLAP_FILE = Path(
    r"D:\ZHHZ\ZHHZ\Saved\OntoTwinMigration\offline_model_overlap_diagnostic.json"
)


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


def component_details(actor):
    details = []
    try:
        components = actor.get_components_by_class(unreal.StaticMeshComponent)
    except Exception:
        components = []
    for component in components:
        try:
            mesh = component.get_editor_property("static_mesh")
        except Exception:
            mesh = None
        materials = []
        try:
            count = component.get_num_materials()
        except Exception:
            count = 0
        for index in range(count):
            try:
                material = component.get_material(index)
            except Exception:
                material = None
            if material:
                materials.append(material.get_path_name())
        details.append(
            {
                "component": component.get_name(),
                "mesh": mesh.get_path_name() if mesh else "",
                "materials": materials,
            }
        )
    return details


def main():
    with OVERLAP_FILE.open("r", encoding="utf-8-sig") as handle:
        overlap = json.load(handle)
    wanted = set()
    wanted_labels = set()
    for target in overlap.get("targets") or []:
        for candidate in target.get("candidates") or []:
            value = norm_guid(candidate.get("guid"))
            if value:
                wanted.add(value)
            if candidate.get("label"):
                wanted_labels.add(str(candidate["label"]))
    if not unreal.EditorLoadingAndSavingUtils.load_map(LEVEL_PACKAGE):
        raise RuntimeError("Could not load " + LEVEL_PACKAGE)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    records = []
    for actor in subsystem.get_all_level_actors():
        guid = actor_guid(actor)
        label = actor.get_actor_label()
        if guid not in wanted and label not in wanted_labels:
            continue
        records.append(
            {
                "guid": guid,
                "label": label,
                "class": actor.get_class().get_path_name(),
                "components": component_details(actor),
            }
        )
    records.sort(key=lambda value: (value["label"], value["guid"]))
    output = (
        Path(unreal.Paths.project_saved_dir())
        / "OntoTwinMigration"
        / "offline_overlap_candidate_materials.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump({"actor_count": len(records), "actors": records}, handle, ensure_ascii=False, indent=2)
    unreal.log("OntoTwin overlap material audit wrote " + str(output))


if __name__ == "__main__":
    main()
