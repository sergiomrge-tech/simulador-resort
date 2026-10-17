class_name Economy
## Todos os números da progressão do Maré Alta. Não espalhar preço, diária ou salário pelo código.
##
## Diária de um quarto = BASE_NIGHTLY + round(estrelas * STAR_BONUS) + redes * HAMMOCK_BONUS
##                     + soma dos bônus (rate) dos upgrades daquele quarto.
## Com 3.0 estrelas e sem upgrade: 100 + 36 = 136, a mesma conta de antes.
##
## Caixa do dia 1 (jogador atento, 2 quartos, 1 virada cada, turno parcial no quiosque):
##   2 diárias ~272 + bar ~70 + quiosque ~100 + gorjetas ~30 ≈ R$ 470, além dos R$ 300 iniciais.
## O ventilador (R$ 320) não cabe no saldo inicial; cabe logo depois da primeira diária (~R$ 436).
## Payback de cada nível ≈ custo / aumento de diária, em noites daquele quarto (ver UPGRADES).

const BASE_NIGHTLY := 100
const STAR_BONUS := 12.0
const HAMMOCK_BONUS := 8
const HAMMOCK_PRICE := 150
const HAMMOCK_MAX := 4
const START_MONEY := 300

## Cada nível de upgrade soma isto na nota do check-out (antes do teto de 5).
const COMFORT_PER_TIER := 0.06
## Avaliação registrada quando um pedido não pode ser servido.
const STOCKOUT_RATING := 2.0
## Chuva tira um pouco da nota. O dia começa de sol.
const RAIN_RATING := 0.1

const BUNGALOW_COST := 900
const BUNGALOW_MAX := 4
## Um bangalô novo devolve uma diária cheia (~136). Payback ≈ 900/136 ≈ 7 noites se encher 1x/dia.

const BARTENDER_MARKUP := 0.15
const MAID_MINUTES := 20.0

const STAFF := {
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

const QUESTS := {
	"cocos_rita": {
		"title": "Cocos da Dona Rita",
		"desc": "A barraca compra 4 cocos do seu estoque.",
		"need": "coco",
		"qty": 4,
		"reward": 50,
	},
}

## Custo unitário no mercadinho / padaria.
const SUPPLIES := {
	"coco": {"name": "Coco", "cost": 3},
	"frutas": {"name": "Frutas", "cost": 2},
	"cachaca": {"name": "Cachaça", "cost": 6},
	"gelo": {"name": "Gelo", "cost": 1},
	"peixe": {"name": "Peixe", "cost": 7},
	"pao": {"name": "Pão", "cost": 2},
}

## Despensa de abertura (presente, não entra no caixa). Cobre a primeira estadia e o primeiro turno.
## Valor de compra: coco 18 + frutas 20 + cachaça 36 + gelo 10 + peixe 42 + pão 12 = R$ 138.
const START_STOCK := {
	"coco": 6, "frutas": 10, "cachaca": 6, "gelo": 10, "peixe": 6, "pao": 6,
}

## Venda - custo dos insumos = margem.
##   Coco gelado   12 - 4  = 8   (67%)
##   Caipirinha    22 - 9  = 13  (59%)
##   Petiscos      26 - 11 = 15  (58%)
##   Suco da fruta 14 - 5  = 9   (64%)
const DISHES := {
	"coco_gelado": {"name": "Coco gelado", "price": 12, "uses": {"coco": 1, "gelo": 1}},
	"caipirinha": {"name": "Caipirinha", "price": 22, "uses": {"cachaca": 1, "frutas": 1, "gelo": 1}},
	"petiscos": {"name": "Petiscos", "price": 26, "uses": {"peixe": 1, "pao": 1, "frutas": 1}},
	"suco": {"name": "Suco da fruta", "price": 14, "uses": {"frutas": 2, "gelo": 1}},
}
const KIOSK_MENU := ["coco_gelado", "caipirinha", "petiscos"]
const BAR_MENU := ["coco_gelado", "caipirinha", "petiscos", "suco"]
const PACK := 6

## rate é o bônus TOTAL de diária naquele nível. Payback do degrau ≈ cost / (rate - rate anterior).
##   clima 1  320 / 22 ≈ 15 noites — primeira melhoria, depois do primeiro check-in
##   clima 2  640 / 42 ≈ 15 noites
##   roupa 1  360 / 24 ≈ 15 noites
##   roupa 2  720 / 48 ≈ 15 noites
##   cama 1   480 / 34 ≈ 14 noites
##   cama 2   960 / 64 ≈ 15 noites
##   decor 1  340 / 22 ≈ 15 noites
##   decor 2  680 / 44 ≈ 15 noites
##   banho 1  400 / 28 ≈ 14 noites
##   banho 2  800 / 52 ≈ 15 noites
const UPGRADES := {
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

const CAT_NAME := {
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
	var d := {}
	for k in UPGRADES:
		d[k] = 0
	return d

static func dish(id: String) -> Dictionary:
	return DISHES[id]

static func supply_cost(id: String) -> int:
	return int(SUPPLIES[id].cost)

static func dish_cost(id: String) -> int:
	var n := 0
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
