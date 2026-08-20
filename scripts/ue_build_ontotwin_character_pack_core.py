"""Build or refresh OntoTwin Core character data assets in an enabled plugin."""

import json

import unreal


PACK_ROOT = "/OntoTwinCharacterPack_Core"
CHARACTER_DIR = f"{PACK_ROOT}/Characters"
SKIN_DIR = f"{PACK_ROOT}/Skins"

GROUND_ROOT = "/Game/Art/A08_Characters/00_Ground_Staff/ThirdPerson"
GROUND_MESH_PATH = f"{GROUND_ROOT}/SkeletonIK/SK_Charactor"
GROUND_ANIM_BP_PATH = f"{GROUND_ROOT}/SkeletonIK/myAnimBlueprint"
GROUND_GRAY_PATH = f"{GROUND_ROOT}/CharacterMaterial/gray"
GROUND_GREEN_PATH = f"{GROUND_ROOT}/CharacterMaterial/green"

MANNY_ROOT = "/Game/Characters/Mannequins"
MANNY_MESH_PATH = f"{MANNY_ROOT}/Meshes/SKM_Manny_Simple"
MANNY_ANIM_BP_PATH = f"{MANNY_ROOT}/Anims/Unarmed/ABP_Unarmed"


def fail(message):
    unreal.log_error(f"ONTOTWIN_CORE_BUILD_ERROR: {message}")
    raise RuntimeError(message)


def create_or_load_data_asset(asset_name, package_path, data_asset_class):
    asset_path = f"{package_path}/{asset_name}"
    existing = unreal.EditorAssetLibrary.load_asset(asset_path)
    if existing:
        if existing.get_class() != data_asset_class:
            fail(
                f"{asset_path} has class {existing.get_class().get_name()}, "
                f"expected {data_asset_class.get_name()}"
            )
        return existing, False
    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", data_asset_class)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name, package_path, data_asset_class, factory
    )
    if not asset:
        fail(f"Could not create {asset_path}")
    return asset, True


def load_required_asset(path, label):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        fail(f"{label} could not be loaded: {path}")
    return asset


def load_required_anim_class(path, label):
    value = unreal.EditorAssetLibrary.load_blueprint_class(path)
    if not value:
        fail(f"{label} class could not be loaded: {path}")
    return value


def configure_character(
    asset,
    mesh,
    anim_class,
    animation_source_mesh=None,
    animation_source_anim_class=None,
):
    asset.set_editor_property("base_mesh", mesh)
    asset.set_editor_property("anim_instance_class", anim_class)
    asset.set_editor_property("animation_source_mesh", animation_source_mesh)
    asset.set_editor_property(
        "animation_source_anim_instance_class", animation_source_anim_class
    )
    asset.set_editor_property("auto_route_animation", None)
    asset.set_editor_property("capsule_radius_cm", 34.0)
    asset.set_editor_property("capsule_half_height_cm", 88.0)
    asset.set_editor_property("mesh_offset_cm", unreal.Vector(0.0, 0.0, -88.0))
    asset.set_editor_property("mesh_yaw_offset_deg", -90.0)


ground_mesh = load_required_asset(GROUND_MESH_PATH, "Ground Staff mesh")
ground_anim_class = load_required_anim_class(GROUND_ANIM_BP_PATH, "Ground Staff animation")
ground_gray = load_required_asset(GROUND_GRAY_PATH, "Ground Staff gray material")
ground_green = load_required_asset(GROUND_GREEN_PATH, "Ground Staff green material")
manny_mesh = load_required_asset(MANNY_MESH_PATH, "Manny mesh")
manny_anim_class = load_required_anim_class(MANNY_ANIM_BP_PATH, "Manny animation")

ground_slots = ground_mesh.get_editor_property("materials")
uniform_indices = []
for index, slot in enumerate(ground_slots):
    material = slot.get_editor_property("material_interface")
    material_path = material.get_path_name() if material else ""
    if material_path in (
        f"{GROUND_GRAY_PATH}.gray",
        f"{GROUND_GREEN_PATH}.green",
    ):
        uniform_indices.append(index)
if len(uniform_indices) != 2:
    fail(f"Expected two Ground Staff uniform slots, found {uniform_indices}")

character_class = unreal.load_class(None, "/Script/OntoTwinSync.TwinCharacterAsset")
skin_class = unreal.load_class(None, "/Script/OntoTwinSync.TwinSkinAsset")
if not character_class or not skin_class:
    fail("OntoTwinSync data asset classes could not be loaded")

characters = []
for asset_name, mesh, anim_class, source_mesh, source_anim_class in (
    # myAnimBlueprint is a Retarget Pose From Mesh graph. It needs a hidden
    # animated Manny parent; without this source the Ground Staff mesh stays in
    # its reference pose while the character capsule moves (visible "sliding").
    ("ObserverBase", ground_mesh, ground_anim_class, manny_mesh, manny_anim_class),
    ("MannyRobot", manny_mesh, manny_anim_class, None, None),
):
    asset, created = create_or_load_data_asset(asset_name, CHARACTER_DIR, character_class)
    configure_character(asset, mesh, anim_class, source_mesh, source_anim_class)
    if not unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False):
        fail(f"Could not save {asset_name}")
    characters.append(
        {
            "name": asset_name,
            "created": created,
            "path": asset.get_path_name(),
            "primary_asset_id": f"TwinCharacter:{asset_name}",
            "mesh": mesh.get_path_name(),
            "anim_class": anim_class.get_path_name(),
            "animation_source_mesh": source_mesh.get_path_name() if source_mesh else "",
            "animation_source_anim_class": (
                source_anim_class.get_path_name() if source_anim_class else ""
            ),
        }
    )

skins = []
for skin_name, skeleton_id, mesh, anim_class, uniform_material in (
    ("ObserverGray", "skeleton.observer.v1", ground_mesh, ground_anim_class, ground_gray),
    ("ObserverGreen", "skeleton.observer.v1", ground_mesh, ground_anim_class, ground_green),
    ("MannyRobotDefault", "skeleton.manny.ue5.v1", manny_mesh, manny_anim_class, None),
):
    overrides = []
    if uniform_material:
        overrides = [None] * len(ground_slots)
        for index in uniform_indices:
            overrides[index] = uniform_material
    skin, created = create_or_load_data_asset(skin_name, SKIN_DIR, skin_class)
    skin.set_editor_property("skeleton_id", skeleton_id)
    skin.set_editor_property("mesh", mesh)
    skin.set_editor_property("anim_instance_class", anim_class)
    skin.set_editor_property("material_overrides", overrides)
    if not unreal.EditorAssetLibrary.save_loaded_asset(skin, only_if_is_dirty=False):
        fail(f"Could not save {skin_name}")
    skins.append(
        {
            "name": skin_name,
            "created": created,
            "path": skin.get_path_name(),
            "primary_asset_id": f"TwinSkin:{skin_name}",
            "material_override_count": len(overrides),
            "uniform_indices": uniform_indices if uniform_material else [],
        }
    )

unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
result = {
    "success": True,
    "characters": characters,
    "skins": skins,
    "ground_uniform_indices": uniform_indices,
}
unreal.log("ONTOTWIN_CORE_BUILD_BEGIN")
unreal.log(json.dumps(result, ensure_ascii=False, sort_keys=True))
unreal.log("ONTOTWIN_CORE_BUILD_END")
unreal.SystemLibrary.quit_editor()
