# Auditoria geral do jogo — checklist de correções

Pedido do usuário (01/11): andar por todo o jogo, listar o que precisa ser corrigido e corrigir.
Tour automático pelo MCP (`game_tour`: 26 câmeras — vila, casas, quiosque, praia, píer, farol,
hotel e uma por região de expansão/negócio) + capturas no PIE. Pranchas em `D:/CodexTemp/tour`.
Legenda: [x] corrigido e conferido em captura · [~] parcial · [ ] pendente.

## Corrigido nesta leva

- [x] **Janelas opacas das casas da vila** (`janela` 193 e `batente` 41): o vidro ficava colado
  na parede e mostrava o reboco. Agora vidro escuro polido (`M_WindowPane_PBR`) refletindo o céu,
  com cortina sugerida. Demais vidros com interior (casa do jogador, quiosque, hotel, lojas) usam
  o vidro neutro transparente `M_ClearWindowGlass`. Ferramenta: `caribbean_coast windows`.
- [x] **Piscinas da pousada e do hotel sem água** (superfície verde opaca): o shader de piscina da
  Godot caiu para um verde opaco no export. Novo `M_PoolWater_PBR` (água de camada única, azul
  piscina, ondulação leve) só nos dois planos de água. Conferido no PIE.
- [x] **Espuma do mar em manchas espalhadas**: agora faixas longas de arrebentação paralelas à praia.

- [x] **Arbusto vermelho e entulho dentro da piscina da pousada**: 25 grupos MultiMesh da Godot
  (grama, conchas, seixos, flores, arbustos, copas) foram exportados sem a transformação por
  instância e ficaram empilhados na origem do mundo, que é o centro da piscina. Removidas 5.729
  instâncias do nível e do `world.json` (lista guardada em `Content/Data/stacked_origin_removed.json`).
  Terreno e morros, com pivô legítimo na origem, foram preservados.

- [x] **Morros costeiros sem mata** (atrás do farol e pontas da praia): área da vegetação
  estendida às pontas; 19.324 instâncias CC0 só sobre os morros (nada na praia/vila).

## Pendente (próximas levas, em ordem)

- [ ] Reconstruir os grupos perdidos (grama, conchas, seixos, flores) nas posições corretas,
  quando houver o export Godot com transformações por instância ou por PCG equivalente.

- [x] Piscinas: água clara e transparente (turquesa), conferido no PIE.
- [x] Janelas acesas à noite: `MPC_MareTime.Night` escrito pelo `UMareVisualWorld`; ~55% das janelas acendem (aleatório por instância). Conferido às 22h no PIE.
- [x] Palmeiras (4 variantes, 171 instâncias): frondes de cartão trocadas por frondes modeladas (raque curvada, ~90 folíolos por fronde, 18 frondes + 4 jovens), material de folhagem com luz atravessando (`M_PalmFrond_PBR`); troncos/cocos mantidos (`tools/ue58/palm_fronds.py`).
- [x] Amendoeiras conferidas: 356 mil vértices com folhas modeladas, não são low poly. As "bolhas" eram as `Copas` empilhadas na origem (removidas).
- [x] Vela plana do `mastro` agora enfunada (barriga máxima no terço da testa, `tools/ue58/billow_sail.py`); a vela da jangada já tinha curvatura.
- [x] Hotel: recepcionista e 4 hóspedes no lobby após a compra (conversando, check-in, elevador); QA `hotel_lobby_guests`.
- [ ] Hotel: restaurante/academia/quartos ainda sem interior utilizável.
- [ ] Medir desempenho com mata, mar graduado, palmeiras e lobby (exige executável — só quando o usuário pedir).
- [ ] Ícones de TextRender e linhas laranja aparecem só no editor (não no jogo) — sem ação.

Validação desta leva: capturas antes/depois em `graphics-reference/auditoria-20261101/`.
