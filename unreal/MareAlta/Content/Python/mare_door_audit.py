"""Read door dimensions without modifying the level."""
import json,unreal

def inspect():
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 result=[]
 for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.MareServiceTarget):
  if str(a.get_editor_property('action'))!='Door':continue
  c=a.get_editor_property('door_mesh');m=c.get_editor_property('static_mesh');b=m.get_bounds()
  origin,extent=a.get_actor_bounds(False)
  result.append({'label':a.get_actor_label(),'location':str(a.get_actor_location()),'rotation':str(a.get_actor_rotation()),'scale':str(a.get_actor_scale3d()),'actor_origin':str(origin),'actor_extent':str(extent),'mesh':m.get_path_name(),'bounds_origin':str(b.origin),'bounds_extent':str(b.box_extent),'component_relative':str(c.get_relative_transform())})
 data=json.loads((__import__("pathlib").Path(unreal.Paths.project_dir())/"Content/Data/imported_meshes.json").read_text(encoding="utf-8-sig"))
 for key in ["World_0898","World_0899","World_0900"]:
  mesh=unreal.load_asset(data[key]);bounds=mesh.get_bounds();result.append({"key":key,"origin":str(bounds.origin),"extent":str(bounds.box_extent)})
 return result

def capture(name):
 if '-MareSaveRoot=D:/CodexTemp/ue58-door-waves' not in unreal.SystemLibrary.get_command_line():raise RuntimeError('Disposable profile required')
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
 if not world:raise RuntimeError('PIE is not running')
 if name not in ('sea-a','sea-b','door','rain-sea'):raise ValueError(name)
 path='D:/CodexTemp/ue58-door-waves/'+name+'.png'
 unreal.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename='+path)
 return path
