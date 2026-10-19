extends CanvasLayer
## v1.0 — minijogo do balcão dos negócios: 3 rodadas de "acerte o tempo". Um cursor vai e volta numa barra;
## aperte E / Espaço / clique / toque quando ele estiver na faixa verde. A faixa encolhe a cada rodada.
## Cada negócio tem seu tema (texto e cores). Resultado 0..3 vai para Core.prog.play_result(id, acertos).
## Pausa o jogo enquanto está aberto (process_mode ALWAYS).

const T: = preload("res://scripts/ui_theme.gd")
const STEPS: = {
	"sorveteria": ["Bola de baunilha na casquinha!", "Agora a de morango!", "Calda de chocolate por cima!"],
	"aluguel": ["Passe a parafina na prancha!", "Aperte o colete do cliente!", "Empurre o caiaque na água!"],
	"surfe": ["Remada! (aluno deitado na prancha)", "Hora de levantar!", "Equilíbrio na onda!"],
	"food_truck": ["Massa na chapa!", "Recheio de camarão!", "Tire da fritura no ponto!"],
	"souvenir": ["Escolha a lembrança!", "Papel de presente!", "Fita e laço!"],
}

var biz_id: = ""
var round_i: = 0
var hits: = 0
var t: = 0.0
var speed: = 1.0
var zone_c: = 0.5
var zone_w: = 0.22
var waiting: = false
var _age: = 0.0
var no_pause: = false     # depuração (--minigame): não pausa, para o print sair
var _was_paused: = false
var _mouse_before: int = Input.MOUSE_MODE_VISIBLE

var panel: PanelContainer
var title_l: Label
var step_l: Label
var bar: Control
var info_l: Label
var dots_l: Label

func _ready() -> void:
	layer = 50
	process_mode = Node.PROCESS_MODE_ALWAYS

func start(id: String) -> void:
	biz_id = id
	_was_paused = get_tree().paused
	if not no_pause:
		get_tree().paused = true
	_mouse_before = Input.mouse_mode
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var root: = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.theme = T.get_theme()
	add_child(root)
	var dim: = ColorRect.new()
	dim.color = Color(0, 0, 0, 0.35)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(dim)
	panel = PanelContainer.new()
	var col: Color = PD.BUSINESSES[id].tint
	panel.add_theme_stylebox_override("panel", T.box(Color(1.0, 0.98, 0.93, 0.97), 28, col.darkened(0.2), 5, 16, 26))
	panel.custom_minimum_size = Vector2(620, 0)
	panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	panel.position = Vector2(-310, -330)
	root.add_child(panel)
	panel.anchor_left = 0.5
	panel.anchor_right = 0.5
	panel.anchor_top = 1.0
	panel.anchor_bottom = 1.0
	panel.offset_left = -310
	panel.offset_right = 310
	panel.offset_top = -330
	panel.offset_bottom = -60
	var v: = VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	panel.add_child(v)
	title_l = _label(v, tr(str(PD.BUSINESSES[id].game)), 30, col.darkened(0.45))
	step_l = _label(v, "", 22, Color(0.16, 0.13, 0.2))
	bar = Control.new()
	bar.custom_minimum_size = Vector2(560, 54)
	bar.draw.connect(_draw_bar)
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(bar)
	dots_l = _label(v, "", 26, Color(0.16, 0.13, 0.2))
	info_l = _label(v, tr("Aperte %s (ou clique) quando o marcador estiver no verde. Esc sai.") % Quality.key_name("interact"), 15, Color(0.42, 0.38, 0.46))
	_next_round()

func _label(p: Node, txt: String, fs: int, c: Color) -> Label:
	var l: = Label.new()
	l.text = txt
	l.add_theme_font_size_override("font_size", fs)
	l.add_theme_color_override("font_color", c)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	p.add_child(l)
	return l

func _next_round() -> void:
	waiting = false
	var steps: Array = STEPS.get(biz_id, ["Atenda o cliente!", "Capriche!", "Finalize!"])
	step_l.text = "%d/3 · %s" % [round_i + 1, tr(str(steps[round_i]))]
	zone_w = [0.24, 0.17, 0.12][round_i]
	zone_c = randf_range(0.2, 0.8)
	speed = [0.9, 1.15, 1.45][round_i]
	t = randf() * 2.0
	_update_dots()

func _update_dots() -> void:
	var s: = ""
	for i in 3:
		s += ("★ " if i < hits else ("☆ " if i < round_i else "· "))
	dots_l.text = s.strip_edges()

func _pos() -> float:
	# ping-pong 0..1 suavizado nas pontas
	var p: = fmod(t * speed, 2.0)
	p = p if p <= 1.0 else 2.0 - p
	return p

func _process(delta: float) -> void:
	_age += delta
	if not waiting:
		t += delta
	if bar:
		bar.queue_redraw()

func _draw_bar() -> void:
	var w: = bar.size.x
	var h: = bar.size.y
	bar.draw_rect(Rect2(0, 10, w, h - 20), Color(0.85, 0.85, 0.9), true)
	var zx: = (zone_c - zone_w * 0.5) * w
	bar.draw_rect(Rect2(zx, 10, zone_w * w, h - 20), Color(0.25, 0.75, 0.4), true)
	bar.draw_rect(Rect2(zx + zone_w * w * 0.35, 10, zone_w * w * 0.3, h - 20), Color(0.15, 0.6, 0.3), true)
	var x: = _pos() * w
	bar.draw_rect(Rect2(x - 5, 0, 10, h), Color(0.95, 0.35, 0.2) if not waiting else Color(0.2, 0.2, 0.25), true)

func _input(e: InputEvent) -> void:
	if biz_id == "" or _age < 0.2:
		return
	var hit: = false
	if e is InputEventKey and e.pressed and not e.echo:
		if e.is_action("pause"):
			_finish()
			get_viewport().set_input_as_handled()
			return
		hit = e.is_action("interact") or e.is_action("ui_accept") or e.physical_keycode == KEY_SPACE
	elif e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
		hit = true
	elif e is InputEventScreenTouch and e.pressed:
		hit = true
	elif e is InputEventJoypadButton and e.pressed:
		hit = e.button_index == JOY_BUTTON_A
		if e.button_index == JOY_BUTTON_B:
			_finish()
	if not hit:
		return
	get_viewport().set_input_as_handled()
	if waiting:
		return
	waiting = true
	var p: = _pos()
	var ok: = absf(p - zone_c) <= zone_w * 0.5
	if ok:
		hits += 1
		get_tree().call_group("audio", "sfx", "click", -2.0, 1.3 + 0.15 * float(hits))
		step_l.text = tr("Perfeito!") if absf(p - zone_c) <= zone_w * 0.15 else tr("Boa!")
	else:
		get_tree().call_group("audio", "sfx", "click", -6.0, 0.6)
		step_l.text = tr("Ops, passou do ponto...")
	round_i += 1
	_update_dots()
	var tm: = get_tree().create_timer(0.7, true, false, true)
	tm.timeout.connect(func():
		if round_i >= 3:
			_finish()
		else:
			_next_round())

func _finish() -> void:
	if biz_id == "":
		return
	var id: = biz_id
	biz_id = ""
	get_tree().paused = _was_paused
	Input.mouse_mode = _mouse_before
	Core.prog.play_result(id, hits)
	queue_free()
