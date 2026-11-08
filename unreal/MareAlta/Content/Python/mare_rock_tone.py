"""07/11 (Sergio's beach photos: red-brown blocks that read as bricks of meat on the white sand): the Poly Haven rock_07
used by the beach rocks and pebbles is a red sandstone. Desaturate it and pull it toward a weathered grey-beige beach
rock: base colour -> Desaturation -> x tint. Idempotent (a node tagged by its description is reused). Editor, PIE stopped.
mare_hud module "mare_rock_tone.run|/Game/Custom/Beach/rock_07/rock_07"."""
import json
import unreal

MEL = unreal.MaterialEditingLibrary
TAG = 'mare_rock_tone'


def run(arg='/Game/Custom/Beach/rock_07/rock_07'):
    mat = unreal.load_asset(arg)
    src = MEL.get_material_property_input_node(mat, unreal.MaterialProperty.MP_BASE_COLOR)
    if src is None:
        return 'no base colour input'
    if src.get_editor_property('desc') == TAG:
        return 'already toned'
    out_name = MEL.get_material_property_input_node_output_name(mat, unreal.MaterialProperty.MP_BASE_COLOR) \
        if hasattr(MEL, 'get_material_property_input_node_output_name') else ''
    pos = (src.get_editor_property('material_expression_editor_x'), src.get_editor_property('material_expression_editor_y'))
    des = MEL.create_material_expression(mat, unreal.MaterialExpressionDesaturation, pos[0] + 250, pos[1])
    des.set_editor_property('desc', TAG + '_d')
    frac = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, pos[0] + 100, pos[1] + 120)
    frac.set_editor_property('r', 0.72)
    MEL.connect_material_expressions(src, out_name or '', des, '')
    MEL.connect_material_expressions(frac, '', des, 'Fraction')
    tint = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, pos[0] + 250, pos[1] + 160)
    tint.set_editor_property('constant', unreal.LinearColor(1.18, 1.12, 1.0, 1))
    mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, pos[0] + 450, pos[1])
    mul.set_editor_property('desc', TAG)
    MEL.connect_material_expressions(des, '', mul, 'A')
    MEL.connect_material_expressions(tint, '', mul, 'B')
    MEL.connect_material_property(mul, '', unreal.MaterialProperty.MP_BASE_COLOR)
    errors = list(MEL.recompile_material(mat))
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    return json.dumps({'src': src.get_class().get_name(), 'out': out_name, 'errors': [str(e) for e in errors]})


def mic_vector(arg=''):
    """'path|Param|r,g,b' : set a vector parameter on a material instance constant and save (PIE stopped).
    07/11: the kiosk's inner counter boards (World_1213) are dark-stained; BaseColorFactor lifts them a little."""
    path, param, rgb = arg.split('|')
    r, g, b = (float(v) for v in rgb.split(','))
    mic = unreal.load_asset(path)
    old = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(mic, param)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mic, param, unreal.LinearColor(r, g, b, 1))
    unreal.EditorAssetLibrary.save_loaded_asset(mic, False)
    return json.dumps({'old': [old.r, old.g, old.b], 'new': [r, g, b]})
