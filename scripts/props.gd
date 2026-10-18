extends RefCounted
class_name P
## Biblioteca de props cartoon (v0.7). Cada nome de modelo antigo (Poly Haven) tem aqui uma versão
## procedural, gordinha e colorida, no estilo do resto do jogo. B.model() usa estes construtores primeiro.
## Todos constroem em espaço local, com a base em y = 0 e a "frente" para +Z.

const WOOD: = Color(0.78, 0.5, 0.28)
const WOOD_DARK: = Color(0.52, 0.31, 0.17)
const WOOD_LIGHT: = Color(0.93, 0.72, 0.46)
const CREAM: = Color(0.99, 0.94, 0.82)
const TEAL: = Color(0.1, 0.72, 0.72)
const CORAL: = Color(1.0, 0.45, 0.35)
const YELLOW: = Color(1.0, 0.82, 0.25)
const LEAF: = Color(0.3, 0.75, 0.3)
const LEAF_DARK: = Color(0.16, 0.55, 0.26)
const CLAY: = Color(0.86, 0.45, 0.28)
const METAL: = Color(0.62, 0.66, 0.7)
const WHITE: = Color(0.97, 0.97, 0.95)

static var _builders: = {}

static func _init_builders() -> void :
	if not _builders.is_empty():
		return
	_builders = {
		"bar_chair_round_01": stool, "wooden_stool_01": stool,
		"outdoor_table_chair_set_01": table_set, "WoodenTable_01": table_rect,
		"plastic_monobloc_chair_01": func(r): chair(r, WHITE),
		"painted_wooden_chair_01": func(r): chair(r, TEAL),
		"WoodenChair_01": func(r): chair(r, WOOD),
		"Shelf_01": shelf, "wooden_bucket_01": bucket,
		"wooden_crate_01": func(r): crate(r, WOOD_LIGHT),
		"plastic_crate_01": func(r): crate(r, Color(0.2, 0.55, 0.9)),
		"wooden_lantern_01": lantern, "vintage_oil_lamp": oil_lamp,
		"wicker_basket_01": basket, "wicker_basket_02": basket,
		"potted_plant_01": func(r): plant(r, 0.9), "potted_plant_02": func(r): plant(r, 1.2),
		"potted_plant_04": func(r): plant(r, 0.7), "planter_pot_clay": func(r): plant(r, 0.8),
		"pachira_aquatica_01": func(r): plant(r, 1.5), "planter_box_01": planter_box,
		"lambis_shell": shell, "ceramic_vase_02": vase, "wooden_bowl_01": bowl,
		"GothicBed_01": bed, "painted_wooden_nightstand": nightstand, "side_table_01": nightstand,
		"painted_wooden_cabinet": cabinet, "painted_wooden_bench": bench, "Rockingchair_01": rocking_chair,
		"ceiling_fan": ceiling_fan, "ornate_mirror_01": mirror, "hanging_picture_frame_02": picture,
		"throw_pillows_01": pillows, "lifebuoy": lifebuoy, "electric_stove": stove,
		"CashRegister_01": register, "CoffeeCart_01": coffee_cart, "street_lamp_01": street_lamp,
		"island_tree_01": island_tree,
	}

static func has(n: String) -> bool:
	_init_builders()
	return _builders.has(n)

static func build(n: String) -> Node3D:
	_init_builders()
	var root: = Node3D.new()
	root.name = n
	_builders[n].call(root)
	return root

static func m(c: Color, rough: = 0.85) -> Material:
	return B.flat(c, rough)

static func glow(c: Color, energy: = 2.0) -> Material:
	var key: = "glow|%s|%s" % [c.to_html(), energy]
	if B._mats.has(key):
		return B._mats[key]
	var mt: = StandardMaterial3D.new()
	mt.albedo_color = c
	mt.emission_enabled = true
	mt.emission = c
	mt.emission_energy_multiplier = energy
	mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	B._mats[key] = mt
	return mt

static func _legs(r: Node3D, hx: float, hz: float, h: float, rad: float, c: Color) -> void :
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.cyl(r, rad, rad * 1.1, h, Vector3(sx * hx, h * 0.5, sz * hz), m(c), 6)

# ------------------------------------------------------------------ assentos e mesas
static func stool(r: Node3D) -> void :
	B.cyl(r, 0.24, 0.22, 0.1, Vector3(0, 0.74, 0), m(CORAL), 14)
	B.cyl(r, 0.2, 0.2, 0.03, Vector3(0, 0.8, 0), m(Color(1.0, 0.62, 0.5)), 14)
	# almofada capitonê com botões
	B.sphere(r, 0.19, Vector3(0, 0.81, 0), m(Color(1.0, 0.55, 0.45), 0.9), Vector3(1.0, 0.22, 1.0))
	for k in 5:
		var a: = TAU * k / 5.0
		B.sphere(r, 0.015, Vector3(cos(a) * 0.1, 0.85, sin(a) * 0.1), m(Color(0.8, 0.3, 0.25)))
	for i in 3:
		var a: = TAU * i / 3.0
		var leg: = B.cyl(r, 0.025, 0.03, 0.74, Vector3(cos(a) * 0.14, 0.37, sin(a) * 0.14), m(WOOD_DARK), 6)
		leg.rotation = Vector3(sin(a) * 0.12, 0, - cos(a) * 0.12)
	var ring: = TorusMesh.new()
	ring.inner_radius = 0.13
	ring.outer_radius = 0.16
	var mi: = MeshInstance3D.new()
	mi.mesh = ring
	mi.material_override = m(WOOD_DARK)
	mi.position = Vector3(0, 0.28, 0)
	r.add_child(mi)

static func chair(r: Node3D, c: Color) -> void :
	# v0.7.2: assento de ripas, encosto com travessas e ripas verticais, almofada, pés com travessa
	for k in 4:
		B.box(r, Vector3(0.46, 0.05, 0.1), Vector3(0, 0.45, -0.165 + k * 0.11), m(c))
	B.box(r, Vector3(0.38, 0.05, 0.36), Vector3(0, 0.49, 0.01), m(c.lightened(0.45), 0.95))
	for sx in [-0.2, 0.2]:
		B.box(r, Vector3(0.05, 0.55, 0.05), Vector3(sx, 0.74, -0.2), m(c.darkened(0.15)))
	for yy in [0.62, 0.96]:
		B.box(r, Vector3(0.44, 0.07, 0.04), Vector3(0, yy, -0.2), m(c))
	for k in 3:
		B.box(r, Vector3(0.05, 0.3, 0.03), Vector3(-0.1 + k * 0.1, 0.79, -0.2), m(c))
	_legs(r, 0.19, 0.18, 0.43, 0.025, c.darkened(0.25))
	for sx in [-0.19, 0.19]:
		B.box(r, Vector3(0.025, 0.025, 0.36), Vector3(sx, 0.14, 0), m(c.darkened(0.25)))

static func round_table(r: Node3D, pos: Vector3, rad: float, top: Color) -> void :
	B.cyl(r, rad, rad, 0.06, pos + Vector3(0, 0.74, 0), m(top), 18)
	# toalha xadrez com barrado
	B.cyl(r, rad * 1.04, rad * 1.04, 0.012, pos + Vector3(0, 0.776, 0), m(Color(1.0, 0.97, 0.92), 0.95), 24)
	B.cyl(r, rad * 1.06, rad * 1.02, 0.12, pos + Vector3(0, 0.72, 0), m(Color(0.95, 0.3, 0.3), 0.95), 24)
	for k in 6:
		var a: = TAU * k / 6.0
		B.box(r, Vector3(rad * 0.9, 0.004, 0.06), pos + Vector3(0, 0.783, 0), m(Color(0.95, 0.3, 0.3), 0.95)).rotation.y = a
	B.cyl(r, 0.035, 0.035, 0.09, pos + Vector3(rad * 0.4, 0.83, 0), m(Color(0.95, 0.95, 0.95), 0.4), 10)
	B.cyl(r, 0.03, 0.03, 0.07, pos + Vector3(rad * 0.4 + 0.08, 0.82, 0.02), m(Color(0.85, 0.2, 0.15), 0.4), 10)
	B.cyl(r, 0.04, 0.04, 0.72, pos + Vector3(0, 0.37, 0), m(WOOD_DARK), 8)
	B.cyl(r, 0.24, 0.28, 0.04, pos + Vector3(0, 0.02, 0), m(WOOD_DARK), 12)

## Mesa redonda com duas cadeiras nos lados ±X, viradas para a mesa.
static func table_set(r: Node3D) -> void :
	round_table(r, Vector3.ZERO, 0.55, WOOD_LIGHT)
	for sx in [-1.0, 1.0]:
		var ch: = Node3D.new()
		ch.position = Vector3(sx * 0.85, 0, 0)
		ch.rotation.y = sx * PI * 0.5
		r.add_child(ch)
		chair(ch, TEAL if sx < 0 else CORAL)

static func table_rect(r: Node3D) -> void :
	B.box(r, Vector3(1.4, 0.06, 0.8), Vector3(0, 0.77, 0), m(WOOD_LIGHT))
	B.box(r, Vector3(1.44, 0.03, 0.84), Vector3(0, 0.735, 0), m(WOOD))
	for sz in [-1.0, 1.0]:
		B.box(r, Vector3(1.2, 0.1, 0.03), Vector3(0, 0.67, sz * 0.34), m(WOOD))
	for sx in [-1.0, 1.0]:
		B.box(r, Vector3(0.03, 0.1, 0.62), Vector3(sx * 0.6, 0.67, 0), m(WOOD))
		for sz in [-1.0, 1.0]:
			_turned_leg(r, Vector3(sx * 0.6, 0.0, sz * 0.32), 0.72, 0.03, WOOD_DARK)
	# toalhinha de renda
	B.cyl(r, 0.28, 0.28, 0.006, Vector3(0, 0.803, 0), m(Color(1, 1, 1), 0.95), 32)

static func bench(r: Node3D) -> void :
	B.box(r, Vector3(1.6, 0.08, 0.42), Vector3(0, 0.45, 0), m(TEAL))
	B.box(r, Vector3(1.6, 0.36, 0.06), Vector3(0, 0.72, -0.2), m(TEAL))
	_legs(r, 0.7, 0.16, 0.42, 0.035, WOOD_DARK)

static func rocking_chair(r: Node3D) -> void :
	chair(r, WOOD)
	for sx in [-1.0, 1.0]:
		var rk: = B.box(r, Vector3(0.04, 0.05, 0.8), Vector3(sx * 0.2, 0.04, 0), m(WOOD_DARK))
		rk.rotation.x = 0.05

# ------------------------------------------------------------------ cozinha, balcão, depósito
static func shelf(r: Node3D) -> void :
	var w: = m(WOOD)
	for sx in [-1.0, 1.0]:
		B.box(r, Vector3(0.06, 1.8, 0.4), Vector3(sx * 0.6, 0.9, 0), w)
	for k in 4:
		B.box(r, Vector3(1.24, 0.05, 0.4), Vector3(0, 0.1 + k * 0.52, 0), w)
	var cols: = [CORAL, YELLOW, TEAL, LEAF, CREAM]
	for k in 3:
		for i in 5:
			var c: Color = cols[(i + k) % cols.size()]
			B.cyl(r, 0.055, 0.06, 0.24, Vector3(-0.44 + i * 0.22, 0.25 + k * 0.52, 0.02), m(c, 0.4), 8)

static func bucket(r: Node3D) -> void :
	B.cyl(r, 0.24, 0.19, 0.4, Vector3(0, 0.2, 0), m(WOOD_LIGHT), 12)
	for y in [0.08, 0.32]:
		B.cyl(r, 0.235 - (0.32 - y) * 0.12, 0.235 - (0.32 - y) * 0.12, 0.035, Vector3(0, y, 0), m(METAL, 0.5), 12)
	B.cyl(r, 0.2, 0.2, 0.02, Vector3(0, 0.37, 0), m(Color(0.75, 0.92, 1.0), 0.2), 12)

static func crate(r: Node3D, c: Color) -> void :
	B.box(r, Vector3(0.6, 0.4, 0.42), Vector3(0, 0.2, 0), m(c))
	B.box(r, Vector3(0.62, 0.06, 0.44), Vector3(0, 0.37, 0), m(c.darkened(0.2)))
	B.box(r, Vector3(0.62, 0.06, 0.44), Vector3(0, 0.03, 0), m(c.darkened(0.2)))
	for i in 3:
		B.sphere(r, 0.09, Vector3(-0.16 + i * 0.16, 0.42, 0), m([CORAL, YELLOW, LEAF][i]))

static func lantern(r: Node3D) -> void :
	B.box(r, Vector3(0.24, 0.04, 0.24), Vector3(0, 0.36, 0), m(WOOD_DARK))
	B.box(r, Vector3(0.2, 0.04, 0.2), Vector3(0, 0.02, 0), m(WOOD_DARK))
	B.box(r, Vector3(0.14, 0.28, 0.14), Vector3(0, 0.19, 0), glow(Color(1.0, 0.75, 0.35), 2.5))
	B.cyl(r, 0.01, 0.01, 0.3, Vector3(0, 0.52, 0), m(WOOD_DARK), 4)

static func basket(r: Node3D) -> void :
	B.cyl(r, 0.24, 0.18, 0.26, Vector3(0, 0.13, 0), m(Color(0.86, 0.65, 0.38)), 12)
	for i in 4:
		B.sphere(r, 0.08, Vector3(-0.1 + (i % 2) * 0.2, 0.28, -0.06 + (i / 2) * 0.12), m([YELLOW, CORAL, LEAF, Color(0.6, 0.2, 0.6)][i]))

static func stove(r: Node3D) -> void :
	B.box(r, Vector3(0.9, 0.82, 0.6), Vector3(0, 0.45, 0), m(WHITE, 0.4))
	B.box(r, Vector3(0.92, 0.04, 0.62), Vector3(0, 0.88, 0), m(Color(0.2, 0.2, 0.22), 0.3))
	B.box(r, Vector3(0.9, 0.2, 0.06), Vector3(0, 0.98, -0.28), m(WHITE, 0.4))
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			var bp: = Vector3(sx * 0.22, 0.905, sz * 0.13)
			B.cyl(r, 0.1, 0.1, 0.012, bp, m(Color(0.12, 0.12, 0.13)), 24)
			B.cyl(r, 0.045, 0.045, 0.02, bp + Vector3(0, 0.01, 0), m(Color(0.25, 0.25, 0.27), 0.4), 24)
			for k in 4:
				B.box(r, Vector3(0.2, 0.012, 0.015), bp + Vector3(0, 0.022, 0), m(Color(0.08, 0.08, 0.08))).rotation.y = k * PI * 0.25
	# porta do forno com visor e puxador
	B.box(r, Vector3(0.74, 0.46, 0.03), Vector3(0, 0.38, 0.305), m(WHITE.darkened(0.05), 0.4))
	B.box(r, Vector3(0.5, 0.24, 0.02), Vector3(0, 0.4, 0.322), m(Color(0.15, 0.17, 0.2), 0.1))
	B._beam(r, Vector3(-0.28, 0.66, 0.35), Vector3(0.28, 0.66, 0.35), 0.014, m(METAL, 0.3))
	for sx in [-0.28, 0.28]:
		B._beam(r, Vector3(sx, 0.66, 0.35), Vector3(sx, 0.66, 0.31), 0.01, m(METAL, 0.3))
	for k in 4:
		var kn: = B.cyl(r, 0.03, 0.03, 0.03, Vector3(-0.27 + k * 0.18, 0.78, 0.315), m(Color(0.15, 0.15, 0.17), 0.4), 16)
		kn.rotation.x = PI * 0.5
	B.box(r, Vector3(0.86, 0.06, 0.04), Vector3(0, 0.06, 0.29), m(Color(0.2, 0.2, 0.22)))
	# panela no fogo
	B.cyl(r, 0.11, 0.1, 0.12, Vector3(0.22, 0.98, 0.13), m(CORAL, 0.4), 24)
	B.cyl(r, 0.115, 0.115, 0.02, Vector3(0.22, 1.05, 0.13), m(CORAL.darkened(0.2), 0.4), 24)
	B.sphere(r, 0.025, Vector3(0.22, 1.07, 0.13), m(Color(0.15, 0.15, 0.17)))

static func register(r: Node3D) -> void :
	B.box(r, Vector3(0.42, 0.14, 0.36), Vector3(0, 0.07, 0), m(CORAL))
	var scr: = B.box(r, Vector3(0.3, 0.16, 0.04), Vector3(0, 0.22, -0.1), m(Color(0.2, 0.25, 0.3)))
	scr.rotation.x = -0.3
	B.box(r, Vector3(0.26, 0.12, 0.02), Vector3(0, 0.225, -0.077), glow(Color(0.4, 1.0, 0.7), 1.2)).rotation.x = -0.3
	for i in 6:
		B.box(r, Vector3(0.06, 0.02, 0.05), Vector3(-0.12 + (i % 3) * 0.12, 0.15, 0.05 + (i / 3) * 0.07), m(CREAM))

static func coffee_cart(r: Node3D) -> void :
	B.box(r, Vector3(1.4, 0.8, 0.7), Vector3(0, 0.7, 0), m(YELLOW))
	B.box(r, Vector3(1.5, 0.06, 0.8), Vector3(0, 1.13, 0), m(WOOD))
	for sx in [-1.0, 1.0]:
		var w: = B.cyl(r, 0.3, 0.3, 0.06, Vector3(sx * 0.5, 0.3, 0.38), m(Color(0.2, 0.2, 0.22)), 14)
		w.rotation.x = PI * 0.5
	B.cyl(r, 0.03, 0.03, 1.5, Vector3(0.5, 1.9, 0), m(WOOD_DARK), 6)
	B.cyl(r, 0.02, 0.9, 0.3, Vector3(0.5, 2.6, 0), m(CORAL), 12)

# ------------------------------------------------------------------ decoração
static func plant(r: Node3D, s: float) -> void :
	B.cyl(r, 0.2 * s, 0.15 * s, 0.32 * s, Vector3(0, 0.16 * s, 0), m(CLAY), 10)
	B.cyl(r, 0.21 * s, 0.21 * s, 0.05 * s, Vector3(0, 0.32 * s, 0), m(CLAY.darkened(0.15)), 10)
	var leaf: = m(LEAF)
	var leaf2: = m(LEAF_DARK)
	B.sphere(r, 0.26 * s, Vector3(0, 0.58 * s, 0), leaf, Vector3(1, 0.9, 1))
	B.sphere(r, 0.18 * s, Vector3(0.14 * s, 0.78 * s, 0.05 * s), leaf2)
	B.sphere(r, 0.17 * s, Vector3(-0.12 * s, 0.74 * s, -0.08 * s), leaf)

static func planter_box(r: Node3D) -> void :
	B.box(r, Vector3(1.0, 0.45, 0.45), Vector3(0, 0.225, 0), m(WOOD))
	for i in 4:
		B.sphere(r, 0.16, Vector3(-0.36 + i * 0.24, 0.52, 0), m([CORAL, YELLOW, Color(0.95, 0.4, 0.7), CORAL][i]))
		B.sphere(r, 0.14, Vector3(-0.3 + i * 0.22, 0.45, 0.08), m(LEAF))

static func shell(r: Node3D) -> void :
	B.sphere(r, 0.1, Vector3(0, 0.06, 0), m(Color(1.0, 0.8, 0.72), 0.5), Vector3(1.4, 0.7, 1))
	var c: = B.cyl(r, 0.0, 0.06, 0.16, Vector3(0.12, 0.07, 0), m(Color(1.0, 0.62, 0.55), 0.5), 8)
	c.rotation.z = - PI * 0.5

static func vase(r: Node3D) -> void :
	B.sphere(r, 0.14, Vector3(0, 0.16, 0), m(TEAL, 0.3), Vector3(1, 1.2, 1))
	B.cyl(r, 0.14, 0.14, 0.02, Vector3(0, 0.16, 0), m(YELLOW, 0.3), 32)
	B.cyl(r, 0.06, 0.08, 0.12, Vector3(0, 0.36, 0), m(TEAL, 0.3), 24)
	B.cyl(r, 0.075, 0.06, 0.03, Vector3(0, 0.43, 0), m(TEAL.darkened(0.15), 0.3), 24)
	var stem: = m(LEAF_DARK)
	var fl: = [CORAL, YELLOW, Color(0.95, 0.45, 0.75), WHITE, CORAL]
	for k in 5:
		var a: = TAU * k / 5.0
		var st: = B.cyl(r, 0.006, 0.006, 0.32, Vector3(cos(a) * 0.04, 0.55, sin(a) * 0.04), stem, 6)
		st.rotation = Vector3(sin(a) * 0.3, 0, - cos(a) * 0.3)
		var top: = Vector3(cos(a) * 0.09, 0.7, sin(a) * 0.09)
		for j in 5:
			var b2: = TAU * j / 5.0
			B.sphere(r, 0.025, top + Vector3(cos(b2) * 0.03, 0, sin(b2) * 0.03), m(fl[k]), Vector3(1, 0.5, 1))
		B.sphere(r, 0.016, top + Vector3(0, 0.01, 0), m(Color(1.0, 0.85, 0.2)))

static func bowl(r: Node3D) -> void :
	B.cyl(r, 0.18, 0.1, 0.1, Vector3(0, 0.05, 0), m(WOOD_LIGHT), 12)
	for i in 3:
		B.sphere(r, 0.06, Vector3(-0.06 + i * 0.06, 0.11, 0), m([CORAL, YELLOW, LEAF][i]))

static func mirror(r: Node3D) -> void :
	B.box(r, Vector3(0.7, 0.95, 0.05), Vector3(0, 0.0, 0), m(Color(0.9, 0.7, 0.3), 0.35))
	B.box(r, Vector3(0.56, 0.8, 0.02), Vector3(0, 0.0, 0.03), m(Color(0.75, 0.92, 1.0), 0.05))

static func picture(r: Node3D) -> void :
	B.box(r, Vector3(0.8, 0.6, 0.04), Vector3.ZERO, m(WOOD_DARK))
	B.box(r, Vector3(0.68, 0.48, 0.02), Vector3(0, 0, 0.025), m(Color(0.45, 0.8, 0.95)))
	B.box(r, Vector3(0.68, 0.16, 0.02), Vector3(0, -0.16, 0.03), m(Color(0.98, 0.85, 0.55)))
	B.sphere(r, 0.07, Vector3(0.18, 0.1, 0.035), m(YELLOW))

static func pillows(r: Node3D) -> void :
	pass

static func lifebuoy(r: Node3D) -> void :
	var t: = TorusMesh.new()
	t.inner_radius = 0.2
	t.outer_radius = 0.32
	t.rings = 24
	var mi: = MeshInstance3D.new()
	mi.mesh = t
	mi.material_override = m(Color(1.0, 0.3, 0.25), 0.6)
	r.add_child(mi)
	for i in 4:
		var a: = TAU * i / 4.0 + PI * 0.25
		B.box(r, Vector3(0.1, 0.13, 0.13), Vector3(cos(a) * 0.26, 0, sin(a) * 0.26), m(WHITE)).rotation.y = - a

# ------------------------------------------------------------------ quarto (v0.7.3: móveis detalhados)
static func _turned_leg(r: Node3D, p: Vector3, h: float, rad: float, c: Color) -> void :
	# perna torneada: base, anéis e bolacha no pé
	B.cyl(r, rad, rad * 0.8, h, p + Vector3(0, h * 0.5, 0), m(c), 16)
	for t in [0.18, 0.55, 0.85]:
		B.cyl(r, rad * 1.35, rad * 1.35, 0.03, p + Vector3(0, h * t, 0), m(c.darkened(0.12)), 16)
	B.sphere(r, rad * 1.2, p + Vector3(0, 0.02, 0), m(c.darkened(0.2)), Vector3(1, 0.6, 1))

static func bed(r: Node3D) -> void :
	var wood: = WOOD
	var dark: = WOOD_DARK
	# estrado e laterais
	B.box(r, Vector3(1.66, 0.22, 2.1), Vector3(0, 0.3, 0), m(wood))
	for sx in [-1.0, 1.0]:
		B.box(r, Vector3(0.06, 0.12, 2.1), Vector3(sx * 0.83, 0.42, 0), m(dark))
	# cabeceira com ripas e topo arredondado
	for sx in [-1.0, 1.0]:
		B.cyl(r, 0.06, 0.06, 1.25, Vector3(sx * 0.84, 0.62, -1.05), m(dark), 18)
		B.sphere(r, 0.085, Vector3(sx * 0.84, 1.28, -1.05), m(dark))
		B.cyl(r, 0.055, 0.055, 0.72, Vector3(sx * 0.84, 0.36, 1.05), m(dark), 18)
		B.sphere(r, 0.075, Vector3(sx * 0.84, 0.75, 1.05), m(dark))
	B.box(r, Vector3(1.62, 0.14, 0.08), Vector3(0, 1.15, -1.05), m(wood))
	B.box(r, Vector3(1.62, 0.1, 0.08), Vector3(0, 0.62, -1.05), m(wood))
	for k in 7:
		B.box(r, Vector3(0.11, 0.48, 0.05), Vector3(-0.66 + k * 0.22, 0.88, -1.05), m(wood.lightened(0.08)))
	var arc: = B.sphere(r, 0.5, Vector3(0, 1.2, -1.05), m(wood), Vector3(1.55, 0.36, 0.08))
	arc.name = "arco"
	# peseira
	B.box(r, Vector3(1.62, 0.32, 0.07), Vector3(0, 0.55, 1.05), m(wood))
	B.box(r, Vector3(1.3, 0.18, 0.02), Vector3(0, 0.55, 1.09), m(wood.lightened(0.12)))
	# colchão gordinho, lençol e colcha de patchwork dobrada
	B.box(r, Vector3(1.56, 0.24, 1.98), Vector3(0, 0.53, 0), m(WHITE, 0.95))
	B.box(r, Vector3(1.6, 0.06, 1.3), Vector3(0, 0.67, 0.36), m(TEAL, 0.95))
	var quilt: = [TEAL, Color(0.2, 0.55, 0.8), CREAM, CORAL]
	for i in 4:
		for j in 3:
			B.box(r, Vector3(0.38, 0.012, 0.4), Vector3(-0.585 + i * 0.39, 0.705, -0.04 + j * 0.41 + 0.04), m(quilt[(i + j) % 4], 0.95))
	B.box(r, Vector3(1.62, 0.09, 0.3), Vector3(0, 0.7, -0.38), m(CREAM, 0.95))
	B.box(r, Vector3(1.64, 0.2, 0.04), Vector3(0, 0.6, 1.0), m(TEAL.darkened(0.15), 0.95))
	# travesseiros fofos
	for sx in [-1.0, 1.0]:
		B.sphere(r, 0.3, Vector3(sx * 0.4, 0.74, -0.75), m(CREAM, 0.95), Vector3(1.0, 0.32, 0.6))
		B.sphere(r, 0.2, Vector3(sx * 0.38, 0.8, -0.6), m(CORAL if sx < 0 else YELLOW, 0.95), Vector3(1.0, 0.45, 0.4))

static func nightstand(r: Node3D) -> void :
	var body: = TEAL
	B.box(r, Vector3(0.46, 0.5, 0.38), Vector3(0, 0.36, 0), m(body))
	B.box(r, Vector3(0.52, 0.04, 0.44), Vector3(0, 0.63, 0), m(WOOD_LIGHT))
	B.box(r, Vector3(0.5, 0.03, 0.42), Vector3(0, 0.12, 0), m(WOOD_LIGHT))
	for k in 2:
		var y: = 0.25 + k * 0.22
		B.box(r, Vector3(0.4, 0.18, 0.02), Vector3(0, y, 0.195), m(body.lightened(0.15)))
		B.box(r, Vector3(0.34, 0.12, 0.012), Vector3(0, y, 0.207), m(body.darkened(0.08)))
		B.sphere(r, 0.025, Vector3(0, y, 0.225), m(YELLOW, 0.3))
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			_turned_leg(r, Vector3(sx * 0.2, 0.0, sz * 0.15), 0.11, 0.022, WOOD_DARK)

## Abajur de mesa (o antigo lampião): base torneada, haste, cúpula plissada e lâmpada acesa.
static func oil_lamp(r: Node3D) -> void :
	var brass: = m(Color(0.85, 0.65, 0.25), 0.35)
	B.cyl(r, 0.09, 0.11, 0.03, Vector3(0, 0.015, 0), brass, 24)
	B.sphere(r, 0.075, Vector3(0, 0.1, 0), m(Color(0.95, 0.5, 0.35), 0.3), Vector3(1, 1.1, 1))
	B.cyl(r, 0.012, 0.012, 0.2, Vector3(0, 0.27, 0), brass, 12)
	B.sphere(r, 0.04, Vector3(0, 0.37, 0), glow(Color(1.0, 0.85, 0.55), 2.5))
	B.cyl(r, 0.075, 0.15, 0.17, Vector3(0, 0.4, 0), m(CREAM, 0.9), 32)
	for k in 16:
		var a: = TAU * k / 16.0
		var pl: = B.box(r, Vector3(0.012, 0.17, 0.012), Vector3(cos(a) * 0.112, 0.4, sin(a) * 0.112), m(CREAM.darkened(0.08), 0.9))
		pl.rotation = Vector3(sin(a) * 0.22, 0, - cos(a) * 0.22)
	B.cyl(r, 0.152, 0.152, 0.015, Vector3(0, 0.32, 0), m(CORAL, 0.8), 32)

static func cabinet(r: Node3D) -> void :
	var body: = TEAL
	B.box(r, Vector3(1.0, 1.7, 0.5), Vector3(0, 0.95, 0), m(body))
	B.box(r, Vector3(1.1, 0.08, 0.58), Vector3(0, 1.84, 0), m(WOOD_LIGHT))
	B.box(r, Vector3(1.04, 0.05, 0.54), Vector3(0, 1.78, 0), m(body.darkened(0.15)))
	B.box(r, Vector3(1.04, 0.1, 0.54), Vector3(0, 0.12, 0), m(body.darkened(0.2)))
	for sx in [-1.0, 1.0]:
		# portas almofadadas
		B.box(r, Vector3(0.46, 1.2, 0.02), Vector3(sx * 0.245, 1.12, 0.255), m(body.lightened(0.12)))
		B.box(r, Vector3(0.36, 0.5, 0.015), Vector3(sx * 0.245, 1.4, 0.268), m(body.darkened(0.06)))
		B.box(r, Vector3(0.36, 0.5, 0.015), Vector3(sx * 0.245, 0.85, 0.268), m(body.darkened(0.06)))
		B.sphere(r, 0.03, Vector3(sx * 0.06, 1.12, 0.285), m(YELLOW, 0.3))
		# gaveta de baixo
		B.box(r, Vector3(0.46, 0.22, 0.02), Vector3(sx * 0.245, 0.33, 0.255), m(body.lightened(0.12)))
		B.box(r, Vector3(0.14, 0.03, 0.03), Vector3(sx * 0.245, 0.33, 0.275), m(YELLOW, 0.3))
		for sz in [-1.0, 1.0]:
			B.sphere(r, 0.05, Vector3(sx * 0.44, 0.04, sz * 0.2), m(WOOD_DARK), Vector3(1, 0.8, 1))

static func ceiling_fan(r: Node3D) -> void :
	B.cyl(r, 0.015, 0.015, 0.3, Vector3(0, 0.15, 0), m(WOOD_DARK), 6)
	B.cyl(r, 0.1, 0.12, 0.1, Vector3(0, 0.0, 0), m(WOOD_DARK), 12)
	for i in 4:
		var bl: = B.box(r, Vector3(0.62, 0.015, 0.13), Vector3(0, -0.02, 0), m(WOOD_LIGHT))
		bl.rotation.y = TAU * i / 4.0
		bl.position = Vector3(cos(TAU * i / 4.0) * 0.36, -0.02, - sin(TAU * i / 4.0) * 0.36)

# ------------------------------------------------------------------ exterior
static func street_lamp(r: Node3D) -> void :
	B.cyl(r, 0.06, 0.09, 3.6, Vector3(0, 1.8, 0), m(Color(0.15, 0.3, 0.32)), 8)
	B.cyl(r, 0.2, 0.08, 0.3, Vector3(0, 3.7, 0), m(Color(0.15, 0.3, 0.32)), 8)
	B.sphere(r, 0.16, Vector3(0, 3.5, 0), glow(Color(1.0, 0.85, 0.5), 2.0))

static func island_tree(r: Node3D) -> void :
	var trunk: = m(Color(0.55, 0.38, 0.24))
	B.cyl(r, 0.18, 0.3, 3.0, Vector3(0, 1.5, 0), trunk, 8)
	var leaves: = [m(LEAF), m(LEAF_DARK), m(Color(0.42, 0.82, 0.32))]
	var offs: = [Vector3(0, 3.6, 0), Vector3(1.0, 3.2, 0.4), Vector3(-0.9, 3.3, -0.5), Vector3(0.2, 3.3, -1.0), Vector3(-0.3, 4.1, 0.6)]
	for i in offs.size():
		B.sphere(r, 1.2 - i * 0.1, offs[i], leaves[i % 3], Vector3(1.2, 0.85, 1.2))
