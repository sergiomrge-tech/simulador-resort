# Mapa da campanha principal — Coconut Simulator (Maré Alta Resort)

Levantamento SOMENTE DE LEITURA, 12/11/2026, branch `codex/ue58-migration`. Vale o código e os dados; onde os documentos
divergem, a divergência está anotada. Caminhos relativos a `D:/Projetos/MareAltaUE58`. Abreviações:
`DEF` = `unreal/MareAlta/Content/Data/definitions.json`, `SRC` = `unreal/MareAlta/Source/MareAlta/`.
Nada foi jogado nem testado: tudo vem de leitura de código, dados e documentos. O que não pôde ser confirmado está
marcado "não verificado".

Estado de build lido: `DEF → demo = true` (build de demonstração; o jogo completo é `demo = false`). Dia de jogo =
08h–24h = 16 min reais (1 min de jogo por segundo; `SRC/MareGame.cpp:3250`, `docs/ue58/BALANCEAMENTO.md:156`).
O save novo começa às 6h30 do dia 1 com R$ 150 (`Content/Data/default_save.json`).

---

## 1. Abertura (do primeiro segundo ao controle livre)

Linha do tempo real, em ordem:

1. **Menu/título** vivo (câmera orbitando a ilha; logo "Coconut Simulator", subtítulo "Maré Alta Resort") — `Content/Data/title.json`, `SRC/MareTitle.cpp`.
   O subtítulo do menu principal diz "O quiosque da avó Dilce espera por você." (`SRC/MareGame.cpp:1961`).
2. **Novo jogo** em um slot: `NewGame` marca `ue_intro_stage = 0` (`SRC/MareSimulation.cpp:83`).
3. **5 cartões-postais** (9 s cada, Espaço avança, Esc pula) — `title.json → story`, `SRC/MareTitle.cpp:96-135`, chamado em `SRC/MareGame.cpp:3225-3235`.
   Textos exatos:
   - "Por quarenta verões, Dona Dilce abriu o quiosque da praia antes do sol."
   - "Um dia chegou uma carta: \"Meu bem, o quiosque agora é seu.\""
   - "Você pegou o primeiro barco para a ilha."
   - "A vila parecia menor... e o mar, do tamanho das lembranças."
   - "Bem-vinda, bem-vindo à Maré Alta."
4. **Chegada de barco** (`SRC/MareIntro.cpp`): câmera no píer vê a lancha vindo do mar aberto; depois câmera na proa. A lancha navega 16 s
   (`SailSeconds`, `MareIntro.h:47`), atraca na ponta do píer, o herói desembarca em 5 s (`DisembarkSeconds`). Um "Barqueiro" (sem fala) fica ao leme e
   leva o barco de volta (`MareIntro.cpp:93`, `:196-215`). E avança/pula a cena. Som: `boat_engine`. HUD durante a cena (`SRC/MareGame.cpp:3101`):
   "Chegada" / "A vila parecia menor... e o mar, do tamanho das minhas lembranças." / "E · avançar". Sem diálogo falado.
   Ao fim grava `ue_intro_stage = 1`.
5. **Controle livre no píer**. HUD (`MareGame.cpp:3103-3105`): "Missões" / "Entre na casa e leia a carta da avó Dilce". Não há marcador
   ou seta específica da casa no código lido (a bússola lista lugares; não verificado se a casa aparece nela).
6. **Carta na casa** (mesa pequena da sala, `(4435,2237,58)`; alvo `IntroLetter`, rótulo "Carta da avó Dilce"; `MareIntro.cpp:47-54`).
   `ReadLetter` (`MareIntro.cpp:208`). Título "Uma carta para você"; botão "Guardar a carta"; a carta fica relegível. Texto exato:

   > Meu neto,
   >
   > Se você está lendo esta carta, chegou à nossa vila. Ainda me lembro de você pequeno, correndo pela areia enquanto eu abria o quiosque. Você dizia que o mar tinha cheiro de aventura. Eu respondia que também tinha cheiro de casa.
   >
   > Nosso negócio começou com um balcão, alguns cocos e a vontade de acolher quem chegava. Nem todos os dias foram fáceis. Quando o vento virou, foram as pessoas da vila que nos ajudaram a continuar. Cada cadeira guarda uma conversa; cada freguês deixou um pedacinho de sua história conosco.
   >
   > Hoje minhas mãos precisam descansar um pouco mais, mas o sonho da família ainda tem muito caminho pela frente. Quero passar o quiosque para você. Abra as portas, conheça nossos vizinhos e faça deste lugar também o seu lugar.
   >
   > Se puder, ajude o negócio a crescer. Mas lembre-se de que o que construímos de mais valioso nunca coube em uma caixa registradora: foi o carinho com que recebemos cada pessoa.
   >
   > Não tenha pressa. Mesmo de longe, vou torcer por você a cada nova maré.
   >
   > Com todo meu amor,
   > Vó Dilce

   Ao guardar grava `ue_intro_stage = 2` (`MareIntro.cpp:222`). **A carta da casa não menciona a dívida.**
7. **Celular → Quiosque → "Dê um nome ao quiosque da família:"** (campo pré-preenchido "Maré Alta", botão "Criar empresa";
   `MareGame.cpp:275-282`). Antes de ler a carta o celular recusa e diz: "Primeiro, entre na casa e leia a carta que sua avó Dilce deixou para você." HUD
   (`MareGame.cpp:3106`): "Comece aqui: B · Celular → Quiosque → Criar empresa".
8. `CreateCompany` (`MareSimulation.cpp:114-122`) cria a empresa, cria a dívida (`EnsureDebt`) e diz: "Empresa criada! Para abrir, vá ao quiosque na praia e use a placa vermelha FECHADO do balcão."
9. **Carta da dívida** (`MareDebt.cpp:162-172`, `debt.json → intro`): vira um *cartão de dica* no canto inferior esquerdo por 14 s (não é tela de carta),
   exibido quando o celular fecha e não há outra dica. Texto exato (3 linhas):
   - Título: "Uma carta de Dona Dilce"
   - "Meu bem, o quiosque é seu. A dívida também: R$ 1.000.000. Eu ia contar no almoço, mas o barco chegou primeiro."
   - "Pague quando puder, pelo celular. Não tem juros nem parcela obrigatória. Primeiro cuide do quiosque; ninguém trabalha bem sem coco gelado."
   - "Com carinho, Dona Dilce"
10. **Primeira missão** "Uma nova maré" (`chegada`) é concluída ao criar a empresa; a recompensa de R$ 40 exige clicar "Concluir" no celular.
11. **HUD guia o próximo passo** (`MareGame.cpp:3107-3114`): "Abra o quiosque: vá até a praia (siga \"Quiosque\" na bússola) e aperte E na placa vermelha FECHADO do balcão". Antes das 8h a abertura fica "marcada".
12. **Dicas de primeira vez** (`Content/Data/tutorial.json`, 14 s cada, uma vez por save): celular, placa do quiosque, atender no balcão, geladeira, pagamento, etc. (≈55 dicas; lista completa no arquivo).
    A dica de pagamento ensina o troco/maquininha (`MarePayment.cpp`).

**Divergências com o documento de abertura** (`docs/ue58/ABERTURA_UMA_NOVA_MARE.md`): o documento diz ônibus, "casa do avô", carta "Meu neto … Vô";
o código usa barco, avó, "Vó Dilce" (a assinatura mudou, o vocativo "Meu neto" continua masculino). O ônibus (`Content/Data/intro_bus.json`) sobrou como dado, sem uso
na cena (`MareIntro.cpp` carrega a lancha). A carta da dívida usa "Meu bem" (neutro); a carta da casa, "Meu neto".

---

## 2. Objetivo central: a dívida de Dona Dilce

| Item | Valor / regra | Onde |
|---|---|---|
| Valor | R$ 1.000.000 (`principal`), congelado em centavos no save ao criar a empresa | `debt.json`, `SRC/MareDebt.cpp:31-52` |
| Juros / parcela | zero / zero; sem multa ou bloqueio | `debt.json` |
| Como paga | Celular → Finanças → cartão "Dívida de Dona Dilce": botões de valores, "o máximo que der", campo livre, "Confirmar" | `SRC/MareGame.cpp:796-835`, `MareDebt.cpp:79-115` |
| Recibo | "Pagamento de R$ {0} recebido. Restam R$ {1}. Um coco de cada vez!" | `debt.json → phone.receipt` |
| Lembrete | a cada 7 dias sem pagamento, ao dormir, dica "Recado do banco": "Faz uma semana sem pagamento. O gerente mandou lembranças e perguntou se aceita coco como garantia. Você paga quando puder." | `MareDebt.cpp:151`, `MareSimulation.cpp:529` |
| Marcos | 25 % "Um quarto mais leve": "R$ 250.000 pagos! Dona Dilce diz que já consegue olhar o extrato com os dois olhos abertos."; 50 % "Metade da maré": "R$ 500.000 pagos! O gerente trouxe um bolo pela metade. Dona Dilce ficou com a parte maior."; 75 % "Quase dá para respirar": "R$ 750.000 pagos! Dona Dilce já ensaia a dança da quitação. O banco pediu que seja longe do balcão." Cada um é só um cartão de dica de 14 s, sem dinheiro/fama | `debt.json → milestones`, `MareGame.cpp:3093-3094` |
| Tela final | só no jogo completo (`!IsDemo`) com saldo zero e celular fechado. Folha de caderno: título "Maré Alta, dívida baixa: zero!"; "R$ 1.000.000 pagos. Você cuidou do quiosque, da vila e de uma promessa de família. Agora o próximo sonho não vem com boleto."; fala "Dona Dilce: Eu sabia que você conseguia. Agora vamos tomar um coco? O meu é por conta da casa, né?". Botões "Continuar no resort" e "Créditos" | `debt.json → finale`, `MareGame.cpp:1789-1803, 2284-2294, 3095` |
| Demo | pagamento limitado a R$ 250.000 no total (`demo_payment_cap`); mensagem "Na demo, você pode abater até R$ {0}. O restante acompanha a história no jogo completo." Final nunca aparece na demo | `MareDebt.cpp:57-62, 79-90` |
| Onde o jogador VÊ o objetivo | (a) celular, aba Finanças (cartão de saldo, barra de lápis, "Você já pagou R$ X de R$ Y"); (b) dicas únicas (carta, 3 marcos, lembrete); (c) dicas `phone:finance` ("A dívida é o objetivo da história.") e `phone:debt`. **O HUD fixo não mostra saldo nem barra da dívida** (só lista a missão da campanha, até 2 pedidos da vila, "Próximo desbloqueio" e passo de capítulo) | `MareGame.cpp:3100-3160`, `tutorial.json` |
| Conquistas ligadas | `CC_DEBT_FIRST/25/50/75/FREE` em `achievements.json`, sem consumidor C++ ("nenhuma integração Steam ativa") | `achievements.json → _doc` |
| QA | `mare.QA paydebt <reais>\|all` paga a dívida para ver o final | `MareGame.cpp:2714-2717` |

**Há outro fim de jogo?** Sim, um segundo: a **Festa da Maré Alta** (última missão da campanha, só no jogo completo): ver seções 3, 8 e 9. Os dois finais são independentes
(a festa "não exige saldo zero": `DIVIDA_DA_AVO.md:28`; `debt.json → campaign_texts.festa`).
**Game over** existe, mas é o do tsunami (seção 8), não da dívida. Dívida não gera derrota em nenhum caso.

**Divergência de documentos:** `debt.json → _doc.status` ("PROPOSTA v1: ainda não há consumidor C++"), `DIVIDA_DA_AVO.md:5` ("Proposta, não implementada") e
`BALANCEAMENTO.md:1` estão desatualizados: o consumidor existe (`MareDebt.cpp`, UI no celular, final, testes). `debt.json → campaign_texts` (substituir `story` das
missões chegada/marealta/festa) **não tem consumidor no código** (grep: nenhum uso); os textos novos foram copiados à mão para `definitions.json`.

---

## 3. Sequência de missões da campanha (21 etapas, estritamente lineares)

Mecânica (`SRC/MareSimulation.cpp:474-486`, `MareGame.cpp:888-899`, `3113-3140`): a campanha é uma fila: só a missão de índice `stage` pode ser concluída;
o jogador precisa abrir o celular → Missões → "Concluir · R$ X" para receber a recompensa (dinheiro em R$; não há fama nem item). Ao concluir, `stage + 1`.
Missões cuja condição já foi cumprida antes de chegar a vez aparecem completas ("— 1/1 · concluir no celular").
O que o jogador VÊ: título + tarefa (`task`) + contador. **O campo `story` das missões (as frases de humor/enredo) não é exibido em nenhuma tela do código** (celular e HUD mostram
`title` e `task`: `MareGame.cpp:895-897`, `3126-3129`). As 21 frases `story` abaixo são, até onde li, texto morto. (Verificado por busca no código: `TEXT("story")` só é lido
nos capítulos da vila, no passeio, na trilha e no cartão-postal da abertura; não verificado em jogo.)
Demo: a campanha para na missão `marealta` (primeira que exige expansão `full_game`); HUD diz "Uma nova maré · a história continua no jogo completo" e a página Missões, "Fim da demo: a história continua no jogo completo, com o Grand Hotel." (`SRC/MareSimulation.cpp:902-909`). Missões 1–14 são da demo; 15–21 só no jogo completo.

Soma de recompensas: campanha R$ 9.400 (demo: R$ 2.400 nas 14 primeiras); missões paralelas R$ 280.

| # | id | Título | Tarefa mostrada | Condição (kind/qty) | Recompensa | Dia mediano (modelo, perfil médio) |
|---|---|---|---|---|---|---|
| 1 | chegada | Uma nova maré | Criar sua empresa no celular | company 1 | R$ 40 | 1 |
| 2 | portas | Portas abertas | Abrir o quiosque pela placa vermelha | open 1 (ou 1 venda) | R$ 30 | 1 |
| 3 | primeiros | O sabor da primeira manhã | Vender 8 produtos no quiosque | sales 8 | R$ 100 | 1 |
| 4 | mesas | Um lugar para ficar | Comprar Mesas e guarda-sóis | expansão `kiosk_tables` | R$ 80 | 1 |
| 5 | equipe | Uma parceria de verdade | Contratar o atendente único | staff atendente | R$ 80 | 1 |
| 6 | morro | O velho do morro | Subir a trilha e conversar com o Seu Tibúrcio | elder (summit.met) | R$ 120 | 2 |
| 7 | oferendas | Três dias sem Onda | Levar 3 oferendas ao cesto do Seu Tibúrcio | offerings 3 (1 por dia; a cortesia do 1º dia não conta) | R$ 200 | 4 |
| 8 | comunidade | O quiosque e o mar | Concluir O píer do Seu Severino em Histórias da vila | capítulo `pier` | R$ 150 | 4 |
| 9 | encontro | O encontro dos viajantes | Comprar o Bar do Coqueiro | expansão `bar` | R$ 200 | 4 |
| 10 | hospedar | Fique mais um dia | Abrir a pousada | expansão `pousada` | R$ 300 | 5 |
| 11 | verao | Um verão inesquecível | Construir a piscina | expansão `pool` | R$ 400 | 6 |
| 12 | prainha_m | A prainha secreta | Concluir A prainha do Padre Robson… | capítulo `prainha` | R$ 200 | 6 |
| 13 | sabores_m | Sabores da Dona Cecília | Concluir Os sabores da Dona Cecília… | capítulo `sabores` | R$ 200 | 7 |
| 14 | carnaval_m | Carnaval na areia | Concluir O carnaval da Prefeita Tuanny… | capítulo `carnaval` | R$ 300 | 8 (fim da demo) |
| 15 | marealta | A Maré Alta da vila | Construir o Grand Hotel Maré Alta | expansão `grand_hotel` (**full_game**) | R$ 1.000 | 25 |
| 16 | salao | O salão da vila | Comprar o salão de jogos | expansão `salao_jogos` | R$ 500 | 26 |
| 17 | chef | Cardápio de chef | Melhorar receitas do quiosque 20 vezes | recipes 20 | R$ 800 | 26 |
| 18 | postal | Cartão-postal | Fazer 40 melhorias de personalização | custom 40 | R$ 1.000 | 26 |
| 19 | lenda | Lenda da costa | Chegar à fama máxima (nível 10) | fame 10 | R$ 1.200 | 26 |
| 20 | fregueses | Sete mil vendas | Chegar a 7.000 vendas no quiosque | sales 7000 | R$ 1.500 | 75 |
| 21 | festa | A Festa da Maré Alta | Ir à praia entre 20h e 23h30 para a Festa da Maré Alta | finale (evento na praia) | R$ 1.000 | 76 |

Textos `story` (não exibidos), copiados do JSON para referência:
- chegada: "Dona Dilce foi morar com as amigas do bingo. Deixou o quiosque, muito carinho e uma dívida de R$ 1.000.000. Dê um nome ao negócio no celular: sua primeira maré começa aqui."
- portas: "Primeiro expediente! A placa vermelha do balcão está esperando há anos. Vire-a e veja a praia descobrir que o quiosque voltou."
- primeiros: "Os primeiros fregueses chegam desconfiados (\"isso aqui não era da Dona Dilce?\"). Anote, retire pronto e entregue no balcão até eles virarem fregueses fiéis."
- mesas: "O povo está tomando água de coco em pé, na areia, igual pinguim. Compre mesas e guarda-sóis e transforme a parada rápida em ponto de encontro."
- equipe: "Você não pode atender, pescar, fotografar o farol e conversar com a vila inteira ao mesmo tempo. Contrate alguém de confiança para o balcão."
- morro: "Os pescadores juram que tem um velho gritando lá do alto do morro desde a semana passada. Suba a trilha atrás da vila e veja se ele precisa de ajuda. Ou de um pastel."
- oferendas: "Seu Tibúrcio jura que o mar está de olho em você. O mar não confirmou, mas também não negou. Leve a oferenda do dia até o cesto dele."
- comunidade: "Seu Severino diz que o píer está \"quase\" caindo. Os pescadores dizem que já caiu duas vezes. Ajude a terminar a história dele."
- encontro: "Turistas perguntam todo dia se tem drink. A resposta \"tem coco\" já não convence ninguém. Abra o Bar do Coqueiro."
- hospedar: "Os visitantes querem ficar mais um dia e estão dormindo na rede do Seu Severino. Ele não gostou. Abra a pousada."
- verao: "Os hóspedes descansam, mas pedem um lugar para boiar sem medo de siri. Construa a piscina."
- prainha_m: "Padre Robson descobriu uma prainha escondida e quer que o mundo conheça. Mas só depois da missa. E do almoço."
- sabores_m: "Dona Cecília garante que tem receitas que fariam o mar chorar de emoção. Ajude a colocá-las no cardápio."
- carnaval_m: "A Prefeita Tuanny quer o maior carnaval de praia da região. O orçamento é pequeno, a empolgação é gigante."
- marealta: "Esta etapa pertence ao jogo completo. O Grand Hotel pode ajudar a quitar a dívida de Dona Dilce; ela já pediu um quarto com vista e desconto de família."
- salao: "Os hóspedes do hotel jogam dominó no corredor e já quebraram dois vasos. Dê a eles um salão de jogos de verdade."
- chef: "Um crítico de comida vem aí. Dizem que ele já fez um chef chorar só olhando para um pastel. Capriche nas receitas."
- postal: "Uma revista de viagem quer o resort na capa. O fotógrafo avisou que só fotografa \"coisa bonita\". Personalize a vila."
- lenda: "Seu Severino já conta para os turistas que foi ele quem ensinou você a abrir coco. Fique famoso de verdade, antes que ele exagere mais."
- fregueses: "A prefeita Tuanny prometeu a festa quando o quiosque chegasse a 7.000 vendas. Dona Dilce já separou a roupa do bingo: diz que serve para festa também."
- festa: "A vila quer comemorar o resort, mas festa não quita dívida. Dona Dilce manda carinho lá do bingo. Vá à praia entre 20h e 23h30 para celebrar; a conta continua sendo um coco de cada vez."

**Missões paralelas** ("Pedidos da vila", `DEF → side_missions`, sem ordem, sem requisito; a HUD mostra até 2 por vez; mesmo resgate manual):

| id | Título | Tarefa | Condição | Recompensa |
|---|---|---|---|---|
| pescador | Um dia com os pescadores | Pescar 5 peixes no píer | fish 5 | R$ 80 |
| gelados | O verão pede sorvete | Vender 12 sorvetes no quiosque | icecream 12 | R$ 100 |
| faroleiro | Cartão-postal da vila | Fotografar o farol com P | photo `farol` | R$ 50 |
| entardecer | As cores do entardecer | Fotografar o pôr do sol com P | photo `por_do_sol` | R$ 50 |

Bloco `DEF → quests` (4 pedidos de moradores: `cocos_rita`, `frutas_lourdes`, `paes_padre`, `peixe_ze`, com giver/reward): **nenhum código C++ lê `quests`** (grep) → conteúdo inerte. "Seu Zé" e "Lourdes" são nomes antigos (renomeados; `docs/CHECKLIST_PEDIDOS.md:70`).
Metas semanais herdadas do Godot (`default_save.json → prog.goals`, `tree`, `medals`) também não têm consumidor C++ (grep).

"Próximo desbloqueio" (HUD e celular, `SRC/MareLeisure.cpp:150-171`): "Próximo desbloqueio: <expansão mais barata cujos pré-requisitos estão comprados> · faltam R$ X e fama N e conclua a história \"…\"" ou "· já dá para comprar no celular". Ignora expansões `full_game` na demo; some quando tudo da demo está comprado.

---

## 4. Capítulos da vila (4, em sequência obrigatória: pier → prainha → sabores → carnaval)

Dados: `DEF → chapters`. Código: `SRC/MareSimulation.cpp:349-400` (progresso/avanço), `SRC/MareVillageWorld.cpp:279-318` (diálogo), `MareGame.cpp:902-914` (celular "Histórias da vila").
Mecânica: cada capítulo tem 3 passos; o avanço é PRESENCIAL: o jogador conversa (E) com quem pediu (campo `giver` = nome exato do morador) e clica no botão ("Entregar N do estoque", "Doar R$ N", "Concluir passo",
ou "Comprar N no mercadinho" quando falta item). A história (`story`) só é falada no passo 1 (`StepIndex==0`); nos passos 2 e 3 só aparece "<título> · passo N/3: <texto do passo> (x/y)". Ao concluir o capítulo: recompensa em dinheiro, **+80 de fama**, e mensagem "Capítulo concluído! Liberado: <unlock>". O capítulo seguinte só abre após o anterior. Morador do capítulo concluído diz: "Obrigado pela ajuda com \"<título>\". A vila não vai esquecer."

| id | Título / quem pede | Fala de abertura (`story`) | Passos (texto mostrado, condição) | Recompensa | Texto de "libera" (`unlock`) | Libera de fato (código) |
|---|---|---|---|---|---|---|
| pier | O píer do Seu Severino — **Seu Severino** | "O píer está caindo aos pedaços. Seu Severino quer reformá-lo para os barcos e para alugar pranchas." | 1) "Levar 4 peixes para o almoço dos pescadores" (entregar 4 `peixe` do estoque); 2) "Entregar 15 produtos no quiosque durante esta etapa" (conta só com o passo ativo); 3) "Doar R$ 150 para as tábuas novas" | R$ 200 + 80 fama | "Aluguel de pranchas e caiaques no píer" | `businesses.aluguel.chapter = pier` (compra liberada) |
| prainha | A Prainha do Oeste — **Padre Robson** | "Depois das pedras existe uma prainha esquecida. Padre Robson quer reabrir a trilha para a comunidade." | 1) "Chegar à fama \"Ponto da praia\"" (fama 3); 2) "Fotografar o farol (tecla P)"; 3) "Levar 6 cocos para o mutirão" | R$ 300 + 80 fama | "Prainha do Oeste aberta + Escolinha de surfe" | `businesses.surfe.chapter = prainha`. "Prainha aberta": **nenhum código C++ trata isso** (não verificado se há barreira física; o doc do Godot falava de barreira em x=-37) |
| sabores | Sabores da vila — **Dona Cecília** | "Dona Cecília quer resgatar as receitas da avó e levar comida boa até a rua principal." | 1) "Descobrir 2 drinks novos no Bar do Coqueiro" (exige o bar); 2) "Vender 10 porções de petiscos durante esta etapa"; 3) "Pagar R$ 250 da reforma da barraca do pastel" | R$ 300 + 80 fama | "Barraca do pastel + dica da moqueca" | `businesses.food_truck.chapter = sabores`. "Dica da moqueca": **ausente** (nenhum código/dica) |
| carnaval | O Carnaval da Maré — **Prefeita Tuanny** | "A prefeita Tuanny sonha com um carnaval de praia que traga turistas de longe. Ela conta com você." | 1) "Chegar à fama \"Famoso na região\"" (fama 5); 2) "Ter 2 negócios funcionando"; 3) "Pagar R$ 400 da decoração" | R$ 500 + 80 fama | "Carnaval no calendário de festas + Lojinha de souvenires" | `events.json → carnaval_chapter` (festa Carnaval entra no calendário), `businesses.souvenir.chapter = carnaval`, e é pré-requisito do Grand Hotel |

(As tarefas das missões da campanha usam títulos ligeiramente diferentes: "O píer do Seu Severino", "A prainha do Padre Robson", "Os sabores da Dona Cecília", "O carnaval da Prefeita Tuanny".)
Conquistas ligadas: `CC_CH_PIER/PRAINHA/SABORES/CARNAVAL` (sem consumidor). Total dos 4 capítulos: R$ 1.300 + 320 de fama (xp).

**Defeito crítico verificável (carnaval):** não existe morador chamado "Prefeita Tuanny" no jogo. `SRC/MareVillageWorld.cpp:61-69` cria só 5 moradores a partir de `Content/Data/village_routes.json`:
Dona Roberta, Alana, Seu Severino, Padre Robson, Dona Cecília. O diálogo só avança o capítulo quando `giver == Person->PersonName` (`MareVillageWorld.cpp:299`), e `AdvanceChapter` só é chamado por esse botão e pelo QA
(`MareGame.cpp:2758`, `MareVillageWorld.cpp:306`). Logo, **o 4.º capítulo (e, em cascata, `carnaval_m`, a tela de fim da demo, o Grand Hotel e todo o restante da campanha) não parece poder ser concluído por um jogador real** — só pelo
comando de QA `mare.QA step carnaval` ou pelas simulações que o chamam. O HUD mostra "Prefeita Tuanny: <passo> — x/y" e o celular diz "(converse com quem pediu para avançar)". Verificado por leitura de código e busca em `Source` e `Content/Data` (o nome só aparece em textos); não testado em jogo. Se houver outro caminho, não o encontrei.

---

## 5. Expansões e negócios, em ordem de desbloqueio

Dados: `DEF → expansions`, `expansion_order`, `businesses`. Compra: `MareSimulation.cpp:316-330` (`BuyExpansion`), `855-872` (`CanBuyBusiness/BuyBusiness`). Demo = sem `full_game`.

| Ordem | id | Nome | Preço (R$) | Requisitos | O que traz | Demo? |
|---|---|---|---|---|---|---|
| 1 | kiosk_tables | Mesas e guarda-sóis | 180 | — | +2 lugares no quiosque, clientes chegam mais rápido | sim |
| 2 | drinks | Licença de drinks | 260 | — | caipirinha no cardápio | sim |
| 3 | neon | Letreiro neon | 150 | kiosk_tables | quiosque aberto até 21h | sim |
| 4 | grill | Chapa de petiscos | 380 | kiosk_tables | petiscos e itens de chapa no cardápio | sim |
| 5 | bar | Bar do Coqueiro | 900 | grill + drinks | bar jogável com bartender, minijogo de drinks, receitas descobertas (`MareBar.cpp`) | sim |
| 6 | pousada | Pousada: recepção + bangalô | 1.400 | bar | recepção com negociação de diária, quartos para arrumar, camareira/recepcionista | sim |
| 7 | pool | Piscina | 1.100 | pousada | piscina, folhas/toalhas/picolés, piscineiro, tobogã/mergulho (hóspedes +★) | sim |
| 8 | passeios | Passeios turísticos | 1.000 | pousada | bilheteria no píer, passeios de barco, mergulho e trilha ao farol jogáveis; guia | sim |
| 9 | grand_hotel | Grand Hotel Maré Alta 5★ | 45.000 | pool + passeios + capítulo `carnaval` + **fama 9** | 32 quartos, VIPs, restaurante, spa, eventos de praia (casamento etc.), crítico | **não** (`full_game`) |
| 10 | salao_jogos | Salão de jogos do hotel | 6.500 | grand_hotel | sinuca, pebolim, pingue-pongue, 2 fliperamas, Campeonato da Maré | **não** |

Negócios (`DEF → businesses`, minijogo próprio, comprados no celular, funcionário rende 60 % sem fama):

| id | Nome | Preço | Fama | Capítulo exigido | Minijogo |
|---|---|---|---|---|---|
| sorveteria | Sorveteria Gelato da Maré | 900 | 2 | — | Montar a casquinha |
| aluguel | Aluguel de pranchas e caiaques | 1.400 | 3 | pier | Encerar a prancha |
| surfe | Escolinha de surfe | 2.200 | 4 | prainha | Aula na areia |
| food_truck | Barraca do pastel | 1.800 | 4 | sabores | Fritar o pastel |
| souvenir | Lojinha de souvenires | 1.600 | 5 | carnaval | Embrulhar o presente |

Diferença documento × dados: o comentário em `MareSimulation.cpp:323` e vários documentos dizem fama 8 para o hotel; o dado é **9**. Os 5 negócios não entram na campanha por missão; só como passo 2 do capítulo carnaval ("Ter 2 negócios funcionando") e nas conquistas.
Há outras compras fora de `expansions`: personalização (5 níveis por peça, `customization.json → price_mult [0,2.5,6,50,260]`), melhorias de receita (`recipes.cost_mult [0,12,30,180,900]`), equipe (atendente R$ 240 etc.). As mudanças de preço "propostas" de `BALANCEAMENTO.md` (260→220, 900→760) **não** foram aplicadas.

---

## 6. Fama, níveis e "árvore de progresso"

- **Níveis** (`SRC/MareSimulation.cpp:410-425`): 10 níveis por xp 0/100/250/450/700/1000/1400/1900/2500/3200. Nomes: 1 Desconhecido, 2 Falado na vila, 3 Ponto da praia, 4 Queridinho da cidade, 5 Famoso na região, 6 Roteiro turístico, 7 Destaque na TV, 8 Destino do verão, 9 Paraíso famoso, 10 Lenda da costa. O HUD mostra "Fama N · <nome>" e barra de xp.
- **Como sobe** (`AddFame`, ver `grep AddFame`): +2 por produto entregue no quiosque (+1 se receita nível ≥ 4, +1 se beleza do quiosque alta; `MareSimulation.cpp:285`); VIP no quiosque +6 (`kiosk_vip`: a partir do nível 2, 7 % dos pedidos); +80 por capítulo; drinks descobertos +6, "mestre dos drinks" +10; peixe +2 (garoupa +10; espécie nova +5); desafios de foto; passeios (`Pax/2 + 2×bons`); aluguel +1/+2 e resgate de caiaque +3; hóspedes da pousada +1/+2 por check-out; VIP e eventos do hotel; críticas do restaurante +4 / estrela +15 / ruim −6; fliperama/sinuca/pingue-pongue; perdas por multa injusta, VIP perdido, evento fracassado. Uma perda nunca baixa de nível.
- **O que os níveis fazem de verdade**: fama exigida de **expansões e negócios** (hotel 9; sorveteria 2, aluguel 3, surfe 4, pastel 4, souvenir 5); passos de capítulo (3 no prainha, 5 no carnaval); missão "lenda" (10); +4 % de clientes no quiosque por nível (`MareSimulation.cpp:637`); +3 % de ocupação da pousada por nível; renda dos negócios +6 % por nível; VIP no bar a partir do nível 4; +2 assentos de passeio no nível 8. Não há "árvore de habilidades": `prog.tree` e as metas semanais do Godot **não foram portados** (nenhuma leitura em C++). Não há tela de "nível novo" com recompensa, só a mensagem "Sua fama subiu: <nome>!" (`MareSimulation.cpp:469`).
- `docs/ue58/PROGRESSAO_2026-11-01.md` descreve o início do sistema; está de acordo com o código.

---

## 7. Personagens com nome

| Personagem | Quem é / onde aparece | O que diz / faz | Papel na campanha |
|---|---|---|---|
| **Dona Dilce (Vó/Vovó)** | avó, dona original do quiosque; **nunca aparece fisicamente** | cartas (casa e dívida), cartões de marco, fala do final de dívida, "áudio de sete minutos" na festa; citada pelos 4 moradores | central: origem da dívida e do quiosque. Sem presença no mundo; não verificado se há imagem dela |
| **Seu Severino** | pescador; (75,−24) perto do píer; MetaHuman "Omari" | saudação: "Eu conheci sua avó Dilce quando aquele píer ainda era novo. Venha conversar comigo para ajudar os pescadores e fazer o negócio da família crescer."; dá capítulo `pier`; chora na festa | forte: capítulo 1; faz a "jangadinha" da lojinha |
| **Padre Robson** | pároco; (77,41) perto da igreja; reza missa 7–8h e 17h30–19h; "Lorenzo" | "A vila fica melhor quando cuidamos uns dos outros. Sua avó Dilce fez isso por muitos anos. Fico feliz em ver você por aqui."; capítulo `prainha` | médio: capítulo 2 |
| **Dona Cecília** | cozinheira; (72,25); "Celeste" | "Bem-vindo de volta! As melhores receitas da vila carregam lembranças. Sua avó Dilce nunca deixava ninguém sair do quiosque sem um sorriso."; capítulo `sabores` | médio: capítulo 3; faz a cocada da lojinha |
| **Dona Roberta** | moradora (ex-Dona Rita), (60,−21); "Ada" | "Sua avó Dilce sempre disse que você voltaria. O quiosque guardou muitas histórias — agora vai ganhar as suas. Se precisar de ajuda, a vila está por perto." Sem capítulo | só saudação; o pedido `cocos_rita` está inerte |
| **Alana** | moradora (69,42); "Tuya" | só a saudação genérica "Bem-vindo à vila! É bom ver o quiosque da família ganhando vida outra vez." | figurante nomeada, sem história |
| **Prefeita Tuanny** | prefeita; **não existe no mundo** | citada nos textos de campanha, no capítulo carnaval, na fala da festa, nos créditos | papel de capítulo sem corpo (seção 4) |
| **Seu Tibúrcio** | velho do morro; sentado no banco do cume | regra do mar, oferenda diária, 4 falas repetíveis; na festa desce ("Trinta anos sem descer esse morro…") | forte: missões morro/oferendas, tsunami diário |
| **Barqueiro** | pilota a lancha na chegada; sem fala | `MareIntro.cpp:93` | cenário |
| **Seu Arnaldo** | reclamão; evento cômico HUM-007 (5 falas em sequência) | "Essa água de coco está muito natural…" | humor, sem campanha |
| **Seu Bené** | pescador contador de histórias (HUM-008); adversário de sinuca/pebolim/pingue-pongue | peixe que cresce a cada conversa | humor + salão de jogos |
| **DJ Maré** | atração da festa de calendário `show_dj` | — | festa semanal |
| Nomes de fregueses/artesãos (Dona Rita, Tia Socorro, Thiago, Wesley, Seu Raimundo, Jéssica, Charbele, Yasmin, Ayla…) | rótulos de clientes e artesãos (`docs/ue58/PENDENCIAS_100.md:725-735`, `docs/CHECKLIST_PEDIDOS.md:70`) | — | figurantes |
| Vendedores dos negócios | todos "Vendedor" (`MareBusinessWorld.cpp:58`); a "Tuany (vendedora da praça)" do `CHECKLIST_PEDIDOS.md:70` **não existe no código** | — | — |

---

## 8. Eventos de enredo

**Tsunami / oferenda diária** (`SRC/MareSummitWorld.cpp`):
- Só ativa depois de conhecer Seu Tibúrcio (`summit.met`). Antes, do dia 2 em diante, das 9h às 18h aparece uma mensagem por dia: "Dizem que um velho lá no alto do morro, atrás da vila, quer muito falar com você. Tem uma trilha." (`:145`).
- Primeira conversa (3 respostas) termina com cortesia: "Hoje Seu Tibúrcio já deu um coco dele, por conta da casa. A partir de amanhã, a oferenda é com você: todo dia, antes das 16h." (a oferenda do dia 1 **não conta** para a missão).
- Fala de abertura: "Finalmente alguém subiu! Faz três semanas que eu grito daqui de cima e só o eco responde. Escuta: este mar aqui é temperamental. Todo santo dia alguém precisa deixar uma oferenda neste cesto, senão ele se zanga e manda a Onda. A grande. A de cem metros." Respostas: "Cem metros?!" / "Que tipo de oferenda?" / "Isso é sério?".
- Cada dia o jogador carrega (nas mãos) um produto do quiosque até o cesto, no topo do morro, antes das 16h. Lembretes às 12h ("Hoje ainda falta a oferenda do Seu Tibúrcio. O mar anda resmungando.") e 13h30 ("O céu está ficando esquisito... a oferenda do Seu Tibúrcio!"); presságio às 14h (chuva, trovões: "O mar ficou bravo de repente. Seu Tibúrcio avisou: sem oferenda, a Onda vem!"); **onda às 16h**: silêncio, o mar recua 3,8 m, onda de 22 a 60 m, **GAME OVER** ("A Onda levou tudo. Seu Tibúrcio bem que avisou.") com "Recomeçar o dia" (volta ao estado da manhã) ou "Menu principal". O dia condenado nunca é gravado (`bHoldSaves`).
- **Não há automação**: nenhum cargo, expansão ou item leva a oferenda. A obrigação continua pelo resto do jogo, inclusive depois do final: os créditos dizem "...ou quase. A maré continua, o quiosque também, e amanhã tem oferenda."
- O modelo de balanceamento assume 180 s por dia para a ida ao morro (`BALANCEAMENTO.md:158`).

**Festas do calendário** (`events.json`, `SRC/MareEvents.cpp`): a partir do dia 8, por dia da semana (`dia % 7`): 2 quermesse, 4 festa junina, 6 show do DJ Maré, 0 carnaval (só após o capítulo carnaval). Demanda ×1,4 (×1,7 com decoração de R$ 120 paga na véspera); carnaval ×2,0 (×2,2). Eventos aleatórios: calor 22 %, lua cheia 12 %, maré alta 10 %, tempestade 8 % (perde 35 % do estoque sem preparo de R$ 80). **Temporadas** de 14 dias: verão ×1,2, outono ×1, inverno ×0,8, primavera ×1 (ciclo de 56 dias). Previsão de amanhã no celular (Calendário). Nenhuma festa tem texto de história.

**Festa da Maré Alta (final da campanha)** (`MareSummitWorld.cpp:325-372`): com a missão `festa` ativa e o jogador na praia (y < 2500) entre 20h e 23h30, a vila desce, Seu Tibúrcio aparece na frente do herói e cinco linhas aparecem a cada 7 s no aviso: (1) "A vila inteira desceu para a praia. E olha quem veio junto: Seu Tibúrcio, de chinelo novo!" (2) "Seu Tibúrcio: \"Trinta anos sem descer esse morro. A trilha encolheu ou fui eu que cresci?\"" (3) "Prefeita Tuanny anuncia a Festa da Maré Alta. Seu Severino chora. Diz que é cebola. Não tem cebola." (4) "E o mar... calminho, calminho. Seu Tibúrcio: \"Barriga cheia. Ele adora festa. Quem não adora?\"" (5) "Vovó Dilce mandou um áudio de sete minutos. Resumo: está muito orgulhosa e quer o quarto com vista." Aos 36 s: tela preta "FIM" + "...ou quase. A maré continua, o quiosque também, e amanhã tem oferenda." + créditos curtos ("Ideia, direção e muita paciência: Sergio"; "Elenco: Vovó Dilce, Seu Severino, Padre Robson, Dona Cecília, Prefeita Tuanny e Seu Tibúrcio"; "E o mar, no papel de si mesmo.") + botão "Continuar na praia". Mensagem final: "Missão concluída: A Festa da Maré Alta. Resgate a recompensa no celular. E boa festa!" (O comentário fala em "fogos do vulcão", mas o vulcão saiu do mapa em 10/11: o efeito não faz nada.)

**VIPs, crítico e eventos do hotel** (jogo completo): VIP do quiosque (`kiosk_vip`: nível ≥ 2, 7 %, títulos "Estrela da TV", "Atleta da seleção", "Chef de TV", "Celebridade", "Lenda do surfe", "Artista de novela"; gorjeta ×0,8; +6 fama); VIP de quarto do hotel (`MareHotelRooms.cpp:177-195`); crítico gastronômico (`MareRestaurant.cpp:227-230`, estrelas do restaurante; a missão "chef" fala de "crítico" mas só conta 20 melhorias de receita); eventos de praia do hotel (`hotel_events.json`: casamento R$ 4.000/fama 12, aniversário R$ 1.500/fama 6, congresso R$ 2.500/fama 8; oferta a cada 2 dias às 9h). **Nenhum tem personagem nomeado nem ligação com a dívida ou a campanha**; são operações.
**Eventos cômicos** (`comic_events.json`, 7: gaivota, turista perdido, Seu Arnaldo, Seu Bené, influenciador, guarda-sol, atendente atrapalhado): não tocam dinheiro/estoque/campanha.
**Passeios** (`tours.json`): 4 tipos (barco, mergulho, trilha ao farol, jangada) com paradas e críticas por escolha; sem história de campanha.

---

## 9. Fim de conteúdo

| Tela | Quando | Conteúdo | Código |
|---|---|---|---|
| **Fim da demo** ("Obrigado por jogar a demo!") | uma vez, ao ter todas as expansões não-`full_game` E os 4 capítulos | "O Maré Alta continua aberto na demo. O Grand Hotel e a quitação da dívida de Dona Dilce esperam no jogo completo. Obrigado por cuidar da nossa primeira maré!"; linha de estatísticas (dias, caixa, fama, estrelas, drinks, fotos); "No jogo completo": Grand Hotel 5 estrelas com quartos para arrumar, hóspedes VIP e pedidos especiais / Casamentos, aniversários e congressos montados na praia / Restaurante com peixe do píer e um crítico gastronômico disfarçado / Salão de jogos: sinuca, pebolim, pingue-pongue, fliperamas e o Campeonato da Maré; botões "Continuar jogando" e (se houver URL) "Lista de desejos na Steam" (`review_url` está vazia) | `events.json → end_of_content`, `MareEvents.cpp:53`, `MareGame.cpp:1789-1850` |
| **Final da dívida** | jogo completo, saldo zero | seção 2 | `MareDebt.cpp`, `MareGame.cpp:1789` |
| **FIM da festa** | missão `festa` | seção 8 | `MareSummitWorld.cpp:366-381` |
| **Game over do tsunami** | falta de oferenda às 16h | seção 8 | `MareSummitWorld.cpp:292` |

Epílogo / créditos longos / novo jogo+ / objetivos pós-final: **não há**. Busca por "epílogo", "novo jogo+", "post-game" em código e documentos: nada. Depois dos dois finais o jogo "continua" sem objetivos novos: a página Missões mostra "Campanha concluída!" e o HUD fixo não mostra nada de campanha (o bloco só desenha com `stage` válido, `MareGame.cpp:3116`); o "Próximo desbloqueio" some quando tudo está comprado; restam receitas/decoração/negócios no nível 3, conquistas sem consumidor e a oferenda diária.
`credits.json` ("nenhum C++ consome credits.json") é contrato não integrado; os créditos do menu são texto fixo `LOCTEXT("CreditsText")` (`MareGame.cpp:1995`); o botão "Créditos" do final da dívida abre o menu principal na página de créditos (`MareGame.cpp:2324-2327`), isto é, **sai do jogo para o menu**.
Conquistas Steam: contrato em `achievements.json` (39 entradas), sem integração. Link da lista de desejos: vazio.

---

## 10. Ritmo medido (modelo, não playtest)

Fonte: `docs/ue58/BALANCEAMENTO.md` (Pacotes 2 e 4, 30 sementes × 3 perfis; modelo `tools/ue58/balance/*.py`, resultados `tools/ue58/balance/jogo_completo/summary.json` e `demo/`), `CHECKLIST_SIMULACAO.md` (simulações de QA de 03/11 e 10/11: validam ausência de erros, não cronometram), `TESTE_MANUAL_DEMO.md`. Todo número é de MODELO com política de jogador hipotética; "Não houve playtest" (`BALANCEAMENTO.md:70`); "confirmar jogando a demo do zero e cronometrando" (`:131`). Conversão: 16 min/dia.

| Marco | Casual (dia / h) | Médio | Dedicado |
|---|---|---|---|
| Fim da demo | 10 / 2,7 | 8 / 2,1 | 7 / 1,9 |
| Grand Hotel comprado | 30,5 / 8,1 | 25 / 6,7 | 23 / 6,1 |
| Campanha completa (festa) | 87 / 23,2 | 76 / 20,3 | 68 / 18,1 |
| Dívida quitada (política: 2 % antes do hotel, 50 % depois) | 85 / 22,7 | 76 / 20,3 | 67 / 17,9 |
| Todas as compras (100 %) | 151 / 40,3 | 139 / 37,1 | 122 / 32,5 |

Dívida: marcos medianos (médio): primeiro pagamento dia 1; 25 % dia 42; 50 % dia 54; 75 % dia 65; 100 % dia 76. Na demo a trajetória da semente 0 paga ~R$ 240–290 até o fim da demo (teto R$ 250.000); nenhuma das 180 trajetórias de demo quitou; o 25 % (R$ 250.000) exigiria ~40+ dias de renda pré-hotel (R$ 5.782/dia, médio), bem além da duração da demo.
Decisão do Sergio (11/11): "Campanha deixa com 20h"; não acelerar porque encurtaria também a demo (`PLANO_E_CHECKLIST_2026-11-08.md:348-350`).

Intervalos longos sem novidade de campanha (médio, em dias): 8 → 25 (17 dias ≈ 4,5 h) entre `carnaval_m` e `marealta`; 26 → 75 (49 dias ≈ 13 h, ~65 % da campanha) entre `lenda`/`salao`/`chef`/`postal` (todas no dia 26 no modelo) e `fregueses` (7.000 vendas), sem outra missão de campanha. O modelo diz que "sempre há algo a comprar" (maior intervalo sem compra: 3 dias) e que depois de todas as compras o caixa cresce sem finalidade (R$ 68.550 → R$ 398.945) (`BALANCEAMENTO.md:99, 321-355`).
Renda média/dia antes do hotel R$ 5.782, depois R$ 42.469 (hotel ≈ 30 %+ da receita).
Outros marcos (médio): casamento montado dia 31, evento "empresa" 31, formatura 34, campeonato 29,5, passeio jangada 22–29, crítico 26, primeira estrela do restaurante dia 89 (só 2/30 dedicados).

---

## Buracos e fraquezas observados (só fatos, com referência)

1. **Capítulo do carnaval sem quem o avance.** "Prefeita Tuanny" é `giver` (`DEF → chapters[3].giver`) mas não existe como morador (`SRC/MareVillageWorld.cpp:61-69`; `village_routes.json → residents` = 5 nomes); o avanço só ocorre ao conversar com quem tem o mesmo nome (`MareVillageWorld.cpp:299-306`). Consequência provável: missão `carnaval_m`, fim da demo (`MareEvents.cpp:53`), Grand Hotel (`chapter: carnaval`), souvenir e festa do carnaval ficam inalcançáveis para um jogador real. Verificado só no código; os testes e a simulação usam `mare.QA step`/`AdvanceChapter` direto.
2. **O `story` das 21 missões + 4 paralelas nunca é mostrado** (celular e HUD usam `title`/`task`; `MareGame.cpp:895-897, 3126-3129`). Todo o humor e enredo da campanha ("amigas do bingo", "dormindo na rede do Seu Severino") está em dados sem tela.
3. **O objetivo central não está no HUD.** Saldo, % pago e botão de pagar só no celular → Finanças; o HUD fixo lista missão, pedidos, "próximo desbloqueio" e capítulo (`MareGame.cpp:3100-3160`). A dívida aparece como cartão de 14 s em só 5 momentos (carta, 3 marcos, lembrete).
4. **A dívida é desligada da campanha.** Nenhuma missão exige pagar nada (`debt.json → campaign_texts.festa`: "não adicionar requisito de dívida à festa"); a campanha termina na festa (dia ~76) e o final da dívida é um segundo final independente que pode vir antes ou depois (modelo: dia 76 e 76). Dois finais sem ordem definida.
5. **A carta da casa não fala da dívida**; ela é revelada por um cartão de 14 s depois de criar a empresa (`MareDebt.cpp:162-172`), no momento mais carregado de tarefas (celular acabou de fechar, primeiro dia). A carta da dívida cita "o barco chegou primeiro" e "almoço", e a missão `chegada` diz que a avó "foi morar com as amigas do bingo".
6. **O motivo da dívida nunca é explicado.** Nenhum texto diz por que existe R$ 1.000.000, com quem (um "gerente" só em piadas) ou por que o neto herda. Busca por "dívida" em `DEF`, `debt.json` e cartas: só o fato e o tom cômico.
7. **Dona Dilce não existe no mundo**: sem retrato, cena ou telefone; só cartas, um "áudio de sete minutos" e uma fala no final. O "quarto com vista / desconto de família" (missão marealta, festa, final) não tem payoff de gameplay (nenhum quarto reservado, nenhuma visita).
8. **O destino do resort depois de pagar não é tratado**: sem epílogo, créditos longos integrados, "novo jogo+" ou objetivos pós-final (busca). "Continuar no resort" só fecha a tela; "Créditos" leva ao menu principal (`MareGame.cpp:2324-2327`). A tela final diz "o próximo sonho não vem com boleto" sem abrir um próximo sonho.
9. **A oferenda/tsunami é obrigação perpétua sem automação** (`MareSummitWorld.cpp:136-153`): uma viagem diária ao morro por 76–150+ dias, com game over; nada na campanha ou nos cargos a delega ou encerra, nem depois da festa (os créditos até brincam com isso). A história de Tibúrcio acaba em 3 oferendas + 1 aparição na festa; as 4 falas repetíveis valem até o fim do jogo.
10. **49 dias de jogo (~13 h) com uma só missão de campanha** ("Sete mil vendas", contador) entre as missões 19 e 20 no modelo do perfil médio (`summary.json`: lenda/salao/chef/postal no dia 26, fregueses no dia 75); 17 dias (~4,5 h) entre `carnaval_m` e `marealta`. Sem novidade de enredo, personagem ou capítulo nesses trechos; os 4 capítulos da vila acabam no dia 8–10.
11. **A vila para de falar quando começa o hotel**: só 4 capítulos, todos antes do Grand Hotel; a maior parte do conteúdo (hotel, salão, eventos, VIPs, crítico) não tem NPC nomeado, fala ou missão de história. As 5 missões pós-hotel (`salao`, `chef`, `postal`, `lenda`, `fregueses`) são contadores/compras.
12. **Textos de história curtos/repetidos**: capítulos só falam no passo 1 (`MareVillageWorld.cpp:303`); passos 2 e 3 só mostram "passo N/3: texto (x/y)"; morador de capítulo concluído sempre diz a mesma frase; Dona Roberta e Alana só têm saudação; 3 respostas do Tibúrcio no 1º encontro e 4 falas aleatórias depois; cada marco da dívida tem uma frase.
13. **Recompensa só em R$ e só ao clicar "Concluir" no celular**; o HUD só avisa "· concluir no celular" na missão atual. Os `unlock` dos capítulos prometem "dica da moqueca" e "Prainha do Oeste aberta" que não existem como código (`grep moqueca`/`prainha` em `SRC`: só QA e dados).
14. **Conteúdo morto/prometido**: `DEF → quests` (4 pedidos de moradores) sem leitura; metas semanais/árvore do Godot (`default_save.json → goals/tree/medals`) sem leitura; `debt.json → campaign_texts` sem leitura; conquistas (39) e `credits.json` sem consumidor; `intro_bus.json` sem uso na cena.
15. **Personagens citados que não aparecem**: Prefeita Tuanny (nunca no mundo), Dona Dilce, "gerente" do banco, "Dona Rita" (só como artesã), "Tuany (vendedora da praça)" (em `CHECKLIST_PEDIDOS.md:70`, ausente do código); Seu Bené e Seu Arnaldo só em eventos cômicos aleatórios; Alana nomeada sem função.
16. **Inconsistência de tom/gênero/identidade**: carta da casa "Meu neto…" / "Vó Dilce"; carta da dívida "Meu bem"; cartão-postal "Bem-vinda, bem-vindo"; créditos "Vovó Dilce"; documento de abertura em avô/"Vô"/ônibus (código: avó/barco). Nome do jogo: "Coconut Simulator" no jogo, "Coconut Coast: Resort Simulator" em `credits.json` e `CHECKLIST_EXPANSOES.md`.
17. **Demo: o objetivo central quase não é jogável**: teto de R$ 250.000 que só se alcança com ~40+ dias de renda; as trajetórias de demo pagam ~R$ 250–300 (`BALANCEAMENTO.md:46-55`); o marco de 25 % é inalcançável no tempo da demo, então 3 dos 4 textos de marco só existem na prática no jogo completo.
18. **Documentos desatualizados**: `debt.json _doc.status`, `DIVIDA_DA_AVO.md:5` e `BALANCEAMENTO.md:1` (dívida "não implementada"); `ABERTURA_UMA_NOVA_MARE.md` (ônibus/avô); fama 8 (comentário `MareSimulation.cpp:323`) vs 9 (dado); `BALANCEAMENTO.md` Pacote 2 cita "4.000 vendas" e R$ 30.000 para o hotel (hoje 7.000 e R$ 45.000).
19. **Sem objetivo explícito depois do fim da demo**: com tudo da demo comprado, o "Próximo desbloqueio" some e o HUD mostra "Uma nova maré · a história continua no jogo completo"; restam só as 2–4 missões paralelas (se restarem) e a oferenda diária.
20. **Primeiro minuto sobrecarregado**: carta da casa → celular → criar empresa → carta da dívida (cartão de 14 s) → placa do balcão, com ~55 dicas de primeira vez em cartões de 14 s; a missão `morro` só é "dita" ao jogador no dia 2, de 9h às 18h, por uma mensagem avulsa.
21. **Não verificado**: se a casa aparece na bússola do HUD (o único hint de onde está a carta é o texto); se há barreira física da "Prainha do Oeste" no mapa; se as recompensas em R$ cobrem os preços no jogo real (o modelo diz que sim); se um jogador real consegue concluir o capítulo do carnaval por algum caminho não encontrado; se os dois finais (festa e dívida) aparecem em ordem sem conflito de tela (`ShowEndOfContent` exige celular fechado e `GameWidget` vazio); se os negócios têm falas de dono (o código usa "Vendedor").

---

*Arquivo gerado por leitura de código/dados/documentos; nenhum arquivo do repositório foi alterado.*
