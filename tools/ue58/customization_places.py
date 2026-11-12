"""Generates the non-kiosk places of unreal/MareAlta/Content/Data/customization.json.

The kiosk block and the recipes are hand-tuned in the JSON and kept as they are; every other place
(bar, pool, pousada, tours, the four Grand Hotel areas, the five businesses and the player's home)
is rebuilt from the tables below, together with the "operations" block read by UMareSimulation.

Coordinates are UE centimetres (Godot x, z * 100). Anchors are world.json chunk names; spots are
[x, y, yaw]. A slot with "visual": false is a service upgrade (no furniture to swap).
Run: python tools/ue58/customization_places.py
"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/Content/Data/customization.json'


def part(model, h=None, w=None, at=None, yaw=None):
    p = {'model': model}
    if w is not None:
        p['w'] = w
    if h is not None:
        p['h'] = h
    if at is not None:
        p['at'] = at
    if yaw is not None:
        p['yaw'] = yaw
    return p


def tier(name, desc, *parts, count=None, material=None):
    t = {'name': name, 'desc': desc}
    if parts:
        t['parts'] = list(parts)
    if count:
        t['count'] = count
    if material:
        t['material'] = material
    return t


def slot(id, name, base, comfort, beauty, tiers, **extra):
    assert len(tiers) == 5, id
    s = {'id': id, 'name': name, 'base_price': base, 'comfort': comfort, 'beauty': beauty}
    s.update(extra)
    s['tiers'] = tiers
    return s


def service(id, name, base, comfort, beauty, names, **extra):
    """Five named service levels without furniture (names: list of (name, desc))."""
    return slot(id, name, base, comfort, beauty, [tier(n, d) for n, d in names], visual=False, **extra)


# Chairs of the outdoor_table_chair_set_01 prefab, relative to its table (same in kiosk, bar and hotel).
def chairs(model, h, front=56, back=-50):
    return (part(model, h, at=[-11, front, 0], yaw=180), part(model, h, at=[7, back, 0], yaw=0))


def plants(n_small, n_mid, n_tall, n_box, n_garden):
    return [
        tier('Vasinhos de suculenta', 'Vasos pequenos de suculenta.', part('potted_plant_04', 34), count=n_small),
        tier('Costela-de-adão', 'Folhagens em vasos de barro.', part('potted_plant_02', 70), count=n_mid),
        tier('Palmeirinhas em vaso', 'Plantas altas em vasos de cerâmica.', part('potted_plant_01', 130), count=n_tall),
        tier('Floreiras de madeira', 'Floreiras com gazânias.', part('planter_box_02', 42, 90), part('flower_gazania', 16, 80, at=[0, 0, 36]), count=n_box),
        tier('Jardim tropical', 'Árvore-da-fortuna e folhagens.', part('pachira_aquatica_01', 175), part('potted_plant_02', 70, at=[55, 30, 0], yaw=40), count=n_garden),
    ]


def table_tiers(h=75, orig='Mesa original do conjunto.'):
    return [
        tier('Mesa de madeira do conjunto', orig),
        tier('Mesa redonda de madeira', 'Tampo redondo e pé central.', part('round_wooden_table_01', h, 80)),
        tier('Mesa de bistrô', 'Madeira escura, pé central torneado.', part('round_wooden_table_02', h, 80)),
        tier('Mesa de mármore', 'Tampo de mármore e base cromada.', part('coffee_table_round_01', h, 82)),
        tier('Mesa posta com toalha', 'Toalha e madeira nobre: clima de restaurante.', part('dining_table', h + 1, 95)),
    ]


def chair_tiers():
    return [
        tier('Cadeiras dobráveis', 'As cadeiras do conjunto original.'),
        tier('Cadeira de jardim', 'Madeira clara com encosto curvo.', *chairs('gallinera_chair', 90)),
        tier('Cadeira branca de madeira', 'Encosto alto e assento largo.', *chairs('painted_wooden_chair_01', 92)),
        tier('Cadeira de madeira nobre', 'Madeira escura entalhada à mão.', *chairs('chinese_armchair', 135, 60, -54)),
        tier('Poltrona de couro e madeira', 'Conforto de lounge.', *chairs('modern_arm_chair_01', 82, 64, -58)),
    ]


def lamp_tiers(orig):
    # The original lantern hangs by its handle from the beam 52 cm above the anchor: every tier hangs from
    # that point (top at +40 cm like the old lantern, brass chain up to +52; the pendant brings its own cable).
    chain = part('mare_hang_chain', 12, at=[0, 0, 40])
    return [
        tier(orig, 'A luminária que já estava lá.'),
        tier('Pendente industrial', 'Cúpula de metal e luz quente.', part('hanging_industrial_lamp', 110, at=[0, 0, -58])),
        tier('Lampião de metal', 'Lampião clássico de vidro.', part('Lantern_01', 40, at=[0, 0, 0]), chain),
        tier('Lanterna de latão', 'Latão trabalhado, luz dourada.', part('brass_diya_lantern', 46, at=[0, 0, -6]), chain),
        tier('Lustre de lanternas', 'Conjunto de lanternas penduradas.', part('lantern_chandelier_01', 60, at=[0, 0, -8])),
    ]


def lounger_tiers(orig):
    return [
        tier(orig, 'A espreguiçadeira que veio com a área.'),
        tier('Espreguiçadeira de ripas', 'Madeira tratada com encosto regulável.', part('mare_lounger_slats', 95, 195)),
        tier('Espreguiçadeira com colchonete', 'Colchonete listrado sobre madeira.', part('mare_lounger_cushion', 95, 195)),
        tier('Espreguiçadeira de vime', 'Trama de fibra natural e almofada.', part('mare_lounger_wicker', 92, 198)),
        tier('Daybed com dossel', 'Cama de praia com cortinas de linho.', part('mare_daybed', 230, 210)),
    ]


TOWELS_POOL = ['World_0088', 'World_0090', 'World_0091', 'World_0092', 'World_0093', 'World_0094']
TOWELS_HOTEL = ['World_2443', 'World_2444', 'World_2455', 'World_2456', 'World_2457', 'World_2458',
                'World_2469', 'World_2470', 'World_2471', 'World_2472', 'World_2483', 'World_2484']

BAR = {
    'name': 'Bar do Coqueiro', 'unlock': 'bar', 'area': [500, 1800, -1800, -800],
    'effects': {'income_per_point': 0.045},
    'slots': [
        slot('banquetas', 'Banquetas do balcão', 90, 1, 1, [
            tier('Banqueta estofada redonda', 'As banquetas originais do bar.'),
            tier('Banqueta de ferro', 'Ferro pintado e assento de madeira.', part('metal_stool_01', 78, 42)),
            tier('Banqueta pintada alta', 'Madeira desgastada pelo sal.', part('painted_wooden_stool', 78, 40)),
            tier('Banqueta industrial', 'Assento de madeira, pés de ferro.', part('metal_stool_02', 78, 42)),
            tier('Banqueta de madeira torneada', 'Madeira maciça torneada, acabamento de bar de hotel.', part('wooden_stool_02', 78, 42)),
        ], anchor='World_0327', hide=['World_0327']),
        slot('mesas', 'Mesas', 110, 2, 1, table_tiers(), anchor='World_0333', hide=['World_0333']),
        slot('cadeiras', 'Cadeiras', 90, 2, 1, chair_tiers(), anchor='World_0333', hide=['World_0332', 'World_0334']),
        slot('balcao', 'Balcão', 140, 0, 2, [
            tier('Madeira rústica', 'O balcão original do bar.'),
            tier('Madeira natural', 'Tábuas envernizadas.', material='M_Custom_Counter_2'),
            tier('Madeira azul-turquesa', 'A cor do mar no balcão.', material='M_Custom_Counter_3'),
            tier('Azulejo português', 'Azulejos azuis pintados.', material='M_Custom_Counter_4'),
            tier('Teca polida', 'Acabamento de bar de luxo.', material='M_Custom_Counter_5'),
        ], anchor='World_0318', also=['World_0319', 'World_0320', 'World_0321'], income=0.04),
        slot('iluminacao', 'Iluminação', 70, 0, 2, lamp_tiers('Lanterna de madeira'), anchor='World_0199', hide=['World_0199', 'World_0200', 'World_0201']),
        slot('plantas', 'Plantas', 60, 0, 2, plants(2, 4, 4, 4, 4), spots=[[880, -1720, 0], [1720, -1720, 90], [1720, -880, 180], [880, -880, 270]]),
        service('carta', 'Carta de drinks', 150, 0, 1, [
            ('Caipirinha e cerveja', 'O básico gelado.'),
            ('Drinks de frutas', 'Batidas e caipirinhas de frutas da estação.'),
            ('Coquetéis clássicos', 'Mojito, piña colada e cuba libre.'),
            ('Coquetelaria autoral', 'Drinks da casa com cachaças envelhecidas.'),
            ('Carta de mixologia premium', 'Destilados raros e drinks assinados.'),
        ], income=0.08),
        service('som', 'Som e ambiente', 110, 1, 1, [
            ('Rádio de pilha', 'Música baixinha.'),
            ('Caixa de som', 'Playlist de praia.'),
            ('Voz e violão', 'Música ao vivo no fim de tarde.'),
            ('Trio de forró', 'Música ao vivo todas as noites.'),
            ('DJ ao pôr do sol', 'Set de música eletrônica tropical.'),
        ], income=0.05),
    ],
}

POOL = {
    'name': 'Piscina', 'unlock': 'pool', 'area': [-900, 900, -200, 1000],
    'effects': {'income_per_point': 0.04, 'stay_per_point': 0.003},
    'slots': [
        slot('espreguicadeiras', 'Espreguiçadeiras', 120, 3, 1, lounger_tiers('Espreguiçadeira simples'), anchor='World_0087', hide=['World_0087'] + TOWELS_POOL),
        slot('guarda_sois', 'Guarda-sóis', 80, 1, 2, [
            tier('Lona crua', 'Lona simples, sombra básica.', material='M_Custom_Umbrella_1'),
            tier('Listrado azul', 'Listras azul e branco.', material='M_Custom_Umbrella_2'),
            tier('Listrado coral', 'Listras coral e areia.', material='M_Custom_Umbrella_3'),
            tier('Palha trançada', 'Palha natural, sombra fresca.', material='M_Custom_Umbrella_4'),
            tier('Lona náutica premium', 'Lona marinho de iate.', material='M_Custom_Umbrella_5'),
        ], anchor='World_0100', also=['World_0101', 'World_0110', 'World_0111', 'World_0115']),
        slot('mesinhas', 'Mesinhas de apoio', 60, 1, 1, [
            tier('Mesinha de madeira', 'A mesinha original ao lado da espreguiçadeira.'),
            tier('Mesinha redonda', 'Madeira clara de pé central.', part('small_wooden_table_01', 58, 50)),
            tier('Mesa de jardim baixa', 'Madeira maciça e pés torneados.', part('round_wooden_table_02', 58, 56)),
            tier('Mesinha de jardim', 'Madeira maciça de pés torneados.', part('gallinera_table', 58, 60)),
            tier('Mesa industrial', 'Tampo de madeira de demolição.', part('industrial_coffee_table', 58, 62)),
        ], anchor='World_0139', hide=['World_0139']),
        slot('plantas', 'Plantas', 70, 0, 2, plants(2, 4, 6, 6, 6), spots=[[-880, -190, 45], [880, -190, 135], [-880, 990, 315], [880, 990, 225], [-320, -190, 0], [320, -190, 0]]),
        service('toalhas', 'Toalhas e enxoval', 90, 2, 0, [
            ('Toalha de algodão', 'Toalha simples por pessoa.'),
            ('Toalhas felpudas', 'Toalhas grossas trocadas todo dia.'),
            ('Kit piscina', 'Toalha, chinelo e protetor solar.'),
            ('Roupões de praia', 'Roupão e toalha de banho por hóspede.'),
            ('Concierge de piscina', 'Toalhas geladas e água aromatizada.'),
        ]),
        service('bar_molhado', 'Serviço na piscina', 160, 1, 1, [
            ('Água e refrigerante', 'Isopor na borda.'),
            ('Sucos naturais', 'Garçom passa a cada hora.'),
            ('Petiscos na espreguiçadeira', 'Cardápio de petiscos.'),
            ('Drinks na piscina', 'Garçom dedicado e drinks gelados.'),
            ('Serviço completo de lounge', 'Champanhe, frutas e petiscos finos.'),
        ], income=0.08),
    ],
}

POUSADA = {
    'name': 'Pousada', 'unlock': 'pousada', 'area': [-600, 600, 1200, 2200],
    'effects': {'occupancy_per_comfort': 0.01, 'occupancy_per_beauty': 0.008},
    'slots': [
        slot('recepcao', 'Balcão da recepção', 160, 0, 2, [
            tier('Madeira pintada', 'O balcão original da recepção.'),
            tier('Madeira natural', 'Tábuas envernizadas.', material='M_Custom_Counter_2'),
            tier('Madeira azul-turquesa', 'Cor da praia.', material='M_Custom_Counter_3'),
            tier('Azulejo português', 'Azulejos azuis pintados.', material='M_Custom_Counter_4'),
            tier('Teca polida', 'Recepção de hotel boutique.', material='M_Custom_Counter_5'),
        ], anchor='World_0040', also=['World_0041', 'World_0042', 'World_0043']),
        slot('espera', 'Poltronas da recepção', 140, 2, 1, [
            tier('Cadeira branca de madeira', 'Cadeira simples para quem espera.', part('painted_wooden_chair_01', 92)),
            tier('Cadeira estofada verde', 'Assento acolchoado.', part('GreenChair_01', 100)),
            tier('Poltrona clássica', 'Poltrona de tecido com braços.', part('ArmChair_01', 105)),
            tier('Poltrona de madeira nobre', 'Madeira escura entalhada.', part('chinese_armchair', 135)),
            tier('Poltrona de design', 'Lounge chair de couro e madeira.', part('mid_century_lounge_chair', 100)),
        ], spots=[[-330, 1420, 90], [330, 1420, 270]]),
        slot('banco', 'Banco da entrada', 120, 1, 1, [
            tier('Banco pintado', 'O banco original da entrada.'),
            tier('Sofá de madeira pintada', 'Encosto de ripas e almofadas.', part('painted_wooden_sofa', 89, 170)),
            tier('Sofá de madeira nobre', 'Madeira escura de linhas retas.', part('chinese_sofa', 68, 180)),
            tier('Sofá de linho', 'Estofado claro e macio.', part('Sofa_01', 80, 157)),
            tier('Sofá de veludo', 'Veludo e pés de madeira torneada.', part('sofa_03', 82, 200)),
        ], anchor='World_0073', hide=['World_0073']),
        slot('plantas', 'Plantas', 100, 0, 2, [
            tier('Costela-de-adão', 'Os vasos originais da varanda.'),
            tier('Palmeirinhas em vaso', 'Plantas altas em vasos de cerâmica.', part('potted_plant_01', 130)),
            tier('Árvore-da-fortuna', 'Pachira trançada em vaso.', part('pachira_aquatica_01', 170)),
            tier('Floreiras de madeira', 'Floreiras com gazânias.', part('planter_box_02', 42, 90), part('flower_gazania', 16, 80, at=[0, 0, 36])),
            tier('Jardim tropical', 'Pachira com folhagens.', part('pachira_aquatica_01', 185), part('potted_plant_02', 70, at=[55, 30, 0], yaw=40)),
        ], anchor='World_0048', hide=['World_0047', 'World_0048', 'World_0049']),
        # Room slots: furniture inside every bungalow (actors tagged MareBungalow), local cm, floor at 45.
        slot('clima', 'Clima dos quartos', 220, 2, 0, [
            tier('Janela aberta', 'Brisa do mar e venezianas abertas.'),
            tier('Ventilador de teto', 'Ventilador silencioso de madeira e latão.', part('mare_ceiling_fan', at=[0, 10, 264])),
            tier('Ar-condicionado', 'Split na parede, com controle remoto.', part('mare_ac_unit', at=[0, -184, 262])),
            tier('Ar inverter silencioso', 'Split inverter e ventilador de teto.', part('mare_ac_unit', at=[0, -184, 262]), part('mare_ceiling_fan', at=[0, 10, 264])),
            tier('Climatização inteligente', 'Ar inverter, ventilador e brisa controlada.', part('mare_ac_unit', at=[0, -184, 262]), part('mare_ceiling_fan', at=[0, 10, 264]), part('potted_plant_01', 120, at=[190, 150, 45])),
        ], rate=22, rooms=True),
        service('enxoval', 'Enxoval', 200, 2, 1, [
            ('Lençol simples', 'Algodão básico.'),
            ('Algodão colorido', 'Jogo de cama estampado.'),
            ('Linho da pousada', 'Linho lavado e passado.'),
            ('Percal 400 fios', 'Lençol de hotel e travesseiros de pluma.'),
            ('Enxoval egípcio', 'Algodão egípcio 600 fios e menu de travesseiros.'),
        ], rate=20),
        slot('cama', 'Camas', 260, 3, 0, [
            tier('Cama de madeira', 'Cama de casal com cabeceira de ripas.', part('mare_bed_simple', at=[0, -82, 45])),
            tier('Cama de ferro', 'Cabeceira de ferro branco e colchão de molas.', part('mare_bed_iron', at=[0, -82, 45])),
            tier('Cama queen estofada', 'Cabeceira capitonê e pillow top.', part('mare_bed_upholstered', at=[0, -78, 45])),
            tier('Cama king', 'King com cabeceira de couro em painéis.', part('mare_bed_king', at=[0, -72, 45])),
            tier('Cama com dossel', 'King com dossel de madeira torneada e cortinas de linho.', part('mare_bed_canopy', at=[0, -76, 45])),
        ], rate=30, rooms=True),
        slot('decoracao', 'Decoração dos quartos', 180, 0, 2, [
            tier('Básico', 'Paredes brancas e piso de madeira.'),
            tier('Tapete trançado', 'Tapete de fibra aos pés da cama.', part('mare_rug', at=[0, 80, 45])),
            tier('Artesanato local', 'Tapete e folhagem em vaso de barro.', part('mare_rug', at=[0, 80, 45]), part('potted_plant_02', 70, at=[195, 150, 45])),
            tier('Lounge de leitura', 'Tapete, folhagem e poltrona de leitura.', part('mare_rug', at=[0, 80, 45]), part('potted_plant_02', 70, at=[195, 150, 45]), part('ArmChair_01', 105, at=[165, 60, 45], yaw=-120)),
            tier('Suíte de design', 'Tapete, poltrona de designer e árvore-da-fortuna.', part('mare_rug', at=[0, 80, 45]), part('mid_century_lounge_chair', 100, at=[160, 60, 45], yaw=-120), part('pachira_aquatica_01', 170, at=[200, -120, 45])),
        ], rate=18, rooms=True),
        service('banheiro', 'Banheiros', 240, 2, 1, [
            ('Chuveiro elétrico', 'Água quente simples.'),
            ('Chuveiro a gás', 'Pressão forte.'),
            ('Ducha com amenities', 'Sabonetes e xampus da casa.'),
            ('Banheira', 'Banheira e roupões.'),
            ('Banheiro spa', 'Ducha de chuva, banheira e sais de banho.'),
        ], rate=25),
    ],
}

TOURS = {
    'name': 'Passeios', 'unlock': 'passeios',
    'effects': {'income_per_point': 0.05},
    'slots': [
        service('barco', 'Barco', 260, 2, 1, [
            ('Canoa a remo', 'Cabe pouca gente.'),
            ('Lancha de alumínio', 'Mais rápida e estável (+1 vaga).'),
            ('Escuna de madeira', 'Toldo e bancos acolchoados (+2 vagas).'),
            ('Catamarã', 'Rede de proa e banheiro (+3 vagas).'),
            ('Iate de passeio', 'Deck de sol e cabine (+4 vagas).'),
        ], seats=1),
        service('mergulho', 'Equipamento de mergulho', 180, 1, 0, [
            ('Máscara e snorkel', 'Equipamento básico.'),
            ('Nadadeiras e colete', 'Mais segurança na água.'),
            ('Equipamento novo', 'Máscaras panorâmicas e coletes.'),
            ('Câmera subaquática', 'Fotos do mergulho incluídas.'),
            ('Batismo com cilindro', 'Mergulho de cilindro com instrutor.'),
        ], income=0.08),
        service('roteiro', 'Roteiros', 160, 0, 2, [
            ('Volta na baía', 'O roteiro de sempre.'),
            ('Ilhas e piscinas naturais', 'Parada para banho.'),
            ('Pôr do sol no mar', 'Saída no fim da tarde.'),
            ('Observação de golfinhos', 'Roteiro com guia biólogo.'),
            ('Expedição exclusiva', 'Praias desertas e almoço na ilha.'),
        ], income=0.07),
        service('lanche', 'Lanche a bordo', 120, 2, 0, [
            ('Água mineral', 'Garrafinha gelada.'),
            ('Frutas da estação', 'Bandeja de frutas.'),
            ('Lanche natural', 'Sanduíche e suco.'),
            ('Petiscos e drinks', 'Isopor com drinks e petiscos.'),
            ('Almoço a bordo', 'Peixe grelhado servido no barco.'),
        ], income=0.05),
        service('fotos', 'Fotos e lembranças', 100, 0, 1, [
            ('Sem fotos', 'Cada um tira as suas.'),
            ('Foto impressa', 'Uma foto do grupo.'),
            ('Álbum digital', 'Fotos enviadas no celular.'),
            ('Vídeo com drone', 'Imagens aéreas do passeio.'),
            ('Ensaio profissional', 'Fotógrafo acompanha o passeio.'),
        ], income=0.06),
    ],
}

HOTEL_RESTAURANT = {
    'name': 'Grand Hotel · Restaurante', 'unlock': 'grand_hotel', 'area': [-1500, -600, 3700, 4700],
    'effects': {'income_per_point': 0.04, 'hotel_per_point': 0.002},
    'slots': [
        slot('mesas', 'Mesas do restaurante', 400, 2, 1, table_tiers(orig='Mesa do conjunto do terraço.'), anchor='World_0333', hide=['World_0333']),
        slot('cadeiras', 'Cadeiras do restaurante', 360, 2, 1, chair_tiers(), anchor='World_0333', hide=['World_0332', 'World_0334']),
        service('cardapio', 'Cardápio', 600, 1, 1, [
            ('Buffet de café da manhã', 'Pães, frutas e café.'),
            ('Bufê regional', 'Moqueca, tapioca e cuscuz.'),
            ('À la carte', 'Pratos preparados na hora.'),
            ('Menu degustação', 'Sete tempos com frutos do mar.'),
            ('Chef estrelado', 'Menu sazonal do chef convidado.'),
        ], income=0.1),
        service('adega', 'Adega', 500, 0, 1, [
            ('Vinho da casa', 'Tinto e branco.'),
            ('Rótulos nacionais', 'Vinícolas do Sul.'),
            ('Importados', 'Chile, Argentina e Portugal.'),
            ('Sommelier', 'Harmonização com cada prato.'),
            ('Adega climatizada', 'Rótulos raros e espumantes.'),
        ], income=0.08),
    ],
}

HOTEL_POOL = {
    'name': 'Grand Hotel · Piscina', 'unlock': 'grand_hotel', 'area': [-4405, -1500, 2800, 4700],
    'effects': {'hotel_per_point': 0.0025},
    'slots': [
        slot('espreguicadeiras', 'Espreguiçadeiras', 450, 3, 1, lounger_tiers('Espreguiçadeira do hotel'), anchor='World_0087', hide=['World_0087'] + TOWELS_HOTEL),
        slot('tochas', 'Iluminação da piscina', 380, 0, 2, [
            tier('Tochas tiki', 'Tochas de bambu com chama.'),
            tier('Poste de ferro', 'Poste baixo de ferro fundido.', part('street_lamp_02', 260)),
            tier('Poste clássico', 'Poste de praça com globo.', part('street_lamp_01', 280)),
            tier('Poste com jardineira', 'Poste clássico com suculentas na base.', part('street_lamp_02', 260), part('potted_plant_04', 34, at=[45, 0, 0])),
            tier('Poste com floreira', 'Poste de praça com floreira de gazânias.', part('street_lamp_01', 280), part('planter_box_02', 42, 90, at=[0, 60, 0]), part('flower_gazania', 16, 80, at=[0, 60, 36])),
        ], anchor='World_1272', hide=['World_1272', 'World_1273']),
        slot('tobogã', 'Tobogã', 500, 0, 2, [
            tier('Fibra branca', 'Acabamento de fábrica.'),
            tier('Azul-piscina', 'Fibra azul brilhante.', material='M_Custom_Slide_2'),
            tier('Amarelo-sol', 'Fibra amarela vibrante.', material='M_Custom_Slide_3'),
            tier('Coral', 'Fibra coral com brilho.', material='M_Custom_Slide_4'),
            tier('Arco-íris noturno', 'Tobogã que brilha em cores à noite.', material='M_Custom_Slide_5'),
        ], anchor='World_2402'),
        service('bar_piscina', 'Bar da piscina', 650, 1, 1, [
            ('Sucos e refrigerantes', 'O básico gelado.'),
            ('Coquetéis tropicais', 'Drinks de frutas.'),
            ('Petiscos finos', 'Ceviche e camarão.'),
            ('Bar molhado', 'Banquetas dentro d\'água.'),
            ('Lounge com DJ', 'DJ ao pôr do sol e espumante.'),
        ], income=0.06),
    ],
}

HOTEL_SUITES = {
    'name': 'Grand Hotel · Suítes', 'unlock': 'grand_hotel',
    'effects': {'hotel_per_point': 0.002},
    'slots': [
        # The visitable suite (actor tagged MareSuite) shows the bed tier; head against the slatted west wall.
        slot('camas', 'Camas das suítes', 900, 3, 0, [
            tier('King padrão', 'Cama estofada com cabeceira capitonê.', part('mare_bed_upholstered', at=[-725, -50, 3], yaw=-90)),
            tier('Pillow top', 'King com cabeceira de couro em painéis.', part('mare_bed_king', at=[-718, -50, 3], yaw=-90)),
            tier('Cama ortopédica', 'King com pufe de couro aos pés.', part('mare_bed_king', at=[-718, -50, 3], yaw=-90), part('Ottoman_01', 45, at=[-540, -50, 3])),
            tier('Cama de dossel', 'Dossel de madeira torneada e cortinas de linho.', part('mare_bed_canopy', at=[-720, -50, 3], yaw=-90)),
            tier('Cama sob medida', 'Dossel, pufe e chaise de leitura.', part('mare_bed_canopy', at=[-720, -50, 3], yaw=-90), part('Ottoman_01', 45, at=[-540, -50, 3]), part('mid_century_lounge_chair', 100, at=[-560, -330, 3], yaw=60)),
        ], rate=18, rooms=True, room_tag='MareSuite'),
        service('enxoval', 'Enxoval', 700, 2, 1, [
            ('Percal 200 fios', 'Branco de hotel.'),
            ('Percal 400 fios', 'Mais macio.'),
            ('Algodão egípcio', '600 fios.'),
            ('Linho italiano', 'Lavado à mão.'),
            ('Seda e linho', 'Enxoval de suíte presidencial.'),
        ], rate=14),
        service('banheiro', 'Banheiros', 850, 2, 1, [
            ('Ducha', 'Box de vidro.'),
            ('Ducha de chuva', 'Cabeça larga e amenities.'),
            ('Banheira', 'Banheira e roupões.'),
            ('Ofurô', 'Ofurô de madeira na varanda.'),
            ('Spa privativo', 'Sauna e hidromassagem na suíte.'),
        ], rate=16),
        service('minibar', 'Frigobar', 500, 1, 0, [
            ('Água e refrigerante', 'O essencial.'),
            ('Cervejas locais', 'Cervejas artesanais.'),
            ('Petiscos gourmet', 'Castanhas e chocolates.'),
            ('Espumante', 'Garrafa de cortesia.'),
            ('Adega na suíte', 'Vinhos e destilados selecionados.'),
        ], rate=10),
        service('vista', 'Varandas', 1000, 1, 2, [
            ('Janela', 'Vista para o jardim.'),
            ('Varanda', 'Cadeiras e vista lateral do mar.'),
            ('Varanda com rede', 'Rede e vista do mar.'),
            ('Varanda gourmet', 'Mesa para jantar ao ar livre.'),
            ('Terraço com piscina', 'Piscina de borda infinita privativa.'),
        ], rate=20),
    ],
}

HOTEL_LEISURE = {
    'name': 'Grand Hotel · Lazer', 'unlock': 'grand_hotel',
    'effects': {'hotel_per_point': 0.0025},
    'slots': [
        service('academia', 'Academia', 600, 2, 0, [
            ('Esteira e bicicleta', 'Aparelhos básicos.'),
            ('Musculação', 'Pesos livres e estação.'),
            ('Aparelhos de ponta', 'Esteiras com tela e bicicletas de spinning.'),
            ('Personal trainer', 'Treinos agendados.'),
            ('Centro de bem-estar', 'Pilates, ioga e funcional.'),
        ]),
        service('spa', 'Spa', 800, 3, 1, [
            ('Massagem', 'Uma sala de massagem.'),
            ('Sauna', 'Sauna seca e a vapor.'),
            ('Tratamentos', 'Pedras quentes e argila.'),
            ('Circuito de águas', 'Hidromassagem e piscina fria.'),
            ('Spa completo', 'Terapias exclusivas e ritual de chegada.'),
        ]),
        service('recreacao', 'Recreação', 500, 1, 1, [
            ('Jogos de mesa', 'Dama e baralho.'),
            ('Monitores', 'Atividades de dia.'),
            ('Clube infantil', 'Espaço para crianças.'),
            ('Shows à noite', 'Música e dança.'),
            ('Programação completa', 'Aulas, festas e shows.'),
        ]),
        service('lobby', 'Lobby', 700, 1, 2, [
            ('Recepção padrão', 'Balcão e sofás.'),
            ('Check-in com drink', 'Suco de boas-vindas.'),
            ('Arte local', 'Obras de artistas da vila.'),
            ('Concierge', 'Atendimento personalizado.'),
            ('Lounge executivo', 'Sala vip e transfer.'),
        ]),
    ],
}

# Businesses: furniture-free equipment levels plus plants beside the booth.
BUSINESS_SPOTS = {
    'aluguel': [[6600, -1840, 0], [6860, -1840, 90]],
    'sorveteria': [[4600, -1700, 0], [4900, -1700, 90]],
    'food_truck': [[2480, 3200, 0], [2920, 3200, 90]],
    'souvenir': [[7950, 3880, 0], [8450, 3880, 90]],
    'surfe': [[-4800, -1940, 0], [-4400, -1940, 90]],
}
BUSINESS_GEAR = {
    'aluguel': ('Equipamento', [('Pranchas usadas', 'Pranchas e caiaques de segunda mão.'), ('Pranchas novas', 'Pranchas de epóxi.'), ('Caiaques duplos', 'Caiaques para dois.'), ('Stand up paddle', 'Pranchas de SUP e remos de carbono.'), ('Frota completa', 'SUP, caiaques e pranchas de todos os tamanhos.')]),
    'sorveteria': ('Sabores', [('Três sabores', 'Morango, chocolate e creme.'), ('Frutas tropicais', 'Cupuaçu, açaí e manga.'), ('Picolés artesanais', 'Picolés de fruta de verdade.'), ('Gelato italiano', 'Massa feita na hora.'), ('Gelateria gourmet', 'Sabores autorais e casquinha artesanal.')]),
    'food_truck': ('Cardápio', [('Pastel de queijo', 'O clássico.'), ('Pastéis variados', 'Carne, frango e palmito.'), ('Pastel de camarão', 'Recheio da praia.'), ('Caldo de cana', 'Pastel com caldo gelado.'), ('Pastelaria gourmet', 'Recheios de chef.')]),
    'souvenir': ('Produtos', [('Ímãs e chaveiros', 'Lembrancinhas simples.'), ('Camisetas', 'Estampas da praia.'), ('Artesanato', 'Peças da vila.'), ('Cerâmica pintada', 'Peças assinadas.'), ('Galeria local', 'Arte e joias de artistas da vila.')]),
    'surfe': ('Aulas', [('Aula em grupo', 'Pranchas de espuma.'), ('Aulas com vídeo', 'Correção pela filmagem.'), ('Turmas por nível', 'Iniciante a avançado.'), ('Instrutores certificados', 'Equipe da federação.'), ('Escola completa', 'Aulas, surf trip e campeonato.')]),
}


def business(id, name):
    gear_name, gear = BUSINESS_GEAR[id]
    return {
        'name': name, 'business': id,
        'effects': {'income_per_point': 0.06},
        'slots': [
            service('equipamento', gear_name, 90, 1, 1, gear, income=0.1),
            service('atendimento', 'Atendimento', 70, 2, 0, [
                ('Um vendedor', 'Atende como dá.'),
                ('Uniforme e crachá', 'Equipe identificada.'),
                ('Pagamento por aproximação', 'Fila anda mais rápido.'),
                ('Atendimento bilíngue', 'Turistas estrangeiros compram mais.'),
                ('Clube de fidelidade', 'Clientes voltam toda semana.'),
            ], income=0.06),
            slot('plantas', 'Plantas da fachada', 60, 0, 2, plants(2, 2, 2, 2, 2), spots=BUSINESS_SPOTS[id]),
        ],
    }


HOME = {
    'name': 'Sua casa', 'area': [4250, 4950, 1740, 2480],
    'effects': {'speed_per_comfort': 0.005, 'fame_per_beauty_night': 0.25},
    'slots': [
        slot('cama', 'Cama', 90, 3, 1, [
            tier('Cama de madeira entalhada', 'A cama que era do sua avó Dilce.'),
            tier('Cama de ferro', 'Cabeceira de ferro trabalhado.', part('old_bed_frame', 110, 215)),
            tier('Divã de madeira', 'Cama de solteiro larga com encosto.', part('vintage_day_bed', 95, 205)),
            tier('Cama estofada', 'Cabeceira de linho e colchão novo.', part('mare_bed_upholstered', 120, 215)),
            tier('Cama com dossel', 'Dossel de madeira e cortinas de linho.', part('mare_bed_canopy', 230, 220)),
        ], anchor='World_0252', hide=['World_0252', 'World_0933', 'World_0934']),
        slot('sofa', 'Sofá', 80, 3, 1, [
            tier('Sofá de tecido', 'O sofá antigo da sala.'),
            tier('Sofá de madeira pintada', 'Ripas e almofadas.', part('painted_wooden_sofa', 89, 170)),
            tier('Sofá de madeira nobre', 'Madeira escura de linhas retas.', part('chinese_sofa', 68, 180)),
            tier('Sofá de linho', 'Estofado claro e macio.', part('Sofa_01', 80, 157)),
            tier('Sofá de veludo', 'Veludo e pés torneados.', part('sofa_03', 82, 200)),
        ], anchor='World_1160', hide=['World_1160', 'World_1161']),
        slot('mesa_centro', 'Mesa de centro', 50, 0, 2, [
            tier('Mesa redonda de mármore', 'A mesa de centro original.'),
            tier('Mesa de madeira clara', 'Tampo de ripas.', part('CoffeeTable_01', 32, 90)),
            tier('Mesa de centro moderna', 'Madeira e metal.', part('modern_coffee_table_02', 32, 100)),
            tier('Mesa gótica', 'Madeira entalhada escura.', part('gothic_coffee_table', 32, 100)),
            tier('Mesa industrial', 'Madeira de demolição e ferro.', part('industrial_coffee_table', 34, 80)),
        ], anchor='World_1166', hide=['World_1166']),
        slot('armario', 'Armário', 70, 1, 2, [
            tier('Armário pintado', 'O armário do quarto.'),
            tier('Cômoda pintada', 'Madeira pintada com gavetas.', part('painted_wooden_cabinet', 110)),
            tier('Armário de madeira nobre', 'Portas entalhadas.', part('chinese_cabinet', 160)),
            tier('Cristaleira antiga', 'Madeira e vidro bisotado.', part('vintage_cabinet_01', 180)),
            tier('Armário gótico', 'Madeira escura com ferragens.', part('GothicCabinet_01', 200)),
        ], anchor='World_1168', hide=['World_1168', 'World_1169', 'World_1170']),
        slot('rack', 'Rack da TV', 60, 0, 2, [
            tier('Mesinha de madeira', 'A mesinha onde fica a TV.'),
            tier('Gaveteiro antigo', 'Madeira com puxadores de latão.', part('vintage_wooden_drawer_01', 79, 120)),
            tier('Aparador pintado', 'Madeira pintada com portas.', part('painted_wooden_cabinet', 79, 110)),
            tier('Aparador de madeira nobre', 'Madeira escura entalhada.', part('chinese_console_table', 79, 150)),
            tier('Aparador industrial', 'Madeira de demolição e ferro.', part('industrial_coffee_table', 79, 90)),
        ], anchor='World_1162', hide=['World_1162']),
        slot('mesa_jantar', 'Mesa de jantar', 60, 1, 1, [
            tier('Mesa de madeira', 'A mesa da cozinha.'),
            tier('Mesa pintada', 'Madeira pintada à mão.', part('painted_wooden_table', 55, 110)),
            tier('Mesa redonda', 'Tampo redondo e pé central.', part('round_wooden_table_01', 55, 100)),
            tier('Mesa de jardim', 'Madeira maciça torneada.', part('gallinera_table', 55, 110)),
            tier('Mesa posta', 'Toalha e madeira nobre.', part('dining_table', 56, 120)),
        ], anchor='World_1111', hide=['World_1111', 'World_1112']),
        slot('cadeiras_jantar', 'Cadeiras da cozinha', 45, 2, 0, [
            tier('Banquinhos de madeira', 'Os banquinhos de sempre.'),
            tier('Cadeira azul', 'Madeira pintada à mão.', part('painted_wooden_chair_02', 92, at=[0, -70, 0], yaw=90), part('painted_wooden_chair_02', 92, at=[0, 70, 0], yaw=270)),
            tier('Cadeira branca', 'Madeira pintada de encosto alto.', part('painted_wooden_chair_01', 92, at=[0, -70, 0], yaw=90), part('painted_wooden_chair_01', 92, at=[0, 70, 0], yaw=270)),
            tier('Cadeira estofada', 'Couro e madeira.', part('dining_chair_02', 90, at=[0, -72, 0], yaw=90), part('dining_chair_02', 90, at=[0, 72, 0], yaw=270)),
            tier('Cadeira de jardim', 'Madeira clara com encosto curvo.', part('gallinera_chair', 90, at=[0, -72, 0], yaw=90), part('gallinera_chair', 90, at=[0, 72, 0], yaw=270)),
        ], anchor='World_1111', hide=['World_0218']),
        slot('criado', 'Criado-mudo', 40, 1, 1, [
            tier('Criado pintado', 'O criado-mudo ao lado da cama.'),
            tier('Mesinha de apoio', 'Madeira clara.', part('side_table_01', 58)),
            tier('Criado clássico', 'Madeira escura com gaveta.', part('ClassicNightstand_01', 58)),
            tier('Mesinha de madeira', 'Madeira clara de pés finos.', part('small_wooden_table_01', 58, 60)),
            tier('Criado industrial', 'Madeira de demolição e ferro.', part('industrial_coffee_table', 58, 55)),
        ], anchor='World_0222', hide=['World_0222', 'World_0223']),
        slot('luminaria', 'Luminária', 35, 0, 2, [
            tier('Lamparina antiga', 'A lamparina de vidro pintado.'),
            tier('Lampião de metal', 'Lampião clássico.', part('Lantern_01', 35)),
            tier('Lanterna de latão', 'Luz dourada.', part('brass_diya_lantern', 40)),
            tier('Lanterna de madeira', 'Madeira e vidro.', part('wooden_lantern_01', 42)),
            tier('Luminária articulada', 'Braço de metal para leitura.', part('desk_lamp_arm_01', 48)),
        ], anchor='World_0936', hide=['World_0935', 'World_0936', 'World_0937']),
        slot('poltrona', 'Poltrona da varanda', 55, 2, 1, [
            tier('Cadeira de balanço', 'A cadeira de balanço da avó Dilce.'),
            tier('Cadeira estofada verde', 'Assento acolchoado.', part('GreenChair_01', 100)),
            tier('Poltrona clássica', 'Tecido e braços largos.', part('ArmChair_01', 105)),
            tier('Poltrona de madeira nobre', 'Madeira escura entalhada.', part('chinese_armchair', 135)),
            tier('Poltrona de design', 'Lounge chair de couro.', part('mid_century_lounge_chair', 100)),
        ], anchor='World_0940', hide=['World_0940']),
        slot('quadros', 'Quadros', 30, 0, 2, [
            tier('Molduras simples', 'Os quadros da parede.'),
            tier('Moldura clara', 'Madeira clara.', part('hanging_picture_frame_01', 50)),
            tier('Gravura antiga', 'Moldura escura de época.', part('hanging_picture_frame_03', 55)),
            tier('Moldura dourada', 'Moldura trabalhada.', part('fancy_picture_frame_01', 60)),
            tier('Pintura a óleo', 'Moldura barroca dourada.', part('fancy_picture_frame_02', 70)),
        ], anchor='World_0938', hide=['World_0938']),
        slot('plantas', 'Plantas', 35, 0, 2, [
            tier('Suculentas', 'Os vasinhos da casa.'),
            tier('Costela-de-adão', 'Folhagem em vaso de barro.', part('potted_plant_02', 70)),
            tier('Palmeirinha', 'Planta alta em vaso.', part('potted_plant_01', 120)),
            tier('Antúrio', 'Flores vermelhas em vaso.', part('anthurium_botany_01', 70)),
            tier('Árvore-da-fortuna', 'Pachira trançada.', part('pachira_aquatica_01', 160)),
        ], anchor='World_0738', hide=['World_0735', 'World_0736', 'World_0737', 'World_0738']),
    ],
}

OPERATIONS = {
    'hourly': {
        'bar': {'name': 'Bar do Coqueiro', 'unlock': 'bar', 'open': [10, 22], 'guests': 2, 'spend': 14, 'staff': 'bartender', 'staff_bonus': 0.15},
        'pool': {'name': 'Piscina (day use)', 'unlock': 'pool', 'open': [9, 18], 'guests': 2, 'spend': 10},
    },
    'pousada': {'rooms_base': 1, 'rate_base': 100, 'star_bonus': 12, 'occupancy': 0.45, 'fame_occupancy': 0.03, 'maid': 'camareira', 'maid_bonus': 0.1, 'tip': 0.04},
    'tours': [
        {'id': 'snorkel', 'name': 'Mergulho com snorkel', 'hour': 10, 'price': 45, 'cost': 25, 'seats': 6},
        {'id': 'barco', 'name': 'Passeio de barco', 'hour': 14, 'price': 70, 'cost': 45, 'seats': 8},
        {'id': 'farol', 'name': 'Trilha ao farol', 'hour': 16, 'price': 35, 'cost': 10, 'seats': 5},
    ],
    'tour_guide': 'guia',
    'business_fame': 0.06,
    'business_rain': 0.4,
}


def main():
    cat = json.loads(DATA.read_text(encoding='utf-8'))
    places = {'kiosk': cat['places']['kiosk'], 'bar': BAR, 'pool': POOL, 'pousada': POUSADA, 'passeios': TOURS,
              'hotel_restaurante': HOTEL_RESTAURANT, 'hotel_piscina': HOTEL_POOL, 'hotel_suites': HOTEL_SUITES,
              'hotel_lazer': HOTEL_LEISURE}
    for id, name in [('aluguel', 'Aluguel de pranchas'), ('sorveteria', 'Sorveteria'), ('food_truck', 'Food truck'),
                     ('souvenir', 'Lojinha de souvenires'), ('surfe', 'Escolinha de surfe')]:
        places['biz_' + id] = business(id, name)
    places['home'] = HOME
    cat['places'] = places
    # Operation blocks and fields added in the data by the game code (hotel_stays, pousada reception and guest
    # profiles...) are kept; only the values this generator knows are rewritten.
    ops = cat.get('operations', {})
    for key, values in OPERATIONS.items():
        ops[key] = {**ops.get(key, {}), **values}
    cat['operations'] = ops
    DATA.write_text(json.dumps(cat, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    total = sum(len(p['slots']) for p in places.values())
    print('places', len(places), 'slots', total, 'tiers', total * 5)


if __name__ == '__main__':
    main()
