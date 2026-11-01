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
    normal=custom(mat,'return normalize(float3((A.xy+B.xy)*.12,1));',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'A':samples[0],'B':samples[1]})
    color=expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.03,.22,.30,1))
    rough=expression(mat,unreal.MaterialExpressionConstant,r=.04)
    opacity=expression(mat,unreal.MaterialExpressionConstant,r=.5)
    for node,prop in [(normal,unreal.MaterialProperty.MP_NORMAL),(color,unreal.MaterialProperty.MP_BASE_COLOR),(rough,unreal.MaterialProperty.MP_ROUGHNESS),(opacity,unreal.MaterialProperty.MP_OPACITY)]:MEL.connect_material_property(node,'',prop)
    output=expression(mat,unreal.MaterialExpressionSingleLayerWaterMaterialOutput)
    connect(expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.0015,.009,.012,1)),'',output,'ScatteringCoefficients')
    connect(expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.045,.010,.007,1)),'',output,'AbsorptionCoefficients')
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


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
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat
