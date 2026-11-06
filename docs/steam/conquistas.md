# Conquistas e Rich Presence — Coconut Coast: Resort Simulator

Proposta para implementação, base efceab9. **36 conquistas**, nomes/descrições em pt-BR e en no [JSON editorial](conquistas.json). Não é payload pronto de importação do Steamworks. Dona Dilce e os nomes de pessoas/máquinas permanecem próprios.

Os cinco IDs CC_DEBT_* exigem o contrato novo de debt.json; **não existem ainda no save**. Os outros 31 usam campos já gravados pelo jogo. Não criar contadores acumulados fictícios para preencher a tabela. demo=true indica que a condição pode ser cumprida na demo, inclusive no jogo livre; 25% da dívida não é meta da sessão de 2 h. Conquistas de conteúdo full_game continuam bloqueadas em nova partida demo, mesmo com dados de save legado: conferir demo + conteúdo antes de premiar.

## Leitura das condições

Paths são relativos ao objeto State. >= e == comparam o valor; contains procura o id na lista; length>= conta a lista. sum_species soma somente sardinha/pargo/robalo/cioba/garoupa, excluindo best_* (medidas em cm). all_businesses exige os cinco ids e lvl >= min. any_tour exige algum resultado com id exato, guide=true e pax>=1; conferir imediatamente após RecordTourResult, pois a lista guarda só 12 registros. any_hotel_polished exige id começando por hotel_ e polished=true em stays.rooms. CC_BEACH_EVENT confere last.score>=0,5 após encerrar; done sozinho também conta fracassos e não serve.

IDs são permanentes; títulos podem ser revisados. Processar depois de transação salva e ao carregar, uma vez por id. Guardar uma fila/conjunto de ids concedidos/pendentes em metadados Steam novos (não confundir com prog.achievements.mestre_drinks existente). Reenviar os pendentes quando houver conexão, sem dinheiro/fama de recompensa. Não remover conquistas ao gastar, reiniciar semana, sair do minijogo ou perder a conexão. Não prometer migração de demo para o jogo completo antes de definir App IDs e testar; os campos do save permitem reconciliação onde ainda houver evidência. Histórico de passeios descartado não permite reconstrução retroativa exata.

## Condições e fontes

| ID | Nome pt-BR / en | Descrição pt-BR / en | Demo | Campo e condição | Fonte |
|---|---|---|---|---|---|
| CC_DEBT_FIRST | Um coco de cada vez / One Coconut at a Time | Faça o primeiro pagamento da dívida. / Make your first debt payment. | sim | `/prog/debt/paid_cents` >= 1 | debt.json + DIVIDA_DA_AVO.md (contrato novo) |
| CC_DEBT_25 | Um quarto mais leve / A Quarter Lighter | Pague R$ 250.000 da dívida. / Pay R$ 250.000 of the debt. | sim | `/prog/debt/paid_cents` >= 25000000 | debt.json + DIVIDA_DA_AVO.md (contrato novo) |
| CC_DEBT_50 | Metade da maré / Halfway Through the Tide | Pague R$ 500.000 da dívida. / Pay R$ 500.000 of the debt. | não | `/prog/debt/paid_cents` >= 50000000 | debt.json + DIVIDA_DA_AVO.md (contrato novo) |
| CC_DEBT_75 | Dá para respirar / Room to Breathe | Pague R$ 750.000 da dívida. / Pay R$ 750.000 of the debt. | não | `/prog/debt/paid_cents` >= 75000000 | debt.json + DIVIDA_DA_AVO.md (contrato novo) |
| CC_DEBT_FREE | Livre do boleto / Debt-free | Quite a dívida de R$ 1.000.000. / Pay off the R$ 1.000.000 debt. | não | `/prog/debt/paid_cents` >= 100000000 | debt.json + DIVIDA_DA_AVO.md (contrato novo) |
| CC_COMPANY | Sua primeira maré / Your First Tide | Crie sua empresa. / Create your company. | sim | `/company/created` == true | MareSimulation.cpp::CreateCompany / MissionAmount |
| CC_SALES_100 | Freguesia de casa / Regulars Welcome | Venda 100 produtos no quiosque. / Sell 100 kiosk products. | sim | `/kiosk_n` >= 100 | MareSimulation.cpp::MissionAmount(sales) |
| CC_EXP_KIOSK_TABLES | Um lugar para ficar / A Place to Stay | Compre a expansão Mesas e guarda-sóis. / Purchase the Tables and umbrellas expansion. | sim | `/unlocked/kiosk_tables` == true | MareSimulation.cpp::BuyExpansion |
| CC_EXP_BAR | Um brinde ao começo / A Toast to Beginnings | Compre a expansão Bar do Coqueiro. / Purchase the Bar do Coqueiro expansion. | sim | `/unlocked/bar` == true | MareSimulation.cpp::BuyExpansion |
| CC_EXP_POUSADA | Fique mais um dia / Stay Another Day | Compre a expansão Pousada. / Purchase the Guesthouse expansion. | sim | `/unlocked/pousada` == true | MareSimulation.cpp::BuyExpansion |
| CC_EXP_POOL | Sem medo de siri / Crab-free Floating | Compre a expansão Piscina. / Purchase the Pool expansion. | sim | `/unlocked/pool` == true | MareSimulation.cpp::BuyExpansion |
| CC_EXP_PASSEIOS | Além do balcão / Beyond the Counter | Compre a expansão Passeios. / Purchase the Tours expansion. | sim | `/unlocked/passeios` == true | MareSimulation.cpp::BuyExpansion |
| CC_EXP_GRAND_HOTEL | Vista de um milhão / A Million-real View | Compre a expansão Grand Hotel. / Purchase the Grand Hotel expansion. | não | `/unlocked/grand_hotel` == true | MareSimulation.cpp::BuyExpansion |
| CC_EXP_SALAO_JOGOS | Só mais uma partida / Just One More Game | Compre a expansão Salão de jogos. / Purchase the Game room expansion. | não | `/unlocked/salao_jogos` == true | MareSimulation.cpp::BuyExpansion |
| CC_CH_PIER | O píer fica de pé / The Pier Stands | Conclua o capítulo O píer do Seu Severino. / Complete the Seu Severino’s Pier chapter. | sim | `/prog/ch/pier` >= 3 | MareSimulation.h:83 IsChapterDone; MareSimulation.cpp::AdvanceChapter |
| CC_CH_PRAINHA | Depois da missa / After Mass | Conclua o capítulo A prainha do Padre Robson. / Complete the Padre Robson’s Hidden Beach chapter. | sim | `/prog/ch/prainha` >= 3 | MareSimulation.h:83 IsChapterDone; MareSimulation.cpp::AdvanceChapter |
| CC_CH_SABORES | Receita de família / Family Recipe | Conclua o capítulo Os sabores da Dona Cecília. / Complete the Dona Cecília’s Flavours chapter. | sim | `/prog/ch/sabores` >= 3 | MareSimulation.h:83 IsChapterDone; MareSimulation.cpp::AdvanceChapter |
| CC_CH_CARNAVAL | A vila na rua / The Village Celebrates | Conclua o capítulo O carnaval da Prefeita Tuanny. / Complete the Prefeita Tuanny’s Carnival chapter. | sim | `/prog/ch/carnaval` >= 3 | MareSimulation.h:83 IsChapterDone; MareSimulation.cpp::AdvanceChapter |
| CC_BAR_50 | Rodada da casa / A Round on the House | Sirva 50 drinks no bar. / Serve 50 drinks at the bar. | sim | `/bar/served` >= 50 | MareBar.cpp:191,429 |
| CC_BAR_MASTER | Mestre dos drinks / Cocktail Master | Descubra todas as receitas do bar. / Discover every bar recipe. | sim | `/prog/achievements/mestre_drinks` == true | MareBar.cpp:196–198 |
| CC_BAR_SECRET | Segredo do Coqueiro / The Coconut Secret | Conheça a receita coqueiro. / Learn the coqueiro recipe. | sim | `/bar/known` contains "coqueiro" | MareBar.cpp:184 |
| CC_TOUR_BARCO | Mar à vista / Out to Sea | Guie o passeio barco com pelo menos um passageiro. / Lead the boat tour with at least one passenger. | sim | `/tour_results` any_tour {"id": "barco", "guide": true, "pax_min": 1} | MareTours.cpp:230–236,258 (lista de 12 resultados) |
| CC_TOUR_SNORKEL | Debaixo da maré / Beneath the Tide | Guie o passeio mergulho com pelo menos um passageiro. / Lead the snorkelling tour with at least one passenger. | sim | `/tour_results` any_tour {"id": "snorkel", "guide": true, "pax_min": 1} | MareTours.cpp:230–236,258 (lista de 12 resultados) |
| CC_TOUR_FAROL | Luz no caminho / Light the Way | Guie o passeio trilha ao farol com pelo menos um passageiro. / Lead the lighthouse trail tour with at least one passenger. | sim | `/tour_results` any_tour {"id": "farol", "guide": true, "pax_min": 1} | MareTours.cpp:230–236,258 (lista de 12 resultados) |
| CC_BIZ_ALL | Vizinho empreendedor / Village Entrepreneur | Tenha os cinco negócios da vila no nível 1 ou maior. / Own all five village businesses at level 1 or above. | sim | `/prog/biz` all_businesses {"ids": ["sorveteria", "food_truck", "aluguel", "souvenir", "surfe"], "field": "lvl", "min": 1} | MareBizCommon.cpp::BizState / BusinessLevel |
| CC_BIZ_MAX | A vila prospera / A Thriving Village | Tenha os cinco negócios da vila no nível 3 ou maior. / Own all five village businesses at level 3 or above. | sim | `/prog/biz` all_businesses {"ids": ["sorveteria", "food_truck", "aluguel", "souvenir", "surfe"], "field": "lvl", "min": 3} | MareBizCommon.cpp::BizState / BusinessLevel |
| CC_FISH_FIRST | Foi fisgado / Hooked | Pesque seu primeiro peixe. / Catch your first fish. | sim | `/prog/fish` sum_species 1 | MareLeisure.cpp::CatchFish; MareSimulation.cpp::MissionAmount(fish) |
| CC_FISH_RARE | História de pescador / A Fish Worth Bragging About | Pesque uma garoupa. / Catch a garoupa. | sim | `/prog/fish/garoupa` >= 1 | MareLeisure.cpp::CatchFish |
| CC_PHOTO_10 | Álbum de família / Family Album | Guarde 10 fotos no álbum. / Keep 10 photos in the album. | sim | `/prog/album` length>= 10 | MareLeisure.cpp::RecordPhoto (máximo 200) |
| CC_HOTEL_VIP | Pedido atendido / Special Delivery | Conclua um pedido VIP do hotel. / Fulfil a hotel VIP request. | não | `/prog/hotel_rooms/vip_done` >= 1 | MareHotelRooms.cpp:175–179 |
| CC_HOTEL_POLISH | Capricho de família / Family Standards | Arrume um quarto do hotel sem ajuda da equipe. / Clean a hotel room without staff assistance. | não | `/stays/rooms` any_hotel_polished true | MareHotelRooms.cpp:126–131; HotelRoom usa stays.rooms |
| CC_RESTAURANT_STARS | Três estrelas no caderno / Three Stars in the Notebook | Ganhe as três estrelas do crítico. / Earn all three critic stars. | não | `/prog/restaurant/stars` >= 3 | MareRestaurant.cpp::RestaurantStars / ReviewCritic |
| CC_BEACH_EVENT | Tudo pronto na areia / Ready on the Sand | Realize um evento montado com ao menos metade das peças. / Host a beach event with at least half its pieces placed. | não | `/hotel_events/last/score` >= 0.5 | MareHotelEvents.cpp::StartHotelEvent / HotelEventsHour (last ao encerrar) |
| CC_CUP | Campeão da Maré / Tide Champion | Vença o Campeonato da Maré. / Win the Campeonato da Maré. | não | `/billiards/cups` >= 1 | MarePoolCup.cpp:169–173 |
| CC_ARCADE_JANGADA | Contra a corrente / Against the Current | Registre uma pontuação positiva em Corrida de Jangada. / Record a positive score in Corrida de Jangada. | não | `/prog/biz/fliperama/records/jangada` >= 1 | MareArcade.h:85 GameId; MareArcade.cpp:35,216 |
| CC_ARCADE_PINBALL | Luz na máquina / Light Up the Machine | Registre uma pontuação positiva em Pinball do Farol. / Record a positive score in Pinball do Farol. | não | `/prog/biz/fliperama/records/pinball` >= 1 | MareArcade.h:85 GameId; MareArcade.cpp:35,216 |

## Rich Presence

Textos sem nome personalizado do jogador. Os gatilhos abaixo são pontos de integração propostos em métodos/widgets existentes; não são novos campos persistentes de gameplay. Usar uma única atividade atual, dar prioridade a minijogo/passeio/painel ativo e voltar ao fallback ao fechar/sair/carregar. No quiosque é o contexto da interação, não apenas company.kiosk_open (o jogador pode estar longe). O fallback sem dívida só vale após quitação no jogo completo. A integração deve mapear estes ids aos recursos do Steamworks; nenhuma sessão multiplayer é oferecida.

| ID | pt-BR | en | Ponto de integração |
|---|---|---|---|
| resort | Administrando o Maré Alta | Managing Maré Alta | fallback |
| kiosk | No quiosque | At the kiosk | interação Customer/Fridge/Cupboard/KioskSign |
| fishing | Pescando | Fishing | AMareController::StartFishing / fechar SMareFishingGame |
| bar | Preparando drinks | Mixing drinks | SMareBarPrepGame aberto / fechar |
| boat | Guiando um passeio de barco | Leading a boat trip | UMareBoatTourWorld::Start / Finish |
| snorkel | Mergulhando | Snorkelling | UMareSnorkelWorld::Start / Finish |
| trail | Na trilha do farol | On the lighthouse trail | UMareTrailWorld::Start / Finish |
| games | No salão de jogos | In the game room | UMareGameRoom/UMareArcade::IsPlaying |
| debt | Cuidando da dívida de Dona Dilce | Taking care of Dona Dilce’s debt | painel de dívida proposto aberto |
| free | Um resort sem dívida | A debt-free resort | fallback se prog.debt.paid_cents == principal_cents |

## Aceite

Testar save sem campos opcionais, dois loads sem prêmio duplicado, conta offline/online e cada limite imediatamente abaixo/no valor. Para dívida: 0/1 centavo, 25/50/75/100%; demo bloqueia acima de 25%. Testar que prêmios de campeonato de NPC não contam como vitória do jogador e que tamanho best_garoupa não conta como peixe pescado. Ícones, configuração/publicação Steam, App IDs e testes no executável ficam para o responsável pela integração.
