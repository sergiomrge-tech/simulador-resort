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
