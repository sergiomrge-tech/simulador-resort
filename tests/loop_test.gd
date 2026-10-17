extends Node
## Teste automático do ciclo completo:
## chegada -> fila -> check-in (pelo raycast do jogador) -> quarto -> piscina/bar -> check-out
## -> quarto sujo -> limpar cama/toalhas/lixo (raycast) -> dinheiro + estrelas -> comprar rede -> save/load
## -> venda no quiosque (raycast no balcão) -> dormir na cama de casa (próximo dia 06:30 + save).

var main
var log_lines := []
var failed := false

func _p(s: String) -> void:
	print("[loop] ", s)

func fail(s: String) -> void:
	failed = true
	print("LOOP_TEST FAIL: ", s)

func check(cond: bool, s: String) -> bool:
	if cond:
		_p("ok  - " + s)
	else:
		fail(s)
	return cond

func wait_until(cond: Callable, timeout_s: float) -> bool:
	var t := 0.0
	while not cond.call():
		await get_tree().process_frame
		t += get_process_delta_time()
		if t > timeout_s:
			return false
	return true

func frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

func aim(pos: Vector3, yaw: float, pitch: float) -> String:
	main.player.set_view(pos, yaw, pitch)
	await frames(3)
	var f = main.player.focus
	return f.get_prompt() if f else ""

func run(m) -> void:
	main = m
	var watchdog := get_tree().create_timer(230.0)
	watchdog.timeout.connect(func():
		print("LOOP_TEST FAIL: watchdog timeout")
		get_tree().quit(1))
	Quality.language = "pt"
	Quality.apply_language()
	main.allow_faint = false
	await frames(5)
	check(main.world.kiosk_counter != null and main.world.bed != null, "vila carregada (quiosque e cama)")
	check(main.village.walkers.size() > 0, "moradores na vila: %d" % main.village.walkers.size())
	check(Core.minutes == Core.WAKE_MIN, "novo jogo começa às 06:30")
	check(main.player.global_position.distance_to(main.world.home_wake) < 1.5, "herói acorda em casa")
	var g = main.guests
	g.enabled = false
	Core.speed_mult = 30.0
	var money0 := Core.money
	var stars0 := Core.stars()
	_p("inicio: dinheiro=%d estrelas=%.2f" % [money0, stars0])
	# 1) chegada e fila
	var guest = g.spawn_guest()
	check(await wait_until(func(): return guest.state == "queue", 20.0), "hóspede chegou à fila")
	# 2) check-in pelo balcão (raycast real do jogador)
	var pr: String = await aim(Vector3(0, 0.15, 14.2), 180.0, -28.0)
	check(pr.begins_with("Fazer check-in"), "prompt do balcão: '%s'" % pr)
	main.player.interact()
	check(Core.rooms[0].state == "occupied", "bangalô 1 ocupado")
	var rate := Core.money - money0
	check(rate > 0, "diária recebida: %d" % rate)
	check(guest.state == "to_room", "hóspede indo para o quarto")
	# 3) estadia completa até o check-out
	var visited := []
	var ok: bool = await wait_until(func():
		if guest.state == "activity" and not (guest.spot.anim in visited):
			visited.append(guest.spot.anim)
		return guest.state == "leaving", 90.0)
	check(ok, "hóspede fez check-out (atividades: %s)" % [visited])
	check(Core.bar_sales_total > 0, "vendas no bar: R$ %d" % Core.bar_sales_total)
	Core.force_flush_bar()
	check(Core.rooms[0].state == "dirty", "bangalô 1 ficou sujo")
	check(Core.guests_served == 1, "hóspedes atendidos = 1")
	check(Core.stars() > stars0, "estrelas subiram: %.2f -> %.2f" % [stars0, Core.stars()])
	# 4) limpeza por interação
	var c: Vector3 = Vector3(main.world.BUNG_X[0], 0, main.world.BUNG_Z)
	var aims := [["cama", Vector3(c.x - 1.2, 0.3, c.z + 2.4), 0.0, -38.0],
		["toalhas", Vector3(c.x + 0.4, 0.3, c.z + 0.6), 0.0, -48.0],
		["lixo", Vector3(c.x + 1.3, 0.3, c.z - 0.6), 180.0, -48.0]]
	for a in aims:
		var p2: String = await aim(a[1], a[2], a[3])
		if check(p2 != "", "prompt de limpeza '%s': '%s'" % [a[0], p2]):
			main.player.interact()
		else:
			Core.clean_item(0, a[0])
		check(not Core.rooms[0].dirty[a[0]], "%s limpo" % a[0])
	check(Core.rooms[0].state == "free", "bangalô 1 pronto de novo")
	check(main.world.room_nodes[0].clean.visible, "cama arrumada visível")
	# 5) dinheiro + compra de rede
	check(Core.money > money0, "dinheiro aumentou: %d -> %d" % [money0, Core.money])
	var m_before := Core.money
	check(Core.buy_rede(), "comprou rede")
	check(Core.redes == 1 and main.world.rede_nodes[0].visible, "rede instalada e visível")
	check(Core.money == m_before - Core.REDE_PRICE, "preço da rede descontado")
	# 6) sem quarto livre
	Core.occupy_room(0, 99)
	Core.occupy_room(1, 98)
	var g2 = g.spawn_guest()
	await wait_until(func(): return g2.state == "queue", 20.0)
	var pr2: String = await aim(Vector3(0, 0.15, 14.2), 180.0, -28.0)
	check(pr2.begins_with("Sem bangalô"), "sem quarto livre: '%s'" % pr2)
	# 7) save / load
	Core.rooms[0].state = "free"
	Core.rooms[1].state = "free"
	Core.save_game()
	var saved_money := Core.money
	Core.money = 1
	Core.redes = 0
	check(Core.load_game(), "save carregado")
	check(Core.money == saved_money and Core.redes == 1, "save preservou dinheiro (%d) e redes (%d)" % [Core.money, Core.redes])
	# 8) quiosque: cliente chega, herói serve pelo balcão
	Core.speed_mult = 4.0
	Core.minutes = 8.5 * 60.0
	main.village.enabled = false
	main.village._on_slept(0)
	var kc = main.village.spawn_customer()
	check(kc != null, "cliente do quiosque criado")
	check(kc != null and await wait_until(func(): return kc.state == "kwait", 30.0), "cliente esperando no balcão")
	var km0 := Core.money
	var kp: String = await aim(main.world.KIOSK_C + Vector3(0, 0.12, 0.4), 180.0, -32.0)
	if check(kp.begins_with("Servir"), "prompt do quiosque: '%s'" % kp):
		main.player.interact()
	check(Core.kiosk_sales_count == 1 and Core.money > km0, "venda no quiosque: %s" % Core.fmt_money(Core.money - km0, true))
	# 9) dormir em casa depois das 20:00
	Core.speed_mult = 1.0
	Core.minutes = 15.0 * 60.0
	var bed_from := Vector3(main.world.HOME_C.x - 2.2, 0.2, main.world.HOME_C.z + 0.9)
	var bp0: String = await aim(bed_from, 0.0, -30.0)
	check(bp0.begins_with("Sua cama"), "cama antes das 20h: '%s'" % bp0)
	Core.minutes = 21.0 * 60.0
	var day0 := Core.day
	var bp: String = await aim(bed_from, 0.0, -30.0)
	if check(bp.begins_with("Dormir"), "prompt da cama: '%s'" % bp):
		main.player.interact()
	check(await wait_until(func(): return Core.day == day0 + 1, 8.0), "dormiu: dia %d -> %d" % [day0, Core.day])
	await wait_until(func(): return not main._sleeping, 5.0)
	check(absf(Core.minutes - Core.WAKE_MIN) < 30.0, "acordou ~06:30 (%s)" % Core.clock_text())
	check(main.player.global_position.distance_to(main.world.home_wake) < 1.5, "acordou em casa")
	var sm: Dictionary = Core.slot_summary(0) if false else {}
	var f := FileAccess.open(Core.SAVE_PATH, FileAccess.READ)
	var saved = JSON.parse_string(f.get_as_text()) if f else {}
	check(typeof(saved) == TYPE_DICTIONARY and int(saved.get("day", 0)) == Core.day and saved.has("player"), "save após dormir (dia %s, posição salva)" % str(saved.get("day", "?")))
	Core.delete_save()
	print("LOOP_TEST %s  dinheiro=%d estrelas=%.2f bar=%d" % ["FAIL" if failed else "PASS", Core.money, Core.stars(), Core.bar_sales_total])
	get_tree().quit(1 if failed else 0)
