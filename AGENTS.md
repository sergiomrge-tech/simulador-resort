# Instruções para qualquer IA que trabalhe neste repositório

Leia **[docs/CONTINUAR.md](docs/CONTINUAR.md)** antes de alterar o projeto.
Esse é o guia vigente, independente da ferramenta ou modelo utilizado.
Leia também **[CLAUDE.md](CLAUDE.md)** para as lições técnicas e erros anteriores;
o nome do arquivo não restringe seu uso à IA Claude.

## Prioridade das informações

1. Pedido atual do usuário.
2. Regras atuais em `docs/CONTINUAR.md` e neste arquivo.
3. Lições técnicas de `CLAUDE.md` e documentação do recurso afetado.
4. Documentos históricos, que não são uma lista de tarefas atuais.

## Preferências que devem continuar valendo

- Responder em português do Brasil e implementar os pedidos, validando o resultado.
- Continuar a linha **1.1.0 RC2**, branch `codex/resort-1.1-mcp`; verificar o Git
  antes de trabalhar. Não substituir por uma versão 1.0.x de instruções antigas.
- **Sem preparo:** pegar produtos prontos na geladeira/armário/cozinha e entregar.
  Sem botão Preparar, cronômetro ou exigência de cozinheiro. Compras abastecem;
  retirada desconta uma vez. Devolução e migração não duplicam cobranças.
- **Balcão antes de sentar:** no modo físico clientes pedem/retiram todos os itens
  no balcão e só depois vão à mesa. Garçom também atende no balcão. Reservar mesas,
  manter fila e liberar retirada ao sair. Não restaurar pedidos sentados.
- **Gestão no celular portátil**, aberto com B em qualquer lugar. Sem PC no balcão. Seis áreas compactas,
  cantos arredondados. Estações mantêm retirada/reposição direta. Quiosque começa
  fechado, exige Abrir quiosque e volta a fechar ao dormir. Saves preservados.
- **Balcão: madeira escura e base cinza**, independente da pintura da empresa.
  Seis copos na bandeja, sem caixa branca, promoções com preços reais frente/verso.
- **Porta da casa funcional:** E abre/fecha; fecha após sair com o arco livre.
- **Cores naturais em tudo**, com texturas preservadas; porta da casa em madeira.
  Não restaurar saturação exagerada nem iluminação artificialmente alaranjada/azul.
  Ambiente usa cor neutra, sem contribuição azul do céu nas superfícies.
- Pessoas **sem óculos escuros, chapéus ou bonés**. Preservar roupa/cabelo animados.
- Equipamentos sempre visíveis no quiosque, inclusive antes de criar empresa;
  expositores preenchidos no estoque zero, sem vender a referência visual.
- Tudo usado no atendimento fica dentro do quiosque; manter as duas entradas.
- Quiosque e mesas ficam voltados para a praia (-Z). Anotar/entregar aos dois
  lugares do balcão por dentro, com mira tolerante. Não voltar a exigir sair.
- Quando acaba um produto, oferecer reposição na própria geladeira/armário pelo
  painel da estação, com preço real dos insumos faltantes e sem cobrança parcial.
- Modelos detalhados, assets licenciados/CC0 ou fontes Blender editáveis. Não trocar
  por low poly ou primitivas usadas como objetos finais. Registrar origem/licença.
- HUD/gestão compactos, sem opções duplicadas; interação na parte inferior da tela.
- Música/efeitos suaves e sem vozes de fundo.
- Pássaros diurnos suaves perto das árvores, com intervalos e atenuação; silêncio
  à noite/chuva e respeito à pausa e volume SFX. Preservar gaivotas e grilos.
- No mar: um navio de madeira com velas por vez, passando bem devagar; cruzeiro
  parado à noite. Baleias saltam ao fundo com efeitos na água; céu com nuvens.
  Usuário rejeitou a prévia do cruzeiro low poly Quaternius por ser simples;
  manter cabines, varandas, botes e detalhes legíveis na câmera da praia.

## Forma de trabalhar

- Não apagar/resetar alterações de outra pessoa/IA. Se houver trabalho concorrente,
  coordenar com o usuário; não sobrescrever os mesmos arquivos silenciosamente.
- Não apagar saves, `userdata/`, configurações do jogador ou a instalação antiga.
  Testes precisam de diretório de dados separado. Veja os exemplos no guia.
- Preferir ferramentas Godot/Blender conectadas quando disponíveis. Outra IA pode
  usar editor/CLI equivalentes; não depender da memória ou das ferramentas deste chat.
- Rodar testes afetados e conferir logs e imagens. PASS lógico não substitui
  inspeção visual e não torna aceitável erro de script ou recurso ausente.
- Testar o executável/PCK exportado antes de entregar um download.
- Atualizar documentação e catálogo quando necessário; fazer commit + push de cada
  lote concluído. Não incluir saves, credenciais, cache ou builds enormes no Git.
- Não declarar trabalho testado, enviado ou concluído sem verificar o resultado.

Consolidação de 23/10/2026. Novos pedidos explícitos do usuário podem alterar
estas preferências; registre a mudança para a próxima IA.

## Revisão visual e gestão de 23/10/2026

Leia [REFINAMENTO_2026-10-23.md](docs/REFINAMENTO_2026-10-23.md) para a revisão
mais recente.
PC usa Classic Laptop CC0; não voltar ao caixa azul/modelo de seis quadrados.
Gestão com seis abas compactas; compras abre em produtos com reposição imediata
para 10, custo dos insumos faltantes. Formulário de fornecedor é secundário.
Não voltar a permitir botões estreitos que esticam os cartões de equipe.
Animais mantêm rigs/animações e rostos refinados; não regenerar pelos antigos
smooth_animals.py que removiam o rig. Pedestres mantêm 12 HD/5 baixa; chegadas
em casas projetadas fora dos bloqueios com margem para o corpo.

## Pedido de 24/10 — louça e balcão

Louça deve corresponder ao que foi consumido: suco → copo vazio; coco → coco aberto;
comida → prato/tigela vazios. Preservar lista por lugar no save e limpar junto dos
objetos. Sem PC no balcão (pedido de 26/10); copos à esquerda e promoções à direita. Downloads/builds no
drive D, pois C ficou cheio. Guia: [docs/LOUCA_BALCAO_2026-10-24.md](docs/LOUCA_BALCAO_2026-10-24.md).

## Pedido de 24/10 — desempenho e atendente único

Somente **um atendente** faz todo o atendimento do quiosque: anotar, retirar pronto,
entregar no balcão com pagamento automático e recolher louça. Substitui cargos separados
(garçom/caixa/limpeza/cozinheiro) no quiosque, preservando migração e histórico.
Cargos de pousada/bar/passeios continuam separados. Não reabrir contratação de
quatro cargos por seguir documentos antigos. Detalhes, métricas e validação em
[docs/DESEMPENHO_ATENDENTE_2026-10-24.md](docs/DESEMPENHO_ATENDENTE_2026-10-24.md).

## Pedido de 24/10 — produtos nas mãos e sorvetes

Produtos transportados acompanham as mãos animadas, inclusive o atendente. Pedidos maiores usam bandeja com apoio dos braços. Sorvetes de morango/chocolate são produtos prontos da geladeira, com reposição direta e pote vazio após consumo. Preservar o único atendente, sem preparo. Guia: [docs/MAOS_SORVETES_2026-10-24.md](docs/MAOS_SORVETES_2026-10-24.md).

## Pedidos de 26/10 — campanha, HUD e operação

Pagamento automático ao entregar cada produto: cliente pega e já paga. Não
restaurar recebimento manual nem caminhada do atendente ao PC para cobrar.
PC excluído por pedido final do usuário; gestão volta ao celular portátil com B,
formato vertical e seis abas compactas. Isso substitui os pedidos de mover para a
lateral e de reduzir alcance. Não deixar PC nem alvo invisível no balcão.
Clientes continuam com mira tolerante e atendimento pelo lado interno.
Pedidos e missões fixos à esquerda, inclusive nas estações; pedidos ficam até
entregar todos os itens. Estações compactas, sem seis abas de gestão duplicadas.
Campanha principal e secundárias persistem e recompensas não repetem.
Porções de batata frita e peixe prontas no armário, com estoque/reposição como coco.
Nunca colocar volume sólido de oclusão no interior acessível da casa.
Navio diurno mais ao fundo (-220 Z), um por vez e lento; cruzeiro noturno ancorado.
Guia atual: [docs/CAMPANHA_CORRECOES_2026-10-26.md](docs/CAMPANHA_CORRECOES_2026-10-26.md).

Chuva deve umedecer a areia sem criar faixas brancas; espuma depende somente da orla. Botões e cartões ajustam-se ao conteúdo, sem faixas verdes esticadas.


## Checkpoint de refinamentos de 26/10 (em andamento)

Usuário pediu encerrar e terminar depois por limite. Ler [docs/REFINAMENTOS_EM_ANDAMENTO_2026-10-26.md](docs/REFINAMENTOS_EM_ANDAMENTO_2026-10-26.md) antes de retomar. Não declarar este lote concluído nem substituir o PCK aprovado antes de validar. Preferências novas: aba Missões direta, pedidos apenas nome/itens, gramado após areia, reggae instrumental suave original, banheiro claro/madeira/praia e mais detalhes/sombras no quiosque.


## Entrega de 27/10 — refinamentos concluídos

O checkpoint em andamento de 26/10 foi retomado. Guia atual: [docs/REFINAMENTOS_2026-10-27.md](docs/REFINAMENTOS_2026-10-27.md). Missões é aba direta; pedidos mostram apenas nome e itens restantes. Banheiro fica atrás/norte da casa, evitando o vizinho a leste. Preservar decoração comprada em Prog.experience, reggae original, gramado depois da areia e controles independentes de qualidade. Os limites de pedestres são configuráveis, padrão 12 HD/5 baixa. Ambiente passa por SFX e possui volume próprio.

## Migração UE5.8 solicitada em 27/10

O usuário mudou o motor de destino para Unreal Engine5.8 e pediu **realista
estilizado**, sem cartoon. A migração está na branch `codex/ue58-migration`;
leia [docs/ue58/MIGRACAO.md](docs/ue58/MIGRACAO.md). Use MCP nativo da UE disponível.
Preserve a entrega Godot e saves. Não declarar o port concluído antes de validar
mecânicas, imagens reais e executável exportado.


Checkpoint UE anterior (histórico): [docs/ue58/CHECKPOINT_2026-10-27.md](docs/ue58/CHECKPOINT_2026-10-27.md). O bloqueio de navegação foi corrigido no guia posterior; não declarar a migração integral finalizada.


## Continuação UE5.8 — cenário e atendimento

Guia atual: [Cenário completo e atendimento nativo](docs/ue58/NAVEGACAO_ATENDIMENTO_2026-10-27.md). São 1.620 modelos, 12.910 instâncias e zero modelos ausentes. O bloqueio de navegação em Z910 foi corrigido. A migração integral e a aprovação visual continuam pendentes; a versão Godot aprovada permanece preservada.


## Continuação UE5.8 — persistência nativa

Guia atual: [Saves e continuidade do atendimento](docs/ue58/PERSISTENCIA_2026-10-27.md). Clientes, pedidos parciais, transporte, louça, reservas, jogador e portas são reconstruídos nos saves UE. Preservar a transação atômica entre atendimento e economia, o marcador de consumo e os campos desconhecidos. A conversão integral e o executável UE aprovado continuam pendentes.


## Prévia UE5.8 — áudio, visual e natação de 28/10

Guia vigente: [docs/ue58/AUDIO_VISUAL_2026-10-28.md](docs/ue58/AUDIO_VISUAL_2026-10-28.md). Branch `codex/ue58-migration`, projeto no D. Há prévia Windows exportada e testada; isso não conclui a migração inteira. Preservar áudio sem vozes, volumes independentes, 114 letreiros nativos, horário de atendimento explicado no celular, natação e perfil separado. A versão Godot e seus saves continuam preservados.
