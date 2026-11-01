# Checklist de pedidos do usuário

Toda solicitação do usuário entra aqui no momento em que é feita e só é marcada quando estiver
implementada **e** validada (compilação, testes pelo MCP, captura real). Mais recente no topo.
Legenda: [x] feito e validado · [~] em andamento/parcial · [ ] pendente.

## 01/11/2026 — continuidade (Claude)

- [x] Assumir o projeto UE5.8, preservar o trabalho do Codex e avançar (branch `codex/ue58-migration`).
- [x] Pendência crítica da demo: campanha travada no capítulo do píer; salário diário, fama, capítulos da vila. (`PROGRESSAO_2026-11-01.md`)
- [x] Gerar prévia Windows e testar (96/96). (pedido "Yes, package it")
- [x] Trabalhar a Unreal pelo MCP do editor.
- [x] Remote Control para conduzir pelo celular.
- [x] Permissões de projeto da Unreal: aceitar sozinho (Computer Use quando o editor aparecer na lista de apps; caso contrário, pelo MCP).
- [x] Após cada lote, seguir o plano do GitHub sem parar a produção.
- [x] Procurar e salvar assets gratuitos; Claude decide quando modelar ou usar asset. (`D:/Assets/PolyHaven`, `tools/ue58/fetch_polyhaven.py`)
- [x] Só gerar executável de teste quando o usuário pedir.
- [x] Hotel 5★: conseguir entrar, decoração e funcionalidade (recepção, renda noturna). (`HOTEL_PRAIA_2026-11-01.md`)
- [x] Praia mais bonita estilo Caribe: areia mais branca, águas claras e belas.
- [x] Ondas quadradas: corrigir (malha do mar graduada 0,75 m).
- [x] Vegetação nas montanhas ao redor e pontas da costa (19.324 instâncias CC0).
- [x] Polimento visual: objetos flutuando (26 itens corrigidos; varredura `mare_float_audit`) e 36 malhas facetadas da praia suavizadas (guarda-sóis listrados/palha/sombreiros, armações e mastros; `tools/ue58/smooth_props.py`).
- [x] Rádio: 3 novas músicas originais (Reggae Roots, Calipso Caribe, Praia Pop/ukulele), 6 estações + desligado, nome no celular; testado no PIE.
- [x] Andar pela vila, principalmente quiosque e hotel: regressão 99/99 no PIE, atendimento real com e sem atendente, hotel acessível; adicionado dispensar atendente. (`ue58/CAMINHADA_2026-11-01.md`)
- [x] HUD/celular mais comercial, amigável e fácil: 3 propostas apresentadas (`ue58/hud-propostas/propostas.html`); usuário escolheu **B · Maré Tropical com o celular em abas laterais como na C** — implementado (faixa de madeira, comandas, bilhete de missões, placa de interação, avisos; celular/estações com abas laterais). Captura: `ue58/graphics-reference/hud-b-20261101`.
- [~] Andar por todo o jogo, montar checklist do que precisa ser corrigido e corrigir (feito: janelas + luz noturna, piscinas, espuma, 5.729 objetos empilhados na piscina, mata das pontas; ver `ue58/AUDITORIA_GERAL.md`) (ex.: janelas opacas de todas as construções). Lista detalhada em `ue58/AUDITORIA_GERAL.md`.
- [~] "Continue com os ajustes gráficos" (01/11): grama/conchas/seixos/flores/caibros/fiação recolocados nas posições da Godot (3.994 instâncias); 34 cabelos/câmeras de hóspedes flutuando no hotel removidos; hotel ganha hóspedes no restaurante, academia e bar da piscina. Pendente: interiores dos quartos.
- [x] "Coloque grama e arbustos" + "Preencha até as montanhas, coloque arbustos também" (01/11): gramado cheio (grama CC0 Poly Haven) do resort, vila e lotes até a mata dos morros, com arbustos, samambaias e flores; lotes de expansão somem com a compra (`mare_lawn.py`).
- [x] "Corrigiu os vidros opacos?": sim, na leva da auditoria (janelas das casas com vidro refletivo e luz à noite; demais vidros transparentes). Conferido de novo nas capturas da vila.
- [x] "Os braços ao nadar estão muito estranhos e feios" (01/11): braçada de peito em primeira pessoa (mãos se encontram, estendem, abrem e recolhem, no terço inferior da tela); parado na água, sculling suave. Regressão 100/100. Observação: o modelo da mão é o do personagem e continua simples.
- [ ] "Após terminar os ajustes gráficos e visuais vamos trabalhar no gameplay" (01/11): próxima fase depois dos coqueiros.
- [x] "Os coqueiros não combinam com o ambiente, substitua por assets mais realistas, procure na web" (01/11): Coconut Tree do Fab (Darmawan Pujisetyadi, CC BY 4.0), baixado pelo Chrome logado do usuário para `D:/Assets/Fab`, aplicado nos 171 coqueiros mantendo posições ("Bem melhor").
- [x] "Troque essas árvores também por assets mais realistas" (01/11): as 16 amendoeiras facetadas viraram o HighPoly Tree Model do Fab (Next Spring, CC BY 4.0).
- [x] "Substitua os cocos do jogo por esses da foto" + "Procure no Fab que tem grátis" (01/11): Megascans só é grátis para Fortnite (Personal R$ 10,80); usado o Coconut grátis de Rabeya Akter (Fab Standard License) com casca CC0 palm_bark nos 26 cocos soltos.
- [x] "Nenhum coco fica em pé assim por causa da gravidade" (01/11): cocos deitados de lado (eixo comprido na horizontal), giro diferente por variação. "Os prints mostram em pé": o modelo do Fab era quase uma bola; agora é oval (1,28:1) e achatado onde apoia, afundado 1,5 cm na areia, e o 5º coco de cada pilha encaixa no vão entre os quatro.
- [x] "Veja o que precisa de refinamento visual" + "Corrigir tudo" (01/11): tour de 38 câmeras. Corrigido: vãos azuis entre a vila e os morros (o plano do oceano aparecia; terreno de preenchimento `tools/ue58/coast_fill.py`), quinas retas de areia no mar (`tools/ue58/round_beach.py`), árvores estilizadas dos morros (island_tree → HighPoly Tree do Fab).
- [x] "Arredonde os cantos para não ficar quadrado, corrigir dos 2 lados da praia" (01/11): praia curva nas duas pontas, sem bancos de areia.
- [x] "Corrigir, precisa ser arredondados e suaves" (01/11): 70 blocos de morro suavizados (subdivisão com bordas compartilhadas, `tools/ue58/smooth_hills.py`) e textura CC0 aerial_grass_rock em projeção tri-planar.
- [x] "Coloque rochas nos morros também, use assets do Poly Haven" (01/11): ~10 mil rochas CC0 (rock_face_01/02, coast_rocks_01/02/03/05) em grupos, mais densas nas encostas íngremes.
- [x] "Trabalhe agora na iluminação noturna: postes de luz, janelas das casas acesas à noite" (01/11): a noite saía estourada (luz do céu fixa em 1 + exposição sem limite) — céu e exposição agora escurecem, lua azulada; 134 luzes reais sem sombra (globos dos postes, lâmpadas, lanternas, piscina) acendem ao anoitecer só nas áreas construídas; vidros das lâmpadas brilham (`M_LampGlow_PBR`); janelas quentes acesas. QA `night_lamps_built`.
- [~] "Todas as correções visuais já foram feitas? Se não, mostre e corrija" (01/11): feito — faixas azuis do norte cobertas, mata dos morros 50% mais densa. Pendente/menor: telhado plano da barraca de souvenir (só visível do alto), farol simples, quartos do hotel sem interior.
- [~] "Personagens com roupas diferentes: praia, social, para o hotel; procure assets ou crie no Blender" (01/11): estilos por cor já no jogo (praia colorida, social para hóspedes/recepção/barman, casual para moradores, uniforme para funcionários; `M_PersonOutfit`). Não existem roupas modernas CC0 para o rig Quaternius (só fantasia).
- [ ] "Na praia precisa ter pessoas com biquíni" (01/11): o corpo exportado não tem pele do joelho ao peito (cortada sob a roupa); precisa restaurar o corpo completo do UBC (Quaternius CC0) no Blender e gerar variantes biquíni/sunga. Material `M_PersonBody` (roupa de banho a partir da roupa íntima pintada) já pronto.
- [~] "Personalização de tudo, 5 opções de cada, valores crescentes, mais bonitos e detalhados — quiosque, expansões, hotel, piscina, tobogã, casa (cama, sofá, armário, TV)" (01/11): sistema de personalização de todo o resort em andamento.
  - [x] Sistema (01/11): catálogo `Content/Data/customization.json` (5 níveis por objeto, preços ×1/2,5/6/14/30), compra/troca grátis do que já tem/prévia grátis, save `custom.*`; efeitos no quiosque: movimento de clientes ×até 3,4, gorjeta, paciência, atendente mais rápido (balcão), fama; aba "Personalizar" no celular; teste `MareAlta.Migration.Customization`.
  - [x] "Melhoria nos pratos, valores" (01/11): 5 níveis de receita por prato (preço ×1 até ×2,3, mais pedidos, fama a partir de Gourmet), nomes por nível.
  - [x] Quiosque: 8 objetos × 5 níveis definidos (mesas, cadeiras, banquetas, guarda-sóis, balcão, iluminação, plantas, letreiro).
  - [x] Quiosque: 22 modelos Poly Haven importados (`/Game/Custom`, `mare_custom.py`) e 14 acabamentos PBR fotográficos (carvalho, madeira azul, azulejo, teca, linho listrado, palha, lona, neon); QA `custom_all_tiers_have_visuals`, `custom_preview_swaps_tables`.
  - [x] "Toda personalização é uma melhoria e precisa ser paga com o dinheiro do quiosque" (01/11): já é assim — níveis 2–5 e receitas são cobrados do caixa (o nível 1 é o item inicial; voltar a um nível já pago não cobra de novo).
  - [ ] Cartões com imagem no celular (Canva) — opcional.
  - [x] "Faça a personalização das expansões primeiro... depois a casa" / "Aproveite que já está no alto e já faça todas as personalizações" (01/11): 15 lugares, 80 objetos, 400 opções — quiosque, bar, piscina, pousada, passeios, Grand Hotel (restaurante, piscina/tobogã, suítes, lazer), 5 negócios da vila e casa (cama, sofá, mesa de centro, armário, rack da TV, mesa e cadeiras da cozinha, criado-mudo, luminária, poltrona, quadros, plantas). Gerador `tools/ue58/customization_places.py`.
  - [x] Renda das expansões (01/11): bar e piscina rendem por hora aberta, pousada cobra diária ao dormir (quartos, ocupação, gorjetas, avaliação), passeios saem às 10h/14h/16h com guia, negócios da vila podem ser comprados (fama + história) e rendem por hora; equipe nova (bartender, camareira, guia); casa confortável deixa o jogador mais rápido e casa bonita dá fama por noite; decoração do hotel aumenta ocupação e diária. Abas Equipe e Resort atualizadas; teste `MareAlta.Migration.ExpansionOperations` (4/4 testes passam).
  - [x] Modelos (01/11): 41 móveis Poly Haven CC0 baixados em `D:/Assets/PolyHaven`; 6 móveis detalhados modelados em bpy (`tools/ue58/gen_custom_furniture.py`: 3 espreguiçadeiras, daybed, cama estofada, cama com dossel) com tecidos fotográficos CC0.
  - [x] Modelos importados na UE (47 novos em `/Game/Custom`), proporções naturais corrigidas, guarda-sóis da piscina e tochas do hotel reconhecidos, tobogã em 5 acabamentos (`M_Custom_Slide_2..5`); imagens de bar, piscina, pousada, hotel (restaurante e piscina) e casa nos 5 níveis; QA PIE 104/104 com `custom_all_places_have_visuals`.
  - [ ] Interior de quartos da pousada/suítes do hotel (os itens de quarto e de serviço já têm efeito, ainda sem móveis próprios no mapa).
- [x] "Procure um modelo real de celular (asset) e adapte a tela" (01/11): "Realistic Smartphone" (dimension Dazzle, Fab, CC BY 4.0) segurado deitado à frente da câmera; a interface é desenhada exatamente sobre o vidro, recalculada a cada quadro (inclui a escala de DPI do monitor). "Não precisa das mãos na tela / só uma": só a mão direita segura a ponta. "A tela não pega todo o celular, corrigir": corrigido (o deslocamento era descontado do tamanho).
- [x] "Aproveite que está mexendo no celular e me ajude a melhorar a interface dele" (01/11): feito com esforço alto.
- [x] "A água da piscina precisa ser real como a da praia, limpa, transparente e realista" (01/11): água Single Layer Water com coeficientes por cm como o mar, mas ~4x mais limpa (absorção no vermelho dá o ciano natural), superfície polida; fundo e paredes com pastilhas de 5 cm (rejunte, variação por peça) e cáusticas de sol animadas (`M_PoolTiles_PBR`), nas piscinas da pousada e do hotel. Fundo e sombras das boias visíveis através da água.
- [x] "No fundo da piscina coloque o desenho de uma baleia orca, faça no Canva, como se fosse de azulejo" (01/11): mosaico gerado no Canva (`D:/Assets/Canva/orca`), reduzido a uma cor por pastilha de 5 cm (`tools/ue58/orca_mural.py`) e aplicado no fundo das duas piscinas, alinhado ao rejunte: 6 × 3 m na pousada, 9 × 4,5 m no hotel. Pastilhas do fundo um pouco mais azuis para o branco da orca aparecer.
- [x] "Mudar o nome dos personagens: Seu Zé vai se chamar Gregory, a avó Dilce; os outros você decide, com Roberta, Charbele, Alana, Tuany, Yasmin, Robson, Ayla e Cecília" (01/11): Seu Gregory (píer), avó Dilce (quem deixou o quiosque e assina a carta; o jogo tinha um avô), Dona Roberta (ex-Rita), Dona Cecília (ex-Lourdes), Padre Robson (ex-Tomé), Tuany (vendedora da praça), Prefeita Tuanny (carnaval); clientes Charbele, Yasmin e Ayla. Dados, diálogos, missões, histórias, carta e QA atualizados; testes 4/4.
- [x] "No celular quero 5 opções totalmente diferentes" / "Use o Canva" / "Gostei da opção 3" (01/11): 5 maquetes no canvas + moodboard no Canva; escolhida a 3, Caderno do Quiosque, implementada em todas as abas: capa kraft, abas de fichário, papel pautado com margem, letra manuscrita (Patrick Hand + Nunito, OFL, `Content/UI/Fonts`), etiquetas de preço inclinadas, carimbos EM USO/CONTRATADO/COMPRADA/SEU, índice "Onde?" na Personalizar, recados no topo. HUD esconde nota de missões e tíquetes com o celular aberto. QA PIE 104/104.
- [x] Manter este checklist sempre que o usuário pedir algo (regra salva na memória).

## Regras permanentes já pedidas

- Celular pelo B, placa física do quiosque, balcão antes da mesa, produtos prontos sem preparo, um atendente, pagamento automático.
- Visual realista estilizado aprovado; sem low poly como arte final; licenças registradas em `CREDITS.md`.
- Mitigação Lumen `r.Lumen.AsyncCompute=0` mantida; não alegar desempenho sem medição.
- Saves do jogador preservados; testes com perfis isolados em `D:/CodexTemp`.
