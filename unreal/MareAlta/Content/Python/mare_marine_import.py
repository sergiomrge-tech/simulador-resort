"""Import existing attributed marine models, without changing the coastal map."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
def build():
 catalog={}
 for name in ('pirate_sailship','coastal_cruise','humpback_whale'):
  source=ROOT/'SourceArt/Marine'/(name+'.glb'); dest='/Game/Marine/'+name
  existing=[unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(dest,recursive=True)]
  meshes=[m for m in existing if isinstance(m,unreal.StaticMesh)]
  if not meshes:
   task=unreal.AssetImportTask();task.filename=str(source);task.destination_path=dest;task.automated=True;task.save=True
   pipeline=unreal.InterchangeGenericAssetsPipeline();pipeline.common_meshes_properties.bake_meshes=True
   pipeline.mesh_pipeline.combine_static_meshes_behavior=unreal.InterchangeCombineStaticMeshesBehavior.ALL
   stack=unreal.InterchangePipelineStackOverride();stack.set_editor_property('override_pipelines',[unreal.SoftObjectPath(pipeline.get_path_name())]);task.options=stack
   unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
   meshes=[unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(dest,recursive=True)]
   meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
  if len(meshes)!=1:raise RuntimeError(name+' expected one static mesh, got '+str([x.get_path_name() for x in meshes]))
  mesh=meshes[0];b=mesh.get_bounds()
  catalog[name]={'path':mesh.get_path_name(),'origin':[b.origin.x,b.origin.y,b.origin.z],'extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z]}
 (ROOT/'Content/Data/marine_assets.json').write_text(json.dumps(catalog,indent=2),encoding='utf-8')
 return catalog

def build_splash_material():
 from mare_materials import material,expression,custom,connect,MEL
 mat=material('M_WhaleRipple')
 mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
 mat.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
 mat.set_editor_property('two_sided',True)
 uv=expression(mat,unreal.MaterialExpressionTextureCoordinate)
 strength=expression(mat,unreal.MaterialExpressionScalarParameter,parameter_name='Strength',default_value=1.0)
 ripple=custom(mat,'float r=length((UV-.5)*2); float ring1=1-smoothstep(.04,.10,abs(r-.42)); float ring2=(1-smoothstep(.025,.07,abs(r-.68)))*.55; return saturate((ring1+ring2)*(1-smoothstep(.82,1,r))*Strength*.45);',unreal.CustomMaterialOutputType.CMOT_FLOAT1,{'UV':uv,'Strength':strength})
 color=expression(mat,unreal.MaterialExpressionConstant3Vector,constant=unreal.LinearColor(.6,.75,.72,1))
 MEL.connect_material_property(ripple,'',unreal.MaterialProperty.MP_OPACITY)
 MEL.connect_material_property(color,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 errors=list(MEL.recompile_material(mat))
 if errors:raise RuntimeError(str(errors))
 unreal.EditorAssetLibrary.save_loaded_asset(mat)
 return mat.get_path_name()
