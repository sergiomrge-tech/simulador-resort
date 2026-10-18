extends Node3D


const POOL_MIN: = Vector2(-6, 0)
const POOL_MAX: = Vector2(6, 8)
var BUNG_X: Array = [-14.0, -21.5]
const BUNG_Z: = -8.0
const BAR_C: = Vector3(13, 0, -13)
const SHORE_Z: = -32.5
const WATER_Y: = -0.3

var lanterns: Array = []
var room_nodes: Array = []
var rede_nodes: Array = []
var desk: Interactable
var ocean_mat: ShaderMaterial
var pool_floor_mat: ShaderMaterial
var sand_mat: ShaderMaterial
var rain: GPUParticles3D
var _birds: Array = []
var points: = {}
var pool_spots: Array = []
var bar_spots: Array = []
var guests_mgr: Node
var mtn_mats: Array[ShaderMaterial] = []
var mtn_tree_mat: ShaderMaterial
var mtn_tree_mats: Array = []

var M: = {}
## v0.7: pedaços do mundo liberados por expansão (id da expansão -> Node3D) e o lote à venda de cada um.
var areas: = {}
var lots: = {}

func _ready() -> void :
	add_to_group("world")
	_materials()
	_ground()
	_ocean()
	_bounds()
	_paths()
	_area("pousada", _reception)
	_area("pool", _pool)
	_ensure_bung_x(Core.rooms.size())
	for i in Core.rooms.size():
		_bungalow(i, Vector3(BUNG_X[i], 0, BUNG_Z))
	_area("bar", _bar)
	_beach_props()
	_palms()
	_vegetation()
	_lantern_posts()
	_redes()
	_signs()
	_route_points()
	Core.room_changed.connect(_on_room_changed)
	Core.redes_changed.connect(_on_redes_changed)
	Core.bungalow_built.connect(_on_bungalow_built)
	Core.weather_changed.connect(_on_weather)
	Core.expansion_bought.connect(_on_expansion)
	for r in Core.rooms:
		_on_room_changed(r.id)
	_on_redes_changed(Core.redes)
	_birds_spawn()
	_weather_fx()
	_mountains()
	_build_lots()
	call_deferred("refresh_areas")

func _materials() -> void :
	M.plaster = B.mat("white_plaster", 0.5, Color(1, 1, 1), 0.9)
	M.terracotta = B.mat("white_plaster", 0.5, Color(0.66, 0.38, 0.26), 0.9)
	M.teal = B.mat("weathered_planks", 0.7, Color(0.15, 0.62, 0.62), 0.7)
	M.planks = B.mat("weathered_planks", 0.45, Color(1, 0.95, 0.88), 0.85)
	M.deckwood = B.mat("weathered_planks", 0.5, Color(0.85, 0.7, 0.55), 0.85)
	M.oak = B.mat("oak_wood_planks", 0.6, Color(1, 1, 1), 0.6)
	M.bamboo = B.mat("bamboo_wall", 0.45, Color(1.28, 1.2, 1.06), 0.85)
	M.linen = B.mat("rough_linen", 1.2, Color(0.97, 0.96, 0.93), 0.95)
	M.linen_teal = B.mat("rough_linen", 1.2, Color(0.35, 0.75, 0.78), 0.95)
	M.linen_sand = B.mat("rough_linen", 1.2, Color(0.9, 0.82, 0.68), 0.95)
	M.azulejo = B.mat("blue_floor_tiles_01", 0.5, Color(1, 1, 1), 0.35)
	M.stone = B.mat("light_stone", 0.55, Color(1, 1, 1), 0.75)
	M.terra_tiles = B.mat("patio_tiles", 0.55, Color(0.95, 0.9, 0.84), 0.75)
	var thatch: = B.mat("reed_roof_04", 0.45, Color(1.25, 1.08, 0.8), 0.95).duplicate()
	thatch.cull_mode = BaseMaterial3D.CULL_DISABLED
	M.thatch = thatch
	M.post = B.mat("palm_tree_bark", 0.8, Color(0.8, 0.7, 0.6), 0.9)
	M.dark = B.flat(Color(0.12, 0.09, 0.07), 0.9)

	M.darkwood = B.mat("dark_wooden_planks", 0.9, Color(1, 0.92, 0.85), 0.6)
	M.floor_in = B.mat("brown_planks_05", 0.42, Color(1, 0.97, 0.92), 0.7)
	M.rug = B.mat("fabric_pattern_07", 1.1, Color(1, 0.95, 0.9), 0.95)
	M.rug_teal = B.mat("fabric_pattern_07", 1.1, Color(0.55, 0.85, 0.85), 0.95)
	M.rattan = B.mat("rattan", 1.6, Color(1, 0.95, 0.85), 0.8)
	M.duvet = B.mat("rough_linen", 1.6, Color(1.0, 0.99, 0.97), 0.95)
	var voile: = B.mat("rough_linen", 1.4, Color(1, 1, 1, 0.55), 0.95).duplicate()
	voile.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
	voile.cull_mode = BaseMaterial3D.CULL_DISABLED
	M.voile = voile
	M.ceramic = B.flat(Color(0.95, 0.95, 0.93), 0.15)


func _height(x: float, z: float) -> float:
	var h: = 0.0
	if z < -24.0:
		var t: = (-24.0 - z)
		h = -0.5 * clampf(t / 14.0, 0.0, 1.0) - maxf(0.0, t - 14.0) * 0.09

	var side: = maxf(0.0, x - 112.0) * 0.8 + maxf(0.0, - x - 62.0) * 0.8
	if side > 0.0:
		h += minf(side * 0.35, 9.0) * (0.75 + 0.25 * sin(x * 0.11) * cos(z * 0.13))
	return h

func _ground() -> void :
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var step: = 2.0
	var x0: = -130.0
	var x1: = 130.0
	var z0: = -60.0
	var z1: = 110.0
	var nx: = int((x1 - x0) / step)
	var nz: = int((z1 - z0) / step)
	for iz in nz:
		for ix in nx:
			var xa: = x0 + ix * step
			var za: = z0 + iz * step
			var xb: = xa + step
			var zb: = za + step

			if xa >= POOL_MIN.x and xb <= POOL_MAX.x and za >= POOL_MIN.y and zb <= POOL_MAX.y:
				continue
			var q: = [Vector3(xa, _height(xa, za), za), Vector3(xb, _height(xb, za), za), 
				Vector3(xb, _height(xb, zb), zb), Vector3(xa, _height(xa, zb), zb)]
			for idx in [0, 1, 2, 0, 2, 3]:
				var v: Vector3 = q[idx]
				var e: = 0.5
				var n: = Vector3(_height(v.x - e, v.z) - _height(v.x + e, v.z), 2.0 * e, _height(v.x, v.z - e) - _height(v.x, v.z + e)).normalized()
				st.set_normal(n)
				st.set_uv(Vector2(v.x, v.z))
				st.add_vertex(v)
	var mi: = MeshInstance3D.new()
	mi.mesh = st.commit()
	var sm: = ShaderMaterial.new()
	sm.shader = load("res://shaders/ground.gdshader")
	sm.set_shader_parameter("dry_tex", B.tex("coast_sand_01"))
	sm.set_shader_parameter("dry_nor", B.nor("coast_sand_01"))
	sm.set_shader_parameter("wet_tex", B.tex("damp_beach_sand"))
	sm.set_shader_parameter("wet_nor", B.nor("damp_beach_sand"))
	sm.set_shader_parameter("wet_start", -23.5)
	sm.set_shader_parameter("wet_end", -33.2)
	sm.set_shader_parameter("rain_wet", 0.0)
	sand_mat = sm
	mi.material_override = sm
	mi.name = "Ground"
	add_child(mi)

	B.wall(self, Vector3(240, 1, 84), Vector3(20, -0.5, 50))
	B.wall(self, Vector3(240, 1, 24), Vector3(20, -0.5, -12))
	B.wall(self, Vector3(94, 1, 8), Vector3(-53, -0.5, 4))
	B.wall(self, Vector3(134, 1, 8), Vector3(73, -0.5, 4))
	var slope: = B.wall(self, Vector3(240, 1, 7.2), Vector3(0, -0.5 - 0.22, -27.5))
	slope.rotation.x = - atan2(0.43, 7.0)

func _ocean() -> void :
	var pm: = PlaneMesh.new()
	pm.size = Vector2(420, 220)
	pm.subdivide_width = 280 if Quality.hd else 140
	pm.subdivide_depth = 180 if Quality.hd else 90
	var mi: = MeshInstance3D.new()
	mi.mesh = pm
	mi.position = Vector3(0, WATER_Y, SHORE_Z - 110 + 4)
	ocean_mat = ShaderMaterial.new()
	ocean_mat.shader = load("res://shaders/ocean_hd.gdshader" if Quality.hd else "res://shaders/ocean.gdshader")
	ocean_mat.set_shader_parameter("shore_z", SHORE_Z)
	mi.material_override = ocean_mat
	mi.name = "Ocean"
	add_child(mi)

## Limites do mapa. v0.7.1: a vila cresceu para o norte (até z 78) e há uma passagem para o píer em x 70–74.
const PIER_X: = 72.0
func _bounds() -> void :
	B.wall(self, Vector3(PIER_X - 1.6 + 52.0, 4, 1), Vector3((-52.0 + PIER_X - 1.6) * 0.5, 1.5, -30.5))
	B.wall(self, Vector3(112.0 - PIER_X - 1.6, 4, 1), Vector3((PIER_X + 1.6 + 112.0) * 0.5, 1.5, -30.5))
	B.wall(self, Vector3(170, 4, 1), Vector3(30, 1.5, 78))
	B.wall(self, Vector3(1, 4, 112), Vector3(-48, 1.5, 23))
	B.wall(self, Vector3(1, 4, 112), Vector3(112, 1.5, 23))

func _strip(a: Vector2, b_: Vector2, w: float, m: Material, y: = 0.025) -> void :
	var d: = b_ - a
	var mid: = (a + b_) * 0.5
	var mi: = B.box(self, Vector3(w, 0.05, d.length()), Vector3(mid.x, y, mid.y), m)
	mi.rotation.y = atan2(d.x, d.y)

func _paths() -> void :
	_strip(Vector2(0, 19.5), Vector2(0, 46), 2.6, M.terra_tiles)
	_strip(Vector2(-10.5, 11.5), Vector2(-10.5, 26), 2.0, M.stone)
	_strip(Vector2(-11.5, 26), Vector2(0, 26), 2.0, M.stone)
	_strip(Vector2(-10.5, 11.5), Vector2(-10.5, -4.5), 2.0, M.stone)
	_strip(Vector2(-23.5, -4.5), Vector2(-9.5, -4.5), 2.0, M.stone)

	_strip(Vector2(9.0, -2.5), Vector2(11.2, -10.2), 1.6, M.deckwood, 0.06)
	_strip(Vector2(0, -3.0), Vector2(0, -16), 1.6, M.deckwood, 0.06)


func _wall_x(x0: float, x1: float, z: float, h: float, gaps: Array, base_y: = 0.0) -> void :

	var segs: = [[x0, x1]]
	for g in gaps:
		var nsegs: = []
		for s in segs:
			if g[1] <= s[0] or g[0] >= s[1]:
				nsegs.append(s)
			else:
				if g[0] > s[0]:
					nsegs.append([s[0], g[0]])
				if g[1] < s[1]:
					nsegs.append([g[1], s[1]])
		segs = nsegs
	for s in segs:
		_wall_piece(Vector3((s[0] + s[1]) * 0.5, base_y, z), s[1] - s[0], h, false)
	for g in gaps:
		var gw: float = g[1] - g[0]
		var cx: float = (g[0] + g[1]) * 0.5
		if g[2] > 0.01:
			_wall_piece(Vector3(cx, base_y, z), gw, g[2], false)
			B.box(self, Vector3(gw + 0.2, 0.08, 0.4), Vector3(cx, base_y + g[2], z), M.teal)
		if g[3] < h:
			var mi: = B.box(self, Vector3(gw, h - g[3], 0.26), Vector3(cx, base_y + (h + g[3]) * 0.5, z), M.plaster)
			mi.name = "lintel"

		B.box(self, Vector3(gw + 0.24, 0.12, 0.32), Vector3(cx, base_y + g[3] + 0.06, z), M.teal)
		B.box(self, Vector3(0.12, g[3] - g[2], 0.32), Vector3(g[0] - 0.06, base_y + (g[2] + g[3]) * 0.5, z), M.teal)
		B.box(self, Vector3(0.12, g[3] - g[2], 0.32), Vector3(g[1] + 0.06, base_y + (g[2] + g[3]) * 0.5, z), M.teal)

func _wall_z(z0: float, z1: float, x: float, h: float, gaps: Array, base_y: = 0.0) -> void :
	var holder: = Node3D.new()
	holder.position = Vector3(x, 0, 0)
	holder.rotation.y = PI * 0.5
	add_child(holder)

	var saved: = get_child_count()
	_wall_x( - z1, - z0, 0.0, h, gaps.map( func(g): return [ - g[1], - g[0], g[2], g[3]]), base_y)
	var added: = []
	for i in range(saved, get_child_count()):
		added.append(get_child(i))
	for n in added:
		var gt: Transform3D = n.transform
		remove_child(n)
		holder.add_child(n)
		n.transform = gt

func _wall_piece(pos: Vector3, w: float, h: float, _unused: bool) -> void :
	B.box(self, Vector3(w, h, 0.26), pos + Vector3(0, h * 0.5, 0), M.plaster, true)

	B.box(self, Vector3(w + 0.02, minf(0.45, h), 0.3), pos + Vector3(0, minf(0.45, h) * 0.5, 0), M.terracotta)

func _reception() -> void :
	var cx: = 0.0
	var cz: = 16.0
	var y0: = 0.12
	B.platform(self, Vector3(10.6, 0.24, 7.6), Vector3(cx, 0.0, cz), M.stone, 0.5)
	B.box(self, Vector3(9.6, 0.02, 6.6), Vector3(cx, y0 + 0.011, cz), M.azulejo)
	var h: = 3.3
	_wall_x(-5, 5, 19.5, h, [[-1.4, 1.4, 0.0, 2.6], [-4.0, -2.4, 1.0, 2.3], [2.4, 4.0, 1.0, 2.3]], y0)
	_wall_x(-5, 5, 12.5, h, [[-1.6, 1.6, 0.0, 2.7], [-4.2, -2.6, 1.0, 2.3], [2.6, 4.2, 1.0, 2.3]], y0)
	_wall_z(12.5, 19.5, -5, h, [[14.5, 17.5, 1.0, 2.3]], y0)
	_wall_z(12.5, 19.5, 5, h, [[14.5, 17.5, 1.0, 2.3]], y0)

	for sx in [-5.0, 5.0]:
		for sz in [12.5, 19.5]:
			B.box(self, Vector3(0.4, h, 0.4), Vector3(sx, y0 + h * 0.5, sz), M.plaster)

	B.box(self, Vector3(10.2, 0.08, 7.2), Vector3(cx, y0 + h + 0.04, cz), M.planks)
	B.hip_roof(self, Vector3(cx, y0 + h + 0.08, cz), 13.0, 10.0, 4.2, M.thatch, 0.25)

	var desk_z: = 15.5
	B.box(self, Vector3(5.2, 1.05, 0.7), Vector3(0, y0 + 0.525, desk_z), M.planks, true)
	B.box(self, Vector3(5.4, 0.06, 0.85), Vector3(0, y0 + 1.08, desk_z), M.oak)
	B.box(self, Vector3(5.22, 0.35, 0.72), Vector3(0, y0 + 0.175, desk_z), M.terracotta)
	B.box(self, Vector3(5.24, 0.08, 0.74), Vector3(0, y0 + 0.9, desk_z), M.teal)
	B.model(self, "CashRegister_01", Vector3(1.4, y0 + 1.11, desk_z - 0.05), PI, 1.0)
	B.model(self, "lambis_shell", Vector3(-1.6, y0 + 1.11, desk_z), 0.6, 1.0)
	B.model(self, "potted_plant_02", Vector3(-4.3, y0, 18.8), 0.0, 1.2)
	B.model(self, "potted_plant_02", Vector3(4.3, y0, 18.8), 1.0, 1.2)
	B.model(self, "planter_pot_clay", Vector3(-4.3, y0, 13.2), 0.0, 1.0)
	B.model(self, "wicker_basket_01", Vector3(4.2, y0, 13.3), 0.0, 1.0)

	B.box(self, Vector3(2.4, 1.2, 0.3), Vector3(-2.2, y0 + 1.5, 12.8), M.oak)
	for i in 4:
		B.box(self, Vector3(0.18, 0.25, 0.04), Vector3(-3.0 + i * 0.5, y0 + 1.6, 12.98), M.teal)
	B.label(self, "RECEPÇÃO", Vector3(0, y0 + 2.95, 19.66), 90, Color(0.1, 0.45, 0.48), Color(1, 1, 1, 0.9))
	desk = Interactable.new()
	var cs: = CollisionShape3D.new()
	var sh: = BoxShape3D.new()
	sh.size = Vector3(5.2, 1.4, 1.2)
	cs.shape = sh
	desk.add_child(cs)
	desk.position = Vector3(0, y0 + 0.8, desk_z)
	desk.name = "Desk"
	add_child(desk)

	var l: = OmniLight3D.new()
	l.position = Vector3(0, y0 + 2.9, cz)
	l.omni_range = 8.0
	l.light_energy = 0.0
	l.light_color = Color(1.0, 0.82, 0.6)
	add_child(l)
	lanterns.append([l, null, 1.6, true])


func _pool() -> void :
	var depth: = 1.4
	var wx: = POOL_MAX.x - POOL_MIN.x
	var wz: = POOL_MAX.y - POOL_MIN.y
	var c: = Vector3((POOL_MIN.x + POOL_MAX.x) * 0.5, 0, (POOL_MIN.y + POOL_MAX.y) * 0.5)

	var deck_y: = 0.06
	B.box(self, Vector3(18, 0.12, 3), Vector3(0, deck_y, -1.5), M.stone)
	B.box(self, Vector3(18, 0.12, 3), Vector3(0, deck_y, 9.5), M.stone)
	B.box(self, Vector3(3, 0.12, 8), Vector3(-7.5, deck_y, 4), M.stone)
	B.box(self, Vector3(3, 0.12, 8), Vector3(7.5, deck_y, 4), M.stone)

	var coping: = B.flat(Color(0.93, 0.9, 0.84), 0.6)
	B.box(self, Vector3(wx + 0.6, 0.16, 0.3), Vector3(c.x, 0.1, POOL_MIN.y - 0.15), coping)
	B.box(self, Vector3(wx + 0.6, 0.16, 0.3), Vector3(c.x, 0.1, POOL_MAX.y + 0.15), coping)
	B.box(self, Vector3(0.3, 0.16, wz), Vector3(POOL_MIN.x - 0.15, 0.1, c.z), coping)
	B.box(self, Vector3(0.3, 0.16, wz), Vector3(POOL_MAX.x + 0.15, 0.1, c.z), coping)

	var basin: Material = M.azulejo
	if Quality.hd:
		pool_floor_mat = ShaderMaterial.new()
		pool_floor_mat.shader = load("res://shaders/pool_floor.gdshader")
		pool_floor_mat.set_shader_parameter("albedo_tex", B.tex("blue_floor_tiles_01"))
		pool_floor_mat.set_shader_parameter("normal_tex", B.nor("blue_floor_tiles_01"))
		basin = pool_floor_mat
	B.box(self, Vector3(wx, 0.1, wz), Vector3(c.x, - depth - 0.05, c.z), basin)
	B.box(self, Vector3(wx, depth, 0.1), Vector3(c.x, - depth * 0.5, POOL_MIN.y + 0.05), basin)
	B.box(self, Vector3(wx, depth, 0.1), Vector3(c.x, - depth * 0.5, POOL_MAX.y - 0.05), basin)
	B.box(self, Vector3(0.1, depth, wz), Vector3(POOL_MIN.x + 0.05, - depth * 0.5, c.z), basin)
	B.box(self, Vector3(0.1, depth, wz), Vector3(POOL_MAX.x - 0.05, - depth * 0.5, c.z), basin)

	var water: = MeshInstance3D.new()
	var pm: = PlaneMesh.new()
	pm.size = Vector2(wx - 0.1, wz - 0.1)
	pm.subdivide_width = 24
	pm.subdivide_depth = 16
	water.mesh = pm
	water.position = Vector3(c.x, -0.12, c.z)
	var wm: = ShaderMaterial.new()
	wm.shader = load("res://shaders/pool_hd.gdshader" if Quality.hd else "res://shaders/pool.gdshader")
	water.material_override = wm
	add_child(water)

	B.wall(self, Vector3(wx, 2, 0.2), Vector3(c.x, 1, POOL_MIN.y))
	B.wall(self, Vector3(wx, 2, 0.2), Vector3(c.x, 1, POOL_MAX.y))
	B.wall(self, Vector3(0.2, 2, wz), Vector3(POOL_MIN.x, 1, c.z))
	B.wall(self, Vector3(0.2, 2, wz), Vector3(POOL_MAX.x, 1, c.z))
	B.wall(self, Vector3(wx, 1, wz), Vector3(c.x, -0.5, c.z))

	var umbrella_tints: = [Color(0.86, 0.22, 0.18), Color(0.95, 0.78, 0.35), Color(0.12, 0.55, 0.58), Color(0.95, 0.95, 0.9)]
	for side in [-1.0, 1.0]:
		for i in 3:
			var p: = Vector3(side * 7.6, 0.12, 1.2 + i * 2.6)
			_lounger(p, - side * PI * 0.5)
			pool_spots.append({"pos": p + Vector3(0, 0.3, 0), "rot": - side * PI * 0.5 + PI, "anim": "Sitting_Idle_Loop", "busy": false})
	for sp in [Vector3(-3, -0.4, 3), Vector3(2.5, -0.4, 5.5), Vector3(0.5, -0.4, 2.0)]:
		pool_spots.append({"pos": sp, "rot": randf() * TAU, "anim": "Swim_Idle_Loop", "busy": false})
	B.model(self, "lifebuoy", Vector3(6.6, 0.95, 8.65), 0.0, 1.0).rotation.x = - PI * 0.5
	B.box(self, Vector3(0.12, 1.4, 0.12), Vector3(6.6, 0.75, 8.9), M.planks)

	var ui: = 0
	for p in [Vector3(-7.6, 0.12, 2.5), Vector3(7.6, 0.12, 2.5), Vector3(-7.6, 0.12, 5.1), Vector3(7.6, 0.12, 5.1)]:
		_umbrella(p, 1.35, umbrella_tints[ui % umbrella_tints.size()], ui == 2)
		ui += 1

func _lounger(p: Vector3, rot: float) -> void :
	var n: = Node3D.new()
	n.position = p
	n.rotation.y = rot
	add_child(n)

	B.box(n, Vector3(0.72, 0.1, 1.9), Vector3(0, 0.3, 0), M.rattan)
	B.box(n, Vector3(0.68, 0.1, 0.72), Vector3(0, 0.56, -0.86), M.rattan).rotation.x = -0.7
	B.box(n, Vector3(0.64, 0.09, 1.25), Vector3(0, 0.39, 0.28), M.linen_teal)
	B.box(n, Vector3(0.6, 0.08, 0.62), Vector3(0, 0.62, -0.8), M.linen_teal).rotation.x = -0.7
	B.box(n, Vector3(0.44, 0.12, 0.22), Vector3(0, 0.82, -1.02), M.linen).rotation.x = -0.6
	for sx in [-0.31, 0.31]:
		for sz in [-0.82, 0.82]:
			B.cyl(n, 0.03, 0.035, 0.3, Vector3(sx, 0.15, sz), M.darkwood, 8)

var _parasol_mats: = {}
var _thatch_parasol: Material


func _umbrella(p: Vector3, r: float, tint: = Color(0.86, 0.22, 0.18), thatch: = false) -> void :
	var n: = Node3D.new()
	n.position = p
	add_child(n)
	var hub_y: = 2.02
	B.cyl(n, 0.03, 0.042, hub_y, Vector3(0, hub_y * 0.5, 0), M.darkwood, 12)
	B.cyl(n, 0.075, 0.075, 0.05, Vector3(0, hub_y - 0.01, 0), M.oak, 12)
	B.sphere(n, 0.042, Vector3(0, hub_y + 0.05, 0), M.oak)
	var panels: = 8 if thatch else 12
	var drop: = 0.58 if thatch else 0.4
	var sag: = 0.2 if thatch else 0.13
	var canopy: = MeshInstance3D.new()
	canopy.mesh = _parasol_canopy(r, panels, drop, sag, thatch)
	canopy.position = Vector3(0, hub_y, 0)
	canopy.material_override = _thatch_parasol_mat() if thatch else _stripe_mat(tint)
	n.add_child(canopy)
	var ribs: = MeshInstance3D.new()
	ribs.mesh = _parasol_ribs(r, panels, drop)
	ribs.position = Vector3(0, hub_y, 0)
	ribs.material_override = M.darkwood
	n.add_child(ribs)

func _parasol_point(a0: float, a1: float, across: float, radial: float, radius: float, drop: float, sag: float) -> Vector3:
	var ang: = lerpf(a0, a1, across)
	var rr: = radial * radius
	var y: = - drop * pow(radial, 1.2)
	y -= sin(across * PI) * sag * radial * radial
	return Vector3(cos(ang) * rr, y, sin(ang) * rr)

func _parasol_canopy(radius: float, panels: int, drop: float, sag: float, thatch: bool) -> ArrayMesh:
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rings: = 7
	var across_n: = 3
	for p in panels:
		var a0: = TAU * float(p) / float(panels)
		var a1: = TAU * float(p + 1) / float(panels)
		for ring in rings:
			var r0: = float(ring) / float(rings)
			var r1: = float(ring + 1) / float(rings)
			for k in across_n:
				var u0: = float(k) / float(across_n)
				var u1: = float(k + 1) / float(across_n)
				var q: = [
					_parasol_point(a0, a1, u0, r0, radius, drop, sag), 
					_parasol_point(a0, a1, u1, r0, radius, drop, sag), 
					_parasol_point(a0, a1, u1, r1, radius, drop, sag), 
					_parasol_point(a0, a1, u0, r1, radius, drop, sag), 
				]
				var uv: = []
				for qi in 4:
					var radial: float = r0 if qi < 2 else r1
					var across: float = u0 if qi == 0 or qi == 3 else u1

					var u: = across * 0.48 + 0.01
					if not thatch and p % 2 == 1:
						u += 0.5
					var v: = radial * (2.4 if thatch else 0.92)
					uv.append(Vector2(u, v))
				for idx in [0, 1, 2, 0, 2, 3]:
					st.set_uv(uv[idx])
					st.add_vertex(q[idx])
		if not thatch:
			for k in 6:
				var u0: = float(k) / 6.0
				var u1: = float(k + 1) / 6.0
				var rim0: = _parasol_point(a0, a1, u0, 1.0, radius, drop, sag)
				var rim1: = _parasol_point(a0, a1, u1, 1.0, radius, drop, sag)
				var hang0: = 0.12 + 0.16 * sin(u0 * PI)
				var hang1: = 0.12 + 0.16 * sin(u1 * PI)
				var out0: = Vector3(rim0.x, 0, rim0.z)
				var out1: = Vector3(rim1.x, 0, rim1.z)
				if out0.length() > 0.01:
					out0 = out0.normalized() * 0.05
				if out1.length() > 0.01:
					out1 = out1.normalized() * 0.05
				var h0: = rim0 + out0 + Vector3(0, - hang0, 0)
				var h1: = rim1 + out1 + Vector3(0, - hang1, 0)
				var fu0: = u0 * 0.48 + 0.01
				var fu1: = u1 * 0.48 + 0.01
				if p % 2 == 1:
					fu0 += 0.5
					fu1 += 0.5
				var uv0: = Vector2(fu0, 0.9)
				var uv1: = Vector2(fu1, 0.9)
				var uvh0: = Vector2(fu0, 1.02)
				var uvh1: = Vector2(fu1, 1.02)
				st.set_uv(uv0);st.add_vertex(rim0)
				st.set_uv(uv1);st.add_vertex(rim1)
				st.set_uv(uvh1);st.add_vertex(h1)
				st.set_uv(uv0);st.add_vertex(rim0)
				st.set_uv(uvh1);st.add_vertex(h1)
				st.set_uv(uvh0);st.add_vertex(h0)
	st.generate_normals()
	return st.commit()

func _parasol_ribs(radius: float, panels: int, drop: float) -> ArrayMesh:
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for p in panels:
		var ang: = TAU * float(p) / float(panels)
		var side: = Vector3( - sin(ang), 0, cos(ang)) * 0.011
		var up: = Vector3(0, 0.012, 0)
		for s in 5:
			var t0: = float(s) / 5.0
			var t1: = float(s + 1) / 5.0
			var p0: = Vector3(cos(ang) * radius * t0, - drop * pow(t0, 1.2) + 0.02, sin(ang) * radius * t0)
			var p1: = Vector3(cos(ang) * radius * t1, - drop * pow(t1, 1.2) + 0.02, sin(ang) * radius * t1)
			var q: = [p0 - side + up, p0 + side + up, p1 + side + up, p1 - side + up]
			for idx in [0, 1, 2, 0, 2, 3]:
				st.set_uv(Vector2(float(idx), t0))
				st.add_vertex(q[idx])
	st.generate_normals()
	return st.commit()

func _stripe_mat(tint: Color) -> Material:
	var key: = tint.to_html()
	if _parasol_mats.has(key):
		return _parasol_mats[key]


	var img: = Image.create(1024, 256, false, Image.FORMAT_RGB8)
	var alt: = Color(0.97, 0.95, 0.91) if tint.get_luminance() < 0.62 else tint.darkened(0.32)
	var half: = 512
	var bands: = 4
	var bw: = int(half / bands)
	for side in 2:
		for i in bands:
			var col: Color = tint if (i + side) % 2 == 0 else alt
			img.fill_rect(Rect2i(side * half + i * bw, 0, bw, 256), col)
	for y in range(0, 256, 7):
		for x in 1024:
			img.set_pixel(x, y, img.get_pixel(x, y).darkened(0.045))
	var tex: = ImageTexture.create_from_image(img)
	var m: = StandardMaterial3D.new()
	m.albedo_texture = tex
	m.roughness = 0.84
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	_parasol_mats[key] = m
	return m

func _thatch_parasol_mat() -> Material:
	if _thatch_parasol == null:
		var m: StandardMaterial3D = M.thatch.duplicate()
		m.uv1_scale = Vector3(1.6, 2.4, 1)
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		_thatch_parasol = m
	return _thatch_parasol

func _coconut_cup(parent: Node, pos: Vector3) -> Node3D:
	var n: = Node3D.new()
	n.position = pos
	parent.add_child(n)
	var shell: = B.flat(Color(0.42, 0.26, 0.12), 0.55)
	B.sphere(n, 0.09, Vector3(0, 0.07, 0), shell, Vector3(1.05, 0.82, 1.05))
	B.sphere(n, 0.04, Vector3(0, 0.13, 0), B.flat(Color(0.96, 0.94, 0.88), 0.35))
	var straw: = B.cyl(n, 0.007, 0.007, 0.2, Vector3(0.02, 0.2, 0), B.flat(Color(0.85, 0.2, 0.16), 0.4), 6)
	straw.rotation.z = -0.55
	return n

func _petisco_plate(parent: Node, pos: Vector3) -> Node3D:
	var n: = Node3D.new()
	n.position = pos
	parent.add_child(n)
	B.cyl(n, 0.15, 0.13, 0.02, Vector3(0, 0.015, 0), B.flat(Color(0.95, 0.94, 0.9), 0.28), 16)
	var bits: = [Color(0.82, 0.42, 0.14), Color(0.72, 0.16, 0.12), Color(0.9, 0.72, 0.28), Color(0.45, 0.62, 0.22)]
	for i in 5:
		var a: = TAU * float(i) / 5.0
		B.sphere(n, 0.026, Vector3(cos(a) * 0.06, 0.04, sin(a) * 0.06), B.flat(bits[i % 4], 0.5))
	return n


func _bungalow(i: int, c: Vector3) -> void :
	var _child_mark: = get_child_count()
	var y0: = 0.25
	var w: = 5.6
	var d: = 5.0

	B.platform(self, Vector3(w + 0.6, 0.5, d + 2.8), Vector3(c.x, 0.0, c.z - 1.1), M.deckwood, 0.55)
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.box(self, Vector3(0.22, 0.5, 0.22), Vector3(c.x + sx * (w * 0.5 + 0.2), 0.05, c.z - 1.1 + sz * (d * 0.5 + 1.3)), M.post)
	var h: = 2.7
	var x0: = c.x - w * 0.5
	var x1: = c.x + w * 0.5
	var zf: = c.z - d * 0.5
	var zb: = c.z + d * 0.5
	_bwall_x(x0, x1, zb, h, [[c.x + 0.8, c.x + 2.0, 0.0, 2.15]], y0)
	_bwall_x(x0, x1, zf, h, [[c.x - 1.6, c.x + 1.6, 0.8, 2.1]], y0)
	_bwall_z(zf, zb, x0, h, [[c.z - 0.6, c.z + 0.6, 1.0, 2.0]], y0)
	_bwall_z(zf, zb, x1, h, [], y0)
	for sx in [x0, x1]:
		for sz in [zf, zb]:
			B.cyl(self, 0.12, 0.14, h, Vector3(sx, y0 + h * 0.5, sz), M.post, 8)
	B.box(self, Vector3(w, 0.06, d), Vector3(c.x, y0 + h, c.z), M.planks)
	B.hip_roof(self, Vector3(c.x, y0 + h + 0.03, c.z - 0.7), w + 2.4, d + 3.8, 3.8, M.thatch, 0.22)

	B.model(self, "wooden_stool_01", Vector3(c.x - 1.5, y0, zf - 1.3), 0.3, 1.0)
	B.model(self, "side_table_01", Vector3(c.x + 1.6, y0, zf - 1.2), 0.0, 1.0)
	B.model(self, "wooden_bucket_01", Vector3(c.x + 2.4, y0, zb + 0.6), 0.0, 1.0)

	var room: = {"clean": Node3D.new(), "dirty": {}, "light": null}
	var bed_c: = Vector3(c.x - 1.2, y0, c.z - 0.2)

	B.box(self, Vector3(w - 0.1, 0.02, d - 0.1), Vector3(c.x, y0 + 0.012, c.z), M.floor_in)
	B.wall(self, Vector3(1.9, 0.7, 2.2), bed_c + Vector3(0, 0.35, 0))
	B.model(self, "painted_wooden_nightstand", Vector3(c.x - 2.45, y0, c.z + 1.55), PI, 1.0)
	B.model(self, "wooden_lantern_01", Vector3(c.x - 2.42, y0 + 0.62, c.z + 1.6), 0.4, 0.75)
	B.model(self, "potted_plant_02", Vector3(c.x + 2.2, y0, c.z - 2.0), 0.0, 0.9)
	B.model(self, "wicker_basket_02", Vector3(c.x + 2.3, y0, c.z + 0.2), 0.6, 1.0)
	var lamp: = OmniLight3D.new()
	lamp.position = Vector3(c.x - 2.42, y0 + 0.9, c.z + 1.55)
	lamp.omni_range = 2.6
	lamp.light_energy = 0.9
	lamp.light_color = Color(1.0, 0.7, 0.4)
	add_child(lamp)
	lanterns.append([lamp, null, 0.9, true])

	var cl: Node3D = room.clean
	add_child(cl)

	B.box(cl, Vector3(1.3, 0.025, 0.42), bed_c + Vector3(0, 0.475, -0.62), M.linen_sand)
	for sx in [-0.22, 0.22]:
		var towel: = B.cyl(cl, 0.075, 0.075, 0.42, bed_c + Vector3(sx, 0.56, -0.62), M.linen_teal, 16)
		towel.rotation.x = PI * 0.5

	var dc: = Node3D.new()
	add_child(dc)
	B.box(dc, Vector3(1.3, 0.04, 1.1), bed_c + Vector3(0.1, 0.49, -0.1), M.linen_sand).rotation = Vector3(0.05, 0.4, 0.06)
	B.box(dc, Vector3(0.8, 0.1, 0.6), bed_c + Vector3(-0.3, 0.53, -0.45), M.linen_sand).rotation = Vector3(0.25, -0.5, 0.15)
	B.box(dc, Vector3(0.55, 0.13, 0.36), bed_c + Vector3(0.4, 0.54, 0.2), M.linen).rotation = Vector3(0.1, 0.9, 0.3)
	B.box(dc, Vector3(0.62, 0.14, 0.4), bed_c + Vector3(-1.05, 0.08, 0.6), M.linen).rotation = Vector3(0.0, 0.3, 0.1)
	var dt: = Node3D.new()
	add_child(dt)
	B.box(dt, Vector3(0.8, 0.03, 0.5), Vector3(c.x + 0.4, y0 + 0.02, c.z - 1.6), M.linen_teal).rotation.y = 0.7
	B.box(dt, Vector3(0.6, 0.06, 0.45), Vector3(c.x + 0.7, y0 + 0.04, c.z - 1.3), M.linen_teal).rotation = Vector3(0.1, -0.3, 0.05)
	B.box(dt, Vector3(0.7, 0.03, 0.5), Vector3(c.x - 0.1, y0 + 0.02, zf - 1.0), M.linen_teal).rotation.y = 1.9
	var dl: = Node3D.new()
	add_child(dl)
	var red: = B.flat(Color(0.75, 0.1, 0.08), 0.35, 0.6)
	var paper: = B.flat(Color(0.95, 0.95, 0.9), 0.9)
	B.cyl(dl, 0.033, 0.033, 0.12, Vector3(c.x + 1.2, y0 + 0.06, c.z + 1.6), red, 10)
	B.cyl(dl, 0.033, 0.033, 0.12, Vector3(c.x + 1.5, y0 + 0.033, c.z + 1.2), red, 10).rotation.z = PI * 0.5
	B.sphere(dl, 0.07, Vector3(c.x + 0.9, y0 + 0.06, c.z + 1.3), paper)
	B.sphere(dl, 0.06, Vector3(c.x + 1.7, y0 + 0.05, c.z + 1.8), paper)
	B.sphere(dl, 0.12, Vector3(c.x + 0.6, y0 + 0.1, c.z + 1.8), B.flat(Color(0.35, 0.23, 0.12), 0.9), Vector3(1, 0.8, 1))
	B.sphere(dl, 0.18, Vector3(c.x + 1.9, y0 + 0.16, c.z + 0.6), B.flat(Color(0.1, 0.1, 0.1), 0.3), Vector3(1, 1.3, 1))
	room.dirty = {"cama": dc, "toalhas": dt, "lixo": dl}

	var items: = {"cama": [bed_c + Vector3(0, 0.6, 0), Vector3(1.9, 0.9, 2.2), "Arrumar a cama"], 
		"toalhas": [Vector3(c.x + 0.4, y0 + 0.3, c.z - 1.4), Vector3(1.6, 0.8, 1.6), "Recolher as toalhas"], 
		"lixo": [Vector3(c.x + 1.3, y0 + 0.3, c.z + 1.3), Vector3(1.6, 0.8, 1.4), "Jogar o lixo fora"]}
	room.inter = {}
	for k in items:
		var it: = Interactable.new()
		var cs: = CollisionShape3D.new()
		var sh: = BoxShape3D.new()
		sh.size = items[k][1]
		cs.shape = sh
		it.add_child(cs)
		it.position = items[k][0]
		var room_id: = i
		var key: String = k
		var txt: String = items[k][2]
		it.prompt_fn = func() -> String:
			var r: Dictionary = Core.rooms[room_id]
			if r.state == "dirty" and r.dirty.get(key, false):
				return "%s (%s)" % [tr(txt), tr("Bangalô %d") % (room_id + 1)]
			return ""
		it.action_fn = func() -> void :
			if Core.clean_item(room_id, key):
				get_tree().call_group("audio", "sfx", "clean")
		add_child(it)
		room.inter[k] = it

	var l: = OmniLight3D.new()
	l.position = Vector3(c.x, y0 + 2.3, c.z)
	l.omni_range = 6.5
	l.light_color = Color(1.0, 0.8, 0.56)
	l.shadow_enabled = Quality.hd
	l.shadow_blur = 1.5
	add_child(l)
	lanterns.append([l, null, 2.0, true])
	B.label(self, "BANGALÔ %d" % (i + 1), Vector3(c.x + 1.4, y0 + 2.45, zb + 0.15), 48, Color(1, 0.95, 0.85), Color(0.2, 0.12, 0.05, 0.9))
	points["room%d_door" % i] = Vector3(c.x + 1.4, 0.25, zb + 1.2)
	points["room%d_in" % i] = Vector3(c.x + 1.4, 0.25, zb - 1.0)
	points["room%d_front" % i] = Vector3(c.x + 1.4, 0, -4.5)
	room.look = {}
	_upgrade_meshes(room, c, y0, bed_c, x0, x1, zf, zb, h)
	_upgrade_sign(i, c, y0, x0)
	var nodes: = []
	for idx in range(_child_mark, get_child_count()):
		nodes.append(get_child(idx))
	room.nodes = nodes
	room_nodes.append(room)

func _bwall_x(x0: float, x1: float, z: float, h: float, gaps: Array, y0: float) -> void :
	var save_pl = M.plaster
	var save_tc = M.terracotta
	M.plaster = M.bamboo
	M.terracotta = M.deckwood
	_wall_x(x0, x1, z, h, gaps, y0)
	M.plaster = save_pl
	M.terracotta = save_tc

func _bwall_z(z0: float, z1: float, x: float, h: float, gaps: Array, y0: float) -> void :
	var save_pl = M.plaster
	var save_tc = M.terracotta
	M.plaster = M.bamboo
	M.terracotta = M.deckwood
	_wall_z(z0, z1, x, h, gaps, y0)
	M.plaster = save_pl
	M.terracotta = save_tc

func _on_room_changed(id: int) -> void :
	if id >= room_nodes.size():
		return
	var r: Dictionary = Core.rooms[id]
	var rn: Dictionary = room_nodes[id]
	rn.clean.visible = r.state == "free"
	for k in rn.dirty:
		rn.dirty[k].visible = r.state == "dirty" and r.dirty.get(k, false)
	apply_room_look(id)


func _look(room: Dictionary, cat: String, tier: int, node: Node3D, max_t: = 99) -> void :
	if not room.look.has(cat):
		room.look[cat] = []
	room.look[cat].append({"n": node, "t": tier, "max": max_t})
	node.visible = false

func _upgrade_meshes(room: Dictionary, c: Vector3, y0: float, bed_c: Vector3, x0: float, x1: float, zf: float, zb: float, h: float) -> void :

	var bed0: = B.model(self, "GothicBed_01", bed_c, PI, 1.0)
	bed0.scale = Vector3(1.12, 1.0, 1.06)
	_look(room, "cama", 0, bed0, 0)
	var bed1: = B.model(self, "GothicBed_01", bed_c, PI, 1.0)
	bed1.scale = Vector3(1.3, 1.0, 1.1)
	_look(room, "cama", 1, bed1)
	var canopy: = Node3D.new()
	add_child(canopy)
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.cyl(canopy, 0.045, 0.055, 2.35, bed_c + Vector3(sx * 1.02, 1.175, sz * 1.15), M.darkwood, 10)
	for sz in [-1.0, 1.0]:
		B.box(canopy, Vector3(2.12, 0.07, 0.07), bed_c + Vector3(0, 2.35, sz * 1.15), M.darkwood)
	for sx in [-1.0, 1.0]:
		B.box(canopy, Vector3(0.07, 0.07, 2.36), bed_c + Vector3(sx * 1.02, 2.35, 0), M.darkwood)

	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			var drape: = B.box(canopy, Vector3(0.34, 2.15, 0.02), bed_c + Vector3(sx * 0.9, 1.25, sz * 1.17), M.voile)
			drape.rotation.y = sx * sz * 0.35
	B.box(canopy, Vector3(2.12, 0.3, 2.36), bed_c + Vector3(0, 2.2, 0), M.voile)
	_look(room, "cama", 2, canopy)

	var blanket: = B.box(self, Vector3(1.5, 0.025, 0.7), bed_c + Vector3(0, 0.48, -0.45), M.rug)
	_look(room, "roupa", 1, blanket, 1)
	var linens: = Node3D.new()
	add_child(linens)
	B.box(linens, Vector3(1.55, 0.03, 0.55), bed_c + Vector3(0, 0.49, -0.6), M.rug_teal)
	B.model(linens, "throw_pillows_01", bed_c + Vector3(0.12, 0.47, 0.5), PI, 0.8)
	_look(room, "roupa", 2, linens)

	var decor: = Node3D.new()
	add_child(decor)
	B.box(decor, Vector3(2.0, 0.015, 1.4), Vector3(c.x + 0.6, y0 + 0.03, c.z - 0.3), M.rug)
	B.box(decor, Vector3(2.1, 0.01, 1.5), Vector3(c.x + 0.6, y0 + 0.025, c.z - 0.3), M.darkwood)
	B.model(decor, "hanging_picture_frame_02", Vector3(bed_c.x, y0 + 1.75, zb - 0.08), PI, 1.1)
	B.model(decor, "ceramic_vase_02", Vector3(c.x - 2.55, y0 + 0.62, c.z + 1.42), 0.0, 0.8)
	_look(room, "decor", 1, decor)
	var lounge: = Node3D.new()
	add_child(lounge)
	B.model(lounge, "Rockingchair_01", Vector3(c.x + 1.75, y0, c.z - 1.55), PI + 0.6, 1.0)
	B.model(lounge, "side_table_01", Vector3(c.x + 2.3, y0, c.z - 0.75), 0.0, 0.9)
	B.model(lounge, "vintage_oil_lamp", Vector3(c.x + 2.3, y0 + 0.5, c.z - 0.75), 0.0, 0.6)
	var plant: = B.model(lounge, "pachira_aquatica_01", Vector3(c.x - 2.0, y0, zb - 0.45), 0.4, 1.0)
	_keep_parts(plant, ["_d"])
	var ll: = OmniLight3D.new()
	ll.position = Vector3(c.x + 2.3, y0 + 1.0, c.z - 0.75)
	ll.omni_range = 3.0
	ll.light_energy = 1.1
	ll.light_color = Color(1.0, 0.68, 0.38)
	lounge.add_child(ll)
	_look(room, "decor", 2, lounge)

	var fan_root: = Node3D.new()
	add_child(fan_root)
	fan_root.position = Vector3(c.x + 0.3, y0 + h, c.z - 0.2)
	var fan_m: = B.model(fan_root, "ceiling_fan", Vector3.ZERO, 0.0, 0.85)
	var blades: = fan_m.find_child("ceiling_fan_blades", true, false) as Node3D
	room.fan = blades if blades else fan_m
	_look(room, "clima", 1, fan_root)
	var ac: = Node3D.new()
	add_child(ac)
	var acp: = Vector3(x1 - 0.13, y0 + 2.12, c.z + 0.2)
	B.box(ac, Vector3(0.22, 0.3, 0.86), acp, B.flat(Color(0.95, 0.96, 0.97), 0.35))
	B.box(ac, Vector3(0.03, 0.05, 0.74), acp + Vector3(-0.115, -0.1, 0), B.flat(Color(0.25, 0.3, 0.32), 0.5))
	B.box(ac, Vector3(0.02, 0.02, 0.08), acp + Vector3(-0.115, 0.08, 0.32), B.flat(Color(0.2, 0.9, 0.5), 0.3))
	_look(room, "clima", 2, ac)

	var bath: = Node3D.new()
	add_child(bath)
	B.model(bath, "ornate_mirror_01", Vector3(x0 + 0.08, y0 + 1.55, c.z - 1.3), PI * 0.5, 1.2)
	B.box(bath, Vector3(0.06, 0.04, 0.5), Vector3(x0 + 0.1, y0 + 1.12, c.z - 0.55), M.darkwood)
	B.box(bath, Vector3(0.05, 0.42, 0.34), Vector3(x0 + 0.12, y0 + 0.9, c.z - 0.55), M.linen_teal)
	_look(room, "banho", 1, bath)
	var vanity: = Node3D.new()
	add_child(vanity)
	B.box(vanity, Vector3(0.5, 0.06, 1.1), Vector3(x0 + 0.3, y0 + 0.82, c.z - 1.3), M.stone)
	B.box(vanity, Vector3(0.46, 0.76, 1.04), Vector3(x0 + 0.3, y0 + 0.4, c.z - 1.3), M.darkwood)
	B.cyl(vanity, 0.2, 0.15, 0.12, Vector3(x0 + 0.32, y0 + 0.91, c.z - 1.3), M.ceramic, 24)
	B.model(vanity, "ceramic_vase_02", Vector3(x0 + 0.28, y0 + 0.85, c.z - 0.9), 0.0, 0.55)
	B.model(vanity, "wicker_basket_01", Vector3(x0 + 0.3, y0 + 0.85, c.z - 1.7), 0.0, 0.7)
	B.box(vanity, Vector3(0.04, 1.6, 0.9), Vector3(x1 - 0.2, y0 + 0.95, zf + 0.5), M.voile)
	_look(room, "banho", 2, vanity)



func _keep_parts(n: Node3D, keep: Array) -> void :
	var kept: = AABB()
	var first: = true
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var ok: = false
		for k in keep:
			if String(mi.name).ends_with(k):
				ok = true
		if not ok:
			mi.queue_free()
			continue
		var bb: AABB = mi.transform * mi.get_aabb()
		kept = bb if first else kept.merge(bb)
		first = false
	if not first:
		var ctr: = kept.get_center()
		for ch in n.get_children():
			if ch is Node3D:
				ch.position -= Vector3(ctr.x, 0, ctr.z)

func _upgrade_sign(i: int, c: Vector3, y0: float, x0: float) -> void :
	var p: = Vector3(x0 - 0.45, y0 + 1.35, c.z)
	B.box(self, Vector3(0.08, 0.7, 0.9), p, M.planks)
	B.label(self, "MELHORIAS", p + Vector3(-0.06, 0, 0), 28, Color(0.15, 0.35, 0.4), Color(1, 1, 1, 0.85), PI * 0.5)
	var it: = Interactable.new()
	var cs: = CollisionShape3D.new()
	var sh: = BoxShape3D.new()
	sh.size = Vector3(0.8, 1.2, 1.2)
	cs.shape = sh
	it.add_child(cs)
	it.position = p
	var room_id: = i
	it.prompt_fn = func() -> String:
		return tr("Melhorias do Bangalô %d (%s)") % [room_id + 1, Core.fmt_money(Core.nightly_rate(room_id))]
	it.action_fn = func() -> void :
		get_tree().call_group("hud", "open_office", "bangalo", room_id)
	add_child(it)

func apply_room_look(id: int) -> void :
	if id < 0 or id >= room_nodes.size() or id >= Core.rooms.size():
		return
	var look: Dictionary = room_nodes[id].get("look", {})
	var u: Dictionary = Core.rooms[id].upgrades
	for cat in look:
		var tier: = int(u.get(cat, 0))
		for e in look[cat]:
			var n: Node3D = e.n
			if is_instance_valid(n):
				n.visible = tier >= int(e.t) and tier <= int(e.get("max", 99))

func upgrade_visible(room_id: int, cat: String, tier: int) -> bool:
	if room_id < 0 or room_id >= room_nodes.size():
		return false
	for e in room_nodes[room_id].get("look", {}).get(cat, []):
		if int(e.t) == tier and is_instance_valid(e.n):
			return bool(e.n.visible)
	return false

func _ensure_bung_x(n: int) -> void :
	while BUNG_X.size() < n:
		BUNG_X.append(float(BUNG_X[-1]) - 8.0)

func _on_bungalow_built(id: int) -> void :
	_ensure_bung_x(id + 1)
	if room_nodes.size() == id:
		_bungalow(id, Vector3(float(BUNG_X[id]), 0, BUNG_Z))
	_on_room_changed(id)

func sync_bungalows() -> void :
	_ensure_bung_x(Core.rooms.size())
	while room_nodes.size() > Core.rooms.size():
		_drop_bungalow(room_nodes.size() - 1)
	while room_nodes.size() < Core.rooms.size():
		var i: = room_nodes.size()
		_bungalow(i, Vector3(float(BUNG_X[i]), 0, BUNG_Z))
	for r in Core.rooms:
		_on_room_changed(int(r.id))

func _drop_bungalow(i: int) -> void :
	var rn: Dictionary = room_nodes[i]
	var doomed: = {}
	for n in rn.get("nodes", []):
		doomed[n] = true
	var keep: = []
	for e in lanterns:
		if not doomed.has(e[0]):
			keep.append(e)
	lanterns = keep
	for n in rn.get("nodes", []):
		if is_instance_valid(n):
			n.queue_free()
	room_nodes.remove_at(i)

func _birds_spawn() -> void :
	var mat: = B.flat(Color(0.12, 0.12, 0.14))
	for i in 5:
		var mi: = MeshInstance3D.new()
		var qm: = QuadMesh.new()
		qm.size = Vector2(0.62, 0.14)
		mi.mesh = qm
		mi.material_override = mat
		add_child(mi)
		_birds.append({"n": mi, "a": float(i) * 1.2, "r": 7.0 + float(i) * 1.6, "y": 8.5 + float(i) * 0.35, "cx": -4.0 + float(i) * 3.0, "cz": -8.0})

func _weather_fx() -> void :
	rain = GPUParticles3D.new()
	rain.amount = 500
	rain.lifetime = 1.05
	rain.visibility_aabb = AABB(Vector3(-90, -8, -50), Vector3(220, 40, 180))
	var pm: = ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(70, 0.5, 50)
	pm.direction = Vector3(0.2, -1, 0.05)
	pm.spread = 6.0
	pm.initial_velocity_min = 16.0
	pm.initial_velocity_max = 24.0
	pm.gravity = Vector3(0, -8, 0)
	rain.process_material = pm
	var qm: = QuadMesh.new()
	qm.size = Vector2(0.025, 0.42)
	var rm: = B.flat(Color(0.75, 0.82, 0.9, 0.65), 0.2)
	rm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	rm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qm.material = rm
	rain.draw_pass_1 = qm
	rain.position = Vector3(20, 16, 8)
	rain.emitting = false
	rain.visible = false
	add_child(rain)
	_on_weather(Core.weather)

func _on_weather(kind: String) -> void :
	var wet: = kind == "rain"
	if rain:
		rain.emitting = wet
		rain.visible = wet
	if sand_mat:
		sand_mat.set_shader_parameter("rain_wet", 0.62 if wet else 0.0)

func _process(delta: float) -> void :
	var t: = Time.get_ticks_msec() * 0.001
	for b in _birds:
		var n: MeshInstance3D = b.n
		if not is_instance_valid(n):
			continue
		var a: float = t * 0.32 + float(b.a)
		n.position = Vector3(float(b.cx) + cos(a) * float(b.r), float(b.y) + sin(a * 2.0) * 0.35, float(b.cz) + sin(a) * float(b.r) * 0.55)
		n.rotation.y = - a
	for rn in room_nodes:
		var fan: Node3D = rn.get("fan")
		if fan and is_instance_valid(fan) and fan.visible:
			fan.rotation.y += delta * 2.2


func _bar() -> void :
	var c: = BAR_C
	B.platform(self, Vector3(7.6, 0.2, 7.6), c, M.deckwood, 0.5)
	var y0: = 0.1
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.cyl(self, 0.13, 0.16, 2.9, c + Vector3(sx * 2.8, y0 + 1.45, sz * 2.8), M.post, 8)
	B.hip_roof(self, c + Vector3(0, y0 + 2.9, 0), 7.4, 7.4, 3.0, M.thatch, 0.22)

	var ch: = 1.1
	var cm: Material = M.darkwood
	B.box(self, Vector3(0.6, ch, 4.4), c + Vector3(-2.0, y0 + ch * 0.5, 0), cm, true)
	B.box(self, Vector3(4.0, ch, 0.6), c + Vector3(0, y0 + ch * 0.5, -2.0), cm, true)
	B.box(self, Vector3(4.0, ch, 0.6), c + Vector3(0, y0 + ch * 0.5, 2.0), cm, true)
	B.box(self, Vector3(0.8, 0.07, 4.6), c + Vector3(-2.0, y0 + ch + 0.035, 0), M.oak)
	B.box(self, Vector3(4.4, 0.07, 0.8), c + Vector3(0, y0 + ch + 0.035, -2.0), M.oak)
	B.box(self, Vector3(4.4, 0.07, 0.8), c + Vector3(0, y0 + ch + 0.035, 2.0), M.oak)

	B.box(self, Vector3(0.4, 1.6, 3.0), c + Vector3(2.3, y0 + 0.8, 0), M.oak)
	var cols: = [Color(0.2, 0.5, 0.2), Color(0.6, 0.35, 0.1), Color(0.85, 0.85, 0.9), Color(0.5, 0.1, 0.15)]
	for i in 10:
		var gm: = B.flat(cols[i % cols.size()], 0.15, 0.1)
		B.cyl(self, 0.045, 0.05, 0.3, c + Vector3(2.25, y0 + 1.75, -1.3 + i * 0.28), gm, 8)
	B.model(self, "lambis_shell", c + Vector3(-2.0, y0 + ch + 0.07, 1.2), 0.3, 1.0)
	B.model(self, "wooden_bucket_01", c + Vector3(-2.0, y0 + ch + 0.07, -1.0), 0.0, 0.6)

	var coco: = B.flat(Color(0.4, 0.5, 0.15), 0.6)
	for k in 3:
		B.sphere(self, 0.12, c + Vector3(-0.6 + k * 0.3, y0 + ch + 0.17, -2.0), coco)

	var stools: = [Vector3(-3.0, 0, -0.9), Vector3(-3.0, 0, 0.9), Vector3(-0.9, 0, -3.0), Vector3(0.9, 0, -3.0), Vector3(-0.9, 0, 3.0), Vector3(0.9, 0, 3.0)]
	for s in stools:
		var face: = atan2( - s.x, - s.z)
		B.model(self, "bar_chair_round_01", c + s + Vector3(0, y0, 0), face, 1.0)
		bar_spots.append({"pos": c + s + Vector3(0, y0 + 0.28, 0), "rot": face, "anim": "Sitting_Idle_Loop", "busy": false})
	var top_y: = y0 + ch + 0.08
	_coconut_cup(self, c + Vector3(-0.85, top_y, -2.22))
	_petisco_plate(self, c + Vector3(0.85, top_y, -2.22))
	_coconut_cup(self, c + Vector3(-2.25, top_y, -0.55))
	_petisco_plate(self, c + Vector3(-2.25, top_y, 0.7))

	B.model(self, "outdoor_table_chair_set_01", c + Vector3(-5.5, 0, 3.5), 0.4, 1.0)
	_umbrella(c + Vector3(-5.5, 0, 3.5), 1.55, Color(0.95, 0.78, 0.35), true)
	_table_bites(c + Vector3(-5.5, 0.75, 3.5))
	B.model(self, "outdoor_table_chair_set_01", c + Vector3(-5.8, 0, -3.0), -0.3, 1.0)
	_umbrella(c + Vector3(-5.8, 0, -3.0), 1.55, Color(0.12, 0.55, 0.58))
	_table_bites(c + Vector3(-5.8, 0.75, -3.0))
	_cooler(c + Vector3(2.6, 0.1, -1.6), 0.4)
	_fruit_row(c + Vector3(-0.2, y0 + ch + 0.16, 2.0))
	_chalkboard(c + Vector3(3.15, y0 + 1.2, -2.2), 0.4, "CARDÁPIO", _menu_lines(Economy.BAR_MENU))
	B.model(self, "wooden_lantern_01", c + Vector3(0, y0 + 2.35, 0), 0.0, 1.0)
	_string_lights(c + Vector3(-2.5, y0 + 2.55, -2.5), c + Vector3(2.5, y0 + 2.55, -2.5), 7)
	_string_lights(c + Vector3(-2.5, y0 + 2.55, -2.5), c + Vector3(-2.5, y0 + 2.55, 2.5), 6)
	_string_lights(c + Vector3(-2.5, y0 + 2.55, 2.5), c + Vector3(2.5, y0 + 2.55, 2.5), 7)

	B.box(self, Vector3(3.2, 0.6, 0.08), c + Vector3(0, y0 + 2.55, -2.86), M.planks)
	B.label(self, "Bar do Coqueiro", c + Vector3(0, y0 + 2.55, -2.92), 64, Color(1.0, 0.95, 0.8), Color(0.25, 0.12, 0.02, 1.0), PI)
	B.label(self, "Bar do Coqueiro", c + Vector3(-2.92, y0 + 2.55, 0), 64, Color(1.0, 0.95, 0.8), Color(0.25, 0.12, 0.02, 1.0), - PI * 0.5)
	B.box(self, Vector3(0.08, 0.6, 3.2), c + Vector3(-2.86, y0 + 2.55, 0), M.planks)
	points["bartender"] = c + Vector3(1.0, y0, 0)
	var l: = OmniLight3D.new()
	l.position = c + Vector3(0, 2.6, 0)
	l.omni_range = 7.0
	l.light_color = Color(1.0, 0.75, 0.45)
	add_child(l)
	lanterns.append([l, null, 1.8, false])

func _bulb_mat() -> StandardMaterial3D:
	var m: StandardMaterial3D = B.flat(Color(1.0, 0.86, 0.45), 0.25).duplicate()
	m.emission_enabled = true
	m.emission = Color(1.0, 0.72, 0.32)
	m.emission_energy_multiplier = 1.6
	return m

func _string_lights(a: Vector3, b: Vector3, count: int) -> void :
	var mat: = _bulb_mat()
	for i in count:
		var t: = float(i + 1) / float(count + 1)
		var p: = a.lerp(b, t)
		p.y -= sin(t * PI) * 0.16
		B.sphere(self, 0.04, p, mat)

func _cooler(p: Vector3, rot: float) -> void :
	var n: = Node3D.new()
	n.position = p
	n.rotation.y = rot
	add_child(n)
	var body: = B.flat(Color(0.85, 0.9, 0.92), 0.35)
	var lid: = B.flat(Color(0.15, 0.45, 0.55), 0.4)
	B.box(n, Vector3(0.7, 0.42, 0.42), Vector3(0, 0.21, 0), body)
	var top: = B.box(n, Vector3(0.72, 0.06, 0.44), Vector3(0, 0.45, -0.02), lid)
	top.rotation.x = -0.5
	B.box(n, Vector3(0.16, 0.04, 0.08), Vector3(0, 0.28, 0.22), lid)

func _table_bites(p: Vector3) -> void :
	_coconut_cup(self, p + Vector3(-0.12, 0, 0.04))
	_petisco_plate(self, p + Vector3(0.14, 0, -0.05))

func _fruit_row(origin: Vector3) -> void :
	var cols: = [Color(0.95, 0.55, 0.1), Color(0.9, 0.2, 0.18), Color(0.75, 0.85, 0.2), Color(0.95, 0.75, 0.15)]
	for i in 4:
		B.sphere(self, 0.07, origin + Vector3(float(i) * 0.16, 0, 0), B.flat(cols[i], 0.45))

func _menu_lines(ids: Array) -> PackedStringArray:
	var lines: = PackedStringArray()
	for id in ids:
		var d: Dictionary = Economy.dish(str(id))
		lines.append("%s   %s" % [tr(str(d.name)), Core.fmt_money(int(d.price))])
	return lines

func _chalkboard(pos: Vector3, rot: float, title: String, lines: PackedStringArray) -> void :
	var n: = Node3D.new()
	n.position = pos
	n.rotation.y = rot
	add_child(n)
	B.box(n, Vector3(1.2, 1.5, 0.08), Vector3.ZERO, M.darkwood)
	B.box(n, Vector3(1.02, 1.28, 0.03), Vector3(0, 0, 0.04), B.flat(Color(0.1, 0.22, 0.18), 0.9))
	B.label(n, title, Vector3(0, 0.46, 0.07), 36, Color(0.95, 0.9, 0.7), Color(0, 0, 0, 0))
	var body: = ""
	for ln in lines:
		if body != "":
			body += "\n"
		body += ln
	B.label(n, body, Vector3(0, -0.08, 0.07), 26, Color(0.9, 0.96, 0.88), Color(0, 0, 0, 0))


func _beach_props() -> void :
	var spots: = [Vector3(-28, 0, -21), Vector3(-17, 0, -22), Vector3(-6, 0, -23), Vector3(4, 0, -22), Vector3(24, 0, -21), Vector3(33, 0, -22)]
	var tints: = [Color(0.86, 0.22, 0.18), Color(0.95, 0.78, 0.35), Color(0.95, 0.95, 0.9), Color(0.12, 0.55, 0.58), Color(0.2, 0.38, 0.72), Color(0.9, 0.45, 0.25)]
	for i in spots.size():
		var p: Vector3 = spots[i]
		_umbrella(p, 1.7, tints[i % tints.size()], i % 3 == 2)
		_lounger(p + Vector3(-0.85, 0, 0.7), PI + 0.18)
		_lounger(p + Vector3(0.85, 0, 0.7), PI - 0.12)
		if i % 2 == 0:
			B.box(self, Vector3(0.45, 0.03, 0.7), p + Vector3(0.2, 0.02, 1.7), M.linen_teal)
			_cooler(p + Vector3(1.7, 0, 1.5), 0.6)
		B.model(self, "wicker_basket_02", p + Vector3(-1.6, 0, 1.4), 0.8, 0.8)

	var j: = Node3D.new()
	j.position = Vector3(-9, -0.42, -30.2)
	j.rotation.y = 0.35
	add_child(j)
	for k in 6:
		B.cyl(j, 0.12, 0.12, 6.0, Vector3(-0.6 + k * 0.24, 0.12, 0), M.post, 8).rotation.x = PI * 0.5
	B.cyl(j, 0.06, 0.07, 5.5, Vector3(0, 2.8, 1.0), M.oak, 8)
	var sail: = MeshInstance3D.new()
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for v in [Vector3(0, 0.6, 1.0), Vector3(0, 5.4, 1.0), Vector3(0, 0.7, -2.4)]:
		st.set_normal(Vector3.RIGHT)
		st.set_uv(Vector2(v.z, v.y) * 0.3)
		st.add_vertex(v)
	sail.mesh = st.commit()
	var sm: = B.mat("rough_linen", 1.0, Color(1, 0.98, 0.94), 0.95).duplicate()
	sm.cull_mode = BaseMaterial3D.CULL_DISABLED
	sail.material_override = sm
	j.add_child(sail)
	B.wall(self, Vector3(2.0, 2.0, 6.5), Vector3(-9, 1.0, -30.2), 0.35)

	B.model(self, "lambis_shell", Vector3(-3, -0.2, -27.5), 1.2, 1.5)
	B.model(self, "wooden_bucket_01", Vector3(6, 0, -19.5), 0.0, 1.0)
	_shore_details()

func _shore_details() -> void :
	var rng: = RandomNumberGenerator.new()
	rng.seed = 19
	for i in 8:
		var x: = rng.randf_range(-40.0, 42.0)
		var z: = rng.randf_range(-30.5, -26.5)
		B.model(self, "lambis_shell", Vector3(x, _height(x, z), z), rng.randf() * TAU, rng.randf_range(0.7, 1.4))
	var rock: Material = M.stone
	for i in 9:
		var x: = rng.randf_range(-38.0, 40.0)
		var z: = rng.randf_range(-31.2, -27.2)
		var s: = rng.randf_range(0.12, 0.28)
		B.sphere(self, s, Vector3(x, _height(x, z) + s * 0.35, z), rock, Vector3(1.3, 0.7, 1.1))
	for i in 4:
		var x2: = -32.0 + float(i) * 16.0
		var log: = B.cyl(self, 0.08, 0.11, rng.randf_range(1.6, 2.6), Vector3(x2, _height(x2, -28.5) + 0.08, -28.5 + float(i) * 0.4), M.post, 8)
		log.rotation.z = PI * 0.5
		log.rotation.y = rng.randf_range(-0.4, 0.4)
	var shrubs: = ["shrub_01", "shrub_02", "shrub_03"]
	for i in 7:
		var x3: = rng.randf_range(-40.0, 40.0)
		var z3: = rng.randf_range(-18.0, -12.0)
		B.model(self, shrubs[i % 3], Vector3(x3, _height(x3, z3), z3), rng.randf() * TAU, rng.randf_range(0.45, 0.7))
	for spot in [Vector3(-42, 0, -16), Vector3(44, 0, -15), Vector3(-38, 0, 6)]:
		B.model(self, "island_tree_01", Vector3(spot.x, _height(spot.x, spot.z), spot.z), spot.x * 0.1, 0.9)

	var ball: = B.sphere(self, 0.16, Vector3(8.5, 0.16, -20.5), B.flat(Color(0.95, 0.35, 0.25), 0.4))
	ball.scale = Vector3(1.0, 1.0, 1.0)
	B.box(self, Vector3(0.7, 0.025, 1.3), Vector3(18.0, 0.02, -23.5), M.linen_sand)

func _palms() -> void :
	var excl: = [Rect2(-6, 12, 12, 8), Rect2(-10, -4, 20, 16), Rect2(-25.5, -12.5, 15, 9), Rect2(8.5, -18, 9, 10), 
		Rect2(-2, 18, 4, 30), Rect2(-12, -6, 3, 34), Rect2(-31, -26, 70, 7), Rect2(1, 25, 100, 10), Rect2(34, 16, 70, 40), Rect2(35, -16, 8, 42)]
	var rng: = RandomNumberGenerator.new()
	rng.seed = 42
	var placed: = []
	var tries: = 0
	while placed.size() < 34 and tries < 2000:
		tries += 1
		var p: = Vector2(rng.randf_range(-44, 44), rng.randf_range(-27, 44))
		var ok: = true
		for r in excl:
			if r.grow(1.5).has_point(p):
				ok = false
				break
		for q in placed:
			if q.distance_to(p) < 4.5:
				ok = false
				break
		if ok:
			placed.append(p)
	for i in placed.size():
		var pp: Vector2 = placed[i]
		Palm.spawn(self, Vector3(pp.x, _height(pp.x, pp.y) - 0.05, pp.y), i * 7 + 3)

	for k in 26:
		var x: = rng.randf_range(-110, 110)
		var z: = rng.randf_range(50, 95)
		if absf(x) < 50 and z < 52:
			continue
		Palm.spawn(self, Vector3(x, _height(x, z) - 0.1, z), 200 + k, false)
	for k in 12:
		var side: = -1.0 if k % 2 == 0 else 1.0
		var x2: = side * rng.randf_range(66, 110) if side < 0.0 else rng.randf_range(108, 126)
		var z2: = rng.randf_range(-20, 45)
		Palm.spawn(self, Vector3(x2, _height(x2, z2) - 0.1, z2), 300 + k, false)

const REDE_PAIRS: = [[Vector3(-27, 0, -14), Vector3(-23.4, 0, -15.0)], [Vector3(-6.5, 0, -17.5), Vector3(-2.9, 0, -18.2)], 
	[Vector3(19.5, 0, -16), Vector3(23.1, 0, -15.2)], [Vector3(27, 0, -4), Vector3(30.4, 0, -5.4)]]

func _redes() -> void :
	var stripes: = Image.create(64, 8, false, Image.FORMAT_RGB8)
	var cols: = [Color(0.95, 0.35, 0.15), Color(1.0, 0.8, 0.2), Color(0.1, 0.6, 0.6), Color(0.95, 0.95, 0.9), Color(0.85, 0.2, 0.3)]
	for x in 64:
		for y in 8:
			stripes.set_pixel(x, y, cols[(x / 6) % cols.size()])
	var stex: = ImageTexture.create_from_image(stripes)
	var rm: = StandardMaterial3D.new()
	rm.albedo_texture = stex
	rm.normal_enabled = true
	rm.normal_texture = B.nor("rough_linen")
	rm.uv2_scale = Vector3(4, 4, 1)
	rm.cull_mode = BaseMaterial3D.CULL_DISABLED
	rm.roughness = 0.95
	for i in REDE_PAIRS.size():
		var a: Vector3 = REDE_PAIRS[i][0]
		var b_: Vector3 = REDE_PAIRS[i][1]
		Palm.spawn(self, a, 500 + i * 2)
		Palm.spawn(self, b_, 501 + i * 2)
		var node: = Node3D.new()
		add_child(node)
		var dir: = (b_ - a)
		var L: = dir.length()
		var fwd: = dir.normalized()
		var side: = fwd.cross(Vector3.UP).normalized()
		var st: = SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var n: = 16
		var prev: = []
		var attach_h: = 1.45
		for k in n + 1:
			var t: = float(k) / n
			var p: = a + dir * t
			p.y = attach_h - sin(t * PI) * 0.85
			var wdt: = 0.15 + 0.5 * sin(t * PI)
			var l: = p - side * wdt + Vector3.UP * 0.12 * sin(t * PI)
			var r: = p + side * wdt + Vector3.UP * 0.12 * sin(t * PI)
			if k > 0:
				for v in [[prev[0], Vector2(t - 1.0 / n, 0)], [l, Vector2(t, 0)], [r, Vector2(t, 1)], [prev[0], Vector2(t - 1.0 / n, 0)], [r, Vector2(t, 1)], [prev[1], Vector2(t - 1.0 / n, 1)]]:
					st.set_normal(Vector3.UP)
					st.set_uv(v[1])
					st.add_vertex(v[0])
			prev = [l, r]
		var mi: = MeshInstance3D.new()
		mi.mesh = st.commit()
		mi.material_override = rm
		node.add_child(mi)

		var rope: = B.flat(Color(0.75, 0.65, 0.45), 0.9)
		for e in [[a, fwd], [b_, - fwd]]:
			var ep: Vector3 = e[0] + Vector3(0, attach_h + 0.15, 0) + e[1] * 0.25
			var rp: = B.cyl(node, 0.015, 0.015, 0.6, ep + e[1] * 0.25 - Vector3(0, 0.08, 0), rope, 5)
			rp.rotation = Vector3(0, 0, 0)
			rp.look_at_from_position(rp.position, ep + e[1] * 0.6 - Vector3(0, 0.2, 0), Vector3.UP)
			rp.rotate_object_local(Vector3.RIGHT, PI * 0.5)
		node.visible = false
		rede_nodes.append(node)

func _on_redes_changed(n: int) -> void :
	for i in rede_nodes.size():
		rede_nodes[i].visible = i < n

func _lantern_posts() -> void :
	var posts: = [Vector3(1.9, 0, 24), Vector3(-1.9, 0, 30), Vector3(1.9, 0, 36), Vector3(-1.9, 0, 42), 
		Vector3(-9.0, 0, 18), Vector3(-9.0, 0, 6), Vector3(-9.0, 0, -6), Vector3(-17.8, 0, -3.2), 
		Vector3(9.4, 0, -0.5), Vector3(9.4, 0, 10.5), Vector3(-9.4, 0, 10.5), Vector3(10.6, 0, -8.0), Vector3(1.3, 0, -14)]
	for p in posts:
		B.box(self, Vector3(0.14, 1.9, 0.14), p + Vector3(0, 0.95, 0), M.oak)
		B.box(self, Vector3(0.5, 0.06, 0.14), p + Vector3(0.18, 1.88, 0), M.oak)
		B.model(self, "wooden_lantern_01", p + Vector3(0.36, 1.45, 0), 0.0, 0.9)
		var glow: = MeshInstance3D.new()
		var sm: = SphereMesh.new()
		sm.radius = 0.07
		sm.height = 0.14
		glow.mesh = sm
		var gm: = StandardMaterial3D.new()
		gm.albedo_color = Color(1, 0.8, 0.5)
		gm.emission_enabled = true
		gm.emission = Color(1.0, 0.7, 0.35)
		gm.emission_energy_multiplier = 0.0
		glow.material_override = gm
		glow.position = p + Vector3(0.36, 1.62, 0)
		add_child(glow)
		var l: = OmniLight3D.new()
		l.position = p + Vector3(0.36, 1.6, 0)
		l.omni_range = 6.0
		l.light_color = Color(1.0, 0.72, 0.4)
		l.light_energy = 0.0
		add_child(l)
		lanterns.append([l, gm, 1.3, false])

func set_atmosphere(night: float, dawn: float, haze: Color = Color(0.62, 0.78, 0.9)) -> void :
	for m in mtn_mats:
		m.set_shader_parameter("dawn", dawn)
		m.set_shader_parameter("night", night)
		m.set_shader_parameter("haze_color", haze)
		m.set_shader_parameter("mist_color", haze.lightened(0.12))
	for tm in mtn_tree_mats:
		var mat: = tm as ShaderMaterial
		mat.set_shader_parameter("dawn", dawn)
		mat.set_shader_parameter("haze_color", haze)
		mat.set_shader_parameter("mist_color", haze.lightened(0.12))

func set_night(t: float) -> void :
	for e in lanterns:
		var k: float = maxf(t, 0.5) if e[3] else t
		if e[0] != null:
			var l: OmniLight3D = e[0]
			l.light_energy = e[2] * k
			l.visible = k > 0.01
		if e[1]:
			e[1].emission_energy_multiplier = 3.0 * t
	ocean_mat.set_shader_parameter("night", t * 0.8)
	if pool_floor_mat:
		pool_floor_mat.set_shader_parameter("day", 1.0 - t)

func _signs() -> void :
	var p: = Vector3(3.6, 0, 40)
	B.box(self, Vector3(0.15, 2.4, 0.15), p + Vector3(-1.4, 1.2, 0), M.post)
	B.box(self, Vector3(0.15, 2.4, 0.15), p + Vector3(1.4, 1.2, 0), M.post)
	B.box(self, Vector3(3.2, 1.0, 0.1), p + Vector3(0, 1.9, 0), M.planks)
	B.label(self, "Pousada\nMaré Alta", p + Vector3(0, 1.9, -0.07), 72, Color(0.1, 0.45, 0.5), Color(1, 1, 1, 0.9), PI)
	B.label(self, "Pousada\nMaré Alta", p + Vector3(0, 1.9, 0.07), 72, Color(0.1, 0.45, 0.5), Color(1, 1, 1, 0.9))


func _route_points() -> void :
	points["spawn"] = Vector3(0, 0, 45)
	points["gate"] = Vector3(0, 0, 21.5)
	for k in 4:
		points["queue%d" % k] = Vector3(0, 0.12, 16.6 + k * 1.25) if k < 3 else Vector3(0, 0, 21.2)
	points["desk_side"] = Vector3(3.8, 0.12, 16.6)
	points["desk_back"] = Vector3(3.8, 0.12, 13.4)
	points["north_door"] = Vector3(0, 0.12, 12.0)
	points["hub_nw"] = Vector3(-10.5, 0, 11.0)
	points["hub_sw"] = Vector3(-10.5, 0, -4.5)
	points["hub_w_exit"] = Vector3(-10.5, 0, 26.0)
	points["exit_join"] = Vector3(-1.2, 0, 27.0)
	points["deck_s"] = Vector3(-7.5, 0.12, -2.2)
	points["deck_se"] = Vector3(8.0, 0.12, -2.2)
	points["walk_bar"] = Vector3(10.6, 0.06, -8.6)

func route_to_room(room: int) -> Array:
	return [points.desk_side, points.desk_back, points.north_door, points.hub_nw, points.hub_sw, 
		points["room%d_front" % room], points["room%d_door" % room], points["room%d_in" % room]]

func route_room_to_hub(room: int) -> Array:
	return [points["room%d_door" % room], points["room%d_front" % room], points.hub_sw]

func route_hub_to_room(room: int) -> Array:
	return [points.hub_sw, points["room%d_front" % room], points["room%d_door" % room], points["room%d_in" % room]]

func route_hub_to_pool(spot: Dictionary) -> Array:
	var p: Vector3 = spot.pos
	if p.y < 0.0:
		return [points.deck_s, Vector3(p.x, 0.12, -0.6), Vector3(p.x, -0.6, 0.6), p]
	if p.x > 0.0:
		return [points.deck_s, Vector3(8.6, 0.12, -2.2), Vector3(8.6, 0.12, p.z), p]
	return [Vector3(-10.5, 0, p.z), Vector3(p.x - 0.8, 0.12, p.z), p]

func route_hub_to_bar(spot: Dictionary) -> Array:
	var p: Vector3 = spot.pos
	var near: = p + (p - BAR_C).normalized() * 0.9
	near.y = 0.1
	return [points.deck_s, points.deck_se, points.walk_bar, near, p]

func route_exit(room: int) -> Array:
	return [points["room%d_door" % room], points["room%d_front" % room], points.hub_sw, points.hub_nw, points.hub_w_exit, points.exit_join, points.spawn]


const VEG_EXCL: = [Rect2(-2.0, 16.0, 40.0, 30.0), Rect2(-3.0, 33.0, 113.0, 44.0), Rect2(20.0, -27.0, 40.0, 6.0), Rect2(-36.0, -26.0, 12.0, 12.0), Rect2(-5.8, 12, 11.6, 8.2), Rect2(-9.4, -3.4, 18.8, 14.8), Rect2(-25.6, -12.2, 15.2, 8.6), 
	Rect2(-1.8, 19, 3.6, 28), Rect2(-11.8, -5.8, 2.6, 33), Rect2(-24.8, -5.8, 15.2, 2.6), Rect2(-11.8, 24.6, 12.2, 2.8), 
	Rect2(8.4, -17.6, 9.2, 9.2), Rect2(8.0, -11.0, 4.2, 9.0), Rect2(-1.2, -17, 2.4, 15), Rect2(1.0, 38.5, 5.5, 3), 
	Rect2(1.0, 25.8, 98, 8.4), Rect2(41.5, 16.5, 56, 9.2), Rect2(39, 34, 58, 9.5), Rect2(65, 34, 20, 20), Rect2(36.4, -16, 3.2, 43), 
	Rect2(33, -17.5, 10, 9), Rect2(56, -24, 12, 9)]

func _veg_free(p: Vector2, margin: = 0.5) -> bool:
	for r in VEG_EXCL:
		if r.grow(margin).has_point(p):
			return false
	return true

func _cross_mesh(w: float, h: float, planes: int) -> ArrayMesh:
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in planes:
		var a: = PI * float(i) / planes
		var d: = Vector3(cos(a), 0, sin(a)) * w * 0.5
		var q: = [[ - d, Vector2(0, 1)], [d, Vector2(1, 1)], [d + Vector3(0, h, 0), Vector2(1, 0)], [ - d + Vector3(0, h, 0), Vector2(0, 0)]]
		for idx in [0, 1, 2, 0, 2, 3]:
			st.set_normal(Vector3.UP)
			st.set_uv(q[idx][1])
			st.add_vertex(q[idx][0])
	return st.commit()

func _scatter(mesh: Mesh, mat: Material, xforms: Array, vis_end: float, shadows: bool) -> void :
	var chunks: = {}
	for t in xforms:
		var key: = Vector2i(int(floor(t.origin.x / 24.0)), int(floor(t.origin.z / 24.0)))
		if not chunks.has(key):
			chunks[key] = []
		chunks[key].append(t)
	for key in chunks:
		var list: Array = chunks[key]
		var mm: = MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		mm.instance_count = list.size()
		for i in list.size():
			mm.set_instance_transform(i, list[i])
		var mmi: = MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.material_override = mat
		mmi.visibility_range_end = vis_end
		mmi.visibility_range_end_margin = 8.0
		mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		mmi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadows else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mmi)

func _vegetation() -> void :
	if not Quality.hd:
		return
	var rng: = RandomNumberGenerator.new()
	rng.seed = 777
	var noise: = FastNoiseLite.new()
	noise.seed = 9
	noise.frequency = 0.06

	var placed: = []
	var tries: = 0
	while placed.size() < 46 and tries < 4000:
		tries += 1
		var p: = Vector2(rng.randf_range(-46, 46), rng.randf_range(-24, 45))
		if not _veg_free(p, 1.6):
			continue
		var ok: = true
		for q in placed:
			if q.distance_to(p) < 3.8:
				ok = false
				break
		if ok:
			placed.append(p)
			Palm.spawn(self, Vector3(p.x, _height(p.x, p.y) - 0.05, p.y), 700 + placed.size() * 3)

	var gm: = ShaderMaterial.new()
	gm.shader = load("res://shaders/foliage.gdshader")
	gm.set_shader_parameter("tex", Toon.grass_tex())
	gm.set_shader_parameter("sway", 0.08)
	var grass: = []
	for i in 22000:
		var p: = Vector2(rng.randf_range(-62, 100), rng.randf_range(-22, 54))
		var n: = noise.get_noise_2d(p.x, p.y)
		var beach: = clampf((p.y + 22.0) / 10.0, 0.0, 1.0)
		if n < 0.05 + (1.0 - beach) * 0.35 or not _veg_free(p):
			continue
		var s: = rng.randf_range(0.6, 1.25) * (0.7 + n)
		var b: = Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.8, 1.3), s))
		grass.append(Transform3D(b, Vector3(p.x, _height(p.x, p.y) - 0.02, p.y)))
	_scatter(_cross_mesh(0.9, 0.75, 3), gm, grass, 70.0, false)

	var bm: = ShaderMaterial.new()
	bm.shader = load("res://shaders/foliage.gdshader")
	bm.set_shader_parameter("tex", Toon.bush_tex())
	bm.set_shader_parameter("sway", 0.03)
	var bushes: = []
	for r in VEG_EXCL:
		var per: = int((r.size.x + r.size.y) * 0.6)
		for k in per:
			var side: = rng.randi() % 4
			var u: = rng.randf()
			var p: Vector2
			match side:
				0: p = Vector2(r.position.x + u * r.size.x, r.position.y - 1.0)
				1: p = Vector2(r.position.x + u * r.size.x, r.end.y + 1.0)
				2: p = Vector2(r.position.x - 1.0, r.position.y + u * r.size.y)
				_: p = Vector2(r.end.x + 1.0, r.position.y + u * r.size.y)
			if not _veg_free(p, 0.3) or rng.randf() < 0.55 or p.y < -21.0:
				continue
			var s: = rng.randf_range(0.8, 1.4)
			bushes.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s, s)), Vector3(p.x, _height(p.x, p.y) - 0.05, p.y)))
	_scatter(_cross_mesh(1.7, 1.4, 4), bm, bushes, 110.0, true)
	print("vegetacao: capim=%d arbustos=%d coqueiros+=%d" % [grass.size(), bushes.size(), placed.size()])




const MTN_RIDGES: Array = [
	[-90.0, 116.0, 180.0, 124.0, 7.0, 11.0, 44.0], 
	[-120.0, 168.0, 220.0, 198.0, 22.0, 34.0, 78.0], 
	[-70.0, 205.0, 185.0, 238.0, 26.0, 40.0, 72.0], 
	[15.0, 240.0, 165.0, 278.0, 18.0, 30.0, 66.0], 
	[-160.0, 320.0, 40.0, 385.0, 70.0, 108.0, 125.0], 
	[15.0, 355.0, 195.0, 420.0, 78.0, 112.0, 115.0], 
	[-90.0, 430.0, 145.0, 485.0, 58.0, 88.0, 105.0], 
	[-120.0, 560.0, 160.0, 740.0, 240.0, 300.0, 210.0], 
	[-20.0, 620.0, 100.0, 780.0, 220.0, 270.0, 180.0], 
	[-210.0, 90.0, -250.0, -10.0, 48.0, 36.0, 55.0], 
	[-255.0, -5.0, -210.0, -70.0, 36.0, 28.0, 42.0], 
	[230.0, 80.0, 275.0, -15.0, 46.0, 34.0, 52.0], 
	[270.0, -10.0, 230.0, -75.0, 34.0, 26.0, 40.0], 
	[-230.0, 40.0, -200.0, -20.0, 30.0, 52.0, 16.0], 
	[250.0, 30.0, 280.0, -25.0, 28.0, 48.0, 16.0], 
]
const CROWN_COLS: Array[Color] = [
	Color(0.32, 0.46, 0.26), 
	Color(0.36, 0.52, 0.28), 
	Color(0.4, 0.56, 0.3), 
	Color(0.3, 0.44, 0.26), 
	Color(0.34, 0.5, 0.28), 
	Color(0.28, 0.4, 0.22), 
]

func _hermite(u: float) -> float:
	u = clampf(u, 0.0, 1.0)
	return u * u * (3.0 - 2.0 * u)

func _ridge(x: float, z: float, ax: float, az: float, bx: float, bz: float, ha: float, hb: float, width: float) -> float:
	var abx: = bx - ax
	var abz: = bz - az
	var t: = clampf(((x - ax) * abx + (z - az) * abz) / (abx * abx + abz * abz), 0.0, 1.0)
	var dx: = x - (ax + abx * t)
	var dz: = z - (az + abz * t)
	var d: = sqrt(dx * dx + dz * dz)
	return lerpf(ha, hb, t) * _hermite(1.0 - d / width)

func _mtn_mask(x: float, z: float) -> float:
	if z < -18.0 and x >= -40.0 and x <= 150.0:
		return 0.0
	# v0.7.1: a vila vai até z ~76; a serra começa depois
	if x >= -60.0 and x <= 124.0 and z < 84.0:
		return 0.0
	return 1.0

func _mtn(x: float, z: float) -> float:
	if _mtn_mask(x, z) <= 0.0:
		return 0.0
	var h: = 0.0
	for r in MTN_RIDGES:
		h = maxf(h, _ridge(x, z, float(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5]), float(r[6])))
	if h > 6.0:
		var cover: = _hermite((h - 6.0) / 22.0)
		h += sin(x * 0.018) * cos(z * 0.013) * 9.0 * cover
		h += sin(x * 0.041 + 1.7) * cos(z * 0.029) * 3.5 * cover
	return maxf(0.0, h)

func _mtn_material(aerial: float, far_fade: float) -> ShaderMaterial:
	var sm: = ShaderMaterial.new()
	sm.shader = load("res://shaders/mountain.gdshader")
	sm.set_shader_parameter("canopy_tex", B.tex("canopy"))
	sm.set_shader_parameter("canopy_nor", B.nor("canopy"))
	sm.set_shader_parameter("rock_tex", B.tex("rock_face"))
	sm.set_shader_parameter("rock_nor", B.nor("rock_face"))
	sm.set_shader_parameter("aerial", aerial)
	sm.set_shader_parameter("far_fade", far_fade)
	mtn_mats.append(sm)
	return sm

func _mtn_build_rect(x0: float, x1: float, z0: float, z1: float, step: float) -> ArrayMesh:
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)


	var nx: = int(ceil((x1 - x0) / step - 0.0001))
	var nz: = int(ceil((z1 - z0) / step - 0.0001))
	var added: = 0
	for iz in nz:
		for ix in nx:
			var xa: = x0 + float(ix) * step
			var za: = z0 + float(iz) * step
			var xb: = minf(xa + step, x1)
			var zb: = minf(za + step, z1)
			if xb - xa < 0.05 or zb - za < 0.05:
				continue
			var hs: Array[float] = [_mtn(xa, za), _mtn(xb, za), _mtn(xb, zb), _mtn(xa, zb)]
			var hmax: = maxf(maxf(hs[0], hs[1]), maxf(hs[2], hs[3]))
			if hmax < 1.2:
				continue
			var pts: Array[Vector3] = [
				_mtn_corner(xa, za, hs[0]), 
				_mtn_corner(xb, za, hs[1]), 
				_mtn_corner(xb, zb, hs[2]), 
				_mtn_corner(xa, zb, hs[3]), 
			]
			var norms: Array[Vector3] = [
				_mtn_up(xa, za), _mtn_up(xb, za), _mtn_up(xb, zb), _mtn_up(xa, zb), 
			]
			for idx in [0, 1, 2, 0, 2, 3]:
				var v: Vector3 = pts[idx]
				st.set_normal(norms[idx])
				st.set_uv(Vector2(v.x * 0.0104, v.z * 0.0104))
				st.add_vertex(v)
			added += 1
	if added == 0:
		return ArrayMesh.new()
	return st.commit()

func _mtn_up(x: float, z: float) -> Vector3:
	var e: = 4.0
	var hx: = _mtn(x + e, z) - _mtn(x - e, z)
	var hz: = _mtn(x, z + e) - _mtn(x, z - e)
	return Vector3( - hx, e * 2.0, - hz).normalized()

func _mtn_corner(x: float, z: float, h: float) -> Vector3:
	if h < 1.2:
		return Vector3(x, -2.2, z)
	if x >= -132.0 and x <= 132.0 and z >= -62.0 and z <= 112.0:
		var g: = _height(x, z)
		if h < g + 1.2:
			return Vector3(x, g - 0.6, z)
	return Vector3(x, h, z)

func _mtn_show(mesh: ArrayMesh, mat: Material, shadows: bool) -> int:
	if mesh.get_surface_count() == 0:
		return 0
	var mi: = MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadows else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.extra_cull_margin = 12.0
	add_child(mi)
	return mesh.get_faces().size() / 3

func _sphere_mid(v: Array[Vector3], cache: Dictionary, a: int, b: int) -> int:
	var lo: = mini(a, b)
	var hi: = maxi(a, b)
	var key: = lo * 1000 + hi
	if cache.has(key):
		return int(cache[key])
	v.append(((v[a] + v[b]) * 0.5).normalized())
	var i: = v.size() - 1
	cache[key] = i
	return i

func _crown_mesh() -> ArrayMesh:
	var t: = (1.0 + sqrt(5.0)) * 0.5
	var v: Array[Vector3] = [
		Vector3(-1, t, 0).normalized(), Vector3(1, t, 0).normalized(), 
		Vector3(-1, - t, 0).normalized(), Vector3(1, - t, 0).normalized(), 
		Vector3(0, -1, t).normalized(), Vector3(0, 1, t).normalized(), 
		Vector3(0, -1, - t).normalized(), Vector3(0, 1, - t).normalized(), 
		Vector3(t, 0, -1).normalized(), Vector3(t, 0, 1).normalized(), 
		Vector3( - t, 0, -1).normalized(), Vector3( - t, 0, 1).normalized(), 
	]
	var faces: Array = [
		[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], 
		[1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8], 
		[3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], 
		[4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1], 
	]
	var cache: = {}
	var nxt: Array = []
	for tri in faces:
		var a: = int(tri[0])
		var b: = int(tri[1])
		var c: = int(tri[2])
		var ab: = _sphere_mid(v, cache, a, b)
		var bc: = _sphere_mid(v, cache, b, c)
		var ca: = _sphere_mid(v, cache, c, a)
		nxt.append([a, ab, ca])
		nxt.append([b, bc, ab])
		nxt.append([c, ca, bc])
		nxt.append([ab, bc, ca])
	faces = nxt
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var blobs: Array = [
		[Vector3(0, 0.12, 0), Vector3(1.0, 0.58, 0.92)], 
		[Vector3(0.52, 0.02, 0.12), Vector3(0.62, 0.42, 0.56)], 
		[Vector3(-0.46, 0.04, -0.16), Vector3(0.55, 0.38, 0.5)], 
	]
	for blob in blobs:
		var center: Vector3 = blob[0]
		var sc: Vector3 = blob[1]
		for tri in faces:
			for k in 3:
				var p: Vector3 = v[int(tri[k])]
				var q: = Vector3(p.x * sc.x, p.y * sc.y, p.z * sc.z) + center
				var nrm: = Vector3(p.x / sc.x, p.y / sc.y, p.z / sc.z).normalized()
				st.set_normal(nrm)
				st.set_uv(Vector2(p.x * 0.5 + 0.5, p.z * 0.5 + 0.5))
				st.add_vertex(q)
	return st.commit()

func _mtn_slope_y(x: float, z: float) -> float:
	var e: = 4.0
	var hx: = _mtn(x + e, z) - _mtn(x - e, z)
	var hz: = _mtn(x, z + e) - _mtn(x, z - e)
	return (2.0 * e) / sqrt(hx * hx + 4.0 * e * e + hz * hz)

func _mtn_push_tree(xfs: Array[Transform3D], cols: Array[Color], rng: RandomNumberGenerator, x: float, z: float, crest: bool) -> bool:
	var h: = _mtn(x, z)
	if h < 4.0 or h > 180.0:
		return false
	if _mtn_slope_y(x, z) < 0.64:
		return false
	var s: = rng.randf_range(4.4, 6.6) if not crest else rng.randf_range(7.2, 10.5)
	var tint: Color = CROWN_COLS[rng.randi() % CROWN_COLS.size()]
	if rng.randf() < 0.016:
		s *= 0.4
		tint = Color(0.545, 0.392, 0.431) if rng.randf() < 0.55 else Color(0.62, 0.56, 0.4)
	var basis: = Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.9, 1.05), s * rng.randf_range(0.86, 1.08)))
	xfs.append(Transform3D(basis, Vector3(x, h - s * 0.2, z)))
	cols.append(tint)
	return true

func _mtn_trees() -> void :
	mtn_tree_mat = ShaderMaterial.new()
	mtn_tree_mat.shader = load("res://shaders/tree_card.gdshader")
	var mesh: = _crown_mesh()
	var near: Array[Transform3D] = []
	var near_c: Array[Color] = []
	var edge: Array[Transform3D] = []
	var edge_c: Array[Color] = []
	var rng: = RandomNumberGenerator.new()
	rng.seed = 463
	var cap_near: = 320
	var x: = -24.0
	while x < 186.0 and near.size() < cap_near:
		var z: = 100.0
		while z < 260.0 and near.size() < cap_near:
			if rng.randf() < 0.82:
				_mtn_push_tree(near, near_c, rng, x + rng.randf_range(-2.2, 2.2), z + rng.randf_range(-2.2, 2.2), false)
			z += 11.0
		x += 11.0
	var cap_edge: = 150
	for ri in [1, 2, 3, 4, 5, 6]:
		var r: Array = MTN_RIDGES[ri]
		var ax: = float(r[0])
		var az: = float(r[1])
		var bx: = float(r[2])
		var bz: = float(r[3])
		var length: = Vector2(bx - ax, bz - az).length()
		var steps: = int(length / 13.0)
		for i in steps:
			if edge.size() >= cap_edge:
				break
			var u: = float(i) / float(maxi(steps, 1))
			var px: = lerpf(ax, bx, u) + rng.randf_range(-3.0, 3.0)
			var pz: = lerpf(az, bz, u) + rng.randf_range(-3.0, 3.0)
			_mtn_push_tree(edge, edge_c, rng, px, pz, true)
	_mtn_cards("Copas", mesh, near, near_c, 0.22)
	_mtn_cards("CopasCrista", mesh, edge, edge_c, 0.55)
	print("serra: copas perto=%d crista=%d" % [near.size(), edge.size()])

func _mtn_cards(node_name: String, mesh: Mesh, xfs: Array[Transform3D], cols: Array[Color], aerial: float) -> void :
	if xfs.is_empty():
		return
	var mm: = MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = mesh
	mm.instance_count = xfs.size()
	for i in xfs.size():
		mm.set_instance_transform(i, xfs[i])
		mm.set_instance_custom_data(i, cols[i])
	var mi: = MultiMeshInstance3D.new()
	mi.name = node_name
	mi.multimesh = mm
	var mat: = mtn_tree_mat.duplicate() as ShaderMaterial
	mat.set_shader_parameter("aerial", aerial)
	mi.material_override = mat
	mtn_tree_mats.append(mat)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	mi.extra_cull_margin = 8.0
	add_child(mi)

func _mountains() -> void :
	var near_mat: = _mtn_material(0.08, 0.0)
	var mid_mat: = _mtn_material(0.38, 0.12)
	var far_mat: = _mtn_material(0.82, 0.5)
	var step_near: = 4.2 if Quality.hd else 4.8
	var tris: = 0
	var slabs: Array = [
		[-160.0, 50.0, 64.0, 170.0, step_near, 0], 
		[50.0, 230.0, 64.0, 170.0, step_near, 0], 
		[-160.0, 50.0, 170.0, 270.0, step_near, 0], 
		[50.0, 230.0, 170.0, 270.0, step_near, 0], 
		[-210.0, 50.0, 270.0, 370.0, 8.0, 1], 
		[50.0, 250.0, 270.0, 370.0, 8.0, 1], 
		[-210.0, 50.0, 370.0, 490.0, 8.0, 1], 
		[50.0, 250.0, 370.0, 490.0, 8.0, 1], 
	]
	for s in slabs:
		var mat: = near_mat if int(s[5]) == 0 else mid_mat
		tris += _mtn_show(_mtn_build_rect(float(s[0]), float(s[1]), float(s[2]), float(s[3]), float(s[4])), mat, int(s[5]) == 0)

	var fx: = -240.0
	while fx < 280.0:
		var fz: = 470.0
		while fz < 860.0:
			tris += _mtn_show(_mtn_build_rect(fx, minf(fx + 64.0, 280.0), fz, minf(fz + 64.0, 860.0), 12.0), far_mat, false)
			fz += 64.0
		fx += 64.0
	var step_side: = 8.0 if Quality.hd else 10.0
	tris += _mtn_show(_mtn_build_rect(-340.0, -150.0, -110.0, 200.0, step_side), mid_mat, false)
	tris += _mtn_show(_mtn_build_rect(190.0, 360.0, -110.0, 200.0, step_side), mid_mat, false)
	_mtn_trees()
	B.wall(self, Vector3(168, 18, 2.4), Vector3(30, 7.0, 63.0))
	B.wall(self, Vector3(2.4, 18, 78), Vector3(-64, 7.0, 24.0))
	B.wall(self, Vector3(2.4, 18, 78), Vector3(120, 7.0, 24.0))
	print("serra: tris encosta=%d" % tris)


# ------------------------------------------------------------------ v0.7: áreas e lotes à venda
## Roda um construtor e move tudo o que ele criou para um nó próprio, que pode ser ligado/desligado.
func _area(id: String, builder: Callable) -> Node3D:
	var before: = get_child_count()
	builder.call()
	var kids: = get_children().slice(before)
	var node: Node3D = areas.get(id)
	if node == null:
		node = Node3D.new()
		node.name = "Area_" + id
		add_child(node)
		areas[id] = node
	for k in kids:
		if k != node:
			k.reparent(node, false)
	return node

func _lot_post(parent: Node3D, p: Vector3) -> void :
	B.cyl(parent, 0.06, 0.07, 1.0, p + Vector3(0, 0.5, 0), M.get("post", B.flat(Color(0.55, 0.4, 0.25))), 6)

## Cerquinha de estacas com corda e uma placa "Lote à venda" com o nome e o preço da expansão.
func _lot(id: String, c: Vector3, size: Vector2, sign_pos: Vector3, sign_rot: float) -> Node3D:
	var n: = Node3D.new()
	n.name = "Lot_" + id
	add_child(n)
	var hx: = size.x * 0.5
	var hz: = size.y * 0.5
	var rope: = B.flat(Color(0.95, 0.55, 0.15), 0.8)
	var corners: = [Vector3(-hx, 0, -hz), Vector3(hx, 0, -hz), Vector3(hx, 0, hz), Vector3(-hx, 0, hz)]
	for i in 4:
		var a: Vector3 = c + corners[i]
		var b_: Vector3 = c + corners[(i + 1) % 4]
		var steps: = maxi(1, int(a.distance_to(b_) / 2.5))
		for k in steps:
			_lot_post(n, a.lerp(b_, float(k) / steps))
		var mid: = (a + b_) * 0.5 + Vector3(0, 0.8, 0)
		var seg: = B.box(n, Vector3(a.distance_to(b_), 0.05, 0.05), mid, rope)
		seg.rotation.y = - atan2(b_.z - a.z, b_.x - a.x)
	var board: = Node3D.new()
	board.position = sign_pos
	board.rotation.y = sign_rot
	n.add_child(board)
	var wood: = B.flat(Color(0.62, 0.42, 0.24), 0.9)
	for sx in [-1.0, 1.0]:
		B.box(board, Vector3(0.14, 2.2, 0.14), Vector3(sx * 1.25, 1.1, 0), wood)
	B.box(board, Vector3(3.0, 1.5, 0.12), Vector3(0, 1.75, 0), B.flat(Color(0.98, 0.93, 0.8), 0.9))
	B.box(board, Vector3(3.2, 0.16, 0.16), Vector3(0, 2.55, 0), B.flat(Color(0.9, 0.3, 0.22), 0.8))
	var e: Dictionary = Economy.EXPANSIONS[id]
	var t1: = B.label(board, tr("LOTE À VENDA"), Vector3(0, 2.25, 0.07), 70, Color(0.85, 0.22, 0.15), Color(1, 1, 1, 0.9))
	t1.set_meta("keep", true)
	B.label(board, tr(str(e.name)), Vector3(0, 1.85, 0.07), 56, Color(0.2, 0.15, 0.1), Color(1, 1, 1, 0.9))
	B.label(board, Core.fmt_money(int(e.cost)), Vector3(0, 1.45, 0.07), 74, Color(0.1, 0.5, 0.25), Color(1, 1, 1, 0.9))
	B.label(board, tr("Compre pelo celular (B)"), Vector3(0, 1.12, 0.07), 40, Color(0.35, 0.28, 0.2), Color(1, 1, 1, 0.9))
	lots[id] = n
	return n

func _build_lots() -> void :
	_lot("bar", BAR_C, Vector2(8.4, 8.4), BAR_C + Vector3(-4.6, 0, 1.0), - PI * 0.5)
	_lot("pousada", Vector3(0, 0, 16), Vector2(11.4, 8.4), Vector3(2.6, 0, 20.8), 0.0)
	var pool_lot: = _lot("pool", Vector3(0, 0, 4), Vector2(18.4, 13.4), Vector3(0, 0, 10.9), 0.0)
	# tampa o buraco da piscina com areia enquanto ela não existe
	var filler: = B.box(pool_lot, Vector3(POOL_MAX.x - POOL_MIN.x + 0.4, 0.4, POOL_MAX.y - POOL_MIN.y + 0.4), 
		Vector3((POOL_MIN.x + POOL_MAX.x) * 0.5, -0.19, (POOL_MIN.y + POOL_MAX.y) * 0.5), sand_patch_mat(), true)
	filler.name = "PoolFiller"

func sand_patch_mat() -> Material:
	return B.flat(Color(0.96, 0.86, 0.62), 0.95)

func _set_live(n: Node3D, on: bool) -> void :
	if n == null:
		return
	n.visible = on
	n.process_mode = Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED

func _on_expansion(_id: String) -> void :
	refresh_areas()

func refresh_areas() -> void :
	for id in areas:
		var owned: bool = Core.has(id)
		_set_live(areas[id], owned)
		_set_live(lots.get(id), not owned)
	get_tree().call_group("world_dyn", "on_areas_changed")
