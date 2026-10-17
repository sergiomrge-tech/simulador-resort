extends RefCounted
class_name Palm
## Coqueiro procedural: tronco curvo com anéis + folhas (textura com alpha) + cocos.

static var _variants := []
static var _frond_mat: StandardMaterial3D
static var _bark_mat: StandardMaterial3D
static var _coco_mat: StandardMaterial3D

static func _mats() -> void:
	if _frond_mat:
		return
	_frond_mat = StandardMaterial3D.new()
	_frond_mat.albedo_texture = load("res://assets/tex/palm_frond.png")
	_frond_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	_frond_mat.alpha_scissor_threshold = 0.4
	_frond_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_frond_mat.roughness = 0.75
	_frond_mat.albedo_color = Color(1.0, 1.0, 0.95)
	_frond_mat.backlight_enabled = true
	_frond_mat.backlight = Color(0.25, 0.35, 0.1)
	_bark_mat = StandardMaterial3D.new()
	_bark_mat.albedo_texture = B.tex("palm_tree_bark")
	_bark_mat.normal_enabled = true
	_bark_mat.normal_texture = B.nor("palm_tree_bark")
	_bark_mat.roughness = 0.9
	_coco_mat = StandardMaterial3D.new()
	_coco_mat.albedo_color = Color(0.42, 0.5, 0.18)
	_coco_mat.roughness = 0.6

static func _build(seed_: int) -> ArrayMesh:
	_mats()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_
	var H := rng.randf_range(7.0, 9.5)
	var lean := rng.randf_range(0.8, 2.2)
	var am := ArrayMesh.new()
	# ---- tronco
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rings := 16
	var segs := 9
	var pts := []
	for i in rings + 1:
		var t := float(i) / rings
		var c := Vector3(lean * t * t, H * t, 0)
		var r := lerpf(0.26, 0.15, t) + 0.08 * maxf(0.0, 1.0 - t * 6.0)
		r *= 1.0 + 0.05 * sin(t * 60.0)   # anéis
		pts.append([c, r, t])
	for i in rings:
		for s in segs:
			var quad := []
			for k in [[i, s], [i + 1, s], [i + 1, s + 1], [i, s + 1]]:
				var p = pts[k[0]]
				var a := TAU * float(k[1]) / segs
				var dir := Vector3(cos(a), 0, sin(a))
				quad.append([p[0] + dir * p[1], dir, Vector2(float(k[1]) / segs, -p[2] * H * 0.6)])
			for idx in [0, 2, 1, 0, 3, 2]:
				st.set_normal(quad[idx][1])
				st.set_uv(quad[idx][2])
				st.add_vertex(quad[idx][0])
	st.generate_tangents()
	st.set_material(_bark_mat)
	st.commit(am)
	var crown := Vector3(lean, H, 0)
	# ---- folhas
	var sf := SurfaceTool.new()
	sf.begin(Mesh.PRIMITIVE_TRIANGLES)
	var nf := rng.randi_range(11, 14)
	for f in nf:
		var yaw := TAU * float(f) / nf + rng.randf_range(-0.2, 0.2)
		var L := rng.randf_range(3.0, 4.0)
		var up0 := rng.randf_range(0.2, 0.9)
		var droop := rng.randf_range(1.6, 2.6)
		var dirh := Vector3(cos(yaw), 0, sin(yaw))
		var side := Vector3(-sin(yaw), 0, cos(yaw))
		var n := 10
		var prev := []
		for j in n + 1:
			var s := float(j) / n
			var center := crown + dirh * (s * L) + Vector3.UP * (up0 * sin(s * PI * 0.8) * 1.4 - s * s * droop)
			var w := 0.75 * sin(PI * minf(1.0, s * 1.05 + 0.04)) + 0.05
			var vdrop := Vector3.DOWN * 0.18 * w
			var l := center - side * w + vdrop
			var r := center + side * w + vdrop
			if j > 0:
				var nn: Vector3 = (center - prev[2]).cross(side).normalized()
				if nn.y < 0:
					nn = -nn
				var uv0 := Vector2(float(j - 1) / n, 0.0)
				var uv1 := Vector2(s, 0.0)
				var verts := [[prev[0], Vector2(uv0.x, 0.02)], [l, Vector2(uv1.x, 0.02)], [r, Vector2(uv1.x, 0.98)],
					[prev[0], Vector2(uv0.x, 0.02)], [r, Vector2(uv1.x, 0.98)], [prev[1], Vector2(uv0.x, 0.98)]]
				for v in verts:
					sf.set_normal(nn)
					sf.set_uv(v[1])
					sf.add_vertex(v[0])
			prev = [l, r, center]
	sf.set_material(_frond_mat)
	sf.commit(am)
	# ---- cocos
	var sc := SurfaceTool.new()
	var sm := SphereMesh.new()
	sm.radius = 0.13
	sm.height = 0.3
	sm.radial_segments = 8
	sm.rings = 4
	for k in rng.randi_range(3, 6):
		var a2 := rng.randf() * TAU
		var off := crown + Vector3(cos(a2) * 0.22, -0.25 - rng.randf() * 0.15, sin(a2) * 0.22)
		sc.append_from(sm, 0, Transform3D(Basis(), off))
	sc.set_material(_coco_mat)
	sc.commit(am)
	return am

static func variant(i: int) -> ArrayMesh:
	while _variants.size() < 4:
		_variants.append(_build(1000 + _variants.size() * 77))
	return _variants[i % _variants.size()]

static func spawn(parent: Node, pos: Vector3, seed_: int, collide := true) -> Node3D:
	var root := Node3D.new()
	root.position = pos
	root.rotation.y = float(seed_ * 37 % 360) * PI / 180.0
	var s := 0.85 + float(seed_ * 13 % 30) / 100.0
	root.scale = Vector3(s, s, s)
	var mi := MeshInstance3D.new()
	mi.mesh = variant(seed_)
	root.add_child(mi)
	parent.add_child(root)
	if collide:
		var sb := StaticBody3D.new()
		var cs := CollisionShape3D.new()
		var sh := CylinderShape3D.new()
		sh.radius = 0.3
		sh.height = 3.0
		cs.shape = sh
		cs.position.y = 1.5
		sb.add_child(cs)
		root.add_child(sb)
	return root
