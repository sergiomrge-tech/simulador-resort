# Maré Alta Resort — Checklist das expansões

04/11/2026. Fonte editável: Claude Doc "Maré Alta Resort — Checklist das expansões" (https://claude.ai/artifact/TGeQ8bPALzs2X7tCLSjivN).

## Como usar

As expansões já têm uma primeira versão no código. O `ROADMAP_STEAM.md` de 02/11 está desatualizado nesse ponto:

- o bar mistura 11 receitas;
- os passeios têm 3 paradas com escolhas;
- os 5 negócios têm um minijogo de 3 rodadas de tempo;
- a piscina tem peneira, toalhas e picolé;
- o restaurante tem mesas, cozinha e serviço de quarto.

O que falta é **profundidade e variedade**. Hoje quase tudo é "aperte E" + barra de tempo ou escolher uma opção. Este checklist transforma cada expansão numa atividade com começo, meio e fim, que dá vontade de repetir.

**Regras para o Claude Code:**

- Branch `codex/ue58-migration` do repositório `sergiomrge-tech/simulador-resort`, projeto em `unreal/MareAlta`.
- Ler antes `CLAUDE.md` e `AGENTS.md`. Valores ficam em `Content/Data/*.json` (bar, tours, business_games, pool, restaurant, leisure, events, game_room); a lógica fica em `MareSimulation` (`MareBar.cpp`, `MareTours.cpp` etc.) e o mundo em `Mare*World.cpp`.
- Antes de cada commit: `python tools/ue58/qa/qa_gate.py` = PASS. Todo item novo ganha um teste automático ou uma checagem no `MarePreviewQA`, e fotos de prova em `docs/ue58/graphics-reference/`.
- Textos novos em PT-BR e depois `python tools/ue58/i18n_extract.py`. Interface no padrão `MareNotebookStyle.h`.
- Nada de low poly ou primitivas: props reais ou modelados no Blender.
- Um item por vez, na ordem do documento. Marcar `[x]` neste arquivo só com teste e foto.

## 1. Bar do Coqueiro

**Hoje:** 13 ingredientes e 11 receitas (`bar.json`). O drink é o conjunto exato de ingredientes. Descobrir uma receita dá +6 de fama, e o barman atende sozinho com 85% da renda. Pedidos: receita conhecida, "surpresa" ou desconhecida com dica.

**Objetivo:** misturar um drink tem que ser gostoso de fazer com as mãos, como no Barfender.

### 1.1 Preparo físico (prioridade)

- [x] Prateleira de garrafas e caixas de frutas no balcão. Mirar e apertar E pega o ingrediente, que aparece na mão e cai no copo com som.
- [x] O copo na bancada mostra as camadas: gelo, fruta, cachaça e espuma, cada uma visível.
- [x] Passos com mini-ação: **socar** (amassador, toques no ritmo), **bater** na coqueteleira (segurar até a barra encher, sem passar) e **liquidificar** (batidas).
- [x] Ingrediente errado: botão "jogar fora" perde o custo e toca uma reação engraçada do cliente.
- [x] Teste: cada receita feita passo a passo dá o drink certo; uma ordem diferente dá o mesmo drink; errar não cobra o cliente.

Decisões (04/11/2026):
- **Sem mãos** (Sergio): o herói não mostra mãos nem braços em todo o jogo. No bar, E no ingrediente o joga direto no copo, num arco da prateleira até o copo, com som; nada aparece "na mão".
- Bancada de preparo `BarPrep_bench` encostada no painel de fundo (face em x = 1510), com 13 ingredientes e as 3 ferramentas; todos modelados em `tools/ue58/gen_bar_prep.py`, exceto o limão do Poly Haven. Posições em `bar.json` (`bench`, `shelf`, `glass`).
- Copo de trabalho 1,5× um copo alto, para as camadas serem legíveis do balcão. Líquido translúcido (`M_BarDrink`, cor média dos líquidos; liquidificado mistura a fruta) e fruta opaca (`M_BarFruit`). A espuma aparece depois de bater ou liquidificar.
- Passos por mistura: "socar" quando há limão, morango, maracujá ou hortelã; depois "liquidificar" quando há coco, leite condensado ou abacaxi, senão "bater". A nota média das mini-ações muda o preço em ±10% (`prep_tip`).
- O estoque sai ao pôr no copo. Errar (mistura sem receita ou outra receita) não cobra o cliente e esvazia o copo. "Jogar fora" fica na página do balcão, com reação do cliente que está sendo atendido (`discard_reactions`).
- O cliente a atender é escolhido na página do balcão (`bar.serving`); sem escolha, vai o que espera há mais tempo.
- Correção encontrada: `Object()` cria o campo ao ler, então um bar recém-comprado podia começar com a prateleira vazia; `Bar()` trata `{}` como não inicializado (teste `BarPrep`).
- Prova: `MareAlta.Gameplay.BarPrep` + fotos em `docs/ue58/graphics-reference/bar_prep_*.jpg`.

### 1.2 Clientes e pedidos

- [x] Banqueta com o cliente pedindo em balão: nome do drink, "surpresa" ou dica ("algo doce, com coco").
- [x] Perfil de gosto por cliente (doce/forte/azedo). A "surpresa" ganha nota de 1 a 3 estrelas pelo perfil.
- [x] **Happy hour** das 17h às 19h, com mais clientes e trilha mais animada. No dia de "Lua cheia", o bar lota à noite.
- [x] Cliente fiel que volta e pede "o de sempre".

Decisões (04/11/2026):
- Balões em Slate no estilo do caderno (`SMareBubbles`), projetados 58 cm acima do cliente sentado; somem com celular, pausa, menu, a mais de 14 m ou atrás de parede. O texto vem de `MareSimulation::BarBubble` e é o mesmo da página do balcão.
- Cada receita tem `taste` {doce, forte, azedo} de 0 a 1 em `bar.json`; estrelas = 1 + arredondar(2 × nota do gosto); o preço da surpresa varia ×0,9 / ×1 / ×1,15 (`stars_price`).
- Rush (`IsBarRush`): happy hour [17, 19) e noite de lua cheia (evento `lua` a partir das 19h). Chegadas ×2 e até 6 banquetas (`max_orders_rush`). Trilha: zona `bar_happy` (Aloha FM · onda alegre) em `audio_zones.json`.
- Fiel: quem recebe o drink certo em até 20 min vira freguês (até 8, `bar.regulars`) e volta com 30% de chance pedindo "o de sempre", que é o drink daquela vez. A página do balcão lista os fiéis e o que bebem; acertar dá +15% e +1 de fama.
- Prova: teste `MareAlta.Gameplay.BarGuests` + `docs/ue58/graphics-reference/bar_guests_bubbles.jpg`.

### 1.3 Caderno de receitas (app do celular)

- [x] Receitas conhecidas com ingredientes. As desconhecidas aparecem como "???" com uma dica.
- [x] Receita secreta "Drink do Coqueiro" só por missão ou cliente VIP.
- [x] Conquista: descobrir todas.

Decisões (04/11/2026):
- Aba nova "Drinks" no celular, só depois de comprar o bar (8 abas cabem na tela; LB/RB percorrem todas). Para as conhecidas: nome, preço, ingredientes e passos do preparo; para as desconhecidas: "???" com a dica.
- O "Drink do Coqueiro" é `secret`: misturar não faz nada até um VIP contar. O VIP ("Comodoro Vasco") aparece a partir da fama 4, com 12% de chance por chegada e um por vez. Pede surpresa no balão "VIP · ... conto um segredo" e, bem servido, cochicha a receita, que entra no caderno. Saves que já tinham descoberto o drink continuam com ele.
- A conquista "Mestre dos drinks" fica em `prog.achievements.mestre_drinks` e vale +10 de fama. Ligar à conquista da Steam na seção 7.
- Prova: `BarGuests` (VIP, segredo, conquista) + `BarPrep` (segredo fechado) + `docs/ue58/graphics-reference/bar_recipe_book.jpg`.

### 1.4 Evolução

- [x] Melhorias (5 níveis, padrão de personalização): liquidificador, freezer de gelo, banquetas extras, letreiro neon e chopeira.
- [x] Gelo acaba e derrete mais rápido no "Dia de calor".
- [x] Barman com nível: só faz as receitas que ele já aprendeu, erra às vezes no nível 1 e aprende com o tempo de casa.

Decisões (04/11/2026):
- As melhorias ficam em `bar.json` (`upgrades`), com 5 níveis e preço por nível, compradas na página do balcão ("Melhorias do bar"). Do nível 1 em diante aparecem os modelos: neon no painel, chopeira no balcão lateral e freezer na prateleira de baixo da bancada (`gen_bar_prep.py`). Efeitos:
  - **liquidificador:** zona do pulso +3% por nível e +3% no preço do batido;
  - **freezer:** +4 gelos na reposição e −18% de derretimento por nível;
  - **banquetas:** +1/+2 lugares, limitados pelas 6 banquetas, e +15% de paciência por nível;
  - **neon:** +15% de chegadas por nível a partir das 18h;
  - **chopeira:** libera o chope e +10% no preço por nível.
- **Chope:** é ingrediente só de torneira (`pour_only`): E na chopeira põe no copo, sem mini-ação, e serve na hora.
- **Gelo:** derrete 0,5 por hora com o bar aberto, ×4 no dia de "calor".
- **Barman:** sabe o cardápio inicial e aprende uma receita que o jogador já descobriu a cada 2 dias. A chance de errar vai de 15% no nível 1 a 0% no nível 5; quando erra, o cliente vai embora sem pagar.
- **Correção encontrada:** os materiais importados estavam sem a flag Nanite e virariam o material padrão no executável; `mare_bar_prep.fix_usage` corrigiu os 106. O neon ganhou material emissivo próprio (`M_BarNeonPink/Cyan`). Os modelos vindos do Blender olham para +Y na UE, e os giros estão anotados no `bar.json`.
- **Prova:** teste `MareAlta.Gameplay.BarUpgrades` + `docs/ue58/graphics-reference/bar_upgrades.jpg`.

## 2. Passeios (snorkel, barco, trilha do farol)

**Hoje:** bilheteria no píer com fila e 3 passeios (`tours.json` + `customization.json`). O guia é feito por diálogo: 3 paradas, cada uma com escolha boa, ok ou ruim, e a nota sai disso. Mar bravo cancela.

**Objetivo:** o jogador **vai junto** no passeio, em vez de só escolher texto.

### 2.1 Bilheteria

- [x] Turistas na fila com pedido no balão ("2 adultos e 1 criança"). O jogador vende e oferece extras: colete, foto do passeio e lanche (+renda, +nota).
- [x] Lotação visível (assentos do barco) e lista de espera.
- [x] Mar bravo: escolher entre devolver o dinheiro ou remarcar para amanhã (afeta a nota).

Decisões (04/11/2026):
- A fila virou uma lista de grupos (`tours.groups`): adultos, crianças e um traço ("chegamos com fome", "é nossa primeira vez!", "queremos sossego"). Cada grupo tem uma figura no píer com balão, e a página da bilheteria mostra o primeiro da fila.
- **Extras** (`tours.json` "extras"): o colete agrada quando há criança, o lanche quem chegou com fome e a foto quem vem pela primeira vez. O extra desejado é pago (por pessoa ou por grupo) e soma nota; oferecer o que não querem é recusado e tira 0,15 ("insistiu demais"). A média dos extras entra na nota do passeio, guiado pelo jogador ou pelo guia. O guia vende sem oferecer extras.
- **Lugares:** "x de y ocupados · z livres". O grupo que não cabe vai para a lista de espera e volta primeiro na fila do dia seguinte.
- **Mar bravo com bilhete vendido:** o passeio fica pendente até o jogador escolher. Devolver vale nota 3; remarcar vale nota 4, e 70% das pessoas mantêm a reserva paga para amanhã. Sem decisão até o fim da hora de saída, o dinheiro é devolvido.
- **Correção encontrada:** os grupos de um passeio que já saiu ficavam na fila e nos balões; agora são limpos.
- **Prova:** teste `MareAlta.Gameplay.TourBooth` (e `ToursHandsOn` segue passando) + `docs/ue58/graphics-reference/tours_booth.jpg`.

### 2.2 Passeio de barco (jogável)

- [x] O jogador pilota um barco simples (acelera e vira) por boias até 3 pontos de parada; turistas sentados no barco.
- [x] Em cada parada, a escolha atual vira **ação**: distribuir coletes (E em cada turista), apontar a câmera para a atração e contar a história.
- [x] Chance de ver a **baleia** ou os golfinhos, que já existem no jogo: o turista vibra e a nota sobe.
- [x] Ondas fortes balançam o barco; acelerar demais deixa turista enjoado (reação cômica, nota menor).

Decisões (05/11/2026):
- **Lancha de passeio:** 8 m, modelada em `tools/ue58/gen_tour_boat.py`, sem gratuita comercial que sirva. Tem bancos para 8, toldo, console baixo para o piloto enxergar e motor de popa. No mesmo gerador estão as boias de rota (vermelha e branca), as de parada (amarela com bandeira) e o golfinho. O colete é o `life_vest` do projeto, renomeado (`tourboat_vest_rename.py`).
- **Pilotagem:** na hora da saída, a bilheteria mostra "Pilotar o passeio agora". W/S acelera, A/D vira, e o analógico esquerdo também funciona. O herói fica no leme sem andar nem nadar, e os passageiros vão presos ao barco. Raso, areia e píer param o barco ("Raso! Cuidado com o casco").
- **Rota** (`tours.json` "boat_tour"): coletes na saída do píer, golfinhos ao sudoeste, praia deserta a oeste (x ≈ −10 000) e volta ao píer. A baleia saiu do jogo em 04/11 por decisão do Sergio, então ficam só os golfinhos, que aparecem com 75% de chance, saltam ao redor do ponto e valem +0,5.
- **Escolhas:** cada parada vale boa, ok ou ruim, como no passeio por diálogo. Todos os coletes = boa; metade = ok. Golfinhos com o motor parado e olhando para eles por 4 s = boa; acelerar para cima deles = ruim. Mirar a praia e apertar E = boa.
- **Enjoo:** acelerar acima de 85% por 6 s deixa um passageiro enjoado ("Ai... meu estômago..."), com −0,3 cada, no máximo −1.
- **Nota:** usa `GuideTour(..., Bonus)`.
- **Mar:** o barco e as boias seguem a superfície real do mar. `AMarePerson::SeaHeight` estava na fórmula antiga, sem o swell de 85 cm, e foi atualizada, o que vale também para os nadadores. Para não aparecer água dentro do casco, o material do mar achata a superfície sob a lancha (MPC `BoatX/BoatY/BoatYaw/BoatH/BoatOn`).
- **Correções encontradas no caminho:**
  - o `ToursHour` encerrava o passeio pilotado ao fim da hora de saída; agora o passeio a bordo (`tours.active`) só termina no píer;
  - o ajuste de assento das pessoas brigava com o barco em movimento; agora os passageiros são reposicionados rigidamente a cada quadro, e o cabelo é teletransportado junto com a física.
- **Prova:** testes `TourBooth` (nota com bônus e penalidade) e `ToursHandsOn` + `docs/ue58/graphics-reference/tours_boat_playable.jpg`.

### 2.3 Snorkel guiado

- [x] O grupo nada seguindo o jogador (usar a natação existente).
- [x] Mostrar peixes e coral: olhar para a espécie e apertar E "apresenta" ao grupo. Cada espécie nova vale nota, e encostar no coral tira nota.
- [x] Contagem do grupo antes de voltar; turista perdido tem que ser buscado.

Decisões (05/11/2026):
- **Onde:** o recife da UE fica ao largo (y ≈ −13 300, a ~9 m de fundo), não no raso perto do píer como no Godot. A lancha ancora junto dele (`tours.json` "snorkel_tour"), e na bilheteria aparece "Guiar o mergulho agora" na hora da saída. O herói pula na água, e o grupo (um nadador por bilhete, até 6) sai pela escada.
- **Mar calmo no recife:** em mar aberto as ondas chegavam a ±2 m e passavam por cima da cabeça de quem nada (a água do nado é plana). Em volta do recife o swell cai para 8%, como num lugar abrigado, no material do mar e em `AMarePerson::SeaHeight`, os dois juntos.
- **Grupo:** turistas MetaHuman em roupa de banho, boiando (`TreadWater`) com máscara e snorkel (`TourBoat_snorkel`, modelado em `gen_tour_boat.py`). Eles nadam em duplas atrás do guia, sem entrar no casco nem em água rasa.
- **Espécies (12):**
  - peixes do recife: palhaço, cirurgião-azul, sargentinho (segunda parada) e sardinhas;
  - corais: cérebro, leque-do-mar, mesa e galhado;
  - vida do fundo: tubarão-galha-preta, anêmona, ouriço e estrela-do-mar.

  Para apresentar, é preciso mergulhar (Ctrl), mirar e apertar E (alvo com o prompt de sempre). Cada espécie nova dá +0,12 de nota.
- **Coral:** encostar o corpo nele dá −0,25 (no máximo uma vez a cada 4 s) e um turista reclama.
- **Turista perdido:** depois de 2 espécies, ou de 70 s, um turista se afasta 11,5 m. O HUD mostra a distância e a direção, e ele aparece num balão. Basta nadar até ele. Na escada é feita a contagem ("Contagem: 4 de 5"). Se o turista continuar perdido 45 s, o marinheiro vai buscá-lo e a escolha fica ruim.
- **Nota:** `SnorkelScore` calcula as três escolhas (coral, espécies e contagem) e o bônus, e o resultado vai para `GuideTour`.
- **Pedido do Sergio no meio do item: rochas, algas, vida marinha e tubarões no fundo** (`Content/Data/reef.json`, `MareReefWorld::Dress`):
  - rochas Poly Haven (CC0) que já estavam no projeto;
  - algas, ervas marinhas, esponjas, anêmonas, ouriços, estrelas e tubarões, modelados em `tools/ue58/gen_seafloor.py`. Não havia gratuito comercial com qualidade: o tubarão CC0 da Quaternius é low poly;
  - tudo em HISM, uma por malha, com corte a 65 m, e só onde a esfera chega à areia, sem coral embaixo;
  - as algas e o rabo do tubarão balançam no material (WPO, na GPU);
  - três tubarões rodeiam os aglomerados e se afastam de quem chega perto.
- **Prova:**
  - teste `TourBooth` (escolhas e nota do snorkel);
  - check `reef_seafloor_dressed` no `MarePreviewQA`;
  - fotos `docs/ue58/graphics-reference/tours_snorkel.jpg` e `reef_seafloor.jpg`.

### 2.4 Trilha do farol (421 m, já existe)

- [ ] O grupo segue o jogador. Se ele andar rápido demais, alguém fica para trás e reclama.
- [ ] Paradas de foto nos mirantes (ligar ao modo foto). Água e protetor solar no início.
- [ ] Pôr do sol no farol com bônus de nota se chegar na hora.

### 2.5 Resultado e evolução

- [ ] Tela final com estrelas, gorjetas e avaliações escritas no app do celular. Uma nota alta aumenta a fila de amanhã.
- [ ] Melhorias: lancha, equipamento de snorkel novo, fotógrafo que vende fotos e passeio novo (pôr do sol na jangada ou ilha vulcânica, só olhando de longe).
- [ ] O guia contratado faz o passeio sozinho com nota média 3; ir junto rende mais.

## 3. Negócios da vila

**Hoje:** 5 negócios (`business_games.json`). Todos usam o **mesmo** minijogo: 3 rodadas de barra de tempo com recompensa de 0,3× a 2,2× e +2 de fama por acerto. Só muda o texto ("Bola de baunilha!", "Fritar o pastel").

**Objetivo:** cada negócio com uma mecânica própria, curta (30–90 s), que fica mais difícil e rende mais com o nível.

### 3.1 Sorveteria — montar a casquinha

- [ ] O cliente pede uma combinação ("2 bolas: coco + açaí, calda de chocolate"), mostrada por 3 s.
- [ ] O jogador monta de memória com os sabores no freezer; a bola cresce enquanto ele segura o botão (pequena, certa ou derramando).
- [ ] Picolé compartilhado com a piscina: a sorveteria abastece o cooler.
- [ ] Dia de calor: o dobro de clientes, com uma fila que cresce.

### 3.2 Food truck do pastel — montar e fritar

- [ ] Escolher o recheio pedido (carne, queijo, pizza, camarão), fechar a massa (arrastar para selar a borda) e mergulhar no óleo.
- [ ] Fritura em tempo real: cru → dourado → queimado, com o ponto certo indicado pelo som e pela cor.
- [ ] Caldo de cana na moenda como pedido extra (girar a manivela).

### 3.3 Aluguel de pranchas e caiaques

- [ ] Alugar com tempo (30/60 min de jogo). O cliente volta e o jogador confere a prancha: amassada cobra multa.
- [ ] Encerar a prancha com movimentos circulares (mouse/analógico) antes de alugar: a cera aumenta a gorjeta.
- [ ] Evento: caiaque à deriva no mar, que o jogador busca nadando ou de caiaque (física simples).

### 3.4 Escolinha de surfe

- [ ] Aula na areia: o aluno copia a pose que o jogador escolhe na ordem certa (remada, pop-up, base).
- [ ] Aula na água: empurrar o aluno na onda na hora certa. Ele fica em pé ou leva caldo, com animação cômica.
- [ ] O jogador pode surfar sozinho (minijogo de equilíbrio na onda) e liberar "aula avançada".

### 3.5 Lojinha de souvenires

- [ ] Comprar artesanato dos moradores da vila (ligar aos capítulos da vila) e arrumar a prateleira: a posição na vitrine afeta a venda.
- [ ] Embrulhar o presente: dobrar o papel em 3 cliques na ordem certa e escolher a fita na cor pedida.
- [ ] Vender cartões-postais feitos com as fotos do modo foto do jogador.

### 3.6 Comum a todos

- [ ] Nível 1 a 3 por negócio, cada um com a mecânica mais exigente e o preço maior.
- [ ] Funcionário que automatiza com 60% da renda; fazer pessoalmente rende 100% + fama.
- [ ] Relatório diário de cada negócio no app do celular.
- [ ] Teste por negócio: acerto perfeito, médio e erro dão a recompensa esperada e são salvos.

## 4. Piscina e day use

**Hoje:** folhas caem toda hora e a peneira tira com E. Toalhas usadas ficam nas espreguiçadeiras e o picolé é vendido no cooler (`pool.json`). Sujeira e toalhas derrubam a renda e as estrelas.

**Objetivo:** a piscina vira um lugar para cuidar e animar, não só limpar.

- [ ] **Peneira de verdade:** a rede segue a câmera e as folhas boiam e se movem com o vento. É preciso passar a rede por cima delas, em vez de um único E.
- [ ] **Química da água:** um kit de teste uma vez por dia (cor da amostra) e a escolha de cloro ou correção de pH. A água turva aos poucos, de forma visível.
- [ ] **Espreguiçadeiras:** o hóspede "marca" o lugar com a toalha e sai (evento cômico). O jogador decide liberar ou não.
- [ ] **Salva-vidas:** uma criança sem boia ou alguém passando mal. O jogador ou o salva-vidas contratado age a tempo.
- [ ] **Aluguel de boias** (flamingo, rosquinha), com renda e devolução.
- [ ] **Tobogã:** fila e um sinal para liberar a descida quando a saída está livre. Liberar cedo demais causa trombada cômica e reclamação.
- [ ] **Festa na piscina** à noite (evento pago na véspera): luzes, DJ e drinks do bar com mais demanda.
- [ ] Picolé abastecido pela sorveteria (ver 3.1). Sem estoque, o cliente reclama.
- [ ] Melhorias: hidromassagem, bar molhado, guarda-sóis e cascata.

## 5. Grand Hotel e salão de jogos

**Hoje:**

- Restaurante: anotar na mesa, pegar no passe da cozinha, servir; serviço de quarto pelo elevador; eventos reservados na véspera (`restaurant.json`).
- Recepção com VIPs.
- Sinuca com física, IA e aposta; pingue-pongue; pebolim com barra de tempo; 2 fliperamas decorativos.
- A torre é só casca: os quartos não têm interior, e o salão de jogos está vazio visualmente (paredes brancas lisas).

### 5.1 Quartos (maior lacuna visual)

- [ ] 3 tipos de quarto visitáveis (standard, luxo e suíte) com interior modelado. Um andar real basta, e os outros repetem o mesmo modelo.
- [ ] Arrumação como na pousada: cama, toalhas, frigobar e lixo. A camareira automatiza.
- [ ] Frigobar: repor e cobrar no check-out.
- [ ] Reclamação pelo telefone do celular ("ar-condicionado quebrado", "barulho"), com tempo para resolver.

### 5.2 VIPs e eventos

- [ ] Pedido especial de cada VIP (pétalas na cama, champanhe, quarto com vista). Acertar dá muita fama.
- [ ] Eventos com montagem: casamento na praia, aniversário, congresso. O jogador posiciona a decoração (cadeiras, arco, mesa de bolo) a partir de um modelo, e a nota depende do capricho e do horário.

### 5.3 Restaurante

- [ ] Cardápio do hotel com pratos nordestinos (moqueca, bobó, carne de sol); ligar o peixe da pesca ao estoque.
- [ ] Crítico gastronômico disfarçado de vez em quando: uma nota alta libera estrela no hotel.

### 5.4 Salão de jogos

- [ ] Decoração: piso, parede com papel ou ripado, iluminação, quadros e balcão de fichas. Hoje está branco e vazio.
- [ ] Sinuca jogada até o fim, com regras completas e placar visível.
- [ ] Pebolim com controle real (girar as barras), em vez da barra de tempo.
- [ ] 2 fliperamas jogáveis em tela (por exemplo, "Corrida de Jangada" e "Pega-Siri"), com recorde salvo.
- [ ] Torneio semanal (a estrutura de copa já existe), hóspedes jogando à noite e renda das fichas.

## 6. Sistemas que amarram tudo

Sem esta parte, as expansões ficam soltas. Cada atividade precisa alimentar dinheiro, estrelas, fama e a campanha.

### 6.1 Ciclo do dia e economia

- [ ] Cada expansão tem horário de pico diferente, para o dia ter um roteiro: manhã no quiosque e na piscina, tarde nos passeios e negócios, fim de tarde no bar e noite no restaurante e salão de jogos.
- [ ] **Balanceamento:** jogar do zero até o Grand Hotel e medir. Meta de um desbloqueio a cada 10–20 min e 6–10 h no Acesso Antecipado. Anotar em `docs/ue58/BALANCEAMENTO.md`.
- [ ] Equipe automatiza com uma renda menor, e o jogador sempre ganha mais fazendo pessoalmente.

### 6.2 Tutorial e objetivos

- [ ] Dica na primeira vez de cada sistema (balcão, celular, bar, passeio, cada negócio, piscina, recepção, sinuca), usando o `tutorial.json` que já existe.
- [ ] Objetivo atual sempre visível e o próximo desbloqueio mostrado no celular ("faltam R$ 1.200 e fama 4 para a piscina").

### 6.3 Pesca e modo foto

- [ ] **Pesca:** hoje são 5 espécies, um E e uma janela de tempo. Acrescentar a escolha de isca, a briga com o peixe (puxar e soltar a linha sem arrebentar), um livro de espécies e a venda para o restaurante.
- [ ] **Modo foto:** hoje são 7 temas. Acrescentar desafios no álbum ("baleia saltando", "farol aceso à noite"), filtros e o envio para a lojinha (cartões-postais).

### 6.4 Eventos do calendário

- [ ] Conferir no jogo, com foto, cada evento de `events.json`: calor, lua cheia, maré alta, tempestade, quermesse, junina, DJ e carnaval. Cada um deve mudar algo **visível** e **jogável**: decoração, prato especial no quiosque, clientes fantasiados.
- [ ] Preparativos comprados na véspera aparecem no mapa.

### 6.5 Fim do Acesso Antecipado

- [ ] Tela "obrigado por jogar" (a lógica `IsEndOfContentDue` já existe), com o que vem a seguir e um botão para avaliar na Steam. O jogo continua livre depois.

## 7. Steam (P0) — em paralelo

A página pública só sai quando o visual estiver bom para as fotos e o trailer (decisão do Sergio). A conta e a parte técnica podem andar já, sem nada público, porque a Steam tem prazos de espera e de revisão.

### Sergio (agora, nada público)

- [ ] Conta Steamworks, taxa de US$ 100, dados fiscais (W-8BEN) e bancários.
- [ ] Criar o App ID do jogo e o da demo. A página fica montada e **não publicada**.
- [ ] Nome comercial escolhido: "Coconut Coast: Resort Simulator" (nenhum jogo com esse nome achado na Steam em 04/11). "Maré Alta" continua como o nome do resort dentro do jogo.

### Claude Code (técnico)

- [ ] Build **Shipping** Win64 testado num PC sem a Unreal instalada.
- [ ] **3 slots de save** (hoje só `slot1.json`), salvamento automático e backup antes de gravar.
- [ ] Menu principal completo e opções completas (gráficos por item, resolução, limite de FPS, FOV, volumes, remapear teclas).
- [ ] Preset **Baixo** real (sem Lumen, menos pessoas, sem MetaHuman longe), medido com `bench_package.ps1` para definir os requisitos mínimos.
- [ ] Integração Steam: Online Subsystem Steam, conquistas, Steam Cloud e Rich Presence.
- [ ] Modo **DEMO** (3 dias de jogo, expansões futuras travadas, tela final com "Adicione à lista de desejos").

### Quando o visual estiver pronto

- [ ] Publicar a página "Em breve" com 5+ prints em 1920×1080 e as cápsulas.
- [ ] Trailer de 30–60 s: acordar, quiosque, bar, passeio de barco, pôr do sol, hotel.
- [ ] Inscrição na Next Fest com a demo.

## 8. Prompt para o Claude Code

```text
Projeto: Maré Alta Resort (Unreal Engine 5.8), repositório sergiomrge-tech/simulador-resort, branch codex/ue58-migration, projeto em unreal/MareAlta.

Antes de começar, leia CLAUDE.md, AGENTS.md e docs/ue58/PENDENCIAS_100.md. Siga todas as regras deles (nada de low poly ou primitivas, interface MareNotebookStyle, textos em PT-BR + i18n_extract).

Tarefa: implementar o checklist docs/ue58/CHECKLIST_EXPANSOES.md, seções 1 a 6, NA ORDEM, um item por vez:
1. Bar do Coqueiro (preparo físico primeiro)
2. Passeios
3. Negócios da vila (uma mecânica própria para cada um)
4. Piscina
5. Grand Hotel e salão de jogos
6. Sistemas (balanceamento, tutorial, pesca, foto, eventos, fim do AE)

Para cada item:
- Valores novos em Content/Data/*.json; lógica em MareSimulation (Mare<Área>.cpp); mundo e props em Mare<Área>World.cpp.
- Escreva um teste automático ou uma checagem no MarePreviewQA e tire fotos de prova no PIE (docs/ue58/graphics-reference/).
- Rode python tools/ue58/qa/qa_gate.py; só comite com PASS. Commit pequeno por item, mensagem em inglês no padrão do repositório.
- Marque o item como [x] em docs/ue58/CHECKLIST_EXPANSOES.md.

Não me pergunte a cada passo: decida pelo bom senso e anote as decisões no checklist. Só pare para perguntar se algo for irreversível ou mudar o rumo do jogo. Responda sempre em português.
```
