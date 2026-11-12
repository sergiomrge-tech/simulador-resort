# Textos da campanha v2 — LOTE COMPLETO (redator, 12/11/2026)

Contrato: `docs/ue58/CAMPANHA_V2.md`. Piloto aprovado: `textos_piloto.md`. Este arquivo é completo sozinho (as versões escolhidas do piloto estão copiadas aqui). Cada string tem um id estável entre crases; a lista completa de ids está no fim, junto com o que deixa de existir.

**Contagem:** caracteres Unicode do texto entre aspas, sem as aspas. Cartas: a carta inteira (parágrafos + assinatura, com as quebras). `(n/limite)` ao lado de cada string.

**Convenções do lote:** tratamento "Meu bem"/"você", sem gênero do jogador. A avó é "Vó Dilce" na assinatura e no narrador próximo do jogador; "Dona Dilce" na boca dos moradores e nos títulos de sistema. Por isso, duas falas aprovadas no piloto trocaram "sua avó" por "a Dona Dilce" (S2 do Severino e o thanks 3 da Dona Roberta); o resto ficou igual. Ninguém diz "Vovó".


## 1. Carta da casa (revisada) + P.S.

Mudanças mínimas: "Meu neto," → "Meu bem,"; "de você pequeno" → "de você criança"; nova linha "(Vire a folha.)" depois da assinatura, que leva ao P.S. O resto é o texto atual, palavra por palavra (a carta atual já passava de 900; não cortei). A frase "Quando o vento virou…" FICA: é virada na carta de 100 %.

### 1a. Primeira folha
- `letter.home.title` **Título (mantido)**: "Uma carta para você" (19/40)

**Carta inteira: 1032 caracteres**

> `letter.home.p1`  
> Meu bem,
>
> `letter.home.p2`  
> Se você está lendo esta carta, chegou à nossa vila. Ainda me lembro de você criança, correndo pela areia enquanto eu abria o quiosque. Você dizia que o mar tinha cheiro de aventura. Eu respondia que também tinha cheiro de casa.
>
> `letter.home.p3`  
> Nosso negócio começou com um balcão, alguns cocos e a vontade de acolher quem chegava. Nem todos os dias foram fáceis. Quando o vento virou, foram as pessoas da vila que nos ajudaram a continuar. Cada cadeira guarda uma conversa; cada freguês deixou um pedacinho de sua história conosco.
>
> `letter.home.p4`  
> Hoje minhas mãos precisam descansar um pouco mais, mas o sonho da família ainda tem muito caminho pela frente. Quero passar o quiosque para você. Abra as portas, conheça nossos vizinhos e faça deste lugar também o seu lugar.
>
> `letter.home.p5`  
> Se puder, ajude o negócio a crescer. Mas lembre-se de que o que construímos de mais valioso nunca coube em uma caixa registradora: foi o carinho com que recebemos cada pessoa.
>
> `letter.home.p6`  
> Não tenha pressa. Mesmo de longe, vou torcer por você a cada nova maré.
>
> `letter.home.p7`  
> Com todo meu amor,
>
> `letter.home.sign`  
> Vó Dilce

- `letter.home.turn` **Linha depois da assinatura**: "(Vire a folha.)" (15/30)
- `letter.home.button` **Botão (mantido)**: "Guardar a carta" (15/30)

### 1b. Segunda folha: P.S. (versão A2, aprovada)

**Carta inteira: 536 caracteres / limite 900**

> `letter.ps.p1`  
> P.S. Deixei esta parte para o verso, porque verso ninguém lê com pressa.
>
> `letter.ps.p2`  
> O quiosque vem com uma dívida de R$ 1.000.000. Sim, seis zeros. Contei duas vezes e eles continuaram lá.
>
> `letter.ps.p3`  
> A boa notícia: não tem juros nem prazo. O gerente do banco é um rapaz paciente e gosta de coco. Pague pelo celular, em Finanças, quando sobrar. Primeiro o quiosque, depois o banco.
>
> `letter.ps.p4`  
> E não, eu não comprei um iate. Cada real dessa conta tem uma história, e quase todas têm nome de vizinho. Vou contando aos poucos, que carta comprida cansa a vista.
>
> `letter.ps.sign`  
> Vó Dilce


**Nota ao tradutor:**
- "de você criança": "criança" é substantivo neutro; nas línguas com gênero, usar "quando você era criança" ou equivalente sem marcar o gênero do jogador.
- "Quando o vento virou, foram as pessoas da vila que nos ajudaram" volta palavra por palavra na carta de 100 %: traduzir as duas ocorrências IGUAIS.
- P.S.: "verso" é o verso da folha (back of the page), não poesia. "Finanças" = nome da aba do celular. Valor "R$ 1.000.000" no formato monetário da língua. "O gerente do banco" é personagem recorrente sem nome: mesma tradução em todas as cartas.


## 2. Cartas dos marcos da dívida

Padrão: Dona Dilce acha que o morador não sabe que foi ela; o morador sempre soube e protegeu o orgulho dela. Carta terna com UMA piada; o morador responde com humor (fala nova depois da carta, duas opções).

### 25 % — o píer depois do vendaval (B1, aprovada)
- `debt.letter.25.title` **Título da folha**: "Um quarto mais leve" (19/40)

**Carta inteira: 616 caracteres / limite 900**

> `debt.letter.25.p1`  
> Meu bem,
>
> `debt.letter.25.p2`  
> Um quarto já foi! Contei para as meninas do bingo e comemoramos com bolo. Perdi a rodada, mas não perdi a pose.
>
> `debt.letter.25.p3`  
> Prometi contar, então aí vai o primeiro pedaço. Há muitos anos um vendaval levou o píer inteiro. Sem píer, barco não sai; sem barco, a vila não come. O banco só emprestava se alguém assinasse junto. Assinei eu. Os pescadores pagaram o que puderam. O resto ficou comigo.
>
> `debt.letter.25.p4`  
> O Severino acha que o dinheiro veio da prefeitura, e eu deixei ele achar. Homem orgulhoso fica mais firme de pé com uma mentirinha.
>
> `debt.letter.25.p5`  
> O píer que você consertou com ele tem tábua minha lá embaixo. Pise com carinho.
>
> `debt.letter.25.sign`  
> Vó Dilce


**Fala nova do Seu Severino** (S2 aprovada; a S1 fica como alternativa)
- `npc.severino.after25.a` **S2 (primeira opção)**: "A Dona Dilce acha que eu acredito na prefeitura. A prefeitura nunca me deu nem um anzol. Se ela perguntar, diga que eu chorei. Não chorei. Foi o vento." (151/260)
- `npc.severino.after25.b` **S1**: "Ela nunca me contou que foi ela. E eu nunca contei para ela que sabia. Esse tempo todo, um protegendo o orgulho do outro." (121/260)

**Nota ao tradutor:**
- "Assinei eu" = ela foi FIADORA (co-signer, guarantor). Usar o mesmo termo de fiança/aval em todas as cartas: é o fio da campanha.
- "Perdi a rodada, mas não perdi a pose": rodada de bingo; a graça é a vaidade dela, não um trocadilho. "Pise com carinho" é literal (tábuas dela debaixo do píer).
- Severino: "Não chorei. Foi o vento." ecoa o "Diz que é cebola. Não tem cebola." da festa: mesma secura, sem exclamação.


### 50 % — o telhado da igreja e o sino (Padre Robson)
- `debt.letter.50.title` **Título da folha**: "Metade da maré" (14/40)

**Carta inteira: 576 caracteres / limite 900**

> `debt.letter.50.p1`  
> Meu bem,
>
> `debt.letter.50.p2`  
> Metade! Estou escrevendo devagar para a notícia durar mais.
>
> `debt.letter.50.p3`  
> O segundo pedaço é da igreja. Num inverno de muita chuva, o telhado cedeu bem em cima do altar, e o sino rachou no mesmo mês. A paróquia não tinha nem para a telha. Fui ao banco outra vez, com a mesma caneta. O gerente já me reconhecia pelo jeito de bater na porta.
>
> `debt.letter.50.p4`  
> O Padre Robson acha que foi um milagre, e eu deixei. Ninguém tira um milagre de um padre.
>
> `debt.letter.50.p5`  
> Toda vez que o sino toca às sete, eu sei que valeu. Agora ele toca também por você. Vá à missa um dia desses, nem que seja só para ouvir.
>
> `debt.letter.50.sign`  
> Vó Dilce


**Fala nova do Padre Robson**
- `npc.robson.after50.a` **Opção a**: "A Dona Dilce acha que eu acredito em milagre de banco. Eu acredito em milagre, meu bem. Mas conheço a letra dela num contrato." (126/260)
- `npc.robson.after50.b` **Opção b**: "Todo domingo eu agradeço a Deus pelo telhado. E à Dona Dilce também, mais baixinho, para ela não ouvir lá do bingo." (115/260)

**Nota ao tradutor:**
- A única piada da carta é "o gerente já me reconhecia pelo jeito de bater na porta" (ela foi tantas vezes ao banco que ele sabia quem era sem abrir). Manter.
- "o sino toca às sete": a missa da manhã do jogo é às 7h; não trocar o horário.
- Padre a: "milagre de banco" = empréstimo que parece milagre; a graça é ele ter reconhecido a assinatura. Tom carinhoso, nada irreverente com a religião.


### 75 % — a cozinha da Dona Cecília e a escola da vila (Prefeita Tuanny)
- `debt.letter.75.title` **Título da folha**: "Quase dá para respirar" (22/40)

**Carta inteira: 667 caracteres / limite 900**

> `debt.letter.75.p1`  
> Meu bem,
>
> `debt.letter.75.p2`  
> Três quartos. Já dá para respirar, e eu respirei fundo, de olho fechado, na varanda das meninas.
>
> `debt.letter.75.p3`  
> Os pedaços de agora são de comer e de aprender. A cozinha da Cecília pegou fogo numa véspera de festa: foram o fogão, as panelas e quase a vontade dela. No mesmo ano, a escola da vila tinha uma sala só, com goteira bem em cima do quadro. Assinei as duas.
>
> `debt.letter.75.p4`  
> A Cecília acha que foi a rifa da paróquia. A Tuanny, que ainda nem era prefeita, acha que a verba veio do governo e fez discurso agradecendo. Deixei as duas achando.
>
> `debt.letter.75.p5`  
> Quando você comer na barraca da Cecília, ou passar na escola na hora do recreio, saiba que aquilo também é um pouco seu agora.
>
> `debt.letter.75.sign`  
> Vó Dilce


**Fala nova da Dona Cecília**
- `npc.cecilia.after75.a` **Opção a**: "Rifa da paróquia? A rifa deu um liquidificador, e ele nem funcionava. Eu sempre soube, meu bem. Por isso o pastel da Dona Dilce sempre veio com recheio dobrado." (160/260)
- `npc.cecilia.after75.b` **Opção b**: "A Dona Dilce acha que eu não sei fazer conta. Eu sei fazer conta, sei fazer cocada e sei quem pagou o meu fogão." (112/260)

**Fala nova da Prefeita Tuanny**
- `npc.tuanny.after75.a` **Opção a**: "Eu sempre soube que foi ela. Mas político não desmente notícia boa, meu bem. Fiz discurso, cortei a fita e mandei flores para o bingo. Sem cartão." (146/260)
- `npc.tuanny.after75.b` **Opção b**: "Vou inaugurar uma placa na escola: "Sala Dona Dilce". Ela vai reclamar. Eu vou cortar a fita do mesmo jeito." (108/260)

**Nota ao tradutor:**
- A piada da carta é a Tuanny fazendo discurso para agradecer o governo por um dinheiro que era da Dilce. Tuanny é política simpática: a graça é a vaidade, nunca corrupção.
- "varanda das meninas" = a casa das amigas do bingo onde Dilce mora. "um pouco seu agora": o jogador herdou a vila, não só a dívida.
- Cecília a: "recheio dobrado" = double filling (ela retribuía em comida). "Sala Dona Dilce" é nome de placa: traduzir "Sala" (classroom/room), manter "Dona Dilce".


### 100 % — a última parcela (lida na Festa da Maré Alta, antes de ela desembarcar)
- `debt.letter.100.title` **Título da folha**: "A última parcela" (16/40)

**Carta inteira: 626 caracteres / limite 900**

> `debt.letter.100.p1`  
> Meu bem,
>
> `debt.letter.100.p2`  
> Se esta carta chegou antes de mim, é porque o barco atrasou. Me espere no píer.
>
> `debt.letter.100.p3`  
> Lembra da primeira carta? Escrevi que, quando o vento virou, foram as pessoas da vila que nos ajudaram a continuar. Era verdade. Só não contei que, antes, quem segurou a vila fui eu. E agora a vila segurou você: cada coco, cada noite na pousada, cada parcela.
>
> `debt.letter.100.p4`  
> Falta o último pedaço. A última assinatura não foi para ninguém da vila. Foi o terreno do quiosque. Comprei no seu nome, para quando você voltasse. Eu sempre soube que você voltava.
>
> `debt.letter.100.p5`  
> O gerente pediu para avisar que vai sentir sua falta. Eu não vou: estou chegando.
>
> `debt.letter.100.sign`  
> Vó Dilce


**Primeira fala da Dona Dilce ao desembarcar** (o "morador ligado" ao marco de 100 % é o jogador; esta é a resposta da carta, usada no roteiro da festa, linha 6)
- `npc.dilce.arrival.a` **Opção a (primeira)**: "Meu bem! Eu disse que você voltava. Agora quem voltou fui eu." (61/260)
- `npc.dilce.arrival.b` **Opção b**: "Meu bem! Recebeu minha carta? Eu cheguei antes da resposta, como sempre." (72/260)

**Nota ao tradutor:**
- A frase "quando o vento virou, foram as pessoas da vila que nos ajudaram a continuar" é CITAÇÃO da carta da casa: usar exatamente a mesma tradução. A virada ("quem segurou a vila fui eu… agora a vila segurou você") depende do mesmo verbo nas duas metades: escolher um verbo (hold up / support) e repetir.
- "Comprei no seu nome, para quando você voltasse": é o fecho emocional do jogo; sem gênero do jogador. "Eu sempre soube que você voltava" responde à saudação da Dona Roberta ("Sua avó sempre disse que você voltaria").
- Única piada: "O gerente… vai sentir sua falta. Eu não vou: estou chegando." — o "não vou sentir falta" é carinho (ela vai estar perto), não frieza.


## 3. Lembrete curto depois de criar a empresa (substitui o cartão de 14 s)

- `debt.reminder.title` **Título**: "A dívida da Dona Dilce" (22/40)
- `debt.reminder.text` **Frase**: "Paga-se aos poucos, pelo celular: B · Finanças. Sem juros, sem prazo, sem pressa." (81/120)

**Nota ao tradutor:**
- "B" é a tecla do celular e "Finanças" a aba: iguais à interface. Título de sistema usa "Dona Dilce" (o piloto dizia "Vó Dilce": ajustado à convenção).


## 4. Capítulos novos

### 5. `rede` — As redes da Dona Roberta (aprovado; ordem das falas conforme o diretor)
- `chapter.rede.title` **Título**: "As redes da Dona Roberta" (24/32)
- `chapter.rede.story` **Abertura (`story`, fala de Dona Roberta no passo 1)**: "Desde que a pousada abriu, o Seu Severino acorda com um turista diferente na rede dele. Ontem eram dois. Eu faço rede há trinta anos, meu bem. Vamos fazer redes para a pousada antes que ele vá dormir no barco." (209/260)

**Passo 1**
- `chapter.rede.step1.text` **Texto do passo**: "Hospedar 6 hóspedes na pousada durante esta etapa" (49/70)
- `chapter.rede.step1.line_a` **Fala a (primeira opção)**: "Primeiro preciso saber o tamanho do povo. Hospede uns seis e me conte quem ronca. Rede de quem ronca leva nó mais firme." (120/260)
- `chapter.rede.step1.line_b` **Fala b**: "Seis hóspedes, meu bem. Eu olho quem sai da pousada e tiro a medida no olho. Nunca errei. Só uma vez, com o Padre, mas ele estava de batina." (140/260)

**Passo 2**
- `chapter.rede.step2.text` **Texto do passo**: "Doar R$ 600 para o tecido das redes" (35/70)
- `chapter.rede.step2.line_a` **Fala a (primeira opção)**: "Linha eu tenho. Paciência eu tenho. Tecido, não. Seiscentos reais resolvem o tecido; o resto é comigo." (102/260)
- `chapter.rede.step2.line_b` **Fala b**: "Algodão bom vem de longe e chega caro. Com R$ 600 compro tecido para todas, e ainda sobra um pedaço para remendar a do Severino." (128/260)

**Passo 3**
- `chapter.rede.step3.text` **Texto do passo**: "Chegar à fama "Roteiro turístico"" (33/70)
- `chapter.rede.step3.line_a` **Fala a (primeira opção)**: "As redes estão prontas. Agora falta gente de longe para deitar nelas. Quando o quiosque virar roteiro turístico, eu penduro." (124/260)
- `chapter.rede.step3.line_b` **Fala b**: "Rede bonita sem ninguém dentro é só tapete pendurado. Deixe o nome do quiosque correr longe, que eu cuido dos ganchos." (118/260)

**Despedidas (`thanks`, sorteadas)**
- `chapter.rede.thanks1` **Thanks 1**: "As redes ficaram lindas. O Severino recuperou a dele e já dormiu nela de botas. Obrigada, meu bem." (98/260)
- `chapter.rede.thanks2` **Thanks 2**: "Passei na pousada hoje e tinha um turista dormindo de boca aberta numa rede minha. Melhor elogio que já recebi." (111/260)
- `chapter.rede.thanks3` **Thanks 3**: "Sabia que foi a Dona Dilce que me deu o primeiro novelo? A rede deu a volta e voltou para a família." (100/260)
- `chapter.rede.unlock` **Unlock**: "Redes de descanso na varanda da pousada" (39/60)

**Nota ao tradutor:**
- "Rede" = rede de dormir (hammock), nunca de pesca. "Roteiro turístico" no passo 3 é o NOME DO NÍVEL 6 de fama: mesma tradução do nível.
- Dona Roberta fala no feminino ("Obrigada"). Fala 1b: a batina (cassock) esconde as medidas do padre.
- "Seiscentos reais" por extenso é fala; pode virar número se a língua preferir.


### 6. `farol` — A lanterna da Alana
- `chapter.farol.title` **Título**: "A lanterna da Alana" (19/32)
- `chapter.farol.story` **Abertura (`story`, fala de Alana no passo 1)**: "Meu avô foi o último faroleiro da ilha. Desde que ele morreu, o farol dorme apagado e os barcos voltam guiados pela luz da sorveteria. Quero acender de novo. Primeiro, preciso que gente de fora volte a subir até lá." (215/260)

**Passo 1**
- `chapter.farol.step1.text` **Texto do passo**: "Guiar 3 passeios turísticos durante esta etapa" (46/70)
- `chapter.farol.step1.line_a` **Fala a (primeira opção)**: "Leve uns turistas para passear. Se o farol voltar a ter visita, ninguém na prefeitura vai ter coragem de dizer que ele não serve para nada." (139/260)
- `chapter.farol.step1.line_b` **Fala b**: "Três passeios. Cada turista que sobe a trilha e diz "que lindo" é mais um voto para o farol." (92/260)

**Passo 2**
- `chapter.farol.step2.text` **Texto do passo**: "Fotografar o farol ao pôr do sol (tecla P)" (42/70)
- `chapter.farol.step2.line_a` **Fala a (primeira opção)**: "Meu avô dizia que o farol fica mais bonito na hora em que precisa acender. Tira uma foto dele ao pôr do sol? Quero mostrar para a prefeita." (139/260)
- `chapter.farol.step2.line_b` **Fala b**: "Uma foto do farol com o céu laranja atrás. Foto de farol apagado ao meio-dia ninguém pendura na parede." (103/260)

**Passo 3**
- `chapter.farol.step3.text` **Texto do passo**: "Doar R$ 900 para a lâmpada nova do farol" (40/70)
- `chapter.farol.step3.line_a` **Fala a (primeira opção)**: "Achei a lâmpada certa. Custa R$ 900 e vem de navio, o que é engraçado: é ela que ajuda o navio a chegar." (104/260)
- `chapter.farol.step3.line_b` **Fala b**: "A lente ainda é a do meu avô, inteirinha. Só falta a lâmpada. R$ 900 e o farol acorda." (86/260)

**Despedidas (`thanks`, sorteadas)**
- `chapter.farol.thanks1` **Thanks 1**: "Ontem à noite o facho passou pela minha janela três vezes antes de eu dormir. Contei como se fossem carneirinhos." (113/260)
- `chapter.farol.thanks2` **Thanks 2**: "Os pescadores voltam mais cedo agora. Dizem que é por causa da luz. Eu acho que é por causa da janta." (101/260)
- `chapter.farol.thanks3` **Thanks 3**: "Meu avô ia gostar de saber que foi alguém da família da Dona Dilce. Ela subia levando café para ele, sabia?" (107/260)
- `chapter.farol.unlock` **Unlock**: "Facho do farol aceso todas as noites" (36/60)

**Nota ao tradutor:**
- "faroleiro" = lighthouse keeper. "facho" = o feixe giratório (beam). "luz da sorveteria": a piada é o farol ter sido substituído por um letreiro de sorvete.
- Passo 2 é o desafio de foto que já existe: o texto deve seguir a tradução do desafio ("pôr do sol", tecla P).
- Thanks 1: contar carneirinhos para dormir; se a língua tiver outro costume para "contar para dormir", adaptar mantendo a imagem de contar.


### 7. `descanso` — O descanso do Seu Tibúrcio
- `chapter.descanso.title` **Título**: "O descanso do Seu Tibúrcio" (26/32)
- `chapter.descanso.story` **Abertura (`story`, fala de Seu Tibúrcio no passo 1)**: "Trinta anos olhando esse mar, meu bem. As pernas já não sobem com a mesma pressa. Se eu tiver certeza de que você leva isso a sério, talvez eu aceite um ajudante. Talvez. O mar é desconfiado, e eu também." (204/260)

**Passo 1**
- `chapter.descanso.step1.text` **Texto do passo**: "Levar 12 oferendas ao cesto (no total)" (38/70)
- `chapter.descanso.step1.line_a` **Fala a (primeira opção)**: "Doze oferendas. O mar precisa conhecer a sua cara antes de aceitar a de outra pessoa." (85/260)
- `chapter.descanso.step1.line_b` **Fala b**: "Não é por mim, é por ele. O mar gosta de rotina. Eu também, mas não conta para ele." (83/260)

**Passo 2**
- `chapter.descanso.step2.text` **Texto do passo**: "Levar 5 cocos para o Seu Tibúrcio" (33/70)
- `chapter.descanso.step2.line_a` **Fala a (primeira opção)**: "Cinco cocos. Não é oferenda, é para mim. Ninguém pensa no velho que passa o dia aqui em cima gritando." (102/260)
- `chapter.descanso.step2.line_b` **Fala b**: "O mar ganha oferenda todo dia. Eu, nada. Traz cinco cocos, e não conta para ele." (80/260)

**Passo 3**
- `chapter.descanso.step3.text` **Texto do passo**: "Doar R$ 2.000 para o cesto novo" (31/70)
- `chapter.descanso.step3.line_a` **Fala a (primeira opção)**: "Este cesto é mais velho que a trilha. Se ele rasgar no dia errado, adeus vila. Um de vime bom custa R$ 2.000." (109/260)
- `chapter.descanso.step3.line_b` **Fala b**: "Um cesto novo e eu deixo o seu atendente subir no seu lugar. Mas o cesto tem que ser bonito. O mar repara." (106/260)

**Despedidas (`thanks`, sorteadas)**
- `chapter.descanso.thanks1` **Thanks 1**: "O atendente subiu hoje. Deu bom-dia para o mar. O mar não respondeu, mas ficou calminho. Aprovado." (98/260)
- `chapter.descanso.thanks2` **Thanks 2**: "Agora eu desço até o quiosque no fim da tarde. A trilha continua do mesmo tamanho; eu é que estou com mais tempo." (113/260)
- `chapter.descanso.thanks3` **Thanks 3**: "Trinta anos de vigia e ninguém nunca me ofereceu folga. Você ofereceu. O mar e eu agradecemos." (94/260)
- `chapter.descanso.unlock` **Unlock**: "Oferenda delegável + Seu Tibúrcio no quiosque à tarde" (53/60)

**Nota ao tradutor:**
- Tibúrcio fala do mar como de uma pessoa temperamental ("ele", "o mar repara"): manter o mar como sujeito masculino/animado onde a língua permitir. "A Onda" (maiúscula) é o tsunami: não aparece aqui, mas não traduzir "onda" como "Onda" por engano.
- "Trinta anos" é fixo para ele (já está em outras falas). "vime" = wicker.
- Passo 2 é uma entrega do estoque (como os peixes do píer): "Levar 5 cocos" no mesmo molde do passo do píer.


### 8. `critico` — O paladar do Seu Arnaldo
- `chapter.critico.title` **Título**: "O paladar do Seu Arnaldo" (24/32)
- `chapter.critico.story` **Abertura (`story`, fala de Seu Arnaldo no passo 1)**: "Faz anos que eu reclamo de tudo nesta ilha e ninguém pergunta por quê. Pois eu digo: porque presto atenção. Melhore suas receitas, e talvez eu tenha um elogio guardado. Talvez. Não me olhe assim." (195/260)

**Passo 1**
- `chapter.critico.step1.text` **Texto do passo**: "Melhorar receitas 10 vezes durante esta etapa" (45/70)
- `chapter.critico.step1.line_a` **Fala a (primeira opção)**: "O caldo de peixe tem medo do sal. A cocada está com pressa. Melhore dez receitas e depois a gente conversa." (107/260)
- `chapter.critico.step1.line_b` **Fala b**: "Dez melhorias. Eu provo tudo e anoto num caderninho. Não, você não pode ver o caderninho." (89/260)

**Passo 2**
- `chapter.critico.step2.text` **Texto do passo**: "Servir 30 pratos no restaurante do hotel" (40/70)
- `chapter.critico.step2.line_a` **Fala a (primeira opção)**: "Comida boa na cozinha não vale nada. Quero ver servida, quente, trinta vezes, sem ninguém reclamar. Além de mim." (112/260)
- `chapter.critico.step2.line_b` **Fala b**: "Vou almoçar no restaurante do hotel todo dia esta semana. Por motivos profissionais. Que eu ainda não posso contar." (115/260)

**Passo 3**
- `chapter.critico.step3.text` **Texto do passo**: "Receber 3 críticas boas no restaurante" (38/70)
- `chapter.critico.step3.line_a` **Fala a (primeira opção)**: "Pronto, conto: o crítico disfarçado do restaurante sou eu. Assino com outro nome há quarenta anos. Três críticas boas e eu ponho meu nome de verdade numa placa." (160/260)
- `chapter.critico.step3.line_b` **Fala b**: "Você já desconfiou, não é? Ninguém reclama tanto de graça. Sim, eu sou o crítico. Três críticas boas e eu assino embaixo, com meu nome de verdade." (146/260)

**Despedidas (`thanks`, sorteadas)**
- `chapter.critico.thanks1` **Thanks 1**: "Recomendado pelo Arnaldo. Quarenta anos de profissão e é a primeira placa que eu assino. Não se acostume." (105/260)
- `chapter.critico.thanks2` **Thanks 2**: "A água de coco continua natural demais. Mas agora acho que isso é uma qualidade." (80/260)
- `chapter.critico.thanks3` **Thanks 3**: "A Dona Dilce foi a única que nunca se ofendeu com as minhas reclamações. Anotava todas e resolvia uma por semana." (113/260)
- `chapter.critico.unlock` **Unlock**: "Placa "Recomendado pelo Arnaldo" no restaurante" (47/60)

**Nota ao tradutor:**
- Seu Arnaldo é o reclamão dos eventos cômicos (HUM-007): usar o mesmo registro e o mesmo nome traduzido ("Mr. Arnaldo"). Thanks 2 cita a primeira fala dele ("água de coco… muito natural"): usar a mesma palavra da tradução de HUM-007.
- A revelação (ele é o crítico gastronômico disfarçado do restaurante) acontece no passo 3; as falas dos passos 1–2 só dão pistas. Não revelar antes na tradução.
- "Recomendado pelo Arnaldo" é o texto da placa no cenário (TextRender): curto, sem "Seu".


### 9. `quarto` — O quarto com vista (Seu Severino, em nome da vila)
- `chapter.quarto.title` **Título**: "O quarto com vista" (18/32)
- `chapter.quarto.story` **Abertura (`story`, fala de Seu Severino no passo 1)**: "Fala baixo, meu bem. A vila resolveu uma coisa: quando a dívida acabar, a Dona Dilce volta. Com festa, com quarto com vista e sem ela saber de nada. Ela vive pedindo esse quarto. Vamos dar." (189/260)

**Passo 1**
- `chapter.quarto.step1.text` **Texto do passo**: "Fazer 10 melhorias de personalização durante esta etapa" (55/70)
- `chapter.quarto.step1.line_a` **Fala a (primeira opção)**: "Primeiro, a vila tem que estar bonita. Dez melhorias. Ela vai chegar procurando defeito, igual a mim." (101/260)
- `chapter.quarto.step1.line_b` **Fala b**: "A Cecília quer flores, o Padre quer bandeirinha, a Roberta quer rede em tudo. Faça dez melhorias e todo mundo fica quieto." (122/260)

**Passo 2**
- `chapter.quarto.step2.text` **Texto do passo**: "Realizar 1 evento do hotel durante esta etapa" (45/70)
- `chapter.quarto.step2.line_a` **Fala a (primeira opção)**: "Precisamos treinar festa. Monte um evento no hotel, que eu fico olhando onde cada um vai ficar no dia." (102/260)
- `chapter.quarto.step2.line_b` **Fala b**: "Um evento no hotel, meu bem. Se a vila sabe organizar casamento de gente que nem conhece, sabe organizar a volta dela." (118/260)

**Passo 3**
- `chapter.quarto.step3.text` **Texto do passo**: "Doar R$ 5.000 para a passagem e o quarto" (40/70)
- `chapter.quarto.step3.line_a` **Fala a (primeira opção)**: "A passagem de barco e o quarto do último andar: R$ 5.000. O resto a vila juntou em lata de biscoito." (100/260)
- `chapter.quarto.step3.line_b` **Fala b**: "O Padre benze o quarto, a Tuanny corta a fita, e eu carrego a mala. Só falta o dinheiro: R$ 5.000." (98/260)

**Despedidas (`thanks`, sorteadas)**
- `chapter.quarto.thanks1` **Thanks 1**: "Está tudo pronto. Se ela perguntar, ninguém sabe de nada. Eu sou péssimo nisso. Fala você." (90/260)
- `chapter.quarto.thanks2` **Thanks 2**: "O quarto tem vista para o píer. Ela vai poder reclamar das minhas tábuas lá de cima." (84/260)
- `chapter.quarto.thanks3` **Thanks 3**: "Agora só falta quitar a dívida. A festa espera, o barco espera, e eu espero. Se eu chorar no dia, é cebola." (107/260)
- `chapter.quarto.unlock` **Unlock**: "Dona Dilce vem para a festa e mora no hotel" (43/60)

**Nota ao tradutor:**
- É um SEGREDO da vila contra a Dona Dilce: o tom é de cochicho. "Fala baixo" = speak quietly.
- Thanks 3 antecipa a fala da festa ("Diz que é cebola. Não tem cebola."): usar a mesma palavra para cebola (onion).
- "lata de biscoito" = cookie tin onde se guarda dinheiro em casa; adaptar ao objeto equivalente da cultura se não existir.


## 5. Capítulos antigos: falas por passo e despedidas

Textos dos passos e aberturas mantidos (não mudam). Só entram `lines` e `thanks`. A frase genérica "Obrigado pela ajuda com …" deixa de existir (substituída pelas `thanks` de cada capítulo).

### `pier` — O píer do Seu Severino

**Passo 1**
- texto do passo (mantido, não muda): "Levar 4 peixes para o almoço dos pescadores"
- `chapter.pier.step1.line_a` **Fala a (primeira opção)**: "Quatro peixes, meu bem. Pescador com fome não segura martelo." (61/260)
- `chapter.pier.step1.line_b` **Fala b**: "O almoço vem primeiro. Ninguém conserta píer de barriga vazia. Nem o píer gosta." (80/260)

**Passo 2**
- texto do passo (mantido, não muda): "Entregar 15 produtos no quiosque durante esta etapa"
- `chapter.pier.step2.line_a` **Fala a (primeira opção)**: "Venda bastante lá no quiosque. Turista feliz anda no píer, e píer cheio é píer que ninguém esquece de consertar." (112/260)
- `chapter.pier.step2.line_b` **Fala b**: "Quinze entregas. Quero ver fila naquele balcão, igual no tempo da Dona Dilce." (77/260)

**Passo 3**
- texto do passo (mantido, não muda): "Doar R$ 150 para as tábuas novas"
- `chapter.pier.step3.line_a` **Fala a (primeira opção)**: "Cento e cinquenta reais de tábua e o píer fica de pé mais trinta anos. Ou dez. Depende do mar." (94/260)
- `chapter.pier.step3.line_b` **Fala b**: "As tábuas novas já estão separadas. Falta pagar. O dono da madeira não aceita peixe; já tentei." (95/260)

**Despedidas (`thanks`, sorteadas)**
- `chapter.pier.thanks1` **Thanks 1**: "O píer está firme. Pulei em cima três vezes para testar. Ninguém viu. Foi só um teste." (86/260)
- `chapter.pier.thanks2` **Thanks 2**: "Os barcos voltaram a atracar sem medo, e as pranchas estão lá para alugar. A Dona Dilce ia gostar." (98/260)
- `chapter.pier.thanks3` **Thanks 3**: "Quando eu contar essa história, vou dizer que fiz tudo sozinho. Você me desmente, se quiser." (92/260)
- `chapter.pier.unlock` **Unlock**: "Aluguel de pranchas e caiaques no píer" (38/60)

**Nota ao tradutor:**
- Thanks 3 prepara a missão `lenda` (Severino exagera para os turistas). "O dono da madeira não aceita peixe" ecoa "Peixe não aceita boleto" da carta de 25 %: pescadores pobres, dito sem drama.


### `prainha` — A Prainha do Oeste (Padre Robson)

**Passo 1**
- texto do passo (mantido, não muda): "Chegar à fama "Ponto da praia""
- `chapter.prainha.step1.line_a` **Fala a (primeira opção)**: "Para reabrir a trilha, preciso que a vila acredite. E a vila acredita em quem é famoso. Ainda não é pecado." (107/260)
- `chapter.prainha.step1.line_b` **Fala b**: "Quando o quiosque virar ponto da praia, o povo me ajuda no mutirão. Antes disso, somos só eu e as formigas." (107/260)

**Passo 2**
- texto do passo (mantido, não muda): "Fotografar o farol (tecla P)"
- `chapter.prainha.step2.line_a` **Fala a (primeira opção)**: "Tire uma foto do farol. Vou pôr no mural da igreja: um pouco de beleza ajuda a juntar voluntário." (97/260)
- `chapter.prainha.step2.line_b` **Fala b**: "O farol é o melhor anúncio desta costa. Com uma foto bonita dele eu convenço até quem cochila na missa." (103/260)

**Passo 3**
- texto do passo (mantido, não muda): "Levar 6 cocos para o mutirão"
- `chapter.prainha.step3.line_a` **Fala a (primeira opção)**: "Seis cocos para o mutirão. Abrir trilha no sol dá sede, e voluntário com sede vira ex-voluntário." (97/260)
- `chapter.prainha.step3.line_b` **Fala b**: "Seis cocos e a gente começa. Eu benzo a trilha, eles carregam as pedras. Divisão justa." (87/260)

**Despedidas (`thanks`, sorteadas)**
- `chapter.prainha.thanks1` **Thanks 1**: "A trilha da prainha está aberta. Primeira missa ao ar livre no domingo. Se chover, foi um ensaio." (97/260)
- `chapter.prainha.thanks2` **Thanks 2**: "Fui à prainha ver o pôr do sol e esqueci de rezar. Deus entende: foi Ele que fez o pôr do sol." (94/260)
- `chapter.prainha.thanks3` **Thanks 3**: "A trilha está aberta graças a você. A Dona Dilce ajudava assim também, sem fazer barulho." (89/260)
- `chapter.prainha.unlock` **Unlock**: "Escolinha de surfe" (18/60)

**Nota ao tradutor:**
- "Ponto da praia" no passo 1 é o NOME DO NÍVEL 3 de fama (usar a tradução do nível; na fala 1b aparece como expressão comum). "mutirão" = trabalho voluntário coletivo (community work day).
- Thanks 3 é pista discreta da carta de 50 % ("sem fazer barulho"): não explicar mais do que o texto diz.
- Unlock perdeu "Prainha do Oeste aberta" (não existe no jogo).


### `sabores` — Sabores da vila (Dona Cecília)

**Passo 1**
- texto do passo (mantido, não muda): "Descobrir 2 drinks novos no Bar do Coqueiro"
- `chapter.sabores.step1.line_a` **Fala a (primeira opção)**: "Prato bom conversa com bebida boa. Descubra dois drinks novos no bar, que eu penso no prato que combina." (104/260)
- `chapter.sabores.step1.line_b` **Fala b**: "Minha avó dizia que todo prato tem o copo certo. Me ajude a achar dois." (71/260)

**Passo 2**
- texto do passo (mantido, não muda): "Vender 10 porções de petiscos durante esta etapa"
- `chapter.sabores.step2.line_a` **Fala a (primeira opção)**: "Dez porções de petisco. Quero ver se o povo daqui ainda sabe comer com a mão e sorrir ao mesmo tempo." (101/260)
- `chapter.sabores.step2.line_b` **Fala b**: "Venda os petiscos, meu bem. Eu fico de longe, olhando a cara de quem prova. É assim que se testa receita." (105/260)

**Passo 3**
- texto do passo (mantido, não muda): "Pagar R$ 250 da reforma da barraca do pastel"
- `chapter.sabores.step3.line_a` **Fala a (primeira opção)**: "A barraca do pastel está com a lona rasgada e o óleo de outra década. Com R$ 250 ela volta a fritar." (100/260)
- `chapter.sabores.step3.line_b` **Fala b**: "Duzentos e cinquenta reais de reforma. A massa eu faço; o resto é tábua, tinta e coragem." (89/260)

**Despedidas (`thanks`, sorteadas)**
- `chapter.sabores.thanks1` **Thanks 1**: "A barraca voltou a fritar. A rua principal fica com cheiro de domingo o dia inteiro." (84/260)
- `chapter.sabores.thanks2` **Thanks 2**: "Pus no cardápio a receita da minha avó. E uma da Dona Dilce, que ela nunca soube que eu copiei." (95/260)
- `chapter.sabores.thanks3` **Thanks 3**: "Pastel de camarão saindo, meu bem. O primeiro é sempre seu. O segundo também, mas não conte." (92/260)
- `chapter.sabores.unlock` **Unlock**: "Barraca do pastel" (17/60)

**Nota ao tradutor:**
- "minha avó" na fala 1b e no thanks 2 é a AVÓ DA CECÍLIA (a abertura do capítulo fala das receitas da avó dela), não a Dona Dilce.
- "óleo de outra década" = óleo de fritura velhíssimo (exagero). Unlock perdeu "dica da moqueca" (não existe).


### `carnaval` — O Carnaval da Maré (Prefeita Tuanny)

**Passo 1**
- texto do passo (mantido, não muda): "Chegar à fama "Famoso na região""
- `chapter.carnaval.step1.line_a` **Fala a (primeira opção)**: "Para trazer turista de longe, o quiosque tem que ser famoso na região. Eu ajudo: falo dele em todo discurso." (108/260)
- `chapter.carnaval.step1.line_b` **Fala b**: "Fama, meu bem. Sem fama não tem patrocínio, e sem patrocínio o carnaval vira três pessoas e um tambor." (102/260)

**Passo 2**
- texto do passo (mantido, não muda): "Ter 2 negócios funcionando"
- `chapter.carnaval.step2.line_a` **Fala a (primeira opção)**: "Dois negócios funcionando na vila. Carnaval sem barraca é só gente pulando com fome." (84/260)
- `chapter.carnaval.step2.line_b` **Fala b**: "No último discurso eu prometi emprego para a vila. Com dois negócios abertos, a promessa fica cumprida. Uma novidade." (117/260)

**Passo 3**
- texto do passo (mantido, não muda): "Pagar R$ 400 da decoração"
- `chapter.carnaval.step3.line_a` **Fala a (primeira opção)**: "R$ 400 para a decoração. Confete, fita e um laço bem grande. O laço é para eu cortar na inauguração." (100/260)
- `chapter.carnaval.step3.line_b` **Fala b**: "A prefeitura entra com o entusiasmo, e você entra com os R$ 400. Parceria, meu bem." (83/260)

**Despedidas (`thanks`, sorteadas)**
- `chapter.carnaval.thanks1` **Thanks 1**: "Carnaval no calendário! Já mandei fazer a faixa. O seu nome está nela, em letra menor que o meu, mas está." (106/260)
- `chapter.carnaval.thanks2` **Thanks 2**: "Hoje cortei a fita do carnaval, da lojinha e de uma porta que nem era inauguração. Dia produtivo." (97/260)
- `chapter.carnaval.thanks3` **Thanks 3**: "A vila nunca teve tanto turista. Já estou pensando no discurso do ano que vem. Você aparece nele." (97/260)
- `chapter.carnaval.unlock` **Unlock**: "Carnaval no calendário de festas + Lojinha de souvenires" (56/60)

**Nota ao tradutor:**
- Tuanny é prefeita em exercício, simpática e política até o osso: promete, inaugura, corta fita. A piada é a vaidade e o discurso; nada de corrupção ou deboche da política real.
- "Famoso na região" no passo 1 é o NOME DO NÍVEL 5 de fama. "cortar a fita" = cerimônia de inauguração (ribbon cutting): imagem recorrente dela no jogo inteiro.


## 6. Missões novas

### `parcela`
- `mission.parcela.title` **Título**: "A primeira parcela" (18/32)
- `mission.parcela.task` **Tarefa**: "Pagar R$ 50 ou mais da dívida no celular (Finanças)" (51/70)
- `mission.parcela.story` **Story**: "O gerente do banco pendurou um quadro para a primeira parcela do quiosque. Está vazio desde que ele pendurou. Qualquer valor a partir de R$ 50 já merece moldura." (161/220)

### `rede_m`
- `mission.rede_m.title` **Título**: "As redes da Dona Roberta" (24/32)
- `mission.rede_m.task` **Tarefa**: "Concluir As redes da Dona Roberta em Histórias da vila" (54/70)
- `mission.rede_m.story` **Story**: "Os hóspedes continuam dormindo na rede do Seu Severino. Ele já pendurou uma placa de "particular". Dona Roberta tem uma ideia, e muita linha." (141/220)

### `farol_m`
- `mission.farol_m.title` **Título**: "A lanterna da Alana" (19/32)
- `mission.farol_m.task` **Tarefa**: "Concluir A lanterna da Alana em Histórias da vila" (49/70)
- `mission.farol_m.story` **Story**: "O farol está apagado há anos e os barcos voltam para casa guiados pela luz da sorveteria. A Alana guardou a lente do avô e tem um plano." (136/220)

### `descanso_m`
- `mission.descanso_m.title` **Título**: "O descanso do Seu Tibúrcio" (26/32)
- `mission.descanso_m.task` **Tarefa**: "Concluir O descanso do Seu Tibúrcio em Histórias da vila" (56/70)
- `mission.descanso_m.story` **Story**: "Seu Tibúrcio grita lá do morro que está cansado. Depois grita que não está. Suba e descubra qual dos dois é verdade." (116/220)

### `divida_25`
- `mission.divida_25.title` **Título**: "Um quarto mais leve" (19/32)
- `mission.divida_25.task` **Tarefa**: "Pagar 25% da dívida (R$ 250.000)" (32/70)
- `mission.divida_25.story` **Story**: "Um quarto da dívida! Dona Dilce prometeu uma carta quando você chegar lá, e ela não promete carta à toa: gasta selo." (116/220)

### `critico_m`
- `mission.critico_m.title` **Título**: "O paladar do Seu Arnaldo" (24/32)
- `mission.critico_m.task` **Tarefa**: "Concluir O paladar do Seu Arnaldo em Histórias da vila" (54/70)
- `mission.critico_m.story` **Story**: "Seu Arnaldo agora reclama no restaurante do hotel: do sal, do garfo e da vista. Talvez esteja na hora de ouvir com atenção." (123/220)

### `divida_50`
- `mission.divida_50.title` **Título**: "Metade da maré" (14/32)
- `mission.divida_50.task` **Tarefa**: "Pagar 50% da dívida (R$ 500.000)" (32/70)
- `mission.divida_50.story` **Story**: "Meio milhão. O gerente do banco prometeu um bolo cortado pela metade. Dona Dilce já avisou que fica com a parte maior." (118/220)

### `divida_75`
- `mission.divida_75.title` **Título**: "Quase dá para respirar" (22/32)
- `mission.divida_75.task` **Tarefa**: "Pagar 75% da dívida (R$ 750.000)" (32/70)
- `mission.divida_75.story` **Story**: "Faltam R$ 250.000. Dona Dilce já ensaia a dança da quitação. O banco pediu que seja longe do balcão." (100/220)

### `quarto_m`
- `mission.quarto_m.title` **Título**: "O quarto com vista" (18/32)
- `mission.quarto_m.task` **Tarefa**: "Concluir O quarto com vista em Histórias da vila" (48/70)
- `mission.quarto_m.story` **Story**: "Seu Severino anda cochichando com a vila inteira e para de falar quando você chega. Vá até ele antes que ele estoure de segredo." (128/220)

### `divida_100`
- `mission.divida_100.title` **Título**: "Dívida baixa: zero" (18/32)
- `mission.divida_100.task` **Tarefa**: "Quitar a dívida (R$ 1.000.000)" (30/70)
- `mission.divida_100.story` **Story**: "As últimas parcelas. O quarto está pronto, o barco está combinado e a vila não aguenta guardar segredo por muito mais tempo." (124/220)

**Nota ao tradutor:**
- Títulos das missões de dívida = títulos das cartas (25/50/75) e da tela final ("Dívida baixa: zero" é parte de "Maré Alta, dívida baixa: zero!"): usar as mesmas traduções.
- `divida_50` e `divida_75` reaproveitam as piadas dos antigos cartões de marco (bolo pela metade, dança da quitação): se já há tradução delas, reaproveitar.
- As tarefas "Concluir X em Histórias da vila" seguem o molde das missões atuais; "Histórias da vila" é o nome da página do celular.


## 7. Missões antigas reescritas (conflito com o final único)

Título e tarefa mantidos, salvo indicação. Revisei as outras 16 `story`: nenhuma tem erro de tratamento (nenhuma marca o gênero do jogador). Nada mais muda nelas.

### `chegada`
- `mission.chegada.story` **Story**: "Dona Dilce foi morar com as amigas do bingo e deixou o quiosque com você. Dê um nome ao negócio no celular: sua primeira maré começa aqui." (138/220)

### `marealta`
- `mission.marealta.story` **Story**: "A vila sonha com um hotel de verdade, e o banco também: hotel paga parcela mais depressa que coco. Construa o Grand Hotel Maré Alta." (132/220)

### `chef`
- `mission.chef.story` **Story**: "Seu Arnaldo agora reclama do tempero. Dizem que ele já fez um cozinheiro chorar só olhando para um pastel. Capriche nas receitas." (129/220)

### `fregueses`
- `mission.fregueses.story` **Story**: "A Prefeita Tuanny quer anunciar um número redondo na próxima festa da vila: sete mil vendas no quiosque. O discurso já está escrito; falta o número ser verdade." (160/220)

### `festa`
- `mission.festa.story` **Story**: "A dívida acabou. A vila preparou tudo em segredo e o barco já saiu. Vá à praia entre 20h e 23h30 para a Festa da Maré Alta." (123/220)

**Nota ao tradutor:**
- `chef` agora é a primeira aparição do Arnaldo na campanha; não dizer ainda que ele é crítico (a revelação é do capítulo `critico`).
- `fregueses`: "número redondo" = round number. `festa`: "o barco já saiu" — de quem é o barco não se diz (surpresa da festa).


## 8. Festa da Maré Alta: roteiro novo, tela final e créditos

Sete linhas no aviso, 7 s cada. Entre a linha 3 e a 4 abre a **carta de 100 %** (mesma tela das cartas; o roteiro espera o jogador fechar). A linha 2 da versão antiga ("Trinta anos sem descer esse morro") saiu: depois do capítulo `descanso` o Tibúrcio desce todo dia. Depois da linha 7 abre a tela final.

- `festa.line1` **Linha 1**: "A vila inteira desceu para a praia. Seu Tibúrcio veio de chinelo novo. Diz que é só para festa." (95/140)
- `festa.line2` **Linha 2**: "Prefeita Tuanny abre a Festa da Maré Alta cortando uma fita no meio da areia. Ninguém sabe de quê." (98/140)
- `festa.line3` **Linha 3 → abre a carta de 100 %**: "Seu Severino tira um envelope do bolso: "Ela mandou na frente. Leia logo, antes que eu chore."" (94/140)
- `festa.line4` **Linha 4**: "Uma luz de barco vem do mar, devagar. Seu Severino chora. Diz que é cebola. Não tem cebola." (91/140)
- `festa.line5` **Linha 5**: "O barco atraca no píer. Desce uma mala. Depois outra mala. Depois, Dona Dilce." (78/140)
- `festa.line6` **Linha 6**: "Dona Dilce: "Meu bem! Eu disse que você voltava. Agora quem voltou fui eu."" (75/140)
- `festa.line7` **Linha 7 → tela final**: "E o mar... calminho, calminho. Seu Tibúrcio: "Barriga cheia. Ele adora festa. Quem não adora?"" (94/140)

A linha 6 usa a fala `npc.dilce.arrival.a`; se o diretor preferir a b: "Dona Dilce: \"Meu bem! Recebeu minha carta? Eu cheguei antes da resposta, como sempre.\"". A linha 7 é a antiga linha 4, igual.

### Tela final
- `finale.title` **Título (mantido)**: "Maré Alta, dívida baixa: zero!" (30/40)
- `finale.text` **Texto (mantido)**: "R$ 1.000.000 pagos. Você cuidou do quiosque, da vila e de uma promessa de família. Agora o próximo sonho não vem com boleto." (124/220)
- `finale.quote` **Fala da Dona Dilce (mantida; agora ela está ali de verdade)**: "Dona Dilce: "Eu sabia que você conseguia. Agora vamos tomar um coco? O meu é por conta da casa, né?"" (100/140)
- `finale.button.continue` **Botão 1**: "Continuar na festa" (18/30)
- `finale.button.credits` **Botão 2 (créditos abrem ali mesmo)**: "Ver os créditos" (15/30)

### Créditos (no lugar da tela preta "FIM")
- `credits.direction` **Linha (mantida)**: "Ideia, direção e muita paciência: Sergio" (40/80)
- `credits.cast` **Elenco (revisada)**: "Elenco: Dona Dilce, Seu Severino, Padre Robson, Dona Cecília, Dona Roberta, Alana, Prefeita Tuanny, Seu Arnaldo, Seu Bené e Seu Tibúrcio" (136/160)
- `credits.sea` **Linha (mantida)**: "E o mar, no papel de si mesmo." (30/60)
- `credits.end` **Fecho dos créditos**: "...ou quase o fim. A maré continua, o quiosque também, e amanhã alguém leva a oferenda." (87/120)
- `credits.button` **Botão (mantido)**: "Continuar na praia" (18/30)
- `finale.mission_done` **Mensagem final (mantida)**: "Missão concluída: A Festa da Maré Alta. Resgate a recompensa no celular. E boa festa!" (85/140)

**Nota ao tradutor:**
- Linha 4: "Diz que é cebola. Não tem cebola." é a piada mais antiga da festa e volta no thanks 3 do capítulo `quarto`: mesma tradução nas duas.
- Linha 5: o ritmo "uma mala. Depois outra mala. Depois, Dona Dilce." é a piada (ela traz bagagem demais); manter as três batidas.
- "Dívida baixa: zero" faz par com "Maré Alta" (maré alta / dívida baixa). Se a língua não tiver o contraste alto/baixo, priorizar "dívida: zero". Fecho dos créditos: "amanhã alguém leva a oferenda" — pode ser o jogador ou o atendente; manter vago.


## 9. Epílogo

### Dona Dilce como moradora
- `epilogue.dilce.hotel1` **Varanda do hotel (dia)**: "Daqui de cima eu vejo o quiosque inteiro. Vejo também quem não limpou a mesa três. Só estou dizendo." (100/260)
- `epilogue.dilce.hotel2` **Varanda do hotel (dia)**: "O quarto é lindo, meu bem. A cama é tão macia que já perdi o bingo duas vezes." (78/260)
- `epilogue.dilce.hotel3` **Varanda do hotel (dia)**: "As meninas do bingo vêm me visitar no domingo. Avise a cozinha: elas comem como se fosse a última rodada." (105/260)
- `epilogue.dilce.kiosk4` **Quiosque (fim da tarde)**: "Quarenta anos atrás deste balcão, e ainda acho que coco gelado é a melhor invenção do mundo." (92/260)
- `epilogue.dilce.kiosk5` **Quiosque (fim da tarde)**: "Não estou trabalhando. Estou só sentada aqui, olhando. Se eu reparar em alguma coisa, foi sem querer." (101/260)
- `epilogue.dilce.kiosk6` **Quiosque (fim da tarde)**: "O Severino vem todo fim de tarde contar que construiu o píer sozinho. Eu deixo. Ele deixa eu deixar." (100/260)

### Moradores sobre a volta dela (2 cada)
- `epilogue.severino.1` **Severino**: "Ela já reclamou de três tábuas do píer. Três! Faz tempo que eu não fico tão feliz." (82/260)
- `epilogue.severino.2` **Severino**: "Agora eu pesco de manhã e levo bronca de tarde. A vida voltou ao normal." (72/260)
- `epilogue.robson.1` **Robson**: "A Dona Dilce voltou à missa das sete. Sentou na frente e cantou mais alto que o sino." (85/260)
- `epilogue.robson.2` **Robson**: "Ela me perguntou se o telhado aguenta. Eu disse que aguenta, graças a Deus. Ela riu." (84/260)
- `epilogue.cecilia.1` **Cecilia**: "Ela provou meu pastel e disse "está quase igual ao meu". Foi o maior elogio da minha vida." (90/260)
- `epilogue.cecilia.2` **Cecilia**: "Agora são duas cozinheiras dando palpite na vila. A cozinha ficou pequena, e eu nunca fui tão feliz." (100/260)
- `epilogue.roberta.1` **Roberta**: "Fiz uma rede com o nome dela bordado. Ela deitou, dormiu e disse que nem viu o bordado." (87/260)
- `epilogue.roberta.2` **Roberta**: "A Dona Dilce voltou e a vila voltou a ter horário: às cinco, todo mundo passa no quiosque." (90/260)
- `epilogue.alana.1` **Alana**: "Ela subiu até o farol comigo e contou que levava café para o meu avô. Esqueceu de contar que subia correndo." (108/260)
- `epilogue.alana.2` **Alana**: "O facho passa pela janela do quarto dela. Ela diz que dorme melhor com a luz piscando." (86/260)
- `epilogue.tuanny.1` **Tuanny**: "Inaugurei uma placa: "Bem-vinda de volta, Dona Dilce". Ela pediu para tirar. Inaugurei outra." (93/260)
- `epilogue.tuanny.2` **Tuanny**: "Pedi um discurso na praça. Ela falou três frases e ganhou mais palmas do que eu em quatro anos." (95/260)
- `epilogue.tiburcio.1` **Tiburcio**: "Ela subiu o morro para conhecer o cesto. Disse que o mar parece mais calmo. Eu disse que é porque ela voltou." (109/260)
- `epilogue.tiburcio.2` **Tiburcio**: "Desço para o quiosque às cinco e ela guarda um coco para mim. Trinta anos, e ninguém nunca tinha guardado." (106/260)
- `epilogue.arnaldo.1` **Arnaldo**: "A água de coco dela também é natural demais. Mas ela me ouve reclamar até o fim. Recomendo." (91/260)
- `epilogue.arnaldo.2` **Arnaldo**: "Ela me serviu um coco e disse: "Pode reclamar." Não consegui. Primeira vez na vida." (83/260)

### Página "Sonhos da vila"
- `phone.dreams.title` **Título**: "Sonhos da vila" (14/32)
- `phone.dreams.intro` **Apresentação**: "A dívida acabou; a vila, não. Estes são os sonhos que ainda dá para realizar, sem pressa e sem boleto." (102/140)

**Nota ao tradutor:**
- "Bem-vinda de volta, Dona Dilce" é feminino porque se refere à Dona Dilce (permitido: o gênero é dela, não do jogador). "sentada" (Dilce) idem.
- "Ele deixa eu deixar" (Dilce sobre Severino): os dois sabem e fingem; é o padrão dos marcos em uma frase. Manter a repetição do verbo.
- "sem boleto" repete a tela final ("o próximo sonho não vem com boleto"): mesma tradução de "boleto".


## 10. Oferenda delegada

- `offering.phone.header` **Cabeçalho no celular (Equipe)**: "Oferenda do dia" (15/32)
- `offering.phone.self` **Opção 1**: "Levar pessoalmente" (18/32)
- `offering.phone.delegate` **Opção 2**: "Mandar o atendente · R$ 60 por dia" (34/40)
- `offering.morning.done` **Mensagem da manhã (atendente levou)**: "O atendente subiu o morro com a oferenda de hoje. R$ 60 descontados. O mar agradece." (84/140)
- `offering.morning.no_money` **Faltou dinheiro**: "Hoje não deu para mandar o atendente: faltou dinheiro. A oferenda é com você, antes das 16h." (92/140)
- `offering.morning.no_staff` **Sem atendente**: "Sem atendente contratado, ninguém subiu o morro. A oferenda de hoje é com você, antes das 16h." (94/140)

**Seu Tibúrcio quando o jogador leva pessoalmente podendo delegar**
- `npc.tiburcio.self_offering.1` **Fala 1**: "Você de novo! Tem atendente e sobe assim mesmo. O mar repara nessas coisas. Eu também." (86/260)
- `npc.tiburcio.self_offering.2` **Fala 2**: "Veio pessoalmente? O mar vai ficar mal-acostumado, meu bem." (59/260)
- `npc.tiburcio.self_offering.3` **Fala 3**: "Senta um pouco, já que veio. A vista é a mesma, mas hoje tem companhia." (71/260)

**Seu Tibúrcio visitando o quiosque (fim da tarde)**
- `npc.tiburcio.kiosk.1` **Fala 1**: "Um coco, por favor. Não é oferenda, é para mim. O mar que espere a vez dele." (76/260)
- `npc.tiburcio.kiosk.2` **Fala 2**: "Daqui de baixo o mar parece menor. Não conta para ele que eu disse isso." (72/260)
- `npc.tiburcio.kiosk.3` **Fala 3**: "Vim conferir se o atendente subiu direitinho. Subiu. Agora vim só pelo coco." (76/260)

**Nota ao tradutor:**
- "Levar pessoalmente" evita "eu mesmo/eu mesma" (marcaria o gênero do jogador): nas outras línguas, também sem gênero ("Take it myself" serve em inglês; em línguas com gênero, usar "pessoalmente").
- "antes das 16h": é o horário da Onda; usar o formato de hora da língua. "atendente" = o cargo do celular (mesma tradução da Equipe).
- O mar continua sendo "ele", com vontades ("mal-acostumado" = spoiled).


## 11. Saudações dos moradores

- `npc.cecilia.greeting` **Dona Cecília (revisada; tirado "Bem-vindo de volta!")**: "Que bom ver você por aqui! As melhores receitas da vila carregam lembranças. A Dona Dilce nunca deixava ninguém sair do quiosque sem um sorriso." (144/260)
- `npc.alana.greeting` **Alana (revisada; tirado "Bem-vindo à vila!")**: "Oi! É bom ver o quiosque da família ganhando vida outra vez." (60/260)
- `npc.tuanny.greeting` **Prefeita Tuanny (nova)**: "Bom dia, bom dia! Prefeita Tuanny, a seu dispor. Precisando de alguma coisa, é só pedir. Se for coisa grande, eu inauguro." (122/260)
- `npc.arnaldo.greeting` **Seu Arnaldo (nova)**: "Hmpf. O guarda-sol está torto, a brisa está forte e o coco está bom demais. Bom dia." (84/260)

**Nota ao tradutor:**
- "a seu dispor" = at your service (neutro). Arnaldo: "Hmpf" é a mesma interjeição de HUM-007; "bom demais" é a reclamação dele (reclama até do que é bom).


## 12. HUD e celular

- `hud.debt` **Linha do HUD (sob o dinheiro)**: "Dívida: R$ {0} · {1} %" (22/40)
- `phone.letters.title` **Seção em Finanças**: "Cartas da Vó Dilce" (18/32)
- `phone.letters.empty` **Seção vazia (antes do primeiro marco; só o P.S.)**: "As próximas cartas chegam a cada quarto da dívida pago." (55/80)

**Nota ao tradutor:**
- {0} = valor restante já formatado; {1} = porcentagem PAGA (inteiro). Manter "·" como separador. "Cartas da Vó Dilce" é o nome que o contrato deu à seção (afetivo, por isso "Vó").


## 13. Vendedores dos negócios (hoje todos "Vendedor")

- `business.sorveteria.vendor_name` **sorveteria: nome**: "Giovana" (7/24)
- `business.sorveteria.vendor_greeting` **sorveteria: saudação**: "Sabor do dia: coco. O de ontem também. Amanhã, quem sabe, coco." (63/140)
- `business.aluguel.vendor_name` **aluguel: nome**: "Seu Valdir" (10/24)
- `business.aluguel.vendor_greeting` **aluguel: saudação**: "Prancha ou caiaque? Pode levar qualquer um, desde que traga de volta, com você em cima." (87/140)
- `business.surfe.vendor_name` **surfe: nome**: "Kauã" (4/24)
- `business.surfe.vendor_greeting` **surfe: saudação**: "A primeira aula é na areia. Ninguém se afoga na areia; eu já conferi." (69/140)
- `business.food_truck.vendor_name` **food_truck: nome**: "Dona Zezé" (9/24)
- `business.food_truck.vendor_greeting` **food_truck: saudação**: "Pastel saindo! Carne, queijo ou camarão? Escolhe rápido, que o óleo não espera." (79/140)
- `business.souvenir.vendor_name` **souvenir: nome**: "Marina" (6/24)
- `business.souvenir.vendor_greeting` **souvenir: saudação**: "A jangadinha é do Seu Severino, a cocada é da Dona Cecília e o embrulho caprichado é meu." (89/140)

**Nota ao tradutor:**
- Nomes próprios não se traduzem ("Seu Valdir", "Dona Zezé": usar a forma de tratamento do glossário, como em "Seu Severino").
- Sorveteria: a piada é ter só um sabor (coco); manter "coco" três vezes. Aluguel: "com você em cima" = sem cair da prancha.
- Lojinha: jangadinha e cocada já existem como produtos feitos por Severino e Cecília; manter os nomes dos produtos como no jogo.


## Lista de todas as strings novas ou alteradas (id estável)

Total de ids neste arquivo: **277** — novas ou alteradas: **265**; mantidas (listadas só para o arquivo ficar completo): **12**.

| id | situação | caracteres |
|---|---|---|
| `letter.home.title` | mantida | 19 |
| `letter.home.p1` | alterada (p1, p2) / mantida (resto) | 8 |
| `letter.home.p2` | alterada (p1, p2) / mantida (resto) | 227 |
| `letter.home.p3` | alterada (p1, p2) / mantida (resto) | 287 |
| `letter.home.p4` | alterada (p1, p2) / mantida (resto) | 224 |
| `letter.home.p5` | alterada (p1, p2) / mantida (resto) | 175 |
| `letter.home.p6` | alterada (p1, p2) / mantida (resto) | 71 |
| `letter.home.p7` | alterada (p1, p2) / mantida (resto) | 18 |
| `letter.home.sign` | alterada (p1, p2) / mantida (resto) | 8 |
| `letter.home.turn` | nova | 15 |
| `letter.home.button` | mantida | 15 |
| `letter.ps.p1` | nova | 72 |
| `letter.ps.p2` | nova | 104 |
| `letter.ps.p3` | nova | 180 |
| `letter.ps.p4` | nova | 164 |
| `letter.ps.sign` | nova | 8 |
| `debt.letter.25.title` | nova | 19 |
| `debt.letter.25.p1` | nova | 8 |
| `debt.letter.25.p2` | nova | 111 |
| `debt.letter.25.p3` | nova | 269 |
| `debt.letter.25.p4` | nova | 131 |
| `debt.letter.25.p5` | nova | 79 |
| `debt.letter.25.sign` | nova | 8 |
| `npc.severino.after25.a` | nova | 151 |
| `npc.severino.after25.b` | nova | 121 |
| `debt.letter.50.title` | nova | 14 |
| `debt.letter.50.p1` | nova | 8 |
| `debt.letter.50.p2` | nova | 59 |
| `debt.letter.50.p3` | nova | 265 |
| `debt.letter.50.p4` | nova | 89 |
| `debt.letter.50.p5` | nova | 137 |
| `debt.letter.50.sign` | nova | 8 |
| `npc.robson.after50.a` | nova | 126 |
| `npc.robson.after50.b` | nova | 115 |
| `debt.letter.75.title` | nova | 22 |
| `debt.letter.75.p1` | nova | 8 |
| `debt.letter.75.p2` | nova | 96 |
| `debt.letter.75.p3` | nova | 254 |
| `debt.letter.75.p4` | nova | 165 |
| `debt.letter.75.p5` | nova | 126 |
| `debt.letter.75.sign` | nova | 8 |
| `npc.cecilia.after75.a` | nova | 160 |
| `npc.cecilia.after75.b` | nova | 112 |
| `npc.tuanny.after75.a` | nova | 146 |
| `npc.tuanny.after75.b` | nova | 108 |
| `debt.letter.100.title` | nova | 16 |
| `debt.letter.100.p1` | nova | 8 |
| `debt.letter.100.p2` | nova | 79 |
| `debt.letter.100.p3` | nova | 259 |
| `debt.letter.100.p4` | nova | 181 |
| `debt.letter.100.p5` | nova | 81 |
| `debt.letter.100.sign` | nova | 8 |
| `npc.dilce.arrival.a` | nova | 61 |
| `npc.dilce.arrival.b` | nova | 72 |
| `debt.reminder.title` | nova | 22 |
| `debt.reminder.text` | nova | 81 |
| `chapter.rede.title` | nova | 24 |
| `chapter.rede.story` | nova | 209 |
| `chapter.rede.step1.text` | nova | 49 |
| `chapter.rede.step1.line_a` | nova | 120 |
| `chapter.rede.step1.line_b` | nova | 140 |
| `chapter.rede.step2.text` | nova | 35 |
| `chapter.rede.step2.line_a` | nova | 102 |
| `chapter.rede.step2.line_b` | nova | 128 |
| `chapter.rede.step3.text` | nova | 33 |
| `chapter.rede.step3.line_a` | nova | 124 |
| `chapter.rede.step3.line_b` | nova | 118 |
| `chapter.rede.thanks1` | nova | 98 |
| `chapter.rede.thanks2` | nova | 111 |
| `chapter.rede.thanks3` | nova | 100 |
| `chapter.rede.unlock` | nova | 39 |
| `chapter.farol.title` | nova | 19 |
| `chapter.farol.story` | nova | 215 |
| `chapter.farol.step1.text` | nova | 46 |
| `chapter.farol.step1.line_a` | nova | 139 |
| `chapter.farol.step1.line_b` | nova | 92 |
| `chapter.farol.step2.text` | nova | 42 |
| `chapter.farol.step2.line_a` | nova | 139 |
| `chapter.farol.step2.line_b` | nova | 103 |
| `chapter.farol.step3.text` | nova | 40 |
| `chapter.farol.step3.line_a` | nova | 104 |
| `chapter.farol.step3.line_b` | nova | 86 |
| `chapter.farol.thanks1` | nova | 113 |
| `chapter.farol.thanks2` | nova | 101 |
| `chapter.farol.thanks3` | nova | 107 |
| `chapter.farol.unlock` | nova | 36 |
| `chapter.descanso.title` | nova | 26 |
| `chapter.descanso.story` | nova | 204 |
| `chapter.descanso.step1.text` | nova | 38 |
| `chapter.descanso.step1.line_a` | nova | 85 |
| `chapter.descanso.step1.line_b` | nova | 83 |
| `chapter.descanso.step2.text` | nova | 33 |
| `chapter.descanso.step2.line_a` | nova | 102 |
| `chapter.descanso.step2.line_b` | nova | 80 |
| `chapter.descanso.step3.text` | nova | 31 |
| `chapter.descanso.step3.line_a` | nova | 109 |
| `chapter.descanso.step3.line_b` | nova | 106 |
| `chapter.descanso.thanks1` | nova | 98 |
| `chapter.descanso.thanks2` | nova | 113 |
| `chapter.descanso.thanks3` | nova | 94 |
| `chapter.descanso.unlock` | nova | 53 |
| `chapter.critico.title` | nova | 24 |
| `chapter.critico.story` | nova | 195 |
| `chapter.critico.step1.text` | nova | 45 |
| `chapter.critico.step1.line_a` | nova | 107 |
| `chapter.critico.step1.line_b` | nova | 89 |
| `chapter.critico.step2.text` | nova | 40 |
| `chapter.critico.step2.line_a` | nova | 112 |
| `chapter.critico.step2.line_b` | nova | 115 |
| `chapter.critico.step3.text` | nova | 38 |
| `chapter.critico.step3.line_a` | nova | 160 |
| `chapter.critico.step3.line_b` | nova | 146 |
| `chapter.critico.thanks1` | nova | 105 |
| `chapter.critico.thanks2` | nova | 80 |
| `chapter.critico.thanks3` | nova | 113 |
| `chapter.critico.unlock` | nova | 47 |
| `chapter.quarto.title` | nova | 18 |
| `chapter.quarto.story` | nova | 189 |
| `chapter.quarto.step1.text` | nova | 55 |
| `chapter.quarto.step1.line_a` | nova | 101 |
| `chapter.quarto.step1.line_b` | nova | 122 |
| `chapter.quarto.step2.text` | nova | 45 |
| `chapter.quarto.step2.line_a` | nova | 102 |
| `chapter.quarto.step2.line_b` | nova | 118 |
| `chapter.quarto.step3.text` | nova | 40 |
| `chapter.quarto.step3.line_a` | nova | 100 |
| `chapter.quarto.step3.line_b` | nova | 98 |
| `chapter.quarto.thanks1` | nova | 90 |
| `chapter.quarto.thanks2` | nova | 84 |
| `chapter.quarto.thanks3` | nova | 107 |
| `chapter.quarto.unlock` | nova | 43 |
| `chapter.pier.step1.line_a` | nova | 61 |
| `chapter.pier.step1.line_b` | nova | 80 |
| `chapter.pier.step2.line_a` | nova | 112 |
| `chapter.pier.step2.line_b` | nova | 77 |
| `chapter.pier.step3.line_a` | nova | 94 |
| `chapter.pier.step3.line_b` | nova | 95 |
| `chapter.pier.thanks1` | nova | 86 |
| `chapter.pier.thanks2` | nova | 98 |
| `chapter.pier.thanks3` | nova | 92 |
| `chapter.pier.unlock` | mantida | 38 |
| `chapter.prainha.step1.line_a` | nova | 107 |
| `chapter.prainha.step1.line_b` | nova | 107 |
| `chapter.prainha.step2.line_a` | nova | 97 |
| `chapter.prainha.step2.line_b` | nova | 103 |
| `chapter.prainha.step3.line_a` | nova | 97 |
| `chapter.prainha.step3.line_b` | nova | 87 |
| `chapter.prainha.thanks1` | nova | 97 |
| `chapter.prainha.thanks2` | nova | 94 |
| `chapter.prainha.thanks3` | nova | 89 |
| `chapter.prainha.unlock` | alterada | 18 |
| `chapter.sabores.step1.line_a` | nova | 104 |
| `chapter.sabores.step1.line_b` | nova | 71 |
| `chapter.sabores.step2.line_a` | nova | 101 |
| `chapter.sabores.step2.line_b` | nova | 105 |
| `chapter.sabores.step3.line_a` | nova | 100 |
| `chapter.sabores.step3.line_b` | nova | 89 |
| `chapter.sabores.thanks1` | nova | 84 |
| `chapter.sabores.thanks2` | nova | 95 |
| `chapter.sabores.thanks3` | nova | 92 |
| `chapter.sabores.unlock` | alterada | 17 |
| `chapter.carnaval.step1.line_a` | nova | 108 |
| `chapter.carnaval.step1.line_b` | nova | 102 |
| `chapter.carnaval.step2.line_a` | nova | 84 |
| `chapter.carnaval.step2.line_b` | nova | 117 |
| `chapter.carnaval.step3.line_a` | nova | 100 |
| `chapter.carnaval.step3.line_b` | nova | 83 |
| `chapter.carnaval.thanks1` | nova | 106 |
| `chapter.carnaval.thanks2` | nova | 97 |
| `chapter.carnaval.thanks3` | nova | 97 |
| `chapter.carnaval.unlock` | mantida | 56 |
| `mission.parcela.title` | nova | 18 |
| `mission.parcela.task` | nova | 51 |
| `mission.parcela.story` | nova | 161 |
| `mission.rede_m.title` | nova | 24 |
| `mission.rede_m.task` | nova | 54 |
| `mission.rede_m.story` | nova | 141 |
| `mission.farol_m.title` | nova | 19 |
| `mission.farol_m.task` | nova | 49 |
| `mission.farol_m.story` | nova | 136 |
| `mission.descanso_m.title` | nova | 26 |
| `mission.descanso_m.task` | nova | 56 |
| `mission.descanso_m.story` | nova | 116 |
| `mission.divida_25.title` | nova | 19 |
| `mission.divida_25.task` | nova | 32 |
| `mission.divida_25.story` | nova | 116 |
| `mission.critico_m.title` | nova | 24 |
| `mission.critico_m.task` | nova | 54 |
| `mission.critico_m.story` | nova | 123 |
| `mission.divida_50.title` | nova | 14 |
| `mission.divida_50.task` | nova | 32 |
| `mission.divida_50.story` | nova | 118 |
| `mission.divida_75.title` | nova | 22 |
| `mission.divida_75.task` | nova | 32 |
| `mission.divida_75.story` | nova | 100 |
| `mission.quarto_m.title` | nova | 18 |
| `mission.quarto_m.task` | nova | 48 |
| `mission.quarto_m.story` | nova | 128 |
| `mission.divida_100.title` | nova | 18 |
| `mission.divida_100.task` | nova | 30 |
| `mission.divida_100.story` | nova | 124 |
| `mission.chegada.story` | alterada | 138 |
| `mission.marealta.story` | alterada | 132 |
| `mission.chef.story` | alterada | 129 |
| `mission.fregueses.story` | alterada | 160 |
| `mission.festa.story` | alterada | 123 |
| `festa.line1` | nova | 95 |
| `festa.line2` | nova | 98 |
| `festa.line3` | nova | 94 |
| `festa.line4` | nova | 91 |
| `festa.line5` | nova | 78 |
| `festa.line6` | nova | 75 |
| `festa.line7` | mantida | 94 |
| `finale.title` | mantida | 30 |
| `finale.text` | mantida | 124 |
| `finale.quote` | mantida | 100 |
| `finale.button.continue` | alterada | 18 |
| `finale.button.credits` | alterada | 15 |
| `credits.direction` | mantida | 40 |
| `credits.cast` | alterada | 136 |
| `credits.sea` | mantida | 30 |
| `credits.end` | alterada | 87 |
| `credits.button` | mantida | 18 |
| `finale.mission_done` | mantida | 85 |
| `epilogue.dilce.hotel1` | nova | 100 |
| `epilogue.dilce.hotel2` | nova | 78 |
| `epilogue.dilce.hotel3` | nova | 105 |
| `epilogue.dilce.kiosk4` | nova | 92 |
| `epilogue.dilce.kiosk5` | nova | 101 |
| `epilogue.dilce.kiosk6` | nova | 100 |
| `epilogue.severino.1` | nova | 82 |
| `epilogue.severino.2` | nova | 72 |
| `epilogue.robson.1` | nova | 85 |
| `epilogue.robson.2` | nova | 84 |
| `epilogue.cecilia.1` | nova | 90 |
| `epilogue.cecilia.2` | nova | 100 |
| `epilogue.roberta.1` | nova | 87 |
| `epilogue.roberta.2` | nova | 90 |
| `epilogue.alana.1` | nova | 108 |
| `epilogue.alana.2` | nova | 86 |
| `epilogue.tuanny.1` | nova | 93 |
| `epilogue.tuanny.2` | nova | 95 |
| `epilogue.tiburcio.1` | nova | 109 |
| `epilogue.tiburcio.2` | nova | 106 |
| `epilogue.arnaldo.1` | nova | 91 |
| `epilogue.arnaldo.2` | nova | 83 |
| `phone.dreams.title` | nova | 14 |
| `phone.dreams.intro` | nova | 102 |
| `offering.phone.header` | nova | 15 |
| `offering.phone.self` | nova | 18 |
| `offering.phone.delegate` | nova | 34 |
| `offering.morning.done` | nova | 84 |
| `offering.morning.no_money` | nova | 92 |
| `offering.morning.no_staff` | nova | 94 |
| `npc.tiburcio.self_offering.1` | nova | 86 |
| `npc.tiburcio.self_offering.2` | nova | 59 |
| `npc.tiburcio.self_offering.3` | nova | 71 |
| `npc.tiburcio.kiosk.1` | nova | 76 |
| `npc.tiburcio.kiosk.2` | nova | 72 |
| `npc.tiburcio.kiosk.3` | nova | 76 |
| `npc.cecilia.greeting` | alterada | 144 |
| `npc.alana.greeting` | alterada | 60 |
| `npc.tuanny.greeting` | nova | 122 |
| `npc.arnaldo.greeting` | nova | 84 |
| `hud.debt` | nova | 22 |
| `phone.letters.title` | nova | 18 |
| `phone.letters.empty` | nova | 55 |
| `business.sorveteria.vendor_name` | nova | 7 |
| `business.sorveteria.vendor_greeting` | nova | 63 |
| `business.aluguel.vendor_name` | nova | 10 |
| `business.aluguel.vendor_greeting` | nova | 87 |
| `business.surfe.vendor_name` | nova | 4 |
| `business.surfe.vendor_greeting` | nova | 69 |
| `business.food_truck.vendor_name` | nova | 9 |
| `business.food_truck.vendor_greeting` | nova | 79 |
| `business.souvenir.vendor_name` | nova | 6 |
| `business.souvenir.vendor_greeting` | nova | 89 |

## Strings antigas que deixam de existir

- `debt.json → intro` (cartão "Uma carta de Dona Dilce": título + "Meu bem, o quiosque é seu. A dívida também…" + "Pague quando puder…" + "Com carinho, Dona Dilce") → substituído por `letter.ps.*` e `debt.reminder.*`.
- `debt.json → milestones` 25/50/75 (textos dos cartões de 14 s: "extrato com os dois olhos", "bolo pela metade", "dança da quitação") → substituídos pelas cartas `debt.letter.25/50/75.*` (as piadas do bolo e da dança foram para `mission.divida_50/75.story`). Os títulos continuam como `debt.letter.*.title`.
- `debt.json → campaign_texts` inteiro (sem consumidor).
- Carta da casa: "Meu neto," e "Ainda me lembro de você pequeno, correndo pela areia…" (trocados em `letter.home.p1/p2`).
- `mission.*.story` antigos de `chegada`, `marealta`, `chef`, `fregueses`, `festa`.
- Frase genérica de capítulo concluído "Obrigado pela ajuda com \"<título>\". A vila não vai esquecer." → `chapter.*.thanks1..3`.
- `unlock` de `prainha`: "Prainha do Oeste aberta + Escolinha de surfe"; `unlock` de `sabores`: "Barraca do pastel + dica da moqueca".
- Festa: linha 2 antiga ("Trinta anos sem descer esse morro. A trilha encolheu ou fui eu que cresci?"), linha 3 antiga ("Prefeita Tuanny anuncia a Festa da Maré Alta. Seu Severino chora…", dividida em `festa.line2` e `festa.line4`) e linha 5 ("Vovó Dilce mandou um áudio de sete minutos…").
- Tela preta "FIM" e "...ou quase. A maré continua, o quiosque também, e amanhã tem oferenda." → `credits.end`.
- Créditos: "Elenco: Vovó Dilce, Seu Severino, Padre Robson, Dona Cecília, Prefeita Tuanny e Seu Tibúrcio" → `credits.cast`.
- Botões da tela final "Continuar no resort" e "Créditos" (que saía para o menu) → `finale.button.*`.
- Saudações antigas da Dona Cecília ("Bem-vindo de volta!…") e da Alana ("Bem-vindo à vila!…").
- Rótulo "Vendedor" dos cinco negócios (pode ficar só como reserva no código).
- Já previsto no contrato (não são textos meus, só confirmo): `DEF → quests`, `intro_bus.json`.

## Pontos para o diretor (não resolvidos por mim)

- Ainda com "sua avó Dilce" na boca de morador, fora do escopo pedido: saudação do Seu Severino ("Eu conheci sua avó Dilce…"), do Padre Robson ("Sua avó Dilce fez isso…") e da Dona Roberta ("Sua avó Dilce sempre disse…"). Pela convenção seria "a Dona Dilce"; não mexi porque não têm erro de gênero.
- Cartão-postal 5 da abertura: "Bem-vinda, bem-vindo à Maré Alta." — não foi pedido; sugestão neutra: "A Maré Alta estava esperando por você."
- HUD da chegada: "A vila parecia menor… e o mar, do tamanho das minhas lembranças." e o pedido "Entre na casa e leia a carta da avó Dilce" estão ok (narrador próximo pode dizer "avó").
- A carta de 100 % precisa abrir DENTRO da festa (o marco de 100 % acontece antes, ao pagar). Sugestão ao programador: ao quitar, não mostrar a carta; ela fica reservada para a linha 3 da festa e depois entra em "Cartas da Vó Dilce".
