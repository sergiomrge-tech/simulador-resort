extends CanvasLayer
## Menu principal (Novo jogo / Continuar / Configurações / Sair), slots de save,
## menu de pausa (Esc / Start) e painel completo de configurações. Funciona com mouse, controle e toque.

signal start_new(slot: int)
signal start_load(slot: int)
signal go_main_menu

var root: Control
var fade_rect: ColorRect
var main_p: Control
var slots_p: Control
var pause_p: Control
var settings_p: Control
var _slot_mode := "new"
var _confirm_slot := -1
var _rebind_action := ""
var _rebind_btn: Button
var _settings_back: Control
var in_menu := true
var touch := false

const C_BG := Color(0.98, 0.95, 0.88, 0.97)
const C_TITLE := Color(0.05, 0.4, 0.45)
const C_TEXT := Color(0.2, 0.15, 0.1)

func _ready() -> void:
	layer = 10
	process_mode = Node.PROCESS_MODE_ALWAYS
	touch = Quality.is_touch()
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	root.theme = UiTheme.get_theme()
	fade_rect = ColorRect.new()
	fade_rect.color = Color(0, 0, 0, 0)
	fade_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	fade_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_all()
	Quality.changed.connect(func(): pass)

func _build_all() -> void:
	for c in root.get_children():
		if c != fade_rect:
			c.queue_free()
	if fade_rect.get_parent() == null:
		root.add_child(fade_rect)
	main_p = _build_main()
	slots_p = _panel(Vector2(760, 560))
	pause_p = _build_pause()
	settings_p = _build_settings()
	root.move_child(fade_rect, root.get_child_count() - 1)
	for p in [main_p, slots_p, pause_p, settings_p]:
		p.visible = false

# ------------------------------------------------------------------ helpers de UI
func _style(c: Color, r: int, border := Color(0, 0, 0, 0), bw := 0) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = c
	s.set_corner_radius_all(r)
	s.content_margin_left = 22
	s.content_margin_right = 22
	s.content_margin_top = 10
	s.content_margin_bottom = 10
	if bw > 0:
		s.border_color = border
		s.set_border_width_all(bw)
	return s

func _panel(sz: Vector2) -> PanelContainer:
	var p := PanelContainer.new()
	p.set_anchors_preset(Control.PRESET_CENTER)
	p.position = -sz * 0.5
	p.size = sz
	p.custom_minimum_size = sz
	p.add_theme_stylebox_override("panel", _style(C_BG, 24))
	root.add_child(p)
	var vb := VBoxContainer.new()
	vb.name = "VB"
	vb.add_theme_constant_override("separation", 14)
	p.add_child(vb)
	return p

func _vb(p: Control) -> VBoxContainer:
	return p.get_node("VB")

func _title(parent: Node, t: String, fs := 40) -> Label:
	var l := Label.new()
	l.text = t
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", fs)
	l.add_theme_color_override("font_color", C_TITLE)
	parent.add_child(l)
	return l

func _text(parent: Node, t: String, fs := 24, col := C_TEXT) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", fs)
	l.add_theme_color_override("font_color", col)
	parent.add_child(l)
	return l

func _btn(parent: Node, t: String, cb: Callable, h := 62, fs := 28, col := Color(0.06, 0.5, 0.52)) -> Button:
	var b := Button.new()
	b.text = t
	b.custom_minimum_size = Vector2(0, h)
	b.add_theme_font_size_override("font_size", fs)
	b.add_theme_color_override("font_color", Color.WHITE)
	b.add_theme_color_override("font_hover_color", Color.WHITE)
	b.add_theme_color_override("font_focus_color", Color.WHITE)
	b.add_theme_color_override("font_pressed_color", Color.WHITE)
	b.add_theme_color_override("font_disabled_color", Color(1, 1, 1, 0.45))
	b.add_theme_stylebox_override("normal", _style(col, 16))
	b.add_theme_stylebox_override("hover", _style(col.lightened(0.15), 16))
	b.add_theme_stylebox_override("pressed", _style(col.lightened(0.3), 16))
	b.add_theme_stylebox_override("disabled", _style(col.darkened(0.2).lerp(Color(0.6, 0.6, 0.6), 0.6), 16))
	b.add_theme_stylebox_override("focus", _style(Color(0, 0, 0, 0), 16, Color(1.0, 0.8, 0.2), 4))
	b.pressed.connect(func():
		get_tree().call_group("audio", "sfx", "click", -10.0)
		cb.call())
	parent.add_child(b)
	return b

func _row(parent: Node, label: String) -> HBoxContainer:
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 16)
	parent.add_child(hb)
	var l := _text(hb, label, 23)
	l.custom_minimum_size = Vector2(300, 0)
	return hb

func _slider(parent: Node, mn: float, mx: float, step: float, val: float, cb: Callable, fmt: Callable) -> HSlider:
	var s := HSlider.new()
	s.min_value = mn
	s.max_value = mx
	s.step = step
	s.value = val
	s.custom_minimum_size = Vector2(300, 36)
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var vl := _text(parent, fmt.call(val), 22)
	vl.custom_minimum_size = Vector2(90, 0)
	vl.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	parent.add_child(s)
	parent.move_child(s, vl.get_index())
	s.value_changed.connect(func(v):
		vl.text = fmt.call(v)
		cb.call(v))
	return s

func _option(parent: Node, items: Array, sel: int, cb: Callable) -> OptionButton:
	var o := OptionButton.new()
	for it in items:
		o.add_item(str(it))
	o.select(sel)
	o.custom_minimum_size = Vector2(360, 46)
	o.add_theme_font_size_override("font_size", 22)
	o.item_selected.connect(cb)
	parent.add_child(o)
	return o

func _check(parent: Node, on: bool, cb: Callable) -> CheckButton:
	var c := CheckButton.new()
	c.button_pressed = on
	c.toggled.connect(cb)
	parent.add_child(c)
	return c

func _show(p: Control) -> void:
	for q in [main_p, slots_p, pause_p, settings_p]:
		q.visible = q == p
	if p:
		var f := p.find_children("*", "Button", true, false)
		for b in f:
			if not b.disabled and b.is_visible_in_tree():
				b.grab_focus()
				break

# ------------------------------------------------------------------ menu principal
func _build_main() -> Control:
	var c := Control.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(c)
	var grad := TextureRect.new()
	var g := Gradient.new()
	g.colors = PackedColorArray([Color(0, 0.05, 0.08, 0.78), Color(0, 0.05, 0.08, 0.0)])
	var gt := GradientTexture2D.new()
	gt.gradient = g
	gt.fill_from = Vector2(0, 0)
	gt.fill_to = Vector2(1, 0)
	grad.texture = gt
	# LEFT_WIDE tem âncoras verticais diferentes: size é descartado. A largura vai no offset.
	grad.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	grad.offset_left = 0.0
	grad.offset_right = 900.0
	grad.offset_top = 0.0
	grad.offset_bottom = 0.0
	grad.custom_minimum_size = Vector2(900, 0)
	grad.stretch_mode = TextureRect.STRETCH_SCALE
	grad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	c.add_child(grad)
	var vb := VBoxContainer.new()
	vb.position = Vector2(90, 64)
	vb.custom_minimum_size = Vector2(460, 0)
	vb.add_theme_constant_override("separation", 16)
	c.add_child(vb)
	var t := Label.new()
	t.text = "Maré Alta Resort"
	t.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	t.add_theme_font_size_override("font_size", 72)
	t.add_theme_color_override("font_color", Color(1.0, 0.95, 0.82))
	t.add_theme_color_override("font_outline_color", Color(0.02, 0.2, 0.25))
	t.add_theme_constant_override("outline_size", 14)
	vb.add_child(t)
	var st := Label.new()
	st.text = "Uma pousada na vila de pescadores"
	st.add_theme_font_size_override("font_size", 28)
	st.add_theme_color_override("font_color", Color(0.75, 0.95, 0.95))
	st.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.7))
	st.add_theme_constant_override("outline_size", 6)
	vb.add_child(st)
	var sp := Control.new()
	sp.custom_minimum_size = Vector2(0, 18)
	vb.add_child(sp)
	var cont := _btn(vb, "Continuar", _on_continue, 70, 30)
	cont.name = "Continue"
	_btn(vb, "Novo jogo", func(): _open_slots("new"), 70, 30)
	_btn(vb, "Carregar jogo", func(): _open_slots("load"), 62, 26)
	_btn(vb, "Configurações", func(): _open_settings(main_p), 62, 26)
	if not touch:
		_btn(vb, "Sair", func(): get_tree().quit(), 62, 26, Color(0.55, 0.25, 0.2))
	var ver := Label.new()
	ver.text = "v%s  ·  %s" % [ProjectSettings.get_setting("application/config/version", "0.2.0"), "PC" if Quality.hd else "Mobile"]
	ver.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
	ver.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	ver.position = Vector2(24, -44)
	ver.add_theme_font_size_override("font_size", 18)
	ver.add_theme_color_override("font_color", Color(1, 1, 1, 0.7))
	c.add_child(ver)
	return c

func show_main() -> void:
	in_menu = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var any := latest_slot() > 0
	var cb: Button = main_p.find_child("Continue", true, false)
	cb.disabled = not any
	_show(main_p)

static func latest_slot() -> int:
	var best := 0
	var best_t := ""
	for i in range(1, 4):
		var s: Dictionary = Core.slot_summary(i)
		if s.is_empty():
			continue
		if best == 0 or str(s.saved_at) > best_t:
			best = i
			best_t = str(s.saved_at)
	return best

func _on_continue() -> void:
	var s := latest_slot()
	if s > 0:
		_launch(func(): start_load.emit(s))

func _launch(cb: Callable) -> void:
	in_menu = false
	_show(null)
	fade(cb)

# ------------------------------------------------------------------ slots
func _open_slots(mode: String) -> void:
	_slot_mode = mode
	_confirm_slot = -1
	_fill_slots()
	_show(slots_p)

func _fill_slots() -> void:
	var vb := _vb(slots_p)
	for ch in vb.get_children():
		ch.free()
	_title(vb, "Novo jogo — escolha um slot" if _slot_mode == "new" else "Carregar jogo")
	for i in range(1, 4):
		var s: Dictionary = Core.slot_summary(i)
		var txt := ""
		if s.is_empty():
			txt = tr("Slot %d  —  vazio") % i
		else:
			var h := int(s.minutes / 60.0)
			txt = tr("Slot %d  —  Dia %d, %02d:%02d  ·  %s  ·  %s") % [i, s.day, h, int(s.minutes) % 60, Core.fmt_money(s.money), str(s.saved_at).replace("T", " ").left(16)]
		if _confirm_slot == i:
			txt = tr("Substituir o slot %d? Clique de novo para confirmar") % i
		var idx := i
		var b := _btn(vb, txt, func(): _pick_slot(idx), 72, 22, Color(0.06, 0.5, 0.52) if _confirm_slot != i else Color(0.7, 0.35, 0.1))
		b.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		b.disabled = _slot_mode == "load" and s.is_empty()
	_btn(vb, "Voltar", func(): show_main() if in_menu else _show(pause_p), 56, 24, Color(0.4, 0.4, 0.4))

func _pick_slot(i: int) -> void:
	var used := not Core.slot_summary(i).is_empty()
	if _slot_mode == "load":
		_launch(func(): start_load.emit(i))
		return
	if used and _confirm_slot != i:
		_confirm_slot = i
		_fill_slots()
		return
	_launch(func(): start_new.emit(i))

# ------------------------------------------------------------------ pausa
func _build_pause() -> Control:
	var p := _panel(Vector2(560, 560))
	var vb := _vb(p)
	_title(vb, "Pausa")
	_btn(vb, "Continuar", toggle_pause, 66, 28)
	_btn(vb, "Configurações", func(): _open_settings(pause_p))
	var sv := _btn(vb, "Salvar jogo", func():
		Core.save_game()
		Core.toast.emit(tr("Jogo salvo (slot %d).") % Core.slot, "good"))
	sv.name = "Save"
	_btn(vb, "Menu principal", func():
		Core.save_game()
		get_tree().paused = false
		go_main_menu.emit(), 62, 26, Color(0.35, 0.4, 0.5))
	if not touch:
		_btn(vb, "Sair do jogo", func():
			Core.save_game()
			get_tree().quit(), 62, 26, Color(0.55, 0.25, 0.2))
	return p

func toggle_pause() -> void:
	if in_menu:
		return
	var open := not (pause_p.visible or settings_p.visible or slots_p.visible)
	get_tree().paused = open
	if open:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		_show(pause_p)
	else:
		_show(null)
		if not touch:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	get_tree().call_group("audio", "sfx", "click", -10.0)

func is_open() -> bool:
	return in_menu or pause_p.visible or settings_p.visible or slots_p.visible

# ------------------------------------------------------------------ configurações
func _open_settings(back: Control) -> void:
	_settings_back = back
	_show(settings_p)

func _build_settings() -> Control:
	var p := _panel(Vector2(980, 680))
	var vb := _vb(p)
	_title(vb, "Configurações", 38)
	var tabs := TabContainer.new()
	tabs.custom_minimum_size = Vector2(920, 500)
	tabs.add_theme_font_size_override("font_size", 24)
	vb.add_child(tabs)
	# --- vídeo
	var vid := VBoxContainer.new()
	vid.name = tr("Vídeo")
	vid.add_theme_constant_override("separation", 10)
	tabs.add_child(vid)
	var r := _row(vid, "Qualidade gráfica")
	var presets := []
	for n in Quality.PRESETS:
		presets.append(tr(n))
	var po := _option(r, presets, Quality.preset, func(i): Quality.set_preset(i))
	po.disabled = not Quality.hd
	if not Quality.hd:
		_text(vid, "Celular: modo leve fixo (renderer Mobile).", 20, Color(0.45, 0.3, 0.2))
	if not touch:
		r = _row(vid, "Modo de janela")
		var wm := []
		for n in Quality.WINDOW_MODES:
			wm.append(tr(n))
		_option(r, wm, Quality.window_mode, func(i): Quality.set_window_mode(i))
		r = _row(vid, "Resolução (janela)")
		var res := []
		for v in Quality.RESOLUTIONS:
			res.append("%d × %d" % [v.x, v.y])
		_option(r, res, Quality.resolution, func(i): Quality.set_resolution(i))
		r = _row(vid, "V-Sync")
		_check(r, Quality.vsync, func(on): Quality.set_vsync(on))
	r = _row(vid, "Escala 3D (FSR 2)")
	_slider(r, 50, 100, 5, Quality.scale * 100.0, func(v): Quality.set_scale(v / 100.0), func(v): return "%d%%" % int(v))
	r = _row(vid, "Escala da interface")
	_slider(r, 75, 150, 5, Quality.ui_scale * 100.0, func(v): Quality.set_ui_scale(v / 100.0), func(v): return "%d%%" % int(v))
	r = _row(vid, "Campo de visão (FOV)")
	_slider(r, 60, 100, 1, Quality.fov, func(v): Quality.set_fov(v), func(v): return "%d°" % int(v))
	# --- áudio
	var aud := VBoxContainer.new()
	aud.name = tr("Áudio")
	aud.add_theme_constant_override("separation", 14)
	tabs.add_child(aud)
	r = _row(aud, "Volume geral")
	_slider(r, 0, 100, 1, Quality.vol_master * 100.0, func(v): Quality.set_volume("Master", v / 100.0), func(v): return "%d%%" % int(v))
	r = _row(aud, "Música")
	_slider(r, 0, 100, 1, Quality.vol_music * 100.0, func(v): Quality.set_volume("Music", v / 100.0), func(v): return "%d%%" % int(v))
	r = _row(aud, "Efeitos e ambiente")
	_slider(r, 0, 100, 1, Quality.vol_sfx * 100.0, func(v): Quality.set_volume("SFX", v / 100.0), func(v): return "%d%%" % int(v))
	# --- controles
	var ctl := VBoxContainer.new()
	ctl.name = tr("Controles")
	ctl.add_theme_constant_override("separation", 8)
	tabs.add_child(ctl)
	r = _row(ctl, "Sensibilidade (mouse/controle)")
	_slider(r, 20, 300, 5, Quality.sensitivity * 100.0, func(v): Quality.set_sensitivity(v / 100.0), func(v): return "%.2f×" % (v / 100.0))
	r = _row(ctl, "Inverter eixo Y")
	_check(r, Quality.invert_y, func(on): Quality.set_invert_y(on))
	if not touch:
		var sc := ScrollContainer.new()
		sc.custom_minimum_size = Vector2(0, 260)
		ctl.add_child(sc)
		var kv := VBoxContainer.new()
		kv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		sc.add_child(kv)
		for a in Quality.REBINDABLE:
			r = _row(kv, Quality.ACTION_NAMES[a])
			var act: String = a
			var holder := []
			var kb := _btn(r, Quality.key_name(a), func(): _start_rebind(act, holder[0]), 44, 22)
			holder.append(kb)
			kb.custom_minimum_size = Vector2(220, 44)
			kb.auto_translate_mode = Node.AUTO_TRANSLATE_MODE_DISABLED
		_btn(kv, "Restaurar teclas padrão", func():
			Quality.reset_keys()
			_rebuild_keep(2), 46, 22, Color(0.4, 0.4, 0.4))
		_text(ctl, "Controle: analógico esquerdo anda, direito olha · A interagir · Y loja · Start pausa · L3 correr", 18, Color(0.35, 0.3, 0.25))
	# --- idioma
	var lang := VBoxContainer.new()
	lang.name = tr("Idioma")
	tabs.add_child(lang)
	r = _row(lang, "Idioma / Language")
	_option(r, ["Português (Brasil)", "English"], 1 if Quality.language == "en" else 0, func(i):
		Quality.set_language("en" if i == 1 else "pt")
		_rebuild_keep(3))
	_btn(vb, "Voltar", func(): _show(_settings_back), 56, 24, Color(0.4, 0.4, 0.4))
	return p

func _rebuild_keep(tab: int) -> void:
	var back_is_pause := _settings_back == pause_p
	call_deferred("_do_rebuild", tab, back_is_pause)

func _do_rebuild(tab: int, back_is_pause: bool) -> void:
	_build_all()
	_settings_back = pause_p if back_is_pause else main_p
	var tabs: TabContainer = settings_p.find_children("*", "TabContainer", true, false)[0]
	tabs.current_tab = tab
	_show(settings_p)

func _start_rebind(action: String, b: Button) -> void:
	_rebind_action = action
	_rebind_btn = b
	b.text = tr("Pressione uma tecla…")

func _unhandled_input(e: InputEvent) -> void:
	if _rebind_action != "" and e is InputEventKey and e.pressed:
		if e.physical_keycode != KEY_ESCAPE:
			Quality.rebind(_rebind_action, e.physical_keycode)
		_rebind_btn.text = Quality.key_name(_rebind_action)
		_rebind_action = ""
		get_viewport().set_input_as_handled()
		return
	if settings_p.visible and e is InputEventJoypadButton and e.pressed and e.button_index in [JOY_BUTTON_LEFT_SHOULDER, JOY_BUTTON_RIGHT_SHOULDER]:
		var tabs: TabContainer = settings_p.find_children("*", "TabContainer", true, false)[0]
		tabs.current_tab = wrapi(tabs.current_tab + (1 if e.button_index == JOY_BUTTON_RIGHT_SHOULDER else -1), 0, tabs.get_tab_count())
		get_viewport().set_input_as_handled()
		return
	if e.is_action_pressed("pause") or (e is InputEventJoypadButton and e.pressed and e.button_index == JOY_BUTTON_B):
		if settings_p.visible:
			_show(_settings_back)
			get_viewport().set_input_as_handled()
		elif slots_p.visible:
			show_main() if in_menu else _show(pause_p)
			get_viewport().set_input_as_handled()
		elif pause_p.visible:
			toggle_pause()
			get_viewport().set_input_as_handled()

# ------------------------------------------------------------------ toque (emulate_mouse_from_touch=false)
func _input(e: InputEvent) -> void:
	if not (e is InputEventScreenTouch and e.pressed):
		return
	if not is_open():
		return
	var visible_root: Control = null
	for p in [main_p, slots_p, pause_p, settings_p]:
		if p.visible:
			visible_root = p
	if visible_root == null:
		return
	for c in visible_root.find_children("*", "Control", true, false):
		if not c.is_visible_in_tree() or not c.get_global_rect().has_point(e.position):
			continue
		if c is HSlider:
			var rr: Rect2 = c.get_global_rect()
			c.value = c.min_value + (c.max_value - c.min_value) * clampf((e.position.x - rr.position.x) / rr.size.x, 0.0, 1.0)
			get_viewport().set_input_as_handled()
			return
		if c is OptionButton:
			c.select((c.selected + 1) % c.item_count)
			c.item_selected.emit(c.selected)
			get_viewport().set_input_as_handled()
			return
		if c is BaseButton and not c.disabled:
			if c.toggle_mode:
				c.button_pressed = not c.button_pressed
			else:
				c.pressed.emit()
			get_viewport().set_input_as_handled()
			return
		if c is TabContainer and e.position.y - c.global_position.y < 48.0:
			var tb: TabBar = c.get_tab_bar()
			var idx := tb.get_tab_idx_at_point(e.position - tb.global_position)
			if idx >= 0:
				c.current_tab = idx
			get_viewport().set_input_as_handled()
			return
	get_viewport().set_input_as_handled()

# ------------------------------------------------------------------ fade
func fade(mid: Callable, dur := 0.45) -> void:
	fade_rect.mouse_filter = Control.MOUSE_FILTER_STOP
	var tw := create_tween()
	tw.set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tw.tween_property(fade_rect, "color:a", 1.0, dur)
	tw.tween_callback(mid)
	tw.tween_interval(0.25)
	tw.tween_property(fade_rect, "color:a", 0.0, dur)
	tw.tween_callback(func(): fade_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE)
