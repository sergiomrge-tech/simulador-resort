extends RefCounted
class_name D
## Detalhes cartoon (v0.7.1): bandeirinhas, franja de palha, tochas, placas, frutas, pranchas, barracas de
## feira, píer, farol, bichinhos da praia... Construtores estáticos em espaço local ou de mundo.

const FLAG_COLS: = [Color(1.0, 0.3, 0.3), Color(1.0, 0.82, 0.2), Color(0.2, 0.7, 1.0), Color(0.35, 0.85, 0.4), Color(1.0, 0.5, 0.8), Color(0.65, 0.4, 0.95), Color(1.0, 0.6, 0.2)]

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
static func thatch_fringe(parent: Node, c: Vector3, half: float, y: float, col: Color, length: = 0.55) -> void :
	var xfs: = []
	var cols: = []
	var rng: = RandomNumberGenerator.new()
	rng.seed = int(c.x * 13.0 + c.z * 7.0)
	var step: = 0.12
	for side in 4:
		var k: = -half
		while k < half:
			var p: Vector3
			match side:
				0: p = Vector3(k, 0, half)
				1: p = Vector3(k, 0, -half)
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
	B.cyl(parent, 0.045, 0.06, 1.7, p + Vector3(0, 0.85, 0), m(Color(0.86, 0.7, 0.4)), 8)
	for y in [0.4, 0.9, 1.4]:
		B.cyl(parent, 0.065, 0.065, 0.04, p + Vector3(0, y, 0), m(Color(0.6, 0.45, 0.25)), 8)
	B.cyl(parent, 0.11, 0.07, 0.22, p + Vector3(0, 1.78, 0), m(Color(0.5, 0.35, 0.2)), 10)
	var flame: = B.sphere(parent, 0.11, p + Vector3(0, 1.98, 0), P.glow(Color(1.0, 0.55, 0.15), 4.0), Vector3(0.8, 1.6, 0.8))
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
	B.cyl(parent, 0.06, 0.07, 2.6, p + Vector3(0, 1.3, 0), m(Color(0.6, 0.42, 0.25)), 8)
	var y: = 2.3
	for a in arrows:
		var piv: = Node3D.new()
		piv.position = p + Vector3(0, y, 0)
		piv.rotation.y = float(a[1])
		parent.add_child(piv)
		var col: Color = a[2]
		B.box(piv, Vector3(1.3, 0.3, 0.05), Vector3(0.7, 0, 0), m(col))
		var tip: = B.cyl(piv, 0.0, 0.21, 0.05, Vector3(1.42, 0, 0), m(col), 3)
		tip.rotation = Vector3(PI * 0.5, 0, PI * 0.5)
		for side in [1.0, -1.0]:
			var l: = B.label(piv, str(a[0]), Vector3(0.68, 0, side * 0.03), 44, Color.WHITE, col.darkened(0.5))
			l.rotation.y = 0.0 if side > 0 else PI
		y -= 0.42

static func surfboard(parent: Node, p: Vector3, rot: float, col: Color, lean: = 0.25) -> void :
	var piv: = Node3D.new()
	piv.position = p
	piv.rotation = Vector3(lean, rot, 0)
	parent.add_child(piv)
	B.sphere(piv, 0.3, Vector3(0, 1.0, 0), m(col, 0.4), Vector3(0.95, 3.4, 0.14))
	B.sphere(piv, 0.3, Vector3(0, 1.0, 0.012), m(Color.WHITE, 0.4), Vector3(0.2, 3.3, 0.14))

static func towel(parent: Node, p: Vector3, rot: float, a: Color, b: Color) -> void :
	for i in 5:
		B.box(parent, Vector3(0.9, 0.012, 0.34), p + Vector3(0, 0.01, 0).rotated(Vector3.UP, rot) + Vector3(-0.68 + i * 0.34, 0, 0).rotated(Vector3.UP, rot + PI * 0.5), m(a if i % 2 == 0 else b), false, rot)

static func coconut_pile(parent: Node, p: Vector3, n: = 9) -> void :
	var rng: = RandomNumberGenerator.new()
	rng.seed = int(p.x * 31.0 + p.z)
	var green: = m(Color(0.42, 0.68, 0.2), 0.6)
	var brown: = m(Color(0.55, 0.36, 0.2), 0.7)
	var layer: = 0
	var placed: = 0
	while placed < n:
		var cnt: = maxi(1, 5 - layer * 2)
		for k in cnt:
			if placed >= n:
				break
			var a: = TAU * k / cnt + layer
			var r: = 0.0 if cnt == 1 else 0.3 - layer * 0.1
			B.sphere(parent, 0.15, p + Vector3(cos(a) * r, 0.13 + layer * 0.22, sin(a) * r), green if rng.randf() < 0.75 else brown, Vector3(1, 1.1, 1))
			placed += 1
		layer += 1

static func bananas(parent: Node, p: Vector3) -> void :
	B.cyl(parent, 0.012, 0.012, 0.5, p + Vector3(0, 0.25, 0), m(Color(0.5, 0.35, 0.2)), 4)
	for k in 7:
		var a: = TAU * k / 7.0
		var b: = B.cyl(parent, 0.03, 0.022, 0.2, p + Vector3(cos(a) * 0.07, -0.05 - (k % 3) * 0.05, sin(a) * 0.07), m(Color(1.0, 0.86, 0.25), 0.5), 6)
		b.rotation = Vector3(cos(a) * 0.5, 0, - sin(a) * 0.5)

static func pineapple(parent: Node, p: Vector3) -> void :
	B.sphere(parent, 0.09, p + Vector3(0, 0.11, 0), m(Color(0.95, 0.65, 0.2), 0.6), Vector3(1, 1.4, 1))
	for k in 6:
		var lf: = B.box(parent, Vector3(0.025, 0.16, 0.01), p + Vector3(0, 0.3, 0), m(Color(0.25, 0.65, 0.25)))
		lf.rotation = Vector3(0.4, TAU * k / 6.0, 0)

static func cup_stack(parent: Node, p: Vector3, col: Color) -> void :
	for k in 5:
		B.cyl(parent, 0.045, 0.035, 0.1, p + Vector3(0, 0.05 + k * 0.025, 0), m(col, 0.4), 10)

static func blender(parent: Node, p: Vector3) -> void :
	B.box(parent, Vector3(0.16, 0.12, 0.16), p + Vector3(0, 0.06, 0), m(Color(0.95, 0.35, 0.3)))
	B.cyl(parent, 0.07, 0.055, 0.22, p + Vector3(0, 0.23, 0), m(Color(0.85, 0.95, 1.0, 0.7), 0.1), 10)
	B.cyl(parent, 0.06, 0.05, 0.12, p + Vector3(0, 0.18, 0), m(Color(1.0, 0.65, 0.3), 0.4), 10)
	B.cyl(parent, 0.075, 0.075, 0.03, p + Vector3(0, 0.355, 0), m(Color(0.2, 0.2, 0.22)), 10)

static func tip_jar(parent: Node, p: Vector3) -> void :
	B.cyl(parent, 0.06, 0.06, 0.16, p + Vector3(0, 0.08, 0), m(Color(0.8, 0.95, 1.0, 0.6), 0.1), 12)
	for k in 3:
		B.cyl(parent, 0.025, 0.025, 0.006, p + Vector3(-0.02 + k * 0.02, 0.02 + k * 0.012, 0), m(Color(1.0, 0.8, 0.2), 0.3), 10)
	var l: = B.label(parent, "GORJETA", p + Vector3(0, 0.08, 0.062), 18, Color(0.2, 0.15, 0.1), Color(1, 1, 1, 0.9))
	l.pixel_size = 0.0025

static func straw_cup(parent: Node, p: Vector3) -> void :
	B.cyl(parent, 0.04, 0.035, 0.12, p + Vector3(0, 0.06, 0), m(Color(0.3, 0.75, 0.9), 0.5), 10)
	var cols: = [Color(1, 0.3, 0.4), Color(1, 0.85, 0.2), Color(0.3, 0.9, 0.5), Color(1, 1, 1)]
	for k in 6:
		var s: = B.cyl(parent, 0.006, 0.006, 0.24, p + Vector3(cos(k) * 0.02, 0.18, sin(k) * 0.02), m(cols[k % 4], 0.4), 4)
		s.rotation = Vector3(cos(k) * 0.15, 0, sin(k) * 0.15)

static func radio(parent: Node, p: Vector3, rot: float) -> void :
	var r: = B.box(parent, Vector3(0.34, 0.2, 0.12), p + Vector3(0, 0.1, 0), m(Color(0.2, 0.7, 0.7)), false, rot)
	for sx in [-1.0, 1.0]:
		var sp: = B.cyl(r, 0.055, 0.055, 0.02, Vector3(sx * 0.09, 0, 0.06), m(Color(0.15, 0.15, 0.18)), 12)
		sp.rotation.x = PI * 0.5
	var ant: = B.cyl(r, 0.005, 0.005, 0.3, Vector3(0.12, 0.22, 0), m(Color(0.7, 0.7, 0.75)), 4)
	ant.rotation.z = -0.4
	B.box(r, Vector3(0.2, 0.025, 0.02), Vector3(0, 0.12, 0), m(Color(0.15, 0.15, 0.18)))

static func trash_bin(parent: Node, p: Vector3, col: = Color(0.25, 0.65, 0.35)) -> void :
	B.cyl(parent, 0.26, 0.22, 0.8, p + Vector3(0, 0.4, 0), m(col), 12)
	B.cyl(parent, 0.28, 0.28, 0.06, p + Vector3(0, 0.82, 0), m(col.darkened(0.2)), 12)

## Placa "ABERTO / FECHADO" pendurada. Devolve o Label3D para o mundo atualizar.
static func open_sign(parent: Node, p: Vector3, rot: float) -> Label3D:
	var piv: = Node3D.new()
	piv.position = p
	piv.rotation.y = rot
	parent.add_child(piv)
	for sx in [-1.0, 1.0]:
		B.box(piv, Vector3(0.01, 0.25, 0.01), Vector3(sx * 0.25, 0.15, 0), m(Color(0.3, 0.25, 0.2)))
	B.box(piv, Vector3(0.7, 0.26, 0.04), Vector3(0, -0.08, 0), m(Color(0.98, 0.95, 0.85)))
	var l: = B.label(piv, "ABERTO", Vector3(0, -0.08, 0.025), 40, Color(0.15, 0.6, 0.25), Color(1, 1, 1, 0.9))
	l.pixel_size = 0.004
	return l

# ------------------------------------------------------------------ praia
static func sand_castle(parent: Node, p: Vector3) -> void :
	var sand: = m(Color(0.95, 0.8, 0.52))
	B.cyl(parent, 0.45, 0.55, 0.3, p + Vector3(0, 0.15, 0), sand, 12)
	for k in 4:
		var a: = TAU * k / 4.0 + 0.4
		B.cyl(parent, 0.13, 0.15, 0.45, p + Vector3(cos(a) * 0.36, 0.42, sin(a) * 0.36), sand, 8)
		B.cyl(parent, 0.0, 0.14, 0.15, p + Vector3(cos(a) * 0.36, 0.72, sin(a) * 0.36), sand, 8)
	B.cyl(parent, 0.18, 0.2, 0.55, p + Vector3(0, 0.55, 0), sand, 8)
	B.cyl(parent, 0.008, 0.008, 0.3, p + Vector3(0, 0.95, 0), m(Color(0.4, 0.3, 0.2)), 4)
	B.box(parent, Vector3(0.14, 0.09, 0.01), p + Vector3(0.07, 1.05, 0), m(Color(1.0, 0.3, 0.3)))
	var bucket: = B.cyl(parent, 0.1, 0.08, 0.14, p + Vector3(0.75, 0.07, 0.2), m(Color(1.0, 0.85, 0.2), 0.4), 10)
	bucket.rotation.z = 1.2
	var shovel: = B.box(parent, Vector3(0.04, 0.4, 0.02), p + Vector3(0.6, 0.03, -0.4), m(Color(0.2, 0.6, 1.0), 0.4))
	shovel.rotation = Vector3(PI * 0.5, 0.6, 0)

static func starfish(parent: Node, p: Vector3, col: = Color(1.0, 0.5, 0.35)) -> void :
	for k in 5:
		var arm: = B.box(parent, Vector3(0.05, 0.02, 0.14), p + Vector3(0, 0.012, 0), m(col, 0.7))
		arm.rotation.y = TAU * k / 5.0
		arm.position += Vector3(sin(TAU * k / 5.0), 0, cos(TAU * k / 5.0)) * 0.06

## Caranguejo que anda de lado, para lá e para cá.
static func crab(parent: Node, p: Vector3, range_m: = 1.6) -> Node3D:
	var c: = Node3D.new()
	c.position = p
	c.rotation.y = randf() * TAU
	parent.add_child(c)
	var red: = m(Color(1.0, 0.35, 0.25), 0.6)
	B.sphere(c, 0.09, Vector3(0, 0.06, 0), red, Vector3(1.3, 0.55, 1.0))
	for sx in [-1.0, 1.0]:
		B.sphere(c, 0.04, Vector3(sx * 0.13, 0.07, 0.07), red, Vector3(1.2, 0.8, 1.0))
		B.sphere(c, 0.018, Vector3(sx * 0.035, 0.12, 0.06), m(Color.WHITE, 0.4))
		B.sphere(c, 0.009, Vector3(sx * 0.035, 0.125, 0.075), m(Color(0.05, 0.05, 0.05), 0.3))
		for k in 3:
			var leg: = B.box(c, Vector3(0.08, 0.012, 0.012), Vector3(sx * 0.1, 0.03, -0.03 + k * 0.03), red)
			leg.rotation.z = sx * 0.4
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
	for sx in [-1.0, 1.0]:
		B.cyl(piv, 0.05, 0.05, 2.5, Vector3(sx * 4.0, 1.25, 0), m(Color(0.95, 0.95, 0.95)), 8)
	B.box(piv, Vector3(8.0, 0.08, 0.02), Vector3(0, 2.4, 0), m(Color(0.95, 0.95, 0.95)))
	var net: = B.box(piv, Vector3(8.0, 0.8, 0.01), Vector3(0, 1.98, 0), m(Color(0.15, 0.15, 0.18, 0.55)))
	net.name = "Net"
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
	B.box(parent, Vector3(0.45, 0.32, 0.3), p + Vector3(cos(r + 2.8) * 0.8, 0.16, sin(r + 2.8) * 0.8), m(Color(0.95, 0.95, 0.98)), false, r)
	B.box(parent, Vector3(0.47, 0.06, 0.32), p + Vector3(cos(r + 2.8) * 0.8, 0.34, sin(r + 2.8) * 0.8), m(Color(0.2, 0.55, 0.95)), false, r)

# ------------------------------------------------------------------ vila
## Poste de luz de madeira com cruzeta (os fios são ligados com wire()).
static func power_pole(parent: Node, p: Vector3) -> Vector3:
	B.cyl(parent, 0.1, 0.13, 7.0, p + Vector3(0, 3.5, 0), m(Color(0.5, 0.36, 0.24)), 8)
	B.box(parent, Vector3(1.4, 0.1, 0.1), p + Vector3(0, 6.6, 0), m(Color(0.45, 0.32, 0.22)))
	for sx in [-0.6, 0.0, 0.6]:
		B.cyl(parent, 0.03, 0.04, 0.12, p + Vector3(sx, 6.72, 0), m(Color(0.9, 0.95, 1.0), 0.3), 6)
	return p + Vector3(0, 6.75, 0)

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
	var wood: = m(Color(0.75, 0.52, 0.3))
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			B.cyl(piv, 0.04, 0.04, 2.3, Vector3(sx * 1.2, 1.15, sz * 0.7), wood, 6)
	B.box(piv, Vector3(2.5, 0.08, 1.5), Vector3(0, 0.85, 0), wood)
	B.box(piv, Vector3(2.5, 0.75, 0.05), Vector3(0, 0.45, 0.72), m(Color(0.95, 0.9, 0.78)))
	for i in 6:
		var stripe: = B.box(piv, Vector3(0.44, 0.04, 1.8), Vector3(-1.1 + i * 0.44, 2.35, 0.1), m(awning if i % 2 == 0 else Color.WHITE), false)
		stripe.rotation.x = 0.25
	for i in 6:
		B.box(piv, Vector3(0.44, 0.22, 0.02), Vector3(-1.1 + i * 0.44, 2.2, 0.99), m(awning if i % 2 == 0 else Color.WHITE))
	var rng: = RandomNumberGenerator.new()
	rng.seed = int(p.x * 7.0 + p.z * 3.0)
	for k in 10:
		var g: Color = goods[k % goods.size()]
		B.sphere(piv, rng.randf_range(0.07, 0.11), Vector3(-1.0 + (k % 5) * 0.5, 0.97, -0.25 + (k / 5) * 0.4), m(g, 0.6))
	B.box(piv, Vector3(0.3, 0.2, 0.3), Vector3(0.9, 0.99, -0.4), m(Color(0.9, 0.7, 0.4)))

static func mailbox(parent: Node, p: Vector3, rot: float) -> void :
	B.cyl(parent, 0.04, 0.04, 1.0, p + Vector3(0, 0.5, 0), m(Color(0.4, 0.3, 0.2)), 6)
	B.box(parent, Vector3(0.3, 0.25, 0.42), p + Vector3(0, 1.1, 0), m(Color(1.0, 0.85, 0.2)), false, rot)

static func cat(parent: Node, p: Vector3, rot: float, col: Color) -> void :
	var piv: = Node3D.new()
	piv.position = p
	piv.rotation.y = rot
	parent.add_child(piv)
	B.sphere(piv, 0.13, Vector3(0, 0.13, 0), m(col), Vector3(1.0, 0.85, 1.4))
	B.sphere(piv, 0.09, Vector3(0, 0.24, 0.16), m(col))
	for sx in [-1.0, 1.0]:
		var ear: = B.cyl(piv, 0.0, 0.035, 0.07, Vector3(sx * 0.05, 0.33, 0.16), m(col), 4)
		ear.rotation.z = - sx * 0.2
		B.sphere(piv, 0.018, Vector3(sx * 0.035, 0.26, 0.24), m(Color(0.3, 0.8, 0.3), 0.3))
	var tail: = B.cyl(piv, 0.02, 0.025, 0.3, Vector3(0, 0.22, -0.2), m(col), 6)
	tail.rotation.x = -0.6

static func dog(parent: Node, p: Vector3, rot: float, col: Color) -> void :
	var piv: = Node3D.new()
	piv.position = p
	piv.rotation.y = rot
	parent.add_child(piv)
	B.sphere(piv, 0.18, Vector3(0, 0.32, 0), m(col), Vector3(1.0, 0.9, 1.6))
	B.sphere(piv, 0.13, Vector3(0, 0.5, 0.28), m(col))
	B.sphere(piv, 0.05, Vector3(0, 0.47, 0.41), m(col.darkened(0.2)), Vector3(1, 0.8, 1.2))
	B.sphere(piv, 0.02, Vector3(0, 0.49, 0.46), m(Color(0.05, 0.05, 0.05)))
	for sx in [-1.0, 1.0]:
		B.sphere(piv, 0.05, Vector3(sx * 0.1, 0.52, 0.25), m(col.darkened(0.3)), Vector3(0.6, 1.4, 0.6))
		for sz in [-1.0, 1.0]:
			B.cyl(piv, 0.035, 0.035, 0.26, Vector3(sx * 0.09, 0.13, sz * 0.15), m(col), 6)
	var tail: = B.cyl(piv, 0.02, 0.03, 0.22, Vector3(0, 0.45, -0.3), m(col), 6)
	tail.rotation.x = -0.9

# ------------------------------------------------------------------ marcos
## Píer de madeira mar adentro (from = ponta na areia, para -Z).
static func pier(parent: Node, from: Vector3, length: float, width: = 2.4) -> void :
	var wood: = B.mat("weathered_planks", 0.6, Color(0.9, 0.7, 0.5), 0.85)
	var post: = m(Color(0.45, 0.32, 0.22))
	var c: = from + Vector3(0, 0, - length * 0.5)
	B.box(parent, Vector3(width, 0.14, length), c + Vector3(0, 0.55, 0), wood, true)
	var k: = 0.0
	while k <= length:
		for sx in [-1.0, 1.0]:
			B.cyl(parent, 0.12, 0.13, 3.4, from + Vector3(sx * (width * 0.5 - 0.05), -1.1, - k), post, 8)
			B.cyl(parent, 0.05, 0.05, 1.0, from + Vector3(sx * (width * 0.5 - 0.05), 1.1, - k), post, 6)
		k += 3.0
	for sx in [-1.0, 1.0]:
		B.box(parent, Vector3(0.06, 0.06, length), c + Vector3(sx * (width * 0.5 - 0.05), 1.5, 0), post)
	var end: = from + Vector3(0, 0.62, - length + 1.0)
	B.box(parent, Vector3(width + 2.0, 0.14, 3.0), end + Vector3(0, -0.07, 0), wood, true)
	B.model(parent, "lifebuoy", end + Vector3(1.6, 0.9, 0), 0.0, 1.0).rotation.x = PI * 0.5
	B.model(parent, "wooden_bucket_01", end + Vector3(-1.4, 0.0, 0.6), 0.0, 0.8)
	var rod: = B.cyl(parent, 0.01, 0.015, 2.2, end + Vector3(-1.2, 0.9, -0.8), m(Color(0.3, 0.2, 0.15)), 4)
	rod.rotation.x = -0.9

## Farol listrado com a luz que gira à noite. Devolve o nó da lanterna (o mundo gira e acende).
static func lighthouse(parent: Node, p: Vector3) -> Node3D:
	var rock: = m(Color(0.58, 0.55, 0.62))
	for k in 6:
		var a: = TAU * k / 6.0
		B.sphere(parent, 2.4 - (k % 2) * 0.6, p + Vector3(cos(a) * 3.0, 0.2, sin(a) * 3.0), rock, Vector3(1.2, 0.6, 1.0))
	B.sphere(parent, 3.4, p + Vector3(0, -0.6, 0), rock, Vector3(1.0, 0.5, 1.0))
	var h: = 14.0
	var bands: = 7
	for i in bands:
		var t0: = float(i) / bands
		var r0: = lerpf(1.6, 1.05, t0)
		var r1: = lerpf(1.6, 1.05, float(i + 1) / bands)
		B.cyl(parent, r1, r0, h / bands, p + Vector3(0, 1.0 + (float(i) + 0.5) * h / bands, 0), m(Color(0.95, 0.25, 0.22) if i % 2 == 0 else Color(0.98, 0.97, 0.94)), 18)
	var top: = p + Vector3(0, 1.0 + h, 0)
	B.cyl(parent, 1.5, 1.5, 0.2, top + Vector3(0, 0.1, 0), m(Color(0.2, 0.22, 0.25)), 18)
	B.cyl(parent, 0.85, 0.85, 1.3, top + Vector3(0, 0.85, 0), m(Color(0.85, 0.95, 1.0, 0.5), 0.1), 14)
	B.cyl(parent, 0.1, 1.05, 0.9, top + Vector3(0, 1.95, 0), m(Color(0.95, 0.25, 0.22)), 14)
	var lamp: = Node3D.new()
	lamp.name = "LighthouseLamp"
	lamp.position = top + Vector3(0, 0.85, 0)
	parent.add_child(lamp)
	B.sphere(lamp, 0.4, Vector3.ZERO, P.glow(Color(1.0, 0.95, 0.7), 3.0))
	var beam: = B.cyl(lamp, 0.25, 2.2, 18.0, Vector3(0, 0, 9.0), P.glow(Color(1.0, 0.95, 0.7, 0.18), 1.5), 12)
	beam.rotation.x = PI * 0.5
	(beam.material_override as StandardMaterial3D).transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
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
