# Rumo à Steam: tudo o que falta, por prioridade

02/11/2026. Jogo para **PC (Steam), Unreal 5.8**, lançamento em **Acesso Antecipado**. Base: `docs/STEAM_PLAN.md`,
o plano de gameplay (`docs/ue58/GAMEPLAY_PLANO_2026-11-02.md`), o checklist de pedidos e o estado real do
código. Marque `[x]` ao concluir; `👤` = só o Sergio pode fazer (contas, pagamentos, decisões).

Legenda de prioridade:
- **P0:** sem isso a Steam não aceita ou o jogo quebra.
- **P1:** sem isso o jogo não segura o jogador (Acesso Antecipado de 6–10 h).
- **P2:** qualidade que vende (página, review).
- **P3:** depois do lançamento.

---

## P0 — Obrigatório para publicar

### Conta e loja (👤)
- [ ] 👤 Criar a conta Steamworks Partner, pagar US$ 100 (Steam Direct), preencher dados bancários e fiscais (W-8BEN Brasil).
- [ ] 👤 Criar o App ID do jogo e o **App ID da demo**.
- [ ] Página "Em breve" no ar **o quanto antes**, para juntar wishlists:
  - cápsulas: header 920×430, small 462×174, main 1232×706, vertical 748×896, fundo 1438×810, biblioteca 600×900 / 3840×1240 / logo 1280×720;
  - 5+ screenshots 1920×1080 do jogo real;
  - descrição PT/EN e tags (Simulação, Gerenciamento, Primeira pessoa, Aconchegante, Praia, Realista);
  - questionário de conteúdo (álcool: caipirinha);
  - requisitos mínimos e recomendados **medidos**.
- [ ] 👤 Classificação etária (IARC pela Steam), EULA e política de privacidade simples.

### Integração Steam no jogo
- [ ] Steamworks SDK / Online Subsystem Steam no projeto UE 5.8 (`steam_appid.txt` só em desenvolvimento).
- [ ] Steam Cloud para os saves e as configurações.
- [ ] Conquistas: primeira venda, primeiro check-in, 5 estrelas, Grand Hotel, vencer na sinuca, dia 30…
- [ ] Rich Presence ("Dia 4 · Quiosque aberto") e overlay funcionando.
- [ ] Depot Windows e upload por SteamPipe em branch beta; testar a instalação pela Steam num PC limpo.

### Build e estabilidade
- [ ] Pacote **Shipping** Win64 (hoje só há prévia Development): cook completo, sem console de dev, sem `-MareSaveRoot`.
- [ ] Teste em PC limpo, sem Unreal instalada (redistribuíveis VC++ e DirectX pelo instalador da Steam).
- [ ] Zero crashes em sessões de 2 h (já houve GPU page fault no hotel, mitigado com `r.Lumen.AsyncCompute=0`; re-testar).
- [ ] Saves: **3 slots** (hoje só `slot1.json`), autosave, migração entre versões, backup antes de gravar.
- [ ] Desempenho **medido no EXE**: 60 FPS em 1080p no recomendado e 30+ no mínimo; com ~30 MetaHumans na cena
  (LOD, limite de pessoas visíveis, grooms em cards) e Lumen nas três qualidades.

### Menus e opções (padrão Steam)
- [ ] **Menu principal:** Novo jogo, Continuar, Carregar (3 slots), Opções, Créditos, Sair. Hoje o jogo abre
  direto na introdução.
- [ ] **Opções completas** (hoje a pausa só tem qualidade média/alta):
  - presets gráficos e itens separados (sombras, Lumen, reflexos);
  - resolução, modo de janela, VSync, limite de FPS, escala 3D e upscaler (TSR/FSR/DLSS);
  - FOV;
  - volumes (geral, música, efeitos, ambiente);
  - sensibilidade do mouse, inverter Y e remapear teclas.
- [ ] **Controle** (Xbox/PlayStation) em todo o jogo e nos menus; selo "Steam Deck" opcional.
- [ ] **Idiomas:** feito por último (ver o fim desta lista).

---

## P1 — Gameplay para o Acesso Antecipado (6–10 h)

### Já pronto e testado (02/11)
- [x] Quiosque completo:
  - pedido no balcão, produtos prontos e entrega;
  - estoque e reposição, atendente;
  - preço por produto, receitas e personalização.
- [x] Pousada com recepção, negociação em 3 rodadas, check-in e limpeza; recepcionista e camareira.
- [x] Grand Hotel com recepção de VIPs e equipe; salão de jogos com sinuca (física, IA e aposta).
- [x] HUD de estrelas, quartos e vendas; fama trazendo clientes; fechamento do dia com salário e resumo.
- [x] Capítulo 1 da vila e campanha de missões.

### Falta
- [ ] **Cada expansão com algo para fazer** (hoje são passivas):
  - [ ] Bar do Coqueiro: drinks por combinação (M8); descobrir receitas dá fama; o barman automatiza;
  - [ ] Negócios da vila, uma tarefa curta cada (portar o minijogo da Godot):
    - pranchas e caiaques;
    - food truck do pastel;
    - sorveteria;
    - lojinha de souvenires;
    - escolinha de surfe;
  - [ ] Piscina: limpar com a peneira (afeta as estrelas), espreguiçadeiras, toalhas, picolé;
  - [ ] Passeios: vender bilhetes no píer, guiar barco/trilha com paradas de foto, nota do passeio;
  - [ ] Restaurante do hotel: atender as mesas (como no quiosque), serviço de quarto, eventos.
- [ ] Salão de jogos: partida de sinuca jogada até o fim no jogo, pebolim, 1–2 fliperamas, hóspedes jogando à
  noite, renda das fichas.
- [ ] Recepção do hotel com a fila de hóspedes visível; toalha da cama do bangalô maior.
- [ ] Pesca no píer e modo foto (P): destravam os **capítulos 2–4** da vila.
- [ ] Festas e eventos do calendário (junina, quermesse, DJ, tempestade, maré alta) portados da Godot.
- [ ] **Balanceamento** (M6): curva de dinheiro e desbloqueios a cada 10–20 min, preços das expansões,
  salários e diárias; jogar do zero até o Grand Hotel e medir as horas.
- [ ] **Tutorial e onboarding:** dicas na primeira vez de cada sistema (balcão, celular, recepção, limpeza,
  sinuca); objetivo sempre visível.
- [ ] **Fim de conteúdo do AE:** tela "obrigado por jogar o Acesso Antecipado" e o que vem a seguir.

---

## P2 — Qualidade que vende

### Pessoas (MetaHuman)
- [x] 21 MetaHumans por papel; banhistas com biquíni (top faixa) e sunga.
- [ ] Biquíni novo aplicado e testado nas 6 banhistas (Ada, Asha, Zuri, Celeste, Jelena, Tuya); Zuri com cabelo ou trocada.
- [ ] **Roupas variadas e coloridas** para praia, social (hotel), uniforme (equipe) e moradores. Hoje é a
  camiseta e a bermuda brancas padrão da Epic.
- [ ] **Calçados** (chinelo, tênis, sapato social): ninguém descalço fora da areia.
- [ ] Animações: sentar nas espreguiçadeiras, nadar no mar e na piscina, conversar, comer e beber.
- [ ] Mais variedade sem perder desempenho (cores, cabelos, idades).

### Mundo e áudio
- [ ] Revisão visual final de todo o mapa (objetos flutuando, low poly, texturas, noite).
- [ ] Personalização com 5 opções em tudo (quiosque, expansões, hotel, piscina, tobogã, casa).
- [ ] Áudio completo: música por lugar, ambiente (mar, pássaros, vila), efeitos de todas as ações, mixagem.
- [ ] Acessibilidade básica: tamanho do texto, legendas, daltonismo no HUD.

### Divulgação
- [ ] Trailer de 30–60 s com gameplay: acordar, quiosque, recepção, pôr do sol, sinuca, dormir.
- [ ] **Demo** de 3 dias (M9) e inscrição no **Steam Next Fest** (precisa da página aprovada semanas antes).
- [ ] Steam Playtest e beta fechado (50–200 pessoas) para medir FPS em várias placas.
- [ ] Press kit, redes sociais, vídeos curtos (TikTok/Shorts) da vida na praia.
- [ ] Preço: US$ 12,99, com preço regional no Brasil em torno de R$ 32,99–37,99.

---

## P3 — Depois do lançamento
- [ ] Co-op online (2–4 jogadores): o que mais vende no gênero; os sistemas novos já guardam o estado na simulação.
- [ ] Eventos cômicos (tarefa #4): turista influenciador, gaivota ladra…
- [ ] Novas expansões e temporadas; espanhol; Steam Workshop (decorações).
- [ ] Atualizações frequentes guiadas pela comunidade (lição do TCG Card Shop Simulator).

---

## Ordem sugerida de trabalho
1. 👤 Conta Steamworks e página "Em breve" (as wishlists levam semanas para crescer).
2. Menu principal, 3 slots, opções completas, inglês e controle (P0 técnico).
3. Expansões com tarefa (bar, negócios, piscina, passeios, restaurante), salão completo, capítulos 2–4.
4. Roupas, calçados e animações das pessoas; revisão visual e áudio.
5. Balanceamento e tutorial jogando do zero; desempenho no EXE.
6. Integração Steam (Cloud, conquistas), build Shipping, PC limpo.
7. Demo, Next Fest, playtest e beta; trailer e lançamento do Acesso Antecipado.

---

## Último passo — tradução (pedido do Sergio, 02/11)
- [ ] Traduzir o jogo inteiro para o **inglês** e para **vários idiomas** (espanhol, chinês simplificado, russo,
  alemão, francês, japonês, coreano, português de Portugal), com tabelas de localização, fontes CJK/cirílico,
  revisão nativa, teste de layout e página da Steam/conquistas traduzidas. Detalhes em `PENDENCIAS_100.md`, seção 11.

## Final — ilha do passeio de barco (pedido do Sergio, 02/11)
- [ ] Ilha circular ao fundo no mar, com muitas árvores e vegetação e uma trilha no meio, como destino do passeio de barco
  (detalhes em `PENDENCIAS_100.md`, seção 12).

## Final — correção de low poly (pedido do Sergio, 02/11)
- [ ] Refazer a fogueira da festa junina (lenha e chamas) sem low poly e revisar os demais props vindos da Godot
  (detalhes em `PENDENCIAS_100.md`, seção 13).

## Final — eventos cômicos e NPCs memoráveis (pedido do Sergio, 31/10, issue #4)
- [ ] Gaivota ladra de batatas, influenciador exigente, cachorro com chinelo, guarda-sol no vento, turista perdido,
  atendente iniciante atrapalhado, Seu Arnaldo e o pescador contador de histórias
  (detalhes em `HUMOR_EVENTOS_COMICOS.md` e `PENDENCIAS_100.md`, seção 14).
