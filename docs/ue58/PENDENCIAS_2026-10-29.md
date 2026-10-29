# Continuação integral autorizada — 29/10/2026

O usuário pediu conferir o checkpoint e **concluir todas as pendências**.
Não encerrar a migração apenas por terminar o gramado. Trabalhar na branch
`codex/ue58-migration`, projeto `D:/Projetos/MareAltaUE58`, Unreal 5.8.3.

## Checkpoint gráfico verificado

Fonte `b7eb5390`, pacote interno
`D:/Builds/MareAltaUE58_GramadoEstavel_2026-10-29/Windows`.
Gramado com 177.454 instâncias HISM, base verde contínua, dois grafos PCG novos,
sem colisão e culling de 18–30 m. Mantém praia/pisos. Hotel opaco Nanite e vidro
separado, materiais diretos/instâncias corrigidos; avisos de uso agora reprovam QA.
Lumen GI/reflexos ativos, AsyncCompute=0 como mitigação de GPU fault observado
na inicialização do hotel desbloqueado. Duas execuções do hotel com a mitigação
passaram; isso não prova a causa exata no driver/engine.

Pacote: 63/63 verificações e áudio audível/mute/pausa aprovados;
abertura natural e avanço 6/6 cada. Evidências:

- `D:/CodexTemp/ue58-package-qa-20261029-074214`.
- Hotel: `D:/CodexTemp/ue58-render-profile-20261029-073953`.
- Bosque: `D:/CodexTemp/ue58-render-profile-20261029-074506`.
- Intro: `D:/CodexTemp/ue58-intro-package-20261029-074701`.

1080p nativo, RTX4060Ti8GB: bosque 71,9 FPS médios / P95 17,589 ms;
hotel 86,3 FPS / P95 14,929 ms. Câmeras fixas, não garantia do mapa inteiro.
O hotel original foi mais rápido que seu proxy Nanite nessa medição (94,2 FPS),
portanto não alegar ganho de velocidade por habilitar Nanite no hotel.
O valor anterior de 84,5 FPS do bosque usava outra configuração de async;
não é o resultado final da configuração de estabilidade.

Pasta/ZIP de checkpoint montados: `D:/Downloads/MareAltaResort_UE58_Gramado_2026-10-29`.
Isso não é a entrega da conversão concluída; não foi publicada uma nova release.

## Trabalho restante — ordem de execução

1. Corpo/mãos do jogador com pegar, carregar, portas e natação. Reutilizar rigs
   e clips originais: `actors.json` contém inclusive Human_0Swim_Idle.
2. Abertura acabada: ônibus detalhado, porta/interior, desembarque coerente,
   caminhada real até casa, carta visível na mesa e ligação com campanha.
   A sequência atual funciona, mas ônibus e descida ainda são provisórios.
3. Vida na vila/praia: pedestres, residentes, vôlei e animais vivos/animados;
   não contar a presença dos clientes do quiosque como esse sistema inteiro.
4. Casa: sofá, TV, som, banheiro e demais interações; geometria/porta/sono já
   existem, mas nem todas as funcionalidades foram portadas.
5. Outros negócios: simulação real de pousada/hotel, restaurante/bar/passeios,
   hóspedes, funcionários e respectivos ciclos. Comprar uma expansão e mostrar
   o prédio não equivale a migrar sua operação.
6. Campanha/secundárias: auditar contadores, capítulos e conexão à progressão real.
7. Varredura global: objetos, animações, mãos/consumo/louça, colisões, navegação,
   interiores de restaurante/recepção/quartos, dia/noite e longa duração.
8. Arte realista estilizada: substituir/refinar elementos ainda cartoon, sobretudo
   fauna/corais, vegetação, horizonte subaquático; finalizar ondas/espuma/splash e
   iluminação noturna (folhagem ainda muito clara/saturada em algumas capturas).
9. Apresentar três propostas distintas de HUD/interface **após** o lote anterior.
   Não escolher silenciosamente uma proposta antes da apresentação.
10. Regressão final completa, desempenho em diferentes setores/carga de NPCs,
    documentação/catálogo, commit/push e pacote final identificado corretamente.

Não apagar instalações, fontes ou as três pastas Actors não rastreadas anteriores.
O usuário dispensou copiar o save para o próximo pacote; QA usa dados separados.
Rádio, placa física, gestão portátil, sem preparo, pagamento automático, atendente
único, pedidos no balcão antes de sentar continuam obrigatórios.

## PAUSA explícita solicitada pelo usuário — 29/10

Interromper trabalho até o usuário mandar retomar. Nenhum editor/jogo/build ativo
ao pausar. Não confundir o checkpoint testado b7eb5390 com o WIP posterior.

### WIP salvo, ainda não aprovado no executável

- `MarePlayerPresentation`: corpo com rig/roupas originais, malha de primeira
  pessoa e corpo completo para sombra; transporte em hand_r com IK e gesto de
  alcance. Câmera saiu do interior da cabeça (12 cm à frente, Z74); reocultar
  pescoço/cabeça após trocar clip evita barba/cabeça na visão para baixo.
- No editor houve checagens lógicas e fotos do corpo/produto corretos em
  `D:/CodexTemp/ue58-player-20261029-b/`. Essas execuções têm erros de plugins
  Python/Automation na inicialização do editor; não provar ausência de erros do EXE.
- Natação ainda em ajuste: a orientação inicial deixava a cabeça atrás da câmera.
  Última alteração usa posição (-10,0,62), rotação (0,90,-85), mais IK cíclica nos
  braços. **Essa última orientação não foi validada visualmente nem exportada.**
- `MareHomeWorld`: código novo de TV com conteúdo costeiro animado, som espacial,
  sofá, chuveiro com gotas e pia. Persistência TV/som em ue_home; preserva decor.
  Ainda não foi executado, nem validado em circulação/posição/áudio.
- Assets materiais TV/chuveiro e `home_assets.json` gerados e salvos fora do PIE
  por MCP (`build_home_appliances`). Referenciam o vidro original World_1164.
- Último build do editor **falhou** em `MareHomeWorld.cpp:39`: trocar a chamada
  inexistente `Actor->GetComponentsByClass(...)` pelo padrão C++ `GetComponents`
  com TArray<UInstancedStaticMeshComponent*>. Ler também o log completo antes de
  corrigir outros erros: `C:/Users/sergi/AppData/Local/UnrealBuildTool/Log.txt`.
- Scripts de QA passaram a exigir `player_body_visible` como último check e
  capturam player-body/player-carry; ampliar depois para as interações da casa,
  conferir todos os frames e só então exportar um pacote novo. Não testar o WIP
  no pacote antigo nem substituir a prévia testada com código que não compila.
- Ferramentas novas MCP: `inspect_player_body`, `player_body_pose` (somente perfil
  QA D:/CodexTemp) e `build_home_appliances`. Não assumir as APIs Python pelo nome
  C++: get_world_transform/get_world_location/get_all_socket_names funcionaram.

Usuário autorizou aceitar permissões necessárias que a Unreal apresentar para
o trabalho do projeto. Não é pedido para alterar segurança/driver/TDR do sistema.
