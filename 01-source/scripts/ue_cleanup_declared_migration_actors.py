"""Audit or remove exactly the UE actors declared by a migration result.

Required environment:
  ONTOTWIN_CLEANUP_LEVEL=/Game/path/to/Level

Optional environment:
  ONTOTWIN_APPLY_ACTOR_CLEANUP=1      Destroy actors and save the level.
  ONTOTWIN_MIGRATION_RESULT=<path>    Defaults to Saved/OntoTwinMigration/
                                      ue_migration_result.json.

The apply path is deliberately fail-closed: every unique GUID in the signed
migration result must resolve exactly once before the first actor is destroyed.
"""

import json
import os
import re
from pathlib import Path

import unreal


LEVEL_PACKAGE = os.environ.get("ONTOTWIN_CLEANUP_LEVEL", "").strip()
APPLY = os.environ.get("ONTOTWIN_APPLY_ACTOR_CLEANUP") == "1"
RESULT_PATH = Path(
    os.environ.get("ONTOTWIN_MIGRATION_RESULT", "").strip()
    or (
        Path(unreal.Paths.project_saved_dir())
        / "OntoTwinMigration"
        / "ue_migration_result.json"
    )
)


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
    compact = "".join(ch for ch in text if ch in "0123456789ABCDEF")
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


def actor_record(actor, guid):
    meshes = []
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        try:
            mesh = component.get_editor_property("static_mesh")
        except Exception:
            mesh = None
        if mesh:
            meshes.append(mesh.get_path_name())
    return {
        "guid": guid,
        "label": actor.get_actor_label(),
        "class": actor.get_class().get_path_name(),
        "meshes": sorted(set(meshes)),
    }


def load_targets():
    with RESULT_PATH.open("r", encoding="utf-8-sig") as handle:
        result = json.load(handle)
    if result.get("schema_version") != "assembly_v1":
        raise RuntimeError("Cleanup requires an assembly_v1 migration result")
    replacement = result.get("replacement") or {}
    if replacement.get("applied") is not True:
        raise RuntimeError("Cleanup requires replacement.applied=true")
    raw_guids = result.get("delete_actor_guids") or []
    targets = [normalize_guid(value) for value in raw_guids]
    if any(not value for value in targets):
        raise RuntimeError("Migration result contains an invalid cleanup GUID")
    if len(set(targets)) != len(targets):
        raise RuntimeError("Migration result contains duplicate cleanup GUIDs")
    expected = int(replacement.get("delete_actor_guid_count") or 0)
    if expected <= 0 or len(targets) != expected:
        raise RuntimeError(
            "Cleanup count mismatch: manifest={} result={}".format(
                expected, len(targets)
            )
        )
    return set(targets), replacement


def scan_targets(subsystem, targets):
    found = {}
    readable_guid_count = 0
    for actor in subsystem.get_all_level_actors():
        guid = actor_guid(actor)
        if guid:
            readable_guid_count += 1
        if guid not in targets:
            continue
        if guid in found:
            raise RuntimeError("Duplicate target ActorGuid in level: " + guid)
        found[guid] = actor
    if readable_guid_count == 0:
        raise RuntimeError("Loaded level exposes no readable ActorGuid values")
    missing = sorted(targets - set(found))
    if missing:
        raise RuntimeError(
            "Cleanup aborted before deletion; {} target GUID(s) missing: {}".format(
                len(missing), ", ".join(missing[:10])
            )
        )
    return found, readable_guid_count


def main():
    if not LEVEL_PACKAGE.startswith("/Game/"):
        raise RuntimeError("ONTOTWIN_CLEANUP_LEVEL must be a /Game/... package")
    targets, replacement = load_targets()
    if not unreal.EditorLoadingAndSavingUtils.load_map(LEVEL_PACKAGE):
        raise RuntimeError("Could not load cleanup level: " + LEVEL_PACKAGE)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    found, readable_count = scan_targets(subsystem, targets)
    records = [actor_record(found[guid], guid) for guid in sorted(found)]

    if APPLY:
        for guid in sorted(found):
            if not subsystem.destroy_actor(found[guid]):
                raise RuntimeError("Could not destroy declared actor: " + guid)
        residual = {
            actor_guid(actor)
            for actor in subsystem.get_all_level_actors()
            if actor_guid(actor) in targets
        }
        if residual:
            raise RuntimeError(
                "Declared actors remain before save: " + ", ".join(sorted(residual))
            )
        if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
            raise RuntimeError("Could not save the cleaned level package")

        # Cold reload the saved package; in-memory destruction alone is not an
        # acceptable cleanup result.
        if not unreal.EditorLoadingAndSavingUtils.load_map(LEVEL_PACKAGE):
            raise RuntimeError("Could not reload the cleaned level package")
        residual_after_reload = {
            actor_guid(actor)
            for actor in subsystem.get_all_level_actors()
            if actor_guid(actor) in targets
        }
        if residual_after_reload:
            raise RuntimeError(
                "Declared actors remain after reload: "
                + ", ".join(sorted(residual_after_reload))
            )

    audit = {
        "success": True,
        "mode": "apply" if APPLY else "audit",
        "level": LEVEL_PACKAGE,
        "migration_result": str(RESULT_PATH),
        "target_guid_count": len(targets),
        "matched_actor_count": len(found),
        "readable_actor_guid_count": readable_count,
        "remaining_target_count": 0 if APPLY else len(found),
        "replacement": replacement,
        "actors": records,
    }
    output = (
        Path(unreal.Paths.project_saved_dir())
        / "OntoTwinMigration"
        / (
            "declared_actor_cleanup_apply.json"
            if APPLY
            else "declared_actor_cleanup_audit.json"
        )
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(audit, handle, ensure_ascii=False, indent=2)
    unreal.log("CODEX_DECLARED_ACTOR_CLEANUP_BEGIN")
    unreal.log(json.dumps(audit, ensure_ascii=False, sort_keys=True))
    unreal.log("CODEX_DECLARED_ACTOR_CLEANUP_END")
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
