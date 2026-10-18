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
	"passeios": {
		"name": "Passeios turísticos", "cost": 1800, "req": ["pousada"], "stars": 3.5, "icon": "banho", "area": "",
		"blurb": "Mergulho, barco e trilha ao farol. Com um guia contratado, os passeios rendem sozinhos.",
	},
}
const EXPANSION_ORDER: = ["kiosk_tables", "drinks", "neon", "grill", "bar", "pousada", "pool", "passeios"]
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
	"guia": {
		"name": "Guia de passeios",
		"hire": 280,
		"wage": 45,
		"req": "passeios",
		"blurb": "Conduz os passeios turísticos nos horários marcados. Salário no fim do dia.",
	},
}

## Missões da vila. "giver"/"where" dizem quem e onde; "req" = expansão necessária; "rating" = voto de nota extra ao concluir.
const QUESTS: = {
	"cocos_rita": {
		"title": "Cocos da Dona Rita", 
		"desc": "A barraca compra 4 cocos do seu estoque.", 
		"need": "coco", "qty": 4, "reward": 50, 
		"giver": "Dona Rita", "where": "Barraca, no fim da praia", "req": "", 
	}, 
	"peixe_ze": {
		"title": "Peixe fresco do Seu Zé", 
		"desc": "Seu Zé quer 3 peixes para o almoço. Pesque no fim do píer e entregue.", 
		"need": "peixe", "qty": 3, "reward": 75, 
		"giver": "Seu Zé", "where": "Início do píer", "req": "", 
	}, 
	"paes_padre": {
		"title": "Quermesse da igreja", 
		"desc": "Padre Tomé precisa de 6 pães para a festa de São Pedro.", 
		"need": "pao", "qty": 6, "reward": 90, "rating": 5.0, 
		"giver": "Padre Tomé", "where": "Em frente à igreja", "req": "kiosk_tables", 
	}, 
	"frutas_lourdes": {
		"title": "Geleia da Dona Lourdes", 
		"desc": "A padaria quer 8 frutas para a geleia da casa.", 
		"need": "frutas", "qty": 8, "reward": 85, 
		"giver": "Dona Lourdes", "where": "Padaria e Mercadinho", "req": "drinks", 
	}, 
}

## Clientes famosos do álbum: aparecem como VIP no quiosque. Cada um novo conta para os prêmios do álbum.
const VIPS: = [
	{"id": "marcel", "name": "Chef Marcel", "title": "Chef francês em férias"}, 
	{"id": "luna", "name": "Luna Influencer", "title": "Faz stories de tudo"}, 
	{"id": "brasa", "name": "Capitão Brasa", "title": "Pirata aposentado"}, 
	{"id": "cora", "name": "Dra. Cora", "title": "Bióloga marinha"}, 
	{"id": "djmare", "name": "DJ Maré", "title": "Toca nas festas da praia"}, 
	{"id": "kai", "name": "Kai Onda", "title": "Campeão de surfe"}, 
	{"id": "zefa", "name": "Dona Zefa", "title": "Cem anos, ainda dança forró"}, 
	{"id": "bento", "name": "Mestre Bento", "title": "Capoeirista lendário"}, 
	{"id": "tiao", "name": "Poeta Tião", "title": "Rima com tudo"}, 
	{"id": "valentina", "name": "Valentina Cruz", "title": "Atriz de novela"}, 
	{"id": "mike", "name": "Mike, o turista", "title": "Americano apaixonado por coco"}, 
	{"id": "prefeito", "name": "Sr. Prefeito", "title": "Veio inspecionar o quiosque"}, 
]
## Prêmio (R$) ao chegar a N famosos no álbum.
const ALBUM_REWARDS: = {3: 100, 6: 250, 9: 500, 12: 1000}

## Pesca no fim do píer e cocos caídos na praia (ingredientes grátis, limitados por dia).
const FISH_CASTS_PER_DAY: = 6
const FISH_SECONDS: = 3.2
const COCO_PILE_YIELD: = 2

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
## Preço ajustável por prato (v0.7.5): multiplicadores, demanda de clientes para cada nível e estoque que estraga.
const PRICE_TIERS: = [0.7, 0.85, 1.0, 1.2, 1.5]
const PRICE_DEFAULT_TIER: = 2
const DEMAND_BY_TIER: = [1.25, 1.12, 1.0, 0.85, 0.65]
## Fração do que sobrou no estoque que estraga durante a noite (o freezer corta pela metade).
const SPOIL: = {"gelo": 0.25, "frutas": 0.2, "peixe": 0.4, "pao": 0.3}
const FREEZER_COST: = 300
## Eventos do dia, sorteados ao acordar: sem evento 55%, calor 30%, lua cheia 15%.
const DAY_EVENTS: = {
	"calor": {"name": "Dia de calor", "blurb": "Todo mundo quer coco e suco gelado: mais clientes e pedidos de bebidas frescas."},
	"lua": {"name": "Noite de lua cheia", "blurb": "À noite o bar e o quiosque lotam. Deixe estoque para o fim da tarde."},
	"mare": {"name": "Maré alta", "blurb": "O mar sobe e a praia some: vêm bem menos clientes da areia e os passeios de barco e mergulho são cancelados."},
	"tempestade": {"name": "Tempestade", "blurb": "Chuva forte e vento. Poucos clientes, passeios cancelados e estoque exposto. Faça os preparativos antes."},
	"quermesse": {"name": "Quermesse da praia", "blurb": "Barraquinhas e música: mais clientes e pedidos maiores. Decoração dá ainda mais movimento.", "party": true},
	"junina": {"name": "Festa junina", "blurb": "Fogueira, quadrilha e petiscos. A galera pede mais comida. Decoração atrai ainda mais gente.", "party": true},
	"show_dj": {"name": "Show do DJ Maré", "blurb": "O DJ Maré toca na praia e passa no quiosque. Clientes de sobra e caipirinha em alta.", "party": true},
}
## Probabilidade de cada evento aleatório (o restante do dia fica sem evento).
const EVENT_ODDS: = [["calor", 0.22], ["lua", 0.12], ["mare", 0.10], ["tempestade", 0.08]]
## Festas do calendário (dia % 7), só a partir do dia 8.
const PARTY_CALENDAR: = {2: "quermesse", 4: "junina", 6: "show_dj"}
const PARTY_FROM_DAY: = 8
const PARTY_DECO_COST: = 120
const PARTY_DEMAND: = 1.4
const PARTY_DECO_DEMAND: = 1.7
const STORM_PREP_COST: = 80
## Fração do estoque perdida numa tempestade sem preparativos.
const STORM_LOSS: = 0.35
const EVENT_DEMAND: = {"mare": 0.8, "tempestade": 0.35}
## Fração dos clientes que chegam da praia (normal 0.6).
const BEACH_SHARE: = {"mare": 0.15, "tempestade": 0.3}

## Fornecedores: o preço do mercadinho oscila a cada dia; contrato fixa desconto por alguns dias.
const PRICE_SWING: = [0.8, 0.9, 1.0, 1.0, 1.0, 1.1, 1.25, 1.4]
const CONTRACT_DISCOUNT: = 0.15
const CONTRACT_DAYS: = 5
const CONTRACT_FEE: = 60

## Passeios turísticos: horário (min), preço por pessoa, custo por saída, vagas.
const TOURS: = {
	"snorkel": {"name": "Mergulho com snorkel", "at": 9.5 * 60.0, "price": 45, "cost": 25, "seats": 6, "sea": true},
	"barco": {"name": "Passeio de barco", "at": 13.5 * 60.0, "price": 70, "cost": 45, "seats": 8, "sea": true},
	"farol": {"name": "Trilha ao farol", "at": 16.0 * 60.0, "price": 35, "cost": 10, "seats": 5, "sea": false},
}
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
	"passeio": "Passeios", 
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
