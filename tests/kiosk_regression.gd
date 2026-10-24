extends Node
## Reproduz lotação, chegada real, postura, consumo e reutilização dos assentos.
var failed: = false

func check(ok: bool, message: String) -> void:
	print("KIOSK_TEST ", "OK " if ok else "FAIL ", message)
	failed = failed or not ok

func run(main) -> void:
	main.allow_faint = false
	main.guests.enabled = false
	var v = main.village
	v.enabled = false
	Core.paused = true
	Core.minutes = 10.0 * 60.0
	Core.speed_mult = 4.0
	Core.unlocked["kiosk_tables"] = true
	main.world.refresh_areas()
	v._on_slept(0)
	for g in v.walkers:
		g.set_process(false)
	for i in main.world.kiosk_spots.size():
		v.spawn_customer()
	var limit: = Time.get_ticks_msec() + 30000
	while Time.get_ticks_msec() < limit:
		var walking: = false
		for g in v.customers:
			g.timer = 10000.0
			if g.has_meta("choose"):
				g.set_meta("choose", 10000.0)
			walking = walking or g.state == "kwalk"
		if not walking:
			break
		await get_tree().process_frame
	var seen: = {}
	for g in v.customers:
		var pos: Vector3 = g.spot.pos
		check(not seen.has(pos), "assento exclusivo %s" % pos)
		seen[pos] = true
		check(g.state in ["kchoose", "kwait"], "chegou: %s pos=%s alvo=%s rota=%s" % [g.state, g.position, pos, g._route])
		check(g._state in ["Sit", "SitTalk"], "postura sentada: %s" % g._state)
		print("KIOSK_DIAG ", pos, " anim=", g._state, " spot=", g.spot)
	check(seen.size() == main.world.kiosk_spots.size(), "todos os lugares ocupados")
	var waiting = v.spawn_customer()
	check(waiting != null and waiting.state == "kqueue" and waiting.spot.is_empty(), "lotação cria espera fora das mesas")
	var served = v.customers[0]
	v._order(served, true)
	for ingredient in Core.stock:
		Core.stock[ingredient] = 100
	check(v.kiosk_serve() and served.state == "keat" and served.spot.busy, "consumo mantém assento reservado")
	var seat: Dictionary = served.spot
	v._leave(served)
	check(seat.busy, "saída não libera a cadeira antes de se afastar")
	limit = Time.get_ticks_msec() + 15000
	while Time.get_ticks_msec() < limit and waiting.state in ["kqueue", "kwalk"]:
		for g in v.customers:
			g.timer = 10000.0
			if g.has_meta("choose"):
				g.set_meta("choose", 10000.0)
		await get_tree().process_frame
	check(waiting.state == "kchoose", "cliente da fila chegou ao lugar liberado: %s" % waiting.state)
	check(int(seat.get("owner", -1)) == waiting.get_instance_id(), "reserva transferida somente ao novo cliente")
	if main.args.has("out"):
		main.hud.visible = false
		main.player.set_physics_process(false)
		main.player.position = Vector3(38, 3, -2)
		main.player.yaw = 0.0
		main.player.pitch = deg_to_rad(-28.0)
		main.player._apply_look()
		main.player.cam.current = true
		for i in 8:
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png(str(main.args.out))
	print("KIOSK_TEST ", "FAIL" if failed else "PASS")
	Core.quit_game(1 if failed else 0)
