# Como continuar o Maré Alta Resort (passagem de bastão — 19/10/2026)

Este arquivo é para qualquer assistente/IA (ou pessoa) que vá continuar o projeto. Leia também o `CLAUDE.md`
na raiz: ele é o "palácio de memória" com TODAS as regras e erros já cometidos. Siga as regras dele.

## 1. Estado atual
- Versão publicada: **v1.0.0** (instalador completo entregue ao Sergio, instalado em `D:\Games\MareAltaResort`).
- Em andamento: **v1.0.1** (correções), parcialmente feita e já comitada (commits `a575188` e `1be22de`).
- O jogo instalado do Sergio está em **Vulkan** (o `override.cfg` dele foi trocado; o DirectX 12 dava tela preta).
- Save de demonstração com tudo liberado no PC dele: **Slot 3** (`save_slot3.json`).

## 2. Regras do Sergio (resumo — detalhes no CLAUDE.md, "Hall de entrada")
- **Proibido low poly e proibido "bolas e quadrados"** (esferas/caixas/cilindros fazendo de objeto). Todo objeto visível vem de
  **asset gratuito CC0** (Poly Haven, Kenney, Quaternius, KayKit, ambientCG, OpenGameArt, itch.io) ou é **modelado no Blender (bpy)**
  com malha detalhada. Registrar fonte em `CREDITS.md` e download em `tools/fetch_assets.py`.
- Ao ver defeito visual, **corrigir na hora**, não só avisar. **Nunca entregar nada quebrado**: testar antes.
- Entregar **patch pequeno** quando ele já tem o jogo instalado (não o instalador de 1 GB), testado no pacote exportado.
- Commit + push no GitHub a cada lote. Respostas em português do Brasil.

## 3. Ambiente
- Godot **4.5.1** (Forward+, GDScript). Blender via `python3` com módulo `bpy` (os scripts `tools/gen_*.py` rodam com `python3 tools/gen_X.py`).
- Assets baixados **não vão no git**: rodar `python3 tools/fetch_assets.py` antes de importar/exportar.
- Depois de criar/alterar modelos ou texturas: `godot --headless --path . --import` → `python3 tools/vram_textures.py` → importar de novo.
- Teste automático: `tests/loop_test.gd` precisa dar **LOOP_TEST PASS**. Rodar com
  `godot --path . --rendering-driver opengl3 --rendering-method gl_compatibility -- --loop-test --quality=0`.
- Prints de conferência: `godot --path . -- --shot=NOME --cam=x,y,z,yaw,pitch[,hora] [--v1]` (salva em `shots/NOME.png`).
  `--v1` libera tudo (negócios, capítulos, hotel 5★). Pitch negativo olha para baixo; y do `--cam` é o corpo (câmera = y+1,65).
- Instalador completo: `bash tools/build_release.sh` (NSIS; limite de 2 GB para exe+pck — ver CLAUDE.md).
- Patch: `bash tools/build_patch.sh <commit base>` (ver "Sala do Patch" no CLAUDE.md).

## 4. O que já foi feito na v1.0.1 (comitado)
1. `tools/prune_export.py`: não exclui mais a pasta `assets/models/qnat` (arbustos/plantas Quaternius). No instalador v1.0 ela
   ficou de fora e o jogo mostrava "placas redondas" no lugar dos arbustos. Também procura uso por caminho.
2. `scripts/real.gd`: `Real.ALIAS` redireciona todas as chaves Kenney low-poly (`k:coconut`, `k:bottle`, `k:pineapple`, `k:orange`,
   `k:frappe`, `k:cup`, `k:glass`, `k:cocktail`, `k:bread`, `k:barrel`, `k:crate-bottles`, `k:campfire_*`, `k:rock_small*`,
   `k:log_large`, `k:tent_smallOpen`, `k:boat-row-large`, `k:flag-pennant`, `k:tool-paddle`) para modelos detalhados.
   Imprime `REAL_MISSING <chave>` no log quando um modelo não existe.
3. `tools/gen_food.py` (Blender) gera: coconut_green, coconut_open, pineapple, orange, frappe, cup_plastic, glass_juice, cocktail,
   campfire_logs, beach_flag, beach_spade, boat_hull (já em `assets/models/gen/*.glb`).
4. `scripts/reef.gd`: corais com altura limitada pela profundidade (antes furavam a água = "pontas no mar").
5. `tools/gen_beach_props.py` e `tools/gen_code_props.py`: `box()` girava as peças em volta da origem do mundo — corrigido
   (espreguiçadeira, venezianas, treliça, revistas da banca). Regerados.
6. `project.godot`: limites de descritores do D3D12 aumentados.

## 5. O que FALTA (fazer nesta ordem)
1. **Pessoas travadas em pé na mesa do quiosque** (dois clientes no mesmo lugar, rótulos de pedido sobrepostos, em pé dentro
   das cadeiras). Investigar a reserva de lugares em `scripts/village_life.gd` (mesas do quiosque, expansão `kiosk_tables`) e a
   regra de sentar do CLAUDE.md ("Sala dos Assentos"). Cada lugar só pode ter um cliente; quem não acha lugar espera em pé fora da mesa.
2. **Conferir em prints do jogo** (com `--v1` quando precisar): prateleira de garrafas do quiosque (x≈38, z≈-13), balcão com frutas
   e coco aberto, carrinho de cocos, pilhas de coco perto das casas/barracas, fogueira da festa junina (`--event=junina`), tendas da
   quermesse (`--event=quermesse`), barco de pesca (`g:boat_hull`, conferir altura do fundo 0,40 m e o mastro), castelo de areia
   (bandeira e pazinha). Ajustar tamanhos/posições (o `Real.place` usa a altura pedida; alguns modelos novos têm canudo e ficam
   menores — ver `ALIAS_H` em `real.gd`).
3. Rodar `--primcheck` e `--floatcheck` (ver CLAUDE.md, "Sala da Faxina") e corrigir o que aparecer.
4. Procurar outros itens low-poly que ainda restem (Quaternius de capim/flores/pedrinhas é estilizado mas aceito; o Sergio gostou
   do arbusto Quaternius). Qualquer outro "k:" novo deve ganhar alias para modelo detalhado.
5. Aplicar no `tools/build_release.sh` o smoke test sobre o **pacote exportado** (`--main-pack build/win/MareAltaResort.pck`,
   `--v1`, procurar `not found`, `SCRIPT ERROR` e `REAL_MISSING` no log). Hoje o smoke roda sobre o projeto e não pega pastas
   que ficaram fora do pacote.
6. LOOP_TEST PASS.
7. Atualizar `CREDITS.md` (modelos de `gen_food.py`; Poly Haven `dead_tree_trunk`, `stone_fire_pit`, `boulder_01`,
   `sand_rocks_small_01`, `wooden_crate_02`, `Barrel_01`, `croissant`) e rodar `python3 tools/gen_item_catalog.py`.
8. Gerar o **patch 1.0.1** com base na v1.0 instalada (base sugerida: commit `51921df`, que publicou a v1.0.0) e conferir que o patch
   leva `assets/models/qnat/*` (arbustos) e os novos `assets/models/gen/*.glb`. Testar o patch sobre o pck da v1.0 antes de entregar.
   Atualizar `docs/latest_version.txt` e copiar o .exe do patch para `patches/`.

## 6. Mapa rápido do código
- `scripts/resort_core.gd` (autoload `Core`): economia, save (v6), expansões. `scripts/progression.gd` (`Core.prog`): fama, árvore,
  negócios, equipe, temporadas, receitas, capítulos, hotel. `scripts/prog_data.gd` (`PD`): dados da evolução.
- `scripts/world.gd` + `scripts/world_village.gd`: mapa (resort, praia, vila). `scripts/biz_world.gd`: negócios no mapa.
  `scripts/hotel_world.gd`: Grand Hotel 5★. `scripts/event_fx.gd`: festas/eventos. `scripts/village_life.gd`: clientes e moradores.
- `scripts/phone_ui.gd`: celular (todos os apps). `scripts/minigame.gd`: minijogo dos negócios.
- `scripts/real.gd`: carrega modelos reais (`g:` Blender, `k:` Kenney, `q:` Quaternius, nome = Poly Haven).
- `tools/gen_*.py`: modelos feitos no Blender. `tools/fetch_assets.py`: baixa os assets CC0.

## 7. Atualização via GitHub MCP (19/10/2026 — validação Godot pendente)
- O `main` avançou após o checkpoint `25e4554`. O commit `886c2de` contém reserva de assentos por `owner`, fila de espera e `tests/kiosk_regression.gd` (necessário executar no Godot).
- `tools/build_release.sh` já possui smoke de pacote exportado via `--main-pack`, `--v1`, verificação de screenshot, `not found`, `SCRIPT ERROR` e `REAL_MISSING`.
- `CREDITS.md` atualizado com os 12 modelos novos de `gen_food.py` e 7 fontes Poly Haven CC0 (commit `0bd920f`).
- `tools/fetch_assets.py` agora gera, depois das texturas, os modelos de `gen_beach_props`, `gen_code_props`, `gen_business`, `gen_hotel` e `gen_food` ausentes, e confere as saídas (commits `4116230` e `4e85874`).
- `tools/build_patch.sh` agora inclui a pasta `assets/models/qnat` e os GLBs novos/corrigidos da v1.0.1 mesmo quando ignorados pelo Git; aborta se faltarem (commit `cb7ff42`).
- **Não foi executado Godot neste ambiente:** o computador Desktop Commander estava offline, sem clone local executável da pasta `resort 2`; nenhuma captura, import, `--primcheck`, `--floatcheck`, `LOOP_TEST PASS`, teste do PCK ou do patch sobre a v1.0 foi confirmado. **Não anunciar patch pronto.**
- **Falta:** clonar localmente, baixar/regenerar assets, importar duas vezes com `vram_textures.py`, conferir prints do quiosque e todos os modelos novos, corrigir qualquer defeito, rodar testes e smoke reais, gerar catálogo com `tools/gen_item_catalog.py`, exportar patch com base `51921df`, testar contra PCK da v1.0 instalada, só então atualizar `docs/latest_version.txt` e publicar `patches/`.
