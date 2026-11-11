# Plano e checklist — depois da ilha completa (08/11/2026)

Pedido do Sergio: "quando terminar a ilha 100%, faça um novo planejamento e checklist para nos orientar e seguir".
Este arquivo é a lista de trabalho a partir de agora. Ele substitui as listas antigas como ordem de execução (as
antigas continuam como histórico e detalhe: `CHECKLIST_EXPANSOES.md`, `REVISAO_DEMO_2026-11-07.md`,
`PENDENCIAS_100.md`, `ROADMAP_STEAM.md`).

Como usar: trabalhar de cima para baixo. Cada item entra com portão de QA PASS, commit, push e foto. Itens marcados
👤 dependem do Sergio. 10/11 (Sergio: "Esquece gpt, faça vc"): textos, traduções e balanceamento agora são do Claude.

---

## Pendências reais — lista única (levantamento de 11/11)

Pedido do Sergio (11/11): "consulte o planejamento e o checklist e veja as pendências". Sete documentos tinham 149
linhas em aberto; a maioria era repetição do mesmo assunto ou item já feito que ninguém marcou. **Esta é a lista que
vale.** Os outros documentos (`PENDENCIAS_100.md`, `ROADMAP_STEAM.md`, `CHECKLIST_EXPANSOES.md`,
`HUMOR_EVENTOS_COMICOS.md`, `AUDITORIA_GERAL.md`, `docs/CHECKLIST_PEDIDOS.md`) ficam como histórico. O cruzamento
"já feito" veio do texto dos documentos e do que se sabe do projeto, não de um teste item a item.

### Depende do Sergio 👤
- [ ] Conta Steamworks (US$ 100, dados fiscais) e App ID do jogo e da demo. Trava: página "Em breve", botão de lista de
  desejos, integração Steam (nuvem, conquistas, Rich Presence), classificação etária, página nos 12 idiomas.
- [ ] Teste do build Shipping num PC sem a Unreal.
- [ ] Nome do jogo: `CHECKLIST_EXPANSOES.md` ainda cita "Coconut Coast: Resort Simulator"; o vigente é "Coconut Simulator". Confirmar.
- [ ] HUD/celular mais comercial: `CHECKLIST_PEDIDOS.md` diz opção B escolhida e feita em 01/11; aqui e no `PENDENCIAS_100` ainda se pedem três propostas. Dizer se está resolvido.
- [ ] Controle (Xbox/PlayStation): código pronto, falta teste com controle físico no executável.
- [ ] Geração de quadros (DLSS): precisa do Sergio clicando na janela durante o teste.
- [ ] Qual item da Fase 2 vem primeiro (lista na Fase 2, abaixo).
- [ ] Crianças e famílias: comprar pacote pago ou seguir sem.
- [ ] Traduções: revisão nativa; transliterar ou não os nomes próprios em chinês, japonês e russo; mais idiomas (cs, hu, ro, da, fi)?
- [ ] Divulgação: preço (US$ 12,99 no roadmap), trailer, playtest fechado, Next Fest.
- [ ] Som ambiente "que não muda nem desliga" (teste da demo): dizer qual som.

### Com o Claude, prontas para fazer
- [x] Lojinha de souvenires: revisão final (11/11): as três páginas jogadas no editor (embrulho perfeito e amassado, compra
  de artesanato, prateleira vendendo por hora, foto -> cartões). Corrigido: linha do artesão quebrava no meio da frase
  (agora duas linhas planejadas) e a miniatura do cartão-postal saía achatada (a legenda esticava a caixa). Fotos em
  `D:/CodexTemp/lojinhaqa`. Ajustes de gosto ficam para quando o Sergio jogar.
- [ ] Banca de jornal verde ao lado da lojinha (vila): é uma caixa lisa do Godot, fora do padrão "nada de caixas";
  trocar por modelo de verdade (procurar gratuito, senão modelar).
- [x] Animações que faltavam (11/11): **telefone** com o aparelho na mão direita junto à orelha (parte de quem espera nas filas dos negócios e do quiosque, e uma pessoa na ponta do píer; `AMarePerson::UpdatePhoneProp`); **levantar da toalha** (clipe LayToIdle do UAL 2, CC0: quem está de costas na toalha se levanta e vai embora ao fim do horário de praia ou na chuva, com o jogador por perto; QA `mare.GetUp`); **píer** com três pessoas de dia (`Data/pier_people.json`). Encostar no corrimão ficou de fora por medida: o píer só tem corda entre estacas de 78 cm e o gesto põe os punhos a 92–95 cm (as mãos pairavam 14 cm acima da estaca); os dois do píer olham o mar de braços cruzados.
- [ ] Gesto de apoiar no corrimão (clipe `Idle_Rail` já importado): precisa de um guarda-corpo de ~93 cm ao alcance da rua (hoje só existem nas sacadas dos sobrados).
- [x] Igreja imponente (pedido do Sergio, 11/11: "mármore com traços de raio, detalhes em ouro, no altar Jesus na cruz"): paredes, pilares, altar e presbitério em mármore branco com veios (textura própria, `marble_image`), colunetas em mármore verde, piso xadrez de mármore polido, capitéis, nervuras, molduras e frisos dourados, abóbadas em marfim; altar-mor com retábulo, resplendor de raios, sacrário e **crucifixo com a figura em mármore** (`tools/ue58/gen_crucifix.py`, corpo humano real posado na cruz, cabelo, barba, coroa e perizônio esculpidos); padre atrás da mesa (`mare_church.highaltar`).
- [x] Recepção principal do Grand Hotel em mármore (pedido do Sergio, 11/11: "bastante detalhes e cores em mármore"): piso creme polido com losangos pretos, faixa vermelha e três rosas dos ventos, colunas vermelhas com base e capitel dourados, paredes em painéis com rodapé verde e filetes dourados, parede de destaque com o emblema, elevadores em mármore preto, balcão revestido, cornija dourada (`tools/ue58/gen_hotel_lobby_marble.py`, `mare_lobby_marble.place`; peça só visual sobre a casca existente).
- [x] Estátua do crucifixo com acabamento de escultura (11/11, "como Michelangelo"): cabelo e barba fundidos numa massa esculpida, perizônio com dobras e espessura, mármore polido.
- [ ] **Todas as roupas do jogo com textura de tecido** (pedido do Sergio, 11/11): falta. Feito só o paramento do padre.
- [ ] **Casa do jogador refeita, mais realista, com desgaste** (pedido do Sergio, 11/11, "quero que você faça, não os outros agentes"): falta.
- [x] Paramento com textura de tecido (11/11, "cor brilhante, precisa ter textura de tecido"): material `M_MH_Vestment`, jacquard do Poly Haven projetado pela posição pré-pose (a peça não tem UV), damasco tom sobre tom, fosco.
- [x] Flores nos jardins (pedido do Sergio, 11/11): canteiro redondo da árvore da praça, as cinco jardineiras de madeira e os dois canteiros azuis da igreja (que tinham flores de palito com bolinha) com gazânias e pervincas do Poly Haven (`mare_gardens.build`, reexecutável).
- [x] Cordas do píer "sem base" (foto do Sergio, 11/11): as cordas do último trecho iam até uma estaca que a plataforma da ponta não tem; dois mourões novos (`mare_pier_post`, `mare_pier.posts`) com as cordas amarradas.
- [x] Banca de jornal da vila (11/11): a caixa verde lisa virou modelo próprio (`mare_newsstand`), com o poste que ficava dentro dela e a jardineira reposicionados e o letreiro na testeira.
- [x] As duas hóspedes de uma mesa do restaurante do hotel eram a mesma MetaHuman com a mesma roupa: os hóspedes não têm
  identificador e o sorteio do corpo caía igual por acaso. Agora pegam a lista do hotel em sequência (`RosterIndex`);
  conferido no jogo (mesa com Celeste e Lorenzo).
- [ ] Cabelo comprido de quem senta inclinado (mesa do restaurante, bancos) fica esticado para trás, rígido: a simulação
  de cabelo só liga no preset Épico e a pose sentada inclina a cabeça ~40°. Opções: ligar a simulação só para quem está
  sentado e perto, ou reduzir a inclinação do pescoço nas poses sentadas. Medir o custo antes.
- [x] Pesca e foto, resto do plano antigo (11/11): o peixe pescado já vai para a cozinha do restaurante (prato "peixe fresco do píer", sem pagar fornecedor) e as fotos do álbum já viram cartões-postais na lojinha; faltavam só os filtros de foto, feitos: O / direcional para cima troca entre natural, verão, sépia, preto e branco e desbotado (prévia de 4 s, aplicado só na foto; `MarePhotoFilter.cpp`, QA `mare.PhotoFilter <i> [s]`).
- [x] Igreja: Padre Robson reza a missa atrás do altar, de frente para os bancos (11/11, `church.json` → `priest`; troca de lugar só com o jogador a 25 m). Paramento (11/11, foto de referência do Sergio): casula vermelha solta sobre a túnica branca, gola branca, punhos e barra brancos, cruz peitoral na corrente, gerada sobre o corpo e o pescoço do próprio MetaHuman (`gen_mh_swimwear.py chasuble`, `metahumans.json` → `named_wear`). Castiçais de mesa que estavam no chão do presbitério foram para cima do altar (`mare_church.candles`). Falta: som da igreja (eco, órgão).
- [x] Sinuca: uma partida jogada até o fim no jogo (11/11, `mare.PoolAutoPlay 1` + `mare.PoolQA` com o salão comprado: 16 tacadas, 7 × 4 para o Seu Bené, a mesa é rearrumada e o jogo volta ao normal; roteiro `sinuca_match.py`).
- [ ] Roupas: vestir os papéis que faltam com as 11 roupas gratuitas já baixadas; móveis e louças do Fab baixados e sem uso.
- [ ] Recife: peixes com cara de desenho; horizonte subaquático vazio.
- [ ] Reteste: 2 h seguidas sem travar, incluindo o hotel (um documento diz feito, outro pede reteste).
- [ ] Sem registro em nenhum documento: acessibilidade básica (texto, legendas, daltonismo), calçados variados, preparativos de festa aparecendo no mapa, cada expansão com horário de pico próprio.
- [ ] Final da dívida no executável do jogo completo (a demo nunca chega lá): só foi visto no editor. 11/11: corrigido o
  caso do pagamento único que pulava a tela final; tela em folha de caderno.

### Já feito que os documentos antigos ainda listam como aberto
Pacote Shipping; menu principal, opções e 3 slots de save; desempenho medido no executável; preset Baixo; eventos
cômicos (`MareComicEvents.cpp`, `comic_events.json`); ilha completa; tradução em 12 idiomas; rádio com troca de faixas;
bar, negócios da vila, restaurante e salão de jogos; pesca com isca, briga e livro; desafios de foto; balanceamento
(fechado em 20 h de campanha); demo de ~2,7 h (os antigos dizem "3 dias").

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
- [x] Desempenho da vila à noite e do saguão. 10/11, demo Shipping instalada (build de 10/11 11h37), 1080p sem geração de
  quadros: praia 72,5 FPS, quiosque 82,9, saguão 102,5 (era 64,9), trilha 102,8, vila à noite 85,3 (era 63,7); tudo acima
  de 60. Sem pessoas a praia vai a 84 (as 6 pessoas na tela custam ~4 ms do processador do jogo). Uma segunda rodada na
  sequência deu 47–69 FPS com a placa a 15–17 ms: outra carga na máquina ao mesmo tempo, descartada.
- [x] Desempenho, próximo (opcional): pessoas na praia (medido em 10/11: sem ganho barato) e o mar em ladrilhos. 11/11,
  executável Shipping, cinco rodadas (`bench_package.ps1 -Hide`): praia com tudo 81,9 e 77,7 FPS (ruído ±4); sem o mar
  84,7 (placa 10,9 ms contra 11,1–11,3); sem a mata 82,5; sem a vegetação rasteira 78,4. O mar custa ~0,3 ms: dividir
  em ladrilhos não paga. Nada alterado.
- [x] Fotos aéreas dos 4 lados, de dia e no fim da tarde (08/11).
- [x] Árvores vistas de muito longe perdem as folhas (09/11): as 6 árvores da mata são Nanite com "preservação de forma:
  nenhuma"; ao simplificar, a Nanite apagava as folhas. Ligado "Preserve Area" (feito para folhagem): a 1 km a copa fica cheia.
- [x] B14: borda reta do mar vista do alto (09/11): a malha do mar acabava a 1,3–2,4 km; depois dela aparecia o chão azul
  da atmosfera. Um anel de quadrados grandes leva o mar até 40 km (`gen_ocean.py`) e as ondas zeram nos últimos 150 m do
  mar detalhado (material e `SeaHeight`), sem fresta na junção.
- [x] Conferir as frestas escuras entre as peças antigas do morro (vistas no levantamento de 05/11). 10/11: varredura do
  morro inteiro por traços (`mare_probe_near.gap_scan`, 3 m e 1 m em volta do cume): 0 buracos; fotos em `D:/CodexTemp/hillgap*`.
- [x] Som de motor de barco de verdade (09/11): gravação real de um motor Seffle de 1950 (Wikimedia Commons, Work With
  Sounds, CC BY 4.0, créditos no CREDITS.md e no credits.json), 12 s em loop emendado; na chegada e no passeio pilotado
  (tom e volume seguem o acelerador).
- [x] Tirar do mapa o que só servia ao ônibus (estrada/ponto), se existir. 10/11: nenhum ator nem dado do ônibus no mapa.

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
- [x] B16 (09/11): decisão do Sergio: até 7 GB está bom; pacote atual 5,87 GB. O pacote tinha 6,1 GB; as MetaHumans tinham 39 texturas de 8K e 31 de 4K (~4 GB). As 70 ganharam
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
- [x] Demo Shipping de 10/11 instalada (`D:\Builds\MareAltaUE58_Shipping_2026-11-10k` → `D:\Games\MareAltaResort_Demo`, 6,20 GB,
  atalho "Coconut Simulator - Demo" na área de trabalho). No executável: QA 107/107; abertura na cópia instalada 13/13. A carta
  da avó em 1280×720 aparece cortada só no quadro em que abre; 2 s depois o texto inteiro cabe (captura nova
  `intro-letter-settled` no teste de abertura). Os scripts de teste param na leitura do `runtime.log`, que o Shipping não
  grava: o resultado vale pelo `preview-qa.json` / `intro-qa.json`.
- [ ] 👤 Teste do build Shipping num PC sem a Unreal.
- [x] Demo Shipping de 11/11 instalada (`D:\Builds\MareAltaUE58_Shipping_2026-11-11b`, 6,21 GB; QA do executável 107/107,
  abertura 13/13): igreja com vitrais, vendedor na barraca do pastel, modo de teste por roteiro.
- [x] Demo Shipping de 11/11 (terceira do dia, `..._2026-11-11f`, 6,24 GB) instalada: vendedores nos cinco negócios,
  animações novas, pesca com isca / briga / livro com as figuras dos oito peixes, desafios de foto. QA do executável
  107/107, abertura 13/13; pescaria fotografada no executável (compra de isca, briga, dois peixes, livro).
- [x] Demo Shipping de 11/11 (segunda do dia) instalada com o interior da igreja (`..._2026-11-11c`; QA do executável
  107/107, abertura 13/13; interior fotografado no executável de dia, de noite e na missa). Na primeiríssima execução
  de um pacote a nave leva ~50 s para aparecer (shader compilando); depois não se repete.
- [x] Preset **Baixo** medido para os requisitos mínimos (11/11, executável Shipping, jogo completo liberado, janela
  1920×1080, escala 3D 80%, RTX 4060 Ti + Ryzen 7 5700G; `bench_package.ps1 -Exec "sg.* 0;..."`):

  | setor | Padrão 1080p | Baixo 1080p | Baixo 720p | placa (ms) padrão / baixo 1080 / baixo 720 |
  |---|---|---|---|---|
  | praia | 81 | 111 | 110 | 11,2 / 6,9 / 4,8 |
  | quiosque | 83 | 128 | 132 | 11,0 / 6,9 / 4,8 |
  | saguão do hotel | 103 | 149 | 143 | 7,8 / 3,8 / 2,8 |
  | trilha da ilha | 106 | 143 | 151 | 8,7 / 6,1 / 4,2 |
  | vila à noite | 89 | 142 | 139 | 10,2 / 5,1 / 3,4 |

  Memória de vídeo em uso (sistema inteiro): 4,5 GB no padrão, 3,4 GB no Baixo. RAM do jogo: 4,3 GB. No Baixo o limite
  passa a ser o processador (jogo 6–8,5 ms), por isso 720p não rende mais que 1080p nesta máquina.
  **Proposta para a página (estimativa por escala de placa; só o teste num PC fraco confirma):** mínimo GTX 1060 6 GB /
  RX 580 8 GB, Ryzen 5 1600 / i5-8400, 12 GB de RAM, 8 GB de disco, DirectX 12 (Baixo, ~40 FPS em 1080p, ~60 em 720p);
  recomendado RTX 3060 / RX 6600 XT, Ryzen 5 5600 / i5-12400, 16 GB (Padrão, 60 FPS em 1080p).
- [x] Conferido no executável (11/11, `script_package.ps1`, roteiro de poses e fotos novo): atendimento do quiosque (a
  atendente vira para o cliente, traz o copo, estende o braço e entrega, +R$ 14), barraca do pastel de dia e de noite com
  fila, minijogo do pastel na barraca (recheio, borda, fritura, entrega paga), tochas acesas, quiosque às 23h normal.
- [x] Barraca do pastel com vendedor (os clientes compravam de um balcão vazio): ponto `vendor` em `business_games.json`.
  11/11: sorveteria (atrás do carrinho), aluguel (dentro da cabana), surfe (sob a tenda) e lojinha (entre o balcão e as
  prateleiras) também têm vendedor; o piso é procurado da altura do peito para baixo (de 3 m o traço caía no telhado).
- [x] Igreja (foto do Sergio, 11/11): a pilastra do meio cruzava a janela central e as janelas eram caixas lisas rosa /
  azul / creme. Pilastras nos vãos entre as janelas e vitrais góticos ornamentados nas duas laterais (3 no oeste, 2 no
  leste, onde a torre ocupa o trecho do terceiro), acesos por dentro à noite. Conferido no editor e no executável.
  Na primeiríssima execução de um pacote os vitrais levam alguns segundos para aparecer (shader compilando).
- [x] Interior da igreja (pedido do Sergio, 11/11, referências da Catedral da Sé, tamanho atual): entra-se andando pela
  porta; nave de três naves com pilares em feixe, arcada, abóbadas de tijolo com nervuras, rosácea sobre a porta, vitrais
  por dentro (acesos de dia) e três novos no fundo (dentro e fora), piso xadrez, 10 bancos, altar elevado, cruz, estante,
  castiçais, três lustres de velas (acesos à noite) e fiéis sentados na missa (7–8h e 17h30–19h). Passagens provadas
  com varredura de cápsula; assentos medidos (0–1 cm). Falta: padre no altar durante a missa; som de igreja (eco, órgão).
- [ ] Integração Steam (Online Subsystem, conquistas da dívida, Steam Cloud, Rich Presence).
- [x] Simulação da demo inteira do zero até o fim (10/11, `simulate_game.py` adaptado à demo, três rodadas em perfil novo;
  detalhe em `CHECKLIST_SIMULACAO.md`). Última rodada, 30 etapas: 0 erros no log, 0 pessoas deslizando, 0 fora do assento,
  save recarregado idêntico, hotel bloqueado na demo, tela de fim aberta.
  - [x] Defeito achado e corrigido: quem senta sem ninguém olhando ficava 52–55 cm fora do assento (Seu Tibúrcio atrás
    do encosto do banco do cume, clientes do bar à noite, hóspedes do restaurante no chão). Checagem nova no portão (`seats`).
  - [x] Roteiro: chegada de barco, fim da demo, hotel bloqueado, atendente no dia 1, tempo 4× mais rápido (`SIM_SPEED`).
  - [x] Banhista de bruços fora da toalha (foto do Sergio): mesmo defeito, corrigido; checagem `lying` no portão.
  - [x] Tochas tiki acesas à noite (chama que tremula e uma luz quente por tocha); as "folhinhas verdes" na areia são as
    algas de enfeite da praia (conferido, não é defeito).

### 1.5 Jogabilidade e desempenho (pedido do Sergio, 10/11, depois da simulação)
- [x] Caixa do jogador no fim da demo (Sergio viu R$ 189.630 na tela de fim: era o dinheiro de teste do QA). Modelo
  econômico com as fórmulas atuais, modo demo, 30 sementes por perfil (`D:/CodexTemp/claude/demo_cash.py` sobre
  `tools/ue58/balance_model.py`): fim da demo no dia 10 / 8,5 / 7 (2,7 h / 2,3 h / 1,9 h: casual, médio, dedicado) com
  R$ 871 / 850 / 1.031 em caixa (P10–P90: R$ 350–1.500). Não sobra dinheiro: o jogador gasta em expansões, equipe e
  decoração conforme ganha. O modelo só não roda direto porque 5 arquivos .cpp mudaram de assinatura; as fórmulas
  extraídas são idênticas às auditadas.
- [x] Tela "Obrigado por jogar a demo!" em folha de caderno (era um cartão creme liso): papel pautado, margem, alfinete
  (`MareNotebook::Page`); foto `D:/CodexTemp/uichk/v3_fim.jpg`. A carta da avó também foi conferida em foto (abre certa).
- [x] Olhar para baixo a pé limitado a −66° (`UMarePlayerPresentation`): de −70° em diante o peito facetado do herói e a
  borda dos braços escondidos tomavam a tela; a −60/−65° só o sapato e a perna. Nadando o limite continua livre (recife).
  Fotos `D:/CodexTemp/uichk/look_m.jpg` e `v2_m.jpg`.
- [x] Desempenho: pessoas na praia. Medido em 6 rodadas na demo instalada (10/11, `D:/CodexTemp/claude/bench_people.txt`):
  duas rodadas completas deram 77,9 e 75,5 FPS (ruído de ±4); sem ninguém, 83 (as pessoas custam 5–7 FPS no total); sem
  cabelo, sem animação de rosto e sem sombra das pessoas ficaram dentro do ruído (70–78). O limite da praia é a placa
  (~11,5 ms), não o processador. Todos os setores acima de 70 FPS em todas as rodadas, sem geração de quadros. Sem ganho
  barato nas pessoas: nada alterado.
- [x] "Homem falando com parede" (foto do Sergio, 10/11, saguão do Grand Hotel no benchmark): o par de conversa do
  saguão ficava em y 5760 e 5880 com a fachada de vidro da torre em y 5773 entre os dois (medido por traço), um do lado
  de fora com o rosto no vidro. Os dois agora ficam dentro (y 5940 e 6060, 1,1 m livres em volta). Checagem nova
  `MARE_TALKERS` (`AMarePerson::TalksToWall`: com alguém à frente, a linha entre as duas cabeças tem de estar livre; sem
  ninguém, nada sólido a 60 cm do rosto) no portão e na simulação. Fotos `D:/CodexTemp/lobbyqa/m2.jpg`.
- [x] Bar da Piscina do hotel com um guarda-sol e duas espreguiçadeiras montados na frente do balcão (achado pela checagem
  nova): a copa cobria a cabeça dos hóspedes e os encostos encostavam nas pernas. O conjunto do meio saiu (9 peças,
  `mare_fix_1110.bar_front`); os dois dos lados ficam.
- [x] Duração da demo no perfil casual: 2,7 h para um teto de 2,5 h. Decisão do Sergio (10/11): "pode ficar 2.7h"; nada
  a ajustar nos preços.
- [ ] 👤 Botão "Lista de desejos na Steam" na tela de fim: só aparece com o endereço da loja (`events.json`
  `review_url`), que depende da conta Steamworks.
- [x] "As mãos estão muito estranhas, parece do avesso" (Sergio, 10/11, vendo as pessoas no jogo). Medido em todos os
  clipes (`mare_metahuman.finger_report`): os 5 clipes originais têm os dedos na pose relaxada (0°); os 19 que entraram
  pelo importador da Quaternius (sentar e levantar, pegar do balcão, correr, pular, golpes do vôlei, dirigir, nadar parado
  e os novos) tinham os ossos da palma girados 64–179° depois da adaptação ao corpo MetaHuman: mão virada, dedos em
  garra. Estava no jogo desde 07/11. Os dedos desses clipes agora usam a mão relaxada do clipe parado
  (`relax_fingers`, braços e punhos mantêm o movimento); o importador faz isso sozinho daqui em diante. Depois: 0° nos 19.
  Folha de conferência num corpo parado: `D:/CodexTemp/clipsheet/m.jpg` (`D:/CodexTemp/claude/ue/clip_sheet.py`).
- [x] Espera com mais vida (referência, item 9): biblioteca Quaternius UAL 2 Standard (CC0, mesmo esqueleto, crédito no
  CREDITS.md). Metade dos clientes que aguardam o pedido no quiosque e das pessoas nas filas dos negócios espera de
  braços cruzados (`AMarePerson::WaitPose`). Importados e ainda sem uso: telefone (falta o celular na mão), apoiar no
  corrimão, carregar com as duas mãos. "Yes" é um braço erguido (não é aceno) e "Consume" leva a mão acima da cabeça:
  conferidos em foto e não usados. Comando de teste `mare.Pose <clipe> [raio]`.
- [x] "Excluir esse food truck" (Sergio, 10/11, foto do caminhão vermelho na rua da vila). Decisão dele: o negócio do
  pastel continua e vira barraca. Caminhão e traseira saíram do nível; `mare_stall_pastel` (gerador de barracas, variante
  com estufa de pastéis, bancada e tabuletas vermelhas) no mesmo ponto, balcão do lado onde era a janela do caminhão, com
  tacho, jarra, tábua e botijão do Poly Haven (CC0, créditos no CREDITS.md); letreiros "Barraca do Pastel". Nome e textos
  nos 13 idiomas (7 chaves novas × 12 traduções, 4170/4170, glossário PASS). O id interno continua `food_truck` (saves,
  conquistas e missões não mudam). Conferido no jogo: rua vazia antes da compra, barraca e fila de clientes depois, noite certa (fotos `D:/CodexTemp/stallqa/g_m.jpg`, `n_m.jpg`); portão PASS.
- [x] Animação de atendimento no quiosque (Sergio, 10/11: "faça animação de atendimento"; referência, item 9). O atendente
  vira de frente para quem atende, gesticula ao anotar o pedido (`Idle_Talking`), estende o braço ao entregar (`Interact`) e
  faz o gesto de recolher ao limpar a mesa; o produto fica meio segundo na mão dele durante o gesto e só então aparece na
  mão do cliente, que já está pegando (`UMareKioskWorld::UpdateAttendant`, `HandoverLeft`). Filmado quadro a quadro de lado e
  por trás (`D:/CodexTemp/serviceqa3/zoom.jpg`, `serviceqa2/zoom.jpg`): postura ereta, mãos relaxadas, nada atravessando o balcão.
  `Walk_Carry` (andar agachado de quem leva peso) não foi usado: o produto já vai na mão à frente do corpo.
- [x] Moradores com nome e história com o sexo trocado (achado nas capturas do executável, 10/11): "Dona Roberta" era um
  homem de barba. O corpo vinha de um sorteio na lista mista da vila. Agora cada um tem corpo fixo (`metahumans.json` "named":
  Dona Roberta = Ada, Dona Cecília = Celeste, Alana = Tuya, Seu Severino = Omari, Padre Robson = Lorenzo), escolhidos numa folha
  com todas as mulheres (`D:/CodexTemp/womensheet/m.jpg`; Etta tem a cabeça raspada e lê como homem). Aoi (homem de barba)
  entrou na lista `men`: era tratado como mulher (calçado). Fotos `D:/CodexTemp/namedqa/m2.jpg`.

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
- [x] B14: fim do plano do mar visto do mirante. 10/11: do cume o mar vai até o horizonte (anel de 40 km de 09/11).
- [~] Animações da referência (Resort Simulator): mais clipes gratuitos (fila, pegar produto, pagar, deitar), gestos ao interagir.
  11/11: quem conversa sentado gesticula (`Sitting_Talking`, UAL 1) e o cliente que cansa de esperar balança a cabeça
  antes de sair (`Idle_No`, UAL 2); atendimento, fila de braços cruzados e pegar no balcão já estavam (10/11).
  Falta: telefone (precisa do aparelho na mão), encostar no corrimão do píer, levantar da toalha. Pendência vista:
  as duas hóspedes de uma mesa do restaurante do hotel são a mesma MetaHuman com a mesma roupa.
- [x] Pesca com isca, briga com o peixe e livro de espécies; desafios no modo foto (11/11, `MareFishing.cpp`, `leisure.json`).
  Iscas: massa de pão (livre), camarão (R$ 20 por 5) e lula (R$ 45 por 5), compradas no próprio painel (teclas 1, 2, 3).
  8 espécies, cada uma com isca preferida, força e, em três casos, horário (xaréu no fim da tarde, peixe-espada à noite).
  Briga: segurar recolhe a linha e sobe a tensão; o peixe puxa em arrancadas; a linha arrebenta no vermelho e o peixe
  se solta com a linha frouxa (sardinha ~5 s, a maior garoupa ~40 s jogando certo; só segurar arrebenta em 1,6 s).
  Livro (tecla L): contagem e recorde de cada espécie, dica para as que faltam; espécie nova dá mais fama e o livro
  completo paga R$ 300. Desafios de foto: 5 metas de uma foto só (farol + píer, pôr do sol, pôr do sol com o farol,
  quiosque + bar, três pontos); cada foto diz qual é o próximo. Testes `FishingFight` e `FishingBook`; 48 textos novos
  nos 12 idiomas. Conferido no jogo (`mare.Fish`): compra de isca, briga na tela, 3 peixes pegos, livro preenchido.
  Figuras dos 8 peixes (pedido do Sergio: procurar asset gratuito, senão modelar): busca na web sem nenhum modelo
  gratuito realista com licença comercial; os oito foram modelados no bpy (`gen_fish.py`) e a figura de perfil de cada
  um aparece no livro (silhueta escura até pescar) e no aviso de peixe pescado (`mare_fish.icons`, `/Game/UI/Fish`).
- [x] Rádio do quiosque com troca de faixas: aparelho no quiosque, na casa e no hotel (`radio.json` stereos; conferido 09/11).

---

## Fase 4 — Jogo completo (Acesso Antecipado pago, depois da demo)

- [x] Grand Hotel inteiro (quartos, VIPs, eventos, restaurante, salão de jogos) revisado com o mapa novo. 10/11: saguão,
  recepção, sinuca, sofás, torre vista de cima, piscina, corredor e suíte fotografados (`D:/CodexTemp/hotel1`), sem defeito.
- [x] Lojinha de souvenires: revisão final (3.5, "por último"). Feita em 11/11 (ver "Pendências reais").
- [x] Balanceamento de 6–10 h: **fechado por decisão do Sergio (11/11): "Campanha deixa com 20h"**. A simulação dá ~20 h
  para concluir a campanha e quitar a dívida (`BALANCEAMENTO.md`); acelerar ~2,3x encurtaria também a demo (2,7 h).
  Nada alterado nos números.
- [x] Final da dívida (só no jogo completo). 11/11, conferido jogando no editor com `mare.QA paydebt <reais>|all`: carta da
  Dona Dilce ao criar a empresa, marcos de 25 / 50 / 75 % como dica, e com o saldo zero (celular fechado) a tela "Maré Alta,
  dívida baixa: zero!" com a fala dela e os botões Continuar no resort / Créditos; fotos em `D:/CodexTemp/debtqa`. A tela
  passou a usar a folha de caderno (era o cartão creme liso). Falta ver no executável do jogo completo (a demo nunca chega lá).

---

## Textos e traduções (Claude)

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

- [x] 10/11: textos pendentes de 07 e 08/11 conferidos: os 12 idiomas estão completos (4170/4170, glossário PASS), inclusive as 21 falas do mar no lugar do vulcão. Antes: GPT: `docs/ue58/I18N_TODO_2026-11-07.json` e `I18N_TODO_2026-11-08.json` (dicas da referência, pagamento, chegada de
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
