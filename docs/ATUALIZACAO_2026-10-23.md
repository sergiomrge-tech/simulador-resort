# Maré Alta Resort 1.1.0 RC2 — atualização de 23/10/2026

Esta revisão reúne as atualizações do quiosque e as correções de validação do
checkpoint 07cbb20. O menu identifica a revisão como RC2 · 23/10/2026.

- Computador no balcão para gestão: E no monitor; B funciona perto dele.
  Seis áreas principais, cantos arredondados e tela mais compacta.
- Abra o quiosque no computador para receber clientes. Cada novo dia começa
  fechado. Horários e checklist continuam valendo.
- Clientes pedem e retiram todo o pedido no balcão antes de sentar nas mesas.
  Estoque descontado uma vez, fila e garçom preservados, sem etapa de preparo.
- Tampo de madeira escura e base cinza, seis copos na bandeja, promoções nas duas
  faces do expositor e retirada da caixa branca.
- Porta da casa abre e fecha com E e fecha após sair com a passagem livre.
- Área de interação do balcão corrigida para atender por dentro sem bloquear o PC.
- Corrigida uma instância temporária de coco que ficava órfã no cache dos
  coqueiros. Encerramento libera a cena antes dos materiais usados pelo renderer.

## Como jogar e atualizar

Baixe o ZIP da release, extraia a pasta inteira e abra **Jogar.vbs** ou
**MareAltaResort.exe**. Não tente executar o jogo dentro do ZIP. O arquivo PCK
deve ficar junto do executável. Jogar.vbs guarda progresso/configurações em
userdata, dentro da pasta do jogo.

Ao atualizar uma cópia portátil, preserve a pasta **userdata** e substitua os
arquivos do programa. O download não inclui saves. Instalações antigas não são
alteradas automaticamente. O primeiro carregamento de save anterior pode exigir
abrir o quiosque novamente no computador, preservando estoque e dinheiro.

WASD anda, mouse olha, E interage, Shift corre, Esc volta/abre o menu.

## Verificação técnica

Godot 4.5.1, Forward+ / Vulkan, dados de teste isolados do progresso do jogador.
Resultados finais e hashes são registrados em VALIDACAO_2026-10-23.md após
concluir os testes do executável exportado. Fontes Blender, geradores, catálogo
e instruções para continuidade acompanham o código no GitHub.
