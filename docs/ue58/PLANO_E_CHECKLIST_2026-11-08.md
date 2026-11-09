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
- [x] **Desempenho, 2ª rodada (08/11):** juntar as peças da vila foi medido antes de fazer: com TODAS as peças do mundo
  exportado do Godot escondidas o ganho seria só +2,5–4 FPS (o render quase não muda) — não compensa. Lumen desligado:
  +3–6. O custo fixo grande era o próprio pacote de teste (Development, com estatísticas). **Pacote Shipping** (o que o
  jogador recebe; compila agora, `package_preview.ps1 -Config Shipping`): praia 81,4 FPS, quiosque 73,1, saguão 64,9,
  vila à noite 63,7 (Development: 63,5 / 66,7 / 67 / 61,3). Com a geração de quadros do DLSS (padrão em RTX 40) o FPS na
  tela praticamente dobra.
- [ ] Desempenho, próximos: vila à noite e saguão (~64 FPS no Shipping, limite no processador do jogo ~12 ms e do render
  ~14 ms): pessoas MetaHuman (4–7 FPS) e luzes; e o mar em ladrilhos para as vistas do mar.
- [x] Fotos aéreas dos 4 lados, de dia e no fim da tarde (08/11).
- [x] Árvores vistas de muito longe perdem as folhas (09/11): as 6 árvores da mata são Nanite com "preservação de forma:
  nenhuma"; ao simplificar, a Nanite apagava as folhas. Ligado "Preserve Area" (feito para folhagem): a 1 km a copa fica cheia.
- [x] B14: borda reta do mar vista do alto (09/11): a malha do mar acabava a 1,3–2,4 km; depois dela aparecia o chão azul
  da atmosfera. Um anel de quadrados grandes leva o mar até 40 km (`gen_ocean.py`) e as ondas zeram nos últimos 150 m do
  mar detalhado (material e `SeaHeight`), sem fresta na junção.
- [ ] Conferir as frestas escuras entre as peças antigas do morro (vistas no levantamento de 05/11).
- [x] Som de motor de barco de verdade (09/11): gravação real de um motor Seffle de 1950 (Wikimedia Commons, Work With
  Sounds, CC BY 4.0, créditos no CREDITS.md e no credits.json), 12 s em loop emendado; na chegada e no passeio pilotado
  (tom e volume seguem o acelerador).
- [ ] Tirar do mapa o que só servia ao ônibus (estrada/ponto), se existir.

### 1.2 Defeitos que já existiam (QA do executável)
- [x] `village_walkers_active`, `rain_mix`, `grass_coverage_cooked`, `grass_nonblocking_culled`: passam no executável desde 08/11 (107/107).
- [x] B4: moradores Aoi e Jorge "deslizando" (09/11): alarme falso da simulação, que media a marcha de quem estava fora da tela
  (pose parada de propósito, `mare.OffscreenPose`). Com todos animados, 0 deslizando; `simulate_game.py` mede como o portão.
- [x] B6: mar verde ao pôr do sol (09/11): a água espalhava mais verde que azul e, com a luz amarela das 16h30–17h30, o mar
  inteiro ficava esmeralda; na praia ainda havia uma faixa verde-limão no horizonte (ângulo rasante). Espalhamento mais azul,
  um pouco mais de absorção do verde e espalhamento reduzido em ângulo rasante. A água rasa continua verde-turquesa.
- [x] B7: palha do telhado do bar (09/11): uma única foto de palha esticada por água do telhado e cumeeira com UV radial.
  `M_ThatchRoof` (`mare_thatch.py`) projeta a palha do Poly Haven a cada 1,2 m com os fios descendo a inclinação, tingida
  de dourado; vale também para o guarda-sol de palha do quiosque.
- [x] B15 (09/11): na demo Shipping instalada, 40 capturas da abertura (60 s) sem o aviso "Preparando shaders"; ele vinha do pacote de teste.
- [ ] B16 (09/11, parcial): o pacote tinha 6,1 GB; as MetaHumans tinham 39 texturas de 8K e 31 de 4K (~4 GB). As 70 ganharam
  `MaxTextureSize` 2048 (`mare_probe_near.cap_textures`). Resultado medido: 6,12 → 5,87 GB (só -250 MB; a estimativa
  por texturas estava errada). Próximo passo: medir o que pesa no .ucas (malhas MetaHuman, groom, roupas) antes de cortar.

### 1.3 Apresentação
- [x] C6 (09/11): na tela inicial toca o "Tema Maré Alta" (`music_tema`) no lugar do rádio; ao começar, baixa suavemente e a
  música do lugar e o rádio voltam (`MareAudioWorld`, `Sim->bTitleOpen`).
- [x] C7 (09/11): tela de carregamento do jogo empacotado (`MareLoading.cpp`, MoviePlayer): arte da tela inicial, folha de
  caderno com uma dica sorteada do `tutorial.json` traduzida e "Carregando..."; em toda troca de mapa (abertura, Carregar,
  Novo jogo em outro slot, voltar ao menu). Só aparece no executável.
- [x] Músicas mais animadas no rádio: as 11 faixas CC0 (`radio_up_01..11`) estão na lista logo depois da Aloha FM (conferido 09/11).
- [x] B13 (09/11): voo da tela inicial (`title.json`) refeito com 16 fotos do percurso: passava a 1 m dos guarda-sóis, do
  telhado do quiosque, das copas dos coqueiros e do mastro do barco a vela; pontos 3-6 mais para o mar e acima do mastro.

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

- [x] C13 (09/11): um em cada três banhistas da toalha deita de bruços (pés juntos, mãos sob o peito; sem o joelho
  dobrado nem as mãos na barriga dos que estão de costas). Um em cada três lê um livro aberto (`tools/ue58/gen_open_book.py`, modelado no bpy) segurado sobre o rosto.
- [x] C14 (09/11): sem pedido, o atendente do bar se volta para o balcão e mexe no tampo a cada 7-12 s (clipe PickUp_Table).
- [x] C18 (09/11): quem chama no evento cômico gesticula enquanto espera (TalkGesture e Cheer alternados a cada 3,5-6 s).
- [x] C19 (09/11): cáusticas do fundo raso mais nítidas e com o dobro do brilho; raios de sol embaixo d'água (10 faixas aditivas na direção do sol,
  `AMareCharacter::UpdateSunShafts`, `M_UnderwaterShaft`), discretos na água rasa clara.
- [x] C20 (09/11): tela de troco no bar e nos negócios (ao fechar o minijogo do balcão, com o total atendido).
- [x] B8 (09/11): a ponta de pedra do píer é a laje `coast_rocks_02` do Poly Haven (46 × 50 m, 1,6 m) com a foto esticada:
  material de rocha projetado no mundo (`rock_face`, 2,6 m) e 11 rochas `rock_face_01/02` em dois grupos (`mare_coast_rocks.point_boulders`).
- [x] B9: conferido em 09/11 de dia e à noite: a faixa turquesa sumiu com a iluminação dos interiores de 06/11.
- [x] B10 (09/11): o salto na piscina virou mergulho de cabeça: o corpo inclina até 78° no arco e chega à água deitado (`dive_pitch`).
- [x] B12 (09/11): `shrub_02/04` (folhas cinza e caules vermelhos, pareciam secos) viraram `shrub_01/03`; tirados ~4.600
  tufos enterrados sob o terreno novo da ilha ou sobre as trilhas e 76 arbustos cuja copa cobria o caminho de cimento
  (`mare_lawn.fix_0911`).
- [ ] B14: fim do plano do mar visto do mirante.
- [ ] Animações da referência (Resort Simulator): mais clipes gratuitos (fila, pegar produto, pagar, deitar), gestos ao interagir.
- [ ] Pesca com isca, briga com o peixe e livro de espécies; desafios no modo foto.
- [x] Rádio do quiosque com troca de faixas: aparelho no quiosque, na casa e no hotel (`radio.json` stereos; conferido 09/11).

---

## Fase 4 — Jogo completo (Acesso Antecipado pago, depois da demo)

- [ ] Grand Hotel inteiro (quartos, VIPs, eventos, restaurante, salão de jogos) revisado com o mapa novo.
- [ ] Lojinha de souvenires: revisão final (3.5, "por último").
- [ ] Balanceamento de 6–10 h (GPT simula; Claude ajusta números no jogo).
- [ ] Final da dívida (só no jogo completo).

---

## Textos e traduções (GPT, em paralelo)

- [x] 08/11 (GPT fora do ar, feito pelo Claude): os 96 textos novos nos 12 idiomas; 4151/4151 em todos; glossário PASS.
- [x] (09/11) Textos montados por partes: o `MareLoc` agora separa frases e contadores "(0/4)", reconhece texto já
  traduzido e número de pedido com nome; 12 pedaços novos (`Data/i18n_pieces.json`) nos 12 idiomas; `tools/ue58/loc_emulate.py`
  repete o tradutor em Python para achar o pedaço que falta. Placa da piscina com "ducha" (estava "duche"). pt-PT: 28
  frases corrigidas ("Pode paga", "Pode pode", "com você" → "consigo", "no ementa", "pra", "frigobar" → "minibar").
- [x] (resolvido em 09/11) Textos montados por partes que o tradutor não reconhece (auditoria `-culture=en -MareLocAudit` no executável, 08/11):
  passos das missões com "

", resumo do dia ("Bom dia! Dia 1 encerrado · vendas..."), "Próximo desbloqueio: ...",
  horário "8h às 18h", número do pedido "#1 Thiago", placas 3D ("PISCINA<br>duche antes de entrar"), rótulo
  "Dormir e encerrar o dia", "Food truck do Pastel", nomes de tecla ("Left Shift"). A fama do HUD já foi corrigida.

- [ ] GPT: `docs/ue58/I18N_TODO_2026-11-07.json` e `I18N_TODO_2026-11-08.json` (dicas da referência, pagamento, chegada de
  barco: "Barqueiro", o cartão "Você pegou o primeiro barco para a ilha." e a carta da dívida com "barco").
- [ ] 👤 Revisão nativa e nomes próprios em chinês/japonês/russo.

---

## Tsunami refeito (08/11, pedido do Sergio com imagens de referência)

- [x] Evento de dia: lembretes 12h e 13h30, presságio 14h, onda 16h (textos "antes das 16h" nos 12 idiomas).
- [x] Céu de tempestade cinza que escurece em ~15 s, sem virar noite e sem chuva (as cortinas desenhavam riscas).
- [x] O mar recua ~3,8 m em todas as praias antes da onda (MPC `Drawback`, mesmo termo em `AMarePerson::SeaHeight`).
- [x] Onda nova: parede escura, verde translúcido sob a crista, espuma por ruído (sem listras), borrifo; cresce de 22 a 60 m.
- [x] Quebra perto da praia (`Break` no WPO): a crista tomba para a frente e vira espuma branca que sobe a areia.
- [x] Mar do dia a dia mais calmo (`mare.SeaCalm` −0,45 → −0,75).
- [x] Defeito antigo: `mare.TsunamiNow` não zerava (prioridade do console) e cada PIE novo disparava a onda.
- QA/filmagem: `mare.TsunamiFreeze 1` segura a onda; `mare.TsunamiBreakQA 0..1` força a quebra.

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

## Pente fino visual de 09/11 (46 fotos de todos os locais, `D:/CodexTemp/claude/ue/tour.py`)
- [x] Faixas escuras na água perto do píer: o terreno novo da ilha acabava 15 m mar adentro a -1,2 m, 1,5-2 m acima do fundo;
  agora desce até -4,5 m e passa por baixo do fundo (`gen_island_terrain.py`).
- [x] Ponta de pedra do farol: rochas menores e assentadas; a laje fica areia molhada embaixo d'água.
- [x] Ponta do píer: vara solta (apoiada em nada) e boia de pé atravessada pelo poste deitadas nas tábuas; ponto de pesca na borda do mar.
- [x] Encosta norte com listras laranja (textura de cima esticada na parede íngreme): rocha projetada de lado nas encostas íngremes.
- [x] Cume: o banco do Seu Tibúrcio olhava para copas de árvore; 40 árvores à frente removidas, agora vê o vulcão e o mar.
- [x] Casa do herói: faixa vermelha no alto da parede da sala (peça terracota do export do Godot) escondida; rodaforro creme.
- [x] B11: a beira da praia já não tem samambaias achatadas (limpeza do gramado).
