"""Restore the authored palm leaflet cutout lost by the legacy shader export.

Uses the original RGBA image and unchanged palm meshes. No texture repainting,
geometry decimation or new low-poly replacement. Native two-sided foliage handles
light transmission; very small vertex motion keeps the silhouette alive.
"""
import json
from pathlib import Path
import unreal
from mare_materials import material,expression,custom,connect,MEL

ROOT=Path(unreal.Paths.project_dir()).resolve()
LEAF='T_f1f14e18e199e61890449da926b5ea91f42718d35366bbbeeb76e236d47588b4.png'


def build():
    tex=unreal.load_asset('/Game/World/Terrain/T_PalmLeaflets')
    if not tex:
        task=unreal.AssetImportTask();task.filename=str(ROOT/'SourceArt/Textures'/LEAF)
        task.destination_path='/Game/World/Terrain';task.destination_name='T_PalmLeaflets';task.automated=True;task.save=True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);tex=unreal.load_asset('/Game/World/Terrain/T_PalmLeaflets')
    if not tex:raise RuntimeError('Authored palm leaflet texture missing')
    mat=material('M_PalmLeaflets_PBR')
    mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_MASKED)
    mat.set_editor_property('two_sided',True)
    mat.set_editor_property('opacity_mask_clip_value',.42)
    mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    mat.set_editor_property('used_with_nanite',True)
    sample=expression(mat,unreal.MaterialExpressionTextureSample,texture=tex,sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    color=custom(mat,'return lerp(Leaf.rgb*1.35,float3(.075,.16,.025),.25);',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Leaf':sample})
    transmission=custom(mat,'return Color*.65;',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Color':color})
    for node,output,prop in [(color,'',unreal.MaterialProperty.MP_BASE_COLOR),(sample,'A',unreal.MaterialProperty.MP_OPACITY_MASK),(transmission,'',unreal.MaterialProperty.MP_SUBSURFACE_COLOR)]:MEL.connect_material_property(node,output,prop)
    for value,prop in [(.78,unreal.MaterialProperty.MP_ROUGHNESS),(.2,unreal.MaterialProperty.MP_SPECULAR),(.65,unreal.MaterialProperty.MP_OPACITY)]:
        MEL.connect_material_property(expression(mat,unreal.MaterialExpressionConstant,r=value),'',prop)
    pos=expression(mat,unreal.MaterialExpressionWorldPosition);origin=expression(mat,unreal.MaterialExpressionObjectPositionWS);time=expression(mat,unreal.MaterialExpressionTime)
    wind=custom(mat,'float m=saturate((Position.z-Origin.z)/300); float phase=Time*.85+Origin.x*.003+Origin.y*.002; return float3(sin(phase)*3.5,cos(phase*.83)*2.5,0)*m;',unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Position':pos,'Origin':origin,'Time':time})
    MEL.connect_material_property(wind,'',unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    data=ROOT/'Content/Data';mapping=json.loads((data/'imported_meshes.json').read_text(encoding='utf-8-sig'))
    aliases=json.loads((data/'model_aliases.json').read_text(encoding='utf-8-sig'));changed=[]
    for source in (ROOT/'SourceArt/Models').glob('World_*.gltf'):
        gltf=json.loads(source.read_text(encoding='utf-8'))
        images=gltf.get('images',[]);textures=gltf.get('textures',[])
        for row in gltf.get('materials',[]):
            index=row.get('pbrMetallicRoughness',{}).get('baseColorTexture',{}).get('index',-1)
            if index<0 or Path(images[textures[index]['source']].get('uri','')).name!=LEAF:continue
            path=mapping[aliases.get(source.stem,source.stem)];mesh=unreal.load_asset(path)
            slots=mesh.get_editor_property('static_materials');target=row['name'];found=False
            for i,slot in enumerate(slots):
                if target in str(slot.material_slot_name) or (slot.material_interface and target in slot.material_interface.get_name()):
                    mesh.set_material(i,mat);found=True
            if not found:raise RuntimeError('Palm slot not identified: '+path)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh);changed.append(path)
    if len(set(changed))!=4:raise RuntimeError('Expected four original palm variants: '+str(changed))
    result={'palms':sorted(set(changed)),'leaf_material':mat.get_path_name(),'alpha_clip':.42,'two_sided':True,'geometry_preserved':True}
    (data/'foliage_visual.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
