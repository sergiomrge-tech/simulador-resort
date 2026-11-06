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

## PRIORIDADE ATUAL — terminar para o Acesso Antecipado (Sergio, 06/11/2026)

"Minha prioridade é terminar para o acesso antecipado."; "mecânicas novas, novos sistemas, pode [ficar para depois]";
"hotel, quartos, salão de jogos são importantes para o EA" (Sergio, 06/11/2026). Siga ESTA ordem:

1. **6.2 Tutorial e objetivos** com o que já existe (`tutorial.json`): dica na primeira vez de cada sistema e objetivo
   atual/próximo desbloqueio sempre visíveis.
2. **5. Grand Hotel e salão de jogos, COMPLETO** (exceção à regra de não criar mecânica nova):
   5.1 quartos (3 tipos visitáveis com interior modelado, arrumação com camareira, frigobar no check-out, reclamações
   pelo celular); 5.4 salão de jogos (decoração, sinuca completa com placar, pebolim com controle real, 2 fliperamas com
   recorde, torneio semanal e renda das fichas); 5.2 VIPs e eventos; 5.3 restaurante e crítico gastronômico.
3. **4. Piscina:** hóspedes aproveitando a piscina e o tobogã (vida/animação, sem gestão nova).
4. **6.1 Balanceamento** do jogo completo: jogar do zero ao Grand Hotel e medir (1 desbloqueio a cada 10–20 min, 6–10 h
   de jogo); ajustar números. Anotar em `docs/ue58/BALANCEAMENTO.md`.
5. **6.5 Tela de fim do Acesso Antecipado.**
6. **Seção 7, parte técnica (Claude Code):** 3 slots de save com salvamento automático e backup; menu e opções completos;
   preset Baixo medido; build Shipping testado; integração Steam (conquistas, Cloud, Rich Presence); modo DEMO.
7. **ILHA** (mapa em forma de ilha pequena, ver seção 0).

**DEPOIS do Acesso Antecipado** (não fazer antes do lançamento): 3.6 (níveis dos negócios, funcionário com 60%, relatório
diário), 6.1 horários de pico, 6.3 pesca e modo foto, 6.4 eventos do calendário e a revisão da lojinha (3.5). Quando os
itens 1–7 acabarem, pare e avise o Sergio em vez de começar estes.

Itens do Sergio na seção 7 (conta Steamworks, App ID, página, trailer, Next Fest) não são do agente.

## 0. Pendências abertas (05/11/2026) — resolver antes de seguir

Pedidos do Sergio e conferências que ficaram para trás no lote de 05/11 (aluguel, fundo do mar, lâmpadas).

- [x] Rodar `python tools/ue58/qa/qa_gate.py` sobre o lote de 05/11: ele foi commitado a pedido do Sergio sem o
  portão, porque o editor derrubou a conexão MCP durante a última rodada de fotos.
  Decisões (06/11): o portão achou 37 corais do recife flutuando: a plataforma do fundo descia 60 cm sob o recife
  (perfil -900 → -960) e os corais ficam a -902. O perfil (`reef.json` → `floor_fill.profile`) ficou plano a -900 sob o
  recife e os planos do fundo foram refeitos. Portão PASS (39 testes, 571 flutuando, log limpo); a linha de base de
  flutuação baixou de 585 para 571, então qualquer coral que volte a flutuar reprova.
- [x] Fotografar à noite as luminárias com foco virado para baixo (`lighting.json` + pendentes do quiosque e ventilador
  da casa em `MareVisualWorld::BuildLamps`): casa, cozinha, banheiro, quiosque, lobby, suíte, pousada e bangalô.
  Pedido: "as lâmpadas precisam iluminar melhor", "lâmpada precisa estar virada para baixo".
- [x] Casa à noite ainda clara e alaranjada: ajustar intensidade/temperatura das luzes da casa e a exposição de
  interiores (`Interiors` em `MareVisualWorld::Tick`).
- [x] Globo das luminárias não brilha quando a luz acende: material com emissivo ligado à noite (como `glow*`).
- [x] Lobby do Grand Hotel: 6 luzes de 2500 cd (`mare_hotel_lobby.py`) só têm luminária em parte dos pontos.
  Regra: luz só onde houver luminária ("a iluminação dos imóveis precisa ser das lâmpadas").
  Decisões (06/11):
  - **Causa da casa clara:** ela não tinha volume `MareInterior` e usava o olho da noite de fora (EV100 −1,9…−0,9, feito
    para o luar), que transformava as lâmpadas de 38 cd em luz do dia. Já a suíte, o lobby e os bangalôs, que tinham
    volume (EV 4,4…5,2), ficavam quase pretos. Agora a casa tem o volume `Interior · casa` (`mare_light_audit.house_volume`)
    e todos os cômodos usam o mesmo olho noturno, `mare.InteriorNightEV` = 2,6 (teto +0,8).
  - Casa em branco neutro de LED: 4000–4200 K, cozinha 38 cd, banheiro 32 cd e ventilador 32 cd. O lampião de óleo
    continua em 1900 K, porque é chama.
  - **Lobby:** as 6 luzes soltas saíram do nível e do `mare_hotel_lobby.furnish`. As 10 luminárias de teto do lobby
    acendem pelo `BuildLamps`: cada uma tem um foco de 250 cd para baixo e um ponto fraco no teto. O `BuildLamps` agora
    também reconhece atores de malha simples, não só instâncias. A suíte foi para 140 cd.
  - **Luzes sem luminária** levam a tag `MareBareLight` e só servem de preenchimento de dia, apagando à noite: o teto
    dos 3 bangalôs (lá quem ilumina são os abajures) e o ponto da porta da recepção da pousada (`mare_light_audit.fix_level`).
  - **Globos:** o `M_LampGlow_PBR` (emissivo com `MPC_MareTime.Night`) foi aplicado aos globos da luminária de teto
    (casa e lobby), da lanterna do quiosque e do lampião (`mare_light_audit.glow`).
  - **Checagem permanente:** o portão reprova luz de cômodo sem luminária a até 160 cm (`mare_light_audit.bare_check`).
    O `tools/ue58/qa/night_lights.py` fotografa os 10 interiores às 22h com tudo liberado e espera 15 s por câmera:
    com 7 s, cômodos vistos pela primeira vez saíam com a luz do dia ainda no cache do Lumen.
  - **Tela de fim do Acesso Antecipado:** ela pausa o jogo, e as fotos noturnas saíam todas congeladas na porta da casa.
    `mare.ShowUI close` agora fecha essa tela.
  - Prova: portão PASS + `docs/ue58/graphics-reference/night_lights_fixtures.jpg`.
- [x] Conferir se o aviso vermelho "Cached lighting in Lumen ... clipped" sumiu no fundo de 100 m depois de travar
  a exposição embaixo d'água.
  Decisão (06/11): não tinha sumido. Medido com `ShowFlag.VisualizeHDR`: a 100 m o olho estava em EV100 10, mas a
  pré-exposição ia a EV ~14,5, porque a engine soma a luminância do `SceneColorTint` na pré-exposição
  (`PostProcessEyeAdaptation.cpp`), e a tinta do fundo tinha luminância 0,013. A faixa segura com
  `r.EyeAdaptation.CachedLightingPreExposure` 4 é [-8, 12], então o cache do Lumen era cortado, e era esse corte que
  escurecia o fundo. Agora `MareUnderwaterGrade` deixa na tinta só a cor, com a luminância da superfície, e o escuro vai
  para o `ColorGain` da LUT, aplicado depois da exposição. O visual é o mesmo (fundo azul-marinho quase preto), sem o
  aviso. Teste permanente: `MareAlta.Visual.UnderwaterGrade` (pré-exposição ≤ 12 em toda profundidade, fundo com ganho
  < 0,03). Portão PASS (40 testes).
- [x] Foto de prova do motorista do ônibus sentado no intro (`HoldPose`).
  Decisão (06/11): sentado estava certo (quadril no banco, coxas na horizontal, pernas para baixo), mas sem papel ele
  caía na lista da praia e dirigia de biquíni. Agora é um morador sentado (`bAmbient` + `bSeated`, nome "Motorista"),
  com roupa da lista `village`. O portão confere a roupa dele durante a chegada (`mare_intro_audit.driver`, reprova
  roupa de banho). Prova: `docs/ue58/graphics-reference/intro_bus_driver_seated.jpg` (`HighResShot 1` funciona no
  PIE e sai sem HUD). Observação: o painel do ônibus é uma caixa sem volante; fica para quando houver um volante
  gratuito que sirva.
- [x] Barra horizontal atravessando a câmera dentro do quiosque com tudo liberado (vista 3700,-1600): identificar
  o objeto.
  Decisão (06/11): eram as hastes do neon "ABERTO" (`World_1296/1297`, `Region_neon`), a 4–57 cm da lente. Foram
  achadas com `mare_light_audit.ray` e confirmadas escondendo os atores. Não é defeito do jogo: a câmera de QA estava
  com o pawn em z 170, ou seja, olho a 2,44 m, atrás da placa. Na altura do olho do herói (pawn z 100, olho 1,74 m) a
  vista é limpa. A câmera `quiosque_barra` do `night_lights.py` foi corrigida.
- [x] `shot showui` parou de gerar arquivo no PIE em algumas rodadas (só `HighResShot 1` funcionou): investigar.
  Decisão (06/11): reproduzido minimizando o editor. A foto com UI é o Slate copiando o back buffer da janela
  (`FSlateApplication::TakeScreenshot`), que não é desenhado com a janela minimizada, e o pedido some sem aviso no log;
  o `HighResShot` lê a cena e por isso funcionava. Novo comando `mare.Shot [arquivo]` (e o `mare.ShotLater`): restaura a
  janela se estiver minimizada e pede a foto 1 s depois. Os scripts de QA (`mare_hud`, `mare_beach`, `mare_hotel_lobby`,
  `mare_progression_probe`) trocaram `Shot showui` por `mare.Shot`. Checagem permanente: o portão minimiza o editor,
  pede `mare.Shot` e exige o arquivo (`ui_shot`). Portão PASS (40 testes).
- [ ] LOJINHA (por último, depois da ilha): revisar a lojinha de souvenires (3.5), que já está pronta, e ajustar o que o Sergio pedir.
- [ ] ILHA (pedido grande, entregue ao agente novo do Sergio): "morro no meio, praia em volta, uma ilha pequena,
  preservando a vila e todas as construções, o restante é vegetação e árvores". Mar, espuma e perfil do fundo
  (`reef.json` → `floor_fill`, `SeabedZ`) precisam virar radiais. Refazer a navegação estática com cuidado.
  Planejar antes, com esforço alto.
- [ ] Git: o repositório recuperado é um clone parcial (blob:none). Usar `GIT_NO_LAZY_FETCH=1` em
  status/diff/add; um `git reset` travou baixando blobs. Se possível, completar o clone (`git fetch --refetch`
  ou clonar de novo) para voltar ao normal.

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

- [x] O grupo segue o jogador. Se ele andar rápido demais, alguém fica para trás e reclama.
- [x] Paradas de foto nos mirantes (ligar ao modo foto). Água e protetor solar no início.
- [x] Pôr do sol no farol com bônus de nota se chegar na hora.

Decisões (05/11/2026):
- **Trajeto real:** o farol da UE fica num promontório de pedra a leste da praia, e o caminho a pé pela navegação tem cerca de 60 m (não 421 m). A trilha (`tours.json` "trail_tour") passa por:
  - largada na areia ao lado do píer;
  - Mirante da praia, com vista da baía;
  - Mirante das pedras;
  - fila nas pedras de frente para o oeste, ao lado do farol.

  Na bilheteria aparece "Guiar a trilha agora" na hora da saída (16h).
- **Grupo a pé:** um turista por bilhete (até 5), a 240 cm/s; o herói anda a 260 e corre a 420. Eles vão em duplas atrás do guia. "Atrás" é de onde o guia veio, e não para onde a câmera olha: virar para ver o grupo não o puxa para a frente. Quem fica a mais de 10 m reclama ("Ei, mais devagar!"), com −0,15, no máximo uma vez a cada 25 s.
- **Largada:** E em cada turista entrega água e protetor solar. A garrafa vai para a mão dele; o herói não usa as mãos.
- **Mirantes:**
  - P (modo foto) tira a foto do grupo, se o grupo estiver lá. Fotos nos dois = boa; em um = ok.
  - E na placa conta a história do farol: o relógio avança 12 min e a nota sobe 0,15. Isso também serve para chegar na hora do pôr do sol.
- **Pôr do sol:** o sol fica a 0° às 18h, e o relógio corre 1 min de jogo por segundo. A janela vai das 17h15 às 17h55. Quem chega cedo espera, e a cada 15 min alguém reclama. Na janela, o grupo comemora e assiste por 12 min, com +0,5. Quem chega tarde perde o pôr do sol. Depois o grupo fica um pouco e volta andando para a praia.
- **Nota:** `TrailScore` calcula as escolhas (água, fotos e pôr do sol) e o bônus, e o resultado vai para `GuideTour`.
- **Prova:** teste `TourBooth` (escolhas e nota da trilha) + `docs/ue58/graphics-reference/tours_trail.jpg` (grupo subindo as pedras; grupo de frente para o pôr do sol com as garrafas).

### 2.5 Resultado e evolução

- [x] Tela final com estrelas, gorjetas e avaliações escritas no app do celular. Uma nota alta aumenta a fila de amanhã.
- [x] Melhorias: lancha, equipamento de snorkel novo, fotógrafo que vende fotos e passeio novo (pôr do sol na jangada ou ilha vulcânica, só olhando de longe).
- [x] O guia contratado faz o passeio sozinho com nota média 3; ir junto rende mais.

Decisões (05/11/2026):
- **Resultado:** cada passeio que sai, com o jogador ou com o guia, grava um resultado no save (`tour_results`, os 12 mais recentes). O resultado traz:
  - nota, gorjeta, pessoas e fotos vendidas;
  - até 3 avaliações escritas, uma por parada (`tours.json` "reviews", conforme a escolha), assinadas pelos grupos que compraram;
  - um destaque no topo quando o bônus da viagem foi alto ou baixo (golfinhos, pôr do sol, espécies; enjoo, coral, gente para trás).

  O celular ganhou a aba **Passeios** (aparece com a expansão). Ao terminar, a mensagem aponta para ela. Usei texto em vez de "★", porque as fontes não têm o símbolo.
- **Fila de amanhã:** nota ≥ 4,5 traz +2 pessoas no mesmo passeio amanhã, ≥ 4 traz +1, e < 2,5 tira 1 (`buzz`, somado em `TourPassengers`).
- **Melhorias:** usei os itens que já existiam em Personalizar · Passeios e liguei cada um ao passeio jogável:
  - Barco: +7% de velocidade e +1,5 s antes do enjoo por nível;
  - Mergulho: o alvo do snorkel alcança +1,2 m e cada espécie vale +0,02 por nível;
  - Fotos (fotógrafo): no nível 2 ou mais, vende fotos a até 60% do grupo, mais com nota alta, de R$ 15 a R$ 60 cada;
  - Roteiros: no nível "Pôr do sol no mar" abre o passeio novo **Pôr do sol na jangada** (17h, R$ 55), guiado por diálogo, com a ilha vulcânica vista de longe.
- **Guia sozinho:** nota 3 (mais a média dos extras), sem gorjeta. Com o jogador, vem a gorjeta de cada parada boa e mais fama.
- **Correção encontrada:** o `GuideTour` recusava a nota depois da hora de saída, e a trilha chega ao farol às 17h15 ou mais. Um passeio jogável em andamento (`tours.active`) agora termina normalmente fora da hora.
- **Prova:** teste `TourBooth` (resultado e avaliações, +2 amanhã, fotos vendidas, jangada travada e liberada, passeio em andamento avaliado depois da hora) + `docs/ue58/graphics-reference/tours_results.png`.

## 3. Negócios da vila

**Hoje:** 5 negócios (`business_games.json`). Todos usam o **mesmo** minijogo: 3 rodadas de barra de tempo com recompensa de 0,3× a 2,2× e +2 de fama por acerto. Só muda o texto ("Bola de baunilha!", "Fritar o pastel").

**Objetivo:** cada negócio com uma mecânica própria, curta (30–90 s), que fica mais difícil e rende mais com o nível.

### 3.1 Sorveteria — montar a casquinha

- [x] O cliente pede uma combinação ("2 bolas: coco + açaí, calda de chocolate"), mostrada por 3 s.
- [x] O jogador monta de memória com os sabores no freezer; a bola cresce enquanto ele segura o botão (pequena, certa ou derramando).
- [x] Picolé compartilhado com a piscina: a sorveteria abastece o cooler.
- [x] Dia de calor: o dobro de clientes, com uma fila que cresce.

Decisões (05/11/2026):
- **Fila:** os clientes chegam a cada hora aberta (1–2; o dobro no Dia de calor; 40% na chuva), até 6 na fila. Quem espera mais de 45 min desiste, e ao fechar todos vão embora. No balcão, o primeiro da fila fica de frente e até 3 esperam atrás.
- **Minijogo** (`SMareIceCreamGame`, dados em `business_games.json` "sorveteria.icecream"):
  - o pedido aparece por 3 s em vermelho ("Davi pede: 3 bolas: chocolate + açaí + limão · calda de caramelo") e some;
  - segurar um pote do freezer faz a bola crescer: clique, teclas 1 a 6, ou A no pote escolhido com as setas;
  - soltar na faixa verde do medidor deixa a bola no tamanho certo (0,7–1,0); abaixo é pequena, acima é grande demais;
  - a cobertura escorre sobre a bola de cima; há os botões "Desfazer bola" e "Entregar".
  - A nota de 0 a 3 vem de três acertos: sabores, tamanho de todas as bolas e cobertura. O pagamento é por bola + cobertura × [0,3; 0,7; 1,0; 1,25], com gorjeta de R$ 5 no perfeito. A mensagem diz o que errou ("bola pequena, cobertura errada"). Atende um cliente atrás do outro enquanto houver fila.
- **Picolé da piscina:** com a sorveteria, o cooler vende picolé caseiro, que ela produz a cada hora aberta (4 por hora, até 12, R$ 2 de custo cada), 40% mais caro que o comprado. O cooler mostra quantos tem e vende só o que tem; quando acaba, avisa "Faltou picolé para N". Sem a sorveteria, nada muda.
- Os outros negócios continuam com o minijogo antigo até os seus itens (3.2–3.5).
- **Prova:** teste `MareAlta.Gameplay.IceCream` (fila, calor ×2, casquinha perfeita, errada e grande demais, paciência, picolé caseiro e falta no cooler, fechamento) + `docs/ue58/graphics-reference/business_icecream.jpg`.

### 3.2 Food truck do pastel — montar e fritar

- [x] Escolher o recheio pedido (carne, queijo, pizza, camarão), fechar a massa (arrastar para selar a borda) e mergulhar no óleo.
- [x] Fritura em tempo real: cru → dourado → queimado, com o ponto certo indicado pelo som e pela cor.
- [x] Caldo de cana na moenda como pedido extra (girar a manivela).

Decisões (05/11/2026):
- **Fila no food truck:** como a da sorveteria, 1–2 clientes por hora aberta, o dobro em dia de festa (quermesse, junina, show) e menos na chuva; até 6, e desistem depois de 40 min. A fila escolhe um lado livre: atrás do cliente ficava a fachada de um prédio, então ela vai pela calçada, conferindo chão e parede.
- **Minijogo** (`SMarePastelGame`, dados em `business_games.json` "food_truck.pastel"):
  1. recheio: carne, queijo, pizza ou camarão, que aparece na massa até fechar;
  2. fechar a borda: arrastar o mouse sobre o pastel (ou alternar as setas); as marcas da borda aparecem;
  3. fritar em tempo real: a massa vai de crua a dourada, escura e queimada pela cor e pelo medidor com a faixa verde. No ponto (5,5–8,5 s) toca um "ding", e o óleo chia a cada 2 s;
  4. caldo de cana, quando pedido (metade dos pedidos): 4 voltas da manivela (girar o mouse ou alternar as setas), com o som da moenda a cada volta.
- **Nota:** 3 acertos (recheio, borda fechada antes do óleo e ponto dourado). Borda aberta vaza; pastel queimado não é vendido; o caldo só é pago se foi espremido. A mensagem diz o que errou ("ficou cru, abriu no óleo, faltou o caldo de cana").
- **Sons novos:** fritura, ding e moenda, sintetizados (`tools/ue58/gen_pastel_sfx.py`, CC0 próprio), porque os pacotes CC0 já usados não têm. Importados com `mare_hud.import_sfx_only`, que não mexe no resto do catálogo.
- **Prova:** teste `MareAlta.Gameplay.Pastel` (fila, festa ×2, perfeito, sem caldo, cru e aberto, queimado sem pagamento, recheio errado, paciência, fechamento) + `docs/ue58/graphics-reference/business_pastel.jpg`.

### 3.3 Aluguel de pranchas e caiaques

- [x] Alugar com tempo (30/60 min de jogo). O cliente volta e o jogador confere a prancha: amassada cobra multa.
  Decisões: fila própria do aluguel (`prog.biz.aluguel`, chegadas por hora, mais no dia de calor, menos na chuva,
  paciência de 40 min); prancha R$ 10 e caiaque R$ 14 por 30 min. Na devolução, 30% voltam com amassado: multa certa
  cobra R$ 20, multa injusta tira 2 de fama, deixar passar não cobra nada (`InspectReturn`). Valores em
  `business_games.json` → `aluguel.rental`; lógica em `MareRental.cpp`; teste `MareAlta.Gameplay.Rental`.
- [x] Encerar a prancha com movimentos circulares (mouse/analógico) antes de alugar: a cera aumenta a gorjeta.
  Decisões: 5 voltas com o mouse (ou a sequência de setas no controle) na tela `SMareRentalGame`; prancha encerada dá
  30% de gorjeta e +2 de fama.
- [x] Evento: caiaque à deriva no mar, que o jogador busca nadando ou de caiaque (física simples).
  Decisões: com um caiaque alugado, 25% de chance por hora de ele ficar à deriva em frente ao aluguel. O caiaque
  (modelo próprio `tools/ue58/gen_rental.py`) boia pelas ondas (`SeaHeight` na proa, popa e bordos) e vai para o largo.
  O jogador nada até ele, aperta E e o reboca a 2,2 m de corda até a areia (`MareRentalWorld.cpp`), ganhando R$ 30 e +3 de fama.

### 3.4 Escolinha de surfe — EXCLUÍDA (Sergio, 06/11/2026: "excluir escola de surfe")

Não fazer. Os três itens abaixo saíram do plano; pule direto para 3.5.

- ~~Aula na areia: o aluno copia a pose que o jogador escolhe na ordem certa (remada, pop-up, base).~~
- ~~Aula na água: empurrar o aluno na onda na hora certa. Ele fica em pé ou leva caldo, com animação cômica.~~
- ~~O jogador pode surfar sozinho (minijogo de equilíbrio na onda) e liberar "aula avançada".~~

### 3.5 Lojinha de souvenires — FICA PARA O FIM (Sergio, 06/11/2026: "lojinha deixa por último")

Já implementada (decisões abaixo). Não mexer agora: revisar e ajustar só no fim, depois da ilha (item final do checklist).

- [x] Comprar artesanato dos moradores da vila (ligar aos capítulos da vila) e arrumar a prateleira: a posição na vitrine afeta a venda.
- [x] Embrulhar o presente: dobrar o papel em 3 cliques na ordem certa e escolher a fita na cor pedida.
- [x] Vender cartões-postais feitos com as fotos do modo foto do jogador.

Decisões (06/11/2026):
- **Tela da lojinha** (`SMareSouvenirGame` em `MareSouvenirGame.cpp`, lógica em `MareSouvenir.cpp`, valores em `business_games.json` → `souvenir.shop`), com três páginas (Tab troca): Embrulhar presente, Prateleira e artesãos, Cartões-postais. O balcão abre sempre que a loja está aberta; o turista só espera no balcão quando alguém pediu embrulho.
- **Artesãos:** Dona Rita (ímã de jangada e colar de conchas, desde o início), Seu Severino (jangadinha, capítulo do píer), Padre Robson (garrafinha de areia colorida, prainha), Dona Cecília (cocada caseira, sabores) e a prefeita Tuanny (máscara de carnaval, carnaval). Cada um faz poucas peças por dia (`daily`); compra em lotes de 4 para o estoque dos fundos.
- **Prateleira:** 4 lugares, da vitrine ao fundo (×1,6, ×1,2, ×0,85, ×0,45). A cada hora aberta chegam 1–3 turistas (mais com fama, ×2 no carnaval); cada um olha da vitrine para dentro e compra com chance 30% × lugar × apelo da peça. A venda da prateleira substitui a renda fixa por hora da loja: prateleira vazia não vende nada. Começa com ímãs na vitrine e colares no balcão.
- **Embrulho:** quem compra pede embrulho em 45% das vezes (fila de até 4, paciência 45 min). A cor da fita aparece por 3 s e some; os três botões de dobra mudam de lugar a cada cliente (a ordem certa é laterais, fundo, topo, escrita no bilhete). Nota: ordem das dobras + fita certa + até 15 s; paga R$ 6 × [0; 0,5; 0,8; 1] e R$ 5 de gorjeta no perfeito. Dobra fora de ordem amassa o papel (desenho mais escuro), e dá para pegar papel novo.
- **Cartões-postais:** as 4 fotos mais novas do álbum aparecem em miniatura (o arquivo da própria foto); imprimir 5 custa R$ 7,50; preço R$ 5 + R$ 2 por atração na foto (até 2). Turistas compram com chance de 35% cada.
- **Prova:** teste `MareAlta.Gameplay.Souvenir` (artesão travado pelo capítulo, peças do dia, prateleira e vitrine vendendo mais que o fundo, prateleira vazia, embrulho perfeito/amassado/demorado, cartões, fechamento e save) + `docs/ue58/graphics-reference/business_souvenir.jpg`. O teste genérico do balcão passou a usar a escolinha de surfe, que continua com a tarefa antiga.

### 3.6 Comum a todos

Feito em 06/11/2026 (estava quase pronto quando o Sergio o mandou para depois do lançamento; fechei com teste e portão em
vez de jogar fora). Lógica em `MareBizCommon.cpp`, valores em `business_games.json` (`businesses.<id>.levels`, `clerk_share`).

- [x] Nível 1 a 3 por negócio, cada um com a mecânica mais exigente e o preço maior. `levels[0]` é o nível 2 e `levels[1]`
  o 3: custo, fama mínima, nome, `price_mult` (×1,3/×1,6; aluguel ×1,25/×1,5) e `set`, que sobrepõe valores da mecânica
  (sorveteria: pedido aparece menos tempo e a bola certa fica mais estreita; pastel: janela do dourado menor; aluguel: mais
  voltas de parafina; lojinha: a fita aparece menos tempo). Compra pelo celular (aba Resort, card do negócio).
- [x] Funcionário que automatiza com 60% da renda; fazer pessoalmente rende 100% + fama. Saves antigos já pagavam salário
  a todos: sem a marca, conta como contratado. Dispensado, a fila só anda quando o jogador atende e quem espera desiste.
- [x] Relatório diário de cada negócio no app do celular: hoje e ontem (atendidos por você com nota média, perfeitos e fama;
  funcionário; prateleira; desistências; total). Prova: `docs/ue58/graphics-reference/business_common_report.jpg`.
  Defeitos achados na foto e corrigidos: o card crescia depois de medido e cobria o "folha x de y" (o `SMareFit` agora
  remede as linhas visíveis, nunca deixa um título sozinho numa folha e reduz a escala só da folha que não cabe); o nome do
  nível cortava o botão (o botão diz "Melhorar · R$ X" e o que muda fica na dica da linha "Próximo: nível 2, ...").
- [x] Teste por negócio: `MareAlta.Gameplay.BusinessCommon` (perfeito, médio e erro em sorveteria, pastel, aluguel e
  embrulho da lojinha, relatório, save, virada do dia, funcionário a 60% sem fama, nível 2 e 3).

## 4. Piscina e day use — EXCLUÍDA (Sergio, 06/11/2026: "excluir 4")

Os itens antigos (riscados abaixo) saíram do plano. No lugar deles fica UM item só (Sergio, 06/11/2026: "na piscina só
coloque hóspedes que entrarem aproveitando a piscina e tobogã"):

- [ ] **Hóspedes aproveitando a piscina e o tobogã:** hóspedes entram na água e nadam, boiam e conversam dentro da
  piscina, e sobem a escada do tobogã e descem escorregando até cair na água. Animação de verdade (MetaHumans, sem
  deslizar nem atravessar a borda, o deck ou outras pessoas), quantidade que aumenta nos dias de calor e de dia. Sem
  minijogo nem gestão nova. Prova: fotos de perto de gente nadando e descendo o tobogã, e o qa_gate com PASS.

**Hoje:** folhas caem toda hora e a peneira tira com E. Toalhas usadas ficam nas espreguiçadeiras e o picolé é vendido no cooler (`pool.json`). Sujeira e toalhas derrubam a renda e as estrelas.

**Objetivo:** a piscina vira um lugar para cuidar e animar, não só limpar.

- ~~**Peneira de verdade:** a rede segue a câmera e as folhas boiam e se movem com o vento. É preciso passar a rede por cima delas, em vez de um único E.~~
- ~~**Química da água:** um kit de teste uma vez por dia (cor da amostra) e a escolha de cloro ou correção de pH. A água turva aos poucos, de forma visível.~~
- ~~**Espreguiçadeiras:** o hóspede "marca" o lugar com a toalha e sai (evento cômico). O jogador decide liberar ou não.~~
- ~~**Salva-vidas:** uma criança sem boia ou alguém passando mal. O jogador ou o salva-vidas contratado age a tempo.~~
- ~~**Aluguel de boias** (flamingo, rosquinha), com renda e devolução.~~
- ~~**Tobogã:** fila e um sinal para liberar a descida quando a saída está livre. Liberar cedo demais causa trombada cômica e reclamação.~~
- ~~**Festa na piscina** à noite (evento pago na véspera): luzes, DJ e drinks do bar com mais demanda.~~
- ~~Picolé abastecido pela sorveteria (ver 3.1). Sem estoque, o cliente reclama.~~
- ~~Melhorias: hidromassagem, bar molhado, guarda-sóis e cascata.~~

## 5. Grand Hotel e salão de jogos

**Hoje:**

- Restaurante: anotar na mesa, pegar no passe da cozinha, servir; serviço de quarto pelo elevador; eventos reservados na véspera (`restaurant.json`).
- Recepção com VIPs.
- Sinuca com física, IA e aposta; pingue-pongue; pebolim com barra de tempo; 2 fliperamas decorativos.
- A torre é só casca: os quartos não têm interior, e o salão de jogos está vazio visualmente (paredes brancas lisas).

### 5.1 Quartos (maior lacuna visual)

- [x] 3 tipos de quarto visitáveis (standard, luxo e suíte) com interior modelado. Um andar real basta, e os outros repetem o mesmo modelo.
- [x] Arrumação como na pousada: cama, toalhas, frigobar e lixo. A camareira automatiza.
- [x] Frigobar: repor e cobrar no check-out.
- [x] Reclamação pelo telefone do celular ("ar-condicionado quebrado", "barulho"), com tempo para resolver.
  Decisões (06/11):
  - **3º andar visitável:** a suíte 301 (que já existia) mais o corredor, o standard 302, o luxo 303 com banheiro e a
    rouparia, a leste da suíte (`tools/ue58/gen_hotel_rooms.py` → `Content/Python/mare_hotel_rooms.py`, que importa,
    mobilia com a biblioteca e cria o volume `MareInterior`). Do saguão, um elevador sobe à suíte e o outro ao corredor
    dos quartos; os dois do 3º andar descem. Luminárias pelo `lighting.json` (luz só de lâmpada à noite).
  - **32 quartos** (`hotel_rooms.json`): 2 suítes, 10 luxo e 20 standard, numerados por andar (301...). O hóspede pede
    o tipo pelo perfil (lua de mel → suíte, família VIP/influenciador → luxo, executivo → standard) e paga a diária
    × `rate_mult`. Os 3 primeiros são os visitáveis; os outros repetem o modelo e ficam com a equipe.
  - **Check-out:** o quarto fica sujo com cama, toalhas, lixo e frigobar (só se o hóspede consumiu). A conta do
    frigobar entra no check-out (preço de venda) e a reposição custa o preço de fornecedor. A equipe de arrumação
    (8h–18h, 8 tarefas por hora) começa pelos quartos que ninguém vê e só chega ao 3º andar depois das 11h, para o
    jogador arrumar à mão de manhã. Quarto arrumado só pelo jogador fica "caprichado": +0,3 na nota do próximo hóspede.
  - **Reclamações** (8h–22h, no máximo 3 abertas): ar-condicionado, barulho, chuveiro, toalhas e TV, cada uma com prazo
    (45–90 min). Pelo celular (aba Resort e recepção) manda o técnico, que cobra; nos quartos 301–303, resolver
    pessoalmente (E no ponto do defeito) é de graça e dá fama. Prazo vencido baixa o humor do hóspede (avaliação pior).
    A reclamação vence no prazo, no tick do mundo, e não na virada da hora.
  - **Visual:** a roupa de cama das 5 camas virou pano (edredom e manta caindo pelos lados, travesseiros que afinam
    na costura) em vez de caixas; a TV da suíte, que era uma caixa cinza, virou a `mare_tv_oled65` sobre o rack.
  - Teste `MareAlta.Gameplay.HotelRooms` (tipos, numeração, pontos de cada tarefa e defeito, check-out e conta do
    frigobar, arrumação à mão × equipe, reclamações resolvidas e vencidas); `PousadaStays` e `HotelReceptionLine`
    atualizados (quarto sujo depois do check-out). QA: `mare.QA hotelroom <i>` e `mare.QA complaint <i>:<tipo>`.
  - Fotos: `docs/ue58/graphics-reference/hotel_rooms_day.jpg`, `hotel_rooms_night.jpg` (22h, luz das luminárias) e
    `hotel_room_task_phone.jpg` ("E Arrumar a cama · Standard 302" com o lençol bagunçado; telefone do hotel no celular).
  - Pendências vistas nas fotos: as janelas dos quartos são painéis de luz do dia (sem vista do mar), como na suíte;
    o lençol bagunçado é uma peça achatada (o mesmo da pousada).

### 5.2 VIPs e eventos

- [ ] Pedido especial de cada VIP (pétalas na cama, champanhe, quarto com vista). Acertar dá muita fama.
- [ ] Eventos com montagem: casamento na praia, aniversário, congresso. O jogador posiciona a decoração (cadeiras, arco, mesa de bolo) a partir de um modelo, e a nota depende do capricho e do horário.

### 5.3 Restaurante

- [ ] Cardápio do hotel com pratos nordestinos (moqueca, bobó, carne de sol); ligar o peixe da pesca ao estoque.
- [ ] Crítico gastronômico disfarçado de vez em quando: uma nota alta libera estrela no hotel.

### 5.4 Salão de jogos

- [x] Decoração: piso, parede com papel ou ripado, iluminação, quadros e balcão de fichas. Hoje está branco e vazio.
  Decisões (06/11):
  - O salão é o meio do saguão do térreo (x -2500..-1700, parede norte y 6890). Peças próprias em
    `tools/ue58/gen_game_room_decor.py` (bpy) e Poly Haven CC0 (alvo de dardos, relógio, quadro, cavalete de giz),
    importadas em `/Game/Custom/GameRoom` e postas por `Content/Python/mare_game_room.py` (`cmd('place')`, reexecutável,
    tag `Region_salao_jogos`: só aparecem depois de comprar o salão; sem colisão nem efeito na navegação, menos balcão,
    porta-tacos e cavalete).
  - Parede de destaque de 7,8 × 3,6 m: reboco azul-petróleo, ripado de nogueira sobre feltro nas duas pontas, rodapé e
    arremate com fita de LED quente; letreiros "SALÃO DE JOGOS" e "FICHAS" em letra-caixa iluminada; quadro, alvo de
    dardos na altura oficial (1,73 m) e relógio. O piso de madeira do saguão ficou, com um tapete de lã em espinha de
    peixe sob a sinuca.
  - Iluminação: luminária de sinuca de 3 cúpulas verdes como luminária do `lighting.json` (acende ao anoitecer, só com
    o salão comprado); a luminária de teto do saguão que ficava ali só aparece sem o salão (`unlock`
    `"grand_hotel,!salao_jogos"`, o `!` é novo em `UMareVisualWorld::UnlockMatches`).
  - Balcão de fichas de 1,3 m (frente ripada, tampo de quartzo, bandeja de fichas de latão) no lugar de uma poltrona do
    saguão, perto dos elevadores; porta-tacos com 6 tacos e giz ao lado da mesa.
  - Defeitos vistos nas primeiras fotos e corrigidos: o trilho de madeira do saguão (parte da malha da torre, 8 cm fora
    da parede) atravessava a parede de 5 cm → parede com 10 cm; o vidro glTF do quadro chegava quase opaco e espelhado
    e escondia a pintura → material próprio `M_GameRoomGlassClear`; as duas calateias do saguão eram uma fileira de
    folhas soltas sem vaso (galhinhos saindo do piso) → vaso `potted_plant_02` (`mare_hotel_lobby.swap_plant`).
    Checagem permanente no portão: `decor` (`mare_game_room.check`).
  - Fotos: `docs/ue58/graphics-reference/game_room_day.jpg` e `game_room_night.jpg`.
  - Visto e deixado para os itens seguintes: os 2 fliperamas são caixas laranja e azul com textura borrada (trocar
    quando ficarem jogáveis); de longe, a luminária da sinuca cobre parte do letreiro.
- [x] Sinuca jogada até o fim, com regras completas e placar visível.
  Decisões (06/11):
  - **Regras completas de bola 8** (`UMareGameRoom::ResolveShot`), além das que já existiam (grupos, bola errada,
    branca na caçapa, bola na mão, 8 antes da hora): saída legal (encaçapar ou levar ao menos 4 bolas à tabela, senão
    falta "saída fraca"); depois do toque, alguma bola tem de cair ou bater na tabela ("nenhuma bola foi à tabela depois
    do toque"); a 8 é **cantada**: a caçapa segue a mira (o anel amarelo mostra qual) e a rodinha do mouse ou LB/RB
    trocam; a 8 em outra caçapa perde. A 8 que cai na saída volta à mesa mesmo com falta (antes perdia). A IA canta onde
    mira (`Shoot` chama `AimPocket`).
  - **Placar visível:** no HUD, um cartão no canto superior direito com as bolas de cada lado (lisas cheias, listradas
    com aro branco, encaçapadas apagadas, a 8 aparece quando é a vez dela) e » em quem joga; a bússola some durante a
    partida (ficava embaixo do cartão). No mundo, o placar escrito a giz no cavalete ao lado da mesa (`game_room.json`
    → `scoreboard`, `UMareGameRoom::BoardLines`): a partida em andamento, ou vitórias e derrotas no hotel.
  - Defeitos vistos nas fotos e corrigidos: a câmera da partida (e a do pingue-pongue) fazia letterbox 16:9 (faixa
    preta e a linha de mira/anel do HUD 20–40 px fora das bolas) → `SetConstraintAspectRatio(false)`, checagem
    permanente `cameras` no portão; `mare.PoolQA` com o salão não comprado abria a partida na mesa inexistente (câmera
    no gramado) → `StartMatch` exige a mesa.
  - Teste `MareAlta.Gameplay.PoolFullMatch` ganhou saída fraca × forte, falta sem tabela, 8 na caçapa cantada (vence)
    e em outra (perde). QA: `mare.PoolQA eight` deixa o jogador na 8.
  - Fotos: `docs/ue58/graphics-reference/pool_called_eight.jpg` (anel na caçapa cantada, placar, giz no cavalete) e
    `pool_board_idle.jpg`.
- [x] Pebolim com controle real (girar as barras), em vez da barra de tempo.
  Decisões (06/11):
  - **Mesa própria modelada no bpy** (`tools/ue58/gen_foosball.py`): móvel de madeira, campo verde com marcações,
    contadores de bolinhas, 8 barras separadas (1-2-3-5 de cada time, coral × azul-mar) com pivô no eixo e a bola.
    `UMareFoosball` (`MareFoosball.cpp`) cria e move as peças; a mesa antiga (`foosball_table`) saiu do
    `UMareBusinessWorld`.
  - **Física 2D determinística** da bola (atrito de rolagem, tabelas, rampas dos cantos, boca do gol, traves) e os pés
    dos bonecos como caixas que andam com o deslize e o giro da barra: girada mais de ~47° a barra deixa a bola passar.
  - **Controle:** a barra ativa é a do jogador mais próxima atrás da bola (sublinhada em amarelo no HUD); mouse para
    frente/trás desliza, para os lados gira (o chute sai com a velocidade do giro), clique = chute rápido, botão direito
    levanta os bonecos; no controle, analógico esquerdo desliza, direito gira, RT chuta, LT levanta. As outras barras
    do jogador acompanham a bola sozinhas. Quem fizer 5 gols vence; o resultado paga pelo `PlayBusiness("pebolim")`
    (3 = venceu por 3+, 2 venceu, 1 perdeu por 1–2) e entra no recorde (`RecordGame("foosball")`).
  - **Adversário** sorteado da lista da sinuca: a mira dele vira a velocidade das mãos. À noite, nas horas das fichas,
    dois hóspedes jogam IA contra IA. Bola parada fora do alcance perto de um gol volta ao goleiro; no meio, nova saída.
  - Defeitos vistos nas fotos e corrigidos: as barras não apareciam (nomes fixos sem o sufixo do importador → caminho
    lido do `custom_assets.json`); o cliente da fila e os jogadores da noite ficavam 15–20 cm um dentro do outro e
    dentro do móvel (novas posições em `business_games.json`); com a câmera baixa a bola sumia atrás da tabela do
    jogador (câmera mais alta); a bola encolhia até sumir em um minuto (quaternião de giro sem normalizar).
  - Teste `MareAlta.Gameplay.FoosballMatch`: gol, tabela, fundo ao lado do gol, boneco bloqueia e levantado deixa
    passar, giro chuta, comandos do jogador (`PlayerControl`: frente desliza para longe, lado gira para o gol, clique
    chuta, direito levanta), 8 partidas IA × IA terminam 5 a algo com jogo de verdade, toque de calcanhar, reposição do
    goleiro, pagamento, malhas carregam pelo `custom_assets.json` e ninguém em pé dentro do móvel ou de outra pessoa.
    QA: `mare.FBQA` (com `mare.FBAutoPlay 1` joga sozinho).
  - Fotos: `docs/ue58/graphics-reference/foosball_table_day.jpg`, `foosball_night_guests.jpg`, `foosball_match.jpg`
    e `foosball_match_shot.jpg`. Visto e aceito: os hóspedes da noite jogam com as mãos sobre a mesa, não nos cabos
    (pose genérica de hóspede).
- [ ] 2 fliperamas jogáveis em tela (por exemplo, "Corrida de Jangada" e "Pega-Siri"), com recorde salvo.
- [ ] Torneio semanal (a estrutura de copa já existe), hóspedes jogando à noite e renda das fichas.

## 6. Sistemas que amarram tudo

Sem esta parte, as expansões ficam soltas. Cada atividade precisa alimentar dinheiro, estrelas, fama e a campanha.

### 6.1 Ciclo do dia e economia

- [ ] Cada expansão tem horário de pico diferente, para o dia ter um roteiro: manhã no quiosque e na piscina, tarde nos passeios e negócios, fim de tarde no bar e noite no restaurante e salão de jogos.
- [ ] **Balanceamento:** jogar do zero até o Grand Hotel e medir. Meta de um desbloqueio a cada 10–20 min e 6–10 h no Acesso Antecipado. Anotar em `docs/ue58/BALANCEAMENTO.md`.
- [ ] Equipe automatiza com uma renda menor, e o jogador sempre ganha mais fazendo pessoalmente.

### 6.2 Tutorial e objetivos

- [x] Dica na primeira vez de cada sistema (balcão, celular, bar, passeio, cada negócio, piscina, recepção, sinuca), usando o `tutorial.json` que já existe.
- [x] Objetivo atual sempre visível e o próximo desbloqueio mostrado no celular ("faltam R$ 1.200 e fama 4 para a piscina").
  Decisões (06/11):
  - `tutorial.json` ganhou dica para todo alvo de E que o jogador usa (bancada e copo do bar, mesa suja, confusão na
    praia, moradores, Seu Tibúrcio, elevador, caiaque à deriva, pingue-pongue, coletes/história/espécies do passeio,
    água e mirante da trilha) e uma por negócio (`biz:<id>`). O teste `MareAlta.Gameplay.TutorialTips` reprova se um
    alvo ou negócio novo ficar sem dica.
  - Balcão de negócio: na primeira vez a dica do próprio negócio (mesmo sem ninguém na fila); numa visita seguinte, a
    dica geral do balcão (funcionário a 60%). Fica em `AMareController::StartBusinessGame`, que também abre pelo QA.
  - `UMareSimulation::NextUnlockText`: a expansão mais barata com os requisitos comprados e tudo o que falta para ela
    (dinheiro, nível de fama e a história da vila), ou "já dá para comprar no celular". Aparece no bloco de Missões do
    HUD (substitui a antiga "Próxima meta", que só falava de dinheiro) e no topo da aba Resort do celular.
  - Visto na foto: com a janela do editor estreita (viewport ~1040×940) o celular sai cortado à esquerda; em 16:9
    está inteiro. Fica para a seção 7 (opções de resolução e proporções 4:3/5:4).
  - Prova: `docs/ue58/graphics-reference/tutorial_next_unlock.jpg` (dica do balcão + Missões no HUD; aba Resort).

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
