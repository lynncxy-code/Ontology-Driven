"""Export high-confidence ZHHZ mother-Actor candidates as assembly_v1.

This automation intentionally changes folder paths only in editor memory, invokes
ATwinSceneManager's real exporter, restores every folder, destroys its temporary
manager, and exits without saving a level.  It is an inventory/export step, not
the destructive cleanup step.
"""

from __future__ import annotations

import json
import os
import shutil
import traceback
import csv

import unreal


MAP_PATH = "/Game/AVIC_Show/Art/Maps/L_AVIC_SHOW_Main"
DATASMITH_AUDIT = (
    r"C:\Users\ADMIN\Documents\zhhz\.codex_migration_work"
    r"\audit\AVIC_0706_group_audit.json"
)
CROSSWALK = (
    r"C:\Users\ADMIN\Documents\zhhz\.codex_migration_work"
    r"\audit\zhhz_migration_crosswalk.json"
)
AUDIT_EXPORT = os.environ.get(
    "ZHHZ_AUDIT_EXPORT",
    (
        r"C:\Users\ADMIN\Documents\zhhz\.codex_migration_work"
        r"\audit\ue_actors_export_all_candidates.json"
    ),
)
AUDIT_SUMMARY = os.environ.get(
    "ZHHZ_AUDIT_SUMMARY",
    (
        r"C:\Users\ADMIN\Documents\zhhz\.codex_migration_work"
        r"\audit\ue_candidate_export_summary.json"
    ),
)
TEMP_FOLDER = "ToMigrateAudit"


def _load_json(path):
    with open(path, "r", encoding="utf-8") as stream:
        return json.load(stream)


def _guid_text(actor):
    try:
        try:
            guid = actor.get_actor_guid()
        except Exception:
            guid = actor.get_editor_property("actor_guid")
        try:
            text = guid.to_string()
        except Exception:
            text = str(guid)
        return "".join(character for character in str(text).upper() if character in "0123456789ABCDEF")
    except Exception:
        return ""


def _folder_text(actor):
    try:
        folder = actor.get_folder_path()
        try:
            return str(folder.to_string())
        except Exception:
            return str(folder)
    except Exception:
        return ""


def _top_candidate_guids():
    datasmith = _load_json(DATASMITH_AUDIT)
    crosswalk = _load_json(CROSSWALK)
    crosswalk_by_handle = {
        row.get("datasmith_handle"): row for row in crosswalk.get("groups") or []
    }
    selection_csv = os.environ.get("ZHHZ_SELECTION_CSV", "").strip()
    selected_handles = None
    if selection_csv:
        with open(selection_csv, "r", encoding="utf-8-sig", newline="") as stream:
            selected_handles = {
                str(row.get("handle") or "").strip()
                for row in csv.DictReader(stream)
                if str(row.get("handle") or "").strip()
            }
        scoped_handles = {
            str(row.get("datasmith_handle") or "").strip()
            for row in crosswalk.get("groups") or []
            if str(row.get("datasmith_handle") or "").strip() in selected_handles
            and row.get("ue_guid")
        }
    else:
        scoped_handles = {
            str(row.get("datasmith_handle") or "").strip()
            for row in crosswalk.get("groups") or []
            if row.get("heuristic_class") == "candidate_equipment_group"
            and row.get("ue_scene_root") == "0713"
            and row.get("ue_guid")
        }

    selected = []
    for group in datasmith.get("groups") or []:
        handle = str(group.get("handle") or "").strip()
        if handle not in scoped_handles:
            continue
        if selected_handles is None:
            candidate_ancestors = [
                str(ancestor)
                for ancestor in group.get("ancestor_group_handles") or []
                if str(ancestor) in scoped_handles
            ]
            if candidate_ancestors:
                continue
        row = crosswalk_by_handle.get(handle) or {}
        guid = "".join(
            character
            for character in str(row.get("ue_guid") or "").upper()
            if character in "0123456789ABCDEF"
        )
        if guid:
            selected.append({
                "guid": guid,
                "label": row.get("label"),
                "datasmith_handle": handle,
                "datasmith_path": row.get("datasmith_path"),
                "geometry_signature": row.get("geometry_signature"),
            })
    if selected_handles is not None:
        found_handles = {item["datasmith_handle"] for item in selected}
        missing_handles = sorted(selected_handles - found_handles)
        if missing_handles:
            raise RuntimeError(
                "Selection CSV contains handles without a UE crosswalk match: "
                + ", ".join(missing_handles)
            )
    limit_text = os.environ.get("ZHHZ_EXPORT_LIMIT", "").strip()
    if limit_text:
        limit = max(0, int(limit_text))
        return selected[:limit]
    return selected


def _set_folder(actor, value):
    actor.set_folder_path(unreal.Name(value or ""))


def main():
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if level_subsystem.load_level(MAP_PATH) is False:
        raise RuntimeError("Unable to load " + MAP_PATH)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(actor_subsystem.get_all_level_actors())
    actor_by_guid = {_guid_text(actor): actor for actor in actors if _guid_text(actor)}
    requested = _top_candidate_guids()
    found = []
    missing = []
    original_folders = []
    manager = None
    manager_original_properties = {}

    try:
        for item in requested:
            actor = actor_by_guid.get(item["guid"])
            if actor is None:
                missing.append(item)
                continue
            original_folders.append((actor, _folder_text(actor)))
            _set_folder(actor, TEMP_FOLDER)
            found.append(item)

        manager_class = unreal.load_class(None, "/Script/OntoTwinSync.TwinSceneManager")
        if manager_class is None:
            raise RuntimeError("OntoTwinSync.TwinSceneManager class is unavailable")
        # The exporter obtains the editor world through GEditor and needs no world-owned
        # manager state.  Calling it on the class default object avoids spawning/saving
        # a temporary Actor (spawn_actor_from_class crashes in this 30k-Actor level).
        manager = unreal.get_default_object(manager_class)
        if manager is None:
            raise RuntimeError("Failed to resolve TwinSceneManager class default object")
        desired_properties = {
            "backend_base_url": "http://127.0.0.1:5000",
            "ue_project_id": "ueproj_ZHHZ",
            "ue_project_name": "ZHHZ",
            "scene_id": "",
            "migration_folder_name": TEMP_FOLDER,
        }
        for property_name, value in desired_properties.items():
            manager_original_properties[property_name] = manager.get_editor_property(property_name)
            manager.set_editor_property(property_name, value)
        manager.export_selected_actors_for_migration()

        project_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
        saved_export = os.path.join(
            project_dir, "Saved", "OntoTwinMigration", "ue_actors_export.json"
        )
        if not os.path.isfile(saved_export):
            raise RuntimeError("Exporter did not create " + saved_export)
        os.makedirs(os.path.dirname(AUDIT_EXPORT), exist_ok=True)
        shutil.copy2(saved_export, AUDIT_EXPORT)

        exported = _load_json(AUDIT_EXPORT)
        summary = {
            "schema_version": "zhhz_candidate_export_summary_v1",
            "read_only_level": True,
            "map_saved": False,
            "requested_top_mothers": len(requested),
            "found_top_mothers": len(found),
            "missing_top_mothers": missing,
            "exported_mothers": len(exported.get("actors") or []),
            "exported_source_actors": sum(
                len(actor.get("source_actor_guids") or [])
                for actor in exported.get("actors") or []
            ),
            "exported_render_parts": sum(
                len(actor.get("render_parts") or [])
                for actor in exported.get("actors") or []
            ),
            "unsupported_mothers": sum(
                bool(actor.get("unsupported_components"))
                for actor in exported.get("actors") or []
            ),
            "saved_export": saved_export,
            "audit_export": AUDIT_EXPORT,
        }
        with open(AUDIT_SUMMARY, "w", encoding="utf-8") as stream:
            json.dump(summary, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        unreal.log("ZHHZ assembly candidate export: " + json.dumps(summary, ensure_ascii=False))
    finally:
        for actor, folder in original_folders:
            try:
                _set_folder(actor, "" if folder in ("None", "none") else folder)
            except Exception as exc:
                unreal.log_error("Failed to restore folder for {}: {}".format(actor, exc))
        if manager is not None:
            for property_name, value in manager_original_properties.items():
                try:
                    manager.set_editor_property(property_name, value)
                except Exception as exc:
                    unreal.log_warning(
                        "Failed to restore manager CDO property {}: {}".format(property_name, exc)
                    )


try:
    main()
except Exception:
    unreal.log_error("ZHHZ candidate export failed:\n" + traceback.format_exc())
    raise
