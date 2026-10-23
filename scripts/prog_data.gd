class_name PD
## v1.0 — dados da evolução: fama, árvore de melhorias, negócios, traços da equipe, temporadas, metas, receitas e capítulos da vila.
## Só dados (constantes); a lógica fica em scripts/progression.gd (nó Core.prog).

# ------------------------------------------------------------------ fama
## XP acumulado para cada nível (índice 0 = nível 1). Cada nível dá +4% de movimento.
const FAME_XP: = [0, 100, 250, 450, 700, 1000, 1400, 1900, 2500, 3200]
const FAME_NAMES: = ["Desconhecido", "Falado na vila", "Ponto da praia", "Queridinho da cidade", "Famoso na região",
	"Roteiro turístico", "Destaque na TV", "Destino do verão", "Paraíso famoso", "Lenda da costa"]
## O que cada nível novo libera (texto mostrado no computador e no aviso de subida).
const FAME_PERKS: = {
	2: "Sorveteria disponível nos Negócios",
	3: "Turistas chegam à praia: gorjetas maiores",
	4: "Árvore de melhorias nível 2 · Escolinha de surfe e food truck",
	5: "Famílias: pedidos maiores · Lojinha de souvenires",
	6: "Árvore de melhorias nível 3",
	7: "Celebridades: o dobro de clientes VIP",
	8: "Passeios lotam mais (+2 lugares)",
	9: "Preço premium aceito sem reclamação",
	10: "Lenda da costa: +R$ 500 por temporada vencida",
}
const FAME_DEMAND: = 0.04
## Fontes de fama (XP).
const XP: = {"sale": 2, "vip": 25, "tour": 8, "photo": 15, "goal": 40, "chapter": 80, "five_star": 1, "recipe": 30, "biz_game": 5, "medal": 60}

# ------------------------------------------------------------------ árvore de melhorias
## área -> ramos -> 3 níveis. "need" = expansão exigida; "fame" de cada nível = nível de fama mínimo.
const TREE: = {
	"quiosque": {"name": "Quiosque", "need": "", "branches": {
		"kiosk_speed": {"name": "Entrega ágil", "desc": "Equipe anda 12% mais rápido por nível", "per": 0.12},
		"kiosk_quality": {"name": "Capricho", "desc": "Clientes dão notas melhores (+0,15 ★ por nível)", "per": 0.15},
		"kiosk_patience": {"name": "Fila animada", "desc": "Clientes esperam 15% mais por nível", "per": 0.15},
	}},
	"bar": {"name": "Bar do Coqueiro", "need": "bar", "branches": {
		"bar_markup": {"name": "Drinks premium", "desc": "Bar cobra 6% a mais por nível", "per": 0.06},
		"tips": {"name": "Simpatia", "desc": "+R$ 1 de gorjeta por atendimento rápido, por nível", "per": 1.0},
		"happy_hour": {"name": "Happy hour", "desc": "+4% de movimento por nível", "per": 0.04},
	}},
	"pousada": {"name": "Pousada", "need": "pousada", "branches": {
		"room_rate": {"name": "Conforto", "desc": "+R$ 10 na diária por nível", "per": 10.0},
		"breakfast": {"name": "Café da manhã", "desc": "Hóspedes avaliam melhor (+0,1 ★ por nível)", "per": 0.1},
		"maid_speed": {"name": "Arrumação", "desc": "Camareira 15% mais rápida por nível", "per": 0.15},
	}},
	"hotel": {"name": "Grand Hotel 5★", "need": "grand_hotel", "branches": {
		"hotel_rate": {"name": "Suítes premium", "desc": "+R$ 25 na diária das suítes por nível", "per": 25.0},
		"hotel_occupancy": {"name": "Agências de viagem", "desc": "+6% de ocupação do hotel por nível", "per": 0.06},
		"hotel_dining": {"name": "Chef estrelado", "desc": "Restaurante rende +15% por nível", "per": 0.15},
	}},
	"praia": {"name": "Praia", "need": "", "branches": {
		"beach_demand": {"name": "Guarda-sóis extras", "desc": "+5% de clientes vindos da praia por nível", "per": 0.05},
		"event_bonus": {"name": "Animação", "desc": "Festas e eventos rendem +10% por nível", "per": 0.1},
		"storm_guard": {"name": "Salva-vidas", "desc": "Tempestade estraga 25% menos estoque por nível", "per": 0.25},
	}},
}
const TREE_COST: = [300, 750, 1600]
## Grand Hotel (fase final): 32 suítes, diária base, gasto no restaurante por hóspede e folha diária da equipe do hotel.
const HOTEL_ROOMS: = 32
const HOTEL_RATE: = 220
const HOTEL_DINING: = 35
const HOTEL_STAFF: = 900
const HOTEL_AMENITIES: = ["Lobby e recepção 24h", "32 suítes com varanda", "Restaurante com buffet", "Academia", "Spa", "Piscina com tobogã", "Bar da piscina"]
const TREE_FAME: = [1, 4, 6]

# ------------------------------------------------------------------ negócios
## Renda por hora aberta, salário diário do operador, requisitos (fama, capítulo da vila) e o minijogo do balcão.
const BUSINESSES: = {
	"sorveteria": {"name": "Sorveteria Gelato da Maré", "cost": 900, "fame": 2, "chapter": "", "hour": 18, "wage": 40,
		"open": [9.0, 19.0], "pos": Vector3(47.5, 0.0, -18.5), "rot": 0.4, "tint": Color(1.0, 0.55, 0.7),
		"game": "Montar a casquinha", "blurb": "Vende muito no calor; quase nada na chuva e no inverno."},
	"aluguel": {"name": "Aluguel de pranchas e caiaques", "cost": 1400, "fame": 3, "chapter": "pier", "hour": 22, "wage": 45,
		"open": [8.0, 17.0], "pos": Vector3(67.3, 0.0, -20.0), "rot": 0.0, "tint": Color(0.3, 0.7, 0.95),
		"game": "Encerar a prancha", "blurb": "Fecha com mar bravo. Rende mais com ondas boas (maré alta)."},
	"surfe": {"name": "Escolinha de surfe", "cost": 2200, "fame": 4, "chapter": "prainha", "hour": 32, "wage": 55,
		"open": [7.0, 16.0], "pos": Vector3(-46.0, 0.0, -21.0), "rot": 0.2, "tint": Color(1.0, 0.75, 0.25),
		"game": "Aula na areia", "blurb": "Fica na Prainha do Oeste. Turistas e famílias adoram."},
	"food_truck": {"name": "Food truck do Pastel", "cost": 1800, "fame": 4, "chapter": "sabores", "hour": 26, "wage": 50,
		"open": [11.0, 23.0], "pos": Vector3(27.0, 0.045, 30.85), "rot": 0.0, "tint": Color(0.95, 0.35, 0.25),
		"game": "Fritar o pastel", "blurb": "Na rua principal. Funciona até tarde e bomba nas festas."},
	"souvenir": {"name": "Lojinha de souvenires", "cost": 1600, "fame": 5, "chapter": "carnaval", "hour": 20, "wage": 40,
		"open": [9.0, 20.0], "pos": Vector3(82.8, 0.1, 40.5), "rot": -PI * 0.5, "tint": Color(0.55, 0.85, 0.45),
		"game": "Embrulhar o presente", "blurb": "Na praça. Quanto mais fama, mais turista compra lembrancinha."},
}
const BIZ_LEVEL_MULT: = [1.0, 1.5, 2.1]
const BIZ_UPGRADE_COST: = [0, 800, 1800]

# ------------------------------------------------------------------ equipe
const STAFF_XP: = [0, 60, 150, 280, 450]     # níveis 1..5
const STAFF_TRAITS: = {
	"rapido": {"name": "Rápido", "desc": "Trabalha 20% mais rápido"},
	"simpatico": {"name": "Simpático", "desc": "Clientes dão notas melhores"},
	"economico": {"name": "Econômico", "desc": "Salário 15% menor"},
	"incansavel": {"name": "Incansável", "desc": "Cansa pela metade"},
	"aprendiz": {"name": "Aprendiz", "desc": "Ganha experiência 50% mais rápido"},
}
const STAFF_TRAIN_COST: = 80
const STAFF_FATIGUE: = 12
const STAFF_REST: = 45

# ------------------------------------------------------------------ temporadas
## 7 dias cada, em ciclo. "demand" multiplica o movimento; "odds" pesa os eventos do dia.
const SEASONS: = [
	{"id": "verao", "name": "Verão", "demand": 1.2, "odds": {"calor": 1.8, "tempestade": 0.6}},
	{"id": "outono", "name": "Outono", "demand": 1.0, "odds": {}},
	{"id": "inverno", "name": "Inverno", "demand": 0.8, "odds": {"calor": 0.2, "tempestade": 2.0, "mare": 1.4}},
	{"id": "primavera", "name": "Primavera", "demand": 1.05, "odds": {"lua": 1.5}},
]
const SEASON_DAYS: = 7
## Metas da semana: sorteia 3. "kind" diz o que conta; alvo cresce com a fama.
const GOAL_POOL: = [
	{"kind": "serve", "text": "Atender %d clientes no quiosque", "base": 25, "per_fame": 6, "reward": 120},
	{"kind": "earn", "text": "Faturar %s na semana", "base": 900, "per_fame": 250, "reward": 150, "money": true},
	{"kind": "dish", "text": "Vender %d petiscos ou pratos da cozinha", "base": 8, "per_fame": 2, "reward": 110},
	{"kind": "vip", "text": "Receber %d cliente(s) VIP", "base": 1, "per_fame": 0, "reward": 130},
	{"kind": "tour", "text": "Fazer %d passeios turísticos", "base": 3, "per_fame": 1, "reward": 140, "need": "passeios"},
	{"kind": "biz", "text": "Jogar %d vezes nos balcões dos negócios", "base": 3, "per_fame": 1, "reward": 120, "need_biz": true},
	{"kind": "photo", "text": "Tirar %d fotos (tecla P)", "base": 3, "per_fame": 0, "reward": 80},
	{"kind": "rating", "text": "Terminar a semana com ★ %.1f ou mais", "base": 4.2, "per_fame": 0.0, "reward": 160, "float": true},
]
## Ranking da temporada: quiosques rivais da costa (pontuação = faturamento da temporada).
const RIVALS: = [["Barraca do Juca", 0.7], ["Quiosque Sol & Mar", 0.95], ["Point da Lagoa", 1.15], ["Deck Paraíso", 1.4], ["Beach Club Coral", 1.8]]
const MEDALS: = [["bronze", "Bronze", 100], ["prata", "Prata", 250], ["ouro", "Ouro", 500]]

# ------------------------------------------------------------------ receitas e fornecedores
## Pratos secretos descobertos na Cozinha experimental (combinando insumos). Entram no Economy.DISHES.
const RECIPES: = {
	"tapioca": {"ings": ["tapioca", "queijo"], "hint": "Goma branca e algo que derrete na chapa"},
	"pastel": {"ings": ["camarao", "pao"], "hint": "Massa fininha recheada com fruto do mar"},
	"acai": {"ings": ["acai", "frutas", "gelo"], "hint": "Tigela roxa, gelada, com frutas por cima"},
	"batida": {"ings": ["coco", "cachaca", "gelo"], "hint": "Drink cremoso de praia (precisa da licença de drinks)", "need": "drinks"},
	"moqueca": {"ings": ["peixe", "camarao", "coco"], "hint": "Panela de barro com peixe, camarão e leite de coco"},
}
const PREMIUM_MULT: = 1.6
const PREMIUM_RATING: = 0.25

# ------------------------------------------------------------------ capítulos da vila
## Cada capítulo: morador, história e 3 passos. Tipos de passo: deliver (insumo, qtd), pay (R$), serve (clientes), fame (nível),
## photo (tema), recipes (quantas descobertas), sell (prato, qtd), biz (quantos negócios). "unlock" = o que libera.
const CHAPTERS: = [
	{"id": "pier", "giver": "Seu Zé", "title": "O píer do Seu Zé",
		"story": "O píer está caindo aos pedaços. Seu Zé quer reformá-lo para os barcos e para alugar pranchas.",
		"steps": [{"kind": "deliver", "item": "peixe", "qty": 4, "text": "Levar 4 peixes para o almoço dos pescadores"},
			{"kind": "serve", "qty": 15, "text": "Atender 15 clientes (o povo precisa conhecer o quiosque)"},
			{"kind": "pay", "qty": 150, "text": "Doar R$ 150 para as tábuas novas"}],
		"unlock": "Aluguel de pranchas e caiaques no píer", "reward": 200},
	{"id": "prainha", "giver": "Padre Tomé", "title": "A Prainha do Oeste",
		"story": "Depois das pedras existe uma prainha esquecida. Padre Tomé quer reabrir a trilha para a comunidade.",
		"steps": [{"kind": "fame", "qty": 3, "text": "Chegar à fama \"Ponto da praia\""},
			{"kind": "photo", "item": "farol", "text": "Fotografar o farol (tecla P)"},
			{"kind": "deliver", "item": "coco", "qty": 6, "text": "Levar 6 cocos para o mutirão"}],
		"unlock": "Prainha do Oeste aberta + Escolinha de surfe", "reward": 300},
	{"id": "sabores", "giver": "Dona Lourdes", "title": "Sabores da vila",
		"story": "Dona Lourdes quer resgatar as receitas da avó e levar comida boa até a rua principal.",
		"steps": [{"kind": "recipes", "qty": 2, "text": "Descobrir 2 receitas na Cozinha experimental"},
			{"kind": "sell", "item": "petiscos", "qty": 10, "text": "Vender 10 petiscos"},
			{"kind": "pay", "qty": 250, "text": "Pagar R$ 250 da reforma do food truck"}],
		"unlock": "Food truck do Pastel + dica da moqueca", "reward": 300},
	{"id": "carnaval", "giver": "Sr. Prefeito", "title": "O Carnaval da Maré",
		"story": "O prefeito sonha com um carnaval de praia que traga turistas de longe. Ele conta com você.",
		"steps": [{"kind": "fame", "qty": 5, "text": "Chegar à fama \"Famoso na região\""},
			{"kind": "biz", "qty": 2, "text": "Ter 2 negócios funcionando"},
			{"kind": "pay", "qty": 400, "text": "Pagar R$ 400 da decoração"}],
		"unlock": "Carnaval no fim de cada verão + Lojinha de souvenires", "reward": 500},
]
