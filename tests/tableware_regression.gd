extends Node
var failed:=false
func check(ok: bool,message: String) -> void:
	failed=failed or not ok
	print("[tableware] ","ok " if ok else "FAIL ",message)
func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
func run(main) -> void:
	Core.new_game()
	Core.in_game=false
	Core.paused=true
	Core.set_process(false)
	main.allow_faint=false
	main.village.enabled=false
	main.village.set_process(false)
	main.guests.enabled=false
	main.player.set_physics_process(false)
	Core.money=10000
	Core.configure_company("Copo e Coco","praia")
	Core.buy_expansion("kiosk_tables")
	Core.minutes=11*60
	main.day.force_update()
	await frames(6)
	var ops=main.operations
	check(ops.computer==null and ops.computer_target==null,"balcão livre de PC e alvo invisível")
	main.hud.toggle_shop()
	check(main.hud.phone.visible,"gestão portátil abre")
	main.hud.phone.close()
	get_tree().paused=false
	var spot: Dictionary=main.world.kiosk_spots[2]
	var guest=main.village._make()
	guest.set_process(false)
	var before_stock: Dictionary=Core.stock.duplicate()
	var before_cash: int=Core.money
	var expected: Dictionary={"sorvete_morango":"g:used_icecream_cup","sorvete_chocolate":"g:used_icecream_cup","suco":"g:used_glass_juice","coco_gelado":"g:coconut_open","caipirinha":"g:used_cocktail","batida":"g:used_dish_batida","acai":"g:table_bowl","moqueca":"g:table_bowl","petiscos":"g:table_plate","tapioca":"g:table_plate","pastel":"g:table_plate"}
	for id in expected:
		guest.spot=spot
		guest.state="keat"
		guest.set_meta("items",[id])
		main.village._leave(guest)
		check(Core.company.dirty_items.get("2")==[id],"saída registra produto consumido: "+id)
		var used=ops.dirt[2].get_node("Used_"+id)
		check(used.get_meta("container")==expected[id],"recipiente correspondente: "+id)
		if id=="suco":
			for mesh in used.find_children("*","MeshInstance3D",true,false):
				for surface in mesh.mesh.get_surface_count():
					var material=mesh.mesh.surface_get_material(surface)
					check(material.resource_name.begins_with("vidro") or material.resource_name.begins_with("canudo"),"suco deixa vidro/canudo sem líquido, gelo ou fruta")
		Core.clean_company_seat(2)
		check(not Core.company.dirty_items.has("2") and not ops.dirt.has(2),"limpeza remove recipiente e registro: "+id)
	guest.spot=spot
	guest.state="keat"
	guest.set_meta("items",["suco","coco_gelado","petiscos"])
	main.village._leave(guest)
	check(ops.dirt[2].get_meta("consumed_items")==["suco","coco_gelado","petiscos"],"pedido misto deixa os três recipientes")
	var save_path: String=Core.SAVE_PATH
	Core.SAVE_PATH="user://tableware_tmp.json"
	Core.save_game()
	Core.company.dirty_items={}
	check(Core.load_game() and Core.company.dirty_items.get("2")==["suco","coco_gelado","petiscos"],"salvar/carregar preserva louça específica")
	check(ops.dirt[2].get_node_or_null("Used_suco")!=null and ops.dirt[2].get_node_or_null("Used_coco_gelado")!=null,"recipientes continuam visíveis após recarga")
	check(Core.stock==before_stock and Core.money==before_cash,"louça e recarga não alteram estoque nem cobram novamente")
	var legacy=Core.CompanyRules.sanitize({"dirty_seats":[2]})
	check(legacy.dirty_seats==[2] and legacy.dirty_items.is_empty(),"save antigo permanece compatível")
	main.hud.visible=false
	main.player.position=spot.serve_pos+Vector3(.45,-.65,1.0)
	main.player.cam.look_at(spot.serve_pos+Vector3(0,.06,0))
	await frames(8)
	if DisplayServer.get_name()!="headless":
		await RenderingServer.frame_post_draw
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://qa_shots"))
		get_viewport().get_texture().get_image().save_png("user://qa_shots/louca_correspondente.png")
	Core.clean_company_seat(2)
	Core.delete_save()
	Core.SAVE_PATH=save_path
	Core.release_visual(guest)
	print("TABLEWARE_TEST FAIL" if failed else "TABLEWARE_TEST PASS")
	Core.quit_game(1 if failed else 0)
