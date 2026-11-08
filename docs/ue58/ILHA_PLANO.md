# Ilha completa: plano (08/11/2026)

Pedido do Sergio (06/11, checklist item 7): "morro no meio, praia em volta, uma ilha pequena, preservando a vila e
todas as construções, o restante é vegetação e árvores". Pedido de 08/11: "avance no jogo, faça a ilha completa".

## Como o mapa é hoje (levantamento de `mare_island.survey`, 05/11)

- **Terreno da vila (`World_0000`):** x −130…+130 m e y −60…+110 m. Os preenchimentos costeiros W e E vão até x −196
  e +221 m.
- **Morros do cume:** são as peças `World_0601…0670`, de y 85 a 430 m e com até 146 m de altura. O lado norte termina
  num paredão, sem nada atrás.
- **Mar (`Ocean`) e volume de natação:** cobrem só o sul (y < +88 m). A ilha vulcânica fica longe, a sudoeste
  (y −1300 m).
- **Linha da praia é uma reta, y = −54,5 m, usada em todo lugar:**
  - fundo do mar (`reef.json` → `floor_fill.profile`, `UMareReefWorld::SeabedZ(Y)`);
  - planos de areia (`mare_water.ensure_seabed`);
  - ondas e espuma do material do mar (`mare_materials.build_water`, termos `Position.y`);
  - `AMarePerson::SeaHeight`;
  - nado e recuperação de queda (`MareGame.cpp` 1106/1111);
  - corais do fundo (`FillFloor`).
- **Navegação estática:** só cobre o quiosque, a casa e a vila (volume `5000,1800 ± 6500,6000`).

## Forma da ilha

- **Praia sul:** fica como está (quiosque, píer, recife, snorkel e passeio de barco não mudam).
- **Contorno:** uma linha fechada e orgânica que abraça a vila, os preenchimentos W/E e o maciço do cume. Tamanho
  aproximado: x −230…+260 m e y −55…+500 m.
- **Morro no meio:** é o maciço do cume que já existe, com a trilha e a casa do velho. O lado norte, hoje paredão,
  ganha encosta descendo até uma praia nova.
- **Lados W, E e N:** praias novas de 30–50 m de largura, com coqueiros na beira e mata subindo o morro.
- **Fonte única:** `Content/Data/island.json`, com os pontos do contorno (cm do mundo) e as larguras de praia por trecho.

## Peças

1. **Campo de distância da costa (base de tudo).**
   - `tools/ue58/gen_island_sdf.py` (numpy) lê o contorno e grava a distância com sinal até a costa (negativa em terra):
     - `T_IslandSDF`, 1024², cerca de 1,3 m por pixel, usado pelo material do mar;
     - `island_sdf.bin`, a mesma grade, usado pelo C++.
   - C++: `UMareIsland::ShoreDistance(X,Y)`, com amostragem bilinear.
   - Teste automático: o C++ e o material dão o mesmo valor em pontos conhecidos; a praia sul atual dá ~0 em y −54,5 m.
2. **Fundo do mar radial.**
   - `SeabedZ(X,Y)` = perfil atual aplicado à distância da costa, não a y. Na praia sul o resultado é idêntico ao de hoje.
   - O recife continua no mesmo lugar.
   - Os planos de areia viram uma malha em anel gerada no bpy a partir do SDF.
   - `FillFloor` percorre o anel inteiro.
3. **Mar.**
   - O plano `Ocean` e o volume de natação passam a cobrir os quatro lados.
   - No material, `shore`, `offshoreWaves`, `coast`, a cor rasa/funda e a espuma passam a usar o SDF. As ondas
     continuam iguais na praia sul.
   - `SeaHeight` muda junto (regra: as duas fórmulas sempre juntas).
4. **Terreno novo (bpy).**
   - Uma "saia" em volta do que existe, sem tocar no terreno da vila nem nos morros: a borda costura nas alturas atuais
     (amostradas com `mare_island.heights`).
   - Desce pela areia até o fundo do perfil e, ao norte, sobe a encosta até encontrar o paredão.
   - Materiais: areia da praia atual e grama/terra dos morros. Colisão de verdade (NavCollision sem hulls convexos,
     lição de 28/10).
5. **Vegetação e acabamento.**
   - Coqueiros na beira, mata tropical na encosta, pedras costeiras nas pontas. Tudo com os assets que já temos
     (palms, amendoeiras, fern, `coast_rocks_*`), em HISM gerado no editor e com culling.
   - Nada de flor na areia (lição de 07/11). Nada de capim marinho no raso.
6. **Ajustes no código.**
   - Nado, recuperação de queda (`Ground` pela distância), gaivotas (`Position.Y<-500`), som do mar (`Beach` pela
     distância) e o vento no quiosque (`CoastGround`, y > −1050).
   - O passeio de barco e o snorkel continuam no sul.
7. **Navegação.**
   - Os NPCs não andam nas praias novas na primeira versão, então o volume não muda e não é preciso refazer.
   - Se mudar: reconstruir com o PIE parado, conferir e só então salvar (lição de 03/11).
8. **QA.**
   - Checagens novas no portão:
     - traços em anel em volta da ilha batem em terra ou em água, sem buraco nem paredão;
     - fundo dentro do perfil;
     - SDF do C++ igual ao do material;
     - a praia sul sem mudança: ondas, nado e recife medidos antes e depois.
   - Fotos aéreas dos 4 lados, de dia e no pôr do sol, mais uma de perto de cada praia nova.

## Ordem

Faço uma peça por vez, cada uma com portão PASS e foto:

1. contorno + SDF;
2. fundo radial;
3. mar;
4. terreno;
5. vegetação;
6. código;
7. fotos.

Estimativa: 2 a 3 dias de trabalho.

## Riscos conhecidos

- O WPO do mar com amostragem de textura no vértice. Funciona na UE, mas precisa conferir a Nanite no plano do mar.
- O paredão norte do cume: a costura entre a encosta nova e as peças antigas pode deixar frestas. Conferir de perto.
- Tamanho do pacote: o SDF tem ~2 MB, e o terreno novo deve ficar abaixo de 30 MB.
