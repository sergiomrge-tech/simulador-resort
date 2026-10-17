extends Node3D
## Hóspede: segue rotas de waypoints e troca de animação conforme o estado.

signal arrived

const SKINS := [Color(0.95, 0.78, 0.62), Color(0.80, 0.58, 0.42), Color(0.62, 0.42, 0.28), Color(0.42, 0.28, 0.18)]
const SHIRTS := [Color(0.95, 0.45, 0.2), Color(0.15, 0.55, 0.75), Color(0.95, 0.85, 0.3), Color(0.9, 0.9, 0.88), Color(0.85, 0.25, 0.35), Color(0.3, 0.7, 0.45), Color(0.55, 0.35, 0.7)]
const SHORTS := [Color(0.15, 0.25, 0.5), Color(0.85, 0.8, 0.65), Color(0.2, 0.2, 0.22), Color(0.3, 0.55, 0.65), Color(0.75, 0.3, 0.2)]
const HAIRS := [Color(0.08, 0.06, 0.05), Color(0.3, 0.18, 0.08), Color(0.75, 0.6, 0.35), Color(0.55, 0.55, 0.55)]
const NAMES := ["Ana", "João", "Maria", "Pedro", "Luiza", "Rafael", "Camila", "Bruno", "Juliana", "Thiago", "Beatriz", "Lucas", "Fernanda", "Gabriel", "Larissa", "Diego"]

static var _scene: PackedScene
static var _mat: ShaderMaterial

var gid := 0
var gname := "Hóspede"
var state := "arrive"
var room := -1
var wait_min := 0.0       # tempo de espera na fila (min de jogo)
var timer := 0.0          # min de jogo restantes no estado atual
var plan: Array = []      # atividades restantes
var spot: Dictionary = {}
var queue_idx := -1
var speed := 1.35
var _route: Array = []
var _ideal := Vector3.ZERO   # posição na rota, antes do desvio lateral
var _stuck := 0.0
var _prev_dist := INF
var _anim: AnimationPlayer
var _cur_anim := ""
var _mesh_insts: Array = []

const NPC_RADIUS := 0.62
const IDLE_RADIUS := 0.42
const PLAYER_RADIUS := 0.72
const MAX_SIDESTEP := 0.55
const POOL_PAD := 1.45          # deck em volta da água (world.gd POOL_MIN/MAX)

func setup(id: int, rng: RandomNumberGenerator) -> void:
	gid = id
	gname = NAMES[rng.randi() % NAMES.size()]
	if _scene == null:
		_scene = load("res://assets/models/ual/guest.glb")
		_mat = ShaderMaterial.new()
		_mat.shader = load("res://shaders/guest.gdshader")
	var m: Node3D = _scene.instantiate()
	add_child(m)
	for mi in m.find_children("*", "MeshInstance3D", true, false):
		mi.material_override = _mat
		_mesh_insts.append(mi)
	set_colors(SKINS[rng.randi() % SKINS.size()], SHIRTS[rng.randi() % SHIRTS.size()], SHORTS[rng.randi() % SHORTS.size()], HAIRS[rng.randi() % HAIRS.size()])
	var aps := m.find_children("*", "AnimationPlayer", true, false)
	if aps.size() > 0:
		_anim = aps[0]
		for an in _anim.get_animation_list():
			if an.ends_with("_Loop"):
				_anim.get_animation(an).loop_mode = Animation.LOOP_LINEAR
	speed = rng.randf_range(1.2, 1.5)
	add_to_group("npc")
	_ideal = position
	play("Idle_Loop")

func set_colors(skin: Color, shirt: Color, shorts: Color, hair: Color) -> void:
	for mi in _mesh_insts:
		mi.set_instance_shader_parameter("skin", skin)
		mi.set_instance_shader_parameter("shirt", shirt)
		mi.set_instance_shader_parameter("shorts", shorts)
		mi.set_instance_shader_parameter("hair", hair)

func play(an: String) -> void:
	if _anim == null:
		return
	# o importador do Godot remove o sufixo _Loop (e já marca a animação como loop)
	if not _anim.has_animation(an) and an.ends_with("_Loop"):
		an = an.trim_suffix("_Loop")
	if an == _cur_anim:
		return
	if _anim.has_animation(an):
		_anim.play(an, 0.25)
		_cur_anim = an
		_anim.speed_scale = clampf(Core.speed_mult, 1.0, 4.0)

func go(route: Array) -> void:
	_ideal = position
	_stuck = 0.0
	_prev_dist = INF
	_route = _expand_route(route)
	if not _route.is_empty():
		play("Swim_Fwd_Loop" if _in_water_motion() else "Walk_Loop")

func is_moving() -> bool:
	return not _route.is_empty()

func _process(delta: float) -> void:
	if _route.is_empty():
		return
	var target: Vector3 = _route[0]
	var to := target - _ideal
	var step := speed * delta * Core.speed_mult
	var flat := Vector3(to.x, 0, to.z)
	var dist := flat.length()
	if dist <= step and absf(to.y) <= step + 0.001:
		# Um passo grande não pode atravessar a água. Se a reta corta a piscina, insere a volta pelo deck.
		var detoured := false
		if _segment_needs_detour(_ideal, target):
			var extra := _detour(_ideal, target)
			var useful := false
			for w in extra:
				var wp: Vector3 = w
				if wp.distance_squared_to(_ideal) > 0.05 and wp.distance_squared_to(target) > 0.05:
					useful = true
					break
			if useful:
				for i in range(extra.size() - 1, -1, -1):
					_route.insert(0, extra[i])
				detoured = true
		if detoured:
			target = _route[0]
			to = target - _ideal
			flat = Vector3(to.x, 0, to.z)
			dist = flat.length()
		else:
			_ideal = target
			_route.pop_front()
			if _route.is_empty():
				position = target
				arrived.emit()
				return
			target = _route[0]
			to = target - _ideal
			flat = Vector3(to.x, 0, to.z)
			dist = flat.length()
	if dist > 0.001:
		var adv := minf(step, dist)
		var nxt_ideal := _ideal + Vector3(flat.x / dist, 0.0, flat.z / dist) * adv
		nxt_ideal.y = _ideal.y + to.y * (adv / dist)
		if not _waypoint_is_swim(target):
			nxt_ideal = _slide_out_of_pool(_ideal, nxt_ideal)
		_ideal = nxt_ideal
	if not _route.is_empty():
		var dnow := _ideal.distance_to(_route[0])
		if dnow < _prev_dist - 0.02:
			_prev_dist = dnow
			_stuck = 0.0
		else:
			_stuck += delta
			if _stuck > 0.35 and _segment_needs_detour(_ideal, _route[0]):
				var around := _detour(_ideal, _route[0])
				var first_ok := false
				if not around.is_empty():
					var first: Vector3 = around[0]
					first_ok = not _segment_needs_detour(_ideal, first)
				if first_ok:
					for i in range(around.size() - 1, -1, -1):
						_route.insert(0, around[i])
				_stuck = 0.0
				_prev_dist = INF
		if not _route.is_empty():
			target = _route[0]
	var swimming := _in_water_motion()
	play("Swim_Fwd_Loop" if swimming else "Walk_Loop")
	var desired := _ideal
	if not swimming:
		var sep := _separation()
		if sep.length() > 0.001:
			var travel := flat
			var offset := sep
			if travel.length() > 0.15:
				var tdir := travel.normalized()
				offset -= tdir * offset.dot(tdir)
			if offset.length() > MAX_SIDESTEP:
				offset = offset.normalized() * MAX_SIDESTEP
			desired = _ideal + offset
			desired.y = _ideal.y
			desired = _slide_out_of_pool(_ideal, desired)
	var blend := minf(1.0, delta * 10.0 * maxf(Core.speed_mult, 1.0))
	var nxt := position.lerp(desired, blend)
	if not swimming:
		nxt = _slide_out_of_pool(position, nxt)
	var face := nxt - position
	face.y = 0
	if face.length() < 0.02:
		face = target - position
		face.y = 0
	if face.length() > 0.02:
		var yaw := atan2(face.x, face.z)
		rotation.y = lerp_angle(rotation.y, yaw, minf(1.0, delta * 8.0 * maxf(Core.speed_mult, 1.0)))
	position = nxt

# ------------------------------------------------------------------ desvio e piscina
func _world() -> Node:
	var p := get_parent()
	if p != null and "world" in p and p.world != null:
		return p.world
	return null

func _pool_rect() -> Rect2:
	var w := _world()
	if w == null:
		return Rect2()
	var mn: Vector2 = w.POOL_MIN
	var mx: Vector2 = w.POOL_MAX
	return Rect2(mn, mx - mn)

func _has_pool() -> bool:
	return _world() != null

func _in_pool(pt: Vector3) -> bool:
	if not _has_pool():
		return false
	var r := _pool_rect()
	var inner := r.grow(-0.04)
	return inner.has_point(Vector2(pt.x, pt.z))

func _hits_pool(a: Vector3, b: Vector3) -> bool:
	if not _has_pool():
		return false
	var r := _pool_rect().grow(-0.04)
	var mn := r.position
	var mx := r.position + r.size
	var dx := b.x - a.x
	var dz := b.z - a.z
	var t0 := 0.0
	var t1 := 1.0
	var ps := PackedFloat32Array([-dx, dx, -dz, dz])
	var qs := PackedFloat32Array([a.x - mn.x, mx.x - a.x, a.z - mn.y, mx.y - a.z])
	for i in 4:
		if absf(ps[i]) < 0.00001:
			if qs[i] < 0.0:
				return false
		else:
			var u: float = qs[i] / ps[i]
			if ps[i] < 0.0:
				if u > t1:
					return false
				t0 = maxf(t0, u)
			else:
				if u < t0:
					return false
				t1 = minf(t1, u)
	return t0 <= t1

func _dist_outside_pool(pt: Vector3) -> float:
	var r := _pool_rect()
	var mn := r.position
	var mx := r.position + r.size
	var dx := maxf(mn.x - pt.x, maxf(0.0, pt.x - mx.x))
	var dz := maxf(mn.y - pt.z, maxf(0.0, pt.z - mx.y))
	return Vector2(dx, dz).length()

## Passo curto pela borda (entrada/saída da água). Travessia longa a pé é bloqueada.
func _rim_step(outside: Vector3, inside: Vector3) -> bool:
	return _dist_outside_pool(outside) <= 1.6 and outside.distance_to(inside) <= 3.2

func _segment_needs_detour(a: Vector3, b: Vector3) -> bool:
	if not _hits_pool(a, b):
		return false
	var a_in := _in_pool(a)
	var b_in := _in_pool(b)
	if a_in and b_in:
		return false
	if a_in and _rim_step(b, a):
		return false
	if b_in and _rim_step(a, b):
		return false
	return true

func _expand_route(route: Array) -> Array:
	var out: Array = []
	var cursor := position
	for raw in route:
		var pt: Vector3 = raw
		if _segment_needs_detour(cursor, pt):
			for w in _detour(cursor, pt):
				_push_pt(out, w)
		_push_pt(out, pt)
		cursor = pt
	return out

func _push_pt(out: Array, p: Vector3) -> void:
	if out.is_empty() or (out[out.size() - 1] as Vector3).distance_squared_to(p) > 0.04:
		out.append(p)

func _rim_outside(p: Vector3) -> Vector3:
	var r := _pool_rect()
	var mn := r.position
	var mx := r.position + r.size
	var dl := p.x - mn.x
	var dr := mx.x - p.x
	var ds := p.z - mn.y
	var dn := mx.y - p.z
	var best := dl
	var out := Vector3(mn.x - 0.75, 0.12, clampf(p.z, mn.y, mx.y))
	if dr < best:
		best = dr
		out = Vector3(mx.x + 0.75, 0.12, clampf(p.z, mn.y, mx.y))
	if ds < best:
		best = ds
		out = Vector3(clampf(p.x, mn.x, mx.x), 0.12, mn.y - 0.75)
	if dn < best:
		out = Vector3(clampf(p.x, mn.x, mx.x), 0.12, mx.y + 0.75)
	return out

func _deck_corners() -> Array:
	var r := _pool_rect()
	var mn := r.position - Vector2(POOL_PAD, POOL_PAD)
	var mx := r.position + r.size + Vector2(POOL_PAD, POOL_PAD)
	var y := 0.12
	return [
		Vector3(mn.x, y, mn.y),
		Vector3(mx.x, y, mn.y),
		Vector3(mx.x, y, mx.y),
		Vector3(mn.x, y, mx.y),
	]

func _path_len(a: Vector3, pts: Array, b: Vector3) -> float:
	var n := a
	var total := 0.0
	for p in pts:
		var q: Vector3 = p
		total += n.distance_to(q)
		n = q
	return total + n.distance_to(b)

func _detour(a: Vector3, b: Vector3) -> Array:
	var start := a
	var prefix: Array = []
	if _in_pool(start):
		var exit := _rim_outside(start)
		prefix.append(exit)
		start = exit
	var goal := b
	var suffix: Array = []
	if _in_pool(goal):
		goal = _rim_outside(goal)
		suffix.append(goal)
	var around := _around(start, goal)
	prefix.append_array(around)
	prefix.append_array(suffix)
	return prefix

func _around(a: Vector3, b: Vector3) -> Array:
	var corners: Array = _deck_corners()
	var best: Array = []
	var best_len := INF
	for c in corners:
		var cc: Vector3 = c
		if _hits_pool(a, cc) or _hits_pool(cc, b):
			continue
		var seq: Array = [cc]
		var L := _path_len(a, seq, b)
		if L < best_len:
			best_len = L
			best = seq
	for i in 4:
		var c1: Vector3 = corners[i]
		var c2: Vector3 = corners[(i + 1) % 4]
		if _hits_pool(a, c1) or _hits_pool(c2, b):
			continue
		var seq2: Array = [c1, c2]
		var L2 := _path_len(a, seq2, b)
		if L2 < best_len:
			best_len = L2
			best = seq2
	if not best.is_empty():
		return best
	var nearest := 0
	var nd := INF
	for i in 4:
		var c: Vector3 = corners[i]
		var d := a.distance_to(c)
		if d < nd and not _hits_pool(a, c):
			nd = d
			nearest = i
	var seq3: Array = []
	for k in 4:
		seq3.append(corners[(nearest + k) % 4])
	return seq3

func _slide_out_of_pool(from: Vector3, to: Vector3) -> Vector3:
	if not _in_pool(to):
		return to
	var xtry := Vector3(to.x, to.y, from.z)
	if not _in_pool(xtry):
		return xtry
	var ztry := Vector3(from.x, to.y, to.z)
	if not _in_pool(ztry):
		return ztry
	return from

func _waypoint_is_swim(t: Vector3) -> bool:
	return t.y < -0.12

func _in_water_motion() -> bool:
	if position.y < -0.08 or _ideal.y < -0.08:
		return true
	if _route.is_empty():
		return false
	return _waypoint_is_swim(_route[0])

func _separation() -> Vector3:
	var push := Vector3.ZERO
	var tree := get_tree()
	if tree == null:
		return push
	for n in tree.get_nodes_in_group("npc"):
		if n == self or not is_instance_valid(n):
			continue
		var other := n as Node3D
		if other == null or not other.visible:
			continue
		var d := global_position - other.global_position
		d.y = 0.0
		var dist := d.length()
		var rad := NPC_RADIUS
		if n.has_method("is_moving") and not n.is_moving():
			rad = IDLE_RADIUS
		if dist <= 0.001:
			push += Vector3(1, 0, 0)
		elif dist < rad:
			push += (d / dist) * ((rad - dist) / rad)
	var pl: Node3D = Core.player_ref
	if is_instance_valid(pl) and Core.in_game and pl.visible:
		var d2 := global_position - pl.global_position
		d2.y = 0.0
		var dist2 := d2.length()
		if dist2 > 0.001 and dist2 < PLAYER_RADIUS:
			push += (d2 / dist2) * ((PLAYER_RADIUS - dist2) / PLAYER_RADIUS)
	return push
