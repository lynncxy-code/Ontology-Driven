"""Write the Ground Staff dependency closure for a conservative file migration."""

import json
import os

import unreal


MANIFEST_PATH = os.environ.get("ONTOTWIN_GROUND_STAFF_MANIFEST", "").strip()
GROUND_ROOT = "/Game/Art/A08_Characters/00_Ground_Staff"
ROOT_PACKAGES = (
    f"{GROUND_ROOT}/ThirdPerson/SkeletonIK/SK_Charactor",
    f"{GROUND_ROOT}/ThirdPerson/SkeletonIK/myAnimBlueprint",
    f"{GROUND_ROOT}/ThirdPerson/CharacterMaterial/gray",
    f"{GROUND_ROOT}/ThirdPerson/CharacterMaterial/green",
)


def fail(message):
    unreal.log_error(f"ONTOTWIN_GROUND_STAFF_MIGRATE_ERROR: {message}")
    raise RuntimeError(message)


if not MANIFEST_PATH:
    fail("ONTOTWIN_GROUND_STAFF_MANIFEST is required")

registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.scan_paths_synchronous([GROUND_ROOT], force_rescan=True)
missing = [package for package in ROOT_PACKAGES if not unreal.EditorAssetLibrary.does_asset_exist(package)]
if missing:
    fail(f"Ground Staff source assets are missing: {missing}")

options = unreal.AssetRegistryDependencyOptions(
    include_soft_package_references=True,
    include_hard_package_references=True,
    include_searchable_names=False,
    include_soft_management_references=True,
    include_hard_management_references=True,
)
closure = set(ROOT_PACKAGES)
pending = list(ROOT_PACKAGES)
unresolved_game_dependencies = set()
while pending:
    package = pending.pop()
    for dependency in registry.get_dependencies(package, options):
        value = str(dependency)
        if not value.startswith("/Game/"):
            continue
        if not unreal.EditorAssetLibrary.does_asset_exist(value):
            unresolved_game_dependencies.add(value)
            continue
        if value not in closure:
            closure.add(value)
            pending.append(value)

external_game_dependencies = {
    package for package in closure if not package.startswith(GROUND_ROOT + "/")
}

manifest = {
    "success": True,
    "ground_root": GROUND_ROOT,
    "roots": sorted(ROOT_PACKAGES),
    "packages": sorted(closure),
    "external_game_dependencies": sorted(external_game_dependencies),
    "unresolved_game_dependencies": sorted(unresolved_game_dependencies),
}
os.makedirs(os.path.dirname(os.path.abspath(MANIFEST_PATH)), exist_ok=True)
with open(MANIFEST_PATH, "w", encoding="utf-8") as stream:
    json.dump(manifest, stream, ensure_ascii=False, indent=2, sort_keys=True)

unreal.log("ONTOTWIN_GROUND_STAFF_MIGRATE_BEGIN")
unreal.log(
    json.dumps(
        {
            "success": True,
            "manifest": os.path.abspath(MANIFEST_PATH),
            "package_count": len(closure),
            "external_game_dependency_count": len(external_game_dependencies),
            "unresolved_game_dependency_count": len(unresolved_game_dependencies),
        },
        sort_keys=True,
    )
)
unreal.log("ONTOTWIN_GROUND_STAFF_MIGRATE_END")
unreal.SystemLibrary.quit_editor()
