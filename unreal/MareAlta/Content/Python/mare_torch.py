"""Tiki torches lit at night (10/11, demo simulation: the kiosk's torches stood dark at 21h30).

The torch is two meshes of the Godot export: World_1272 (bamboo pole, 1.92 m) and World_1273 (the flame, 52 cm), whose
'glow' material came through the glTF export as a plain orange (no emission): a dull orange cone by day and by night.
M_TorchFlame: fire that glows and flickers, drawn only from dusk on (by day the torch is out, as a real one); each flame
also gets a warm point light through UMareVisualWorld::BuildLamps (Kinds: World_1273).
probe(): where the flame mesh is and how many instances. build(): the material. apply(): material on the flame mesh
(PIE stopped; saves)."""
import json
import unreal

import mare_materials as mm

MEL = unreal.MaterialEditingLibrary
FLAME = 'World_1273'
PATH = '/Game/World/Materials/M_TorchFlame'


def _mesh():
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    for d in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'StaticMesh'), True):
        if str(d.asset_name) == FLAME:
            return unreal.load_asset(str(d.package_name))
    return None


def probe(arg=''):
    mesh = _mesh()
    out = {'mesh': mesh.get_path_name() if mesh else None, 'instances': [], 'materials': []}
    if not mesh:
        return json.dumps(out)
    out['materials'] = [str(m.material_interface.get_path_name()) if m.material_interface else None for m in mesh.static_materials]
    try:
        out['nanite'] = mesh.get_editor_property('nanite_settings').get_editor_property('enabled')
    except Exception:
        pass
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if c.get_editor_property('static_mesh') != mesh:
                continue
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                for i in range(c.get_instance_count()):
                    t = c.get_instance_transform(i, True)
                    out['instances'].append([a.get_actor_label(), round(t.translation.x), round(t.translation.y), round(t.translation.z), round(t.scale3d.z, 2)])
            else:
                t = c.get_world_transform()
                out['instances'].append([a.get_actor_label(), round(t.translation.x), round(t.translation.y), round(t.translation.z), round(t.scale3d.z, 2)])
    out['count'] = len(out['instances'])
    return json.dumps(out, ensure_ascii=False)


def build(arg=''):
    """Fire: white-yellow at the wick to orange-red at the tip (height in the mesh's own space), a flicker in the glow
    and in the tip (the mask eats the top unevenly), each torch out of step with the others (its world position).
    Masked out by day (MPC_MareTime.Night under .25)."""
    mat = unreal.load_asset(PATH)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_TorchFlame', '/Game/World/Materials', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided', True)
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    night = mm.expression(mat, unreal.MaterialExpressionCollectionParameter, collection=mm.time_collection(), parameter_name='Night')
    world = mm.expression(mat, unreal.MaterialExpressionWorldPosition)
    local = mm.expression(mat, unreal.MaterialExpressionTransformPosition,
                          transform_source_type=unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,
                          transform_type=unreal.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_INSTANCE)   # the flames are instances of one actor: LOCAL is the actor's space (the mask ate the flame down to a candle)
    MEL.connect_material_expressions(world, '', local, '')
    obj = mm.expression(mat, unreal.MaterialExpressionObjectPositionWS)
    time = mm.expression(mat, unreal.MaterialExpressionTime)
    glow = mm.custom(mat, '''
float h=saturate(L.z/52.0);
float ph=frac(dot(O.xy,float2(.0131,.0277)))*6.2832;
float fl=.78+.14*sin(T*11.0+ph)+.08*sin(T*23.7+ph*2.3+L.x*.3);
float3 core=float3(1.0,.74,.20), mid=float3(1.0,.40,.045), tip=float3(1.0,.17,.015);
float3 c=lerp(core,mid,smoothstep(.0,.45,h));c=lerp(c,tip,smoothstep(.45,1.0,h));
// night exposure is EV100 -1..-2: 26 all over came out as a solid white bulb and 1-4.5 as dull brown (pixels 135,80,20).
return c*fl*lerp(12.0,3.2,smoothstep(.0,.6,h))*smoothstep(.25,.6,N);''', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'L': local, 'O': obj, 'T': time, 'N': night})
    MEL.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mask = mm.custom(mat, '''
float h=saturate(L.z/52.0);
float ph=frac(dot(O.xy,float2(.0131,.0277)))*6.2832;
float a=atan2(L.y,L.x);
float top=.80+.12*sin(T*9.0+ph+a*3.0)+.08*sin(T*17.0+ph*1.7-a*5.0);
return (N>.25 && h<top)?1.0:0.0;''', unreal.CustomMaterialOutputType.CMOT_FLOAT1, {'L': local, 'O': obj, 'T': time, 'N': night})
    MEL.connect_material_property(mask, '', unreal.MaterialProperty.MP_OPACITY_MASK)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return json.dumps({'material': mat.get_path_name()})


def apply(arg=''):
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    mat = unreal.load_asset(PATH) or unreal.load_asset(json.loads(build())['material'])
    mesh = _mesh()
    before = [str(m.material_interface.get_name()) if m.material_interface else None for m in mesh.static_materials]
    for i in range(len(mesh.static_materials)):
        mesh.set_material(i, mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    return json.dumps({'mesh': mesh.get_path_name(), 'before': before, 'after': [str(m.material_interface.get_name()) for m in mesh.static_materials]})
