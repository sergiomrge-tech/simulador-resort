# Apresentação dos pedidos — RC3

O ID de Economy.DISHES é a fonte única para preço, preparo e aparência. A apresentação só nasce quando um item é entregue e permanece vinculada ao cliente e ao assento reservado. Pedidos múltiplos/repetidos mantêm cada unidade; saída, fechamento e troca de dia removem os objetos. A preparação tem um objeto próprio no balcão. Não existem pratos prontos permanentes nas mesas do quiosque.

| ID | Modelo | Categoria |
|---|---|---|
| coco_gelado | coconut_open | bebida |
| suco | glass_juice | bebida |
| caipirinha | cocktail | bebida |
| batida | dish_batida | bebida |
| petiscos | dish_petiscos + plate-dinner + utensil-fork | comida |
| tapioca | dish_tapioca + plate-dinner + utensil-fork | comida |
| pastel | dish_pastel + plate-dinner + utensil-fork | comida |
| acai | dish_acai + plate-deep + utensil-spoon | comida |
| moqueca | dish_moqueca + plate-deep + utensil-spoon | comida |

Louça e talheres: Kenney Food Kit (CC0), https://kenney.nl/assets/food-kit . Os novos recheios são originais e reproduzíveis com `tools/gen_dishes.py` (Blender/bpy 4.5.14). Sementes de distribuição fixas; os modelos são gerados como GLB antes da importação Godot. `tools/build_patch.sh` inclui explicitamente esses GLBs e a louça na atualização cumulativa.

Validação funcional: Godot 4.5.1 `--headless --path . -- --loop-test --order-visual-test --quality=0`. As capturas com `--orders-demo` executam o fluxo real de entrega, preservando contagem e consumo de estoque; não são mockups. Os testes existentes de assentos e do ciclo completo continuam obrigatórios. Renderização e instalação no Windows real exigem verificação no dispositivo.
