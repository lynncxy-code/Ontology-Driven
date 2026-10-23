"""Create or verify the plugin-owned AlwaysCook label for OntoTwin UI assets.

Run through UnrealEditor-Cmd with PythonScriptPlugin enabled and the interactive
editor closed for the target project. The label removes the need for every host
project to add /OntoTwinSync/UI to DirectoriesToAlwaysCook.
"""

import json

import unreal


LABEL_DIR = "/OntoTwinSync/UI"
LABEL_NAME = "PAL_OntoTwinUI"
LABEL_PATH = "{}/{}".format(LABEL_DIR, LABEL_NAME)
MARKER = "ONTOTWIN_UI_COOK_LABEL"


def emit(name, payload, error=False):
    message = "{}_{} {}".format(
        MARKER,
        name,
        json.dumps(payload, ensure_ascii=True, sort_keys=True),
    )
    if error:
        unreal.log_error(message)
    else:
        unreal.log(message)


def set_bool_property(asset, candidates, value):
    last_error = None
    for candidate in candidates:
        try:
            asset.set_editor_property(candidate, value)
            return candidate
        except Exception as exc:  # Unreal Python names differ across minors.
            last_error = exc
    raise RuntimeError(
        "Could not set any of {}: {}".format(candidates, last_error)
    )


def create_label():
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", unreal.PrimaryAssetLabel)
    return asset_tools.create_asset(
        LABEL_NAME,
        LABEL_DIR,
        unreal.PrimaryAssetLabel,
        factory,
    )


def main():
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_registry.scan_paths_synchronous(
        [LABEL_DIR], force_rescan=True, ignore_deny_list_scan_filters=True
    )
    label = None
    if unreal.EditorAssetLibrary.does_asset_exist(LABEL_PATH):
        label = unreal.EditorAssetLibrary.load_asset(LABEL_PATH)
    action = "verified"
    if not label:
        label = create_label()
        action = "created"
    if not label:
        raise RuntimeError("Could not create {}".format(LABEL_PATH))

    rules = label.get_editor_property("rules")
    rules.set_editor_property(
        "cook_rule", unreal.PrimaryAssetCookRule.ALWAYS_COOK
    )
    rules.set_editor_property("chunk_id", -1)
    rules.set_editor_property("priority", 1)
    rules.set_editor_property("apply_recursively", True)
    label.set_editor_property("rules", rules)

    directory_property = set_bool_property(
        label,
        ("label_assets_in_my_directory", "b_label_assets_in_my_directory"),
        True,
    )
    runtime_property = set_bool_property(
        label,
        ("is_runtime_label", "b_is_runtime_label"),
        True,
    )

    try:
        saved = unreal.EditorAssetLibrary.save_loaded_asset(
            label, only_if_is_dirty=False
        )
    except TypeError:
        saved = unreal.EditorAssetLibrary.save_loaded_asset(label)
    if saved is False:
        raise RuntimeError("Could not save {}".format(LABEL_PATH))

    emit(
        "END",
        {
            "success": True,
            "action": action,
            "label": label.get_path_name(),
            "directory_property": directory_property,
            "runtime_property": runtime_property,
            "cook_rule": str(rules.get_editor_property("cook_rule")),
        },
    )
    unreal.SystemLibrary.quit_editor()


try:
    main()
except Exception as exc:
    emit(
        "ERROR",
        {
            "success": False,
            "exception_type": type(exc).__name__,
            "message": str(exc),
        },
        error=True,
    )
    raise
