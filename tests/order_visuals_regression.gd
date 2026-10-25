extends Node
const Presentation=preload("res://scripts/dish_presentation.gd")
var failed:=false
func check(ok: bool,message: String) -> void:
	failed=failed or not ok
	print("ORDER_VISUAL_TEST ","OK " if ok else "FAIL ",message)
func frames(count: int) -> void:
	for i in count: await get_tree().process_frame
func run(main) -> void:
	Core.new_game()
	Core.set_process(false)
	Core.configure_company("Pedidos reais","praia")
	Core.money=100000
	Core.buy_expansion("kiosk_tables")
	Core.minutes=11*60
	main.village.enabled=false
	main.village.set_process(false)
	main.guests.enabled=false
	main.allow_faint=false
	check(Presentation.RECIPES.size()==Economy.KIOSK_MENU.size(),"catálogo cobre todos os produtos")
	for id in Economy.KIOSK_MENU:
		var model: Node3D=Presentation.build(main.world,id)
		check(model!=null and not model.find_children("*","MeshInstance3D",true,false).is_empty(),"asset e identidade: "+id)
		Core.release_visual(model)
	var guests: Array=[]
	for index in [2,4]:
		var g=main.village._make()
		g.set_process(false)
		g.spot=main.world.kiosk_spots[index]
		g.spot.busy=true
		g.state="keat"
		g.set_meta("items",["suco","sorvete_morango","sorvete_chocolate"])
		g.set_meta("delivered",3)
		for i in 3: main.village._show_delivered_visual(g,str(g.get_meta("items")[i]),i)
		guests.append(g)
		var root: Node3D=g.get_meta("served_visuals")
		check(root.global_position.distance_to(g.spot.serve_pos)<.001,"produtos apoiados na mesa do proprietário")
		check(main.village.served_dishes(g).size()==3,"pedido misto mantém os três itens")
		check(root.get_child(0).position.distance_to(root.get_child(1).position)>.15,"produtos têm posições distintas")
	check(guests[0].get_meta("served_visuals")!=guests[1].get_meta("served_visuals"),"pedidos não compartilham apresentação")
	var root=guests[0].get_meta("served_visuals")
	main.village.clear_served_visuals(guests[0])
	await frames(3)
	check(not is_instance_valid(root) and main.village.served_dishes(guests[1]).size()==3,"limpar uma apresentação preserva o outro pedido")
	main.village.clear_served_visuals(guests[1])
	print("ORDER_VISUAL_TEST FAIL" if failed else "ORDER_VISUAL_TEST PASS")
	Core.quit_game(1 if failed else 0)
