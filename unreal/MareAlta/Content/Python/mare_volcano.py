"""Volcanic island far out at sea (pedido do Sergio, 04/11): rocky cone with ash rising from the crater.

Meshes from tools/ue58/gen_volcano.py (SourceArt/Models/Volcano), CC0 Poly Haven textures rock_face and
burned_ground_01 (SourceArt/Textures/Custom). Entry points (mare_hud action 'module', arg "mare_volcano.<fn>|<text>"):
  probe   -> ocean bounds, to place the island
  build   -> import meshes, build materials, place (or move) the island actor; "x,y" overrides the position (cm)
"""
import json
from pathlib import Path
import unreal
import mare_materials as mm
from mare_hotel_lobby import _import

ROOT = Path(unreal.Paths.project_dir()).resolve()
MEL = unreal.MaterialEditingLibrary
FOLDER = '/Game/World/Volcano'
LABEL = 'Ilha vulcânica'
# 1.3 km off the beach (shore near y=-3000), a little east of the kiosk so it frames the sea view.
DEFAULT_AT = (9000.0, -130000.0, -60.0)


def probe(_=''):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        mesh = a.static_mesh_component.static_mesh
        if mesh and mesh.get_path_name().startswith('/Game/World/Ocean/'):
            o, e = a.get_actor_bounds(False)
            out.append({'label': a.get_actor_label(), 'origin': [o.x, o.y, o.z], 'extent': [e.x, e.y, e.z]})
    return json.dumps(out)


def _projected(mat, tex, size_cm):
    fn = unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture')
    obj = mm.expression(mat, unreal.MaterialExpressionTextureObject, texture=tex)
    call = mm.expression(mat, unreal.MaterialExpressionMaterialFunctionCall)
    call.set_editor_property('material_function', fn)
    mm.connect(obj, '', call, 'TextureObject')
    mm.connect(mm.expression(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(size_cm, size_cm, size_cm, 1)), '', call, 'TextureSize')
    return call


def _new_material(name):
    path = FOLDER + '/' + name
    mat = unreal.load_asset(path)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, FOLDER, unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    return mat


def rock_material():
    mat = _new_material('M_Volcano_Rock')
    mat.set_editor_property('used_with_nanite', True)
    tex = mm._custom_texture
    # Stratovolcano like Arenal: green forest on the lower, gentler slopes, grey ash and scree on the summit, dark rock
    # in the ravines (vertex colour R). Fully matte (Sergio: "vulcão não pode ser brilhoso"). On eruption nights
    # (MPC_MareTime.Volcano) the lava channels (vertex colour B) and the crater glow.
    rock = _projected(mat, tex('rock_face_diff_2k.jpg'), 2300)
    rock2 = _projected(mat, tex('rock_face_diff_2k.jpg'), 7100)
    ash = _projected(mat, tex('burned_ground_01_diff_2k.jpg'), 1100)
    grass = _projected(mat, mm.texture('leafy_grass_diff'), 900)
    rock_n = _projected(mat, tex('rock_face_nor_gl_2k.jpg', normal=True), 2300)
    # Masks from UV1 (see tools/ue58/gen_volcano.py): float3(ravine, wet, lava) like the old vertex colour.
    uvm = mm.expression(mat, unreal.MaterialExpressionTextureCoordinate, coordinate_index=1)
    pos = mm.expression(mat, unreal.MaterialExpressionWorldPosition)
    obj = mm.expression(mat, unreal.MaterialExpressionActorPositionWS)   # pivot = sea level (ObjectPosition is the bounds centre)
    vc = mm.custom(mat, 'float h=(P.z-O.z)/100; return float3(saturate(M.x),1-smoothstep(0,4,h),saturate(1-M.y));', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'M': uvm, 'P': pos, 'O': obj})
    nrm = mm.expression(mat, unreal.MaterialExpressionVertexNormalWS)
    vol = mm._mpc(mat, 'Volcano')
    time = mm.expression(mat, unreal.MaterialExpressionTime)
    noise2 = ('float vn(float2 x){float2 i=floor(x),f=frac(x);f=f*f*(3-2*f);'
              'float a=frac(sin(dot(i,float2(127.1,311.7)))*43758.55),b=frac(sin(dot(i+float2(1,0),float2(127.1,311.7)))*43758.55),'
              'c=frac(sin(dot(i+float2(0,1),float2(127.1,311.7)))*43758.55),d=frac(sin(dot(i+float2(1,1),float2(127.1,311.7)))*43758.55);'
              'return lerp(lerp(a,b,f.x),lerp(c,d,f.x),f.y);}')
    common = (
        'float3 L=float3(.3,.59,.11);'
        'float2 q=(P.xy-O.xy)/100; float h=(P.z-O.z)/100; float r=length(q);'
        'float n1=0,n2=0;{float2 x=q*0.018;float2 i=floor(x),f=frac(x);f=f*f*(3-2*f);'
        ' float a=frac(sin(dot(i,float2(127.1,311.7)))*43758.55),b=frac(sin(dot(i+float2(1,0),float2(127.1,311.7)))*43758.55);'
        ' float c=frac(sin(dot(i+float2(0,1),float2(127.1,311.7)))*43758.55),d=frac(sin(dot(i+float2(1,1),float2(127.1,311.7)))*43758.55);'
        ' n1=lerp(lerp(a,b,f.x),lerp(c,d,f.x),f.y);}'
        '{float2 x=q*0.09;float2 i=floor(x),f=frac(x);f=f*f*(3-2*f);'
        ' float a=frac(sin(dot(i,float2(127.1,311.7)))*43758.55),b=frac(sin(dot(i+float2(1,0),float2(127.1,311.7)))*43758.55);'
        ' float c=frac(sin(dot(i+float2(0,1),float2(127.1,311.7)))*43758.55),d=frac(sin(dot(i+float2(1,1),float2(127.1,311.7)))*43758.55);'
        ' n2=lerp(lerp(a,b,f.x),lerp(c,d,f.x),f.y);}'
        'float slope=1-saturate(N.z);'
        'float veg=(1-smoothstep(55,115,h+45*(n1-.5)+12*(n2-.5)))*(1-smoothstep(.42,.68,slope+.15*(n2-.5)))*(1-.55*saturate(V.r))*smoothstep(.6,2.5,h);'
        'float ashm=smoothstep(110,175,h+30*(n1-.5)+15*(n2-.5))*.8;')
    color = mm.custom(mat, common + (
        'float d=.55*dot(R,L)+.45*dot(R2,L);'
        'float3 rockc=float3(.17,.16,.15)*(.45+1.2*d)*lerp(1,.6,saturate(V.r));'
        'float3 ashc=float3(.21,.20,.19)*(.6+.8*dot(A,L));'
        'float3 forest=lerp(float3(.045,.075,.028),float3(.085,.12,.042),n2)*(.6+.8*dot(G,L))*(.8+.4*n1);'
        'float3 c=lerp(rockc,ashc,ashm*(1-.5*saturate(V.r)));'
        'c=lerp(c,forest,veg);'
        'return c*lerp(1,.7,saturate(V.g));'), unreal.CustomMaterialOutputType.CMOT_FLOAT3,
        {'R': rock, 'R2': rock2, 'A': ash, 'G': grass, 'V': vc, 'P': pos, 'O': obj, 'N': nrm})
    glow = mm.custom(mat, common + (
        # Red-hot lava flowing downhill: bright pulses travel down the channel (phase grows with height).
        'float flow=frac(h*.045+T*.22+n2*.6); float pulse=.55+.45*smoothstep(.0,.25,flow)*(1-smoothstep(.45,1,flow));'
        'float lava=pow(saturate(V.b),.7)*pulse;'
        'float crater=(1-smoothstep(12,26,r))*(1-smoothstep(132,148,h));'
        'return Vol*(lava*lerp(float3(9,.9,.08),float3(22,5,.6),pow(saturate(V.b),3))+crater*float3(16,3,.4));'), unreal.CustomMaterialOutputType.CMOT_FLOAT3,
        {'V': vc, 'P': pos, 'O': obj, 'N': nrm, 'T': time, 'Vol': vol})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(mm.expression(mat, unreal.MaterialExpressionConstant, r=1.0), '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(mm.expression(mat, unreal.MaterialExpressionConstant, r=0.2), '', unreal.MaterialProperty.MP_SPECULAR)
    MEL.connect_material_property(rock_n, '', unreal.MaterialProperty.MP_NORMAL)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError('M_Volcano_Rock ' + str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def ash_material():
    mat = _new_material('M_Volcano_Ash')
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property('two_sided', True)
    mat.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE)
    pos = mm.expression(mat, unreal.MaterialExpressionWorldPosition)
    time = mm.expression(mat, unreal.MaterialExpressionTime)
    uv = mm.expression(mat, unreal.MaterialExpressionTextureCoordinate)
    nrm = mm.expression(mat, unreal.MaterialExpressionVertexNormalWS)
    cam = mm.expression(mat, unreal.MaterialExpressionCameraVectorWS)
    # Billowing ash: scrolling 3D value noise (rises and drifts with the wind), thicker near the crater,
    # 07/11 (Sergio: "fumaça parada"): it rose ~0.8 m/s, invisible from kilometres away. Now ~7 m/s up, a wind drift,
    # and each octave moves at its own speed so the ash churns instead of sliding as one block.
    # thinning and fading at the top and at the silhouette edges (no hard tube outline).
    code = (
        'float3 p=(P-O)*0.00028-float3(T*0.045,0,T*0.19);'
        'float n=0,amp=.55,f=1;'
        '[unroll] for(int i=0;i<3;i++){float3 q=p*f+float3(sin(T*.05+i*1.7)*.6,T*.06*i,-T*.09*i); float3 c=floor(q),w=frac(q); w=w*w*(3-2*w);'
        ' float h=frac(sin(dot(c,float3(12.99,78.23,37.72)))*43758.55);'
        ' float hx=frac(sin(dot(c+float3(1,0,0),float3(12.99,78.23,37.72)))*43758.55);'
        ' float hy=frac(sin(dot(c+float3(0,1,0),float3(12.99,78.23,37.72)))*43758.55);'
        ' float hxy=frac(sin(dot(c+float3(1,1,0),float3(12.99,78.23,37.72)))*43758.55);'
        ' float hz=frac(sin(dot(c+float3(0,0,1),float3(12.99,78.23,37.72)))*43758.55);'
        ' float hxz=frac(sin(dot(c+float3(1,0,1),float3(12.99,78.23,37.72)))*43758.55);'
        ' float hyz=frac(sin(dot(c+float3(0,1,1),float3(12.99,78.23,37.72)))*43758.55);'
        ' float hxyz=frac(sin(dot(c+float3(1,1,1),float3(12.99,78.23,37.72)))*43758.55);'
        ' float v=lerp(lerp(lerp(h,hx,w.x),lerp(hy,hxy,w.x),w.y),lerp(lerp(hz,hxz,w.x),lerp(hyz,hxyz,w.x),w.y),w.z);'
        ' n+=v*amp; amp*=.5; f*=2.03;}'
        'float edge=pow(saturate(abs(dot(normalize(N),normalize(C)))*1.3),1.5);'
        'float h=1-UV.y;'
        'float body=smoothstep(0,.025,h)*(1-smoothstep(.3,.78,h));'
        'return saturate((n-.24)*1.9)*edge*body*lerp(1,.4,h);')
    opacity = mm.custom(mat, code, unreal.CustomMaterialOutputType.CMOT_FLOAT1, {'P': pos, 'O': mm.expression(mat, unreal.MaterialExpressionObjectPositionWS), 'T': time, 'UV': uv, 'N': nrm, 'C': cam})
    color = mm.custom(mat, 'return lerp(float3(.11,.10,.10),float3(.36,.35,.34),saturate((1-UV.y)*1.6));', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'UV': uv})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(opacity, '', unreal.MaterialProperty.MP_OPACITY)
    # Eruption nights: the lower plume is lit orange by the lava.
    ember = mm.custom(mat, 'return Vol*pow(saturate(1-(1-UV.y)*4),3)*float3(1.6,.35,.06);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'UV': uv, 'Vol': mm._mpc(mat, 'Volcano')})
    MEL.connect_material_property(ember, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(mm.expression(mat, unreal.MaterialExpressionConstant, r=1.0), '', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError('M_Volcano_Ash ' + str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def sparks_material():
    # Spark fountain: additive unlit, bright dashes running along each ballistic arc (UV u), only on eruption nights.
    mat = _new_material('M_Volcano_Sparks')
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    uv = mm.expression(mat, unreal.MaterialExpressionTextureCoordinate)
    time = mm.expression(mat, unreal.MaterialExpressionTime)
    glow = mm.custom(mat, (
        'float ph=frac(UV.y*7.13);'
        'float s=frac(UV.x*2.2-T*(.45+.3*ph)+ph);'
        'float dash=smoothstep(.0,.08,s)*(1-smoothstep(.12,.4,s));'
        'float fade=1-smoothstep(.55,1,UV.x);'
        'return Vol*dash*fade*lerp(float3(30,9,1.5),float3(18,3,.4),UV.x);'), unreal.CustomMaterialOutputType.CMOT_FLOAT3,
        {'UV': uv, 'T': time, 'Vol': mm._mpc(mat, 'Volcano')})
    MEL.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError('M_Volcano_Sparks ' + str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build(arg=''):
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    at = DEFAULT_AT
    if arg.strip():
        x, y = (float(v) for v in arg.split(','))
        at = (x, y, DEFAULT_AT[2])
    models = ROOT / 'SourceArt/Models/Volcano'
    island = _import(models / 'Volcano_Island.glb', FOLDER + '/Island', 'Volcano_Island', True, search=False)
    plume = _import(models / 'Volcano_Plume.glb', FOLDER + '/Plume', 'Volcano_Plume', False, search=False)
    sparks = _import(models / 'Volcano_Sparks.glb', FOLDER + '/Sparks', 'Volcano_Sparks', False, search=False)
    rock, ash, spark_mat = rock_material(), ash_material(), sparks_material()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = {}
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        if a.get_actor_label() in (LABEL, LABEL + ' · cinzas', LABEL + ' · fagulhas'):
            actors[a.get_actor_label()] = a
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    out = {}
    for label, mesh, mat in ((LABEL, island, rock), (LABEL + ' · cinzas', plume, ash), (LABEL + ' · fagulhas', sparks, spark_mat)):
        a = actors.get(label) or sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*at))
        a.set_actor_label(label)
        a.set_actor_location(unreal.Vector(*at), False, False)
        comp = a.static_mesh_component
        comp.set_static_mesh(mesh)
        comp.set_material(0, mat)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_collision_profile_name('NoCollision')
        comp.set_editor_property('can_ever_affect_navigation', False)
        if mesh is island:
            # The lava is emissive: as a Lumen light source it lit the whole island pale at night (04/11).
            comp.set_editor_property('affect_indirect_lighting_while_hidden', False) if False else None
            comp.set_editor_property('affect_dynamic_indirect_lighting', False)
            comp.set_editor_property('affect_distance_field_lighting', False)
        if mesh is not island:
            comp.set_editor_property('cast_shadow', False)
            comp.set_editor_property('affect_dynamic_indirect_lighting', False)
            if mesh is plume:
                a.tags = [unreal.Name('MareVolcanoPlume')]   # MareMarineWorld shows it only on smoky days
        o, e = a.get_actor_bounds(False)
        out[label] = {'origin': [round(o.x), round(o.y), round(o.z)], 'extent': [round(e.x), round(e.y), round(e.z)]}
    unreal.EditorLevelLibrary.save_current_level()
    return json.dumps(out)


def preview_glow(value=''):
    """QA in the editor before the C++ is rebuilt: MPC_MareTime.Volcano default (eruption look), '0' restores."""
    import mare_materials as m
    mpc = m.time_collection()
    params = list(mpc.get_editor_property('scalar_parameters'))
    for p in params:
        if str(p.get_editor_property('parameter_name')) == 'Volcano':
            p.set_editor_property('default_value', float(value or 0))
    mpc.set_editor_property('scalar_parameters', params)
    unreal.EditorAssetLibrary.save_loaded_asset(mpc)
    return 'Volcano default ' + str(float(value or 0))


def fix_mpc_ids(_=''):
    """A CollectionScalarParameter created from Python keeps a zero GUID and materials reject it ('invalid parameter');
    give every parameter without one a fresh id."""
    import mare_materials as m
    mpc = m.time_collection()
    params = list(mpc.get_editor_property('scalar_parameters'))
    fixed = []
    for p in params:
        gid = p.get_editor_property('id')
        if not unreal.GuidLibrary.is_valid(gid):
            p.set_editor_property('id', unreal.GuidLibrary.new_guid())
            fixed.append(str(p.get_editor_property('parameter_name')))
    mpc.set_editor_property('scalar_parameters', params)
    unreal.EditorAssetLibrary.save_loaded_asset(mpc)
    return json.dumps({'fixed': fixed, 'all': [str(p.get_editor_property('parameter_name')) for p in params]})


def vc_probe(_=''):
    p = unreal.InterchangeGenericAssetsPipeline()
    c = p.common_meshes_properties
    out = {k: str(c.get_editor_property(k)) for k in ('vertex_color_import_option', 'vertex_override_color') if hasattr(c, 'get_editor_property')}
    mesh = unreal.load_asset(FOLDER + '/Island/Volcano_Island')
    if mesh:
        out['mesh_has_colors'] = str(unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).has_vertex_colors(mesh))
    return json.dumps(out)


def ocean_probe(_=''):
    out = []
    for path in unreal.EditorAssetLibrary.list_assets('/Game/World/Ocean'):
        m = unreal.load_asset(path)
        if isinstance(m, unreal.StaticMesh):
            out.append({'mesh': path, 'verts': m.get_num_vertices(0), 'tris': m.get_num_triangles(0),
                        'bounds': str(m.get_bounds().box_extent)})
    return json.dumps(out)


def ash(_=''):
    """Rebuild only the ash material (07/11: faster, churning plume). Editor, PIE stopped."""
    ash_material()
    return 'ok'


def remove(_=''):
    """10/11 (Sergio: "tire o vulcão"): deletes the volcanic island and its plume and sparks from the level and saves it.
    The story now speaks of the sea (MareSummitWorld, definitions.json, tours.json); without the plume actor the
    eruption glow stays off (UMareMarineWorld). PIE stopped. build() puts it back."""
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    gone = []
    for a in actors.get_all_level_actors():
        if a.get_actor_label().startswith(LABEL):
            gone.append(a.get_actor_label())
            actors.destroy_actor(a)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'removed': gone})
