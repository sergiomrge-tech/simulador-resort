# Integração local da 1.1.0 RC2 — 22/10/2026

Linha escolhida pelo Sergio: continuar a versão mais nova. A branch `codex/resort-1.1-mcp` integra `origin/refine/company-kiosk` (`300c7e6`, que contém a RC2 `d107960`) com o checkpoint local `b57cfbe`.

## Resultado

- Sistema de empresa, save v7 e migração v6 preservados da RC2.
- Preservados os desvios locais dos NPCs em torno de mesas/casas, props detalhados nas mãos, pilhas compactas de cocos e salto da junina.
- Auditorias de primitivas/apoios terminam antes da captura.
- Área sem vegetação ampliada atrás do quiosque: o capim atravessava o acesso ao novo anexo. Capturas Vulkan antes/depois confirmam o acesso livre.
- Gerados e importados os dez modelos próprios de pratos/equipamentos. Baixados os quatro modelos Kenney que faltavam na cópia local, com suavização do downloader.
- Catálogo atualizado para 2.034 entradas, mantendo os códigos existentes.

## Testes no Windows, Godot 4.5.1

Executados por processos iniciados pelo MCP do Godot; cada teste usa um APPDATA separado em `build/`.

| Teste | Log | Resultado |
|---|---|---|
| Referências, ownership e espera assíncrona | `build/logs/rc2-lifecycle.log` | LIFECYCLE_TEST PASS |
| Reserva, chegada, consumo, saída e fila | `build/logs/rc2-kiosk.log` | KIOSK_TEST PASS |
| Modelos de pedidos/entrega e limpeza | `build/logs/rc2-orders.log` | ORDER_VISUAL_TEST PASS |
| Ciclo completo da fonte | `build/logs/rc2-loop.log` | LOOP_TEST PASS |
| Empresa na fonte, após restaurar pratos/talheres | `build/logs/rc2-company-final.log` | COMPANY_TEST PASS |
| Empresa no PCK exportado | `build/logs/rc2-pack-company.log` | COMPANY_TEST PASS |
| Ciclo completo no PCK exportado | `build/logs/rc2-pack-loop.log` | LOOP_TEST PASS |
| Captura Vulkan do PCK, com empresa/todas as expansões | `build/logs/rc2-pack-visual.log` | SHOT_SAVED, sem recursos ausentes ou erros de script |

Os logs finais da empresa, na fonte e no PCK, contêm os quatro marcadores de conclusão: preservação do rascunho; preparo/retirada/percurso/entrega pelo cozinheiro e garçom; caminhada/limpeza da louça; suspensão do garçom na folga.

Capturas inspecionadas: `shots/rc2_empresa_final.png`, `shots/rc2_empresa_noite.png` e `shots/rc2_pack_visual.png`.

Continuam os avisos conhecidos de UID com fallback textual na fonte e de recursos/RIDs/ObjectDB no encerramento automático da engine. Não foram considerados encerramento limpo; os marcadores PASS e a ausência de SCRIPT ERROR/REAL_MISSING foram verificados separadamente.

## Cópia jogável

### Controles do quiosque e personalização (22/10/2026)

**Ampliação posterior:** as três frentes de gestão solicitadas foram implementadas em [SIMULACAO_QUIOSQUE.md](SIMULACAO_QUIOSQUE.md). Usar essa documentação para horários configuráveis, custos, reposição, validade e escalas; os horários fixos descritos no checkpoint abaixo são o padrão de migração.

No celular, **B → Meu Quiosque**, ou **E** mirando a placa frontal: abrir/fechar novas chegadas, nome de até 24 caracteres, fonte, cor, prévia e botão **Salvar nome e placa**. O fechamento mantém os clientes existentes; o horário continua 08:00–18:00, ou até 21:00 com neon. A escolha de funcionamento persiste no save, sem alterar a abertura dos saves antigos. A placa ABERTO/FECHADO acompanha o controle imediatamente.

`kiosk-controls-company.log` e `kiosk-controls-pack-company.log` validam fechamento sem expulsão, bloqueio de novas chegadas, horários, migração, save/recarga, interação com a placa, atualização do nome no cenário e preservação do rascunho. `kiosk-controls-loop.log`: LOOP_TEST PASS. A captura `shots/kiosk_controls_ui_final.png` foi inspecionada; o formulário cabe no celular e o texto digitado tem contraste. O checksum corrente da cópia jogável está em `build/rc2-playable/SHA256SUMS.txt`; os hashes abaixo documentam os pacotes anteriores.

`build/rc2-playable/Jogar.vbs` abre `MareAltaResort.exe` e o PCK completo 1.1.0 exportado nesta máquina. O runtime Windows 4.5.1 foi reutilizado da instalação existente. Os saves desta cópia ficam em seu próprio `userdata/`; a instalação `D:/Games/MareAltaResort` não foi alterada.

O primeiro PCK da integração tinha 1.733.165.240 bytes e SHA-256 `d6692c8b74f5e9f190424f916e42dbeebd5b1814dccfcdb2a9c493d9e6e344c1`.

Atualização de áudio solicitada pelo Sergio no mesmo dia: trilha original `music_relax.ogg` (64 BPM, estéreo, 30 s, sem vozes/percussão marcada), música de fundo 7 dB mais baixa e remoção do `village_murmur`. Mar, aves e demais efeitos preservados. O pacote jogável foi reexportado. `build/logs/audio-pack-check.log` confirmou `AUDIO_TEST PASS`, faixa nova tocando em loop a -20 dB e ausência do player de vozes. SHA-256 do PCK atualizado: `98bb6643045371441eb4a2c13e0603502b376100b48a5e45ad6a6e9ae7ab02cd`.

A cópia completa é necessária para carregar o núcleo e os autoloads 1.1.0 desde a inicialização. O candidato antigo `patch_1.0.1.pck` não é a entrega desta linha. Não foi publicada outra release nem alterado `latest_version.txt`.

Instalação por NSIS sobre a versão antiga, migração dos saves reais do jogador e um turno operado manualmente não foram executados nesta rodada. Os testes de migração usam saves isolados de teste.

O snapshot dos imports locais anteriores à integração foi preservado no stash `imports locais antes da integracao 1.1`. Não restaurar em massa sobre os imports novos sem comparar o conteúdo.

### Gestão ampliada — validação final (22/10/2026)

O pacote completo atualizado passou em `simulation-final-pack.log` (SIMULATION_TEST PASS) e `simulation-company-final-pack.log` (COMPANY_TEST PASS), sem SCRIPT ERROR ou REAL_MISSING nesses logs. O ciclo completo passou em `simulation-loop-pack.log` (LOOP_TEST PASS). A validação cobre horários e dias, reposição com orçamento, turnos e salários, perdas, custos, save/recarga e preservação dos formulários durante transações. Permanecem os avisos conhecidos de recursos no encerramento automático.

As telas de horários, estoque, equipe e resultado foram capturadas e inspecionadas em `shots/simulation_*.png`. O resultado exibido usa movimento de caixa e compras da despensa compartilhada; a margem por prato é uma estimativa pelo preço atual dos fornecedores.

PCK final: SHA-256 `385a25fac6499ef3c0ce3eea6dc64c04e2b56918ba58b2c8b7c1247ffab6fd63`. A cópia jogável inclui `GESTAO_DO_QUIOSQUE.md`.

### Cais: chão e recuperação de quedas (22/10/2026)

Relato do jogador: queda sem fim ao andar no cais. A regressão reproduziu o defeito antes da correção (`pier-before.log`: PIER_TEST FAIL, 160 pontos sem piso). Os modelos do Blender eram somente visuais; a alternativa procedural tinha colisão, mas não era usada com os GLBs presentes.

`details.gd` agora acrescenta piso físico aos oito módulos e à plataforma, com sobreposição nas emendas e topo coincidente com as tábuas (y=0,37). A rampa de acesso foi alinhada ao deck e tem piso visível com textura. Os limites da plataforma acompanham o final real do modelo. O nado só começa abaixo da superfície; o jogador sobre o cais continua andando. Quedas abaixo do terreno retornam ao último piso seguro, ou ao ponto de despertar se ainda não houver apoio registrado na sessão.

`pier-ramp.log` e `pier-pack.log`: PIER_TEST PASS. A regressão verifica 171 pontos de piso, caminhada real da praia ao fim, contenção na borda, volta pela rampa, permanência sobre o mar sem nadar, recuperação de queda e nado fora do cais. `pier-loop.log`: LOOP_TEST PASS. Capturas Vulkan inspecionadas: `shots/pier_fixed.png` e `shots/pier_pack_fixed.png` (esta última do pacote exportado). Permanecem os avisos conhecidos no encerramento automático; sem SCRIPT ERROR ou REAL_MISSING nas validações do cais.

Pacote corrigido: SHA-256 `46e78d8a6dd8c720f434141569239a1974d47faa9fee8095e4fe89f299c24a6a`. ZIP completo em `C:/Users/sergi/Downloads/MareAltaResort_1.1_CaisCorrigido.zip`, com CRC de todos os arquivos verificado. Os saves reais não foram alterados.

`pier-loop-pack.log`: LOOP_TEST PASS no pacote final (dinheiro=5406, estrelas=4,48, bar=12), sem SCRIPT ERROR ou REAL_MISSING. `pier-visual-pack.log` confirmou SHOT_SAVED da captura Vulkan desse mesmo pacote.

### Vidros, barcos e passos (22/10/2026)

Os vidros de janelas/portas da vila, casa e hotel usam `VM.window_glass`: branco neutro com alfa 0,16, sem metal ou emissão. O material das lâmpadas permanece separado; a rotina noturna não colore os vidros. O barco vermelho passou de (74; -26,6) para (82; -29,5) em XZ. O barco verde perto da plataforma foi afastado de x=75,2 para x=76; os AABBs transformados de casco, mastro e vela ficam fora do piso do cais.

Passos antigos foram substituídos por quinze pisadas curtas Kenney Impact Sounds (CC0), cinco por superfície. Impactos abafados na areia/terra, madeira no cais/decks e concreto nas calçadas, com identificação do material por raycast. Volume -18 dB (antes -14), sem repetir a mesma variante consecutivamente; espaçamento de 1,5 m andando e 1,85 m correndo (antes 0,75/0,95). A reprodução real dos AudioStreamPlayers é exercitada com driver Dummy em saves de teste; a avaliação subjetiva do áudio continua a cargo do jogador.

`glass-boat-steps-final.log`: PIER_TEST PASS na fonte, incluindo cores neutras de dia/noite, barcos sem sobreposição, quinze clipes sem loop, piso e caminhada, classificação de superfícies, 29 pisadas na ida/volta e silêncio parado. Capturas Vulkan inspecionadas: `shots/glass_clear.png` e `shots/boat_clear_pier.png`.

PCK atualizado: SHA-256 `d339aec50cdbcfed030067f562cb85b4c2e8854f7412a88073f5357ea4dee464`. O ZIP `MareAltaResort_1.1_CaisCorrigido.zip` em Downloads foi atualizado com as três correções; CRC de todos os arquivos verificado.

`glass-boat-steps-pack.log`: PIER_TEST PASS no pacote exportado, com as mesmas verificações de vidro, barcos e áudio e 29 pisadas. `glass-boat-loop-pack.log`: LOOP_TEST PASS (dinheiro=5232, estrelas=4,54, bar=12). Sem SCRIPT ERROR ou REAL_MISSING nesses logs; permanecem os avisos conhecidos de recursos no encerramento automático.

### Celular sem corte lateral (22/10/2026)

Relato: conteúdo do celular cortado nas laterais. A captura `shots/phone_before_home.png` confirmou que nomes compridos dos apps alargavam a grade de quatro colunas para fora da tela. O aparelho agora usa escala máxima 0,9 e se adapta à janela; ícones de 64 px, três colunas, fontes/botões menores e quebra de linha. Cartões usam a largura disponível do ScrollContainer, sem mínimo fixo que ignore a barra de rolagem. Prêmios do Álbum passam para outra linha quando necessário.

`phone-layout-final.log`: PHONE_LAYOUT_TEST PASS, 132 verificações (21 apps + início, em 1280×720, 800×600 e 360×640), com nome de 24 letras W, equipe contratada e quatro bangalôs. Verifica os limites horizontais de todos os controles e o encaixe do aparelho na janela. Capturas inspecionadas: `shots/phone_after_home.png` e `shots/phone_company_fit.png`. Conteúdo longo continua acessível por rolagem vertical.

`phone-layout-pack.log`: PHONE_LAYOUT_TEST PASS no pacote final, repetindo as 132 verificações. SHA-256 do PCK: `7f806518bf4aa584dd1eabd07ebda85f46bbe77b62261c84566f79148fb427a8`. O ZIP existente `MareAltaResort_1.1_CaisCorrigido.zip` em Downloads contém esta atualização; todos os CRCs foram verificados.

Regressões do mesmo pacote: `phone-loop-pack.log` LOOP_TEST PASS (dinheiro=5147, estrelas=4,54, bar=12); `phone-company-pack.log` COMPANY_TEST PASS, incluindo formulário, rascunhos e gravação da placa. Sem SCRIPT ERROR ou REAL_MISSING nesses logs. Permanecem os avisos conhecidos de recursos no encerramento automático.

### Sugestões 2 a 7 — gestão completa (22/10/2026)

Implementação e regras em [ROTINAS_QUIOSQUE.md](ROTINAS_QUIOSQUE.md): rotina de abertura/fechamento, perfis de contratação, encomendas com prazo, equipamentos, personalização com prévia e demanda por hora/clima. Dados sob `company.sim.management`, com padrões de migração e checklist obrigatório opcional. A simulação usa os modelos existentes; mesas movem malha, assento, entrega e bloqueio em conjunto. Ao carregar um save sem identidade comprada, o visual original é restaurado.

Validação na fonte: `management-world-final.log` MANAGEMENT_TEST PASS com Vulkan e capturas; `management-company-check.log` COMPANY_TEST PASS; `management-simulation.log` SIMULATION_TEST PASS; `management-loop.log` LOOP_TEST PASS. Um problema de precisão dos floats no roundtrip foi corrigido normalizando estado/higiene no sanitize.

Validação do PCK final:

| Log em build/logs | Resultado |
|---|---|
| management-final-pack.log | MANAGEMENT_TEST PASS, com Vulkan e testes de interface/cenário |
| management-loop-pack.log | LOOP_TEST PASS, dinheiro=5437, estrelas=4,57, bar=12 |
| management-layout-pack.log | PHONE_LAYOUT_TEST PASS, 168 verificações nos 27 apps e início em três tamanhos |
| management-company-pack.log | COMPANY_TEST PASS |
| management-simulation-pack.log | SIMULATION_TEST PASS, preservando estoque, salários, custos e validade anteriores |

O teste novo cobre cobrança e entrega única após recarga, quantidade mínima/cotação inválida, candidato pelo preço anunciado, salário e jornada, desgaste e bloqueio do equipamento sem consumir ingrediente, serviço pendente após recarga, duração/limpeza/melhoria, risco de perda, prévia sem gasto, compra pela interface, pintura real, deslocamento físico, uniforme, horário/clima e seleção de mesa abrigada, requisitos de fechamento, diferença de caixa sem criar dinheiro e conservação de bebida limitada a uma noite. Também verifica que editar quantidades não destrói o formulário.

Capturas inspecionadas do pacote final: `shots/management_world.png`, `management_recrutamento.png`, `management_fornecedores.png`, `management_equipamentos.png`, `management_movimento.png` e `management_personalizar.png`. Os campos numéricos novos usam texto escuro após revisão de contraste. Não houve SCRIPT ERROR ou REAL_MISSING nos logs finais acima; continuam os avisos conhecidos de recursos no encerramento automático.

PCK deste checkpoint: SHA-256 `5d992cdd678cafc044a2dc4a20cfc608ef2bf766c5aa11790539b8b6a0f56eb5`. ZIP atualizado naquele momento no mesmo caminho `C:/Users/sergi/Downloads/MareAltaResort_1.1_CaisCorrigido.zip` (1.830.768.380 bytes), com todos os CRCs verificados. Inclui `ROTINAS_DO_QUIOSQUE.md` e a documentação anterior. Os saves reais do jogador e a instalação D:/Games não foram alterados.

## Quiosque prático e fachada — revisão final de 22/10/2026

Pedido posterior do Sergio: menos opções repetidas, todas as estações dentro do
quiosque, geladeira compreensível, pedidos claros e tela limpa. Implementação em
[QUIOSQUE_PRATICO.md](QUIOSQUE_PRATICO.md). O anexo foi removido; duas entradas laterais
e uma linha interna de geladeira/retirada/cozinha preservam o atendimento físico.
O celular tem seis áreas iniciais. Os caminhos antigos continuam aceitos internamente,
sem duplicar atalhos na tela inicial. Estações priorizam receitas pedidas e mostram
disponível/consumo; ingredientes visíveis não criam produtos preparados gratuitos.

Cinco modelos Blender originais: fachada, cobertura em fiadas, moldura de neon,
cozinha e liquidificador. `.blend` preservados/reabertos em `art/blender/`, com imagem
de madeira incorporada. `art/.gdignore` impede importar ou exportar fontes artísticas.
O gerador integra `fetch_assets.py`; catálogo de itens regenerado com códigos estáveis.

Fonte: `practical-workflow2.log` PRACTICAL_TEST PASS, `practical-company2.log`
COMPANY_TEST PASS, `practical-management.log` MANAGEMENT_TEST PASS,
`practical-layout1.log` PHONE_LAYOUT_TEST PASS e `practical-loop-final.log`
LOOP_TEST PASS (dinheiro=5562, estrelas=4,55, bar=14).

Todos os logs abaixo são do PCK de entrega, usando saves/configurações de teste:

| Log | Resultado |
|---|---|
| practical-delivery-workflow.log | PRACTICAL_TEST PASS, Vulkan; movimento com colisão pelas entradas, preparo, retirada, entrega e navegação |
| practical-delivery-layout.log | PHONE_LAYOUT_TEST PASS; 204 verificações nos apps/rotas e início, em três resoluções |
| practical-delivery-company.log | COMPANY_TEST PASS; marca, atendimento, percurso da equipe, caixa e limpeza |
| practical-delivery-management.log | MANAGEMENT_TEST PASS; rotina, estoque, salários, entregas, manutenção e personalização |
| practical-delivery-loop.log | LOOP_TEST PASS; dinheiro=5117, estrelas=4,45, bar=12 |

Sem SCRIPT ERROR ou REAL_MISSING nesses logs. Persistem os avisos conhecidos de
recursos/materiais no encerramento automático. O teste de caminhada confirmou
y=0,101 no deck e y=0,001 na areia, sem queda. A primeira asserção tratava a saída
para a areia como deck; foi corrigida para respeitar os dois pisos. O ciclo geral
também detectou o marco `areas.grill` ausente após substituir a chapa; o marco foi
restaurado sem duplicar equipamentos e o ciclo foi repetido com sucesso.

Capturas finais do executável inspecionadas: `shots/practical_workroom.png`,
`practical_station.png`, `practical_phone.png`, `practical_orders.png` e
`practical_facade.png`. Conferência noturna adicional em `practical_night.png` na fonte.

PCK final: 1.740.071.356 bytes, SHA-256
`926204d89476fe0e3dbc9f0874c25a73ce061c15aa1cae55bda216a97d9359d5`.
ZIP em Downloads no mesmo caminho: 1.836.751.194 bytes, nove arquivos, todos os CRCs
verificados; sem userdata. O pacote ganhou `QUIOSQUE_PRATICO.md` e instruções de
atendimento novas. `build/rc2-playable/Jogar.vbs` abre a cópia atualizada. Saves do
jogador e a instalação em D:/Games preservados. Reempacotamento reproduzível:
`python tools/package_quiosque_portable.py`.

## Expositores sempre preenchidos — 22/10/2026

Pedido seguinte do Sergio: geladeira e armário devem ter os produtos vendidos e
não ficar vazios. A exposição agora preenche três prateleiras em cada móvel,
com bebidas e pratos do catálogo correspondente. Receitas básicas bloqueadas são
identificadas; secretos continuam condicionados à descoberta. Cada receita tem
etiqueta de estoque real. Ao retirar a última unidade, as referências visuais
permanecem; a etiqueta indica preparar mais e a retirada continua bloqueada no zero.
Quantidades, ingredientes, dinheiro, produção e saves não são alterados pelo expositor.
A cache inclui catálogo/cardápio e acompanha mudanças de receita durante a operação.

Fonte: `shelves-filled.log` PRACTICAL_TEST PASS e conferência visual do interior.
PCK de entrega: `shelves-pack-practical.log` PRACTICAL_TEST PASS, incluindo estoque
zero, bloqueio de retirada da referência, preparo, etiqueta atualizada e permanência
após retirar a última unidade; `shelves-pack-company.log` COMPANY_TEST PASS.
Sem SCRIPT ERROR/REAL_MISSING; avisos de encerramento já documentados persistem.
Captura inspecionada: `shots/practical_workroom.png`, agora com prateleiras preenchidas.

PCK: 1.740.073.324 bytes; SHA-256
`530876383fddb4a97ebefd7894e40d7a9f886213f348b3c2242d34c32eea0319`.
ZIP atualizado no mesmo caminho de Downloads: 1.836.753.556 bytes, nove arquivos,
CRCs verificados e sem userdata. Documentação e instruções do expositor atualizadas.
# Funcionários presentes e geladeira ampliada — 22/10/2026

- Fonte: `staff-practical.log` PRACTICAL_TEST PASS em Vulkan, com inspeção de
  `shots/practical_facade.png` (caixa no balcão) e `practical_workroom.png`.
- `staff-company.log`: COMPANY_TEST PASS, incluindo trabalho automático.
- PCK: `staff-loop.log` LOOP_TEST PASS, ciclo geral sem erros de script.
- PCK: `staff-pack.log` PRACTICAL_TEST PASS. Contratação imediata com jogo pausado
  e loja fechada, limite do turno, demissão, atendente legado, folga, 12 bebidas,
  preparo, retirada e entrega. Sem SCRIPT ERROR/REAL_MISSING.
- SHA-256 PCK: `35dce12a574def7353476ccab1de851bcb189ee3c4f848f52a2b2039de1f7fa2`.
- ZIP de Downloads atualizado e CRC conferido, sem incluir saves. Avisos de
  material nulo e recursos na saída permanecem no encerramento dos testes.
# Parede e personagens sem chapéus — 23/10/2026

- `no-hats-proof.log` e `no-hats-pack.log`: PRACTICAL_TEST PASS em Vulkan.
- Inspeção de roupa e cabelo em pé, andando e sentado nas capturas
  `practical_clothing*.png`. Corpos preservados; braços/mãos da base original;
  cabelos rígidos presos a Head. Removidos todos os chapéus/bonés.
- Parede traseira com teste de raycast; entradas laterais e serviço preservados.
- `clothes-whole-company.log`: COMPANY_TEST PASS.
- PCK SHA-256: `a01c8728fc301431129ae3158e8e61a67f4405ce7caf09cb52b3d03465e6a0e6`.
- ZIP em Downloads atualizado, CRC conferido e sem saves do jogador.
- Permanecem avisos já existentes de recursos/material no encerramento do motor.
# Roupas casuais — 23/10/2026

- Barra das camisas encurtada e reta; cano dos calçados reduzido a 15 cm,
  com pernas da base original entre o calçado e a calça. Cores mais neutras.
- Fonte `casual-proof.log` e PCK `casual-pack.log`: PRACTICAL_TEST PASS,
  sem SCRIPT ERROR nem recursos ausentes. Conferidas capturas em pé, andando
  e sentado. Mantida a remoção dos chapéus.
- PCK SHA-256: `87fe02c4ac8a50406cb41dbd9a80f54a909a989d308107838239b8e346b1902e`.
- ZIP atualizado em Downloads e CRC conferido, preservando os saves.
# Acabamento do quiosque — 23/10/2026

- Azulejos com juntas, prateleira com suportes e coifa com filtro/duto/luz
  integrados à fachada Blender existente. Fonte reaberta: KIOSK_BLEND_PORTABLE PASS.
- Fonte `kiosk-finish-proof.log` e pacote `kiosk-finish-pack.log`:
  PRACTICAL_TEST PASS. Conferida captura `practical_workroom.png` no Vulkan.
  Circulação, preparo, retirada e entrega preservados; sem erros de script ou
  recursos ausentes. Avisos conhecidos de encerramento do motor permanecem.
- SHA-256 PCK: `df7c8c0799877648bd9742d01e9a4bf3ec091f0f1cb1992bdacdfd87c4c3596c`.
- ZIP em Downloads atualizado e CRC conferido, sem incluir/apagar saves.
# Refinamento de materiais e luz — 23/10/2026

- Azulejos retangulares areia com juntas suaves e variação discreta de material.
- Luz de trabalho quente, sem sombra dinâmica, na área interna do quiosque.
- Conferido `practical_workroom.png` no Vulkan: equipamentos mais legíveis e
  madeira mais quente. Não foram alteradas posições, colisões ou interações.
- `refine-proof.log` (fonte) e `refine-pack.log` (PCK): PRACTICAL_TEST PASS,
  sem SCRIPT ERROR ou recursos ausentes. Avisos conhecidos de saída permanecem.
- PCK SHA-256: `be191881c6ee638e3697b1f855cdaac7cf27106034769a1207d43edac88a1388`.
- ZIP de Downloads atualizado com CRC conferido e saves preservados.
# Refinamento de pessoas — 23/10/2026

- Cabeças entre 1,06–1,14 e menor variação de porte; preservado o estilo cartoon.
- Pele e cabelo com iluminação difusa suave; menor brilho lateral e saturação
  das roupas. Retirados colares de esferas e estampas aleatórias das calças.
- Fonte `people-refine-proof.log` e pacote `people-refine-pack.log`:
  PRACTICAL_TEST PASS, sem SCRIPT ERROR ou recursos ausentes. Inspeção de
  `people_portraits.png` e capturas em pé/andando/sentado. Avisos de saída conhecidos.
- PCK SHA-256: `40af90c04c7f7c2e013a63e15138c6756c6c04a850240f4ee730b4eab66aa486`.
- ZIP atualizado em Downloads, CRC conferido e saves preservados.
# Óculos proporcionais — 23/10/2026

- Lentes menores/ovais, armação fina escura e encaixe a 0,093 m do osso da
  cabeça, com escala 0,9. Fonte Blender salva/reaberta e GLB atualizado.
- `glasses-proof.log`: PRACTICAL_TEST PASS, retrato masculino/feminino com
  óculos forçados para inspeção, além de andar e sentar. Conferido people_portraits.png.
- `glasses-pack.log`: PRACTICAL_TEST PASS. Sem erros de script/recursos ausentes.
  Permanecem os avisos conhecidos de recursos no encerramento do motor.
- SHA-256 PCK: `3ce2443d864a2eeff632c0efd803ead05823bbb786a91aa6b56872024d210170`.
- ZIP de Downloads atualizado e CRC verificado; saves preservados.
# Sete refinamentos integrados — 23/10/2026

- Escopo e limites em REFINAMENTO_COMPLETO.md. Fontes Blender de roupas/avental
  e conjunto de balcão salvas e reabertas. Cinco WAVs originais sem vozes.
- Fonte: `seven3-proof.log` PRACTICAL_TEST PASS, `seven2-company.log`
  COMPANY_TEST PASS. Conferidos retratos, gesto de preparo, circulação, balcão,
  bermudas e capturas de pôr do sol/noite.
- PCK: `seven-pack-visual.log` PRACTICAL_TEST PASS em Vulkan;
  `seven-pack-company.log` COMPANY_TEST PASS; `seven-pack-loop.log` LOOP_TEST PASS.
- `seven-pack-audio.log`: PRACTICAL_TEST PASS com driver Dummy, incluindo
  carregamento/duração dos cinco sons e reprodução posicional com limite de repetição.
- Sem SCRIPT ERROR/recursos ausentes nos testes finais. Continuam avisos já
  existentes de material/recursos no encerramento do motor.
- SHA-256 PCK: `da59a2b1432376a332599587c7bd68e07771b918b4262b1699cfe807261d3014`.
- ZIP em Downloads atualizado, CRC conferido, documentação incluída, sem saves.

# Avental ajustado e pessoas sem óculos — 23/10/2026

- Óculos escuros removidos de todos os Guest, inclusive da preparação das imagens
  de teste. A biblioteca Blender do acessório foi preservada sem uso nas pessoas.
- Aventais masculino/feminino com perfil ajustado à roupa, bolso, alças e cintura,
  bordas e espessura; deformação contínua no quadril e folga para a caminhada.
- Fontes Blender com texturas incorporadas salvas e reabertas.
- Fonte: apron3-no-glasses.log PRACTICAL_TEST PASS. Executável/PCK:
  apron-pack-visual.log PRACTICAL_TEST PASS; apron-pack-loop.log LOOP_TEST PASS.
- Conferidos retrato, preparo, andar e sentar. Sem SCRIPT ERROR/recursos ausentes;
  permanecem os avisos de materiais/RID já conhecidos no encerramento.
- PCK SHA256: 25b4bfcd4e6827f0c314c31901e5d3f961ecee8a8b88d2539f6920dadaf5cc1b.
- ZIP em Downloads atualizado, 10 arquivos, CRC verificado, sem incluir saves.

# Casa, cores naturais e quiosque visível — 23/10/2026
- Nova fonte editável player_home_details.blend salva/reaberta. Cozinha, cortinas,
  persianas, molduras e acabamentos; piso claro, porta de madeira e tapete neutro.
- Paleta global e saturação revisadas por pedido explícito em tudo; mapas dos
  modelos mantidos, sem reforço artificial laranja. Ver REFINAMENTO_COMPLETO.md.
- Corrigido KioskOperations oculto quando empresa não criada. E abre cadastro.
- Fonte natural-practical.log e PCK natural-pack-practical.log: PRACTICAL_TEST PASS,
  incluindo ausência de empresa. Cenário original sem empresa capturado também em
  kiosk_restored.png. Interior home_natural.png e fachada home_exterior_pack.png.
- Sem SCRIPT ERROR/recursos ausentes nos testes finais; avisos conhecidos de saída.
- PCK SHA256: 33bf471c1900967bf72671bfc613336ac5b44469ef567d4bad554ccef53330f5.
