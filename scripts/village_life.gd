extends Node3D



const GuestScript: = preload("res://scripts/guest.gd")
const KIOSK_OPEN: = 8.0 * 60.0
const KIOSK_CLOSE: = 18.0 * 60.0
const KIOSK_PATIENCE: = 90.0
## Minutos de jogo que o cliente passa lendo o cardápio antes de pedir.
const CHOOSE_MIN: = Vector2(4.0, 9.0)
## Minutos de jogo comendo/bebendo depois de servido.
const EAT_MIN: = Vector2(14.0, 26.0)

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
const GOAL_REWARD: = 40
var combo: = 0
var served_today: = 0
var goal_paid: = false
var rush_done: = false
var rush_left: = 0

func _ready() -> void :
	add_to_group("kiosk")
	rng.seed = 7171
	var n_walk: = 12 if Quality.hd else 5
	for i in n_walk:
		var g: = _make()
		var path: Array = world.village_paths[i % world.village_paths.size()]
		g.set_meta("path", path)
		g.set_meta("dir", 1 if i % 2 == 0 else -1)
		var k: = rng.randi() % path.size()
		g.set_meta("idx", k)
		g.set_meta("wait", rng.randf_range(0.0, 4.0))
		g.position = path[k]
		g.speed = rng.randf_range(0.95, 1.3)
		walkers.append(g)
	var sit_n: = mini(3 if Quality.hd else 1, world.bench_spots.size())
	for i in sit_n:
		var s: Dictionary = world.bench_spots[i * 2 % world.bench_spots.size()]
		var g2: = _make()
		g2.position = s.pos + Vector3(sin(s.rot), 0, cos(s.rot)) * 0.12
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
	world.kiosk_counter.prompt_fn = kiosk_prompt
	world.kiosk_counter.action_fn = kiosk_serve
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
		var hide: = night and i >= 3
		g.visible = not hide
		if hide:
			continue
		if g.is_moving():
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
	_kiosk_tick(dmin)

func _outside_blocks(p: Vector3) -> Vector3:
	var rects: Array = world.block_rects
	var q: = p
	for _pass in 2:
		for r in rects:
			var rect: Rect2 = r
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
	return Core.minutes >= KIOSK_OPEN and Core.minutes < Core.kiosk_close_min()

func waiting_customers() -> Array:
	return customers.filter( func(c): return c.state == "kwait")

func _free_spot() -> int:
	var free: = []
	for i in world.kiosk_spots.size():
		var sp: Dictionary = world.kiosk_spots[i]
		var need: = str(sp.get("need", ""))
		if not sp.busy and (need == "" or Core.has(need)):
			free.append(i)
	if free.is_empty():
		return -1
	return free[rng.randi() % free.size()]

func spawn_customer() -> Node3D:
	var si: = _free_spot()
	if si < 0:
		return null
	var g: = _make()
	var from_beach: = rng.randf() < 0.6
	var start: Vector3 = Vector3(rng.randf_range(46, 80), 0, rng.randf_range(-24, -21)) if from_beach else world.village_points.kiosk_approach[0]
	g.position = start
	var spot: Dictionary = world.kiosk_spots[si]
	spot.busy = true
	g.spot = spot
	g.state = "kwalk"
	g.timer = KIOSK_PATIENCE
	var menu: Array = Core.kiosk_menu()
	var dish: String = str(menu[rng.randi() % menu.size()])
	g.set_meta("dish", dish)
	if rng.randf() < VIP_CHANCE and Core.stars() >= 3.0:
		g.set_meta("vip", true)
	var route: Array = [] if from_beach else world.village_points.kiosk_approach.slice(1)
	if from_beach:
		# contorna o quiosque pela lateral em vez de atravessar o balcão
		var kc: Vector3 = world.KIOSK_C
		var sx: = 1.0 if start.x >= kc.x else -1.0
		route.append(Vector3(kc.x + sx * 5.2, 0.05, kc.z - 3.8))
		route.append(Vector3(kc.x + sx * 5.2, 0.05, kc.z + 3.6))
	var front: Vector3 = Vector3(spot.pos.x, 0.1, spot.pos.z) if spot.get("table", false) else Vector3(spot.pos.x, 0.1, spot.pos.z + 0.85)
	route.append(front)
	g.go(route)
	customers.append(g)
	return g

func _kiosk_tick(dmin: float) -> void :
	# v0.7.1: depois do horário ninguém mais chega, e quem estava esperando vai embora (sem perder estrela)
	if not kiosk_open():
		var sent: = 0
		for g in customers:
			if g.state in ["kwalk", "kchoose", "kwait", "keat"]:
				_leave(g)
				sent += 1
		if sent > 0 and Core.in_game:
			Core.toast.emit(tr("Quiosque fechado por hoje. Os últimos clientes foram embora."), "info")
	if enabled and kiosk_open():
		kiosk_spawn_in -= dmin
		if kiosk_spawn_in <= 0.0:
			var rngv: Vector2 = Economy.KIOSK_SPAWN_TABLES if Core.has("kiosk_tables") else Economy.KIOSK_SPAWN
			kiosk_spawn_in = rng.randf_range(rngv.x, rngv.y)
			if rush_left > 0:
				rush_left -= 1
				kiosk_spawn_in = rng.randf_range(2.5, 5.0)
			if waiting_customers().size() < world.kiosk_spots.size():
				spawn_customer()
		# ônibus de turistas: uma vez por dia, entre 11h e 15h, com o quiosque já rodando
		if not rush_done and Core.in_game and Core.minutes >= 11.0 * 60.0 and Core.minutes <= 15.0 * 60.0 and served_today >= 3:
			if rng.randf() < dmin * 0.004:
				rush_done = true
				rush_left = 4
				kiosk_spawn_in = 1.5
				Core.toast.emit(tr("Chegou um ônibus de turistas! Vem gente: sirva rápido para manter o combo."), "good")
	for g in customers.duplicate():
		match g.state:
			"kwalk":
				if not g.is_moving():
					# senta e olha o cardápio antes de pedir
					g.state = "kchoose"
					g.position = g.spot.pos
					g.rotation.y = g.spot.rot
					g.play("Sitting_Idle_Loop")
					g.set_meta("choose", rng.randf_range(CHOOSE_MIN.x, CHOOSE_MIN.y))
					g.show_menu(true)
			"kchoose":
				var ch: float = float(g.get_meta("choose", 0.0)) - dmin
				g.set_meta("choose", ch)
				if ch <= 0.0:
					_order(g)
			"kwait":
				g.timer -= dmin
				var urgent: bool = g.timer < KIOSK_PATIENCE * 0.3
				if urgent and not g.get_meta("urgent", false):
					g.set_meta("urgent", true)
					g.show_order(_order_text(g), true)
				if g.timer < KIOSK_PATIENCE * 0.22:
					g.play("Sitting_Talking_Loop")
				else:
					g.play("Sitting_Idle_Loop")
				if g.timer <= 0.0:
					kiosk_lost += 1
					combo = 0
					Core.add_rating(Economy.KIOSK_RATING_LOST)
					Core.toast.emit(tr("Um cliente cansou de esperar no quiosque. ★%.1f") % Economy.KIOSK_RATING_LOST, "bad")
					_leave(g)
			"keat":
				var left: float = float(g.get_meta("eat", 0.0)) - dmin
				g.set_meta("eat", left)
				if left <= 0.0:
					_leave(g)
			"kleave":
				if not g.is_moving():
					customers.erase(g)
					g.queue_free()

## Termina de ler o cardápio e faz o pedido (balão sobre a cabeça).
func _order(g) -> void :
	g.show_menu(false)
	g.state = "kwait"
	g.timer = KIOSK_PATIENCE
	g.set_meta("urgent", false)
	g.show_order(_order_text(g))
	g.play("Sitting_Talking_Loop")

func _order_text(g) -> String:
	var dish: = str(g.get_meta("dish", ""))
	if dish == "" or not Economy.DISHES.has(dish):
		return "?"
	return ("★ " if g.get_meta("vip", false) else "") + tr(str(Economy.dish(dish).name)) + "!"

func _leave(g) -> void :
	g.play("Sitting_Idle_Loop")
	g.show_menu(false)
	g.show_order("")
	g.spot.busy = false
	g.state = "kleave"
	g.position.y = 0.1
	g.go([g.position + Vector3(0, 0, 2.5), Vector3(rng.randf_range(44, 90), 0, rng.randf_range(-25, -21))])

func kiosk_prompt() -> String:
	var w: = waiting_customers()
	if w.is_empty():
		if customers.any(func(c): return c.state == "kchoose"):
			return tr("Cliente olhando o cardápio...")
		if not kiosk_open():
			return tr("Quiosque fechado (abre 08:00–18:00)")
		return tr("Quiosque: aguardando clientes")
	var dish: String = str(w[0].get_meta("dish"))
	var d: Dictionary = Economy.dish(dish)
	if not Core.can_make(dish):
		return tr("Sem %s no estoque") % tr(str(d.name))
	var extra: = ""
	if w[0].get_meta("vip", false):
		extra += "  ★ VIP"
	if combo >= 2:
		extra += "  ·  Combo x%d" % combo
	extra += "  ·  " + tr("Meta %d/%d") % [mini(served_today, daily_goal()), daily_goal()]
	return tr("Servir %s (%s)") % [tr(str(d.name)), Core.fmt_money(int(d.price))] + extra

## Quantos clientes atender por dia para ganhar a meta: cresce com as expansões compradas.
func daily_goal() -> int:
	var n: = 0
	for id in Economy.EXPANSION_ORDER:
		if Core.has(id):
			n += 1
	return 8 + 2 * n

func kiosk_serve() -> bool:
	var w: = waiting_customers()
	if w.is_empty():
		return false
	var g = w[0]
	var dish: String = str(g.get_meta("dish"))
	if not Core.can_make(dish):
		Core.note_stockout(dish)
		_leave(g)
		return false
	var fast: bool = g.timer > KIOSK_PATIENCE * 0.6
	var tip: = 2 if fast else 0
	if Core.has("kiosk_tables") and fast:
		tip += 1
	# sequência: cada atendimento rápido seguido sobe o combo (até x5) e rende gorjeta extra
	if fast:
		combo = mini(combo + 1, COMBO_MAX)
		if combo >= 2:
			tip += combo - 1
			Core.toast.emit(tr("Combo x%d! +R$ %d de gorjeta") % [combo, tip], "good")
	else:
		combo = maxi(0, combo - 1)
	var price: = Core.sell_dish(dish, "kiosk")
	Core.add_rating(Economy.KIOSK_RATING_FAST if fast else Economy.KIOSK_RATING_SLOW)
	if g.get_meta("vip", false) and price > 0:
		var vip_tip: = price + 5
		Core.book(vip_tip, tr("Cliente VIP: gorjeta generosa"), "gorjeta", false)
		Core.add_rating(5.0)
		Core.toast.emit(tr("Cliente VIP encantado! +R$ %d de gorjeta") % vip_tip, "good")
	if tip > 0:
		Core.book(tip, tr("Gorjeta do quiosque"), "gorjeta", false)
	served_today += 1
	if not goal_paid and served_today >= daily_goal():
		goal_paid = true
		Core.book(GOAL_REWARD, tr("Meta do dia"), "missao", false)
		Core.toast.emit(tr("Meta do dia cumprida: %d clientes! +R$ %d") % [daily_goal(), GOAL_REWARD], "good")
	get_tree().call_group("audio", "sfx", "coin", -8.0)
	# v0.7.1: o cliente fica sentado consumindo antes de ir embora (o lugar continua ocupado)
	g.position = g.spot.pos
	g.rotation.y = g.spot.rot
	g.show_order("")
	g.state = "keat"
	g.set_meta("eat", rng.randf_range(EAT_MIN.x, EAT_MIN.y))
	g.consume(dish != "petiscos")
	return true

## Atendente contratado: serve o primeiro cliente esperando (chamado por Core a cada HELPER_MINUTES).
func helper_serve() -> void :
	if not kiosk_open() or waiting_customers().is_empty():
		return
	kiosk_serve()

func _on_slept(_d: int) -> void :
	for g in customers.duplicate():
		g.spot.busy = false
		customers.erase(g)
		g.queue_free()
	kiosk_spawn_in = 10.0
	combo = 0
	served_today = 0
	goal_paid = false
	rush_done = false
	rush_left = 0
