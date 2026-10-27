extends Node3D
## v1.0 — os negócios no mapa (sorveteria, aluguel, escolinha de surfe, food truck, lojinha) e a barreira da Prainha do Oeste.
## Cada negócio comprado (Core.prog.biz) ganha a montagem com modelos do Blender (tools/gen_business.py), placa com o nome e um
## balcão interativo que abre o minijogo (scripts/minigame.gd). Criado por world.gd.

const B_: = preload("res://scripts/build.gd")
var world: Node3D
var built: = {}          # id -> Node3D
var prainha: Node3D      # barreira enquanto o capítulo "prainha" não termina
var _rng: = RandomNumberGenerator.new()

func setup(w: Node3D) -> void:
	world = w
	_rng.seed = 77
	for id in PD.BUSINESSES:
		_refresh(id)
	_refresh_prainha()
	Core.prog.biz_changed.connect(_refresh)
	Core.prog.chapters_changed.connect(_refresh_prainha)
	Core.expansion_bought.connect(func(_e): for id in PD.BUSINESSES: _refresh(id))

func _refresh(id: String) -> void:
	if id == "" or not PD.BUSINESSES.has(id):
		for k in PD.BUSINESSES:
			_refresh(k)
		return
	var own: bool = Core.prog.owns(id)
	if own and not built.has(id):
		built[id] = _build(id)
	elif not own and built.has(id):
		built[id].queue_free()
		built.erase(id)

func _build(id: String) -> Node3D:
	var b: Dictionary = PD.BUSINESSES[id]
	var root: = Node3D.new()
	root.name = "Biz_" + id
	root.position = b.pos
	root.rotation.y = float(b.rot)
	add_child(root)
	var tint: Color = b.tint
	var counter: = Vector3(0, 0, 1.2)   # ponto do balcão (local), frente = +Z
	var sign_pos: = Vector3(0, 2.6, 0.9)
	match id:
		"sorveteria":
			Real.place(root, "g:biz_gelato", Vector3.ZERO, -1.0, 0.0, Color.WHITE, 0.0, false)
			Real.tint_named(root, tint)
			Real.place(root, "g:cooler_box", Vector3(1.4, 0, 0.1), -1.0, 0.3)
			counter = Vector3(0, 0, 0.9)
			sign_pos = Vector3(0, 3.0, 0.0)
		"aluguel":
			Real.place(root, "g:biz_booth", Vector3.ZERO, -1.0, 0.0, Color.WHITE, 0.0, false)
			Real.tint_named(root, tint)
			Real.place(root, "g:biz_kayak_rack", Vector3(0.0, 0, -2.5), -1.0, 0.0)
			Real.place(root, "g:biz_board_rack", Vector3(2.9, 0, 0.3), -1.0, PI * 0.5)
			_boards(root, Vector3(2.9, 0, 0.3), PI * 0.5)
			Real.place(root, "g:cooler_box", Vector3(1.0, 1.07, 0.55), -1.0, 0.2)
		"surfe":
			Real.place(root, "g:biz_canopy", Vector3.ZERO, -1.0, 0.0, Color.WHITE, 0.0, false)
			Real.tint_named(root, tint)
			Real.place(root, "g:biz_board_rack", Vector3(0, 0, -0.9), -1.0, 0.0)
			_boards(root, Vector3(0, 0, -0.9), 0.0)
			# pranchas deitadas na areia para a aula
			for k in 4:
				var piv: = Node3D.new()
				piv.position = Vector3(-4.8 + k * 2.0, 0.04, 4.0)
				root.add_child(piv)
				Real.place(piv, "g:surfboard", Vector3.ZERO, 0.0, 0.0, [Color(1, 0.5, 0.3), Color(0.3, 0.7, 1), Color(1, 0.85, 0.3), Color(0.5, 0.9, 0.5)][k], 2.0)
			counter = Vector3(0, 0, 1.4)
			sign_pos = Vector3(0, 2.75, 1.55)
		"food_truck":
			Real.place(root, "g:biz_food_truck", Vector3.ZERO, -1.0, 0.0, Color.WHITE, 0.0, false)
			Real.tint_named(root, tint)
			# estacionado na rua principal, janela virada para a calçada (+Z)
			counter = Vector3(-0.8, 0, 1.9)
			sign_pos = Vector3(-0.3, 3.15, 0.0)
		"souvenir":
			Real.place(root, "g:biz_booth", Vector3.ZERO, -1.0, 0.0, Color.WHITE, 0.0, false)
			Real.tint_named(root, tint)
			Real.place(root, "g:biz_souvenir", Vector3(0.2, 0, 1.6), -1.0, 0.0)
			counter = Vector3(-1.7, 0, 1.3)
	var nm: = tr(str(b.name))
	var l: = B_.label(root, nm, sign_pos, 54, Color(1, 0.98, 0.9), Color(0.1, 0.08, 0.05, 0.9))
	l.double_sided = true
	l.width = 560
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	# balcão interativo
	var it: = Interactable.new()
	var cs: = CollisionShape3D.new()
	var sh: = BoxShape3D.new()
	sh.size = Vector3(1.6, 1.4, 0.8)
	cs.shape = sh
	it.add_child(cs)
	it.position = counter + Vector3(0, 0.8, 0)
	root.add_child(it)
	it.prompt_fn = func() -> String:
		if not Core.prog.biz_open(id):
			var o: Array = PD.BUSINESSES[id].open
			return tr("%s: fechado (abre %02dh–%02dh)") % [nm, int(o[0]), int(o[1])]
		if Core.prog.can_play(id):
			return tr("%s Atender no balcão: %s") % [Quality.key_name("interact"), tr(str(PD.BUSINESSES[id].game))]
		return tr("%s: rendendo %s/h · volte na próxima hora para atender") % [nm, Core.fmt_money(Core.prog.biz_rate(id))]
	it.action_fn = func() -> void:
		if Core.prog.can_play(id):
			var mg: CanvasLayer = load("res://scripts/minigame.gd").new()
			get_tree().root.add_child(mg)
			mg.start(id)
	# bloqueio para os pedestres não atravessarem
	if world.get("block_rects") != null:
		var half: = Vector2(3.0, 2.0) if id != "food_truck" else Vector2(3.0, 1.4)
		var c: = Vector2(root.position.x, root.position.z)
		var ext: = Vector2(absf(cos(root.rotation.y)) * half.x + absf(sin(root.rotation.y)) * half.y, absf(sin(root.rotation.y)) * half.x + absf(cos(root.rotation.y)) * half.y)
		world.block_rects.append(Rect2(c - ext, ext * 2.0))
	return root

## Pranchas em pé nos encaixes do suporte (5 de cada lado, a cada 0,36 m).
func _boards(root: Node3D, at: Vector3, rot: float) -> void:
	var cols: = [Color(1, 0.45, 0.3), Color(0.25, 0.65, 1), Color(1, 0.85, 0.25), Color(0.45, 0.85, 0.5), Color(0.95, 0.95, 0.95)]
	for side in [-1, 1]:
		for k in 5:
			var x: = -0.72 + k * 0.36
			var local: = Vector3(x, 0.1, side * 0.42)
			var p: = at + local.rotated(Vector3.UP, rot)
			var piv: = Node3D.new()
			piv.position = p
			piv.rotation = Vector3(0, rot, 0)
			root.add_child(piv)
			var inner: = Node3D.new()
			inner.rotation = Vector3(-side * 0.26, 0, 0)
			piv.add_child(inner)
			var h: = Real.place(inner, "g:surfboard", Vector3(0, 1.0, 0), 0.0, 0.0, cols[(k + (side + 1)) % cols.size()], 2.0)
			if h:
				h.rotation = Vector3(-PI * 0.5, 0, PI * 0.5)

# ------------------------------------------------------------------ Prainha do Oeste
func _refresh_prainha() -> void:
	var done: bool = Core.prog.chapter_done("prainha")
	if done and prainha:
		prainha.queue_free()
		prainha = null
	elif not done and prainha == null:
		prainha = Node3D.new()
		prainha.name = "PrainhaBarreira"
		add_child(prainha)
		var x: = -37.0
		for k in 5:
			Real.place(prainha, "g:biz_barrier", Vector3(x, 0, -29.0 + k * 3.6), -1.0, PI * 0.5 + (0.08 if k % 2 else -0.06))
		var l: = B_.label(prainha, tr("Trilha da Prainha do Oeste fechada\nFale com o Padre Tomé (celular > Vila)"), Vector3(x, 1.9, -22.0), 48, Color(1, 0.95, 0.6), Color(0.15, 0.08, 0.0, 0.9), PI * 0.5)
		l.double_sided = true
		var wall: = StaticBody3D.new()
		var cs: = CollisionShape3D.new()
		var sh: = BoxShape3D.new()
		sh.size = Vector3(0.6, 3.0, 19.0)
		cs.shape = sh
		wall.add_child(cs)
		wall.position = Vector3(x, 1.5, -21.0)
		prainha.add_child(wall)
