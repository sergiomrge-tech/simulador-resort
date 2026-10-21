extends Node3D
## Operação do quiosque: estoque pronto separado de ingredientes e contas a receber.
const Dishes = preload("res://scripts/dish_presentation.gd")
var main
var stations: Dictionary = {}
var products: Node3D
var door: Node3D
var hand: Node3D
var actors: Dictionary = {}
var dirt: Dictionary = {}
var waiter_target: WeakRef
var waiter_phase := ""
var waiter_role_active := ""
var cleaner_seat := -1
var cleaner_time := 0.0
var pulse := 0.0
var _display_key := ""
var _hand_key := "?"

func _ready() -> void:
	name = "KioskOperations"
	_build()
	Core.company_changed.connect(sync_company)
	sync_company()

func center() -> Vector3:
	return main.world.KIOSK_C

func _build() -> void:
	var c: Vector3 = center()
	var wood: Material = main.world.M.post
	# Anexo externo: pode ser alcançado contornando a lateral, sem atravessar o balcão.
	for x in [-2.1, 2.1]:
		B.cyl(self, 0.055, 0.055, 2.25, c + Vector3(x, 1.13, -4.5), wood)
	B.box(self, Vector3(4.4, 0.12, 1.8), c + Vector3(0, 2.3, -4.35), main.world.M.thatch)
	_station("bebidas", "Geladeira · bebidas prontas", c + Vector3(-1.4, 0.1, -4.0), Vector3(1.0, 1.9, 0.65))
	_station("pratos", "Armário · pratos e porções", c + Vector3(0, 0.1, -4.0), Vector3(1.15, 1.35, 0.65))
	_station("cozinha", "Cozinha · preparar pedidos", c + Vector3(1.4, 0.1, -4.0), Vector3(1.1, 0.95, 0.65))
	Real.place(self, "g:service_fridge", stations.bebidas.position, -1.0, PI)
	Real.place(self, "g:service_food_cabinet", stations.pratos.position, -1.0, PI)
	B.box(self, Vector3(1.1, 0.1, 0.65), stations.cozinha.position + Vector3(0, 0.9, 0), wood)
	for dx in [-0.45, 0.45]:
		B.box(self, Vector3(0.065, 0.9, 0.5), stations.cozinha.position + Vector3(dx, 0.45, 0), wood)
	door = Node3D.new()
	add_child(door)
	door.position = stations.bebidas.position + Vector3(0.475, 0, -0.34)
	door.rotation.y = PI
	Real.place(door, "g:service_fridge_door", Vector3.ZERO, -1.0, 0, Color.WHITE, 0, false)
	var register_pos: Vector3 = c + Vector3(1.3, 1.28, 1.8)
	Real.place(self, "g:service_register", register_pos, -1.0)
	_interaction(self, register_pos + Vector3(0, 0.12, 0), Vector3(0.4, 0.3, 0.4), _register_prompt, collect_payments)
	products = Node3D.new()
	add_child(products)
	hand = Node3D.new()
	main.player.cam.add_child(hand)
	hand.position = Vector3(0.32, -0.32, -0.65)

func _interaction(parent: Node, pos: Vector3, size: Vector3, prompt: Callable, action: Callable) -> Interactable:
	var item := Interactable.new()
	parent.add_child(item)
	item.position = pos
	item.prompt_fn = prompt
	item.action_fn = action
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	collision.shape = shape
	item.add_child(collision)
	return item

func _station(kind: String, title: String, pos: Vector3, size: Vector3) -> void:
	var node := Node3D.new()
	add_child(node)
	node.position = pos
	stations[kind] = node
	var label := B.label(node, title, Vector3(0, size.y + 0.16, -0.36), 27, Color(1, 0.96, 0.8), Color(0, 0, 0, 0.8), PI)
	label.pixel_size = 0.003
	_interaction(node, Vector3(0, size.y * 0.5, 0), size, station_prompt.bind(kind, title), open_station.bind(kind))

func station_prompt(_kind: String, title: String) -> String:
	return title if Core.company_enabled() else ""

func can_access(kind: String) -> bool:
	return Core.company_enabled() and stations.has(kind) and main.player.global_position.distance_to(stations[kind].global_position) < 2.8

func open_station(kind: String) -> void:
	if not can_access(kind):
		return
	Core.service_station = kind
	if kind == "bebidas":
		door.rotation.y = PI - deg_to_rad(100)
	main.hud.phone.open("servico")
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func finish_station() -> void:
	main.hud.toggle_shop()
	door.rotation.y = PI

func _register_prompt() -> String:
	return "Caixa · receber %d contas" % Core.company.receivables.size() if Core.company_enabled() else ""

func collect_payments() -> void:
	var amount: int = Core.collect_company_payments()
	Core.toast.emit("Recebido: " + Core.fmt_money(amount), "good")

func customer_prompt(ref: WeakRef) -> String:
	var g = ref.get_ref()
	if not Core.company_enabled() or not is_instance_valid(g) or g.is_queued_for_deletion() or g.state != "kwait":
		return ""
	var id: String = str(Core.company.carry)
	if id in main.village._remaining(g):
		return "Entregar " + tr(str(Economy.dish(id).name))
	return "Pedido: " + main.village._order_text(g)

func deliver(ref: WeakRef) -> bool:
	var g = ref.get_ref()
	if not Core.company_enabled() or not is_instance_valid(g) or g.is_queued_for_deletion() or g.state != "kwait":
		return false
	if str(Core.company.carry) not in main.village._remaining(g):
		Core.toast.emit("Leve um dos itens pedidos por este cliente.", "bad")
		return false
	return main.village._deliver_item(g, str(Core.company.carry), true)

func mark_dirty(g) -> void:
	var index: int = main.world.kiosk_spots.find(g.spot)
	if index >= 0 and index not in Core.company.dirty_seats:
		Core.company.dirty_seats.append(index)
		Core.company_changed.emit()

func clean_prompt(index: int) -> String:
	return "Recolher pratos e limpar o lugar" if Core.company_enabled() and index in Core.company.dirty_seats else ""

func clean(index: int) -> void:
	Core.clean_company_seat(index)

func sync_company() -> void:
	visible = Core.company_enabled()
	hand.visible = visible
	for role in actors:
		actors[role].visible = visible and Core.prog.staff_eff(role) > 0
		actors[role].set_process(actors[role].visible)
	var key: String = JSON.stringify(Core.company.ready)
	if key != _display_key:
		_display_key = key
		for child in products.get_children():
			products.remove_child(child)
			child.queue_free()
		var drink_slot := 0
		var food_slot := 0
		for id in Economy.KIOSK_MENU:
			if int(Core.company.ready.get(id, 0)) <= 0:
				continue
			var drink: bool = Dishes.is_drink(id)
			var slot: int = drink_slot if drink else food_slot
			var anchor: Node3D = stations.bebidas if drink else stations.pratos
			var root := Node3D.new()
			products.add_child(root)
			root.position = anchor.position + Vector3(-0.22 + (slot % 2) * 0.44, (0.315 if drink else 0.065) + floorf(float(slot) / 2.0) * (0.48 if drink else 0.35), 0)
			root.rotation.y = PI
			root.scale = Vector3.ONE * (0.7 if drink else 0.8)
			Dishes.build(root, id)
			if drink:
				drink_slot += 1
			else:
				food_slot += 1
	var held: String = str(Core.company.carry)
	if held != _hand_key:
		_hand_key = held
		for child in hand.get_children():
			hand.remove_child(child)
			child.queue_free()
		if held != "":
			Dishes.build(hand, held)
	for index in dirt.keys():
		if index not in Core.company.dirty_seats:
			dirt[index].queue_free()
			dirt.erase(index)
	for index in Core.company.dirty_seats:
		if dirt.has(index) or index >= main.world.kiosk_spots.size():
			continue
		var root := Node3D.new()
		add_child(root)
		root.position = main.world.kiosk_spots[index].serve_pos
		Real.place(root, "k:plate-dinner", Vector3.ZERO, 0.022)
		_interaction(root, Vector3(0, 0.1, 0), Vector3(0.5, 0.25, 0.5), clean_prompt.bind(index), clean.bind(index))
		dirt[index] = root

func _process(delta: float) -> void:
	if not Core.company_enabled() or not Core.in_game or Core.paused or get_tree().paused:
		return
	for g in main.village.customers:
		if is_instance_valid(g) and not g.has_meta("company_target"):
			var ref: WeakRef = weakref(g)
			_interaction(g, Vector3(0, 0.8, 0), Vector3(0.58, 1.3, 0.58), customer_prompt.bind(ref), deliver.bind(ref))
			g.set_meta("company_target", true)
	pulse -= delta
	if pulse > 0:
		return
	pulse = 0.25
	_staff_tick()

func _actor(role: String, pos: Vector3):
	if not actors.has(role):
		var g = main.village._make()
		g.position = pos
		g.state = "employee"
		g.go([])
		g.speed = 2.0
		B.label(g, str(Economy.STAFF[role].name), Vector3(0, 2.1, 0), 26, Color(0.9, 1, 1))
		actors[role] = g
	return actors[role]

func _staff_tick() -> void:
	var c: Vector3 = center()
	var waiter_role: String = "garcom" if Core.prog.staff_eff("garcom") > 0 else "atendente"
	if waiter_role != waiter_role_active:
		waiter_role_active = waiter_role
		waiter_phase = ""
		waiter_target = null
		for old_role in ["garcom", "atendente"]:
			if actors.has(old_role):
				_clear_tray(actors[old_role])
	for role in ["garcom", "atendente", "caixa", "cozinheiro", "limpeza"]:
		var active: bool = Core.prog.staff_eff(role) > 0 and main.village.kiosk_open()
		if actors.has(role):
			actors[role].visible = active
			actors[role].set_process(active)
		if not active:
			continue
		var pos: Vector3 = c + Vector3(1.4, 0.1, -5.3)
		if role == "caixa":
			pos = c + Vector3(1.25, 0.1, 1.15)
		elif role == "limpeza":
			pos = c + Vector3(-3.6, 0.1, 3.4)
		var g = _actor(role, pos)
		g.speed = 2.0 * Core.prog.staff_eff(role)
		if role == "caixa":
			if not Core.company.receivables.is_empty():
				Core.collect_company_payments()
		elif role == "cozinheiro" or (role == "atendente" and waiter_role == "garcom"):
			_cook()
		elif role == "limpeza":
			_cleaner(g)
		else:
			_waiter(g)

func _cook() -> void:
	if not Core.company.production.is_empty():
		return
	for g in main.village.waiting_customers():
		for id in main.village._remaining(g):
			if int(Core.company.ready.get(id, 0)) == 0 and Core.company.carry != id and Core.company.staff_carry != id and Core.prepare_company_dish(id):
				return
	for id in Core.kiosk_menu():
		if int(Core.company.ready.get(id, 0)) < 2 and Core.prepare_company_dish(id):
			return

func _waiter(g) -> void:
	if g.is_moving():
		return
	if waiter_phase == "deliver":
		var target = waiter_target.get_ref() if waiter_target != null else null
		if is_instance_valid(target) and not target.is_queued_for_deletion() and target.state == "kwait" and str(Core.company.staff_carry) in main.village._remaining(target) and g.position.distance_to(target.spot.approach) < 1.0:
			main.village._deliver_item(target, str(Core.company.staff_carry), true, true)
		waiter_phase = ""
		_clear_tray(g)
		g.play("Idle_Loop")
	# Return safely to the shelves before returning or taking an item.
	var pickup: Vector3 = center() + Vector3(0, 0.1, -5.3)
	if g.position.distance_to(pickup) > 0.5:
		g.go([center() + Vector3(3.8, 0.1, 3.5), center() + Vector3(3.8, 0.1, -5.3), pickup])
		return
	if Core.company.staff_carry != "":
		if not Core.return_company_staff_dish():
			return
	for target in main.village.waiting_customers():
		for id in main.village._remaining(target):
			if not Core.reserve_company_staff_dish(id):
				continue
			waiter_target = weakref(target)
			waiter_phase = "deliver"
			var tray := Node3D.new()
			tray.name = "StaffTray"
			g.add_child(tray)
			tray.position = Vector3(0, 1.0, 0.32)
			tray.scale = Vector3.ONE * 0.65
			Dishes.build(tray, id)
			g.go([center() + Vector3(3.8, 0.1, -5.3), center() + Vector3(3.8, 0.1, 3.5), target.spot.approach])
			return

func _cleaner(g) -> void:
	if g.is_moving():
		return
	if cleaner_seat >= 0:
		cleaner_time += pulse
		if cleaner_time < 2.0:
			return
		Core.clean_company_seat(cleaner_seat)
		cleaner_seat = -1
	if Core.company.dirty_seats.is_empty():
		return
	cleaner_seat = int(Core.company.dirty_seats[0])
	cleaner_time = 0.0
	if cleaner_seat < main.world.kiosk_spots.size():
		g.go([main.world.kiosk_spots[cleaner_seat].approach])

func _clear_tray(g) -> void:
	var tray = g.get_node_or_null("StaffTray")
	if tray != null:
		g.remove_child(tray)
		tray.queue_free()
