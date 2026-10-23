# Guia vigente para as próximas atualizações

Atualizado em **23/10/2026**. Destinado a qualquer IA ou pessoa, sem depender deste
chat. Leia junto com [AGENTS.md](../AGENTS.md). Novos pedidos do usuário prevalecem.

## Base correta

- Projeto: **Maré Alta Resort**, Godot **4.5.1**, GDScript, Forward+ / Vulkan.
- Versão em `project.godot`: **1.1.0**; linha de trabalho **1.1.0 RC2**.
- Branch usada nas entregas: **`codex/resort-1.1-mcp`**.
- Repositório: https://github.com/sergiomrge-tech/simulador-resort
- Última alteração funcional antes deste guia: **`6a0a3c2`**, pedidos nas mesas.
  Verifique `git log` e `git status`; commits posteriores podem ter atualizado a base.
- O jogo começa com o quiosque e evolui por expansões. Gestão no celular (B).

Antes de editar, confira branch/remoto e alterações pendentes. Não use reset,
checkout ou cópia de um build antigo para substituir trabalho existente. Não
trabalhe nos mesmos arquivos ao mesmo tempo que outro chat sem coordenação.

## Regras atuais de produto

1. **Sem preparar produtos.** E na geladeira/armário/cozinha, escolher produto
   pronto, levar ao cliente, E para entregar e receber no caixa. Sem espera,
   cronômetro, etapas de montagem ou necessidade de cozinheiro.
2. **Estoque continua existindo.** Compras abastecem a despensa compartilhada.
   A retirada desconta os insumos uma vez; a entrega não desconta de novo.
   Devolver guarda unidade já paga; retirar a devolução não cobra novamente.
   Produção pendente de save antigo vira unidade pronta uma única vez.
3. **Pedido na mesa.** No atendimento físico, o cliente senta, olha o cardápio e
   aguarda E para anotar. Marcador `E · #pedido`; ao registrar, itens vão para
   HUD/celular. E permite consultar ou entregar quando se carrega o item correto.
   Garçom vai até a mesa para anotar, volta para buscar e entrega. Cliente fica
   sentado para consumir. Não gastar estoque nem reiniciar paciência ao consultar.
4. **Compatibilidade de modos.** `company_enabled()` exige empresa criada e modo
   físico ativo. No modo legado, pedidos continuam automáticos e consultáveis;
   atendimento no balcão é imediato, sem preparo. Antes da empresa, E na estação
   abre o cadastro. Não esconder os móveis por causa desse estado.
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
    bola e braços animados. Dois barcos passam continuamente de dia, em sentidos
    opostos e faixas afastadas. Cruzeiro iluminado fica ancorado à noite, sem
    deslocamento nem esteira de propulsão, conforme correção do usuário.
    Embarcações distantes da faixa de banho/cais; congelar movimento na pausa.
    Quadra deve ficar livre de guarda-sóis/espreguiçadeiras e outros props.

Use modelos detalhados e licenciados, preferencialmente CC0, ou Blender com
malha trabalhada. Não substituir objetos por low poly ou montagens de primitivas
como acabamento final. Reutilize a biblioteca existente e registre licenças em
`CREDITS.md`. Salve fontes `.blend` editáveis, com texturas incorporadas; reabra
para conferir. Atualize downloads/geradores e o catálogo (`tools/gen_item_catalog.py`).

## Onde alterar cada coisa

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
