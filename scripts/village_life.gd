extends Node3D



const DishPresentation = preload("res://scripts/dish_presentation.gd")
var prep_visual: Node3D

const GuestScript: = preload("res://scripts/guest.gd")
const KIOSK_OPEN: = 8.0 * 60.0
const KIOSK_CLOSE: = 18.0 * 60.0
const KIOSK_PATIENCE: = 90.0
## Minutos de jogo que o cliente passa lendo o cardápio antes de pedir.
const CHOOSE_MIN: = Vector2(4.0, 9.0)
## Minutos de jogo comendo/bebendo depois de servido.
const EAT_MIN: = Vector2(14.0, 26.0)
const MAX_QUEUE: = 3

var world: Node3D
var enabled: = true
var rng: = RandomNumberGenerator.new()
var walkers: Array = []
var customers: Array = []
var kiosk_spawn_in: = 10.0
var kiosk_lost: = 0
## v0.7.4: ritmo do dia no quiosque — sequência (combo), cliente VIP, ônibus de turistas e meta diária.
const COMBO_MAX: = 5
const VIP_CHANCE: = 0.08
var _dj_came: = false
const GOAL_REWARD: = 40
var combo: = 0
var served_today: = 0
var goal_paid: = false
var rush_done: = false
var rush_left: = 0
## Preparo em andamento no balcão: {g, dish, stage, p, away}. Vazio = nada sendo preparado.
var prep: = {}
## Pesca no píer: {t} enquanto a linha está na água.
var fish: = {}
var fish_casts: = 0

## v0.9.5: fregueses fiéis — voltam dia após dia, sempre pedem o prato favorito e deixam gorjeta maior a cada visita.
const REGULARS: = [
	{"id": "cida", "name": "Dona Cida", "fav": "suco", "f": true, "skin": Color(0.62, 0.42, 0.28), "shirt": Color(0.95, 0.5, 0.65), "hair": Color(0.75, 0.75, 0.78)},
	{"id": "nino", "name": "Seu Nino", "fav": "coco_gelado", "f": false, "skin": Color(0.8, 0.58, 0.42), "shirt": Color(0.95, 0.85, 0.3), "hair": Color(0.9, 0.9, 0.88)},
	{"id": "bia", "name": "Bia Surfista", "fav": "coco_gelado", "f": true, "skin": Color(0.95, 0.78, 0.62), "shirt": Color(0.15, 0.55, 0.75), "hair": Color(0.9, 0.78, 0.5)},
	{"id": "toninho", "name": "Toninho Pescador", "fav": "petiscos", "f": false, "skin": Color(0.42, 0.28, 0.18), "shirt": Color(0.9, 0.9, 0.88), "hair": Color(0.08, 0.06, 0.05)},
	{"id": "lia", "name": "Lia da Padaria", "fav": "caipirinha", "f": true, "skin": Color(0.8, 0.58, 0.42), "shirt": Color(0.3, 0.7, 0.45), "hair": Color(0.3, 0.18, 0.08)},
	{"id": "joca", "name": "Joca Músico", "fav": "suco", "f": false, "skin": Color(0.62, 0.42, 0.28), "shirt": Color(0.55, 0.35, 0.7), "hair": Color(0.18, 0.12, 0.08)},
]
var regulars: = {}

func _load_regulars() -> void :
	var f: = FileAccess.open("user://fregueses.json", FileAccess.READ)
	if f:
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			regulars = d

func _save_regulars() -> void :
	var f: = FileAccess.open("user://fregueses.json", FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(regulars))

func _pick_regular(menu: Array, female: bool) -> Dictionary:
	var present: = {}
	for g in customers:
		if is_instance_valid(g) and g.has_meta("regular"):
			present[g.get_meta("regular")] = true
	var opts: Array = REGULARS.filter(func(r): return not present.has(r.id) and menu.has(r.fav) and bool(r.f) == female)
	return {} if opts.is_empty() else opts[rng.randi() % opts.size()]

func _ready() -> void :
	add_to_group("kiosk")
	_load_regulars()
	rng.seed = 7171
	var n_walk: = 12 if Quality.hd else 5
	for i in n_walk:
		var g: = _make()
		var path: Array = world.village_paths[mini(world.village_paths.size()-1, floori(float(i)*world.village_paths.size()/n_walk))]
		g.set_meta("path", path)
		g.set_meta("dir", 1 if i % 2 == 0 else -1)
		var k: = rng.randi() % path.size()
		g.set_meta("idx", k)
		g.set_meta("wait", rng.randf_range(0.0, 4.0))
		g.position = _outside_blocks(path[k])
		g.speed = rng.randf_range(0.95, 1.3)
		walkers.append(g)
	var sit_n: = mini(3 if Quality.hd else 1, world.bench_spots.size())
	for i in sit_n:
		var s: Dictionary = world.bench_spots[i * 2 % world.bench_spots.size()]
		var g2: = _make()
		g2.position = s.pos
		g2.rotation.y = s.rot
		g2.play("Sitting_Idle_Loop")
		g2.set_meta("sitter", true)

	var rita: = _make()
	rita.position = world.village_points.barraca
	rita.rotation.y = 0.0
	rita.set_colors(Color(0.62, 0.42, 0.28), Color(0.95, 0.85, 0.3), Color(0.85, 0.3, 0.35), Color(0.08, 0.06, 0.05))
	rita.play("Idle_Talking_Loop")
	var cart: = _make()
	cart.position = world.village_points.cart
	cart.rotation.y = - PI * 0.5
	cart.set_colors(Color(0.8, 0.58, 0.42), Color(0.9, 0.9, 0.88), Color(0.15, 0.25, 0.5), Color(0.3, 0.18, 0.08))
	cart.play("Idle_Loop")
	# moradores com missão: Seu Zé (píer), Padre Tomé (igreja) e Dona Lourdes (padaria)
	var ze: = _make()
	ze.position = world.village_points.ze
	ze.rotation.y = 0.0
	ze.set_colors(Color(0.7, 0.5, 0.36), Color(0.95, 0.8, 0.2), Color(0.12, 0.2, 0.42), Color(0.9, 0.9, 0.88))
	ze.play("Idle_Talking_Loop")
	var padre: = _make()
	padre.position = world.village_points.padre
	padre.rotation.y = PI
	padre.set_colors(Color(0.78, 0.58, 0.44), Color(0.1, 0.1, 0.12), Color(0.1, 0.1, 0.12), Color(0.75, 0.75, 0.78))
	padre.play("Idle_Loop")
	var lourdes: = _make()
	lourdes.position = world.village_points.lourdes
	lourdes.rotation.y = 0.0
	lourdes.set_colors(Color(0.62, 0.42, 0.3), Color(0.95, 0.5, 0.65), Color(0.95, 0.95, 0.92), Color(0.25, 0.15, 0.1))
	lourdes.play("Idle_Talking_Loop")
	world.fish_spot.prompt_fn = fish_prompt
	world.fish_spot.action_fn = fish_action
	world.kiosk_counter.prompt_fn = kiosk_prompt
	world.kiosk_counter.action_fn = kiosk_action
	Core.slept.connect(_on_slept)

func _make() -> Node3D:
	var g: = Node3D.new()
	g.set_script(GuestScript)
	add_child(g)
	g.setup(9000 + get_child_count(), rng)
	g.block_rects = world.block_rects
	return g

func _process(delta: float) -> void :
	var dmin: = delta * Core.minutes_per_sec * Core.speed_mult
	var night: = Core.minutes > 22.0 * 60.0 or Core.minutes < 5.5 * 60.0
	for i in walkers.size():
		var g: Node3D = walkers[i]
		# v0.9.5: às 21h30 quem mora na vila caminha até a porta de uma casa e entra (some lá dentro); de manhã sai de novo
		var home_time: = Core.minutes > 21.5 * 60.0 or Core.minutes < 5.5 * 60.0
		if i >= 3 and home_time:
			if not g.has_meta("home_target"):
				var doors: Array = world.get("house_doors") if world.get("house_doors") != null else []
				var best: = Vector3.INF
				for dp in doors:
					if (dp as Vector3).distance_to(g.position) < best.distance_to(g.position):
						best = dp
				if best != Vector3.INF and best.distance_to(g.position) < 40.0:
					best = _outside_blocks(best)
					g.set_meta("home_target", best)
					g.go([best])
				else:
					g.set_meta("home_target", g.position)
			elif not g.is_moving():
				g.set_meta("home_done", true)
		elif g.has_meta("home_target"):
			g.remove_meta("home_target")
			g.remove_meta("home_done")
		var hide: bool = bool(g.get_meta("home_done", false)) or bool(g.get_meta("on_tour", false))
		g.visible = not hide
		if hide or g.has_meta("home_target"):
			continue
		if g.is_moving():
			continue
		if g.get_meta("shelter", false):
			# tempestade: fica abrigado sob o beiral até a chuva passar (EventFX)
			g.play("Idle_Talking_Loop" if i % 2 else "Idle_Loop")
			continue
		var w: float = g.get_meta("wait") - delta * Core.speed_mult
		if w > 0.0:
			g.set_meta("wait", w)
			g.play("Idle_Loop")
			continue
		var path: Array = g.get_meta("path")
		var idx: int = g.get_meta("idx")
		var dir: int = g.get_meta("dir")
		var nxt: = idx + dir
		if nxt < 0 or nxt >= path.size():
			dir = - dir
			nxt = idx + dir
			g.set_meta("dir", dir)
			g.set_meta("wait", rng.randf_range(2.0, 7.0))
		g.set_meta("idx", nxt)
		var jitter: = Vector3(rng.randf_range(-0.35, 0.35), 0, rng.randf_range(-0.35, 0.35))
		g.go([_outside_blocks(path[nxt] + jitter)])
	if prep.is_empty():
		_clear_prep_visual()
	_kiosk_tick(dmin)
	_prep_tick(delta)
	_fish_tick(delta)

func fish_prompt() -> String:
	if not fish.is_empty():
		return tr("Pescando...  %s") % _bar(float(fish.t) / Economy.FISH_SECONDS)
	if fish_casts >= Economy.FISH_CASTS_PER_DAY:
		return tr("Os peixes cansaram de você por hoje. Volte amanhã.")
	return tr("Pescar (%d/%d lançamentos hoje)") % [fish_casts, Economy.FISH_CASTS_PER_DAY]

func fish_action() -> void :
	if not fish.is_empty() or fish_casts >= Economy.FISH_CASTS_PER_DAY:
		return
	fish = {"t": 0.0}
	get_tree().call_group("audio", "sfx", "glass", -10.0, 0.7)

func _fish_tick(delta: float) -> void :
	if fish.is_empty():
		return
	var pl = get_parent().get("player")
	if pl == null or pl.focus != world.fish_spot:
		fish = {}
		return
	fish.t = float(fish.t) + delta
	if float(fish.t) >= Economy.FISH_SECONDS:
		fish = {}
		fish_catch(randf())

## r < 0,12 bota velha; até 0,65 um peixe; até 0,9 dois; o resto, peixe grande (3).
func fish_catch(r: float) -> int:
	fish_casts += 1
	var n: = 0
	if r >= 0.9:
		n = 3
	elif r >= 0.65:
		n = 2
	elif r >= 0.12:
		n = 1
	if n == 0:
		Core.toast.emit(tr("Você pescou uma bota velha. Tente de novo!"), "info")
		return 0
	Core.stock["peixe"] = int(Core.stock.get("peixe", 0)) + n
	Core.stock_changed.emit()
	Core.toast.emit((tr("Peixe grande! +%d peixes") % n) if n == 3 else (tr("Você pescou +%d peixe") % n if n == 1 else tr("Você pescou +%d peixes") % n), "good")
	get_tree().call_group("audio", "sfx", "coin", -8.0, 1.2)
	return n

## Segurar E no balcão adianta o preparo; se o jogador sai de perto por 2 s, o preparo é perdido.
func _prep_tick(delta: float) -> void :
	if prep.is_empty():
		return
	if not is_instance_valid(prep.g) or prep.g.state != "kwait":
		prep = {}
		return
	var pl = get_parent().get("player")
	var on: bool = pl != null and pl.focus == world.kiosk_counter
	if on:
		prep.away = 0.0
		if Input.is_action_pressed("interact"):
			prep_advance(delta)
	else:
		prep.away = float(prep.away) + delta
		if float(prep.away) > 2.0:
			prep = {}
			Core.toast.emit(tr("Preparo cancelado: fique de frente para o balcão."), "info")

func _outside_blocks(p: Vector3) -> Vector3:
	var rects: Array = world.block_rects
	var q: = p
	for _pass in 2:
		for r in rects:
			var rect: Rect2 = (r as Rect2).grow(0.38)
			if not rect.has_point(Vector2(q.x, q.z)):
				continue
			var dl: = q.x - rect.position.x
			var dr: = rect.end.x - q.x
			var dz0: = q.z - rect.position.y
			var dz1: = rect.end.y - q.z
			if dl <= dr and dl <= dz0 and dl <= dz1:
				q.x = rect.position.x - 0.08
			elif dr <= dz0 and dr <= dz1:
				q.x = rect.end.x + 0.08
			elif dz0 <= dz1:
				q.z = rect.position.y - 0.08
			else:
				q.z = rect.end.y + 0.08
	return q


func kiosk_open() -> bool:
	return Core.kiosk_is_within_hours()

func waiting_customers() -> Array:
	return customers.filter( func(c): return c.state == "kwait" and (not Core.company_enabled() or bool(c.get_meta("order_taken", true))))

func customers_to_order() -> Array:
	return customers.filter(func(c): return c.state == "kwait" and not bool(c.get_meta("order_taken", true)))

func _free_spot() -> int:
	var free: = []
	for i in world.kiosk_spots.size():
		var sp: Dictionary = world.kiosk_spots[i]
		# Balcão fica livre para retirada; no modo físico o consumo usa as mesas.
		if Core.company_enabled() and not sp.get("table",false): continue
		var need: = str(sp.get("need", ""))
		if not sp.busy and (need == "" or Core.has(need)) and (not Core.company_enabled() or i not in Core.company.dirty_seats) and Core.CompanyRules.Simulation.Management.sheltered(Core, sp):
			free.append(i)
	if free.is_empty():
		return -1
	# tempestade: primeiro as banquetas do balcão, que ficam debaixo do telhado de palha
	if Core.weather == "rain":
		var dry: Array = free.filter(func(i): return not world.kiosk_spots[i].get("table", false))
		if not dry.is_empty():
			free = dry
	return free[rng.randi() % free.size()]

func spawn_customer() -> Node3D:
	var si: = _free_spot()
	var queued: Array = customers.filter(func(c): return c.state in ["kqueue", "kcounter_queue"])
	if si < 0 and queued.size() >= MAX_QUEUE:
		return null
	if Core.company_enabled() and queued.size()>=MAX_QUEUE and customers.filter(func(c):return c.has_meta("counter_slot")).size()>=2:
		return null
	var g: = _make()
	var from_beach: = rng.randf() < Core.beach_share()
	var start: Vector3 = Vector3(rng.randf_range(46, 80), 0, rng.randf_range(-24, -21)) if from_beach else world.village_points.kiosk_approach[0]
	g.position = start
	var spot: Dictionary = world.kiosk_spots[si] if si >= 0 else {}
	if si >= 0:
		spot.busy = true
		spot["owner"] = g.get_instance_id()
	g.spot = spot
	g.set_meta("counter_first", Core.company_enabled())
	g.state = "kwalk" if si >= 0 else "kqueue"
	g.timer = KIOSK_PATIENCE
	var menu: Array = Core.kiosk_menu()
	var dish: String = _pick_dish(menu)
	var reg: Dictionary = _pick_regular(menu, bool(g.get("_female"))) if rng.randf() < 0.25 and not Core.day_event == "show_dj" else {}
	if not reg.is_empty():
		dish = str(reg.fav)
		g.set_meta("regular", reg.id)
		g.set_colors(reg.skin, reg.shirt, Color(0.2, 0.25, 0.4), reg.hair)
		var visits: = int(regulars.get(reg.id, 0))
		var rl: = B.label(g, "%s ♥%d" % [reg.name, visits] if visits > 0 else str(reg.name), Vector3(0, 2.1, 0), 20, Color(0.75, 1.0, 0.75), Color(0.05, 0.25, 0.08, 1))
		rl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		rl.pixel_size = 0.0025
		rl.no_depth_test = false
		rl.visible = not Core.company_enabled()
	g.set_meta("dish", dish)
	# quiosque cheio (ou mesas compradas) = pedidos maiores
	var items: Array = [dish]
	var extra_p: = (0.12 if Core.has("kiosk_tables") else 0.0) + 0.1 * float(customers.size())
	if Core.is_party():
		extra_p += 0.25 if Core.day_event == "junina" else 0.12
	if Core.prog.fame_level >= 5:   # fama 5: famílias pedem mais
		extra_p += 0.15
	if rng.randf() < minf(extra_p, 0.4):
		items.append(str(menu[rng.randi() % menu.size()]))
		if Core.stars() >= 4.0 and rng.randf() < 0.25:
			items.append(str(menu[rng.randi() % menu.size()]))
	g.set_meta("items", items)
	g.set_meta("delivered", 0)
	g.set_meta("revenue", 0)
	var dj_now: = Core.day_event == "show_dj" and not _dj_came
	if dj_now or (rng.randf() < VIP_CHANCE * (2.0 if Core.prog.fame_level >= 7 else 1.0) and Core.stars() >= 3.0):
		g.set_meta("vip", true)
		var vid: = "djmare" if dj_now else _pick_vip()
		if dj_now:
			_dj_came = true
		g.set_meta("vip_id", vid)
		var vl: = B.label(g, _vip_name(vid), Vector3(0, 2.15, 0), 22, Color(1.0, 0.88, 0.3), Color(0.25, 0.15, 0.02, 1))
		vl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		vl.double_sided = true
		vl.pixel_size = 0.0025
		vl.no_depth_test = false
		vl.visible = not Core.company_enabled()
	var route: Array = [] if from_beach else world.village_points.kiosk_approach.slice(1)
	if si < 0:
		var used: Array = queued.map(func(c): return int(c.get_meta("queue_slot")))
		var slot: = 0
		while slot in used:
			slot += 1
		g.set_meta("queue_slot", slot)
		# Fila a leste das mesas, fora das cadeiras e do corredor de acesso ao balcão.
		g.go([world.kiosk_point(Vector3(7.5, 0.1, 5.0 + slot * 1.1))])
		customers.append(g)
		return g
	if bool(g.get_meta("counter_first", false)):
		customers.append(g)
		_join_counter(g, route)
		return g
	if from_beach:
		route.append(world.kiosk_point(Vector3(-7.5,.05,12)))
	# Chega por trás da cadeira, sem cruzar o tampo para alcançar a raiz da animação.
	var front: Vector3 = spot.get("approach", Vector3(spot.pos.x, 0.1, spot.pos.z + 0.85))
	route.append(front)
	g.go(route)
	customers.append(g)
	return g

func _join_counter(g, route: Array = []) -> void:
	if not g.has_meta("dining_spot"): g.set_meta("dining_spot", g.spot)
	var occupied: Array = customers.filter(func(c): return c != g and c.has_meta("counter_slot")).map(func(c): return int(c.get_meta("counter_slot")))
	var slot := -1
	for i in 2:
		if i not in occupied: slot = i; break
	if slot < 0:
		g.state = "kcounter_queue"
		var queued: Array = customers.filter(func(c): return c != g and c.state in ["kqueue", "kcounter_queue"])
		var used: Array = queued.map(func(c): return int(c.get_meta("queue_slot", 0)))
		var queue_slot := 0
		while queue_slot in used: queue_slot += 1
		g.set_meta("queue_slot", queue_slot)
		g.go([world.kiosk_point(Vector3(7.5,.1,5+queue_slot*1.1))])
		return
	g.set_meta("counter_slot", slot)
	var x := -.7+slot*1.4
	g.spot = {"pos":world.kiosk_point(Vector3(x,.1,3.6)), "approach":world.kiosk_point(Vector3(x,.1,4.3)),
		"staff_approach":world.kiosk_point(Vector3(x,.1,1.05)), "serve_pos":world.kiosk_point(Vector3(x,1.30,2.15)),
		"serve_rot":PI, "rot":world.kiosk_spots[slot].rot, "table":false}
	g.state = "kwalk"
	var path: Array = route.duplicate()
	path.append(world.kiosk_point(Vector3(-3.3,.1,4.5)))
	path.append(g.spot.approach)
	g.go(path)

func _walk_to_dining(g, dish: String) -> void:
	clear_served_visuals(g)
	g.set_meta("counter_departure", g.spot.pos)
	g.spot = g.get_meta("dining_spot")
	g.remove_meta("dining_spot")
	g.set_meta("pickup_dish", dish)
	g.state = "kto_table"
	g.show_order("")
	g.hold_order(_items(g))
	var local: Vector3 = world.kiosk_local(g.spot.approach)
	var side := -1.0 if local.x<0 else 1.0
	g.go([world.kiosk_point(Vector3(side*3.3,.1,4.5)), g.spot.approach])

func _sit_with_order(g, dish: String) -> void:
	clear_served_visuals(g)
	g.position = g.spot.pos
	g.rotation.y = g.spot.rot
	g.state = "keat"
	g.set_meta("eat", rng.randf_range(EAT_MIN.x,EAT_MIN.y))
	for i in _items(g).size(): _show_delivered_visual(g,str(_items(g)[i]),i)
	g.consume_dish(dish)

func _kiosk_tick(dmin: float) -> void :
	# v0.7.1: depois do horário ninguém mais chega, e quem estava esperando vai embora (sem perder estrela)
	if not kiosk_open():
		var sent: = 0
		for g in customers:
			if g.state in ["kqueue", "kcounter_queue", "kwalk", "kchoose", "kwait", "kto_table", "keat"]:
				_leave(g)
				sent += 1
		if sent > 0 and Core.in_game:
			Core.toast.emit(tr("Quiosque fechado por hoje. Os últimos clientes foram embora."), "info")
	if enabled and Core.kiosk_accepting_customers():
		kiosk_spawn_in -= dmin
		if kiosk_spawn_in <= 0.0:
			var rngv: Vector2 = Economy.KIOSK_SPAWN_TABLES if Core.has("kiosk_tables") else Economy.KIOSK_SPAWN
			kiosk_spawn_in = rng.randf_range(rngv.x, rngv.y) / (Core.demand_factor() * Core.CompanyRules.Simulation.Management.arrival_factor(Core))
			if Core.day_event == "lua" and Core.minutes >= 17.0 * 60.0:
				kiosk_spawn_in *= 0.6
			if rush_left > 0:
				rush_left -= 1
				kiosk_spawn_in = rng.randf_range(2.5, 5.0)
			spawn_customer()
		# ônibus de turistas: uma vez por dia, entre 11h e 15h, com o quiosque já rodando
		if not rush_done and Core.in_game and Core.minutes >= 11.0 * 60.0 and Core.minutes <= 15.0 * 60.0 and served_today >= 3:
			if rng.randf() < dmin * 0.004:
				rush_done = true
				rush_left = 4
				kiosk_spawn_in = 1.5
				Core.toast.emit(tr("Chegou um ônibus de turistas! Vem gente: sirva rápido para manter o combo."), "good")
	for g in customers.duplicate():
		if g.has_meta("counter_departure"):
			if g.position.distance_to(g.get_meta("counter_departure"))>1.2:
				g.remove_meta("counter_departure")
				g.remove_meta("counter_slot")
		match g.state:
			"kcounter_queue":
				g.timer -= dmin
				if g.timer <= 0: _leave(g)
				elif not g.is_moving():
					var occupied := customers.filter(func(c): return c.has_meta("counter_slot"))
					if occupied.size()<2: _join_counter(g)
					else: g.play("Idle_Loop")
			"kqueue":
				g.timer -= dmin
				if not g.is_moving():
					var si: = _free_spot()
					if si >= 0:
						g.spot = world.kiosk_spots[si]
						g.spot.busy = true
						g.spot["owner"] = g.get_instance_id()
						if bool(g.get_meta("counter_first", false)):
							_join_counter(g)
							continue
						g.state = "kwalk"
						var front: Vector3 = g.spot.get("approach", Vector3(g.spot.pos.x, 0.1, g.spot.pos.z + 0.85))
						g.go([front])
					else:
						g.play("Idle_Loop")
				if g.state == "kqueue" and g.timer <= 0.0:
					_leave(g)
			"kwalk":
				if not g.is_moving():
					# senta e olha o cardápio antes de pedir
					g.state = "kchoose"
					g.position = g.spot.pos
					g.rotation.y = g.spot.rot
					g.play("Idle_Loop" if bool(g.get_meta("counter_first",false)) else "Sitting_Idle_Loop")
					g.set_meta("choose", rng.randf_range(CHOOSE_MIN.x, CHOOSE_MIN.y))
					g.show_menu(true)
			"kchoose":
				var ch: float = float(g.get_meta("choose", 0.0)) - dmin
				g.set_meta("choose", ch)
				if ch <= 0.0:
					_order(g)
			"kwait":
				g.timer -= dmin
				var urgent: bool = g.timer < _patience(g) * 0.3
				if urgent and not g.get_meta("urgent", false):
					g.set_meta("urgent", true)
					g.show_order(_order_text(g), true)
				if bool(g.get_meta("counter_first",false)):
					g.play("Idle_Talking_Loop")
				elif g.timer < _patience(g) * 0.22:
					g.play("Sitting_Talking_Loop")
				else:
					g.play("Sitting_Idle_Loop")
				if g.timer <= 0.0:
					kiosk_lost += 1
					combo = 0
					Core.add_rating(Economy.KIOSK_RATING_LOST)
					Core.toast.emit(tr("Um cliente cansou de esperar no quiosque. ★%.1f") % Economy.KIOSK_RATING_LOST, "bad")
					_leave(g)
			"kto_table":
				if not g.is_moving(): _sit_with_order(g,str(g.get_meta("pickup_dish")))
			"keat":
				var left: float = float(g.get_meta("eat", 0.0)) - dmin
				g.set_meta("eat", left)
				if left <= 0.0:
					_leave(g)
			"kleave":
				# O lugar continua reservado enquanto o cliente ainda está junto da cadeira.
				if not g.spot.is_empty() and g.position.distance_to(g.spot.pos) > 1.2:
					_release_spot(g)
				if not g.is_moving():
					_release_spot(g)
					customers.erase(g)
					Core.release_visual(g)

## Termina de ler o cardápio e faz o pedido (balão sobre a cabeça).
func _order(g, recorded: bool = false) -> void :
	g.show_menu(false)
	g.state = "kwait"
	g.timer = _patience(g)
	g.set_meta("order_taken", recorded or not Core.company_enabled())
	g.set_meta("urgent", false)
	g.show_order(_order_text(g))
	g.play("Idle_Talking_Loop" if bool(g.get_meta("counter_first",false)) else "Sitting_Talking_Loop")

## Sorteia o prato; em dia de calor coco e suco saem muito mais.
func _pick_dish(menu: Array) -> String:
	var total: = 0.0
	var ws: Array = []
	for d in menu:
		var w: = 2.5 if (Core.day_event == "calor" and (d == "coco_gelado" or d == "suco")) else 1.0
		if (Core.day_event == "junina" and d == "petiscos") or (Core.day_event == "show_dj" and d == "caipirinha") or (Core.day_event == "quermesse" and d == "suco"):
			w = 2.0
		# v0.9.5: na tempestade o povo quer comida quente e foge do coco gelado
		if Core.day_event == "tempestade":
			w = {"petiscos": 2.6, "coco_gelado": 0.35, "suco": 0.7}.get(d, 1.0)
		w *= Core.CompanyRules.Simulation.Management.dish_weight(Core, str(d))
		ws.append(w)
		total += w
	var r: = rng.randf() * total
	for i in menu.size():
		r -= float(ws[i])
		if r <= 0.0:
			return str(menu[i])
	return str(menu[menu.size() - 1])

## Famoso do dia: 85% de chance de ser alguém que ainda não está no álbum.
func _pick_vip() -> String:
	var fresh: Array = []
	for v in Economy.VIPS:
		if not Core.album.has(v.id):
			fresh.append(str(v.id))
	if not fresh.is_empty() and randf() < 0.85:
		return fresh[randi() % fresh.size()]
	return str(Economy.VIPS[randi() % Economy.VIPS.size()].id)

func _vip_name(id: String) -> String:
	for v in Economy.VIPS:
		if v.id == id:
			return str(v.name)
	return tr("Cliente VIP")

func _items(g) -> Array:
	return g.get_meta("items", [str(g.get_meta("dish", ""))])

## Pedidos maiores dão mais tempo para o cliente esperar.
func _patience(g) -> float:
	return KIOSK_PATIENCE * (1.8 if Core.company_enabled() else 1.0) * (1.0 + 0.45 * float(_items(g).size() - 1)) * (1.0 + Core.prog.eff("kiosk_patience"))

func _remaining(g) -> Array:
	return _items(g).slice(int(g.get_meta("delivered", 0)))

func _order_text(g) -> String:
	var names: Array = []
	for d in _remaining(g):
		if Economy.DISHES.has(d):
			names.append(tr(str(Economy.dish(d).name)))
	if names.is_empty():
		return "?"
	return ("★ " if g.get_meta("vip", false) else "") + " + ".join(names) + "!"

func _release_spot(g) -> void:
	if g.has_meta("dining_spot"):
		var dining: Dictionary = g.get_meta("dining_spot")
		if int(dining.get("owner",-1))==g.get_instance_id():
			dining.busy = false
			dining.erase("owner")
		g.remove_meta("dining_spot")
	for key in ["counter_slot","counter_departure"]:
		if g.has_meta(key): g.remove_meta(key)
	if g.spot.is_empty():
		return
	# Uma saída atrasada nunca libera o assento que já pertence a outro cliente.
	if int(g.spot.get("owner", g.get_instance_id())) == g.get_instance_id():
		g.spot.busy = false
		g.spot.erase("owner")
	g.spot = {}

func _leave(g) -> void :
	if Core.company_enabled() and g.state == "keat":
		get_parent().operations.mark_dirty(g)
	clear_served_visuals(g)
	if not prep.is_empty() and prep.get("g") == g:
		prep = {}
		_clear_prep_visual()
	var standing: bool = bool(g.get_meta("counter_first",false)) and g.state!="keat"
	g.play("Idle_Loop" if standing else "Sitting_Idle_Loop")
	g.show_menu(false)
	g.show_order("")
	g.state = "kleave"
	g.position.y = 0.1
	var exit: Vector3 = g.position if standing else g.spot.get("approach", g.position + Vector3(0, 0, 1.8))
	g.go([exit, world.kiosk_point(Vector3(-7.5,.1,12)), Vector3(rng.randf_range(44, 90), 0, rng.randf_range(-25, -21))])

func _next_customer():
	var w: = waiting_customers()
	if w.is_empty():
		return null
	# quem está para perder a paciência vai primeiro
	w.sort_custom( func(a, b): return a.timer < b.timer)
	return w[0]

func w0_vip(g) -> String:
	return str(g.get_meta("vip_id", ""))

func _bar(p: float) -> String:
	var n: = clampi(int(round(p * 8.0)), 0, 8)
	return "▰".repeat(n) + "▱".repeat(8 - n)

func kiosk_prompt() -> String:
	if Core.company_enabled():
		if not Core.company.receivables.is_empty():
			return "Caixa · receber %d contas" % Core.company.receivables.size()
		for index in Core.company.dirty_seats:
			if index < 2 and not world.kiosk_spots[index].busy:
				return "Recolher louça do balcão"
		return tr("Entre pela lateral · geladeira e cozinha dentro do quiosque")
	if not prep.is_empty():
		var st: Array = Economy.DISH_STAGES[prep.dish]
		return "%s  %s  (%d/%d)  ·  %s" % [tr(str(st[prep.stage][0])), _bar(float(prep.p)), int(prep.stage) + 1, st.size(), tr("segure E")]
	var g = _next_customer()
	if g == null:
		if customers.any(func(c): return c.state == "kchoose"):
			return tr("Cliente olhando o cardápio...")
		if not kiosk_open():
			return tr("Quiosque fechado · horário %02d:00–%02d:00") % [int(Core.kiosk_open_min() / 60.0), int(Core.kiosk_close_min() / 60.0)]
		return tr("Quiosque fechado · abra no computador do balcão") if not Core.kiosk_accepting_customers() else tr("Quiosque: aguardando clientes")
	var rem: Array = _remaining(g)
	var dish: String = str(rem[0])
	var d: Dictionary = Economy.dish(dish)
	if not Core.can_make(dish):
		return tr("Sem %s no estoque") % tr(str(d.name))
	var extra: = ""
	if rem.size() > 1:
		extra += "  +%d" % (rem.size() - 1)
	if g.get_meta("vip", false):
		extra += "  ★ " + _vip_name(str(w0_vip(g)))
	if combo >= 2:
		extra += "  ·  Combo x%d" % combo
	extra += "  ·  " + tr("Meta %d/%d") % [mini(served_today, daily_goal()), daily_goal()]
	return tr("Pegar %s (%s)") % [tr(str(d.name)), Core.fmt_money(Core.price_of(dish))] + extra

## Quantos clientes atender por dia para ganhar a meta: cresce com as expansões compradas.
func daily_goal() -> int:
	var n: = 0
	for id in Economy.EXPANSION_ORDER:
		if Core.has(id):
			n += 1
	return 8 + 2 * n

## Aperta E no balcão: começa o preparo do próximo prato; com o preparo andando, cada toque adianta um pedaço.
func kiosk_action() -> bool:
	if Core.company_enabled():
		if not Core.company.receivables.is_empty():
			get_parent().operations.collect_payments()
			return true
		for index in Core.company.dirty_seats.duplicate():
			if index < 2 and not world.kiosk_spots[index].busy:
				return Core.clean_company_seat(index)
		Core.toast.emit(kiosk_prompt(), "info")
		return false
	prep = {}
	var g = _next_customer()
	if g == null:
		return false
	return _deliver_item(g, str(_remaining(g)[0]))

func _stage_secs() -> float:
	if prep.is_empty():
		return 1.0
	return float(Economy.DISH_STAGES[prep.dish][prep.stage][1])

## Avança o preparo em "sec" segundos de trabalho (segurar E no jogo; o teste chama direto).
func prep_advance(sec: float) -> void :
	if prep.is_empty():
		return
	var stages: Array = Economy.DISH_STAGES[prep.dish]
	# v1.0: melhoria "Mãos rápidas" encurta cada etapa
	prep.p = float(prep.p) + sec / (float(stages[prep.stage][1]) * maxf(0.4, 1.0 - Core.prog.eff("kiosk_speed")))
	while float(prep.p) >= 1.0 and not prep.is_empty():
		prep.p = float(prep.p) - 1.0
		prep.stage = int(prep.stage) + 1
		get_tree().call_group("audio", "sfx", "click", -10.0, 1.0 + 0.12 * float(prep.stage))
		if int(prep.stage) >= stages.size():
			var g = prep.g
			var dish: String = prep.dish
			prep = {}
			_clear_prep_visual()
			_deliver_item(g, dish)
			return

## Entrega um prato do pedido; o último fecha o atendimento (nota, gorjeta, combo, meta).
func _deliver_item(g, dish: String, prepared: bool = false, by_staff: bool = false) -> bool:
	if not is_instance_valid(g) or g.is_queued_for_deletion() or g.state != "kwait" or dish not in _remaining(g):
		return false
	if Core.company_enabled() != prepared:
		return false
	if not prepared and not Core.can_make(dish):
		Core.note_stockout(dish)
		combo = 0
		_leave(g)
		return false
	var price: int = Core.sell_company_dish(dish, by_staff) if prepared else Core.sell_dish(dish, "kiosk")
	if price < 0:
		return false
	var items: Array = _items(g).duplicate()
	var delivered: int = int(g.get_meta("delivered", 0))
	var index: int = items.find(dish, delivered)
	var previous: String = str(items[delivered])
	items[delivered] = dish
	items[index] = previous
	g.set_meta("items", items)
	_show_delivered_visual(g, dish)
	g.set_meta("revenue", int(g.get_meta("revenue", 0)) + maxi(price, 0))
	g.set_meta("delivered", int(g.get_meta("delivered", 0)) + 1)
	get_tree().call_group("audio", "sfx", "glass", -8.0)
	if _remaining(g).is_empty():
		_complete_order(g, dish)
	else:
		g.show_order(_order_text(g), g.get_meta("urgent", false))
	return true

func _complete_order(g, last_dish: String) -> void :
	var fast: bool = g.timer > _patience(g) * 0.6
	var tip: = (2 if fast else 0) * _items(g).size()
	if Core.has("kiosk_tables") and fast:
		tip += 1
	if fast:   # v1.0: melhoria "Sorriso no balcão" e fama 3 (turistas dão gorjeta)
		tip += int(Core.prog.eff("tips")) + (1 if Core.prog.fame_level >= 3 else 0)
	# sequência: cada atendimento rápido seguido sobe o combo (até x5) e rende gorjeta extra
	if fast:
		combo = mini(combo + 1, COMBO_MAX)
		if combo >= 2:
			tip += combo - 1
			Core.toast.emit(tr("Combo x%d! +R$ %d de gorjeta") % [combo, tip], "good")
	else:
		combo = maxi(0, combo - 1)
	if Core.company.created:
		var social: float = Core.CompanyRules.Simulation.Management.profile_factor(Core, "atendente", "social")
		tip = int(round(tip * social))
	var adj: = Core.price_rating_adjust()
	Core.add_rating(clampf((Economy.KIOSK_RATING_FAST if fast else Economy.KIOSK_RATING_SLOW) + adj, 1.0, 5.0))
	if adj <= -0.3 and rng.randf() < 0.4:
		Core.toast.emit(tr("Cliente reclamou: \"Tá caro!\" Baixe os preços no Cardápio do computador."), "bad")
	var rev: = int(g.get_meta("revenue", 0))
	if g.get_meta("vip", false) and rev > 0:
		var vip_tip: = rev + 5
		Core.book(vip_tip, tr("Cliente VIP: gorjeta generosa"), "gorjeta", false)
		Core.add_rating(5.0)
		Core.toast.emit(tr("Cliente VIP encantado! +R$ %d de gorjeta") % vip_tip, "good")
		Core.vip_served(g.get_meta("vip_id", ""))
	if g.has_meta("regular"):
		var rid: String = g.get_meta("regular")
		var v: = int(regulars.get(rid, 0)) + 1
		regulars[rid] = v
		_save_regulars()
		tip += mini(v, 6)
		var rn: = str(REGULARS.filter(func(r): return r.id == rid)[0].name)
		if v in [3, 7, 15, 30]:
			Core.toast.emit(tr("%s já veio %d vezes: virou freguês fiel! Gorjeta maior a cada visita.") % [rn, v], "good")
			Core.add_rating(5.0)
	if tip > 0:
		Core.book(tip, tr("Gorjeta do quiosque"), "gorjeta", false)
	served_today += 1
	if not goal_paid and served_today >= daily_goal():
		goal_paid = true
		Core.book(GOAL_REWARD, tr("Meta do dia"), "missao", false)
		Core.toast.emit(tr("Meta do dia cumprida: %d clientes! +R$ %d") % [daily_goal(), GOAL_REWARD], "good")
	get_tree().call_group("audio", "sfx", "coin", -8.0)
	if bool(g.get_meta("counter_first",false)) and g.has_meta("dining_spot"):
		_walk_to_dining(g,last_dish)
		return
	# v0.7.1: o cliente fica sentado consumindo antes de ir embora (o lugar continua ocupado)
	g.position = g.spot.pos
	g.rotation.y = g.spot.rot
	g.show_order("")
	g.state = "keat"
	g.set_meta("eat", rng.randf_range(EAT_MIN.x, EAT_MIN.y))
	g.consume_dish(last_dish)

## Serve o pedido inteiro de uma vez (atendente contratado e testes).
func kiosk_serve() -> bool:
	if Core.company_enabled():
		return false
	var g = _next_customer()
	if g == null:
		return false
	prep = {}
	for d in _remaining(g).duplicate():
		if g.state != "kwait" or not _deliver_item(g, str(d)):
			return false
	return true

## Atendente contratado: serve o primeiro cliente esperando (chamado por Core a cada HELPER_MINUTES).
func helper_serve() -> void :
	if not kiosk_open() or waiting_customers().is_empty():
		return
	kiosk_serve()

func _on_slept(_d: int) -> void :
	_clear_prep_visual()
	for g in customers.duplicate():
		clear_served_visuals(g)
		_release_spot(g)
		customers.erase(g)
		Core.release_visual(g)
	kiosk_spawn_in = 10.0
	_dj_came = false
	combo = 0
	served_today = 0
	goal_paid = false
	rush_done = false
	rush_left = 0
	prep = {}
	fish = {}
	fish_casts = 0
	world.reset_coco_piles()

## Apresentação vinculada ao proprietário do pedido e à superfície do assento.
func _prep_position() -> Vector3:
	return world.kiosk_point(Vector3(0, 1.28, 1.85))

func _clear_prep_visual() -> void:
	if is_instance_valid(prep_visual):
		prep_visual.visible = false
		Core.release_visual(prep_visual)
	prep_visual = null

func _show_prep_visual(dish: String) -> void:
	_clear_prep_visual()
	prep_visual = DishPresentation.build(world, dish)
	if prep_visual != null:
		prep_visual.name = "PreparingDish"
		prep_visual.global_position = _prep_position()
		prep_visual.scale = Vector3.ONE * 0.85

func served_dishes(g) -> Array:
	var result: Array = []
	var root = g.get_meta("served_visuals") if g.has_meta("served_visuals") else null
	if is_instance_valid(root):
		for child in root.get_children():
			if child.has_meta("dish_id"):
				result.append(str(child.get_meta("dish_id")))
	return result

func clear_served_visuals(g) -> void:
	g.clear_held_order()
	for key in ["work_target","work_kind"]:
		if g.has_meta(key): g.remove_meta(key)
	var root = g.get_meta("served_visuals") if g.has_meta("served_visuals") else null
	if is_instance_valid(root):
		root.visible = false
		Core.release_visual(root)
	if g.has_meta("served_visuals"):
		g.remove_meta("served_visuals")

func _show_delivered_visual(g, dish: String, index_override: int = -1) -> void:
	var root = g.get_meta("served_visuals") if g.has_meta("served_visuals") else null
	if not is_instance_valid(root):
		root = Node3D.new()
		root.name = "ServedOrder_%d" % g.get_instance_id()
		root.set_meta("customer_id", g.get_instance_id())
		world.add_child(root)
		root.global_position = g.spot.get("serve_pos", _prep_position())
		root.rotation.y = float(g.spot.get("serve_rot", 0.0))
		g.set_meta("served_visuals", root)
		# Callable de método: não captura um Node em lambda que possa ser liberado.
		g.tree_exiting.connect(root.queue_free)
	var index: int = index_override if index_override>=0 else int(g.get_meta("delivered", 0))
	var count: int = _items(g).size()
	var food: Node3D = DishPresentation.build(root, dish)
	if food == null:
		return
	var target := Vector3((index - (count - 1) * 0.5) * 0.225, 0, 0)
	food.scale = Vector3.ONE * (0.72 if bool(g.spot.get("table", false)) else 0.86)
	if index_override>=0:
		food.position = target
		return
	food.position = root.to_local(_prep_position())
	var tween: Tween = food.create_tween()
	tween.tween_property(food, "position", target, 0.35).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
