class_name OfficeUI
extends Control
## Escritório da pousada: caixa do dia, insumos, melhorias dos quartos e equipe.

var tab := "caixa"
var room_focus := 0
var body: VBoxContainer
var title_l: Label
var sub_l: Label
var summary: Control
var summary_body: VBoxContainer

func _ready() -> void:
	set_anchors_preset(Control.PRESET_CENTER)
	offset_left = -440
	offset_top = -330
	offset_right = 440
	offset_bottom = 330
	mouse_filter = Control.MOUSE_FILTER_STOP
	var panel := StyleBoxFlat.new()
	panel.bg_color = Color(0.97, 0.94, 0.88, 0.98)
	panel.set_corner_radius_all(18)
	panel.content_margin_left = 18
	panel.content_margin_right = 18
	panel.content_margin_top = 14
	panel.content_margin_bottom = 14
	panel.border_color = Color(0.75, 0.55, 0.28, 0.9)
	panel.set_border_width_all(2)
	add_theme_stylebox_override("panel", panel)
	# Control não desenha StyleBox de panel; usa um Panel por baixo.
	var bg := Panel.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bg.add_theme_stylebox_override("panel", panel)
	add_child(bg)
	var root := VBoxContainer.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.offset_left = 16
	root.offset_top = 12
	root.offset_right = -16
	root.offset_bottom = -12
	root.add_theme_constant_override("separation", 8)
	add_child(root)
	title_l = _label(root, "Escritório da Pousada", 28, Color(0.08, 0.32, 0.36))
	title_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub_l = _label(root, "", 18, Color(0.25, 0.2, 0.12))
	sub_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 8)
	root.add_child(tabs)
	for pair in [["caixa", "Caixa"], ["insumos", "Insumos"], ["bangalo", "Bangalôs"], ["equipe", "Equipe"]]:
		var b := Button.new()
		b.text = pair[1]
		b.focus_mode = Control.FOCUS_NONE
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.custom_minimum_size = Vector2(0, 40)
		b.add_theme_font_size_override("font_size", 18)
		var id: String = pair[0]
		b.pressed.connect(func():
			tab = id
			call_deferred("refresh"))
		tabs.add_child(b)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(820, 430)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	root.add_child(scroll)
	body = VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 6)
	scroll.add_child(body)
	var close := Button.new()
	close.text = "Fechar"
	close.focus_mode = Control.FOCUS_NONE
	close.custom_minimum_size = Vector2(0, 42)
	close.add_theme_font_size_override("font_size", 20)
	close.pressed.connect(func(): get_tree().call_group("hud", "toggle_shop"))
	root.add_child(close)
	_build_summary()
	visible = false

func _label(parent: Node, t: String, fs: int, c: Color) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", fs)
	l.add_theme_color_override("font_color", c)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	parent.add_child(l)
	return l

func _btn(text: String, cb: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(150, 36)
	b.add_theme_font_size_override("font_size", 16)
	b.pressed.connect(cb)
	return b

func _clear_body() -> void:
	while body.get_child_count() > 0:
		var c := body.get_child(0)
		body.remove_child(c)
		c.free()

func show_tab(which: String, room_id := -1) -> void:
	tab = which
	if room_id >= 0:
		room_focus = room_id
	visible = true
	refresh()

func refresh() -> void:
	if body == null:
		return
	_clear_body()
	sub_l.text = "%s   ·   ★ %.1f   ·   %s" % [Core.fmt_money(Core.money), Core.stars(), tr("Dia %d  %s") % [Core.day, Core.clock_text()]]
	match tab:
		"insumos":
			_fill_supplies()
		"bangalo":
			_fill_rooms()
		"equipe":
			_fill_staff()
		_:
			_fill_ledger()

func _fill_ledger() -> void:
	_label(body, "Caixa de hoje", 22, Color(0.1, 0.35, 0.32))
	var net := Core.day_income - Core.day_expense
	_label(body, tr("Entradas %s    Saídas %s    Saldo do dia %s") % [Core.fmt_money(Core.day_income, true), Core.fmt_money(-Core.day_expense), Core.fmt_money(net, true)], 18, Color(0.2, 0.16, 0.1))
	var cats := {}
	for line in Core.ledger_today:
		var c: String = str(line.get("c", "outro"))
		cats[c] = int(cats.get(c, 0)) + int(line.get("a", 0))
	for c in Economy.CAT_NAME:
		if not cats.has(c):
			continue
		_label(body, "%s   %s" % [tr(Economy.CAT_NAME[c]), Core.fmt_money(int(cats[c]), true)], 18, Color(0.15, 0.2, 0.18))
	_label(body, tr("Lançamentos"), 20, Color(0.1, 0.35, 0.32))
	var lines: Array = Core.ledger_today.duplicate()
	lines.reverse()
	var n := mini(12, lines.size())
	if n == 0:
		_label(body, tr("Nada lançado hoje. Diárias, bar, quiosque e compras aparecem aqui."), 16, Color(0.3, 0.25, 0.18))
	for i in n:
		var line: Dictionary = lines[i]
		var col := Color(0.1, 0.4, 0.2) if int(line.a) >= 0 else Color(0.45, 0.15, 0.1)
		_label(body, "%s   %s" % [str(line.r), Core.fmt_money(int(line.a), true)], 16, col)

func _fill_supplies() -> void:
	_label(body, tr("Mercadinho e padaria — o estoque vale para o bar e o quiosque."), 18, Color(0.2, 0.16, 0.1))
	for id in Economy.SUPPLIES:
		var s: Dictionary = Economy.SUPPLIES[id]
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		body.add_child(row)
		var name := _label(row, "%s" % tr(str(s.name)), 18, Color(0.12, 0.18, 0.16))
		name.custom_minimum_size = Vector2(160, 0)
		var info := _label(row, tr("estoque %d   compra %s") % [int(Core.stock.get(id, 0)), Core.fmt_money(int(s.cost))], 16, Color(0.25, 0.2, 0.12))
		info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(_btn(tr("×1"), _buy.bind(id, 1)))
		row.add_child(_btn(tr("Fardo ×%d") % Economy.PACK, _buy.bind(id, Economy.PACK)))
	_label(body, tr("Cardápio — margem por prato"), 20, Color(0.1, 0.35, 0.32))
	for id in Economy.BAR_MENU:
		var d: Dictionary = Economy.dish(id)
		var where := tr("bar e quiosque") if id in Economy.KIOSK_MENU else tr("só no bar")
		var ok := "●" if Core.can_make(id) else "○"
		_label(body, "%s %s  %s   %s   %s %s" % [ok, tr(str(d.name)), Core.fmt_money(int(d.price)), tr("margem %s") % Core.fmt_money(Economy.dish_margin(id)), tr("custo %s") % Core.fmt_money(Economy.dish_cost(id)), where], 16, Color(0.15, 0.18, 0.14))

func _fill_rooms() -> void:
	var pick := HBoxContainer.new()
	body.add_child(pick)
	for i in Core.rooms.size():
		var b := _btn(tr("Bangalô %d") % (i + 1), _pick_room.bind(i))
		if i == room_focus:
			b.modulate = Color(0.75, 1.0, 0.85)
		pick.add_child(b)
	room_focus = clampi(room_focus, 0, Core.rooms.size() - 1)
	var rate := Core.nightly_rate(room_focus)
	_label(body, tr("Diária deste quarto: %s    (base com estrelas e redes + melhorias)") % Core.fmt_money(rate), 18, Color(0.12, 0.28, 0.22))
	for cat in Economy.UPGRADES:
		var def: Dictionary = Economy.UPGRADES[cat]
		var tier: int = int(Core.rooms[room_focus].upgrades.get(cat, 0))
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		body.add_child(row)
		var name := _label(row, tr(str(def.name)), 18, Color(0.12, 0.18, 0.16))
		name.custom_minimum_size = Vector2(150, 0)
		var nxt := Economy.next_cost(cat, tier)
		var desc := tr(Economy.tier_name(cat, tier))
		if nxt < 0:
			desc += "  ·  " + tr("no máximo") + "  ·  " + tr("+%s na diária") % Core.fmt_money(Economy.tier_rate(cat, tier))
		else:
			var gain: int = Economy.tier_rate(cat, tier + 1) - Economy.tier_rate(cat, tier)
			desc += "  →  %s   %s   %s" % [tr(Economy.tier_name(cat, tier + 1)), Core.fmt_money(nxt), tr("+%s/noite") % Core.fmt_money(gain)]
		var info := _label(row, desc, 15, Color(0.25, 0.2, 0.12))
		info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		if nxt >= 0:
			row.add_child(_btn(tr("Melhorar"), _upgrade.bind(cat)))
	var hammock := HBoxContainer.new()
	body.add_child(hammock)
	_label(hammock, tr("Redes na praia: %d / %d") % [Core.redes, Core.MAX_REDES], 18, Color(0.12, 0.18, 0.16)).size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hammock.add_child(_btn(tr("Comprar rede (%s)") % Core.fmt_money(Core.REDE_PRICE), func():
		if Core.buy_rede():
			get_tree().call_group("audio", "sfx", "coin")
		call_deferred("refresh")))
	if Core.rooms.size() < Economy.BUNGALOW_MAX:
		var grow := HBoxContainer.new()
		body.add_child(grow)
		_label(grow, tr("Novo bangalô"), 18, Color(0.12, 0.18, 0.16)).size_flags_horizontal = Control.SIZE_EXPAND_FILL
		grow.add_child(_btn(tr("Construir (%s)") % Core.fmt_money(Economy.BUNGALOW_COST), func():
			if Core.build_bungalow():
				get_tree().call_group("audio", "sfx", "coin")
				room_focus = Core.rooms.size() - 1
			call_deferred("refresh")))

func _fill_staff() -> void:
	_label(body, tr("Contratar gente da vila. O salário sai no fechamento do dia."), 18, Color(0.2, 0.16, 0.1))
	for role in Economy.STAFF:
		var s: Dictionary = Economy.STAFF[role]
		var hired := bool(Core.staff.get(role, false))
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		body.add_child(row)
		var name := _label(row, tr(str(s.name)), 18, Color(0.12, 0.18, 0.16))
		name.custom_minimum_size = Vector2(160, 0)
		var st := tr("na equipe") if hired else tr("livre")
		var info := _label(row, "%s   %s   %s" % [tr(str(s.blurb)), tr("contrato %s") % Core.fmt_money(int(s.hire)), tr("dia %s · %s") % [Core.fmt_money(int(s.wage)), st]], 15, Color(0.25, 0.2, 0.12))
		info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		if not hired:
			row.add_child(_btn(tr("Contratar"), _hire_role.bind(role)))
	var q: Dictionary = Economy.QUESTS.cocos_rita
	var qs := str(Core.quests.get("cocos_rita", ""))
	var qstate := tr("disponível")
	if qs == "active":
		qstate = tr("aceita")
	elif qs == "done":
		qstate = tr("entregue")
	_label(body, "%s — %s (%s)  %s" % [tr(str(q.title)), tr(str(q.desc)), qstate, tr("paga %s") % Core.fmt_money(int(q.reward))], 16, Color(0.15, 0.2, 0.16))

func _build_summary() -> void:
	summary = Control.new()
	summary.set_anchors_preset(Control.PRESET_FULL_RECT)
	summary.visible = false
	summary.mouse_filter = Control.MOUSE_FILTER_STOP
	var dim := ColorRect.new()
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0.02, 0.08, 0.1, 0.55)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	summary.add_child(dim)
	var box := PanelContainer.new()
	box.set_anchors_preset(Control.PRESET_CENTER)
	box.offset_left = -360
	box.offset_top = -250
	box.offset_right = 360
	box.offset_bottom = 250
	var st := StyleBoxFlat.new()
	st.bg_color = Color(0.98, 0.95, 0.88, 0.98)
	st.set_corner_radius_all(16)
	st.content_margin_left = 20
	st.content_margin_right = 20
	st.content_margin_top = 16
	st.content_margin_bottom = 16
	box.add_theme_stylebox_override("panel", st)
	summary.add_child(box)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 6)
	box.add_child(vb)
	summary_body = vb
	# O resumo é filho do HUD, não deste painel, para aparecer com o escritório fechado.
	summary.visible = false

func attach_summary(parent: Control) -> void:
	if summary.get_parent():
		summary.get_parent().remove_child(summary)
	parent.add_child(summary)

func show_day_summary(data: Dictionary) -> void:
	while summary_body.get_child_count() > 0:
		var c := summary_body.get_child(0)
		summary_body.remove_child(c)
		c.free()
	_label(summary_body, tr("Fechamento do dia %d") % int(data.get("day", Core.day)), 28, Color(0.08, 0.32, 0.36)).horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var income := int(data.get("income", 0))
	var expense := int(data.get("expense", 0))
	_label(summary_body, tr("Entradas %s") % Core.fmt_money(income, true), 20, Color(0.1, 0.4, 0.18))
	_label(summary_body, tr("Saídas %s") % Core.fmt_money(-expense), 20, Color(0.45, 0.14, 0.1))
	_label(summary_body, tr("Resultado %s") % Core.fmt_money(income - expense, true), 22, Color(0.1, 0.25, 0.28))
	var cats: Dictionary = data.get("cats", {})
	for c in Economy.CAT_NAME:
		if not cats.has(c):
			continue
		_label(summary_body, "%s   %s" % [tr(str(Economy.CAT_NAME[c])), Core.fmt_money(int(cats[c]), true)], 16, Color(0.2, 0.18, 0.12))
	var lines: Array = data.get("lines", [])
	if not lines.is_empty():
		_label(summary_body, tr("Últimos lançamentos"), 18, Color(0.1, 0.35, 0.32))
	var start := maxi(0, lines.size() - 6)
	for i in range(start, lines.size()):
		var line: Dictionary = lines[i]
		_label(summary_body, "%s   %s" % [str(line.get("r", "")), Core.fmt_money(int(line.get("a", 0)), true)], 15, Color(0.18, 0.16, 0.12))
	var close := Button.new()
	close.text = tr("Continuar o dia")
	close.focus_mode = Control.FOCUS_NONE
	close.custom_minimum_size = Vector2(0, 46)
	close.add_theme_font_size_override("font_size", 20)
	close.pressed.connect(func(): summary.visible = false)
	summary_body.add_child(close)
	summary.visible = true

func _buy(id: String, qty: int) -> void:
	Core.buy_supply(id, qty)
	call_deferred("refresh")

func _pick_room(i: int) -> void:
	room_focus = i
	call_deferred("refresh")

func _upgrade(cat: String) -> void:
	if Core.upgrade_room(room_focus, cat):
		get_tree().call_group("audio", "sfx", "coin")
	call_deferred("refresh")

func _hire_role(role: String) -> void:
	if Core.hire(role):
		get_tree().call_group("audio", "sfx", "coin")
	call_deferred("refresh")
