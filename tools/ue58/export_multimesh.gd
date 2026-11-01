extends SceneTree
## Re-exporta só as transformações por instância dos MultiMesh da Godot (grama, conchas, seixos, flores).
## Em --headless o servidor de renderização falso não guarda os dados do MultiMesh e tudo volta como
## identidade (foi o que empilhou 5.729 instâncias na origem); por isso rode COM janela:
##   Godot_v4.7.2-stable_win64_console.exe --path . --script tools/ue58/export_multimesh.gd
## Saída: D:/CodexTemp/multimesh/multimesh.json  {name: {count, mesh, transforms:[{position,basis}]}}
var output: String="D:/CodexTemp/multimesh/multimesh.json"
var groups: Dictionary={}
func _initialize() -> void:call_deferred("run")
func v3(v: Vector3) -> Array:return [v.x,v.y,v.z]
func visit(node: Node) -> void:
 if node is Node3D and not node.is_visible_in_tree():return
 if node is MultiMeshInstance3D and node.multimesh!=null:
  var mm: MultiMesh=node.multimesh
  var rows: Array=[]
  for i in mm.instance_count:
   var t: Transform3D=node.global_transform*mm.get_instance_transform(i)
   if mm.get_instance_transform(i).basis.determinant()<.0000001:continue
   rows.append({"position":v3(t.origin),"basis":[v3(t.basis.x),v3(t.basis.y),v3(t.basis.z)]})
  var key: String=str(node.name)
  if groups.has(key):key+="#"+str(groups.size())
  groups[key]={"count":rows.size(),"mesh":str(mm.mesh.resource_name if mm.mesh else ""),"parent":str(node.get_parent().name),"transforms":rows}
 for child in node.get_children():visit(child)
func run() -> void:
 DirAccess.make_dir_recursive_absolute(output.get_base_dir())
 var Core: Node=root.get_node("Core")
 seed(414141)
 Core.SAVE_PATH="user://ue_multimesh_probe.json"
 Core.new_game()
 var main=load("res://scenes/main.tscn").instantiate()
 root.add_child(main)
 current_scene=main
 for i in 3:await process_frame
 Core.set_process(false)
 main.set_process(false)
 main.village.set_process(false)
 visit(main.world)
 visit(main.operations)
 visit(main.get_node("Refinements"))
 var f:=FileAccess.open(output,FileAccess.WRITE)
 f.store_string(JSON.stringify(groups))
 f.close()
 var total: int=0
 for k in groups:total+=int(groups[k].count)
 print("UE_MULTIMESH groups=",groups.size()," instances=",total)
 quit(0)
