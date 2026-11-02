# Pendências para o jogo ficar 100%

02/11/2026. Lista única de tudo que falta para o Maré Alta Resort ficar completo, por área, com prioridade.
O lado Steam/lançamento (conta, página, integração, demo) está em `ROADMAP_STEAM.md`; aqui está o **jogo**.
Fontes:
- checklist de pedidos;
- `AUDITORIA_GERAL.md`;
- `PENDENCIAS_2026-10-29.md`;
- plano de gameplay;
- testes no editor e no PIE de 02/11.

Prioridade:
- **P0:** defeito visível ou quebra;
- **P1:** sistema/conteúdo essencial;
- **P2:** acabamento.

Marcar `[x]` só depois de testado no jogo, com foto ou teste automático.

## 1. Defeitos conhecidos (corrigir primeiro)
- [x] P0 **Biquíni novo (top faixa e parte de baixo até a virilha)** importado e conferido nas 6 banhistas
  (Ada, Asha, Zuri, Celeste, Jelena, Tuya), 02/11.
- [x] P0 **MetaHumans descalços**: chinelo e tênis feitos sobre o pé dos MetaHumans (`tools/ue58/gen_mh_shoes.py`), conferidos no PIE, 02/11.
- [x] P0 **Roupa padrão da Epic** pintada por papel (`metahumans.json` → `clothes`), conferida no PIE, 02/11. Roupas de modelos
  variados (regata, vestido, camisa social) continuam na seção 5.
- [~] P1 Toalha em cima da cama do bangalô sujo: ampliada 1,8× (falta foto no PIE).
- [ ] P1 Faixa de pele um pouco mais clara onde ficava a roupa íntima assada em algumas banhistas (ajustar o preenchimento).
- [ ] P1 Zuri careca (preset da Epic): dar cabelo ou trocar de banhista.
- [ ] P1 Vasos de pachira do saguão do hotel com colisão de copa enorme (bloqueia a mira). Corrigir a colisão
  quando o Sergio liberar esses arquivos, que têm mudanças dele.
- [ ] P1 Painel da negociação: conferir no jogo o texto já corrigido (estava espremido).
- [ ] P2 Bainha das pernas da sunga boxer levemente marcada; pequenos furos no cós.

## 2. Migração Godot → Unreal ainda incompleta
- [x] P1 **Pesca no píer** e **modo foto (P)** com álbum (02/11): E na ponta do píer abre a pescaria (espera, "fisgou!",
  janela curta para puxar; 5 espécies com tamanho, garoupa rara); cada peixe vai ao estoque (capítulo do Seu Gregory).
  P (ou direcional para baixo) tira a foto sem a interface, salva em `Saved/Album` e registra no álbum o que estava
  enquadrado (farol, píer, hotel, quiosque, bar, piscina): a foto do farol cumpre o passo do Padre Robson.
  `MareLeisure.cpp`, `Content/Data/leisure.json`, teste `MareAlta.Gameplay.FishingPhotoChapters`. Falta: vara de pesca na mão
  e uma página de álbum no celular.
- [x] P1 **Capítulos 2–4 da vila** com contagem real (02/11): peixes da pescaria, foto do farol, receitas = drinks
  descobertos no bar (o texto do capítulo "Sabores" foi atualizado; a cozinha experimental da Godot não foi portada),
  negócios contam só os comprados.
- [x] P1 **Festas e eventos do calendário** (02/11): eventos do dia da Godot (calor, lua cheia, maré alta, tempestade) e
  festas semanais a partir do dia 8 (quermesse, junina, show do DJ; carnaval depois do capítulo da prefeita); previsão
  do dia seguinte e preparativos pagos na agenda do celular (decoração da festa ou proteção do estoque); clientes
  conforme o evento; tempestade com chuva, perda de estoque sem preparativos e passeios de mar cancelados.
  Cenário na praia: barracas, bandeirinhas, fogueira com chamas e luz tremulando, cabine do DJ, faixa (modelos
  `tools/ue58/gen_festival.py`). `MareEvents.cpp`, `MareEventsWorld.cpp`, `Content/Data/events.json`, teste
  `MareAlta.Gameplay.DayEventsParties`. Falta: mar mais agitado na tempestade e na maré alta (o material do mar não tem
  parâmetro de ondas), pessoas dançando a quadrilha e música própria de cada festa.
- [ ] P1 **Minijogo dos negócios** (3 rodadas da Godot), ainda não portado.
- [ ] P1 Corpo do jogador em primeira pessoa: pegar, carregar, portas e natação. Estava em validação em 29/10; re-testar.
- [ ] P1 Abertura: ônibus detalhado, desembarque, caminhada até a casa e carta (provisórios em 29/10); re-testar.
- [ ] P1 Casa: todas as interações da Godot (sofá, TV, som, chuveiro); a captura do chuveiro ficou pendente.
- [ ] P2 Animais da vila e fauna marinha ainda com aparência cartoon; horizonte subaquático azul e vazio.
- [ ] P2 Interior dos quartos do hotel além da suíte visitável (a torre é casca com fachada).

## 3. Gameplay: cada lugar com algo para fazer
Pronto e testado (02/11):
- quiosque completo;
- pousada com recepção, negociação e limpeza;
- hotel com recepção de VIPs;
- HUD de estrelas, quartos e vendas;
- preço por produto;
- fama trazendo clientes;
- sinuca (física, IA e aposta).

- [x] P1 **Bar do Coqueiro** (M8, 02/11): clientes sentam nas banquetas com pedidos (do cardápio, "me surpreenda" ou um
  drink desconhecido com dica); o jogador mistura até 5 ingredientes na coqueteleira; 11 receitas (2 conhecidas no início),
  descobrir dá fama; gorjeta pela rapidez; reposição de ingredientes; o bartender serve sozinho o que está no cardápio.
  Dados em `Content/Data/bar.json`, lógica em `MareBar.cpp`, mundo em `MareBarWorld.cpp`, teste `MareAlta.Gameplay.BarDrinks`.
  Falta: animação do bartender preparando e copo no balcão.
- [x] P1 **Negócios da vila**, uma tarefa curta cada (02/11): balcão com E em cada negócio comprado e um cliente esperando
  quando há atendimento na hora; minijogo de 3 rodadas da Godot portado (pranchas, food truck, sorveteria, souvenires, surfe),
  pagamento e fama pelos acertos, uma vez por hora dentro do horário. `MareBusiness.cpp`, `MareBusinessWorld.cpp`,
  `Content/Data/business_games.json`, teste `MareAlta.Gameplay.BusinessCounter`. Falta foto do cliente na nova posição ao
  lado do balcão e conferir os balcões do food truck, souvenires, aluguel e surfe no jogo.
- [x] P1 **Piscina** (02/11): folhas caem na água a cada hora aberta (E com a peneira), banhistas deixam toalhas nas
  espreguiçadeiras (E recolhe) e pedem picolé (E no cooler vende). Sujeira e toalhas reduzem a renda por hora e, no
  fechamento, viram nota dos banhistas (estrelas). `MarePool.cpp`, `MarePoolWorld.cpp`, `Content/Data/pool.json`, folhas em
  `tools/ue58/gen_pool_mess.py`, teste `MareAlta.Gameplay.PoolDayUse`.
- [x] P1 **Passeios** (02/11): bilheteria na entrada do píer com fila de compradores nas 3 horas antes de cada saída
  (snorkel 10h, barco 14h, trilha do farol 16h); o jogador vende os bilhetes (o guia vende sozinho); na hora da saída o
  jogador guia: 3 paradas com uma escolha boa, uma aceitável e uma ruim, que viram nota (estrelas), gorjeta e fama; sem
  jogador e sem guia o passeio é cancelado e os bilhetes devolvidos; passageiros esperam no píer e embarcam.
  `MareTours.cpp`, `MareToursWorld.cpp`, `Content/Data/tours.json`, teste `MareAlta.Gameplay.ToursHandsOn`.
  Falta: barco saindo do píer com os passageiros e as paradas mostradas em cena.
- [x] P1 **Restaurante do hotel** (02/11): no almoço e no jantar clientes sentam nas 6 mesas do terraço; E na mesa anota o
  pedido, a cozinha prepara em 20 min, E no passe (balcão do bufê) pega os pratos prontos, E na mesa serve (gorjeta pela
  rapidez); serviço de quarto das suítes entregue no elevador; a equipe do hotel atende quem esperar 45 min; eventos
  (aniversário, casamento na praia, jantar de empresa) marcados para o dia seguinte. `MareRestaurant.cpp`,
  `MareRestaurantWorld.cpp`, `Content/Data/restaurant.json`, teste `MareAlta.Gameplay.HotelRestaurant`.
  Falta: pratos visíveis nas mesas e na bandeja, decoração do evento em cena.
- [~] P1 **Salão de jogos** (02/11):
  - [ ] partida de sinuca jogada até o fim no jogo (física e IA testadas; falta jogar uma partida inteira e conferir);
  - [x] pebolim (modelo bpy `tools/ue58/gen_game_room_extras.py`) com partida rápida de 3 rodadas contra um hóspede;
  - [x] 2 fliperamas "Maré Attack" com tela e letreiro acesos, partida rápida de 3 rodadas;
  - [x] hóspedes jogando das 18h às 23h e renda das fichas (mais jogadores com o hotel cheio).
  Dados em `Content/Data/business_games.json` (`pebolim`, `fliperama`, `game_room`), teste em `MareAlta.Gameplay.BusinessCounter`.
- [x] P1 Recepção do hotel com a fila de hóspedes visível no saguão (check-in vai ao elevador, check-out de manhã sai pela
  porta; teste `MareAlta.Gameplay.HotelReceptionLine`, foto no PIE 02/11).
- [x] P1 Equipe coerente com as tarefas novas (02/11): página de equipe com atendente, recepcionista, camareira,
  bartender, guia e os novos piscineiro (peneira e toalhas a cada hora) e garçom do restaurante (atende mesas e serviço de
  quarto após 15 min a 90%); descrições reescritas; teste `MareAlta.Gameplay.NewStaffRoles`. Turnos por horário ainda não
  existem (todos trabalham no horário do lugar).
- [ ] P2 Pedidos especiais e clientes VIP/influenciador no quiosque (eventos cômicos da tarefa #4).

## 4. Progressão, economia e conteúdo
- [~] P1 **Balanceamento** jogando do zero até o Grand Hotel (02/11: primeira passada por modelo em
  `docs/ue58/BALANCEAMENTO.md` e `tools/ue58/balance_model.py`; falta o playtest cronometrado para trocar as hipóteses):
  - desbloqueio novo a cada 10–20 min;
  - preços das expansões, salários, diárias e renda do salão.
- [ ] P1 Duração do Acesso Antecipado: 6–10 h de conteúdo com objetivo sempre visível.
- [ ] P1 **Tutorial**: dica na primeira vez de cada sistema (balcão, celular, recepção, limpeza, sinuca, bar…).
- [ ] P1 Campanha e missões secundárias auditadas (contadores, recompensas únicas, ligação com capítulos e expansões).
- [ ] P2 Temporadas (verão/carnaval) e calendário com variedade de clientes.
- [ ] P2 Tela de fim do conteúdo do Acesso Antecipado.

## 5. Pessoas
- [x] 21 MetaHumans por papel; banhistas com biquíni e sunga; mãos corrigidas.
- [ ] P0 Roupas reais e coloridas por papel:
  - praia: camiseta regata, saída de praia, bermuda de surfe;
  - social: camisa, vestido;
  - uniforme da equipe com cores do resort;
  - moradores.
- [x] P0 Calçados: chinelo, sandália de tiras, tênis e sapato social com saltinho (02/11), sorteados por papel
  (`metahumans.json` → `shoes`); sapato social conferido no saguão do hotel.
- [ ] P1 Mais banhistas: mulheres e homens de outras idades e tipos de corpo.
- [ ] P1 Animações:
  - deitar na espreguiçadeira e na canga;
  - nadar no mar e na piscina;
  - comer e beber sentado (já existe);
  - conversar com gestos;
  - limpar e atender (equipe).
- [ ] P1 Rosto: expressões faciais simples (sorriso ao receber, irritado na negociação).
- [ ] P2 Crianças e famílias (se houver presets/assets adequados).

## 6. Mundo e arte
- [x] Barcos detalhados (jangadas e botes), palmeiras, janelas, piscinas, mata dos morros.
- [ ] P1 Varredura visual final de todo o mapa:
  - objetos flutuando ou low poly;
  - texturas;
  - folhagem muito clara à noite;
  - ondas, espuma e respingos.
- [ ] P1 Personalização com 5 opções em tudo:
  - quiosque, expansões, hotel, piscina, tobogã;
  - casa (cama, sofá, armário, TV).
- [ ] P1 Interiores do restaurante, da recepção da pousada (o balcão rústico é externo) e dos negócios da vila.
- [ ] P2 Clima: chuva com poças, vento nas palmeiras, tempestade com mar bravo.
- [ ] P2 Detalhes de vida: pássaros, gaivotas, cachorros e gatos animados, barcos passando.

## 7. Áudio
- [ ] P1 Música por lugar e horário (quiosque, hotel, salão, noite).
- [ ] P1 Efeitos de todas as ações novas:
  - campainha da recepção, chaves, cama, lixo;
  - tacadas e bolas da sinuca;
  - liquidificador e coqueteleira do bar.
- [ ] P1 Mixagem final e volumes por categoria (já existem: geral, música, efeitos, ambiente).
- [ ] P2 Vozes curtas (murmúrios) sem diálogo falado, respeitando a regra de áudio suave.

## 8. Interface e experiência
- [x] P0 **Menu principal**: Novo jogo, Continuar, Carregar (3 slots), Opções, Créditos, Sair (02/11, foto no PIE;
  QA de PIE usa `-MareSkipMenu`).
- [x] P0 **Opções completas** (02/11, teste `MareAlta.Options.SaveAndReload`; idioma só troca fora do editor):
  - gráficos detalhados, resolução, janela, VSync, FPS, upscaler, FOV;
  - mouse e controle, remapear teclas;
  - idioma.
- [~] P0 **Controle** (Xbox/PlayStation) em todo o jogo e nos menus. (Tradução: ver a seção 11, no final.)
  - Código feito em 02/11 (`MareGamepad.h/.cpp`, mapeamentos em `Config/DefaultInput.ini`), falta testar com controle de verdade no EXE.
    Mapa fixo: analógico esquerdo anda, direito olha (sensibilidade própria + inverter Y); A pula/sobe nadando; **X interage**
    (A ficou com o pulo para não pular ao falar/servir); Y ou View celular; Start pausa; LT segurar ou L3 alternar corre; B mergulha.
    Menus: foco no 1º botão ao abrir com o controle, direcional/analógico navega, A confirma, B volta/fecha, LB/RB trocam abas,
    analógico direito rola. Sinuca: analógico mira, segurar RT dá força, B sai. HUD mostra botão ou tecla conforme a última entrada;
    opção "Botões do controle" Xbox/PlayStation. Testes: `MareAlta.Gamepad.MappingsAndLabels` e `MareAlta.Gamepad.MenuFocusAndBack`.
- [ ] P1 Três propostas de HUD/celular mais comercial (pedido antigo, apresentar antes de escolher).
- [ ] P1 Acessibilidade: tamanho do texto, legendas, daltonismo nos ícones de estrela e humor.
- [ ] P2 Indicador no mapa ou bússola com os lugares (pousada, hotel, salão, negócios).

## 9. Desempenho e estabilidade
- [ ] P0 FPS medido no executável:
  - setores pesados: praia com pessoas, saguão do hotel, vila à noite;
  - MetaHumans: limite visível, LOD, grooms.
- [ ] P0 Sessões de 2 h sem crash (GPU page fault do hotel mitigado com `r.Lumen.AsyncCompute=0`; re-testar).
- [x] P0 Saves: 3 slots, autosave ao dormir, migração do slot1 antigo, backup `.bak` (teste `MareAlta.Saves.Slots`, 02/11).
- [ ] P1 Memória: build de pessoas e texturas 8K das banhistas (avaliar 4K), tamanho do pacote final.
- [ ] P1 Testes automáticos cobrindo cada sistema novo (hoje 8 testes MareAlta.*) e QA de PIE com fotos por sistema.

## 10. Lançamento
Ver `ROADMAP_STEAM.md`: conta Steamworks e página, Steam Cloud, conquistas, build Shipping em PC limpo, demo,
Next Fest, playtest e beta, trailer, preço.

## 11. Tradução (por último, pedido do Sergio em 02/11)
Fazer depois de todo o resto, quando os textos estiverem estáveis.
- [ ] Todos os textos do jogo em tabelas de localização da Unreal (LOCTEXT/StringTable), sem texto fixo no código;
  inclui menus, celular, HUD, missões, cartas, placas 3D (TextRender) e nomes de produtos.
- [ ] **Inglês** completo.
- [ ] Vários idiomas (os que mais vendem na Steam): espanhol, chinês simplificado, russo, alemão, francês,
  japonês, coreano e português de Portugal; fontes com suporte a CJK e cirílico.
- [ ] Revisão por falante nativo de cada idioma e teste de layout (textos maiores em alemão/russo não podem cortar).
- [ ] Página da Steam e conquistas nos mesmos idiomas.

## 12. Ilha do passeio de barco (pedido do Sergio em 02/11, para o final)
- [ ] Ilha circular ao fundo, no mar, destino do passeio de barco: bastante árvores e vegetação (nada de low poly),
  praia em volta e uma trilha passando pelo meio.
- [ ] O passeio de barco sai do píer, vai até a ilha (desembarque e trilha) e volta; paradas do passeio guiado na ilha.

## 13. Correção de assets low poly (pedido do Sergio em 02/11, para o final)
Regra do projeto: nenhum asset low poly no jogo.
- [ ] **Fogueira da festa junina**: a lenha (`festa_campfire_logs`, vinda da Godot) são poucos troncos lisos e a chama
  ficou com cara de cone. Refazer com toras de verdade (casca com relevo, pontas cortadas e queimadas, brasas e cinzas
  na base, pedras em volta) e um fogo convincente (chamas em camadas com movimento, faíscas e fumaça em partículas).
- [ ] Revisar os outros modelos trazidos da versão Godot para as festas (cabine do DJ, faixa) e qualquer outro prop com
  poucas faces que aparecer na varredura visual final.
