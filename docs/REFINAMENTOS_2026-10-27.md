# Refinamentos concluídos — 27/10/2026

Linha 1.1.0 RC2, branch codex/resort-1.1-mcp, Godot 4.5.1.
Este guia substitui o checkpoint em andamento de 26/10. Preservar as preferências
mais recentes em AGENTS.md; documentos de PC/preparo são históricos.

## Resultado e uso

- B abre celular vertical em qualquer lugar. Seis abas: Quiosque, Compras, Equipe,
  Finanças, Resort, **Missões**. Vila/fotos/lazer ficam acessíveis por Missões.
- Início: abrir/fechar, resultado real do dia (inclui investimentos/contratações),
  atendente e alerta de estoque baixo. Botão abrir/fechar recalcula largura ao mudar
  texto; não volta à coluna vertical nem estica cartão. Compras têm imagens SVG
  por produto, disponibilidade, custo e reposição imediata até dez.
- HUD de pedidos mostra **somente nome e itens restantes**, fixos à esquerda até
  última entrega. A página Pedidos segue o mesmo formato. Missões são separadas.
- Clientes têm nomes distinguíveis e preferências por refrescos, sorvetes ou
  porções; fregueses conhecidos preservam favoritos e histórico de visitas.
  Gestos temporários de pedir/receber/agradecer usam IK, olhar existente e mãos
  animadas; não soltar produtos da âncora. Consumo/louça correspondentes preservados.
- Os mesmos pedestres caminham, conversam, descansam em bancos livres e entram
  em casa à noite. Aproximação do banco precede alinhamento da pose; não sentar
  sobre outro NPC. Cachorro existente pode acompanhar morador com rota livre.
- E nos moradores apresenta conversa curta com contexto/objetivo da campanha;
  o morador responsável permite concluir a etapa já cumprida. Aba Missões mantém
  as dez etapas principais e quatro secundárias, sem duplicar recompensas.
- Interior do quiosque: quadro náutico em madeira/corda, conchas e cerâmicas.
  Em Quiosque > Decoração e nome, três melhorias visíveis: floreiras R$90,
  cordão de luzes R$120 e expositor artesanal R$150. Cobrança única, estado salvo.
  Luzes decorativas acendem ao anoitecer e não projetam sombras extras.
- Casa tem decoração de praia e banheiro claro com madeira, vaso, pia/torneira,
  espelho, sabonetes, toalha e box de vidro incolor com chuveiro/ralo. E abre/fecha
  a porta. Anexo fica **atrás/norte da casa**, ligado por abertura perto da cozinha;
  a tentativa inicial a leste colidia com o vizinho e foi corrigida. Piso/paredes,
  bancada, vaso e vidro têm colisões; vegetação não invade o ambiente.
- Espreguiçadeiras decorativas antes sobrepostas às cadeiras do quiosque foram
  afastadas para x82. Clientes permanecem nas cadeiras corretas para consumir.
- Após a areia existe gramado verde com textura/variação suave, sem cobrir ruas
  de pedra. Chuva escurece o gramado/areia; espuma continua restrita à orla.
- Sombras: menor bias para contato, luz interna do quiosque e banheiro com sombra;
  controle independente em Configurações. Mantidas cores naturais/ambiente neutro.
- Reggae instrumental suave **original** de 48 segundos, em loop, sem vozes ou
  samples de artistas. Folhas localizadas nas árvores; pássaros/ondas/gaivotas/
  grilos preservados. Música, SFX e Ambiente têm volumes separados. Ambiente
  passa por SFX para respeitar também o volume geral de efeitos e a pausa dos pássaros.
- Configurações: sombras independentes; densidade de vegetação 35–100%, distância
  dos detalhes 50–150%, pedestres 4–18 (padrão 12 HD/5 baixa), FPS/tempo de quadro.
  Opções afetam cenário real e persistem em settings; não apagam configurações antigas.

## Implementação e assets

scripts/refinements.gd integra visual, diálogos e qualidade. Progresso adicional
em Prog.experience.decor/greeted, serializado com o save e com defaults para saves
antigos. Não reintroduzir PC, preparo, recebimento manual ou pedidos sentados.
As duas entradas e estações internas do quiosque continuam livres.

Modelos originais CC0: tools/gen_nautical_home.py, fontes .blend portáveis, GLB
embutido e agrupado por material para poucas chamadas de desenho. SVGs originais:
tools/gen_product_icons.py. Áudio original: tools/gen_reggae.py. Registros em CREDITS.
Espelho tem acabamento metálico, sem reflexo de câmera em tempo real; pia/chuveiro
são mobiliário decorativo, sem nova necessidade de higiene do personagem.

## Validação

Testes com APPDATA separado, nunca em userdata real. Teste refinements verifica
botão após mudar texto, seis abas/Missões, imagens de produtos, custos e persistência
das melhorias, conversa/recompensa única, perfis/nomes, rotina de conversa/banco,
cachorro, áudio/loop/buses, controles reais/settings/FPS, porta via mira/E, passagem
física ao banheiro e HUD só com nomes/itens. Capturas de banheiro, casa, quiosque,
gramado seco/molhado, conversa e cliente sentado, com inspeção visual.

Suíte afetada: refinements, home, phone-layout, revision26, birds, company,
counter-first, held-order, tableware, optimization. Executável exportado também
exercita management, practical e coastal. Logs/hash finais em
qa/refinamentos-2026-10-27/validacao.json.

Medição fonte na RTX 4060 Ti, Vulkan, 1280×720, preset Médio: quiosque 96,7FPS
(10,32ms médio, p95 15,65ms), vila 107,5FPS (9,29ms, p95 14,84ms), praia 142,5FPS
(7,01ms, p95 11,44ms). Três cenas de 8 s após 3 s de aquecimento. Resultado desta
execução, sem alegar ganho percentual ou garantir FPS em outras resoluções.

## Entrega

Novo pacote/pasta no drive D. Preserve userdata ao atualizar; não substitua ou
apague instalações anteriores. Na retomada futura, verificar Git/branch antes de
editar. A release de 27/10 inclui as versões anteriores; não usar o checkpoint WIP
como instrução para refazer alterações já concluídas.


Validação final: 13 regressões distintas no executável; cinco reforçadas após
revisão da mira/HUD, e refinements/revision26 repetidas no PCK final após corrigir
expiração de rotinas ao dormir. Sem teleporte de volta ao banco. Onze verificações
na fonte (inclui benchmark). Encerramento0, sem ERROR/REAL_MISSING. Hash de cada
rodada em validacao.json.

PCK final SHA256: `8256611f0885e90cb489ff500345a8de03809b7c753fbe92a67344ba7da9383f` (1820044456 bytes).
