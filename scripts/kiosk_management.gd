extends RefCounted
## Rotina, candidatos, entregas, equipamentos, identidade e demanda do quiosque.
static var _equipment_warning: Dictionary = {}
const ROLES = ["garcom", "caixa", "limpeza", "cozinheiro", "atendente"]
const EQUIPMENT = {"fridge": "Geladeira", "grill": "Chapa", "blender": "Liquidificador"}
const PAINT = {"mar": Color(0.35, 0.75, 0.8), "coral": Color(0.96, 0.55, 0.42), "areia": Color(0.94, 0.82, 0.58)}
const UNIFORMS = {"mar": Color(0.12, 0.55, 0.65), "coral": Color(0.85, 0.32, 0.25), "areia": Color(0.94, 0.85, 0.65)}
const BOARDS = {"madeira": Color(0.06, 0.29, 0.31), "clara": Color(0.75, 0.68, 0.5), "escura": Color(0.08, 0.09, 0.14)}
const SUPPLIERS = {"express": {"name": "Mercado Express", "factor": 1.15, "hour": 0, "min": 1}, "horta": {"name": "Horta da Vila", "factor": 0.88, "hour": 8, "min": 1}, "atacado": {"name": "Distribuidora Costa", "factor": 0.8, "hour": 14, "min": 12}}
const PROFILES = [
 {"title": "Em formação", "speed": 0.9, "care": 0.9, "social": 0.95, "wage": 0.85, "fee": 0.85, "trait": "aprendiz"},
 {"title": "Ágil e experiente", "speed": 1.15, "care": 0.95, "social": 1.0, "wage": 1.2, "fee": 1.3, "trait": "rapido"},
 {"title": "Cuidadoso e cordial", "speed": 0.95, "care": 1.25, "social": 1.3, "wage": 1.1, "fee": 1.15, "trait": "incansavel"}]
const NAMES = {"garcom": ["Lara", "Davi", "Caio"], "caixa": ["Aline", "Bruno", "Nina"], "limpeza": ["Rosa", "Joel", "Beto"], "cozinheiro": ["Iara", "Enzo", "Lúcia"], "atendente": ["Bia", "André", "Rui"]}

static func defaults() -> Dictionary:
 return {"day": 0, "counter": 100.0, "strict": false, "checks": [], "closed_day": -1, "closing": {}, "store": {}, "aged": [],
  "orders": [], "delivery_log": [], "next_order": 1, "profiles": {}, "worked": {},
  "equipment": {"fridge": {"condition": 100.0, "hygiene": 100.0, "level": 1}, "grill": {"condition": 100.0, "hygiene": 100.0, "level": 1}, "blender": {"condition": 100.0, "hygiene": 100.0, "level": 1}},
  "task": {}, "look": {"paint": "mar", "board": "madeira", "uniform": "mar", "layout": "original", "menu": true}, "look_owned": false}

static func number(raw: Variant, fallback: float, low: float, high: float) -> float:
 return clampf(float(raw), low, high) if (raw is int or raw is float) and is_finite(float(raw)) else fallback

static func sanitize(raw: Variant) -> Dictionary:
 var d := defaults()
 if not raw is Dictionary: return d
 d.day = int(number(raw.get("day"), 0, 0, 100000))
 d.closed_day = int(number(raw.get("closed_day"), -1, -1, 100000))
 d.strict = bool(raw.get("strict", false))
 d.counter = number(raw.get("counter"), 100, 0, 100)
 d.look_owned = bool(raw.get("look_owned", false))
 if raw.get("checks") is Array:
  for key in ["limpeza", "estoque", "equipe"]:
   if key in raw.checks: d.checks.append(key)
 if raw.get("look") is Dictionary:
  for key in d.look:
   if key == "menu": d.look.menu = bool(raw.look.get("menu", true))
   else:
    var allowed: Array = PAINT.keys() if key == "paint" else (BOARDS.keys() if key == "board" else (UNIFORMS.keys() if key == "uniform" else ["original", "amplo"]))
    var value := str(raw.look.get(key, d.look[key]))
    if value in allowed: d.look[key] = value
 if raw.get("equipment") is Dictionary:
  for id in EQUIPMENT:
   var item: Variant = raw.equipment.get(id)
   if item is Dictionary:
    d.equipment[id].condition = float(roundi(number(item.get("condition"), 100, 0, 100) * 100.0)) / 100.0
    d.equipment[id].hygiene = float(roundi(number(item.get("hygiene"), 100, 0, 100) * 100.0)) / 100.0
    d.equipment[id].level = int(number(item.get("level"), 1, 1, 3))
 if raw.get("profiles") is Dictionary:
  for role in ROLES:
   var item: Variant = raw.profiles.get(role)
   if item is Dictionary:
    d.profiles[role] = {"kind": int(number(item.get("kind"), 0, 0, 2)), "morale": number(item.get("morale"), 100, 0, 100)}
 if raw.get("worked") is Dictionary:
  for role in ROLES: d.worked[role] = number(raw.worked.get(role), 0, 0, 1440)
 if raw.get("store") is Dictionary:
  for id in Economy.KIOSK_MENU: d.store[id] = int(number(raw.store.get(id), 0, 0, 4))
 if raw.get("aged") is Array:
  for id in Economy.KIOSK_MENU:
   if id in raw.aged: d.aged.append(id)
 d.next_order = int(number(raw.get("next_order"), 1, 1, 10000000))
 if raw.get("orders") is Array:
  for order in raw.orders.slice(0, 32):
   if order is Dictionary and str(order.get("ingredient", "")) in Economy.SUPPLIES and str(order.get("supplier", "")) in SUPPLIERS:
    d.orders.append({"id": int(number(order.get("id"), 1, 1, 10000000)), "ingredient": str(order.ingredient), "supplier": str(order.supplier), "qty": int(number(order.get("qty"), 1, 1, 48)), "due_day": int(number(order.get("due_day"), 1, 1, 100000)), "due_min": int(number(order.get("due_min"), 480, 0, 1439)), "cost": int(number(order.get("cost"), 0, 0, 1000000))})
 if raw.get("delivery_log") is Array:
  for line in raw.delivery_log.slice(-8): d.delivery_log.append(str(line).left(150))
 if raw.get("task") is Dictionary:
  var task: Dictionary = raw.task
  if str(task.get("item", "")) in EQUIPMENT and str(task.get("kind", "")) in ["clean", "repair"]:
   d.task = {"item": str(task.item), "kind": str(task.kind), "left": number(task.get("left"), 15, 0, 60)}
 if raw.get("closing") is Dictionary:
  for key in ["day", "expected", "counted", "variance"]:
   d.closing[key] = int(number(raw.closing.get(key), 0, -10000000, 10000000))
 return d

static func state(core) -> Dictionary:
 return core.company.sim.management

static func changed(core, save: bool = true) -> void:
 core.company_changed.emit()
 if save: core.save_game()

static func new_day(core) -> void:
 var d := state(core)
 if int(d.day) == core.day: return
 if int(d.day) > 0:
  d.counter = maxf(0, float(d.counter) - 5)
  for role in d.profiles:
   var rec: Dictionary = d.profiles[role]
   var hours := float(d.worked.get(role, 0)) / 60.0
   rec.morale = clampf(float(rec.morale) + (8 if hours == 0 else (2 if hours <= 8 else -8 * (hours - 8))), 0, 100)
   if hours > 8 and core.staff.get(role, false):
    var employee: Dictionary = core.prog.staff_rec(role)
    employee.energy = maxi(0, int(employee.energy) - int((hours - 8) * 3))
 d.day = core.day
 d.checks = []
 d.worked = {}

static func opening_ready(core) -> bool:
 var d := state(core)
 return not bool(d.strict) or (int(d.day) == core.day and d.checks.size() == 3 and int(d.closed_day) != core.day)

static func check_opening(core, key: String) -> bool:
 if not core.company.created: return false
 if key not in ["limpeza", "estoque", "equipe"] or bool(core.company.kiosk_open):
  core.toast.emit("Feche o quiosque para conferir a abertura.", "info")
  return false
 new_day(core)
 if key == "estoque":
  for id in core.CompanyRules.Simulation.ingredients(core):
   if int(core.stock.get(id, 0)) < 1:
    core.toast.emit("Reponha os ingredientes do cardápio antes de confirmar o estoque.", "bad")
    return false
 var d := state(core)
 if key == "limpeza": d.counter = 100.0
 if key not in d.checks: d.checks.append(key)
 # Uma nova conferência permite reabrir no mesmo dia após um fechamento.
 d.closed_day = -1
 changed(core)
 return true

static func active_service(core) -> bool:
 for village in core.get_tree().get_nodes_in_group("kiosk"):
  for guest in village.customers:
   if is_instance_valid(guest) and guest.state != "kleave": return true
 return false

static func can_close(core) -> bool:
 return not bool(core.company.kiosk_open) and not active_service(core) and core.company.receivables.is_empty() and core.company.dirty_seats.is_empty() and core.company.production.is_empty() and core.company.carry == "" and core.company.staff_carry == ""

static func store_drinks(core) -> bool:
 if not can_close(core) or not core.freezer:
  core.toast.emit("Conclua o atendimento, receba, limpe e tenha freezer para guardar bebidas.", "info")
  return false
 var d := state(core)
 if float(d.equipment.fridge.condition) < 50 or float(d.equipment.fridge.hygiene) < 50: return false
 d.store = {}
 for id in core.company.ready:
  if load("res://scripts/dish_presentation.gd").is_drink(id) and id not in d.aged:
   d.store[id] = int(core.company.ready[id])
 changed(core)
 return true

static func retain(core, id: String, qty: int) -> int:
 var d := state(core)
 var keep := mini(qty, int(d.store.get(id, 0))) if core.freezer and id not in d.aged and float(d.equipment.fridge.condition) >= 50 and float(d.equipment.fridge.hygiene) >= 50 else 0
 if keep > 0: d.aged.append(id)
 else: d.aged.erase(id)
 return keep

static func close_shift(core, counted: int) -> bool:
 if not core.company.created: return false
 var d := state(core)
 if not can_close(core) or int(d.closed_day) == core.day:
  core.toast.emit("Feche novas chegadas e conclua clientes, caixa, louça e preparo antes do fechamento.", "info")
  return false
 var expected: int = int(core.company.sim.today.cash_in)
 d.closing = {"day": core.day, "expected": expected, "counted": maxi(0, counted), "variance": maxi(0, counted) - expected}
 d.closed_day = core.day
 d.checks = []
 changed(core)
 return true

static func candidate(role: String, kind: int) -> Dictionary:
 var p: Dictionary = PROFILES[clampi(kind, 0, 2)].duplicate()
 p.name = NAMES[role][clampi(kind, 0, 2)]
 p.cost = int(round(int(Economy.STAFF[role].hire) * float(p.fee)))
 p.daily = int(round(int(Economy.STAFF[role].wage) * float(p.wage)))
 return p

static func hire_candidate(core, role: String, kind: int) -> bool:
 if not core.company.created: return false
 if role not in ROLES or kind < 0 or kind > 2 or core.staff.get(role, false): return false
 var p := candidate(role, kind)
 if core.money < int(p.cost): return false
 if not core.hire(role, int(p.cost)): return false
 state(core).profiles[role] = {"kind": kind, "morale": 100.0}
 var rec: Dictionary = core.prog.staff_rec(role)
 rec.trait = p.trait
 core.staff_changed.emit()
 changed(core)
 return true

static func profile_factor(core, role: String, key: String) -> float:
 var d := state(core)
 if not d.profiles.has(role): return 1.0
 var p: Dictionary = d.profiles[role]
 var factor: float = float(PROFILES[int(p.kind)].get(key, 1.0))
 if key == "speed" and float(p.morale) < 30: factor *= 0.7
 return factor

static func quote(core, supplier: String, ingredient: String, qty: int) -> Dictionary:
 if supplier not in SUPPLIERS or ingredient not in Economy.SUPPLIES or qty < int(SUPPLIERS[supplier].min) or qty > 48: return {}
 var s: Dictionary = SUPPLIERS[supplier]
 return {"cost": int(ceil(core.supply_total(ingredient, qty) * float(s.factor))), "day": core.day if supplier == "express" else core.day + 1, "minute": int(core.minutes) if supplier == "express" else int(s.hour) * 60 + (60 if core.forecast_next == "tempestade" else 0)}

static func order_supply(core, supplier: String, ingredient: String, qty: int, expected: int = -1) -> bool:
 if not core.company.created: return false
 var q := quote(core, supplier, ingredient, qty)
 var d := state(core)
 if q.is_empty() or d.orders.size() >= 32 or core.money < int(q.cost): return false
 if expected >= 0 and int(q.cost) != expected:
  core.toast.emit("O preço mudou. Atualize a cotação antes de encomendar.", "info")
  return false
 core.book(-int(q.cost), "Fornecedor: " + str(SUPPLIERS[supplier].name), "insumo", true)
 if supplier == "express":
  core.stock[ingredient] = int(core.stock.get(ingredient, 0)) + qty
  core.stock_changed.emit()
 else:
  d.orders.append({"id": int(d.next_order), "ingredient": ingredient, "supplier": supplier, "qty": qty, "due_day": int(q.day), "due_min": int(q.minute), "cost": int(q.cost)})
  d.next_order += 1
 changed(core)
 return true

static func equipment_for(id: String) -> Array:
 if not load("res://scripts/dish_presentation.gd").is_drink(id): return ["grill"]
 return ["fridge", "blender"] if id in ["suco", "caipirinha", "batida"] else ["fridge"]

static func can_prepare(core, id: String) -> bool:
 var d := state(core)
 if not d.task.is_empty(): return false
 for machine in equipment_for(id):
  if float(d.equipment[machine].condition) < 10 or float(d.equipment[machine].hygiene) < 15:
   var now := Time.get_ticks_msec()
   if now - int(_equipment_warning.get(machine, -15000)) >= 15000:
    _equipment_warning[machine] = now
    core.toast.emit("Equipamento precisa de limpeza ou manutenção: " + str(EQUIPMENT[machine]), "bad")
   return false
 return true

static func prepare_speed(core, id: String) -> float:
 var speed := 2.0
 for machine in equipment_for(id):
  var item: Dictionary = state(core).equipment[machine]
  speed = minf(speed, (0.55 + float(item.condition) * 0.0045) * (1 + 0.1 * (int(item.level) - 1)))
 return speed

static func wear(core, id: String) -> void:
 state(core).counter = maxf(0, float(state(core).counter) - 1)
 for machine in equipment_for(id):
  var item: Dictionary = state(core).equipment[machine]
  item.condition = maxf(0, float(item.condition) - 0.35)
  item.hygiene = maxf(0, float(item.hygiene) - 2)
 if int(core.company.ready.get(id, 0)) == 0: state(core).aged.erase(id)

static func error_risk(core, id: String) -> float:
 var energy := 100
 if core.staff.get("cozinheiro", false) and core.kiosk_staff_on_shift("cozinheiro"): energy = int(core.prog.staff_rec("cozinheiro").energy)
 var hygiene: float = float(state(core).counter)
 for machine in equipment_for(id): hygiene = minf(hygiene, float(state(core).equipment[machine].hygiene))
 return clampf((maxf(0, 30 - energy) * 0.008 + maxf(0, 35 - hygiene) * 0.004) / profile_factor(core, "cozinheiro", "care"), 0, 0.4)

static func equipment_action(core, id: String, action: String) -> bool:
 if not core.company.created: return false
 var d := state(core)
 if id not in EQUIPMENT or action not in ["clean", "repair", "upgrade"] or not d.task.is_empty() or not core.company.production.is_empty() or bool(core.company.kiosk_open):
  core.toast.emit("Feche as chegadas e termine o preparo antes de cuidar dos equipamentos.", "info")
  return false
 var item: Dictionary = d.equipment[id]
 if action == "upgrade" and int(item.level) >= 3: return false
 var cost := 3 if action == "clean" else (int(ceil((100 - float(item.condition)) * 0.8)) if action == "repair" else 240 * int(item.level))
 if core.money < cost: return false
 if (action == "clean" and float(item.hygiene) >= 100) or (action == "repair" and float(item.condition) >= 100): return false
 core.book(-cost, str(EQUIPMENT[id]) + ": " + str({"clean": "limpeza", "repair": "reparo", "upgrade": "melhoria"}[action]), "equipamento", false)
 core.CompanyRules.Simulation.record(core, "investment", cost)
 if action == "upgrade":
  item.level += 1
  item.condition = 100.0
 else: d.task = {"item": id, "kind": action, "left": 12.0 if action == "clean" else 30.0}
 changed(core)
 return true

static func apply_look(core, choice: Dictionary) -> bool:
 if not core.company.created: return false
 var clean: Dictionary = sanitize({"look": choice}).look
 if bool(core.company.kiosk_open) or active_service(core) or not core.company.dirty_seats.is_empty():
  core.toast.emit("Personalize com o quiosque fechado, sem clientes nem louça nas mesas.", "info")
  return false
 var d := state(core)
 if bool(d.look_owned) and clean == d.look: return true
 if core.money < 180: return false
 core.book(-180, "Personalização do quiosque", "decoracao", false)
 core.CompanyRules.Simulation.record(core, "investment", 180)
 d.look = clean
 d.look_owned = true
 changed(core)
 return true

static func arrival_factor(core) -> float:
 if not core.company.created: return 1.0
 var hour: float = core.minutes / 60.0
 var factor := 0.75 if hour < 10 else (1.4 if hour >= 11 and hour < 14 else (1.15 if hour < 17 else 1.25))
 if core.weather == "rain": factor *= 0.65
 if core.day_event == "tempestade": factor *= 0.55
 return factor

static func dish_weight(core, id: String) -> float:
 if not core.company.created: return 1.0
 var hour: float = core.minutes / 60.0
 var drink: bool = load("res://scripts/dish_presentation.gd").is_drink(id)
 if hour < 10: return 2.0 if id in ["suco", "tapioca"] else (1.2 if drink else 0.65)
 if hour >= 11 and hour < 14: return 2.2 if not drink else 0.85
 if hour < 17: return 1.8 if drink else 0.8
 return 1.7 if id in ["caipirinha", "petiscos", "batida"] else 1.0

static func sheltered(core, spot: Dictionary) -> bool:
 return not core.company.created or core.weather != "rain" or not bool(spot.get("table", false)) or bool(spot.get("covered", false))

static func tick(core, minutes: float) -> void:
 if not core.company.created: return
 new_day(core)
 var d := state(core)
 var notify := false
 for order in d.orders.duplicate():
  if core.day > int(order.due_day) or (core.day == int(order.due_day) and core.minutes >= int(order.due_min)):
   core.stock[order.ingredient] = int(core.stock.get(order.ingredient, 0)) + int(order.qty)
   d.delivery_log.append("Dia %d: %d × %s — %s" % [core.day, int(order.qty), Economy.SUPPLIES[order.ingredient].name, SUPPLIERS[order.supplier].name])
   if d.delivery_log.size() > 8: d.delivery_log.pop_front()
   d.orders.erase(order)
   core.stock_changed.emit()
   core.toast.emit("Entrega recebida: %d × %s" % [int(order.qty), Economy.SUPPLIES[order.ingredient].name], "good")
   notify = true
 if not d.task.is_empty():
  d.task.left = float(d.task.left) - maxf(0, minutes)
  if float(d.task.left) <= 0:
   d.equipment[d.task.item]["hygiene" if d.task.kind == "clean" else "condition"] = 100.0
   d.task = {}
   core.toast.emit("Cuidado com o equipamento concluído.", "good")
   notify = true
 if core.kiosk_accepting_customers():
  d.equipment.fridge.condition = maxf(0, float(d.equipment.fridge.condition) - maxf(0, minutes) * 0.01)
  for role in d.profiles:
   if core.prog.staff_eff(role) > 0: d.worked[role] = float(d.worked.get(role, 0)) + maxf(0, minutes)
 if notify: changed(core)
