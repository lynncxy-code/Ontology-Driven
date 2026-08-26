"""Fresh-start verification for OntoTwinCharacterPack_Core."""

import json

import unreal


EXPECTED = (
    ("TwinCharacter", "TwinCharacterAsset", "ObserverBase", "/OntoTwinCharacterPack_Core/Characters/ObserverBase"),
    ("TwinCharacter", "TwinCharacterAsset", "MannyRobot", "/OntoTwinCharacterPack_Core/Characters/MannyRobot"),
    ("TwinSkin", "TwinSkinAsset", "ObserverGray", "/OntoTwinCharacterPack_Core/Skins/ObserverGray"),
    ("TwinSkin", "TwinSkinAsset", "ObserverGreen", "/OntoTwinCharacterPack_Core/Skins/ObserverGreen"),
    ("TwinSkin", "TwinSkinAsset", "MannyRobotDefault", "/OntoTwinCharacterPack_Core/Skins/MannyRobotDefault"),
)
GROUND_ROOT = "/Game/Art/A08_Characters/00_Ground_Staff/ThirdPerson"
GROUND_MESH_PATH = f"{GROUND_ROOT}/SkeletonIK/SK_Charactor"
GROUND_ANIM_PATH = f"{GROUND_ROOT}/SkeletonIK/myAnimBlueprint"
GROUND_GRAY_PATH = f"{GROUND_ROOT}/CharacterMaterial/gray.gray"
GROUND_GREEN_PATH = f"{GROUND_ROOT}/CharacterMaterial/green.green"
MANNY_MESH_PATH = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
MANNY_ANIM_PATH = "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed"
QUINN_MESH_PATH = f"{GROUND_ROOT}/Meshes/SKM_Quinn_Simple"
QUINN_ANIM_PATH = (
    f"{GROUND_ROOT}/Mannequin/Mannequins/Animations/ABP_Quinn"
)
QUINN_WALK_PATH = (
    f"{GROUND_ROOT}/Mannequin/Mannequins/Animations/Quinn/MF_Walk_Fwd"
)
MANNY_WALK_PATH = (
    "/Game/Characters/Mannequins/Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd"
)


def path_name(value):
    return value.get_path_name() if value else ""


def verify_skeleton_pair(mesh_path, anim_path):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    anim = unreal.EditorAssetLibrary.load_asset(anim_path)
    mesh_skeleton = mesh.get_editor_property("skeleton") if mesh else None
    anim_skeleton = anim.get_editor_property("target_skeleton") if anim else None
    result = {
        "mesh": mesh_path,
        "anim": anim_path,
        "mesh_skeleton": path_name(mesh_skeleton),
        "anim_skeleton": path_name(anim_skeleton),
    }
    result["success"] = (
        bool(result["mesh_skeleton"])
        and result["mesh_skeleton"] == result["anim_skeleton"]
    )
    return result


def verify_route_skeleton(mesh_path, animation_path):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    animation = unreal.EditorAssetLibrary.load_asset(animation_path)
    mesh_skeleton = mesh.get_editor_property("skeleton") if mesh else None
    animation_skeleton = (
        animation.get_editor_property("skeleton") if animation else None
    )
    result = {
        "mesh": mesh_path,
        "animation": animation_path,
        "mesh_skeleton": path_name(mesh_skeleton),
        "animation_skeleton": path_name(animation_skeleton),
    }
    result["success"] = (
        bool(result["mesh_skeleton"])
        and result["mesh_skeleton"] == result["animation_skeleton"]
    )
    return result


expected_meshes = {
    "ObserverBase": GROUND_MESH_PATH,
    "MannyRobot": MANNY_MESH_PATH,
    "ObserverGray": GROUND_MESH_PATH,
    "ObserverGreen": GROUND_MESH_PATH,
    "MannyRobotDefault": MANNY_MESH_PATH,
}
expected_uniform_materials = {
    "ObserverGray": GROUND_GRAY_PATH,
    "ObserverGreen": GROUND_GREEN_PATH,
}
results = []
for type_name, expected_class, asset_name, expected_path in EXPECTED:
    asset = unreal.EditorAssetLibrary.load_asset(expected_path)
    item = {
        "primary_asset_id": f"{type_name}:{asset_name}",
        "expected_path": expected_path,
        "asset_loaded": bool(asset),
        "asset_class": asset.get_class().get_name() if asset else "",
    }
    if asset:
        mesh_property = "base_mesh" if type_name == "TwinCharacter" else "mesh"
        item["mesh"] = path_name(asset.get_editor_property(mesh_property))
        item["anim_class"] = path_name(asset.get_editor_property("anim_instance_class"))
        if type_name == "TwinCharacter":
            item["animation_source_mesh"] = path_name(
                asset.get_editor_property("animation_source_mesh")
            )
            item["animation_source_anim_class"] = path_name(
                asset.get_editor_property("animation_source_anim_instance_class")
            )
            item["route_animation"] = path_name(
                asset.get_editor_property("auto_route_animation")
            )
    item["success"] = (
        item["asset_loaded"]
        and item["asset_class"] == expected_class
        and item.get("mesh", "").split(".", 1)[0] == expected_meshes[asset_name]
        and bool(item.get("anim_class"))
    )
    if type_name == "TwinCharacter" and asset:
        if asset_name == "ObserverBase":
            item["success"] = (
                item["success"]
                and item["animation_source_mesh"].split(".", 1)[0] == QUINN_MESH_PATH
                and item["animation_source_anim_class"].split(".", 1)[0]
                == QUINN_ANIM_PATH
                and item["route_animation"].split(".", 1)[0] == QUINN_WALK_PATH
            )
        else:
            item["success"] = (
                item["success"]
                and not item["animation_source_mesh"]
                and not item["animation_source_anim_class"]
                and item["route_animation"].split(".", 1)[0] == MANNY_WALK_PATH
            )
    if type_name == "TwinSkin" and asset:
        overrides = asset.get_editor_property("material_overrides")
        item["skeleton_id"] = str(asset.get_editor_property("skeleton_id"))
        item["material_override_count"] = len(overrides)
        if asset_name in expected_uniform_materials:
            material_paths = [path_name(value) for value in overrides if value]
            item["uniform_materials"] = material_paths
            item["success"] = (
                item["success"]
                and len(overrides) == 16
                and material_paths == [expected_uniform_materials[asset_name]] * 2
            )
        else:
            item["success"] = item["success"] and len(overrides) == 0
    results.append(item)

skeleton_checks = (
    verify_skeleton_pair(GROUND_MESH_PATH, GROUND_ANIM_PATH),
    verify_skeleton_pair(MANNY_MESH_PATH, MANNY_ANIM_PATH),
    verify_skeleton_pair(QUINN_MESH_PATH, QUINN_ANIM_PATH),
    verify_route_skeleton(QUINN_MESH_PATH, QUINN_WALK_PATH),
    verify_route_skeleton(MANNY_MESH_PATH, MANNY_WALK_PATH),
)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "AssetManager.DumpTypeSummary")
result = {
    "success": all(item["success"] for item in results)
    and all(item["success"] for item in skeleton_checks),
    "assets": results,
    "skeletons": skeleton_checks,
    "asset_manager_summary_requested": True,
}
unreal.log("ONTOTWIN_CORE_VERIFY_BEGIN")
unreal.log(json.dumps(result, ensure_ascii=False, sort_keys=True))
unreal.log("ONTOTWIN_CORE_VERIFY_END")
if not result["success"]:
    raise RuntimeError("OntoTwinCharacterPack_Core verification failed")
unreal.SystemLibrary.quit_editor()
