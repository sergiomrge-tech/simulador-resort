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
- [ ] P1 **Pesca no píer** (missão do pescador) e **modo foto (P)** com álbum: destravam os capítulos 2–4 da vila.
- [ ] P1 **Capítulos 2–4 da vila** (fama, foto, receitas, negócios) com contagem real.
- [ ] P1 **Festas e eventos do calendário**:
  - junina, quermesse, DJ, tempestade, maré alta;
  - preparativos pagos, tendas, fogueira, bandeirinhas.
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

- [ ] P1 **Bar do Coqueiro**: drinks por combinação de ingredientes (M8), receitas a descobrir, barman automatiza.
- [ ] P1 **Negócios da vila**, uma tarefa curta cada:
  - pranchas e caiaques;
  - food truck do pastel;
  - sorveteria;
  - lojinha de souvenires;
  - escolinha de surfe.
- [ ] P1 **Piscina**: limpar com a peneira (afeta estrelas), espreguiçadeiras, toalhas, picolé.
- [ ] P1 **Passeios**: vender bilhetes no píer, guiar barco ou trilha do farol com paradas de foto, nota do passeio.
- [ ] P1 **Restaurante do hotel**: atender as mesas, serviço de quarto, eventos (casamento, festa).
- [ ] P1 **Salão de jogos**:
  - partida de sinuca jogada até o fim no jogo;
  - pebolim;
  - 1–2 fliperamas;
  - hóspedes jogando à noite e renda das fichas.
- [ ] P1 Recepção do hotel com a fila de hóspedes visível no saguão.
- [ ] P1 Equipe: contratação, turnos e salários de recepcionista, camareira, barman, guia e garçom do
  restaurante coerentes com as tarefas novas.
- [ ] P2 Pedidos especiais e clientes VIP/influenciador no quiosque (eventos cômicos da tarefa #4).

## 4. Progressão, economia e conteúdo
- [ ] P1 **Balanceamento** jogando do zero até o Grand Hotel:
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
- [~] P0 Calçados: chinelo e tênis feitos (02/11); faltam sandália e sapato social.
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
- [ ] P0 **Controle** (Xbox/PlayStation) em todo o jogo e nos menus. (Tradução: ver a seção 11, no final.)
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
