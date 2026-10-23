# Casa decorada e cores neutras — 23/10/2026

A casa recebeu sofá de couro com madeira, mesa de centro de mármore, aparador,
TV de tubo, aparelho de som, estante com livros, relógio, planta e escultura de
madeira. São modelos detalhados Poly Haven CC0; fontes e licenças em CREDITS.md.
A mesa de refeições e a cadeira de balanço foram reposicionadas para liberar
a circulação da entrada até a cama e a cozinha. Os móveis novos têm colisão.

Mire na TV e pressione E para ligar/desligar uma animação silenciosa de mar.
Mire no som e pressione E para ligar/desligar a trilha suave existente. O volume
diminui com a distância; mute e volume de música continuam valendo. A trilha de
fundo é reduzida perto do aparelho para evitar duas músicas sobrepostas.
TV e som começam desligados; seu estado ligado não é salvo nesta revisão.

A luz ambiente deixou de usar a contribuição azul/lilás do céu. Paredes e móveis
recebem preenchimento neutro, preservando suas texturas e cores. O céu, o ciclo
do sol e a mudança de horário continuam existentes. Paredes da casa em tom claro
neutro e estante com pintura acinzentada, mantendo marcas e desgaste da madeira.

Implementação: scripts/home_furnishings.gd, scripts/world_village.gd,
scripts/daycycle.gd, scripts/audio.gd e shaders/home_tv.gdshader.
Download direcionado: tools/fetch_home_assets.py; conversão reproduzível:
tools/import_home_assets.py. Oito fontes art/blender/home_*.blend com texturas
incorporadas, salvas e reabertas; execução usa assets/models/gen/home_*.glb.

Teste --loop-test --home-test verifica caminhada física até cama/cozinha,
apoios de TV/som no aparador, bloqueio do sofá, mira/E, TV liga/desliga, mute,
bus Music e redução/restauração da trilha. Em Vulkan também captura interior de
dia/noite e tela da TV de perto. Usar dados isolados conforme CONTINUAR.md.
