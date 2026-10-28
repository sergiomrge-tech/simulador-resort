# Varredura UE — em andamento

O usuário pediu uma varredura de todo o jogo, priorizando quiosque, clientes,
objetos flutuantes e animações. Não declarar a migração concluída com base neste
lote. Projeto `D:/Projetos/MareAltaUE58`, branch `codex/ue58-migration`; último
commit publicado antes deste trabalho `5eb6e649`.

## Alterações locais

- Folhas das quatro variantes originais de coqueiro recuperaram o recorte alfa,
  iluminação dos dois lados e movimento leve; geometria e textura preservadas.
  Revisadas em imagem no editor. Ajustes de cor do gramado, mar e iluminação.
- Corrigida a posição da luz do banheiro, que estava na casa vizinha.
- O atendimento usa os clipes originais e IK nos braços. Os produtos acompanham
  as mãos com ponto de apoio e orientação estável; bebidas fazem gesto de consumo.
  Transição entre clipes e fixação de escala estão em código, aguardando validação
  na compilação final. Não remover as duas peças de cabelo da variante longa:
  são complementares e, separadas, deixavam uma falha no topo da cabeça.
- Auditoria encontrou materiais sem suporte persistido para Nanite, que podiam
  aparecer cinza. Corrigidas 74 raízes e reutilizados 718 slots de materiais com
  parâmetros idênticos, sem apagar os assets. Evidência e relatório detalhado em
  `D:/CodexTemp/ue58-world-audit-20261028/material-repair.json`.
- Em PIE, perfil isolado, o atendente gerou vendas e entrega automática; capturas
  com pessoas e produtos em `D:/CodexTemp/ue58-world-audit-20261028/`.
  Verificar atendimento manual, produtos, pose sentada, ciclo completo e save.

## Pendências e cuidados

- Pedido posterior: após terminar os pedidos anteriores, apresentar **três
  propostas de HUD e interface totalmente diferentes**. O usuário pediu para
  receber as opções depois das correções e da abertura; não escolher nem
  implementar uma das três antes de apresentar as alternativas.
- Pedido de abertura: jogador chega à vila de ônibus, desce, entra na casa e
  encontra uma carta emocionante do avô entregando o quiosque e convidando-o a
  expandir o negócio da família. Proteger saves anteriores e ligar a introdução
  à campanha. O ônibus CC0 de ajanhallinta foi localizado e baixado para
  `D:/CodexTemp/ue58-intro-assets/bus.zip`; é sem interior e requer adaptação
  visual/porta. Fonte: https://opengameart.org/content/3d-bus .

- Processo de build/QA iniciado para `D:/Builds/MareAltaUE58_Varredura_2026-10-28`;
  consultar log `D:/CodexTemp/ue58-sweep-build.log` e o processo antes de repetir.
  O QA do EXE foi ampliado para verificar quatro personagens e produtos nas mãos.
  Só entregar após aprovação, áudio, inspeção visual e ausência de erros reais.
- Mar: peixes do recife exportados como modelos estáticos atravessam a superfície;
  corrigir posição e animação com base em `scripts/reef.gd`. Cruzeiro, veleiro,
  baleias e vida ambiente nativos seguem pendentes. Não ocultar a falha apenas
  no relatório.
- Verificar casa e banheiro na posição correta, cais, rua, colisões, NPCs, estação,
  funcionários, missões, compras, chuva e performance. Vários negócios e capítulos
  ainda não foram convertidos. Não classificar recurso ausente como aprovado.
- Repetir regressão de persistência após as mudanças físicas; preservar progresso
  do usuário. Os três diretórios não rastreados `Content/Actors/dish_fish_portion`,
  `dish_fries` e `player_home_door` eram anteriores e não devem ser removidos.
- Após validação: atualizar instruções, commit e push do lote, pacote com nome novo
  no D, ZIP sem dados pessoais, e publicação identificada como prévia. A versão
  anterior e seus saves permanecem intactos.

## Checkpoint posterior — rádio, placa e roteiro

- Implementados e enviados em `e5c3b130`: rádio instrumental com seleção e
  volume persistidos; placa física vermelha/verde abre e fecha o quiosque. O
  controle de abertura saiu do celular. Build `D:/Builds/MareAltaUE58_RadioPlaca_2026-10-28/Windows`;
  regressão isolada do pacote teve 48 verificações aprovadas, incluindo clique
  na placa e seleção de rádio. Esse build ainda não contém a abertura e não deve
  ser anunciado como entrega final dos pedidos posteriores.
- Roteiro da chegada e texto da carta em `ABERTURA_UMA_NOVA_MARE.md`. Asset CC0
  do ônibus importado para `/Game/Intro/Bus/`; fontes editáveis em
  `unreal/MareAlta/SourceArt/Intro/`. O veículo é uma malha combinada sem interior:
  não há ainda animação de porta, ônibus no mundo, sequência, carta interativa,
  estado persistido ou validação visual. Fazer essas etapas antes de afirmar que
  a abertura está pronta. O manifesto `intro_bus.json` registra os limites reais
  (origem deslocada); corrigir o pivô ao posicionar.
- Depois que o lote anterior estiver realmente concluído, propor três interfaces
  de HUD distintas. O usuário não autorizou escolher uma antecipadamente.

## Protótipo de abertura — código em teste (28/10)

Há uma implementação inicial em `MareIntro`: para perfil novo, ônibus cruza a
vila, câmera passa para uma breve descida em primeira pessoa, e a carta pode ser
lida na mesa da casa. E/Esc avança a chegada; a carta pode ser relida e o estado
é salvo. O ônibus é uma malha sem interior ou porta funcional, e a movimentação
de descida é uma aproximação: não chamar de cena acabada. O usuário informou que
não precisa preservar o save, portanto a próxima entrega pode começar um perfil
novo sem copiar o progresso; não apagar seus arquivos existentes desnecessariamente.

No teste do editor com perfil descartável `D:/CodexTemp/ue58-intro-qa-d`, seis
checagens passaram: chegada natural, interação na carta, abertura, conclusão e
releitura. A captura de saída coloca o jogador diante da casa. O editor em modo
jogo apresentou erros de inicialização dos plugins Python experimentais da engine;
essa execução não prova ausência de erros no executável empacotado. A chegada
com pulo foi testada na versão anterior do protótipo, mas deve ser repetida após
as alterações. Falta validar partida, abertura e roteiro no executável exportado,
colisão/caminho até a casa, visual da carta na mesa, perfil existente e reinício.
A sequência não substitui os demais recursos pendentes da varredura.

### Teste empacotado do protótipo

O build interno `D:/Builds/MareAltaUE58_IntroWIP_2026-10-28/Windows` foi
compilado a partir de `b9bcee78`. Teste `tools/ue58/test_intro_package.ps1`
rodou com dois perfis descartáveis: chegada natural e avanço, seis verificações
em cada, saída 0 e sem erros no log. Capturas em
`D:/CodexTemp/ue58-intro-package-20261028-125625/` mostram o ônibus na rua,
a vista da casa e a carta. São testes parciais: ainda não comprovam o percurso a
pé nem visualização clara do objeto sobre a mesa. O modelo do ônibus é simples,
sem interior/porta; melhorar antes de declarar o roteiro acabado. Não disponibilizar
este build como entrega final, pois o usuário prefere testar após as correções e
adições pendentes. Os três conceitos de interface vêm depois desse lote.

### Pedidos adicionais: batente e ondas

- Porta principal: a folha tinha topo a 232 cm e o batente começava em 247 cm,
  deixando vão de 15 cm. Ajustada a escala vertical da folha em runtime; o lado
  da porta principal também foi aproximado do batente, com o pivô preservado.
  A escala faz parte do gerador do mapa. Captura anterior ao último ajuste lateral
  `D:/CodexTemp/ue58-door-waves/door.png` confirma o vão superior resolvido;
  repetir verificação da lateral e ciclo de abertura/fechamento no pacote.
- Material do oceano: ondulação animada mais forte perto da orla e espuma
  fragmentada com movimento para a praia, restrita à faixa costeira. Captura
  preliminar `D:/CodexTemp/ue58-door-waves/sea-b.png`; ainda verificar a espuma
  em tempo real, também sob chuva, e no pacote. Os peixes estáticos fora d'água
  continuam um defeito separado. Inspeção aponta 97 pares Body/Tail nos modelos
  0544/0545, 0546/0547, 0555/0556 e 0564/0565, escalados até cerca de 3x e
  profundos apenas 29–97 cm. `mare_fish_audit.py` registra as dimensões antes de
  implementar natação e profundidade adequadas; ainda não corrige os peixes.
- Regressão do executável com abertura, anterior a estes dois ajustes: 48 checks
  passaram (`D:/CodexTemp/ue58-package-qa-20261028-125730`), áudio audível,
  silenciado e pausado aprovados. Repetir após a porta e água.
