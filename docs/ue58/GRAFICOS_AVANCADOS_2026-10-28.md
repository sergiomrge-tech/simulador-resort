# Nanite, Lumen e PCG — implementação de 28/10

Checkpoint anterior: `1effce34`. Unreal 5.8.3, Windows x64, DX12, SM6,
RTX 4060 Ti 8 GB (8188 MiB pelo nvidia-smi), driver 617.42. Meta: 60 FPS.
As configurações anteriores estão em `graphics-reference/`.

## Nanite

A auditoria encontrou 1.623 Static Meshes, 12.914 instâncias e Nanite já ativado
em 1.579 modelos. Alta densidade opaca já utilizava o recurso. Oceano, materiais
transparentes e deformações foram excluídos da ativação adicional. Tentativa em
World_1391 (poste, 30.610 triângulos) e World_2348 (37.577) foi REJEITADA após
reabrir o mapa: Material Instances sobrescreviam o blend para translucência.
Nanite voltou a ficar desativado nesses dois. A auditoria passou a considerar
essas sobrescritas; não usar a lista `nanite-enabled.json` como prova de aprovação.

Há 1.289 modelos com menos de 1.000 triângulos que já tinham Nanite. Foram
identificados para revisão artística/de custo; não se tornou sua geometria mais
rica ao ativar o recurso. Nenhum modelo foi substituído por primitivas.

## Lumen

GI=1 e Reflections=1 confirmados em execução, distance fields ativos, VSM ativos,
sem hardware ray tracing. Mantido software Lumen para o alvo de 8 GB. No volume de
pós-processamento do piloto e Coast: Scene Lighting Quality=1, Final Gather=1,
Reflection Quality=0,75, exposição mínima EV100=5 e máxima=14. A qualidade média
existente do menu continua sendo alternativa de menor custo. A revisão específica
de cada restaurante, quarto, recepção e piscina, inclusive à noite, segue pendente.
Não inferir acabamento final de interiores por haver Lumen ligado no projeto.

## PCG

Plugin nativo PCG habilitado. Sete grafos por região: Palms, TropicalTrees, Shrubs,
GroundPlants, Rocks, OrnamentalGarden e NaturalDetails em `/Game/Graphics/PCG`.
Os grafos usam Create Points → Static Mesh Spawner → Output. A distribuição é
pré-calculada no editor pelo script `mare_graphics.py`, com semente determinística,
espaçamento, escala original do modelo, rotação variada e exclusões de blocos de
construções/rotas/acesso do quiosque. Apenas terreno plano foi admitido nesta etapa;
não existe ainda adaptação genérica a encostas. Generation On Demand; não gerar
vegetação continuamente durante a partida.

Primeiro testado em `/Game/Maps/GraphicsPilot`, cópia real de Coast. Depois integrado
em Coast: faixa verde oeste X15–27m, Y-7–4m e faixa leste X55–67m, Y-7–4m, 30
instâncias em cada região (60 totais). A vegetação anterior permanece. Os novos
componentes são NoCollision; a navegação ainda exige caminhada completa/QA exportado.
O primeiro ensaio tinha plantas superdimensionadas e limites PCG inválidos; corrigidos
usando escala original, menor densidade e BoxComponent de limites explícitos.

## Medição real e limites

CSV Profiler nativo com eventos GPU, capturas reais em `graphics-reference/images`.
Raw CSVs: `D:/CodexTemp/ue58-graphics/UE/Saved/Profiling/CSV/`.
`comparison.json` contém cada sessão e eventos GPU de Nanite, Lumen e sombras.

A primeira comparação do quiosque usou viewport do editor 760×395; não representa
720p nem comprova 60 FPS. Comparação final do primeiro bosque: viewport real
1280×688, ScreenPercentage=80, qualidade GI/reflexos/sombras=2, sem VSync/limite.
Sem PCG: 12,095 ms/frame (P95 16,085), GPU 7,435 ms. Com 30 instâncias: 11,849
ms/frame (P95 15,804), GPU 7,500 ms. VRAM local em torno de 4.236 MiB inclui o editor.
As diferenças de CPU estão sujeitas a ruído; não se afirma ganho de FPS pelo PCG.
Falta a medição isolada do pacote em 1280×720 e regressão depois destas alterações.

No piloto, foram exercitados alvo da geladeira/abertura do painel, porta da casa,
celular e save em perfil descartável. Resultados em `interaction-probes.json`.
Não houve alteração dos sistemas de economia/gameplay para esta etapa gráfica.

## Continuação obrigatória

1. Executar benchmark exportado `-MareGraphicsQA -csvGpuStats` (perfil D:/CodexTemp),
   que mede a mesma câmera com tudo ligado, sem PCG, Nanite desligado e Lumen desligado.
2. Regressão funcional/áudio do pacote e inspeção das imagens. Confirmar 60 instâncias
   PCG serializadas, materiais sem erro e navegação. Não substituir o download aprovado.
3. Conferir dia/noite e interiores reais; expandir PCG apenas após validação das zonas.
4. Rever modelos estilizados simples com o usuário na etapa de arte; Nanite/Lumen
   não substituem remodelagem. Os pedidos anteriores da migração continuam vigentes.
