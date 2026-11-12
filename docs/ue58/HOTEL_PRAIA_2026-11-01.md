# Grand Hotel acessível e praia caribenha — 01/11/2026

Pedido do usuário: entrar no Hotel 5★ (decoração e funcionalidade), praia mais bonita com
areia mais branca e água clara tipo Caribe, e corrigir as "ondas quadradas".
Branch `codex/ue58-migration`, Unreal 5.8.3. Trabalho na engine pelo MCP do editor.

## Hotel 5★

**Causa:** o térreo da torre era um núcleo maciço com um plano pintado de "lobby" atrás do
vidro, e uma coluna da galeria ficava no eixo da entrada. Nada era acessível.

- `tools/ue58/hotel_lobby_shell.py` (Blender 5.2 portátil, background) parte do glTF importado
  (`SourceArt/Models/World_2365.gltf`, cópia original em `D:/CodexTemp/hotel-lobby/orig`):
  remove o núcleo, a coluna central e o vidro do vão da porta, e cria a casca do lobby com os
  próprios materiais `MA_…` da torre: paredes, rodapé/faixa, forro com vigas de madeira,
  4 colunas torneadas, balcão de recepção (frente ripada, tampo de pedra), painel de ripas,
  dois elevadores com batentes e botoeiras, floreiras. Exporta também as partes Nanite
  opaca/vidro. Mesmos limites; soma de triângulos validada pelo `mare_nanite_architecture.build`.
- `Content/Python/mare_hotel_lobby.py` (ferramenta MCP `hotel_lobby`): reimporta colisor
  (complexo como simples) e proxies; mobilia com 20 modelos **Poly Haven CC0** (sofás,
  poltronas, mesas, pufe, plantas, vasos, quadros, pendentes) com base calculada pelos limites
  reais da malha; luzes quentes; tudo marcado `Region_grand_hotel` (oculto até a compra).
  Layout em `Content/Data/hotel_lobby.json`; créditos em `CREDITS.md`.
- Vidro do hotel: substituição só nos slots de vidro do proxy pelo `M_ClearWindowGlass`
  (vidro neutro deixado pelo Codex, agora validado), sem tom azul.
- Gramado PCG: 57 instâncias nasciam dentro do antigo núcleo; removidas e a área da torre
  excluída em `mare_grass.excluded()`. `grass_coverage.json`: 177.397 instâncias.
- Função: alvo **Recepção do Grand Hotel** no balcão (aparece após a compra) abre o celular
  na aba Resort com ocupação prevista, diária e resultado da última noite. Ao dormir,
  `HotelNight` (port fiel da v1.0 Godot): 32 suítes, diária 220, restaurante 1,7×35 por
  hóspede, equipe −900, avaliações 4,3–5★ e fama; ocupação = 0,42 + 0,12·(nota−4) +
  0,03·(fama−7), limitada a 15–98 %. Temporada, festas e árvore de melhorias ainda neutras.

## Praia caribenha e ondas

- `mare_materials.build_ground`: areia seca clareada de forma multiplicativa (preserva o
  grão), segunda amostragem girada da areia para quebrar a grade de repetição; areia molhada
  bege-clara. Grama inalterada.
- `mare_materials.build_water`: turquesa claro nas águas rasas → azul profundo ao largo,
  absorção menor (mais transparente), espalhamento verde-azulado, espuma branca em manchas
  orgânicas (antes eram retângulos).
- **Ondas quadradas:** a malha do mar tinha quadrados de ~10 m para ondas de ~7 m.
  `tools/ue58/gen_ocean.py` gera grade graduada: 0,75 m na praia jogável, crescendo até 24 m
  no alto-mar (232.680 triângulos, mesma extensão). Ondas curtas atenuadas fora da faixa densa
  e, perto da areia, a ondulação só eleva a água (sem vales expondo o fundo raso).
  Original salvo em `D:/CodexTemp/ocean-orig`.

## Validação

- Compilação MareAltaEditor OK; testes de automação pelo MCP **2/2** (inclui noite do hotel).
- PIE com save isolado `D:/CodexTemp/claude-qa-hotel`: varredura de cápsula do jogador da
  marquise até a recepção **livre**; mira na recepção e celular aberto com o painel do hotel.
- Capturas do editor e do PIE: `D:/CodexTemp/hotel-lobby/shots`, `D:/CodexTemp/beach`
  (antes/depois). Seleção em `graphics-reference/hotel-praia-20261101/`.
- QA do executável ganhou `hotel_entrance_walkable` e `hotel_reception_after_purchase`.

## Limitações

- Hóspedes ainda não caminham pelo lobby (NavMesh do interior não reconstruído); quartos,
  restaurante e spa do hotel seguem como exterior.
- A borda entre água e areia continua reta onde o terreno é reto.
- Guarda-sol listrado e algumas peças antigas da praia ainda são low poly: próximo polimento.
- Desempenho com a nova malha do mar ainda não medido no perfil gráfico.
