# Produtos nas mãos e sorvetes — 24/10/2026

Linha 1.1.0 RC2, Godot 4.5.1, branch codex/resort-1.1-mcp.

## Transporte

Clientes e o atendente usam o mesmo transporte vinculado a hand_r por
BoneAttachment3D. A apresentação é sincronizada depois das modificações do
esqueleto, mantendo os produtos em pé durante animação, caminhada e curvas.
Um copo/coco/pote fica na mão; pedidos mistos e pratos usam bandeja de madeira,
com os dois braços apoiando suas bordas. Ao sentar, sair ou cancelar, remover
âncora, produtos e metadados sem alterar estoque ou pagamentos.

Durante o consumo o recipiente também acompanha a mão, em escala coerente com
o produto servido. Não voltar a usar a posição fixa no peito que fazia os
produtos flutuarem. Não consultar poses fora do ciclo do SkeletonModifier para
validar a pose renderizada: a engine restaura os valores de animação depois dos
modificadores. Conferir capturas e a âncora atualizada.

## Sorvetes

- Sorvete de morango: R$ 12; unidade pronta custa R$ 4.
- Sorvete de chocolate: R$ 14; unidade pronta custa R$ 5.
- Disponíveis desde o início, seis unidades de cada no estoque inicial.
- Retirada pronta e Repor 10 na geladeira; compra usa cotação real, saldo e regras
  de contrato existentes. Sem preparo, taxa ou ingrediente extra ao entregar.
- Dois insumos/unidades independentes; devolução retorna uma unidade já paga.
- Pote vazio com colher após consumir, preservado no registro de louça/save.
- is_chilled é a classificação da estação; is_drink continua descrevendo a
  animação. Sorvete não deve usar animação de beber ou aparecer no armário.

Modelos originais CC0, fontes art/blender/icecream_*.blend,
used_icecream_cup.blend e service_carry_tray.blend. Gerador tools/gen_icecream.py.
Fontes foram salvas e reabertas; não dependem de texturas externas.

## Validação

Regressões afetadas: held-order, counter-first, company, practical, order-visual
e tableware. APPDATA separado. O teste held-order verifica sincronismo a cada
quadro, durante giro/deslocamento com animação de caminhada; estoque, reposição,
devolução, save e recipiente usado. Conferir os logs e capturas na pasta
qa/maos-sorvetes-2026-10-24, inclusive no executável/PCK exportado.

O antigo teste order-visual ainda exigia preparo e pedido sentado. Foi atualizado
para conferir catálogo completo, apoio nas mesas, itens distintos e isolamento
entre pedidos; counter-first/company cobrem a retirada real antes de sentar.

Pacote: D:/Downloads/MareAltaResort_1.1_RC2_Maos_Sorvetes_2026-10-24.zip.
Preservar userdata/ ao atualizar. Release:
https://github.com/sergiomrge-tech/simulador-resort/releases/tag/v1.1.0-rc2.20261024-maos-sorvetes

Resultado final: as seis regressões passaram na fonte e no executável/PCK, com saída 0 e sem erros de script/recursos ausentes. Capturas do executável inspecionadas: pote na mão, bandeja apoiada e consumo. Hash do PCK e registros em [validacao.json](qa/maos-sorvetes-2026-10-24/validacao.json).
