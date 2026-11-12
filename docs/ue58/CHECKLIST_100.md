# Checklist total — o que falta para o jogo ficar 100% (refeito em 12/11/2026)

Pedidos do Sergio (12/11): "faça um checklist total para o jogo ficar 100%, sem a parte da Steam, que é minha; HUD atual
está ok"; depois, com a revisão da campanha e do recife em mãos: "com base em todos esses erros que você achou, refaça
o checklist". Esta é a ordem de trabalho. Histórico do que já foi feito:
[`PLANO_E_CHECKLIST_2026-11-08.md`](PLANO_E_CHECKLIST_2026-11-08.md). Desenho da campanha nova:
[`CAMPANHA_V2.md`](CAMPANHA_V2.md). Levantamento da campanha atual: [`CAMPANHA_MAPA_2026-11-12.md`](CAMPANHA_MAPA_2026-11-12.md).

**Fora desta lista:** Steam (conta, App ID, página, integração, conquistas, nuvem, preço, trailer, Next Fest, playtest),
que é do Sergio; HUD/celular (o atual fica, só entra a linha da dívida); co-op online e Workshop (pós-lançamento).

**Como ler:** `[ ]` falta · `[~]` em andamento · `[?]` listado como aberto em documento antigo e ainda não conferido no
jogo (primeiro conferir; só vira trabalho se reprovar) · 👤 depende do Sergio.
Cada item fecha com portão de QA PASS, foto analisada, commit e push. Pacote só no fim de cada bloco.

**O que a revisão de 12/11 ensinou (vale para todos os blocos):** os testes passavam porque pulavam o caminho do
jogador (`mare.QA step` no lugar da conversa; `mare.Comic` sem ninguém por perto). Um sistema só conta como pronto
quando foi percorrido PELO CAMINHO DO JOGADOR, com prova em imagem, e essa prova vira checagem do portão.

---

## Bloco A — Travas: o jogo não pode ser terminado (corrigir primeiro)

- [~] **A1. Capítulo do carnaval impossível de concluir.** Só avança conversando com a "Prefeita Tuanny", que não existe
  no mundo (a vila cria 5 moradores). Sem ele não abre o fim da demo, o Grand Hotel, a lojinha nem o resto da campanha.
  Código já reconhece a moradora; falta: ponto medido na praça, corpo próprio, entrada em `village_routes.json` e
  `metahumans.json`, foto e conversa testada.
- [ ] **A2. Teste do portão: campanha da demo percorrida CONVERSANDO** com cada morador (sem `mare.QA step`), do barco
  à tela de fim da demo. Reprova se algum `giver` de capítulo não existir como pessoa no mundo.
- [ ] **A3. Checagem de dados no `data_lint`:** todo `giver`, `speaker`, `maker` e nome citado em missão precisa existir
  como pessoa criada pelo jogo (ou estar numa lista explícita de "só citado").
- [ ] **A4. Os dois finais sem ordem** (festa e quitação podem abrir em qualquer sequência, e "Créditos" joga o jogador
  para o menu principal): resolvido pelo final único do Bloco C; até lá, conferir que as duas telas não se atropelam.
- [ ] **A5. Demo instalada (11/11i) tem a trava A1:** reempacotar e reinstalar assim que A1 e A2 passarem.

## Bloco B — Eventos cômicos (prioridade do Sergio: "importante para vender")

Sete eventos existem no código (gaivota ladra de batatas, influenciador exigente, guarda-sol levado pelo vento, turista
perdido, atendente atrapalhado, Seu Arnaldo reclama, pescador e o peixe). O cachorro ladrão de chinelo do desenho
original não existe (cachorros saíram do jogo em 03/11). Os 10 critérios de aceite de `HUMOR_EVENTOS_COMICOS.md` nunca
foram marcados.
- [x] B1. Os 7 eventos filmados no jogo e analisados quadro a quadro (12/11; folhas em `D:/CodexTemp/comicqa`, roteiros de filmagem em `D:/CodexTemp/comicqa/py`). Todos disparam e terminam. Só o guarda-sol e o influenciador têm animação à altura; os outros cinco funcionam com animação fraca.
- [ ] B2. **Gaivota (HUM-001):** asas rígidas (malha parada do começo ao fim); atravessa o tronco e o braço do cliente; o cliente não reage; a batata do prato não diminui.
- [ ] B3. **Atendente atrapalhado (HUM-006):** o corpo inteiro inclina rígido (não é um tropeço); o cabelo descola e a cabeça fica careca durante o giro; os pratos flutuam ao lado das mãos e um atravessa o tronco. Falta ver com o atendente andando com pedido de verdade.
- [ ] B4. **Seu Arnaldo (HUM-007) e Seu Bené (HUM-008) caem em qualquer pedestre:** nas filmagens os dois foram mulheres jovens de vestido. Viram personagens fixos, homens mais velhos com corpo e lugar próprios (Arnaldo entra na campanha, Bloco C).
- [ ] B5. **Gesto que conta a piada** nos quatro eventos de conversa: hoje alternam dois clipes genéricos e a pessoa fica curvada de braços caídos. Turista perdido olhando em volta com um mapa; Arnaldo de braços cruzados, apontando e balançando a cabeça; Bené abrindo as mãos para mostrar o tamanho do peixe, maior a cada conversa; influenciador já tem a selfie.
- [ ] B6. **Guarda-sol (HUM-004):** o dono não corre atrás (só o aviso de texto); conferir a copa que aparece azul caída e amarela em pé.
- [ ] B7. **Influenciador (HUM-002):** contorno amarelo de interação em volta do celular; no primeiro quadro o celular aparece de lado na cintura.
- [ ] B8. **Telas:** o aviso "Dica" e o prompt "E · ..." ficam por cima ou atrás do diálogo aberto.
- [ ] B9. **Sem testar ainda:** as respostas do diálogo e a página de reação (clique nos botões); o comando `mare.Comic` falha em silêncio sem pedestre por perto e o gestor fica preso com diálogo aberto por comando (dar o motivo no log e um comando de QA para responder).
- [ ] B10. Evento novo no lugar do cachorro, e mais variedade para a piada não se repetir.
- [ ] B11. Os 10 critérios de aceite do documento, incluindo 100 ciclos sem travar pessoa, fila ou navegação, pausa, save no meio do evento e presets baixo/alto.
- [ ] B12. Cada evento visto no executável e gravado em clipe para divulgação.
- Achados de roupa nas filmagens (vão para o Bloco E): maiô vermelho com a calcinha azul aparecendo por baixo; vestidos com a faixa da cintura translúcida (branco, amarelo, roxo); cabelo escuro cobrindo o queixo de quem olha para baixo.

### B-novos. Cenas aleatórias novas (ideias de 12/11; o Sergio escolhe quais entram)

Pedido do Sergio (12/11): "aleatoriedade no jogo eu acho muito importante, o jogo não ficar chato". Regras: curtas,
opcionais, sem prejuízo que irrite; quem participa ganha gorjeta, fama ou a risada; sem cachorro, gato nem criança.
Só começam depois de B2–B9 (consertar os sete atuais). ★ = primeira leva sugerida (8).

**Regras de frequência (valem para todos)**
- [ ] Um evento a cada poucos minutos; nunca o mesmo duas vezes no dia; cada lugar (quiosque, praia, vila, hotel) com a sua lista.
- [ ] Personagens fixos (prefeita, Bené, Arnaldo, gaivota) voltam com fala nova a cada vez, em sequência.
- [ ] 👤 Sergio marca quais das 32 ideias entram e quais corta.

**Quiosque**
- [ ] N1. Coco teimoso: escapa rolando pela areia; o jogador pode buscar e devolver.
- [ ] N2. Pedido impossível ("água de coco sem coco"), com três respostas.
- [ ] N3. Casal que não decide: trocam o pedido um do outro; a fila suspira.
- [ ] N4. ★ O freguês do fiado: "põe na conta da Dona Dilce" (liga com a dívida).
- [ ] N5. Siri no balcão: fregueses levantam os pés, o atendente sobe na banqueta.
- [ ] N6. Brinde errado: um copo voa e todos fingem que nada aconteceu.
- [ ] N7. Turista torrado: vermelho, andando duro, pede "qualquer coisa gelada".
- [ ] N8. O sommelier de água de coco: "notas de... coco."

**Praia**
- [ ] N9. ★ Maré na toalha: a onda leva o chinelo e a pessoa corre atrás.
- [ ] N10. Castelo de areia ambicioso: um adulto constrói, outro tropeça.
- [ ] N11. ★ Bola de vôlei perdida: cai na mesa, no mar ou no colo do jogador.
- [ ] N12. Dormiu no sol: acorda com a marca do livro no peito.
- [ ] N13. Fotógrafos do pôr do sol: param tudo às 17h30; quem passa na frente leva bronca.
- [ ] N14. Guarda-sol que fecha sozinho em cima do dono.

**Vila**
- [ ] N15. Procissão do santo errado: o andor entra na rua errada e a vila dá meia-volta.
- [ ] N16. ★ A prefeita inaugura qualquer coisa: corta fita num banco, num poste, numa lixeira.
- [ ] N17. Fofoca em cadeia: a história volta aumentada por outro morador.
- [ ] N18. ★ Seu Bené e Seu Severino discutindo o tamanho do peixe, cada um abrindo mais os braços.
- [ ] N19. Serenata desafinada: a janela fecha.
- [ ] N20. O sino fora de hora: a vila confere o relógio.
- [ ] N21. Bandeirinhas ao vento: o varal enrola num pedestre.

**Hotel**
- [ ] N22. ★ Hóspede de roupão no lugar errado (saguão, restaurante).
- [ ] N23. A mala que abre na recepção.
- [ ] N24. Elevador indeciso: abre, fecha, abre; o hóspede vai de escada.
- [ ] N25. O VIP disfarçado que todo mundo reconhece.
- [ ] N26. Noivos atrasados: o noivo chega correndo pela praia, de terno e descalço.
- [ ] N27. ★ Bombinha na piscina: molha quem lê na espreguiçadeira.
- [ ] N28. Campeão de sinuca: comemora uma tacada como final de campeonato.

**O mar e o tempo**
- [ ] N29. ★ Chuva de verão de cinco minutos: todos correm para um teto; para de repente.
- [ ] N30. Golfinhos ao largo: a praia aponta; vira desafio de foto.
- [ ] N31. Arco-íris depois da chuva.
- [ ] N32. Gaivota no letreiro do quiosque, virando mascote (a mesma da batata).

## Bloco C — Campanha v2 (aprovada em 12/11; contrato em `CAMPANHA_V2.md`)

Defeitos da campanha atual que este bloco resolve: história das 21 missões nunca aparece; dívida escondida no celular,
sem motivo e solta da campanha; ~13 h (65 % do jogo) com uma missão só; hotel sem personagem nem enredo; oferenda
diária obrigatória até o fim do jogo; Dona Dilce nunca aparece; sem epílogo; tratamento inconsistente nas cartas.

**C1. Lógica**
- [~] Etapa da campanha guardada por ID, com migração do save antigo.
- [~] Fila nova (31 missões) e 5 capítulos novos do jogo completo, tipos de passo novos, requisitos de expansão e de dívida.
- [~] Capítulos do jogo completo invisíveis na demo e fora da conta do fim da demo.
- [~] Oferenda delegável ao atendente depois do capítulo do Seu Tibúrcio.
- [~] Cartas da dívida por marco (dados e estado de lidas); festa exige dívida quitada.
- [~] Testes de automação da fila inteira, da demo, da migração e da delegação.

**C2. Textos**
- [x] Piloto (12/11): P.S. da carta, carta de 25 %, capítulo da Dona Roberta, em [`CAMPANHA_TEXTOS_PILOTO.md`](CAMPANHA_TEXTOS_PILOTO.md). Voz aprovada pelo diretor para seguir (P.S. engraçado, cartas de marco ternas com uma piada, morador que "sempre soube"); o Sergio ainda pode pedir ajuste ao ler.
- [x] Lote escrito (12/11): 277 textos com id estável em [`CAMPANHA_TEXTOS_LOTE.md`](CAMPANHA_TEXTOS_LOTE.md) (cartas, 9 capítulos com fala por passo, missões novas e reescritas, roteiro da festa, epílogo, oferenda delegada, nomes dos vendedores). 👤 Sergio lê a carta de 100 % e o roteiro da festa.
- [ ] Passar os 277 textos para os dados do jogo (depois da lógica C1) e conferir cada um na tela.
- [ ] Reescrever o que conflita com o final único (missões `chegada`, `marealta`, `fregueses`, `festa`, falas da festa, tela final, créditos).
- [ ] Tratamento único "Meu bem" (hoje: "Meu neto", "Meu bem", "Bem-vinda, bem-vindo", "Vó"/"Vovó").
- [ ] Tradução nos 12 idiomas, glossário e auditoria no executável.

**C3. Telas**
- [ ] História (`story`) da missão atual e das concluídas no celular.
- [ ] Linha do saldo da dívida no HUD (só depois de lida a carta).
- [ ] Cartas dos marcos em folha de caderno, relegíveis no celular; P.S. na carta da casa.
- [ ] Falas em todos os passos dos capítulos e despedidas variadas.
- [ ] Festa + quitação num final só; créditos abrem ali, sem sair para o menu.
- [ ] Opção da oferenda no celular (Equipe).
- [ ] "Sonhos da vila" depois do final.
- [ ] Recompensa de missão: hoje só entra ao tocar "Concluir" no celular e o HUD mal avisa; tornar o aviso claro.

**C4. Pessoas e lugares (editor)**
- [ ] Prefeita Tuanny de **terno ou roupa social** (Sergio, 12/11: "em um cargo executivo, precisa de roupa adequada"): procurar entre as roupas já baixadas e as gratuitas do Fab; senão gerar a peça.
  12/11: nenhuma das 12 roupas baixadas é social e não há roupa social gratuita para MetaHuman no Fab (todas pagas, R$ 28–110 na busca). 👤 Sergio decide: comprar um conjunto feminino e um masculino paramétricos, ou piloto de terninho gerado aqui. Roupa de senhora para a Dona Dilce não apareceu nem paga: sai gerada.
- [ ] Prefeita Tuanny na praça (A1) e depois na **prefeitura** (prédio novo na vila; decisão do Sergio em 12/11).
- [ ] Seu Arnaldo como morador (quiosque; depois restaurante do hotel).
- [ ] Dona Dilce: levantar se há corpo de senhora idosa; cena da chegada de barco; lugar no hotel e no quiosque.
- [ ] Peças ligadas aos capítulos: redes da pousada, facho do farol aceso, placa do Arnaldo, quarto com vista.
- [ ] Fala nova de cada morador depois da carta que o cita.

**C5. Limpeza do que está morto ou prometido sem existir**
- [~] Dados sem uso: `definitions.json → quests`, `debt.json → campaign_texts`, promessas "dica da moqueca" e "Prainha do Oeste aberta".
- [ ] Decidir o destino do que sobrou sem consumidor: metas semanais e árvore herdadas do Godot, `credits.json`, `intro_bus.json`, efeito "fogos do vulcão" da festa (o vulcão saiu do mapa).
- [ ] Documentos que contradizem o jogo: `DIVIDA_DA_AVO.md`, `BALANCEAMENTO.md` e `debt.json` (dizem que a dívida não está implementada), `ABERTURA_UMA_NOVA_MARE.md` (ônibus e avô), fama do hotel (comentário diz 8, dado diz 9), nome antigo do jogo em `credits.json` e `CHECKLIST_EXPANSOES.md`.
- [ ] Vendedores dos negócios se chamam todos "Vendedor": dar nome a cada um.

**C6. Demo**
- [ ] Missão `parcela` (primeiro pagamento) ensina a tela da dívida dentro da demo.
- [ ] Depois do fim da demo o jogador fica sem objetivo no HUD: mostrar o que ainda dá para fazer.
- [ ] Primeiro dia sobrecarregado (carta, celular, empresa, dívida, placa e ~55 dicas de 14 s): rever a ordem e o ritmo das dicas com a carta nova.
- [?] A casa aparece na bússola? (o único aviso de onde está a carta é o texto do HUD.)
- [ ] Demo jogada do zero pelo caminho do jogador e cronometrada (~2,7 h).

**C7. Prova**
- [ ] Modelo de balanceamento rodado com a fila nova: 20 h mantidas, maior trecho sem missão nova ≤ ~10 dias de jogo.
- [ ] Campanha inteira no executável do jogo completo, do barco à festa, pelo caminho do jogador.

## Bloco D — Recife

Medido em fotos (12/11): os 97 peixes são pontinhos quase invisíveis e de desenho; a água é transparente até o fim da
areia, com uma faixa azul chapada depois; os corais são pastel liso, com cara de plástico; na vista para a costa há um
degrau reto na areia e um objeto listrado vermelho e azul boiando.
- [x] D1. Três peixes realistas modelados e aprovados (palhaço, cirurgião-azul, sargentinho); a sardinha já existia.
- [~] D2. Nado de cardume: ~500 peixes, apontando para onde nadam, fugindo do nadador; ondulação do corpo no material (GPU).
- [~] D3. Névoa de distância da água ligada à câmera de mergulho (compilada; falta fotografar e calibrar).
- [ ] D4. Importar os peixes, ligar o nado, fotografar de perto e de longe; snorkel guiado continua achando as 4 espécies.
- [ ] D5. Corais com superfície de verdade (texturas reais de coral do Poly Haven; remodelar as formas que continuarem com cara de plástico).
- [ ] D6. Degrau reto na areia visto do recife para a costa; identificar e corrigir o objeto listrado boiando.
- [ ] D7. Horizonte: relevo distante e cardumes ao longe, depois da névoa calibrada.
- [ ] D8. Os 8 peixes da pesca têm a cor gravada errada (convertida duas vezes: mais escura e puxada para o vermelho): corrigir no gerador e refazer as figuras do livro.
- [ ] D9. Passeio de snorkel do início ao fim no executável, com medição de FPS.

## Bloco E — Pessoas

- [ ] E1. Cabelo comprido de quem senta fica rígido no nível Alto: reduzir a inclinação da cabeça nas poses sentadas (a física foi descartada: custa ~12 FPS).
- [ ] E2. Vestir os papéis que faltam com as 11 roupas gratuitas já baixadas.
- [ ] E3. Calçados variados; ninguém descalço fora da areia.
- [ ] E3b. Maiô com a roupa de baixo aparecendo; vestidos do Fab com a cintura translúcida; cabelo cobrindo o queixo de quem olha para baixo (vistos nas filmagens dos eventos, 12/11).
- [ ] E4. Camiseta azul-escura da Dona Roberta parece lisa na sombra; biquínis conferidos de perto.
- [ ] E5. Casal da mesa do restaurante do hotel inclina o tronco demais.
- [?] E6. Conversa em pé com gesto melhor; variedade de moradores e turistas sem a mesma pessoa lado a lado.
- [ ] 👤 E7. Crianças e famílias: comprar pacote pago ou seguir sem.

## Bloco F — Cenário

- [ ] F1. Casa do jogador: calçada de cimento em volta e caixa do relógio com cara de medidor.
- [ ] F2. Farol: faixa lisa da encosta acima das pedras; um dos modelos de pedra sai quase preto.
- [ ] 👤 F3. Igreja: pilares listrados ou em um mármore só.
- [ ] F4. Móveis e louças do Fab baixados e sem uso: usar ou apagar do projeto.
- [?] F5. Props do Godot ainda em low poly (fogueira junina e outros); toalha da cama do bangalô; fila visível na recepção do hotel.

## Bloco G — Jogabilidade que ainda não existe

- [ ] G1. Horário de pico próprio por expansão (manhã quiosque e piscina, tarde passeios e negócios, fim de tarde bar, noite restaurante e salão).
- [ ] G2. Preparativos de festa comprados na véspera aparecem no mapa.
- [?] G3. Festas e eventos do calendário conferidos um a um, com foto; hoje nenhuma festa tem texto de história.
- [?] G4. Equipe rende menos que o jogador fazendo pessoalmente; personalização com 5 opções em tudo; dica de primeira vez em cada sistema.
- [ ] G5. Subir de fama não tem tela nem recompensa, só uma mensagem: dar um momento a cada nível.
- [ ] G6. VIPs, crítico e eventos do hotel são só operação, sem rosto: ligar ao capítulo do Arnaldo e ao do quarto (Bloco C).

## Bloco H — Ilha viva (parte de trás da ilha reservada para estas construções)

Ordem proposta, do mais barato para o mais caro; cada uma pode virar expansão paga com capítulo próprio.
- [ ] H1. Pontos de parada nas trilhas: mirante na Trilha Norte, banco com vista na Oeste, placas.
- [ ] H2. Turistas e moradores nas trilhas e nas praias novas (estender a navegação).
- [ ] H3. Passeio de barco de volta completa à ilha.
- [ ] H4. Praia norte com uso: pesca de praia, coleta de cocos e conchas, quiosque secundário.
- [ ] H5. Estátua original de braços abertos no morro. Sistema grande: subir o esforço do modelo antes.
- [ ] H6. Casa do herói com 1 andar. Sistema grande: subir o esforço do modelo antes.

## Bloco I — Prova final e fechamento

- [ ] I1. Simulação do jogo completo do zero até a festa (0 erros no log, 0 pessoas deslizando, 0 fora do assento, save recarregado idêntico), sem atalhos de teste nos pontos em que o jogador conversa, compra ou paga.
- [ ] I2. Cada expansão do jogo completo jogada uma vez no executável.
- [ ] I3. Pente fino visual do mapa inteiro, de dia e de noite.
- [ ] I4. Áudio: mixagem medida com os sons novos; toda ação com efeito sonoro.
- [ ] I5. Traduções: auditoria no executável nos 12 idiomas; layout com alemão e russo.
- [ ] I6. Saves: versão antiga, backup antes de gravar, 3 slots.
- [ ] I7. Desempenho no pacote final (Padrão e Baixo, 5 setores) e teste longo.
- [ ] I8. Créditos conferidos contra todos os assets de terceiros; `credits.json` ligado à tela ou removido.
- [ ] I9. Pacote Shipping do **jogo completo** (hoje só a demo é empacotada): QA do executável, abertura, tamanho.
- [ ] I10. Limpeza do repositório: `todo_*.json` soltos, documentos antigos marcados como histórico.

## Bloco J — Só o Sergio 👤 (fora a Steam)
- [ ] Roupa social da prefeita: comprar no Fab ou gerar (ver C4).
- [ ] Escolher quais das 32 cenas aleatórias entram (bloco B-novos).

- [ ] Julgar a voz do piloto dos textos da campanha (C2).
- [ ] Ouvir o órgão numa missa (7h–8h ou 17h30–19h): timbre e volume.
- [ ] Pintura do teto da recepção do hotel: o traço está como queria?
- [ ] Rodar a demo num PC sem a Unreal.
- [ ] Controle físico (Xbox/PlayStation) no executável.
- [ ] Geração de quadros do DLSS (clicando na janela durante o teste).
- [ ] Traduções: revisão nativa; transliterar nomes próprios em chinês, japonês e russo; mais idiomas?
- [ ] Qual é o som ambiente "que não muda nem desliga" do teste da demo.
- [ ] Confirmar o nome "Coconut Simulator".
