extends Node
var failed := false
func check(ok: bool,label: String) -> void:
	failed = failed or not ok
	print("[coast] ","ok " if ok else "FAIL ",label)
func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
func shot(main,label: String,pos: Vector3,look: Vector3) -> void:
	if DisplayServer.get_name()=="headless": return
	main.player.set_view(pos,0,0)
	main.player.cam.look_at(look,Vector3.UP)
	main.day.force_update()
	await frames(20)
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://shots/"+label+".png")
func run(main) -> void:
	Core.new_game()
	Core.paused = true
	Core.in_game = false
	Core.minutes = 11*60
	main.player.set_physics_process(false)
	main.village.enabled = false
	main.guests.enabled = false
	main.hud.root.visible = false
	var coast = main.get_node("CoastalLife")
	coast._update_visibility()
	check(coast.players.size()==4 and coast.ball.visible,"quatro pessoas jogam vôlei de dia")
	check(coast.yacht.visible and not coast.cruise.visible,"iate diurno sem cruzeiro sobreposto")
	var before: Vector3 = coast.yacht.position
	var ball_before: Vector3 = coast.ball.position
	coast._advance(.825)
	check(coast.yacht.position.x>before.x and coast.ball.position.distance_to(ball_before)>1,"iate navega e bola avança na jogada")
	check(absf(coast.ball.position.z)<.05 and coast.ball.position.y>2.5,"bola cruza acima da rede")
	coast._advance(.825)
	check(float(coast.players[1].get_meta("volley_weight"))>.9,"recebedor alcança a bola no contato")
	check(coast.yacht.position.z+5<main.world.SHORE_Z-20,"iate longe da faixa de banho e do cais")
	await shot(main,"beach_volleyball",Vector3(33,.10,-17),coast.court.position+Vector3(0,1.5,0))
	await shot(main,"beach_yacht",Vector3(38,.15,-29),coast.yacht.position+Vector3(0,2,0))
	var previous: float = coast.sea_time
	coast._process(3)
	check(coast.sea_time==previous,"pausa congela movimento ambiente")
	Core.minutes = 20*60
	coast._update_visibility()
	check(not coast.yacht.visible and coast.cruise.visible,"cruzeiro aparece à noite e iate recolhe")
	check(not coast.ball.visible and coast.players.all(func(g):return not g.visible),"quadra descansa à noite")
	check(coast.cruise.position.z+9<main.world.SHORE_Z-100,"cruzeiro no mar distante")
	var emissive := false
	for mi in coast.cruise.find_children("*","MeshInstance3D",true,false):
		for i in mi.mesh.get_surface_count():
			var material = mi.get_active_material(i)
			if material is StandardMaterial3D and material.emission_enabled and material.emission_energy_multiplier>1: emissive=true
	check(emissive,"janelas iluminadas no navio")
	await shot(main,"beach_cruise_night",Vector3(38,.15,-29),coast.cruise.position+Vector3(0,10,0))
	Core.minutes = 11*60
	Core.set_weather("rain")
	coast._update_visibility()
	check(not coast.ball.visible,"vôlei interrompe na chuva")
	print("COASTAL_TEST FAIL" if failed else "COASTAL_TEST PASS")
	get_tree().quit(1 if failed else 0)
