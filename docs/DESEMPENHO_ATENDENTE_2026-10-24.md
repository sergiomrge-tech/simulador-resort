# Desempenho e atendente único — 24/10/2026

Linha 1.1.0 RC2, Godot 4.5.1, branch codex/resort-1.1-mcp. Pedidos atuais:
otimizar para RTX 4060 Ti e usar somente um funcionário no atendimento do quiosque.

## Otimizações

- Materiais de modelos repetidos compartilhados por fonte/cor. Preserva mapas,
  textura, transparência, tintas e variações; alterações individuais duplicam o
  material antes de pintar. Real.place e B.model usam o mesmo cache.
- NPCs filtram os bloqueios próximos uma vez por passo, reutilizando a busca nas
  múltiplas correções da caminhada. Rotas/destinos/mesas mantêm a regra original.
  Regressão compara 1200 trajetos com o algoritmo sem cache, incluindo sobreposição.
- Occlusion culling apenas com volumes contidos dentro dos corpos opacos das casas
  decorativas. Não há um volume fechando a casa acessível do jogador ou o quiosque.
  Objetos realmente escondidos pelas casas deixam de consumir desenho.
- LOD dos modelos importados ajustado por preset: Baixo 3 / Médio 2 / Alto 1,5 /
  Ultra 1 pixel. Modelos/fontes detalhados e mapas preservados.
- Sombras direcionais: 35/50/75/110 m por preset; duas cascatas até Alto e quatro no
  Ultra. Mantém detalhe próximo, reduz trabalho com sombras muito distantes.
- Tela física do PC atualiza quando os dados mudam; não redesenha a interface
  estática em todos os quadros. Mudanças de caixa/empresa/horário continuam visíveis.
- Quantidade de moradores preservada: 12 HD/5 baixa. Não foram removidos os animais,
  navio, baleias, nuvens ou a decoração da vila. Configurações/saves não são apagados.

## Medição e limites

Máquina medida: RTX 4060 Ti 8 GB, Ryzen 7 5700G. 1920×1080, preset Alto, resolução
nativa, FSR desligado e VSync desligado somente no benchmark. Câmeras fixas no
quiosque, vila e praia; dois segundos de aquecimento e seis de medição por braço.
Duas rodadas pareadas, invertendo a ordem, no mesmo processo para reduzir a
interferência das demais aplicações. Unity/compilação e outros aplicativos estavam
abertos em segundo plano; portanto os FPS variam entre as rodadas.

O braço original usa materiais individuais, a busca de colisão sem cache,
parâmetros anteriores de LOD/sombra e occlusion culling desligado. O otimizado usa
as mudanças acima. São controles no mesmo executável, não uma promessa de FPS
fixo em qualquer save, resolução ou computador. Os primeiros ensaios sequenciais
variaram muito e não foram usados como estimativa final do ganho.

Medições finais no executável/PCK, em ordem normal e invertida:

| Rodada / cena | Controle | Otimizado |
|---|---:|---:|
| 1 / quiosque | 96.3 FPS | 118.9 FPS |
| 1 / vila | 70.9 FPS | 98.1 FPS |
| 1 / praia | 106.1 FPS | 104.6 FPS |
| 2 / quiosque | 99.9 FPS | 119.5 FPS |
| 2 / vila | 55.9 FPS | 90.3 FPS |
| 2 / praia | 105.5 FPS | 134.6 FPS |

A primeira rodada teve +23,4% no quiosque e +38,2% na vila; a segunda teve maior variação da carga de GPU em segundo plano. Na vila as chamadas de desenho caíram de cerca de 5200 para 2000 (62%); as primitivas incluindo sombras, cerca de 32%. Na praia a primeira rodada foi neutra e a segunda variou bastante: não atribuir essa oscilação toda às otimizações. Não é uma garantia de FPS nem uma medição isolada de outros aplicativos.

As primeiras rodadas na fonte (paired-high, paired-high-reverse e paired-ultra) ficam como dados exploratórios: o controle inicial individualizava materiais de B.model. O benchmark final também individualiza os de Real.place; os números finais acima correspondem ao PCK entregue. Cores HDR preservadas no cache final.

Dados finais: [rodada normal](qa/desempenho-atendente-2026-10-24/final-exported-paired-high.json), [ordem invertida](qa/desempenho-atendente-2026-10-24/final-exported-paired-high-reverse.json).

Reproduzir: tools/run_perf.ps1 -Label comparacao -Preset 2 -Paired, e repetir com
-Reverse. Salva resultados em D:/CodexTemp/resort-perf, sem acessar saves reais.
-Exported usa o PCK exportado. --perf-original é somente um controle de benchmark.
Os controles não são opções oferecidas ao jogador nem modificam seus settings.

Referências da engine:
https://docs.godotengine.org/en/4.5/tutorials/performance/optimizing_3d_performance.html
https://docs.godotengine.org/en/4.5/tutorials/3d/mesh_lod.html
https://docs.godotengine.org/en/4.5/tutorials/3d/occlusion_culling.html

## Um atendente para o quiosque

A vaga ativa é atendente. Ele anota no balcão, busca o produto pronto, entrega,
caminha ao PC para receber e recolhe a louça nas mesas. Tarefas são sequenciais;
não precisa contratar garçom, caixa, auxiliar de limpeza nem cozinheiro separados.
Falta de estoque não bloqueia limpeza; não há preparo nem compra automática extra.

Uma única contratação/diária: base R$ 240 para contratar e R$ 30/dia, ou valores do
perfil escolhido. O turno padrão acompanha todo o expediente. Turnos personalizados,
folga, energia, salários proporcionais e treinamento continuam disponíveis.
Os três perfis são alternativas para a mesma vaga. Cargos do resort, como camareira,
barman e guia, continuam independentes do único atendente do quiosque.

Saves com vários cargos do quiosque são unificados ao carregar: mantém o maior
nível (XP desempata), turno/perfil correspondente e os registros históricos. Não
cobra contratação/rescisão, não reembolsa investimentos históricos e não altera
estoque/dinheiro. Somente atendente fica ativo e recebe diária. Migração repetida
não duplica experiência/custos; nomes de cargos antigos permanecem no formato do
save por compatibilidade, sem oferecer novas contratações desses cargos.

## Validação e distribuição

Regressões: optimization, single-staff, company, practical, simulation, management,
counter-first, tableware, home, counter e phone-layout, com APPDATA de teste separado.
Logs e capturas finais ficam em docs/qa/desempenho-atendente-2026-10-24.
As onze regressões passaram na fonte e no executável/PCK, com saída 0 e sem ERROR/REAL_MISSING. O teste de otimização do pacote final também verifica que cores HDR não colidem com branco no cache. PCK e logs finais: [validacao-pck.json](qa/desempenho-atendente-2026-10-24/validacao-pck.json). Capturas da gestão, casa e cenas do benchmark foram inspecionadas visualmente.

Empacotar: tools/package_quiosque_portable.py --variant performance.
Destino D:/Downloads/MareAltaResort_1.1_RC2_Performance_Atendente_2026-10-24.zip.
Extrair inteiro no D e abrir Jogar.vbs. Preservar userdata/ ao atualizar.

Release desta revisão: [Windows — desempenho e atendente](https://github.com/sergiomrge-tech/simulador-resort/releases/tag/v1.1.0-rc2.20261024-performance-atendente).
