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
	main.player.set_view(pos, yaw, pitch)
	main.day.force_update()
	await frames(12)
	await RenderingServer.frame_post_draw
	var path := "res://shots/" + label + ".png"
	get_viewport().get_texture().get_image().save_png(path)
	print("SHOT_SAVED ", path)
func run(main) -> void:
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
	check(Core.hire("cozinheiro"), "contratação fora do horário")
	check(main.operations.actors.has("cozinheiro") and main.operations.actors.cozinheiro.visible, "contratado aparece imediatamente com jogo pausado e quiosque fechado")
	check(Core.prog.staff_eff("cozinheiro") == 0, "presença não libera trabalho fora do turno")
	Core.staff.cozinheiro = false
	Core.staff_changed.emit()
	check(not main.operations.actors.cozinheiro.visible, "demissão remove presença")
	Core.minutes = 11 * 60
	var c: Vector3 = main.world.KIOSK_C
	for station in main.operations.stations.values():
		check(absf(station.position.x - c.x) < 2 and absf(station.position.z - c.z) < 2.5, "estação dentro do quiosque")
	check(main.operations.get_node_or_null("ServiceDeck") == null, "sem anexo externo")
	main.player.global_position = c + Vector3(3.6, 0.1, -0.85)
	await frames(4)
	await walk(main, c + Vector3(0, 0.1, -0.85))
	await walk(main, c + Vector3(0, 0.1, 0.8))
	await walk(main, c + Vector3(0, 0.1, -0.85))
	await walk(main, c + Vector3(-3.6, 0.1, -0.85))
	main.player.global_position = c + Vector3(-1.2, 0.1, -0.65)
	check(main.operations.can_access("bebidas"), "geladeira acessível pelo corredor interno")
	main.player.global_position = c + Vector3(-1.2, 0.1, -3.0)
	check(not main.operations.can_access("bebidas"), "não retira pela traseira do móvel")
	main.player.global_position = c + Vector3(-1.2, 0.1, -0.65)
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
	var stock_before: int = Core.stock.coco
	main.operations.open_station("bebidas")
	check(main.hud.phone.app == "servico", "E na geladeira abre a estação")
	main.hud.phone._service_action("coco_gelado", "prepare")
	check(Core.stock.coco == stock_before - 1 and not Core.company.production.is_empty(), "preparo consome ingrediente uma vez")
	Core.tick_company(10)
	check(int(Core.company.ready.get("coco_gelado", 0)) == 1, "preparo abastece geladeira")
	check(main.operations.products.get_node("Shelf_coco_gelado").get_meta("stock_count") == 1, "etiqueta acompanha preparo real")
	main.operations.open_station("bebidas")
	main.hud.phone._service_action("coco_gelado", "pickup")
	check(Core.company.carry == "coco_gelado" and int(Core.company.ready.coco_gelado) == 0, "retirada transfere produto para a mão")
	check(main.operations.products.get_node("Shelf_coco_gelado").get_meta("display_only") and main.operations.products.get_child_count() == main.operations.shelf_menu().size(), "retirar último item mantém os expositores completos")
	var guest = main.village.spawn_customer()
	check(guest != null, "cliente para pedido de prova")
	if guest != null:
		guest.go([])
		guest.position = guest.spot.pos
		guest.set_meta("items", ["coco_gelado"])
		guest.set_meta("delivered", 0)
		main.village._order(guest)
		main.hud._update_orders()
		check(main.hud.orders_text.text.contains(main.operations.order_number(guest)) and main.hud.work_text.text.contains("Coco"), "pedido e item na mão claros no HUD")
		check(guest._bubble.text.begins_with("#") and guest._bubble.text.length() == 3, "marcador curto no cliente")
		check(main.operations.deliver(weakref(guest)) and guest.state == "keat", "entrega conclui pedido físico")
	main.hud.phone.close()
	main.hud._update_orders()
	check(main.hud.money_l.get_theme_font_size("font_size") == 20 and main.hud.prompt_l.get_theme_font_size("font_size") == 16, "HUD compacto")
	check(PhoneUI.HOME_APPS.size() == 6, "seis áreas na tela inicial")
	main.hud.phone.open("")
	await frames(4)
	var home_buttons := 0
	for child in main.hud.phone.screen.find_children("*", "Button", true, false): home_buttons += 1
	check(home_buttons == 6, "sem atalhos duplicados no início")
	main.hud.phone._open_management("painel")
	main.hud.phone._open_management("horarios")
	main.hud.phone.back()
	check(main.hud.phone.app == "painel", "voltar respeita a categoria")
	main.hud.phone.close()
	check(Core.hire("caixa"), "caixa contratado para conferência visual")
	if DisplayServer.get_name() != "headless":
		main.operations.open_station("bebidas")
		await shot(main, "practical_station", c + Vector3(0, .1, .75), 0, -5)
		main.hud.phone.open("")
		await shot(main, "practical_phone", c + Vector3(0, .1, .75), 0, -5)
		main.hud.phone.close()
		Core.company.carry = ""
		Core.company.ready.suco = 2
		Core.company_changed.emit()
		if guest != null:
			guest.state = "kwait"
			guest.set_meta("items", ["suco"])
			guest.set_meta("delivered", 0)
			main.village._order(guest)
		main.hud._update_orders()
		await shot(main, "practical_orders", c + Vector3(0, .1, .7), 180, -4)
		await shot(main, "practical_workroom", c + Vector3(0, .1, 1.15), 0, -7)
		main.hud.root.visible = false
		await shot(main, "practical_facade", c + Vector3(1.5, .35, 7), 15, -3)
	Core.company.created = false
	Core.staff.atendente = true
	Core.staff_changed.emit()
	check(main.operations.actors.has("atendente") and main.operations.actors.atendente.visible, "atendente aparece no modo anterior à criação da empresa")
	Core.prog.staff_rec("atendente").off = true
	Core.staff_changed.emit()
	check(not main.operations.actors.atendente.visible, "folga oculta atendente")
	print("PRACTICAL_TEST ", "FAIL" if failed else "PASS")
	get_tree().quit(1 if failed else 0)
