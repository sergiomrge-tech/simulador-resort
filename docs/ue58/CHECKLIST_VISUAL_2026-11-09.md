# Checklist de erros visuais — sondagem de 09/11/2026

Pedido do Sergio: "faça uma sondagem total do mapa do jogo, faça um check list de todos os erros visuais que precisa de
correção" e, em seguida, "quero uma sondagem das pequenas coisas: quiosque, hotel, quartos, sala de jogos, recepção,
casas, ruas, móveis, itens decorativos".

Fontes:
- Grade de 150 m sobre a ilha inteira, com uma foto aérea e uma na altura dos olhos em cada ponto (70 fotos,
  `D:/CodexTemp/survey`, script `D:/CodexTemp/claude/ue/survey.py`).
- Volta pelos 48 locais às 11h, 18h e 21h30 (`D:/CodexTemp/tour*`).
- Sondagem das coisas pequenas (seção 3, abaixo).

Legenda: [x] corrigido hoje · [ ] falta corrigir · (A) alta, (M) média, (B) baixa prioridade.

## 1. Mapa (sondagem grande)

- [x] (A) Encostas íngremes e a face do morro com uma textura cinza em zigue-zague, parecendo calçada. Era a rocha
  procedural feita de manhã com senos. Agora é ruído em 5 camadas: rocha escura com fendas e manchas de musgo.
- [x] (M) Face do morro vista do mar ao norte clara demais (cone bege acima da mata). A rocha das encostas íngremes ficou
  mais escura e com manchas grandes de vegetação verde-escura; do mar o cume agora se junta à mata (`D:/CodexTemp/forest2`).
- [x] (A) Praia norte e outras 8 praias: placas marrons quadradas na beira d'água. Eram fatias de 54 m da rocha
  `coast_line_01` achatadas. Testei pedregulho e conjunto de rochas (ficaram escuros ou flutuando) e escondi o grupo; as
  outras rochas de arenito ficam.
- [x] (M) Enseada oeste e costa sudoeste: retângulos lisos e degraus sob a água rasa. Eram três coisas juntas: o fundo de
  areia da ilha ainda seguia a reta da praia antiga da baía e, fora dela, ficava areia molhada escura sem cáusticas; o
  terreno novo da ilha deixava prateleiras retas por cima dos blocos de morro submersos; e a saia desses blocos descia
  até −2,2 m. Agora o fundo é areia clara com cáusticas em toda a volta, o terreno novo não cobre os blocos de morro
  (`gen_island_terrain.py`) e o morro vira areia debaixo d'água, levantado no material (−2,2 m vira −1,15 m).
  Conferido em foto nas duas costas e na baía (`D:/CodexTemp/hill10`).
- [x] (B) Costa oeste: alguns riscos escuros finos na água rasa, nas emendas entre o morro e o terreno novo. Feito em 10/11
  (a borda do terreno novo no mar mergulha sob o fundo; ver o item da costa oeste no fim da seção 2).
- [x] (A) Rochas flutuando nas encostas do oeste (foto do Sergio). Assentadas com `mare_mountains.seat_rocks`: 31 pedras
  em cima das trilhas e 25 enterradas retiradas, medição final com 0 pedras flutuando mais de 30 cm; 621 árvores que
  atravessavam 646 pedras retiradas (`clear_trunks`). Conferido em foto (`D:/CodexTemp/rocks2`).
- [x] (M) Costa sudeste: água rasa com manchas escuras. O chão da ilha mostrava grama e folhas debaixo d'água; agora
  vira areia abaixo do nível do mar. As manchas que sobraram são capim marinho (natural).
- [x] (M) Gramados da costa: verde muito saturado e uniforme. Agora com tom menos neon e mais variação.
- [x] (M) Chão da mata nos morros: verde-claro liso. Agora tem folhas secas em manchas (a mesma textura do terreno novo),
  só na mata (a mais de ~35 m da costa) e perto da câmera; a primeira versão, em tudo, deixou as encostas abertas marrons
  vistas do alto e foi restringida.
- [x] (B) Água rasa com a malha de cáusticas muito regular, vista do alto. A rede única de senos (repetia a cada ~5,7 m)
  agora é entortada por uma ondulação larga, soma uma segunda rede girada 37° e some em manchas. Conferido
  (`D:/CodexTemp/caust2`).

## 2. Luz, céu e noite

- [x] (A) Água rasa embaixo d'água estourada de branco ao meio-dia: exposição travada em EV 10 contra cena em 15,5.
  O teto agora acompanha a profundidade.
- [x] (A) Lua cheia de verdade no céu, com mapa da NASA, nascendo do lado oposto ao sol e iluminando a noite (antes
  era uma luz fraca e parada). Tirado o ponto branco no meio dela.
- [x] (A) Estrelas, Via Láctea e aurora sobre o mar à noite.
- [x] (A) A cúpula do céu tinha colisão e bloqueava a mira (TV, sofá, cama, conversas) no teste do executável.
  Colisão desligada.
- [x] (M) Água em volta do píer à noite verde-neon. Postes sobre o mar com luz mais fria (4300 K). Conferido em foto
  noturna (10/11): a água junto aos postes fica verde-esmeralda, sem o neon de antes.
- [x] (B) Costa oeste vista do alto à noite: retângulo escuro recortado. Conferido (10/11): é da captura `HighResShot`
  (faixas verticais a ~17% e ~83% da largura, também de dia); na captura da própria janela do jogo (`mare.Shot`) não existe.
- [x] (B) Ponta do farol à noite: lajes de pedra pretas. Conferido (10/11): são as rochas escuras da costa sob o luar, com
  a areia mais clara em volta; leitura natural, não é defeito.
- [x] (M) Rochas flutuando perto do farol (pergunta do Sergio, 10/11). As pedras estão apoiadas na laje grande
  `coast_rocks_02` (0 com a base no ar, medido com `mare_fix_0911.rocks_anywhere`); o que flutuava era a própria laje: a
  beirada avançava sobre a água com ~2 m de vão até a areia do fundo. Ganhou uma base de pedra submersa até o fundo
  (`farol_slab_base`) e a pedra que passava 2 m da beirada foi para dentro. Conferido em foto (`D:/CodexTemp/farolrocks2`).
- [x] (A) "Todas as rochas ao redor do farol estão erradas" (Sergio, 10/11, foto de um braço de laje flutuando). Refeito:
  a base submersa de 09/11 saiu; as pedras da ponta viraram matacões do Poly Haven (`point_boulders`), 34 matacões na
  beirada das lajes (`mare_coast_rocks.point_rim`), e a areia sobe até as lajes: os topos delas foram medidos
  (`mare_probe_near.shelf_map` → `SourceArt/Island/shelf_tops.json`) e o gerador do terreno troca as células de 5 m em volta
  por uma malha de 50 cm com a borda casando com as vizinhas (`gen_island_terrain.shelf_dune`). Vão sob a beirada medido
  com traços laterais: de até 60 cm para ~10 cm. Antes/depois em `D:/CodexTemp/farol_antes_depois.jpg`.
- [x] (B) Ponta do farol: faixas de água reta na praia entre o píer e o farol (o chão antigo `Maré · Ground` fica a −24..−31 cm,
  no nível do mar). O terreno cobre essa praia a −12 cm no mínimo (`gen_island_terrain`, caixa x 75–105 m, y −32,6..−23 m);
  o mapa `mare_probe_near.low_ground` só mostra mar de verdade.
- [x] (B) Costa oeste vista do alto: linha escura fina e reta na água. Era a borda do terreno novo no mar (−0,6 a −0,9 m)
  cortada numa linha da grade junto ao fundo a −1,9 m; os pontos da borda agora descem a −2,6 m, por baixo do fundo.

- [x] (M) Manchas de "areia escura" de borda nítida perto do farol (10/11): eram o topo da laje `coast_rocks_02` (a
  textura de rocha esticada lia como terra). A laje ficou mais cinza e a areia da praia cobre as partes planas e baixas e os
  vãos (`mare_coast_rocks.slab_material`); fotos `D:/CodexTemp/slab2`.
- [x] (B) Costa oeste de perto: faixa clara de cantos retos na beira d'água (10/11). Era o morro submerso levantado pelo
  material até −0,8 m, terminando num degrau de 1 m sobre o fundo atual (−2,1 m). O levantamento foi zerado
  (`M_HillGround_PBR`); comparação com e sem em `D:/CodexTemp/lift_a` e `lift_b`.
- [x] (M) Fogueira da festa junina sem chamas (10/11): o fogo de fluido 2D estava deitado no chão. Duas folhas em pé e
  cruzadas; e os esportes de praia não acontecem em dia de festa (a festa usa o mesmo trecho da praia).
- [x] (B) Log: um pedestre da vila tentava nascer 3 vezes por segundo no mesmo ponto bloqueado por um vaso (3.451 avisos
  numa sessão). O ponto é ajustado para fora do obstáculo, e quem não cabe ao lado do líder vira pedestre de outra rota.

## 3. Coisas pequenas (casas, quiosque, hotel, móveis e decoração)

- [x] (A) Anexo do banheiro da casa do herói sem telhado. O "cilindro vermelho" escondido de manhã era o telhado dele,
  que atravessava 27 cm da parede da sala. Voltou, encurtado até a parede.
- [x] (M) Anexo do banheiro: parede lisa, parecendo caixa. Ganhou janela basculante de vidro fosco com peitoril de pedra
  e o barrado cinza da casa nos três lados (`tools/ue58/gen_annex_dress.py`, `mare_fix_0911.annex_dress`).
- [x] (B) Janela da casa do herói: "moldura pequena colada no vidro". Medido: é a janela da parede oeste da sala
  (x 42,5 m), vista de viés pela janela sul. Não é defeito.

Sondagem das coisas pequenas: 33 vistas de perto, com tudo liberado (`D:/CodexTemp/detail`, script
`D:/CodexTemp/claude/ue/detail.py`).

**Bar do Coqueiro**
- [x] (A) Mão no tampo do balcão: não é defeito. Era a mão do cliente sentado no banco de x 1000, apoiada no balcão,
  com a câmera entre os dois bancos.

**Quiosque**
- [x] (A) Tudo liso, sem textura (foto do Sergio: "tudo precisa ter sinais de desgaste"). Metade dos materiais era só uma
  cor. Agora cada superfície tem textura real do Poly Haven (CC0) recolorida e desgaste: tábuas gastas na parede e nos
  postes, tinta verde-água e creme descascando, balcão de carvalho com veio, coifa e geladeira com tinta rachada, armário
  esmaltado arranhado, azulejos com craquelado, inox com riscos e sujeira perto do chão (`mare_kiosk_wear.py`). Conferido
  em foto (`D:/CodexTemp/kiosk2`, `kiosk3`).
- [x] (A) "ENTRADA" escrito no armário do fogão e na geladeira: letreiros antigos das entradas laterais, escondidos.
- [x] (M) Bloco creme liso no fim do balcão: não é defeito. É a estante de salgados (prateleiras creme, combinando
  com a geladeira e o azulejo) vista por trás. A primeira tentativa (madeira do balcão) deixou a estante de duas cores
  e foi desfeita.

**Pousada**
- [x] (M) Placa azul em branco na frente da recepção: escondida no componente (a compra da pousada reexibia o ator).
- [x] (B) Os três bangalôs eram idênticos por dentro. O 2 ganhou aquarela do píer e lambri cor de areia; o 3, aquarela
  do quiosque e lambri azul-céu (aquarelas feitas de fotos do próprio jogo; `mare_fix_0911.bungalow_variety`). A cama
  continua igual (é o nível de quarto comprado).

**Casa do herói**
- [x] (M) Banheiro: toalha e suporte cruzando o batente. Afastados 55 cm da porta.
- [x] (B) Cozinha: vasinho de planta no chão. Conferido: é decoração de chão, fica.

**Grand Hotel**
- [x] (M) Saguão, lado oeste: "portas" que eram só placas marrons na parede. Eram 4 placas da malha da torre, de 0,9 a
  1,2 m x 2 m e a 60 cm do chão (altas demais para portas). Cada uma ganhou um painel ripado de carvalho por cima
  (`tools/ue58/gen_lobby_slat_panel.py`, `mare_fix_0911.lobby_panels`).
- [x] (M) Suíte: parede da TV, pia, banheira e bancada com reboco de pedrinhas (pintas cinza). Agora pedra clara lisa
  (`M_SuiteStone`).
- [x] (M) Suíte: quarto grande quase vazio. Agora com mesa de jantar para seis, aparador com vaso e planta no canto
  sudeste, mesinhas ao lado do sofá, pufe ao pé da cama e poltrona de leitura com mesinha no quarto
  (`mare_fix_0911.suite_extra`, chamado também por `mare_beach.place_suite`).
- [x] (B) Suíte: sofá antigo estampado, e ainda de lado para a TV. Trocado pelo `Sofa_01` de frente para a TV.
- [x] (B) Quartos 302 e 303: painel branco liso no banheiro. Conferido de frente: é a toalha de banho dobrada no
  suporte cromado ao lado da banheira, não é defeito.

**Vila**
- [x] (A) Caminhão vermelho parado no meio da rua principal: um caixote vermelho liso, sem portas nem lanternas, com um
  galão azul ao lado. É o food truck (negócio da vila) visto por trás; o "galão" é o botijão de gás dele. A traseira
  ganhou um modelo próprio (`mare_truck_rear`): duas portas com travas cromadas, dobradiças, lanternas de três lentes,
  luzes de teto, placa e degrau.
- [x] (B) Tampas de bueiro redondas e lisas. As 24 viraram tampas de ferro fundido com aro, anéis em relevo e
  textura antiderrapante (`tools/ue58/gen_manhole.py`, `mare_fix_0911.manholes`).

**Conferido e ok:** saguão (sinuca, pingue-pongue, placar, poltronas, plantas), recepção do hotel, corredor dos
quartos, cômodos da casa (sala, quarto, cozinha), cozinha e geladeira do quiosque, mesas do bar, quarto dos bangalôs,
fachadas e ruas da vila.

## Pedidos novos durante a correção

- [x] Tela de idioma antes do menu (bandeiras, 13 idiomas), só na primeira abertura (`MareLanguage.cpp`).
- [x] Dicas passando no carregamento (10/11): a tela de carregamento e a de preparo dos gráficos trocam de dica a cada
  6 s, com um esmaecer curto (`MareLoading.cpp`, QA `mare.ShowUI loading` / `warmup`).

- [x] Esportes na praia (10/11): vôlei 2 x 2 com rede, peteca em roda de três e futebol de areia 2 x 2 com traves; um
  por dia, sorteado pelo número do dia e nunca igual ao da véspera, das 9h às 17h em dia sem chuva
  (`MareBeachSports.cpp`, `Content/Data/beach_sports.json`, QA `mare.Sport volei|peteca|futebol|hold|go|auto`).
- [x] Fundo da tela inicial (10/11): primeiro a pintura em 2.5D (desliza por profundidade, `M_Title25D`); depois, a
  pedido do Sergio, o próprio jogo: uma câmera girando devagar ao redor da ilha, longe no mar (`title.json` "orbit",
  `AMareTitleCamera`, QA `mare.TitleAt 0..1`). A pintura ficou só na tela de carregamento e na de idioma.

## Não são defeitos do jogo

- Faixas verticais nas bordas das fotos ao entardecer e à noite: vêm da captura `HighResShot`, não do jogo.
- Fotos com câmera dentro de copa de árvore ou de tronco: pose ruim da sondagem.
