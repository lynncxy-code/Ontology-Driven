import os
import traceback

import unreal


MAP_PATH = "/Game/SCC_W9/Art/Maps/L_SCC_W9_Main"
AUDIT_PATH = r"D:\SCC\SCC2\scc2\Saved\OntoTwinMigration\ue_preview_audit.json"


def main():
    unreal.log("CODEX_W9_PREVIEW_BEGIN")
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if world is None:
        raise RuntimeError("Failed to load map: " + MAP_PATH)

    manager_class = unreal.load_class(None, "/Script/OntoTwinSync.TwinSceneManager")
    if manager_class is None:
        raise RuntimeError("TwinSceneManager class is unavailable")
    unreal.log("CODEX_W9_PREVIEW_CLASS_LOADED")

    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    unreal.log("CODEX_W9_PREVIEW_SPAWN_BEGIN")
    manager = subsystem.spawn_actor_from_class(
        manager_class,
        unreal.Vector(0.0, 0.0, 0.0),
        unreal.Rotator(0.0, 0.0, 0.0),
    )
    if manager is None:
        raise RuntimeError("Failed to spawn TwinSceneManager")
    unreal.log("CODEX_W9_PREVIEW_SPAWN_DONE")

    manager.preview_migrated_actors_from_snapshot_file()
    unreal.log("CODEX_W9_PREVIEW_CALL_DONE")
    if not os.path.isfile(AUDIT_PATH):
        raise RuntimeError("Preview audit was not created: " + AUDIT_PATH)
    unreal.log("CODEX_W9_PREVIEW_DONE audit=" + AUDIT_PATH)


try:
    main()
except Exception:
    unreal.log_error("CODEX_W9_PREVIEW_FAILED\n" + traceback.format_exc())
    raise
