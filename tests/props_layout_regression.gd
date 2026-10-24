extends Node
var failed := false
func check(ok: bool, label: String) -> void:
	failed = failed or not ok
	print("[props-layout] ", "ok " if ok else "FAIL ", label)
func frames(n: int) -> void:
	for i in n: await get_tree().process_frame
func board_bounds(board: Node) -> void:
	for label in board.find_children("*", "Label3D", true, false):
		var rect: AABB = label.get_aabb()
		rect.position += label.position
		check(rect.position.x >= -.49 and rect.end.x <= .49 and rect.position.y >= -.61 and rect.end.y <= .61,
			"texto dentro da placa: "+label.name+" "+str(rect))
func shot(main, target: Vector3, camera: Vector3, label: String) -> void:
	if DisplayServer.get_name() == "headless": return
	main.player.set_view(camera-Vector3.UP*1.65, 0, 0)
	main.player.cam.global_position = camera
	main.player.cam.look_at(target, Vector3.UP)
	main.day.force_update()
	await frames(15)
	await RenderingServer.frame_post_draw
	var folder := "user://qa_shots"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
	var path := folder+"/"+label+".png"
	check(get_viewport().get_texture().get_image().save_png(path) == OK, "captura "+label)
	print("PROP_SHOT ", ProjectSettings.globalize_path(path))
func run(main) -> void:
	Core.new_game()
	Core.paused = true
	Core.in_game = false
	Core.minutes = 11*60
	main.allow_faint = false
	main.player.set_physics_process(false)
	main.village.enabled = false
	main.guests.enabled = false
	main.hud.root.visible = false
	main.world._refresh_kiosk_board()
	await frames(3)
	var board = main.world._kiosk_board.get_child(0)
	board_bounds(board)
	check(board.global_position.y-.64 > 1.20, "área escrita acima do guarda-corpo")
	await shot(main, board.global_position, board.global_position+board.global_basis.z*1.8+Vector3.UP*.05, "board_starter_fixed")
	Core.unlock_all()
	main.world._refresh_kiosk_board()
	await frames(3)
	board = main.world._kiosk_board.get_child(0)
	board_bounds(board)
	check(board.get_node("BoardMenu").text.split("\n").size() >= 4, "cardápio expandido exercitado")
	await shot(main, board.global_position, board.global_position+board.global_basis.z*1.8+Vector3.UP*.05, "board_full_fixed")
	var baskets: Array = []
	for node in main.world.find_children("*", "Node3D", true, false):
		if node.scene_file_path == "res://assets/models/gen/wicker_basket_closed.glb": baskets.append(node)
	check(not baskets.is_empty(), "cestos do cenário usam modelo com tampa encaixada")
	check(Real.resolve("wicker_basket_02") == "g:wicker_basket_closed", "cestos de Real e B.model usam a mesma correção")
	if not baskets.is_empty():
		var basket = baskets[0]
		var bounds: AABB = Real._aabb(basket)
		check(bounds.size.y > .24 and bounds.size.y < .27 and bounds.size.x < .24, "cesto compacto sem tampa solta lateral")
		var target: Vector3 = basket.global_position+Vector3.UP*.12
		await shot(main, target, target+Vector3(.42,.38,.48), "basket_closed_fixed")
	print("PROPS_LAYOUT_TEST FAIL" if failed else "PROPS_LAYOUT_TEST PASS")
	Core.quit_game(1 if failed else 0)
