# Estado salvo para continuar com outra IA — 23/10/2026 (atualizado)

Leia também AGENTS.md, CONTINUAR.md, COMPUTADOR_E_BALCAO.md e CLAUDE.md.

## Base

- Repositório: sergiomrge-tech/simulador-resort.
- Branch de entrega: `codex/resort-1.1-mcp` (checkpoint anterior `07cbb20`).
- Correções deste lote na branch de trabalho `cursor/loop-counter-aim-ee9e`
  (a empilhar / mesclar em `codex/resort-1.1-mcp`).
- Versão 1.1.0 RC2, Godot 4.5.1, Forward+ / Vulkan.

## O que já estava no checkpoint 07cbb20

- Gestão no computador físico do balcão (E no monitor; B só perto).
- Interface compacta, cantos arredondados, seis áreas.
- Quiosque começa fechado; abertura manual; dormir fecha de novo.
- Clientes pedem/retiram no balcão antes de sentar (modo físico).
- Porta da casa com E; tampo escuro / base cinza; copos e promoções.
- Fontes Blender, geradores, catálogo e docs.

## Correções deste lote (mira, rush, encerramento)

1. **Interactable do balcão** (`world_village.gd`): caixa 3,0×1,2×0,4 m em
   z≈1,88 (lado interno, à frente da madeira), sem cobrir o PC em x≈1,70.
   A mira do staff deixa de bater na StaticBody da madeira com prompt vazio.
2. **Fixture do `--loop-test`** (`loop_test.gd`): `Core.set_kiosk_open(true)`
   antes do atendimento legado e do rush; mira pelo lado interno
   (`kiosk_point(0, 0.12, 0.65)`, pitch −18). Verificações Pegar/venda/keat/combo
   e chegadas do rush **mantidas** — não foram removidas nem o fluxo voltou
   a atendimento sentado.
3. **`coastal_life.gd`**: iate/cruzeiro nascem mesmo se o UBC faltar; jogadores
   de vôlei só se os corpos existirem; `is_instance_valid` em `_process`;
   `set_process(false)` + limpeza de refs em `tree_exiting` (mitiga AV no
   encerramento após PASS lógico).

## Verificação neste ambiente (Linux, Godot 4.5.1, gl_compatibility)

APPDATA/`XDG_DATA_HOME` isolados; saves reais não tocados. Após `fetch` do UBC
e `--import`:

| Teste | Fonte | PCK exportado (`--main-pack`) |
|---|---|---|
| `--loop-test` | PASS, exit 0, 0 SCRIPT ERROR | PASS, exit 0 |
| `--counter-first-test` | PASS, exit 0 | PASS, exit 0 |
| `--company-test` | PASS, exit 0 | PASS, exit 0 |
| `--coastal-test` | PASS, exit 0 | (não reexportado dedicado) |
| `--terminal-test` | PASS, exit 0 | — |

PCK de fumaça gerado aqui (~439 MB, LITE/assets parciais) só para validar
scripts no pack; **não** substitui o PCK Windows completo (~1,8 GB) da máquina
do Sérgio. Imagens de referência em `docs/images/computador-balcao/` conferidas
(gestão, balcão madeira/cinza, porta).

O **access violation Windows (−1073741819)** do checkpoint anterior não se
reproduz neste Linux (exit 0 + RID warnings conhecidos). A mitigação de
liberação do `coastal_life` deve ser revalidada no executável Windows com
`run_counter_batch.ps1 -Exported`.

## Ainda pendente na máquina Windows do Sérgio

- Projeto: `C:/Users/sergi/Documents/ChatGPT/resort 2`.
- Engine: Godot 4.5.1 em
  `C:/Users/sergi/Documents/ChatGPT/Gestao Facil/Ilha Selvagem/tools/`.
- Reexportar PCK completo (prune → export-pack → restore), rodar o batch
  `-Exported` (loop, counter-first, company, terminal) e confirmar exit 0
  sem AV no encerramento.
- **ZIP em Downloads ainda é da revisão anterior** (23/10 ~16:40):
  `C:/Users/sergi/Downloads/MareAltaResort_1.1_CaisCorrigido.zip`.
  Só atualizar com `tools/package_quiosque_portable.py` **depois** da
  validação no PCK Windows completo. Este ambiente Linux não tem esse caminho.

## Comandos úteis

```powershell
./tools/run_counter_batch.ps1 -Checks @('loop','terminal','counter-first','company')
./tools/run_counter_batch.ps1 -Exported -Checks @('loop','terminal','counter-first','company')
```

Linux (dados isolados):

```bash
export XDG_DATA_HOME=/tmp/mare-qa/$RUN HOME=/tmp/mare-qa/$RUN-home
godot --headless --path . --rendering-driver opengl3 --rendering-method gl_compatibility \
  --audio-driver Dummy -- --loop-test --quality=0
```

## Imagens

![Gestão no computador](images/computador-balcao/gestao.png)

![Balcão em madeira escura e cinza](images/computador-balcao/balcao.png)

![Porta funcional de madeira](images/computador-balcao/porta.png)
