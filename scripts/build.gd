extends RefCounted
class_name B


static var _mats: = {}
static var _scenes: = {}


static func _hd_path(n: String, suf: String) -> String:
	if Quality.hd:
		var p: = "res://assets/tex_hd/%s_%s.jpg" % [n, suf]
		if ResourceLoader.exists(p):
			return p
	return ""

static func tex(n: String) -> Texture2D:
	var p: = _hd_path(n, "diff")
	return load(p if p != "" else "res://assets/tex/%s_diff.jpg" % n)

static func nor(n: String) -> Texture2D:
	var p: = _hd_path(n, "nor")
	return load(p if p != "" else "res://assets/tex/%s_nor.jpg" % n)

static func rough_tex(n: String) -> Texture2D:
	var p: = _hd_path(n, "rough")
	return load(p) if p != "" else null


static func mat(n: String, scale: = 0.5, tint: = Color.WHITE, rough: = 0.85, triplanar: = true) -> StandardMaterial3D:
	if Toon.enabled():
		return Toon.material(n, scale, tint, rough)
	var key: = "%s|%s|%s|%s|%s" % [n, scale, tint.to_html(), rough, triplanar]
	if _mats.has(key):
		return _mats[key]
	var m: = StandardMaterial3D.new()
	m.albedo_texture = tex(n)
	m.albedo_color = tint
	m.normal_enabled = true
	m.normal_texture = nor(n)
	m.normal_scale = 1.0
	m.roughness = rough
	var rt: = rough_tex(n)
	if rt:
		m.roughness_texture = rt
		m.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_GRAYSCALE
		m.roughness = clampf(rough + 0.1, 0.0, 1.0)
	if triplanar:
		m.uv1_triplanar = true
		m.uv1_world_triplanar = true
		m.uv1_scale = Vector3.ONE * scale
		m.uv1_triplanar_sharpness = 4.0
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_mats[key] = m
	return m

static func flat(c: Color, rough: = 0.8, metal: = 0.0) -> StandardMaterial3D:
	if Toon.enabled():
		return Toon.flat(c, rough, metal)
	var key: = "flat|%s|%s|%s" % [c.to_html(), rough, metal]
	if _mats.has(key):
		return _mats[key]
	var m: = StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	m.metallic = metal
	_mats[key] = m
	return m


static func box(parent: Node, size: Vector3, pos: Vector3, m: Material, collide: = false, rot_y: = 0.0) -> MeshInstance3D:
	var mi: = MeshInstance3D.new()
	var bm: = BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = m
	mi.position = pos
	mi.rotation.y = rot_y
	parent.add_child(mi)
	if collide:
		var sb: = StaticBody3D.new()
		var cs: = CollisionShape3D.new()
		var sh: = BoxShape3D.new()
		sh.size = size
		cs.shape = sh
		sb.add_child(cs)
		mi.add_child(sb)
	return mi

static func cyl(parent: Node, r_top: float, r_bot: float, h: float, pos: Vector3, m: Material, segs: = 12) -> MeshInstance3D:
	var mi: = MeshInstance3D.new()
	var cm: = CylinderMesh.new()
	cm.top_radius = r_top
	cm.bottom_radius = r_bot
	cm.height = h
	cm.radial_segments = segs
	cm.rings = 1
	mi.mesh = cm
	mi.material_override = m
	mi.position = pos
	parent.add_child(mi)
	return mi

static func sphere(parent: Node, r: float, pos: Vector3, m: Material, scale: = Vector3.ONE) -> MeshInstance3D:
	var mi: = MeshInstance3D.new()
	var sm: = SphereMesh.new()
	sm.radius = r
	sm.height = r * 2.0
	sm.radial_segments = 12
	sm.rings = 6
	mi.mesh = sm
	mi.material_override = m
	mi.position = pos
	mi.scale = scale
	parent.add_child(mi)
	return mi


static func wall(parent: Node, size: Vector3, pos: Vector3, rot_y: = 0.0) -> StaticBody3D:
	var sb: = StaticBody3D.new()
	var cs: = CollisionShape3D.new()
	var sh: = BoxShape3D.new()
	sh.size = size
	cs.shape = sh
	sb.add_child(cs)
	sb.position = pos
	sb.rotation.y = rot_y
	parent.add_child(sb)
	return sb


static func platform(parent: Node, size: Vector3, pos: Vector3, m: Material, bevel: = 0.6) -> MeshInstance3D:
	var mi: = box(parent, size, pos, m, false)
	var sb: = StaticBody3D.new()
	var cs: = CollisionShape3D.new()
	var sh: = ConvexPolygonShape3D.new()
	var hx: = size.x * 0.5
	var hz: = size.z * 0.5
	var h: = size.y * 0.5
	var pts: = PackedVector3Array()
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			pts.append(Vector3(sx * hx, h, sz * hz))
			pts.append(Vector3(sx * (hx + bevel), - h, sz * (hz + bevel)))
	sh.points = pts
	cs.shape = sh
	sb.add_child(cs)
	mi.add_child(sb)
	return mi


static func hip_roof(parent: Node, center: Vector3, w: float, d: float, peak: float, m: Material, thickness: = 0.18) -> MeshInstance3D:
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var hx: = w * 0.5
	var hz: = d * 0.5
	var ridge: = maxf(0.0, (w - d) * 0.5)
	var a: = Vector3( - hx, 0, - hz)
	var b_: = Vector3(hx, 0, - hz)
	var c: = Vector3(hx, 0, hz)
	var dd: = Vector3( - hx, 0, hz)
	var r1: = Vector3( - ridge, peak, 0)
	var r2: = Vector3(ridge, peak, 0)
	var faces: = [[a, b_, r2, r1], [b_, c, r2], [c, dd, r1, r2], [dd, a, r1]]
	for f in faces:
		var n: Vector3 = (f[1] - f[0]).cross(f[2] - f[0]).normalized()
		if n.y < 0:
			n = - n
		var tris: = []
		if f.size() == 4:
			tris = [[f[0], f[1], f[2]], [f[0], f[2], f[3]]]
		else:
			tris = [[f[0], f[1], f[2]]]
		var tan_u: Vector3 = (f[1] - f[0]).normalized()
		var tan_v: Vector3 = n.cross(tan_u).normalized()
		for t in tris:
			for v in t:
				st.set_normal(n)
				st.set_uv(Vector2(v.dot(tan_u), - v.dot(tan_v)) * 0.55)
				st.add_vertex(v)

	for f in faces:
		var tris2: = []
		if f.size() == 4:
			tris2 = [[f[0], f[2], f[1]], [f[0], f[3], f[2]]]
		else:
			tris2 = [[f[0], f[2], f[1]]]
		for t in tris2:
			for v in t:
				var vv: Vector3 = v - Vector3(0, thickness, 0)
				st.set_normal(Vector3.DOWN)
				st.set_uv(Vector2(vv.x, vv.z) * 0.55)
				st.add_vertex(vv)

	var ring: = [a, b_, c, dd, a]
	for i in 4:
		var p0: Vector3 = ring[i]
		var p1: Vector3 = ring[i + 1]
		var q0: = p0 - Vector3(0, thickness, 0)
		var q1: = p1 - Vector3(0, thickness, 0)
		var n2: = (p1 - p0).cross(Vector3.DOWN).normalized()
		for v in [p0, q0, p1, p1, q0, q1]:
			st.set_normal(n2)
			st.set_uv(Vector2(v.x + v.z, v.y * 3.0) * 0.55)
			st.add_vertex(v)
	st.generate_tangents()
	var mi: = MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = m
	mi.position = center
	parent.add_child(mi)
	return mi


static func model(parent: Node, n: String, pos: Vector3, rot_y: = 0.0, s: = 1.0) -> Node3D:
	if Toon.enabled() and P.has(n):
		var pr: = P.build(n)
		pr.position = pos
		pr.rotation.y = rot_y
		pr.scale = Vector3.ONE * s
		parent.add_child(pr)
		return pr
	if not _scenes.has(n):

		var hdp: = "res://assets/models_hd/%s/%s.gltf" % [n, n]
		var p: = "res://assets/models/%s/%s.gltf" % [n, n]
		if Quality.hd and ResourceLoader.exists(hdp):
			p = hdp
		_scenes[n] = load(p) if ResourceLoader.exists(p) else null
	var ps: PackedScene = _scenes[n]
	if ps == null:
		var empty: = Node3D.new()
		empty.position = pos
		parent.add_child(empty)
		return empty
	var inst: Node3D = ps.instantiate()
	if Toon.enabled():
		for mi in inst.find_children("*", "MeshInstance3D", true, false):
			for si in mi.mesh.get_surface_count():
				var sm: Material = mi.mesh.surface_get_material(si)
				if sm:
					mi.set_surface_override_material(si, Toon.toonify(sm))
	inst.position = pos
	inst.rotation.y = rot_y
	inst.scale = Vector3.ONE * s
	parent.add_child(inst)
	return inst

static func label(parent: Node, text: String, pos: Vector3, size: = 64, col: = Color.WHITE, outline: = Color(0, 0, 0, 0.7), rot_y: = 0.0) -> Label3D:
	var l: = Label3D.new()
	l.text = text
	l.font_size = size
	l.font = UiTheme.bold()
	l.pixel_size = 0.005
	l.modulate = col
	l.outline_modulate = outline
	l.outline_size = 10
	l.position = pos
	l.rotation.y = rot_y
	l.double_sided = false
	parent.add_child(l)
	return l

static func has_model(n: String) -> bool:
	if Toon.enabled() and P.has(n):
		return true
	return ResourceLoader.exists("res://assets/models/%s/%s.gltf" % [n, n]) or (Quality.hd and ResourceLoader.exists("res://assets/models_hd/%s/%s.gltf" % [n, n]))


static func aabb_of(n: Node3D) -> AABB:
	var out: = AABB()
	var first: = true
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var t: Transform3D = n.global_transform.affine_inverse() * mi.global_transform if n.is_inside_tree() else mi.transform
		var bb: AABB = t * mi.get_aabb()
		out = bb if first else out.merge(bb)
		first = false
	return out
