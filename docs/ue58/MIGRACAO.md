# Migração para Unreal Engine 5.8

Pedido vigente de 27/10/2026: converter o jogo para UE 5.8 e manter o trabalho no GitHub.
Direção artística: **realista estilizado**, com proporções naturais, materiais PBR,
texturas, luz natural e sombras de contato. Evitar contornos toon, cores chapadas e
caricaturas. Trocar o motor sozinho não constitui aprovação visual.

Branch: `codex/ue58-migration`. Base Godot preservada: `8d3be2d`, branch
`codex/resort-1.1-mcp`. Não substituir a entrega Godot por um protótipo Unreal.
Projeto nativo: `unreal/MareAlta/MareAlta.uproject`. Trabalho local no drive D.

## Conexão MCP verificada

UE instalada: `D:/UE_5.8`, versão **5.8.3-58210709**. Usa os plugins nativos
ModelContextProtocol, EditorToolset e AutomationTestToolset, somente no editor.
O servidor escuta em `127.0.0.1:8000/mcp`. O cliente configurado no Codex é
`unreal_topgpt`; ferramentas diretas foram descobertas nesta sessão.

Abra com `unreal/MareAlta/Abrir-Editor-MCP.ps1`. O diretório Content/Python registra
`mare_mcp.MareMigrationTools`: status, importação em lotes, validação, montagem de
mapa e recarga das ferramentas do projeto. Não exige plugin de terceiros.
`tools/ue58/mcp_client.py` é alternativa de diagnóstico via MCP HTTP.

## Estado concreto — conversão em andamento

- Módulo C++ compilado com a UE 5.8.3 instalada e MSVC14.44.
- Economia nativa: empresa, abertura, estoque, retirada/devolução, reposição atômica,
  entrega com pagamento, atendente único, expansões e recompensas da campanha.
- `MareAlta.Migration.NativeEconomy` executado por MCP: **Success**, sem erros ou
  avisos. Testa consumo/devolução, ausência de duplicação, reposição sem cobrança
  parcial, pagamento por produto, fechamento ao dormir e recompensa idempotente.
- Celular Slate e personagem nativo compilados. Interações físicas ainda pendentes:
  não declarar esses recursos jogáveis só porque o módulo compila.
- Exportados 12.910 posicionamentos do cenário, 2.985 variantes de modelo, reduzidas
  a 1.620 modelos canônicos. Fontes glTF portáveis e imagens compartilhadas geradas.
- Calibração real de importação: Godot(1,2,3)m → UE(100,300,200)cm.
- Primeiros 18 modelos nativos importados/validados por MCP. Importação restante,
  mapa, render e aprovação visual continuam pendentes.
- O acesso a EpicGames/UnrealEngine retornou404 nesta conta; a engine instalada
  permite compilar. Não redistribuir o código/binários da engine neste repositório.

## Próximas etapas obrigatórias

1. Completar importação pelo MCP e inspecionar materiais PBR, orientação, colisões
   e escala no mapa. Não aceitar cenário incompleto ou cores planas como final.
2. Concluir personagem, estações, fila, reserva de mesas, mãos/rig/animações,
   atendente físico, louça, navegação e porta da casa.
3. Completar todos os sistemas existentes: capítulos, negócios, progressão, horas,
   diária/pousada, clima, oceano/navios/baleias, animais, áudio e configurações.
4. Terminar celular compacto, HUD à esquerda e todas as interações. A aba operacional
   não deve permitir retirar produtos remotamente; isso pertence às estações.
5. Testar importação de save como cópia, preservar campos desconhecidos e validar
   migração de funcionário/cobrança. Nunca escrever na instalação/dados Godot.
6. Testar visual e função na UE, depois empacotar e testar executável com dados
   separados. Só então publicar uma nova versão jogável no GitHub e no drive D.

As preferências de AGENTS.md continuam vigentes exceto o novo motor/direção
artística. Esta documentação é um checkpoint de migração; não é uma entrega final.

## Fontes e licenças

Modelos/texturas vêm do projeto base e conservam as atribuições em CREDITS.md e nos
catálogos existentes. O exportador transforma materiais toon em PBR sem remover UVs.
`export_godot.gd` exporta dados da versão aprovada em perfil isolado;
`deduplicate_models.py` identifica duplicatas sem apagar fontes;
`prepare_assets.py` gera glTF e texturas por hash, sem executar o Godot no jogo UE.
Fontes e assets Unreal usam Git LFS. Caches, builds e export bruto não entram no Git.

## Nota técnica de integração MCP

A chamada direta `mcp__unreal_topgpt` foi validada no chat: status identifica o
projeto no D, teste nativo retornaSuccess e CaptureViewport devolve imagem real.
Foi salvo `/Game/Maps/Coast` com 19grupos/36instâncias importadas; faltam1602modelos.
A primeira captura confirma posicionamento básico, mas está com exterior claro
excessivo e preenchimento insuficiente. **Reprovada como resultado visual final**;
completar cenário e corrigir luz antes de apresentar como jogo migrado.
