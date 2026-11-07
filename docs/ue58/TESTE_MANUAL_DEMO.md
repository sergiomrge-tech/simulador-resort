# Roteiro manual da demo — primeira instalação (~2 h, sem cronômetro)

**Objetivo:** Sergio, em PC Windows com build candidata da demo de `Coconut Coast: Resort Simulator`, percorrer **um save novo, sem QA** até a tela final, registrar dinheiro, fama, capítulo, rádio, piscina, falhas e screenshots reais. A duração é uma meta editorial aproximada; se o percurso durar mais, registrar o tempo de fato. Demo ≠ Grand Hotel/quitacão integral da dívida.

## Antes de começar (0–5 min)

1. Anotar versão, commit/build ID, resolução, preset, GPU, sistema e idiomas pt-BR/en. Usar perfil Steam/teste separado e **slot vazio**; não apagar saves pessoais. Conferir áudio e controles.
2. Cronômetro REAL externo começa quando clica **Novo jogo**. Não usar `mare.QA`, `mare.ShowUI`, `mare.Shot`, `mare.PoolSwim` ou coast clock neste teste: todos alteram observação ou estado e invalidam a medida do percurso.
3. Preparar anotações com saldos antes/depois de cada pagamento, custo de cada compra, nível de fama e capítulo. Capturas reais via Steam F12 (overlay) ou captura do SO, sem esconder defeitos.

## Percurso por janelas aproximadas

| Tempo real | Ação na partida nova | O que conferir e anotar | Falhas mais prováveis |
|---|---|---|---|
| 00:00–00:10 | Chegada de ônibus → entrar na casa → abrir a carta de Dona Dilce → sair | Avó viva, herança, **R$ 1.000.000**, nenhuma cutscene presa, E funciona, dica cabe na tela; primeira partida sem conteúdo futuro | Porta sem alcance, ponteiro travado, carta com texto cortado |
| 00:10–00:20 | Celular → nome da empresa → placa **ABERTO** | Empresa criada uma vez, caixa inicial e missão; cliente só chega depois da placa/horário | Placa invisível, tutorial repetido, UI desatualizada |
| 00:20–00:35 | Atender 3+ clientes do lado INTERNO do quiosque; E no pedido → produto PRONTO → entregar | Pagamento exatamente uma vez **na entrega**; estoque cai uma vez, caixa aumenta uma vez, fama apenas nos eventos previstos | Cobrar ao anotar, cobrar duas vezes, item flutuando, NPC preso |
| 00:35–00:45 | Comprar/repor insumos pelo celular e no armário; checar receitas, equipe e missões | Saldo antes/depois igual ao custo mostrado, nenhum saldo duplicado; dica de cada aba só uma vez | Estoque negativo, compras sem cobrança, botão sem resposta |
| 00:45–00:55 | Contratar atendente (se dinheiro permitir); observar atendimento e explorar quiosque | Contratação cobrada apenas uma vez; funcionário não cria caixa paralelo; música: E no aparelho passa faixa, celular anterior/próxima/desligar; música off não elimina mar/efeitos | Rádio em silêncio (auditoria P0), botões não mudam título, volume perde estado |
| 00:55–01:05 | Dormir na cama → ler resumo → fechar/abrir o jogo e carregar slot | Dia avança, placa fecha, despesas e salários **uma vez**, dados/posição/capítulo/dica persistem | Save falha, salários dobram, relógio e vendas voltam |
| 01:05–01:20 | Comprar expansão acessível → Bar do Coqueiro; atender drink | Requisito de fama/custo correto, saldo descontado uma vez, preparo específico do bar, pagamento e nota | Expansão liberada sem requisito, receita quebrada |
| 01:20–01:35 | Pousada: negociar diária, check-in, tarefas de quarto; conferir piscina | Quarto limpo para check-in, diária e avaliações; piscina limpa/picolés/banhistas se disponível, sem tobogã do hotel | Check-in em quarto sujo, banhista imobilizado, piscina vazia em dia/horário válido |
| 01:35–01:45 | Passeios: bilheteria, barco ou trilha e missão do morador | Clima/horário e permissões; dinheiro, fama, gorjetas e objetivo só após ação concluída | Bilhete vendido sem saída, participante some, salvamento |
| 01:45–02:00+ | Avançar capítulos da vila, concluir conteúdo disponível, abrir tela de agradecimento | Título da próxima etapa **“A Maré Alta da vila”**, Grand Hotel bloqueado na demo; tela final não exige pagar R$ 1 mi; lista de desejos leva ao jogo PRINCIPAL; **Continuar jogando** não apaga save | Final não dispara, link vazio/errado, tela prende controles, missão invisível |

**Se a campanha exigir mais de duas horas:** continuar até chegar ao encerramento narrativo, sem usar trapaças. Anotar qual requisito atrasou, para calibrar o marketing. **Se a dívida ainda não estiver integrada:** marcar bloqueador da build; não presumir funcionalidade a partir do JSON.

## Regressões obrigatórias antes de enviar a Steam

- Pausar durante atendimento e minijogo; voltar sem cobrança dupla e sem movimento oculto.
- Testar música desligada e volume de efeitos audível; reiniciar e verificar persistência.
- Duas tentativas de entrega rápida do mesmo pedido (não gerar segunda receita).
- Fechar/reabrir jogo depois de dormir, depois de compra e no meio de uma missão; comparar estado real.
- Rodar pelo menos mais um idioma (en), textos longos, fontes CJK em smoke separado, e UI 85%/150%.
- Inspecionar itens soltos, cabelos e banhistas, vidro, água, NPCs colidindo, noite/chuva e FPS; registrar a configuração real.

## Planilha de evidências (preencher durante a sessão)

| Hora real | Cronômetro | Dia/hora no jogo | Etapa/ação | Caixa antes → depois (R$) | Fama/nível | Capítulo/missão | Resultado esperado × obtido | Gravidade | Foto/vídeo e nome do arquivo |
|---|---|---|---|---|---|---|---|---|---|
| ___ | 00:00 | Dia 1 / ___ | Novo jogo | ___ → ___ | ___ | ___ | ___ | ___ | ___ |
| ___ | ___ | ___ | Entrega 1 | ___ → ___ | ___ | ___ | ___ | ___ | ___ |
| ___ | ___ | ___ | Rádio | ___ → ___ | ___ | ___ | ___ | ___ | ___ |
| ___ | ___ | ___ | Expansão | ___ → ___ | ___ | ___ | ___ | ___ | ___ |
| ___ | ___ | ___ | Tela final | ___ → ___ | ___ | ___ | ___ | ___ | ___ |

**Severidade:** P0 = impede continuar/perde save; P1 = dinheiro/fama errado ou mecânica fundamental; P2 = UI/áudio/visual; P3 = cosmético. Anotar a sequência exata e o build ID para reproduzir.

## QA técnico separado (não vale como playtest)

**Somente depois da sessão orgânica**, em save temporário e com Unreal Editor/servidor MCP aberto:
```text
mare.ShowUI play
mare.ShowUI phone0
mare.ShowUI options
mare.ShowUI letter
mare.ShowUI close
mare.QA money 500000
mare.QA buy bar
mare.QA buy pool
mare.PoolSwim 6
mare.PoolSwim dump
mare.PoolSwim auto
mare.Shot D:/CodexTemp/qa/demo_falha.png
```
A câmera e o relógio de QA são operados por `tools/ue58/qa/qa_gate.py`: `coast('clock','660')`, `coast('pie','qa_<nome>,x,y,z,pitch,yaw')` e `coast('pie','qa_<nome>!,0,0,0,0,0')`. Não executar `mare.QA buy` em saves reais; não publicar capturas forçadas como conquistas naturais. Para pacote de imagens, usar `tools/ue58/qa/marketing_shots.py` apenas com imagens reais e revisão humana. O comando `mare.Shot` não substitui o F12 do jogador.

## Aceite

**Aprovado para submissão apenas se:** nenhuma perda de save, nenhum bloqueio de missão, cobranças e fama consistentes, rádio e música válidos e licenciados, 10 capturas reais verificadas, tela final acessível, tradução legível e link correto. Assinar: build ___ / duração ___ / bugs P0 ___ / P1 ___ / decisão ___.
