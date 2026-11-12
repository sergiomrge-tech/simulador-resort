# Checkpoint — 09/11/2026 (pausa até 16:30)

Branch `codex/ue58-migration`, último commit `f8d52eea`. Demo Shipping instalada em `D:\Games\MareAltaResort_Demo`
(build de 11:59, teste do executável 107/107), atalho "Coconut Simulator - Demo" na área de trabalho.
Plano completo: [PLANO_E_CHECKLIST_2026-11-08.md](PLANO_E_CHECKLIST_2026-11-08.md).

## Feito hoje (commits 2bb109e0 → f8d52eea)

- Mar até o horizonte (B14 do alto), sem mar verde ao entardecer (B6), árvores com folhas a 1 km, palha do bar (B7),
  motor de barco de verdade (CC BY 4.0), moradores "deslizando" era alarme falso da simulação (B4).
- Traduções: textos montados por partes, 12 pedaços novos nos 12 idiomas, 28 frases do pt-PT, placa "ducha".
- Gramado da pousada (B12), ponta de pedra do farol (B8), voo da tela inicial (B13), mergulho na piscina (B10),
  música própria na tela inicial (C6), tela de carregamento (C7), B9 conferido, B11 conferido, B15 (não aparece no Shipping).
- Banhistas de bruços e lendo (C13), bartender arrumando o balcão (C14), gestos nos eventos cômicos (C18),
  cáusticas e raios de sol embaixo d'água (C19), troco no bar e nos negócios (C20).
- Texturas das MetaHumans limitadas a 2K; B16 fechado (Sergio: até 7 GB está bom; pacote 5,87 GB).
- Pente fino com 46 fotos: faixas escuras na água do píer, rochas da ponta, vara e boia do píer, encosta norte
  listrada, vista do cume tapada por árvores, faixa vermelha na sala da casa do herói.
- Material do chão da ilha passava do limite de 16 texturas do DirectX 11 e sumia no jogo cozido: rocha procedural.

## Retomada às 16:30 (agendada)

1. Refazer com a câmera no lugar certo as fotos que caíram dentro de parede/terreno: bangalô da pousada, casa do
   herói por fora, início da trilha, mata, praia norte, recife nadando (`D:/CodexTemp/claude/ue/tour.py`).
2. Mesma volta de fotos no fim da tarde (`CLOCK=1080`) e à noite (`CLOCK=1290`); analisar item a item e corrigir.
3. Portão de QA, commit/push, pacote, teste do executável, instalar a demo.

## Ainda pendente (do plano)

**Técnico / visual**
- Desempenho da vila à noite e do saguão (~64 FPS no Shipping, limite no processador).
- Frestas escuras entre peças antigas do morro.
- Tirar do mapa o que só servia ao ônibus (estrada/ponto), se existir.
- Fim do plano do mar visto do mirante (conferir com o mar novo; do alto já está resolvido).
- Raios de sol embaixo d'água estão discretos na água rasa clara (aumentar se o Sergio quiser).
- Rodar de novo a exclusão do conteúdo de editor dos plugins (MetaHuman Animator 556 MB, NNE 103 MB) — foi desfeita
  enquanto o erro real era o material da ilha; só se o tamanho voltar a importar (limite 7 GB).

**Build para a Steam**
- Teste num PC sem a Unreal; preset Baixo medido para os requisitos mínimos.
- Integração Steam (conquistas da dívida, Steam Cloud, Rich Presence) — depende da conta Steamworks.
- Simulação da demo inteira do zero ao fim (`tools/ue58/qa/simulate_game.py`) e lista de correções.

**Jogabilidade (Fase 3)**
- Mais animações da referência (fila, pegar produto, pagar), gestos ao interagir.
- Pesca com isca, briga com o peixe, livro de espécies; desafios no modo foto.

**Jogo completo (Fase 4)**
- Grand Hotel revisado com o mapa novo; revisão final da lojinha; balanceamento de 6–10 h; final da dívida.

**Traduções**
- GPT: `I18N_TODO_2026-11-07.json` e `I18N_TODO_2026-11-08.json`.
- Revisão nativa e nomes próprios em chinês, japonês e russo.

## Decisões do Sergio

- Conta Steamworks (US$ 100, dados fiscais), App ID do jogo e da demo.
- Confirmar o nome "Coconut Simulator" (livre na Steam e no Google).
- Qual proposta da Fase 2 vem primeiro: gente nas trilhas, pontos de parada, praia norte com uso, volta de barco na
  ilha, estátua no morro, casa do herói com andar.
- Três propostas de HUD/celular mais comercial.
