# Plano e checklist — depois da ilha completa (08/11/2026)

Pedido do Sergio: "quando terminar a ilha 100%, faça um novo planejamento e checklist para nos orientar e seguir".
Este arquivo é a lista de trabalho a partir de agora. Ele substitui as listas antigas como ordem de execução (as
antigas continuam como histórico e detalhe: `CHECKLIST_EXPANSOES.md`, `REVISAO_DEMO_2026-11-07.md`,
`PENDENCIAS_100.md`, `ROADMAP_STEAM.md`).

Como usar: trabalhar de cima para baixo. Cada item entra com portão de QA PASS, commit, push e foto. Itens marcados
👤 dependem do Sergio. Itens marcados GPT são do GPT (texto, traduções, balanceamento: `gpt-division-of-work`).

---

## Onde estamos

**Ilha completa (feita entre 08/11 manhã e tarde, commits 7c9873bb … 35faa11f e 455d1b38):**

- [x] Contorno da ilha e campo de distância da costa (`island.json`, `island_sdf.bin`, `MareIsland::ShoreDistance`).
- [x] Fundo do mar em volta da ilha inteira, mar nos quatro lados e ondas/espuma seguindo a costa.
- [x] Terreno novo com praias em volta, planície baixa (não é tudo montanha) e o domo do norte virando planície.
- [x] Floresta grande no meio (~12 mil árvores e 17 mil arbustos), coqueiros na praia (~500), pedras assentadas no morro.
- [x] Três trilhas: a do cume (já existia) e duas novas da vila para a floresta (Oeste e Norte), sinuosas e com largura variando.
- [x] Vegetação rasteira: ~440 mil touceiras de capim, samambaias e bromélias em manchas.
- [x] Código que supunha a praia reta: som do mar, gaivotas, pegadas na areia, guarda-sol do evento, som da mata e passos.
- [x] Chegada de barco no lugar do ônibus: o barco vem do mar, atraca de proa no píer, o herói desembarca de frente para a vila,
  o barqueiro vai embora. Barcos da costa passam além do píer (antes atravessavam o píer).
- [x] Tudo vale para o jogo inteiro (demo e jogo completo usam o mesmo mapa).

---

## Fase 1 — Fechar a demo (P0)

Meta: uma demo de ~2 h, estável, bonita, pronta para a Next Fest.

### 1.1 Ilha: conferência final no executável
- [x] Empacotado e instalado (08/11, `D:\Games\MareAltaResort_Demo`). Abertura no executável: natural 13/13 e pulada
  12/12. QA do executável: 102 de 107; as 5 reprovações já existiam (item 1.2). `void_recovery` voltou a passar (quem
  ficava "nadando" dentro da terra sob a praia agora volta ao chão). 17 materiais sem a marca Nanite corrigidos.
- [x] **Desempenho, 1ª rodada (08/11, executável 1080p, sem geração de quadros):** praia 57,6 → 63,5 FPS, quiosque
  59,8 → 66,7, vila à noite 57,6 → 61,3. Feito: Nanite a 2 pixels por aresta (a folhagem recortada era o grosso da
  placa: −2,8 ms), só as 4 luzes mais próximas com sombra (sombras à noite 1.124 → 580 chamadas), Nanite nos coqueiros,
  no fundo e no terreno da ilha e nas peças do fundo do mar, peças do fundo fora do campo de distância. Medição por
  parte (`bench_package.ps1 -Hide`): mar, fundo, floresta e vegetação rasteira custam pouco nas vistas do benchmark.
- [ ] **Desempenho, 2ª rodada (P0):** o limite agora é o processador de render (~14–16 ms, ~4,8 ms sem categoria, igual a
  04/11); sem nenhuma pessoa o jogo fica em 67–72 FPS. Caminhos: juntar as milhares de peças soltas da vila exportadas do
  Godot (2.584 atores) em instâncias/HLOD, menos MetaHumans perto ao mesmo tempo ou LOD mais simples para os de longe,
  e o mar em ladrilhos (2,3 M triângulos desenhados quando aparece). Com a geração de quadros do DLSS (padrão em RTX 40)
  o FPS na tela praticamente dobra.
- [x] Fotos aéreas dos 4 lados, de dia e no fim da tarde (08/11).
- [ ] Árvores vistas de muito longe (~1 km, do alto ou do barco) perdem as folhas e parecem secas: corrigir a máscara
  das folhas na distância (mip da opacidade / LOD com folhagem cheia).
- [ ] B14: borda reta do mar distante vista do alto (fim da malha do mar detalhado).
- [ ] Conferir as frestas escuras entre as peças antigas do morro (vistas no levantamento de 05/11).
- [ ] Som de motor de barco de verdade (gratuito, uso comercial) no lugar do motor do ônibus com tom mais grave.
- [ ] Tirar do mapa o que só servia ao ônibus (estrada/ponto), se existir.

### 1.2 Defeitos que já existiam (QA do executável)
- [ ] `village_walkers_active`, `rain_mix`, `grass_coverage_cooked`, `grass_nonblocking_culled` (reprovam desde antes de 07/11).
- [ ] B4: moradores Aoi e Jorge deslizando em dois momentos.
- [ ] B6: mar verde ao pôr do sol ao longe (conferir de novo com o mar novo).
- [ ] B7: palha do telhado do bar esticada de perto.
- [ ] B15: "Preparando shaders" na tela inicial (precache de PSO no pacote).
- [ ] B16: pacote de 6,7 GB para uma demo (tirar o que é só do hotel, limitar texturas).

### 1.3 Apresentação
- [ ] C6: música própria na tela inicial e fade para o jogo.
- [ ] C7: tela de carregamento com arte e dica.
- [ ] Músicas mais animadas no rádio (11 faixas CC0 já baixadas e normalizadas: conferir e ligar).
- [ ] B13: câmera da tela inicial raspando folhas/telhado (vale para a tela 3D de reserva).

### 1.4 Build para a Steam
- [ ] Build **Shipping** Win64 e teste num PC sem a Unreal.
- [ ] Preset **Baixo** medido para os requisitos mínimos.
- [ ] Integração Steam (Online Subsystem, conquistas da dívida, Steam Cloud, Rich Presence).
- [ ] Simulação da demo inteira do zero até o fim (roteiro `simulate_game.py`) e lista de correções.

---

## Fase 2 — Ilha viva (depois da demo fechada)

A ilha agora é grande e bonita, mas ainda é cenário. Propostas para dar uso a ela (👤 o Sergio escolhe quais e a ordem):

- [ ] 👤 Turistas e moradores passeando nas trilhas (precisa estender a navegação estática para as trilhas e praias novas).
- [ ] 👤 Pontos de parada nas trilhas: mirante na Trilha Norte, banco com vista na Oeste, placas de trilha.
- [ ] 👤 Praia norte com uso: pesca de praia, coleta de cocos/conchas, quiosque secundário (expansão paga).
- [ ] 👤 Passeio de barco da ilha (volta completa à ilha) usando o barco da chegada.
- [ ] 👤 Ponto turístico no morro (estátua original de braços abertos, item 16 das pendências).
- [ ] 👤 Casa do herói com 1 andar (expansão paga, item 19 das pendências).

---

## Fase 3 — Melhorias de jogabilidade e acabamento (P2)

- [ ] C13: banhistas variados (de bruços, sentados lendo).
- [ ] C14: bartender limpando o balcão quando está ocioso.
- [ ] C18: eventos cômicos com gesto, não só fala.
- [ ] C19: cáusticas mais fortes no raso e raios de sol embaixo d'água.
- [ ] C20: troco também no bar e nos negócios.
- [ ] B8: ilhota de pedra lisa na baía → rochas reais.
- [ ] B9: faixa turquesa no teto da cozinha à noite.
- [ ] B10: banhista pulando "em pé" na piscina.
- [ ] B12: manchas de mato seco no gramado da pousada.
- [ ] B14: fim do plano do mar visto do mirante.
- [ ] Animações da referência (Resort Simulator): mais clipes gratuitos (fila, pegar produto, pagar, deitar), gestos ao interagir.
- [ ] Pesca com isca, briga com o peixe e livro de espécies; desafios no modo foto.
- [ ] Rádio do quiosque com troca de faixas (fim da fila).

---

## Fase 4 — Jogo completo (Acesso Antecipado pago, depois da demo)

- [ ] Grand Hotel inteiro (quartos, VIPs, eventos, restaurante, salão de jogos) revisado com o mapa novo.
- [ ] Lojinha de souvenires: revisão final (3.5, "por último").
- [ ] Balanceamento de 6–10 h (GPT simula; Claude ajusta números no jogo).
- [ ] Final da dívida (só no jogo completo).

---

## Textos e traduções (GPT, em paralelo)

- [ ] GPT: `docs/ue58/I18N_TODO_2026-11-07.json` e `I18N_TODO_2026-11-08.json` (dicas da referência, pagamento, chegada de
  barco: "Barqueiro", o cartão "Você pegou o primeiro barco para a ilha." e a carta da dívida com "barco").
- [ ] 👤 Revisão nativa e nomes próprios em chinês/japonês/russo.

---

## Decisões que só o Sergio pode tomar (👤)

- [ ] Conta Steamworks (US$ 100, dados fiscais), App ID do jogo e da demo.
- [ ] Nome final na loja: "Coconut Simulator" (conferir que está livre na Steam e no Google antes de registrar).
- [ ] Qual proposta da Fase 2 vem primeiro.
- [ ] Três propostas de HUD/celular mais comercial (pedido antigo).

---

## Regras que continuam valendo

- Motor só pelo MCP; portão `qa_gate.py` antes de cada commit; foto e análise item a item de toda captura.
- Asset gratuito antes de modelar (Poly Haven, Kenney, Quaternius, ambientCG…), com crédito em `CREDITS.md`.
- Pesado no drive D:; repositório é clone parcial (`GIT_NO_LAZY_FETCH=1`, commit por `commit-tree`).
- Máximo de trabalho na placa de vídeo; medir CPU x GPU no executável antes de concluir.
