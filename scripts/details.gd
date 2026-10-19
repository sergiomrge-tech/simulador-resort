extends RefCounted
class_name D
## Detalhes cartoon (v0.7.1): bandeirinhas, franja de palha, tochas, placas, frutas, pranchas, barracas de
## feira, píer, farol, bichinhos da praia... Construtores estáticos em espaço local ou de mundo.

const FLAG_COLS: = [Color(1.0, 0.3, 0.3), Color(1.0, 0.82, 0.2), Color(0.2, 0.7, 1.0), Color(0.35, 0.85, 0.4), Color(1.0, 0.5, 0.8), Color(0.65, 0.4, 0.95), Color(1.0, 0.6, 0.2)]

const ANIMAL_YAW: = -PI * 0.5   # modelos Quaternius olham para +X
const CRAB_YAW: = 0.0

static func m(c: Color, r: = 0.85) -> Material:
	return B.flat(c, r)

static func _vcol_mat() -> Material:
	var key: = "vcol_toon"
	if B._mats.has(key):
		return B._mats[key]
	var mt: = StandardMaterial3D.new()
	mt.vertex_color_use_as_albedo = true
	mt.vertex_color_is_srgb = true
	mt.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
	mt.specular_mode = BaseMaterial3D.SPECULAR_TOON
	mt.cull_mode = BaseMaterial3D.CULL_DISABLED
	mt.roughness = 0.9
	B._mats[key] = mt
	return mt

## Muitas cópias da mesma malha numa só chamada de desenho.
static func multimesh(parent: Node, mesh: Mesh, xforms: Array, cols: Array = [], mat: Material = null) -> MultiMeshInstance3D:
	var mm: = MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = not cols.is_empty()
	mm.mesh = mesh
	mm.instance_count = xforms.size()
	for i in xforms.size():
		mm.set_instance_transform(i, xforms[i])
		if mm.use_colors:
			mm.set_instance_color(i, cols[i % cols.size()])
	var mi: = MultiMeshInstance3D.new()
	mi.multimesh = mm
	if mat:
		mi.material_override = mat
	elif mm.use_colors:
		mi.material_override = _vcol_mat()
	parent.add_child(mi)
	return mi

static func _bmesh(size: Vector3) -> BoxMesh:
	var b: = BoxMesh.new()
	b.size = size
	return b

# ------------------------------------------------------------------ festas e decoração
## Cordão de bandeirinhas de festa entre a e b, com barriga.
static func bunting(parent: Node, a: Vector3, b: Vector3, sag: = 0.5, spacing: = 0.45) -> void :
	var L: = a.distance_to(b)
	var n: = maxi(2, int(L / spacing))
	var flag: = PrismMesh.new()
	flag.size = Vector3(0.3, 0.36, 0.01)
	flag.left_to_right = 0.5
	var xfs: = []
	var cols: = []
	var dir: = (b - a).normalized()
	var yaw: = atan2(dir.x, dir.z) + PI * 0.5
	for i in n:
		var t: = (float(i) + 0.5) / n
		var p: = a.lerp(b, t) - Vector3(0, sag * 4.0 * t * (1.0 - t), 0)
		var bs: = Basis(Vector3.UP, yaw) * Basis(Vector3.RIGHT, PI)
		xfs.append(Transform3D(bs, p - Vector3(0, 0.18, 0)))
		cols.append(FLAG_COLS[i % FLAG_COLS.size()])
	multimesh(parent, flag, xfs, cols)
	# o barbante
	var segs: = 10
	var xs: = []
	for k in segs:
		var t0: = float(k) / segs
		var t1: = float(k + 1) / segs
		var p0: = a.lerp(b, t0) - Vector3(0, sag * 4.0 * t0 * (1.0 - t0), 0)
		var p1: = a.lerp(b, t1) - Vector3(0, sag * 4.0 * t1 * (1.0 - t1), 0)
		var mid: = (p0 + p1) * 0.5
		var d: = p1 - p0
		var bas: = Basis.looking_at(d.normalized(), Vector3.UP) if d.length() > 0.001 else Basis()
		xs.append(Transform3D(bas.scaled(Vector3(1, 1, d.length())), mid))
	multimesh(parent, _bmesh(Vector3(0.015, 0.015, 1.0)), xs, [], m(Color(0.95, 0.95, 0.9)))

## Franja de palha pendurada na borda de um telhado quadrado (half = meia largura do beiral).
static func thatch_fringe(parent: Node, c: Vector3, half: float, y: float, col: Color, length: = 0.55, half_z: = -1.0) -> void :
	var xfs: = []
	var cols: = []
	var rng: = RandomNumberGenerator.new()
	rng.seed = int(c.x * 13.0 + c.z * 7.0)
	var step: = 0.09
	var hz: = half if half_z < 0.0 else half_z
	for side in 4:
		var lim: = half if side < 2 else hz
		var k: = -lim
		while k < lim:
			var p: Vector3
			match side:
				0: p = Vector3(k, 0, hz)
				1: p = Vector3(k, 0, -hz)
				2: p = Vector3(half, 0, k)
				_: p = Vector3(-half, 0, k)
			var l: = length * rng.randf_range(0.45, 1.3)
			var bs: = Basis(Vector3.UP, 0.0 if side < 2 else PI * 0.5).scaled(Vector3(1, l, 1))
			xfs.append(Transform3D(bs, c + p + Vector3(0, y - l * 0.5, 0)))
			cols.append(col.darkened(rng.randf_range(0.0, 0.18)))
			k += step
	var mi: = multimesh(parent, _bmesh(Vector3(0.045, 1.0, 0.02)), xfs, cols)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

## Tocha tiki de bambu. Devolve a luz (o mundo liga à noite).
static func tiki_torch(parent: Node, p: Vector3) -> OmniLight3D:
	# haste de bambu com nós, cordas e copo de barro: modelo do Blender (tools/gen_code_props.py)
	if Real.place(parent, "g:tiki_torch", p, -1.0, 0.0, Color.WHITE, 0.0, false) == null:
		B.cyl(parent, 0.045, 0.06, 1.7, p + Vector3(0, 0.85, 0), m(Color(0.86, 0.7, 0.4)), 8)
		B.cyl(parent, 0.11, 0.07, 0.22, p + Vector3(0, 1.78, 0), m(Color(0.5, 0.35, 0.2)), 10)
	var flame: Node3D = Real.place_glow(parent, "g:flame", p + Vector3(0, 1.84, 0), -0.8, 0.0, P.glow(Color(1.0, 0.55, 0.15), 4.0))
	if flame == null:
		flame = B.sphere(parent, 0.11, p + Vector3(0, 1.98, 0), P.glow(Color(1.0, 0.55, 0.15), 4.0), Vector3(0.8, 1.6, 0.8))
	flame.name = "TikiFlame"
	var l: = OmniLight3D.new()
	l.position = p + Vector3(0, 2.0, 0)
	l.omni_range = 5.0
	l.light_color = Color(1.0, 0.6, 0.3)
	l.light_energy = 0.0
	parent.add_child(l)
	return l

## Poste com placas-seta: arrows = [[texto, ângulo, cor], ...]
static func signpost(parent: Node, p: Vector3, arrows: Array) -> void :
	if Real.place(parent, "g:signpost_post", p, -1.0, 0.0, Color.WHITE, 0.0, false) == null:
		B.cyl(parent, 0.06, 0.07, 2.6, p + Vector3(0, 1.3, 0), m(Color(0.6, 0.42, 0.25)), 8)
	var y: = 2.3
	for a in arrows:
		var piv: = Node3D.new()
		piv.position = p + Vector3(0, y, 0)
		piv.rotation.y = float(a[1])
		parent.add_child(piv)
		var col: Color = a[2]
		if Real.place(piv, "g:sign_arrow", Vector3(0, -0.15, 0), -1.0, 0.0, col.lerp(Color.WHITE, 0.3), 0.0, false) == null:
			B.box(piv, Vector3(1.3, 0.3, 0.05), Vector3(0.7, 0, 0), m(col))
			var tip: = B.cyl(piv, 0.0, 0.21, 0.05, Vector3(1.42, 0, 0), m(col), 3)
			tip.rotation = Vector3(PI * 0.5, 0, PI * 0.5)
		for side in [1.0, -1.0]:
			var l: = B.label(piv, str(a[0]), Vector3(0.68, 0, side * 0.034), 44, Color.WHITE, col.darkened(0.5))
			l.rotation.y = 0.0 if side > 0 else PI
		y -= 0.42

static func surfboard(parent: Node, p: Vector3, rot: float, col: Color, lean: = 0.25) -> void :
	# prancha modelada no Blender (tools/gen_surfboard.py): perfil real, rocker e três quilhas
	var piv: = Node3D.new()
	piv.position = p
	piv.rotation = Vector3(lean, rot, 0)
	parent.add_child(piv)
	var h: = Real.place(piv, "g:surfboard", Vector3(0, 1.0, 0), 0.0, 0.0, col.lerp(Color.WHITE, 0.2), 2.0)
	if h:
		h.rotation.x = -PI * 0.5

static func towel(parent: Node, p: Vector3, rot: float, a: Color, b: Color) -> void :
	# toalha de pano ondulado com listras (modelo gerado no Blender: tools/gen_beach_props.py), cor = mistura das duas cores
	var h: = Real.place(parent, "g:towel", p, 0.0, rot, a.lerp(b, 0.25), 1.9)
	if h == null:
		B.box(parent, Vector3(0.9, 0.012, 1.9), p + Vector3(0, 0.01, 0), m(a), false, rot)

static func coconut_pile(parent: Node, p: Vector3, n: = 9) -> void :
	# cocos reais (Kenney CC0) empilhados em pirâmide
	var rng: = RandomNumberGenerator.new()
	rng.seed = int(p.x * 31.0 + p.z)
	var layer: = 0
	var placed: = 0
	while placed < n:
		var cnt: = maxi(1, 5 - layer * 2)
		for k in cnt:
			if placed >= n:
				break
			var a: = TAU * k / cnt + layer
			var r: = 0.0 if cnt == 1 else 0.3 - layer * 0.1
			var tint: = Color(1.0, 1.0, 1.0) if rng.randf() < 0.75 else Color(0.85, 0.7, 0.55)
			Real.place(parent, "k:coconut", p + Vector3(cos(a) * r, layer * 0.2, sin(a) * r), 0.24, rng.randf() * TAU, tint)
			placed += 1
		layer += 1

static func bananas(parent: Node, p: Vector3) -> void :
	# cesto de vime pendurado na viga por uma corda grossa, com bananas reais dentro
	B.cyl(parent, 0.014, 0.014, 0.5, p + Vector3(0, 0.25, 0), m(Color(0.55, 0.4, 0.25)), 8)
	Real.place(parent, "wicker_basket_01", p + Vector3(0, -0.2, 0), 0.2, 0.0, Color.WHITE, 0.42)
	Real.place(parent, "bananas", p + Vector3(0, -0.12, 0), 0.12, 0.6)

static func pineapple(parent: Node, p: Vector3) -> void :
	Real.place(parent, "k:pineapple", p, 0.32)

static func cup_stack(parent: Node, p: Vector3, col: Color) -> void :
	for k in 3:
		Real.place(parent, "k:cup", p + Vector3(0.0, k * 0.012, 0.0), 0.12, k * 0.7, col.lerp(Color.WHITE, 0.5))

static func blender(parent: Node, p: Vector3) -> void :
	Real.place(parent, "k:frappe", p + Vector3(-0.07, 0, 0), 0.24)
	Real.place(parent, "k:frappe", p + Vector3(0.09, 0, 0.03), 0.22, 1.0, Color(1.0, 0.8, 0.8))

static func tip_jar(parent: Node, p: Vector3) -> void :
	Real.place(parent, "k:glass", p, 0.2, 0.0, Color(1.0, 0.95, 0.7))
	var l: = B.label(parent, "GORJETA", p + Vector3(0, 0.1, 0.07), 18, Color(0.2, 0.15, 0.1), Color(1, 1, 1, 0.9))
	l.pixel_size = 0.0025

static func straw_cup(parent: Node, p: Vector3) -> void :
	Real.place(parent, "k:cocktail", p, 0.24)

static func radio(parent: Node, p: Vector3, rot: float) -> void :
	Real.place(parent, "boombox", p, 0.0, rot, Color.WHITE, 0.36)

static func trash_bin(parent: Node, p: Vector3, col: = Color(0.25, 0.65, 0.35)) -> void :
	Real.place(parent, "wicker_basket_02", p, 0.6, 0.0, col.lerp(Color.WHITE, 0.6))

static func open_sign(parent: Node, p: Vector3, rot: float) -> Label3D:
	var piv: = Node3D.new()
	piv.position = p
	piv.rotation.y = rot
	parent.add_child(piv)
	if Real.place(piv, "g:open_sign", Vector3(0, -0.21, 0), -1.0, 0.0, Color.WHITE, 0.0, false) == null:
		for sx in [-1.0, 1.0]:
			B.box(piv, Vector3(0.01, 0.25, 0.01), Vector3(sx * 0.25, 0.15, 0), m(Color(0.3, 0.25, 0.2)))
		B.box(piv, Vector3(0.7, 0.26, 0.04), Vector3(0, -0.08, 0), m(Color(0.98, 0.95, 0.85)))
	var l: = B.label(piv, "ABERTO", Vector3(0, -0.08, 0.034), 40, Color(0.15, 0.6, 0.25), Color(1, 1, 1, 0.9))
	l.pixel_size = 0.004
	return l

# ------------------------------------------------------------------ praia
static func sand_castle(parent: Node, p: Vector3) -> void :
	# castelo de areia modelado no Blender (tools/gen_beach_props.py) + balde e pá reais
	var h: = Real.place(parent, "g:sandcastle", p, 1.1, 0.4)
	if h == null:
		return
	var fl: = Real.place(parent, "g:beach_flag", p + Vector3(0.0, 1.0, 0.0), 0.35, 0.0)
	if fl:
		Real.tint_named(fl, Color(1.0, 0.35, 0.3))
	Real.place(parent, "wooden_bucket_02", p + Vector3(0.85, 0.0, 0.25), 0.2, 0.5, Color(1.0, 0.85, 0.25))
	# pazinha de plástico fincada na areia, inclinada (tools/gen_food.py)
	var sh: = Real.place(parent, "g:beach_spade", p + Vector3(0.7, -0.06, -0.45), 0.38, 0.6)
	if sh:
		Real.tint_named(sh, Color(0.3, 0.7, 1.0))
		sh.rotation.z = 0.35

static func starfish(parent: Node, p: Vector3, col: = Color(1.0, 0.5, 0.35)) -> void :
	if Real.place(parent, "g:starfish", p, -1.0, p.x * 3.0, col, 0.0, true) == null:
		Real.place(parent, "lambis_shell", p, 0.13, p.x * 3.0, col.lerp(Color.WHITE, 0.6))

static func crab(parent: Node, p: Vector3, range_m: = 1.6) -> Node3D:
	var c: = Node3D.new()
	c.position = p
	c.rotation.y = randf() * TAU
	parent.add_child(c)
	# caranguejo real (OpenGameArt, CC0), de lado como os caranguejos andam
	var h: = Real.place(c, "g:crab", Vector3.ZERO, 0.0, 0.0, Color(0.9, 0.62, 0.55), 0.34)
	if h:
		h.rotation.y = CRAB_YAW
	if parent.is_inside_tree():
		_crab_walk(c, range_m)
	else:
		c.ready.connect(func(): _crab_walk(c, range_m), CONNECT_ONE_SHOT)
	return c

static func _crab_walk(c: Node3D, range_m: float) -> void :
	var side: = c.transform.basis.x
	var a: = c.position
	var t: = c.create_tween().set_loops()
	t.tween_property(c, "position", a + side * range_m, 2.2 + randf()).set_trans(Tween.TRANS_SINE)
	t.tween_interval(randf_range(0.5, 2.5))
	t.tween_property(c, "position", a, 2.2 + randf()).set_trans(Tween.TRANS_SINE)
	t.tween_interval(randf_range(0.5, 2.5))

static func volley_net(parent: Node, c: Vector3, rot: float) -> void :
	var piv: = Node3D.new()
	piv.position = c
	piv.rotation.y = rot
	parent.add_child(piv)
	if Real.place(piv, "g:volley_net", Vector3.ZERO, -1.0, 0.0, Color.WHITE, 0.0, false) == null:
		for sx in [-1.0, 1.0]:
			B.cyl(piv, 0.05, 0.05, 2.5, Vector3(sx * 4.0, 1.25, 0), m(Color(0.95, 0.95, 0.95)), 8)
		B.box(piv, Vector3(8.0, 0.08, 0.02), Vector3(0, 2.4, 0), m(Color(0.95, 0.95, 0.95)))
		var net: = B.box(piv, Vector3(8.0, 0.8, 0.01), Vector3(0, 1.98, 0), m(Color(0.15, 0.15, 0.18, 0.55)))
		net.name = "Net"
	if Real.place(piv, "g:volleyball", Vector3(1.2, 0.0, 2.0), 0.22, 0.0) == null:
		B.sphere(piv, 0.11, Vector3(1.2, 0.11, 2.0), m(Color(1.0, 0.9, 0.3), 0.5))
	# linhas da quadra na areia
	for sz in [-4.0, 4.0]:
		B.box(piv, Vector3(8.0, 0.01, 0.06), Vector3(0, 0.012, sz), m(Color(0.25, 0.55, 0.95)))
	for sx in [-4.0, 4.0]:
		B.box(piv, Vector3(0.06, 0.01, 8.0), Vector3(sx, 0.012, 0), m(Color(0.25, 0.55, 0.95)))

## Guarda-sol de praia com duas cangas e um isopor.
static func beach_spot(parent: Node, p: Vector3, seed_: int) -> void :
	var rng: = RandomNumberGenerator.new()
	rng.seed = seed_
	var c1: Color = FLAG_COLS[rng.randi() % FLAG_COLS.size()]
	var c2: Color = FLAG_COLS[rng.randi() % FLAG_COLS.size()]
	B.cyl(parent, 0.03, 0.03, 2.2, p + Vector3(0, 1.1, 0), m(Color(0.95, 0.95, 0.95)), 6)
	var top: = B.cyl(parent, 0.04, 1.3, 0.45, p + Vector3(0, 2.2, 0), m(c1, 0.8), 10)
	top.rotation.z = 0.15
	B.cyl(parent, 0.05, 1.32, 0.02, p + Vector3(0, 1.98, 0), m(c2, 0.8), 10).rotation.z = 0.15
	var r: = rng.randf() * TAU
	towel(parent, p + Vector3(cos(r) * 1.2, 0, sin(r) * 1.2), r, c2, Color.WHITE)
	towel(parent, p + Vector3(cos(r + 1.2) * 1.3, 0, sin(r + 1.2) * 1.3), r + 1.2, c1, Color(1.0, 0.95, 0.6))
	var cp: = p + Vector3(cos(r + 2.8) * 0.8, 0, sin(r + 2.8) * 0.8)
	Real.place(parent, "plastic_crate_02", cp, 0.32, r, Color(0.8, 0.9, 1.0))

# ------------------------------------------------------------------ vila
## Poste de luz de madeira com cruzeta (os fios são ligados com wire()).
static func power_pole(parent: Node, p: Vector3) -> Vector3:
	if Real.place(parent, "g:power_pole", p, -1.0, 0.0, Color.WHITE, 0.0, false) == null:
		B.cyl(parent, 0.1, 0.13, 7.0, p + Vector3(0, 3.5, 0), m(Color(0.5, 0.36, 0.24)), 8)
		B.box(parent, Vector3(1.4, 0.1, 0.1), p + Vector3(0, 6.6, 0), m(Color(0.45, 0.32, 0.22)))
		for sx in [-0.6, 0.0, 0.6]:
			B.cyl(parent, 0.03, 0.04, 0.12, p + Vector3(sx, 6.72, 0), m(Color(0.9, 0.95, 1.0), 0.3), 6)
	return p + Vector3(0, 6.82, 0)

static func wire(parent: Node, a: Vector3, b: Vector3, sag: = 0.6) -> void :
	var segs: = 8
	var xs: = []
	for k in segs:
		var t0: = float(k) / segs
		var t1: = float(k + 1) / segs
		var p0: = a.lerp(b, t0) - Vector3(0, sag * 4.0 * t0 * (1.0 - t0), 0)
		var p1: = a.lerp(b, t1) - Vector3(0, sag * 4.0 * t1 * (1.0 - t1), 0)
		var d: = p1 - p0
		var bas: = Basis.looking_at(d.normalized(), Vector3.UP)
		xs.append(Transform3D(bas.scaled(Vector3(1, 1, d.length())), (p0 + p1) * 0.5))
	var mi: = multimesh(parent, _bmesh(Vector3(0.025, 0.025, 1.0)), xs, [], m(Color(0.12, 0.12, 0.14)))
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

## Barraca de feira com toldo listrado e mercadorias coloridas.
static func stall(parent: Node, p: Vector3, rot: float, awning: Color, goods: Array) -> void :
	var piv: = Node3D.new()
	piv.position = p
	piv.rotation.y = rot
	parent.add_child(piv)
	var wood: = B.mat("weathered_planks", 0.6, Color(1.0, 0.85, 0.65), 0.85)
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.cyl(piv, 0.045, 0.05, 2.3, Vector3(sx * 1.2, 1.15, sz * 0.7), wood, 16)
	B.box(piv, Vector3(2.5, 0.08, 1.5), Vector3(0, 0.85, 0), wood)
	B.box(piv, Vector3(2.5, 0.75, 0.05), Vector3(0, 0.45, 0.72), m(Color(0.95, 0.9, 0.78)))
	for i in 6:
		var stripe: = B.box(piv, Vector3(0.44, 0.04, 1.8), Vector3(-1.1 + i * 0.44, 2.35, 0.1), m(awning if i % 2 == 0 else Color.WHITE), false)
		stripe.rotation.x = 0.25
	for i in 6:
		B.box(piv, Vector3(0.44, 0.22, 0.02), Vector3(-1.1 + i * 0.44, 2.2, 0.99), m(awning if i % 2 == 0 else Color.WHITE))
	var rng: = RandomNumberGenerator.new()
	rng.seed = int(p.x * 7.0 + p.z * 3.0)
	# frutas reais (Poly Haven / Kenney, CC0) em cestas e soltas no balcão; cada barraca vende 3 tipos
	var kinds: = ["k:orange", "food_apple_01", "food_lime_01", "lemon", "food_pomegranate_01", "food_lychee_01", "food_avocado_01", "food_pears_asian_01", "food_kiwi_01"]
	var base_k: = int(absf(p.x) * 0.37) % kinds.size()
	var hs: = {"k:orange": 0.1, "food_apple_01": 0.1, "food_lime_01": 0.08, "lemon": 0.09, "food_pomegranate_01": 0.1, "food_lychee_01": 0.06, "food_avocado_01": 0.11, "food_pears_asian_01": 0.11, "food_kiwi_01": 0.06}
	for bi in 3:
		var key: String = kinds[(base_k + bi * 2) % kinds.size()]
		var bx: = -0.85 + bi * 0.85
		Real.place(piv, "wicker_basket_02", Vector3(bx, 0.89, -0.2), 0.16, rng.randf() * TAU, Color.WHITE, 0.55)
		for f in 6:
			var ang: = rng.randf() * TAU
			var rr: = rng.randf() * 0.16
			Real.place(piv, key, Vector3(bx + cos(ang) * rr, 1.0 + (f % 2) * 0.05, -0.2 + sin(ang) * rr), float(hs[key]), rng.randf() * TAU)
	Real.place(piv, "wooden_crate_02", Vector3(0.9, 0.89, -0.4), 0.0, 0.2, Color.WHITE, 0.4)

static func mailbox(parent: Node, p: Vector3, rot: float) -> void :
	if Real.place(parent, "g:mailbox", p, -1.0, rot, Color.WHITE, 0.0, false) == null:
		B.cyl(parent, 0.04, 0.04, 1.0, p + Vector3(0, 0.5, 0), m(Color(0.4, 0.3, 0.2)), 6)
		B.box(parent, Vector3(0.3, 0.25, 0.42), p + Vector3(0, 1.1, 0), m(Color(1.0, 0.85, 0.2)), false, rot)

static func cat(parent: Node, p: Vector3, rot: float, col: Color) -> void :
	# gato real (Quaternius Animal Pack Vol.2, CC0, suavizado no Blender)
	var piv: = Node3D.new()
	piv.position = p
	piv.rotation.y = rot
	parent.add_child(piv)
	var h: = Real.place(piv, "g:cat", Vector3.ZERO, 0.42, ANIMAL_YAW, Color.WHITE.lerp(col, 0.35))
	if h == null:
		B.sphere(piv, 0.13, Vector3(0, 0.13, 0), m(col), Vector3(1.0, 0.85, 1.4))

static func dog(parent: Node, p: Vector3, rot: float, col: Color) -> void :
	# cachorro real (Quaternius Animal Pack Vol.2, CC0, suavizado no Blender)
	var piv: = Node3D.new()
	piv.position = p
	piv.rotation.y = rot
	parent.add_child(piv)
	var h: = Real.place(piv, "g:dog", Vector3.ZERO, 0.62, ANIMAL_YAW, Color.WHITE.lerp(col, 0.5))
	if h == null:
		B.sphere(piv, 0.18, Vector3(0, 0.32, 0), m(col), Vector3(1.0, 0.9, 1.6))

# ------------------------------------------------------------------ marcos
## Píer de madeira mar adentro (from = ponta na areia, para -Z).
static func pier(parent: Node, from: Vector3, length: float, width: = 2.4) -> void :
	var wood: = B.mat("weathered_planks", 0.6, Color(0.9, 0.7, 0.5), 0.85)
	var post: = m(Color(0.45, 0.32, 0.22))
	var c: = from + Vector3(0, 0, - length * 0.5)
	var end: = from + Vector3(0, 0.62, - length + 1.0)
	# píer de tábuas individuais, estacas com corda e plataforma final: módulos do Blender (tools/gen_code_props.py)
	var segs: = int(floor((length - 3.0) / 3.0))
	var ok: = false
	for i in segs:
		var sg: = Real.place(parent, "g:pier_segment", from + Vector3(0, -2.8, - i * 3.0), -1.0, 0.0, Color.WHITE, 0.0, false)
		if sg == null:
			break
		sg.rotation.y = PI    # +Y do Blender (mar) vira -Z no glTF; o módulo já aponta para o mar
		sg.rotation.y = 0.0
		sg.scale.x = width / 2.4
		ok = true
	if ok:
		end = from + Vector3(0, 0.62, - float(segs) * 3.0 - 1.5)
		var ep: = Real.place(parent, "g:pier_end", end + Vector3(0, -3.42, 0), -1.0, 0.0, Color.WHITE, 0.0, false)
		if ep:
			ep.scale.x = (width + 2.0) / 4.4
	else:
		B.box(parent, Vector3(width, 0.14, length), c + Vector3(0, 0.55, 0), wood, true)
		var k: = 0.0
		while k <= length:
			for sx in [-1.0, 1.0]:
				B.cyl(parent, 0.12, 0.13, 3.4, from + Vector3(sx * (width * 0.5 - 0.05), -1.1, - k), post, 8)
				B.cyl(parent, 0.05, 0.05, 1.0, from + Vector3(sx * (width * 0.5 - 0.05), 1.1, - k), post, 6)
			k += 3.0
		for sx in [-1.0, 1.0]:
			B.box(parent, Vector3(0.06, 0.06, length), c + Vector3(sx * (width * 0.5 - 0.05), 1.5, 0), post)
		B.box(parent, Vector3(width + 2.0, 0.14, 3.0), end + Vector3(0, -0.07, 0), wood, true)
	B.model(parent, "lifebuoy", end + Vector3(1.4, 0.0, 0.9), 0.4, 1.0)   # deitada no deck (antes ficava em pé solta no ar)
	B.model(parent, "wooden_bucket_01", end + Vector3(-1.4, 0.0, 0.6), 0.0, 0.8)
	var rod: = B.cyl(parent, 0.01, 0.015, 2.2, end + Vector3(-1.2, 0.9, -0.8), m(Color(0.3, 0.2, 0.15)), 4)
	rod.rotation.x = -0.9

## Farol listrado com a luz que gira à noite. Devolve o nó da lanterna (o mundo gira e acende).
static func lighthouse(parent: Node, p: Vector3) -> Node3D:
	# base de pedras reais (Poly Haven, CC0) em volta e sob o farol
	var rks: = ["coast_land_rocks_02", "coast_rocks_03", "coast_rocks_05", "coast_land_rocks_03", "coast_rocks_02", "coast_rocks_03"]
	for k in 6:
		var a: = TAU * k / 6.0
		Real.place(parent, rks[k], p + Vector3(cos(a) * 3.0, -0.4, sin(a) * 3.0), 2.6 - (k % 2) * 0.5, a * 1.7, Color(0.95, 0.93, 1.0))
	Real.place(parent, "coast_rocks_05", p + Vector3(0, -0.7, 0), 2.6, 0.5, Color(0.95, 0.93, 1.0), 6.8)
	var h: = 14.0
	var bands: = 7
	# torre, soco, galeria, lanterna e cúpula: modelo do Blender (tools/gen_code_props.py). Sem ele, cai no construtor antigo.
	var tower: = Real.place(parent, "g:lighthouse", p + Vector3(0, 1.0, 0), -1.0, 0.0, Color.WHITE, 0.0, false)
	for i in (0 if tower else bands):
		var t0: = float(i) / bands
		var r0: = lerpf(1.6, 1.05, t0)
		var r1: = lerpf(1.6, 1.05, float(i + 1) / bands)
		B.cyl(parent, r1, r0, h / bands, p + Vector3(0, 1.0 + (float(i) + 0.5) * h / bands, 0), B.mat("white_plaster", 0.5, Color(1.0, 0.45, 0.4) if i % 2 == 0 else Color(1.0, 0.99, 0.96), 0.8), 32)
	var top: = p + Vector3(0, 1.0 + h, 0)
	if tower == null:
		B.cyl(parent, 1.5, 1.5, 0.2, top + Vector3(0, 0.1, 0), m(Color(0.2, 0.22, 0.25)), 18)
		B.cyl(parent, 0.1, 1.05, 0.9, top + Vector3(0, 1.95, 0), m(Color(0.95, 0.25, 0.22)), 14)
	B.cyl(parent, 0.82, 0.82, 1.3, top + Vector3(0, 0.85, 0), m(Color(0.85, 0.95, 1.0, 0.5), 0.1), 24)
	var lamp: = Node3D.new()
	lamp.name = "LighthouseLamp"
	lamp.position = top + Vector3(0, 0.85, 0)
	parent.add_child(lamp)
	if Real.place_glow(lamp, "g:fresnel_lens", Vector3(0, -0.4, 0), -1.0, 0.0, P.glow(Color(1.0, 0.95, 0.7), 3.0), true) == null:
		B.sphere(lamp, 0.4, Vector3.ZERO, P.glow(Color(1.0, 0.95, 0.7), 3.0))
	# v0.9.5: facho longo (42 m) com shader aditivo que esmaece nas bordas e na ponta (antes: cone liso de 18 m)
	var beam: = B.cyl(lamp, 4.2, 0.3, 42.0, Vector3(0, 0, 21.0), null, 32)   # boca larga longe da lente
	var bm: = ShaderMaterial.new()
	bm.shader = load("res://shaders/light_beam.gdshader")
	beam.material_override = bm
	beam.rotation.x = PI * 0.5
	beam.name = "Beam"
	beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var l: = SpotLight3D.new()
	l.spot_range = 60.0
	l.spot_angle = 12.0
	l.light_color = Color(1.0, 0.95, 0.75)
	l.light_energy = 0.0
	l.rotation.y = PI
	lamp.add_child(l)
	return lamp
