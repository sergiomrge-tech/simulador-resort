extends Node
const Sim = preload("res://scripts/kiosk_simulation.gd")
var failed := false
func check(ok: bool, label: String) -> void:
	failed = failed or not ok
	print("[simulation] ", "ok " if ok else "FAIL ", label)

func run(main) -> void:
	Core.new_game()
	Core.paused = true
	Core.in_game = false
	main.village.enabled = false
	Core.money = 10000
	Core.configure_company("Simulação da Praia", "praia")
	Core.minutes = 10 * 60
	check(Core.set_kiosk_schedule(9, 22, [0, 1, 2, 3, 4]), "horários e dias válidos")
	check(not Core.set_kiosk_schedule(22, 9, [0]), "recusa horário invertido sem alterar escala")
	check(Core.kiosk_open_min() == 540 and Core.kiosk_close_min() == 1320 and Core.kiosk_accepting_customers(), "horários afetam abertura real")
	Core.day = 7
	check(not Core.kiosk_accepting_customers(), "domingo fechado pela escala semanal")
	Core.day = 1
	Core.company.sim.target = 6
	for id in Sim.ingredients(Core):
		Core.stock[id] = 0
		Core.supply_mult[id] = 1.0
	Core.supply_mult.coco = 1.4
	Core.contracts.coco = 5
	var quote: int = Sim.reorder_quote(Core)
	var cash: int = Core.money
	check(Core.restock_kiosk() and Core.money == cash - quote, "reposição usa cotação e contrato reais")
	check(Core.stock.coco == 6 and Core.stock.frutas == 6 and Core.stock.gelo == 6, "reposição atende meta do cardápio")
	cash = Core.money
	check(Core.restock_kiosk() and Core.money == cash, "repor acima da meta não compra novamente")
	Core.stock.coco = 0
	Core.money = 0
	check(not Core.restock_kiosk() and Core.stock.coco == 0 and Core.money == 0, "orçamento insuficiente não compra parcialmente")
	Core.money = 10000
	check(Core.hire("cozinheiro"), "contratação disponível")
	Core.prog.staff_rec("cozinheiro").trait = "rapido"
	Core.set_kiosk_shift("cozinheiro", 8, 16)
	var base: int = Core.prog.staff_wage("cozinheiro")
	Core.set_kiosk_shift("cozinheiro", 8, 20)
	check(Core.prog.staff_wage("cozinheiro") == int(round(base * 1.5)), "turno de 12h custa mais que turno de 8h")
	Core.minutes = 10 * 60
	check(Core.prog.staff_eff("cozinheiro") > 0, "funcionário trabalha dentro do turno")
	Core.minutes = 21 * 60
	check(Core.prog.staff_eff("cozinheiro") == 0, "funcionário para fora do turno")
	Core.minutes = 10 * 60
	Core.prog.toggle_off("cozinheiro")
	check(Core.prog.staff_eff("cozinheiro") == 0, "folga impede trabalho")
	Core.prog.toggle_off("cozinheiro")
	Core.company.sim.today = Sim.stats()
	Core.company.sim.today.open_minutes = 120.0
	Core.company.sim.today.cash_in = 150
	Core.company.sim.today.supplies = 25
	Core.company.sim.day = 1
	Core.company.ready = {"suco": 3}
	Core.company.carry = "coco_gelado"
	Core.company.production = {"dish": "suco", "left": 1.0}
	Core.day = 2
	var wage: int = Core.prog.staff_wage("cozinheiro")
	Core._pay_wages(true)
	cash = Core.money
	Core._pay_wages(true)
	check(Core.money == cash and Core.company.sim.today.payroll == wage, "folha cobrada uma única vez por dia")
	var energy_before: int = Core.prog.staff_rec("cozinheiro").energy
	Sim.rollover(Core)
	check(int(Core.prog.staff_rec("cozinheiro").energy) < energy_before, "turno longo aumenta cansaço na virada")
	var energy_after: int = Core.prog.staff_rec("cozinheiro").energy
	var report: Dictionary = Core.company.sim.history.back()
	check(Core.money == cash - 16 and report.overhead == 16, "estrutura cobra 12 mais 2 por hora aberta")
	check(report.net == 150 - 25 - wage - 16, "relatório concilia recebimentos, compras, folha e custos")
	check(report.waste == 5 and Core.company.carry == "" and Core.company.production.is_empty() and Core.company.ready.suco == 0, "virada descarta produtos preparados e registra desperdício")
	cash = Core.money
	Sim.rollover(Core)
	check(Core.money == cash and Core.company.sim.history.size() == 1 and Core.prog.staff_rec("cozinheiro").energy == energy_after, "virada repetida não cobra, descarta nem cansa novamente")
	Core.set_kiosk_reorder(true, 4)
	for id in Sim.ingredients(Core):
		Core.stock[id] = 0
	Core.day = 3
	Sim.rollover(Core)
	Sim.run_auto_order(Core)
	cash = Core.money
	Sim.run_auto_order(Core)
	check(Core.stock.coco == 4 and Core.stock.frutas == 4 and Core.money == cash, "reposição automática ocorre uma vez na virada")
	var old_path: String = Core.SAVE_PATH
	Core.SAVE_PATH = "user://simulation_regression_tmp.json"
	Core._pay_wages(true)
	Core.save_game()
	var state: Dictionary = Core.company.duplicate(true)
	Core.company = Core.CompanyRules.defaults()
	check(Core.load_game() and Core.company == Core.CompanyRules.sanitize(state), "save preserva horários, escala, custos e histórico")
	cash = Core.money
	Core._pay_wages(true)
	check(Core.money == cash, "recarga não repete salário já pago")
	var fee: int = Core.prog.staff_wage("cozinheiro") * 3
	check(Core.dismiss_kiosk_staff("cozinheiro") and not Core.staff.cozinheiro and Core.money == cash - fee, "dispensa remove funcionário e cobra rescisão")
	main.hud.phone.open("gestao_equipe")
	main.hud.phone._hire_staff("garcom")
	check(Core.staff.garcom, "contratação pelo painel da equipe")
	for page in ["horarios", "estoque_quiosque", "gestao_equipe", "resultado"]:
		main.hud.phone.open(page)
		await get_tree().process_frame
		await get_tree().process_frame
		check(main.hud.phone.app == page and main.hud.phone.visible, "painel disponível: " + page)
		var spins: Array = main.hud.phone.find_children("*", "SpinBox", true, false)
		if not spins.is_empty():
			var spin = spins[0]
			var edited: float = minf(spin.max_value, spin.value + 1)
			spin.value = edited
			Core.money_changed.emit(Core.money)
			Core.stock_changed.emit()
			Core.company_changed.emit()
			await get_tree().process_frame
			await get_tree().process_frame
			check(is_instance_valid(spin) and spin.value == edited, "vendas não apagam edição: " + page)
	main.hud.phone.close()
	Core.delete_save()
	Core.SAVE_PATH = old_path
	print("SIMULATION_TEST FAIL" if failed else "SIMULATION_TEST PASS")
	get_tree().quit(1 if failed else 0)
