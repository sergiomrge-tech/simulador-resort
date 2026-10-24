extends Node
var failed := false
func check(ok: bool, label: String) -> void:
	failed = failed or not ok
	print("[counter-first] ","ok " if ok else "FAIL ",label)
func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
func walk_until(village, guest, state: String) -> void:
	guest.set_process(false)
	for i in 2200:
		if guest.state==state: break
		guest._process(.05)
		village._kiosk_tick(0)
		if i%12==0: await frames(1)
	check(guest.state==state,"percurso real até "+state+" · "+str(guest.position))
func shot(main, label: String) -> void:
	if DisplayServer.get_name()=="headless": return
	main.hud._update_orders()
	main.hud._update_objective()
	Core.time_changed.emit(Core.day,Core.minutes)
	Core.money_changed.emit(Core.money)
	await frames(8)
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://qa_shots"))
	check(get_viewport().get_texture().get_image().save_png("user://qa_shots/"+label+".png")==OK,"captura "+label)
	print("COUNTER_FIRST_SHOT ",ProjectSettings.globalize_path("user://qa_shots/"+label+".png"))
func run(main) -> void:
	Core.new_game()
	Core.configure_company("Quiosque da Praia","praia")
	Core.paused=true
	Core.in_game=false
	Core.minutes=11*60
	Core.money=100000
	Core.buy_expansion("kiosk_tables")
	main.allow_faint=false
	main.player.set_physics_process(false)
	main.village.enabled=false
	main.guests.enabled=false
	main.operations.set_process(false)
	for role in Core.staff: Core.staff[role]=false
	for ingredient in Core.stock: Core.stock[ingredient]=100
	check(not Core.kiosk_accepting_customers(),"novo quiosque começa fechado")
	var Rules=load("res://scripts/company_rules.gd")
	check(not Rules.sanitize({"created":true,"kiosk_open":true}).kiosk_open,"save anterior exige abrir uma vez")
	check(Rules.sanitize({"opening_version":1,"kiosk_open":true}).kiosk_open,"abertura deliberada persiste no save atual")
	var village=main.village
	village.enabled=true
	village.kiosk_spawn_in=0
	village._kiosk_tick(.01)
	check(village.customers.is_empty(),"sem chegadas antes de abrir")
	village.enabled=false
	Core.set_kiosk_open(true)
	check(Core.kiosk_accepting_customers(),"abertura manual libera chegadas no horário")
	var occupancy: Array=main.world.kiosk_spots.map(func(s):return s.busy)
	for i in main.world.kiosk_spots.size(): main.world.kiosk_spots[i].busy=i!=2
	var g=village.spawn_customer()
	for i in main.world.kiosk_spots.size():
		if i!=2: main.world.kiosk_spots[i].busy=occupancy[i]
	check(g!=null and g.has_meta("dining_spot") and g.get_meta("dining_spot").get("table",false),"mesa reservada sem sentar antes de pedir")
	if g==null: Core.quit_game(1); return
	g.set_meta("items",["coco_gelado","coco_gelado"])
	g.set_meta("vip",false)
	g.position=main.world.kiosk_point(Vector3(-3.3,.1,4.5))
	g.go([g.spot.approach])
	await walk_until(village,g,"kchoose")
	check(g._state not in ["Sit","SitTalk"],"espera de pé no balcão")
	g.set_meta("choose",0)
	village._kiosk_tick(.01)
	main.operations._process(0)
	await frames(3)
	var target=g.get_node("CustomerInteraction")
	main.player.position=main.operations.service_approach(g)
	main.player.cam.look_at(target.global_position+Vector3(0,.20,0),Vector3.UP)
	await frames(3)
	main.player.refresh_focus()
	check(main.player.focus==target,"mira no cliente de pé pelo lado interno do balcão")
	main.player.interact()
	check(bool(g.get_meta("order_taken",false)),"E anota o pedido no balcão")
	var second=village.spawn_customer()
	var third=village.spawn_customer()
	check(main.operations.order_number(g)!="#00" and main.operations.order_number(g)!=main.operations.order_number(second),"pedidos possuem números distintos e válidos no balcão")
	check(second!=null and third!=null and third.state=="kcounter_queue","fila aguarda quando as duas retiradas estão ocupadas")
	await shot(main,"counter_first_waiting")
	var stock_before: int=Core.stock.coco
	for i in 2:
		check(Core.pickup_company_dish("coco_gelado"),"retira produto pronto "+str(i+1))
		main.player.refresh_focus()
		main.player.interact()
		check(g.state==("kwait" if i==0 else "kto_table"),"só parte para a mesa após receber o pedido inteiro")
	check(Core.stock.coco==stock_before-2 and Core.company.carry=="","estoque descontado uma vez por item")
	check(g.has_node("CustomerTray") and not g._eating,"transporta os produtos sem consumir em pé")
	var billed: int=Core.company.receivables.size()
	var stock_after: Dictionary=Core.stock.duplicate()
	await walk_until(village,g,"keat")
	check(bool(g.spot.get("table",false)) and g._eating,"senta e consome apenas depois da retirada")
	check(not g.has_meta("counter_slot"),"libera a retirada ao se afastar do balcão")
	check(village.served_dishes(g).size()==2,"produtos acompanham o cliente até a mesa")
	check(Core.stock==stock_after and Core.company.receivables.size()==billed,"trajeto não duplica estoque nem cobrança")
	main.player.set_view(g.position+Vector3(0,.7,2.3),0,0)
	main.player.cam.look_at(g.position+Vector3(0,1,0),Vector3.UP)
	await shot(main,"counter_first_dining")
	if third!=null:
		await walk_until(village,third,"kchoose")
		check(int(third.get_meta("counter_slot",-1))==0,"próximo da fila ocupa a retirada liberada")
		village._leave(third)
		third.go([])
		village._kiosk_tick(0)
	Core.set_kiosk_open(false)
	var count: int=village.customers.size()
	village.enabled=true
	village.kiosk_spawn_in=0
	village._kiosk_tick(.01)
	check(village.customers.size()==count,"fechar bloqueia novas chegadas sem expulsar atendidos")
	village.enabled=false
	Core.set_kiosk_open(true)
	Core.sleep()
	check(not Core.company.kiosk_open,"cada novo dia começa fechado")
	print("COUNTER_FIRST_TEST FAIL" if failed else "COUNTER_FIRST_TEST PASS")
	Core.quit_game(1 if failed else 0)
