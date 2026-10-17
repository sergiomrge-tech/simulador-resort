extends Node3D
## Vida da vila: moradores andando pelas calçadas, gente sentada na praça,
## Dona Rita na barraca, e os clientes do quiosque onde o herói trabalha.

const GuestScript := preload("res://scripts/guest.gd")
const KIOSK_OPEN := 8.0 * 60.0
const KIOSK_CLOSE := 18.0 * 60.0
const KIOSK_PATIENCE := 90.0      # min de jogo esperando no balcão

var world: Node3D
var enabled := true
var rng := RandomNumberGenerator.new()
var walkers: Array = []
var customers: Array = []
var kiosk_spawn_in := 10.0
var kiosk_lost := 0

func _ready() -> void:
	rng.seed = 7171
	var n_walk := 14 if Quality.hd else 6
	for i in n_walk:
		var g := _make()
		var path: Array = world.village_paths[i % world.village_paths.size()]
		g.set_meta("path", path)
		g.set_meta("dir", 1 if i % 2 == 0 else -1)
		var k := rng.randi() % path.size()
		g.set_meta("idx", k)
		g.set_meta("wait", rng.randf_range(0.0, 4.0))
		g.position = path[k]
		g.speed = rng.randf_range(0.95, 1.3)
		walkers.append(g)
	var sit_n := mini(3 if Quality.hd else 1, world.bench_spots.size())
	for i in sit_n:
		var s: Dictionary = world.bench_spots[i * 2 % world.bench_spots.size()]
		var g2 := _make()
		g2.position = s.pos + Vector3(sin(s.rot), 0, cos(s.rot)) * 0.12
		g2.rotation.y = s.rot
		g2.play("Sitting_Idle_Loop")
		g2.set_meta("sitter", true)
	# Dona Rita na barraca e o vendedor de tapioca
	var rita := _make()
	rita.position = world.village_points.barraca
	rita.rotation.y = 0.0
	rita.set_colors(Color(0.62, 0.42, 0.28), Color(0.95, 0.85, 0.3), Color(0.85, 0.3, 0.35), Color(0.08, 0.06, 0.05))
	rita.play("Idle_Talking_Loop")
	var cart := _make()
	cart.position = world.village_points.cart
	cart.rotation.y = -PI * 0.5
	cart.set_colors(Color(0.8, 0.58, 0.42), Color(0.9, 0.9, 0.88), Color(0.15, 0.25, 0.5), Color(0.3, 0.18, 0.08))
	cart.play("Idle_Loop")
	world.kiosk_counter.prompt_fn = kiosk_prompt
	world.kiosk_counter.action_fn = kiosk_serve
	Core.slept.connect(_on_slept)

func _make() -> Node3D:
	var g := Node3D.new()
	g.set_script(GuestScript)
	add_child(g)
	g.setup(9000 + get_child_count(), rng)
	return g

func _process(delta: float) -> void:
	var dmin := delta * Core.minutes_per_sec * Core.speed_mult
	var night := Core.minutes > 22.0 * 60.0 or Core.minutes < 5.5 * 60.0
	for i in walkers.size():
		var g: Node3D = walkers[i]
		var hide := night and i >= 3
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
		var nxt := idx + dir
		if nxt < 0 or nxt >= path.size():
			dir = -dir
			nxt = idx + dir
			g.set_meta("dir", dir)
			g.set_meta("wait", rng.randf_range(2.0, 7.0))
		g.set_meta("idx", nxt)
		var jitter := Vector3(rng.randf_range(-0.35, 0.35), 0, rng.randf_range(-0.35, 0.35))
		g.go([path[nxt] + jitter])
	_kiosk_tick(dmin)

# ------------------------------------------------------------------ quiosque
func kiosk_open() -> bool:
	return Core.minutes >= KIOSK_OPEN and Core.minutes < KIOSK_CLOSE

func waiting_customers() -> Array:
	return customers.filter(func(c): return c.state == "kwait")

func _free_spot() -> int:
	for i in world.kiosk_spots.size():
		if not world.kiosk_spots[i].busy:
			return i
	return -1

func spawn_customer() -> Node3D:
	var si := _free_spot()
	if si < 0:
		return null
	var g := _make()
	var from_beach := rng.randf() < 0.6
	var start: Vector3 = Vector3(rng.randf_range(46, 80), 0, rng.randf_range(-24, -21)) if from_beach else world.village_points.kiosk_approach[0]
	g.position = start
	var spot: Dictionary = world.kiosk_spots[si]
	spot.busy = true
	g.spot = spot
	g.state = "kwalk"
	g.timer = KIOSK_PATIENCE
	var dish: String = Economy.KIOSK_MENU[rng.randi() % Economy.KIOSK_MENU.size()]
	g.set_meta("dish", dish)
	var route: Array = [] if from_beach else world.village_points.kiosk_approach.slice(1)
	route.append(Vector3(spot.pos.x, 0.1, spot.pos.z + 0.85))
	g.go(route)
	customers.append(g)
	return g

func _kiosk_tick(dmin: float) -> void:
	if enabled and kiosk_open():
		kiosk_spawn_in -= dmin
		if kiosk_spawn_in <= 0.0:
			kiosk_spawn_in = rng.randf_range(22.0, 45.0)
			if waiting_customers().size() < 3:
				spawn_customer()
	for g in customers.duplicate():
		match g.state:
			"kwalk":
				if not g.is_moving():
					g.state = "kwait"
					g.position = g.spot.pos
					g.rotation.y = g.spot.rot
					g.play("Sitting_Idle_Loop")
			"kwait":
				g.timer -= dmin
				if g.timer < KIOSK_PATIENCE * 0.4:
					g.play("Sitting_Talking_Loop")
				if g.timer <= 0.0:
					kiosk_lost += 1
					Core.toast.emit(tr("Um cliente cansou de esperar no quiosque."), "bad")
					_leave(g)
			"kleave":
				if not g.is_moving():
					customers.erase(g)
					g.queue_free()

func _leave(g) -> void:
	g.spot.busy = false
	g.state = "kleave"
	g.position.y = 0.1
	g.go([g.position + Vector3(0, 0, 2.5), Vector3(rng.randf_range(44, 90), 0, rng.randf_range(-25, -21))])

func kiosk_prompt() -> String:
	var w := waiting_customers()
	if w.is_empty():
		if not kiosk_open():
			return tr("Quiosque fechado (abre 08:00–18:00)")
		return tr("Quiosque: aguardando clientes")
	var dish: String = str(w[0].get_meta("dish"))
	var d: Dictionary = Economy.dish(dish)
	if not Core.can_make(dish):
		return tr("Sem %s no estoque") % tr(str(d.name))
	return tr("Servir %s (%s)") % [tr(str(d.name)), Core.fmt_money(int(d.price))]

func kiosk_serve() -> bool:
	var w := waiting_customers()
	if w.is_empty():
		return false
	var g = w[0]
	var dish: String = str(g.get_meta("dish"))
	if not Core.can_make(dish):
		Core.note_stockout(dish)
		_leave(g)
		return false
	var tip := 2 if g.timer > KIOSK_PATIENCE * 0.6 else 0
	Core.sell_dish(dish, "kiosk")
	if tip > 0:
		Core.book(tip, tr("Gorjeta do quiosque"), "gorjeta", false)
	get_tree().call_group("audio", "sfx", "coin", -8.0)
	g.play("Interact")
	g.position = g.spot.pos
	_leave(g)
	return true

func _on_slept(_d: int) -> void:
	for g in customers.duplicate():
		g.spot.busy = false
		customers.erase(g)
		g.queue_free()
	kiosk_spawn_in = 10.0
