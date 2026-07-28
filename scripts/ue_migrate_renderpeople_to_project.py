"""Migrate the six OntoTwin RenderPeople adapters and their dependencies.

This script is intentionally conservative: existing destination packages are
never overwritten. Run it through UnrealEditor-Cmd against the source project
while both interactive editors are closed.
"""

import json
import os

import unreal


DESTINATION_CONTENT = os.environ.get("ONTOTWIN_MIGRATION_DESTINATION", "").strip()
CHARACTERS = ("Carla", "Claudia", "Eric", "Manuel", "Nathan", "Sophia")
CHARACTER_DIR = "/Game/OntoTwin/SceneInteraction/Characters/RenderPeople"
SKIN_DIR = "/Game/OntoTwin/SceneInteraction/Skins/RenderPeople"


def fail(message):
    unreal.log_error(f"CODEX_MIGRATE_RENDERPEOPLE_ERROR: {message}")
    raise RuntimeError(message)


if not DESTINATION_CONTENT:
    fail("ONTOTWIN_MIGRATION_DESTINATION is required")

destination = os.path.abspath(DESTINATION_CONTENT).replace("\\", "/")
if os.path.basename(destination).lower() != "content":
    fail(f"Destination must be a UE project Content directory: {destination}")
if not os.path.isdir(destination):
    fail(f"Destination Content directory does not exist: {destination}")

packages = []
for display_name in CHARACTERS:
    character_name = f"RenderPeople{display_name}"
    packages.append(f"{CHARACTER_DIR}/{character_name}")
    packages.append(f"{SKIN_DIR}/{character_name}Default")

registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous([CHARACTER_DIR, SKIN_DIR], force_rescan=True)

missing = [
    package
    for package in packages
    if not unreal.EditorAssetLibrary.does_asset_exist(package)
]
if missing:
    fail(f"Source adapter assets are missing: {missing}")

options = unreal.MigrationOptions()
options.set_editor_property("prompt", False)
options.set_editor_property("ignore_dependencies", False)
options.set_editor_property("asset_conflict", unreal.AssetMigrationConflict.SKIP)

unreal.log("CODEX_MIGRATE_RENDERPEOPLE_BEGIN")
unreal.log(
    json.dumps(
        {
            "destination": destination,
            "package_count": len(packages),
            "packages": packages,
            "conflict_policy": "skip",
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)

unreal.AssetToolsHelpers.get_asset_tools().migrate_packages(
    packages,
    destination,
    options,
)

unreal.log("CODEX_MIGRATE_RENDERPEOPLE_END")
unreal.SystemLibrary.quit_editor()
