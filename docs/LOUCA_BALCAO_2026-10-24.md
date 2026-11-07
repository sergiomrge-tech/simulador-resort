# Louça correspondente e PC central — 24/10/2026

Linha 1.1.0 RC2, branch codex/resort-1.1-mcp, Godot 4.5.1.

- Suco deixa o mesmo copo vazio, com canudo, sem líquido, gelo nem fruta.
- Coco gelado deixa o coco aberto com canudo, sem prato genérico.
- Caipirinha deixa a taça vazia; batida deixa o copo vazio. A taça mantém a escala
  do recipiente servido, mesmo após retirar a sombrinha e o enfeite da bebida.
- Petiscos/tapioca/pastel deixam prato vazio e garfo; açaí/moqueca deixam tigela
  vazia e colher. Os modelos de cerâmica não contêm comida no próprio asset.
- Pedidos mistos deixam um recipiente por item, inclusive itens repetidos.
- company.dirty_items guarda a lista consumida por lugar, com chaves de texto.
  O registro é validado ao carregar e removido junto da limpeza. Sem nova cobrança
  ou desconto de estoque. Save antigo sem lista continua válido, com prato vazio
  de compatibilidade: não é possível recuperar o produto que não foi registrado.
- PC no centro do balcão (X local zero), bandeja/seis copos à esquerda e promoções
  à direita. Área de interação interna fica antes da área genérica do balcão para
  E alcançar o PC central. Do lado dos clientes, o balcão continua acessível.
  B continua restrito à proximidade e ao lado de dentro.

Fontes editáveis empacotadas e reabertas: art/blender/used_glass_juice.blend,
used_cocktail.blend, used_dish_batida.blend, table_plate.blend e table_bowl.blend.
Derivações de modelos autorais existentes; gerador tools/gen_used_drinks.py,
registrado em fetch_assets.py. Cerâmica autoral com perfil torneado detalhado.
O mesmo prato/tigela vazio é a base dos alimentos servidos, evitando a comida
embutida no antigo modelo Kenney plate-dinner.

Teste --loop-test --tableware-test: nove produtos, saída do cliente, louça mista,
limpeza, save/load real, estoque/saldo preservados, migração antiga e mira do PC
central por dentro/fora. Complementar com terminal/company/counter-first/counter.
Usar APPDATA de teste separado e repetir no PCK antes de entregar. Logs/capturas
finais ficam em docs/qa/louca-balcao-2026-10-24.

Distribuição pelo drive D: tools/package_quiosque_portable.py --variant louca.
ZIP MareAltaResort_1.1_RC2_Louca_Balcao_2026-10-24.zip em D:/Downloads.
O diretório gerado build/rc2-playable é uma junção para
D:/CodexTemp/resort-build/rc2-playable nesta máquina; evita exportar builds grandes
no C cheio. Não mover nem apagar saves/instalações do jogador.


## Resultado

Tableware, terminal, company, counter-first e counter passaram na fonte e no
executável exportado, com saída 0 e sem erros nos logs finais. Inspecionadas as
capturas do PCK: mesa com copo vazio/coco/prato vazio e balcão com PC central,
sem bandeja atravessando as frutas. Recipientes Blender reabertos pelo gerador.
Frutas ficam agora sobre a bancada lateral, liberando a frente do balcão.

Download: https://github.com/sergiomrge-tech/simulador-resort/releases/tag/v1.1.0-rc2.20261024-louca-balcao .
