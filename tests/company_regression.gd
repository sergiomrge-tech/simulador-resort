extends Node
const Rules = preload("res://scripts/company_rules.gd")
var failed := false
func check(ok: bool, label: String) -> void:
	print("[company] ", "ok " if ok else "FAIL ", label)
	if not ok:
		failed = true

func run(main = null) -> void:
	var old_path: String = Core.SAVE_PATH
	Core.SAVE_PATH = "user://company_regression_tmp.json"
	Core.in_game = false
	Core.paused = true
	Core.new_game()
	check(not Core.company_enabled(), "novo jogo preserva atendimento original até criar empresa")
	check(not Core.configure_company("W".repeat(25), "praia"), "limite de 24 caracteres")
	check(not Core.configure_company("\n", "praia"), "nome vazio recusado")
	check(not Core.configure_company("Empresa", "invalida"), "fonte fora da lista recusada")
	check(Core.configure_company("  Quiosque São João  ", "elegante", "dourado"), "criação com acentos e normalização")
	check(Core.company.name == "Quiosque São João" and Core.company_enabled(), "marca e operação ativadas")
	Core.minutes = 10 * 60
	Core.set_kiosk_open(false)
	check(not Core.kiosk_accepting_customers(), "fechamento manual bloqueia novas chegadas")
	Core.set_kiosk_open(true)
	check(Core.kiosk_accepting_customers(), "abertura manual permite clientes no horário")
	Core.minutes = 7 * 60
	check(not Core.kiosk_accepting_customers(), "abertura respeita o início às 08:00")
	Core.minutes = 22 * 60
	check(not Core.kiosk_accepting_customers(), "abertura respeita o encerramento do dia")
	Core.minutes = 10 * 60
	check(not Rules.sanitize({}).kiosk_open, "save antigo começa fechado até abertura deliberada")
	check(not Rules.sanitize({"kiosk_open": false}).kiosk_open, "estado fechado preservado na migração")
	for font in Rules.FONTS:
		var sign := Label3D.new()
		sign.font_size = 120
		sign.outline_size = 12
		Rules.fit_sign(sign, "W".repeat(24), font, "creme", 2.95)
		var width: float = sign.font.get_string_size(sign.text, HORIZONTAL_ALIGNMENT_LEFT, -1, sign.font_size).x + 2 * sign.outline_size
		check(width * sign.pixel_size <= 2.951, "nome máximo cabe na placa: " + font)
		sign.free()
	for key in Core.stock:
		Core.stock[key] = 100
	var before: Dictionary = Core.stock.duplicate()
	check(not Core.prepare_company_dish("suco"), "preparo removido")
	check(Core.pickup_company_dish("suco") and Core.company.production.is_empty(), "retirada imediata sem preparo")
	for ing in Economy.dish("suco").uses:
		check(Core.stock[ing] == before[ing] - Economy.dish("suco").uses[ing], "estoque usado uma vez: " + ing)
	var after: Dictionary = Core.stock.duplicate()
	check(not Core.pickup_company_dish("suco"), "não duplica retirada")
	check(Core.sell_company_dish("coco_gelado") == -1 and Core.company.carry == "suco", "entrega errada preserva item")
	var cash: int = Core.money
	var price: int = Core.sell_company_dish("suco")
	check(price > 0 and Core.company.carry == "", "entrega consome apenas item carregado")
	check(Core.stock == after and Core.money == cash+price, "entrega paga automaticamente sem gastar ingredientes outra vez")
	check(Core.collect_company_payments() == 0 and Core.money == cash + price, "pagamento da entrega não cria conta pendente")
	check(Core.collect_company_payments() == 0 and Core.money == cash + price, "conta não pode ser recebida duas vezes")
	Core.company.ready.suco = 0
	before = Core.stock.duplicate()
	check(Core.pickup_company_dish("suco") and Core.return_company_dish(), "devolução preserva produto retirado")
	after = Core.stock.duplicate()
	check(Core.pickup_company_dish("suco") and Core.stock == after, "retirar devolução não cobra estoque outra vez")
	check(Core.sell_company_dish("suco") > 0, "entrega direta libera mãos")
	check(Core.reserve_company_staff_dish("suco") and Core.company.staff_carry == "suco", "garçom retira direto sem cozinheiro")
	after = Core.stock.duplicate()
	check(not Core.reserve_company_staff_dish("suco") and Core.stock == after, "reserva repetida não gasta estoque")
	check(Core.sell_company_dish("suco", true) > 0 and Core.company.staff_carry == "", "garçom entrega sem alterar mãos do jogador")
	for ingredient in Economy.dish("suco").uses: Core.stock[ingredient] = 0
	check(not Core.pickup_company_dish("suco") and Core.company_available("suco") == 0, "estoque zero bloqueia retirada sem valores negativos")
	for ingredient in Core.stock: Core.stock[ingredient] = 100
	var migrated: Dictionary = Rules.sanitize({"ready":{"suco":2},"production":{"dish":"suco","left":5.0}})
	check(migrated.production.is_empty() and migrated.ready.suco == 3, "save antigo converte preparo pago em produto pronto uma vez")
	check(Rules.sanitize(migrated).ready.suco == 3 and Rules.sanitize(migrated).production.is_empty(), "migração não duplica produto ao recarregar")
	Core.money = 20000
	check(Core.hire("atendente") and not Core.hire("caixa") and not Core.hire("garcom"), "uma única vaga faz todo o atendimento")
	cash = Core.money
	check(Core.pickup_company_dish("suco"), "retirada para caixa contratado")
	price = Core.sell_company_dish("suco")
	check(Core.money==cash+price and Core.company.receivables.is_empty(),"produto entregue já está pago")
	Core.collect_company_payments()
	check(Core.money>cash and Core.company.receivables.is_empty(),"receber no caixa liquida as contas uma vez")
	Core.company.dirty_seats = [0]
	check(not Core.set_company_service(false), "não desativa operação com louça pendente")
	check(Core.clean_company_seat(0) and not Core.clean_company_seat(0), "limpeza idempotente")
	Core.company.ready.suco = 2
	Core.company.carry = "suco"
	Core.company.staff_carry = "coco_gelado"
	Core.company.production = {"dish": "suco", "left": 1.25}
	Core.company.receivables = [{"dish": "suco", "value": 7}]
	Core.company.dirty_seats = [1]
	Core.set_kiosk_open(false)
	var snapshot: Dictionary = Core.company.duplicate(true)
	var saved_cash: int=Core.money
	snapshot.receivables=[]
	Core.save_game()
	Core.company = Rules.defaults()
	var loaded: bool=Core.load_game()
	var expected: Dictionary=Rules.sanitize(snapshot)
	var actual: Dictionary=Core.company.duplicate(true)
	expected.erase("sim")
	actual.erase("sim")
	check(loaded and actual==expected and Core.money==saved_cash+7, "save mantém produtos e louça, liquidando conta antiga uma vez")
	check(not Core.company.kiosk_open, "save e recarga preservam quiosque fechado")
	var file = FileAccess.open(Core.SAVE_PATH, FileAccess.READ)
	var legacy: Dictionary = JSON.parse_string(file.get_as_text())
	legacy.money=Core.money
	file.close()
	legacy.erase("company")
	legacy.v = 6
	file = FileAccess.open(Core.SAVE_PATH, FileAccess.WRITE)
	file.store_string(JSON.stringify(legacy))
	file.close()
	cash = Core.money
	check(Core.load_game() and not Core.company_enabled() and Core.money == cash, "migração v6 preserva dinheiro e atendimento original")
	if main != null:
		await _integration(main)
	Core.delete_save()
	Core.SAVE_PATH = old_path
	print("COMPANY_TEST FAIL" if failed else "COMPANY_TEST PASS")
	Core.quit_game(1 if failed else 0)

func _integration(main) -> void:
	var village = main.village
	village.enabled = false
	village._on_slept(0)
	Core.configure_company("Quiosque do Sergio", "praia")
	for role in Core.staff:
		Core.staff[role] = false
	Core.minutes = 10 * 60
	for key in Core.stock:
		Core.stock[key] = 100
	Core.company.ready.suco = 2
	var g = village.spawn_customer()
	check(g != null, "cliente criado")
	if g == null:
		return
	g.go([])
	g.position = g.spot.pos
	g.set_meta("items", ["coco_gelado", "suco"])
	g.set_meta("delivered", 0)
	g.set_meta("vip", false)
	village._order(g, true)
	Core.set_kiosk_open(false)
	var before_close: int = village.customers.size()
	village.enabled = true
	village.kiosk_spawn_in = 0.0
	village._kiosk_tick(0.01)
	village.enabled = false
	check(village.customers.size() == before_close and g.state == "kwait", "fechar impede chegada sem expulsar cliente com pedido")
	check(main.world._open_sign.text == "FECHADO", "placa de funcionamento muda ao fechar")
	Core.set_kiosk_open(true)
	check(main.world._open_sign.text == "ABERTO", "placa de funcionamento muda ao abrir")
	Core.pickup_company_dish("suco")
	check(main.operations.deliver(weakref(g)), "entrega física permite ordem diferente do pedido")
	check(village._remaining(g) == ["coco_gelado"], "pedido parcial mantém apenas item pendente")
	check(not main.operations.deliver(weakref(g)), "não repete item já entregue")
	Core.company.ready.coco_gelado = 1
	Core.pickup_company_dish("coco_gelado")
	check(main.operations.deliver(weakref(g)) and g.state == "kto_table", "pedido completo libera cliente para sentar")
	await to_table(village,g)
	var index: int = main.world.kiosk_spots.find(g.spot)
	village._leave(g)
	check(index in Core.company.dirty_seats, "saída deixa louça para recolher")
	village._release_spot(g)
	for i in main.world.kiosk_spots.size():
		if i != index:
			main.world.kiosk_spots[i].busy = true
	check(village._free_spot() == -1, "lugar sujo não é ocupado por novo cliente")
	Core.clean_company_seat(index)
	check(village._free_spot() == index, "limpeza libera assento")
	for sign in main.world.company_signs:
		check(sign.label.text == "Quiosque do Sergio", "marca aplicada à placa real")
	check(main.operations.stations.size() == 3, "geladeira, armário e cozinha presentes")
	var deck = main.world.find_child("KioskFloor",true,false)
	check(absf(deck.position.y + deck.mesh.get_aabb().end.y - main.operations.stations.pratos.position.y) < 0.005, "equipamentos apoiados no piso interno do quiosque")
	var floors: Array = deck.find_children("*", "StaticBody3D", true, false)
	check(floors.size() == 1 and floors[0].collision_layer == 1, "deck visível com colisão de piso")
	check(not main.operations.can_access("bebidas"), "retirada remota bloqueada")
	main.player.position = main.operations.stations.bebidas.global_position + Vector3(0, 0, -1.2)
	check(main.operations.can_access("bebidas"), "retirada disponível ao chegar à geladeira")

	# Edição real do formulário e operações ligadas à cena.
	main.hud.phone.close()
	main.world.find_child("KioskSign",true,false).use()
	check(not main.hud.phone.visible,"placa orienta para o celular sem abrir ao esbarrar")
	main.player.position = main.world.kiosk_point(Vector3(0,.1,.65))
	main.operations.open_computer()
	check(main.hud.phone.visible and main.hud.phone.app=="","celular abre a tela inicial da gestão")
	main.hud.phone._open_management("empresa")
	check(main.hud.phone.company_name.max_length == 24, "formulário limita o nome")
	await get_tree().process_frame
	await get_tree().process_frame
	check(main.hud.phone.company_name.get_global_rect().end.x <= main.hud.phone._phone.get_global_rect().end.x - 14.0, "formulário cabe na largura do celular")
	main.hud.phone.company_name.grab_focus()
	var key := InputEventKey.new()
	key.keycode = KEY_B
	key.physical_keycode = KEY_B
	key.pressed = true
	var in_game_before: bool = Core.in_game
	Core.in_game = true
	main.hud._input(key)
	Core.in_game = in_game_before
	check(main.hud.phone.visible, "letra B do nome não fecha o celular")
	main.hud.phone.company_name.text = "Marca em edição"
	main.hud.phone.company_font.select(2)
	main.hud.phone.company_name.release_focus()
	Core.stock_changed.emit()
	Core.money_changed.emit(Core.money)
	await get_tree().process_frame
	await get_tree().process_frame
	check(main.hud.phone.company_name.text == "Marca em edição" and main.hud.phone.company_font.selected == 2, "vendas e reposição não apagam rascunho ao escolher fonte")
	main.hud.phone._toggle_kiosk()
	check(not Core.company.kiosk_open and main.hud.phone.company_name.text == "Marca em edição", "botão fecha sem apagar rascunho da placa")
	main.hud.phone._toggle_kiosk()
	main.hud.phone._save_company()
	check(Core.company.name == "Marca em edição" and main.world.company_signs[0].label.text == "Marca em edição", "salvar o formulário atualiza a placa no mundo")
	main.hud.phone.close()
	# Cargos trabalham no mundo: cozinheiro prepara, garçom contorna o quiosque.
	village._on_slept(0)
	for spot in main.world.kiosk_spots:
		spot.busy = false
	Core.company.ready = {}
	Core.company.carry = ""
	Core.company.staff_carry = ""
	Core.company.production = {}
	Core.company.dirty_seats = []
	Core.company.receivables = []
	g = village.spawn_customer()
	g.go([])
	g.position = g.spot.pos
	g.set_meta("items", ["suco"])
	g.set_meta("delivered", 0)
	g.set_meta("vip", false)
	village._order(g)
	village.set_process(false)
	Core.staff.cozinheiro = false
	Core.staff.atendente = true
	Core.staff.garcom = false
	Core.staff.caixa = false
	Core.staff.limpeza = false
	Core.speed_mult = 16.0
	var counter_approach: Vector3 = main.operations.service_approach(g)
	# O teste aciona o mesmo passo de 0,25 s usado pelo processador da operação.
	main.operations.pulse = 0.25
	var elapsed := 0.0
	while g.state == "kwait" and elapsed < 15.0:
		Core.tick_company(0.05)
		main.operations._staff_tick()
		await get_tree().process_frame
		elapsed += get_process_delta_time()
	check(g.state == "kto_table", "garçom anota, retira e entrega no balcão pelo percurso real")
	var waiter = main.operations.actors.get("atendente")
	check(is_instance_valid(waiter) and waiter.position.distance_to(counter_approach) < 1.5, "garçom chegou ao cliente antes de entregar")
	elapsed=0
	while not Core.company.receivables.is_empty() and elapsed<8:
		main.operations._staff_tick()
		await get_tree().process_frame
		elapsed+=get_process_delta_time()
	check(Core.company.receivables.is_empty(),"o pedido termina pago, sem caminhada ao caixa")
	await to_table(village,g)
	village._leave(g)
	village._release_spot(g)
	elapsed = 0.0
	while not Core.company.dirty_seats.is_empty() and elapsed < 10.0:
		main.operations._staff_tick()
		await get_tree().process_frame
		elapsed += get_process_delta_time()
	check(Core.company.dirty_seats.is_empty(), "auxiliar caminha e limpa a louça")
	Core.prog.staff_rec("atendente").off = true
	main.operations._staff_tick()
	check(not waiter.visible, "folga suspende garçom")
	Core.speed_mult = 1.0

func to_table(village, guest) -> void:
	guest.set_process(false)
	for i in 2200:
		if guest.state=="keat": break
		guest._process(.05)
		village._kiosk_tick(0)
		if i%12==0: await get_tree().physics_frame
	check(guest.state=="keat","cliente caminha para consumir após retirada completa")
