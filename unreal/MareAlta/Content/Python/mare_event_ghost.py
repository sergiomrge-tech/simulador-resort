"""Ghost material for the plan of a Grand Hotel event (CHECKLIST 5.2, MareHotelEventsWorld.cpp).

A piece not set yet shows as a light-blue see-through outline on the beach: lit translucent (an unlit emissive one read
black under the daylight exposure), more opaque at the silhouette (fresnel) so it reads at a distance without hiding the sand. Run with PIE stopped: mare_event_ghost.run('')."""
import unreal

PATH = '/Game/Custom/HotelEvents'
NAME = 'M_EventGhost'


def run(arg=''):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    lib = unreal.MaterialEditingLibrary
    full = f'{PATH}/{NAME}'
    if unreal.EditorAssetLibrary.does_asset_exist(full):
        mat = unreal.EditorAssetLibrary.load_asset(full)
        for e in list(lib.get_material_expressions(mat) if hasattr(lib, 'get_material_expressions') else []):
            lib.delete_material_expression(mat, e)
    else:
        mat = tools.create_asset(NAME, PATH, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mat.set_editor_property('two_sided', True)
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    color = lib.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -600, 0)
    color.set_editor_property('constant', unreal.LinearColor(0.35, 0.85, 1.0, 1))
    glow = lib.create_material_expression(mat, unreal.MaterialExpressionMultiply, -350, 0)
    glow.set_editor_property('const_b', 0.35)
    lib.connect_material_expressions(color, '', glow, 'A')
    lib.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    fres = lib.create_material_expression(mat, unreal.MaterialExpressionFresnel, -600, 250)
    fres.set_editor_property('exponent', 2.5)
    lerp = lib.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -350, 250)
    lerp.set_editor_property('const_a', 0.35)
    lerp.set_editor_property('const_b', 0.85)
    lib.connect_material_expressions(fres, '', lerp, 'Alpha')
    lib.connect_material_property(lerp, '', unreal.MaterialProperty.MP_OPACITY)
    lib.recompile_material(mat)
    ok = unreal.EditorAssetLibrary.save_asset(full, only_if_is_dirty=False)
    return f'{full} saved={ok}'
