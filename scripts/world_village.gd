extends "res://scripts/world.gd"




const STREET_Z: = 30.0
const HOME_C: = Vector3(46, 0, 21)
const KIOSK_C: = Vector3(38, 0, -13)
const CHURCH_C: = Vector3(75, 0, 50)
const PRACA: = Rect2(66, 34.5, 18, 9.3)

var company_signs: Array = []
var _painted: Array = []
var _sign_panels: Array = []
var _table_looks: Array = []
var _table_menus: Array = []
var _look_key := ""

var village_points: = {}
var village_paths: Array = []
var kiosk_root: Node3D
var kiosk_counter: Interactable
var kiosk_spots: Array = []
var bed: Interactable
var home_wake: = Vector3(HOME_C.x - 0.8, 0.2, HOME_C.z - 0.6)
var bench_spots: Array = []
var market: Interactable
var quest_board: Interactable
var coco_piles: Array = []
var coco_spots: Array = []
var coco_piles_taken: Array = []
var fish_spot: Interactable
var VM: = {}
var _kiosk_board: Node3D
var _open_sign: Label3D
var _lighthouse: Node3D
var _night: = 0.0
var _kiosk_menu_c: = Vector3.ZERO
var block_rects: Array = []
var _bloom_xf: Array = []
var _bloom_col: Array = []

func _ready() -> void :
	add_to_group("world_dyn")
	super._ready()
	_village_materials()
	_street()
	_houses()
	_hero_house()
	_church_and_praca()
	_quiosque()
	_barraca()
	_village_props()
	_street_lamps()
	_village_palms()
	_village_routes()
	_village_expansion()
	_beach_life()
	_landmark_details()
	_map_details()
	_finish_blooms()
	Core.company_changed.connect(_refresh_company_signs)
	_refresh_company_signs()
	Core.time_changed.connect(_on_time)

func _village_materials() -> void :
	VM.road = B.mat("cobblestone_floor_04", 0.4, Color(0.92, 0.9, 0.86), 0.9)
	VM.calcada = B.mat("calcada", 0.55, Color(1, 1, 1), 0.85)
	VM.curb = B.mat("light_stone", 1.2, Color(0.92, 0.92, 0.9), 0.8)
	var clay: = B.mat("clay_roof_tiles_02", 0.55, Color(1, 1, 1), 0.8).duplicate()
	clay.cull_mode = BaseMaterial3D.CULL_DISABLED
	VM.clay = clay
	VM.stone = B.mat("cobblestone_floor_04", 0.8, Color(0.97, 0.92, 0.86), 0.9)
	VM.trim = B.mat("white_stucco", 0.5, Color(0.97, 0.96, 0.93), 0.85)
	VM.floor = B.mat("terracotta_floor_tiles", 0.7, Color(1, 1, 1), 0.6)
	VM.door = B.mat("weathered_planks", 0.9, Color(0.45, 0.28, 0.16), 0.7)
	var glass: = StandardMaterial3D.new()
	glass.albedo_color = Color(0.62, 0.78, 0.88, 0.7)
	glass.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	glass.roughness = 0.08
	glass.metallic = 0.04
	glass.emission_enabled = true
	glass.emission = Color(1.0, 0.64, 0.3)
	glass.emission_energy_multiplier = 0.0
	glass.cull_mode = BaseMaterial3D.CULL_DISABLED
	# Vidro das janelas separado das lâmpadas: neutro, sem emissão nem tinta.
	var window_glass := glass.duplicate() as StandardMaterial3D
	window_glass.albedo_color = Color(1, 1, 1, 0.16)
	window_glass.metallic = 0.0
	window_glass.emission_enabled = false
	window_glass.resource_name = "clear_window_glass"
	VM.window_glass = window_glass
	VM.glass = glass
	# v0.9.5: cada casa acende e apaga a luz numa hora diferente (3 grupos de janelas)
	VM.glass_b = glass.duplicate()
	VM.glass_c = glass.duplicate()

func stucco(c: Color) -> Material:
	return B.mat("white_stucco", 0.5, c, 0.88)

func wood_tint(c: Color) -> Material:
	return B.mat("weathered_planks", 0.9, c, 0.7)

## Banco de madeira pintado (Poly Haven). O modelo original tem o assento a 0,65 m (alto demais para o "sentado" da animação):
## achatado para 0,46 m. Devolve o lugar de sentar: a raiz do personagem fica 0,3 m à frente do meio do assento
## (na animação Sitting_Idle a bacia fica 0,33 m atrás da raiz e o bumbum a 0,46 m de altura).
const SEAT_DROP: = 0.455
func _bench(p: Vector3, rot: float, parent: Node = null) -> Dictionary:
	var par: Node = parent if parent else self
	var b: = B.model(par, "painted_wooden_bench", p, rot, 1.0)
	b.scale = Vector3(1.0, 0.7, 1.0)
	if parent == null:
		_block(p, 1.0, 1.0, 0.12)
	var local: = Vector3(0.06, 0.0, -0.062 + 0.3).rotated(Vector3.UP, rot)
	return {"pos": p + local + Vector3(0, 0.457 - SEAT_DROP, 0), "rot": rot, "anim": "Sitting_Idle_Loop", "busy": false}

func _front_at(x: float, street_z: float, side: float) -> Array:
	for hf in _house_fronts:
		if x >= hf[0] and x <= hf[1] and signf(street_z - hf[2]) == side and absf(street_z - hf[2]) < 8.0:
			return hf
	return []

func _street_bunting(street_z: float, spacing: float) -> void :
	var x: = 0.0
	while x < 110.0:
		var fn: = _front_at(x, street_z, 1.0)
		var fs: = _front_at(x + 3.0, street_z, -1.0)
		if not fn.is_empty() and not fs.is_empty():
			# sobrado: prende sob a cornija de cima (6,1 m), longe da sacada
			var a: = Vector3(x, 6.15 if fn[4] > 5.0 else 3.38, fn[2] + 0.1)
			var b: = Vector3(x + 3.0, 6.15 if fs[4] > 5.0 else 3.38, fs[2] - 0.1)
			D.bunting(self, a, b, 0.45)
			for e in [[a, 0.0], [b, PI]]:
				var hk: = Real.place(self, "g:brass_knob", e[0], -1.6, 0.0, Color(0.55, 0.55, 0.58), 0.0, false)
				if hk:
					hk.rotation.x = PI * 0.5 if e[1] == 0.0 else - PI * 0.5
			x += spacing
		else:
			x += 1.0

func _block(c: Vector3, w: float, d: float, pad: = 0.42) -> void :
	block_rects.append(Rect2(c.x - w * 0.5 - pad, c.z - d * 0.5 - pad, w + pad * 2.0, d + pad * 2.0))

func _occlude(c: Vector3, w: float, d: float, h: float) -> void :
	var occ: = OccluderInstance3D.new()
	var box: = BoxOccluder3D.new()
	box.size = Vector3(w, h, d)
	occ.occluder = box
	occ.position = c + Vector3(0, h * 0.5, 0)
	add_child(occ)

func _bloom(p: Vector3, yaw: float, col: Color, s: = 1.0) -> void :
	var basis: = Basis(Vector3.UP, yaw).scaled(Vector3(s, s * 1.15, s))
	_bloom_xf.append(Transform3D(basis, p))
	_bloom_col.append(col)

func _flower_box(p: Vector3, yaw: float, col: Color) -> void :
	var wood: = wood_tint(Color(0.4, 0.24, 0.12))
	B.box(self, Vector3(0.95, 0.16, 0.28), p, wood, false, yaw)
	for i in 4:
		var ox: = -0.3 + float(i) * 0.2
		_bloom(p + Vector3(cos(yaw) * ox, 0.16, - sin(yaw) * ox), yaw, col, 0.55)

func _juliet(c: Vector3, front: float, w: float, d: float) -> void :
	var wood: = wood_tint(Color(0.38, 0.22, 0.12))
	var x: = c.x - w * 0.22
	var z: = c.z + front * (d * 0.5 + 0.16)
	B.box(self, Vector3(1.35, 0.05, 0.06), Vector3(x, 1.15, z), wood)
	for sx in [-0.62, 0.62]:
		B.box(self, Vector3(0.045, 0.42, 0.045), Vector3(x + sx, 1.34, z), wood)
	_flower_box(Vector3(x, 1.08, z + front * 0.12), 0.0 if front > 0.0 else PI, Color(0.9, 0.25, 0.45))

## Primavera (buganvília) plantada num vaso, subindo por uma treliça encostada na parede (v0.7.3).
## p = chão logo à frente da parede; front = +1/-1 para que lado a parede fica (atrás do vaso).
func _bougainvillea(p: Vector3, front: float) -> void :
	var cols: = [Color(0.86, 0.12, 0.42), Color(0.95, 0.42, 0.12), Color(0.62, 0.18, 0.72), Color(0.96, 0.82, 0.88)]
	var wood: = wood_tint(Color(0.45, 0.28, 0.14))
	var back: = - front * 0.18
	# v0.9.5: vaso torneado, treliça de ripas e galhos num modelo só (Blender); antes eram cilindros e caixas
	if Real.place(self, "g:trellis_planter", p, -1.0, 0.0 if front > 0.0 else PI, Color.WHITE, 0.0, false) == null:
		var clay_m: = B.flat(Color(0.82, 0.42, 0.26), 0.8)
		B.cyl(self, 0.24, 0.18, 0.38, p + Vector3(0, 0.19, 0), clay_m, 24)
		for sx in [-0.42, 0.42]:
			B.box(self, Vector3(0.04, 2.5, 0.04), p + Vector3(sx, 1.25, back), wood)
		for k in 5:
			B.box(self, Vector3(0.9, 0.03, 0.03), p + Vector3(0, 0.7 + k * 0.42, back), wood)
	var rng: = RandomNumberGenerator.new()
	rng.seed = int(p.x * 13.0 + p.z * 7.0)
	for i in 26:
		var h: = rng.randf_range(0.6, 2.55)
		var q: = p + Vector3(rng.randf_range(-0.5, 0.5), h, back + rng.randf_range(-0.08, 0.14) * front)
		if i % 3 == 0:
			_bloom(q, 0.0, Color(0.2, 0.5, 0.2).lerp(Color(0.32, 0.62, 0.25), rng.randf()), rng.randf_range(0.75, 1.0))
		else:
			_bloom(q, 0.0, cols[i % cols.size()], rng.randf_range(0.5, 0.75))

const BLOOM_KEYS: = {"magenta": Color(0.86, 0.12, 0.42), "laranja": Color(0.95, 0.42, 0.12), "roxa": Color(0.62, 0.18, 0.72), "rosa": Color(0.96, 0.62, 0.78)}

func _bloom_key(c: Color) -> String:
	if c.g > c.r and c.g > c.b:
		return "folhas"
	var best: = "magenta"
	var bd: = 99.0
	for k in BLOOM_KEYS:
		var o: Color = BLOOM_KEYS[k]
		var d: = Vector3(c.r - o.r, c.g - o.g, c.b - o.b).length()
		if d < bd:
			bd = d
			best = k
	return best

## Folhagem e flores: ramos de buganvília modelados no Blender (folhas ovais, brácteas de papel e florzinhas), em MultiMesh por cor.
## Nada de bolinhas coloridas (regra do Sergio). Sem o modelo, usa a bolinha antiga como último recurso.
func _finish_blooms() -> void :
	if _bloom_xf.is_empty():
		return
	var groups: = {}
	for i in _bloom_xf.size():
		var k: = _bloom_key(_bloom_col[i])
		if not groups.has(k):
			groups[k] = []
		groups[k].append(i)
	for k in groups:
		var mesh: Mesh = Real.mesh_of("g:bloom_" + k)
		var idx: Array = groups[k]
		if mesh == null:
			continue
		var mm: = MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		mm.instance_count = idx.size()
		for n in idx.size():
			var xf: Transform3D = _bloom_xf[idx[n]]
			var rng_yaw: = float((idx[n] * 7919) % 628) / 100.0
			xf.basis = xf.basis * Basis(Vector3.UP, rng_yaw).scaled(Vector3.ONE * 1.7)
			mm.set_instance_transform(n, xf)
		var mi: = MultiMeshInstance3D.new()
		mi.multimesh = mm
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.visibility_range_end = 70.0
		add_child(mi)

func _fence(a: Vector3, b: Vector3) -> void :
	var wood: = wood_tint(Color(0.42, 0.26, 0.14))
	var dir: = b - a
	var L: = Vector2(dir.x, dir.z).length()
	if L < 0.4:
		return
	var n: = maxi(int(L / 1.5), 1)
	var yaw: = atan2(dir.x, dir.z)
	for i in n + 1:
		var t: = float(i) / float(n)
		var p: = a.lerp(b, t)
		B.box(self, Vector3(0.08, 0.95, 0.08), p + Vector3(0, 0.48, 0), wood)
	var mid: = a.lerp(b, 0.5)
	var rail: = B.box(self, Vector3(0.06, 0.06, L), mid + Vector3(0, 0.72, 0), wood, false, yaw)
	rail.rotation.y = yaw
	var rail2: = B.box(self, Vector3(0.05, 0.05, L), mid + Vector3(0, 0.38, 0), wood)
	rail2.rotation.y = yaw


func _street() -> void :
	var x0: = 1.3
	var x1: = 99.0
	var L: = x1 - x0
	var cx: = (x0 + x1) * 0.5
	B.box(self, Vector3(L, 0.05, 4.0), Vector3(cx, 0.02, STREET_Z), VM.road)
	for side in [-1.0, 1.0]:
		var z_side: float = STREET_Z + side * 2.9
		B.platform(self, Vector3(L, 0.3, 1.8), Vector3(cx, 0.0, z_side), VM.calcada, 0.35)
		B.box(self, Vector3(L, 0.32, 0.22), Vector3(cx, 0.0, STREET_Z + side * 2.05), VM.curb)

	B.box(self, Vector3(2.4, 0.06, 24.0), Vector3(38, 0.03, 15.0), VM.calcada)
	B.box(self, Vector3(1.5, 0.04, 4.5), Vector3(38, 0.035, 2.4), M.deckwood)
	village_points.street_w = Vector3(2.5, 0.15, STREET_Z - 2.9)

	# v0.9.3: bancos fora das varandas (antes um caía dentro do piso da varanda e outro atravessava a coluna)
	for spot in [[Vector3(55.6, 0.15, 26.6), 0.0], [Vector3(81.0, 0.15, 26.6), 0.0], [Vector3(50.0, 0.15, 33.4), PI], [Vector3(96.8, 0.15, 33.4), PI]]:
		bench_spots.append(_bench(spot[0], spot[1]))

func _facade(c: Vector3, n: Vector3, half: float, offset: float, kind: String, col: Color, base_y: = 0.0) -> void :
	# v0.7.2: portas almofadadas com bandeira e degrau; janelas com caixilho em cruz e venezianas ripadas
	var t: = Vector3( - n.z, 0, n.x)
	var rot: = atan2(n.x, n.z)
	var p: = c + n * (half + 0.03) + t * offset
	var leaf_m: = wood_tint(col)
	var dark: = wood_tint(col.darkened(0.35))
	var piv: = Node3D.new()
	piv.position = p + Vector3(0, base_y, 0)
	piv.rotation.y = rot
	add_child(piv)
	if kind == "door":
		var dframe: Node3D = Real.place_glow(piv, "g:door_frame", Vector3.ZERO, -1.0, 0.0, VM.window_glass)
		var dleaf: Node3D = Real.place(piv, "g:door_leaf", Vector3.ZERO, -1.0, 0.0, col.lightened(0.3), 0.0, false)
		if dframe == null or dleaf == null:
			B.box(piv, Vector3(1.36, 2.95, 0.1), Vector3(0, 1.47, 0), VM.trim)
			B.box(piv, Vector3(1.05, 2.2, 0.1), Vector3(0, 1.1, 0.03), leaf_m)
			for py in [0.55, 1.15, 1.75]:
				for px in [-0.24, 0.24]:
					B.box(piv, Vector3(0.36, 0.42, 0.04), Vector3(px, py, 0.09), dark)
					B.box(piv, Vector3(0.28, 0.34, 0.04), Vector3(px, py, 0.11), leaf_m)
			B.box(piv, Vector3(1.05, 0.45, 0.06), Vector3(0, 2.48, 0.02), VM.window_glass)
			for k in 3:
				B.box(piv, Vector3(0.03, 0.42, 0.05), Vector3(-0.26 + k * 0.26, 2.48, 0.06), VM.trim)
			B.box(piv, Vector3(1.6, 0.14, 0.5), Vector3(0, 0.07, 0.26), VM.curb)
			# marquise de telha sobre a porta, com duas mãos-francesas
			var hood: = B.box(piv, Vector3(1.9, 0.07, 0.78), Vector3(0, 3.12, 0.38), VM.clay)
			hood.rotation.x = 0.2
			B.box(piv, Vector3(1.92, 0.05, 0.06), Vector3(0, 3.0, 0.74), VM.trim)
			for sx in [-1.0, 1.0]:
				var br: = B.box(piv, Vector3(0.07, 0.07, 0.62), Vector3(sx * 0.78, 2.98, 0.34), dark)
				br.rotation.x = 0.3
		var knob: = Real.place(piv, "g:brass_knob", Vector3(0.38, 1.05, 0.075), -1.0, 0.0, Color.WHITE, 0.0, false)
		if knob != null:
			knob.rotation.x = PI * 0.5
		else:
			B.sphere(piv, 0.04, Vector3(0.38, 1.05, 0.14), B.flat(Color(0.95, 0.78, 0.3), 0.25, 0.6))
		# numero da casa e luminária de parede
		var num: = absi(int(c.x * 3.0 + c.z)) % 300 + 1
		B.box(piv, Vector3(0.24, 0.18, 0.03), Vector3(-0.9, 1.9, 0.04), B.flat(Color(0.15, 0.4, 0.75), 0.4))
		var nl: = B.label(piv, str(num), Vector3(-0.9, 1.9, 0.062), 32, Color.WHITE, Color(0.1, 0.25, 0.5, 1))
		nl.pixel_size = 0.004
		B.box(piv, Vector3(0.08, 0.08, 0.2), Vector3(0.9, 2.55, 0.1), dark)
		if Real.place_glow(piv, "g:lamp_bulb", Vector3(0.9, 2.28, 0.22), -1.5, 0.0, VM.glass) == null:
			B.cyl(piv, 0.09, 0.07, 0.22, Vector3(0.9, 2.45, 0.22), VM.glass, 10)
			B.cyl(piv, 0.11, 0.02, 0.08, Vector3(0.9, 2.6, 0.22), dark, 10)
	else:
		var wframe: Node3D = Real.place_glow(piv, "g:win_frame", Vector3.ZERO, -1.0, 0.0, VM.window_glass)
		var wshut: Node3D = Real.place(piv, "g:win_shutters", Vector3.ZERO, -1.0, 0.0, col, 0.0, false)
		if wframe == null or wshut == null:
			B.box(piv, Vector3(1.4, 1.65, 0.1), Vector3(0, 1.75, 0), VM.trim)
			B.box(piv, Vector3(1.1, 1.35, 0.06), Vector3(0, 1.75, 0.01), VM.window_glass)
			# caixilho em cruz
			B.box(piv, Vector3(0.05, 1.35, 0.06), Vector3(0, 1.75, 0.04), VM.trim)
			B.box(piv, Vector3(1.1, 0.05, 0.06), Vector3(0, 1.9, 0.04), VM.trim)
			B.box(piv, Vector3(1.62, 0.09, 0.24), Vector3(0, 0.95, 0.08), VM.trim)
			B.box(piv, Vector3(1.55, 0.12, 0.14), Vector3(0, 2.62, 0.04), VM.trim)
			# verga com pedra-chave, cimalha e mísulas sob o peitoril
			B.box(piv, Vector3(1.78, 0.09, 0.2), Vector3(0, 2.74, 0.06), VM.trim)
			B.box(piv, Vector3(0.26, 0.24, 0.22), Vector3(0, 2.66, 0.07), VM.trim)
			for sx in [-1.0, 1.0]:
				B.box(piv, Vector3(0.1, 0.2, 0.16), Vector3(sx * 0.6, 0.82, 0.07), VM.trim)
				B.box(piv, Vector3(0.08, 0.08, 0.1), Vector3(sx * 0.6, 0.7, 0.06), VM.trim)
			# venezianas abertas com ripas
			for sd in [-1.0, 1.0]:
				var hinge: = Node3D.new()
				hinge.position = Vector3(sd * 0.64, 1.75, 0.04)
				hinge.rotation.y = sd * 1.05
				piv.add_child(hinge)
				B.box(hinge, Vector3(0.52, 1.32, 0.035), Vector3(sd * 0.26, 0, 0.02), leaf_m)
				for k in 9:
					var slat: = B.box(hinge, Vector3(0.42, 0.06, 0.03), Vector3(sd * 0.26, -0.52 + k * 0.13, 0.045), dark)
					slat.rotation.x = 0.5
			# grade de ferro baixinha
			var iron: = B.flat(Color(0.12, 0.12, 0.14), 0.5, 0.4)
			B.box(piv, Vector3(1.2, 0.03, 0.03), Vector3(0, 1.32, 0.14), iron)
			for k in 7:
				B.box(piv, Vector3(0.025, 0.32, 0.025), Vector3(-0.54 + k * 0.18, 1.16, 0.14), iron)

## Detalhes extras de uma casa: cornija dupla, faixa colorida, caibros, calha, chaminé, antena, ar-condicionado.
func _house_extras(c: Vector3, w: float, d: float, h: float, front: float, col: Color, shutter: Color, eaves: = true) -> void :
	var rng: = RandomNumberGenerator.new()
	rng.seed = int(c.x * 17.0 + c.z * 5.0)
	B.box(self, Vector3(w + 0.06, 0.26, d + 0.06), c + Vector3(0, h - 0.45, 0), stucco(shutter.lightened(0.45)))
	var gm: = B.flat(Color(0.88, 0.88, 0.85), 0.5, 0.3)
	if eaves:
		B.box(self, Vector3(w + 0.32, 0.1, d + 0.32), c + Vector3(0, h + 0.06, 0), VM.trim)
		# caibros aparentes sob o beiral (frente e fundos)
		var xfs: = []
		var k: = - w * 0.5 - 0.6
		while k <= w * 0.5 + 0.6:
			for sz in [-1.0, 1.0]:
				xfs.append(Transform3D(Basis(), c + Vector3(k, h + 0.0, sz * (d * 0.5 + 0.45))))
			k += 0.55
		var rm: = BoxMesh.new()
		rm.size = Vector3(0.09, 0.12, 0.9)
		D.multimesh(self, rm, xfs, [], wood_tint(Color(0.5, 0.3, 0.16)))
		# calha e cano na frente
		var gz: = c.z + front * (d * 0.5 + 0.86)
		var gut: = B.cyl(self, 0.06, 0.06, w + 1.7, Vector3(c.x, h + 0.02, gz), gm, 12)
		gut.rotation.z = PI * 0.5
		B.cyl(self, 0.045, 0.045, h, Vector3(c.x + w * 0.5 + 0.8, h * 0.5, gz), gm, 10)
	if rng.randf() < 0.45:
		var chx: = c.x + rng.randf_range(- w * 0.25, w * 0.25)
		B.box(self, Vector3(0.6, 1.4, 0.6), Vector3(chx, h + 1.6, c.z - front * d * 0.18), stucco(col.darkened(0.15)))
		B.box(self, Vector3(0.75, 0.12, 0.75), Vector3(chx, h + 2.35, c.z - front * d * 0.18), VM.trim)
	if rng.randf() < 0.3:
		# antena yagi do Blender no telhado (antes: varetas de caixa)
		var ax: = c.x - w * 0.3
		Real.place(self, "g:tv_antenna", Vector3(ax, h + (0.55 if eaves else 0.1), c.z), -1.0, 0.3, Color.WHITE, 0.0, false)
	if rng.randf() < 0.35:
		# ar-condicionado split na parede lateral (Blender: grade, ventilador, suportes e cano)
		var side: = 1.0 if rng.randf() < 0.5 else -1.0
		Real.place(self, "g:ac_unit", Vector3(c.x + side * (w * 0.5 + 0.02), 2.1, c.z), -1.0, side * PI * 0.5, Color.WHITE, 0.0, false)
	# relógio de luz ao lado da porta
	B.box(self, Vector3(0.35, 0.45, 0.14), c + Vector3(- w * 0.42 * front, 1.5, front * (d * 0.5 + 0.08)), B.flat(Color(0.75, 0.78, 0.8), 0.5))
	# vaso pendurado
	if rng.randf() < 0.5:
		# v0.9.3: mais alto (a hera descia até 1,6 m e atravessava a cabeça de quem passava na porta)
		var vp: = c + Vector3(w * 0.1 * front, 3.0, front * (d * 0.5 + 0.35))
		B.cyl(self, 0.012, 0.012, h - 3.0, vp + Vector3(0, (h - 3.0) * 0.5, 0), B.flat(Color(0.3, 0.25, 0.2)), 8)
		# vaso de barro com hera em cascata: modelo do Blender (centro do vaso a 0,97 m do ponto mais baixo)
		if Real.place(self, "g:hanging_planter", vp - Vector3(0, 0.97, 0), -1.0, 0.0, Color.WHITE, 0.0, false) == null:
			B.cyl(self, 0.14, 0.1, 0.18, vp, B.flat(Color(0.85, 0.45, 0.3), 0.8), 14)

var _house_fronts: Array = []
var house_doors: Array = []   # v0.9.5: os moradores entram em casa à noite
## v0.9.3: variedade de casas. Estilo sorteado pela posição (estável): 0 térrea de telhado, 1 sobrado com sacada de ferro,
## 2 platibanda (fachada reta escondendo o telhado, com frontão e ano), 3 casa de madeira (tábuas pintadas). Telhado em 4 tons.
const ROOF_TINTS: = [Color(1, 1, 1), Color(0.55, 0.36, 0.3), Color(1.15, 0.92, 0.78), Color(0.5, 0.56, 0.64)]
var _roof_mats: = {}
func _roof_mat(i: int) -> Material:
	if not _roof_mats.has(i):
		var m: StandardMaterial3D = VM.clay.duplicate()
		m.albedo_color = m.albedo_color * ROOF_TINTS[i]
		_roof_mats[i] = m
	return _roof_mats[i]

func _house(c: Vector3, w: float, d: float, front: float, col: Color, shutter: Color, porch: bool, sign_text: = "") -> void :
	var hr: = RandomNumberGenerator.new()
	hr.seed = int(c.x * 131.0 + c.z * 17.0) + 5
	var style: = hr.randi() % 4
	if sign_text != "" and style == 3:
		style = 0
	var h: = 6.3 if style == 1 else 3.5
	_house_fronts.append([c.x - w * 0.5 + 0.4, c.x + w * 0.5 - 0.4, c.z + d * 0.5 * front, front, h])
	house_doors.append(Vector3(c.x - w * 0.18 * front, 0.12, c.z + front * (d * 0.5 + (1.6 if porch else 0.55))))
	var glass_keep: Material = VM.glass
	VM.glass = [VM.glass, VM.get("glass_b", VM.glass), VM.get("glass_c", VM.glass)][hr.randi() % 3]
	var wall_m: Material = stucco(col)
	if style == 3:
		wall_m = B.mat("weathered_planks", 0.45, col.lightened(0.15), 0.85)
	var body: = B.box(self, Vector3(w, h, d), c + Vector3(0, h * 0.5, 0), wall_m, true)
	body.name = "house"
	B.box(self, Vector3(w + 0.06, 0.7, d + 0.06), c + Vector3(0, 0.35, 0), VM.stone)
	B.box(self, Vector3(w + 0.14, 0.07, d + 0.14), c + Vector3(0, 0.72, 0), VM.trim)
	B.box(self, Vector3(w + 0.16, 0.28, d + 0.16), c + Vector3(0, h - 0.1, 0), VM.trim)
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.box(self, Vector3(0.32, h, 0.32), c + Vector3(sx * w * 0.5, h * 0.5, sz * d * 0.5), VM.trim)
	var n: = Vector3(0, 0, front)
	_facade(c, n, d * 0.5, - w * 0.18 * front, "door", shutter)
	_facade(c, n, d * 0.5, w * 0.22 * front, "window", shutter)
	if w > 7.5:
		_facade(c, n, d * 0.5, - w * 0.38 * front, "window", shutter)
	_facade(c, - n, d * 0.5, 0.0, "window", shutter)
	_facade(c, Vector3(1, 0, 0), w * 0.5, 0.0, "window", shutter)
	_facade(c, Vector3(-1, 0, 0), w * 0.5, 0.0, "window", shutter)
	var roof_m: = _roof_mat(hr.randi() % ROOF_TINTS.size())
	if style == 1:
		# sobrado: faixa entre andares, janelas de cima e sacada com gradil de ferro (sem sacada se tiver varanda embaixo)
		B.box(self, Vector3(w + 0.14, 0.12, d + 0.14), c + Vector3(0, 3.0, 0), VM.trim)
		_facade(c, n, d * 0.5, - w * 0.18 * front, "window", shutter, 2.95)
		_facade(c, n, d * 0.5, w * 0.22 * front, "window", shutter, 2.95)
		_facade(c, - n, d * 0.5, 0.0, "window", shutter, 2.95)
		if not porch:
			var bz: = c.z + front * (d * 0.5 + 0.42)
			var bx: = c.x - w * 0.18 * front
			B.box(self, Vector3(2.3, 0.14, 0.9), Vector3(bx, 2.98, bz), VM.trim)
			if Real.place(self, "g:balcony_rail", Vector3(bx, 3.05, bz + front * 0.42), -1.0, 0.0 if front > 0 else PI, Color.WHITE, 0.0, false) != null:
				for sx in [-1.0, 1.0]:
					var side: = Real.place(self, "g:balcony_rail", Vector3(bx + sx * 1.13, 3.05, bz), -1.0, PI * 0.5, Color.WHITE, 0.0, false)
					if side:
						side.scale = Vector3(1.0, 1.0, 1.0)
						side.get_child(0).scale = Vector3(0.42, 1.0, 1.0)
		B.hip_roof(self, c + Vector3(0, h + 0.05, 0), w + 1.75, d + 1.75, 2.05, roof_m, 0.14)
	elif style == 2:
		# platibanda: telhado baixo escondido atrás de mureta reta com cornija, frontão no meio e o ano da casa
		var ph: = 1.0
		B.hip_roof(self, c + Vector3(0, h + 0.05, 0), w - 0.3, d - 0.3, 0.8, roof_m, 0.12)
		for sz in [-1.0, 1.0]:
			B.box(self, Vector3(w + 0.1, ph, 0.2), c + Vector3(0, h + ph * 0.5, sz * (d * 0.5 - 0.05)), stucco(col))
			B.box(self, Vector3(w + 0.3, 0.12, 0.34), c + Vector3(0, h + ph + 0.06, sz * (d * 0.5 - 0.05)), VM.trim)
		for sx in [-1.0, 1.0]:
			B.box(self, Vector3(0.2, ph, d + 0.1), c + Vector3(sx * (w * 0.5 - 0.05), h + ph * 0.5, 0), stucco(col))
			B.box(self, Vector3(0.34, 0.12, d + 0.3), c + Vector3(sx * (w * 0.5 - 0.05), h + ph + 0.06, 0), VM.trim)
		var fz: = c.z + front * (d * 0.5 - 0.05)
		B.box(self, Vector3(2.2, 0.55, 0.22), Vector3(c.x, h + ph + 0.33, fz), stucco(col))
		B.box(self, Vector3(2.4, 0.1, 0.34), Vector3(c.x, h + ph + 0.65, fz), VM.trim)
		B.box(self, Vector3(w + 0.2, 0.18, 0.26), Vector3(c.x, h + 0.25, fz), stucco(shutter.lightened(0.4)))
		var yr: = B.label(self, str(1928 + hr.randi() % 40), Vector3(c.x, h + ph + 0.3, fz + front * 0.12), 48, Color(0.97, 0.96, 0.93), Color(0.3, 0.25, 0.2, 0.6), 0.0 if front > 0 else PI)
		yr.pixel_size = 0.006
	else:
		B.hip_roof(self, c + Vector3(0, h + 0.05, 0), w + 1.75, d + 1.75, 2.05, roof_m, 0.14)
	VM.glass = glass_keep
	_house_extras(c, w, d, h, front, col, shutter, style != 2)
	_block(c, w, d, 0.4)
	_occlude(c, w * 0.9, d * 0.9, h * 0.9)
	var win_x: = c.x - w * 0.22
	if porch:
		_flower_box(Vector3(win_x, 1.02, c.z + front * (d * 0.5 + 0.2)), 0.0 if front > 0.0 else PI, Color(0.92, 0.28, 0.48).lerp(shutter, 0.35))
	else:
		_juliet(c, front, w, d)
	_bougainvillea(c + Vector3(w * 0.38 * front, 0.0, front * (d * 0.5 + 0.32)), front)
	if porch:
		var pz: = c.z + front * (d * 0.5 + 0.75)
		B.platform(self, Vector3(w - 0.6, 0.18, 1.5), Vector3(c.x, 0.0, pz), stucco(Color(0.75, 0.42, 0.3)), 0.3)
		for sx in [-1.0, 1.0]:
			# coluna torneada do Blender (base, fuste com êntase e capitel); o cilindro de 10 lados ficava facetado
			var cp: = Vector3(c.x + sx * (w * 0.5 - 0.6), 0.18, pz + front * 0.6)
			if Real.place(self, "g:porch_column", cp, 2.62, 0.0, Color(1.0, 0.98, 0.95), 0.0, true) == null:
				B.cyl(self, 0.09, 0.1, 2.6, Vector3(cp.x, 1.3, cp.z), VM.trim, 10)
		var pr: = B.box(self, Vector3(w - 0.2, 0.1, 1.9), Vector3(c.x, 2.75, pz + front * 0.1), VM.clay)
		pr.rotation.x = -0.18 * front
		B.model(self, "painted_wooden_chair_01" if B.has_model("painted_wooden_chair_01") else "wooden_stool_01", Vector3(c.x + w * 0.3, 0.09, pz), PI if front > 0 else 0.0, 1.0)
		B.model(self, "potted_plant_04", Vector3(c.x - w * 0.35, 0.09, pz + front * 0.6), 0.0, 1.0)
	else:
		B.model(self, "potted_plant_01", c + Vector3(w * 0.42, 0, front * (d * 0.5 + 0.45)), 0.0, 1.0)
	if sign_text != "":
		B.box(self, Vector3(3.4, 0.6, 0.08), c + Vector3(0, 2.95, front * (d * 0.5 + 0.1)), VM.door, false, 0.0 if front > 0 else PI)
		B.label(self, sign_text, c + Vector3(0, 2.95, front * (d * 0.5 + 0.15)), 70, Color(1.0, 0.93, 0.75), Color(0.25, 0.12, 0.03, 1), 0.0 if front > 0 else PI)

const HOUSE_COLS: = [Color(0.98, 0.78, 0.45), Color(0.55, 0.78, 0.86), Color(0.96, 0.62, 0.55), Color(0.72, 0.86, 0.62), 
	Color(0.98, 0.9, 0.55), Color(0.82, 0.7, 0.9), Color(0.98, 0.72, 0.78), Color(0.6, 0.85, 0.8), Color(0.95, 0.85, 0.7)]
const SHUT_COLS: = [Color(0.1, 0.45, 0.55), Color(0.15, 0.4, 0.2), Color(0.85, 0.55, 0.1), Color(0.2, 0.3, 0.65), Color(0.6, 0.15, 0.15), Color(0.95, 0.95, 0.9)]

func _houses() -> void :

	var north: = [[54.0, 7.0, false], [62.0, 7.5, true], [80.0, 7.0, false], [88.0, 7.5, true], [96.0, 6.0, false]]
	var i: = 0
	for hh in north:
		_house(Vector3(hh[0], 0, 21.2), hh[1], 7.0, 1.0, HOUSE_COLS[i % HOUSE_COLS.size()], SHUT_COLS[i % SHUT_COLS.size()], hh[2])
		i += 1

	var pc: = Vector3(71, 0, 21.2)
	_house(pc, 9.0, 7.0, 1.0, Color(0.98, 0.86, 0.5), Color(0.6, 0.15, 0.15), false, "Padaria e Mercadinho")
	var awn: = B.box(self, Vector3(8.6, 0.06, 1.8), pc + Vector3(0, 2.6, 4.3), B.mat("rough_linen", 1.0, Color(0.85, 0.2, 0.2), 0.9))
	awn.rotation.x = -0.25
	B.model(self, "wooden_crate_01", pc + Vector3(-3.4, 0.0, 4.2), 0.2, 1.0)
	B.model(self, "wicker_basket_02", pc + Vector3(-2.6, 0.0, 4.4), 0.0, 1.0)
	B.model(self, "plastic_crate_01", pc + Vector3(3.5, 0.0, 4.2), 0.5, 1.0)
	B.model(self, "Shelf_01", pc + Vector3(2.6, 0.0, 4.0), PI, 1.0)
	market = Interactable.new()
	market.name = "Mercadinho"
	var mcs: = CollisionShape3D.new()
	var msh: = BoxShape3D.new()
	msh.size = Vector3(3.2, 2.0, 1.2)
	mcs.shape = msh
	market.add_child(mcs)
	market.position = pc + Vector3(0, 1.1, 4.7)
	village_points.lourdes = pc + Vector3(1.1, 0.1, 3.7)
	_quest_giver("frutas_lourdes", "Dona Lourdes", pc + Vector3(1.1, 1.0, 4.1), Vector3(1.0, 1.8, 0.8))
	market.prompt_fn = func() -> String: return tr("Comprar insumos no mercadinho")
	market.action_fn = func() -> void : get_tree().call_group("hud", "open_office", "insumos", -1)
	add_child(market)

	var south: = [[44.0, 7.0, true], [52.0, 6.5, false], [60.0, 7.5, false], [90.0, 7.0, true], [97.5, 5.5, false]]
	for hh in south:
		_house(Vector3(hh[0], 0, 38.8), hh[1], 7.0, -1.0, HOUSE_COLS[i % HOUSE_COLS.size()], SHUT_COLS[(i + 2) % SHUT_COLS.size()], hh[2])
		i += 1


func _hero_house() -> void :
	var c: = HOME_C
	var w: = 7.0
	var d: = 7.0
	var col: = Color(0.89, 0.87, 0.82)
	var y0: = 0.12
	B.platform(self, Vector3(w + 0.4, 0.24, d + 0.4), c, B.mat("light_stone", 1.0, Color(0.88, 0.91, 0.88), 0.85), 0.4)
	var save: = [M.plaster, M.terracotta, M.teal]
	M.plaster = stucco(col)
	M.terracotta = stucco(col.darkened(0.35))
	M.teal = VM.trim
	var h: = 3.3
	var x0: = c.x - w * 0.5
	var x1: = c.x + w * 0.5
	var zf: = c.z + d * 0.5
	var zb: = c.z - d * 0.5
	_wall_x(x0, x1, zf, h, [[c.x + 1.1, c.x + 2.3, 0.0, 2.35], [c.x - 2.4, c.x - 1.0, 1.0, 2.3]], y0)
	_wall_x(x0, x1, zb, h, [[c.x - 2.6, c.x - 0.2, 0.85, 2.35]], y0)
	_wall_z(zb, zf, x0, h, [[c.z - 0.6, c.z + 0.6, 1.0, 2.3]], y0)
	_wall_z(zb, zf, x1, h, [], y0)
	M.plaster = save[0]
	M.terracotta = save[1]
	M.teal = save[2]
	for sx in [x0, x1]:
		for sz in [zb, zf]:
			B.box(self, Vector3(0.34, h, 0.34), Vector3(sx, y0 + h * 0.5, sz), VM.trim)
	B.box(self, Vector3(w + 0.16, 0.26, d + 0.16), Vector3(c.x, y0 + h - 0.1, c.z), VM.trim)
	B.box(self, Vector3(w - 0.2, 0.06, d - 0.2), Vector3(c.x, y0 + h - 0.05, c.z), M.planks)
	B.hip_roof(self, Vector3(c.x, y0 + h + 0.05, c.z), w + 1.8, d + 1.8, 2.15, VM.clay, 0.14)
	_block(c, w, d, 0.38)
	_occlude(c, w * 0.85, d * 0.85, h * 0.85)
	_bougainvillea(Vector3(x0 + 0.75, 0.0, zf + 0.62), 1.0)

	B.box(self, Vector3(1.35, 1.22, 0.04), Vector3(c.x - 1.7, y0 + 1.65, zf), VM.window_glass)
	B.box(self, Vector3(2.15, 1.4, 0.04), Vector3(c.x - 1.4, y0 + 1.6, zb), VM.window_glass)
	B.box(self, Vector3(0.04, 1.22, 1.15), Vector3(x0, y0 + 1.65, c.z), VM.window_glass)
	B.label(self, "Casa", Vector3(c.x + 1.7, y0 + 2.75, zf + 0.2), 44, Color(1, 1, 1), Color(0.1, 0.25, 0.35, 0.9))

	var home_door := Node3D.new()
	home_door.set_script(load("res://scripts/home_door.gd"))
	home_door.position = Vector3(c.x+2.3,y0,zf)
	add_child(home_door)

	var bc: = Vector3(c.x - 2.15, y0, zb + 1.55)
	var gothic: = B.model(self, "GothicBed_01", bc + Vector3(0.15, 0, 0.55), PI, 1.0)
	gothic.scale = Vector3(0.95, 1.0, 0.92)
	B.model(self, "throw_pillows_01", bc + Vector3(0.05, 0.5, -0.15), 0.0, 0.7)
	B.model(self, "painted_wooden_nightstand", bc + Vector3(1.15, 0, -0.15), PI * 0.5, 0.95)
	B.model(self, "vintage_oil_lamp", bc + Vector3(1.15, 0.585, -0.27), 0.4, 0.9)   # tampo do criado-mudo (0,616 x 0,95)
	B.model(self, "hanging_picture_frame_02", Vector3(bc.x, y0 + 1.7, zb + 0.12), 0.0, 0.85)
	B.model(self, "ceramic_vase_02", bc + Vector3(1.15, 0.585, 0.02), 0.2, 0.5)
	bed = Interactable.new()
	var cs: = CollisionShape3D.new()
	var sh: = BoxShape3D.new()
	sh.size = Vector3(1.7, 1.0, 2.3)
	cs.shape = sh
	bed.add_child(cs)
	bed.position = bc + Vector3(0, 0.6, 0.4)
	bed.name = "Bed"
	add_child(bed)
	B.model(self, "Rockingchair_01", Vector3(c.x + .30, y0 - 0.09, c.z + 2.45), -.65, 0.85)   # origem do modelo abaixo dos balanços
	B.model(self, "electric_stove", Vector3(x1 - 0.5, y0, zb + 1.0), - PI * 0.5, 1.0)
	var fan_root: = Node3D.new()
	fan_root.position = Vector3(c.x, y0 + h - 0.02, c.z)
	add_child(fan_root)
	B.model(fan_root, "ceiling_fan", Vector3.ZERO, 0.2, 0.72)
	Real.place(self, "g:player_home_details", c + Vector3(0,y0,0), -1.0, 0.0, Color.WHITE, 0.0, false)
	B.wall(self, Vector3(.65,.88,2.2), Vector3(x1-.45,y0+.44,zb+2.7))
	B.model(self, "WoodenTable_01", Vector3(c.x + 0.75, y0, c.z - 1.35), 0.0, 1.0)
	B.model(self, "wooden_stool_01", Vector3(c.x + 0.75, y0, c.z - .70), 0.3, 1.0)
	B.model(self, "wooden_stool_01", Vector3(c.x + 0.75, y0, c.z - 2.0), 1.1, 1.0)
	B.model(self, "wooden_bowl_01" if B.has_model("wooden_bowl_01") else "wicker_basket_01", Vector3(c.x + 0.75, y0 + 0.55, c.z - 1.35), 0.0, 1.0)   # tampo da WoodenTable_01 a 0,55 m (flutuava 23 cm)
	B.box(self, Vector3(2.65, 0.015, 2.25), Vector3(c.x - 1.65, y0 + 0.01, c.z + 1.4), B.mat("rough_linen", 1.5, Color(0.58, 0.57, 0.49), 0.95))
	B.model(self, "potted_plant_04", Vector3(x0 + 0.5, y0, zb + 0.5), 0.0, 0.9)
	B.model(self, "planter_box_01", Vector3(c.x - 1.7, 0.0, zf + 0.9), 0.0, 1.0)
	B.model(self, "potted_plant_04", Vector3(x1-.60,y0,zf-.65), 0.3, .85)
	B.model(self, "hanging_picture_frame_02", Vector3(c.x+.40,y0+1.85,zb+.12), 0, .70)
	Real.place(self, "k:plate-dinner", Vector3(x1-.48,y0+.955,zb+3.55), 0,0,Color.WHITE,.22)
	Real.place(self, "g:cup_plastic", Vector3(x1-.50,y0+.945,zb+2.25), .15)
	B.model(self, "ceramic_vase_02", Vector3(x1-.27,y0+1.94,zb+2.15), 0.2, .45)
	B.model(self, "book_encyclopedia_set_01", Vector3(x1-.27,y0+1.94,zb+3.22), PI*.5, .4)
	var lounge := Node3D.new()
	lounge.set_script(load("res://scripts/home_furnishings.gd"))
	lounge.name = "HomeLounge"
	lounge.position = c + Vector3(0,y0,0)
	add_child(lounge)
	var l: = OmniLight3D.new()
	l.position = Vector3(c.x, y0 + 2.8, c.z)
	l.omni_range = 7.0
	l.light_color = Color(1.0, 0.96, 0.89)
	add_child(l)
	l.shadow_enabled = Quality.hd
	lanterns.append([l, null, 1.3, true])
	village_points.home_door_out = Vector3(c.x + 1.7, 0.15, zf + 1.2)
	village_points.home_door_in = Vector3(c.x + 1.7, 0.15, zf - 0.8)


func _church_and_praca() -> void :
	var r: = PRACA
	var pc: = Vector3(r.get_center().x, 0, r.get_center().y)
	B.platform(self, Vector3(r.size.x, 0.2, r.size.y), pc, VM.calcada, 0.4)
	var c: = CHURCH_C
	var w: = 10.0
	var d: = 12.0
	var h: = 7.0
	var white: = stucco(Color(0.98, 0.97, 0.94))
	var blue: = stucco(Color(0.2, 0.42, 0.72))
	var yellow: = stucco(Color(0.98, 0.8, 0.3))
	B.box(self, Vector3(w, h, d), c + Vector3(0, h * 0.5, 0), white, true)
	_block(c, w, d, 0.5)
	_occlude(c, w * 0.92, d * 0.92, h)
	B.box(self, Vector3(w + 0.06, 0.8, d + 0.06), c + Vector3(0, 0.4, 0), blue)
	for sx in [-1.0, 1.0]:
		B.box(self, Vector3(0.5, h, 0.5), c + Vector3(sx * w * 0.5, h * 0.5, - d * 0.5), yellow)
	B.box(self, Vector3(w + 0.3, 0.35, 0.5), c + Vector3(0, h, - d * 0.5), yellow)

	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var fz: = c.z - d * 0.5 - 0.02
	var pts: = [Vector3(c.x - w * 0.5, h + 0.15, fz), Vector3(c.x, h + 3.2, fz), Vector3(c.x + w * 0.5, h + 0.15, fz)]
	for v in pts:
		st.set_normal(Vector3(0, 0, -1))
		st.set_uv(Vector2(v.x, v.y) * 0.5)
		st.add_vertex(v)
	var ped: = MeshInstance3D.new()
	ped.mesh = st.commit()
	var pm: StandardMaterial3D = white.duplicate()
	pm.cull_mode = BaseMaterial3D.CULL_DISABLED
	ped.material_override = pm
	add_child(ped)
	B.hip_roof(self, c + Vector3(0, h + 0.1, 0.3), w + 0.8, d + 0.6, 3.1, VM.clay, 0.14)
	_facade(c, Vector3(0, 0, -1), d * 0.5, 0.0, "door", Color(0.45, 0.25, 0.12))
	B.box(self, Vector3(2.0, 3.6, 0.1), c + Vector3(0, 1.8, - d * 0.5 - 0.06), wood_tint(Color(0.45, 0.25, 0.12)))
	for sx in [-1.0, 1.0]:
		_facade(c + Vector3(0, 2.0, 0), Vector3(0, 0, -1), d * 0.5, sx * 2.8, "window", Color(0.2, 0.42, 0.72))
	if Real.place(self, "g:rose_window", c + Vector3(0, h + 1.6 - 0.64, - d * 0.5 - 0.05), -1.0, 0.0, Color.WHITE, 0.0, false) == null:
		B.sphere(self, 0.6, c + Vector3(0, h + 1.6, - d * 0.5 - 0.05), B.flat(Color(0.25, 0.45, 0.75), 0.3), Vector3(1, 1, 0.15))

	var tc: = c + Vector3(w * 0.5 + 1.6, 0, - d * 0.5 + 1.6)
	B.box(self, Vector3(3.2, 13.0, 3.2), tc + Vector3(0, 6.5, 0), white, true)
	_block(tc, 3.2, 3.2, 0.35)
	_occlude(tc, 3.0, 3.0, 12.5)
	B.box(self, Vector3(4.4, 0.16, 1.1), c + Vector3(0, 0.1, - d * 0.5 - 0.55), VM.curb)
	B.box(self, Vector3(3.2, 0.16, 0.7), c + Vector3(0, 0.22, - d * 0.5 - 0.95), VM.curb)
	B.box(self, Vector3(3.3, 0.7, 3.3), tc + Vector3(0, 0.35, 0), blue)
	for k in [4.5, 9.0, 12.8]:
		B.box(self, Vector3(3.45, 0.3, 3.45), tc + Vector3(0, k, 0), yellow)
	for n in [Vector3(0, 0, -1), Vector3(1, 0, 0), Vector3(-1, 0, 0), Vector3(0, 0, 1)]:
		B.box(self, Vector3(1.1, 1.8, 0.1), tc + n * 1.62 + Vector3(0, 11.0, 0), VM.window_glass, false, atan2(n.x, n.z))
	B.hip_roof(self, tc + Vector3(0, 13.0, 0), 3.8, 3.8, 3.0, VM.clay, 0.12)
	B.box(self, Vector3(0.14, 1.6, 0.14), tc + Vector3(0, 16.7, 0), B.flat(Color(0.9, 0.85, 0.6), 0.3, 0.7))
	B.box(self, Vector3(0.8, 0.14, 0.14), tc + Vector3(0, 17.1, 0), B.flat(Color(0.9, 0.85, 0.6), 0.3, 0.7))
	B.label(self, "Igreja de São Pedro", c + Vector3(0, h - 0.6, - d * 0.5 - 0.1), 60, Color(0.15, 0.3, 0.55), Color(1, 1, 1, 0.9), PI)
	village_points.church_bell = tc + Vector3(0, 11, 0)
	village_points.padre = c + Vector3(2.6, 0.1, - d * 0.5 - 2.6)
	_quest_giver("paes_padre", "Padre Tomé", c + Vector3(2.6, 1.0, - d * 0.5 - 2.3), Vector3(1.0, 1.8, 1.0))

	B.cyl(self, 2.2, 2.3, 0.45, pc + Vector3(0, 0.3, 0), VM.curb, 24)
	if Quality.hd and B.has_model("island_tree_01"):
		var tree: = B.model(self, "island_tree_01", pc + Vector3(0, 0.5, 0), 0.4, 1.0)
		var bb: = B.aabb_of(tree)
		if bb.size.y > 0.1:
			tree.scale = Vector3.ONE * clampf(9.0 / bb.size.y, 0.2, 5.0)
	else:
		Palm.spawn(self, pc + Vector3(0.4, 0.5, 0.2), 911)
	var sbc: = B.wall(self, Vector3(4.4, 1.5, 4.4), pc + Vector3(0, 0.75, 0))
	sbc.name = "planter_col"

	for k in 4:
		var a: = PI * 0.5 * k + PI * 0.25
		var bp: = pc + Vector3(cos(a) * 4.2, 0.1, sin(a) * 3.2)
		var face: = atan2(pc.x - bp.x, pc.z - bp.z)
		bench_spots.append(_bench(bp, face))
	for corner in [Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]:
		B.model(self, "planter_box_01", pc + Vector3(corner.x * (r.size.x * 0.5 - 0.8), 0.1, corner.y * (r.size.y * 0.5 - 0.7)), 0.0, 1.0)

	B.model(self, "CoffeeCart_01", pc + Vector3(-7.2, 0.1, 3.0), 2.4, 1.0)
	village_points.cart = pc + Vector3(-6.0, 0.1, 3.2)


## Authoring axes: +Z is the service front. World front faces the beach (-Z).
func kiosk_point(offset: Vector3) -> Vector3:
	return KIOSK_C + Vector3(-offset.x, offset.y, -offset.z)

func kiosk_local(point: Vector3) -> Vector3:
	var p := point - KIOSK_C
	return Vector3(-p.x,p.y,-p.z)

func kiosk_authored(point: Vector3) -> Vector3:
	return kiosk_point(point - KIOSK_C)

func kiosk_rect(rect: Rect2) -> Rect2:
	return Rect2(Vector2(2*KIOSK_C.x-rect.end.x,2*KIOSK_C.z-rect.end.y),rect.size)

func _quiosque() -> void :
	var first_node := get_child_count()
	var first_block := block_rects.size()
	var c: = KIOSK_C
	# v0.7.1: ninguém atravessa o quiosque — área bloqueada para os moradores (os bancos da frente ficam fora)
	block_rects.append(Rect2(c.x - 2.95, c.z - 3.05, 5.9, 5.35))
	var floor_mesh := B.platform(self, Vector3(5.6, 0.2, 5.6), c, M.deckwood, 0.45)
	floor_mesh.name = "KioskFloor"
	var y0: = 0.1
	B.hip_roof(self, c + Vector3(0, y0 + 2.8, 0), 6.6, 6.6, 1.8, M.darkwood, 0.22)
	Real.place(self, "g:kiosk_roof", c + Vector3(0, y0 + 2.84, 0), -1.0, 0.0, Color.WHITE, 0.0, false)
	var ch: = 1.1
	var wood: Material = M.darkwood
	_painted.append(B.box(self, Vector3(4.6, ch, 0.6), c + Vector3(0, y0 + ch * 0.5, 2.0), wood, true))
	_painted.append(B.box(self, Vector3(0.6, ch, 2.4), c + Vector3(-2.0, y0 + ch * 0.5, 0.95), wood, true))
	_painted.append(B.box(self, Vector3(0.6, ch, 2.4), c + Vector3(2.0, y0 + ch * 0.5, 0.95), wood, true))
	_kiosk_facade(c, y0)
	var rear_wall := StaticBody3D.new()
	rear_wall.name = "KioskRearWall"
	add_child(rear_wall)
	rear_wall.position = c + Vector3(0, y0 + 1.32, -2.4)
	var rear_shape := CollisionShape3D.new()
	var rear_box := BoxShape3D.new()
	rear_box.size = Vector3(4.65, 2.64, 0.16)
	rear_shape.shape = rear_box
	rear_wall.add_child(rear_shape)
	# Equipamentos funcionais ocupam a parede traseira; entradas laterais livres.
	# Altura real do tampo: base e acabamento; itens apoiados, sem sobreposição.
	var snack_y: = y0 + ch + 0.08
	Real.place(self, "carved_wooden_plate", c + Vector3(-1.45, snack_y, 1.85), 0.0, 0.0, Color(0.82, 0.68, 0.48), 0.8)
	_fruit_row(c + Vector3(-1.69, snack_y + 0.105, 1.85))
	# Placa abaixo da franja e à frente do beiral: texto inteiro visível.
	# Mantém espaço livre entre o balcão e a borda inferior da moldura.
	for sx in [-1.0, 1.0]:
		B.cyl(self, 0.018, 0.018, 0.32, c + Vector3(sx * 1.55, y0 + 2.70, 3.38), M.post, 8)
	B.box(self, Vector3(4.0, 0.64, 0.10), c + Vector3(0, y0 + 2.25, 3.40), M.darkwood)
	_sign_panels.append(B.box(self, Vector3(3.82, 0.5, 0.025), c + Vector3(0, y0 + 2.25, 3.465), wood_tint(Color(0.06, 0.29, 0.31))))
	var brand: Label3D = B.label(self, "MARÉ ALTA", c + Vector3(0, y0 + 2.33, 3.49), 76, Color(1.0, 0.94, 0.78), Color(0.025, 0.1, 0.11, 0.8))
	brand.outline_size = 4
	company_signs.append({"label": brand, "width": 3.45})
	var sign_action := Interactable.new()
	sign_action.name = "KioskSign"
	sign_action.position = c + Vector3(0, y0 + 2.25, 3.49)
	var sign_shape := CollisionShape3D.new()
	var sign_box := BoxShape3D.new()
	sign_box.size = Vector3(4.0, 0.64, 0.18)
	sign_shape.shape = sign_box
	sign_action.add_child(sign_shape)
	sign_action.prompt_fn = func(): return tr("Gestão no computador do balcão")
	sign_action.action_fn = func():
		Core.toast.emit("Use o computador dentro do quiosque para personalizar e abrir o negócio.","info")
	add_child(sign_action)
	var subtitle: Label3D = B.label(self, "QUIOSQUE • SABORES DA PRAIA", c + Vector3(0, y0 + 2.08, 3.49), 24, Color(0.94, 0.83, 0.6), Color(0, 0, 0, 0))
	subtitle.shaded = false
	_kiosk_board = Node3D.new()
	_kiosk_board.name = "KioskMenuBoard"
	add_child(_kiosk_board)
	_kiosk_menu_c = c
	_refresh_kiosk_board()
	B.model(self, "wooden_lantern_01", c + Vector3(0, y0 + 2.25, 0.2), 0.0, 1.1)
	# v0.7.1: o quiosque já começa com uma mesinha; "Mesas e guarda-sóis" traz mais duas com guarda-sol
	_kiosk_table(c + Vector3(-4.4, 0, 4.6), "", Color(0.95, 0.78, 0.35), false)
	_area("kiosk_tables", func():
		_kiosk_table(c + Vector3(4.4, 0, 4.6), "kiosk_tables", Color(0.12, 0.55, 0.58), true)
		_kiosk_table(c + Vector3(-4.6, 0, 8.6), "kiosk_tables", Color(1.0, 0.45, 0.35), true))
	_kiosk_details(c, y0)
	hut_details(c, 2.4, y0, 2.8, 1.8, 3.3, false)
	_area("drinks", func(): _kiosk_drinks(c, y0))
	_area("neon", func(): _kiosk_neon(c, y0))
	# Mantém o marco da expansão; a chapa integra a cozinha funcional interna.
	_area("grill", func(): pass)
	kiosk_counter = Interactable.new()
	var cs: = CollisionShape3D.new()
	var sh: = BoxShape3D.new()
	sh.size = Vector3(4.6, 1.5, 0.6)
	cs.shape = sh
	kiosk_counter.add_child(cs)
	kiosk_counter.position = c + Vector3(0, y0 + 0.9, 2.0)
	kiosk_counter.name = "KioskCounter"
	add_child(kiosk_counter)
	for k in 2:
		var p: = c + Vector3(-0.7 + k * 1.4, y0, 2.72)   # em cima do deck (antes na borda inclinada, 10 cm no ar)
		B.model(self, "bar_chair_round_01", p, PI, 1.0)
		# banqueta de bar: assento a 0,69 m; a raiz vai 0,22 m para a frente (para o balcão)
		kiosk_spots.insert(k, {"approach": Vector3(p.x, 0.1, p.z + 0.63), "pos": p + Vector3(0, 0.69 - SEAT_DROP, -0.22), "rot": PI, "busy": false, "need": "", "serve_pos": c + Vector3(-0.7 + k * 1.4, snack_y, 2.1), "serve_rot": 0.0, "staff_approach": c + Vector3(-0.7 + k * 1.4, .1, 1.05)})
	village_points.kiosk_work = c + Vector3(0, 0.1, 0.8)
	var l: = OmniLight3D.new()
	l.position = c + Vector3(0, 2.5, 0)
	l.omni_range = 6.5
	l.light_color = Color(1.0, 0.75, 0.45)
	add_child(l)
	lanterns.append([l, null, 0.95, false])
	# One frame for all furniture, lights, colliders and expansion roots.
	var built := get_children().slice(first_node)
	kiosk_root = Node3D.new()
	kiosk_root.name = "KioskBeachFrame"
	add_child(kiosk_root)
	for node in built: node.reparent(kiosk_root,false)
	kiosk_root.transform = Transform3D(Basis(Vector3.UP,PI),Vector3(2*c.x,0,2*c.z))
	for i in range(first_block,block_rects.size()): block_rects[i] = kiosk_rect(block_rects[i])
	for spot in kiosk_spots:
		for field in ["pos","approach","serve_pos","staff_approach"]:
			if spot.has(field): spot[field] = kiosk_authored(spot[field])
		spot.rot = wrapf(float(spot.rot)+PI,-PI,PI)
		spot.serve_rot = wrapf(float(spot.serve_rot)+PI,-PI,PI)
	village_points.kiosk_work = kiosk_point(Vector3(0,.1,.8))



## Fachada Blender: acabamentos separados para a pintura não cobrir madeira/latão.
func _kiosk_facade(c: Vector3, y0: float) -> void:
	var facade := Real.place(self, "g:kiosk_facade", c + Vector3(0, y0, 0), -1.0, 0.0, Color.WHITE, 0.0, false)
	if facade == null:
		push_error("KIOSK_FACADE_MISSING")
		return
	facade.name = "KioskFacade"
	for mesh in facade.find_children("*", "MeshInstance3D", true, false):
		var part := mesh as MeshInstance3D
		if part.name == "facade_paint":
			# One material per Blender mesh; preserve the native wood/brass elsewhere.
			part.material_override = part.get_active_material(0)
			_painted.append(part)
		if part.name == "glow_facade_warm":
			var lit := part.get_active_material(0).duplicate() as StandardMaterial3D
			lit.emission_enabled = true
			lit.emission = Color(1.0, 0.64, 0.28)
			lit.emission_energy_multiplier = 0.0
			part.material_override = lit
			lanterns.append([null, lit, 0.8, false])
	var task_light := OmniLight3D.new()
	task_light.name = "KioskWorkLight"
	task_light.position = c + Vector3(0.25, 2.32, -0.9)
	task_light.light_color = Color(1.0, 0.93, 0.82)
	task_light.light_energy = 0.65
	task_light.omni_range = 3.4
	task_light.omni_attenuation = 1.2
	task_light.shadow_enabled = false
	add_child(task_light)
	for x in [-2.68, 2.68]:
		var lamp := OmniLight3D.new()
		lamp.name = "KioskPendantLight"
		lamp.position = c + Vector3(x, y0 + 2.21, 3.0)
		lamp.light_color = Color(1.0, 0.73, 0.43)
		lamp.omni_range = 3.5
		lamp.omni_attenuation = 1.8
		add_child(lamp)
		lanterns.append([lamp, null, 0.65, false])
	for x in [-1.4,1.4]:
		var sign_light := OmniLight3D.new()
		sign_light.name = "KioskSignWarmLight"
		sign_light.position = c + Vector3(x,2.55,3.85)
		sign_light.light_color = Color(1,.78,.48)
		sign_light.omni_range = 2.1
		sign_light.shadow_enabled = false
		add_child(sign_light)
		lanterns.append([sign_light,null,.42,false])
	for x in [-2.43, 2.43]:
		Real.place(self, "g:hanging_planter", c + Vector3(x, 1.92, -0.4), 0.98)


## Mesa com duas cadeiras (dois lugares de cliente) e, opcionalmente, guarda-sol.
func _kiosk_table(tp: Vector3, need: String, umb: Color, umbrella: bool) -> void :
	var first_node := get_child_count()
	var first_spot := kiosk_spots.size()
	var block_index := block_rects.size()
	B.model(self, "outdoor_table_chair_set_01", tp, 0.0, 1.0)
	if umbrella:
		_umbrella(tp, 1.45, umb, false)
	# tampo da mesa dobrável a 0,73 m, centrado em (-0,08; 0,07): petiscos e cardápio apoiados nele (antes flutuavam 5 cm)
	var top: = tp + Vector3(-0.08, 0.732, 0.07)
	# Pratos e bebidas aparecem só quando o pedido deste lugar é entregue.
	# cardapinho em pé na mesa
	var menu: = B.box(self, Vector3(0.16, 0.22, 0.02), top + Vector3(0, 0.105, 0), B.flat(Color(1.0, 0.45, 0.35), 0.8))
	_table_menus.append(menu)
	menu.rotation.x = -0.2
	# as duas cadeiras dobráveis do conjunto ficam na frente e atrás da mesa (eixo z), levemente giradas; assento a 0,384 m
	for sd in [[Vector3(-0.017, 0.384, 0.447), Vector3(-0.343, 0, -0.94)], [Vector3(-0.089, 0.384, -0.371), Vector3(-0.148, 0, 0.989)]]:
		var seat_c: Vector3 = sd[0]
		var fwd: Vector3 = sd[1]
		var root: = tp + Vector3(seat_c.x, seat_c.y - SEAT_DROP, seat_c.z) + fwd * 0.27
		var approach: = tp + Vector3(seat_c.x, 0.1, seat_c.z) - fwd * 0.85
		kiosk_spots.append({"pos": root, "approach": approach, "rot": atan2(fwd.x, fwd.z), "busy": false, "need": need, "anim": "Sitting_Idle_Loop", "table": true, "covered": umbrella, "serve_pos": top - fwd * 0.17, "serve_rot": atan2(fwd.x, fwd.z)})
	# mesa + cadeiras bloqueadas: pedestres contornam o conjunto todo (quem vai sentar entra)
	_block(tp, 1.0, 1.9, 0.12)
	var nodes: Array = []
	for node in get_children().slice(first_node):
		if node is Node3D: nodes.append({"node": node, "position": node.position})
	var seats: Array = []
	for spot in kiosk_spots.slice(first_spot): seats.append({"spot": spot, "base": spot.duplicate()})
	_table_looks.append({"nodes": nodes, "seats": seats, "block": block_index, "rect": block_rects[block_index], "side": -1 if tp.x < KIOSK_C.x else 1})

## Quadro-negro do quiosque: mostra só os pratos liberados.
func _refresh_kiosk_board() -> void :
	if _kiosk_board == null:
		return
	for ch in _kiosk_board.get_children():
		ch.queue_free()
	var c: = _kiosk_menu_c
	var before: = get_child_count()
	# Outside the railing/bunting plane, with its full writing area above the rail.
	_chalkboard(c + Vector3(3.05, 0.1 + 1.8, 0.9), PI * 0.5, "HOJE", _menu_lines(Core.kiosk_menu()))
	var board = get_child(before)
	for side in [-1.0, 1.0]:
		B.box(board, Vector3(.07,.07,.28), Vector3(side*.40,-.65,-.16), M.darkwood)
	for k in get_children().slice(before):
		k.reparent(_kiosk_board, false)

func on_areas_changed() -> void :
	_refresh_kiosk_board()

## Letreiro neon (expansão "neon"): tubos coloridos que brilham, mais cordões de luz.
func _kiosk_neon(c: Vector3, y0: float) -> void :
	_string_lights(c + Vector3(-2.3, y0 + 2.45, 2.3), c + Vector3(2.3, y0 + 2.45, 2.3), 8)
	_string_lights(c + Vector3(-2.3, y0 + 2.45, -2.3), c + Vector3(-2.3, y0 + 2.45, 2.3), 6)
	_string_lights(c + Vector3(2.3, y0 + 2.45, -2.3), c + Vector3(2.3, y0 + 2.45, 2.3), 6)
	# A expansão ilumina a placa principal, sem duplicar o nome no telhado.
	var glow := P.glow(Color(0.16, 0.85, 0.78), 3.0)
	# Base do modelo a 1,952 m; Real.place apoia a AABB antes desta elevação.
	var trim := Real.place_glow(self, "g:kiosk_neon_trim", c + Vector3(0, y0 + 1.952, 0), -1.0, 0.0, glow)
	if trim: trim.name = "KioskNeonTrim"
	var nl := OmniLight3D.new()
	nl.position = c + Vector3(0, y0 + 2.5, 3.65)
	nl.light_color = Color(0.32, 0.85, 0.78)
	nl.omni_range = 4.0
	nl.light_energy = 0.0
	add_child(nl)
	lanterns.append([nl, glow, 0.4, false])


## Chapa de petiscos (expansão "grill"): fogão e panela; pratos prontos vêm da entrega.
func _kiosk_grill(c: Vector3, y0: float) -> void :
	B.model(self, "electric_stove", c + Vector3(1.3, y0, -1.3), 0.0, 0.9)
	# frigideira real (Poly Haven) com três coxinhas em pé dentro (modelo do Blender), sem encostar umas nas outras
	var pan: = Real.place(self, "brass_pan_01", c + Vector3(1.1, y0 + 0.86, -1.2), 0.0, 0.4, Color(0.55, 0.5, 0.48), 0.4)
	if pan == null:
		pan = B.cyl(self, 0.18, 0.15, 0.06, c + Vector3(1.1, y0 + 0.86, -1.2), B.flat(Color(0.15, 0.15, 0.17), 0.4), 14)
	pan.name = "Pan"
	for k in 3:
		var a: = TAU * k / 3.0
		Real.place(self, "g:coxinha", c + Vector3(1.1 + cos(a) * 0.065, y0 + 0.875, -1.2 + sin(a) * 0.065), -1.0, 0.5 + k, Color.WHITE, 0.0, true)
	# Superfície de entrega livre: nenhum prato pronto permanente.
	var smoke: = GPUParticles3D.new()
	var pm: = ParticleProcessMaterial.new()
	pm.direction = Vector3.UP
	pm.spread = 12.0
	pm.initial_velocity_min = 0.3
	pm.initial_velocity_max = 0.6
	pm.gravity = Vector3(0, 0.15, 0)
	pm.scale_min = 0.4
	pm.scale_max = 1.0
	pm.color = Color(1, 1, 1, 0.35)
	smoke.process_material = pm
	var qm: = QuadMesh.new()
	qm.size = Vector2(0.55, 0.55)
	var sm: = StandardMaterial3D.new()
	sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	sm.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	sm.vertex_color_use_as_albedo = true
	sm.particles_anim_h_frames = 1
	var puff: Texture2D = load("res://assets/tex/smoke_puff.png") if ResourceLoader.exists("res://assets/tex/smoke_puff.png") else null
	if puff:
		sm.albedo_texture = puff
	sm.albedo_color = Color(1, 1, 1, 0.55)
	qm.material = sm
	var fade: = Gradient.new()
	fade.set_color(0, Color(1, 1, 1, 0.0))
	fade.set_color(1, Color(1, 1, 1, 0.0))
	fade.add_point(0.2, Color(1, 1, 1, 0.6))
	var ft: = GradientTexture1D.new()
	ft.gradient = fade
	pm.color_ramp = ft
	pm.scale_min = 0.5
	pm.scale_max = 1.3
	pm.angle_min = -180.0
	pm.angle_max = 180.0
	smoke.draw_pass_1 = qm
	smoke.amount = 10
	smoke.lifetime = 2.0
	smoke.position = c + Vector3(1.1, y0 + 0.95, -1.2)
	add_child(smoke)

func _barraca() -> void :
	var c: = Vector3(62, 0, -20)
	var stripes: = Image.create(64, 8, false, Image.FORMAT_RGB8)
	for x in 64:
		for y in 8:
			stripes.set_pixel(x, y, Color(0.95, 0.85, 0.2) if (x / 8) % 2 == 0 else Color(0.1, 0.5, 0.75))
	var cm: = StandardMaterial3D.new()
	cm.albedo_texture = ImageTexture.create_from_image(stripes)
	cm.cull_mode = BaseMaterial3D.CULL_DISABLED
	cm.roughness = 0.9
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.cyl(self, 0.05, 0.05, 2.6, c + Vector3(sx * 2.8, 1.3, sz * 2.0), M.oak, 8)
	var roof: = B.box(self, Vector3(6.2, 0.04, 4.6), c + Vector3(0, 2.65, 0), cm)
	roof.rotation.x = 0.06
	B.box(self, Vector3(2.4, 0.9, 0.7), c + Vector3(-1.6, 0.45, -1.4), M.bamboo, true)
	B.label(self, "Barraca da Dona Rita", c + Vector3(0, 2.3, 2.1), 56, Color(0.1, 0.35, 0.6), Color(1, 1, 1, 0.9))
	for k in 3:
		var tp: = c + Vector3(-2.0 + k * 2.2, 0, 3.6)
		B.model(self, "outdoor_table_chair_set_01", tp, k * 0.7, 1.0)
		_umbrella(tp, 1.5, Color(0.95, 0.82, 0.28) if k != 1 else Color(0.16, 0.48, 0.7), k == 2)
		_table_bites(tp + Vector3(0, 0.75, 0))
	B.model(self, "plastic_crate_01", c + Vector3(1.8, 0, -1.4), 0.3, 1.0)
	B.model(self, "plastic_monobloc_chair_01", c + Vector3(2.4, 0, -0.4), 2.5, 1.0)
	village_points.barraca = c + Vector3(-1.6, 0, -0.6)
	quest_board = _quest_giver("cocos_rita", "Dona Rita", c + Vector3(-1.6, 1.0, 0.4), Vector3(1.4, 1.8, 1.2))


## Doador de missão da vila: caixa de interação perto do morador. Aceita a encomenda e depois entrega do estoque.
func _quest_giver(qid: String, who: String, pos: Vector3, size: Vector3) -> Interactable:
	var qb: = Interactable.new()
	qb.name = "Quest_" + qid
	var cs: = CollisionShape3D.new()
	var sh: = BoxShape3D.new()
	sh.size = size
	cs.shape = sh
	qb.add_child(cs)
	qb.position = pos
	qb.prompt_fn = func() -> String:
		var q: Dictionary = Economy.QUESTS[qid]
		var st: = str(Core.quests.get(qid, ""))
		if st == "done":
			return ""
		if not Core.quest_available(qid):
			return tr("%s: sem encomendas ainda (compre %s)") % [tr(who), tr(str(Economy.EXPANSIONS[q.req].name))]
		var item: = tr(str(Economy.SUPPLIES[q.need].name))
		if st == "":
			return tr("%s: aceitar \"%s\" (%d × %s)") % [tr(who), tr(str(q.title)), int(q.qty), item]
		return tr("%s: entregar %d × %s (você tem %d)") % [tr(who), int(q.qty), item, int(Core.stock.get(q.need, 0))]
	qb.action_fn = func() -> void :
		if str(Core.quests.get(qid, "")) == "":
			Core.accept_quest(qid)
		else:
			Core.complete_quest(qid)
	add_child(qb)
	return qb

## Cocos caídos junto às palmeiras da praia: rendem cocos grátis uma vez por dia.
func _coco_piles(spots: Array) -> void :
	for i in spots.size():
		var base: Vector3 = spots[i]
		var pile: = Node3D.new()
		pile.position = base
		add_child(pile)
		D.coconut_pile(pile, Vector3.ZERO, 5)
		var ia: = Interactable.new()
		ia.name = "CocoPile%d" % i
		var cc: = CollisionShape3D.new()
		var bs: = BoxShape3D.new()
		bs.size = Vector3(1.1, 0.9, 1.1)
		cc.shape = bs
		ia.add_child(cc)
		ia.position = Vector3(0, 0.45, 0)
		pile.add_child(ia)
		ia.prompt_fn = func() -> String:
			return tr("Juntar cocos caídos (+%d cocos)") % Economy.COCO_PILE_YIELD
		ia.action_fn = func() -> void :
			Core.stock["coco"] = int(Core.stock.get("coco", 0)) + Economy.COCO_PILE_YIELD
			Core.stock_changed.emit()
			Core.toast.emit(tr("Você juntou %d cocos caídos.") % Economy.COCO_PILE_YIELD, "good")
			get_tree().call_group("audio", "sfx", "click", -6.0)
			pile.visible = false
			ia.collision_layer = 0
			coco_piles_taken.append(pile)
		coco_piles.append(pile)

func reset_coco_piles() -> void :
	for pile in coco_piles:
		pile.visible = true
		for ch in pile.get_children():
			if ch is Interactable:
				ch.collision_layer = 2
	coco_piles_taken.clear()

func _umbrella_hd(p: Vector3, r: float) -> void :
	_umbrella(p, r)


const BIKE_COLS: = {"red": Color(0.8, 0.15, 0.15), "blue": Color(0.1, 0.4, 0.75), "yellow": Color(0.95, 0.75, 0.1), "green": Color(0.15, 0.55, 0.3), "white": Color(0.9, 0.9, 0.9)}

func _bike(p: Vector3, rot: float, col: Color) -> void :
	var n: = Node3D.new()
	n.position = p
	n.rotation = Vector3(0, rot, 0.18)
	add_child(n)
	# bicicleta modelada no Blender (quadro tubular, raios, cestinha de vime), na cor mais próxima
	var bk: = "white"
	var best: = 99.0
	for kk in BIKE_COLS:
		var dd: = Vector3(col.r - BIKE_COLS[kk].r, col.g - BIKE_COLS[kk].g, col.b - BIKE_COLS[kk].b).length()
		if dd < best:
			best = dd
			bk = kk
	if Real.place(n, "g:bike_" + bk, Vector3.ZERO, -1.0, 0.0, Color.WHITE, 0.0, false) != null:
		return
	var tire: = B.flat(Color(0.08, 0.08, 0.08), 0.7)
	var frame: = B.flat(col, 0.35, 0.6)
	for zz in [-0.52, 0.52]:
		var t: = MeshInstance3D.new()
		var tm: = TorusMesh.new()
		tm.inner_radius = 0.29
		tm.outer_radius = 0.34
		tm.rings = 24
		tm.ring_segments = 8
		t.mesh = tm
		t.material_override = tire
		t.position = Vector3(0, 0.34, zz)
		t.rotation.z = PI * 0.5
		n.add_child(t)
	var bars: = [[Vector3(0, 0.34, -0.52), Vector3(0, 0.75, 0.3)], [Vector3(0, 0.34, 0.52), Vector3(0, 0.75, 0.3)], 
		[Vector3(0, 0.34, -0.52), Vector3(0, 0.8, -0.2)], [Vector3(0, 0.8, -0.2), Vector3(0, 0.75, 0.3)], 
		[Vector3(0, 0.75, 0.3), Vector3(0, 1.0, 0.42)], [Vector3(0, 0.8, -0.2), Vector3(0, 0.92, -0.28)]]
	# v0.7.3: quadro montado em coordenadas locais (antes as barras iam parar longe e só sobravam as rodas)
	for b in bars:
		B._beam(n, b[0], b[1], 0.022, frame)
	var metal: = B.flat(Color(0.75, 0.76, 0.78), 0.3, 0.6)
	for zz in [-0.52, 0.52]:
		var hub: = B.cyl(n, 0.035, 0.035, 0.1, Vector3(0, 0.34, zz), metal, 16)
		hub.rotation.z = PI * 0.5
		for k in 8:
			var a: = TAU * k / 8.0
			B._beam(n, Vector3(0, 0.34, zz), Vector3(0, 0.34 + sin(a) * 0.29, zz + cos(a) * 0.29), 0.004, metal)
	# guidão, selim, pedivela e pedais, descanso
	B._beam(n, Vector3(-0.26, 1.0, 0.42), Vector3(0.26, 1.0, 0.42), 0.016, tire)
	for sx in [-0.27, 0.27]:
		B._beam(n, Vector3(sx, 1.0, 0.42), Vector3(sx * 1.15, 1.0, 0.36), 0.024, B.flat(Color(0.9, 0.3, 0.25), 0.8))
	B.sphere(n, 0.1, Vector3(0, 0.96, -0.28), tire, Vector3(0.8, 0.35, 1.4))
	var crank: = B.cyl(n, 0.09, 0.09, 0.02, Vector3(0.04, 0.36, 0.0), metal, 24)
	crank.rotation.z = PI * 0.5
	B._beam(n, Vector3(0.06, 0.36, 0.0), Vector3(0.1, 0.22, 0.08), 0.012, metal)
	B._beam(n, Vector3(-0.06, 0.36, 0.0), Vector3(-0.1, 0.5, -0.08), 0.012, metal)
	B.box(n, Vector3(0.1, 0.02, 0.05), Vector3(0.14, 0.22, 0.08), tire)
	B.box(n, Vector3(0.1, 0.02, 0.05), Vector3(-0.14, 0.5, -0.08), tire)
	B._beam(n, Vector3(0, 0.34, -0.1), Vector3(0, 0.36, 0.0), 0.012, metal)
	B._beam(n, Vector3(-0.02, 0.33, -0.15), Vector3(-0.2, 0.0, -0.2), 0.012, metal)
	# cestinha na frente
	B.cyl(n, 0.16, 0.13, 0.18, Vector3(0, 0.95, 0.62), B.flat(Color(0.82, 0.62, 0.36), 0.9), 20)

func _jangada2(p: Vector3, rot: float) -> void :
	var j: = Node3D.new()
	j.position = p
	j.rotation.y = rot
	add_child(j)
	# jangada de troncos com vela enfunada: modelo do Blender (tools/gen_code_props.py)
	if Real.place(j, "g:jangada", Vector3.ZERO, -1.0, 0.0, Color.WHITE, 0.0, false) != null:
		B.wall(self, Vector3(2.0, 2.0, 6.5), p + Vector3(0, 1.4, 0), rot)
		return
	for k in 6:
		var log_: = B.cyl(j, 0.12, 0.12, 6.0, Vector3(-0.6 + k * 0.24, 0.12, 0), M.post, 8)
		log_.rotation.x = PI * 0.5
	B.cyl(j, 0.06, 0.07, 5.5, Vector3(0, 2.8, 1.0), M.oak, 8)
	var sail: = MeshInstance3D.new()
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for v in [Vector3(0, 0.6, 1.0), Vector3(0, 5.4, 1.0), Vector3(0, 0.7, -2.4)]:
		st.set_normal(Vector3.RIGHT)
		st.set_uv(Vector2(v.z, v.y) * 0.3)
		st.add_vertex(v)
	sail.mesh = st.commit()
	var sm: StandardMaterial3D = B.mat("rough_linen", 1.0, Color(1, 0.98, 0.94), 0.95).duplicate()
	sm.cull_mode = BaseMaterial3D.CULL_DISABLED
	sail.material_override = sm
	j.add_child(sail)
	B.wall(self, Vector3(2.0, 2.0, 6.5), p + Vector3(0, 1.4, 0), rot)

func _fishing_boat(p: Vector3, rot: float, paint: Color, solid: = true) -> Node3D:
	var j: = Node3D.new()
	j.name = "FishingBoat"
	j.add_to_group("fishing_boats")
	j.position = p
	j.rotation.y = rot
	add_child(j)
	# casco real (Kenney Pirate Kit, CC0, suavizado no Blender); pintado com a cor do barco
	var hull: = Real.place(j, "k:boat-row-large", Vector3(0, 0.0, 0), 0.0, 0.0, paint.lerp(Color.WHITE, 0.12), 4.6)
	if hull != null:
		hull.rotation.y = 0.0
	B.model(j, "wooden_crate_01", Vector3(-0.15, 0.4, 1.15), 0.2, 0.55)   # fundo do casco a 0,40 m
	B.model(j, "wooden_bucket_01", Vector3(0.28, 0.4, 0.55), 0.5, 0.45)
	if Real.place(j, "g:boat_mast", Vector3(0.05, 0.25, -0.15), -1.0, 0.0, Color.WHITE, 0.0, false) != null:
		if solid:
			B.wall(self, Vector3(1.7, 0.7, 4.6), p + Vector3(0, 0.35, 0.1), rot)
		return j
	B.cyl(j, 0.035, 0.04, 2.4, Vector3(0.05, 1.45, -0.15), M.oak, 6)
	var sail: = MeshInstance3D.new()
	var sst: = SurfaceTool.new()
	sst.begin(Mesh.PRIMITIVE_TRIANGLES)
	for v in [Vector3(0.05, 0.7, -0.15), Vector3(0.05, 2.55, -0.15), Vector3(0.05, 0.85, 1.35)]:
		sst.set_normal(Vector3.RIGHT)
		sst.set_uv(Vector2(v.z, v.y) * 0.4)
		sst.add_vertex(v)
	sail.mesh = sst.commit()
	var smat: StandardMaterial3D = B.mat("rough_linen", 1.2, Color(0.96, 0.94, 0.88), 0.9).duplicate() as StandardMaterial3D
	smat.cull_mode = BaseMaterial3D.CULL_DISABLED
	sail.material_override = smat
	j.add_child(sail)
	if solid:
		B.wall(self, Vector3(1.7, 0.7, 4.6), p + Vector3(0, 0.35, 0.1), rot)
	return j

func _boat_mesh() -> ArrayMesh:
	if VM.has("boat"):
		return VM.boat
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var secs: = [
		[-2.55, 0.06, 0.42, 0.58], 
		[-1.85, 0.38, 0.06, 0.5], 
		[-0.7, 0.68, 0.0, 0.46], 
		[0.55, 0.74, 0.0, 0.44], 
		[1.7, 0.58, 0.02, 0.48], 
		[2.4, 0.32, 0.1, 0.52], 
	]
	for i in secs.size() - 1:
		var a: Array = secs[i]
		var b_: Array = secs[i + 1]
		var pts: = []
		for s in [a, b_]:
			pts.append(Vector3( - s[1], s[3], s[0]))
			pts.append(Vector3(s[1], s[3], s[0]))
			pts.append(Vector3(0, s[2], s[0]))
			pts.append(Vector3( - s[1] * 0.62, s[2] + 0.16, s[0]))
			pts.append(Vector3(s[1] * 0.62, s[2] + 0.16, s[0]))

		_boat_quad(st, pts[0], pts[5], pts[7], pts[2])
		_boat_quad(st, pts[1], pts[2], pts[7], pts[6])
		_boat_quad(st, pts[3], pts[8], pts[9], pts[4])
		_boat_quad(st, pts[0], pts[3], pts[8], pts[5])
		_boat_quad(st, pts[1], pts[6], pts[9], pts[4])
	st.generate_normals()
	var mesh: = st.commit()
	VM.boat = mesh
	return mesh

func _boat_quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3) -> void :
	var n: Vector3 = (b - a).cross(d - a)
	if n.length_squared() < 1e-05:
		n = Vector3.UP
	else:
		n = n.normalized()
	for v in [a, b, c, a, c, d]:
		st.set_normal(n)
		st.set_uv(Vector2(v.x * 0.8 + 0.5, v.z * 0.25 + 0.5))
		st.add_vertex(v)

func _net(a: Vector3, b: Vector3) -> void :
	var wood: = wood_tint(Color(0.35, 0.22, 0.12))
	var ay: = _height(a.x, a.z)
	var by: = _height(b.x, b.z)
	B.cyl(self, 0.04, 0.05, 1.5, Vector3(a.x, ay + 0.75, a.z), wood, 6)
	B.cyl(self, 0.04, 0.05, 1.5, Vector3(b.x, by + 0.75, b.z), wood, 6)
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n: = 8
	var prev: = []
	for k in n + 1:
		var t: = float(k) / float(n)
		var p: = a.lerp(b, t)
		p.y = lerpf(ay, by, t) + 1.35 - sin(t * PI) * 0.55
		var side: = (b - a).cross(Vector3.UP).normalized()
		if side.length_squared() < 0.01:
			side = Vector3.RIGHT
		var l: = p
		var r: = p + Vector3(0, -0.7, 0) + side * 0.02
		if k > 0:
			for v in [[prev[0], Vector2(t - 1.0 / n, 0)], [l, Vector2(t, 0)], [r, Vector2(t, 1)], [prev[0], Vector2(t - 1.0 / n, 0)], [r, Vector2(t, 1)], [prev[1], Vector2(t - 1.0 / n, 1)]]:
				st.set_normal(Vector3.UP)
				st.set_uv(v[1])
				st.add_vertex(v[0])
		prev = [l, r]
	var mi: = MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = _net_mat()
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)

func _net_mat() -> Material:
	if VM.has("net"):
		return VM.net
	var img: = Image.create(128, 64, false, Image.FORMAT_RGBA8)
	for y in 64:
		for x in 128:
			var on: = (x % 8) < 2 or (y % 8) < 2
			img.set_pixel(x, y, Color(0.78, 0.7, 0.5, 0.9) if on else Color(0, 0, 0, 0))
	var m: = StandardMaterial3D.new()
	m.albedo_texture = ImageTexture.create_from_image(img)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	m.alpha_scissor_threshold = 0.4
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.roughness = 0.9
	VM.net = m
	return m

func _village_props() -> void :
	var bike_spots: = [[Vector3(57.6, 0.15, 25.6), 0.0, Color(0.8, 0.15, 0.15)], [Vector3(66.2, 0.15, 25.6), 0.1, Color(0.1, 0.4, 0.75)], 
		[Vector3(48.4, 0.15, 34.4), PI, Color(0.95, 0.75, 0.1)], [Vector3(84.2, 0.15, 25.7), -0.1, Color(0.15, 0.55, 0.3)], [Vector3(70.5, 0.25, 36.0), PI * 0.5, Color(0.9, 0.9, 0.9)]]
	for b in bike_spots:
		_bike(b[0], b[1] + PI * 0.5, b[2])
	for k in 3:
		var x: = 52.0 + k * 13.0
		_jangada2(Vector3(x, _height(x, -29.5) - 0.12, -29.5), 0.3 - k * 0.25)
	var boats: = [[Vector3(58.5, 0, -27.2), 0.35, Color(0.2, 0.45, 0.62)], [Vector3(82.0, 0, -29.5), -0.4, Color(0.72, 0.22, 0.16)], [Vector3(88.5, 0, -27.4), 0.15, Color(0.85, 0.72, 0.28)]]
	for b in boats:
		var bp: Vector3 = b[0]
		bp.y = _height(bp.x, bp.z) - 0.05
		_fishing_boat(bp, b[1], b[2])
	_net(Vector3(63.2, 0, -25.4), Vector3(67.4, 0, -24.6))
	_net(Vector3(80.0, 0, -25.2), Vector3(84.2, 0, -24.2))
	for cr in [Vector3(60.4, 0, -25.6), Vector3(70.2, 0, -25.2), Vector3(85.5, 0, -25.0)]:
		B.model(self, "wooden_crate_01", Vector3(cr.x, _height(cr.x, cr.z), cr.z), cr.x * 0.1, 0.85)
		B.model(self, "wicker_basket_02", Vector3(cr.x + 0.7, _height(cr.x, cr.z), cr.z + 0.3), 0.4, 0.9)
	for k in 6:
		var x2: = 50.0 + k * 9.0
		B.model(self, ["potted_plant_01", "potted_plant_04", "planter_pot_clay"][k % 3], Vector3(x2 + 2.8, 0.15, 26.4), 0.0, 1.0)
	_fence(Vector3(50.2, 0, 16.6), Vector3(66.5, 0, 16.6))
	_fence(Vector3(76.2, 0, 16.6), Vector3(99.2, 0, 16.6))
	_fence(Vector3(41.2, 0, 43.2), Vector3(63.5, 0, 43.2))
	_fence(Vector3(86.5, 0, 43.2), Vector3(100.5, 0, 43.2))
	if Quality.hd:
		for k in 18:
			var sp: = Vector2(40 + k * 3.4, 15.0 if k % 2 == 0 else 45.5)
			if sp.y > 42.0 and sp.x > 64.0 and sp.x < 86.0:
				continue
			Real.place(self, ["q:Bush_Common", "q:Bush_Common_Flowers", "q:Plant_1_Big", "q:Fern_1"][k % 4], Vector3(sp.x, 0, sp.y), 1.0, k * 1.3)

func _village_palms() -> void :

	var rng: = RandomNumberGenerator.new()
	rng.seed = 4242
	var excl: = [Rect2(34, -17.5, 9, 9), Rect2(36.2, -17, 3.6, 44), Rect2(55, -25, 14, 11), Rect2(40, 15.5, 62, 42), Rect2(0, 24.5, 104, 11)]
	var n: = 46 if Quality.hd else 22
	var placed: = 0
	var tries: = 0
	while placed < n and tries < 600:
		tries += 1
		var p: = Vector2(rng.randf_range(44, 101), rng.randf_range(-23, 13))
		if tries % 4 == 0:
			p = Vector2(rng.randf_range(42, 101), rng.randf_range(43, 54))
		var bad: = false
		for r in excl:
			if r.has_point(p):
				bad = true
				break
		if bad:
			continue
		Palm.spawn(self, Vector3(p.x, _height(p.x, p.y) - 0.05, p.y), 3000 + placed)
		if p.y < 12.0 and p.x < 90.0 and coco_spots.size() < 4:
			coco_spots.append(Vector3(p.x + 1.15, _height(p.x + 1.15, p.y + 0.6), p.y + 0.6))
		placed += 1

	Palm.spawn(self, Vector3(33.2, _height(33.2, -9.5) - 0.05, -9.5), 4242)
	_coco_piles(coco_spots)

func _street_lamps() -> void :
	var spots: = []
	var x: = 8.0
	while x < 98.0:
		spots.append([Vector3(x, 0.15, STREET_Z - 3.5), 0.0])
		spots.append([Vector3(x + 6.0, 0.15, STREET_Z + 3.5), PI])
		x += 12.0
	var pc: = PRACA.get_center()
	for cc in [Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]:
		spots.append([Vector3(pc.x + cc.x * 7.8, 0.1, pc.y + cc.y * 3.6), 0.0])
	spots.append([Vector3(38.9, 0.05, 0.0), 0.0])
	spots.append([Vector3(38.9, 0.05, 14.0), 0.0])
	for s in spots:
		var p: Vector3 = s[0]
		var top: = 4.2
		if B.has_model("street_lamp_01"):
			var m: = B.model(self, "street_lamp_01", p, s[1], 1.0)
			var bb: = B.aabb_of(m)
			if bb.size.y > 0.5:
				top = bb.end.y - 0.35
		else:
			B.cyl(self, 0.06, 0.09, 4.2, p + Vector3(0, 2.1, 0), B.flat(Color(0.12, 0.14, 0.13), 0.5, 0.6), 10)
		var gm: = _lamp_glow_mat()
		_lamp_head(p + Vector3(0, top, 0), gm)
		var l: = OmniLight3D.new()
		l.position = p + Vector3(0, top - 0.15, 0)
		l.omni_range = 11.0
		l.light_color = Color(1.0, 0.74, 0.42)
		l.light_energy = 0.0
		l.shadow_enabled = false
		add_child(l)
		lanterns.append([l, gm, 2.6, false])


func _village_routes() -> void :
	var zn: = STREET_Z - 2.9
	var zs: = STREET_Z + 2.9
	village_paths = [
		[Vector3(4, 0.15, zn), Vector3(37, 0.15, zn), Vector3(70, 0.15, zn), Vector3(97, 0.15, zn)], 
		[Vector3(97, 0.15, zs), Vector3(64, 0.15, zs), Vector3(30, 0.15, zs), Vector3(4, 0.15, zs)], 
		[Vector3(67.5, 0.2, 35.6), Vector3(82.5, 0.2, 35.6), Vector3(82.5, 0.2, 42.6), Vector3(67.5, 0.2, 42.6), Vector3(67.5, 0.2, 35.6)], 
		[Vector3(38, 0.05, zn), Vector3(38, 0.05, 5.0), Vector3(38, 0.05, -7.0), Vector3(43.8, 0, -8.2), Vector3(44.2, 0, -17.0), Vector3(48, 0, -22), Vector3(90, 0, -24)], 
		[Vector3(30, 0.15, zn), Vector3(55, 0.15, zn), Vector3(55, 0.15, zs), Vector3(85, 0.15, zs)], 
	]
	village_points.kiosk_approach = [Vector3(38, 0.15, zn), Vector3(45.5, 0.05, 5.0), Vector3(45.5, 0.05, -25.0)]
	village_points.home_route = [village_points.home_door_out, Vector3(HOME_C.x + 1.7, 0.15, zn)]

func set_night(t: float) -> void :
	super.set_night(t)
	_night = t
	if _lighthouse:
		var beam: = _lighthouse.get_node_or_null("Beam")
		if beam:
			beam.visible = t > 0.3
			if beam is GeometryInstance3D and (beam as GeometryInstance3D).material_override is ShaderMaterial:
				((beam as GeometryInstance3D).material_override as ShaderMaterial).set_shader_parameter("night", clampf((t - 0.3) / 0.5, 0.0, 1.0))
		for ch in _lighthouse.get_children():
			if ch is SpotLight3D:
				ch.light_energy = 6.0 * t
	if VM.has("glass"):
		# janelas: grupo A (também igreja, quiosque, lojas) aceso a noite toda; B das 18h30 às 21h30 (dorme cedo);
		# C das 19h30 à 0h30 e de novo das 5h às 6h30 (acorda cedo). Apagada = reflexo fraco.
		var h: = Core.minutes / 60.0
		var on: = {"glass": true, "glass_b": h >= 18.5 and h < 21.5, "glass_c": (h >= 19.5 or h < 0.5) or (h >= 5.0 and h < 6.5)}
		for key in on:
			if not VM.has(key):
				continue
			var glass: StandardMaterial3D = VM[key]
			var k: = t if on[key] else t * 0.06
			glass.emission_energy_multiplier = 7.0 * k
			glass.albedo_color = Color(0.62, 0.78, 0.88, 0.7).lerp(Color(1.0, 0.7, 0.35, 0.95), k)


# ------------------------------------------------------------------ v0.7.1: quiosque cheio de detalhes
func _kiosk_details(c: Vector3, y0: float) -> void :
	for pair in [[Vector3(3.1, 0, -3.1), Vector3(3.1, 0, 3.1)], [Vector3(-3.1, 0, -3.1), Vector3(-3.1, 0, 3.1)]]:
		D.bunting(self, c + pair[0] + Vector3(0, y0 + 2.3, 0), c + pair[1] + Vector3(0, y0 + 2.3, 0), 0.18, 0.28)
	# frutas penduradas nas vigas
	D.bananas(self, c + Vector3(-1.7, y0 + 2.35, 1.7))
	D.bananas(self, c + Vector3(1.75, y0 + 2.35, -1.6))
	for k in 3:
		var cc: = c + Vector3(-0.6 + k * 0.6, y0 + 2.45, -2.25)
		B.cyl(self, 0.014, 0.014, 0.62, cc + Vector3(0, 0.05, 0), D.m(Color(0.45, 0.3, 0.16)), 8)
		Real.place(self, "k:coconut", cc + Vector3(0, -0.55, 0), 0.26, k * 1.3)
	# balcão
	var top: = c + Vector3(0, y0 + 1.18, 2.0)
	D.tip_jar(self, top + Vector3(1.6, 0, 0.15))
	D.straw_cup(self, c + Vector3(-2.0, y0 + 1.1, 0.95))
	D.cup_stack(self, top + Vector3(-1.95, 0, 0.0), Color(1.0, 0.9, 0.3))
	D.cup_stack(self, top + Vector3(-1.75, 0, 0.12), Color(0.3, 0.8, 1.0))

	D.pineapple(self, top + Vector3(1.95, 0, -0.1))

	_open_sign = D.open_sign(self, c + Vector3(1.65, y0 + 2.3, 2.5), 0.0)
	# Lixeira no lado interno do balcão; passagens laterais desobstruídas.
	D.trash_bin(self, c + Vector3(-1.35, y0, 0.75))
	B.model(self, "lifebuoy", c + Vector3(2.48, y0 + 1.8, 2.48), PI * 0.25, 0.8).rotation.x = PI * 0.5
	D.signpost(self, c + Vector3(-3.4, 0.05, 4.2), [["Vila", - PI * 0.5, Color(0.2, 0.55, 0.85)], ["Pousada", PI, Color(1.0, 0.45, 0.35)], ["Praia", PI * 0.5, Color(0.2, 0.7, 0.45)]])
	for tp in [Vector3(-3.0, 0, 3.4), Vector3(3.0, 0, 3.6), Vector3(-3.4, 0, -2.6), Vector3(3.5, 0, -3.0)]:
		var l: = D.tiki_torch(self, c + tp + Vector3(0, 0.05, 0))
		lanterns.append([l, null, 1.6, false])
	# caminho de tábuas até a calçada
	for k in 8:
		var plank: = B.box(self, Vector3(1.6, 0.06, 0.4), c + Vector3(rng_off(k) * 0.15, 0.04, 3.6 + k * 0.75), M.deckwood)
		plank.rotation.y = rng_off(k + 3) * 0.08

## Prateleira de fundo do quiosque (v0.7.3): três tábuas com montantes, onde as garrafas e o rádio apoiam de verdade.
func _back_bar(c: Vector3, y0: float) -> void :
	var w: Material = M.darkwood
	var z: = c.z - 1.92
	var yb: = c.y + y0 + 0.028
	for x in [-1.9, -0.65, 0.65, 1.9]:
		B.box(self, Vector3(0.07, 1.85, 0.36), Vector3(c.x + x, yb + 0.925, z), w)
	for top in [0.62, 1.21, 1.79]:
		B.box(self, Vector3(3.95, 0.05, 0.38), Vector3(c.x, c.y + y0 + top - 0.025, z), M.oak)
		B.box(self, Vector3(3.95, 0.07, 0.03), Vector3(c.x, c.y + y0 + top - 0.06, z + 0.19), w)
	B.box(self, Vector3(3.95, 1.85, 0.03), Vector3(c.x, yb + 0.925, z - 0.18), M.planks)
	# prateleira de baixo: jarros, potes e garrafas reais; o chão do vão guarda garrafas grandes
	var shelf_y: = c.y + y0 + 0.65
	var kinds: = ["jug_01", "k:bottle-oil", "ceramic_pot", "k:bottle-large", "pot_enamel_01", "k:bottle", "wooden_bowl_02", "k:bottle-oil", "jug_01"]
	var hts: = [0.3, 0.3, 0.2, 0.32, 0.24, 0.3, 0.12, 0.3, 0.3]
	var tints: = [Color.WHITE, Color(1.0, 0.8, 0.5), Color.WHITE, Color(0.6, 1.0, 0.7), Color(0.6, 0.9, 1.0), Color(1.0, 0.55, 0.5), Color.WHITE, Color(1.0, 0.95, 0.5), Color.WHITE]
	for i in 9:
		Real.place(self, kinds[i], Vector3(c.x - 1.7 + i * 0.42, shelf_y, z), hts[i], i * 0.9, tints[i])
	# garrafas da prateleira do meio e do alto
	for i in 8:
		Real.place(self, "k:bottle" if i % 2 == 0 else "k:bottle-large", Vector3(c.x - 1.65 + i * 0.47, c.y + y0 + 1.24, z), 0.3, i * 1.1, tints[(i + 3) % 9])
	for i in 6:
		Real.place(self, "k:bottle", Vector3(c.x - 0.3 + i * 0.13, c.y + y0 + 0.028, z + 0.05), 0.24, i * 0.8, tints[i])

## Suporte de pranchas atrás do quiosque: as pranchas encostam numa trave, nada fica no ar.
func _surf_rack(p: Vector3) -> void :
	var w: Material = M.darkwood
	B.box(self, Vector3(1.9, 0.12, 0.22), p + Vector3(0, 0.06, 0.05), w)
	for sx in [-0.95, 0.95]:
		B.box(self, Vector3(0.09, 1.45, 0.09), p + Vector3(sx, 0.725, -0.32), w)
		B.box(self, Vector3(0.08, 0.08, 0.5), p + Vector3(sx, 0.08, -0.15), w)
	B.box(self, Vector3(2.0, 0.09, 0.09), p + Vector3(0, 1.36, -0.32), w)
	var cols: = [Color(1.0, 0.45, 0.35), Color(0.2, 0.75, 0.95), Color(1.0, 0.85, 0.25)]
	for k in 3:
		# base na frente, topo apoiado na trave (inclinação para trás = -X)
		D.surfboard(self, p + Vector3(-0.6 + k * 0.6, 0.1, 0.1), PI, cols[k], 0.33)

func rng_off(k: int) -> float:
	return sin(float(k) * 12.9898) * 2.0 - 1.0 if k % 2 == 0 else cos(float(k) * 7.31)

## Expansão "drinks": garrafas, limões e taças com guarda-chuvinha.
func _kiosk_drinks(c: Vector3, y0: float) -> void :
	# Decoração apoiada no tampo lateral; bebidas são preparadas nas estações.
	Real.place(self, "g:bottle_cachaca", c + Vector3(-2.0, y0 + 1.18, 0.4), 0.32)
	Real.place(self, "food_lime_01", c + Vector3(-2.0, y0 + 1.18, 0.8), 0.08)


func _on_time(_d: int, _m: float) -> void :
	if _open_sign:
		var open: bool = Core.kiosk_accepting_customers()
		var txt: = "ABERTO" if open else "FECHADO"
		if _open_sign.text != txt:
			_open_sign.text = txt
			_open_sign.modulate = Color(0.15, 0.6, 0.25) if open else Color(0.8, 0.2, 0.15)

func _process(delta: float) -> void :
	super._process(delta)
	if _lighthouse and _night > 0.05:
		_lighthouse.rotation.y += delta * 0.8

# ------------------------------------------------------------------ v0.7.1: vila maior
const BACK_Z: = 64.0
const CROSS_X: = 1.5
const SHOP_SIGNS: = ["Farmácia", "Peixaria do Tonho", "Sorveteria Gelato", "Posto de Saúde", "Escola Municipal", "Correios", "Bar do Zé", "Barbearia", "Lojinha de Artesanato", "Açaí da Praia"]

var _road_n: = 0
func _road(a: Vector3, b: Vector3) -> void :
	var horizontal: = absf(b.x - a.x) > absf(b.z - a.z)
	var L: = a.distance_to(b)
	_road_n += 1
	var c: = (a + b) * 0.5 + Vector3(0, 0.005 * (_road_n % 4), 0)
	if horizontal:
		B.box(self, Vector3(L, 0.05, 4.0), Vector3(c.x, 0.02 + c.y, c.z), VM.road)
		for side in [-1.0, 1.0]:
			B.platform(self, Vector3(L, 0.3, 1.8), Vector3(c.x, c.y, c.z + side * 2.9), VM.calcada, 0.35)
			B.box(self, Vector3(L, 0.32, 0.22), Vector3(c.x, c.y, c.z + side * 2.05), VM.curb)
	else:
		B.box(self, Vector3(4.0, 0.05, L), Vector3(c.x, 0.02 + c.y, c.z), VM.road)
		for side in [-1.0, 1.0]:
			B.platform(self, Vector3(1.8, 0.3, L), Vector3(c.x + side * 2.9, c.y, c.z), VM.calcada, 0.35)
			B.box(self, Vector3(0.22, 0.32, L), Vector3(c.x + side * 2.05, c.y, c.z), VM.curb)

func _lamp_glow_mat() -> StandardMaterial3D:
	var gm: = StandardMaterial3D.new()
	gm.albedo_color = Color(1, 0.86, 0.55)
	gm.emission_enabled = true
	gm.emission = Color(1.0, 0.72, 0.32)
	gm.emission_energy_multiplier = 0.0
	gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return gm

## Cabeça de poste do Blender (g:lamp_globe): o centro do globo (0,31 m no modelo) fica em `c`.
func _lamp_head(c: Vector3, gm: StandardMaterial3D, sc: float = 1.1) -> void :
	if Real.place_glow(self, "g:lamp_globe", c - Vector3(0, 0.31 * sc, 0), -sc, 0.0, gm) != null:
		return
	var glow: = MeshInstance3D.new()
	var sm: = SphereMesh.new()
	sm.radius = 0.22
	sm.height = 0.44
	glow.mesh = sm
	glow.material_override = gm
	glow.position = c
	glow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(glow)

func _add_lamp(p: Vector3) -> void :
	B.model(self, "street_lamp_01", p, 0.0, 1.0)
	var gm: = _lamp_glow_mat()
	_lamp_head(p + Vector3(0, 3.5, 0), gm)
	var l: = OmniLight3D.new()
	l.position = p + Vector3(0, 3.35, 0)
	l.omni_range = 11.0
	l.light_color = Color(1.0, 0.74, 0.42)
	l.light_energy = 0.0
	add_child(l)
	lanterns.append([l, gm, 2.6, false])

func _village_expansion() -> void :
	var rng: = RandomNumberGenerator.new()
	rng.seed = 1717
	# ruas novas: a da pousada (sobe do mar até a rua de trás) e a rua de trás, paralela à principal
	_road(Vector3(CROSS_X, 0, STREET_Z + 2.1), Vector3(CROSS_X, 0, BACK_Z - 2.1))
	_road(Vector3(-1.0, 0, BACK_Z), Vector3(109.0, 0, BACK_Z))
	_road(Vector3(104.0, 0, STREET_Z + 2.1), Vector3(104.0, 0, BACK_Z - 2.1))
	var x1: = 99.0
	B.box(self, Vector3(109.0 - x1, 0.05, 4.0), Vector3((x1 + 109.0) * 0.5, 0.02, STREET_Z), VM.road)
	var si: = 0
	var ci: = 3
	# rua principal, lado oeste (perto da pousada)
	for hh in [[12.0, 7.0], [20.5, 7.5], [28.5, 6.5]]:
		_house(Vector3(hh[0], 0, 21.2), hh[1], 7.0, 1.0, HOUSE_COLS[ci % HOUSE_COLS.size()], SHUT_COLS[ci % SHUT_COLS.size()], ci % 2 == 0)
		ci += 1
	for hh in [[10.0, 7.0], [18.0, 7.0], [26.0, 6.5], [34.0, 6.0]]:
		var sign_t: = ""
		if hh[0] == 18.0:
			sign_t = SHOP_SIGNS[si]
			si += 1
		_house(Vector3(hh[0], 0, 38.8), hh[1], 7.0, -1.0, HOUSE_COLS[ci % HOUSE_COLS.size()], SHUT_COLS[(ci + 1) % SHUT_COLS.size()], ci % 3 == 0, sign_t)
		ci += 1
	# rua de trás: lado sul (de costas para a praça e a feira) e lado norte
	for x in [10.0, 18.0, 26.0, 34.0, 42.0, 50.0, 58.0, 92.0, 100.0]:
		var sign_a: = ""
		if int(x) % 16 == 2 and si < SHOP_SIGNS.size():
			sign_a = SHOP_SIGNS[si]
			si += 1
		_house(Vector3(x, 0, BACK_Z - 6.6), rng.randf_range(6.0, 7.2), 6.6, 1.0, HOUSE_COLS[ci % HOUSE_COLS.size()], SHUT_COLS[ci % SHUT_COLS.size()], rng.randf() < 0.4, sign_a)
		ci += 1
	var x2: = 6.0
	while x2 < 106.0:
		var sign_b: = ""
		if rng.randf() < 0.45 and si < SHOP_SIGNS.size():
			sign_b = SHOP_SIGNS[si]
			si += 1
		var w: = rng.randf_range(6.0, 7.4)
		_house(Vector3(x2, 0, BACK_Z + 6.6), w, 6.6, -1.0, HOUSE_COLS[ci % HOUSE_COLS.size()], SHUT_COLS[(ci + 2) % SHUT_COLS.size()], rng.randf() < 0.45, sign_b)
		ci += 1
		x2 += 8.0
	# feira entre a rua principal e a rua de trás
	var feira_c: = Vector3(34.0, 0, 48.0)
	B.platform(self, Vector3(24.0, 0.15, 7.0), feira_c, VM.calcada, 0.3)
	var goods: = [[Color(1.0, 0.35, 0.3), Color(1.0, 0.75, 0.2), Color(0.4, 0.8, 0.3)], [Color(0.9, 0.85, 0.3), Color(0.95, 0.55, 0.2)], [Color(0.55, 0.3, 0.7), Color(0.3, 0.6, 0.25), Color(1.0, 0.4, 0.5)], [Color(0.6, 0.85, 0.95), Color(0.95, 0.95, 0.9)]]
	var aw: = [Color(1.0, 0.35, 0.3), Color(0.2, 0.6, 0.95), Color(0.3, 0.75, 0.4), Color(1.0, 0.7, 0.2), Color(0.85, 0.4, 0.85)]
	for k in 5:
		var sp: = feira_c + Vector3(-9.6 + k * 4.8, 0.08, -1.4)
		D.stall(self, sp, 0.0, aw[k], goods[k % goods.size()])
		_block(sp, 2.6, 1.6, 0.3)
	B.label(self, "FEIRA DA VILA", feira_c + Vector3(0, 3.4, -2.6), 90, Color(1.0, 0.95, 0.6), Color(0.45, 0.2, 0.05, 1.0), PI)
	var feira_top: = 3.3
	for sx in [-1.0, 1.0]:
		var pp: = feira_c + Vector3(sx * 11.6, 0.0, -2.6)
		pp.y = 0.0
		if Real.place(self, "g:bamboo_pole", pp, 3.6, 0.0) != null:
			feira_top = 3.6 * 4.48 / 4.62
		else:
			B.cyl(self, 0.08, 0.08, 3.6, feira_c + Vector3(sx * 11.6, 1.8, -2.6), D.m(Color(0.6, 0.42, 0.25)), 8)
	D.bunting(self, feira_c + Vector3(-11.6, feira_top, -2.6), feira_c + Vector3(11.6, feira_top, -2.6), 0.6, 0.5)
	# bandeirinhas atravessando as ruas
	# v0.9.3: cada fio vai de uma fachada à da frente (preso sob a cornija com um gancho), nunca solto no ar
	_street_bunting(STREET_Z, 9.0)
	_street_bunting(BACK_Z, 12.0)
	# postes de luz de madeira com fios
	var prev: = Vector3.INF
	var px: = 0.0
	while px < 110.0:
		var top: = D.power_pole(self, Vector3(px, 0, BACK_Z - 3.9))
		if prev != Vector3.INF:
			for o in [-0.6, 0.0, 0.6]:
				D.wire(self, prev + Vector3(o, 0, 0), top + Vector3(o, 0, 0), 0.5)
		prev = top
		px += 15.0
	# postes de iluminação nas ruas novas
	var lx: = 6.0
	while lx < 106.0:
		_add_lamp(Vector3(lx, 0.15, BACK_Z + 3.5))
		lx += 14.0
	for lz in [40.0, 52.0]:
		_add_lamp(Vector3(CROSS_X - 3.5, 0.15, lz))
		_add_lamp(Vector3(104.0 + 3.5, 0.15, lz))
	# caixinhas de correio, bancos, bichos
	for k in 8:
		D.mailbox(self, Vector3(9.0 + k * 12.0, 0.15, BACK_Z + 2.4), 0.0)
	# gatos com os pés no piso: varanda (topo a 0,09 m) ou calçada (topo a 0,15 m); antes ficavam a 0,3 m, flutuando
	D.cat(self, Vector3(20.5, 0.09, 25.2), 0.4, Color(0.95, 0.6, 0.25))
	D.cat(self, Vector3(62.0, 0.09, 26.0), -1.2, Color(0.2, 0.2, 0.22))
	D.cat(self, Vector3(42.0, 0.15, BACK_Z - 2.6), 2.0, Color(0.95, 0.95, 0.92))
	D.dog(self, Vector3(66.0, 0.15, 33.6), 1.4, Color(0.75, 0.55, 0.32))
	D.dog(self, Vector3(30.0, 0.15, BACK_Z + 2.8), -0.6, Color(0.95, 0.9, 0.82))
	for k in 4:
		var bp: = Vector3(16.0 + k * 22.0, 0.15, BACK_Z + 2.4)
		bench_spots.append(_bench(bp, PI))
	for k in 6:
		_bike(Vector3(14.0 + k * 15.0, 0.15, BACK_Z - 2.6), PI * 0.5, D.FLAG_COLS[k % D.FLAG_COLS.size()])
	# píer e farol
	D.pier(self, Vector3(PIER_X, -0.25, -22.0), 27.0, 2.6)
	var ramp: = B.box(self, Vector3(2.6, 0.2, 2.4), Vector3(PIER_X, 0.065, -21.0), B.mat("weathered_planks", 0.6, Color(0.9, 0.7, 0.5), 0.85), true)
	ramp.name = "PierAccessRamp"
	ramp.rotation.x = 0.2
	for sx in [-1.0, 1.0]:
		B.wall(self, Vector3(0.2, 3.0, 28.0), Vector3(PIER_X + sx * 1.35, 1.6, -36.0))
	B.wall(self, Vector3(5.0, 3.0, 0.2), Vector3(PIER_X, 1.6, -49.0))
	# pesca no fim do píer (a lógica fica em village_life) e o Seu Zé na cabeceira
	fish_spot = Interactable.new()
	fish_spot.name = "Pesca"
	var fcs: = CollisionShape3D.new()
	var fsh: = BoxShape3D.new()
	fsh.size = Vector3(4.0, 1.8, 0.9)
	fcs.shape = fsh
	fish_spot.add_child(fcs)
	fish_spot.position = Vector3(PIER_X, 1.4, -49.3)
	add_child(fish_spot)
	village_points.ze = Vector3(PIER_X + 3.0, 0.1, -23.7)
	_quest_giver("peixe_ze", "Seu Zé", Vector3(PIER_X + 3.0, 1.0, -23.3), Vector3(1.0, 1.8, 1.0))
	for sx in [-1.0, 1.0]:
		B.wall(self, Vector3(0.2, 3.0, 3.2), Vector3(PIER_X + sx * 2.5, 1.6, -47.5))
	_lighthouse = D.lighthouse(self, Vector3(108.0, 0.0, -40.0))
	# caminhos novos dos moradores
	var bn: = BACK_Z - 2.9
	var bs: = BACK_Z + 2.9
	village_paths.append([Vector3(-1, 0.15, bn), Vector3(30, 0.15, bn), Vector3(70, 0.15, bn), Vector3(107, 0.15, bn)])
	village_paths.append([Vector3(107, 0.15, bs), Vector3(60, 0.15, bs), Vector3(20, 0.15, bs), Vector3(-1, 0.15, bs)])
	village_paths.append([Vector3(CROSS_X + 2.9, 0.15, STREET_Z + 3.5), Vector3(CROSS_X + 2.9, 0.15, bn)])
	village_paths.append([Vector3(104 - 2.9, 0.15, bn), Vector3(104 - 2.9, 0.15, STREET_Z + 3.5)])
	village_paths.append([feira_c + Vector3(-11, 0.15, 1.6), feira_c + Vector3(11, 0.15, 1.6), feira_c + Vector3(11, 0.15, 2.8), feira_c + Vector3(-11, 0.15, 2.8)])
	village_paths.append([Vector3(PIER_X, 0.4, -24.0), Vector3(PIER_X, 0.4, -46.0)])

# ------------------------------------------------------------------ v0.7.1: vida na praia
func _beach_life() -> void :
	var spots: = [Vector3(55, 0, -22), Vector3(47, 0, -22.5), Vector3(4, 0, -27.0), Vector3(95, 0, -22.0), Vector3(-36, 0, -21.0)]
	for i in spots.size():
		var p: Vector3 = spots[i]
		p.y = _height(p.x, p.z)
		D.beach_spot(self, p, 50 + i)
	D.sand_castle(self, Vector3(33.0, _height(33, -24.5), -24.5))
	# Active volleyball court is built by CoastalLife beside the beach-facing kiosk.
	var rng: = RandomNumberGenerator.new()
	rng.seed = 99
	for k in 14:
		var sp: = Vector3(rng.randf_range(-40, 100), 0, rng.randf_range(-28.5, -25.5))
		sp.y = _height(sp.x, sp.z)
		D.starfish(self, sp, [Color(1.0, 0.5, 0.35), Color(1.0, 0.8, 0.3), Color(0.95, 0.4, 0.6)][k % 3])
	for k in 7:
		var cp: = Vector3(rng.randf_range(-35, 100), 0, rng.randf_range(-29.0, -26.0))
		cp.y = _height(cp.x, cp.z) + 0.01
		D.crab(self, cp, rng.randf_range(1.0, 2.2))
	_sand_clutter(rng)


## Revisão visual 18/10/2026: a areia entre o mato e a praia era lisa demais. Espalha seixos, conchas, touceiras e flores (CC0).
func _sand_clutter(rng: RandomNumberGenerator) -> void :
	var kinds: = [
		["q:Pebble_Round_1", 0.12, 0.26], ["q:Pebble_Round_3", 0.1, 0.22], ["q:Pebble_Square_2", 0.12, 0.24],
		["lambis_shell", 0.1, 0.2], ["q:Grass_Wispy_Short", 0.3, 0.5], ["q:Grass_Common_Short", 0.25, 0.4],
		["q:Flower_3_Group", 0.25, 0.4], ["q:Flower_4_Group", 0.25, 0.4],
		["periwinkle_plant", 0.25, 0.4], ["fern_02", 0.3, 0.5],
	]
	var placed: = 0
	var tries: = 0
	while placed < 150 and tries < 900:
		tries += 1
		var x: = rng.randf_range(-40.0, 98.0)
		var z: = rng.randf_range(-25.0, -5.0)
		var q: = Vector2(x, z)
		var bad: = Rect2(21.5,-27.5,9,9).has_point(q)
		for r in block_rects:
			if (r as Rect2).grow(1.2).has_point(q):
				bad = true
				break
		if bad or (absf(x - 38.0) < 8.0 and z > -20.0) or (x > 55.0 and x < 97.0 and z < -22.0):
			continue
		var k: Array = kinds[rng.randi() % kinds.size()]
		Real.place(self, str(k[0]), Vector3(x, _height(x, z) - 0.01, z), rng.randf_range(float(k[1]), float(k[2])), rng.randf() * TAU)
		placed += 1


# ------------------------------------------------------------------ v0.7.2: igreja, praça, píer e farol detalhados
func _landmark_details() -> void :
	var c: = CHURCH_C
	var w: = 10.0
	var d: = 12.0
	var white: = stucco(Color(0.98, 0.97, 0.94))
	var yellow: = stucco(Color(0.98, 0.8, 0.3))
	var blue: = stucco(Color(0.2, 0.42, 0.72))
	var stained: = [Color(0.95, 0.3, 0.35), Color(0.3, 0.55, 0.95), Color(1.0, 0.8, 0.25), Color(0.35, 0.8, 0.45)]
	# janelas em arco com vitral nas laterais, pilastras e cornija
	for sx in [-1.0, 1.0]:
		var x: float = c.x + sx * (w * 0.5 + 0.04)
		for k in 3:
			var z: = c.z - 3.6 + k * 3.6
			var piv: = Node3D.new()
			piv.position = Vector3(x, 0, z)
			piv.rotation.y = sx * PI * 0.5
			add_child(piv)
			B.box(piv, Vector3(1.3, 2.6, 0.12), Vector3(0, 3.0, 0), yellow)
			var g: = StandardMaterial3D.new()
			g.albedo_color = stained[(k + int(sx + 1.0)) % stained.size()]
			g.emission_enabled = true
			g.emission = g.albedo_color
			g.emission_energy_multiplier = 0.35
			g.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
			B.box(piv, Vector3(0.9, 2.1, 0.14), Vector3(0, 2.95, 0.02), g)
			B.arch(piv, Vector3(0, 4.0, 0.02), 0.45, 0.65, 0.16, yellow)
			var semi: = B.arch(piv, Vector3(0, 4.0, 0.0), 0.0, 0.45, 0.12, g)
			semi.name = "Vitral" 
			B.box(piv, Vector3(0.05, 2.1, 0.16), Vector3(0, 2.95, 0.03), yellow)
			B.box(piv, Vector3(0.9, 0.05, 0.16), Vector3(0, 3.3, 0.03), yellow)
			B.box(piv, Vector3(1.5, 0.12, 0.3), Vector3(0, 1.6, 0.1), white)
		for k in 5:
			B.box(self, Vector3(0.3, 7.0, 0.5), Vector3(x + sx * 0.08, 3.5, c.z - d * 0.5 + 0.4 + k * 2.8), yellow)
	B.box(self, Vector3(w + 0.5, 0.3, d + 0.5), c + Vector3(0, 6.85, 0), white)
	B.box(self, Vector3(w + 0.7, 0.14, d + 0.7), c + Vector3(0, 7.05, 0), yellow)
	# arco da porta, sino visível na torre e lanternas
	B.arch(self, c + Vector3(0, 3.6, - d * 0.5 - 0.1), 1.0, 1.25, 0.2, yellow, PI)
	B.arch(self, c + Vector3(0, 3.6, - d * 0.5 - 0.06), 0.0, 1.0, 0.1, wood_tint(Color(0.45, 0.25, 0.12)), PI)
	var tc: = c + Vector3(w * 0.5 + 1.6, 0, - d * 0.5 + 1.6)
	var gold: = B.flat(Color(0.95, 0.75, 0.25), 0.3, 0.8)
	if Real.place(self, "g:bell", tc + Vector3(0, 10.05, 0), -1.0, 0.0, Color.WHITE, 0.0, false) == null:
		B.cyl(self, 0.2, 0.55, 0.9, tc + Vector3(0, 10.6, 0), gold, 24)
		B.sphere(self, 0.22, tc + Vector3(0, 11.1, 0), gold)
		B.sphere(self, 0.08, tc + Vector3(0, 10.1, 0), B.flat(Color(0.3, 0.25, 0.2), 0.5))
	B._beam(self, tc + Vector3(-1.4, 11.3, 0), tc + Vector3(1.4, 11.3, 0), 0.07, wood_tint(Color(0.4, 0.25, 0.14)))
	for sx in [-1.0, 1.0]:
		var lp: = c + Vector3(sx * 2.2, 0, - d * 0.5 - 0.15)
		B.box(self, Vector3(0.12, 0.12, 0.3), lp + Vector3(0, 2.9, 0), B.flat(Color(0.15, 0.15, 0.17), 0.5, 0.4))
		B.cyl(self, 0.12, 0.09, 0.32, lp + Vector3(0, 2.75, -0.18), VM.glass, 12)
	# canteiros e gradil do adro
	for sx in [-1.0, 1.0]:
		var bed: = c + Vector3(sx * 3.4, 0, - d * 0.5 - 0.8)
		B.box(self, Vector3(2.2, 0.35, 0.9), bed + Vector3(0, 0.17, 0), blue)
		Real.place(self, "g:flowerbed", bed + Vector3(0, 0.34, 0), -1.0, 0.0, Color.WHITE, 0.0, false)
	var iron: = B.flat(Color(0.12, 0.12, 0.14), 0.5, 0.4)
	for seg in [[c.x - 6.0, c.x - 1.6], [c.x + 1.6, c.x + 6.0]]:
		var x0: float = seg[0]
		while x0 <= seg[1]:
			B.cyl(self, 0.02, 0.02, 1.1, Vector3(x0, 0.65, c.z - d * 0.5 - 1.5), iron, 6)
			B.cyl(self, 0.0, 0.04, 0.1, Vector3(x0, 1.25, c.z - d * 0.5 - 1.5), iron, 6)
			x0 += 0.22
		B._beam(self, Vector3(seg[0], 1.0, c.z - d * 0.5 - 1.5), Vector3(seg[1], 1.0, c.z - d * 0.5 - 1.5), 0.02, iron)
		B._beam(self, Vector3(seg[0], 0.3, c.z - d * 0.5 - 1.5), Vector3(seg[1], 0.3, c.z - d * 0.5 - 1.5), 0.02, iron)
	# praça: banca de jornal, carrinho de pipoca e pombinhos
	var pc: = Vector3(PRACA.get_center().x, 0.1, PRACA.get_center().y)
	var banca: = pc + Vector3(7.4, 0, -3.2)
	# v0.9.5: banca de jornal do Blender (frisos, toldo recortado, revistas nos expositores); frente para -Z como antes
	if Real.place(self, "g:newsstand", banca, -1.0, PI, Color.WHITE, 0.0, false) != null:
		B.label(self, "BANCA", banca + Vector3(0, 2.27, -0.86), 48, Color(1, 1, 1), Color(0.1, 0.3, 0.15, 1), PI).pixel_size = 0.005
	else:
		B.box(self, Vector3(2.2, 2.2, 1.6), banca + Vector3(0, 1.1, 0), B.flat(Color(0.2, 0.55, 0.35), 0.6))
	var pip: = pc + Vector3(-4.6, 0, 2.9)   # v0.9.5: afastado do carrinho de café (encostavam)
	# v0.9.5: carrinho de pipoca do Blender (vitrine, rodas raiadas, guarda-sol listrado); pipoca dentro da vitrine
	if Real.place(self, "g:popcorn_cart", pip, -1.0, PI, Color.WHITE, 0.0, false) != null:
		Real.place(self, "g:popcorn", pip + Vector3(0.05, 1.16, -0.02), -1.35, 0.0, Color(1.0, 0.93, 0.7), 0.0, true)   # vitrine cheia, pipoca amanteigada
		B.label(self, "PIPOCA", pip + Vector3(-0.25, 0.75, -0.38), 40, Color.WHITE, Color(0.6, 0.1, 0.1, 1), PI).pixel_size = 0.004
	else:
		B.box(self, Vector3(1.0, 0.9, 0.7), pip + Vector3(0, 0.75, 0), B.flat(Color(0.95, 0.25, 0.25), 0.5))
	var rng: = RandomNumberGenerator.new()
	rng.seed = 3131
	for k in 10:
		var bp: = pc + Vector3(rng.randf_range(-5, 5), 0.0, rng.randf_range(-3, 3.5))
		if bp.distance_to(pc) < 2.6:
			continue
		var bird: = Node3D.new()
		bird.position = bp
		bird.rotation.y = rng.randf() * TAU
		add_child(bird)
		bird.add_to_group("gull")
		if Real.place(bird, "g:seagull_perch", Vector3.ZERO, -1.25, 0.0, Color.WHITE, 0.0, true) == null:
			B.sphere(bird, 0.09, Vector3(0, 0.09, 0), B.flat(Color(0.6, 0.62, 0.7), 0.7), Vector3(0.8, 0.8, 1.3))
			B.sphere(bird, 0.05, Vector3(0, 0.18, 0.09), B.flat(Color(0.45, 0.5, 0.6), 0.7))
	# píer: postes com lanternas, caixotes e rolos de corda, barquinho amarrado
	var wood: = wood_tint(Color(0.45, 0.3, 0.2))
	for k in 4:
		var lz: = -24.0 - k * 7.5
		for sx in [-1.0, 1.0]:
			var lp2: = Vector3(PIER_X + sx * 1.25, 0.3, lz)
			B.cyl(self, 0.05, 0.06, 1.6, lp2 + Vector3(0, 0.8, 0), wood, 8)
			if Real.place_glow(self, "g:lamp_globe", lp2 + Vector3(0, 1.6, 0), -0.6, 0.0, P.glow(Color(1.0, 0.8, 0.45), 1.6)) == null:
				B.sphere(self, 0.12, lp2 + Vector3(0, 1.7, 0), P.glow(Color(1.0, 0.8, 0.45), 1.6))
	var end: = Vector3(PIER_X, 0.37, -47.0)
	for k in 3:
		B.model(self, "wooden_crate_01", end + Vector3(-1.9 + (k % 2) * 0.1, k * 0.0, 0.6 - k * 0.7), k * 0.4, 0.8)
	# rolo de corda de verdade (Blender), não argolas empilhadas
	Real.place(self, "g:rope_coil", end + Vector3(1.75, 0.0, 0.2), -1.0, 0.7, Color.WHITE, 0.0, false)
	_fishing_boat(Vector3(PIER_X + 4.0, -0.25, -44.0), 0.1, Color(0.2, 0.6, 0.55))
	# farol: porta, janelinhas, balcão com gradil e casinha do faroleiro
	var fp: = Vector3(108.0, 0.0, -40.0)
	B.box(self, Vector3(0.9, 1.7, 0.2), fp + Vector3(0, 1.85, -1.55), B.flat(Color(0.25, 0.45, 0.8), 0.6))
	for k in 4:
		var a: = k * 1.7
		var r: = lerpf(1.6, 1.05, (3.0 + k * 2.6) / 14.0) + 0.02
		var win: = B.box(self, Vector3(0.35, 0.55, 0.12), fp + Vector3(sin(a) * r, 4.0 + k * 2.6, - cos(a) * r), VM.window_glass)
		win.rotation.y = - a
	for k in 20:
		var a2: = TAU * k / 20.0
		B.cyl(self, 0.02, 0.02, 0.6, fp + Vector3(cos(a2) * 1.42, 15.5, sin(a2) * 1.42), iron, 6)
	var ring: = TorusMesh.new()
	ring.inner_radius = 1.38
	ring.outer_radius = 1.46
	ring.rings = 40
	var rmi: = MeshInstance3D.new()
	rmi.mesh = ring
	rmi.material_override = iron
	rmi.position = fp + Vector3(0, 15.8, 0)
	add_child(rmi)
	var hut: = Vector3(99.0, 0.0, -27.5)
	hut.y = _height(hut.x, hut.z)
	B.box(self, Vector3(3.0, 2.4, 2.6), hut + Vector3(0, 1.2, 0), stucco(Color(0.98, 0.97, 0.94)), true)
	B.hip_roof(self, hut + Vector3(0, 2.45, 0), 3.8, 3.4, 1.4, VM.clay, 0.12)
	B.box(self, Vector3(0.8, 1.7, 0.1), hut + Vector3(0, 0.85, 1.32), B.flat(Color(0.95, 0.3, 0.25), 0.6))

# ------------------------------------------------------------------ v0.7.2: mapa cheio de detalhes miúdos
func _map_details() -> void :
	var rng: = RandomNumberGenerator.new()
	rng.seed = 2468
	# conchas e pedrinhas na areia: modelos do Blender (g:pebble_*, g:shell_*), um MultiMesh por tipo
	var kinds: = ["pebble_a", "pebble_b", "pebble_c", "shell_a", "shell_b", "shell_c"]
	var kx: = {}
	for kn in kinds:
		kx[kn] = []
	for k in 900:
		var p: = Vector3(rng.randf_range(-45, 104), 0, rng.randf_range(-30.0, -17.0))
		if Rect2(21.5,-27.5,9,9).has_point(Vector2(p.x,p.z)): continue
		p.y = _height(p.x, p.z) - 0.004
		var kn: String = kinds[rng.randi() % kinds.size()]
		var sc: = rng.randf_range(0.6, 1.5) * (1.0 if kn.begins_with("shell") else 1.3)
		var tilt: = Basis(Vector3.RIGHT, rng.randf_range(-0.08, 0.08)) if kn.begins_with("shell") else Basis(Vector3.RIGHT, rng.randf() * TAU)
		kx[kn].append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU) * tilt * Basis.from_scale(Vector3.ONE * sc), p))
	for kn in kinds:
		var pm: Mesh = Real.mesh_of("g:" + kn)
		if pm == null:
			continue
		var mi1: = D.multimesh(self, pm, kx[kn])
		mi1.material_override = null
		mi1.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi1.visibility_range_end = 45.0
	# algas na linha da maré
	var weed_x: = []
	for k in 160:
		var p: = Vector3(rng.randf_range(-45, 104), 0, rng.randf_range(-30.5, -28.5))
		p.y = _height(p.x, p.z) + 0.01
		weed_x.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU), p))
	var wm: Mesh = Real.mesh_of("g:alga")
	var mi3: MultiMeshInstance3D
	if wm != null:
		mi3 = D.multimesh(self, wm, weed_x)
		mi3.material_override = null
	else:
		var bm: = BoxMesh.new()
		bm.size = Vector3(0.5, 0.015, 0.06)
		mi3 = D.multimesh(self, bm, weed_x, [], B.flat(Color(0.2, 0.42, 0.25), 0.8))
	mi3.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi3.visibility_range_end = 60.0
	# troncos trazidos pelo mar
	for k in 10:
		var p: = Vector3(rng.randf_range(-40, 100), 0, rng.randf_range(-27.0, -19.0))
		if absf(p.x - KIOSK_C.x) < 7.0 or absf(p.x - PIER_X) < 4.0 or Rect2(20.5,-28.5,11,11).has_point(Vector2(p.x,p.z)):
			continue
		p.y = _height(p.x, p.z) + 0.08
		var a: = rng.randf() * TAU
		var L: = rng.randf_range(1.2, 2.6)
		B._beam(self, p - Vector3(cos(a), 0, sin(a)) * L * 0.5, p + Vector3(cos(a), 0, sin(a)) * L * 0.5, rng.randf_range(0.08, 0.14), B.flat(Color(0.72, 0.62, 0.5), 0.95))
	# pegadas na areia molhada
	var fx: = []
	var px: = -10.0
	var pz: = -26.5
	for k in 60:
		px += 0.42
		pz += sin(k * 0.3) * 0.08
		var side: = 0.12 if k % 2 == 0 else -0.12
		fx.append(Transform3D(Basis(Vector3.UP, 0.0).scaled(Vector3(0.6, 1.0, 1.0)), Vector3(px, _height(px, pz + side) + 0.012, pz + side)))
	var fm: = CylinderMesh.new()
	fm.top_radius = 0.09
	fm.bottom_radius = 0.09
	fm.height = 0.01
	fm.radial_segments = 12
	var mi4: = D.multimesh(self, fm, fx, [], B.flat(Color(0.85, 0.68, 0.45), 0.9))
	mi4.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# vila: vasos nas calçadas, tampas de bueiro, varais de roupa e árvores nos quintais
	for k in 26:
		var on_back: = k % 2 == 0
		var vx: = rng.randf_range(4, 104)
		var vz: = (BACK_Z + 2.4 * (1.0 if rng.randf() < 0.5 else -1.0)) if on_back else (STREET_Z + 2.4 * (1.0 if rng.randf() < 0.5 else -1.0))
		B.model(self, ["potted_plant_01", "potted_plant_02", "planter_pot_clay", "potted_plant_04"][k % 4], Vector3(vx, 0.16, vz), rng.randf() * TAU, rng.randf_range(0.8, 1.1))
	for k in 12:
		var mx: = 6.0 + k * 9.0
		for zz in [STREET_Z, BACK_Z]:
			var cap: = B.cyl(self, 0.32, 0.32, 0.02, Vector3(mx, 0.065 + (0.012 if zz == BACK_Z else 0.0), zz + 0.8), B.flat(Color(0.35, 0.35, 0.38), 0.5, 0.5), 20)
			cap.name = "Bueiro"
	for k in 8:
		var lx: = 10.0 + k * 12.0
		var lz: = BACK_Z + 11.5
		var pole_m: = wood_tint(Color(0.5, 0.35, 0.22))
		var a2: = Vector3(lx - 2.5, 0, lz)
		var b2: = Vector3(lx + 2.5, 0, lz)
		# varal: mastros de bambu, fio e roupas de pano do Blender (camisetas e toalhas com prendedores), tingidas
		var top_y: = 1.95
		for pp in [a2, b2]:
			if Real.place(self, "g:bamboo_pole", pp, 2.0, 0.0) == null:
				B.cyl(self, 0.04, 0.05, 2.0, pp + Vector3(0, 1.0, 0), pole_m, 8)
		D.wire(self, a2 + Vector3(0, top_y, 0), b2 + Vector3(0, top_y, 0), 0.25)
		for j in 6:
			var t6: = (j + 0.5) / 6.0
			var cp: = a2.lerp(b2, t6) + Vector3(0, top_y - 0.25 * 4.0 * t6 * (1.0 - t6), 0)
			var piece: = Real.place(self, "g:cloth_shirt" if j % 2 == 0 else "g:cloth_towel", cp, -1.0, rng.randf_range(-0.06, 0.06), Color.WHITE, 0.0, false)
			if piece:
				piece.position.y = cp.y - B.aabb_of(piece).size.y + 0.04   # prendedores no fio, pano pendurado embaixo
				Real.tint_named(piece, D.FLAG_COLS[(j + k) % D.FLAG_COLS.size()])
			else:
				B.box(self, Vector3(0.45, 0.5, 0.02), cp, B.flat(D.FLAG_COLS[(j + k) % D.FLAG_COLS.size()], 0.95))
	for k in 12:
		B.model(self, "island_tree_01", Vector3(4.0 + k * 9.0 + rng.randf_range(-2, 2), 0, BACK_Z + 14.5 + rng.randf_range(-1, 2)), rng.randf() * TAU, rng.randf_range(1.6, 2.2))

func _refresh_company_signs() -> void:
	_apply_kiosk_look()
	_on_time(Core.day, Core.minutes)
	var rules = load("res://scripts/company_rules.gd")
	for sign in company_signs:
		rules.fit_sign(sign.label, str(Core.company.name) if Core.company.created else "MARÉ ALTA", str(Core.company.font), str(Core.company.color), float(sign.width))

func _apply_kiosk_look() -> void:
	var m: Dictionary = Core.company.sim.management
	var key: String = JSON.stringify(m.look) if m.look_owned else "legacy"
	if key == _look_key: return
	_look_key = key
	var rules = Core.CompanyRules.Simulation.Management
	var look: Dictionary = m.look if m.look_owned else rules.defaults().look
	var paint_material := B.mat("weathered_planks", 0.6, rules.PAINT[look.paint]).duplicate() as StandardMaterial3D
	paint_material.albedo_color = rules.PAINT[look.paint]
	var board_material := B.mat("weathered_planks", 0.6, rules.BOARDS[look.board]).duplicate() as StandardMaterial3D
	board_material.albedo_color = rules.BOARDS[look.board]
	for mesh in _painted:
		if not mesh.has_meta("original_look"): mesh.set_meta("original_look", mesh.material_override)
		mesh.material_override = paint_material if m.look_owned else mesh.get_meta("original_look")
	for mesh in _sign_panels:
		if not mesh.has_meta("original_look"): mesh.set_meta("original_look", mesh.material_override)
		mesh.material_override = board_material if m.look_owned else mesh.get_meta("original_look")
	if is_instance_valid(_kiosk_board): _kiosk_board.visible = bool(look.menu)
	for menu in _table_menus: menu.visible = bool(look.menu)
	for group in _table_looks:
		var offset := Vector3(float(group.side) * 0.85, 0, 0.55) if look.layout == "amplo" else Vector3.ZERO
		for entry in group.nodes: entry.node.position = entry.position + offset
		for entry in group.seats:
			for field in ["pos", "approach", "serve_pos"]: entry.spot[field] = kiosk_authored(entry.base[field] + offset)
		var rect: Rect2 = group.rect
		rect.position += Vector2(offset.x, offset.z)
		block_rects[int(group.block)] = kiosk_rect(rect)
