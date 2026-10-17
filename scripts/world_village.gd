extends "res://scripts/world.gd"
## Vila de pescadores ao redor da pousada: rua de paralelepípedo, calçadas de pedra portuguesa,
## casinhas coloniais coloridas, igreja e praça, padaria/mercadinho, barraca de praia,
## o quiosque onde o herói trabalha e a casa do herói (com interior).

const STREET_Z := 30.0
const HOME_C := Vector3(46, 0, 21)
const KIOSK_C := Vector3(38, 0, -13)
const CHURCH_C := Vector3(75, 0, 50)
const PRACA := Rect2(66, 34.5, 18, 9.3)

var village_points := {}
var village_paths: Array = []      # polilinhas para os moradores
var kiosk_counter: Interactable
var kiosk_spots: Array = []
var bed: Interactable
var home_wake := Vector3(HOME_C.x - 0.8, 0.2, HOME_C.z - 0.6)
var bench_spots: Array = []
var market: Interactable
var quest_board: Interactable
var VM := {}

func _ready() -> void:
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

func _village_materials() -> void:
	VM.road = B.mat("cobblestone_floor_04", 0.4, Color(0.92, 0.9, 0.86), 0.9)
	VM.calcada = B.mat("calcada", 0.55, Color(1, 1, 1), 0.85)
	VM.curb = B.mat("light_stone", 1.2, Color(0.92, 0.92, 0.9), 0.8)
	var clay := B.mat("clay_roof_tiles_02", 0.55, Color(1, 1, 1), 0.8).duplicate()
	clay.cull_mode = BaseMaterial3D.CULL_DISABLED
	VM.clay = clay
	VM.trim = B.mat("white_stucco", 0.5, Color(0.97, 0.96, 0.93), 0.85)
	VM.floor = B.mat("terracotta_floor_tiles", 0.7, Color(1, 1, 1), 0.6)
	VM.door = B.mat("weathered_planks", 0.9, Color(0.45, 0.28, 0.16), 0.7)
	VM.glass = B.flat(Color(0.12, 0.16, 0.2), 0.08, 0.3)

func stucco(c: Color) -> Material:
	return B.mat("white_stucco", 0.5, c, 0.88)

func wood_tint(c: Color) -> Material:
	return B.mat("weathered_planks", 0.9, c, 0.7)

# ------------------------------------------------------------------ rua e calçadas
func _street() -> void:
	var x0 := 1.3
	var x1 := 99.0
	var L := x1 - x0
	var cx := (x0 + x1) * 0.5
	B.box(self, Vector3(L, 0.05, 4.0), Vector3(cx, 0.02, STREET_Z), VM.road)
	for side in [-1.0, 1.0]:
		var z_side: float = STREET_Z + side * 2.9
		B.platform(self, Vector3(L, 0.3, 1.8), Vector3(cx, 0.0, z_side), VM.calcada, 0.35)
		B.box(self, Vector3(L, 0.32, 0.22), Vector3(cx, 0.0, STREET_Z + side * 2.05), VM.curb)
	# acesso da calçada até o quiosque (passa entre a pousada e as casas)
	B.box(self, Vector3(2.4, 0.06, 34.0), Vector3(38, 0.03, 9.2), VM.calcada)
	# calçadinhas das portas
	village_points.street_w = Vector3(2.5, 0.15, STREET_Z - 2.9)

func _facade(c: Vector3, n: Vector3, half: float, offset: float, kind: String, col: Color, base_y := 0.0) -> void:
	# porta ou janela embutida numa fachada (casas fechadas)
	var t := Vector3(-n.z, 0, n.x)
	var rot := atan2(n.x, n.z)
	var p := c + n * (half + 0.03) + t * offset
	if kind == "door":
		B.box(self, Vector3(1.3, 2.45, 0.08), p + Vector3(0, base_y + 1.22, 0), VM.trim, false, rot)
		B.box(self, Vector3(1.05, 2.25, 0.1), p + Vector3(0, base_y + 1.12, 0) + n * 0.02, wood_tint(col), false, rot)
		B.box(self, Vector3(0.5, 0.05, 0.04), p + Vector3(0, base_y + 1.6, 0) + n * 0.08, VM.door, false, rot)
	else:
		B.box(self, Vector3(1.35, 1.6, 0.08), p + Vector3(0, base_y + 1.75, 0), VM.trim, false, rot)
		B.box(self, Vector3(1.1, 1.35, 0.06), p + Vector3(0, base_y + 1.75, 0) + n * 0.01, VM.glass, false, rot)
		for s in [-1.0, 1.0]:   # venezianas abertas
			var sh := B.box(self, Vector3(0.56, 1.35, 0.05), p + t * s * 0.86 + Vector3(0, base_y + 1.75, 0) + n * 0.04, wood_tint(col), false, rot)
			sh.name = "shutter"
		B.box(self, Vector3(1.5, 0.08, 0.2), p + Vector3(0, base_y + 0.98, 0) + n * 0.06, VM.trim, false, rot)

func _house(c: Vector3, w: float, d: float, front: float, col: Color, shutter: Color, porch: bool, sign_text := "") -> void:
	var h := 3.5
	var body := B.box(self, Vector3(w, h, d), c + Vector3(0, h * 0.5, 0), stucco(col), true)
	body.name = "house"
	B.box(self, Vector3(w + 0.04, 0.7, d + 0.04), c + Vector3(0, 0.35, 0), stucco(col.darkened(0.35)))       # barrado
	B.box(self, Vector3(w + 0.16, 0.28, d + 0.16), c + Vector3(0, h - 0.1, 0), VM.trim)                       # cornija
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.box(self, Vector3(0.32, h, 0.32), c + Vector3(sx * w * 0.5, h * 0.5, sz * d * 0.5), VM.trim)
	var n := Vector3(0, 0, front)
	_facade(c, n, d * 0.5, -w * 0.18 * front, "door", shutter)
	_facade(c, n, d * 0.5, w * 0.22 * front, "window", shutter)
	if w > 7.5:
		_facade(c, n, d * 0.5, -w * 0.38 * front, "window", shutter)
	_facade(c, -n, d * 0.5, 0.0, "window", shutter)
	_facade(c, Vector3(1, 0, 0), w * 0.5, 0.0, "window", shutter)
	_facade(c, Vector3(-1, 0, 0), w * 0.5, 0.0, "window", shutter)
	B.hip_roof(self, c + Vector3(0, h + 0.05, 0), w + 1.0, d + 1.0, 1.9, VM.clay, 0.12)
	if porch:
		var pz := c.z + front * (d * 0.5 + 0.75)
		B.platform(self, Vector3(w - 0.6, 0.18, 1.5), Vector3(c.x, 0.0, pz), stucco(Color(0.75, 0.42, 0.3)), 0.3)
		for sx in [-1.0, 1.0]:
			B.cyl(self, 0.09, 0.1, 2.6, Vector3(c.x + sx * (w * 0.5 - 0.6), 1.3, pz + front * 0.6), VM.trim, 10)
		var pr := B.box(self, Vector3(w - 0.2, 0.1, 1.9), Vector3(c.x, 2.75, pz + front * 0.1), VM.clay)
		pr.rotation.x = -0.18 * front
		B.model(self, "painted_wooden_chair_01" if B.has_model("painted_wooden_chair_01") else "wooden_stool_01", Vector3(c.x + w * 0.3, 0.09, pz), PI if front > 0 else 0.0, 1.0)
		B.model(self, "potted_plant_04", Vector3(c.x - w * 0.35, 0.09, pz + front * 0.6), 0.0, 1.0)
	else:
		B.model(self, "potted_plant_01", c + Vector3(w * 0.42, 0, front * (d * 0.5 + 0.45)), 0.0, 1.0)
	if sign_text != "":
		B.box(self, Vector3(3.4, 0.6, 0.08), c + Vector3(0, 2.95, front * (d * 0.5 + 0.1)), VM.door, false, 0.0 if front > 0 else PI)
		B.label(self, sign_text, c + Vector3(0, 2.95, front * (d * 0.5 + 0.15)), 70, Color(1.0, 0.93, 0.75), Color(0.25, 0.12, 0.03, 1), 0.0 if front > 0 else PI)

const HOUSE_COLS := [Color(0.98, 0.78, 0.45), Color(0.55, 0.78, 0.86), Color(0.96, 0.62, 0.55), Color(0.72, 0.86, 0.62),
	Color(0.98, 0.9, 0.55), Color(0.82, 0.7, 0.9), Color(0.98, 0.72, 0.78), Color(0.6, 0.85, 0.8), Color(0.95, 0.85, 0.7)]
const SHUT_COLS := [Color(0.1, 0.45, 0.55), Color(0.15, 0.4, 0.2), Color(0.85, 0.55, 0.1), Color(0.2, 0.3, 0.65), Color(0.6, 0.15, 0.15), Color(0.95, 0.95, 0.9)]

func _houses() -> void:
	# fileira do lado do mar (porta para a rua, +Z)
	var north := [[54.0, 7.0, false], [62.0, 7.5, true], [80.0, 7.0, false], [88.0, 7.5, true], [96.0, 6.0, false]]
	var i := 0
	for hh in north:
		_house(Vector3(hh[0], 0, 21.2), hh[1], 7.0, 1.0, HOUSE_COLS[i % HOUSE_COLS.size()], SHUT_COLS[i % SHUT_COLS.size()], hh[2])
		i += 1
	# padaria / mercadinho (mais larga, com toldo)
	var pc := Vector3(71, 0, 21.2)
	_house(pc, 9.0, 7.0, 1.0, Color(0.98, 0.86, 0.5), Color(0.6, 0.15, 0.15), false, "Padaria e Mercadinho")
	var awn := B.box(self, Vector3(8.6, 0.06, 1.8), pc + Vector3(0, 2.6, 4.3), B.mat("rough_linen", 1.0, Color(0.85, 0.2, 0.2), 0.9))
	awn.rotation.x = -0.25
	B.model(self, "wooden_crate_01", pc + Vector3(-3.4, 0.0, 4.2), 0.2, 1.0)
	B.model(self, "wicker_basket_02", pc + Vector3(-2.6, 0.0, 4.4), 0.0, 1.0)
	B.model(self, "plastic_crate_01", pc + Vector3(3.5, 0.0, 4.2), 0.5, 1.0)
	B.model(self, "Shelf_01", pc + Vector3(2.6, 0.0, 4.0), PI, 1.0)
	market = Interactable.new()
	market.name = "Mercadinho"
	var mcs := CollisionShape3D.new()
	var msh := BoxShape3D.new()
	msh.size = Vector3(3.2, 2.0, 1.2)
	mcs.shape = msh
	market.add_child(mcs)
	market.position = pc + Vector3(0, 1.1, 4.7)
	market.prompt_fn = func() -> String: return tr("Comprar insumos no mercadinho")
	market.action_fn = func() -> void: get_tree().call_group("hud", "open_office", "insumos", -1)
	add_child(market)
	# fileira do lado de dentro (porta para a rua, -Z)
	var south := [[44.0, 7.0, true], [52.0, 6.5, false], [60.0, 7.5, false], [90.0, 7.0, true], [97.5, 5.5, false]]
	for hh in south:
		_house(Vector3(hh[0], 0, 38.8), hh[1], 7.0, -1.0, HOUSE_COLS[i % HOUSE_COLS.size()], SHUT_COLS[(i + 2) % SHUT_COLS.size()], hh[2])
		i += 1

# ------------------------------------------------------------------ casa do herói
func _hero_house() -> void:
	var c := HOME_C
	var w := 7.0
	var d := 7.0
	var col := Color(0.55, 0.8, 0.88)
	var y0 := 0.12
	B.platform(self, Vector3(w + 0.4, 0.24, d + 0.4), c, VM.floor, 0.4)
	var save := [M.plaster, M.terracotta, M.teal]
	M.plaster = stucco(col)
	M.terracotta = stucco(col.darkened(0.35))
	M.teal = VM.trim
	var h := 3.3
	var x0 := c.x - w * 0.5
	var x1 := c.x + w * 0.5
	var zf := c.z + d * 0.5     # frente (rua)
	var zb := c.z - d * 0.5     # fundos (mar)
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
	B.hip_roof(self, Vector3(c.x, y0 + h + 0.05, c.z), w + 1.0, d + 1.0, 2.0, VM.clay, 0.12)
	B.label(self, "Casa", Vector3(c.x + 1.7, y0 + 2.75, zf + 0.2), 44, Color(1, 1, 1), Color(0.1, 0.25, 0.35, 0.9))
	# porta de madeira aberta
	var door := B.box(self, Vector3(0.06, 2.2, 1.15), Vector3(c.x + 2.35, y0 + 1.1, zf - 0.55), wood_tint(Color(0.1, 0.45, 0.55)))
	door.name = "door"
	# interior: cama, cozinha, mesa, guarda-roupa, tapete
	var bc := Vector3(c.x - 2.2, y0, zb + 1.4)
	B.box(self, Vector3(1.5, 0.35, 2.1), bc + Vector3(0, 0.175, 0.4), M.oak, true)
	B.box(self, Vector3(1.6, 0.9, 0.08), bc + Vector3(0, 0.45, -0.68), M.oak)
	B.box(self, Vector3(1.42, 0.2, 2.0), bc + Vector3(0, 0.45, 0.4), M.linen)
	B.box(self, Vector3(1.46, 0.05, 1.3), bc + Vector3(0, 0.57, 0.75), B.mat("rough_linen", 1.2, Color(0.95, 0.6, 0.3), 0.95))
	B.box(self, Vector3(0.9, 0.14, 0.4), bc + Vector3(0, 0.62, -0.35), M.linen)
	bed = Interactable.new()
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = Vector3(1.7, 1.0, 2.3)
	cs.shape = sh
	bed.add_child(cs)
	bed.position = bc + Vector3(0, 0.6, 0.4)
	bed.name = "Bed"
	add_child(bed)
	B.model(self, "painted_wooden_cabinet", Vector3(x0 + 0.45, y0, c.z + 1.6), PI * 0.5, 1.0)
	B.model(self, "electric_stove", Vector3(x1 - 0.5, y0, zb + 1.0), -PI * 0.5, 1.0)
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
	var l := OmniLight3D.new()
	l.position = Vector3(c.x, y0 + 2.8, c.z)
	l.omni_range = 7.0
	l.light_color = Color(1.0, 0.82, 0.6)
	add_child(l)
	l.shadow_enabled = Quality.hd
	lanterns.append([l, null, 2.2, true])
	village_points.home_door_out = Vector3(c.x + 1.7, 0.15, zf + 1.2)
	village_points.home_door_in = Vector3(c.x + 1.7, 0.15, zf - 0.8)

# ------------------------------------------------------------------ igreja e praça
func _church_and_praca() -> void:
	var r := PRACA
	var pc := Vector3(r.get_center().x, 0, r.get_center().y)
	B.platform(self, Vector3(r.size.x, 0.2, r.size.y), pc, VM.calcada, 0.4)
	var c := CHURCH_C
	var w := 10.0
	var d := 12.0
	var h := 7.0
	var white := stucco(Color(0.98, 0.97, 0.94))
	var blue := stucco(Color(0.2, 0.42, 0.72))
	var yellow := stucco(Color(0.98, 0.8, 0.3))
	B.box(self, Vector3(w, h, d), c + Vector3(0, h * 0.5, 0), white, true)
	B.box(self, Vector3(w + 0.06, 0.8, d + 0.06), c + Vector3(0, 0.4, 0), blue)
	for sx in [-1.0, 1.0]:
		B.box(self, Vector3(0.5, h, 0.5), c + Vector3(sx * w * 0.5, h * 0.5, -d * 0.5), yellow)
	B.box(self, Vector3(w + 0.3, 0.35, 0.5), c + Vector3(0, h, -d * 0.5), yellow)
	# frontão triangular
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var fz := c.z - d * 0.5 - 0.02
	var pts := [Vector3(c.x - w * 0.5, h + 0.15, fz), Vector3(c.x, h + 3.2, fz), Vector3(c.x + w * 0.5, h + 0.15, fz)]
	for v in pts:
		st.set_normal(Vector3(0, 0, -1))
		st.set_uv(Vector2(v.x, v.y) * 0.5)
		st.add_vertex(v)
	var ped := MeshInstance3D.new()
	ped.mesh = st.commit()
	var pm: StandardMaterial3D = white.duplicate()
	pm.cull_mode = BaseMaterial3D.CULL_DISABLED
	ped.material_override = pm
	add_child(ped)
	B.hip_roof(self, c + Vector3(0, h + 0.1, 0.3), w + 0.8, d + 0.6, 3.1, VM.clay, 0.14)
	_facade(c, Vector3(0, 0, -1), d * 0.5, 0.0, "door", Color(0.45, 0.25, 0.12))
	B.box(self, Vector3(2.0, 3.6, 0.1), c + Vector3(0, 1.8, -d * 0.5 - 0.06), wood_tint(Color(0.45, 0.25, 0.12)))
	for sx in [-1.0, 1.0]:
		_facade(c + Vector3(0, 2.0, 0), Vector3(0, 0, -1), d * 0.5, sx * 2.8, "window", Color(0.2, 0.42, 0.72))
	B.sphere(self, 0.6, c + Vector3(0, h + 1.6, -d * 0.5 - 0.05), B.flat(Color(0.25, 0.45, 0.75), 0.3), Vector3(1, 1, 0.15))   # rosácea
	# torre
	var tc := c + Vector3(w * 0.5 + 1.6, 0, -d * 0.5 + 1.6)
	B.box(self, Vector3(3.2, 13.0, 3.2), tc + Vector3(0, 6.5, 0), white, true)
	B.box(self, Vector3(3.3, 0.7, 3.3), tc + Vector3(0, 0.35, 0), blue)
	for k in [4.5, 9.0, 12.8]:
		B.box(self, Vector3(3.45, 0.3, 3.45), tc + Vector3(0, k, 0), yellow)
	for n in [Vector3(0, 0, -1), Vector3(1, 0, 0), Vector3(-1, 0, 0), Vector3(0, 0, 1)]:
		B.box(self, Vector3(1.1, 1.8, 0.1), tc + n * 1.62 + Vector3(0, 11.0, 0), VM.glass, false, atan2(n.x, n.z))
	B.hip_roof(self, tc + Vector3(0, 13.0, 0), 3.8, 3.8, 3.0, VM.clay, 0.12)
	B.box(self, Vector3(0.14, 1.6, 0.14), tc + Vector3(0, 16.7, 0), B.flat(Color(0.9, 0.85, 0.6), 0.3, 0.7))
	B.box(self, Vector3(0.8, 0.14, 0.14), tc + Vector3(0, 17.1, 0), B.flat(Color(0.9, 0.85, 0.6), 0.3, 0.7))
	B.label(self, "Igreja de São Pedro", c + Vector3(0, h - 0.6, -d * 0.5 - 0.1), 60, Color(0.15, 0.3, 0.55), Color(1, 1, 1, 0.9), PI)
	village_points.church_bell = tc + Vector3(0, 11, 0)
	# árvore central (PC: modelo detalhado; celular: coqueiros)
	B.cyl(self, 2.2, 2.3, 0.45, pc + Vector3(0, 0.3, 0), VM.curb, 24)
	if Quality.hd and B.has_model("island_tree_01"):
		var tree := B.model(self, "island_tree_01", pc + Vector3(0, 0.5, 0), 0.4, 1.0)
		var bb := B.aabb_of(tree)
		if bb.size.y > 0.1:
			tree.scale = Vector3.ONE * clampf(9.0 / bb.size.y, 0.2, 5.0)
	else:
		Palm.spawn(self, pc + Vector3(0.4, 0.5, 0.2), 911)
	var sbc := B.wall(self, Vector3(4.4, 1.5, 4.4), pc + Vector3(0, 0.75, 0))
	sbc.name = "planter_col"
	# bancos virados para a árvore
	for k in 4:
		var a := PI * 0.5 * k + PI * 0.25
		var bp := pc + Vector3(cos(a) * 4.2, 0.1, sin(a) * 3.2)
		var face := atan2(pc.x - bp.x, pc.z - bp.z)
		B.model(self, "painted_wooden_bench", bp, face, 1.0)
		bench_spots.append({"pos": bp + Vector3(0, 0.08, 0), "rot": face, "anim": "Sitting_Idle_Loop", "busy": false})
	for corner in [Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]:
		B.model(self, "planter_box_01", pc + Vector3(corner.x * (r.size.x * 0.5 - 0.8), 0.1, corner.y * (r.size.y * 0.5 - 0.7)), 0.0, 1.0)
	# carrinho de tapioca
	B.model(self, "CoffeeCart_01", pc + Vector3(-7.2, 0.1, 3.0), 2.4, 1.0)
	village_points.cart = pc + Vector3(-6.0, 0.1, 3.2)

# ------------------------------------------------------------------ quiosque (trabalho do herói)
func _quiosque() -> void:
	var c := KIOSK_C
	B.platform(self, Vector3(5.6, 0.2, 5.6), c, M.deckwood, 0.45)
	var y0 := 0.1
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.cyl(self, 0.12, 0.15, 2.8, c + Vector3(sx * 2.4, y0 + 1.4, sz * 2.4), M.post, 8)
	B.hip_roof(self, c + Vector3(0, y0 + 2.8, 0), 6.6, 6.6, 2.8, M.thatch, 0.22)
	var ch := 1.1
	B.box(self, Vector3(4.6, ch, 0.6), c + Vector3(0, y0 + ch * 0.5, 2.0), M.bamboo, true)       # balcão de frente (+Z)
	B.box(self, Vector3(0.6, ch, 3.4), c + Vector3(-2.0, y0 + ch * 0.5, 0.5), M.bamboo, true)
	B.box(self, Vector3(0.6, ch, 3.4), c + Vector3(2.0, y0 + ch * 0.5, 0.5), M.bamboo, true)
	B.box(self, Vector3(4.9, 0.07, 0.85), c + Vector3(0, y0 + ch + 0.035, 2.0), M.oak)
	B.box(self, Vector3(4.2, 1.5, 0.35), c + Vector3(0, y0 + 0.75, -2.1), M.oak)              # prateleira atrás
	var cols := [Color(0.2, 0.55, 0.2), Color(0.85, 0.85, 0.9), Color(0.65, 0.4, 0.1)]
	for i in 9:
		B.cyl(self, 0.045, 0.05, 0.3, c + Vector3(-1.6 + i * 0.4, y0 + 1.65, -2.1), B.flat(cols[i % 3], 0.15, 0.1), 8)
	var coco := B.flat(Color(0.42, 0.52, 0.16), 0.6)
	for k in 7:
		B.sphere(self, 0.13, c + Vector3(-1.4 + (k % 4) * 0.28, y0 + ch + 0.18 + (k / 4) * 0.2, 2.0), coco)
	B.model(self, "plastic_crate_01", c + Vector3(1.4, y0, -1.2), 0.0, 1.0)
	B.model(self, "wooden_bucket_01", c + Vector3(1.6, y0 + ch + 0.07, 2.0), 0.0, 0.7)
	B.box(self, Vector3(3.6, 0.6, 0.08), c + Vector3(0, y0 + 2.5, 2.42), M.planks)
	B.label(self, "Quiosque Maré Alta", c + Vector3(0, y0 + 2.5, 2.48), 64, Color(1.0, 0.95, 0.8), Color(0.25, 0.12, 0.02, 1.0))
	B.box(self, Vector3(3.9, 0.42, 0.05), c + Vector3(0, y0 + 0.72, 2.33), M.dark)
	var board := ""
	for dish_id in Economy.KIOSK_MENU:
		var dish: Dictionary = Economy.dish(dish_id)
		if board != "":
			board += " · "
		board += "%s %s" % [tr(str(dish.name)), Core.fmt_money(int(dish.price))]
	B.label(self, board, c + Vector3(0, y0 + 0.72, 2.37), 36, Color(1, 0.95, 0.8), Color(0, 0, 0, 0.6))
	for k in 2:
		B.model(self, "plastic_monobloc_chair_01", c + Vector3(-3.5 + k * 7.0, 0, 4.5), PI + (0.4 if k == 0 else -0.4), 1.0)
	kiosk_counter = Interactable.new()
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = Vector3(4.6, 1.5, 1.4)
	cs.shape = sh
	kiosk_counter.add_child(cs)
	kiosk_counter.position = c + Vector3(0, y0 + 0.9, 2.0)
	kiosk_counter.name = "KioskCounter"
	add_child(kiosk_counter)
	for k in 3:
		var p := c + Vector3(-1.3 + k * 1.3, 0.1, 3.0)
		kiosk_spots.append({"pos": p, "rot": PI, "busy": false})
	village_points.kiosk_work = c + Vector3(0, 0.1, 0.8)
	var l := OmniLight3D.new()
	l.position = c + Vector3(0, 2.5, 0)
	l.omni_range = 6.5
	l.light_color = Color(1.0, 0.75, 0.45)
	add_child(l)
	lanterns.append([l, null, 1.6, false])

# ------------------------------------------------------------------ barraca de praia
func _barraca() -> void:
	var c := Vector3(62, 0, -20)
	var stripes := Image.create(64, 8, false, Image.FORMAT_RGB8)
	for x in 64:
		for y in 8:
			stripes.set_pixel(x, y, Color(0.95, 0.85, 0.2) if (x / 8) % 2 == 0 else Color(0.1, 0.5, 0.75))
	var cm := StandardMaterial3D.new()
	cm.albedo_texture = ImageTexture.create_from_image(stripes)
	cm.cull_mode = BaseMaterial3D.CULL_DISABLED
	cm.roughness = 0.9
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.cyl(self, 0.05, 0.05, 2.6, c + Vector3(sx * 2.8, 1.3, sz * 2.0), M.oak, 8)
	var roof := B.box(self, Vector3(6.2, 0.04, 4.6), c + Vector3(0, 2.65, 0), cm)
	roof.rotation.x = 0.06
	B.box(self, Vector3(2.4, 0.9, 0.7), c + Vector3(-1.6, 0.45, -1.4), M.bamboo, true)
	B.label(self, "Barraca da Dona Rita", c + Vector3(0, 2.3, 2.1), 56, Color(0.1, 0.35, 0.6), Color(1, 1, 1, 0.9))
	for k in 3:
		var tp := c + Vector3(-2.0 + k * 2.2, 0, 3.6)
		B.model(self, "outdoor_table_chair_set_01", tp, k * 0.7, 1.0)
		_umbrella_hd(tp + Vector3(0, 0, 0), 1.5)
	B.model(self, "plastic_crate_01", c + Vector3(1.8, 0, -1.4), 0.3, 1.0)
	B.model(self, "plastic_monobloc_chair_01", c + Vector3(2.4, 0, -0.4), 2.5, 1.0)
	village_points.barraca = c + Vector3(-1.6, 0, -0.6)
	quest_board = Interactable.new()
	quest_board.name = "DonaRita"
	var qcs := CollisionShape3D.new()
	var qsh := BoxShape3D.new()
	qsh.size = Vector3(1.4, 1.8, 1.2)
	qcs.shape = qsh
	quest_board.add_child(qcs)
	quest_board.position = c + Vector3(-1.6, 1.0, 0.4)
	quest_board.prompt_fn = func() -> String:
		var st := str(Core.quests.get("cocos_rita", ""))
		if st == "done":
			return ""
		if st == "":
			return tr("Dona Rita: aceitar encomenda de cocos")
		return tr("Dona Rita: entregar cocos")
	quest_board.action_fn = func() -> void:
		if str(Core.quests.get("cocos_rita", "")) == "":
			Core.accept_quest("cocos_rita")
		else:
			Core.complete_quest("cocos_rita")
	add_child(quest_board)

func _umbrella_hd(p: Vector3, r: float) -> void:
	_umbrella(p, r)

# ------------------------------------------------------------------ objetos da vila
func _bike(p: Vector3, rot: float, col: Color) -> void:
	var n := Node3D.new()
	n.position = p
	n.rotation = Vector3(0, rot, 0.18)
	add_child(n)
	var tire := B.flat(Color(0.08, 0.08, 0.08), 0.7)
	var frame := B.flat(col, 0.35, 0.6)
	for zz in [-0.52, 0.52]:
		var t := MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = 0.29
		tm.outer_radius = 0.34
		tm.rings = 24
		tm.ring_segments = 8
		t.mesh = tm
		t.material_override = tire
		t.position = Vector3(0, 0.34, zz)
		t.rotation.z = PI * 0.5
		n.add_child(t)
	var bars := [[Vector3(0, 0.34, -0.52), Vector3(0, 0.75, 0.3)], [Vector3(0, 0.34, 0.52), Vector3(0, 0.75, 0.3)],
		[Vector3(0, 0.34, -0.52), Vector3(0, 0.8, -0.2)], [Vector3(0, 0.8, -0.2), Vector3(0, 0.75, 0.3)],
		[Vector3(0, 0.75, 0.3), Vector3(0, 1.0, 0.42)], [Vector3(0, 0.8, -0.2), Vector3(0, 0.92, -0.28)]]
	for b in bars:
		var a: Vector3 = b[0]
		var e: Vector3 = b[1]
		var cyl := B.cyl(n, 0.022, 0.022, a.distance_to(e), (a + e) * 0.5, frame, 6)
		cyl.look_at_from_position(cyl.position, e, Vector3.UP if absf((e - a).normalized().dot(Vector3.UP)) < 0.99 else Vector3.RIGHT)
		cyl.rotate_object_local(Vector3.RIGHT, PI * 0.5)
	B.box(n, Vector3(0.5, 0.03, 0.03), Vector3(0, 1.0, 0.42), tire)
	B.box(n, Vector3(0.14, 0.05, 0.24), Vector3(0, 0.95, -0.28), tire)

func _jangada2(p: Vector3, rot: float) -> void:
	var j := Node3D.new()
	j.position = p
	j.rotation.y = rot
	add_child(j)
	for k in 6:
		var log_ := B.cyl(j, 0.12, 0.12, 6.0, Vector3(-0.6 + k * 0.24, 0.12, 0), M.post, 8)
		log_.rotation.x = PI * 0.5
	B.cyl(j, 0.06, 0.07, 5.5, Vector3(0, 2.8, 1.0), M.oak, 8)
	var sail := MeshInstance3D.new()
	var st := SurfaceTool.new()
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

func _village_props() -> void:
	var bike_spots := [[Vector3(57.6, 0.15, 25.6), 0.0, Color(0.8, 0.15, 0.15)], [Vector3(66.2, 0.15, 25.6), 0.1, Color(0.1, 0.4, 0.75)],
		[Vector3(48.4, 0.15, 34.4), PI, Color(0.95, 0.75, 0.1)], [Vector3(84.2, 0.15, 25.7), -0.1, Color(0.15, 0.55, 0.3)], [Vector3(70.5, 0.25, 36.0), PI * 0.5, Color(0.9, 0.9, 0.9)]]
	for b in bike_spots:
		_bike(b[0], b[1] + PI * 0.5, b[2])
	for k in 3:
		var x := 52.0 + k * 13.0
		_jangada2(Vector3(x, _height(x, -29.5) - 0.12, -29.5), 0.3 - k * 0.25)
	for k in 6:
		var x2 := 50.0 + k * 9.0
		B.model(self, ["potted_plant_01", "potted_plant_04", "planter_pot_clay"][k % 3], Vector3(x2 + 2.8, 0.15, 26.4), 0.0, 1.0)
	if Quality.hd:
		B.model(self, "coast_rocks_01", Vector3(101, -0.5, -25), 0.6, 1.0)
		B.model(self, "coast_rocks_01", Vector3(-44, -0.5, -25.5), 2.2, 1.0)
		for k in 18:
			var sp := Vector2(40 + k * 3.4, 15.0 if k % 2 == 0 else 45.5)
			B.model(self, ["shrub_01", "shrub_02", "shrub_03"][k % 3], Vector3(sp.x, 0, sp.y), k * 1.3, 0.9)

func _village_palms() -> void:
	# coqueiral entre a vila e a praia, e alguns nos quintais
	var rng := RandomNumberGenerator.new()
	rng.seed = 4242
	var excl := [Rect2(34, -17.5, 9, 9), Rect2(36.2, -17, 3.6, 44), Rect2(55, -25, 14, 11), Rect2(40, 15.5, 62, 42), Rect2(0, 24.5, 104, 11)]
	var n := 46 if Quality.hd else 22
	var placed := 0
	var tries := 0
	while placed < n and tries < 600:
		tries += 1
		var p := Vector2(rng.randf_range(44, 101), rng.randf_range(-23, 13))
		if tries % 4 == 0:
			p = Vector2(rng.randf_range(42, 101), rng.randf_range(43, 54))
		var bad := false
		for r in excl:
			if r.has_point(p):
				bad = true
				break
		if bad:
			continue
		Palm.spawn(self, Vector3(p.x, _height(p.x, p.y) - 0.05, p.y), 3000 + placed)
		placed += 1

func _street_lamps() -> void:
	var spots := []
	var x := 8.0
	while x < 98.0:
		spots.append([Vector3(x, 0.15, STREET_Z - 3.5), 0.0])
		spots.append([Vector3(x + 6.0, 0.15, STREET_Z + 3.5), PI])
		x += 12.0
	var pc := PRACA.get_center()
	for cc in [Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]:
		spots.append([Vector3(pc.x + cc.x * 7.8, 0.1, pc.y + cc.y * 3.6), 0.0])
	spots.append([Vector3(38.9, 0.05, 0.0), 0.0])
	spots.append([Vector3(38.9, 0.05, 14.0), 0.0])
	for s in spots:
		var p: Vector3 = s[0]
		var top := 4.2
		if B.has_model("street_lamp_01"):
			var m := B.model(self, "street_lamp_01", p, s[1], 1.0)
			var bb := B.aabb_of(m)
			if bb.size.y > 0.5:
				top = bb.end.y - 0.35
		else:
			B.cyl(self, 0.06, 0.09, 4.2, p + Vector3(0, 2.1, 0), B.flat(Color(0.12, 0.14, 0.13), 0.5, 0.6), 10)
		var glow := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radius = 0.12
		sm.height = 0.24
		glow.mesh = sm
		var gm := StandardMaterial3D.new()
		gm.albedo_color = Color(1, 0.85, 0.6)
		gm.emission_enabled = true
		gm.emission = Color(1.0, 0.75, 0.4)
		gm.emission_energy_multiplier = 0.0
		glow.material_override = gm
		glow.position = p + Vector3(0, top, 0)
		add_child(glow)
		if Quality.hd:
			var l := OmniLight3D.new()
			l.position = p + Vector3(0, top - 0.2, 0)
			l.omni_range = 9.0
			l.light_color = Color(1.0, 0.75, 0.45)
			l.light_energy = 0.0
			add_child(l)
			lanterns.append([l, gm, 1.8, false])
		else:
			lanterns.append([null, gm, 0.0, false])

# ------------------------------------------------------------------ rotas dos moradores
func _village_routes() -> void:
	var zn := STREET_Z - 2.9
	var zs := STREET_Z + 2.9
	village_paths = [
		[Vector3(4, 0.15, zn), Vector3(37, 0.15, zn), Vector3(70, 0.15, zn), Vector3(97, 0.15, zn)],
		[Vector3(97, 0.15, zs), Vector3(64, 0.15, zs), Vector3(30, 0.15, zs), Vector3(4, 0.15, zs)],
		[Vector3(67.5, 0.2, 35.6), Vector3(82.5, 0.2, 35.6), Vector3(82.5, 0.2, 42.6), Vector3(67.5, 0.2, 42.6), Vector3(67.5, 0.2, 35.6)],
		[Vector3(38, 0.05, zn), Vector3(38, 0.05, 5.0), Vector3(38, 0.05, -7.5), Vector3(48, 0, -22), Vector3(90, 0, -24)],
		[Vector3(30, 0.15, zn), Vector3(55, 0.15, zn), Vector3(55, 0.15, zs), Vector3(85, 0.15, zs)],
	]
	village_points.kiosk_approach = [Vector3(38, 0.15, zn), Vector3(38, 0.05, 5.0), Vector3(38, 0.05, -8.0)]
	village_points.home_route = [village_points.home_door_out, Vector3(HOME_C.x + 1.7, 0.15, zn)]

func set_night(t: float) -> void:
	super.set_night(t)
