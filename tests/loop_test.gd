extends Node





var main
var log_lines: = []
var failed: = false

func _p(s: String) -> void :
	print("[loop] ", s)

func fail(s: String) -> void :
	failed = true
	print("LOOP_TEST FAIL: ", s)

func check(cond: bool, s: String) -> bool:
	if cond:
		_p("ok  - " + s)
	else:
		fail(s)
	return cond

func wait_until(cond: Callable, timeout_s: float) -> bool:
	var t: = 0.0
	while not cond.call():
		await get_tree().process_frame
		t += get_process_delta_time()
		if t > timeout_s:
			return false
	return true

func frames(n: int) -> void :
	for i in n:
		await get_tree().physics_frame

func aim(pos: Vector3, yaw: float, pitch: float) -> String:
	main.player.set_view(pos, yaw, pitch)
	await frames(3)
	var f = main.player.focus
	return f.get_prompt() if f else ""

## v0.7: começa só com o quiosque, compra as expansões em ordem e vê cada área aparecer no mundo.
## No fim deixa o estado igual ao jogo antigo (2 bangalôs, despensa cheia) para o resto do teste.
func career_test() -> void :
	var w = main.world
	check(Core.rooms.is_empty() and not Core.has("pousada"), "novo jogo começa só com o quiosque")
	check(Core.money == Economy.START_MONEY, "dinheiro inicial %s" % Core.fmt_money(Core.money))
	check( not w.areas.pousada.visible and w.lots.pousada.visible, "pousada é um lote à venda")
	check( not w.areas.bar.visible and w.lots.bar.visible, "bar é um lote à venda")
	check( not w.areas.pool.visible and w.lots.pool.visible, "piscina é um lote à venda")
	check( not w.areas.kiosk_tables.visible and not w.areas.neon.visible, "quiosque começa simples")
	check(Core.kiosk_menu() == ["coco_gelado", "suco"], "cardápio inicial: coco gelado e suco")
	check(Core.expansion_state("bar")[0] == "locked", "bar bloqueado no início")
	check( not main.guests.bartender.visible, "barman ainda não existe")
	check(Core.expansion_state("kiosk_tables")[0] == "money", "mesas exigem juntar dinheiro no 1º dia")
	Core.money = 200
	check(Core.expansion_state("kiosk_tables")[0] == "ready", "mesas já dá para comprar")
	check(Core.buy_expansion("kiosk_tables"), "comprou mesas e guarda-sóis")
	await frames(2)
	check(w.areas.kiosk_tables.visible, "mesas apareceram no quiosque")
	check( not Core.buy_expansion("pousada"), "pousada recusada sem requisitos")
	check(Core.expansion_state("grill")[0] == "locked", "chapa exige nota mínima")
	Core.ratings = [5.0, 5.0, 5.0]
	Core.money = 20000
	for id in Economy.EXPANSION_ORDER:
		if id == "pool":
			check(Core.expansion_state("pool")[0] == "locked", "piscina exige 2 bangalôs")
			check(Core.build_bungalow(), "segundo bangalô construído")
		if not Core.has(id):
			check(Core.buy_expansion(id), "comprou %s" % id)
	await frames(2)
	for id in ["bar", "pousada", "pool", "neon", "grill"]:
		check(w.areas[id].visible and (not w.lots.has(id) or not w.lots[id].visible), "área %s visível" % id)
	check(main.guests.bartender.visible, "barman no bar")
	check(Core.kiosk_menu().size() == 4, "cardápio completo no quiosque")
	check(Core.rooms.size() == 2 and w.room_nodes.size() == 2, "dois bangalôs no mundo")
	var visitor = main.guests.spawn_bar_visitor()
	check(visitor != null and visitor.has_meta("visitor"), "banhista indo ao bar")
	main.guests.guests.erase(visitor)
	visitor.spot.busy = false
	visitor.queue_free()
	Core.save_game()
	Core.unlocked = {}
	check(Core.load_game() and Core.has("pool") and Core.has("kiosk_tables"), "save guardou as expansões")
	# volta ao estado do jogo antigo para o resto do teste
	Core.money = 300
	Core.ratings = [3.0, 3.0, 3.0]
	Core.stock = {"coco": 6, "frutas": 10, "cachaca": 6, "gelo": 10, "peixe": 6, "pao": 6}
	Core.stock_changed.emit()
	Core.ledger_today = []
	Core.day_income = 0
	Core.day_expense = 0

## v0.8: cliente VIP de ponta a ponta, ônibus de turistas (rush), fechamento do quiosque e evento "calor".
func vip_rush_test() -> void :
	var v = main.village
	v.enabled = false
	Core.speed_mult = 8.0
	Core.minutes = 12.0 * 60.0
	Core.day_event = ""
	v._on_slept(0)
	# --- VIP: o famoso entra no álbum e paga gorjeta generosa
	Core.album = []
	for k in Core.stock.keys():
		Core.stock[k] = 30   # o prato é sorteado: precisa de estoque de tudo
	Core.stock_changed.emit()
	var vc = v.spawn_customer()
	if not check(vc != null, "VIP: cliente criado"):
		return
	vc.set_meta("vip", true)
	vc.set_meta("vip_id", "kai")
	var m0: = Core.money
	check( await wait_until( func(): return vc.state == "kwait", 40.0), "VIP: esperando no balcão")
	check(v.kiosk_serve(), "VIP: pedido servido")
	check(Core.album.has("kai"), "VIP: Kai Onda entrou no álbum")
	check(Core.money - m0 > 10, "VIP: pagou o pedido e a gorjeta (%d)" % (Core.money - m0))
	# --- rush: o ônibus manda 4 clientes seguidos, sem estourar as vagas do quiosque
	v._on_slept(0)
	for k in Core.stock.keys():
		Core.stock[k] = 30   # o rush precisa de estoque para todos os pratos
	Core.stock_changed.emit()
	v.enabled = true
	v.rush_left = 4
	v.rush_done = true
	v.kiosk_spawn_in = 0.5
	Core.minutes = 12.0 * 60.0
	var peak: = 0
	var t: = 0.0
	while t < 40.0 and v.customers.size() < 4:
		await get_tree().process_frame
		t += get_process_delta_time()
		peak = maxi(peak, v.customers.size())
	check(v.customers.size() >= 3, "rush: %d clientes chegaram em %.0fs" % [v.customers.size(), t])
	check(v.customers.size() <= main.world.kiosk_spots.size(), "rush respeita as vagas do quiosque (%d de %d)" % [v.customers.size(), main.world.kiosk_spots.size()])
	var served0: int = v.served_today
	v.enabled = false
	for k in 12:
		var up = await wait_until( func(): return not v.waiting_customers().is_empty(), 25.0)
		if not up:
			var st: = []
			for c in v.customers:
				st.append("%s/%.1f/%s" % [c.state, float(c.timer), str(c.is_moving())])
			_p("rush: sem cliente esperando (k=%d) estados=%s min=%.0f open=%s" % [k, st, Core.minutes, str(v.kiosk_open())])
			break
		v.kiosk_serve()
	check(v.served_today - served0 >= 3, "rush: atendeu %d clientes seguidos (combo x%d)" % [v.served_today - served0, v.combo])
	# --- fechamento: depois da hora quem está no quiosque vai embora
	Core.minutes = Core.kiosk_close_min() + 5.0
	await frames(6)
	var stuck: = 0
	for c in v.customers:
		if not (c.state in ["kleave"]):
			stuck += 1
	check(stuck == 0, "quiosque fechado: ninguém fica parado (%d presos)" % stuck)
	# --- calor: mais demanda; lua: mais movimento à noite
	Core.day_event = "calor"
	var d_calor: float = Core.demand_factor()
	Core.day_event = ""
	var d_base: float = Core.demand_factor()
	check(d_calor > d_base * 1.2, "evento calor aumenta a demanda: %.2f -> %.2f" % [d_base, d_calor])
	v._on_slept(0)
	Core.speed_mult = 30.0
	Core.minutes = 8.5 * 60.0

func mechanics_test() -> void :
	var d0: = Core.day
	var money0: = Core.money
	var stock0: = Core.stock.duplicate()
	# fornecedores: preço oscila e contrato dá desconto
	Core.supply_mult["coco"] = 1.4
	var hi: = Core.supply_total("coco", Economy.PACK)
	Core.supply_mult["coco"] = 0.8
	var lo: = Core.supply_total("coco", Economy.PACK)
	check(hi > lo and lo >= 1, "preço do fornecedor oscila: %d > %d" % [hi, lo])
	Core.supply_mult["coco"] = 1.4
	var m_c: = Core.money
	check(Core.buy_contract("coco"), "assinou contrato de coco")
	check(Core.money == m_c - Economy.CONTRACT_FEE, "taxa do contrato cobrada")
	check(Core.supply_total("coco", Economy.PACK) < Economy.supply_cost("coco") * Economy.PACK, "contrato nunca paga mais que o normal")
	for i in Economy.CONTRACT_DAYS:
		Core.roll_supply_prices()
	check(not Core.contracts.has("coco"), "contrato expira depois de %d dias" % Economy.CONTRACT_DAYS)
	Core.supply_mult = {}
	# festas do calendário
	check(Core.pick_event(5) not in ["quermesse", "junina", "show_dj"], "antes do dia 8 não tem festa")
	check(Core.pick_event(9) == "quermesse" and Core.pick_event(11) == "junina" and Core.pick_event(13) == "show_dj", "calendário de festas")
	Core.day_event = ""
	Core.prep_active = false
	var f_base: = Core.demand_factor()
	Core.day_event = "quermesse"
	var f_party: = Core.demand_factor()
	Core.money = 1000
	check(Core.buy_prep(), "decorou a festa do dia")
	var f_deco: = Core.demand_factor()
	check(f_party > f_base * 1.2 and f_deco > f_party, "festa atrai clientes (%.2f < %.2f < %.2f)" % [f_base, f_party, f_deco])
	Core.day_event = "tempestade"
	Core.prep_active = false
	check(Core.demand_factor() < f_base * 0.5, "tempestade espanta clientes")
	check(Core.beach_share() < 0.4, "tempestade esvazia a praia")
	# tempestade: sem preparativos o estoque se perde; com preparativos, não
	for k in Core.stock.keys():
		Core.stock[k] = 20
	Core.forecast_next = "tempestade"
	Core.forecast_set = true
	Core.prep_paid = false
	Core.roll_day_event()
	check(int(Core.stock["coco"]) < 20 and Core.day_event == "tempestade", "tempestade sem preparativos estraga estoque (%d)" % int(Core.stock["coco"]))
	check(Core.weather == "rain", "tempestade traz chuva")
	for k in Core.stock.keys():
		Core.stock[k] = 20
	Core.forecast_next = "tempestade"
	Core.forecast_set = true
	Core.prep_active = false
	var m_p: = Core.money
	check(Core.buy_prep(), "pagou os preparativos da tempestade")
	check(Core.money == m_p - Economy.STORM_PREP_COST, "custo dos preparativos")
	Core.roll_day_event()
	check(int(Core.stock["coco"]) == 20 and Core.prep_active, "preparativos protegem o estoque")
	Core.set_weather("sun")
	# passeios: guia + horário certo = renda; mar bravo cancela
	var had: = Core.has("passeios")
	Core.unlocked["passeios"] = true
	Core.staff["guia"] = true
	Core.day_event = ""
	Core.tours_done = {}
	Core.minutes = float(Economy.TOURS.snorkel.at) + 5.0
	var m_t: = Core.money
	Core._check_tours()
	check(Core.tours_done.has("snorkel") and Core.money > m_t, "passeio de snorkel rendeu %d" % (Core.money - m_t))
	var m_t2: = Core.money
	Core._check_tours()
	check(Core.money == m_t2, "o mesmo passeio não roda duas vezes")
	Core.day_event = "mare"
	check(Core.run_tour("barco") == 0 and Core.tours_done.has("barco"), "maré alta cancela o passeio de barco")
	check(Core.run_tour("farol") > 0, "trilha ao farol acontece na maré alta")
	Core.staff["guia"] = false
	if not had:
		Core.unlocked.erase("passeios")
	Core.tours_done = {}
	Core.day_event = ""
	Core.prep_active = false
	Core.prep_paid = false
	Core.forecast_next = ""
	Core.forecast_set = false
	Core.day = d0
	Core.money = money0
	Core.stock = stock0

func run(m) -> void :
	main = m
	var watchdog: = get_tree().create_timer(230.0)
	watchdog.timeout.connect( func():
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
	await career_test()
	var g = main.guests
	g.enabled = false
	main.village.enabled = false
	Core.speed_mult = 30.0
	var money0: = Core.money
	var stars0: = Core.stars()
	_p("inicio: dinheiro=%d estrelas=%.2f" % [money0, stars0])

	var guest = g.spawn_guest()
	check( await wait_until( func(): return guest.state == "queue", 20.0), "hóspede chegou à fila")

	var pr: String = await aim(Vector3(0, 0.15, 14.2), 180.0, -28.0)
	check(pr.begins_with("Fazer check-in"), "prompt do balcão: '%s'" % pr)
	main.player.interact()
	check(Core.rooms[0].state == "occupied", "bangalô 1 ocupado")
	var rate: = Core.money - money0
	check(rate > 0, "diária recebida: %d" % rate)
	check(guest.state == "to_room", "hóspede indo para o quarto")

	var visited: = []
	var ok: bool = await wait_until( func():
		if guest.state == "activity" and not (guest.spot.anim in visited):
			visited.append(guest.spot.anim)
		return guest.state == "leaving", 90.0)
	check(ok, "hóspede fez check-out (atividades: %s)" % [visited])
	check(Core.bar_sales_total > 0, "vendas no bar: R$ %d" % Core.bar_sales_total)
	Core.force_flush_bar()
	check(Core.rooms[0].state == "dirty", "bangalô 1 ficou sujo")
	check(Core.guests_served == 1, "hóspedes atendidos = 1")
	check(Core.stars() > stars0, "estrelas subiram: %.2f -> %.2f" % [stars0, Core.stars()])

	var c: Vector3 = Vector3(main.world.BUNG_X[0], 0, main.world.BUNG_Z)
	var aims: = [["cama", Vector3(c.x - 1.2, 0.3, c.z + 2.4), 0.0, -38.0], 
		["toalhas", Vector3(c.x + 0.4, 0.3, c.z + 0.6), 0.0, -48.0], 
		["lixo", Vector3(c.x + 1.3, 0.3, c.z - 0.6), 180.0, -48.0]]
	for a in aims:
		var p2: String = await aim(a[1], a[2], a[3])
		if check(p2 != "", "prompt de limpeza '%s': '%s'" % [a[0], p2]):
			main.player.interact()
		else:
			Core.clean_item(0, a[0])
		check( not Core.rooms[0].dirty[a[0]], "%s limpo" % a[0])
	check(Core.rooms[0].state == "free", "bangalô 1 pronto de novo")
	check(main.world.room_nodes[0].clean.visible, "cama arrumada visível")

	check(Core.money > money0, "dinheiro aumentou: %d -> %d" % [money0, Core.money])
	var m_before: = Core.money
	check(Core.buy_rede(), "comprou rede")
	check(Core.redes == 1 and main.world.rede_nodes[0].visible, "rede instalada e visível")
	check(Core.money == m_before - Core.REDE_PRICE, "preço da rede descontado")

	Core.occupy_room(0, 99)
	Core.occupy_room(1, 98)
	var g2 = g.spawn_guest()
	await wait_until( func(): return g2.state == "queue", 20.0)
	var pr2: String = await aim(Vector3(0, 0.15, 14.2), 180.0, -28.0)
	check(pr2.begins_with("Sem bangalô"), "sem quarto livre: '%s'" % pr2)

	Core.rooms[0].state = "free"
	Core.rooms[1].state = "free"
	Core.save_game()
	var saved_money: = Core.money
	Core.money = 1
	Core.redes = 0
	check(Core.load_game(), "save carregado")
	check(Core.money == saved_money and Core.redes == 1, "save preservou dinheiro (%d) e redes (%d)" % [Core.money, Core.redes])

	Core.speed_mult = 4.0
	Core.minutes = 8.5 * 60.0
	main.village.enabled = false
	main.village._on_slept(0)
	var kc = main.village.spawn_customer()
	check(kc != null, "cliente do quiosque criado")
	check(kc != null and await wait_until( func(): return kc.state == "kwait", 30.0), "cliente esperando no balcão")
	var km0: = Core.money
	var kp: String = await aim(main.world.KIOSK_C + Vector3(0, 0.12, 0.4), 180.0, -32.0)
	if check(kp.begins_with("Preparar"), "prompt do quiosque: '%s'" % kp):
		main.player.interact()
		check(not main.village.prep.is_empty(), "preparo começou ao apertar E")
		var tries: = 0
		while kc.state == "kwait" and tries < 8:
			if main.village.prep.is_empty():
				main.village.kiosk_action()
			main.village.prep_advance(30.0)
			tries += 1
	check(Core.kiosk_sales_count >= 1 and Core.money > km0, "venda no quiosque: %s (%d itens)" % [Core.fmt_money(Core.money - km0, true), Core.kiosk_sales_count])
	check(kc.state == "keat", "cliente atendido fica comendo/bebendo")
	check(main.village.served_today == 1, "contador de atendimentos do dia: %d" % main.village.served_today)
	check(main.village.daily_goal() >= 8, "meta diária: %d clientes" % main.village.daily_goal())
	check(main.village.combo >= 1, "combo após atendimento rápido: x%d" % main.village.combo)

	# v0.7.5: preço ajustável, estoque que estraga, freezer e eventos do dia
	var base_p: = int(Economy.dish("coco_gelado").price)
	check(Core.price_of("coco_gelado") == base_p, "preço padrão do coco: %d" % base_p)
	Core.set_price_tier("coco_gelado", 4)
	check(Core.price_of("coco_gelado") == int(round(base_p * 1.5)), "preço ×1,5 do coco: %d" % Core.price_of("coco_gelado"))
	check(Core.demand_factor() < 1.0, "preço alto reduz a demanda: %.2f" % Core.demand_factor())
	Core.set_price_tier("coco_gelado", 0)
	check(Core.demand_factor() > 1.0 and Core.price_rating_adjust() >= 0.0, "preço baixo atrai mais clientes: %.2f" % Core.demand_factor())
	Core.set_price_tier("coco_gelado", 2)
	Core.stock["gelo"] = 20
	Core.stock["peixe"] = 10
	Core.freezer = false
	Core.spoil_stock()
	var gelo1: int = int(Core.stock["gelo"])
	check(gelo1 < 20 and gelo1 >= 12, "gelo estraga à noite: 20 -> %d" % gelo1)
	Core.stock["gelo"] = 20
	Core.freezer = true
	Core.spoil_stock()
	check(int(Core.stock["gelo"]) > gelo1, "freezer reduz a perda: 20 -> %d" % int(Core.stock["gelo"]))
	Core.freezer = false
	var ev_seen: = {}
	var d0: = Core.day
	Core.day = 5
	for i in 60:
		Core.roll_day_event()
		ev_seen[Core.day_event] = true
	Core.day = d0
	Core.day_event = ""
	check(ev_seen.has("calor") and ev_seen.has("lua") and ev_seen.has(""), "eventos do dia sorteados: %s" % str(ev_seen.keys()))
	check(ev_seen.has("mare") and ev_seen.has("tempestade"), "maré alta e tempestade sorteadas: %s" % str(ev_seen.keys()))
	Core.set_weather("sun")
	Core.forecast_set = false
	Core.prep_paid = false
	Core.prep_active = false
	Core.supply_mult = {}
	mechanics_test()
	Core.set_weather("sun")
	Core.stock = Economy.START_STOCK.duplicate()
	Core.stock["gelo"] = 18
	Core.stock["peixe"] = 10

	Core.speed_mult = 1.0
	Core.minutes = 15.0 * 60.0
	var bed_from: = Vector3(main.world.HOME_C.x - 2.2, 0.2, main.world.HOME_C.z + 0.9)
	var bp0: String = await aim(bed_from, 0.0, -30.0)
	check(bp0.begins_with("Sua cama"), "cama antes das 20h: '%s'" % bp0)
	Core.minutes = 21.0 * 60.0
	var day0: = Core.day
	var bp: String = await aim(bed_from, 0.0, -30.0)
	if check(bp.begins_with("Dormir"), "prompt da cama: '%s'" % bp):
		main.player.interact()
	check( await wait_until( func(): return Core.day == day0 + 1, 8.0), "dormiu: dia %d -> %d" % [day0, Core.day])
	await wait_until( func(): return not main._sleeping, 5.0)
	check(absf(Core.minutes - Core.WAKE_MIN) < 30.0, "acordou ~06:30 (%s)" % Core.clock_text())
	check(main.player.global_position.distance_to(main.world.home_wake) < 1.5, "acordou em casa")
	var sm: Dictionary = Core.slot_summary(0) if false else {}
	var f: = FileAccess.open(Core.SAVE_PATH, FileAccess.READ)
	var saved = JSON.parse_string(f.get_as_text()) if f else {}
	check(typeof(saved) == TYPE_DICTIONARY and int(saved.get("day", 0)) == Core.day and saved.has("player"), "save após dormir (dia %s, posição salva)" % str(saved.get("day", "?")))

	check(Economy.dish_margin("caipirinha") > 0 and Economy.dish_margin("petiscos") > 0, "cardápio tem margem")
	check(int(Core.last_summary.get("income", 0)) > 0, "fechamento: entradas %s" % Core.fmt_money(int(Core.last_summary.get("income", 0))))
	check(int(Core.last_summary.get("expense", 0)) >= Core.REDE_PRICE, "fechamento: saídas incluem a rede")
	var rate0: = Core.nightly_rate(0)
	var fan_cost: = Economy.next_cost("clima", 0)
	if Core.money < fan_cost:
		Core.book(fan_cost, "Aporte", "outro", false)
	check(Core.upgrade_room(0, "clima"), "melhorou o clima do bangalô 1")
	check(int(Core.rooms[0].upgrades.clima) == 1, "ventilador no nível 1")
	check(Core.nightly_rate(0) == rate0 + Economy.tier_rate("clima", 1), "diária subiu %d → %d" % [rate0, Core.nightly_rate(0)])
	check(main.world.upgrade_visible(0, "clima", 1), "ventilador visível")
	check( not main.world.upgrade_visible(0, "clima", 2), "ar-condicionado ainda oculto")
	Core.stock["coco"] = 1
	Core.stock["gelo"] = 4
	var dish_price: = int(Economy.dish("coco_gelado").price)
	var m_sell: = Core.money
	check(Core.sell_dish("coco_gelado", "kiosk") == dish_price, "vendeu coco gelado a %s" % Core.fmt_money(dish_price))
	check(Core.money == m_sell + dish_price, "venda entrou no caixa")
	check(int(Core.stock["coco"]) == 0, "coco acabou")
	var outs0: = Core.stockouts
	check(Core.sell_dish("coco_gelado", "kiosk") == -1, "sem estoque não vende")
	check(Core.stockouts == outs0 + 1, "falta de estoque derruba a avaliação")
	var m_buy: = Core.money
	check(Core.buy_supply("coco", Economy.PACK), "comprou fardo de coco")
	check(int(Core.stock["coco"]) == Economy.PACK, "estoque de coco = %d" % int(Core.stock["coco"]))
	check(Core.money == m_buy - Core.supply_total("coco", Economy.PACK), "custo do fardo descontado")
	var m_q: = Core.money
	check(Core.complete_quest("cocos_rita"), "entregou a encomenda da Dona Rita")
	check(Core.money == m_q + int(Economy.QUESTS.cocos_rita.reward), "recompensa da missão")
	# v0.7.5: missões novas, pesca, cocos caídos e álbum
	var peixe0: int = int(Core.stock.get("peixe", 0))
	check(main.village.fish_catch(0.95) == 3 and int(Core.stock["peixe"]) == peixe0 + 3, "pesca: peixe grande rende 3")
	check(main.village.fish_catch(0.05) == 0, "pesca: bota velha não rende nada")
	Core.accept_quest("peixe_ze")
	var mz: = Core.money
	check(Core.complete_quest("peixe_ze") and Core.money == mz + int(Economy.QUESTS.peixe_ze.reward), "entregou o peixe ao Seu Zé")
	check(main.world.coco_piles.size() >= 1, "cocos caídos na praia: %d montes" % main.world.coco_piles.size())
	var coco0: int = int(Core.stock.get("coco", 0))
	for ch in main.world.coco_piles[0].get_children():
		if ch is Interactable:
			ch.use()
	check(int(Core.stock["coco"]) == coco0 + Economy.COCO_PILE_YIELD and not main.world.coco_piles[0].visible, "juntou cocos caídos")
	main.world.reset_coco_piles()
	check(main.world.coco_piles[0].visible, "cocos caídos voltam no dia seguinte")
	Core.album = []
	var ma: = Core.money
	Core.vip_served("marcel")
	Core.vip_served("marcel")
	Core.vip_served("luna")
	check(Core.album.size() == 2, "álbum sem repetidos: %d" % Core.album.size())
	Core.vip_served("brasa")
	check(Core.album.size() == 3 and Core.money == ma + int(Economy.ALBUM_REWARDS[3]), "prêmio do álbum com 3 famosos")
	await vip_rush_test()
	if Core.money < int(Economy.STAFF.camareira.hire):
		Core.book(int(Economy.STAFF.camareira.hire), "Aporte", "outro", false)
	check(Core.hire("camareira"), "contratou camareira")
	check(bool(Core.staff.camareira), "camareira na equipe")
	var pocket: = Core.money
	Core.money = 0
	check( not Core.build_bungalow(), "bangalô extra recusado sem dinheiro")
	Core.money = pocket
	if Core.money < Economy.BUNGALOW_COST:
		Core.book(Economy.BUNGALOW_COST, "Aporte", "outro", false)
	check(Core.build_bungalow(), "construiu o bangalô 3")
	check(Core.rooms.size() == 3 and main.world.room_nodes.size() == 3, "terceiro bangalô existe no mundo")
	Core.set_weather("rain")
	check(Core.weather == "rain" and main.world.rain.visible, "chuva ligada")
	Core.set_weather("sun")
	check(Core.weather == "sun" and not main.world.rain.visible, "sol de volta")
	var had_upgrade: = false
	for line in Core.ledger_today:
		if str(line.get("c", "")) == "upgrade":
			had_upgrade = true
	check(had_upgrade, "livro-caixa tem melhoria")
	Core.save_game()
	var keep_coco: = int(Core.stock["coco"])
	var keep_up: = int(Core.rooms[0].upgrades.clima)
	var keep_n: = Core.rooms.size()
	var keep_money: = Core.money
	Core.stock["coco"] = 0
	Core.rooms[0].upgrades.clima = 0
	Core.money = 4
	Core.staff.camareira = false
	check(Core.load_game(), "save da progressão")
	check(int(Core.stock["coco"]) == keep_coco and int(Core.rooms[0].upgrades.clima) == keep_up, "save guardou estoque e upgrade")
	check(Core.rooms.size() == keep_n and Core.money == keep_money and bool(Core.staff.camareira), "save guardou bangalôs, dinheiro e equipe")
	Core.delete_save()
	print("LOOP_TEST %s  dinheiro=%d estrelas=%.2f bar=%d" % ["FAIL" if failed else "PASS", Core.money, Core.stars(), Core.bar_sales_total])
	get_tree().quit(1 if failed else 0)
