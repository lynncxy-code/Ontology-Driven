"""Read-only fresh-start verification for all Renderpeople adapters."""

import json
import unreal


CHARACTER_DIR = "/Game/OntoTwin/SceneInteraction/Characters/RenderPeople"
SKIN_DIR = "/Game/OntoTwin/SceneInteraction/Skins/RenderPeople"
CHARACTERS = ("Carla", "Claudia", "Eric", "Manuel", "Nathan", "Sophia")
GROUND_ROOT = "/Game/Art/A08_Characters/00_Ground_Staff/ThirdPerson"
EXPECTED_VISIBLE_ANIM = (
    f"{GROUND_ROOT}/SkeletonIK/myAnimBlueprint.myAnimBlueprint_C"
)
EXPECTED_SOURCE_MESH = (
    f"{GROUND_ROOT}/Meshes/SKM_Quinn_Simple.SKM_Quinn_Simple"
)
EXPECTED_SOURCE_ANIM = (
    f"{GROUND_ROOT}/Mannequin/Mannequins/Animations/ABP_Quinn.ABP_Quinn_C"
)
EXPECTED_ROUTE_ANIMATION = (
    f"{GROUND_ROOT}/Mannequin/Mannequins/Animations/Quinn/"
    "MF_Walk_Fwd.MF_Walk_Fwd"
)


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
        source_mesh = character.get_editor_property("animation_source_mesh")
        route_animation = character.get_editor_property("auto_route_animation")
        item["source_skeleton"] = path_name(
            source_mesh.get_editor_property("skeleton") if source_mesh else None
        )
        item["route_skeleton"] = path_name(
            route_animation.get_editor_property("skeleton")
            if route_animation
            else None
        )
    item["success"] = (
        item["character_loaded"]
        and item["skin_loaded"]
        and item.get("character_class") == "TwinCharacterAsset"
        and item.get("skin_class") == "TwinSkinAsset"
        and item.get("skin_skeleton_id") == "skeleton.renderpeople.ue4.v1"
        and bool(item.get("character_mesh"))
        and item.get("character_mesh") == item.get("skin_mesh")
        and item.get("character_anim_class") == EXPECTED_VISIBLE_ANIM
        and item.get("skin_anim_class") == EXPECTED_VISIBLE_ANIM
        and item.get("source_mesh") == EXPECTED_SOURCE_MESH
        and item.get("source_anim_class") == EXPECTED_SOURCE_ANIM
        and item.get("route_animation") == EXPECTED_ROUTE_ANIMATION
        and bool(item.get("source_skeleton"))
        and item.get("source_skeleton") == item.get("route_skeleton")
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
