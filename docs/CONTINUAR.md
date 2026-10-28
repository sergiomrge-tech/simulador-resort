# Guia vigente para as próximas atualizações

**Entrega vigente:** [Refinamentos de 27/10](REFINAMENTOS_2026-10-27.md). Retomada do checkpoint concluída; celular com Missões direta, banheiro atrás da casa, gramado, reggae original e configurações independentes. Evidências de fonte/PCK no guia.

Atualizado em **27/10/2026**. Destinado a qualquer IA ou pessoa, sem depender deste
chat. Leia junto com [AGENTS.md](../AGENTS.md). Novos pedidos do usuário prevalecem.

**Atualização anterior:** [Campanha e correções de 26/10](CAMPANHA_CORRECOES_2026-10-26.md).

Pagamento na entrega substitui o recebimento manual. Sem PC: gestão no celular portátil com B em qualquer lugar; missões e pedidos fixos à esquerda. Porções prontas de batata e peixe no armário.

[Produtos nas mãos e sorvetes](MAOS_SORVETES_2026-10-24.md) continua vigente.

[Desempenho e atendente único](DESEMPENHO_ATENDENTE_2026-10-24.md) continua vigente.

**Atualização de louça e balcão (24/10):** [LOUCA_BALCAO_2026-10-24.md](LOUCA_BALCAO_2026-10-24.md).

**Revisão mais recente de visual e gestão:**
[REFINAMENTO_2026-10-23.md](REFINAMENTO_2026-10-23.md). Notebook CC0 detalhado,
compras por produto, seis abas compactas, promoções alinhadas, cabelos, rotas,
ruas, animais animados com rosto e pássaros. Inclui os resultados fonte/PCK.

**Adição sonora:** [PASSAROS.md](PASSAROS.md) documenta os cantos direcionais
diurnos perto das árvores, volume suave, pausa e respeito ao silêncio/SFX.

**Atualização concluída de 23/10:** leia
[VALIDACAO_2026-10-23.md](VALIDACAO_2026-10-23.md) e
[ATUALIZACAO_2026-10-23.md](ATUALIZACAO_2026-10-23.md).
Corrigidos mira legada, abertura no rush, nós órfãos e liberação de recursos;
bateria do executável com PASS e saída 0, sem erros nos logs.
O documento PASSAGEM_PARA_OUTRA_IA.md guarda o checkpoint histórico anterior.

## Base correta

- Projeto: **Maré Alta Resort**, Godot **4.5.1**, GDScript, Forward+ / Vulkan.
- Versão em `project.godot`: **1.1.0**; linha de trabalho **1.1.0 RC2**.
- Branch usada nas entregas: **`codex/resort-1.1-mcp`**.
- Repositório: https://github.com/sergiomrge-tech/simulador-resort
- Base anterior ao checkpoint de computador/balcão: **`80bc38d`**.
  Verifique `git log` e `git status` para identificar o checkpoint mais recente.
- O jogo começa com o quiosque e evolui por expansões. Gestão no celular portátil (B; sem computador físico).

Antes de editar, confira branch/remoto e alterações pendentes. Não use reset,
checkout ou cópia de um build antigo para substituir trabalho existente. Não
trabalhe nos mesmos arquivos ao mesmo tempo que outro chat sem coordenação.

## Regras atuais de produto

1. **Sem preparar produtos.** E na geladeira/armário/cozinha, escolher produto
   pronto, levar ao cliente, E para entregar com pagamento automático. Sem espera,
   cronômetro, etapas de montagem ou necessidade de cozinheiro.
2. **Estoque continua existindo.** Compras abastecem a despensa compartilhada.
   A retirada desconta os insumos uma vez; a entrega não desconta de novo.
   Devolver guarda unidade já paga; retirar a devolução não cobra novamente.
   Produção pendente de save antigo vira unidade pronta uma única vez.
3. **Balcão antes da mesa.** Clientes reservam mesa, pedem e retiram todos os
   produtos de pé no balcão; só então levam os produtos e sentam para consumir.
   E anota/entrega por dentro. Garçom também atende no balcão. Fila e duas retiradas,
   sem duplicar estoque/cobrança. Não usar banquetas como assentos no modo físico.
   Quiosque começa fechado; abertura explícita no celular, respeitando horário/checklist.
   Migração opening_version=1 fecha save antigo uma vez; dormir fecha novo dia.
4. **Compatibilidade de modos.** `company_enabled()` exige empresa criada e modo
   físico ativo. No modo legado, pedidos continuam automáticos e consultáveis;
   atendimento no balcão é imediato, sem preparo. Antes da empresa, a estação orienta criar a empresa no celular. Não esconder os móveis por causa desse estado.
5. **Quiosque prático.** Todos os equipamentos usados ficam dentro; geladeira à
   esquerda, armário ao centro, cozinha à direita, caixa na frente. Manter parede
   traseira, piso físico, corredor e duas entradas laterais, sem anexo externo.
   Quiosque e todas as mesas agora ficam virados para a praia (-Z). O frame
   KioskBeachFrame gira geometria/luzes/colisões juntos. Construção usa coordenadas
   autorais antigas (+Z); dados de NPCs e rotas usam kiosk_point/kiosk_local.
   Nunca somar um offset antigo diretamente a KIOSK_C para rotas/objetivos.
   Balcão tem staff_approach interno para anotar/entregar; mesas usam approach.
6. **Exposição permanente.** Geladeira/armário mostram os produtos que vendem
   mesmo no estoque zero (12 apresentações de bebidas). A etiqueta informa a
   disponibilidade real. Não vender a referência visual nem criar estoque grátis.
7. **Cores naturais em todo o jogo.** Menos saturação e menos laranja artificial,
   madeira/areia/terracota naturais e mapas dos modelos preservados. Casa com piso
   claro, detalhes, cortinas, persianas e cozinha; porta em madeira, não azul.
   Manter personagens estilizados; cores naturais não exigem trocar a engine.
   A luz ambiente usa AMBIENT_SOURCE_COLOR neutra e sky_contribution zero;
   não restaurar o banho azul/lilás do céu nos materiais.
   Refinamento posterior: contorno fino/discreto com fade por distância, água HD
   com gradientes suaves e espuma contínua, bloom noturno contido. Não restaurar
   linhas escuras grossas nas folhas nem faixas duras e saturadas na água.
   Sala da casa tem sofá, mesa de centro, estante, TV e som: E liga/desliga. TV exibe animação silenciosa;
   som respeita mute/volume e distância. Preservar passagem até cama/cozinha.
8. **Pessoas sem óculos escuros, chapéus ou bonés.** Preservar cabelos presos à
   cabeça animada e roupas compatíveis com o rig. Não recolocar acessórios nos
   testes só para tirar imagens. Avental com caimento, alças, bolso e cintura.
9. **Interface limpa.** HUD/textos compactos, prompt embaixo, celular com seis
   áreas iniciais sem atalhos duplicados e layout que caiba em telas pequenas.
10. **Áudio suave, sem vozes de fundo.** Preservar também o cais com colisão,
    recuperação de queda, barcos afastados e vidros sem coloração azul.
11. **Reposição na estação.** E na geladeira/armário, produto esgotado → Repor 10.
    Comprar só os insumos faltantes para dez porções; mostrar preço antes de cobrar.
    Usar supply_total e buy_supply, respeitar saldo/contratos e evitar compra parcial.
    Continuar na estação para pegar o produto pronto. Sem ressuscitar preparo.
12. **Vida na praia.** Quatro jogadores na quadra de vôlei ao lado do quiosque,
    bola e braços animados. Um navio de madeira/velas passa lentamente de dia,
    um por vez, usando Ship Pinnace CC0 da Poly Haven. Cruzeiro fica ancorado à noite, sem
    deslocamento nem esteira de propulsão, conforme correção do usuário.
    Usuário rejeitou a prévia do Cruise Ship Quaternius low poly por ser simples.
    Cruzeiro vigente é o autoral detalhado, coastal_cruise, ampliado a 1,6 para
    leitura na praia, com varandas, botes, radar e cabines parcialmente apagadas.
    Embarcações distantes da faixa de banho/cais; congelar movimento na pausa.
    Quadra deve ficar livre de guarda-sóis/espreguiçadeiras e outros props.
13. Baleias saltam ao fundo em ciclos alternados, com respingos balísticos,
    espuma, ondas dissipando e som suave SFX. Nuvens usam shader de céu, seguindo
    horário/clima. Pausa congela animações. Scripts whale_wildlife.gd, shaders
    sky_clouds/whale_foam; teste --whale-test. Geradores gen_whale_and_sailship.py
    e gen_whale_splash_audio.py; fontes editáveis incorporadas em art/blender.

Use modelos detalhados e licenciados, preferencialmente CC0, ou Blender com
malha trabalhada. Não substituir objetos por low poly ou montagens de primitivas
como acabamento final. Reutilize a biblioteca existente e registre licenças em
`CREDITS.md`. Salve fontes `.blend` editáveis, com texturas incorporadas; reabra
para conferir. Atualize downloads/geradores e o catálogo (`tools/gen_item_catalog.py`).

## Histórico: computador e balcão (substituído pelo celular em 26/10)

Leia [COMPUTADOR_E_BALCAO.md](COMPUTADOR_E_BALCAO.md). PC físico com E, sem gestão
remota; telas de estação continuam diretas. Porta da casa abre/fecha e fecha após
sair com arco livre. Tampo madeira escura/base cinza, copos na bandeja, sem caixa
branca e promoções nas duas faces com preços reais. Fontes Blender incorporadas.
As regras de PC deste trecho são históricas; celular portátil e pagamento automático prevalecem.

## Onde alterar cada coisa

Quadros: `world.gd::_chalkboard/_fit_board_text` mede a fonte localizada e reduz
pixel_size para caber em 0,86 m de largura/altura. Quadro do quiosque em
world_village.gd fica a Y=1,9 m para a escrita passar acima do guarda-corpo.
Cesto fechado: `tools/import_closed_basket.py`, `g:wicker_basket_closed`,
fonte Blender com texturas incorporadas. Alias de Real e desvio em B.model
corrigem chamadas existentes sem alterar os downloads originais. Teste:
`--loop-test --props-layout-test`, capturas no user://qa_shots isolado.

| Área | Arquivos principais |
|---|---|
| Estado, compras, retirada, devolução, caixa, save | `scripts/resort_core.gd`, `scripts/company_rules.gd` |
| Clientes, lugares, leitura, pedido e consumo | `scripts/village_life.gd` |
| Estações físicas, interação E, equipe e exposição | `scripts/kiosk_operations.gd` |
| Aparência, roupas, cabelo e gestos | `scripts/guest.gd`, `scripts/people.gd`, `scripts/work_arm.gd` |
| HUD e celular | `scripts/hud.gd`, `scripts/phone_ui.gd` |
| Rotinas, manutenção, fornecedores, custos | `scripts/kiosk_management.gd`, `scripts/kiosk_simulation.gd` |
| Vila, casa, quiosque, colisões | `scripts/world_village.gd`, `scripts/world.gd` |
| Mobiliário da casa, TV, som e redução da trilha | `scripts/home_furnishings.gd`, `scripts/audio.gd`, `shaders/home_tv.gdshader` |
| Vôlei, tráfego marítimo e poses | `scripts/coastal_life.gd`, `scripts/volley_arm.gd`, `shaders/coastal_wake.gdshader` |
| Paleta e ciclo de luz | `scripts/toon.gd`, `scripts/daycycle.gd`, `shaders/guest.gdshader` |
| Fontes artísticas | `art/blender/`, `tools/gen_*.py`, `assets/models/gen/` |

O quiosque está em `(38, 0, -13)`, frente **-Z / praia**; a casa em `(46, 0, 21)`.
Interação de clientes usa seleção tolerante de 11 graus/3 m, acima do tampo,
com teste de visibilidade física. Estações diretamente miradas têm prioridade;
paredes continuam bloqueando. Não fazer entrega a cliente escolhido arbitrariamente.
`_order(g)` cria pedido aguardando anotação no modo físico; `order_taken` registra
se foi anotado. `waiting_customers()` retorna os registrados; `customers_to_order()`
os não anotados. Fixtures podem usar `_order(g, true)`; testes da interação real
precisam passar por `kchoose` e raycast/E, não apenas chamar a função diretamente.

A leitura detalhada das lições técnicas continua obrigatória em [CLAUDE.md](../CLAUDE.md).
Seus trechos antigos sobre preparo, cores exageradas, óculos e entrega obrigatória
por NSIS foram substituídos pelas preferências atuais deste guia.

## Assets e ambiente em outra máquina

Caches `.godot/`, `build/`, saves e muitos downloads não estão no Git. Um clone
não contém automaticamente todas as dependências da instalação do Sergio.

- Localize Godot 4.5.1 e os templates Windows correspondentes; não adivinhe paths.
- Use Python com as dependências dos geradores. Nesta máquina existe
  `build/python/Scripts/python.exe` com `bpy` 4.5.3; esse ambiente não é versionado.
- Examine `tools/fetch_assets.py` e seus wrappers para recuperar modelos/texturas
  externos. O fetch também pode regenerar assets: revise antes de executá-lo sobre
  fontes já personalizadas. Roupas base usam `tools/fetch_compatible_outfits.py`.
- Importe o projeto, execute `tools/vram_textures.py` e importe novamente se houver
  texturas novas. Conferir `.gdignore` e cache quando um asset existente não carrega.
- Geradores relevantes: `gen_kiosk_facade.py`, `gen_counter_details.py`,
  `gen_compatible_clothing.py`, `gen_player_home.py` e `gen_kiosk_soft_audio.py`.
- Móveis da sala: `fetch_home_assets.py` baixa oito modelos CC0 e
  `import_home_assets.py` preserva malhas/UVs, incorpora texturas nas fontes
  `art/blender/home_*.blend` e exporta `assets/models/gen/home_*.glb`.
  Aceita slugs individuais para reconstruir só o recurso alterado.
- Tráfego marítimo: `tools/gen_coastal_traffic.py` baixa o cabin cruiser CC0 da
  Innerscene e gera o cruzeiro autoral detalhado. Fontes coastal_*.blend incorporadas,
  reabertas; GLBs e texturas runtime versionados. Aceita yacht/cruise separadamente.
  Não reduzir os navios a caixas/cascos low poly; preservar decks, vidros e detalhes.
- Cruzeiro: `tools/gen_coastal_traffic.py cruise` gera `coastal_cruise.blend/glb`.
  Modelos gratuitos mais detalhados localizados em Sketchfab e BlendSwap exigem
  login para download nesta sessão; não foram baixados. Não confundir resultados
  de pesquisa com assets realmente instalados. Mantida fonte autoral editável.
- Não regenere tudo sem necessidade. Preserve pesos/UVs, escala e origem. No
  Blender, frente -Y vira +Z na Godot. Peças rígidas Hair_* precisam de
  BoneAttachment em Head; só mudar o caminho skeleton não resolve cabelo sem Skin.
- No Windows, o gerador de roupa salva em staging e copia para evitar o erro de
  sobrescrita `file saved with @`. Preserve a fonte final e reabra para verificar.

Ausência de recurso, textura ou móvel é falha de integração, mesmo com PASS no
log. Não considerar assets externos opcionais para reproduzir o visual atual.

## Testes sem mexer no save do jogador

Na instalação portátil, `Jogar.vbs` usa `userdata/`. **Não execute testes com os
saves reais, não apague `userdata/` e não sobrescreva configurações do jogador.**

Exemplo PowerShell para uma execução isolada. Ajuste o executável à máquina;
`$Godot` deve ser um caminho absoluto válido do Godot, ou o EXE portátil para testar
um PCK. Use uma pasta de trabalho separada por execução:

```powershell
$Root = (Get-Location).Path  # executar na raiz do checkout
$Godot = (Get-Command godot -ErrorAction Stop).Source
$RunId = 'company-' + [guid]::NewGuid().ToString('N')
$TestData = Join-Path $Root ('build/qa/' + $RunId)
$LogDir = Join-Path $Root 'build/logs'
New-Item -ItemType Directory -Force -Path $TestData,$LogDir | Out-Null
$Log = Join-Path $LogDir ($RunId + '.log')
$PreviousAppData = $env:APPDATA
try {
    $env:APPDATA = $TestData
    & $Godot --headless --path $Root --audio-driver Dummy --log-file $Log -- --loop-test --company-test --quality=1
    $RunExitCode = $LASTEXITCODE
} finally {
    $env:APPDATA = $PreviousAppData
}
Get-Content -LiteralPath $Log
# Conferir marcador PASS, exit code e erros de script/recursos, não só a última linha.
```

Em Linux/macOS, isole também o diretório de dados de usuário apropriado à plataforma
(`XDG_DATA_HOME` em Linux), além da pasta/log por execução. Se usar Godot MCP,
defina APPDATA no processo que cria o jogo filho; mudar só o shell não muda o
ambiente de um servidor MCP já aberto.

| O que mudou | Comando/flag após `-- --loop-test` | Resultado esperado |
|---|---|---|
| Fluxo físico, mão, estoque, entrega e equipe | `--company-test` | `COMPANY_TEST PASS` |
| Quiosque, colisões, E nas mesas e visual | `--practical-test` | `PRACTICAL_TEST PASS` |
| Casa, circulação, colisões, apoio, E na TV/som e mute | `--home-test` | `HOME_TEST PASS` |
| Balcão interno, mira, reposição na geladeira e migração da posição | `--counter-test` | `COUNTER_TEST PASS` |
| Vôlei, iate, cruzeiro, horários, chuva e pausa | `--coastal-test` | `COASTAL_TEST PASS` |
| Gestão, equipamentos e candidatos | `--management-test` | `MANAGEMENT_TEST PASS` |
| Custos, perdas, virada e fornecedores | `--simulation-test` | `SIMULATION_TEST PASS` |
| Celular em vários tamanhos | `--phone-layout-test` | conferir log do teste |
| Cais e queda | `--pier-test` | conferir log do teste |
| Ciclo geral e atendimento legado | sem flag extra | `LOOP_TEST PASS` |

Rode um teste específico por processo: o dispatcher retorna após a primeira flag.
Para visual, retire `--headless` e use Vulkan / `--resolution 1280x720`; as imagens
ficam em `shots/`. Headless não valida aparência. Nesta máquina, use no máximo dois
processos pesados simultâneos. O fallback OpenGL pode ajudar em outra GPU, mas não
comprova o mesmo resultado visual de Vulkan. Erros de script/recursos bloqueiam a
entrega; avisos conhecidos de material/RID ao encerrar foram registrados na validação
anterior, não equivalem a um log inteiramente limpo.

Exceção: `--coastal-test` grava capturas em `user://qa_shots` e imprime o caminho
absoluto no log; assim o mesmo teste funciona com o PCK, onde `res://` não é
um diretório de saída gravável. APPDATA deve continuar isolado para cada teste.

## Exportação e entrega

1. Termine os testes da fonte e a inspeção visual. Preserve os saves existentes.
2. Confirme todos os assets importados. O preset Windows exporta recursos; confira
   `tools/prune_export.py`, pois ele remove pastas supostamente sem uso e já causou
   exclusões indevidas. `apply` precisa de `restore` em `finally`, mesmo se falhar.
3. Exporte o PCK com o preset **Windows Desktop**. Exemplo conceitual:
   `godot --headless --path . --export-pack "Windows Desktop" CAMINHO/MareAltaResort.pck`.
   Depois de iniciar uma exportação, espere terminar e examine os erros.
4. Coloque EXE/PCK correspondentes na pasta portátil. Teste **esse EXE com esse PCK**,
   com dados isolados; o exemplo acima adapta-se usando o EXE e `--path` da pasta
   portátil. Não basta ter testado a fonte antes da exportação.
5. Use `tools/package_quiosque_portable.py` após os testes. Ele inclui documentos,
   hashes e verifica CRC do ZIP; não inclui saves. Revise seus caminhos se estiver
   em outra máquina. O nome histórico do ZIP foi mantido nas atualizações.
6. Atualize documentação, registre testes/limitações e o hash do pacote, faça
   commit + push na branch correta e confirme o SHA remoto. Entregue o link real
   para baixar o ZIP. Não alegue que um executável foi publicado no GitHub quando
   apenas o código foi enviado.

### Caminhos desta máquina (não portáteis)

- Checkout: `C:/Users/sergi/Documents/ChatGPT/resort 2`.
- EXE/PCK: `build/rc2-playable/`; launcher `Jogar.vbs`.
- Staging com espaço: `D:/CodexTemp/marealta-quiosque-pratico/`.
- ZIP: `C:/Users/sergi/Downloads/MareAltaResort_1.1_CaisCorrigido.zip`.
- A instalação antiga em `D:/Games/MareAltaResort` não foi atualizada por esses ZIPs.
- Disco C teve pouco espaço; exportar no staging D evita duplicações grandes.

A entrega atual é o portátil Windows. NSIS e scripts bash antigos continuam no
repositório para quando forem necessários, mas não são a única forma de entrega.
Não trocar saves ao atualizar: substituir programa/PCK e manter `userdata/`.

## Estado validado e histórico

A entrega funcional `6a0a3c2` passou os testes de empresa e prático, na fonte e no
executável; prático verificou raycast/E em cadeiras opostas da mesa. A anterior
`5179265` validou retirada sem preparo, devolução, migração, gestão, simulação e
ciclo. Leia [VALIDACAO_1.1.0_LOCAL.md](VALIDACAO_1.1.0_LOCAL.md) para hashes/logs.
Isso é evidência daquelas entregas, não garantia sobre uma alteração futura.

- [QUIOSQUE_PRATICO.md](QUIOSQUE_PRATICO.md): uso e disposição do quiosque.
- [REFINAMENTO_COMPLETO.md](REFINAMENTO_COMPLETO.md): refinamentos e revisões.
- [SIMULACAO_QUIOSQUE.md](SIMULACAO_QUIOSQUE.md), [ROTINAS_QUIOSQUE.md](ROTINAS_QUIOSQUE.md): gestão.
- [ITENS.md](ITENS.md), `itens.json`, `itens_registro.json`: códigos estáveis.
- [CREDITS.md](../CREDITS.md): origem e licenças.
- [HISTORICO_CONTINUACAO_2026-10-19.md](HISTORICO_CONTINUACAO_2026-10-19.md):
  cópia integral do antigo guia, preservada para consulta. Versões, pendências e
  instruções antigas ali não devem ser executadas como plano atual.

Ao concluir uma atualização, atualize este guia se a preferência/fluxo mudou,
registre evidências em validação, preserve as lições em CLAUDE.md e deixe um resumo
com o que mudou, como foi verificado, limitações e commit/branch para a próxima IA.

## Revisão visual e gestão de 23/10/2026

Leia [REFINAMENTO_2026-10-23.md](REFINAMENTO_2026-10-23.md) para a revisão
mais recente.
PC usa Classic Laptop CC0; não voltar ao caixa azul/modelo de seis quadrados.
Gestão com seis abas compactas; compras abre em produtos com reposição imediata
para 10, custo dos insumos faltantes. Formulário de fornecedor é secundário.
Não voltar a permitir botões estreitos que esticam os cartões de equipe.
Animais mantêm rigs/animações e rostos refinados; não regenerar pelos antigos
smooth_animals.py que removiam o rig. Pedestres mantêm 12 HD/5 baixa; chegadas
em casas projetadas fora dos bloqueios com margem para o corpo.

## Pedido de 24/10 — louça e balcão

Louça deve corresponder ao que foi consumido: suco → copo vazio; coco → coco aberto;
comida → prato/tigela vazios. Preservar lista por lugar no save e limpar junto dos
objetos. PC central, copos à esquerda e promoções à direita. Downloads/builds no
drive D, pois C ficou cheio. Guia: [LOUCA_BALCAO_2026-10-24.md](LOUCA_BALCAO_2026-10-24.md).

## Pedido de 24/10 — desempenho e atendente único

Somente **um atendente** faz todo o atendimento do quiosque: anotar, retirar pronto,
entregar no balcão, receber no PC e recolher louça. Substitui cargos separados
(garçom/caixa/limpeza/cozinheiro) no quiosque, preservando migração e histórico.
Cargos de pousada/bar/passeios continuam separados. Não reabrir contratação de
quatro cargos por seguir documentos antigos. Detalhes, métricas e validação em
[DESEMPENHO_ATENDENTE_2026-10-24.md](DESEMPENHO_ATENDENTE_2026-10-24.md).

## Pedido de 24/10 — produtos nas mãos e sorvetes

Produtos transportados acompanham as mãos animadas, inclusive o atendente. Pedidos maiores usam bandeja com apoio dos braços. Sorvetes de morango/chocolate são produtos prontos da geladeira, com reposição direta e pote vazio após consumo. Preservar o único atendente, sem preparo. Guia: [MAOS_SORVETES_2026-10-24.md](MAOS_SORVETES_2026-10-24.md).

## Migração vigente para UE5.8 — em andamento

Pedido atual do usuário: conversão integral com visual **realista estilizado**.
Branch `codex/ue58-migration`; guia [ue58/MIGRACAO.md](ue58/MIGRACAO.md).
A entrega Godot acima permanece sendo a última versão jogável aprovada.


## Trabalho atual UE5.8

Pedido posterior migrou o destino para UE5.8, realista estilizado. Branch codex/ue58-migration no D. Leia [checkpoint UE](ue58/CHECKPOINT_2026-10-27.md). Godot permanece a última versão jogável; o port UE ainda não está pronto.


## Continuação UE5.8 — cenário e atendimento

Guia atual: [Cenário completo e atendimento nativo](ue58/NAVEGACAO_ATENDIMENTO_2026-10-27.md). São 1.620 modelos, 12.910 instâncias e zero modelos ausentes. O bloqueio de navegação em Z910 foi corrigido. A migração integral e a aprovação visual continuam pendentes; a versão Godot aprovada permanece preservada.


## Continuação UE5.8 — persistência nativa

Guia atual: [Saves e continuidade do atendimento](ue58/PERSISTENCIA_2026-10-27.md). Clientes, pedidos parciais, transporte, louça, reservas, jogador e portas são reconstruídos nos saves UE. Preservar a transação atômica entre atendimento e economia, o marcador de consumo e os campos desconhecidos. A conversão integral e o executável UE aprovado continuam pendentes.


## Continuação UE5.8 — prévia de 28/10

Leia [Áudio, visual, natação e entrega Windows](ue58/AUDIO_VISUAL_2026-10-28.md). Esta seção substitui o estado anterior de executável ainda não exportado: a prévia Windows passou no teste externo, com 22 verificações, mixagem gravada e imagens reais revisadas. A conversão integral continua em andamento; não declarar os demais negócios e sistemas marinhos concluídos. Entrega no D, branch `codex/ue58-migration`; manter a instalação Godot.

## Retorno do teste do usuário — expansões

Guia mais recente: [Correções do teste UE de 28/10](ue58/CORRECOES_TESTE_USUARIO_2026-10-28.md).
O usuário relatou ausência de pessoas, interações confusas, objetos deslocados,
visual insuficiente e expansões aparentando ativas. O lote de expansões foi
corrigido e passou em 40 verificações no EXE, com imagens antes/depois da compra.
Inclui hotel, negócios e terreno da piscina, preservando propriedade salva e
pedidos antigos. **As sete frentes aprovadas e os demais relatos permanecem
pendentes conforme a lista do guia; não declarar a conversão integral concluída.**

Pedidos posteriores: rádio com reggae e músicas praianas instrumentais; a placa
física do balcão abre/fecha o quiosque, vermelha quando fechado e verde quando
aberto. Retirar a opção de abrir/fechar do celular, mantendo gestão e horários.

## Checkpoint gráfico avançado de 28/10

Usuário encerrou por limite. Ler [checkpoint gráfico](ue58/CHECKPOINT_GRAFICOS_2026-10-28.md)
e [relatório Nanite/Lumen/PCG](ue58/GRAFICOS_AVANCADOS_2026-10-28.md) antes de retomar.
Projeto ativo no D, branch codex/ue58-migration. Há implementação real, mapas e
benchmark nativo; o último pacote integrado ainda precisa de regressão e inspeção
após a divisão do hotel. Não declarar o lote inteiro nem a migração concluídos.
