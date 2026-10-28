# UE5.8 — cenário completo e atendimento nativo, 27/10/2026

Branch: codex/ue58-migration. Projeto ativo: D:/Projetos/MareAltaUE58/unreal/MareAlta/MareAlta.uproject.
Este guia substitui o bloqueio e as contagens do CHECKPOINT_2026-10-27.md. A migração do jogo inteiro permanece incompleta; não há release UE jogável aprovada.

## Cenário e colisões

Todos os 1.620 modelos canônicos do cenário foram importados. Coast agora tem 1.689 grupos e 12.910 instâncias, sem modelos ausentes. A validação confere recursos, materiais efetivos, BodySetup e ausência de hulls automáticos.

A navegação em Z910 cm vinha dos hulls convexos gerados pelo Interchange, que o Recast exporta mesmo quando a física usa ComplexAsSimple. Remover esses hulls e atualizar a colisão resolveu a superfície falsa. A projeção de referência agora fica em Z10 cm; os percursos externos e internos ao balcão retornam caminhos completos.

O importador não gera novos hulls; atualiza a colisão triangular e recolhe recursos temporários entre lotes. remove_collisions_with_notification(mesh,False) chama RefreshCollisionChange/CreateNavCollision(true) sem pedir uma reconstrução completa desnecessária do mesh. Salvar explicitamente o asset depois. MARE_MCP_TIMEOUT permite prazo maior para modelos detalhados; um timeout HTTP não cancela uma importação que já começou. Conferir o catálogo/log e aguardar o término antes de retomar.

Nanite foi desativado somente nos 42 modelos com materiais translúcidos/aditivos incompatíveis. Máscaras/objetos opacos mantêm Nanite. Isso preserva transparências, sem declarar otimização medida.

## Atendimento e HUD

MoveTo não soma mais o raio da cápsula ao limite de chegada. Destinos são projetados na malha de navegação; não usar a distância de um destino bruto diferente do término do caminho. Clientes chegam, viram para o atendimento, recebem produtos com pagamento automático e só então seguem à mesa.

Ao sentar, o movimento é desativado; ao levantar, o cliente usa o ponto de acesso projetado antes de reativar a cápsula. Clientes sem mesa usam pose em pé ao consumir. Fechar o quiosque dispensa quem ainda não fez pedido; pedidos já anotados continuam sendo entregues.

Pedidos, campanha principal e até duas secundárias aparecem à esquerda. O texto se ajusta à largura livre ao lado do celular e tem sombra para leitura. Esc fecha o celular. Pausa fora do celular, foto, corrida e demais configurações ainda exigem port/validação.

## Reprodução e segurança

Testes usam exclusivamente -MareSaveRoot=D:/CodexTemp/ue58-navigation-20261027. O helper gameplay_probe recusa mutações sem um perfil de QA no D:/CodexTemp. Os saves Godot/instalação aprovada foram preservados.

Interchange/MCP funcionam pelo servidor nativo local. Não chamar as funções Python estáticas de NavigationSystemV1 durante PIE: o rastreador de script da UE5.8 acessa GetWorld do CDO e emite ensure. Consultar os caminhos com PIE parado e validar no jogo pelo movimento físico. O helper foi protegido contra essa consulta durante PIE.

O empacotamento inclui os diretórios dos atores carregados pelo catálogo JSON e o mapa Coast; os dados Data já são copiados como NonUFS. O editor abre Coast; o mapa inicial do jogo continua Entry enquanto a migração não for aprovada. A configuração de cook ainda precisa ser validada num pacote real.

## Pendências que continuam

- Persistência nativa foi concluída no lote posterior: [Saves e atendimento](PERSISTENCIA_2026-10-27.md). Conferir esse guia antes de retomar.
- Refinar mãos/bandejas/apoio dos braços, pessoas e materiais; revisar iluminação e desempenho na câmera final. A importação completa não equivale à aprovação visual.
- Completar negócios, capítulos, progressão, salários, atividades, clima, dia/noite, navios, baleias, animais, áudio e opções.
- Validar porta, todas as entradas/áreas, saves copiados e executável empacotado antes de publicar download.
- Imports rejeitados antigos continuam locais, fora do commit; não repetir a limpeza que encerrou o editor no lote anterior.

A última versão jogável aprovada continua sendo a Godot 8d3be2d. Não a substituir por este projeto de migração.

## Evidências deste lote

- Build C++ do cenário/atendimento: Succeeded. Teste MareAlta.Migration.NativeEconomy: Success, 0.0771222 s, sem erros ou avisos.
- Validação: 1620 modelos, zero erros. Mapa: 1689 grupos / 12910 instâncias / zero ausentes.
- Atendimento em PIE por 111,8 segundos: exatamente um funcionário, cliente recebeu coco e pagou R$12 antes de sentar; posição sentada estável; saída caminhando por mais de 5m; louça apareceu e foi recolhida pelo funcionário; ao fechar, não restaram clientes aguardando. Trace e resumo em docs/qa/ue58/service-complete-*.json.
- Interação da geladeira por E abriu o painel. Porta da casa abriu e fechou automaticamente após saída com arco livre; evidência door-open-auto-close.json.
- Revisão visual encontrou texto pequeno por escala DPI duplicada e contraste ruim nos botões. Corrigidos escala física, contraste, proporção vertical e abas em duas colunas no viewport curto; confirmação visual final registrada nas imagens de QA.
- Permanecem avisos de geometria de navegação detalhada (232040 triângulos em um componente). Isso exige perfil e colisões simplificadas corretas por peça; não restaurar o hull gigante para silenciar o aviso. Não foi feita uma medição de desempenho comparável neste lote.

As imagens de QA são capturas reais do editor/PIE, para verificação, sem aprovação artística final. Não foi exportado nem aprovado um executável UE neste lote.

A revisão final do celular foi feita no viewport real de 760x395: seis abas legíveis em duas colunas, cabeçalho sem quebra incorreta, ações ajustadas ao texto e painel da geladeira com rolagem. Imagens phone-small-viewport.png e fridge-small-viewport.png em docs/qa/ue58. CaptureEditorImage inclui o Slate; HighResShot serve para a cena/HUD e não comprova o conteúdo do celular.
