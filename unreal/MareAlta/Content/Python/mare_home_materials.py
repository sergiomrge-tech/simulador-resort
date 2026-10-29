"""Reuse the authored TV glass and add animated, original coastal TV content."""
import json,math
from pathlib import Path
import unreal
from mare_materials import material, expression, custom, MEL


def build():
    root=Path(unreal.Paths.project_dir()).resolve()
    data=root/'Content/Data'
    world=json.loads((data/'world.json').read_text(encoding='utf-8-sig'))
    mapping=json.loads((data/'imported_meshes.json').read_text(encoding='utf-8-sig'))
    aliases=json.loads((data/'model_aliases.json').read_text(encoding='utf-8-sig'))
    row=next(r for r in world['instances'] if r['name']=='HomeTVGlassOff')
    key=f"World_{row['mesh_index']:04d}"
    catalog={'tv_screen_mesh':mapping[aliases.get(key,key)]}
    mat=material('M_HomeTV_Coast')
    mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('used_with_nanite',True)
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    mesh=unreal.load_asset(catalog['tv_screen_mesh']);bounds=mesh.get_bounds()
    width=bounds.box_extent.x*2*math.sqrt(sum(v*v for v in row['transform']['basis'][0]))
    height=bounds.box_extent.z*2*math.sqrt(sum(v*v for v in row['transform']['basis'][1]))
    position=expression(mat,unreal.MaterialExpressionWorldPosition)
    center=expression(mat,unreal.MaterialExpressionObjectPositionWS)
    uv=custom(mat,f'return float2((P.x-C.x)/{max(1,width):.6f}+.5,(P.z-C.z)/{max(1,height):.6f}+.5);',unreal.CustomMaterialOutputType.CMOT_FLOAT2,{'P':position,'C':center})
    time=expression(mat,unreal.MaterialExpressionTime)
    code='float2 p=float2(UV.x,1-UV.y);float w=.012*sin(p.x*24+Time*.8)+.008*sin(p.x*45-Time);float3 sky=lerp(float3(.72,.80,.78),float3(.33,.53,.64),smoothstep(.53,1,p.y));float3 sea=lerp(float3(.10,.28,.31),float3(.24,.48,.51),p.y*1.5);float foam=1-smoothstep(0,.018,abs(frac(p.y*7+w+Time*.035)-.5));sea+=foam*.10;float3 c=lerp(sea,sky,smoothstep(.527+w,.533+w,p.y));c=lerp(float3(.65,.58,.42),c,smoothstep(.02,.13+sin(p.x*4)*.06,p.y));return c*(.97+.03*sin(p.y*720))*30;'
    node=custom(mat,code,unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'UV':uv,'Time':time})
    MEL.connect_material_property(node,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors=list(MEL.recompile_material(mat))
    if errors:raise RuntimeError(str(errors))
    if not unreal.EditorAssetLibrary.save_loaded_asset(mat,False):raise RuntimeError('TV material was not saved; stop PIE')
    spray=material('M_ShowerWater')
    spray.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
    spray.set_editor_property('used_with_instanced_static_meshes',True)
    spray.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    color=expression(spray,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(60,64,62,1))
    alpha=expression(spray,unreal.MaterialExpressionConstant,r=.32)
    MEL.connect_material_property(color,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(alpha,'',unreal.MaterialProperty.MP_OPACITY)
    errors=list(MEL.recompile_material(spray))
    if errors:raise RuntimeError(str(errors))
    if not unreal.EditorAssetLibrary.save_loaded_asset(spray,False):raise RuntimeError('Shower material was not saved; stop PIE')
    (data/'home_assets.json').write_text(json.dumps(catalog,indent=2),encoding='utf-8')
    return catalog
