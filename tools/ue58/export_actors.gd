extends SceneTree
## Exporta personagens com rig/roupa/cabelo e objetos de interação, em perfil isolado.
var out: String="D:/Projetos/MareAltaUE58/unreal/MareAlta/SourceArt/Actors"
var Core: Node
func _initialize() -> void:call_deferred("run")
func pbr(mi: MeshInstance3D,guest: Node=null) -> void:
 var source: Material=mi.material_override
 if source==null:source=mi.mesh.surface_get_material(0)
 var mat:=StandardMaterial3D.new()
 if source is BaseMaterial3D:
  mat=source.duplicate()
  mat.diffuse_mode=BaseMaterial3D.DIFFUSE_BURLEY
  mat.specular_mode=BaseMaterial3D.SPECULAR_SCHLICK_GGX
  mat.shading_mode=BaseMaterial3D.SHADING_MODE_PER_PIXEL
  mat.rim_enabled=false
 elif source is ShaderMaterial:
  if source.shader.resource_path.contains("npc_eyes"):
   mat.albedo_color=source.get_shader_parameter("tint")
   mat.albedo_texture=source.get_shader_parameter("eye_texture")
   mat.roughness=.25
  elif guest!=null:
   var zone: float=float(source.get_shader_parameter("garment_zone"))
   var key: String="shirt" if zone==1 else ("shorts" if zone==2 else ("shoes" if zone==4 else "skin"))
   var value: Variant=mi.get_instance_shader_parameter(key)
   mat.albedo_color=value if value is Color else Color(.8,.78,.72)
   if bool(source.get_shader_parameter("use_fabric")):mat.albedo_texture=source.get_shader_parameter("fabric_texture")
   mat.roughness=.85
 mi.material_override=mat
func convert_node(node: Node,guest: Node=null) -> void:
 for child in node.get_children():
  if child is Node3D and not child.visible:
   node.remove_child(child);child.free();continue
  if child is AnimationTree or child is SkeletonModifier3D:
   node.remove_child(child);child.free();continue
  if child is MeshInstance3D:
   if not child.visible:node.remove_child(child);child.free();continue
   pbr(child,guest)
  convert_node(child,guest)
func export_scene(scene: Node3D,path: String) -> bool:
 var doc:=GLTFDocument.new()
 var state:=GLTFState.new()
 var e:int=doc.append_from_scene(scene,state)
 if e!=OK:return false
 return doc.write_to_filesystem(state,path)==OK
func run() -> void:
 Core=root.get_node("Core")
 Core.SAVE_PATH="user://ue_actor_export.json"
 Core.new_game()
 Core.set_process(false)
 DirAccess.make_dir_recursive_absolute(out)
 for i in (0 if "--props-only" in OS.get_cmdline_user_args() else 4):
  var guest=load("res://scripts/guest.gd").new()
  root.add_child(guest)
  var rng:=RandomNumberGenerator.new()
  rng.seed=18400+i
  guest.setup(i,rng)
  guest.set_process(false)
  guest._model.scale=Vector3.ONE
  convert_node(guest,guest)
  guest._skel.reset_bone_poses()
  guest._anim.stop()
  for library_name in guest._anim.get_animation_library_list():
   var library: AnimationLibrary=guest._anim.get_animation_library(library_name)
   for clip in library.get_animation_list():
    if not ["Idle_Loop","Idle","Idle_Talking_Loop","Idle_Talking","Walk_Loop","Walk","Sitting_Idle_Loop","Sitting_Idle","Interact"].any(func(suffix):return str(clip).ends_with(suffix)):library.remove_animation(clip)
  var name: String="Human_"+str(i)
  if not export_scene(guest._model,out+"/"+name+".glb"):push_error("ACTOR_EXPORT_FAILED "+name);quit(1);return
  print("ACTOR_EXPORTED ",name," female=",guest._female," clips=",guest._anim.get_animation_list())
  guest.free()
  await process_frame
 for name in ["player_home_door","coconut_open","cup_plastic","dish_fries","dish_fish_portion"]:
  var model=load("res://assets/models/gen/"+name+".glb").instantiate()
  root.add_child(model)
  convert_node(model)
  if not export_scene(model,out+"/"+name+".glb"):push_error("PROP_EXPORT_FAILED "+name);quit(1);return
  model.free()
 var presentation=load("res://scripts/dish_presentation.gd")
 for dish in presentation.RECIPES:
  for used in [false,true]:
   var holder:=Node3D.new()
   root.add_child(holder)
   var model: Node3D=presentation.build_used(holder,dish) if used else presentation.build(holder,dish)
   convert_node(holder)
   var name: String=("Used_" if used else "Dish_")+str(dish)
   if not export_scene(holder,out+"/"+name+".glb"):push_error("DISH_EXPORT_FAILED "+name);quit(1);return
   holder.free()
 print("DISH_EXPORT_PASS")
 print("ACTOR_EXPORT_PASS")
 Core.quit_game()
