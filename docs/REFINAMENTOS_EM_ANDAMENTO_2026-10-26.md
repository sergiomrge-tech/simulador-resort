# Checkpoint de refinamentos — 26/10/2026 (trabalho em andamento)

O usuário pediu encerrar agora por limite de uso e terminar depois. Este é um
checkpoint de código/assets, não uma nova versão jogável aprovada. Não declarar
as oito sugestões concluídas e não substituir o executável validado por este lote
antes das verificações abaixo. Base jogável anterior: commit 45fc277, release
v1.1.0-rc2.20261026-campanha-correcoes, celular/campanha no D:/Downloads.

## Pedidos atuais que precisam ser preservados

- Fazer as oito sugestões: atendimento natural; celular direto; rotinas na vila;
  preferências dos clientes; melhorias visíveis; campanha com conversas no mundo;
  áudio localizado; controles independentes de desempenho e FPS.
- Casa com decoração de praia e banheiro **claro com madeira e detalhes de praia**
  (escolha confirmada do usuário). Vaso, pia/espelho, box e porta.
- Aba **Missões** diretamente no celular. Agora são seis abas: Quiosque, Compras,
  Equipe, Finanças, Resort, Missões. Vila e lazer é atalho dentro de Missões.
- Reggae instrumental suave de fundo, referência de gênero Bob Marley; composição
  original, sem vozes, sem samples ou melodias de artistas.
- Mais detalhes dentro do quiosque. Manter entradas/balcão de trabalho livres.
- Sombras de contato nos objetos, com opção de reduzir custo nas configurações.
- Pedidos à esquerda somente com nome do cliente e itens restantes; sem números,
  localização e legenda adicional. Permanecer até entregar tudo. Missões separadas.
- Depois da areia, terreno de gramado verde natural. Preservar praia e pavimento.
- Imagem de pessoa atravessando espreguiçadeira: há sobreposição do conjunto
  decorativo BeachSet em (33,-22) com as mesas voltadas à praia. Movido para x82;
  é preciso conferir por imagem, não afirmar pose corrigida sem essa verificação.

## Código/assets iniciados

scripts/refinements.gd integra decoração inicial e três melhorias compráveis,
conversas em moradores existentes, distribuição de pedestres/vegetação/distância
configurável e FPS. Estado salvo em Prog.experience (decor/greeted), sem apagar
save antigo. Dialoga com a campanha existente; não cria campanha duplicada.

phone_ui.gd: início com abertura, resultado, atendente e estoque baixo; compras
com desenhos SVG por produto e reposição existente. Corrigida a largura do botão
criado vazio e preenchido depois: _refresh_kiosk_controls recalcula a largura.
Botões curtos (<3 caracteres) preservam largura pequena; não impor mínimo100 a
setas/controles curtos, pois estourava a página Bangalôs.

VillageLife: preferências refrescos/sorvetes/porções e nomes; fregueses conhecidos
mantêm favoritos/histórico. Rotinas de conversa/banco usam os mesmos pedestres.
VillageAnimal: pode seguir um pedestre por referência fraca, com obstáculos.
Guest: gesto temporário pedir/receber/agradecer usa IK existente; produtos mantêm
âncoras de mão e consumo/louça existentes. Ainda precisa revisão visual.

Quality/Menu: sombras, vegetação35–100%, detalhes50–150%, pedestres4–18 (padrão12),
FPS e volume Ambiente separados. Não foi medida melhora de FPS neste lote.
Sombras: bias do sol menor e uma luz de contato no quiosque. Revisão visual pendente.
Ground: transição ruído/smoothstep z=-12..-5 para textura leafy_grass; chuva continua
separada da espuma. Conferir sol/chuva e preservação dos caminhos por imagem.

Banheiro anexo a leste da casa, sem ocupar a sala: HomeBathroom, abertura na parede
leste, piso/paredes/teto, fixtures Blender, porta reutilizada com auto_close=false.
HomeDoor usa coordenadas locais para a porta girada do banheiro. A porta da casa
mantém nome PlayerHomeDoor e fechamento automático. Conferir passagem/colisões e
acessórios; fixtures ainda precisam de colisores individuais e revisão de escala.

Novos geradores/fontes CC0: gen_nautical_home.py (quatro .blend/GLB),
gen_product_icons.py (13 SVGs), gen_reggae.py (48s WAV estéreo original + folhas).
Modelos agrupados por material, texturas incorporadas, fontes reabertas pelo
próprio gerador. Godot extrai JPGs embutidos ao importar; não são downloads novos.
WAV usado porque soundfile/OGG encerrou o processo nesta instalação; não restaurar
o OGG de 4KB incompleto. _loop suporta WAV e define loop_mode/loop_end.

## Validação e pendências prioritárias

- Importação no Godot 4.5.1 executada, sem erros de importação.
- revision26 passou durante a implementação, inclusive entregas e pagamentos.
- phone-layout detectou overflow de Bangalôs ao mudar largura mínima global;
  restaurada regra de botões curtos, mantendo correção específica de abrir/fechar.
  Resultado final está no log checkpoint abaixo, quando disponível.
- Não há nova exportação/PCK/ZIP deste lote. O executável entregue anteriormente
  permanece o último aprovado; não afirmar que ele contém banheiro/gramado/reggae.

Próxima IA: ler este documento, AGENTS, CONTINUAR e CLAUDE. Verificar Git antes de
editar. Criar regressão refinements cobrindo: abrir/fechar botão após mudar texto;
aba Missões; compras; melhorias com cobrança única/save; conversas e recompensas;
preferências; banco/cachorro; qualidade/settings; áudio/pausa; pedidos só nomes/itens;
banheiro/porta/passagem; gramado/chuva; sobreposição mesas/BeachSet e sombras.
Inspecionar imagens reais de casa, banheiro, quiosque, clientes e gramado. Conferir
se os anexos não bloqueiam a cozinha/janelas. Revisar o painel de conversa ao
fechar/reabrir celular e o resultado financeiro do início (incluir investment).
Terminar ajustes antes de exportar, testar EXE/PCK em APPDATA isolado e entregar
nova pasta/ZIP no D. Não apagar userdata nem instalações anteriores. Medir tempo de
quadro se forem alegadas melhorias de desempenho. Atualizar catálogo e documentação
com resultados reais; commit/push e release somente após PCK aprovado.

Checagem de encerramento: PHONE_LAYOUT_TEST PASS em 1280×720, 800×600 e 360×640, saída0, sem ERROR/REAL_MISSING. Evidências em docs/qa/refinamentos-checkpoint-2026-10-26. revision26 foi executado antes dos últimos ajustes de decoração/gramado; repetir na retomada.
