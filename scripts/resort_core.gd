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

var SAVE_PATH: = "user://save_slot1.json"
var slot: int = 1
const SAVE_VERSION: = 3
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
var staff: = {"camareira": false, "bartender": false}
var quests: = {}
var weather: = "sun"

var _autosave_t: = 0.0
var _bar_batch_count: = 0
var _bar_batch_value: = 0
var _bar_batch_t: = -1.0
var _maid_acc: = 0.0

func _ready() -> void :
	process_mode = Node.PROCESS_MODE_ALWAYS
	_reset_economy()
	reset_rooms(2)

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
	staff = {"camareira": false, "bartender": false}
	quests = {}
	_maid_acc = 0.0
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
	reset_rooms(2)
	_emit_all()
	if is_inside_tree():
		get_tree().call_group("world", "sync_bungalows")

func _emit_all() -> void :
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
		toast.emit(tr("Dia %d começou!") % day, "info")
	time_changed.emit(day, minutes)

	if _bar_batch_t >= 0.0:
		_bar_batch_t -= delta * speed_mult
		if _bar_batch_t < 0.0:
			_flush_bar()
	if bool(staff.get("camareira", false)):
		_maid_acc += delta * minutes_per_sec * speed_mult
		if _maid_acc >= Economy.MAID_MINUTES:
			_maid_acc = 0.0
			_maid_sweep()
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
	ratings.append(clampf(r, 1.0, 5.0))
	while ratings.size() > 12:
		ratings.pop_front()
	stars_changed.emit(stars())

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
	money_changed.emit(money)
	ledger_changed.emit()
	if do_toast and reason != "":
		toast.emit("%s  %s" % [reason, fmt_money(v, true)], "money" if v >= 0 else "bad")

func nightly_rate(room_id: int = -1) -> int:
	var v: = Economy.BASE_NIGHTLY + int(round(stars() * Economy.STAR_BONUS)) + redes * Economy.HAMMOCK_BONUS
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
	_pay_wages()
	force_flush_bar()
	slept.emit(day)
	last_summary = _snapshot_ledger()
	_reset_day_ledger()
	day_closed.emit(last_summary)
	time_changed.emit(day, minutes)
	toast.emit(tr("Bom dia! Dia %d") % day, "info")
	save_game()

func _pay_wages() -> void :
	var total: = 0
	for role in staff:
		if not bool(staff[role]) or not Economy.STAFF.has(role):
			continue
		var w: = int(Economy.STAFF[role].wage)
		total += w
		book( - w, tr("Salário: %s") % tr(str(Economy.STAFF[role].name)), "folha", false)
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

func menu_blocked() -> bool:
	for id in Economy.KIOSK_MENU:
		if not can_make(id):
			return true
	return false

func note_stockout(id: String) -> void :
	stockouts += 1
	add_rating(Economy.STOCKOUT_RATING)
	var name: = id
	if Economy.DISHES.has(id):
		name = str(Economy.dish(id).name)
	toast.emit(tr("Sem estoque para %s") % tr(name), "bad")

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
	var price: = int(Economy.dish(id).price)
	if channel == "bar" and bool(staff.get("bartender", false)):
		price = int(round(float(price) * (1.0 + Economy.BARTENDER_MARKUP)))
	var nm: = str(Economy.dish(id).name)
	if channel == "bar":
		bar_sale(price, tr("Bar: %s") % tr(nm))
	else:
		kiosk_sale(nm, price)
	return price

func serve_bar() -> int:
	var ready: Array = []
	for id in Economy.BAR_MENU:
		if can_make(id):
			ready.append(id)
	if ready.is_empty():
		note_stockout(str(Economy.BAR_MENU[0]))
		return 0
	return maxi(0, sell_dish(str(ready[randi() % ready.size()]), "bar"))

func buy_supply(id: String, qty: int) -> bool:
	if not Economy.SUPPLIES.has(id) or qty <= 0:
		return false
	var cost: = Economy.supply_cost(id) * qty
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

func hire(role: String) -> bool:
	if not Economy.STAFF.has(role):
		return false
	if bool(staff.get(role, false)):
		toast.emit(tr("Já contratado: %s") % tr(str(Economy.STAFF[role].name)), "info")
		return false
	var cost: = int(Economy.STAFF[role].hire)
	if money < cost:
		toast.emit(tr("Dinheiro insuficiente para contratar (%s).") % fmt_money(cost), "bad")
		return false
	staff[role] = true
	book( - cost, tr("Contratação: %s") % tr(str(Economy.STAFF[role].name)), "folha", true)
	staff_changed.emit()
	return true

func accept_quest(id: String) -> void :
	if not Economy.QUESTS.has(id) or str(quests.get(id, "")) != "":
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
		"v": SAVE_VERSION, "money": money, "ratings": ratings, "day": day, 
		"minutes": minutes, "redes": redes, "served": guests_served, 
		"bar": bar_sales_total, "tut": tutorial_step, "rooms": [], 
		"kiosk": kiosk_sales_total, "kiosk_n": kiosk_sales_count, 
		"stock": stock.duplicate(), "stockouts": stockouts, 
		"staff": staff.duplicate(), "quests": quests.duplicate(), 
		"weather": weather, "ledger": ledger_today.duplicate(true), 
		"day_in": day_income, "day_out": day_expense, 
		"summary": last_summary.duplicate(true), 
		"saved_at": Time.get_datetime_string_from_system(false, true), 
	}
	if is_instance_valid(player_ref) and player_ref.is_inside_tree():
		var pp: = player_ref.global_position
		data["player"] = {"x": pp.x, "y": pp.y, "z": pp.z, "yaw": player_ref.rotation.y}
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
	var qs = data.get("quests", {})
	quests = qs if typeof(qs) == TYPE_DICTIONARY else {}
	day_income = int(data.get("day_in", 0))
	day_expense = int(data.get("day_out", 0))
	var led = data.get("ledger", [])
	ledger_today = led if typeof(led) == TYPE_ARRAY else []
	var ls = data.get("summary", {})
	last_summary = ls if typeof(ls) == TYPE_DICTIONARY else {}
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
	weather_changed.emit(weather)
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
