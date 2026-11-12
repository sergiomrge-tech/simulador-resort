extends Node
var failed := false
func check(ok: bool, label: String) -> void:
 failed = failed or not ok
 print("[pier] ", "ok " if ok else "FAIL ", label)
func frames(count: int) -> void:
 for i in count:
  await get_tree().physics_frame
func run(main) -> void:
 Core.paused = true
 main.audio.muted = false # driver Dummy: exercita a reprodução sem saída no PC
 main.allow_faint = false
 main.guests.enabled = false
 main.village.enabled = false
 var player = main.player
 player.set_physics_process(true)
 await frames(3)
 var pane: StandardMaterial3D = main.world.VM.window_glass
 var neutral := Color(1, 1, 1, 0.16)
 check(pane.albedo_color.is_equal_approx(neutral) and not pane.emission_enabled, "janelas transparentes e sem pigmento ou emissão")
 main.world.set_night(1.0)
 check(pane.albedo_color.is_equal_approx(neutral) and not pane.emission_enabled, "vidro continua neutro à noite")
 main.world.set_night(0.0)
 var clear_boats := true
 var boat_count := 0
 for boat in get_tree().get_nodes_in_group("fishing_boats"):
  boat_count += 1
  for mi in boat.find_children("*", "MeshInstance3D", true, false):
   var bounds: AABB = mi.global_transform * mi.mesh.get_aabb()
   var rect := Rect2(Vector2(bounds.position.x, bounds.position.z), Vector2(bounds.size.x, bounds.size.z))
   if rect.intersects(Rect2(70.7, -46, 2.6, 24)) or rect.intersects(Rect2(69.7, -49, 4.6, 3)):
    print("[pier] barco sobre o cais: ", boat.global_position, " / ", mi.name, " / ", rect)
    clear_boats = false
 check(boat_count >= 3 and clear_boats, "cascos, mastros e velas fora da área do cais")
 var variants_ok := true
 for surface in ["carpet", "concrete", "wood"]:
  for index in 5:
   var clip = load("res://assets/audio/footstep_%s_%03d.ogg" % [surface, index]) as AudioStreamOggVorbis
   variants_ok = variants_ok and clip != null and clip.get_length() < 0.3 and not clip.loop
 check(variants_ok, "quinze pisadas curtas carregam sem loop")
 var footsteps: Array = []
 var capture := func(node: Node):
  if node is AudioStreamPlayer and node.stream and "footstep_" in node.stream.resource_path:
   footsteps.append(node.stream.resource_path)
   check(is_equal_approx(node.volume_db, -18.0), "pisada com volume suave")
 get_tree().node_added.connect(capture)
 var gaps := 0
 for x in [71.2, 72.0, 72.8]:
  for i in 55:
   var z: float = -21.5 - i * 0.5
   var query := PhysicsRayQueryParameters3D.create(Vector3(x, 2, z), Vector3(x, 0.1, z), 1, [player.get_rid()])
   var hit = main.world.get_world_3d().direct_space_state.intersect_ray(query)
   if hit.is_empty(): gaps += 1
 for x in [70.2, 73.8]:
  for z in [-46.5, -47.5, -48.5]:
   var query := PhysicsRayQueryParameters3D.create(Vector3(x, 2, z), Vector3(x, 0.1, z), 1, [player.get_rid()])
   if main.world.get_world_3d().direct_space_state.intersect_ray(query).is_empty(): gaps += 1
 check(gaps == 0, "piso contínuo na entrada, módulos, emendas e plataforma (%d lacunas)" % gaps)
 player.set_view(Vector3(72, 0.05, -19.5), 0)
 player.velocity = Vector3.ZERO
 player.move_input = Vector2(0, 1)
 Input.action_press("sprint")
 var reached := false
 var fell := false
 var swam := false
 for i in 480:
  await frames(1)
  fell = fell or player.global_position.y < -0.2
  swam = swam or player.swimming
  if player.global_position.z < -48.3:
   reached = true
   break
  if player.global_position.y < -3: break
 player.move_input = Vector2.ZERO
 Input.action_release("sprint")
 check(reached and not fell and not swam, "caminha da praia ao fim sem cair nem nadar: pos=%s caiu=%s nadou=%s" % [player.global_position, fell, swam])
 if reached:
  player.move_input = Vector2(0, 1)
  await frames(60)
  player.move_input = Vector2.ZERO
  check(player.global_position.z > -49.1 and player.global_position.y > 0.2, "limite final segura o personagem sobre a plataforma")
  player.move_input = Vector2(0, -1)
  Input.action_press("sprint")
  for i in 400:
   await frames(1)
   if player.global_position.z > -20: break
  player.move_input = Vector2.ZERO
  Input.action_release("sprint")
  check(player.global_position.z > -20 and player.global_position.y > -0.1, "volta pela rampa até a praia")
 player.set_view(Vector3(72, 0.5, -47.5), 0)
 player.velocity = Vector3.ZERO
 await frames(45)
 check(player.is_on_floor() and not player.swimming and absf(player.global_position.y - 0.37) < 0.08, "fica parado no piso do cais sobre o mar")
 check(player._footstep_surface() == "wood", "pisada de madeira identificada no piso do cais")
 var count_before := footsteps.size()
 await frames(30)
 check(footsteps.size() == count_before and count_before >= 8 and count_before < 70, "cadência de passos e silêncio quando parado: %d pisadas" % count_before)
 get_tree().node_added.disconnect(capture)
 var safe: Vector3 = player.global_position
 player.global_position.y = -100
 player.velocity.y = -50
 await frames(5)
 check(player.global_position.distance_to(safe) < 0.2 and player.velocity.y > -1, "recupera queda abaixo do mapa sem perder progresso")
 player.global_position = Vector3(72, 0.05, -19)
 check(player._footstep_surface() == "carpet", "impacto abafado na areia")
 player.global_position = Vector3(38, 0.15, main.world.STREET_Z + 2.9)
 check(player._footstep_surface() == "concrete", "pisada firme na calçada")
 # Fora do cais, o nado continua disponível.
 player.set_view(Vector3(65, -2.0, -48), 0)
 player.velocity = Vector3.ZERO
 await frames(5)
 check(player.swimming, "nado preservado fora do cais")
 player.move_input = Vector2.ZERO
 print("PIER_TEST ", "FAIL" if failed else "PASS")
 Core.quit_game(1 if failed else 0)
