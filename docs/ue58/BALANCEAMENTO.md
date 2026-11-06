# Demo grátis de ~2 h — números aplicados (Claude, 06/11/2026)

O primeiro lançamento é a demo (`definitions.json` → `"demo": true`). Ela termina quando o jogador tem todas as
expansões que não são `full_game` e os 4 capítulos da vila (mesma condição da tela final, `MareEvents`). O modelo
ganhou o marco **`fim_demo`** e a meta de **1,5–2,5 h** (`DEMO_HOURS`).

Antes, no ritmo de 06/11, o fim da demo vinha no dia 13/10/8 (casual/médio/dedicado), ou seja, 3,5/2,7/2,1 h.
O que segurava era o dinheiro para pousada, piscina e passeios (os capítulos acabavam no dia 8–9). Mudanças em
`definitions.json`:

| Expansão | Antes | Agora |
|---|---|---|
| Bar do Coqueiro | R$ 1.200 | R$ 900 |
| Pousada | R$ 2.400 | R$ 1.400 |
| Piscina | R$ 2.000 | R$ 1.100 |
| Passeios | R$ 1.800 | R$ 1.000 |

Também entrou a correção do relatório do GPT: a decoração dos negócios (`biz_<id>`) agora vale nas vendas das filas
(`UMareSimulation::BizSaleMult` = nível × decoração), e o modelo faz o mesmo.

Resultado (30 sementes, `tools/ue58/balance/demo/`), dia P10/P50/P90 do `fim_demo` e horas da mediana a 16 min/dia:

| Perfil | Dias | Horas | Na meta 1,5–2,5 h |
|---|---|---|---|
| casual | 9 / 10 / 11 | 2,7 h | 6/30 |
| médio | 7 / 8 / 9 | 2,1 h | 28/30 |
| dedicado | 7 / 7 / 8 | 1,9 h | 30/30 |

Atenção para o jogo completo: com as expansões mais baratas, o Grand Hotel do perfil médio caiu de ~6,7 h para
~5,3 h (abaixo da meta de 6–10 h do Acesso Antecipado). Quando o jogo completo for balanceado, subir o custo do
hotel (hoje R$ 30.000) ou a fama exigida; isso não mexe na demo. O modelo continua sendo uma estimativa: confirmar
jogando a demo do zero e cronometrando.

# Balanceamento — Pacote 2, meta de 6–10 horas até hotel e tela do EA

Referência fixa: **fa49a68b5d8d33fdedde48fd096097f0aac0f267**, branch de origem `codex/ue58-migration`, 06/11/2026. Esta análise atualiza o pacote do PR #7. O PR #7 foi incorporado sem conflitos; o branch gpt/pacote-2 foi atualizado para esta base após três novos commits durante o trabalho. Os arquivos consultados correspondem aos blobs dessa referência; os hashes SHA-256 usados na execução estão em `tools/ue58/balance/pacote2/results/inputs_sha256.json`.

**É um modelo agregado de economia, não um playtest nem a execução do C++ em Python.** O resultado estima a progressão de uma política de jogo explícita. Não comprova que uma pessoa real alcançará o hotel ou a tela de fim em 6–10 horas. Navegação, animações e habilidade precisam ser medidas no executável antes de aplicar as propostas.

## Reproduzir

Na raiz de um checkout com os dados do jogo:

```sh
python tools/ue58/balance_model.py --self-test
python tools/ue58/balance_model.py --days 240 --seeds 30
python tools/ue58/balance_model.py --days 240 --seeds 10 --service-scale 1.25 --out tools/ue58/balance/pacote2/sensitivity_lento
python tools/ue58/balance_model.py --days 240 --seeds 10 --service-scale 0.8 --out tools/ue58/balance/pacote2/sensitivity_rapido
python tools/ue58/balance/report.py
```

Cada cenário usa sementes **0–29**, com limite de 240 dias. O cenário proposto só aplica em memória os JSON Pointers de `balance/proposed.json`; rejeita uma proposta cujo valor atual não coincide com o arquivo lido. Nenhum dado do jogo é escrito. Os dois cenários usam os mesmos números de sementes; escolhas diferentes alteram o consumo posterior do gerador, portanto não são sorteios pareados de cada cliente. É usado `random.Random`, e não o `FRandomStream` da Unreal.

Saídas: `summary.json` (P10/mediana/P90 por marco e censuras), seis CSV diários completos da semente 0, seis CSV por semente, configuração da execução e hashes. Há mais sete dias após a conclusão das compras e da campanha para observar sobra de dinheiro. A tabela diária é uma trajetória reproduzível, não uma média artificial de jogadores com compras incompatíveis entre si.

## Tempo real: diferença entre o pedido e o código

`MareGame.cpp:2861` avança **1 minuto do jogo por segundo real**. Porém `MareSimulation.cpp::Sleep` reinicia às **8h** e `AdvanceMinutes` limita o relógio a 24h. Assim, um dia completo jogado tem **960 segundos = 16 minutos reais**. O primeiro save começa às 6h30, uma diferença inicial de até 1,5 minuto que a aproximação diária não conta. Pausas e tempo com menus pausados também não estão no cálculo.

A coluna de 24 minutos atende à referência pedida para um ciclo de 24h. Ela é **uma conversão alternativa do número de dias**, sem aumentar a produção: as oito horas adicionais não são jogadas pelo código atual. Não tratar essa coluna como medição nem multiplicar a renda por 1,5. O trajeto diário ao morro (hipótese de 180 s) está dentro dos 16 minutos, sem somá-lo novamente ao total.

## Marcos de conclusão

| Marco | Condição usada |
|---|---|
| Grand Hotel | Piscina + passeios, carnaval concluído, fama 9 e R$ 30.000 no cenário atual |
| Tela de fim do EA | Todas as expansões e os quatro capítulos; `MareEvents.cpp:53`, sem exigir negócios ou campanha final |
| Campanha | Todas as missões em ordem; inclui salão, +20 níveis de receita, +40 níveis de decoração equipada, fama 10, 4.000 vendas e festa na noite seguinte |
| Todas as compras finitas | Dez expansões, cinco negócios no nível 3, 25 melhorias do bar, 68 melhorias de receitas e todos os níveis 2–5 dos slots de personalização; contratação de uma pessoa por cargo ativo |

O marco de compras não inclui reposição infinita de estoque, apostas, contratos repetíveis ou uma segunda pessoa opcional por cargo. Quartos, VIPs, fichas, torneios e eventos são operações do conteúdo comprado, não expansões que o jogador compra individualmente. A simulação percorre esses sistemas durante os dias; participar/vencer todos os torneios ou colecionar todos os recordes não define sua parada.

## Fórmulas reais e cobertura

| Sistema | Fonte dos valores | Regra econômica observada e representação |
|---|---|---|
| Quiosque | `definitions.json`, `customization.json`; `MareKioskWorld.cpp:61`, `:209`, `MareSimulation.cpp:240`, `:589` | Intervalo aleatório 18–30 s dividido por conforto/beleza, fama, estação, evento e boca a boca; picos ×1,6. Pedido tem 1 produto e 25% de chance do segundo. Insumo é debitado uma vez; reposição para dez. Receitas afetam preço e peso no cardápio. Capacidade física é hipótese. |
| Fama | `MareSimulation.cpp:374`, `:416` | Limiares extraídos do C++: 0, 100, 250, 450, 700, 1000, 1400, 1900, 2500, 3200. Venda dá 2 XP, mais receita alta e beleza; capítulos +80. Negativos descontam XP até o piso do nível atual; não há regressão de nível. O neon estende o quiosque até pelo menos 21h. |
| Expansões e capítulos | `definitions.json`; `MareSimulation.cpp:277`, `:348`, `:807` | Respeita pré-requisitos, fama, capítulo, pagamentos, entregas e contagem de vendas durante o passo ativo. Compra de negócio não exige pousada. Recompensas não se repetem. |
| Salários e manutenção | `definitions.json/staff_rules`; `MareStaff.cpp:92`, `:140`, `:153`; `MareSimulation.cpp:444`, `:583` | Um empregado por cargo não legado; integral, folga aos domingos (hipótese de escala), XP, reajustes, fadiga/ausências. Funcionário dos negócios é padrão na aquisição. Manutenção: 0,5% dos preços das expansões por dia; hotel tem mais R$ 900 fixos de equipe. |
| Bar | `bar.json`, operações horárias; `MareBar.cpp:170`, `:390` | Receita por bebida + gorjeta/preparo manual; bartender ganha 85%, erra por nível e aprende uma receita a cada dois dias; ingredientes, gelo derretendo, cinco linhas de upgrades. Renda horária genérica do bar existe além dos drinks. Filas/paciência são agregadas. |
| Piscina | `pool.json`; `MarePool.cpp:39`, `:68` | Folhas, toalhas, chuva, limpeza, avaliação e picolés; renda horária × limpeza, conforto, fama, clima e sorteio. Sorveteria produz picolés pagos; cooler tem limite. |
| Pousada e hotel | `customization.json/operations`, `hotel_rooms.json`; `MareStays.cpp:53`, `:82`, `:125`, `:165` | Fila, perfil, limite/oferta, diárias antecipadas por todas as noites, capacidade, check-out, limpeza e ocupação por estado. Hotel tem 2 suítes, 10 luxo, 20 standard; fallback de quarto conforme o código. Receita não é a antiga hipótese de ocupação × diária × 30%. |
| Frigobar e VIP | `hotel_rooms.json`; `MareHotelRooms.cpp:90`, `:150`, `:201` | Consumo sorteado no check-out, cobrança e reposição posterior; reclamações com prazo/custo, um pedido VIP por estadia (a nova entrada limpa vip_asked/vip_done), gorjeta/fama presencial nos três visitáveis. |
| Restaurante e eventos | `restaurant.json`; `MareRestaurant.cpp:109`, `:125`; `MareSimulation.cpp:395` | Seis mesas, serviços, cozinha, room service, equipe a 70% ou garçom a 90%; reservas pagas no dia anterior, receita às 21h por usar `Started == event_hour`. Reserva vencida ao dormir paga na chamada horária do dia seguinte. Refeições noturnas genéricas são fonte separada. Crítico: chance 0,4/h após dia devido, intervalo 3–5 dias, nota arredondada em meios pontos, até três estrelas (+12% cada). Peixe em estoque dá +25% no prato manual de mesa; sem estoque, custo R$ 22; equipe e room service não chamam TakeKitchenFish. |
| Passeios | `tours.json`, `customization.json/operations/tours`; `MareTours.cpp:145`, `:245`, `:284` | Três janelas de procura em grupos, assentos, guia, mar bravo cancela passeios no mar, bilhetes, custo por saída, gorjeta, nota, fotos e boca a boca. Jangada depende de roteiro nível 3. Bilheteria e duração são agregadas por dia. |
| Negócios | `business_games.json`; `MareBusiness.cpp`, `MareBizCommon.cpp`, `MareIceCream.cpp`, `MarePastel.cpp`, `MareRental.cpp`, `MareSouvenir.cpp` | Filas por cliente, funcionário a 60%, sabores/bolas, pastel e caldo, aluguel/devolução/multa/resgate, artesanato e postais com custo, surf por hora, níveis e multiplicadores reais. Não soma renda horária fictícia às quatro filas. |
| Salão | `game_room.json`, `business_games.json`; `MareBusiness.cpp:63`, `MarePoolCup.cpp`, `MareArcade.cpp:208`, `MareGameRoom.cpp:324`, `MareFoosball.cpp`, `MareTableTennis.cpp` | Fichas por ocupação e espectadores, apostas, partidas, duas máquinas dividindo a recompensa do mesmo id por hora, torneio semanal de três rodadas com taxa e prêmios. Desempenho é sorteio por perfil, sem simular física. |
| Lazer, tutorial e humor | `leisure.json`, `tutorial.json`; `MareLeisure.cpp`, `MareSummitWorld.cpp`, `MareComicEvents.cpp` | Pesca/foto fornecem itens/flags de história e fama; dicas são apresentação, não fonte de renda. Visitas narrativas são hipótese. Efeitos pontuais dos eventos cômicos não recebem renda inventada. |
| Montagem na praia | `hotel_events.json`; `MareHotelEvents.cpp:32–120` | Pedido às 9h nos dias pares, aceito para amanhã. Score = peças obrigatórias montadas / total; com score ≥ 0,5, cachê = round(fee × score × (1 + extra_bonus × extras)), fama pela mesma proporção. Abaixo da metade: sinal de 20% e perda de 4 XP. Sem custo de peças no código. |


## Estado dos sistemas solicitados para o Pacote 2

A base recebeu três commits durante a tarefa e foi atualizada antes dos resultados finais. Todos os sistemas abaixo foram encontrados e suas fórmulas revisadas; não se reutilizaram os resultados da referência anterior.

| Recurso solicitado | Presença constatada |
|---|---|
| hotel_events | presente e contemplado |
| fama_negativa | presente e contemplado |
| neon_ate_21 | presente e contemplado |
| aluguel_fecha_tempestade | presente e contemplado |
| aluguel_bonus_mare_alta | presente e contemplado |
| evento_restaurante_ao_dormir | presente e contemplado |
| critic | presente e contemplado |
| fresh_fish | presente e contemplado |

O modelo registra hashes de Source e recusa execução se o snapshot divergir de source_features.json; novos commits exigem revisar as fórmulas antes de renovar o registro.


### Hipóteses dos três perfis

Valores sem telemetria, expostos em `profiles.json` para substituição após teste.

| Perfil | Ações ativas/dia, incluindo morro | Sucesso por etapa | Atende tentativas do quiosque | Evento do hotel a cada | Guia passeio a cada | Chance de vitória |
|---|---|---|---|---|---|---|
| casual | 360 s | 0.5 | 0.65 | 7 dias | 7 dias | 0.35 |
| medio | 600 s | 0.72 | 0.8 | 3 dias | 3 dias | 0.55 |
| dedicado | 840 s | 0.9 | 0.95 | 1 dias | 1 dias | 0.75 |

O restante do dia é deslocamento, observação, espera ou atividades sem receita contada. A equipe atua em paralelo. O orçamento manual é único: quiosque, bar, recepção, minijogos, piscina, partidas e queixas disputam os mesmos segundos. Passeios e campeonato reservam tempo antes das tarefas opcionais. Tempo por ação é hipótese (8–35 s; passeio 120 s; partida de torneio 90 s). O atendente tem capacidade inicial de um produto a cada 11 s, afetada pelo balcão; há sensibilidade abaixo.

Política de investimento: reserva de R$ 100/250/1.200 conforme estágio; cargos elegíveis, expansões na ordem dos dados, negócios baratos e melhorias de menor custo. Melhorias usam até 30% do caixa disponível antes do hotel e 65% depois, com uma etapa por slot por dia. Isso é uma política reproduzível, não a estratégia ótima. O jogador cobra preços de referência e não explora o limite de 200% do preço. Decoração comprada fica equipada no maior nível. Ações narrativas ocorrem ao iniciar/fechar o dia; progressão intradiária é aproximada.

A recepção/limpeza de pousada, chegadas de bar e restaurante e tempos de expiração são discretizados por hora: a fila contínua e a navegação não são reproduzidas. No restaurante, a hipótese de espera é cook_minutes + 20 × (1 − sucesso do perfil), além de 14 s ativos por atendimento. Isso alimenta a gorjeta e a nota do crítico. A ordem horária agrega ações que no jogo ocorrem entre chamadas; não comprova os prazos de atendimento. O crítico também concorre pelo orçamento manual; não há estrela garantida. A preparação do bar usa uma nota média por perfil; gostos, fregueses e tempo exato não são emulados. No passeio não se simulam individualmente todas as opções de extras, golfinhos, colisão no coral ou remarcações; a política cancela mar bravo e usa notas agregadas. A limpeza manual completa de quarto com bônus `polished` não é modelada: a equipe limpa, e o jogador pode resolver queixas nos visitáveis. A probabilidade de responder queixa resume atraso dentro da hora. Estoque do quiosque, bar, frigobar, artesanato, postais e picolés têm desembolsos próprios; **não se inventou CMV de pastel ou casquinha**. O restaurante agora cobra peixe do fornecedor somente no pedido manual de mesa sem peixe em estoque, exatamente onde TakeKitchenFish é chamado. O modelo conserva a origem indiferenciada de stock.peixe, inclusive peixe comprado. Na montagem, 6 s por peça e até 2/8/10 peças por hora nos perfis casual/médio/dedicado são hipóteses; montar com E não tem chance de erro. Ofertas são aceitas com a probabilidade de engajamento do perfil. As peças prioritárias disputam o orçamento do dia antes das atividades opcionais; extras só depois das obrigatórias. Congressos às 10h deixam uma janela curta após acordar às 8h.

## Resultado atual: 30 sementes por perfil

| Perfil | Marco | Dia P10 / P50 / P90 | P50 a 16 min/dia | P50 a 24 min/dia | Concluíram |
|---|---|---|---|---|---|
| casual | Grand Hotel | 27 / 30 / 31 | 8.0 h | 12.0 h | 30/30 |
| casual | Tela de fim do EA | 28 / 31 / 32 | 8.3 h | 12.4 h | 30/30 |
| casual | Campanha | 54 / 55 / 56 | 14.7 h | 22.0 h | 30/30 |
| casual | Todas as compras finitas | 54.9 / 56 / 58 | 14.9 h | 22.4 h | 30/30 |
| medio | Grand Hotel | 24 / 25 / 27 | 6.7 h | 10.0 h | 30/30 |
| medio | Tela de fim do EA | 25 / 26 / 28 | 6.9 h | 10.4 h | 30/30 |
| medio | Campanha | 47 / 48 / 49 | 12.8 h | 19.2 h | 30/30 |
| medio | Todas as compras finitas | 49 / 51 / 52 | 13.6 h | 20.4 h | 30/30 |
| dedicado | Grand Hotel | 20 / 22 / 23 | 5.9 h | 8.8 h | 30/30 |
| dedicado | Tela de fim do EA | 21 / 23 / 24 | 6.1 h | 9.2 h | 30/30 |
| dedicado | Campanha | 41 / 42 / 43 | 11.2 h | 16.8 h | 30/30 |
| dedicado | Todas as compras finitas | 43 / 45 / 45.1 | 12.0 h | 18.0 h | 30/30 |

### Sementes na meta de 6–10 h (16 min/dia)

| Cenário | Perfil | Grand Hotel | Tela do EA |
|---|---|---|---|
| atual | casual | 30/30 | 30/30 |
| atual | medio | 30/30 | 30/30 |
| atual | dedicado | 9/30 | 22/30 |
| proposto | casual | 30/30 | 30/30 |
| proposto | medio | 29/30 | 30/30 |
| proposto | dedicado | 2/30 | 9/30 |

A meta deste pacote é **6–10 horas até Grand Hotel e tela do EA**, não até a última missão da campanha ou a compra de todas as melhorias. A coluna efetiva usa 16 minutos, confirmados no código. A duração de campanha aparece como informação complementar. Comprar o catálogo inteiro e concluir a campanha podem ocorrer em ordem diferente; não publicar uma duração na loja com base só neste modelo.

## Quando as expansões ficam disponíveis e são compradas

Disponível = pré-requisitos/fama/capítulo alcançados; comprada = pagou mantendo reserva e a política de compras. São medianas em dias, não datas prometidas. Uma cadeia pode ficar disponível na mesma rodada de compras do fechamento.

### Cenário atual

| Expansão | Casual: disponível → comprada | Médio: disponível → comprada | Dedicado: disponível → comprada |
|---|---|---|---|
| Mesas e guarda-sóis | 1 → 1 | 1 → 1 | 1 → 1 |
| Licença de drinks | 1 → 2 | 1 → 2 | 1 → 1 |
| Letreiro neon | 1 → 2 | 1 → 2 | 1 → 2 |
| Chapa de petiscos | 1 → 3 | 1 → 2 | 1 → 2 |
| Bar do Coqueiro | 3 → 4 | 2 → 4 | 2 → 4 |
| Pousada: recepção + bangalô | 4 → 9.5 | 4 → 8 | 4 → 6 |
| Piscina | 9.5 → 11 | 8 → 9 | 6 → 7 |
| Passeios turísticos | 9.5 → 12 | 8 → 10 | 6 → 8 |
| Grand Hotel Maré Alta 5★ | 17 → 30 | 13 → 25 | 11 → 22 |
| Salão de jogos do hotel | 30 → 31 | 25 → 26 | 22 → 23 |

### Cenário proposto

| Expansão | Casual: disponível → comprada | Médio: disponível → comprada | Dedicado: disponível → comprada |
|---|---|---|---|
| Mesas e guarda-sóis | 1 → 1 | 1 → 1 | 1 → 1 |
| Licença de drinks | 1 → 2 | 1 → 2 | 1 → 1 |
| Letreiro neon | 1 → 2 | 1 → 2 | 1 → 2 |
| Chapa de petiscos | 1 → 3 | 1 → 2 | 1 → 2 |
| Bar do Coqueiro | 3 → 4 | 2 → 4 | 2 → 4 |
| Pousada: recepção + bangalô | 4 → 9.5 | 4 → 8 | 4 → 6 |
| Piscina | 9.5 → 11 | 8 → 9 | 6 → 7 |
| Passeios turísticos | 9.5 → 12 | 8 → 10 | 6 → 8 |
| Grand Hotel Maré Alta 5★ | 17 → 27 | 13 → 24 | 11 → 20 |
| Salão de jogos do hotel | 27 → 28 | 24 → 25 | 20 → 21 |

## Capítulos, negócios e experiências observadas

| Marco atual: dia mediano (execuções que atingiram) | Casual | Médio | Dedicado |
|---|---|---|---|
| capitulo:pier | 1 (30/30) | 1 (30/30) | 1 (30/30) |
| capitulo:prainha | 3 (30/30) | 2 (30/30) | 2 (30/30) |
| capitulo:sabores | 9 (30/30) | 8 (30/30) | 7 (30/30) |
| capitulo:carnaval | 9 (30/30) | 8.5 (30/30) | 8 (30/30) |
| negocio:aluguel | 7.5 (30/30) | 6 (30/30) | 5.5 (30/30) |
| negocio:food_truck | 12 (30/30) | 11 (30/30) | 9 (30/30) |
| negocio:sorveteria | 5 (30/30) | 4 (30/30) | 4 (30/30) |
| negocio:souvenir | 10 (30/30) | 10 (30/30) | 9 (30/30) |
| negocio:surfe | 13 (30/30) | 12 (30/30) | 10 (30/30) |
| bar_secreto | 8 (29/30) | 5 (30/30) | 5 (30/30) |
| passeio:jangada | 31 (30/30) | 29 (30/30) | 25 (30/30) |
| vip_hotel_atendido | 31 (30/30) | 26 (30/30) | 23 (30/30) |
| evento:formatura | 50 (30/30) | 34 (30/30) | 25 (30/30) |
| evento:bodas | 36 (30/30) | 28 (30/30) | 23 (30/30) |
| evento:empresa | 43 (30/30) | 31 (30/30) | 24 (30/30) |
| montagem:casamento | 37 (30/30) | 31 (30/30) | 27 (30/30) |
| montagem:aniversario | 35 (29/30) | 33 (30/30) | 27 (30/30) |
| montagem:congresso | 43 (29/30) | 29 (30/30) | 31 (30/30) |
| critico_atendido | 31 (30/30) | 26 (30/30) | 23 (30/30) |
| estrela_restaurante:1 | não observado | não observado | 48.5 (2/30) |
| estrela_restaurante:3 | não observado | não observado | não observado |
| campeonato_inscrito | 40 (28/30) | 29 (30/30) | 29 (30/30) |
| fliperamas_jogados | não observado | não observado | não observado |

Medianas de experiências só usam quem as viveu; a contagem evita transformar uma experiência opcional rara em uma conclusão garantida.

## Renda dominante, retorno e paredes

A tabela abaixo descreve a **semente 0 do médio**. Receita é entrada de caixa, portanto diárias incluem antecipação de várias noites; não confundir com lucro por competência. Fase pós-hotel começa no dia seguinte à compra; os sete dias finais permitem observar a renda depois das compras.

### Renda por fase — atual

| Fase | Dias amostrados | Receita média/dia (R$) | Saldo antes de investimentos/dia (R$) | Quatro maiores parcelas da receita |
|---|---|---|---|---|
| Antes do hotel | 24 | 5.782 | 4.624 | quiosque: 28%, passeios: 15%, bar_drinks: 11%, bar_passivo: 11% |
| Hotel até todas as compras | 26 | 42.469 | 38.539 | hotel_diarias: 30%, passeios: 13%, quiosque: 11%, hotel_refeicoes_noturnas: 7% |
| Após todas as compras | 6 | 59.244 | 55.066 | hotel_diarias: 36%, passeios: 11%, quiosque: 9%, hotel_refeicoes_noturnas: 8% |

Maior intervalo sem compra antes de completar o catálogo: **nenhum** (0 dias). Depois do catálogo, caixa passou de **R$ 68.550** para **R$ 398.945** no dia 56. Isso revela ausência de uso finito adicional do dinheiro; receita diária continua entrando.

### Renda por fase — proposto

| Fase | Dias amostrados | Receita média/dia (R$) | Saldo antes de investimentos/dia (R$) | Quatro maiores parcelas da receita |
|---|---|---|---|---|
| Antes do hotel | 23 | 5.504 | 4.406 | quiosque: 28%, passeios: 14%, bar_drinks: 11%, bar_passivo: 11% |
| Hotel até todas as compras | 24 | 42.169 | 38.167 | hotel_diarias: 30%, passeios: 13%, quiosque: 11%, hotel_refeicoes_noturnas: 7% |
| Após todas as compras | 6 | 60.096 | 56.091 | hotel_diarias: 33%, passeios: 13%, quiosque: 9%, hotel_refeicoes_noturnas: 9% |

Maior intervalo sem compra antes de completar o catálogo: **nenhum** (0 dias). Depois do catálogo, caixa passou de **R$ 73.560** para **R$ 410.103** no dia 53. Isso revela ausência de uso finito adicional do dinheiro; receita diária continua entrando.


- **Contratos passivos foram moderados na base nova:** bodas custa 1.200 e paga 3.200 (saldo base 2.000), formatura 600 → 1.600 (saldo 1.000), empresa 900 → 2.400 (saldo 1.500). A decoração ainda multiplica a receita. Os eventos montados são separados: casamento paga até 5.600 com quatro extras no estado atual, mas só há oferta a cada dois dias e é preciso montar; não contar esse cachê como receita diária garantida.
- **Peixe e crítico têm retorno condicionado:** pescado/estoque melhora pratos de mesa atendidos manualmente; a automação não recebe esse bônus e pode evitar o custo do peixe. Estrelas sobem o menu, não o cachê dos contratos. Um jogador focado em outras fontes pode deixar todos os críticos com a equipe e nunca ganhar estrela.
- **Aluguel:** tempestade bloqueia novas chegadas, preservando devoluções; maré alta multiplica chegadas por 1,4 antes do limite da fila, sem aumentar RentalPrice. Isso favorece ter capacidade de atendimento em vez de contar um bônus no preço.
- **Hotel acelera a economia:** o pagamento antecipado multiplica o efeito das primeiras chegadas; decoração aumenta a diária e as receitas. Não usar um modelo de ocupação passiva de 45% × 30% da receita: ele subestimava esse fluxo. O caixa pode crescer antes de a campanha de vendas terminar.
- **Passeios e bar ficam competitivos com decoração:** as fórmulas multiplicam preço/renda, e o bar também tem receita genérica por hora. Verificar se o desejo de design é manter ambos os fluxos, sem excluir silenciosamente um deles do simulador.
- **Negócios com fila não usam `definitions.businesses.<id>.hour` para precificar cada casquinha/pastel/aluguel/artesanato.** O retorno vem de seus próprios pedidos. A decoração de `biz_*` que só muda `BusinessRate` não se transfere automaticamente às vendas das quatro filas: tende a oferecer retorno monetário menor do que seu painel sugere. O surfe continua usando essa taxa.
- **Banquetas do bar:** os níveis altos aumentam paciência, mas o array de assentos extra estabiliza em 2. O retorno marginal não equivale a abrir duas novas vagas a cada nível.
- **Salão é variedade, não motor de riqueza:** fichas e prêmios são pequenos diante das diárias e dos eventos. Torneio tem taxa e chance de eliminação; não contar 600 de prêmio diário ou uma vitória certa. Os dois fliperamas compartilham o bloqueio de recompensa por hora do id `fliperama`.
- **Parede de expansão não é necessariamente dia sem compra:** mesmo antes do hotel há receitas, decoração e níveis de negócios compráveis. A tabela diária mostra esse preenchimento. Depois de terminar as compras, manter milhares de vendas como requisito pode virar uma cauda de espera com caixa sem finalidade.

## Sensibilidade: capacidade do atendente ainda não medida

Mesmo número de dias de operação; varia apenas a hipótese de segundos por produto do funcionário, não o relógio nem os preços. Dez sementes 0–9 em cada extremo. As séries de sensibilidade guardam a configuração exata em seus diretórios.

| Hipótese de capacidade | Cenário | Dia mediano da campanha | 16 min/dia | 24 min/dia |
|---|---|---|---|---|
| 8,8 s/produto | atual | 42.5 | 11.3 h | 17.0 h |
| 8,8 s/produto | proposto | 42.5 | 11.3 h | 17.0 h |
| 11 s/produto | atual | 48 | 12.8 h | 19.2 h |
| 11 s/produto | proposto | 48 | 12.8 h | 19.2 h |
| 13,75 s/produto | atual | 54 | 14.4 h | 21.6 h |
| 13,75 s/produto | proposto | 54 | 14.4 h | 21.6 h |

A variação de habilidade e deslocamento pode ser maior que a variação entre sementes. Antes de aceitar os números propostos, medir pelo menos três sessões completas do perfil médio: tempo por produto, vendas/dia, tempo fora do quiosque, partidas e ocupação. Registrar também quando o jogador dorme mais cedo. Aumentar o número de sementes não corrige uma hipótese errada de capacidade.

## Tabelas dia a dia

Valores em R$, arredondados nesta apresentação. **Q** quiosque; **VQ** VIP do quiosque; **B** drinks; **BH** bar por hora; **P** pousada; **H** diárias do hotel; **HN** refeições noturnas; **M** frigobar; **VH** VIP hotel; **R** restaurante; **E** jantares/contratos do restaurante; **EM** eventos montados na praia; **T** passeios; **F** fotos; **PL** piscina; **PI** picolés; **I** sorveteria; **PA** pastel; **AL** aluguel; **S** souvenir; **SU** surfe; **FI** fichas; **PE** pebolim; **AR** fliperama; **AP** partidas/apostas recebidas; **CP** campeonato; **RE** recompensas. Fonte ausente na célula = zero, não desconhecida.

Salários incluem equipe contratada, funcionários dos negócios e R$ 900 da equipe fixa do hotel. Estoque reúne todos os desembolsos com prefixo `estoque_`. Outras despesas incluem manutenção, passeios, queixas, preparativos e taxas/perdas em partidas. Investimentos são as aquisições finitas. O CSV preserva cada categoria, centavos, caixa inicial, evento, chuva, ocupação, vendas acumuladas, todas as compras e as expansões que eram compráveis antes de gastar no fechamento. Como as células são arredondadas, a conciliação exata deve usar o CSV.

### Atual — casual, semente 0

[CSV diário completo](../../tools/ue58/balance/pacote2/results/atual_casual_diario_seed0.csv).

| Dia | Renda por fonte | Salários | Estoque | Outras saídas | Investimento | Caixa final | Nível / XP | Compras / expansões compráveis |
|---|---|---|---|---|---|---|---|---|
| 1 | RE 370, Q 274 | 0 | 126 | 150 | 240 | 278 | 2 / 118.0 | equipe:atendente; podia: drinks; kiosk_tables |
| 2 | RE 280, Q 410, VQ 19 | 30 | 111 | 0 | 440 | 406 | 2 / 216.0 | kiosk_tables, drinks; podia: drinks; kiosk_tables |
| 3 | RE 300, Q 548, VQ 29 | 32 | 245 | 2 | 593 | 411 | 3 / 382.0 | neon, grill + 1 melhorias; podia: grill; neon |
| 4 | RE 550, Q 1.070, VQ 76 | 32 | 465 | 5 | 1.200 | 405 | 4 / 532.0 | bar; podia: bar |
| 5 | Q 849, B 131, BH 382, VQ 11 | 32 | 380 | 11 | 485 | 870 | 4 / 681.0 | equipe:bartender + 3 melhorias |
| 6 | Q 689, B 301, BH 285, VQ 34 | 77 | 304 | 11 | 1.076 | 711 | 5 / 802.0 | negocio:sorveteria + 2 melhorias |
| 7 | Q 818, B 78, BH 392, I 196, VQ 57 | 117 | 229 | 11 | 1.400 | 495 | 5 / 946.0 | negocio:aluguel |
| 8 | Q 591, AL 356, B 459, BH 469, I 222, VQ 21 | 165 | 316 | 131 | 497 | 1.503 | 6 / 1049.0 | 5 melhorias |
| 9 | RE 1.100, Q 1.091, AL 57, B 425, BH 274, I 109, VQ 67 | 165 | 551 | 661 | 2.400 | 849 | 6 / 1368.0 | pousada; podia: pousada |
| 10 | RE 1.100, Q 858, AL 401, B 446, BH 485, I 336, VQ 56 | 165 | 386 | 143 | 2.460 | 1.377 | 7 / 1502.0 | equipe:camareira, equipe:recepcionista, pool; podia: passeios; pool |
| 11 | Q 1.163, AL 228, B 430, BH 478, PI 10, PL 164, P 461, I 186, VQ 39 | 241 | 481 | 33 | 2.370 | 1.411 | 7 / 1674.0 | equipe:piscineiro, passeios + 3 melhorias; podia: passeios |
| 12 | Q 956, AL 270, B 526, BH 505, PL 225, P 248, I 178, VQ 74 | 277 | 390 | 162 | 2.306 | 1.258 | 7 / 1835.0 | equipe:guia, negocio:souvenir + 3 melhorias |
| 13 | Q 1.147, AL 291, B 555, BH 492, T 960, PL 219, P 804, I 198, S 580, VQ 59 | 364 | 720 | 242 | 4.294 | 943 | 8 / 2017.0 | negocio:food_truck, negocio:surfe + 2 melhorias |
| 14 | Q 1.211, AL 207, BH 414, PA 178, T 396, PL 160, I 141, S 665, SU 217, VQ 147 | 469 | 494 | 67 | 900 | 2.748 | 8 / 2214.0 | 6 melhorias |
| 15 | Q 901, AL 213, B 567, BH 535, PA 136, T 935, PL 224, P 692, I 147, S 557, SU 350, VQ 43 | 473 | 496 | 242 | 1.961 | 4.876 | 8 / 2353.0 | 12 melhorias |
| 16 | Q 1.352, AL 227, B 714, BH 586, PA 294, T 1.190, PL 246, P 452, I 175, S 647, SU 289, VQ 140 | 478 | 794 | 122 | 2.812 | 6.981 | 9 / 2556.0 | 15 melhorias |
| 17 | Q 1.235, AL 397, B 691, BH 631, PA 188, T 1.270, PL 309, P 650, I 411, S 627, SU 370, VQ 70 | 484 | 750 | 242 | 3.631 | 8.723 | 9 / 2754.0 | 16 melhorias |
| 18 | Q 1.733, AL 279, B 990, BH 735, PA 411, T 1.305, PL 324, I 192, S 517, SU 449, VQ 93 | 487 | 746 | 122 | 4.236 | 10.160 | 9 / 2979.0 | 15 melhorias |
| 19 | Q 1.295, AL 230, B 1.223, BH 895, PA 194, F 150, T 1.644, PL 354, P 695, I 169, S 595, SU 413, VQ 94 | 490 | 584 | 242 | 4.838 | 11.957 | 10 / 3228.0 | 14 melhorias |
| 20 | Q 2.018, AL 191, B 1.356, BH 980, PA 313, F 135, T 1.556, PI 30, PL 394, P 190, I 168, S 629, SU 499, VQ 60 | 490 | 934 | 242 | 5.295 | 13.516 | 10 / 3540.0 | 14 melhorias |
| 21 | Q 1.900, AL 206, BH 940, PA 174, F 45, T 461, PL 285, I 133, S 641, SU 390, VQ 110 | 490 | 618 | 67 | 5.040 | 12.585 | 10 / 3830.0 | 12 melhorias |
| 22 | Q 1.703, AL 273, B 1.223, BH 1.105, PA 174, F 120, T 1.648, PL 432, P 436, I 208, S 587, SU 521, VQ 44 | 496 | 738 | 242 | 5.600 | 13.982 | 10 / 4075.0 | 12 melhorias |
| 23 | Q 2.400, AL 48, B 1.475, BH 676, PA 236, F 105, T 1.567, PL 291, I 47, S 647, SU 251, VQ 224 | 498 | 796 | 122 | 5.904 | 14.629 | 10 / 4422.0 | 11 melhorias |
| 24 | Q 1.970, AL 289, B 1.481, BH 1.315, PA 206, F 150, T 1.965, PL 536, P 719, I 242, S 588, SU 560, VQ 74 | 502 | 762 | 242 | 6.410 | 16.807 | 10 / 4698.0 | 11 melhorias |
| 25 | Q 2.254, AL 278, B 1.399, BH 1.261, PA 263, F 225, T 2.043, PL 478, P 146, I 143, S 543, SU 648, VQ 55 | 502 | 734 | 122 | 7.390 | 17.795 | 10 / 5001.0 | 11 melhorias |
| 26 | Q 2.134, AL 190, B 1.925, BH 1.360, PA 173, F 250, T 2.565, PI 20, PL 505, P 1.011, I 187, S 593, SU 562, VQ 106 | 505 | 796 | 242 | 7.490 | 20.343 | 10 / 5315.0 | 10 melhorias |
| 27 | RE 1.000, Q 2.530, AL 270, B 2.093, BH 1.500, PA 404, F 225, T 2.733, PL 541, P 918, I 186, S 615, SU 474, VQ 94 | 505 | 802 | 242 | 30.000 | 2.376 | 10 / 5645.0 | grand_hotel; podia: grand_hotel |
| 28 | RE 3.500, Q 2.505, AL 90, BH 787, PA 95, F 125, M 46, H 4.846, HN 417, T 926, PL 246, R 809, I 59, S 621, SU 200, VQ 234 | 1.405 | 688 | 1.622 | 8.480 | 5.686 | 10 / 5970.0 | equipe:garcom_hotel, salao_jogos + 2 melhorias; podia: salao_jogos |
| 29 | Q 2.151, AL 346, B 1.945, BH 1.514, E 3.200, FI 101, PA 172, F 250, M 153, H 8.972, HN 773, EM 800, T 2.575, PL 488, P 167, R 1.106, I 307, S 564, SU 512, VQ 27 | 1.453 | 694 | 934 | 17.270 | 11.458 | 10 / 6281.0 | 20 melhorias |
| 30 | Q 2.816, AL 234, B 2.036, BH 1.585, FI 411, PA 390, F 250, M 526, H 8.099, HN 933, T 2.693, PL 566, P 1.524, R 1.039, I 196, S 637, SU 742, VQ 102 | 1.457 | 862 | 994 | 19.810 | 13.116 | 10 / 6686.0 | 20 melhorias |
| 31 | Q 2.747, AL 335, B 2.196, BH 1.686, FI 120, PA 212, F 325, M 479, H 10.137, HN 1.254, T 3.834, PI 98, PL 640, R 1.234, I 151, S 582, SU 723, VQ 246 | 1.463 | 980 | 814 | 22.455 | 14.403 | 10 / 7096.0 | 19 melhorias |
| 32 | Q 3.669, AL 168, B 2.357, BH 1.718, FI 125, PA 368, F 325, M 128, H 14.384, HN 1.861, T 4.118, PL 653, P 1.287, R 1.780, I 238, S 577, SU 655, VQ 371 | 1.466 | 1.096 | 994 | 28.110 | 17.518 | 10 / 7630.0 | 21 melhorias |
| 33 | Q 2.454, AL 502, B 2.365, BH 1.711, FI 148, PA 185, F 120, M 856, H 9.637, HN 1.861, T 664, PI 53, PL 664, R 1.260, I 216, S 534, SU 869, VQ 230 | 1.473 | 620 | 854 | 23.415 | 15.487 | 10 / 8041.0 | 15 melhorias |
| 34 | Q 3.989, AL 265, B 2.666, BH 1.874, FI 143, PA 539, F 560, M 421, H 7.578, HN 2.234, T 5.206, PL 624, P 1.929, R 1.772, I 200, S 800, SU 760, VQ 190 | 1.473 | 1.276 | 754 | 26.540 | 17.192 | 10 / 8544.0 | 15 melhorias |
| 35 | Q 3.767, AL 365, BH 1.676, FI 141, PA 214, F 120, M 834, H 9.256, HN 2.137, T 847, PL 463, R 1.751, I 216, S 805, SU 618, VQ 166 | 1.473 | 874 | 1.389 | 22.600 | 14.232 | 10 / 9008.0 | 12 melhorias |
| 36 | Q 3.495, AL 460, B 2.643, BH 2.028, E 3.696, FI 145, PA 240, F 120, M 504, H 9.846, HN 2.234, T 846, PL 657, P 975, R 1.405, I 277, S 698, SU 1.033, VQ 222 | 1.473 | 1.060 | 554 | 25.200 | 17.470 | 10 / 9467.0 | 12 melhorias |
| 37 | Q 4.517, AL 97, B 2.970, BH 1.294, FI 377, PA 244, F 520, M 525, H 7.715, HN 2.331, T 5.138, PL 465, P 1.697, R 1.728, I 73, S 832, SU 347, VQ 169 | 1.473 | 1.066 | 819 | 27.085 | 18.066 | 10 / 9965.0 | 12 melhorias |
| 38 | Q 3.586, AL 598, B 3.029, BH 2.112, FI 156, PA 258, F 120, M 616, H 13.532, HN 2.470, T 800, PI 98, PL 799, R 1.760, I 206, S 626, SU 1.010, VQ 218 | 1.473 | 970 | 764 | 28.740 | 18.114 | 10 / 10385.0 | 11 melhorias |
| 39 | Q 4.753, AL 290, B 2.740, BH 2.165, FI 155, PA 570, F 520, M 694, H 10.257, HN 2.582, T 5.844, PL 816, P 1.953, R 2.139, I 276, S 705, SU 912, VQ 332 | 1.477 | 1.136 | 684 | 31.040 | 21.480 | 10 / 10912.0 | 11 melhorias |
| 40 | Q 1.860, B 3.145, BH 1.393, FI 161, PA 186, F 120, M 268, H 12.007, HN 2.996, T 728, PL 498, P 572, R 1.483, I 206, S 631, SU 591 | 1.477 | 772 | 1.024 | 27.880 | 17.172 | 10 / 11158.0 | 9 melhorias |
| 41 | Q 4.606, AL 73, B 3.110, BH 1.498, FI 145, PA 336, F 840, M 538, H 6.682, HN 2.277, EM 300, T 6.268, PL 489, R 1.946, I 184, S 897, SU 478, VQ 98 | 1.477 | 914 | 924 | 27.960 | 16.664 | 10 / 11669.0 | 8 melhorias |
| 42 | Q 4.768, AL 398, BH 2.091, FI 123, PA 268, F 300, M 494, H 9.183, HN 2.755, T 1.606, PI 105, PL 605, R 2.836, I 412, S 937, SU 944, VQ 189 | 1.477 | 974 | 1.439 | 25.880 | 14.908 | 10 / 12146.0 | 7 melhorias |
| 43 | Q 5.047, AL 356, B 3.294, BH 2.558, E 3.328, FI 131, PA 335, F 900, M 464, H 13.706, HN 3.465, EM 300, T 7.407, PL 829, P 4.550, R 2.347, I 377, S 784, SU 1.512, VQ 150 | 1.477 | 1.076 | 1.209 | 39.900 | 23.085 | 10 / 12663.0 | 9 melhorias |
| 44 | Q 5.032, AL 521, B 3.010, BH 2.640, FI 407, PA 651, F 960, M 539, H 9.528, HN 2.634, T 8.278, PI 73, PL 962, R 1.875, I 287, S 887, SU 1.164, VQ 262 | 1.477 | 992 | 874 | 36.460 | 22.992 | 10 / 13206.0 | 7 melhorias |
| 45 | Q 4.790, AL 446, B 3.857, BH 2.494, FI 150, PA 379, F 960, M 458, H 13.872, HN 2.786, T 7.763, PL 910, R 2.502, I 467, S 796, SU 1.707, VQ 170 | 1.477 | 1.072 | 919 | 36.800 | 27.232 | 10 / 13717.0 | 6 melhorias |
| 46 | Q 5.284, AL 318, B 3.605, BH 2.500, FI 154, PA 595, F 960, M 380, H 15.036, HN 3.247, T 8.574, PL 870, P 1.604, R 2.563, I 402, S 894, SU 1.224, VQ 166 | 1.477 | 1.020 | 904 | 43.000 | 29.207 | 10 / 14230.0 | 6 melhorias |
| 47 | Q 4.696, AL 543, B 3.642, BH 2.500, FI 130, PA 378, F 960, M 626, H 20.902, HN 3.415, EM 800, T 9.060, PL 928, P 1.108, R 2.691, I 830, S 817, SU 1.510, VQ 285 | 1.477 | 1.002 | 959 | 43.500 | 38.089 | 10 / 14746.0 | 5 melhorias |
| 48 | Q 4.805, AL 441, B 3.612, BH 2.577, FI 163, PA 521, F 1.020, M 194, H 22.774, HN 4.967, T 9.464, PL 888, P 1.178, R 3.179, I 443, S 955, SU 1.172, VQ 183 | 1.480 | 1.150 | 1.344 | 55.100 | 37.551 | 10 / 15283.0 | 5 melhorias |
| 49 | Q 4.651, AL 266, BH 2.132, FI 154, PA 332, F 300, M 903, H 6.871, HN 4.425, EM 300, T 2.093, PL 688, R 1.915, I 370, S 958, SU 1.161, VQ 578 | 1.480 | 764 | 1.894 | 38.100 | 23.410 | 10 / 15802.0 | 3 melhorias |
| 50 | Q 2.730, B 3.242, BH 1.525, E 9.152, FI 145, PA 256, F 180, M 403, H 6.257, HN 4.618, T 1.206, PL 483, P 2.811, R 3.149, I 183, S 852, SU 795, VQ 114 | 1.480 | 924 | 514 | 29.000 | 29.592 | 10 / 16115.0 | 2 melhorias |
| 51 | Q 4.983, AL 375, B 3.595, BH 2.619, FI 389, PA 621, F 960, M 453, H 16.779, HN 4.016, T 8.734, PI 73, PL 913, P 1.912, R 3.244, I 395, S 941, SU 1.182, VQ 424 | 1.480 | 946 | 894 | 45.000 | 33.880 | 10 / 16667.0 | 3 melhorias |
| 52 | Q 5.074, AL 532, B 3.512, BH 2.490, FI 152, PA 348, F 1.020, M 415, H 19.508, HN 3.557, T 9.714, PL 931, P 471, R 2.852, I 312, S 826, SU 1.309, VQ 264 | 1.480 | 1.206 | 774 | 36.000 | 47.707 | 10 / 17196.0 | 2 melhorias |
| 53 | Q 4.927, AL 79, B 3.555, BH 1.589, FI 134, PA 428, F 960, M 555, H 15.421, HN 3.772, EM 500, T 8.792, PL 562, P 3.482, R 3.614, I 182, S 1.001, SU 454, VQ 132 | 1.480 | 1.002 | 879 | 40.500 | 53.985 | 10 / 17729.0 | 2 melhorias |
| 54 | RE 1.500, Q 4.756, AL 467, B 3.513, BH 2.499, FI 150, PA 307, F 960, M 390, H 22.921, HN 4.430, T 9.580, PI 73, PL 901, P 1.988, R 3.119, I 463, S 886, SU 1.413, VQ 319 | 1.480 | 1.144 | 1.054 | 70.500 | 40.442 | 10 / 18269.0 | 3 melhorias |
| 55 | RE 1.000, Q 5.089, AL 464, B 3.151, BH 2.667, FI 144, PA 599, F 960, M 322, H 20.505, HN 5.362, EM 300, T 8.715, PL 924, P 898, R 3.260, I 290, S 956, SU 1.137, VQ 130 | 1.480 | 932 | 904 | 57.000 | 36.999 | 10 / 18761.0 | 2 melhorias |
| 56 | Q 4.733, AL 290, BH 2.141, FI 156, PA 284, F 360, M 543, H 16.271, HN 4.663, T 2.284, PL 646, R 4.460, I 360, S 963, SU 1.150, VQ 501 | 1.480 | 898 | 2.019 | 0 | 72.407 | 10 / 19293.0 | — |
| 57 | Q 5.507, AL 135, B 3.009, BH 1.541, E 10.112, FI 142, PA 146, F 1.020, M 325, H 26.804, HN 5.129, T 8.984, PL 460, P 2.048, R 3.192, I 131, S 811, SU 541, VQ 410 | 1.480 | 1.058 | 744 | 0 | 139.572 | 10 / 19856.0 | — |
| 58 | Q 4.984, AL 587, B 3.716, BH 2.640, FI 401, PA 608, F 1.020, M 570, H 22.403, HN 5.829, T 9.675, PL 921, P 1.922, R 3.721, I 404, S 811, SU 1.106, VQ 161 | 1.480 | 940 | 854 | 0 | 197.777 | 10 / 20399.0 | — |
| 59 | Q 4.757, AL 400, B 3.687, BH 2.598, FI 141, PA 328, F 1.020, M 539, H 8.428, HN 3.730, EM 300, T 9.023, PL 927, R 2.503, I 512, S 884, SU 1.249, VQ 158 | 1.480 | 1.116 | 969 | 0 | 235.395 | 10 / 20910.0 | — |
| 60 | Q 5.071, AL 370, B 3.594, BH 2.558, FI 137, PA 631, F 1.020, M 615, H 30.278, HN 4.896, T 9.464, PI 36, PL 923, P 2.840, R 3.218, I 407, S 894, SU 1.170, VQ 37 | 1.480 | 1.156 | 704 | 0 | 300.215 | 10 / 21412.0 | — |
| 61 | Q 4.994, AL 330, B 3.777, BH 2.547, FI 141, PA 321, F 960, M 286, H 29.725, HN 5.595, EM 500, T 9.137, PI 146, PL 926, P 2.028, R 4.154, I 382, S 911, SU 1.389, VQ 296 | 1.480 | 1.050 | 1.294 | 0 | 364.936 | 10 / 21969.0 | — |

### Atual — medio, semente 0

[CSV diário completo](../../tools/ue58/balance/pacote2/results/atual_medio_diario_seed0.csv).

| Dia | Renda por fonte | Salários | Estoque | Outras saídas | Investimento | Caixa final | Nível / XP | Compras / expansões compráveis |
|---|---|---|---|---|---|---|---|---|
| 1 | RE 530, Q 464 | 0 | 118 | 150 | 570 | 306 | 2 / 138.0 | equipe:atendente, kiosk_tables, neon; podia: drinks; kiosk_tables |
| 2 | RE 420, Q 830, VQ 53 | 30 | 295 | 2 | 778 | 504 | 3 / 356.0 | drinks, grill + 2 melhorias; podia: drinks; grill |
| 3 | Q 977, VQ 130 | 32 | 523 | 5 | 900 | 150 | 4 / 524.0 | negocio:sorveteria |
| 4 | RE 550, Q 1.089, I 302, VQ 32 | 72 | 521 | 5 | 1.200 | 325 | 5 / 703.0 | bar; podia: bar |
| 5 | Q 1.054, B 14, BH 402, I 412, VQ 16 | 72 | 244 | 11 | 674 | 1.222 | 5 / 886.0 | equipe:bartender + 5 melhorias |
| 6 | RE 300, Q 1.032, B 311, BH 449, I 233, VQ 40 | 117 | 478 | 11 | 2.400 | 582 | 6 / 1088.0 | pousada; podia: pousada |
| 7 | Q 1.119, B 153, BH 395, I 315, VQ 35 | 117 | 458 | 23 | 756 | 1.244 | 6 / 1285.0 | equipe:camareira, equipe:recepcionista + 3 melhorias; podia: passeios; pool |
| 8 | RE 1.100, Q 1.179, B 428, BH 458, P 480, I 272, VQ 78 | 190 | 497 | 393 | 2.358 | 1.802 | 7 / 1553.0 | pool + 3 melhorias; podia: passeios; pool |
| 9 | Q 1.338, B 418, BH 475, PI 10, PL 173, P 343, I 256, VQ 54 | 196 | 608 | 33 | 3.400 | 632 | 7 / 1770.0 | equipe:piscineiro, passeios, negocio:aluguel; podia: passeios |
| 10 | RE 800, Q 1.136, AL 249, B 356, BH 485, PI 80, PL 237, P 218, I 242, VQ 120 | 271 | 405 | 562 | 2.143 | 1.175 | 8 / 2066.0 | equipe:guia, negocio:souvenir + 2 melhorias |
| 11 | Q 1.558, AL 37, B 606, BH 290, T 1.235, PL 135, P 220, I 94, S 463, VQ 96 | 364 | 842 | 122 | 4.000 | 580 | 8 / 2307.0 | negocio:food_truck, negocio:surfe |
| 12 | Q 1.140, AL 341, B 520, BH 511, PA 214, T 1.215, PI 40, PL 221, P 633, I 413, S 601, SU 425, VQ 30 | 478 | 562 | 242 | 1.632 | 3.970 | 9 / 2521.0 | 11 melhorias |
| 13 | Q 1.378, AL 323, B 655, BH 579, PA 336, T 1.305, PI 10, PL 239, P 640, I 195, S 661, SU 444, VQ 109 | 478 | 738 | 242 | 2.691 | 6.695 | 9 / 2761.0 | 16 melhorias |
| 14 | Q 1.830, AL 341, BH 494, PA 152, PI 11, PL 193, I 202, S 637, SU 564, VQ 103 | 478 | 636 | 42 | 2.803 | 7.263 | 9 / 3020.0 | 14 melhorias |
| 15 | Q 1.401, AL 242, B 781, BH 638, PA 175, T 1.199, PI 76, PL 289, P 156, I 173, S 488, SU 516, VQ 42 | 481 | 772 | 242 | 3.524 | 8.419 | 10 / 3244.0 | 15 melhorias |
| 16 | Q 1.915, AL 276, B 691, BH 763, PA 347, F 135, T 1.247, PI 54, PL 340, P 351, I 223, S 625, SU 467, VQ 209 | 484 | 798 | 122 | 4.084 | 10.573 | 10 / 3540.0 | 14 melhorias |
| 17 | Q 1.764, AL 400, B 1.056, BH 916, PA 274, F 150, T 1.587, PL 372, P 1.206, I 148, S 637, SU 634, VQ 140 | 487 | 702 | 242 | 5.306 | 13.121 | 10 / 3902.0 | 15 melhorias |
| 18 | Q 2.216, AL 259, B 852, BH 1.032, PA 356, F 165, T 1.735, PI 30, PL 372, I 169, S 616, SU 584, VQ 153 | 493 | 898 | 122 | 5.895 | 14.252 | 10 / 4263.0 | 15 melhorias |
| 19 | Q 1.864, AL 118, B 1.519, BH 670, PA 117, F 135, T 1.662, PL 261, P 264, I 57, S 604, SU 384, VQ 120 | 496 | 748 | 242 | 6.030 | 14.512 | 10 / 4608.0 | 14 melhorias |
| 20 | Q 2.686, AL 251, B 1.413, BH 1.107, PA 338, F 135, T 1.926, PI 54, PL 433, I 196, S 690, SU 574, VQ 131 | 498 | 854 | 242 | 6.674 | 16.178 | 10 / 4972.0 | 13 melhorias |
| 21 | Q 2.680, AL 287, B 43, BH 1.119, PA 213, F 75, T 728, PL 363, I 170, S 625, SU 617, VQ 300 | 498 | 762 | 67 | 6.140 | 15.932 | 10 / 5372.0 | 11 melhorias |
| 22 | Q 2.327, AL 332, B 1.723, BH 1.245, PA 169, F 225, T 1.867, PI 100, PL 447, P 1.925, I 193, S 555, SU 874, VQ 130 | 502 | 828 | 242 | 7.720 | 18.753 | 10 / 5744.0 | 12 melhorias |
| 23 | Q 2.844, AL 307, B 1.619, BH 1.417, PA 388, F 225, T 2.329, PI 40, PL 510, I 191, S 634, SU 931, VQ 47 | 502 | 982 | 122 | 7.970 | 20.658 | 10 / 6120.0 | 11 melhorias |
| 24 | RE 1.000, Q 2.373, AL 225, B 1.746, BH 1.383, PA 169, F 275, T 2.673, PI 43, PL 529, P 1.280, I 234, S 574, SU 845, VQ 175 | 502 | 754 | 1.442 | 30.780 | 704 | 10 / 6494.0 | grand_hotel + 1 melhorias; podia: grand_hotel |
| 25 | RE 3.500, Q 2.914, AL 283, B 1.870, BH 1.381, E 3.200, PA 378, F 250, M 97, H 7.735, HN 476, T 2.693, PI 87, PL 560, R 908, I 178, S 624, SU 868, VQ 122 | 1.402 | 872 | 752 | 16.040 | 9.762 | 10 / 6920.0 | equipe:garcom_hotel, salao_jogos + 11 melhorias; podia: salao_jogos |
| 26 | Q 2.883, AL 86, B 2.151, BH 904, FI 102, PA 98, F 250, M 136, H 8.847, HN 893, T 2.693, PL 330, P 711, R 885, I 77, S 661, SU 399, VQ 95 | 1.453 | 844 | 884 | 17.320 | 11.462 | 10 / 7322.0 | 19 melhorias |
| 27 | Q 3.156, AL 207, B 2.572, BH 1.699, FI 127, PA 341, F 350, M 242, H 9.331, HN 1.333, EM 1.429, T 3.875, PI 48, PL 622, P 836, R 1.399, I 177, S 633, SU 739, VQ 207 | 1.463 | 1.006 | 2.129 | 23.185 | 13.002 | 10 / 7793.0 | 22 melhorias |
| 28 | Q 4.182, AL 224, B 77, BH 1.369, E 2.976, FI 145, PA 171, M 147, H 9.018, HN 1.697, PI 52, PL 451, R 1.540, I 217, S 653, SU 688, VQ 122 | 1.463 | 850 | 1.079 | 19.870 | 13.469 | 10 / 8378.0 | 16 melhorias |
| 29 | Q 1.625, B 2.781, BH 1.077, FI 161, PA 152, F 50, M 964, H 8.066, HN 1.699, T 474, PL 371, P 1.150, R 1.947, I 130, S 567, SU 643, VQ 50 | 1.463 | 772 | 1.424 | 19.050 | 12.667 | 10 / 8686.0 | 14 melhorias |
| 30 | Q 3.663, AL 335, B 2.330, BH 1.728, FI 365, PA 409, F 600, M 343, H 7.142, HN 1.618, T 4.836, PL 684, R 1.566, I 319, S 541, SU 764, VQ 407 | 1.466 | 1.232 | 1.779 | 21.555 | 14.286 | 10 / 9271.0 | 14 melhorias |
| 31 | Q 3.286, AL 687, B 2.584, BH 1.908, E 2.464, FI 425, PA 272, F 120, M 568, H 7.035, HN 1.554, T 801, PI 54, PL 688, P 1.069, R 1.671, I 305, S 799, SU 960, VQ 119 | 1.473 | 904 | 1.179 | 22.700 | 15.401 | 10 / 9772.0 | 13 melhorias |
| 32 | Q 4.452, AL 294, B 2.561, BH 2.007, CP 600, FI 326, PA 495, F 520, M 281, H 11.827, HN 1.845, T 5.273, PI 112, PL 671, P 1.475, R 2.200, I 266, S 805, SU 900, VQ 299 | 1.473 | 1.146 | 1.179 | 29.800 | 19.011 | 10 / 10371.0 | 16 melhorias |
| 33 | Q 4.216, AL 181, B 3.289, BH 1.243, FI 146, PA 168, F 600, M 499, H 13.296, HN 2.234, EM 1.429, T 5.676, PL 422, P 670, R 1.817, I 178, S 694, SU 635, VQ 173 | 1.473 | 942 | 2.694 | 31.585 | 19.882 | 10 / 10918.0 | 15 melhorias |
| 34 | Q 4.862, AL 509, B 3.091, BH 2.199, E 5.312, FI 154, PA 547, F 600, M 339, H 10.361, HN 2.722, T 5.218, PI 30, PL 743, P 636, R 1.856, I 258, S 774, SU 1.247, VQ 206 | 1.473 | 1.116 | 1.204 | 35.940 | 21.813 | 10 / 11514.0 | 15 melhorias |
| 35 | Q 5.615, AL 445, BH 1.893, FI 164, PA 231, M 488, H 9.995, HN 2.694, PI 65, PL 524, R 1.791, I 361, S 821, SU 1.144, VQ 256 | 1.473 | 1.102 | 859 | 27.000 | 17.867 | 10 / 12108.0 | 10 melhorias |
| 36 | Q 4.598, AL 337, B 3.024, BH 2.203, FI 443, PA 254, F 600, M 342, H 10.842, HN 2.358, T 6.220, PL 797, P 3.092, R 1.652, I 424, S 737, SU 1.397, VQ 189 | 1.473 | 1.162 | 2.384 | 32.540 | 19.818 | 10 / 12655.0 | 11 melhorias |
| 37 | Q 4.935, AL 433, B 3.358, BH 2.251, E 6.080, FI 420, PA 552, F 780, M 608, H 12.531, HN 2.996, EM 4.800, T 5.697, PI 100, PL 795, R 2.464, I 432, S 984, SU 1.110, VQ 237 | 1.477 | 782 | 914 | 40.840 | 27.367 | 10 / 13249.0 | 12 melhorias |
| 38 | Q 4.148, AL 563, B 3.722, BH 2.428, CP 600, FI 368, PA 288, F 900, M 399, H 7.238, HN 3.017, T 6.981, PI 35, PL 904, P 1.548, R 2.894, I 482, S 907, SU 1.818, VQ 233 | 1.477 | 1.212 | 1.334 | 38.480 | 24.338 | 10 / 13820.0 | 10 melhorias |
| 39 | Q 5.244, AL 464, B 3.657, BH 2.588, FI 149, PA 571, F 1.020, M 359, H 19.332, HN 3.188, EM 4.800, T 7.321, PL 844, P 700, R 1.772, I 306, S 916, SU 1.344, VQ 421 | 1.477 | 1.048 | 2.044 | 47.560 | 27.205 | 10 / 14412.0 | 10 melhorias |
| 40 | Q 4.753, AL 527, B 3.355, BH 2.626, E 7.040, FI 145, PA 377, F 960, M 269, H 12.419, HN 3.372, T 7.815, PI 146, PL 966, P 2.605, R 2.819, I 482, S 853, SU 1.884, VQ 233 | 1.477 | 1.030 | 1.049 | 46.400 | 30.896 | 10 / 14973.0 | 8 melhorias |
| 41 | Q 5.945, AL 354, B 3.070, BH 2.590, FI 152, PA 707, F 960, M 484, H 12.900, HN 3.556, EM 5.200, T 8.242, PI 73, PL 911, P 1.992, R 2.767, I 474, S 889, SU 1.707, VQ 243 | 1.477 | 1.114 | 1.389 | 49.600 | 30.531 | 10 / 15597.0 | 7 melhorias |
| 42 | Q 5.357, AL 443, BH 2.212, FI 142, PA 313, F 420, M 851, H 17.679, HN 3.252, T 2.699, PI 36, PL 621, R 2.476, I 382, S 991, SU 1.619, VQ 434 | 1.477 | 910 | 2.029 | 33.700 | 32.341 | 10 / 16192.0 | 4 melhorias |
| 43 | Q 5.390, AL 341, B 3.293, BH 2.560, E 8.384, FI 477, PA 400, F 1.020, M 448, H 24.359, HN 4.783, T 9.253, PI 73, PL 820, P 389, R 3.023, I 494, S 873, SU 1.516, VQ 255 | 1.477 | 1.262 | 1.264 | 53.000 | 43.488 | 10 / 16781.0 | 5 melhorias |
| 44 | Q 5.722, AL 319, B 2.904, BH 2.693, FI 154, PA 547, F 1.020, M 731, H 10.798, HN 4.040, T 9.714, PI 73, PL 932, P 456, R 3.611, I 370, S 833, SU 1.701, VQ 314 | 1.477 | 1.124 | 994 | 50.000 | 36.825 | 10 / 17403.0 | 4 melhorias |
| 45 | Q 5.292, AL 54, B 3.584, BH 1.534, FI 148, PA 223, F 1.140, M 342, H 16.041, HN 5.020, EM 1.429, T 9.576, PL 553, P 3.872, R 3.539, I 147, S 927, SU 895, VQ 548 | 1.477 | 1.290 | 2.189 | 44.000 | 42.733 | 10 / 18000.0 | 3 melhorias |
| 46 | RE 1.500, Q 5.859, AL 484, B 3.424, BH 2.476, E 9.152, FI 148, PA 734, F 960, M 441, H 12.910, HN 4.618, T 9.176, PI 109, PL 903, R 3.486, I 394, S 822, SU 1.480, VQ 263 | 1.480 | 954 | 1.049 | 48.000 | 50.589 | 10 / 18617.0 | 3 melhorias |
| 47 | RE 1.000, Q 5.323, AL 453, B 3.006, BH 2.489, FI 134, PA 282, F 960, M 329, H 15.914, HN 4.812, EM 5.200, T 8.889, PL 937, P 2.651, R 2.466, I 868, S 799, SU 1.739, VQ 289 | 1.480 | 988 | 1.094 | 58.500 | 47.067 | 10 / 19226.0 | 3 melhorias |
| 48 | Q 5.452, AL 456, B 3.542, BH 2.672, FI 144, PA 673, F 1.140, M 462, H 11.014, HN 4.663, T 9.497, PI 109, PL 938, R 2.916, I 478, S 975, SU 1.495, VQ 349 | 1.480 | 1.182 | 2.359 | 45.000 | 44.021 | 10 / 19827.0 | 2 melhorias |
| 49 | Q 5.430, AL 386, BH 2.236, E 10.112, FI 150, PA 347, M 321, H 17.374, HN 4.663, EM 1.950, PL 645, R 3.895, I 432, S 988, SU 1.732, VQ 267 | 1.480 | 928 | 749 | 52.500 | 39.293 | 10 / 20433.0 | 2 melhorias |
| 50 | Q 4.969, AL 351, B 3.318, BH 2.537, FI 405, PA 267, F 960, M 635, H 23.182, HN 5.129, T 8.639, PI 73, PL 862, P 4.914, R 3.179, I 473, S 822, SU 2.044, VQ 146 | 1.480 | 1.034 | 1.134 | 30.000 | 68.550 | 10 / 20999.0 | 1 melhorias |
| 51 | Q 5.607, AL 487, B 3.848, BH 2.527, FI 147, PA 556, F 1.140, M 826, H 17.063, HN 5.595, EM 3.429, T 9.613, PL 925, R 2.304, I 359, S 931, SU 1.495, VQ 445 | 1.480 | 1.132 | 2.554 | 0 | 120.681 | 10 / 21613.0 | — |
| 52 | Q 5.628, AL 124, B 3.758, BH 1.554, E 10.112, FI 150, PA 246, F 960, M 974, H 18.993, HN 3.963, T 9.042, PL 556, P 2.372, R 3.600, I 194, S 798, SU 890, VQ 198 | 1.480 | 1.150 | 879 | 0 | 181.283 | 10 / 22233.0 | — |
| 53 | Q 6.064, AL 485, B 3.838, BH 2.577, FI 133, PA 537, F 1.020, M 506, H 34.446, HN 4.663, EM 4.800, T 9.637, PL 925, R 3.066, I 398, S 874, SU 1.490, VQ 263 | 1.480 | 1.508 | 1.094 | 0 | 252.923 | 10 / 22867.0 | — |
| 54 | Q 4.381, AL 712, B 3.426, BH 2.610, FI 142, PA 334, F 300, M 751, H 24.430, HN 5.829, T 1.608, PI 36, PL 894, P 2.922, R 3.720, I 375, S 801, SU 1.840, VQ 202 | 1.480 | 976 | 2.454 | 0 | 303.325 | 10 / 23384.0 | — |
| 55 | Q 5.554, AL 404, B 3.490, BH 2.551, E 10.112, FI 139, PA 585, F 960, M 703, H 7.894, HN 4.430, EM 1.950, T 8.908, PL 878, R 4.023, I 452, S 961, SU 1.253, VQ 439 | 1.480 | 1.106 | 1.374 | 0 | 355.052 | 10 / 24028.0 | — |
| 56 | Q 6.018, AL 429, BH 2.161, FI 142, PA 238, M 572, H 25.800, HN 4.896, PI 36, PL 628, R 3.796, I 321, S 869, SU 1.386, VQ 41 | 1.480 | 1.116 | 844 | 0 | 398.945 | 10 / 24613.0 | — |

### Atual — dedicado, semente 0

[CSV diário completo](../../tools/ue58/balance/pacote2/results/atual_dedicado_diario_seed0.csv).

| Dia | Renda por fonte | Salários | Estoque | Outras saídas | Investimento | Caixa final | Nível / XP | Compras / expansões compráveis |
|---|---|---|---|---|---|---|---|---|
| 1 | RE 530, Q 766 | 0 | 321 | 150 | 680 | 295 | 2 / 172.0 | equipe:atendente, kiosk_tables, drinks; podia: drinks; kiosk_tables |
| 2 | RE 420, Q 802, VQ 19 | 30 | 275 | 2 | 668 | 561 | 3 / 378.0 | neon, grill + 2 melhorias; podia: grill; neon |
| 3 | Q 1.167, VQ 72 | 32 | 556 | 5 | 900 | 307 | 4 / 548.0 | negocio:sorveteria; podia: bar |
| 4 | RE 550, Q 1.398, I 363, VQ 111 | 72 | 525 | 5 | 1.350 | 777 | 5 / 829.0 | bar + 2 melhorias; podia: bar |
| 5 | Q 1.096, B 246, BH 399, I 385, VQ 66 | 72 | 440 | 11 | 1.748 | 698 | 6 / 1100.0 | equipe:bartender, negocio:aluguel + 1 melhorias; podia: pousada |
| 6 | Q 1.583, AL 102, B 552, BH 282, I 98, VQ 110 | 162 | 701 | 11 | 2.200 | 352 | 6 / 1366.0 | negocio:surfe; podia: pousada |
| 7 | RE 1.100, Q 1.128, AL 463, B 137, BH 412, I 251, SU 689, VQ 29 | 217 | 437 | 661 | 2.488 | 757 | 7 / 1761.0 | pousada + 1 melhorias; podia: pousada |
| 8 | RE 1.100, Q 1.197, AL 437, B 508, BH 496, I 422, SU 593, VQ 106 | 220 | 457 | 143 | 2.744 | 2.052 | 8 / 2036.0 | equipe:camareira, equipe:recepcionista, pool + 3 melhorias; podia: passeios; pool |
| 9 | Q 1.526, AL 466, B 472, BH 496, PI 60, PL 163, P 934, I 252, SU 554, VQ 80 | 290 | 748 | 33 | 5.400 | 583 | 8 / 2335.0 | equipe:piscineiro, passeios, negocio:souvenir, negocio:food_truck; podia: passeios |
| 10 | Q 1.098, AL 501, B 467, BH 515, PA 184, T 432, PI 50, PL 233, I 495, S 482, SU 422, VQ 18 | 416 | 542 | 187 | 1.433 | 2.902 | 9 / 2571.0 | equipe:guia + 9 melhorias |
| 11 | Q 1.476, AL 357, B 496, BH 510, PA 407, T 1.355, PI 10, PL 233, P 1.237, I 218, S 639, SU 495, VQ 56 | 469 | 660 | 122 | 2.661 | 6.479 | 9 / 2843.0 | 17 melhorias |
| 12 | Q 1.497, AL 59, B 840, BH 377, PA 148, T 1.413, PL 145, P 104, I 136, S 631, SU 241, VQ 102 | 473 | 852 | 242 | 2.952 | 7.654 | 9 / 3130.0 | 16 melhorias |
| 13 | Q 2.061, AL 271, B 537, BH 619, PA 369, T 1.378, PI 13, PL 314, P 128, I 199, S 615, SU 449, VQ 123 | 478 | 820 | 242 | 3.841 | 9.348 | 10 / 3450.0 | 17 melhorias |
| 14 | Q 2.249, AL 311, BH 680, PA 135, T 410, PL 252, I 245, S 700, SU 694, VQ 117 | 478 | 766 | 67 | 3.936 | 9.894 | 10 / 3785.0 | 14 melhorias |
| 15 | Q 1.976, AL 419, B 839, BH 920, PA 185, F 135, T 1.487, PI 15, PL 352, P 490, I 448, S 640, SU 678, VQ 109 | 481 | 772 | 242 | 4.778 | 12.314 | 10 / 4175.0 | 14 melhorias |
| 16 | Q 2.376, AL 208, B 1.131, BH 1.024, PA 382, F 150, T 1.647, PI 45, PL 385, P 333, I 229, S 651, SU 632, VQ 82 | 484 | 1.080 | 122 | 5.655 | 14.248 | 10 / 4600.0 | 15 melhorias |
| 17 | Q 2.238, AL 358, B 1.285, BH 1.066, PA 187, F 135, T 1.782, PI 34, PL 432, P 925, I 381, S 606, SU 802, VQ 83 | 487 | 676 | 242 | 6.780 | 16.377 | 10 / 4999.0 | 16 melhorias |
| 18 | Q 2.948, AL 259, B 1.249, BH 1.103, PA 350, F 180, T 2.203, PL 458, I 222, S 597, SU 749, VQ 119 | 487 | 966 | 122 | 7.064 | 18.174 | 10 / 5431.0 | 14 melhorias |
| 19 | Q 2.316, AL 454, B 1.607, BH 1.292, PA 220, F 150, T 1.966, PI 19, PL 460, P 132, I 207, S 625, SU 941, VQ 101 | 496 | 710 | 242 | 7.880 | 19.336 | 10 / 5843.0 | 14 melhorias |
| 20 | Q 2.760, AL 319, B 1.726, BH 1.243, PA 397, F 250, T 2.025, PI 20, PL 531, P 1.330, I 235, S 616, SU 932, VQ 68 | 498 | 952 | 242 | 8.620 | 21.477 | 10 / 6262.0 | 13 melhorias; podia: grand_hotel |
| 21 | Q 3.377, AL 173, B 83, BH 1.248, PA 159, F 125, T 886, PL 351, I 228, S 695, SU 892, VQ 217 | 498 | 914 | 67 | 8.330 | 20.102 | 10 / 6744.0 | 11 melhorias |
| 22 | RE 1.000, Q 2.536, AL 423, B 2.042, BH 1.531, PA 208, F 100, T 662, PI 129, PL 492, P 1.688, I 198, S 664, SU 1.147, VQ 130 | 502 | 638 | 1.372 | 30.000 | 539 | 10 / 7147.0 | grand_hotel; podia: grand_hotel |
| 23 | RE 3.500, Q 3.424, AL 282, B 2.058, BH 1.532, E 3.200, PA 355, F 275, M 51, H 9.977, HN 536, T 2.855, PI 43, PL 542, R 960, I 201, S 695, SU 744, VQ 106 | 1.402 | 1.100 | 1.747 | 17.720 | 9.906 | 10 / 7647.0 | equipe:garcom_hotel, salao_jogos + 13 melhorias; podia: salao_jogos |
| 24 | Q 3.118, AL 533, B 2.119, BH 1.578, E 2.400, FI 129, PA 193, F 300, M 54, H 13.960, HN 1.012, T 2.927, PI 44, PL 548, P 661, R 1.413, I 384, S 649, SU 901, VQ 64 | 1.450 | 814 | 1.569 | 24.900 | 14.160 | 10 / 8105.0 | 26 melhorias |
| 25 | Q 4.572, AL 269, B 1.875, BH 1.693, E 1.984, FI 148, PA 365, F 375, M 433, H 10.716, HN 1.549, T 4.274, PI 74, PL 621, P 454, R 1.115, I 175, S 557, SU 1.044, VQ 186 | 1.454 | 1.166 | 2.619 | 25.815 | 15.585 | 10 / 8781.0 | 22 melhorias |
| 26 | Q 3.912, AL 433, B 2.331, BH 1.877, E 4.352, FI 169, PA 197, F 350, M 316, H 14.735, HN 2.023, T 4.177, PI 156, PL 625, P 1.595, R 1.771, I 674, S 636, SU 1.082, VQ 194 | 1.457 | 1.102 | 2.784 | 32.850 | 18.997 | 10 / 9400.0 | 24 melhorias |
| 27 | Q 4.761, AL 325, B 2.399, BH 1.737, E 4.928, FI 151, PA 498, F 600, M 533, H 5.887, HN 2.016, EM 5.600, T 4.538, PL 657, P 807, R 2.125, I 323, S 790, SU 901, VQ 342 | 1.457 | 1.034 | 2.634 | 34.955 | 18.836 | 10 / 10097.0 | 21 melhorias |
| 28 | Q 5.659, AL 290, B 94, BH 1.706, E 4.928, FI 158, PA 243, F 240, M 215, H 9.823, HN 2.234, T 1.573, PL 504, R 2.069, I 326, S 815, SU 893, VQ 178 | 1.457 | 1.322 | 1.909 | 29.600 | 16.496 | 10 / 10765.0 | 16 melhorias |
| 29 | Q 4.168, AL 417, B 2.785, BH 2.027, E 4.928, FI 423, PA 253, F 680, M 311, H 7.463, HN 2.234, EM 5.600, T 5.675, PI 58, PL 663, P 3.025, R 2.229, I 282, S 739, SU 1.312, VQ 210 | 1.467 | 946 | 2.674 | 35.825 | 21.067 | 10 / 11366.0 | 17 melhorias |
| 30 | Q 5.641, AL 294, B 2.957, BH 2.132, E 5.312, FI 323, PA 470, F 600, M 1.267, H 7.129, HN 1.570, T 6.092, PI 120, PL 781, R 1.685, I 309, S 723, SU 1.686, VQ 246 | 1.470 | 1.080 | 2.154 | 33.700 | 22.001 | 10 / 12053.0 | 14 melhorias |
| 31 | Q 5.080, AL 351, B 3.232, BH 2.274, CP 150, E 5.696, FI 415, PA 238, F 680, M 792, H 15.425, HN 2.133, EM 1.786, T 6.513, PI 33, PL 822, P 628, R 2.395, I 377, S 773, SU 1.671, VQ 363 | 1.473 | 1.580 | 2.649 | 41.540 | 26.586 | 10 / 12687.0 | 15 melhorias |
| 32 | Q 5.626, AL 495, B 2.976, BH 2.333, E 5.696, FI 140, PA 496, F 680, M 313, H 13.666, HN 2.470, T 6.722, PI 100, PL 853, P 323, R 2.547, I 426, S 747, SU 1.663, VQ 270 | 1.473 | 1.076 | 2.859 | 44.440 | 25.281 | 10 / 13400.0 | 14 melhorias |
| 33 | Q 5.054, AL 375, B 3.293, BH 2.432, E 6.080, FI 144, PA 372, F 960, M 466, H 17.828, HN 2.996, T 6.782, PI 167, PL 821, P 2.393, R 2.239, I 471, S 834, SU 1.772, VQ 198 | 1.473 | 1.070 | 2.529 | 48.680 | 27.206 | 10 / 14025.0 | 13 melhorias |
| 34 | Q 6.253, AL 260, B 3.832, BH 2.447, E 6.656, FI 155, PA 601, F 1.020, M 650, H 10.249, HN 3.049, T 7.869, PI 35, PL 840, P 2.678, R 2.677, I 556, S 1.030, SU 2.071, VQ 146 | 1.477 | 1.238 | 2.469 | 46.440 | 28.656 | 10 / 14698.0 | 10 melhorias |
| 35 | Q 6.459, AL 410, B 82, BH 2.168, E 7.040, FI 139, PA 332, F 360, M 224, H 19.069, HN 3.665, T 2.112, PI 73, PL 625, R 2.475, I 478, S 981, SU 1.871, VQ 144 | 1.477 | 1.164 | 1.779 | 45.420 | 27.524 | 10 / 15345.0 | 8 melhorias |
| 36 | Q 4.809, AL 640, B 3.266, BH 2.467, E 7.424, FI 419, PA 358, F 300, M 541, H 7.340, HN 3.711, T 1.342, PI 145, PL 847, P 2.770, R 2.473, I 458, S 918, SU 2.739, VQ 162 | 1.477 | 934 | 2.729 | 40.900 | 24.613 | 10 / 15902.0 | 6 melhorias |
| 37 | Q 6.199, AL 107, B 3.519, BH 1.531, E 7.808, FI 386, PA 344, F 1.080, M 377, H 18.857, HN 3.415, EM 1.950, T 8.648, PL 558, R 2.758, I 168, S 896, SU 685, VQ 131 | 1.477 | 1.324 | 2.024 | 48.700 | 30.505 | 10 / 16558.0 | 6 melhorias |
| 38 | Q 5.543, AL 603, B 3.273, BH 2.560, E 8.384, FI 157, PA 264, F 1.140, M 573, H 15.720, HN 4.599, T 9.634, PI 36, PL 936, P 3.735, R 4.118, I 724, S 786, SU 2.152, VQ 98 | 1.477 | 1.020 | 2.324 | 53.000 | 37.720 | 10 / 17179.0 | 5 melhorias |
| 39 | Q 5.539, AL 484, B 3.751, BH 2.602, E 8.768, FI 143, PA 616, F 1.080, M 508, H 8.471, HN 3.655, EM 1.950, T 9.640, PI 73, PL 956, R 2.724, I 565, S 1.019, SU 2.261, VQ 378 | 1.477 | 1.224 | 2.184 | 50.000 | 38.017 | 10 / 17862.0 | 4 melhorias |
| 40 | Q 5.467, AL 103, B 3.306, BH 1.513, E 9.152, FI 140, PA 238, F 1.200, M 297, H 33.599, HN 4.819, T 10.035, PL 569, P 1.920, R 3.561, I 215, S 903, SU 1.248, VQ 230 | 1.477 | 1.024 | 2.694 | 59.000 | 52.337 | 10 / 18535.0 | 4 melhorias |
| 41 | RE 1.500, Q 6.221, AL 469, B 3.446, BH 2.576, E 9.536, FI 151, PA 666, F 1.140, M 201, H 18.516, HN 5.440, EM 1.950, T 9.497, PL 929, P 974, R 3.514, I 487, S 860, SU 1.715, VQ 264 | 1.477 | 1.116 | 2.749 | 70.500 | 46.547 | 10 / 19231.0 | 4 melhorias |
| 42 | RE 1.000, Q 6.181, AL 499, B 150, BH 2.125, E 10.112, FI 158, PA 367, F 420, M 506, H 11.326, HN 5.362, T 2.699, PI 109, PL 682, R 2.669, I 524, S 1.075, SU 2.282, VQ 198 | 1.477 | 836 | 2.329 | 42.000 | 48.349 | 10 / 19888.0 | 2 melhorias |
| 43 | Q 5.262, AL 881, B 3.594, BH 2.598, E 10.112, FI 457, PA 356, F 1.140, M 418, H 16.023, HN 5.362, EM 1.786, T 9.500, PI 36, PL 832, P 3.831, R 3.788, I 898, S 842, SU 1.672, VQ 237 | 1.477 | 1.152 | 2.554 | 49.500 | 63.291 | 10 / 20520.0 | 2 melhorias |
| 44 | Q 6.868, AL 437, B 3.160, BH 2.524, E 10.112, FI 436, PA 612, F 1.080, M 190, H 26.585, HN 6.295, T 9.139, PL 904, P 914, R 4.224, I 374, S 983, SU 1.734, VQ 182 | 1.480 | 1.298 | 2.444 | 57.000 | 77.821 | 10 / 21211.0 | 2 melhorias |
| 45 | Q 5.590, AL 928, B 3.115, BH 2.651, E 10.112, FI 157, PA 306, F 1.200, M 625, H 13.403, HN 4.197, EM 1.786, T 9.690, PI 73, PL 891, P 900, R 3.641, I 892, S 854, SU 1.843, VQ 134 | 1.480 | 1.054 | 2.054 | 0 | 136.220 | 10 / 21829.0 | — |
| 46 | Q 6.728, AL 364, B 3.111, BH 2.655, E 10.112, FI 145, PA 564, F 1.080, M 294, H 25.771, HN 4.896, T 9.026, PL 868, P 391, R 3.335, I 387, S 855, SU 2.100, VQ 308 | 1.480 | 1.218 | 2.319 | 0 | 204.194 | 10 / 22550.0 | — |
| 47 | Q 5.977, AL 403, B 3.217, BH 2.554, E 10.112, FI 148, PA 290, F 1.140, M 791, H 17.209, HN 4.430, EM 1.950, T 9.588, PI 73, PL 925, P 5.228, R 4.019, I 424, S 927, SU 1.981, VQ 230 | 1.480 | 1.064 | 2.509 | 0 | 270.756 | 10 / 23202.0 | — |
| 48 | Q 7.009, AL 305, B 3.108, BH 2.671, E 10.112, FI 150, PA 628, F 1.080, M 277, H 30.989, HN 5.595, T 9.571, PI 109, PL 869, R 3.676, I 413, S 862, SU 2.267, VQ 379 | 1.480 | 1.424 | 2.174 | 0 | 345.748 | 10 / 23925.0 | — |
| 49 | Q 6.653, AL 394, BH 2.191, E 10.112, FI 148, PA 316, F 420, M 769, H 12.064, HN 4.430, EM 5.600, T 2.699, PI 109, PL 659, R 4.496, I 558, S 952, SU 1.761, VQ 466 | 1.480 | 1.054 | 2.569 | 0 | 395.443 | 10 / 24671.0 | — |
| 50 | Q 5.677, AL 491, B 3.784, BH 2.516, E 10.112, FI 403, PA 387, F 1.200, M 400, H 29.212, HN 5.362, T 10.035, PI 36, PL 856, P 4.249, R 3.626, I 448, S 775, SU 1.941, VQ 242 | 1.480 | 1.252 | 2.754 | 0 | 471.709 | 10 / 25334.0 | — |

### Proposto — casual, semente 0

[CSV diário completo](../../tools/ue58/balance/pacote2/results/proposto_casual_diario_seed0.csv).

| Dia | Renda por fonte | Salários | Estoque | Outras saídas | Investimento | Caixa final | Nível / XP | Compras / expansões compráveis |
|---|---|---|---|---|---|---|---|---|
| 1 | RE 370, Q 274 | 0 | 126 | 150 | 240 | 278 | 2 / 118.0 | equipe:atendente; podia: drinks; kiosk_tables |
| 2 | RE 280, Q 410, VQ 19 | 30 | 111 | 0 | 440 | 406 | 2 / 216.0 | kiosk_tables, drinks; podia: drinks; kiosk_tables |
| 3 | RE 300, Q 548, VQ 29 | 32 | 245 | 2 | 593 | 411 | 3 / 382.0 | neon, grill + 1 melhorias; podia: grill; neon |
| 4 | RE 550, Q 1.070, VQ 76 | 32 | 465 | 5 | 1.200 | 405 | 4 / 532.0 | bar; podia: bar |
| 5 | Q 849, B 131, BH 382, VQ 11 | 32 | 380 | 11 | 485 | 870 | 4 / 681.0 | equipe:bartender + 3 melhorias |
| 6 | Q 689, B 301, BH 285, VQ 34 | 77 | 304 | 11 | 1.076 | 711 | 5 / 802.0 | negocio:sorveteria + 2 melhorias |
| 7 | Q 818, B 78, BH 392, I 196, VQ 57 | 117 | 229 | 11 | 1.400 | 495 | 5 / 946.0 | negocio:aluguel |
| 8 | Q 591, AL 356, B 459, BH 469, I 222, VQ 21 | 165 | 316 | 131 | 497 | 1.503 | 6 / 1049.0 | 5 melhorias |
| 9 | RE 1.100, Q 1.091, AL 57, B 425, BH 274, I 109, VQ 67 | 165 | 551 | 661 | 2.400 | 849 | 6 / 1368.0 | pousada; podia: pousada |
| 10 | RE 1.100, Q 858, AL 401, B 446, BH 485, I 336, VQ 56 | 165 | 386 | 143 | 2.460 | 1.377 | 7 / 1502.0 | equipe:camareira, equipe:recepcionista, pool; podia: passeios; pool |
| 11 | Q 1.163, AL 228, B 430, BH 478, PI 10, PL 164, P 461, I 186, VQ 39 | 241 | 481 | 33 | 2.370 | 1.411 | 7 / 1674.0 | equipe:piscineiro, passeios + 3 melhorias; podia: passeios |
| 12 | Q 956, AL 270, B 526, BH 505, PL 225, P 248, I 178, VQ 74 | 277 | 390 | 162 | 2.306 | 1.258 | 7 / 1835.0 | equipe:guia, negocio:souvenir + 3 melhorias |
| 13 | Q 1.147, AL 291, B 555, BH 492, T 960, PL 219, P 804, I 198, S 580, VQ 59 | 364 | 720 | 242 | 4.294 | 943 | 8 / 2017.0 | negocio:food_truck, negocio:surfe + 2 melhorias |
| 14 | Q 1.211, AL 207, BH 414, PA 178, T 396, PL 160, I 141, S 665, SU 217, VQ 147 | 469 | 494 | 67 | 900 | 2.748 | 8 / 2214.0 | 6 melhorias |
| 15 | Q 901, AL 213, B 567, BH 535, PA 136, T 935, PL 224, P 692, I 147, S 557, SU 350, VQ 43 | 473 | 496 | 242 | 1.961 | 4.876 | 8 / 2353.0 | 12 melhorias |
| 16 | Q 1.352, AL 227, B 714, BH 586, PA 294, T 1.190, PL 246, P 452, I 175, S 647, SU 289, VQ 140 | 478 | 794 | 122 | 2.812 | 6.981 | 9 / 2556.0 | 15 melhorias |
| 17 | Q 1.235, AL 397, B 691, BH 631, PA 188, T 1.270, PL 309, P 650, I 411, S 627, SU 370, VQ 70 | 484 | 750 | 242 | 3.631 | 8.723 | 9 / 2754.0 | 16 melhorias |
| 18 | Q 1.733, AL 279, B 990, BH 735, PA 411, T 1.305, PL 324, I 192, S 517, SU 449, VQ 93 | 487 | 746 | 122 | 4.236 | 10.160 | 9 / 2979.0 | 15 melhorias |
| 19 | Q 1.295, AL 230, B 1.223, BH 895, PA 194, F 150, T 1.644, PL 354, P 695, I 169, S 595, SU 413, VQ 94 | 490 | 584 | 242 | 4.838 | 11.957 | 10 / 3228.0 | 14 melhorias |
| 20 | Q 2.018, AL 191, B 1.356, BH 980, PA 313, F 135, T 1.556, PI 30, PL 394, P 190, I 168, S 629, SU 499, VQ 60 | 490 | 934 | 242 | 5.295 | 13.516 | 10 / 3540.0 | 14 melhorias |
| 21 | Q 1.900, AL 206, BH 940, PA 174, F 45, T 461, PL 285, I 133, S 641, SU 390, VQ 110 | 490 | 618 | 67 | 5.040 | 12.585 | 10 / 3830.0 | 12 melhorias |
| 22 | Q 1.703, AL 273, B 1.223, BH 1.105, PA 174, F 120, T 1.648, PL 432, P 436, I 208, S 587, SU 521, VQ 44 | 496 | 738 | 242 | 5.600 | 13.982 | 10 / 4075.0 | 12 melhorias |
| 23 | Q 2.400, AL 48, B 1.475, BH 676, PA 236, F 105, T 1.567, PL 291, I 47, S 647, SU 251, VQ 224 | 498 | 796 | 122 | 5.904 | 14.629 | 10 / 4422.0 | 11 melhorias |
| 24 | Q 1.970, AL 289, B 1.481, BH 1.315, PA 206, F 150, T 1.965, PL 536, P 719, I 242, S 588, SU 560, VQ 74 | 502 | 762 | 242 | 6.380 | 16.837 | 10 / 4698.0 | 11 melhorias |
| 25 | Q 2.334, AL 186, B 1.375, BH 1.316, PA 371, F 225, T 2.043, PI 40, PL 481, P 872, I 199, S 583, SU 507, VQ 78 | 502 | 838 | 122 | 7.320 | 18.665 | 10 / 5001.0 | 11 melhorias |
| 26 | RE 1.000, Q 2.161, AL 248, B 1.992, BH 1.399, PA 169, F 250, T 2.419, PL 517, P 348, I 167, S 598, SU 611, VQ 120 | 505 | 702 | 242 | 28.000 | 1.215 | 10 / 5308.0 | grand_hotel; podia: grand_hotel |
| 27 | RE 3.500, Q 2.437, AL 244, B 1.854, BH 1.387, PA 370, F 225, M 374, H 7.507, HN 417, T 2.519, PL 518, P 171, R 1.032, I 164, S 653, SU 492, VQ 69 | 1.405 | 826 | 782 | 13.260 | 8.875 | 10 / 5636.0 | equipe:garcom_hotel, salao_jogos + 9 melhorias; podia: salao_jogos |
| 28 | Q 2.372, AL 259, BH 1.212, FI 104, PA 167, F 100, M 333, H 9.626, HN 773, T 783, PI 65, PL 365, R 1.365, I 168, S 645, SU 475, VQ 106 | 1.453 | 632 | 2.129 | 14.900 | 8.679 | 10 / 5996.0 | 18 melhorias |
| 29 | Q 2.191, AL 274, B 1.782, BH 1.560, E 3.200, FI 113, PA 227, F 250, M 321, H 9.025, HN 1.190, EM 300, T 2.644, PL 524, P 976, R 1.079, I 362, S 605, SU 754, VQ 15 | 1.453 | 994 | 824 | 20.600 | 12.199 | 10 / 6319.0 | 22 melhorias |
| 30 | Q 3.110, AL 288, B 2.462, BH 1.635, FI 425, PA 354, F 300, M 358, H 7.177, HN 1.533, T 3.694, PL 596, P 404, R 1.081, I 207, S 681, SU 562, VQ 162 | 1.457 | 928 | 899 | 21.015 | 12.928 | 10 / 6755.0 | 19 melhorias |
| 31 | Q 3.066, AL 370, B 2.349, BH 1.638, FI 142, PA 208, F 300, M 244, H 9.577, HN 1.697, T 3.720, PL 645, P 1.737, R 1.328, I 253, S 604, SU 636, VQ 90 | 1.463 | 1.004 | 1.034 | 22.730 | 15.301 | 10 / 7189.0 | 18 melhorias |
| 32 | Q 3.619, AL 312, B 2.429, BH 1.836, FI 148, PA 268, F 325, M 696, H 8.306, HN 1.699, T 4.061, PL 621, P 1.400, R 1.498, I 250, S 539, SU 799, VQ 179 | 1.466 | 846 | 1.034 | 25.760 | 15.180 | 10 / 7704.0 | 18 melhorias |
| 33 | Q 3.279, AL 108, B 2.161, BH 1.129, FI 154, PA 92, F 480, M 559, H 13.549, HN 1.780, T 4.083, PL 424, R 1.402, I 93, S 600, SU 384, VQ 92 | 1.473 | 1.162 | 1.414 | 25.305 | 16.195 | 10 / 8166.0 | 16 melhorias |
| 34 | Q 3.966, AL 335, B 2.321, BH 1.959, FI 134, PA 496, F 520, M 421, H 5.527, HN 2.428, T 5.063, PI 55, PL 700, P 520, R 2.006, I 361, S 797, SU 730, VQ 174 | 1.473 | 846 | 1.004 | 25.820 | 15.565 | 10 / 8675.0 | 15 melhorias |
| 35 | Q 3.993, AL 261, BH 1.675, FI 146, PA 251, F 160, M 868, H 5.602, HN 1.943, EM 500, T 1.162, PL 511, R 1.804, I 225, S 828, SU 930, VQ 284 | 1.473 | 996 | 1.899 | 19.240 | 13.099 | 10 / 9166.0 | 10 melhorias |
| 36 | Q 3.997, AL 65, B 2.733, BH 1.224, E 3.696, FI 154, PA 222, F 520, M 347, H 7.075, HN 1.943, T 5.071, PL 433, P 2.712, R 2.041, I 99, S 721, SU 594, VQ 144 | 1.473 | 1.042 | 874 | 25.645 | 17.856 | 10 / 9668.0 | 12 melhorias |
| 37 | Q 4.605, AL 323, B 3.161, BH 2.301, FI 368, PA 500, F 520, M 542, H 10.915, HN 2.040, EM 300, T 5.232, PL 789, P 1.020, R 1.782, I 269, S 705, SU 1.173, VQ 168 | 1.473 | 1.124 | 864 | 32.080 | 19.027 | 10 / 10174.0 | 14 melhorias |
| 38 | Q 3.921, AL 271, B 2.613, BH 2.255, FI 151, PA 297, F 780, M 594, H 13.582, HN 2.358, T 5.522, PL 812, R 2.453, I 280, S 759, SU 1.211, VQ 110 | 1.473 | 1.080 | 1.204 | 32.560 | 20.679 | 10 / 10668.0 | 12 melhorias |
| 39 | Q 4.537, AL 312, B 3.513, BH 2.387, FI 139, PA 493, F 780, M 332, H 18.320, HN 2.919, T 6.657, PL 849, R 2.327, I 447, S 772, SU 1.208, VQ 130 | 1.477 | 972 | 764 | 40.060 | 23.529 | 10 / 11183.0 | 13 melhorias |
| 40 | Q 3.982, AL 569, B 3.099, BH 2.432, FI 150, PA 320, F 840, M 274, H 4.791, HN 2.636, T 6.058, PI 140, PL 869, P 3.805, R 2.495, I 782, S 874, SU 1.024, VQ 218 | 1.477 | 942 | 894 | 32.000 | 23.574 | 10 / 11659.0 | 9 melhorias |
| 41 | Q 4.556, AL 298, B 4.023, BH 2.593, FI 152, PA 742, F 1.020, M 485, H 6.429, HN 2.755, T 7.847, PL 856, P 848, R 2.179, I 412, S 978, SU 1.549, VQ 116 | 1.477 | 964 | 934 | 36.240 | 21.797 | 10 / 12139.0 | 9 melhorias |
| 42 | Q 5.018, AL 267, BH 2.215, FI 147, PA 311, F 240, M 381, H 17.600, HN 2.772, T 1.643, PI 109, PL 704, R 2.471, I 377, S 901, SU 1.141, VQ 203 | 1.477 | 956 | 1.259 | 34.660 | 19.946 | 10 / 12607.0 | 7 melhorias |
| 43 | Q 4.843, AL 396, B 3.878, BH 2.636, E 3.520, FI 139, PA 329, F 960, M 864, H 10.441, HN 2.199, EM 500, T 8.371, PL 884, P 2.435, R 2.499, I 252, S 832, SU 1.359, VQ 169 | 1.477 | 950 | 804 | 35.240 | 28.980 | 10 / 13140.0 | 6 melhorias |
| 44 | Q 4.941, AL 374, B 3.849, BH 2.587, FI 352, PA 682, F 960, M 238, H 15.846, HN 3.247, T 8.907, PL 954, P 1.671, R 3.017, I 358, S 889, SU 1.168, VQ 257 | 1.477 | 1.232 | 644 | 40.600 | 35.324 | 10 / 13654.0 | 6 melhorias |
| 45 | Q 4.801, AL 417, B 3.531, BH 2.519, FI 138, PA 271, F 1.020, M 385, H 20.805, HN 3.740, EM 800, T 8.850, PI 73, PL 904, P 1.260, R 3.394, I 366, S 894, SU 1.346, VQ 73 | 1.477 | 1.004 | 954 | 53.260 | 34.216 | 10 / 14147.0 | 6 melhorias |
| 46 | Q 5.187, AL 304, B 3.830, BH 2.424, FI 157, PA 636, F 1.020, M 637, H 7.846, HN 4.217, T 9.272, PL 941, R 3.617, I 431, S 989, SU 1.197, VQ 198 | 1.477 | 1.096 | 1.114 | 41.600 | 31.831 | 10 / 14677.0 | 4 melhorias |
| 47 | Q 4.886, AL 342, B 3.082, BH 2.575, FI 164, PA 284, F 1.020, M 935, H 19.033, HN 4.217, EM 800, T 9.426, PL 883, P 379, R 2.667, I 388, S 750, SU 1.235, VQ 249 | 1.477 | 1.050 | 924 | 47.900 | 33.796 | 10 / 15172.0 | 4 melhorias |
| 48 | Q 5.085, AL 52, B 3.510, BH 1.536, FI 136, PA 368, F 900, M 220, H 26.241, HN 5.649, T 8.831, PL 542, P 2.185, R 3.571, I 168, S 905, SU 484, VQ 237 | 1.480 | 1.178 | 1.504 | 53.000 | 37.254 | 10 / 15735.0 | 4 melhorias |
| 49 | Q 4.882, AL 354, BH 2.105, FI 154, PA 296, F 360, M 356, H 7.547, HN 5.021, T 2.284, PL 606, R 3.304, I 338, S 1.030, SU 1.139, VQ 269 | 1.480 | 858 | 1.979 | 30.000 | 32.981 | 10 / 16223.0 | 2 melhorias |
| 50 | Q 4.381, AL 321, B 3.542, BH 2.601, E 10.112, FI 407, PA 278, F 960, M 480, H 9.878, HN 4.430, T 9.099, PI 109, PL 858, P 3.718, R 2.987, I 429, S 811, SU 1.377, VQ 267 | 1.480 | 974 | 999 | 52.800 | 33.772 | 10 / 16726.0 | 3 melhorias |
| 51 | Q 5.652, AL 445, B 3.461, BH 2.694, FI 153, PA 641, F 1.020, M 246, H 25.638, HN 5.362, T 9.675, PL 927, R 4.524, I 312, S 973, SU 1.209, VQ 466 | 1.480 | 998 | 924 | 42.000 | 51.770 | 10 / 17294.0 | 2 melhorias |
| 52 | Q 2.472, B 3.899, BH 1.619, FI 150, PA 183, F 240, M 467, H 21.819, HN 4.896, T 1.474, PL 581, P 751, R 3.084, I 227, S 882, SU 557, VQ 37 | 1.480 | 648 | 979 | 24.000 | 68.000 | 10 / 17606.0 | 1 melhorias |
| 53 | RE 1.500, Q 5.353, AL 381, B 3.285, BH 2.532, FI 138, PA 719, F 1.020, M 169, H 22.426, HN 5.595, T 9.503, PL 878, P 3.944, R 2.966, I 376, S 952, SU 1.549, VQ 324 | 1.480 | 1.270 | 704 | 0 | 128.157 | 10 / 18161.0 | — |
| 54 | RE 1.000, Q 4.496, AL 509, B 3.768, BH 2.626, FI 154, PA 358, F 1.020, M 309, H 14.919, HN 4.896, T 9.848, PI 109, PL 871, P 418, R 3.157, I 435, S 728, SU 1.530, VQ 368 | 1.480 | 994 | 1.514 | 0 | 175.688 | 10 / 18704.0 | — |
| 55 | Q 4.925, AL 301, B 3.430, BH 2.543, FI 150, PA 570, F 960, M 540, H 31.823, HN 5.129, EM 800, T 8.889, PI 73, PL 885, P 2.295, R 4.300, I 400, S 994, SU 1.539, VQ 234 | 1.480 | 888 | 1.054 | 0 | 243.047 | 10 / 19230.0 | — |
| 56 | Q 4.612, AL 354, BH 2.257, FI 150, PA 340, F 360, M 758, H 26.864, HN 4.896, T 2.284, PI 146, PL 628, R 4.329, I 461, S 942, SU 1.190, VQ 131 | 1.480 | 958 | 1.999 | 0 | 289.312 | 10 / 19711.0 | — |
| 57 | Q 2.901, B 3.662, BH 1.518, E 10.112, FI 162, PA 158, F 240, M 247, H 30.257, HN 6.062, EM 500, T 1.474, PL 500, P 692, R 4.040, I 219, S 807, SU 688, VQ 70 | 1.480 | 956 | 834 | 0 | 350.352 | 10 / 20034.0 | — |
| 58 | Q 5.039, AL 349, B 3.731, BH 2.616, FI 380, PA 587, F 960, M 610, H 12.241, HN 5.595, T 8.812, PI 73, PL 858, P 3.051, R 3.168, I 450, S 868, SU 1.403, VQ 156 | 1.480 | 962 | 939 | 0 | 397.917 | 10 / 20550.0 | — |
| 59 | Q 2.651, B 3.707, BH 1.478, FI 148, PA 187, F 240, M 354, H 13.848, HN 5.595, T 1.474, PL 532, P 1.940, R 3.751, I 207, S 1.023, SU 614, VQ 179 | 1.480 | 872 | 954 | 0 | 432.540 | 10 / 20854.0 | — |
| 60 | Q 5.163, AL 182, B 2.969, BH 1.564, FI 161, PA 436, F 1.020, M 562, H 16.894, HN 4.430, T 9.234, PL 537, R 4.075, I 173, S 800, SU 463, VQ 217 | 1.480 | 906 | 694 | 0 | 478.340 | 10 / 21396.0 | — |

### Proposto — medio, semente 0

[CSV diário completo](../../tools/ue58/balance/pacote2/results/proposto_medio_diario_seed0.csv).

| Dia | Renda por fonte | Salários | Estoque | Outras saídas | Investimento | Caixa final | Nível / XP | Compras / expansões compráveis |
|---|---|---|---|---|---|---|---|---|
| 1 | RE 530, Q 464 | 0 | 118 | 150 | 570 | 306 | 2 / 138.0 | equipe:atendente, kiosk_tables, neon; podia: drinks; kiosk_tables |
| 2 | RE 420, Q 830, VQ 53 | 30 | 295 | 2 | 778 | 504 | 3 / 356.0 | drinks, grill + 2 melhorias; podia: drinks; grill |
| 3 | Q 977, VQ 130 | 32 | 523 | 5 | 900 | 150 | 4 / 524.0 | negocio:sorveteria |
| 4 | RE 550, Q 1.089, I 302, VQ 32 | 72 | 521 | 5 | 1.200 | 325 | 5 / 703.0 | bar; podia: bar |
| 5 | Q 1.054, B 14, BH 402, I 412, VQ 16 | 72 | 244 | 11 | 674 | 1.222 | 5 / 886.0 | equipe:bartender + 5 melhorias |
| 6 | RE 300, Q 1.032, B 311, BH 449, I 233, VQ 40 | 117 | 478 | 11 | 2.400 | 582 | 6 / 1088.0 | pousada; podia: pousada |
| 7 | Q 1.119, B 153, BH 395, I 315, VQ 35 | 117 | 458 | 23 | 756 | 1.244 | 6 / 1285.0 | equipe:camareira, equipe:recepcionista + 3 melhorias; podia: passeios; pool |
| 8 | RE 1.100, Q 1.179, B 428, BH 458, P 480, I 272, VQ 78 | 190 | 497 | 393 | 2.358 | 1.802 | 7 / 1553.0 | pool + 3 melhorias; podia: passeios; pool |
| 9 | Q 1.338, B 418, BH 475, PI 10, PL 173, P 343, I 256, VQ 54 | 196 | 608 | 33 | 3.400 | 632 | 7 / 1770.0 | equipe:piscineiro, passeios, negocio:aluguel; podia: passeios |
| 10 | RE 800, Q 1.136, AL 249, B 356, BH 485, PI 80, PL 237, P 218, I 242, VQ 120 | 271 | 405 | 562 | 2.143 | 1.175 | 8 / 2066.0 | equipe:guia, negocio:souvenir + 2 melhorias |
| 11 | Q 1.558, AL 37, B 606, BH 290, T 1.235, PL 135, P 220, I 94, S 463, VQ 96 | 364 | 842 | 122 | 4.000 | 580 | 8 / 2307.0 | negocio:food_truck, negocio:surfe |
| 12 | Q 1.140, AL 341, B 520, BH 511, PA 214, T 1.215, PI 40, PL 221, P 633, I 413, S 601, SU 425, VQ 30 | 478 | 562 | 242 | 1.632 | 3.970 | 9 / 2521.0 | 11 melhorias |
| 13 | Q 1.378, AL 323, B 655, BH 579, PA 336, T 1.305, PI 10, PL 239, P 640, I 195, S 661, SU 444, VQ 109 | 478 | 738 | 242 | 2.691 | 6.695 | 9 / 2761.0 | 16 melhorias |
| 14 | Q 1.830, AL 341, BH 494, PA 152, PI 11, PL 193, I 202, S 637, SU 564, VQ 103 | 478 | 636 | 42 | 2.803 | 7.263 | 9 / 3020.0 | 14 melhorias |
| 15 | Q 1.401, AL 242, B 781, BH 638, PA 175, T 1.199, PI 76, PL 289, P 156, I 173, S 488, SU 516, VQ 42 | 481 | 772 | 242 | 3.524 | 8.419 | 10 / 3244.0 | 15 melhorias |
| 16 | Q 1.915, AL 276, B 691, BH 763, PA 347, F 135, T 1.247, PI 54, PL 340, P 351, I 223, S 625, SU 467, VQ 209 | 484 | 798 | 122 | 4.084 | 10.573 | 10 / 3540.0 | 14 melhorias |
| 17 | Q 1.764, AL 400, B 1.056, BH 916, PA 274, F 150, T 1.587, PL 372, P 1.206, I 148, S 637, SU 634, VQ 140 | 487 | 702 | 242 | 5.306 | 13.121 | 10 / 3902.0 | 15 melhorias |
| 18 | Q 2.216, AL 259, B 852, BH 1.032, PA 356, F 165, T 1.735, PI 30, PL 372, I 169, S 616, SU 584, VQ 153 | 493 | 898 | 122 | 5.895 | 14.252 | 10 / 4263.0 | 15 melhorias |
| 19 | Q 1.864, AL 118, B 1.519, BH 670, PA 117, F 135, T 1.662, PL 261, P 264, I 57, S 604, SU 384, VQ 120 | 496 | 748 | 242 | 6.030 | 14.512 | 10 / 4608.0 | 14 melhorias |
| 20 | Q 2.686, AL 251, B 1.413, BH 1.107, PA 338, F 135, T 1.926, PI 54, PL 433, I 196, S 690, SU 574, VQ 131 | 498 | 854 | 242 | 6.674 | 16.178 | 10 / 4972.0 | 13 melhorias |
| 21 | Q 2.680, AL 287, B 43, BH 1.119, PA 213, F 75, T 728, PL 363, I 170, S 625, SU 617, VQ 300 | 498 | 762 | 67 | 6.140 | 15.932 | 10 / 5372.0 | 11 melhorias |
| 22 | Q 2.398, AL 401, B 1.601, BH 1.263, PA 228, F 135, T 1.747, PI 100, PL 468, P 1.925, I 186, S 597, SU 853, VQ 171 | 502 | 850 | 242 | 7.620 | 18.791 | 10 / 5743.0 | 12 melhorias |
| 23 | RE 1.000, Q 2.974, AL 285, B 2.051, BH 1.399, PA 304, F 250, T 2.356, PI 80, PL 518, I 188, S 584, SU 650, VQ 234 | 502 | 1.040 | 202 | 28.000 | 1.919 | 10 / 6153.0 | grand_hotel; podia: grand_hotel |
| 24 | RE 3.500, Q 964, B 1.996, BH 882, PA 117, F 125, M 149, H 10.060, HN 476, T 666, PL 316, P 480, R 842, I 108, S 588, SU 452, VH 100, VQ 60 | 1.402 | 550 | 1.852 | 12.480 | 7.517 | 10 / 6361.0 | equipe:garcom_hotel, salao_jogos + 8 melhorias; podia: salao_jogos |
| 25 | Q 2.929, AL 223, B 1.547, BH 1.403, E 3.200, FI 118, PA 350, F 250, M 166, H 11.731, HN 952, EM 2.175, T 2.583, PL 480, R 1.127, I 230, S 599, SU 612, VQ 102 | 1.450 | 902 | 999 | 21.140 | 13.802 | 10 / 6814.0 | 26 melhorias |
| 26 | Q 2.959, AL 269, B 1.733, BH 1.546, FI 123, PA 181, F 250, M 613, H 8.372, HN 1.131, T 2.802, PL 591, P 1.088, R 1.140, I 193, S 594, SU 765, VQ 80 | 1.457 | 850 | 924 | 21.180 | 13.821 | 10 / 7243.0 | 22 melhorias |
| 27 | Q 3.927, AL 213, B 2.317, BH 1.651, FI 138, PA 376, F 375, M 463, H 5.595, HN 1.623, T 4.074, PI 49, PL 612, P 976, R 1.289, I 122, S 628, SU 807, VQ 118 | 1.463 | 1.244 | 2.334 | 20.825 | 13.308 | 10 / 7787.0 | 18 melhorias |
| 28 | Q 4.457, AL 335, BH 1.359, E 2.976, FI 160, PA 201, M 1.086, H 9.674, HN 1.476, PL 464, R 1.373, I 227, S 627, SU 691, VQ 269 | 1.463 | 870 | 1.344 | 21.700 | 13.305 | 10 / 8419.0 | 17 melhorias |
| 29 | Q 3.579, AL 382, B 2.664, BH 1.772, FI 422, PA 167, F 300, M 556, H 10.622, HN 1.780, EM 5.200, T 4.062, PI 53, PL 605, P 785, R 1.290, I 599, S 608, SU 773, VQ 229 | 1.463 | 1.314 | 1.079 | 29.040 | 16.858 | 10 / 8941.0 | 20 melhorias |
| 30 | Q 3.857, AL 329, B 2.580, BH 1.775, FI 380, PA 557, F 560, M 686, H 8.834, HN 1.924, T 4.523, PI 110, PL 678, P 480, R 1.897, I 333, S 826, SU 791, VQ 122 | 1.470 | 1.076 | 2.019 | 27.705 | 15.830 | 10 / 9472.0 | 17 melhorias |
| 31 | Q 4.128, AL 156, B 2.760, BH 1.212, E 2.464, FI 151, PA 142, F 600, M 601, H 8.004, HN 2.234, T 5.312, PL 388, P 1.488, R 1.646, I 227, S 576, SU 400, VQ 122 | 1.473 | 1.212 | 1.504 | 26.780 | 17.471 | 10 / 10021.0 | 15 melhorias |
| 32 | Q 4.760, AL 435, B 2.597, BH 2.055, FI 143, PA 607, F 600, M 587, H 10.468, HN 2.234, T 5.782, PI 31, PL 776, P 1.588, R 1.839, I 266, S 808, SU 1.404, VQ 99 | 1.473 | 1.036 | 634 | 31.205 | 20.202 | 10 / 10595.0 | 15 melhorias |
| 33 | Q 3.913, AL 338, B 2.989, BH 2.414, FI 135, PA 275, F 600, M 437, H 10.110, HN 2.234, EM 5.200, T 5.706, PL 786, P 1.815, R 2.127, I 382, S 818, SU 1.271, VQ 416 | 1.473 | 1.060 | 2.199 | 36.400 | 21.035 | 10 / 11171.0 | 16 melhorias |
| 34 | Q 5.274, AL 350, B 3.186, BH 2.249, E 5.696, FI 144, PA 414, F 840, M 419, H 13.930, HN 2.582, T 5.699, PI 67, PL 798, P 646, R 2.056, I 184, S 800, SU 1.861, VQ 260 | 1.473 | 1.084 | 1.434 | 38.380 | 26.120 | 10 / 11812.0 | 14 melhorias |
| 35 | Q 5.615, AL 407, BH 2.075, FI 145, PA 246, M 750, H 7.790, HN 2.582, EM 5.200, PI 70, PL 643, R 2.117, I 381, S 866, SU 1.148, VQ 226 | 1.473 | 1.030 | 604 | 30.880 | 22.394 | 10 / 12402.0 | 10 melhorias |
| 36 | Q 4.727, AL 203, B 3.365, BH 1.426, FI 320, PA 195, F 900, M 449, H 7.081, HN 2.756, T 6.868, PL 480, P 997, R 1.981, I 122, S 858, SU 626, VQ 118 | 1.477 | 1.190 | 2.479 | 31.720 | 19.001 | 10 / 12939.0 | 9 melhorias |
| 37 | Q 5.528, AL 113, B 3.411, BH 1.588, E 6.656, FI 158, PA 440, F 960, M 1.037, H 8.693, HN 2.230, EM 1.429, T 7.103, PL 541, P 750, R 2.737, I 199, S 987, SU 681, VQ 237 | 1.477 | 1.110 | 894 | 35.560 | 25.438 | 10 / 13566.0 | 9 melhorias |
| 38 | Q 5.417, AL 531, B 3.917, BH 2.604, FI 145, PA 314, F 960, M 414, H 17.164, HN 2.634, T 8.278, PI 146, PL 925, P 1.934, R 2.586, I 366, S 940, SU 2.257, VQ 181 | 1.477 | 1.270 | 1.344 | 44.380 | 28.680 | 10 / 14150.0 | 9 melhorias |
| 39 | Q 5.401, AL 71, B 3.379, BH 1.513, FI 141, PA 506, F 900, M 423, H 12.961, HN 2.932, EM 5.200, T 7.478, PL 553, P 1.575, R 2.542, I 148, S 693, SU 700, VQ 286 | 1.477 | 1.114 | 2.044 | 42.440 | 29.008 | 10 / 14753.0 | 7 melhorias |
| 40 | Q 4.880, AL 332, B 3.338, BH 2.563, E 7.424, FI 142, PA 396, F 1.020, M 313, H 20.388, HN 3.556, T 9.637, PL 908, P 986, R 3.111, I 467, S 970, SU 2.263, VQ 115 | 1.477 | 1.088 | 1.464 | 53.440 | 34.348 | 10 / 15325.0 | 7 melhorias |
| 41 | Q 5.656, AL 419, B 3.565, BH 2.554, FI 150, PA 624, F 1.020, M 804, H 11.379, HN 3.652, EM 2.175, T 9.637, PL 911, P 1.563, R 2.830, I 439, S 938, SU 1.383, VQ 162 | 1.477 | 1.050 | 1.229 | 47.420 | 33.033 | 10 / 15912.0 | 5 melhorias |
| 42 | Q 5.643, AL 423, BH 2.233, FI 138, PA 264, F 360, M 348, H 24.381, HN 4.618, T 2.491, PI 36, PL 631, R 3.232, I 392, S 977, SU 1.397, VQ 216 | 1.477 | 1.074 | 2.199 | 45.900 | 30.163 | 10 / 16491.0 | 4 melhorias |
| 43 | Q 5.029, AL 450, B 4.037, BH 2.541, E 9.152, FI 142, PA 264, F 960, M 575, H 19.036, HN 4.819, T 9.177, PI 109, PL 853, P 2.008, R 3.278, I 458, S 849, SU 2.100, VQ 173 | 1.477 | 1.036 | 1.319 | 48.600 | 43.740 | 10 / 17080.0 | 4 melhorias |
| 44 | Q 5.701, AL 387, B 3.873, BH 2.608, FI 411, PA 750, F 900, M 282, H 13.763, HN 5.231, T 8.197, PL 894, P 3.048, R 4.674, I 414, S 905, SU 1.365, VQ 158 | 1.477 | 1.154 | 1.114 | 58.400 | 35.155 | 10 / 17675.0 | 4 melhorias |
| 45 | Q 2.462, B 3.475, BH 1.497, FI 409, PA 160, F 300, M 580, H 13.174, HN 4.896, EM 2.175, T 1.608, PL 529, R 4.104, I 153, S 917, SU 604, VQ 120 | 1.480 | 792 | 2.169 | 33.600 | 34.276 | 10 / 18002.0 | 2 melhorias |
| 46 | RE 1.500, Q 5.826, AL 402, B 3.123, BH 2.502, CP 150, E 10.112, FI 343, PA 686, F 1.020, M 226, H 25.698, HN 5.595, T 9.445, PL 876, P 1.920, R 3.051, I 413, S 838, SU 1.492, VQ 99 | 1.480 | 1.150 | 769 | 61.200 | 44.994 | 10 / 18602.0 | 3 melhorias |
| 47 | RE 1.000, Q 5.315, AL 581, B 3.498, BH 2.625, FI 153, PA 329, F 960, M 546, H 17.929, HN 4.896, T 8.889, PI 146, PL 930, P 1.988, R 3.327, I 389, S 887, SU 1.780, VQ 445 | 1.480 | 1.108 | 1.459 | 24.000 | 73.560 | 10 / 19219.0 | 1 melhorias |
| 48 | Q 6.070, AL 123, B 3.022, BH 1.476, FI 144, PA 347, F 1.200, M 534, H 23.046, HN 5.595, T 10.471, PL 557, P 390, R 3.735, I 139, S 993, SU 533, VQ 269 | 1.480 | 980 | 1.954 | 0 | 127.790 | 10 / 19801.0 | — |
| 49 | Q 6.090, AL 330, BH 2.199, E 10.112, FI 159, PA 366, M 443, H 19.479, HN 5.595, EM 5.800, PL 688, R 3.541, I 323, S 932, SU 1.330, VQ 299 | 1.480 | 1.192 | 1.219 | 0 | 181.585 | 10 / 20447.0 | — |
| 50 | Q 5.099, AL 333, B 3.590, BH 2.670, FI 345, PA 314, F 1.020, M 459, H 16.092, HN 5.829, T 9.406, PL 846, P 3.188, R 3.469, I 324, S 769, SU 2.258, VQ 187 | 1.480 | 976 | 1.004 | 0 | 234.324 | 10 / 21014.0 | — |
| 51 | Q 5.047, AL 477, B 3.760, BH 2.589, FI 435, PA 650, F 1.140, M 1.162, H 15.803, HN 3.497, EM 1.429, T 9.479, PL 898, P 740, R 3.695, I 458, S 941, SU 1.153, VQ 227 | 1.480 | 1.204 | 2.204 | 0 | 283.015 | 10 / 21575.0 | — |
| 52 | Q 5.328, AL 563, B 3.344, BH 2.655, E 10.112, FI 122, PA 364, F 1.020, M 108, H 28.091, HN 5.595, T 9.579, PL 943, P 426, R 3.110, I 343, S 863, SU 1.821, VQ 130 | 1.480 | 1.064 | 1.044 | 0 | 353.944 | 10 / 22133.0 | — |
| 53 | Q 5.784, AL 418, B 3.367, BH 2.612, FI 151, PA 610, F 1.020, M 629, H 16.569, HN 5.129, EM 2.175, T 9.541, PI 73, PL 933, P 3.196, R 4.950, I 453, S 877, SU 1.188, VQ 274 | 1.480 | 1.136 | 1.174 | 0 | 410.103 | 10 / 22749.0 | — |

### Proposto — dedicado, semente 0

[CSV diário completo](../../tools/ue58/balance/pacote2/results/proposto_dedicado_diario_seed0.csv).

| Dia | Renda por fonte | Salários | Estoque | Outras saídas | Investimento | Caixa final | Nível / XP | Compras / expansões compráveis |
|---|---|---|---|---|---|---|---|---|
| 1 | RE 530, Q 766 | 0 | 321 | 150 | 680 | 295 | 2 / 172.0 | equipe:atendente, kiosk_tables, drinks; podia: drinks; kiosk_tables |
| 2 | RE 420, Q 802, VQ 19 | 30 | 275 | 2 | 668 | 561 | 3 / 378.0 | neon, grill + 2 melhorias; podia: grill; neon |
| 3 | Q 1.167, VQ 72 | 32 | 556 | 5 | 900 | 307 | 4 / 548.0 | negocio:sorveteria; podia: bar |
| 4 | RE 550, Q 1.398, I 363, VQ 111 | 72 | 525 | 5 | 1.350 | 777 | 5 / 829.0 | bar + 2 melhorias; podia: bar |
| 5 | Q 1.096, B 246, BH 399, I 385, VQ 66 | 72 | 440 | 11 | 1.748 | 698 | 6 / 1100.0 | equipe:bartender, negocio:aluguel + 1 melhorias; podia: pousada |
| 6 | Q 1.583, AL 102, B 552, BH 282, I 98, VQ 110 | 162 | 701 | 11 | 2.200 | 352 | 6 / 1366.0 | negocio:surfe; podia: pousada |
| 7 | RE 1.100, Q 1.128, AL 463, B 137, BH 412, I 251, SU 689, VQ 29 | 217 | 437 | 661 | 2.488 | 757 | 7 / 1761.0 | pousada + 1 melhorias; podia: pousada |
| 8 | RE 1.100, Q 1.197, AL 437, B 508, BH 496, I 422, SU 593, VQ 106 | 220 | 457 | 143 | 2.744 | 2.052 | 8 / 2036.0 | equipe:camareira, equipe:recepcionista, pool + 3 melhorias; podia: passeios; pool |
| 9 | Q 1.526, AL 466, B 472, BH 496, PI 60, PL 163, P 934, I 252, SU 554, VQ 80 | 290 | 748 | 33 | 5.400 | 583 | 8 / 2335.0 | equipe:piscineiro, passeios, negocio:souvenir, negocio:food_truck; podia: passeios |
| 10 | Q 1.098, AL 501, B 467, BH 515, PA 184, T 432, PI 50, PL 233, I 495, S 482, SU 422, VQ 18 | 416 | 542 | 187 | 1.433 | 2.902 | 9 / 2571.0 | equipe:guia + 9 melhorias |
| 11 | Q 1.476, AL 357, B 496, BH 510, PA 407, T 1.355, PI 10, PL 233, P 1.237, I 218, S 639, SU 495, VQ 56 | 469 | 660 | 122 | 2.661 | 6.479 | 9 / 2843.0 | 17 melhorias |
| 12 | Q 1.497, AL 59, B 840, BH 377, PA 148, T 1.413, PL 145, P 104, I 136, S 631, SU 241, VQ 102 | 473 | 852 | 242 | 2.952 | 7.654 | 9 / 3130.0 | 16 melhorias |
| 13 | Q 2.061, AL 271, B 537, BH 619, PA 369, T 1.378, PI 13, PL 314, P 128, I 199, S 615, SU 449, VQ 123 | 478 | 820 | 242 | 3.841 | 9.348 | 10 / 3450.0 | 17 melhorias |
| 14 | Q 2.249, AL 311, BH 680, PA 135, T 410, PL 252, I 245, S 700, SU 694, VQ 117 | 478 | 766 | 67 | 3.936 | 9.894 | 10 / 3785.0 | 14 melhorias |
| 15 | Q 1.976, AL 419, B 839, BH 920, PA 185, F 135, T 1.487, PI 15, PL 352, P 490, I 448, S 640, SU 678, VQ 109 | 481 | 772 | 242 | 4.778 | 12.314 | 10 / 4175.0 | 14 melhorias |
| 16 | Q 2.376, AL 208, B 1.131, BH 1.024, PA 382, F 150, T 1.647, PI 45, PL 385, P 333, I 229, S 651, SU 632, VQ 82 | 484 | 1.080 | 122 | 5.655 | 14.248 | 10 / 4600.0 | 15 melhorias |
| 17 | Q 2.238, AL 358, B 1.285, BH 1.066, PA 187, F 135, T 1.782, PI 34, PL 432, P 925, I 381, S 606, SU 802, VQ 83 | 487 | 676 | 242 | 6.780 | 16.377 | 10 / 4999.0 | 16 melhorias |
| 18 | Q 2.948, AL 259, B 1.249, BH 1.103, PA 350, F 180, T 2.203, PL 458, I 222, S 597, SU 749, VQ 119 | 487 | 966 | 122 | 7.064 | 18.174 | 10 / 5431.0 | 14 melhorias |
| 19 | Q 2.316, AL 454, B 1.607, BH 1.292, PA 220, F 150, T 1.966, PI 19, PL 460, P 132, I 207, S 625, SU 941, VQ 101 | 496 | 710 | 242 | 7.880 | 19.336 | 10 / 5843.0 | 14 melhorias |
| 20 | RE 1.000, Q 2.915, AL 360, B 1.683, BH 1.240, PA 347, F 250, T 2.025, PL 489, P 1.238, I 195, S 635, SU 807, VQ 90 | 498 | 1.018 | 1.442 | 28.600 | 1.052 | 10 / 6276.0 | grand_hotel + 1 melhorias; podia: grand_hotel |
| 21 | RE 3.500, Q 3.170, AL 306, B 41, BH 1.047, E 3.200, PA 135, F 100, M 87, H 6.634, HN 357, T 683, PI 80, PL 322, R 719, I 267, S 658, SU 936, VQ 117 | 1.398 | 786 | 1.327 | 12.620 | 7.280 | 10 / 6760.0 | equipe:garcom_hotel, salao_jogos + 9 melhorias; podia: salao_jogos |
| 22 | Q 2.447, AL 349, B 2.138, BH 1.458, E 2.400, FI 350, PA 219, F 300, M 221, H 9.375, HN 833, T 2.804, PI 20, PL 488, P 1.456, R 1.113, I 194, S 626, SU 920, VQ 119 | 1.450 | 874 | 1.859 | 19.260 | 11.667 | 10 / 7208.0 | 25 melhorias |
| 23 | Q 3.193, AL 186, B 1.959, BH 1.599, E 1.600, FI 347, PA 358, F 275, M 919, H 8.620, HN 893, EM 6.400, T 2.720, PI 22, PL 545, P 840, R 1.194, I 175, S 577, SU 637, VQ 153 | 1.454 | 1.128 | 2.474 | 25.780 | 14.043 | 10 / 7720.0 | 28 melhorias |
| 24 | Q 3.838, AL 507, B 2.201, BH 1.736, E 3.584, FI 135, PA 199, F 325, M 46, H 11.624, HN 1.533, T 3.885, PI 75, PL 627, P 1.420, R 1.190, I 403, S 562, SU 873, VQ 130 | 1.454 | 1.148 | 2.464 | 27.545 | 16.325 | 10 / 8295.0 | 24 melhorias |
| 25 | Q 4.469, AL 414, B 2.159, BH 1.646, E 4.352, FI 145, PA 368, F 350, M 304, H 8.250, HN 1.861, EM 1.786, T 4.381, PL 639, R 1.878, I 359, S 550, SU 991, VQ 90 | 1.454 | 1.034 | 2.534 | 29.340 | 16.956 | 10 / 8911.0 | 22 melhorias |
| 26 | Q 4.436, AL 504, B 2.499, BH 1.877, E 4.352, FI 153, PA 161, F 560, M 508, H 6.473, HN 1.780, T 4.356, PL 653, P 1.272, R 1.507, I 706, S 589, SU 981, VQ 183 | 1.461 | 1.094 | 2.854 | 28.545 | 16.551 | 10 / 9544.0 | 19 melhorias |
| 27 | Q 5.076, AL 356, B 2.902, BH 1.921, E 4.928, FI 158, PA 548, F 640, M 879, H 8.481, HN 1.845, EM 1.786, T 5.430, PI 27, PL 689, P 1.532, R 1.601, I 260, S 751, SU 1.074, VQ 77 | 1.461 | 1.214 | 2.544 | 32.420 | 19.872 | 10 / 10174.0 | 19 melhorias |
| 28 | Q 5.882, AL 327, BH 1.615, E 4.928, FI 160, PA 228, F 200, M 334, H 12.311, HN 2.137, T 1.307, PL 570, R 1.730, I 299, S 857, SU 1.084, VQ 185 | 1.461 | 1.300 | 2.154 | 31.565 | 17.545 | 10 / 10892.0 | 16 melhorias |
| 29 | Q 4.446, AL 327, B 2.847, BH 2.136, E 4.928, FI 389, PA 288, F 640, M 358, H 14.973, HN 2.525, EM 6.400, T 5.706, PI 124, PL 723, P 1.047, R 2.078, I 391, S 631, SU 1.723, VQ 239 | 1.467 | 994 | 2.184 | 42.300 | 23.519 | 10 / 11503.0 | 19 melhorias |
| 30 | Q 5.112, AL 399, B 3.133, BH 2.345, E 5.696, FI 381, PA 520, F 960, M 1.018, H 3.182, HN 2.245, T 6.279, PL 815, P 292, R 1.842, I 223, S 810, SU 1.399, VQ 214 | 1.470 | 1.044 | 2.104 | 34.580 | 21.185 | 10 / 12134.0 | 13 melhorias |
| 31 | Q 5.327, AL 467, B 3.357, BH 2.440, E 5.696, FI 166, PA 274, F 960, M 522, H 9.841, HN 2.133, EM 1.786, T 7.241, PI 100, PL 822, P 1.866, R 2.540, I 1.165, S 641, SU 1.801, VQ 160 | 1.473 | 1.366 | 2.294 | 39.580 | 25.778 | 10 / 12775.0 | 13 melhorias |
| 32 | Q 6.474, AL 216, B 2.713, BH 1.405, E 6.080, FI 172, PA 364, F 960, M 931, H 12.051, HN 2.397, T 7.116, PL 555, P 608, R 2.563, I 226, S 801, SU 724, VQ 317 | 1.477 | 1.094 | 2.374 | 43.040 | 24.466 | 10 / 13518.0 | 12 melhorias |
| 33 | Q 5.095, AL 339, B 3.188, BH 1.587, E 6.656, FI 147, PA 221, F 960, M 756, H 16.837, HN 2.230, EM 6.400, T 7.945, PL 516, P 1.892, R 2.616, I 341, S 917, SU 885, VQ 350 | 1.477 | 1.330 | 2.564 | 47.520 | 31.452 | 10 / 14199.0 | 11 melhorias |
| 34 | Q 5.860, AL 490, B 3.981, BH 2.535, E 7.040, FI 151, PA 672, F 1.140, M 593, H 14.401, HN 3.079, T 8.790, PI 146, PL 871, P 713, R 2.599, I 590, S 1.001, SU 1.643, VQ 246 | 1.477 | 1.144 | 2.599 | 50.940 | 31.834 | 10 / 14872.0 | 9 melhorias |
| 35 | Q 5.766, AL 444, BH 2.204, E 7.424, FI 164, PA 328, F 420, M 256, H 13.006, HN 3.865, EM 2.175, T 2.474, PI 146, PL 645, R 2.568, I 369, S 955, SU 1.694, VQ 357 | 1.477 | 1.108 | 2.404 | 40.600 | 31.504 | 10 / 15570.0 | 6 melhorias |
| 36 | Q 5.220, AL 474, B 3.852, BH 2.635, E 7.808, FI 375, PA 368, F 1.080, M 567, H 9.203, HN 2.927, T 8.949, PI 73, PL 853, P 3.621, R 2.775, I 410, S 819, SU 2.629, VQ 214 | 1.477 | 1.074 | 2.464 | 43.660 | 37.681 | 10 / 16187.0 | 5 melhorias |
| 37 | Q 6.127, AL 498, B 3.756, BH 2.526, E 8.768, FI 397, PA 521, F 1.200, M 251, H 15.799, HN 4.617, EM 2.175, T 10.202, PL 871, P 3.270, R 3.122, I 414, S 942, SU 1.701, VQ 257 | 1.477 | 1.160 | 2.264 | 63.100 | 37.093 | 10 / 16849.0 | 6 melhorias |
| 38 | Q 5.282, AL 551, B 3.288, BH 2.521, CP 600, E 9.152, FI 371, PA 408, F 1.200, M 748, H 14.544, HN 3.614, T 9.421, PI 36, PL 945, R 2.195, I 553, S 886, SU 2.287, VQ 214 | 1.477 | 1.012 | 2.469 | 48.000 | 42.950 | 10 / 17517.0 | 4 melhorias |
| 39 | Q 6.180, AL 444, B 3.030, BH 2.549, E 9.536, FI 151, PA 448, F 1.200, M 528, H 25.895, HN 3.766, EM 6.400, T 9.690, PI 73, PL 953, P 2.052, R 3.847, I 566, S 797, SU 2.224, VQ 258 | 1.477 | 1.222 | 2.244 | 71.000 | 47.594 | 10 / 18218.0 | 5 melhorias |
| 40 | Q 5.265, AL 651, B 4.018, BH 2.615, E 10.112, FI 149, PA 375, F 420, M 347, H 22.398, HN 5.362, T 1.916, PI 36, PL 903, P 982, R 3.909, I 377, S 938, SU 2.495, VQ 114 | 1.477 | 1.258 | 2.624 | 52.800 | 52.817 | 10 / 18822.0 | 3 melhorias |
| 41 | RE 1.500, Q 6.089, AL 496, B 3.564, BH 2.540, E 10.112, FI 143, PA 641, F 1.140, M 244, H 13.420, HN 5.129, EM 1.786, T 9.934, PL 913, R 4.233, I 423, S 1.009, SU 2.268, VQ 294 | 1.480 | 992 | 2.629 | 66.000 | 47.593 | 10 / 19530.0 | 3 melhorias |
| 42 | RE 1.000, Q 6.910, AL 454, B 150, BH 2.181, E 10.112, FI 135, PA 284, F 360, M 715, H 23.197, HN 4.896, T 2.284, PI 36, PL 589, R 3.196, I 400, S 939, SU 2.091, VQ 242 | 1.480 | 1.074 | 2.174 | 0 | 103.036 | 10 / 20240.0 | — |
| 43 | Q 5.538, AL 502, B 3.719, BH 2.490, E 10.112, FI 153, PA 410, F 1.200, M 573, H 21.736, HN 4.896, EM 1.786, T 9.780, PI 109, PL 865, P 3.128, R 4.342, I 451, S 913, SU 2.236, VQ 324 | 1.480 | 1.240 | 2.384 | 0 | 173.195 | 10 / 20896.0 | — |
| 44 | Q 6.183, AL 618, B 3.255, BH 2.592, E 10.112, FI 439, PA 699, F 1.140, M 848, H 24.817, HN 4.663, T 9.407, PI 73, PL 898, R 4.256, I 331, S 997, SU 1.749, VQ 96 | 1.480 | 1.178 | 2.264 | 0 | 241.445 | 10 / 21553.0 | — |
| 45 | Q 5.437, AL 382, B 3.433, BH 2.461, E 10.112, FI 337, PA 267, F 1.200, M 118, H 26.800, HN 6.295, EM 1.786, T 9.857, PI 73, PL 921, P 5.245, R 2.803, I 553, S 814, SU 2.038, VH 110, VQ 66 | 1.480 | 1.370 | 2.424 | 0 | 317.279 | 10 / 22181.0 | — |
| 46 | Q 6.818, AL 509, B 3.368, BH 2.491, E 10.112, FI 156, PA 719, F 1.200, M 705, H 12.682, HN 5.129, T 10.260, PI 73, PL 867, P 2.164, R 3.533, I 368, S 806, SU 2.046, VQ 269 | 1.480 | 1.112 | 2.294 | 0 | 376.668 | 10 / 22911.0 | — |
| 47 | Q 6.153, AL 263, B 3.569, BH 1.506, E 10.112, FI 137, PA 229, F 1.140, M 642, H 15.798, HN 5.595, EM 1.786, T 9.783, PL 527, R 3.326, I 312, S 929, SU 816, VQ 522 | 1.480 | 1.342 | 2.279 | 0 | 434.712 | 10 / 23606.0 | — |
| 48 | Q 6.649, AL 476, B 3.078, BH 2.510, E 10.112, FI 140, PA 688, F 1.080, M 882, H 22.739, HN 4.197, T 9.295, PI 36, PL 884, R 3.449, I 480, S 896, SU 2.215, VQ 314 | 1.480 | 1.160 | 2.434 | 0 | 499.757 | 10 / 24325.0 | — |

## MUDANÇAS PROPOSTAS

**Não aplicadas aos JSON do jogo.** São candidatos para teste no editor, com valor atual validado pelo simulador. Os três números abaixo foram alterados somente em memória e simulados juntos; o efeito individual de cada um não foi isolado. JSON Pointer usa índices de array começando em zero.

| Arquivo em Content/Data | Campo JSON exato | Valor atual | Valor novo | Motivo |
|---|---|---|---|---|
| definitions.json | `/expansions/grand_hotel/cost` | 30000 | 28000 | Reduzir levemente a espera financeira pelo hotel, preservando fama 9 e carnaval; testar a meta de 6–10 h até hotel e tela do EA. |
| hotel_events.json | `/extra_bonus` | 0.1 | 0.15 | Valorizar a montagem opcional: cada extra passa a +15% do cachê/fama sobre a fração obrigatória; testar sem acelerar os contratos passivos. |
| customization.json | `/price_mult/4` | 30 | 24 | Suavizar o custo das melhorias finais sem mudar seus efeitos; conteúdo posterior à tela do EA permanece opcional. |

### Resultado com todas as propostas em memória

| Perfil | Marco | Dia P10 / P50 / P90 | P50 a 16 min/dia | P50 a 24 min/dia | Concluíram |
|---|---|---|---|---|---|
| casual | Grand Hotel | 26 / 27 / 31 | 7.2 h | 10.8 h | 30/30 |
| casual | Tela de fim do EA | 27 / 28 / 32 | 7.5 h | 11.2 h | 30/30 |
| casual | Campanha | 54 / 55 / 56 | 14.7 h | 22.0 h | 30/30 |
| casual | Todas as compras finitas | 52 / 53 / 55.1 | 14.1 h | 21.2 h | 30/30 |
| medio | Grand Hotel | 23 / 24 / 25.1 | 6.4 h | 9.6 h | 30/30 |
| medio | Tela de fim do EA | 24 / 25 / 26.1 | 6.7 h | 10.0 h | 30/30 |
| medio | Campanha | 47 / 48 / 49 | 12.8 h | 19.2 h | 30/30 |
| medio | Todas as compras finitas | 47 / 48 / 49 | 12.8 h | 19.2 h | 30/30 |
| dedicado | Grand Hotel | 19 / 20 / 22 | 5.3 h | 8.0 h | 30/30 |
| dedicado | Tela de fim do EA | 20 / 21 / 23 | 5.6 h | 8.4 h | 30/30 |
| dedicado | Campanha | 41 / 42 / 43 | 11.2 h | 16.8 h | 30/30 |
| dedicado | Todas as compras finitas | 41 / 42 / 43 | 11.2 h | 16.8 h | 30/30 |

O alvo é o tempo até o Grand Hotel e a tela do EA na escala real do código. A campanha continua com 4.000 vendas: este pacote não reduz sua meta para forçar uma duração menor. A conversão de 24 minutos é uma referência separada, não o tempo efetivamente simulado. As propostas não prometem duração fixa.

A tela usa uma condição C++ diferente da campanha e pode aparecer antes das 4.000 vendas; a meta solicitada deste pacote usa explicitamente hotel e tela. As correções de fama, neon, aluguel, reserva ao dormir e reinício de VIP foram recebidas da outra IA na base e estão contempladas, sem edição de Source/Data neste PR. O perfil dedicado pode chegar antes das 6 h: a meta é o perfil médio, e aumentar o hotel para atrasar o dedicado prejudicaria o casual. Medir o build antes de publicar duração na loja.
