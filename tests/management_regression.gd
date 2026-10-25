extends Node
const M = preload("res://scripts/kiosk_management.gd")
var failed := false
func check(ok: bool, label: String) -> void:
 failed = failed or not ok
 print("[management] ", "ok " if ok else "FAIL ", label)
func frames(count: int) -> void:
 for i in count: await get_tree().process_frame
func run(main) -> void:
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("user://qa_shots"))
 Core.new_game()
 Core.paused = true
 Core.in_game = false
 main.allow_faint = false
 main.village.enabled = false
 main.guests.enabled = false
 main.operations.set_process(false)
 Core.money = 100000
 Core.configure_company("Gestão Completa", "praia")
 Core.unlock_all()
 Core.minutes = 9 * 60
 Core.day = 1
 Core.company.sim.day = 1
 for id in Core.stock: Core.stock[id] = 100
 var d := M.state(Core)
 d.strict = true
 Core.set_kiosk_open(false)
 Core.set_kiosk_open(true)
 check(not Core.company.kiosk_open and not Core.kiosk_accepting_customers(), "checklist obrigatório bloqueia abertura")
 for key in ["limpeza", "estoque", "equipe"]: check(M.check_opening(Core, key), "conferência " + key)
 Core.set_kiosk_open(true)
 check(Core.kiosk_accepting_customers(), "checklist libera abertura real")
 Core.set_kiosk_open(false)
 var stock_before: int = Core.stock.coco
 var q := M.quote(Core, "horta", "coco", 12)
 var before: int = Core.money
 check(M.order_supply(Core, "horta", "coco", 12, int(q.cost)) and Core.money == before - int(q.cost) and Core.stock.coco == stock_before, "encomenda paga sem adiantar estoque")
 Core.save_game()
 check(Core.load_game(), "save completo recarrega gestão e encomenda")
 d = M.state(Core)
 check(d.orders.size() == 1 and d.strict and d.checks.size() == 3, "pedido e checklist sobrevivem ao JSON")
 Core.day = int(q.day)
 Core.minutes = int(q.minute) - 1
 M.tick(Core, 0)
 check(Core.stock.coco == stock_before, "não entrega antes do horário")
 Core.minutes += 1
 M.tick(Core, 0)
 var delivered: int = Core.stock.coco
 M.tick(Core, 1)
 check(delivered == stock_before + 12 and Core.stock.coco == delivered and d.orders.is_empty(), "entrega exatamente uma vez")
 q = M.quote(Core, "express", "coco", 2)
 before = Core.money
 check(M.order_supply(Core, "express", "coco", 2, int(q.cost)) and Core.money == before - int(q.cost) and Core.stock.coco == delivered + 2, "express cobra mais e entrega na hora")
 check(not M.order_supply(Core, "atacado", "coco", 2), "atacado respeita quantidade mínima")
 before = Core.money
 check(not M.order_supply(Core, "horta", "coco", 12, 1) and Core.money == before, "cotação alterada não cobra")
 Core.day = 1
 Core.minutes = 9 * 60
 d.day = 1
 Core.staff.atendente = false
 Core.prog.staff_info.erase("atendente")
 var p := M.candidate("atendente", 0)
 Core.money = int(p.cost)
 check(M.hire_candidate(Core, "atendente", 0) and Core.money == 0, "candidato iniciante contrata pelo preço menor anunciado")
 check(is_equal_approx(M.profile_factor(Core, "atendente", "wage"), 0.85), "salário usa o perfil contratado")
 check(Core.prog.staff_wage("atendente") == int(p.daily), "diária da oferta corresponde ao salário inicial")
 Core.money = 100000
 d.worked.atendente = 720.0
 var energy: int = Core.prog.staff_rec("atendente").energy
 Core.day = 2
 M.new_day(Core)
 check(float(d.profiles.atendente.morale) < 100 and Core.prog.staff_rec("atendente").energy < energy, "jornada longa reduz satisfação e energia")
 Core.day = 1
 Core.minutes = 9 * 60
 d.day = 1
 d.strict = false
 Core.company.ready = {}
 Core.company.production = {}
 var health: float = d.equipment.fridge.condition
 stock_before = Core.stock.coco
 check(Core.pickup_company_dish("coco_gelado") and Core.stock.coco < stock_before and float(d.equipment.fridge.condition) == health, "retirada direta usa estoque sem preparo ou desgaste de lote")
 check(Core.company.production.is_empty() and Core.company.carry == "coco_gelado", "produto vai direto para a mão")
 check(Core.return_company_dish(), "produto pode voltar à geladeira")
 d.equipment.fridge.condition = 5.0
 stock_before = Core.stock.coco
 check(Core.pickup_company_dish("coco_gelado") and Core.stock.coco == stock_before, "retirada de devolução não cobra estoque mesmo sem etapa de preparo")
 check(Core.return_company_dish(), "libera mãos antes da manutenção")
 before = Core.money
 check(M.equipment_action(Core, "fridge", "repair") and Core.money == before - 76, "manutenção cobra o orçamento")
 M.tick(Core, 29)
 check(not d.task.is_empty() and float(d.equipment.fridge.condition) == 5, "manutenção precisa terminar")
 Core.save_game()
 check(Core.load_game(), "recarrega manutenção em andamento")
 d = M.state(Core)
 M.tick(Core, 1)
 check(d.task.is_empty() and float(d.equipment.fridge.condition) == 100, "manutenção termina após recarga sem nova cobrança")
 d.equipment.fridge.hygiene = 10.0
 check(Core.pickup_company_dish("coco_gelado") and Core.return_company_dish(), "retirada não exige etapa de preparo")
 check(M.equipment_action(Core, "fridge", "clean"), "inicia limpeza")
 M.tick(Core, 12)
 check(float(d.equipment.fridge.hygiene) == 100, "limpeza restaura higiene")
 check(M.equipment_action(Core, "fridge", "upgrade") and M.prepare_speed(Core, "coco_gelado") > 1, "melhoria aumenta velocidade")
 d.equipment.fridge.hygiene = 20.0
 check(M.error_risk(Core, "coco_gelado") > 0, "higiene precária aumenta risco de perdas")
 d.equipment.fridge.hygiene = 100.0
 var look := {"paint": "coral", "board": "escura", "uniform": "areia", "layout": "amplo", "menu": false}
 var table: Dictionary = main.world._table_looks[0]
 var old_position: Vector3 = table.seats[0].spot.pos
 var old_block: Rect2 = main.world.block_rects[int(table.block)]
 before = Core.money
 var phone = main.hud.phone
 phone.open("personalizar")
 await frames(8)
 var selectors: Array = phone.screen.find_children("*", "OptionButton", true, false)
 for pair in [[0, 1], [1, 2], [2, 2], [3, 1]]:
  selectors[pair[0]].select(pair[1])
  selectors[pair[0]].item_selected.emit(pair[1])
 for control in phone.screen.find_children("*", "CheckButton", true, false):
  if control.text.begins_with("Exibir"): control.button_pressed = false
 check(Core.money == before and not d.look_owned and table.seats[0].spot.pos == old_position, "prévia altera seleção sem cobrar nem mover o cenário")
 for button in phone.screen.find_children("*", "Button", true, false):
  if button.text.begins_with("Aplicar personalização"): button.pressed.emit(); break
 check(d.look == look and Core.money == before - 180, "compra pela interface aplica a seleção exibida")
 phone.close()
 check(table.seats[0].spot.pos != old_position and main.world.block_rects[int(table.block)] != old_block and table.nodes[0].node.position != table.nodes[0].position, "layout move malha, assento e colisão")
 check(main.world._painted[0].material_override.albedo_color == M.PAINT.coral, "pintura muda no modelo real")
 check(not main.world._table_menus[0].visible, "cardápios expostos respondem à personalização")
 before = Core.money
 check(M.apply_look(Core, look) and Core.money == before, "reaplicar estilo não cobra de novo")
 Core.set_kiosk_open(true)
 check(not M.apply_look(Core, {"paint": "mar"}), "mudança de disposição exige quiosque fechado")
 Core.set_kiosk_open(false)
 main.operations._staff_tick()
 check(main.operations.actors.has("atendente") and main.operations.actors.atendente.get_meta("uniform", "") == "areia", "uniforme aplicado ao funcionário real")
 Core.minutes = 12 * 60
 Core.weather = "clear"
 Core.day_event = ""
 var midday := M.arrival_factor(Core)
 check(M.dish_weight(Core, "petiscos") > M.dish_weight(Core, "suco"), "almoço favorece refeições")
 Core.minutes = 8 * 60
 check(M.dish_weight(Core, "suco") > M.dish_weight(Core, "petiscos") and M.arrival_factor(Core) < midday, "manhã tem outro movimento e cardápio")
 Core.minutes = 12 * 60
 Core.weather = "rain"
 check(M.arrival_factor(Core) < midday, "chuva reduz chegada")
 check(not M.sheltered(Core, {"table": true, "covered": false}) and M.sheltered(Core, {"table": true, "covered": true}), "chuva exclui mesas descobertas")
 for spot in main.world.kiosk_spots: spot.busy = not bool(spot.get("table", false))
 var index: int = main.village._free_spot()
 check(index >= 0 and bool(main.world.kiosk_spots[index].get("covered", false)), "seleção real de lugar usa mesa abrigada")
 for spot in main.world.kiosk_spots: spot.busy = false
 Core.weather = "clear"
 Core.company.ready = {"coco_gelado": 2, "petiscos": 1}
 Core.company.production = {}
 Core.company.carry = ""
 Core.company.staff_carry = ""
 Core.company.receivables = []
 Core.company.dirty_seats = [0]
 check(not M.close_shift(Core, 0), "fechamento exige louça recolhida")
 Core.company.dirty_seats = []
 Core.company.receivables = [{"dish": "coco_gelado", "value": 5}]
 check(not M.close_shift(Core, 0), "fechamento exige contas recebidas")
 Core.company.receivables = []
 Core.freezer = true
 Core.company.sim.today.cash_in = 100
 check(M.store_drinks(Core), "guarda bebidas com freezer")
 before = Core.money
 check(M.close_shift(Core, 103) and int(d.closing.variance) == 3 and Core.money == before, "conferência registra diferença sem criar dinheiro")
 check(not M.close_shift(Core, 103), "não duplica fechamento no dia")
 Core.save_game()
 check(Core.load_game() and M.state(Core).look == look, "identidade e fechamento persistem no save real")
 d = M.state(Core)
 Core.company.sim.day = Core.day
 Core.day += 1
 Core.CompanyRules.Simulation.rollover(Core)
 check(Core.company.ready.coco_gelado == 2 and Core.company.ready.petiscos == 0, "bebidas guardadas duram uma noite; comida vence")
 check(M.store_drinks(Core), "pode organizar o próximo fechamento")
 Core.day += 1
 Core.CompanyRules.Simulation.rollover(Core)
 check(Core.company.ready.coco_gelado == 0, "bebidas não são conservadas indefinidamente")
 phone.open("fornecedores")
 await frames(5)
 var picker = phone.screen.find_children("*", "SpinBox", true, false)[0]
 picker.value = 17
 Core.stock_changed.emit()
 Core.money_changed.emit(Core.money)
 await frames(5)
 check(is_instance_valid(picker) and picker.value == 17, "quantidade e cotação não destroem formulário durante edição")
 phone.close()
 if main.args.has("management-shots"):
  Core.day = 1
  Core.minutes = 12 * 60
  main.day.force_update()
  main.player.set_view(Vector3(46, 0.7, -5), 45, -8)
  main.hud.visible = false
  main.operations._staff_tick()
  await frames(30)
  get_viewport().get_texture().get_image().save_png(ProjectSettings.globalize_path("user://qa_shots/management_world.png"))
  main.hud.visible = true
  for app in ["recrutamento", "fornecedores", "equipamentos", "movimento", "personalizar"]:
   phone.open(app)
   if phone._tween: phone._tween.kill()
   phone._place()
   await frames(8)
   if app == "personalizar":
    var scroll = phone.screen.find_children("*", "ScrollContainer", true, false)[0]
    scroll.scroll_vertical = 300
   await frames(30)
   get_viewport().get_texture().get_image().save_png(ProjectSettings.globalize_path("user://qa_shots/management_" + app + ".png"))
  phone.close()
 var normalized := M.sanitize(JSON.parse_string(JSON.stringify(d)))
 check(normalized.look == look and normalized.profiles.has("atendente") and normalized.closing.has("variance"), "novo estado tem roundtrip JSON")
 print("MANAGEMENT_TEST ", "FAIL" if failed else "PASS")
 Core.quit_game(1 if failed else 0)
