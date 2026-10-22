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

`build/rc2-playable/Jogar.vbs` abre `MareAltaResort.exe` e o PCK completo 1.1.0 exportado nesta máquina. O runtime Windows 4.5.1 foi reutilizado da instalação existente. Os saves desta cópia ficam em seu próprio `userdata/`; a instalação `D:/Games/MareAltaResort` não foi alterada.

O PCK tem 1.733.165.240 bytes. SHA-256: `d6692c8b74f5e9f190424f916e42dbeebd5b1814dccfcdb2a9c493d9e6e344c1`.

A cópia completa é necessária para carregar o núcleo e os autoloads 1.1.0 desde a inicialização. O candidato antigo `patch_1.0.1.pck` não é a entrega desta linha. Não foi publicada outra release nem alterado `latest_version.txt`.

Instalação por NSIS sobre a versão antiga, migração dos saves reais do jogador e um turno operado manualmente não foram executados nesta rodada. Os testes de migração usam saves isolados de teste.

O snapshot dos imports locais anteriores à integração foi preservado no stash `imports locais antes da integracao 1.1`. Não restaurar em massa sobre os imports novos sem comparar o conteúdo.
