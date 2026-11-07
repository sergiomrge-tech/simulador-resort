# Validação local pelo MCP do Godot — 22/10/2026

Base local: `886c2de`, Godot 4.5.1, Windows, GeForce RTX 4060 Ti.

- Ponte do editor confirmada com `get_editor_state`: editor aberto em `scenes/main.tscn`.
- `build/logs/loop-mcp.log`: **LOOP_TEST PASS**, quatro clientes atendidos no rush.
- A navegação de `guest.gd` agora contorna os retângulos de mesas e casas antes de caminhar; o deslizamento continua evitando entrada em obstáculos.
- `main.gd` executa as auditorias antes da captura, sem depender de um temporizador que podia disparar depois do encerramento.
- `build/logs/faxina-mcp.log`: PRIMCHECK, 67 grupos; FLOATCHECK, 3.935 grupos e 42 alertas. São candidatos para inspeção, não 42 defeitos confirmados: incluem lanternas penduradas, decoração na parede e objetos dentro de barcos ou sobre o píer.
- O alerta das mesas do hotel foi conferido no gerador: `hotel_restaurant` tem um piso próprio de 0,35 m. A altura original das mesas foi preservada.
- Capturas Vulkan em `shots/`: balcão, prateleira, carrinho, pilhas de cocos, junina, quermesse, barco, castelo e restaurante. As capturas antigas `castelo_novo` e `hotel_mcp` estavam obstruídas; usar `castelo_mcp` e `hotel_mcp_close`.
- Festa junina: arco do salto aumentado para o personagem passar por cima da chama.
- Pilhas de cocos: camadas compactas com espaçamento coerente com o modelo novo, em vez de anéis com vazios entre os apoios.
- Créditos atualizados e catálogo regenerado.

## Ensaio do pacote

`tools/build_patch.sh 51921df` executado por processo iniciado através do MCP. A seleção de fontes inclui `qnat` e os modelos resolvidos pelos aliases, mesmo ignorados pelo Git.

Uma cópia da instalação `D:/Games/MareAltaResort` está em `build/patch-test`; o jogo original e seus saves não foram alterados.

- `build/patch-test/smoke-final.log`: `[patch] patch_1.0.1.pck ok`, captura gravada, sem `not found`, `SCRIPT ERROR` ou `REAL_MISSING`.
- `build/patch-test/loop-final.log`: **LOOP_TEST PASS**, quatro clientes atendidos no rush.
- Esses ensaios do pacote precedem o último ajuste de espaçamento dos cocos; reexportar e repetir o smoke após esse ajuste antes de entregar.
- Há avisos de recursos/RIDs ainda alocados no encerramento automático do Godot. Não foram tratados como ausência de recursos, nem como prova de encerramento limpo.

## Publicação pendente

O fetch revelou `origin/main` 29 commits à frente da base local (`8f631c0`) e a branch `origin/refine/company-kiosk` com a versão 1.1.0. O GitHub já tem releases candidatas até `v1.1.0-rc2`.

O instalador candidato 1.0.1 tem aproximadamente 134 MiB (PCK de 144 MiB): excede o limite de um arquivo comum do GitHub. Não foi anunciado como atualização final nem publicado. Resolver a linha de versão com o usuário antes de alterar `latest_version.txt`, integrar as mudanças remotas ou disponibilizar esse instalador.

Os `.import` de assets foram atualizados pela importação local no Windows; permanecem fora deste lote de código para evitar versionar alterações de plataforma em massa.
