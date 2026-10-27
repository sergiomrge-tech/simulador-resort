# Checkpoint UE5.8 — 27/10/2026

Branch `codex/ue58-migration`, checkout `D:/Projetos/MareAltaUE58`.
Direção: realista estilizado, sem cartoon. Migração incompleta; nenhuma nova release jogável UE publicada.
A entrega Godot 8d3be2d e os saves permanecem preservados.

## Salvo neste lote

- 730/1620 modelos canônicos importados e validados, sem recursos ausentes nessa validação.
- Coast: 784 grupos, 4472 instâncias; 890 modelos ainda faltam. Aprovação visual: false.
- Materiais PBR de areia/areia úmida/gramado e oceano SingleLayerWater com normais animadas; luz/exposição revisadas, ainda sem aprovação visual final.
- 4 pessoas com corpo/roupa/cabelo e 10 clipes por variante; 13 produtos prontos e 13 representações de louça usada. Catálogo em Content/Data/actors.json, fontes em SourceArt/Actors.
- C++ nativo: estações físicas, celular, alvos de interação, porta, clientes, atendente único e louça. Compilação concluída com sucesso.
- Economia com transporte separado do jogador e funcionário. AutomationTest MareAlta.Migration.NativeEconomy: Success, sem erros/avisos, duração 0.0450033 s.
- PIE: jogador estável Z100.4 cm, velocidade zero; interação E na geladeira abriu painel físico. Isso não valida o ciclo completo de clientes.
- Dados de teste isolados em D:/CodexTemp/ue58-native-gameplay-20261027. Sem teste no perfil real.

## Primeiro bloqueio a corrigir

A navegação projeta (3870,-1635,98) em (3870,-1635,910) cm. Clientes ficam sem caminhar corretamente.
A física do jogador está estável no chão. Suspeita: UNavCollision antiga da geometria importada persiste após BodySetup mudar para ComplexAsSimple. Investigar/invalidate/recreate nav collision e reconstruir Recast. Não mascarar com teleporte ou extensão maior de projeção.
Bounds presentes: centro (4200,300,250), extensão (3000,4500,1000).
APIs disponíveis: UStaticMesh::RecreateNavCollision/CreateNavCollision/SetNavCollision, UNavCollision::InvalidateCollision/Setup/GatherCollision.

## Outras pendências

1. Completar 890 modelos e revisar imagens reais, materiais, iluminação, escala e colisões.
2. Validar ciclo físico completo: abrir, fila, anotar, retirar, entregar/pagar antes de sentar, consumo e louça; atendente único e porta.
3. Refinar mãos, bandeja/apoio dos braços e cabelo/roupa animados. Grip atual é provisório.
4. Persistir/recriar clientes, pedidos ativos e louça ao recarregar; não deixar pedidos órfãos.
5. Portar integralmente campanhas, demais negócios/progressão, clima/dia/noite, navios/baleias/animais, áudio, opções e pausa. HUD de missões ainda pendente.
6. Testar saves copiados e executável empacotado em dados separados. Não substituir o jogo aprovado por esse protótipo.

## Encerramento e recuperação

PIE foi parado e os assets foram salvos antes do encerramento. A tentativa de limpar imports rejeitados pelo Editor encontrou inconsistências de referências e o processo do Editor deixou de existir. Não repetir limpeza automática: investigar o log D:/CodexTemp/ue58-native-gameplay-editor.log primeiro. As pastas rejeitadas dish_fries, dish_fish_portion e player_home_door fora de Combined permanecem locais e não devem ser versionadas; o catálogo usa Combined. Não apagar arquivos que tenham referências válidas.

Reabrir via unreal/MareAlta/Abrir-Editor-MCP.ps1; MCP local 127.0.0.1:8000/mcp. Configurar caches/TEMP e dados de teste no D. GameDefaultMap permanece Entry enquanto o port estiver incompleto.

## Fontes e licenças

Pessoas: Quaternius Universal Base Characters CC0, roupas/fontes do projeto original com créditos preservados. Pratos e louça são exportados dos construtores de dish_presentation.gd. Terreno: texturas CC0 Poly Haven já atribuídas em CREDITS.md. Oceano: grade autoral e normal de água da engine instalada; não redistribuir fontes/binários da engine.
