# Empresa e atendimento físico — 1.1.0 RC2

Branch: `refine/company-kiosk`. Código testado: `d107960625e68b8751631ab43685685f8b8c7bf4`.
Base: refinamento visual RC5 sobre o RC4. O diagnóstico da falha original de referências liberadas e ownership permanece em [RELATORIO_RC4.md](RELATORIO_RC4.md).

## Como jogar

1. Abra **B → Minha Empresa**. Escolha nome de 1 a 24 caracteres, fonte e cor. O texto é medido para caber inteiro nas duas placas.
2. Ative **Atendimento com retirada e entrega**. Contorne o quiosque para chegar ao anexo na parte de trás.
3. Na geladeira, prepare/retire bebidas. Na cozinha, prepare comida; retire os pratos prontos no armário. Tempo base: 3 segundos para bebidas e 6 para comida, com aceleração pelo cozinheiro.
4. Leve um item por vez e aperte **E no cliente** que o pediu. Pedidos múltiplos aceitam entrega em qualquer ordem, com o alimento correto aparecendo na mesa/balcão.
5. Receba as contas no terminal do balcão. Após o cliente consumir e sair, recolha a louça para liberar o lugar. O próprio ponto de interação do balcão também permite receber e recolher a louça das banquetas.
6. Em **Equipe**, contrate e gerencie os funcionários. Salários diários, energia, treinamento e folgas usam o sistema existente.

| Cargo | Contratação | Salário base/dia | Trabalho |
|---|---:|---:|---|
| Garçom | R$ 260 | R$ 38 | Retira produto pronto, contorna o quiosque e entrega |
| Operador de caixa | R$ 220 | R$ 32 | Recebe contas pendentes |
| Auxiliar de limpeza | R$ 180 | R$ 28 | Caminha até o lugar e recolhe a louça |
| Cozinheiro | R$ 300 | R$ 44 | Prepara pedidos pendentes e repõe produtos |

O atendente anterior continua disponível: conserva o serviço anterior no modo original; na empresa ajuda nas entregas, ou no preparo quando há um garçom contratado. As receitas e expansões mantêm seus requisitos de progressão.

## Estoque, cobrança e save

- Ingredientes são descontados uma vez, no início do preparo. Retirada e entrega movimentam produtos prontos.
- Cada produto comporta quatro unidades na prateleira. O preparo reserva uma vaga para impedir perda por devolução durante a produção.
- Jogador e garçom têm inventários separados. Se o cliente sair, o produto do garçom volta à prateleira. O item também é salvo durante o percurso.
- Entregar cria uma conta a receber. O recebimento remove a conta antes de creditar o dinheiro, evitando duplicação. Gorjetas, avaliações, metas e progressão continuam ativas.
- Save v7 guarda marca, fonte, cor, modo de atendimento, prateleiras, preparo, itens carregados, contas e lugares sujos.
- Saves v6 preservam dinheiro/progressão e continuam no atendimento original até criar e ativar a empresa.
- Desligar o atendimento físico exige concluir o preparo, esvaziar as mãos, receber contas e limpar lugares. Produtos prontos podem continuar guardados.
- Para voltar a uma versão anterior, use um backup anterior de `userdata`: versões antigas não reconhecem o estado da empresa.

## Arquivos alterados

| Arquivos | Responsabilidade |
|---|---|
| `scripts/company_rules.gd` | Nome, fontes, cores, medição das placas e validação do save |
| `scripts/resort_core.gd`, `scripts/economy.gd` | Empresa, produção, estoque pronto, contas, cargos e save v7 |
| `scripts/kiosk_operations.gd` | Estações, porta de vidro, produtos visíveis, item nas mãos, interações e funcionários |
| `scripts/village_life.gd` | Entrega por item, ordem flexível, limpeza e compatibilidade do atendimento anterior |
| `scripts/world_village.gd` | Marca nas placas, suportes/letreiro e aproximação das banquetas |
| `scripts/phone_ui.gd`, `scripts/player.gd`, `scripts/hud.gd` | Editor, operação próxima à estação, objetivos e digitação sem movimento/atalhos |
| `scripts/main.gd` | Integração e cenário de captura real |
| `tools/gen_kiosk_service.py`, `tools/fetch_assets.py`, `tools/build_patch.sh` | Modelos originais e inclusão nos pacotes |
| `tests/company_regression.gd`, `tests/loop_test.gd` | Regressões da empresa, da interface e do serviço na cena |
| `.github/workflows/visual-refine.yml` | Testes, capturas Godot, exportação, teste do PCK e instalador completo |
| `.github/workflows/patch-1.0.1.yml` | Fluxo cumulativo alinhado à versão 1.1.0 e teste da empresa |
| `project.godot`, `export_presets.cfg`, `installer/setup.nsi`, `installer/LEIA-ME.txt`, `CREDITS.md` | Versão, instalação, instruções e autoria |

## Validação

A RC1 teve uma espera ausente no teste da cena: `run()` não aguardava `_integration()`. Assim, o PASS anterior não comprovava a conclusão das verificações assíncronas de rascunho/equipe. A RC2 aguarda o fluxo inteiro e exige nos logs os marcadores de atendimento pelo cozinheiro/garçom, limpeza, folga e preservação do rascunho. O teste da tecla B também executa com `Core.in_game=true`.

A [execução 39591282021](https://github.com/sergiomrge-tech/simulador-resort/actions/runs/39591282021) terminou com **sucesso**. `LIFECYCLE_TEST`, `KIOSK_TEST`, `ORDER_VISUAL_TEST`, `LOOP_TEST` e `COMPANY_TEST` passaram. O teste da empresa passou na fonte e novamente no PCK exportado.

Os logs reais, além das linhas de comando, confirmam duas ocorrências de cada marcador — uma na fonte e outra no pacote:
- preservação do rascunho durante vendas/reposição;
- preparo, retirada, percurso e entrega pelo cozinheiro/garçom;
- caminhada e limpeza da louça;
- suspensão do garçom durante a folga.

Também passaram a migração/save v7, o limite/medição do nome e fontes, estoque sem débito duplo, cobrança sem repetição, entrega parcial e fora de ordem, assentos sujos bloqueados até limpar e apoio/colisão do deck. O ciclo completo terminou com dinheiro 5487, estrelas 4,54 e 26 vendas no bar.

Quatro capturas reais do Godot foram geradas e os logs conferidos. A inspeção visual local ficou pendente devido a desconexões do ambiente/visualizador. Permanecem avisos de recursos/RIDs/ObjectDB no encerramento do renderizador dummy e avisos de UID com fallback textual em execuções da fonte; não houve `SCRIPT ERROR` nos registros finais. Esses avisos de encerramento não foram corrigidos nesta versão.

## Instalador e arquivos

- [Instalador completo 1.1.0 RC2](https://github.com/sergiomrge-tech/simulador-resort/releases/download/v1.1.0-rc2/Instalar_MareAltaResort_v1.1.0.exe) — 1119645243 bytes, aproximadamente 1,12 GB.
- [Release de testes](https://github.com/sergiomrge-tech/simulador-resort/releases/tag/v1.1.0-rc2).
- SHA-256 do executável informado pelo GitHub: `85595d7d12fcb5185f6c0e7214ce514aa568cb6e2868eaae80887e764d7c7091`.
- [Capturas](https://github.com/sergiomrge-tech/simulador-resort/actions/runs/39591282021/artifacts/12343430397).
- [Logs e capturas de auditoria](https://github.com/sergiomrge-tech/simulador-resort/actions/runs/39591282021/artifacts/12342894201).
- [Instalador e checksum no Actions](https://github.com/sergiomrge-tech/simulador-resort/actions/runs/39591282021/artifacts/12342978743).

O jogo publicado corresponde a `d107960625e68b8751631ab43685685f8b8c7bf4`. O executável foi exportado para Windows e o PCK foi testado pelo Godot Linux. A instalação no Windows permanece pendente de teste manual.

## Verificação manual no Windows

- Instalar sobre a versão anterior e conferir saves/configurações.
- Conferir nomes com acentos e 24 caracteres, três fontes e leitura das placas de dia/noite.
- Avaliar vidro, abertura da porta, acesso aos equipamentos, item carregado e ângulos de interação.
- Completar um turno manual e outro com a equipe, verificando percursos, animações, contas, salários, energia, folgas e limpeza.
- Salvar/reabrir com produto nas mãos, preparo e contas pendentes.
- Conferir teclado/controle, áudio, desempenho e renderizadores no computador do jogador.

A execução do pacote pelo Godot no Linux não substitui a instalação e o teste interativo do executável no Windows.
