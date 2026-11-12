extends RefCounted
## Regras e contabilidade da operação; sem class_name para aceitar saves anteriores.
const Management = preload("res://scripts/kiosk_management.gd")
const ROLES = ["garcom", "caixa", "limpeza", "cozinheiro", "atendente"]
const DAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

static func stats() -> Dictionary:
	return {"cash_in": 0, "supplies": 0, "payroll": 0, "overhead": 0, "investment": 0, "waste": 0, "stockouts": 0, "open_minutes": 0.0}

static func defaults() -> Dictionary:
	return {"start": 8, "end": 18, "custom_hours": false, "days": [0, 1, 2, 3, 4, 5, 6], "shifts": {}, "auto_order": false, "target": 6, "day": 0, "wage_day": -1, "staff_day": -1, "auto_due": false, "management": Management.defaults(), "today": stats(), "history": []}

static func sanitize(raw: Variant) -> Dictionary:
	var d := defaults()
	if not raw is Dictionary:
		return d
	d.start = clampi(int(raw.get("start", 8)), 6, 22)
	d.end = clampi(int(raw.get("end", 18)), int(d.start) + 1, 23)
	d.custom_hours = bool(raw.get("custom_hours", false))
	d.auto_order = bool(raw.get("auto_order", false))
	d.target = clampi(int(raw.get("target", 6)), 1, 48)
	d.day = maxi(0, int(raw.get("day", 0)))
	d.wage_day = maxi(-1, int(raw.get("wage_day", -1)))
	d.staff_day = maxi(-1, int(raw.get("staff_day", -1)))
	d.auto_due = bool(raw.get("auto_due", false))
	d.management = Management.sanitize(raw.get("management", {}))
	if raw.get("days") is Array:
		d.days = []
		for index in raw.days:
			if (index is int or index is float) and is_finite(float(index)) and int(index) == float(index) and int(index) >= 0 and int(index) < 7 and int(index) not in d.days:
				d.days.append(int(index))
	if raw.get("shifts") is Dictionary:
		for role in ROLES:
			var shift: Variant = raw.shifts.get(role)
			if shift is Dictionary:
				var start := clampi(int(shift.get("start", 8)), 6, 22)
				d.shifts[role] = {"start": start, "end": clampi(int(shift.get("end", 16)), start + 1, 23)}
	if raw.get("today") is Dictionary:
		for key in d.today:
			var value: Variant = raw.today.get(key, 0)
			if (value is int or value is float) and is_finite(float(value)):
				d.today[key] = maxf(0, float(value)) if key == "open_minutes" else maxi(0, int(value))
	if raw.get("history") is Array:
		for entry in raw.history.slice(-7):
			if entry is Dictionary:
				var item := stats()
				for key in item:
					var value: Variant = entry.get(key, 0)
					if (value is int or value is float) and is_finite(float(value)):
						item[key] = maxf(0.0, float(value)) if key == "open_minutes" else maxi(0, int(value))
				item.day = maxi(1, int(entry.get("day", 1)))
				item.net = int(item.cash_in) - int(item.supplies) - int(item.payroll) - int(item.overhead) - int(item.investment)
				d.history.append(item)
	return d

static func is_workday(core) -> bool:
	return posmod(core.day - 1, 7) in core.company.sim.days

static func staff_on_shift(core, role: String) -> bool:
	if not core.kiosk_is_within_hours():
		return false
	var shift: Dictionary = core.company.sim.shifts.get(role, {})
	return shift.is_empty() or (core.minutes >= int(shift.start) * 60.0 and core.minutes < int(shift.end) * 60.0)

static func wage_factor(core, role: String) -> float:
	var shift: Dictionary = core.company.sim.shifts.get(role, {})
	return 1.0 if shift.is_empty() else maxf(0.5, float(int(shift.end) - int(shift.start)) / 8.0)

static func ingredients(core) -> Array:
	var ids: Array = []
	for dish in core.kiosk_menu():
		for id in Economy.dish(dish).uses:
			if id not in ids:
				ids.append(id)
	return ids

static func reorder_quote(core) -> int:
	var total := 0
	for id in ingredients(core):
		var qty := maxi(0, int(core.company.sim.target) - int(core.stock.get(id, 0)))
		if qty > 0:
			total += core.supply_total(id, qty)
	return total

static func reorder(core) -> bool:
	# Compra inteira ou nenhuma: orçamento conferido antes de alterar dinheiro/estoque.
	var total := reorder_quote(core)
	if total > core.money:
		core.toast.emit("Reposição cancelada: saldo insuficiente para completar o pedido.", "bad")
		return false
	for id in ingredients(core):
		var qty := maxi(0, int(core.company.sim.target) - int(core.stock.get(id, 0)))
		if qty > 0:
			core.buy_supply(id, qty)
	return true

static func record(core, key: String, amount: int) -> void:
	if core.company.created:
		core.company.sim.today[key] = int(core.company.sim.today.get(key, 0)) + maxi(0, amount)

static func rollover(core) -> void:
	if not core.company.created:
		return
	var d: Dictionary = core.company.sim
	if int(d.day) == 0:
		d.day = core.day
		return
	if int(d.day) == core.day:
		return
	core.prog._staff_day(true)
	var report: Dictionary = d.today.duplicate(true)
	report.day = int(d.day)
	# Custo de estrutura somente nos dias de operação: R$ 12 + R$ 2 por hora aberta.
	var hours: float = float(report.open_minutes) / 60.0
	var overhead := 12 + int(ceil(hours * 2.0)) if hours > 0.0 else 0
	if overhead > 0:
		core.book(-overhead, "Quiosque: energia, água e manutenção", "operacao", false)
	report.overhead = overhead
	# Produtos preparados na prateleira duram até a virada do dia; ingredientes usam spoil_stock().
	for id in core.company.ready:
		var keep: int = Management.retain(core, id, int(core.company.ready[id]))
		report.waste += int(core.company.ready[id]) - keep
		core.company.ready[id] = keep
	for key in ["carry", "staff_carry"]:
		if str(core.company[key]) != "":
			report.waste += 1
			core.company[key] = ""
	if not core.company.production.is_empty():
		report.waste += 1
		core.company.production = {}
	report.net = int(report.cash_in) - int(report.supplies) - int(report.payroll) - overhead - int(report.investment)
	d.history.append(report)
	if d.history.size() > 7:
		d.history.pop_front()
	d.management.store = {}
	Management.new_day(core)
	d.today = stats()
	d.day = core.day  # gravar antes da compra impede fechamento repetido após recarga
	d.auto_due = bool(d.auto_order)
	core.company_changed.emit()

static func run_auto_order(core) -> void:
	if core.company.created and bool(core.company.sim.auto_due):
		core.company.sim.auto_due = false
		reorder(core)

static func tick(core, elapsed_minutes: float) -> void:
	rollover(core)
	run_auto_order(core)
	Management.tick(core, elapsed_minutes)
	if core.company.created and core.kiosk_accepting_customers():
		core.company.sim.today.open_minutes += clampf(elapsed_minutes, 0.0, 60.0)
