extends Node
const Presentation = preload("res://scripts/dish_presentation.gd")
var failed := false
var main

func check(ok: bool, message: String) -> bool:
	print("ORDER_VISUAL_TEST ", "OK " if ok else "FAIL ", message)
	failed = failed or not ok
	return ok

func frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame

func place_customer(v, index: int, items: Array):
	var g = v.spawn_customer()
	if g == null:
		return null
	v._release_spot(g)
	g.spot = main.world.kiosk_spots[index]
	if bool(g.spot.busy):
		g.queue_free()
		v.customers.erase(g)
		return null
	g.spot.busy = true
	g.spot["owner"] = g.get_instance_id()
	g.position = g.spot.pos
	g._route.clear()
	g.set_meta("items", items)
	g.set_meta("delivered", 0)
	g.set_meta("revenue", 0)
	v._order(g)
	g.timer = 10000.0
	return g

func run(m) -> void:
	main = m
	main.allow_faint = false
	main.guests.enabled = false
	var v = main.village
	v.enabled = false
	Core.paused = true
	Core.minutes = 600.0
	Core.speed_mult = 1.0
	Core.unlock_all()
	main.world.refresh_areas()
	v._on_slept(0)
	for id in Economy.DISHES:
		Core.prog.discovered[id] = true
	for ingredient in Economy.SUPPLIES:
		Core.stock[ingredient] = 100
	Core.prog.week_goals.clear()
	Core.staff["atendente"] = false
	await frames(2)
	check(Presentation.RECIPES.size() == Economy.KIOSK_MENU.size(), "catálogo cobre todos os nove pratos")
	for id in Economy.KIOSK_MENU:
		check(Presentation.RECIPES.has(id), "ID aprovado: " + id)
		var model: Node3D = Presentation.build(main.world, id)
		check(model != null and not model.find_children("*", "MeshInstance3D", true, false).is_empty(), "asset importado: " + id)
		check(str(model.get_meta("dish_id")) == id, "identidade do prato: " + id)
		model.queue_free()
	check(not Presentation.is_drink("tapioca") and not Presentation.is_drink("acai") and not Presentation.is_drink("moqueca"), "pratos são comida, não bebida")
	check(Presentation.is_drink("batida") and Presentation.is_drink("coco_gelado"), "bebidas reconhecidas")
	var g = place_customer(v, 0, ["coco_gelado", "petiscos"])
	if not check(g != null, "cliente exclusivo no balcão"):
		get_tree().quit(1)
		return
	check(v.served_dishes(g).is_empty(), "pedido não servido não aparece pronto")
	check(v.kiosk_action() and is_instance_valid(v.prep_visual), "preparo aparece no balcão")
	check(str(v.prep_visual.get_meta("dish_id")) == "coco_gelado", "preparo corresponde ao primeiro item")
	v.prep_advance(30.0)
	check(v.served_dishes(g) == ["coco_gelado"] and g.state == "kwait", "entrega parcial preserva pedido restante")
	check(v.kiosk_action(), "segundo item entra em preparo")
	v.prep_advance(30.0)
	check(v.served_dishes(g) == ["coco_gelado", "petiscos"] and g.state == "keat", "balcão mostra só os itens entregues")
	check(not g._consume_drink and g.get_meta("consuming_dish") == "petiscos", "prop na mão corresponde à comida")
	var first_root = g.get_meta("served_visuals")
	v._leave(g)
	await frames(2)
	check(not is_instance_valid(first_root) and v.served_dishes(g).is_empty(), "saída remove louça e bebida do cliente")
	check(g.spot.busy, "limpeza visual não libera assento antes da saída")
	var table = place_customer(v, 2, ["suco", "tapioca", "acai"])
	if not check(table != null, "cliente exclusivo na mesa"):
		get_tree().quit(1)
		return
	check(v.kiosk_serve(), "pedido múltiplo atendido")
	check(v.served_dishes(table) == ["suco", "tapioca", "acai"], "mesa mostra três itens diferentes")
	check(not table._consume_drink, "açaí usa animação de comida")
	var root: Node3D = table.get_meta("served_visuals")
	check(root.global_position.distance_to(table.spot.serve_pos) < 0.001, "itens apoiados na mesa do proprietário")
	await get_tree().create_timer(0.4).timeout
	check(root.get_child(0).position.distance_to(root.get_child(1).position) > 0.15, "itens têm posições distintas")
	var other = place_customer(v, 4, ["suco", "suco"])
	if not check(other != null, "segunda mesa independente"):
		get_tree().quit(1)
		return
	check(v.kiosk_serve() and v.served_dishes(other) == ["suco", "suco"], "quantidades repetidas são preservadas")
	check(other.get_meta("served_visuals") != root, "pedidos não compartilham o nó de apresentação")
	v._leave(table)
	await frames(2)
	check(v.served_dishes(other).size() == 2, "limpar uma mesa preserva o pedido da outra")
	Core.minutes = Core.kiosk_close_min() + 1.0
	await frames(3)
	check(v.served_dishes(other).is_empty(), "fechamento limpa pratos pendentes")
	v._on_slept(0)
	await frames(2)
	check(not is_instance_valid(v.prep_visual), "novo dia limpa o preparo")
	print("ORDER_VISUAL_TEST ", "FAIL" if failed else "PASS")
	get_tree().quit(1 if failed else 0)
