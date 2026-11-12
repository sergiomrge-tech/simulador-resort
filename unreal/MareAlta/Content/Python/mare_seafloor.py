"""Reef seafloor life (05/11): imports tools/ue58/gen_seafloor.py models (SourceArt/Models/Seafloor) to
/Game/Custom/Seafloor/<name> (fresh folder each, unique Sea_* names, LOCAL search), gives every material the instanced
static mesh usage (they are drawn as HISM by MareReefWorld, Content/Data/reef.json) and adds the GPU sway: kelp and
seagrass bend with the current, anemone tentacles stir, the shark's tail beats (World Position Offset from the
pre-skinned local position, turned to world by a Local->World transform so instance rotations are respected).
PIE must be stopped."""
import json

import unreal

MEL = unreal.MaterialEditingLibrary

# Local-space offset (cm) from LP (local position), T (time), W (world position, for a per-instance phase).
SWAY = {
    'kelp': 'float ph=dot(W.xy,float2(.0041,.0033)); float h=saturate(LP.z/240); float b=pow(h,1.5);'
            ' return float3(sin(T*.8+ph)*16*b+sin(T*2.1+LP.z*.04+ph)*2.5*h, cos(T*.63+ph)*10*b, -3*b*b);',
    'grass': 'float ph=dot(W.xy,float2(.009,.006)); float h=saturate(LP.z/50); return float3(sin(T*1.1+ph)*4*h*h, cos(T*.9+ph)*2.5*h*h, 0);',
    'anemone': 'float ph=dot(W.xy,float2(.02,.017)); float h=saturate((LP.z-11)/12); return float3(sin(T*1.4+ph+LP.x*.08)*1.6*h, cos(T*1.2+ph+LP.y*.08)*1.6*h, 0);',
    # Snout at local y=-160, tail fin out to y=+40: the beat grows toward the tail and travels down the body.
    'shark': 'float k=saturate((LP.y+110)/150); return float3(sin(T*6.5-LP.y*.028)*11*k*k, 0, 0);',
}
KIND = {'Sea_kelp_a': 'kelp', 'Sea_kelp_b': 'kelp', 'Sea_seagrass': 'grass', 'Sea_anemone': 'anemone', 'Sea_shark': 'shark'}


def _game_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()


def _sway(mat, code):
    lp = MEL.create_material_expression(mat, unreal.MaterialExpressionPreSkinnedPosition, -900, 600)
    t = MEL.create_material_expression(mat, unreal.MaterialExpressionTime, -900, 700)
    w = MEL.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -900, 800)
    c = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -600, 700)
    c.set_editor_property('code', code)
    c.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ins = []
    for n in ('LP', 'T', 'W'):
        i = unreal.CustomInput()
        i.set_editor_property('input_name', n)
        ins.append(i)
    c.set_editor_property('inputs', ins)
    MEL.connect_material_expressions(lp, '', c, 'LP')
    MEL.connect_material_expressions(t, '', c, 'T')
    MEL.connect_material_expressions(w, '', c, 'W')
    x = MEL.create_material_expression(mat, unreal.MaterialExpressionTransform, -300, 700)
    x.set_editor_property('transform_source_type', unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL)
    x.set_editor_property('transform_type', unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
    MEL.connect_material_expressions(c, '', x, '')
    MEL.connect_material_property(x, '', unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)


def import_models(arg=''):
    import mare_hotel_lobby as hl
    from pathlib import Path
    if _game_world():
        raise RuntimeError('Stop PIE first')
    src = Path(unreal.Paths.project_dir()) / 'SourceArt/Models/Seafloor'
    names = [n for n in arg.split(',') if n] or sorted(p.stem for p in src.glob('*.glb'))
    out = {}
    for name in names:
        folder = f'/Game/Custom/Seafloor/{name}'
        if unreal.EditorAssetLibrary.does_directory_exist(folder):
            unreal.EditorAssetLibrary.delete_directory(folder)
        mesh = hl._import(src / f'{name}.glb', folder, name, False, search=False)
        mesh.set_editor_property('light_map_resolution', 32)
        b = mesh.get_bounds()
        mats = []
        for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
            a = unreal.load_asset(p)
            if not isinstance(a, unreal.Material):
                continue
            a.set_editor_property('used_with_instanced_static_meshes', True)
            a.set_editor_property('used_with_nanite', True)
            if name in KIND:
                _sway(a, SWAY[KIND[name]])
            errs = MEL.recompile_material(a)
            unreal.EditorAssetLibrary.save_loaded_asset(a, False)
            mats.append([a.get_name(), str(a.get_editor_property('blend_mode')).split('.')[-1], a.get_editor_property('two_sided')])
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
        out[name] = {'size': [round(b.box_extent.x * 2), round(b.box_extent.y * 2), round(b.box_extent.z * 2)],
                     'origin': [round(b.origin.x), round(b.origin.y), round(b.origin.z)], 'mats': mats}
    return json.dumps(out)


def qa(arg=''):
    """PIE: AMareController::ReefQA ('state', 'sharks')."""
    pc = unreal.GameplayStatics.get_player_controller(_game_world(), 0)
    return json.dumps([[c, pc.reef_qa(c)] for c in arg.split(';') if c])


def probe(arg='Local'):
    return json.dumps([n for n in dir(unreal) if n.startswith('MaterialExpression') and any(k in n for k in arg.split(','))])
