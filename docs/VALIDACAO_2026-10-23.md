# Validação da atualização RC2 de 23/10/2026

As pendências do checkpoint 07cbb20 foram resolvidas. Engine Godot 4.5.1,
Forward+ / Vulkan, RTX 4060 Ti. Testes usaram APPDATA isolado, sem alterar saves
reais. O executável foi iniciado pela pasta portátil, sem --path do projeto.

## Correções

- Mira legada: alvo do balcão volta a começar antes da colisão do tampo,
  recortado na extremidade do computador. Preservados os dois atendimentos por dentro.
- Rush: a fixture abre explicitamente o quiosque antes de esperar chegadas.
  O jogo continua iniciando fechado e fechando novamente ao dormir.
- Palm._coco_mesh libera a instância temporária após extrair Mesh/Material.
  Teste reconstrói o cache três vezes e verifica que não acumula nós órfãos.
- Core.quit_game remove a cena mantendo recursos gráficos vivos até o renderer
  processar os quadros pendentes. Botões de saída, fechamento da janela e testes
  usam esse caminho. Salvar ao sair da janela/menu foi preservado.
- Core.release_visual protege a troca/remoção de produtos e NPCs durante o jogo.
- Capturas são gravadas em user://qa_shots; res:// não é gravável no executável.
  Runner rejeita qualquer ERROR:, além de falhas lógicas e saída diferente de 0.

## Resultados no executável

| Teste | Resultado | Saída |
|---|---|---|
| terminal | PASS | 0 |
| counter-first | PASS | 0 |
| company | PASS | 0 |
| counter | PASS | 0 |
| practical | PASS | 0 |
| phone-layout | PASS | 0 |
| home | PASS | 0 |
| simulation | PASS | 0 |
| management | PASS | 0 |
| loop | PASS | 0 |

Logs em [qa/release-2026-10-23](qa/release-2026-10-23), sem ERROR:, REAL_MISSING,
falhas lógicas ou avisos de recursos vazados. Gestão foi repetida após ajustar
a indentação da criação da pasta de capturas; essa última mudança alterou apenas
o teste. Retirada/empresa foram repetidos para conferir o encerramento.

O ciclo geral final registrou `LOOP_TEST PASS dinheiro=5506 estrelas=4.56 bar=48`.
Inclui atendimento legado, abertura manual no rush, estoque, VIP, progressão,
clima, finanças e salvar/carregar. O teste físico verifica pedido parcial/completo,
fila, retirada antes da mesa e ausência de cobrança duplicada.

Inspeção visual do balcão, PC, cliente consumindo na mesa e porta; captura do menu
confirmou **v1.1.0 · RC2 · 23/10/2026 · PC**. Smoke do menu encerrou com saída 0,
sem erros. Imagens em images/computador-balcao.

## Artefato de distribuição

- Release: `v1.1.0-rc2.20261023`.
- Arquivo: `MareAltaResort_1.1_RC2_2026-10-23.zip`.
- Tamanho: **1.564.730.396 bytes** (aproximadamente 1,56 GB).
- ZIP verificado por CRC, sem userdata/saves. Checksum externo acompanha a release.
- SHA-256 do ZIP: `e24aa3747917a3d8068660576b57bd233300264b5ba009a6469ac355a293f395`.
- PCK: **1.798.934.644 bytes**.
- SHA-256 do PCK: `dcb848afebe166ca89f96314ac12fceb32f5431ebd4435dca7039cd1945dfde7`.

Extraia a pasta inteira e abra Jogar.vbs ou MareAltaResort.exe. Preserve userdata
ao atualizar. O instalador da release de 21/10 permanece histórico; o ZIP acima
contém as atualizações de 23/10.
