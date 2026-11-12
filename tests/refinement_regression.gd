extends Node
var failed := false
func check(ok: bool,label: String) -> void:
	failed=failed or not ok
	print("[refinement] ","ok " if ok else "FAIL ",label)
func frames(n: int) -> void:
	for i in n: await get_tree().physics_frame
func shot(label: String) -> void:
	await frames(8)
	if DisplayServer.get_name()=="headless": return
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://qa_shots"))
	check(get_viewport().get_texture().get_image().save_png("user://qa_shots/"+label+".png")==OK,"captura "+label)
func view(main,eye: Vector3,at: Vector3) -> void:
	main.player.position=eye-Vector3(0,1.65,0)
	main.player.cam.global_position=eye
	main.player.cam.look_at(at)
func run(main) -> void:
	Core.new_game()
	Core.set_process(false)
	Core.in_game=true
	Core.paused=true
	Core.minutes=11*60
	main.allow_faint=false
	main.village.enabled=false
	main.village.set_process(false)
	main.guests.enabled=false
	main.player.set_physics_process(false)
	main.day.force_update()
	await frames(12)
	Core.money=10000
	Core.configure_company("Brisa da Praia","praia")
	var phone=main.hud.phone
	phone.open("compras")
	await frames(8)
	check(phone.navbar.get_child_count()==6,"seis áreas de gestão sempre acessíveis")
	await shot("compras_compactas")
	for ingredient in Core.stock: Core.stock[ingredient]=0
	var id: String=Core.kiosk_menu()[0]
	var quote: Dictionary=Core.company_restock_quote(id,10)
	var cash: int=Core.money
	phone._buy_product_stock(id)
	check(Core.money==cash-int(quote.cost) and Core.company_available(id)>=10,"compra simples cobra somente cotação e abastece imediatamente")
	phone._buy_product_stock(id)
	check(Core.money==cash-int(quote.cost),"repetir reposição completa não cobra de novo")
	phone._open_management("equipe")
	await frames(12)
	for button in phone.screen.find_children("*","Button",true,false):
		check(button.size.x>=(30 if button.text=="‹" else 95) and button.size.y<=90,"botão de equipe legível e compacto: "+button.text)
	for card in phone.screen.find_children("*","PanelContainer",true,false):
		check(card.size.y<260,"cartão de equipe sem grandes vazios")
	await shot("equipe_compacta")
	phone.close()
	var display=main.operations.computer.find_child("CounterDisplay",true,false)
	# Display is a child of the physical model, outside its interaction Area.
	display=main.operations.find_child("CounterDisplay",true,false) if display==null else display
	check(display!=null,"tela física contém gestão real")
	view(main,main.world.kiosk_point(Vector3(0,1.90,.8)),main.world.kiosk_point(Vector3(0,1.47,1.65)))
	await shot("computador_detalhado")
	view(main,main.world.kiosk_point(Vector3(1.1,1.85,.7)),main.world.kiosk_point(Vector3(1.1,1.5,1.95)))
	await shot("cardapio_interno")
	view(main,main.world.kiosk_point(Vector3(1.1,1.85,3.1)),main.world.kiosk_point(Vector3(1.1,1.5,1.85)))
	await shot("cardapio_externo")
	main.hud.visible=false
	var animals:=get_tree().get_nodes_in_group("village_animals")
	check(animals.size()==5,"cinco animais preservados")
	for animal in animals:
		animal.set_process(false)
		check(animal.animation!=null and not animal.walk_clip.is_empty() and not animal.idle_clip.is_empty(),"rig com descanso e caminhada: "+animal.kind)
		var skeleton=animal.find_children("*","Skeleton3D",true,false)[0]
		animal.animation.play(animal.walk_clip)
		animal.animation.advance(.0)
		var poses: Array=[]
		for bone in skeleton.get_bone_count(): poses.append(skeleton.get_bone_pose(bone))
		animal.animation.advance(.23)
		var animated:=false
		for bone in skeleton.get_bone_count():
			if not poses[bone].is_equal_approx(skeleton.get_bone_pose(bone)): animated=true
		check(animated,"caminhada altera ossos e patas: "+animal.kind)
		check(animal.find_children("*Eye*","MeshInstance3D",true,false).size()>=2,"olhos modelados: "+animal.kind)
		Core.paused=false
		var before: Vector3=animal.position
		for i in 240: animal._process(.05)
		check(before.distance_to(animal.position)>.05,"passeio real: "+animal.kind)
		Core.paused=true
		var frozen: Vector3=animal.position
		animal._process(1)
		check(animal.position==frozen and not animal.animation.active,"pausa congela animal: "+animal.kind)
		if animal==animals[0] or animal==animals[3]:
			animal.rotation.y=0
			animal._play(false)
			animal.animation.active=true
			animal.animation.advance(.25)
			var p: Vector3=animal.global_position
			view(main,p+Vector3(.45,.45,1.15),p+Vector3(0,.28,.20))
			await shot("animal_"+animal.kind)
	var village=main.village
	check(village.walkers.size()==12,"quantidade HD de pedestres preservada")
	var back_walkers:=0
	for guest in village.walkers:
		guest.set_process(false)
		for point in guest.get_meta("path"):
			if point.z>60: back_walkers+=1;break
	check(back_walkers>=2,"rotas da rua de trás recebem moradores")
	Core.minutes=22*60
	village._process(0)
	for guest in village.walkers:
		if not guest.has_meta("home_target"): continue
		var goal: Vector3=guest.get_meta("home_target")
		check(goal.distance_to(village._outside_blocks(goal))<.001,"destino de casa mantém corpo fora da parede")
		for i in 1200:
			guest._process(.05)
			if not guest.is_moving(): break
		check(not guest.is_moving(),"morador chega à entrada sem ficar andando preso")
	Core.minutes=11*60
	village._process(0)
	view(main,Vector3(38,1.7,64),Vector3(74,1.45,64))
	await shot("rua_viva")
	var person=village.walkers[0]
	person.position=Vector3(44,.15,64)
	person.rotation.y=0
	person.play("Idle_Loop")
	view(main,person.position+Vector3(.65,1.65,1.25),person.position+Vector3(0,1.52,0))
	await shot("pessoa_cabelo")
	print("REFINEMENT_TEST FAIL" if failed else "REFINEMENT_TEST PASS")
	Core.quit_game(1 if failed else 0)
