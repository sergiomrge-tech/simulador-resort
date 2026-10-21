# Empresa e atendimento físico — 1.1.0 RC1

Branch: `refine/company-kiosk`. Código testado: `7d4f7cf85bf16290a935a7a6a8d4e6120aafc031`.
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

- Godot 4.5.1 local: scripts compilados e regras/estoque/cobrança/save aprovados com `COMPANY_TEST PASS`.
- Teste isolado dos equipamentos com os quatro GLBs reais: estações, colisões condicionais, vidro após importação/toon, editor e porta aprovados com `EQUIPMENT_TEST PASS`. O renderizador dummy registrou `Parameter material is null` no encerramento; a avaliação visual usa OpenGL no CI.
- Blender 4.5.14: quatro equipamentos gerados e importados. Vidro exportado com `alphaMode=BLEND` e alfa 0,14, preservados pelo Godot.
- [Actions 39579903544](https://github.com/sergiomrge-tech/simulador-resort/actions/runs/39579903544): ciclo de vida/ownership, importação, assentos, pedidos visuais, ciclo completo e empresa **aprovados**. O teste da empresa verificou preparo pelo cozinheiro, retirada/percurso/entrega pelo garçom, caixa, limpeza, formulário e migração na cena real.
- Capturas da empresa e empacotamento: em andamento. A publicação do instalador depende da aprovação de todas as etapas, incluindo a execução do PCK exportado.

## Verificação manual no Windows

- Instalar sobre a versão anterior e conferir saves/configurações.
- Conferir nomes com acentos e 24 caracteres, três fontes e leitura das placas de dia/noite.
- Avaliar vidro, abertura da porta, acesso aos equipamentos, item carregado e ângulos de interação.
- Completar um turno manual e outro com a equipe, verificando percursos, animações, contas, salários, energia, folgas e limpeza.
- Salvar/reabrir com produto nas mãos, preparo e contas pendentes.
- Conferir teclado/controle, áudio, desempenho e renderizadores no computador do jogador.

A execução do pacote pelo Godot no Linux não substitui a instalação e o teste interativo do executável no Windows.
