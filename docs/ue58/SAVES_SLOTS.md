# Saves em 3 slots — contrato e auditoria (Pacote 8)

**C++ consultado, não alterado:** `unreal/MareAlta/Source/MareAlta/MareSimulation.cpp/.h` e `MareKioskPersistence.cpp`. A funcionalidade básica **já existe** em C++; não duplicar.

## Implementação atual

- `SlotCount=3`: arquivos `slot1.json`, `slot2.json`, `slot3.json` em `FPaths::ProjectSavedDir()/SaveGames` ou em `-MareSaveRoot=...` para QA.
- `slots.json` com `{"last":N}` conserva o slot ativo. `-MareSlot=N` força a seleção; um perfil antigo com apenas `slot1.json` vira slot 1.
- `LoadSlot` tenta o JSON e depois `slotN.json.bak`. `NewGame` cria perfil a partir de `default_save.json` e grava no slot.
- `Save` guarda estado e captura NPCs do quiosque. `Sleep` faz autosave ao final do dia; operações importantes já chamam `Save()`. `WriteState` grava `.tmp`, copia o arquivo principal para `.bak` e faz move de temp para principal.

## Correção de risco (Claude, C++)

**Risco comprovado pela leitura do código:** depois de recuperar um save de `.bak` porque o principal está corrompido, um novo `WriteState` pode copiar **o principal corrompido** para cima do backup íntegro. Antes de rotacionar `.bak`, validar origem, guardar cópia intacta da última versão boa, validar `.tmp` e substituir atomicamente; recuperar `slots.json` truncado. Validar além da sintaxe (`v`, `company`, `money`, `day`) e ter comportamento claro em save de versão futura. Jamais apagar campos desconhecidos.

## Ferramenta offline

`python tools/ue58/qa/save_check.py --self-test` valida **4 casos**: atual v7, antigo incompleto, JSON truncado e tipo inválido. `python tools/ue58/qa/save_check.py CAMINHO/slot1.json --json` informa erros e campos faltantes em comparação com `Data/default_save.json` (v7). `--strict-missing` torna ausência fatal; `--fallback-bak` apenas lê `.bak`, não regrava nem repara. Objetos de dicionário dinâmico representados por `{}` no default não fornecem esquema interno, logo esta é uma auditoria estrutural, não uma prova de integridade de gameplay.

Fixtures em `tools/ue58/qa/fixtures/`: `save_antigo.json` (legado parcial), `save_atual.json` (igual ao v7, com data alterada), `save_corrompido.json` (incompleto propositalmente). Nunca carregar fixtures no perfil real.

## Steam Cloud — configurar só após QA

Na build Windows, conferir a pasta exata de `FPaths::ProjectSavedDir()/SaveGames`; candidata: `%LOCALAPPDATA%/MareAlta/Saved/SaveGames/`. Auto-Cloud: sincronizar `slot[1-3].json`, `slot[1-3].json.bak` e `slots.json`, **não** `*.tmp`/logs. Confirmar isolamento da demo e do jogo completo (AppIDs diferentes; migração explícita se necessária), conflito de cloud/offline e cópia local segura antes de sobrescrever. Em conflito, pedir decisão ao jogador; nunca decidir pelo saldo financeiro ou dia mais alto.

## QA no jogo (Claude)

Criar e alternar 1→2→3→1 (nomes/saldos/posições/visitantes independentes); autosave de fim de dia, compra/entrega paga uma vez, fechamento do processo durante escrita; corromper principal **apenas em pasta isolada de testes**, recuperar de `.bak` e salvar duas vezes garantindo que cópia boa nunca desapareça; importar perfil legado; testar duas máquinas com Steam Cloud e um conflito offline. Documentar logs e capturas reais.
