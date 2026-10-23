import json
import re
from pathlib import Path
import unreal

CHANGE_ROOT = Path(r"D:\ZHHZ\ZHHZ-Offline-Changes-20260821-113527\ZHHZ-Offline-Changes-20260821-113527")
BACKUP_PROJECT = Path(r"D:\ZHHZ\Backups\OfflineMerge-20260821-113527\Database\customer-edit-before-ds_1784694647848-20260821T043713Z.json")

def load_json(path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)

def norm(value):
    if value is None:
        return ""
    if hasattr(value, "to_string"):
        value = value.to_string()
    text = str(value).upper()
    match = re.search(r"([0-9A-F]{8})-([0-9A-F]{4})-([0-9A-F]{4})-([0-9A-F]{4})-([0-9A-F]{12})", text)
    if match:
        return "".join(match.groups())
    words = re.findall(r"(?<![0-9A-F])[0-9A-F]{8}(?![0-9A-F])", text)
    if len(words) >= 4:
        return "".join(words[-4:])
    compact = "".join(ch for ch in text if ch in "0123456789ABCDEF")
    return compact if len(compact) == 32 else ""

def get_guid(actor):
    getter = getattr(actor, "get_actor_guid", None)
    if callable(getter):
        guid = norm(getter())
        if guid:
            return guid
    for name in ("actor_guid", "actor_instance_guid"):
        try:
            guid = norm(actor.get_editor_property(name))
        except Exception:
            continue
        if guid:
            return guid
    return ""

def package(path):
    value = str(path).replace("\\", "/")
    return "/Game/" + value[8:-5] if value.lower().startswith("content/") and value.lower().endswith(".umap") else ""

def main():
    changes = load_json(CHANGE_ROOT / "customer-overrides.json")
    report = load_json(CHANGE_ROOT / "return-report.json")
    backup = load_json(BACKUP_PROJECT)
    targets = set()
    labels = set()
    for operation in changes.get("instance_operations") or []:
        if operation.get("op") not in {"delete", "replace"}:
            continue
        instance_id = operation["instance_id"]
        original = backup["instances"][instance_id]
        root = norm(instance_id[3:])
        if root:
            targets.add(root)
        render = original.get("render_config") or {}
        for value in render.get("source_actor_guids") or []:
            guid = norm(value)
            if guid:
                targets.add(guid)
        for part in render.get("render_parts") or []:
            guid = norm(part.get("source_actor_guid"))
            if guid:
                targets.add(guid)
            label = str(part.get("source_actor_label") or "")
            if label:
                labels.add(label)
    maps = []
    for value in (report.get("changed_files") or []) + (report.get("added_files") or []):
        item = package(value)
        if item and item not in maps:
            maps.append(item)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    result = {"target_guids": len(targets), "target_labels": len(labels), "maps": [], "samples": []}
    for item in maps:
        if not unreal.EditorLoadingAndSavingUtils.load_map(item):
            raise RuntimeError("Could not load " + item)
        readable = 0
        guid_hits = 0
        label_hits = 0
        for actor in subsystem.get_all_level_actors():
            guid = get_guid(actor)
            label = actor.get_actor_label()
            readable += int(bool(guid))
            is_guid = guid in targets
            is_label = label in labels
            guid_hits += int(is_guid)
            label_hits += int(is_label)
            if (is_guid or is_label) and len(result["samples"]) < 200:
                result["samples"].append({"map": item, "label": label, "guid": guid, "guid_hit": is_guid, "label_hit": is_label})
        result["maps"].append({"map": item, "guid_readable": readable, "guid_hits": guid_hits, "label_hits": label_hits})
        unreal.log("OntoTwin residue diagnostic {} readable={} guid_hits={} label_hits={}".format(item, readable, guid_hits, label_hits))
    output = Path(unreal.Paths.project_saved_dir()) / "OntoTwinMigration" / "offline_actor_residue_diagnostic.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    unreal.log("OntoTwin residue diagnostic summary " + json.dumps(result["maps"], ensure_ascii=False))

if __name__ == "__main__":
    main()