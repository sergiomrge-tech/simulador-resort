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
- [ ] (M) Face do morro vista do mar ao norte ainda clara demais (cone bege acima da mata). Escurecer ou cobrir com
  vegetação na encosta.
- [x] (A) Praia norte e outras 8 praias: placas marrons quadradas na beira d'água. Eram fatias de 54 m da rocha
  `coast_line_01` achatadas. Testei pedregulho e conjunto de rochas (ficaram escuros ou flutuando) e escondi o grupo; as
  outras rochas de arenito ficam.
- [x] (M) Enseada oeste e costa sudoeste: retângulos lisos e degraus sob a água rasa. Eram três coisas juntas: o fundo de
  areia da ilha ainda seguia a reta da praia antiga da baía e, fora dela, ficava areia molhada escura sem cáusticas; o
  terreno novo da ilha deixava prateleiras retas por cima dos blocos de morro submersos; e a saia desses blocos descia
  até −2,2 m. Agora o fundo é areia clara com cáusticas em toda a volta, o terreno novo não cobre os blocos de morro
  (`gen_island_terrain.py`) e o morro vira areia debaixo d'água, levantado no material (−2,2 m vira −1,15 m).
  Conferido em foto nas duas costas e na baía (`D:/CodexTemp/hill10`).
- [ ] (B) Costa oeste: alguns riscos escuros finos na água rasa, nas emendas entre o morro e o terreno novo.
- [x] (A) Rochas flutuando nas encostas do oeste (foto do Sergio). Assentadas com `mare_mountains.seat_rocks`: 31 pedras
  em cima das trilhas e 25 enterradas retiradas, medição final com 0 pedras flutuando mais de 30 cm; 621 árvores que
  atravessavam 646 pedras retiradas (`clear_trunks`). Conferido em foto (`D:/CodexTemp/rocks2`).
- [x] (M) Costa sudeste: água rasa com manchas escuras. O chão da ilha mostrava grama e folhas debaixo d'água; agora
  vira areia abaixo do nível do mar. As manchas que sobraram são capim marinho (natural).
- [x] (M) Gramados da costa: verde muito saturado e uniforme. Agora com tom menos neon e mais variação.
- [ ] (M) Chão da mata em alguns trechos (x 0, y 400 m): verde-claro liso, quase sem folhas nem textura.
- [ ] (B) Água rasa com a malha de cáusticas muito regular, vista do alto.

## 2. Luz, céu e noite

- [x] (A) Água rasa embaixo d'água estourada de branco ao meio-dia: exposição travada em EV 10 contra cena em 15,5.
  O teto agora acompanha a profundidade.
- [x] (A) Lua cheia de verdade no céu, com mapa da NASA, nascendo do lado oposto ao sol e iluminando a noite (antes
  era uma luz fraca e parada). Tirado o ponto branco no meio dela.
- [x] (A) Estrelas, Via Láctea e aurora sobre o mar à noite.
- [x] (A) A cúpula do céu tinha colisão e bloqueava a mira (TV, sofá, cama, conversas) no teste do executável.
  Colisão desligada.
- [x] (M) Água em volta do píer à noite verde-neon. Postes sobre o mar com luz mais fria (4300 K). Falta conferir em
  foto noturna.
- [ ] (B) Costa oeste vista do alto à noite: retângulo escuro de sombra recortada (limite de distância das sombras).
- [ ] (B) Ponta do farol à noite: lajes de pedra parecem recortes pretos chapados.

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
- [ ] (B) Os três bangalôs são idênticos por dentro (mesmo quadro, mesma cama, mesmas cores).

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

## Não são defeitos do jogo

- Faixas verticais nas bordas das fotos ao entardecer e à noite: vêm da captura `HighResShot`, não do jogo.
- Fotos com câmera dentro de copa de árvore ou de tronco: pose ruim da sondagem.
