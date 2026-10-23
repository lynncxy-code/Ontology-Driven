"""Inspect the Ground Staff assets required by OntoTwin Core."""

import json

import unreal


ROOT = "/Game/Art/A08_Characters/00_Ground_Staff/ThirdPerson"
MESH_PATH = f"{ROOT}/SkeletonIK/SK_Charactor"
ANIM_PATH = f"{ROOT}/SkeletonIK/myAnimBlueprint"
MATERIAL_PATHS = (
    f"{ROOT}/CharacterMaterial/gray",
    f"{ROOT}/CharacterMaterial/green",
)


def path_name(value):
    return value.get_path_name() if value else ""


mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
anim = unreal.EditorAssetLibrary.load_asset(ANIM_PATH)
anim_class = unreal.EditorAssetLibrary.load_blueprint_class(ANIM_PATH)
materials = [unreal.EditorAssetLibrary.load_asset(path) for path in MATERIAL_PATHS]
if not mesh or not anim or not anim_class or not all(materials):
    raise RuntimeError("Ground Staff root assets are incomplete")

slots = []
for index, slot in enumerate(mesh.get_editor_property("materials")):
    slots.append(
        {
            "index": index,
            "slot_name": str(slot.get_editor_property("material_slot_name")),
            "material": path_name(slot.get_editor_property("material_interface")),
        }
    )

result = {
    "success": True,
    "mesh": path_name(mesh),
    "mesh_skeleton": path_name(mesh.get_editor_property("skeleton")),
    "anim_blueprint": path_name(anim),
    "anim_class": path_name(anim_class),
    "anim_skeleton": path_name(anim.get_editor_property("target_skeleton")),
    "materials": [path_name(value) for value in materials],
    "slots": slots,
}
result["success"] = (
    bool(result["mesh_skeleton"])
    and result["mesh_skeleton"] == result["anim_skeleton"]
)

unreal.log("ONTOTWIN_GROUND_STAFF_INSPECT_BEGIN")
unreal.log(json.dumps(result, ensure_ascii=False, sort_keys=True))
unreal.log("ONTOTWIN_GROUND_STAFF_INSPECT_END")
if not result["success"]:
    raise RuntimeError("Ground Staff mesh and animation skeletons do not match")
unreal.SystemLibrary.quit_editor()
