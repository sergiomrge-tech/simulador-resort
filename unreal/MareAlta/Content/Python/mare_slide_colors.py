"""Colourful water slide (07/11, Sergio: "tobogã precisa ser assim"): tools/gen_hotel.py gives the chute four coloured
sections (slots 4..7 of mare_water_slide); an in-place reimport keeps the old materials and leaves the new slots on the
grid material. Duplicate the chute material per colour, set its base colour and assign the slots. Editor, PIE stopped.
Run: mare_hud module "mare_slide_colors.run|" (or "mare_slide_colors.probe|")."""
import json
import unreal

FOLDER = '/Game/Custom/mare_water_slide'
MESH = FOLDER + '/mare_water_slide'
BASE = FOLDER + '/mare_water_slide_tint_calha'
COLORS = [('rosa', (0.95, 0.35, 0.6)), ('verde', (0.45, 0.85, 0.35)), ('amarela', (0.98, 0.82, 0.2)), ('lilas', (0.65, 0.5, 0.95))]
MEL = unreal.MaterialEditingLibrary


def probe(_=''):
    base = unreal.load_asset(BASE)
    out = {'class': base.get_class().get_name()}
    if isinstance(base, unreal.Material):
        out['nodes'] = [(e.get_class().get_name(), e.get_name()) for e in MEL.get_material_expressions(base)] \
            if hasattr(MEL, 'get_material_expressions') else 'n/a'
    mesh = unreal.load_asset(MESH)
    out['slots'] = [str(s.material_slot_name) for s in mesh.static_materials]
    return json.dumps(out, default=str)


def _set_color(mat, rgb):
    """Base colour = a constant 3-vector (the glTF factor), replacing whatever fed it."""
    for e in list(MEL.get_material_expressions(mat)) if hasattr(MEL, 'get_material_expressions') else []:
        if isinstance(e, (unreal.MaterialExpressionConstant3Vector, unreal.MaterialExpressionVectorParameter)):
            prop = 'constant' if isinstance(e, unreal.MaterialExpressionConstant3Vector) else 'default_value'
            e.set_editor_property(prop, unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1))
            return 'edited'
    c = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 0)
    c.set_editor_property('constant', unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1))
    MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_BASE_COLOR)
    return 'new'


def run(_=''):
    mesh = unreal.load_asset(MESH)
    mats = list(mesh.static_materials)
    done = {}
    for i, (name, rgb) in enumerate(COLORS):
        path = f'{FOLDER}/mare_water_slide_calha_{name}'
        mat = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else \
            unreal.EditorAssetLibrary.duplicate_asset(BASE, path)
        how = _set_color(mat, rgb)
        if isinstance(mat, unreal.Material):
            MEL.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
        slot = 4 + i
        if slot < len(mats):
            mesh.set_material(slot, mat)
        done[name] = how
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return json.dumps(done)
