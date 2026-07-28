"""Install the six rigged Renderpeople characters as OntoTwin adapters.

Run only while the interactive UE editor is closed. The script is idempotent:
existing OntoTwin adapter assets are updated, while Fab source assets are never
modified.
"""

import json
import unreal


CHARACTER_DIR = "/Game/OntoTwin/SceneInteraction/Characters/RenderPeople"
SKIN_DIR = "/Game/OntoTwin/SceneInteraction/Skins/RenderPeople"
PACK_CHARACTER_DIR = "/Game/Scanned3DPeoplePack/RP_Character"
EXPECTED_SKELETON = (
    f"{PACK_CHARACTER_DIR}/00_rp_master/Mannequin/"
    "UE4_Mannequin_Skeleton.UE4_Mannequin_Skeleton"
)
OBSERVER_CHARACTER = "/Game/OntoTwin/SceneInteraction/Characters/ObserverBase"
OBSERVER_SKIN = "/Game/OntoTwin/SceneInteraction/Skins/ObserverGray"
CHARACTERS = (
    ("Carla", "rp_carla_rigged_001_ue4"),
    ("Claudia", "rp_claudia_rigged_002_ue4"),
    ("Eric", "rp_eric_rigged_001_ue4"),
    ("Manuel", "rp_manuel_rigged_001_ue4"),
    ("Nathan", "rp_nathan_rigged_003_ue4"),
    ("Sophia", "rp_sophia_rigged_003_ue4"),
)


def create_or_load(asset_name, package_path, data_asset_class):
    asset_path = f"{package_path}/{asset_name}"
    existing = unreal.EditorAssetLibrary.load_asset(asset_path)
    if existing:
        if existing.get_class() != data_asset_class:
            raise RuntimeError(
                f"{asset_path} exists with class {existing.get_class()}, "
                f"expected {data_asset_class}"
            )
        return existing, False

    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", data_asset_class)
    created = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name, package_path, data_asset_class, factory
    )
    if not created:
        raise RuntimeError(f"Could not create {asset_path}")
    return created, True


observer_character = unreal.load_asset(OBSERVER_CHARACTER)
observer_skin = unreal.load_asset(OBSERVER_SKIN)
if not observer_character or not observer_skin:
    raise RuntimeError("Observer adapter assets could not be loaded")

character_template_properties = (
    "character_class",
    "anim_instance_class",
    "animation_source_mesh",
    "animation_source_anim_instance_class",
    "auto_route_animation",
    "auto_route_animation_reference_speed_cm_s",
    "capsule_radius_cm",
    "capsule_half_height_cm",
    "mesh_offset_cm",
    "mesh_yaw_offset_deg",
)
results = []

for display_name, source_asset_name in CHARACTERS:
    source_mesh_path = (
        f"{PACK_CHARACTER_DIR}/{source_asset_name}/{source_asset_name}"
    )
    source_mesh = unreal.load_asset(source_mesh_path)
    if not source_mesh:
        raise RuntimeError(f"Source mesh could not be loaded: {source_mesh_path}")

    actual_skeleton = source_mesh.get_editor_property("skeleton")
    actual_skeleton_path = actual_skeleton.get_path_name() if actual_skeleton else ""
    if actual_skeleton_path != EXPECTED_SKELETON:
        raise RuntimeError(
            f"{display_name} Skeleton mismatch: {actual_skeleton_path!r}; "
            f"expected {EXPECTED_SKELETON!r}"
        )

    character_name = f"RenderPeople{display_name}"
    skin_name = f"{character_name}Default"
    character, character_created = create_or_load(
        character_name, CHARACTER_DIR, observer_character.get_class()
    )
    skin, skin_created = create_or_load(
        skin_name, SKIN_DIR, observer_skin.get_class()
    )

    for property_name in character_template_properties:
        character.set_editor_property(
            property_name, observer_character.get_editor_property(property_name)
        )
    character.set_editor_property("base_mesh", source_mesh)

    skin.set_editor_property("skeleton_id", "skeleton.renderpeople.ue4.v1")
    skin.set_editor_property("mesh", source_mesh)
    skin.set_editor_property(
        "anim_instance_class", observer_skin.get_editor_property("anim_instance_class")
    )
    skin.set_editor_property("material_overrides", [])

    if not unreal.EditorAssetLibrary.save_loaded_asset(
        character, only_if_is_dirty=False
    ):
        raise RuntimeError(f"Could not save {character_name}")
    if not unreal.EditorAssetLibrary.save_loaded_asset(skin, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save {skin_name}")

    results.append(
        {
            "display_name": display_name,
            "character": character.get_path_name(),
            "character_created": character_created,
            "character_primary_asset_id": f"TwinCharacter:{character_name}",
            "skin": skin.get_path_name(),
            "skin_created": skin_created,
            "skin_primary_asset_id": f"TwinSkin:{skin_name}",
            "source_mesh": source_mesh.get_path_name(),
            "source_skeleton": actual_skeleton_path,
        }
    )

unreal.log("CODEX_INSTALL_RENDERPEOPLE_BEGIN")
unreal.log(
    json.dumps(
        {"success": True, "character_count": len(results), "characters": results},
        ensure_ascii=False,
        sort_keys=True,
    )
)
unreal.log("CODEX_INSTALL_RENDERPEOPLE_END")
unreal.SystemLibrary.quit_editor()
