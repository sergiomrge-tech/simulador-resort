# Quiosque reorganizado — 22/10/2026

Revisão 23/10: fachada e todas as mesas voltadas para a praia. No balcão, permaneça
dentro e mire no cliente para E anotar/entregar. A mira tolera pequenos desvios e
mostra o número do pedido, preservando a escolha entre os dois lugares.
Na geladeira/armário, produto esgotado oferece Repor 10 com preço dos insumos
faltantes. A compra acontece na mesma tela e permite retirar logo depois.

Pessoas sem óculos escuros, chapéus ou bonés, conforme preferência atual.

Pessoas refinadas em 23/10: proporções de cabeça e porte menos exageradas,
sombreamento suave da pele/cabelo, roupa com menos saturação e brilho lateral.
Sem colares de esferas nem estampas aleatórias nas calças. Sem chapéus/bonés.

Refinamento visual de 23/10: revestimento retangular em tons areia, juntas
mais suaves e pequenas variações cerâmicas. Luz de trabalho quente permanente
no interior reduz a predominância azul da iluminação ambiente sobre equipamentos.

Acabamento interno de 23/10: faixa de azulejos claros com juntas e bordas
arredondadas na área de preparo, prateleira de madeira com suportes de latão e
coifa modelada com filtro, duto e luz de trabalho. Equipamentos, corredor,
parede traseira e entradas laterais mantêm suas posições funcionais.

Revisão de roupas de 23/10: camisas com barra reta, sem cinto e abas inferiores
medievais. Calçados baixos substituem as botas de cano alto, com pernas da base
original preservadas entre o sapato e a calça. Cores dos calçados mais neutras.

A traseira agora tem parede de madeira com ripas e travessas, combinando com o
acabamento do balcão. A parede bloqueia passagem; as entradas laterais continuam
livres e todos os equipamentos ficam dentro. Pessoas usam roupas CC0 Quaternius
com pesos de animação originais, camisas, calças e calçados com acabamento suave.
Personagens sem chapéus e bonés, conforme pedido. Cabelos rígidos seguem a cabeça
por BoneAttachment3D, inclusive durante as animações de sentar e andar.

Contratação cria imediatamente o funcionário no quiosque, inclusive com o celular
aberto ou fora do horário. Ele trabalha apenas no turno; folga e demissão ocultam
o personagem. O atendente também aparece antes da criação da empresa.
A geladeira exibe 12 bebidas em duas fileiras nas três prateleiras. As etiquetas
continuam mostrando estoque real; a exposição no zero não pode ser vendida.

O quiosque mantém o acabamento novo e concentra o trabalho dentro da construção.
Entre por uma das laterais: geladeira à esquerda, retirada de pratos ao centro e
cozinha à direita. Caixa na frente e liquidificador no tampo lateral. Sem anexo externo.

## Como atender (atualizado: sem preparo)

Antes de pegar os produtos, vá até o cliente sentado. Quando ele terminar de
escolher, aparece **E · #pedido**; mire nele e aperte **E para anotar**. O pedido
entra na lista da tela e do celular. E novamente permite consultar; levando o
produto correto, E entrega. O garçom também caminha até a mesa para anotar.

1. E na geladeira para bebidas ou no armário/cozinha para alimentos.
2. Escolha **Pegar e levar ao cliente**. O produto vai imediatamente para sua mão.
3. E no cliente com o número correspondente para entregar.
4. Receba no caixa e recolha a louça. O garçom também retira direto, sem cozinheiro.

Não há botão Preparar, etapa de montagem nem cronômetro. Compras abastecem o
estoque compartilhado; retirar desconta os insumos uma vez. Devolver guarda uma
unidade pronta, que pode ser retirada de novo sem novo desconto. Saves antigos
convertem o preparo já pago numa unidade pronta, uma única vez.

Geladeira e armário mantêm **expositores com os produtos vendidos**, inclusive quando
o estoque vendável chega a zero. Cada receita tem uma vaga fixa e uma etiqueta de
quantidade; no zero, indica repor estoque. Receitas básicas ainda indisponíveis
ficam identificadas para desbloquear, e receitas secretas aparecem ao descobrir.
O exemplar de exposição não pode ser retirado nem vendido sem estoque. A retirada
desconta o estoque uma vez; entrega e retirada de um item devolvido não descontam
novamente. Sem estoque, use Compras.

## Celular

A tela inicial tem seis áreas, sem repetir os antigos 27 atalhos:

| Área | Funções |
|---|---|
| Quiosque | Abrir/fechar, pedidos, cardápio/receitas, horários/rotina, equipamentos e aparência/nome |
| Compras | Ingredientes, fornecedor, prazo, quantidade e reposição automática |
| Equipe | Pessoal, turnos, treino, folgas e escolha de candidatos por vaga |
| Finanças | Recebimentos, custos, resultado e extrato |
| Resort | Construções, quartos, hotel, evolução e negócios |
| Vila e lazer | Agenda/clima, missões, moradores e álbum |

Voltar retorna à área correspondente. Preparar/retirar são ações de **E nos
equipamentos**, sem app solto na tela inicial. Marca: Quiosque → Aparência e nome
→ Nome e letras da placa. Custos, entregas, validade e salários preservados.

## Visual e tela

Ripas, tampo acabado, colunas torneadas/amarras, placa única com moldura e contorno
de neon na expansão, luminárias de fibra, plantas suspensas e cobertura baixa com
doze fiadas de palha. Modelos originais Blender; fontes editáveis em `art/blender/`.

HUD: valores 20 px, interação 16 px, avisos 15 px. Sem dica redundante no topo.
Até três pedidos no canto, ocultos com o celular aberto ou longe do quiosque.
Até dois avisos simultâneos, com repetidos filtrados. Funcionários sem nomes grandes.

## Validação

`--loop-test --practical-test` caminha pelas entradas/corredor com colisão real,
verifica o piso, bloqueia retirada por trás da geladeira, confere ingredientes
visíveis, preparo/retirada/entrega e navegação. Com renderização, captura interior,
pedidos, estação, celular e fachada. Saves de teste separados do progresso do jogador.
Executar também as regressões de empresa, gestão, celular e o ciclo geral.
