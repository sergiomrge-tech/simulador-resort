extends Node


signal money_changed(value: int)
signal stars_changed(value: float)
signal time_changed(day: int, minutes: float)
signal room_changed(room_id: int)
signal toast(text: String, kind: String)
signal redes_changed(count: int)
signal slept(day: int)
signal kiosk_sold(item: String, value: int)
signal stock_changed
signal ledger_changed
signal upgrades_changed(room_id: int)
signal bungalow_built(room_id: int)
signal staff_changed
signal day_closed(summary: Dictionary)
signal weather_changed(kind: String)
signal expansion_bought(id: String)
signal market_changed
signal event_changed
signal tour_done(id: String, pax: int, revenue: int)

var SAVE_PATH: = "user://save_slot1.json"
var slot: int = 1
var proc_props: = false   # --proc: usa os props montados por código (P) em vez dos modelos reais
const SAVE_VERSION: = 7
const CompanyRules = preload("res://scripts/company_rules.gd")
signal company_changed
var company: Dictionary = CompanyRules.defaults()
var service_station: String = "cozinha"
const WAKE_MIN: = 390.0
const SLEEP_FROM: = 20.0 * 60.0
const MAX_REDES: = Economy.HAMMOCK_MAX
const REDE_PRICE: = Economy.HAMMOCK_PRICE
const START_MONEY: = Economy.START_MONEY

var money: int = START_MONEY
var ratings: Array = [3.0, 3.0, 3.0]
var day: int = 1
var minutes: float = WAKE_MIN
var minutes_per_sec: float = 2.0
var speed_mult: float = 1.0
var redes: int = 0
var guests_served: int = 0
var bar_sales_total: int = 0
var rooms: Array = []
var paused: bool = false
var tutorial_step: int = 0
var kiosk_sales_total: int = 0
var kiosk_sales_count: int = 0
var player_ref: Node3D
var loaded_player: = {}
var in_game: = false
var stock: Dictionary = {}
var ledger_today: Array = []
var day_income: int = 0
var day_expense: int = 0
var last_summary: Dictionary = {}
var stockouts: int = 0
var staff: = {"atendente": false, "camareira": false, "bartender": false, "guia": false}
var unlocked: = {}
var quests: = {}
var weather: = "sun"
## v0.7.5: preço por prato (nível 0-4), freezer, evento do dia e álbum de clientes famosos.
var price_tier: = {}
var freezer: = false
var day_event: = ""
var album: Array = []
## v0.9.0: fornecedores (preço do dia e contratos), previsão de eventos, preparativos e passeios.
var supply_mult: = {}      # id -> multiplicador do preço de hoje
var contracts: = {}        # id -> dias restantes do contrato
var forecast_next: = ""    # evento de amanhã (previsão)
var forecast_set: = false
var prep_paid: = false     # preparativos pagos para o próximo evento
var prep_active: = false   # preparativos valendo no evento de hoje
var tours_done: = {}       # passeios já realizados hoje
var tours_total: int = 0
var tours_revenue: int = 0

var prog: Prog   # v1.0: fama, árvore de melhorias, negócios, equipe, temporadas, receitas e capítulos
var _autosave_t: = 0.0
var _bar_batch_count: = 0
var _bar_batch_value: = 0
var _bar_batch_t: = -1.0
var _maid_acc: = 0.0
var _helper_acc: = 0.0

func _ready() -> void :
	process_mode = Node.PROCESS_MODE_ALWAYS
	prog = Prog.new()
	prog.name = "Prog"
	add_child(prog)
	prog.reset()
	_reset_economy()
	reset_rooms(0)

func _blank_room(i: int) -> Dictionary:
	return {"id": i, "state": "free", "guest": -1, 
		"dirty": {"cama": false, "toalhas": false, "lixo": false}, 
		"upgrades": Economy.blank_upgrades()}

func reset_rooms(n: int) -> void :
	rooms.clear()
	for i in n:
		rooms.append(_blank_room(i))

func _reset_economy() -> void :
	stock = Economy.START_STOCK.duplicate()
	ledger_today = []
	day_income = 0
	day_expense = 0
	last_summary = {}
	stockouts = 0
	staff = {}
	for role in Economy.STAFF:
		staff[role] = false
	company = CompanyRules.defaults()
	supply_mult = {}
	contracts = {}
	forecast_next = ""
	forecast_set = false
	prep_paid = false
	prep_active = false
	tours_done = {}
	tours_total = 0
	tours_revenue = 0
	quests = {}
	price_tier = {}
	freezer = false
	day_event = ""
	album = []
	_maid_acc = 0.0
	_helper_acc = 0.0
	if weather != "sun":
		weather = "sun"
		weather_changed.emit(weather)

func new_game() -> void :
	money = START_MONEY
	ratings = [3.0, 3.0, 3.0]
	day = 1
	minutes = WAKE_MIN
	redes = 0
	kiosk_sales_total = 0
	kiosk_sales_count = 0
	loaded_player = {}
	guests_served = 0
	bar_sales_total = 0
	tutorial_step = 0
	_reset_bar_batch()
	_reset_economy()
	unlocked = {}
	reset_rooms(0)
	prog.reset()
	_emit_all()
	expansion_bought.emit("")
	if is_inside_tree():
		get_tree().call_group("world", "sync_bungalows")

func _emit_all() -> void :
	company_changed.emit()
	money_changed.emit(money)
	stars_changed.emit(stars())
	time_changed.emit(day, minutes)
	redes_changed.emit(redes)
	for r in rooms:
		room_changed.emit(r.id)

func _process(delta: float) -> void :
	if paused or get_tree().paused or not in_game:
		return
	minutes += delta * minutes_per_sec * speed_mult
	if minutes >= 1440.0:
		minutes -= 1440.0
		day += 1
		_pay_wages(true)
		toast.emit(tr("Dia %d começou!") % day, "info")
	time_changed.emit(day, minutes)

	if _bar_batch_t >= 0.0:
		_bar_batch_t -= delta * speed_mult
		if _bar_batch_t < 0.0:
			_flush_bar()
	prog.tick(delta * minutes_per_sec * speed_mult)
	if prog.staff_eff("camareira") > 0.0:
		_maid_acc += delta * minutes_per_sec * speed_mult * prog.staff_eff("camareira") * (1.0 + prog.eff("maid_speed"))
		if _maid_acc >= Economy.MAID_MINUTES:
			_maid_acc = 0.0
			_maid_sweep()
	if not company_enabled() and prog.staff_eff("atendente") > 0.0:
		_helper_acc += delta * minutes_per_sec * speed_mult * prog.staff_eff("atendente")
		if _helper_acc >= Economy.HELPER_MINUTES:
			_helper_acc = 0.0
			get_tree().call_group("kiosk", "helper_serve")
	CompanyRules.Simulation.tick(self, delta * minutes_per_sec * speed_mult)
	tick_company(delta)
	_check_tours()
	_autosave_t += delta
	if _autosave_t > 45.0 and in_game:
		_autosave_t = 0.0
		save_game()

func _maid_sweep() -> void :
	for r in rooms:
		if r.state != "dirty":
			continue
		for k in ["lixo", "toalhas", "cama"]:
			if r.dirty.get(k, false):
				clean_item(int(r.id), k)
				return


func stars() -> float:
	if ratings.is_empty():
		return 3.0
	var s: = 0.0
	for r in ratings:
		s += float(r)
	return clampf(s / ratings.size(), 1.0, 5.0)

func add_rating(r: float) -> void :
	ratings.append(clampf(r + rating_bonus(), 1.0, 5.0))
	while ratings.size() > 12:
		ratings.pop_front()
	stars_changed.emit(stars())

## v1.0: capricho do quiosque, café da manhã, fornecedores premium e atendente simpático melhoram todas as notas.
func rating_bonus() -> float:
	if prog == null:
		return 0.0
	var b: = prog.eff("kiosk_quality") + prog.eff("breakfast") + prog.premium_share() * PD.PREMIUM_RATING
	if prog.staff_eff("atendente") > 0.0 and str(prog.staff_rec("atendente").trait) == "simpatico":
		b += 0.15
	return b

func add_money(v: int, reason: String = "", cat: String = "outro") -> void :
	book(v, reason, cat, reason != "")


func book(v: int, reason: String, cat: String, do_toast: = true) -> void :
	money += v
	if v >= 0:
		day_income += v
	else:
		day_expense += - v
	if reason != "":
		ledger_today.append({"a": v, "r": reason, "c": cat})
		if ledger_today.size() > 40:
			ledger_today.pop_front()
	if company.created:
		if cat == "quiosque" and v > 0:
			CompanyRules.Simulation.record(self, "cash_in", v)
		elif cat == "insumo" and v < 0:
			CompanyRules.Simulation.record(self, "supplies", -v)
	money_changed.emit(money)
	ledger_changed.emit()
	if prog:
		prog.on_income(v, cat)
	if do_toast and reason != "":
		toast.emit("%s  %s" % [reason, fmt_money(v, true)], "money" if v >= 0 else "bad")

func nightly_rate(room_id: int = -1) -> int:
	var v: = Economy.BASE_NIGHTLY + int(round(stars() * Economy.STAR_BONUS)) + redes * Economy.HAMMOCK_BONUS + int(prog.eff("room_rate"))
	if room_id >= 0:
		v += room_rate_bonus(room_id)
	return v

func room_rate_bonus(id: int) -> int:
	if id < 0 or id >= rooms.size():
		return 0
	var s: = 0
	var u: Dictionary = rooms[id].upgrades
	for cat in u:
		if Economy.UPGRADES.has(cat):
			s += Economy.tier_rate(cat, int(u[cat]))
	return s

func room_comfort(id: int) -> float:
	if id < 0 or id >= rooms.size():
		return 0.0
	var t: = 0
	for cat in rooms[id].upgrades:
		t += int(rooms[id].upgrades[cat])
	return float(t) * Economy.COMFORT_PER_TIER

func bar_sale(value: int, reason: String = "") -> void :
	book(value, reason if reason != "" else tr("Bar"), "bar", false)
	bar_sales_total += value
	_bar_batch_count += 1
	_bar_batch_value += value
	if _bar_batch_t < 0.0:
		_bar_batch_t = 20.0

func _flush_bar() -> void :
	if _bar_batch_count > 0:
		var txt: = (tr("Bar do Coqueiro: %d venda") if _bar_batch_count == 1 else tr("Bar do Coqueiro: %d vendas")) % _bar_batch_count
		toast.emit("%s  %s" % [txt, fmt_money(_bar_batch_value, true)], "money")
	_reset_bar_batch()

func _reset_bar_batch() -> void :
	_bar_batch_count = 0
	_bar_batch_value = 0
	_bar_batch_t = -1.0

func force_flush_bar() -> void :
	_flush_bar()

static func fmt_money(v: int, sign_plus: = false) -> String:
	var a: = absi(v)
	var s: = str(a)
	var out: = ""
	while s.length() > 3:
		out = "." + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	out = s + out
	var pre: = ""
	if v < 0:
		pre = "-"
	elif sign_plus:
		pre = "+"
	return "%sR$ %s" % [pre, out]

func clock_text() -> String:
	var h: = int(minutes / 60.0)
	var m: = int(minutes) % 60
	return "%02d:%02d" % [h, m]

func is_night() -> bool:
	return minutes < 6.0 * 60.0 or minutes > 18.5 * 60.0

func kiosk_sale(item: String, value: int) -> void :
	book(value, tr("Quiosque: %s") % tr(item), "quiosque", true)
	kiosk_sales_total += value
	kiosk_sales_count += 1
	kiosk_sold.emit(item, value)

func can_sleep() -> bool:
	return minutes >= SLEEP_FROM or minutes < 5.0 * 60.0


func sleep() -> void :
	if minutes >= 12.0 * 60.0:
		day += 1
	minutes = WAKE_MIN
	company.kiosk_open = false
	_pay_wages()
	CompanyRules.Simulation.rollover(self)
	prog.on_new_day()
	force_flush_bar()
	spoil_stock()
	slept.emit(day)
	last_summary = _snapshot_ledger()
	_reset_day_ledger()
	day_closed.emit(last_summary)
	time_changed.emit(day, minutes)
	toast.emit(tr("Bom dia! Dia %d") % day, "info")
	roll_supply_prices()
	roll_day_event()
	CompanyRules.Simulation.run_auto_order(self)
	tours_done = {}
	save_game()

func _pay_wages(company_only: bool = false) -> void :
	var total: = 0
	var pay_day: int = day - 1
	for role in staff:
		var company_role: bool = company.created and role in CompanyRules.Simulation.ROLES
		if company_only and not company_role:
			continue
		if company_role and int(company.sim.wage_day) >= pay_day:
			continue
		if not bool(staff[role]) or not Economy.STAFF.has(role):
			continue
		var w: = prog.staff_wage(role)
		total += w
		book( - w, tr("Salário: %s") % tr(str(Economy.STAFF[role].name)), "folha", false)
		if role in CompanyRules.Simulation.ROLES:
			CompanyRules.Simulation.record(self, "payroll", w)
	if company.created:
		company.sim.wage_day = maxi(int(company.sim.wage_day), pay_day)
	if total > 0:
		toast.emit("%s  %s" % [tr("Salários do dia"), fmt_money( - total)], "bad")

func _snapshot_ledger() -> Dictionary:
	var cats: = {}
	for line in ledger_today:
		var c: = str(line.get("c", "outro"))
		cats[c] = int(cats.get(c, 0)) + int(line.get("a", 0))
	return {
		"day": day - 1, 
		"income": day_income, 
		"expense": day_expense, 
		"net": day_income - day_expense, 
		"cats": cats, 
		"lines": ledger_today.duplicate(true), 
	}

func _reset_day_ledger() -> void :
	ledger_today = []
	day_income = 0
	day_expense = 0

func set_slot(i: int) -> void :
	slot = clampi(i, 1, 3)
	SAVE_PATH = slot_path(slot)

static func slot_path(i: int) -> String:
	return "user://save_slot%d.json" % i


static func slot_summary(i: int) -> Dictionary:
	var p: = slot_path(i)
	if not FileAccess.file_exists(p):
		return {}
	var f: = FileAccess.open(p, FileAccess.READ)
	if f == null:
		return {}
	var data = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(data) != TYPE_DICTIONARY:
		return {}
	return {"day": int(data.get("day", 1)), "money": int(data.get("money", 0)), "minutes": float(data.get("minutes", 0)), 
		"saved_at": str(data.get("saved_at", ""))}


func free_room() -> int:
	for r in rooms:
		if r.state == "free":
			return r.id
	return -1

func occupy_room(id: int, guest_id: int) -> void :
	rooms[id].state = "occupied"
	rooms[id].guest = guest_id
	room_changed.emit(id)

func vacate_room(id: int) -> void :
	rooms[id].state = "dirty"
	rooms[id].guest = -1
	rooms[id].dirty = {"cama": true, "toalhas": true, "lixo": true}
	room_changed.emit(id)

func clean_item(id: int, item: String) -> bool:
	var r: Dictionary = rooms[id]
	if r.state != "dirty" or not r.dirty.get(item, false):
		return false
	r.dirty[item] = false
	var done: = true
	for k in r.dirty:
		if r.dirty[k]:
			done = false
	if done:
		r.state = "free"
		toast.emit(tr("Bangalô %d limpo e pronto!") % (id + 1), "good")
	room_changed.emit(id)
	return true

func dirty_count() -> int:
	var n: = 0
	for r in rooms:
		if r.state == "dirty":
			n += 1
	return n


func buy_rede() -> bool:
	if redes >= MAX_REDES:
		toast.emit(tr("Todas as redes já foram instaladas."), "bad")
		return false
	if money < REDE_PRICE:
		toast.emit(tr("Dinheiro insuficiente para a rede (%s).") % fmt_money(REDE_PRICE), "bad")
		return false
	add_money( - REDE_PRICE, tr("Rede comprada"), "compra")
	redes += 1
	redes_changed.emit(redes)
	add_rating(4.5)
	save_game()
	return true


func can_make(id: String) -> bool:
	if not Economy.DISHES.has(id):
		return false
	var uses: Dictionary = Economy.dish(id).uses
	for ing in uses:
		if int(stock.get(ing, 0)) < int(uses[ing]):
			return false
	return true

# ------------------------------------------------------------------ progressão (v0.7)
func has(id: String) -> bool:
	return bool(unlocked.get(id, false))

func dish_unlocked(id: String) -> bool:
	if bool(Economy.DISHES.get(id, {}).get("secret", false)) and not prog.is_discovered(id):
		return false
	return not Economy.DISH_UNLOCK.has(id) or has(str(Economy.DISH_UNLOCK[id]))

## Pratos que os clientes podem pedir: liberados e não desligados no Cardápio.
func kiosk_menu() -> Array:
	return Economy.KIOSK_MENU.filter(func(d): return dish_unlocked(d) and not bool(prog.menu_off.get(d, false)))

func bar_menu() -> Array:
	return Economy.BAR_MENU.filter(func(d): return dish_unlocked(d))

func kiosk_open_min() -> float:
	return float(company.sim.start) * 60.0 if bool(company.sim.custom_hours) else 8.0 * 60.0

func kiosk_close_min() -> float:
	if bool(company.sim.custom_hours):
		return float(company.sim.end) * 60.0
	return (Economy.KIOSK_CLOSE_NEON_H if has("neon") else Economy.KIOSK_CLOSE_H) * 60.0

## "owned" | "ready" (pode comprar agora) | "money" (falta dinheiro) | "locked" (falta requisito). Motivo em [1].
func expansion_state(id: String) -> Array:
	if has(id):
		return ["owned", ""]
	var e: Dictionary = Economy.EXPANSIONS[id]
	for r in e.get("req", []):
		if not has(str(r)):
			return ["locked", tr("Precisa de: %s") % tr(str(Economy.EXPANSIONS[r].name))]
	if stars() + 0.001 < float(e.get("stars", 0.0)):
		return ["locked", tr("Precisa de ★ %.1f (agora ★ %.1f)") % [float(e.stars), stars()]]
	if rooms.size() < int(e.get("rooms", 0)):
		return ["locked", tr("Precisa de %d bangalôs") % int(e.rooms)]
	if prog.fame_level < int(e.get("fame", 0)):
		return ["locked", tr("Precisa de fama \"%s\"") % tr(prog.fame_name(int(e.fame)))]
	if str(e.get("chapter", "")) != "" and not prog.chapter_done(str(e.chapter)):
		return ["locked", tr("Conclua o capítulo \"%s\" (app Vila)") % tr(prog.chapter_title(str(e.chapter)))]
	if money < int(e.cost):
		return ["money", tr("Faltam %s") % fmt_money(int(e.cost) - money)]
	return ["ready", ""]

## Próxima expansão ainda não comprada, na ordem da campanha ("" quando tudo foi comprado).
func next_expansion() -> String:
	for id in Economy.EXPANSION_ORDER:
		if not has(id):
			return id
	return ""

func buy_expansion(id: String) -> bool:
	if not Economy.EXPANSIONS.has(id):
		return false
	var st: = expansion_state(id)
	if st[0] == "owned":
		return false
	if st[0] != "ready":
		toast.emit(str(st[1]), "bad")
		return false
	var e: Dictionary = Economy.EXPANSIONS[id]
	unlocked[id] = true
	book( - int(e.cost), tr(str(e.name)), "upgrade", true)
	if id == "pousada" and rooms.is_empty():
		rooms.append(_blank_room(0))
		bungalow_built.emit(0)
		room_changed.emit(0)
	expansion_bought.emit(id)
	toast.emit(tr("Nova conquista: %s!") % tr(str(e.name)), "good")
	get_tree().call_group("audio", "sfx", "bell")
	save_game()
	return true

## Usado por saves antigos (v0.6.x) e pelo teste: libera tudo.
func unlock_all() -> void :
	for id in Economy.EXPANSIONS:
		unlocked[id] = true
	expansion_bought.emit("")

func menu_blocked() -> bool:
	for id in kiosk_menu():
		if not can_make(id):
			return true
	return false

func note_stockout(id: String) -> void :
	CompanyRules.Simulation.record(self, "stockouts", 1)
	stockouts += 1
	add_rating(Economy.STOCKOUT_RATING)
	var name: = id
	if Economy.DISHES.has(id):
		name = str(Economy.dish(id).name)
	toast.emit(tr("Sem estoque para %s") % tr(name), "bad")

## Preço de venda atual do prato (o jogador ajusta pelo computador, em 5 níveis).
func price_tier_of(id: String) -> int:
	return clampi(int(price_tier.get(id, Economy.PRICE_DEFAULT_TIER)), 0, Economy.PRICE_TIERS.size() - 1)

func price_of(id: String) -> int:
	return maxi(1, int(round(float(Economy.dish(id).price) * float(Economy.PRICE_TIERS[price_tier_of(id)]))))

func set_price_tier(id: String, tier: int) -> void :
	if not Economy.DISHES.has(id):
		return
	price_tier[id] = clampi(tier, 0, Economy.PRICE_TIERS.size() - 1)
	stock_changed.emit()

## Média dos multiplicadores de preço do cardápio do quiosque.
func avg_price_mult() -> float:
	var m: Array = kiosk_menu()
	if m.is_empty():
		return 1.0
	var t: = 0.0
	for d in m:
		t += float(Economy.PRICE_TIERS[price_tier_of(d)])
	return t / float(m.size())

## Quanto o preço atrai (ou afasta) clientes: > 1 = mais clientes. Inclui o evento do dia.
func demand_factor() -> float:
	var m: Array = kiosk_menu()
	var f: = 1.0
	if not m.is_empty():
		f = 0.0
		for d in m:
			f += float(Economy.DEMAND_BY_TIER[price_tier_of(d)])
		f /= float(m.size())
	if day_event == "calor":
		f *= 1.25 * (1.0 + prog.eff("event_bonus"))
	elif day_event == "carnaval":
		f *= Economy.CARNAVAL_DEMAND * (1.0 + prog.eff("event_bonus"))
	elif is_party():
		f *= (Economy.PARTY_DECO_DEMAND if prep_active else Economy.PARTY_DEMAND) * (1.0 + prog.eff("event_bonus"))
	elif Economy.EVENT_DEMAND.has(day_event):
		f *= float(Economy.EVENT_DEMAND[day_event])
	# v1.0: fama, temporada e melhorias da praia/bar
	f *= (1.0 + PD.FAME_DEMAND * float(prog.fame_level - 1)) * prog.season_demand() * (1.0 + prog.eff("beach_demand") + prog.eff("happy_hour"))
	return f

func is_party() -> bool:
	return day_event != "" and bool(Economy.DAY_EVENTS[day_event].get("party", false))

## Fração dos clientes do quiosque que vêm da praia (a maré alta e a tempestade esvaziam a areia).
func beach_share() -> float:
	return float(Economy.BEACH_SHARE.get(day_event, 0.6))

## Ajuste na nota de quem foi atendido: preço salgado reclama, preço camarada agrada.
func price_rating_adjust() -> float:
	var a: = avg_price_mult()
	if prog.fame_level >= 9 and a < 1.35:
		return 0.0
	if a >= 1.35:
		return -0.9
	if a >= 1.1:
		return -0.3
	if a <= 0.8:
		return 0.15
	return 0.0

## Evento de um dia: festa do calendário (a partir do dia 8) ou sorteio (calor, lua, maré alta, tempestade).
func pick_event(d: int) -> String:
	if prog.is_carnaval_day(d):
		return "carnaval"
	if d >= Economy.PARTY_FROM_DAY and Economy.PARTY_CALENDAR.has(d % 7):
		return str(Economy.PARTY_CALENDAR[d % 7])
	if d <= 1:
		return ""
	# v1.0: a temporada pesa as chances (verão: calor; inverno: tempestade e maré)
	var odds: Dictionary = PD.SEASONS[prog.season_index(d)].odds
	var r: = randf()
	var acc: = 0.0
	for o in Economy.EVENT_ODDS:
		acc += float(o[1]) * float(odds.get(o[0], 1.0))
		if r < acc:
			return str(o[0])
	return ""

## Evento do dia: o que foi previsto ontem (ou sorteado), e já prevê o de amanhã.
func roll_day_event() -> void :
	var prev: = day_event
	day_event = forecast_next if forecast_set else pick_event(day)
	forecast_next = pick_event(day + 1)
	forecast_set = true
	prep_active = prep_paid and day_event != ""
	prep_paid = false
	if day_event == "tempestade":
		set_weather("rain")
		if prep_active:
			toast.emit(tr("Preparativos prontos: o estoque está protegido da tempestade."), "good")
		else:
			_storm_damage()
	elif prev == "tempestade":
		set_weather("sun")
	if day_event != "":
		var e: Dictionary = Economy.DAY_EVENTS[day_event]
		toast.emit("%s: %s" % [tr(str(e.name)), tr(str(e.blurb))], "info")
	if forecast_next != "":
		toast.emit(tr("Previsão para amanhã: %s.") % tr(str(Economy.DAY_EVENTS[forecast_next].name)), "info")
	event_changed.emit()

func _storm_damage() -> void :
	var lost: = 0
	for id in stock.keys():
		var n: = int(round(float(int(stock[id])) * Economy.STORM_LOSS * maxf(0.0, 1.0 - prog.eff("storm_guard"))))
		if n > 0:
			stock[id] = int(stock[id]) - n
			lost += n
	if lost > 0:
		stock_changed.emit()
		toast.emit(tr("A tempestade molhou o estoque: %d itens perdidos.") % lost, "bad")

## Quanto custam os preparativos para o evento citado ("" = não precisa de preparativos).
func prep_cost(ev: String) -> int:
	if ev == "tempestade" or ev == "mare":
		return Economy.STORM_PREP_COST
	if ev != "" and bool(Economy.DAY_EVENTS[ev].get("party", false)):
		return Economy.PARTY_DECO_COST
	return 0

## Paga os preparativos: do evento de amanhã (tempestade, maré, festa) ou decoração da festa de hoje.
func buy_prep() -> bool:
	if prep_paid or prep_active:
		toast.emit(tr("Os preparativos já estão pagos."), "info")
		return false
	var target: = forecast_next
	var today: = false
	if is_party() and not prep_active:
		target = day_event
		today = true
	var cost: = prep_cost(target)
	if cost <= 0:
		toast.emit(tr("Não há nada para preparar."), "info")
		return false
	if money < cost:
		toast.emit(tr("Dinheiro insuficiente (%s).") % fmt_money(cost), "bad")
		return false
	book( - cost, tr("Preparativos: %s") % tr(str(Economy.DAY_EVENTS[target].name)), "outro", true)
	if today:
		prep_active = true
	else:
		prep_paid = true
	event_changed.emit()
	return true

## Fornecedores: sorteia o preço de hoje de cada insumo e desconta os dias dos contratos.
func roll_supply_prices() -> void :
	for id in Economy.SUPPLIES:
		var m: float = float(Economy.PRICE_SWING[randi() % Economy.PRICE_SWING.size()])
		supply_mult[id] = m
		if contracts.has(id):
			contracts[id] = int(contracts[id]) - 1
			if int(contracts[id]) <= 0:
				contracts.erase(id)
				toast.emit(tr("Contrato de %s terminou.") % tr(str(Economy.SUPPLIES[id].name)).to_lower(), "info")
	market_changed.emit()

## Multiplicador do preço de hoje. Contrato = desconto fixo e nunca paga mais que o preço normal.
func supply_factor(id: String) -> float:
	var m: float = float(supply_mult.get(id, 1.0))
	if contracts.has(id):
		return minf(m, 1.0) * (1.0 - Economy.CONTRACT_DISCOUNT)
	return m

## Preço total de comprar qty unidades hoje (arredonda para cima).
func supply_total(id: String, qty: int) -> int:
	var prem: = PD.PREMIUM_MULT if bool(prog.premium.get(id, false)) else 1.0
	return maxi(1, int(ceil(float(Economy.supply_cost(id)) * supply_factor(id) * prem * float(qty) - 0.001)))

func buy_contract(id: String) -> bool:
	if not Economy.SUPPLIES.has(id) or contracts.has(id):
		return false
	if money < Economy.CONTRACT_FEE:
		toast.emit(tr("Dinheiro insuficiente para o contrato (%s).") % fmt_money(Economy.CONTRACT_FEE), "bad")
		return false
	contracts[id] = Economy.CONTRACT_DAYS
	book( - Economy.CONTRACT_FEE, tr("Contrato: %s (%d dias)") % [tr(str(Economy.SUPPLIES[id].name)), Economy.CONTRACT_DAYS], "insumo", true)
	market_changed.emit()
	return true

## Passeios turísticos: com o guia contratado, cada saída rende no horário marcado.
func _check_tours() -> void :
	if not has("passeios") or not bool(staff.get("guia", false)):
		return
	for id in Economy.TOURS:
		var t: Dictionary = Economy.TOURS[id]
		if tours_done.has(id) or minutes < float(t.at) or minutes > float(t.at) + 90.0:
			continue
		run_tour(id)

func run_tour(id: String) -> int:
	if not Economy.TOURS.has(id) or tours_done.has(id):
		return 0
	tours_done[id] = true
	var t: Dictionary = Economy.TOURS[id]
	if bool(t.sea) and (day_event == "mare" or day_event == "tempestade"):
		toast.emit(tr("%s cancelado pelo mar.") % tr(str(t.name)), "bad")
		return 0
	if not bool(t.sea) and day_event == "tempestade":
		toast.emit(tr("%s cancelada pela tempestade.") % tr(str(t.name)), "bad")
		return 0
	var occupied: = 0
	for r in rooms:
		if r.state == "occupied":
			occupied += 1
	var seats: = int(t.seats) + (2 if prog.fame_level >= 8 else 0)
	var pax: = clampi(int(round(1.0 + stars() * 1.2 + float(occupied) * 1.5 + 0.3 * float(prog.fame_level - 1))), 1, seats)
	if is_party():
		pax = mini(int(t.seats), pax + 2)
	# guia com nível cobra um pouco mais (experiência)
	var gl: = int(prog.staff_rec("guia").lvl) if bool(staff.get("guia", false)) else 1
	var rev: int = int(round(float(pax * int(t.price)) * (1.0 + 0.05 * float(gl - 1)))) - int(t.cost)
	tours_total += 1
	tours_revenue += rev
	book(rev, tr("%s · %d pessoas") % [tr(str(t.name)), pax], "passeio", true)
	add_rating(0.05)
	tour_done.emit(id, pax, rev)
	prog.on_tour(pax)
	return rev

func tour_status(id: String) -> String:
	var t: Dictionary = Economy.TOURS[id]
	if tours_done.has(id):
		return "done"
	if minutes > float(t.at):
		return "missed"
	return "wait"

## Estoque que sobra estraga durante a noite (gelo derrete, peixe e pão passam do ponto).
func spoil_stock() -> void :
	var lost: = []
	for id in Economy.SPOIL:
		var have: = int(stock.get(id, 0))
		if have <= 0:
			continue
		var rate: = float(Economy.SPOIL[id]) * (0.5 if freezer else 1.0)
		var n: = mini(have, int(round(float(have) * rate)))
		if n > 0:
			stock[id] = have - n
			lost.append("%d %s" % [n, tr(str(Economy.SUPPLIES[id].name)).to_lower()])
	if not lost.is_empty():
		stock_changed.emit()
		toast.emit(tr("Estragou durante a noite: %s.") % ", ".join(lost), "bad")

func buy_freezer() -> bool:
	if freezer or money < Economy.FREEZER_COST:
		return false
	freezer = true
	book( - Economy.FREEZER_COST, tr("Freezer"), "compra", true)
	stock_changed.emit()
	return true

## Chamado quando um cliente VIP é atendido: o famoso entra no álbum e os marcos pagam prêmio.
func vip_served(id: String) -> void :
	if id != "":
		prog.on_vip()
	if id == "" or album.has(id):
		return
	album.append(id)
	var nm: = id
	for v in Economy.VIPS:
		if v.id == id:
			nm = str(v.name)
	toast.emit(tr("Novo no álbum: %s! (%d/%d)") % [nm, album.size(), Economy.VIPS.size()], "good")
	if Economy.ALBUM_REWARDS.has(album.size()):
		var r: = int(Economy.ALBUM_REWARDS[album.size()])
		book(r, tr("Prêmio do álbum: %d famosos") % album.size(), "missao", true)

func quest_available(id: String) -> bool:
	if not Economy.QUESTS.has(id):
		return false
	var req: = str(Economy.QUESTS[id].get("req", ""))
	return req == "" or has(req)

func sell_dish(id: String, channel: String) -> int:
	if not Economy.DISHES.has(id):
		return -1
	if not can_make(id):
		note_stockout(id)
		return -1
	var uses: Dictionary = Economy.dish(id).uses
	for ing in uses:
		stock[ing] = int(stock[ing]) - int(uses[ing])
	stock_changed.emit()
	var price: = price_of(id)
	if channel == "bar":
		price = int(round(float(price) * (1.0 + Economy.BARTENDER_MARKUP * prog.staff_eff("bartender") + prog.eff("bar_markup"))))
	var nm: = str(Economy.dish(id).name)
	if channel == "bar":
		bar_sale(price, tr("Bar: %s") % tr(nm))
	else:
		kiosk_sale(nm, price)
	prog.on_sale(id, channel)
	return price

func serve_bar() -> int:
	var ready: Array = []
	for id in bar_menu():
		if can_make(id):
			ready.append(id)
	if ready.is_empty():
		note_stockout(str(bar_menu()[0]))
		return 0
	return maxi(0, sell_dish(str(ready[randi() % ready.size()]), "bar"))

func buy_supply(id: String, qty: int) -> bool:
	if not Economy.SUPPLIES.has(id) or qty <= 0:
		return false
	var cost: = supply_total(id, qty)
	if money < cost:
		toast.emit(tr("Dinheiro insuficiente no mercadinho (%s).") % fmt_money(cost), "bad")
		return false
	stock[id] = int(stock.get(id, 0)) + qty
	book( - cost, tr("%s ×%d") % [tr(str(Economy.SUPPLIES[id].name)), qty], "insumo", true)
	stock_changed.emit()
	return true


func upgrade_room(id: int, cat: String) -> bool:
	if id < 0 or id >= rooms.size() or not Economy.UPGRADES.has(cat):
		return false
	if not rooms[id].upgrades.has(cat):
		rooms[id].upgrades[cat] = 0
	var tier: = int(rooms[id].upgrades[cat])
	var cost: = Economy.next_cost(cat, tier)
	if cost < 0:
		toast.emit(tr("Esse cômodo já está no máximo."), "info")
		return false
	if money < cost:
		toast.emit(tr("Dinheiro insuficiente para a melhoria (%s).") % fmt_money(cost), "bad")
		return false
	rooms[id].upgrades[cat] = tier + 1
	book( - cost, tr("%s · Bangalô %d") % [tr(Economy.tier_name(cat, tier + 1)), id + 1], "upgrade", true)
	room_changed.emit(id)
	upgrades_changed.emit(id)
	return true

func build_bungalow() -> bool:
	if not has("pousada"):
		toast.emit(tr("Compre a pousada primeiro (computador → Expansões)."), "bad")
		return false
	if rooms.size() >= Economy.BUNGALOW_MAX:
		toast.emit(tr("A pousada já tem o máximo de bangalôs."), "info")
		return false
	if money < Economy.BUNGALOW_COST:
		toast.emit(tr("Dinheiro insuficiente para um bangalô (%s).") % fmt_money(Economy.BUNGALOW_COST), "bad")
		return false
	var id: = rooms.size()
	rooms.append(_blank_room(id))
	book( - Economy.BUNGALOW_COST, tr("Novo bangalô %d") % (id + 1), "upgrade", true)
	bungalow_built.emit(id)
	room_changed.emit(id)
	return true

func hire(role: String, offered_fee: int = -1) -> bool:
	if not Economy.STAFF.has(role):
		return false
	if bool(Economy.STAFF[role].get("company", false)) and not bool(company.created):
		toast.emit(tr("Crie sua empresa no computador primeiro."), "bad")
		return false
	if bool(staff.get(role, false)):
		toast.emit(tr("Já contratado: %s") % tr(str(Economy.STAFF[role].name)), "info")
		return false
	var need: = str(Economy.STAFF[role].get("req", ""))
	if need != "" and not has(need):
		toast.emit(tr("Precisa de: %s") % tr(str(Economy.EXPANSIONS[need].name)), "bad")
		return false
	var cost: int = offered_fee if offered_fee >= 0 else int(Economy.STAFF[role].hire)
	if money < cost:
		toast.emit(tr("Dinheiro insuficiente para contratar (%s).") % fmt_money(cost), "bad")
		return false
	staff[role] = true
	if role in CompanyRules.Simulation.ROLES and company.created:
		var begin: int = int(kiosk_open_min() / 60)
		company.sim.shifts[role] = {"start": begin, "end": mini(23, begin + 8)}
		CompanyRules.Simulation.record(self, "investment", cost)
	book( - cost, tr("Contratação: %s") % tr(str(Economy.STAFF[role].name)), "folha", true)
	staff_changed.emit()
	company_changed.emit()
	return true

func accept_quest(id: String) -> void :
	if not Economy.QUESTS.has(id) or str(quests.get(id, "")) != "" or not quest_available(id):
		return
	quests[id] = "active"
	toast.emit(tr(str(Economy.QUESTS[id].title)), "info")

func complete_quest(id: String) -> bool:
	if not Economy.QUESTS.has(id) or str(quests.get(id, "")) == "done":
		return false
	var q: Dictionary = Economy.QUESTS[id]
	if int(stock.get(q.need, 0)) < int(q.qty):
		toast.emit(tr("Faltam %d × %s.") % [int(q.qty), tr(str(Economy.SUPPLIES[q.need].name))], "bad")
		return false
	stock[q.need] = int(stock[q.need]) - int(q.qty)
	quests[id] = "done"
	stock_changed.emit()
	book(int(q.reward), tr(str(q.title)), "missao", true)
	if q.has("rating"):
		add_rating(float(q.rating))
	return true

func set_weather(kind: String) -> void :
	if kind != "rain":
		kind = "sun"
	if weather == kind:
		return
	weather = kind
	weather_changed.emit(kind)


func save_game() -> void :
	var data: = {
		"company": company.duplicate(true), "v": SAVE_VERSION, "money": money, "ratings": ratings, "day": day,
		"minutes": minutes, "redes": redes, "served": guests_served, 
		"bar": bar_sales_total, "tut": tutorial_step, "rooms": [], 
		"kiosk": kiosk_sales_total, "kiosk_n": kiosk_sales_count, 
		"stock": stock.duplicate(), "stockouts": stockouts, 
		"staff": staff.duplicate(), "quests": quests.duplicate(), 
		"weather": weather, "ledger": ledger_today.duplicate(true), 
		"ptier": price_tier.duplicate(), "freezer": freezer, "event": day_event, "album": album.duplicate(), 
		"smult": supply_mult.duplicate(), "contracts": contracts.duplicate(), "forecast": forecast_next, "forecast_set": forecast_set, 
		"prep_paid": prep_paid, "prep_active": prep_active, "tours_done": tours_done.duplicate(), "tours_n": tours_total, "tours_rev": tours_revenue, 
		"day_in": day_income, "day_out": day_expense, 
		"summary": last_summary.duplicate(true), "unlocked": unlocked.duplicate(), "prog": prog.to_dict(), 
		"saved_at": Time.get_datetime_string_from_system(false, true), 
	}
	if is_instance_valid(player_ref) and player_ref.is_inside_tree():
		var pp: = player_ref.global_position
		data["player"] = {"x": pp.x, "y": pp.y, "z": pp.z, "yaw": player_ref.rotation.y, "kiosk_facing": "beach"}
	for r in rooms:
		var st: String = r.state
		var dirty: Dictionary = r.dirty.duplicate()
		if st == "occupied":
			st = "dirty"
			dirty = {"cama": true, "toalhas": true, "lixo": true}
		data.rooms.append({"state": st, "dirty": dirty, "upgrades": r.upgrades.duplicate()})
	var f: = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(data))
		f.close()

func load_game() -> bool:
	if not FileAccess.file_exists(SAVE_PATH):
		return false
	var f: = FileAccess.open(SAVE_PATH, FileAccess.READ)
	if f == null:
		return false
	var data = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(data) != TYPE_DICTIONARY or int(data.get("v", 0)) < 1:
		return false
	if typeof(data.get("rooms")) != TYPE_ARRAY or typeof(data.get("ratings")) != TYPE_ARRAY:
		return false
	money = int(data.money)
	_reset_bar_batch()
	ratings = data.ratings
	day = int(data.day)
	minutes = float(data.minutes)
	redes = int(data.redes)
	guests_served = int(data.get("served", 0))
	bar_sales_total = int(data.get("bar", 0))
	tutorial_step = int(data.get("tut", 0))
	kiosk_sales_total = int(data.get("kiosk", 0))
	kiosk_sales_count = int(data.get("kiosk_n", 0))
	stockouts = int(data.get("stockouts", 0))
	loaded_player = data.get("player", {})
	_reset_economy()
	company = CompanyRules.sanitize(data.get("company", {}))
	weather = str(data.get("weather", "sun"))
	var sk = data.get("stock", {})
	if typeof(sk) == TYPE_DICTIONARY:
		for k in sk:
			if stock.has(k):
				stock[k] = int(sk[k])
	var stf = data.get("staff", {})
	if typeof(stf) == TYPE_DICTIONARY:
		for k in staff.keys():
			staff[k] = bool(stf.get(k, false))
	var pt = data.get("ptier", {})
	price_tier = pt.duplicate() if typeof(pt) == TYPE_DICTIONARY else {}
	freezer = bool(data.get("freezer", false))
	day_event = str(data.get("event", ""))
	var sm = data.get("smult", {})
	supply_mult = sm.duplicate() if typeof(sm) == TYPE_DICTIONARY else {}
	var ct = data.get("contracts", {})
	contracts = ct.duplicate() if typeof(ct) == TYPE_DICTIONARY else {}
	forecast_next = str(data.get("forecast", ""))
	forecast_set = bool(data.get("forecast_set", false))
	prep_paid = bool(data.get("prep_paid", false))
	prep_active = bool(data.get("prep_active", false))
	var td = data.get("tours_done", {})
	tours_done = td.duplicate() if typeof(td) == TYPE_DICTIONARY else {}
	tours_total = int(data.get("tours_n", 0))
	tours_revenue = int(data.get("tours_rev", 0))
	var alb = data.get("album", [])
	album = alb.duplicate() if typeof(alb) == TYPE_ARRAY else []
	var qs = data.get("quests", {})
	quests = qs if typeof(qs) == TYPE_DICTIONARY else {}
	day_income = int(data.get("day_in", 0))
	day_expense = int(data.get("day_out", 0))
	var led = data.get("ledger", [])
	ledger_today = led if typeof(led) == TYPE_ARRAY else []
	var ls = data.get("summary", {})
	last_summary = ls if typeof(ls) == TYPE_DICTIONARY else {}
	unlocked = {}
	if int(data.get("v", 0)) < 4:
		for id in Economy.EXPANSIONS:
			unlocked[id] = true
	else:
		var ul = data.get("unlocked", {})
		if typeof(ul) == TYPE_DICTIONARY:
			for k in ul:
				if Economy.EXPANSIONS.has(k):
					unlocked[k] = bool(ul[k])
	var pd = data.get("prog", {})
	prog.from_dict(pd if typeof(pd) == TYPE_DICTIONARY else {})
	reset_rooms(data.rooms.size())
	for i in data.rooms.size():
		rooms[i].state = data.rooms[i].state
		rooms[i].dirty = data.rooms[i].dirty
		var up = data.rooms[i].get("upgrades", {})
		if typeof(up) == TYPE_DICTIONARY:
			for k in rooms[i].upgrades.keys():
				if up.has(k):
					rooms[i].upgrades[k] = int(up[k])
	_emit_all()
	stock_changed.emit()
	staff_changed.emit()
	company_changed.emit()
	market_changed.emit()
	event_changed.emit()
	weather_changed.emit(weather)
	expansion_bought.emit("")
	if is_inside_tree():
		get_tree().call_group("world", "sync_bungalows")
	return true

func delete_save() -> void :
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_PATH))

func _notification(what: int) -> void :
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		if in_game:
			save_game()

# ================================================================ empresa / operação física
func kiosk_is_within_hours() -> bool:
	return CompanyRules.Simulation.is_workday(self) and minutes >= kiosk_open_min() and minutes < kiosk_close_min()

func kiosk_accepting_customers() -> bool:
	return kiosk_is_within_hours() and bool(company.get("kiosk_open", false)) and CompanyRules.Simulation.Management.opening_ready(self)

func set_kiosk_open(value: bool) -> void:
	if value and not CompanyRules.Simulation.Management.opening_ready(self):
		toast.emit("Conclua o checklist de abertura em Quiosque → Horários e rotina.", "info")
		return
	company.kiosk_open = value
	company_changed.emit()
	save_game()
	if value:
		toast.emit(tr("Quiosque aberto!") if kiosk_is_within_hours() else tr("Quiosque preparado para abrir no próximo horário programado."), "good")
	else:
		toast.emit(tr("Quiosque fechado para novas chegadas. Conclua os pedidos dos clientes que já estão aqui."), "info")

func set_kiosk_schedule(start: int, end: int, days: Array) -> bool:
	if start < 6 or end > 23 or start >= end or days.is_empty():
		toast.emit("Escolha abertura entre 06h e 22h, fechamento até 23h e ao menos um dia.", "bad")
		return false
	for index in days:
		if not index is int or index < 0 or index > 6:
			return false
	company.sim.start = start
	company.sim.end = end
	company.sim.days = days.duplicate()
	company.sim.custom_hours = true
	company_changed.emit()
	save_game()
	return true

func set_kiosk_shift(role: String, start: int, end: int) -> bool:
	if role not in CompanyRules.Simulation.ROLES or not bool(staff.get(role, false)) or start < 6 or start >= end or end > 23:
		toast.emit("Escolha um turno válido, com entrada antes da saída, entre 06h e 23h.", "bad")
		return false
	company.sim.shifts[role] = {"start": start, "end": end}
	staff_changed.emit()
	save_game()
	return true

func kiosk_staff_on_shift(role: String) -> bool:
	return CompanyRules.Simulation.staff_on_shift(self, role)

func dismiss_kiosk_staff(role: String) -> bool:
	if role not in CompanyRules.Simulation.ROLES or not bool(staff.get(role, false)):
		return false
	var fee: int = prog.staff_wage(role) * 3
	if money < fee:
		toast.emit("Saldo insuficiente para a rescisão de três diárias.", "bad")
		return false
	if role in ["garcom", "atendente"] and company.staff_carry != "" and not return_company_staff_dish():
		toast.emit("Libere espaço para devolver o produto do funcionário.", "bad")
		return false
	staff[role] = false
	company.sim.shifts.erase(role)
	company.sim.management.profiles.erase(role)
	prog.staff_info.erase(role)
	CompanyRules.Simulation.record(self, "investment", fee)
	book(-fee, "Rescisão: " + str(Economy.STAFF[role].name), "folha", true)
	staff_changed.emit()
	company_changed.emit()
	save_game()
	return true

func set_kiosk_reorder(enabled: bool, target: int) -> void:
	company.sim.auto_order = enabled
	company.sim.target = clampi(target, 1, 48)
	company_changed.emit()
	save_game()

func restock_kiosk() -> bool:
	var okay: bool = CompanyRules.Simulation.reorder(self)
	if okay:
		save_game()
	return okay

func company_enabled() -> bool:
	return bool(company.created) and bool(company.physical)

func configure_company(title: String, font_id: String, color_id: String = "creme") -> bool:
	title = title.strip_edges()
	if not CompanyRules.valid_name(title) or not CompanyRules.FONTS.has(font_id) or not CompanyRules.COLORS.has(color_id):
		toast.emit(tr("Use um nome de 1 a 24 caracteres e uma fonte da lista."), "bad")
		return false
	if int(company.sim.day) == 0:
		company.sim.day = day
	company.created = true
	company.name = title
	company.font = font_id
	company.color = color_id
	company_changed.emit()
	save_game()
	return true

func set_company_service(enabled: bool) -> bool:
	if not company.created:
		return false
	if not enabled and (company.carry != "" or company.staff_carry != "" or not company.production.is_empty() or not company.receivables.is_empty() or not company.dirty_seats.is_empty()):
		toast.emit(tr("Entregue o item, receba as contas e limpe as mesas primeiro."), "bad")
		return false
	company.physical = enabled
	company_changed.emit()
	save_game()
	return true

# Produtos são retirados prontos. O estoque compartilhado é debitado uma vez.
func company_available(id: String) -> int:
	if id not in Economy.KIOSK_MENU or not dish_unlocked(id):
		return 0
	var count := 9999
	for ing in Economy.dish(id).uses:
		count = mini(count, int(stock.get(ing, 0)) / int(Economy.dish(id).uses[ing]))
	return int(company.ready.get(id, 0)) + count

func _take_company_unit(id: String) -> bool:
	if company_available(id) <= 0:
		return false
	if int(company.ready.get(id, 0)) > 0:
		company.ready[id] = int(company.ready[id]) - 1
	else:
		for ing in Economy.dish(id).uses:
			stock[ing] = int(stock[ing]) - int(Economy.dish(id).uses[ing])
	return true

func prepare_company_dish(_id: String) -> bool:
	# Compatibility entry point for old saves/extensions; preparation is removed.
	return false

func tick_company(_delta: float) -> void:
	# Recover an already-paid unit from an older save without another stock debit.
	if company.production.is_empty():
		return
	var id: String = str(company.production.get("dish", ""))
	company.production = {}
	if id in Economy.KIOSK_MENU:
		company.ready[id] = int(company.ready.get(id, 0)) + 1
	company_changed.emit()

func pickup_company_dish(id: String) -> bool:
	if not company_enabled() or company.carry != "" or not _take_company_unit(id):
		return false
	company.carry = id
	stock_changed.emit()
	company_changed.emit()
	return true

func return_company_dish() -> bool:
	var id: String = str(company.carry)
	if id == "" or int(company.ready.get(id, 0)) + (1 if company.production.get("dish", "") == id else 0) >= CompanyRules.MAX_READY:
		return false
	company.ready[id] = int(company.ready.get(id, 0)) + 1
	company.carry = ""
	company_changed.emit()
	return true

func sell_company_dish(id: String, by_staff: bool = false) -> int:
	var source: String = "staff_carry" if by_staff else "carry"
	if not company_enabled() or company[source] != id or id not in Economy.KIOSK_MENU:
		return -1
	if company.receivables.size() >= 256 and prog.staff_eff("caixa") <= 0.0:
		return -1
	var price: int = price_of(id)
	company[source] = ""
	company.receivables.append({"dish": id, "value": price})
	company_changed.emit()
	if prog.staff_eff("caixa") > 0.0:
		collect_company_payments()
	return price

func collect_company_payments() -> int:
	if not company_enabled():
		return 0
	var bills: Array = company.receivables.duplicate(true)
	company.receivables.clear()
	var total := 0
	for bill in bills:
		kiosk_sale(str(Economy.dish(str(bill.dish)).name), int(bill.value))
		prog.on_sale(str(bill.dish), "kiosk")
		total += int(bill.value)
	company_changed.emit()
	return total

func clean_company_seat(index: int) -> bool:
	if index not in company.dirty_seats:
		return false
	company.dirty_seats.erase(index)
	company_changed.emit()
	return true

func reserve_company_staff_dish(id: String) -> bool:
	if not company_enabled() or company.staff_carry != "" or not _take_company_unit(id):
		return false
	company.staff_carry = id
	stock_changed.emit()
	company_changed.emit()
	return true

func return_company_staff_dish() -> bool:
	var id: String = str(company.staff_carry)
	if id == "" or int(company.ready.get(id, 0)) + (1 if company.production.get("dish", "") == id else 0) >= CompanyRules.MAX_READY:
		return false
	company.ready[id] = int(company.ready.get(id, 0)) + 1
	company.staff_carry = ""
	company_changed.emit()
	return true

## Quote only the missing ingredients for a target number of ready portions.
func company_restock_quote(id: String, servings: int = 10) -> Dictionary:
	var result := {"items":{},"cost":0,"servings":servings}
	if not company_enabled() or id not in kiosk_menu() or servings < 1 or servings > 100: return result
	for ingredient in Economy.dish(id).uses:
		var missing := maxi(0,int(Economy.dish(id).uses[ingredient])*servings-int(stock.get(ingredient,0)))
		if missing > 0:
			result.items[ingredient] = missing
			result.cost += supply_total(ingredient,missing)
	return result

func restock_company_dish(id: String, servings: int = 10) -> bool:
	var quote := company_restock_quote(id,servings)
	if quote.items.is_empty(): return false
	if money < int(quote.cost):
		toast.emit("Saldo insuficiente para repor: " + fmt_money(int(quote.cost)), "bad")
		return false
	# Check the entire basket first, avoiding a partially purchased recipe.
	for ingredient in quote.items:
		buy_supply(ingredient,int(quote.items[ingredient]))
	toast.emit("Estoque reposto para " + str(servings) + " unidades de " + str(Economy.dish(id).name), "good")
	return true
