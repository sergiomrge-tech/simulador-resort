extends Node
var failed := false
func check(ok: bool, message: String) -> void:
	failed=failed or not ok
	print("[birds] ","ok " if ok else "FAIL ",message)
func run(main) -> void:
	Core.paused=true
	Core.in_game=true
	Core.minutes=12*60+10
	Core.weather="sun"
	Core.day_event=""
	main.set_process(false)
	main.player.set_physics_process(false)
	main.guests.enabled=false
	main.village.enabled=false
	var audio=main.audio
	audio.set_process(false)
	audio.muted=false
	audio.set_night(0)
	main.player.position=Vector3(38,.1,-13)
	for i in 2: await get_tree().physics_frame
	var sfx_bus := AudioServer.get_bus_index("SFX")
	var capture := AudioEffectCapture.new()
	capture.buffer_length=.5
	AudioServer.add_bus_effect(sfx_bus,capture)
	for name in ["bird1","bird2"]:
		var sound: AudioStream=load("res://assets/audio/"+name+".ogg")
		check(sound!=null and sound.get_length()>.4,"canto CC0 carregado: "+name)
	audio._bird_t=0
	audio._tick_birds(.1)
	check(audio.bird_voice.playing and audio.bird_voice.bus=="Ambiente","canto diurno posicional ativo no quiosque")
	check(audio.bird_voice.global_position.y>=5 and audio.bird_voice.max_polyphony==1,"vem das árvores e não sobrepõe cantos")
	check(audio._bird_t>=4 and audio._bird_t<=9,"intervalo entre cantos")
	await get_tree().create_timer(.25).timeout
	var samples := capture.get_buffer(capture.get_frames_available())
	var peak := 0.0
	for sample in samples: peak=maxf(peak,maxf(absf(sample.x),absf(sample.y)))
	check(samples.size()>0 and peak>.0001 and peak<.8,"mixagem real audível e sem saturação: "+str(peak))
	audio.bird_voice.stop()
	audio._bird_t=0
	audio._tick_birds(.1)
	get_tree().paused=true
	var timer_before: float=audio._bird_t
	audio._tick_birds(2)
	await get_tree().process_frame
	audio._tick_birds(0)
	check((audio.bird_voice.stream_paused or not audio.bird_voice.playing) and audio._bird_t==timer_before,"pausa suspende canto e intervalo")
	get_tree().paused=false
	audio.set_night(1)
	audio._tick_birds(.1)
	check(not audio.bird_voice.playing,"silêncio de pássaros à noite")
	audio.set_night(0)
	Core.weather="rain"
	audio._bird_t=0
	audio._tick_birds(.1)
	check(not audio.bird_voice.playing,"cantos silenciam durante chuva")
	Core.weather="sun"
	audio.muted=true
	audio._bird_t=0
	audio._tick_birds(.1)
	check(not audio.bird_voice.playing,"respeita mute")
	audio.muted=false
	AudioServer.set_bus_mute(sfx_bus,true)
	audio._bird_t=0
	audio._tick_birds(.1)
	check(not audio.bird_voice.playing,"respeita volume de efeitos zerado")
	AudioServer.set_bus_mute(sfx_bus,false)
	main.player.position=Vector3(70,.1,30)
	audio._bird_t=0
	audio._tick_birds(.1)
	check(audio.bird_voice.playing,"pássaros também na vila")
	main.player.position=Vector3(38,.1,-100)
	audio._tick_birds(.1)
	check(not audio.bird_voice.playing,"sem cantos de árvores em mar aberto")
	AudioServer.remove_bus_effect(sfx_bus,AudioServer.get_bus_effect_count(sfx_bus)-1)
	print("BIRDS_TEST FAIL" if failed else "BIRDS_TEST PASS")
	Core.quit_game(1 if failed else 0)
