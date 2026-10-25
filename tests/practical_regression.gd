extends Node
var failed := false
func check(ok: bool, label: String) -> void:
	failed = failed or not ok
	print("[practical] ", "ok " if ok else "FAIL ", label)
func frames(count: int) -> void:
	for i in count: await get_tree().process_frame
func walk(main, destination: Vector3) -> void:
	var player = main.player
	for i in 240:
		var offset: Vector3 = destination - player.global_position
		offset.y = 0
		if offset.length() < 0.09: break
		player.velocity = offset.normalized() * 2.5 + Vector3(0, -0.5, 0)
		player.move_and_slide()
		await get_tree().physics_frame
	player.velocity = Vector3.ZERO
	check(Vector2(player.position.x, player.position.z).distance_to(Vector2(destination.x, destination.z)) < 0.16, "passagem física " + str(destination))
	var on_deck := absf(destination.x - main.world.KIOSK_C.x) < 2.8
	check(absf(player.position.y - (0.1 if on_deck else 0.0)) < 0.09, "piso contínuo sem queda · y=%.3f" % player.position.y)
func shot(main, label: String, pos: Vector3, yaw: float, pitch: float) -> void:
	if DisplayServer.get_name() == "headless": return
	main.player.set_view(pos, yaw+180.0, pitch)
	main.day.force_update()
	await frames(12)
	await RenderingServer.frame_post_draw
	var path := "user://qa_shots/" + label + ".png"
	get_viewport().get_texture().get_image().save_png(path)
	print("SHOT_SAVED ", path)
func run(main) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://qa_shots"))
	Core.new_game()
	Core.paused = true
	Core.in_game = false
	Core.money = 10000
	Core.minutes = 11 * 60
	Core.time_changed.emit(Core.day, Core.minutes)
	main.allow_faint = false
	main.player.set_physics_process(false)
	main.village.enabled = false
	main.guests.enabled = false
	main.operations.set_process(false)
	Core.configure_company("Quiosque Prático", "praia")
	Core.unlock_all()
	for role in Core.staff: Core.staff[role] = false
	for id in Core.stock: Core.stock[id] = 30
	Core.minutes = 22 * 60
	check(Core.hire("atendente"), "contratação fora do horário")
	check(main.operations.actors.has("atendente") and main.operations.actors.atendente.visible, "contratado aparece imediatamente com jogo pausado e quiosque fechado")
	check(Core.prog.staff_eff("atendente") == 0, "presença não libera trabalho fora do turno")
	Core.staff.atendente = false
	Core.staff_changed.emit()
	check(not main.operations.actors.atendente.visible, "demissão remove presença")
	Core.minutes = 11 * 60
	var c: Vector3 = main.world.KIOSK_C
	for station in main.operations.stations.values():
		check(absf(station.position.x - c.x) < 2 and absf(station.position.z - c.z) < 2.5, "estação dentro do quiosque")
	check(main.operations.get_node_or_null("ServiceDeck") == null, "sem anexo externo")
	check(main.world.find_child("KioskRearWall",true,false) != null, "parede traseira com colisão")
	main.player.global_position = main.world.kiosk_point(Vector3(3.6, 0.1, -0.85))
	await frames(4)
	var rear_ray := PhysicsRayQueryParameters3D.create(main.world.kiosk_point(Vector3(0, 1.2, -3.0)), main.world.kiosk_point(Vector3(0, 1.2, -1.8)), 1)
	var rear_hit: Dictionary = main.world.get_world_3d().direct_space_state.intersect_ray(rear_ray)
	check(not rear_hit.is_empty() and rear_hit.collider.name == "KioskRearWall", "parede bloqueia passagem física atrás dos equipamentos")
	await walk(main, main.world.kiosk_point(Vector3(0, 0.1, -0.85)))
	await walk(main, main.world.kiosk_point(Vector3(0, 0.1, 0.8)))
	await walk(main, main.world.kiosk_point(Vector3(0, 0.1, -0.85)))
	await walk(main, main.world.kiosk_point(Vector3(-3.6, 0.1, -0.85)))
	main.player.global_position = main.world.kiosk_point(Vector3(-1.2, 0.1, -0.65))
	check(main.operations.can_access("bebidas"), "geladeira acessível pelo corredor interno")
	main.player.global_position = main.world.kiosk_point(Vector3(-1.2, 0.1, -3.0))
	check(not main.operations.can_access("bebidas"), "não retira pela traseira do móvel")
	main.player.global_position = main.world.kiosk_point(Vector3(-1.2, 0.1, -0.65))
	for ingredient in Core.stock: Core.stock[ingredient] = 0
	Core.company.ready = {}
	Core.company.production = {}
	main.operations.sync_company()
	check(main.operations.products.get_child_count() == main.operations.shelf_menu().size(), "todos os produtos do expositor visíveis com estoque zero")
	check(main.operations.products.has_node("Shelf_coco_gelado") and main.operations.products.has_node("Shelf_petiscos"), "geladeira e armário têm produtos próprios")
	check(main.operations.products.get_node("Shelf_coco_gelado").get_meta("display_only"), "referência visual não cria estoque vendável")
	check(not Core.pickup_company_dish("coco_gelado"), "não vende exemplar de referência com estoque zero")
	var drink_models := 0
	for display in main.operations.products.get_children():
		if main.operations.Dishes.is_drink(str(display.get_meta("shelf_dish_id"))):
			for child in display.get_children():
				if child is Node3D and not child is Label3D: drink_models += 1
	check(drink_models == 12, "doze bebidas visíveis na geladeira")
	for ingredient in Core.stock: Core.stock[ingredient] = 30
	main.operations.sync_company()
	var stock_before: int = Core.stock.coco
	main.operations.open_station("bebidas")
	check(main.hud.phone.app == "servico", "E na geladeira abre a estação")
	var buttons: Array[String] = []
	for button in main.hud.phone.screen.find_children("*","Button",true,false): buttons.append(button.text)
	check(not "Preparar · 3 s" in buttons and "Pegar e levar ao cliente" in buttons, "estação oferece retirada sem preparo")
	main.hud.phone._service_action("coco_gelado", "pickup")
	check(Core.stock.coco == stock_before - 1 and Core.company.production.is_empty(), "retirada imediata consome estoque uma vez")
	check(Core.company.carry == "coco_gelado", "produto na mão sem esperar")
	check(main.operations.products.get_node("Shelf_coco_gelado").get_meta("stock_count") == 29, "etiqueta acompanha estoque de retirada")
	check(Core.return_company_dish(), "devolve produto pronto")
	main.operations.open_station("bebidas")
	main.hud.phone._service_action("coco_gelado","pickup")
	check(Core.stock.coco == stock_before - 1, "retirada após devolver não cobra duas vezes")
	var guest = main.village.spawn_customer()
	check(guest != null, "cliente para pedido de prova")
	if guest != null:
		guest.go([])
		guest.position = guest.spot.pos
		guest.set_meta("items", ["coco_gelado"])
		guest.set_meta("delivered", 0)
		main.village._order(guest, true)
		main.hud._update_orders()
		check(main.hud.orders_text.text.contains(main.operations.order_number(guest)) and main.hud.work_text.text.contains("Coco"), "pedido e item na mão claros no HUD")
		check(guest._bubble.text.begins_with("#") and guest._bubble.text.length() == 3, "marcador curto no cliente")
		check(main.operations.deliver(weakref(guest)) and guest.state == "kto_table", "entrega conclui pedido físico")
	main.village._on_slept(0)
	# Table reservations are served at the counter before the walk to a seat.
	for seat_index in [2,3]:
		var occupancy: Array = main.world.kiosk_spots.map(func(s): return s.busy)
		for i in main.world.kiosk_spots.size(): main.world.kiosk_spots[i].busy = i != seat_index
		var seated = main.village.spawn_customer()
		for i in main.world.kiosk_spots.size():
			if i != seat_index: main.world.kiosk_spots[i].busy = occupancy[i]
		check(seated != null and seated.get_meta("dining_spot",{}).get("table",false), "cliente com mesa reservada")
		if seated == null: continue
		seated.go([])
		seated.position = seated.spot.pos
		seated.rotation.y = seated.spot.rot
		seated.play("Idle")
		seated.set_meta("items",["coco_gelado"])
		seated.set_meta("delivered",0)
		seated.state = "kchoose"
		seated.set_meta("choose",0)
		main.village._kiosk_tick(.01)
		main.operations._process(0)
		check(not bool(seated.get_meta("order_taken",true)) and seated not in main.village.waiting_customers(), "pedido aguarda anotação no balcão")
		var target = seated.get_node("CustomerInteraction")
		main.player.position = main.operations.service_approach(seated)
		main.player.cam.look_at(target.global_position+Vector3(0,.20,0),Vector3.UP)
		await frames(4)
		main.player.refresh_focus()
		check(main.player.focus == target, "mira alcança cliente no balcão pelo lado interno")
		var stock_snapshot: Dictionary = Core.stock.duplicate()
		if DisplayServer.get_name() != "headless":
			await frames(2)
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png("user://qa_shots/table_order_"+str(seat_index)+".png")
		main.player.interact()
		check(bool(seated.get_meta("order_taken",false)) and seated in main.village.waiting_customers(), "E anota pedido do cliente no balcão")
		check(Core.stock == stock_snapshot, "anotar não consome produtos")
		var timer_before: float = seated.timer
		main.player.interact()
		check(seated.timer == timer_before, "consultar pedido anotado não reinicia paciência")
		check(Core.pickup_company_dish("coco_gelado"), "pega produto pronto para retirada")
		main.player.interact()
		check(seated.state == "kto_table" and Core.company.carry == "", "mesma interação entrega ao cliente no balcão")
		main.village._leave(seated)
		main.village._release_spot(seated)
		main.village.customers.erase(seated)
		seated.queue_free()
		Core.clean_company_seat(seat_index)
	main.hud.phone.close()
	main.hud._update_orders()
	check(main.hud.money_l.get_theme_font_size("font_size") == 20 and main.hud.prompt_l.get_theme_font_size("font_size") == 16, "HUD compacto")
	check(PhoneUI.HOME_APPS.size() == 6, "seis áreas na tela inicial")
	main.hud.phone.open("")
	await frames(4)
	check(main.hud.phone.navbar.get_child_count()==6, "seis abas distintas sem atalhos duplicados")
	main.hud.phone._open_management("painel")
	main.hud.phone._open_management("horarios")
	main.hud.phone.back()
	check(main.hud.phone.app == "painel", "voltar respeita a categoria")
	main.hud.phone.close()
	check(Core.hire("atendente"), "atendente contratado para conferência visual")
	check(main.operations.actors.atendente._skel.has_node("StaffBadge"),"uniforme com identificação por função")
	check(main.operations.menu_card.text.contains("PROMOÇÕES"),"cardápio físico acompanha receitas disponíveis")
	for cue in ["fridge","pickup","prepare","ready","cash"]:
		var stream: AudioStream = load("res://assets/audio/kiosk_" + cue + ".wav")
		check(stream != null and stream.get_length() > 0 and stream.get_length() < 1,"som curto sem vozes: " + cue)
	if DisplayServer.get_name() == "headless":
		main.audio.muted = false
		var before: int = main.audio.find_children("*","AudioStreamPlayer3D",true,false).size()
		main.audio.kiosk_sfx("cash",c)
		var after: int = main.audio.find_children("*","AudioStreamPlayer3D",true,false).size()
		main.audio.kiosk_sfx("cash",c)
		check(after == before+1 and main.audio.find_children("*","AudioStreamPlayer3D",true,false).size() == after,"som posicional reproduz e impede repetição excessiva")
		main.audio.muted = true
	main.operations._update_work_lighting(Core.day,12*60)
	var light = main.world.find_child("KioskWorkLight",true,false)
	var day_energy: float = light.light_energy
	main.operations._update_work_lighting(Core.day,20*60)
	check(light.light_energy > day_energy and light.light_color.b < .82,"luz mais quente e legível à noite")
	main.operations._update_work_lighting(Core.day,11*60)
	if DisplayServer.get_name() != "headless":
		main.operations.open_station("bebidas")
		await shot(main, "practical_station", main.world.kiosk_point(Vector3(0, .1, .75)), 0, -5)
		main.hud.phone.open("")
		await shot(main, "practical_phone", main.world.kiosk_point(Vector3(0, .1, .75)), 0, -5)
		main.hud.phone.close()
		Core.company.carry = ""
		Core.company.ready.suco = 2
		Core.company_changed.emit()
		if guest != null:
			guest.state = "kwait"
			guest.set_meta("items", ["suco"])
			guest.set_meta("delivered", 0)
			main.village._order(guest, true)
		main.hud._update_orders()
		await shot(main, "practical_orders", main.world.kiosk_point(Vector3(0, .1, .7)), 180, -4)
		await shot(main, "practical_workroom", main.world.kiosk_point(Vector3(0, .1, 1.15)), 0, -7)
		main.hud.root.visible = false
		await shot(main, "practical_facade", main.world.kiosk_point(Vector3(1.5, .35, 7)), 15, -3)
		# Isolate the two proof actors so passing pedestrians do not block the camera.
		for pedestrian in get_tree().get_nodes_in_group("npc"): pedestrian.hide()
		var shown: Dictionary = {}
		for i in 12:
			var person = main.village._make()
			var gender: String = "female" if person._female else "male"
			if shown.has(gender):
				person.queue_free()
				continue
			shown[gender] = person
			person.position = main.world.kiosk_point(Vector3(-.62 if person._female else .62, .1, 4.0))
			person.rotation.y = 0
			person.go([])
			person.set_process(false)
			check(person._face.get_node_or_null("Sunglasses") == null, "pessoas sem óculos escuros")
			person.apply_staff_uniform("atendente")
			var clothes = person.find_children("Tailored_*", "MeshInstance3D", true, false)
			check(clothes.size() == 5, "roupas importadas " + gender)
			check(person._body_mi.mesh.get_surface_count() > 0, "corpo preservado sob roupas " + gender)
			for clothing in clothes:
				check(clothing.skin != null and clothing.get_node(clothing.skeleton) == person._skel, "roupa ligada ao esqueleto existente")
			for hair in person._hair_parts:
				if str(hair.name).begins_with("Hair"):
					check(hair.get_parent() is BoneAttachment3D and hair.get_parent().bone_name == "Head", "cabelo rígido preso à cabeça animada")
			if shown.size() == 2: break
		await shot(main, "practical_clothing", main.world.kiosk_point(Vector3(0, .1, 6.3)), 0, -14)
		await shot(main, "people_portraits", main.world.kiosk_point(Vector3(0, .05, 5.55)), 0, 0)
		for person in shown.values():
			var apron = person._skel.get_node_or_null("Tailored_apron")
			check(apron != null and not apron.visible,"atendente usa uniforme de atendimento sem função de cozinha")
			person.set_meta("work_kind","pickup")
			person.set_meta("work_target",person.global_position+Vector3(-.18,1.05,.40))
		await frames(18)
		await shot(main,"staff_preparing",main.world.kiosk_point(Vector3(0,.05,5.55)),0,0)
		for person in shown.values(): person.remove_meta("work_target")
		for person in shown.values(): person.play("Walk_Loop")
		await frames(35)
		await shot(main, "practical_clothing_walk", main.world.kiosk_point(Vector3(0, .1, 6.3)), 0, -14)
		for person in shown.values(): person.play("Sitting_Idle_Loop")
		await frames(35)
		await shot(main, "practical_clothing_sit", main.world.kiosk_point(Vector3(0, .1, 6.3)), 0, -14)
	if DisplayServer.get_name() != "headless":
		Core.minutes = 17.5*60
		Core.time_changed.emit(Core.day,Core.minutes)
		await shot(main,"kiosk_sunset",main.world.kiosk_point(Vector3(1.5,.35,7)),15,-3)
		Core.minutes = 20*60
		Core.time_changed.emit(Core.day,Core.minutes)
		await shot(main,"kiosk_night",main.world.kiosk_point(Vector3(1.5,.35,7)),15,-3)
		Core.minutes = 11*60
	Core.company.created = false
	Core.company_changed.emit()
	check(main.operations.visible and main.operations.products.is_visible_in_tree(), "equipamentos e expositores presentes sem empresa criada")
	Core.staff.atendente = true
	Core.staff_changed.emit()
	check(main.operations.actors.has("atendente") and main.operations.actors.atendente.visible, "atendente aparece no modo anterior à criação da empresa")
	Core.prog.staff_rec("atendente").off = true
	Core.staff_changed.emit()
	check(not main.operations.actors.atendente.visible, "folga oculta atendente")
	print("PRACTICAL_TEST ", "FAIL" if failed else "PASS")
	Core.quit_game(1 if failed else 0)
