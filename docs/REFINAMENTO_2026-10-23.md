# Revisão visual e gestão — 23/10/2026

Linha 1.1.0 RC2, Godot 4.5.1, branch codex/resort-1.1-mcp.
Esta revisão responde às nove capturas enviadas pelo usuário e inclui os pássaros.

## Mudanças

- Notebook **Classic Laptop**, Poly Haven CC0, substitui o computador simplificado
  e o caixa azul do balcão. Tela física mostra nome, abertura, caixa e contas reais;
  E abre a gestão e B continua restrito à proximidade. Não existe acesso remoto.
- Seis abas fixas: Quiosque, Compras, Equipe, Finanças, Resort e Vila e lazer.
  Cabeçalhos menores; botões reservam largura para o texto, sem cartões esticados.
  Removidos a barra inferior de celular e o contorno roxo. Cantos arredondados mantidos.
- Compras abre na reposição dos **produtos vendidos**: disponibilidade, custo real e
  botão Repor para 10. Compra imediata dos insumos faltantes, sem formulário prévio
  de fornecedor, sem preparo e sem cobrança repetida quando já abastecido.
  Contratos/entregas e reposição automática continuam como opções secundárias.
- Equipe mostra funções disponíveis, com candidatos e salários legíveis. Cozinheiro
  não contratado não é oferecido no fluxo sem preparo; saves antigos são preservados.
- Suporte de promoções com folhas e textos acompanhando a inclinação das duas faces;
  valores continuam ligados ao preço atual dos produtos.
- Removido sorteio de penteado vazio; cabelo longo recebe cobertura de topo presa ao
  osso da cabeça. Escala de cabeça mais discreta, sem óculos, chapéus ou bonés.
- Rotas distribuídas por toda a vila, incluindo a rua de trás, mantendo 12 pedestres
  em HD/5 em baixa. Posições iniciais e chegada à casa mantêm margem do corpo junto
  às paredes. Não remover a exceção de chegada a mesas dos clientes.
- Ruas usam a textura original de pedras em escala menor, vasos junto às fachadas e
  remoção de palmeiras aleatórias dentro da área construída da rua de trás.
- Gatos e cães preservam os rigs e os clipes Idle/Walking do Quaternius. Malha
  suavizada, olhos/íris/pupilas/brilhos, focinho, boca e bigodes dos gatos seguem a
  cabeça. Fazem passeios curtos por trajetos livres, alternando descanso/caminhada;
  pés acompanham o chão e pausa congela movimento e animação.
- Pássaros suaves de dia perto das árvores; detalhes em [PASSAROS.md](PASSAROS.md).

## Assets reproduzíveis

PC: https://polyhaven.com/a/classic_laptop — autor Arrangemonk, CC0.
Licença: https://docs.polyhaven.com/en/faq?q=commercial .
Fonte empacotada e reaberta: art/blender/kiosk_laptop.blend.
Importador: tools/import_counter_laptop.py; GLB kiosk_laptop e mapas importados.

Animais: Quaternius Animal Pack Vol.2, CC0, fonte já usada no projeto.
https://opengameart.org/content/animated-animales-low-poly
Gerador tools/refine_living_animals.py, fontes cat_living.blend/dog_living.blend
com rigs e materiais preservados. Fontes originais baixadas pelo gerador se ausentes.
`fetch_assets.py` registra a recuperação do notebook e dos animais refinados.
O catálogo está em ITENS.md/itens.json; não renumerar códigos.

## Validação

APPDATA separado em build/qa, sem acessar ou apagar saves reais. Runner rejeita
qualquer ERROR, recurso ausente, FAIL ou saída diferente de zero.

`--loop-test --refinement-test` cobre compra com valor exato, reposição repetida,
seis abas, largura/altura de botões/cartões de equipe, tela física, cinco animais
com caminhada alterando ossos, deslocamento e pausa, destinos de casa seguros e
chegada dos nove moradores noturnos. Captura notebook, promoções frente/verso,
compras/equipe, gatos/cães, cabelo e rua para inspeção visual.

Executar também terminal, counter-first, company, practical, phone-layout e birds
na fonte e no PCK. Phone-layout verifica todas as páginas em 1280×720, 800×600 e
360×640. Birds inspeciona a mixagem real, não apenas o estado de reprodução.
Resultados finais e logs na pasta docs/qa/refinamento-2026-10-23.

## Limites preservados

A direção artística das pessoas e animais continua estilizada. Não houve troca
completa dos corpos/rigs. Não foi aumentado o limite de NPCs. Caminhada dos animais
é local, não um sistema de navegação da vila inteira. Entregas agendadas e contratos
continuam disponíveis para quem quiser usar o fluxo avançado. Esta revisão não
reinicia progressão nem substitui saves do jogador.


## Resultado desta entrega

**14 execuções com PASS e saída 0:** refinement, terminal, counter-first, company,
practical, phone-layout e birds, em fonte e no executável exportado. Zero ERROR,
recurso ausente ou FAIL nos logs finais. Capturas do PCK inspecionadas: computador,
compras/equipe, promoções dos dois lados, gato/cão, penteado e rua.

O teste novo verificou alteração real dos ossos durante Walking dos cinco animais,
deslocamento e pausa; os nove moradores noturnos chegaram às entradas. Phone-layout
conferiu todas as páginas nas três resoluções. Fontes .blend empacotadas foram
reabertas e verificadas pelos importadores/geradores. Detalhes e hashes em
[resultado.json](qa/refinamento-2026-10-23/resultado.json).

Download da revisão: https://github.com/sergiomrge-tech/simulador-resort/releases/tag/v1.1.0-rc2.20261023-refinado .
ZIP: MareAltaResort_1.1_RC2_Refinado_2026-10-23.zip. Extraia inteiro e abra Jogar.vbs.
Preserve userdata/ ao atualizar. A release anterior continua disponível.
