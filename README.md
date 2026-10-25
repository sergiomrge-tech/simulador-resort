# Maré Alta Resort 🌴

Simulador de quiosque e resort em primeira pessoa numa vila do Nordeste brasileiro,
feito em **Godot 4.5.1**, GDScript, Forward+, para Windows.

Linha atual: **1.1.0 RC2**, branch **`codex/resort-1.1-mcp`**.

**Atualização de 24/10/2026:** produtos presos às mãos animadas e sorvetes na geladeira, com otimizações de desempenho e atendente único; inclui as revisões anteriores.
[Download para Windows — produtos nas mãos e sorvetes](https://github.com/sergiomrge-tech/simulador-resort/releases/tag/v1.1.0-rc2.20261024-maos-sorvetes).
Extraia o ZIP inteiro e abra Jogar.vbs. Preserve userdata ao atualizar.

## Vai continuar o projeto com outra IA?

Comece por **[AGENTS.md](AGENTS.md)** e **[docs/CONTINUAR.md](docs/CONTINUAR.md)**.
O guia contém preferências atuais, mapa do código, recuperação de assets, testes
com saves separados, exportação e entrega. As lições técnicas estão em
[CLAUDE.md](CLAUDE.md) e as verificações anteriores em
[docs/VALIDACAO_1.1.0_LOCAL.md](docs/VALIDACAO_1.1.0_LOCAL.md).

Você pode enviar este pedido à próxima IA:

> Continue o Maré Alta Resort na branch codex/resort-1.1-mcp. Leia AGENTS.md e
> docs/CONTINUAR.md antes de alterar qualquer arquivo. Preserve as preferências
> atuais e os saves; implemente meu pedido, teste na fonte e no pacote exportado,
> atualize a documentação e faça commit + push das mudanças.

## O que está implementado

- Atendimento sem preparo: pegar produtos prontos e entregar aos clientes.
- Clientes pedem e retiram tudo no balcão antes de sentar; E anota/entrega por dentro.
- Geladeira e armário com exposição permanente; compras e estoque real separados
  das referências visuais, sem desconto duplicado ao devolver um item.
- Gestão no computador do balcão: nome/placa, horários, equipe, fornecedores e finanças.
- Quiosque começa fechado e exige abertura manual; porta da casa abre/fecha com E.
- Balcão com madeira escura/base cinza, copos e promoções nas duas faces.
- Cantos suaves de pássaros durante o dia perto das árvores, com áudio direcional.
- Casa detalhada, paleta mais natural no jogo inteiro e pessoas sem óculos escuros,
  chapéus ou bonés.
- Progressão do quiosque para resort, clima, vila, pousada e expansões.

## Abrir e testar

Abra `project.godot` no Godot 4.5.1 padrão (não .NET). Em um clone novo, recupere
os assets externos antes da importação: parte dos modelos e texturas é ignorada
pelo Git e **não é opcional para reproduzir o visual atual**. Siga o guia de
continuação; não aceite fallbacks/móveis ausentes como uma instalação completa.

Os testes usam `-- --loop-test` e flags específicas. Use dados de teste separados
conforme [docs/CONTINUAR.md](docs/CONTINUAR.md), sem alterar o progresso do jogador.
A versão Windows portátil abre com `Jogar.vbs` e guarda o progresso em `userdata/`.

Créditos: [CREDITS.md](CREDITS.md). Fontes artísticas: [art/blender/](art/blender/).
Histórico antigo: [docs/HISTORICO_CONTINUACAO_2026-10-19.md](docs/HISTORICO_CONTINUACAO_2026-10-19.md).
