# Computador, retirada e acabamento — 23/10/2026

A gestão agora fica no **computador sobre o balcão**. Entre por uma lateral,
mire no monitor e use **E**. A tela tem seis áreas: Quiosque, Compras, Equipe,
Finanças, Resort e Vila e lazer. B funciona perto do computador; longe dele
orienta a usar o terminal. Esc volta/fecha. As telas de retirada e reposição
continuam acessíveis por E na geladeira e no armário.

O quiosque começa **fechado**, inclusive na migração de saves antigos. Crie a
empresa no computador e use **Abrir quiosque** antes de receber clientes.
Horários e checklist continuam valendo. Abrir fora do expediente prepara a
abertura daquele dia; dormir fecha o negócio novamente. O estado deliberado
de abertura continua salvo, sem apagar estoque, dinheiro ou progresso.

No modo físico, o cliente reserva uma mesa, vai ao balcão e escolhe em pé.
E anota o pedido. Pegue os produtos prontos nas estações e entregue por dentro
do balcão. Só depois de receber **todos os itens** ele leva os produtos à mesa
para sentar e consumir. Duas posições de retirada, fila com paciência e liberação
da posição ao se afastar. Balcão não é assento de consumo no modo físico.
Garçom anota e entrega no balcão. Retirada desconta estoque uma vez; o trajeto
e a mesa não geram produtos, vendas ou cobranças adicionais. Sem preparo.
Modo legado mantém seu comportamento anterior.

Acabamento escolhido pelo usuário: **tampo em madeira escura e base cinza**.
Mantém veios, ripas, bordas e ferragens. Pintura da empresa não muda esse
acabamento. Bandeja com seis copos, sem caixa branca. Expositor de madeira
mostra duas ofertas com os preços reais do cardápio em ambas as faces;
texto reduzido pelas medidas da fonte para caber no papel. Não cria desconto
ou cobrança diferente do preço configurado.

A porta da casa é de madeira, com painéis e ferragens. E abre/fecha e a folha
fechada bloqueia passagem. Ao sair, fecha depois que o jogador libera o arco
da porta. Fechamento manual no vão pede para se afastar. Pausa congela a
detecção de saída. A colisão da folha é reativada ao terminar a animação.

## Implementação e verificação

- `phone_ui.gd` preserva a classe interna PhoneUI por compatibilidade; o produto
  é um terminal de gestão centralizado, com cantos arredondados e seis áreas.
- `kiosk_operations.gd` integra PC/interação, copos e promoções frente/verso.
  A área Interactable genérica do balcão tem 3,0×1,2×0,4 m e fica em z≈1,88
  (lado interno, à frente da madeira), para a mira do staff acertar o balcão
  sem cobrir o monitor em x≈1,70; colisões físicas da construção seguem separadas.
- `village_life.gd`: counter_first, dining_spot, counter_slot, kcounter_queue,
  kto_table. Reservas liberadas com verificação do dono, inclusive desistência.
- `company_rules.gd`: opening_version=1 migra estado antigo para fechado.
  `Core.sleep()` fecha o quiosque a cada novo dia.
- `home_door.gd`: folha com colisão, E, movimento e fechamento após saída.
- Fontes editáveis incorporadas em `art/blender`: kiosk_computer,
  player_home_door, kiosk_facade e kiosk_counter_details. Geradores em tools.
  A textura escura é incorporada já tingida: MixRGB não conservava esse tom
  na exportação glTF. Não escurecer toda a fachada para corrigir só o balcão.
- Testes: `--terminal-test`, `--counter-first-test`, `--company-test`,
  `--counter-test`, `--practical-test`, `--phone-layout-test`, `--home-test`,
  `--simulation-test`, `--management-test`, sempre após `--loop-test`.
  `tools/run_counter_batch.ps1` cria APPDATA isolado e aceita `-Exported`.
  Capturas dos novos testes vão para `user://qa_shots`; conferir também o PCK.

Este documento substitui instruções anteriores sobre gestão remota no celular,
abertura automática e atendimento de clientes já sentados nas mesas.
