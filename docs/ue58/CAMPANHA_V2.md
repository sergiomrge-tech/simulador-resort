# Campanha v2 — desenho e contrato (12/11/2026)

Aprovado pelo Sergio em 12/11 ("vou seguir sua sugestão"), a partir do levantamento
[`CAMPANHA_MAPA_2026-11-12.md`](CAMPANHA_MAPA_2026-11-12.md). Este arquivo é o CONTRATO para quem programa, escreve,
traduz e opera o editor: ids, condições e números daqui valem; texto de jogo vem do redator e é revisado pelo diretor.

## Limites que não mudam
- Campanha ~20 h (perfil médio), demo ~2,7 h terminando no capítulo do carnaval. Preços e rendas não mudam.
- HUD atual fica; só entra UMA linha pequena com o saldo da dívida.
- Todo texto novo sai nos 12 idiomas. Jogador sem gênero definido: tratamento "Meu bem" (nunca "meu neto/minha neta").
- Save antigo continua carregando: a etapa da campanha passa a ser guardada pelo ID da missão (migrar o índice antigo).

## 1. A dívida vira a espinha da campanha

**Por que existe a dívida (revelado aos poucos, uma carta por marco):** em quarenta anos Dona Dilce assinou como
fiadora de tudo o que a vila precisou e não podia pagar. Cada carta conta um pedaço e aponta para um morador:

| Marco | Carta revela | Morador ligado |
|---|---|---|
| Abertura (P.S. da carta da casa) | existe uma dívida de R$ 1.000.000, sem juros nem prazo; "eu conto o resto aos poucos" | — |
| 25 % | o píer reconstruído depois do vendaval | Seu Severino |
| 50 % | o telhado da igreja e o sino | Padre Robson |
| 75 % | a cozinha da Dona Cecília e a escola da vila | Dona Cecília, Prefeita Tuanny |
| 100 % | a última parcela era o terreno do quiosque, comprado no nome do neto/da neta "para quando voltasse" | o jogador |

- A dívida passa a ser contada na **carta da casa**, numa segunda folha (P.S.), antes de criar a empresa. O cartão de
  14 s depois de criar a empresa fica só como lembrete curto de onde se paga.
- Cada marco (25/50/75 %) abre uma **carta em folha de caderno** (mesma tela da carta da casa), relegível no celular
  (Finanças → "Cartas da Vó Dilce"), no lugar do cartão de 14 s.
- O morador ligado ao marco ganha uma fala nova depois da carta ("ela nunca contou que foi ela...").
- **Linha no HUD:** `Dívida: R$ 912.400 · 9 %` sob o dinheiro, só depois de lida a carta.

**Missões de pagamento na fila da campanha** (`kind: debt`, `qty` = % pago; sem recompensa em dinheiro, recompensa = carta):

| id | Título provisório | Condição | Onde entra |
|---|---|---|---|
| `parcela` | A primeira parcela | pagar qualquer valor ≥ R$ 50 | depois de `equipe` (demo) |
| `divida_25` | Um quarto mais leve | 25 % pago | depois de `descanso_m` |
| `divida_50` | Metade da maré | 50 % pago | depois de `critico_m` |
| `divida_75` | Quase dá para respirar | 75 % pago | depois de `divida_50` |
| `divida_100` | Dívida baixa: zero | 100 % pago | depois de `fregueses` |

**Um final só.** A missão `festa` passa a exigir a dívida quitada. A Festa da Maré Alta é a comemoração da quitação:
Dona Dilce chega de barco ao píer, a vila desce, as falas atuais da festa ficam (com a do "áudio de sete minutos"
trocada pela chegada dela) e a festa termina na tela "Maré Alta, dívida baixa: zero!" (a tela final que já existe), com
os créditos abrindo ali mesmo, sem sair para o menu. A tela preta "FIM" separada deixa de existir.
Na demo nada disso aparece (teto de pagamento e fim no carnaval, como hoje).

## 2. Segunda leva de capítulos (preenche os vazios)

Cinco capítulos novos, só do jogo completo (`full_game: true` no capítulo; não contam para o fim da demo). Mesma
mecânica dos quatro atuais (3 passos, conversa presencial, +80 de fama), com duas mudanças: **cada passo tem fala
própria** (`lines`, hoje só o passo 1 fala) e **quem concluiu varia a despedida** (lista `thanks`, sorteada).

| # | id | Título provisório | Quem pede | Abre depois de | Passos (tipo · quantidade) | Recompensa | Libera |
|---|---|---|---|---|---|---|---|
| 5 | `rede` | As redes da Dona Roberta | Dona Roberta | `carnaval` + pousada | hospedar 6 hóspedes (check-outs no passo) · doar R$ 600 (tecido) · fama 6 | R$ 400 | redes de descanso na pousada (peças no cenário) |
| 6 | `farol` | A lanterna da Alana | Alana | `rede` + passeios | guiar 3 passeios (no passo) · fotografar o farol ao pôr do sol (desafio de foto existente) · doar R$ 900 (lâmpada) | R$ 600 | facho do farol aceso à noite |
| 7 | `descanso` | O descanso do Seu Tibúrcio | Seu Tibúrcio (no cume) | `farol` + Grand Hotel | 12 oferendas no total · entregar 5 cocos do estoque · doar R$ 2.000 (cesto novo) | R$ 800 | **oferenda delegável** (ver 3) e Tibúrcio visita o quiosque no fim da tarde |
| 8 | `critico` | O paladar do Seu Arnaldo | Seu Arnaldo (o reclamão dos eventos cômicos) | `descanso` + restaurante do hotel | 10 melhorias de receita (no passo) · servir 30 pratos no restaurante (no passo) · 3 críticas boas (no passo) | R$ 1.000 | revela-se que ele é o crítico gastronômico; placa "Recomendado pelo Arnaldo" no restaurante |
| 9 | `quarto` | O quarto com vista | Seu Severino (em nome da vila) | `critico` + 75 % da dívida | 10 melhorias de personalização (no passo) · realizar 1 evento do hotel (no passo) · doar R$ 5.000 (passagem e quarto) | R$ 1.500 | Dona Dilce vem para a festa e fica morando no hotel |

Tipos de passo novos para o programador (usar contadores que já existam; criar só o que faltar): `guests`, `tours`,
`offerings`, `dishes`, `reviews`, `custom`, `hotel_event`, além dos atuais (`deliver`, `serve`/`sell`, `pay`, `fame`,
`photo`, `recipes`, `biz`). Requisito extra de abertura: expansão comprada (`needs`) e % da dívida (`debt`).

**Fila da campanha (ids em ordem; novos em negrito):** chegada, portas, primeiros, mesas, equipe, **parcela**, morro,
oferendas, comunidade, encontro, hospedar, verao, prainha_m, sabores_m, carnaval_m *(fim da demo)*, **rede_m**,
**farol_m**, marealta, salao, chef, postal, lenda, **descanso_m**, **divida_25**, **critico_m**, **divida_50**,
**divida_75**, **quarto_m**, fregueses, **divida_100**, festa.

Ritmo esperado no perfil médio (dias; conferir no modelo de balanceamento depois de implementar): rede 10–14, farol
15–22, hotel 25, descanso 30–38, 25 % no dia 42, crítico 44–52, 50 % no 54, 75 % no 65, quarto 66–72, 7.000 vendas no
75, quitação e festa no 76. Maior trecho sem missão nova: ~10 dias (era 49).

## 3. Oferenda com fim
Ao concluir `descanso`, o celular (Equipe) ganha "Oferenda do dia: levar eu mesmo / mandar o atendente (R$ 60 por
dia)". Delegada, é descontada de manhã e conta como feita; sem dinheiro ou sem atendente contratado, volta a ser do
jogador e o lembrete das 12h avisa. Levar pessoalmente continua possível e rende uma fala do Tibúrcio.

## 4. História visível
- Página Missões do celular: o `story` da missão atual aparece sob o título (e o das concluídas, ao tocar nelas).
- Capítulos: fala em todos os passos e despedidas variadas (acima).
- Dona Roberta e Alana deixam de ser figurantes (capítulos 5 e 6).
- Textos órfãos saem dos dados ou ganham função: "dica da moqueca" e "Prainha do Oeste aberta" são retirados dos
  `unlock`; `DEF → quests`, `debt.json → campaign_texts` e `intro_bus.json` são removidos.

## 5. Epílogo
Depois da festa: Dona Dilce existe no mundo (varanda do hotel de dia, quiosque no fim da tarde), com falas próprias;
a página Missões mostra "Sonhos da vila", uma lista de metas longas que já existem como contador (todas as compras,
primeira estrela do restaurante, livro de pesca completo, desafios de foto, 5 drinks mestres). Sem recompensa nova:
é o que dá objetivo a quem continua.

## 6. Pessoas e lugares novos (editor)
- **Prefeita Tuanny** na praça da vila (já: destrava o carnaval) e depois dentro/na porta da **prefeitura** (prédio novo na vila).
- **Seu Arnaldo** como morador fixo (mesa do quiosque de dia; restaurante do hotel depois de `descanso`).
- **Dona Dilce**: precisa de um corpo de senhora idosa (não há MetaHuman idosa no projeto: levantar o que existe antes).
- Redes da pousada, facho do farol, placa do Arnaldo, quarto com vista: peças de cenário ligadas ao capítulo concluído.

## 7. Pacotes de trabalho e ordem
1. **A1 lógica** (programador): capítulos e missões novos por dados, tipos de passo, etapa por ID com migração,
   requisito de dívida, delegação da oferenda, testes de automação. Textos provisórios nos dados.
2. **Textos** (redator): piloto = P.S. da carta + carta de 25 % + capítulo `rede`; depois o lote. Voz: a das cartas e
   missões atuais (carinho com piada seca).
3. **A2 telas** (programador): história no celular, linha da dívida no HUD, cartas dos marcos, festa + final único,
   créditos no lugar, "Sonhos da vila".
4. **Editor** (operador): Tuanny, prefeitura, Arnaldo, Dilce, peças de cenário, cena da chegada dela.
5. **Tradução** (tradutor) dos textos aprovados, 12 idiomas.
6. **Prova**: teste do portão que percorre a campanha conversando (sem `mare.QA step`), modelo de balanceamento
   rodado de novo, campanha inteira no executável.
