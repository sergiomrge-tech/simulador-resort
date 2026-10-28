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
    blend='float edge=sin(Position.x*.0017)*90+sin(Position.x*.0041)*35; float wet=1-smoothstep(-3400,-2400,Position.y+edge); float inland=smoothstep(-1200,-500,Position.y+edge*.6); '
    color=custom(mat,blend+'float l=dot(Grass.rgb,float3(.2126,.7152,.0722)); float macro=.94+.06*sin(Position.x*.0013)*sin(Position.y*.0011); float3 turf=lerp(Grass.rgb,float3(.28,.48,.15)*l*1.8,.45)*macro; return lerp(lerp(Sand.rgb,Wet.rgb,wet),turf,inland);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{k:v for k,v in inputs.items() if 'Normal' not in k})
    normal=custom(mat,blend+'return normalize(lerp(lerp(SandNormal.xyz,WetNormal.xyz,wet),GrassNormal.xyz,inland));',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{k:v for k,v in inputs.items() if k=='Position' or 'Normal' in k})
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
    wpo=custom(mat,'float a=Position.x*.003+Position.y*.0017-Time*.55; float b=Position.y*.004-Position.x*.0012-Time*.38; return float3(0,0,sin(a)*9+sin(b)*5);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Position':pos,'Time':time})
    uv1=custom(mat,'return Position.xy*.0015 + Time*float2(.017,.011);',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos,'Time':time})
    uv2=custom(mat,'return float2(Position.x-Position.y*.37,Position.y+Position.x*.29)*.0021 + Time*float2(-.013,.008);',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'Position':pos,'Time':time})
    water_normal=unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions02/ExampleContent/Textures/water_n')
    samples=[]
    for uv in (uv1,uv2):
        node=expression(mat,unreal.MaterialExpressionTextureSample,texture=water_normal,sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        connect(uv,'',node,'UVs');samples.append(node)
    normal=custom(mat,'return normalize(float3((A.xy+B.xy)*.32,max(.65,A.z*B.z)));',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'A':samples[0],'B':samples[1]})
    color=custom(mat,'float offshore=1-smoothstep(-17000,-4000,Position.y); return lerp(float3(.018,.075,.067),float3(.006,.025,.039),offshore);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Position':pos})
    rough=expression(mat,unreal.MaterialExpressionConstant,r=.18)
    specular=expression(mat,unreal.MaterialExpressionConstant,r=.25)
    MEL.connect_material_property(specular,'',unreal.MaterialProperty.MP_SPECULAR)
    opacity=expression(mat,unreal.MaterialExpressionConstant,r=.5)
    for node,prop in [(wpo,unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET),(normal,unreal.MaterialProperty.MP_NORMAL),(color,unreal.MaterialProperty.MP_BASE_COLOR),(rough,unreal.MaterialProperty.MP_ROUGHNESS),(opacity,unreal.MaterialProperty.MP_OPACITY)]:MEL.connect_material_property(node,'',prop)
    output=expression(mat,unreal.MaterialExpressionSingleLayerWaterMaterialOutput)
    scattering=expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.001,.003,.004,1))
    absorption=expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.04,.012,.008,1))
    connect(scattering,'',output,'ScatteringCoefficients')
    connect(absorption,'',output,'AbsorptionCoefficients')
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat
