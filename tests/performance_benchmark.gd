extends Node
## Mesma câmera, resolução, preset e duração para comparar versões sem tocar em saves.
var rows: Array=[]
func run(main) -> void:
	Core.new_game()
	Core.set_process(false)
	Core.in_game=true
	Core.paused=false
	Core.minutes=11*60
	main.allow_faint=false
	main.player.set_physics_process(false)
	main.guests.enabled=false
	main.village.kiosk_spawn_in=100000
	main.hud.phone.close()
	main.menus.in_menu=false
	Quality.vsync=false
	Quality.upscaler=0
	Quality.scale=1
	Quality.apply()
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps=0
	main.day.force_update()
	Core.time_changed.emit(Core.day,Core.minutes)
	if main.args.has("perf-original"):
		var old_display=main.operations.find_child("CounterDisplay",true,false)
		if old_display: old_display.viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	var viewport:=get_viewport()
	RenderingServer.viewport_set_measure_render_time(viewport.get_viewport_rid(),true)
	var scenarios: Array=[
		["quiosque",main.world.kiosk_point(Vector3(.1,.1,.2)),main.world.kiosk_point(Vector3(0,1.45,1.8))],
		["vila",Vector3(49,.15,30.15),Vector3(76,1.5,30)],
		["praia",Vector3(45,.15,-22),Vector3(18,2,-110)]
	]
	if main.args.has("perf-paired"):
		await run_paired(main,scenarios)
		return
	for scenario in scenarios:
		main.player.position=scenario[1]
		main.player.cam.look_at(scenario[2])
		await get_tree().create_timer(3.0).timeout
		var times: Array=[]
		var gpu: Array=[]
		var cpu: Array=[]
		var process: Array=[]
		var calls: Array=[]
		var primitives: Array=[]
		var start:=Time.get_ticks_usec()
		var start_frame:=Engine.get_frames_drawn()
		var end:=start+8000000
		var last:=Time.get_ticks_usec()
		while Time.get_ticks_usec()<end:
			await RenderingServer.frame_post_draw
			var now:=Time.get_ticks_usec()
			times.append((now-last)/1000.0)
			last=now
			gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(viewport.get_viewport_rid()))
			cpu.append(RenderingServer.viewport_get_measured_render_time_cpu(viewport.get_viewport_rid()))
			process.append(Performance.get_monitor(Performance.TIME_PROCESS)*1000)
			calls.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
			primitives.append(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
		var row: Dictionary={"scene":scenario[0],"frames":times.size(),"drawn_fps":(Engine.get_frames_drawn()-start_frame)*1000000.0/(Time.get_ticks_usec()-start),"frame_ms":stats(times),"gpu_ms":stats(gpu),"render_cpu_ms":stats(cpu),"process_ms":stats(process),"draw_calls":stats(calls),"primitives":stats(primitives),"vram_mb":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED)/1048576.0}
		rows.append(row)
		print("BENCH_SCENE ",JSON.stringify(row))
		if main.args.has("perf-shots"):
			DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://qa_shots"))
			get_viewport().get_texture().get_image().save_png("user://qa_shots/perf_"+scenario[0]+".png")
	var report: Dictionary={"gpu":RenderingServer.get_video_adapter_name(),"preset":Quality.preset,"resolution":viewport.size,"native":true,"scenes":rows}
	var file:=FileAccess.open("user://benchmark.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  "))
	print("PERFORMANCE_TEST PASS")
	Core.quit_game()

func stats(values: Array) -> Dictionary:
	values.sort()
	var total:=0.0
	for value in values: total+=float(value)
	return {"mean":total/maxi(1,values.size()),"p50":values[values.size()/2],"p95":values[mini(values.size()-1,int(values.size()*.95))]}

var material_pairs: Array=[]
func run_paired(main, scenarios: Array) -> void:
	for mesh in main.find_children("*","MeshInstance3D",true,false):
		if not mesh.has_meta("performance_material"): continue
		var shared: Array=[]
		var separate: Array=[]
		for surface in mesh.mesh.get_surface_count():
			var material: Material=mesh.get_active_material(surface)
			shared.append(material)
			separate.append(material.duplicate() if material else null)
		material_pairs.append([mesh,shared,separate])
	var viewport:=get_viewport()
	for scenario in scenarios:
		main.player.position=scenario[1]
		main.player.cam.look_at(scenario[2])
		for original in ([false,true] if main.args.has("perf-reverse") else [true,false]):
			Quality.benchmark_original=original
			Quality.apply()
			preload("res://scripts/guest.gd").use_block_cache=not original
			for pair in material_pairs:
				if not is_instance_valid(pair[0]): continue
				for surface in pair[1].size(): pair[0].set_surface_override_material(surface,pair[2 if original else 1][surface])
			var display=main.operations.find_child("CounterDisplay",true,false)
			if display: display.viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS if original else SubViewport.UPDATE_ONCE
			await get_tree().create_timer(2.0).timeout
			var times: Array=[]
			var gpu: Array=[]
			var calls: Array=[]
			var primitives: Array=[]
			var start:=Time.get_ticks_usec()
			var start_frame:=Engine.get_frames_drawn()
			var last:=start
			while Time.get_ticks_usec()-start<6000000:
				await RenderingServer.frame_post_draw
				var now:=Time.get_ticks_usec()
				times.append((now-last)/1000.0)
				last=now
				gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(viewport.get_viewport_rid()))
				calls.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
				primitives.append(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
			var arm: String="original" if original else "optimized"
			var row: Dictionary={"scene":scenario[0],"arm":arm,"fps":(Engine.get_frames_drawn()-start_frame)*1000000.0/(Time.get_ticks_usec()-start),"frame_ms":stats(times),"gpu_ms":stats(gpu),"draw_calls":stats(calls),"primitives":stats(primitives)}
			rows.append(row)
			print("BENCH_PAIRED ",JSON.stringify(row))
			if main.args.has("perf-shots"):
				DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://qa_shots"))
				viewport.get_texture().get_image().save_png("user://qa_shots/paired_"+scenario[0]+"_"+arm+".png")
	var file:=FileAccess.open("user://benchmark.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"gpu":RenderingServer.get_video_adapter_name(),"preset":Quality.preset,"resolution":get_viewport().size,"native":true,"paired":true,"scenes":rows},"  "))
	print("PERFORMANCE_TEST PASS")
	Core.quit_game()
