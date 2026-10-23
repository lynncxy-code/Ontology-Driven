"""Generate the five OntoTwin Slate-postbuffer UI material variants.

Run this script through UnrealEditor-Cmd with PythonScriptPlugin enabled while
the interactive editor is closed. The operation is intentionally conservative:
an existing material is verified and skipped, never rewritten.
"""

import json
import math

import unreal


MARKER_PREFIX = "ONTOTWIN_GLASS_MATERIALS"
MATERIAL_DIR = "/OntoTwinSync/UI/RendererSpike"
SLOT_COUNT = 5


class GlassMaterialGenerationError(RuntimeError):
    """Failure already reported through the machine-readable ERROR marker."""


def emit(marker, payload, error=False):
    message = "{}_{} {}".format(
        MARKER_PREFIX,
        marker,
        json.dumps(payload, ensure_ascii=True, sort_keys=True),
    )
    if error:
        unreal.log_error(message)
    else:
        unreal.log(message)


def fail(message, **details):
    payload = {"message": message}
    payload.update(details)
    emit("ERROR", payload, error=True)
    raise GlassMaterialGenerationError(message)


def object_path(value):
    return value.get_path_name() if value else ""


def class_name(value):
    value_class = value.get_class() if value else None
    return value_class.get_name() if value_class else ""


def expected_paths(slot):
    material_name = "M_OT_GlassHigh_RT{}".format(slot)
    return {
        "slot": slot,
        "material_name": material_name,
        "material": "{}/{}".format(MATERIAL_DIR, material_name),
        "function": (
            "/Engine/Functions/UserInterface/GetSlatePost{0}."
            "GetSlatePost{0}".format(slot)
        ),
        "texture": (
            "/Engine/EngineResources/SlatePost{0}_RT."
            "SlatePost{0}_RT".format(slot)
        ),
    }


def load_required_asset(path, kind, slot):
    asset = unreal.load_asset(path)
    if not asset:
        fail(
            "Required {} could not be loaded".format(kind),
            slot=slot,
            asset_path=path,
        )
    return asset


def get_property_input(material, material_property):
    return unreal.MaterialEditingLibrary.get_material_property_input_node(
        material, material_property
    )


def get_property_output_name(material, material_property):
    return unreal.MaterialEditingLibrary.get_material_property_input_node_output_name(
        material, material_property
    )


def validate_material(material, paths):
    """Return a machine-readable summary or fail on any structural mismatch."""
    slot = paths["slot"]
    material_path = paths["material"]
    problems = []

    if class_name(material) != "Material":
        problems.append(
            "asset class is {!r}, expected 'Material'".format(class_name(material))
        )
    else:
        domain = material.get_editor_property("material_domain")
        blend_mode = material.get_editor_property("blend_mode")
        if domain != unreal.MaterialDomain.MD_UI:
            problems.append(
                "material_domain is {!r}, expected MD_UI".format(str(domain))
            )
        if blend_mode != unreal.BlendMode.BLEND_TRANSLUCENT:
            problems.append(
                "blend_mode is {!r}, expected BLEND_TRANSLUCENT".format(
                    str(blend_mode)
                )
            )

        expression_count = (
            unreal.MaterialEditingLibrary.get_num_material_expressions(material)
        )
        if expression_count != 2:
            problems.append(
                "expression count is {}, expected exactly 2".format(expression_count)
            )

        color_node = get_property_input(
            material, unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
        if class_name(color_node) != "MaterialExpressionMaterialFunctionCall":
            problems.append(
                "UI final color input is {!r}, expected function call".format(
                    class_name(color_node)
                )
            )
        else:
            called_function = color_node.get_editor_property("material_function")
            if object_path(called_function) != paths["function"]:
                problems.append(
                    "function is {!r}, expected {!r}".format(
                        object_path(called_function), paths["function"]
                    )
                )
            output_name = get_property_output_name(
                material, unreal.MaterialProperty.MP_EMISSIVE_COLOR
            )
            if output_name != "RGB":
                problems.append(
                    "UI final color output is {!r}, expected 'RGB'".format(
                        output_name
                    )
                )

        opacity_node = get_property_input(material, unreal.MaterialProperty.MP_OPACITY)
        if class_name(opacity_node) != "MaterialExpressionConstant":
            problems.append(
                "opacity input is {!r}, expected constant".format(
                    class_name(opacity_node)
                )
            )
        else:
            opacity = float(opacity_node.get_editor_property("r"))
            if not math.isclose(opacity, 1.0, rel_tol=0.0, abs_tol=1.0e-6):
                problems.append(
                    "opacity constant is {}, expected 1.0".format(opacity)
                )

        used_textures = sorted(
            object_path(texture)
            for texture in unreal.MaterialEditingLibrary.get_used_textures(material)
            if texture
        )
        used_postbuffers = [
            path
            for path in used_textures
            if path.startswith("/Engine/EngineResources/SlatePost")
        ]
        # In UE 5.6, get_used_textures() can return no function-internal
        # dependencies under -nullrhi. The exact GetSlatePostN function and
        # RGB connection remain the authoritative graph check in that mode.
        # If the wrapper does expose Slate RT dependencies, keep the stricter
        # matching/no-cross-slot validation.
        if used_postbuffers:
            if paths["texture"] not in used_postbuffers:
                problems.append(
                    "matching Slate postbuffer texture is not in reported dependencies"
                )
            unexpected_postbuffers = [
                path for path in used_postbuffers if path != paths["texture"]
            ]
            if unexpected_postbuffers:
                problems.append(
                    "unexpected Slate postbuffer dependencies: {!r}".format(
                        unexpected_postbuffers
                    )
                )

    if problems:
        fail(
            "Existing or generated asset is structurally incompatible",
            slot=slot,
            material=material_path,
            problems=problems,
        )

    return {
        "slot": slot,
        "material": object_path(material),
        "function": paths["function"],
        "texture": paths["texture"],
        "domain": "MD_UI",
        "blend_mode": "BLEND_TRANSLUCENT",
        "expression_count": 2,
        "color_output": "RGB",
        "opacity": 1.0,
        "texture_dependency_check": (
            "verified" if used_postbuffers else "deferred_by_nullrhi"
        ),
    }


def save_loaded_asset(asset):
    """Keep compatibility with the UE 5.6 signature and older exposed wrappers."""
    try:
        saved = unreal.EditorAssetLibrary.save_loaded_asset(
            asset, only_if_is_dirty=False
        )
    except TypeError:
        saved = unreal.EditorAssetLibrary.save_loaded_asset(asset)
    if saved is False:
        fail("Could not save generated material", material=object_path(asset))


def create_material(paths, material_function):
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialFactoryNew()
    material = asset_tools.create_asset(
        paths["material_name"],
        MATERIAL_DIR,
        unreal.Material,
        factory,
    )
    if not material:
        fail(
            "Could not create material",
            slot=paths["slot"],
            material=paths["material"],
        )

    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_UI)
    material.set_editor_property(
        "blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT
    )

    function_call = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionMaterialFunctionCall,
        -420,
        -80,
    )
    if not function_call:
        fail(
            "Could not create material-function expression",
            slot=paths["slot"],
            material=paths["material"],
        )

    set_function = getattr(function_call, "set_material_function", None)
    if callable(set_function):
        function_set = set_function(material_function)
        if function_set is False:
            fail(
                "UE rejected the Slate postbuffer material function",
                slot=paths["slot"],
                function=paths["function"],
            )
    else:
        # Defensive fallback for wrappers where the UE 5.6 BlueprintCallable
        # method is not exported but its editable property remains available.
        function_call.set_editor_property("material_function", material_function)

    opacity = unreal.MaterialEditingLibrary.create_material_expression(
        material,
        unreal.MaterialExpressionConstant,
        -420,
        160,
    )
    if not opacity:
        fail(
            "Could not create opacity expression",
            slot=paths["slot"],
            material=paths["material"],
        )
    opacity.set_editor_property("r", 1.0)

    color_connected = unreal.MaterialEditingLibrary.connect_material_property(
        function_call,
        "RGB",
        unreal.MaterialProperty.MP_EMISSIVE_COLOR,
    )
    opacity_connected = unreal.MaterialEditingLibrary.connect_material_property(
        opacity,
        "",
        unreal.MaterialProperty.MP_OPACITY,
    )
    if not color_connected or not opacity_connected:
        fail(
            "Could not connect generated material graph",
            slot=paths["slot"],
            color_connected=bool(color_connected),
            opacity_connected=bool(opacity_connected),
        )

    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    save_loaded_asset(material)

    reloaded = unreal.EditorAssetLibrary.load_asset(paths["material"])
    if not reloaded:
        fail(
            "Generated material could not be reloaded",
            slot=paths["slot"],
            material=paths["material"],
        )
    return reloaded


def main():
    paths_by_slot = [expected_paths(slot) for slot in range(SLOT_COUNT)]
    emit(
        "BEGIN",
        {
            "material_dir": MATERIAL_DIR,
            "slot_count": SLOT_COUNT,
            "overwrite_existing": False,
        },
    )

    functions = {}
    for paths in paths_by_slot:
        functions[paths["slot"]] = load_required_asset(
            paths["function"], "material function", paths["slot"]
        )
        load_required_asset(paths["texture"], "postbuffer texture", paths["slot"])

    existing = {}
    missing = []
    for paths in paths_by_slot:
        if unreal.EditorAssetLibrary.does_asset_exist(paths["material"]):
            material = unreal.EditorAssetLibrary.load_asset(paths["material"])
            if material:
                existing[paths["slot"]] = validate_material(material, paths)
                continue
            fail(
                "Existing asset could not be loaded",
                slot=paths["slot"],
                material=paths["material"],
            )
        missing.append(paths)

    if missing and not unreal.EditorAssetLibrary.does_directory_exist(MATERIAL_DIR):
        if not unreal.EditorAssetLibrary.make_directory(MATERIAL_DIR):
            fail("Could not create material directory", directory=MATERIAL_DIR)

    results = []
    for paths in paths_by_slot:
        slot = paths["slot"]
        if slot in existing:
            summary = dict(existing[slot])
            summary["action"] = "verified"
        else:
            material = create_material(paths, functions[slot])
            summary = validate_material(material, paths)
            summary["action"] = "created"
        results.append(summary)
        emit("ASSET", summary)

    emit(
        "END",
        {
            "success": True,
            "asset_count": len(results),
            "created_count": sum(
                1 for result in results if result["action"] == "created"
            ),
            "verified_count": sum(
                1 for result in results if result["action"] == "verified"
            ),
            "materials": [result["material"] for result in results],
        },
    )
    unreal.SystemLibrary.quit_editor()


try:
    main()
except Exception as exc:
    # fail() already emits detailed errors. This catch covers unexpected Python
    # or Unreal wrapper failures while preserving a single searchable marker.
    if not isinstance(exc, GlassMaterialGenerationError):
        emit(
            "ERROR",
            {
                "message": "Unexpected script failure",
                "exception_type": type(exc).__name__,
                "exception": str(exc),
            },
            error=True,
        )
    raise
