extends Node
var failed:=false
func check(ok: bool,label: String) -> void:
	failed=failed or not ok
	print("[whale] ","ok " if ok else "FAIL ",label)
func capture(main,w,time: float,label: String) -> void:
	w.clock=time
	w.update_scene(time)
	for i in 12: await get_tree().physics_frame
	if DisplayServer.get_name()=="headless":return
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://shots/"+label+".png")
func run(main) -> void:
	Core.new_game()
	Core.minutes=11*60
	Core.paused=true
	Core.in_game=false
	main.village.enabled=false
	main.guests.enabled=false
	main.player.set_physics_process(false)
	main.hud.root.visible=false
	var w=main.get_node("WhaleWildlife")
	main.player.set_view(Vector3(0,.15,-30),0,0)
	main.player.cam.look_at(Vector3(-12,13,-139),Vector3.UP)
	main.day.force_update()
	await capture(main,w,2,"whale_breach")
	check(w.whales[0].body.visible and w.whales[0].body.position.y>5,"baleia emerge em salto")
	check(w.clouds.visible and main.day.env.sky.sky_material==w.cloud_mat,"nuvens no céu")
	await capture(main,w,4.6,"whale_splash")
	check(not w.whales[0].body.visible and w.whales[0].spray.visible and w.whales[0].foam.visible,"queda gera respingos e espuma")
	check(w.whales[0].spray.multimesh.instance_count==100,"spray com gotas balísticas")
	await capture(main,w,7,"whale_rings")
	check(not w.whales[0].spray.visible and w.whales[0].foam.visible,"ondas continuam após os respingos")
	w.clock=11
	w.update_scene(11)
	check(not w.whales[0].foam.visible and not w.whales[0].spray.visible,"efeitos se dissipam")
	w._process(1)
	check(w.clock==11,"pausa congela baleias e nuvens")
	w.update_scene(34)
	check(w.whales[0].body.visible,"salto se repete ao fundo")
	for item in w.whales:check(item.origin.z < -130 and item.origin.z > -180,"baleias separadas das rotas de barcos e cruzeiro")
	w.update_scene(3.9)
	Core.paused=false
	main.audio.muted=false
	w.update_scene(4.1)
	check(w.whales[0].sound.playing and w.whales[0].sound.bus=="SFX","impacto com som posicional suave")
	main.audio.muted=true
	w.update_scene(4.2)
	check(not w.whales[0].sound.playing,"impacto respeita mute")
	Core.paused=true
	print("WHALE_TEST FAIL" if failed else "WHALE_TEST PASS")
	get_tree().quit(1 if failed else 0)
