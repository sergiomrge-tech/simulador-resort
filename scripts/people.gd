extends RefCounted
class_name Ppl
## Pessoas (v0.7.3): corpo, rosto e cabelo vêm do pacote CC0 "Universal Base Characters" (Quaternius).
## As roupas (camisa e bermuda) são geradas aqui a partir da própria malha do corpo, deslocada para fora,
## então já nascem com o mesmo esqueleto e os mesmos pesos de pele. As animações vêm do guest.glb antigo
## (mesmo esqueleto UAL de 65 ossos, mesmos nomes de osso).

const DIR: = "res://assets/models/ubc/"
const SHIRT_BONES: = ["spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r"]
const SHORTS_BONES: = ["pelvis", "thigh_l", "thigh_r"]
const HAIR_MALE: = ["Hair_Buzzed", "Hair_SimpleParted", "Hair_SimpleParted", "Hair_Long", "Hair_Buzzed", ""]
const HAIR_FEMALE: = ["Hair_BuzzedFemale", "Hair_Long", "Hair_Buns", "Hair_SimpleParted", "Hair_Long", "Hair_Buns"]

static var _scenes: = {}
static var _clothes: = {}
static var _hairs: = {}
static var _anim_src: PackedScene

static func _scene(female: bool) -> PackedScene:
	var key: = "f" if female else "m"
	if not _scenes.has(key):
		_scenes[key] = load(DIR + ("Superhero_Female_FullBody.gltf" if female else "Superhero_Male_FullBody.gltf"))
	return _scenes[key]

## Instancia o corpo e enxerta o AnimationPlayer do boneco antigo (mesmos ossos).
static func build_body(female: bool) -> Node3D:
	var root: Node3D = _scene(female).instantiate()
	if _anim_src == null:
		_anim_src = load("res://assets/models/ual/guest.glb")
	var old: Node = _anim_src.instantiate()
	var ap: = old.find_child("AnimationPlayer", true, false)
	if ap:
		ap.get_parent().remove_child(ap)
		root.add_child(ap)
		ap.owner = null
	old.queue_free()
	return root

static func skeleton_of(root: Node) -> Skeleton3D:
	var s: = root.find_children("*", "Skeleton3D", true, false)
	return s[0] if s.size() > 0 else null

static func body_mesh(root: Node) -> MeshInstance3D:
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var n: = String(mi.name).to_lower()
		if not n.contains("eye") and not n.contains("brow"):
			return mi
	return null

static func _bone_name(mi: MeshInstance3D, skel: Skeleton3D, idx: int) -> String:
	var sk: Skin = mi.skin
	if sk != null and idx < sk.get_bind_count():
		var nm: = sk.get_bind_name(idx)
		if nm != "":
			return nm
		var b: = sk.get_bind_bone(idx)
		if b >= 0 and b < skel.get_bone_count():
			return skel.get_bone_name(b)
	return skel.get_bone_name(idx) if idx < skel.get_bone_count() else ""

## Camisa (zona 1) e bermuda (zona 2): triângulos cujos 3 vértices pertencem ao grupo de ossos, empurrados para fora.
static func clothes(female: bool, mi: MeshInstance3D, skel: Skeleton3D) -> Dictionary:
	var key: = "f" if female else "m"
	if _clothes.has(key):
		return _clothes[key]
	var arrays: Array = mi.mesh.surface_get_arrays(0)
	var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var norms: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
	var uvs: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV] if arrays[Mesh.ARRAY_TEX_UV] != null else PackedVector2Array()
	var idx: PackedInt32Array = arrays[Mesh.ARRAY_INDEX] if arrays[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
	var bones: PackedInt32Array = arrays[Mesh.ARRAY_BONES] if arrays[Mesh.ARRAY_BONES] != null else PackedInt32Array()
	var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS] if arrays[Mesh.ARRAY_WEIGHTS] != null else PackedFloat32Array()
	var out: = {}
	var hem_shirt: = 0.96 if female else 0.98
	var neck_y: = 1.45 if female else 1.48
	var sleeve_x: = 0.34 if female else 0.4
	var hem_shorts: = 0.64 if female else 0.66
	var waist_y: = 1.02 if female else 1.04
	if verts.is_empty() or bones.is_empty() or idx.is_empty():
		_clothes[key] = out
		return out
	var n: = verts.size()
	var stride: = bones.size() / n
	var shirt_w: = PackedFloat32Array()
	var shorts_w: = PackedFloat32Array()
	shirt_w.resize(n)
	shorts_w.resize(n)
	var name_cache: = {}
	for v in n:
		var sw: = 0.0
		var hw: = 0.0
		for k in stride:
			var w: = weights[v * stride + k]
			if w <= 0.0:
				continue
			var bi: = bones[v * stride + k]
			if not name_cache.has(bi):
				name_cache[bi] = _bone_name(mi, skel, bi)
			var bn: String = name_cache[bi]
			if SHIRT_BONES.has(bn):
				sw += w
			elif SHORTS_BONES.has(bn):
				hw += w
		shirt_w[v] = sw
		shorts_w[v] = hw
	for spec in [["shirt", shirt_w, 1.0, 0.016], ["shorts", shorts_w, 2.0, 0.014]]:
		var sel: PackedFloat32Array = spec[1]
		var remap: = {}
		var nv: = PackedVector3Array()
		var nn: = PackedVector3Array()
		var nuv: = PackedVector2Array()
		var nb: = PackedInt32Array()
		var nw: = PackedFloat32Array()
		var ncol: = PackedColorArray()
		var nidx: = PackedInt32Array()
		var zone: float = spec[2]
		var off: float = spec[3]
		var t: = 0
		while t + 2 < idx.size():
			var a: = idx[t]
			var b: = idx[t + 1]
			var c: = idx[t + 2]
			t += 3
			# bainha reta: corta por altura (e pelo comprimento da manga) em vez de seguir os pesos dos ossos
			var cut_ok: = true
			for vi in [a, b, c]:
				var pv: Vector3 = verts[vi]
				if zone < 1.5:
					if pv.y < hem_shirt or pv.y > neck_y + minf(0.12, maxf(0.0, (absf(pv.x) - 0.1) * 1.1)) or absf(pv.x) > sleeve_x:
						cut_ok = false
				elif pv.y < hem_shorts or pv.y > waist_y:
					cut_ok = false
			if not cut_ok:
				continue
			for vi in [a, b, c]:
				if not remap.has(vi):
					remap[vi] = nv.size()
					nv.append(verts[vi] + norms[vi] * off)
					nn.append(norms[vi])
					if not uvs.is_empty():
						nuv.append(uvs[vi])
					var ws: = 0.0
					for k in 4:
						nb.append(bones[vi * stride + k])
						var w2: = weights[vi * stride + k]
						nw.append(w2)
						ws += w2
					if ws > 0.0001:
						var base: = nw.size() - 4
						for k in 4:
							nw[base + k] = nw[base + k] / ws
					ncol.append(Color(zone * 32.0 / 255.0, 0, 0, 1))
				nidx.append(remap[vi])
		if nidx.is_empty():
			continue
		var arr: = []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = nv
		arr[Mesh.ARRAY_NORMAL] = nn
		if not nuv.is_empty():
			arr[Mesh.ARRAY_TEX_UV] = nuv
		arr[Mesh.ARRAY_COLOR] = ncol
		arr[Mesh.ARRAY_BONES] = nb
		arr[Mesh.ARRAY_WEIGHTS] = nw
		arr[Mesh.ARRAY_INDEX] = nidx
		var am: = ArrayMesh.new()
		am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		out[spec[0]] = am
	_clothes[key] = out
	return out

static func hair_mesh(style: String) -> MeshInstance3D:
	if style == "":
		return null
	if not _hairs.has(style):
		_hairs[style] = load(DIR + style + ".gltf")
	var root: Node = (_hairs[style] as PackedScene).instantiate()
	var found: = root.find_children("*", "MeshInstance3D", true, false)
	if found.is_empty():
		root.queue_free()
		return null
	var mi: MeshInstance3D = found[0]
	mi.get_parent().remove_child(mi)
	root.queue_free()
	return mi

## Deixa um material importado com cara de cartoon e tingido.
static func toon_copy(src: Material, tint: Color) -> Material:
	if src is BaseMaterial3D:
		var m: BaseMaterial3D = (src as BaseMaterial3D).duplicate()
		m.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
		m.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
		m.roughness = 0.85
		m.metallic = 0.0
		m.normal_enabled = false
		m.rim_enabled = false
		m.albedo_color = tint
		return m
	return src

static var _gray_hair: = {}

## Cabelo: a textura original é azulada; usa uma versão em tons de cinza (média 0,5) para a cor do cabelo sair exata.
static func hair_copy(src: Material, tint: Color) -> Material:
	var m: Material = toon_copy(src, tint)
	if m is BaseMaterial3D and (m as BaseMaterial3D).albedo_texture != null:
		var bm: BaseMaterial3D = m as BaseMaterial3D
		var tex: Texture2D = bm.albedo_texture
		var key: = tex.get_instance_id()
		if not _gray_hair.has(key):
			var img: Image = tex.get_image()
			if img != null:
				if img.is_compressed():
					img.decompress()
				img.resize(256, 256)
				var sum: = 0.0
				var cnt: = 0
				for y in 256:
					for x in 256:
						var c: = img.get_pixel(x, y)
						var l: = c.get_luminance()
						img.set_pixel(x, y, Color(l, l, l, c.a))
						if c.a > 0.5:
							sum += l
							cnt += 1
				var k: = 0.5 / maxf(sum / maxf(cnt, 1), 0.02)
				for y in 256:
					for x in 256:
						var c: = img.get_pixel(x, y)
						var l: = clampf(c.r * k, 0.0, 1.0)
						img.set_pixel(x, y, Color(l, l, l, c.a))
				_gray_hair[key] = ImageTexture.create_from_image(img)
			else:
				_gray_hair[key] = tex
		bm.albedo_texture = _gray_hair[key]
	return m

## Cor final do corpo: textura clara ou escura (já com a roupa de baixo desenhada) tingida para o tom de pele.
static func skin_material(female: bool, skin: Color) -> StandardMaterial3D:
	var lum: = skin.get_luminance()
	var dark: = lum < 0.5
	var path: = DIR
	if female:
		path += "T_Superhero_Female_Dark_BaseColor.png" if dark else "T_Superhero_Female_Light_BaseColor.png"
	else:
		path += "T_Superhero_Male_Dark.png" if dark else "T_Superhero_Male_Ligh.png"
	var est: = Color(0.46, 0.3, 0.22) if dark else Color(0.82, 0.64, 0.52)
	var tint: = Color(clampf(skin.r / est.r, 0.45, 1.5), clampf(skin.g / est.g, 0.45, 1.5), clampf(skin.b / est.b, 0.45, 1.5))
	var m: = StandardMaterial3D.new()
	m.albedo_texture = load(path)
	m.albedo_color = tint
	m.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
	m.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	m.roughness = 0.8
	m.rim_enabled = true
	m.rim = 0.2
	m.rim_tint = 0.6
	return m
