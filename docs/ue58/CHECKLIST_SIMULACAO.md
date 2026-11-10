# Checklist da simulação do jogo inteiro

Simulação de 03/11/2026 (`tools/ue58/qa/simulate_game.py`, perfil novo `D:/CodexTemp/claude-sim-113645`, relatório e
fotos em `D:/CodexTemp/qa/sim/20261103-113749`). Da chegada de ônibus ao fim da campanha: carta, empresa, 1º dia
do quiosque, sono, as 8 expansões na ordem do jogo, os 4 capítulos, os 5 negócios, noite e recarregamento.
Em todas as 30 etapas: **0 linhas de erro no log** e **0 pessoas deslizando**; eventos cômicos dispararam sozinhos
(HUM-004, HUM-005, HUM-008). Cada item abaixo vem de dado medido ou de foto analisada; marcar `[x]` só com prova.

## Defeitos do jogo
- [x] P1 Letreiros soltos mostram o texto **espelhado** de um dos lados (visto: "Sorveteria Gelato da Maré" a partir
  da praia; antes, o food truck). O material padrão do TextRender tem dupla face. Corrigir com material de texto de
  face única e, nos letreiros soltos dos negócios, uma cópia virada para o outro lado. Conferir os 5 negócios e as
  placas de direção ("Vila", "Pousada", "Praia") dos dois lados.
- [x] P1 Clientes do bar (Duda e Vini) reprovados na auditoria de assento logo depois de comprar o bar (etapa 10_bar);
  no save antigo, com o bar comprado desde o início, eles passam. Suspeita: sentam antes da colisão das banquetas
  ficar ativa e o traço do topo da banqueta falha. Medir e corrigir.
- [x] P2 Cumeeira do telhado do Bar do Coqueiro: a ponta é um cone liso bege, sem textura (parece um balão de perto).
  Trocar por acabamento de palha com relevo.
- [x] P2 Mata do morro ao norte: a espécie `tree_small_02` (Poly Haven) tem copa verde-esbranquiçada e tronco branco
  e destoa da mata tropical ("árvores geladas" vistas da vila e do terreno do hotel). Escurecer e saturar a folhagem.
- [x] P1 Começo de jogo: com os R$ 150 iniciais, comprar estoque e contratar o atendente não cabem juntos; conferir
  que o celular avisa claramente quando falta dinheiro (contratação recusada sem mensagem = defeito) e que o
  primeiro dia é jogável só com o estoque inicial (coco 12, frutas 12, gelo 18, porções 6).

### Correções (03/11, com prova)
- Letreiros: material de texto de face única (`M_TextOneSided`) em todos os 120 textos e cópia de costas nos letreiros
  soltos dos negócios; food truck pintado nos dois lados.
- Bar: clientes cujo traço da banqueta falhou ficam em `Untraced` e são sentados de novo nos ticks seguintes;
  2ª simulação (`claude-sim-120501`): 0 falhas de assento no bar.
- Cumeeira: as quatro peças das arestas (`World_0314`) usavam um bege liso; agora usam a palha do telhado
  (`mare_hud meshmat World_0314|World_0313`), com fios no sentido da aresta (`D:/CodexTemp/beach/bar_roof3.jpg`).
- Mata: o teste com folha vermelha provou que a mudança de material chega ao render; folha de `M_HPTreeLeaf_PBR`
  mais escura e saturada e tronco cinza-castanho (`build_hp_tree`). Conferido após reabrir o editor
  (`trees_fix2.jpg`, `trees_fix3.jpg`, `hotel_glass.jpg`).
- Começo de jogo: o atendente custa R$ 240 e o caixa inicial é R$ 150; a recusa agora diz o preço e sugere atender
  sozinho (teste `Hire refusal names the cost`); a recusa de expansão também diz nome e preço. Perfil novo
  (`claude-day1-125315`), quiosque aberto sem reposição: cliente chega e pede com o estoque inicial.
- Achado extra: braço atravessando a mesa (foto do Sergio). IK apoia o antebraço no tampo quando há mesa à frente;
  `armaudit` 4/5 → 0.
- Achado extra: janelas do Grand Hotel pareciam paredes (vidro claro mostrando quartos bege vazios). Vidro próprio
  `M_HotelWindowGlass` (escuro, refletivo); paredes e aletas com reboco fino em coordenadas do mundo
  (`mare_materials.plaster_finish`): `tower_plaster2.jpg`, `grass6.jpg`.
- Achado extra: grama. Tufos `grass_medium` escuros e secos recoloridos para verde natural (`grass_hue`); grama PCG
  com verde mais escuro e textura (contraste entre lâminas e manchas amplas, `grass_tone`); corte da PCG 28–42 m.

## Roteiro da simulação (para a próxima rodada valer)
- [x] A chegada de ônibus não foi fotografada (câmera de QA dentro de uma parede): agora usa a visão do jogador.
- [x] O Grand Hotel e o salão de jogos foram recusados por regra do jogo ("precisa de fama nível 8"): incluir o
  passo de fama no roteiro e rodar de novo hotel, restaurante, recepção, salão de jogos, noite e recarregamento.
- [x] Recarregamento: comparar o que foi salvo (expansões, capítulos, negócios, empresa) em vez do caixa, que
  continua mudando com as vendas automáticas durante o carregamento.

## Conferido sem defeito
- Quiosque recém-aberto, mesas e guarda-sóis após a compra, licença de drinks, chapa de petiscos, casa ao acordar,
  pousada (recepção e bangalô), piscina (mural de orca intencional), píer dos passeios, sorveteria, aluguel de
  pranchas, food truck (letreiro pintado nas laterais), escolinha de surfe, quiosque e vila à noite.
- Tronco caído de madeira clara no morro: parecia dourado só com a luz do fim de tarde.

---

## Simulação da demo — 10/11/2026

Roteiro `tools/ue58/qa/simulate_game.py` adaptado à demo (`"demo": true`): chegada de barco, carta, empresa, 1º dia do
quiosque com atendente, sono, as 8 expansões da demo, os 4 capítulos, os 5 negócios, fim da demo, terreno do hotel
bloqueado, noite e recarregamento. Três rodadas em perfil novo; a última é `D:/CodexTemp/qa/sim/20261110-181735`
(perfil `claude-sim-qa-20261110-1816`). O dia do quiosque e o sono correm 4× mais rápido (`SIM_SPEED`).

Resultado da última rodada, nas 30 etapas: **0 linhas de erro no log, 0 pessoas deslizando, 0 em pé dentro de móvel,
0 fora do assento**; o save recarregado é idêntico ao de antes; Grand Hotel e salão de jogos continuam bloqueados com
fama e dinheiro; `ea_end_shown` gravado (a tela de fim abriu).

### Defeito do jogo
- [x] P1 **Quem senta sem ninguém olhando fica fora do assento.** Seu Tibúrcio atrás do encosto do banco do cume, com
  os braços atravessando a madeira (em todas as etapas, já na rodada de 07/11); os 4 clientes do Bar do Coqueiro à
  noite; os hóspedes do restaurante do hotel sentados no chão ao lado da cadeira. Todos com a mesma medida: 28 cm
  abaixo e 35 cm atrás do assento (52–55 cm). Causa medida no log (`hidden=1 rendered=0 tick=0`, bacia = pose em pé):
  o alinhamento desloca o corpo para a bacia animada cair no assento, mas quem não está sendo visto tem o esqueleto
  pausado (`mare.OffscreenPose`, `SetDistanceHidden`) e a bacia lida era a da pose em pé. Forçar
  `TickAnimation`/`RefreshBoneTransforms` não muda nada num esqueleto pausado. Correção: enquanto há alinhamento
  pendente (sentar ou deitar na toalha) o esqueleto anima de verdade (`PoseAwake`) e o deslocamento espera três
  quadros avaliados. Depois: Seu Tibúrcio 0–2 cm, clientes do bar à noite 3–5 cm; fotos `D:/CodexTemp/seatqa/fix_m.jpg`.
  Checagem permanente: `mare.QA seats wake` + `mare.QA seats all` (`AMarePerson::SeatError`, linha `MARE_SEATS`),
  no portão (`seats`) e em cada etapa da simulação.

### Não são defeitos (conferidos)
- Recarregamento "diferente" da rodada de 07/11: não se repete; o save volta igual.
- Aoi e Jorge "deslizando" (07/11): alarme falso resolvido em 09/11.
- Quiosque branco "de dia" às 21h30: foto tirada logo depois do pulo do relógio com a câmera em outro lugar; parado no
  quiosque por 40 s a noite sai certa (`D:/CodexTemp/simchk/noite_quiosque_40s.png`).
- Atendente curvado sobre a bancada em fotos seguidas: é o gesto de arrumar o balcão; duas fotos com 4 s de intervalo
  mostram posturas diferentes.
- Fila da sorveteria "colada": 95 cm por pessoa no código, achatada pelo ângulo da foto.
- Painel branco com letras sobre o toldo do aluguel: é o telhado branco do quiosque com a placa em pé na borda.
- Cleber (comendo) apontado uma vez pela auditoria antiga: medido no meio da transição de sentar.

### Roteiro (para a próxima rodada valer)
- [x] O comando `mare.QA buy` compra também o que é do jogo completo (de propósito): na demo o roteiro não compra mais
  o hotel; a recusa da compra do jogador é o teste "Hotel not for sale".
- [x] Dia 1 sem atendimento (a reposição zerava o caixa e a contratação era recusada): caixa para contratar antes.
- [x] Câmeras: bar (estava dentro do telhado) e souvenir (de cara para a parede).
- [x] Noite: 30 s depois do pulo do relógio.
- [x] Tela de fim da demo fotografada quando abre (o fechamento da etapa anterior a escondia).
- [x] A auditoria antiga de assento (`seataudit`) só mede móveis do tamanho de cadeira: bancos ficam para a medida nova.

### Achado do Sergio durante a simulação
- [x] Banhista de bruços fora da toalha, com as pernas sobre a esteira vizinha (foto do Sergio, 10/11). Mesmo defeito
  dos assentos: os banhistas só nascem com o herói a mais de 25 m, então sempre deitam sem ninguém olhar e eram
  alinhados com o esqueleto pausado. Os dados das toalhas batem com as toalhas do cenário (0–1 cm,
  `mare_rest_audit.towels`). Com a correção: 3 banhistas a 3–8 cm do centro da toalha, bacia 11–13 cm acima do pano
  (`mare_rest_audit.bathers`), fotos `D:/CodexTemp/restqa/fix_m.jpg`. Checagem permanente: `AMarePerson::LieError`,
  linha `MARE_RESTS` do `mare.QA seats all`, no portão (`seats ... lying`) e na simulação.

### Melhorias pequenas anotadas
- [x] Tochas tiki do quiosque apagadas à noite (10/11). A chama (`World_1273`, 11 no mapa: 4 no quiosque, 7 no terraço da
  piscina do hotel) era um cone laranja sem brilho, de dia e de noite. Material `M_TorchFlame` (`mare_torch.py`): fogo que
  brilha e tremula, miolo amarelo e ponta laranja, cada tocha fora de fase; de dia a tocha fica apagada (sem chama). Uma
  luz quente por tocha (`BuildLamps`, 38 cd, 1900 K). Duas armadilhas medidas: o espaço "local" de uma instância é o do
  ator (a chama virava uma velinha de 10 cm; usar INSTANCE) e brilho 26 saía branco, 1–4,5 saía marrom (ficou 3–12).
  Fotos `D:/CodexTemp/torchqa/v4_m.jpg`.
- [x] Folhinhas verde-escuras espalhadas na areia da praia (foto do benchmark): conferido de perto (10/11). São as algas
  de enfeite da praia, com uma estrela-do-mar e pedrinhas ao lado, apoiadas na areia e na escala certa; não é defeito
  (`D:/CodexTemp/simchk/areia_zoom.jpg`).
