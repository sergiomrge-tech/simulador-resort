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
	["empresa", "Minha Empresa", Color(0.15, 0.55, 0.5), "shop"],
	["servico", "Operação", Color(0.9, 0.55, 0.2), "prato"],
	["expansoes", "Expansões", Color(1.0, 0.45, 0.35), "upgrade"],
	["mercado", "Mercado", Color(0.15, 0.72, 0.45), "compra"],
	["cardapio", "Cardápio", Color(1.0, 0.72, 0.18), "prato"],
	["bangalos", "Bangalôs", Color(0.2, 0.6, 0.95), "cama"],
	["equipe", "Equipe", Color(0.6, 0.4, 0.9), "equipe"],
	["caixa", "Caixa", Color(0.1, 0.65, 0.68), "caixa"],
	["missoes", "Missões", Color(0.95, 0.55, 0.2), "missao"],
	["album", "Álbum", Color(0.85, 0.35, 0.6), "gorjeta"],
	["agenda", "Agenda", Color(0.95, 0.35, 0.5), "clima"],
	["evolucao", "Evolução", Color(0.95, 0.65, 0.1), "laurel-crown"],
	["negocios", "Negócios", Color(0.25, 0.55, 0.85), "shop"],
	["temporada", "Temporada", Color(0.85, 0.5, 0.15), "trophy"],
	["cozinha", "Cozinha", Color(0.8, 0.3, 0.3), "cooking-pot"],
	["vila", "Vila", Color(0.35, 0.6, 0.35), "village"],
	["hotel", "Hotel 5★", Color(0.75, 0.6, 0.2), "bangalo"],
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
	Core.company_changed.connect(_company_refresh)
	Core.stock_changed.connect(_refresh_if_open)
	Core.expansion_bought.connect(func(_id): _refresh_if_open())
	Core.staff_changed.connect(_refresh_if_open)
	Core.market_changed.connect(_refresh_if_open)
	Core.event_changed.connect(_refresh_if_open)
	Core.upgrades_changed.connect(func(_r): _refresh_if_open())
	Core.prog.fame_changed.connect(func(_l, _x): _refresh_if_open())
	Core.prog.tree_changed.connect(_refresh_if_open)
	Core.prog.biz_changed.connect(func(_id): _refresh_if_open())
	Core.prog.goals_changed.connect(_refresh_if_open)
	Core.prog.chapters_changed.connect(_refresh_if_open)
	Core.prog.recipes_changed.connect(_refresh_if_open)

func _place() -> void :
	var vs: = get_viewport_rect().size if size.x < 10.0 else size
	_phone.size = Vector2(W, minf(H, vs.y - 30.0))
	_phone.position = Vector2(vs.x - W - 60.0, (vs.y - _phone.size.y) * 0.5)

func _refresh_if_open() -> void :
	# O formulário mantém seu rascunho durante vendas e reposições, mesmo ao trocar de fonte.
	if app == "empresa":
		return
	if visible:
		call_deferred("refresh")

# ------------------------------------------------------------------ abrir / fechar
func open(which: String = "", arg: int = -1) -> void :
	if arg >= 0:
		room_focus = arg
	app = which
	visible = true
	move_to_front()
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
		"empresa", "servico", "cardapio", "mercado", "album", "missoes", "agenda", "evolucao", "negocios", "temporada", "cozinha", "vila", "hotel":
			return tab
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
	p.add_child(_icon(id if T.icon(id) != null else "insumo", sz - 14, Color.WHITE))
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
	# largura fixa: sem isto os textos longos empurram os cartões para fora da tela do celular
	list.custom_minimum_size.x = W - 28.0 - 24.0 - 10.0
	m.add_child(list)
	match app:
		"empresa":
			_app_company(list)
		"servico":
			_app_service(list)
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
		"missoes":
			_app_quests(list)
		"album":
			_app_album(list)
		"agenda":
			_app_agenda(list)
		"evolucao":
			_app_evolution(list)
		"negocios":
			_app_business(list)
		"temporada":
			_app_season(list)
		"cozinha":
			_app_kitchen(list)
		"vila":
			_app_village(list)
		"hotel":
			_app_hotel(list)

func _home() -> void :
	var m: = MarginContainer.new()
	for side in ["left", "right"]:
		m.add_theme_constant_override("margin_" + side, 20)
	m.add_theme_constant_override("margin_top", 14)
	m.add_theme_constant_override("margin_bottom", 10)
	m.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var hsc: = ScrollContainer.new()
	hsc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	hsc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	screen.add_child(hsc)
	hsc.add_child(m)
	var v: = VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	m.add_child(v)
	var hello: = _lbl(v, str(Core.company.name) if Core.company.created else tr("Quiosque Maré Alta"), 26, INK, true)
	hello.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if Engine.has_meta("update_ver"):
		var up: = _card(v, Color(0.85, 1.0, 0.9, 0.95))
		_lbl(up, tr("ATUALIZAÇÃO DISPONÍVEL"), 14, INK_SOFT, true)
		_lbl(up, tr("Versão %s do jogo já saiu. Baixe o patch (Atualizar_MareAltaResort) e rode com o jogo fechado.") % str(Engine.get_meta("update_ver")), 15, INK, false, true)
		_btn(up, tr("Abrir página dos patches"), func(): OS.shell_open(str(Engine.get_meta("update_page"))))
	_fame_bar(v)
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
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 8)
	grid.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(grid)
	for a in APPS:
		var cell: = VBoxContainer.new()
		cell.add_theme_constant_override("separation", 4)
		grid.add_child(cell)
		var b: = Button.new()
		b.custom_minimum_size = Vector2(72, 72)
		var n: = _box(a[2], 22, 10)
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
		var l: = _lbl(cell, tr(str(a[1])), 13, INK, true)
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
				_lbl(c, str(st[1]), 14, BAD if st[0] == "money" else INK_SOFT, true, true)

func _app_market(list: VBoxContainer) -> void :
	_lbl(list, tr("Entrega na hora no quiosque. Fardos de %d. O preço do mercadinho muda todo dia (▲ caro, ▼ barato).") % Economy.PACK, 15, INK_SOFT, false, true)
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
		var f: = Core.supply_factor(id)
		var trend: = ""
		if f > 1.05:
			trend = "  ▲"
		elif f < 0.95:
			trend = "  ▼"
		_lbl(v, tr("Estoque: %d  ·  %s cada") % [int(Core.stock.get(id, 0)), Core.fmt_money(Core.supply_total(id, 10)) + "/10"] + trend + ("" if used else "  ·  " + tr("ainda não usa")), 14, BAD if f > 1.05 else (GOOD if f < 0.95 else INK_SOFT), false, true)
		var cost: = Core.supply_total(id, Economy.PACK)
		_btn(r, "+%d\n%s" % [Economy.PACK, Core.fmt_money(cost)], func(): Core.buy_supply(id, Economy.PACK), Color(0.15, 0.72, 0.45), Core.money >= cost)
		var cr: = _row(c, 8)
		if Core.contracts.has(id):
			_expand(_lbl(cr, tr("Contrato: -%d%% por mais %d dia(s)") % [int(Economy.CONTRACT_DISCOUNT * 100.0), int(Core.contracts[id])], 13, GOOD, true, true))
		else:
			_expand(_lbl(cr, tr("Contrato de %d dias: -%d%% e nunca paga mais que o normal") % [Economy.CONTRACT_DAYS, int(Economy.CONTRACT_DISCOUNT * 100.0)], 13, INK_SOFT, false, true))
			_btn(cr, tr("Assinar %s") % Core.fmt_money(Economy.CONTRACT_FEE), func(): Core.buy_contract(id), Color(0.2, 0.6, 0.95), Core.money >= Economy.CONTRACT_FEE)
		if Economy.SPOIL.has(id):
			_lbl(c, tr("Estraga %d%% do que sobrar por noite%s") % [int(round(float(Economy.SPOIL[id]) * (0.5 if Core.freezer else 1.0) * 100.0)), tr(" (freezer ligado)") if Core.freezer else ""], 13, BAD if not Core.freezer else INK_SOFT, false, true)
	var fc: = _card(list, Color(0.9, 1.0, 0.92, 0.95) if Core.freezer else Color(1, 1, 1, 0.94))
	var fr: = _row(fc, 10)
	_badge(fr, "gelo", Color(0.2, 0.6, 0.95), 40)
	var fv: = VBoxContainer.new()
	fv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	fr.add_child(fv)
	_lbl(fv, tr("Freezer"), 18, INK, true)
	_lbl(fv, tr("Metade do estoque deixa de estragar durante a noite."), 14, INK_SOFT, false, true)
	if Core.freezer:
		_lbl(fr, tr("✓ Seu"), 16, GOOD, true)
	else:
		_btn(fr, Core.fmt_money(Economy.FREEZER_COST), func(): Core.buy_freezer(), Color(0.2, 0.6, 0.95), Core.money >= Economy.FREEZER_COST)

func _app_menu(list: VBoxContainer) -> void :
	var ev: = str(Core.day_event)
	if ev != "":
		var ec: = _card(list, Color(1.0, 0.96, 0.78, 0.97))
		_lbl(ec, tr(str(Economy.DAY_EVENTS[ev].name)), 18, INK, true)
		_lbl(ec, tr(str(Economy.DAY_EVENTS[ev].blurb)), 14, INK_SOFT, false, true)
	_lbl(list, tr("Ajuste o preço de cada prato: barato atrai mais gente, caro rende mais por cliente mas pode irritar."), 14, INK_SOFT, false, true)
	for id in Economy.DISHES:
		var d: Dictionary = Economy.DISHES[id]
		if bool(d.get("secret", false)) and not Core.prog.is_discovered(id):
			continue   # prato secreto: só aparece depois de descoberto na Cozinha
		var ok: = Core.dish_unlocked(id)
		var c: = _card(list, Color(1, 1, 1, 0.94) if ok else Color(0.92, 0.92, 0.95, 0.9))
		var r: = _row(c, 10)
		_expand(_lbl(r, tr(str(d.name)), 18, INK if ok else INK_SOFT, true))
		var price: = Core.price_of(id)
		_lbl(r, Core.fmt_money(price), 18, GOOD if ok else INK_SOFT, true)
		var where: = []
		if id in Core.kiosk_menu():
			where.append(tr("quiosque"))
		if Core.has("bar") and id in Core.bar_menu():
			where.append(tr("bar"))
		var margin: = price - Economy.dish_cost(id)
		var info: = tr("Custo %s · margem %s") % [Core.fmt_money(Economy.dish_cost(id)), Core.fmt_money(margin)]
		if not ok and Economy.DISH_UNLOCK.has(id):
			info = tr("Bloqueado: compre %s") % tr(str(Economy.EXPANSIONS[Economy.DISH_UNLOCK[id]].name))
		elif where.is_empty():
			info += "  ·  " + tr("ainda não é vendido")
		else:
			info += "  ·  " + ", ".join(where)
		_lbl(c, info, 14, INK_SOFT, false, true)
		if ok:
			var pr: = _row(c, 6)
			var t: = Core.price_tier_of(id)
			_btn(pr, "−", func(): Core.set_price_tier(id, t - 1), Color(0.35, 0.55, 0.95), t > 0)
			var ml: = _lbl(pr, "×%.2f" % float(Economy.PRICE_TIERS[t]), 17, INK, true)
			ml.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			_expand(ml)
			_btn(pr, "+", func(): Core.set_price_tier(id, t + 1), Color(1.0, 0.55, 0.2), t < Economy.PRICE_TIERS.size() - 1)
		if ok and not Core.can_make(id):
			_lbl(c, tr("Sem insumos! Compre no Mercado."), 14, BAD, true)

func _app_quests(list: VBoxContainer) -> void :
	_lbl(list, tr("Encomendas dos moradores. Aceite com o morador, junte os itens e entregue a ele."), 14, INK_SOFT, false, true)
	var tips: = _card(list, Color(0.9, 0.97, 1.0, 0.95))
	_lbl(tips, tr("Dica: pesque no fim do píer e junte cocos caídos sob as palmeiras. Os dois dão insumos de graça."), 14, INK, false, true)
	for id in Economy.QUESTS:
		var q: Dictionary = Economy.QUESTS[id]
		var st: = str(Core.quests.get(id, ""))
		var avail: = Core.quest_available(id)
		var c: = _card(list, Color(0.9, 1.0, 0.92, 0.95) if st == "done" else Color(1, 1, 1, 0.94))
		var r: = _row(c, 10)
		_badge(r, str(q.need), GOOD if st == "done" else (Color(0.95, 0.55, 0.2) if avail else Color(0.6, 0.6, 0.66)), 40)
		var v: = VBoxContainer.new()
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r.add_child(v)
		_lbl(v, tr(str(q.title)), 18, INK, true, true)
		_lbl(v, tr(str(q.desc)), 14, INK_SOFT, false, true)
		_lbl(c, "%s · %s" % [tr(str(q.giver)), tr(str(q.where))], 13, INK_SOFT, false, true)
		var r2: = _row(c, 8)
		_expand(_lbl(r2, tr("Paga %s") % Core.fmt_money(int(q.reward)) + (" + ★" if q.has("rating") else ""), 16, INK, true))
		if st == "done":
			_lbl(r2, tr("✓ Entregue"), 16, GOOD, true)
		elif not avail:
			_lbl(r2, tr("Compre: %s") % tr(str(Economy.EXPANSIONS[q.req].name)), 13, BAD, true, true)
		elif st == "":
			_lbl(r2, tr("Fale com o morador"), 14, INK_SOFT, true)
		else:
			var have: = int(Core.stock.get(q.need, 0))
			_lbl(r2, "%d/%d %s" % [mini(have, int(q.qty)), int(q.qty), tr(str(Economy.SUPPLIES[q.need].name))], 15, GOOD if have >= int(q.qty) else BAD, true)

func _app_album(list: VBoxContainer) -> void :
	_album_photos(list)
	var n: = Core.album.size()
	var head: = _card(list, Color(1.0, 0.96, 0.8, 0.97))
	_lbl(head, tr("Clientes famosos: %d/%d") % [n, Economy.VIPS.size()], 20, INK, true)
	_lbl(head, tr("Sirva um cliente VIP (balão dourado) para colocá-lo no álbum. Cada marco paga um prêmio."), 14, INK_SOFT, false, true)
	var ms: = _row(head, 8)
	for k in Economy.ALBUM_REWARDS:
		var done: = n >= int(k)
		_chip(ms, "%d: %s" % [int(k), Core.fmt_money(int(Economy.ALBUM_REWARDS[k]))], Color.WHITE if done else INK, GOOD if done else Color(0.9, 0.9, 0.94))
	for v in Economy.VIPS:
		var got: bool = Core.album.has(v.id)
		var c: = _card(list, Color(1, 1, 1, 0.95) if got else Color(0.92, 0.92, 0.95, 0.9))
		var r: = _row(c, 10)
		_badge(r, "gorjeta", Color(0.95, 0.7, 0.15) if got else Color(0.65, 0.65, 0.7), 40)
		var col: = VBoxContainer.new()
		col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r.add_child(col)
		_lbl(col, str(v.name) if got else "???", 18, INK if got else INK_SOFT, true)
		_lbl(col, tr(str(v.title)) if got else tr("Ainda não visitou o quiosque"), 14, INK_SOFT, false, true)

## v0.9.5: fotos tiradas com a tecla P (user://album) e temas que pagam prêmio.
func _album_photos(list: VBoxContainer) -> void :
	var data: = {"fotos": [], "temas": {}}
	var f: = FileAccess.open("user://album/album.json", FileAccess.READ)
	if f:
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			data = d
	var head: = _card(list, Color(0.85, 0.95, 1.0, 0.97))
	var themes: Dictionary = load("res://scripts/photo_mode.gd").THEMES
	_lbl(head, tr("Fotos: %d   ·   Temas: %d/%d") % [data.fotos.size(), data.temas.size(), themes.size()], 20, INK, true)
	_lbl(head, tr("Aperte P para fotografar. Cada tema novo rende um prêmio."), 14, INK_SOFT, false, true)
	var ch: = HFlowContainer.new()
	ch.add_theme_constant_override("h_separation", 6)
	ch.add_theme_constant_override("v_separation", 6)
	head.add_child(ch)
	for t in themes:
		var got: bool = data.temas.has(t)
		_chip(ch, tr(str(themes[t][0])), Color.WHITE if got else INK, GOOD if got else Color(0.9, 0.9, 0.94))
	var grid: = GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	list.add_child(grid)
	var fotos: Array = data.fotos
	for i in range(fotos.size() - 1, maxi(-1, fotos.size() - 13), -1):
		var img: = Image.load_from_file("user://album/" + str(fotos[i].arq))
		if img == null or img.is_empty():
			continue
		var tr_: = TextureRect.new()
		tr_.texture = ImageTexture.create_from_image(img)
		tr_.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr_.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		tr_.custom_minimum_size = Vector2(150, 84)
		grid.add_child(tr_)

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

func _app_agenda(list: VBoxContainer) -> void :
	var ev: = str(Core.day_event)
	var c: = _card(list, Color(1.0, 0.96, 0.78, 0.97))
	_lbl(c, tr("Hoje (dia %d)") % Core.day, 15, INK_SOFT, true)
	if ev == "":
		_lbl(c, tr("Dia normal, sem eventos."), 17, INK, true)
	else:
		_lbl(c, tr(str(Economy.DAY_EVENTS[ev].name)), 18, INK, true)
		_lbl(c, tr(str(Economy.DAY_EVENTS[ev].blurb)), 14, INK_SOFT, false, true)
		if Core.prep_active:
			_lbl(c, tr("✓ Preparativos feitos"), 15, GOOD, true)
	var fc: = _card(list)
	_lbl(fc, tr("Previsão para amanhã"), 15, INK_SOFT, true)
	var fn: = str(Core.forecast_next)
	if fn == "":
		_lbl(fc, tr("Tempo firme, sem eventos."), 17, INK, true)
	else:
		_lbl(fc, tr(str(Economy.DAY_EVENTS[fn].name)), 18, INK, true)
		_lbl(fc, tr(str(Economy.DAY_EVENTS[fn].blurb)), 14, INK_SOFT, false, true)
	# preparativos: evento de amanhã, ou decoração da festa de hoje
	var target: = fn
	if Core.is_party() and not Core.prep_active:
		target = ev
	var pc: = Core.prep_cost(target)
	if pc > 0 and not Core.prep_paid and not Core.prep_active:
		var storm: = target == "tempestade" or target == "mare"
		var r: = _row(fc, 8)
		_expand(_lbl(r, tr("Proteger o estoque e amarrar tudo") if storm else tr("Decoração da festa: mais movimento"), 14, INK, false, true))
		_btn(r, tr("Preparar\n%s") % Core.fmt_money(pc), func(): Core.buy_prep(), Color(0.95, 0.35, 0.5), Core.money >= pc)
	elif Core.prep_paid:
		_lbl(fc, tr("✓ Preparativos pagos para amanhã"), 15, GOOD, true)
	var cal: = _card(list)
	_lbl(cal, tr("Festas do calendário"), 15, INK_SOFT, true)
	if Core.day < Economy.PARTY_FROM_DAY:
		_lbl(cal, tr("A primeira festa da praia acontece no dia %d.") % Economy.PARTY_FROM_DAY, 14, INK_SOFT, false, true)
	else:
		for k in [2, 4, 6]:
			var pid: String = str(Economy.PARTY_CALENDAR[k])
			var d: = Core.day
			while d % 7 != k or d < Core.day:
				d += 1
			_lbl(cal, "%s · dia %d" % [tr(str(Economy.DAY_EVENTS[pid].name)), d], 14, INK, false, true)
	var tc: = _card(list)
	_lbl(tc, tr("Passeios turísticos"), 15, INK_SOFT, true)
	if not Core.has("passeios"):
		_lbl(tc, tr("Compre a expansão Passeios turísticos e contrate um guia."), 14, INK_SOFT, false, true)
	else:
		if not bool(Core.staff.get("guia", false)):
			_lbl(tc, tr("Contrate um guia na aba Equipe para os passeios rodarem."), 14, BAD, false, true)
		for id in Economy.TOURS:
			var t: Dictionary = Economy.TOURS[id]
			var hh: = int(float(t.at) / 60.0)
			var mm: = int(float(t.at)) % 60
			var stt: = Core.tour_status(id)
			var mark: = "✓" if stt == "done" else ("–" if stt == "missed" else "•")
			var sea: = ""
			if bool(t.sea) and (ev == "mare" or ev == "tempestade"):
				sea = "  " + tr("(cancelado pelo mar)")
			_lbl(tc, "%s %02d:%02d  %s · %s/pessoa%s" % [mark, hh, mm, tr(str(t.name)), Core.fmt_money(int(t.price)), sea], 14, INK, false, true)
		_lbl(tc, tr("Total: %d passeios, %s") % [Core.tours_total, Core.fmt_money(Core.tours_revenue)], 14, GOOD, true, true)

func _app_staff(list: VBoxContainer) -> void :
	for role in Economy.STAFF:
		var s: Dictionary = Economy.STAFF[role]
		var hired: = bool(Core.staff.get(role, false))
		var need: = str(s.get("req", ""))
		var c: = _card(list, Color(0.9, 1.0, 0.92, 0.95) if hired else Color(1, 1, 1, 0.94))
		var r: = _row(c, 10)
		_badge(r, "quiosque" if role == "atendente" else ("equipe" if role == "guia" else role), Color(0.6, 0.4, 0.9))
		var v: = VBoxContainer.new()
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r.add_child(v)
		_lbl(v, tr(str(s.name)), 18, INK, true, true)
		_lbl(v, tr(str(s.blurb)), 14, INK_SOFT, false, true)
		var r2: = _row(c, 8)
		_expand(_lbl(r2, tr("Contratar %s · salário %s/dia") % [Core.fmt_money(int(s.hire)), Core.fmt_money(int(s.wage))], 14, INK, true, true))
		if hired:
			_chip(r2, tr("✓ Na equipe"), Color.WHITE, GOOD)
			_staff_card(c, role)
		elif bool(s.get("company", false)) and not Core.company.created:
			_lbl(c, "Crie sua empresa no app Minha Empresa.", 14, INK_SOFT, false, true)
		elif need != "" and not Core.has(need):
			_lbl(c, tr("Precisa de: %s") % tr(str(Economy.EXPANSIONS[need].name)), 14, INK_SOFT, true, true)
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


# ================================================================== v1.0: evolução
func _progress(parent: Node, val: float, mx: float, c: Color, h: = 12) -> void:
	var pb: = ProgressBar.new()
	pb.max_value = maxf(mx, 0.001)
	pb.value = clampf(val, 0.0, mx)
	pb.show_percentage = false
	pb.custom_minimum_size = Vector2(0, h)
	pb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pb.add_theme_stylebox_override("background", _box(Color(0.85, 0.85, 0.9), 6, 0))
	pb.add_theme_stylebox_override("fill", _box(c, 6, 0))
	parent.add_child(pb)

## Barra de fama (tela inicial e app Evolução).
func _fame_bar(parent: Node) -> void:
	var P: Prog = Core.prog
	var c: = _card(parent, Color(1.0, 0.97, 0.85, 0.95))
	var r: = _row(c, 10)
	_badge(r, "laurel-crown", Color(0.95, 0.65, 0.1), 40)
	var v: = VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	r.add_child(v)
	_lbl(v, tr("Fama %d: %s") % [P.fame_level, tr(P.fame_name())], 17, INK, true, true)
	var fp: Array = P.fame_progress()
	if int(fp[1]) > 0:
		_progress(v, float(fp[0]), float(fp[1]), Color(0.95, 0.65, 0.1))
		var nxt: = str(PD.FAME_PERKS.get(P.fame_level + 1, ""))
		_lbl(v, tr("Próximo: %s") % tr(nxt) if nxt != "" else "", 13, INK_SOFT, false, true)
	else:
		_lbl(v, tr("Fama máxima!"), 13, GOOD, true)

func _app_evolution(list: VBoxContainer) -> void:
	var P: Prog = Core.prog
	_fame_bar(list)
	_lbl(list, tr("Ganhe fama vendendo, recebendo VIPs, fazendo passeios, cumprindo metas e capítulos. Cada nível traz mais clientes e libera melhorias."), 14, INK_SOFT, false, true)
	for area in PD.TREE:
		var A: Dictionary = PD.TREE[area]
		var head: = _card(list, Color(0.95, 0.92, 1.0, 0.95))
		_lbl(head, tr(str(A.name)).to_upper(), 15, INK_SOFT, true)
		if str(A.need) != "" and not Core.has(str(A.need)):
			_lbl(head, tr("Compre \"%s\" em Expansões para liberar.") % tr(str(Economy.EXPANSIONS[A.need].name)), 14, INK_SOFT, false, true)
			continue
		for br in A.branches:
			var B_: Dictionary = A.branches[br]
			var l: = P.lvl(br)
			var row: = _row(head, 8)
			var col: = VBoxContainer.new()
			col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			row.add_child(col)
			_lbl(col, "%s  %s" % [tr(str(B_.name)), "●".repeat(l) + "○".repeat(3 - l)], 16, INK, true, true)
			_lbl(col, tr(str(B_.desc)), 13, INK_SOFT, false, true)
			var st: Array = P.tree_state(br)
			if st[0] == "max":
				_chip(row, tr("Máximo"), Color.WHITE, GOOD)
			elif st[0] == "locked":
				_lbl(col, str(st[1]), 13, BAD, true, true)
			else:
				var brc: String = br
				_btn(row, Core.fmt_money(int(PD.TREE_COST[l])), func(): P.buy_tree(brc), Color(0.95, 0.65, 0.1), st[0] == "ready")

# ================================================================== v1.0: negócios
func _app_business(list: VBoxContainer) -> void:
	var P: Prog = Core.prog
	_lbl(list, tr("Negócios rendem por hora enquanto abertos. Vá até o balcão e aperte E para atender (minijogo, 1 vez por hora): quanto melhor, maior o prêmio."), 14, INK_SOFT, false, true)
	for id in PD.BUSINESSES:
		var b: Dictionary = PD.BUSINESSES[id]
		var st: Array = P.biz_state(id)
		var owned: bool = st[0] == "owned"
		var c: = _card(list, Color(0.9, 1.0, 0.92, 0.95) if owned else Color(1, 1, 1, 0.94))
		var r: = _row(c, 10)
		_badge(r, "shop", b.tint if st[0] != "locked" else Color(0.6, 0.6, 0.66))
		var v: = VBoxContainer.new()
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r.add_child(v)
		_lbl(v, tr(str(b.name)), 18, INK, true, true)
		_lbl(v, tr(str(b.blurb)), 13, INK_SOFT, false, true)
		_lbl(c, tr("Abre %02dh–%02dh · operador %s/dia · minijogo: %s") % [int(b.open[0]), int(b.open[1]), Core.fmt_money(int(b.wage)), tr(str(b.game))], 13, INK_SOFT, false, true)
		var r2: = _row(c, 8)
		if owned:
			var lv: = int(P.biz[id].lvl)
			var rate: = P.biz_rate(id)
			_expand(_lbl(r2, tr("Nível %d · %s · hoje %s") % [lv, tr("aberto %s/h") % Core.fmt_money(rate) if rate > 0 else tr("fechado agora"), Core.fmt_money(int(P.biz[id].get("today", 0)))], 14, GOOD if rate > 0 else INK_SOFT, true, true))
			if lv < 3:
				var cost: = int(PD.BIZ_UPGRADE_COST[lv])
				var idc: String = id
				_btn(r2, tr("Nível %d\n%s") % [lv + 1, Core.fmt_money(cost)], func(): P.upgrade_biz(idc), Color(0.25, 0.55, 0.85), Core.money >= cost)
			else:
				_chip(r2, tr("Máximo"), Color.WHITE, GOOD)
		else:
			_expand(_lbl(r2, Core.fmt_money(int(b.cost)), 18, INK, true))
			if st[0] == "ready":
				var idb: String = id
				_btn(r2, tr("Abrir negócio"), func(): P.buy_biz(idb), Color(0.25, 0.55, 0.85))
			else:
				_lbl(c, str(st[1]), 14, BAD if st[0] == "money" else INK_SOFT, true, true)

# ================================================================== v1.0: temporada e metas
func _app_season(list: VBoxContainer) -> void:
	var P: Prog = Core.prog
	var c: = _card(list, Color(1.0, 0.95, 0.82, 0.97))
	_lbl(c, tr("%s · temporada %d") % [tr(P.season_name()), P.season_number()], 20, INK, true)
	_lbl(c, tr("Dia %d de %d · movimento ×%.2f") % [P.day_in_season(), PD.SEASON_DAYS, P.season_demand()], 14, INK_SOFT, false, true)
	if P.chapter_done("carnaval"):
		_lbl(c, tr("O Carnaval da Maré acontece no último dia de cada verão."), 13, GOOD, false, true)
	var g: = _card(list)
	_lbl(g, tr("METAS DA SEMANA"), 14, INK_SOFT, true)
	for goal in P.week_goals:
		var done: = bool(goal.done)
		var rr: = _row(g, 8)
		_expand(_lbl(rr, ("✓ " if done else "• ") + P.goal_text(goal), 15, GOOD if done else INK, true, true))
		_lbl(rr, Core.fmt_money(int(goal.reward)), 14, GOOD if done else INK_SOFT, true)
		if not done:
			_progress(g, P.goal_progress(goal), float(goal.target), Color(0.85, 0.5, 0.15), 8)
	var rk: = _card(list)
	_lbl(rk, tr("RANKING DA COSTA (faturamento na temporada)"), 14, INK_SOFT, true, true)
	var rank: Array = P.ranking()
	for i in rank.size():
		var me: = str(rank[i][0]).ends_with("(você)")
		var rr: = _row(rk, 8)
		_expand(_lbl(rr, "%dº  %s" % [i + 1, str(rank[i][0])], 15, Color(0.1, 0.45, 0.8) if me else INK, me, true))
		_lbl(rr, Core.fmt_money(int(rank[i][1])), 15, INK, me)
	_lbl(rk, tr("1º lugar: ouro · 2º: prata · 3º: bronze (com prêmio em dinheiro e fama)."), 13, INK_SOFT, false, true)
	var md: = _card(list)
	_lbl(md, tr("MEDALHAS: %d") % P.medals.size(), 14, INK_SOFT, true)
	var fl: = HFlowContainer.new()
	fl.add_theme_constant_override("h_separation", 6)
	fl.add_theme_constant_override("v_separation", 6)
	md.add_child(fl)
	var cols: = {"ouro": Color(0.95, 0.72, 0.1), "prata": Color(0.62, 0.66, 0.72), "bronze": Color(0.75, 0.45, 0.2)}
	for m in P.medals:
		_chip(fl, "%s · T%d" % [tr(str(m.get("name", ""))), int(m.get("season", 0))], Color.WHITE, cols.get(str(m.medal), INK_SOFT))
	if P.medals.is_empty():
		_lbl(md, tr("Nenhuma ainda. Fature mais que os rivais até o fim da temporada."), 13, INK_SOFT, false, true)

# ================================================================== v1.0: cozinha experimental
var _kit_sel: Array = []

func _app_kitchen(list: VBoxContainer) -> void:
	var P: Prog = Core.prog
	var ex: = _card(list, Color(1.0, 0.93, 0.9, 0.97))
	_lbl(ex, tr("COZINHA EXPERIMENTAL"), 14, INK_SOFT, true)
	_lbl(ex, tr("Escolha 2 ou 3 insumos e teste. Cada teste gasta 1 de cada. Acertou a combinação: prato secreto novo no cardápio!"), 14, INK, false, true)
	var fl: = HFlowContainer.new()
	fl.add_theme_constant_override("h_separation", 6)
	fl.add_theme_constant_override("v_separation", 6)
	ex.add_child(fl)
	for id in Economy.SUPPLIES:
		var on: = _kit_sel.has(id)
		var idc: String = id
		var b: = _btn(fl, "%s (%d)" % [tr(str(Economy.SUPPLIES[id].name)), int(Core.stock.get(id, 0))], func():
			if _kit_sel.has(idc):
				_kit_sel.erase(idc)
			elif _kit_sel.size() < 3:
				_kit_sel.append(idc)
			refresh(), Color(0.8, 0.3, 0.3) if on else Color(0.6, 0.58, 0.66))
		b.add_theme_font_size_override("font_size", 14)
	var tr2: = _row(ex, 8)
	_expand(_lbl(tr2, tr("Panela: %s") % (", ".join(_kit_sel.map(func(i): return tr(str(Economy.SUPPLIES[i].name)))) if not _kit_sel.is_empty() else "—"), 14, INK, true, true))
	_btn(tr2, tr("Testar"), func():
		P.try_recipe(_kit_sel.duplicate())
		_kit_sel.clear()
		refresh(), Color(0.8, 0.3, 0.3), _kit_sel.size() >= 2)
	var rc: = _card(list)
	_lbl(rc, tr("CADERNO DE RECEITAS"), 14, INK_SOFT, true)
	for id in PD.RECIPES:
		var got: = P.is_discovered(id)
		var hint: = str(PD.RECIPES[id].hint)
		if id == "moqueca" and not P.chapter_done("sabores") and not got:
			hint = "Dona Lourdes sabe essa (capítulo \"Sabores da vila\")"
		_lbl(rc, ("✓ %s" % tr(str(Economy.DISHES[id].name))) if got else ("? " + tr(hint)), 14, GOOD if got else INK, got, true)
	var mn: = _card(list)
	_lbl(mn, tr("CARDÁPIO DO QUIOSQUE"), 14, INK_SOFT, true)
	_lbl(mn, tr("Desligue pratos para focar nos mais lucrativos (pelo menos 1 fica ligado)."), 13, INK_SOFT, false, true)
	var on_n: = 0
	for d in Economy.KIOSK_MENU:
		if Core.dish_unlocked(d) and not bool(P.menu_off.get(d, false)):
			on_n += 1
	for d in Economy.KIOSK_MENU:
		if not Core.dish_unlocked(d):
			continue
		var off: = bool(P.menu_off.get(d, false))
		var rr: = _row(mn, 8)
		_expand(_lbl(rr, tr(str(Economy.DISHES[d].name)), 15, INK_SOFT if off else INK, true))
		var dc: String = d
		_btn(rr, tr("Desligado") if off else tr("Ligado"), func(): P.toggle_menu(dc), Color(0.6, 0.6, 0.66) if off else GOOD, off or on_n > 1)
	var pr: = _card(list)
	_lbl(pr, tr("FORNECEDORES PREMIUM"), 14, INK_SOFT, true)
	_lbl(pr, tr("Insumo premium custa %d%% a mais e os clientes avaliam melhor (até +%.2f ★ com tudo premium).") % [int(round((PD.PREMIUM_MULT - 1.0) * 100.0)), PD.PREMIUM_RATING], 13, INK_SOFT, false, true)
	for id in Economy.SUPPLIES:
		var on: = bool(P.premium.get(id, false))
		var rr: = _row(pr, 8)
		_expand(_lbl(rr, tr(str(Economy.SUPPLIES[id].name)), 15, INK, true))
		var ic: String = id
		_btn(rr, tr("Premium") if on else tr("Comum"), func(): P.toggle_premium(ic), Color(0.95, 0.65, 0.1) if on else Color(0.6, 0.6, 0.66))

# ================================================================== v1.0: capítulos da vila
func _app_village(list: VBoxContainer) -> void:
	var P: Prog = Core.prog
	_lbl(list, tr("Histórias dos moradores. Cada capítulo concluído libera um lugar ou negócio novo."), 14, INK_SOFT, false, true)
	for c in PD.CHAPTERS:
		var id: String = c.id
		var open: = P.chapter_open(id)
		var done: = P.chapter_done(id)
		var card: = _card(list, Color(0.9, 1.0, 0.92, 0.95) if done else (Color(1, 1, 1, 0.94) if open else Color(0.92, 0.92, 0.95, 0.9)))
		var r: = _row(card, 10)
		_badge(r, "village", GOOD if done else (Color(0.35, 0.6, 0.35) if open else Color(0.6, 0.6, 0.66)), 40)
		var v: = VBoxContainer.new()
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		r.add_child(v)
		_lbl(v, tr(str(c.title)), 18, INK, true, true)
		_lbl(v, "%s · %s" % [tr(str(c.giver)), tr("concluído") if done else (tr("passo %d de 3") % (P.chapter_step(id) + 1) if open else tr("bloqueado"))], 13, INK_SOFT, false, true)
		if not open:
			_lbl(card, tr("Conclua o capítulo anterior."), 13, INK_SOFT, false, true)
			continue
		_lbl(card, tr(str(c.story)), 14, INK, false, true)
		for i in 3:
			var s: Dictionary = c.steps[i]
			var k: = P.chapter_step(id)
			var mark: = "✓" if i < k else ("→" if i == k else "·")
			var extra: = ""
			if i == k and not done:
				match str(s.kind):
					"serve":
						extra = "  (%d/%d)" % [int(P.chapters.get(id + "_serve", 0)), int(s.qty)]
					"sell":
						extra = "  (%d/%d)" % [int(P.chapters.get(id + "_sell", 0)), int(s.qty)]
					"deliver":
						extra = "  (%d/%d)" % [mini(int(Core.stock.get(str(s.item), 0)), int(s.qty)), int(s.qty)]
					"recipes":
						extra = "  (%d/%d)" % [P.discovered.size(), int(s.qty)]
					"biz":
						extra = "  (%d/%d)" % [P.biz.size(), int(s.qty)]
			_lbl(card, "%s %s%s" % [mark, tr(str(s.text)), extra], 14, GOOD if i < k else (INK if i == k else INK_SOFT), i == k, true)
		var r2: = _row(card, 8)
		_expand(_lbl(r2, tr("Libera: %s · prêmio %s") % [tr(str(c.unlock)), Core.fmt_money(int(c.reward))], 13, GOOD if done else INK_SOFT, true, true))
		if not done:
			var kind: = str(c.steps[P.chapter_step(id)].kind)
			var label: = tr("Entregar") if kind == "deliver" else (tr("Pagar") if kind == "pay" else tr("Concluir passo"))
			_btn(r2, label, func(): P.advance_chapter(id), Color(0.35, 0.6, 0.35), P.step_met(id))


## v1.0: nível, experiência, energia, traço, treino e folga de cada funcionário.
func _staff_card(c: VBoxContainer, role: String) -> void:
	var P: Prog = Core.prog
	var sr: Dictionary = P.staff_rec(role)
	var tr_: Dictionary = PD.STAFF_TRAITS.get(str(sr.trait), {"name": "", "desc": ""})
	var lv: = int(sr.lvl)
	_lbl(c, tr("Nível %d · %s: %s · salário atual %s/dia") % [lv, tr(str(tr_.name)), tr(str(tr_.desc)), Core.fmt_money(P.staff_wage(role))], 13, INK, false, true)
	var xr: = _row(c, 6)
	_lbl(xr, tr("XP"), 13, INK_SOFT, true)
	if lv < PD.STAFF_XP.size():
		_progress(xr, float(int(sr.xp) - int(PD.STAFF_XP[lv - 1])), float(int(PD.STAFF_XP[lv]) - int(PD.STAFF_XP[lv - 1])), Color(0.6, 0.4, 0.9), 8)
	else:
		_lbl(xr, tr("nível máximo"), 13, GOOD, true)
	var er: = _row(c, 6)
	_lbl(er, tr("Energia"), 13, INK_SOFT, true)
	_progress(er, float(sr.energy), 100.0, GOOD if int(sr.energy) >= 30 else BAD, 8)
	var br: = _row(c, 8)
	var cost: = PD.STAFF_TRAIN_COST * lv
	_btn(br, tr("Treinar %s") % Core.fmt_money(cost), func(): P.train(role), Color(0.6, 0.4, 0.9), Core.money >= cost and lv < PD.STAFF_XP.size())
	_btn(br, tr("Voltar ao trabalho") if bool(sr.off) else tr("Dar folga hoje"), func(): P.toggle_off(role), Color(0.2, 0.6, 0.95))
	if bool(sr.off):
		_lbl(c, tr("De folga: não trabalha hoje, recupera energia e recebe meio salário."), 13, INK_SOFT, false, true)


# ================================================================== v1.0: Grand Hotel 5★ (fase final)
func _app_hotel(list: VBoxContainer) -> void:
	var P: Prog = Core.prog
	var e: Dictionary = Economy.EXPANSIONS.grand_hotel
	var head: = _card(list, Color(1.0, 0.95, 0.8, 0.97))
	_lbl(head, tr(str(e.name)), 20, INK, true, true)
	_lbl(head, tr(str(e.blurb)), 14, INK_SOFT, false, true)
	if not Core.has("grand_hotel"):
		var st: Array = Core.expansion_state("grand_hotel")
		var req: = _card(list)
		_lbl(req, tr("PARA CONSTRUIR"), 14, INK_SOFT, true)
		var checks: = [
			[tr("Piscina e Passeios turísticos"), Core.has("pool") and Core.has("passeios")],
			[tr("★ %.1f de avaliação") % float(e.stars), Core.stars() + 0.001 >= float(e.stars)],
			[tr("Fama \"%s\"") % tr(P.fame_name(int(e.fame))), P.fame_level >= int(e.fame)],
			[tr("Capítulo \"%s\" concluído") % tr(P.chapter_title(str(e.chapter))), P.chapter_done(str(e.chapter))],
			[tr("%s em caixa") % Core.fmt_money(int(e.cost)), Core.money >= int(e.cost)],
		]
		for c in checks:
			_lbl(req, ("✓ " if c[1] else "○ ") + str(c[0]), 15, GOOD if c[1] else INK, c[1], true)
		var r: = _row(req, 8)
		_expand(_lbl(r, Core.fmt_money(int(e.cost)), 20, INK, true))
		_btn(r, tr("Construir o hotel"), func(): Core.buy_expansion("grand_hotel"), Color(0.75, 0.6, 0.2), st[0] == "ready")
		return
	var occ: = P.hotel_occupancy()
	var c: = _card(list)
	_lbl(c, tr("PREVISÃO PARA ESTA NOITE"), 14, INK_SOFT, true)
	var rr: = _row(c, 8)
	_lbl(rr, tr("Ocupação"), 15, INK, true)
	_progress(rr, occ, 1.0, Color(0.75, 0.6, 0.2), 12)
	_lbl(rr, "%d%%" % int(occ * 100.0), 15, INK, true)
	_lbl(c, tr("Diária das suítes: %s · %d suítes") % [Core.fmt_money(P.hotel_rate()), PD.HOTEL_ROOMS], 14, INK_SOFT, false, true)
	if not P.hotel_last.is_empty():
		var l: = _card(list)
		_lbl(l, tr("ÚLTIMA NOITE"), 14, INK_SOFT, true)
		_lbl(l, tr("%d suítes ocupadas · diárias %s") % [int(P.hotel_last.rooms), Core.fmt_money(int(P.hotel_last.rev))], 15, INK, false, true)
		_lbl(l, tr("Restaurante e bar: %s") % Core.fmt_money(int(P.hotel_last.dining)), 15, INK, false, true)
		_lbl(l, tr("Equipe do hotel: %s") % Core.fmt_money(- int(P.hotel_last.staff), true), 15, BAD, false, true)
		var net: = int(P.hotel_last.rev) + int(P.hotel_last.dining) - int(P.hotel_last.staff)
		_lbl(l, tr("Lucro: %s") % Core.fmt_money(net, true), 17, GOOD if net >= 0 else BAD, true)
	var am: = _card(list)
	_lbl(am, tr("ESTRUTURA"), 14, INK_SOFT, true)
	var fl: = HFlowContainer.new()
	fl.add_theme_constant_override("h_separation", 6)
	fl.add_theme_constant_override("v_separation", 6)
	am.add_child(fl)
	for a in PD.HOTEL_AMENITIES:
		_chip(fl, tr(str(a)), Color.WHITE, GOOD)
	_lbl(list, tr("Dica: melhore o hotel no app Evolução (área Grand Hotel 5★). Ocupação sobe com estrelas, fama, verão e festas."), 13, INK_SOFT, false, true)

# ------------------------------------------------------------------ empresa / atendimento físico
const CompanyRules = preload("res://scripts/company_rules.gd")
var company_name: LineEdit
var company_font: OptionButton
var company_color: OptionButton
var company_preview: Label
var company_count: Label

func _company_refresh() -> void:
	# Não reconstruir o formulário enquanto o jogador digita.
	if app != "empresa":
		_refresh_if_open()

func _app_company(list: VBoxContainer) -> void:
	_lbl(list, "Sua marca na praia", 23, INK, true)
	_lbl(list, "Escolha um nome de até 24 caracteres. O tamanho das letras se ajusta para caber inteiro na placa.", 15, INK_SOFT, false, true)
	company_name = LineEdit.new()
	company_name.max_length = CompanyRules.MAX_NAME
	company_name.text = str(Core.company.name)
	company_name.placeholder_text = "Nome da empresa"
	list.add_child(company_name)
	company_font = OptionButton.new()
	for id in CompanyRules.FONTS:
		company_font.add_item(str(CompanyRules.FONTS[id]))
	company_font.select(CompanyRules.FONTS.keys().find(Core.company.font))
	list.add_child(company_font)
	company_color = OptionButton.new()
	for id in CompanyRules.COLORS:
		company_color.add_item(str(id).capitalize())
	company_color.select(CompanyRules.COLORS.keys().find(Core.company.color))
	list.add_child(company_color)
	var board := _card(list, Color(0.06, 0.22, 0.23))
	company_preview = _lbl(board, "", 28, Color.WHITE, true)
	company_preview.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	company_preview.clip_text = true
	company_count = _lbl(list, "", 14, INK_SOFT)
	company_name.text_changed.connect(_preview_company.unbind(1))
	company_font.item_selected.connect(_preview_company.unbind(1))
	company_color.item_selected.connect(_preview_company.unbind(1))
	_preview_company()
	_btn(list, "Salvar marca" if Core.company.created else "Criar minha empresa", _save_company)
	if Core.company.created:
		var manual := CheckButton.new()
		manual.text = "Atendimento com retirada e entrega"
		manual.button_pressed = bool(Core.company.physical)
		manual.toggled.connect(_set_service)
		list.add_child(manual)
	_lbl(list, "Você começa atendendo. Contrate garçom, caixa, cozinheiro e limpeza para dividir o trabalho. Há custo de contratação e salário diário; folgas e energia afetam a equipe.", 15, INK_SOFT, false, true)
	_btn(list, "Contratar e gerenciar equipe", _company_staff)
	_lbl(list, "Contorne o quiosque para acessar a geladeira, a cozinha e o armário. Retire um item por vez e aperte E no cliente que o pediu. Receba as contas no terminal do balcão e recolha a louça após a saída.", 15, INK_SOFT, false, true)

func _preview_company() -> void:
	var font_id: String = str(CompanyRules.FONTS.keys()[company_font.selected])
	var color_id: String = str(CompanyRules.COLORS.keys()[company_color.selected])
	var f: Font = CompanyRules.font_for(font_id)
	company_preview.text = company_name.text
	company_preview.add_theme_font_override("font", f)
	company_preview.add_theme_color_override("font_color", CompanyRules.COLORS[color_id])
	var width: float = f.get_string_size(company_name.text, HORIZONTAL_ALIGNMENT_LEFT, -1, 28).x
	company_preview.add_theme_font_size_override("font_size", mini(28, maxi(12, int(28 * 300.0 / maxf(width, 1.0)))))
	company_count.text = "%d/24 caracteres" % company_name.text.length()

func _save_company() -> void:
	if Core.configure_company(company_name.text, str(CompanyRules.FONTS.keys()[company_font.selected]), str(CompanyRules.COLORS.keys()[company_color.selected])):
		Core.toast.emit("Sua empresa está pronta!", "good")
		refresh()

func _set_service(enabled: bool) -> void:
	Core.set_company_service(enabled)
	call_deferred("refresh")

func _company_staff() -> void:
	app = "equipe"
	refresh()

func _operations():
	return get_tree().current_scene.operations

func _service_action(id: String, action: String) -> void:
	var ops = _operations()
	var kind: String = str(Core.service_station)
	if not ops.can_access(kind):
		return
	var drink: bool = load("res://scripts/dish_presentation.gd").is_drink(id)
	var ok := false
	if action == "prepare" and (kind == "cozinha" or (kind == "bebidas" and drink)):
		ok = Core.prepare_company_dish(id)
	elif action == "pickup" and ((kind == "bebidas" and drink) or (kind == "pratos" and not drink)):
		ok = Core.pickup_company_dish(id)
	elif action == "return" and ((kind == "bebidas" and drink) or (kind == "pratos" and not drink)):
		ok = Core.return_company_dish()
	if ok:
		ops.finish_station()
	else:
		Core.toast.emit("Confira os ingredientes, o preparo e o espaço disponível.", "bad")

func _app_service(list: VBoxContainer) -> void:
	if not Core.company_enabled():
		_lbl(list, "Crie a empresa e ative o atendimento com retirada no app Minha Empresa.", 17, INK, false, true)
		return
	var kind: String = str(Core.service_station)
	var near: bool = _operations().can_access(kind)
	_lbl(list, {"bebidas": "Geladeira", "pratos": "Armário de pratos", "cozinha": "Cozinha"}.get(kind, "Operação"), 23, INK, true)
	_lbl(list, "Máximo de 4 unidades prontas por produto. Ingredientes são usados no preparo; retirar e entregar não gastam ingredientes novamente.", 14, INK_SOFT, false, true)
	if not near:
		_lbl(list, "Aproxime-se da estação atrás do quiosque e aperte E para preparar ou retirar.", 16, BAD, false, true)
	if not Core.company.production.is_empty():
		_lbl(list, "Preparando %s · %.1f s estimados" % [Economy.dish(Core.company.production.dish).name, float(Core.company.production.left)], 15, INK, true, true)
	var carried: String = str(Core.company.carry)
	if carried != "":
		_lbl(list, "Carregando: " + str(Economy.dish(carried).name), 17, GOOD, true, true)
		var matches: bool = (kind == "bebidas") == load("res://scripts/dish_presentation.gd").is_drink(carried) and kind != "cozinha"
		_btn(list, "Devolver à prateleira", _service_action.bind(carried, "return"), GOOD, near and matches)
	for id in Core.kiosk_menu():
		var drink: bool = load("res://scripts/dish_presentation.gd").is_drink(id)
		if kind != "cozinha" and (kind == "bebidas") != drink:
			continue
		if kind == "cozinha" and drink:
			continue
		var card := _card(list)
		var count: int = int(Core.company.ready.get(id, 0))
		_lbl(card, "%s · %d prontas" % [Economy.dish(id).name, count], 17, INK, true, true)
		if kind == "bebidas" or kind == "cozinha":
			_btn(card, "Preparar · 3 s" if drink else "Preparar · 6 s", _service_action.bind(id, "prepare"), Color(0.15, 0.55, 0.5), near and Core.company.production.is_empty() and count < 4 and Core.can_make(id))
		if kind != "cozinha":
			_btn(card, "Retirar e levar ao cliente", _service_action.bind(id, "pickup"), GOOD, near and count > 0 and carried == "")
	_lbl(list, "%d contas aguardando recebimento no terminal · %d lugares para limpar" % [Core.company.receivables.size(), Core.company.dirty_seats.size()], 15, INK_SOFT, false, true)
