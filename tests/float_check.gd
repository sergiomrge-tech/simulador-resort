extends RefCounted
## Pente fino automático: acha objetos "flutuando" (base acima de qualquer superfície embaixo) ou afundados.
## Agrupa as malhas por modelo (raiz da cena instanciada) e compara a base de cada um com o topo dos outros e com o chão.
## Uso: godot -- --shot=vila --floatcheck  (saída: linhas "FLOAT ..." no log)

static func _root_of(mi: Node, world: Node) -> Node:
	var n: Node = mi
	var best: Node = mi
	while n and n != world:
		if n.scene_file_path != "":
			best = n
		n = n.get_parent()
	# o holder de Real.place (Node3D sem malha com um único filho instanciado) é a raiz lógica
	if best.get_parent() and best.get_parent() != world and best.get_parent().get_child_count() == 1 and not (best.get_parent() is MeshInstance3D):
		best = best.get_parent()
	return best

static func run(world: Node3D) -> void:
	var groups: = {}
	var big: Array = []
	for mi in world.find_children("*", "MeshInstance3D", true, false):
		var m: MeshInstance3D = mi
		if not m.is_visible_in_tree() or m.mesh == null:
			continue
		var p: = m.get_parent()
		var skip: = false
		while p and p != world:
			if p.is_in_group("npc") or p is Skeleton3D:
				skip = true
				break
			p = p.get_parent()
		if skip:
			continue
		var bb: AABB = m.global_transform * m.get_aabb()
		if bb.size.x > 6.0 or bb.size.z > 6.0 or bb.size.y > 6.0:
			# peças grandes (calçadas, pisos, píer, plataformas) só servem de apoio
			big.append(bb)
			continue
		var r: = _root_of(m, world)
		var key: = r.get_instance_id()
		if groups.has(key):
			groups[key].bb = groups[key].bb.merge(bb)
			groups[key].parts.append(bb)
		else:
			groups[key] = {"bb": bb, "node": r, "parts": [bb]}
	var list: Array = groups.values()
	var n_float: = 0
	for g in list:
		var bb: AABB = g.bb
		if bb.size.y < 0.015:
			continue
		var c: = bb.get_center()
		var bottom: = bb.position.y
		var ground: = float(world.call("_height", c.x, c.z)) if world.has_method("_height") else 0.0
		var support: = ground
		for ob2 in big:
			var bg: AABB = ob2
			if c.x >= bg.position.x and c.x <= bg.end.x and c.z >= bg.position.z and c.z <= bg.end.z:
				# topo real de uma laje grande: só conta se for fina (piso) ou se a base do objeto estiver perto do topo
				var top2: = bg.end.y
				if top2 <= bottom + 0.03 and top2 > support:
					support = top2
		for o in list:
			if o == g:
				continue
			for pb in o.parts:
				var ob: AABB = pb
				var top: = ob.end.y
				if top > bottom + 0.03 or top < support:
					continue
				if c.x >= ob.position.x and c.x <= ob.end.x and c.z >= ob.position.z and c.z <= ob.end.z:
					support = top
		var gap: = bottom - support
		if gap > 0.04 and bottom < 6.0 and g.node.scene_file_path != "":
			n_float += 1
			print("FLOAT gap=%.2f bottom=%.2f at (%.1f, %.1f, %.1f) size=(%.2f,%.2f,%.2f) %s" % [gap, bottom, c.x, c.y, c.z, bb.size.x, bb.size.y, bb.size.z, String(g.node.name) + " <" + g.node.scene_file_path.get_file() + ">"])
	print("FLOATCHECK groups=%d flagged=%d" % [list.size(), n_float])
