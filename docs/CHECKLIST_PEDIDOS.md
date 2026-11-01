# Checklist de pedidos do usuário

Toda solicitação do usuário entra aqui no momento em que é feita e só é marcada quando estiver
implementada **e** validada (compilação, testes pelo MCP, captura real). Mais recente no topo.
Legenda: [x] feito e validado · [~] em andamento/parcial · [ ] pendente.

## 01/11/2026 — continuidade (Claude)

- [x] Assumir o projeto UE5.8, preservar o trabalho do Codex e avançar (branch `codex/ue58-migration`).
- [x] Pendência crítica da demo: campanha travada no capítulo do píer; salário diário, fama, capítulos da vila. (`PROGRESSAO_2026-11-01.md`)
- [x] Gerar prévia Windows e testar (96/96). (pedido "Yes, package it")
- [x] Trabalhar a Unreal pelo MCP do editor.
- [x] Remote Control para conduzir pelo celular.
- [x] Permissões de projeto da Unreal: aceitar sozinho (Computer Use quando o editor aparecer na lista de apps; caso contrário, pelo MCP).
- [x] Após cada lote, seguir o plano do GitHub sem parar a produção.
- [x] Procurar e salvar assets gratuitos; Claude decide quando modelar ou usar asset. (`D:/Assets/PolyHaven`, `tools/ue58/fetch_polyhaven.py`)
- [x] Só gerar executável de teste quando o usuário pedir.
- [x] Hotel 5★: conseguir entrar, decoração e funcionalidade (recepção, renda noturna). (`HOTEL_PRAIA_2026-11-01.md`)
- [x] Praia mais bonita estilo Caribe: areia mais branca, águas claras e belas.
- [x] Ondas quadradas: corrigir (malha do mar graduada 0,75 m).
- [x] Vegetação nas montanhas ao redor (16.896 instâncias CC0).
- [x] Polimento visual: objetos flutuando (26 itens corrigidos; varredura `mare_float_audit`) e 36 malhas facetadas da praia suavizadas (guarda-sóis listrados/palha/sombreiros, armações e mastros; `tools/ue58/smooth_props.py`).
- [x] Rádio: 3 novas músicas originais (Reggae Roots, Calipso Caribe, Praia Pop/ukulele), 6 estações + desligado, nome no celular; testado no PIE.
- [x] Andar pela vila, principalmente quiosque e hotel: regressão 99/99 no PIE, atendimento real com e sem atendente, hotel acessível; adicionado dispensar atendente. (`ue58/CAMINHADA_2026-11-01.md`)
- [~] HUD/celular mais comercial, amigável e fácil: 3 propostas apresentadas (`ue58/hud-propostas/propostas.html`); **aguardando escolha do usuário** para implementar.
- [x] Manter este checklist sempre que o usuário pedir algo (regra salva na memória).

## Regras permanentes já pedidas

- Celular pelo B, placa física do quiosque, balcão antes da mesa, produtos prontos sem preparo, um atendente, pagamento automático.
- Visual realista estilizado aprovado; sem low poly como arte final; licenças registradas em `CREDITS.md`.
- Mitigação Lumen `r.Lumen.AsyncCompute=0` mantida; não alegar desempenho sem medição.
- Saves do jogador preservados; testes com perfis isolados em `D:/CodexTemp`.
