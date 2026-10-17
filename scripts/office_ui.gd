class_name OfficeUI
extends Control
## Escritório da pousada: caixa do dia, insumos, melhorias dos quartos e equipe.
## v0.4: tema UiTheme (fonte grande, cartões arredondados, ícones), painel do tamanho do conteúdo.

const T := preload("res://scripts/ui_theme.gd")
const PANEL_W := 1060.0
const BODY_MAX_H := 400.0

var tab := "caixa"
var room_focus := 0
var body: VBoxContainer
var scroll: ScrollContainer
var title_l: Label
var chips: HBoxContainer
var tab_btns := {}
var summary: Control
var summary_body: VBoxContainer

func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	theme = T.get_theme()
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)
	var panel := PanelContainer.new()
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	panel.custom_minimum_size = Vector2(PANEL_W, 0)
	var ps := T.box(T.SAND, 24, T.WOOD, 3, 22, 0)
	ps.content_margin_left = 0
	ps.content_margin_right = 0
	ps.content_margin_top = 0
	ps.content_margin_bottom = 18
	panel.add_theme_stylebox_override("panel", ps)
	center.add_child(panel)
	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 14)
	panel.add_child(root)
	# cabeçalho de madeira: ícone + título à esquerda, saldo/estrelas/dia à direita
	var head := PanelContainer.new()
	var hs := T.box(T.WOOD, 22, T.WOOD_DARK, 0, 0, 22)
	hs.corner_radius_bottom_left = 0
	hs.corner_radius_bottom_right = 0
	hs.border_width_bottom = 4
	hs.border_color = T.WOOD_DARK
	head.add_theme_stylebox_override("panel", hs)
	root.add_child(head)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 14)
	head.add_child(hb)
	hb.add_child(_icon("bangalo", 44, Color(1, 0.93, 0.78)))
	title_l = _lbl(hb, "Escritório da Pousada", T.FS_TITLE, Color(1, 0.97, 0.9), true)
	title_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.35))
	title_l.add_theme_constant_override("shadow_offset_y", 2)
	chips = HBoxContainer.new()
	chips.add_theme_constant_override("separation", 10)
	chips.alignment = BoxContainer.ALIGNMENT_END
	hb.add_child(chips)
	# abas com ícone
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 10)
	var tabs_m := _margin(tabs, 22, 0)
	root.add_child(tabs_m)
	for pair in [["caixa", "Caixa"], ["insumos", "Insumos"], ["bangalo", "Bangalôs"], ["equipe", "Equipe"]]:
		var b := Button.new()
		b.theme_type_variation = "TabButton"
		b.text = pair[1]
		b.icon = T.icon(pair[0])
		b.expand_icon = false
		b.add_theme_constant_override("icon_max_width", 32)
		b.toggle_mode = true
		b.focus_mode = Control.FOCUS_ALL
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.custom_minimum_size = Vector2(0, 58)
		var id: String = pair[0]
		b.pressed.connect(func():
			tab = id
			call_deferred("refresh"))
		tabs.add_child(b)
		tab_btns[id] = b
	# corpo com rolagem (a altura acompanha o conteúdo até BODY_MAX_H)
	scroll = ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.custom_minimum_size = Vector2(0, 200)
	root.add_child(_margin(scroll, 22, 0))
	body = VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 12)
	scroll.add_child(body)
	# rodapé
	var foot := HBoxContainer.new()
	foot.add_theme_constant_override("separation", 12)
	root.add_child(_margin(foot, 22, 0))
	var tip := _fill(foot, "B abre e fecha o escritório  ·  Esc volta ao jogo", T.FS_SMALL, T.TEXT_SOFT)
	tip.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	var close := Button.new()
	close.theme_type_variation = "SoftButton"
	close.text = "Fechar"
	close.custom_minimum_size = Vector2(190, 52)
	close.pressed.connect(func(): get_tree().call_group("hud", "toggle_shop"))
	foot.add_child(close)
	_build_summary()
	visible = false

# ------------------------------------------------------------------ helpers
func _lbl(parent: Node, t: String, fs: int, c: Color, strong := false, wrap := false) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", fs)
	l.add_theme_color_override("font_color", c)
	if strong:
		l.add_theme_font_override("font", T.bold())
	if wrap:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		l.custom_minimum_size.x = 220
	parent.add_child(l)
	return l

## Texto de uma linha que ocupa o espaço livre e corta com reticências se faltar lugar.
func _fill(parent: Node, t: String, fs: int, c: Color, strong := false) -> Label:
	var l := _lbl(parent, t, fs, c, strong)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	l.clip_text = true
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	return l

# Compatibilidade com o código antigo.
func _label(parent: Node, t: String, fs: int, c: Color) -> Label:
	return _lbl(parent, t, fs, c)

func _icon(id: String, sz: int, c: Color) -> Control:
	var tr_ := TextureRect.new()
	tr_.texture = T.icon(id)
	tr_.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr_.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr_.custom_minimum_size = Vector2(sz, sz)
	tr_.self_modulate = c
	tr_.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	tr_.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return tr_

## Ícone dentro de um círculo colorido.
func _badge(id: String, sz: int, bg: Color, fg := Color.WHITE) -> Control:
	var p := PanelContainer.new()
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.set_corner_radius_all(sz)
	s.corner_detail = 12
	var pad := sz * 0.2
	s.content_margin_left = pad
	s.content_margin_right = pad
	s.content_margin_top = pad
	s.content_margin_bottom = pad
	p.add_theme_stylebox_override("panel", s)
	p.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	p.add_child(_icon(id, int(sz * 0.6), fg))
	return p

func _margin(c: Control, h: int, v: int) -> MarginContainer:
	var m := MarginContainer.new()
	m.add_theme_constant_override("margin_left", h)
	m.add_theme_constant_override("margin_right", h)
	m.add_theme_constant_override("margin_top", v)
	m.add_theme_constant_override("margin_bottom", v)
	m.add_child(c)
	return m

func _card(parent: Node, sep := 8) -> VBoxContainer:
	var p := PanelContainer.new()
	p.theme_type_variation = "Card"
	p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(p)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", sep)
	p.add_child(v)
	return v

func _hrow(parent: Node, sep := 12) -> HBoxContainer:
	var r := HBoxContainer.new()
	r.add_theme_constant_override("separation", sep)
	parent.add_child(r)
	return r

func _chip(parent: Node, text: String, fg: Color, bg: Color, icon_id := "") -> PanelContainer:
	var p := PanelContainer.new()
	p.theme_type_variation = "Chip"
	var s := T.box(bg, 12, Color(), 0, 0, 12)
	s.content_margin_top = 4
	s.content_margin_bottom = 4
	p.add_theme_stylebox_override("panel", s)
	p.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 6)
	p.add_child(h)
	if icon_id != "":
		h.add_child(_icon(icon_id, 22, fg))
	var l := _lbl(h, text, T.FS_SMALL + 1, fg, true)
	l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	parent.add_child(p)
	return p

func _btn(text: String, cb: Callable, soft := false, icon_id := "") -> Button:
	var b := Button.new()
	b.text = text
	if soft:
		b.theme_type_variation = "SoftButton"
	if icon_id != "":
		b.icon = T.icon(icon_id)
	b.focus_mode = Control.FOCUS_ALL
	b.custom_minimum_size = Vector2(150, 48)
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	b.pressed.connect(cb)
	return b

func _section(text: String, icon_id := "") -> void:
	var r := _hrow(body, 10)
	if icon_id != "":
		r.add_child(_icon(icon_id, 30, T.TEAL_DARK))
	_lbl(r, text, T.FS_H2, T.TEAL_DARK, true, true).vertical_alignment = VERTICAL_ALIGNMENT_CENTER

func _stat(parent: Node, icon_id: String, cap: String, value: String, col: Color) -> void:
	var v := _card(parent, 2)
	var r := _hrow(v, 12)
	r.add_child(_badge(icon_id, 52, col))
	var vv := VBoxContainer.new()
	vv.add_theme_constant_override("separation", -2)
	r.add_child(vv)
	_lbl(vv, cap, T.FS_SMALL, T.TEXT_SOFT)
	var l := _lbl(vv, value, 32, col, true)
	l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED

func _clear_body() -> void:
	while body.get_child_count() > 0:
		var c := body.get_child(0)
		body.remove_child(c)
		c.free()

# ------------------------------------------------------------------ abas
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
	for id in tab_btns:
		tab_btns[id].set_pressed_no_signal(id == tab or (tab not in tab_btns and id == "caixa"))
	while chips.get_child_count() > 0:
		var c := chips.get_child(0)
		chips.remove_child(c)
		c.free()
	var chip_bg := Color(0, 0, 0, 0.22)
	_chip(chips, Core.fmt_money(Core.money), Color(0.8, 1.0, 0.75), chip_bg, "caixa")
	_chip(chips, "★ %.1f" % Core.stars(), Color(1.0, 0.88, 0.45), chip_bg)
	_chip(chips, tr("Dia %d  %s") % [Core.day, Core.clock_text()], Color(1, 0.97, 0.9), chip_bg)
	match tab:
		"insumos":
			_fill_supplies()
		"bangalo":
			_fill_rooms()
		"equipe":
			_fill_staff()
		_:
			_fill_ledger()
	call_deferred("_fit")

## Ajusta a altura da área rolável ao conteúdo (sem grandes áreas vazias).
func _fit() -> void:
	if body == null:
		return
	var h := body.get_combined_minimum_size().y
	scroll.custom_minimum_size.y = clampf(h + 4.0, 120.0, BODY_MAX_H)

func _fill_ledger() -> void:
	var net := Core.day_income - Core.day_expense
	var stats := _hrow(body, 12)
	_stat(stats, "diaria", tr("Entradas de hoje"), Core.fmt_money(Core.day_income, true), T.GOOD)
	_stat(stats, "compra", tr("Saídas de hoje"), Core.fmt_money(-Core.day_expense), T.BAD)
	_stat(stats, "caixa", tr("Saldo do dia"), Core.fmt_money(net, true), T.TEAL if net >= 0 else T.BAD)
	var cats := {}
	for line in Core.ledger_today:
		var c: String = str(line.get("c", "outro"))
		cats[c] = int(cats.get(c, 0)) + int(line.get("a", 0))
	var cols := _hrow(body, 12)
	var left := _card(cols, 6)
	left.get_parent().size_flags_stretch_ratio = 0.8
	var lh := _hrow(left, 8)
	_lbl(lh, tr("Por categoria"), T.FS_H2, T.TEAL_DARK, true)
	if cats.is_empty():
		_lbl(left, tr("Ainda sem movimento hoje."), T.FS_BODY, T.TEXT_SOFT, false, true)
	for c in Economy.CAT_NAME:
		if not cats.has(c):
			continue
		var r := _hrow(left, 10)
		var v := int(cats[c])
		r.add_child(_icon(c, 28, T.WOOD))
		var n := _fill(r, tr(Economy.CAT_NAME[c]), T.FS_BODY, T.TEXT)
		var a := _lbl(r, Core.fmt_money(v, true), T.FS_BODY, T.GOOD if v >= 0 else T.BAD, true)
		a.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	var right := _card(cols, 6)
	_lbl(right, tr("Lançamentos"), T.FS_H2, T.TEAL_DARK, true)
	var lines: Array = Core.ledger_today.duplicate()
	lines.reverse()
	var n_ := mini(10, lines.size())
	if n_ == 0:
		_lbl(right, tr("Nada lançado hoje. Diárias, bar, quiosque e compras aparecem aqui."), T.FS_BODY, T.TEXT_SOFT, false, true)
	for i in n_:
		var line: Dictionary = lines[i]
		var r := _hrow(right, 10)
		r.add_child(_icon(str(line.get("c", "outro")), 26, T.WOOD))
		var d := _fill(r, str(line.r), T.FS_BODY, T.TEXT)
		d.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		var a := _lbl(r, Core.fmt_money(int(line.a), true), T.FS_BODY, T.GOOD if int(line.a) >= 0 else T.BAD, true)
		a.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED

func _fill_supplies() -> void:
	_section(tr("Mercadinho e padaria — o estoque vale para o bar e o quiosque."), "insumos")
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 12)
	body.add_child(grid)
	for id in Economy.SUPPLIES:
		var s: Dictionary = Economy.SUPPLIES[id]
		var stock := int(Core.stock.get(id, 0))
		var v := _card(grid, 8)
		v.get_parent().size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var top := _hrow(v, 10)
		top.add_child(_badge(id, 50, T.TEAL))
		var nv := VBoxContainer.new()
		nv.add_theme_constant_override("separation", 0)
		nv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		top.add_child(nv)
		_lbl(nv, tr(str(s.name)), T.FS_H2, T.TEXT, true)
		_lbl(nv, tr("%s cada · fardo %s") % [Core.fmt_money(int(s.cost)), Core.fmt_money(int(s.cost) * Economy.PACK)], T.FS_SMALL, T.TEXT_SOFT)
		var low := stock <= 2
		_chip(top, tr("estoque %d") % stock, Color.WHITE, T.BAD if low else T.GOOD)
		var br := _hrow(v, 8)
		var b1 := _btn(tr("+1"), _buy.bind(id, 1), true)
		b1.custom_minimum_size = Vector2(80, 46)
		br.add_child(b1)
		var b2 := _btn(tr("Fardo ×%d") % Economy.PACK, _buy.bind(id, Economy.PACK))
		b2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		br.add_child(b2)
	_section(tr("Cardápio — margem por prato"), "prato")
	var menu := _card(body, 4)
	for id in Economy.BAR_MENU:
		var d: Dictionary = Economy.dish(id)
		var r := _hrow(menu, 12)
		var ok := Core.can_make(id)
		r.add_child(_icon("prato", 30, T.TEAL if ok else Color(0.6, 0.55, 0.5)))
		var n := _lbl(r, tr(str(d.name)), T.FS_BODY, T.TEXT, true)
		n.custom_minimum_size = Vector2(210, 0)
		_lbl(r, Core.fmt_money(int(d.price)), T.FS_BODY, T.TEXT).custom_minimum_size = Vector2(90, 0)
		var m := _fill(r, tr("margem %s · custo %s") % [Core.fmt_money(Economy.dish_margin(id)), Core.fmt_money(Economy.dish_cost(id))], T.FS_SMALL, T.TEXT_SOFT)
		m.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		_chip(r, tr("bar e quiosque") if id in Economy.KIOSK_MENU else tr("só no bar"), T.WOOD_DARK, T.SAND_DARK)
		_chip(r, tr("pronto") if ok else tr("falta insumo"), Color.WHITE, T.GOOD if ok else T.BAD)

func _tier_dots(parent: Node, tier: int, mx: int) -> void:
	var t := ""
	for k in mx:
		t += "●" if k < tier else "○"
	var l := _lbl(parent, t, T.FS_BODY, T.CORAL, true)
	l.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED

func _fill_rooms() -> void:
	room_focus = clampi(room_focus, 0, Core.rooms.size() - 1)
	var pick := _hrow(body, 10)
	for i in Core.rooms.size():
		var b := _btn(tr("Bangalô %d") % (i + 1), _pick_room.bind(i), true, "bangalo")
		b.toggle_mode = true
		b.theme_type_variation = "TabButton"
		b.add_theme_font_size_override("font_size", T.FS_BODY)
		b.set_pressed_no_signal(i == room_focus)
		pick.add_child(b)
	var rate := Core.nightly_rate(room_focus)
	var hdr := _hrow(pick, 8)
	hdr.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hdr.alignment = BoxContainer.ALIGNMENT_END
	_lbl(hdr, tr("Diária deste quarto"), T.FS_BODY, T.TEXT_SOFT).vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	var rl := _lbl(hdr, Core.fmt_money(rate), 34, T.TEAL_DARK, true)
	rl.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 12)
	body.add_child(grid)
	for cat in Economy.UPGRADES:
		var def: Dictionary = Economy.UPGRADES[cat]
		var tier: int = int(Core.rooms[room_focus].upgrades.get(cat, 0))
		var mx := Economy.max_tier(cat)
		var v := _card(grid, 6)
		var top := _hrow(v, 12)
		top.add_child(_badge(cat, 54, T.WOOD if tier < mx else T.CORAL))
		var nv := VBoxContainer.new()
		nv.add_theme_constant_override("separation", 0)
		nv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		top.add_child(nv)
		var tr_ := _hrow(nv, 10)
		_lbl(tr_, tr(str(def.name)), T.FS_H2, T.TEXT, true)
		_tier_dots(tr_, tier, mx)
		_lbl(nv, tr(Economy.tier_name(cat, tier)), T.FS_BODY, T.TEXT_SOFT)
		var nxt := Economy.next_cost(cat, tier)
		if nxt < 0:
			_chip(top, tr("no máximo · +%s") % Core.fmt_money(Economy.tier_rate(cat, tier)), Color.WHITE, T.CORAL)
		else:
			var gain: int = Economy.tier_rate(cat, tier + 1) - Economy.tier_rate(cat, tier)
			var nr := _hrow(v, 10)
			var nl := _fill(nr, "→ %s" % tr(Economy.tier_name(cat, tier + 1)), T.FS_BODY, T.TEXT)
			nl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			_chip(nr, tr("+%s/noite") % Core.fmt_money(gain), T.GOOD, Color(0.85, 0.95, 0.85))
			var b := _btn(tr("Melhorar  %s") % Core.fmt_money(nxt), _upgrade.bind(cat))
			b.disabled = Core.money < nxt
			nr.add_child(b)
	var extra := _hrow(body, 12)
	var hv := _card(extra, 6)
	var hr := _hrow(hv, 12)
	hr.add_child(_badge("redes", 50, T.TEAL))
	var hl := _fill(hr, tr("Redes %d/%d") % [Core.redes, Core.MAX_REDES], T.FS_BODY, T.TEXT, true)
	hl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	var bh := _btn(tr("Comprar  %s") % Core.fmt_money(Core.REDE_PRICE), func():
		if Core.buy_rede():
			get_tree().call_group("audio", "sfx", "coin")
		call_deferred("refresh"))
	bh.disabled = Core.redes >= Core.MAX_REDES
	hr.add_child(bh)
	if Core.rooms.size() < Economy.BUNGALOW_MAX:
		var gv := _card(extra, 6)
		var gr := _hrow(gv, 12)
		gr.add_child(_badge("novo", 50, T.TEAL))
		var gl := _fill(gr, tr("Novo bangalô"), T.FS_BODY, T.TEXT, true)
		gl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		gr.add_child(_btn(tr("Construir  %s") % Core.fmt_money(Economy.BUNGALOW_COST), func():
			if Core.build_bungalow():
				get_tree().call_group("audio", "sfx", "coin")
				room_focus = Core.rooms.size() - 1
			call_deferred("refresh")))

func _fill_staff() -> void:
	_section(tr("Contratar gente da vila. O salário sai no fechamento do dia."), "equipe")
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 12)
	body.add_child(grid)
	for role in Economy.STAFF:
		var s: Dictionary = Economy.STAFF[role]
		var hired := bool(Core.staff.get(role, false))
		var v := _card(grid, 6)
		var top := _hrow(v, 12)
		top.add_child(_badge(role, 58, T.TEAL if hired else T.WOOD))
		var nv := VBoxContainer.new()
		nv.add_theme_constant_override("separation", 0)
		nv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		top.add_child(nv)
		_lbl(nv, tr(str(s.name)), T.FS_H2, T.TEXT, true)
		_lbl(nv, tr(str(s.blurb)), T.FS_BODY, T.TEXT_SOFT, false, true)
		var br := _hrow(v, 10)
		_chip(br, tr("contrato %s") % Core.fmt_money(int(s.hire)), T.WOOD_DARK, T.SAND_DARK)
		_chip(br, tr("salário %s/dia") % Core.fmt_money(int(s.wage)), T.WOOD_DARK, T.SAND_DARK)
		var sp := Control.new()
		sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		br.add_child(sp)
		if hired:
			_chip(br, tr("na equipe"), Color.WHITE, T.GOOD)
		else:
			br.add_child(_btn(tr("Contratar"), _hire_role.bind(role)))
	_section(tr("Missões da vila"), "missao")
	var q: Dictionary = Economy.QUESTS.cocos_rita
	var qs := str(Core.quests.get("cocos_rita", ""))
	var qstate := tr("disponível")
	var qcol := T.TEAL
	if qs == "active":
		qstate = tr("aceita")
		qcol = T.CORAL
	elif qs == "done":
		qstate = tr("entregue")
		qcol = T.GOOD
	var qv := _card(body, 4)
	var qr := _hrow(qv, 12)
	qr.add_child(_badge("missao", 50, T.WOOD))
	var qn := VBoxContainer.new()
	qn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	qr.add_child(qn)
	_lbl(qn, tr(str(q.title)), T.FS_H2, T.TEXT, true)
	_lbl(qn, tr(str(q.desc)), T.FS_BODY, T.TEXT_SOFT, false, true)
	_chip(qr, tr("paga %s") % Core.fmt_money(int(q.reward)), T.GOOD, Color(0.85, 0.95, 0.85))
	_chip(qr, qstate, Color.WHITE, qcol)

# ------------------------------------------------------------------ fechamento do dia
func _build_summary() -> void:
	summary = Control.new()
	summary.set_anchors_preset(Control.PRESET_FULL_RECT)
	summary.visible = false
	summary.mouse_filter = Control.MOUSE_FILTER_STOP
	summary.theme = T.get_theme()
	var dim := ColorRect.new()
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.color = Color(0.02, 0.08, 0.1, 0.55)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	summary.add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	summary.add_child(center)
	var box := PanelContainer.new()
	box.custom_minimum_size = Vector2(820, 0)
	var st := T.box(T.SAND, 24, T.WOOD, 3, 24, 24)
	st.content_margin_top = 18
	st.content_margin_bottom = 20
	box.add_theme_stylebox_override("panel", st)
	center.add_child(box)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 12)
	box.add_child(vb)
	summary_body = vb
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
	var head := _hrow(summary_body, 12)
	head.alignment = BoxContainer.ALIGNMENT_CENTER
	head.add_child(_badge("caixa", 56, T.WOOD))
	_lbl(head, tr("Fechamento do dia %d") % int(data.get("day", Core.day)), T.FS_TITLE, T.TEAL_DARK, true)
	var income := int(data.get("income", 0))
	var expense := int(data.get("expense", 0))
	var net := income - expense
	var stats := _hrow(summary_body, 12)
	_stat(stats, "diaria", tr("Entradas"), Core.fmt_money(income, true), T.GOOD)
	_stat(stats, "compra", tr("Saídas"), Core.fmt_money(-expense), T.BAD)
	_stat(stats, "caixa", tr("Resultado"), Core.fmt_money(net, true), T.TEAL if net >= 0 else T.BAD)
	var cols := _hrow(summary_body, 12)
	var cats: Dictionary = data.get("cats", {})
	var left := _card(cols, 4)
	_lbl(left, tr("Por categoria"), T.FS_H2, T.TEAL_DARK, true)
	var out_cats := ["insumo", "upgrade", "compra", "folha", "multa"]
	for c in Economy.CAT_NAME:
		if not cats.has(c):
			continue
		var v := int(cats[c])
		if c in out_cats and v > 0:
			v = -v
		var r := _hrow(left, 10)
		r.add_child(_icon(c, 26, T.WOOD))
		var n := _fill(r, tr(str(Economy.CAT_NAME[c])), T.FS_BODY, T.TEXT)
		_lbl(r, Core.fmt_money(v, true), T.FS_BODY, T.GOOD if v >= 0 else T.BAD, true).auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	var lines: Array = data.get("lines", [])
	if not lines.is_empty():
		var right := _card(cols, 4)
		right.get_parent().size_flags_stretch_ratio = 1.4
		_lbl(right, tr("Últimos lançamentos"), T.FS_H2, T.TEAL_DARK, true)
		var start := maxi(0, lines.size() - 6)
		for i in range(start, lines.size()):
			var line: Dictionary = lines[i]
			var r := _hrow(right, 10)
			r.add_child(_icon(str(line.get("c", "outro")), 24, T.WOOD))
			var d := _fill(r, str(line.get("r", "")), T.FS_BODY, T.TEXT)
			d.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
			var a := int(line.get("a", 0))
			_lbl(r, Core.fmt_money(a, true), T.FS_BODY, T.GOOD if a >= 0 else T.BAD, true).auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	var close := Button.new()
	close.text = tr("Continuar o dia")
	close.icon = T.icon("redes")
	close.custom_minimum_size = Vector2(320, 58)
	close.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	close.add_theme_font_size_override("font_size", T.FS_H2)
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
