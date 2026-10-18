extends RefCounted
class_name Palm


static var _variants: = []
static var _frond_mat: ShaderMaterial
static var _bark_mat: StandardMaterial3D
static var _coco_mat: StandardMaterial3D
static var _leaflet_tex: Texture2D

static func _mats() -> void :
	if _frond_mat:
		return
	_frond_mat = ShaderMaterial.new()
	_frond_mat.shader = load("res://shaders/palm_wind.gdshader")
	_frond_mat.set_shader_parameter("tex", _leaflet_texture())
	_bark_mat = B.mat("palm_tree_bark", 1.4, Color.WHITE, 0.9)
	_coco_mat = B.flat(Color(0.5, 0.7, 0.2), 0.6)

static func _build(seed_: int) -> ArrayMesh:
	_mats()
	var rng: = RandomNumberGenerator.new()
	rng.seed = seed_
	var H: = rng.randf_range(7.0, 9.5)
	var lean: = rng.randf_range(0.8, 2.2)
	var am: = ArrayMesh.new()

	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rings: = 16
	var segs: = 9
	var pts: = []
	for i in rings + 1:
		var t: = float(i) / rings
		var c: = Vector3(lean * t * t, H * t, 0)
		var r: = lerpf(0.26, 0.15, t) + 0.08 * maxf(0.0, 1.0 - t * 6.0)
		r *= 1.0 + 0.05 * sin(t * 60.0)
		pts.append([c, r, t])
	for i in rings:
		for s in segs:
			var quad: = []
			for k in [[i, s], [i + 1, s], [i + 1, s + 1], [i, s + 1]]:
				var p = pts[k[0]]
				var a: = TAU * float(k[1]) / segs
				var dir: = Vector3(cos(a), 0, sin(a))
				quad.append([p[0] + dir * p[1], dir, Vector2(float(k[1]) / segs, - p[2] * H * 0.6)])
			for idx in [0, 2, 1, 0, 3, 2]:
				st.set_normal(quad[idx][1])
				st.set_uv(quad[idx][2])
				st.add_vertex(quad[idx][0])
	st.generate_tangents()
	st.set_material(_bark_mat)
	st.commit(am)
	var crown: = Vector3(lean, H, 0)

	var sf: = SurfaceTool.new()
	sf.begin(Mesh.PRIMITIVE_TRIANGLES)
	var nf: = rng.randi_range(10, 13)
	for f in nf:
		var yaw: = TAU * float(f) / nf + rng.randf_range(-0.18, 0.18)
		var L: = rng.randf_range(3.1, 4.3)
		var up0: = rng.randf_range(0.35, 1.0)
		var droop: = rng.randf_range(1.7, 2.7)
		var dirh: = Vector3(cos(yaw), 0, sin(yaw))
		var side: = Vector3( - sin(yaw), 0, cos(yaw))
		var nseg: = 8
		for j in nseg:
			var s0: = float(j) / float(nseg)
			var s1: = float(j + 1) / float(nseg)
			var c0: = _frond_center(crown, dirh, s0, L, up0, droop)
			var c1: = _frond_center(crown, dirh, s1, L, up0, droop)
			var rib: = 0.028 + 0.02 * (1.0 - s0)
			_frond_quad(sf, c0 - side * rib, c0 + side * rib, c1 + side * rib, c1 - side * rib, 0.42, 0.58, s0, s1)
			var reach: = lerpf(0.72, 0.16, s0) * rng.randf_range(0.88, 1.08)
			var hang: = lerpf(0.02, 0.42, s0)
			for sgn_i in 2:
				var sgn: = -1.0 if sgn_i == 0 else 1.0
				var spread: float = sgn * rng.randf_range(0.85, 1.15)
				var outward: Vector3 = (side * spread + dirh * 0.22).normalized()
				var lift: = Vector3.UP * lerpf(0.12, -0.05, s0)
				var base_l: = c0
				var base_r: = c0.lerp(c1, 0.55)
				var tip_l: Vector3 = c0 + outward * reach + lift + Vector3.DOWN * hang
				var tip_r: Vector3 = base_r + outward * reach * 0.78 + lift * 0.65 + Vector3.DOWN * hang * 1.15
				var mid_l: = base_l.lerp(tip_l, 0.48) + Vector3.DOWN * (0.03 + hang * 0.15)
				var mid_r: = base_r.lerp(tip_r, 0.48) + Vector3.DOWN * (0.04 + hang * 0.2)
				_frond_quad(sf, base_l, base_r, mid_r, mid_l, 0.08, 0.92, 0.0, 0.48)
				_frond_quad(sf, mid_l, mid_r, tip_r, tip_l, 0.14, 0.86, 0.48, 1.0)
	sf.set_material(_frond_mat)
	sf.commit(am)

	var sc: = SurfaceTool.new()
	var sm: = SphereMesh.new()
	sm.radius = 0.13
	sm.height = 0.3
	sm.radial_segments = 8
	sm.rings = 4
	for k in rng.randi_range(3, 6):
		var a2: = rng.randf() * TAU
		var off: = crown + Vector3(cos(a2) * 0.22, -0.25 - rng.randf() * 0.15, sin(a2) * 0.22)
		sc.append_from(sm, 0, Transform3D(Basis(), off))
	sc.set_material(_coco_mat)
	sc.commit(am)
	return am

static func _frond_center(crown: Vector3, dirh: Vector3, s: float, L: float, up0: float, droop: float) -> Vector3:
	return crown + dirh * (s * L) + Vector3.UP * (up0 * sin(s * PI * 0.75) * 1.35 - s * s * droop)

static func _frond_quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, u0: float, u1: float, v0: float, v1: float) -> void :
	var n: Vector3 = (b - a).cross(d - a)
	if n.length_squared() < 1e-06:
		n = Vector3.UP
	else:
		n = n.normalized()
	if n.y < 0.0:
		n = - n
	var verts: = [[a, Vector2(u0, v0)], [b, Vector2(u1, v0)], [c, Vector2(u1, v1)], [a, Vector2(u0, v0)], [c, Vector2(u1, v1)], [d, Vector2(u0, v1)]]
	for v in verts:
		st.set_normal(n)
		st.set_uv(v[1])
		st.add_vertex(v[0])


static func _leaflet_texture() -> Texture2D:
	if _leaflet_tex:
		return _leaflet_tex
	var w: = 128
	var h: = 512
	var img: = Image.create(w, h, false, Image.FORMAT_RGBA8)
	var cx: = float(w - 1) * 0.5
	for y in h:
		var t: = float(y) / float(h - 1)
		var profile: = pow(sin(t * PI), 0.62)
		var half: = (0.05 + 0.48 * profile) * cx
		var serr: = 0.1 * sin(t * 52.0)
		for x in w:
			var dx: = float(x) - cx
			var limit: = maxf(half * (1.0 - serr * 0.35), 1.0)
			var edge: = absf(dx) / limit
			if edge > 1.0:
				continue
			var alpha: = 1.0 if edge < 0.78 else clampf((1.0 - edge) / 0.22, 0.0, 1.0)
			var vein: = exp( - dx * dx / (half * half * 0.05 + 0.8))
			var g: = lerpf(0.22, 0.58, clampf(t * 1.15, 0.0, 1.0))
			g *= lerpf(0.72, 1.0, 1.0 - edge)
			var r: = g * 0.38 + vein * 0.06
			var bcol: = g * 0.2
			if absf(dx) < 1.5:
				r = 0.42
				g = 0.38
				bcol = 0.14
				alpha = 1.0
			img.set_pixel(x, y, Color(r, g, bcol, alpha))
	_leaflet_tex = ImageTexture.create_from_image(img)
	return _leaflet_tex

static func variant(i: int) -> ArrayMesh:
	while _variants.size() < 4:
		_variants.append(_build(1000 + _variants.size() * 77))
	return _variants[i % _variants.size()]

static func spawn(parent: Node, pos: Vector3, seed_: int, collide: = true) -> Node3D:
	var root: = Node3D.new()
	root.position = pos
	root.rotation.y = float(seed_ * 37 % 360) * PI / 180.0
	var s: = 0.85 + float(seed_ * 13 % 30) / 100.0
	root.scale = Vector3(s, s, s)
	var mi: = MeshInstance3D.new()
	mi.mesh = variant(seed_)
	var tones: = [Color(0.82, 1.0, 0.7), Color(1.0, 0.96, 0.78), Color(0.7, 0.92, 0.58), Color(0.95, 1.0, 0.62)]
	mi.set_instance_shader_parameter("tint", tones[absi(seed_) % tones.size()])
	mi.visibility_range_end = 120.0 if collide else 78.0
	mi.visibility_range_end_margin = 14.0
	mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
	mi.extra_cull_margin = 1.8
	root.add_child(mi)
	parent.add_child(root)
	if collide:
		var sb: = StaticBody3D.new()
		var cs: = CollisionShape3D.new()
		var sh: = CylinderShape3D.new()
		sh.radius = 0.3
		sh.height = 3.0
		cs.shape = sh
		cs.position.y = 1.5
		sb.add_child(cs)
		root.add_child(sb)
	return root
