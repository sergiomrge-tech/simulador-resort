# Relatório do pacote de Acesso Antecipado

06/11/2026. Repositório `sergiomrge-tech/simulador-resort`. Branch de trabalho **gpt/ea-pacote**, criada de **codex/ue58-migration**, referência **8e817f7a0813e4af628d6d317af54d50b67dbeba**. Os blobs de Source/Data lidos foram conferidos contra essa referência para evitar misturar trabalho concorrente.

> Registro histórico do pacote 1 / PR #7. Os números e achados desta primeira parte pertencem à referência indicada acima. A situação atual está na seção **Pacote 2** ao final.

## Entregas

- Ampliação de `tools/ue58/balance_model.py`: três perfis, sementes, economia por fonte, estoques, salários, manutenção, fama, capítulos, aquisições, quartos, VIPs, eventos, passeios, aluguel e salão de jogos.
- Parâmetros de comportamento em `tools/ue58/balance/profiles.json`; quatro propostas de valores em `proposed.json`, aplicadas apenas em memória e com validação do valor atual.
- Simulação principal com **30 sementes por perfil em cada cenário: 180 trajetórias**, mais sensibilidade de capacidade com dez sementes por perfil/cenário em cada extremo: **120 trajetórias adicionais**. Limite de 240 dias, com censura explícita se algum marco não fosse alcançado.
- Tabelas de todos os dias de cada perfil para a semente 0, receitas por fonte, despesas, caixa, fama, compras e expansões compráveis. CSV completos, estatísticas P10/P50/P90, configuração e hashes dos insumos em `tools/ue58/balance/`.
- [BALANCEAMENTO.md](BALANCEAMENTO.md) substitui o relatório antigo; `balance/report.py` reproduz suas tabelas a partir dos resultados.
- [Loja pt-BR](../steam/loja_pt-BR.md), [loja em inglês](../steam/loja_en.md), [questionário bilíngue](../steam/acesso_antecipado.md), [12 traduções da loja](../steam/loja_traducoes.md) e [tags e roteiro de dez capturas](../steam/tags_e_capturas.md).

Os textos comerciais não anunciam co-op, Steam Workshop, conquistas ou Cloud como recursos entregues. A reserva de casamento existente foi descrita como reserva de evento, sem inventar montagem física. Prazo de EA e política de aumento de preço não estão definidos nos documentos: as respostas explicitam essa situação, sem criar promessas comerciais.

## Achados principais

O código usa 1 minuto do jogo por segundo, mas reinicia às 8h: são **16 minutos jogáveis por dia até meia-noite**, além da pequena diferença do primeiro dia, pausas e menus. A referência de 24 minutos pedida foi apresentada como uma conversão alternativa do número de dias, sem inventar renda das oito horas não jogadas.

A tela de fim do EA, a campanha e a compra de todo o catálogo têm critérios diferentes. O relatório mostra as três durações separadamente. A escala de 16 minutos e a referência de 24 minutos não podem ser trocadas sem revisar as metas comerciais.

As propostas usam preços menores do hotel e da cauda de decoração, menos vendas na missão final e menor pagamento do casamento. O relatório contém os resultados atuais e propostos; as conclusões dependem da política de jogo e dos tempos presumidos, especialmente da capacidade do atendente. Não foi comprovada duração de campanha por uma pessoa real.

## Bugs e incoerências encontrados — nenhuma correção aplicada

Linhas relativas exclusivamente ao commit de referência. Os links apontam para os arquivos do repositório; outra IA pode mover as linhas depois deste pacote.

| Gravidade / natureza | Arquivo e linha | Problema observado | Correção recomendada e validação |
|---|---|---|---|
| Alta — código | [MareGame.cpp:2814](../../unreal/MareAlta/Source/MareAlta/MareGame.cpp#L2814) | `SaveClock+=DeltaSeconds` e o teste `SaveClock>=30` ficaram na mesma linha após `//`; o compilador trata ambos como comentário. O autosave periódico dessa função não executa. Isso não impede os saves explícitos das ações e ao dormir. | Separar comentário e instruções em linhas próprias. Testar uma sessão sem ações por mais de 30 s e conferir o arquivo do slot, inclusive após carregar. |
| Alta — código | [MareSimulation.cpp:418](../../unreal/MareAlta/Source/MareAlta/MareSimulation.cpp#L418), [MareHotelRooms.cpp:195](../../unreal/MareAlta/Source/MareAlta/MareHotelRooms.cpp#L195), [MareRental.cpp:106](../../unreal/MareAlta/Source/MareAlta/MareRental.cpp#L106) | `AddFame` retorna quando XP é menor ou igual a zero. Expirar pedido VIP e multar indevidamente um aluguel chamam essa função com valor negativo: o texto diz que perdeu fama, mas o XP não cai. | Permitir delta assinado com piso em zero, definir aviso de queda de nível e testar os dois chamadores. O cenário atual e o proposto mantêm o comportamento defeituoso. |
| Alta — código | [MareHotelRooms.cpp:99](../../unreal/MareAlta/Source/MareAlta/MareHotelRooms.cpp#L99), [MareHotelRooms.cpp:223](../../unreal/MareAlta/Source/MareAlta/MareHotelRooms.cpp#L223) e [MareStays.cpp:102](../../unreal/MareAlta/Source/MareAlta/MareStays.cpp#L102) | `vip_asked` pertence ao objeto do quarto e bloqueia novos pedidos pela presença do campo. Check-out e novo check-in não removem `vip_asked`/`vip_done`. O efeito passa de “uma vez por estadia” para “uma vez por quarto”, mesmo com novo hóspede. | Limpar os marcadores ao iniciar/encerrar cada estadia, ou ligá-los ao id da reserva. Testar duas estadias consecutivas no mesmo quarto, incluindo expiração e save/load. O modelo preserva a marca para não inflar VIPs recorrentes. |
| Alta — progressão | [MareEvents.cpp:53](../../unreal/MareAlta/Source/MareAlta/MareEvents.cpp#L53) contra [MareSimulation.cpp:297](../../unreal/MareAlta/Source/MareAlta/MareSimulation.cpp#L297) | A tela de fim do EA exige todas as expansões e capítulos, mas não os negócios, as melhorias, a fama final, as 4.000 vendas ou a festa da campanha. Pode agradecer e sugerir conclusão antes de grande parte da progressão. | Definir um único marco comercial com Sergio. Se for a campanha, condicionar a tela ao encerramento dela; se for só expansões, mudar a comunicação e apresentar as metas restantes. Acrescentar teste para “todas expansões, campanha incompleta”. Não é resolvido pelos quatro números JSON propostos. |
| Média — horário versus descrição | [MareSimulation.cpp:132](../../unreal/MareAlta/Source/MareAlta/MareSimulation.cpp#L132), [MareSimulation.cpp:277](../../unreal/MareAlta/Source/MareAlta/MareSimulation.cpp#L277), `definitions.json → expansions.neon.blurb` | A descrição do neon promete quiosque até 21h. `IsOpen` só lê `company.sim.end` (18 no save padrão); `BuyExpansion` não modifica esse campo e não foi encontrado outro vínculo entre esse desbloqueio e o horário. | Aplicar o efeito quando comprar/migrar neon, respeitando horário personalizado, ou ajustar a descrição. Testar quiosque às 20h antes/depois e após carregar. O modelo mantém 8h–18h. |
| Média — horário de evento | [MareRestaurant.cpp:135](../../unreal/MareAlta/Source/MareAlta/MareRestaurant.cpp#L135) e [MareRestaurant.cpp:122](../../unreal/MareAlta/Source/MareAlta/MareRestaurant.cpp#L122) | O texto de reserva anuncia `event_hour` (20h), mas a operação dispara quando `Started=Hour-1` chega a 20, isto é, no cruzamento de 21h. Dormir antes disso também pode fazer a reserva do dia ficar para trás sem receita. | Escolher se o contrato acontece no começo ou no fim da hora; alinhar o aviso e o gatilho. Definir cancelamento/adiamento para dormir cedo e testar 19h59, 20h, 21h e virada de dia. O modelo recebe às 21h. |
| Média — clima versus descrição | [MareRental.cpp:53](../../unreal/MareAlta/Source/MareAlta/MareRental.cpp#L53), [MareBusiness.cpp:17](../../unreal/MareAlta/Source/MareAlta/MareBusiness.cpp#L17), `definitions.json → businesses.aluguel.blurb` | O texto diz que aluguel fecha com mar bravo. A abertura comum só consulta horário, `RentalHour` continua gerando fila por clima e não chama `IsSeaRough`; a venda também não tem esse bloqueio. Passeios marítimos têm cancelamento explícito. | Bloquear novos aluguéis/chegadas com mar bravo e manter devoluções seguras, ou reescrever o texto se essa for a regra desejada. Testar tempestade e maré alta. O modelo conserva a divergência do código. |
| Média — painel versus fórmula | [MareSimulation.cpp:745](../../unreal/MareAlta/Source/MareAlta/MareSimulation.cpp#L745), [MareIceCream.cpp:26](../../unreal/MareAlta/Source/MareAlta/MareIceCream.cpp#L26), [MarePastel.cpp:26](../../unreal/MareAlta/Source/MareAlta/MarePastel.cpp#L26), [MareRental.cpp:33](../../unreal/MareAlta/Source/MareAlta/MareRental.cpp#L33), [MareSouvenir.cpp:28](../../unreal/MareAlta/Source/MareAlta/MareSouvenir.cpp#L28) | `BusinessRate` recebe a personalização `biz_*`, e a interface a usa como estimativa de renda. As funções de preço das quatro filas usam o multiplicador de nível, mas não o fator de personalização. Parte das melhorias pode aparentar retorno financeiro que não entra nas vendas. | Decidir quais efeitos cada slot deve produzir. Aplicar um multiplicador apropriado uma única vez nas vendas ou mostrar apenas efeitos realmente usados. Testar preço antes/depois de uma decoração e de uma melhoria de nível, para cada negócio. |
| Revisão de design — fluxo duplo | [MareSimulation.cpp:395](../../unreal/MareAlta/Source/MareAlta/MareSimulation.cpp#L395), [MareSimulation.cpp:765](../../unreal/MareAlta/Source/MareAlta/MareSimulation.cpp#L765) e [MareRestaurant.cpp:125](../../unreal/MareAlta/Source/MareAlta/MareRestaurant.cpp#L125) | Há refeições/bar genéricos do hotel à noite, além das vendas manuais/automáticas do restaurante. O bar de praia também tem receita horária e drinks separados. São fluxos confirmados; não é possível provar só por texto que são a mesma venda duplicada. Podem explicar a aceleração de renda. | Validar intenção econômica, atribuir origem clara no extrato e testar uma noite sem atendimento manual. Se forem fontes distintas, comunicar isso; se representarem o mesmo consumo, consolidar. O modelo conta os fluxos existentes separadamente. |
| Documentação divergente | `CHECKLIST_EXPANSOES.md:44`, `:478`, `ROADMAP_STEAM.md` | O roteiro antigo ainda lista expansões como passivas e partes de pesca/foto/negócios como futuras, apesar de já haver funções e dados. O checklist recente deixa montagem de eventos e crítico pendentes. `hotel_events.json`/`MareHotelEvents.cpp`, pedidos na tarefa, não existem nesta referência. | Usar o checklist mais recente para prioridade e C++/JSON para existência. Atualizar os documentos em tarefa separada; não criar arquivos de dados fictícios para preencher a análise. |

## Limites e itens que ficaram de fora

- Não houve editor, acesso ao PC, compilação C++, execução de `qa_gate.py`, build Shipping, benchmark, screenshots, publicação na Steam ou teste de integração Steam. O portão do projeto depende do ambiente Unreal; não se declara PASS dele com base em testes Python.
- A simulação é agregada, com aproximações por hora e ações presumidas. Não reproduz física, navegação, animação, fila contínua, todos os resultados de minijogos, incidentes cômicos, ondas/tsunami, gostos individuais do bar ou todas as alternativas dos passeios. As diferenças e seus possíveis impactos estão discriminados em `BALANCEAMENTO.md`.
- As visitas narrativas e as oferendas assumem jogador cooperativo que cumpre a rotina, sem provocar desastre. Pesca e fotografia mínimas da história são simplificadas, sem exploração de renda por pesca. Recompensas opcionais de cada quest e missão secundária não foram usadas para acelerar a curva.
- Escala de pessoal: um empregado por cargo ativo, integral com domingo de folga; segundo turno opcional não é necessário para o marco do catálogo. Não foi otimizada a melhor combinação de folgas, preços de venda ou apostas.
- Traduções são rascunhos de texto comercial, sem revisão nativa ou teste de layout da loja. Não foi prometida duração de 12–20 horas, data de versão completa, aumento de preço ou recurso não comprovado.
- Não foram corrigidos os bugs listados, alterados JSON do jogo nem modificados Source, Content, Config ou outros branches. Nenhum merge deve ser feito automaticamente por este pacote.

## Validação

`balance_model.py --self-test`: reprodução por semente, variação entre sementes, conciliação de caixa, estoque não negativo, orçamento de ações, capacidade de quartos, fórmula de personalização, comportamento atual da penalidade e overlay isolado com rejeição de valor obsoleto. A execução das trajetórias também verifica caixa/estoque/orçamento/capacidade a cada dia.

As descrições curtas de pt-BR, inglês e dos 12 idiomas foram verificadas com limite de 300 caracteres. As estatísticas e tabelas foram geradas dos arquivos de resultado. A validação adicional em `tools/ue58/balance/validate.py` confere configurações, CSV, resumo e traduções. A lista de arquivos do PR deve conter somente os caminhos autorizados pelo pedido.


## Pacote 2

### Base, incorporação e escopo

O **PR #7 foi incorporado sem conflitos**, conforme autorizado. Criei `gpt/pacote-2` a partir da base e, quando chegaram três commits durante a tarefa, avancei o branch para **fa49a68b5d8d33fdedde48fd096097f0aac0f267** de `codex/ue58-migration`, antes de publicar qualquer alteração deste pacote. A análise final, os dados e os hashes correspondem a essa referência. Os novos arquivos e correções chegaram da outra IA; não são mudanças de Source/Data deste PR.

Estão presentes e contemplados: montagem dos eventos do Grand Hotel; fama negativa com piso no nível já alcançado; neon até pelo menos 21h; aluguel fechado na tempestade e chegadas ×1,4 na maré alta; pagamento de reserva do restaurante cuja noite foi dormida; crítico gastronômico, estrelas e peixe fresco. O novo check-in também reinicia os marcadores VIP. As observações preliminares de ausência foram substituídas após a atualização da base.

`balance/source_audit.py` e `source_features.json` registram presença e hashes das fontes inspecionadas. O modelo rejeita Source divergente desse registro até revisão das fórmulas; essa inspeção textual não equivale a compilar o jogo.

### Traduções

Executados `i18n_extract.py`, `i18n_pt_pt.py` e o extrator novamente após cada rodada. Foram preenchidas duas levas, de **69 e 100 entradas por idioma**; houve remoção de textos obsoletos pelo extrator. Isso inclui fliperamas, placares, campeonato de sinuca, pedidos VIP, montagem de casamento/aniversário/congresso, crítico, peixe e novos jantares. Identificadores técnicos e comandos de QA extraídos heuristicamente foram preservados; nomes de pessoas e pratos brasileiros também. pt-PT foi regenerado pelo script solicitado, preservando Antônio.

| Idioma | LOCTEXT | Strings | Faltando | Marcadores divergentes |
|---|---|---|---|---|
| en | 113 | 3907 | 0 | 0 |
| es | 113 | 3907 | 0 | 0 |
| de | 113 | 3907 | 0 | 0 |
| fr | 113 | 3907 | 0 | 0 |
| zh-Hans | 113 | 3907 | 0 | 0 |
| ja | 113 | 3907 | 0 | 0 |
| ru | 113 | 3907 | 0 | 0 |
| ko | 113 | 3907 | 0 | 0 |
| it | 113 | 3907 | 0 | 0 |
| pl | 113 | 3907 | 0 | 0 |
| nl | 113 | 3907 | 0 | 0 |
| pt-PT | 113 | 3907 | 0 | 0 |

Marcadores `{0}`, `{1}` etc., `<br>` e `R$` foram verificados no corpus inteiro; os espaços das entradas novas foram preservados. Os textos anteriormente preenchidos dos 11 idiomas foram conservados. Os 12 `todo_*.json`, que já estavam versionados na base, foram apagados após a conferência final. Registro em `balance/pacote2/traducoes_verificacao.json`. Não houve revisão nativa ou teste de layout no editor.

### Verificador de dados

Novo `tools/ue58/qa/data_lint.py`, apenas biblioteca padrão. Lê recursivamente todos os JSON; apresenta `arquivo → JSON Pointer → problema`, saída **1** em falha, com `--json` e `--self-test`. Verifica sintaxe/chaves duplicadas, ids repetidos em listas, referências cruzadas de expansões/capítulos/pratos/insumos/equipe/receitas/slots, ciclos de pré-requisitos, valores monetários, chances/frações, intervalos, horários, modelos e dupla codificação. Não confunde renda horária de negócio com relógio nem coordenadas negativas com preço.

As regras citam os consumidores reais em `RULE_SOURCES`, incluindo `MareHotelEvents.cpp` e `MareRestaurant.cpp`. Modelos são resolvidos por custom_assets, catálogos de importação, aliases, Dish_<id> e caminhos montados pelos carregadores. Slugs do lobby e `fab:N` foram conferidos nos scripts de importação, sem executá-los na Unreal.

```sh
python tools/ue58/qa/data_lint.py --self-test
python tools/ue58/qa/data_lint.py
# Reprodução da conferência na nuvem, sem baixar .uasset:
python tools/ue58/qa/data_lint.py --asset-index tools/ue58/balance/package_index.json --json
```

O índice registra **281 packages** relevantes comprovados na árvore Git, revisão e hashes dos 46 JSON; rejeita snapshot obsoleto. Referências /Game precisam de sintaxe válida e arquivo, índice ou catálogo de importação. Presença no catálogo não comprova importação no PC nem carregamento, tipo, materiais ou conteúdo do binário.

**Resultado final: PASS, saída 0; 46 JSON, 796 etapas de resolução de modelos, 0 erros.** Nenhum achado de dados na execução final; resultado integral em `balance/data_lint_results.json`. Nenhum JSON de Data foi corrigido.

O self-test usa fixtures temporárias que reprovam JSON inválido/chaves duplicadas, id repetido, referência inexistente, dinheiro negativo, chance >1, faixa invertida, horário >24, modelo/path ausente e mojibake. Aceita português válido, coordenadas negativas, renda horária 32 e modelo registrado. Não foi ligado ao portão de qualidade, conforme pedido.

### Balanceamento e meta de 6–10 horas

Recalculados os três perfis com **30 sementes por cenário** (180 trajetórias), mais dois extremos de capacidade com dez sementes por perfil/cenário (120). Total **300 trajetórias**; resultados, configurações e hashes em `balance/pacote2/`. O histórico das execuções do pacote 1 foi preservado nos diretórios antigos.

Montagem usa Score = peças obrigatórias montadas / total. Com pelo menos metade: cachê arredondado de fee × Score × (1 + extra_bonus × extras), fama proporcional; abaixo da metade, sinal de 20% e −4 XP, limitado pelo piso do nível. Ofertas às 9h dos dias pares, aceitas para amanhã. Não foi inventado custo de peças. A hipótese de montagem é 6 s por peça, com atenção de 2/8/10 peças por hora para casual/médio/dedicado, usando o orçamento único de ações; E não tem chance de falhar. Aceitar oferta é uma decisão probabilística de engajamento. A duração da festa visual não gera receita adicional.

Crítico usa intervalos de 3–5 dias, chance horária 0,4, nota por espera e frescor, até três estrelas e preço +12% por estrela. Espera manual é uma hipótese por perfil; navegação real precisa ser medida. Peixe em estoque dá +25% e fama no prato manual de mesa; sem estoque cobra R$ 22. O modelo mantém a automação/room service sem essa chamada de consumo, como o código atual. Reserva vencida do restaurante pode ser liquidada na próxima chamada horária.

Dia efetivamente jogável: **16 min**, de 8h a 24h, com 1 minuto do jogo/segundo real. A coluna de 24 min continua identificada como conversão alternativa; não aumenta a renda. Tela do EA, campanha e todas as compras são marcos distintos.

| Cenário | Perfil | Hotel: dia / horas medianas | Tela do EA: dia / horas medianas | Hotel e tela entre 6–10 h |
|---|---|---|---|---|
| atual | casual | 30 / 8.0 h | 31 / 8.3 h | 30/30 e 30/30 |
| atual | medio | 25 / 6.7 h | 26 / 6.9 h | 30/30 e 30/30 |
| atual | dedicado | 22 / 5.9 h | 23 / 6.1 h | 9/30 e 22/30 |
| proposto | casual | 27 / 7.2 h | 28 / 7.5 h | 30/30 e 30/30 |
| proposto | medio | 24 / 6.4 h | 25 / 6.7 h | 29/30 e 30/30 |
| proposto | dedicado | 20 / 5.3 h | 21 / 5.6 h | 2/30 e 9/30 |

O perfil médio atinge a meta nas **30 sementes**, tanto atual como proposto. O dedicado pode chegar antes de 6 h. Trata-se de modelo agregado, não de duração comprovada em playtest. A política prioriza expansão e fontes de renda; obter todas as estrelas do restaurante não é condição de encerramento, e a equipe pode atender os críticos sem ganhar estrelas.

A lista **MUDANÇAS PROPOSTAS** foi refeita: `definitions.json /expansions/grand_hotel/cost` 30.000 → 28.000; `hotel_events.json /extra_bonus` 0,10 → 0,15; `customization.json /price_mult/4` 30 → 24. Valores atuais conferidos e mudanças simuladas juntas só em memória. A redução antiga do casamento foi retirada porque a base já trocou os contratos por jantares moderados. A campanha continua com 4.000 vendas, sem redução artificial para cumprir a nova meta.

### Bugs e incoerências novos — somente leitura

Linhas da referência fa49a68. São recomendações, não correções deste PR.

| Arquivo e linha | Problema observado | Como corrigir / verificar |
|---|---|---|
| `Source/MareAlta/MareRestaurant.cpp:184`, `MareSimulation.cpp:372`; `Content/Data/definitions.json:1031` | `TakeKitchenFish` considera todo `stock.peixe` fresco do píer, inclusive o comprado no mercadinho por R$ 7. Assim, comprar dá o mesmo bônus de pesca e evita o fornecedor de R$ 22. A mensagem de origem pode ser falsa. | Se a intenção for premiar pesca, separar a origem/estoque pescado e consumir esse saldo para o bônus. Se a intenção for qualquer peixe em estoque, ajustar a comunicação. Testar compra versus pesca com o mesmo prato. |
| `Source/MareAlta/MareRestaurant.cpp:163–177`, `:180–187` | O atendimento automático escolhe/vende pratos com peixe sem chamar `TakeKitchenFish`; o room service também não chama essa função. Consumo/custo de peixe só acontece quando o jogador toma pedido de mesa. Isso pode fazer a automação evitar um custo cobrado no atendimento manual. | Centralizar o consumo por pedido com marcador de cobrança única; decidir explicitamente se room service tem custo e bônus de frescor. Testar manual, garçom, equipe e quarto com estoque 0/1, evitando cobrança dupla. |
| `Source/MareAlta/MareRestaurant.cpp:148–153` | A reserva ainda anuncia 20h mas usa `Started=Hour-1`; o cachê entra no cruzamento de 21h. A correção de noite dormida resolve a perda de receita, não esse descompasso de horário. | Alinhar gatilho e mensagem; testar 19h59/20h/21h e primeiro avanço após dormir. |
| `Source/MareAlta/MareSimulationTests.cpp:1212–1213`, `:1328–1329` | O teste antigo lê `State.fame_xp` em vez de `State.prog.fame_xp`, não usa o valor e só confere mensagem. O teste novo aceita `Fame() <= F0`, o que passa sem desconto. Agora existe piso de nível intencional, mas a perda acima do piso deveria ser comprovada. | Usar campo correto; iniciar XP acima do limiar; exigir delta exato e caso separado com truncamento no piso. Não exigir queda de nível, pois a regra nova a impede. |

### Achados do pacote 1 revistos

- Autosave: corrigido na base (`MareGame.cpp:2861`), instruções fora do comentário.
- Fama negativa: corrigida na base (`MareSimulation.cpp:422`), com piso do nível atual por design.
- VIP por estadia: corrigido na base (`MareStays.cpp:102`).
- Neon e aluguel: corrigidos na base (`KioskCloseHour`, `IsBusinessOpen`, `RentalHour`); maré aumenta procura, não preço.
- Noite dormida do contrato: corrigida na base; permanece a diferença de uma hora descrita acima.
- Condição da tela do EA versus campanha, painel de personalização dos negócios e possível intenção de fluxos duplos continuam questões já registradas, não bugs novos deste pacote.

### Verificação e limites

- `balance_model.py --self-test`: PASS, inclusive perda de XP com piso, evento com 6/7/14 peças, extras, reserva vencida ao dormir e estrela com peixe fresco.
- `data_lint.py --self-test`: PASS; 46 JSON reais com índice: PASS/0.
- `balance/validate.py`: PASS para 18 séries diárias e 300 trajetórias, fontes/despesas/caixa, fama, capacidade, configurações, hashes e traduções.
- Extrator final: 113/113 LOCTEXT e 3.907/3.907 strings nos 12 idiomas; `todo_*.json` removidos.
- Sem editor, PC, compilação C++, QA gate, playtest visual, binários, screenshots ou publicação. Sem alterações em Source, Content/Data, Config ou .uasset. O novo PR fica aberto para revisão; somente o #7 recebeu merge autorizado.


## Pacote 3

Base: **9e5b4adcadba60ec0c46ffa2e4767bcb6805db0a**, branch **gpt/pacote-3**.

### Entregas

- **18 traduções novas nos 12 idiomas**, mantendo as antigas. pt-PT pelo adaptador do projeto, aproveitando somente os valores faltantes. Extrator final: **113/113 LOCTEXT e strings 3922/3922 em todos os idiomas**, zero faltando. Conferidos {N}, <br>, R$, nomes, espaços e pontuação final das entradas novas, inclusive “ chega no jogo completo.”. Apagados os todo_*.json gerados.
- Páginas pt-BR/en da demo de **Coconut Coast: Resort Simulator**, com descrições curtas de **266/267 caracteres**, descrições longas, conteúdo da demo versus jogo completo e lista de desejos. Maré Alta é o resort. Cerca de 2 h é a meta informada de progressão, sem medição nesta tarefa; pode continuar depois do resumo. Sem promessa de data.
- Nova etapa **data** no qa_gate.py, antes da conexão MCP. Falha grava report.json com pass=false, lista arquivo/campo/problema e encerra com **1**, sem chamar a Unreal. Resposta inválida também reprova. A inicialização do cliente foi adiada; funções das outras etapas ficaram idênticas na comparação da AST.

### Conferência

Na raiz do checkout:

```sh
python tools/ue58/i18n_extract.py
python tools/ue58/qa/data_lint.py --self-test
python tools/ue58/qa/data_lint.py
python -m py_compile tools/ue58/qa/qa_gate.py
```

O extrator deve imprimir 3922/3922 nesta referência; apague novamente os todo_*.json vazios que ele gerar. Testes Python: **PASS**. Os **46 JSON** passaram com **zero erros e 796 etapas de resolução de modelos**, usando índice temporário de metadados Git e hashes atuais, sem baixar assets; o índice histórico de balanceamento não foi alterado.

Fixtures temporárias, com rede bloqueada, comprovaram importação sem conexão, aprovação de dados válidos e reprovação de preço negativo, JSON inválido e resposta inválida. O main saiu com 1 antes de criar o cliente ou chamar PIE. **Portão completo não executado**, pois exige Unreal; no editor, rodar **python tools/ue58/qa/qa_gate.py, sem argumentos**.

### Pendência de dados — somente relatada

**Content/Data/events.json → /end_of_content/review_url está vazio.** Em MareGame.cpp:1749, a chamada e o botão de lista de desejos só aparecem com URL preenchida. Antes de distribuir, informar a URL real da página do jogo completo na Steam e testar o botão. Não foi inventada URL/app id; isso é pendência funcional de publicação, não erro estrutural do linter.

Sem alterações em C++, .uasset, definitions.json, customization.json, JSON de economia, balance_model.py ou resultados de balanceamento. Sem compilação C++/Unreal, capturas ou publicação na Steam.


## Pacote 4

Base efceab9; branch gpt/pacote-4. Desenho em DIVIDA_DA_AVO.md, contrato novo debt.json, 29 textos completos em 12 idiomas (113 LOCTEXT + 3.951 strings por idioma), 36 conquistas pt-BR/en e dez presenças. Nada disso foi implementado em C++ ou publicado na Steam.

### Ordem para o Claude

1. Ler a pergunta de moeda no topo do desenho; usar R$ 1.000.000 até decisão. Implementar leitura de debt.json e migração única de prog.debt, preservando caixa/campos antigos e congelando o principal em centavos.
2. Implementar pagamento livre transacional no cartão de Finanças: confirmar, debitar uma vez, persistir, recusar valores inválidos sem cobrança e respeitar teto demo de R$ 250.000. Não implementar juros, parcelas obrigatórias ou game over.
3. Integrar carta na chegada/primeiro celular, lembrete semanal sem punição e cartões únicos 25/50/75%. Trocar apenas os três story propostos de campanha, mantendo metas/recompensas. Textos estão em debt.json e traduzidos.
4. Integrar final ao quitar no jogo completo, créditos/continuidade; preservar o agradecimento independente da demo e revisar a antiga condição de fim do EA. Não exigir comprar todo o catálogo nem quitar para fazer a festa.
5. Implementar a fila idempotente de conquistas e presença com as condições de conquistas.json/md. Cinco condições usam o contrato novo da dívida; as outras 31 usam campos existentes. App IDs, ícones e publicação ainda precisam de configuração/testes reais.
6. Testar migração, limites/centavos, save falhando, pagamento duplo, salto de marcos, lembretes/load, demo/legado e final. Só depois avaliar os dois preços de nível 5 propostos; não aplicar automaticamente.

### Resultado e limites

540 trajetórias registradas (30 sementes por perfil/cenário): médio quita em **20,3 h**, campanha **20,5 h**; compras com dívida vão a **43,7 h** na economia atual ou **40,3 h** com as propostas. Baseline sem dívida reproduz **20,3/37,1 h**. Demo média **2,3 h**, sem quitação. São hipóteses de pagamentos voluntários, não duração garantida nem débito automático. Dados, tabelas, hashes e comandos estão no balanceamento/desenho.

Guardas de source_features da base tinham hashes divergentes para dois C++ publicados; renovado somente o registro de leitura e corrigida a revisão antiga do modelo. Incoerência encontrada: a missão fregueses tem qty/texto de 7.000, mas título “Quatro mil fregueses”; só relatada. O índice histórico de assets do pacote 2 também não é reutilizável sem atualizar seus hashes de Data; a checagem desta tarefa usa metadados temporários atuais, sem editar esse histórico.

47 JSON de Data passaram no linter (796 resoluções de modelos, zero erros), com índice temporário de metadados Git. Validação Python: testes da transação/modelo, conciliação de caixa/dívida, censura, hashes, demo, traduções e condições/ids das conquistas. Sem Unreal, C++, assets, aplicação dos preços ou edição dos JSON econômicos existentes. O novo debt.json ainda requer o consumidor; as mudanças de campanha estão somente propostas.


## Pacote 5

Base atualizada em 07/11/2026: **2bea4d2d016eb5920a4b317973fb711a1ea67db9**, incluindo pacote 4 e decisão definitiva de moeda **R$ 1.000.000**. Branch **gpt/pacote-5**; destino do PR **codex/ue58-migration**. A branch remota do pacote estava um commit atrás e foi avançada com fast-forward da base antes das alterações.

### Entregas

- [Revisão do português](REVISAO_TEXTOS.md): leitura das **4.064 entradas** (113 LOCTEXT + 3.951 strings), com **76 linhas de achados/decisões** e tabela individual dos **29 textos da dívida**. Aponta concordância, orientações antigas de caixa, “duche”, acentos, concatenações, nomenclatura e glossário. Não renomeia personagens diferentes só por terem nomes parecidos. Chaves pt-BR e traduções ficaram intactas; Claude aplica em migração coordenada.
- **tools/ue58/i18n_length_audit.py**, somente biblioteca padrão e leitura dos catálogos. São **48.768 comparações**; o filtro exige >30% **e** >25 caracteres extras. **63 ocorrências**: de 19, en 2, fr 25, it 11, nl 3, pl 2, ru 1; es/ja/ko/pt-PT/zh-Hans 0. Cada idioma lista até 50 casos reais, sem preencher artificialmente. Zero traduções vazias ou marcadores divergentes na referência.
- [Relatório de tamanho](REVISAO_TRADUCOES_TAMANHO.md), **I18N_TAMANHO.json** com métricas/hashes e **I18N_SUGESTOES_CURTAS.json** com 63 propostas menores nos respectivos idiomas, além de duas propostas de largura estimada em coreano. O gerador confere marcadores e espaços de fragmentos. Não equivale a medição da fonte ou teste de recorte na Unreal.
- Kits pt-BR/en em **docs/steam/presskit_pt-BR.md** e **presskit_en.md**: ficha, descrições, história, recursos, demo/completo, FAQ e contatos a preencher. Gancho: a avó viva e a carta do milhão. A dívida continua sendo trabalho de integração, não um recurso declarado aprovado.
- **docs/steam/trailer_roteiro.md**: 12 planos que totalizam **60 s**, texto pt-BR/en, música/ritmo e dez capturas com local, horário e critério de aceite. São roteiros; nenhuma imagem/vídeo foi fabricada ou apresentada como gameplay capturado.
- **loja_pt-BR.md**, **loja_en.md** e as **12 versões de loja_traducoes.md** atualizadas com a dívida como objetivo do completo; nome comercial Coconut Coast: Resort Simulator, Maré Alta como resort, sem data. As 14 descrições curtas têm 122–252 caracteres, abaixo de 300.
- **docs/steam/next_fest_plano.md**: cronograma relativo T−8 a T+2, posts/devlogs, metas internas de desejos, 24 objetivos de demo conforme conquistas.json, revisão da build, QA, idiomas, tela final e destino real da lista de desejos. Regras consultadas na documentação Steamworks; não foi feita inscrição ou publicação.

### O que precisa do Claude

1. Aplicar as sugestões de português **nos consumidores e nos 12 catálogos juntos**, mantendo as chaves antigas durante a migração; não executar uma troca isolada em source.json. Validar os formatos `{0}{1}` para não duplicar espaços ou produzir “60%a renda”. Preservar ids internos como `Album`/`Radio`.
2. Integrar o contrato debt.json: carta, Finanças, transação atômica, marcos, teto cumulativo de R$ 250.000 na demo, final apenas no completo, avó viva, sem juros/parcela obrigatória. Não mudar a moeda já decidida nem aplicar os preços propostos automaticamente.
3. Medir as sugestões de tradução **na UI real**, com fonte, resolução, escala e valores expandidos; atenção a diálogos longos e Hangul. Pedir revisão nativa dos textos comerciais/traduções antes da publicação.
4. Concluir/validar banhistas (nadar, boiar, conversar, saltar) e uso do tobogã do Grand Hotel. Não usar esses comportamentos em trailer/galeria da demo antes de aprovados; Grand Hotel permanece completo.
5. Executar build/instalação Steam e QA de percurso, save, áudio, portas, dormir, balcão, produtos apoiados e mar. Validar a tela final, o link do jogo completo e as condições dos 24 objetivos demo; nenhuma revisão editorial substitui esse teste.

### O que precisa do Sergio

1. Escolher a edição do Next Fest e confirmar elegibilidade/inscrição no painel. **Não lançar o jogo completo em EA antes/durante o festival escolhido.** Demo gratuita e jogo completo têm App IDs distintos a configurar/verificar.
2. Fornecer a URL pública real do jogo completo e autorizar seu preenchimento em **Content/Data/events.json → /end_of_content/review_url**, ainda vazio na base. O botão hoje não aparece sem a URL; este pacote não a inventou nem alterou o arquivo.
3. Preencher desenvolvedor/publicador, contato de imprensa, site/redes, App IDs, links de cápsulas e materiais. Aprovar música/licenças, copy, trailer e capturas reais antes de divulgar.
4. Decidir a publicação de conquistas na demo, considerando a recomendação Steam de desativá-las. O contrato mantém 24 objetivos demo; nenhum foi removido. A escolha não autoriza presumir Cloud ou transferência de saves.
5. Cronometrar playtests: ~2 h de demo, ~20 h de história e ~37–40 h para 100% são metas. O modelo do pacote 4 tem 43,7 h de compras na economia atual com dívida ou 40,3 h com propostas; não prometer 100% garantido em 40 h com base só na simulação.

### Verificação e limites

Comandos desta entrega:

```sh
python tools/ue58/i18n_length_audit.py --self-test
python tools/ue58/i18n_length_audit.py --output docs/ue58/I18N_TAMANHO.json --suggestions docs/ue58/I18N_SUGESTOES_CURTAS.json --report docs/ue58/REVISAO_TRADUCOES_TAMANHO.md
python -m py_compile tools/ue58/i18n_length_audit.py
```

Self-test aprovado: fronteiras estritas de 30%/25 caracteres, NFC, marcação, largura asiática, placeholders repetidos e printf, fixture multilíngue com entrada faltante/marcador perdido e prova de que os inputs não são escritos. Auditoria real aprovada: 12 idiomas completos, 63 sugestões menores com marcadores preservados. Conferidos também os 29 textos da dívida presentes no catálogo, os 24 IDs de conquista demo e a soma de 60 s do roteiro.

Sem alterações em **unreal/MareAlta/Source**, **.uasset**, **debt.json**, catálogos de localização ou JSON de economia (definitions, customization, business_games, bar, pool, pool_swim, tours, restaurant, hotel_*, sunbathers). O trabalho foi feito em checkout separado para não incluir a piscina/MetaHumans em andamento no checkout principal. Sem compilação C++, Unreal Editor, teste de executável, nova medição de FPS, publicação Steam, inscrição Next Fest ou envio de imprensa neste pacote. O PR fica aberto para revisão; nenhum merge foi solicitado.
