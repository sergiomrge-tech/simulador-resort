# Pendências para o jogo ficar 100%

02/11/2026. Lista única de tudo que falta para o Maré Alta Resort ficar completo, por área, com prioridade.
O lado Steam/lançamento (conta, página, integração, demo) está em `ROADMAP_STEAM.md`; aqui está o **jogo**.
Fontes:
- checklist de pedidos;
- `AUDITORIA_GERAL.md`;
- `PENDENCIAS_2026-10-29.md`;
- plano de gameplay;
- testes no editor e no PIE de 02/11.

Prioridade:
- **P0:** defeito visível ou quebra;
- **P1:** sistema/conteúdo essencial;
- **P2:** acabamento.

Marcar `[x]` só depois de testado no jogo, com foto ou teste automático.

## 0. Correção geral antes de novas mecânicas (pedido do Sergio, 03/11)
Nada de mecânica nova até esta seção fechar. Cada passada roda uma auditoria com dados, corrige o que achar e anexa a prova.
- [x] P0 Movimentação natural: auditoria de marcha (`gait_audit.py`: quem anda mexe pés e mãos) em todos os personagens,
  dia/noite, vila/praia/hotel/quiosque/equipe; 0 deslizando. (Causa achada: esqueleto oculto do MetaHuman com
  `OnlyTickPoseWhenRendered`, 11 de 14 pedestres deslizando.) Corrigido (`AMarePerson::SetMetaHuman` força
  `AlwaysTickPoseAndRefreshBones`; a vila só otimiza quem não é MetaHuman). Prova 03/11: 6 rodadas, dia, noite e quiosque
  aberto, 11–14 pessoas andando por rodada (moradores, garçom, guia, camareira, piscineiro, cliente), 0 deslizando.
- [x] P0 Eventos cômicos já feitos (HUM-001/002/004/005/006/007/008) conferidos por captura e estabilizados.
  03/11: gaivota (tamanho real, só voa com caminho livre de telhado/guarda-sol, bico no prato), guarda-sol (cópia ISM
  com as cores, deita na areia, banhista vai buscar, E recoloca), influencer (selfie com IK do braço), atendente
  (tropeço e bandeja), turista perdido, Seu Arnaldo e pescador; capturas analisadas; teste ComicEvents ok.
- [x] P0 Log limpo: PIE de vários minutos sem `Error`/`Ensure`/avisos de material/`missing`; testes automáticos 100%.
  03/11: portão `tools/ue58/qa/qa_gate.py` PASS: 27/27 testes, 0 linhas de erro no PIE (dia e noite).
- [x] P0 Pessoas: postura sentada/em pé/andando, roupas sem atravessar, cabelos, calçados; ninguém dentro de móvel.
  03/11: auditoria de assento (12/12 ok, pelve 13-14 cm, 2 cm do centro) e em pé (0 dentro de móvel) em 4 rodadas;
  close-ups de sentados (balcão, terraço do hotel) e andando conferidos.
- [x] P0 Objetos: flutuando, primitivos, low poly e colisões (auditorias `float_audit`/`primitives`/`lowpoly`) sem novidades.
  03/11: 585 marcações conferidas por amostragem: peixes do recife, folhas de vaso, luzes da piscina, azulejos, varal,
  vasos pendurados, livros na estante, mensageiro de conchas, caixotes fechados = falsos positivos. Linha de base
  congelada no portão (não pode aumentar).
- [x] P0 Ciclo do quiosque completo no PIE (abrir, pedido, entrega, pagamento, limpeza, fechar, dormir, salvar/carregar).
  03/11: achado e corrigido: cliente preso atrás da cadeira desistia da mesa e ia embora com a comida; agora tenta o
  caminho de novo (12 s/24 s) e senta se estiver a <3 m. Execução: 10/10 clientes chegam, pedem, recebem, comem e saem;
  6 mesas sujas limpas; caixa sobe; salvar/recarregar sem pedido/mesa duplicados. QA amplo (MarePreviewQA) 104/104.
  HUM-006: o quiosque não sobrescreve mais a velocidade do atendente durante o tropeço (0 cm medido).
- [x] P0 Sistemas já feitos revisados no PIE: bar, piscina, pousada, hotel, negócios, passeios, festas, salão de jogos,
  celular (todos os apps), clima, noite, mar, natação, áudio.
  03/11: QA amplo 104/104 (natação, celular, pausa, noite, chuva, rádio, casa, vila, capítulos, sono, hotel, recife,
  expansões, personalização); 27 testes (bar, piscina, pousada, hotel, negócios, passeios, festas, equipe); os 7 apps
  do celular conferidos por captura; varredura dia/noite de todos os marcadores. Corrigidos: bússola com nomes
  sobrepostos (largura medida da fonte) e letreiro do food truck espelhado sobre o teto (pintado nas laterais).
- [x] P0 Interface: todas as telas no padrão caderno (03/11, pedido do Sergio): menu principal, pausa, opções, diálogos
  da vila/eventos e carta da avó convertidos (`MareNotebookStyle.h`); diálogo com respostas quebrando linha dentro da folha.
- [x] P0 Varredura visual final por área (montagem de capturas analisadas item a item) e desempenho no editor.
  03/11: fotos de referência fixas no portão + varredura de todos os marcadores de dia e de noite analisadas; noite clara
  nas primeiras fotos = adaptação de exposição após teleporte (estabiliza em ~10 s, medido); mosaico de orca na
  piscina é intencional. Editor PIE ~35-38 FPS em todas as áreas (indicador; FPS real no executável, item próprio).
- [x] P0 Simulação do jogo inteiro depois das auditorias acima: perfil novo, avançando todas as etapas (dias, expansões,
  capítulos, negócios até o Grand Hotel), registrando cada erro em `docs/ue58/CHECKLIST_SIMULACAO.md`.
  03/11: `tools/ue58/qa/simulate_game.py` (perfil novo, 30 etapas, 0 erros de log, 0 deslizando); achados em
  `docs/ue58/CHECKLIST_SIMULACAO.md`.
- [x] P0 Corrigir TODOS os itens de `CHECKLIST_SIMULACAO.md` (com prova) antes de qualquer mecânica nova (03/11, commit 5f10bf6f).

## 1. Defeitos conhecidos (corrigir primeiro)
- [x] P0 **Biquíni novo (top faixa e parte de baixo até a virilha)** importado e conferido nas 6 banhistas
  (Ada, Asha, Zuri, Celeste, Jelena, Tuya), 02/11.
- [x] P0 **MetaHumans descalços**: chinelo e tênis feitos sobre o pé dos MetaHumans (`tools/ue58/gen_mh_shoes.py`), conferidos no PIE, 02/11.
- [x] P0 **Roupa padrão da Epic** pintada por papel (`metahumans.json` → `clothes`), conferida no PIE, 02/11. Roupas de modelos
  variados (regata, vestido, camisa social) continuam na seção 5.
- [x] P1 Toalha em cima da cama do bangalô sujo: ampliada 2,8× (foto `toalha-negociacao-20261102.jpg`).
- [x] P1 Faixa de pele um pouco mais clara onde ficava a roupa íntima assada (02/11): a cor já estava certa; o mapa
  SRMF mantinha rugosidade/especular de tecido (255/127 contra ~160/160 da pele). `mh_skin_underwear.py` agora preenche
  também o SRMF; 7 corpos de banho reimportados; foto `docs/ue58/graphics-reference/pele-banhistas-20261102.jpg`.
- [x] P1 Zuri careca (preset da Epic): retirada dos elencos (02/11) até ganhar cabelo.
- [x] P1 Vasos de pachira do saguão do hotel com colisão de copa enorme (bloqueia a mira). Corrigir a colisão (03/11: Sergio autorizou mexer nos arquivos do saguão) Feito 03/11: caixa só no tronco (60×60×110 cm, `mare_hud trunkbox`); raio a 87 cm bate no tronco, a 217 cm atravessa a copa.
  quando o Sergio liberar esses arquivos, que têm mudanças dele.
- [x] P1 Painel da negociação: detalhes numa linha própria e botões em duas fileiras, conferido no jogo (02/11).
- [x] P2 Bainha da sunga boxer marcada e furos no cós (02/11): a sunga agora é uma peça única copiada da pele entre o
  cós e as barras (cortes retos, costura central soldada, uma subdivisão), sem o degrau entre quadril e pernas;
  foto `docs/ue58/graphics-reference/sunga-20261102.jpg`.

## 2. Migração Godot → Unreal ainda incompleta
- [x] P1 **Pesca no píer** e **modo foto (P)** com álbum (02/11): E na ponta do píer abre a pescaria (espera, "fisgou!",
  janela curta para puxar; 5 espécies com tamanho, garoupa rara); cada peixe vai ao estoque (capítulo do Seu Gregory).
  P (ou direcional para baixo) tira a foto sem a interface, salva em `Saved/Album` e registra no álbum o que estava
  enquadrado (farol, píer, hotel, quiosque, bar, piscina): a foto do farol cumpre o passo do Padre Robson.
  `MareLeisure.cpp`, `Content/Data/leisure.json`, teste `MareAlta.Gameplay.FishingPhotoChapters`. Falta: vara de pesca na mão
  e uma página de álbum no celular.
- [x] P1 **Capítulos 2–4 da vila** com contagem real (02/11): peixes da pescaria, foto do farol, receitas = drinks
  descobertos no bar (o texto do capítulo "Sabores" foi atualizado; a cozinha experimental da Godot não foi portada),
  negócios contam só os comprados.
- [x] P1 **Festas e eventos do calendário** (02/11): eventos do dia da Godot (calor, lua cheia, maré alta, tempestade) e
  festas semanais a partir do dia 8 (quermesse, junina, show do DJ; carnaval depois do capítulo da prefeita); previsão
  do dia seguinte e preparativos pagos na agenda do celular (decoração da festa ou proteção do estoque); clientes
  conforme o evento; tempestade com chuva, perda de estoque sem preparativos e passeios de mar cancelados.
  Cenário na praia: barracas, bandeirinhas, fogueira com chamas e luz tremulando, cabine do DJ, faixa (modelos
  `tools/ue58/gen_festival.py`). `MareEvents.cpp`, `MareEventsWorld.cpp`, `Content/Data/events.json`, teste
  `MareAlta.Gameplay.DayEventsParties`. Falta: mar mais agitado na tempestade e na maré alta (o material do mar não tem
  parâmetro de ondas), pessoas dançando a quadrilha e música própria de cada festa.
- [x] P1 **Minijogo dos negócios** (3 rodadas da Godot): portado em 02/11 (balcão de cada negócio, seção 3).
- [x] P1 Corpo do jogador em primeira pessoa: pegar, carregar, devolver, portas, natação e mergulho re-testados pela QA
  completa (`-MarePreviewQA`, 104/104 em 02/11, pasta de save limpa antes de cada rodada).
- [x] P1 Abertura: ônibus detalhado, desembarque (pode pular), caminhada até a casa, porta e carta re-testados pela
  QA `-MareIntroQA` (11/11 em 02/11, save limpo).
- [x] P1 Casa: sofá, TV, som, chuveiro e cama conferidos pela QA completa com capturas (02/11, `home-*.png`).
- [ ] P2 [adiado-usuario] (03/11: "deixa o fundo do mar para depois") Horizonte subaquático azul e vazio. Material
  `M_UnderwaterFog` pronto (`mare_materials.build_underwater_fog`), falta ligar como blendable na câmera Eyes e conferir. (Animais da vila:
  gatos e cachorros saíram do jogo a pedido do Sergio, 03/11.)
- [ ] P2 Peixes do recife com cara de desenho (malhas corpo+cauda do Godot) [bloqueado-usuario]: os melhores gratuitos
  são escaneamentos CC0 da ffishAsia no Sketchfab, que exige login. 03/11: o acesso ao Chrome foi negado duas vezes
  (o Sergio pode estar usando o PC). Basta entrar no Sketchfab no Chrome (Google/Epic) uma vez; os downloads seguem
  por script. Candidatos (CC0): peixe-anjo listrado a5c0bb6877184e698c1992e5ce1a69d0, budião dac672386dd741af8485fcab811b9db4,
  garoupa afefbdad11ae4f5da06c6943f7bbf573, vermelho d253b4e2651644e0aadc7a17b955c051, bodião 30a07294d36c4539b23f398e522dd910,
  xaréu (cardume) cad0abfc668e4e3486e930491ac0d840. Os CC0 do Smithsonian (baiacu, peixe-cofre) são espécimes secos de museu.
- [x] P2 Interior dos quartos do hotel além da suíte visitável (a torre é casca com fachada). 03/11: as portas de varanda dos 32 quartos ganharam vida pelo vidro (`M_HotelRoomWindow`, `mare_hotel_lobby.hotel_room_windows`): de dia, cortinas puxadas para um ou os dois lados aparecem pelo vidro escuro; à noite ~45% dos quartos acendem com luz quente, mais fraca atrás da cortina, sorteio fixo por quarto. Guarda-corpos e lobby continuam com o vidro do hotel (separados no espaço da malha). Prova: `docs/ue58/graphics-reference/hotel-quartos-noite-20261103.jpg`, `hotel-quartos-dia-20261103.jpg`.

## 3. Gameplay: cada lugar com algo para fazer
Pronto e testado (02/11):
- quiosque completo;
- pousada com recepção, negociação e limpeza;
- hotel com recepção de VIPs;
- HUD de estrelas, quartos e vendas;
- preço por produto;
- fama trazendo clientes;
- sinuca (física, IA e aposta).

- [x] P1 **Bar do Coqueiro** (M8, 02/11): clientes sentam nas banquetas com pedidos (do cardápio, "me surpreenda" ou um
  drink desconhecido com dica); o jogador mistura até 5 ingredientes na coqueteleira; 11 receitas (2 conhecidas no início),
  descobrir dá fama; gorjeta pela rapidez; reposição de ingredientes; o bartender serve sozinho o que está no cardápio.
  Dados em `Content/Data/bar.json`, lógica em `MareBar.cpp`, mundo em `MareBarWorld.cpp`, teste `MareAlta.Gameplay.BarDrinks`.
  Falta: animação do bartender preparando e copo no balcão.
- [x] P1 **Negócios da vila**, uma tarefa curta cada (02/11): balcão com E em cada negócio comprado e um cliente esperando
  quando há atendimento na hora; minijogo de 3 rodadas da Godot portado (pranchas, food truck, sorveteria, souvenires, surfe),
  pagamento e fama pelos acertos, uma vez por hora dentro do horário. `MareBusiness.cpp`, `MareBusinessWorld.cpp`,
  `Content/Data/business_games.json`, teste `MareAlta.Gameplay.BusinessCounter`. Falta foto do cliente na nova posição ao
  lado do balcão e conferir os balcões do food truck, souvenires, aluguel e surfe no jogo.
- [x] P1 **Piscina** (02/11): folhas caem na água a cada hora aberta (E com a peneira), banhistas deixam toalhas nas
  espreguiçadeiras (E recolhe) e pedem picolé (E no cooler vende). Sujeira e toalhas reduzem a renda por hora e, no
  fechamento, viram nota dos banhistas (estrelas). `MarePool.cpp`, `MarePoolWorld.cpp`, `Content/Data/pool.json`, folhas em
  `tools/ue58/gen_pool_mess.py`, teste `MareAlta.Gameplay.PoolDayUse`.
- [x] P1 **Passeios** (02/11): bilheteria na entrada do píer com fila de compradores nas 3 horas antes de cada saída
  (snorkel 10h, barco 14h, trilha do farol 16h); o jogador vende os bilhetes (o guia vende sozinho); na hora da saída o
  jogador guia: 3 paradas com uma escolha boa, uma aceitável e uma ruim, que viram nota (estrelas), gorjeta e fama; sem
  jogador e sem guia o passeio é cancelado e os bilhetes devolvidos; passageiros esperam no píer e embarcam.
  `MareTours.cpp`, `MareToursWorld.cpp`, `Content/Data/tours.json`, teste `MareAlta.Gameplay.ToursHandsOn`.
  Falta: barco saindo do píer com os passageiros e as paradas mostradas em cena.
- [x] P1 **Restaurante do hotel** (02/11): no almoço e no jantar clientes sentam nas 6 mesas do terraço; E na mesa anota o
  pedido, a cozinha prepara em 20 min, E no passe (balcão do bufê) pega os pratos prontos, E na mesa serve (gorjeta pela
  rapidez); serviço de quarto das suítes entregue no elevador; a equipe do hotel atende quem esperar 45 min; eventos
  (aniversário, casamento na praia, jantar de empresa) marcados para o dia seguinte. `MareRestaurant.cpp`,
  `MareRestaurantWorld.cpp`, `Content/Data/restaurant.json`, teste `MareAlta.Gameplay.HotelRestaurant`.
  Falta: pratos visíveis nas mesas e na bandeja, decoração do evento em cena.
- [x] P1 **Salão de jogos** (02/11):
  - [x] partida de sinuca jogada até o fim (02/11): no Play com `mare.PoolAutoPlay 1` + `mare.PoolQA` (hóspede venceu 4×3 em
    11 tacadas, placar e câmera conferidos, foto `sinuca-partida-20261102.jpg`) e teste `MareAlta.Gameplay.PoolFullMatch`
    (40 partidas completas com a física real: todas terminam, média 6,3 tacadas, bolas sempre na mesa, os dois lados vencem);
  - [x] pebolim (modelo bpy `tools/ue58/gen_game_room_extras.py`) com partida rápida de 3 rodadas contra um hóspede;
  - [x] 2 fliperamas "Maré Attack" com tela e letreiro acesos, partida rápida de 3 rodadas;
  - [x] hóspedes jogando das 18h às 23h e renda das fichas (mais jogadores com o hotel cheio).
  Dados em `Content/Data/business_games.json` (`pebolim`, `fliperama`, `game_room`), teste em `MareAlta.Gameplay.BusinessCounter`.
- [x] P1 **Tênis de mesa** no salão de jogos com gameplay completo (pedido do Sergio, 03/11): mesa e raquetes reais
  (asset gratuito antes de modelar), bola com física de quique e efeito, saque e regras (11 pontos, troca de saque a cada
  2, vantagem de 2), adversário hóspede com níveis, placar e câmera; controle por mouse e por controle; teste automático
  de partidas completas como na sinuca.
  Feito 03/11: mesa oficial, rede com malha, raquetes e bola modeladas no bpy (`tools/ue58/gen_table_tennis.py`, sem
  download gratuito sem login); `UMareTableTennis`: bola 3D com gravidade, arrasto, topspin, quique e rede; regras
  oficiais (saque nos dois lados, let, um quique por lado, 11 com vantagem de 2, saque a cada 2 pontos, melhor de 3);
  mouse/analógico move a raquete, a batida e o movimento dão a direção, clique segurado corta; adversários da sala
  com nível (reação, velocidade, erros); página da mesa (amistoso e apostas), sons sintetizados (raquete e quique),
  sem braços nem mãos; quem passa perto da câmera sai de cena. Teste `TableTennisMatch` (16 partidas, cerca de 8
  rebatidas por ponto, placares legais) e partidas completas no jogo (2×0, 11×8).
- [x] P1 **Sinuca como jogo completo** (pedido do Sergio, 03/11): modos amistoso (contra hóspede, sem aposta),
  partida com aposta pequena e **campeonato** (chave de 4–8 jogadores da vila/hotel, rodadas por dia, troféu e prêmio);
  regras completas de bola 8 (faltas, bola na mão, encaçapar a 8 cedo perde, tacada de saída), escolha de adversário,
  histórico de vitórias; teste de campeonato inteiro.
  Feito 03/11: bola 8 com saída, mesa aberta, lisas/listradas, faltas (branca na caçapa, não tocar, bola errada primeiro)
  com bola na mão (o jogador arrasta a branca com mouse/analógico), a 8 só no fim; 8 adversários com nível em
  `game_room.json`; página da mesa no caderno com amistoso, valendo R$ 20/50/100, Campeonato da Maré (8 jogadores,
  mata-mata, uma rodada por dia, inscrição R$ 50, prêmio R$ 600, vice R$ 150, fama e troféus) e histórico. Testes
  `PoolFullMatch` (40 partidas, 17×23, média 19,8 tacadas, faltas e 8 antecipada) e `PoolCup` (campeonato inteiro);
  no jogo, partidas completas 7×6 com fotos da página, do placar com grupos e da vez do jogador.
- [x] P1 Recepção do hotel com a fila de hóspedes visível no saguão (check-in vai ao elevador, check-out de manhã sai pela
  porta; teste `MareAlta.Gameplay.HotelReceptionLine`, foto no PIE 02/11).
- [x] P1 Equipe coerente com as tarefas novas (02/11): página de equipe com atendente, recepcionista, camareira,
  bartender, guia e os novos piscineiro (peneira e toalhas a cada hora) e garçom do restaurante (atende mesas e serviço de
  quarto após 15 min a 90%); descrições reescritas; teste `MareAlta.Gameplay.NewStaffRoles`. Turnos por horário ainda não
  existem (todos trabalham no horário do lugar).
- [x] P1 **Refinamento dos funcionários** (pedido do Sergio em 02/11; feito em 02/11):
  - [x] cada funcionário visível no lugar onde trabalha, andando entre as paradas e com pose de trabalho: recepcionista
    atrás do balcão da pousada, camareira de bangalô em bangalô, piscineiro pelo deck da piscina (folhas e toalhas), guia
    no quiosque de passeios e na fila, garçom entre a cozinha e as mesas levando pratos; bartender e atendente já
    existiam (`UMareStaffWorld`, rotas em `Content/Data/staff_world.json`);
  - [x] MetaHuman e uniforme próprios de cada cargo (`metahumans.json` → `staff_<cargo>`: camisa, bermuda e calçado);
  - [x] crachá no uniforme (`tools/ue58/gen_staff_badge.py`, preso ao peito esquerdo pelo osso spine_05; foto
    `docs/ue58/graphics-reference/cracha-20261102.jpg`);
  - [x] turnos (integral, manhã 6h–14h, tarde e noite 14h–24h), dia de folga e até 2 pessoas por cargo, cada uma num
    turno; o efeito do cargo só vale com alguém de serviço (`definitions.json` → `staff_rules`, `MareStaff.cpp`);
  - [x] nível e experiência (horas trabalhadas; cada nível melhora o efeito e sobe o salário, com aviso), cansaço
    (turno integral sem folga cansa, rende menos e chega a faltar um dia);
  - [x] página de equipe com nível, horas do dia, cansaço, turno e folga de cada pessoa e o que está fazendo agora;
  - [x] o que cada um fez e rendeu no dia (entregas, drinks, bilhetes, mesas, check-ins, tarefas e R$) na página de equipe;
  - [x] humor além do cansaço: feito como HUM-006 (atendente iniciante atrapalhado, some com o nível);
  - teste `MareAlta.Gameplay.StaffShiftsAndLevels` (24/24 MareAlta.* passando); foto
    `docs/ue58/graphics-reference/equipe-20261102.jpg`.
- [x] P2 Pedidos especiais e clientes VIP/influenciador no quiosque (eventos cômicos da tarefa #4). Feito 03/11:
  a partir da fama 2, 7% dos pedidos são de um VIP (`definitions.json` → `kiosk_vip`: título neutro em gênero e um
  pedido especial na comanda), gorjeta extra de 80% do preço por item e +6 de fama ao servir tudo; o influenciador
  segue como HUM-002. Teste em `MareAlta.Simulation.*`, `mare.QA vip`, foto da comanda e gorjeta VIP no caixa.

## 4. Progressão, economia e conteúdo
- Balanceamento e duração foram para a seção 15, no fim da fila (pedido do Sergio, 03/11).
- [x] P1 **Tutorial** (02/11): dica na primeira vez de cada sistema (21 dicas em `Content/Data/tutorial.json`: celular,
  placa, balcão, geladeira, recepções, limpeza, bar, negócios, passeios, pesca, piscina, restaurante, sinuca, foto, cama),
  num cartão no canto inferior esquerdo, uma vez por save; e "Próxima meta" sempre visível na nota de missões (próxima
  expansão e quanto falta). Teste `MareAlta.Gameplay.TutorialTips`. As dicas podem ser desligadas nas opções.
- [x] P1 Campanha e missões secundárias auditadas (02/11, teste `MareAlta.Gameplay.CampaignAudit`: as 10 missões
  principais, os 4 capítulos e as 4 secundárias jogados pelas ações reais, com ordem, recompensa exata e paga uma vez).
  Quatro defeitos corrigidos:
  - "Um dia com os pescadores" nunca completava (lia um contador que ninguém incrementava): conta pelo diário de pesca;
  - as missões de foto liam `chapter_photo` e a câmera grava `chp`: nunca completavam;
  - "As cores do entardecer" pedia a foto `por_do_sol`, que não existia: novo tema "Pôr do sol" pela direção do sol baixo
    no fim da tarde (foto `docs/ue58/graphics-reference/foto-por-do-sol-20261102.png`);
  - o Grand Hotel podia ser comprado sem a história do carnaval e sem fama 8: travado na simulação e no celular.
- [x] P2 Temporadas (02/11): ciclo de 56 dias (alta temporada de verão, outono, inverno chuvoso, primavera) que muda o
  movimento e a chance de chuva; aparece na agenda do celular. Variedade de tipos de cliente por temporada ainda não.
- [x] P2 Tela de fim do conteúdo do Acesso Antecipado (02/11): quando tudo está comprado e as histórias da vila concluídas,
  agradecimento com as estatísticas da partida e "Continuar jogando" (uma vez por save). Teste
  `MareAlta.Gameplay.SeasonsAndEndOfContent`.

## 5. Pessoas
- [x] 21 MetaHumans por papel; banhistas com biquíni e sunga; mãos corrigidas.
- [x] P0 Roupas reais e coloridas por papel (02/11): as 20 MetaHumans reconstruídas com roupas gratuitas do Fab
  (camiseta, camiseta por dentro, cropped, bermuda, vestido curto, conjuntos casuais, chinelo, sapatilha, mocassim;
  plano em `Content/Data/outfits_fab.json`, script `tools/ue58/dress_metahumans.py`, lotes de 5 builds por sessão).
  As peças `_top`/`_btm` recebem as cores de cada papel (`metahumans.json` → `clothes`), os sapatos do Fab substituem
  os gerados; 3 banhistas de maiô Aeron (`<Nome>_Swim_Aeron`). Texturas das roupas limitadas a 1024 (estouro de memória
  de vídeo com 4K). Lista e processo em `docs/ue58/ROUPAS_FAB.md`; QA 104/104, testes 26/26. Vestido e conjuntos casuais também
  recebem a cor do papel (03/11, foto `roupas-cores-festa-20261103.jpg`).
- [x] P0 Calçados: chinelo, sandália de tiras, tênis e sapato social com saltinho (02/11), sorteados por papel
  (`metahumans.json` → `shoes`); sapato social conferido no saguão do hotel.
- [x] P1 Mais banhistas: mulheres e homens de outras idades e tipos de corpo. 03/11: sem precisar de login (rig e texturas já
  baixados): Etta e Vivian (mais velhas), Walter (mais velho), Dominic e Sunita (outro porte) ganharam corpo de banho
  (`mh_swimall`), pele sem a roupa íntima assada (`mh_skin_underwear.py`), biquíni/sunga ajustados ao corpo
  (`gen_mh_swimwear.py`) e entraram no papel `beach` (fregueses do quiosque e banhistas deitados). Correção junto: o
  sexo vinha do caminho do esqueleto, mas TODO corpo MetaHuman usa o mesmo esqueleto em Common/Female, então os homens
  calçavam o chinelo/sandália do pé feminino; agora `metahumans.json` → `men` (`AMarePerson::IsWoman`).
- [x] P0 Verificar TODOS os personagens da ilha (vila, praia, hotel, quiosque, equipe, eventos; MetaHumans e os demais)
  com movimentação natural: quem anda mexe pernas e braços, ninguém desliza parado nem congela (03/11, pedido do Sergio:
  banhista MetaHuman do guarda-sol deslizou sem animar; causa: esqueleto oculto com OnlyTickPoseWhenRendered).
  Feito 03/11: auditoria no corpo VISÍVEL de todo ator com esqueleto (`mare_hud allpeople`, 42 MetaHumans + jogador),
  três amostras a 0,35 s (a 1,2 s coincidia com o ciclo do passo e dava falsos "deslizando"): 7 rodadas dia/noite com
  0 deslizando e 0 congelados. Virou checagem permanente do QA gate ("visible").
- [x] P1 Animações (03/11): 7 clipes gratuitos de captura do Fab (Animation Shopee) importados
  (`mare_metahuman.import_mocap`, dois passes, `frame_alignment` SNAP_TO_CLOSEST) e redirecionados (`retarget_mocap`, só
  FK). Causa dos bonecos tortos: o esqueleto da captura olha para -Y e a MetaHuman para +Y; o redirecionador exige os
  dois virados para o mesmo lado. A pose de origem gira o Hips 180° ANTES de alinhar a MetaHuman (alinhada à pose T sem
  girar, os braços horizontais saíam espelhados). Conferido com números contra a captura original (`mh_twist`: ombros,
  quadril e joelhos; `mh_arms`: cotovelos e mãos, diferença ≤ 0,03) e imagens de frente e de lado a 30% e 70%.
  Depois: raiz ×100 (`rescale_mocap_root`/`inplacemocap`) e direção +Y com a pelve sentada 30 cm atrás da raiz
  (`orient_mocap`). EM USO: metade dos fregueses sentados conversa gesticulando (`SitTalk`); na festa do dia, morador ou
  passante parado a até 9 m rebola (`DanceHip`) ou comemora (`Cheer`), `UMareEventsWorld::UpdateDancers`; QA
  `mare.Event junina`, CVar `mare.Mocap 0` desliga. Fora: `Dance` (a captura se curva 50 cm à frente com os braços
  pendurados; o Sergio apontou "braços errados"), `TalkGesture` (curva o tronco ~35°, parece reverência), `SitDrink` (banqueta, senta 9 cm mais alto) e `LieDown` (fica para a canga). Clipes locais, fora do git
  como as roupas do Fab (`D:/CodexTemp/fab/anim`); sem eles o jogo usa os clipes base.
  - deitar na canga: FEITO 03/11 (`sunbathers.json`, `UMareVillageWorld::UpdateSunbathers`, `AMarePerson::LieOn`): 5
    banhistas MetaHuman de maiô/sunga deitados de barriga para cima nas toalhas dos guarda-sóis das 9h às 17h sem chuva,
    mãos no peito e respiração lenta (início do clipe `Cheer`, os idles em pé têm um pé 37 cm atrás e afundavam um
    calcanhar; o `LieDown` deita de lado encolhido e foi recusado pelo Sergio); chegam e saem só com o jogador a mais de
    25 m. Junto: toalhas e lonas dos guarda-sóis com tecido (`M_BeachFabric`: felpa waffle, barra e listras brancas nas
    pontas; lona com trama de denim e 8 gomos costurados), pedra tirada de cima de uma toalha e o tronco que estava em
    cima da lona de um guarda-sol descido para a areia. Prova `docs/ue58/graphics-reference/banhistas-canga-20261103.jpg`.
  - deitar na espreguiçadeira: FEITO 03/11. Com a piscina comprada, 3 banhistas reclinados nas espreguiçadeiras: a mesma pose
    de barriga para cima com o tronco dobrado 30° na cintura (`spine_01` no proxy de animação, `AMarePerson::Recline`),
    pelve logo à frente da dobra do encosto (perfil medido: assento 58 cm, encosto 63→116 cm em 60 cm). Com 40° sobrava
    um vão entre as costas e a almofada; com 30° as costas encostam. `sunbathers.json` → `loungers`/`recline`.
  - nadar no mar e na piscina: FEITO 03/11. `Swim_Idle` do UAL redirecionado para a MetaHuman (`mh_rtclip`): 3 banhistas
    boiando no mar de frente para a praia (fundo ≥ 1,6 m, longe do píer), água nos ombros, subindo e descendo com a onda
    (`AMarePerson::SeaHeight` replica o deslocamento de vértices do material do mar, com a tempestade); na piscina (1,32 m)
    não dá para boiar: duas pessoas em pé no fundo conversando com a água no peito. `sunbathers.json` → `swimmers`.
  - comer e beber sentado (já existe);
  - conversar com gestos sentado (feito, `SitTalk`); em pé usa o clipe base `Idle_Talking` (gestos leves); dançar nas festas (feito);
  - limpar e atender (equipe): piscineiro FEITO 03/11. Peneira de piscina modelada no bpy (`tools/ue58/gen_pool_skimmer.py`,
    cabo telescópico, aro e rede de fios reais; nenhum CC0 encontrado) segura com as duas mãos por IK e varrida sobre a
    água (pose `Skim`, `AMarePerson::UpdateTool`). Junto, defeito antigo: ele atravessava a piscina andando SOBRE a
    água (a superfície tem colisão e entra na navegação estática; o corredor entre a borda e as espreguiçadeiras é
    estreito demais): rota com pontos de passagem por fora das espreguiçadeiras. Camareira FEITO 03/11: varre o deck e
    a soleira de cada bangalô alugado com a vassoura de plástico do Poly Haven (CC0), cabeça no piso em golpes curtos e
    as duas mãos no cabo por IK (pose `Sweep`). O garçom do hotel já leva os pratos da cozinha às mesas nas mãos.
- [ ] P2 [bloqueado-usuario] Conversar gesticulando em pé com um clipe de captura melhor que o `Idle_Talking` (o `TalkGesture`
  do Fab foi recusado: curva o tronco como reverência; outro clipe gratuito do Fab exige o login do Sergio no navegador).
- [x] P0 Sentados no ar/no encosto (03/11): hóspedes do restaurante do hotel em cadeiras reais (`Data/hotel_seats.json`, gerado por
  `mare_hud.chair_seats` a partir dos vértices das cadeiras) e alinhamento da bacia no assento por corpo (`AMarePerson::SitOn`,
  `AlignToSeatBelow`; restaurante, bar e quiosque). Teste no PIE: `hud_seataudit` (12/12 ok). Copos flutuando no restaurante
  corrigidos com `float_audit place` (pivô + nome, nunca índice: nomes se repetem entre atores).
- [x] P1 Objetos flutuando no mapa (03/11): `float_audit scan` acha 593 candidatos; 418 são tipos legítimos (peixes, folhas
  sobre vasos, varais, vasos pendurados, azulejos). Corrigidos e conferidos por imagem: copos ao lado das mesas do hotel,
  tigela no ar junto ao quiosque, bola de praia meio enterrada. Conferidos e legítimos: conchas = mensageiro dos ventos no
  beiral dos bangalôs; sofá, colunas de varanda e caixotes = móveis sem colisão (o raio desce até o piso, falso positivo);
  Cube_0xx = interiores das casas. Cabine `biz_booth` do hotel conferida no PIE pelos 4 lados (frente ao sul com a placa
  "BAR DA PISCINA" e o atendente de frente para os clientes; o lado norte é o fundo).
  Ferramentas: `float_audit place|surface|near|bbox`, `hud_freecam` (escolhe a câmera pela linha de visão livre).
- [x] P1 Bicicletas da vila low poly (03/11): a malha exportada da Godot tinha 3.179 triângulos. Trocadas pela "Vintage Bicycle
  3D Model" (Fab, Patrick Goud, CC-BY 4.0) em 5 cores (`prep_fab_food.py bike_<cor>`: quadro repintado, pneu azul da marca
  em preto, 60 mil triângulos, mapas 2048) e `hud_fabbikes` (importa e troca as 11 instâncias + `imported_meshes.json`).
  `hud_fitbikes` deixa em pé no chão (as antigas eram deitadas/encostadas com 10° de inclinação) e `hud_clearbikes` afasta
  de postes, bancos, cadeiras e vasos (amostras a cada 5 cm na largura real do guidão e pedais). Conferido de lado e em diagonal.
- [x] P1 Gramado com "confete preto" (03/11): as texturas de cor da vegetação Poly Haven vieram em JPG sem alfa, então cada
  lâmina/folha era um cartão inteiro com fundo preto. `tools/ue58/fix_foliage_alpha.py` baixa o mapa Alpha/Opacity (CC0) e
  grava RGBA; `hud_foliagealpha` reimporta as 15 texturas (gramas, pervinca, rooibos, azedinha, samambaia, 5 arbustos,
  folhas de 5 árvores) e deixa os materiais em máscara. Conferido por imagem (boia e lâminas limpas).
  Falta: plantas em vaso do saguão do hotel (arquivos do Sergio em edição; RGBA já pronto em D:/Assets/PolyHaven),
  antúrio e calathea (fora de /Game/Nature). Faixas de grama sobre a calçada (03/11): os glTF `grass_medium_01/02` trazem
  17/5 variações enfileiradas (5,6 m / 1,3 m) numa malha só; `mare_lawn.populate` agora testa a fileira inteira (pontas e
  meio) contra calçada, rua, rotas e lote antes de aceitar (grass_medium_01 aberto 72.613 → 16.598; 02 72.966 → 41.785).
  Conferido: borda da piscina, calçadas da vila, muro do hotel e gramado aberto. Pedra do PCG `World_0495` (rock_07
  exportada da Godot com material roxo listrado) trocada pelo import nativo.
- [x] P0 "Pessoa dentro da mesa" (03/11): era a recepcionista da pousada dentro da ponta do balcão (a recepção tinha yaw 0, mas
  o tampo corre em X e a frente é +Y). `customization.json` reception yaw 90 + `reception_mesh_yaw` -90 (modelo igual) e
  `staff_world.json` behind 55: ela fica entre o tampo e o quadro de chaves, e os hóspedes fazem fila na frente. Auditoria
  `hud_standaudit` (pelve dentro de móvel) sem ocorrências; conferido de frente, lado e diagonal.
- [x] P2 Capturas de QA com a câmera dentro de paredes (tint_Celeste, conchas, biz_booth): `hud_freecam` escolhe a câmera pela
  linha de visão livre; capturas em lote no PIE com `lot_pie.py` (vários ângulos por alvo, imagem inválida = refazer).
- [x] P1 Rosto: expressões faciais simples (sorriso ao receber, irritado na negociação). 03/11: o rosto deixou de seguir o
  corpo por leader pose (que o deixava sem avaliação própria: nem piscava) e copia a pose do corpo com as curvas de
  controle (`UMareFaceAnimInstance`, `CTRL_expressions_*`, RigLogic do `ABP_Face_PostProcess`): pisca a cada 3-6 s,
  sorri ao receber o pedido e ao fechar negócio na recepção, fica irritado com contraproposta ou ao desistir e faz
  "hmm" ao escolher (`AMarePerson::Express`). Ossos do rosto conferidos contra os do corpo (0,00 cm). Teste
  `MareAlta.People.FaceCurves`; QA `mare.Express smile|annoyed`; `mare.Faces 0` volta ao rosto parado.
- [ ] P2 [bloqueado-usuario] Crianças e famílias (se houver presets/assets adequados). 03/11: o MetaHuman Creator só tem corpos
  adultos (sem preset infantil; os sliders de altura não chegam a proporção de criança) e os pacotes de crianças MetaHuman
  são pagos (Athian Games, Fab); nenhum gratuito com esqueleto compatível sem login. Decisão do Sergio: comprar ou seguir sem.

## 6. Mundo e arte
- [x] Barcos detalhados (jangadas e botes), palmeiras, janelas, piscinas, mata dos morros.
- [x] P1 Varredura visual final de todo o mapa (03/11):
  - objetos flutuando ou low poly; (03/11) auditoria por forma: `float_audit lowpoly` (malhas com poucos triângulos
    para o tamanho) + `primitives` (esfera/cilindro pelos vértices; caixas arredondadas de 252 triângulos ficam de fora)
    e `swapfit` (troca por modelo real, reencaixada por instância, salva em `world.json`/`imported_meshes.json`).
    Trocados: bola de praia (392 tri → `gen_beach_ball.py`, 9 mil), 9 "troncos" cilindro → Dead Tree Trunk, 46 seixos
    Quaternius + 425 pedrinhas de 318 tri → Rock 07/09 (Poly Haven, Nanite), 60 "pegadas" disco → pegada de pé
    translúcida (`gen_footprints.py`, inclinada pela normal da areia), 8 placas lisas do caminho do quiosque → tábuas
    (`gen_beach_walkway.py`), jangada de cilindros da praia oeste → `mare_jangada` (`mare_fab._replace_west_raft`).
    Conferido no editor e no PIE. Aceitos: vigas roliças dos telhados dos bangalôs, calhas, postes da grade.
    Canteiro da praça (cilindro bege de 4,6 m) → meio-fio de pedra e terra (`gen_tree_planter.py`).
    Carrinho de bagagem da pousada (placa rosa + varetas + malas-caixa) → carrinho de latão (`gen_luggage_cart.py`) e
    malas Vintage Suitcase (Poly Haven CC0, `prep_luggage.py`). Resto da lista conferido por foto: calhas, colunas
    roliças, mastros, postes e a lanterna do farol são arquitetura (aceitos); discos do pináculo não ficam visíveis.
    O mato que aparece na varanda da pousada no editor é o gramado do lote (some no jogo com a pousada construída).
  - texturas; (03/11) areia nova tipo Copacabana, piso de terracota na pousada, cortiça/postais desenhados.
  - folhagem muito clara à noite; (03/11) feito: a transmissão de luz das folhas das palmeiras (`M_PalmFab_PBR`)
    cai 75% com o Night; conferido às 22h (praia, palmeiras, quiosque, vila, praça, jardim, hotel, pousada).
  - ondas, espuma e respingos. (03/11) feito: ondas maiores, espuma na beira d'água e mar bravo na tempestade.
- [x] P1 Personalização com 5 opções em tudo:
  - quiosque, expansões, hotel, piscina, tobogã;
  - casa (cama, sofá, armário, TV).
  03/11: conferido em `customization.json`: todos os itens de quiosque, bar, piscina, pousada, passeios, hotel
  (restaurante, piscina com tobogã, suítes, lazer), negócios e casa já tinham 5 opções (modelo, material ou serviço).
  Faltava a TV da casa: item `tv` novo com a TV de tubo da vó e quatro TVs de tela plana modeladas no bpy
  (`tools/ue58/gen_tv_sets.py`: 32" com pés, 43" e 55"/65" com pedestal, as duas maiores com soundbar). Ligadas,
  mostram as paisagens da costa na tela inteira (`M_HomeTV_Flat`, pelas UVs da tela; `UMareHomeWorld::UpdateTV`).
  QA `mare.HomeTV`. Prova `docs/ue58/graphics-reference/tv-casa-opcoes-20261103.jpg`.
- [x] P1 Interiores do restaurante, da recepção da pousada (o balcão rústico é externo) e dos negócios da vila (03/11).
  Recepção da pousada: piso de lajota de terracota com taquinhos (Poly Haven patterned_terracotta_tiling, UV pelo mundo,
  `hud_pousadafloor`), área de estar com móveis rústicos pintados Poly Haven (sofá, mesinha, cadeiras, armário, mesa
  redonda, lanterna, planta, quadros e lustre; `mare_fab.POUSADA_DECOR`, tag Region_pousada; modelos Poly Haven ficam
  de frente para +Y local nesta importação), porta-chaves de verdade na parede oeste atrás do balcão
  (`gen_key_rack.py`; a tábua antiga invadia a janela), mural de cortiça com postais (`gen_notice_board.py`; o antigo
  flutuava 19 cm da parede e cobria a janela leste), carrinho de bagagem e malas. Restaurante do hotel é um pavilhão
  aberto (já mobiliado) e os negócios da vila são barracas externas (sorveteria, pranchas, surfe, pastel, souvenires):
  não têm interior. Conferido no PIE de vários ângulos.
- [x] P2 Clima: chuva com poças, vento nas palmeiras, tempestade com mar bravo (03/11). `MPC_MareTime` ganhou Rain, Wind e
  Storm, escritos por `UMareVisualWorld::UpdateWeather` a partir do clima do dia (chuva; tempestade; maré alta = mar bravo
  sem chuva), com transição de ~4 s; QA `mare.Weather 1|2|3|4` (limpo, chuva, tempestade, mar bravo). Chuva: duas cortinas
  de gotas em volta da câmera (`M_RainCurtain`, textura desenhada por `tools/ue58/gen_weather_textures.py`), escondidas sob
  teto; céu fechado (nuvens volumétricas e atmosfera), sol apagado e luz do céu difusa; luzes internas mais fortes.
  Poças: 70 espelhos d'água nas ruas e na praça (`hud_puddles`, `M_Puddle`), crescem com a chuva e somem no seco.
  Vento: `M_PalmFab_PBR` balança tronco e folhas com o Wind. O Nanite ignorava o WPO aqui (medido: diferença entre
  quadros 0,8 com Nanite, 9 sem); as 4 malhas de palmeira ficaram sem Nanite com LODs automáticos 11k/5,6k/2,8k/1,4k
  e o vento para além de 80 m. Mar bravo: `M_CoastalWater_PBR` com ondas 2,4x, ondas curtas, carneirinhos e mar mais escuro.
  Mar do dia a dia mais agitado (pedido do Sergio 03/11): ondulação ao largo ~35 cm e arrebentação ±10 cm em volta do
  nível antigo (só subir alagava a quadra de vôlei). Recepção da pousada com duas luzes quentes. Conferido no PIE
  (limpo × tempestade à mesma hora; palmeiras por diferença entre quadros).
- [x] P2 Detalhes de vida: pássaros, gaivotas, cachorros e gatos animados, barcos passando (03/11). Feito: as 5 gaivotas
  exportadas paradas no ar (World_0536) planam em círculos em volta de onde estavam, sobem e descem e inclinam nas curvas;
  um bote de pesca (leste) e uma jangada a vela (oeste) passam ao longo da costa de dia, balançando nas ondas
  (`UMareMarineWorld::UpdateLife`). Conferido no PIE por quadros e pela posição. Falta: cachorros e gatos animados
  realistas: o Sergio decidiu tirar gatos e cachorros do jogo (03/11); o latido de cachorro do som ambiente da vila
  também saiu (código, catálogo `audio.json` e áudio).

- [x] P1 Mar verde-cristalino (pedido do Sergio, 03/11, foto de referência: água rasa turquesa-esverdeada e transparente,
  fundo de areia visível com cáusticas, azul mais profundo só ao longe).
  Feito 03/11: cor verde-turquesa no raso, turquesa no meio e azul ao longe; transparência que cresce suave com a
  distância da praia (sem a linha dura onde o terreno acabava); absorção que favorece o verde; sem pontos/faixas brancas
  (espuma de crista só na tempestade); espuma da beira ondulada (não quadriculada); fundo de areia da praia estendido
  mar adentro (`mare_water.ensure_seabed`: rampa até -9 m e fundo plano) com cáusticas; ondas maiores e marola
  ("parecia lago"), com três escalas de ondulação e ondas mais calmas junto à costa e ao píer (a água subia no deque).
  Corais e peixes do recife levados 85 m mar adentro, apoiados no fundo de -9 m (`mare_water.move_reef`, só as peças
  World_0537..0600; o píer fica). Fotos `sea_before.jpg` → `sea_after6.jpg`.
- [x] P1 Sombras (pedido do Sergio, 03/11: "nada tem sombra, fica muito artificial"): móveis, pessoas e objetos sem
  sombra no saguão do hotel (e conferir no resto do jogo, de dia e de noite).
  Feito 03/11: as luzes de interior (saguão, suíte, bangalôs: 23 no nível, `mare_hud lightshadows`) e os postes e
  lanternas maiores (`MareVisualWorld`, raio ≥ 8 m) projetam sombra, com sombra de contato curta; os geradores
  (`mare_hotel_lobby`, `mare_beach`) já criam as luzes assim. Foto `shadows_night.jpg` (saguão, salão, vila, quiosque).
  Medir o custo no executável junto com o item de FPS (seção 9).
- [x] P1 Poltronas do saguão do hotel (pedido do Sergio, 03/11, foto circulada): corrigir posição/orientação/apoio.
  Feito 03/11: a frente desses modelos é +Y e o gerador supunha outra; as poltronas clássicas e as lounge viradas
  para as suas mesas de centro (`mare_hud faceactors`), foto `armchairs2.jpg`.
- [x] P1 Piso do saguão/salão do hotel da mesma cor das paredes (pedido do Sergio, 03/11): trocar por piso vinílico
  amadeirado em réguas, como na foto de referência (madeira clara mel, réguas longas com veio).
  Feito 03/11: Poly Haven `laminate_floor` (CC0) alinhado ao mundo (2 m por placa), relevo e brilho acetinado
  (`mare_materials.wood_floor` no material do piso da torre), foto `floor_day.jpg`.

## 7. Áudio
- [x] P1 Música por lugar e horário (02/11): zonas em `Content/Data/audio_zones.json` (saguão do hotel bossa, restaurante relax,
  salão de jogos à noite pop, bar reggae, piscina calipso), rádio portátil abaixa dentro das zonas; níveis medidos no PIE.
- [x] P1 Efeitos de todas as ações novas (02/11, 42 sons CC0 ligados: recepção, limpeza, sinuca, bar, dinheiro, negociação):
  - campainha da recepção, chaves, cama, lixo;
  - tacadas e bolas da sinuca;
  - liquidificador e coqueteleira do bar.
- [x] P1 Rádio com músicas havaianas de ukulele ORIGINAIS (pedido do Sergio, 03/11): compor/gerar com ferramenta gratuita
  (sem copiar músicas existentes, ex.: "Over the Rainbow" tem direitos), várias faixas leves + uma música-tema do jogo. 03/11: feitas "Aloha FM" (120 s, ukulele/steel/ipu,
  `gen_radio_music.havaiana`) e o tema (73 s), padrão no rádio; depois "Aloha FM · onda alegre" (104 BPM, ré maior) e
  "Aloha FM · luar" (slack key, 72 BPM, fá maior). Cada estação toca sozinha no mesmo nível (0,066, `mare_hud radio/loops`).
- [x] P1 Ambiente de fundo suave e relaxante (03/11): vento, mar/ondas, pássaros e gaivotas em volume baixo, sem poluição sonora.
  Feito 03/11: pássaros a cada 10–22 s (0,16) e gaivotas a cada 28–55 s (0,13) sobre vento e mar (`MareAudioWorld`).
- [x] P1 Mixagem final e volumes por categoria (já existem: geral, música, efeitos, ambiente).
  - 03/11: `tools/ue58/measure_mix.py` mede cada som como o jogador ouve (LUFS do arquivo + ganho do código/catálogo + barramentos padrão)
    e aponta o que foge mais de 6 dB da mediana da categoria. Corrigido: chuva 18 dB acima do mar (agora ~3 dB), folhas inaudíveis,
    pássaros 25 dB acima das gaivotas, gaivota 2 gravada 8 dB mais baixa, passos de concreto 8 dB abaixo do carpete (ganho por
    superfície), clique/caixa/retirada baixos, negociação/sinuca/pingue-pongue/liquidificador baixos no catálogo, reggae_praia 3,6 dB
    abaixo das outras estações e vozes normalizadas por loudness (-23 LUFS) em vez de pico. Todas as categorias dentro de ±6 dB.
- [x] P2 Vozes curtas (murmúrios) sem diálogo falado, respeitando a regra de áudio suave. 03/11: risadinha, resmungo,
  suspiro e "hmm" de pacotes CC0 do OpenGameArt (`tools/ue58/fetch_murmurs.py`, só sons sem palavras); as versões
  masculinas das femininas foram feitas com o vocoder WORLD (tom x0,58, formantes x0,84; F0 medido 110-159 Hz contra
  188-441 Hz das femininas). Volume 0,14, pico -9 dBFS, saem da cabeça de quem faz a expressão (grupos
  `voice_<humor>_<f|m>`).

## 8. Interface e experiência
- [x] P0 **Menu principal**: Novo jogo, Continuar, Carregar (3 slots), Opções, Créditos, Sair (02/11, foto no PIE;
  QA de PIE usa `-MareSkipMenu`).
- [x] P0 **Opções completas** (02/11, teste `MareAlta.Options.SaveAndReload`; idioma só troca fora do editor):
  - gráficos detalhados, resolução, janela, VSync, FPS, upscaler, FOV;
  - mouse e controle, remapear teclas;
  - idioma.
- [~] P0 **Controle** (Xbox/PlayStation) em todo o jogo e nos menus. [bloqueado-usuario] (Tradução: ver a seção 11, no final.)
  - Código feito em 02/11 (`MareGamepad.h/.cpp`, mapeamentos em `Config/DefaultInput.ini`), falta testar com controle de verdade no EXE.
    [bloqueado-usuario] (precisa do Sergio jogando com um controle físico no executável; os testes automáticos passam).
    Mapa fixo: analógico esquerdo anda, direito olha (sensibilidade própria + inverter Y); A pula/sobe nadando; **X interage**
    (A ficou com o pulo para não pular ao falar/servir); Y ou View celular; Start pausa; LT segurar ou L3 alternar corre; B mergulha.
    Menus: foco no 1º botão ao abrir com o controle, direcional/analógico navega, A confirma, B volta/fecha, LB/RB trocam abas,
    analógico direito rola. Sinuca: analógico mira, segurar RT dá força, B sai. HUD mostra botão ou tecla conforme a última entrada;
    opção "Botões do controle" Xbox/PlayStation. Testes: `MareAlta.Gamepad.MappingsAndLabels` e `MareAlta.Gamepad.MenuFocusAndBack`.
- [ ] [bloqueado-usuario] P1 Três propostas de HUD/celular mais comercial (pedido antigo, apresentar antes de escolher).
  04/11: apresentadas no quadro https://claude.ai/artifact/PD9RvV7TzpW83nhDvEqLRK sobre uma foto real da praia:
  A) caderno de bordo (evolução do estilo atual: papel kraft, fita adesiva, post-it, celular = caderno de couro com
  marcadores coloridos); B) cartão-postal tropical (pílulas grossas, cores vivas, missões com barra de progresso,
  celular de verdade com apps); C) resort premium (vidro fosco, tipografia fina, celular com menu lateral).
  Falta o Sergio escolher (ou misturar); a escolhida substitui o MareNotebookStyle em todas as telas.
- [x] P1 Acessibilidade (02/11): tamanho da interface e do texto (85–150%, foto `interface-130-20261102.png`), dicas do
  tutorial liga/desliga, modo para daltonismo (+/- nas variações de estrelas). Não há falas, então legendas não se aplicam.
  Em janelas pequenas, 140–150% encosta nas bordas do celular.
- [x] P2 Indicador no mapa ou bússola com os lugares (pousada, hotel, salão, negócios): faixa sob a placa com N/S/L/O e
  os lugares liberados na direção do olhar (`Content/Data/map_markers.json`), mais perto primeiro, em duas linhas;
  foto `docs/ue58/graphics-reference/bussola-20261102.png`.

- [x] P0 Interfaces sem rolagem (pedido do Sergio, 03/11): todo painel/página do celular e das estações cabe inteiro
  na tela, sem barra de rolagem nem subir/descer; conferir em 1280×720, 1920×1080 e janelas menores.
  Feito 03/11: nenhuma SScrollBox na UI. `SMareFit` (MareNotebookStyle.h): reduz até 85% quando falta pouco e, quando
  falta muito, divide a página em folhas inteiras do caderno ("‹ folha 1 de N ›", título em todas, título de seção
  junto do bloco, folha lembrada entre recargas); conteúdo recortado na página. Grades de cartões em fileiras
  separadas (`FRowGrid`) para virar a folha entre fileiras. Celular (7 abas), 8 estações, pausa, opções, créditos e
  carta conferidos por foto (`ui_fit_1..3.jpg`); o log `MARE_UI_FIT` registra conteúdo × espaço de cada página.

## 9. Desempenho e estabilidade
- [x] P0 FPS medido no executável:
  - setores pesados: praia com pessoas, saguão do hotel, vila à noite;
  - MetaHumans: limite visível, LOD, grooms.
  - 04/11: `MareAlta.exe -MareBench` (tools/ue58/bench_package.ps1) mede 20 s por setor (média, p50/p95/p99, jogo/render/GPU,
    perfil CSV, foto). RTX 4060 Ti, 1920×1080, opções padrão, tudo liberado. Antes → depois das correções:
    praia 13h 26 → 33 FPS; quiosque 15h 26 → 36; saguão do hotel 43 → 45; vila 21h 43 → 52. O gargalo era a thread de
    render: as ~60 pessoas do mapa (6 na tela) desenhadas nas sombras do sol (3.400 draw calls). Agora pessoas a mais de
    30 m não projetam sombra (`mare.PeopleShadowDistance`) e quem ninguém vê mantém a pose (`mare.OffscreenPose`).
    Grooms não pesam (variante sem cabelo igual). Sem pessoas a praia faz 49 FPS: o resto é do cenário (abaixo).
- [x] P1 Chegar a 60 FPS de dia na praia (RTX 4060 Ti, 1080p): o cenário sozinho gasta 20 ms de render com ~2.030 draw
  calls de sombra de malhas sem Nanite (achar quais: vegetação/instâncias) e as pessoas ainda ~8 ms (componentes
  registrados: oclusão, velocidades). Medir com `tools/ue58/bench_package.ps1 -Exec "cvar valor"` sem reempacotar.
  04/11, já testado e descartado: (1) ligar Nanite nas 70 malhas sem Nanite que fazem sombra (`hud_shadowcasters`): os
  maiores (postes World_0688/0683/1391, lanternas) têm vidro translúcido por instância de material, então só 4 pequenas
  poderiam (`hud_naniteon dry:...`); (2) `r.Shadow.Virtual.Cache.StaticSeparate 0` (cache de sombra para Movable):
  sem diferença; (3) cache de sombra das árvores com vento: sem diferença. Próximo passo: captura do Unreal Insights no
  executável para ver o que a thread de render desenha a cada quadro.
  04/11, eliminação por categoria (sem pessoas, praia 13h): sem grama, sem vegetação instanciada ou sem terreno nada muda
  (render ~19,5 ms); sem as malhas instanciadas render 20 → 15 ms e GPU 19 → 10 ms (48 → 67 FPS). O custo está nas
  instâncias do cenário exportado (casas, postes, móveis): falta descobrir quais (por região/malha) no Insights.
  04/11, varredura por malha (`-MareBenchSweep`): só as jacarandás dos morros pesavam na GPU (−3,5 ms escondidas; a sombra
  delas sozinha ~5 FPS). Morros com metade das árvores (pedido do Sergio, "tem muitas"): 10.153 → 5.360 árvores,
  15.175 → 8.971 arbustos, com clareiras. Jogo completo: GPU da praia 22,1 → 20,7 ms, p99 43 → 38 ms, FPS 32,7 → 33,3.
  O limite agora é a thread de render (CPU ~28–30 ms de dia), espalhada por todas as malhas do cenário exportado.
  04/11, testes no executável (praia, jogo completo, ~33 FPS de base): HZB (r.HZBOcclusion 1) render 30 → 21 ms mas FPS
  igual; resolução 50% só +4 FPS (GPU 20,7 → 17,7: custo da placa NÃO depende da resolução); qualidade Alta do Lumen
  (perfil de 60 FPS da Epic) igual; sombras virtuais (LodBias 1,5, NonNaniteVSM 0, LastLevel 16) +0–2 FPS; tela cheia
  igual. Diagnóstico: custo de GEOMETRIA (~1,6 M triângulos/quadro em malhas sem Nanite, exportadas com um único LOD).
  Plano: (1) LODs automáticos nas malhas sem Nanite mais desenhadas; (2) separar o vidro dos postes/lanternas numa malha
  própria para o corpo opaco ganhar Nanite; (3) distância de corte e sem sombra em objetos pequenos; (4) HZB ligado.
  Ferramentas: `tools/ue58/bench_package.ps1 -Exec/-NoShadow/-Fullscreen`, `-MareBenchSweep`, `hud_shadowcasters`.
  04/11, dicas da pesquisa aplicadas (commit 0df7d273): LODs automáticos em 42 malhas sem Nanite (`hud_autolods`), HZB
  ligado, 260 objetos <15 cm sem sombra e 608 <60 cm cortados além de 40 m (`hud_smallprops`). Executável na praia:
  render 30,0 → 21,1 ms, GPU 20,7 → 19,1, jogo 15,8 → 13,7, mas o quadro continua ~30 ms. Unreal Insights
  (`UnrealInsights.exe -OpenTraceFile=... -ExecOnAnalysisCompleteCmd="@=cmds.rsp" -AutoQuit -NoUI`, comandos
  `TimingInsights.ExportTimerStatistics <csv> -threads="RenderThread 0"|GameThread|RHIThread|GPU0-Graphics0`):
  as threads passam o quadro esperando umas às outras (jogo espera ~13 ms, render ~10, RHI ~23). GPU na fila gráfica:
  VRS/ContrastAdaptiveShading 3,9 ms, TSR 3,8, cabelo 2,7 (testados VRS off e TAA: FPS igual). Só baixar a resolução
  move o quadro (+4 FPS): o tempo real da placa deve passar dos 19 ms medidos. Próximo: exportar as filas
  GPU0-Compute0/GPU0-Copy0 e as bolhas da fila gráfica na linha do tempo.
  04/11 (manhã, Sergio priorizou e subiu o esforço; meta: 60 FPS SEM DLSS, DLSS só como extra):
  - Causa da espera: com `r.HZBOcclusion 1` o render passava ~10 ms por quadro em MapOcclusionResults → FlushRHIThread
    (lê o resultado do quadro anterior), então render e placa se revezavam (render 21 + placa 19 ≈ quadro 31 ms) e a placa
    ficava ~55% ocupada (nvidia-smi, 70 W de 160 W). Consultas por primitiva com 2 quadros de folga
    (`r.HZBOcclusion 0`, `r.NumBufferedOcclusionQueries 2`): praia 29 → 33, quiosque 29 → 36, vila 40 → 46. 3 quadros: igual.
  - Testes no executável (base nova): Lumen Lite da 5.8 (`sg.GlobalIlluminationQuality 1`, reflexos 1) placa 19 → 17,5 ms,
    +0–4 FPS; VRS desligado PIOR (mantido); `r.ViewDistanceScale 0.6` praia 33 → 38; **sem pessoas praia 58, quiosque 55,
    saguão 77, vila 76**: as ~60 MetaHumans (6 na tela) custam ~10 ms de render mesmo escondidas pela distância.
  - Aplicado: oclusão por consulta (DefaultEngine.ini), Lumen Lite como padrão, menos pessoas de ambiente (pedestres 12 → 6,
    banhistas 5 → 3, nadadores do mar 3 → 2, espreguiçadeiras 3 → 2, hotel 15 → 10), pessoas a mais de 50 m da câmera
    escondidas e sem animar (`mare.PeopleDrawDistance`; as de ambiente também param de andar, clientes e equipe seguem),
    menu gráfico com Distância de visão, Detalhe dos modelos (LOD), Efeitos, Sombreamento e Pessoas nas cenas, e o
    DLSS 4.5 (Super Resolution + Geração de quadros, `tools/ue58/install_dlss.ps1`, plugins opcionais fora do git).
  04/11 (tarde), mais cortes, todos medidos no executável:
  - Luzes locais com distância (`mare.LightDrawDistance` 30 m; preenchimento `MareBounce` x1, sem sombra; sem sombra
    abaixo de 10 m de raio, `mare.LightShadowMinRadius`): ~150 luzes do mapa eram desenhadas o dia todo, 99 com sombra.
  - Física do cabelo das MetaHumans (solver Niagara) só no Efeitos Épico; pessoas fora do cone de visão (tela + 20°,
    além de 6 m) escondidas e pausadas como as distantes (`mare.PeopleHideOffscreen`).
  - Postes (World_0688, 193), lanternas (World_0683) e World_1391 com vidro fosco opaco que brilha à noite
    (`M_LampGlassFrosted`, `mare_hud frostedglass`) e Nanite; Nanite também em barco, jangada, bola, 2 plantas e
    World_0687. Sombras sem Nanite estimadas 1.693 → 839.
  - **Resultado sem DLSS (duas rodadas): praia 67–69, quiosque 74, saguão 76–78, vila 87–89 FPS** (de 29/29/35/40).
  - Testados e descartados: VRS desligado (pior), TSR/pós médios (igual), sombra das pessoas 15/10 m (igual),
    `r.HairStrands.Enable 0` (derruba o executável), `r.NumBufferedOcclusionQueries 3` (igual a 2).
  - 04/11 (noite), regra do Sergio "máximo de processamento na GPU": usar a folga da placa para qualidade custou mais do
    que sobrava (resolução 100% praia 60, GI/reflexos Alto 61, sombras/AA Épico 63, tudo junto 43–52): mantidos os padrões.
    Separar o vidro de 27 malhas para o corpo usar Nanite (`mare_hud splitglass`/`glassslots`, Geometry Script, vidro por
    cima em tempo de execução via `Content/Data/glass_split.json`) deu praia 64–66 e quiosque 70–71, PIOR que 67–69/74:
    eram só 77 cópias e o vidro virou 39 componentes novos. Desfeito; a ferramenta fica para malhas com muitas cópias.
    Próximo passo de GPU, se valer: multidão distante em animação gravada em textura (AnimToTexture) ou Animation
    Sharing; sem pessoas a praia ganhava ~4 FPS, então o ganho máximo é pequeno para o tamanho do trabalho.
- [x] P1 DLSS 4.5 no executável: plugins carregam, DLSS e Geração de quadros aparecem no menu (RTX 40). DLSS Super
  Resolution provado no executável (04/11, `bench_package.ps1 -Exec "r.NGX.DLSS.Enable 1"`: recurso NGX DLSS-SR criado,
  praia 71, quiosque 73, saguão 76, vila 87 FPS).
- [ ] [bloqueado-usuario] (precisa do Sergio clicar na janela do jogo durante o teste) P1 Provar a Geração de quadros: o plugin só gera quadros com a janela EM FOCO (StreamlineDLSSG.cpp, `FApp::HasFocus`) e o Windows
  não deixa um script dar foco; o Sergio clica na janela durante `bench_package.ps1 -Focus -Exec "r.Streamline.DLSSG.Enable 1"`
  (o resultado mostra "na tela" = quadros exibidos e `focus`). Testar também DLSS Super Resolution (`r.NGX.DLSS.Enable 1`).
- [x] P0 Sessões de 2 h sem crash (GPU page fault do hotel mitigado com `r.Lumen.AsyncCompute=0`; re-testar).
  04/11: `tools/ue58/bench_package.ps1 -Soak 7200` (executável, tudo liberado): 120 min, 60 voltas pelos 4 setores dormindo
  entre elas (60 dias de jogo, saguão do hotel visitado 60 vezes), nenhum erro no log, FPS estável do início ao fim
  (praia 35, quiosque 35, saguão 42, vila 49), RAM 4,0 GB no início e 3,4 GB no fim.
- [x] P0 Saves: 3 slots, autosave ao dormir, migração do slot1 antigo, backup `.bak` (teste `MareAlta.Saves.Slots`, 02/11).
- [x] P1 Memória: build de pessoas e texturas 8K das banhistas (avaliar 4K), tamanho do pacote final.
  - 04/11: nenhuma textura das pessoas passa de 4K (build Medium; o 8K era só intermediário do maiô). Texturas 4K de
    objetos pequenos limitadas por MaxTextureSize (fonte intacta): açaí/coco 1024, banqueta/sofá de vime, fogueira e
    celular 2048; conferido de perto (`D:/CodexTemp/qa/texcap2.jpg`). Roupas Khaos 6K já em 1024.
  - 04/11, erro grave evitado: o jogo carrega por caminho em texto (LoadClass/LoadObject e JSON) MetaHumans, roupas de
    banho, animações, ícones e todo `/Game/Custom` (personalização, festas, sala de jogos): 303 pacotes ficariam FORA do
    executável. `DirectoriesToAlwaysCook` ganhou essas pastas e só os 35 MetaHumans das listas. `tools/ue58/qa/cook_audit.py`
    (no portão de QA) reprova qualquer caminho carregado por texto que não seja cozido; assets de edição pesados
    (MH_*.uasset 117 MB, OA_* 170 MB) não entram.
  - 04/11: pacote final 6,1 GB (5,2 GB de conteúdo; 1,46 GB em 01/11, antes dos MetaHumans), 10.786 pacotes cozidos.
    No executável: 4,1 GB de RAM e 4,6 GB de VRAM na praia (perfil CSV do -MareBench). Log do executável limpo.
- [x] P1 Testes automáticos cobrindo cada sistema novo (23 testes MareAlta.* em 02/11) e QA de PIE com fotos por sistema
  (`docs/ue58/graphics-reference/*-20261102.*`).

## 10. Lançamento
Ver `ROADMAP_STEAM.md`: conta Steamworks e página, Steam Cloud, conquistas, build Shipping em PC limpo, demo,
Next Fest, playtest e beta, trailer, preço.

## 11. Tradução (por último, pedido do Sergio em 02/11)
Fazer depois de todo o resto, quando os textos estiverem estáveis.
- [x] Camada de tradução `MareLoc` (04/11): LOCTEXT registrado como polyglot (pt-BR nativo, en, es) e dicionário de textos
  montados pelo código (`MareLoc::Text/Tr`, modelos `{n}` e divisão por separadores do HUD). Todos os `FText::FromString`
  passam por ela; placas 3D (TextRender) fixas e dinâmicas também. Textos em `Content/Localization/Mare/*.json`, gerados por
  `tools/ue58/i18n_extract.py` (código + Data/*.json) e traduzidos em lotes (`i18n_batch.py`). Auditoria: `-MareLocAudit`
  registra `MARE_LOC_MISSING` no log.
- [x] **Inglês** completo (04/11): 111 LOCTEXT + 2.528 textos (~10,3 mil palavras), conferido no executável (menu, opções e HUD).
- [x] **Espanhol** completo (04/11), mesmo volume. Troca de idioma em Opções → Idioma (pt-BR / English / Español);
  `-culture=en` na linha de comando para testes.
- [x] Idiomas prontos e no jogo (04/11): pt-BR, en, es, zh-Hans, ru, de, fr, it, ja, ko, nl. O menu lista sozinho cada idioma
  que tem `Content/Localization/Mare/<cultura>.json`; fontes CJK/cirílico por `tools/ue58/i18n_fonts.py`; placas 3D com
  cirílico ou CJK mostram o texto original (a fonte das placas é só latina); bússola com as letras de cada idioma.
  Os 8 restantes ficaram no fim da fila (seção 17).
- [ ] [bloqueado-usuario] (decisão de gosto do Sergio) Nomes próprios (Seu Gregory, Dona Rita...) seguem em letras latinas no chinês/japonês/russo: decidir se transliterar.
- [ ] Revisão por falante nativo de cada idioma e teste de layout (textos maiores em alemão/russo não podem cortar). [bloqueado-usuario] (precisa de revisores nativos; o teste de layout fica junto da tradução)
- [ ] Página da Steam e conquistas nos mesmos idiomas. [bloqueado-usuario] (precisa da conta Steamworks do Sergio)

## 12. Ilha do passeio de barco (pedido do Sergio em 02/11; redefinido em 04/11)
- [x] **Ilha vulcânica** a 1,3 km da praia (04/11): estratovulcão como o Arenal gerado no bpy (`tools/ue58/gen_volcano.py`,
  não há vulcão gratuito com licença livre), ravinas fundas, mata nas encostas baixas, topo de cinza, rocha fosca
  (Poly Haven CC0). Fumaça em dias sorteados (`mare.VolcanoSmoke`), erupção em noites sorteadas (`mare.VolcanoErupt`):
  lava vermelha escorrendo pelas ravinas da face da praia, chafariz de fagulhas e mar bem agitado. Editor:
  `mare_hud module mare_volcano.build`. Cruzeiro, baleia e galeão saíram do jogo a pedido do Sergio.
- [ ] [adiado-usuario] (o pedido de 04/11 pede só a ilha) O passeio de barco até a ilha, com desembarque e trilha.

## 13. Correção de assets low poly (pedido do Sergio em 02/11, para o final)
Regra do projeto: nenhum asset low poly no jogo.
- [x] **Fogueira da festa junina** (02/11): lenha escaneada (Quixel "Campfire", da biblioteca do usuário) e fogo com
  fumaça simulados (Niagara Fluids `Grid2D_Gas_SmokeFire`, plugin da Epic ativado); foto `fogueira-junina-20261102.jpg`.
  Antes: a lenha (`festa_campfire_logs`, vinda da Godot) eram poucos troncos lisos e a chama
  ficou com cara de cone. Refazer com toras de verdade (casca com relevo, pontas cortadas e queimadas, brasas e cinzas
  na base, pedras em volta) e um fogo convincente (chamas em camadas com movimento, faíscas e fumaça em partículas).
- [x] Revisar os outros modelos trazidos da versão Godot para as festas: barraca trocada pela barraca listrada do Fab
  (`festa_stall_fab`, 03/11); cabine do DJ, faixa e bandeirinhas sem substituto gratuito adequado no Fab (refazer ou
  procurar de novo); e qualquer outro prop com poucas faces que aparecer na varredura visual final.
  04/11: faixa refeita (`festa_banner`, gen_festival.py banner + gen_banner_print.py): lona impressa "Festa na Praia"
  virada para a festa, verso liso, ilhoses e cordas de 12 mm amarradas nos bambus; a antiga era um pano em branco.
  Bandeirinhas já eram do gen_festival.
  04/11: palco do DJ refeito (`festa_dj`, gen_festival.py dj): treliça com diagonais, 5 refletores em suporte U, caixas
  em tripé com cone/corneta, bancada com estampa "Maré Alta DJ" e LED, toca-discos, mixer, notebook e cabos; virado para
  a pista (giro 180° no MareEventsWorld: a frente da antiga ficava de costas para os dançarinos). Conferido no lugar
  da festa (`D:/CodexTemp/qa/dj_scene2.jpg`).

## 14. Eventos cômicos e personagens memoráveis (pedido do Sergio em 31/10, issue #4; para o final)
Especificação completa em `docs/ue58/HUMOR_EVENTOS_COMICOS.md`
([issue #4](https://github.com/sergiomrge-tech/simulador-resort/issues/4)). Humor ocasional, sem pastelão, sem travar
atendimento, economia ou saves; um evento por vez, com cooldown e seed testável; textos em PT-BR e EN.
- [x] Gestor leve de eventos cômicos (03/11): `UMareComicEvents` + `Content/Data/comic_events.json` — IDs `HUM-00x`, estados
  idle/active/resolved, um por vez, intervalo próprio e global em minutos de jogo, sorteio com semente (`mare.ComicSeed`),
  horário e chance por evento, intervalos e contagem de falas no save (`comic`). Um passante perto do jogador para, se
  vira e chama; E abre a conversa (`UMareVillageWorld::Quip`, painel embaixo, E/Esc fecha); ignorado, termina sozinho.
  Nada mexe em dinheiro, estoque ou pedidos. QA `mare.Comic <id>`; teste `MareAlta.Gameplay.ComicEvents`.
- [x] HUM-005 Turista perdido pergunta onde fica a praia (03/11): só com o jogador do lado da praia; 3 perguntas, 2
  respostas com reação; conferido no PIE (o turista para, chama e a conversa abre embaixo da tela).
- [x] Diálogos recorrentes (03/11): Seu Arnaldo (HUM-007, 5 reclamações em sequência) e Seu Bené, pescador (HUM-008, o
  peixe cresce a cada conversa: 2 kg → do tamanho da jangada), pelo mesmo gestor; textos PT-BR e EN nos dados.
- [x] HUM-002 Turista influenciador exigente (selfies, pede mesa com vista), sem atrasar a fila; bônus pequeno depois. (03/11, conferido por captura)
- [x] HUM-001 Gaivota rouba batata da mesa, turista reage; sem mexer em estoque/pagamento no começo. (03/11, conferido por captura)
- [x] HUM-003 Cachorro foge com um chinelo: cancelado (03/11, o Sergio tirou gatos e cachorros do jogo).
- [x] HUM-004 Guarda-sol levado pelo vento; recolocar é opcional; física controlada. (03/11, conferido por captura)
- [x] HUM-006 Atendente iniciante atrapalhado (quase derruba bandeja), diminui com treinamento; sem perder pedido/dinheiro. (03/11, conferido por captura)
- [~] [adiado-usuario] Critérios de aceite da especificação: 100 ciclos sem travar NPC/fila, sem cobrança/estoque duplicados no reload,
  fotos e clipe do EXE. 03/11: a parte da economia virou teste permanente `MareAlta.Acceptance.HundredCycles` (100
  ciclos de pedido/retirada/entrega, salvar e recarregar em outra sessão a cada 10, pedido pela metade retomado): caixa
  sobe exatamente a venda registrada (preço + gorjeta da decoração), estoque cai 1 por retirada, nada cobrado nem
  entregue duas vezes. Falta: 100 ciclos com NPCs e fila no mundo (04/11: o Sergio faz esse teste jogando; o script
  automático foi removido a pedido dele), e fotos/clipe do executável (só quando o Sergio pedir o EXE).

## 15. Balanceamento e diversão (no fim da fila, pedido do Sergio em 03/11)
Objetivo: o jogo ser divertido e não cansativo nem maçante, com várias atividades acontecendo ao mesmo tempo (quiosque,
negócios, hóspedes, salão, passeios, eventos) e o jogador sempre escolhendo o que fazer.
- [~] [bloqueado-usuario] (precisa do playtest cronometrado do Sergio) P1 **Balanceamento** financeiro e econômico de tudo, jogando do zero até o Grand Hotel (02/11: primeira passada por modelo em
  `docs/ue58/BALANCEAMENTO.md` e `tools/ue58/balance_model.py`; falta o playtest cronometrado para trocar as hipóteses):
  - desbloqueio novo a cada 10–20 min;
  - preços das expansões, salários, diárias e renda do salão.
- [x] (04/11) P1 Duração do Acesso Antecipado: Sergio pediu campanha de **12 h no mínimo**. Relógio voltou a 1 min/s (dia de
  16 min), hotel com fama 9 e ato 5 (salão, 20 receitas, 40 personalizações, fama 10, 4.000 vendas) antes da festa;
  modelo `balance_model.py`: festa no dia 55, ~15 h (a personalização adianta alguns dias). Objetivo sempre visível no
  painel (tarefa + "R$ x / y · fama a/b"). Ver docs/ue58/BALANCEAMENTO.md (segunda passada).
- [x] (liberado 04/11 para o Acesso Antecipado; Sergio 04/11: "precisa ter desafio, um pouco difícil mas também divertido") P1 Ritmo e desafio: nunca mais de 1–2 min sem algo a fazer; tarefas paralelas que se sobrepõem (pedido no quiosque enquanto
  o bar chama, hóspede na recepção, evento cômico), sem fila de espera longa nem tarefa repetitiva demais.
  FEITO 04/11: cada cliente do quiosque dá estrelas pelo tempo de espera (5★ na hora, 2,5★ no limite) e quem desiste
  vai embora bravo com 1★ e um aviso; as estrelas mexem no movimento (`WordOfMouth`: 0,7× a 1,25×); paciência de 80 s
  (era 120); picos de almoço (12–14h) e pôr do sol (17–18h30) com 60% mais clientes; manutenção diária de 0,5% das
  expansões (`DailyUpkeep`). Junto com a oferenda diária, os eventos cômicos e as missões, o dia tem tarefas que se
  sobrepõem. Testes em MareSimulationTests (Customization, DayClose). Confirmar a dificuldade num playtest.

## 16. Ponto turístico no morro (no fim da fila, pedido do Sergio em 03/11)
- [ ] [bloqueado-usuario] (sistema grande: aguarda o Sergio escolher a prioridade e subir o esforço do Opus, regra global) P2 O morro careca ao fundo vira ponto turístico: no alto, uma estátua ORIGINAL de Jesus Cristo de braços abertos
  (figura cristã livre; não copiar o desenho do Cristo Redentor do Rio, que tem direitos de imagem controlados),
  com mirante; uma trilha subindo a montanha desde a vila (caminho de terra e degraus de pedra, vegetação, corrimão
  de madeira nos trechos íngremes, bancos e placas), visitável a pé, com vista do resort lá de cima; algo bem legal
  (ex.: pôr do sol no mirante, foto com a estátua, turistas subindo). Cobrir o morro careca com mata.

## 17. Traduções restantes (no fim da fila, pedido do Sergio em 04/11)
Os 18 idiomas escolhidos são os do Supermarket Simulator, menos turco e lituano; 10 já estão prontos (seção 11).
- [ ] (04/11: Sergio pediu terminar; fica depois da campanha, porque os textos novos também precisam de tradução) Português de Portugal (pt-PT), polonês (pl), tcheco (cs), húngaro (hu), romeno (ro), dinamarquês (da)
  e finlandês (fi). Processo: criar `<idioma>.json` vazio, rodar `i18n_extract.py`, traduzir em lotes com
  `i18n_batch.py show/merge` sem rodar o extrator entre show e merge (os índices mudam quando o source.json ganha textos), `i18n_batch.py compose <idioma>`, `i18n_fonts.py`, captura com
  `-culture=<idioma> -MareLocAudit`. Todos usam letras latinas (fontes atuais já cobrem).

## 18. Multidão na placa de vídeo (na fila, pedido do Sergio em 04/11)
- [ ] [adiado-usuario] (vale quando quisermos mais gente na praia) Pessoas distantes com animação gravada em textura e
  desenhadas pela placa (técnica da Epic para multidões, plugin AnimToTexture). Medição de 04/11: sem nenhuma pessoa a
  praia ganhava só ~4 FPS, então hoje não compensa; exige gerar as animações de várias MetaHumans. Permite multidão
  grande sem custo no processador (regra global: máximo de processamento na GPU).

## 19. Pedidos de 04/11 para depois do vulcão
- [x] Mar com mais ondas no dia a dia (04/11: ondulação longa de ~1,7 m, ondas médias 1,7x, cristas tipo Gerstner, relevo no normal e espuma sem grade): piso de agitação `mare.SeaSwell` 0,25 aplicado em 04/11; conferir por captura e
  ajustar o material do mar se ainda parecer calmo. 04/11: ainda parece calmo de dia (o material só perturba a superfície);
  ondas de verdade pedem deslocamento (Gerstner) no mar. Com o mar bravo, longe da costa aparecem manchas ovais de espuma
  em grade regular (textura repetida): corrigir junto.
- [x] (04/11) **Tsunami**: uma tarefa que o
  personagem precisa cumprir todo dia; se esquecer, começa chuva fortíssima, mar extremamente agitado e ao fundo sobe uma
  onda gigante até 100 m que devasta a ilha e encerra o jogo. Evento épico.
  Decisão do Sergio (04/11): a tarefa é uma **oferenda** diária a um velho que mora numa casa toda de madeira no topo da
  montanha e fica sentado num banco na frente da casa. Falta: modelo da casa (asset gratuito antes de modelar), trilha até
  o topo, o velho sentado (MetaHuman), interação da oferenda e a sequência do tsunami.
  Decisões do Sergio (04/11): subida por **bondinho** (tipo Pão de Açúcar) saindo dos fundos da vila, trilha a pé opcional;
  NÃO mostrar o mapa devastado: quando a onda atinge o herói a tela escurece e aparece um GAME OVER grande.
  Casa: "Wooden House" (Helindu.Art, Fab, CC BY 4.0) em D:/Assets/Fab/wooden_house. Topo escolhido: x 4000, y 38750, z ~107 m.
  FEITO 04/11: `UMareSummitWorld` (Seu Tibúrcio no banco do cume, conversa em Quip, oferenda = produto do quiosque
  nas mãos ou um abraço enquanto não há quiosque; avisos 15h/18h; presságio 19h com chuva, mar 1,9x e relâmpagos;
  às 22h silêncio, mar liso e a onda de 100 m (`tools/ue58/gen_tsunami_wave.py`, `M_TsunamiWave`) sobe e avança;
  ao atingir o herói, tela preta + GAME OVER com "Recomeçar o dia" (foto da manhã) e "Menu principal"). Teste
  `MareAlta.Gameplay.SummitOffering`; QA `mare.ElderMet 1`, `mare.TsunamiNow 1|2`.
- [x] (04/11) **Campanha principal** com história completa até o final e tudo pronto no jogo; tom de comédia, animado
  e calmo, clima de praia. FEITO: 16 missões em 4 atos (`definitions.json` campaign; textos com humor), novas
  `elder`/`offerings`/`finale`, final "A Festa da Maré Alta" (`UMareSummitWorld::UpdateFinale`: vila na praia às 20h,
  Seu Tibúrcio desce o morro, o vulcão solta "fogos", tela FIM com créditos e "Continuar na praia"). Teste da campanha
  inteira em MareSimulationTests; QA `mare.FinaleNow 1`.
- [ ] [bloqueado-usuario] (cota de imagens do Canva esgotada em 04/11; renovar a cota ou o Sergio decidir) **Animação de abertura** em estilo desenho (Canva) e **animações nos eventos
  principais** da história.
  04/11: 3 de 6 quadros gerados no Canva em aquarela infantil (mídias MAHZ_tdgrZI vovó e a chave, MAHZ_tPWSC4 o ônibus
  chegando, MAHZ_vxA6mE o quiosque FECHADO com a gaivota). Os quadros 4 (Seu Tibúrcio gritando do morro), 5 (quiosque
  lotado ao pôr do sol) e 6 (vila em festa, vulcão com fogos, espaço para o título) voltaram "quota_exceeded": a cota de
  imagens do Canva do Sergio acabou. Falta também exportar em resolução cheia (design com uma imagem por página → PNG)
  e montar a sequência no jogo (Ken Burns, legendas e música).
- [x] Noite mais escura (Sergio, 04/11): `mare.NightDarken` tira 1,3 stop da exposição à noite; conferir praia, vila, quiosque e erupção.
- [x] Som de mata fechada ao longo da trilha do cume (Sergio, 04/11): `forest_loop` (OpenGameArt CC0) entra além dos fundos da vila (y>8400), mais baixo à noite e na chuva; medido 0,126 na trilha e no cume, 0 na vila e na praia.
- [ ] Casa do herói com 1 andar (Sergio, 04/11): quarto em cima com varanda; no térreo sala, banheiro e cozinha. É uma EXPANSÃO PAGA (comprada no jogo; só acontece depois de pagar). Fazer depois do tsunami.
