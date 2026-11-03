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
- [ ] P1 Vasos de pachira do saguão do hotel com colisão de copa enorme (bloqueia a mira). Corrigir a colisão
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
- [ ] P2 Animais da vila e fauna marinha ainda com aparência cartoon; horizonte subaquático azul e vazio.
- [ ] P2 Interior dos quartos do hotel além da suíte visitável (a torre é casca com fachada).

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
- [~] P1 **Salão de jogos** (02/11):
  - [x] partida de sinuca jogada até o fim (02/11): no Play com `mare.PoolAutoPlay 1` + `mare.PoolQA` (hóspede venceu 4×3 em
    11 tacadas, placar e câmera conferidos, foto `sinuca-partida-20261102.jpg`) e teste `MareAlta.Gameplay.PoolFullMatch`
    (40 partidas completas com a física real: todas terminam, média 6,3 tacadas, bolas sempre na mesa, os dois lados vencem);
  - [x] pebolim (modelo bpy `tools/ue58/gen_game_room_extras.py`) com partida rápida de 3 rodadas contra um hóspede;
  - [x] 2 fliperamas "Maré Attack" com tela e letreiro acesos, partida rápida de 3 rodadas;
  - [x] hóspedes jogando das 18h às 23h e renda das fichas (mais jogadores com o hotel cheio).
  Dados em `Content/Data/business_games.json` (`pebolim`, `fliperama`, `game_room`), teste em `MareAlta.Gameplay.BusinessCounter`.
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
  - [ ] humor além do cansaço (fica para os eventos cômicos da seção 14, atendente iniciante);
  - teste `MareAlta.Gameplay.StaffShiftsAndLevels` (24/24 MareAlta.* passando); foto
    `docs/ue58/graphics-reference/equipe-20261102.jpg`.
- [ ] P2 Pedidos especiais e clientes VIP/influenciador no quiosque (eventos cômicos da tarefa #4).

## 4. Progressão, economia e conteúdo
- [~] P1 **Balanceamento** jogando do zero até o Grand Hotel (02/11: primeira passada por modelo em
  `docs/ue58/BALANCEAMENTO.md` e `tools/ue58/balance_model.py`; falta o playtest cronometrado para trocar as hipóteses):
  - desbloqueio novo a cada 10–20 min;
  - preços das expansões, salários, diárias e renda do salão.
- [ ] P1 Duração do Acesso Antecipado: 6–10 h de conteúdo com objetivo sempre visível.
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
- [ ] P1 Mais banhistas: mulheres e homens de outras idades e tipos de corpo.
- [ ] P1 Animações (03/11): 7 clipes gratuitos de captura do Fab (Animation Shopee) importados
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
  - deitar na espreguiçadeira e na canga;
  - nadar no mar e na piscina;
  - comer e beber sentado (já existe);
  - conversar com gestos sentado (feito, `SitTalk`; em pé ainda falta clipe bom); dançar nas festas (feito);
  - limpar e atender (equipe).
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
- [ ] P1 Rosto: expressões faciais simples (sorriso ao receber, irritado na negociação).
- [ ] P2 Crianças e famílias (se houver presets/assets adequados).

## 6. Mundo e arte
- [x] Barcos detalhados (jangadas e botes), palmeiras, janelas, piscinas, mata dos morros.
- [ ] P1 Varredura visual final de todo o mapa:
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
  - texturas;
  - folhagem muito clara à noite;
  - ondas, espuma e respingos.
- [ ] P1 Personalização com 5 opções em tudo:
  - quiosque, expansões, hotel, piscina, tobogã;
  - casa (cama, sofá, armário, TV).
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

## 7. Áudio
- [x] P1 Música por lugar e horário (02/11): zonas em `Content/Data/audio_zones.json` (saguão do hotel bossa, restaurante relax,
  salão de jogos à noite pop, bar reggae, piscina calipso), rádio portátil abaixa dentro das zonas; níveis medidos no PIE.
- [x] P1 Efeitos de todas as ações novas (02/11, 42 sons CC0 ligados: recepção, limpeza, sinuca, bar, dinheiro, negociação):
  - campainha da recepção, chaves, cama, lixo;
  - tacadas e bolas da sinuca;
  - liquidificador e coqueteleira do bar.
- [ ] P1 Mixagem final e volumes por categoria (já existem: geral, música, efeitos, ambiente).
- [ ] P2 Vozes curtas (murmúrios) sem diálogo falado, respeitando a regra de áudio suave.

## 8. Interface e experiência
- [x] P0 **Menu principal**: Novo jogo, Continuar, Carregar (3 slots), Opções, Créditos, Sair (02/11, foto no PIE;
  QA de PIE usa `-MareSkipMenu`).
- [x] P0 **Opções completas** (02/11, teste `MareAlta.Options.SaveAndReload`; idioma só troca fora do editor):
  - gráficos detalhados, resolução, janela, VSync, FPS, upscaler, FOV;
  - mouse e controle, remapear teclas;
  - idioma.
- [~] P0 **Controle** (Xbox/PlayStation) em todo o jogo e nos menus. (Tradução: ver a seção 11, no final.)
  - Código feito em 02/11 (`MareGamepad.h/.cpp`, mapeamentos em `Config/DefaultInput.ini`), falta testar com controle de verdade no EXE.
    Mapa fixo: analógico esquerdo anda, direito olha (sensibilidade própria + inverter Y); A pula/sobe nadando; **X interage**
    (A ficou com o pulo para não pular ao falar/servir); Y ou View celular; Start pausa; LT segurar ou L3 alternar corre; B mergulha.
    Menus: foco no 1º botão ao abrir com o controle, direcional/analógico navega, A confirma, B volta/fecha, LB/RB trocam abas,
    analógico direito rola. Sinuca: analógico mira, segurar RT dá força, B sai. HUD mostra botão ou tecla conforme a última entrada;
    opção "Botões do controle" Xbox/PlayStation. Testes: `MareAlta.Gamepad.MappingsAndLabels` e `MareAlta.Gamepad.MenuFocusAndBack`.
- [ ] P1 Três propostas de HUD/celular mais comercial (pedido antigo, apresentar antes de escolher).
- [x] P1 Acessibilidade (02/11): tamanho da interface e do texto (85–150%, foto `interface-130-20261102.png`), dicas do
  tutorial liga/desliga, modo para daltonismo (+/- nas variações de estrelas). Não há falas, então legendas não se aplicam.
  Em janelas pequenas, 140–150% encosta nas bordas do celular.
- [x] P2 Indicador no mapa ou bússola com os lugares (pousada, hotel, salão, negócios): faixa sob a placa com N/S/L/O e
  os lugares liberados na direção do olhar (`Content/Data/map_markers.json`), mais perto primeiro, em duas linhas;
  foto `docs/ue58/graphics-reference/bussola-20261102.png`.

## 9. Desempenho e estabilidade
- [ ] P0 FPS medido no executável:
  - setores pesados: praia com pessoas, saguão do hotel, vila à noite;
  - MetaHumans: limite visível, LOD, grooms.
- [ ] P0 Sessões de 2 h sem crash (GPU page fault do hotel mitigado com `r.Lumen.AsyncCompute=0`; re-testar).
- [x] P0 Saves: 3 slots, autosave ao dormir, migração do slot1 antigo, backup `.bak` (teste `MareAlta.Saves.Slots`, 02/11).
- [ ] P1 Memória: build de pessoas e texturas 8K das banhistas (avaliar 4K), tamanho do pacote final.
- [x] P1 Testes automáticos cobrindo cada sistema novo (23 testes MareAlta.* em 02/11) e QA de PIE com fotos por sistema
  (`docs/ue58/graphics-reference/*-20261102.*`).

## 10. Lançamento
Ver `ROADMAP_STEAM.md`: conta Steamworks e página, Steam Cloud, conquistas, build Shipping em PC limpo, demo,
Next Fest, playtest e beta, trailer, preço.

## 11. Tradução (por último, pedido do Sergio em 02/11)
Fazer depois de todo o resto, quando os textos estiverem estáveis.
- [ ] Todos os textos do jogo em tabelas de localização da Unreal (LOCTEXT/StringTable), sem texto fixo no código;
  inclui menus, celular, HUD, missões, cartas, placas 3D (TextRender) e nomes de produtos.
- [ ] **Inglês** completo.
- [ ] Vários idiomas (os que mais vendem na Steam): espanhol, chinês simplificado, russo, alemão, francês,
  japonês, coreano e português de Portugal; fontes com suporte a CJK e cirílico.
- [ ] Revisão por falante nativo de cada idioma e teste de layout (textos maiores em alemão/russo não podem cortar).
- [ ] Página da Steam e conquistas nos mesmos idiomas.

## 12. Ilha do passeio de barco (pedido do Sergio em 02/11, para o final)
- [ ] Ilha circular ao fundo, no mar, destino do passeio de barco: bastante árvores e vegetação (nada de low poly),
  praia em volta e uma trilha passando pelo meio.
- [ ] O passeio de barco sai do píer, vai até a ilha (desembarque e trilha) e volta; paradas do passeio guiado na ilha.

## 13. Correção de assets low poly (pedido do Sergio em 02/11, para o final)
Regra do projeto: nenhum asset low poly no jogo.
- [x] **Fogueira da festa junina** (02/11): lenha escaneada (Quixel "Campfire", da biblioteca do usuário) e fogo com
  fumaça simulados (Niagara Fluids `Grid2D_Gas_SmokeFire`, plugin da Epic ativado); foto `fogueira-junina-20261102.jpg`.
  Antes: a lenha (`festa_campfire_logs`, vinda da Godot) eram poucos troncos lisos e a chama
  ficou com cara de cone. Refazer com toras de verdade (casca com relevo, pontas cortadas e queimadas, brasas e cinzas
  na base, pedras em volta) e um fogo convincente (chamas em camadas com movimento, faíscas e fumaça em partículas).
- [~] Revisar os outros modelos trazidos da versão Godot para as festas: barraca trocada pela barraca listrada do Fab
  (`festa_stall_fab`, 03/11); cabine do DJ, faixa e bandeirinhas sem substituto gratuito adequado no Fab (refazer ou
  procurar de novo); e qualquer outro prop com poucas faces que aparecer na varredura visual final.

## 14. Eventos cômicos e personagens memoráveis (pedido do Sergio em 31/10, issue #4; para o final)
Especificação completa em `docs/ue58/HUMOR_EVENTOS_COMICOS.md`
([issue #4](https://github.com/sergiomrge-tech/simulador-resort/issues/4)). Humor ocasional, sem pastelão, sem travar
atendimento, economia ou saves; um evento por vez, com cooldown e seed testável; textos em PT-BR e EN.
- [ ] Gestor leve de eventos cômicos (IDs `HUM-00x`, estados idle/active/resolved, cooldown, um por vez), dados em JSON.
- [ ] HUM-005 Turista perdido pergunta onde fica a praia (olhando para ela); resposta curta, E/Esc fecha.
- [ ] Diálogos recorrentes: **Seu Arnaldo** (reclamão carismático) e o **pescador** com histórias cada vez mais exageradas.
- [ ] HUM-002 Turista influenciador exigente (selfies, pede mesa com vista), sem atrasar a fila; bônus pequeno depois.
- [ ] HUM-001 Gaivota rouba batata da mesa, turista reage; sem mexer em estoque/pagamento no começo.
- [ ] HUM-003 Cachorro foge com um chinelo; recolher é opcional.
- [ ] HUM-004 Guarda-sol levado pelo vento; recolocar é opcional; física controlada.
- [ ] HUM-006 Atendente iniciante atrapalhado (quase derruba bandeja), diminui com treinamento; sem perder pedido/dinheiro.
- [ ] Critérios de aceite da especificação: 100 ciclos sem travar NPC/fila, sem cobrança/estoque duplicados no reload,
  fotos e clipe do EXE.
