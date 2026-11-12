# Falas de conversa dos personagens (redator, 12/11/2026)

Mesmas regras do lote: jogador sem gênero ("Meu bem", "você"), "Dona Dilce" na boca dos moradores, nada de trocadilho que só funcione em português. Cada fala ≤ 200 caracteres; `(n/200)` ao lado. Ids no formato `npc.<quem>.talk.<situação>`.

**Como o jogo sorteia (sugestão ao programador):** ao conversar, se houver fala de missão/capítulo ela tem prioridade. Senão, monta a lista com as 4 gerais + a do horário (manhã cedo = antes das 9h; fim de tarde/noite = depois das 17h) + a do clima (chuva) + a de festa (dia de festa do calendário) + a da dívida (menos ou mais da metade paga) e sorteia uma, evitando repetir a última. Depois da festa final, a fala `epilogue` entra no lugar das duas da dívida.


# Parte 1 — personagens decididos

## a) Prefeita Tuanny

> **Quem é:** prefeita em exercício, de terninho, na praça (manhã) e no alpendre da prefeitura (tarde).  
> **Jeito de falar:** tom de palanque mesmo em conversa de balcão; anuncia em vez de contar.  
> **Mania:** cortar fita em qualquer coisa; anda com uma tesoura dourada no bolso do terninho.  

- `npc.tuanny.talk.general1` **Geral 1**: "Esta semana eu inaugurei um banco da praça, uma lixeira e um degrau. O degrau foi o mais emocionante." (101/200)
- `npc.tuanny.talk.general2` **Geral 2**: "Prometi calçamento até a praia. Ainda não veio, mas a promessa está ótima, muito bem conservada." (96/200)
- `npc.tuanny.talk.general3` **Geral 3**: "Carrego a tesoura dourada no bolso. Nunca se sabe quando vai aparecer uma fita." (79/200)
- `npc.tuanny.talk.general4` **Geral 4**: "Se alguém perguntar, o quiosque é um orgulho da gestão. Se der errado, é iniciativa privada." (92/200)
- `npc.tuanny.talk.morning` **Manhã cedo**: "Bom dia! Prefeita acorda cedo: às seis já tem gente na porta pedindo coisa. Às sete, eu já prometi tudo." (104/200)
- `npc.tuanny.talk.evening` **Fim de tarde / noite**: "Fim de expediente. Hoje foram três reuniões, dois discursos e uma fita. Dia tranquilo." (86/200)
- `npc.tuanny.talk.rain` **Dia de chuva**: "Chuva em inauguração dá sorte. Pelo menos é o que eu digo em toda inauguração com chuva." (88/200)
- `npc.tuanny.talk.festival` **Dia de festa do calendário**: "Dia de festa! A prefeitura apoia, prestigia e, principalmente, aparece na foto." (79/200)
- `npc.tuanny.talk.debt_low` **Dívida: pagou menos da metade**: "Um milhão é bastante dinheiro, meu bem. Eu sei porque é mais ou menos o orçamento da vila. Do ano inteiro." (106/200)
- `npc.tuanny.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade paga! Se quiser, faço um discurso. Curto. Uns quarenta minutos." (78/200)
- `npc.tuanny.talk.epilogue` **Depois que a Dona Dilce voltou**: "Com a Dona Dilce de volta, a vila ganhou mais uma eleitora e mais uma fiscal da prefeitura. Estou feliz e com medo." (115/200)

**Nota ao tradutor:**
- Tuanny é política simpática: a graça é vaidade e discurso, nunca corrupção. "cortar fita" = ribbon cutting (imagem recorrente dela).
- "calçamento" = rua calçada/pavimentada. "iniciativa privada" = private sector; a piada é ela assumir só o que dá certo.


## b) Seu Arnaldo

> **Quem é:** o freguês reclamão dos eventos cômicos (HUM-007); no capítulo `critico` revela-se o crítico gastronômico. Mesa do quiosque de dia; restaurante do hotel depois.  
> **Jeito de falar:** frases curtas, "Hmpf", detalhe técnico preciso demais para um freguês comum.  
> **Mania:** anota tudo num caderninho e esconde quando alguém olha. Antes da revelação as falas só dão pistas; depois, ele reclama com nota.  

- `npc.arnaldo.talk.general1` **Geral 1**: "O gelo deste coco foi feito com água da torneira. Dá para sentir no segundo gole. Eu sinto." (91/200)
- `npc.arnaldo.talk.general2` **Geral 2**: "A cadeira da mesa dois balança três milímetros para a esquerda. Não estou reclamando. Estou registrando." (104/200)
- `npc.arnaldo.talk.general3` **Geral 3**: "O pastel saiu dois minutos antes do ponto. Eu sei porque contei. Eu sempre conto." (81/200)
- `npc.arnaldo.talk.general4` **Geral 4**: "Hmpf. A gaivota que roubou a batata ontem tinha razão. Estava sem sal." (70/200)
- `npc.arnaldo.talk.morning` **Manhã cedo**: "Cedo assim, o coco ainda está com gosto de sono. Volto às dez, quando ele acordar." (82/200)
- `npc.arnaldo.talk.evening` **Fim de tarde / noite**: "O pôr do sol de hoje veio alaranjado demais. Exagerado. Mas dou sete." (69/200)
- `npc.arnaldo.talk.rain` **Dia de chuva**: "Chuva. Pelo menos agora ninguém pode dizer que eu reclamo do sol." (65/200)
- `npc.arnaldo.talk.festival` **Dia de festa do calendário**: "Festa é ótima para avaliar cozinha: todo mundo com pressa, ninguém prestando atenção. Menos eu." (95/200)
- `npc.arnaldo.talk.debt_low` **Dívida: pagou menos da metade**: "Um milhão de dívida e você ainda põe hortelã de graça no suco. Generosidade não é estratégia financeira." (104/200)
- `npc.arnaldo.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade paga. Admito: não esperava. Anotei." (50/200)
- `npc.arnaldo.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce me pediu uma crítica do quiosque. Dei dez. Ela disse que eu devia estar doente. Talvez esteja." (107/200)
- `npc.arnaldo.talk.post_reveal1` **Geral extra, só depois do capítulo `critico`**: "Agora que todo mundo sabe quem eu sou, ninguém mais me serve pastel cru. Perdi metade do meu material." (102/200)
- `npc.arnaldo.talk.post_reveal2` **Geral extra, só depois do capítulo `critico`**: "Nota de hoje: coco, oito. Pastel, sete e meio. Atendimento, nove. Brisa, quatro: continua bagunçando meu cabelo." (112/200)

**Nota ao tradutor:**
- Usar o mesmo nome e o mesmo "Hmpf" da tradução de HUM-007. A brisa que bagunça o cabelo (post_reveal2) cita a fala 3 de HUM-007.
- Até o capítulo `critico` NÃO traduzir de modo que revele o crítico: "dou sete" é só mania de dar nota.
- As duas `post_reveal` entram no sorteio no lugar de `general1` e `general3` depois do capítulo.


## c) Seu Bené

> **Quem é:** pescador velho, contador de histórias (HUM-008); rival amistoso do Seu Severino. Píer de manhã, beira do quiosque à tarde.  
> **Jeito de falar:** arrastado, começa com "Sabe..."; cada história é maior que a anterior.  
> **Mania:** medir peixe abrindo os braços, cada vez mais.  

- `npc.bene.talk.general1` **Geral 1**: "Sabe o robalo de que eu falei? Ontem ele passou por baixo do píer e o píer subiu um palmo." (90/200)
- `npc.bene.talk.general2` **Geral 2**: "O Severino diz que pesca mais do que eu. Pesca mesmo. Mas os meus peixes são maiores na conversa." (97/200)
- `npc.bene.talk.general3` **Geral 3**: "Sabe, uma vez pesquei um polvo que sabia contar. Contou meus anzóis e levou três." (81/200)
- `npc.bene.talk.general4` **Geral 4**: "Peixe grande não se mede com régua, se mede com os braços. E os meus braços crescem com o tempo." (96/200)
- `npc.bene.talk.morning` **Manhã cedo**: "Cedo assim o mar ainda fala baixinho. É a hora em que ele conta onde estão os peixes." (85/200)
- `npc.bene.talk.evening` **Fim de tarde / noite**: "Fim de tarde é hora de história. De dia eu pesco; de noite o peixe cresce." (74/200)
- `npc.bene.talk.rain` **Dia de chuva**: "Com chuva o peixe sobe para ver o que está acontecendo. Peixe é curioso igual gente." (84/200)
- `npc.bene.talk.festival` **Dia de festa do calendário**: "Em dia de festa eu conto a história da garoupa no palco. Ninguém me convida, mas eu subo." (89/200)
- `npc.bene.talk.debt_low` **Dívida: pagou menos da metade**: "Um milhão? Sabe, eu devo uma rede para o Severino há trinta anos. Ele cobra toda semana. Dívida pequena incomoda mais." (118/200)
- `npc.bene.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade? Quando eu contar essa história, vai ter sido numa semana só." (76/200)
- `npc.bene.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce é a única que lembra o tamanho certo dos meus peixes. Por isso eu fujo dela." (89/200)

**Nota ao tradutor:**
- Robalo (snook) e garoupa (grouper) são os peixes de HUM-008: mesma tradução. "um palmo" = palm's width (~20 cm).
- Bené nunca é mentiroso cruel: o exagero é carinhoso e todo mundo sabe.


## d) Dona Dilce (só no epílogo; complementa as 6 falas do lote)

> **Quem é:** a avó, de volta; varanda do hotel de dia, quiosque no fim da tarde.  
> **Jeito de falar:** a mesma voz das cartas: carinho com piada seca, frases curtas.  
> **Mania:** reparar em tudo do quiosque e jurar que é sem querer.  

- `npc.dilce.talk.morning` **Manhã cedo**: "Acordei às cinco, de costume. Quarenta anos abrindo quiosque, e o corpo ainda não sabe que eu me aposentei." (107/200)
- `npc.dilce.talk.evening` **Fim de tarde / noite**: "Fim de tarde era a minha hora preferida atrás do balcão. Agora é a minha hora preferida na frente dele." (103/200)
- `npc.dilce.talk.rain` **Dia de chuva**: "Chuva de verão é igual visita de vizinho: chega sem avisar e vai embora antes do café." (86/200)
- `npc.dilce.talk.festival` **Dia de festa do calendário**: "Festa na vila! As meninas do bingo vieram de barco. Esconde as cocadas, meu bem." (80/200)

**Nota ao tradutor:**
- Ela não tem falas de dívida (já está quitada). As 6 falas gerais estão em `textos_lote.md`, ids `epilogue.dilce.*`.


## e) Os cinco vendedores
Os vendedores sabem da dívida por fofoca da vila; as falas de dívida são leves e não revelam a fiança.

### Giovana — Sorveteria Gelato da Maré

> **Quem é:** sorveteira jovem, balcão da sorveteria, 9h–19h.  
> **Jeito de falar:** rápido e animado, tudo em lista.  
> **Mania:** anunciar o "sabor do dia", que é sempre coco.  

- `npc.giovana.talk.general1` **Geral 1**: "Hoje tem sorvete de coco, coco queimado e coco com coco. Variedade é tudo." (74/200)
- `npc.giovana.talk.general2` **Geral 2**: "Tem freguês que pede casquinha de três bolas e come a casquinha primeiro. Eu não julgo. Só observo." (99/200)
- `npc.giovana.talk.general3` **Geral 3**: "O segredo do gelato é paciência e um freezer que não desliga quando passa o caminhão do gás." (92/200)
- `npc.giovana.talk.general4` **Geral 4**: "Um dia eu faço sorvete de manga. Quando o coco deixar." (54/200)
- `npc.giovana.talk.morning` **Manhã cedo**: "De manhã ninguém quer sorvete. Às dez em ponto todo mundo quer, ao mesmo tempo." (79/200)
- `npc.giovana.talk.evening` **Fim de tarde / noite**: "Fim de tarde o sorvete derrete mais devagar e as pessoas conversam mais. Gosto dessa hora." (90/200)
- `npc.giovana.talk.rain` **Dia de chuva**: "Chuva é ótima: só aparece quem gosta de sorvete de verdade. Hoje foram dois. Eu e o Kauã." (89/200)
- `npc.giovana.talk.festival` **Dia de festa do calendário**: "Em dia de festa eu faço sorvete de coco com confete. É o mesmo de coco, só que mais feliz." (90/200)
- `npc.giovana.talk.debt_low` **Dívida: pagou menos da metade**: "Ouvi dizer que é um milhão. Quantas casquinhas dá isso? Comecei a conta e desisti no meio." (90/200)
- `npc.giovana.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade paga! Hoje a bola extra é por conta da casa. Da minha casa, no caso." (83/200)
- `npc.giovana.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce provou meu sorvete e disse que faltava coco. Faltava coco! No sorvete de coco!" (91/200)

### Seu Valdir — Aluguel de pranchas e caiaques

> **Quem é:** homem maduro, quiosque de aluguel no píer, 8h–18h.  
> **Jeito de falar:** pausado, conta tudo em caiaques e coletes.  
> **Mania:** conta os caiaques que saem e os que voltam, e confere cada colete duas vezes.  

- `npc.valdir.talk.general1` **Geral 1**: "Saíram doze caiaques hoje e voltaram doze. Dia bom. Teve dia que voltaram onze e meio." (86/200)
- `npc.valdir.talk.general2` **Geral 2**: "Tem turista que aluga a prancha só para tirar foto. Cobro igual. A prancha também trabalha na foto." (99/200)
- `npc.valdir.talk.general3` **Geral 3**: "Colete salva-vidas não é enfeite. Repito isso vinte vezes por dia. Às vezes para a mesma pessoa." (96/200)
- `npc.valdir.talk.general4` **Geral 4**: "O Seu Severino me deixou este canto do píer. Disse que é para eu vigiar os barcos dele. De graça, claro." (104/200)
- `npc.valdir.talk.morning` **Manhã cedo**: "Cedo o mar fica liso que nem mesa. É a melhor hora para remar e a hora em que ninguém acorda." (93/200)
- `npc.valdir.talk.evening` **Fim de tarde / noite**: "Fim de tarde eu conto os caiaques e passo cera nas pranchas. Prancha encerada dorme melhor." (91/200)
- `npc.valdir.talk.rain` **Dia de chuva**: "Com chuva ninguém aluga nada. Aproveito para conversar com os coletes." (70/200)
- `npc.valdir.talk.festival` **Dia de festa do calendário**: "Em dia de festa sempre aparece alguém querendo remar fantasiado. Pode. Com o colete por cima da fantasia." (105/200)
- `npc.valdir.talk.debt_low` **Dívida: pagou menos da metade**: "Dívida se paga igual se rema contra o vento: devagar, mas sem largar o remo." (76/200)
- `npc.valdir.talk.debt_high` **Dívida: pagou mais da metade**: "Passou da metade? Agora o vento virou a favor. Só não solte o remo, hein." (73/200)
- `npc.valdir.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce alugou um caiaque e sumiu por duas horas. Achei na prainha, tomando coco com o Padre." (98/200)

### Kauã — Escolinha de surfe

> **Quem é:** instrutor jovem, areia da prainha, 8h–17h.  
> **Jeito de falar:** tranquilo, sem pressa, conselho em forma de onda.  
> **Mania:** dar nota de 0 a 10 para tudo, como se fosse onda.  

- `npc.kaua.talk.general1` **Geral 1**: "Primeira lição: cair. Segunda lição: cair melhor. A terceira eu ainda estou aprendendo." (87/200)
- `npc.kaua.talk.general2` **Geral 2**: "Tem aluno que fica em pé na prancha perfeitamente na areia. Aí entra na água e esquece que tem pernas." (102/200)
- `npc.kaua.talk.general3` **Geral 3**: "Dou nota para tudo como se fosse onda. O quiosque é oito. Com coco gelado, nove." (80/200)
- `npc.kaua.talk.general4` **Geral 4**: "Ainda não convenci o Seu Valdir a subir numa prancha. Ele diz que já sobe no píer todo dia." (91/200)
- `npc.kaua.talk.morning` **Manhã cedo**: "As melhores ondas chegam às seis. Os alunos chegam às dez. A gente se desencontra todo dia." (91/200)
- `npc.kaua.talk.evening` **Fim de tarde / noite**: "O mar de fim de tarde é o mais bonito e o mais difícil. Igual prova final." (74/200)
- `npc.kaua.talk.rain` **Dia de chuva**: "Chuva não molha quem já está no mar. É o meu argumento para não cancelar aula." (78/200)
- `npc.kaua.talk.festival` **Dia de festa do calendário**: "Em dia de festa eu dou aula de camisa florida. A camisa cai na água junto, mas cai bonita." (90/200)
- `npc.kaua.talk.debt_low` **Dívida: pagou menos da metade**: "Um milhão é uma onda grande. Não dá para pegar de uma vez. Rema, espera e pega a que vier." (90/200)
- `npc.kaua.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade? Isso é você em pé na prancha, de verdade. Nota nove." (68/200)
- `npc.kaua.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce quer aprender a surfar. Eu disse que começa na areia. Ela disse que a areia é minha e o mar é dela." (112/200)

### Dona Zezé — Barraca do pastel

> **Quem é:** senhora, dona da barraca do pastel na rua principal, 10h–20h.  
> **Jeito de falar:** rápido, mandão e carinhoso; chama qualquer pessoa de "criatura".  
> **Mania:** recusa qualquer pastel que não seja carne, queijo ou camarão.  

- `npc.zeze.talk.general1` **Geral 1**: "Carne, queijo e camarão. Pastel de chocolate eu não faço. Pastel é coisa séria, criatura." (89/200)
- `npc.zeze.talk.general2` **Geral 2**: "Tem freguês que assopra o pastel e queima a boca assim mesmo. Todo santo dia. É tradição." (89/200)
- `npc.zeze.talk.general3` **Geral 3**: "O meu óleo eu troco toda semana. A Dona Cecília conferiu. Ela confere tudo." (75/200)
- `npc.zeze.talk.general4` **Geral 4**: "A massa eu abro na mão, igual a minha mãe abria. A máquina eu comprei, mas ela fica de enfeite." (95/200)
- `npc.zeze.talk.morning` **Manhã cedo**: "Cedo eu ainda estou abrindo massa. Pastel antes das dez é falta de respeito com o pastel." (89/200)
- `npc.zeze.talk.evening` **Fim de tarde / noite**: "Fim de tarde a fila dobra. Todo mundo jura que só vai comer um. Ninguém come um." (80/200)
- `npc.zeze.talk.rain` **Dia de chuva**: "Chuva dá vontade de pastel. Sol também. Pensando bem, tudo dá vontade de pastel." (80/200)
- `npc.zeze.talk.festival` **Dia de festa do calendário**: "Em dia de festa eu frito três vezes mais e ainda falta. A fila chega na igreja." (79/200)
- `npc.zeze.talk.debt_low` **Dívida: pagou menos da metade**: "Um milhão é muito pastel, criatura. Fiz a conta: dá para fritar até eu me aposentar duas vezes." (95/200)
- `npc.zeze.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade paga? Leve um de camarão, por conta. Só hoje, que eu também tenho conta para pagar." (98/200)
- `npc.zeze.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce pediu um pastel e ficou olhando eu fritar. Fiquei mais nervosa que no dia em que abri a barraca." (109/200)

### Marina — Lojinha de souvenires

> **Quem é:** adulta, dona da lojinha de souvenires, 9h–19h.  
> **Jeito de falar:** explica cada peça como se fosse de museu.  
> **Mania:** embrulha tudo com laço, até o que a pessoa vai usar na hora.  

- `npc.marina.talk.general1` **Geral 1**: "Esta jangadinha o Seu Severino levou três dias para fazer. Ele diz que foram três semanas." (90/200)
- `npc.marina.talk.general2` **Geral 2**: "Tem turista que compra o ímã de geladeira, pede embrulho de presente e dá de presente para a própria geladeira." (111/200)
- `npc.marina.talk.general3` **Geral 3**: "Eu embrulho tudo. Uma vez embrulhei um protetor solar que a pessoa ia passar ali mesmo." (87/200)
- `npc.marina.talk.general4` **Geral 4**: "A cocada da Dona Cecília é o item que mais vende e o que mais some antes de chegar ao balcão." (93/200)
- `npc.marina.talk.morning` **Manhã cedo**: "De manhã eu arrumo a vitrine, cada concha no lugar. Um dia uma concha mudou de lugar sozinha. Era um siri." (106/200)
- `npc.marina.talk.evening` **Fim de tarde / noite**: "No fim da tarde todo mundo lembra que precisa levar lembrança. É o horário dos presentes atrasados." (99/200)
- `npc.marina.talk.rain` **Dia de chuva**: "Com chuva a loja enche. Ninguém compra nada, mas a loja enche." (62/200)
- `npc.marina.talk.festival` **Dia de festa do calendário**: "Em dia de festa eu vendo bandeirinha e ensino a pendurar. A segunda parte é a mais difícil." (91/200)
- `npc.marina.talk.debt_low` **Dívida: pagou menos da metade**: "Pensei em fazer um cartão-postal com o valor da dívida. Achei que ninguém ia acreditar." (87/200)
- `npc.marina.talk.debt_high` **Dívida: pagou mais da metade**: "Passou da metade? Vou embrulhar a notícia com laço e pôr na vitrine." (68/200)
- `npc.marina.talk.epilogue` **Depois que a Dona Dilce voltou**: "Fiz uma jangadinha com a Dona Dilce em cima. O Seu Severino achou parecida. Ela achou que ficou baixinha." (105/200)

**Nota ao tradutor:**
- Nomes não se traduzem; "Seu"/"Dona" seguem o glossário. Giovana: a piada é existir só um sabor (coco).
- Zezé: "criatura" é vocativo carinhoso e neutro (serve para qualquer pessoa); traduzir por um vocativo afetuoso sem gênero, nunca por "filho/filha".
- Marina general2: a graça é a pessoa embrulhar para presente algo para a própria casa. Jangadinha e cocada são produtos que já existem na lojinha.


## f) Moradores antigos (hoje só têm a saudação)

### Dona Roberta

> **Quem é:** tecelã de redes, porta da casa dela na vila.  
> **Jeito de falar:** manso, conselho de quem já viu muita coisa.  
> **Mania:** dá nó em qualquer corda que encontra.  

- `npc.roberta.talk.general1` **Geral 1**: "Rede boa se reconhece pelo nó. Gente boa também. Por isso eu reparo nas mãos de todo mundo." (91/200)
- `npc.roberta.talk.general2` **Geral 2**: "Ontem dei nó na corda do varal, na alça da bolsa e no cordão do sapato do Padre. Ele só percebeu na missa." (106/200)
- `npc.roberta.talk.general3` **Geral 3**: "Trinta anos fazendo rede e nunca deitei numa por mais de dez minutos. Sempre acho um ponto para arrumar." (104/200)
- `npc.roberta.talk.general4` **Geral 4**: "A vila é igual rede: um fio sozinho não segura ninguém." (55/200)
- `npc.roberta.talk.morning` **Manhã cedo**: "De manhã cedo a linha está mais firme. Depois do almoço ela fica preguiçosa, igual a gente." (91/200)
- `npc.roberta.talk.evening` **Fim de tarde / noite**: "Fim de tarde eu sento na porta e vejo quem passa. A vila inteira passa, se a gente esperar." (91/200)
- `npc.roberta.talk.rain` **Dia de chuva**: "Chuva é bom para tecer. A mão fica ocupada e a cabeça vai longe." (64/200)
- `npc.roberta.talk.festival` **Dia de festa do calendário**: "Em dia de festa eu penduro as redes coloridas na porta. Quem quiser descansar da festa, pode." (93/200)
- `npc.roberta.talk.debt_low` **Dívida: pagou menos da metade**: "A Dona Dilce nunca deixou ninguém desta vila na mão. Agora é a vila que não vai deixar você." (92/200)
- `npc.roberta.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade, meu bem. Já dá para ver o outro lado da rede." (61/200)
- `npc.roberta.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce passa aqui toda tarde para conferir os meus nós. Achou um torto em trinta anos. Um!" (96/200)

### Alana

> **Quem é:** neta do último faroleiro, perto da igreja e no farol.  
> **Jeito de falar:** sonhadora, mas com os pés no chão.  
> **Mania:** tenta prever o tempo pelas nuvens, como o avô, e quase sempre erra.  

- `npc.alana.talk.general1` **Geral 1**: "Meu avô sabia o tempo pelas nuvens. Eu tento. Ontem previ sol e choveu em mim." (78/200)
- `npc.alana.talk.general2` **Geral 2**: "Do alto do farol dá para ver a vila inteira. Dá para ver até quem devia estar trabalhando e não está." (101/200)
- `npc.alana.talk.general3` **Geral 3**: "Tenho o caderno do meu avô com o horário de cada barco que passou. O último é de muitos anos atrás." (99/200)
- `npc.alana.talk.general4` **Geral 4**: "Gosto de ver o mar quando ninguém está olhando. Ele parece mais à vontade." (74/200)
- `npc.alana.talk.morning` **Manhã cedo**: "De manhã cedo o farol faz uma sombra comprida até a praia. Parece que ele está se espreguiçando." (96/200)
- `npc.alana.talk.evening` **Fim de tarde / noite**: "No fim da tarde eu olho para o farol. Meu avô dizia que é a hora em que ele acorda." (83/200)
- `npc.alana.talk.rain` **Dia de chuva**: "Chuva com vento sul. Meu avô mandaria recolher os barcos. Eu mando recolher as toalhas." (87/200)
- `npc.alana.talk.festival` **Dia de festa do calendário**: "Dia de festa! Eu adoro ver as bandeirinhas lá de cima. A vila fica parecendo um presente." (89/200)
- `npc.alana.talk.debt_low` **Dívida: pagou menos da metade**: "Um milhão é muito. Mas o farol também estava muito apagado, e olha só. Uma coisa de cada vez." (93/200)
- `npc.alana.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade! Dá para ver daqui de cima: o quiosque está mais iluminado. Juro." (80/200)
- `npc.alana.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce subiu a escada do farol sem parar nenhuma vez. Eu parei três. Ela me proibiu de contar." (100/200)

### Seu Severino

> **Quem é:** pescador, perto do píer.  
> **Jeito de falar:** orgulhoso, chora e nega.  
> **Mania:** dizer que foi ele quem ensinou ou construiu tudo que deu certo na vila. Rival amistoso do Seu Bené.  

- `npc.severino.talk.general1` **Geral 1**: "Fui eu que ensinei metade da vila a pescar. A outra metade aprendeu errado com o Bené." (86/200)
- `npc.severino.talk.general2` **Geral 2**: "O Bené diz que pescou um peixe do tamanho da jangada. Eu estava lá. Era do tamanho do chinelo dele." (99/200)
- `npc.severino.talk.general3` **Geral 3**: "Quem ensinou o Kauã a ficar em pé na prancha fui eu. Ele não lembra. Eu também não, mas fui eu." (95/200)
- `npc.severino.talk.general4` **Geral 4**: "Pescador de verdade não fala do peixe que pegou. Fala do que escapou. Esse é sempre maior." (90/200)
- `npc.severino.talk.morning` **Manhã cedo**: "Às cinco eu já estou no píer. O mar acorda comigo. Às vezes eu acordo ele." (74/200)
- `npc.severino.talk.evening` **Fim de tarde / noite**: "Fim de tarde é hora de sentar no píer e não fazer nada. Eu levo isso muito a sério." (83/200)
- `npc.severino.talk.rain` **Dia de chuva**: "Chuva? Não estou chorando. É chuva mesmo. Desta vez é." (54/200)
- `npc.severino.talk.festival` **Dia de festa do calendário**: "Em dia de festa eu visto a camisa boa. A camisa boa é a mesma, só que passada." (78/200)
- `npc.severino.talk.debt_low` **Dívida: pagou menos da metade**: "Dívida grande se paga igual se puxa rede cheia: devagar e sem reclamar em voz alta." (83/200)
- `npc.severino.talk.debt_high` **Dívida: pagou mais da metade**: "Passou da metade! Vou contar para todo mundo que fui eu que te ensinei a fazer conta." (85/200)
- `npc.severino.talk.epilogue` **Depois que a Dona Dilce voltou**: "Com a Dona Dilce de volta, eu pesco o dobro. Ela come o dobro também, então empata." (83/200)

### Padre Robson

> **Quem é:** pároco, perto da igreja; missa às 7h e às 17h30.  
> **Jeito de falar:** bem-humorado, sermão curto.  
> **Mania:** todo assunto termina em almoço.  

- `npc.robson.talk.general1` **Geral 1**: "Sermão bom é sermão curto. O almoço também é obra de Deus e não pode esfriar." (77/200)
- `npc.robson.talk.general2` **Geral 2**: "O sino às vezes toca sozinho com o vento. Eu digo que é um recado. Os pescadores dizem que é a corda frouxa." (108/200)
- `npc.robson.talk.general3` **Geral 3**: "Abençoei o quiosque, o píer e o barco do Severino. O barco do Severino, duas vezes, por precaução." (98/200)
- `npc.robson.talk.general4` **Geral 4**: "A Dona Cecília manda pastel para a paróquia toda sexta. Eu rezo por ela toda sexta. Troca justa." (96/200)
- `npc.robson.talk.morning` **Manhã cedo**: "Missa das sete: eu, quatro senhoras e um pescador dormindo no último banco. Comunidade fiel." (92/200)
- `npc.robson.talk.evening` **Fim de tarde / noite**: "Depois da missa da tarde eu fico olhando o pôr do sol. É o único sermão melhor que o meu." (89/200)
- `npc.robson.talk.rain` **Dia de chuva**: "Com chuva a igreja enche. Muita fé e pouco guarda-chuva." (56/200)
- `npc.robson.talk.festival` **Dia de festa do calendário**: "Em dia de festa eu abençoo a comida. De bem perto, para ter certeza." (68/200)
- `npc.robson.talk.debt_low` **Dívida: pagou menos da metade**: "Paciência também é virtude, meu bem. E coco gelado ajuda muito a paciência." (75/200)
- `npc.robson.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade paga. Vou acender uma vela. Pequena, que vela também custa." (74/200)
- `npc.robson.talk.epilogue` **Depois que a Dona Dilce voltou**: "Desde que a Dona Dilce voltou, ninguém mais dorme na missa das sete. Ela cutuca." (80/200)

### Dona Cecília

> **Quem é:** cozinheira da vila, rua principal.  
> **Jeito de falar:** receita no meio da frase.  
> **Mania:** prova tudo e acrescenta "uma pitadinha".  

- `npc.cecilia.talk.general1` **Geral 1**: "Tempero bom não se mede. Se dá para medir, já não é tempero, é conta." (69/200)
- `npc.cecilia.talk.general2` **Geral 2**: "Provei o caldo do restaurante do hotel. Faltava uma pitadinha. Eu levei a pitadinha no bolso." (93/200)
- `npc.cecilia.talk.general3` **Geral 3**: "A receita da cocada é da minha avó. O segredo também. Morre comigo e com a panela." (82/200)
- `npc.cecilia.talk.general4` **Geral 4**: "Quem cozinha com pressa serve com desculpa." (43/200)
- `npc.cecilia.talk.morning` **Manhã cedo**: "De manhã cedo eu já estou com a panela no fogo. O cheiro acorda a vila antes do galo." (85/200)
- `npc.cecilia.talk.evening` **Fim de tarde / noite**: "Fim de tarde é hora de café com bolo. Não é lei, mas devia ser." (63/200)
- `npc.cecilia.talk.rain` **Dia de chuva**: "Dia de chuva pede caldo quente. Eu tenho um caldo para cada tipo de chuva." (74/200)
- `npc.cecilia.talk.festival` **Dia de festa do calendário**: "Em dia de festa eu cozinho para a vila inteira. Ninguém pede; eu já sei que vão pedir." (86/200)
- `npc.cecilia.talk.debt_low` **Dívida: pagou menos da metade**: "Um milhão se paga igual se faz cocada: mexendo sem parar, até dar o ponto." (74/200)
- `npc.cecilia.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade! Isso merece um bolo. Inteiro, não aquele pela metade do gerente." (80/200)
- `npc.cecilia.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce entrou na minha cozinha e mudou o sal de lugar. Trinta anos de amizade, meu bem. Foi por pouco." (108/200)

### Seu Tibúrcio

> **Quem é:** o velho do morro, banco do cume (e, depois do capítulo `descanso`, o quiosque no fim da tarde).  
> **Jeito de falar:** dramático, fala do mar como de uma pessoa temperamental.  
> **Mania:** conversar com o mar e traduzir o que ele "disse".  

- `npc.tiburcio.talk.general1` **Geral 1**: "O mar está de bom humor hoje. Dá para ver pela espuma. Espuma enrolada é mar sorrindo." (86/200)
- `npc.tiburcio.talk.general2` **Geral 2**: "Trinta anos aqui em cima e nunca vi a Onda. Isso prova que a oferenda funciona!" (79/200)
- `npc.tiburcio.talk.general3` **Geral 3**: "O mar me disse que gostou do coco de ontem. Disse com uma ondinha. Eu entendo ondinha." (86/200)
- `npc.tiburcio.talk.general4` **Geral 4**: "Não é superstição, é educação. Ninguém chega na casa dos outros sem levar nada." (79/200)
- `npc.tiburcio.talk.morning` **Manhã cedo**: "Bom dia! O mar acordou meio rabugento. Ainda não recebeu a oferenda dele." (73/200)
- `npc.tiburcio.talk.evening` **Fim de tarde / noite**: "Fim de tarde o mar fica calmo e eu fico com fome. Somos parecidos." (66/200)
- `npc.tiburcio.talk.rain` **Dia de chuva**: "Chuva é o mar visitando a terra. Tem que receber bem, senão ele se ofende." (74/200)
- `npc.tiburcio.talk.festival` **Dia de festa do calendário**: "Festa lá embaixo? O mar ouve a música daqui. Ele gosta, mas não admite." (71/200)
- `npc.tiburcio.talk.debt_low` **Dívida: pagou menos da metade**: "Dívida e mar são parecidos: não adianta brigar, tem que levar um pouco todo dia." (80/200)
- `npc.tiburcio.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade? O mar está orgulhoso. Eu sei porque ele está mais azul." (71/200)
- `npc.tiburcio.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce subiu comigo com a oferenda hoje. O mar ficou tão calmo que parecia lago. Ele tem preferências." (108/200)

**Nota ao tradutor:**
- "Trinta anos" é fixo para Roberta, Tibúrcio e a amizade Cecília–Dilce; "quarenta" é da Dona Dilce no quiosque. Não trocar.
- Severino debt_high usa "te ensinei" (informal, neutro em português): em línguas com tratamento formal/informal, ele trata o jogador com intimidade.
- Cecília "minha avó" é a avó DELA. Tibúrcio: "a Onda" com maiúscula é o tsunami do jogo; o mar é sempre "ele", com vontades.
- Alana "vento sul": se a língua tiver nome de vento diferente, manter só "vento do sul". "mudou o sal de lugar" (Cecília) = mexeu na cozinha dela, quase briga.


# Parte 2 — PROPOSTA de NPCs novos (o dono escolhe)

**Isto é proposta, não decisão.** Os 8 corpos novos já estão prometidos aos personagens da Parte 1 (Tuanny, Arnaldo, Bené, Dilce e os 4–5 vendedores, conforme a conta do diretor). Para qualquer um destes seis entrar, o dono precisa trocar por alguém da Parte 1 ou liberar corpo novo. Ordem sugerida de prioridade: 1 Seu Jurandir, 2 Nazaré, 3 Seu Ivo, 4 Dandara, 5 Dona Glória, 6 Seu Otávio (este só no jogo completo).

**Gerente do banco: não proposto.** A piada funciona porque ele nunca aparece: é o homem paciente que "gosta de coco", "liga sem tossir" e "reconhece a Dona Dilce pelo jeito de bater na porta". Com corpo e falas, vira explicação e cada jogador imagina menos. Ficou de fora. Reservas, se faltar alguém: músico da praça (rende a "serenata desafinada") e vendedor ambulante de praia (rende "pedido impossível").


## 1. Seu Jurandir — carteiro do barco do correio
| campo | proposta |
|---|---|
| Papel | carteiro: o correio chega de barco às terças e sextas; ele entrega na vila e no hotel |
| Onde e quando | píer 8h–10h (dias de barco); praça e rua principal 10h–15h; nos outros dias, banco da praça |
| Aparência | homem, ~60 anos, uniforme de carteiro (camisa de manga curta com o emblema do correio, calça social), bolsa de couro a tiracolo; sem boné |
| Mania | lê o remetente em voz alta e adivinha a notícia pelo peso do envelope |
| Relação | é quem entrega as cartas da Dona Dilce; conhece a letra dela e sabe se ela está contente. Pode ser quem traz a carta de 100 % (hoje está com o Seu Severino no roteiro da festa: decisão do diretor) |
| Cenas onde rende | fofoca em cadeia; mala que abre; freguês do fiado ("põe na conta da Dona Dilce"); noivos atrasados |

- `npc.jurandir.talk.general1` **Geral 1**: "Carta da capital, conta de luz e um pacote que faz barulho. Eu não abro. Mas eu escuto." (87/200)
- `npc.jurandir.talk.general2` **Geral 2**: "Pelo envelope eu sei se a notícia é boa. Envelope pesado é convite. Envelope fino é cobrança." (93/200)
- `npc.jurandir.talk.general3` **Geral 3**: "Já entreguei pedido de casamento nesta ilha e levei a resposta de volta. Era sim, mas demorou três barcos." (106/200)
- `npc.jurandir.talk.general4` **Geral 4**: "Correio aqui chega de barco, terça e sexta. Se o mar estiver bravo, a notícia espera." (85/200)
- `npc.jurandir.talk.morning` **Manhã cedo**: "O barco do correio chega cedo. Notícia boa tem que ser entregue antes de o café esfriar." (88/200)
- `npc.jurandir.talk.evening` **Fim de tarde / noite**: "No fim da tarde eu já entreguei tudo e sei de tudo. Não conto nada. Só se perguntarem." (86/200)
- `npc.jurandir.talk.rain` **Dia de chuva**: "Com chuva eu embrulho as cartas num plástico e a mim em outro." (62/200)
- `npc.jurandir.talk.festival` **Dia de festa do calendário**: "Em dia de festa todo mundo manda cartão. Entrego cartão até para quem mora na casa ao lado." (91/200)
- `npc.jurandir.talk.debt_low` **Dívida: pagou menos da metade**: "Eu entrego as cartas da Dona Dilce. A letra dela inclina para a frente, igual quem tem pressa de chegar." (104/200)
- `npc.jurandir.talk.debt_high` **Dívida: pagou mais da metade**: "As cartas da Dona Dilce estão mais grossas. Ela escreve mais quando está feliz." (79/200)
- `npc.jurandir.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce voltou e eu perdi a minha melhor remetente. Agora ela me para na praça e conta tudo de boca." (105/200)

**Nota ao tradutor:**
- "remetente" = sender. "Envelope fino é cobrança" = bill; a piada é universal.
- Liga o jogador às cartas da avó: é o rosto do "correio" das cartas dos marcos.


## 2. Nazaré — pescadora
| campo | proposta |
|---|---|
| Papel | pescadora profissional; pesca mais que os dois velhos juntos |
| Onde e quando | píer 5h–11h; beira da praia consertando rede 15h–18h |
| Aparência | mulher, ~45 anos, roupa de pesca: camisa de manga comprida contra o sol, calça arregaçada, bota de borracha, balança de mão presa ao cinto |
| Mania | pesa tudo: peixe, coco, mala de turista, a história do Bené |
| Relação | árbitra de Seu Bené e Seu Severino; a única que tem a balança para provar quem mente |
| Cenas onde rende | Bené e Severino discutindo o tamanho do peixe; siri no balcão; coco teimoso (abre com um golpe de facão); golfinhos; maré na toalha |

- `npc.nazare.talk.general1` **Geral 1**: "Pesei o peixe do Bené. Novecentos gramas. Ele disse que a balança encolheu com o sal." (85/200)
- `npc.nazare.talk.general2` **Geral 2**: "Eu pesco mais que o Severino e o Bené juntos. Não conto vantagem: a balança conta por mim." (90/200)
- `npc.nazare.talk.general3` **Geral 3**: "Peixe se limpa na hora. História de peixe também, senão estraga." (64/200)
- `npc.nazare.talk.general4` **Geral 4**: "Abro coco com um golpe de facão. Quem precisa de dois não está com fome." (72/200)
- `npc.nazare.talk.morning` **Manhã cedo**: "Às quatro eu já estou no mar. Às oito eu volto, e os dois ainda estão discutindo no píer." (89/200)
- `npc.nazare.talk.evening` **Fim de tarde / noite**: "Fim de tarde é hora de consertar rede e ouvir mentira de pescador. Faço as duas coisas juntas." (94/200)
- `npc.nazare.talk.rain` **Dia de chuva**: "Chuva fina é peixe na rede. Chuva grossa é peixe no café da manhã de outra pessoa." (82/200)
- `npc.nazare.talk.festival` **Dia de festa do calendário**: "Em dia de festa eu levo peixe para a Dona Cecília. Ela faz o prato, eu fico com a fama." (87/200)
- `npc.nazare.talk.debt_low` **Dívida: pagou menos da metade**: "Dívida se pesa igual peixe: sem enganar a balança. Um milhão é um milhão, não adianta abrir os braços." (102/200)
- `npc.nazare.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade? Pelas minhas contas, agora falta menos do que já foi. É assim que se pesa uma boa notícia." (106/200)
- `npc.nazare.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce me pediu para pesar o peixe que o Bené contou para ela. Pesei. Ele ficou um mês sem falar comigo." (110/200)

**Nota ao tradutor:**
- "não adianta abrir os braços" responde à mania do Bené de medir peixe com os braços.
- Nazaré é seca e prática: nunca exclamativa.


## 3. Seu Ivo — fotógrafo lambe-lambe
| campo | proposta |
|---|---|
| Papel | fotógrafo de rua com câmera antiga de caixão; faz retrato na praça e no pôr do sol |
| Onde e quando | praça 9h–17h; mirante da praia no pôr do sol |
| Aparência | homem, ~75 anos, camisa social clara de manga curta, colete de fotógrafo cheio de bolsos, câmera de madeira em tripé com pano preto |
| Mania | manda todo mundo "falar xis" e fotografa quem olha o pôr do sol, não o sol |
| Relação | tem fotos antigas do píer antes do vendaval e da Dona Dilce jovem atrás do balcão, ao lado de uma pilha de papéis do banco: pista visual da dívida antes das cartas |
| Cenas onde rende | fotógrafos do pôr do sol; arco-íris; gaivota no letreiro; noivos atrasados; castelo de areia; bandeirinhas ao vento |

- `npc.ivo.talk.general1` **Geral 1**: "Minha câmera tem sessenta anos e nunca tremeu. Quem treme é o cliente." (70/200)
- `npc.ivo.talk.general2` **Geral 2**: "Fale xis! Não precisa gritar. A foto não tem som." (49/200)
- `npc.ivo.talk.general3` **Geral 3**: "Tenho uma caixa de fotos do píer antes do vendaval. Quem quiser ver, traz um café." (82/200)
- `npc.ivo.talk.general4` **Geral 4**: "O celular tira mil fotos e ninguém lembra de nenhuma. Eu tiro uma e a família pendura na sala por cinquenta anos." (113/200)
- `npc.ivo.talk.morning` **Manhã cedo**: "Luz de manhã é honesta: mostra tudo. Por isso ninguém quer foto de manhã." (73/200)
- `npc.ivo.talk.evening` **Fim de tarde / noite**: "No pôr do sol todo mundo fotografa o sol. Eu fotografo quem está olhando para ele." (82/200)
- `npc.ivo.talk.rain` **Dia de chuva**: "Com chuva eu fecho o pano preto e espero. Fotografia é paciência com um pouco de sorte." (87/200)
- `npc.ivo.talk.festival` **Dia de festa do calendário**: "Em dia de festa eu fotografo a vila inteira na escadaria da igreja. Sempre tem um que pisca." (92/200)
- `npc.ivo.talk.debt_low` **Dívida: pagou menos da metade**: "Tenho uma foto da Dona Dilce jovem atrás do balcão, com uma pilha de papéis do banco ao lado. Nunca entendi aqueles papéis." (123/200)
- `npc.ivo.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade paga? Vou fazer um retrato seu para a parede do quiosque. Do lado do retrato dela." (97/200)
- `npc.ivo.talk.epilogue` **Depois que a Dona Dilce voltou**: "Fotografei a Dona Dilce no mesmo lugar da foto de quarenta anos atrás. O balcão é o mesmo. O sorriso também." (108/200)

**Nota ao tradutor:**
- "lambe-lambe" = fotógrafo de rua com câmera de caixão (street photographer with a box camera); não traduzir o termo, descrever.
- "Fale xis": usar a palavra que a língua usa para sorrir na foto (cheese, patata, Käsekuchen...); a piada é "a foto não tem som".
- debt_low é PISTA da fiança: não explicar mais do que o texto diz.


## 4. Dandara — salva-vidas
| campo | proposta |
|---|---|
| Papel | salva-vidas da praia |
| Onde e quando | cadeira alta do posto na praia 8h–18h; à noite, fora do mapa |
| Aparência | mulher, ~30 anos, uniforme de salva-vidas (regata e bermuda vermelhas), apito no pescoço, boia de resgate laranja |
| Mania | apita para tudo: banhista, gaivota, nuvem |
| Relação | levou a Onda do Seu Tibúrcio a sério demais: sobe o morro toda semana para conferir o cesto |
| Cenas onde rende | turista torrado; dormiu no sol; maré na toalha; bola de vôlei perdida; golfinhos; bombinha na piscina; guarda-sol que fecha sozinho |

- `npc.dandara.talk.general1` **Geral 1**: "Apitei para uma gaivota hoje. Ela estava longe demais da praia. Não voltou, mas ouviu." (86/200)
- `npc.dandara.talk.general2` **Geral 2**: "Protetor solar de hora em hora. Repito isso tanto que já sonho com frasco." (74/200)
- `npc.dandara.talk.general3` **Geral 3**: "O Seu Tibúrcio me explicou a Onda. Agora subo o morro toda semana para conferir o cesto. Por segurança." (103/200)
- `npc.dandara.talk.general4` **Geral 4**: "Bandeira vermelha: não entre. Amarela: cuidado. Verde: hoje eu estou de bom humor." (82/200)
- `npc.dandara.talk.morning` **Manhã cedo**: "Cedo eu conto os banhistas: zero. É o meu horário favorito." (59/200)
- `npc.dandara.talk.evening` **Fim de tarde / noite**: "No fim da tarde todo mundo quer o último mergulho. Eu deixo, com o apito na boca." (81/200)
- `npc.dandara.talk.rain` **Dia de chuva**: "Chuva com raio: todo mundo fora da água. Chuva sem raio: todo mundo fora também. Prefiro assim." (95/200)
- `npc.dandara.talk.festival` **Dia de festa do calendário**: "Em dia de festa tem gente que entra no mar fantasiada. Já resgatei um pirata e meio abacaxi." (92/200)
- `npc.dandara.talk.debt_low` **Dívida: pagou menos da metade**: "Dívida é igual correnteza: não nade contra. Nade de lado, devagar, até sair dela." (81/200)
- `npc.dandara.talk.debt_high` **Dívida: pagou mais da metade**: "Passou da metade? Agora você está na parte rasa. Mas cuidado: na parte rasa também tem siri." (92/200)
- `npc.dandara.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce entrou no mar sem protetor. Apitei. Ela apitou de volta. Eu não sabia que ela tinha apito." (103/200)

**Nota ao tradutor:**
- "nade de lado" é o conselho real para sair de correnteza (swim parallel to the shore): manter correto.
- "meio abacaxi" = alguém fantasiado de metade de um abacaxi; imagem, não trocadilho.


## 5. Dona Glória — dona da pousada vizinha (concorrente)
| campo | proposta |
|---|---|
| Papel | dona da Pousada Sol Nascente, a concorrente da pousada do jogador |
| Onde e quando | varanda da pousada dela 7h–19h; passa no quiosque das 15h às 16h "só para olhar" (precisa de uma casa existente como pousada dela) |
| Aparência | mulher, ~70 anos, roupa de dona de pousada: blusa social, saia, crachá "Gerência" e colar de pérolas |
| Mania | anota os preços dos outros num bloquinho |
| Relação | rival de quarenta anos da Dona Dilce (no balcão e no bingo); dá a entender que também deve algo à Dona Dilce, sem nunca admitir |
| Cenas onde rende | casal que não decide; pedido impossível; fofoca em cadeia; prefeita inaugura qualquer coisa; sommelier de água de coco |

- `npc.gloria.talk.general1` **Geral 1**: "Na minha pousada o café da manhã tem doze tipos de bolo. Treze, se contar o de ontem." (85/200)
- `npc.gloria.talk.general2` **Geral 2**: "Vim só olhar o seu cardápio. Não estou copiando. Estou comparando de perto." (75/200)
- `npc.gloria.talk.general3` **Geral 3**: "O seu preço do coco é bom. Bom demais. Vou ter que baixar o meu, e eu odeio baixar coisas." (90/200)
- `npc.gloria.talk.general4` **Geral 4**: "A Dona Dilce e eu disputamos o mesmo turista por quarenta anos. Ele envelheceu sem escolher." (92/200)
- `npc.gloria.talk.morning` **Manhã cedo**: "Às seis eu já servi o café de todos os meus hóspedes. Os seus ainda estão dormindo, aposto." (91/200)
- `npc.gloria.talk.evening` **Fim de tarde / noite**: "No fim da tarde eu passo aqui para ver quem está mais cheio. Hoje empatamos. Amanhã eu ganho." (93/200)
- `npc.gloria.talk.rain` **Dia de chuva**: "Chuva é ótimo para pousada: ninguém vai embora. Nem os que querem." (66/200)
- `npc.gloria.talk.festival` **Dia de festa do calendário**: "Em dia de festa eu penduro mais bandeirinhas que você. Contei as suas ontem." (76/200)
- `npc.gloria.talk.debt_low` **Dívida: pagou menos da metade**: "Eu nunca devi um centavo a ninguém. Quer dizer, a ninguém que cobrasse." (71/200)
- `npc.gloria.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade? A Dona Dilce vai ficar insuportável de orgulho. Mande lembranças. Fingidas, mas mande." (102/200)
- `npc.gloria.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce voltou e veio direto aqui me mostrar o quarto com vista dela. Pela janela. Da minha pousada." (105/200)

**Nota ao tradutor:**
- Ela diz "Dona Dilce" por regra do jogo, mas com ironia de rival; se a língua permitir um tom levemente formal-irônico, melhor.
- debt_low é uma confissão escondida (ela também foi ajudada): traduzir com a mesma ambiguidade.
- "Pousada Sol Nascente" é nome próprio de estabelecimento: pode ser traduzido como nome de hotel ("Sunrise Inn") se o glossário traduzir nomes de lugares; senão manter.


## 6. Seu Otávio — gerente do Grand Hotel (só jogo completo)
| campo | proposta |
|---|---|
| Papel | gerente-geral do Grand Hotel Maré Alta |
| Onde e quando | lobby do hotel 7h–21h; ronda na piscina 15h |
| Aparência | homem, ~50 anos, terno escuro do hotel com crachá, gravata e lenço no bolso |
| Mania | chama todo problema de "oportunidade de experiência" e sorri para todo hóspede, com medo de ser o crítico disfarçado |
| Relação | vive com medo do Seu Arnaldo: antes do capítulo `critico` desconfia de todos; depois, oferece sobremesa a ele a cada meia hora |
| Cenas onde rende | elevador indeciso; hóspede de roupão; VIP disfarçado; noivos atrasados; mala que abre; campeão de sinuca; bombinha na piscina |

- `npc.otavio.talk.general1` **Geral 1**: "Aqui não temos problemas, temos oportunidades de experiência. O elevador hoje teve três oportunidades." (102/200)
- `npc.otavio.talk.general2` **Geral 2**: "Qualquer hóspede pode ser o crítico disfarçado. Eu sorrio para todos. Estou com cãibra no rosto." (96/200)
- `npc.otavio.talk.general3` **Geral 3**: "Um hóspede desceu de roupão para o café. Chamei de tendência. Agora são onze." (77/200)
- `npc.otavio.talk.general4` **Geral 4**: "Experiência premium é quando o coco chega gelado e o hóspede acha que a ideia foi dele." (87/200)
- `npc.otavio.talk.morning` **Manhã cedo**: "Às seis eu confiro o lobby, as flores e o meu sorriso. O sorriso é o que demora mais." (85/200)
- `npc.otavio.talk.evening` **Fim de tarde / noite**: "À noite eu confiro se ninguém está perdido nos corredores. Ontem eram dois, juntos, discutindo direção." (103/200)
- `npc.otavio.talk.rain` **Dia de chuva**: "Chuva? No Grand Hotel chamamos de clima de spa." (47/200)
- `npc.otavio.talk.festival` **Dia de festa do calendário**: "Dia de festa na vila: metade dos hóspedes sai, e a outra metade pede para a festa vir até o hotel." (98/200)
- `npc.otavio.talk.debt_low` **Dívida: pagou menos da metade**: "O hotel paga boa parte da dívida, sabia? Não digo isso aos hóspedes. Digo que é sustentabilidade." (97/200)
- `npc.otavio.talk.debt_high` **Dívida: pagou mais da metade**: "Mais da metade paga. Vou mandar flores para o banco. Com o cartão do hotel, por favor: é publicidade." (101/200)
- `npc.otavio.talk.epilogue` **Depois que a Dona Dilce voltou**: "A Dona Dilce está no quarto com vista e já pediu três mudanças. Todas boas. Vou aplicar no hotel inteiro." (105/200)

**Nota ao tradutor:**
- Fala de hotelaria corporativa ("experiência premium", "oportunidade"): usar o jargão equivalente da língua; é a graça.
- general2 só faz sentido antes do capítulo `critico`; depois, sugiro trocar pela variante: "Agora sei quem é o crítico. Continuo sorrindo para todos. Hábito." (`npc.otavio.talk.post_reveal1`).

- `npc.otavio.talk.post_reveal1` **Geral extra, depois do capítulo `critico` (substitui general2)**: "Agora sei quem é o crítico. Continuo sorrindo para todos. Virou hábito." (71/200)

# Lista de ids

Total: **227 falas** — Parte 1: 160; Parte 2 (proposta): 67. Todas novas.

| id | caracteres |
|---|---|
| `npc.tuanny.talk.general1` | 101 |
| `npc.tuanny.talk.general2` | 96 |
| `npc.tuanny.talk.general3` | 79 |
| `npc.tuanny.talk.general4` | 92 |
| `npc.tuanny.talk.morning` | 104 |
| `npc.tuanny.talk.evening` | 86 |
| `npc.tuanny.talk.rain` | 88 |
| `npc.tuanny.talk.festival` | 79 |
| `npc.tuanny.talk.debt_low` | 106 |
| `npc.tuanny.talk.debt_high` | 78 |
| `npc.tuanny.talk.epilogue` | 115 |
| `npc.arnaldo.talk.general1` | 91 |
| `npc.arnaldo.talk.general2` | 104 |
| `npc.arnaldo.talk.general3` | 81 |
| `npc.arnaldo.talk.general4` | 70 |
| `npc.arnaldo.talk.morning` | 82 |
| `npc.arnaldo.talk.evening` | 69 |
| `npc.arnaldo.talk.rain` | 65 |
| `npc.arnaldo.talk.festival` | 95 |
| `npc.arnaldo.talk.debt_low` | 104 |
| `npc.arnaldo.talk.debt_high` | 50 |
| `npc.arnaldo.talk.epilogue` | 107 |
| `npc.arnaldo.talk.post_reveal1` | 102 |
| `npc.arnaldo.talk.post_reveal2` | 112 |
| `npc.bene.talk.general1` | 90 |
| `npc.bene.talk.general2` | 97 |
| `npc.bene.talk.general3` | 81 |
| `npc.bene.talk.general4` | 96 |
| `npc.bene.talk.morning` | 85 |
| `npc.bene.talk.evening` | 74 |
| `npc.bene.talk.rain` | 84 |
| `npc.bene.talk.festival` | 89 |
| `npc.bene.talk.debt_low` | 118 |
| `npc.bene.talk.debt_high` | 76 |
| `npc.bene.talk.epilogue` | 89 |
| `npc.dilce.talk.morning` | 107 |
| `npc.dilce.talk.evening` | 103 |
| `npc.dilce.talk.rain` | 86 |
| `npc.dilce.talk.festival` | 80 |
| `npc.giovana.talk.general1` | 74 |
| `npc.giovana.talk.general2` | 99 |
| `npc.giovana.talk.general3` | 92 |
| `npc.giovana.talk.general4` | 54 |
| `npc.giovana.talk.morning` | 79 |
| `npc.giovana.talk.evening` | 90 |
| `npc.giovana.talk.rain` | 89 |
| `npc.giovana.talk.festival` | 90 |
| `npc.giovana.talk.debt_low` | 90 |
| `npc.giovana.talk.debt_high` | 83 |
| `npc.giovana.talk.epilogue` | 91 |
| `npc.valdir.talk.general1` | 86 |
| `npc.valdir.talk.general2` | 99 |
| `npc.valdir.talk.general3` | 96 |
| `npc.valdir.talk.general4` | 104 |
| `npc.valdir.talk.morning` | 93 |
| `npc.valdir.talk.evening` | 91 |
| `npc.valdir.talk.rain` | 70 |
| `npc.valdir.talk.festival` | 105 |
| `npc.valdir.talk.debt_low` | 76 |
| `npc.valdir.talk.debt_high` | 73 |
| `npc.valdir.talk.epilogue` | 98 |
| `npc.kaua.talk.general1` | 87 |
| `npc.kaua.talk.general2` | 102 |
| `npc.kaua.talk.general3` | 80 |
| `npc.kaua.talk.general4` | 91 |
| `npc.kaua.talk.morning` | 91 |
| `npc.kaua.talk.evening` | 74 |
| `npc.kaua.talk.rain` | 78 |
| `npc.kaua.talk.festival` | 90 |
| `npc.kaua.talk.debt_low` | 90 |
| `npc.kaua.talk.debt_high` | 68 |
| `npc.kaua.talk.epilogue` | 112 |
| `npc.zeze.talk.general1` | 89 |
| `npc.zeze.talk.general2` | 89 |
| `npc.zeze.talk.general3` | 75 |
| `npc.zeze.talk.general4` | 95 |
| `npc.zeze.talk.morning` | 89 |
| `npc.zeze.talk.evening` | 80 |
| `npc.zeze.talk.rain` | 80 |
| `npc.zeze.talk.festival` | 79 |
| `npc.zeze.talk.debt_low` | 95 |
| `npc.zeze.talk.debt_high` | 98 |
| `npc.zeze.talk.epilogue` | 109 |
| `npc.marina.talk.general1` | 90 |
| `npc.marina.talk.general2` | 111 |
| `npc.marina.talk.general3` | 87 |
| `npc.marina.talk.general4` | 93 |
| `npc.marina.talk.morning` | 106 |
| `npc.marina.talk.evening` | 99 |
| `npc.marina.talk.rain` | 62 |
| `npc.marina.talk.festival` | 91 |
| `npc.marina.talk.debt_low` | 87 |
| `npc.marina.talk.debt_high` | 68 |
| `npc.marina.talk.epilogue` | 105 |
| `npc.roberta.talk.general1` | 91 |
| `npc.roberta.talk.general2` | 106 |
| `npc.roberta.talk.general3` | 104 |
| `npc.roberta.talk.general4` | 55 |
| `npc.roberta.talk.morning` | 91 |
| `npc.roberta.talk.evening` | 91 |
| `npc.roberta.talk.rain` | 64 |
| `npc.roberta.talk.festival` | 93 |
| `npc.roberta.talk.debt_low` | 92 |
| `npc.roberta.talk.debt_high` | 61 |
| `npc.roberta.talk.epilogue` | 96 |
| `npc.alana.talk.general1` | 78 |
| `npc.alana.talk.general2` | 101 |
| `npc.alana.talk.general3` | 99 |
| `npc.alana.talk.general4` | 74 |
| `npc.alana.talk.morning` | 96 |
| `npc.alana.talk.evening` | 83 |
| `npc.alana.talk.rain` | 87 |
| `npc.alana.talk.festival` | 89 |
| `npc.alana.talk.debt_low` | 93 |
| `npc.alana.talk.debt_high` | 80 |
| `npc.alana.talk.epilogue` | 100 |
| `npc.severino.talk.general1` | 86 |
| `npc.severino.talk.general2` | 99 |
| `npc.severino.talk.general3` | 95 |
| `npc.severino.talk.general4` | 90 |
| `npc.severino.talk.morning` | 74 |
| `npc.severino.talk.evening` | 83 |
| `npc.severino.talk.rain` | 54 |
| `npc.severino.talk.festival` | 78 |
| `npc.severino.talk.debt_low` | 83 |
| `npc.severino.talk.debt_high` | 85 |
| `npc.severino.talk.epilogue` | 83 |
| `npc.robson.talk.general1` | 77 |
| `npc.robson.talk.general2` | 108 |
| `npc.robson.talk.general3` | 98 |
| `npc.robson.talk.general4` | 96 |
| `npc.robson.talk.morning` | 92 |
| `npc.robson.talk.evening` | 89 |
| `npc.robson.talk.rain` | 56 |
| `npc.robson.talk.festival` | 68 |
| `npc.robson.talk.debt_low` | 75 |
| `npc.robson.talk.debt_high` | 74 |
| `npc.robson.talk.epilogue` | 80 |
| `npc.cecilia.talk.general1` | 69 |
| `npc.cecilia.talk.general2` | 93 |
| `npc.cecilia.talk.general3` | 82 |
| `npc.cecilia.talk.general4` | 43 |
| `npc.cecilia.talk.morning` | 85 |
| `npc.cecilia.talk.evening` | 63 |
| `npc.cecilia.talk.rain` | 74 |
| `npc.cecilia.talk.festival` | 86 |
| `npc.cecilia.talk.debt_low` | 74 |
| `npc.cecilia.talk.debt_high` | 80 |
| `npc.cecilia.talk.epilogue` | 108 |
| `npc.tiburcio.talk.general1` | 86 |
| `npc.tiburcio.talk.general2` | 79 |
| `npc.tiburcio.talk.general3` | 86 |
| `npc.tiburcio.talk.general4` | 79 |
| `npc.tiburcio.talk.morning` | 73 |
| `npc.tiburcio.talk.evening` | 66 |
| `npc.tiburcio.talk.rain` | 74 |
| `npc.tiburcio.talk.festival` | 71 |
| `npc.tiburcio.talk.debt_low` | 80 |
| `npc.tiburcio.talk.debt_high` | 71 |
| `npc.tiburcio.talk.epilogue` | 108 |
| `npc.jurandir.talk.general1` | 87 |
| `npc.jurandir.talk.general2` | 93 |
| `npc.jurandir.talk.general3` | 106 |
| `npc.jurandir.talk.general4` | 85 |
| `npc.jurandir.talk.morning` | 88 |
| `npc.jurandir.talk.evening` | 86 |
| `npc.jurandir.talk.rain` | 62 |
| `npc.jurandir.talk.festival` | 91 |
| `npc.jurandir.talk.debt_low` | 104 |
| `npc.jurandir.talk.debt_high` | 79 |
| `npc.jurandir.talk.epilogue` | 105 |
| `npc.nazare.talk.general1` | 85 |
| `npc.nazare.talk.general2` | 90 |
| `npc.nazare.talk.general3` | 64 |
| `npc.nazare.talk.general4` | 72 |
| `npc.nazare.talk.morning` | 89 |
| `npc.nazare.talk.evening` | 94 |
| `npc.nazare.talk.rain` | 82 |
| `npc.nazare.talk.festival` | 87 |
| `npc.nazare.talk.debt_low` | 102 |
| `npc.nazare.talk.debt_high` | 106 |
| `npc.nazare.talk.epilogue` | 110 |
| `npc.ivo.talk.general1` | 70 |
| `npc.ivo.talk.general2` | 49 |
| `npc.ivo.talk.general3` | 82 |
| `npc.ivo.talk.general4` | 113 |
| `npc.ivo.talk.morning` | 73 |
| `npc.ivo.talk.evening` | 82 |
| `npc.ivo.talk.rain` | 87 |
| `npc.ivo.talk.festival` | 92 |
| `npc.ivo.talk.debt_low` | 123 |
| `npc.ivo.talk.debt_high` | 97 |
| `npc.ivo.talk.epilogue` | 108 |
| `npc.dandara.talk.general1` | 86 |
| `npc.dandara.talk.general2` | 74 |
| `npc.dandara.talk.general3` | 103 |
| `npc.dandara.talk.general4` | 82 |
| `npc.dandara.talk.morning` | 59 |
| `npc.dandara.talk.evening` | 81 |
| `npc.dandara.talk.rain` | 95 |
| `npc.dandara.talk.festival` | 92 |
| `npc.dandara.talk.debt_low` | 81 |
| `npc.dandara.talk.debt_high` | 92 |
| `npc.dandara.talk.epilogue` | 103 |
| `npc.gloria.talk.general1` | 85 |
| `npc.gloria.talk.general2` | 75 |
| `npc.gloria.talk.general3` | 90 |
| `npc.gloria.talk.general4` | 92 |
| `npc.gloria.talk.morning` | 91 |
| `npc.gloria.talk.evening` | 93 |
| `npc.gloria.talk.rain` | 66 |
| `npc.gloria.talk.festival` | 76 |
| `npc.gloria.talk.debt_low` | 71 |
| `npc.gloria.talk.debt_high` | 102 |
| `npc.gloria.talk.epilogue` | 105 |
| `npc.otavio.talk.general1` | 102 |
| `npc.otavio.talk.general2` | 96 |
| `npc.otavio.talk.general3` | 77 |
| `npc.otavio.talk.general4` | 87 |
| `npc.otavio.talk.morning` | 85 |
| `npc.otavio.talk.evening` | 103 |
| `npc.otavio.talk.rain` | 47 |
| `npc.otavio.talk.festival` | 98 |
| `npc.otavio.talk.debt_low` | 97 |
| `npc.otavio.talk.debt_high` | 101 |
| `npc.otavio.talk.epilogue` | 105 |
| `npc.otavio.talk.post_reveal1` | 71 |

**Strings que deixam de ser a única fala:** as saudações atuais (`npc.*.greeting`) continuam valendo como primeira fala do dia de cada morador; nenhuma string antiga é removida por este arquivo.
