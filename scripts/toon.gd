extends RefCounted
class_name Toon
## Visual cartoon do Maré Alta (v0.7): paleta saturada, sombreamento em faixas (toon), texturas
## "pintadas à mão" geradas por código e contorno escuro em tela cheia.
## B.mat()/B.flat() passam por aqui, então todo o mundo procedural muda de uma vez.

## Cor base de cada material antigo (nome da textura do Poly Haven) e o padrão desenhado nele.
const PALETTE: = {
	"white_plaster": [Color(0.99, 0.95, 0.88), "plaster"],
	"white_stucco": [Color(1.0, 0.97, 0.92), "plaster"],
	"weathered_planks": [Color(0.86, 0.62, 0.4), "planks"],
	"oak_wood_planks": [Color(0.9, 0.6, 0.32), "planks"],
	"brown_planks_05": [Color(0.8, 0.52, 0.3), "planks"],
	"dark_wooden_planks": [Color(0.56, 0.33, 0.2), "planks"],
	"bamboo_wall": [Color(0.95, 0.8, 0.45), "bamboo"],
	"rough_linen": [Color(0.98, 0.96, 0.92), "flat"],
	"fabric_pattern_07": [Color(1.0, 0.55, 0.42), "stripes"],
	"rattan": [Color(0.92, 0.7, 0.42), "weave"],
	"blue_floor_tiles_01": [Color(0.32, 0.74, 0.9), "tiles"],
	"light_stone": [Color(0.95, 0.9, 0.82), "tiles"],
	"patio_tiles": [Color(0.98, 0.78, 0.6), "tiles"],
	"terracotta_floor_tiles": [Color(0.92, 0.52, 0.34), "tiles"],
	"reed_roof_04": [Color(0.96, 0.75, 0.38), "thatch"],
	"palm_tree_bark": [Color(0.66, 0.47, 0.32), "bark"],
	"cobblestone_floor_04": [Color(0.78, 0.74, 0.7), "cobble"],
	"calcada": [Color(0.98, 0.97, 0.94), "calcada"],
	"clay_roof_tiles_02": [Color(0.95, 0.45, 0.3), "rooftiles"],
	"coast_sand_01": [Color(1.0, 0.88, 0.62), "flat"],
	"damp_beach_sand": [Color(0.9, 0.74, 0.5), "flat"],
	"forest_floor": [Color(0.36, 0.62, 0.3), "flat"],
	"leafy_grass": [Color(0.42, 0.75, 0.32), "flat"],
	"rock_face": [Color(0.62, 0.58, 0.55), "flat"],
}

static var _patterns: = {}
static var _mats: = {}

static func enabled() -> bool:
	return true

## Mistura a cor base do material com o tom pedido pelo código antigo.
## Tons saturados (teal, terracota) viram a cor principal; tons claros só clareiam/escurecem a base.
static func resolve_color(n: String, tint: Color) -> Color:
	var base: Color = PALETTE.get(n, [Color(0.9, 0.85, 0.78), "flat"])[0]
	var t: = Color(tint.r, tint.g, tint.b)
	var c: Color
	if t.s > 0.25 and maxf(t.r, maxf(t.g, t.b)) <= 1.0:
		c = Color.from_hsv(t.h, clampf(t.s * 1.15, 0.0, 1.0), clampf(t.v * 1.12 + 0.06, 0.0, 1.0))
	else:
		var bright: = (t.r + t.g + t.b) / 3.0
		c = base * Color(bright, bright, bright)
		c = c.lerp(base * t, 0.5)
	c.a = tint.a
	return c

static func pattern_kind(n: String) -> String:
	return PALETTE.get(n, [Color.WHITE, "flat"])[1]

## Textura em tons de cinza claro (0.78..1.0) com o desenho do material; multiplica a cor base.
static func pattern(kind: String) -> Texture2D:
	if kind == "flat":
		return null
	if _patterns.has(kind):
		return _patterns[kind]
	var s: = 128
	var img: = Image.create(s, s, true, Image.FORMAT_L8)
	var rng: = RandomNumberGenerator.new()
	rng.seed = hash(kind)
	for y in s:
		for x in s:
			var v: = 1.0
			match kind:
				"planks":
					var row: = y / 16
					var off: = (row * 37) % s
					v = 0.97 + 0.03 * sin(float(x) * 0.3 + row)
					if y % 16 == 0:
						v = 0.72
					elif (x + off) % 64 == 0:
						v = 0.8
				"tiles":
					v = 0.78 if (x % 32 == 0 or y % 32 == 0) else 0.98 - 0.04 * float(((x / 32) + (y / 32)) % 2)
				"thatch":
					v = 0.86 + 0.14 * absf(sin(float(x) * 0.9 + sin(float(y) * 0.2) * 2.0))
					if y % 24 < 2:
						v *= 0.82
				"bamboo":
					v = 0.82 if x % 16 < 2 else 0.98
					if y % 40 == 0:
						v = 0.78
				"stripes":
					v = 1.0 if (x / 16) % 2 == 0 else 0.84
				"weave":
					v = 0.82 + 0.18 * float(((x / 8) + (y / 8)) % 2)
				"bark":
					v = 0.82 + 0.18 * absf(sin(float(y) * 0.35 + float(x) * 0.05))
				"cobble":
					var cx: = float(x % 21) - 10.0
					var cy: = float((y + (x / 21) * 9) % 21) - 10.0
					v = 0.75 if (cx * cx + cy * cy) > 90.0 else 0.97
				"calcada":
					var wv: = sin(float(x) * 0.098) * 14.0
					v = 0.55 if int(float(y) + wv) % 32 < 10 else 0.98
				"rooftiles":
					v = 0.98 - 0.16 * float(y % 16) / 16.0
					if x % 22 == 0:
						v = 0.78
				"plaster":
					v = 0.96 + rng.randf() * 0.04
			img.set_pixel(x, y, Color(v, v, v))
	img.generate_mipmaps()
	var tex: = ImageTexture.create_from_image(img)
	_patterns[kind] = tex
	return tex

static func _base(c: Color, rough: float) -> StandardMaterial3D:
	var m: = StandardMaterial3D.new()
	m.albedo_color = c
	m.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
	m.specular_mode = BaseMaterial3D.SPECULAR_TOON
	m.roughness = clampf(rough, 0.35, 1.0)
	m.metallic_specular = 0.25
	m.rim_enabled = true
	m.rim = 0.25
	m.rim_tint = 0.6
	if c.a < 0.99:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
	return m

static func material(n: String, scale: float, tint: Color, rough: float) -> StandardMaterial3D:
	var key: = "%s|%s|%s|%s" % [n, scale, tint.to_html(), rough]
	if _mats.has(key):
		return _mats[key]
	var m: = _base(resolve_color(n, tint), rough)
	m.resource_name = n
	var tex: = pattern(pattern_kind(n))
	if tex:
		m.albedo_texture = tex
		m.uv1_triplanar = true
		m.uv1_world_triplanar = true
		m.uv1_scale = Vector3.ONE * scale * 0.5
		m.uv1_triplanar_sharpness = 6.0
		m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_mats[key] = m
	return m

## Cor chapada: levemente mais saturada para o visual cartoon.
static func flat(c: Color, rough: float, metal: float) -> StandardMaterial3D:
	var key: = "flat|%s|%s|%s" % [c.to_html(), rough, metal]
	if _mats.has(key):
		return _mats[key]
	var cc: = c
	if cc.s > 0.08:
		cc = Color.from_hsv(cc.h, clampf(cc.s * 1.12, 0.0, 1.0), cc.v, cc.a)
	var m: = _base(cc, rough)
	m.metallic = metal * 0.5
	_mats[key] = m
	return m

## Deixa um material vindo de glTF com cara de cartoon (sem textura de normal, faixas de luz).
static func toonify(mt: Material) -> Material:
	if mt is StandardMaterial3D:
		var s: StandardMaterial3D = mt.duplicate()
		s.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
		s.specular_mode = BaseMaterial3D.SPECULAR_TOON
		s.normal_enabled = false
		s.roughness_texture = null
		s.metallic_texture = null
		s.ao_enabled = false
		return s
	return mt

## Tufo de capim desenhado: 7 folhas pontudas em dois verdes, base mais escura.
static func grass_tex() -> Texture2D:
	if _patterns.has("grass_tex"):
		return _patterns["grass_tex"]
	var w: = 128
	var h: = 128
	var img: = Image.create(w, h, true, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var rng: = RandomNumberGenerator.new()
	rng.seed = 42
	var greens: = [Color(0.36, 0.78, 0.3), Color(0.5, 0.88, 0.34), Color(0.26, 0.66, 0.28)]
	for k in 7:
		var base_x: = 20.0 + k * 14.0 + rng.randf_range(-4, 4)
		var tip_x: = base_x + rng.randf_range(-22, 22)
		var tip_y: = rng.randf_range(6, 40)
		var half: = rng.randf_range(5.0, 8.0)
		var col: Color = greens[k % greens.size()]
		for y in range(int(tip_y), h):
			var t: = (float(y) - tip_y) / (h - tip_y)
			var cx: = lerpf(tip_x, base_x, pow(t, 0.7))
			var hw: = half * t
			for x in range(int(cx - hw), int(cx + hw) + 1):
				if x >= 0 and x < w:
					var c: = col.darkened(0.25 * smoothstep(0.7, 1.0, t))
					img.set_pixel(x, y, c)
	img.generate_mipmaps()
	var tex: = ImageTexture.create_from_image(img)
	_patterns["grass_tex"] = tex
	return tex

## Arbusto desenhado: bolas de folhagem sobrepostas com uma flor ou outra.
static func bush_tex() -> Texture2D:
	if _patterns.has("bush_tex"):
		return _patterns["bush_tex"]
	var s: = 128
	var img: = Image.create(s, s, true, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var rng: = RandomNumberGenerator.new()
	rng.seed = 7
	var blobs: = []
	for k in 9:
		blobs.append([Vector2(rng.randf_range(28, 100), rng.randf_range(40, 110)), rng.randf_range(16, 28)])
	blobs.sort_custom(func(a, b): return a[0].y < b[0].y)
	for b in blobs:
		var c: Vector2 = b[0]
		var r: float = b[1]
		for y in range(int(c.y - r), int(c.y + r) + 1):
			for x in range(int(c.x - r), int(c.x + r) + 1):
				if x < 0 or y < 0 or x >= s or y >= s:
					continue
				var d: = Vector2(x, y).distance_to(c)
				if d <= r:
					var lit: = (Vector2(x, y) - c).dot(Vector2(-0.5, -0.8)) / r
					var col: = Color(0.28, 0.68, 0.3) if lit < 0.15 else Color(0.42, 0.82, 0.34)
					if d > r - 2.5:
						col = Color(0.18, 0.48, 0.24)
					img.set_pixel(x, y, col)
	for k in 6:
		var fc: = Vector2(rng.randf_range(30, 98), rng.randf_range(35, 100))
		var fcol: Color = [Color(1.0, 0.45, 0.6), Color(1.0, 0.85, 0.3), Color(1.0, 1.0, 1.0)][k % 3]
		for y in range(int(fc.y) - 3, int(fc.y) + 4):
			for x in range(int(fc.x) - 3, int(fc.x) + 4):
				if x >= 0 and y >= 0 and x < s and y < s and img.get_pixel(x, y).a > 0.5 and Vector2(x, y).distance_to(fc) < 3.2:
					img.set_pixel(x, y, fcol)
	img.generate_mipmaps()
	var tex: = ImageTexture.create_from_image(img)
	_patterns["bush_tex"] = tex
	return tex

## Contorno em tela cheia preso à câmera.
static func attach_outline(cam: Camera3D) -> MeshInstance3D:
	if cam == null or RenderingServer.get_current_rendering_method() != "forward_plus":
		return null
	var q: = MeshInstance3D.new()
	q.name = "ToonOutline"
	var qm: = QuadMesh.new()
	qm.size = Vector2(2, 2)
	qm.flip_faces = true
	q.mesh = qm
	q.extra_cull_margin = 16384.0
	q.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var sm: = ShaderMaterial.new()
	sm.shader = load("res://shaders/outline.gdshader")
	q.material_override = sm
	q.position = Vector3(0, 0, -1)
	cam.add_child(q)
	return q
