class_name Economy











const BASE_NIGHTLY: = 100
const STAR_BONUS: = 12.0
const HAMMOCK_BONUS: = 8
const HAMMOCK_PRICE: = 150
const HAMMOCK_MAX: = 4
const START_MONEY: = 300


const COMFORT_PER_TIER: = 0.06

const STOCKOUT_RATING: = 2.0

const RAIN_RATING: = 0.1

const BUNGALOW_COST: = 900
const BUNGALOW_MAX: = 4


const BARTENDER_MARKUP: = 0.15
const MAID_MINUTES: = 20.0

const STAFF: = {
	"camareira": {
		"name": "Camareira", 
		"hire": 220, 
		"wage": 36, 
		"blurb": "Limpa um item de bangalô a cada 20 min. Salário no fim do dia.", 
	}, 
	"bartender": {
		"name": "Bartender", 
		"hire": 260, 
		"wage": 42, 
		"blurb": "Os preços do bar sobem 15%. Salário no fim do dia.", 
	}, 
}

const QUESTS: = {
	"cocos_rita": {
		"title": "Cocos da Dona Rita", 
		"desc": "A barraca compra 4 cocos do seu estoque.", 
		"need": "coco", 
		"qty": 4, 
		"reward": 50, 
	}, 
}


const SUPPLIES: = {
	"coco": {"name": "Coco", "cost": 3}, 
	"frutas": {"name": "Frutas", "cost": 2}, 
	"cachaca": {"name": "Cachaça", "cost": 6}, 
	"gelo": {"name": "Gelo", "cost": 1}, 
	"peixe": {"name": "Peixe", "cost": 7}, 
	"pao": {"name": "Pão", "cost": 2}, 
}



const START_STOCK: = {
	"coco": 6, "frutas": 10, "cachaca": 6, "gelo": 10, "peixe": 6, "pao": 6, 
}






const DISHES: = {
	"coco_gelado": {"name": "Coco gelado", "price": 12, "uses": {"coco": 1, "gelo": 1}}, 
	"caipirinha": {"name": "Caipirinha", "price": 22, "uses": {"cachaca": 1, "frutas": 1, "gelo": 1}}, 
	"petiscos": {"name": "Petiscos", "price": 26, "uses": {"peixe": 1, "pao": 1, "frutas": 1}}, 
	"suco": {"name": "Suco da fruta", "price": 14, "uses": {"frutas": 2, "gelo": 1}}, 
}
const KIOSK_MENU: = ["coco_gelado", "caipirinha", "petiscos"]
const BAR_MENU: = ["coco_gelado", "caipirinha", "petiscos", "suco"]
const PACK: = 6












const UPGRADES: = {
	"clima": {
		"name": "Clima", 
		"tiers": [
			{"name": "Janela aberta", "cost": 0, "rate": 0}, 
			{"name": "Ventilador de teto", "cost": 320, "rate": 22}, 
			{"name": "Ar-condicionado", "cost": 640, "rate": 64}, 
		], 
	}, 
	"roupa": {
		"name": "Enxoval", 
		"tiers": [
			{"name": "Lençol simples", "cost": 0, "rate": 0}, 
			{"name": "Algodão colorido", "cost": 360, "rate": 24}, 
			{"name": "Linho da pousada", "cost": 720, "rate": 72}, 
		], 
	}, 
	"cama": {
		"name": "Cama", 
		"tiers": [
			{"name": "Cama de casal", "cost": 0, "rate": 0}, 
			{"name": "Colchão king", "cost": 480, "rate": 34}, 
			{"name": "Cama com dossel", "cost": 960, "rate": 98}, 
		], 
	}, 
	"decor": {
		"name": "Decoração", 
		"tiers": [
			{"name": "Básico", "cost": 0, "rate": 0}, 
			{"name": "Tapete e quadro", "cost": 340, "rate": 22}, 
			{"name": "Lounge e luminária", "cost": 680, "rate": 66}, 
		], 
	}, 
	"banho": {
		"name": "Banheiro", 
		"tiers": [
			{"name": "Chuveiro simples", "cost": 0, "rate": 0}, 
			{"name": "Espelho e toalheiro", "cost": 400, "rate": 28}, 
			{"name": "Banheiro em pedra", "cost": 800, "rate": 80}, 
		], 
	}, 
}

const CAT_NAME: = {
	"diaria": "Diárias", 
	"gorjeta": "Gorjetas", 
	"bar": "Bar", 
	"quiosque": "Quiosque", 
	"insumo": "Insumos", 
	"upgrade": "Melhorias", 
	"compra": "Compras", 
	"folha": "Equipe", 
	"missao": "Missões", 
	"multa": "Multas", 
	"outro": "Outros", 
}


static func blank_upgrades() -> Dictionary:
	var d: = {}
	for k in UPGRADES:
		d[k] = 0
	return d

static func dish(id: String) -> Dictionary:
	return DISHES[id]

static func supply_cost(id: String) -> int:
	return int(SUPPLIES[id].cost)

static func dish_cost(id: String) -> int:
	var n: = 0
	var uses: Dictionary = DISHES[id].uses
	for ing in uses:
		n += int(uses[ing]) * supply_cost(ing)
	return n

static func dish_margin(id: String) -> int:
	return int(DISHES[id].price) - dish_cost(id)

static func tier_name(cat: String, tier: int) -> String:
	return str(UPGRADES[cat].tiers[tier].name)

static func tier_rate(cat: String, tier: int) -> int:
	return int(UPGRADES[cat].tiers[tier].rate)

static func next_cost(cat: String, tier: int) -> int:
	var tiers: Array = UPGRADES[cat].tiers
	if tier + 1 >= tiers.size():
		return -1
	return int(tiers[tier + 1].cost)

static func max_tier(cat: String) -> int:
	return UPGRADES[cat].tiers.size() - 1
