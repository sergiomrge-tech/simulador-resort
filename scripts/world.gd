extends Node3D
## Constrói a pousada Maré Alta: praia, mar, recepção, piscina, bangalôs, bar e decoração.

const POOL_MIN := Vector2(-6, 0)     # buraco da piscina (x,z) alinhado à grade de 2 m
const POOL_MAX := Vector2(6, 8)
var BUNG_X: Array = [-14.0, -21.5]
const BUNG_Z := -8.0
const BAR_C := Vector3(13, 0, -13)
const SHORE_Z := -32.5
const WATER_Y := -0.3

var lanterns: Array = []          # [OmniLight3D, MeshInstance3D emissiva]
var room_nodes: Array = []        # por quarto: {clean:Node3D, dirty:{cama,toalhas,lixo}:Node3D, light}
var rede_nodes: Array = []
var desk: Interactable
var ocean_mat: ShaderMaterial
var pool_floor_mat: ShaderMaterial
var sand_mat: ShaderMaterial
var rain: GPUParticles3D
var _birds: Array = []
var points := {}                  # pontos nomeados para rotas
var pool_spots: Array = []        # [{pos, rot, anim}]
var bar_spots: Array = []
var guests_mgr: Node              # definido pelo main

var M := {}

func _ready() -> void:
	add_to_group("world")
	_materials()
	_ground()
	_ocean()
	_bounds()
	_paths()
	_reception()
	_pool()
	for i in BUNG_X.size():
		_bungalow(i, Vector3(BUNG_X[i], 0, BUNG_Z))
	_bar()
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
	for r in Core.rooms:
		_on_room_changed(r.id)
	_on_redes_changed(Core.redes)
	_birds_spawn()
	_weather_fx()

func _materials() -> void:
	M.plaster = B.mat("white_plaster", 0.5, Color(1, 1, 1), 0.9)
	M.terracotta = B.mat("white_plaster", 0.5, Color(0.66, 0.38, 0.26), 0.9)
	M.teal = B.mat("weathered_planks", 0.7, Color(0.15, 0.62, 0.62), 0.7)
	M.planks = B.mat("weathered_planks", 0.45, Color(1, 0.95, 0.88), 0.85)
	M.deckwood = B.mat("weathered_planks", 0.5, Color(0.85, 0.7, 0.55), 0.85)
	M.oak = B.mat("oak_wood_planks", 0.6, Color(1, 1, 1), 0.6)
	M.bamboo = B.mat("bamboo_wall", 0.45, Color(1, 0.97, 0.9), 0.85)
	M.linen = B.mat("rough_linen", 1.2, Color(0.97, 0.96, 0.93), 0.95)
	M.linen_teal = B.mat("rough_linen", 1.2, Color(0.35, 0.75, 0.78), 0.95)
	M.linen_sand = B.mat("rough_linen", 1.2, Color(0.9, 0.82, 0.68), 0.95)
	M.azulejo = B.mat("blue_floor_tiles_01", 0.5, Color(1, 1, 1), 0.35)
	M.stone = B.mat("light_stone", 0.55, Color(1, 1, 1), 0.75)
	M.terra_tiles = B.mat("patio_tiles", 0.55, Color(0.95, 0.9, 0.84), 0.75)
	var thatch := B.mat("reed_roof_04", 0.45, Color(1.25, 1.08, 0.8), 0.95).duplicate()
	thatch.cull_mode = BaseMaterial3D.CULL_DISABLED
	M.thatch = thatch
	M.post = B.mat("palm_tree_bark", 0.8, Color(0.8, 0.7, 0.6), 0.9)
	M.dark = B.flat(Color(0.12, 0.09, 0.07), 0.9)

# ------------------------------------------------------------------ chão
func _height(x: float, z: float) -> float:
	var h := 0.0
	if z < -24.0:
		var t := (-24.0 - z)
		h = -0.5 * clampf(t / 14.0, 0.0, 1.0) - maxf(0.0, t - 14.0) * 0.09
	# dunas ao fundo e nas laterais
	var far := maxf(0.0, z - 58.0) + maxf(0.0, x - 112.0) * 0.8 + maxf(0.0, -x - 62.0) * 0.8
	if far > 0.0:
		h += minf(far * 0.35, 9.0) * (0.75 + 0.25 * sin(x * 0.11) * cos(z * 0.13))
	return h

func _ground() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var step := 2.0
	var x0 := -130.0
	var x1 := 130.0
	var z0 := -60.0
	var z1 := 110.0
	var nx := int((x1 - x0) / step)
	var nz := int((z1 - z0) / step)
	for iz in nz:
		for ix in nx:
			var xa := x0 + ix * step
			var za := z0 + iz * step
			var xb := xa + step
			var zb := za + step
			# buraco da piscina
			if xa >= POOL_MIN.x and xb <= POOL_MAX.x and za >= POOL_MIN.y and zb <= POOL_MAX.y:
				continue
			var q := [Vector3(xa, _height(xa, za), za), Vector3(xb, _height(xb, za), za),
				Vector3(xb, _height(xb, zb), zb), Vector3(xa, _height(xa, zb), zb)]
			for idx in [0, 1, 2, 0, 2, 3]:
				var v: Vector3 = q[idx]
				var e := 0.5
				var n := Vector3(_height(v.x - e, v.z) - _height(v.x + e, v.z), 2.0 * e, _height(v.x, v.z - e) - _height(v.x, v.z + e)).normalized()
				st.set_normal(n)
				st.set_uv(Vector2(v.x, v.z))
				st.add_vertex(v)
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var sm := ShaderMaterial.new()
	sm.shader = load("res://shaders/ground.gdshader")
	sm.set_shader_parameter("dry_tex", B.tex("coast_sand_01"))
	sm.set_shader_parameter("dry_nor", B.nor("coast_sand_01"))
	sm.set_shader_parameter("wet_tex", B.tex("damp_beach_sand"))
	sm.set_shader_parameter("wet_nor", B.nor("damp_beach_sand"))
	sm.set_shader_parameter("wet_start", -25.0)
	sm.set_shader_parameter("wet_end", -31.0)
	sm.set_shader_parameter("rain_wet", 0.0)
	sand_mat = sm
	mi.material_override = sm
	mi.name = "Ground"
	add_child(mi)
	# colisão do chão (plano em terra, sem a piscina)
	B.wall(self, Vector3(240, 1, 84), Vector3(20, -0.5, 50))          # z 8..92
	B.wall(self, Vector3(240, 1, 24), Vector3(20, -0.5, -12))         # z -24..0
	B.wall(self, Vector3(94, 1, 8), Vector3(-53, -0.5, 4))
	B.wall(self, Vector3(134, 1, 8), Vector3(73, -0.5, 4))
	var slope := B.wall(self, Vector3(240, 1, 7.2), Vector3(0, -0.5 - 0.22, -27.5))  # rampa da praia
	slope.rotation.x = -atan2(0.43, 7.0)

func _ocean() -> void:
	var pm := PlaneMesh.new()
	pm.size = Vector2(420, 220)
	pm.subdivide_width = 280 if Quality.hd else 140
	pm.subdivide_depth = 180 if Quality.hd else 90
	var mi := MeshInstance3D.new()
	mi.mesh = pm
	mi.position = Vector3(0, WATER_Y, SHORE_Z - 110 + 4)
	ocean_mat = ShaderMaterial.new()
	ocean_mat.shader = load("res://shaders/ocean_hd.gdshader" if Quality.hd else "res://shaders/ocean.gdshader")
	ocean_mat.set_shader_parameter("shore_z", SHORE_Z)
	mi.material_override = ocean_mat
	mi.name = "Ocean"
	add_child(mi)

func _bounds() -> void:
	B.wall(self, Vector3(160, 4, 1), Vector3(28, 1.5, -30.5))   # não entrar no mar
	B.wall(self, Vector3(160, 4, 1), Vector3(28, 1.5, 56))
	B.wall(self, Vector3(1, 4, 90), Vector3(-48, 1.5, 12))
	B.wall(self, Vector3(1, 4, 90), Vector3(104, 1.5, 12))

func _strip(a: Vector2, b_: Vector2, w: float, m: Material, y := 0.025) -> void:
	var d := b_ - a
	var mid := (a + b_) * 0.5
	var mi := B.box(self, Vector3(w, 0.05, d.length()), Vector3(mid.x, y, mid.y), m)
	mi.rotation.y = atan2(d.x, d.y)

func _paths() -> void:
	_strip(Vector2(0, 19.5), Vector2(0, 46), 2.6, M.terra_tiles)          # entrada
	_strip(Vector2(-10.5, 11.5), Vector2(-10.5, 26), 2.0, M.stone)        # lateral oeste
	_strip(Vector2(-11.5, 26), Vector2(0, 26), 2.0, M.stone)
	_strip(Vector2(-10.5, 11.5), Vector2(-10.5, -4.5), 2.0, M.stone)
	_strip(Vector2(-23.5, -4.5), Vector2(-9.5, -4.5), 2.0, M.stone)
	# passarela de madeira até o bar e até a areia
	_strip(Vector2(9.0, -2.5), Vector2(11.2, -10.2), 1.6, M.deckwood, 0.06)
	_strip(Vector2(0, -3.0), Vector2(0, -16), 1.6, M.deckwood, 0.06)

# ------------------------------------------------------------------ recepção
func _wall_x(x0: float, x1: float, z: float, h: float, gaps: Array, base_y := 0.0) -> void:
	# parede ao longo de X com aberturas [[gx0,gx1,gy0,gy1],...]
	var segs := [[x0, x1]]
	for g in gaps:
		var nsegs := []
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
		if g[2] > 0.01:   # parapeito (janela)
			_wall_piece(Vector3(cx, base_y, z), gw, g[2], false)
			B.box(self, Vector3(gw + 0.2, 0.08, 0.4), Vector3(cx, base_y + g[2], z), M.teal)
		if g[3] < h:      # verga
			var mi := B.box(self, Vector3(gw, h - g[3], 0.26), Vector3(cx, base_y + (h + g[3]) * 0.5, z), M.plaster)
			mi.name = "lintel"
		# moldura turquesa
		B.box(self, Vector3(gw + 0.24, 0.12, 0.32), Vector3(cx, base_y + g[3] + 0.06, z), M.teal)
		B.box(self, Vector3(0.12, g[3] - g[2], 0.32), Vector3(g[0] - 0.06, base_y + (g[2] + g[3]) * 0.5, z), M.teal)
		B.box(self, Vector3(0.12, g[3] - g[2], 0.32), Vector3(g[1] + 0.06, base_y + (g[2] + g[3]) * 0.5, z), M.teal)

func _wall_z(z0: float, z1: float, x: float, h: float, gaps: Array, base_y := 0.0) -> void:
	var holder := Node3D.new()
	holder.position = Vector3(x, 0, 0)
	holder.rotation.y = PI * 0.5
	add_child(holder)
	# reutiliza a lógica de X em um nó rotacionado
	var saved := get_child_count()
	_wall_x(-z1, -z0, 0.0, h, gaps.map(func(g): return [-g[1], -g[0], g[2], g[3]]), base_y)
	var added := []
	for i in range(saved, get_child_count()):
		added.append(get_child(i))
	for n in added:
		var gt: Transform3D = n.transform
		remove_child(n)
		holder.add_child(n)
		n.transform = gt

func _wall_piece(pos: Vector3, w: float, h: float, _unused: bool) -> void:
	B.box(self, Vector3(w, h, 0.26), pos + Vector3(0, h * 0.5, 0), M.plaster, true)
	# rodapé terracota
	B.box(self, Vector3(w + 0.02, minf(0.45, h), 0.3), pos + Vector3(0, minf(0.45, h) * 0.5, 0), M.terracotta)

func _reception() -> void:
	var cx := 0.0
	var cz := 16.0
	var y0 := 0.12
	B.platform(self, Vector3(10.6, 0.24, 7.6), Vector3(cx, 0.0, cz), M.stone, 0.5)
	B.box(self, Vector3(9.6, 0.02, 6.6), Vector3(cx, y0 + 0.011, cz), M.azulejo)
	var h := 3.3
	_wall_x(-5, 5, 19.5, h, [[-1.4, 1.4, 0.0, 2.6], [-4.0, -2.4, 1.0, 2.3], [2.4, 4.0, 1.0, 2.3]], y0)
	_wall_x(-5, 5, 12.5, h, [[-1.6, 1.6, 0.0, 2.7], [-4.2, -2.6, 1.0, 2.3], [2.6, 4.2, 1.0, 2.3]], y0)
	_wall_z(12.5, 19.5, -5, h, [[14.5, 17.5, 1.0, 2.3]], y0)
	_wall_z(12.5, 19.5, 5, h, [[14.5, 17.5, 1.0, 2.3]], y0)
	# pilares de canto
	for sx in [-5.0, 5.0]:
		for sz in [12.5, 19.5]:
			B.box(self, Vector3(0.4, h, 0.4), Vector3(sx, y0 + h * 0.5, sz), M.plaster)
	# teto de madeira + telhado de sapê alto
	B.box(self, Vector3(10.2, 0.08, 7.2), Vector3(cx, y0 + h + 0.04, cz), M.planks)
	B.hip_roof(self, Vector3(cx, y0 + h + 0.08, cz), 13.0, 10.0, 4.2, M.thatch, 0.25)
	# balcão
	var desk_z := 15.5
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
	# prateleira de chaves atrás do balcão
	B.box(self, Vector3(2.4, 1.2, 0.3), Vector3(-2.2, y0 + 1.5, 12.8), M.oak)
	for i in 4:
		B.box(self, Vector3(0.18, 0.25, 0.04), Vector3(-3.0 + i * 0.5, y0 + 1.6, 12.98), M.teal)
	B.label(self, "RECEPÇÃO", Vector3(0, y0 + 2.95, 19.66), 90, Color(0.1, 0.45, 0.48), Color(1, 1, 1, 0.9))
	desk = Interactable.new()
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = Vector3(5.2, 1.4, 1.2)
	cs.shape = sh
	desk.add_child(cs)
	desk.position = Vector3(0, y0 + 0.8, desk_z)
	desk.name = "Desk"
	add_child(desk)
	# luz interna
	var l := OmniLight3D.new()
	l.position = Vector3(0, y0 + 2.9, cz)
	l.omni_range = 8.0
	l.light_energy = 0.0
	l.light_color = Color(1.0, 0.82, 0.6)
	add_child(l)
	lanterns.append([l, null, 1.6, true])

# ------------------------------------------------------------------ piscina
func _pool() -> void:
	var depth := 1.4
	var wx := POOL_MAX.x - POOL_MIN.x
	var wz := POOL_MAX.y - POOL_MIN.y
	var c := Vector3((POOL_MIN.x + POOL_MAX.x) * 0.5, 0, (POOL_MIN.y + POOL_MAX.y) * 0.5)
	# deck de pedra clara em volta (moldura)
	var deck_y := 0.06
	B.box(self, Vector3(18, 0.12, 3), Vector3(0, deck_y, -1.5), M.stone)
	B.box(self, Vector3(18, 0.12, 3), Vector3(0, deck_y, 9.5), M.stone)
	B.box(self, Vector3(3, 0.12, 8), Vector3(-7.5, deck_y, 4), M.stone)
	B.box(self, Vector3(3, 0.12, 8), Vector3(7.5, deck_y, 4), M.stone)
	# borda (coping)
	var coping := B.flat(Color(0.93, 0.9, 0.84), 0.6)
	B.box(self, Vector3(wx + 0.6, 0.16, 0.3), Vector3(c.x, 0.1, POOL_MIN.y - 0.15), coping)
	B.box(self, Vector3(wx + 0.6, 0.16, 0.3), Vector3(c.x, 0.1, POOL_MAX.y + 0.15), coping)
	B.box(self, Vector3(0.3, 0.16, wz), Vector3(POOL_MIN.x - 0.15, 0.1, c.z), coping)
	B.box(self, Vector3(0.3, 0.16, wz), Vector3(POOL_MAX.x + 0.15, 0.1, c.z), coping)
	# bacia de azulejos (no PC com cáusticas animadas)
	var basin: Material = M.azulejo
	if Quality.hd:
		pool_floor_mat = ShaderMaterial.new()
		pool_floor_mat.shader = load("res://shaders/pool_floor.gdshader")
		pool_floor_mat.set_shader_parameter("albedo_tex", B.tex("blue_floor_tiles_01"))
		pool_floor_mat.set_shader_parameter("normal_tex", B.nor("blue_floor_tiles_01"))
		basin = pool_floor_mat
	B.box(self, Vector3(wx, 0.1, wz), Vector3(c.x, -depth - 0.05, c.z), basin)
	B.box(self, Vector3(wx, depth, 0.1), Vector3(c.x, -depth * 0.5, POOL_MIN.y + 0.05), basin)
	B.box(self, Vector3(wx, depth, 0.1), Vector3(c.x, -depth * 0.5, POOL_MAX.y - 0.05), basin)
	B.box(self, Vector3(0.1, depth, wz), Vector3(POOL_MIN.x + 0.05, -depth * 0.5, c.z), basin)
	B.box(self, Vector3(0.1, depth, wz), Vector3(POOL_MAX.x - 0.05, -depth * 0.5, c.z), basin)
	# água
	var water := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(wx - 0.1, wz - 0.1)
	pm.subdivide_width = 24
	pm.subdivide_depth = 16
	water.mesh = pm
	water.position = Vector3(c.x, -0.12, c.z)
	var wm := ShaderMaterial.new()
	wm.shader = load("res://shaders/pool_hd.gdshader" if Quality.hd else "res://shaders/pool.gdshader")
	water.material_override = wm
	add_child(water)
	# mureta invisível (não cair na piscina)
	B.wall(self, Vector3(wx, 2, 0.2), Vector3(c.x, 1, POOL_MIN.y))
	B.wall(self, Vector3(wx, 2, 0.2), Vector3(c.x, 1, POOL_MAX.y))
	B.wall(self, Vector3(0.2, 2, wz), Vector3(POOL_MIN.x, 1, c.z))
	B.wall(self, Vector3(0.2, 2, wz), Vector3(POOL_MAX.x, 1, c.z))
	B.wall(self, Vector3(wx, 1, wz), Vector3(c.x, -0.5, c.z))
	# espreguiçadeiras e boia
	for side in [-1.0, 1.0]:
		for i in 3:
			var p := Vector3(side * 7.6, 0.12, 1.2 + i * 2.6)
			_lounger(p, -side * PI * 0.5)
			pool_spots.append({"pos": p + Vector3(0, 0.3, 0), "rot": -side * PI * 0.5 + PI, "anim": "Sitting_Idle_Loop", "busy": false})
	for sp in [Vector3(-3, -0.4, 3), Vector3(2.5, -0.4, 5.5), Vector3(0.5, -0.4, 2.0)]:
		pool_spots.append({"pos": sp, "rot": randf() * TAU, "anim": "Swim_Idle_Loop", "busy": false})
	B.model(self, "lifebuoy", Vector3(6.6, 0.95, 8.65), 0.0, 1.0).rotation.x = -PI * 0.5
	B.box(self, Vector3(0.12, 1.4, 0.12), Vector3(6.6, 0.75, 8.9), M.planks)
	# guarda-sóis da piscina
	for p in [Vector3(-7.6, 0.12, 2.5), Vector3(7.6, 0.12, 2.5), Vector3(-7.6, 0.12, 5.1), Vector3(7.6, 0.12, 5.1)]:
		_umbrella(p, 1.4)

func _lounger(p: Vector3, rot: float) -> void:
	var n := Node3D.new()
	n.position = p
	n.rotation.y = rot
	add_child(n)
	B.box(n, Vector3(0.7, 0.08, 1.9), Vector3(0, 0.3, 0), M.oak)
	B.box(n, Vector3(0.66, 0.08, 0.7), Vector3(0, 0.55, -0.85), M.oak).rotation.x = -0.7
	B.box(n, Vector3(0.62, 0.06, 1.3), Vector3(0, 0.37, 0.25), M.linen_teal)
	for sx in [-0.3, 0.3]:
		for sz in [-0.8, 0.8]:
			B.box(n, Vector3(0.06, 0.3, 0.06), Vector3(sx, 0.15, sz), M.oak)

func _umbrella(p: Vector3, r: float) -> void:
	B.cyl(self, 0.04, 0.05, 2.4, p + Vector3(0, 1.2, 0), M.oak, 8)
	var top := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.02
	cm.bottom_radius = r
	cm.height = 0.7
	cm.radial_segments = 14
	top.mesh = cm
	top.material_override = M.thatch
	top.position = p + Vector3(0, 2.45, 0)
	add_child(top)

# ------------------------------------------------------------------ bangalôs
func _bungalow(i: int, c: Vector3) -> void:
	var _child_mark := get_child_count()
	var y0 := 0.25
	var w := 5.6
	var d := 5.0
	# plataforma de madeira (com varanda voltada para o mar, -Z)
	B.platform(self, Vector3(w + 0.6, 0.5, d + 2.8), Vector3(c.x, 0.0, c.z - 1.1), M.deckwood, 0.55)
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.box(self, Vector3(0.22, 0.5, 0.22), Vector3(c.x + sx * (w * 0.5 + 0.2), 0.05, c.z - 1.1 + sz * (d * 0.5 + 1.3)), M.post)
	var h := 2.7
	var x0 := c.x - w * 0.5
	var x1 := c.x + w * 0.5
	var zf := c.z - d * 0.5   # frente (mar)
	var zb := c.z + d * 0.5   # fundos (porta)
	_bwall_x(x0, x1, zb, h, [[c.x + 0.8, c.x + 2.0, 0.0, 2.15]], y0)
	_bwall_x(x0, x1, zf, h, [[c.x - 1.6, c.x + 1.6, 0.8, 2.1]], y0)
	_bwall_z(zf, zb, x0, h, [[c.z - 0.6, c.z + 0.6, 1.0, 2.0]], y0)
	_bwall_z(zf, zb, x1, h, [], y0)
	for sx in [x0, x1]:
		for sz in [zf, zb]:
			B.cyl(self, 0.12, 0.14, h, Vector3(sx, y0 + h * 0.5, sz), M.post, 8)
	B.box(self, Vector3(w, 0.06, d), Vector3(c.x, y0 + h, c.z), M.planks)
	B.hip_roof(self, Vector3(c.x, y0 + h + 0.03, c.z - 0.7), w + 2.4, d + 3.8, 3.8, M.thatch, 0.22)
	# varanda: cadeiras e lanterna
	B.model(self, "wooden_stool_01", Vector3(c.x - 1.5, y0, zf - 1.3), 0.3, 1.0)
	B.model(self, "side_table_01", Vector3(c.x + 1.6, y0, zf - 1.2), 0.0, 1.0)
	B.model(self, "wooden_bucket_01", Vector3(c.x + 2.4, y0, zb + 0.6), 0.0, 1.0)
	# interior: cama de casal
	var room := {"clean": Node3D.new(), "dirty": {}, "light": null}
	var bed_c := Vector3(c.x - 1.2, y0, c.z - 0.2)
	B.box(self, Vector3(1.8, 0.35, 2.2), bed_c + Vector3(0, 0.175, 0), M.oak, true)
	B.box(self, Vector3(1.9, 1.0, 0.1), bed_c + Vector3(0, 0.5, 1.12), M.oak)       # cabeceira
	B.box(self, Vector3(1.72, 0.22, 2.1), bed_c + Vector3(0, 0.46, 0), M.linen)       # colchão
	B.model(self, "side_table_01", Vector3(c.x - 2.55, y0, c.z + 1.4), 0.0, 1.0)
	B.model(self, "wooden_lantern_01", Vector3(c.x - 2.55, y0 + 0.62, c.z + 1.4), 0.0, 0.8)
	B.model(self, "potted_plant_02", Vector3(c.x + 2.2, y0, c.z - 2.0), 0.0, 0.9)
	# estado limpo
	var cl: Node3D = room.clean
	add_child(cl)
	B.box(cl, Vector3(1.76, 0.04, 1.5), bed_c + Vector3(0, 0.59, -0.3), M.linen_sand)
	for sx in [-0.42, 0.42]:
		B.box(cl, Vector3(0.62, 0.14, 0.4), bed_c + Vector3(sx, 0.66, 0.82), M.linen)
	B.box(cl, Vector3(0.5, 0.08, 0.32), bed_c + Vector3(-0.3, 0.65, -0.7), M.linen_teal)
	B.box(cl, Vector3(0.5, 0.08, 0.32), bed_c + Vector3(0.3, 0.65, -0.7), M.linen_teal)
	# estado sujo: cama bagunçada / toalhas no chão / lixo
	var dc := Node3D.new()
	add_child(dc)
	B.box(dc, Vector3(1.6, 0.05, 1.3), bed_c + Vector3(0.15, 0.6, -0.1), M.linen_sand).rotation = Vector3(0.05, 0.4, 0.1)
	B.box(dc, Vector3(0.9, 0.12, 0.7), bed_c + Vector3(-0.4, 0.66, -0.5), M.linen_sand).rotation = Vector3(0.3, -0.5, 0.2)
	B.box(dc, Vector3(0.62, 0.14, 0.4), bed_c + Vector3(0.5, 0.64, 0.2), M.linen).rotation = Vector3(0.1, 0.9, 0.3)
	B.box(dc, Vector3(0.62, 0.14, 0.4), bed_c + Vector3(-1.05, 0.08, 0.6), M.linen).rotation = Vector3(0.0, 0.3, 0.1)
	var dt := Node3D.new()
	add_child(dt)
	B.box(dt, Vector3(0.8, 0.03, 0.5), Vector3(c.x + 0.4, y0 + 0.02, c.z - 1.6), M.linen_teal).rotation.y = 0.7
	B.box(dt, Vector3(0.6, 0.06, 0.45), Vector3(c.x + 0.7, y0 + 0.04, c.z - 1.3), M.linen_teal).rotation = Vector3(0.1, -0.3, 0.05)
	B.box(dt, Vector3(0.7, 0.03, 0.5), Vector3(c.x - 0.1, y0 + 0.02, zf - 1.0), M.linen_teal).rotation.y = 1.9
	var dl := Node3D.new()
	add_child(dl)
	var red := B.flat(Color(0.75, 0.1, 0.08), 0.35, 0.6)
	var paper := B.flat(Color(0.95, 0.95, 0.9), 0.9)
	B.cyl(dl, 0.033, 0.033, 0.12, Vector3(c.x + 1.2, y0 + 0.06, c.z + 1.6), red, 10)
	B.cyl(dl, 0.033, 0.033, 0.12, Vector3(c.x + 1.5, y0 + 0.033, c.z + 1.2), red, 10).rotation.z = PI * 0.5
	B.sphere(dl, 0.07, Vector3(c.x + 0.9, y0 + 0.06, c.z + 1.3), paper)
	B.sphere(dl, 0.06, Vector3(c.x + 1.7, y0 + 0.05, c.z + 1.8), paper)
	B.sphere(dl, 0.12, Vector3(c.x + 0.6, y0 + 0.1, c.z + 1.8), B.flat(Color(0.35, 0.23, 0.12), 0.9), Vector3(1, 0.8, 1))  # coco vazio
	B.sphere(dl, 0.18, Vector3(c.x + 1.9, y0 + 0.16, c.z + 0.6), B.flat(Color(0.1, 0.1, 0.1), 0.3), Vector3(1, 1.3, 1))  # saco de lixo
	room.dirty = {"cama": dc, "toalhas": dt, "lixo": dl}
	# interagíveis
	var items := {"cama": [bed_c + Vector3(0, 0.6, 0), Vector3(1.9, 0.9, 2.2), "Arrumar a cama"],
		"toalhas": [Vector3(c.x + 0.4, y0 + 0.3, c.z - 1.4), Vector3(1.6, 0.8, 1.6), "Recolher as toalhas"],
		"lixo": [Vector3(c.x + 1.3, y0 + 0.3, c.z + 1.3), Vector3(1.6, 0.8, 1.4), "Jogar o lixo fora"]}
	room.inter = {}
	for k in items:
		var it := Interactable.new()
		var cs := CollisionShape3D.new()
		var sh := BoxShape3D.new()
		sh.size = items[k][1]
		cs.shape = sh
		it.add_child(cs)
		it.position = items[k][0]
		var room_id := i
		var key: String = k
		var txt: String = items[k][2]
		it.prompt_fn = func() -> String:
			var r: Dictionary = Core.rooms[room_id]
			if r.state == "dirty" and r.dirty.get(key, false):
				return "%s (%s)" % [tr(txt), tr("Bangalô %d") % (room_id + 1)]
			return ""
		it.action_fn = func() -> void:
			if Core.clean_item(room_id, key):
				get_tree().call_group("audio", "sfx", "clean")
		add_child(it)
		room.inter[k] = it
	# luz interna e da varanda
	var l := OmniLight3D.new()
	l.position = Vector3(c.x, y0 + 2.3, c.z)
	l.omni_range = 5.5
	l.light_color = Color(1.0, 0.78, 0.5)
	add_child(l)
	lanterns.append([l, null, 1.2, true])
	B.label(self, "BANGALÔ %d" % (i + 1), Vector3(c.x + 1.4, y0 + 2.45, zb + 0.15), 48, Color(1, 0.95, 0.85), Color(0.2, 0.12, 0.05, 0.9))
	points["room%d_door" % i] = Vector3(c.x + 1.4, 0.25, zb + 1.2)
	points["room%d_in" % i] = Vector3(c.x + 1.4, 0.25, zb - 1.0)
	points["room%d_front" % i] = Vector3(c.x + 1.4, 0, -4.5)
	room.look = {}
	_upgrade_meshes(room, c, y0, bed_c, x0, x1, zf, zb, h)
	_upgrade_sign(i, c, y0, x0)
	var nodes := []
	for idx in range(_child_mark, get_child_count()):
		nodes.append(get_child(idx))
	room.nodes = nodes
	room_nodes.append(room)

func _bwall_x(x0: float, x1: float, z: float, h: float, gaps: Array, y0: float) -> void:
	var save_pl = M.plaster
	var save_tc = M.terracotta
	M.plaster = M.bamboo
	M.terracotta = M.deckwood
	_wall_x(x0, x1, z, h, gaps, y0)
	M.plaster = save_pl
	M.terracotta = save_tc

func _bwall_z(z0: float, z1: float, x: float, h: float, gaps: Array, y0: float) -> void:
	var save_pl = M.plaster
	var save_tc = M.terracotta
	M.plaster = M.bamboo
	M.terracotta = M.deckwood
	_wall_z(z0, z1, x, h, gaps, y0)
	M.plaster = save_pl
	M.terracotta = save_tc

func _on_room_changed(id: int) -> void:
	if id >= room_nodes.size():
		return
	var r: Dictionary = Core.rooms[id]
	var rn: Dictionary = room_nodes[id]
	rn.clean.visible = r.state == "free"
	for k in rn.dirty:
		rn.dirty[k].visible = r.state == "dirty" and r.dirty.get(k, false)
	apply_room_look(id)

func _look(room: Dictionary, cat: String, tier: int, node: Node3D) -> void:
	if not room.look.has(cat):
		room.look[cat] = []
	room.look[cat].append({"n": node, "t": tier})
	node.visible = false

func _upgrade_meshes(room: Dictionary, c: Vector3, y0: float, bed_c: Vector3, x0: float, x1: float, zf: float, zb: float, h: float) -> void:
	var mattress := B.box(self, Vector3(1.84, 0.14, 2.16), bed_c + Vector3(0, 0.64, 0), M.linen)
	_look(room, "cama", 1, mattress)
	var canopy := Node3D.new()
	add_child(canopy)
	for sx in [-0.95, 0.95]:
		for sz in [-1.05, 1.05]:
			B.box(canopy, Vector3(0.06, 1.45, 0.06), bed_c + Vector3(sx, 1.4, sz), M.oak)
	B.box(canopy, Vector3(2.1, 0.05, 2.35), bed_c + Vector3(0, 2.12, 0), M.linen_sand)
	B.box(canopy, Vector3(2.05, 0.85, 0.04), bed_c + Vector3(0, 1.65, -1.05), M.linen_teal)
	_look(room, "cama", 2, canopy)
	var blanket := B.box(self, Vector3(1.45, 0.045, 1.1), bed_c + Vector3(0.05, 0.72, -0.2), M.linen_teal)
	_look(room, "roupa", 1, blanket)
	var linens := Node3D.new()
	add_child(linens)
	B.box(linens, Vector3(1.7, 0.035, 2.0), bed_c + Vector3(0, 0.76, 0), B.flat(Color(0.98, 0.98, 0.96)))
	B.box(linens, Vector3(0.42, 0.14, 0.3), bed_c + Vector3(-0.55, 0.86, 0.72), B.flat(Color(0.82, 0.38, 0.32)))
	B.box(linens, Vector3(0.42, 0.14, 0.3), bed_c + Vector3(0.55, 0.86, 0.72), B.flat(Color(0.95, 0.78, 0.35)))
	_look(room, "roupa", 2, linens)
	var decor := Node3D.new()
	add_child(decor)
	B.box(decor, Vector3(2.2, 0.02, 1.5), Vector3(c.x + 0.3, y0 + 0.02, c.z + 0.2), B.flat(Color(0.55, 0.2, 0.16)))
	B.box(decor, Vector3(0.85, 0.55, 0.04), Vector3(c.x - 0.2, y0 + 1.7, zf + 0.06), B.flat(Color(0.2, 0.45, 0.55)))
	_look(room, "decor", 1, decor)
	var lounge := Node3D.new()
	add_child(lounge)
	B.cyl(lounge, 0.08, 0.12, 1.05, Vector3(c.x + 1.9, y0 + 0.55, c.z + 1.45), M.oak, 8)
	B.sphere(lounge, 0.16, Vector3(c.x + 1.9, y0 + 1.15, c.z + 1.45), B.flat(Color(1.0, 0.93, 0.72), 0.4))
	B.model(lounge, "potted_plant_01", Vector3(c.x - 2.1, y0, zb - 0.4), 0.4, 0.8)
	_look(room, "decor", 2, lounge)
	var fan := Node3D.new()
	add_child(fan)
	fan.position = Vector3(c.x, y0 + h - 0.18, c.z)
	B.cyl(fan, 0.07, 0.07, 0.1, Vector3.ZERO, M.dark, 8)
	for k in 3:
		var pivot := Node3D.new()
		fan.add_child(pivot)
		pivot.rotation.y = k * TAU / 3.0
		B.box(pivot, Vector3(0.82, 0.02, 0.14), Vector3(0.4, -0.05, 0), B.flat(Color(0.9, 0.9, 0.93)))
	room.fan = fan
	_look(room, "clima", 1, fan)
	var ac := Node3D.new()
	add_child(ac)
	B.box(ac, Vector3(0.26, 0.28, 0.72), Vector3(x1 - 0.12, y0 + 2.15, c.z + 0.2), B.flat(Color(0.93, 0.94, 0.96)))
	B.box(ac, Vector3(0.05, 0.08, 0.48), Vector3(x1 - 0.26, y0 + 2.05, c.z + 0.2), B.flat(Color(0.15, 0.2, 0.22)))
	_look(room, "clima", 2, ac)
	var bath := Node3D.new()
	add_child(bath)
	B.box(bath, Vector3(0.05, 0.7, 0.42), Vector3(x0 + 0.16, y0 + 1.5, c.z - 1.35), B.flat(Color(0.75, 0.86, 0.92), 0.15, 0.55))
	B.box(bath, Vector3(0.46, 0.04, 0.08), Vector3(x0 + 0.28, y0 + 1.12, c.z - 0.75), M.oak)
	B.box(bath, Vector3(0.26, 0.38, 0.05), Vector3(x0 + 0.3, y0 + 0.85, c.z - 0.75), M.linen)
	_look(room, "banho", 1, bath)
	var vanity := Node3D.new()
	add_child(vanity)
	B.box(vanity, Vector3(0.48, 0.72, 1.05), Vector3(x0 + 0.42, y0 + 0.36, c.z - 1.25), M.stone)
	B.box(vanity, Vector3(0.36, 0.08, 0.36), Vector3(x0 + 0.55, y0 + 0.76, c.z - 1.25), B.flat(Color(0.86, 0.9, 0.93), 0.2))
	B.box(vanity, Vector3(0.06, 1.35, 0.85), Vector3(x1 - 0.2, y0 + 0.85, zf + 0.4), M.linen_teal)
	_look(room, "banho", 2, vanity)

func _upgrade_sign(i: int, c: Vector3, y0: float, x0: float) -> void:
	var p := Vector3(x0 - 0.45, y0 + 1.35, c.z)
	B.box(self, Vector3(0.08, 0.7, 0.9), p, M.planks)
	B.label(self, "MELHORIAS", p + Vector3(-0.06, 0, 0), 28, Color(0.15, 0.35, 0.4), Color(1, 1, 1, 0.85), PI * 0.5)
	var it := Interactable.new()
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = Vector3(0.8, 1.2, 1.2)
	cs.shape = sh
	it.add_child(cs)
	it.position = p
	var room_id := i
	it.prompt_fn = func() -> String:
		return tr("Melhorias do Bangalô %d (%s)") % [room_id + 1, Core.fmt_money(Core.nightly_rate(room_id))]
	it.action_fn = func() -> void:
		get_tree().call_group("hud", "open_office", "bangalo", room_id)
	add_child(it)

func apply_room_look(id: int) -> void:
	if id < 0 or id >= room_nodes.size() or id >= Core.rooms.size():
		return
	var look: Dictionary = room_nodes[id].get("look", {})
	var u: Dictionary = Core.rooms[id].upgrades
	for cat in look:
		var tier := int(u.get(cat, 0))
		for e in look[cat]:
			var n: Node3D = e.n
			if is_instance_valid(n):
				n.visible = tier >= int(e.t)

func upgrade_visible(room_id: int, cat: String, tier: int) -> bool:
	if room_id < 0 or room_id >= room_nodes.size():
		return false
	for e in room_nodes[room_id].get("look", {}).get(cat, []):
		if int(e.t) == tier and is_instance_valid(e.n):
			return bool(e.n.visible)
	return false

func _ensure_bung_x(n: int) -> void:
	while BUNG_X.size() < n:
		BUNG_X.append(float(BUNG_X[-1]) - 8.0)

func _on_bungalow_built(id: int) -> void:
	_ensure_bung_x(id + 1)
	if room_nodes.size() == id:
		_bungalow(id, Vector3(float(BUNG_X[id]), 0, BUNG_Z))
	_on_room_changed(id)

func sync_bungalows() -> void:
	_ensure_bung_x(Core.rooms.size())
	while room_nodes.size() > Core.rooms.size():
		_drop_bungalow(room_nodes.size() - 1)
	while room_nodes.size() < Core.rooms.size():
		var i := room_nodes.size()
		_bungalow(i, Vector3(float(BUNG_X[i]), 0, BUNG_Z))
	for r in Core.rooms:
		_on_room_changed(int(r.id))

func _drop_bungalow(i: int) -> void:
	var rn: Dictionary = room_nodes[i]
	var doomed := {}
	for n in rn.get("nodes", []):
		doomed[n] = true
	var keep := []
	for e in lanterns:
		if not doomed.has(e[0]):
			keep.append(e)
	lanterns = keep
	for n in rn.get("nodes", []):
		if is_instance_valid(n):
			n.queue_free()
	room_nodes.remove_at(i)

func _birds_spawn() -> void:
	var mat := B.flat(Color(0.12, 0.12, 0.14))
	for i in 5:
		var mi := MeshInstance3D.new()
		var qm := QuadMesh.new()
		qm.size = Vector2(0.62, 0.14)
		mi.mesh = qm
		mi.material_override = mat
		add_child(mi)
		_birds.append({"n": mi, "a": float(i) * 1.2, "r": 7.0 + float(i) * 1.6, "y": 8.5 + float(i) * 0.35, "cx": -4.0 + float(i) * 3.0, "cz": -8.0})

func _weather_fx() -> void:
	rain = GPUParticles3D.new()
	rain.amount = 500
	rain.lifetime = 1.05
	rain.visibility_aabb = AABB(Vector3(-90, -8, -50), Vector3(220, 40, 180))
	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = Vector3(70, 0.5, 50)
	pm.direction = Vector3(0.2, -1, 0.05)
	pm.spread = 6.0
	pm.initial_velocity_min = 16.0
	pm.initial_velocity_max = 24.0
	pm.gravity = Vector3(0, -8, 0)
	rain.process_material = pm
	var qm := QuadMesh.new()
	qm.size = Vector2(0.025, 0.42)
	var rm := B.flat(Color(0.75, 0.82, 0.9, 0.65), 0.2)
	rm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	rm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qm.material = rm
	rain.draw_pass_1 = qm
	rain.position = Vector3(20, 16, 8)
	rain.emitting = false
	rain.visible = false
	add_child(rain)
	_on_weather(Core.weather)

func _on_weather(kind: String) -> void:
	var wet := kind == "rain"
	if rain:
		rain.emitting = wet
		rain.visible = wet
	if sand_mat:
		sand_mat.set_shader_parameter("rain_wet", 0.62 if wet else 0.0)

func _process(delta: float) -> void:
	var t := Time.get_ticks_msec() * 0.001
	for b in _birds:
		var n: MeshInstance3D = b.n
		if not is_instance_valid(n):
			continue
		var a: float = t * 0.32 + float(b.a)
		n.position = Vector3(float(b.cx) + cos(a) * float(b.r), float(b.y) + sin(a * 2.0) * 0.35, float(b.cz) + sin(a) * float(b.r) * 0.55)
		n.rotation.y = -a
	for rn in room_nodes:
		var fan: Node3D = rn.get("fan")
		if fan and is_instance_valid(fan) and fan.visible:
			fan.rotation.y += delta * 2.2

# ------------------------------------------------------------------ bar
func _bar() -> void:
	var c := BAR_C
	B.platform(self, Vector3(7.6, 0.2, 7.6), c, M.deckwood, 0.5)
	var y0 := 0.1
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.cyl(self, 0.13, 0.16, 2.9, c + Vector3(sx * 2.8, y0 + 1.45, sz * 2.8), M.post, 8)
	B.hip_roof(self, c + Vector3(0, y0 + 2.9, 0), 7.4, 7.4, 3.0, M.thatch, 0.22)
	# balcão em U (aberto atrás, lado +X)
	var ch := 1.1
	var cm: Material = M.bamboo
	B.box(self, Vector3(0.6, ch, 4.4), c + Vector3(-2.0, y0 + ch * 0.5, 0), cm, true)
	B.box(self, Vector3(4.0, ch, 0.6), c + Vector3(0, y0 + ch * 0.5, -2.0), cm, true)
	B.box(self, Vector3(4.0, ch, 0.6), c + Vector3(0, y0 + ch * 0.5, 2.0), cm, true)
	B.box(self, Vector3(0.8, 0.07, 4.6), c + Vector3(-2.0, y0 + ch + 0.035, 0), M.oak)
	B.box(self, Vector3(4.4, 0.07, 0.8), c + Vector3(0, y0 + ch + 0.035, -2.0), M.oak)
	B.box(self, Vector3(4.4, 0.07, 0.8), c + Vector3(0, y0 + ch + 0.035, 2.0), M.oak)
	# prateleira de garrafas
	B.box(self, Vector3(0.4, 1.6, 3.0), c + Vector3(2.3, y0 + 0.8, 0), M.oak)
	var cols := [Color(0.2, 0.5, 0.2), Color(0.6, 0.35, 0.1), Color(0.85, 0.85, 0.9), Color(0.5, 0.1, 0.15)]
	for i in 10:
		var gm := B.flat(cols[i % cols.size()], 0.15, 0.1)
		B.cyl(self, 0.045, 0.05, 0.3, c + Vector3(2.25, y0 + 1.75, -1.3 + i * 0.28), gm, 8)
	B.model(self, "lambis_shell", c + Vector3(-2.0, y0 + ch + 0.07, 1.2), 0.3, 1.0)
	B.model(self, "wooden_bucket_01", c + Vector3(-2.0, y0 + ch + 0.07, -1.0), 0.0, 0.6)
	# cocos no balcão
	var coco := B.flat(Color(0.4, 0.5, 0.15), 0.6)
	for k in 3:
		B.sphere(self, 0.12, c + Vector3(-0.6 + k * 0.3, y0 + ch + 0.17, -2.0), coco)
	# banquetas
	var stools := [Vector3(-3.0, 0, -0.9), Vector3(-3.0, 0, 0.9), Vector3(-0.9, 0, -3.0), Vector3(0.9, 0, -3.0), Vector3(-0.9, 0, 3.0), Vector3(0.9, 0, 3.0)]
	for s in stools:
		var face := atan2(-s.x, -s.z)   # olhando para o balcão
		B.model(self, "bar_chair_round_01", c + s + Vector3(0, y0, 0), face, 1.0)
		bar_spots.append({"pos": c + s + Vector3(0, y0 + 0.28, 0), "rot": face, "anim": "Sitting_Idle_Loop", "busy": false})
	# mesas na areia
	B.model(self, "outdoor_table_chair_set_01", c + Vector3(-5.5, 0, 3.5), 0.4, 1.0)
	B.model(self, "outdoor_table_chair_set_01", c + Vector3(-5.8, 0, -3.0), -0.3, 1.0)
	# placa
	B.box(self, Vector3(3.2, 0.6, 0.08), c + Vector3(0, y0 + 2.55, -2.86), M.planks)
	B.label(self, "Bar do Coqueiro", c + Vector3(0, y0 + 2.55, -2.92), 64, Color(1.0, 0.95, 0.8), Color(0.25, 0.12, 0.02, 1.0), PI)
	B.label(self, "Bar do Coqueiro", c + Vector3(-2.92, y0 + 2.55, 0), 64, Color(1.0, 0.95, 0.8), Color(0.25, 0.12, 0.02, 1.0), -PI * 0.5)
	B.box(self, Vector3(0.08, 0.6, 3.2), c + Vector3(-2.86, y0 + 2.55, 0), M.planks)
	points["bartender"] = c + Vector3(1.0, y0, 0)
	var l := OmniLight3D.new()
	l.position = c + Vector3(0, 2.6, 0)
	l.omni_range = 7.0
	l.light_color = Color(1.0, 0.75, 0.45)
	add_child(l)
	lanterns.append([l, null, 1.8, false])

# ------------------------------------------------------------------ praia
func _beach_props() -> void:
	var spots := [Vector3(-28, 0, -21), Vector3(-17, 0, -22), Vector3(-6, 0, -23), Vector3(4, 0, -22), Vector3(24, 0, -21), Vector3(33, 0, -22)]
	for i in spots.size():
		var p: Vector3 = spots[i]
		_umbrella(p, 1.6)
		_lounger(p + Vector3(-0.8, 0, 0.6), PI + 0.15)
		_lounger(p + Vector3(0.8, 0, 0.6), PI - 0.15)
	# jangada na areia
	var j := Node3D.new()
	j.position = Vector3(-9, -0.42, -30.2)
	j.rotation.y = 0.35
	add_child(j)
	for k in 6:
		B.cyl(j, 0.12, 0.12, 6.0, Vector3(-0.6 + k * 0.24, 0.12, 0), M.post, 8).rotation.x = PI * 0.5
	B.cyl(j, 0.06, 0.07, 5.5, Vector3(0, 2.8, 1.0), M.oak, 8)
	var sail := MeshInstance3D.new()
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for v in [Vector3(0, 0.6, 1.0), Vector3(0, 5.4, 1.0), Vector3(0, 0.7, -2.4)]:
		st.set_normal(Vector3.RIGHT)
		st.set_uv(Vector2(v.z, v.y) * 0.3)
		st.add_vertex(v)
	sail.mesh = st.commit()
	var sm := B.mat("rough_linen", 1.0, Color(1, 0.98, 0.94), 0.95).duplicate()
	sm.cull_mode = BaseMaterial3D.CULL_DISABLED
	sail.material_override = sm
	j.add_child(sail)
	B.wall(self, Vector3(2.0, 2.0, 6.5), Vector3(-9, 1.0, -30.2), 0.35)
	# conchas e baldes
	B.model(self, "lambis_shell", Vector3(-3, -0.2, -27.5), 1.2, 1.5)
	B.model(self, "wooden_bucket_01", Vector3(6, 0, -19.5), 0.0, 1.0)

func _palms() -> void:
	var excl := [Rect2(-6, 12, 12, 8), Rect2(-10, -4, 20, 16), Rect2(-25.5, -12.5, 15, 9), Rect2(8.5, -18, 9, 10),
		Rect2(-2, 18, 4, 30), Rect2(-12, -6, 3, 34), Rect2(-31, -26, 70, 7), Rect2(1, 25, 100, 10), Rect2(34, 16, 70, 40), Rect2(35, -16, 8, 42)]
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	var placed := []
	var tries := 0
	while placed.size() < 34 and tries < 2000:
		tries += 1
		var p := Vector2(rng.randf_range(-44, 44), rng.randf_range(-27, 44))
		var ok := true
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
	# coqueiros distantes nas dunas (sem colisão)
	for k in 26:
		var x := rng.randf_range(-110, 110)
		var z := rng.randf_range(50, 95)
		if absf(x) < 50 and z < 52:
			continue
		Palm.spawn(self, Vector3(x, _height(x, z) - 0.1, z), 200 + k, false)
	for k in 12:
		var side := -1.0 if k % 2 == 0 else 1.0
		var x2 := side * rng.randf_range(66, 110) if side < 0.0 else rng.randf_range(108, 126)
		var z2 := rng.randf_range(-20, 45)
		Palm.spawn(self, Vector3(x2, _height(x2, z2) - 0.1, z2), 300 + k, false)

const REDE_PAIRS := [[Vector3(-27, 0, -14), Vector3(-23.4, 0, -15.0)], [Vector3(-6.5, 0, -17.5), Vector3(-2.9, 0, -18.2)],
	[Vector3(19.5, 0, -16), Vector3(23.1, 0, -15.2)], [Vector3(27, 0, -4), Vector3(30.4, 0, -5.4)]]

func _redes() -> void:
	var stripes := Image.create(64, 8, false, Image.FORMAT_RGB8)
	var cols := [Color(0.95, 0.35, 0.15), Color(1.0, 0.8, 0.2), Color(0.1, 0.6, 0.6), Color(0.95, 0.95, 0.9), Color(0.85, 0.2, 0.3)]
	for x in 64:
		for y in 8:
			stripes.set_pixel(x, y, cols[(x / 6) % cols.size()])
	var stex := ImageTexture.create_from_image(stripes)
	var rm := StandardMaterial3D.new()
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
		var node := Node3D.new()
		add_child(node)
		var dir := (b_ - a)
		var L := dir.length()
		var fwd := dir.normalized()
		var side := fwd.cross(Vector3.UP).normalized()
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var n := 16
		var prev := []
		var attach_h := 1.45
		for k in n + 1:
			var t := float(k) / n
			var p := a + dir * t
			p.y = attach_h - sin(t * PI) * 0.85
			var wdt := 0.15 + 0.5 * sin(t * PI)
			var l := p - side * wdt + Vector3.UP * 0.12 * sin(t * PI)
			var r := p + side * wdt + Vector3.UP * 0.12 * sin(t * PI)
			if k > 0:
				for v in [[prev[0], Vector2(t - 1.0 / n, 0)], [l, Vector2(t, 0)], [r, Vector2(t, 1)], [prev[0], Vector2(t - 1.0 / n, 0)], [r, Vector2(t, 1)], [prev[1], Vector2(t - 1.0 / n, 1)]]:
					st.set_normal(Vector3.UP)
					st.set_uv(v[1])
					st.add_vertex(v[0])
			prev = [l, r]
		var mi := MeshInstance3D.new()
		mi.mesh = st.commit()
		mi.material_override = rm
		node.add_child(mi)
		# cordas
		var rope := B.flat(Color(0.75, 0.65, 0.45), 0.9)
		for e in [[a, fwd], [b_, -fwd]]:
			var ep: Vector3 = e[0] + Vector3(0, attach_h + 0.15, 0) + e[1] * 0.25
			var rp := B.cyl(node, 0.015, 0.015, 0.6, ep + e[1] * 0.25 - Vector3(0, 0.08, 0), rope, 5)
			rp.rotation = Vector3(0, 0, 0)
			rp.look_at_from_position(rp.position, ep + e[1] * 0.6 - Vector3(0, 0.2, 0), Vector3.UP)
			rp.rotate_object_local(Vector3.RIGHT, PI * 0.5)
		node.visible = false
		rede_nodes.append(node)

func _on_redes_changed(n: int) -> void:
	for i in rede_nodes.size():
		rede_nodes[i].visible = i < n

func _lantern_posts() -> void:
	var posts := [Vector3(1.9, 0, 24), Vector3(-1.9, 0, 30), Vector3(1.9, 0, 36), Vector3(-1.9, 0, 42),
		Vector3(-9.0, 0, 18), Vector3(-9.0, 0, 6), Vector3(-9.0, 0, -6), Vector3(-17.8, 0, -3.2),
		Vector3(9.4, 0, -0.5), Vector3(9.4, 0, 10.5), Vector3(-9.4, 0, 10.5), Vector3(10.6, 0, -8.0), Vector3(1.3, 0, -14)]
	for p in posts:
		B.box(self, Vector3(0.14, 1.9, 0.14), p + Vector3(0, 0.95, 0), M.oak)
		B.box(self, Vector3(0.5, 0.06, 0.14), p + Vector3(0.18, 1.88, 0), M.oak)
		B.model(self, "wooden_lantern_01", p + Vector3(0.36, 1.45, 0), 0.0, 0.9)
		var glow := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.07
		sm.height = 0.14
		glow.mesh = sm
		var gm := StandardMaterial3D.new()
		gm.albedo_color = Color(1, 0.8, 0.5)
		gm.emission_enabled = true
		gm.emission = Color(1.0, 0.7, 0.35)
		gm.emission_energy_multiplier = 0.0
		glow.material_override = gm
		glow.position = p + Vector3(0.36, 1.62, 0)
		add_child(glow)
		var l := OmniLight3D.new()
		l.position = p + Vector3(0.36, 1.6, 0)
		l.omni_range = 6.0
		l.light_color = Color(1.0, 0.72, 0.4)
		l.light_energy = 0.0
		add_child(l)
		lanterns.append([l, gm, 1.3, false])

func set_night(t: float) -> void:
	for e in lanterns:
		var k: float = maxf(t, 0.5) if e[3] else t   # luz interna acesa de dia (sem GI no mobile)
		if e[0] != null:
			var l: OmniLight3D = e[0]
			l.light_energy = e[2] * k
			l.visible = k > 0.01
		if e[1]:
			e[1].emission_energy_multiplier = 3.0 * t
	ocean_mat.set_shader_parameter("night", t * 0.8)
	if pool_floor_mat:
		pool_floor_mat.set_shader_parameter("day", 1.0 - t)

func _signs() -> void:
	var p := Vector3(3.6, 0, 40)
	B.box(self, Vector3(0.15, 2.4, 0.15), p + Vector3(-1.4, 1.2, 0), M.post)
	B.box(self, Vector3(0.15, 2.4, 0.15), p + Vector3(1.4, 1.2, 0), M.post)
	B.box(self, Vector3(3.2, 1.0, 0.1), p + Vector3(0, 1.9, 0), M.planks)
	B.label(self, "Pousada\nMaré Alta", p + Vector3(0, 1.9, -0.07), 72, Color(0.1, 0.45, 0.5), Color(1, 1, 1, 0.9), PI)
	B.label(self, "Pousada\nMaré Alta", p + Vector3(0, 1.9, 0.07), 72, Color(0.1, 0.45, 0.5), Color(1, 1, 1, 0.9))

# ------------------------------------------------------------------ rotas
func _route_points() -> void:
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
	var near := p + (p - BAR_C).normalized() * 0.9
	near.y = 0.1
	return [points.deck_s, points.deck_se, points.walk_bar, near, p]

func route_exit(room: int) -> Array:
	return [points["room%d_door" % room], points["room%d_front" % room], points.hub_sw, points.hub_nw, points.hub_w_exit, points.exit_join, points.spawn]

# ------------------------------------------------------------------ vegetação (só PC)
const VEG_EXCL := [Rect2(-5.8, 12, 11.6, 8.2), Rect2(-9.4, -3.4, 18.8, 14.8), Rect2(-25.6, -12.2, 15.2, 8.6),
	Rect2(-1.8, 19, 3.6, 28), Rect2(-11.8, -5.8, 2.6, 33), Rect2(-24.8, -5.8, 15.2, 2.6), Rect2(-11.8, 24.6, 12.2, 2.8),
	Rect2(8.4, -17.6, 9.2, 9.2), Rect2(8.0, -11.0, 4.2, 9.0), Rect2(-1.2, -17, 2.4, 15), Rect2(1.0, 38.5, 5.5, 3),
	Rect2(1.0, 25.8, 98, 8.4), Rect2(41.5, 16.5, 56, 9.2), Rect2(39, 34, 58, 9.5), Rect2(65, 34, 20, 20), Rect2(36.4, -16, 3.2, 43),
	Rect2(33, -17.5, 10, 9), Rect2(56, -24, 12, 9)]

func _veg_free(p: Vector2, margin := 0.5) -> bool:
	for r in VEG_EXCL:
		if r.grow(margin).has_point(p):
			return false
	return true

func _cross_mesh(w: float, h: float, planes: int) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in planes:
		var a := PI * float(i) / planes
		var d := Vector3(cos(a), 0, sin(a)) * w * 0.5
		var q := [[-d, Vector2(0, 1)], [d, Vector2(1, 1)], [d + Vector3(0, h, 0), Vector2(1, 0)], [-d + Vector3(0, h, 0), Vector2(0, 0)]]
		for idx in [0, 1, 2, 0, 2, 3]:
			st.set_normal(Vector3.UP)
			st.set_uv(q[idx][1])
			st.add_vertex(q[idx][0])
	return st.commit()

func _scatter(mesh: Mesh, mat: Material, xforms: Array, vis_end: float, shadows: bool) -> void:
	var chunks := {}
	for t in xforms:
		var key := Vector2i(int(floor(t.origin.x / 24.0)), int(floor(t.origin.z / 24.0)))
		if not chunks.has(key):
			chunks[key] = []
		chunks[key].append(t)
	for key in chunks:
		var list: Array = chunks[key]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		mm.instance_count = list.size()
		for i in list.size():
			mm.set_instance_transform(i, list[i])
		var mmi := MultiMeshInstance3D.new()
		mmi.multimesh = mm
		mmi.material_override = mat
		mmi.visibility_range_end = vis_end
		mmi.visibility_range_end_margin = 8.0
		mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
		mmi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if shadows else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mmi)

func _vegetation() -> void:
	if not Quality.hd:
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = 777
	var noise := FastNoiseLite.new()
	noise.seed = 9
	noise.frequency = 0.06
	# mais coqueiros
	var placed := []
	var tries := 0
	while placed.size() < 46 and tries < 4000:
		tries += 1
		var p := Vector2(rng.randf_range(-46, 46), rng.randf_range(-24, 45))
		if not _veg_free(p, 1.6):
			continue
		var ok := true
		for q in placed:
			if q.distance_to(p) < 3.8:
				ok = false
				break
		if ok:
			placed.append(p)
			Palm.spawn(self, Vector3(p.x, _height(p.x, p.y) - 0.05, p.y), 700 + placed.size() * 3)
	# capim de restinga
	var gm := ShaderMaterial.new()
	gm.shader = load("res://shaders/foliage.gdshader")
	gm.set_shader_parameter("tex", load("res://assets/tex_hd/grass_tuft.png"))
	gm.set_shader_parameter("sway", 0.08)
	var grass := []
	for i in 38000:
		var p := Vector2(rng.randf_range(-62, 100), rng.randf_range(-22, 54))
		var n := noise.get_noise_2d(p.x, p.y)
		var beach := clampf((p.y + 22.0) / 10.0, 0.0, 1.0)   # menos capim perto do mar
		if n < 0.05 + (1.0 - beach) * 0.35 or not _veg_free(p):
			continue
		var s := rng.randf_range(0.6, 1.25) * (0.7 + n)
		var b := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s * rng.randf_range(0.8, 1.3), s))
		grass.append(Transform3D(b, Vector3(p.x, _height(p.x, p.y) - 0.02, p.y)))
	_scatter(_cross_mesh(0.9, 0.75, 3), gm, grass, 70.0, false)
	# arbustos floridos junto às construções e caminhos
	var bm := ShaderMaterial.new()
	bm.shader = load("res://shaders/foliage.gdshader")
	bm.set_shader_parameter("tex", load("res://assets/tex_hd/bush.png"))
	bm.set_shader_parameter("sway", 0.03)
	var bushes := []
	for r in VEG_EXCL:
		var per := int((r.size.x + r.size.y) * 0.6)
		for k in per:
			var side := rng.randi() % 4
			var u := rng.randf()
			var p: Vector2
			match side:
				0: p = Vector2(r.position.x + u * r.size.x, r.position.y - 1.0)
				1: p = Vector2(r.position.x + u * r.size.x, r.end.y + 1.0)
				2: p = Vector2(r.position.x - 1.0, r.position.y + u * r.size.y)
				_: p = Vector2(r.end.x + 1.0, r.position.y + u * r.size.y)
			if not _veg_free(p, 0.3) or rng.randf() < 0.55 or p.y < -21.0:
				continue
			var s := rng.randf_range(0.8, 1.4)
			bushes.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(s, s, s)), Vector3(p.x, _height(p.x, p.y) - 0.05, p.y)))
	_scatter(_cross_mesh(1.7, 1.4, 4), bm, bushes, 110.0, true)
	print("vegetacao: capim=%d arbustos=%d coqueiros+=%d" % [grass.size(), bushes.size(), placed.size()])
