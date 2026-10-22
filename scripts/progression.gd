extends Node
class_name Prog
## v1.0 — sistemas de evolução: fama, árvore de melhorias, negócios, equipe com nível, temporadas e metas,
## receitas/fornecedores e capítulos da vila. Vive como filho do Core (Core.prog) e é salvo junto (save v6).

signal fame_changed(level: int, xp: int)
signal tree_changed
signal biz_changed(id: String)
signal goals_changed
signal chapters_changed
signal recipes_changed

var fame_xp: = 0
var fame_level: = 1
var tree: = {}            # ramo -> nível (0..3)
var biz: = {}             # id -> {"lvl": 1, "games_hour": -1, "today": 0}
var staff_info: = {}      # cargo -> {"lvl", "xp", "energy", "trait", "off"}
var week_goals: Array = []
var week_stats: = {}
var season_stats: = {"earn": 0}
var medals: Array = []    # [{"season": n, "medal": "ouro"}]
var discovered: = {}      # prato secreto -> true
var menu_off: = {}        # prato -> true (desligado no cardápio)
var premium: = {}         # insumo -> true (fornecedor premium)
var chapters: = {}        # id -> passo atual (0..3); 3 = concluído
var chapter_photo: = {}   # tema -> true (fotos feitas, para os passos "photo")
var hotel_last: = {}      # última noite do Grand Hotel: occ (0..1), rooms, rev, dining, staff
var _hour_acc: = 0.0

func reset() -> void:
	fame_xp = 0
	fame_level = 1
	tree = {}
	biz = {}
	staff_info = {}
	week_goals = []
	week_stats = {}
	season_stats = {"earn": 0}
	medals = []
	discovered = {}
	menu_off = {}
	premium = {}
	chapters = {}
	chapter_photo = {}
	hotel_last = {}
	_hour_acc = 0.0
	roll_week()

# ================================================================== fama
func add_fame(xp: int, why: = "") -> void:
	if xp <= 0:
		return
	fame_xp += xp
	var lvl: = 1
	for i in PD.FAME_XP.size():
		if fame_xp >= int(PD.FAME_XP[i]):
			lvl = i + 1
	if lvl > fame_level:
		fame_level = lvl
		var perk: = str(PD.FAME_PERKS.get(lvl, ""))
		Core.toast.emit(tr("Fama subiu: %s! %s") % [tr(fame_name()), tr(perk)], "good")
		get_tree().call_group("audio", "sfx", "bell")
	fame_changed.emit(fame_level, fame_xp)

func fame_name(lvl: = -1) -> String:
	var l: = fame_level if lvl < 1 else lvl
	return str(PD.FAME_NAMES[clampi(l - 1, 0, PD.FAME_NAMES.size() - 1)])

func fame_progress() -> Array:
	# [xp no nível, xp para o próximo] ou [x, 0] no máximo
	if fame_level >= PD.FAME_XP.size():
		return [fame_xp, 0]
	var a: = int(PD.FAME_XP[fame_level - 1])
	var b: = int(PD.FAME_XP[fame_level])
	return [fame_xp - a, b - a]

# ================================================================== árvore de melhorias
func lvl(branch: String) -> int:
	return int(tree.get(branch, 0))

## Efeito somado de um ramo (nível × valor por nível).
func eff(branch: String) -> float:
	for area in PD.TREE:
		var br: Dictionary = PD.TREE[area].branches
		if br.has(branch):
			return float(br[branch].per) * float(lvl(branch))
	return 0.0

func branch_area(branch: String) -> String:
	for area in PD.TREE:
		if PD.TREE[area].branches.has(branch):
			return area
	return ""

## ["ready"|"max"|"locked"|"money", motivo, custo]
func tree_state(branch: String) -> Array:
	var l: = lvl(branch)
	if l >= 3:
		return ["max", "", 0]
	var area: Dictionary = PD.TREE[branch_area(branch)]
	var need: = str(area.need)
	if need != "" and not Core.has(need):
		return ["locked", tr("Precisa de: %s") % tr(str(Economy.EXPANSIONS[need].name)), 0]
	var fr: = int(PD.TREE_FAME[l])
	if fame_level < fr:
		return ["locked", tr("Fama \"%s\"") % tr(fame_name(fr)), 0]
	var cost: = int(PD.TREE_COST[l])
	if Core.money < cost:
		return ["money", tr("Faltam %s") % Core.fmt_money(cost - Core.money), cost]
	return ["ready", "", cost]

func buy_tree(branch: String) -> bool:
	var st: = tree_state(branch)
	if st[0] != "ready":
		if st[1] != "":
			Core.toast.emit(str(st[1]), "bad")
		return false
	tree[branch] = lvl(branch) + 1
	var nm: = str(PD.TREE[branch_area(branch)].branches[branch].name)
	Core.book(- int(st[2]), tr("Melhoria: %s %d") % [tr(nm), lvl(branch)], "upgrade", true)
	tree_changed.emit()
	Core.save_game()
	return true

# ================================================================== negócios
func owns(id: String) -> bool:
	return biz.has(id)

func biz_state(id: String) -> Array:
	var b: Dictionary = PD.BUSINESSES[id]
	if owns(id):
		return ["owned", ""]
	var ch: = str(b.chapter)
	if ch != "" and not chapter_done(ch):
		return ["locked", tr("Libere no capítulo \"%s\"") % tr(chapter_title(ch))]
	if fame_level < int(b.fame):
		return ["locked", tr("Fama \"%s\"") % tr(fame_name(int(b.fame)))]
	if Core.money < int(b.cost):
		return ["money", tr("Faltam %s") % Core.fmt_money(int(b.cost) - Core.money)]
	return ["ready", ""]

func buy_biz(id: String) -> bool:
	var st: = biz_state(id)
	if st[0] != "ready":
		if st[1] != "":
			Core.toast.emit(str(st[1]), "bad")
		return false
	biz[id] = {"lvl": 1, "games_hour": -1, "today": 0}
	Core.book(- int(PD.BUSINESSES[id].cost), tr(str(PD.BUSINESSES[id].name)), "upgrade", true)
	Core.toast.emit(tr("Novo negócio aberto: %s!") % tr(str(PD.BUSINESSES[id].name)), "good")
	get_tree().call_group("audio", "sfx", "bell")
	biz_changed.emit(id)
	Core.save_game()
	return true

func upgrade_biz(id: String) -> bool:
	if not owns(id):
		return false
	var l: = int(biz[id].lvl)
	if l >= 3:
		return false
	var cost: = int(PD.BIZ_UPGRADE_COST[l])
	if Core.money < cost:
		Core.toast.emit(tr("Faltam %s") % Core.fmt_money(cost - Core.money), "bad")
		return false
	biz[id].lvl = l + 1
	Core.book(- cost, tr("%s nível %d") % [tr(str(PD.BUSINESSES[id].name)), l + 1], "upgrade", true)
	biz_changed.emit(id)
	return true

func biz_open(id: String) -> bool:
	var o: Array = PD.BUSINESSES[id].open
	var h: = Core.minutes / 60.0
	if h < float(o[0]) or h >= float(o[1]):
		return false
	if id == "aluguel" and (Core.day_event == "mare" or Core.day_event == "tempestade"):
		return false
	if id == "surfe" and Core.day_event == "tempestade":
		return false
	return true

## Renda por hora agora (0 se fechado).
func biz_rate(id: String) -> int:
	if not owns(id) or not biz_open(id):
		return 0
	var b: Dictionary = PD.BUSINESSES[id]
	var r: = float(b.hour) * float(PD.BIZ_LEVEL_MULT[int(biz[id].lvl) - 1]) * (1.0 + 0.06 * float(fame_level - 1)) * season_demand()
	match id:
		"sorveteria":
			r *= 1.8 if Core.day_event == "calor" else (0.2 if Core.weather == "rain" else 1.0)
			if season_id() == "inverno":
				r *= 0.5
		"aluguel":
			r *= 1.2 if season_id() == "verao" else 1.0
		"surfe":
			r *= 1.3 if Core.day_event == "mare" else 1.0
			r *= 1.0 + (0.15 if fame_level >= 5 else 0.0)
		"food_truck":
			r *= 1.6 if Core.is_party() else 1.0
		"souvenir":
			r *= 1.0 + 0.05 * float(fame_level)
	if Core.weather == "rain" and id != "food_truck" and id != "souvenir":
		r *= 0.4
	return int(round(r))

func _biz_tick() -> void:
	var total: = 0
	for id in biz:
		var v: = biz_rate(id)
		if v > 0:
			biz[id].today = int(biz[id].get("today", 0)) + v
			total += v
	if total > 0:
		Core.book(total, tr("Negócios (última hora)"), "negocio", false)

## Minijogo do balcão: uma vez por hora por negócio. score 0..3 -> prêmio.
func can_play(id: String) -> bool:
	return owns(id) and biz_open(id) and int(biz[id].get("games_hour", -1)) != int(Core.minutes / 60.0) + Core.day * 24

func play_result(id: String, score: int) -> void:
	if not owns(id):
		return
	biz[id].games_hour = int(Core.minutes / 60.0) + Core.day * 24
	var base: = maxi(biz_rate(id), int(PD.BUSINESSES[id].hour))
	var reward: = int(round(float(base) * [0.3, 0.8, 1.4, 2.2][clampi(score, 0, 3)]))
	Core.book(reward, tr("%s: atendimento (%d/3)") % [tr(str(PD.BUSINESSES[id].name)), score], "negocio", true)
	add_fame(PD.XP.biz_game * score)
	_goal_add("biz", 1)
	biz_changed.emit(id)

# ================================================================== equipe
func staff_rec(role: String) -> Dictionary:
	if not staff_info.has(role):
		var traits: = PD.STAFF_TRAITS.keys()
		staff_info[role] = {"lvl": 1, "xp": 0, "energy": 100, "trait": str(traits[randi() % traits.size()]), "off": false}
	return staff_info[role]

## Multiplicador de rendimento (nível, cansaço, traço). 0 se está de folga hoje.
func staff_eff(role: String) -> float:
	if not bool(Core.staff.get(role, false)):
		return 0.0
	var s: = staff_rec(role)
	if Core.company.created and role in Core.CompanyRules.Simulation.ROLES and not Core.kiosk_staff_on_shift(role):
		return 0.0
	if bool(s.off):
		return 0.0
	var e: = 1.0 + 0.12 * float(int(s.lvl) - 1)
	if int(s.energy) < 30:
		e *= 0.6
	if str(s.trait) == "rapido":
		e *= 1.2
	return e

func staff_wage(role: String) -> int:
	var base: = int(Economy.STAFF[role].wage)
	var s: = staff_rec(role)
	var w: = float(base) * (1.0 + 0.15 * float(int(s.lvl) - 1))
	if str(s.trait) == "economico":
		w *= 0.85
	if bool(s.off):
		w *= 0.5
	if Core.company.created and role in Core.CompanyRules.Simulation.ROLES:
		w *= Core.CompanyRules.Simulation.wage_factor(Core, role)
	return int(round(w))

func train(role: String) -> bool:
	var s: = staff_rec(role)
	var cost: = PD.STAFF_TRAIN_COST * int(s.lvl)
	if Core.money < cost or int(s.lvl) >= PD.STAFF_XP.size():
		return false
	if role in Core.CompanyRules.Simulation.ROLES:
		Core.CompanyRules.Simulation.record(Core, "investment", cost)
	Core.book(- cost, tr("Treinamento: %s") % tr(str(Economy.STAFF[role].name)), "folha", true)
	_staff_xp(role, 40)
	s.energy = maxi(0, int(s.energy) - 10)
	Core.staff_changed.emit()
	return true

func toggle_off(role: String) -> void:
	var s: = staff_rec(role)
	s.off = not bool(s.off)
	Core.staff_changed.emit()

func _staff_xp(role: String, xp: int) -> void:
	var s: = staff_rec(role)
	if str(s.trait) == "aprendiz":
		xp = int(xp * 1.5)
	s.xp = int(s.xp) + xp
	var l: = 1
	for i in PD.STAFF_XP.size():
		if int(s.xp) >= int(PD.STAFF_XP[i]):
			l = i + 1
	if l > int(s.lvl):
		s.lvl = l
		Core.toast.emit(tr("%s subiu para o nível %d!") % [tr(str(Economy.STAFF[role].name)), l], "good")

func _staff_day(company_only: bool = false) -> void:
	var work_day: int = Core.day - 1
	for role in Core.staff:
		var company_role: bool = Core.company.created and role in Core.CompanyRules.Simulation.ROLES
		if company_only and not company_role:
			continue
		if company_role and int(Core.company.sim.staff_day) >= work_day:
			continue
		if not bool(Core.staff[role]):
			continue
		var s: = staff_rec(role)
		var scheduled_off: bool = company_role and posmod(work_day - 1, 7) not in Core.company.sim.days
		if bool(s.off) or scheduled_off:
			s.energy = mini(100, int(s.energy) + PD.STAFF_REST)
			s.off = false
		else:
			var factor: float = Core.CompanyRules.Simulation.wage_factor(Core, role) if company_role else 1.0
			_staff_xp(role, int(round(20 * factor)))
			var fatigue: float = PD.STAFF_FATIGUE / 2.0 if str(s.trait) == "incansavel" else float(PD.STAFF_FATIGUE)
			s.energy = maxi(0, int(s.energy) - int(round(fatigue * factor)))
			if int(s.energy) < 30:
				Core.toast.emit(tr("%s está exausto(a). Dê uma folga na aba Equipe.") % tr(str(Economy.STAFF[role].name)), "bad")

	if Core.company.created:
		Core.company.sim.staff_day = maxi(int(Core.company.sim.staff_day), work_day)

# ================================================================== temporadas e metas
func season_index(d: = -1) -> int:
	var dd: = Core.day if d < 0 else d
	return int((dd - 1) / PD.SEASON_DAYS) % PD.SEASONS.size()

func season_id() -> String:
	return str(PD.SEASONS[season_index()].id)

func season_name() -> String:
	return str(PD.SEASONS[season_index()].name)

func season_demand() -> float:
	return float(PD.SEASONS[season_index()].demand)

func season_number() -> int:
	return int((Core.day - 1) / PD.SEASON_DAYS) + 1

func day_in_season() -> int:
	return (Core.day - 1) % PD.SEASON_DAYS + 1

func is_carnaval_day(d: int) -> bool:
	# último dia de cada verão, depois do capítulo do prefeito
	return chapter_done("carnaval") and season_index(d) == 0 and (d - 1) % PD.SEASON_DAYS == PD.SEASON_DAYS - 1

func roll_week() -> void:
	week_goals.clear()
	week_stats = {"serve": 0, "earn": 0, "dish": 0, "vip": 0, "tour": 0, "biz": 0, "photo": 0}
	var pool: Array = PD.GOAL_POOL.filter(func(g):
		if g.has("need") and not Core.has(str(g.need)):
			return false
		if g.get("need_biz", false) and biz.is_empty():
			return false
		return true)
	pool.shuffle()
	for i in mini(3, pool.size()):
		var g: Dictionary = pool[i]
		var target = float(g.base) + float(g.per_fame) * float(fame_level - 1)
		week_goals.append({"kind": g.kind, "target": target, "reward": int(g.reward) + 20 * (fame_level - 1), "done": false,
			"text": str(g.text), "money": g.get("money", false), "float": g.get("float", false)})
	goals_changed.emit()

func goal_text(g: Dictionary) -> String:
	if bool(g.get("money", false)):
		return tr(str(g.text)) % Core.fmt_money(int(g.target))
	if bool(g.get("float", false)):
		return tr(str(g.text)) % float(g.target)
	return tr(str(g.text)) % int(g.target)

func goal_progress(g: Dictionary) -> float:
	if str(g.kind) == "rating":
		return Core.stars()
	return float(week_stats.get(str(g.kind), 0))

func _goal_add(kind: String, v: int) -> void:
	week_stats[kind] = int(week_stats.get(kind, 0)) + v
	for g in week_goals:
		if not bool(g.done) and str(g.kind) == kind and goal_progress(g) >= float(g.target):
			g.done = true
			Core.book(int(g.reward), tr("Meta da semana: %s") % goal_text(g), "missao", true)
			add_fame(PD.XP.goal)
	goals_changed.emit()

## Ranking da temporada: rivais com pontuação proporcional à fama e ao dia.
func ranking() -> Array:
	var base: = 600.0 * (1.0 + 0.35 * float(fame_level - 1)) * float(day_in_season()) / float(PD.SEASON_DAYS)
	var out: Array = []
	for r in PD.RIVALS:
		out.append([str(r[0]), int(base * float(r[1]))])
	out.append([tr("Quiosque Maré Alta (você)"), int(season_stats.get("earn", 0))])
	out.sort_custom(func(a, b): return a[1] > b[1])
	return out

func _season_end() -> void:
	var rank: = ranking()
	var pos: = 0
	for i in rank.size():
		if str(rank[i][0]).ends_with("(você)"):
			pos = i
	var medal: = ""
	if pos == 0:
		medal = "ouro"
	elif pos <= 1:
		medal = "prata"
	elif pos <= 2:
		medal = "bronze"
	if medal != "":
		var m: Array = PD.MEDALS.filter(func(x): return x[0] == medal)[0]
		var reward: = int(m[2]) + (500 if fame_level >= 10 else 0)
		medals.append({"season": season_number() - 1, "medal": medal, "name": season_name()})
		Core.book(reward, tr("Medalha de %s na temporada!") % tr(str(m[1])), "missao", true)
		add_fame(PD.XP.medal)
	else:
		Core.toast.emit(tr("Temporada encerrada em %dº lugar. Na próxima dá!") % (pos + 1), "info")
	season_stats = {"earn": 0}

# ================================================================== receitas e fornecedores
func is_discovered(dish: String) -> bool:
	return bool(discovered.get(dish, false))

func try_recipe(ings: Array) -> String:
	# consome 1 de cada insumo escolhido; devolve o prato descoberto ou ""
	for i in ings:
		if int(Core.stock.get(i, 0)) < 1:
			Core.toast.emit(tr("Falta %s no estoque.") % tr(str(Economy.SUPPLIES[i].name)), "bad")
			return ""
	for i in ings:
		Core.stock[i] = int(Core.stock[i]) - 1
	Core.stock_changed.emit()
	var set_a: = ings.duplicate()
	set_a.sort()
	for id in PD.RECIPES:
		var r: Dictionary = PD.RECIPES[id]
		var set_b: Array = r.ings.duplicate()
		set_b.sort()
		if set_a == set_b:
			if r.has("need") and not Core.has(str(r.need)):
				Core.toast.emit(tr("Quase! Essa receita precisa de: %s") % tr(str(Economy.EXPANSIONS[r.need].name)), "info")
				return ""
			if is_discovered(id):
				Core.toast.emit(tr("Essa você já sabe: %s.") % tr(str(Economy.DISHES[id].name)), "info")
				return id
			discovered[id] = true
			add_fame(PD.XP.recipe)
			Core.toast.emit(tr("Receita nova: %s! Já está no cardápio.") % tr(str(Economy.DISHES[id].name)), "good")
			get_tree().call_group("audio", "sfx", "bell")
			recipes_changed.emit()
			Core.market_changed.emit()
			return id
	Core.toast.emit(tr("Não deu liga... tente outra combinação."), "bad")
	return ""

func toggle_menu(dish: String) -> void:
	menu_off[dish] = not bool(menu_off.get(dish, false))
	Core.market_changed.emit()

func toggle_premium(item: String) -> void:
	premium[item] = not bool(premium.get(item, false))
	Core.market_changed.emit()

func premium_share() -> float:
	if premium.is_empty():
		return 0.0
	var n: = 0
	for k in premium:
		if bool(premium[k]):
			n += 1
	return float(n) / float(Economy.SUPPLIES.size())

# ================================================================== capítulos da vila
func chapter_def(id: String) -> Dictionary:
	for c in PD.CHAPTERS:
		if str(c.id) == id:
			return c
	return {}

func chapter_title(id: String) -> String:
	return str(chapter_def(id).get("title", id))

func chapter_step(id: String) -> int:
	return int(chapters.get(id, 0))

func chapter_done(id: String) -> bool:
	return chapter_step(id) >= 3

func chapter_open(id: String) -> bool:
	# abre em sequência: o anterior precisa estar concluído
	for i in PD.CHAPTERS.size():
		if str(PD.CHAPTERS[i].id) == id:
			return i == 0 or chapter_done(str(PD.CHAPTERS[i - 1].id))
	return false

## Passo automático (fama, serve, receitas...) já cumprido?
func step_met(id: String) -> bool:
	var c: = chapter_def(id)
	var k: = chapter_step(id)
	if k >= 3:
		return true
	var s: Dictionary = c.steps[k]
	match str(s.kind):
		"fame":
			return fame_level >= int(s.qty)
		"serve":
			return int(chapters.get(id + "_serve", 0)) >= int(s.qty)
		"sell":
			return int(chapters.get(id + "_sell", 0)) >= int(s.qty)
		"recipes":
			return discovered.size() >= int(s.qty)
		"biz":
			return biz.size() >= int(s.qty)
		"photo":
			return bool(chapter_photo.get(str(s.item), false))
		"deliver":
			return int(Core.stock.get(str(s.item), 0)) >= int(s.qty)
		"pay":
			return Core.money >= int(s.qty)
	return false

func advance_chapter(id: String) -> bool:
	if not chapter_open(id) or chapter_done(id) or not step_met(id):
		return false
	var c: = chapter_def(id)
	var s: Dictionary = c.steps[chapter_step(id)]
	match str(s.kind):
		"deliver":
			Core.stock[str(s.item)] = int(Core.stock[str(s.item)]) - int(s.qty)
			Core.stock_changed.emit()
		"pay":
			Core.book(- int(s.qty), tr("%s: %s") % [tr(str(c.title)), tr(str(s.text))], "missao", true)
	chapters[id] = chapter_step(id) + 1
	if chapter_done(id):
		Core.book(int(c.reward), tr("Capítulo concluído: %s") % tr(str(c.title)), "missao", true)
		Core.toast.emit(tr("Liberado: %s") % tr(str(c.unlock)), "good")
		add_fame(PD.XP.chapter)
		get_tree().call_group("audio", "sfx", "bell")
	chapters_changed.emit()
	Core.save_game()
	return true

# ================================================================== ganchos chamados pelo Core
func on_sale(dish: String, channel: String) -> void:
	add_fame(PD.XP.sale)
	if channel != "bar":
		_goal_add("serve", 1)
		for c in PD.CHAPTERS:
			if chapter_open(str(c.id)) and not chapter_done(str(c.id)):
				var k: = chapter_step(str(c.id))
				var s: Dictionary = c.steps[k]
				if str(s.kind) == "serve":
					chapters[str(c.id) + "_serve"] = int(chapters.get(str(c.id) + "_serve", 0)) + 1
				elif str(s.kind) == "sell" and str(s.item) == dish:
					chapters[str(c.id) + "_sell"] = int(chapters.get(str(c.id) + "_sell", 0)) + 1
	if dish == "petiscos" or Economy.DISHES.get(dish, {}).get("secret", false):
		_goal_add("dish", 1)

func on_income(v: int, cat: String) -> void:
	if v > 0 and cat != "missao":
		season_stats.earn = int(season_stats.get("earn", 0)) + v
		week_stats.earn = int(week_stats.get("earn", 0)) + v
		for g in week_goals:
			if not bool(g.done) and str(g.kind) == "earn" and float(week_stats.earn) >= float(g.target):
				_goal_add("earn", 0)
				break

func on_vip() -> void:
	add_fame(PD.XP.vip)
	_goal_add("vip", 1)

func on_tour(pax: int) -> void:
	add_fame(PD.XP.tour * maxi(1, pax / 2))
	_goal_add("tour", 1)

func on_photo(theme: String) -> void:
	_goal_add("photo", 1)
	if theme != "":
		chapter_photo[theme] = true
		add_fame(PD.XP.photo)

## Ocupação do hotel nesta noite (0..0,98): estrelas, fama, temporada, eventos e melhorias.
func hotel_occupancy() -> float:
	var o: = 0.42 + 0.12 * (Core.stars() - 4.0) + 0.03 * float(fame_level - 7) + (season_demand() - 1.0) * 0.8 + eff("hotel_occupancy")
	if Core.is_party() or Core.day_event == "carnaval":
		o += 0.12
	if Core.day_event == "tempestade":
		o -= 0.15
	return clampf(o, 0.15, 0.98)

func hotel_rate() -> int:
	return PD.HOTEL_RATE + int(eff("hotel_rate"))

func _hotel_night() -> void:
	if not Core.has("grand_hotel"):
		return
	var occ: = hotel_occupancy()
	var n: = int(round(float(PD.HOTEL_ROOMS) * occ))
	var rev: = n * hotel_rate()
	var dining: = int(round(float(n) * 1.7 * float(PD.HOTEL_DINING) * (1.0 + eff("hotel_dining"))))
	Core.book(rev, tr("Grand Hotel: %d suítes ocupadas") % n, "diaria", false)
	Core.book(dining, tr("Grand Hotel: restaurante e bar"), "bar", false)
	Core.book(- PD.HOTEL_STAFF, tr("Grand Hotel: equipe (recepção, cozinha, spa, limpeza)"), "folha", false)
	hotel_last = {"occ": occ, "rooms": n, "rev": rev, "dining": dining, "staff": PD.HOTEL_STAFF}
	# hóspedes de hotel 5★ avaliam a estadia
	for i in mini(6, maxi(1, n / 5)):
		Core.add_rating(randf_range(4.3, 5.0))
	add_fame(n / 2)
	Core.toast.emit(tr("Grand Hotel: %d%% de ocupação, %s na noite") % [int(occ * 100.0), Core.fmt_money(rev + dining - PD.HOTEL_STAFF)], "money")

func on_new_day() -> void:
	_hotel_night()
	_staff_day()
	for id in biz:
		biz[id].today = 0
		var w: = int(PD.BUSINESSES[id].wage)
		Core.book(- w, tr("Operador: %s") % tr(str(PD.BUSINESSES[id].name)), "folha", false)
	# fim de semana de 7 dias: paga a meta de nota, troca as metas e, a cada 7 dias, fecha a temporada
	if (Core.day - 1) % PD.SEASON_DAYS == 0 and Core.day > 1:
		for g in week_goals:
			if not bool(g.done) and str(g.kind) == "rating" and Core.stars() >= float(g.target):
				g.done = true
				Core.book(int(g.reward), tr("Meta da semana: %s") % goal_text(g), "missao", true)
				add_fame(PD.XP.goal)
		_season_end()
		roll_week()
		Core.toast.emit(tr("Começou o %s! Novas metas da semana no celular.") % tr(season_name()), "info")

func tick(dmin: float) -> void:
	_hour_acc += dmin
	if _hour_acc >= 60.0:
		_hour_acc -= 60.0
		_biz_tick()

# ================================================================== save
func to_dict() -> Dictionary:
	return {"fame_xp": fame_xp, "tree": tree.duplicate(), "biz": biz.duplicate(true), "staff": staff_info.duplicate(true),
		"goals": week_goals.duplicate(true), "wstats": week_stats.duplicate(), "sstats": season_stats.duplicate(), "medals": medals.duplicate(true),
		"disc": discovered.duplicate(), "off": menu_off.duplicate(), "prem": premium.duplicate(), "ch": chapters.duplicate(), "chp": chapter_photo.duplicate(), "hotel": hotel_last.duplicate()}

func from_dict(d: Dictionary) -> void:
	reset()
	fame_xp = int(d.get("fame_xp", 0))
	fame_level = 1
	for i in PD.FAME_XP.size():
		if fame_xp >= int(PD.FAME_XP[i]):
			fame_level = i + 1
	tree = d.get("tree", {}) if typeof(d.get("tree")) == TYPE_DICTIONARY else {}
	biz = d.get("biz", {}) if typeof(d.get("biz")) == TYPE_DICTIONARY else {}
	staff_info = d.get("staff", {}) if typeof(d.get("staff")) == TYPE_DICTIONARY else {}
	if typeof(d.get("goals")) == TYPE_ARRAY and not (d.goals as Array).is_empty():
		week_goals = d.goals
	week_stats = d.get("wstats", week_stats) if typeof(d.get("wstats")) == TYPE_DICTIONARY else week_stats
	season_stats = d.get("sstats", season_stats) if typeof(d.get("sstats")) == TYPE_DICTIONARY else season_stats
	medals = d.get("medals", []) if typeof(d.get("medals")) == TYPE_ARRAY else []
	discovered = d.get("disc", {}) if typeof(d.get("disc")) == TYPE_DICTIONARY else {}
	menu_off = d.get("off", {}) if typeof(d.get("off")) == TYPE_DICTIONARY else {}
	premium = d.get("prem", {}) if typeof(d.get("prem")) == TYPE_DICTIONARY else {}
	chapters = d.get("ch", {}) if typeof(d.get("ch")) == TYPE_DICTIONARY else {}
	chapter_photo = d.get("chp", {}) if typeof(d.get("chp")) == TYPE_DICTIONARY else {}
	hotel_last = d.get("hotel", {}) if typeof(d.get("hotel")) == TYPE_DICTIONARY else {}
	fame_changed.emit(fame_level, fame_xp)
	tree_changed.emit()
	goals_changed.emit()
	chapters_changed.emit()
	for id in biz:
		biz_changed.emit(id)
