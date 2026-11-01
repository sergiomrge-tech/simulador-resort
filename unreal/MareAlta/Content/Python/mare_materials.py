"""Native physically based coast materials, built with Unreal material expressions."""
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
MEL=unreal.MaterialEditingLibrary

def connect(source,output,destination,input_name):
    if not MEL.connect_material_expressions(source,output,destination,input_name):
        names=list(MEL.get_material_expression_input_names(destination))
        raise RuntimeError(f'Connection failed {type(destination).__name__}.{input_name}; inputs={names}')


def material(name):
    path='/Game/World/Materials/'+name
    mat=unreal.load_asset(path)
    if not mat:mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,'/Game/World/Materials',unreal.Material,unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat,old)
    if MEL.get_num_material_expressions(mat)!=0:raise RuntimeError('Old material graph not cleared')
    return mat

def expression(mat,cls,**values):
    node=MEL.create_material_expression(mat,cls)
    for key,value in values.items():node.set_editor_property(key,value)
    return node

def custom(mat,code,output,inputs):
    node=expression(mat,unreal.MaterialExpressionCustom,code=code,output_type=output)
    values=[]
    for name in inputs:
        value=unreal.CustomInput();value.set_editor_property('input_name',name);values.append(value)
    node.set_editor_property('inputs',values)
    for name,source in inputs.items():connect(source,'',node,name)
    return node

def texture(name,normal=False):
    path='/Game/World/Terrain/'+name
    tex=unreal.load_asset(path)
    if not tex:
        task=unreal.AssetImportTask();task.filename=str(ROOT/'SourceArt'/'Terrain'/(name+'.jpg'));task.destination_path='/Game/World/Terrain';task.destination_name=name;task.automated=True;task.save=True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);tex=unreal.load_asset(path)
    if normal:
        tex.set_editor_property('srgb',False);tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP);tex.set_editor_property('flip_green_channel',True)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    return tex

def build_ground():
    mat=material('M_CoastGround_PBR')
    pos=expression(mat,unreal.MaterialExpressionWorldPosition)
    uv=custom(mat,'return Position.xy * 0.0022;',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos})
    inputs={'Position':pos}
    for key,name in [('Sand','coast_sand_01'),('Wet','damp_beach_sand'),('Grass','leafy_grass')]:
        for normal in (False,True):
            tex=texture(name+('_nor' if normal else '_diff'),normal)
            node=expression(mat,unreal.MaterialExpressionTextureSample,texture=tex,sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if normal else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
            connect(uv,'',node,'UVs')
            inputs[key+('Normal' if normal else '')]=node
    # Second, rotated and larger sampling of the dry sand hides the 4.5 m tile grid on pale sand.
    uv_b=custom(mat,'return float2(Position.x*.8-Position.y*.6,Position.x*.6+Position.y*.8)*0.00083;',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos})
    for normal in (False,True):
        node=expression(mat,unreal.MaterialExpressionTextureSample,texture=texture('coast_sand_01'+('_nor' if normal else '_diff'),normal),sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if normal else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
        connect(uv_b,'',node,'UVs')
        inputs['SandB'+('Normal' if normal else '')]=node
    blend='float edge=sin(Position.x*.0017)*90+sin(Position.x*.0041)*35; float wet=1-smoothstep(-3400,-2400,Position.y+edge); float inland=smoothstep(-1200,-500,Position.y+edge*.6); '
    color=custom(mat,blend+'float l=dot(Grass.rgb,float3(.2126,.7152,.0722)); float macro=.94+.06*sin(Position.x*.0013)*sin(Position.y*.0011); float detail=clamp(l*2.4,.65,1.25); float3 turf=lerp(Grass.rgb,float3(.10,.24,.045)*detail,.78)*macro; float mixb=.5+.35*sin(Position.x*.00031+sin(Position.y*.00047)*2.1)*sin(Position.y*.00027); float3 sand=lerp(Sand.rgb,SandB.rgb,mixb); float sl=dot(sand,float3(.2126,.7152,.0722)); float3 pale=lerp(sand,float3(sl,sl,sl),.45)*float3(1.85,1.8,1.68); float3 dry=min(pale+float3(.08,.075,.065),float3(.90,.88,.82)); float wl=dot(Wet.rgb,float3(.2126,.7152,.0722)); float3 damp=min(lerp(Wet.rgb,float3(wl,wl,wl),.3)*float3(1.35,1.3,1.2),float3(.66,.61,.53)); return lerp(lerp(dry,damp,wet),turf,inland);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{k:v for k,v in inputs.items() if 'Normal' not in k})
    normal=custom(mat,blend+'float mixb=.5+.35*sin(Position.x*.00031+sin(Position.y*.00047)*2.1)*sin(Position.y*.00027); float3 sn=normalize(lerp(SandNormal.xyz,SandBNormal.xyz,mixb)); return normalize(lerp(lerp(sn,WetNormal.xyz,wet),GrassNormal.xyz,inland));',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{k:v for k,v in inputs.items() if k=='Position' or 'Normal' in k})
    rough=custom(mat,blend+'return lerp(lerp(.9,.45,wet),.96,inland);',unreal.CustomMaterialOutputType.CMOT_FLOAT1,{'Position':pos})
    for node,prop in [(color,unreal.MaterialProperty.MP_BASE_COLOR),(normal,unreal.MaterialProperty.MP_NORMAL),(rough,unreal.MaterialProperty.MP_ROUGHNESS)]:MEL.connect_material_property(node,'',prop)
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat

def build_water():
    mat=material('M_CoastalWater_PBR')
    mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_SINGLE_LAYER_WATER)
    mat.set_editor_property('two_sided',True)
    mat.set_editor_property('used_with_nanite',False)
    mat.set_editor_property('automatically_set_usage_in_editor',False)
    pos=expression(mat,unreal.MaterialExpressionWorldPosition)
    time=expression(mat,unreal.MaterialExpressionTime)
    wpo=custom(mat,'float a=Position.x*.003+Position.y*.0017-Time*.55; float b=Position.y*.004-Position.x*.0012-Time*.38; float shore=smoothstep(-6500,-4300,Position.y)*(1-smoothstep(-3000,-2300,Position.y)); float swell=sin(Position.y*.009+sin(Position.x*.0025)*.7-Time*.8); float2 outside=max(float2(abs(Position.x-4000)-16000,-9500-Position.y),0); float fade=1-smoothstep(1500,6000,length(outside))*.85; float offshoreWaves=smoothstep(-2300,-4800,Position.y); return float3(0,0,(sin(a)*9+sin(b)*5)*fade*offshoreWaves+shore*(swell*.5+.5)*14);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Position':pos,'Time':time})
    uv1=custom(mat,'return Position.xy*.0015 + Time*float2(.017,.011);',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos,'Time':time})
    uv2=custom(mat,'return float2(Position.x-Position.y*.37,Position.y+Position.x*.29)*.0021 + Time*float2(-.013,.008);',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos,'Time':time})
    water_normal=unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions02/ExampleContent/Textures/water_n')
    samples=[]
    for uv in (uv1,uv2):
        node=expression(mat,unreal.MaterialExpressionTextureSample,texture=water_normal,sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        connect(uv,'',node,'UVs');samples.append(node)
    normal=custom(mat,'return normalize(float3((A.xy+B.xy)*.22,max(.72,A.z*B.z)));',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'A':samples[0],'B':samples[1]})
    color=custom(mat,'float offshore=1-smoothstep(-17000,-4000,Position.y); float near=1-smoothstep(-9000,-4200,Position.y); float3 sea=lerp(lerp(float3(.02,.16,.15),float3(.012,.07,.085),near),float3(.006,.03,.055),offshore); float shore=smoothstep(-6500,-4300,Position.y)*(1-smoothstep(-3000,-2300,Position.y)); float phase=Position.y*.009+sin(Position.x*.0025)*.7-Time*.8; float crest=smoothstep(.80,.985,sin(phase)); float n1=sin(Position.x*.0023+sin(Position.y*.004)*.8+Time*.1)*.5+.5; float n2=sin(Position.x*.0061-Time*.17+sin(Position.x*.0013)*2.0)*.5+.5; float breaks=smoothstep(.3,.75,n1)*(.55+.45*smoothstep(.2,.8,n2)); return lerp(sea,float3(.84,.89,.88),shore*crest*breaks*.55);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Position':pos,'Time':time})
    rough=expression(mat,unreal.MaterialExpressionConstant,r=.18)
    specular=expression(mat,unreal.MaterialExpressionConstant,r=.25)
    MEL.connect_material_property(specular,'',unreal.MaterialProperty.MP_SPECULAR)
    opacity=expression(mat,unreal.MaterialExpressionConstant,r=.5)
    for node,prop in [(wpo,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET),(normal,unreal.MaterialProperty.MP_NORMAL),(color,unreal.MaterialProperty.MP_BASE_COLOR),(rough,unreal.MaterialProperty.MP_ROUGHNESS),(opacity,unreal.MaterialProperty.MP_OPACITY)]:MEL.connect_material_property(node,'',prop)
    output=expression(mat,unreal.MaterialExpressionSingleLayerWaterMaterialOutput)
    scattering=expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.0012,.0058,.0062,1))
    absorption=expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.026,.0055,.0042,1))
    connect(scattering,'',output,'ScatteringCoefficients')
    connect(absorption,'',output,'AbsorptionCoefficients')
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_pool_water():
    """Clear swimming-pool water (Single Layer Water): the exported Godot pool shader fell back to
    an opaque dark green; this replaces it with bright, transparent pool-blue water."""
    mat=material('M_PoolWater_PBR')
    mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_SINGLE_LAYER_WATER)
    mat.set_editor_property('two_sided',True)
    mat.set_editor_property('used_with_nanite',False)
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    pos=expression(mat,unreal.MaterialExpressionWorldPosition)
    time=expression(mat,unreal.MaterialExpressionTime)
    water_normal=unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions02/ExampleContent/Textures/water_n')
    samples=[]
    for code in ('return Position.xy*.004 + Time*float2(.03,.02);','return float2(Position.x-Position.y*.4,Position.y+Position.x*.3)*.006 + Time*float2(-.02,.025);'):
        uv=custom(mat,code,unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos,'Time':time})
        node=expression(mat,unreal.MaterialExpressionTextureSample,texture=water_normal,sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        connect(uv,'',node,'UVs');samples.append(node)
    normal=custom(mat,'return normalize(float3((A.xy+B.xy)*.07,1));',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'A':samples[0],'B':samples[1]})
    # Clear, chlorinated water: little colour of its own; the tint comes from depth (absorption below).
    color=expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.02,.11,.12,1))
    rough=expression(mat,unreal.MaterialExpressionConstant,r=.02)
    MEL.connect_material_property(expression(mat,unreal.MaterialExpressionConstant,r=.5),'',unreal.MaterialProperty.MP_SPECULAR)
    opacity=expression(mat,unreal.MaterialExpressionConstant,r=.5)
    for node,prop in [(normal,unreal.MaterialProperty.MP_NORMAL),(color,unreal.MaterialProperty.MP_BASE_COLOR),(rough,unreal.MaterialProperty.MP_ROUGHNESS),(opacity,unreal.MaterialProperty.MP_OPACITY)]:MEL.connect_material_property(node,'',prop)
    output=expression(mat,unreal.MaterialExpressionSingleLayerWaterMaterialOutput)
    # Per cm, like the sea (M_CoastalWater_PBR) but ~4x clearer: 1.5 m keeps ~70% green/blue and ~15% red,
    # so the tiled floor stays visible with the natural cyan of a real pool.
    connect(expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.0003,.0016,.0018,1)),'',output,'ScatteringCoefficients')
    connect(expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.013,.0026,.002,1)),'',output,'AbsorptionCoefficients')
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_pool_tiles():
    """Pool floor and walls: 5 cm glass mosaic (aqua tiles, light grout, per-tile shade) with sunlit
    caustics, so the bottom reads through the clear M_PoolWater_PBR like in a real pool."""
    mat=material('M_PoolTiles_PBR')
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    mat.set_editor_property('used_with_nanite',True)
    pos=expression(mat,unreal.MaterialExpressionWorldPosition)
    nrm=expression(mat,unreal.MaterialExpressionVertexNormalWS)
    time=expression(mat,unreal.MaterialExpressionTime)
    night=expression(mat,unreal.MaterialExpressionCollectionParameter,collection=time_collection(),parameter_name='Night')
    plane='float3 an=abs(N); float2 uv=an.z>.5?P.xy:(an.x>an.y?P.yz:P.xz);'
    color=custom(mat,plane+'float2 cell=floor(uv/5.0); float2 g=frac(uv/5.0); float grout=smoothstep(.0,.07,min(g.x,g.y))*smoothstep(1.0,.93,max(g.x,g.y)); float h=frac(sin(dot(cell,float2(12.9898,78.233)))*43758.5453); float3 tile=lerp(float3(.30,.60,.74),float3(.38,.68,.80),h); tile*=.94+.06*frac(h*7.31); return lerp(float3(.80,.83,.80),tile,grout);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'P':pos,'N':nrm})
    rough=custom(mat,plane+'float2 g=frac(uv/5.0); float grout=smoothstep(.0,.07,min(g.x,g.y))*smoothstep(1.0,.93,max(g.x,g.y)); return lerp(.75,.18,grout);',unreal.CustomMaterialOutputType.CMOT_FLOAT1,{'P':pos,'N':nrm})
    # Caustics: three warped sine fields; bright thin lines where their sum crosses zero, drifting slowly.
    caustic=custom(mat,plane+'float2 q=uv*.02; float t=T*.55; float a=sin(q.x*1.7+sin(q.y*1.3+t)*1.6+t*.7); float b=sin(q.y*1.9+sin(q.x*1.1-t*.8)*1.7-t*.5); float c=sin((q.x+q.y)*1.3+sin(q.x*.7-q.y*.9+t*.9)*1.4+t*.4); float v=abs(a+b+c)/3.0; float lines=pow(saturate(1.0-v),6.0); float floorOnly=saturate(abs(N.z)*1.5-.3); return float3(1.0,.98,.9)*lines*floorOnly*(1.0-Night)*1.1;',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'P':pos,'N':nrm,'T':time,'Night':night})
    # Orca mural on each pool floor (Canva mosaic, one texel per 5 cm tile, tools/ue58/orca_mural.py):
    # 6 x 3 m in the resort pool, 9 x 4.5 m in the Grand Hotel pool, aligned to the tile grid.
    mural=_custom_texture('orca_mural.png')
    mural.set_editor_property('filter',unreal.TextureFilter.TF_NEAREST)
    mural.set_editor_property('mip_gen_settings',unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    mural.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    mural.set_editor_property('address_x',unreal.TextureAddress.TA_CLAMP);mural.set_editor_property('address_y',unreal.TextureAddress.TA_CLAMP)
    unreal.EditorAssetLibrary.save_loaded_asset(mural)
    place='bool hotel=abs(P.x+2600)<1300 && abs(P.y-3600)<800; float2 c=hotel?float2(-2600,3600):float2(0,400); float2 size=hotel?float2(900,450):float2(600,300);'
    mural_uv=custom(mat,place+'float2 cell=floor((P.xy-c+size*.5)/5.0); float2 uv=(cell+.5)/(size/5.0); return float2(uv.x,1.0-uv.y);',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'P':pos})
    sample=expression(mat,unreal.MaterialExpressionTextureSample,texture=mural)
    connect(mural_uv,'',sample,'UVs')
    final=custom(mat,plane+place+'float2 m=(P.xy-c)/size+.5; float inside=(all(m>0) && all(m<1))?1.0:0.0; float floorOnly=step(.7,an.z); float2 g=frac(uv/5.0); float grout=smoothstep(.0,.07,min(g.x,g.y))*smoothstep(1.0,.93,max(g.x,g.y)); float k=MuralA*inside*floorOnly*grout; return lerp(Tiles,MuralRGB,k);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'P':pos,'N':nrm,'Tiles':color,'MuralRGB':sample,'MuralA':sample})
    MEL.connect_material_expressions(sample,'A',final,'MuralA');MEL.connect_material_expressions(sample,'RGB',final,'MuralRGB')
    for node,prop in [(final,unreal.MaterialProperty.MP_BASE_COLOR),(rough,unreal.MaterialProperty.MP_ROUGHNESS),(caustic,unreal.MaterialProperty.MP_EMISSIVE_COLOR)]:MEL.connect_material_property(node,'',prop)
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def time_collection():
    """MPC_MareTime: scalar Night (0 day .. 1 night) written by UMareVisualWorld every tick."""
    path='/Game/World/Materials/MPC_MareTime'
    mpc=unreal.load_asset(path)
    if not mpc:
        mpc=unreal.AssetToolsHelpers.get_asset_tools().create_asset('MPC_MareTime','/Game/World/Materials',unreal.MaterialParameterCollection,unreal.MaterialParameterCollectionFactoryNew())
        p=unreal.CollectionScalarParameter();p.set_editor_property('parameter_name','Night');p.set_editor_property('default_value',0.0)
        mpc.set_editor_property('scalar_parameters',[p])
        unreal.EditorAssetLibrary.save_loaded_asset(mpc)
    return mpc


def build_window_pane():
    """Facade window glass seen from the street: the panes sit on the wall, so a transparent
    material showed plaster. Dark, polished glass reflects the sky like a real window by day,
    with a soft lighter band suggesting a curtain behind it."""
    mat=material('M_WindowPane_PBR')
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    mat.set_editor_property('used_with_nanite',True)
    pos=expression(mat,unreal.MaterialExpressionWorldPosition)
    color=custom(mat,'float band=smoothstep(.15,.35,frac(Position.z/280.0))*(1-smoothstep(.75,.95,frac(Position.z/280.0))); float folds=.85+.15*sin(Position.x*.21+Position.y*.21); return lerp(float3(.018,.026,.03),float3(.11,.10,.085)*folds,band*.35);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Position':pos})
    for node,prop in [(color,unreal.MaterialProperty.MP_BASE_COLOR),(expression(mat,unreal.MaterialExpressionConstant,r=.035),unreal.MaterialProperty.MP_ROUGHNESS),(expression(mat,unreal.MaterialExpressionConstant,r=.9),unreal.MaterialProperty.MP_SPECULAR)]:MEL.connect_material_property(node,'',prop)
    # Night: about 55% of the windows glow warm behind the curtain (per-instance random), like Godot.
    night=expression(mat,unreal.MaterialExpressionCollectionParameter,collection=time_collection(),parameter_name='Night')
    rnd=expression(mat,unreal.MaterialExpressionPerInstanceRandom)
    glow=custom(mat,'float lit=step(.45,R); float band=.6+.4*sin(Position.z*.02); return float3(1.0,.62,.30)*N*lit*band*3.0;',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'R':rnd,'N':night,'Position':pos})
    MEL.connect_material_property(glow,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_palm_frond():
    """Modelled palm leaflets: two-sided foliage with back-lighting and gentle colour variation."""
    mat=material('M_PalmFrond_PBR')
    mat.set_editor_property('two_sided',True)
    mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    mat.set_editor_property('used_with_nanite',True)
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    pos=expression(mat,unreal.MaterialExpressionWorldPosition)
    uv=expression(mat,unreal.MaterialExpressionTextureCoordinate)
    color=custom(mat,'float v=.5+.5*sin(Position.x*.013+Position.y*.017); float tip=UV.y; float3 a=float3(.055,.17,.03); float3 b=float3(.12,.26,.045); return lerp(lerp(a,b,v),float3(.16,.24,.06),tip*.35);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Position':pos,'UV':uv})
    sss=expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.18,.32,.04,1))
    for node,prop in [(color,unreal.MaterialProperty.MP_BASE_COLOR),(expression(mat,unreal.MaterialExpressionConstant,r=.55),unreal.MaterialProperty.MP_ROUGHNESS),(sss,unreal.MaterialProperty.MP_SUBSURFACE_COLOR)]:MEL.connect_material_property(node,'',prop)
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def _model_texture(file, folder, normal=False):
    """Texture shipped next to a re-exported model glTF (SourceArt/Models)."""
    name = Path(file).stem
    path = folder + '/' + name
    tex = unreal.load_asset(path)
    if not tex:
        task = unreal.AssetImportTask(); task.filename = str(ROOT / 'SourceArt' / 'Models' / file); task.destination_path = folder
        task.destination_name = name; task.automated = True; task.save = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]); tex = unreal.load_asset(path)
    if normal:
        tex.set_editor_property('srgb', False); tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    return tex


def build_palm_fab():
    """Fab "Coconut Tree" (CC BY 4.0): one atlas for trunk, fronds and nuts; fronds cut out by the
    alpha channel, lit from both sides like foliage."""
    folder = '/Game/Nature/Palms'
    color_tex = _model_texture('palm_fab_basecolor.png', folder)
    normal_tex = _model_texture('palm_fab_normal.jpg', folder, True)
    mat = material('M_PalmFab_PBR')
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property('two_sided', True)
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    color = expression(mat, unreal.MaterialExpressionTextureSample, texture=color_tex, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    normal = expression(mat, unreal.MaterialExpressionTextureSample, texture=normal_tex, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    sss = custom(mat, 'return Base.rgb * float3(.55,.75,.35);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'Base': color})
    MEL.connect_material_property(color, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(color, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.connect_material_property(normal, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(sss, '', unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.7), '', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_hp_tree():
    """Fab "HighPoly Tree Model" (Next Spring, CC BY 4.0): alpha-cut two-sided leaves + bark with normal."""
    folder = '/Game/Nature/Trees'
    leaf_tex = _model_texture('hp_tree_leaf.png', folder)
    bark_tex = _model_texture('hp_tree_trunk.png', folder)
    bark_nrm = _model_texture('hp_tree_trunk_normal.png', folder, True)
    leaf = material('M_HPTreeLeaf_PBR')
    leaf.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    leaf.set_editor_property('two_sided', True)
    leaf.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    for m in (leaf,):
        m.set_editor_property('used_with_nanite', True)
        m.set_editor_property('used_with_instanced_static_meshes', True)
    color = expression(leaf, unreal.MaterialExpressionTextureSample, texture=leaf_tex, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    MEL.connect_material_property(color, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(color, 'A', unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.connect_material_property(custom(leaf, 'return Base.rgb * float3(.6,.8,.4);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'Base': color}), '', unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
    MEL.connect_material_property(expression(leaf, unreal.MaterialExpressionConstant, r=.65), '', unreal.MaterialProperty.MP_ROUGHNESS)
    bark = material('M_HPTreeTrunk_PBR')
    bark.set_editor_property('used_with_nanite', True)
    bark.set_editor_property('used_with_instanced_static_meshes', True)
    c = expression(bark, unreal.MaterialExpressionTextureSample, texture=bark_tex, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    n = expression(bark, unreal.MaterialExpressionTextureSample, texture=bark_nrm, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    MEL.connect_material_property(c, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(n, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(expression(bark, unreal.MaterialExpressionConstant, r=.85), '', unreal.MaterialProperty.MP_ROUGHNESS)
    for m in (leaf, bark):
        errors = list(MEL.recompile_material(m))
        if errors: raise RuntimeError(str(errors))
        unreal.EditorAssetLibrary.save_loaded_asset(m)
    return {'leaf': leaf, 'trunk': bark}


def build_coconut():
    """Dry coconut (Fab, Rabeya Akter): husk with the CC0 Poly Haven palm_bark maps, fibre strands."""
    folder = '/Game/Nature/Coconut'
    diff = _model_texture('coconut_husk_diff.jpg', folder)
    nor = _model_texture('coconut_husk_nor_gl.jpg', folder, True)
    nor.set_editor_property('flip_green_channel', True)
    rough = _model_texture('coconut_husk_rough.jpg', folder)
    rough.set_editor_property('srgb', False)
    unreal.EditorAssetLibrary.save_loaded_asset(nor); unreal.EditorAssetLibrary.save_loaded_asset(rough)
    husk = material('M_CoconutHusk_PBR')
    fibre = material('M_CoconutFiber_PBR')
    fibre.set_editor_property('two_sided', True)
    for m in (husk, fibre):
        m.set_editor_property('used_with_nanite', True)
        m.set_editor_property('used_with_instanced_static_meshes', True)
    uv = custom(husk, 'return UV * 2.0;', unreal.CustomMaterialOutputType.CMOT_FLOAT2, {'UV': expression(husk, unreal.MaterialExpressionTextureCoordinate)})
    nodes = {}
    for key, tex, kind in (('c', diff, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR), ('n', nor, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL),
                           ('r', rough, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)):
        nodes[key] = expression(husk, unreal.MaterialExpressionTextureSample, texture=tex, sampler_type=kind)
        connect(uv, '', nodes[key], 'UVs')
    # Palm bark is grey-brown; a dry husk is warmer and darker.
    color = custom(husk, 'float l=dot(Base.rgb,float3(.2126,.7152,.0722)); return float3(.50,.27,.11)*clamp(l*2.3,.45,1.45);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'Base': nodes['c']})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(nodes['n'], 'RGB', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(nodes['r'], 'R', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(expression(fibre, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.22, .13, .06, 1)), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(expression(fibre, unreal.MaterialExpressionConstant, r=.9), '', unreal.MaterialProperty.MP_ROUGHNESS)
    for m in (husk, fibre):
        errors = list(MEL.recompile_material(m))
        if errors: raise RuntimeError(str(errors))
        unreal.EditorAssetLibrary.save_loaded_asset(m)
    return {'husk': husk, 'fiber': fibre}


def build_hill_ground():
    """Low-poly Godot hill tiles: CC0 Poly Haven aerial_grass_rock projected tri-planar in world space
    (no stretching on the steep faces), tinted toward the lawn green, with a second larger sample
    and macro variation so the tile repeat and the facets read as terrain."""
    folder = '/Game/World/Terrain'
    diff = _model_texture('hill_grass_rock_diff.jpg', folder)
    nor = _model_texture('hill_grass_rock_nor_gl.jpg', folder, True)
    nor.set_editor_property('flip_green_channel', True)
    unreal.EditorAssetLibrary.save_loaded_asset(nor)
    mat = material('M_HillGround_PBR')
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    fn = unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture')
    def projected(tex, size):
        obj = expression(mat, unreal.MaterialExpressionTextureObject, texture=tex)
        call = expression(mat, unreal.MaterialExpressionMaterialFunctionCall)
        call.set_editor_property('material_function', fn)
        connect(obj, '', call, 'TextureObject')
        connect(expression(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(size, size, size, 1)), '', call, 'TextureSize')
        return call
    near, far, nrm = projected(diff, 900.0), projected(diff, 4100.0), projected(nor, 900.0)
    pos = expression(mat, unreal.MaterialExpressionWorldPosition)
    color = custom(mat, 'float m=.5+.5*sin(P.x*.00021+sin(P.y*.00017)*2.0); float3 c=lerp(A.rgb,B.rgb,.45*m); float l=dot(c,float3(.2126,.7152,.0722)); float3 turf=float3(.11,.22,.05)*clamp(l*2.6,.55,1.35); return lerp(c,turf,.55)*(.9+.12*sin(P.x*.0009)*sin(P.y*.0007));',
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'A': near, 'B': far, 'P': pos})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(nrm, 'XYZ Texture', unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.92), '', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_lamp_glow():
    """Lamp globes and bulbs: frosted warm glass, softly lit by day, glowing at night (MPC_MareTime.Night).
    The Godot 'glow' materials were lost in the glTF export (they came in as the default grey)."""
    mat = material('M_LampGlow_PBR')
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    night = expression(mat, unreal.MaterialExpressionCollectionParameter, collection=time_collection(), parameter_name='Night')
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.92, .86, .72, 1)), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.25), '', unreal.MaterialProperty.MP_ROUGHNESS)
    glow = custom(mat, 'return float3(1.0,.70,.38)*(.05+N*N*60.0);', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'N': night})
    MEL.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_person_outfit():
    """Tintable clothing for the UBC people: the outfit atlas is desaturated (keeps folds, seams and
    stitching) and recoloured by 'Tint', so beach / social / casual outfits differ per person."""
    path = '/Game/Actors/Combined/Shared/M_PersonOutfit'
    mat = unreal.load_asset(path)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_PersonOutfit', '/Game/Actors/Combined/Shared', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('used_with_skeletal_mesh', True)
    atlas = expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, parameter_name='Atlas',
                       texture=unreal.load_asset('/Game/Actors/Combined/Human_0/Human_0_texture_6'))
    tint = expression(mat, unreal.MaterialExpressionVectorParameter, parameter_name='Tint', default_value=unreal.LinearColor(.8, .8, .8, 1))
    color = custom(mat, 'float l=dot(A.rgb,float3(.2126,.7152,.0722)); float detail=clamp(l*2.8,.45,1.25); return T.rgb*detail;',
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'A': atlas, 'T': tint})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.82), '', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def build_person_body():
    """UBC body with swimwear: the dark-grey underwear painted on the body atlas (bra/briefs) becomes a
    bikini or swim trunks in 'SwimTint'; skin is untouched. M_PersonHidden removes garment pieces."""
    path = '/Game/Actors/Combined/Shared/M_PersonBody'
    mat = unreal.load_asset(path)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_PersonBody', '/Game/Actors/Combined/Shared', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('used_with_skeletal_mesh', True)
    atlas = expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, parameter_name='Atlas',
                       texture=unreal.load_asset('/Game/Actors/Combined/Human_2/Human_2_texture_2'))
    tint = expression(mat, unreal.MaterialExpressionVectorParameter, parameter_name='SwimTint', default_value=unreal.LinearColor(.85, .2, .3, 1))
    code = ('float mx=max(A.r,max(A.g,A.b)); float mn=min(A.r,min(A.g,A.b)); float sat=(mx-mn)/max(mx,.001); float l=dot(A.rgb,float3(.2126,.7152,.0722));'
            ' float cloth=(1-smoothstep(.16,.30,sat))*(1-smoothstep(.22,.40,l)); float detail=clamp(l*4.0,.55,1.2);'
            ' return lerp(A.rgb,T.rgb*detail,cloth);')
    color = custom(mat, code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'A': atlas, 'T': tint})
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.62), '', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = list(MEL.recompile_material(mat))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    hidden = unreal.load_asset('/Game/Actors/Combined/Shared/M_PersonHidden')
    if not hidden:
        hidden = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_PersonHidden', '/Game/Actors/Combined/Shared', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(hidden)):
        MEL.delete_material_expression(hidden, old)
    hidden.set_editor_property('used_with_skeletal_mesh', True)
    hidden.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
    MEL.connect_material_property(expression(hidden, unreal.MaterialExpressionConstant, r=0), '', unreal.MaterialProperty.MP_OPACITY_MASK)
    errors = list(MEL.recompile_material(hidden))
    if errors: raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(hidden)
    return mat



def _custom_texture(file, normal=False, linear=False):
    """CC0 Poly Haven maps copied to SourceArt/Textures/Custom, imported into /Game/Custom/Textures."""
    name = Path(file).stem
    path = '/Game/Custom/Textures/' + name
    tex = unreal.load_asset(path)
    if not tex:
        task = unreal.AssetImportTask(); task.filename = str(ROOT / 'SourceArt/Textures/Custom' / file); task.destination_path = '/Game/Custom/Textures'
        task.destination_name = name; task.automated = True; task.save = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]); tex = unreal.load_asset(path)
    if normal:
        tex.set_editor_property('srgb', False); tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property('flip_green_channel', True)
    elif linear:
        tex.set_editor_property('srgb', False)
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    return tex


def _custom_pbr(name, slug, size_cm, color_code='return A.rgb;', emissive_code=None, two_sided=False, rough_const=None):
    """World-aligned (tri-planar) PBR so any exported mesh UV works; color_code may recolour A (diffuse)."""
    path = '/Game/Custom/Materials/' + name
    mat = unreal.load_asset(path)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, '/Game/Custom/Materials', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    mat.set_editor_property('two_sided', two_sided)
    fn = unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture')

    def projected(tex):
        obj = expression(mat, unreal.MaterialExpressionTextureObject, texture=tex)
        call = expression(mat, unreal.MaterialExpressionMaterialFunctionCall)
        call.set_editor_property('material_function', fn)
        connect(obj, '', call, 'TextureObject')
        connect(expression(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(size_cm, size_cm, size_cm, 1)), '', call, 'TextureSize')
        return call
    diff = projected(_custom_texture(slug + '_diff_1k.jpg'))
    nor = projected(_custom_texture(slug + '_nor_1k.jpg', normal=True))
    inputs = {'A': diff, 'P': expression(mat, unreal.MaterialExpressionWorldPosition), 'O': expression(mat, unreal.MaterialExpressionObjectPositionWS)}
    color = custom(mat, color_code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, inputs)
    MEL.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(nor, 'XYZ Texture', unreal.MaterialProperty.MP_NORMAL)
    rough_file = ROOT / 'SourceArt/Textures/Custom' / (slug + '_rough_1k.jpg')
    if rough_const is None and rough_file.exists():
        MEL.connect_material_property(projected(_custom_texture(slug + '_rough_1k.jpg', linear=True)), 'XYZ Texture', unreal.MaterialProperty.MP_ROUGHNESS)
    else:
        MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=rough_const or .6), '', unreal.MaterialProperty.MP_ROUGHNESS)
    if emissive_code:
        night = expression(mat, unreal.MaterialExpressionCollectionParameter, collection=time_collection(), parameter_name='Night')
        t = expression(mat, unreal.MaterialExpressionTime)
        glow = custom(mat, emissive_code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'N': night, 'T': t, 'P': inputs['P']})
        MEL.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError(name + str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat.get_path_name()


def build_custom_materials():
    """Material tiers of Data/customization.json from CC0 Poly Haven photo-scanned PBR sets."""
    lum = 'float l=dot(A.rgb,float3(.2126,.7152,.0722));'
    # Radial stripes around the umbrella centre (object position), over the linen weave detail.
    stripes = lum + 'float2 d=P.xy-O.xy; float a=atan2(d.y,d.x)/6.2831853+.5; float s=step(.5,frac(a*12.0)); float detail=clamp(l*2.2,.7,1.25); return lerp(%s,%s,s)*detail;'
    out = {}
    out['M_Custom_Counter_2'] = _custom_pbr('M_Custom_Counter_2', 'oak_wood_planks', 120)
    out['M_Custom_Counter_3'] = _custom_pbr('M_Custom_Counter_3', 'blue_painted_planks', 120, lum + 'return lerp(A.rgb,float3(.10,.52,.55)*clamp(l*2.6,.5,1.4),.65);')
    out['M_Custom_Counter_4'] = _custom_pbr('M_Custom_Counter_4', 'blue_floor_tiles_01', 90, 'return A.rgb*1.45;')
    out['M_Custom_Counter_5'] = _custom_pbr('M_Custom_Counter_5', 'teak_veneer', 140, 'return A.rgb*1.05;', rough_const=.32)
    out['M_Custom_Umbrella_1'] = _custom_pbr('M_Custom_Umbrella_1', 'rough_linen', 60, lum + 'return float3(.86,.80,.68)*clamp(l*2.0,.7,1.2);', two_sided=True)
    out['M_Custom_Umbrella_2'] = _custom_pbr('M_Custom_Umbrella_2', 'rough_linen', 60, stripes % ('float3(.08,.32,.62)', 'float3(.92,.92,.88)'), two_sided=True)
    out['M_Custom_Umbrella_3'] = _custom_pbr('M_Custom_Umbrella_3', 'rough_linen', 60, stripes % ('float3(.90,.38,.30)', 'float3(.93,.86,.70)'), two_sided=True)
    out['M_Custom_Umbrella_4'] = _custom_pbr('M_Custom_Umbrella_4', 'thatch_roof_angled', 140, lum + 'return lerp(A.rgb,float3(.66,.50,.28)*clamp(l*2.4,.5,1.4),.6);', two_sided=True)
    out['M_Custom_Umbrella_5'] = _custom_pbr('M_Custom_Umbrella_5', 'denim_fabric', 50, lum + 'return float3(.05,.09,.22)*clamp(l*3.0,.6,1.5);', two_sided=True)
    neon = 'return %s*(.8+N*N*40.0);'
    out['M_Custom_Sign_1'] = _custom_pbr('M_Custom_Sign_1', 'oak_wood_planks', 80)
    out['M_Custom_Sign_2'] = _custom_pbr('M_Custom_Sign_2', 'rough_linen', 40, 'return float3(.9,.9,.9);', emissive_code=neon % 'float3(1.0,.97,.92)', rough_const=.2)
    out['M_Custom_Sign_3'] = _custom_pbr('M_Custom_Sign_3', 'rough_linen', 40, 'return float3(.4,.9,.9);', emissive_code=neon % 'float3(.10,.95,.90)', rough_const=.2)
    out['M_Custom_Sign_4'] = _custom_pbr('M_Custom_Sign_4', 'rough_linen', 40, 'return float3(.95,.5,.8);', emissive_code=neon % 'float3(1.0,.18,.62)', rough_const=.2)
    rainbow = 'float h=frac(T*.08+P.x*.0015); float3 c=saturate(abs(frac(h+float3(0,.333,.667))*6-3)-1); return c*(.8+N*N*40.0);'
    out['M_Custom_Sign_5'] = _custom_pbr('M_Custom_Sign_5', 'rough_linen', 40, 'return float3(.9,.9,.9);', emissive_code=rainbow, rough_const=.2)
    # Water slide fibreglass: glossy colour over a faint weave so it does not read as flat plastic.
    glass = lum + 'return %s*clamp(l*1.6,.85,1.12);'
    out['M_Custom_Slide_2'] = _custom_pbr('M_Custom_Slide_2', 'rough_linen', 200, glass % 'float3(.05,.45,.75)', rough_const=.18)
    out['M_Custom_Slide_3'] = _custom_pbr('M_Custom_Slide_3', 'rough_linen', 200, glass % 'float3(.95,.72,.08)', rough_const=.18)
    out['M_Custom_Slide_4'] = _custom_pbr('M_Custom_Slide_4', 'rough_linen', 200, glass % 'float3(.93,.38,.30)', rough_const=.18)
    out['M_Custom_Slide_5'] = _custom_pbr('M_Custom_Slide_5', 'rough_linen', 200, 'return float3(.85,.85,.9);', emissive_code='float h=frac(T*.05+P.z*.002); float3 c=saturate(abs(frac(h+float3(0,.333,.667))*6-3)-1); return c*N*N*12.0;', rough_const=.18)
    return out
