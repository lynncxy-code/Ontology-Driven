"""NEW-07: generate the grey and wireframe status materials in an isolated UE host only."""
import unreal

root = '/OntoTwinIndustrialBehavior/Materials'
lib = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def fresh(name):
    material = unreal.load_asset(root + '/' + name)
    if not material:
        material = tools.create_asset(name, root, unreal.Material, unreal.MaterialFactoryNew())
    lib.delete_all_material_expressions(material)
    material.set_editor_property('blend_mode', unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property('two_sided', True)
    return material


def color(material, rgb, x=-400, y=0):
    node = lib.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, x, y)
    node.set_editor_property('constant', unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    return node


def save(material, name):
    lib.recompile_material(material)
    if not unreal.EditorAssetLibrary.save_loaded_asset(material):
        raise RuntimeError(name + ' save failed')
    unreal.log('OT_STATUS_ASSET_SAVED ' + root + '/' + name)


# Solid neutral grey: the original colours are no longer visible.
gray = fresh('M_StatusGray')
gray.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
assert lib.connect_material_property(color(gray, (0.32, 0.32, 0.32)), '', unreal.MaterialProperty.MP_BASE_COLOR)
rough = lib.create_material_expression(gray, unreal.MaterialExpressionConstant, -400, 150)
rough.set_editor_property('r', 0.85)
assert lib.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
save(gray, 'M_StatusGray')

# Edges only, everything between them is see-through.
wire = fresh('M_StatusWireframe')
wire.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
wire.set_editor_property('wireframe', True)
assert lib.connect_material_property(color(wire, (0.55, 0.8, 1.0)), '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
save(wire, 'M_StatusWireframe')
