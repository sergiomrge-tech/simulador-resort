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

## Benchmark exportado inicial (80%)

Executável do commit `b29c787f`, sem editor aberto, 1920×1080, TSR em 80%, RTX4060Ti8GB.
Quatro capturas CSV de 12 s após aquecimento, câmera fixa no bosque, perfil novo.

| Configuração | Frame médio | GPU média | FPS médio | Frame P95 |
|---|---:|---:|---:|---:|
| Tudo ativo | 10,290 ms | 8,932 ms | 97,2 | 14,257 ms |
| PCG oculto | 10,664 ms | 8,976 ms | 93,8 | 15,391 ms |
| Nanite desligado | 10,902 ms | 10,192 ms | 91,7 | 13,230 ms |
| Lumen desligado | 8,801 ms | 7,945 ms | 113,6 | 11,360 ms |

Memória local de GPU em torno de 3.065 MiB no caso completo. Não atribuir a pequena
variação ao ocultar PCG a uma melhoria; o resultado está sujeito a ruído. Os custos
separados dos passes constam de `package-benchmark.json`; eventos podem se sobrepor.
Dados brutos em `D:/CodexTemp/ue58-render-profile-20261028-182707`. Os quatro cenários
preservaram 60 instâncias serializadas e não geraram erros de script/material/Nanite.
Esta medição não substitui o teste em resolução nativa nem a regressão funcional.

A exposição agora usa limites EV100 0–8 à noite e 5–14 de dia, evitando que o limite
mínimo diurno torne a noite inteira preta. Alteração apenas visual, aguardando fotos
do próximo pacote. Novo parâmetro de QA permite medir resolução nativa com
`-MareNativeResolution`; ele não altera a preferência gráfica do jogador.

## Resolução nativa — benchmark do executável

Pacote `D:/Builds/MareAltaUE58_GraphicsNative_2026-10-28/Windows`, commit `52fd8f51`.
Saída 1920×1080 com ScreenPercentage=100, perfil descartável e quatro variantes:

| Variante | FPS médio | Frame P95 | GPU média |
|---|---:|---:|---:|
| Tudo ativo | 79,6 | 16,203 ms | 11,490 ms |
| PCG oculto | 83,0 | 14,115 ms | 11,384 ms |
| Nanite desligado | 79,7 | 14,101 ms | 12,067 ms |
| Lumen desligado | 91,3 | 13,275 ms | 10,211 ms |

Os resultados atendem à meta de 60 FPS **nesta câmera e neste intervalo**, não
comprovam o desempenho em todos os ambientes. O teste preservou 60 instâncias PCG
no pacote, dimensões corretas e log sem erros. Dados em
`D:/CodexTemp/ue58-render-profile-20261028-183344`, sumário versionado em
`graphics-reference/native-1080-benchmark.json`. A regressão funcional e revisão
específica de cada interior ainda são necessárias. Não comparar diretamente esses
valores com as primeiras capturas de viewport menor do editor.

## Nanite arquitetônico adicional — hotel

Para superar a limitação de transparência do modelo original, foram criadas duas
exportações derivadas de `SourceArt/Models/World_2365.gltf`, reutilizando seu BIN e
texturas, sem editar a fonte original:

- `HotelTower_Opaque`: 230.384 triângulos virtuais Nanite; fallback 3.404.
- `HotelTower_Glass`: 1.656 triângulos, transparência mantida, Nanite desativado.

A soma dos triângulos e a união dos limites foram comparadas com o original de
232.040 triângulos (tolerância de 1 cm para bounds). Duas novas ISMs cuidam somente
da renderização; a ISM original continua como colisor invisível com as mesmas
instâncias e QueryAndPhysics. As tags de expansão permanecem no mesmo ator, para
não liberar hotel antes da compra. Material-base derivado dentro de `/Game` quando
necessário; nenhum material da instalação Unreal foi editado.

Integração em Coast e imagens reais com câmera coincidente em
`graphics-reference/images/hotel-match-before.png` e `hotel-match-after.png`.
Relatório em `nanite-architecture-integration.json`. Isto substitui a conclusão
anterior de que não havia ativação adicional aprovada; o poste e a sorveteria
seguem sem Nanite porque misturam vidro no mesmo mesh. Falta medir o proxy novo
no executável com `test_graphics_package.ps1 -Hotel`, incluindo a variante
`hotel-legacy`, que mantém o modelo original completo como comparação de render.
A colisão detalhada antiga ainda gera aviso de muitos triângulos na navegação;
ela foi preservada, não otimizada nem ignorada como problema inexistente.

Para reconstruir o mapa posteriormente, aplicar `mare_nanite_architecture.integrate()`
após o gerador-base, e reaplicar `mare_graphics` para os setores de PCG/Lumen. A
adição não implementa gameplay dos negócios e não conclui a migração geral.
