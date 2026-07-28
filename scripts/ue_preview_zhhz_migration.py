"""Spawn and audit the ZHHZ migration preview without saving a level."""

from __future__ import annotations

import json
import os
import traceback

import unreal


MAP_PATH = "/Game/AVIC_Show/Art/Maps/L_AVIC_SHOW_Main"


def main():
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if level_subsystem.load_level(MAP_PATH) is False:
        raise RuntimeError("Unable to load " + MAP_PATH)

    manager_class = unreal.load_class(None, "/Script/OntoTwinSync.TwinSceneManager")
    if manager_class is None:
        raise RuntimeError("OntoTwinSync.TwinSceneManager class is unavailable")
    manager = unreal.get_default_object(manager_class)
    if manager is None:
        raise RuntimeError("Failed to resolve TwinSceneManager class default object")

    original_properties = {}
    desired_properties = {
        "backend_base_url": "http://127.0.0.1:5000",
        "ue_project_id": "ueproj_ZHHZ",
        "ue_project_name": "ZHHZ",
        "scene_id": "",
    }
    try:
        for property_name, value in desired_properties.items():
            original_properties[property_name] = manager.get_editor_property(property_name)
            manager.set_editor_property(property_name, value)

        manager.preview_migrated_actors_from_snapshot_file()
        project_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
        audit_path = os.path.join(
            project_dir, "Saved", "OntoTwinMigration", "ue_preview_audit.json"
        )
        if not os.path.isfile(audit_path):
            raise RuntimeError("Preview audit was not created: " + audit_path)
        with open(audit_path, "r", encoding="utf-8") as stream:
            audit = json.load(stream)
        if not audit.get("passed"):
            raise RuntimeError(
                "Preview audit failed: " + json.dumps(audit, ensure_ascii=False)
            )
        unreal.log("ZHHZ migration preview audit PASS: " + json.dumps(audit, ensure_ascii=False))
    finally:
        for property_name, value in original_properties.items():
            try:
                manager.set_editor_property(property_name, value)
            except Exception as exc:
                unreal.log_warning(
                    "Failed to restore manager CDO property {}: {}".format(property_name, exc)
                )


try:
    main()
except Exception:
    unreal.log_error("ZHHZ migration preview failed:\n" + traceback.format_exc())
    raise
