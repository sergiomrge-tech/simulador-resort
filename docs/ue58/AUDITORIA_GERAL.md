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

## Pendente (próximas levas, em ordem)

- [ ] Reconstruir os grupos perdidos (grama, conchas, seixos, flores) nas posições corretas,
  quando houver o export Godot com transformações por instância ou por PCG equivalente.

- [x] Piscinas: água clara e transparente (turquesa), conferido no PIE.
- [x] Janelas acesas à noite: `MPC_MareTime.Night` escrito pelo `UMareVisualWorld`; ~55% das janelas acendem (aleatório por instância). Conferido às 22h no PIE.
- [ ] Palmeiras com folhas em cartões chapados (low poly) — buscar/modelar palmeira detalhada.
- [ ] Amendoeiras com copa em "bolhas" facetadas (`tree_amendoeira`).
- [ ] Velas dos barcos de praia chapadas, sem tecido/costuras.
- [ ] Hotel: hóspedes no lobby; restaurante/academia/quartos sem interior utilizável.
- [ ] Ícones de TextRender e linhas laranja aparecem só no editor (não no jogo) — sem ação.

Validação desta leva: capturas antes/depois em `graphics-reference/auditoria-20261101/`.
