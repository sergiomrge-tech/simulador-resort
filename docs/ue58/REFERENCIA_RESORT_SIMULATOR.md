# Dicas do "Resort Simulator" (Fishleaf Games) para o Coconut Simulator — 07/11/2026

Pedido do Sergio: "olhe esse jogo, é assim que o nosso deveria ser, pelo menos na jogabilidade e animação das pessoas";
"veja os vídeos na Steam e pegue dicas". Fonte: as 10 capturas e o trailer (1min34s) da página
https://store.steampowered.com/app/4319390/Resort_Simulator/ (vistos em quadros a cada 3 s).
É referência de jogabilidade e animação: **não copiar nome, arte, interface nem conteúdo.**

## O que eles fazem bem (visto nos quadros)

| # | Observado | Ideia para o nosso jogo | Onde |
|---|---|---|---|
| 1 | O objeto mirado ganha **contorno colorido** (a cama aparece com borda verde-amarela). | Contorno no alvo do E (custom depth + pós-processo), além do botão embaixo. | `MareServiceTarget`, pós-processo |
| 2 | **Dica de controle no canto** com ícone: "Clique esquerdo: arrumar a cama", "Clique direito: devolver", "G: jogar". | Lista curta de ações do alvo atual, com o ícone da tecla ou do botão do controle. | HUD |
| 3 | **Pedidos em lista à direita** ("Quarto 101 precisa de chinelos"). | Pedidos do quiosque, das mesas e das reclamações dos quartos numa lista fixa à direita, sem sumir ao abrir uma estação. | HUD (feito em parte: os bilhetes ficam visíveis na estação) |
| 4 | **Retorno visual satisfatório**: nuvem de espuma e brilho ao arrumar a cama. | Partículas ao limpar a mesa, arrumar o quarto e entregar o pedido; moedinha subindo ao receber. | Niagara |
| 5 | **Bagunça física** no chão do quarto (roupas, toalhas, chinelos), recolhida item a item. | Quartos e mesas com sujeira em objetos de verdade (copos, guardanapos, toalhas). | Pousada e quiosque |
| 6 | **Caixa físico**: gaveta com notas e moedas para dar o troco; maquininha com teclado. | Minijogo opcional do troco no quiosque (cliente paga em dinheiro ou cartão). | Quiosque |
| 7 | **Repor prateleira com contador** (3/8) a partir de uma caixa de produto. | "Repor 10" vira levar a caixa e colocar unidade por unidade (com opção rápida). | Geladeira e armário |
| 8 | **Tablet de gestão** com abas grandes (Quartos, Móveis, Decoração, Funcionários) e cartões com +/- e carrinho. | Celular com cartões +/- e carrinho nas compras. | Celular |
| 9 | **Pessoas vivas**: grupos andando juntos, gente de sacola, sentada no banco de chinelo, banhistas em toalhas e espreguiçadeiras, cliente no banquinho do bar **recebendo o drink da mão do bartender**. | Mais clipes de animação (entregar e receber, beber, conversar em grupo, deitar, pegar da prateleira, pagar); grupos de 2 a 3 andando juntos; ninguém travado. | `MarePerson`, `MareServiceAnimation` |
| 10 | **Tobogã**: calha aberta e colorida, com uma pessoa deitada descendo e caindo na água. | Refazer a saída reta como calha aberta, com borda e água escorrendo (o nosso tem uma caixa fechada). | `gen_water_slide.py` |
| 11 | **Entrega no quarto**: o hóspede abre a porta e recebe o item. | Serviço de quarto na pousada e no hotel com a animação da porta. | Pousada |
| 12 | **HUD enxuto**: nível, XP e estrelas no canto superior esquerdo; dinheiro, relógio e dia à direita. | Rever o nosso HUD para ficar igualmente limpo. | HUD |
| 13 | **Ruas cheias** de gente e de carros estacionados; tudo colorido e limpo. | Mais pedestres em grupos na vila (sem passar do orçamento de CPU). | Vila |

## Prioridade sugerida (jogabilidade e animação das pessoas)

1. Ninguém travado e poses naturais (clientes, banhistas, bar), com mais clipes gratuitos de animação.
2. Contorno no alvo e dicas de controle no canto.
3. Lista de pedidos fixa à direita e retorno visual ao entregar e ao limpar.
4. Repor com caixa e contador; troco no caixa (opcional).
5. Grupos de pedestres e entrega no quarto.
