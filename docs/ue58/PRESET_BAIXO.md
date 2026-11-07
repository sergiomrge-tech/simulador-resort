# Preset gráfico Baixo — proposta sem alteração de C++ (Pacote 8)

## Estado observado

Li `MareOptions.h/.cpp` e `tools/ue58/bench_package.ps1` sem editar C++. O projeto **já oferece** `SetPreset(0)` (grupos Scalability 0, isto é, Baixo), mas **não** altera necessariamente `Crowd`, escala da resolução nem desliga caminhos específicos de Lumen apenas com esse botão. `MareOptions.h` inicia `GlobalIllumination=1`, `Reflections=1` (Lumen Lite), `Crowd=1` (6 caminhantes; distância 5000 cm). `Crowd=0` usa **3 caminhantes e 3500 cm**. `ModelDetail=0` já aplica `r.StaticMeshLODDistanceScale=2` e `r.SkeletalMeshLODBias=2`. `r.HairStrands.Simulation` só fica ativo em Effects=3, portanto normalmente já fica desativado no Baixo.

## Configuração proposta para verdadeiro modo Baixo (Claude em C++)

| Alavanca | Configuração proposta | Por que ajuda | Ganho esperado / cautela |
|---|---|---|---|
| Scalability geral | `Preset=0`; `sg.ShadowQuality=0`, `sg.GlobalIlluminationQuality=0`, `sg.ReflectionQuality=0`, `sg.PostProcessQuality=0`, `sg.ViewDistanceQuality=0`, `sg.FoliageQuality=0`, `sg.EffectsQuality=0`, `sg.TextureQuality=0`, `sg.AntiAliasingQuality=0`, `sg.ShadingQuality=0` | Reduz custo de sombra, GI, reflexos, shaders e vegetação | Potencial redução de tempo de GPU e VRAM; medir a qualidade e não somar estimativas |
| Desligar Lumen de verdade | Avaliar `r.DynamicGlobalIlluminationMethod=0` e `r.ReflectionMethod=0`, além de `GlobalIllumination=0` e `Reflections=0`; compatibilizar com `DefaultEngine.ini` e restart | Evita GI/reflexos Lumen no hardware de entrada | Pode reduzir custo de GPU; verificar iluminação indireta sem ambientes escuros |
| Segurança Lumen | **Manter** `r.Lumen.AsyncCompute=0` independentemente do preset | `KeepLumenSafe()` mitiga falha de GPU já tratada no projeto | Segurança, não é ajuste de FPS |
| População | `Crowd=0`: **3** walkers e alcance **3500 cm**, contra normal **6** e **5000 cm** | Diminui animação, tick, draw calls, cabelo | Hipótese de melhora na CPU/GPU em vila, recepção e praia; assegurar que NPCs funcionais permaneçam |
| MetaHuman distante | Instância simplificada/impostor/LOD agressivo e visibilidade por distância; nunca remover NPC crítico | Reduz skin, groom e draw calls de humanos longes | Potencial melhora significativa em aglomerações; requer C++/editor e testes de popping |
| Detalhe de modelos | `ModelDetail=0` → `r.StaticMeshLODDistanceScale=2`, `r.SkeletalMeshLODBias=2` (já implementado) | Transição de LOD mais cedo | Menos triângulos/skin; manter legibilidade de balcões e placas |
| Sombras | `Shadows=0`; testar `r.ShadowQuality=1`, distância e cascatas menores, não usar sombras caras em figurantes | Custo de sombras é sensível à quantidade de objetos | Redução de GPU; verificar sombra de objetos importantes |
| Vegetação / Nanite / PCG | `Foliage=0`, `ViewDistance=0`, distância de cull conservadora por grupo e densidade de instâncias reduzida | Praia/serra podem ter muitos materiais e instâncias | Ganho de renderização/memória pode variar; não desligar PCG/Nanite globalmente sem comparar |
| Resolução | 1920×1080 de saída, `ResolutionScale=67–75` com TSR; sugerir 1280×720 se GPU não mantiver 30 FPS | Reduz pixels sombreados | Melhora GPU quando pixel-bound; troca por nitidez |
| Upscaler e FG | `Upscaler=TSR` por compatibilidade; `FrameGeneration=0`, sem depender de DLSS/FSR | Preset válido mesmo em GPU sem RTX 40 | Compatibilidade maior; FPS real é a métrica, não só apresentado |
| Texturas | `Textures=0`, pool de streaming testado sem thrashing | Reduz pressão em VRAM 6 GB | Menos stutter quando acima do orçamento; medir VRAM |
| Cabelo | `Effects=0` já desativa simulação `r.HairStrands.Simulation=0`; oferecer card hair simplificado | Gamer não paga por groom dinâmico desnecessário | Melhoria já parcialmente presente; não anunciar como novidade |

**Importante:** variáveis exatas de Lumen, shadow/PCG e groom requerem comprovação no executável UE5.8. Valores aqui são metas, não testes executados. Não alterar `DefaultEngine.ini` ou assets até confirmar que as mudanças não prejudiquem configurações Média/Alta.

## Benchmarks disponíveis, sem extrapolação indevida

- `docs/ue58/graphics-reference/package-benchmark.json` (1080p de saída, screen percentage 80, variante all-enabled): frame mean **10,29 ms**, p95 **14,26 ms**, GPU média **8,93 ms**, VRAM **3065 MB**. Registrado em cenário/ambiente específico; **não equivale a mínimo suportado**.
- `docs/ue58/graphics-reference/native-1080-benchmark.json` (1080p nativo, all-enabled): mean **12,56 ms**, p95 **16,20 ms**, GPU **11,49 ms**, VRAM **3279 MB**. Há variantes comparativas sem PCG, mas os resultados não isolam todas as otimizações e podem ser limitados por CPU, render thread ou GPU.
- `bench_package.ps1` permite `-Variants @('', 'MareBenchNoPeople', 'MareBenchNoGroom')`, `-ResX 1920 -ResY 1080`, `-Soak 7200`, `-NoShadow`, `-Exec`, e imprime métricas do `bench.json`. **Nenhum benchmark deste pacote foi executado num hardware mínimo.** Não transformar ganho hipotético em FPS anunciado.

## Requisitos para Steam — **provisórios, não publicar como comprovados**

| | Mínimos a validar | Recomendados a validar |
|---|---|---|
| SO | Windows 10 64-bit / Windows 11; DirectX 12 | Windows 11 64-bit |
| CPU | Intel Core i5-10400 ou AMD Ryzen 5 3600 | Intel Core i5-12400 ou AMD Ryzen 5 5600 |
| RAM | 16 GB | 32 GB |
| GPU | NVIDIA RTX 2060 6 GB ou AMD RX 6600 8 GB (UE 5.8 + Nanite/DX12 a conferir) | NVIDIA RTX 3060 12 GB / RTX 4060 8 GB ou AMD RX 6700 XT 12 GB |
| Armazenamento | SSD, **espaço a medir após package** (não chutar GB) | SSD NVMe, espaço a medir |
| Meta | 1280×720, Baixo, 30 FPS reais estáveis após testes | 1920×1080, Médio/Alto, 60 FPS reais após testes |

Não incluir placa integrada ou 8 GB RAM sem ensaios específicos. Se mínimo proposto não atingir critérios, subir o requisito ou reduzir recursos, não esconder o problema com frame generation.

## Roteiro de medição obrigatório (Claude)

1. Gerar pacotes Windows Shipping comparáveis, sem editor aberto, da mesma revisão Git/mesmos saves/mapa. Capturar `MareOptions.json`, `DefaultEngine.ini`, versão do driver, hardware real, resolução e RHI.
2. Configuração A = Médio atual; B = `SetPreset(0)` atual; C = Baixo proposto, explicitando diferenças de GI, crowd, sombras, TSR, LOD e groom. Reiniciar processo sempre que uma variável exigir restart. Medir também `MareBenchNoPeople`/NoGroom e sem sombra para isolar gargalos.
3. Em **pelo menos 3 repetições** por configuração, testar praia, quiosque com fila, vila, hotel e piscina, de dia/noite e com movimento. Aquecer shaders/asset cache, registrar fps médio, 1% low, p95/p99 frame ms, GPU ms, game/render thread, VRAM e stutter. Não misturar FPS com Frame Generation com FPS real.
4. Hardware A: RTX 4060 Ti 8 GB para baseline; B: PC mínimo proposto, de preferência CPU i5-10400/R5 3600 e GPU RTX 2060 ou RX 6600; C: PC recomendado. Usar o mesmo driver/cenário por comparação.
5. Rodar `powershell -File tools/ue58/bench_package.ps1 -Package 'D:/Builds/.../Windows' -ResX 1920 -ResY 1080 -Variants @('','MareBenchNoPeople','MareBenchNoGroom')` (ajustar sintaxe de arrays PowerShell no terminal conforme necessário). Repetir 7200 s para sessão longa, verificar aumento de memória e FPS.
6. Critérios antes da Steam: mínimo p95 de frame <=33,3 ms e quase nenhum frame >66,7 ms na meta 30 FPS; recomendado p95 <=16,7 ms na meta 60; sem crashes, falhas de renderização, pop-in inaceitável, travamentos de NPC, problemas de luz noturna. Se falhar, revisar presets/requisitos e repetir.
7. Registrar tabela **observado vs esperado** em relatório, screenshots reais e logs. **Nada no Pacote 8 é medição inédita.**
