# Quiosque: rotinas e decisões de gestão

> **Revisão vigente:** [Computador e balcão](COMPUTADOR_E_BALCAO.md). Gestão no PC com E; abrir o quiosque antes das chegadas; clientes pedem/retiram tudo no balcão antes de sentar. Porta funcional; balcão madeira escura/base cinza. Essa revisão substitui os fluxos antigos descritos abaixo.

> **Regra vigente — 23/10: sem preparo.** Pegar o produto pronto na geladeira,
> armário ou cozinha e entregar. Sem cronômetro e sem precisar cozinheiro.
> Compras abastecem o estoque; retirada desconta uma vez. Referências históricas
> a preparo abaixo foram substituídas por este fluxo. Saves antigos recuperam
> unidades já pagas sem consumir o estoque novamente.


Implementação das sugestões 2 a 7, em 22/10/2026. A revisão posterior reorganizou o acesso em seis áreas: consulte [QUIOSQUE_PRATICO.md](QUIOSQUE_PRATICO.md). No computador do balcão (E; B apenas perto), use Quiosque para rotina/horários/equipamentos/aparência, Equipe para candidatos/turnos, Compras para entregas e Finanças para resultado. Os saves anteriores recebem padrões compatíveis; o checklist obrigatório começa desligado.

## Rotina do dia

Feche novas chegadas para conferir limpeza do balcão, ingredientes e equipe. O herói pode trabalhar sozinho. A conferência do estoque exige ingredientes do cardápio; limpar o balcão restaura sua higiene. Preparos sujam o balcão, e a virada do dia também reduz a limpeza. Ative **Exigir checklist para abrir** se quiser que as três conferências sejam obrigatórias a cada dia. Prepare as primeiras bebidas em Operação antes de abrir.

Para fechar o turno, conclua clientes, preparo, itens carregados, contas e louça. O app permite devolver o item do herói/equipe à prateleira. Recebimentos e limpeza das mesas continuam sendo feitos no mundo. **Atualizar checklist e fechamento** atualiza a tela sem apagar automaticamente uma contagem em edição. A conferência compara o valor digitado com as vendas recebidas, sem gorjetas: registra a diferença e não cria/retira dinheiro. Salários e estrutura continuam sendo cobrados na virada do dia.

Com freezer e geladeira com estado/higiene de pelo menos 50%, guarde as bebidas antes da virada. As quantidades guardadas resistem a uma noite, apenas uma vez. Comidas continuam vencendo na virada; bebidas não podem ser conservadas indefinidamente. Sem guardar, vale a validade anterior. A perda não desconta ingredientes ou dinheiro novamente.

## Candidatos e funcionários

Cada cargo do quiosque tem três candidatos nomeados: em formação, ágil/experiente e cuidadoso/cordial. Compare taxa de contratação, diária base, velocidade, cuidado e simpatia. Há uma vaga por cargo; os contratados anteriores continuam funcionando com seus atributos anteriores. Candidatos novos usam seus multiplicadores de salário e desempenho. Cuidado do cozinheiro reduz risco de perdas; simpatia do garçom afeta gorjetas.

A diária anunciada considera nível 1 e turno de 8h. Turnos, experiência e folga continuam modificando o salário. Horas efetivamente trabalhadas no quiosque são registradas. Mais de 8h reduz satisfação e energia adicionalmente; dias sem trabalhar recuperam satisfação. Satisfação abaixo de 30% reduz produtividade. Energia baixa aumenta o risco de perder um preparo. Turnos, folgas, treinamento e rescisão ficam em Escala e equipe; a rescisão limpa o perfil da vaga.

## Entregas

Escolha ingrediente, quantidade e fornecedor. As cotações usam preço atual e contratos existentes:

| Fornecedor | Preço | Chegada |
|---|---|---|
| Mercado Express | +15% | Imediata |
| Horta da Vila | −12% | Amanhã às 08h |
| Distribuidora Costa | −20%, mínimo 12 unidades | Amanhã às 14h |

Previsão de tempestade acrescenta 1h ao prazo, mostrada na cotação. Pague na encomenda; não há cancelamento nesta versão. Se o preço mudar antes de confirmar, a operação recusa a cotação antiga. Limite de 48 unidades por pedido e 32 encomendas pendentes. Quantidade em edição permanece no formulário durante vendas/reposições. Ingredientes de entrega futura entram somente no horário prometido; salvar/recarregar não duplica a entrega nem a cobrança. O app mantém as últimas oito entregas.

Mercado e reposição automática anteriores continuam disponíveis. Compras e encomendas usam a mesma despensa compartilhada com o bar. O custo é lançado no pagamento, e não novamente no recebimento.

## Equipamentos

Geladeira, chapa e liquidificador possuem estado, higiene e três níveis. Cada lote perde 0,35 ponto de estado e 2 pontos de higiene nos equipamentos usados; a geladeira perde também 0,01 ponto por minuto aberto. O balcão perde 1 ponto de limpeza por lote e 5 na virada do dia. Coco usa geladeira; outras bebidas batidas usam também liquidificador; comidas usam chapa.

- Limpeza: R$ 3, 12 minutos do jogo, restaura higiene.
- Reparo: R$ 0,80 por ponto recuperado, arredondado para cima; 30 minutos do jogo.
- Melhoria: R$ 240 × nível atual; restaura estado e aumenta velocidade em até 20%.

Feche novas chegadas e termine o preparo antes de iniciar serviços. Apenas um serviço por vez; enquanto ele ocorre, não começa outro preparo. Estado baixo reduz velocidade; abaixo de 10% o equipamento para. Higiene abaixo de 15% impede preparar; higiene ruim e exaustão aumentam perdas, limitadas a 40% de risco por lote. O cuidado do cozinheiro reduz o risco. Perdas usam os ingredientes já gastos e entram em desperdício uma única vez. Serviços em andamento persistem no save. Avisos de equipamento não são repetidos a cada tentativa automática do cozinheiro.

## Personalizar

Escolha pintura, acabamento da placa, uniforme, disposição original/mais espaçada das mesas e exibição dos cardápios. A prévia mostra cores, placa, uniforme e esquema de disposição sem gastar ou mover o mundo. **Aplicar** custa R$ 180, com o quiosque fechado, sem clientes nem louça. Reaplicar a mesma seleção já comprada não cobra.

São reutilizados os modelos detalhados atuais: pintura nos painéis de madeira, acabamento das placas e cor das roupas dos funcionários. As mesas, assentos, pontos de entrega e bloqueios de circulação se movem juntos; os guarda-sóis acompanham as mesas. Não são criados novos móveis primitivos. Nome, fonte e cor das letras continuam no app Meu Quiosque. A identidade persiste no save; carregar um save sem personalização restaura o aspecto e a disposição originais.

## Movimento

O ritmo de chegadas do quiosque e as probabilidades de pratos variam por faixa: manhã leve/sucos e tapioca; almoço mais movimentado/refeições; tarde/bebidas; fim de tarde/petiscos e bebidas. Esses fatores se combinam com preços, calor, festas e eventos já existentes. Pratos ainda bloqueados não passam a ser vendidos por causa de uma preferência.

Chuva reduz a frequência de chegadas em 35%, com redução adicional na tempestade. Novas chegadas não ocupam mesas descobertas; balcão e mesas com guarda-sol continuam disponíveis. O app mostra os lugares utilizáveis e os fatores atuais. Não há garantia de vendas; é uma distribuição de chances. Clientes que já estão sentados mantêm o atendimento em andamento.

## Validação

`--loop-test --management-test`: abertura real, preços, encomenda e entrega única após save/recarga, candidato com taxa menor, salário, cansaço/satisfação, desgaste, bloqueios, serviços com duração, melhoria, risco de perda, prévia e compra pela interface, movimentação de malha/assento/colisão, uniforme real, horário/clima, seleção de mesa abrigada, fechamento, validade e persistência. `--phone-layout-test` percorre os 27 apps e início em três tamanhos. Ver os logs finais do pacote em VALIDACAO_1.1.0_LOCAL.md.
