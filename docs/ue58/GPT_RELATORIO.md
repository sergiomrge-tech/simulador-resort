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


# Pacote 6 — dados, localização e contratos para integração

07/11/2026. Base conferida: `899e77a66ce718e19f48d9ae3f06049fdc77cd64`. Branch `gpt/pacote-6`, destino `codex/ue58-migration`.
**Nenhum arquivo de `unreal/MareAlta/Source`, nenhum `.uasset` e nenhum save do jogador foram alterados.**
Não se declara build, execução no editor, integração Steam ou implementação da dívida em C++.

## Aplicado

- 19 correções da revisão nos cinco JSON de dados: definições, tutorial, personalização, passeios e minijogos. O item 7 foi adaptado ao código: sujeira impede usar a mesa, sem afirmar penalidade direta de avaliação.
- Cada frase nova tem tradução nova nos 12 idiomas. Chaves antigas só saem quando deixam de ter consumidor; “Passe da cozinha” continua no Source até a integração do Claude.
- `GLOSSARIO.json`: 32 conceitos/nomes fixos, nos 12 idiomas, com flexões e contextos explícitos; `glossary_check.py` reprova divergências e entra no `data_lint.py`. Fama continua distinta de avaliação/estrelas. Nomes próprios são preservados, inclusive Bar do Coqueiro, Padre Robson e Seu Severino.
- 20 vetores fixos da dívida / 45 ações, modelo Python persistente de referência, teste de paridade dos pagamentos com o modelo econômico e pseudocódigo em `DIVIDA_DA_AVO.md`.
- `achievements.json`: 36 IDs preservados, nome/descrição pt-BR, flags editoriais, condições genéricas, proveniência e 10 textos de Rich Presence. São contratos de dados para o consumidor futuro.
- 15 falas novas: cinco listas sorteadas de `comic_events.json` passam de 3 para 6 opções cada (gaivota, turista perdido, influenciador, guarda-sol e bandeja). `asks_en` acompanha as entradas inglesas; os 12 catálogos têm todas as variações.
- Extrator limita `achievements.json` a nome/descrição/presença; condições, caminhos, comparações e IDs não viram texto. Os sete identificadores internos chat/climb/edge/float/fly/jump/ride também não entram como traduções.
- Índice de packages atualizado com nomes comprovados da árvore Git da base, sem ler/escrever binários. Hashes vinculam o índice aos dados deste pacote; checkout textual usa esse índice automaticamente, checkout com assets usa os arquivos presentes.

Catálogo final: **113/113 LOCTEXT + 4042/4042 strings em cada idioma**. Diferença de chaves: 112 novas e 19 removidas; nenhuma tradução vazia. Não há `todo_*.json` no commit.

Mudanças de valor em chaves já existentes, decorrentes do glossário, nomes, separadores e correções de métricas herdadas: en: 34, es: 53, de: 33, fr: 64, zh-Hans: 136, ja: 138, ru: 55, ko: 82, it: 25, pl: 35, nl: 31, pt-PT: 0. São contagens de entradas alteradas, não número de falas novas.

## Correções nos dados e prova da mecânica

| Item | Dados | Texto aplicado / conferência |
|---|---|---|
| 5 | definitions.json | O pagamento é recebido automaticamente a cada produto entregue. — MareSimulation.cpp:237–248 Deliver/Book: pagamento por produto. |
| 6 | definitions.json | Cuida de todo o quiosque: anota pedidos, entrega produtos prontos e recolhe a louça. O cliente paga ao receber. — MareKioskWorld.cpp:170–195: atendente único, entrega e louça; Deliver cobra. |
| 7 | tutorial.json | Mesas sujas ficam indisponíveis para novos clientes. Limpe com E ou deixe a tarefa com o atendente. — MareKioskWorld.cpp:38 e :109–124: mesa suja indisponível; :78 calcula nota por espera, sem penalidade direta de sujeira. |
| 10 | tutorial.json | A placa abre e fecha o quiosque. O atendimento segue o horário do negócio; dormir encerra o dia e o deixa fechado. — MareSimulation.cpp:124–144 SetOpen/IsOpen/KioskCloseHour; :451–453 Sleep fecha o negócio. |
| 22 | tutorial.json | Batata, peixe e petiscos ficam aqui, prontos para servir. Quando acabar, reponha aqui ou pelo celular. — MareSimulation.cpp:179–195 Restock/RestockCost e MareGame.cpp painel de estação Fridge/Cupboard. |
| 23 | tutorial.json | Anote o pedido, pegue o prato pronto no balcão de retirada da cozinha e sirva. Rapidez rende gorjeta. — MareRestaurant.cpp:75–104: pedidos, retirada pronta e entrega; MareRestaurantWorld.cpp:31 é a estação existente. |
| 24 | tutorial.json | Balcão de retirada da cozinha — Só rótulo do tutorial; alvo físico nativo fica na tabela do Claude. |
| 30 | tutorial.json | Antes de subir, dê água e protetor solar a cada pessoa. Sem isso, o grupo se cansa e reclama. — MareTrailWorld.cpp:82–116: água/protetor por participante antes da subida. |
| 31 | tours.json | Entregue água e protetor solar a cada pessoa (E) e siga para o primeiro mirante. — Mesmo fluxo de MareTrailWorld, sem mudar E ou consequências. |
| 37 | definitions.json | Um bar de praia com bartender. Banhistas se sentam e pedem drinks. — MareBar.cpp:82–114: gera pedidos dos clientes; não altera autonomia. |
| 39 | customization.json | Ducha de cabeça larga e itens de higiene de cortesia. — Descrição do mesmo upgrade de ducha, sem novo efeito. |
| 40 | customization.json | Ducha com itens de higiene de cortesia — Nome do mesmo upgrade, sem alterar id/preço. |
| 42 | definitions.json | A Barraca da Dona Rita compra 4 cocos do seu estoque. — definitions.quests.cocos_rita; MareSimulation.cpp:369–380 entrega insumos à missão, qty preservado. |
| 54 | tutorial.json | Espere o peixe morder a isca e aperte na hora certa. Os peixes vão para o estoque; Seu Severino precisa de alguns. — MareLeisure.cpp:22–31 CatchFish acrescenta peixe ao estoque; dicas do minijogo SMareFishingGame. |
| 58 | business_games.json | Casquinhas de até 4 bolas. O pedido aparece por menos tempo e a faixa de tamanho correto fica menor. — business_games.sorveteria.levels[0].set e MareIceCream.cpp:46–54, :89: até 4 bolas e faixa right. |
| 59 | business_games.json | Pedidos de 2 a 4 bolas, visíveis por 1,8 s. A bola cresce mais rápido e a faixa correta é bem estreita. — business_games.sorveteria.levels[1].set: show_seconds 1.8, scoops 2–4; leitura pelo minijogo. |
| 65 | tutorial.json | Cada negócio tem sua tarefa. Quanto melhor o atendimento, mais o cliente paga. Sem você, o funcionário atende com 60% da receita. — MareBizCommon.cpp:82 BizClerkShare e business_games.clerk_share=.6; sem alterar a divisão. |
| 66 | tutorial.json | Negocie a diária como na pousada. Após 2 horas sem atendimento, a equipe aceita a oferta do hóspede. — MareStays.cpp:186–192: após 120 minutos chama AcceptOffer quando há quarto limpo; :121–123 usa oferta. |
| 69 | customization.json | Piscina (entrada por dia) — customization.operations.hourly.pool: nome da mesma receita de entrada, sem mudar cobrança. |

Não refeitos os itens já aplicados pelo Claude: 1, 2, 3, 14–17, 29, 33, 34, 38, 41, 43–46. Os dados deles foram preservados.
O glossário encontrou traduções herdadas do item 45 sem a palavra de avaliação: o texto localizado foi corrigido, sem
reescrever o dado nem a condição. Corrigiu também nomes trocados por “Gregory” em traduções de Seu Severino.

## Para o Claude — textos do C++

A tabela abaixo não aplica alterações ao Source. Versão estruturada para copiar: [PACOTE6_TEXTOS_CPP.json](PACOTE6_TEXTOS_CPP.json).
Os textos atuais de LOCTEXT continuam no source.json; ao aplicar, manter as chaves MareMenu,OptLanguageHint / OptKeysHint /
OptDefaultsLoaded / OptKeepVideo / QuitDesktop. Para strings, migrar a chave portuguesa nos 12 mapas e rodar o extrator.
O item 9 é o fragmento sem separador do item 8 e aponta ao mesmo literal; não inserir dois sufixos no resumo.

| Item | Arquivo:linha (base) | Texto atual | Texto novo |
|---|---|---|---|
| 8 | unreal/MareAlta/Source/MareAlta/MareSimulation.cpp:842 |  · sem guia contratado os passeios não saem |  · sem guia contratado, você precisa guiar os passeios |
| 9 | unreal/MareAlta/Source/MareAlta/MareSimulation.cpp:842 | sem guia contratado os passeios não saem | sem guia contratado, você precisa guiar os passeios |
| 24 | unreal/MareAlta/Source/MareAlta/MareRestaurantWorld.cpp:31 | Passe da cozinha · pegar pratos prontos | Balcão de retirada da cozinha · pegar pratos prontos |
| 63 | unreal/MareAlta/Source/MareAlta/MareSimulation.cpp:120 | Empresa criada. Abra o quiosque para receber clientes. | Empresa criada. Abra o quiosque pela placa do balcão para receber clientes. |
| 67 | unreal/MareAlta/Source/MareAlta/MareGame.cpp:586 | Quem você não atender em 2 horas, a equipe do hotel recebe pela oferta do hóspede. | Após 2 horas sem atendimento, a equipe do hotel aceita a oferta do hóspede. |
| 72 | unreal/MareAlta/Source/MareAlta/MareGame.cpp:2271 | A tradução para o inglês ainda está sendo feita: alguns textos podem continuar em português. | Se encontrar algum texto sem tradução, informe o idioma e a tela em que ele aparece. |
| 73 | unreal/MareAlta/Source/MareAlta/MareGame.cpp:2244 | Clique numa ação e aperte a nova tecla (Esc cancela). Se a tecla já estiver em uso, as duas ações trocam. | Clique em uma ação e pressione a nova tecla (Esc cancela). Se a tecla já estiver em uso, as duas ações trocam de tecla. |
| 74 | unreal/MareAlta/Source/MareAlta/MareGame.cpp:2332 | Valores padrão carregados (o áudio já mudou). Clique em Aplicar para usar o resto. | Padrões carregados; o áudio já mudou. Clique em Aplicar para confirmar as demais configurações. |
| 75 | unreal/MareAlta/Source/MareAlta/MareGame.cpp:2292 | Manter este modo de tela? Volta ao anterior em {0} s. | Manter este modo de tela? O anterior volta em {0} s. |
| 76 | unreal/MareAlta/Source/MareAlta/MareGame.cpp:2487 | Sair para o desktop | Sair para a área de trabalho |

### As 12 traduções prontas para os textos nativos

| Item | Idioma | Tradução nova |
|---|---|---|
| 8 | en |  · without a hired guide, you need to lead the tours |
| 8 | es |  · sin un guía contratado, tienes que guiar los paseos |
| 8 | de |  · ohne angestellten Guide musst du die Ausflüge selbst führen |
| 8 | fr |  · sans guide embauché, vous devez guider les excursions |
| 8 | zh-Hans |  · 没有雇用导游时，需要你亲自带团 |
| 8 | ja |  · ガイドを雇っていなければ、自分でツアーを案内します |
| 8 | ru |  · без нанятого гида экскурсии нужно проводить самому |
| 8 | ko |  · 고용한 가이드가 없으면 직접 투어를 안내해야 합니다 |
| 8 | it |  · senza una guida assunta, devi guidare tu le escursioni |
| 8 | pl |  · bez zatrudnionego przewodnika musisz samodzielnie prowadzić wycieczki |
| 8 | nl |  · zonder ingehuurde gids moet je zelf de tochten leiden |
| 8 | pt-PT |  · sem guia contratado, tem de guiar os passeios |
| 9 | en | without a hired guide, you need to lead the tours |
| 9 | es | sin un guía contratado, tienes que guiar los paseos |
| 9 | de | ohne angestellten Guide musst du die Ausflüge selbst führen |
| 9 | fr | sans guide embauché, vous devez guider les excursions |
| 9 | zh-Hans | 没有雇用导游时，需要你亲自带团 |
| 9 | ja | ガイドを雇っていなければ、自分でツアーを案内します |
| 9 | ru | без нанятого гида экскурсии нужно проводить самому |
| 9 | ko | 고용한 가이드가 없으면 직접 투어를 안내해야 합니다 |
| 9 | it | senza una guida assunta, devi guidare tu le escursioni |
| 9 | pl | bez zatrudnionego przewodnika musisz samodzielnie prowadzić wycieczki |
| 9 | nl | zonder ingehuurde gids moet je zelf de tochten leiden |
| 9 | pt-PT | sem guia contratado, tem de guiar os passeios |
| 24 | en | Kitchen pickup counter · collect ready dishes |
| 24 | es | Mostrador de recogida de la cocina · recoger platos listos |
| 24 | de | Abholtresen der Küche · fertige Gerichte abholen |
| 24 | fr | Comptoir de retrait de la cuisine · récupérer les plats prêts |
| 24 | zh-Hans | 厨房取餐台 · 领取做好的菜品 |
| 24 | ja | 厨房の受け取りカウンター · 出来上がった料理を受け取る |
| 24 | ru | Стойка выдачи кухни · забрать готовые блюда |
| 24 | ko | 주방 픽업대 · 완성된 요리 가져가기 |
| 24 | it | Banco di ritiro della cucina · ritira i piatti pronti |
| 24 | pl | Lada odbioru w kuchni · odbierz gotowe dania |
| 24 | nl | Afhaalbalie van de keuken · klaargemaakte gerechten ophalen |
| 24 | pt-PT | Balcão de retirada da cozinha · levantar pratos prontos |
| 63 | en | Company created. Open the kiosk using the counter sign to welcome customers. |
| 63 | es | Empresa creada. Abre el quiosco con el cartel del mostrador para recibir clientes. |
| 63 | de | Firma gegründet. Öffne den Kiosk über das Schild am Tresen, um Gäste zu empfangen. |
| 63 | fr | Entreprise créée. Ouvrez le kiosque avec le panneau du comptoir pour accueillir les clients. |
| 63 | zh-Hans | 公司已创建。使用柜台上的招牌开启小摊，迎接顾客。 |
| 63 | ja | 会社を設立しました。カウンターの看板で売店を開けて、お客さんを迎えましょう。 |
| 63 | ru | Компания создана. Откройте киоск с помощью вывески на прилавке, чтобы принимать клиентов. |
| 63 | ko | 회사를 만들었습니다. 카운터 간판으로 가판대를 열어 손님을 받으세요. |
| 63 | it | Impresa creata. Apri il chiosco con l'insegna sul banco per accogliere i clienti. |
| 63 | pl | Firma utworzona. Otwórz kiosk szyldem na ladzie, aby przyjmować klientów. |
| 63 | nl | Bedrijf opgericht. Open de kiosk met het bord op de toonbank om klanten te ontvangen. |
| 63 | pt-PT | Empresa criada. Abra o quiosque pela placa do balcão para receber clientes. |
| 67 | en | After 2 hours without service, the hotel staff accepts the guest's offer. |
| 67 | es | Tras 2 horas sin atención, el equipo del hotel acepta la oferta del huésped. |
| 67 | de | Nach 2 Stunden ohne Bedienung nimmt das Hotelpersonal das Angebot des Gastes an. |
| 67 | fr | Après 2 heures sans accueil, l'équipe de l'hôtel accepte l'offre du client. |
| 67 | zh-Hans | 若2小时无人接待，酒店员工会接受客人的报价。 |
| 67 | ja | 2時間対応しないと、ホテルのスタッフが宿泊客の提示額を受け入れます。 |
| 67 | ru | Через 2 часа без обслуживания персонал отеля принимает предложение гостя. |
| 67 | ko | 2시간 동안 응대하지 않으면 호텔 직원이 투숙객의 제안을 수락합니다. |
| 67 | it | Dopo 2 ore senza assistenza, il personale dell'hotel accetta l'offerta dell'ospite. |
| 67 | pl | Po 2 godzinach bez obsługi personel hotelu przyjmuje ofertę gościa. |
| 67 | nl | Na 2 uur zonder bediening accepteert het hotelpersoneel het bod van de gast. |
| 67 | pt-PT | Após 2 horas sem atendimento, a equipe do hotel aceita a oferta do hóspede. |
| 72 | en | If you find any untranslated text, report the language and the screen where it appears. |
| 72 | es | Si encuentras texto sin traducir, indica el idioma y la pantalla donde aparece. |
| 72 | de | Falls du unübersetzten Text findest, melde die Sprache und den Bildschirm, auf dem er erscheint. |
| 72 | fr | Si vous trouvez du texte non traduit, indiquez la langue et l'écran où il apparaît. |
| 72 | zh-Hans | 如果发现未翻译的文字，请报告语言及其所在界面。 |
| 72 | ja | 未翻訳の文章を見つけた場合は、言語と表示された画面をお知らせください。 |
| 72 | ru | Если найдёте непереведённый текст, укажите язык и экран, на котором он появился. |
| 72 | ko | 번역되지 않은 문구를 발견하면 언어와 표시된 화면을 알려 주세요. |
| 72 | it | Se trovi testo non tradotto, segnala la lingua e la schermata in cui appare. |
| 72 | pl | Jeśli znajdziesz nieprzetłumaczony tekst, podaj język i ekran, na którym się pojawia. |
| 72 | nl | Meld de taal en het scherm als je onvertaalde tekst tegenkomt. |
| 72 | pt-PT | Se encontrar algum texto sem tradução, informe o idioma e a tela em que ele aparece. |
| 73 | en | Click an action and press the new key (Esc cancels). If the key is already in use, the two actions swap keys. |
| 73 | es | Haz clic en una acción y pulsa la nueva tecla (Esc cancela). Si ya está en uso, las dos acciones intercambian teclas. |
| 73 | de | Klicke auf eine Aktion und drücke die neue Taste (Esc bricht ab). Ist sie bereits belegt, tauschen die beiden Aktionen ihre Tasten. |
| 73 | fr | Cliquez sur une action et appuyez sur la nouvelle touche (Esc annule). Si elle est déjà utilisée, les deux actions échangent leurs touches. |
| 73 | zh-Hans | 点击一个操作并按下新按键（Esc取消）。如果按键已被使用，两个操作会交换按键。 |
| 73 | ja | 操作をクリックして新しいキーを押します（Escでキャンセル）。使用中のキーの場合は、2つの操作のキーが入れ替わります。 |
| 73 | ru | Нажмите на действие и задайте новую клавишу (Esc — отмена). Если она уже занята, два действия обменяются клавишами. |
| 73 | ko | 동작을 클릭하고 새 키를 누르세요(Esc로 취소). 이미 사용 중인 키라면 두 동작의 키가 서로 바뀝니다. |
| 73 | it | Fai clic su un'azione e premi il nuovo tasto (Esc annulla). Se è già in uso, le due azioni si scambiano i tasti. |
| 73 | pl | Kliknij działanie i naciśnij nowy klawisz (Esc anuluje). Jeśli jest już używany, oba działania zamienią się klawiszami. |
| 73 | nl | Klik op een actie en druk op de nieuwe toets (Esc annuleert). Als de toets al in gebruik is, wisselen de twee acties van toets. |
| 73 | pt-PT | Clique em uma ação e pressione a nova tecla (Esc cancela). Se a tecla já estiver em uso, as duas ações trocam de tecla. |
| 74 | en | Defaults loaded; audio has already changed. Click Apply to confirm the other settings. |
| 74 | es | Valores predeterminados cargados; el audio ya cambió. Haz clic en Aplicar para confirmar las demás opciones. |
| 74 | de | Standardwerte geladen; der Ton wurde bereits geändert. Klicke auf Anwenden, um die übrigen Einstellungen zu bestätigen. |
| 74 | fr | Valeurs par défaut chargées ; l'audio a déjà changé. Cliquez sur Appliquer pour confirmer les autres réglages. |
| 74 | zh-Hans | 已加载默认设置；音频已更改。点击应用以确认其他设置。 |
| 74 | ja | 初期設定を読み込みました。音声はすでに変更されています。適用をクリックして、その他の設定を確定してください。 |
| 74 | ru | Стандартные значения загружены; звук уже изменился. Нажмите «Применить», чтобы подтвердить остальные настройки. |
| 74 | ko | 기본값을 불러왔으며 오디오는 이미 변경되었습니다. 적용을 클릭해 나머지 설정을 확정하세요. |
| 74 | it | Valori predefiniti caricati; l'audio è già cambiato. Fai clic su Applica per confermare le altre impostazioni. |
| 74 | pl | Wczytano ustawienia domyślne; dźwięk już się zmienił. Kliknij Zastosuj, aby potwierdzić pozostałe ustawienia. |
| 74 | nl | Standaardwaarden geladen; het geluid is al gewijzigd. Klik op Toepassen om de overige instellingen te bevestigen. |
| 74 | pt-PT | Padrões carregados; o áudio já mudou. Clique em Aplicar para confirmar as demais configurações. |
| 75 | en | Keep this display mode? The previous one returns in {0} s. |
| 75 | es | ¿Mantener este modo de pantalla? El anterior volverá en {0} s. |
| 75 | de | Diesen Anzeigemodus beibehalten? Der vorherige kehrt in {0} s zurück. |
| 75 | fr | Conserver ce mode d'affichage ? Le précédent revient dans {0} s. |
| 75 | zh-Hans | 保留此显示模式？{0}秒后恢复之前的模式。 |
| 75 | ja | この画面モードを維持しますか？{0}秒後に元のモードに戻ります。 |
| 75 | ru | Сохранить этот режим экрана? Предыдущий вернётся через {0} с. |
| 75 | ko | 이 화면 모드를 유지할까요? {0}초 후 이전 모드로 돌아갑니다. |
| 75 | it | Mantenere questa modalità video? La precedente torna fra {0} s. |
| 75 | pl | Zachować ten tryb ekranu? Poprzedni wróci za {0} s. |
| 75 | nl | Deze schermmodus behouden? De vorige keert terug over {0} s. |
| 75 | pt-PT | Manter este modo de tela? O anterior volta em {0} s. |
| 76 | en | Quit to desktop |
| 76 | es | Salir al escritorio |
| 76 | de | Zum Desktop beenden |
| 76 | fr | Quitter vers le bureau |
| 76 | zh-Hans | 退出到桌面 |
| 76 | ja | デスクトップに戻る |
| 76 | ru | Выйти на рабочий стол |
| 76 | ko | 바탕 화면으로 나가기 |
| 76 | it | Esci al desktop |
| 76 | pl | Wyjdź na pulpit |
| 76 | nl | Afsluiten naar bureaublad |
| 76 | pt-PT | Sair para a área de trabalho |

## Conquistas — integração sem casos especiais por ID

O consumidor interpreta apenas `all` (AND recursivo) e folhas com `path`, `op`, `value`; `aggregate` opcional `sum` ou
`count` lida com diário de pesca e álbum. Operações: `>=`, `==` e `contains`. Não usar nomes de conquista para escolher
lógica nem traduzir paths, enum `coqueiro`, ids ou nomes de campo. A referência em `achievements_check.py` recusa bool
como contador, strings em lugar de listas e ausências de dados. Não conceder conquistas em save vazio.

**27 conquistas usam campos atuais; cinco aguardam `/prog/debt/paid_cents`; quatro aguardam contadores novos.** Os cinco
negócios usam AND de cinco campos existentes `/prog/biz/<id>/lvl`. Contagem do álbum significa fotos presentes, conforme
a especificação; a pesca soma as espécies registradas. As 36 flags demo/hidden e os textos pt-BR foram comparados com
`docs/steam/conquistas.json` automaticamente.

| Conquistas / campos | Proveniência confirmada |
|---|---|
| Empresa; vendas; oito expansões | MareSimulation.cpp:114, :249, :295 (`company.created`, `kiosk_n`, `unlocked.<id>`) |
| Quatro capítulos | MareSimulation.cpp:348–366 AdvanceChapter; tamanho dos steps em definitions.json; `prog.ch.<id>` |
| Bar 50; todas as receitas; receita secreta | MareBar.cpp:184, :191, :197, :429; `bar.served`, `prog.achievements.mestre_drinks`, `bar.known` |
| Cinco negócios nível 1/3 | MareBizCommon.cpp:26–27, :75; `prog.biz.<id>.lvl` |
| Pesca/garoupa e fotos | MareLeisure.cpp:22–28, :35–49; `prog.fish`, `prog.album` |
| Pedido VIP; crítico; evento na praia | MareHotelRooms.cpp:175–179; MareRestaurant.cpp:190–216; MareHotelEvents.cpp:104, :120 |
| Campeonato; dois fliperamas | MarePoolCup.cpp:173; MareArcade.cpp:35, :216; `billiards.cups`, `prog.biz.fliperama.records.<id>` |

| Novo contador | Atualizar no ponto existente | Por que precisa |
|---|---|---|
| `/prog/steam_counters/guided_barco` | RecordTourResult, MareTours.cpp:210–236, bGuide e Pax>=1 e id barco | `tour_results` retém só 12 resultados |
| `/prog/steam_counters/guided_snorkel` | Mesmo ponto, id snorkel | Evitar perder o fato histórico ao sair do histórico |
| `/prog/steam_counters/guided_farol` | Mesmo ponto, id farol | Mesmo motivo |
| `/prog/steam_counters/hotel_polished` | CleanHotelRoom, MareHotelRooms.cpp:118–131, ao concluir sem ajuda | `polished` some no checkout; incrementar uma vez por arrumação, nunca por tarefa |

Inicial 0; saves antigos podem reconstruir um mínimo comprovado do histórico/quartos atuais, sem inventar o que já se
perdeu. Campos e regras estão em `_new_counters`. Conquistas da dívida dependem da transação real, não de faturamento,
`ea_end_shown`, patrimônio ou campanha. Criar fila persistente/offline e idempotente para Steam; o JSON sozinho não
habilita conquistas. Rich Presence inclui textos prontos e pontos de entrada/saída propostos em `_trigger`; a seleção de
atividade depende do contexto do runtime e não é dedutível só do save. Conta Steamworks/App ID exigem configuração real.

## Variações: o que ficou preservado e por quê

Conferência de sorteio: `MareComicEvents.cpp:129–132`, `:227–229`, `:336–338`, `:409–411` chama LineIndex com
`bSequence=false` para as cinco listas ampliadas. `MareComicEventsTests.cpp:27–29` exige asks_en com o mesmo tamanho.
Respostas e reações são pares por índice, não listas de sorteio independentes: preservadas.

- `tours.json/reviews`: MareTours.cpp:228–229 indexa pelo resultado da escolha (bom/neutro/ruim), não sorteia. Acrescentar
  três strings ali não produziria variação e poderia confundir a semântica. Preservado; para variar, o Claude teria de
  mudar o consumidor C++, fora deste pacote.
- `hotel_rooms.json`: reclamações são tipos de tarefa com id, custo e prazo; os textos são campos individuais dos tipos.
  Não duplicar tipos para criar falas: isso alteraria probabilidades e tarefas.
- `restaurant.json`: menu/mesas e avaliação do crítico têm resultado calculado; as falas relevantes vêm do C++.
- `business_games.json/steps`: passos ordenados das rodadas, não falas sorteadas; alterar tamanho mudaria o minijogo.
- `comic_events.json` HUM-007/HUM-008 têm sequence=true: reclamações/pescaria crescem em sequência; preservadas.
- `bar.json/discard_reactions`: MareBar.cpp:271 usa contador módulo tamanho, não sorteio; preservado pela regra atual.
- Moradores: falas e opções principais são nativas; HUMOR_EVENTOS_COMICOS.md é documentação, não lista consumida no jogo.

## Só o que exige Claude / C++ / editor

1. Aplicar os 10 registros de textos nativos (9 pontos de consumidor; item 9 é derivado do 8), com suas traduções acima.
2. Implementar State.prog.debt, migração, PayDebt e lembretes idempotentes, carta, cartão Finanças, marcos e final/créditos;
   o roteiro e as funções existentes estão em DIVIDA_DA_AVO.md. Não copiar a simplificação de lembretes do modelo econômico.
3. Ler achievements.json, criar quatro contadores, avaliação genérica e fila Steam offline; Rich Presence e Steamworks.
4. No editor/runtime, testar fluxo da demo e completo, dois cliques, falha de save, Unicode, quebra de linha e comprimento
   dos textos nos 12 idiomas. Rodar qa_gate.py com Unreal e fotografar os painéis; estes testes não foram simulados como PASS.
5. Aumentar diversidade de avaliações/diálogos indexados somente se mudar os consumidores nativos explicitamente.

As sugestões de reescrita extra dos textos de debt.json na seção “Os 29 textos da dívida” da revisão não fazem parte dos
itens numerados solicitados. Não alteradas: o contrato original de dívida continua intacto, com seus textos já traduzidos.
Não se mexeu em taxas/preços/condições de progressão, nem se aplicaram os descontos econômicos opcionais do pacote 4.

## Como conferir (sem Unreal)

```sh
python tools/ue58/i18n_extract.py
python tools/ue58/qa/data_lint.py
python tools/ue58/qa/data_lint.py --self-test
python tools/ue58/qa/glossary_check.py --self-test
python tools/ue58/qa/achievements_check.py
python tools/ue58/balance/test_debt_vectors.py
python tools/ue58/balance/test_debt.py
python tools/ue58/balance_model.py --self-test
```

Resultado final observado: 12 idiomas completos, zero erros no lint/glossário/contrato de conquistas; 20 vetores/45 ações
da dívida e testes econômicos passam. O índice de assets verifica caminhos e referências, não a carga/renderização.
O extrator gera todo_*.json vazios como intermediários: não versionar esses arquivos. Para o runtime futuro, verificar
exatamente as condições nos pontos de evento, salvar antes de notificar Steam e preservar campos desconhecidos do save.


# Pacote 7 — tutorial, campanha, percurso da demo e Steam

07/11/2026. Base remota conferida: `09dcc3837a91e3428c29b9fb8d91c38dc3c05ec9`, merge do Pacote 6. A árvore desse merge
é idêntica à entrega anterior (`1a385f5c23553e0bafa11a3bebb37aad82fae7d0`). Branch `gpt/pacote-7`, destino
`codex/ue58-migration`. **Não houve alteração em C++, .uasset, metas, recompensas, ordem ou números de economia.**
Não houve execução da Unreal, build Shipping, publicação na Steam ou medição de duração em playtest.

## Entrega e contagens

- **62 campos textuais existentes corrigidos:** 42 em tutorial.json, 12 em definitions.json, seis em world.json,
  um em tours.json e um em events.json. Campos numéricos, IDs, pré-requisitos, ordenação e recompensas preservados.
- Todas as **44 dicas anteriores foram conferidas**: 42 reescritas; RoomService e biz:surfe mantidas por serem curtas
  e corretas (a tradução polonesa de surfe foi encurtada). Duas dicas novas usam ações já existentes: Door e IntroLetter.
- Nove dicas de gestão adicionais, prontas nos dados e nos idiomas, **ainda sem chamadas C++**: phone:stock, staff,
  finance, expansions, missions, custom, recipes, events e debt. Não são anunciadas como fluxos ativos. Total: 55 dicas.
- **113/113 LOCTEXT e 4.055/4.055 strings em cada um dos 12 idiomas**, sem vazias. 81 chaves novas e
  68 removidas contra a base. Chaves antigas com consumidor nativo continuam existindo até ele ser migrado.
- Extrator corrigido para os quatro textos de desbloqueio de capítulos e para títulos explícitos de tutorial com
  hífen (Pingue-pongue). Slugs como fab:143 deixam de virar traduções. IDs, teclas e campos de save não são traduzidos.
- `demo_walkthrough.py` e `number_text_check.py` ligados ao `data_lint.py`, além do glossário e conquistas do Pacote 6.
- Materiais finais pt-BR/en: página da demo, página do jogo principal em Acesso Antecipado, FAQ do EA e patch notes 0.1.
  Os cabeçalhos editoriais separam texto publicável e condições de integração; não há promessa de data/preço futuro.

## Tutorial: o que a leitura do código mudou

| Tema | Correção / evidência |
|---|---|
| Quiosque | Produto pronto, anotar com E, pagamento na entrega: MareSimulation.cpp:237–248; placa e dormir: :124–144, :451–453 |
| Bar | E no ingrediente executa BarPick + BarPour, sem transporte manual: MareServiceTarget.cpp:129–132. Dicas BarCounter/BarIngredient/BarGlass atualizadas |
| Coletes | Entrega ocorre na primeira parada. Sair sem todos os coletes gera resultado pior, mas é permitido: MareBoatTourWorld.cpp:256–257. Removido “ninguém sai sem colete” |
| Mesa suja | Mesa indisponível até limpar, e atendente recolhe: MareKioskWorld.cpp:38, :120–126, :192–195 |
| Piscina | Folhas/toalhas afetam limpeza e nota ao fechar; piscineiro contratado ajuda: MarePool.cpp:36–39, :90–99. Venda respeita estoque: :59–68 |
| Pousada | Negociação e necessidade de quarto limpo: MareStays.cpp:83–118. Não foram inventadas diárias ou etapas novas |
| Hotel | Recepção aceita oferta depois de 120 minutos se houver quarto limpo: MareStays.cpp:186–192. Arrumação/consumo do frigobar: MareHotelRooms.cpp:94–131 |
| Oferenda | Cortesia no encontro não conta como entrega manual; levar ao cesto nos dias seguintes antes das 22h: MareSummitWorld.cpp:125–157 |
| Gestão | Celular reúne o que já existe. Chamadas por seção ainda exigem C++ e estão discriminadas abaixo |
| Dívida | Objetivo narrativo na abertura, no gancho e no final da demo. Não se prometeu botão de pagamento ativo nesta base; phone:debt aguarda PayDebt |

O cartão de dica **não fica dentro da tela do celular** nesta base: MareGame.cpp:2596–2599 usa largura 400/wrap 370,
fonte FCoreStyle Regular 12 (a chamada passa 12.5 a um parâmetro int32); :2760–2761 conta 14 segundos e o oculta enquanto
bPhone estiver aberto. Encurtamos os textos para o espaço real encontrado. A estimativa estática, com margem de fonte,
ficou em até duas linhas para **715 combinações (55 dicas × pt-BR e 12 traduções)**, registrada em
[PACOTE7_TUTORIAL_QA.json](PACOTE7_TUTORIAL_QA.json). Usa DejaVu Sans 16px e avanço CJK de 16px como aproximação; não
substitui o layout Slate, DPI, fontes de fallback ou a escala escolhida pelo jogador. A confirmação visual é do editor.

## Fontes CJK reconstruídas sem editor

Os recortes Noto Sans SC/JP/KR estavam atrás dos catálogos, inclusive em textos anteriores a este pacote. Foram
reconstruídos a partir das fontes oficiais Google Fonts (peso 500), sem alterar .uasset ou C++ e preservando as
atribuições já existentes em CREDITS.md. As três licenças SIL OFL foram incluídas em Content/UI/Fonts/OFL-NotoSans*.txt.
`i18n_fonts.py` ganhou --source-dir e --families para funcionar fora do caminho fixo do Windows, preservando o padrão
antigo. Não se versionaram downloads completos nem caches.

`font_coverage_check.py` confere os intervalos de MareNotebookStyle.h contra os três arquivos resultantes:
**1.626 pontos SC, 1.129 JP e 880 KR exigidos; zero glifos CJK ausentes**. Evidência com hashes dos TTF em
[PACOTE7_FONTES_QA.json](PACOTE7_FONTES_QA.json). Isto comprova cobertura dos arquivos, não a seleção/renderização Slate.

Fontes-base: `https://github.com/google/fonts/tree/main/ofl/notosanssc`, `notosansjp` e `notosanskr`. Licenças copiadas
junto aos recortes. Para reconstruir num cache fora do Windows (fontTools já é dependência do script):

```sh
python tools/ue58/i18n_fonts.py --source-dir /caminho/do/cache --families NotoSansSC NotoSansJP NotoSansKR --download
python tools/ue58/qa/font_coverage_check.py
```

## Campanha e capítulos: conferência de todos os predicados

MareSimulation.cpp:299–326 define MissionAmount; :330–366 define abertura/progresso/avanço dos capítulos; :432–443
resgata a missão e avança stage. “serve” conta **produtos entregues**, não clientes únicos (:253–259). “sell” conta
somente o item vendido durante a etapa ativa. Corrigidos os dois textos. Os textos de descoberta do bar são corretos
em partida nova; saves legados também podem ter prog.disc, que soma ao contador (:350). Melhorias de receitas de
campanha são a soma de RecipeLevel-1, e personalização conta tier-1 em uso, não compras históricas (:322–325).

| Missão | Exigência real / contador | Demo |
|---|---|---|
| chegada: Uma nova maré | company.created (booleano); meta 1 | sim |
| portas: Portas abertas | company.kiosk_open OU kiosk_n > 0; meta 1 | sim |
| primeiros: O sabor da primeira manhã | kiosk_n, produtos entregues acumulados; meta 8 | sim |
| mesas: Um lugar para ficar | unlocked.<id>; meta 1; item kiosk_tables | sim |
| equipe: Uma parceria de verdade | staff.atendente (booleano); meta 1 | sim |
| morro: O velho do morro | summit.met; meta 1 | sim |
| oferendas: Três dias sem Onda | summit.count, entregas manuais; meta 3 | sim |
| comunidade: O quiosque e o mar | prog.ch.<id> >= quantidade de steps; meta 1; item pier | sim |
| encontro: O encontro dos viajantes | unlocked.<id>; meta 1; item bar | sim |
| hospedar: Fique mais um dia | unlocked.<id>; meta 1; item pousada | sim |
| verao: Um verão inesquecível | unlocked.<id>; meta 1; item pool | sim |
| prainha_m: A prainha secreta | prog.ch.<id> >= quantidade de steps; meta 1; item prainha | sim |
| sabores_m: Sabores da Dona Cecília | prog.ch.<id> >= quantidade de steps; meta 1; item sabores | sim |
| carnaval_m: Carnaval na areia | prog.ch.<id> >= quantidade de steps; meta 1; item carnaval | sim |
| marealta: A Maré Alta da vila | unlocked.<id>; meta 1; item grand_hotel | limite; não resgatada |
| salao: O salão da vila | unlocked.<id>; meta 1; item salao_jogos | jogo completo |
| chef: Cardápio de chef | soma RecipeLevel(dish)-1; meta 20 | jogo completo |
| postal: Cartão-postal | soma max(0,tier-1) em State.custom; meta 40 | jogo completo |
| lenda: Lenda da costa | FameLevel, teto 10; meta 10 | jogo completo |
| fregueses: Sete mil vendas | kiosk_n, produtos entregues acumulados; meta 7000 | jogo completo |
| festa: A Festa da Maré Alta | prog.campaign.finale após cena na praia; meta 1 | jogo completo |

| Capítulo / etapa | Texto conferido | Contador real |
|---|---|---|
| pier / 1 | Levar 4 peixes para o almoço dos pescadores | stock.<item>; desconta qty ao concluir |
| pier / 2 | Entregar 15 produtos no quiosque durante esta etapa | prog.ch.<id>_serve; por produto na etapa ativa |
| pier / 3 | Doar R$ 150 para as tábuas novas | money >= qty; Book(-qty) |
| prainha / 1 | Chegar à fama "Ponto da praia" | FameLevel |
| prainha / 2 | Fotografar o farol (tecla P) | prog.chp.<item> (booleano) |
| prainha / 3 | Levar 6 cocos para o mutirão | stock.<item>; desconta qty ao concluir |
| sabores / 1 | Descobrir 2 drinks novos no Bar do Coqueiro | prog.disc + BarDiscoveries |
| sabores / 2 | Vender 10 porções de petiscos durante esta etapa | prog.ch.<id>_sell; item na etapa ativa |
| sabores / 3 | Pagar R$ 250 da reforma do food truck | money >= qty; Book(-qty) |
| carnaval / 1 | Chegar à fama "Famoso na região" | FameLevel |
| carnaval / 2 | Ter 2 negócios funcionando | quantidade de negócios comprados (lvl > 0) |
| carnaval / 3 | Pagar R$ 400 da decoração | money >= qty; Book(-qty) |

Os quatro story de capítulos continuam coerentes com os pedidos/givers. O unlock de carnaval foi corrigido: o evento
segue events.party_calendar por Day%7 após party_from_day e o capítulo, **não o fim de cada verão** (MareEvents.cpp:20–26).

A abertura passa a citar Dona Dilce viva no bingo e R$ 1.000.000; o marco marealta liga o Grand Hotel à dívida sem dizer
que a etapa é da demo dentro da build completa. A festa deixa explícito que comemorar não quita dívida; sua janela é
20h até antes de 23h30 (MareSummitWorld.cpp:292). A meta permanece **7.000 vendas**; o título virou “Sete mil vendas”.

**Limite nativo importante:** MissionsPage mostra title/task, mas **não campaign.story**, e omite a missão bloqueada
(MareGame.cpp:805–812). As histórias estão preparadas e traduzidas; exibi-las precisa da pequena alteração de UI abaixo.
O gancho visível da demo já foi aplicado em events.end_of_content.text, lido por SMareEndScreen em MareGame.cpp:1756:
“Grand Hotel e quitação da dívida de Dona Dilce” ficam no jogo completo. O próprio objetivo bloqueado não é resgatado.

## Percurso da demo em Python

[PACOTE7_DEMO_PERCURSO.json](PACOTE7_DEMO_PERCURSO.json) contém o rastro completo de uma partida lógica nova:
empresa → placa → vendas → compras na expansion_order → atendente → Seu Tibúrcio → três oferendas manuais em dias
subsequentes à cortesia → capítulos → negócios necessários → campanha parada em marealta → todas as oito expansões
da demo e quatro capítulos → tela de agradecimento. Grand Hotel e salão permanecem trancados.

O teste lê os JSON atuais, não injeta caixa, usa vendas repetíveis de coco com compra de insumos, recompensas e custos
registrados. Reserva capital para financiar a próxima venda; nas noites das oferendas usa teto salarial conservador
dos níveis. Não reproduz relógio/XP de funcionário, navmesh, estoques físicos de cena, tentativas/habilidade, eventos
aleatórios ou as consequências visuais. É prova de **alcançabilidade dos predicados modelados**, não execução do C++
nem medição de cerca de 2 horas. O código nativo foi a referência de leitura, não uma biblioteca executada em Python.

Verifica pré-requisitos/ordem, IDs, itens entregáveis/vendáveis, fotos, limites booleanos/fama/descobertas/negócios,
idiomas de missões/capítulos/dicas/final, bloqueio full_game antes do limite e condição da tela final. **13 mutações
negativas são reprovadas**, incluindo pré-requisito falso/full_game, item ausente, fama 11, 999 descobertas, meta
booleana 2, negócio impossível, tradução ausente, dica ausente, coco sem margem e final já marcado no save inicial.

## Auditoria de números

O inventário [PACOTE7_AUDITORIA_NUMEROS.json](PACOTE7_AUDITORIA_NUMEROS.json) lista textos numéricos extraídos dos
JSON e do Source, com arquivos/campos/linhas. Classifica números mecânicos, formatos dinâmicos, atributos/numeração,
humor e console/QA; não transforma nomes, tempos cômicos ou detalhes de material em regra de economia. A classificação
é triagem contextual, não prova automática de cada regra nativa. O validador permanente cobre os vínculos mecânicos
explícitos que podem ser comparados sem Unreal.

| Conferência | Resultado / fonte |
|---|---|
| Expansões | bar R$ 900; pousada R$ 1.400; piscina R$ 1.100; passeios R$ 1.000; Grand Hotel R$ 45.000 — definitions.expansions; preservados |
| Venda final | task, título e história em 7.000, com mesmo qty/reward/posição |
| Dívida | principal R$ 1.000.000; marcos 25/50/75%, teto demo R$ 250.000; debt.json intacto e sem consumidor nativo |
| Preços impressos | Confrontados com definitions.dishes.<id>.price; são preços-base, não preços personalizados de um save |
| Estoque nas placas | Removidos “6 prontos”/“12 prontos” fixos de seis etiquetas de world.json: viraram “Produtos prontos”; estoque real é variável |
| Chapa / maior preço | Petiscos custam 26 e porção de peixe 28. Removido “o prato mais caro” da descrição da expansão; preços não mudaram |
| Camareira | Removido “a cada 20 minutos”: StaysHour processa tarefas por hora, orçamento 3×StaffSkill, não um relógio fixo de 20 min |
| Pôr do sol | JSON [17.25,17.95] = 17h15–17h57; instrução antiga dizia 17h55; corrigida nas 12 traduções |
| Minijogos | bolas/1,8 s, voltas 7/9, fritura 6–8 e 6,3–7,6 s, fitas 2/12 e 1,5/9 s conferidos com levels[].set |
| Bônus | Balcão +10/20/30/40% e barco +1/2/3/4 vagas seguem efeitos × tier-1; funcionário 60%, bartender 85% e +15% conferidos |
| Hotel | 32 quartos vem de PlaceRooms/MareStays.cpp:33; três tipos e três visitáveis em hotel_rooms.json; não chamar todos de suítes |
| EA e duração | Cerca de 2 h é estimativa de progressão informada/simulada, não timer. Nenhuma duração total ou data garantida na copy |

Números nativos atuais lidos e correspondências principais (nenhuma troca de preço fixo nativo foi necessária):

| Texto/regra C++ | Fonte dos dados / regra | Arquivo:linha |
|---|---|---|
| Almoço 12h–15h, jantar 19h–22h | restaurant.services [[12,15],[19,22]] | MareGame.cpp:298; MareRestaurant.cpp:40 |
| Hóspedes 10h–20h | janela nativa de StaysHour, não preço | MareStays.cpp:179–185; MareGame.cpp:590 |
| Recepção após 2h | 120 minutos, oferta com quarto limpo | MareStays.cpp:191; MareGame.cpp:586 |
| +15% bartender / +10% camareira | operations.hourly.bar.staff_bonus=.15; operations.pousada.maid_bonus=.1 | MareSimulation.cpp:837–839 |
| Restaurante: 90%, sem garçom 45 min/70% | .9 e 15 min nativos; restaurant.crew_minutes=45/crew_share=.7 | MareRestaurant.cpp:159–161 |
| Sinuca: oito jogadores / uma rodada ao dia | bracket de oito nativo; game_room.cup para taxa/prêmios/ciclo semanal | MarePoolCup.cpp:120; MareGame.cpp:423 |
| Tênis de mesa: melhor de 3, 11 pontos | regra nativa (dois games vencidos, vantagem de dois pontos) | MareTableTennis.h:19–20 |
| Três paradas / três rodadas | tours.stops com três escolhas; business_games.steps; consumidores de tour/minijogo | MareTours.cpp:228; MareBoatTourWorld.cpp:58 |
| Cinco níveis de receitas/bar, três de negócios | recipes.levels e upgrades.prices têm cinco; base+levels dos negócios = três | MareSimulation.cpp:600; MareBizCommon.cpp:27 |

Os números são corretos nesta base; alguns rótulos nativos ainda são literais e podem divergir se os dados mudarem.
As linhas exatas de todas as ocorrências catalogadas estão no inventário. Tamanhos de TV, fios de roupa de cama,
numeração de quartos/props, regra de bola 8 e exageros de pescaria foram mantidos em suas categorias; não são custos
de expansão nem metas. A inspeção física de props e o comportamento de minijogos continuam sendo validação no editor.

## Materiais da Steam prontos

| Uso | pt-BR | en |
|---|---|---|
| Demo grátis | [loja_pt-BR.md](../steam/loja_pt-BR.md) | [loja_en.md](../steam/loja_en.md) |
| Jogo principal / EA | [loja_completo_pt-BR.md](../steam/loja_completo_pt-BR.md) | [loja_completo_en.md](../steam/loja_completo_en.md) |
| Notas 0.1 da demo | [patch_notes_demo_0_1_pt-BR.md](../steam/patch_notes_demo_0_1_pt-BR.md) | [patch_notes_demo_0_1_en.md](../steam/patch_notes_demo_0_1_en.md) |
| FAQ de EA e comparação | [acesso_antecipado.md](../steam/acesso_antecipado.md) | Mesmo arquivo, seção English |

Descrição curta e longa de cada produto, distinção demo/EA, por que EA, duração sem previsão inventada, diferenças
pretendidas, conteúdo atual, preço sem compromisso e participação da comunidade estão incluídos. A copy do jogo
principal que descreve pagar a dívida depende da implementação antes da publicação; a demo não anuncia botão de
pagamento que não existe. Não se prometem migração de save, Steam Cloud, conquistas integradas, Deck, co-op, data ou
requisitos de hardware sem teste. Materiais de planejamento/presskit anteriores não substituem estas páginas finais.

## Para o Claude — somente C++ ou editor

1. **Mostrar campaign.story** em MissionsPage (MareGame.cpp:805–810) além de title/task, respeitando o limite da demo;
   traduzir via MareLoc o valor já localizado em Data. As 21 histórias já estão completas nos 12 mapas: nenhum texto
   novo precisa ser inventado. O gancho final visível de SMareEndScreen já vem de events.json; não duplicar a tela.
2. **Ligar as nove dicas de gestão** abaixo a ShowTip e tornar a dica visível na seção apropriada do celular. Não chamar
   em cada Rebuild, marcar como vista antes de aparecer ou deixar o timeout vencer escondido. O comportamento atual
   é MareGame.cpp:2500 e :2760–2761; manter o sistema existente, sem novo tutorial/onboarding.
3. **Trocar três rótulos/instruções nativos** na tabela abaixo, migrando as chaves e os 12 idiomas junto do Source.
4. **Integrar dívida/final/Steam** já entregues no Pacote 6: DIVIDA_DA_AVO.md, debt.json, achievements.json,
   PACOTE6_TEXTOS_CPP.json. Permanecem tarefas nativas, não um motivo para adiar dados/traduções. Os pagamentos e
   o final precisam existir antes de publicar a copy do jogo principal que os descreve.
5. **Editor/build:** confirmar wrapping/DPI/fallback dos 12 idiomas, duas dicas novas em portas/carta, timings reais,
   navegação, chegada/campanha/continuidade da demo e texto final. Rodar qa_gate.py e capturar evidências reais.
   Medir as cerca de 2 h com jogadores; os testes Python não foram apresentados como esse playtest.

### Três textos nativos — colar com as traduções

Versão estruturada: [PACOTE7_TEXTOS_CPP.json](PACOTE7_TEXTOS_CPP.json). No item bar_pick, o formato C++ continua usando
`%s` e `%d`; as chaves de localização usam {0}/{1}. Nenhuma destas substituições foi aplicada ao Source ou antecipada
nos catálogos ativos.

| ID | Arquivo:linha | Atual | Novo |
|---|---|---|---|
| bar_help | unreal/MareAlta/Source/MareAlta/MareGame.cpp:548 | Pegue os ingredientes na bancada do fundo (E) e coloque no copo (E). Depois use o copo para socar, bater e servir. | Use E nos ingredientes para colocá-los direto no copo. Depois use E no copo para preparar e servir. |
| bar_pick | unreal/MareAlta/Source/MareAlta/MareBarWorld.cpp:177 | {0} · pegar ({1}) | {0} · adicionar ao copo ({1}) |
| demo_hook | unreal/MareAlta/Source/MareAlta/MareGame.cpp:812 | Fim da demo: a história continua no jogo completo, com o Grand Hotel. | Fim da demo: o Grand Hotel e a quitação da dívida de Dona Dilce continuam no jogo completo. |

| ID | Idioma | Tradução nova |
|---|---|---|
| bar_help | en | Use E on ingredients to add them straight to the glass. Then use E on the glass to prepare and serve. |
| bar_help | es | Usa E en los ingredientes para añadirlos al vaso. Luego usa E en el vaso para preparar y servir. |
| bar_help | de | Mit E auf Zutaten kommen sie direkt ins Glas. Danach mit E am Glas zubereiten und servieren. |
| bar_help | fr | E sur les ingrédients les ajoute au verre. Puis E sur le verre pour préparer et servir. |
| bar_help | zh-Hans | 对原料按E即可直接加入杯中，然后对杯子按E完成调制并供应。 |
| bar_help | ja | 材料にEを押すと直接グラスへ。続いてグラスでEを押し、仕上げて提供します。 |
| bar_help | ru | Нажмите E на ингредиентах: они попадут в бокал. Затем E на бокале, чтобы приготовить и подать. |
| bar_help | ko | 재료에 E를 누르면 바로 잔에 들어갑니다. 그다음 잔에 E를 눌러 준비하고 서빙하세요. |
| bar_help | it | Usa E sugli ingredienti per metterli nel bicchiere. Poi E sul bicchiere per preparare e servire. |
| bar_help | pl | Użyj E na składnikach, by dodać je do szklanki. Potem E na szklance, by przygotować i podać. |
| bar_help | nl | Gebruik E op ingrediënten om ze in het glas te doen. Gebruik daarna E op het glas om te bereiden en serveren. |
| bar_help | pt-PT | Use E nos ingredientes para colocá-los direto no copo. Depois use E no copo para preparar e servir. |
| bar_pick | en | {0} · add to glass ({1}) |
| bar_pick | es | {0} · añadir al vaso ({1}) |
| bar_pick | de | {0} · ins Glas geben ({1}) |
| bar_pick | fr | {0} · ajouter au verre ({1}) |
| bar_pick | zh-Hans | {0} · 加入杯中（{1}） |
| bar_pick | ja | {0} · グラスに加える（{1}） |
| bar_pick | ru | {0} · добавить в бокал ({1}) |
| bar_pick | ko | {0} · 잔에 넣기 ({1}) |
| bar_pick | it | {0} · aggiungi al bicchiere ({1}) |
| bar_pick | pl | {0} · dodaj do szklanki ({1}) |
| bar_pick | nl | {0} · in het glas doen ({1}) |
| bar_pick | pt-PT | {0} · adicionar ao copo ({1}) |
| demo_hook | en | End of demo: the Grand Hotel and paying off Dona Dilce's debt continue in the full game. |
| demo_hook | es | Fin de la demo: el Grand Hotel y liquidar la deuda de Dona Dilce continúan en el juego completo. |
| demo_hook | de | Ende der Demo: Grand Hotel und Tilgung von Dona Dilces Schulden gehen im vollständigen Spiel weiter. |
| demo_hook | fr | Fin de la démo : le Grand Hotel et le remboursement de la dette de Dona Dilce continuent dans le jeu complet. |
| demo_hook | zh-Hans | 试玩版结束：Grand Hotel和还清Dona Dilce债务的目标将在完整版继续。 |
| demo_hook | ja | デモ終了。Grand HotelとDona Dilceの借金完済は製品版へ続きます。 |
| demo_hook | ru | Конец демо: Grand Hotel и погашение долга Dona Dilce продолжаются в полной игре. |
| demo_hook | ko | 데모 끝: Grand Hotel과 Dona Dilce의 빚 청산은 전체 게임에서 이어집니다. |
| demo_hook | it | Fine demo: Grand Hotel e rimborso del debito di Dona Dilce continuano nel gioco completo. |
| demo_hook | pl | Koniec dema: Grand Hotel i spłata długu Dona Dilce czekają w pełnej grze. |
| demo_hook | nl | Einde demo: het Grand Hotel en het aflossen van Dona Dilce's schuld gaan verder in de volledige game. |
| demo_hook | pt-PT | Fim da demo: o Grand Hotel e a quitação da dívida de Dona Dilce continuam no jogo completo. |

### Dicas de gestão preparadas — gatilhos ainda pendentes

As 12 traduções de cada linha já estão em tutorial.json/Localization e no JSON acima, prontas para uso após os gatilhos.

| Chave | Ponto sugerido no C++ | Texto pt-BR |
|---|---|---|
| phone:stock | unreal/MareAlta/Source/MareAlta/MareGame.cpp:940 | Reponha produtos pelo celular. Confira o custo antes de comprar. |
| phone:staff | unreal/MareAlta/Source/MareAlta/MareGame.cpp:941 | Confira contratação, salário e turno antes de contratar. |
| phone:finance | unreal/MareAlta/Source/MareAlta/MareGame.cpp:942 | Veja o caixa e os lançamentos. A dívida é o objetivo da história. |
| phone:expansions | unreal/MareAlta/Source/MareAlta/MareGame.cpp:943 | Confira os requisitos e o preço da próxima expansão. |
| phone:missions | unreal/MareAlta/Source/MareAlta/MareGame.cpp:944 | Confira a tarefa atual e resgate as recompensas já liberadas. |
| phone:custom | unreal/MareAlta/Source/MareAlta/MareGame.cpp:945 | Compare preço e efeito das melhorias antes de comprar. |
| phone:recipes | unreal/MareAlta/Source/MareAlta/MareGame.cpp:876 | Melhore receitas para valorizar os produtos. Veja o custo do próximo nível. |
| phone:events | unreal/MareAlta/Source/MareAlta/MareGame.cpp:747 | Veja a previsão de amanhã e prepare o resort para o evento. |
| phone:debt | unreal/MareAlta/Source/MareAlta/MareGame.cpp:732 | Pague quando puder, sem juros. Confira o caixa antes de confirmar. |

phone:recipes fica na seção de receitas dentro de CustomizePage; phone:events, no cartão de previsão/preparativos de
ResortPage. phone:debt só deve disparar depois que o cartão da dívida existir. Não expor essas dicas como promessa de
funcionalidade antes da integração. As dicas genéricas phone e as ações físicas existentes continuam ativas.

## Como conferir

```sh
python tools/ue58/i18n_extract.py
python tools/ue58/qa/data_lint.py
python tools/ue58/qa/demo_walkthrough.py
python tools/ue58/qa/demo_walkthrough.py --self-test
python tools/ue58/qa/number_text_check.py --self-test
python tools/ue58/qa/test_i18n_extract.py
python tools/ue58/qa/font_coverage_check.py
python tools/ue58/qa/glossary_check.py --self-test
python tools/ue58/qa/achievements_check.py
python tools/ue58/balance/test_debt_vectors.py
python tools/ue58/balance/test_debt.py
python tools/ue58/balance_model.py --self-test
```

Resultado observado: 12 catálogos completos; 49 JSON, 796 referências de modelos e **zero erros no data_lint**,
incluindo glossário, conquistas, percurso e vínculos numéricos. 13 mutações de percurso e cinco de números rejeitadas;
regressões do extrator, cobertura CJK e testes herdados passam. O teste de fontes exige fontTools; o data_lint permanece sem dependências externas. Sem C++, .uasset, alteração de meta/valor ou arquivo todo no commit.
O índice de packages mantém a origem dos nomes na árvore Git e apenas renova hashes dos JSON textuais alterados.

Para reproduzir os relatórios de dados:

```sh
python tools/ue58/qa/demo_walkthrough.py --json > docs/ue58/PACOTE7_DEMO_PERCURSO.json
python tools/ue58/qa/number_text_check.py --inventory > docs/ue58/PACOTE7_AUDITORIA_NUMEROS.json
```

O extrator cria todo_*.json vazios como intermediários; não versioná-los. O relatório de tamanho é estimativa estática,
não captura da Unreal. O diff dos dados foi comparado estruturalmente: apenas os 62 campos textuais existentes e as
11 entradas de dicas foram alterados/adicionados; listas e números preexistentes são idênticos à base.


---

# Pacote 8 — rádio, Steamworks, saves em 3 slots e preset Baixo

**Data:** 07/11/2026. Branch \`gpt/pacote-8\`, baseada no merge do pacote 7 \`2e8aa8e4154c5eb1baf9c22effc225fc8418c623\`; alvo do PR: \`codex/ue58-migration\`. **Nenhum arquivo C++ nem .uasset alterado.** Escopo: fontes JSON, localização, scripts Python/SteamPipe, documentos e metadados do índice de assets.

## 1. Rádio

- [Rádio — 12 faixas e segurança de licenças](RADIO_MUSICAS.md), [manifesto de músicas](../../tools/ue58/radio_tracks.json), [script de download](../../tools/ue58/fetch_radio.py) e créditos em [CREDITS.md](../../CREDITS.md).
- Fonte CC0 1.0 *Open Lo-Fi* do autor B. Tahir: autorização expressa para apps, games, vídeos e streams e uso comercial; release ZIP com SHA-256 publicado \`0040fb9c8bcc22e5f91d1dbf3fb02b6ceff97e249588369bddf9c1fb26950550\`. O script baixa **fora do repositório**, para \`D:/Assets/Audio/radio/\`, confere esse hash e registra SHA-256 individual de cada faixa. Não baixa quando executado sem \`--download\`.
- **Limites de segurança:** o catálogo não garante ausência de Content ID, não é música baiana autêntica, e não disponibiliza MP3 individuais nem duração/BPM no catálogo. Assim, **nenhuma das 12 faixas externas está aprovada para inclusão comercial ou streamer mode**, mesmo sob licença CC0. Ausência de reivindicação não é provada. A pesquisa excluiu Kevin MacLeod por política explícita de Content ID; o caminho de menor risco é encomendar música original baiana sob contrato que também proíba cadastro em sistemas de claims.
- \`audio.json\`: preservados os \`/Game/Audio\` originais, seis registros preexistentes \`radio_*\` marcados com \`group:\"radio\"\`; os 12 externos NÃO recebem path inexistente. \`radio_ui.json\`: rótulos de estação, música anterior/próxima, ligar e desligar; todas as 12 traduções incorporadas.
- **Claude (apenas C++/editor):** conectar grupo \`radio\` no player com UI, controles, volume, estado salvo, modo streamer e importação de assets **apenas após liberação de direitos**, sem registrar músicas sem uasset.
- **Sergio:** aprovar o repertório realmente baiano e a documentação de licença + ausência de Content ID. A autorização de jogos/streams não prova imunidade a claims.

## 2. Steamworks

- **13 VDFs de Rich Presence** em [rich_presence/](../steam/rich_presence/) com tokens de estados e 36 conquistas por idioma, traduzidos com as strings existentes; sistema ainda precisa conectar tokens ao cliente Steam.
- [Tabela CSV de 36 conquistas × pt-BR e inglês](../steam/conquistas_upload_ptBR_en.csv), IDs/oculto/demo/jogo completo explícitos; **36 IDs**, **72 linhas de dados**. A demo elegível não implica conquista ativada automaticamente no AppID da demo.
- [SteamCMD](../../tools/ue58/steamcmd/): quatro VDFs app_build/depot_build separados para demo ~2 h e jogo completo; só valores de AppID/DepotID marcados como \`PREENCHER_*\`. Caminhos previstos \`D:/Builds/MareAltaUE58_Demo/Windows\` e \`D:/Builds/MareAltaUE58_Completo/Windows\` devem ser conferidos contra saída real do BuildCookRun.
- [Guia Steamworks para Sergio, na ordem](../steam/STEAMWORKS_PASSO_A_PASSO.md): IDs, localização, achievements, configuração da demo, empacotamento Unreal/SteamPipe, builds internos, QA e publicação manual.
- **Claude (apenas C++/editor):** Steamworks SDK/Rich Presence, tela e gatilhos de conquistas, criar Shipping real/demo separadamente e validar executáveis.
- **Sergio:** configurar Steamworks real, inserir IDs, localização, enviar builds e decidir publicação. Nenhum upload para Steam foi feito.

## 3. Saves

- [Auditoria Save/Load e Steam Cloud](SAVES_SLOTS.md) baseada nos \`MareSimulation.cpp/.h\` e \`MareKioskPersistence.cpp\` existentes. O jogo **já tem três slots**, \`slots.json\`, autosave e \`.bak\`; não inventamos trabalho inexistente.
- [Validador Python](../../tools/ue58/qa/save_check.py) de estrutura de saves JSON e [fixtures](../../tools/ue58/qa/fixtures/): v7 atual, antigo v6 incompleto e JSON truncado. \`--self-test\` aprovado em **4/4** cenários; \`--fallback-bak\` verifica cópia sem alterar arquivo.
- **Defeito a tratar pelo Claude em C++:** depois de ler um principal corrompido pelo \`.bak\` íntegro, \`WriteState\` pode copiar o **principal corrompido** sobre a cópia boa na próxima gravação. Validar antes de rotacionar backup e fazer teste de recuperação após duas gravações.
- **Sergio:** configurar Steam Cloud após confirmar path real e testes cruzados/offline, sem apontar a nuvem para builds divergentes.

## 4. Gráficos baixos

- [Preset Baixo com variáveis, motivação e medição](PRESET_BAIXO.md). \`MareOptions\` atualmente tem \`SetPreset(0)\`, redução de crowd 6→3 e alcance 5000→3500 cm, LOD agressivo e simulação de cabelo já desligada se Effects<3. Proposta para desligar Lumen real e diminuir sombras, distância, densidade de NPC, vegetação, resolução/TSR.
- Benchmarks anteriores **não são FPS na máquina mínima**: 1080p 80% ~10,29 ms frame médio/p95 ~14,26 ms; 1080p nativo ~12,56 ms/p95 ~16,20 ms, em cenário próprio.
- Requisitos Steam **provisórios** (16 GB RAM/RTX 2060 ou RX 6600 mínimo candidato; 32 GB RAM/RTX 3060–4060 recomendado candidato). Sem divulgação como medido antes de testar hardware real.
- **Claude (apenas C++/editor):** implementar preset completo, perfis LOD/MetaHuman distante e 3 rodadas do benchmark em máquinas distintas; registrar FPS real, 1% low, p95/p99, VRAM e qualidade visual.
- **Sergio:** validar e publicar requisitos apenas após logs reais.

## 5. Traduções e QA

- [Workflow CI](../../.github/workflows/pacote8-validacao.yml) em GitHub Actions, compilação não necessária; executa \`python tools/ue58/i18n_extract.py\` completo, compara arquivos por \`git diff --exit-code\`, exige zero traduções vazias em 12 idiomas, depois \`save_check --self-test\`, \`achievements_check.py\` e \`data_lint.py\`.
- CI executada em [GitHub Actions](https://github.com/sergiomrge-tech/simulador-resort/actions/runs/42384844041): **12 idiomas**, cada um com **4.061 strings + 113 LOCTEXT**, extração reproduzível, nenhuma vazia; **4/4** cenários de save e **36** conquistas validados.
- \`data_lint\` nesse run: **50 JSON**, **796** referências de modelos, **12.012** packages reais da árvore Git consultados, **ZERO erros**, inclusive glossário e números; índice Git atualizado em \`tools/ue58/balance/package_index.json\` com hashes SHA-256 dos 50 JSON. A CI cria índice efêmero do snapshot para funcionar em checkout esparso, sem acessar conteúdo binário dos uassets. Não corresponde a validação de runtime Unreal.
- Primeiro CI falhou por Python 3.11 incompatível com a sintaxe do lint existente; migrado para Python 3.12. Segundo falhou porque o índice de pacotes antigo estava obsoleto e três idiomas não preservavam literal \`Maré Alta\`; ambos corrigidos. **Não silenciaram** os erros do glossário.
- Verificar depois do PR: \`python tools/ue58/i18n_extract.py\`; \`python tools/ue58/qa/build_package_index.py --output indice-qa.json\` (com Git); \`python tools/ue58/qa/data_lint.py --asset-index tools/ue58/balance/package_index.json --json\`; \`python tools/ue58/qa/save_check.py --self-test\`; \`python tools/ue58/qa/achievements_check.py\`; \`python tools/ue58/fetch_radio.py --list\`.
- **Limites desta entrega:** nenhum executável/asset foi compilado, nenhum download de rádio foi comprovado no drive D: do Sergio, não houve verificação real de direitos Content ID ou de FPS mínimo, nenhum cadastro de Steamworks foi alterado. Esses limites **não** invalidam as validações estáticas aprovadas.

**Próximo handoff:** Claude fica exclusivamente com C++/Unreal Editor indicados acima; Sergio com aprovações de música, Steamworks, requisitos após QA e publicação. O PR permanece para revisão, sem merge automático.


## Complemento — música opcional nas configurações

Solicitação de Sergio: **manter as músicas existentes** e oferecer um interruptor **“Desativar música”** em `Opções → Áudio`, sem afetar efeitos, vento, mar e sons da praia. `Content/Data/radio_ui.json` declara rótulo, texto de ajuda e comportamento. As 12 traduções serão atualizadas nesta mesma branch. O áudio existente já permite `Music=0`; a implementação da caixa/checkbox C++ em `MareGame.cpp::SMareOptions::AudioPage` e a restauração persistente do volume anterior ficam para Claude (sem editar C++ nesta entrega). A possibilidade de desativar música não supre a checagem de Content ID.


---

# Pacote 9 — auditoria, Steam multilíngue, créditos, captação e divulgação

**07/11/2026 · branch `gpt/pacote-9` · origem `codex/ue58-migration` @ `0ba71c4cd15d23a5007edfb7f142f6dfa98f263f` · PR direcionado para essa base.** Nenhum C++/header, `.uasset`, `radio.json` ou `audio.json` foi alterado. O ramo não deve ser mesclado antes do gate técnico e jurídico.

## Entregas efetivamente versionadas

| Pedido | Status / arquivos | Validação / limite |
|---|---|---|
| 1. Auditoria C++ somente leitura | `docs/ue58/AUDITORIA_CODIGO_PACOTE9.md`: cenários concretos, gravidades P0/P1/P2, linhas e diffs/propostas, incluindo rádio, tela de créditos, dicas e natação | **69 arquivos .cpp** de `Source/MareAlta` lidos e varridos estaticamente; nenhuma compilação nem PIE |
| 2. Teste manual da demo | `docs/ue58/TESTE_MANUAL_DEMO.md`: percurso aproximado de 2 h do save novo ao agradecimento, controle de caixa/fama/compra/capítulo e planilha de problemas/fotos | Percurso **não executado** por humano; gates definidos para Sergio |
| 3. Acessibilidade | `docs/ue58/ACESSIBILIDADE.md`: texto, sons, daltonismo, controles, pausa, velocidade e modo sem pressa, com código, esforço e prioridade | Proposta sem C++; não publicar como recursos entregues |
| 4. Steam em 13 idiomas | `docs/steam/loja_<locale>.md` **demo**, `docs/steam/loja_completo_<locale>.md` **jogo completo** para es/de/fr/it/nl/pl/pt-PT/ru/ja/ko/zh-Hans; pt-BR e en mantêm originais. `docs/steam/TAMANHOS_PACOTE9.md` | **22 descrições curtas novas <=300 caracteres Unicode**, tabela nominal; revisão humana nativa ainda necessária. Duas páginas distintas |
| 5. Direitos e créditos | `docs/LICENCAS_TERCEIROS.md` lista autores, licenças e links; `Content/Data/credits.json` contém seis seções propostas, autor/papel/atribuição e títulos traduzidos em 12 idiomas | **Bloqueadores comerciais**: prova de assets locais Fab/info.json, Caveat OFL, Open Lo-Fi/stream, avisos Unreal/CC BY na UI |
| 6. Capturas 1080p | `tools/ue58/qa/marketing_shots.py` e `docs/ue58/CAPTURAS_PACOTE9.md`; 10 capturas da demo, 12 planos do trailer, câmeras, preparação e nomes, uso de `qa_gate.py` e `pool_swim_qa.py` | **Roteiro/script entregues, 0 capturas reais obtidas**: requer Unreal Editor, MCP, save QA e revisão do Sergio |
| 7. Dica do rádio | Texto pt-BR e local do gatilho em `AUDITORIA_CODIGO_PACOTE9.md` | **Não editado** `tutorial.json` porque `MareServiceTarget.cpp:91` retorna antes de `ShowTip` linha 93; C++ deve ser alterado primeiro |
| 8. Devlogs / campanhas | `docs/steam/devlogs/01_heranca_` ... `08_radio_` em pt-BR e en (**16 arquivos**); `CALENDARIO_6_SEMANAS.md` com **30 posts × 2 idiomas**: Steam/X/Instagram/TikTok/Reddit | Preparado, **não publicado**; calendário relativo S-6 a S-1, sem datas prometidas |
| 9. Relatório | Esta seção `Pacote 9` de `docs/ue58/GPT_RELATORIO.md` | Estado do PR/CI precisa ser confirmado após abertura |

**Créditos e i18n:** os dados de `credits.json` são **proposta não integrada**, todos os campos editoriais têm prefixo `_`, logo o extrator atual de `i18n_extract.py` os ignora até existir consumidor C++. Quando Claude ativar os textos na UI, migrar para conteúdo player-facing com chave pt-BR, atualizar `source.json` e os 12 idiomas. A dica do rádio também depende de gatilho no C++, portanto não introduzir traduções órfãs agora.

## Críticos para Claude — C++/editor (somente estas dependências)

1. **P0 `MareAudioWorld.cpp:27-42`** — esquema de `radio.json` é array `[id,nome]`, mas o leitor C++ usa `AsObject`/campos `id`/`name`. Aplicar o diff do documento de auditoria, testar `Aloha FM → ... → off`, UI do celular e E nos três aparelhos; confirmar que as ondas importadas/permitidas realmente tocam.
2. **P1 `MareServiceTarget.cpp:91-93` + `MareHomeWorld.cpp:80-92`** — ligar `ShowTip` à ação HomeStereoKiosk; após o gatilho, incluir a dica **“Rádio do quiosque” / “Use E no rádio para trocar a música. No celular, escolha anterior, próxima ou desligar.”** em `tutorial.json`. Traduzir pelas regras **chave = frase pt-BR**, inclusive 12 catálogos, extrair completamente.
3. **P1 `MareGame.cpp:2224-2235`, `MareAudioWorld.cpp:54-98`** — integrar a opção de **Desativar música** que `radio_ui.json` já propõe, persistindo `MusicMuted` e `MusicLastNonZero`; manter ambiente/efeitos, inclusive em streams. Testar reinício/restauração.
4. **P1 `MareGame.cpp:1837-1845` e tela final da dívida** — substituir créditos estáticos por consumer de `credits.json`, incluir duas linhas literais do Unreal EULA e atribuição CC BY; disponibilizar créditos completos ao público.
5. **P2 `MarePoolSwimWorld.cpp:224,232,253,356`** — defensivas de `Jump_Start` nulo, `ride_seconds`/tempo mínimo, entrada do console; validar MetaHuman/piscina/tobogã em PIE/packaged, sem prometer tobogã da demo.
6. **Editor (sem mudar catálogo protegido)** — varrer `/Game/Custom`, `/Game/Audio`, roupas/Fab, `info.json` em `D:/Assets`, licenças de fontes e cook; somente publicar faixas licenciadas/com liberação de stream confirmada. Fotos reais de 1920×1080 e testes de UI/CJK.

**Notas de correções anteriores confirmadas estaticamente:** `MareGame.cpp:2881` agora chama `SaveClock+=DeltaSeconds` fora do comentário e executa o autosave de 30 s; `MareSimulation.cpp:424-429` agora aplica XP negativo com piso de nível; `MareStays.cpp:102` já remove `vip_asked/vip_done` por nova estadia. **Ainda não são provas de teste em runtime.** Não reabrir regressões resolvidas sem reprodução.

## Para Sergio — teste e lançamento

- Jogar **uma sessão do zero (~2 h)** conforme `TESTE_MANUAL_DEMO.md`, **sem comandos QA**, anotando duração verdadeira, cada compra/pagamento, fama, capítulo, carta, rádio, piscina, saldo após carregar, screenshot/defeito.
- Não autorizar marketing com capturas não geradas/revisadas, música pendente de Content ID ou hotel/tobogã tratados como demo.
- Fazer gate documental com a versão exata da build: `docs/LICENCAS_TERCEIROS.md`, contratos Fab/info.json, atribuição game-icons, licenças OFL/Caveat, EULA Unreal/MetaHuman/NVIDIA.
- Depois das correções, testar PT-BR, EN, pelo menos um CJK, controle/teclado, texto 150%, música desligada e retorno do save; assinar checklist antes da Steam.

## Como conferir tecnicamente

```powershell
# No clone atualizado de gpt/pacote-9; Python 3, arquivos com encoding='utf-8'
python tools/ue58/i18n_extract.py
python tools/ue58/qa/save_check.py --self-test
python tools/ue58/qa/achievements_check.py
python tools/ue58/qa/build_package_index.py --output .tmp-pacote9-index.json --log-chunks
python tools/ue58/qa/data_lint.py --asset-index .tmp-pacote9-index.json --json
python -m py_compile tools/ue58/qa/marketing_shots.py
python tools/ue58/qa/marketing_shots.py --plan
```

**Gate do i18n:** `git diff --exit-code -- unreal/MareAlta/Content/Localization/Mare/` *excluindo* `todo_*.json` gerados; nenhum `todo_*.json` entra no commit; catálogo válido, placeholders `{N}` e `<br>`, nenhum texto vazio. O workflow já existente `.github/workflows/pacote8-validacao.yml` executa o extrator completo, comparação do `source.json`/12 traduções e `data_lint.py --asset-index ... --json` no PR para `codex/ue58-migration`.

**Estado de validação nesta sessão:** inventário/manual/contratos/roteiros criados e versionados; **não foi possível executar editor Unreal no ambiente GitHub, nem alegar zero erros do data_lint antes do resultado do Actions**. CI/PR devem confirmar `i18n_extract.py` integral sem diff e `data_lint` com zero erros. Qualquer falha deve ser corrigida **sem alterar os caminhos proibidos** antes de merge.

**Checklist de integridade antes do merge:** diff sem `Source/**`, `*.uasset`, `radio.json`, `audio.json`; 11 pares de páginas, 16 devlogs, 6 semanas de posts; `credits.json` JSON válido e 12 títulos localizados por seção; screenshots do editor somente se foram realmente produzidas.


## Encerramento e validação verificada do Pacote 9

- **Branch/PR:** `gpt/pacote-9` → `codex/ue58-migration`, [PR #15](https://github.com/sergiomrge-tech/simulador-resort/pull/15), **sem merge**.
- **Build de verificação:** `5b5400cdeaa866193931699c7050e6fe96174851` — o GitHub Actions concluiu com **success** os dois jobs: **Pacote 8 - integridade de dados e traducoes** (extrator `i18n_extract.py`, catálogos, verificador de saves/conquistas, índice de assets e `data_lint.py` com saída sem erros) e **Pacote 9 - QA dos materiais de lancamento** (sintaxe Python, descrições curtas, créditos 12 idiomas e devlogs). Confirmação por consulta a execuções do commit, não por execução local.
- **Dica de rádio:** as **12 traduções adicionais** (mais a fonte pt-BR, 13 versões totais) foram preparadas na [auditoria de código](AUDITORIA_CODIGO_PACOTE9.md#traduções-prontas-da-dica-do-rádio-após-integração-pelo-claude). Só inserir `tutorial.json` + catálogos após corrigir o gatilho `MareServiceTarget.cpp:91-93`; o pacote não altera os textos ativos do jogo sem consumidor.
- **Permanecem externos:** compilação C++/PIE, cook/pacote Steam, capturas reais, conferência jurídica e teste manual Sergio. Nenhum deles está aprovado apenas pelo CI de dados.

**ATENÇÃO:** o commit desta subseção atualizará o SHA após os checks anteriores. O workflow do PR será novamente acionado na cabeça mais recente; verificar conclusão do novo SHA antes do merge.
