extends Node




signal changed

const PRESETS: = ["Baixo", "Médio", "Alto", "Ultra"]
const CFG: = "user://settings.cfg"
const RESOLUTIONS: = [Vector2i(1280, 720), Vector2i(1600, 900), Vector2i(1920, 1080), Vector2i(2560, 1440), Vector2i(3840, 2160)]
const WINDOW_MODES: = ["Janela", "Tela cheia (sem bordas)", "Tela cheia exclusiva"]
const REBINDABLE: = ["move_forward", "move_back", "move_left", "move_right", "interact", "shop", "sprint"]
const ACTION_NAMES: = {"move_forward": "Andar para frente", "move_back": "Andar para trás", "move_left": "Andar para a esquerda", 
	"move_right": "Andar para a direita", "interact": "Interagir", "shop": "Loja", "sprint": "Correr"}

var hd: = false
var preset: = 3
var scale: = 1.0
var vsync: = true
var window_mode: = 1
var resolution: = 2
var fov: = 75.0
var vol_master: = 1.0
var vol_music: = 0.8
var vol_sfx: = 1.0
var vol_ambience: float=.75
var shadows: int=-1
var vegetation: float=1.0
var detail_distance: float=1.0
var population: int=12
var show_fps: bool=false
var sensitivity: = 1.0
var invert_y: = false
var language: = "pt"
var ui_scale: = 1.0
var keybinds: = {}
# v0.7.3: upscaler (0 = desligado, 1 = FSR 1, 2 = FSR 2.2) e API gráfica no Windows
const UPSCALERS: = ["Desligado (nativo)", "AMD FSR 1.0", "AMD FSR 2.2 (tipo DLSS)"]
const APIS: = ["Vulkan", "DirectX 12"]
var upscaler: = 2
var api: = 0

var benchmark_original: bool=false
var env: Environment
var sun: DirectionalLight3D

func _ready() -> void :
	process_mode = Node.PROCESS_MODE_ALWAYS
	hd = RenderingServer.get_current_rendering_method() == "forward_plus"
	if not hd:
		preset = 1
	language = "pt" if OS.get_locale_language() == "pt" else "en"
	_ensure_inputs()
	_load()
	I18n.install()
	apply_language()
	apply_keybinds()
	apply_audio()
	_apply_window()
	ThemeDB.fallback_font = UiTheme.font()
	UiTheme.apply_scale(get_tree(), ui_scale)

var fullscreen: bool:
	get: return window_mode != 0

func is_touch() -> bool:
	return OS.has_feature("mobile")


func _load() -> void :
	var c: = ConfigFile.new()
	if c.load(CFG) != OK:
		return
	preset = clampi(int(c.get_value("video", "preset", preset)), 0, 3)
	scale = clampf(float(c.get_value("video", "scale", scale)), 0.5, 1.0)
	vsync = bool(c.get_value("video", "vsync", vsync))
	window_mode = clampi(int(c.get_value("video", "window_mode", window_mode)), 0, 2)
	resolution = clampi(int(c.get_value("video", "resolution", resolution)), 0, RESOLUTIONS.size() - 1)
	fov = clampf(float(c.get_value("video", "fov", fov)), 60.0, 100.0)
	vol_master = clampf(float(c.get_value("audio", "master", vol_master)), 0.0, 1.0)
	vol_music = clampf(float(c.get_value("audio", "music", vol_music)), 0.0, 1.0)
	vol_sfx = clampf(float(c.get_value("audio", "sfx", vol_sfx)), 0.0, 1.0)
	sensitivity = clampf(float(c.get_value("controls", "sensitivity", sensitivity)), 0.2, 3.0)
	invert_y = bool(c.get_value("controls", "invert_y", invert_y))
	language = str(c.get_value("general", "language", language))
	ui_scale = clampf(float(c.get_value("general", "ui_scale", ui_scale)), 0.75, 1.5)
	upscaler = clampi(int(c.get_value("video", "upscaler", upscaler)), 0, 2)
	api = 1 if current_api() == "d3d12" else 0
	shadows=clampi(int(c.get_value("video","shadows",-1)),-1,3)
	vegetation=clampf(float(c.get_value("video","vegetation",1.0)),.35,1.0)
	detail_distance=clampf(float(c.get_value("video","detail_distance",1.0)),.5,1.5)
	population=clampi(int(c.get_value("video","population",12)),4,18)
	show_fps=bool(c.get_value("video","show_fps",false))
	vol_ambience=clampf(float(c.get_value("audio","ambience",.75)),0,1)
	var kb = c.get_value("controls", "keys", {})
	if typeof(kb) == TYPE_DICTIONARY:
		keybinds = kb

func save() -> void :
	var c: = ConfigFile.new()
	c.set_value("video", "preset", preset)
	for key in ["shadows","vegetation","detail_distance","population","show_fps"]:c.set_value("video",key,get(key))
	c.set_value("audio","ambience",vol_ambience)
	c.set_value("video", "scale", scale)
	c.set_value("video", "vsync", vsync)
	c.set_value("video", "window_mode", window_mode)
	c.set_value("video", "resolution", resolution)
	c.set_value("video", "fov", fov)
	c.set_value("video", "upscaler", upscaler)
	c.set_value("audio", "master", vol_master)
	c.set_value("audio", "music", vol_music)
	c.set_value("audio", "sfx", vol_sfx)
	c.set_value("controls", "sensitivity", sensitivity)
	c.set_value("controls", "invert_y", invert_y)
	c.set_value("controls", "keys", keybinds)
	c.set_value("general", "language", language)
	c.set_value("general", "ui_scale", ui_scale)
	c.save(CFG)


func _add_key(action: String, key: Key) -> void :
	var e: = InputEventKey.new()
	e.physical_keycode = key
	InputMap.action_add_event(action, e)

func _add_joy_axis(action: String, axis: JoyAxis, v: float) -> void :
	var e: = InputEventJoypadMotion.new()
	e.axis = axis
	e.axis_value = v
	InputMap.action_add_event(action, e)

func _add_joy_btn(action: String, b: JoyButton) -> void :
	var e: = InputEventJoypadButton.new()
	e.button_index = b
	InputMap.action_add_event(action, e)

func _has_joy_motion(action: String) -> bool:
	for e in InputMap.action_get_events(action):
		if e is InputEventJoypadMotion:
			return true
	return false

func _has_joy_button(action: String) -> bool:
	for e in InputMap.action_get_events(action):
		if e is InputEventJoypadButton:
			return true
	return false

func _ensure_inputs() -> void :
	for a in ["move_forward", "move_back", "move_left", "move_right", "interact", "shop", "sprint", "pause", 
			"look_left", "look_right", "look_up", "look_down"]:
		if not InputMap.has_action(a):
			InputMap.add_action(a, 0.2)
	if InputMap.action_get_events("sprint").is_empty():
		_add_key("sprint", KEY_SHIFT)
	if InputMap.action_get_events("pause").is_empty():
		_add_key("pause", KEY_ESCAPE)

	if not _has_joy_motion("move_forward"):
		_add_joy_axis("move_forward", JOY_AXIS_LEFT_Y, -1.0)
		_add_joy_axis("move_back", JOY_AXIS_LEFT_Y, 1.0)
		_add_joy_axis("move_left", JOY_AXIS_LEFT_X, -1.0)
		_add_joy_axis("move_right", JOY_AXIS_LEFT_X, 1.0)
		_add_joy_axis("look_left", JOY_AXIS_RIGHT_X, -1.0)
		_add_joy_axis("look_right", JOY_AXIS_RIGHT_X, 1.0)
		_add_joy_axis("look_up", JOY_AXIS_RIGHT_Y, -1.0)
		_add_joy_axis("look_down", JOY_AXIS_RIGHT_Y, 1.0)
	if not _has_joy_button("interact"):
		_add_joy_btn("interact", JOY_BUTTON_A)
		_add_joy_btn("shop", JOY_BUTTON_Y)
		_add_joy_btn("pause", JOY_BUTTON_START)
		_add_joy_btn("sprint", JOY_BUTTON_LEFT_STICK)

func key_for(action: String) -> int:
	for e in InputMap.action_get_events(action):
		if e is InputEventKey:
			return e.physical_keycode if e.physical_keycode != 0 else e.keycode
	return 0

func key_name(action: String) -> String:
	var k: = key_for(action)
	if k == 0:
		return "—"
	if DisplayServer.get_name() == "headless":
		return OS.get_keycode_string(k)
	return OS.get_keycode_string(DisplayServer.keyboard_get_keycode_from_physical(k))

func rebind(action: String, physical: int) -> void :
	keybinds[action] = physical
	apply_keybinds()
	save()

func reset_keys() -> void :
	keybinds = {}
	var defaults: = {"move_forward": KEY_W, "move_back": KEY_S, "move_left": KEY_A, "move_right": KEY_D, "interact": KEY_E, "shop": KEY_B, "sprint": KEY_SHIFT}
	for a in defaults:
		_set_key(a, defaults[a])
	save()

func _set_key(action: String, physical: int) -> void :
	for e in InputMap.action_get_events(action):
		if e is InputEventKey:
			InputMap.action_erase_event(action, e)
	_add_key(action, physical)

func apply_keybinds() -> void :
	for a in keybinds:
		if InputMap.has_action(a):
			_set_key(a, int(keybinds[a]))


func set_language(l: String) -> void :
	language = l
	apply_language()
	save()
	changed.emit()

func apply_language() -> void :
	TranslationServer.set_locale("en" if language == "en" else "pt_BR")

func set_volume(bus: String, v: float) -> void :
	match bus:
		"Master": vol_master = v
		"Music": vol_music = v
		"SFX": vol_sfx = v
		"Ambiente": vol_ambience=v
	apply_audio()
	save()

func apply_audio() -> void :
	var a = load("res://scripts/audio.gd")
	a.ensure_buses()
	for pair in [["Master", vol_master], ["Music", vol_music], ["SFX", vol_sfx], ["Ambiente",vol_ambience]]:
		var i: = AudioServer.get_bus_index(pair[0])
		if i >= 0:
			AudioServer.set_bus_volume_db(i, linear_to_db(maxf(pair[1], 0.0001)))
			AudioServer.set_bus_mute(i, pair[1] <= 0.001)


func _apply_window() -> void :
	if DisplayServer.get_name() == "headless" or is_touch():
		return
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)
	if _has_shot_arg():
		return
	match window_mode:
		0:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
			var r: Vector2i = RESOLUTIONS[resolution]
			var scr: = DisplayServer.screen_get_size()
			r = Vector2i(mini(r.x, scr.x), mini(r.y, scr.y))
			DisplayServer.window_set_size(r)
			DisplayServer.window_set_position(DisplayServer.screen_get_position() + (scr - r) / 2)
		1:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
		2:
			DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN)

func _has_shot_arg() -> bool:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shot") or a.begins_with("--loop-test"):
			return true
	return false

func toggle_fullscreen() -> void :
	window_mode = 0 if window_mode != 0 else 1
	_apply_window()
	save()
	changed.emit()

func set_window_mode(m: int) -> void :
	window_mode = clampi(m, 0, 2)
	_apply_window()
	save()
	changed.emit()

func set_resolution(i: int) -> void :
	resolution = clampi(i, 0, RESOLUTIONS.size() - 1)
	_apply_window()
	save()

func set_preset(p: int) -> void :
	preset = clampi(p, 0, 3)
	shadows=-1
	apply()
	save()

func set_scale(s: float) -> void :
	scale = clampf(s, 0.5, 1.0)
	apply()
	save()

func set_upscaler(u: int) -> void :
	upscaler = clampi(u, 0, 2)
	apply()
	save()

func current_api() -> String:
	return RenderingServer.get_current_rendering_driver_name()

# A API gráfica só muda ao reiniciar: grava um override.cfg ao lado do .exe
# (o Godot lê esse arquivo na inicialização; se o DirectX 12 falhar, ele volta ao Vulkan sozinho).
func set_api(a: int) -> void :
	api = clampi(a, 0, 1)
	if OS.has_feature("editor") or OS.get_name() != "Windows":
		return
	var path: = OS.get_executable_path().get_base_dir().path_join("override.cfg")
	# v0.9.3: mescla em vez de sobrescrever (o override.cfg também guarda o carregador de patches)
	var cf: = ConfigFile.new()
	cf.load(path)
	cf.set_value("rendering", "rendering_device/driver.windows", "d3d12" if api == 1 else "vulkan")
	cf.set_value("rendering", "rendering_device/fallback_to_vulkan", true)
	cf.set_value("rendering", "rendering_device/fallback_to_d3d12", true)
	cf.save(path)

func set_ui_scale(s: float) -> void :
	ui_scale = clampf(s, 0.75, 1.5)
	UiTheme.apply_scale(get_tree(), ui_scale)
	save()

func set_vsync(v: bool) -> void :
	vsync = v
	_apply_window()
	save()

func set_fov(f: float) -> void :
	fov = clampf(f, 60.0, 100.0)
	save()
	changed.emit()

func set_sensitivity(s: float) -> void :
	sensitivity = clampf(s, 0.2, 3.0)
	save()

func set_invert_y(v: bool) -> void :
	invert_y = v
	save()


func setup(e: Environment, s: DirectionalLight3D) -> void :
	env = e
	sun = s
	apply()

func apply() -> void :
	if env == null:
		return
	var vp: = get_viewport()
	if not hd:
		changed.emit()
		return
	var p: = shadows if shadows>=0 else preset

	# v0.7: o contorno cartoon lê profundidade/normais da tela, o que não funciona com MSAA.
	# FXAA suaviza as linhas sem borrar as cores chapadas (TAA borraria).
	vp.msaa_3d = Viewport.MSAA_DISABLED
	vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA
	vp.use_taa = false
	var sc: = scale if upscaler > 0 else 1.0
	if upscaler == 2 and sc < 0.99:
		vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR2
	elif upscaler == 1 and sc < 0.99:
		vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR
		vp.fsr_sharpness = 0.3
	else:
		vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	vp.scaling_3d_scale = sc
	var original: bool=benchmark_original or OS.get_cmdline_user_args().has("--perf-original")
	vp.use_occlusion_culling=not original
	vp.mesh_lod_threshold = [2.0,1.0,1.0,.5][p] if original else [3.0,2.0,1.5,1.0][p]
	vp.positional_shadow_atlas_size = [2048, 2048, 4096, 4096][p]

	RenderingServer.directional_shadow_atlas_set_size(2048 if p == 0 else 4096, true)
	RenderingServer.directional_soft_shadow_filter_set_quality([RenderingServer.SHADOW_QUALITY_SOFT_LOW, RenderingServer.SHADOW_QUALITY_SOFT_LOW, RenderingServer.SHADOW_QUALITY_SOFT_MEDIUM, RenderingServer.SHADOW_QUALITY_SOFT_MEDIUM][p])
	RenderingServer.positional_soft_shadow_filter_set_quality([RenderingServer.SHADOW_QUALITY_HARD, RenderingServer.SHADOW_QUALITY_SOFT_LOW, RenderingServer.SHADOW_QUALITY_SOFT_MEDIUM, RenderingServer.SHADOW_QUALITY_SOFT_HIGH][p])
	if sun:
		sun.shadow_enabled=shadows!=0
		sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS if p <= (0 if original else 2) else DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
		sun.directional_shadow_max_distance = [50.0,80.0,110.0,150.0][p] if original else [35.0,50.0,75.0,110.0][p]
		sun.shadow_blur = 1.0
		sun.light_angular_distance = 0.5 if p >= 2 else 0.0

	# v0.7 cartoon: sombras nítidas, oclusão leve, sem GI/SSR/neblina volumétrica (achatariam as cores)
	env.ssao_enabled = p >= 1
	env.ssao_radius = 0.9
	env.ssao_intensity = 0.9
	env.ssao_power = 1.2
	env.ssil_enabled = false
	env.ssr_enabled = false
	env.sdfgi_enabled = false
	env.volumetric_fog_enabled = false
	env.glow_enabled = true
	env.glow_intensity = 0.55
	env.glow_bloom = 0.04
	if sun:
		sun.light_angular_distance = 0.0
		sun.shadow_blur = 0.6
	RenderingServer.environment_set_ssao_quality(RenderingServer.ENV_SSAO_QUALITY_MEDIUM if p < 3 else RenderingServer.ENV_SSAO_QUALITY_HIGH, true, 0.5, 2, 50, 300)
	RenderingServer.environment_set_ssil_quality(RenderingServer.ENV_SSIL_QUALITY_MEDIUM if p < 3 else RenderingServer.ENV_SSIL_QUALITY_HIGH, true, 0.5, 4, 50, 300)
	RenderingServer.environment_set_sdfgi_ray_count(RenderingServer.ENV_SDFGI_RAY_COUNT_64 if p < 3 else RenderingServer.ENV_SDFGI_RAY_COUNT_96)
	RenderingServer.environment_set_volumetric_fog_volume_size(64 if p == 2 else 128, 64 if p == 2 else 96)
	changed.emit()

func people_limit() -> int:
	return population if hd else mini(5,population)
func set_detail(key: String,value: Variant) -> void:
	if key not in ["shadows","vegetation","detail_distance","population","show_fps"]:return
	match key:
		"shadows":value=clampi(int(value),-1,3)
		"vegetation":value=clampf(float(value),.35,1)
		"detail_distance":value=clampf(float(value),.5,1.5)
		"population":value=clampi(int(value),4,18)
	set(key,value)
	apply()
	save()
