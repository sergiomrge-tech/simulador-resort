# Quiosque reorganizado — 22/10/2026

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

## Como atender

1. Mire na geladeira (bebidas) ou cozinha (comida) e aperte **E**. A estação informa
   o estoque disponível e o consumo de cada receita. Pedidos pendentes aparecem primeiro.
2. Escolha **Preparar**. A tela fecha e o andamento aparece discretamente no jogo.
3. Quando ficar pronto, use **E** na geladeira ou na retirada de pratos e escolha
   **Retirar e levar ao cliente**. Você carrega um item de cada vez.
4. Cada cliente tem um marcador como **#03**. A lista no canto relaciona esse número
   ao lugar e aos itens pendentes. **✓** indica unidade pronta para retirar. Mire no
   cliente correto e aperte **E**.
5. Receba no caixa e recolha a louça quando o cliente sair.

Geladeira e armário mantêm **expositores com os produtos vendidos**, inclusive quando
o estoque vendável chega a zero. Cada receita tem uma vaga fixa e uma etiqueta de
quantidade; no zero, indica preparar mais. Receitas básicas ainda indisponíveis
ficam identificadas para desbloquear, e receitas secretas aparecem ao descobrir.
O exemplar de exposição não pode ser retirado nem vendido. O preparo consome
ingredientes uma vez e abastece o estoque real; retirada e entrega não consomem
ingredientes novamente. Sem ingredientes, use Compras.

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
