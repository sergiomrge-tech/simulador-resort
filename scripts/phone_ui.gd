extends Control
class_name PhoneUI
## Gestão no celular. Nome da classe preservado para compatibilidade.
## Seis áreas principais; telas de retirada continuam acessíveis nas estações físicas.

const T: = preload("res://scripts/ui_theme.gd")
const Management = preload("res://scripts/kiosk_management.gd")
var resident_name: String="Dona Rita"
const W: = 420.0
const H: = 700.0
const INK: = Color(0.16, 0.13, 0.2)
const INK_SOFT: = Color(0.42, 0.38, 0.46)
const SCREEN_TOP: = Color(0.95, 0.96, 0.94)
const SCREEN_BOT: = Color(0.88, 0.91, 0.88)
const GOOD: = Color(0.12, 0.62, 0.32)
const BAD: = Color(0.85, 0.28, 0.22)

## id, nome, cor, ícone
const HOME_APPS := ["painel", "compras", "equipe", "financas", "resort", "missoes"]
const PARENTS := {"empresa":"personalizar", "personalizar":"painel", "horarios":"painel", "rotina":"horarios", "movimento":"painel", "equipamentos":"painel", "pedidos":"painel", "cardapio":"painel", "cozinha":"cardapio", "estoque_quiosque":"compras", "mercado":"compras", "fornecedores":"compras", "gestao_equipe":"equipe", "recrutamento":"equipe", "resultado":"financas", "caixa":"financas", "expansoes":"resort", "bangalos":"resort", "hotel":"resort", "evolucao":"resort", "temporada":"resort", "negocios":"resort", "mundo":"missoes", "conversa":"missoes", "album":"mundo", "agenda":"mundo", "vila":"mundo"}
const APPS: = [
	["conversa","Conversa",Color(.2,.5,.4),"village"],
	["painel", "Quiosque", Color(0.15, 0.55, 0.5), "shop"],
	["compras", "Compras", Color(0.25, 0.65, 0.35), "compra"],
	["financas", "Finanças", Color(0.1, 0.6, 0.55), "caixa"],
	["resort", "Resort", Color(0.2, 0.6, 0.95), "cama"],
	["mundo", "Vila e lazer", Color(0.8, 0.4, 0.4), "village"],
	["pedidos", "Pedidos", Color(0.9, 0.55, 0.2), "prato"],
	["rotina", "Rotina do dia", Color(0.15, 0.55, 0.5), "agenda"],
	["recrutamento", "Candidatos", Color(0.6, 0.4, 0.8), "equipe"],
	["fornecedores", "Entregas", Color(0.25, 0.65, 0.35), "compra"],
	["equipamentos", "Equipamentos", Color(0.8, 0.5, 0.2), "cozinha"],
	["personalizar", "Personalizar", Color(0.8, 0.35, 0.4), "shop"],
	["movimento", "Movimento", Color(0.18, 0.5, 0.65), "clima"],
	["empresa", "Nome e placa", Color(0.15, 0.55, 0.5), "shop"],
	["horarios", "Horários", Color(0.18, 0.5, 0.65), "clima"],
	["estoque_quiosque", "Estoque e perdas", Color(0.25, 0.65, 0.35), "compra"],
	["gestao_equipe", "Escala e equipe", Color(0.6, 0.4, 0.8), "equipe"],
	["resultado", "Resultado", Color(0.1, 0.6, 0.55), "caixa"],
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
	["cozinha", "Receitas", Color(0.8, 0.3, 0.3), "cooking-pot"],
	["vila", "Vila", Color(0.35, 0.6, 0.35), "village"],
	["hotel", "Hotel 5★", Color(0.75, 0.6, 0.2), "bangalo"],
]

var app: = ""
var room_focus: = 0
var body_frame: Control
var screen: VBoxContainer
var status_l: Label
var navbar: GridContainer
var _phone: Control
var _tween: Tween

func _ready() -> void :
	add_to_group("phone")
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	theme = T.get_theme().duplicate()
	for type_name in ["Button", "OptionButton", "CheckButton", "CheckBox", "LineEdit", "SpinBox"]:
		theme.set_font_size("font_size", type_name, 16)
	_phone = PanelContainer.new()
	_phone.mouse_filter = Control.MOUSE_FILTER_STOP
	_phone.custom_minimum_size = Vector2(W, H)
	_phone.size = Vector2(W, H)
	var bezel: = StyleBoxFlat.new()
	bezel.bg_color = Color(0.10, 0.12, 0.12)
	bezel.set_corner_radius_all(24)
	bezel.set_border_width_all(4)
	bezel.border_color = Color(.23,.29,.27)
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
	scr.add_theme_stylebox_override("panel", _box(SCREEN_BOT, 14, 0))
	scr.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW
	_phone.add_child(scr)
	var bg: = TextureRect.new()
	bg.texture = grad
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.stretch_mode = TextureRect.STRETCH_SCALE
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	scr.add_child(bg)
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
	navbar = GridContainer.new()
	navbar.columns=3
	navbar.add_theme_constant_override("h_separation",5)
	navbar.add_theme_constant_override("v_separation",5)
	col.add_child(navbar)
	for id in HOME_APPS:
		var info: Array=APPS.filter(func(entry): return entry[0]==id)[0]
		var tab := _btn(navbar,str(info[1]),_open_management.bind(str(id)),Color(.16,.34,.31))
		tab.name="Nav_"+str(id)
		tab.toggle_mode=true
		tab.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	screen = VBoxContainer.new()
	screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
	screen.add_theme_constant_override("separation", 0)
	col.add_child(screen)
	visible = false
	resized.connect(_place)
	Core.money_changed.connect(func(_v): _refresh_if_open())
	Core.company_changed.connect(_company_refresh)
	Core.time_changed.connect(func(_d, _m):
		_refresh_kiosk_controls()
		_refresh_staff_status()
		_refresh_management_task())
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
	var service: bool=app=="servico"
	var dimensions:=Vector2(420,470) if service else Vector2(W,H)
	_phone.custom_minimum_size=dimensions
	_phone.size=dimensions
	var factor:=minf(.95,minf((vs.x-32)/dimensions.x,(vs.y-32)/dimensions.y)) if service else minf(.9,minf((vs.x-32)/W,(vs.y-32)/H))
	_phone.scale=Vector2.ONE*maxf(.1,factor)
	var fitted:=_phone.size*_phone.scale
	_phone.position=(vs-fitted)*.5
	if vs.x>=900: _phone.position.x=vs.x-fitted.x-22
	if navbar: navbar.visible=not service

func _refresh_if_open() -> void :
	# O formulário mantém seu rascunho durante vendas e reposições, mesmo ao trocar de fonte.
	if app in ["empresa", "horarios", "estoque_quiosque", "compras", "equipe", "gestao_equipe", "personalizar", "fornecedores", "recrutamento", "rotina"]:
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
	# Terminal fixo: abertura imediata, sem animação de aparelho portátil.

func close() -> void :
	for child in get_children():
		if child.name=="ResidentConversation":child.queue_free()
	visible = false
	var scene = get_tree().current_scene
	if scene != null and scene.get("operations") != null and is_instance_valid(scene.operations.door): scene.operations.door.rotation.y = 0

func back() -> void :
	if app == "":
		close()
	else:
		app = str(PARENTS.get(app, ""))
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
		"rotina", "recrutamento", "fornecedores", "equipamentos", "personalizar", "movimento", "empresa", "horarios", "estoque_quiosque", "gestao_equipe", "resultado", "servico", "cardapio", "mercado", "album", "missoes", "agenda", "evolucao", "negocios", "temporada", "cozinha", "vila", "hotel":
			return tab
	return ""

# ------------------------------------------------------------------ helpers de UI
func _lbl(parent: Node, t: String, fs: int, c: Color, strong: = false, _wrap: = false) -> Label:
	var l: = Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", maxi(13, roundi(fs * 0.9)))
	l.add_theme_color_override("font_color", c)
	l.add_theme_font_override("font", T.bold() if strong else T.font())
	# Todo texto pode quebrar linha: o nome de um app não alarga a tela.
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

func _card(parent: Node, tint: = Color(1, 1, 1, 0.92), compact: bool=true) -> VBoxContainer:
	var p: = PanelContainer.new()
	var st: = _box(tint, 12 if compact else 18, 8 if compact else 12)
	st.shadow_color = Color(0, 0, 0, 0.12)
	st.shadow_size = 4
	st.shadow_offset = Vector2(0, 2)
	p.add_theme_stylebox_override("panel", st)
	parent.add_child(p)
	var v: = VBoxContainer.new()
	v.add_theme_constant_override("separation", 3 if compact else 6)
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
	b.add_theme_font_size_override("font_size", 15)
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	# Em HBox, largura zero fazia o texto virar uma coluna com centenas de pixels.
	b.custom_minimum_size = Vector2(clampf(T.bold().get_string_size(text,HORIZONTAL_ALIGNMENT_LEFT,-1,15).x+26,34 if text.length()<=2 else 100,230),34)
	b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	b.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
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
	var label := _lbl(p, text, 15, fg, true)
	label.autowrap_mode = TextServer.AUTOWRAP_OFF
	parent.add_child(p)

func _expand(c: Control) -> Control:
	c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return c

# ------------------------------------------------------------------ telas
func refresh() -> void :
	_place()
	if navbar:
		for tab in navbar.get_children():
			tab.set_pressed_no_signal(tab.name=="Nav_"+(app if app in HOME_APPS else str(PARENTS.get(app,"painel")) if app!="" else "painel"))
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
	var hs: = _box(Color(.94,.95,.93), 0, 6)
	head.add_theme_stylebox_override("panel", hs)
	screen.add_child(head)
	var hr: = _row(head, 10)
	var bk: = Button.new()
	bk.text = "‹"
	bk.flat = true
	bk.add_theme_font_size_override("font_size", 24)
	bk.add_theme_color_override("font_color", INK)
	bk.pressed.connect(back)
	hr.add_child(bk)
	_expand(_lbl(hr, tr(str(a[1])), 20, INK, true))
	var sc: = ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	screen.add_child(sc)
	var m: = MarginContainer.new()
	m.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for side in ["left", "right", "top", "bottom"]:
		m.add_theme_constant_override("margin_" + side, 10)
	sc.add_child(m)
	var list: = VBoxContainer.new()
	list.add_theme_constant_override("separation", 7)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	# O ScrollContainer fornece a largura útil, descontando a barra de rolagem.
	list.custom_minimum_size.x = 0
	m.add_child(list)
	if app in ["rotina", "recrutamento", "fornecedores", "equipamentos", "personalizar", "movimento"] and not Core.company.created:
		_lbl(list, "Crie sua empresa para usar esta gestão.", 20, INK, true, true)
		_btn(list, "Criar meu quiosque", _open_management.bind("empresa"))
		return
	match app:
		"conversa":
			_app_conversation(list)
		"painel":
			_app_dashboard(list)
		"compras":
			_app_product_shop(list)
		"financas":
			_app_kiosk_results(list)
			_btn(list, "Extrato de entradas e saídas", _open_management.bind("caixa"))
		"resort":
			_app_hub(list, [["expansoes","Construções e expansões"],["bangalos","Bangalôs"],["hotel","Hotel"],["evolucao","Evolução"],["negocios","Outros negócios"],["temporada","Temporada"]])
		"mundo":
			_app_hub(list, [["agenda","Agenda e clima"],["missoes","Missões"],["vila","Moradores"],["album","Fotos e conquistas"]])
		"pedidos":
			_app_orders(list)
		"rotina":
			_app_routine(list)
		"recrutamento":
			_app_candidates(list)
		"fornecedores":
			_app_suppliers(list)
		"equipamentos":
			_app_equipment(list)
		"personalizar":
			_app_customize(list)
		"movimento":
			_app_demand(list)
		"horarios":
			_app_kiosk_schedule(list)
		"estoque_quiosque":
			_app_kiosk_inventory(list)
		"gestao_equipe":
			_app_staff(list)
		"resultado":
			_app_kiosk_results(list)
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

func _home() -> void:
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	screen.add_child(scroll)
	var margin := MarginContainer.new()
	margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for side in ["left", "right", "top", "bottom"]: margin.add_theme_constant_override("margin_" + side, 12)
	scroll.add_child(margin)
	var list := VBoxContainer.new()
	list.add_theme_constant_override("separation", 9)
	margin.add_child(list)
	_lbl(list, str(Core.company.name) if Core.company.created else "Maré Alta", 23, INK, true)
	_app_dashboard(list)

func _app_hub(list: VBoxContainer, links: Array) -> void:
	for link in links: _btn(list, str(link[1]), _open_management.bind(str(link[0])))

func _app_dashboard(list: VBoxContainer) -> void:
	if not Core.company.created:
		_lbl(list, "Dê um nome ao seu quiosque para começar a operar.", 18, INK, true)
		_btn(list, "Criar meu quiosque", _open_management.bind("empresa"))
		return
	var card := _card(list)
	company_status = _lbl(card, "", 18, INK, true)
	company_open_button = _btn(card, "", _toggle_kiosk)
	_refresh_kiosk_controls()
	var summary := _card(list)
	_lbl(summary,"Hoje",17,INK,true)
	var day_data: Dictionary=Core.company.sim.get("today",{})
	_lbl(summary,"Resultado: "+Core.fmt_money(int(day_data.get("cash_in",0))-int(day_data.get("supplies",0))-int(day_data.get("payroll",0))-int(day_data.get("overhead",0))-int(day_data.get("investment",0)),true),15,INK)
	_lbl(summary,"Atendente: "+("contratado" if Core.staff.get("atendente",false) else "nenhum · contratação em Equipe"),14,INK_SOFT,false,true)
	var low: Array=[]
	for id in Core.kiosk_menu():
		if Core.company_available(id)<=3:low.append(str(Economy.dish(id).name))
	_lbl(summary,"Estoque baixo: "+(", ".join(low) if not low.is_empty() else "tudo abastecido"),14,BAD if not low.is_empty() else GOOD,false,true)
	if not low.is_empty():_btn(summary,"Repor produtos",_open_management.bind("compras"),GOOD)
	_app_hub(list, [["pedidos","Pedidos"],["cardapio","Cardápio e preços"],["horarios","Horários e rotina"],["equipamentos","Equipamentos"],["personalizar","Decoração e nome"],["movimento","Movimento"]])

func _app_orders(list: VBoxContainer) -> void:
	var waiting: Array = get_tree().current_scene.village.waiting_customers()
	if waiting.is_empty():_lbl(list,"Nenhum pedido anotado.",17,INK_SOFT)
	for guest in waiting:
		var card:=_card(list)
		_lbl(card,guest.gname,16,INK,true,true)
		var items: Array=[]
		for id in get_tree().current_scene.village._remaining(guest):items.append(str(Economy.dish(id).name))
		_lbl(card," + ".join(items),14,INK_SOFT,false,true)

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

func _app_product_shop(list: VBoxContainer) -> void:
	_lbl(list,"Reposição imediata · produtos para vender",18,INK,true)
	_lbl(list,"Abasteça até 10 porções. O valor inclui só os insumos que faltam.",14,INK_SOFT)
	if not Core.company.created:
		_btn(list,"Criar meu quiosque",_open_management.bind("empresa"))
		return
	for id in Core.kiosk_menu():
		var card := _card(list)
		var row := _row(card)
		var picture:=TextureRect.new()
		picture.texture=load("res://assets/ui/products/"+str(id)+".svg")
		picture.custom_minimum_size=Vector2(42,42)
		picture.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
		picture.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		row.add_child(picture)
		var text := VBoxContainer.new()
		text.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		row.add_child(text)
		var available: int=Core.company_available(id)
		var quote: Dictionary=Core.company_restock_quote(id,10)
		var cost: int=int(quote.get("cost",0))
		_lbl(text,tr(str(Economy.dish(id).name)),16,INK,true,true)
		_lbl(text,"%d disponíveis" % available,13,INK_SOFT,false,true)
		_btn(row,"Completo" if available>=10 else "Repor 10 · "+Core.fmt_money(cost),_buy_product_stock.bind(str(id)),GOOD,available<10 and Core.money>=cost)
	var extra := VBoxContainer.new()
	list.add_child(extra)
	_btn(extra,"Reposição automática",_open_management.bind("estoque_quiosque"),Color(.35,.40,.39))
	_btn(extra,"Fornecedores e entregas",_open_management.bind("fornecedores"),Color(.35,.40,.39))

func _buy_product_stock(id: String) -> void:
	if Core.restock_company_dish(id,10):
		Core.toast.emit("Estoque reposto. Pegue os produtos na geladeira ou no armário.","good")
	refresh()

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
	_btn(list, "Descobrir receitas", _open_management.bind("cozinha"))
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
		var ingredient_cost: int = 0
		for ing in Economy.dish(id).uses:
			ingredient_cost += Core.supply_total(ing, int(Economy.dish(id).uses[ing]))
		var margin: = price - ingredient_cost
		var info: = tr("Custo atual %s · margem bruta %s") % [Core.fmt_money(ingredient_cost), Core.fmt_money(margin)]
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
	_btn(list,"Vila, fotos e lazer",_open_management.bind("mundo"))
	_campaign_cards(list)
	_lbl(list,"ENCOMENDAS DOS MORADORES",17,INK,true)

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
	var ms := HFlowContainer.new()
	ms.add_theme_constant_override("h_separation", 8)
	ms.add_theme_constant_override("v_separation", 6)
	head.add_child(ms)
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
	if app in ["gestao_equipe", "equipe"]:
		var payroll := 0
		for job in Core.CompanyRules.Simulation.ROLES:
			if bool(Core.staff.get(job, false)):
				payroll += Core.prog.staff_wage(job)
		_lbl(list, "Folha do quiosque: %s/dia" % Core.fmt_money(payroll), 19, INK, true, true)
		_lbl(list, "Turnos de até 8h usam a diária proporcional (mínimo meia diária); turnos maiores custam mais. Folga paga meia diária. O salário é devido mesmo sem vendas.", 14, INK_SOFT, false, true)
	for role in Economy.STAFF:
		if role in Core.KIOSK_STAFF_ROLES and role!="atendente": continue
		if role=="cozinheiro" and not Core.staff.get(role,false): continue
		if str(Economy.STAFF[role].get("req",""))!="" and not Core.has(str(Economy.STAFF[role].req)) and not Core.staff.get(role,false): continue
		if app == "gestao_equipe" and role not in Core.CompanyRules.Simulation.ROLES:
			continue
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
			_lbl(c, "Crie sua empresa em Quiosque → Nome e placa.", 14, INK_SOFT, false, true)
		elif need != "" and not Core.has(need):
			_lbl(c, tr("Precisa de: %s") % tr(str(Economy.EXPANSIONS[need].name)), 14, INK_SOFT, true, true)
		elif role=="atendente" and not Core.company.created:
			_btn(c,"Criar meu quiosque",_open_management.bind("empresa"))
		elif role in Management.ROLES:
			_btn(r2, "Escolher candidato", _choose_candidate.bind(str(role)))
		else:
			_btn(r2, tr("Contratar"), _hire_staff.bind(role), Color(0.6, 0.4, 0.9), Core.money >= int(s.hire))

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
	_btn(br, tr("Treinar %s") % Core.fmt_money(cost), _train_staff.bind(role), Color(0.6, 0.4, 0.9), Core.money >= cost and lv < PD.STAFF_XP.size())
	_btn(br, tr("Voltar ao trabalho") if bool(sr.off) else tr("Dar folga hoje"), _rest_staff.bind(role), Color(0.2, 0.6, 0.95))
	if role in Core.CompanyRules.Simulation.ROLES and Core.company.created:
		_staff_status_labels[role] = weakref(_lbl(c, "Em serviço" if P.staff_eff(role) > 0.0 else "Fora do turno ou de folga", 14, GOOD if P.staff_eff(role) > 0.0 else INK_SOFT, true, true))
		if not Core.company.sim.shifts.has(role):
			_lbl(c, "Sem escala personalizada: segue o quiosque e recebe a diária base. Salvar o turno aplica a proporção de horas.", 13, INK_SOFT, false, true)
		var shift: Dictionary = Core.company.sim.shifts.get(role, {"start": int(Core.kiosk_open_min() / 60), "end": int(Core.kiosk_close_min() / 60)})
		var shift_row := _row(c)
		var start := _hour_picker(shift_row, "Entrada", int(shift.start))
		var end := _hour_picker(shift_row, "Saída", int(shift.end))
		_btn(c, "Salvar turno", func():
			if Core.set_kiosk_shift(role, int(start.value), int(end.value)):
				refresh())
		_btn(c, "Dispensar · rescisão %s" % Core.fmt_money(P.staff_wage(role) * 3), _dismiss_staff.bind(role), BAD, Core.money >= P.staff_wage(role) * 3)
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
var company_status: Label
var company_open_button: Button

func _company_refresh() -> void:
	# Não reconstruir o formulário enquanto o jogador digita.
	if app in ["empresa", "painel"]:
		_refresh_kiosk_controls()
	else:
		_refresh_if_open()

func _app_company(list: VBoxContainer) -> void:
	_lbl(list, "Personalizar a placa", 23, INK, true)
	_lbl(list, "Escolha um nome de até 24 caracteres. O tamanho das letras se ajusta para caber inteiro na placa.", 15, INK_SOFT, false, true)
	company_name = LineEdit.new()
	company_name.max_length = CompanyRules.MAX_NAME
	company_name.text = str(Core.company.name)
	company_name.placeholder_text = "Nome na placa do quiosque"
	company_name.add_theme_color_override("font_color", INK)
	company_name.add_theme_color_override("font_placeholder_color", INK_SOFT)
	company_name.add_theme_color_override("caret_color", INK)
	company_name.add_theme_font_size_override("font_size", 20)
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
	_btn(list, "Salvar nome e placa", _save_company)
	if Core.company.created:
		var manual := CheckButton.new()
		manual.text = "Atendimento com retirada e entrega"
		manual.add_theme_font_size_override("font_size", 16)
		manual.clip_text = true
		manual.button_pressed = bool(Core.company.physical)
		manual.toggled.connect(_set_service)
		list.add_child(manual)

func _refresh_kiosk_controls() -> void:
	if app not in ["", "painel", "empresa"] or not is_instance_valid(company_status) or not is_instance_valid(company_open_button):
		return
	var requested: bool = bool(Core.company.get("kiosk_open", false))
	company_status.text = "Aberto · recebendo clientes" if Core.kiosk_accepting_customers() else ("Fora do horário de atendimento" if requested else "Fechado para novas chegadas")
	if requested and not Management.opening_ready(Core): company_status.text = "Confira a abertura em Horários e rotina"
	company_status.add_theme_color_override("font_color", GOOD if Core.kiosk_accepting_customers() else INK_SOFT)
	company_open_button.text = "Fechar quiosque" if requested else ("Abrir quiosque" if Core.kiosk_is_within_hours() else "Programar abertura")
	company_open_button.custom_minimum_size.x = clampf(T.bold().get_string_size(company_open_button.text,HORIZONTAL_ALIGNMENT_LEFT,-1,15).x+30,150,270)

func _toggle_kiosk() -> void:
	Core.set_kiosk_open(not bool(Core.company.get("kiosk_open", false)))

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
		Core.toast.emit("Nome e placa do quiosque atualizados!", "good")
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
	var drink: bool = load("res://scripts/dish_presentation.gd").is_chilled(id)
	var ok := false
	var matches: bool = (kind == "bebidas" and drink) or (kind in ["pratos", "cozinha"] and not drink)
	if action == "pickup" and matches:
		ok = Core.pickup_company_dish(id)
	elif action == "return" and matches:
		ok = Core.return_company_dish()
	if ok:
		ops.finish_station()
	else:
		Core.toast.emit("Confira o estoque e se você já está carregando um item.", "bad")

func _service_restock(id: String) -> void:
	if not _operations().can_access(str(Core.service_station)): return
	var drink: bool = load("res://scripts/dish_presentation.gd").is_chilled(id)
	if (str(Core.service_station) == "bebidas") != drink: return
	Core.restock_company_dish(id,10)
	refresh()

func _app_service(list: VBoxContainer) -> void:
	if not Core.company_enabled():
		_lbl(list, "Crie a empresa e ative o atendimento com retirada em B → Quiosque.", 17, INK, false, true)
		return
	var kind: String = str(Core.service_station)
	var near: bool = _operations().can_access(kind)
	_lbl(list, {"bebidas": "Geladeira", "pratos": "Armário de pratos", "cozinha": "Cozinha"}.get(kind, "Operação"), 18, INK, true)
	_lbl(list, "Retire pronto. Reponha aqui se acabar. Pagamento na entrega.", 14, INK_SOFT, false, true)
	if not near:
		_lbl(list, "Entre no quiosque e aproxime-se da estação e aperte E para pegar um produto.", 16, BAD, false, true)
	var carried: String = str(Core.company.carry)
	if carried != "":
		_lbl(list, "Carregando: " + str(Economy.dish(carried).name), 17, GOOD, true, true)
		var matches: bool = (kind == "bebidas") == load("res://scripts/dish_presentation.gd").is_chilled(carried)
		_btn(list, "Devolver à prateleira", _service_action.bind(carried, "return"), GOOD, near and matches)
	var menu: Array = Core.kiosk_menu()
	var requests: Dictionary = {}
	for guest in get_tree().current_scene.village.waiting_customers():
		for recipe in get_tree().current_scene.village._remaining(guest):
			if not requests.has(recipe): requests[recipe] = []
			requests[recipe].append(_operations().order_number(guest))
	menu.sort_custom(func(a, b): return requests.get(a, []).size() > requests.get(b, []).size())
	for id in menu:
		var drink: bool = load("res://scripts/dish_presentation.gd").is_chilled(id)
		if kind != "cozinha" and (kind == "bebidas") != drink:
			continue
		if kind == "cozinha" and drink:
			continue
		var card := _card(list,Color(1,1,1,.94),true)
		var row:=_row(card,10)
		var details:=VBoxContainer.new()
		details.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		row.add_child(details)
		var count: int=Core.company_available(id)
		_lbl(details,"%s · %d" % [Economy.dish(id).name,count],15,INK,true,true)
		if requests.has(id): _lbl(details,"Pedidos "+", ".join(requests[id]),13,GOOD,false,true)
		if count>0:
			_btn(row,"Pegar",_service_action.bind(id,"pickup"),GOOD,near and carried=="")
		else:
			var quote: Dictionary=Core.company_restock_quote(id,10)
			_btn(row,"Repor 10 · "+Core.fmt_money(int(quote.cost)),_service_restock.bind(id),Color(.20,.52,.70),near and not quote.items.is_empty() and Core.money>=int(quote.cost))

	_lbl(list, "Pagamento na entrega · %d lugares para limpar" % Core.company.dirty_seats.size(), 15, INK_SOFT, false, true)

# ------------------------------------------------------------------ simulação de gestão
func _open_management(id: String) -> void:
	app = id
	refresh()

func _hour_picker(parent: Node, title: String, initial: int) -> SpinBox:
	var col := VBoxContainer.new()
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	parent.add_child(col)
	_lbl(col, title, 14, INK, true)
	var spin := SpinBox.new()
	spin.min_value = 6
	spin.max_value = 23
	spin.step = 1
	spin.value = initial
	spin.suffix = "h"
	spin.get_line_edit().add_theme_color_override("font_color", INK)
	spin.get_line_edit().add_theme_font_size_override("font_size", 18)
	col.add_child(spin)
	return spin

func _app_kiosk_schedule(list: VBoxContainer) -> void:
	_btn(list, "Checklist e fechamento do turno", _open_management.bind("rotina"))
	_lbl(list, "Sua semana de trabalho", 22, INK, true, true)
	_lbl(list, "Defina o expediente entre 06h e 23h. Dia 1 é segunda-feira. Para parar novas chegadas antes do fim do expediente e concluir os pedidos, use Fechar quiosque.", 14, INK_SOFT, false, true)
	var row := _row(list)
	var start := _hour_picker(row, "Abertura", int(Core.kiosk_open_min() / 60))
	var end := _hour_picker(row, "Fechamento", int(Core.kiosk_close_min() / 60))
	var days := HFlowContainer.new()
	list.add_child(days)
	var checks: Array = []
	for i in 7:
		var button := CheckButton.new()
		button.text = Core.CompanyRules.Simulation.DAYS[i]
		button.add_theme_font_size_override("font_size", 15)
		button.button_pressed = i in Core.company.sim.days
		days.add_child(button)
		checks.append(button)
	_btn(list, "Salvar horários e dias", func():
		var selected: Array = []
		for i in 7:
			if checks[i].button_pressed:
				selected.append(i)
		if Core.set_kiosk_schedule(int(start.value), int(end.value), selected):
			Core.toast.emit("Horários e dias de funcionamento salvos.", "good")
			refresh())
	_lbl(list, "Escalas dos funcionários são configuradas separadamente. Nos dias fechados, a equipe do quiosque não inicia o turno.", 14, INK_SOFT, false, true)
	_btn(list, "Configurar equipe e turnos", _open_management.bind("gestao_equipe"))

func _app_kiosk_inventory(list: VBoxContainer) -> void:
	_lbl(list, "Ingredientes e reposição", 22, INK, true)
	_lbl(list, "As compras abastecem os produtos disponíveis. Pegue diretamente na geladeira ou no armário; não há etapa de preparo.", 14, INK_SOFT, false, true)
	var cfg: Dictionary = Core.company.sim
	var auto_order := CheckButton.new()
	auto_order.text = "Repor ao começar o dia"
	auto_order.add_theme_font_size_override("font_size", 16)
	auto_order.button_pressed = bool(cfg.auto_order)
	list.add_child(auto_order)
	_lbl(list, "Meta de unidades por ingrediente", 15, INK, true)
	var target := SpinBox.new()
	target.min_value = 1
	target.max_value = 48
	target.step = 1
	target.value = int(cfg.target)
	target.get_line_edit().add_theme_color_override("font_color", INK)
	list.add_child(target)
	_btn(list, "Salvar política de reposição", func():
		Core.set_kiosk_reorder(auto_order.button_pressed, int(target.value))
		refresh())
	var quote: int = Core.CompanyRules.Simulation.reorder_quote(Core)
	_lbl(list, "Reposição até a meta salva: %s" % Core.fmt_money(quote), 17, INK, true, true)
	_btn(list, "Repor agora", func():
		Core.restock_kiosk()
		refresh(), GOOD, Core.money >= quote and quote > 0)
	for id in Core.CompanyRules.Simulation.ingredients(Core):
		var c := _card(list)
		_lbl(c, "%s · %d unidades" % [Economy.SUPPLIES[id].name, int(Core.stock.get(id, 0))], 17, INK, true, true)
		_lbl(c, "Fornecedor hoje: %s/unidade%s" % [Core.fmt_money(Core.supply_total(id, 1)), " · contrato ativo" if Core.contracts.has(id) else ""], 14, INK_SOFT, false, true)
	_lbl(list, "A reposição compra apenas ingredientes do cardápio atual, respeita preços/contratos e só ocorre com saldo para o pedido inteiro. Contratos de desconto são negociados no Mercado.", 14, INK_SOFT, false, true)
	_btn(list, "Mercado e contratos", _open_management.bind("mercado"))

func _app_kiosk_results(list: VBoxContainer) -> void:
	_lbl(list, "Caixa do quiosque", 22, INK, true)
	var d: Dictionary = Core.company.sim.today
	var net: int = int(d.cash_in) - int(d.supplies) - int(d.payroll) - int(d.overhead) - int(d.investment)
	_lbl(list, "Movimento atual: %s" % Core.fmt_money(net, true), 20, GOOD if net >= 0 else BAD, true, true)
	_lbl(list, "Recebimentos: %s\nCompras da despensa: %s\nSalários pagos: %s\nContratação/treinamento/rescisão: %s\nTempo aberto: %.1f h" % [Core.fmt_money(int(d.cash_in)), Core.fmt_money(int(d.supplies)), Core.fmt_money(int(d.payroll)), Core.fmt_money(int(d.investment)), float(d.open_minutes) / 60.0], 16, INK, false, true)
	_lbl(list, "Fechamento: R$ 12 de estrutura + R$ 2/h aberta, cobrados uma vez ao virar o dia. Este é um resultado de caixa: as compras incluem ingredientes compartilhados com o bar; contas ainda não recebidas não entram.", 14, INK_SOFT, false, true)
	_lbl(list, "Contas pendentes: %d · faltas de estoque: %d" % [Core.company.receivables.size(), int(d.stockouts)], 15, INK, true, true)
	_btn(list, "Ajustar preços e cardápio", _open_management.bind("cardapio"))
	for id in Core.kiosk_menu():
		var cost := 0
		for ing in Economy.dish(id).uses:
			cost += Core.supply_total(ing, int(Economy.dish(id).uses[ing]))
		_lbl(list, "%s · venda %s · margem bruta estimada %s" % [Economy.dish(id).name, Core.fmt_money(Core.price_of(id)), Core.fmt_money(Core.price_of(id) - cost, true)], 14, INK, false, true)
	_lbl(list, "Últimos fechamentos", 19, INK, true)
	var history: Array = Core.company.sim.history.duplicate()
	history.reverse()
	if history.is_empty():
		_lbl(list, "O primeiro relatório aparece ao virar o dia.", 14, INK_SOFT)
	for report in history:
		var c := _card(list)
		_lbl(c, "Dia %d · saldo %s" % [int(report.day), Core.fmt_money(int(report.net), true)], 17, GOOD if int(report.net) >= 0 else BAD, true, true)
		_lbl(c, "Estrutura: %s · desperdício: %d produtos · rupturas: %d" % [Core.fmt_money(int(report.overhead)), int(report.waste), int(report.stockouts)], 14, INK_SOFT, false, true)

var _staff_status_labels: Dictionary = {}
func _refresh_staff_status() -> void:
	if app not in ["gestao_equipe", "equipe"]:
		return
	for role in _staff_status_labels:
		var reference: WeakRef = _staff_status_labels[role]
		var label = reference.get_ref()
		if is_instance_valid(label):
			var active: bool = Core.prog.staff_eff(role) > 0
			label.text = "Em serviço" if active else "Fora do turno ou de folga"
			label.add_theme_color_override("font_color", GOOD if active else INK_SOFT)

func _hire_staff(role: String) -> void:
	if Core.hire(role):
		Core.save_game()
		refresh()

func _train_staff(role: String) -> void:
	if Core.prog.train(role):
		Core.save_game()
		refresh()

func _rest_staff(role: String) -> void:
	Core.prog.toggle_off(role)
	Core.save_game()
	refresh()

func _dismiss_staff(role: String) -> void:
	if Core.dismiss_kiosk_staff(role):
		refresh()

# ------------------------------------------------------------------ gestão ampliada
var _candidate_role := "atendente"
var _supplier_id := "horta"
var _supplier_ingredient := "coco"
var _supplier_quantity := 12
var _management_task_label: Label

func _management_action(action: Callable) -> void:
	if action.call():
		Core.save_game()
		refresh()
	else:
		Core.toast.emit("Confira saldo e requisitos desta operação.", "info")

func _choice(parent: Node, title: String, items: Array, selected: int) -> OptionButton:
	_lbl(parent, title, 15, INK, true)
	var control := OptionButton.new()
	control.fit_to_longest_item = false
	for item in items: control.add_item(str(item))
	control.select(maxi(0, selected))
	parent.add_child(control)
	return control

func _app_routine(list: VBoxContainer) -> void:
	var d := Management.state(Core)
	_lbl(list, "Abra, opere e feche o seu dia", 22, INK, true)
	_lbl(list, "Fechar novas chegadas permite terminar os clientes atuais. O fechamento do caixa exige concluir as entregas e recolher a louça; os produtos são pagos na entrega.", 14, INK_SOFT, false, true)
	_btn(list, "Fechar novas chegadas", func(): Core.set_kiosk_open(false); refresh())
	var strict := CheckButton.new()
	strict.text = "Exigir checklist para abrir"
	strict.button_pressed = bool(d.strict)
	strict.toggled.connect(func(value):
		d.strict = value
		if value and not Management.opening_ready(Core): Core.set_kiosk_open(false)
		Management.changed(Core)
		refresh())
	list.add_child(strict)
	_lbl(list, "Limpeza do balcão: %.0f%%" % float(d.counter), 15, INK, true)
	var names := {"limpeza": "Limpar e conferir o balcão", "estoque": "Contar ingredientes do cardápio", "equipe": "Conferir equipe e turnos"}
	for key in names:
		var done: bool = key in d.checks and int(d.day) == Core.day
		_btn(list, ("✓ " if done else "○ ") + str(names[key]), _management_action.bind(Management.check_opening.bind(Core, str(key))), GOOD if done else Color(0.15, 0.55, 0.5), not done and not Core.company.kiosk_open)
	_lbl(list, "Você pode começar sozinho. Prepare as primeiras bebidas em Operação antes de abrir e confira o estado dos equipamentos.", 14, INK_SOFT, false, true)
	_btn(list, "Abrir quiosque", func(): Core.set_kiosk_open(true); refresh(), GOOD, Management.opening_ready(Core))
	_btn(list, "Ver equipamentos e limpeza", _open_management.bind("equipamentos"))
	_lbl(list, "Guardar e fechar", 20, INK, true)
	if Core.company.carry != "": _btn(list, "Devolver item carregado", _management_action.bind(Core.return_company_dish))
	if Core.company.staff_carry != "": _btn(list, "Devolver item da equipe", _management_action.bind(Core.return_company_staff_dish))
	_lbl(list, "Com freezer e geladeira limpa/em bom estado, bebidas guardadas duram mais uma noite. Não podem ser guardadas novamente; comidas continuam vencendo na virada.", 14, INK_SOFT, false, true)
	_btn(list, "Guardar bebidas no freezer", _management_action.bind(Management.store_drinks.bind(Core)), GOOD, Management.can_close(Core) and Core.freezer)
	_lbl(list, "Vendas recebidas hoje (sem gorjetas): " + Core.fmt_money(int(Core.company.sim.today.cash_in)), 16, INK, true)
	_lbl(list, "Informe quanto contou nos recebimentos do quiosque. A conferência registra a diferença sem alterar o saldo.", 14, INK_SOFT, false, true)
	var counted := SpinBox.new()
	counted.min_value = 0
	counted.max_value = 10000000
	counted.step = 1
	counted.get_line_edit().add_theme_color_override("font_color", INK)
	counted.get_line_edit().add_theme_color_override("caret_color", INK)
	counted.value = int(Core.company.sim.today.cash_in)
	list.add_child(counted)
	_btn(list, "Conferir caixa e concluir turno", func(): _management_action(Management.close_shift.bind(Core, int(counted.value))), GOOD, Management.can_close(Core) and int(d.closed_day) != Core.day)
	if not d.closing.is_empty():
		_lbl(list, "Dia %d · contado %s · diferença %s" % [int(d.closing.day), Core.fmt_money(int(d.closing.counted)), Core.fmt_money(int(d.closing.variance), true)], 15, INK, true, true)
	_lbl(list, "Salários e custos de funcionamento são cobrados na virada do dia e aparecem em Resultado.", 14, INK_SOFT, false, true)
	_btn(list, "Atualizar checklist e fechamento", refresh)
	_btn(list, "Ver resultado e custos", _open_management.bind("resultado"))

func _choose_candidate(role: String) -> void:
	_candidate_role = role
	_open_management("recrutamento")

func _app_candidates(list: VBoxContainer) -> void:
	_candidate_role="atendente"
	if not Core.company.created:
		_lbl(list,"Crie sua empresa antes de contratar o atendente.",16,INK)
		_btn(list,"Criar meu quiosque",_open_management.bind("empresa"))
		return
	_lbl(list,"Um atendente para todo o quiosque",18,INK,true)
	var hired: bool = bool(Core.staff.get(_candidate_role, false))
	var record: Dictionary = Management.state(Core).profiles.get(_candidate_role, {})
	if hired:
		var person: String = Management.candidate(_candidate_role, int(record.kind)).name if not record.is_empty() else "Equipe atual"
		_lbl(list, person + " · " + Core.fmt_money(Core.prog.staff_wage(_candidate_role)) + "/dia", 20, INK, true, true)
		if not record.is_empty():
			_lbl(list, "Satisfação: %d%%. Jornadas acima de 8h reduzem a satisfação e aceleram o cansaço; folgas ajudam a recuperar." % int(record.morale), 14, INK_SOFT, false, true)
		_btn(list, "Gerenciar turnos, folgas e treinamento", _open_management.bind("equipe"))
		return
	_lbl(list, "Compare o custo e o perfil. A diária abaixo é a base de 8h no nível 1; turno, experiência e folga modificam o valor. Uma única vaga para o atendimento do quiosque.", 14, INK_SOFT, false, true)
	for kind in 3:
		var p := Management.candidate(_candidate_role, kind)
		var card := _card(list)
		_lbl(card, str(p.name) + " · " + str(p.title), 18, INK, true, true)
		_lbl(card, "Velocidade %d%% · cuidado %d%% · simpatia %d%%\nContratação %s · diária base %s" % [int(p.speed * 100), int(p.care * 100), int(p.social * 100), Core.fmt_money(int(p.cost)), Core.fmt_money(int(p.daily))], 14, INK, false, true)
		_btn(card, "Contratar " + str(p.name), _management_action.bind(Management.hire_candidate.bind(Core, _candidate_role, kind)), GOOD, not hired and Core.money >= int(p.cost))
	_lbl(list, "Velocidade afeta o trabalho; simpatia do garçom melhora gorjetas. A equipe pega os produtos diretamente, sem preparar.", 14, INK_SOFT, false, true)

func _app_suppliers(list: VBoxContainer) -> void:
	var supplies: Array = Economy.SUPPLIES.keys()
	var suppliers: Array = Management.SUPPLIERS.keys()
	var ingredient := _choice(list, "Ingrediente", supplies.map(func(id): return str(Economy.SUPPLIES[id].name)), supplies.find(_supplier_ingredient))
	ingredient.item_selected.connect(func(index): _supplier_ingredient = supplies[index]; refresh())
	_lbl(list, "Em estoque: %d unidades de %s" % [int(Core.stock.get(_supplier_ingredient, 0)), Economy.SUPPLIES[_supplier_ingredient].name], 16, INK, true, true)
	var supplier := _choice(list, "Fornecedor", suppliers.map(func(id): return str(Management.SUPPLIERS[id].name)), suppliers.find(_supplier_id))
	supplier.item_selected.connect(func(index): _supplier_id = suppliers[index]; refresh())
	_lbl(list, "Quantidade (1–48; atacado a partir de 12)", 14, INK)
	var qty := SpinBox.new()
	qty.min_value = int(Management.SUPPLIERS[_supplier_id].min)
	qty.max_value = 48
	qty.step = 1
	qty.get_line_edit().add_theme_color_override("font_color", INK)
	qty.get_line_edit().add_theme_color_override("caret_color", INK)
	qty.value = maxi(_supplier_quantity, int(qty.min_value))
	list.add_child(qty)
	var q: Dictionary = Management.quote(Core, _supplier_id, _supplier_ingredient, int(qty.value))
	var quote_label := _lbl(list, "", 18, INK, true, true)
	var order_action := func():
		var cost: int = int(q.get("cost", -1))
		_management_action(Management.order_supply.bind(Core, _supplier_id, _supplier_ingredient, int(qty.value), cost))
	var order_button := _btn(list, "Pagar e encomendar", order_action, GOOD)
	var update_quote := func(value):
		_supplier_quantity = int(value)
		q.assign(Management.quote(Core, _supplier_id, _supplier_ingredient, int(value)))
		quote_label.text = "Cotação: %s\n%s" % [Core.fmt_money(int(q.get("cost", 0))), "Entrega imediata" if _supplier_id == "express" else "Entrega dia %d às %02d:%02d" % [int(q.get("day", 1)), int(q.get("minute", 0)) / 60, int(q.get("minute", 0)) % 60]]
		order_button.disabled = q.is_empty() or Core.money < int(q.get("cost", 0))
	qty.value_changed.connect(update_quote)
	update_quote.call(qty.value)
	_lbl(list, "Express: +15%, na hora. Horta: −12%, amanhã 08h. Distribuidora: −20%, amanhã 14h, mínimo 12. Contratos e preço do dia entram na cotação. Previsão de tempestade adia a entrega em 1h. Pagamento na encomenda, sem cancelamento.", 14, INK_SOFT, false, true)
	_btn(list, "Atualizar cotação", refresh)
	_lbl(list, "Pedidos a caminho", 19, INK, true)
	for order in Management.state(Core).orders:
		_lbl(list, "#%d · %d × %s · dia %d %02dh · pago %s" % [int(order.id), int(order.qty), Economy.SUPPLIES[order.ingredient].name, int(order.due_day), int(order.due_min) / 60, Core.fmt_money(int(order.cost))], 14, INK, false, true)
	if Management.state(Core).orders.is_empty(): _lbl(list, "Nenhuma entrega pendente.", 14, INK_SOFT)
	for line in Management.state(Core).delivery_log: _lbl(list, str(line), 13, INK_SOFT, false, true)

func _refresh_management_task() -> void:
	if not is_instance_valid(_management_task_label): return
	var task: Dictionary = Management.state(Core).task
	_management_task_label.text = "Nenhum serviço em andamento." if task.is_empty() else "%s: %s · faltam %.0f min do jogo" % [Management.EQUIPMENT[task.item], "limpeza" if task.kind == "clean" else "manutenção", float(task.left)]

func _app_equipment(list: VBoxContainer) -> void:
	_lbl(list, "Conservar os equipamentos", 22, INK, true)
	_lbl(list, "Feche novas chegadas para limpar, reparar ou melhorar. Limpeza leva 12 min do jogo e custa R$ 3; reparo leva 30 min e custa R$ 0,80 por ponto recuperado.", 14, INK_SOFT, false, true)
	_management_task_label = _lbl(list, "", 16, INK, true, true)
	_refresh_management_task()
	for id in Management.EQUIPMENT:
		var item: Dictionary = Management.state(Core).equipment[id]
		var card := _card(list)
		_lbl(card, "%s · nível %d" % [Management.EQUIPMENT[id], int(item.level)], 19, INK, true)
		_lbl(card, "Estado %.0f%% · higiene %.0f%%" % [float(item.condition), float(item.hygiene)], 15, BAD if float(item.condition) < 25 or float(item.hygiene) < 25 else INK, true)
		_btn(card, "Limpar · R$ 3", _management_action.bind(Management.equipment_action.bind(Core, str(id), "clean")), GOOD, float(item.hygiene) < 100)
		_btn(card, "Reparar · " + Core.fmt_money(int(ceil((100 - float(item.condition)) * 0.8))), _management_action.bind(Management.equipment_action.bind(Core, str(id), "repair")), Color(0.8, 0.5, 0.2), float(item.condition) < 100)
		_btn(card, "Melhorar · " + Core.fmt_money(240 * int(item.level)), _management_action.bind(Management.equipment_action.bind(Core, str(id), "upgrade")), Color(0.3, 0.55, 0.8), int(item.level) < 3)
	_lbl(list, "Mantenha os equipamentos limpos e conservados. A retirada dos produtos é imediata e não depende de preparo.", 14, INK_SOFT, false, true)

func _app_customize(list: VBoxContainer) -> void:
	_decor_shop(list)
	_btn(list, "Nome e letras da placa", _open_management.bind("empresa"))
	var current: Dictionary = Management.state(Core).look
	var paints: Array = Management.PAINT.keys()
	var boards: Array = Management.BOARDS.keys()
	var uniforms: Array = Management.UNIFORMS.keys()
	var layouts: Array = ["original", "amplo"]
	var paint := _choice(list, "Pintura", paints.map(func(id): return str(id).capitalize()), paints.find(current.paint))
	var board := _choice(list, "Placa", boards.map(func(id): return str(id).capitalize()), boards.find(current.board))
	var uniform := _choice(list, "Uniforme", uniforms.map(func(id): return str(id).capitalize()), uniforms.find(current.uniform))
	var layout := _choice(list, "Mesas", ["Original", "Mais espaço entre mesas"], layouts.find(current.layout))
	var menu := CheckButton.new()
	menu.text = "Exibir cardápios nas mesas e quadro"
	menu.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	menu.button_pressed = bool(current.menu)
	list.add_child(menu)
	_lbl(list, "Prévia — sem gastar", 20, INK, true)
	var facade := PanelContainer.new()
	list.add_child(facade)
	var sample := _lbl(facade, str(Core.company.name), 22, Color.WHITE, true)
	sample.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sample.add_theme_font_override("font", CompanyRules.font_for(str(Core.company.font)))
	var uniform_preview := _card(list)
	var uniform_label := _lbl(uniform_preview, "Uniforme da equipe", 16, Color.WHITE, true)
	var diagram := Control.new()
	diagram.custom_minimum_size = Vector2(0, 124)
	list.add_child(diagram)
	var choice := func(): return {"paint": paints[paint.selected], "board": boards[board.selected], "uniform": uniforms[uniform.selected], "layout": layouts[layout.selected], "menu": menu.button_pressed}
	var preview := func():
		var selected: Dictionary = choice.call()
		facade.add_theme_stylebox_override("panel", _box(Management.BOARDS[selected.board], 12, 12))
		uniform_preview.get_parent().add_theme_stylebox_override("panel", _box(Management.UNIFORMS[selected.uniform], 12, 12))
		uniform_label.text = "Uniforme: " + str(selected.uniform).capitalize()
		sample.add_theme_color_override("font_color", CompanyRules.COLORS[str(Core.company.color)])
		diagram.queue_redraw()
	diagram.draw.connect(func():
		var selected: Dictionary = choice.call()
		var center_x := diagram.size.x * 0.5
		diagram.draw_rect(Rect2(center_x - 42, 4, 84, 30), Management.PAINT[selected.paint])
		var spread := 100.0 if selected.layout == "amplo" else 70.0
		for pos in [Vector2(center_x - spread, 58), Vector2(center_x + spread, 58), Vector2(center_x - spread, 100)]:
			diagram.draw_circle(pos, 14, Color(0.65, 0.45, 0.25))
			if selected.menu: diagram.draw_rect(Rect2(pos - Vector2(3, 6), Vector2(6, 12)), Color.WHITE))
	for control in [paint, board, uniform, layout]: control.item_selected.connect(preview.unbind(1))
	menu.toggled.connect(preview.unbind(1))
	preview.call()
	_lbl(list, "O esquema mostra as cores e a disposição; o quiosque usa os modelos detalhados atuais. Mudar as mesas move também os lugares de sentar, os pontos de entrega e o bloqueio de circulação.", 14, INK_SOFT, false, true)
	_btn(list, "Aplicar personalização · R$ 180", func(): _management_action(Management.apply_look.bind(Core, choice.call())), GOOD, Core.money >= 180)
	_lbl(list, "Aplique com o quiosque fechado, sem clientes ou louça. Reaplicar a mesma seleção já comprada não cobra novamente. Nome, fonte e cor das letras continuam em Aparência e nome → Nome e letras da placa.", 14, INK_SOFT, false, true)

func _app_demand(list: VBoxContainer) -> void:
	var factor := Management.arrival_factor(Core)
	_lbl(list, "Movimento de agora", 22, INK, true)
	_lbl(list, "%s · chegada de clientes ×%.2f" % [Core.clock_text(), factor], 18, INK, true)
	_lbl(list, "06–10h: ritmo leve, sucos e tapioca. 11–14h: pico do almoço e pratos. 14–17h: bebidas. Depois das 17h: petiscos e bebidas de fim de tarde.", 14, INK_SOFT, false, true)
	_lbl(list, "Chuva reduz o movimento em 35%; tempestade reduz ainda mais. Novas chegadas não ocupam mesas descobertas na chuva. Mesas com guarda-sol e lugares no balcão continuam disponíveis.", 14, INK_SOFT, false, true)
	var village = get_tree().get_first_node_in_group("kiosk")
	var covered := 0
	var total := 0
	if village:
		for spot in village.world.kiosk_spots:
			if spot.get("need", "") != "" and not Core.has(str(spot.need)): continue
			total += 1
			if Management.sheltered(Core, spot): covered += 1
	_lbl(list, "Lugares utilizáveis no clima atual: %d/%d" % [covered, total], 16, INK, true)
	for id in Core.kiosk_menu():
		_lbl(list, "%s · preferência de horário ×%.2f" % [Economy.dish(id).name, Management.dish_weight(Core, str(id))], 15, INK, false, true)
	_lbl(list, "Os fatores combinam com preços, eventos e condições já existentes. Preferência altera a chance do pedido, sem garantir vendas.", 14, INK_SOFT, false, true)
	_btn(list, "Atualizar movimento", refresh)
	_btn(list, "Planejar horários", _open_management.bind("horarios"))

func _campaign_cards(list: VBoxContainer) -> void:
	var campaign=Core.prog.Campaign
	var current: Dictionary=campaign.current(Core.prog)
	_lbl(list,"CAMPANHA PRINCIPAL · Uma nova maré",19,INK,true)
	if current.is_empty(): _lbl(list,"Campanha concluída! O resort continua aberto para sua história.",15,GOOD,false,true)
	else:
		var card:=_card(list)
		_lbl(card,"%d/%d · %s" % [int(Core.prog.campaign.stage)+1,campaign.MAIN.size(),current.title],17,INK,true,true)
		_lbl(card,str(current.story),14,INK_SOFT,false,true)
		_lbl(card,"%s · %d/%d" % [current.task,mini(campaign.amount(Core.prog,current),int(current.qty)),int(current.qty)],15,INK,true,true)
		_btn(card,"Concluir · "+Core.fmt_money(int(current.reward)),_claim_campaign.bind(str(current.id),false),GOOD,campaign.ready(Core.prog,current))
	_lbl(list,"MISSÕES SECUNDÁRIAS",17,INK,true)
	for q in campaign.SIDE:
		var done: bool=q.id in Core.prog.campaign.side_done
		var card:=_card(list)
		var row:=_row(card)
		var info:=VBoxContainer.new()
		info.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		row.add_child(info)
		_lbl(info,("✓ " if done else "")+str(q.title),16,INK,true,true)
		_lbl(info,"%s · %d/%d" % [q.task,mini(campaign.amount(Core.prog,q),int(q.qty)),int(q.qty)],13,INK_SOFT,false,true)
		if not done:_btn(row,"Concluir · "+Core.fmt_money(int(q.reward)),_claim_campaign.bind(str(q.id),true),GOOD,campaign.ready(Core.prog,q))
	_btn(list,"Histórias da vila · píer, prainha e carnaval",_open_management.bind("vila"))
func _claim_campaign(id: String,side: bool) -> void:
	Core.prog.Campaign.claim(Core.prog,id,side)
	refresh()

func _decor_shop(list: VBoxContainer) -> void:
	var refinement=get_tree().current_scene.get_node("Refinements")
	_lbl(list,"Melhorias que aparecem no quiosque",17,INK,true,true)
	for id in refinement.DECOR:
		var data: Dictionary=refinement.DECOR[id]
		var card:=_card(list)
		_lbl(card,str(data.title),16,INK,true,true)
		_lbl(card,str(data.description),13,INK_SOFT,false,true)
		var owned: bool=bool(Core.prog.experience.decor.get(id,false))
		_btn(card,"Instalado" if owned else "Comprar · "+Core.fmt_money(int(data.price)),func():
			refinement.buy_decor(str(id))
			refresh(),GOOD,not owned and Core.money>=int(data.price))

func _app_conversation(list: VBoxContainer) -> void:
	var q: Dictionary=Core.prog.Campaign.current(Core.prog)
	var ref=get_tree().current_scene.get_node("Refinements")
	var speaker: String=ref.SPEAKERS[mini(int(Core.prog.campaign.stage),ref.SPEAKERS.size()-1)]
	_lbl(list,resident_name,20,INK,true,true)
	var card:=_card(list)
	var own: bool=resident_name==speaker
	_lbl(card,str(q.get("story","A vila cresceu com seu cuidado. Obrigado!")) if own else "Que bom ver você! "+speaker+" está acompanhando sua próxima etapa.",16,INK,false,true)
	_lbl(card,str(q.get("task","Explore as missões secundárias.")),15,INK_SOFT,true,true)
	if own and Core.prog.Campaign.ready(Core.prog,q):
		_btn(card,"Concluir etapa",func():
			Core.prog.Campaign.claim(Core.prog,str(q.id))
			refresh(),GOOD)
	_btn(list,"Acompanhar missões",_open_management.bind("missoes"))
	_btn(list,"Até logo",close)
