extends Node3D
## Operação do quiosque: estoque pronto separado de ingredientes e contas a receber.
const Dishes = preload("res://scripts/dish_presentation.gd")
var main
var stations: Dictionary = {}
var station_bodies: Array[Interactable] = []
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
var _production_key := ""
var menu_card: Label3D
var door_tween: Tween

func _ready() -> void:
	name = "KioskOperations"
	_build()
	Core.company_changed.connect(sync_company)
	Core.staff_changed.connect(sync_company)
	Core.stock_changed.connect(sync_company)
	Core.time_changed.connect(_update_work_lighting)
	sync_company()

func center() -> Vector3:
	return main.world.KIOSK_C

func _build() -> void:
	var c: Vector3 = center()
	# Três estações no mesmo piso do balcão. Entradas laterais de 1,2 m.
	_station("bebidas", "Geladeira", c + Vector3(-1.2, 0.1, -1.8), Vector3(0.95, 1.85, 0.62))
	_station("pratos", "Retirada de pratos", c + Vector3(0, 0.1, -1.8), Vector3(1.1, 1.3, 0.62))
	_station("cozinha", "Cozinha", c + Vector3(1.2, 0.1, -1.8), Vector3(1.1, 0.94, 0.65))
	Real.place(self, "g:service_fridge", stations.bebidas.position, -1.0)
	Real.place(self, "g:service_food_cabinet", stations.pratos.position, -1.0)
	Real.place(self, "g:kiosk_workbench", stations.cozinha.position, -1.0)
	door = Node3D.new()
	add_child(door)
	door.position = stations.bebidas.position + Vector3(-0.475, 0, 0.34)
	Real.place(door, "g:service_fridge_door", Vector3.ZERO, -1.0, 0, Color.WHITE, 0, false)
	for side in [-1.0, 1.0]:
		var label := B.label(self, "ENTRADA", c + Vector3(side * 2.42, 1.45, -0.75), 18, Color(1, 0.94, 0.75), Color(0.05, 0.12, 0.12), side * PI * 0.5)
		label.pixel_size = 0.0018
	Real.place(self, "g:kiosk_blender", c + Vector3(-2.0, 1.28, 0.25), -1.0)
	var register_pos: Vector3 = c + Vector3(1.3, 1.28, 1.8)
	Real.place(self, "g:service_register", register_pos, -1.0)
	_interaction(self, register_pos + Vector3(0, 0.12, 0), Vector3(0.4, 0.3, 0.4), _register_prompt, collect_payments)
	Real.place(self, "g:kiosk_counter_details", c + Vector3(0,1.28,0), -1.0,0,Color.WHITE,0,false)
	menu_card = B.label(self,"",c+Vector3(-.90,1.50,2.023),22,Color(.08,.16,.16),Color(0,0,0,0),0)
	menu_card.pixel_size = .0008
	menu_card.outline_size = 0
	var pickup_label := B.label(self,"PEDIDOS PRONTOS",c+Vector3(.20,1.36,2.20),16,Color(.95,.89,.72),Color(.05,.12,.12),0)
	pickup_label.pixel_size = .0006
	Real.place(self,"k:utensil-fork",c+Vector3(-1.98,1.31,.93),0.0,PI*.5,Color.WHITE,.13)
	Real.place(self,"k:utensil-spoon",c+Vector3(-1.90,1.31,.93),0.0,PI*.5,Color.WHITE,.13)
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
	var label := B.label(node, title, Vector3(0, size.y + 0.12, 0), 20, Color(1, 0.96, 0.8), Color(0, 0, 0, 0.8), 0)
	label.pixel_size = 0.0018
	station_bodies.append(_interaction(node, Vector3(0, size.y * 0.5, 0), size, station_prompt.bind(kind, title), open_station.bind(kind)))

func station_prompt(_kind: String, title: String) -> String:
	return title if Core.company_enabled() else title + " · E para criar seu quiosque"

func can_access(kind: String) -> bool:
	return Core.company_enabled() and stations.has(kind) and main.player.global_position.distance_to(stations[kind].global_position) < 2.1 and absf(main.player.global_position.x - center().x) < 2.0 and main.player.global_position.z > center().z - 1.5

func open_station(kind: String) -> void:
	if not Core.company_enabled():
		main.hud.phone.open("empresa")
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		return
	if not can_access(kind):
		return
	Core.service_station = kind
	main.audio.kiosk_sfx("fridge" if kind == "bebidas" else "pickup",stations[kind].global_position)
	if kind == "bebidas":
		_animate_door(-deg_to_rad(105))
	main.hud.phone.open("servico")
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func finish_station() -> void:
	main.hud.toggle_shop()
	if absf(door.rotation.y) > .1: main.audio.kiosk_sfx("fridge",stations.bebidas.global_position)
	_animate_door(0.0)

func _register_prompt() -> String:
	return "Caixa · receber %d contas" % Core.company.receivables.size() if Core.company_enabled() else ""

func collect_payments() -> void:
	var amount: int = Core.collect_company_payments()
	if amount > 0: main.audio.kiosk_sfx("cash",center()+Vector3(1.3,1.4,1.8))
	Core.toast.emit("Recebido: " + Core.fmt_money(amount), "good")

func customer_prompt(ref: WeakRef) -> String:
	var g = ref.get_ref()
	if not is_instance_valid(g) or g.is_queued_for_deletion():
		return ""
	if g.state == "kchoose": return "Cliente escolhendo no cardápio"
	if g.state != "kwait": return ""
	if not bool(g.get_meta("order_taken", true)): return "Anotar pedido " + order_number(g)
	var id: String = str(Core.company.carry)
	if id in main.village._remaining(g):
		return "Entregar " + tr(str(Economy.dish(id).name))
	return "Ver pedido " + order_number(g) + " · " + main.village._order_text(g)

func take_order(ref: WeakRef, by_staff: bool = false) -> bool:
	var g = ref.get_ref()
	if not is_instance_valid(g) or g.is_queued_for_deletion() or g.state != "kwait" or bool(g.get_meta("order_taken", true)):
		return false
	if not by_staff and main.player.global_position.distance_to(g.global_position) > 3.0:
		return false
	g.set_meta("order_taken", true)
	g.timer = main.village._patience(g)
	g.set_meta("urgent", false)
	g.show_order(main.village._order_text(g))
	main.hud._update_orders()
	if not by_staff:
		Core.toast.emit("Pedido anotado " + order_number(g) + ": " + main.village._order_text(g), "good")
	return true

func customer_action(ref: WeakRef) -> bool:
	var g = ref.get_ref()
	if not is_instance_valid(g) or g.is_queued_for_deletion() or g.state != "kwait":
		return false
	if main.player.global_position.distance_to(g.global_position) > 3.0: return false
	if not bool(g.get_meta("order_taken", true)):
		return take_order(ref)
	if str(Core.company.carry) in main.village._remaining(g):
		return deliver(ref)
	Core.toast.emit("Pedido " + order_number(g) + ": " + main.village._order_text(g), "info")
	return true

func deliver(ref: WeakRef) -> bool:
	var g = ref.get_ref()
	if not Core.company_enabled() or not is_instance_valid(g) or g.is_queued_for_deletion() or g.state != "kwait" or not bool(g.get_meta("order_taken", true)):
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
	visible = true
	for body in find_children("*", "StaticBody3D", true, false):
		if body is Interactable:
			body.collision_layer = (3 if body in station_bodies else 2) if visible else 0
		else:
			body.collision_layer = 1 if visible else 0
	hand.visible = Core.company_enabled()
	_sync_staff_presence()
	_sync_products()
	_update_menu_card()
	var held: String = str(Core.company.carry)
	if held != _hand_key:
		if held != "": main.audio.kiosk_sfx("pickup",main.player.global_position)
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
	for g in main.village.customers:
		if is_instance_valid(g) and not g.has_meta("company_target"):
			var ref: WeakRef = weakref(g)
			var target := _interaction(g, Vector3(0, 0.95, -0.28), Vector3(0.65, 1.0, 0.65), customer_prompt.bind(ref), customer_action.bind(ref))
			target.name = "CustomerInteraction"
			g.set_meta("company_target", true)
	if not Core.company_enabled() or not Core.in_game or Core.paused or get_tree().paused:
		return
	pulse -= delta
	if pulse > 0:
		return
	pulse = 0.25
	_staff_tick()
	_sync_products()

func _actor(role: String, pos: Vector3):
	if not actors.has(role):
		var g = main.village._make()
		g.position = pos
		g.state = "employee"
		g.go([])
		g.speed = 2.0
		var display_name: String = str(Economy.STAFF[role].name)
		if Core.company.sim.management.profiles.has(role):
			display_name = Core.CompanyRules.Simulation.Management.candidate(role, int(Core.company.sim.management.profiles[role].kind)).name
		g.set_meta("staff_name", display_name)
		g.apply_staff_uniform(role)
		if role == "cozinheiro": g.rotation.y = PI
		actors[role] = g
	return actors[role]

func _staff_home(role: String) -> Vector3:
	var offsets := {"cozinheiro": Vector3(1.2, 0.1, -1.08), "atendente": Vector3(-0.9, 0.1, 0.55), "garcom": Vector3(0.1, 0.1, 0.7), "caixa": Vector3(1.25, 0.1, 1.15), "limpeza": Vector3(-3.6, 0.1, 3.4)}
	return center() + offsets[role]

func _sync_staff_presence() -> void:
	for role in ["garcom", "atendente", "caixa", "cozinheiro", "limpeza"]:
		var hired: bool = bool(Core.staff.get(role, false))
		var present: bool = hired and not bool(Core.prog.staff_rec(role).get("off", false))
		if present:
			var g = _actor(role, _staff_home(role))
			g.visible = true
			var working: bool = Core.company_enabled() and Core.prog.staff_eff(role) > 0 and main.village.kiosk_open()
			g.set_process(working)
			if not working:
				if g.has_meta("work_target"): g.remove_meta("work_target")
				g.go([])
				g.play("Idle_Loop")
		elif actors.has(role):
			actors[role].visible = false
			actors[role].set_process(false)

func _staff_tick() -> void:
	_sync_staff_presence()
	var c: Vector3 = center()
	var waiter_role: String = "garcom" if Core.prog.staff_eff("garcom") > 0 else ("atendente" if Core.prog.staff_eff("atendente") > 0 else "cozinheiro")
	if waiter_role != waiter_role_active:
		waiter_role_active = waiter_role
		waiter_phase = ""
		waiter_target = null
		for old_role in ["garcom", "atendente", "cozinheiro"]:
			if actors.has(old_role):
				_clear_tray(actors[old_role])
	for role in ["garcom", "atendente", "caixa", "cozinheiro", "limpeza"]:
		var active: bool = Core.prog.staff_eff(role) > 0 and main.village.kiosk_open()
		if actors.has(role):
			actors[role].set_process(active)
		if not active:
			continue
		var pos: Vector3 = c + Vector3(1.05, 0.1, -0.2)
		if role == "atendente": pos = c + Vector3(-0.9, 0.1, 0.55)
		elif role == "garcom": pos = c + Vector3(0.1, 0.1, 0.7)
		if role == "caixa":
			pos = c + Vector3(1.25, 0.1, 1.15)
		elif role == "limpeza":
			pos = c + Vector3(-3.6, 0.1, 3.4)
		var g = _actor(role, pos)
		var uniform: String = str(Core.company.sim.management.look.uniform)
		if Core.company.sim.management.look_owned and str(g.get_meta("uniform", "")) != uniform:
			g.set_colors(g._skin, Core.CompanyRules.Simulation.Management.UNIFORMS[uniform], Color(0.15, 0.2, 0.27), g._hair_col)
			g.set_meta("uniform", uniform)
		g.speed = 2.0 * Core.prog.staff_eff(role) * (1.0 + Core.prog.eff("kiosk_speed"))
		if role == "caixa":
			if not Core.company.receivables.is_empty():
				Core.collect_company_payments()
		elif role == "cozinheiro" and waiter_role != "cozinheiro":
			if g.has_meta("work_target"): g.remove_meta("work_target")
		elif role == "limpeza":
			_cleaner(g)
		else:
			_waiter(g)

func _waiter(g) -> void:
	if g.is_moving():
		return
	if waiter_phase == "order":
		var target = waiter_target.get_ref() if waiter_target != null else null
		if is_instance_valid(target) and not target.spot.is_empty() and g.position.distance_to(target.spot.approach) < 1.2:
			take_order(waiter_target, true)
		waiter_phase = ""
		waiter_target = null
		return
	if waiter_phase == "" and Core.company.staff_carry == "" and main.village.waiting_customers().is_empty():
		var pending: Array = main.village.customers_to_order()
		if not pending.is_empty():
			waiter_target = weakref(pending[0])
			waiter_phase = "order"
			g.go([center()+Vector3(3.2,.1,-.85), center()+Vector3(3.2,.1,3.5), pending[0].spot.approach])
			return
	if waiter_phase == "pickup":
		if Time.get_ticks_msec() < int(g.get_meta("handoff_until",0)): return
		waiter_phase = "deliver"
		g.set_meta("work_kind","carry")
		g.go(g.get_meta("delivery_route",[]))
		return
	if waiter_phase == "deliver":
		var target = waiter_target.get_ref() if waiter_target != null else null
		if is_instance_valid(target) and not target.is_queued_for_deletion() and target.state == "kwait" and str(Core.company.staff_carry) in main.village._remaining(target) and g.position.distance_to(target.spot.approach) < 1.0:
			if not g.has_meta("delivering"):
				g.set_meta("delivering",true)
				g.set_meta("handoff_until",Time.get_ticks_msec()+400)
				g.set_meta("work_kind","handoff")
				g.set_meta("work_target",target.global_position+Vector3(0,1.0,0))
				return
			if Time.get_ticks_msec() < int(g.get_meta("handoff_until")): return
			g.remove_meta("delivering")
			main.village._deliver_item(target, str(Core.company.staff_carry), true, true)
		waiter_phase = ""
		_clear_tray(g)
		g.play("Idle_Loop")
	# Return safely to the shelves before returning or taking an item.
	var pickup: Vector3 = center() + Vector3(0, 0.1, -0.65)
	if g.position.distance_to(pickup) > 0.5:
		g.go([center() + Vector3(3.2, 0.1, 3.5), center() + Vector3(3.2, 0.1, -0.85), center() + Vector3(1.1, 0.1, -0.85), pickup])
		return
	if Core.company.staff_carry != "":
		if not Core.return_company_staff_dish():
			return
	for target in main.village.waiting_customers():
		for id in main.village._remaining(target):
			if not Core.reserve_company_staff_dish(id):
				continue
			waiter_target = weakref(target)
			waiter_phase = "pickup"
			g.set_meta("handoff_until",Time.get_ticks_msec()+400)
			var tray := Node3D.new()
			tray.name = "StaffTray"
			g.add_child(tray)
			tray.position = Vector3(0, 1.0, 0.32)
			tray.scale = Vector3.ONE * 0.65
			Dishes.build(tray, id)
			g.set_meta("work_kind","pickup")
			g.set_meta("work_target",center()+Vector3(-.18,1.10,-1.10))
			g.set_meta("delivery_route",[center() + Vector3(1.1, 0.1, -0.85), center() + Vector3(3.2, 0.1, -0.85), center() + Vector3(3.2, 0.1, 3.5), target.spot.approach])
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
	if g.has_meta("work_target"): g.remove_meta("work_target")
	if g.has_meta("delivering"): g.remove_meta("delivering")
	var tray = g.get_node_or_null("StaffTray")
	if tray != null:
		g.remove_child(tray)
		tray.queue_free()

func order_number(g) -> String:
	var index: int = main.world.kiosk_spots.find(g.spot)
	return "#%02d" % (index + 1)

func seat_name(g) -> String:
	var index: int = main.world.kiosk_spots.find(g.spot)
	return "Balcão %d" % (index + 1) if index < 2 else "Mesa %d%s" % [1 + int((index - 2) / 2), "A" if index % 2 == 0 else "B"]

func order_summary(g) -> String:
	var parts: Array = []
	for id in main.village._remaining(g):
		var available: bool = Core.company_available(id) > 0
		parts.append("%s · %s" % [Economy.dish(id).name, "retirar" if available else "repor estoque"])
	return "%s %s\n%s" % [order_number(g), seat_name(g), "\n".join(parts)]

## Uma vaga fixa por receita: o último produto retirado não deixa o expositor vazio.
## A quantidade vendável continua em company.ready; o exemplar de referência não é estoque.
func shelf_menu() -> Array:
	var catalog: Array = []
	for id in Economy.KIOSK_MENU:
		if not bool(Economy.dish(id).get("secret", false)) or Core.prog.is_discovered(id):
			catalog.append(id)
	return catalog

func _sync_products() -> void:
	var catalog: Array = shelf_menu()
	var menu: Array = Core.kiosk_menu()
	var key := JSON.stringify([Core.company.ready, Core.stock, catalog, menu])
	if key == _display_key: return
	_display_key = key
	for child in products.get_children():
		products.remove_child(child)
		child.queue_free()
	var drink_slot := 0
	var food_slot := 0
	var drinks: Array = catalog.filter(func(id): return Dishes.is_drink(id))
	var food_count := catalog.size() - drinks.size()
	for id in catalog:
		var drink: bool = Dishes.is_drink(id)
		var slot: int = drink_slot if drink else food_slot
		var anchor: Node3D = stations.bebidas if drink else stations.pratos
		var columns := 2 if drink else 3
		var kind_count := maxi(1, drinks.size() if drink else food_count)
		var capacity := 12 if drink else 9
		var row := int(slot / columns)
		var shelf_y: float = [0.315, 0.795, 1.275][mini(row, 2)] if drink else [0.0625, 0.4125, 0.7625][mini(row, 2)]
		var x := -0.22 + float(slot % columns) * 0.44 if drink else -0.31 + float(slot % columns) * 0.31
		var count := Core.company_available(id)
		var display := Node3D.new()
		display.name = "Shelf_" + str(id)
		display.set_meta("shelf_dish_id", id)
		display.set_meta("stock_count", count)
		display.set_meta("display_only", count == 0)
		products.add_child(display)
		# Exposição completa nas três prateleiras; a etiqueta informa o estoque vendável.
		var copies := int(ceil(float(capacity - slot) / float(kind_count)))
		for unit in maxi(1, copies):
			var cell := slot + unit * kind_count
			var shelf_cell := cell % 6 if drink else cell
			var item_row := mini(2, int(shelf_cell / columns))
			var item_y: float = [0.315, 0.795, 1.275][item_row] if drink else [0.0625, 0.4125, 0.7625][item_row]
			var item_x := -0.22 + float(cell % columns) * 0.44 if drink else -0.31 + float(cell % columns) * 0.31
			var item := Node3D.new()
			display.add_child(item)
			item.position = anchor.position + Vector3(item_x, item_y, (0.13 if cell < 6 else -0.13) if drink else 0.08)
			item.scale = Vector3.ONE * 0.95
			Dishes.build(item, id)
		var status: String = "%d prontos" % count
		if count == 0:
			status = "Repor estoque" if id in menu else ("Fora do cardápio" if Core.dish_unlocked(id) else "Desbloquear receita")
		var tag := B.label(display, "%s\n%s" % [Economy.dish(id).name, status], anchor.position + Vector3(x, shelf_y + 0.02, 0.335), 18, Color(1, 0.94, 0.72) if count > 0 else Color(1, 0.72, 0.52), Color(0.03, 0.08, 0.09))
		tag.name = "StockTag"
		tag.pixel_size = 0.0014
		tag.outline_size = 3
		tag.shaded = false
		if drink: drink_slot += 1
		else: food_slot += 1

func _update_menu_card() -> void:
	if menu_card == null: return
	var lines: Array[String] = ["CARDÁPIO"]
	for id in Core.kiosk_menu():
		if lines.size() >= 5: break
		lines.append(str(Economy.dish(id).name))
	menu_card.text = "\n".join(lines)

func _update_work_lighting(_day: int, minutes: float) -> void:
	var evening := smoothstep(16.5,19.5,minutes/60.0)
	var lamp = main.world.find_child("KioskWorkLight",true,false)
	if lamp != null:
		lamp.light_energy = lerpf(.65,.92,evening)
		lamp.light_color = Color(1,.93,.82).lerp(Color(1,.84,.64),evening)

func _animate_door(angle: float) -> void:
	if door_tween != null and door_tween.is_valid(): door_tween.kill()
	door_tween = create_tween()
	door_tween.set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	door_tween.tween_property(door,"rotation:y",angle,.24).set_trans(Tween.TRANS_SINE)
