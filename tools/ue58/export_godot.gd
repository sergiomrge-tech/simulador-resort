extends SceneTree
## Exportação de dados e geometria; não transporta scripts/shaders de Godot para o runtime UE.
var output: String="D:/Projetos/MareAltaUE58/unreal/MareAlta/SourceArt/World"
var chunks: Dictionary={}
var materials: Dictionary={}
var metadata: Dictionary={"chunks":[],"instances":[],"collisions":[],"texts":[],"tables":[],"residents":[],"paths":[],"doors":[]}
var area_nodes: Dictionary={}
var total: int=0
var Core: Node
func _initialize() -> void:call_deferred("run")
func encode(v: Variant) -> Variant:
 if v is Dictionary:
  var d: Dictionary={}
  for k in v:d[str(k)]=encode(v[k])
  return d
 if v is Array:
  var a: Array=[]
  for x in v:a.append(encode(x))
  return a
 if v is Vector3:return [v.x,v.y,v.z]
 if v is Vector2:return [v.x,v.y]
 if v is Color:return [v.r,v.g,v.b,v.a]
 if v is Rect2:return [v.position.x,v.position.y,v.size.x,v.size.y]
 if v is Object:return str(v)
 return v
func write(path: String,v: Variant) -> void:
 var f:=FileAccess.open(path,FileAccess.WRITE)
 f.store_string(JSON.stringify(encode(v),"\t"))
func run() -> void:
 DirAccess.make_dir_recursive_absolute(output)
 var data_path:=output.get_base_dir().get_base_dir()+"/Content/Data"
 DirAccess.make_dir_recursive_absolute(data_path)
 Core=root.get_node("Core")
 seed(414141)
 Core.SAVE_PATH="user://ue_migration_seed.json"
 Core.new_game()
 Core.save_game()
 write(data_path+"/default_save.json",JSON.parse_string(FileAccess.get_file_as_string(Core.SAVE_PATH)))
 var defs: Dictionary={"schema":1,"source_commit":"8d3be2d","engine":"Unreal Engine 5.8.3","art_direction":"realista estilizado, sem toon/contornos", "dishes":Economy.DISHES,"supplies":Economy.SUPPLIES,"expansions":Economy.EXPANSIONS,"expansion_order":Economy.EXPANSION_ORDER,"staff":Economy.STAFF,"quests":Economy.QUESTS,"campaign":Core.prog.Campaign.MAIN,"side_missions":Core.prog.Campaign.SIDE}
 var pd=load("res://scripts/prog_data.gd")
 defs["chapters"]=pd.CHAPTERS
 defs["businesses"]=pd.BUSINESSES
 write(data_path+"/definitions.json",defs)
 var probe:=Node3D.new()
 var cube:=MeshInstance3D.new()
 cube.name="CalibrationXYZ_1_2_3"
 cube.mesh=BoxMesh.new()
 cube.position=Vector3(1,2,3)
 probe.add_child(cube)
 export_scene(probe,output+"/Calibration.glb")
 probe.free()
 var main=load("res://scenes/main.tscn").instantiate()
 root.add_child(main)
 current_scene=main
 for i in 3:await process_frame
 Core.set_process(false)
 main.set_process(false)
 main.village.set_process(false)
 Core.minutes=11*60
 for id in main.world.areas:area_nodes[main.world.areas[id]]=str(id)
 metadata["tables"]=main.world.kiosk_spots
 metadata["paths"]=main.world.village_paths
 metadata["blocks"]=main.world.block_rects
 metadata["points"]=main.world.village_points
 for npc in main.village.get_children():
  if npc is Node3D and npc.has_meta("resident_name"):metadata.residents.append({"name":npc.get_meta("resident_name"),"position":npc.position,"rotation":npc.rotation})
 visit(main.world,"")
 # Móveis operacionais e decoração estão fora de World, mas pertencem ao cenário.
 visit(main.operations,"")
 visit(main.get_node("Refinements"),"")
 var priorities: Dictionary={}
 for inst in metadata.instances:
  var pos: Vector3=inst.transform.position
  var index: int=int(inst.mesh_index)
  var distance: float=Vector2(pos.x-38,pos.z+13).length()
  priorities[index]=minf(float(priorities.get(index,99999.0)),distance)
 for i in chunks.size():
  var name: String="World_"+str(i).pad_zeros(4)
  metadata.chunks.append({"name":name,"region":"shared","source":name+".glb","nodes":1})
 write(data_path+"/world.json",metadata)
 var order: Array=range(chunks.size())
 order.sort_custom(func(a,b):return float(priorities.get(a,99999))<float(priorities.get(b,99999)))
 var completed: int=0
 for index in order:
  var group: Node3D=chunks[chunks.keys()[index]]
  var name: String="World_"+str(index).pad_zeros(4)
  if not FileAccess.file_exists(output+"/"+name+".glb"):
   var error: int=export_scene(group,output+"/"+name+".glb")
   if error!=OK:push_error("UE_EXPORT_FAILED "+name);quit(1);return
  group.free()
  completed+=1
  print("UE_MODEL ",completed,"/",chunks.size()," ",name," distance=",priorities.get(index,0))
  await process_frame
 print("UE_EXPORT_PASS models=",completed," meshes=",total)
 Core.quit_game()
func export_scene(scene: Node3D,path: String) -> int:
 var document:=GLTFDocument.new()
 var state:=GLTFState.new()
 var err:=document.append_from_scene(scene,state)
 if err!=OK:return err
 return document.write_to_filesystem(state,path)
func transform(t: Transform3D) -> Dictionary:
 return {"position":t.origin,"basis":[t.basis.x,t.basis.y,t.basis.z]}
func visit(node: Node,region: String) -> void:
 if area_nodes.has(node):region=area_nodes[node]
 if node.name=="HotelWorld":region="grand_hotel"
 if str(node.name).begins_with("Biz_"):region=str(node.name)
 if node.has_meta("ue_region"):region=str(node.get_meta("ue_region"))
 if node is Node3D and not node.is_visible_in_tree():return
 if node.get_script()!=null and str(node.get_script().resource_path).ends_with("home_door.gd"):
  metadata.doors.append({"name":str(node.name),"transform":transform(node.global_transform),"label":node.door_label,"auto_close":node.auto_close})
  return
 if node is Label3D:
  if node.text!="":metadata.texts.append({"text":node.text,"transform":transform(node.global_transform),"size":node.font_size,"pixel_size":node.pixel_size,"region":region})
  return
 if node is CollisionShape3D and node.shape is BoxShape3D:
  metadata.collisions.append({"transform":transform(node.global_transform),"size":node.shape.size,"region":region,"interaction":node.get_parent() is Interactable,"name":str(node.get_parent().name)})
 if node is MeshInstance3D and node.mesh!=null:add_mesh(node.mesh,node.global_transform,node,region)
 if node is MultiMeshInstance3D and node.multimesh!=null:
  var mm: MultiMesh=node.multimesh
  for i in mm.instance_count:
   var t: Transform3D=mm.get_instance_transform(i)
   if t.basis.determinant()<.0000001:continue
   add_mesh(mm.mesh,node.global_transform*t,node,region)
 for child in node.get_children():visit(child,region)
func pbr(source: Material) -> Material:
 if source==null:return null
 if materials.has(source):return materials[source]
 var m: StandardMaterial3D
 if source is StandardMaterial3D:
  m=source.duplicate()
  m.diffuse_mode=BaseMaterial3D.DIFFUSE_BURLEY
  m.specular_mode=BaseMaterial3D.SPECULAR_SCHLICK_GGX
  m.shading_mode=BaseMaterial3D.SHADING_MODE_PER_PIXEL
  m.rim_enabled=false
  var color: Color=m.albedo_color
  m.albedo_color=Color.from_hsv(color.h,color.s*.9,minf(color.v,.92),color.a)
  var name: String=source.resource_name
  var texture_path: String="res://assets/tex/"+name+"_diff.jpg"
  if FileAccess.file_exists(texture_path):
   m.albedo_texture=load(texture_path)
   var normal_path: String=texture_path.replace("_diff","_nor")
   if FileAccess.file_exists(normal_path):m.normal_enabled=true;m.normal_texture=load(normal_path)
 else:
  m=StandardMaterial3D.new()
  m.albedo_color=Color(.35,.40,.28)
  m.roughness=.8
  if source is ShaderMaterial:
   var tex=source.get_shader_parameter("tex")
   if tex is Texture2D:m.albedo_texture=tex
   if source.shader.resource_path.contains("foliage"):
    m.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
    m.alpha_scissor_threshold=.4
    m.cull_mode=BaseMaterial3D.CULL_DISABLED
 materials[source]=m
 return m
func add_mesh(mesh: Mesh,t: Transform3D,original: GeometryInstance3D,region: String) -> void:
 if original is MeshInstance3D and original.skeleton!=NodePath("") and original.get_node_or_null(original.skeleton) is Skeleton3D:return
 var source: Material=original.material_override
 if source is ShaderMaterial and source.shader!=null:
  var shader: String=source.shader.resource_path
  if ["water","ocean","underwater","foam","sky","foliage"].any(func(word):return shader.contains(word)):
   return
 var signature: String=str(mesh.get_instance_id())+"|"+str(source.get_instance_id() if source else 0)
 if original is MeshInstance3D:
  for i in mesh.get_surface_count():
   var mat: Material=original.get_active_material(i)
   signature+="|"+str(mat.get_instance_id() if mat else 0)
 if not chunks.has(signature):
  var group:=Node3D.new()
  var copy:=MeshInstance3D.new()
  copy.name="Model_"+str(chunks.size())
  copy.mesh=mesh
  if source!=null:copy.material_override=pbr(source)
  elif original is MeshInstance3D:
   for i in mesh.get_surface_count():copy.set_surface_override_material(i,pbr(original.get_active_material(i)))
  else:
   for i in mesh.get_surface_count():copy.set_surface_override_material(i,pbr(mesh.surface_get_material(i)))
  group.add_child(copy)
  chunks[signature]=group
 metadata.instances.append({"mesh_index":chunks.keys().find(signature),"region":region,"transform":transform(t),"name":str(original.name)})
 total+=1
