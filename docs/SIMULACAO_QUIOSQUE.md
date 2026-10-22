# Gestão do quiosque — expansão local de 22/10/2026

> Ampliação posterior no mesmo dia: [ROTINAS_QUIOSQUE.md](ROTINAS_QUIOSQUE.md) documenta os seis novos apps de rotina, candidatos, entregas, equipamentos, personalização e movimento. No pacote, leia ROTINAS_DO_QUIOSQUE.md. As regras abaixo continuam válidas, com a nova exceção de guardar bebidas no freezer por uma única noite. Os seis apps novos aparecem antes dos apps citados nesta seção.

Solicitação do Sergio: implementar as três frentes de simulação (estoque/fornecedores, equipe/turnos e custos/preços/resultado), além de horários e personalização da placa.

## Acesso

Abra o celular com **B**. Os primeiros apps são **Meu Quiosque**, **Horários**, **Estoque e perdas**, **Escala e equipe** e **Resultado**. Mirar na placa frontal e apertar **E** abre Meu Quiosque. Personalize nome (até 24 caracteres), fonte e cor e use **Salvar nome e placa**. A prévia e as duas placas reais recebem a marca.

## Expediente

- Abertura e fechamento em horas inteiras, entre 06h e 23h, sem atravessar a meia-noite.
- Escolha os dias da semana. Dia 1 é segunda-feira. Os saves antigos preservam 08h–18h, ou até 21h com neon, até salvar um horário personalizado.
- **Fechar quiosque** impede novas chegadas, mantendo os pedidos existentes até o término do expediente. O horário de encerramento conserva a regra do jogo de mandar os clientes embora.
- O botão de abertura fora do expediente prepara a abertura para o próximo horário/dia programado.
- A escolha manual e a escala persistem no save. A placa ABERTO/FECHADO muda imediatamente.

## Estoque e fornecedores

- Meta de 1 a 48 unidades por ingrediente necessário ao cardápio atual.
- Reposição manual ou automática na virada do dia. A compra considera estoque existente, cotação atual e contratos do Mercado.
- O orçamento do pedido inteiro é conferido antes de comprar: sem saldo suficiente, não há compra parcial. Repor novamente acima da meta não cobra nada.
- Produtos preparados nas prateleiras, carregados ou em produção vencem na virada do dia. Ingredientes crus continuam usando o sistema existente de deterioração/freezer/tempestade.
- O relatório conta produtos desperdiçados; não desconta o valor deles novamente, pois os ingredientes já foram comprados.
- A despensa é compartilhada com o bar; o painel deixa isso explícito.

## Pessoas e produtividade

- Garçom, caixa, limpeza, cozinheiro e atendente têm contratação, diária, traço, XP, energia, treinamento e folga.
- Novas contratações recebem turno de até 8 horas, a partir da abertura. Edite a entrada/saída em cada ficha.
- Trabalham somente dentro do expediente, nos dias abertos, dentro do turno e quando não estão de folga.
- Turno personalizado: diária × duração/8, com mínimo de meia diária. Nível, traço econômico e folga continuam afetando o salário. Folga explícita paga metade.
- Turnos longos aumentam o cansaço e a experiência na virada. Dias sem expediente recuperam energia. Energia baixa reduz rendimento, como no sistema existente.
- Funcionários de saves antigos seguem o expediente com a diária base até receberem uma escala personalizada.
- Salários são pagos uma vez por dia, inclusive na passagem natural pela meia-noite. Dormir ou recarregar não repete o pagamento da equipe do quiosque.
- Dispensa tem rescisão de três diárias atuais. Requer saldo; um produto nas mãos do garçom precisa voltar à prateleira antes da saída.

## Custos, preços e resultado

- Dias com operação cobram R$ 12 de estrutura mais R$ 2 por hora aberta. Sem tempo aberto, não há cobrança de estrutura.
- Painel mostra recebimentos, compras da despensa, salários pagos, contratação/treinamento/rescisão, horas abertas, contas pendentes e faltas de estoque.
- Sete fechamentos ficam no histórico, com saldo, custo de estrutura e desperdício.
- O saldo é **resultado de caixa**, não lucro contábil por prato: as compras são da despensa compartilhada e contas pendentes só entram quando recebidas.
- Cardápio e Resultado usam cotação/contratos atuais para estimar custo dos ingredientes e margem bruta. Preços continuam usando os níveis de preço, com efeitos reais na demanda e nas avaliações já existentes.

## Implementação e validação

Regras da simulação em `scripts/kiosk_simulation.gd`; persistência via `company.sim` no save v7. Dados antigos recebem padrões compatíveis. A migração trata os números que o JSON carrega como floats, inclusive os dias da semana, para não fechar a empresa ao recarregar.

`tests/simulation_regression.gd`, executado por `--loop-test --simulation-test`, verifica horário/dias inválidos, orçamento e contratos, reposição sem duplicação, contratação, turno, salário, folga, cansaço, estrutura, conciliação do relatório, desperdício, fechamento idempotente, reposição automática, save/recarga e rescisão. Os painéis são abertos na cena real. Há testes de empresa/assentos e ciclo completo separados.

Os logs finais ficam em `build/logs/simulation-*.log` e as capturas em `shots/simulation_*.png`. O pacote jogável é reexportado em `build/rc2-playable`; o checksum corrente fica em `SHA256SUMS.txt`. Não substitui a instalação original nem publica uma release automaticamente.
