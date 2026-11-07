# Natação e prévia Windows UE5.8

Branch `codex/ue58-migration`, projeto ativo em `D:/Projetos/MareAltaUE58`.
Pedido: permitir que o herói nade e fazer os ajustes necessários para um teste
executável. A conversão integral continua em andamento; manter a instalação e os
saves Godot aprovados.

## Implementação

- Natação nativa de CharacterMovement no mar, com flutuação, avanço, mergulho,
  subida e volta à caminhada na areia. WASD move, mouse orienta, Espaço sobe,
  Ctrl ou Shift mergulha. Shift corre em terra.
- PhysicsVolume acompanha o oceano em Z=-30 cm e começa em Y=-3200 cm.
  PhysicsOnContact desativado: o corpo deve entrar no volume; andar acima no cais
  não deve ativar natação. O volume é recriado por `mare_water.ensure_volume`,
  também chamado pelo construtor do mapa e exposto no MCP.
- A água renderizada não é sólida. Definir UseDefaultCollision=false e perfil
  NoCollision, além de CollisionEnabled. Só alterar CollisionEnabled deixou a
  superfície bloquear a cabeça ao subir. A inspeção visual revelou o problema
  apesar de o teste inicial indicar Swimming. A regressão agora exige também
  câmera acima da água e centro do personagem na faixa correta.
- Transição de cor/vinheta submersa e recuperação para a última posição segura
  em terra se o personagem cair abaixo do mundo. Não há dano por afogamento.
- Coast é o mapa de abertura do jogo. Esc abre pausa com retomar, salvar,
  qualidade média/alta e sair. Pausa e celular não sobrepõem controles.
- Configuração inicial: janela 1280x720, limite 60 FPS, escalabilidade alta e
  resolução interna de 80%. São valores iniciais, não uma medição de desempenho.
- PreExposure=8 cobre a faixa de exposição usada pelo sol físico e elimina o
  aviso de clipping do cache de iluminação visto nas capturas iniciais.

## Teste reproduzível

`AMarePreviewQA` só executa com `-MarePreviewQA` e um `-MareSaveRoot` explícito
dentro de `D:/CodexTemp/`. Nunca passar esses parâmetros ao perfil do jogador.
Ele injeta as teclas reais no PlayerController, observa movimento/posição,
valida os assets dinâmicos do catálogo, celular, pausa e save, grava JSON e
capturas no perfil descartável. No pacote, encerra ao terminar.

O teste por MCP/PIE passou 15 verificações em
`docs/qa/ue58/swimming-pie.json`. O catálogo completo foi acrescentado depois
para ser exercitado no pacote. Dados e imagens anteriores à correção da colisão
não são evidência do resultado final.

Empacotamento: `tools/ue58/package_preview.ps1`. Não executar simultaneamente
com outro UBT: o UAT falha com ConflictingInstance. Builds, cache, temporários,
arquivos de teste e entrega ficam no D. A publicação exige confirmar o resultado
do pacote exportado e suas imagens, não apenas o executável do editor.

## Limites da prévia

A câmera é em primeira pessoa e ainda não possui braços/corpo com animação de
natação. O lote seguinte implementou áudio e refinamento visual, com sol/luar
ligados ao relógio. Ainda faltam os demais negócios, salários, capítulos completos,
clima completo, animação dos navios/baleias/animais, opções completas e revisão
integral da migração de progresso. A prévia não substitui a versão Godot aprovada.

## Resultado do pacote

Guia posterior: [Áudio, visual e pacote de 28/10](AUDIO_VISUAL_2026-10-28.md).
Ele contém os resultados do EXE exportado e os caminhos da prévia; substitui o
estado provisório deste checkpoint inicial de natação.
