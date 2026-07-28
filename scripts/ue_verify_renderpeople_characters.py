"""Read-only fresh-start verification for all Renderpeople adapters."""

import json
import unreal


CHARACTER_DIR = "/Game/OntoTwin/SceneInteraction/Characters/RenderPeople"
SKIN_DIR = "/Game/OntoTwin/SceneInteraction/Skins/RenderPeople"
CHARACTERS = ("Carla", "Claudia", "Eric", "Manuel", "Nathan", "Sophia")


def path_name(value):
    return value.get_path_name() if value else None


results = []
for display_name in CHARACTERS:
    character_name = f"RenderPeople{display_name}"
    skin_name = f"{character_name}Default"
    character = unreal.load_asset(f"{CHARACTER_DIR}/{character_name}")
    skin = unreal.load_asset(f"{SKIN_DIR}/{skin_name}")
    item = {
        "display_name": display_name,
        "character_loaded": bool(character),
        "skin_loaded": bool(skin),
    }
    if character and skin:
        item.update(
            {
                "character_class": character.get_class().get_name(),
                "character_mesh": path_name(
                    character.get_editor_property("base_mesh")
                ),
                "character_anim_class": path_name(
                    character.get_editor_property("anim_instance_class")
                ),
                "source_mesh": path_name(
                    character.get_editor_property("animation_source_mesh")
                ),
                "source_anim_class": path_name(
                    character.get_editor_property(
                        "animation_source_anim_instance_class"
                    )
                ),
                "route_animation": path_name(
                    character.get_editor_property("auto_route_animation")
                ),
                "skin_class": skin.get_class().get_name(),
                "skin_skeleton_id": str(
                    skin.get_editor_property("skeleton_id")
                ),
                "skin_mesh": path_name(skin.get_editor_property("mesh")),
                "skin_anim_class": path_name(
                    skin.get_editor_property("anim_instance_class")
                ),
            }
        )
    item["success"] = (
        item["character_loaded"]
        and item["skin_loaded"]
        and item.get("character_class") == "TwinCharacterAsset"
        and item.get("skin_class") == "TwinSkinAsset"
        and item.get("skin_skeleton_id") == "skeleton.renderpeople.ue4.v1"
        and bool(item.get("character_mesh"))
        and item.get("character_mesh") == item.get("skin_mesh")
        and bool(item.get("character_anim_class"))
        and item.get("character_anim_class") == item.get("skin_anim_class")
        and bool(item.get("source_mesh"))
        and bool(item.get("source_anim_class"))
        and bool(item.get("route_animation"))
    )
    results.append(item)

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "AssetManager.DumpTypeSummary")
result = {
    "success": all(item["success"] for item in results),
    "character_count": len(results),
    "characters": results,
}
unreal.log("CODEX_VERIFY_RENDERPEOPLE_BEGIN")
unreal.log(json.dumps(result, ensure_ascii=False, sort_keys=True))
unreal.log("CODEX_VERIFY_RENDERPEOPLE_END")
unreal.SystemLibrary.quit_editor()
