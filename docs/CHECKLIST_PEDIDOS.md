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
- [x] Vegetação nas montanhas ao redor e pontas da costa (19.324 instâncias CC0).
- [x] Polimento visual: objetos flutuando (26 itens corrigidos; varredura `mare_float_audit`) e 36 malhas facetadas da praia suavizadas (guarda-sóis listrados/palha/sombreiros, armações e mastros; `tools/ue58/smooth_props.py`).
- [x] Rádio: 3 novas músicas originais (Reggae Roots, Calipso Caribe, Praia Pop/ukulele), 6 estações + desligado, nome no celular; testado no PIE.
- [x] Andar pela vila, principalmente quiosque e hotel: regressão 99/99 no PIE, atendimento real com e sem atendente, hotel acessível; adicionado dispensar atendente. (`ue58/CAMINHADA_2026-11-01.md`)
- [x] HUD/celular mais comercial, amigável e fácil: 3 propostas apresentadas (`ue58/hud-propostas/propostas.html`); usuário escolheu **B · Maré Tropical com o celular em abas laterais como na C** — implementado (faixa de madeira, comandas, bilhete de missões, placa de interação, avisos; celular/estações com abas laterais). Captura: `ue58/graphics-reference/hud-b-20261101`.
- [~] Andar por todo o jogo, montar checklist do que precisa ser corrigido e corrigir (feito: janelas + luz noturna, piscinas, espuma, 5.729 objetos empilhados na piscina, mata das pontas; ver `ue58/AUDITORIA_GERAL.md`) (ex.: janelas opacas de todas as construções). Lista detalhada em `ue58/AUDITORIA_GERAL.md`.
- [~] "Continue com os ajustes gráficos" (01/11): grama/conchas/seixos/flores/caibros/fiação recolocados nas posições da Godot (3.994 instâncias); 34 cabelos/câmeras de hóspedes flutuando no hotel removidos; hotel ganha hóspedes no restaurante, academia e bar da piscina. Pendente: interiores dos quartos.
- [x] "Coloque grama e arbustos" + "Preencha até as montanhas, coloque arbustos também" (01/11): gramado cheio (grama CC0 Poly Haven) do resort, vila e lotes até a mata dos morros, com arbustos, samambaias e flores; lotes de expansão somem com a compra (`mare_lawn.py`).
- [x] "Corrigiu os vidros opacos?": sim, na leva da auditoria (janelas das casas com vidro refletivo e luz à noite; demais vidros transparentes). Conferido de novo nas capturas da vila.
- [x] "Os braços ao nadar estão muito estranhos e feios" (01/11): braçada de peito em primeira pessoa (mãos se encontram, estendem, abrem e recolhem, no terço inferior da tela); parado na água, sculling suave. Regressão 100/100. Observação: o modelo da mão é o do personagem e continua simples.
- [ ] "Após terminar os ajustes gráficos e visuais vamos trabalhar no gameplay" (01/11): próxima fase depois dos coqueiros.
- [x] "Os coqueiros não combinam com o ambiente, substitua por assets mais realistas, procure na web" (01/11): Coconut Tree do Fab (Darmawan Pujisetyadi, CC BY 4.0), baixado pelo Chrome logado do usuário para `D:/Assets/Fab`, aplicado nos 171 coqueiros mantendo posições ("Bem melhor").
- [x] "Troque essas árvores também por assets mais realistas" (01/11): as 16 amendoeiras facetadas viraram o HighPoly Tree Model do Fab (Next Spring, CC BY 4.0).
- [x] "Substitua os cocos do jogo por esses da foto" + "Procure no Fab que tem grátis" (01/11): Megascans só é grátis para Fortnite (Personal R$ 10,80); usado o Coconut grátis de Rabeya Akter (Fab Standard License) com casca CC0 palm_bark nos 26 cocos soltos.
- [x] "Nenhum coco fica em pé assim por causa da gravidade" (01/11): cocos deitados de lado (eixo comprido na horizontal), giro diferente por variação. "Os prints mostram em pé": o modelo do Fab era quase uma bola; agora é oval (1,28:1) e achatado onde apoia, afundado 1,5 cm na areia, e o 5º coco de cada pilha encaixa no vão entre os quatro.
- [x] Manter este checklist sempre que o usuário pedir algo (regra salva na memória).

## Regras permanentes já pedidas

- Celular pelo B, placa física do quiosque, balcão antes da mesa, produtos prontos sem preparo, um atendente, pagamento automático.
- Visual realista estilizado aprovado; sem low poly como arte final; licenças registradas em `CREDITS.md`.
- Mitigação Lumen `r.Lumen.AsyncCompute=0` mantida; não alegar desempenho sem medição.
- Saves do jogador preservados; testes com perfis isolados em `D:/CodexTemp`.
