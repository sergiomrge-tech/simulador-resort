# Campanha, operação e correções — 26/10/2026

Linha 1.1.0 RC2, Godot 4.5.1, branch codex/resort-1.1-mcp.
Este documento prevalece sobre instruções antigas de gestão no PC e recebimento manual no caixa. O pedido final é excluir o PC e usar celular portátil.

## Pedidos consolidados

1. Casa: removido o volume sólido de oclusão legado em _hero_house. Ele preenchia
   o interior e escondia paredes/móveis através das janelas quando culling estava
   ligado. A mesma câmera foi comparada com culling ligado/desligado, além de
   inspeção do interior. Oclusores de casas opacas da vila continuam funcionando.
2. Navio de madeira: rota em Z=-220, cerca de 190 m além da faixa da praia; mantém
   velocidade 0,5 m/s, um navio por vez e modelos detalhados. Cruzeiro noturno
   continua ancorado, sem esteira/deslocamento.
3. Gestão no celular portátil: notebook, alvo físico e SubViewport do PC foram
   removidos. B abre em qualquer lugar. Formato vertical com seis abas numa grade
   3×2, cantos arredondados e cartões compactos. Pedidos finais do usuário para
   EXCLUIR o PC e voltar ao celular substituem pedidos anteriores de mover o PC
   à lateral ou ajustar seu alcance. Nenhum alvo invisível continua no balcão.
4. Clientes: alcance tolerante até a abordagem interna, nos dois lugares. Mira
   considera cabeça acima do tampo e mantém teste de linha de visão. Nenhuma
   parede ou colisão foi removida. Número vem de dining_spot (reserva), sem #00.
5. HUD: missões principal/secundária à esquerda, abaixo de dinheiro/horário;
   pedidos fixos abaixo até a entrega de todos os itens, inclusive longe do
   quiosque ou com a estação aberta. Estado de cada pedido usa itens restantes.
   Tela de estação compacta à direita; uma linha por produto e botão curto Pegar,
   ou Repor 10 quando necessário. Navegação da gestão fica no celular.
6. Pagamento: cada entrega recebe o valor real imediatamente, inclusive pelo
   atendente. Retirada desconta insumos uma vez, entrega não desconta de novo.
   Não é preciso receber no caixa/PC; removido alvo invisível antigo do caixa.
   Contas de saves antigos são liquidadas na carga, limpando a lista antes do
   crédito; salvar/recarregar não repete dinheiro nem registro de vendas.
7. Porções: batata frita (R$ 16) e peixe (R$ 28) disponíveis desde o início no
   armário. Insumos são unidades prontas separadas (base R$ 4/R$ 8); seis porções
   iniciais de cada. Retirada, devolução e reposição direta usam a mesma lógica
   dos demais produtos, sem preparo/cozinheiro. Depois deixam prato vazio.
8. Vila: pavimento contínuo nas ruas e passeios no trecho antes vazio atrás das
   casas, respeitando feira/igreja; bancos, vasos e postes nas laterais. Sem novos
   pedestres ou sombras dinâmicas adicionais; modelos existentes reaproveitados.
9. Chuva: umidade e espuma marítima são calculadas separadamente. A chuva não
   alimenta o limiar de espuma, que gerava faixas brancas por todo o terreno.
   Removido smoothstep com limites invertidos; areia molhada escurece com brilho
   moderado. Comparação visual sol/chuva e teste da proporção de branco no chão.
10. Botões: largura acompanha texto/margens em todos os botões genéricos. Não
    esticar Concluir/Pegar para a largura do cartão. A largura do celular e o
    espaçamento menor dos cartões evitam grandes vazios laterais.

## Campanha Uma nova maré

Dez etapas sequenciais: criar empresa, abrir, vender oito produtos, comprar mesas,
contratar o atendente, ajudar Seu Zé no píer, abrir o bar, abrir a pousada, construir
piscina e concluir o Grand Hotel. Cada etapa tem contexto, objetivo, progresso e
prêmio. Concluir em Celular (B) → Vila e lazer → Missões; é preciso reivindicar a
etapa concluída para avançar. Condições existentes em saves antigos são reconhecidas.

Quatro secundárias independentes: pescar cinco peixes, vender doze sorvetes,
fotografar o farol e fotografar o pôr do sol. Continuam disponíveis as encomendas
dos moradores e as quatro histórias da vila (píer, prainha, sabores e carnaval).

Dados em scripts/campaign.gd e prog.campaign, dentro do save existente. Consulta
pelo HUD não produz efeitos; recompensas marcam etapa/ID antes de creditar e
salvam. IDs antigos/duplo clique não repetem prêmio. Save antigo inicializa o
bloco novo sem apagar empresa, estoque, personagem ou progresso de outras áreas.
A regressão exercita a lógica das dez etapas, secundárias e persistência; não é
uma afirmação de que uma campanha inteira foi jogada manualmente.

## Assets

Gerador tools/gen_portions.py. Fontes Blender editáveis e reabertas:
art/blender/dish_fries.blend e dish_fish_portion.blend; GLBs correspondentes em
assets/models/gen. Modelos originais CC0, sem texturas externas. Registrar no
catálogo por tools/gen_item_catalog.py; importar no editor antes de executar.

## Verificação e entrega

Dados de teste separados por APPDATA, sem acessar saves reais. Regressões
revision26, home, company, counter-first, phone-layout, coastal, held-order,
tableware, management, practical, terminal e optimization. Logs/capturas finais em
qa/campanha-correcoes-2026-10-26. PASS lógico não substitui inspeção visual nem
permite ERROR/REAL_MISSING. Suíte completa de 12 regressões aprovada no executável/PCK exportado, além de oito verificações na fonte. Após atualizar somente os avisos restantes de computador para celular, revision26, phone-layout e optimization foram repetidas e aprovadas no PCK final antes de empacotar. A regressão também verifica entrega parcial/final, pagamento, permanência/remoção dos pedidos e inexistência do PC.

Gerar tools/package_quiosque_portable.py --variant revisao26. ZIP no D:
MareAltaResort_1.1_RC2_Celular_Campanha_2026-10-26.zip. Abrir Jogar.vbs após
extrair tudo; preservar userdata/ ao atualizar. Instalações anteriores permanecem.
Release: https://github.com/sergiomrge-tech/simulador-resort/releases/tag/v1.1.0-rc2.20261026-campanha-correcoes


## Auditoria dos pedidos desta sessão

| Pedido | Resultado / evidência |
| --- | --- |
| Casa desaparecendo pela janela | Oclusor legado removido; comparação da mesma câmera e captura casa_janela_corrigida.png. |
| Navio muito perto | Rota -220 Z; navio_distante.png e regressão coastal. |
| PC não responde / abre sem querer / mover à lateral | Substituído pelo último pedido: PC excluído; B abre celular em qualquer lugar, sem alvo físico. |
| Atendimento por dentro do balcão | E anota e entrega nos dois lugares; entrega parcial preserva pedido. |
| HUD e botões grandes, vazios | Celular 420×700, seis abas 3×2, estações em lista compacta e botões por conteúdo. |
| Pedidos e missões à esquerda | Painéis fixos e visíveis com estações/celular em tela larga; pedido some só ao entregar último item. |
| Campanha principal e secundárias | Dez etapas e quatro secundárias com progresso, persistência e recompensa única. |
| Vila vazia | Passeios pavimentados, bancos, vasos e postes com assets existentes. |
| Cliente pega e paga | Recebimento automático por produto; migração de contas antigas sem repetição. |
| Porções de batata frita e peixe | Modelos Blender próprios, estoque inicial, venda, retirada e reposição sem preparo. |
| Faixas brancas na chuva | Espuma separada da umidade; comparação sol/chuva e inspeção da captura. |

Os pedidos de alcance/posição do PC foram substituídos expressamente pela remoção
final, e não devem ser restaurados. A campanha foi validada por regressão de lógica
e save; as capturas documentam a apresentação, sem alegar uma campanha inteira
jogada manualmente. Nenhuma medição nova de FPS foi feita neste lote.


PCK final: SHA256 `5e420931892f379c7e6e3dc3a66501c120fb9cde39d79ea2185e020b97f9d0c5`, 1805368728 bytes. Logs sem ERROR/REAL_MISSING e encerramento code=0.
