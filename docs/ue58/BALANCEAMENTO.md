# Balanceamento do jogo completo — análise de texto e simulação

Referência fixa: **8e817f7a0813e4af628d6d317af54d50b67dbeba**, branch de origem `codex/ue58-migration`, 06/11/2026. Esta análise substitui as duas passadas antigas. Os arquivos consultados correspondem aos blobs dessa referência; os hashes SHA-256 usados na execução estão em `tools/ue58/balance/results/inputs_sha256.json`.

**É um modelo agregado de economia, não um playtest nem a execução do C++ em Python.** O resultado estima a progressão de uma política de jogo explícita. Não comprova que uma pessoa real terminará em 12–20 horas. Navegação, animações e habilidade precisam ser medidas no executável antes de aplicar as propostas.

## Reproduzir

Na raiz de um checkout com os dados do jogo:

```sh
python tools/ue58/balance_model.py --self-test
python tools/ue58/balance_model.py --days 240 --seeds 30
python tools/ue58/balance_model.py --days 240 --seeds 10 --service-scale 1.25 --out tools/ue58/balance/sensitivity_lento
python tools/ue58/balance_model.py --days 240 --seeds 10 --service-scale 0.8 --out tools/ue58/balance/sensitivity_rapido
python tools/ue58/balance/report.py
```

Cada cenário usa sementes **0–29**, com limite de 240 dias. O cenário proposto só aplica em memória os JSON Pointers de `balance/proposed.json`; rejeita uma proposta cujo valor atual não coincide com o arquivo lido. Nenhum dado do jogo é escrito. Os dois cenários usam os mesmos números de sementes; escolhas diferentes alteram o consumo posterior do gerador, portanto não são sorteios pareados de cada cliente. É usado `random.Random`, e não o `FRandomStream` da Unreal.

Saídas: `summary.json` (P10/mediana/P90 por marco e censuras), seis CSV diários completos da semente 0, seis CSV por semente, configuração da execução e hashes. Há mais sete dias após a conclusão das compras e da campanha para observar sobra de dinheiro. A tabela diária é uma trajetória reproduzível, não uma média artificial de jogadores com compras incompatíveis entre si.

## Tempo real: diferença entre o pedido e o código

`MareGame.cpp:2814` avança **1 minuto do jogo por segundo real**. Porém `MareSimulation.cpp:478` reinicia às **8h** e `AdvanceMinutes` limita o relógio a 24h. Assim, um dia completo jogado tem **960 segundos = 16 minutos reais**. O primeiro save começa às 6h30, uma diferença inicial de até 1,5 minuto que a aproximação diária não conta. Pausas e tempo com menus pausados também não estão no cálculo.

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
| Fama | `MareSimulation.cpp:374`, `:416` | Limiares extraídos do C++: 0, 100, 250, 450, 700, 1000, 1400, 1900, 2500, 3200. Venda dá 2 XP, mais receita alta e beleza; capítulos +80. Negativos são ignorados no código atual. |
| Expansões e capítulos | `definitions.json`; `MareSimulation.cpp:277`, `:348`, `:807` | Respeita pré-requisitos, fama, capítulo, pagamentos, entregas e contagem de vendas durante o passo ativo. Compra de negócio não exige pousada. Recompensas não se repetem. |
| Salários e manutenção | `definitions.json/staff_rules`; `MareStaff.cpp:92`, `:140`, `:153`; `MareSimulation.cpp:444`, `:583` | Um empregado por cargo não legado; integral, folga aos domingos (hipótese de escala), XP, reajustes, fadiga/ausências. Funcionário dos negócios é padrão na aquisição. Manutenção: 0,5% dos preços das expansões por dia; hotel tem mais R$ 900 fixos de equipe. |
| Bar | `bar.json`, operações horárias; `MareBar.cpp:170`, `:390` | Receita por bebida + gorjeta/preparo manual; bartender ganha 85%, erra por nível e aprende uma receita a cada dois dias; ingredientes, gelo derretendo, cinco linhas de upgrades. Renda horária genérica do bar existe além dos drinks. Filas/paciência são agregadas. |
| Piscina | `pool.json`; `MarePool.cpp:39`, `:68` | Folhas, toalhas, chuva, limpeza, avaliação e picolés; renda horária × limpeza, conforto, fama, clima e sorteio. Sorveteria produz picolés pagos; cooler tem limite. |
| Pousada e hotel | `customization.json/operations`, `hotel_rooms.json`; `MareStays.cpp:53`, `:82`, `:125`, `:165` | Fila, perfil, limite/oferta, diárias antecipadas por todas as noites, capacidade, check-out, limpeza e ocupação por estado. Hotel tem 2 suítes, 10 luxo, 20 standard; fallback de quarto conforme o código. Receita não é a antiga hipótese de ocupação × diária × 30%. |
| Frigobar e VIP | `hotel_rooms.json`; `MareHotelRooms.cpp:90`, `:150`, `:201` | Consumo sorteado no check-out, cobrança e reposição posterior; reclamações com prazo/custo, um pedido VIP por marca no quarto (bug: não é reiniciada por estadia), gorjeta/fama presencial nos três visitáveis. |
| Restaurante e eventos | `restaurant.json`; `MareRestaurant.cpp:109`, `:125`; `MareSimulation.cpp:395` | Seis mesas, serviços, cozinha, room service, equipe a 70% ou garçom a 90%; reservas pagas no dia anterior, receita às 21h por usar `Started == event_hour`. Refeições noturnas genéricas do hotel são contabilizadas separadamente. |
| Passeios | `tours.json`, `customization.json/operations/tours`; `MareTours.cpp:145`, `:245`, `:284` | Três janelas de procura em grupos, assentos, guia, mar bravo cancela passeios no mar, bilhetes, custo por saída, gorjeta, nota, fotos e boca a boca. Jangada depende de roteiro nível 3. Bilheteria e duração são agregadas por dia. |
| Negócios | `business_games.json`; `MareBusiness.cpp`, `MareBizCommon.cpp`, `MareIceCream.cpp`, `MarePastel.cpp`, `MareRental.cpp`, `MareSouvenir.cpp` | Filas por cliente, funcionário a 60%, sabores/bolas, pastel e caldo, aluguel/devolução/multa/resgate, artesanato e postais com custo, surf por hora, níveis e multiplicadores reais. Não soma renda horária fictícia às quatro filas. |
| Salão | `game_room.json`, `business_games.json`; `MareBusiness.cpp:63`, `MarePoolCup.cpp`, `MareArcade.cpp:208`, `MareGameRoom.cpp:324`, `MareFoosball.cpp`, `MareTableTennis.cpp` | Fichas por ocupação e espectadores, apostas, partidas, duas máquinas dividindo a recompensa do mesmo id por hora, torneio semanal de três rodadas com taxa e prêmios. Desempenho é sorteio por perfil, sem simular física. |
| Lazer, tutorial e humor | `leisure.json`, `tutorial.json`; `MareLeisure.cpp`, `MareSummitWorld.cpp`, `MareComicEvents.cpp` | Pesca/foto fornecem itens/flags de história e fama; dicas são apresentação, não fonte de renda. Visitas narrativas são hipótese. Efeitos pontuais dos eventos cômicos não recebem renda inventada. |
| Arquivos ausentes | Inventário do commit | Não existem `hotel_events.json` ou `MareHotelEvents.cpp`. Pedidos especiais ficam em `hotel_rooms.json`; contratos de eventos, em `restaurant.json`. Montagem física de casamento e crítico gastronômico seguem pendentes no checklist. |

### Hipóteses dos três perfis

Os valores abaixo não vieram de telemetria. Estão expostos em `profiles.json` para substituição após teste.

| Perfil | Ações ativas/dia, incluindo morro | Sucesso por etapa | Atende tentativas do quiosque | Evento do hotel a cada | Guia passeio a cada | Chance de vitória |
|---|---|---|---|---|---|---|
| casual | 360 s | 0.5 | 0.65 | 7 dias | 7 dias | 0.35 |
| medio | 600 s | 0.72 | 0.8 | 3 dias | 3 dias | 0.55 |
| dedicado | 840 s | 0.9 | 0.95 | 1 dias | 1 dias | 0.75 |

O restante do dia é deslocamento, observação, espera ou atividades sem receita contada. A equipe atua em paralelo. O orçamento manual é único: quiosque, bar, recepção, minijogos, piscina, partidas e queixas disputam os mesmos segundos. Passeios e campeonato reservam tempo antes das tarefas opcionais. Tempo por ação é hipótese (8–35 s; passeio 120 s; partida de torneio 90 s). O atendente tem capacidade inicial de um produto a cada 11 s, afetada pelo balcão; há sensibilidade abaixo.

Política de investimento: reserva de R$ 100/250/1.200 conforme estágio; cargos elegíveis, expansões na ordem dos dados, negócios baratos e melhorias de menor custo. Melhorias usam até 30% do caixa disponível antes do hotel e 65% depois, com uma etapa por slot por dia. Isso é uma política reproduzível, não a estratégia ótima. O jogador cobra preços de referência e não explora o limite de 200% do preço. Decoração comprada fica equipada no maior nível. Ações narrativas ocorrem ao iniciar/fechar o dia; progressão intradiária é aproximada.

A recepção/limpeza de pousada, chegadas de bar e restaurante e tempos de expiração são discretizados por hora: a fila contínua e a navegação não são reproduzidas. No restaurante, o tempo manual vira participação com gorjeta média de 5%; nas mesas reais depende de `Waited`. A preparação do bar usa uma nota média por perfil; gostos, fregueses e tempo exato não são emulados. No passeio não se simulam individualmente todas as opções de extras, golfinhos, colisão no coral ou remarcações; a política cancela mar bravo e usa notas agregadas. A limpeza manual completa de quarto com bônus `polished` não é modelada: a equipe limpa, e o jogador pode resolver queixas nos visitáveis. A probabilidade de responder queixa resume atraso dentro da hora. Estoque do quiosque, bar, frigobar, artesanato, postais e picolés têm desembolsos próprios; **não se inventou CMV de pastel, casquinha ou pratos do restaurante, pois suas funções de venda não o cobram**.

## Resultado atual: 30 sementes por perfil

| Perfil | Marco | Dia P10 / P50 / P90 | P50 a 16 min/dia | P50 a 24 min/dia | Concluíram |
|---|---|---|---|---|---|
| casual | Grand Hotel | 31 / 32 / 36 | 8.5 h | 12.8 h | 30/30 |
| casual | Tela de fim do EA | 32 / 33 / 37 | 8.8 h | 13.2 h | 30/30 |
| casual | Campanha | 66 / 67 / 68.1 | 17.9 h | 26.8 h | 30/30 |
| casual | Todas as compras finitas | 58 / 59.5 / 62 | 15.9 h | 23.8 h | 30/30 |
| medio | Grand Hotel | 26 / 27 / 30 | 7.2 h | 10.8 h | 30/30 |
| medio | Tela de fim do EA | 27 / 28 / 31 | 7.5 h | 11.2 h | 30/30 |
| medio | Campanha | 56 / 57 / 59 | 15.2 h | 22.8 h | 30/30 |
| medio | Todas as compras finitas | 51.9 / 53 / 55 | 14.1 h | 21.2 h | 30/30 |
| dedicado | Grand Hotel | 23 / 24 / 25 | 6.4 h | 9.6 h | 30/30 |
| dedicado | Tela de fim do EA | 24 / 25 / 26 | 6.7 h | 10.0 h | 30/30 |
| dedicado | Campanha | 49 / 49.5 / 50.1 | 13.2 h | 19.8 h | 30/30 |
| dedicado | Todas as compras finitas | 44 / 45.5 / 46.1 | 12.1 h | 18.2 h | 30/30 |

A meta de 12–20 horas é plausível para a **campanha do médio na escala efetiva de 16 minutos**, sob estas hipóteses. Já a tela de fim do EA chega antes e a conversão de 24 minutos alonga a campanha. Comprar o catálogo inteiro e concluir a campanha também podem ocorrer em ordem diferente. Não publicar uma duração na loja com base apenas nesta planilha de simulação.

## Quando as expansões ficam disponíveis e são compradas

Disponível = pré-requisitos/fama/capítulo alcançados; comprada = pagou mantendo reserva e a política de compras. São medianas em dias, não datas prometidas. Uma cadeia pode ficar disponível na mesma rodada de compras do fechamento.

### Cenário atual

| Expansão | Casual: disponível → comprada | Médio: disponível → comprada | Dedicado: disponível → comprada |
|---|---|---|---|
| Mesas e guarda-sóis | 1 → 1 | 1 → 1 | 1 → 1 |
| Licença de drinks | 1 → 2 | 1 → 2 | 1 → 1 |
| Letreiro neon | 1 → 2 | 1 → 2 | 1 → 2 |
| Chapa de petiscos | 1 → 3 | 1 → 2 | 1 → 2 |
| Bar do Coqueiro | 3 → 7 | 2 → 4 | 2 → 4 |
| Pousada: recepção + bangalô | 7 → 11 | 4 → 8 | 4 → 7 |
| Piscina | 11 → 13 | 8 → 10 | 7 → 8 |
| Passeios turísticos | 11 → 14 | 8 → 11 | 7 → 9 |
| Grand Hotel Maré Alta 5★ | 20 → 32 | 15 → 27 | 12 → 24 |
| Salão de jogos do hotel | 32 → 33 | 27 → 28 | 24 → 25 |

### Cenário proposto

| Expansão | Casual: disponível → comprada | Médio: disponível → comprada | Dedicado: disponível → comprada |
|---|---|---|---|
| Mesas e guarda-sóis | 1 → 1 | 1 → 1 | 1 → 1 |
| Licença de drinks | 1 → 2 | 1 → 2 | 1 → 1 |
| Letreiro neon | 1 → 2 | 1 → 2 | 1 → 2 |
| Chapa de petiscos | 1 → 3 | 1 → 2 | 1 → 2 |
| Bar do Coqueiro | 3 → 7 | 2 → 4 | 2 → 4 |
| Pousada: recepção + bangalô | 7 → 11 | 4 → 8 | 4 → 7 |
| Piscina | 11 → 13 | 8 → 10 | 7 → 8 |
| Passeios turísticos | 11 → 14 | 8 → 11 | 7 → 9 |
| Grand Hotel Maré Alta 5★ | 20 → 29.5 | 15 → 24 | 12 → 20 |
| Salão de jogos do hotel | 29.5 → 30.5 | 24 → 25 | 20 → 21 |

## Capítulos, negócios e experiências observadas

| Marco atual: dia mediano (execuções que atingiram) | Casual | Médio | Dedicado |
|---|---|---|---|
| capitulo:pier | 1 (30/30) | 1 (30/30) | 1 (30/30) |
| capitulo:prainha | 3 (30/30) | 2 (30/30) | 2 (30/30) |
| capitulo:sabores | 12.5 (30/30) | 8.5 (30/30) | 7 (30/30) |
| capitulo:carnaval | 12.5 (30/30) | 8.5 (30/30) | 8 (30/30) |
| negocio:aluguel | 9 (30/30) | 7 (30/30) | 6 (30/30) |
| negocio:food_truck | 15 (30/30) | 11.5 (30/30) | 10 (30/30) |
| negocio:sorveteria | 4 (30/30) | 5 (30/30) | 3 (30/30) |
| negocio:souvenir | 13.5 (30/30) | 10 (30/30) | 9 (30/30) |
| negocio:surfe | 16 (30/30) | 12 (30/30) | 11 (30/30) |
| bar_secreto | 13 (27/30) | 6 (30/30) | 5 (30/30) |
| passeio:jangada | 34 (30/30) | 30 (30/30) | 27 (30/30) |
| vip_hotel_atendido | 33 (30/30) | 28 (30/30) | 25 (30/30) |
| evento:aniversario | 50 (30/30) | 37 (30/30) | 27 (30/30) |
| evento:casamento | 36 (30/30) | 31 (30/30) | 25 (30/30) |
| evento:empresa | 43 (30/30) | 34 (30/30) | 26 (30/30) |
| campeonato_inscrito | 43 (27/30) | 30 (30/30) | 29 (30/30) |
| fliperamas_jogados | não observado | não observado | não observado |

Medianas de experiências só usam quem as viveu; a contagem evita transformar uma experiência opcional rara em uma conclusão garantida.

## Renda dominante, retorno e paredes

A tabela abaixo descreve a **semente 0 do médio**. Receita é entrada de caixa, portanto diárias incluem antecipação de várias noites; não confundir com lucro por competência. Fase pós-hotel começa no dia seguinte à compra; os sete dias finais permitem observar a renda depois das compras.

### Renda por fase — atual

| Fase | Dias amostrados | Receita média/dia (R$) | Saldo antes de investimentos/dia (R$) | Quatro maiores parcelas da receita |
|---|---|---|---|---|
| Antes do hotel | 27 | 5.258 | 4.248 | quiosque: 24%, passeios: 15%, bar_drinks: 13%, bar_passivo: 11% |
| Hotel até todas as compras | 26 | 41.453 | 37.861 | hotel_diarias: 30%, passeios: 13%, quiosque: 9%, eventos_hotel: 8% |
| Após todas as compras | 9 | 61.789 | 58.092 | hotel_diarias: 33%, passeios: 14%, eventos_hotel: 10%, hotel_refeicoes_noturnas: 8% |

Maior intervalo sem compra antes de completar o catálogo: **nenhum** (0 dias). Depois do catálogo, caixa passou de **R$ 54.652** para **R$ 577.480** no dia 62. Isso revela ausência de uso finito adicional do dinheiro; receita diária continua entrando.

### Renda por fase — proposto

| Fase | Dias amostrados | Receita média/dia (R$) | Saldo antes de investimentos/dia (R$) | Quatro maiores parcelas da receita |
|---|---|---|---|---|
| Antes do hotel | 25 | 4.696 | 3.726 | quiosque: 25%, passeios: 13%, bar_drinks: 12%, bar_passivo: 11% |
| Hotel até todas as compras | 24 | 39.203 | 35.591 | hotel_diarias: 33%, passeios: 13%, quiosque: 9%, hotel_refeicoes_noturnas: 7% |
| Após todas as compras | 6 | 66.465 | 62.706 | hotel_diarias: 39%, passeios: 14%, hotel_refeicoes_noturnas: 7%, quiosque: 6% |

Maior intervalo sem compra antes de completar o catálogo: **nenhum** (0 dias). Depois do catálogo, caixa passou de **R$ 73.294** para **R$ 449.527** no dia 55. Isso revela ausência de uso finito adicional do dinheiro; receita diária continua entrando.


- **Casamento domina os contratos:** no valor atual, custo 2.200, renda 5.600, saldo base 3.400 (154,5% do custo), contra 1.000 no aniversário e 1.500 no jantar de empresa. A decoração ainda multiplica toda a renda. Depois de experimentar os três, a política escolhe o melhor saldo. Não há minijogo de montagem limitando esse retorno.
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
| 8,8 s/produto | atual | 51 | 13.6 h | 20.4 h |
| 8,8 s/produto | proposto | 43.5 | 11.6 h | 17.4 h |
| 11 s/produto | atual | 57 | 15.2 h | 22.8 h |
| 11 s/produto | proposto | 49 | 13.1 h | 19.6 h |
| 13,75 s/produto | atual | 63 | 16.8 h | 25.2 h |
| 13,75 s/produto | proposto | 54 | 14.4 h | 21.6 h |

A variação de habilidade e deslocamento pode ser maior que a variação entre sementes. Antes de aceitar os números propostos, medir pelo menos três sessões completas do perfil médio: tempo por produto, vendas/dia, tempo fora do quiosque, partidas e ocupação. Registrar também quando o jogador dorme mais cedo. Aumentar o número de sementes não corrige uma hipótese errada de capacidade.

## Tabelas dia a dia

Valores em R$, arredondados nesta apresentação. **Q** quiosque; **VQ** VIP do quiosque; **B** drinks; **BH** bar por hora; **P** pousada; **H** diárias do hotel; **HN** refeições noturnas; **M** frigobar; **VH** VIP hotel; **R** restaurante; **E** contratos do hotel; **T** passeios; **F** fotos; **PL** piscina; **PI** picolés; **I** sorveteria; **PA** pastel; **AL** aluguel; **S** souvenir; **SU** surfe; **FI** fichas; **PE** pebolim; **AR** fliperama; **AP** partidas/apostas recebidas; **CP** campeonato; **RE** recompensas. Fonte ausente na célula = zero, não desconhecida.

Salários incluem equipe contratada, funcionários dos negócios e R$ 900 da equipe fixa do hotel. Estoque reúne todos os desembolsos com prefixo `estoque_`. Outras despesas incluem manutenção, passeios, queixas, preparativos e taxas/perdas em partidas. Investimentos são as aquisições finitas. O CSV preserva cada categoria, centavos, caixa inicial, evento, chuva, ocupação, vendas acumuladas, todas as compras e as expansões que eram compráveis antes de gastar no fechamento. Como as células são arredondadas, a conciliação exata deve usar o CSV.

### Atual — casual, semente 0

[CSV diário completo](../../tools/ue58/balance/results/atual_casual_diario_seed0.csv).

| Dia | Renda por fonte | Salários | Estoque | Outras saídas | Investimento | Caixa final | Nível / XP | Compras / expansões compráveis |
|---|---|---|---|---|---|---|---|---|
| 1 | RE 370, Q 274 | 0 | 126 | 150 | 240 | 278 | 2 / 118.0 | equipe:atendente; podia: drinks; kiosk_tables |
| 2 | RE 280, Q 410, VQ 19 | 30 | 111 | 0 | 440 | 406 | 2 / 216.0 | kiosk_tables, drinks; podia: drinks; kiosk_tables |
| 3 | RE 300, Q 548, VQ 29 | 32 | 245 | 2 | 593 | 411 | 3 / 382.0 | neon, grill + 1 melhorias; podia: grill; neon |
| 4 | RE 350, Q 768 | 32 | 378 | 5 | 900 | 214 | 4 / 482.0 | negocio:sorveteria |
| 5 | Q 705, I 189, VQ 50 | 72 | 331 | 5 | 150 | 600 | 4 / 592.0 | 2 melhorias |
| 6 | RE 200, Q 662, I 190, VQ 56 | 75 | 105 | 5 | 1.200 | 322 | 5 / 706.0 | bar; podia: bar |
| 7 | Q 628, B 14, BH 389, I 180, VQ 40 | 75 | 230 | 11 | 423 | 835 | 5 / 819.0 | equipe:bartender + 2 melhorias |
| 8 | Q 690, B 344, BH 438, I 354 | 117 | 527 | 131 | 1.488 | 398 | 5 / 923.0 | negocio:aluguel + 1 melhorias |
| 9 | Q 1.003, AL 228, B 301, BH 466, I 172, VQ 13 | 165 | 324 | 11 | 497 | 1.583 | 6 / 1060.0 | 5 melhorias |
| 10 | RE 300, Q 702, AL 348, B 396, BH 483, I 339, VQ 21 | 165 | 360 | 131 | 2.520 | 997 | 6 / 1173.0 | pousada + 1 melhorias; podia: pousada |
| 11 | RE 1.900, Q 816, AL 243, B 450, BH 458, I 185, VQ 48 | 167 | 372 | 673 | 2.460 | 1.424 | 7 / 1463.0 | equipe:camareira, equipe:recepcionista, pool; podia: passeios; pool |
| 12 | Q 755, AL 233, B 432, BH 483, PL 148, P 682, I 150 | 241 | 216 | 153 | 2.388 | 1.309 | 7 / 1585.0 | equipe:piscineiro, passeios + 3 melhorias; podia: passeios |
| 13 | Q 876, AL 254, B 558, BH 503, PI 50, PL 201, I 160, VQ 126 | 277 | 516 | 162 | 2.168 | 914 | 7 / 1745.0 | equipe:guia, negocio:souvenir + 2 melhorias |
| 14 | Q 918, AL 173, BH 413, T 297, PI 40, PL 149, I 138, S 588, VQ 42 | 362 | 490 | 67 | 1.944 | 809 | 7 / 1874.0 | negocio:food_truck + 1 melhorias |
| 15 | Q 655, AL 53, B 625, BH 304, PA 109, T 690, PL 121, P 550, I 76, S 633, VQ 30 | 414 | 510 | 242 | 2.500 | 989 | 8 / 1988.0 | negocio:surfe + 2 melhorias |
| 16 | Q 972, AL 266, B 655, BH 538, PA 387, T 1.260, PL 236, P 556, I 183, S 555, SU 270, VQ 62 | 473 | 564 | 122 | 1.500 | 4.270 | 8 / 2138.0 | 10 melhorias |
| 17 | Q 803, AL 333, B 510, BH 572, PA 193, T 1.260, PL 251, P 623, I 207, S 597, SU 294, VQ 23 | 478 | 630 | 242 | 2.451 | 6.135 | 8 / 2265.0 | 14 melhorias |
| 18 | Q 1.170, AL 226, B 605, BH 582, PA 350, T 1.270, PL 264, I 186, S 582, SU 306, VQ 60 | 484 | 528 | 122 | 2.893 | 7.708 | 8 / 2441.0 | 14 melhorias |
| 19 | Q 1.043, AL 317, B 940, BH 738, PA 201, T 1.260, PL 302, P 363, I 171, S 569, SU 428, VQ 91 | 490 | 644 | 242 | 3.608 | 9.147 | 9 / 2629.0 | 15 melhorias |
| 20 | Q 1.354, AL 46, B 963, BH 451, PA 263, F 150, T 1.453, PL 192, P 302, I 42, S 560, SU 194, VQ 69 | 490 | 778 | 242 | 3.880 | 9.796 | 9 / 2804.0 | 13 melhorias |
| 21 | Q 1.409, AL 196, BH 726, PA 180, F 45, T 456, PL 244, I 150, S 679, SU 341 | 490 | 424 | 67 | 3.896 | 9.344 | 9 / 3012.0 | 11 melhorias |
| 22 | Q 1.402, AL 341, B 1.310, BH 1.024, PA 156, F 135, T 1.600, PL 335, P 1.431, I 384, S 527, SU 548, VQ 102 | 490 | 654 | 242 | 4.875 | 12.378 | 10 / 3248.0 | 13 melhorias |
| 23 | Q 1.728, AL 227, B 1.277, BH 1.095, PA 367, F 150, T 1.798, PL 464, I 174, S 581, SU 511, VQ 126 | 496 | 864 | 122 | 5.460 | 13.933 | 10 / 3510.0 | 13 melhorias |
| 24 | Q 1.330, AL 162, B 1.186, BH 1.152, PA 176, F 120, T 1.712, PI 18, PL 463, I 184, S 536, SU 568, VQ 50 | 498 | 518 | 242 | 5.600 | 14.732 | 10 / 3726.0 | 12 melhorias |
| 25 | Q 1.812, AL 211, B 1.374, BH 1.150, PA 459, F 120, T 1.840, PI 57, PL 463, I 215, S 598, SU 430, VQ 86 | 502 | 686 | 122 | 6.454 | 15.782 | 10 / 3977.0 | 12 melhorias |
| 26 | Q 1.510, AL 289, B 1.501, BH 1.243, PA 165, F 120, T 1.746, PL 529, P 777, I 167, S 588, SU 545, VQ 95 | 502 | 624 | 242 | 6.510 | 17.180 | 10 / 4207.0 | 11 melhorias |
| 27 | Q 1.871, AL 235, B 1.545, BH 1.300, PA 336, F 225, T 2.026, PI 20, PL 491, P 828, I 169, S 605, SU 548, VQ 118 | 505 | 756 | 242 | 7.460 | 18.533 | 10 / 4475.0 | 11 melhorias |
| 28 | Q 1.860, AL 169, BH 1.155, PA 188, F 100, T 812, PL 359, I 135, S 635, SU 484, VQ 54 | 505 | 502 | 67 | 6.770 | 16.639 | 10 / 4718.0 | 9 melhorias |
| 29 | Q 1.481, AL 115, B 1.991, BH 883, PA 92, F 200, T 1.983, PL 294, P 1.274, I 74, S 509, SU 350, VQ 182 | 505 | 738 | 242 | 6.720 | 17.863 | 10 / 4958.0 | 8 melhorias |
| 30 | Q 1.841, AL 264, B 1.859, BH 1.558, PA 332, F 250, T 2.733, PI 43, PL 523, I 170, S 596, SU 592, VQ 100 | 505 | 470 | 122 | 7.680 | 19.947 | 10 / 5215.0 | 9 melhorias |
| 31 | RE 1.000, Q 1.947, AL 279, B 2.513, BH 1.586, PA 201, F 250, T 2.802, PI 67, PL 572, P 941, I 202, S 531, SU 737, VQ 54 | 505 | 712 | 242 | 30.000 | 2.169 | 10 / 5496.0 | grand_hotel; podia: grand_hotel |
| 32 | RE 3.500, Q 2.278, AL 217, B 2.374, BH 1.606, PA 432, F 250, H 8.310, HN 595, T 2.713, PL 523, R 813, I 197, S 547, SU 517, VQ 182 | 1.411 | 642 | 622 | 15.180 | 9.370 | 10 / 5814.0 | equipe:garcom_hotel, salao_jogos + 9 melhorias; podia: salao_jogos |
| 33 | Q 1.718, AL 366, B 1.894, BH 1.651, FI 120, PA 143, F 325, M 278, H 5.551, HN 800, T 4.176, PI 96, PL 589, P 1.161, R 1.340, I 182, S 548, SU 642, VQ 36 | 1.462 | 760 | 1.144 | 17.060 | 10.559 | 10 / 6124.0 | 17 melhorias |
| 34 | Q 2.515, AL 225, B 2.416, BH 1.585, FI 134, PA 432, F 300, M 295, H 9.923, HN 1.328, T 3.835, PL 630, P 1.848, R 1.217, I 188, S 565, SU 624, VQ 98 | 1.469 | 782 | 614 | 21.375 | 14.477 | 10 / 6474.0 | 18 melhorias |
| 35 | Q 2.792, AL 217, BH 1.438, FI 129, PA 111, F 125, M 516, H 10.024, HN 1.618, T 1.061, PL 408, R 974, I 218, S 665, SU 547, VQ 126 | 1.469 | 632 | 2.689 | 19.370 | 11.285 | 10 / 6841.0 | 15 melhorias |
| 36 | Q 2.172, AL 394, B 2.785, BH 1.831, E 7.616, FI 148, PA 197, F 520, M 406, H 6.536, HN 1.537, T 4.536, PI 106, PL 627, P 948, R 1.751, I 307, S 561, SU 695, VQ 74 | 1.469 | 922 | 829 | 25.520 | 16.293 | 10 / 7188.0 | 17 melhorias |
| 37 | Q 3.290, AL 306, B 2.513, BH 1.923, FI 409, PA 457, F 520, M 437, H 10.024, HN 1.741, T 4.910, PI 27, PL 651, P 690, R 1.414, I 272, S 764, SU 800, VQ 207 | 1.469 | 934 | 379 | 27.775 | 17.092 | 10 / 7599.0 | 16 melhorias |
| 38 | Q 1.905, AL 469, B 2.492, BH 1.994, FI 159, PA 311, F 120, M 598, H 11.440, HN 1.651, T 846, PI 28, PL 707, R 1.540, I 311, S 728, SU 763, VQ 192 | 1.473 | 856 | 474 | 24.000 | 16.543 | 10 / 7884.0 | 13 melhorias |
| 39 | Q 3.434, AL 309, B 3.077, BH 2.023, FI 135, PA 546, F 560, M 207, H 11.057, HN 2.040, T 5.259, PI 116, PL 712, P 1.194, R 1.495, I 342, S 849, SU 874, VQ 196 | 1.473 | 924 | 404 | 29.200 | 18.966 | 10 / 8297.0 | 14 melhorias |
| 40 | Q 2.938, AL 156, B 2.817, BH 1.327, FI 130, PA 142, F 560, M 104, H 14.298, HN 2.525, T 5.473, PL 444, P 1.074, R 1.325, I 243, S 697, SU 383, VQ 158 | 1.473 | 808 | 484 | 31.985 | 19.010 | 10 / 8646.0 | 14 melhorias |
| 41 | Q 3.658, AL 92, B 2.576, BH 1.286, FI 143, PA 222, F 560, M 666, H 2.449, HN 2.582, T 5.793, PL 470, P 2.240, R 2.469, I 102, S 819, SU 446, VQ 202 | 1.473 | 644 | 624 | 26.540 | 16.503 | 10 / 9073.0 | 10 melhorias |
| 42 | Q 3.260, AL 126, BH 1.162, FI 161, PA 112, F 200, M 530, H 12.487, HN 2.582, T 1.608, PL 311, R 1.467, I 196, S 797, SU 380, VQ 34 | 1.473 | 1.042 | 1.369 | 22.340 | 15.692 | 10 / 9421.0 | 8 melhorias |
| 43 | Q 3.539, AL 122, B 2.761, BH 1.391, E 4.272, FI 160, PA 95, F 560, M 441, H 9.046, HN 2.694, T 5.738, PL 433, P 606, R 1.333, I 359, S 687, SU 490, VQ 54 | 1.473 | 754 | 674 | 27.280 | 20.293 | 10 / 9815.0 | 9 melhorias |
| 44 | Q 3.433, AL 327, B 3.514, BH 2.260, FI 371, PA 718, F 840, M 708, H 11.233, HN 2.397, T 6.191, PI 33, PL 829, R 2.857, I 426, S 921, SU 910, VQ 87 | 1.477 | 1.046 | 454 | 34.560 | 20.810 | 10 / 10205.0 | 10 melhorias |
| 45 | Q 3.650, AL 965, B 3.133, BH 2.417, FI 152, PA 402, F 900, M 560, H 9.652, HN 2.230, T 6.981, PL 866, P 3.154, R 1.962, I 839, S 842, SU 915, VQ 68 | 1.477 | 876 | 504 | 34.280 | 23.361 | 10 / 10595.0 | 9 melhorias |
| 46 | Q 4.054, AL 479, B 3.166, BH 2.610, FI 146, PA 541, F 900, M 321, H 16.046, HN 2.911, T 7.491, PI 35, PL 884, R 2.857, I 288, S 931, SU 1.174, VQ 44 | 1.477 | 982 | 444 | 41.340 | 23.996 | 10 / 10990.0 | 9 melhorias |
| 47 | Q 1.865, AL 217, B 3.367, BH 1.550, FI 137, PA 189, F 180, M 762, H 8.936, HN 3.519, T 1.125, PL 573, P 1.425, R 2.656, I 168, S 869, SU 691, VQ 120 | 1.477 | 560 | 514 | 26.620 | 23.173 | 10 / 11214.0 | 5 melhorias |
| 48 | Q 3.819, AL 345, B 3.663, BH 2.635, FI 158, PA 562, F 840, M 716, H 15.057, HN 3.079, T 7.707, PI 36, PL 838, P 1.843, R 1.532, I 430, S 910, SU 1.337, VQ 191 | 1.477 | 1.088 | 594 | 36.800 | 28.911 | 10 / 11630.0 | 6 melhorias |
| 49 | Q 3.982, AL 111, BH 1.256, FI 155, PA 197, F 360, M 666, H 13.948, HN 3.092, T 2.191, PL 359, R 2.402, I 115, S 1.040, SU 452, VQ 210 | 1.477 | 1.110 | 1.004 | 35.200 | 20.656 | 10 / 12020.0 | 5 melhorias |
| 50 | Q 3.667, AL 452, B 3.147, BH 2.672, E 3.904, FI 143, PA 299, F 780, M 264, H 24.385, HN 4.065, T 7.578, PI 73, PL 856, P 1.846, R 2.380, I 421, S 816, SU 1.239, VQ 180 | 1.477 | 914 | 444 | 41.500 | 35.488 | 10 / 12410.0 | 5 melhorias |
| 51 | Q 4.128, AL 417, B 3.310, BH 2.584, FI 371, PA 644, F 960, M 569, H 14.451, HN 4.047, T 8.523, PI 109, PL 882, P 386, R 3.325, I 294, S 952, SU 1.225, VQ 210 | 1.477 | 746 | 444 | 41.600 | 38.609 | 10 / 12832.0 | 4 melhorias |
| 52 | Q 3.832, AL 369, B 3.841, BH 2.464, FI 146, PA 324, F 1.020, M 569, H 14.394, HN 4.425, T 9.445, PI 73, PL 896, P 4.775, R 2.979, I 370, S 837, SU 1.446, VQ 79 | 1.477 | 1.078 | 524 | 47.900 | 39.915 | 10 / 13209.0 | 4 melhorias |
| 53 | Q 4.045, AL 268, B 3.591, BH 2.591, FI 146, PA 546, F 960, M 301, H 13.046, HN 5.422, T 9.138, PL 909, R 2.471, I 352, S 884, SU 1.467, VQ 185 | 1.480 | 928 | 504 | 42.500 | 40.825 | 10 / 13602.0 | 3 melhorias |
| 54 | Q 3.492, AL 484, B 4.096, BH 2.630, FI 162, PA 321, F 960, M 685, H 6.403, HN 3.815, T 9.407, PL 892, P 462, R 2.925, I 424, S 907, SU 1.527, VQ 93 | 1.480 | 824 | 519 | 45.000 | 32.687 | 10 / 13991.0 | 3 melhorias |
| 55 | Q 3.808, AL 294, B 3.042, BH 2.545, FI 152, PA 751, F 960, M 501, H 32.867, HN 4.394, T 9.137, PI 109, PL 924, P 1.924, R 3.225, I 363, S 957, SU 1.166, VQ 199 | 1.480 | 1.010 | 524 | 55.500 | 41.490 | 10 / 14426.0 | 3 melhorias |
| 56 | Q 3.627, AL 443, BH 2.209, FI 166, PA 351, F 300, M 631, H 15.087, HN 5.362, T 1.903, PL 635, R 2.376, I 368, S 958, SU 1.136, VQ 191 | 1.480 | 880 | 2.569 | 42.000 | 30.305 | 10 / 14797.0 | 2 melhorias |
| 57 | Q 3.732, AL 390, B 3.647, BH 2.658, E 17.696, FI 166, PA 386, F 1.020, M 731, H 10.196, HN 4.197, T 9.406, PL 811, P 3.898, R 4.787, I 335, S 936, SU 1.280, VQ 136 | 1.480 | 852 | 684 | 49.500 | 44.198 | 10 / 15198.0 | 2 melhorias |
| 58 | Q 4.190, AL 427, B 3.767, BH 2.505, FI 295, PA 476, F 1.020, M 454, H 23.373, HN 4.663, T 9.848, PL 887, P 1.124, R 4.326, I 305, S 978, SU 1.172, VQ 132 | 1.480 | 1.044 | 479 | 57.000 | 44.137 | 10 / 15619.0 | 2 melhorias |
| 59 | Q 3.801, AL 423, B 3.575, BH 2.457, FI 159, PA 299, F 1.020, M 401, H 19.248, HN 4.430, T 9.368, PI 146, PL 904, R 3.711, I 454, S 837, SU 1.516, VQ 96 | 1.480 | 1.032 | 519 | 0 | 93.951 | 10 / 15999.0 | — |
| 60 | Q 4.255, AL 337, B 3.756, BH 2.589, FI 151, PA 566, F 960, M 767, H 21.873, HN 4.896, T 9.580, PL 887, P 3.987, R 3.649, I 397, S 790, SU 1.173, VQ 172 | 1.480 | 884 | 399 | 0 | 151.973 | 10 / 16436.0 | — |
| 61 | Q 3.754, AL 453, B 3.812, BH 2.628, FI 158, PA 446, F 960, M 871, H 21.019, HN 4.663, T 8.851, PI 109, PL 890, P 1.932, R 3.348, I 442, S 853, SU 1.377, VQ 175 | 1.480 | 1.104 | 579 | 0 | 205.551 | 10 / 16843.0 | — |
| 62 | Q 4.228, AL 457, B 3.421, BH 2.601, FI 142, PA 553, F 960, M 482, H 19.662, HN 4.663, T 8.966, PL 936, R 4.529, I 383, S 718, SU 1.146, VQ 259 | 1.480 | 994 | 459 | 0 | 256.725 | 10 / 17290.0 | — |
| 63 | Q 3.703, AL 287, BH 2.190, FI 151, PA 371, F 360, M 382, H 30.683, HN 5.362, T 2.491, PL 609, R 2.424, I 234, S 1.015, SU 1.230, VQ 170 | 1.480 | 764 | 2.489 | 0 | 303.655 | 10 / 17673.0 | — |
| 64 | Q 3.982, AL 205, B 3.595, BH 1.488, E 17.696, FI 141, PA 165, F 960, M 720, H 9.194, HN 3.730, T 9.369, PL 500, P 1.028, R 3.217, I 155, S 885, SU 540, VQ 323 | 1.480 | 996 | 444 | 0 | 358.628 | 10 / 18139.0 | — |
| 65 | RE 1.500, Q 4.196, AL 310, B 3.432, BH 2.528, FI 343, PA 696, F 1.020, M 128, H 19.893, HN 4.663, T 9.406, PI 73, PL 901, P 1.139, R 4.154, I 339, S 931, SU 1.137, VQ 214 | 1.480 | 1.004 | 404 | 0 | 412.744 | 10 / 18570.0 | — |
| 66 | RE 1.000, Q 3.626, AL 276, B 3.658, BH 2.655, FI 130, PA 374, F 900, M 255, H 25.811, HN 5.362, T 8.947, PL 870, P 773, R 4.027, I 411, S 894, SU 1.670, VQ 317 | 1.480 | 850 | 704 | 0 | 471.665 | 10 / 18982.0 | — |
| 67 | Q 4.314, AL 247, B 3.555, BH 2.558, FI 160, PA 667, F 1.020, M 989, H 17.543, HN 3.963, T 9.080, PI 36, PL 933, P 5.122, R 4.302, I 391, S 832, SU 1.213, VQ 26 | 1.480 | 840 | 484 | 0 | 525.811 | 10 / 19391.0 | — |
| 68 | Q 3.964, AL 411, B 3.004, BH 2.540, FI 152, PA 270, F 960, M 655, H 26.831, HN 4.430, T 8.639, PI 73, PL 886, R 3.264, I 391, S 910, SU 1.391, VQ 310 | 1.480 | 1.036 | 444 | 0 | 581.932 | 10 / 19794.0 | — |
| 69 | Q 3.705, AL 548, B 3.777, BH 2.575, FI 148, PA 654, F 1.020, M 276, H 30.827, HN 5.595, T 9.195, PI 36, PL 910, R 3.931, I 369, S 991, SU 1.184, VQ 151 | 1.480 | 1.044 | 544 | 0 | 644.757 | 10 / 20206.0 | — |
| 70 | Q 3.637, AL 261, BH 2.203, FI 161, PA 328, F 360, M 433, H 23.174, HN 5.362, T 2.284, PL 641, R 2.917, I 407, S 979, SU 1.183, VQ 188 | 1.480 | 758 | 2.559 | 0 | 684.477 | 10 / 20588.0 | — |
| 71 | Q 3.637, AL 540, B 3.402, BH 2.533, E 17.696, FI 380, PA 340, F 960, M 327, H 23.311, HN 5.595, T 8.484, PL 886, P 4.010, R 3.679, I 752, S 911, SU 1.120, VQ 334 | 1.480 | 898 | 589 | 0 | 760.406 | 10 / 21012.0 | — |
| 72 | Q 4.056, AL 493, B 3.244, BH 2.554, FI 151, PA 630, F 960, M 479, H 20.159, HN 5.595, T 8.889, PL 924, R 3.103, I 424, S 837, SU 1.134, VQ 177 | 1.480 | 898 | 384 | 0 | 811.453 | 10 / 21428.0 | — |

### Atual — medio, semente 0

[CSV diário completo](../../tools/ue58/balance/results/atual_medio_diario_seed0.csv).

| Dia | Renda por fonte | Salários | Estoque | Outras saídas | Investimento | Caixa final | Nível / XP | Compras / expansões compráveis |
|---|---|---|---|---|---|---|---|---|
| 1 | RE 530, Q 464 | 0 | 118 | 150 | 570 | 306 | 2 / 138.0 | equipe:atendente, kiosk_tables, neon; podia: drinks; kiosk_tables |
| 2 | RE 420, Q 684, VQ 53 | 30 | 295 | 2 | 703 | 433 | 3 / 334.0 | drinks, grill + 1 melhorias; podia: drinks; grill |
| 3 | Q 834, VQ 37 | 32 | 400 | 85 | 225 | 562 | 4 / 452.0 | 3 melhorias |
| 4 | RE 350, Q 233 | 32 | 120 | 5 | 264 | 724 | 4 / 478.0 | 3 melhorias |
| 5 | RE 200, Q 1.043, VQ 56 | 32 | 259 | 5 | 1.200 | 527 | 4 / 631.0 | bar; podia: bar |
| 6 | Q 969, B 277, BH 217, VQ 41 | 35 | 433 | 11 | 1.160 | 393 | 5 / 833.0 | equipe:bartender, negocio:sorveteria |
| 7 | Q 873, B 217, BH 234, I 96, VQ 12 | 117 | 490 | 11 | 196 | 1.010 | 5 / 971.0 | 2 melhorias |
| 8 | Q 911, B 408, BH 466, I 272, VQ 29 | 117 | 332 | 131 | 1.613 | 904 | 6 / 1127.0 | negocio:aluguel + 2 melhorias; podia: pousada |
| 9 | RE 1.100, Q 1.107, AL 301, B 384, BH 469, I 211, VQ 62 | 165 | 534 | 661 | 2.400 | 778 | 7 / 1470.0 | pousada; podia: pousada |
| 10 | RE 1.100, Q 782, AL 464, B 431, BH 473, I 375, VQ 69 | 165 | 304 | 143 | 2.460 | 1.400 | 7 / 1650.0 | equipe:camareira, equipe:recepcionista, pool; podia: passeios; pool |
| 11 | Q 1.098, AL 404, B 469, BH 468, PI 30, PL 165, P 954, I 244, VQ 31 | 237 | 586 | 33 | 3.720 | 687 | 7 / 1831.0 | equipe:piscineiro, passeios, negocio:souvenir + 1 melhorias; podia: passeios |
| 12 | Q 749, AL 276, B 592, BH 487, T 234, PI 20, PL 214, I 219, S 472, VQ 84 | 317 | 456 | 187 | 2.330 | 743 | 8 / 2005.0 | equipe:guia, negocio:food_truck + 2 melhorias |
| 13 | Q 1.078, AL 294, B 480, BH 509, PA 418, T 1.260, PI 10, PL 233, P 342, I 218, S 515, VQ 22 | 414 | 496 | 242 | 2.920 | 2.050 | 8 / 2193.0 | negocio:surfe + 5 melhorias |
| 14 | Q 1.235, AL 218, B 54, BH 422, PA 182, PI 20, PL 153, I 173, S 749, SU 386, VQ 22 | 469 | 568 | 42 | 1.200 | 3.385 | 8 / 2381.0 | 8 melhorias |
| 15 | Q 840, AL 274, B 651, BH 576, PA 209, T 1.032, PI 10, PL 223, P 517, I 176, S 561, SU 421, VQ 11 | 473 | 718 | 242 | 2.186 | 5.266 | 9 / 2533.0 | 13 melhorias |
| 16 | Q 1.412, AL 64, B 754, BH 373, PA 286, T 990, PL 150, P 274, I 95, S 695, SU 199 | 478 | 684 | 122 | 2.497 | 6.777 | 9 / 2735.0 | 13 melhorias |
| 17 | Q 1.131, AL 265, B 582, BH 647, PA 155, T 1.225, PI 51, PL 313, P 584, I 189, S 564, SU 706, VQ 34 | 481 | 590 | 242 | 3.421 | 8.489 | 9 / 2948.0 | 15 melhorias |
| 18 | Q 1.485, AL 59, B 866, BH 452, PA 248, T 1.222, PL 198, P 314, I 109, S 627, SU 172, VQ 98 | 487 | 686 | 122 | 3.636 | 9.408 | 9 / 3172.0 | 13 melhorias |
| 19 | Q 1.317, AL 277, B 1.093, BH 873, PA 151, F 135, T 1.530, PI 93, PL 321, P 336, I 229, S 545, SU 719, VQ 102 | 490 | 722 | 242 | 4.358 | 11.316 | 10 / 3458.0 | 13 melhorias |
| 20 | Q 1.700, AL 209, B 1.399, BH 965, PA 366, F 150, T 1.587, PI 30, PL 371, P 206, I 136, S 549, SU 675, VQ 62 | 490 | 760 | 242 | 5.155 | 13.073 | 10 / 3753.0 | 14 melhorias |
| 21 | Q 2.111, AL 217, BH 931, PA 184, F 60, T 499, PI 31, PL 262, I 189, S 655, SU 477, VQ 245 | 490 | 622 | 67 | 5.000 | 12.755 | 10 / 4083.0 | 12 melhorias |
| 22 | Q 1.424, AL 224, B 1.349, BH 1.107, PA 179, F 120, T 1.648, PI 102, PL 412, P 753, I 253, S 572, SU 903, VQ 70 | 496 | 654 | 242 | 5.870 | 14.610 | 10 / 4362.0 | 13 melhorias |
| 23 | Q 2.172, AL 237, B 1.506, BH 1.207, PA 365, F 135, T 1.980, PI 19, PL 488, P 775, I 153, S 616, SU 704, VQ 209 | 498 | 704 | 122 | 6.894 | 16.959 | 10 / 4714.0 | 13 melhorias |
| 24 | Q 1.561, AL 321, B 1.622, BH 1.248, PA 154, F 60, T 501, PL 512, P 354, I 202, S 660, SU 760 | 502 | 708 | 172 | 6.410 | 17.122 | 10 / 4945.0 | 11 melhorias |
| 25 | Q 2.269, AL 296, B 1.641, BH 1.305, PA 330, F 225, T 2.043, PI 60, PL 490, I 191, S 580, SU 815, VQ 70 | 502 | 884 | 122 | 7.390 | 18.540 | 10 / 5273.0 | 11 melhorias |
| 26 | Q 2.006, AL 278, B 1.891, BH 1.412, PA 167, F 250, T 2.438, PI 40, PL 512, P 1.059, I 182, S 552, SU 866, VQ 126 | 502 | 684 | 242 | 8.330 | 20.560 | 10 / 5611.0 | 11 melhorias |
| 27 | RE 1.000, Q 2.383, AL 302, B 2.068, BH 1.448, PA 306, F 300, T 2.996, PI 86, PL 530, P 640, I 229, S 651, SU 617, VQ 134 | 505 | 760 | 242 | 30.840 | 1.904 | 10 / 5944.0 | grand_hotel + 1 melhorias; podia: grand_hotel |
| 28 | RE 3.500, Q 2.349, AL 336, B 87, BH 1.306, PA 166, H 8.424, HN 536, PL 392, R 1.140, I 184, S 628, SU 704, VQ 123 | 1.405 | 776 | 512 | 11.000 | 8.086 | 10 / 6290.0 | equipe:garcom_hotel, salao_jogos + 5 melhorias; podia: salao_jogos |
| 29 | Q 1.828, AL 444, B 2.543, BH 1.578, FI 389, PA 217, F 250, M 721, H 7.960, HN 655, T 2.693, PI 43, PL 495, P 1.280, R 1.139, I 360, S 605, SU 774, VQ 27 | 1.453 | 630 | 1.234 | 17.880 | 10.890 | 10 / 6614.0 | 20 melhorias |
| 30 | Q 2.503, AL 274, B 1.805, BH 1.698, FI 134, PA 324, F 350, M 133, H 12.558, HN 1.266, T 3.696, PI 24, PL 598, P 408, R 1.543, I 186, S 644, SU 683, VQ 70 | 1.457 | 878 | 3.114 | 22.745 | 11.593 | 10 / 6979.0 | 22 melhorias |
| 31 | Q 2.278, AL 318, B 2.004, BH 1.754, E 6.944, FI 148, PA 158, F 300, M 317, H 10.952, HN 1.845, T 4.004, PI 26, PL 641, P 948, R 1.621, I 232, S 544, SU 1.103, VQ 98 | 1.463 | 810 | 1.519 | 27.310 | 16.726 | 10 / 7416.0 | 22 melhorias |
| 32 | Q 3.081, AL 288, B 2.207, BH 1.684, FI 150, PA 382, F 325, M 770, H 6.513, HN 1.861, T 4.084, PI 27, PL 653, P 654, R 1.342, I 319, S 564, SU 1.141, VQ 182 | 1.466 | 768 | 769 | 24.550 | 15.399 | 10 / 7880.0 | 17 melhorias |
| 33 | Q 3.058, AL 67, B 2.897, BH 1.063, FI 152, PA 135, F 560, M 962, H 4.599, HN 1.833, T 4.360, PL 388, P 658, R 1.899, I 71, S 718, SU 460, VQ 154 | 1.473 | 1.130 | 1.619 | 21.165 | 14.045 | 10 / 8298.0 | 13 melhorias |
| 34 | Q 3.304, AL 486, B 2.622, BH 1.962, E 3.696, FI 149, PA 577, F 560, M 431, H 7.509, HN 1.943, T 5.661, PI 84, PL 729, R 1.903, I 307, S 793, SU 843, VQ 168 | 1.473 | 1.066 | 624 | 26.950 | 17.658 | 10 / 8777.0 | 15 melhorias |
| 35 | Q 4.167, AL 118, BH 1.000, FI 136, PA 165, M 325, H 13.450, HN 1.748, PL 273, R 1.803, I 81, S 804, SU 572, VQ 164 | 1.473 | 898 | 384 | 23.800 | 15.910 | 10 / 9282.0 | 12 melhorias |
| 36 | Q 3.104, AL 132, B 3.025, BH 1.263, FI 407, PA 123, F 200, M 262, H 14.700, HN 2.428, T 978, PL 397, P 1.981, R 1.768, I 111, S 760, SU 781, VQ 160 | 1.473 | 808 | 1.084 | 27.665 | 17.459 | 10 / 9657.0 | 13 melhorias |
| 37 | Q 4.017, AL 95, B 3.279, BH 1.258, E 2.656, FI 416, PA 377, F 560, M 365, H 3.948, HN 2.408, T 5.894, PL 459, P 520, R 1.575, I 130, S 815, SU 525, VQ 150 | 1.473 | 1.016 | 499 | 26.160 | 17.758 | 10 / 10131.0 | 11 melhorias |
| 38 | Q 3.378, AL 477, B 3.066, BH 2.264, CP 150, FI 477, PA 204, F 520, M 597, H 10.463, HN 2.470, T 5.470, PI 65, PL 839, P 1.640, R 1.936, I 552, S 655, SU 1.454, VQ 218 | 1.473 | 858 | 534 | 32.300 | 19.488 | 10 / 10541.0 | 12 melhorias |
| 39 | Q 4.299, AL 275, B 2.819, BH 2.355, FI 144, PA 432, F 640, M 1.020, H 12.531, HN 2.021, T 6.558, PL 826, P 728, R 2.077, I 450, S 677, SU 1.269, VQ 286 | 1.477 | 1.078 | 2.614 | 32.540 | 21.185 | 10 / 11033.0 | 11 melhorias |
| 40 | Q 3.182, AL 497, B 3.373, BH 2.431, E 10.640, FI 145, PA 208, F 180, M 743, H 13.825, HN 2.516, T 972, PI 33, PL 833, P 1.107, R 1.864, I 364, S 810, SU 1.616, VQ 110 | 1.477 | 1.016 | 494 | 37.240 | 26.407 | 10 / 11452.0 | 11 melhorias |
| 41 | Q 4.650, AL 361, B 3.183, BH 2.392, FI 158, PA 660, F 780, M 520, H 14.003, HN 2.886, T 6.154, PL 827, P 1.353, R 2.446, I 540, S 938, SU 1.216, VQ 251 | 1.477 | 1.154 | 624 | 42.080 | 24.390 | 10 / 11951.0 | 11 melhorias |
| 42 | Q 4.612, AL 387, BH 2.071, FI 155, PA 285, F 360, M 335, H 14.558, HN 3.049, T 2.020, PL 638, R 2.488, I 378, S 973, SU 1.524, VQ 122 | 1.477 | 942 | 2.479 | 32.100 | 21.346 | 10 / 12406.0 | 7 melhorias |
| 43 | Q 4.009, AL 514, B 3.874, BH 2.584, E 11.648, FI 150, PA 311, F 960, M 192, H 13.405, HN 3.465, T 7.656, PI 182, PL 877, P 2.600, R 2.548, I 490, S 783, SU 1.987 | 1.477 | 938 | 519 | 43.260 | 33.387 | 10 / 12836.0 | 8 melhorias |
| 44 | Q 5.141, AL 297, B 3.236, BH 2.548, FI 355, PA 652, F 840, M 512, H 12.704, HN 3.865, T 7.707, PL 902, P 2.228, R 2.666, I 341, S 930, SU 1.472, VQ 292 | 1.477 | 906 | 554 | 46.200 | 30.938 | 10 / 13329.0 | 7 melhorias |
| 45 | Q 3.752, AL 812, B 4.035, BH 2.543, FI 389, PA 270, F 1.140, M 493, H 7.374, HN 3.577, T 9.068, PL 917, P 1.443, R 2.334, I 777, S 847, SU 1.716, VQ 74 | 1.477 | 1.022 | 2.944 | 38.200 | 28.855 | 10 / 13725.0 | 5 melhorias |
| 46 | Q 4.816, AL 488, B 3.510, BH 2.456, E 13.664, FI 140, PA 639, F 1.020, M 765, H 9.023, HN 3.089, T 9.099, PI 73, PL 870, R 2.591, I 418, S 910, SU 1.721, VQ 158 | 1.477 | 1.022 | 459 | 47.900 | 33.448 | 10 / 14242.0 | 5 melhorias |
| 47 | Q 3.975, AL 322, B 3.849, BH 2.525, FI 140, PA 359, F 960, M 519, H 15.492, HN 3.270, T 9.139, PI 182, PL 883, R 3.833, I 544, S 843, SU 1.783, VQ 179 | 1.477 | 974 | 564 | 46.500 | 32.730 | 10 / 14707.0 | 4 melhorias |
| 48 | Q 4.480, AL 240, B 3.419, BH 2.509, FI 131, PA 542, F 1.140, M 363, H 18.556, HN 3.614, T 10.056, PI 36, PL 970, P 6.214, R 3.641, I 454, S 947, SU 1.738, VQ 238 | 1.480 | 1.046 | 2.764 | 55.100 | 31.629 | 10 / 15184.0 | 4 melhorias |
| 49 | Q 4.979, AL 458, B 330, BH 2.149, E 16.016, FI 149, PA 357, M 296, H 19.882, HN 4.217, PL 660, R 2.164, I 399, S 937, SU 1.698, VQ 282 | 1.480 | 840 | 324 | 45.000 | 38.957 | 10 / 15714.0 | 3 melhorias |
| 50 | Q 4.153, AL 141, B 3.335, BH 1.534, FI 161, PA 207, F 900, M 681, H 9.754, HN 4.394, T 8.657, PL 461, P 2.004, R 3.672, I 223, S 904, SU 790, VQ 118 | 1.480 | 1.060 | 504 | 36.000 | 42.003 | 10 / 16169.0 | 2 melhorias |
| 51 | Q 5.097, AL 468, B 3.542, BH 2.500, FI 403, PA 542, F 1.200, M 219, H 28.857, HN 4.881, T 10.126, PI 109, PL 905, R 3.620, I 344, S 967, SU 1.464, VQ 368 | 1.480 | 1.178 | 2.724 | 61.500 | 40.734 | 10 / 16663.0 | 3 melhorias |
| 52 | Q 4.428, AL 676, B 3.330, BH 2.621, E 17.696, FI 155, PA 276, F 960, M 160, H 20.981, HN 5.829, T 9.215, PI 36, PL 912, P 1.218, R 4.110, I 794, S 885, SU 1.679, VQ 117 | 1.480 | 844 | 564 | 49.500 | 64.424 | 10 / 17116.0 | 2 melhorias |
| 53 | Q 5.076, AL 200, B 3.577, BH 1.519, FI 147, PA 367, F 960, M 371, H 16.370, HN 5.362, T 8.408, PL 531, P 806, R 4.461, I 189, S 926, SU 736, VQ 161 | 1.480 | 954 | 504 | 57.000 | 54.652 | 10 / 17630.0 | 2 melhorias |
| 54 | Q 4.257, AL 312, B 3.563, BH 2.546, FI 151, PA 276, F 1.140, M 586, H 17.335, HN 5.129, T 10.263, PI 36, PL 925, P 2.702, R 3.036, I 370, S 886, SU 2.025, VQ 54 | 1.480 | 802 | 2.904 | 0 | 105.058 | 10 / 18041.0 | — |
| 55 | RE 1.500, Q 4.794, AL 476, B 3.175, BH 2.550, E 17.696, FI 145, PA 501, F 960, M 473, H 24.055, HN 5.129, T 9.580, PI 73, PL 925, P 4.064, R 2.524, I 359, S 873, SU 1.477, VQ 335 | 1.480 | 1.190 | 474 | 0 | 183.579 | 10 / 18567.0 | — |
| 56 | RE 1.000, Q 4.557, AL 245, BH 2.086, FI 140, PA 283, M 543, H 26.453, HN 4.430, PI 145, PL 621, R 2.917, I 454, S 958, SU 1.683, VQ 152 | 1.480 | 916 | 284 | 0 | 227.566 | 10 / 19057.0 | — |
| 57 | Q 4.415, AL 383, B 3.560, BH 2.605, FI 154, PA 303, F 1.140, M 371, H 35.977, HN 5.829, T 9.994, PI 73, PL 816, P 936, R 3.229, I 341, S 702, SU 2.186, VQ 208 | 1.480 | 990 | 2.799 | 0 | 295.519 | 10 / 19502.0 | — |
| 58 | Q 5.610, AL 298, B 3.555, BH 2.676, E 17.696, FI 430, PA 773, F 1.020, M 312, H 14.701, HN 5.829, T 9.503, PL 902, P 1.058, R 3.053, I 340, S 924, SU 1.437, VQ 287 | 1.480 | 960 | 419 | 0 | 363.063 | 10 / 20043.0 | — |
| 59 | Q 4.564, AL 420, B 3.134, BH 2.565, FI 161, PA 317, F 960, M 289, H 14.121, HN 5.362, T 8.965, PL 883, P 766, R 3.639, I 524, S 853, SU 2.191, VQ 200 | 1.480 | 882 | 604 | 0 | 410.011 | 10 / 20519.0 | — |
| 60 | Q 4.972, AL 448, B 2.978, BH 2.527, FI 163, PA 643, F 1.140, M 377, H 15.100, HN 6.062, T 9.708, PI 72, PL 913, P 2.605, R 4.456, I 381, S 828, SU 1.696, VQ 347 | 1.480 | 980 | 2.639 | 0 | 460.329 | 10 / 21011.0 | — |
| 61 | Q 4.623, AL 54, B 3.653, BH 1.529, E 17.696, FI 147, PA 212, F 1.020, M 541, H 13.988, HN 4.197, T 9.291, PL 541, P 2.680, R 4.126, I 270, S 810, SU 970, VQ 161 | 1.480 | 1.150 | 519 | 0 | 523.689 | 10 / 21521.0 | — |
| 62 | Q 5.149, AL 388, B 3.298, BH 2.571, FI 150, PA 711, F 1.020, M 753, H 20.110, HN 3.963, T 9.714, PI 36, PL 915, P 1.014, R 4.031, I 463, S 874, SU 1.361, VQ 192 | 1.480 | 908 | 534 | 0 | 577.480 | 10 / 22050.0 | — |

### Atual — dedicado, semente 0

[CSV diário completo](../../tools/ue58/balance/results/atual_dedicado_diario_seed0.csv).

| Dia | Renda por fonte | Salários | Estoque | Outras saídas | Investimento | Caixa final | Nível / XP | Compras / expansões compráveis |
|---|---|---|---|---|---|---|---|---|
| 1 | RE 530, Q 766 | 0 | 321 | 150 | 680 | 295 | 2 / 172.0 | equipe:atendente, kiosk_tables, drinks; podia: drinks; kiosk_tables |
| 2 | RE 420, Q 802, VQ 19 | 30 | 275 | 2 | 668 | 561 | 3 / 378.0 | neon, grill + 2 melhorias; podia: grill; neon |
| 3 | Q 888, VQ 30 | 32 | 425 | 5 | 900 | 118 | 4 / 504.0 | negocio:sorveteria |
| 4 | RE 550, Q 1.039, I 514, VQ 126 | 72 | 340 | 5 | 1.275 | 655 | 5 / 739.0 | bar + 1 melhorias; podia: bar |
| 5 | Q 1.058, B 219, BH 394, I 415, VQ 163 | 72 | 430 | 11 | 1.735 | 656 | 6 / 1026.0 | equipe:bartender, negocio:aluguel + 1 melhorias |
| 6 | RE 300, Q 1.059, AL 419, B 402, BH 480, I 318, VQ 122 | 162 | 558 | 11 | 2.400 | 624 | 6 / 1268.0 | pousada; podia: pousada |
| 7 | RE 1.900, Q 1.148, AL 148, B 412, BH 257, P 471, I 127, VQ 30 | 162 | 330 | 673 | 2.460 | 1.492 | 7 / 1607.0 | equipe:camareira, equipe:recepcionista, pool; podia: passeios; pool |
| 8 | Q 1.089, AL 515, B 293, BH 493, PI 60, PL 181, P 1.114, I 350, VQ 59 | 235 | 629 | 153 | 3.864 | 766 | 7 / 1826.0 | equipe:piscineiro, passeios, negocio:souvenir + 3 melhorias; podia: passeios |
| 9 | Q 1.217, AL 305, B 449, BH 506, T 234, PI 40, PL 223, I 251, S 665, VQ 56 | 311 | 694 | 67 | 2.376 | 1.263 | 8 / 2060.0 | equipe:guia, negocio:food_truck + 3 melhorias |
| 10 | Q 978, AL 425, B 474, BH 510, PA 180, T 1.355, PI 20, PL 221, P 750, I 242, S 566, VQ 38 | 408 | 558 | 242 | 3.109 | 2.706 | 8 / 2284.0 | negocio:surfe + 7 melhorias |
| 11 | Q 1.293, AL 336, B 433, BH 507, PA 428, T 1.355, PI 20, PL 234, P 99, I 189, S 532, SU 528, VQ 39 | 473 | 704 | 202 | 2.112 | 5.208 | 9 / 2536.0 | 14 melhorias |
| 12 | Q 405, AL 80, B 659, BH 357, PA 164, T 273, PL 152, P 492, I 100, S 680, SU 430, VQ 47 | 478 | 424 | 172 | 2.283 | 5.691 | 9 / 2714.0 | 13 melhorias |
| 13 | Q 1.598, AL 322, B 593, BH 584, PA 419, T 1.296, PI 22, PL 274, P 115, I 203, S 672, SU 524, VQ 70 | 481 | 800 | 242 | 3.118 | 7.741 | 9 / 2986.0 | 15 melhorias |
| 14 | Q 1.864, AL 336, B 78, BH 615, PA 178, T 351, PI 13, PL 218, I 176, S 654, SU 566, VQ 76 | 481 | 700 | 67 | 3.383 | 8.236 | 10 / 3258.0 | 14 melhorias |
| 15 | Q 1.417, AL 309, B 875, BH 750, PA 222, F 135, T 1.326, PI 40, PL 313, P 762, I 251, S 565, SU 884, VQ 154 | 484 | 714 | 242 | 4.216 | 10.582 | 10 / 3535.0 | 14 melhorias |
| 16 | Q 2.022, AL 275, B 1.222, BH 917, PA 339, F 165, T 1.735, PI 30, PL 380, P 250, I 191, S 662, SU 626, VQ 130 | 484 | 844 | 122 | 5.000 | 13.075 | 10 / 3907.0 | 14 melhorias |
| 17 | Q 1.739, AL 180, B 1.026, BH 592, PA 171, F 165, T 1.517, PL 240, P 528, I 174, S 639, SU 387, VQ 61 | 487 | 710 | 242 | 5.535 | 13.521 | 10 / 4237.0 | 14 melhorias |
| 18 | Q 2.319, AL 281, B 1.284, BH 1.173, PA 379, F 150, T 1.832, PI 17, PL 424, P 420, I 171, S 682, SU 699, VQ 38 | 493 | 862 | 122 | 6.030 | 15.883 | 10 / 4597.0 | 14 melhorias |
| 19 | Q 1.747, AL 339, B 1.350, BH 1.141, PA 229, F 165, T 2.094, PI 54, PL 461, P 234, I 239, S 624, SU 900, VQ 94 | 498 | 696 | 242 | 6.674 | 17.445 | 10 / 4944.0 | 13 melhorias |
| 20 | Q 2.825, AL 78, B 1.847, BH 758, PA 192, F 165, T 1.985, PL 279, I 83, S 579, SU 413, VQ 202 | 502 | 1.002 | 242 | 7.340 | 17.764 | 10 / 5366.0 | 13 melhorias |
| 21 | Q 2.589, AL 235, BH 1.083, PA 129, F 100, T 683, PI 80, PL 373, I 243, S 679, SU 932, VQ 109 | 502 | 620 | 67 | 6.520 | 17.291 | 10 / 5762.0 | 10 melhorias |
| 22 | Q 2.453, AL 152, B 1.826, BH 850, PA 130, F 275, T 2.296, PL 275, P 2.299, I 124, S 539, SU 546, VQ 35 | 502 | 888 | 242 | 7.970 | 19.488 | 10 / 6129.0 | 11 melhorias |
| 23 | Q 2.941, AL 164, B 2.069, BH 856, PA 187, F 250, T 2.559, PL 318, I 71, S 689, SU 368, VQ 118 | 502 | 816 | 122 | 8.340 | 20.300 | 10 / 6549.0 | 10 melhorias |
| 24 | RE 1.000, Q 2.492, AL 389, B 1.667, BH 1.560, PA 198, F 275, T 2.893, PI 43, PL 557, I 266, S 605, SU 1.187, VQ 138 | 502 | 840 | 242 | 30.000 | 1.986 | 10 / 6935.0 | grand_hotel; podia: grand_hotel |
| 25 | RE 3.500, Q 3.174, AL 70, B 1.807, BH 917, PA 237, F 275, H 9.082, HN 536, T 2.559, PL 322, P 2.347, R 878, I 72, S 542, SU 376, VQ 176 | 1.402 | 868 | 3.247 | 15.380 | 7.959 | 10 / 7414.0 | equipe:garcom_hotel, salao_jogos + 10 melhorias; podia: salao_jogos |
| 26 | Q 2.466, AL 322, B 2.011, BH 1.633, E 5.600, FI 117, PA 194, F 275, M 362, H 11.429, HN 952, T 2.924, PI 22, PL 558, P 720, R 1.000, I 225, S 584, SU 1.146, VH 110, VQ 86 | 1.453 | 682 | 2.384 | 22.410 | 13.767 | 10 / 7852.0 | 23 melhorias |
| 27 | Q 3.595, AL 233, B 2.597, BH 1.649, E 2.976, FI 116, PA 244, F 350, M 120, H 8.753, HN 1.328, T 3.801, PI 25, PL 621, R 1.418, I 192, S 670, SU 979, VQ 46 | 1.463 | 1.090 | 1.949 | 24.765 | 14.213 | 10 / 8376.0 | 21 melhorias |
| 28 | Q 4.281, AL 237, BH 1.475, E 2.176, FI 154, PA 178, F 100, M 269, H 10.084, HN 1.942, T 857, PI 52, PL 412, R 1.131, I 309, S 654, SU 989, VQ 78 | 1.463 | 896 | 2.789 | 22.350 | 12.094 | 10 / 8906.0 | 17 melhorias |
| 29 | Q 2.735, AL 665, B 2.149, BH 1.833, E 7.616, FI 369, PA 152, F 560, M 333, H 11.824, HN 2.023, T 4.624, PI 27, PL 654, P 1.318, R 1.222, I 799, S 643, SU 1.130, VQ 136 | 1.466 | 874 | 3.094 | 31.275 | 16.197 | 10 / 9362.0 | 20 melhorias |
| 30 | Q 3.705, AL 321, B 2.823, BH 1.873, E 8.624, FI 406, PA 454, F 600, M 761, H 4.418, HN 1.845, T 5.412, PI 84, PL 705, P 277, R 1.980, I 398, S 819, SU 883, VQ 215 | 1.469 | 958 | 2.739 | 30.380 | 17.254 | 10 / 9890.0 | 17 melhorias |
| 31 | Q 3.178, AL 109, B 2.859, BH 1.160, E 8.624, FI 150, PA 168, F 200, M 706, H 16.006, HN 1.943, T 1.100, PL 439, P 2.098, R 2.140, I 156, S 718, SU 883, VQ 114 | 1.473 | 1.044 | 2.864 | 34.300 | 20.325 | 10 / 10378.0 | 17 melhorias |
| 32 | Q 4.643, AL 115, B 2.633, BH 1.282, E 8.624, FI 153, PA 369, F 680, M 139, H 10.069, HN 2.234, T 5.957, PL 443, R 2.188, I 226, S 685, SU 673, VQ 250 | 1.473 | 1.188 | 2.904 | 35.785 | 20.338 | 10 / 10985.0 | 16 melhorias |
| 33 | Q 4.253, AL 157, B 2.878, BH 1.286, E 9.968, FI 146, PA 138, F 640, M 548, H 8.258, HN 2.358, T 6.020, PL 477, P 2.256, R 1.993, I 158, S 733, SU 890, VQ 48 | 1.473 | 706 | 2.804 | 37.140 | 21.419 | 10 / 11492.0 | 14 melhorias |
| 34 | Q 4.835, AL 394, B 2.953, BH 2.264, E 9.968, FI 147, PA 465, F 600, M 854, H 14.643, HN 2.133, T 6.171, PI 67, PL 872, P 1.113, R 2.210, I 375, S 815, SU 1.777, VQ 183 | 1.473 | 1.120 | 2.699 | 44.820 | 24.146 | 10 / 12076.0 | 15 melhorias |
| 35 | Q 5.523, AL 109, B 137, BH 1.206, E 10.640, FI 143, PA 180, F 360, M 320, H 14.121, HN 2.756, T 1.807, PL 322, R 1.664, I 185, S 931, SU 697, VQ 108 | 1.473 | 1.126 | 2.644 | 38.460 | 21.651 | 10 / 12675.0 | 11 melhorias |
| 36 | Q 4.194, AL 772, B 3.202, BH 2.425, E 11.648, FI 482, PA 253, F 900, M 603, H 17.245, HN 2.624, T 6.629, PI 35, PL 771, P 2.942, R 2.264, I 706, S 796, SU 2.004, VQ 197 | 1.473 | 1.160 | 2.914 | 48.980 | 27.816 | 10 / 13160.0 | 12 melhorias |
| 37 | Q 5.504, AL 193, B 3.386, BH 1.547, E 11.648, FI 155, PA 451, F 1.140, M 415, H 17.407, HN 3.188, T 8.337, PL 508, P 1.311, R 1.907, I 170, S 974, SU 887, VQ 355 | 1.477 | 962 | 2.764 | 51.660 | 30.435 | 10 / 13766.0 | 10 melhorias |
| 38 | Q 4.087, AL 589, B 3.415, BH 2.659, E 12.992, FI 157, PA 373, F 1.080, M 133, H 14.980, HN 4.020, T 8.819, PI 36, PL 933, R 2.525, I 612, S 838, SU 2.769, VQ 82 | 1.477 | 912 | 2.689 | 52.200 | 34.256 | 10 / 14259.0 | 8 melhorias |
| 39 | Q 5.528, AL 223, B 4.034, BH 1.521, E 13.664, FI 140, PA 381, F 960, M 618, H 10.864, HN 3.577, T 8.045, PL 540, P 976, R 3.632, I 238, S 934, SU 821, VQ 259 | 1.477 | 980 | 2.704 | 55.700 | 30.350 | 10 / 14851.0 | 7 melhorias |
| 40 | Q 1.920, AL 191, B 3.327, BH 1.488, E 14.672, FI 158, PA 296, F 420, M 174, H 17.412, HN 4.967, T 1.916, PL 531, P 2.886, R 3.100, I 309, S 774, SU 1.232, VQ 122 | 1.477 | 768 | 2.629 | 53.000 | 28.372 | 10 / 15160.0 | 5 melhorias |
| 41 | Q 5.651, AL 372, B 3.217, BH 2.513, E 15.344, FI 166, PA 661, F 1.140, M 523, H 13.458, HN 3.848, T 9.918, PI 73, PL 909, P 2.248, R 3.424, I 444, S 994, SU 1.823, VQ 294 | 1.477 | 1.114 | 2.819 | 50.000 | 39.982 | 10 / 15762.0 | 4 melhorias |
| 42 | Q 5.557, AL 476, B 82, BH 2.148, E 16.016, FI 150, PA 266, F 360, M 608, H 15.449, HN 4.819, T 2.249, PI 36, PL 602, R 1.984, I 472, S 975, SU 1.699, VQ 158 | 1.477 | 852 | 2.464 | 44.000 | 45.295 | 10 / 16319.0 | 3 melhorias |
| 43 | Q 4.449, AL 550, B 4.090, BH 2.490, E 16.016, FI 374, PA 303, F 1.200, M 964, H 15.019, HN 4.016, T 10.246, PI 72, PL 854, P 1.514, R 3.741, I 509, S 871, SU 1.874, VQ 182 | 1.477 | 1.202 | 2.869 | 66.000 | 43.080 | 10 / 16829.0 | 4 melhorias |
| 44 | Q 5.766, AL 65, B 3.354, BH 1.546, E 17.696, FI 151, PA 413, F 1.080, M 385, H 25.928, HN 4.881, T 9.527, PL 548, P 466, R 3.839, I 85, S 918, SU 906, VQ 234 | 1.477 | 1.364 | 2.524 | 61.500 | 54.003 | 10 / 17466.0 | 3 melhorias |
| 45 | Q 4.744, AL 517, B 3.649, BH 2.670, E 17.696, FI 141, PA 338, F 1.140, M 655, H 25.132, HN 5.129, T 9.934, PI 72, PL 953, P 4.653, R 3.551, I 523, S 847, SU 2.506, VQ 199 | 1.477 | 948 | 2.884 | 76.500 | 57.244 | 10 / 18001.0 | 3 melhorias |
| 46 | Q 6.013, AL 430, B 3.385, BH 2.636, E 17.696, FI 157, PA 737, F 1.080, M 321, H 29.045, HN 5.829, T 9.169, PI 146, PL 944, R 4.053, I 444, S 823, SU 2.233, VQ 241 | 1.480 | 1.104 | 2.684 | 30.000 | 107.357 | 10 / 18609.0 | 1 melhorias |
| 47 | Q 4.526, AL 541, B 4.341, BH 2.568, E 17.696, FI 152, PA 380, F 1.140, M 541, H 17.948, HN 5.829, T 10.263, PI 36, PL 916, P 2.920, R 4.819, I 456, S 864, SU 2.258, VQ 185 | 1.480 | 992 | 2.924 | 0 | 180.340 | 10 / 19149.0 | — |
| 48 | RE 1.500, Q 5.520, AL 364, B 3.609, BH 2.583, E 17.696, FI 161, PA 665, F 1.080, M 393, H 16.246, HN 5.129, T 9.331, PI 73, PL 970, R 4.165, I 395, S 977, SU 2.241, VQ 198 | 1.480 | 1.272 | 2.684 | 0 | 248.200 | 10 / 19730.0 | — |
| 49 | RE 1.000, Q 6.260, AL 126, B 122, BH 1.278, E 17.696, FI 151, PA 159, F 360, M 481, H 31.432, HN 5.829, T 2.491, PL 378, R 2.967, I 215, S 987, SU 681, VQ 367 | 1.480 | 990 | 2.599 | 0 | 316.111 | 10 / 20364.0 | — |
| 50 | Q 3.801, AL 525, B 3.332, BH 2.662, E 17.696, FI 395, PA 365, F 420, M 600, H 16.359, HN 4.896, T 1.916, PI 73, PL 820, P 3.437, R 3.574, I 565, S 969, SU 1.835, VQ 96 | 1.480 | 944 | 2.664 | 0 | 375.359 | 10 / 20806.0 | — |
| 51 | Q 5.693, AL 506, B 3.608, BH 2.568, E 17.696, FI 143, PA 719, F 1.140, M 353, H 20.613, HN 5.595, T 9.438, PI 73, PL 901, P 970, R 4.456, I 438, S 913, SU 1.559, VQ 277 | 1.480 | 1.036 | 2.599 | 0 | 447.902 | 10 / 21395.0 | — |
| 52 | Q 4.998, AL 450, B 3.264, BH 2.593, E 17.696, FI 133, PA 323, F 1.140, M 698, H 13.291, HN 4.663, T 9.530, PI 73, PL 905, P 2.572, R 2.501, I 782, S 876, SU 1.882, VQ 168 | 1.480 | 1.204 | 2.744 | 0 | 511.011 | 10 / 21939.0 | — |
| 53 | Q 5.051, AL 445, B 3.899, BH 2.511, E 17.696, FI 132, PA 629, F 1.140, M 637, H 24.824, HN 5.129, T 9.933, PI 109, PL 901, P 1.120, R 3.559, I 430, S 923, SU 2.213, VQ 184 | 1.480 | 1.018 | 2.639 | 0 | 587.339 | 10 / 22518.0 | — |
| 54 | Q 5.076, AL 498, B 3.245, BH 2.477, E 17.696, FI 148, PA 371, F 1.200, M 415, H 15.252, HN 5.362, T 10.246, PI 146, PL 922, R 3.506, I 445, S 926, SU 2.578, VQ 382 | 1.480 | 1.106 | 2.754 | 0 | 652.889 | 10 / 23070.0 | — |
| 55 | Q 5.488, AL 302, B 3.479, BH 2.593, E 17.696, FI 156, PA 629, F 1.080, M 421, H 22.041, HN 4.430, T 9.119, PI 109, PL 904, P 1.079, R 3.434, I 445, S 971, SU 2.202, VQ 134 | 1.480 | 1.136 | 2.814 | 0 | 724.172 | 10 / 23655.0 | — |

### Proposto — casual, semente 0

[CSV diário completo](../../tools/ue58/balance/results/proposto_casual_diario_seed0.csv).

| Dia | Renda por fonte | Salários | Estoque | Outras saídas | Investimento | Caixa final | Nível / XP | Compras / expansões compráveis |
|---|---|---|---|---|---|---|---|---|
| 1 | RE 370, Q 274 | 0 | 126 | 150 | 240 | 278 | 2 / 118.0 | equipe:atendente; podia: drinks; kiosk_tables |
| 2 | RE 280, Q 410, VQ 19 | 30 | 111 | 0 | 440 | 406 | 2 / 216.0 | kiosk_tables, drinks; podia: drinks; kiosk_tables |
| 3 | RE 300, Q 548, VQ 29 | 32 | 245 | 2 | 593 | 411 | 3 / 382.0 | neon, grill + 1 melhorias; podia: grill; neon |
| 4 | RE 350, Q 768 | 32 | 378 | 5 | 900 | 214 | 4 / 482.0 | negocio:sorveteria |
| 5 | Q 705, I 189, VQ 50 | 72 | 331 | 5 | 150 | 600 | 4 / 592.0 | 2 melhorias |
| 6 | RE 200, Q 662, I 190, VQ 56 | 75 | 105 | 5 | 1.200 | 322 | 5 / 706.0 | bar; podia: bar |
| 7 | Q 628, B 14, BH 389, I 180, VQ 40 | 75 | 230 | 11 | 423 | 835 | 5 / 819.0 | equipe:bartender + 2 melhorias |
| 8 | Q 690, B 344, BH 438, I 354 | 117 | 527 | 131 | 1.488 | 398 | 5 / 923.0 | negocio:aluguel + 1 melhorias |
| 9 | Q 1.003, AL 228, B 301, BH 466, I 172, VQ 13 | 165 | 324 | 11 | 497 | 1.583 | 6 / 1060.0 | 5 melhorias |
| 10 | RE 300, Q 702, AL 348, B 396, BH 483, I 339, VQ 21 | 165 | 360 | 131 | 2.520 | 997 | 6 / 1173.0 | pousada + 1 melhorias; podia: pousada |
| 11 | RE 1.900, Q 816, AL 243, B 450, BH 458, I 185, VQ 48 | 167 | 372 | 673 | 2.460 | 1.424 | 7 / 1463.0 | equipe:camareira, equipe:recepcionista, pool; podia: passeios; pool |
| 12 | Q 755, AL 233, B 432, BH 483, PL 148, P 682, I 150 | 241 | 216 | 153 | 2.388 | 1.309 | 7 / 1585.0 | equipe:piscineiro, passeios + 3 melhorias; podia: passeios |
| 13 | Q 876, AL 254, B 558, BH 503, PI 50, PL 201, I 160, VQ 126 | 277 | 516 | 162 | 2.168 | 914 | 7 / 1745.0 | equipe:guia, negocio:souvenir + 2 melhorias |
| 14 | Q 918, AL 173, BH 413, T 297, PI 40, PL 149, I 138, S 588, VQ 42 | 362 | 490 | 67 | 1.944 | 809 | 7 / 1874.0 | negocio:food_truck + 1 melhorias |
| 15 | Q 655, AL 53, B 625, BH 304, PA 109, T 690, PL 121, P 550, I 76, S 633, VQ 30 | 414 | 510 | 242 | 2.500 | 989 | 8 / 1988.0 | negocio:surfe + 2 melhorias |
| 16 | Q 972, AL 266, B 655, BH 538, PA 387, T 1.260, PL 236, P 556, I 183, S 555, SU 270, VQ 62 | 473 | 564 | 122 | 1.500 | 4.270 | 8 / 2138.0 | 10 melhorias |
| 17 | Q 803, AL 333, B 510, BH 572, PA 193, T 1.260, PL 251, P 623, I 207, S 597, SU 294, VQ 23 | 478 | 630 | 242 | 2.451 | 6.135 | 8 / 2265.0 | 14 melhorias |
| 18 | Q 1.170, AL 226, B 605, BH 582, PA 350, T 1.270, PL 264, I 186, S 582, SU 306, VQ 60 | 484 | 528 | 122 | 2.893 | 7.708 | 8 / 2441.0 | 14 melhorias |
| 19 | Q 1.043, AL 317, B 940, BH 738, PA 201, T 1.260, PL 302, P 363, I 171, S 569, SU 428, VQ 91 | 490 | 644 | 242 | 3.608 | 9.147 | 9 / 2629.0 | 15 melhorias |
| 20 | Q 1.354, AL 46, B 963, BH 451, PA 263, F 150, T 1.453, PL 192, P 302, I 42, S 560, SU 194, VQ 69 | 490 | 778 | 242 | 3.880 | 9.796 | 9 / 2804.0 | 13 melhorias |
| 21 | Q 1.409, AL 196, BH 726, PA 180, F 45, T 456, PL 244, I 150, S 679, SU 341 | 490 | 424 | 67 | 3.896 | 9.344 | 9 / 3012.0 | 11 melhorias |
| 22 | Q 1.402, AL 341, B 1.310, BH 1.024, PA 156, F 135, T 1.600, PL 335, P 1.431, I 384, S 527, SU 548, VQ 102 | 490 | 654 | 242 | 4.875 | 12.378 | 10 / 3248.0 | 13 melhorias |
| 23 | Q 1.728, AL 227, B 1.277, BH 1.095, PA 367, F 150, T 1.798, PL 464, I 174, S 581, SU 511, VQ 126 | 496 | 864 | 122 | 5.460 | 13.933 | 10 / 3510.0 | 13 melhorias |
| 24 | Q 1.330, AL 162, B 1.186, BH 1.152, PA 176, F 120, T 1.712, PI 18, PL 463, I 184, S 536, SU 568, VQ 50 | 498 | 518 | 242 | 5.600 | 14.732 | 10 / 3726.0 | 12 melhorias |
| 25 | Q 1.829, AL 176, B 1.606, BH 1.116, PA 230, F 120, T 1.840, PI 57, PL 491, I 189, S 618, SU 419, VQ 55 | 502 | 812 | 122 | 6.404 | 15.638 | 10 / 3980.0 | 12 melhorias |
| 26 | Q 1.575, AL 150, B 1.451, BH 1.284, PA 178, F 150, T 2.035, PI 40, PL 482, P 908, I 177, S 578, SU 618, VQ 38 | 502 | 592 | 242 | 6.980 | 16.986 | 10 / 4198.0 | 12 melhorias; podia: grand_hotel |
| 27 | RE 1.000, Q 1.852, AL 307, B 1.341, BH 1.252, PA 318, F 200, T 1.884, PI 20, PL 528, P 597, I 155, S 647, SU 620, VQ 96 | 505 | 644 | 242 | 24.600 | 1.812 | 10 / 4466.0 | grand_hotel + 1 melhorias; podia: grand_hotel |
| 28 | RE 3.500, Q 1.654, AL 219, BH 1.059, PA 151, F 75, M 44, H 7.546, HN 536, T 578, PI 40, PL 341, R 779, I 156, S 645, SU 484, VQ 15 | 1.405 | 556 | 2.867 | 10.040 | 4.766 | 10 / 4710.0 | equipe:garcom_hotel, salao_jogos + 5 melhorias; podia: salao_jogos |
| 29 | Q 1.379, AL 304, B 1.941, BH 1.368, E 3.800, FI 104, PA 199, F 225, M 161, H 7.350, HN 952, T 2.393, PL 447, P 693, R 1.360, I 158, S 577, SU 506, VQ 107 | 1.453 | 538 | 679 | 16.060 | 10.061 | 10 / 4970.0 | 22 melhorias |
| 30 | Q 2.163, AL 301, B 2.147, BH 1.522, FI 381, PA 317, F 250, M 377, H 8.105, HN 1.071, T 2.871, PL 524, P 510, R 1.228, I 198, S 681, SU 478, VQ 144 | 1.457 | 890 | 704 | 18.220 | 12.058 | 10 / 5273.0 | 21 melhorias |
| 31 | Q 1.927, AL 261, B 1.593, BH 1.528, FI 155, PA 164, F 325, M 404, H 12.515, HN 1.399, T 3.887, PL 544, P 860, R 1.272, I 187, S 638, SU 584, VQ 183 | 1.457 | 766 | 974 | 23.350 | 13.937 | 10 / 5596.0 | 23 melhorias |
| 32 | Q 2.979, AL 251, B 2.005, BH 1.658, FI 153, PA 416, F 325, M 160, H 13.899, HN 1.918, T 4.084, PL 634, P 1.114, R 1.697, I 173, S 569, SU 696, VQ 150 | 1.463 | 898 | 634 | 26.555 | 17.269 | 10 / 5984.0 | 22 melhorias |
| 33 | Q 2.489, AL 147, B 2.199, BH 1.102, FI 155, PA 106, F 325, M 389, H 8.207, HN 1.942, T 4.197, PL 417, R 1.630, I 265, S 642, SU 348, VQ 155 | 1.470 | 704 | 624 | 23.620 | 15.566 | 10 / 6318.0 | 18 melhorias |
| 34 | Q 2.879, AL 309, B 2.453, BH 1.825, FI 154, PA 363, F 325, M 348, H 7.406, HN 1.861, T 4.220, PL 665, P 452, R 1.526, I 306, S 649, SU 771, VQ 65 | 1.473 | 1.072 | 634 | 23.320 | 15.644 | 10 / 6692.0 | 16 melhorias |
| 35 | Q 2.825, AL 191, BH 1.784, FI 164, PA 217, F 160, M 434, H 7.348, HN 2.291, T 1.059, PL 456, R 1.465, I 321, S 805, SU 674, VQ 64 | 1.473 | 582 | 1.199 | 19.425 | 13.223 | 10 / 7031.0 | 12 melhorias |
| 36 | Q 2.826, AL 572, B 2.848, BH 2.046, E 3.696, FI 155, PA 293, F 520, M 595, H 5.822, HN 1.943, T 4.924, PL 748, P 1.733, R 2.113, I 480, S 626, SU 794, VQ 108 | 1.473 | 936 | 589 | 26.900 | 16.166 | 10 / 7404.0 | 15 melhorias |
| 37 | Q 3.110, AL 252, B 3.053, BH 2.122, FI 398, PA 495, F 520, M 1.124, H 8.585, HN 1.554, T 5.326, PL 826, P 1.005, R 1.277, I 282, S 783, SU 1.127, VQ 90 | 1.473 | 978 | 324 | 27.800 | 17.520 | 10 / 7792.0 | 14 melhorias |
| 38 | Q 2.953, AL 453, B 3.194, BH 2.236, FI 131, PA 261, F 840, M 603, H 5.863, HN 1.748, T 5.718, PI 64, PL 792, P 550, R 2.170, I 268, S 705, SU 1.429, VQ 122 | 1.473 | 960 | 474 | 26.985 | 17.726 | 10 / 8170.0 | 12 melhorias |
| 39 | Q 3.551, AL 97, B 3.775, BH 1.467, FI 141, PA 368, F 780, M 403, H 14.337, HN 2.133, T 5.626, PL 500, P 1.268, R 2.534, I 66, S 741, SU 515, VQ 125 | 1.477 | 1.004 | 354 | 33.540 | 19.779 | 10 / 8583.0 | 13 melhorias |
| 40 | Q 3.018, AL 595, B 3.167, BH 2.507, FI 145, PA 280, F 900, M 475, H 12.379, HN 2.133, T 6.868, PL 866, P 1.773, R 2.011, I 683, S 746, SU 1.090, VQ 98 | 1.477 | 922 | 534 | 33.020 | 23.559 | 10 / 8949.0 | 11 melhorias |
| 41 | Q 3.337, AL 536, B 3.368, BH 2.647, FI 148, PA 540, F 900, M 434, H 18.001, HN 2.876, T 7.111, PL 898, R 2.851, I 319, S 901, SU 1.190, VQ 126 | 1.477 | 842 | 414 | 41.160 | 25.851 | 10 / 9329.0 | 12 melhorias |
| 42 | Q 3.881, AL 379, BH 2.039, FI 152, PA 275, F 240, M 434, H 8.587, HN 2.886, T 1.399, PL 595, R 2.091, I 349, S 952, SU 1.146, VQ 250 | 1.477 | 782 | 939 | 27.480 | 20.828 | 10 / 9712.0 | 7 melhorias |
| 43 | Q 3.344, AL 602, B 3.132, BH 2.422, E 3.328, FI 143, PA 323, F 900, M 532, H 8.079, HN 3.188, T 8.039, PL 846, P 4.216, R 2.616, I 749, S 880, SU 1.541, VQ 86 | 1.477 | 932 | 614 | 38.740 | 24.030 | 10 / 10104.0 | 8 melhorias |
| 44 | Q 4.062, AL 127, B 3.186, BH 1.525, FI 396, PA 303, F 1.020, M 442, H 8.096, HN 2.932, T 9.675, PL 550, R 3.476, I 158, S 905, SU 611, VQ 122 | 1.477 | 928 | 414 | 34.920 | 23.877 | 10 / 10525.0 | 6 melhorias |
| 45 | Q 3.639, AL 458, B 3.432, BH 2.478, FI 130, PA 322, F 1.020, M 337, H 26.794, HN 3.711, T 9.464, PL 908, P 465, R 3.348, I 368, S 876, SU 1.394, VQ 91 | 1.477 | 942 | 614 | 50.800 | 29.279 | 10 / 10907.0 | 7 melhorias |
| 46 | Q 4.136, AL 131, B 3.255, BH 1.537, FI 152, PA 348, F 900, M 275, H 14.807, HN 3.572, T 8.600, PL 558, P 3.307, R 3.030, I 163, S 853, SU 460, VQ 239 | 1.477 | 894 | 409 | 44.700 | 28.122 | 10 / 11343.0 | 5 melhorias |
| 47 | Q 3.718, AL 459, B 3.398, BH 2.503, FI 154, PA 290, F 960, M 478, H 17.133, HN 4.016, T 8.523, PI 36, PL 891, P 2.765, R 3.648, I 416, S 842, SU 1.488, VQ 70 | 1.477 | 748 | 509 | 39.800 | 37.376 | 10 / 11707.0 | 4 melhorias |
| 48 | Q 3.862, AL 290, B 3.227, BH 2.612, FI 142, PA 623, F 1.020, M 577, H 24.718, HN 5.440, T 9.675, PL 910, R 4.589, I 436, S 915, SU 1.129, VQ 255 | 1.480 | 938 | 514 | 57.100 | 37.765 | 10 / 12134.0 | 5 melhorias |
| 49 | Q 3.866, AL 389, BH 2.198, FI 141, PA 250, F 420, M 428, H 11.769, HN 5.325, T 2.699, PL 625, R 2.911, I 316, S 989, SU 1.199, VQ 155 | 1.480 | 830 | 2.519 | 39.600 | 27.016 | 10 / 12506.0 | 3 melhorias |
| 50 | Q 3.876, AL 450, B 3.728, BH 2.614, E 12.008, FI 405, PA 277, F 900, M 604, H 16.162, HN 5.129, T 8.562, PI 146, PL 878, P 5.150, R 3.547, I 431, S 806, SU 1.123, VQ 126 | 1.480 | 988 | 659 | 44.000 | 46.811 | 10 / 12898.0 | 3 melhorias |
| 51 | Q 3.711, AL 366, B 3.622, BH 2.665, FI 152, PA 669, F 1.020, M 141, H 23.480, HN 5.362, T 9.637, PI 72, PL 911, R 3.217, I 397, S 937, SU 1.401, VQ 273 | 1.480 | 824 | 294 | 55.000 | 47.246 | 10 / 13317.0 | 3 melhorias |
| 52 | Q 3.578, AL 586, B 3.613, BH 2.622, FI 144, PA 294, F 960, M 486, H 24.414, HN 5.362, T 8.542, PI 36, PL 956, P 3.080, R 3.093, I 820, S 748, SU 1.549, VQ 136 | 1.480 | 838 | 594 | 0 | 105.352 | 10 / 13711.0 | — |
| 53 | Q 4.379, AL 468, B 3.361, BH 2.591, FI 139, PA 630, F 900, M 340, H 29.134, HN 4.896, T 8.370, PI 36, PL 917, R 4.614, I 379, S 858, SU 1.221, VQ 184 | 1.480 | 1.012 | 469 | 0 | 165.809 | 10 / 14125.0 | — |
| 54 | Q 1.885, AL 90, B 3.371, BH 1.551, FI 136, PA 227, F 180, M 493, H 22.277, HN 5.829, T 1.206, PL 527, R 4.811, I 127, S 781, SU 732, VQ 41 | 1.480 | 788 | 339 | 0 | 207.465 | 10 / 14330.0 | — |
| 55 | RE 1.500, Q 4.250, AL 97, B 3.532, BH 1.558, FI 144, PA 318, F 960, M 525, H 10.712, HN 5.362, T 8.888, PL 525, P 2.371, R 3.188, I 170, S 821, SU 538, VQ 274 | 1.480 | 802 | 509 | 0 | 250.407 | 10 / 14760.0 | — |
| 56 | RE 1.000, Q 4.129, AL 229, BH 2.184, FI 155, PA 299, F 240, M 584, H 18.370, HN 4.663, T 1.730, PL 603, R 2.708, I 403, S 968, SU 1.180, VQ 250 | 1.480 | 810 | 2.459 | 0 | 285.354 | 10 / 15139.0 | — |
| 57 | Q 3.683, AL 354, B 3.923, BH 2.461, E 12.008, FI 368, PA 307, F 1.020, M 339, H 27.296, HN 4.197, T 9.464, PL 885, P 3.873, R 4.710, I 434, S 790, SU 1.305, VQ 94 | 1.480 | 968 | 584 | 0 | 359.833 | 10 / 15541.0 | — |
| 58 | Q 4.124, AL 391, B 3.664, BH 2.437, FI 136, PA 665, F 960, M 427, H 21.730, HN 4.896, T 8.851, PL 908, R 3.780, I 282, S 905, SU 1.166, VQ 130 | 1.480 | 900 | 354 | 0 | 412.550 | 10 / 15948.0 | — |
| 59 | Q 3.906, AL 600, B 3.234, BH 2.532, FI 151, PA 330, F 1.020, M 297, H 23.485, HN 4.896, T 9.195, PL 877, P 2.036, R 2.554, I 708, S 837, SU 1.532, VQ 233 | 1.480 | 722 | 509 | 0 | 468.262 | 10 / 16360.0 | — |
| 60 | Q 4.152, AL 232, B 3.155, BH 2.520, FI 149, PA 724, F 1.020, M 566, H 21.355, HN 4.430, T 9.195, PL 943, P 1.080, R 3.899, I 391, S 858, SU 1.225, VQ 99 | 1.480 | 1.102 | 394 | 0 | 521.279 | 10 / 16778.0 | — |
| 61 | Q 3.928, AL 514, B 3.482, BH 2.551, FI 159, PA 321, F 1.020, M 683, H 31.476, HN 5.595, T 9.502, PI 109, PL 917, R 3.949, I 441, S 873, SU 1.310, VQ 302 | 1.480 | 946 | 494 | 0 | 585.490 | 10 / 17191.0 | — |
| 62 | Q 4.495, AL 350, B 3.553, BH 2.585, FI 139, PA 785, F 1.020, M 256, H 15.995, HN 5.595, T 9.330, PL 886, P 3.198, R 2.819, I 375, S 927, SU 1.084, VQ 268 | 1.480 | 1.048 | 514 | 0 | 636.107 | 10 / 17619.0 | — |

### Proposto — medio, semente 0

[CSV diário completo](../../tools/ue58/balance/results/proposto_medio_diario_seed0.csv).

| Dia | Renda por fonte | Salários | Estoque | Outras saídas | Investimento | Caixa final | Nível / XP | Compras / expansões compráveis |
|---|---|---|---|---|---|---|---|---|
| 1 | RE 530, Q 464 | 0 | 118 | 150 | 570 | 306 | 2 / 138.0 | equipe:atendente, kiosk_tables, neon; podia: drinks; kiosk_tables |
| 2 | RE 420, Q 684, VQ 53 | 30 | 295 | 2 | 703 | 433 | 3 / 334.0 | drinks, grill + 1 melhorias; podia: drinks; grill |
| 3 | Q 834, VQ 37 | 32 | 400 | 85 | 225 | 562 | 4 / 452.0 | 3 melhorias |
| 4 | RE 350, Q 233 | 32 | 120 | 5 | 264 | 724 | 4 / 478.0 | 3 melhorias |
| 5 | RE 200, Q 1.043, VQ 56 | 32 | 259 | 5 | 1.200 | 527 | 4 / 631.0 | bar; podia: bar |
| 6 | Q 969, B 277, BH 217, VQ 41 | 35 | 433 | 11 | 1.160 | 393 | 5 / 833.0 | equipe:bartender, negocio:sorveteria |
| 7 | Q 873, B 217, BH 234, I 96, VQ 12 | 117 | 490 | 11 | 196 | 1.010 | 5 / 971.0 | 2 melhorias |
| 8 | Q 911, B 408, BH 466, I 272, VQ 29 | 117 | 332 | 131 | 1.613 | 904 | 6 / 1127.0 | negocio:aluguel + 2 melhorias; podia: pousada |
| 9 | RE 1.100, Q 1.107, AL 301, B 384, BH 469, I 211, VQ 62 | 165 | 534 | 661 | 2.400 | 778 | 7 / 1470.0 | pousada; podia: pousada |
| 10 | RE 1.100, Q 782, AL 464, B 431, BH 473, I 375, VQ 69 | 165 | 304 | 143 | 2.460 | 1.400 | 7 / 1650.0 | equipe:camareira, equipe:recepcionista, pool; podia: passeios; pool |
| 11 | Q 1.098, AL 404, B 469, BH 468, PI 30, PL 165, P 954, I 244, VQ 31 | 237 | 586 | 33 | 3.720 | 687 | 7 / 1831.0 | equipe:piscineiro, passeios, negocio:souvenir + 1 melhorias; podia: passeios |
| 12 | Q 749, AL 276, B 592, BH 487, T 234, PI 20, PL 214, I 219, S 472, VQ 84 | 317 | 456 | 187 | 2.330 | 743 | 8 / 2005.0 | equipe:guia, negocio:food_truck + 2 melhorias |
| 13 | Q 1.078, AL 294, B 480, BH 509, PA 418, T 1.260, PI 10, PL 233, P 342, I 218, S 515, VQ 22 | 414 | 496 | 242 | 2.920 | 2.050 | 8 / 2193.0 | negocio:surfe + 5 melhorias |
| 14 | Q 1.235, AL 218, B 54, BH 422, PA 182, PI 20, PL 153, I 173, S 749, SU 386, VQ 22 | 469 | 568 | 42 | 1.200 | 3.385 | 8 / 2381.0 | 8 melhorias |
| 15 | Q 840, AL 274, B 651, BH 576, PA 209, T 1.032, PI 10, PL 223, P 517, I 176, S 561, SU 421, VQ 11 | 473 | 718 | 242 | 2.186 | 5.266 | 9 / 2533.0 | 13 melhorias |
| 16 | Q 1.412, AL 64, B 754, BH 373, PA 286, T 990, PL 150, P 274, I 95, S 695, SU 199 | 478 | 684 | 122 | 2.497 | 6.777 | 9 / 2735.0 | 13 melhorias |
| 17 | Q 1.131, AL 265, B 582, BH 647, PA 155, T 1.225, PI 51, PL 313, P 584, I 189, S 564, SU 706, VQ 34 | 481 | 590 | 242 | 3.421 | 8.489 | 9 / 2948.0 | 15 melhorias |
| 18 | Q 1.485, AL 59, B 866, BH 452, PA 248, T 1.222, PL 198, P 314, I 109, S 627, SU 172, VQ 98 | 487 | 686 | 122 | 3.636 | 9.408 | 9 / 3172.0 | 13 melhorias |
| 19 | Q 1.317, AL 277, B 1.093, BH 873, PA 151, F 135, T 1.530, PI 93, PL 321, P 336, I 229, S 545, SU 719, VQ 102 | 490 | 722 | 242 | 4.358 | 11.316 | 10 / 3458.0 | 13 melhorias |
| 20 | Q 1.700, AL 209, B 1.399, BH 965, PA 366, F 150, T 1.587, PI 30, PL 371, P 206, I 136, S 549, SU 675, VQ 62 | 490 | 760 | 242 | 5.155 | 13.073 | 10 / 3753.0 | 14 melhorias |
| 21 | Q 2.111, AL 217, BH 931, PA 184, F 60, T 499, PI 31, PL 262, I 189, S 655, SU 477, VQ 245 | 490 | 622 | 67 | 5.000 | 12.755 | 10 / 4083.0 | 12 melhorias |
| 22 | Q 1.424, AL 224, B 1.349, BH 1.107, PA 179, F 120, T 1.648, PI 102, PL 412, P 753, I 253, S 572, SU 903, VQ 70 | 496 | 654 | 242 | 5.870 | 14.610 | 10 / 4362.0 | 13 melhorias |
| 23 | Q 2.172, AL 237, B 1.506, BH 1.207, PA 365, F 135, T 1.980, PI 19, PL 488, P 775, I 153, S 616, SU 704, VQ 209 | 498 | 704 | 122 | 6.854 | 16.999 | 10 / 4714.0 | 13 melhorias |
| 24 | Q 1.686, AL 263, B 1.315, BH 1.282, PA 141, F 60, T 501, PI 40, PL 497, P 770, I 235, S 548, SU 775 | 502 | 732 | 172 | 6.920 | 16.785 | 10 / 4955.0 | 12 melhorias |
| 25 | RE 1.000, Q 2.109, AL 300, B 1.501, BH 1.274, PA 355, F 225, T 2.026, PI 20, PL 506, I 169, S 542, SU 840, VQ 214 | 502 | 808 | 122 | 24.600 | 1.836 | 10 / 5300.0 | grand_hotel + 1 melhorias; podia: grand_hotel |
| 26 | RE 3.500, Q 1.861, AL 145, B 1.684, BH 777, PA 144, F 200, M 16, H 11.718, HN 655, T 1.943, PL 314, P 522, R 894, I 96, S 584, SU 419 | 1.402 | 570 | 1.182 | 14.720 | 9.434 | 10 / 5611.0 | equipe:garcom_hotel, salao_jogos + 12 melhorias; podia: salao_jogos |
| 27 | Q 2.295, AL 200, B 1.832, BH 1.441, FI 118, PA 292, F 275, M 174, H 10.431, HN 1.071, T 2.528, PL 481, P 603, R 1.262, I 149, S 620, SU 630, VQ 176 | 1.453 | 900 | 3.474 | 18.700 | 9.486 | 10 / 5988.0 | 24 melhorias |
| 28 | Q 2.734, AL 299, BH 1.240, E 3.800, FI 130, PA 170, M 308, H 8.201, HN 1.131, PI 44, PL 369, R 862, I 195, S 635, SU 731, VQ 111 | 1.453 | 592 | 1.024 | 16.360 | 11.017 | 10 / 6428.0 | 18 melhorias |
| 29 | Q 1.959, AL 347, B 2.302, BH 1.614, FI 146, PA 181, F 75, M 151, H 9.422, HN 1.533, T 525, PI 72, PL 560, P 1.336, R 1.207, I 208, S 599, SU 1.121, VQ 119 | 1.457 | 916 | 729 | 19.610 | 11.783 | 10 / 6762.0 | 19 melhorias |
| 30 | Q 3.144, AL 31, B 2.200, BH 1.011, FI 363, PA 172, F 350, M 358, H 5.595, HN 1.845, T 3.997, PL 378, P 380, R 1.347, I 88, S 562, SU 279, VQ 61 | 1.457 | 668 | 1.614 | 19.175 | 11.029 | 10 / 7185.0 | 16 melhorias |
| 31 | Q 2.932, AL 344, B 2.451, BH 1.705, E 2.976, FI 388, PA 207, F 325, M 1.006, H 5.264, HN 1.328, T 4.220, PI 53, PL 652, P 1.140, R 1.515, I 357, S 543, SU 926, VQ 162 | 1.463 | 920 | 704 | 22.880 | 13.557 | 10 / 7604.0 | 18 melhorias |
| 32 | Q 3.180, AL 335, B 2.177, BH 1.801, FI 137, PA 373, F 300, M 621, H 7.320, HN 1.214, T 4.004, PI 82, PL 694, P 233, R 1.649, I 356, S 603, SU 830, VQ 180 | 1.470 | 1.144 | 444 | 22.740 | 13.848 | 10 / 8077.0 | 16 melhorias |
| 33 | Q 2.770, AL 197, B 2.370, BH 1.853, FI 132, PA 200, F 600, M 230, H 11.739, HN 1.924, T 4.801, PI 168, PL 712, P 2.116, R 1.920, I 397, S 630, SU 1.621, VQ 140 | 1.473 | 942 | 1.109 | 28.755 | 16.089 | 10 / 8472.0 | 18 melhorias |
| 34 | Q 3.533, AL 108, B 2.718, BH 1.235, E 2.464, FI 146, PA 315, F 560, M 971, H 8.875, HN 1.845, T 5.379, PL 462, R 1.999, I 122, S 828, SU 392, VQ 143 | 1.473 | 942 | 509 | 26.950 | 18.311 | 10 / 8959.0 | 15 melhorias |
| 35 | Q 4.153, AL 255, BH 1.939, FI 146, PA 268, M 486, H 13.645, HN 1.943, PI 32, PL 512, R 1.143, I 256, S 810, SU 1.220, VQ 158 | 1.473 | 1.054 | 374 | 26.000 | 16.377 | 10 / 9438.0 | 13 melhorias |
| 36 | Q 3.259, AL 673, B 3.306, BH 2.266, FI 426, PA 213, F 960, M 73, H 16.414, HN 2.622, T 5.943, PL 704, P 1.294, R 1.853, I 453, S 685, SU 1.113, VQ 98 | 1.473 | 892 | 2.764 | 34.185 | 19.417 | 10 / 9821.0 | 15 melhorias |
| 37 | Q 4.104, AL 67, B 3.662, BH 1.404, E 6.764, FI 139, PA 239, F 840, M 289, H 7.719, HN 2.919, T 6.240, PL 515, P 3.109, R 2.047, I 54, S 856, SU 567, VQ 146 | 1.473 | 872 | 534 | 35.080 | 23.139 | 10 / 10324.0 | 13 melhorias |
| 38 | Q 3.832, AL 225, B 4.002, BH 1.532, FI 158, PA 227, F 840, M 702, H 5.089, HN 2.470, T 6.398, PL 518, R 2.116, I 360, S 739, SU 732, VQ 74 | 1.477 | 920 | 534 | 30.680 | 19.542 | 10 / 10777.0 | 10 melhorias |
| 39 | Q 4.012, AL 338, B 3.465, BH 2.498, FI 145, PA 548, F 900, M 470, H 17.401, HN 2.397, T 7.288, PI 109, PL 917, P 860, R 2.437, I 319, S 900, SU 1.096, VQ 113 | 1.477 | 1.112 | 2.749 | 38.400 | 22.017 | 10 / 11222.0 | 11 melhorias |
| 40 | Q 1.892, AL 198, B 3.760, BH 1.525, E 7.904, FI 148, PA 286, F 180, M 442, H 16.012, HN 2.886, T 1.032, PL 557, R 2.456, I 280, S 720, SU 1.389, VQ 96 | 1.477 | 650 | 524 | 37.240 | 23.888 | 10 / 11509.0 | 9 melhorias |
| 41 | Q 5.101, AL 10, B 3.185, BH 1.525, FI 144, PA 416, F 900, M 760, H 12.413, HN 3.188, T 8.242, PL 541, P 3.188, R 2.147, I 198, S 1.001, SU 893, VQ 134 | 1.477 | 1.006 | 694 | 36.060 | 28.638 | 10 / 12016.0 | 7 melhorias |
| 42 | Q 4.311, AL 460, BH 2.138, FI 151, PA 302, F 300, M 482, H 12.402, HN 3.372, T 2.093, PI 73, PL 596, R 1.925, I 348, S 968, SU 1.696, VQ 241 | 1.477 | 948 | 2.434 | 31.200 | 24.437 | 10 / 12478.0 | 5 melhorias |
| 43 | Q 4.330, AL 595, B 4.247, BH 2.573, E 8.816, FI 152, PA 347, F 960, M 215, H 15.142, HN 4.020, T 9.234, PI 109, PL 869, P 1.575, R 2.985, I 385, S 915, SU 2.000, VQ 273 | 1.477 | 1.148 | 689 | 43.800 | 37.064 | 10 / 12982.0 | 6 melhorias |
| 44 | Q 4.189, AL 351, B 3.431, BH 2.482, FI 371, PA 534, F 1.020, M 582, H 12.020, HN 3.750, T 9.714, PI 36, PL 871, P 1.815, R 3.212, I 458, S 921, SU 1.512, VQ 144 | 1.477 | 828 | 544 | 44.700 | 36.928 | 10 / 13439.0 | 5 melhorias |
| 45 | Q 3.620, AL 483, B 4.050, BH 2.595, FI 158, PA 273, F 1.020, M 646, H 23.568, HN 4.618, T 8.986, PI 72, PL 883, P 1.271, R 3.289, I 443, S 812, SU 1.828, VQ 110 | 1.477 | 944 | 2.764 | 49.800 | 40.668 | 10 / 13851.0 | 5 melhorias |
| 46 | Q 4.874, AL 459, B 3.512, BH 2.563, E 11.324, FI 159, PA 664, F 1.020, M 459, H 12.769, HN 4.812, T 9.848, PI 36, PL 887, P 1.160, R 2.715, I 578, S 926, SU 1.924, VQ 156 | 1.477 | 1.150 | 374 | 59.700 | 38.813 | 10 / 14363.0 | 5 melhorias |
| 47 | Q 4.269, AL 393, B 3.545, BH 2.527, FI 142, PA 275, F 1.020, M 744, H 12.739, HN 3.772, T 9.291, PI 73, PL 959, P 2.562, R 4.547, I 419, S 782, SU 1.692, VQ 209 | 1.480 | 838 | 429 | 55.000 | 31.026 | 10 / 14842.0 | 4 melhorias |
| 48 | RE 1.500, Q 4.502, AL 406, B 3.899, BH 2.628, FI 135, PA 685, F 1.020, M 485, H 22.410, HN 4.430, T 9.215, PI 73, PL 936, P 445, R 3.172, I 404, S 1.042, SU 1.452, VQ 226 | 1.480 | 1.254 | 2.734 | 51.000 | 33.623 | 10 / 15331.0 | 3 melhorias |
| 49 | RE 1.000, Q 5.201, AL 465, BH 2.164, E 12.008, FI 138, PA 322, M 902, H 28.707, HN 4.430, PI 36, PL 606, R 3.404, I 401, S 937, SU 1.541, VQ 170 | 1.480 | 1.026 | 254 | 20.000 | 73.294 | 10 / 15847.0 | 1 melhorias |
| 50 | Q 4.510, AL 584, B 3.390, BH 2.519, FI 150, PA 277, F 900, M 480, H 23.627, HN 5.129, T 8.850, PI 145, PL 884, P 2.905, R 3.205, I 405, S 938, SU 2.040, VQ 312 | 1.480 | 982 | 549 | 0 | 131.532 | 10 / 16327.0 | — |
| 51 | Q 4.056, AL 474, B 3.584, BH 2.590, FI 397, PA 748, F 1.140, M 235, H 14.725, HN 5.595, T 9.992, PI 73, PL 952, P 421, R 3.433, I 418, S 916, SU 1.190, VQ 85 | 1.480 | 1.148 | 2.699 | 0 | 177.228 | 10 / 16752.0 | — |
| 52 | Q 3.732, AL 362, B 3.384, BH 2.505, E 12.008, FI 141, PA 423, F 960, M 583, H 13.632, HN 4.430, T 8.965, PI 182, PL 898, P 2.327, R 3.977, I 540, S 921, SU 1.698, VQ 142 | 1.480 | 712 | 629 | 0 | 236.216 | 10 / 17217.0 | — |
| 53 | Q 4.672, AL 540, B 3.532, BH 2.593, FI 166, PA 592, F 1.020, M 563, H 32.067, HN 4.197, T 9.292, PI 219, PL 909, P 1.581, R 3.654, I 432, S 839, SU 1.923, VQ 146 | 1.480 | 1.100 | 534 | 0 | 302.039 | 10 / 17711.0 | — |
| 54 | Q 3.906, AL 352, B 3.077, BH 2.554, FI 152, PA 378, F 1.140, M 279, H 31.147, HN 4.430, T 9.363, PI 73, PL 914, P 1.593, R 3.741, I 569, S 864, SU 1.521, VQ 166 | 1.480 | 882 | 2.749 | 0 | 363.147 | 10 / 18135.0 | — |
| 55 | Q 5.028, AL 368, B 3.519, BH 2.492, E 12.008, FI 136, PA 800, F 960, M 175, H 41.536, HN 5.829, T 9.023, PI 73, PL 877, P 1.130, R 2.604, I 346, S 1.003, SU 1.492, VQ 154 | 1.480 | 1.078 | 614 | 0 | 449.527 | 10 / 18654.0 | — |

### Proposto — dedicado, semente 0

[CSV diário completo](../../tools/ue58/balance/results/proposto_dedicado_diario_seed0.csv).

| Dia | Renda por fonte | Salários | Estoque | Outras saídas | Investimento | Caixa final | Nível / XP | Compras / expansões compráveis |
|---|---|---|---|---|---|---|---|---|
| 1 | RE 530, Q 766 | 0 | 321 | 150 | 680 | 295 | 2 / 172.0 | equipe:atendente, kiosk_tables, drinks; podia: drinks; kiosk_tables |
| 2 | RE 420, Q 802, VQ 19 | 30 | 275 | 2 | 668 | 561 | 3 / 378.0 | neon, grill + 2 melhorias; podia: grill; neon |
| 3 | Q 888, VQ 30 | 32 | 425 | 5 | 900 | 118 | 4 / 504.0 | negocio:sorveteria |
| 4 | RE 550, Q 1.039, I 514, VQ 126 | 72 | 340 | 5 | 1.275 | 655 | 5 / 739.0 | bar + 1 melhorias; podia: bar |
| 5 | Q 1.058, B 219, BH 394, I 415, VQ 163 | 72 | 430 | 11 | 1.735 | 656 | 6 / 1026.0 | equipe:bartender, negocio:aluguel + 1 melhorias |
| 6 | RE 300, Q 1.059, AL 419, B 402, BH 480, I 318, VQ 122 | 162 | 558 | 11 | 2.400 | 624 | 6 / 1268.0 | pousada; podia: pousada |
| 7 | RE 1.900, Q 1.148, AL 148, B 412, BH 257, P 471, I 127, VQ 30 | 162 | 330 | 673 | 2.460 | 1.492 | 7 / 1607.0 | equipe:camareira, equipe:recepcionista, pool; podia: passeios; pool |
| 8 | Q 1.089, AL 515, B 293, BH 493, PI 60, PL 181, P 1.114, I 350, VQ 59 | 235 | 629 | 153 | 3.864 | 766 | 7 / 1826.0 | equipe:piscineiro, passeios, negocio:souvenir + 3 melhorias; podia: passeios |
| 9 | Q 1.217, AL 305, B 449, BH 506, T 234, PI 40, PL 223, I 251, S 665, VQ 56 | 311 | 694 | 67 | 2.376 | 1.263 | 8 / 2060.0 | equipe:guia, negocio:food_truck + 3 melhorias |
| 10 | Q 978, AL 425, B 474, BH 510, PA 180, T 1.355, PI 20, PL 221, P 750, I 242, S 566, VQ 38 | 408 | 558 | 242 | 3.109 | 2.706 | 8 / 2284.0 | negocio:surfe + 7 melhorias |
| 11 | Q 1.293, AL 336, B 433, BH 507, PA 428, T 1.355, PI 20, PL 234, P 99, I 189, S 532, SU 528, VQ 39 | 473 | 704 | 202 | 2.112 | 5.208 | 9 / 2536.0 | 14 melhorias |
| 12 | Q 405, AL 80, B 659, BH 357, PA 164, T 273, PL 152, P 492, I 100, S 680, SU 430, VQ 47 | 478 | 424 | 172 | 2.283 | 5.691 | 9 / 2714.0 | 13 melhorias |
| 13 | Q 1.598, AL 322, B 593, BH 584, PA 419, T 1.296, PI 22, PL 274, P 115, I 203, S 672, SU 524, VQ 70 | 481 | 800 | 242 | 3.118 | 7.741 | 9 / 2986.0 | 15 melhorias |
| 14 | Q 1.864, AL 336, B 78, BH 615, PA 178, T 351, PI 13, PL 218, I 176, S 654, SU 566, VQ 76 | 481 | 700 | 67 | 3.383 | 8.236 | 10 / 3258.0 | 14 melhorias |
| 15 | Q 1.417, AL 309, B 875, BH 750, PA 222, F 135, T 1.326, PI 40, PL 313, P 762, I 251, S 565, SU 884, VQ 154 | 484 | 714 | 242 | 4.216 | 10.582 | 10 / 3535.0 | 14 melhorias |
| 16 | Q 2.022, AL 275, B 1.222, BH 917, PA 339, F 165, T 1.735, PI 30, PL 380, P 250, I 191, S 662, SU 626, VQ 130 | 484 | 844 | 122 | 5.000 | 13.075 | 10 / 3907.0 | 14 melhorias |
| 17 | Q 1.739, AL 180, B 1.026, BH 592, PA 171, F 165, T 1.517, PL 240, P 528, I 174, S 639, SU 387, VQ 61 | 487 | 710 | 242 | 5.535 | 13.521 | 10 / 4237.0 | 14 melhorias |
| 18 | Q 2.319, AL 281, B 1.284, BH 1.173, PA 379, F 150, T 1.832, PI 17, PL 424, P 420, I 171, S 682, SU 699, VQ 38 | 493 | 862 | 122 | 6.030 | 15.883 | 10 / 4597.0 | 14 melhorias |
| 19 | Q 1.747, AL 339, B 1.350, BH 1.141, PA 229, F 165, T 2.094, PI 54, PL 461, P 234, I 239, S 624, SU 900, VQ 94 | 498 | 696 | 242 | 7.174 | 16.945 | 10 / 4944.0 | 14 melhorias; podia: grand_hotel |
| 20 | RE 1.000, Q 2.766, AL 84, B 1.727, BH 779, PA 214, F 165, T 1.985, PL 282, I 101, S 583, SU 425, VQ 225 | 502 | 1.010 | 242 | 24.000 | 1.526 | 10 / 5366.0 | grand_hotel; podia: grand_hotel |
| 21 | RE 3.500, Q 2.569, AL 377, B 148, BH 1.081, PA 184, F 60, M 261, H 6.615, HN 417, T 672, PI 38, PL 339, R 800, I 219, S 612, SU 832, VQ 126 | 1.402 | 652 | 2.847 | 10.620 | 4.854 | 10 / 5778.0 | equipe:garcom_hotel, salao_jogos + 7 melhorias; podia: salao_jogos |
| 22 | Q 798, AL 89, B 1.671, BH 707, E 3.800, FI 344, PA 188, F 60, M 66, H 14.180, HN 952, T 501, PL 281, P 1.194, R 1.234, I 102, S 624, SU 464, VH 150, VQ 33 | 1.450 | 498 | 2.009 | 18.200 | 10.136 | 10 / 6041.0 | 28 melhorias |
| 23 | Q 3.081, AL 222, B 1.824, BH 1.318, E 2.400, FI 436, PA 355, F 225, M 119, H 10.893, HN 1.249, T 2.466, PL 531, P 408, R 1.193, I 212, S 650, SU 712, VQ 155 | 1.454 | 918 | 1.449 | 21.480 | 13.283 | 10 / 6494.0 | 26 melhorias |
| 24 | Q 2.560, AL 529, B 2.305, BH 1.585, CP 600, E 1.600, FI 444, PA 196, F 300, M 367, H 10.251, HN 1.428, T 3.042, PL 527, P 556, R 1.145, I 453, S 628, SU 976, VQ 134 | 1.454 | 928 | 3.344 | 24.870 | 12.313 | 10 / 6921.0 | 25 melhorias |
| 25 | Q 4.060, AL 306, B 2.008, BH 1.719, E 4.712, FI 140, PA 355, F 350, M 700, H 7.399, HN 1.697, T 4.018, PI 74, PL 624, P 1.008, R 1.259, I 168, S 559, SU 1.054, VQ 132 | 1.454 | 1.094 | 3.109 | 25.035 | 13.963 | 10 / 7500.0 | 21 melhorias |
| 26 | Q 3.404, AL 336, B 2.206, BH 1.713, E 4.712, FI 147, PA 142, F 325, M 690, H 6.855, HN 1.549, T 4.161, PI 81, PL 676, P 978, R 1.508, I 314, S 521, SU 1.399, VQ 226 | 1.461 | 984 | 2.824 | 25.980 | 14.657 | 10 / 8040.0 | 20 melhorias |
| 27 | Q 4.124, AL 349, B 2.463, BH 1.830, E 5.168, FI 139, PA 407, F 325, M 392, H 9.343, HN 1.861, T 3.980, PI 137, PL 725, R 1.106, I 258, S 574, SU 915, VQ 209 | 1.467 | 1.174 | 2.789 | 27.800 | 15.732 | 10 / 8605.0 | 19 melhorias |
| 28 | Q 4.466, AL 360, B 139, BH 1.699, E 5.852, FI 152, PA 224, F 200, M 380, H 10.912, HN 1.833, T 1.252, PI 28, PL 474, R 1.076, I 309, S 871, SU 1.307, VQ 108 | 1.467 | 1.026 | 2.579 | 27.045 | 15.258 | 10 / 9171.0 | 16 melhorias |
| 29 | Q 3.759, AL 82, B 3.190, BH 1.318, E 5.852, FI 416, PA 170, F 600, M 595, H 12.568, HN 1.943, T 5.394, PL 425, P 2.938, R 1.519, I 90, S 642, SU 649, VQ 198 | 1.470 | 960 | 2.859 | 33.600 | 18.718 | 10 / 9663.0 | 18 melhorias |
| 30 | Q 4.186, AL 362, B 2.998, BH 2.218, E 5.852, FI 405, PA 467, F 900, M 535, H 11.832, HN 2.040, T 5.616, PI 64, PL 790, R 2.334, I 311, S 827, SU 1.222, VQ 76 | 1.473 | 1.124 | 2.649 | 34.985 | 21.521 | 10 / 10184.0 | 16 melhorias |
| 31 | Q 4.030, AL 462, B 2.952, BH 2.398, CP 150, E 6.308, FI 397, PA 211, F 900, M 322, H 9.975, HN 2.617, T 5.832, PI 33, PL 822, P 2.273, R 2.037, I 349, S 695, SU 2.107, VQ 290 | 1.473 | 910 | 2.729 | 38.740 | 22.829 | 10 / 10688.0 | 15 melhorias |
| 32 | Q 4.978, AL 413, B 3.893, BH 2.398, E 6.764, FI 160, PA 519, F 900, M 976, H 8.234, HN 2.021, T 6.663, PI 35, PL 878, R 2.005, I 393, S 711, SU 1.646, VQ 141 | 1.477 | 1.038 | 2.634 | 39.820 | 21.587 | 10 / 11261.0 | 13 melhorias |
| 33 | Q 4.245, AL 171, B 3.564, BH 1.552, E 7.220, FI 156, PA 294, F 1.020, M 229, H 23.518, HN 2.996, T 7.808, PL 548, P 2.106, R 2.188, I 250, S 805, SU 973, VQ 22 | 1.477 | 1.102 | 2.754 | 46.640 | 29.278 | 10 / 11785.0 | 13 melhorias |
| 34 | Q 5.027, AL 567, B 3.543, BH 2.594, E 7.904, FI 138, PA 803, F 1.140, M 812, H 8.863, HN 3.049, T 8.993, PL 904, R 2.402, I 481, S 824, SU 1.885, VQ 284 | 1.477 | 1.020 | 2.694 | 45.940 | 28.360 | 10 / 12367.0 | 10 melhorias |
| 35 | Q 5.935, AL 138, BH 1.317, E 8.360, FI 144, PA 189, F 420, M 514, H 14.513, HN 3.079, T 2.474, PL 359, R 2.316, I 216, S 1.115, SU 830, VQ 392 | 1.477 | 1.188 | 2.639 | 40.120 | 25.248 | 10 / 12995.0 | 7 melhorias |
| 36 | Q 4.552, AL 108, B 3.941, BH 1.601, E 8.816, FI 383, PA 210, F 1.080, M 297, H 10.894, HN 3.865, T 9.182, PL 487, P 5.258, R 2.805, I 267, S 853, SU 1.119, VQ 82 | 1.477 | 988 | 2.899 | 42.800 | 32.884 | 10 / 13481.0 | 6 melhorias |
| 37 | Q 5.383, AL 406, B 3.685, BH 2.549, E 9.728, FI 327, PA 582, F 1.020, M 433, H 14.469, HN 3.924, T 8.836, PI 109, PL 967, R 3.368, I 487, S 898, SU 2.103, VQ 73 | 1.477 | 1.072 | 2.669 | 52.700 | 34.312 | 10 / 14015.0 | 6 melhorias |
| 38 | Q 3.533, AL 761, B 3.352, BH 2.627, E 10.868, FI 143, PA 361, F 300, M 678, H 15.641, HN 3.614, T 1.394, PI 36, PL 963, R 3.349, I 532, S 864, SU 2.820, VQ 70 | 1.477 | 892 | 2.759 | 49.800 | 31.290 | 10 / 14486.0 | 5 melhorias |
| 39 | Q 5.133, AL 182, B 3.213, BH 1.488, E 11.324, FI 144, PA 460, F 1.140, M 520, H 21.307, HN 4.603, T 9.465, PL 551, P 3.218, R 5.011, I 211, S 878, SU 804, VQ 122 | 1.477 | 1.128 | 2.524 | 59.700 | 36.236 | 10 / 15047.0 | 5 melhorias |
| 40 | Q 4.283, AL 408, B 3.838, BH 2.539, E 12.008, FI 163, PA 358, F 1.140, M 633, H 18.594, HN 5.325, T 9.708, PI 73, PL 931, P 394, R 3.593, I 558, S 772, SU 2.798, VQ 222 | 1.477 | 872 | 2.789 | 55.000 | 44.435 | 10 / 15552.0 | 4 melhorias |
| 41 | RE 1.500, Q 5.462, AL 170, B 3.354, BH 1.559, E 12.008, FI 148, PA 409, F 1.080, M 241, H 18.191, HN 4.430, T 9.654, PL 562, P 1.089, R 3.468, I 198, S 904, SU 808, VQ 210 | 1.480 | 1.230 | 2.829 | 51.000 | 53.340 | 10 / 16159.0 | 3 melhorias |
| 42 | RE 1.000, Q 5.104, AL 441, B 559, BH 2.196, E 12.008, FI 153, PA 320, F 360, M 556, H 18.965, HN 5.362, T 2.491, PI 36, PL 614, R 2.425, I 449, S 980, SU 1.671, VQ 222 | 1.480 | 816 | 2.559 | 20.000 | 84.397 | 10 / 16713.0 | 1 melhorias |
| 43 | Q 4.261, AL 399, B 3.404, BH 2.518, E 12.008, FI 414, PA 250, F 1.140, M 506, H 15.899, HN 4.663, T 9.711, PI 36, PL 867, P 2.960, R 4.858, I 477, S 758, SU 2.066, VQ 279 | 1.480 | 1.004 | 2.754 | 0 | 146.632 | 10 / 17230.0 | — |
| 44 | Q 5.677, AL 473, B 4.284, BH 2.590, E 12.008, FI 146, PA 749, F 1.140, M 685, H 16.618, HN 4.197, T 9.618, PI 109, PL 936, R 3.217, I 422, S 949, SU 2.009, VQ 144 | 1.480 | 1.058 | 2.714 | 0 | 207.350 | 10 / 17803.0 | — |
| 45 | Q 4.643, AL 319, B 2.478, BH 2.636, E 12.008, FI 149, PA 354, F 1.200, M 450, H 31.350, HN 5.129, T 10.035, PI 72, PL 957, P 4.871, R 3.914, I 485, S 814, SU 2.481, VQ 338 | 1.480 | 1.128 | 2.809 | 0 | 286.617 | 10 / 18370.0 | — |
| 46 | Q 4.908, AL 450, B 3.735, BH 2.565, E 12.008, FI 148, PA 762, F 1.140, M 274, H 20.784, HN 5.595, T 9.918, PI 146, PL 898, R 3.870, I 539, S 931, SU 2.303, VQ 280 | 1.480 | 1.082 | 2.774 | 0 | 352.536 | 10 / 18963.0 | — |
| 47 | Q 4.046, AL 362, B 3.965, BH 2.450, E 12.008, FI 148, PA 388, F 1.080, M 507, H 21.851, HN 5.129, T 9.518, PI 146, PL 909, P 1.761, R 4.188, I 440, S 984, SU 2.373, VQ 144 | 1.480 | 970 | 2.809 | 0 | 419.673 | 10 / 19477.0 | — |
| 48 | Q 6.028, AL 88, B 3.042, BH 1.586, E 12.008, FI 130, PA 402, F 1.140, M 852, H 21.773, HN 4.430, T 9.978, PL 543, P 2.022, R 4.267, I 207, S 840, SU 900, VQ 225 | 1.480 | 1.118 | 2.794 | 0 | 484.742 | 10 / 20110.0 | — |

## MUDANÇAS PROPOSTAS

**Não aplicadas aos JSON do jogo.** São candidatos para teste no editor, com valor atual validado pelo simulador. Os quatro números abaixo foram alterados somente em memória e simulados juntos; o efeito individual de cada um não foi isolado. JSON Pointer usa índices de array começando em zero.

| Arquivo em Content/Data | Campo JSON exato | Valor atual | Valor novo | Motivo |
|---|---|---|---|---|
| definitions.json | `/expansions/grand_hotel/cost` | 30000 | 24000 | Reduzir a acumulação anterior ao hotel, preservando fama 9, carnaval e pré-requisitos. |
| definitions.json | `/campaign/19/qty` | 4000 | 3300 | Reduzir a cauda de vendas após adquirir o conteúdo; calibrar nas escalas de 16 e 24 minutos. |
| restaurant.json | `/events/1/income` | 5600 | 3800 | Reduzir o retorno automático do casamento: 5600 por 2200 supera amplamente os outros contratos. |
| customization.json | `/price_mult/4` | 30 | 20 | Diminuir a cauda de compras de nível 5, sem aumentar os bônus econômicos de decoração. |

### Resultado com todas as propostas em memória

| Perfil | Marco | Dia P10 / P50 / P90 | P50 a 16 min/dia | P50 a 24 min/dia | Concluíram |
|---|---|---|---|---|---|
| casual | Grand Hotel | 26 / 29.5 / 31 | 7.9 h | 11.8 h | 30/30 |
| casual | Tela de fim do EA | 27 / 30.5 / 32 | 8.1 h | 12.2 h | 30/30 |
| casual | Campanha | 56 / 57.5 / 60 | 15.3 h | 23.0 h | 30/30 |
| casual | Todas as compras finitas | 51 / 54 / 56.1 | 14.4 h | 21.6 h | 30/30 |
| medio | Grand Hotel | 23 / 24 / 25 | 6.4 h | 9.6 h | 30/30 |
| medio | Tela de fim do EA | 24 / 25 / 26 | 6.7 h | 10.0 h | 30/30 |
| medio | Campanha | 48 / 49 / 50 | 13.1 h | 19.6 h | 30/30 |
| medio | Todas as compras finitas | 47 / 48 / 49 | 12.8 h | 19.2 h | 30/30 |
| dedicado | Grand Hotel | 18.9 / 20 / 22 | 5.3 h | 8.0 h | 30/30 |
| dedicado | Tela de fim do EA | 19.9 / 21 / 23 | 5.6 h | 8.4 h | 30/30 |
| dedicado | Campanha | 41.9 / 42 / 43 | 11.2 h | 16.8 h | 30/30 |
| dedicado | Todas as compras finitas | 40 / 41.5 / 43 | 11.1 h | 16.6 h | 30/30 |

As propostas aproximam a mediana do médio da janela desejada nas duas conversões, mas o P90 e a sensibilidade podem ultrapassar 20 horas na referência de 24 minutos. Não prometem duração fixa. A proposta de vendas é uma meta de campanha, não uma forma de criar mais conteúdo.

O principal problema de fim do EA **não se resolve só por JSON**: a tela usa uma condição C++ diferente da campanha e pode aparecer cedo. Essa alteração fica exclusivamente recomendada em `GPT_RELATORIO.md`, assim como a correção das penalidades e do reinício dos pedidos VIP. Nenhuma dessas correções foi aplicada nem presumida no cenário proposto. Medir o build e decidir qual dos três marcos define o fim comercial deve vir antes de publicar a duração da campanha.
