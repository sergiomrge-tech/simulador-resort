# Plano de gameplay — 02/11/2026

Decisões do Sergio nesta conversa: **hospedagem mãos na massa**, **negociação em rodadas de oferta** e
**sinuca com partida contra hóspede**. Ideias trazidas de *Arcade & Motel Simulator Together* (Nons Games,
30/10/2026): negociação na recepção, minijogos jogáveis e estrelas/ocupação sempre na tela; mais o pedido
de um **salão de jogos no hotel**. Este documento é o plano; nada dele está implementado ainda.

## 1. Onde o jogo está (Unreal 5.8)

| Sistema | Estado |
|---|---|
| Quiosque | Completo: pedido e retirada no balcão, produtos prontos, entrega com pagamento automático, estoque/reposição, um atendente, personalização paga, receitas melhoráveis |
| Pousada / Hotel 5★ | **Passivos**: `PousadaNight` / `HotelNight` sorteiam ocupação e lançam a receita ao dormir; o jogador não faz nada neles |
| Avaliação | `ratings` (últimas 40 notas) → `Stars()`; notas da pousada são sorteadas 3,4–4,4 + conforto |
| Progressão | Fama (XP por entrega e capítulo), capítulo 1 da vila, campanha, fechamento do dia com salário, negócios, passeios, expansões |
| Faltando da Godot | Pesca no píer, modo foto (P), eventos/festas nativos, fama aumentando a demanda |
| Pessoas | Trocando pelo MetaHuman (em andamento): papéis, banhistas com biquíni/sunga |

**Buraco principal:** depois do quiosque, o dinheiro compra expansões que só geram renda passiva. A
pousada e o hotel precisam virar lugares onde o jogador **trabalha**, como no quiosque.

## 2. Pilares

1. **Trabalho com as mãos, em primeira pessoa**: atender, negociar, arrumar e jogar com os hóspedes.
2. **Crescer do quiosque ao Hotel 5★**: cada expansão traz uma tarefa nova, não só um número a mais.
3. **Praia viva**: MetaHumans (banhistas, moradores, hóspedes), histórias da vila e eventos.
4. **Reputação visível**: estrelas e ocupação sempre na tela; cada decisão (preço, limpeza, rapidez) mexe nelas.

## 3. Ciclos

- **Minuto a minuto**: atender o rush do quiosque, receber hóspede na recepção (negociar), arrumar um quarto
  vago, jogar uma partida no salão.
- **Um dia (08:00–21:00)**:
  - manhã: abrir o quiosque, repor estoque e fazer check-outs/limpeza;
  - tarde: rush da praia e check-ins na recepção;
  - noite: salão de jogos com os hóspedes e fechar;
  - dormir mostra o resumo do dia (receita, notas e estrelas).
- **Semana**: festas e eventos, capítulos da vila, comprar expansões e melhorias, subir de estrelas e fama.

## 4. Sistemas novos

### 4.1 Recepção com negociação (pousada e hotel)

- Hóspedes MetaHuman chegam à recepção ao longo do dia (taxa ~ ocupação esperada; fama e estrelas aumentam)
  e esperam numa fila com paciência visível.
- **E no balcão abre a negociação** (painel compacto à direita, como as estações):
  - **Preço de referência** = `PousadaRate()` / diária do hotel (já existe: base + 12 × estrelas + personalização).
  - Cada hóspede tem **perfil** sorteado pela save id: mochileiro (orçamento 0,7–0,9× referência),
    casal (0,9–1,1×), família (1,0–1,2×, 2 quartos às vezes), executivo/VIP no hotel (1,1–1,4×).
  - O hóspede **abre com uma oferta** de 75–90% do seu limite secreto. O jogador **aceita**, **recusa** ou
    **contrapropõe** (botões −10 / −5 / +5 / +10% e confirmar).
  - **Até 3 rodadas.** Contraproposta acima do limite → recusa educada e humor cai; se cair a zero, ele vai
    embora. Abaixo do limite: aceita, com chance de contraoferta no meio do caminho.
  - Fechar perto do limite rende mais dinheiro e humor menor; aceitar logo rende menos e humor maior.
- **Humor do check-in** soma na nota final da estadia (até ±0,6 estrela). A nota sai da limpeza do quarto,
  do conforto/decoração (`PlaceComfort`) e do humor.
- Recepcionista contratado faz check-ins automáticos pelo preço de referência, sem a margem da negociação,
  para quem prefere ficar no quiosque.

### 4.2 Quartos e limpeza

- Estado por quarto: **livre → ocupado (com hóspede e chave) → sujo → livre**. O check-out acontece de
  manhã (08:00–11:00).
- O quarto sujo mostra o que falta: **cama desfeita** (E arruma), **toalhas no chão** (E recolhe e leva
  ao cesto), **lixo** (E recolhe e leva à lixeira). Usa os bangalôs mobiliados e a suíte que já existem.
- Quarto sujo não pode receber hóspede. Hóspede que encontra o quarto sujo dá nota baixa.
- A **camareira** (cargo que já existe nos dados) limpa sozinha, mais devagar, e cobra salário ao dormir.
- `PousadaNight` / `HotelNight` passam a **cobrar as estadias reais** (check-ins do dia) em vez de sortear
  ocupação. Saves antigos: no primeiro dia, os quartos ocupados no sorteio viram hóspedes reais.

### 4.3 HUD de reputação

- Canto superior esquerdo, sempre visível (fora do celular): **★ 4,2** (média `Stars()`), **🛏 3/5** quartos
  ocupados (pousada + hotel, quando existirem) e **clientes atendidos hoje**.
- A fonte manuscrita não tem ★ nem 🛏 (lição de 01/11): usar ícones como imagem (Slate brush), não caracteres.
- Mudanças piscam por 1 s (+0,1 estrela verde, −0,1 vermelha).

### 4.4 Salão de jogos no Grand Hotel

- Expansão paga com o caixa do quiosque (regra fixa), liberada com o hotel; ocupa uma sala do prédio,
  com acesso pelo lobby.
- **Sinuca — partida contra hóspede (decisão do Sergio):**
  - física real com Chaos: 15 bolas + branca; mesa com tabelas, caçapas e atrito de pano calibrados;
  - mira com o mouse, força segurando e soltando o clique, com linha-guia curta;
  - partida curta: bola 8 simplificada, ou "primeiro a encaçapar 4", para durar 3–5 minutos;
  - o hóspede adversário é um MetaHuman, com IA de tacada (escolhe a bola mais fácil e erra com a
    precisão do seu nível);
  - aposta leve opcional: ganhar dá gorjeta e humor no hóspede; perder dá humor e um pouco de fama;
  - modelos reais de mesa, taco e bolas (procurar CC0/Fab antes; Blender só se não houver).
- **Pebolim** e **2 fliperamas** jogáveis com minijogos curtos (os fliperamas podem reaproveitar o
  minijogo dos negócios).
- Os hóspedes usam o salão à noite (animação perto das mesas), cobrando fichas: renda extra por noite e
  bônus de nota para o hotel.

### 4.5 Fama aumenta a demanda (pendente da Godot)

- +4% de clientes no quiosque e de chegadas na recepção por nível de fama (como na Godot).

## 5. Ordem de implementação (marcos testáveis)

1. **M1 – HUD de reputação** (pequeno, vale para tudo): estrelas, ocupação, atendidos hoje.
2. **M2 – Recepção da pousada**: hóspedes chegando, fila, negociação em 3 rodadas, chave, estadia real no
   fechamento do dia, migração de saves.
3. **M3 – Quartos e limpeza**: estados dos bangalôs, tarefas de cama/toalhas/lixo, camareira, nota final
   da estadia.
4. **M4 – Hotel 5★ com o mesmo sistema**: suíte e quartos do hotel, perfis VIP, recepcionista.
5. **M5 – Salão de jogos**: sala, móveis reais e sinuca jogável contra um hóspede. Depois pebolim e
   fliperamas.
6. **M6 – Fama → demanda** e balanceamento da economia (diária, salário, renda do salão).
7. Depois: pesca no píer, modo foto (P), eventos cômicos (issue #4) e co-op (projeto grande, fora deste plano).

Cada marco tem:
- teste de automação no MCP (dinheiro uma vez, save/reload, sem cobrança dupla);
- PIE com capturas e EXE só quando pedido;
- entrada no `CHECKLIST_PEDIDOS.md`.

## 6. Números iniciais (balancear no M6)

| Item | Valor inicial |
|---|---|
| Diária pousada (referência) | 100 + 12 × estrelas (+ personalização), já existente |
| Diária hotel | referência × 2,5 |
| Limite secreto do hóspede | perfil × referência (0,7–1,4×) |
| Humor → nota | ±0,6 estrela |
| Quarto sujo ao receber hóspede | nota máxima 2,5 |
| Camareira | limpa um quarto em ~6 min de jogo; salário como os outros cargos |
| Ficha do salão | R$ 5 por partida/hóspede; 2–6 hóspedes por noite conforme ocupação |

## 7. O que já deu certo no gênero e o que vamos copiar

Pesquisa de 02/11 (Steam, GameDiscover, Game World Observer, Raijin/SteamSpy; vendas são estimativas).

| Jogo | Resultado | Por que funcionou | O que trazemos |
|---|---|---|---|
| **Supermarket Simulator** (Nokta) | 1,8–3 mi de cópias, pico de ~40 mil jogadores simultâneos | Tarefas físicas simples e satisfatórias (repor, passar no caixa); o jogador define o preço e vê a reação do cliente; licenças liberam produtos novos; contrata funcionários para automatizar o que cansa; co-op 2–4 chegou depois | **Preço por produto no quiosque** com reação do cliente ("caro!" / sorriso) e efeito na demanda; **licenças por nível** (já temos receitas e licenças: só deixar visível); funcionários assumindo o que é repetitivo |
| **TCG Card Shop Simulator** (solo dev) | 100 mil cópias em 3 dias, 4 mi de jogadores, ~95% positivo | Copiou o ciclo do Supermarket com um tema que as pessoas amam; **duas progressões que se alimentam** (a loja paga os pacotes, as cartas raras pagam a loja); tensão de fazer duas coisas ao mesmo tempo; demo "Prólogo" e atualizações constantes | O **tema é o nosso diferencial** (resort de praia brasileiro, aconchegante); **dois motores**: o quiosque financia a hospedagem e os hóspedes trazem clientes ao quiosque e ao salão; **tensão**: rush do quiosque, recepção e quarto sujo ao mesmo tempo |
| **Gas Station Simulator** (Drago) | +US$ 10 mi só na Steam | Pegar um lugar decadente e reformá-lo aos poucos; cada melhoria é visível | **Personalização paga** (já temos) mostrada como antes/depois; quartos melhorados aparecem na nota |
| **Motel Manager Simulator** | "Muito positivas" (~1,5 mil análises) | Alugar, mobiliar e decorar quartos, com uma loja de conveniência anexa | Hospedagem mãos na massa (este plano) e decoração do quarto aumentando a diária |
| **Schedule I** (solo dev, 2025) | ~97% positivo, pico de ~460 mil simultâneos | Combinação de receitas (ingredientes que criam produtos com propriedades); **co-op para 4** com papéis divididos | **Bar de drinks com combinações** (frutas, base e gelo dão drinks novos com propriedades e preço próprio) no lugar da cozinha experimental da Godot; co-op planejado |
| **Arcade & Motel Simulator Together** / **Barfender CO-OP** | Lançamentos recentes do mesmo nicho | Negócio caótico em co-op, minijogos jogáveis | Negociação, salão de jogos e estrelas na tela (este plano) |

**Padrões que se repetem em quase todos:**

1. **Ações físicas curtas e satisfatórias** (pegar, levar, arrumar, encaixar): cada uma com som e animação caprichados.
2. **O jogador define o preço** e vê a consequência na hora.
3. **Crescer → contratar** para automatizar o repetitivo, liberando o jogador para a parte nova.
4. **Desbloqueios frequentes** (produto, móvel, área) a cada 10–20 minutos de jogo.
5. **Tema forte e reconhecível** como diferencial: o nosso é a praia brasileira.
6. **Co-op 2–4** é o que mais impulsiona as vendas, mas quase todos lançaram solo e acrescentaram depois.
7. **Demo/prólogo cedo e acesso antecipado** com atualizações frequentes guiadas pela comunidade.

**Acréscimos ao plano** (entram depois dos marcos M1–M6):

- **M7 – Preço por produto no quiosque**: etiqueta editável no celular, faixa "barato/justo/caro" em
  relação ao preço de referência; o cliente reage (balão) e a demanda e a gorjeta respondem.
- **M8 – Bar de drinks combinatório**: ingredientes do estoque dão drinks com propriedades e preço próprio,
  e descobrir receitas dá fama. Substitui a cozinha experimental pendente da Godot.
- **M9 – Demo de 3 dias** (já prevista no STEAM_PLAN): quiosque, pousada com negociação/limpeza e um teaser
  do salão de jogos.
- **Co-op** fica registrado como meta pós-lançamento. Até lá, novos sistemas guardam estado na simulação
  (não no ator) para facilitar a replicação no futuro.

## 8. Riscos

- **Desempenho**: muitos MetaHumans (hóspedes, banhistas e salão). Limitar a quantidade simultânea, usar
  LOD e grooms em cards, e medir no EXE.
- **Física da sinuca**: Chaos com bolas pequenas precisa de substepping/CCD. Validar a tacada em PIE antes
  de montar a IA.
- **Saves**: migração da renda passiva para estadias reais sem perder dinheiro nem cobrar duas vezes.
