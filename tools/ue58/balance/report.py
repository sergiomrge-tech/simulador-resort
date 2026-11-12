"""Gera as tabelas do relatório a partir dos CSV/JSON, sem recalcular números à mão."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'pacote2' / 'results'
SUMMARY = json.loads((RESULTS/'summary.json').read_text(encoding='utf-8'))
PROFILES = ('casual','medio','dedicado')


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(str(x).replace('|','/') for x in r)+' |' for r in rows])+'\n'


def num(x):
    return f'{float(x):,.0f}'.replace(',','.')


def load_rows(scenario,profile):
    with (RESULTS/f'{scenario}_{profile}_diario_seed0.csv').open(encoding='utf-8') as f:
        return list(csv.DictReader(f))


def summary_rows(scenario):
    rows=[]
    for p in PROFILES:
        for key,title in [('grand_hotel','Grand Hotel'),('tela_fim_ea','Tela de fim do EA'),('campanha_completa','Campanha'),('todas_compras','Todas as compras finitas')]:
            m=SUMMARY[scenario][p]['marcos'][key]
            rows.append([p,title,f"{m['p10']:g} / {m['p50']:g} / {m['p90']:g}",f"{m['p50']*16/60:.1f} h",f"{m['p50']*24/60:.1f} h",f"{m['concluidos']}/30"])
    return rows


intro='''# Balanceamento — Pacote 2, meta de 6–10 horas até hotel e tela do EA

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

'''
profiles=json.loads((HERE/'profiles.json').read_text())
audit=json.loads((RESULTS/'source_features.json').read_text())
intro += '\n## Estado dos sistemas solicitados para o Pacote 2\n\n'
intro += 'A base recebeu três commits durante a tarefa e foi atualizada antes dos resultados finais. Todos os sistemas abaixo foram encontrados e suas fórmulas revisadas; não se reutilizaram os resultados da referência anterior.\n\n'
intro += table(['Recurso solicitado','Presença constatada'],[[k,'presente e contemplado' if v else 'ausente nesta base'] for k,v in audit['novidades'].items()])
intro += '\nO modelo registra hashes de Source e recusa execução se o snapshot divergir de source_features.json; novos commits exigem revisar as fórmulas antes de renovar o registro.\n\n'
intro+='\n### Hipóteses dos três perfis\n\nValores sem telemetria, expostos em `profiles.json` para substituição após teste.\n\n'
text=intro+table(['Perfil','Ações ativas/dia, incluindo morro','Sucesso por etapa','Atende tentativas do quiosque','Evento do hotel a cada','Guia passeio a cada','Chance de vitória'],[[p,f"{profiles[p]['active_seconds']} s",profiles[p]['success'],profiles[p]['kiosk_share'],f"{profiles[p]['event_every']} dias",f"{profiles[p]['tour_every']} dias",profiles[p]['win']] for p in PROFILES])
text+='''
O restante do dia é deslocamento, observação, espera ou atividades sem receita contada. A equipe atua em paralelo. O orçamento manual é único: quiosque, bar, recepção, minijogos, piscina, partidas e queixas disputam os mesmos segundos. Passeios e campeonato reservam tempo antes das tarefas opcionais. Tempo por ação é hipótese (8–35 s; passeio 120 s; partida de torneio 90 s). O atendente tem capacidade inicial de um produto a cada 11 s, afetada pelo balcão; há sensibilidade abaixo.

Política de investimento: reserva de R$ 100/250/1.200 conforme estágio; cargos elegíveis, expansões na ordem dos dados, negócios baratos e melhorias de menor custo. Melhorias usam até 30% do caixa disponível antes do hotel e 65% depois, com uma etapa por slot por dia. Isso é uma política reproduzível, não a estratégia ótima. O jogador cobra preços de referência e não explora o limite de 200% do preço. Decoração comprada fica equipada no maior nível. Ações narrativas ocorrem ao iniciar/fechar o dia; progressão intradiária é aproximada.

A recepção/limpeza de pousada, chegadas de bar e restaurante e tempos de expiração são discretizados por hora: a fila contínua e a navegação não são reproduzidas. No restaurante, a hipótese de espera é cook_minutes + 20 × (1 − sucesso do perfil), além de 14 s ativos por atendimento. Isso alimenta a gorjeta e a nota do crítico. A ordem horária agrega ações que no jogo ocorrem entre chamadas; não comprova os prazos de atendimento. O crítico também concorre pelo orçamento manual; não há estrela garantida. A preparação do bar usa uma nota média por perfil; gostos, fregueses e tempo exato não são emulados. No passeio não se simulam individualmente todas as opções de extras, golfinhos, colisão no coral ou remarcações; a política cancela mar bravo e usa notas agregadas. A limpeza manual completa de quarto com bônus `polished` não é modelada: a equipe limpa, e o jogador pode resolver queixas nos visitáveis. A probabilidade de responder queixa resume atraso dentro da hora. Estoque do quiosque, bar, frigobar, artesanato, postais e picolés têm desembolsos próprios; **não se inventou CMV de pastel ou casquinha**. O restaurante agora cobra peixe do fornecedor somente no pedido manual de mesa sem peixe em estoque, exatamente onde TakeKitchenFish é chamado. O modelo conserva a origem indiferenciada de stock.peixe, inclusive peixe comprado. Na montagem, 6 s por peça e até 2/8/10 peças por hora nos perfis casual/médio/dedicado são hipóteses; montar com E não tem chance de erro. Ofertas são aceitas com a probabilidade de engajamento do perfil. As peças prioritárias disputam o orçamento do dia antes das atividades opcionais; extras só depois das obrigatórias. Congressos às 10h deixam uma janela curta após acordar às 8h.

## Resultado atual: 30 sementes por perfil

'''+table(['Perfil','Marco','Dia P10 / P50 / P90','P50 a 16 min/dia','P50 a 24 min/dia','Concluíram'],summary_rows('atual'))
rows=[]
for sc in ['atual','proposto']:
    for p in PROFILES:
        m=SUMMARY[sc][p]['meta_atingida']
        rows.append([sc,p,f"{m['grand_hotel']['entre_6_e_10_h']}/{m['grand_hotel']['total']}",f"{m['tela_fim_ea']['entre_6_e_10_h']}/{m['tela_fim_ea']['total']}"])
text+='\n### Sementes na meta de 6–10 h (16 min/dia)\n\n'+table(['Cenário','Perfil','Grand Hotel','Tela do EA'],rows)
text+='''
A meta deste pacote é **6–10 horas até Grand Hotel e tela do EA**, não até a última missão da campanha ou a compra de todas as melhorias. A coluna efetiva usa 16 minutos, confirmados no código. A duração de campanha aparece como informação complementar. Comprar o catálogo inteiro e concluir a campanha podem ocorrer em ordem diferente; não publicar uma duração na loja com base só neste modelo.

## Quando as expansões ficam disponíveis e são compradas

Disponível = pré-requisitos/fama/capítulo alcançados; comprada = pagou mantendo reserva e a política de compras. São medianas em dias, não datas prometidas. Uma cadeia pode ficar disponível na mesma rodada de compras do fechamento.

'''
for scenario in ['atual','proposto']:
    rows=[]
    definitions=json.loads((ROOT/'unreal/MareAlta/Content/Data/definitions.json').read_text())
    for e in definitions['expansion_order']:
        row=[definitions['expansions'][e]['name']]
        for p in PROFILES:
            m=SUMMARY[scenario][p]['marcos'];row.append(f"{m['liberada:'+e]['p50']:g} → {m[e]['p50']:g}")
        rows.append(row)
    text+=f'### Cenário {scenario}\n\n'+table(['Expansão','Casual: disponível → comprada','Médio: disponível → comprada','Dedicado: disponível → comprada'],rows)+'\n'
text+='## Capítulos, negócios e experiências observadas\n\n'
keys=['capitulo:'+x['id'] for x in definitions['chapters']]+['negocio:'+x for x in definitions['businesses']]+['bar_secreto','passeio:jangada','vip_hotel_atendido','evento:formatura','evento:bodas','evento:empresa','montagem:casamento','montagem:aniversario','montagem:congresso','critico_atendido','estrela_restaurante:1','estrela_restaurante:3','campeonato_inscrito','fliperamas_jogados']
rows=[]
for key in keys:
    row=[key]
    for p in PROFILES:
        m=SUMMARY['atual'][p]['marcos'].get(key)
        row.append(f"{m['p50']:g} ({m['concluidos']}/30)" if m else 'não observado')
    rows.append(row)
text+=table(['Marco atual: dia mediano (execuções que atingiram)','Casual','Médio','Dedicado'],rows)
text+='''
Medianas de experiências só usam quem as viveu; a contagem evita transformar uma experiência opcional rara em uma conclusão garantida.

## Renda dominante, retorno e paredes

A tabela abaixo descreve a **semente 0 do médio**. Receita é entrada de caixa, portanto diárias incluem antecipação de várias noites; não confundir com lucro por competência. Fase pós-hotel começa no dia seguinte à compra; os sete dias finais permitem observar a renda depois das compras.

'''
for scenario in ['atual','proposto']:
    rs=load_rows(scenario,'medio');seed=list(csv.DictReader((RESULTS/f'{scenario}_medio_sementes.csv').open()))[0];hotel=int(seed['grand_hotel']);all_bought=int(seed['todas_compras'])
    groups=[('Antes do hotel',[r for r in rs if int(r['dia'])<=hotel]),('Hotel até todas as compras',[r for r in rs if hotel<int(r['dia'])<=all_bought]),('Após todas as compras',[r for r in rs if int(r['dia'])>all_bought])]
    rows=[]
    for name,group in groups:
        sources=Counter()
        for r in group:
            for k,v in r.items():
                if k.startswith('renda_') and k!='renda_total':sources[k[6:]]+=float(v or 0)
        total=sum(sources.values());top=', '.join(f'{k}: {v/total:.0%}' for k,v in sources.most_common(4))
        rows.append([name,len(group),num(sum(float(r['renda_total']) for r in group)/len(group)),num(sum(float(r['renda_total'])-float(r['despesas_total'])+float(r.get('despesa_investimentos',0)) for r in group)/len(group)),top])
    text+=f'### Renda por fase — {scenario}\n\n'+table(['Fase','Dias amostrados','Receita média/dia (R$)','Saldo antes de investimentos/dia (R$)','Quatro maiores parcelas da receita'],rows)+'\n'
    empty=[int(r['dia']) for r in rs if not r['compras'] and int(r['dia'])<=all_bought];runs=[]
    for d in empty:
        if runs and runs[-1][-1]==d-1:runs[-1].append(d)
        else:runs.append([d])
    longest=max(runs,key=len,default=[])
    tails=[r for r in rs if int(r['dia'])>all_bought]
    text+=f"Maior intervalo sem compra antes de completar o catálogo: **{str(longest[0])+'–'+str(longest[-1]) if longest else 'nenhum'}** ({len(longest)} dias). Depois do catálogo, caixa passou de **R$ {num(rs[all_bought-1]['caixa'])}** para **R$ {num(rs[-1]['caixa'])}** no dia {rs[-1]['dia']}. Isso revela ausência de uso finito adicional do dinheiro; receita diária continua entrando.\n\n"
text+='''
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

'''
rows=[]
for folder,label in [('sensitivity_rapido','8,8 s/produto'),('results','11 s/produto'),('sensitivity_lento','13,75 s/produto')]:
    path=RESULTS/'summary.json' if folder=='results' else HERE/'pacote2'/folder/'summary.json'
    if not path.exists():continue
    ss=json.loads(path.read_text())
    for sc in ['atual','proposto']:
        m=ss[sc]['medio']['marcos']['campanha_completa'];rows.append([label,sc,f"{m['p50']:g}",f"{m['p50']*16/60:.1f} h",f"{m['p50']*24/60:.1f} h"])
text+=table(['Hipótese de capacidade','Cenário','Dia mediano da campanha','16 min/dia','24 min/dia'],rows)
text+='''
A variação de habilidade e deslocamento pode ser maior que a variação entre sementes. Antes de aceitar os números propostos, medir pelo menos três sessões completas do perfil médio: tempo por produto, vendas/dia, tempo fora do quiosque, partidas e ocupação. Registrar também quando o jogador dorme mais cedo. Aumentar o número de sementes não corrige uma hipótese errada de capacidade.

## Tabelas dia a dia

Valores em R$, arredondados nesta apresentação. **Q** quiosque; **VQ** VIP do quiosque; **B** drinks; **BH** bar por hora; **P** pousada; **H** diárias do hotel; **HN** refeições noturnas; **M** frigobar; **VH** VIP hotel; **R** restaurante; **E** jantares/contratos do restaurante; **EM** eventos montados na praia; **T** passeios; **F** fotos; **PL** piscina; **PI** picolés; **I** sorveteria; **PA** pastel; **AL** aluguel; **S** souvenir; **SU** surfe; **FI** fichas; **PE** pebolim; **AR** fliperama; **AP** partidas/apostas recebidas; **CP** campeonato; **RE** recompensas. Fonte ausente na célula = zero, não desconhecida.

Salários incluem equipe contratada, funcionários dos negócios e R$ 900 da equipe fixa do hotel. Estoque reúne todos os desembolsos com prefixo `estoque_`. Outras despesas incluem manutenção, passeios, queixas, preparativos e taxas/perdas em partidas. Investimentos são as aquisições finitas. O CSV preserva cada categoria, centavos, caixa inicial, evento, chuva, ocupação, vendas acumuladas, todas as compras e as expansões que eram compráveis antes de gastar no fechamento. Como as células são arredondadas, a conciliação exata deve usar o CSV.

'''
codes={'quiosque':'Q','vip_quiosque':'VQ','bar_drinks':'B','bar_passivo':'BH','pousada':'P','hotel_diarias':'H','hotel_refeicoes_noturnas':'HN','frigobar':'M','vip_hotel':'VH','restaurante':'R','eventos_hotel':'E','montagem_hotel':'EM','passeios':'T','fotos_passeios':'F','pool_passivo':'PL','picoles':'PI','sorveteria':'I','food_truck':'PA','aluguel':'AL','souvenir':'S','surfe':'SU','fichas':'FI','pebolim':'PE','fliperama':'AR','sinuca_tenis':'AP','campeonato':'CP','recompensas':'RE'}
for scenario in ['atual','proposto']:
    for p in PROFILES:
        rs=load_rows(scenario,p);rows=[]
        for r in rs:
            revenue=', '.join(f"{codes.get(k[6:],k[6:])} {num(v)}" for k,v in r.items() if k.startswith('renda_') and k!='renda_total' and float(v or 0)) or '0'
            wages=sum(float(r.get('despesa_'+x,0)) for x in ['salarios','salarios_negocios','equipe_hotel']);stock=sum(float(v or 0) for k,v in r.items() if k.startswith('despesa_estoque_'));invest=float(r.get('despesa_investimentos',0));other=float(r['despesas_total'])-wages-stock-invest
            purchases=r['compras'].split('; ') if r['compras'] else []
            main=[x for x in purchases if not x.startswith(('custom:','receita:','bar:','negocio_nivel:'))];n=len(purchases)-len(main)
            bought=', '.join(main)+(' + ' if main and n else '')+(f'{n} melhorias' if n else '')
            possible=r.get('expansoes_compraveis_antes_das_compras','')
            if possible:bought+='; podia: '+possible
            rows.append([r['dia'],revenue,num(wages),num(stock),num(other),num(invest),num(r['caixa']),f"{r['fama_nivel']} / {r['fama_xp']}",bought or '—'])
        link='../../tools/ue58/balance/pacote2/results/'+f'{scenario}_{p}_diario_seed0.csv'
        text+=f'### {scenario.capitalize()} — {p}, semente 0\n\n[CSV diário completo]({link}).\n\n'+table(['Dia','Renda por fonte','Salários','Estoque','Outras saídas','Investimento','Caixa final','Nível / XP','Compras / expansões compráveis'],rows)+'\n'
text+='''## MUDANÇAS PROPOSTAS

**Não aplicadas aos JSON do jogo.** São candidatos para teste no editor, com valor atual validado pelo simulador. Os três números abaixo foram alterados somente em memória e simulados juntos; o efeito individual de cada um não foi isolado. JSON Pointer usa índices de array começando em zero.

'''
changes=json.loads((HERE/'proposed.json').read_text())
text+=table(['Arquivo em Content/Data','Campo JSON exato','Valor atual','Valor novo','Motivo'],[[c['file'],f"`{c['pointer']}`",c['current'],c['new'],c['reason']] for c in changes])
text+='''
### Resultado com todas as propostas em memória

'''+table(['Perfil','Marco','Dia P10 / P50 / P90','P50 a 16 min/dia','P50 a 24 min/dia','Concluíram'],summary_rows('proposto'))
text+='''
O alvo é o tempo até o Grand Hotel e a tela do EA na escala real do código. A campanha continua com 4.000 vendas: este pacote não reduz sua meta para forçar uma duração menor. A conversão de 24 minutos é uma referência separada, não o tempo efetivamente simulado. As propostas não prometem duração fixa.

A tela usa uma condição C++ diferente da campanha e pode aparecer antes das 4.000 vendas; a meta solicitada deste pacote usa explicitamente hotel e tela. As correções de fama, neon, aluguel, reserva ao dormir e reinício de VIP foram recebidas da outra IA na base e estão contempladas, sem edição de Source/Data neste PR. O perfil dedicado pode chegar antes das 6 h: a meta é o perfil médio, e aumentar o hotel para atrasar o dedicado prejudicaria o casual. Medir o build antes de publicar duração na loja.
'''
(ROOT/'docs/ue58/BALANCEAMENTO.md').write_text(text,encoding='utf-8')
print('Gerado docs/ue58/BALANCEAMENTO.md a partir de resultados reproduzíveis')
