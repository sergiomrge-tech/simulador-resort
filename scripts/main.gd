extends Node3D



var world: Node3D
var guests: Node3D
var village: Node3D
var player: CharacterBody3D
var hud: CanvasLayer
var menus: CanvasLayer
var day: Node
var audio: Node
var menu_cam: Camera3D
var args: = {}
var _sleeping: = false
var allow_faint: = true
var _t: = 0.0
var _touring: = false
var _tour_t: = 0.0
var _tour_posed: = false
var _tour_walker: Node3D
var _tour_kind: = ""

const SHOTS: = {

	"entrada": [Vector3(1.5, 0, 34), 4.0, -3.0, 9.5], 
	"recepcao": [Vector3(0.35, 0.12, 17.9), 182.0, -8.0, 10.4], 
	"piscina": [Vector3(-8.4, 0.12, 10.4), -52.0, -14.0, 11.0], 
	"bangalo": [Vector3(-6.5, 0, -16.5), 128.0, 4.0, 15.5], 
	"interior": [Vector3(-12.3, 0.25, -6.2), 56.0, -16.0, 14.0], 
	"bar": [Vector3(5.5, 0, -19.0), 236.0, 2.0, 16.6], 
	"praia": [Vector3(-24, 1.5, -16.5), -18.0, -6.0, 16.7], 
	"praia_meio": [Vector3(-24, 1.5, -16.5), -18.0, -6.0, 11.5], 
	"agua": [Vector3(-8.0, 1.45, -19.5), 132.0, -16.0, 17.15], 
	"balcao": [Vector3(35.6, 1.55, -8.8), 152.0, -12.0, 16.9], 
	"npc_anda": [Vector3(2.6, 1.2, 7.4), -138.0, -8.0, 10.4], 
	"npc_senta": [Vector3(-5.0, 1.2, 1.6), -97.0, -10.0, 16.8], 
	"npc_bar": [Vector3(13.0, 1.65, -19.4), 180.0, -9.0, 16.8], 
	"sombrinha": [Vector3(-24.0, 4.6, -17.0), 45.0, -29.9, 11.2], 
	"sombrinha_sape": [Vector3(-2.6, 4.4, -19.4), 42.9, -30.0, 16.6], 
	"pausa": [Vector3(-14, 0.6, -18), -30.0, -6.0, 17.2], 
	"noite": [Vector3(6.0, 0, 26.0), 20.0, 0.0, 20.5], 
	"vila": [Vector3(49.0, 1.58, 30.15), -77.9, 1.2, 10.5], 
	"praca": [Vector3(66.8, 1.62, 36.0), -139.1, 14.4, 16.2], 
	"casa": [Vector3(43.7, 1.5, 22.9), -54.3, -6.0, 10.2], 
	"casa_ext": [Vector3(46.4, 1.58, 29.4), 1.5, 7.6, 10.4], 
	"barcos": [Vector3(70.5, 1.25, -23.2), -47.4, -9.1, 16.4], 
	"vila_anda": [Vector3(49.0, 1.58, 30.15), -77.9, 1.2, 10.6], 
	"palmeira": [Vector3(22.5, 2.8, -1.5), -52.4, 17.6, 11.0], 
	"quiosque": [Vector3(37.2, 1.35, -7.8), -17.7, -4.4, 16.8], 
	"celular": [Vector3(37.2, 1.35, -7.8), -17.7, -4.4, 10.5], 
	"celular_home": [Vector3(37.2, 1.35, -7.8), -17.7, -4.4, 10.5], 
	"cel_cardapio": [Vector3(37.2, 1.35, -7.8), -17.7, -4.4, 10.5], 
	"cel_mercado": [Vector3(37.2, 1.35, -7.8), -17.7, -4.4, 10.5], 
	"cel_album": [Vector3(37.2, 1.35, -7.8), -17.7, -4.4, 10.5], 
	"cel_missoes": [Vector3(37.2, 1.35, -7.8), -17.7, -4.4, 10.5], 
	"lote": [Vector3(4.0, 1.6, 30.0), 10.0, -6.0, 15.0], 
	"resort": [Vector3(26.0, 34.0, -52.0), 196.0, -30.0, 16.0], 
	"neon": [Vector3(37.4, 1.6, -4.6), -10.0, 6.0, 19.6], 
	"rosto": [Vector3(38.0, 0.0, -11.9), 180.0, -14.0, 10.5], 
	"vila_nova": [Vector3(52.0, 30.0, 98.0), 0.0, -38.0, 15.5], 
	"rua_tras": [Vector3(20.0, 0.15, 64.0), -90.0, -2.0, 16.0], 
	"feira": [Vector3(34.0, 0.15, 55.5), 0.0, -8.0, 10.0], 
	"pier": [Vector3(72.0, 0.3, -23.5), 0.0, -3.0, 17.3], 
	"farol_noite": [Vector3(88.0, 0.2, -27.0), -56.0, 6.0, 20.6], 
	"mesas": [Vector3(37.0, 1.2, -1.0), 10.0, -18.0, 10.5], 
	"quiosque_ext": [Vector3(44.0, 0.2, -4.0), 33.7, -8.0, 11.0], 
	"bar_ext": [Vector3(20.0, 0.2, -6.0), 45.0, -8.0, 11.0], 
	"recepcao_ext": [Vector3(6.0, 0.2, 27.0), 28.6, -6.0, 11.0], 
	"bangalo_ext": [Vector3(-6.0, 0.2, -1.0), 48.8, -6.0, 11.0], 
	"casa_vila": [Vector3(57.0, 0.2, 29.0), 20.6, -2.0, 11.0], 
	"padaria": [Vector3(74.0, 0.2, 29.5), 20.0, -2.0, 11.0], 
	"igreja": [Vector3(70.0, 0.2, 36.5), -159.0, 8.0, 11.0], 
	"barraca": [Vector3(66.0, 0.2, -12.0), 26.6, -8.0, 11.0], 
	"farol": [Vector3(95.0, 0.2, -27.0), -60.0, 10.0, 11.0], 
	"galera": [Vector3(30.0, -0.35, -15.0), 0.0, -2.0, 10.5], 
	"noite_vila": [Vector3(49.0, 1.58, 30.15), -77.9, 1.2, 21.2], 
	"serra_dia": [Vector3(58.0, 2.2, 28.5), -175.0, 12.2, 10.8], 
	"serra_praia": [Vector3(8.0, 2.0, -24.0), -165.4, 9.3, 11.2], 
	"serra_ouro": [Vector3(-18.0, 6.5, -36.0), -159.1, 8.2, 17.15], 
	"serra_alvorada": [Vector3(20.0, 4.5, -18.0), -172.8, 11.5, 6.35], 
	"aerea": [Vector3(26.0, 34.0, -52.0), 196.0, -30.0, 16.0], 
	"menu": [Vector3(0, 0, 0), 0.0, 0.0, 17.3], 
	"config": [Vector3(0, 0, 0), 0.0, 0.0, 17.3], 
	"estoque": [Vector3(68.5, 0.2, 27.5), 12.0, -6.0, 11.0], 
	"upgrade": [Vector3(-12.3, 0.25, -6.2), 56.0, -16.0, 17.2], 
	"bangalo_up": [Vector3(-12.3, 0.25, -6.2), 56.0, -16.0, 17.3], 
	"resumo": [Vector3(6.0, 0, 26.0), 20.0, 0.0, 20.5], 
}

func _ready() -> void :
	for a in OS.get_cmdline_user_args():
		var kv: PackedStringArray = a.trim_prefix("--").split("=", true, 1)
		args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	Core.in_game = false
	Core.proc_props = args.has("proc")
	var testing: = args.has("shot") or args.has("loop-test") or args.has("tour")
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
	Toon.attach_outline(player.cam)
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
	menus.go_main_menu.connect( func(): get_tree().reload_current_scene())
	world.bed.prompt_fn = _bed_prompt
	world.bed.action_fn = _bed_use
	menu_cam = Camera3D.new()
	menu_cam.fov = 60.0
	menu_cam.far = 1200.0
	add_child(menu_cam)
	Toon.attach_outline(menu_cam)
	day.force_update()
	if args.has("shot"):
		_run_shot(args.shot)
	elif args.has("loop-test"):
		Core.in_game = true
		menus.in_menu = false
		var t = load("res://tests/loop_test.gd").new()
		add_child(t)
		t.run(self)
	elif args.has("tour"):
		_run_tour()
	else:
		_enter_menu()


func _enter_menu() -> void :
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

func _update_menu_cam(t: float) -> void :
	var a: = 0.35 + sin(t * 0.03) * 0.25
	var target: = Vector3(34, 1.5, 6)
	menu_cam.global_position = target + Vector3(sin(a) * 52.0, 13.0 + sin(t * 0.05) * 1.5, - cos(a) * 52.0)
	menu_cam.look_at(target, Vector3.UP)

func _reset_world_people() -> void :
	guests.on_sleep(0)
	village._on_slept(0)

func _on_start_new(slot: int) -> void :
	Core.set_slot(slot)
	Core.delete_save()
	Core.new_game()
	_reset_world_people()
	_place_at_home()
	_begin_play(true)
	Core.save_game()

func _on_start_load(slot: int) -> void :
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

func _begin_play(fresh: bool) -> void :
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
		Core.toast.emit(tr("Bom dia! Hoje você abre o seu quiosque na praia. Siga a seta amarela."), "good")
		Core.toast.emit(tr("Junte dinheiro e compre expansões pelo celular (%s): mesas, drinks, bar, pousada...") % Quality.key_name("shop"), "info")
	else:
		Core.toast.emit(tr("Bem-vindo de volta! Dia %d") % Core.day, "info")

func _place_at_home() -> void :
	player.set_view(world.home_wake, 0.0, -6.0)


func _bed_prompt() -> String:
	if Core.can_sleep():
		return tr("Dormir até amanhã (06:30)")
	return tr("Sua cama (dá para dormir depois das 20:00)")

func _bed_use() -> void :
	if not Core.can_sleep():
		Core.toast.emit(tr("Ainda é cedo para dormir. O quiosque e a pousada precisam de você!"), "info")
		return
	go_to_sleep(false)

func go_to_sleep(fainted: bool) -> void :
	if _sleeping:
		return
	_sleeping = true
	menus.fade( func():
		if fainted:
			Core.add_money(-20, tr("Você adormeceu de cansaço na rua"), "multa")
		Core.sleep()
		_place_at_home()
		day.force_update()
		_sleeping = false, 0.8)

func _process(delta: float) -> void :
	_t += delta
	if _touring:
		_tour_t += delta
		if not _tour_posed and _tour_t > 0.2:
			_tour_posed = true
			_eat_at_bar()
			for c in village.customers:
				c.play("Eat")
			for g in guests.get_children():
				if g == _tour_walker or not g.has_method("play"):
					continue
				if g.global_position.y > 0.2 and g.global_position.distance_to(world.BAR_C) >= 5.5 and g._state != "Sit":
					g.play("Sitting_Idle_Loop")
		_apply_tour_cam()
		return
	if menu_cam and menu_cam.current:
		_update_menu_cam(_t)
	if Core.in_game and allow_faint and not get_tree().paused and not _sleeping:

		if Core.minutes >= 120.0 and Core.minutes < 300.0:
			go_to_sleep(true)


func _run_shot(n: String) -> void :
	var s: Array = SHOTS.get(n, SHOTS.entrada)
	# câmera livre para depuração: --cam=x,y,z,yaw,pitch[,hora]
	if args.has("cam"):
		var cv: = str(args.cam).split(",")
		s = [Vector3(float(cv[0]), float(cv[1]), float(cv[2])), float(cv[3]), float(cv[4]), float(cv[5]) if cv.size() > 5 else 11.0]
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
	if args.has("gallery"):
		# depuração: --gallery=chave1,chave2,... enfileira modelos (chaves do Real: nome, k:nome, q:nome, g:nome) diante da câmera
		var keys: PackedStringArray = str(args.gallery).split(",")
		var yaw_r: float = deg_to_rad(float(s[1]))
		var fwd: = Vector3(-sin(yaw_r), 0, -cos(yaw_r))
		var right: = Vector3(cos(yaw_r), 0, -sin(yaw_r))
		var base_p: Vector3 = s[0] + fwd * 3.2 - Vector3(0, 1.6, 0)
		var gfloor: = MeshInstance3D.new()
		var gbox: = BoxMesh.new()
		gbox.size = Vector3(40, 0.1, 40)
		gfloor.mesh = gbox
		var gmat: = StandardMaterial3D.new()
		gmat.albedo_color = Color(0.82, 0.84, 0.88)
		gfloor.material_override = gmat
		gfloor.position = base_p + fwd * 6.0 + Vector3(0, -0.06, 0)
		world.add_child(gfloor)
		var gcols: int = int(str(args.get("gcols", "0")))
		if gcols <= 0:
			gcols = keys.size()
		for gi in keys.size():
			var gcol: int = gi % gcols
			var grow: int = gi / gcols
			Real.place(world, keys[gi], base_p + right * (float(gcol) - gcols * 0.5 + 0.5) * 1.6 + fwd * float(grow) * 1.8, 1.2, 0.0)
	if args.has("noroof"):
		# depuração: esconde telhado e bandeirinhas do quiosque para ver o balcão de cima
		await get_tree().process_frame
		for gi in world.find_children("*", "GeometryInstance3D", true, false):
			var gp: Vector3 = gi.global_position
			var gb: AABB = gi.get_aabb() if gi is MeshInstance3D else AABB()
			var top: float = gp.y + gb.position.y + gb.size.y
			var bot: float = gp.y + gb.position.y
			if absf(gp.x - 38.0) < 5.5 and absf(gp.z + 11.0) < 5.5 and (bot > 1.9 or gi is MultiMeshInstance3D or (top > 2.2 and gb.size.x > 3.0)):
				gi.visible = false

	if n in ["quiosque_ext", "bar_ext", "recepcao_ext", "bangalo_ext", "resort", "neon", "bar", "piscina", "recepcao", "bangalo", "interior", "upgrade", "bangalo_up", "npc_bar", "npc_anda", "npc_senta", "entrada", "noite", "praia"] or args.has("full"):
		Core.unlock_all()
		if Core.rooms.size() < 2:
			Core.reset_rooms(2)
			world.sync_bungalows()
		world.refresh_areas()
		if args.has("dirty"):
			# depuração: --dirty deixa os quartos sujos (cama bagunçada, toalhas e lixo)
			for rr in Core.rooms:
				Core.vacate_room(rr.id)
	if not args.has("empty"):
		_stage_guests()
		if n in ["vila", "noite_vila", "vila_anda", "praca", "casa", "casa_ext", "barcos", "palmeira", "serra_dia", "serra_praia", "serra_ouro", "serra_alvorada"]:
			_stage_village(n)
		if n == "quiosque" or n == "balcao" or n == "rosto" or n == "mesas":
			if n == "mesas":
				Core.unlocked["kiosk_tables"] = true
				world.refresh_areas()
			for k in (5 if n == "mesas" else 2):
				var c = village.spawn_customer()
				if c:
					c.position = c.spot.pos
					c._route.clear()
					c.state = "kwait"
					c.rotation.y = c.spot.rot
					c.timer = 90.0
					if n == "mesas" and k % 2 == 1:
						c.state = "keat"
						c.set_meta("eat", 30.0)
						c.consume(k == 1)
					else:
						c.show_order(village._order_text(c))
						c.play("Sitting_Idle_Loop")
		if n == "galera":
			for k in 8:
				var gg = guests._make_guest()
				gg.position = Vector3(26.6 + k * 0.95, 0.0, -19.0)
				gg.rotation.y = 0.0
				gg.play("Idle_Loop" if k % 3 else "Idle_Talking_Loop")
		if n == "npc_bar":
			_eat_at_bar()
		if n == "npc_anda":
			var walker = guests._make_guest()
			walker.position = Vector3(-6.0, 0.0, 5.0)
			walker.go([Vector3(80.0, 0.0, 2.0)])
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
	if n == "recepcao":
		hud.show_desk_card(tr("Fazer check-in de %s") % "Ana")
	elif n == "npc_bar":
		_eat_at_bar()
	elif n == "quiosque" or n == "balcao" or n == "rosto" or n == "mesas":
		pass
	elif n == "pausa":
		menus.toggle_pause()
	if n == "celular":
		hud.open_office("expansoes")
	elif n == "celular_home":
		hud.open_office("")
	elif n.begins_with("cel_"):
		hud.open_office(n.substr(4))
	if n == "estoque":
		hud.open_office("insumos")
	elif n == "upgrade":
		_dress_room(0)
		hud.open_office("bangalo", 0)
	elif n == "bangalo_up":
		_dress_room(0)
	elif n == "resumo":
		hud.show_summary(_demo_summary())
	if n in ["estoque", "upgrade", "bangalo_up", "resumo", "pausa", "recepcao", "npc_bar", "npc_anda", "npc_senta", "quiosque", "balcao", "rosto", "celular", "celular_home", "mesas", "cel_cardapio", "cel_mercado", "cel_album", "cel_missoes"]:
		var extra: = 36 if n in ["npc_bar", "quiosque", "balcao", "celular", "celular_home"] else 12
		for i in extra:
			await get_tree().process_frame
	if n == "npc_anda":
		for c in guests.get_children():
			if c.has_method("is_moving") and c.is_moving():
				c._route.clear()
				c.position = Vector3(0.15, 0.0, 4.7)
				c.rotation.y = deg_to_rad(-25.0)
				break
		for i in 2:
			await get_tree().process_frame
	var img: = get_viewport().get_texture().get_image()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://shots"))
	var out: String = args.get("out", "res://shots/%s.png" % n)
	img.save_png(out)
	print("SHOT_SAVED ", out)
	get_tree().quit()

func _eat_at_bar() -> void :
	for g in guests.get_children():
		if g is Node3D and g.global_position.y > 0.2 and g.global_position.distance_to(world.BAR_C) < 5.5:
			g.play("Eat")

func _aim_cam(pos: Vector3, target: Vector3) -> void :
	var d: = target - pos
	player.global_position = pos
	player.yaw = atan2( - d.x, - d.z)
	player.pitch = atan2(d.y, Vector2(d.x, d.z).length())
	player._apply_look()

func _run_tour() -> void :
	if str(args.get("tour", "")) == "vila":
		_run_village_tour()
		return
	Core.paused = true
	Core.in_game = true
	Core.minutes = 16.6 * 60.0
	menus.in_menu = false
	hud.visible = false
	guests.enabled = false
	village.enabled = false
	day.force_update()
	player.set_physics_process(false)
	player.cam.current = true
	_stage_guests()
	_eat_at_bar()
	_tour_walker = guests._make_guest()
	_tour_walker.position = Vector3(-4.0, 0.0, 8.0)
	_tour_walker.go([Vector3(20.0, 0.0, 6.5)])
	for off in [Vector3(-0.85, 0.32, 0.7), Vector3(0.85, 0.32, 0.7)]:
		var sitter = guests._make_guest()
		sitter.position = Vector3(-6.0, 0.0, -23.0) + off
		sitter.rotation.y = PI
		sitter.play("Sitting_Idle_Loop")
	var kc = village.spawn_customer()
	if kc:
		kc.position = kc.spot.pos
		kc._route.clear()
		kc.state = "kwait"
		kc.rotation.y = kc.spot.rot
		kc.play("Eat")
	_touring = true
	_tour_t = 0.0
	_apply_tour_cam()

func _apply_tour_cam() -> void :
	if _tour_kind == "vila":
		_apply_village_tour_cam()
		return
	var t: = _tour_t
	var pos: = Vector3.ZERO
	var look: = Vector3.ZERO
	if t < 4.0:
		var u: = t / 4.0
		pos = Vector3(-8.0, 1.75, 12.2).lerp(Vector3(3.2, 1.65, 11.0), u)
		look = (_tour_walker.global_position + Vector3(0, 1.05, 0)) if _tour_walker else Vector3(0, 1.0, 7.0)
	elif t < 8.0:
		var u: = (t - 4.0) / 4.0
		pos = Vector3(15.2, 1.7, -19.8).lerp(Vector3(10.6, 1.55, -19.3), u)
		look = Vector3(13.0, 1.05, -15.7)
	elif t < 12.0:
		var u: = (t - 8.0) / 4.0
		pos = Vector3(-10.4, 1.55, -19.0).lerp(Vector3(-2.2, 1.42, -19.4), u)
		look = Vector3(-6.0, 0.75, -22.3)
	else:
		var u: = clampf((t - 12.0) / 4.0, 0.0, 1.0)
		pos = Vector3(-16.0, 1.7, -21.5).lerp(Vector3(-3.0, 1.9, -20.0), u)
		look = Vector3(-8.0, 0.1, -33.2)
	_aim_cam(pos, look)

func _run_village_tour() -> void :
	Core.paused = true
	Core.in_game = true
	Core.minutes = 10.5 * 60.0
	menus.in_menu = false
	hud.visible = false
	guests.enabled = false
	village.enabled = false
	day.force_update()
	player.set_physics_process(false)
	player.cam.current = true
	_stage_village("vila_anda")
	_touring = true
	_tour_kind = "vila"
	_tour_t = 0.0
	_apply_tour_cam()

func _apply_village_tour_cam() -> void :
	var t: = _tour_t
	var pos: = Vector3.ZERO
	var look: = Vector3.ZERO
	if t < 3.5:
		var u: = t / 3.5
		pos = Vector3(49.6, 1.68, 27.9).lerp(Vector3(52.4, 1.62, 28.5), u)
		look = Vector3(46.2, 2.15, 22.4)
	elif t < 8.0:
		var u: = (t - 3.5) / 4.5
		pos = Vector3(54.0, 1.62, 28.7).lerp(Vector3(78.0, 1.62, 28.55), u)
		look = pos + Vector3(6.0, 0.4, -5.4)
	elif t < 12.5:
		var u: = (t - 8.0) / 4.5
		pos = Vector3(67.2, 1.68, 36.0).lerp(Vector3(71.5, 1.75, 38.2), u)
		look = Vector3(76.2, 5.8, 49.2)
	else:
		var u: = clampf((t - 12.5) / 5.5, 0.0, 1.0)
		pos = Vector3(39.2, 1.62, 24.0).lerp(Vector3(37.6, 1.55, -6.2), u)
		look = Vector3(38.2, 1.35, pos.z - 6.5)
	_aim_cam(pos, look)

func _stage_village(n: String) -> void :
	village.set_process(false)
	var walkers: Array = village.walkers
	if n.begins_with("serra_"):
		var ahead: = [Vector3(63.5, 0.15, 33.1), Vector3(69.2, 0.15, 32.6)]
		for i in walkers.size():
			var sg: Node3D = walkers[i]
			if n == "serra_dia" and i < ahead.size():
				sg.visible = true
				sg.position = ahead[i]
				sg._route.clear()
				sg.rotation.y = PI * 0.5
				sg.play("Idle_Loop")
			else:
				sg.visible = false
				sg._route.clear()
		return
	if n == "casa" or n == "casa_ext" or n == "palmeira" or n == "barcos":
		for g in walkers:
			g.position = Vector3(8.0, 0.15, 27.1)
			g._route.clear()
			g.visible = n == "barcos"
		if n == "barcos" and walkers.size() > 0:
			var fisher: Node3D = walkers[0]
			fisher.position = Vector3(66.5, 0.05, -24.2)
			fisher.rotation.y = 0.4
			fisher.visible = true
			fisher.play("Idle_Loop")
		return
	if n == "praca":
		var pts: = [Vector3(69.2, 0.2, 37.2), Vector3(73.5, 0.2, 36.6), Vector3(79.0, 0.2, 37.8), Vector3(71.0, 0.2, 40.6)]
		for i in walkers.size():
			var g: Node3D = walkers[i]
			if i < pts.size():
				g.visible = true
				g.position = pts[i]
				g.go([pts[(i + 1) % pts.size()]])
			else:
				g.position = Vector3(8.0, 0.15, 27.1)
				g._route.clear()
				g.visible = false
		return
	for i in walkers.size():
		var g2: Node3D = walkers[i]
		g2.visible = true
		if i >= 6:
			g2.position = Vector3(10.0, 0.15, 27.1)
			g2._route.clear()
			g2.visible = false
			continue
		if i < 2:
			g2.position = Vector3(61.2 + float(i) * 0.8, 0.15, 27.35)
			g2.rotation.y = PI if i == 0 else 0.0
			g2._route.clear()
			g2.play("Idle_Talking_Loop")
			continue
		var dir: = 1.0 if i % 2 == 0 else -1.0
		var lane: = 27.2 if i % 2 == 0 else 32.8
		g2.position = Vector3(54.0 + float(i) * 3.6, 0.15, lane)
		g2.go([g2.position + Vector3(14.0 * dir, 0.0, 0.0)])

func _stage_guests() -> void :
	Core.redes = 2
	Core.redes_changed.emit(2)
	Core.money = 1240
	Core.money_changed.emit(Core.money)
	Core.ratings = [4.5, 4.0, 4.6, 4.2]
	Core.stars_changed.emit(Core.stars())
	if not Core.has("pousada"):
		Core.money = 214
		Core.money_changed.emit(Core.money)
		return
	Core.vacate_room(1)
	for k in 2:
		var g = guests.spawn_guest()
		g.position = world.points["queue%d" % k]
		g._route.clear()
		g.state = "queue"
		g.rotation.y = PI
		g.play("Idle_Talking_Loop" if k == 0 else "Idle_Loop")
	var spots: = [world.pool_spots[0], world.pool_spots[4], world.pool_spots[6], world.pool_spots[7], world.bar_spots[0], world.bar_spots[2], world.bar_spots[3]]
	for s in spots:
		var g = guests._make_guest()
		g.position = s.pos
		g.rotation.y = s.rot
		g.play(s.anim)
	var w = guests._make_guest()
	w.position = Vector3(-10.5, 0, 4.0)
	w.rotation.y = PI
	w.play("Walk_Loop")

func _dress_room(id: int) -> void :
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
