"""Remove source UE actors superseded by one accepted offline edit package.

Run through UnrealEditor-Cmd. The default mode is a read-only audit. Set
ONTOTWIN_APPLY_ACTOR_CLEANUP=1 to destroy matched actors and save dirty maps.
"""

import json
import os
import re
from pathlib import Path

import unreal


CHANGE_ROOT = Path(
    r"D:\ZHHZ\ZHHZ-Offline-Changes-20260821-113527"
    r"\ZHHZ-Offline-Changes-20260821-113527"
)
BACKUP_PROJECT = Path(
    r"D:\ZHHZ\Backups\OfflineMerge-20260821-113527\Database"
    r"\customer-edit-before-ds_1784694647848-20260821T043713Z.json"
)
APPLY = os.environ.get("ONTOTWIN_APPLY_ACTOR_CLEANUP") == "1"


def load_json(path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def normalize_guid(value):
    if value is None:
        return ""
    if hasattr(value, "to_string"):
        value = value.to_string()
    text = str(value).strip().upper()
    canonical = re.search(
        r"([0-9A-F]{8})-([0-9A-F]{4})-([0-9A-F]{4})-"
        r"([0-9A-F]{4})-([0-9A-F]{12})",
        text,
    )
    if canonical:
        return "".join(canonical.groups())
    words = re.findall(r"(?<![0-9A-F])[0-9A-F]{8}(?![0-9A-F])", text)
    if len(words) >= 4:
        return "".join(words[-4:])
    compact = "".join(character for character in text if character in "0123456789ABCDEF")
    return compact if len(compact) == 32 else ""


def actor_guid(actor):
    getter = getattr(actor, "get_actor_guid", None)
    if callable(getter):
        guid = normalize_guid(getter())
        if guid:
            return guid
    for property_name in ("actor_guid", "actor_instance_guid"):
        try:
            guid = normalize_guid(actor.get_editor_property(property_name))
        except Exception:
            continue
        if guid:
            return guid
    return ""


def collect_guids(record):
    result = set()
    if not isinstance(record, dict):
        return result
    instance_id = str(record.get("id") or record.get("instance_id") or "")
    if instance_id.lower().startswith("ue_"):
        guid = normalize_guid(instance_id[3:])
        if guid:
            result.add(guid)
    render = record.get("render_config") or {}
    for value in render.get("source_actor_guids") or []:
        guid = normalize_guid(value)
        if guid:
            result.add(guid)
    for part in render.get("render_parts") or []:
        if isinstance(part, dict):
            guid = normalize_guid(part.get("source_actor_guid"))
            if guid:
                result.add(guid)
    return result


def content_file_to_package(relative_path):
    normalized = str(relative_path).replace("\\", "/")
    if not normalized.lower().startswith("content/") or not normalized.lower().endswith(".umap"):
        return ""
    return "/Game/" + normalized[len("Content/") : -len(".umap")]


def main():
    changes = load_json(CHANGE_ROOT / "customer-overrides.json")
    report = load_json(CHANGE_ROOT / "return-report.json")
    backup = load_json(BACKUP_PROJECT)
    backup_instances = backup.get("instances") or {}

    target_guids = set()
    accepted_instance_ids = []
    for operation in changes.get("instance_operations") or []:
        if operation.get("op") not in {"delete", "replace"}:
            continue
        instance_id = str(operation.get("instance_id") or "")
        original = backup_instances.get(instance_id)
        if not isinstance(original, dict):
            raise RuntimeError("Missing original instance in merge backup: " + instance_id)
        target_guids.update(collect_guids({"id": instance_id, **original}))
        accepted_instance_ids.append(instance_id)

    protected_guids = set()
    for operation in changes.get("instance_operations") or []:
        guid = normalize_guid(operation.get("source_actor_guid"))
        if guid:
            protected_guids.add(guid)
        new_record = dict(operation)
        new_record.pop("instance_id", None)
        protected_guids.update(collect_guids(new_record))
    target_guids.difference_update(protected_guids)

    map_packages = []
    for relative_path in (report.get("changed_files") or []) + (report.get("added_files") or []):
        package = content_file_to_package(relative_path)
        if package and package not in map_packages:
            map_packages.append(package)
    if not map_packages:
        raise RuntimeError("Return report contains no changed UE maps")

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    found_guids = set()
    map_results = []
    guid_readable_count = 0
    for package in map_packages:
        world = unreal.EditorLoadingAndSavingUtils.load_map(package)
        if not world:
            raise RuntimeError("Could not load map: " + package)
        matched = []
        for actor in actor_subsystem.get_all_level_actors():
            guid = actor_guid(actor)
            if guid:
                guid_readable_count += 1
            if guid not in target_guids:
                continue
            matched.append((actor, guid))
            found_guids.add(guid)
        if APPLY:
            for actor, _ in matched:
                if not actor_subsystem.destroy_actor(actor):
                    raise RuntimeError("Could not destroy actor: " + actor.get_path_name())
            if matched and not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
                raise RuntimeError("Could not save dirty packages after map cleanup: " + package)
        map_results.append({"map": package, "matched_actor_count": len(matched)})
        unreal.log(
            "OntoTwin offline cleanup {}: {} actor(s){}".format(
                package, len(matched), " removed" if APPLY else " matched"
            )
        )

    if guid_readable_count == 0:
        raise RuntimeError("No loaded actor exposed an ActorGuid; cleanup cannot be verified safely")

    audit = {
        "mode": "apply" if APPLY else "audit",
        "accepted_instance_count": len(accepted_instance_ids),
        "target_guid_count": len(target_guids),
        "found_guid_count": len(found_guids),
        "unresolved_guid_count": len(target_guids - found_guids),
        "maps": map_results,
    }
    audit_path = Path(unreal.Paths.project_saved_dir()) / "OntoTwinMigration" / (
        "offline_actor_cleanup_apply.json" if APPLY else "offline_actor_cleanup_audit.json"
    )
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("w", encoding="utf-8") as handle:
        json.dump(audit, handle, ensure_ascii=False, indent=2)
    unreal.log("OntoTwin offline cleanup summary: " + json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    main()
