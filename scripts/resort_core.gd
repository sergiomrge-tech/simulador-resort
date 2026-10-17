extends Node
## Estado central do Maré Alta Resort: dinheiro, estrelas, tempo, quartos, compras e save.

signal money_changed(value: int)
signal stars_changed(value: float)
signal time_changed(day: int, minutes: float)
signal room_changed(room_id: int)
signal toast(text: String, kind: String)
signal redes_changed(count: int)
signal slept(day: int)
signal kiosk_sold(item: String, value: int)

var SAVE_PATH := "user://save_slot1.json"
var slot: int = 1
const SAVE_VERSION := 2
const WAKE_MIN := 390.0          # 06:30 — o herói acorda em casa
const SLEEP_FROM := 20.0 * 60.0
const MAX_REDES := 4
const REDE_PRICE := 150
const START_MONEY := 300

var money: int = START_MONEY
var ratings: Array = [3.0, 3.0, 3.0]   # últimas avaliações (média = estrelas)
var day: int = 1
var minutes: float = WAKE_MIN          # minutos do dia (0..1440)
var minutes_per_sec: float = 2.0        # 1 s real = 2 min de jogo (dia = 12 min)
var speed_mult: float = 1.0             # acelera tudo (usado em teste)
var redes: int = 0
var guests_served: int = 0
var bar_sales_total: int = 0
var rooms: Array = []                   # [{id, state, guest, dirty:{cama,toalhas,lixo}}]
var paused: bool = false
var tutorial_step: int = 0
var kiosk_sales_total: int = 0
var kiosk_sales_count: int = 0
var player_ref: Node3D               # para salvar posição do herói
var loaded_player := {}             # posição lida do save (aplicada pelo main)
var in_game := false                # false no menu principal (relógio parado)

var _autosave_t := 0.0
var _bar_batch_count := 0
var _bar_batch_value := 0
var _bar_batch_t := -1.0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	reset_rooms(2)

func reset_rooms(n: int) -> void:
	rooms.clear()
	for i in n:
		rooms.append({"id": i, "state": "free", "guest": -1,
			"dirty": {"cama": false, "toalhas": false, "lixo": false}})

func new_game() -> void:
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
	reset_rooms(2)
	_emit_all()

func _emit_all() -> void:
	money_changed.emit(money)
	stars_changed.emit(stars())
	time_changed.emit(day, minutes)
	redes_changed.emit(redes)
	for r in rooms:
		room_changed.emit(r.id)

func _process(delta: float) -> void:
	if paused or get_tree().paused or not in_game:
		return
	minutes += delta * minutes_per_sec * speed_mult
	if minutes >= 1440.0:
		minutes -= 1440.0
		day += 1
		toast.emit(tr("Dia %d começou!") % day, "info")
	time_changed.emit(day, minutes)
	# vendas do bar agrupadas em um só aviso
	if _bar_batch_t >= 0.0:
		_bar_batch_t -= delta * speed_mult
		if _bar_batch_t < 0.0:
			_flush_bar()
	_autosave_t += delta
	if _autosave_t > 45.0 and in_game:
		_autosave_t = 0.0
		save_game()

# ---------------------------------------------------------------- economia
func stars() -> float:
	if ratings.is_empty():
		return 3.0
	var s := 0.0
	for r in ratings:
		s += float(r)
	return clampf(s / ratings.size(), 1.0, 5.0)

func add_rating(r: float) -> void:
	ratings.append(clampf(r, 1.0, 5.0))
	while ratings.size() > 12:
		ratings.pop_front()
	stars_changed.emit(stars())

func add_money(v: int, reason: String = "") -> void:
	money += v
	money_changed.emit(money)
	if reason != "":
		toast.emit("%s  %s" % [reason, fmt_money(v, true)], "money")

func nightly_rate() -> int:
	return 100 + int(round(stars() * 12.0)) + redes * 8

func bar_sale(value: int) -> void:
	money += value
	bar_sales_total += value
	money_changed.emit(money)
	_bar_batch_count += 1
	_bar_batch_value += value
	if _bar_batch_t < 0.0:
		_bar_batch_t = 20.0

func _flush_bar() -> void:
	if _bar_batch_count > 0:
		var txt := (tr("Bar do Coqueiro: %d venda") if _bar_batch_count == 1 else tr("Bar do Coqueiro: %d vendas")) % _bar_batch_count
		toast.emit("%s  %s" % [txt, fmt_money(_bar_batch_value, true)], "money")
	_bar_batch_count = 0
	_bar_batch_value = 0
	_bar_batch_t = -1.0

func force_flush_bar() -> void:
	_flush_bar()

static func fmt_money(v: int, sign_plus := false) -> String:
	var a := absi(v)
	var s := str(a)
	var out := ""
	while s.length() > 3:
		out = "." + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	out = s + out
	var pre := ""
	if v < 0:
		pre = "-"
	elif sign_plus:
		pre = "+"
	return "%sR$ %s" % [pre, out]

func clock_text() -> String:
	var h := int(minutes / 60.0)
	var m := int(minutes) % 60
	return "%02d:%02d" % [h, m]

func is_night() -> bool:
	return minutes < 6.0 * 60.0 or minutes > 18.5 * 60.0

func kiosk_sale(item: String, value: int) -> void:
	money += value
	kiosk_sales_total += value
	kiosk_sales_count += 1
	money_changed.emit(money)
	kiosk_sold.emit(item, value)
	toast.emit("%s  %s" % [tr("Quiosque: %s") % tr(item), fmt_money(value, true)], "money")

func can_sleep() -> bool:
	return minutes >= SLEEP_FROM or minutes < 5.0 * 60.0

## Dormir: vai para o próximo dia às 06:30 e salva.
func sleep() -> void:
	if minutes >= 12.0 * 60.0:
		day += 1
	minutes = WAKE_MIN
	force_flush_bar()
	slept.emit(day)
	time_changed.emit(day, minutes)
	toast.emit(tr("Bom dia! Dia %d") % day, "info")
	save_game()

func set_slot(i: int) -> void:
	slot = clampi(i, 1, 3)
	SAVE_PATH = slot_path(slot)

static func slot_path(i: int) -> String:
	return "user://save_slot%d.json" % i

## Resumo de um slot para o menu (vazio se não existe).
static func slot_summary(i: int) -> Dictionary:
	var p := slot_path(i)
	if not FileAccess.file_exists(p):
		return {}
	var f := FileAccess.open(p, FileAccess.READ)
	if f == null:
		return {}
	var data = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(data) != TYPE_DICTIONARY:
		return {}
	return {"day": int(data.get("day", 1)), "money": int(data.get("money", 0)), "minutes": float(data.get("minutes", 0)),
		"saved_at": str(data.get("saved_at", ""))}

# ---------------------------------------------------------------- quartos
func free_room() -> int:
	for r in rooms:
		if r.state == "free":
			return r.id
	return -1

func occupy_room(id: int, guest_id: int) -> void:
	rooms[id].state = "occupied"
	rooms[id].guest = guest_id
	room_changed.emit(id)

func vacate_room(id: int) -> void:
	rooms[id].state = "dirty"
	rooms[id].guest = -1
	rooms[id].dirty = {"cama": true, "toalhas": true, "lixo": true}
	room_changed.emit(id)

func clean_item(id: int, item: String) -> bool:
	var r: Dictionary = rooms[id]
	if r.state != "dirty" or not r.dirty.get(item, false):
		return false
	r.dirty[item] = false
	var done := true
	for k in r.dirty:
		if r.dirty[k]:
			done = false
	if done:
		r.state = "free"
		toast.emit(tr("Bangalô %d limpo e pronto!") % (id + 1), "good")
	room_changed.emit(id)
	return true

func dirty_count() -> int:
	var n := 0
	for r in rooms:
		if r.state == "dirty":
			n += 1
	return n

# ---------------------------------------------------------------- loja
func buy_rede() -> bool:
	if redes >= MAX_REDES:
		toast.emit(tr("Todas as redes já foram instaladas."), "bad")
		return false
	if money < REDE_PRICE:
		toast.emit(tr("Dinheiro insuficiente para a rede (%s).") % fmt_money(REDE_PRICE), "bad")
		return false
	add_money(-REDE_PRICE, tr("Rede comprada"))
	redes += 1
	redes_changed.emit(redes)
	add_rating(4.5)  # decoração deixa os hóspedes felizes
	save_game()
	return true

# ---------------------------------------------------------------- save
func save_game() -> void:
	var data := {
		"v": SAVE_VERSION, "money": money, "ratings": ratings, "day": day,
		"minutes": minutes, "redes": redes, "served": guests_served,
		"bar": bar_sales_total, "tut": tutorial_step, "rooms": [],
		"kiosk": kiosk_sales_total, "kiosk_n": kiosk_sales_count,
		"saved_at": Time.get_datetime_string_from_system(false, true),
	}
	if is_instance_valid(player_ref) and player_ref.is_inside_tree():
		var pp := player_ref.global_position
		data["player"] = {"x": pp.x, "y": pp.y, "z": pp.z, "yaw": player_ref.rotation.y}
	for r in rooms:
		var st: String = r.state
		var dirty: Dictionary = r.dirty.duplicate()
		if st == "occupied":   # hóspede em trânsito não é salvo: quarto fica sujo
			st = "dirty"
			dirty = {"cama": true, "toalhas": true, "lixo": true}
		data.rooms.append({"state": st, "dirty": dirty})
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(data))
		f.close()

func load_game() -> bool:
	if not FileAccess.file_exists(SAVE_PATH):
		return false
	var f := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if f == null:
		return false
	var data = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(data) != TYPE_DICTIONARY or int(data.get("v", 0)) < 1:
		return false
	money = int(data.money)
	ratings = data.ratings
	day = int(data.day)
	minutes = float(data.minutes)
	redes = int(data.redes)
	guests_served = int(data.get("served", 0))
	bar_sales_total = int(data.get("bar", 0))
	tutorial_step = int(data.get("tut", 0))
	kiosk_sales_total = int(data.get("kiosk", 0))
	kiosk_sales_count = int(data.get("kiosk_n", 0))
	loaded_player = data.get("player", {})
	reset_rooms(data.rooms.size())
	for i in data.rooms.size():
		rooms[i].state = data.rooms[i].state
		rooms[i].dirty = data.rooms[i].dirty
	_emit_all()
	return true

func delete_save() -> void:
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_PATH))

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		if in_game:
			save_game()
