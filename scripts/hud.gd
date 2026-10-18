extends CanvasLayer


var player: Node
var guests: Node
var root: Control
var money_l: Label
var stars_l: Label
var clock_l: Label
var hint_l: Label
var prompt_l: Label
var desk_card: PanelContainer
var desk_body: Label
var _desk_hold: = ""
var crosshair: Control
var toasts: VBoxContainer
var shop: Control
var btn_interact: Button
var btn_shop: Button
var joy_base: = Vector2.ZERO
var joy_knob: = Vector2.ZERO
var joy_id: = -1
var look_id: = -1
var joy_radius: = 110.0
var joy_draw: Control
var _hint_t: = 0.0
var _touch_buttons: Array = []
var touch: = true
var menus: CanvasLayer
var world: Node3D
var village: Node3D
var keys_l: Label
var obj_l: Label
var obj_draw: Control
var obj_target: = Vector3.INF
var obj_text: = ""
var _pad_used: = false
var office: OfficeUI
var phone: PhoneUI
var compass: Control

func _ready() -> void :
	add_to_group("hud")
	layer = 5
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	root.theme = UiTheme.get_theme()

	var top: = PanelContainer.new()
	top.position = Vector2(18, 14)
	var ts: = UiTheme.box(Color(0.03, 0.17, 0.2, 0.78), 20, Color(1, 0.9, 0.7, 0.35), 2, 8, 18)
	top.add_theme_stylebox_override("panel", ts)
	root.add_child(top)
	var hb: = HBoxContainer.new()
	hb.add_theme_constant_override("separation", 26)
	top.add_child(hb)
	hb.add_child(_hud_icon("caixa", Color(0.75, 1.0, 0.7)))
	money_l = _label(hb, "R$ 300", 32, Color(0.75, 1.0, 0.7))
	stars_l = _label(hb, "★ 3.0", 32, Color(1.0, 0.86, 0.35))
	clock_l = _label(hb, "", 32, Color(1, 1, 1))
	for l in [money_l, stars_l, clock_l]:
		l.add_theme_font_override("font", UiTheme.bold())
	clock_l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	money_l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	stars_l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED

	hint_l = Label.new()
	hint_l.set_anchors_preset(Control.PRESET_CENTER_TOP)
	hint_l.position = Vector2(-400, 122)
	hint_l.size = Vector2(800, 60)
	hint_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint_l.add_theme_font_size_override("font_size", 25)
	hint_l.add_theme_font_override("font", UiTheme.bold())
	hint_l.add_theme_color_override("font_color", Color(1, 0.98, 0.94))
	hint_l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	hint_l.add_theme_constant_override("outline_size", 8)
	hint_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(hint_l)

	crosshair = Control.new()
	crosshair.set_anchors_preset(Control.PRESET_CENTER)
	crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	crosshair.draw.connect( func():
		crosshair.draw_circle(Vector2.ZERO, 4.0, Color(1, 1, 1, 0.9))
		crosshair.draw_arc(Vector2.ZERO, 7.0, 0, TAU, 20, Color(0, 0, 0, 0.5), 1.5))
	root.add_child(crosshair)
	prompt_l = Label.new()
	prompt_l.set_anchors_preset(Control.PRESET_CENTER)
	prompt_l.position = Vector2(-380, 30)
	prompt_l.size = Vector2(760, 52)
	prompt_l.grow_horizontal = Control.GROW_DIRECTION_BOTH
	var pst: = UiTheme.box(Color(0.03, 0.15, 0.18, 0.82), 26, Color(1.0, 0.85, 0.45, 0.8), 2, 6, 22)
	prompt_l.add_theme_stylebox_override("normal", pst)
	prompt_l.add_theme_font_override("font", UiTheme.bold())
	prompt_l.add_theme_color_override("font_color", Color(1, 0.97, 0.9))
	prompt_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	prompt_l.add_theme_font_size_override("font_size", 30)
	prompt_l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	prompt_l.add_theme_constant_override("outline_size", 10)
	prompt_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(prompt_l)
	_build_desk_card()

	toasts = VBoxContainer.new()
	toasts.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	toasts.position = Vector2(-500, 96)
	toasts.size = Vector2(480, 300)
	toasts.add_theme_constant_override("separation", 8)
	toasts.alignment = BoxContainer.ALIGNMENT_BEGIN
	toasts.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(toasts)

	btn_shop = _button("Loja", Vector2(-170, 14), Vector2(150, 64), Control.PRESET_TOP_RIGHT, Color(0.9, 0.55, 0.15, 0.9))
	btn_shop.pressed.connect(toggle_shop)
	btn_interact = _button("Interagir", Vector2(-250, -250), Vector2(210, 210), Control.PRESET_BOTTOM_RIGHT, Color(0.1, 0.55, 0.55, 0.85), 105)
	btn_interact.pressed.connect( func(): player.interact())
	var btn_menu: = _button("☰", Vector2(-260, 14), Vector2(76, 64), Control.PRESET_TOP_RIGHT, Color(0.1, 0.3, 0.4, 0.9))
	btn_menu.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	var open_menu: = func():
		if menus and not get_tree().paused:
			menus.toggle_pause()
	btn_menu.pressed.connect(open_menu)
	_touch_buttons = [[btn_shop, toggle_shop], [btn_interact, func(): player.interact()], [btn_menu, open_menu]]
	set_meta("btn_menu", btn_menu)

	joy_draw = Control.new()
	joy_draw.set_anchors_preset(Control.PRESET_FULL_RECT)
	joy_draw.mouse_filter = Control.MOUSE_FILTER_IGNORE
	joy_draw.draw.connect(_draw_joy)
	root.add_child(joy_draw)
	_build_shop()
	_build_objective()
	_build_compass()
	Core.day_closed.connect( func(s): office.show_day_summary(s))
	touch = Quality.is_touch()
	if not touch:

		btn_interact.visible = false
		btn_shop.visible = false
		joy_draw.visible = false
		btn_menu.visible = false
		keys_l = Label.new()
		_update_keys_hint()
		Quality.changed.connect(_update_keys_hint)
		keys_l.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
		keys_l.position = Vector2(-600, -58)
		keys_l.size = Vector2(1200, 44)
		keys_l.grow_horizontal = Control.GROW_DIRECTION_BOTH
		keys_l.add_theme_stylebox_override("normal", UiTheme.box(Color(0.03, 0.15, 0.18, 0.6), 20, Color(), 0, 0, 18))
		keys_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		keys_l.add_theme_font_size_override("font_size", 21)
		keys_l.add_theme_color_override("font_color", Color(1, 1, 1, 0.85))
		keys_l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
		keys_l.add_theme_constant_override("outline_size", 6)
		keys_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		root.add_child(keys_l)
		_update_keys_hint()
	Core.money_changed.connect( func(v): money_l.text = Core.fmt_money(v))
	Core.stars_changed.connect( func(v): stars_l.text = "★ %.1f" % v)
	Core.time_changed.connect( func(d, _m): clock_l.text = tr("Dia %d  %s") % [d, Core.clock_text()])
	Core.toast.connect(show_toast)
	money_l.text = Core.fmt_money(Core.money)
	stars_l.text = "★ %.1f" % Core.stars()

	root.move_child(office, root.get_child_count() - 1)
	root.move_child(office.summary, root.get_child_count() - 1)

func _style(c: Color, r: int) -> StyleBoxFlat:
	var s: = StyleBoxFlat.new()
	s.bg_color = c
	s.set_corner_radius_all(r)
	s.content_margin_left = 18
	s.content_margin_right = 18
	s.content_margin_top = 8
	s.content_margin_bottom = 8
	return s


func _hug(l: Label, fs: int, top: float, pad: float) -> void :
	var f: Font = l.get_theme_font("font")
	var w: = f.get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x + pad
	l.offset_left = - w * 0.5
	l.offset_right = w * 0.5
	l.offset_top = top
	l.offset_bottom = top + fs * 1.6

func _hud_icon(id: String, c: Color) -> TextureRect:
	var t: = TextureRect.new()
	t.texture = UiTheme.icon(id)
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	t.custom_minimum_size = Vector2(34, 34)
	t.self_modulate = c
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return t

func _label(parent: Node, t: String, fs: int, c: Color) -> Label:
	var l: = Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", fs)
	l.add_theme_color_override("font_color", c)
	parent.add_child(l)
	return l

func _button(t: String, pos: Vector2, sz: Vector2, preset: int, c: Color, radius: = 18) -> Button:
	var b: = Button.new()
	b.text = t
	b.set_anchors_preset(preset)
	b.position = pos
	b.size = sz
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_size_override("font_size", 30)
	for st in ["normal", "hover", "pressed"]:
		var s: = _style(c if st != "pressed" else c.lightened(0.25), radius)
		s.border_color = Color(1, 1, 1, 0.6)
		s.set_border_width_all(3)
		b.add_theme_stylebox_override(st, s)
	root.add_child(b)
	return b

func _build_shop() -> void :
	office = OfficeUI.new()
	root.add_child(office)
	office.attach_summary(root)
	office.visible = false
	phone = PhoneUI.new()
	root.add_child(phone)
	shop = phone
	shop.visible = false

## Abre o celular direto num app (os nomes das abas do antigo escritório ainda funcionam).
func open_office(tab: String = "caixa", room_id: int = -1) -> void :
	phone.open(PhoneUI.app_for_tab(tab), room_id)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func show_summary(data: Dictionary) -> void :
	office.show_day_summary(data)

func toggle_shop() -> void :
	if shop.visible:
		phone.close()
	else:
		phone.open(phone.app)
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		if _pad_used:
			var buttons: = shop.find_children("*", "Button", true, false)
			if not buttons.is_empty():
				buttons[0].grab_focus()
	if not shop.visible and not touch and not get_tree().paused and Core.in_game:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	get_tree().call_group("audio", "sfx", "click")

func show_toast(text: String, kind: String) -> void :
	var p: = PanelContainer.new()
	var c: = Color(0.02, 0.2, 0.25, 0.8)
	if kind == "money":
		c = Color(0.08, 0.38, 0.12, 0.85)
	elif kind == "bad":
		c = Color(0.5, 0.1, 0.08, 0.85)
	elif kind == "good":
		c = Color(0.05, 0.42, 0.45, 0.85)
	p.add_theme_stylebox_override("panel", UiTheme.box(c, 16, Color(1, 1, 1, 0.25), 2, 6, 16))
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var l: = _label(p, text, 23, Color.WHITE)
	l.add_theme_font_override("font", UiTheme.bold())
	l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(440, 0)
	toasts.add_child(p)
	while toasts.get_child_count() > 5:
		toasts.get_child(0).free()
	var tw: = create_tween()
	tw.tween_interval(4.5)
	tw.tween_property(p, "modulate:a", 0.0, 0.6)
	tw.tween_callback(p.queue_free)

func _build_desk_card() -> void :
	desk_card = PanelContainer.new()
	desk_card.set_anchors_preset(Control.PRESET_CENTER)
	desk_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	desk_card.visible = false
	desk_card.add_theme_stylebox_override("panel", UiTheme.box(UiTheme.SAND, 20, UiTheme.WOOD, 3, 14, 18))
	var vb: = VBoxContainer.new()
	vb.add_theme_constant_override("separation", 6)
	desk_card.add_child(vb)
	var title: = Label.new()
	title.text = tr("Recepção")
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_override("font", UiTheme.bold())
	title.add_theme_font_size_override("font_size", 30)
	title.add_theme_color_override("font_color", UiTheme.TEAL)
	vb.add_child(title)
	desk_body = Label.new()
	desk_body.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	desk_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desk_body.custom_minimum_size = Vector2(420, 0)
	desk_body.add_theme_font_override("font", UiTheme.font())
	desk_body.add_theme_font_size_override("font_size", 24)
	desk_body.add_theme_color_override("font_color", UiTheme.TEXT)
	vb.add_child(desk_body)
	root.add_child(desk_card)

func show_desk_card(text: String) -> void :
	_desk_hold = text
	_apply_desk_card(text)

func _apply_desk_card(text: String) -> void :
	if desk_card == null:
		return
	desk_body.text = text
	desk_card.visible = text != ""
	desk_card.reset_size()
	var sz: = desk_card.get_combined_minimum_size()
	desk_card.offset_left = - sz.x * 0.5
	desk_card.offset_right = sz.x * 0.5
	desk_card.offset_top = 48.0
	desk_card.offset_bottom = 48.0 + sz.y
	prompt_l.visible = false

func _process(delta: float) -> void :
	var f = player.focus if player else null
	var ptxt: String = f.get_prompt() if f else ""
	var at_desk: = f != null and str(f.name) == "Desk" and ptxt != ""
	if _desk_hold != "":
		_apply_desk_card(_desk_hold)
	elif at_desk:
		var line: = ptxt
		if not touch:
			line = "[%s]  %s" % [Quality.key_name("interact"), ptxt]
		_apply_desk_card(line)
	else:
		if desk_card:
			desk_card.visible = false
		if ptxt != "" and not touch:
			ptxt = "[%s]  %s" % [Quality.key_name("interact"), ptxt]
		if ptxt != prompt_l.text:
			prompt_l.text = ptxt
			_hug(prompt_l, 30, 30.0, 56.0)
		prompt_l.visible = ptxt != ""
	btn_interact.modulate = Color(1, 1, 1, 1.0 if f else 0.55)
	_hint_t -= delta
	if _hint_t <= 0.0:
		_hint_t = 0.5
		hint_l.text = _hint()
		_update_objective()
	crosshair.queue_redraw()
	obj_draw.queue_redraw()
	if compass:
		compass.queue_redraw()

func _hint() -> String:
	for r in Core.rooms:
		if r.state == "dirty":
			var falta: = []
			if r.dirty.cama: falta.append(tr("arrume a cama"))
			if r.dirty.toalhas: falta.append(tr("recolha as toalhas"))
			if r.dirty.lixo: falta.append(tr("jogue o lixo fora"))
			return tr("Bangalô %d sujo: %s.") % [r.id + 1, ", ".join(falta)]
	if guests and guests.queue_size() > 0:
		if Core.free_room() >= 0:
			return tr("Hóspede esperando! Vá ao balcão da recepção e faça o check-in.")
		return tr("Hóspedes esperando, mas nenhum bangalô livre.")
	if village and not village.waiting_customers().is_empty():
		return tr("Clientes esperando no quiosque!")
	if Core.money >= Core.REDE_PRICE and Core.redes < Core.MAX_REDES:
		return tr("Dica: compre uma rede na Loja para ganhar estrelas.")
	return tr("Aproveite a brisa... novos hóspedes chegam em breve.")


func _input(e: InputEvent) -> void :
	if e is InputEventScreenTouch:
		if e.pressed:
			for tb in _touch_buttons:
				var c: Control = tb[0]
				if c.is_visible_in_tree() and c.get_global_rect().has_point(e.position):
					tb[1].call()
					get_viewport().set_input_as_handled()
					return
			if shop.visible:
				get_viewport().set_input_as_handled()
				return
			var vw: = root.get_viewport_rect().size.x
			if e.position.x < vw * 0.42 and joy_id == -1:
				joy_id = e.index
				joy_base = e.position
				joy_knob = e.position
			elif look_id == -1:
				look_id = e.index
			get_viewport().set_input_as_handled()
		else:
			if e.index == joy_id:
				joy_id = -1
				player.move_input = Vector2.ZERO
			elif e.index == look_id:
				look_id = -1
		joy_draw.queue_redraw()
	elif e is InputEventScreenDrag:
		if e.index == joy_id:
			var d: Vector2 = e.position - joy_base
			d = d.limit_length(joy_radius)
			joy_knob = joy_base + d
			player.move_input = Vector2(d.x, - d.y) / joy_radius
			joy_draw.queue_redraw()
		elif e.index == look_id:
			player.look_delta(e.relative, true)
		get_viewport().set_input_as_handled()
	elif e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
		_pad_used = false
		if not shop.visible and not get_tree().paused and Core.in_game and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED and not _over_button(e.position):
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	elif (e is InputEventKey or e is InputEventJoypadButton) and e.is_pressed() and not e.is_echo():
		if e is InputEventJoypadButton:
			_pad_used = true
		if e is InputEventKey and e.physical_keycode == KEY_F11:
			Quality.toggle_fullscreen()
			return
		if not Core.in_game or not visible:
			return
		if e.is_action("pause") and not get_tree().paused:
			if shop.visible and phone.app != "":
				phone.back()
			elif shop.visible:
				toggle_shop()
			elif menus:
				menus.toggle_pause()
			get_viewport().set_input_as_handled()
		elif get_tree().paused:
			return
		elif shop.visible and e is InputEventJoypadButton and e.button_index == JOY_BUTTON_B:
			if phone.app != "":
				phone.back()
			else:
				toggle_shop()
		elif e.is_action("shop"):
			toggle_shop()
		elif e.is_action("interact") and not shop.visible:
			player.interact()

func _over_button(p: Vector2) -> bool:
	for tb in _touch_buttons:
		var c: Control = tb[0]
		if c.is_visible_in_tree() and c.get_global_rect().has_point(p):
			return true
	return false

func _draw_joy() -> void :
	var vs: = root.get_viewport_rect().size
	var base: = joy_base if joy_id != -1 else Vector2(170, vs.y - 170)
	var knob: = joy_knob if joy_id != -1 else base
	joy_draw.draw_circle(base, joy_radius, Color(1, 1, 1, 0.12))
	joy_draw.draw_arc(base, joy_radius, 0, TAU, 48, Color(1, 1, 1, 0.45), 3.0)
	joy_draw.draw_circle(knob, 46, Color(1, 1, 1, 0.45))


func _update_keys_hint() -> void :
	if keys_l == null:
		return
	keys_l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	var mv: = "%s%s%s%s" % [Quality.key_name("move_forward"), Quality.key_name("move_left"), Quality.key_name("move_back"), Quality.key_name("move_right")]
	keys_l.text = tr("%s andar  ·  Mouse olhar  ·  %s interagir  ·  %s celular  ·  %s correr  ·  Esc menu  ·  F11 tela cheia") % [mv, Quality.key_name("interact"), Quality.key_name("shop"), Quality.key_name("sprint")]
	if keys_l.is_inside_tree():
		_hug(keys_l, 21, -58.0, 44.0)


func _build_objective() -> void :
	obj_l = Label.new()
	obj_l.set_anchors_preset(Control.PRESET_TOP_LEFT)
	obj_l.position = Vector2(22, 84)
	obj_l.size = Vector2(640, 40)
	obj_l.add_theme_font_size_override("font_size", 26)
	obj_l.add_theme_font_override("font", UiTheme.bold())
	obj_l.add_theme_color_override("font_color", Color(1.0, 0.92, 0.55))
	obj_l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	obj_l.add_theme_constant_override("outline_size", 8)
	obj_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	obj_l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	root.add_child(obj_l)
	obj_draw = Control.new()
	obj_draw.set_anchors_preset(Control.PRESET_FULL_RECT)
	obj_draw.mouse_filter = Control.MOUSE_FILTER_IGNORE
	obj_draw.draw.connect(_draw_objective)
	root.add_child(obj_draw)

func objective() -> Array:

	if world == null or player == null:
		return ["", Vector3.INF, 0.0]
	var pp: Vector3 = player.global_position
	var home: Vector3 = world.bed.global_position if world.get("bed") else Vector3.INF
	if Core.can_sleep() and home != Vector3.INF:
		return [tr("Já é tarde: volte para casa e durma"), home, 2.5]
	for r in Core.rooms:
		if r.state == "dirty":
			var bc: = Vector3(world.BUNG_X[r.id], 0.6, world.BUNG_Z)
			return [tr("Limpar o Bangalô %d") % (r.id + 1), bc, 5.0]
	if guests and guests.queue_size() > 0 and Core.free_room() >= 0:
		return [tr("Check-in na recepção"), world.desk.global_position, 3.5]
	if village:
		var kc: Vector3 = world.kiosk_counter.global_position
		if not village.waiting_customers().is_empty():
			return [tr("Turno no quiosque: clientes esperando"), kc, 4.0]
	for id in Economy.EXPANSION_ORDER:
		if Core.expansion_state(id)[0] == "ready":
			return [tr("Dá para comprar: %s — abra o celular (%s)") % [tr(str(Economy.EXPANSIONS[id].name)), Quality.key_name("shop")], Vector3.INF, 0.0]
	if village:
		var kc: Vector3 = world.kiosk_counter.global_position
		if Core.minutes < 8.0 * 60.0:
			return [tr("Turno no quiosque às 08:00"), kc, 6.0]
		if village.kiosk_open() and pp.distance_to(kc) > 30.0:
			return [tr("Turno no quiosque"), kc, 6.0]
	if Core.menu_blocked() and world.get("market"):
		return [tr("Estoque baixo: mercadinho"), world.market.global_position, 4.0]
	for r in Core.rooms:
		if int(r.upgrades.get("clima", 0)) == 0 and Core.money >= Economy.next_cost("clima", 0):
			return [tr("Melhorar o Bangalô %d") % (r.id + 1), Vector3(world.BUNG_X[r.id], 0.6, world.BUNG_Z), 6.0]
	var nx: = Core.next_expansion()
	if nx != "":
		var st: Array = Core.expansion_state(nx)
		return [tr("Meta: %s · %s") % [tr(str(Economy.EXPANSIONS[nx].name)), str(st[1])], Vector3.INF, 0.0]
	return ["", Vector3.INF, 0.0]

func _update_objective() -> void :
	var o: = objective()
	obj_text = o[0]
	obj_target = o[1]
	if obj_text == "":
		obj_l.text = ""
		return
	if obj_target == Vector3.INF:
		obj_l.text = "➤ " + obj_text
		obj_l.set_meta("min_d", o[2])
		return
	var d: float = player.global_position.distance_to(obj_target) if player else 0.0
	obj_l.text = "➤ %s  (%d m)" % [obj_text, int(d)] if d > float(o[2]) else "➤ " + obj_text
	obj_l.set_meta("min_d", o[2])

func _draw_objective() -> void :
	if obj_target == Vector3.INF or player == null or not Core.in_game:
		return
	var cam: Camera3D = get_viewport().get_camera_3d()
	if cam == null:
		return
	var d: float = player.global_position.distance_to(obj_target)
	if d < float(obj_l.get_meta("min_d", 3.0)):
		return
	var vs: = root.get_viewport_rect().size
	var tp: = obj_target + Vector3(0, 1.2, 0)
	var behind: = cam.is_position_behind(tp)
	var sp: = cam.unproject_position(tp)
	var col: = Color(1.0, 0.85, 0.3, 0.95)
	var margin: = 60.0
	var inside: = not behind and sp.x > margin and sp.x < vs.x - margin and sp.y > margin and sp.y < vs.y - margin
	if inside:

		var pts: = PackedVector2Array([sp + Vector2(0, -16), sp + Vector2(11, 0), sp + Vector2(0, 16), sp + Vector2(-11, 0)])
		obj_draw.draw_colored_polygon(pts, col)
		obj_draw.draw_polyline(pts + PackedVector2Array([pts[0]]), Color(0, 0, 0, 0.6), 2.0)
		obj_draw.draw_string(get_theme_default_font(), sp + Vector2(-30, 38), "%d m" % int(d), HORIZONTAL_ALIGNMENT_CENTER, 60, 20, Color.WHITE)
		return

	var c: = vs * 0.5
	var dir: = (sp - c)
	if behind:
		dir = - dir
	if dir.length() < 1.0:
		dir = Vector2(0, 1)
	dir = dir.normalized()
	var r: = minf(vs.x, vs.y) * 0.42
	var p: = c + dir * r
	var n: = Vector2( - dir.y, dir.x)
	var tri: = PackedVector2Array([p + dir * 26, p - dir * 12 + n * 18, p - dir * 12 - n * 18])
	obj_draw.draw_colored_polygon(tri, col)
	obj_draw.draw_polyline(tri + PackedVector2Array([tri[0]]), Color(0, 0, 0, 0.6), 2.0)

func get_theme_default_font() -> Font:
	return UiTheme.bold()

func _build_compass() -> void :
	compass = Control.new()
	compass.set_anchors_preset(Control.PRESET_FULL_RECT)
	compass.mouse_filter = Control.MOUSE_FILTER_IGNORE
	compass.draw.connect(_draw_compass)
	root.add_child(compass)

func _draw_compass() -> void :
	if player == null or not Core.in_game or not visible:
		return
	var body: = player as Node3D
	var fwd: Vector3 = - body.global_transform.basis.z
	var head: = fposmod(rad_to_deg(atan2(fwd.x, - fwd.z)), 360.0)
	var vs: = root.get_viewport_rect().size
	var cx: = vs.x * 0.5
	var y: = 86.0
	var px: = 2.4
	compass.draw_rect(Rect2(cx - 130, y - 14, 260, 28), Color(0.02, 0.12, 0.16, 0.45))
	var marks: = [["N", 0.0], ["L", 90.0], ["S", 180.0], ["O", 270.0]]
	for m in marks:
		var delta: = wrapf(float(m[1]) - head, -180.0, 180.0)
		if absf(delta) > 70.0:
			continue
		var x: = cx + delta * px
		compass.draw_string(get_theme_default_font(), Vector2(x - 8, y + 6), str(m[0]), HORIZONTAL_ALIGNMENT_LEFT, -1, 21, Color(1, 0.92, 0.7))
	compass.draw_line(Vector2(cx, y - 12), Vector2(cx, y + 12), Color(1, 0.85, 0.35), 2.0)
	var wind: = tr("chuva") if Core.weather == "rain" else tr("sol")
	compass.draw_string(get_theme_default_font(), Vector2(cx + 138, y + 4), wind, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color(0.85, 0.95, 1))
