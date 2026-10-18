extends RefCounted
class_name Real
## Carrega modelos REAIS baixados da web (Poly Haven e Kenney, CC0) e posiciona com tamanho certo.
## Regra do projeto: nada de "bolas e quadrados" montados por código. Fontes em CREDITS.md / tools/fetch_assets.py.
## Chave "k:nome" = Kenney (assets/models/kenney/nome.glb); chave "nome" = Poly Haven (assets/models[_hd]/nome/nome.gltf).

static var _cache: = {}

## Modelos Poly Haven muito escuros (viravam quase pretos sob o toon): clareados por chave. Revisão visual 18/10/2026.
const LIFT: = {
	"bar_chair_round_01": Color(2.1, 1.85, 1.6), "wooden_stool_01": Color(1.6, 1.5, 1.4),
	"GothicBed_01": Color(1.25, 1.2, 1.15), "ceiling_fan": Color(5.0, 4.2, 3.4),
	"Rockingchair_01": Color(1.9, 1.7, 1.5), "WoodenChair_01": Color(1.6, 1.5, 1.4),
}

static func lift(key: String) -> Color:
	return LIFT.get(key, Color.WHITE)

static func path_of(key: String) -> String:
	if key.begins_with("q:"):
		return "res://assets/models/qnat/%s.gltf" % key.substr(2)
	if key.begins_with("g:"):
		return "res://assets/models/gen/%s.glb" % key.substr(2)
	if key.begins_with("k:"):
		return "res://assets/models/kenney/%s.glb" % key.substr(2)
	var hd: = "res://assets/models_hd/%s/%s.gltf" % [key, key]
	if Quality.hd and ResourceLoader.exists(hd):
		return hd
	return "res://assets/models/%s/%s.gltf" % [key, key]

static func available(key: String) -> bool:
	return ResourceLoader.exists(path_of(key))

static func _scene(key: String) -> PackedScene:
	var p: = path_of(key)
	if not _cache.has(p):
		_cache[p] = load(p) if ResourceLoader.exists(p) else null
	return _cache[p]

## Instancia o modelo, ajusta para `height` (m) de altura (ou `width` se height <= 0), centra em XZ e apoia a base em y = 0.
## `tint` multiplica a cor (deixa mais vivo/cartoon). Retorna null se o arquivo não existe.
## height < 0: escala uniforme direta (-height); center_xz = false mantém a origem do modelo em XZ (chapéus, óculos).
static func place(parent: Node, key: String, pos: Vector3, height: float, rot_y: = 0.0, tint: = Color.WHITE, width: = 0.0, center_xz: = true) -> Node3D:
	var ps: = _scene(key)
	if ps == null:
		return null
	var inst: Node3D = ps.instantiate()
	for mi in inst.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (mi as MeshInstance3D).mesh
		if mesh == null:
			continue
		for si in mesh.get_surface_count():
			var sm: Material = mesh.surface_get_material(si)
			if sm:
				var tm: Material = Toon.toonify(sm)
				if (key.begins_with("q:") or key.begins_with("k:coconut")) and tm is BaseMaterial3D and sm is BaseMaterial3D:
					(tm as BaseMaterial3D).albedo_color = (sm as BaseMaterial3D).albedo_color   # já são estilizados: sem o clareamento do toonify
				if tm is BaseMaterial3D and tint != Color.WHITE:
					(tm as BaseMaterial3D).albedo_color = (tm as BaseMaterial3D).albedo_color * tint
				(mi as MeshInstance3D).set_surface_override_material(si, tm)
	var holder: = Node3D.new()
	holder.position = pos
	holder.rotation.y = rot_y
	parent.add_child(holder)
	holder.add_child(inst)
	var bb: = _aabb(inst)
	var ref: float = bb.size.y if height > 0.0 else maxf(bb.size.x, bb.size.z)
	var want: float = height if height > 0.0 else width
	var s: float = want / maxf(ref, 0.0001)
	if height < 0.0:
		s = -height
	inst.scale = Vector3.ONE * s
	var c: = bb.get_center()
	inst.position = Vector3(-c.x * s if center_xz else 0.0, -bb.position.y * s, -c.z * s if center_xz else 0.0)
	return holder

static func _aabb(n: Node3D) -> AABB:
	var out: = AABB()
	var first: = true
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var m: = mi as MeshInstance3D
		if m.mesh == null:
			continue
		var t: Transform3D = Transform3D.IDENTITY
		var cur: Node = m
		while cur != null and cur != n:
			if cur is Node3D:
				t = (cur as Node3D).transform * t
			cur = cur.get_parent()
		var bb: AABB = t * m.get_aabb()
		out = bb if first else out.merge(bb)
		first = false
	return out
