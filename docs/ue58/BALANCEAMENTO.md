# Balanceamento — primeira passada (02/11/2026)

Modelo reproduzível: `python tools/ue58/balance_model.py [dias]`. Ele lê os dados do jogo e simula um jogador médio,
que compra cada expansão e negócio assim que o dinheiro, os pré-requisitos e a fama deixam.

A escala de tempo medida no PIE é de 1 minuto do jogo por segundo real. Um dia jogado vai das 8h às 24h e dura
cerca de 16 minutos reais.

As hipóteses ficam marcadas `ASSUME` no script. São elas que precisam ser trocadas por números medidos jogando:
- clientes atendidos;
- drinks por hora;
- passeios guiados;
- tarefas nos negócios.

## Resultado do modelo (sem personalização)

| Dia | Tempo real | O que é comprado |
|---|---|---|
| 1 | 0,3 h | mesas, bebidas, neon |
| 2–3 | 0,5–0,8 h | grill, Bar do Coqueiro |
| 5 | 1,3 h | pousada, sorveteria |
| 6 | 1,6 h | piscina |
| 7–9 | 1,9–2,4 h | passeios e os outros 4 negócios |
| 16 | 4,3 h | Grand Hotel (R$ 30.000) |
| 17 | 4,5 h | salão de jogos |

A renda diária sobe de cerca de R$ 600 no dia 1 para R$ 4.400 no dia 10 e R$ 6.800 depois do hotel.

## Leitura

- **Ritmo inicial:** um desbloqueio por dia jogado, ou seja, a cada 15–20 minutos. Isso cumpre a meta de 10–20 min
  do roteiro.
- **Buraco do meio:** do dia 9 ao 16, cerca de 2 h, o jogador só junta dinheiro para o Grand Hotel. Esse trecho
  precisa ser preenchido pela personalização e pelas receitas (abaixo) e pelos capítulos da vila. Se o playtest
  mostrar tédio, crie metas intermediárias ou reduza o hotel para cerca de R$ 22.000.
- **Fim do conteúdo novo:** a última compra é o salão, por volta de 4,5 h. Daí em diante o dinheiro vai para a
  personalização e as receitas:
  - deixar todos os 15 lugares da personalização no nível máximo custa cerca de R$ 857 mil (preço base de
    R$ 16.320 × multiplicadores 2,5 / 6 / 14 / 30);
  - melhorar as receitas do quiosque custa mais cerca de R$ 68 mil;
  - no ritmo de R$ 6.800 por dia, isso dá dezenas de dias. A meta de 6–10 h do Acesso Antecipado depende de esses
    níveis darem retorno visível: mais estrelas, clientes e fama.
- **Fama:** o modelo chega à fama 7 no dia 16 e à 10 no dia 25. Na Godot, o Grand Hotel pedia fama 8 e o capítulo do
  carnaval; no Unreal ele só pede piscina e passeios. Exigir fama 8 seguraria o hotel até o dia 17–18 e daria mais
  sentido aos capítulos.

## Recomendações (aplicar depois de medir jogando)

1. Fazer um playtest cronometrado do zero até o hotel, anotando os números `ASSUME`, e rodar o modelo de novo.
2. Grand Hotel: exigir fama 8 (como na Godot) e manter o preço; se o buraco do meio cansar, baixar para R$ 22–25 mil.
3. Mostrar no celular a próxima meta e quanto falta (objetivo sempre visível, item do tutorial).
4. Salários: a equipe toda contratada custa cerca de R$ 265 por dia, menos de 10% da renda do meio do jogo. Para a
   contratação pesar, subir os salários 1,5× ou fazer o salário crescer com a fama.
5. Eventos: festa com decoração rende 1,7×. Se o playtest mostrar que o jogador compra decoração sempre, subir a
   decoração de R$ 120 para R$ 200–250.

## Segunda passada — Acesso Antecipado (04/11/2026, Sergio: "campanha precisa ser 12 h mínimo")

- **Relógio:** voltou a 1 minuto do jogo por segundo real (estava 2×, herdado do primeiro checkpoint). Um dia das
  8h às 24h dura 16 minutos reais, a escala que este modelo sempre pressupôs, e a subida diária ao Seu Tibúrcio
  (~3 min) cabe no dia.
- **Grand Hotel:** fama 9 (era 8) + capítulo do carnaval.
- **Ato 5 "Maré Alta de verdade"** entre o hotel e a festa final: salão de jogos, 20 níveis de receita, 40 melhorias de
  personalização, fama 10 e 4.000 vendas no quiosque. O dinheiro sobra a partir do dia ~22; quem dita o ritmo são
  as vendas (jogo de verdade, não espera) e a fama.
- **Resultado do modelo:** hotel no dia 21, festa no dia 55, cerca de **15 h**. A personalização aumenta a chegada de
  clientes (o modelo não conta), então a festa deve vir alguns dias antes, ainda acima de 12 h. Confirmar com
  playtest cronometrado e, se ficar abaixo, subir a meta de vendas.
- **Ritmo/objetivo visível:** o painel de missões mostra a tarefa da missão atual e, nas compras, quanto falta
  ("R$ 12.400 / 30.000 · fama 7/9"). Tarefas que se sobrepõem no dia: quiosque, oferenda diária no cume, bar,
  hóspedes, eventos cômicos, capítulos e minijogos.
