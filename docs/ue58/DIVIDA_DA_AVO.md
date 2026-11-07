# A dívida de Dona Dilce — pacote para implementação

**Moeda decidida pelo Sergio (07/11/2026): R$ 1.000.000** (o jogo inteiro usa reais).

Base: efceab984ef6a1eb3dfc0cdd88ca9a7377586aaf. **Proposta, não implementada em C++.** [debt.json](../../unreal/MareAlta/Content/Data/debt.json) é um contrato novo; o jogo atual ainda não o lê. Os números de economia do jogo permanecem intactos.

## Uma dívida, um saldo, um botão

Dona Dilce foi morar com as amigas do bingo: não morreu. Junto do quiosque, deixou uma dívida de um milhão. Na chegada de ônibus, reutilizar a apresentação existente e mostrar a carta no primeiro acesso ao celular após criar a empresa. Não atrasar o ônibus nem exigir novo ator, cenário ou visita presencial. A carta fica disponível para releitura; o gerente aparece apenas por recado escrito do banco.

A dívida fica em um cartão dentro de **Finanças** do celular: principal, total pago, saldo restante e progresso. Um botão abre o valor livre e a confirmação mostra o caixa que restará. Pagamentos em qualquer horário, inclusive depois de dormir/carregar, são permitidos quando o jogo aceitar interação. Nenhum minijogo bancário, empréstimo adicional ou sistema de crédito.

**Decisão: sem parcela mínima, sem juros e sem multa.** weekly_minimum e interest_rate são zero. Um compromisso semanal obrigatório retiraria capital da pousada/bar justamente quando o casual precisa expandir, e criaria cálculos de atraso sem ajudar a meta. O saldo de um milhão continua sendo o objetivo final; os marcos dão direção sem impor uma punição diária.

Após sete dias completos sem pagamento, enviar o recado cômico de debt.json. Um por intervalo, com last_reminder_day persistido; pagar qualquer valor reinicia a contagem. Não tomar estoque, reduzir fama, fechar negócios, visitar fisicamente o jogador nem dar game over. Não há dívida crescente. Na demo, parar os lembretes ao atingir o teto amortizável.

## Marcos e final

| Pago | Saldo | Entrega única |
|---|---|---|
| R$ 250.000 (25%) | R$ 750.000 | Cartão “Um quarto mais leve” e comentário de Dona Dilce |
| R$ 500.000 (50%) | R$ 500.000 | Cartão “Metade da maré” e a piada do meio bolo |
| R$ 750.000 (75%) | R$ 250.000 | Cartão “Quase dá para respirar” e a dança da quitação |
| R$ 1.000.000 (100%) | zero | Tela final, fala da avó, créditos e continuar no mesmo resort |

Recompensas são narrativas e conquistas: **não devolvem dinheiro nem acrescentam fama**, portanto não fabricam renda para a própria dívida. Cartões curtos reutilizam a UI; sem novo asset ou animação obrigatória. Se um pagamento cruzar três marcos, consolidar a apresentação e marcar os três, sem três interrupções consecutivas.

No jogo completo, saldo zero é o novo objetivo final. Uma tela de quitação oferece créditos com base em CREDITS.md (tela textual a integrar) ou continuidade; créditos podem ser pulados. Nenhuma expansão, equipe, estoque ou save é removido. A festa da campanha permanece independente: não exige quitação e não significa que o banco já recebeu. Jogador que priorizar o milhão pode quitar antes de fazer tudo; não esconder o botão até 20 h nem exigir 100% de decoração.

Claude deve revisar a antiga tela de fim do EA (IsEndOfContentDue): no **jogo completo**, comprar expansões não deve ser anunciado como final definitivo antes da quitação. Na **demo**, preservar o gatilho atual de agradecimento, sem exigir a dívida. Nunca usar ea_end_shown como prova de dívida paga.

## Demo

Mostrar a carta, o saldo total e permitir pagamentos desde o começo. A tela de agradecimento continua nos marcos atuais da demo (~2 h), com a dívida restante no cartão de Finanças; **não precisa quitar para terminar**. Nas sementes, comparar o valor pago exatamente no dia fim_demo, não após dias de jogo livre.

Para garantir que a demo não encerre a história da dívida mesmo no jogo livre prolongado, limitar o **total amortizado a R$ 250.000** (demo_payment_cap), com explicação antes da confirmação. O primeiro marco fica acessível; 50/75/100% e a quitação ficam no jogo completo. Não interromper a operação ao alcançar o teto. Isto é uma decisão de escopo comercial proposta, não um bloqueio já existente. Em save legado com mais amortização, preservar o pago e impedir novos pagamentos até o modo completo; nunca devolver/descontar automaticamente. Não prometer migração de saves/App IDs antes de teste real.

## Contrato de save e transação

Novo objeto **State.prog.debt**, ausente hoje:

| Campo proposto | Inicial / significado |
|---|---|
| version | 1 |
| principal_cents | 100000000; congelado quando a dívida é criada |
| paid_cents | 0; acumulado de transferências efetivas, não patrimônio nem faturamento |
| created_day | dia de criação/migração |
| last_payment_day | created_day inicialmente; atualizar ao confirmar pagamento |
| last_reminder_day | 0; evita repetir o mesmo recado ao carregar |
| intro_seen | false; carta apresentada uma vez |
| milestones_seen | lista vazia; ids quarter/half/three_quarters já reconhecidos pelo jogador |
| finale_seen | false; somente após apresentar/dispensar o final completo |

Saldo é **principal_cents − paid_cents**, derivado; não manter um terceiro valor que possa divergir. Ausência do objeto em save antigo inicializa a dívida uma única vez, sem cobrar, apagar campos desconhecidos ou alterar o caixa. Este novo objetivo também se aplica a saves antigos; não fingir que ganhos anteriores já foram pagamentos. Não reinicializar uma dívida parcialmente paga ao atualizar o JSON.

Pseudofluxo para PayDebt, método novo: validar valor finito e centavos inteiros >0; conferir saldo, caixa e limite demo; rejeitar integralmente se exceder algum deles. Usar o fluxo Book para debitar uma vez, atualizar paid_cents e last_payment_day na mesma transação, salvar atomicamente e só depois mostrar recibo. Falha no save restaura ambos os valores. Bloquear reentrada do botão durante a operação. Não truncar silenciosamente um pedido maior para um valor menor. Assegurar 0 <= paid_cents <= principal_cents, sem arredondamento acumulativo; na fronteira float/centavos, converter/validar uma vez.

Os textos JSON com {N} são modelos: localizar primeiro e formatar depois, sem tratar as chaves como formato printf. Formatar os números uma única vez e manter R$ como especificado.

Ao carregar, reapresentar marcos pendentes se seus limiares já foram cruzados, mas não repetir recompensas. Como são apenas texto, a repetição após falha antes do reconhecimento não injeta dinheiro. Guardar o reconhecimento da tela separadamente do dinheiro pago. A fila de conquistas Steam também deve ser idempotente/offline, conforme [conquistas.md](../steam/conquistas.md).

## Campanha: trocas propostas, não aplicadas

Somente substituir o campo story dos ids abaixo em definitions.campaign. kind, item, qty, reward, a meta de 7.000 vendas e as condições dos capítulos ficam iguais. Os textos novos estão em debt.json → campaign_texts e nos 12 idiomas, para o extrator não descartar suas traduções antes da integração.

| Campo atual exato | Troca proposta |
|---|---|
| /campaign/0/story (id chegada) | campaign_texts.chegada: revela a dívida e a carta, preservando Dona Dilce viva no bingo |
| /campaign/14/story (id marealta) | campaign_texts.marealta: liga o Grand Hotel à capacidade de pagar a dívida |
| /campaign/20/story (id festa) | campaign_texts.festa: festa não é recibo de quitação |

Não substituir os textos da demo por uma promessa de final já acessível. Nenhum story foi trocado por este pacote.

## Política da simulação e reprodução

O jogo terá **pagamentos manuais livres**. A simulação precisa de uma escolha de jogador: ao fechar o dia, depois dos custos operacionais e antes das compras finitas, o perfil cooperativo paga **2% do saldo operacional positivo antes do hotel e 50% depois**, respeitando a reserva já usada pelo modelo (R$ 100/250/1.200) e o saldo da dívida. A fração não é débito automático, imposto nem obrigação do jogo. Reserva é uma hipótese de comportamento, não dinheiro protegido pelo banco.

Saldo operacional aqui é fluxo de caixa: entradas do dia menos saídas antes de investimentos/pagamentos, inclusive adiantamentos de diárias. Não confundir com lucro contábil. Por isso, 30 sementes não substituem cronometrar ações, medir gastos e testar perfis que adiem a dívida. Os perfis diferem no mesmo conjunto de tempos/habilidade do modelo anterior, não na taxa obrigatória de pagamento.

Baseline: debt-policy off mantém o milionário objetivo fora da conta para comparar com 20,3 h/37 h anteriores. O modo full ignora o bloqueio comercial da demo só no modelo; mode demo respeita full_game, mantém a campanha bloqueada e registra uma janela final de sete dias contando o dia fim_demo. Não alterar definitions.demo para simular.

```sh
python tools/ue58/balance_model.py --self-test
python tools/ue58/balance/test_debt.py
python tools/ue58/balance_model.py --days 360 --seeds 30 --debt-policy off --out tools/ue58/balance/pacote4/baseline
python tools/ue58/balance_model.py --days 360 --seeds 30 --out tools/ue58/balance/pacote4/results
python tools/ue58/balance_model.py --days 120 --seeds 30 --mode demo --out tools/ue58/balance/pacote4/demo
```

Cada execução gera atual/proposto, com/sem os dois ajustes de nível 5 em proposed.json, CSV diários por fonte e dívida, todas as sementes, estatísticas/censura, configuração e hashes. **540 trajetórias registradas**, todas com 30 sementes por perfil/cenário. Sem Unreal ou execução do C++; a parte da dívida representa a proposta futura.

## Aceite para o Claude

Testar novo save e migração sem perda de campos; carta única; valor zero/negativo/NaN/centavos e caixa insuficiente sem débito; dois cliques; save falhando; salto de 0 para 100%; marcos após load; lembretes em created_day+7 e created_day+14 sem juros; teto demo e save legado acima dele; final completo uma vez; continuar após créditos e após agradecimento da demo. Testar as conquistas com dados reais e fila offline. O saldo nunca muda por apenas abrir o celular.

## Resultado quantitativo

## 30 sementes por perfil: objetivo final e cauda de compras

540 trajetórias registradas: três execuções × dois cenários × três perfis × 30 sementes. O jogo completo usa limite de 360 dias, a demo 120. A coluna atual abaixo significa **economia atual mais dívida proposta**; baseline é o jogo sem pagamentos. O proposto aplica somente em memória os dois JSON Pointers de nível 5. Todos os valores em horas usam 16 minutos jogáveis/dia, sem contar pausas.

| Cenário | Perfil | Campanha P50 (h) | Dívida P50 (h) | Compras P50 (h) | Quitaram |
|---|---|---|---|---|---|
| Sem dívida (baseline) | casual | 23.2 | — | 40.3 | desligada |
| Sem dívida (baseline) | medio | 20.3 | — | 37.1 | desligada |
| Sem dívida (baseline) | dedicado | 18.1 | — | 32.5 | desligada |
| Dívida / economia atual | casual | 23.6 | 22.7 | 47.5 | 30/30 |
| Dívida / economia atual | medio | 20.5 | 20.3 | 43.7 | 30/30 |
| Dívida / economia atual | dedicado | 18.4 | 17.9 | 38.4 | 30/30 |
| Dívida / economia proposta | casual | 23.5 | 22.7 | 43.5 | 30/30 |
| Dívida / economia proposta | medio | 20.5 | 20.3 | 40.3 | 30/30 |
| Dívida / economia proposta | dedicado | 18.4 | 17.9 | 35.5 | 30/30 |

“Compras” continua sendo o catálogo finito usado no relatório anterior, não todas as conquistas. A dívida compete pelo mesmo caixa: não é um objetivo resolvido por mero faturamento ou patrimônio. Sem os descontos de nível 5, ela alonga a cauda; não foi escondido esse custo.

| Economia com dívida | Perfil | Quitação: dias P10/P50/P90 | Quitação: horas P10/P50/P90 |
|---|---|---|---|
| atual | casual | 83 / 85 / 87 | 22.1 / 22.7 / 23.2 |
| atual | medio | 75 / 76 / 78.1 | 20.0 / 20.3 / 20.8 |
| atual | dedicado | 66 / 67 / 68.1 | 17.6 / 17.9 / 18.2 |
| proposto | casual | 83 / 85 / 87 | 22.1 / 22.7 / 23.2 |
| proposto | medio | 75 / 76 / 78.1 | 20.0 / 20.3 / 20.8 |
| proposto | dedicado | 66 / 67 / 68 | 17.6 / 17.9 / 18.1 |

### Marcos da dívida — dias medianos (economia atual)

| Perfil | Primeiro pagamento | 25% | 50% | 75% | 100% |
|---|---|---|---|---|---|
| casual | 1.0 | 48.0 | 61.0 | 73.0 | 85.0 |
| medio | 1.0 | 42.0 | 54.0 | 65.0 | 76.0 |
| dedicado | 1.0 | 37.0 | 47.0 | 57.5 | 67.0 |

## Decisão econômica

Hipótese de comportamento em debt_policy.json: pagamento voluntário ao fechar o dia, **2% do saldo operacional de caixa positivo antes do hotel e 50% depois**, mantendo a reserva operacional preexistente do modelo. Não automatizar essa fração no jogo. Perfis usam os mesmos percentuais, variando tempo ativo/habilidade e fontes de renda como antes. Quem preferir comprar tudo ou não pagar não recebe final por cronômetro; o tempo depende de suas escolhas. Os modos cauteloso/intensivo ficam disponíveis como hipóteses alternativas, sem alegar estatísticas de 30 sementes deles neste relatório.

A quitação está perto da campanha de 7.000 vendas sem aumentar receitas, dar perdão ou prender o pagamento a uma missão. A festa não exige saldo zero. O baseline sem dívida confirma os números herdados; não se reduziu a meta de vendas para obter o resultado.

## Demo: o objetivo é apresentado, não quitado

mode demo bloqueia Grand Hotel/salão, preserva capítulos e termina nos marcos existentes. Total amortizável proposto: **R$ 250.000**; final completo indisponível. Nenhuma das 180 trajetórias demo quitou a dívida. Pagamentos já afetam levemente o ritmo de expansão; os preços da demo não foram editados.

| Perfil | Fim demo: dias P10/P50/P90 | P50 (h) | Dia fim semente 0 | Pago nesse dia, semente 0 | Saldo nesse dia, semente 0 |
|---|---|---|---|---|---|
| casual | 9.9/10/11 | 2.7 | 10 | R$ 241.63 | R$ 999758.37 |
| medio | 8/8.5/9.1 | 2.3 | 8 | R$ 287.41 | R$ 999712.59 |
| dedicado | 7/7/8 | 1.9 | 7 | R$ 246.89 | R$ 999753.11 |

O valor pago da tabela é a trajetória da semente 0 no dia exato de fim_demo; não é mediana nem total ao fim da janela adicional de jogo livre. Nenhuma compra de Grand Hotel ou salão foi feita nas trajetórias demo.

## MUDANÇAS PROPOSTAS — NÃO APLICADAS AO JOGO

Compensação parcial do novo desembolso de um milhão, somente no nível 5. Não mexe nos preços das expansões, receitas do hotel, pagamentos de eventos ou campanha. O milhão e as quatro etapas da dívida permanecem integrais. Aplicar preços somente junto da dívida implementada; isoladamente encurtam o catálogo. As mudanças são opcionais para teste; a quitação próxima de 20 h já funciona com a economia atual.

| Arquivo | JSON Pointer | Atual | Proposto | Motivo |
|---|---|---|---|---|
| customization.json | /price_mult/4 | 260 | 220 | Compensar parte do custo do milhão na cauda de compras: manter o 100% próximo de 40 h sem reduzir a dívida nem preços de expansões. |
| customization.json | /recipes/cost_mult/4 | 900 | 760 | Mesma compensação apenas no nível 5 de receitas; manter as 7.000 vendas e o ritmo de campanha. Proposta, não aplicada ao jogo. |


## Pacote 6 — roteiro de integração C++ (base 899e77a6)

O contrato executável de referência está em `tools/ue58/balance/debt_contract.py`; os **20 vetores/45 ações** de
`debt_vectors.json` são oráculos fixos em centavos. `test_debt_vectors.py` também confronta cada pagamento aceito ou
recusado com `balance_model.Model.pay_debt`. Isto testa a proposta em Python, não o jogo nem falhas reais de disco.

Pontos existentes a reaproveitar, lidos nesta base:

| Integração | Ponto real |
|---|---|
| Débito e extrato | `MareSimulation.cpp:103` `UMareSimulation::Book` altera `money`, `day_out` e `ledger`; incluir todos no rollback |
| Persistência e backup | `MareSimulation.cpp:493` `Save`, `:499` `WriteState`: `.tmp`, cópia `.bak` e move; usar retorno e não anunciar sucesso antecipado |
| Empresa / migração | `MareSimulation.cpp:114` `CreateCompany`; no carregamento, inicializar somente se `prog.debt` estiver ausente |
| Finanças | `MareGame.cpp:732` `SMarePhone::FinancePage`; inserir cartão antes de “Últimos lançamentos” |
| Abertura / fechamento | `MareGame.cpp:2496` `AMareController::OpenPhone`, `:2514` `ClosePhone`; manter navegação e bloqueios atuais |
| Carta existente | `MareIntro.cpp:146` `AMareIntro::ReadLetter`: carta afetiva já existe. Acrescentar a revelação da dívida no primeiro celular após criar empresa, sem substituir a carta inteira ou disparar duas cartas concorrentes |
| Fim e retomada | `MareGame.cpp:2047` `AMareController::ShowEndOfContent`, widget `SMareEndScreen`; reaproveitar enquadramento/pausa/retomada, separando o reconhecimento da dívida de `ea_end_shown` |
| Condição de fim atual | `MareEvents.cpp:53` `IsEndOfContentDue`, `:65` `MarkEndOfContentShown`; na demo manter a condição por expansões/capítulos; no completo não anunciar quitação só porque comprou tudo |
| Créditos | `MareGame.cpp:1834` `SMareMainMenu`, caso `EPage::Credits`; reutilizar conteúdo/apresentação sem carregar outro save nem iniciar um novo jogo |

### Pseudocódigo transacional

```text
EnsureDebt(day):
  se State.prog.debt existe: validar tipos/faixas, preservar principal e campos desconhecidos; não recriar
  senão: criar objeto com os campos da tabela do contrato; principal_cents = debt.json.principal * 100
         created_day = last_payment_day = day; last_reminder_day = 0
         paid_cents = 0; intro_seen = finale_seen = false; milestones_seen = []
  salvar a migração uma vez; abrir/fechar Finanças nunca debita

PayDebt(valor):
  se transação já em andamento: rejeitar segundo clique
  converter entrada monetária uma vez para centavos exatos, rejeitando NaN/Inf, bool e subcentavos
  d = State.prog.debt
  limite = demo ? min(principal_cents, demo_payment_cap * 100) : principal_cents
  validar inteiro > 0 e <= caixa_em_centavos e <= principal_cents-paid_cents e <= limite-paid_cents
  se inválido: mensagem phone.invalid/demo_limit; nenhuma alteração, nem cobrança parcial
  bloquear botão; snapshot profundo dos campos mutáveis da transação (não uma shared pointer para o mesmo objeto)
  Book(-valor_cents/100, texto localizado de phone.pay)
  d.paid_cents += valor_cents; d.last_payment_day = day
  se Save/WriteState falhar: restaurar money, day_out, ledger, prog.debt e demais efeitos capturados; destravar; erro
  se sucesso: destravar; mostrar recibo; recalcular saldo e marcos pendentes
  marcos = todos os limiares cruzados e ausentes de milestones_seen, em ordem
  apresentar em um único cartão; ao reconhecer, adicionar IDs e salvar; se falhar, permitir reapresentação
  avaliar conquistas e enfileirar desbloqueios idempotentes, inclusive offline
  se modo completo e paid_cents == principal_cents e !finale_seen: agendar cena final

Reminder(day):
  se saldo zero ou demo no/acima do teto: não enviar
  referência = max(created_day, last_payment_day, last_reminder_day)
  se day - referência >= reminder_every_days:
    enfileirar um recado; last_reminder_day = day; salvar
  repetir a chamada ou carregar no mesmo dia não repete o recado; saltar dias envia só um
```

Na migração, `principal_cents` existente fica congelado mesmo se o JSON mudar. Em demo com pagamento legado acima do
teto, manter o valor e bloquear apenas pagamentos futuros; `demo_payment_cap` não é saldo adicional por operação.
Valores em centavos são o contrato; `State.money` e `Book` hoje usam reais double, portanto conferir a fronteira de
conversão e tolerância de centavos, sem arredondar um pagamento inválido para um valor aceito.

### Celular e final, sem novo sistema

Em **Finanças**, cartão com `phone.title`, saldo derivado, total pago, principal original, progresso e botão `phone.pay`.
O botão abre valor livre; a confirmação usa `phone.confirm` com valor e caixa remanescente. No teto demo mostrar
`phone.demo_limit`, e em saldo zero mostrar `phone.settled`. Formatar **depois** de localizar a chave, com `{N}`;
manter R$ e os nomes. A carta curta usa `intro.*`; o flag `intro_seen` só é reconhecido depois da apresentação.

Final completo pendente: esperar não haver outro modal, fechar Finanças, usar a estrutura de `ShowEndOfContent` para
mostrar `finale.title/text/grandma`, botões Créditos e Continuar. Marcar `finale_seen` ao apresentar/dispensar com sucesso
e salvar; após falha de gravação, reapresentar é permitido e não dá dinheiro. Continuar fecha o modal e restaura
controles/pausa, preservando o mesmo slot, empresa, inventário, expansões e caixa. Os créditos também voltam ao mesmo
resort. Na demo, este final nunca dispara: continua valendo o agradecimento atual, sem exigir pagamento.

O modelo econômico antigo conta lembretes em dias múltiplos do intervalo e não persiste `last_reminder_day`; não copiar
essa simplificação para C++. Os vetores do contrato cobrem chamada repetida no mesmo dia e salto até o dia 30.
