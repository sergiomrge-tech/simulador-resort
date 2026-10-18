class_name Economy
## Todos os números da progressão do Maré Alta. Não espalhar preço, diária ou salário pelo código.
##
## v0.7 — modo carreira: o jogo começa só com um quiosque simples na praia (coco gelado e suco).
## Cada expansão (EXPANSIONS) é comprada pelo celular e aparece no mundo no lugar de um lote à venda.
## Caixa típico do dia 1: ~18 clientes no quiosque × ~R$ 13 ≈ R$ 230, menos ~R$ 70 de insumos.

const BASE_NIGHTLY: = 100
const STAR_BONUS: = 12.0
const HAMMOCK_BONUS: = 8
const HAMMOCK_PRICE: = 150
const HAMMOCK_MAX: = 4
const START_MONEY: = 150

## Nota que o cliente do quiosque dá: atendido rápido / atendido devagar / foi embora sem ser atendido.
const KIOSK_RATING_FAST: = 4.8
const KIOSK_RATING_SLOW: = 3.6
const KIOSK_RATING_LOST: = 2.0
## Horário do quiosque. O letreiro neon estende o fechamento até 21:00.
const KIOSK_OPEN_H: = 8.0
const KIOSK_CLOSE_H: = 18.0
const KIOSK_CLOSE_NEON_H: = 21.0
## Intervalo entre clientes do quiosque (minutos de jogo). Mesas e guarda-sóis aceleram.
const KIOSK_SPAWN: = Vector2(22.0, 42.0)
const KIOSK_SPAWN_TABLES: = Vector2(14.0, 30.0)
## Atendente do quiosque serve um cliente a cada X minutos de jogo.
const HELPER_MINUTES: = 14.0

## Expansões em ordem de progressão. "req" = ids que precisam estar comprados; "stars" = nota mínima.
## "area" liga a expansão a um pedaço do mundo (world.gd mostra/esconde e põe um lote à venda no lugar).
const EXPANSIONS: = {
	"kiosk_tables": {
		"name": "Mesas e guarda-sóis", "cost": 180, "req": [], "stars": 0.0, "icon": "quiosque",
		"blurb": "+2 lugares no quiosque e clientes chegando mais rápido.",
	},
	"drinks": {
		"name": "Licença de drinks", "cost": 260, "req": [], "stars": 0.0, "icon": "cachaca",
		"blurb": "Libera a caipirinha no cardápio do quiosque.",
	},
	"neon": {
		"name": "Letreiro neon", "cost": 150, "req": ["kiosk_tables"], "stars": 0.0, "icon": "novo",
		"blurb": "O quiosque fica aberto até 21:00, com luzes coloridas.",
	},
	"grill": {
		"name": "Chapa de petiscos", "cost": 380, "req": ["kiosk_tables"], "stars": 3.4, "icon": "peixe",
		"blurb": "Libera os petiscos de peixe (o prato mais caro).",
	},
	"bar": {
		"name": "Bar do Coqueiro", "cost": 1200, "req": ["grill", "drinks"], "stars": 3.6, "icon": "bar", "area": "bar",
		"blurb": "Um bar de praia com barman. Banhistas sentam e pedem drinks sozinhos.",
	},
	"pousada": {
		"name": "Pousada: recepção + bangalô", "cost": 2400, "req": ["bar"], "stars": 3.8, "icon": "bangalo", "area": "pousada",
		"blurb": "Recepção e o primeiro bangalô. Hóspedes pagam diária e dão gorjeta.",
	},
	"pool": {
		"name": "Piscina", "cost": 2000, "req": ["pousada"], "stars": 4.0, "rooms": 2, "icon": "banho", "area": "pool",
		"blurb": "Piscina com espreguiçadeiras. Hóspedes ficam mais felizes (+★).",
	},
}
const EXPANSION_ORDER: = ["kiosk_tables", "drinks", "neon", "grill", "bar", "pousada", "pool"]
## Pratos liberados por expansão (o resto já vem no quiosque inicial).
const DISH_UNLOCK: = {"caipirinha": "drinks", "petiscos": "grill"}
## Bônus de nota da estadia quando a piscina existe.
const POOL_RATING: = 0.2


const COMFORT_PER_TIER: = 0.06

const STOCKOUT_RATING: = 2.0

const RAIN_RATING: = 0.1

const BUNGALOW_COST: = 900
const BUNGALOW_MAX: = 4


const BARTENDER_MARKUP: = 0.15
const MAID_MINUTES: = 20.0

const STAFF: = {
	"atendente": {
		"name": "Atendente do quiosque",
		"hire": 240,
		"wage": 30,
		"req": "kiosk_tables",
		"blurb": "Serve um cliente do quiosque a cada 14 min, mesmo sem você. Salário no fim do dia.",
	},
	"camareira": {
		"name": "Camareira",
		"hire": 220,
		"wage": 36,
		"req": "pousada",
		"blurb": "Limpa um item de bangalô a cada 20 min. Salário no fim do dia.",
	},
	"bartender": {
		"name": "Bartender",
		"hire": 260,
		"wage": 42,
		"req": "bar",
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



## Despensa de abertura do quiosque (presente, não entra no caixa): dá para a manhã do dia 1.
const START_STOCK: = {
	"coco": 12, "frutas": 12, "cachaca": 0, "gelo": 18, "peixe": 0, "pao": 0,
}






const DISHES: = {
	"coco_gelado": {"name": "Coco gelado", "price": 12, "uses": {"coco": 1, "gelo": 1}}, 
	"caipirinha": {"name": "Caipirinha", "price": 22, "uses": {"cachaca": 1, "frutas": 1, "gelo": 1}}, 
	"petiscos": {"name": "Petiscos", "price": 26, "uses": {"peixe": 1, "pao": 1, "frutas": 1}}, 
	"suco": {"name": "Suco da fruta", "price": 14, "uses": {"frutas": 2, "gelo": 1}}, 
}
## Preparo no balcão (v0.7.5): etapas por prato [rótulo, segundos segurando E]. Cada toque em E adianta um pedaço.
const DISH_STAGES: = {
	"coco_gelado": [["Cortar o coco", 1.0]],
	"suco": [["Espremer as frutas", 1.0], ["Misturar com gelo", 0.8]],
	"caipirinha": [["Amassar o limão", 0.8], ["Pôr cachaça e gelo", 0.8], ["Agitar a coqueteleira", 1.0]],
	"petiscos": [["Fritar o peixe", 1.4], ["Montar o prato", 0.9]],
}
const TAP_BURST: = 0.16
const KIOSK_MENU: = ["coco_gelado", "suco", "caipirinha", "petiscos"]
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
