extends Node3D
## Monta a cena: mundo + vila, hóspedes, moradores, jogador, HUD, menus, ciclo dia/noite e áudio.
## Argumentos de teste (após --):  --shot=<nome>  --loop-test  --newgame  --mute  --quality=N  --hidehud  --empty  --out=

var world: Node3D
var guests: Node3D
var village: Node3D
var player: CharacterBody3D
var hud: CanvasLayer
var menus: CanvasLayer
var day: Node
var audio: Node
var menu_cam: Camera3D
var args := {}
var _sleeping := false
var allow_faint := true
var _t := 0.0

const SHOTS := {
	# nome: [posição, yaw, pitch, hora]
	"entrada": [Vector3(1.5, 0, 34), 4.0, -3.0, 9.5],
	"recepcao": [Vector3(-1.6, 0.12, 13.4), 200.0, -6.0, 10.0],
	"piscina": [Vector3(-8.4, 0.12, 10.4), -52.0, -14.0, 11.0],
	"bangalo": [Vector3(-6.5, 0, -16.5), 128.0, 4.0, 15.5],
	"interior": [Vector3(-12.3, 0.25, -6.2), 56.0, -16.0, 14.0],
	"bar": [Vector3(5.5, 0, -19.0), 236.0, 2.0, 16.6],
	"praia": [Vector3(-16, 0, -27.5), -78.0, 0.0, 17.3],
	"noite": [Vector3(6.0, 0, 26.0), 20.0, 0.0, 20.5],
	"vila": [Vector3(39.5, 0.15, 29.0), -84.0, -2.0, 15.5],
	"praca": [Vector3(68.6, 0.2, 35.0), 205.0, 5.0, 16.4],
	"casa": [Vector3(47.7, 0.27, 23.0), 52.0, -16.0, 7.0],
	"quiosque": [Vector3(33.6, 0, -5.4), -32.0, -4.0, 10.5],
	"noite_vila": [Vector3(56.0, 0.15, 29.4), -80.0, 0.0, 20.6],
	"aerea": [Vector3(26.0, 34.0, -52.0), 196.0, -30.0, 16.0],
	"menu": [Vector3(0, 0, 0), 0.0, 0.0, 17.3],
	"config": [Vector3(0, 0, 0), 0.0, 0.0, 17.3],
	"estoque": [Vector3(68.5, 0.2, 27.5), 12.0, -6.0, 11.0],
	"upgrade": [Vector3(-12.3, 0.25, -6.2), 56.0, -16.0, 17.2],
	"bangalo_up": [Vector3(-12.3, 0.25, -6.2), 56.0, -16.0, 17.3],
	"resumo": [Vector3(6.0, 0, 26.0), 20.0, 0.0, 20.5],
}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		var kv: PackedStringArray = a.trim_prefix("--").split("=", true, 1)
		args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	Core.in_game = false
	var testing := args.has("shot") or args.has("loop-test")
	if testing:
		Core.SAVE_PATH = "user://test_save.json"
		Quality.language = "en" if args.get("lang", "pt") == "en" else "pt"
		Quality.apply_language()
	if args.has("newgame") or testing:
		Core.delete_save()
		Core.new_game()
	if args.has("quality"):
		Quality.preset = clampi(int(args.quality), 0, 3)
	audio = Node.new()
	audio.set_script(load("res://scripts/audio.gd"))
	audio.process_mode = Node.PROCESS_MODE_ALWAYS
	audio.muted = args.has("mute") or testing or DisplayServer.get_name() == "headless"
	add_child(audio)
	world = Node3D.new()
	world.set_script(load("res://scripts/world_village.gd"))
	world.name = "World"
	add_child(world)
	day = Node.new()
	day.set_script(load("res://scripts/daycycle.gd"))
	add_child(day)
	day.world = world
	day.setup(self)
	Quality.setup(day.env, day.sun)
	guests = Node3D.new()
	guests.set_script(load("res://scripts/guests.gd"))
	guests.world = world
	add_child(guests)
	world.guests_mgr = guests
	village = Node3D.new()
	village.set_script(load("res://scripts/village_life.gd"))
	village.world = world
	village.name = "Village"
	add_child(village)
	player = CharacterBody3D.new()
	player.set_script(load("res://scripts/player.gd"))
	add_child(player)
	Core.player_ref = player
	_place_at_home()
	audio.player = player
	hud = CanvasLayer.new()
	hud.set_script(load("res://scripts/hud.gd"))
	hud.player = player
	hud.guests = guests
	hud.world = world
	hud.village = village
	hud.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(hud)
	menus = CanvasLayer.new()
	menus.set_script(load("res://scripts/menus.gd"))
	add_child(menus)
	hud.menus = menus
	menus.start_new.connect(_on_start_new)
	menus.start_load.connect(_on_start_load)
	menus.go_main_menu.connect(func(): get_tree().reload_current_scene())
	world.bed.prompt_fn = _bed_prompt
	world.bed.action_fn = _bed_use
	menu_cam = Camera3D.new()
	menu_cam.fov = 60.0
	menu_cam.far = 800.0
	add_child(menu_cam)
	day.force_update()
	if args.has("shot"):
		_run_shot(args.shot)
	elif args.has("loop-test"):
		Core.in_game = true
		menus.in_menu = false
		var t = load("res://tests/loop_test.gd").new()
		add_child(t)
		t.run(self)
	else:
		_enter_menu()

# ------------------------------------------------------------------ menu principal / início
func _enter_menu() -> void:
	Core.in_game = false
	Core.minutes = 17.3 * 60.0
	day.force_update()
	guests.enabled = false
	village.enabled = false
	hud.visible = false
	player.set_physics_process(false)
	menu_cam.current = true
	_update_menu_cam(0.0)
	menus.show_main()

func _update_menu_cam(t: float) -> void:
	var a := 0.35 + sin(t * 0.03) * 0.25
	var target := Vector3(34, 1.5, 6)
	menu_cam.global_position = target + Vector3(sin(a) * 52.0, 13.0 + sin(t * 0.05) * 1.5, -cos(a) * 52.0)
	menu_cam.look_at(target, Vector3.UP)

func _reset_world_people() -> void:
	guests.on_sleep(0)
	village._on_slept(0)

func _on_start_new(slot: int) -> void:
	Core.set_slot(slot)
	Core.delete_save()
	Core.new_game()
	_reset_world_people()
	_place_at_home()
	_begin_play(true)
	Core.save_game()

func _on_start_load(slot: int) -> void:
	Core.set_slot(slot)
	if not Core.load_game():
		Core.new_game()
	_reset_world_people()
	var lp: Dictionary = Core.loaded_player
	if lp.has("x"):
		player.global_position = Vector3(float(lp.x), float(lp.y) + 0.05, float(lp.z))
		player.yaw = float(lp.get("yaw", 0.0))
		player.pitch = 0.0
		player._apply_look()
	else:
		_place_at_home()
	_begin_play(false)

func _begin_play(fresh: bool) -> void:
	Core.in_game = true
	guests.enabled = true
	village.enabled = true
	hud.visible = true
	player.cam.current = true
	player.set_physics_process(true)
	day.force_update()
	Core.time_changed.emit(Core.day, Core.minutes)
	if not Quality.is_touch():
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	if fresh:
		Core.toast.emit(tr("Bom dia! Você mora na vila e trabalha no quiosque da praia. Siga a seta amarela."), "good")
		Core.toast.emit(tr("Ajude também na pousada: check-in na recepção e limpeza dos bangalôs."), "info")
	else:
		Core.toast.emit(tr("Bem-vindo de volta! Dia %d") % Core.day, "info")

func _place_at_home() -> void:
	player.set_view(world.home_wake, 0.0, -6.0)

# ------------------------------------------------------------------ dormir
func _bed_prompt() -> String:
	if Core.can_sleep():
		return tr("Dormir até amanhã (06:30)")
	return tr("Sua cama (dá para dormir depois das 20:00)")

func _bed_use() -> void:
	if not Core.can_sleep():
		Core.toast.emit(tr("Ainda é cedo para dormir. O quiosque e a pousada precisam de você!"), "info")
		return
	go_to_sleep(false)

func go_to_sleep(fainted: bool) -> void:
	if _sleeping:
		return
	_sleeping = true
	menus.fade(func():
		if fainted:
			Core.add_money(-20, tr("Você adormeceu de cansaço na rua"), "multa")
		Core.sleep()
		_place_at_home()
		day.force_update()
		_sleeping = false, 0.8)

func _process(delta: float) -> void:
	_t += delta
	if menu_cam and menu_cam.current:
		_update_menu_cam(_t)
	if Core.in_game and allow_faint and not get_tree().paused and not _sleeping:
		# depois das 02:00 o herói desmaia de sono e acorda em casa
		if Core.minutes >= 120.0 and Core.minutes < 300.0:
			go_to_sleep(true)

# ------------------------------------------------------------------ screenshots
func _run_shot(n: String) -> void:
	var s: Array = SHOTS.get(n, SHOTS.entrada)
	Core.paused = true
	Core.minutes = s[3] * 60.0
	guests.enabled = false
	village.enabled = false
	day.force_update()
	Core.time_changed.emit(Core.day, Core.minutes)
	player.set_physics_process(false)
	if n == "menu" or n == "config":
		hud.visible = false
		menu_cam.current = true
		_update_menu_cam(0.0)
		menus.show_main()
		if n == "config":
			menus._open_settings(menus.main_p)
	else:
		menus.in_menu = false
		Core.in_game = true
		player.set_view(s[0], s[1], s[2])
	if args.has("hidehud"):
		hud.visible = false
	# cenário de vida: hóspedes na fila, na piscina e no bar; quarto sujo; redes
	if not args.has("empty"):
		_stage_guests()
		if n == "quiosque":
			for k in 2:
				var c = village.spawn_customer()
				if c:
					c.position = c.spot.pos
					c._route.clear()
					c.state = "kwait"
					c.rotation.y = c.spot.rot
					c.play("Idle_Loop")
	await get_tree().create_timer(0.3).timeout
	for i in 25:
		await get_tree().process_frame
	day.force_update()
	Core.paused = true
	for i in 20:
		await get_tree().process_frame
	if hud.visible:
		hud._hint_t = 0.0
		await get_tree().process_frame
		await get_tree().process_frame
	if n == "estoque":
		hud.open_office("insumos")
	elif n == "upgrade":
		_dress_room(0)
		hud.open_office("bangalo", 0)
	elif n == "bangalo_up":
		_dress_room(0)
	elif n == "resumo":
		hud.show_summary(_demo_summary())
	if n in ["estoque", "upgrade", "bangalo_up", "resumo"]:
		for i in 10:
			await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://shots"))
	var out: String = args.get("out", "res://shots/%s.png" % n)
	img.save_png(out)
	print("SHOT_SAVED ", out)
	get_tree().quit()

func _stage_guests() -> void:
	Core.redes = 2
	Core.redes_changed.emit(2)
	Core.money = 1240
	Core.money_changed.emit(Core.money)
	Core.ratings = [4.5, 4.0, 4.6, 4.2]
	Core.stars_changed.emit(Core.stars())
	Core.vacate_room(1)
	for k in 2:
		var g = guests.spawn_guest()
		g.position = world.points["queue%d" % k]
		g._route.clear()
		g.state = "queue"
		g.rotation.y = PI
		g.play("Idle_Talking_Loop" if k == 0 else "Idle_Loop")
	var spots := [world.pool_spots[0], world.pool_spots[4], world.pool_spots[6], world.pool_spots[7], world.bar_spots[0], world.bar_spots[2], world.bar_spots[3]]
	for s in spots:
		var g = guests._make_guest()
		g.position = s.pos
		g.rotation.y = s.rot
		g.play(s.anim)
	var w = guests._make_guest()
	w.position = Vector3(-10.5, 0, 4.0)
	w.rotation.y = PI
	w.play("Walk_Loop")

func _dress_room(id: int) -> void:
	for cat in Economy.UPGRADES:
		Core.rooms[id].upgrades[cat] = Economy.max_tier(cat)
	world.apply_room_look(id)

func _demo_summary() -> Dictionary:
	return {
		"day": 1,
		"income": 248,
		"expense": 338,
		"cats": {"diaria": 158, "bar": 44, "quiosque": 26, "gorjeta": 20, "insumo": 18, "upgrade": 320},
		"lines": [
			{"a": 158, "r": "Check-in Lia (Bangalô 1)", "c": "diaria"},
			{"a": 22, "r": "Bar: Caipirinha", "c": "bar"},
			{"a": 26, "r": "Quiosque: Petiscos", "c": "quiosque"},
			{"a": 20, "r": "Gorjeta", "c": "gorjeta"},
			{"a": -18, "r": "Coco ×6", "c": "insumo"},
			{"a": -320, "r": "Ventilador de teto · Bangalô 1", "c": "upgrade"},
		],
	}
