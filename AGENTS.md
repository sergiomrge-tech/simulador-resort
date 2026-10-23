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
- **Gestão no computador do balcão**, com E; B somente perto. Seis áreas compactas,
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
