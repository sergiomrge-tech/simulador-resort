extends Node
var failed := false
func check(ok: bool, message: String) -> void:
	failed = failed or not ok
	print("[terminal] ","ok " if ok else "FAIL ",message)
func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
func shot(label: String) -> void:
	if DisplayServer.get_name()=="headless": return
	await frames(6)
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://qa_shots"))
	check(get_viewport().get_texture().get_image().save_png("user://qa_shots/"+label+".png")==OK,"captura "+label)
func walk(main, destination: Vector3, steps: int = 180) -> void:
	for i in steps:
		var offset: Vector3 = destination-main.player.position
		offset.y=0
		if offset.length()<.15: break
		main.player.velocity=offset.normalized()*2.5+Vector3(0,-.5,0)
		main.player.move_and_slide()
		await frames(1)
	main.player.velocity=Vector3.ZERO
func run(main) -> void:
	Core.new_game()
	Core.paused=true
	Core.in_game=false
	Core.minutes=11*60
	main.allow_faint=false
	main.village.enabled=false
	main.guests.enabled=false
	main.player.set_physics_process(false)
	main.day.force_update()
	var ops=main.operations
	check(is_instance_valid(ops.computer),"computador presente antes de criar empresa")
	main.player.position=main.world.HOME_C
	main.hud.phone.close()
	main.hud.toggle_shop()
	check(not main.hud.phone.visible,"gestão não abre remotamente")
	main.player.position=main.world.kiosk_point(Vector3(1.60,.1,.65))
	main.player.cam.look_at(ops.computer.global_position+Vector3(0,.3,0))
	await frames(4)
	main.player.refresh_focus()
	check(main.player.focus!=null and main.player.focus.get_prompt().contains("Computador"),"mira alcança PC por dentro")
	main.player.interact()
	check(main.hud.phone.visible and main.hud.phone.app=="","E abre a gestão no computador")
	await shot("terminal_home")
	main.hud.phone.close()
	var cups=ops.find_children("CounterCup*","Node3D",true,false)
	check(cups.size()==6,"seis copos apoiados na bandeja")
	Core.configure_company("Praia do Sergio","praia")
	Core.company_changed.emit()
	check(get_tree().get_nodes_in_group("counter_promotions").size()==2,"promoções nas duas faces")
	for card in get_tree().get_nodes_in_group("counter_promotions"):
		check(card.text.contains("PROMOÇÕES") and card.text.contains(Core.fmt_money(Core.price_of("coco_gelado"))),"texto e preço real nas duas faces")
	main.player.position=main.world.kiosk_point(Vector3(.3,.3,-.15))
	main.player.cam.look_at(main.world.kiosk_point(Vector3(.20,1.4,2.0)))
	await shot("counter_inside")
	main.player.position=main.world.kiosk_point(Vector3(-.2,.5,4.1))
	main.player.cam.look_at(main.world.kiosk_point(Vector3(0,1.05,1.9)))
	await shot("counter_finish")
	var door=main.world.find_child("PlayerHomeDoor",true,false)
	check(door!=null and not door.opened,"porta da casa começa fechada")
	var origin: Vector3=door.global_position
	main.player.position=origin+Vector3(-.60,0,-.8)
	await walk(main,origin+Vector3(-.60,0,.8),50)
	check(main.player.position.z<origin.z,"porta fechada bloqueia passagem física")
	main.player.cam.look_at(origin+Vector3(-.575,1.1,0))
	await frames(4)
	main.player.refresh_focus()
	check(main.player.focus!=null and main.player.focus.get_prompt().contains("Porta"),"porta alcançável com E")
	main.player.interact()
	await get_tree().create_timer(.55).timeout
	check(door.opened and not door.collider.disabled,"E abre a folha e preserva colisão")
	door.check_exit()
	await walk(main,origin+Vector3(-.60,0,1.8))
	check(main.player.position.z>origin.z+1.55,"jogador atravessa a porta aberta e sai")
	door.check_exit()
	await get_tree().create_timer(.55).timeout
	check(not door.opened and not door.collider.disabled,"porta fecha após sair com vão livre")
	main.player.set_view(origin+Vector3(-.6,.1,2.4),0,-4)
	await shot("home_door_closed")
	print("TERMINAL_TEST FAIL" if failed else "TERMINAL_TEST PASS")
	get_tree().quit(1 if failed else 0)
