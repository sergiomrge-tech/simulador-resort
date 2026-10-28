"""Preserve the original hotel collider; split derived render surfaces for Nanite."""
import json
from pathlib import Path
import unreal
from editor_toolset.toolsets.actor import ActorTools
ROOT=Path(unreal.Paths.project_dir()).resolve();OUT=Path('D:/CodexTemp/ue58-graphics')

def build():
 result={}
 for name in ('HotelTower_Opaque','HotelTower_Glass'):
  dest='/Game/Graphics/Architecture/'+name
  meshes=[unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(dest,recursive=True)]
  meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
  if not meshes:
   task=unreal.AssetImportTask();task.filename=str(ROOT/'SourceArt/Models'/(name+'.gltf'));task.destination_path=dest;task.automated=True;task.save=True
   pipeline=unreal.InterchangeGenericAssetsPipeline();pipeline.common_meshes_properties.bake_meshes=True;pipeline.mesh_pipeline.combine_static_meshes_behavior=unreal.InterchangeCombineStaticMeshesBehavior.ALL
   stack=unreal.InterchangePipelineStackOverride();stack.set_editor_property('override_pipelines',[unreal.SoftObjectPath(pipeline.get_path_name())]);task.options=stack;unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
   meshes=[unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(dest,recursive=True)];meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
  if len(meshes)!=1:raise RuntimeError(name+' imported '+str(len(meshes))+' meshes')
  mesh=meshes[0];opaque=name.endswith('Opaque')
  for slot in mesh.static_materials:
   mat=slot.material_interface
   if isinstance(mat,unreal.MaterialInstanceConstant):
    overrides=mat.get_editor_property('base_property_overrides')
    if opaque and overrides.override_blend_mode and overrides.blend_mode!=unreal.BlendMode.BLEND_OPAQUE:raise RuntimeError('Transparent slot in opaque proxy')
    root=mat.get_editor_property('parent')
    if opaque and isinstance(root,unreal.Material):
     if not root.get_path_name().startswith('/Game/'):
      path='/Game/Graphics/Architecture/Materials/M_Nanite_'+root.get_name();clone=unreal.load_asset(path) or unreal.EditorAssetLibrary.duplicate_asset(root.get_path_name(),path);mat.set_editor_property('parent',clone);root=clone
     root.set_editor_property('used_with_nanite',True);root.set_editor_property('used_with_instanced_static_meshes',True)
     errors=list(unreal.MaterialEditingLibrary.recompile_material(root))
     if errors:raise RuntimeError(str(errors))
     unreal.EditorAssetLibrary.save_loaded_asset(root,False);unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
  settings=mesh.get_editor_property('nanite_settings');settings.enabled=opaque;unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).set_nanite_settings(mesh,settings,True);unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
  b=mesh.get_bounds();result[name]={'path':mesh.get_path_name(),'triangles':mesh.get_num_nanite_triangles() if opaque else mesh.get_num_triangles(0),'fallback_triangles':mesh.get_num_triangles(0),'nanite':settings.enabled,'min':[b.origin.x-b.box_extent.x,b.origin.y-b.box_extent.y,b.origin.z-b.box_extent.z],'max':[b.origin.x+b.box_extent.x,b.origin.y+b.box_extent.y,b.origin.z+b.box_extent.z]}
 original=unreal.load_asset('/Game/World/Models/World_2365/World_2365.World_2365');b=original.get_bounds();lo=[b.origin.x-b.box_extent.x,b.origin.y-b.box_extent.y,b.origin.z-b.box_extent.z];hi=[b.origin.x+b.box_extent.x,b.origin.y+b.box_extent.y,b.origin.z+b.box_extent.z]
 if any(abs(min(r['min'][i] for r in result.values())-lo[i])>1 or abs(max(r['max'][i] for r in result.values())-hi[i])>1 for i in range(3)):raise RuntimeError('Derived hotel bounds differ from original')
 (OUT/'hotel-split-candidate.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 if sum(r['triangles'] for r in result.values())!=original.get_num_triangles(0):raise RuntimeError('Triangle count changed during split')
 (ROOT/'Content/Data/nanite_architecture.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return result

def integrate():
 if '/Coast.' not in unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name():raise RuntimeError('Coast only')
 assets=json.loads((ROOT/'Content/Data/nanite_architecture.json').read_text(encoding='utf-8'));report=[]
 for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
  components=list(actor.get_components_by_class(unreal.InstancedStaticMeshComponent))
  for source in components:
   if not source.static_mesh or source.static_mesh.get_name()!='World_2365':continue
   collision=str(source.get_collision_enabled());count=source.get_instance_count()
   if count==0:continue
   transforms=[source.get_instance_transform(i,True) for i in range(count)]
   for name,row in assets.items():
    component=next((c for c in components if name in str(c.get_editor_property('component_tags'))),None)
    if not component:
     component=ActorTools.add_component(actor,unreal.InstancedStaticMeshComponent.static_class(),name);component.set_editor_property('component_tags',[name]);component.set_static_mesh(unreal.load_asset(row['path']));component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);component.add_instances(transforms,False,True)
    component.set_visibility(True,False)
   source.set_visibility(False,False);source.set_cast_shadow(False)
   if str(source.get_collision_enabled())!=collision or source.get_instance_count()!=count:raise RuntimeError('Collider changed')
   report.append({'actor':actor.get_actor_label(),'source':source.static_mesh.get_path_name(),'instances':count,'collision_unchanged':collision,'render_proxies':assets})
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level();(OUT/'nanite-architecture-integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8');return report

def preview(enabled):
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
 if not world:raise RuntimeError('PIE required')
 count=0
 for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor):
  for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
   if c.static_mesh and c.static_mesh.get_name()=='World_2365':c.set_visibility(not enabled,False);c.set_cast_shadow(not enabled)
   if any('HotelTower_' in str(t) for t in c.component_tags):c.set_visibility(enabled,False);count+=c.get_instance_count()
 return {'enabled':enabled,'proxy_instances':count}
