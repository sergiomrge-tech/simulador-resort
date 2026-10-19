extends RefCounted
## Verificador de primitivas (pente fino da regra "nada de bolas e quadrados"): lista malhas BoxMesh/CylinderMesh/SphereMesh/
## CapsuleMesh/TorusMesh/PrismMesh visíveis no mapa que NÃO sejam parede/piso/telhado (grandes ou finas) e as agrupa por formato.
## Uso: godot -- --shot=vila --full --primcheck  (linhas "PRIM ..." no log)

static func run(world: Node3D) -> void:
	var groups: = {}
	for mi in world.find_children("*", "MeshInstance3D", true, false):
		var m: MeshInstance3D = mi
		if not m.is_visible_in_tree() or m.mesh == null:
			continue
		var kind: = ""
		var sz: = Vector3.ZERO
		if m.mesh is BoxMesh:
			kind = "box"
			sz = (m.mesh as BoxMesh).size
		elif m.mesh is CylinderMesh:
			kind = "cyl"
			var cm: CylinderMesh = m.mesh
			sz = Vector3(maxf(cm.top_radius, cm.bottom_radius) * 2.0, cm.height, maxf(cm.top_radius, cm.bottom_radius) * 2.0)
		elif m.mesh is SphereMesh:
			kind = "sphere"
			sz = Vector3.ONE * (m.mesh as SphereMesh).radius * 2.0
		elif m.mesh is CapsuleMesh:
			kind = "capsule"
			sz = Vector3((m.mesh as CapsuleMesh).radius * 2.0, (m.mesh as CapsuleMesh).height, 0)
		elif m.mesh is TorusMesh:
			kind = "torus"
			sz = Vector3.ONE * (m.mesh as TorusMesh).outer_radius * 2.0
		elif m.mesh is PrismMesh:
			kind = "prism"
			sz = (m.mesh as PrismMesh).size
		else:
			continue
		var p: = m.get_parent()
		var skip: = false
		while p and p != world:
			if p.is_in_group("npc"):
				skip = true
				break
			p = p.get_parent()
		if skip:
			continue
		var s: = sz * m.global_transform.basis.get_scale()
		var dims: = [s.x, s.y, s.z]
		dims.sort()
		# paredes, pisos, lajes, telhados e faixas de acabamento: maior medida > 1,6 m e (mais fina < 0,35 m) -> arquitetura
		if dims[2] > 1.6 and dims[0] < 0.35:
			continue
		if dims[2] > 3.0:
			continue
		var col: = Color.WHITE
		var mat: = m.material_override
		if mat is BaseMaterial3D:
			col = (mat as BaseMaterial3D).albedo_color
		var key: = "%s %.2fx%.2fx%.2f c=%s" % [kind, s.x, s.y, s.z, col.to_html(false)]
		if not groups.has(key):
			groups[key] = {"n": 0, "at": m.global_position, "name": String(m.get_parent().name) + "/" + String(m.name)}
		groups[key].n += 1
	var keys: = groups.keys()
	keys.sort_custom(func(a, b): return groups[a].n > groups[b].n)
	for k in keys:
		var g: Dictionary = groups[k]
		print("PRIM n=%d %s at (%.1f, %.1f, %.1f) %s" % [g.n, k, g.at.x, g.at.y, g.at.z, g.name])
	print("PRIMCHECK grupos=%d" % keys.size())
