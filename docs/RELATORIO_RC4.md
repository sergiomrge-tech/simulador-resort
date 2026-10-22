# Maré Alta Resort 1.0.1 RC4 — correção e pedidos visuais

Branch: `fix/visual-kiosk-orders-rc3` (mantida para continuidade do trabalho).
Código do jogo validado: `ffe0ea135bce60d11f3edbdd3b5bde09eb8f447c`.
[Execução do GitHub Actions](https://github.com/sergiomrge-tech/simulador-resort/actions/runs/39519582593).

## Causa e correção

O teste de ciclo completo aguardava o estado de um cliente por meio de uma lambda que capturava o nó. O cliente podia sair e ser liberado durante a espera. A captura inválida provocava acessos a `state` em objeto nulo e mensagens repetidas, terminando em `LOOP_TEST FAIL`. A espera agora recebe `WeakRef`, verifica remoção/liberação e encerra com falha controlada. O percurso completo até os assentos permanece coberto pelo teste específico do quiosque; o teste comercial usa uma aproximação curta e determinística.

AnimationPlayer e cabelos importados também mantinham owners da cena anterior ao serem transplantados para personagens. A limpeza recursiva do owner passou a ocorrer antes de remover e reanexar os nós.

Na integração dos pedidos, a validação revelou que `get_meta(chave, null)` ainda emite erro quando a chave não existe no Godot 4.5.1. A consulta passou a usar `has_meta` antes de ler. O workflow barra esse erro mesmo que o processo ou a suíte retornem sucesso.

## Arquivos alterados

| Grupo | Arquivos |
|---|---|
| Testes e ciclo de vida | `tests/loop_test.gd`, `tests/support/state_waiter.gd`, `tests/lifecycle_regression.gd`, `tests/order_visuals_regression.gd`, `scripts/people.gd` |
| Entrega e consumo | `scripts/dish_presentation.gd`, `scripts/village_life.gd`, `scripts/guest.gd`, `scripts/main.gd` |
| Cenário e iluminação | `scripts/world.gd`, `scripts/world_village.gd`, `scripts/daycycle.gd`, `scripts/toon.gd`, `shaders/ground.gdshader`, `shaders/palm_wind.gdshader` |
| Assets e instaladores | `tools/gen_dishes.py`, `tools/fetch_assets.py`, `tools/smooth_kenney.py`, `tools/build_patch.sh`, `.github/workflows/patch-1.0.1.yml` |
| Créditos e documentação | `CREDITS.md`, `docs/PEDIDOS_SERVIDOS_RC3.md`, este relatório |

Os nove IDs do cardápio têm apresentação própria. Cada unidade entregue aparece no assento reservado do cliente; pedidos parciais, múltiplos e repetidos são preservados. Saída, fechamento e troca de dia limpam os objetos. Estoque, preços, gorjetas, VIPs, metas, reservas e progressão continuam no fluxo existente. Pratos prontos fixos foram retirados da área de entrega do quiosque; equipamentos e ingredientes decorativos permanecem.

Louça e talheres: [Kenney Food Kit, CC0](https://kenney.nl/assets/food-kit). Os seis novos modelos de receitas são gerados pelo Blender com sementes fixas. As fontes, receitas e inclusões do patch estão documentadas no repositório.

## Validação

- Parsing dos scripts alterados no Godot 4.5.1, sintaxe Python, YAML/Bash e `git diff --check`: aprovados.
- `LIFECYCLE_TEST`, `KIOSK_TEST`, `ORDER_VISUAL_TEST` e `LOOP_TEST`: PASS no Actions.
- Capturas reais OpenGL de dia, noite, balcão e pedidos: geradas; sem erros de script, metadados, recursos ausentes, referências a nós liberados ou ownership inconsistente nos logs verificados.
- Patch sobre o PCK 1.0.0 e pacote completo: aprovados, com pedidos reais, sem erros de script, metadados ou recursos ausentes.
- Exportação Windows, geração NSIS e publicação: concluídas; execução `39519582593` terminou com `success`.
- [Instalador completo](https://github.com/sergiomrge-tech/simulador-resort/releases/download/v1.0.1-rc4/Instalar_MareAltaResort_v1.0.1.exe): 1.119.419.918 bytes. SHA-256 `a634eb4fcd9f4f0675de2be6e3864567616409b7494c2d87547c51b2cb49fbde`.
- [Atualização](https://github.com/sergiomrge-tech/simulador-resort/releases/download/v1.0.1-rc4/Atualizar_MareAltaResort_v1.0.1.exe): 82.611.574 bytes. SHA-256 `a0f1cf1bada122975ea0cd842d7f08adbd7645609c6390ca46d9ac825675edd2`.
- A prévia pública `v1.0.1-rc4` aponta para o código testado; os três assets da release estão marcados como `uploaded`.

Os logs ainda registram avisos de recursos/RIDs ao encerrar os processos de teste/renderização. A suíte não comprova ausência de vazamentos durante sessões longas. No smoke do patch, o runner não tem dispositivo ALSA e usa o driver de áudio Dummy; isso não valida reprodução sonora no Windows. A franja do telhado ainda sobrepõe a parte superior da placa na captura frontal, exigindo ajuste visual de acabamento.

## Verificação manual pendente

1. Instalar e iniciar no Windows real; conferir atalhos, diretório escolhido e abertura do jogo.
2. Atualizar uma instalação 1.0.0 e carregar um save existente; salvar novamente e reabrir.
3. Conferir de perto os nove itens, a escala sobre cada mesa/balcão e a animação de consumo. As capturas atuais são abertas e não aprovam todos esses detalhes.
4. Conferir a placa sob o beiral, os níveis de qualidade, dia/noite, áudio, FPS e estabilidade em uma sessão longa no PC do usuário. Não houve execução do instalador Windows nem medição de desempenho no aparelho.
