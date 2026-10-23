# Quiosque de frente para a praia — 23/10/2026

> **Revisão vigente:** [Computador e balcão](COMPUTADOR_E_BALCAO.md). Gestão no PC com E; abrir o quiosque antes das chegadas; clientes pedem/retiram tudo no balcão antes de sentar. Porta funcional; balcão madeira escura/base cinza. Essa revisão substitui os fluxos antigos descritos abaixo.

Fachada, balcão, lugares dos clientes e todas as mesas/guarda-sóis agora ficam
do lado da praia. As entradas laterais e a área interna continuam utilizáveis.
Os caminhos dos clientes e funcionários acompanham a orientação; personalização
do layout move modelos, assentos e bloqueios juntos. Saves antigos gravados
dentro da construção acompanham a rotação uma vez para evitar aparecer no móvel.

No balcão, permaneça dentro e mire no cliente: E anota quando ele termina de
escolher; levando o produto correto, E entrega. O prompt mostra o número do
pedido. A área de seleção é maior e aceita pequenos desvios; paredes ainda
bloqueiam. O cliente leva os produtos à mesa após retirar todo o pedido no balcão.

E na geladeira/armário abre a estação. Se o produto esgotar, Repor 10 mostra o
valor e os ingredientes faltantes para dez porções. A compra usa os preços e
contratos do dia, verifica o saldo do conjunto e não compra parcialmente. Os
insumos já existentes não são cobrados. A tela permanece aberta; pegue o produto
pronto assim que a reposição terminar. O estoque continua compartilhado e a
retirada desconta uma vez; sem mecânica de preparo.

Praia: quatro pessoas trocam a bola de vôlei em trajetórias sobre a rede, com
movimento corporal/contato dos braços. A quadra fica ao lado do quiosque, livre
de guarda-sóis e espreguiçadeiras. Funciona das 08h às 18h30 e para na chuva.
Um navio de madeira passa devagar ao fundo das 06h às 19h; o cruzeiro com
janelas iluminadas fica ancorado das 19h às 06h, em posição fixa e sem esteira.
Todos ficam no mar distante, fora do cais e da faixa de banho.
São elementos de ambientação, sem embarque nem minijogo de vôlei nesta revisão.
Pausa congela seu movimento.

Implementação: world_village.gd (kiosk_point/kiosk_local e frame),
kiosk_operations.gd (balcão e foco), player.gd (seleção), phone_ui.gd e
resort_core.gd (reposição), coastal_life.gd/volley_arm.gd (praia).
Assets: tools/gen_coastal_traffic.py e fontes Blender coastal_*.blend;
origens/licenças no CREDITS.md. Testes --counter-test e --coastal-test,
além de --company-test, --practical-test e layout do computador. Dados sempre isolados.


Revisão posterior: um único navio de madeira e velas por vez, passando devagar
durante o dia, asset Ship Pinnace CC0 Poly Haven. Cruzeiro fixo à noite.
Duas baleias saltam alternadamente ao fundo, com respingos balísticos, espuma,
ondas circulares e som suave posicional respeitando mute/SFX. Céu com nuvens
suaves animadas, cor acompanhando horário e chuva. Animações congelam na pausa.

Cruzeiro refinado: modelo Blender detalhado, com cabines/varandas, botes,
conveses, radar e iluminação de janelas parcialmente apagadas. Escala maior
para leitura desde a praia, ancorado em Z=-210, sem esteira. A prévia low poly
Quaternius foi rejeitada e retirada. Assets gratuitos mais detalhados foram
localizados em Sketchfab/BlendSwap, mas o download exigiu login; não instalados.
