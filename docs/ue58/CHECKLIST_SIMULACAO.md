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
