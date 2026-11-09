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
- [ ] (A) Praia norte, lado oeste (x -150 m, y 880 m): duas placas marrons quadradas e planas na beira d'água, parecendo
  caixa crua. Identificar a peça e trocar ou remover.
- [ ] (M) Enseada oeste (x -150 m, y -80 m): retângulos brancos lisos, um dentro d'água rasa e outro na areia.
- [ ] (M) Costa sudeste (x 300 m, y -80 m): água rasa com manchas escuras irregulares.
- [ ] (M) Gramados da costa (sudoeste e sudeste): verde muito saturado e uniforme, sem variação, com pedras pousadas
  como peças soltas.
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
- [ ] (M) Água em volta do píer à noite verde-neon sob os postes.
- [ ] (B) Costa oeste vista do alto à noite: retângulo escuro de sombra recortada (limite de distância das sombras).
- [ ] (B) Ponta do farol à noite: lajes de pedra parecem recortes pretos chapados.

## 3. Coisas pequenas (casas, quiosque, hotel, móveis e decoração)

- [x] (A) Anexo do banheiro da casa do herói sem telhado. O "cilindro vermelho" escondido de manhã era o telhado dele,
  que atravessava 27 cm da parede da sala. Voltou, encurtado até a parede.
- [ ] (M) Anexo do banheiro: parede lisa, sem janela nem detalhe, parecendo caixa.
- [ ] (B) Janela da casa do herói: moldura pequena (espelho ou quadro do banheiro) colada no vidro, vista de fora.

Sondagem das coisas pequenas: 33 vistas de perto, com tudo liberado (`D:/CodexTemp/detail`, script
`D:/CodexTemp/claude/ue/detail.py`).

**Bar do Coqueiro**
- [ ] (A) Uma mão saindo do tampo do balcão ao lado do prato de pastel (braço de cliente sentado atravessando o
  balcão).

**Quiosque**
- [ ] (A) A palavra "ENTRADA" escrita na porta do armário do fogão (texto de placa fora do lugar).
- [ ] (M) Bloco creme liso no fim do balcão, sem detalhe (parece caixa crua).

**Pousada**
- [ ] (M) Placa azul em branco num poste na frente da recepção (sem texto nem desenho).
- [ ] (B) Os três bangalôs são idênticos por dentro (mesmo quadro, mesma cama, mesmas cores).

**Casa do herói**
- [ ] (M) Banheiro: o toalheiro está pregado sobre o batente e atravessa a porta.
- [ ] (B) Cozinha: vasinho de planta no chão, no canto.

**Grand Hotel**
- [ ] (M) Saguão, lado oeste: três "portas" que são só placas marrons na parede, sem batente nem maçaneta.
- [ ] (M) Suíte: parede divisória (a da TV) com textura de reboco manchado, como pintas cinza.
- [ ] (M) Suíte: quarto grande quase vazio; a cama fica sozinha num piso enorme.
- [ ] (B) Suíte: sofá antigo de tecido estampado destoa do estilo moderno do hotel.
- [ ] (B) Quartos 302 e 303: painel branco liso encostado na parede do banheiro (toalheiro sem detalhe).

**Vila**
- [ ] (A) Caminhão vermelho parado no meio da rua principal: um caixote vermelho liso, sem portas nem lanternas, com um
  galão azul ao lado (sobra do ônibus ou do food truck).
- [ ] (B) Tampas de bueiro redondas e lisas no calçamento.

**Conferido e ok:** saguão (sinuca, pingue-pongue, placar, poltronas, plantas), recepção do hotel, corredor dos
quartos, cômodos da casa (sala, quarto, cozinha), cozinha e geladeira do quiosque, mesas do bar, quarto dos bangalôs,
fachadas e ruas da vila.

## Não são defeitos do jogo

- Faixas verticais nas bordas das fotos ao entardecer e à noite: vêm da captura `HighResShot`, não do jogo.
- Fotos com câmera dentro de copa de árvore ou de tronco: pose ruim da sondagem.
