extends "res://scripts/world.gd"




const STREET_Z: = 30.0
const HOME_C: = Vector3(46, 0, 21)
const KIOSK_C: = Vector3(38, 0, -13)
const CHURCH_C: = Vector3(75, 0, 50)
const PRACA: = Rect2(66, 34.5, 18, 9.3)

var village_points: = {}
var village_paths: Array = []
var kiosk_counter: Interactable
var kiosk_spots: Array = []
var bed: Interactable
var home_wake: = Vector3(HOME_C.x - 0.8, 0.2, HOME_C.z - 0.6)
var bench_spots: Array = []
var market: Interactable
var quest_board: Interactable
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
	VM.glass = glass

func stucco(c: Color) -> Material:
	return B.mat("white_stucco", 0.5, c, 0.88)

func wood_tint(c: Color) -> Material:
	return B.mat("weathered_planks", 0.9, c, 0.7)

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
	var clay_m: = B.flat(Color(0.82, 0.42, 0.26), 0.8)
	B.cyl(self, 0.24, 0.18, 0.38, p + Vector3(0, 0.19, 0), clay_m, 24)
	B.cyl(self, 0.26, 0.26, 0.06, p + Vector3(0, 0.38, 0), B.flat(Color(0.7, 0.34, 0.2), 0.8), 24)
	B.cyl(self, 0.22, 0.22, 0.02, p + Vector3(0, 0.4, 0), B.flat(Color(0.32, 0.2, 0.12), 0.9), 24)
	var back: = - front * 0.18
	for sx in [-0.42, 0.42]:
		B.box(self, Vector3(0.04, 2.5, 0.04), p + Vector3(sx, 1.25, back), wood)
	for k in 5:
		B.box(self, Vector3(0.9, 0.03, 0.03), p + Vector3(0, 0.7 + k * 0.42, back), wood)
	# galhos subindo do vaso
	var stem: = B.flat(Color(0.35, 0.22, 0.12), 0.9)
	for sx in [-0.25, 0.05, 0.3]:
		var st: = B.cyl(self, 0.022, 0.03, 1.9, p + Vector3(sx * 0.6, 1.3, back * 0.6), stem, 8)
		st.rotation.z = sx * 0.35
	var rng: = RandomNumberGenerator.new()
	rng.seed = int(p.x * 13.0 + p.z * 7.0)
	for i in 26:
		var h: = rng.randf_range(0.6, 2.55)
		var q: = p + Vector3(rng.randf_range(-0.5, 0.5), h, back + rng.randf_range(-0.08, 0.14) * front)
		if i % 3 == 0:
			_bloom(q, 0.0, Color(0.2, 0.5, 0.2).lerp(Color(0.32, 0.62, 0.25), rng.randf()), rng.randf_range(0.75, 1.0))
		else:
			_bloom(q, 0.0, cols[i % cols.size()], rng.randf_range(0.5, 0.75))

func _finish_blooms() -> void :
	if _bloom_xf.is_empty():
		return
	# v0.7.3: flores em bolinhas 3D (antes eram cartões chapados que pareciam manchas flutuando)
	var ball: = SphereMesh.new()
	ball.radius = 0.2
	ball.height = 0.34
	ball.radial_segments = 16
	ball.rings = 8
	var mm: = MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	mm.mesh = ball
	mm.instance_count = _bloom_xf.size()
	for i in _bloom_xf.size():
		mm.set_instance_transform(i, _bloom_xf[i])
		mm.set_instance_color(i, _bloom_col[i])
	var mi: = MultiMeshInstance3D.new()
	mi.multimesh = mm
	var mat: = StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo = true
	mat.vertex_color_is_srgb = true
	mat.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
	mat.specular_mode = BaseMaterial3D.SPECULAR_TOON
	mat.roughness = 0.8
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
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

	for spot in [[Vector3(58.5, 0.1, 25.85), 0.0], [Vector3(86.0, 0.1, 25.85), 0.0], [Vector3(50.0, 0.1, 34.55), PI], [Vector3(93.0, 0.1, 34.55), PI]]:
		B.model(self, "painted_wooden_bench", spot[0], spot[1], 1.0)
		bench_spots.append({"pos": spot[0] + Vector3(0, 0.05, 0), "rot": spot[1], "anim": "Sitting_Idle_Loop", "busy": false})

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
		B.box(piv, Vector3(1.36, 2.95, 0.1), Vector3(0, 1.47, 0), VM.trim)
		B.box(piv, Vector3(1.05, 2.2, 0.1), Vector3(0, 1.1, 0.03), leaf_m)
		for py in [0.55, 1.15, 1.75]:
			for px in [-0.24, 0.24]:
				B.box(piv, Vector3(0.36, 0.42, 0.04), Vector3(px, py, 0.09), dark)
				B.box(piv, Vector3(0.28, 0.34, 0.04), Vector3(px, py, 0.11), leaf_m)
		B.sphere(piv, 0.04, Vector3(0.38, 1.05, 0.14), B.flat(Color(0.95, 0.78, 0.3), 0.25, 0.6))
		B.box(piv, Vector3(1.05, 0.45, 0.06), Vector3(0, 2.48, 0.02), VM.glass)
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
		# numero da casa e luminária de parede
		var num: = absi(int(c.x * 3.0 + c.z)) % 300 + 1
		B.box(piv, Vector3(0.24, 0.18, 0.03), Vector3(-0.9, 1.9, 0.04), B.flat(Color(0.15, 0.4, 0.75), 0.4))
		var nl: = B.label(piv, str(num), Vector3(-0.9, 1.9, 0.062), 32, Color.WHITE, Color(0.1, 0.25, 0.5, 1))
		nl.pixel_size = 0.004
		B.box(piv, Vector3(0.08, 0.08, 0.2), Vector3(0.9, 2.55, 0.1), dark)
		B.cyl(piv, 0.09, 0.07, 0.22, Vector3(0.9, 2.45, 0.22), VM.glass, 10)
		B.cyl(piv, 0.11, 0.02, 0.08, Vector3(0.9, 2.6, 0.22), dark, 10)
	else:
		B.box(piv, Vector3(1.4, 1.65, 0.1), Vector3(0, 1.75, 0), VM.trim)
		B.box(piv, Vector3(1.1, 1.35, 0.06), Vector3(0, 1.75, 0.01), VM.glass)
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
func _house_extras(c: Vector3, w: float, d: float, h: float, front: float, col: Color, shutter: Color) -> void :
	var rng: = RandomNumberGenerator.new()
	rng.seed = int(c.x * 17.0 + c.z * 5.0)
	B.box(self, Vector3(w + 0.06, 0.26, d + 0.06), c + Vector3(0, h - 0.45, 0), stucco(shutter.lightened(0.45)))
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
	var gm: = B.flat(Color(0.88, 0.88, 0.85), 0.5, 0.3)
	var gut: = B.cyl(self, 0.06, 0.06, w + 1.7, Vector3(c.x, h + 0.02, gz), gm, 12)
	gut.rotation.z = PI * 0.5
	B.cyl(self, 0.045, 0.045, h, Vector3(c.x + w * 0.5 + 0.8, h * 0.5, gz), gm, 10)
	if rng.randf() < 0.45:
		var chx: = c.x + rng.randf_range(- w * 0.25, w * 0.25)
		B.box(self, Vector3(0.6, 1.4, 0.6), Vector3(chx, h + 1.6, c.z - front * d * 0.18), stucco(col.darkened(0.15)))
		B.box(self, Vector3(0.75, 0.12, 0.75), Vector3(chx, h + 2.35, c.z - front * d * 0.18), VM.trim)
	if rng.randf() < 0.3:
		var ax: = c.x - w * 0.3
		var az: = c.z
		B.cyl(self, 0.02, 0.02, 1.6, Vector3(ax, h + 2.4, az), gm, 6)
		for j in 4:
			var bar: = B.box(self, Vector3(0.9 - j * 0.15, 0.02, 0.02), Vector3(ax, h + 2.8 + j * 0.15, az), gm)
			bar.rotation.y = 0.3
	if rng.randf() < 0.35:
		var side: = 1.0 if rng.randf() < 0.5 else -1.0
		B.box(self, Vector3(0.28, 0.5, 0.75), Vector3(c.x + side * (w * 0.5 + 0.16), 2.4, c.z), B.flat(Color(0.95, 0.95, 0.95), 0.5))
		var grille: = B.cyl(self, 0.2, 0.2, 0.03, Vector3(c.x + side * (w * 0.5 + 0.31), 2.4, c.z), B.flat(Color(0.3, 0.3, 0.32), 0.5), 16)
		grille.rotation.z = PI * 0.5
	# relógio de luz ao lado da porta
	B.box(self, Vector3(0.35, 0.45, 0.14), c + Vector3(- w * 0.42 * front, 1.5, front * (d * 0.5 + 0.08)), B.flat(Color(0.75, 0.78, 0.8), 0.5))
	# vaso pendurado
	if rng.randf() < 0.5:
		var vp: = c + Vector3(w * 0.1 * front, 2.6, front * (d * 0.5 + 0.35))
		B.cyl(self, 0.012, 0.012, h - 2.6, vp + Vector3(0, (h - 2.6) * 0.5, 0), B.flat(Color(0.3, 0.25, 0.2)), 8)
		for sx in [-1.0, 1.0]:
			var cord: = B.cyl(self, 0.008, 0.008, 0.26, vp + Vector3(sx * 0.07, 0.12, 0), B.flat(Color(0.3, 0.25, 0.2)), 6)
			cord.rotation.z = sx * 0.5
		B.cyl(self, 0.14, 0.1, 0.18, vp, B.flat(Color(0.85, 0.45, 0.3), 0.8), 14)
		for j in 5:
			var lf: = B.sphere(self, 0.07, vp + Vector3(cos(j) * 0.12, -0.05 - (j % 2) * 0.12, sin(j) * 0.12), B.flat(Color(0.3, 0.72, 0.3)))
			lf.scale = Vector3(1, 1.5, 1)

func _house(c: Vector3, w: float, d: float, front: float, col: Color, shutter: Color, porch: bool, sign_text: = "") -> void :
	var h: = 3.5
	var body: = B.box(self, Vector3(w, h, d), c + Vector3(0, h * 0.5, 0), stucco(col), true)
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
	B.hip_roof(self, c + Vector3(0, h + 0.05, 0), w + 1.75, d + 1.75, 2.05, VM.clay, 0.14)
	_house_extras(c, w, d, h, front, col, shutter)
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
			B.cyl(self, 0.09, 0.1, 2.6, Vector3(c.x + sx * (w * 0.5 - 0.6), 1.3, pz + front * 0.6), VM.trim, 10)
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
	var col: = Color(0.55, 0.8, 0.88)
	var y0: = 0.12
	B.platform(self, Vector3(w + 0.4, 0.24, d + 0.4), c, VM.floor, 0.4)
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

	B.box(self, Vector3(1.35, 1.22, 0.04), Vector3(c.x - 1.7, y0 + 1.65, zf), VM.glass)
	B.box(self, Vector3(2.15, 1.4, 0.04), Vector3(c.x - 1.4, y0 + 1.6, zb), VM.glass)
	B.box(self, Vector3(0.04, 1.22, 1.15), Vector3(x0, y0 + 1.65, c.z), VM.glass)
	B.label(self, "Casa", Vector3(c.x + 1.7, y0 + 2.75, zf + 0.2), 44, Color(1, 1, 1), Color(0.1, 0.25, 0.35, 0.9))

	var door: = B.box(self, Vector3(0.06, 2.2, 1.15), Vector3(c.x + 2.35, y0 + 1.1, zf - 0.55), wood_tint(Color(0.1, 0.45, 0.55)))
	door.name = "door"

	var bc: = Vector3(c.x - 2.15, y0, zb + 1.55)
	var gothic: = B.model(self, "GothicBed_01", bc + Vector3(0.15, 0, 0.55), PI, 1.0)
	gothic.scale = Vector3(0.95, 1.0, 0.92)
	B.model(self, "throw_pillows_01", bc + Vector3(0.05, 0.5, -0.15), 0.0, 0.7)
	B.model(self, "painted_wooden_nightstand", bc + Vector3(1.15, 0, -0.15), PI * 0.5, 0.95)
	B.model(self, "vintage_oil_lamp", bc + Vector3(1.15, 0.65, -0.27), 0.4, 0.9)
	B.model(self, "Shelf_01", Vector3(x0 + 0.85, y0, c.z + 0.2), PI * 0.5, 0.9)
	B.model(self, "hanging_picture_frame_02", Vector3(bc.x, y0 + 1.7, zb + 0.12), 0.0, 0.85)
	B.model(self, "ceramic_vase_02", bc + Vector3(1.15, 0.65, 0.02), 0.2, 0.5)
	bed = Interactable.new()
	var cs: = CollisionShape3D.new()
	var sh: = BoxShape3D.new()
	sh.size = Vector3(1.7, 1.0, 2.3)
	cs.shape = sh
	bed.add_child(cs)
	bed.position = bc + Vector3(0, 0.6, 0.4)
	bed.name = "Bed"
	add_child(bed)
	B.model(self, "painted_wooden_cabinet", Vector3(x0 + 0.42, y0, c.z + 1.7), PI * 0.5, 1.0)
	B.model(self, "Rockingchair_01", Vector3(c.x - 0.15, y0, c.z + 1.35), 0.5, 0.85)
	B.model(self, "pachira_aquatica_01", Vector3(x0 + 0.55, y0, zb + 0.55), 0.3, 0.85)
	B.model(self, "electric_stove", Vector3(x1 - 0.5, y0, zb + 1.0), - PI * 0.5, 1.0)
	var fan_root: = Node3D.new()
	fan_root.position = Vector3(c.x, y0 + h - 0.02, c.z)
	add_child(fan_root)
	B.model(fan_root, "ceiling_fan", Vector3.ZERO, 0.2, 0.72)
	B.box(self, Vector3(0.65, 0.9, 2.2), Vector3(x1 - 0.45, y0 + 0.45, zb + 2.7), M.oak, true)
	B.box(self, Vector3(0.7, 0.05, 2.3), Vector3(x1 - 0.45, y0 + 0.92, zb + 2.7), VM.curb)
	B.box(self, Vector3(0.45, 0.04, 0.4), Vector3(x1 - 0.45, y0 + 0.95, zb + 3.2), B.flat(Color(0.75, 0.78, 0.8), 0.25, 0.8))
	B.box(self, Vector3(0.3, 0.6, 1.8), Vector3(x1 - 0.2, y0 + 1.9, zb + 2.7), M.oak)
	B.model(self, "WoodenTable_01", Vector3(c.x + 0.6, y0, c.z + 0.6), 0.0, 1.0)
	B.model(self, "wooden_stool_01", Vector3(c.x + 0.6, y0, c.z + 1.25), 0.3, 1.0)
	B.model(self, "wooden_stool_01", Vector3(c.x + 0.6, y0, c.z - 0.05), 1.1, 1.0)
	B.model(self, "wooden_bowl_01" if B.has_model("wooden_bowl_01") else "wicker_basket_01", Vector3(c.x + 0.6, y0 + 0.78, c.z + 0.6), 0.0, 1.0)
	B.box(self, Vector3(2.2, 0.015, 1.5), Vector3(c.x - 0.9, y0 + 0.01, c.z + 0.4), B.mat("rough_linen", 1.5, Color(0.2, 0.5, 0.6), 0.95))
	B.model(self, "potted_plant_04", Vector3(x0 + 0.5, y0, zb + 0.5), 0.0, 0.9)
	B.model(self, "planter_box_01", Vector3(c.x - 1.7, 0.0, zf + 0.9), 0.0, 1.0)
	var l: = OmniLight3D.new()
	l.position = Vector3(c.x, y0 + 2.8, c.z)
	l.omni_range = 7.0
	l.light_color = Color(1.0, 0.82, 0.6)
	add_child(l)
	l.shadow_enabled = Quality.hd
	lanterns.append([l, null, 2.2, true])
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
		B.box(self, Vector3(1.1, 1.8, 0.1), tc + n * 1.62 + Vector3(0, 11.0, 0), VM.glass, false, atan2(n.x, n.z))
	B.hip_roof(self, tc + Vector3(0, 13.0, 0), 3.8, 3.8, 3.0, VM.clay, 0.12)
	B.box(self, Vector3(0.14, 1.6, 0.14), tc + Vector3(0, 16.7, 0), B.flat(Color(0.9, 0.85, 0.6), 0.3, 0.7))
	B.box(self, Vector3(0.8, 0.14, 0.14), tc + Vector3(0, 17.1, 0), B.flat(Color(0.9, 0.85, 0.6), 0.3, 0.7))
	B.label(self, "Igreja de São Pedro", c + Vector3(0, h - 0.6, - d * 0.5 - 0.1), 60, Color(0.15, 0.3, 0.55), Color(1, 1, 1, 0.9), PI)
	village_points.church_bell = tc + Vector3(0, 11, 0)

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
		B.model(self, "painted_wooden_bench", bp, face, 1.0)
		bench_spots.append({"pos": bp + Vector3(0, 0.08, 0), "rot": face, "anim": "Sitting_Idle_Loop", "busy": false})
	for corner in [Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]:
		B.model(self, "planter_box_01", pc + Vector3(corner.x * (r.size.x * 0.5 - 0.8), 0.1, corner.y * (r.size.y * 0.5 - 0.7)), 0.0, 1.0)

	B.model(self, "CoffeeCart_01", pc + Vector3(-7.2, 0.1, 3.0), 2.4, 1.0)
	village_points.cart = pc + Vector3(-6.0, 0.1, 3.2)


func _quiosque() -> void :
	var c: = KIOSK_C
	# v0.7.1: ninguém atravessa o quiosque — área bloqueada para os moradores (os bancos da frente ficam fora)
	block_rects.append(Rect2(c.x - 2.95, c.z - 3.05, 5.9, 5.35))
	block_rects.append(Rect2(c.x + 3.0, c.z - 2.2, 1.3, 3.6))
	block_rects.append(Rect2(c.x - 4.6, c.z - 3.4, 1.6, 3.6))
	B.platform(self, Vector3(5.6, 0.2, 5.6), c, M.deckwood, 0.45)
	var y0: = 0.1
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.cyl(self, 0.12, 0.15, 2.8, c + Vector3(sx * 2.4, y0 + 1.4, sz * 2.4), M.post, 8)
	B.hip_roof(self, c + Vector3(0, y0 + 2.8, 0), 6.6, 6.6, 2.8, M.thatch, 0.22)
	var ch: = 1.1
	var wood: Material = M.darkwood
	B.box(self, Vector3(4.6, ch, 0.6), c + Vector3(0, y0 + ch * 0.5, 2.0), wood, true)
	B.box(self, Vector3(0.6, ch, 3.4), c + Vector3(-2.0, y0 + ch * 0.5, 0.5), wood, true)
	B.box(self, Vector3(0.6, ch, 3.4), c + Vector3(2.0, y0 + ch * 0.5, 0.5), wood, true)
	B.box(self, Vector3(4.9, 0.08, 0.9), c + Vector3(0, y0 + ch + 0.04, 2.0), M.oak)
	_back_bar(c, y0)
	var cols: = [Color(0.15, 0.45, 0.22), Color(0.85, 0.88, 0.9), Color(0.55, 0.28, 0.1), Color(0.7, 0.1, 0.16)]
	for i in 8:
		B.cyl(self, 0.04, 0.045, 0.28, c + Vector3(-1.4 + i * 0.38, y0 + 1.35, -1.9), B.flat(cols[i % 4], 0.15, 0.05), 16)
	_fruit_row(c + Vector3(-1.5, y0 + ch + 0.14, 1.85))
	var snack_y: = y0 + ch + 0.1
	_coconut_cup(self, c + Vector3(-0.55, snack_y, 2.22))
	_petisco_plate(self, c + Vector3(0.5, snack_y, 2.22))
	var coco: = B.flat(Color(0.42, 0.52, 0.16), 0.6)
	for k in 5:
		B.sphere(self, 0.11, c + Vector3(0.35 + (k % 3) * 0.24, y0 + ch + 0.14, 2.05), coco)
	B.model(self, "wooden_bucket_01", c + Vector3(1.55, y0 + ch + 0.08, 1.9), 0.4, 0.65)
	_cooler(c + Vector3(1.3, y0 + 0.028, 0.3), 1.2)
	B.model(self, "plastic_crate_01", c + Vector3(-1.3, y0 + 0.028, -0.35), 0.2, 1.0)
	B.box(self, Vector3(3.6, 0.6, 0.08), c + Vector3(0, y0 + 2.5, 2.42), M.planks)
	B.label(self, "Quiosque Maré Alta", c + Vector3(0, y0 + 2.5, 2.48), 64, Color(1.0, 0.95, 0.8), Color(0.25, 0.12, 0.02, 1.0))
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
	hut_details(c, 2.4, y0, 2.8, 2.8, 3.3)
	_area("drinks", func(): _kiosk_drinks(c, y0))
	_area("neon", func(): _kiosk_neon(c, y0))
	_area("grill", func(): _kiosk_grill(c, y0))
	kiosk_counter = Interactable.new()
	var cs: = CollisionShape3D.new()
	var sh: = BoxShape3D.new()
	sh.size = Vector3(4.6, 1.5, 1.4)
	cs.shape = sh
	kiosk_counter.add_child(cs)
	kiosk_counter.position = c + Vector3(0, y0 + 0.9, 2.0)
	kiosk_counter.name = "KioskCounter"
	add_child(kiosk_counter)
	for k in 2:
		var p: = c + Vector3(-0.7 + k * 1.4, y0, 2.85)
		B.model(self, "bar_chair_round_01", p, PI, 1.0)
		kiosk_spots.insert(k, {"pos": p + Vector3(0, 0.28, 0), "rot": PI, "busy": false, "need": ""})
	village_points.kiosk_work = c + Vector3(0, 0.1, 0.8)
	var l: = OmniLight3D.new()
	l.position = c + Vector3(0, 2.5, 0)
	l.omni_range = 6.5
	l.light_color = Color(1.0, 0.75, 0.45)
	add_child(l)
	lanterns.append([l, null, 1.6, false])


## Mesa com duas cadeiras (dois lugares de cliente) e, opcionalmente, guarda-sol.
func _kiosk_table(tp: Vector3, need: String, umb: Color, umbrella: bool) -> void :
	B.model(self, "outdoor_table_chair_set_01", tp, 0.0, 1.0)
	if umbrella:
		_umbrella(tp, 1.45, umb, false)
	_table_bites(tp + Vector3(0, 0.78, 0))
	# cardapinho em pé na mesa
	var menu: = B.box(self, Vector3(0.16, 0.22, 0.02), tp + Vector3(0, 0.9, 0), B.flat(Color(1.0, 0.45, 0.35), 0.8))
	menu.rotation.x = -0.2
	for sx in [-1.0, 1.0]:
		var seat: = tp + Vector3(sx * 0.85, 0, 0)
		kiosk_spots.append({"pos": seat + Vector3(0, 0.02, 0), "rot": - sx * PI * 0.5, "busy": false, "need": need, "anim": "Sitting_Idle_Loop", "table": true})
	# mesa + cadeiras bloqueadas: pedestres contornam o conjunto todo (quem vai sentar entra)
	_block(tp, 2.5, 1.0, 0.12)

## Quadro-negro do quiosque: mostra só os pratos liberados.
func _refresh_kiosk_board() -> void :
	if _kiosk_board == null:
		return
	for ch in _kiosk_board.get_children():
		ch.queue_free()
	var c: = _kiosk_menu_c
	var before: = get_child_count()
	_chalkboard(c + Vector3(2.35, 0.1 + 1.15, 0.9), PI * 0.5, "HOJE", _menu_lines(Core.kiosk_menu()))
	for k in get_children().slice(before):
		k.reparent(_kiosk_board, false)

func on_areas_changed() -> void :
	_refresh_kiosk_board()

## Letreiro neon (expansão "neon"): tubos coloridos que brilham, mais cordões de luz.
func _kiosk_neon(c: Vector3, y0: float) -> void :
	_string_lights(c + Vector3(-2.3, y0 + 2.45, 2.3), c + Vector3(2.3, y0 + 2.45, 2.3), 8)
	_string_lights(c + Vector3(-2.3, y0 + 2.45, -2.3), c + Vector3(-2.3, y0 + 2.45, 2.3), 6)
	_string_lights(c + Vector3(2.3, y0 + 2.45, -2.3), c + Vector3(2.3, y0 + 2.45, 2.3), 6)
	var pink: = P.glow(Color(1.0, 0.25, 0.65), 4.0)
	var cyan: = P.glow(Color(0.2, 0.95, 1.0), 4.0)
	var back: = B.box(self, Vector3(3.4, 0.9, 0.08), c + Vector3(0, y0 + 3.55, 2.5), B.flat(Color(0.12, 0.1, 0.16), 0.6))
	back.rotation.x = -0.12
	var l: = B.label(self, "MARÉ ALTA", c + Vector3(0, y0 + 3.62, 2.58), 120, Color(1.0, 0.45, 0.8), Color(1.0, 0.2, 0.6, 0.9))
	l.rotation.x = -0.12
	l.shaded = false
	l.outline_size = 18
	for sx in [-1.0, 1.0]:
		B.box(self, Vector3(0.06, 0.7, 0.06), c + Vector3(sx * 1.6, y0 + 3.55, 2.56), cyan)
	B.box(self, Vector3(3.2, 0.05, 0.05), c + Vector3(0, y0 + 3.15, 2.6), cyan)
	B.box(self, Vector3(1.6, 0.04, 0.04), c + Vector3(0, y0 + 3.98, 2.5), pink)
	var nl: = OmniLight3D.new()
	nl.position = c + Vector3(0, y0 + 3.3, 3.2)
	nl.light_color = Color(1.0, 0.4, 0.75)
	nl.omni_range = 7.0
	nl.light_energy = 0.0
	add_child(nl)
	lanterns.append([nl, null, 2.2, false])

## Chapa de petiscos (expansão "grill"): fogão, panela e pratos de peixe frito.
func _kiosk_grill(c: Vector3, y0: float) -> void :
	B.model(self, "electric_stove", c + Vector3(1.3, y0, -1.3), 0.0, 0.9)
	var pan: = B.cyl(self, 0.18, 0.15, 0.06, c + Vector3(1.1, y0 + 0.86, -1.2), B.flat(Color(0.15, 0.15, 0.17), 0.4), 14)
	pan.name = "Pan"
	for k in 3:
		B.sphere(self, 0.06, c + Vector3(1.04 + k * 0.06, y0 + 0.9, -1.2), B.flat(Color(0.95, 0.65, 0.25)), Vector3(1.6, 0.6, 1.0))
	_petisco_plate(self, c + Vector3(-1.2, y0 + 1.2, 2.22))
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
	var qm: = SphereMesh.new()
	qm.radius = 0.08
	qm.height = 0.16
	qm.radial_segments = 6
	qm.rings = 3
	var sm: = StandardMaterial3D.new()
	sm.albedo_color = Color(1, 1, 1, 0.35)
	sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qm.material = sm
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
	quest_board = Interactable.new()
	quest_board.name = "DonaRita"
	var qcs: = CollisionShape3D.new()
	var qsh: = BoxShape3D.new()
	qsh.size = Vector3(1.4, 1.8, 1.2)
	qcs.shape = qsh
	quest_board.add_child(qcs)
	quest_board.position = c + Vector3(-1.6, 1.0, 0.4)
	quest_board.prompt_fn = func() -> String:
		var st: = str(Core.quests.get("cocos_rita", ""))
		if st == "done":
			return ""
		if st == "":
			return tr("Dona Rita: aceitar encomenda de cocos")
		return tr("Dona Rita: entregar cocos")
	quest_board.action_fn = func() -> void :
		if str(Core.quests.get("cocos_rita", "")) == "":
			Core.accept_quest("cocos_rita")
		else:
			Core.complete_quest("cocos_rita")
	add_child(quest_board)

func _umbrella_hd(p: Vector3, r: float) -> void :
	_umbrella(p, r)


func _bike(p: Vector3, rot: float, col: Color) -> void :
	var n: = Node3D.new()
	n.position = p
	n.rotation = Vector3(0, rot, 0.18)
	add_child(n)
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

func _fishing_boat(p: Vector3, rot: float, paint: Color) -> void :
	var j: = Node3D.new()
	j.position = p
	j.rotation.y = rot
	add_child(j)
	var hull: = MeshInstance3D.new()
	hull.mesh = _boat_mesh()
	var hm: = wood_tint(paint).duplicate() as StandardMaterial3D
	hm.cull_mode = BaseMaterial3D.CULL_DISABLED
	hull.material_override = hm
	j.add_child(hull)
	var trim: = wood_tint(Color(0.93, 0.9, 0.82))
	B.box(j, Vector3(1.15, 0.06, 0.28), Vector3(0, 0.42, 0.2), trim)
	B.box(j, Vector3(0.9, 0.06, 0.22), Vector3(0, 0.4, -0.85), trim)
	B.model(j, "wooden_crate_01", Vector3(-0.15, 0.48, 1.15), 0.2, 0.55)
	B.model(j, "wooden_bucket_01", Vector3(0.28, 0.42, 0.55), 0.5, 0.45)
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
	B.wall(self, Vector3(1.7, 0.7, 4.6), p + Vector3(0, 0.35, 0.1), rot)

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
	var boats: = [[Vector3(58.5, 0, -27.2), 0.35, Color(0.2, 0.45, 0.62)], [Vector3(74.0, 0, -26.6), -0.4, Color(0.72, 0.22, 0.16)], [Vector3(88.5, 0, -27.4), 0.15, Color(0.85, 0.72, 0.28)]]
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
			B.model(self, ["shrub_01", "shrub_02", "shrub_03"][k % 3], Vector3(sp.x, 0, sp.y), k * 1.3, 0.9)

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
		placed += 1

	Palm.spawn(self, Vector3(33.2, _height(33.2, -9.5) - 0.05, -9.5), 4242)

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
		var glow: = MeshInstance3D.new()
		var sm: = SphereMesh.new()
		sm.radius = 0.22
		sm.height = 0.44
		glow.mesh = sm
		var gm: = StandardMaterial3D.new()
		gm.albedo_color = Color(1, 0.86, 0.55)
		gm.emission_enabled = true
		gm.emission = Color(1.0, 0.72, 0.32)
		gm.emission_energy_multiplier = 0.0
		gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		glow.material_override = gm
		glow.position = p + Vector3(0, top, 0)
		glow.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(glow)
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
	village_points.kiosk_approach = [Vector3(38, 0.15, zn), Vector3(38, 0.05, 5.0), Vector3(38, 0.05, -8.0)]
	village_points.home_route = [village_points.home_door_out, Vector3(HOME_C.x + 1.7, 0.15, zn)]

func set_night(t: float) -> void :
	super.set_night(t)
	_night = t
	if _lighthouse:
		var beam: = _lighthouse.get_node_or_null("Beam")
		if beam:
			beam.visible = t > 0.3
		for ch in _lighthouse.get_children():
			if ch is SpotLight3D:
				ch.light_energy = 6.0 * t
	if VM.has("glass"):
		var glass: StandardMaterial3D = VM.glass
		glass.emission_energy_multiplier = 7.0 * t
		glass.albedo_color = Color(0.62, 0.78, 0.88, 0.7).lerp(Color(1.0, 0.7, 0.35, 0.95), t)


# ------------------------------------------------------------------ v0.7.1: quiosque cheio de detalhes
func _kiosk_details(c: Vector3, y0: float) -> void :
	var thatch_c: = Color(0.96, 0.75, 0.38)
	D.thatch_fringe(self, c, 3.32, y0 + 2.86, thatch_c, 0.26)
	for pair in [[Vector3(-3.1, 0, 3.1), Vector3(3.1, 0, 3.1)], [Vector3(3.1, 0, -3.1), Vector3(3.1, 0, 3.1)], [Vector3(-3.1, 0, -3.1), Vector3(-3.1, 0, 3.1)]]:
		D.bunting(self, c + pair[0] + Vector3(0, y0 + 2.3, 0), c + pair[1] + Vector3(0, y0 + 2.3, 0), 0.25, 0.42)
	# frutas penduradas nas vigas
	D.bananas(self, c + Vector3(-1.7, y0 + 2.35, 1.7))
	D.bananas(self, c + Vector3(1.75, y0 + 2.35, -1.6))
	for k in 3:
		var cc: = c + Vector3(-0.6 + k * 0.6, y0 + 2.45, -2.25)
		B.cyl(self, 0.014, 0.014, 0.62, cc + Vector3(0, 0.05, 0), D.m(Color(0.45, 0.3, 0.16)), 8)
		B.sphere(self, 0.13, cc + Vector3(0, -0.4, 0), D.m(Color(0.45, 0.68, 0.22), 0.6), Vector3(1, 1.1, 1))
	# balcão
	var top: = c + Vector3(0, y0 + 1.18, 2.0)
	D.tip_jar(self, top + Vector3(1.6, 0, 0.15))
	D.straw_cup(self, top + Vector3(1.25, 0, 0.1))
	D.cup_stack(self, top + Vector3(-1.95, 0, 0.0), Color(1.0, 0.9, 0.3))
	D.cup_stack(self, top + Vector3(-1.75, 0, 0.12), Color(0.3, 0.8, 1.0))
	D.blender(self, top + Vector3(-1.2, 0, -0.15))
	D.pineapple(self, top + Vector3(1.95, 0, -0.1))
	B.box(self, Vector3(0.14, 0.12, 0.08), top + Vector3(-0.15, 0.06, 0.2), D.m(Color(0.95, 0.95, 0.98)))
	D.radio(self, c + Vector3(-1.1, y0 + 1.79, -1.9), 0.0)
	# frente do balcão: bambu e cocos cortados
	for k in 15:
		B.cyl(self, 0.05, 0.05, 1.0, c + Vector3(-2.2 + k * 0.315, y0 + 0.52, 2.33), D.m(Color(0.9, 0.76, 0.42)), 6)
	for k in 3:
		var half: = B.sphere(self, 0.12, c + Vector3(-1.3 + k * 1.3, y0 + 0.75, 2.4), D.m(Color(0.55, 0.36, 0.2)), Vector3(1, 1, 0.45))
		B.sphere(half, 0.1, Vector3(0, 0, 0.05), D.m(Color(0.98, 0.96, 0.9)), Vector3(1, 1, 0.4))
	_open_sign = D.open_sign(self, c + Vector3(1.65, y0 + 2.3, 2.5), 0.0)
	# em volta
	D.coconut_pile(self, c + Vector3(3.7, 0.05, 0.8), 10)
	D.coconut_pile(self, c + Vector3(3.4, 0.05, -1.6), 6)
	var cart: = Node3D.new()
	cart.position = c + Vector3(-3.9, 0.05, -0.4)
	cart.rotation.y = 0.5
	add_child(cart)
	B.box(cart, Vector3(0.7, 0.35, 1.0), Vector3(0, 0.45, 0), D.m(Color(0.25, 0.55, 0.85)))
	var wheel: = B.cyl(cart, 0.18, 0.18, 0.08, Vector3(0, 0.18, 0.62), D.m(Color(0.2, 0.2, 0.22)), 12)
	wheel.rotation.z = PI * 0.5
	for sx in [-1.0, 1.0]:
		B.box(cart, Vector3(0.05, 0.05, 0.9), Vector3(sx * 0.25, 0.55, -0.75), D.m(Color(0.6, 0.45, 0.3)))
	D.coconut_pile(cart, Vector3(0, 0.55, 0), 5)
	_surf_rack(c + Vector3(-1.2, 0.0, -3.35))
	D.trash_bin(self, c + Vector3(3.1, 0.05, 2.8))
	D.trash_bin(self, c + Vector3(3.6, 0.05, 2.8), Color(0.2, 0.55, 0.9))
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
	# prateleira de baixo: potes, caixas e garrafas grandes
	var cols: = [Color(1.0, 0.45, 0.35), Color(1.0, 0.82, 0.25), Color(0.1, 0.72, 0.72), Color(0.3, 0.75, 0.3), Color(0.99, 0.94, 0.82)]
	for i in 9:
		var px: = -1.7 + i * 0.42
		if i % 3 == 0:
			B.box(self, Vector3(0.3, 0.22, 0.24), Vector3(c.x + px, c.y + y0 + 0.73, z), D.m(cols[i % 5]))
		else:
			B.cyl(self, 0.08, 0.09, 0.26, Vector3(c.x + px, c.y + y0 + 0.75, z), D.m(cols[i % 5], 0.4), 16)
			B.cyl(self, 0.085, 0.085, 0.04, Vector3(c.x + px, c.y + y0 + 0.9, z), D.m(cols[(i + 2) % 5].darkened(0.2), 0.4), 16)
	for i in 6:
		B.cyl(self, 0.035, 0.04, 0.2, Vector3(c.x - 0.3 + i * 0.13, c.y + y0 + 0.07, z + 0.05), D.m(cols[i % 5], 0.3), 12)

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
	var top: = c + Vector3(0, y0 + 1.18, 2.0)
	for k in 3:
		var g: = top + Vector3(0.45 + k * 0.22, 0, 0.18)
		B.cyl(self, 0.04, 0.025, 0.1, g + Vector3(0, 0.05, 0), D.m(Color(0.9, 1.0, 0.75, 0.75), 0.1), 10)
		B.cyl(self, 0.002, 0.002, 0.12, g + Vector3(0.02, 0.14, 0), D.m(Color(0.4, 0.3, 0.2)), 4)
		B.cyl(self, 0.0, 0.05, 0.03, g + Vector3(0.02, 0.2, 0), D.m(D.FLAG_COLS[k * 2 % D.FLAG_COLS.size()]), 8)
	var crate_p: = c + Vector3(-1.4, y0 + 0.028, -0.9)
	B.box(self, Vector3(0.5, 0.25, 0.35), crate_p + Vector3(0, 0.125, 0), D.m(Color(0.85, 0.65, 0.4)))
	for k in 8:
		B.sphere(self, 0.04, crate_p + Vector3(-0.18 + (k % 4) * 0.12, 0.27, -0.08 + (k / 4) * 0.14), D.m(Color(0.45, 0.85, 0.25), 0.5))
	for k in 4:
		B.cyl(self, 0.045, 0.05, 0.32, c + Vector3(0.3 + k * 0.2, y0 + 1.95, -1.9), D.m(Color(0.95, 0.95, 0.9, 0.8), 0.15), 16)
	var sign_p: = c + Vector3(-2.38, y0 + 1.75, 0.9)
	B.box(self, Vector3(0.06, 0.5, 1.1), sign_p, D.m(Color(0.25, 0.65, 0.35)))
	var l: = B.label(self, "CAIPIRINHA", sign_p + Vector3(-0.04, 0.08, 0), 40, Color.WHITE, Color(0.1, 0.3, 0.15), - PI * 0.5)
	l.pixel_size = 0.0035
	var l2: = B.label(self, Core.fmt_money(int(Economy.dish("caipirinha").price)), sign_p + Vector3(-0.04, -0.12, 0), 48, Color(1.0, 0.95, 0.4), Color(0.1, 0.3, 0.15), - PI * 0.5)
	l2.pixel_size = 0.0035

func _on_time(_d: int, _m: float) -> void :
	if _open_sign:
		var open: bool = Core.minutes >= 8.0 * 60.0 and Core.minutes < Core.kiosk_close_min()
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

func _add_lamp(p: Vector3) -> void :
	B.model(self, "street_lamp_01", p, 0.0, 1.0)
	var glow: = MeshInstance3D.new()
	var sm: = SphereMesh.new()
	sm.radius = 0.22
	sm.height = 0.44
	glow.mesh = sm
	var gm: = StandardMaterial3D.new()
	gm.albedo_color = Color(1, 0.86, 0.55)
	gm.emission_enabled = true
	gm.emission = Color(1.0, 0.72, 0.32)
	gm.emission_energy_multiplier = 0.0
	gm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	glow.material_override = gm
	glow.position = p + Vector3(0, 3.5, 0)
	add_child(glow)
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
	for sx in [-1.0, 1.0]:
		B.cyl(self, 0.08, 0.08, 3.6, feira_c + Vector3(sx * 11.6, 1.8, -2.6), D.m(Color(0.6, 0.42, 0.25)), 8)
	D.bunting(self, feira_c + Vector3(-11.6, 3.3, -2.6), feira_c + Vector3(11.6, 3.3, -2.6), 0.6, 0.5)
	# bandeirinhas atravessando as ruas
	var bx: = 46.0
	while bx < 100.0:
		D.bunting(self, Vector3(bx, 4.6, STREET_Z - 3.6), Vector3(bx + 4.0, 4.6, STREET_Z + 3.6), 0.7)
		bx += 9.0
	bx = 4.0
	while bx < 104.0:
		D.bunting(self, Vector3(bx, 4.4, BACK_Z - 3.6), Vector3(bx + 3.0, 4.4, BACK_Z + 3.6), 0.6)
		bx += 12.0
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
	D.cat(self, Vector3(20.5, 0.3, 25.2), 0.4, Color(0.95, 0.6, 0.25))
	D.cat(self, Vector3(62.0, 0.3, 26.0), -1.2, Color(0.2, 0.2, 0.22))
	D.cat(self, Vector3(42.0, 0.3, BACK_Z - 2.6), 2.0, Color(0.95, 0.95, 0.92))
	D.dog(self, Vector3(66.0, 0.15, 33.6), 1.4, Color(0.75, 0.55, 0.32))
	D.dog(self, Vector3(30.0, 0.15, BACK_Z + 2.8), -0.6, Color(0.95, 0.9, 0.82))
	for k in 4:
		var bp: = Vector3(16.0 + k * 22.0, 0.1, BACK_Z + 2.4)
		B.model(self, "painted_wooden_bench", bp, PI, 1.0)
		bench_spots.append({"pos": bp + Vector3(0, 0.05, 0), "rot": PI, "anim": "Sitting_Idle_Loop", "busy": false})
	for k in 6:
		_bike(Vector3(14.0 + k * 15.0, 0.15, BACK_Z - 2.6), PI * 0.5, D.FLAG_COLS[k % D.FLAG_COLS.size()])
	# píer e farol
	D.pier(self, Vector3(PIER_X, -0.25, -22.0), 27.0, 2.6)
	var ramp: = B.wall(self, Vector3(2.6, 0.2, 2.2), Vector3(PIER_X, 0.12, -21.6))
	ramp.rotation.x = 0.12
	for sx in [-1.0, 1.0]:
		B.wall(self, Vector3(0.2, 3.0, 28.0), Vector3(PIER_X + sx * 1.35, 1.6, -36.0))
	B.wall(self, Vector3(5.0, 3.0, 0.2), Vector3(PIER_X, 1.6, -50.7))
	for sx in [-1.0, 1.0]:
		B.wall(self, Vector3(0.2, 3.0, 3.2), Vector3(PIER_X + sx * 2.5, 1.6, -48.6))
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
	var spots: = [Vector3(28, 0, -21.5), Vector3(47, 0, -22.5), Vector3(22, 0, -24.0), Vector3(95, 0, -22.0), Vector3(-36, 0, -21.0)]
	for i in spots.size():
		var p: Vector3 = spots[i]
		p.y = _height(p.x, p.z)
		D.beach_spot(self, p, 50 + i)
	D.sand_castle(self, Vector3(33.0, _height(33, -24.5), -24.5))
	D.volley_net(self, Vector3(-30.0, 0.0, -20.0), 0.0)
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
		for k in 7:
			B.sphere(self, 0.13, bed + Vector3(-0.9 + k * 0.3, 0.42, (k % 2) * 0.2 - 0.1), B.flat(D.FLAG_COLS[(k + 2) % D.FLAG_COLS.size()], 0.7))
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
	B.box(self, Vector3(2.2, 2.2, 1.6), banca + Vector3(0, 1.1, 0), B.flat(Color(0.2, 0.55, 0.35), 0.6))
	var awn: = B.box(self, Vector3(2.6, 0.06, 0.9), banca + Vector3(0, 2.3, -1.1), B.flat(Color(1.0, 0.85, 0.2), 0.7))
	awn.rotation.x = 0.3
	for k in 12:
		B.box(self, Vector3(0.28, 0.36, 0.02), banca + Vector3(-0.85 + (k % 6) * 0.34, 0.9 + (k / 6) * 0.45, -0.81), B.flat(D.FLAG_COLS[k % D.FLAG_COLS.size()], 0.8))
	B.label(self, "BANCA", banca + Vector3(0, 2.0, -0.82), 48, Color(1, 1, 1), Color(0.1, 0.3, 0.15, 1), PI).pixel_size = 0.005
	var pip: = pc + Vector3(-6.0, 0, 2.9)
	B.box(self, Vector3(1.0, 0.9, 0.7), pip + Vector3(0, 0.75, 0), B.flat(Color(0.95, 0.25, 0.25), 0.5))
	B.box(self, Vector3(0.8, 0.6, 0.6), pip + Vector3(0, 1.5, 0), B.flat(Color(0.85, 0.95, 1.0, 0.6), 0.1))
	for k in 14:
		B.sphere(self, 0.06, pip + Vector3(-0.3 + (k % 5) * 0.15, 1.28 + (k / 5) * 0.08, -0.15 + (k % 3) * 0.12), B.flat(Color(1.0, 0.97, 0.85), 0.9))
	for sx in [-0.4, 0.4]:
		var wh: = B.cyl(self, 0.22, 0.22, 0.05, pip + Vector3(sx, 0.22, 0.38), B.flat(Color(0.2, 0.2, 0.22), 0.6), 16)
		wh.rotation.x = PI * 0.5
	B.cyl(self, 0.02, 0.02, 1.2, pip + Vector3(0, 2.4, 0), wood_tint(Color(0.5, 0.3, 0.2)), 6)
	B.cyl(self, 0.03, 0.75, 0.25, pip + Vector3(0, 3.0, 0), B.flat(Color(1.0, 0.95, 0.9), 0.7), 16)
	B.label(self, "PIPOCA", pip + Vector3(0, 0.75, -0.36), 40, Color.WHITE, Color(0.6, 0.1, 0.1, 1), PI).pixel_size = 0.005
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
		B.sphere(bird, 0.09, Vector3(0, 0.09, 0), B.flat(Color(0.6, 0.62, 0.7), 0.7), Vector3(0.8, 0.8, 1.3))
		B.sphere(bird, 0.05, Vector3(0, 0.18, 0.09), B.flat(Color(0.45, 0.5, 0.6), 0.7))
		B.cyl(bird, 0.0, 0.015, 0.04, Vector3(0, 0.18, 0.15), B.flat(Color(1.0, 0.65, 0.2), 0.5), 6).rotation.x = PI * 0.5
	# píer: postes com lanternas, caixotes e rolos de corda, barquinho amarrado
	var wood: = wood_tint(Color(0.45, 0.3, 0.2))
	for k in 4:
		var lz: = -24.0 - k * 7.5
		for sx in [-1.0, 1.0]:
			var lp2: = Vector3(PIER_X + sx * 1.25, 0.3, lz)
			B.cyl(self, 0.05, 0.06, 1.6, lp2 + Vector3(0, 0.8, 0), wood, 8)
			B.sphere(self, 0.12, lp2 + Vector3(0, 1.7, 0), P.glow(Color(1.0, 0.8, 0.45), 1.6))
	var end: = Vector3(PIER_X, 0.37, -47.0)
	for k in 3:
		B.model(self, "wooden_crate_01", end + Vector3(-1.9 + (k % 2) * 0.1, k * 0.0, 0.6 - k * 0.7), k * 0.4, 0.8)
	var coil: = TorusMesh.new()
	coil.inner_radius = 0.12
	coil.outer_radius = 0.3
	coil.rings = 24
	for k in 3:
		var mi: = MeshInstance3D.new()
		mi.mesh = coil
		mi.material_override = B.flat(Color(0.86, 0.74, 0.5), 0.95)
		mi.position = end + Vector3(1.8, 0.05 + k * 0.06, 0.9)
		add_child(mi)
	_fishing_boat(Vector3(PIER_X + 3.2, -0.25, -44.0), 0.1, Color(0.2, 0.6, 0.55))
	# farol: porta, janelinhas, balcão com gradil e casinha do faroleiro
	var fp: = Vector3(108.0, 0.0, -40.0)
	B.box(self, Vector3(0.9, 1.7, 0.2), fp + Vector3(0, 1.85, -1.55), B.flat(Color(0.25, 0.45, 0.8), 0.6))
	for k in 4:
		var a: = k * 1.7
		var r: = lerpf(1.6, 1.05, (3.0 + k * 2.6) / 14.0) + 0.02
		var win: = B.box(self, Vector3(0.35, 0.55, 0.12), fp + Vector3(sin(a) * r, 4.0 + k * 2.6, - cos(a) * r), VM.glass)
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
	# conchas e pedrinhas na areia (MultiMesh: milhares sem pesar)
	var shell_x: = []
	var shell_c: = []
	var pebble_x: = []
	var pebble_c: = []
	for k in 900:
		var p: = Vector3(rng.randf_range(-45, 104), 0, rng.randf_range(-30.0, -17.0))
		p.y = _height(p.x, p.z) + 0.01
		if rng.randf() < 0.5:
			shell_x.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(1.0, 0.45, 1.3) * rng.randf_range(0.6, 1.3)), p))
			shell_c.append([Color(1.0, 0.85, 0.8), Color(1.0, 0.95, 0.85), Color(1.0, 0.75, 0.6), Color(0.95, 0.9, 1.0)][k % 4])
		else:
			pebble_x.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(1.2, 0.6, 1.0) * rng.randf_range(0.5, 1.6)), p))
			pebble_c.append(Color(0.75, 0.72, 0.7).darkened(rng.randf() * 0.25))
	var sm: = SphereMesh.new()
	sm.radius = 0.035
	sm.height = 0.07
	sm.radial_segments = 10
	sm.rings = 5
	var mi1: = D.multimesh(self, sm, shell_x, shell_c)
	mi1.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi1.visibility_range_end = 45.0
	var mi2: = D.multimesh(self, sm, pebble_x, pebble_c)
	mi2.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi2.visibility_range_end = 45.0
	# algas na linha da maré
	var weed_x: = []
	for k in 160:
		var p: = Vector3(rng.randf_range(-45, 104), 0, rng.randf_range(-30.5, -28.5))
		p.y = _height(p.x, p.z) + 0.01
		weed_x.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU), p))
	var wm: = BoxMesh.new()
	wm.size = Vector3(0.5, 0.015, 0.06)
	var mi3: = D.multimesh(self, wm, weed_x, [], B.flat(Color(0.2, 0.42, 0.25), 0.8))
	mi3.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# troncos trazidos pelo mar
	for k in 10:
		var p: = Vector3(rng.randf_range(-40, 100), 0, rng.randf_range(-27.0, -19.0))
		if absf(p.x - KIOSK_C.x) < 7.0 or absf(p.x - PIER_X) < 4.0:
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
		for pp in [a2, b2]:
			B.cyl(self, 0.04, 0.05, 2.0, pp + Vector3(0, 1.0, 0), pole_m, 8)
		D.wire(self, a2 + Vector3(0, 1.9, 0), b2 + Vector3(0, 1.9, 0), 0.25)
		for j in 6:
			var cp: = a2.lerp(b2, (j + 0.5) / 6.0) + Vector3(0, 1.62 - 0.25 * 4.0 * ((j + 0.5) / 6.0) * (1.0 - (j + 0.5) / 6.0), 0)
			var piece: = B.box(self, Vector3(0.45, 0.5 if j % 2 == 0 else 0.35, 0.02), cp, B.flat(D.FLAG_COLS[(j + k) % D.FLAG_COLS.size()], 0.95))
			piece.rotation.z = rng.randf_range(-0.08, 0.08)
	for k in 12:
		B.model(self, "island_tree_01", Vector3(4.0 + k * 9.0 + rng.randf_range(-2, 2), 0, BACK_Z + 14.5 + rng.randf_range(-1, 2)), rng.randf() * TAU, rng.randf_range(1.6, 2.2))
