extends Node
var failed := false
func check(ok: bool, label: String) -> void:
	failed = failed or not ok
	print("[counter] ","ok " if ok else "FAIL ",label)
func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
func shot(label: String) -> void:
	if DisplayServer.get_name()=="headless": return
	await frames(10)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://shots/"+label+".png")
func aim(main, target: Interactable, degrees: float = 0) -> void:
	main.player.cam.look_at(target.global_position+Vector3(0,.20,0),Vector3.UP)
	main.player.cam.rotate_object_local(Vector3.UP,deg_to_rad(degrees))
	await frames(3)
	main.player.refresh_focus()
func run(main) -> void:
	Core.new_game()
	Core.configure_company("Quiosque da Praia","praia")
	Core.unlock_all()
	Core.paused = true
	Core.in_game = false
	Core.minutes = 11*60
	Core.money = 10000
	main.allow_faint = false
	main.player.set_physics_process(false)
	main.village.enabled = false
	main.guests.enabled = false
	main.operations.set_process(false)
	for role in Core.staff: Core.staff[role] = false
	for ingredient in Core.stock: Core.stock[ingredient] = 30
	Core.time_changed.emit(Core.day,Core.minutes)
	Core.money_changed.emit(Core.money)
	var world = main.world
	var ops = main.operations
	check((world.kiosk_root.global_basis*Vector3.BACK).dot(Vector3.FORWARD)>.99,"fachada voltada para praia e mar")
	for spot in world.kiosk_spots:
		check(spot.pos.z<world.KIOSK_C.z,"balcão e todas as mesas no lado da praia")
	var guests: Array = []
	for seat_index in [0,1]:
		var previous: Array = world.kiosk_spots.map(func(sp): return sp.busy)
		for i in world.kiosk_spots.size(): world.kiosk_spots[i].busy = i!=seat_index
		var guest = main.village.spawn_customer()
		for i in world.kiosk_spots.size():
			if i!=seat_index: world.kiosk_spots[i].busy = previous[i]
		check(guest!=null,"cliente no balcão "+str(seat_index+1))
		if guest==null: continue
		guest.go([])
		guest.position = guest.spot.pos
		guest.rotation.y = guest.spot.rot
		guest.play("Sitting_Idle_Loop")
		guest.set_meta("items",["coco_gelado"])
		guest.set_meta("delivered",0)
		main.village._order(guest)
		guests.append(guest)
	ops._process(0)
	await frames(5)
	for guest in guests:
		var target = guest.get_node("CustomerInteraction")
		main.player.position = ops.service_approach(guest)
		for angle in [-8.0,0.0,8.0]:
			await aim(main,target,angle)
			check(main.player.focus==target,"mira tolerante "+str(angle)+" graus · "+ops.order_number(guest))
		await aim(main,target)
		main.player.interact()
		check(bool(guest.get_meta("order_taken",false)),"E anota por dentro · "+ops.order_number(guest))
		check(Core.pickup_company_dish("coco_gelado"),"retirada para teste de entrega")
		await aim(main,target,6)
		if guest==guests[0]: await shot("counter_service_inside")
		main.player.interact()
		check(guest.state=="keat" and Core.company.carry=="","E entrega do lado interno sem sair · "+ops.order_number(guest))
	# A wall must still block the forgiving aim.
	var blocked = guests[0]
	blocked.state = "kwait"
	main.player.position = world.kiosk_point(Vector3(-.7,.1,-3.3))
	await aim(main,blocked.get_node("CustomerInteraction"))
	check(main.player.focus!=blocked.get_node("CustomerInteraction"),"não seleciona cliente através da parede traseira")
	blocked.state = "keat"
	# Restock through the actual refrigerator UI and callback.
	main.player.position = world.kiosk_point(Vector3(-1.2,.1,-.65))
	Core.company.ready = {}
	Core.company.carry = ""
	for ingredient in Economy.dish("coco_gelado").uses: Core.stock[ingredient] = 0
	ops.open_station("bebidas")
	await frames(3)
	var buy: Button = null
	for button in main.hud.phone.screen.find_children("*","Button",true,false):
		if button.text.begins_with("Repor 10"): buy = button; break
	check(buy!=null and not buy.disabled,"geladeira oferece reposição direta no celular")
	var quote: Dictionary = Core.company_restock_quote("coco_gelado",10)
	var money_before: int = Core.money
	await shot("counter_restock")
	if buy!=null: buy.pressed.emit()
	await frames(3)
	check(Core.money==money_before-int(quote.cost) and Core.company_available("coco_gelado")==10,"compra repõe 10 e cobra orçamento exato")
	check(main.hud.phone.app=="servico" and main.hud.phone.visible,"permanece na geladeira após comprar")
	check(not Core.restock_company_dish("coco_gelado",10),"não cobra novamente estoque já reposto")
	for ingredient in Economy.dish("coco_gelado").uses: Core.stock[ingredient] = 0
	Core.money = 0
	var stock_before: Dictionary = Core.stock.duplicate()
	main.hud.phone._service_restock("coco_gelado")
	check(Core.stock==stock_before and Core.money==0,"saldo insuficiente não faz compra parcial")
	Core.money = money_before
	main.player.position = world.HOME_C
	main.hud.phone._service_restock("coco_gelado")
	check(Core.stock==stock_before and Core.money==money_before,"reposição da estação exige estar na geladeira")
	main.player.position = world.kiosk_point(Vector3(-1.2,.1,-.65))
	main.hud.phone._service_restock("coco_gelado")
	main.hud.phone._service_action("coco_gelado","pickup")
	check(Core.company.carry=="coco_gelado" and Core.company_available("coco_gelado")==9,"pega produto imediatamente após repor")
	Core.return_company_dish()
	main.hud.phone.close()
	main.hud.root.visible = false
	main.player.set_view(world.kiosk_point(Vector3(1.5,.35,7)),195,-3)
	main.day.force_update()
	await shot("kiosk_beach_front")
	main.player.set_view(world.kiosk_point(Vector3(7,2.4,11)),218,-14)
	await shot("kiosk_beach_tables")

	# Old interior saves follow the rotated kiosk once; new saves keep their location.
	main.player.position = world.KIOSK_C+Vector3(-1.2,.1,-.65)
	main.player.rotation.y = .3
	Core.set_slot(Core.slot)
	Core.save_game()
	var saved: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(Core.SAVE_PATH))
	saved.player.erase("kiosk_facing")
	var file := FileAccess.open(Core.SAVE_PATH,FileAccess.WRITE)
	file.store_string(JSON.stringify(saved))
	file.close()
	main._on_start_load(Core.slot)
	var expected: Vector3 = world.kiosk_point(Vector3(-1.2,.1,-.65))
	check(Vector2(main.player.position.x,main.player.position.z).distance_to(Vector2(expected.x,expected.z))<.01,"save antigo dentro do quiosque acompanha a rotação")
	Core.save_game()
	var migrated_position: Vector3 = main.player.position
	main._on_start_load(Core.slot)
	check(Vector2(main.player.position.x,main.player.position.z).distance_to(Vector2(migrated_position.x,migrated_position.z))<.01,"nova gravação não gira o jogador novamente")
	print("COUNTER_TEST FAIL" if failed else "COUNTER_TEST PASS")
	get_tree().quit(1 if failed else 0)
