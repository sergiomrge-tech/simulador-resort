extends Node3D
## Integração de decoração, encontros e qualidade. Estado persistente em Prog.experience.
const DECOR={
 "floreiras":{"title":"Jardim do quiosque","description":"Floreiras e vasos nos apoios laterais, fora das entradas.","price":90},
 "luzes":{"title":"Luzes de fim de tarde","description":"Cordão de lâmpadas sob o beiral, aceso ao anoitecer.","price":120},
 "expositor":{"title":"Expositor artesanal","description":"Bandejas de madeira, frutas e cerâmicas na bancada lateral.","price":150}}
const SPEAKERS=["Dona Rita","Dona Rita","Dona Rita","Dona Lourdes","Dona Rita","Seu Zé","Dona Lourdes","Padre Tomé","Padre Tomé","Dona Rita"]
var main
var decor_nodes: Dictionary={}
var night_lights: Array=[]
var fps: Label
var _last_quality: int=-1
var _leaves: float=5.0
func _ready() -> void:
 main=get_parent()
 _baseline_kiosk()
 _build_decor()
 _conversations()
 fps=Label.new()
 main.hud.root.add_child(fps)
 fps.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
 fps.position=Vector2(-175,-30)
 fps.size=Vector2(165,24)
 fps.add_theme_font_size_override("font_size",13)
 fps.mouse_filter=Control.MOUSE_FILTER_IGNORE
 Core.company_changed.connect(sync_decor)
 Core.expansion_bought.connect(func(_id):sync_decor())
 Quality.changed.connect(apply_details)
 call_deferred("apply_details")
 call_deferred("_dog_walk")
 sync_decor()
func _baseline_kiosk() -> void:
 var frame:=Node3D.new()
 frame.name="NauticalInterior"
 frame.transform=Transform3D(Basis(Vector3.UP,PI),main.world.KIOSK_C)
 add_child(frame)
 for x in [-1.7,1.6]:
  Real.place(frame,"lambis_shell",Vector3(x,1.30,.45),.12,.4)
 Real.place(frame,"ceramic_vase_02",Vector3(2.05,1.28,.15),.27,.3)
 Real.place(frame,"wooden_bowl_01",Vector3(-1.5,1.28,-.4),.10)
 # Poster náutico em fonte Blender: madeira, corda e arte original de praia.
 Real.place(frame,"g:nautical_wall_set",Vector3(-2.20,1.30,.2),-1,PI*.5)
 var lamp:=OmniLight3D.new()
 lamp.name="KioskContactShadows"
 lamp.position=Vector3(0,2.65,.2)
 lamp.omni_range=5.5
 lamp.light_color=Color(1,.97,.90)
 lamp.light_energy=.65
 lamp.shadow_enabled=true
 lamp.shadow_bias=.025
 lamp.shadow_normal_bias=.22
 frame.add_child(lamp)
func _build_decor() -> void:
 for id in DECOR:
  var node:=Node3D.new()
  node.name="Decor_"+str(id)
  node.transform=Transform3D(Basis(Vector3.UP,PI),main.world.KIOSK_C)
  add_child(node)
  decor_nodes[id]=node
  match str(id):
   "floreiras":
    for x in [-2.15,2.15]:Real.place(node,"potted_plant_04",Vector3(x,1.28,-.75),.46)
   "luzes":
    Real.place(node,"g:nautical_string_lights",Vector3(0,2.4,1.7),-1)
    for x in [-1.6,1.6]:
     var light:=OmniLight3D.new()
     light.position=Vector3(x,2.4,1.7)
     light.light_color=Color(1,.88,.67)
     light.light_energy=.35
     light.omni_range=2.5
     light.shadow_enabled=false
     node.add_child(light)
     night_lights.append(light)
   "expositor":
    Real.place(node,"g:nautical_counter_set",Vector3(1.75,1.28,-.45),-1)
func sync_decor() -> void:
 for id in decor_nodes:decor_nodes[id].visible=bool(Core.prog.experience.decor.get(id,false))
func buy_decor(id: String) -> bool:
 if not DECOR.has(id) or not Core.company.created or Core.prog.experience.decor.get(id,false):return false
 var cost: int=int(DECOR[id].price)
 if Core.money<cost:return false
 Core.prog.experience.decor[id]=true
 Core.book(-cost,str(DECOR[id].title),"melhoria",false)
 sync_decor()
 Core.save_game()
 return true
func _conversations() -> void:
 var people=["Dona Rita","Vendedor","Seu Zé","Padre Tomé","Dona Lourdes"]
 var index: int=0
 for npc in main.village.get_children():
  if not npc is Node3D or npc in main.village.walkers or npc.get_meta("sitter",false):continue
  if index>=people.size():break
  var who: String=people[index]
  index+=1
  npc.set_meta("resident_name",who)
  var target:=Interactable.new()
  target.name="Conversation"
  npc.add_child(target)
  target.position=Vector3(0,1.25,0)
  var cs:=CollisionShape3D.new()
  var shape:=CapsuleShape3D.new()
  shape.radius=.32
  shape.height=1.15
  cs.shape=shape
  target.add_child(cs)
  target.prompt_fn=func():return "Conversar · "+who
  target.action_fn=func():show_conversation(who,npc)
func show_conversation(who: String,npc=null) -> void:
 if is_instance_valid(npc):npc.service_reaction("pedir")
 Core.prog.experience.greeted[who]=true
 Core.save_game()
 var phone=main.hud.phone
 phone.resident_name=who
 phone.open("conversa")
 Input.mouse_mode=Input.MOUSE_MODE_VISIBLE

func apply_details() -> void:
 _geometry(main.world)
 for mm in get_tree().get_nodes_in_group("scalable_vegetation"):
  mm.multimesh.visible_instance_count=maxi(1,floori(mm.multimesh.instance_count*Quality.vegetation))
 var count: int=Quality.people_limit()
 if main.village.walkers.size()>count:
  while main.village.walkers.size()>count:
   var npc=main.village.walkers.pop_back()
   Core.release_visual(npc)
 # Aumentar sem reconstruir o mapa, mantendo as rotas e colisões existentes.
 while main.village.walkers.size()<count:
  var npc=main.village._make()
  var path: Array=main.world.village_paths[main.village.walkers.size()%main.world.village_paths.size()]
  npc.position=main.village._outside_blocks(path[0])
  npc.set_meta("path",path)
  npc.set_meta("dir",1)
  npc.set_meta("idx",0)
  npc.set_meta("wait",2.0)
  main.village.walkers.append(npc)
 var lamp=find_child("KioskContactShadows",true,false)
 if lamp:lamp.shadow_enabled=Quality.shadows!=0
func _geometry(node: Node) -> void:
 if node is GeometryInstance3D and not node is Label3D:
  if not node.has_meta("detail_base"):node.set_meta("detail_base",node.visibility_range_end)
  var distance: float=float(node.get_meta("detail_base"))
  node.visibility_range_end=(distance if distance>0 else 220.0)*Quality.detail_distance
 if node is Light3D and not node is DirectionalLight3D:
  if not node.has_meta("base_shadow"):node.set_meta("base_shadow",node.shadow_enabled)
  node.shadow_enabled=Quality.shadows!=0 and bool(node.get_meta("base_shadow"))
 for child in node.get_children():_geometry(child)
func _process(delta: float) -> void:
 fps.visible=Quality.show_fps
 if fps.visible:
  var rate: float=Engine.get_frames_per_second()
  fps.text="%d FPS · %.1f ms"%[rate,1000.0/maxf(1,rate)]
 for lamp in night_lights:lamp.visible=Core.minutes>17.5*60 or Core.minutes<6*60
 if not Core.in_game or Core.paused:return
 _leaves-=delta
 if _leaves<=0:
  _leaves=randf_range(8,15)
  if Core.weather!="rain" and Core.minutes>6*60 and Core.minutes<19*60:
   var nearby: Array=[]
   for tree in main.audio.BIRD_TREES:
    if main.player.global_position.distance_to(tree)<20:nearby.append(tree)
   if not nearby.is_empty():main.audio.at_position("leaves_soft",nearby.pick_random(),-25,"Ambiente")

func _dog_walk() -> void:
 for animal in get_tree().get_nodes_in_group("village_animals"):
  if animal.kind!="dog":continue
  var nearest=null
  var distance: float=18.0
  for walker in main.village.walkers:
   var d: float=animal.position.distance_to(walker.position)
   if d<distance:nearest=walker;distance=d
  if nearest!=null:animal.walking_partner=weakref(nearest)
  break

func resolve_resident_focus(camera: Camera3D,direct: Interactable) -> Interactable:
 if direct!=null and direct.has_meta("customer_ref"):return direct
 var choice: Interactable=direct
 var score: float=cos(deg_to_rad(9.0))
 for npc in main.village.get_children():
  if not npc is Node3D or not npc.has_meta("resident_name"):continue
  var aim: Vector3=npc.global_position+Vector3(0,1.6,0)
  var offset: Vector3=aim-camera.global_position
  if offset.length()>2.8 or offset.length()<.1:continue
  var dot: float=(-camera.global_basis.z).dot(offset.normalized())
  if dot<score:continue
  var query:=PhysicsRayQueryParameters3D.create(camera.global_position,aim,1,[main.player.get_rid()])
  if not main.get_world_3d().direct_space_state.intersect_ray(query).is_empty():continue
  choice=npc.get_node("Conversation")
  score=dot
 return choice
