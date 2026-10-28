extends Node3D
## v1.0 — fase final: Grand Hotel Maré Alta 5★ (expansão "grand_hotel"). Fica no terreno a sudoeste do resort
## (x -46..4, z 23..75, reservado sem palmeiras/vegetação desde o começo). Antes da compra: cerca de obra e placa.
## Depois: prédio de 5 andares (g:hotel_tower), terraço elevado (1,2 m) com piscina, tobogã (g:water_slide), restaurante
## (g:hotel_restaurant), academia (g:hotel_gym + aparelhos), bar molhado, espreguiçadeiras, palmeiras e hóspedes animados.

const B_: = preload("res://scripts/build.gd")
const GuestScript: = preload("res://scripts/guest.gd")
const TOWER: = Vector3(-21.0, 0.0, 63.0)
const TER_MIN: = Vector2(-44.0, 26.0)     # terraço (x, z)
const TER_MAX: = Vector2(-4.0, 50.0)
const TER_Y: = 1.2
const POOL_MIN: = Vector2(-35.0, 31.0)
const POOL_MAX: = Vector2(-17.0, 41.0)
const WATER_Y: = 1.05

var world: Node3D
var built: Node3D
var lot: Node3D
var _rng: = RandomNumberGenerator.new()
var _npcs: Array = []

func setup(w: Node3D) -> void:
	world = w
	_rng.seed = 505
	_refresh()
	Core.expansion_bought.connect(func(_id): _refresh())

func _refresh() -> void:
	var own: bool = Core.has("grand_hotel")
	if own and built == null:
		if lot:
			lot.queue_free()
			lot = null
		built = _build()
	elif not own and lot == null and built == null:
		lot = _build_lot()

# ------------------------------------------------------------------ terreno à venda
func _build_lot() -> Node3D:
	var n: = Node3D.new()
	n.name = "HotelLot"
	add_child(n)
	for k in 6:
		Real.place(n, "g:biz_barrier", Vector3(-36.0 + k * 6.0, 0.0, 24.5), -1.0, 0.0)
	Real.place(n, "g:signpost_post", Vector3(-22.0, 0.0, 23.2), 2.6, 0.0)
	var l: = B_.label(n, tr("Futuro Grand Hotel Maré Alta 5★\n(celular > Hotel 5★)"), Vector3(-22.0, 2.9, 23.0), 60, Color(1, 0.92, 0.55), Color(0.2, 0.1, 0.0, 0.9))
	l.double_sided = true
	return n

# ------------------------------------------------------------------ hotel construído
func _build() -> Node3D:
	# Some helpers append loungers/umbrellas directly to World. Keep their
	# ownership when exporting the full scene to another engine.
	var world_children_before: Array = world.get_children()
	var root: = Node3D.new()
	root.name = "GrandHotel"
	add_child(root)
	# Vidros neutros compartilham o material transparente das janelas da vila.
	var vm = world.get("VM")
	var glow: Material = vm.get("window_glass") if vm is Dictionary and vm.has("window_glass") else StandardMaterial3D.new()
	Real.place_glow(root, "g:hotel_tower", TOWER, -1.0, PI, glow)
	B_.wall(root, Vector3(32.4, 20.0, 13.4), TOWER + Vector3(0, 10.0, 0))
	B_.wall(root, Vector3(10.0, 0.5, 7.0), TOWER + Vector3(0, 4.7, 9.7))
	var sign: = B_.label(root, "MARÉ ALTA ★★★★★", TOWER + Vector3(0, 21.65, -6.35), 220, Color(1.0, 0.92, 0.6), Color(0.25, 0.12, 0.02, 1), PI)
	sign.double_sided = false
	sign.pixel_size = 0.012
	var lob: = B_.label(root, tr("LOBBY · SPA"), TOWER + Vector3(0, 4.15, -9.9), 90, Color(0.3, 0.22, 0.12), Color(1, 1, 1, 0.0), PI)
	lob.double_sided = true
	_terrace(root)
	_pool(root)
	# tobogã: torre em x -40,5, a calha termina dentro da piscina (x ≈ -34,3)
	Real.place(root, "g:water_slide", Vector3(-40.5, TER_Y, 36.0), -1.0, 0.0, Color.WHITE, 0.0, false)
	Real.tint_named(root.get_child(root.get_child_count() - 1), Color(0.15, 0.55, 0.95))
	B_.wall(root, Vector3(2.4, 8.0, 2.4), Vector3(-40.5, TER_Y + 4.0, 36.0))
	# restaurante (frente para a piscina, -X) com mesas Poly Haven
	Real.place(root, "g:hotel_restaurant", Vector3(-9.0, TER_Y, 43.0), -1.0, -PI * 0.5, Color.WHITE, 0.0, false)
	for i in 3:
		for j in 2:
			B_.model(root, "outdoor_table_chair_set_01", Vector3(-12.0 + j * 2.8, TER_Y + 0.35, 38.6 + i * 3.4), j * 0.4, 1.0)
	B_.label(root, tr("RESTAURANTE"), Vector3(-13.9, TER_Y + 3.5, 43.0), 80, Color(1, 0.95, 0.85), Color(0.2, 0.1, 0.05, 0.9), -PI * 0.5).double_sided = true
	# academia (frente para o mar, -Z) e aparelhos
	var gp: = Vector3(-11.0, TER_Y, 30.0)
	Real.place(root, "g:hotel_gym", gp, -1.0, PI, Color.WHITE, 0.0, false)
	Real.place(root, "g:gym_treadmill", gp + Vector3(-3.0, 0.28, -1.0), -1.0, PI)
	Real.place(root, "g:gym_treadmill", gp + Vector3(-1.5, 0.28, -1.0), -1.0, PI)
	Real.place(root, "g:gym_bike", gp + Vector3(0.3, 0.28, -1.2), -1.0, PI)
	Real.place(root, "g:gym_bike", gp + Vector3(1.5, 0.28, -1.2), -1.0, PI)
	Real.place(root, "g:gym_bench", gp + Vector3(3.0, 0.28, 1.0), -1.0, PI * 0.5)
	Real.place(root, "g:gym_dumbbells", gp + Vector3(-2.0, 0.28, 2.6), -1.0, 0.0)
	B_.label(root, tr("ACADEMIA"), gp + Vector3(0, 4.25, -3.75), 80, Color(1, 1, 1), Color(0.1, 0.1, 0.15, 0.9), PI).double_sided = true
	B_.wall(root, Vector3(10.4, 4.0, 7.4), gp + Vector3(0, 2.0, 0))
	# bar molhado na borda sul da piscina
	var bar_p: = Vector3(-26.0, TER_Y, 46.6)
	Real.place(root, "g:biz_booth", bar_p, -1.0, PI, Color.WHITE, 0.0, false)
	Real.tint_named(root.get_child(root.get_child_count() - 1), Color(0.2, 0.6, 0.65))
	B_.label(root, tr("BAR DA PISCINA"), bar_p + Vector3(0, 2.25, -0.86), 64, Color(1, 1, 1), Color(0.05, 0.2, 0.25, 0.9), PI).double_sided = true
	# espreguiçadeiras com guarda-sol nos dois lados longos
	for k in 6:
		var x: = -33.5 + k * 3.0
		# cabeceira (encosto) longe da piscina: quem deita olha para a água
		world._lounger(Vector3(x, TER_Y, 28.6), 0.0)
		world._lounger(Vector3(x, TER_Y, 43.6), PI)
		if k % 2 == 0:
			world._umbrella(Vector3(x + 1.5, TER_Y, 28.2), 1.35, [Color(0.95, 0.95, 0.9), Color(0.12, 0.55, 0.58)][(k / 2) % 2])
			world._umbrella(Vector3(x + 1.5, TER_Y, 44.0), 1.35, [Color(0.12, 0.55, 0.58), Color(0.95, 0.95, 0.9)][(k / 2) % 2])
	# palmeiras em vasos ao redor do terraço e na frente do prédio
	for p in [Vector2(-43, 27), Vector2(-43, 49), Vector2(-5, 27), Vector2(-16, 49), Vector2(-36, 49), Vector2(-30, 53), Vector2(-12, 53), Vector2(-2, 56), Vector2(-40, 56)]:
		var y: = TER_Y if (p.x >= TER_MIN.x and p.x <= TER_MAX.x and p.y >= TER_MIN.y and p.y <= TER_MAX.y) else 0.0
		Palm.spawn(root, Vector3(p.x, y, p.y), int(absf(p.x * 13.0 + p.y)))
	# noite: tochas tiki em volta da piscina, luzes subaquáticas e luz quente no bar e no restaurante
	var D_: = preload("res://scripts/details.gd")
	for tp in [Vector3(-36.2, TER_Y, 30.2), Vector3(-36.2, TER_Y, 41.8), Vector3(-17.4, TER_Y, 30.3), Vector3(-15.8, TER_Y, 41.8), Vector3(-26.0, TER_Y, 30.0), Vector3(-30.5, TER_Y, 45.5), Vector3(-21.5, TER_Y, 45.5)]:
		var tl: OmniLight3D = D_.tiki_torch(root, tp)
		if world.get("lanterns") != null:
			world.lanterns.append([tl, null, 1.6, false])
	for k in 4:
		var lx: = lerpf(POOL_MIN.x + 2.0, POOL_MAX.x - 2.0, k / 3.0)
		for lz in [POOL_MIN.y + 0.12, POOL_MAX.y - 0.12]:
			var pl: = Real.place_glow(root, "g:pool_light", Vector3(lx, WATER_Y - 0.55, lz), -1.0, 0.0, P.glow(Color(0.6, 0.95, 1.0), 2.0))
			if pl != null:
				pl.rotation.x = PI * 0.5 if lz < (POOL_MIN.y + POOL_MAX.y) * 0.5 else -PI * 0.5
	for lp in [Vector3(-26.0, TER_Y + 2.3, 46.4), Vector3(-9.0, TER_Y + 3.0, 43.0), Vector3(-9.0, TER_Y + 3.0, 39.0), Vector3(-9.0, TER_Y + 3.0, 47.0)]:
		var ol: = OmniLight3D.new()
		ol.position = lp
		ol.omni_range = 7.0
		ol.light_color = Color(1.0, 0.75, 0.45)
		ol.light_energy = 0.0
		root.add_child(ol)
		if world.get("lanterns") != null:
			world.lanterns.append([ol, null, 1.4, false])
	_people(root)
	if world.get("block_rects") != null:
		world.block_rects.append(Rect2(TER_MIN.x - 0.5, TER_MIN.y - 0.5, TER_MAX.x - TER_MIN.x + 1.0, TER_MAX.y - TER_MIN.y + 1.0))
		world.block_rects.append(Rect2(TOWER.x - 16.5, TOWER.z - 13.0, 33.0, 20.0))
	Core.toast.emit(tr("O Grand Hotel Maré Alta 5★ abriu as portas! Ele rende toda noite (celular > Hotel 5★)."), "good")
	for child in world.get_children():
		if not world_children_before.has(child):
			child.set_meta("ue_region", "grand_hotel")
	return root

## Terraço elevado de pedra com degraus ao norte e ao leste (acesso pelo resort), com borda e muro de contenção.
func _terrace(root: Node3D) -> void:
	var stone: Material = world.M.stone if world.get("M") != null else B_.flat(Color(0.85, 0.82, 0.76), 0.8)
	var tile: Material = world.M.terra_tiles if world.get("M") != null else stone
	var coping: = B_.flat(Color(0.93, 0.9, 0.84), 0.6)
	var c: = (TER_MIN + TER_MAX) * 0.5
	var sz: = TER_MAX - TER_MIN
	# 4 blocos em volta do buraco da piscina (o terraço é oco onde fica a piscina)
	var h: = TER_Y
	var pairs: = [
		[Vector2(TER_MIN.x, TER_MIN.y), Vector2(TER_MAX.x, POOL_MIN.y)],
		[Vector2(TER_MIN.x, POOL_MAX.y), Vector2(TER_MAX.x, TER_MAX.y)],
		[Vector2(TER_MIN.x, POOL_MIN.y), Vector2(POOL_MIN.x, POOL_MAX.y)],
		[Vector2(POOL_MAX.x, POOL_MIN.y), Vector2(TER_MAX.x, POOL_MAX.y)],
	]
	for pr in pairs:
		var a: Vector2 = pr[0]
		var b: Vector2 = pr[1]
		var mid: = (a + b) * 0.5
		B_.box(root, Vector3(b.x - a.x, h, b.y - a.y), Vector3(mid.x, h * 0.5, mid.y), tile, true)
	# borda de pedra em volta do terraço
	for side in 4:
		var horiz: = side < 2
		var L: float = sz.x if horiz else sz.y
		var pos: = Vector3(c.x, h + 0.08, TER_MIN.y if side == 0 else TER_MAX.y) if horiz else Vector3(TER_MIN.x if side == 2 else TER_MAX.x, h + 0.08, c.y)
		B_.box(root, Vector3(L + 0.3, 0.16, 0.3) if horiz else Vector3(0.3, 0.16, L + 0.3), pos, coping)
	# muro de contenção revestido (faces externas)
	B_.box(root, Vector3(sz.x + 0.2, h, 0.2), Vector3(c.x, h * 0.5, TER_MIN.y - 0.05), stone)
	B_.box(root, Vector3(sz.x + 0.2, h, 0.2), Vector3(c.x, h * 0.5, TER_MAX.y + 0.05), stone)
	B_.box(root, Vector3(0.2, h, sz.y), Vector3(TER_MIN.x - 0.05, h * 0.5, c.y), stone)
	B_.box(root, Vector3(0.2, h, sz.y), Vector3(TER_MAX.x + 0.05, h * 0.5, c.y), stone)
	# escadarias: norte (centro) e leste (vindo do caminho do resort) e sul (para o hotel)
	for k in 8:
		var y: = (k + 1) * h / 8.0
		B_.box(root, Vector3(5.0, y, 0.34), Vector3(-26.0, y * 0.5, TER_MIN.y - 0.17 - (7 - k) * 0.34), stone)
		B_.box(root, Vector3(0.34, y, 3.0), Vector3(TER_MAX.x + 0.17 + (7 - k) * 0.34, y * 0.5, 34.0), stone)
		B_.box(root, Vector3(4.0, y, 0.34), Vector3(-21.0, y * 0.5, TER_MAX.y + 0.17 + (7 - k) * 0.34), stone)
	# colisão das escadas = rampa invisível (o jogador não sobe degrau de 15 cm sozinho)
	_ramp(root, Vector3(-26.0, 0.0, TER_MIN.y - 2.72), Vector3(-26.0, h, TER_MIN.y), 5.0)
	_ramp(root, Vector3(TER_MAX.x + 2.72, 0.0, 34.0), Vector3(TER_MAX.x, h, 34.0), 3.0)
	_ramp(root, Vector3(-21.0, 0.0, TER_MAX.y + 2.72), Vector3(-21.0, h, TER_MAX.y), 4.0)
	# caminho de pedra do resort até a escada leste
	world._strip(Vector2(0.0, 27.0), Vector2(-1.0, 34.0), 2.4, stone, 0.03)

func _ramp(root: Node3D, bottom: Vector3, top: Vector3, width: float) -> void:
	var dir: = top - bottom
	var zx: = dir.normalized()
	var xx: = Vector3.UP.cross(zx).normalized()
	var yy: = zx.cross(xx).normalized()
	var sb: = StaticBody3D.new()
	var cs: = CollisionShape3D.new()
	var sh: = BoxShape3D.new()
	sh.size = Vector3(width, 0.2, dir.length() + 0.3)
	cs.shape = sh
	sb.add_child(cs)
	sb.transform = Transform3D(Basis(xx, yy, zx), (top + bottom) * 0.5 - yy * 0.1)
	root.add_child(sb)

func _pool(root: Node3D) -> void:
	var wx: = POOL_MAX.x - POOL_MIN.x
	var wz: = POOL_MAX.y - POOL_MIN.y
	var c: = Vector3((POOL_MIN.x + POOL_MAX.x) * 0.5, 0, (POOL_MIN.y + POOL_MAX.y) * 0.5)
	var basin: Material = world.M.azulejo if world.get("M") != null else B_.flat(Color(0.4, 0.7, 0.9), 0.4)
	if Quality.hd:
		var pf: = ShaderMaterial.new()
		pf.shader = load("res://shaders/pool_floor.gdshader")
		pf.set_shader_parameter("albedo_tex", B_.tex("blue_floor_tiles_01"))
		pf.set_shader_parameter("normal_tex", B_.nor("blue_floor_tiles_01"))
		basin = pf
	var depth: = TER_Y - 0.08
	B_.box(root, Vector3(wx, 0.1, wz), Vector3(c.x, 0.08, c.z), basin)
	B_.box(root, Vector3(wx, depth, 0.1), Vector3(c.x, 0.08 + depth * 0.5, POOL_MIN.y + 0.05), basin)
	B_.box(root, Vector3(wx, depth, 0.1), Vector3(c.x, 0.08 + depth * 0.5, POOL_MAX.y - 0.05), basin)
	B_.box(root, Vector3(0.1, depth, wz), Vector3(POOL_MIN.x + 0.05, 0.08 + depth * 0.5, c.z), basin)
	B_.box(root, Vector3(0.1, depth, wz), Vector3(POOL_MAX.x - 0.05, 0.08 + depth * 0.5, c.z), basin)
	var water: = MeshInstance3D.new()
	var pm: = PlaneMesh.new()
	pm.size = Vector2(wx - 0.1, wz - 0.1)
	pm.subdivide_width = 30
	pm.subdivide_depth = 16
	water.mesh = pm
	water.position = Vector3(c.x, WATER_Y, c.z)
	var wm: = ShaderMaterial.new()
	wm.shader = load("res://shaders/pool_hd.gdshader" if Quality.hd else "res://shaders/pool.gdshader")
	water.material_override = wm
	root.add_child(water)
	# o jogador não cai na piscina (como na piscina do resort)
	B_.wall(root, Vector3(wx, 2, 0.2), Vector3(c.x, TER_Y + 1, POOL_MIN.y))
	B_.wall(root, Vector3(wx, 2, 0.2), Vector3(c.x, TER_Y + 1, POOL_MAX.y))
	B_.wall(root, Vector3(0.2, 2, wz), Vector3(POOL_MIN.x, TER_Y + 1, c.z))
	B_.wall(root, Vector3(0.2, 2, wz), Vector3(POOL_MAX.x, TER_Y + 1, c.z))
	B_.model(root, "lifebuoy", Vector3(POOL_MAX.x + 0.6, TER_Y + 0.75, POOL_MAX.y + 0.42), 0.0, 1.0)   # boia pendurada em pé no mastro
	Real.place(root, "g:bamboo_pole", Vector3(POOL_MAX.x + 0.6, TER_Y, POOL_MAX.y + 0.55), 1.4, 0.0)

# ------------------------------------------------------------------ hóspedes
func _npc(parent: Node, pos: Vector3, rot: float, anim: String) -> Node3D:
	var g: = Node3D.new()
	g.set_script(GuestScript)
	parent.add_child(g)
	g.setup(9000 + _rng.randi() % 3000, _rng)
	g.position = pos
	g.rotation.y = rot
	g.call_deferred("play", anim)
	_npcs.append(g)
	return g

func _people(root: Node3D) -> void:
	var n_lounge: = 6 if Quality.hd else 3
	for k in n_lounge:
		var x: = -33.5 + (k % 6) * 3.0
		var north: = k % 2 == 0
		var p: = Vector3(x, TER_Y + 0.3, 28.6 if north else 43.6)
		_npc(root, p, (0.0 if north else PI) + PI, "Sitting_Idle_Loop")
	var n_swim: = 5 if Quality.hd else 2
	for k in n_swim:
		var p2: = Vector3(_rng.randf_range(POOL_MIN.x + 1.5, POOL_MAX.x - 1.5), WATER_Y - 0.28, _rng.randf_range(POOL_MIN.y + 1.2, POOL_MAX.y - 1.2))
		_npc(root, p2, _rng.randf() * TAU, "Swim_Idle_Loop")
	# academia: dois correndo na esteira, um na bike (em pé, animação de corrida)
	var gp: = Vector3(-11.0, TER_Y + 0.28 + 0.25, 30.0)
	_npc(root, gp + Vector3(-3.0, 0, -0.9), 0.0, "Jog_Fwd_Loop")   # de frente para o painel da esteira (-Z)
	if Quality.hd:
		_npc(root, gp + Vector3(-1.5, 0, -0.9), 0.0, "Jog_Fwd_Loop")
	# restaurante: casais conversando nas mesas
	for i in (3 if Quality.hd else 1):
		_npc(root, Vector3(-11.4, TER_Y + 0.35 + 0.1, 38.6 + i * 3.4), PI * 0.5, "Sitting_Talking_Loop").set_meta("anim_kind", "keep")
	# bar da piscina: dois em pé no balcão
	_npc(root, Vector3(-26.6, TER_Y, 45.2), PI, "Idle_Talking_Loop").set_meta("anim_kind", "keep")   # de frente para o balcão (+Z)
	_npc(root, Vector3(-25.2, TER_Y, 45.1), PI - 0.2, "Idle_Talking_Loop").set_meta("anim_kind", "keep")

func _process(_d: float) -> void:
	if built == null:
		return
	# à noite o pessoal sai da piscina e das espreguiçadeiras (fica só o restaurante e o bar)
	var night: bool = Core.minutes >= 20.0 * 60.0 or Core.minutes < 7.0 * 60.0
	for g in _npcs:
		if is_instance_valid(g):
			var a: String = g.get_meta("anim_kind", "")
			(g as Node3D).visible = not night or a == "keep"
