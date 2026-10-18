extends Control
class_name PhoneUI
## Celular do herói (v0.7): toda a gestão do negócio por apps — Expansões, Mercado, Cardápio,
## Bangalôs, Equipe e Caixa. Abre e fecha com B (ou Y no controle). Substitui o escritório.

const T: = preload("res://scripts/ui_theme.gd")
const W: = 420.0
const H: = 680.0
const INK: = Color(0.16, 0.13, 0.2)
const INK_SOFT: = Color(0.42, 0.38, 0.46)
const SCREEN_TOP: = Color(0.62, 0.9, 1.0)
const SCREEN_BOT: = Color(1.0, 0.95, 0.84)
const GOOD: = Color(0.12, 0.62, 0.32)
const BAD: = Color(0.85, 0.28, 0.22)

## id, nome, cor, ícone
const APPS: = [
	["expansoes", "Expansões", Color(1.0, 0.45, 0.35), "upgrade"],
	["mercado", "Mercado", Color(0.15, 0.72, 0.45), "compra"],
	["cardapio", "Cardápio", Color(1.0, 0.72, 0.18), "prato"],
	["bangalos", "Bangalôs", Color(0.2, 0.6, 0.95), "cama"],
	["equipe", "Equipe", Color(0.6, 0.4, 0.9), "equipe"],
	["caixa", "Caixa", Color(0.1, 0.65, 0.68), "caixa"],
]

var app: = ""
var room_focus: = 0
var body_frame: Control
var screen: VBoxContainer
var status_l: Label
var _phone: Control
var _tween: Tween

func _ready() -> void :
	add_to_group("phone")
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	theme = T.get_theme()
	_phone = PanelContainer.new()
	_phone.mouse_filter = Control.MOUSE_FILTER_STOP
	_phone.custom_minimum_size = Vector2(W, H)
	_phone.size = Vector2(W, H)
	var bezel: = StyleBoxFlat.new()
	bezel.bg_color = Color(0.13, 0.12, 0.2)
	bezel.set_corner_radius_all(46)
	bezel.set_border_width_all(4)
	bezel.border_color = Color(0.32, 0.3, 0.45)
	bezel.shadow_color = Color(0, 0, 0, 0.45)
	bezel.shadow_size = 24
	bezel.shadow_offset = Vector2(0, 10)
	bezel.set_content_margin_all(14)
	bezel.corner_detail = 12
	_phone.add_theme_stylebox_override("panel", bezel)
	add_child(_phone)
	var scr: = Panel.new()
	scr.clip_contents = true
	var grad: = GradientTexture2D.new()
	var g: = Gradient.new()
	g.colors = PackedColorArray([SCREEN_TOP, SCREEN_BOT])
	grad.gradient = g
	grad.fill_from = Vector2(0, 0)
	grad.fill_to = Vector2(0, 1)
	var sb: = StyleBoxTexture.new()
	sb.texture = grad
	scr.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	_phone.add_child(scr)
	var bg: = TextureRect.new()
	bg.texture = grad
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.stretch_mode = TextureRect.STRETCH_SCALE
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	scr.add_child(bg)
	var round_mask: = StyleBoxFlat.new()
	round_mask.bg_color = Color(0, 0, 0, 0)
	round_mask.set_corner_radius_all(34)
	var col: = VBoxContainer.new()
	col.set_anchors_preset(Control.PRESET_FULL_RECT)
	col.add_theme_constant_override("separation", 0)
	scr.add_child(col)
	var bar: = MarginContainer.new()
	for side in ["left", "right"]:
		bar.add_theme_constant_override("margin_" + side, 22)
	bar.add_theme_constant_override("margin_top", 10)
	bar.add_theme_constant_override("margin_bottom", 4)
	col.add_child(bar)
	status_l = _lbl(bar, "", 16, INK, true)
	screen = VBoxContainer.new()
	screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
	screen.add_theme_constant_override("separation", 0)
	col.add_child(screen)
	var home_bar: = ColorRect.new()
	home_bar.color = Color(0.13, 0.12, 0.2, 0.6)
	home_bar.custom_minimum_size = Vector2(120, 5)
	home_bar.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	var hb_m: = MarginContainer.new()
	hb_m.add_theme_constant_override("margin_bottom", 8)
	hb_m.add_theme_constant_override("margin_top", 6)
	hb_m.add_child(home_bar)
	col.add_child(hb_m)
	visible = false
	resized.connect(_place)
	Core.money_changed.connect(func(_v): _refresh_if_open())
	Core.stock_changed.connect(_refresh_if_open)
	Core.expansion_bought.connect(func(_id): _refresh_if_open())
	Core.staff_changed.connect(_refresh_if_open)
	Core.upgrades_changed.connect(func(_r): _refresh_if_open())

func _place() -> void :
	var vs: = size
	_phone.size = Vector2(W, minf(H, vs.y - 30.0))
	_phone.position = Vector2(vs.x - W - 60.0, (vs.y - _phone.size.y) * 0.5)

func _refresh_if_open() -> void :
	if visible:
		call_deferred("refresh")

# ------------------------------------------------------------------ abrir / fechar
func open(which: String = "", arg: int = -1) -> void :
	if arg >= 0:
		room_focus = arg
	app = which
	visible = true
	_place()
	refresh()
	if _tween:
		_tween.kill()
	var end_y: = _phone.position.y
	_phone.position.y = size.y + 20.0
	_tween = create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_tween.tween_property(_phone, "position:y", end_y, 0.28)

func close() -> void :
	visible = false

func back() -> void :
	if app == "":
		close()
	else:
		app = ""
		refresh()

## Compatibilidade com as abas do antigo escritório.
static func app_for_tab(tab: String) -> String:
	match tab:
		"insumos":
			return "mercado"
		"bangalo":
			return "bangalos"
		"equipe":
			return "equipe"
		"caixa":
			return "caixa"
		"expansoes":
			return "expansoes"
	return ""

# ------------------------------------------------------------------ helpers de UI
func _lbl(parent: Node, t: String, fs: int, c: Color, strong: = false, wrap: = false) -> Label:
	var l: = Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", fs)
	l.add_theme_color_override("font_color", c)
	l.add_theme_font_override("font", T.bold() if strong else T.font())
	if wrap:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(l)
	return l

func _box(c: Color, r: = 18, pad: = 12) -> StyleBoxFlat:
	var s: = StyleBoxFlat.new()
	s.bg_color = c
	s.set_corner_radius_all(r)
	s.corner_detail = 8
	s.set_content_margin_all(pad)
	return s

func _card(parent: Node, tint: = Color(1, 1, 1, 0.92)) -> VBoxContainer:
	var p: = PanelContainer.new()
	var st: = _box(tint, 18, 12)
	st.shadow_color = Color(0, 0, 0, 0.12)
	st.shadow_size = 4
	st.shadow_offset = Vector2(0, 2)
	p.add_theme_stylebox_override("panel", st)
	parent.add_child(p)
	var v: = VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	p.add_child(v)
	return v

func _row(parent: Node, sep: = 8) -> HBoxContainer:
	var h: = HBoxContainer.new()
	h.add_theme_constant_override("separation", sep)
	parent.add_child(h)
	return h

func _icon(id: String, sz: int, c: Color) -> Control:
	var tr_: = TextureRect.new()
	tr_.texture = T.icon(id)
	tr_.custom_minimum_size = Vector2(sz, sz)
	tr_.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr_.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr_.modulate = c
	tr_.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return tr_

func _badge(parent: Node, id: String, bg: Color, sz: = 44) -> void :
	var p: = PanelContainer.new()
	p.add_theme_stylebox_override("panel", _box(bg, 14, 6))
	p.custom_minimum_size = Vector2(sz, sz)
	p.add_child(_icon(id, sz - 14, Color.WHITE))
	parent.add_child(p)

func _btn(parent: Node, text: String, cb: Callable, c: = Color(0.1, 0.65, 0.68), enabled: = true) -> Button:
	var b: = Button.new()
	b.text = text
	b.add_theme_font_size_override("font_size", 17)
	var n: = _box(c, 14, 8)
	n.border_width_bottom = 4
	n.border_color = c.darkened(0.3)
	var hv: = n.duplicate()
	hv.bg_color = c.lightened(0.12)
	var pr: = n.duplicate()
	pr.bg_color = c.darkened(0.15)
	pr.border_width_bottom = 1
	var ds: = n.duplicate()
	ds.bg_color = Color(0.72, 0.7, 0.74)
	ds.border_color = Color(0.55, 0.53, 0.58)
	b.add_theme_stylebox_override("normal", n)
	b.add_theme_stylebox_override("hover", hv)
	b.add_theme_stylebox_override("pressed", pr)
	b.add_theme_stylebox_override("disabled", ds)
	b.add_theme_stylebox_override("focus", hv)
	b.disabled = not enabled
	b.pressed.connect(func():
		get_tree().call_group("audio", "sfx", "click")
		cb.call())
	parent.add_child(b)
	return b

func _chip(parent: Node, text: String, fg: Color, bg: Color) -> void :
	var p: = PanelContainer.new()
	var st: = _box(bg, 10, 4)
	st.content_margin_left = 10
	st.content_margin_right = 10
	p.add_theme_stylebox_override("panel", st)
	p.size_flags_horizontal = Control.SIZE_SHRINK_END
	p.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_lbl(p, text, 15, fg, true)
	parent.add_child(p)

func _expand(c: Control) -> Control:
	c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return c

# ------------------------------------------------------------------ telas
func refresh() -> void :
	if screen == null:
		return
	for ch in screen.get_children():
		screen.remove_child(ch)
		ch.queue_free()
	status_l.text = "%s     %s   ★ %.1f" % [Core.clock_text(), Core.fmt_money(Core.money), Core.stars()]
	if app == "":
		_home()
		return
	var info: Array = APPS.filter(func(a): return a[0] == app)
	if info.is_empty():
		app = ""
		_home()
		return
	var a: Array = info[0]
	var head: = PanelContainer.new()
	var hs: = _box(a[2], 0, 10)
	head.add_theme_stylebox_override("panel", hs)
	screen.add_child(head)
	var hr: = _row(head, 10)
	var bk: = Button.new()
	bk.text = "‹"
	bk.flat = true
	bk.add_theme_font_size_override("font_size", 34)
	bk.add_theme_color_override("font_color", Color.WHITE)
	bk.pressed.connect(back)
	hr.add_child(bk)
	hr.add_child(_icon(a[3], 30, Color.WHITE))
	_expand(_lbl(hr, tr(str(a[1])), 24, Color.WHITE, true))
	var sc: = ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	screen.add_child(sc)
	var m: = MarginContainer.new()
	m.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for side in ["left", "right", "top", "bottom"]:
		m.add_theme_constant_override("margin_" + side, 12)
	sc.add_child(m)
	var list: = VBoxContainer.new()
	list.add_theme_constant_override("separation", 10)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	m.add_child(list)
	match app:
		"expansoes":
			_app_expansions(list)
		"mercado":
			_app_market(list)
		"cardapio":
			_app_menu(list)
		"bangalos":
			_app_rooms(list)
		"equipe":
			_app_staff(list)
		"caixa":
			_app_ledger(list)

func _home() -> void :
	var m: = MarginContainer.new()
	for side in ["left", "right"]:
		m.add_theme_constant_override("margin_" + side, 20)
	m.add_theme_constant_override("margin_top", 14)
	m.size_flags_vertical = Control.SIZE_EXPAND_FILL
	screen.add_child(m)
	var v: = VBoxContainer.new()
	v.add_theme_constant_override("separation", 16)
	m.add_child(v)
	var hello: = _lbl(v, tr("Quiosque Maré Alta"), 28, INK, true)
	hello.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var nx: = Core.next_expansion()
	if nx != "":
		var goal: = _card(v, Color(1, 1, 1, 0.85))
		_lbl(goal, tr("PRÓXIMA META"), 14, INK_SOFT, true)
		var gr: = _row(goal, 10)
		_badge(gr, str(Economy.EXPANSIONS[nx].get("icon", "bangalo")), Color(1.0, 0.45, 0.35), 40)
		var gv: = VBoxContainer.new()
		gv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		gr.add_child(gv)
		_lbl(gv, tr(str(Economy.EXPANSIONS[nx].name)), 19, INK, true)
		var st: Array = Core.expansion_state(nx)
		var cost: = int(Economy.EXPANSIONS[nx].cost)
		var pb: = ProgressBar.new()
		pb.max_value = cost
		pb.value = clampi(Core.money, 0, cost)
		pb.show_percentage = false
		pb.custom_minimum_size = Vector2(0, 12)
		pb.add_theme_stylebox_override("background", _box(Color(0.85, 0.85, 0.9), 6, 0))
		pb.add_theme_stylebox_override("fill", _box(GOOD if st[0] == "ready" else Color(1.0, 0.6, 0.2), 6, 0))
		gv.add_child(pb)
		_lbl(gv, tr("Pronto para comprar!") if st[0] == "ready" else str(st[1]), 15, GOOD if st[0] == "ready" else INK_SOFT, false, true)
	var grid: = GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 14)
	grid.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(grid)
	for a in APPS:
		var cell: = VBoxContainer.new()
		cell.add_theme_constant_override("separation", 4)
		grid.add_child(cell)
		var b: = Button.new()
		b.custom_minimum_size = Vector2(92, 92)
		var n: = _box(a[2], 26, 10)
		n.shadow_color = Color(0, 0, 0, 0.18)
		n.shadow_size = 5
		n.shadow_offset = Vector2(0, 3)
		var hv: = n.duplicate()
		hv.bg_color = a[2].lightened(0.15)
		b.add_theme_stylebox_override("normal", n)
		b.add_theme_stylebox_override("hover", hv)
		b.add_theme_stylebox_override("pressed", n)
		b.add_theme_stylebox_override("focus", hv)
		b.icon = T.icon(a[3])
		b.expand_icon = true
		b.add_theme_color_override("icon_normal_color", Color.WHITE)
		b.add_theme_color_override("icon_hover_color", Color.WHITE)
		b.add_theme_color_override("icon_pressed_color", Color.WHITE)
		b.add_theme_color_override("icon_focus_color", Color.WHITE)
		var id: String = a[0]
		b.pressed.connect(func():
			get_tree().call_group("audio", "sfx", "click")
			app = id
			refresh())
		cell.add_child(b)
		var l: = _lbl(cell, tr(str(a[1])), 15, INK, true)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		if a[0] == "expansoes":
			var ready_n: = 0
			for eid in Economy.EXPANSION_ORDER:
				if Core.expansion_state(eid)[0] == "ready":
					ready_n += 1
			if ready_n > 0:
				l.text = tr("Expansões") + " (%d)" % ready_n
				l.add_theme_color_override("font_color", BAD)
	var tip: = _lbl(v, tr("%s fecha o celular") % Quality.key_name("shop"), 14, INK_SOFT)
	tip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER

func _app_expansions(list: VBoxContainer) -> void :
	for id in Economy.EXPANSION_ORDER:
		var e: Dictionary = Economy.EXPANSIONS[id]
		var st: Array = Core.expansion_state(id)
		var owned: bool = st[0] == "owned"
		var c: = _card(list, Color(0.9, 1.0, 0.92, 0.95) if owned else Color(1, 1, 1, 0.94))
		var r: = _row(c, 10)
		_badge(r, str(e.get("icon", "bangalo")), GOOD if owned else (Color(1.0, 0.45, 0.35) if st[0] != "locked" else Color(0.6, 0.6, 0.66)))
		var v: = VBoxContainer.new()
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r.add_child(v)
		_lbl(v, tr(str(e.name)), 18, INK, true, true)
		_lbl(v, tr(str(e.blurb)), 14, INK_SOFT, false, true)
		var r2: = _row(c, 8)
		if owned:
			_expand(_lbl(r2, tr("✓ Já é seu"), 16, GOOD, true))
		else:
			_expand(_lbl(r2, Core.fmt_money(int(e.cost)), 18, INK, true))
			if st[0] == "ready":
				_btn(r2, tr("Comprar"), func(): Core.buy_expansion(id), Color(1.0, 0.45, 0.35))
			else:
				_chip(r2, str(st[1]), Color.WHITE, BAD if st[0] == "money" else Color(0.55, 0.55, 0.62))

func _app_market(list: VBoxContainer) -> void :
	_lbl(list, tr("Entrega na hora no quiosque. Fardos de %d.") % Economy.PACK, 15, INK_SOFT, false, true)
	for id in Economy.SUPPLIES:
		var sup: Dictionary = Economy.SUPPLIES[id]
		var used: = false
		for d in Core.kiosk_menu() + Core.bar_menu():
			if Economy.dish(d).uses.has(id):
				used = true
		var c: = _card(list)
		var r: = _row(c, 10)
		_badge(r, id, Color(0.15, 0.72, 0.45) if used else Color(0.6, 0.6, 0.66), 40)
		var v: = VBoxContainer.new()
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r.add_child(v)
		_lbl(v, tr(str(sup.name)), 18, INK, true)
		_lbl(v, tr("Estoque: %d  ·  %s cada") % [int(Core.stock.get(id, 0)), Core.fmt_money(int(sup.cost))] + ("" if used else "  ·  " + tr("ainda não usa")), 14, INK_SOFT, false, true)
		var cost: = int(sup.cost) * Economy.PACK
		_btn(r, "+%d\n%s" % [Economy.PACK, Core.fmt_money(cost)], func(): Core.buy_supply(id, Economy.PACK), Color(0.15, 0.72, 0.45), Core.money >= cost)

func _app_menu(list: VBoxContainer) -> void :
	for id in Economy.DISHES:
		var d: Dictionary = Economy.DISHES[id]
		var ok: = Core.dish_unlocked(id)
		var c: = _card(list, Color(1, 1, 1, 0.94) if ok else Color(0.92, 0.92, 0.95, 0.9))
		var r: = _row(c, 10)
		_expand(_lbl(r, tr(str(d.name)), 18, INK if ok else INK_SOFT, true))
		_lbl(r, Core.fmt_money(int(d.price)), 18, GOOD if ok else INK_SOFT, true)
		var where: = []
		if id in Core.kiosk_menu():
			where.append(tr("quiosque"))
		if Core.has("bar") and id in Core.bar_menu():
			where.append(tr("bar"))
		var info: = tr("Custo %s · margem %s") % [Core.fmt_money(Economy.dish_cost(id)), Core.fmt_money(Economy.dish_margin(id))]
		if not ok:
			info = tr("Bloqueado: compre %s") % tr(str(Economy.EXPANSIONS[Economy.DISH_UNLOCK[id]].name))
		elif where.is_empty():
			info += "  ·  " + tr("ainda não é vendido")
		else:
			info += "  ·  " + ", ".join(where)
		_lbl(c, info, 14, INK_SOFT, false, true)
		if ok and not Core.can_make(id):
			_lbl(c, tr("Sem insumos! Compre no Mercado."), 14, BAD, true)

func _app_rooms(list: VBoxContainer) -> void :
	if not Core.has("pousada"):
		var c: = _card(list)
		_lbl(c, tr("A pousada ainda é um lote à venda."), 18, INK, true, true)
		_lbl(c, tr("Compre \"%s\" em Expansões para ter bangalôs.") % tr(str(Economy.EXPANSIONS.pousada.name)), 15, INK_SOFT, false, true)
		return
	var tabs: = _row(list, 6)
	for i in Core.rooms.size():
		var idx: = i
		_btn(tabs, tr("B%d") % (i + 1), func():
			room_focus = idx
			refresh(), Color(0.2, 0.6, 0.95) if i == room_focus else Color(0.55, 0.62, 0.75))
	room_focus = clampi(room_focus, 0, maxi(0, Core.rooms.size() - 1))
	if Core.rooms.size() < Economy.BUNGALOW_MAX:
		_btn(tabs, tr("+ Novo %s") % Core.fmt_money(Economy.BUNGALOW_COST), func(): Core.build_bungalow(), Color(1.0, 0.45, 0.35), Core.money >= Economy.BUNGALOW_COST)
	var room: Dictionary = Core.rooms[room_focus]
	var info: = _card(list)
	_lbl(info, tr("Bangalô %d  ·  diária %s") % [room_focus + 1, Core.fmt_money(Core.nightly_rate(room_focus))], 18, INK, true)
	var st_txt: = {"free": tr("Livre e limpo"), "occupied": tr("Ocupado"), "dirty": tr("Sujo — precisa limpar")}
	_lbl(info, str(st_txt.get(room.state, room.state)), 15, BAD if room.state == "dirty" else INK_SOFT)
	for cat in Economy.UPGRADES:
		var tier: = int(room.upgrades.get(cat, 0))
		var c: = _card(list)
		var r: = _row(c, 10)
		_badge(r, cat, Color(0.2, 0.6, 0.95), 40)
		var v: = VBoxContainer.new()
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r.add_child(v)
		_lbl(v, tr(str(Economy.UPGRADES[cat].name)), 17, INK, true)
		_lbl(v, tr(Economy.tier_name(cat, tier)) + "  " + "●".repeat(tier) + "○".repeat(Economy.max_tier(cat) - tier), 14, INK_SOFT, false, true)
		var nc: = Economy.next_cost(cat, tier)
		if nc < 0:
			_chip(r, tr("Máximo"), Color.WHITE, GOOD)
		else:
			var rid: = room_focus
			var catc: String = cat
			_btn(r, "%s\n%s" % [tr(Economy.tier_name(cat, tier + 1)), Core.fmt_money(nc)], func(): Core.upgrade_room(rid, catc), Color(0.2, 0.6, 0.95), Core.money >= nc)

func _app_staff(list: VBoxContainer) -> void :
	for role in Economy.STAFF:
		var s: Dictionary = Economy.STAFF[role]
		var hired: = bool(Core.staff.get(role, false))
		var need: = str(s.get("req", ""))
		var c: = _card(list, Color(0.9, 1.0, 0.92, 0.95) if hired else Color(1, 1, 1, 0.94))
		var r: = _row(c, 10)
		_badge(r, "quiosque" if role == "atendente" else role, Color(0.6, 0.4, 0.9))
		var v: = VBoxContainer.new()
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r.add_child(v)
		_lbl(v, tr(str(s.name)), 18, INK, true, true)
		_lbl(v, tr(str(s.blurb)), 14, INK_SOFT, false, true)
		var r2: = _row(c, 8)
		_expand(_lbl(r2, tr("Contratar %s · salário %s/dia") % [Core.fmt_money(int(s.hire)), Core.fmt_money(int(s.wage))], 14, INK, true))
		if hired:
			_chip(r2, tr("✓ Na equipe"), Color.WHITE, GOOD)
		elif need != "" and not Core.has(need):
			_chip(r2, tr("Precisa: %s") % tr(str(Economy.EXPANSIONS[need].name)), Color.WHITE, Color(0.55, 0.55, 0.62))
		else:
			_btn(r2, tr("Contratar"), func(): Core.hire(role), Color(0.6, 0.4, 0.9), Core.money >= int(s.hire))

func _app_ledger(list: VBoxContainer) -> void :
	var top: = _card(list)
	var r: = _row(top, 8)
	var inl: = _expand(_lbl(r, tr("Entradas\n%s") % Core.fmt_money(Core.day_income), 17, GOOD, true))
	var outl: = _expand(_lbl(r, tr("Saídas\n%s") % Core.fmt_money(Core.day_expense), 17, BAD, true))
	var net: = Core.day_income - Core.day_expense
	_expand(_lbl(r, tr("Saldo do dia\n%s") % Core.fmt_money(net, true), 17, GOOD if net >= 0 else BAD, true))
	inl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	outl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if Core.ledger_today.is_empty():
		_lbl(list, tr("Nada lançado hoje ainda. Vendas, compras e expansões aparecem aqui."), 15, INK_SOFT, false, true)
		return
	var lines: = _card(list)
	var shown: = Core.ledger_today.duplicate()
	shown.reverse()
	for line in shown.slice(0, 18):
		var lr: = _row(lines, 8)
		_expand(_lbl(lr, tr(str(line.get("r", ""))), 14, INK, false, true))
		var a: = int(line.get("a", 0))
		_lbl(lr, Core.fmt_money(a, true), 14, GOOD if a >= 0 else BAD, true)
