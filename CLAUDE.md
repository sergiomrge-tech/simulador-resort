# Maré Alta Resort — Palácio de Memória

> **Para continuar o trabalho (outra IA ou pessoa): leia primeiro [`docs/CONTINUAR.md`](docs/CONTINUAR.md).**

> Instruções comuns a todas as IAs: [AGENTS.md](AGENTS.md). Este arquivo guarda
> lições de várias versões; referências antigas a preparo, óculos, cores muito
> saturadas, versão 1.0.x e entrega obrigatória por NSIS não substituem o guia
> vigente. Preserve as lições técnicas, seguindo as preferências atuais do usuário.

Regras aprendidas com erros reais deste projeto. Leia antes de mexer em qualquer coisa.
Cada "cômodo" guarda um tipo de erro: o que aconteceu, a regra e como conferir.
Ao corrigir um erro novo, acrescente uma linha no cômodo certo (ou crie um cômodo).

Projeto: Godot 4.5.1, Forward+, GDScript, estilo cartoon (referência: Barfender CO-OP).
Base de trabalho: v0.6.5 recuperada; versões atuais em `project.godot` / `export_presets.cfg`.

---

## 🚪 Hall de entrada — regras fixas do Sergio
- **Acabamento (23/10):** contorno de tela espesso e opaco desenhava nervuras escuras em toda folha/roupa. Reduzir espessura/opacidade e antecipar fade preserva silhuetas sem ocultar mapas. Água HD usa gradientes largos, brilho suave e espuma smoothstep; manter a fórmula inversa de profundidade do outline para não reintroduzir tremor de piso. Conferir Vulkan perto do balcão, mar diurno e cruzeiro noturno.
- **Praia/balcão (23/10):** quiosque/mesas girados 180° para -Z. KioskBeachFrame mantém coordenadas autorais antigas nos modelos; spots/block_rects e rotas são globais convertidos por kiosk_point/kiosk_local. Operação usa o mesmo frame para móveis; funcionários pertencem à vila e recebem posições globais. Não usar station.position como global. Balcão tem staff_approach interno; mesas mantêm approach. Recalcular também layout de personalização, não apenas malhas.
- **Mira/reposição (23/10):** cliente sentado tem alvo maior e seleção tolerante de 11°/3 m acima do tampo, com teste físico de visibilidade; estações miradas diretamente têm prioridade. Testar E por dentro nos dois lugares e parede bloqueando. Repor 10 na geladeira compra só os insumos faltantes com orçamento inteiro antes de cobrar; não fecha a estação, não duplica estoque pronto nem exige preparo.
- **Praia viva (23/10):** CoastalLife mantém quatro jogadores separados de clientes/pedestres, bola cruza acima da rede e IK dos braços só no contato. Iate diurno e cruzeiro noturno em mar distante. Ao criar quadra, afastar props tanto de world._beach_props_build quanto de world_village._beach_life, excluir troncos/clutter; conferir imagem. Uma quadra lógica não impede guarda-sol antigo dentro dela.
- **Save girado (23/10):** player.kiosk_facing=beach marca gravação nova. Save antigo dentro do footprint acompanha posição/yaw do quiosque uma vez. No teste --loop-test, Core.SAVE_PATH é test_save.json; usar set_slot antes do teste real _on_start_load, que seleciona save_slot1.json, senão o teste carrega outro arquivo e parece falha de migração.
- **Casa e azul global (23/10):** paredes/materiais naturais ainda ficavam azuis com AMBIENT_SOURCE_SKY, sky_contribution .45 e cor ambiente azul/lilás. Usar ambiente de cor neutra, contribuição do céu zero e reflexão de céu desativada; preservar céu/ciclo do sol. Conferir interior, pessoas e quiosque em Vulkan. Casa: home_furnishings.gd e teste --home-test validam passagem real até cama/cozinha, apoios, colisões e E na TV/som. Som respeita mute/Music e reduz trilha sobreposta por distância.
- **CRT sem manchas (23/10):** vidro da televisão_02 é componente conectado curvo. Separar do corpo e alternar vidro desligado/tela ligada. Recortar por limites de coordenadas causa buracos; sobrepor cópia quase coincidente causa z-fighting. Preservar faces/UVs e conferir de perto em home_media.png, não só HOME_TEST PASS. Fontes móveis home_*.blend devem continuar incorporadas e reabertas.
- **Pedidos na mesa (23/10):** após escolher, cliente espera E para anotar. `order_taken` separa aguardando anotação de pedido registrado sem trocar estados do NPC. Espera/entrega continuam sentadas; mirar e usar E funciona nos dois lados da mesa. Garçom vai até approach para anotar antes de buscar o produto. Coletar/consultar não gasta estoque nem permite reiniciar paciência repetindo E. Fixtures podem usar `_order(g, true)`; teste real deve usar transição kchoose → _order e raycast/E.
- **Sem preparo (23/10/2026):** pegar produtos prontos na geladeira/armário/cozinha e entregar. Removidos botões e cronômetros; estoque compartilhado debitado uma vez na retirada. Devolução guarda unidade já paga; empresa antiga com produção pendente converte em pronta sem novo débito. Não reintroduzir preparo manual, nem exigir cozinheiro. Garçom retira diretamente; cozinheiro pode auxiliar entrega se não houver outro atendente.
- **Cores (23/10/2026):** Sergio pediu cores mais realistas em TUDO. Reduzir a saturação global e não reintroduzir reforços de laranja/saturação em Toon/daycycle. Preservar mapas dos modelos importados. Porta da casa deve parecer madeira natural, sem pintura azul. A nova preferência de cores prevalece sobre descrições históricas de paleta muito saturada.
- **Quiosque vazio (23/10/2026):** nunca ocultar KioskOperations inteiro porque o save não criou a empresa. Equipamentos e expositores são permanentes; company_enabled controla gestão/atendimento e item carregado. Antes do cadastro, E na estação abre empresa. Testar cenário sem empresa, além dos testes que criam empresa no início.
- **Nada de low poly**, principalmente móveis, casas e pessoas. Cilindro/esfera com poucos lados, caixa crua e corpo facetado são proibidos.
- **REGRA (18/10/2026): nada de "bolas e quadrados".** Nenhum objeto do jogo pode ser só esfera, caixa ou cilindro montados por código (frutas = esfera, garrafa = cilindro, caixote = caixa são proibidos). **Todo objeto vem de um modelo real baixado da web (CC0)**, com malha detalhada. Antes de criar qualquer prop, **busque o asset**: Poly Haven (API `api.polyhaven.com`), Quaternius, KayKit, ambientCG, itch.io, OpenGameArt. Só monte por código o que não existe pronto (ex.: parede, piso, telhado), e mesmo assim com textura e relevo. Registre a fonte em `CREDITS.md` e o asset em `tools/fetch_assets.py`.
- **REGRA (18/10/2026, reforçada pelo Sergio): proibido low poly e proibido "bolas coloridas"** (esferas/elipsoides achatadas fazendo de flor, fruta, balão, folhagem, copa). Tudo que for visível tem que ser modelado de verdade **no Blender (bpy)** com malha detalhada. Se não souber como é o objeto, **busque referências de imagem na web** (image_search/WebSearch) antes de modelar. Ao ver blobs/formas primitivas no jogo, troque-os, não deixe para depois.
- Visual cartoon colorido, iluminação quente e neon, personagens caricatos, gestão pelo celular.
- O jogo começa só com o quiosque e evolui por expansões.
- Quiosque abre às 8h e fecha às 18h (21h com neon); depois do horário não chega cliente.
- Cliente senta, lê o cardápio, pede e fica comendo ou bebendo com animação. Não levanta logo depois de atendido.
- Ninguém atravessa o quiosque nem as mesas.
- Prompt de interação fica embaixo, nunca no centro da tela.
- Entrega final = instalador (NSIS) em `D:\Jujuba\MareAltaResort\builds\vX.Y.Z\` + push no GitHub.

## 🧱 Sala das Faces — geometria gerada por código
- **Erro (v0.7.1–0.7.3):** `rounded_box`, `arch` e o telhado detalhado foram montados com triângulos anti-horários. A Godot considera **horário = frente**. Resultado: todas as caixas do jogo do avesso, "paredes transparentes" com o interior da casa aparecendo.
- **Regra:** toda malha feita com `SurfaceTool` passa por `B.fix_winding(arr)` / `B.cw_mesh(arr)`, que acertam a ordem pela normal.
- **Conferir:** render com a câmera colada numa parede (`--cam=`). Se aparecer o que está atrás, a malha está do avesso.

## 🎈 Sala das Coisas Flutuantes — apoio e altura
- **Erro:** garrafas e rádio fora da estante (estante com 1,24 m de largura e garrafas espalhadas por 2,8 m); pranchas inclinadas sem nada atrás; cordas de 5–8 mm invisíveis (vaso e cocos pareciam voar); cordas que não chegavam até a viga.
- **Erro:** cooler e caixote posicionados dentro da parede lateral do quiosque (parede de 0,6 m de espessura em x = ±2,0).
- **Regra:** todo objeto precisa de um apoio visível. Calcule a altura do topo da superfície (centro + metade da altura) e a extensão da peça **antes** de posicionar.
- **Regra:** corda ou corrente tem pelo menos 12 mm de raio e vai do objeto até a viga ou o beiral, com o comprimento calculado.
- **Regra:** antes de colocar um prop, confira as paredes e os móveis em volta (posição ± metade do tamanho, já com a rotação).
- **Conferir:** render de perto (`--cam=`) de cada canto novo.

## 🧭 Sala dos Nós Perdidos — transformações
- **Erro:** `look_at_from_position(cyl.position, ...)` usa posição **global**, mas recebia a posição **local** de um filho. As barras da bicicleta e as cordas da rede foram parar longe, e só sobravam as rodas.
- **Regra:** para cilindro ou cápsula entre dois pontos locais, use `B._beam(parent, a, b, raio, mat)`. Nunca use `look_at*` em nó filho com coordenadas locais.

## 🪜 Sala do Chão — z-fighting e contorno
- **Correção (22/10/2026):** os barcos da praia devem ficar fora do corredor e da plataforma do cais, considerando o AABB transformado de casco, mastro e vela. Passos usam amostras curtas e o material do piso atingido por raycast; altura do jogador não identifica madeira e cadência de 0,75 m fazia as pisadas soarem como escavação.
- **Erro (22/10/2026):** os GLBs do cais tinham tábuas visíveis, mas nenhum piso físico; a plataforma final também ficava antes do limite de colisão. Acrescentar colisão contínua aos módulos e à plataforma, alinhar os limites ao piso e testar caminhando da praia ao fim e de volta. A rampa deve encontrar o deck sem degrau. Não ativar nado só pela profundidade do terreno quando o personagem está sobre o cais; recuperar quedas abaixo do mapa para o último piso seguro.
- **Erro:** o deslocamento em y para evitar z-fighting crescia sem limite (`0.008 * n`), virando degraus no chão.
- **Regra:** use deslocamento cíclico: `y + passo * (n % 4)`.
- **Erro:** o contorno cartoon usava a 2ª derivada da profundidade linear, que gera linhas tracejadas em todo piso visto de lado (o "chão tremendo" ao andar).
- **Regra:** o contorno usa a 2ª derivada de **1/profundidade**, que é linear na tela sobre planos. O contorno só funciona sem MSAA (use FXAA).

## 👥 Sala das Pessoas
- **Preferência (23/10):** Sergio pediu tirar os óculos escuros de todas as pessoas. Não gerar `Sunglasses` em Guest nem forçar o acessório em provas visuais. Manter também a preferência anterior por pessoas sem chapéus/bonés.
- **Avental (23/10):** ajustar a superfície ao perfil da roupa, com alças e bolso, em vez de um plano distante do corpo. Os pesos de quadril/pernas precisam ser contínuos em todas as linhas: trocar de zero para peso de coxa numa altura fixa quebra o tecido durante o idle. Conferir em pé, andando, preparando e sentado. No bpy Windows, salvar fonte em arquivo temporário novo e copiar ao destino evita o erro de sobrescrita `file saved with @`; reabrir a fonte final e conferir texturas incorporadas.
- **Roupas/gestos (23/10):** ao encurtar calça, ocultar pele acima da barra real; deixar coxa de corpo muscular sob roupa Regular faz triângulos de pele atravessarem o tecido. O IK de trabalho deve girar a orientação atual do membro para o alvo: os braços Quaternius se estendem em X, não em Y. Retirada/entrega aguardam 400 ms sem reservar/consumir estoque outra vez. Validar com empresa e imagens de preparo, andar/sentar.
- **Correção definitiva do cabelo:** os glTFs Hair_* desta instalação são malhas rígidas, sem Skin. Usar `Ppl.attach_hair`: BoneAttachment3D em Head e transformação inversa do repouso da cabeça; apenas `skeleton = ".."` não resolve malha sem pesos. Esta regra detalha e substitui a orientação simplificada abaixo. Chapéus e bonés foram retirados por pedido do Sergio.
- **Roupas e cabelo (22/10/2026):** roupa MakeHuman ajustada só por escala não acompanha este corpo/rig; usar peças Quaternius compatíveis, com pesos originais, e conferir andar/sentar. Ao reanexar cabelo/barba em `Skeleton3D`, definir `skeleton = NodePath("..")`; deixar o caminho do arquivo importado faz o cabelo flutuar. Ao reconstruir ArrayMesh de corpo, descartar atributos CUSTOM não utilizados e preservar a flag de oito pesos quando aplicável; um erro na superfície pode apagar o corpo inteiro apesar de o teste lógico terminar com PASS. Conferir logs e imagem.
- **Contratação (22/10/2026):** não criar o personagem somente no tick de trabalho. Sincronizar presença em `staff_changed`, inclusive com celular aberto, fora do turno e no atendente legado sem empresa; turno controla trabalho, folga/demissão controlam ausência. Testar contratação pausada e entrega automática separadamente.
- O corpo vem de `assets/models/ual/guest.glb` (manequim Quaternius), com zonas de cor gravadas em `COLOR.r` por `tools/color_zones.py`. Se trocar ou suavizar a malha, **rode o color_zones de novo**.
- Chapéus e cabelos ficam presos ao osso `Head`, e a cabeça é aumentada pelo `head_scaler`. Confira se a aba não corta os olhos (aba de palha em y ≥ 0,245).
- Pedestres: 12 no modo HD e 5 no leve (o Sergio pediu metade). Não aumente sem pedir.
- Bloqueios (`block_rects`) cobrem mesa **e** cadeiras. O bloco que contém o destino final do NPC não barra a chegada dele (`_slide_out_of_blocks`).
- **Blender (bpy 5.x):** não use `bpy.ops.object.modifier_move_up` em script (laço infinito). Use `obj.modifiers.move(i, 0)`. Nunca chame um script de `inspect.py` (conflita com o módulo padrão do Python).

### Pessoas v0.7.3 (corpo real, CC0)
- Corpo, rosto e cabelo: `assets/models/ubc/` (Quaternius Universal Base Characters, gratuito, CC0). Código em `scripts/people.gd` (classe `Ppl`).
- O esqueleto é o mesmo UAL de 65 ossos do `guest.glb`; as animações vêm de lá (o AnimationPlayer é enxertado no corpo novo).
- Camisa e bermuda são **geradas** a partir da malha do corpo, empurradas para fora, cortadas por altura (bainha reta) e posição (manga). Cortar por peso de osso deixa a bainha serrilhada.
- O osso `Head` fica em y ≈ 1,60 (homem) e 1,55 (mulher); olhos 0,09 acima. Chapéu: `HAT_Y` = 0,14 em `guest.gd`.
- O pacote gratuito só tem corpos "Superhero" (musculosos): use escala X/Z de 0,86–1,0 para variar o porte.
- Download do itch.io pelo shell: GET na página, POST `/download_url` com `csrf_token`, abrir a URL devolvida, depois POST `/file/<id>?source=view_game&as_props=1&after_download_lightbox=true` (a URL assinada dura 60 s). Kenney, ambientCG e Poly Haven respondem direto do shell.

## 🖥️ Sala do Vídeo
- **Celular (22/10/2026):** nomes de apps sem quebra de linha alargavam a grade e eram cortados pelo painel. Grade de três colunas, textos/botões com quebra e rolagem vertical; o Álbum usa FlowContainer nos prêmios. Dimensionar o aparelho por escala da janela e manter a largura útil dos cartões sob controle, sem mínimo fixo que ignore a barra de rolagem. `--loop-test --phone-layout-test` verifica todos os apps em 1280×720, 800×600 e 360×640.
- DirectX 12: opção "API gráfica" grava um `override.cfg` ao lado do .exe (com volta automática para o Vulkan).
- DLSS **não existe na Godot**. O upscaler é o FSR 2.2 / FSR 1, na opção "Upscaling" + "Escala 3D".

## 🏷️ Sala dos Códigos — catálogo de itens
- Todo item do jogo tem um código estável (MOD-017, DSH-002, EXP-005…) em `docs/ITENS.md` / `docs/itens.json`. O usuário pode pedir mudanças citando o código.
- O registro `docs/itens_registro.json` garante que o código nunca muda. **Depois de adicionar modelo, prato, expansão etc., rode `python3 tools/gen_item_catalog.py`** e comite os três arquivos.

## 📅 Sala da Agenda — eventos, preços e passeios (v0.9.0)
- Eventos do dia (`Economy.DAY_EVENTS`): calor, lua, maré alta, tempestade e 3 festas (calendário `PARTY_CALENDAR`, só a partir do dia 8). O de amanhã é previsto (`Core.forecast_next`) e aparece no app Agenda; `Core.buy_prep()` paga preparativos (tempestade: estoque não se perde; festa: mais clientes).
- Preço do mercadinho muda por dia (`supply_mult`); **sempre use `Core.supply_total(id, qty)`**, nunca `Economy.supply_cost` para cobrar. Contratos dão -15% por 5 dias.
- Passeios: expansão `passeios` + equipe `guia`; `Core._check_tours()` roda no horário de `Economy.TOURS`; mar bravo cancela os passeios de mar.
- Save agora é versão 5; campos novos têm padrão ao carregar saves antigos. `tests/loop_test.gd` tem `mechanics_test()`.

## 🔨 Sala do Blender — o que era código virou modelo (v0.9.1)
- `tools/gen_code_props.py` (bpy) gera tocha, poste/seta de direção, placa ABERTO, rede de vôlei, poste de luz, caixa de correio, estrela-do-mar, ventilador, farol, píer (`pier_segment` 3 m + `pier_end`), bicicletas por cor, jangada e mastro/vela. Rode `python3 tools/gen_code_props.py [nome]`, depois `godot --import` + `vram_textures.py`.
- **Eixos:** Blender +Y vira Godot -Z; frente do modelo = -Y do Blender. Use `Real.place(parent, "g:nome", pos, -1.0, rot, tint, 0.0, false)` (escala 1, origem mantida em XZ, base do modelo em y=0).
- Redes/telas finas: barras reais, não modificador Wireframe (some no render). `godot` fica em `/home/claude/godot/godot` (não está no PATH).
- Também em Blender: buganvília (`bloom_<cor>`), hera pendurada, canteiro florido, bolas de praia/vôlei, gaivotas (`seagull_fly`/`seagull_perch`), coxinha, pipoca e rosácea. A "árvore de bolas" (`island_tree_01`) agora usa `q:CommonTree_N` (Quaternius) em `B.model`.
- O código antigo continua como fallback quando o .glb não existe.

## 🧪 Sala da Conferência — antes de entregar
- **Quiosque prático (22/10/2026):** ao substituir um prop de expansão, preservar seu marco lógico em `areas` (ex.: `grill`) mesmo com a cozinha agora interna; `career_test` e desbloqueios dependem dele. Validar o corredor com movimento real da cápsula. Na saída do deck, o chão passa de y=0,1 para y=0: a asserção de piso deve considerar o destino. GLB exporta cores lineares e `Toon.toonify` clareia novamente; julgar madeira/palha no jogo e reservar margem na cor original. Não exibir nomes de fregueses atravessando o telhado: no atendimento físico, usar apenas o número curto e a lista de pedidos.
- **Gestão ampliada (22/10/2026):** normalizar os números de estado/higiene no sanitize evita diferenças de precisão em save/recarga. Personalização move modelo, assento, ponto de entrega e bloqueio juntos; prévia não cobra. Para cores de prévia iguais às do cenário, definir o albedo solicitado no material duplicado (Toon.material satura a cor). Testar encomendas e serviços pendentes após recarga e evitar avisos repetidos em cada tentativa automática de preparo.
1. `godot --headless --check-only -s scripts/X.gd` em todo script editado. Erros "Identifier not found: Core/Quality/Economy" são normais (autoloads). Qualquer outro erro bloqueia.
2. Erros já cometidos: função duplicada no mesmo arquivo (`oil_lamp`); `var w: = M.algo` sem tipo (use `var w: Material = ...`).
3. Prints: `./shot.sh nome` ou câmera livre com `--cam=x,y,z,yaw,pitch[,hora]` (ver `main.gd`). Olhe de perto paredes, móveis, pessoas e chão.
4. `tests/loop_test.gd` precisa dar LOOP_TEST PASS. **Rode com `--rendering-driver opengl3 --rendering-method gl_compatibility`**: no Vulkan/lavapipe (mobile) a RSS passa de 5,9 GB e o processo morre por OOM (exit 137); em GL fica em ~3 GB.
5. **Assets baixados não vão no git** (`assets/tex*`, `assets/models/**/*.gltf` ficam no `.gitignore`). Antes de exportar, rode `python3 tools/fetch_assets.py` e `godot --headless --import`; sem isso o instalador sai sem texturas ("Resource file not found: res://assets/tex/...") e o log do `shot` mostra o erro. Confira com `grep -c "not found" shots/X.log` = 0.
6. **Modelos reais têm prioridade** (regra 18/10/2026): `B.model` usa o glTF baixado quando existe; `props.gd` (P) só vale quando não há asset ou com `--proc`. Para itens soltos use `Real.place(parent, chave, pos, altura, rot, tint, largura)` (`scripts/real.gd`): chave `nome` = Poly Haven, `k:nome` = Kenney, `g:nome` = gerado no Blender (`tools/gen_*.py`).
6b. **Texturas lossless estouram a memória.** Os `.import` de jpg/png nascem com `compress/mode=0` (sem compressão; o `shot` foi morto por OOM com shmem de 3,9 GB). Depois de `godot --import`, rode `python3 tools/vram_textures.py` e importe de novo (o `build_release.sh` já faz).
6c. **Kenney:** o GLB original aponta para `Textures/colormap.png` externo (sem ele tudo fica branco/azulado) e é facetado. `tools/fetch_assets.py` passa por `tools/smooth_kenney.py` (Blender/bpy: subdivisão + sombreamento suave + textura embutida). Pack novo → acrescente em `KENNEY` no fetch.
6d. Para ver o balcão do quiosque por cima use `--noroof` (esconde telhado e bandeirinhas). Câmeras antigas de `SHOTS` ficaram desatualizadas (vila foi movida): quiosque fica em x=38, z=-13. Shots pesados: `Q=1` em `/tmp/claude-0/sub/dbg.sh`.
6f. **Revisão visual:** a galeria `--gallery` isola o modelo e distorce cor e escala; julgue os itens em cenas do jogo (`dbg.sh` com `--cam`). Modelos Poly Haven muito escuros (banquinhos, cama, cadeiras) são clareados em `Real.LIFT`; o ventilador real tem pás pretas, por isso os bangalôs usam `P.build("ceiling_fan")`. Arbustos grandes usam a malha real (`Real.mesh_of`) em MultiMesh, não cartões cruzados.
6e. Nunca use `pkill -f` com texto que aparece no próprio comando (mata o shell).
7. Versão em `project.godot`, `export_presets.cfg` e `installer/setup.nsi`; depois exporte, rode o `makensis`, entregue no PC e faça o push.
8. Arquivos acima de 30 MB para o PC: primeiro `SendUserFile`, depois commit com o `fileUuid`.
- Pedrinhas e conchas da areia (v0.9.1): `g:pebble_a/b/c`, `g:shell_a/b/c` (Blender, `gen_code_props.py`) em MultiMesh por tipo no `world_village.gd`; nada de SphereMesh nelas.

## 🎉 Sala dos Eventos — efeitos visíveis (v0.9.2)
- `scripts/event_fx.gd` (classe `EventFX`, criada em `world.gd`): festas (quermesse = tendas Kenney; junina = fogueira com chama do Blender e luz tremulando; DJ = `g:dj_booth` com refletores coloridos), faixa `g:party_banner` + bandeirinhas + varal de luzes só quando os preparativos foram pagos (`Core.prep_active`); maré alta/tempestade mexem nos uniforms `swell`/`tide` do shader do mar; passeio de barco/mergulho solta um barco do píer (`Core.tour_done`).
- Testar: `XTRA="--event=show_dj --deco" Q=1 bash /tmp/claude-0/sub/dbg.sh nome "52,1.6,-17.5,0,2,21"`; também `--event=junina|quermesse|mare|tempestade` e `--tourboat`. Os nomes de shot "piscina", "quiosque" etc. liberam expansões; nome livre não tem piscina.
- Luzes: superfícies de modelo com material chamado `glow*` recebem o material ligado/desligado à noite via `Real.place_glow(...)` (lâmpadas `g:lamp_globe`/`g:lamp_bulb`, `g:flame`, `g:fresnel_lens`, `g:pool_light`, janelas/portas `g:win_frame`/`g:door_frame` com `VM.glass`).
- Janelas e portas da vila: `g:win_frame` + `g:win_shutters` (tingidas), `g:door_frame` + `g:door_leaf`; sino da igreja `g:bell`; maçanetas `g:brass_knob`; algas `g:alga`; fumaça = sprite Kenney (`tools/fetch_assets.py` -> `assets/tex/smoke_puff.png`).
- Metal no glTF vira preto no toon: use `metallic` 0 em material novo que precisa aparecer claro (aço da luz da piscina).
- **Erro (v0.9.2):** manchas pretas no fundo da piscina = `pow()` de base negativa (`1.0 - voronoi(...)`) no `pool_floor.gdshader` gerava NaN. **Regra:** em shader, `pow(max(x, 0.0), n)` sempre. Ao ver um defeito visual, ache a causa e corrija na hora, sem só avisar (pedido do Sergio, 18/10/2026).


## 🪑 Sala dos Assentos e Apoios — pente fino (v0.9.3)
- **Correção (v1.0.1):** cada lugar do quiosque tem proprietário (`owner`); só é liberado quando quem sai se afasta 1,2 m. Quem encontra lotação espera na fila lateral (`kqueue`, no máximo 3), sem ocupar cadeira nem exibir pedido. Mesas têm `approach` atrás de cada cadeira. Teste real: `--loop-test --kiosk-test --quality=0` verifica chegada, postura, consumo, saída e transferência da reserva.
- **Erro:** pessoas sentadas dentro do banco (assento do `painted_wooden_bench` fica a 0,65 m), no ar ao lado da mesa (as cadeiras do `outdoor_table_chair_set_01` ficam na frente/atrás, eixo z, não nos lados) e atrás da banqueta.
- **Regra:** na animação `Sitting_Idle` o bumbum fica 0,46 m acima da raiz e 0,33 m **atrás** dela. Lugar de sentar = centro do assento + frente × 0,27–0,3, com y = topo do assento − `SEAT_DROP` (0,455). Meça o assento com Blender (faces horizontais) antes de criar um lugar. O banco é achatado (`_bench()`, escala y 0,7 → assento a 0,46 m).
- **Erro:** objetos no ar: tigela 23 cm acima da `WoodenTable_01` (tampo a 0,55 m), petiscos 5 cm acima da mesa dobrável (0,73 m), gatos a 0,3 m (varanda tem topo 0,09 m e calçada 0,15 m; `B.platform` é centrada no y dado), balde fora do deck do bangalô, boia em pé solta no píer, varais de bandeirinha terminando no vazio.
- **Regra:** varal de bandeirinha sempre preso em fachada (`_street_bunting`) ou em mastro `g:bamboo_pole`. Cadeira de balanço Poly Haven tem a origem 10,6 cm abaixo dos balanços.
- **Ferramenta:** `XTRA="--full --floatcheck" Q=1 bash /tmp/claude-0/sub/dbg.sh fc "40,40,0,0,-60,12"` lista no log `FLOAT gap=...` cada modelo cuja base não encosta em nada (`tests/float_check.gd`). Itens no píer e dentro do barco aparecem como falso positivo; confira com render.
- `--lineup=x,z` (depuração) põe 8 pessoas em fila e uma sentada num banco, para olhar calçados e roupas de perto. Na câmera `--cam`, pitch **negativo olha para baixo**.
- Pessoas usam calçados gerados do pé da malha (`Ppl.clothes`: "shoes" = tênis, "sandals" = sandália com tira; zonas 4/5 no `guest.gdshader`). Nada de NPC descalço.
- Gaivota: o `join` herdava a rotação do corpo e ela ficava em pé ("garrafa"); aplique a rotação (`transform_apply`) antes do `join`.

## 🩹 Sala do Patch — atualizar sem reinstalar (v0.9.3)
- O Sergio já tem o jogo instalado: entregue **patch**, não o instalador de 1,3 GB. `bash tools/build_patch.sh <commit da versão instalada>` (0.9.2 = `477454d`) gera `build/patch/patch_<VER>.pck` só com os arquivos mudados e `/home/claude/inst/patch/Atualizar_MareAltaResort_v<VER>.exe` (~25 MB).
- Como funciona: o instalador do patch copia `patch_<VER>.pck` + `installer/patch_loader.gd` e grava no `override.cfg` `[autoload] Patch="*D:/.../patch_loader.gd"`; o carregador monta todos os `patch_*.pck` (em ordem) por cima do pacote principal. Patches seguintes só acrescentam outro `patch_*.pck`.
- **Regra:** script novo **não** pode usar `class_name` novo (o cache de classes vem do pacote base): carregue por caminho (`load("res://scripts/x.gd").new()`). Autoloads (Core, Quality) não são atualizados pelo patch na sessão (já instanciados antes do carregador).
- Teste do patch no Linux: copiar o binário da Godot como `MareAltaResort` ao lado de um `.pck` base + patch + `override.cfg`, rodar um `--shot` e procurar `[patch] ... ok` no log.
- `pkill -f`/`pgrep -f` com texto que aparece no próprio comando mata o shell (aconteceu de novo com "build_release" e "dbg.sh"): use `ps aux | grep "[g]odot/godot" | awk '{print $2}' | xargs kill`.
- v0.9.4: casas variadas em `_house` (estilo pela posição: térrea, sobrado com sacada `g:balcony_rail`, platibanda com frontão e ano, madeira) e telhado em 4 tons (`ROOF_TINTS`). Patch: `bash tools/build_patch.sh c8d566e` (base 0.9.3); os patches se somam (`patch_0.9.3.pck` + `patch_0.9.4.pck`).
- v0.9.4: a "árvore de bolas" voltou a aparecer no modo leve: a `q:CommonTree` da Quaternius também tem copa de esferas. Trocada por `g:tree_amendoeira_1..3` (Blender, galhos em andares e rosetas de folhas de verdade) em `B.model("island_tree_01")`.

## 🧹 Sala da Faxina — v0.9.5
- `--primcheck` (`tests/prim_check.gd`) lista no log `PRIM n=...` toda BoxMesh/CylinderMesh/SphereMesh/... que não é parede, piso ou telhado. Rode junto com `--floatcheck` antes de cada patch: `XTRA="--full --primcheck --floatcheck" Q=1 bash /tmp/claude-0/sub/dbg.sh pc "40,40,0,0,-60,12"`. Aceitos: neon, grades, placas de número, bueiros, corrimãos, amarras.
- Novos modelos do Blender: trellis_planter, towel_folded, flipflops, pool_float, rope_coil, cloth_shirt/towel, ac_unit, tv_antenna, straw, popcorn_cart, newsstand, cooler_box, coconut_cart, bottle_*. Materiais chamados `tint*` são coloridos no jogo com `Real.tint_named(nó, cor)`.
- Snorkel: `player.gd` nada quando o fundo está abaixo de -1,1 m (máscara em y -0,48, Shift mergulha); `scripts/underwater.gd` + `shaders/underwater.gdshader` ligam a visão subaquática quando a câmera fica abaixo de WATER_Y (-0,3). No `--cam` o y é do corpo: câmera = y + 1,65.
- Fotos: tecla P (`scripts/photo_mode.gd`, registrada em tempo de execução porque o patch não muda o InputMap do project.godot), álbum em `user://album`. Fregueses fiéis em `user://fregueses.json` (`village_life.gd`, não no Core, que é autoload e não muda com patch).
- Aviso de atualização: `scripts/update_check.gd` lê `docs/latest_version.txt` no GitHub; os patches ficam em `patches/` no repositório. **A cada patch novo: atualize `docs/latest_version.txt` e copie o .exe para `patches/`.**
- Janelas acendem em 3 horários (`VM.glass`, `glass_b`, `glass_c`); moradores vão até a porta (`house_doors`) às 21h30; facho do farol com `shaders/light_beam.gdshader`.
- O carregador do patch grava `diagnostico.txt` (placa, API, renderizador, FPS) na pasta do jogo.
- Política de instalador: patches pequenos para quem já tem o jogo; instalador completo consolidado a cada ~5 versões (próximo na 0.9.7 ou quando pedirem).
- Pacote cumulativo: `bash tools/build_patch.sh 477454d` (base 0.9.2) gera um patch único com tudo; renomeie para `Atualizar_MareAltaResort_0.9.2_para_X_completo.exe` e deixe só ele em `patches/`.

- **Erro prevenido (v1.0.1):** `git diff` não inclui `assets/models/qnat` ignorados nem garante novos `assets/models/gen/*.glb`; o patch precisa acrescentar qnat e os GLBs atualizados explicitamente (`tools/build_patch.sh`). `fetch_assets.py` deve gerar também `gen_food`, `gen_business` e `gen_hotel` após as texturas, e falhar se um GLB não sair. O código foi corrigido via GitHub MCP, mas **testes reais no Godot ainda estão pendentes**.

## 🏆 Sala da Evolução — v1.0 (fama, negócios, temporadas, receitas, capítulos, Hotel 5★)
- Lógica em `scripts/progression.gd` (nó `Core.prog`, salvo em `"prog"` no save v6); dados em `scripts/prog_data.gd` (classe `PD`). Ganchos no Core: `on_sale`, `on_income` (via `book`), `on_vip`, `on_tour`, `on_new_day`, `tick`.
- Efeitos da árvore: `Core.prog.eff("ramo")`; equipe: `staff_eff(cargo)` (0 = folga) e `staff_wage(cargo)`. Nunca leia `Economy.STAFF[x].wage` direto para pagar.
- Pratos secretos (`"secret": true` em `Economy.DISHES`) só entram no cardápio depois de descobertos (`prog.is_discovered`). Cardápio do quiosque respeita `prog.menu_off`.
- Negócios no mapa: `scripts/biz_world.gd` (modelos `g:biz_*`), minijogo `scripts/minigame.gd` (pausa a árvore; 3 rodadas). Prainha do Oeste: barreira em x=-37 até o capítulo "prainha".
- Hotel 5★: expansão `grand_hotel` (fama 8 + capítulo "carnaval"), `scripts/hotel_world.gd`, terraço elevado a 1,2 m (piscina x -35..-17, z 31..41, água 1,05). O terreno x -47..4, z 23..75 é reservado (sem palmeiras/vegetação) em `VEG_EXCL` e `_palms`. Renda à noite: `prog._hotel_night()`.
- **Erro (gen_*.py):** `box()` do `gen_code_props.py` aplica a localização na malha (origem fica em 0,0,0); `rotation_euler` depois gira em volta da origem do mundo e o objeto "voa" (toldo do food truck no chão, cartões-postais espalhados). **Regra:** para caixa girada use `rbox(size, loc, mat, rot)` (gen_business/gen_hotel). `from gen_code_props import *` não traz nomes com `_` (importe `_mesh_obj`, `_torus`... explicitamente).
- **Erro (v1.0):** o `.pck` chegou a 2,1 GB e o `makensis` falhou ("error mmapping file ... out of range"): o NSIS não aceita mais de 2 GB. **Regra:** `tools/vram_textures.py` limita a 1024 px os mapas `_nor/_rough/_arm/_ao/_disp` e as texturas embutidas dos modelos `g:*` (pck foi para 1,5 GB); o `build_release.sh` aborta se exe+pck passar de 2 GB. Para listar o que pesa no pack: `python3 tools/pck_list.py build/win/MareAltaResort.pck`.
- Teste do pack exportado (o mesmo do instalador): binário Linux da Godot com `--main-pack /home/claude/inst/MareAltaResort.pck --rendering-driver opengl3` e um `--shot` (script `/tmp/claude-0/pcktest.sh`).
- Depuração: `--v1` libera tudo (expansões, capítulos, negócios, fama máxima). Ex.: `XTRA="--v1" Q=1 bash /tmp/claude-0/sub/dbg.sh h "-14,9,10,200,-12,11"`.
- **Erro (v1.0, PC do Sergio):** tela preta no DirectX 12 ("not enough room in the current frame's RESOURCES descriptor heap" e depois `0x887a0005` = placa removida). A cena da v1.0 passou do limite padrão de descritores do D3D12. **Regra:** `project.godot` tem `rendering_device/d3d12/max_resource_descriptors_per_frame=65536` (+ sampler/misc 2048); se o jogo instalado já usa D3D12, dá para corrigir só com essas linhas no `override.cfg` ao lado do .exe. Log do jogo instalado: `D:\Games\MareAltaResort\userdata\Godot\app_userdata\Maré Alta Resort\logs\godot.log`.

## ⏸️ CHECKPOINT v1.0.1 (19/10/2026, em andamento — continuar daqui)
- FEITO: `prune_export.py` não exclui mais `qnat` (arbustos Quaternius sumiam no jogo instalado = "placas redondas"); `Real` avisa `REAL_MISSING` no log; `Real.ALIAS` troca todo `k:` low-poly por modelo detalhado (`tools/gen_food.py`: coconut_green, coconut_open, pineapple, orange, frappe, cup_plastic, glass_juice, cocktail, campfire_logs, beach_flag, beach_spade, boat_hull; Poly Haven: croissant, Barrel_01, wooden_crate_02, stone_fire_pit, sand_rocks_small_01, boulder_01, dead_tree_trunk); recife com altura limitada pela profundidade (pontas no mar); espreguiçadeira/venezianas/treliça/banca corrigidas; D3D12 com mais descritores.
- FALTA: (1) pessoas travadas em pé na mesa do quiosque (dois clientes no mesmo lugar, rótulos sobrepostos) em `village_life.gd`; (2) conferir em prints: prateleira do quiosque, balcão, carrinho de cocos, pilhas de coco, fogueira junina, tendas da quermesse, barco de pesca (`g:boat_hull`), castelo de areia; (3) `--primcheck`/`--floatcheck`; (4) LOOP_TEST; (5) gerar PATCH a partir da v1.0 instalada (base = commit da v1.0, ex. `51921df`) — o patch precisa levar a pasta `assets/models/qnat`; (6) atualizar CREDITS (gen_food + dead_tree_trunk Poly Haven) e catálogo.
- A edição em `tools/build_release.sh` para o smoke testar o .pck exportado (`--main-pack`, `--v1`) ainda NÃO foi aplicada.
