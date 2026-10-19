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

## Centro da festa na areia, ao lado do quiosque.
const PARTY_C: = Vector3(52.0, 0.0, -23.0)
const PIER_X: = 72.0

func setup(w: Node3D) -> void :
	world = w
	name = "EventFX"
	Core.event_changed.connect(_refresh)
	Core.tour_done.connect(_on_tour)
	_refresh()

func _ground(x: float, z: float) -> float:
	return float(world.call("_height", x, z)) if world.has_method("_height") else 0.0

func _refresh() -> void :
	_sea()
	_party()

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
	_sea_tween = create_tween().set_parallel(true)
	_sea_tween.tween_property(om, "shader_parameter/swell", sw, 3.0)
	_sea_tween.tween_property(om, "shader_parameter/tide", td, 3.0)

# ------------------------------------------------------------------ festas
func _party() -> void :
	if party_root and is_instance_valid(party_root):
		party_root.queue_free()
	party_root = null
	_dj_lights.clear()
	_fire_light = null
	_fire_flame = null
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
				Real.place(party_root, "g:bench" if false else "painted_wooden_bench", lp, 0.0, -a + PI * 0.5, Color.WHITE, 1.4)
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
	# faixa com o nome da festa (só se os preparativos/decoração foram pagos)
	if deco:
		var bp: = c + Vector3(0, 0, -3.4)
		bp.y = _ground(bp.x, bp.z)
		if Real.place(party_root, "g:party_banner", bp, -1.0, 0.0, Color.WHITE, 0.0, false):
			var lb: = B.label(party_root, title, bp + Vector3(0, 2.4, 0.07), 60, Color(0.75, 0.1, 0.2), Color(1, 1, 1, 0.0))
			lb.pixel_size = 0.0045
		for k in 3:
			var a: = c + Vector3(-9.0, 4.2, -2.0 + k * 3.0)
			var b: = c + Vector3(9.0, 4.2, -2.0 + k * 3.0)
			D.bunting(party_root, a, b, 0.9)
		var la: = c + Vector3(-8.0, 3.0, 5.5)
		var lb2: = c + Vector3(8.0, 3.0, 5.5)
		if world.has_method("_string_lights"):
			world.call("_string_lights", la, lb2, 24)
	else:
		D.bunting(party_root, c + Vector3(-6.0, 4.0, 0.0), c + Vector3(6.0, 4.0, 0.0), 0.7)

func _flame_mat() -> Material:
	return P.glow(Color(1.0, 0.55, 0.15), 4.0)

# ------------------------------------------------------------------ passeios
func _on_tour(id: String, _pax: int, _rev: int) -> void :
	if id == "farol":
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
	var out: = Vector3(pier_x - 12.0, -0.25, -150.0)
	var tw: = create_tween()
	tw.tween_property(_boat, "position", out, 38.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_interval(6.0)
	tw.tween_callback(func(): if is_instance_valid(_boat): _boat.rotation.y = 0.0)
	tw.tween_property(_boat, "position", start, 38.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_callback(func():
		if is_instance_valid(_boat):
			_boat.queue_free()
		_boat = null)

func _process(delta: float) -> void :
	_t += delta
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
