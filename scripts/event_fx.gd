extends Node3D
## Efeitos visíveis dos eventos do dia: festas (palco, fogueira, barracas, faixa), maré alta e tempestade (mar), barco do passeio.
## Os objetos vêm do Blender (g:dj_booth, g:party_banner, g:flame) e do Kenney (tenda, fogueira).
class_name EventFX

var world: Node3D
var party_root: Node3D
var _fire_light: OmniLight3D
var _fire_flame: Node3D
var _dj_lights: Array = []
var _boat: Node3D
var _sea_tween: Tween
var _t: = 0.0
# v0.9.3: gente nas festas, passageiros, tempestade e trilha do farol
const GuestScript: = preload("res://scripts/guest.gd")
var _rng: = RandomNumberGenerator.new()
var _crowd: Array = []          # {g, mode, ...}
var _queues: Array = []         # quermesse: [[g, g, g], ...]
var _queue_t: = 0.0
var _pax: Array = []
var _trail: Array = []
var _flash: DirectionalLight3D
var _bolt_t: = 8.0
var _lights: Array = []
var _storm_on: = false
var _puddles: Node3D

## Centro da festa na areia, ao lado do quiosque.
const PARTY_C: = Vector3(52.0, 0.0, -23.0)
const PIER_X: = 72.0

func setup(w: Node3D) -> void :
	world = w
	name = "EventFX"
	Core.event_changed.connect(_refresh)
	Core.tour_done.connect(_on_tour)
	Core.weather_changed.connect(func(_k): _storm())
	_rng.seed = 4242
	_flash = DirectionalLight3D.new()
	_flash.light_energy = 0.0
	_flash.light_color = Color(0.85, 0.9, 1.0)
	_flash.rotation = Vector3(-1.2, 0.4, 0.0)
	_flash.shadow_enabled = false
	add_child(_flash)
	_refresh()

func _ground(x: float, z: float) -> float:
	return float(world.call("_height", x, z)) if world.has_method("_height") else 0.0

func _refresh() -> void :
	_sea()
	_party()
	_storm()

# ------------------------------------------------------------------ mar
func _sea() -> void :
	var om: ShaderMaterial = world.get("ocean_mat")
	if om == null:
		return
	var sw: = 1.0
	var td: = 0.0
	if Core.day_event == "tempestade":
		sw = 2.6
		td = 0.12
	elif Core.day_event == "mare":
		sw = 1.5
		td = 0.42
	if _sea_tween:
		_sea_tween.kill()
	if Core.paused:
		om.set_shader_parameter("swell", sw)
		om.set_shader_parameter("tide", td)
		return
	# tween_method: o caminho "shader_parameter/x" não existe enquanto o shader não foi compilado (erro no log)
	var sw0: = float(om.get_shader_parameter("swell") if om.get_shader_parameter("swell") != null else 1.0)
	var td0: = float(om.get_shader_parameter("tide") if om.get_shader_parameter("tide") != null else 0.0)
	_sea_tween = create_tween().set_parallel(true)
	_sea_tween.tween_method(func(v: float): om.set_shader_parameter("swell", v), sw0, sw, 3.0)
	_sea_tween.tween_method(func(v: float): om.set_shader_parameter("tide", v), td0, td, 3.0)

# ------------------------------------------------------------------ festas
func _party() -> void :
	if party_root and is_instance_valid(party_root):
		party_root.queue_free()
	party_root = null
	_dj_lights.clear()
	_fire_light = null
	_fire_flame = null
	_crowd.clear()
	_queues.clear()
	if not Core.is_party():
		return
	party_root = Node3D.new()
	party_root.name = "Party"
	add_child(party_root)
	var deco: bool = Core.prep_active
	var c: = PARTY_C
	var title: = ""
	match Core.day_event:
		"quermesse":
			title = "QUERMESSE DA PRAIA"
			for k in 3:
				var sp: = c + Vector3(-5.0 + k * 5.0, 0.0, 0.0)
				sp.y = _ground(sp.x, sp.z)
				var tent: = Real.place(party_root, "k:tent_smallOpen", sp, 2.6, PI, Color(1.0, 0.9, 0.9) if k % 2 == 0 else Color(0.9, 0.95, 1.0))
				if tent:
					Real.place(party_root, "k:crate-bottles", sp + Vector3(1.6, 0.0, 0.2), 0.5, 0.3)
					Real.place(party_root, "k:barrel", sp + Vector3(-1.5, 0.0, 0.5), 0.8, 0.0)
		"junina":
			title = "FESTA JUNINA"
			var fp: = c + Vector3(0, 0, 0)
			fp.y = _ground(fp.x, fp.z)
			Real.place(party_root, "k:campfire_stones", fp, 0.0, 0.0, Color.WHITE, 1.8)
			Real.place(party_root, "k:campfire_logs", fp + Vector3(0, 0.02, 0), 0.0, 0.0, Color.WHITE, 1.4)
			_fire_flame = Real.place_glow(party_root, "g:flame", fp + Vector3(0, 0.15, 0), -2.4, 0.0, _flame_mat())
			_fire_light = OmniLight3D.new()
			_fire_light.position = fp + Vector3(0, 1.2, 0)
			_fire_light.omni_range = 12.0
			_fire_light.light_color = Color(1.0, 0.6, 0.25)
			_fire_light.light_energy = 2.6
			party_root.add_child(_fire_light)
			for k in 4:
				var a: = TAU * k / 4.0 + 0.4
				var lp: = fp + Vector3(cos(a), 0, sin(a)) * 2.6
				lp.y = _ground(lp.x, lp.z)
				world.call("_bench", lp, -a + PI * 0.5, party_root)
		"show_dj":
			title = "DJ MARÉ"
			var dp: = c + Vector3(0, 0, 0)
			dp.y = _ground(dp.x, dp.z)
			Real.place(party_root, "g:dj_booth", dp, -1.0, 0.0, Color.WHITE, 0.0, false)
			for k in 3:
				var l: = OmniLight3D.new()
				l.position = dp + Vector3(-1.8 + k * 1.8, 2.6, 1.2)
				l.omni_range = 9.0
				l.light_energy = 2.0
				party_root.add_child(l)
				_dj_lights.append(l)
	_party_crowd(c)
	# faixa com o nome da festa (só se os preparativos/decoração foram pagos)
	if deco:
		var bp: = c + Vector3(0, 0, -3.4)
		bp.y = _ground(bp.x, bp.z)
		if Real.place(party_root, "g:party_banner", bp, -1.0, 0.0, Color.WHITE, 0.0, false):
			var lb: = B.label(party_root, title, bp + Vector3(0, 2.4, 0.07), 60, Color(0.75, 0.1, 0.2), Color(1, 1, 1, 0.0))
			lb.pixel_size = 0.0045
		for k in 3:
			_pole_bunting(c + Vector3(-9.0, 0, -2.0 + k * 3.0), c + Vector3(9.0, 0, -2.0 + k * 3.0), 0.9)
		# varal de luzes também preso em mastros de bambu (antes as pontas ficavam soltas no ar)
		var la: = c + Vector3(-8.0, 0.0, 5.5)
		var lb2: = c + Vector3(8.0, 0.0, 5.5)
		for pp in [la, lb2]:
			var gp: Vector3 = pp
			gp.y = _ground(gp.x, gp.z)
			Real.place(party_root, "g:bamboo_pole", gp, -1.0, 0.0, Color.WHITE, 0.0, false)
		la.y = _ground(la.x, la.z) + 4.35
		lb2.y = _ground(lb2.x, lb2.z) + 4.35
		if world.has_method("_string_lights"):
			world.call("_string_lights", la, lb2, 24, party_root)
	else:
		_pole_bunting(c + Vector3(-6.0, 0, 2.6), c + Vector3(6.0, 0, 2.6), 0.7)

## Varal de bandeirinhas preso no topo de dois mastros de bambu (g:bamboo_pole, argola a 4,48 m).
func _pole_bunting(a: Vector3, b: Vector3, sag: float) -> void :
	var top: = 4.45
	for p in [a, b]:
		var gp: Vector3 = p
		gp.y = _ground(gp.x, gp.z)
		Real.place(party_root, "g:bamboo_pole", gp, -1.0, 0.0, Color.WHITE, 0.0, false)
	D.bunting(party_root, Vector3(a.x, _ground(a.x, a.z) + top, a.z), Vector3(b.x, _ground(b.x, b.z) + top, b.z), sag)

func _flame_mat() -> Material:
	return P.glow(Color(1.0, 0.55, 0.15), 4.0)


# ------------------------------------------------------------------ gente
func _npc(parent: Node, pos: Vector3, rot: float) -> Node3D:
	var g: = Node3D.new()
	g.set_script(GuestScript)
	parent.add_child(g)
	g.setup(7000 + _rng.randi() % 2000, _rng)
	g.block_rects = world.get("block_rects") if world.get("block_rects") != null else []
	g.position = pos
	g.rotation.y = rot
	return g

func _face(p: Vector3, target: Vector3) -> float:
	return atan2(target.x - p.x, target.z - p.z)

## Festa: dança na frente do DJ, quadrilha em volta da fogueira (com quem pula a fogueira), filas nas barracas da quermesse.
func _party_crowd(c: Vector3) -> void :
	var n: = 10 if Quality.hd else 5
	match Core.day_event:
		"show_dj":
			for k in n:
				var p: = c + Vector3(_rng.randf_range(-3.6, 3.6), 0, _rng.randf_range(2.6, 6.0))
				p.y = _ground(p.x, p.z)
				var g: = _npc(party_root, p, _face(p, c))
				_crowd.append({"g": g, "mode": "dance", "delay": _rng.randf_range(0.0, 1.2)})
		"junina":
			var ring: = maxi(n - 1, 3)
			for k in ring:
				var a: = TAU * k / float(ring)
				var g2: = _npc(party_root, c, 0.0)
				_crowd.append({"g": g2, "mode": "ring", "a": a, "r": 4.1})
			var j: = _npc(party_root, c + Vector3(-1.7, 0, 0.3), PI * 0.5)
			_crowd.append({"g": j, "mode": "jump", "t": 0.0, "side": -1.0})
		"quermesse":
			for k in 3:
				var sp: = c + Vector3(-5.0 + k * 5.0, 0.0, 0.0)
				var q: Array = []
				for i in (3 if Quality.hd else 2):
					var p2: = sp + Vector3(0.0, 0.0, 2.3 + i * 0.85)
					p2.y = _ground(p2.x, p2.z)
					var g3: = _npc(party_root, p2, PI)
					q.append(g3)
				_queues.append({"q": q, "base": sp})

func _party_hours() -> bool:
	return Core.minutes >= 16.0 * 60.0 and Core.minutes < 23.0 * 60.0

func _crowd_tick(delta: float) -> void :
	if party_root == null or not is_instance_valid(party_root):
		return
	var on: = _party_hours() or Core.paused
	for d in _crowd:
		var g: Node3D = d.g
		g.visible = on
	for qd in _queues:
		for g in qd.q:
			(g as Node3D).visible = on
	if not on:
		return
	var dt: = delta * maxf(Core.speed_mult, 1.0)
	var c: = PARTY_C
	c.y = _ground(c.x, c.z)
	for d in _crowd:
		var g: Node3D = d.g
		match d.mode:
			"dance":
				if d.delay > 0.0:
					d.delay -= dt
					if d.delay <= 0.0:
						g.play("Dance_Loop")
			"ring":
				d.a = fmod(d.a + dt * 0.28, TAU)
				var p: Vector3 = c + Vector3(cos(d.a), 0, sin(d.a)) * float(d.r)
				p.y = _ground(p.x, p.z)
				g.position = p
				g.rotation.y = atan2(-sin(d.a), cos(d.a))   # tangente (anda em roda)
				g.play("Walk_Loop")
			"jump":
				d.t += dt
				var cyc: = fmod(d.t, 7.0)
				if cyc < 1.1:
					var u: = cyc / 1.1
					var x: = lerpf(1.7 * d.side, -1.7 * d.side, u)
					g.position = c + Vector3(x, sin(PI * u) * 0.75, 0.3)
					g.rotation.y = PI * 0.5 * -d.side
					g.play("Jump_Loop")
				else:
					if g.position.y > c.y + 0.01:
						g.position.y = c.y
						d.side = -d.side
					g.play("Idle_Talking_Loop")
	# quermesse: quem está na frente compra (Interact) e volta para o fim da fila
	_queue_t += dt
	if _queue_t > 7.0:
		_queue_t = 0.0
		for qd in _queues:
			var q: Array = qd.q
			if q.is_empty():
				continue
			var front: Node3D = q.pop_front()
			q.append(front)
			for i in q.size():
				var g2: Node3D = q[i]
				var tgt: Vector3 = qd.base + Vector3(0.0, 0.0, 2.3 + i * 0.85)
				tgt.y = _ground(tgt.x, tgt.z)
				if g2 == front:
					# dá a volta pela lateral até o fim da fila
					g2.go([qd.base + Vector3(1.6, 0, 2.6), qd.base + Vector3(1.6, 0, 2.3 + i * 0.85 + 0.6), tgt])
				else:
					g2.go([tgt])
	for qd in _queues:
		var q2: Array = qd.q
		for i in q2.size():
			var g3: Node3D = q2[i]
			if not g3.is_moving():
				g3.rotation.y = PI
				g3.play("Interact" if i == 0 and _queue_t > 1.0 and _queue_t < 4.0 else "Idle_Loop")

# ------------------------------------------------------------------ passageiros do passeio
func _vest(g: Node3D) -> void :
	# colete salva-vidas no tronco (preso ao osso spine_03, que acompanha a animação)
	var sk: Skeleton3D = g.get("_skel")
	if sk == null:
		return
	var att: = BoneAttachment3D.new()
	att.bone_name = "spine_03"
	sk.add_child(att)
	var holder: = Node3D.new()
	att.add_child(holder)
	var v: = Real.place(holder, "g:life_vest", Vector3.ZERO, -1.05, 0.0, Color.WHITE, 0.0, false)
	if v:
		# a origem do colete é o meio do tronco; o osso spine_03 fica no alto do peito
		holder.position = Vector3(0.0, -0.08, 0.0)
		holder.set_meta("vest", true)

func _board(boat: Node3D, pax: int) -> void :
	_pax.clear()
	var n: = clampi(pax, 3, 8 if Quality.hd else 4)
	for i in n:
		var row: = int(i / 2)
		var lp: = Vector3(-0.42 if i % 2 == 0 else 0.42, 0.4, -1.1 + row * 0.75)
		var g: = _npc(boat, lp, PI if row % 2 == 0 else 0.0)
		g.play("Idle_Talking_Loop" if i % 3 == 0 else "Idle_Loop")
		_vest(g)
		_pax.append(g)
	# os hóspedes da praia saem para o passeio: alguns pedestres somem enquanto o barco está fora
	var vl: = get_tree().get_first_node_in_group("kiosk")
	if vl and vl.get("walkers") != null:
		var w: Array = vl.walkers
		for i in mini(n, w.size()):
			(w[w.size() - 1 - i] as Node3D).set_meta("on_tour", true)

func _unboard() -> void :
	_pax.clear()
	var vl: = get_tree().get_first_node_in_group("kiosk")
	if vl and vl.get("walkers") != null:
		for g in vl.walkers:
			if (g as Node3D).has_meta("on_tour"):
				(g as Node3D).remove_meta("on_tour")

## Trilha do farol: guia na frente e o grupo em fila indiana, da rua até o farol e de volta.
func _farol_walk(pax: int) -> void :
	for g in _trail:
		if is_instance_valid(g):
			g.queue_free()
	_trail.clear()
	var route: Array = [Vector3(104.0, 0.1, 27.5), Vector3(106.0, 0.0, 6.0), Vector3(107.0, 0.0, -16.0), Vector3(107.5, 0.0, -30.0)]
	for i in route.size():
		var rp: Vector3 = route[i]
		rp.y = maxf(_ground(rp.x, rp.z), 0.0)
		route[i] = rp
	var n: = clampi(pax, 3, 6) + 1
	for i in n:
		var start: Vector3 = route[0] + Vector3(0.0, 0.0, i * 1.3)
		var g: = _npc(self, start, PI)
		if i == 0:
			g.set_colors(Color(0.7, 0.5, 0.36), Color(0.95, 0.75, 0.15), Color(0.2, 0.35, 0.25), Color(0.1, 0.07, 0.05))   # guia de camisa amarela
		g.speed = 1.15
		g.go(route.slice(0))
		_trail.append(g)
		g.arrived.connect(_on_trail_arrived.bind(g, route), CONNECT_ONE_SHOT)

func _on_trail_arrived(g: Node3D, route: Array) -> void :
	if not is_instance_valid(g):
		return
	g.rotation.y = 0.0
	g.play("Idle_Talking_Loop")
	get_tree().create_timer(25.0).timeout.connect(func():
		if not is_instance_valid(g):
			return
		var back: = route.duplicate()
		back.reverse()
		g.go(back)
		g.arrived.connect(func(): if is_instance_valid(g): g.queue_free(), CONNECT_ONE_SHOT))

# ------------------------------------------------------------------ tempestade
func _storm() -> void :
	var on: = Core.day_event == "tempestade" and Core.weather == "rain"
	if on == _storm_on:
		return
	_storm_on = on
	# guarda-sóis fechados
	for n in get_tree().get_nodes_in_group("parasol"):
		var mi: Node3D = n
		var sc: = Vector3(0.12, 3.0, 0.12) if on else Vector3.ONE
		if Core.paused:
			mi.scale = sc
		else:
			create_tween().tween_property(mi, "scale", sc, 1.6)
	# poças na areia e nas ruas
	if _puddles and is_instance_valid(_puddles):
		_puddles.queue_free()
		_puddles = null
	var vl: = get_tree().get_first_node_in_group("kiosk")
	if on:
		_puddles = Node3D.new()
		_puddles.name = "Pocas"
		add_child(_puddles)
		var pm: = StandardMaterial3D.new()
		pm.albedo_color = Color(0.32, 0.42, 0.52, 0.72)
		pm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		pm.roughness = 0.04
		pm.metallic_specular = 0.9
		pm.rim_enabled = true
		for k in (40 if Quality.hd else 18):
			var pp: = Vector3(_rng.randf_range(-20.0, 100.0), 0.0, _rng.randf_range(-22.0, 64.0))
			if Rect2(-7.0, -1.0, 14.0, 10.0).has_point(Vector2(pp.x, pp.z)):
				continue
			pp.y = _ground(pp.x, pp.z) + 0.014
			if absf(pp.z - 30.0) < 2.2 or absf(pp.z - 64.0) < 2.2:
				pp.y = 0.06   # rua
			var mi2: = MeshInstance3D.new()
			mi2.mesh = _puddle_mesh(_rng.randf_range(0.5, 1.4))
			mi2.material_override = pm
			mi2.position = pp
			mi2.rotation.y = _rng.randf() * TAU
			mi2.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			_puddles.add_child(mi2)
		# quem está na rua corre para debaixo do beiral mais próximo
		if vl and vl.get("walkers") != null:
			var fronts: Array = world.get("_house_fronts") if world.get("_house_fronts") != null else []
			for g in vl.walkers:
				var gp: Vector3 = (g as Node3D).position
				var best: = Vector3.INF
				for hf in fronts:
					var t: = Vector3(clampf(gp.x, hf[0], hf[1]), 0.12, hf[2] + hf[3] * 0.55)
					if t.distance_to(gp) < best.distance_to(gp):
						best = t
				if best != Vector3.INF and best.distance_to(gp) < 25.0:
					g.set_meta("shelter", true)
					g.speed = 2.8
					if Core.paused:
						g.position = best
					else:
						g.go([best])
		_lights = world.find_children("*", "OmniLight3D", true, false)
	else:
		if vl and vl.get("walkers") != null:
			for g in vl.walkers:
				if (g as Node3D).has_meta("shelter"):
					g.remove_meta("shelter")
					g.speed = 1.1

func _puddle_mesh(r: float) -> ArrayMesh:
	# poça com contorno irregular (ruído), um pouco abaixo do centro nas bordas
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var seg: = 28
	var ph: = _rng.randf() * TAU
	var ph2: = _rng.randf() * TAU
	var pts: Array = []
	for i in seg:
		var a: = TAU * i / seg
		var rr: = r * (1.0 + 0.22 * sin(a * 3.0 + ph) + 0.12 * sin(a * 5.0 + ph2))
		pts.append(Vector3(cos(a) * rr, 0.0, sin(a) * rr * 0.7))
	st.set_normal(Vector3.UP)
	for i in seg:
		var a0: Vector3 = pts[i]
		var a1: Vector3 = pts[(i + 1) % seg]
		st.add_vertex(Vector3.ZERO)
		st.add_vertex(a1)
		st.add_vertex(a0)
	return st.commit()

func _storm_tick(delta: float) -> void :
	if not _storm_on or Core.paused:
		return
	_bolt_t -= delta
	if _bolt_t > 0.0:
		return
	_bolt_t = _rng.randf_range(7.0, 16.0)
	# relâmpago duplo + trovão atrasado + luzes da vila piscando
	var tw: = create_tween()
	tw.tween_property(_flash, "light_energy", 3.5, 0.05)
	tw.tween_property(_flash, "light_energy", 0.3, 0.08)
	tw.tween_property(_flash, "light_energy", 2.6, 0.05)
	tw.tween_property(_flash, "light_energy", 0.0, 0.35)
	var au: = get_tree().get_first_node_in_group("audio")
	if au:
		get_tree().create_timer(_rng.randf_range(0.4, 1.8)).timeout.connect(func(): au.sfx("thunder", -4.0, _rng.randf_range(0.85, 1.1)))
	for l in _lights:
		if is_instance_valid(l) and _rng.randf() < 0.35 and (l as OmniLight3D).visible:
			var ol: OmniLight3D = l
			ol.visible = false
			get_tree().create_timer(_rng.randf_range(0.08, 0.35)).timeout.connect(func(): if is_instance_valid(ol): ol.visible = true)

# ------------------------------------------------------------------ passeios
func _on_tour(id: String, _pax: int, _rev: int) -> void :
	if id == "farol":
		_farol_walk(_pax)
		return
	if _boat and is_instance_valid(_boat):
		return
	var pier_x: = PIER_X
	var start: = Vector3(pier_x - 3.4, -0.25, -44.0)
	_boat = world.call("_fishing_boat", start, PI, Color(0.95, 0.85, 0.3), false)
	if _boat == null:
		return
	_boat.get_parent().remove_child(_boat)
	add_child(_boat)
	_boat.position = start
	_board(_boat, _pax)
	var out: = Vector3(pier_x - 12.0, -0.25, -150.0)
	var tw: = create_tween()
	tw.tween_property(_boat, "position", out, 38.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_interval(6.0)
	tw.tween_callback(func(): if is_instance_valid(_boat): _boat.rotation.y = 0.0)
	tw.tween_property(_boat, "position", start, 38.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_callback(func():
		if is_instance_valid(_boat):
			_boat.queue_free()
		_boat = null
		_unboard())

func _process(delta: float) -> void :
	_t += delta
	_crowd_tick(delta)
	_storm_tick(delta)
	if _fire_light:
		_fire_light.light_energy = 2.4 + sin(_t * 17.0) * 0.5 + sin(_t * 7.3) * 0.3
		if _fire_flame:
			_fire_flame.scale = Vector3(1.0 + sin(_t * 11.0) * 0.06, 1.0 + sin(_t * 13.0 + 1.0) * 0.12, 1.0 + sin(_t * 9.0) * 0.06)
	for i in _dj_lights.size():
		var l: OmniLight3D = _dj_lights[i]
		l.light_color = Color.from_hsv(fmod(_t * 0.35 + float(i) * 0.33, 1.0), 0.85, 1.0)
		l.light_energy = 1.6 + sin(_t * 6.0 + float(i)) * 0.8
	if _boat and is_instance_valid(_boat):
		_boat.position.y = -0.25 + sin(_t * 1.6) * 0.06
		_boat.rotation.z = sin(_t * 1.3) * 0.05
