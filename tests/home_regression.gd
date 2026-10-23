extends Node
var failed := false
func check(ok: bool, label: String) -> void:
	failed = failed or not ok
	print("[home] ", "ok " if ok else "FAIL ", label)
func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
func walk(main, destination: Vector3) -> void:
	for i in 240:
		var offset: Vector3 = destination-main.player.global_position
		offset.y = 0
		if offset.length()<.08: break
		main.player.velocity = offset.normalized()*2.5+Vector3(0,-.5,0)
		main.player.move_and_slide()
		await get_tree().physics_frame
	main.player.velocity = Vector3.ZERO
	check(Vector2(main.player.position.x,main.player.position.z).distance_to(Vector2(destination.x,destination.z))<.15,"corredor livre "+str(destination))
func use(main, node: Interactable) -> void:
	main.player.cam.look_at(node.global_position,Vector3.UP)
	await frames(4)
	main.player.ray.force_raycast_update()
	check(main.player.ray.get_collider()==node,"mira alcança "+node.get_prompt())
	main.player.focus = node if main.player.ray.get_collider()==node else null
	main.player.interact()
func run(main) -> void:
	Core.new_game()
	Core.paused = true
	Core.in_game = false
	main.allow_faint = false
	main.player.set_physics_process(false)
	main.village.enabled = false
	main.guests.enabled = false
	main.operations.set_process(false)
	var c: Vector3 = main.world.HOME_C+Vector3(0,.12,0)
	main.world.find_child("PlayerHomeDoor",true,false).set_open(true)
	await get_tree().create_timer(.55).timeout
	var lounge = main.world.get_node("HomeLounge")
	check(lounge.screen!=null,"tela derivada do CRT importado")
	check(lounge.has_node("HomeSofaCollision") and lounge.has_node("TVConsoleCollision"),"móveis detalhados têm colisão")
	var console_top: float = lounge.console.global_position.y+Real._aabb(lounge.console).end.y
	check(absf(lounge.tv.global_position.y-console_top)<.003 and absf(lounge.stereo.global_position.y-console_top)<.003,"TV e som apoiados no tampo real")
	main.player.position = c+Vector3(1.7,0,3.9)
	for offset in [Vector3(1.7,0,2.7),Vector3(1.7,0,.75),Vector3(-.45,0,.75),Vector3(0,0,-.6),Vector3(-.8,0,-.6)]:
		await walk(main,c+offset)
	await walk(main,c+Vector3(-.45,0,.75))
	await use(main,lounge.tv_control)
	check(lounge.tv_on and lounge.screen.visible,"E liga imagem silenciosa da TV")
	await use(main,lounge.tv_control)
	check(not lounge.tv_on and not lounge.screen.visible,"E desliga TV")
	await use(main,lounge.stereo_control)
	check(lounge.stereo_on and not lounge.speaker.playing,"som respeita mute")
	main.audio.muted = false
	lounge._update_audio()
	check(lounge.speaker.playing and lounge.speaker.bus=="Music" and main.audio.home_duck>0,"som posicional toca e reduz trilha sobreposta")
	await use(main,lounge.stereo_control)
	check(not lounge.speaker.playing and main.audio.home_duck==0,"desligar som restaura trilha")
	main.audio.muted = true
	main.player.position = c+Vector3(-2.5,0,1.65)
	for i in 45:
		main.player.velocity = Vector3(0,-.5,2.5)
		main.player.move_and_slide()
		await get_tree().physics_frame
	check(main.player.position.z<c.z+2.1,"jogador não atravessa sofá")
	main.player.velocity = Vector3.ZERO
	if DisplayServer.get_name()!="headless":
		main.hud.root.visible = false
		lounge.toggle_tv()
		main.player.cam.rotation = Vector3.ZERO
		main.player.set_view(c+Vector3(1.4,.06,2.8),56,-9)
		main.day.force_update()
		await frames(15)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("res://shots/home_lounge.png")
		main.player.set_view(c+Vector3(-1.4,.04,1.88),0,-9)
		await frames(12)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("res://shots/home_media.png")
		Core.minutes = 20*60
		main.day.force_update()
		main.player.set_view(c+Vector3(1.4,.06,2.8),56,-9)
		await frames(12)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("res://shots/home_lounge_night.png")
	print("HOME_TEST FAIL" if failed else "HOME_TEST PASS")
	get_tree().quit(1 if failed else 0)
