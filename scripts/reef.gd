extends Node3D
## Recife de coral e peixes na água rasa (para o mergulho de snorkel). Corais e peixes vêm do Blender (g:coral_*, g:fish_*).
## Os cardumes nadam em círculos lentos em volta de cada canteiro; a cauda ("Tail") balança.
## (sem class_name: carregado por caminho em world.gd)

var world: Node3D
var rng := RandomNumberGenerator.new()
var _fish: Array = []
var _t := 0.0

const PATCHES := [Vector3(26, 0, -47), Vector3(38, 0, -49), Vector3(50, 0, -46), Vector3(62, 0, -50), Vector3(84, 0, -47), Vector3(94, 0, -50), Vector3(104, 0, -46), Vector3(14, 0, -49)]
const CORALS := ["g:coral_branch_a", "g:coral_branch_b", "g:coral_branch_c", "g:coral_table", "g:coral_brain", "g:sea_fan"]
const SPECIES := [["g:fish_clown", 0.2], ["g:fish_blue", 0.28], ["g:fish_angel", 0.3], ["g:fish_silver", 0.36]]

func setup(w: Node3D) -> void :
	world = w
	name = "Reef"
	rng.seed = 5150
	var per: = 7 if Quality.hd else 3
	var schools: = 2 if Quality.hd else 1
	for pi in PATCHES.size():
		var c: Vector3 = PATCHES[pi]
		for k in per:
			var p: = c + Vector3(rng.randf_range(-3.5, 3.5), 0, rng.randf_range(-1.8, 1.8))
			p.y = float(world.call("_height", p.x, p.z)) - 0.02
			var key: String = CORALS[rng.randi() % CORALS.size()]
			var tint: = Color.from_hsv(rng.randf(), rng.randf_range(0.0, 0.15), rng.randf_range(0.9, 1.0))
			Real.place(self, key, p, -rng.randf_range(0.9, 1.7), rng.randf() * TAU, tint, 0.0, false)
		for s in schools:
			var sp: Array = SPECIES[(pi + s) % SPECIES.size()]
			var n: = rng.randi_range(4, 7) if Quality.hd else rng.randi_range(2, 4)
			var cx: = c + Vector3(rng.randf_range(-1.5, 1.5), 0, rng.randf_range(-1.5, 1.5))
			var base_y: = float(world.call("_height", cx.x, cx.z)) + rng.randf_range(0.25, 0.5)
			var rad: = rng.randf_range(1.2, 2.4)
			var spd: = rng.randf_range(0.25, 0.5) * (1.0 if rng.randf() < 0.5 else -1.0)
			for i in n:
				var f: = Node3D.new()
				add_child(f)
				var h: = Real.place(f, sp[0], Vector3.ZERO, -rng.randf_range(2.2, 3.4), 0.0, Color(0.62, 0.64, 0.7), 0.0, true)
				if h == null:
					f.queue_free()
					continue
				var tail: Node3D = null
				for nd in f.find_children("Tail", "Node3D", true, false):
					tail = nd
				_fish.append({"n": f, "tail": tail, "c": Vector3(cx.x, base_y, cx.z), "r": rad * rng.randf_range(0.8, 1.2), "w": spd * rng.randf_range(0.85, 1.15), "ph": rng.randf() * TAU, "yb": rng.randf_range(-0.2, 0.2)})

func _ready() -> void :
	# vistos de longe pela água viravam "sujeira" na superfície: só aparecem perto (mergulho/snorkel)
	call_deferred("_limit_range")

func _limit_range() -> void :
	for mi in find_children("*", "GeometryInstance3D", true, false):
		(mi as GeometryInstance3D).visibility_range_end = 16.0
		(mi as GeometryInstance3D).visibility_range_end_margin = 3.0
		(mi as GeometryInstance3D).visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF

func _process(delta: float) -> void :
	_t += delta
	for d in _fish:
		var f: Node3D = d.n
		var a: float = d.ph + _t * d.w
		var pos: Vector3 = d.c + Vector3(cos(a) * d.r, d.yb + sin(a * 1.7 + d.ph) * 0.12, sin(a) * d.r * 0.7)
		var vel: = Vector3(-sin(a) * d.w * d.r, 0, cos(a) * d.w * d.r * 0.7)
		# o cardume foge de quem mergulha perto (2,5 m) e volta devagar depois
		var pl: Node3D = Core.player_ref
		var flee: Vector3 = d.get("flee", Vector3.ZERO)
		if is_instance_valid(pl):
			var away: Vector3 = (pos + flee) - pl.global_position - Vector3(0, 1.4, 0)
			if away.length() < 2.5:
				flee += away.normalized() * delta * 3.0
		flee = flee.lerp(Vector3.ZERO, delta * 0.4)
		d["flee"] = flee
		f.position = pos + flee
		var mv: Vector3 = vel + flee * 4.0
		f.rotation.y = atan2(mv.x, mv.z)
		var tl: Node3D = d.tail
		if tl:
			tl.rotation.y = sin(_t * 9.0 + d.ph) * 0.45
