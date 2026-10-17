extends Node3D
## Gerencia chegada, fila, check-in, estadia, consumo e check-out dos hóspedes.

const GuestScript := preload("res://scripts/guest.gd")
const MAX_QUEUE := 4
const PATIENCE := 200.0          # min de jogo na fila antes de desistir

var world: Node3D
var guests: Array = []
var queue: Array = []
var rng := RandomNumberGenerator.new()
var next_id := 1
var spawn_in := 8.0             # min de jogo até o próximo hóspede
var enabled := true
var bartender: Node3D

func _ready() -> void:
	rng.seed = 2026
	Core.slept.connect(on_sleep)
	# barman fixo atrás do balcão
	bartender = _make_guest()
	bartender.position = world.points.bartender
	bartender.rotation.y = -PI * 0.5
	bartender.set_colors(Color(0.62, 0.42, 0.28), Color(0.95, 0.95, 0.92), Color(0.2, 0.2, 0.22), Color(0.08, 0.06, 0.05))
	bartender.play("Idle_Talking_Loop")
	world.desk.prompt_fn = desk_prompt
	world.desk.action_fn = checkin_front

func _make_guest() -> Node3D:
	var g := Node3D.new()
	g.set_script(GuestScript)
	add_child(g)
	g.setup(next_id, rng)
	next_id += 1
	return g

func _process(delta: float) -> void:
	var dmin := delta * Core.minutes_per_sec * Core.speed_mult
	if enabled:
		var h := Core.minutes / 60.0
		if h >= 7.0 and h < 21.0:
			spawn_in -= dmin
			if spawn_in <= 0.0:
				if queue.size() < MAX_QUEUE:
					spawn_guest()
				spawn_in = maxf(35.0, 110.0 - Core.stars() * 12.0) * rng.randf_range(0.8, 1.2)
	for g in guests.duplicate():
		_tick(g, dmin)

func spawn_guest() -> Node3D:
	var g := _make_guest()
	g.position = world.points.spawn
	g.state = "arrive"
	guests.append(g)
	queue.append(g)
	g.queue_idx = queue.size() - 1
	g.go([world.points.gate, world.points["queue%d" % mini(g.queue_idx, 3)]])
	if queue.size() == 1:
		Core.toast.emit(tr("%s chegou à recepção!") % g.gname, "info")
		get_tree().call_group("audio", "sfx", "bell")
	return g

func _refresh_queue() -> void:
	for i in queue.size():
		var g = queue[i]
		if g.queue_idx != i:
			g.queue_idx = i
			g.go([world.points["queue%d" % mini(i, 3)]])

func _tick(g, dmin: float) -> void:
	match g.state:
		"arrive", "queue":
			g.wait_min += dmin
			if not g.is_moving():
				g.state = "queue"
				g.play("Idle_Loop" if g.queue_idx > 0 else "Idle_Talking_Loop")
				g.rotation.y = PI    # olhando para o balcão (-Z)
			if g.wait_min > PATIENCE:
				_give_up(g)
		"to_room", "to_activity", "back_room", "leaving":
			if not g.is_moving():
				_arrive_state(g)
		"rest", "activity":
			g.timer -= dmin
			if g.timer <= 0.0:
				_next_activity(g)

func _arrive_state(g) -> void:
	match g.state:
		"to_room", "back_room":
			g.state = "rest"
			g.timer = rng.randf_range(35.0, 60.0)
			g.visible = false        # dentro do bangalô
		"to_activity":
			g.state = "activity"
			g.position = g.spot.pos
			g.rotation.y = g.spot.rot
			g.play(g.spot.anim)
			if g.spot in world.bar_spots:
				g.timer = rng.randf_range(30.0, 50.0)
				var drinks := rng.randi_range(1, 3)
				for k in drinks:
					Core.bar_sale(rng.randi_range(12, 24))
				get_tree().call_group("audio", "sfx", "glass")
			else:
				g.timer = rng.randf_range(60.0, 100.0)
		"leaving":
			guests.erase(g)
			g.queue_free()

func desk_prompt() -> String:
	if queue.is_empty():
		return ""
	var g = queue[0]
	if g.is_moving() or g.queue_idx != 0:
		return ""
	if Core.free_room() < 0:
		return tr("Sem bangalô limpo para %s") % g.gname
	return tr("Fazer check-in de %s") % g.gname

func checkin_front() -> bool:
	if queue.is_empty():
		return false
	var g = queue[0]
	if g.is_moving():
		return false
	var room := Core.free_room()
	if room < 0:
		Core.toast.emit(tr("Nenhum bangalô limpo! Limpe um bangalô primeiro."), "bad")
		return false
	queue.pop_front()
	_refresh_queue()
	g.room = room
	Core.occupy_room(room, g.gid)
	Core.add_money(Core.nightly_rate(), tr("Check-in %s (Bangalô %d)") % [g.gname, room + 1])
	get_tree().call_group("audio", "sfx", "coin")
	g.state = "to_room"
	g.plan = ["pool", "bar"]
	if rng.randf() < 0.5:
		g.plan = ["bar", "pool"]
	g.plan.append("rest")
	g.plan.append("checkout")
	g.go(world.route_to_room(room))
	if Core.tutorial_step < 1:
		Core.tutorial_step = 1
	return true

func _free_spot(list: Array) -> Dictionary:
	var free := []
	for s in list:
		if not s.busy:
			free.append(s)
	if free.is_empty():
		return {}
	return free[rng.randi() % free.size()]

func _release_spot(g) -> void:
	if not g.spot.is_empty():
		g.spot.busy = false
		g.spot = {}

func _next_activity(g) -> void:
	var from_room: bool = g.state == "rest"
	_release_spot(g)
	if g.plan.is_empty():
		g.plan = ["checkout"]
	var act: String = g.plan.pop_front()
	g.visible = true
	var start: Array = world.route_room_to_hub(g.room) if from_room else _back_to_hub(g)
	match act:
		"pool", "bar":
			var s := _free_spot(world.pool_spots if act == "pool" else world.bar_spots)
			if s.is_empty():
				_next_activity_fallback(g, from_room)
				return
			s.busy = true
			g.spot = s
			g.state = "to_activity"
			g.go(start + (world.route_hub_to_pool(s) if act == "pool" else world.route_hub_to_bar(s)))
		"rest":
			if from_room:
				g.state = "rest"
				g.timer = rng.randf_range(40.0, 70.0)
				g.visible = false
			else:
				g.state = "back_room"
				g.go(start + world.route_hub_to_room(g.room))
		"checkout":
			_checkout(g, start)

func _next_activity_fallback(g, from_room: bool) -> void:
	if from_room:
		g.state = "rest"
		g.timer = 30.0
		g.visible = false
	else:
		g.state = "back_room"
		g.go(_back_to_hub(g) + world.route_hub_to_room(g.room))

func _back_to_hub(g) -> Array:
	# volta do ponto atual (piscina/bar) até o hub oeste
	var p: Vector3 = g.position
	if p.y < -0.2:
		return [Vector3(p.x, -0.6, 0.6), Vector3(p.x, 0.12, -0.6), world.points.deck_s, world.points.hub_sw]
	if p.z < -6.0 and p.x > 8.0:   # bar
		var near: Vector3 = p + (p - world.BAR_C).normalized() * 0.9
		return [near, world.points.walk_bar, world.points.deck_se, world.points.deck_s, world.points.hub_sw]
	if p.x > 0.0:
		return [Vector3(8.6, 0.12, p.z), Vector3(8.6, 0.12, -2.2), world.points.deck_s, world.points.hub_sw]
	return [Vector3(-10.5, 0, p.z), world.points.hub_sw]

func _checkout(g, start: Array) -> void:
	var rating := 5.0
	rating -= maxf(0.0, (g.wait_min - 30.0) / 45.0)
	rating += Core.redes * 0.15
	rating += rng.randf_range(-0.4, 0.3)
	rating = clampf(rating, 1.0, 5.0)
	var tip := int(round(rating * 4.0))
	Core.vacate_room(g.room)
	Core.add_rating(rating)
	Core.guests_served += 1
	Core.add_money(tip, tr("%s fez check-out ★%.1f, gorjeta") % [g.gname, rating])
	get_tree().call_group("audio", "sfx", "coin")
	g.state = "leaving"
	g.room = -1
	var r: Array = start.duplicate()
	r.append_array([world.points.hub_nw, world.points.hub_w_exit, world.points.exit_join, world.points.spawn])
	g.go(r)

func _give_up(g) -> void:
	queue.erase(g)
	_refresh_queue()
	Core.add_rating(1.5)
	Core.toast.emit(tr("%s cansou de esperar e foi embora ★1.5") % g.gname, "bad")
	g.state = "leaving"
	g.go([world.points.gate, world.points.spawn])

func queue_size() -> int:
	return queue.size()

## O herói dormiu: quem estava hospedado faz check-out de manhã cedo (quarto fica sujo),
## quem estava na fila foi procurar outra pousada (sem penalidade).
func on_sleep(_day: int) -> void:
	var outs := 0
	var total := 0
	for g in guests.duplicate():
		if g.room >= 0:
			_release_spot(g)
			var rating := clampf(4.6 - maxf(0.0, (g.wait_min - 30.0) / 45.0) + Core.redes * 0.15 + rng.randf_range(-0.4, 0.3), 1.0, 5.0)
			Core.vacate_room(g.room)
			Core.add_rating(rating)
			Core.guests_served += 1
			var tip := int(round(rating * 4.0))
			Core.money += tip
			total += tip
			outs += 1
		guests.erase(g)
		g.queue_free()
	queue.clear()
	spawn_in = 30.0
	Core.money_changed.emit(Core.money)
	if outs > 0:
		Core.toast.emit(tr("Durante a noite, %d hóspede(s) fizeram check-out. Gorjetas %s") % [outs, Core.fmt_money(total, true)], "money")
