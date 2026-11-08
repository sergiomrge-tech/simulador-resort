# Revisão da demo — simulação completa e lista de correções e melhorias (noite de 07/11/2026)

Pedido do Sergio: "após corrigir tudo, rode uma simulação de toda a demo e faça uma longa lista de correções e melhorias".

**Como foi feito:**
- `tools/ue58/qa/simulate_game.py` em perfil novo (`D:/CodexTemp/claude-sim-20261107-2304`), do ônibus da chegada até a
  noite e o salvar/recarregar. Relatório e fotos em `D:/CodexTemp/qa/sim/20261107-230549`.
- Mais as fotos que o Sergio mandou da demo, as minhas capturas desta noite e o jogo de referência (Resort Simulator,
  Fishleaf, ver `REFERENCIA_RESORT_SIMULATOR.md`).

**Resultado geral da simulação:**
- Nenhuma linha de erro no log em 27 etapas.
- Todas as compras e capítulos da demo funcionaram.
- O salvar e recarregar só diferiu na fila do food truck, que andou entre as duas leituras; não é perda de save.

**Prioridades:**
- **P0:** quebra o jogo ou a primeira impressão.
- **P1:** aparece para todo jogador.
- **P2:** acabamento.
- **P3:** ideia nova (só com o OK do Sergio, pela regra de não criar mecânicas novas sem pedido).

## A. Corrigido nesta noite (commit 0561ea2a e seguintes)

| # | Item | Como |
|---|---|---|
| 1 | Tela inicial era o menu sobre o jogo parado | Tela de título viva: câmera passeando pela baía, logo "Coconut Simulator", selo DEMO (`MareTitle.cpp`, `title.json`) |
| 2 | Sem abertura | 5 cartões-postais no Novo jogo, com capturas do jogo e legenda; Esc pula (`/Game/UI/Intro`) |
| 3 | Clientes travados | Saída tenta 6 direções; quem não tem caminho não nasce; só some fora da vista (`WalkAway`) |
| 4 | Quiosque escuro | Lâmpadas do quiosque acesas no expediente, 25x mais fortes de dia (`mare.KioskDayLight`) |
| 5 | Homem chamado "Luiza" | Nome pelo sexo do MetaHuman (`IsWoman`) |
| 6 | Pedido sumia ao abrir a geladeira | Bilhetes ficam visíveis com a estação aberta |
| 7 | Evento cômico só com texto | Só começa na vista do jogador; tropeço do atendente bem maior |
| 8 | Tutorial não dizia onde abrir | Missão: "vá até a praia (siga Quiosque na bússola) e aperte E na placa vermelha"; abertura marcada mostra a hora |
| 9 | Plantas flutuando / flores na areia | 102 pervincas tiradas da areia; arbusto vermelho "Bush_Common" trocado por arbusto real do Poly Haven |
| 10 | Pedras cor de carne | Material `rock_07` dessaturado para rocha de praia |
| 11 | Fumaça do vulcão parada | Sobe ~7 m/s, camadas em velocidades diferentes |
| 12 | Banhista "todo duro" | Mãos na barriga, um joelho dobrado (direito, esquerdo ou nenhum), respiração leve |
| 13 | Tobogã sem calha | Calha com parede de verdade, colorida (rosa, verde, amarelo, lilás) |
| 14 | Montanhas ao fundo | Duas serras a 5 e 8 km com névoa azulada (`gen_mountains.py`, `mare_serra.py`) |
| 15 | Fundo do mar | Corais x4, esponjas e anêmonas x3; capim marinho só abaixo de 2,5 m (mar de "gramado" ao pôr do sol) |
| 16 | Bar | Cliente fica bebendo no banquinho 25–40 s; bartender vira e entrega o drink |
| 17 | Pagamento | Tela com total/recebido/troco, gaveta de notas e moedas, maquininha; gorjeta e estrelas pelo troco (`MarePayment.cpp`) |
| 18 | Dívida da avó | Cartão em Finanças, carta, marcos, recado do banco, final só no jogo completo, teste com 20 vetores |
| 19 | Aviso de memória de vídeo | Pool de texturas por qualidade (`DefaultScalability.ini`) |
| 20 | Faixa cortada no painel | Mensagem em linha própria com quebra |
| 21 | Letreiro com quadradinho | "•" desenhado como traço na fonte 3D |
| 22 | Animação das pessoas | Gesto de pegar no balcão (cliente e atendente), motorista dirigindo (clipes UAL) |
| 23 | Músicas mais animadas | 11 faixas CC0 do OpenGameArt no rádio, logo depois da Aloha FM (créditos no CREDITS.md) |
| 24 | Jogo não instalado | Demo instalada em `D:\Games\MareAltaResort_Demo` com atalhos |

## B. Correções pendentes

| # | Prio | Item | Origem | Próximo passo |
|---|---|---|---|---|
| B1 | P0 | Som ambiente não muda nem desliga na demo | Sergio | Aguardando: qual som (música de fundo ou mar/vento) e onde (Opções › Ambiente ou rádio do celular). O código liga mar, vento, grilos, mata, pássaros e chuva ao controle "Ambiente"; a música de fundo segue "Música" |
| B2 | P0 | Primeira imagem da chegada é um close de estofado (simulação 01) | Simulação | Conferir no .exe os 2 primeiros segundos da câmera do ônibus; afastar a câmera do banco |
| B3 | P1 | 54 textos novos sem tradução (pagamento, abertura, título, faixas) | i18n_extract | Pacote para o GPT: `docs/ue58/I18N_TODO_2026-11-07.json` |
| B4 | P1 | Moradores Aoi e Jorge deslizando em dois momentos na vila | Simulação (marcha) | Reproduzir com a auditoria de marcha; ver se é o pedestre parado por um evento cômico (`HoldPedestrianNear`) |
| B5 | P1 | Interior do quiosque ainda escuro com sol a pino (madeira do balcão muito escura) | Fotos | Clarear o material interno do balcão ou um preenchimento suave sob o telhado |
| B6 | P1 | Mar ao pôr do sol verde e "gramado" ao longe | Fotos | Conferir de novo com o capim marinho mais fundo; se continuar, ajustar a cor de espalhamento da água com o sol baixo |
| B7 | P1 | Telhado de palha do bar com textura esticada/borrada de perto | Simulação 10_bar | Reprojetar UV ou textura de palha em escala menor |
| B8 | P2 | Ilhota de pedra lisa (laje marrom) na baía | Simulação | Trocar por rochas reais (Poly Haven) ou relevo com detalhe |
| B9 | P2 | Faixa turquesa no teto da cozinha da casa à noite | Simulação 05 | Ver a luz da cozinha (cor ou temperatura) |
| B10 | P2 | Banhista pulando "em pé" na água da piscina | Simulação 10_pool | Pose de mergulho (UAL `Jump_Loop` inclinado) ou entrada sentado pela borda |
| B11 | P2 | Folhas de samambaia grandes e chapadas na borda da praia | Fotos | Trocar por planta real com volume |
| B12 | P2 | Gramado da pousada com manchas de mato seco | Simulação 10_pousada | Menos densidade do mato marrom perto das casas |
| B13 | P2 | Câmera da tela inicial raspa as folhas e o telhado do quiosque em dois pontos | Fotos | Ajustar `title.json` |
| B14 | P2 | A volta da serra: conferir o fim do plano do mar (2,5 km) visto do mirante | Revisão | Foto do cume; se aparecer a borda, estender o mar distante |
| B15 | P2 | "Preparando shaders" aparece na tela inicial | Fotos | Cache de PSO no empacotamento (precache) |
| B16 | P2 | Pacote com 6,7 GB para uma demo | Build | Limitar texturas não vistas na demo e tirar o que é só do hotel |
| B17 | QA | Roteiro da simulação: fama 9 para o Grand Hotel; fechar a tela de fim da demo (`mare.ShowUI close`) depois das compras; comparar o save sem a fila dos negócios | Simulação | Ajustar `simulate_game.py` |
| B19 | P1 | QA do executável (106 checagens): 5 reprovações que já existiam antes desta noite: `void_recovery` (quem cai abaixo do mapa não volta ao chão seguro: o herói ficou caindo a -104 m), `village_walkers_active`, `rain_mix`, `grass_coverage_cooked`, `grass_nonblocking_culled` (`hotel_lobby_guests` é esperado na demo, sem hotel) | `test_preview_package.ps1` | Corrigir `void_recovery` primeiro (jogador preso); depois as outras |
| B18 | QA | Auditoria de assento acusa o Seu Tibúrcio no ar (o banco do cume não tem colisão) | Simulação | Falso positivo: dar colisão de consulta ao banco ou ensinar a auditoria |

## C. Melhorias (jogabilidade e apresentação)

| # | Prio | Melhoria | De onde |
|---|---|---|---|
| C1 | P1 | Contorno colorido no objeto mirado (como na referência) | Referência |
| C2 | P1 | Dicas de controle no canto com ícone da tecla ou do botão ("E: anotar pedido", "Clique: dar troco") | Referência |
| C3 | P1 | Lista de pedidos fixa à direita, também na estação e no bar | Referência |
| C4 | P1 | Partículas de retorno: brilho ao limpar a mesa, moedinha subindo ao receber, espuma ao arrumar o quarto | Referência |
| C5 | P1 | Ícone sobre a cabeça de quem espera para pedir ("!" ou balão) | Referência e simulação (clientes parados em ORDER) |
| C6 | P1 | Música própria na tela inicial (tema da praia) e fade para o jogo | Plano de apresentação |
| C7 | P1 | Tela de carregamento com arte e dica (Novo jogo, Carregar) | Plano de apresentação |
| C8 | P1 | Logo desenhado (Canva) no lugar do logo de texto; mesmo logo na cápsula da Steam | Plano de apresentação |
| C9 | P1 | Dívida: digitar um valor livre além dos botões R$ 1.000 / 10.000 / 50.000 / máximo | Contrato da dívida |
| C10 | P1 | Pagamento: dica "digite 1850 para R$ 18,50" na maquininha; som de caixa ao confirmar | Revisão |
| C11 | P2 | Animações: sentar e levantar com transição (UAL `Sitting_Enter`/`Sitting_Exit`), andar variado, conversar em grupo | Referência |
| C12 | P2 | Pedestres em grupos de 2–3 e alguns com sacolas | Referência |
| C13 | P2 | Banhistas variados: de bruços, sentados na toalha lendo | Revisão |
| C14 | P2 | Bartender ocioso limpando o balcão entre os pedidos | Referência |
| C15 | P2 | Repor com caixa e contador (3/8) além do "Repor 10" | Referência |
| C16 | P2 | Entrega no quarto da pousada: hóspede abre a porta e recebe | Referência |
| C17 | P2 | HUD mais enxuto: nível, XP e estrelas num cartão no alto à esquerda | Referência |
| C18 | P2 | Eventos cômicos genéricos (turista perdido, influenciador) com gesto (acenar) e não só a fala | Revisão |
| C19 | P2 | Cáusticas no fundo do mar mais fortes no raso e raios de sol embaixo d'água | Referência |
| C20 | P3 | Troco também no bar e nos negócios | Ideia |

## D. Lançamento (Steam e build)

| # | Item |
|---|---|
| D1 | Nome: "Resort Simulator" já é da Fishleaf (Steam 4319390); conferir na Steam e no Google que "Coconut Simulator" está livre antes de registrar o app |
| D2 | Build Shipping (sem console e sem o aviso de memória de desenvolvimento) e teste num PC sem a Unreal |
| D3 | Integração Steam (conquistas da dívida em `docs/steam/conquistas.json`, nuvem, Rich Presence) |
| D4 | Músicas CC0 do OpenGameArt: conferir se alguma está registrada no Content ID antes de liberar streaming |
| D5 | Créditos do jogo (`credits.json`) com as faixas novas e o "IA nas músicas e na imagem" já decidido |
| D6 | Preset Baixo medido com `bench_package.ps1` para os requisitos mínimos |
