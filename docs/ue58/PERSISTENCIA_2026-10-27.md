# UE5.8 — continuidade do atendimento e saves

Projeto: D:/Projetos/MareAltaUE58, branch codex/ue58-migration. Continuação do cenário/atendimento de c044dead. A migração integral permanece em andamento; a entrega Godot 8d3be2d e seus saves foram preservados.

## Comportamento implementado

O save UE agora inclui clientes físicos, pedidos parciais, produtos já entregues, reservas de lugares, consumo, louça, posição do jogador, visão e portas. O atendente contratado reaparece uma única vez e retoma o produto transportado sem nova contratação nem nova retirada de estoque.

O snapshot entra no mesmo JSON e na mesma substituição atômica que saldo, estoque e pagamento. Ele é atualizado nas transações, no autosave de 30 segundos e antes do encerramento do mundo, enquanto os atores ainda existem. Os dados físicos ficam em ue_kiosk, versão 1; ue_orders e ue_dirty_tables continuam sendo usados. Campos desconhecidos do estado, snapshot, cliente, jogador e atendente são preservados.

Ao criar um pedido, o snapshot vincula o cliente ao identificador já gravado mesmo que o método chamador ainda não tenha recebido esse identificador. Ao entregar, calcula os produtos pagos a partir do pedido restante, evitando restaurar o estado anterior ao último produto. A criação e a última entrega foram exercitadas com leitura do arquivo logo após a transação.

Pedidos UE antigos sem cliente correspondente recebem novamente um cliente físico. Se o formato antigo contém somente remaining, recuperam-se os produtos ainda não entregues, sem inventar histórico nem cobrar os itens anteriores. Quem já tem pedido pode retornar ao balcão mesmo com o quiosque fechado; novas chegadas continuam exigindo abertura.

O consumo tem marcador próprio: recolher a louça enquanto o cliente ainda descansa não recria os objetos a cada frame. A cadeira fica reservada até a pessoa sair. A disposição dos objetos usados ocupa duas colunas e avança para dentro da mesa, evitando a fileira que deixava pratos para fora. Dormir grava o próximo dia sem os clientes/pedidos do dia anterior e mantém as regras existentes de estoque e fechamento.

## Reprodução dos testes

Iniciar o editor com o MCP local e o parâmetro obrigatório:

    -MareSaveRoot=D:/CodexTemp/ue58-persistence-20261027

Com o editor pronto e PIE parado, executar na raiz do projeto:

    D:/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe tools/ue58/test_persistence.py --seed

O script confere o perfil exato antes de gerar a fixture. --seed substitui somente a fixture descartável dessa pasta de QA. Ele abre/fecha PIE, faz retiradas e entregas pelas interações reais e registra o relatório no D:/CodexTemp. Nunca apontar testes para a instalação ou progresso real.

A ferramenta gameplay_probe tem consultas de clientes, identificadores persistentes, produtos nas mãos, objetos usados e reservas. Mutações de QA são recusadas fora de um perfil explícito em D:/CodexTemp. A SubsystemBlueprintLibrary não está exposta no Python desta instalação; localizar o subsistema real por ObjectIterator e conferir o outer do mundo.

## Pendências gerais

Continuam pendentes os demais negócios/atividades, salários, capítulos completos, clima/dia/noite, navios/baleias/animais, áudio, opções e acabamento visual. A importação completa do progresso Godot também exige conferir o mapeamento dos sistemas que ainda não foram portados. Este lote valida saves nativos UE e preserva os arquivos originais; não declara todos os sistemas migrados.

O aviso de geometria detalhada da navegação permanece e pede perfil/colisões apropriadas por peça. Não restaurar o hull gigante. Não há executável UE novo aprovado neste lote; empacotamento e teste do pacote continuam obrigatórios antes de uma publicação jogável.

## Resultado verificado

- Compilação C++: Succeeded (16,98 s, log D:/CodexTemp/ue58-persistence-build.log).
- Integração real por MCP/PIE: 45 verificações aprovadas, com múltiplos encerramentos e recargas. Inclui pedido parcial, última entrega, pagamento único, estoque/carry, louça, reserva de cadeira ocupada, consumo, sono, recuperação do formato antigo, funcionário, porta aberta e posição do jogador.
- Regressão MareAlta.Migration.NativeEconomy: Success, sem erros/avisos, 0,0529508 s.
- Relatórios: docs/qa/ue58/persistence-roundtrip.json e native-economy-persistence.json. Conferência visual da louça reconstruída em restored-used-dishes.png; os objetos ficaram sobre a mesa, sem a fileira lateral anterior. A imagem não representa aprovação artística final.
- Log final do editor sem erro de script/JSON, ensure ou fatal durante essa bateria; permanece o aviso já documentado sobre geometria detalhada de navegação. Perfil usado apenas no D:/CodexTemp. Nenhum executável foi publicado neste lote.
