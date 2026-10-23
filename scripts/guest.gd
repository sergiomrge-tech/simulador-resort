extends Node3D


signal arrived

const SKINS: = [Color(0.95, 0.78, 0.62), Color(0.8, 0.58, 0.42), Color(0.62, 0.42, 0.28), Color(0.42, 0.28, 0.18)]
const SHIRTS: = [Color(0.70, 0.34, 0.26), Color(0.18, 0.52, 0.54), Color(0.85, 0.74, 0.55), Color(0.86, 0.83, 0.74), Color(0.16, 0.34, 0.46), Color(0.36, 0.55, 0.43), Color(0.32, 0.47, 0.65)]
const SHORTS: = [Color(0.15, 0.25, 0.5), Color(0.85, 0.8, 0.65), Color(0.2, 0.2, 0.22), Color(0.3, 0.55, 0.65), Color(0.75, 0.3, 0.2)]
const HAIRS: = [Color(0.08, 0.06, 0.05), Color(0.3, 0.18, 0.08), Color(0.75, 0.6, 0.35), Color(0.6, 0.57, 0.54), Color(0.5, 0.2, 0.1), Color(0.9, 0.78, 0.5), Color(0.18, 0.12, 0.08)]
const NAMES: = ["Ana", "João", "Maria", "Pedro", "Luiza", "Rafael", "Camila", "Bruno", "Juliana", "Thiago", "Beatriz", "Lucas", "Fernanda", "Gabriel", "Larissa", "Diego"]

static var _mat: ShaderMaterial

var gid: = 0
var gname: = "Hóspede"
var state: = "arrive"
var room: = -1
var wait_min: = 0.0
var timer: = 0.0
var plan: Array = []
var spot: Dictionary = {}
var queue_idx: = -1
var speed: = 1.35
var _route: Array = []
var _ideal: = Vector3.ZERO
var _stuck: = 0.0
var _prev_dist: = INF
var _anim: AnimationPlayer
var _tree: AnimationTree
var _playback: AnimationNodeStateMachinePlayback
var _cur_anim: = ""
var _state: = ""
var _move_speed: = 0.0
var _skel: Skeleton3D
var _look_pt: Marker3D
var _cup: Node3D
var _food: Node3D
var _eating: = false
var _eat_t: = 0.0
## true = leva o copo/coco à boca em vez da comida (v0.7.1)
var _consume_drink: = false
var _mesh_insts: Array = []
var _skin: = Color(0.8, 0.6, 0.45)
var _face: Node3D
var _female: = false
var _model: Node3D
var _body_mi: MeshInstance3D
var _rng_seed: = 0
var _hair_col: = Color(0.1, 0.07, 0.05)
var _skin_parts: Array = []
var _hair_parts: Array = []


const WALK_REF: = 1.05
const JOG_REF: = 2.55
const SWIM_REF: = 1.15

const NPC_RADIUS: = 0.62
const IDLE_RADIUS: = 0.42
const PLAYER_RADIUS: = 0.72
const MAX_SIDESTEP: = 0.55
const POOL_PAD: = 1.45
var block_rects: Array = []

func setup(id: int, rng: RandomNumberGenerator) -> void :
	gid = id
	gname = NAMES[rng.randi() % NAMES.size()]
	if _mat == null:
		_mat = ShaderMaterial.new()
		_mat.shader = load("res://shaders/guest.gdshader")
	_female = rng.randf() < 0.5
	var m: Node3D = Ppl.build_body(_female)
	add_child(m)
	_model = m
	_dress(m, rng)
	set_colors(SKINS[rng.randi() % SKINS.size()], SHIRTS[rng.randi() % SHIRTS.size()], SHORTS[rng.randi() % SHORTS.size()], HAIRS[rng.randi() % HAIRS.size()])
	var aps: = m.find_children("*", "AnimationPlayer", true, false)
	if aps.size() > 0:
		_anim = aps[0]
		for an in _anim.get_animation_list():
			if an.ends_with("_Loop") or an.ends_with("Idle") or an.ends_with("Walk"):
				_anim.get_animation(an).loop_mode = Animation.LOOP_LINEAR
	speed = rng.randf_range(1.2, 1.5)
	add_to_group("npc")
	_ideal = position
	_build_anim(m)
	_caricature(rng)
	_finish_look(rng)
	play("Idle_Loop")

func set_colors(skin: Color, shirt: Color, shorts: Color, hair: Color) -> void :
	_skin = skin
	_hair_col = hair
	if _body_mi and is_instance_valid(_body_mi):
		_body_mi.material_override = Ppl.skin_material(_female, skin)
	var htint: = Color(clampf(hair.r * 1.9 + 0.04, 0.0, 0.9), clampf(hair.g * 1.9 + 0.03, 0.0, 0.88), clampf(hair.b * 1.9 + 0.03, 0.0, 0.84))   # teto < 1: branco puro vira azul na sombra do chapéu
	for n in _hair_parts:
		if is_instance_valid(n):
			n.material_override = Ppl.hair_copy(n.get_meta("src"), htint)
	for mi in _mesh_insts:
		mi.set_instance_shader_parameter("skin", skin)
		mi.set_instance_shader_parameter("shirt", shirt)
		mi.set_instance_shader_parameter("shorts", shorts)
		mi.set_instance_shader_parameter("hair", hair)

func _clip(an: String) -> String:
	if _anim == null:
		return ""
	if _anim.has_animation(an):
		return an
	if an.ends_with("_Loop") and _anim.has_animation(an.trim_suffix("_Loop")):
		return an.trim_suffix("_Loop")
	return ""

func _state_for(an: String) -> String:
	var key: = an
	if not _clip(key).is_empty() and key.ends_with("_Loop") and not _anim.has_animation(key):
		key = key.trim_suffix("_Loop")
	match key:
		"Idle_Loop", "Idle":
			return "Idle"
		"Idle_Talking_Loop", "Idle_Talking":
			return "Talk"
		"Walk_Loop", "Walk", "Walk_Formal_Loop", "Walk_Formal":
			return "Walk"
		"Jog_Fwd_Loop", "Jog_Fwd":
			return "Jog"
		"Sitting_Idle_Loop", "Sitting_Idle":
			return "Sit"
		"Sitting_Talking_Loop", "Sitting_Talking":
			return "SitTalk"
		"Swim_Fwd_Loop", "Swim_Fwd":
			return "Swim"
		"Swim_Idle_Loop", "Swim_Idle":
			return "SwimIdle"
		"Dance_Loop", "Dance":
			return "Dance"
		"Jump_Loop", "Jump":
			return "Jump"
		"Sprint_Loop", "Sprint":
			return "Sprint"
		"Interact":
			return "Drink"
		"Eat", "Eating":
			return "Sit"
		_:
			return ""

func _build_anim(model: Node3D) -> void :
	if _anim == null:
		return
	var skels: = model.find_children("*", "Skeleton3D", true, false)
	if skels.size() > 0:
		_skel = skels[0]
		_look_pt = Marker3D.new()
		_look_pt.name = "LookPoint"
		add_child(_look_pt)
		var look: = LookAtModifier3D.new()
		look.bone_name = "Head"
		look.use_angle_limitation = true
		look.primary_limit_angle = deg_to_rad(50.0)
		look.secondary_limit_angle = deg_to_rad(22.0)
		_skel.add_child(look)
		look.target_node = look.get_path_to(_look_pt)
		var att: = BoneAttachment3D.new()
		att.bone_name = "hand_r"
		_skel.add_child(att)
		_cup = _make_cup()
		att.add_child(_cup)
		_cup.visible = false
		_food = _make_food()
		att.add_child(_food)
		var eat: = SkeletonModifier3D.new()
		eat.name = "EatArm"
		eat.set_script(load("res://scripts/eat_arm.gd"))
		eat.guest = self
		_skel.add_child(eat)
	var sm: = AnimationNodeStateMachine.new()
	var specs: = {
		"Idle": "Idle_Loop", "Talk": "Idle_Talking_Loop", "Walk": "Walk_Loop", "Jog": "Jog_Fwd_Loop", 
		"Sit": "Sitting_Idle_Loop", "SitTalk": "Sitting_Talking_Loop", 
		"Swim": "Swim_Fwd_Loop", "SwimIdle": "Swim_Idle_Loop", "Drink": "Interact", 
		"Dance": "Dance_Loop", "Jump": "Jump_Loop", "Sprint": "Sprint_Loop", 
	}
	var order: = ["Idle", "Talk", "Walk", "Jog", "Sit", "SitTalk", "Swim", "SwimIdle", "Drink", "Dance", "Jump", "Sprint"]
	var added: = {}
	var i: = 0
	for st in order:
		var clip: = _clip(specs[st])
		if clip == "":
			continue
		var bt: = AnimationNodeBlendTree.new()
		var node: = AnimationNodeAnimation.new()
		node.animation = clip
		var rate: = AnimationNodeTimeScale.new()
		bt.add_node("clip", node)
		bt.add_node("rate", rate)
		bt.connect_node("rate", 0, "clip")
		bt.connect_node("output", 0, "rate")
		sm.add_node(st, bt, Vector2(200.0 * (i % 3), 140.0 * int(i / 3)))
		added[st] = true
		i += 1
	if not added.has("Idle"):
		return
	var enter: = AnimationNodeStateMachineTransition.new()
	enter.xfade_time = 0.2
	sm.add_transition("Start", "Idle", enter)
	for a in added.keys():
		for b in added.keys():
			if a == b:
				continue
			var tr: = AnimationNodeStateMachineTransition.new()
			tr.xfade_time = 0.28
			sm.add_transition(a, b, tr)
	_tree = AnimationTree.new()
	_tree.name = "GuestTree"
	add_child(_tree)
	_tree.anim_player = _tree.get_path_to(_anim)
	_tree.tree_root = sm
	_tree.active = true
	_playback = _tree.get("parameters/playback")
	if _playback == null:
		call_deferred("_arm_tree")

func _arm_tree() -> void :
	if _tree == null:
		return
	_playback = _tree.get("parameters/playback")
	if _playback == null:
		_tree.active = false
		return
	if _eating:
		_state = ""
		_go_state("Sit")
		return
	if _state != "":
		_playback.start(_state)

func _make_cup() -> Node3D:
	var n: = Node3D.new()
	var cup: = Real.place(n, "g:cup_plastic", Vector3(0.0, 0.02, 0.06), 0.11)
	if cup:
		cup.rotation.x = 0.4
	return n

func _make_food() -> Node3D:
	var n: = Node3D.new()
	Real.place(n, "g:coxinha", Vector3(0.0, 0.02, 0.06), 0.085)
	n.visible = false
	return n

func _set_eating(on: bool) -> void :
	_eating = on
	if not on:
		_eat_t = 0.0
	if _food:
		_food.visible = on and not _consume_drink
	if _cup:
		_cup.visible = on and _consume_drink

func _go_state(st: String) -> void :
	if st == "" or st == _state:
		return
	if _playback == null:
		var clip: = _clip(st)
		if clip != "" and _anim.has_animation(clip):
			_anim.play(clip, 0.3)
			_cur_anim = clip
		return
	if _state == "":
		_playback.start(st)
	else:
		_playback.travel(st)
	_state = st
	_cur_anim = st
	if st != "Sit" and st != "SitTalk":
		_set_eating(false)
	if _cup:
		_cup.visible = ((st == "Drink" or st == "SitTalk") and not _eating) or (_eating and _consume_drink)

func _sync_rate() -> void :
	if _tree == null or _state == "":
		return
	var scale: = 1.0
	if _state == "Walk" and _move_speed > 0.2:
		scale = clampf(_move_speed / WALK_REF, 0.7, 5.0)
	elif _state == "Jog" and _move_speed > 0.2:
		scale = clampf(_move_speed / JOG_REF, 0.7, 5.0)
	elif _state == "Swim" and _move_speed > 0.2:
		scale = clampf(_move_speed / SWIM_REF, 0.7, 5.0)
	_tree.set("parameters/%s/rate/scale" % _state, scale)

func _update_look() -> void :
	if _look_pt == null:
		return
	var ahead: = global_position - global_transform.basis.z * 3.5 + Vector3(0, 1.5, 0)
	var pl: Node3D = Core.player_ref
	if is_instance_valid(pl) and pl.visible and Core.in_game:
		var to: = pl.global_position - global_position
		to.y = 0.0
		var dist: = to.length()
		var face: = - global_transform.basis.z
		face.y = 0.0
		if dist > 0.45 and dist < 8.0 and face.length() > 0.01 and face.normalized().dot(to / dist) > -0.2:
			ahead = pl.global_position + Vector3(0, 1.45, 0)
	_look_pt.global_position = ahead

func play(an: String) -> void :
	if _anim == null:
		return
	if an == "Eat" or an == "Eating":
		_set_eating(true)
		_go_state("Sit")
		return
	if _eating:
		_set_eating(false)
	var st: = _state_for(an)
	if st == "":
		var clip: = _clip(an)
		if clip != "" and clip != _cur_anim:
			_anim.play(clip, 0.3)
			_cur_anim = clip
		return
	_go_state(st)

func _locomote(swimming: bool) -> void :
	if swimming:
		_go_state("Swim")
		return
	if _state == "Jog" and _move_speed > 1.7:
		return
	if _move_speed > 2.15:
		_go_state("Jog")
	else:
		_go_state("Walk")

func go(route: Array) -> void :
	_ideal = position
	_stuck = 0.0
	_prev_dist = INF
	_route = _expand_route(route)
	if not _route.is_empty():
		_locomote(_in_water_motion())

func is_moving() -> bool:
	return not _route.is_empty()

func _process(delta: float) -> void :
	if _eating:
		_eat_t += delta
	var prev: = position
	if _route.is_empty():
		_move_speed = 0.0
		_sync_rate()
		_update_look()
		return
	var target: Vector3 = _route[0]
	var to: = target - _ideal
	var step: = speed * delta * Core.speed_mult
	var flat: = Vector3(to.x, 0, to.z)
	var dist: = flat.length()
	if dist <= step and absf(to.y) <= step + 0.001:

		var detoured: = false
		if _segment_needs_detour(_ideal, target):
			var extra: = _detour(_ideal, target)
			var useful: = false
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
		var adv: = minf(step, dist)
		var nxt_ideal: = _ideal + Vector3(flat.x / dist, 0.0, flat.z / dist) * adv
		nxt_ideal.y = _ideal.y + to.y * (adv / dist)
		if not _waypoint_is_swim(target):
			nxt_ideal = _slide_out_of_blocks(_ideal, _slide_out_of_pool(_ideal, nxt_ideal))
		_ideal = nxt_ideal
	if not _route.is_empty():
		var dnow: = _ideal.distance_to(_route[0])
		if dnow < _prev_dist - 0.02:
			_prev_dist = dnow
			_stuck = 0.0
		else:
			_stuck += delta
			if _stuck > 0.35 and _segment_needs_detour(_ideal, _route[0]):
				var around: = _detour(_ideal, _route[0])
				var first_ok: = false
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
	var swimming: = _in_water_motion()
	_locomote(swimming)
	var desired: = _ideal
	if not swimming:
		var sep: = _separation()
		if sep.length() > 0.001:
			var travel: = flat
			var offset: = sep
			if travel.length() > 0.15:
				var tdir: = travel.normalized()
				offset -= tdir * offset.dot(tdir)
			if offset.length() > MAX_SIDESTEP:
				offset = offset.normalized() * MAX_SIDESTEP
			desired = _ideal + offset
			desired.y = _ideal.y
			desired = _slide_out_of_blocks(_ideal, _slide_out_of_pool(_ideal, desired))
	var blend: = minf(1.0, delta * 10.0 * maxf(Core.speed_mult, 1.0))
	var nxt: = position.lerp(desired, blend)
	if not swimming:
		nxt = _slide_out_of_blocks(position, _slide_out_of_pool(position, nxt))
	var face: = nxt - position
	face.y = 0
	if face.length() < 0.02:
		face = target - position
		face.y = 0
	if face.length() > 0.02:
		var yaw: = atan2(face.x, face.z)
		rotation.y = lerp_angle(rotation.y, yaw, minf(1.0, delta * 8.0 * maxf(Core.speed_mult, 1.0)))
	position = nxt
	_move_speed = Vector2(position.x - prev.x, position.z - prev.z).length() / maxf(delta, 0.0001)
	_locomote(swimming)
	_sync_rate()
	_update_look()


func _world() -> Node:
	var p: = get_parent()
	if p != null and "world" in p and p.world != null:
		return p.world
	return null

func _pool_rect() -> Rect2:
	var w: = _world()
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
	var r: = _pool_rect()
	var inner: = r.grow(-0.04)
	return inner.has_point(Vector2(pt.x, pt.z))

func _hits_pool(a: Vector3, b: Vector3) -> bool:
	if not _has_pool():
		return false
	var r: = _pool_rect().grow(-0.04)
	var mn: = r.position
	var mx: = r.position + r.size
	var dx: = b.x - a.x
	var dz: = b.z - a.z
	var t0: = 0.0
	var t1: = 1.0
	var ps: = PackedFloat32Array([ - dx, dx, - dz, dz])
	var qs: = PackedFloat32Array([a.x - mn.x, mx.x - a.x, a.z - mn.y, mx.y - a.z])
	for i in 4:
		if absf(ps[i]) < 1e-05:
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
	var r: = _pool_rect()
	var mn: = r.position
	var mx: = r.position + r.size
	var dx: = maxf(mn.x - pt.x, maxf(0.0, pt.x - mx.x))
	var dz: = maxf(mn.y - pt.z, maxf(0.0, pt.z - mx.y))
	return Vector2(dx, dz).length()


func _rim_step(outside: Vector3, inside: Vector3) -> bool:
	return _dist_outside_pool(outside) <= 1.6 and outside.distance_to(inside) <= 3.2

func _segment_needs_detour(a: Vector3, b: Vector3) -> bool:
	if not _hits_pool(a, b):
		return false
	var a_in: = _in_pool(a)
	var b_in: = _in_pool(b)
	if a_in and b_in:
		return false
	if a_in and _rim_step(b, a):
		return false
	if b_in and _rim_step(a, b):
		return false
	return true

func _expand_route(route: Array) -> Array:
	var out: Array = []
	var cursor: = position
	for raw in route:
		var pt: Vector3 = raw
		if _segment_needs_detour(cursor, pt):
			for w in _detour(cursor, pt):
				_push_pt(out, w)
		_push_pt(out, pt)
		cursor = pt
	# Antes só a piscina tinha desvio; mesas e casas prendiam o NPC na borda.
	var safe: Array = []
	cursor = position
	for target in out:
		for waypoint in _around_blocks(cursor, target):
			_push_pt(safe, waypoint)
		cursor = target
	return safe

func _hits_rect(a: Vector2, b: Vector2, rect: Rect2) -> bool:
	var delta: = b - a
	var lo: = 0.0
	var hi: = 1.0
	for axis in 2:
		if absf(delta[axis]) < 0.00001:
			if a[axis] < rect.position[axis] or a[axis] > rect.end[axis]:
				return false
		else:
			var t0: float = (rect.position[axis] - a[axis]) / delta[axis]
			var t1: float = (rect.end[axis] - a[axis]) / delta[axis]
			lo = maxf(lo, minf(t0, t1))
			hi = minf(hi, maxf(t0, t1))
			if lo > hi:
				return false
	return hi > 0.00001 and lo < 0.99999

func _blocks_clear(a: Vector2, b: Vector2, obstacles: Array) -> bool:
	for rect in obstacles:
		if _hits_rect(a, b, rect):
			return false
	return true

func _around_blocks(from: Vector3, to: Vector3, search_margin: float = 3.0) -> Array:
	var a: = Vector2(from.x, from.z)
	var b: = Vector2(to.x, to.z)
	var obstacles: Array = []
	for raw in block_rects:
		var rect: Rect2 = raw
		if rect.grow(0.08).has_point(a) or rect.grow(0.08).has_point(b):
			continue
		obstacles.append(rect.grow(0.08))
	if _blocks_clear(a, b, obstacles):
		return [to]
	var region: = Rect2(a, Vector2.ZERO).expand(b).grow(search_margin)
	var points: Array[Vector2] = [a, b]
	for raw in obstacles:
		var rect: Rect2 = raw
		if not rect.intersects(region):
			continue
		var edge: = rect.grow(0.03)
		for corner in [edge.position, Vector2(edge.end.x, edge.position.y), edge.end, Vector2(edge.position.x, edge.end.y)]:
			var inside: = false
			for other in obstacles:
				if other.has_point(corner):
					inside = true
					break
			if not inside:
				points.append(corner)
	var distances: Array[float] = []
	distances.resize(points.size())
	distances.fill(INF)
	distances[0] = 0.0
	var previous: Array[int] = []
	previous.resize(points.size())
	previous.fill(-1)
	var visited: = {}
	for _step in points.size():
		var current: = -1
		var best: = INF
		for i in points.size():
			if not visited.has(i) and distances[i] < best:
				current = i
				best = distances[i]
		if current < 0 or current == 1:
			break
		visited[current] = true
		for i in points.size():
			if visited.has(i):
				continue
			var candidate: = best + points[current].distance_to(points[i])
			if candidate < distances[i] and _blocks_clear(points[current], points[i], obstacles):
				distances[i] = candidate
				previous[i] = current
	if previous[1] < 0:
		if search_margin < 24.0:
			return _around_blocks(from, to, search_margin * 2.0)
		print("NAV_BLOCKED ", from, " -> ", to)
		return [to]
	var path: Array = []
	var index: = 1
	while index > 0:
		var p: Vector2 = points[index]
		path.push_front(Vector3(p.x, to.y, p.y))
		index = previous[index]
	return path

func _push_pt(out: Array, p: Vector3) -> void :
	if out.is_empty() or (out[out.size() - 1] as Vector3).distance_squared_to(p) > 0.04:
		out.append(p)

func _rim_outside(p: Vector3) -> Vector3:
	var r: = _pool_rect()
	var mn: = r.position
	var mx: = r.position + r.size
	var dl: = p.x - mn.x
	var dr: = mx.x - p.x
	var ds: = p.z - mn.y
	var dn: = mx.y - p.z
	var best: = dl
	var out: = Vector3(mn.x - 0.75, 0.12, clampf(p.z, mn.y, mx.y))
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
	var r: = _pool_rect()
	var mn: = r.position - Vector2(POOL_PAD, POOL_PAD)
	var mx: = r.position + r.size + Vector2(POOL_PAD, POOL_PAD)
	var y: = 0.12
	return [
		Vector3(mn.x, y, mn.y), 
		Vector3(mx.x, y, mn.y), 
		Vector3(mx.x, y, mx.y), 
		Vector3(mn.x, y, mx.y), 
	]

func _path_len(a: Vector3, pts: Array, b: Vector3) -> float:
	var n: = a
	var total: = 0.0
	for p in pts:
		var q: Vector3 = p
		total += n.distance_to(q)
		n = q
	return total + n.distance_to(b)

func _detour(a: Vector3, b: Vector3) -> Array:
	var start: = a
	var prefix: Array = []
	if _in_pool(start):
		var exit: = _rim_outside(start)
		prefix.append(exit)
		start = exit
	var goal: = b
	var suffix: Array = []
	if _in_pool(goal):
		goal = _rim_outside(goal)
		suffix.append(goal)
	var around: = _around(start, goal)
	prefix.append_array(around)
	prefix.append_array(suffix)
	return prefix

func _around(a: Vector3, b: Vector3) -> Array:
	var corners: Array = _deck_corners()
	var best: Array = []
	var best_len: = INF
	for c in corners:
		var cc: Vector3 = c
		if _hits_pool(a, cc) or _hits_pool(cc, b):
			continue
		var seq: Array = [cc]
		var L: = _path_len(a, seq, b)
		if L < best_len:
			best_len = L
			best = seq
	for i in 4:
		var c1: Vector3 = corners[i]
		var c2: Vector3 = corners[(i + 1) % 4]
		if _hits_pool(a, c1) or _hits_pool(c2, b):
			continue
		var seq2: Array = [c1, c2]
		var L2: = _path_len(a, seq2, b)
		if L2 < best_len:
			best_len = L2
			best = seq2
	if not best.is_empty():
		return best
	var nearest: = 0
	var nd: = INF
	for i in 4:
		var c: Vector3 = corners[i]
		var d: = a.distance_to(c)
		if d < nd and not _hits_pool(a, c):
			nd = d
			nearest = i
	var seq3: Array = []
	for k in 4:
		seq3.append(corners[(nearest + k) % 4])
	return seq3

func _slide_out_of_blocks(from: Vector3, to: Vector3) -> Vector3:
	if block_rects.is_empty():
		return to
	var p: = to
	# o bloco que contém o destino final (ex.: a mesa onde o cliente vai sentar) não barra a chegada
	var dest: Vector2 = Vector2(INF, INF)
	if not _route.is_empty():
		var last: Vector3 = _route[_route.size() - 1]
		dest = Vector2(last.x, last.z)
	for _pass in 2:
		for r in block_rects:
			var rect: Rect2 = r
			if not rect.has_point(Vector2(p.x, p.z)) or rect.has_point(Vector2(from.x, from.z)) or rect.has_point(dest):
				continue
			var dl: = p.x - rect.position.x
			var dr: = rect.end.x - p.x
			var dz0: = p.z - rect.position.y
			var dz1: = rect.end.y - p.z
			if dl <= dr and dl <= dz0 and dl <= dz1:
				p.x = rect.position.x - 0.06
			elif dr <= dz0 and dr <= dz1:
				p.x = rect.end.x + 0.06
			elif dz0 <= dz1:
				p.z = rect.position.y - 0.06
			else:
				p.z = rect.end.y + 0.06
	if from.distance_squared_to(p) < 1e-06 and rect_contains_any(to):
		return from
	return p

func rect_contains_any(p: Vector3) -> bool:
	var q: = Vector2(p.x, p.z)
	for r in block_rects:
		if (r as Rect2).has_point(q):
			return true
	return false

func _slide_out_of_pool(from: Vector3, to: Vector3) -> Vector3:
	if not _in_pool(to):
		return to
	var xtry: = Vector3(to.x, to.y, from.z)
	if not _in_pool(xtry):
		return xtry
	var ztry: = Vector3(from.x, to.y, to.z)
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
	var push: = Vector3.ZERO
	var tree: = get_tree()
	if tree == null:
		return push
	for n in tree.get_nodes_in_group("npc"):
		if n == self or not is_instance_valid(n):
			continue
		var other: = n as Node3D
		if other == null or not other.visible:
			continue
		var d: = global_position - other.global_position
		d.y = 0.0
		var dist: = d.length()
		var rad: = NPC_RADIUS
		if n.has_method("is_moving") and not n.is_moving():
			rad = IDLE_RADIUS
		if dist <= 0.001:
			push += Vector3(1, 0, 0)
		elif dist < rad:
			push += (d / dist) * ((rad - dist) / rad)
	var pl: Node3D = Core.player_ref
	if is_instance_valid(pl) and Core.in_game and pl.visible:
		var d2: = global_position - pl.global_position
		d2.y = 0.0
		var dist2: = d2.length()
		if dist2 > 0.001 and dist2 < PLAYER_RADIUS:
			push += (d2 / dist2) * ((PLAYER_RADIUS - dist2) / PLAYER_RADIUS)
	return push


# ------------------------------------------------------------------ v0.7.3: corpo, rosto e cabelo reais (Quaternius, CC0)
const PRINT_COLS: = [Color(1, 1, 1), Color(1.0, 0.9, 0.3), Color(0.15, 0.2, 0.35), Color(1.0, 0.45, 0.6), Color(0.3, 0.85, 0.75)]

## Corpo texturizado, olhos e sobrancelhas, cabelo, camisa e bermuda — tudo no mesmo esqueleto.
func _dress(m: Node3D, rng: RandomNumberGenerator) -> void :
	var skel: = Ppl.skeleton_of(m)
	if skel == null:
		return
	_body_mi = Ppl.body_mesh(m)
	for mi in m.find_children("*", "MeshInstance3D", true, false):
		var n: = String(mi.name).to_lower()
		if n.contains("brow"):
			mi.set_meta("src", mi.mesh.surface_get_material(0))
			_hair_parts.append(mi)
		elif n.contains("eye") and mi.mesh.surface_get_material(0) is BaseMaterial3D:
			mi.material_override = Ppl.toon_copy(mi.mesh.surface_get_material(0), Color.WHITE)
	var foot: = "shoes"
	_body_mi.mesh = Ppl.covered_body(_female, _body_mi.mesh)
	for cm in Ppl.outfit_parts(_female):
		var garment_mat: ShaderMaterial = _mat.duplicate()
		var garment_zone: float = 0.0 if str(cm.name).begins_with("skin_") else (4.0 if str(cm.name).contains("shoes") else (2.0 if str(cm.name).contains("trousers") else 1.0))
		garment_mat.set_shader_parameter("garment_zone", garment_zone)
		var src: Material = cm.mesh.surface_get_material(0)
		if garment_zone > 0.0 and src is BaseMaterial3D and src.albedo_texture != null:
			garment_mat.set_shader_parameter("use_fabric", true)
			garment_mat.set_shader_parameter("fabric_texture", src.albedo_texture)
		cm.material_override = garment_mat
		cm.name = "Tailored_" + str(cm.name)
		skel.add_child(cm)
		cm.skeleton = NodePath("..")
		_mesh_insts.append(cm)
	var shoe_cols: = [Color(0.82, 0.80, 0.74), Color(0.12, 0.14, 0.16), Color(0.22, 0.29, 0.34), Color(0.35, 0.24, 0.16)]
	var sc: Color = shoe_cols[rng.randi() % shoe_cols.size()]
	var so: Color = Color(0.95, 0.93, 0.88) if foot == "shoes" and sc.get_luminance() < 0.7 else Color(0.25, 0.2, 0.18)
	for mi in _mesh_insts:
		mi.set_instance_shader_parameter("shoes", sc)
		mi.set_instance_shader_parameter("sole", so)
	# cabelo
	var styles: Array = Ppl.HAIR_FEMALE if _female else Ppl.HAIR_MALE
	var hm: = Ppl.hair_mesh(styles[rng.randi() % styles.size()])
	if hm:
		Ppl.attach_hair(hm, skel)
		hm.set_meta("src", hm.mesh.surface_get_material(0))
		_hair_parts.append(hm)
	if not _female and rng.randf() < 0.28:
		var bm: = Ppl.hair_mesh("Hair_Beard")
		if bm:
			Ppl.attach_hair(bm, skel)
			bm.set_meta("src", bm.mesh.surface_get_material(0))
			_hair_parts.append(bm)

## Cabeça um pouco maior (caricatura) e chapéu/boné/flor sorteados, presos ao osso da cabeça.
func _caricature(rng: RandomNumberGenerator) -> void :
	if _skel == null:
		return
	var hs: = SkeletonModifier3D.new()
	hs.set_script(load("res://scripts/head_scaler.gd"))
	hs.head_scale = rng.randf_range(1.06, 1.14)
	_skel.add_child(hs)
	var att: = BoneAttachment3D.new()
	att.bone_name = "Head"
	_skel.add_child(att)
	_face = Node3D.new()
	att.add_child(_face)
	# óculos de sol e câmera no pescoço
	if rng.randf() < 0.3:
		Real.place(_face, "g:sunglasses", Vector3(0, 0.075, 0.115), -1.0, 0.0, Color.WHITE, 0.0, false)
	if rng.randf() < 0.14:
		var att3: = BoneAttachment3D.new()
		att3.bone_name = "neck_01"
		_skel.add_child(att3)
		Real.place(att3, "Camera_01", Vector3(0, -0.2, 0.1), 0.0, PI, Color.WHITE, 0.14)

## Estampa da roupa e altura/porte variados.
func _finish_look(rng: RandomNumberGenerator) -> void :
	var pat: = 0.0
	var p2: Color = PRINT_COLS[rng.randi() % PRINT_COLS.size()]
	for mi in _mesh_insts:
		mi.set_instance_shader_parameter("pattern", pat)
		mi.set_instance_shader_parameter("shirt2", p2)
		mi.set_instance_shader_parameter("shorts_pattern", 0.0)
	if _model:
		var h: = rng.randf_range(0.94, 1.06)
		var w: = rng.randf_range(0.91, 1.04)
		_model.scale = Vector3(w * lerpf(1.0, h, 0.5), h, w * lerpf(1.0, h, 0.5))

const HAT_Y: = 0.14


# ------------------------------------------------------------------ v0.7.1: cardápio e balão de pedido
var _menu_card: Node3D
var _bubble: Label3D

## Mostra/esconde o cardapinho na mão direita (cliente escolhendo).
func show_menu(on: bool) -> void :
	if not on:
		if _menu_card:
			_menu_card.queue_free()
			_menu_card = null
		return
	if _menu_card or _skel == null:
		return
	var att: = BoneAttachment3D.new()
	att.bone_name = "hand_r"
	_skel.add_child(att)
	_menu_card = att
	var card: = Node3D.new()
	card.position = Vector3(0.0, 0.1, 0.04)
	card.rotation = Vector3(0.0, 0.0, 0.3)
	att.add_child(card)
	B.box(card, Vector3(0.2, 0.28, 0.012), Vector3.ZERO, B.flat(Color(1.0, 0.45, 0.35), 0.8))
	B.box(card, Vector3(0.17, 0.25, 0.014), Vector3(0, 0, 0.002), B.flat(Color(0.99, 0.95, 0.85), 0.9))
	for k in 4:
		B.box(card, Vector3(0.12, 0.012, 0.016), Vector3(-0.01, 0.07 - k * 0.045, 0.004), B.flat(Color(0.35, 0.28, 0.22), 0.9))

## Balão sobre a cabeça com o pedido; urgente = vermelho (quase indo embora). Texto vazio esconde.
func show_order(text: String, urgent: = false) -> void :
	if text == "":
		if _bubble:
			_bubble.queue_free()
			_bubble = null
		return
	if _bubble == null:
		_bubble = Label3D.new()
		_bubble.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_bubble.font = UiTheme.bold()
		_bubble.font_size = 22
		_bubble.pixel_size = 0.0025
		_bubble.outline_size = 4
		_bubble.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_bubble.width = 200.0
		_bubble.no_depth_test = false
		_bubble.render_priority = 10
		_bubble.fixed_size = false
		# A raiz sentada fica à frente do corpo; ancora o pedido acima da cabeça.
		# Nas cadeiras opostas os balões têm alturas alternadas para não se cobrirem.
		_bubble.position = Vector3(0, 1.8 + (0.5 if spot.get("table", false) and cos(rotation.y) > 0.0 else 0.0), -0.3)
		add_child(_bubble)
	_bubble.text = text
	if Core.company_enabled() and not spot.is_empty():
		var world = _world()
		if world != null:
			_bubble.text = "#%02d" % (world.kiosk_spots.find(spot) + 1)
	_bubble.modulate = Color(0.2, 0.12, 0.08)
	_bubble.outline_modulate = Color(1.0, 0.55, 0.5) if urgent else (Color(1.0, 0.85, 0.25) if get_meta("vip", false) else Color(1, 1, 1))


## Cliente atendido: senta comendo (prato na mão) ou bebendo (copo/coco), levando à boca. (v0.7.1)
func consume(drink: bool) -> void :
	consume_dish("suco" if drink else "petiscos")

func consume_dish(dish: String) -> void:
	var presentation = load("res://scripts/dish_presentation.gd")
	_consume_drink = presentation.is_drink(dish)
	set_meta("consuming_dish", dish)
	var holder: Node3D = _cup if _consume_drink else _food
	if holder != null:
		for child in holder.get_children():
			if child is Node3D:
				child.visible = false
			child.queue_free()
		var model: Node3D = presentation.build(holder, dish)
		if model != null:
			model.scale = Vector3.ONE * (0.42 if _consume_drink else 0.32)
			model.position = Vector3(0, 0.02, 0.04)
	play("Eat")
	_set_eating(true)
