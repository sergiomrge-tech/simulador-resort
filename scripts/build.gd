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


static var _rboxes: = {}

## Caixa com cantos arredondados (v0.7.1 — regra do projeto: nada de visual low poly).
## Faces planas, bordas suaves com normais contínuas. Cacheada por tamanho.
static func rounded_box(size: Vector3) -> Mesh:
	var key: = Vector3i(roundi(size.x * 200.0), roundi(size.y * 200.0), roundi(size.z * 200.0))
	if _rboxes.has(key):
		return _rboxes[key]
	var h: = size * 0.5
	var r: = clampf(minf(size.x, minf(size.y, size.z)) * 0.2, 0.006, 0.045)
	var axis_coords: = func(hh: float) -> PackedFloat32Array:
		return PackedFloat32Array([-hh, -hh + r * 0.3, -hh + r, hh - r, hh - r * 0.3, hh])
	var cx: PackedFloat32Array = axis_coords.call(h.x)
	var cy: PackedFloat32Array = axis_coords.call(h.y)
	var cz: PackedFloat32Array = axis_coords.call(h.z)
	var inner: = h - Vector3.ONE * r
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var faces: = [
		[Vector3(1, 0, 0), 1, 2], [Vector3(-1, 0, 0), 2, 1], [Vector3(0, 1, 0), 2, 0],
		[Vector3(0, -1, 0), 0, 2], [Vector3(0, 0, 1), 0, 1], [Vector3(0, 0, -1), 1, 0],
	]
	var coords: = [cx, cy, cz]
	for f in faces:
		var n: Vector3 = f[0]
		var ua: int = f[1]
		var va: int = f[2]
		var ca: PackedFloat32Array = coords[ua]
		var cb: PackedFloat32Array = coords[va]
		var grid: = []
		for j in cb.size():
			var row: = []
			for i in ca.size():
				var v: = Vector3.ZERO
				v[ua] = ca[i]
				v[va] = cb[j]
				var na: int = 3 - ua - va
				v[na] = h[na] * signf(n[na])
				var inn: = v.clamp(- inner, inner)
				var d: = v - inn
				var nd: = d.normalized() if d.length() > 0.00001 else n
				row.append([inn + nd * r, nd])
			grid.append(row)
		for j in cb.size() - 1:
			for i in ca.size() - 1:
				var q: = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
				var e1: Vector3 = q[1][0] - q[0][0]
				var e2: Vector3 = q[3][0] - q[0][0]
				var flip: = e1.cross(e2).dot(n) < 0.0
				var order: = [0, 1, 2, 0, 2, 3] if not flip else [0, 2, 1, 0, 3, 2]
				for k in order:
					st.set_normal(q[k][1])
					st.set_uv(Vector2(q[k][0][ua], q[k][0][va]))
					st.add_vertex(q[k][0])
	var mesh: = st.commit()
	_rboxes[key] = mesh
	return mesh

static func box(parent: Node, size: Vector3, pos: Vector3, m: Material, collide: = false, rot_y: = 0.0) -> MeshInstance3D:
	var mi: = MeshInstance3D.new()
	if Toon.enabled() and minf(size.x, minf(size.y, size.z)) >= 0.03:
		mi.mesh = rounded_box(size)
	else:
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
	# nada de low poly: cilindros redondos (só formas de 3-5 lados, como setas, ficam como estão)
	cm.radial_segments = segs if segs <= 5 else maxi(segs * 2, 24 if maxf(r_top, r_bot) > 0.08 else 16)
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
	sm.radial_segments = 32 if r > 0.05 else 20
	sm.rings = 16 if r > 0.05 else 10
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


static var _roofs: = {}

## Telhado de quatro águas detalhado (v0.7.2): telhas de barro em fileiras onduladas com cumeeira
## e espigões, ou sapê em camadas desfiadas. O estilo vem do material (nome da textura antiga).
static func hip_roof(parent: Node, center: Vector3, w: float, d: float, peak: float, m: Material, thickness: = 0.18) -> MeshInstance3D:
	var style: = ""
	if Toon.enabled() and m:
		if m.resource_name == "clay_roof_tiles_02":
			style = "clay"
		elif m.resource_name == "reed_roof_04":
			style = "thatch"
	if style == "":
		return _hip_roof_flat(parent, center, w, d, peak, m, thickness)
	var key: = "%s|%d|%d|%d|%d" % [style, roundi(w * 4.0), roundi(d * 4.0), roundi(peak * 4.0), roundi(thickness * 50.0)]
	if not _roofs.has(key):
		_roofs[key] = _detailed_roof_mesh(w, d, peak, thickness, style)
	var mi: = MeshInstance3D.new()
	mi.mesh = _roofs[key]
	mi.material_override = m
	mi.position = center
	parent.add_child(mi)
	var hx: = w * 0.5
	var hz: = d * 0.5
	var ridge: = maxf(0.0, (w - d) * 0.5)
	var cap_m: Material = flat(Color(0.85, 0.36, 0.24), 0.8) if style == "clay" else flat(Color(0.78, 0.55, 0.26), 0.95)
	var cap_r: = 0.09 if style == "clay" else 0.16
	var r1: = Vector3(- ridge, peak, 0)
	var r2: = Vector3(ridge, peak, 0)
	if ridge > 0.05:
		_beam(mi, r1, r2, cap_r, cap_m)
	for pair in [[Vector3(- hx, 0, - hz), r1], [Vector3(- hx, 0, hz), r1], [Vector3(hx, 0, - hz), r2], [Vector3(hx, 0, hz), r2]]:
		_beam(mi, pair[0], pair[1] + Vector3(0, 0.02, 0), cap_r * 0.8, cap_m)
	return mi

## Peça cilíndrica arredondada entre dois pontos (cumeeira, espigão, viga).
static func _beam(parent: Node, a: Vector3, b: Vector3, r: float, m: Material) -> MeshInstance3D:
	var mi: = MeshInstance3D.new()
	var cm: = CapsuleMesh.new()
	cm.radius = r
	cm.height = a.distance_to(b) + r * 2.0
	cm.radial_segments = 16
	cm.rings = 4
	mi.mesh = cm
	mi.material_override = m
	parent.add_child(mi)
	var dir: = (b - a).normalized()
	var up: = Vector3.UP if absf(dir.dot(Vector3.UP)) < 0.95 else Vector3.RIGHT
	var bas: = Basis.looking_at(dir, up)
	mi.transform = Transform3D(bas * Basis(Vector3.RIGHT, PI * 0.5), (a + b) * 0.5)
	return mi

## Arco (meia-coroa) de moldura sobre portas e janelas, de frente para +Z local.
static func arch(parent: Node, center: Vector3, r_in: float, r_out: float, depth: float, m: Material, rot_y: = 0.0) -> MeshInstance3D:
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var segs: = 24
	var hz: = depth * 0.5
	for i in segs:
		var a0: = PI * float(i) / segs
		var a1: = PI * float(i + 1) / segs
		var i0: = Vector3(cos(a0) * r_in, sin(a0) * r_in, 0)
		var i1: = Vector3(cos(a1) * r_in, sin(a1) * r_in, 0)
		var o0: = Vector3(cos(a0) * r_out, sin(a0) * r_out, 0)
		var o1: = Vector3(cos(a1) * r_out, sin(a1) * r_out, 0)
		for face in [[hz, Vector3(0, 0, 1)], [- hz, Vector3(0, 0, -1)]]:
			var z: float = face[0]
			var n: Vector3 = face[1]
			var tri: = [i0, o0, o1, i0, o1, i1] if z > 0 else [i0, o1, o0, i0, i1, o1]
			for v in tri:
				st.set_normal(n)
				st.add_vertex(v + Vector3(0, 0, z))
		var no: = Vector3(cos((a0 + a1) * 0.5), sin((a0 + a1) * 0.5), 0)
		for v in [o0 + Vector3(0, 0, hz), o0 - Vector3(0, 0, hz), o1 + Vector3(0, 0, hz), o1 + Vector3(0, 0, hz), o0 - Vector3(0, 0, hz), o1 - Vector3(0, 0, hz)]:
			st.set_normal(no)
			st.add_vertex(v)
		for v in [i0 + Vector3(0, 0, hz), i1 + Vector3(0, 0, hz), i0 - Vector3(0, 0, hz), i1 + Vector3(0, 0, hz), i1 - Vector3(0, 0, hz), i0 - Vector3(0, 0, hz)]:
			st.set_normal(- no)
			st.add_vertex(v)
	var mi: = MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = m
	mi.position = center
	mi.rotation.y = rot_y
	parent.add_child(mi)
	return mi

static func _detailed_roof_mesh(w: float, d: float, peak: float, thickness: float, style: String) -> Mesh:
	var hx: = w * 0.5
	var hz: = d * 0.5
	var ridge: = maxf(0.0, (w - d) * 0.5)
	var a: = Vector3(- hx, 0, - hz)
	var b_: = Vector3(hx, 0, - hz)
	var c: = Vector3(hx, 0, hz)
	var dd: = Vector3(- hx, 0, hz)
	var r1: = Vector3(- ridge, peak, 0)
	var r2: = Vector3(ridge, peak, 0)
	# [base0, base1, topo0, topo1]
	var faces: = [[a, b_, r1, r2], [b_, c, r2, r2], [c, dd, r2, r1], [dd, a, r1, r1]]
	var st: = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var tile_w: = 0.26 if style == "clay" else 0.5
	var course: = 0.34 if style == "clay" else 0.3
	for f in faces:
		var p0: Vector3 = f[0]
		var p1: Vector3 = f[1]
		var q0: Vector3 = f[2]
		var q1: Vector3 = f[3]
		var L: = p0.distance_to(p1)
		var S: = ((p0 + p1) * 0.5).distance_to((q0 + q1) * 0.5)
		var n: Vector3 = (p1 - p0).cross(q0.lerp(q1, 0.5) - p0).normalized()
		if n.y < 0:
			n = - n
		var nu: = clampi(int(L / tile_w * (4.0 if style == "clay" else 1.5)), 6, 220)
		var nv: = clampi(int(S / course * 3.0), 4, 80)
		var grid: = []
		for j in nv + 1:
			var v: = float(j) / nv
			var row: = []
			for i in nu + 1:
				var u: = float(i) / nu
				var base: = p0.lerp(p1, u).lerp(q0.lerp(q1, u), v)
				var along: = u * L
				var up_s: = v * S
				var fcourse: = fposmod(up_s / course, 1.0)
				var disp: = 0.0
				if style == "clay":
					disp = 0.045 * absf(sin(PI * along / tile_w)) + 0.028 * (1.0 - fcourse)
				else:
					var jag: = 0.5 + 0.5 * sin(along * 7.3 + floor(up_s / course) * 2.1) * sin(along * 3.1)
					disp = 0.07 * pow(1.0 - fcourse, 1.6) * (0.6 + 0.4 * jag)
				# perto da borda e do topo a ondulação some (para fechar com a cumeeira e o beiral)
				disp *= clampf(v * 12.0, 0.25, 1.0) * clampf((1.0 - v) * 10.0, 0.0, 1.0)
				row.append(base + n * disp)
			grid.append(row)
		for j in nv:
			for i in nu:
				var q: = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
				var fn: Vector3 = (q[1] - q[0]).cross(q[3] - q[0])
				var flip: = fn.dot(n) < 0.0
				var tris: = [[0, 1, 2], [0, 2, 3]] if not flip else [[0, 2, 1], [0, 3, 2]]
				for t in tris:
					var tn: Vector3 = (q[t[1]] - q[t[0]]).cross(q[t[2]] - q[t[0]]).normalized()
					if tn.length() < 0.5:
						tn = n
					tn = tn.lerp(n, 0.35).normalized()
					for k in t:
						st.set_normal(tn)
						st.set_uv(Vector2(q[k].x + q[k].z, q[k].y) * 0.55)
						st.add_vertex(q[k])
		# lado de baixo (forro) e a espessura do beiral
		var u0: = p0 - Vector3(0, thickness, 0)
		var u1: = p1 - Vector3(0, thickness, 0)
		var w0: = q0 - Vector3(0, thickness, 0)
		var w1: = q1 - Vector3(0, thickness, 0)
		for tri in [[u0, w0, u1], [u1, w0, w1]]:
			for vv in tri:
				st.set_normal(Vector3.DOWN)
				st.set_uv(Vector2(vv.x, vv.z) * 0.55)
				st.add_vertex(vv)
		var en: = (p1 - p0).cross(Vector3.DOWN).normalized()
		for vv in [p0, u0, p1, p1, u0, u1]:
			st.set_normal(en)
			st.set_uv(Vector2(vv.x + vv.z, vv.y * 3.0) * 0.55)
			st.add_vertex(vv)
	var arr: = st.commit_to_arrays()
	var im: = ImporterMesh.new()
	im.add_surface(Mesh.PRIMITIVE_TRIANGLES, arr)
	im.generate_lods(25.0, 60.0, [])
	return im.get_mesh()

static func _hip_roof_flat(parent: Node, center: Vector3, w: float, d: float, peak: float, m: Material, thickness: = 0.18) -> MeshInstance3D:
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
