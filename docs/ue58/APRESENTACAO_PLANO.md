# Plano: apresentação do jogo (abertura e tela inicial), 07/11/2026

Pedido do Sergio, depois de jogar a demo: "início travado sem abertura, precisa ter uma tela inicial";
"o menu inicial já é a tela do jogo".

## O que existe hoje

- Ao abrir o .exe, o mundo carrega e o menu (uma folha de caderno pequena) aparece por cima do jogo **pausado**, com
  uma película escura de 55%. Parece o jogo travado, não uma tela de título.
- Não há logo, música de abertura, nem transição: "Novo jogo" solta direto na cena do ônibus (`AMareIntro`).
- A carta da avó só aparece dentro da casa.

## Fluxo proposto

1. **Abertura do logo (4 s, pular com qualquer tecla).** Fundo preto, o logo do jogo surge com o som das ondas.
   Também cobre o carregamento do mapa: o jogador não vê o mundo congelado.
2. **Tela de título viva.**
   - O mundo NÃO fica pausado: uma câmera lenta passeia pela baía (praia, quiosque, farol, pôr do sol) por um
     trajeto fixo, sem HUD, sem o herói e com as pessoas andando normalmente.
   - O logo fica no alto à esquerda, com o selo "DEMO", e o menu no estilo caderno em coluna, à esquerda:
     Continuar / Novo jogo / Carregar / Opções / Créditos / Sair.
   - Música própria (uma faixa do rádio escolhida como tema) e, primeiro, "Aperte qualquer tecla".
   - A versão e a "Lista de desejos na Steam" ficam no rodapé.
3. **Abertura da história (Novo jogo, ~40 s, pular com Esc).**
   - 5 quadros ilustrados, no estilo cartão-postal ou álbum, com legenda curta:
     (1) Dona Dilce no quiosque antigo;
     (2) a carta: "o quiosque é seu";
     (3) o ônibus na estrada da costa;
     (4) a vila vista da janela;
     (5) o letreiro "Maré Alta".
   - Depois, a cena do ônibus que já existe, com a câmera cinematográfica.
   - A revelação do R$ 1.000.000 continua na carta depois de criar a empresa (já está no código da dívida).
4. **Tela de carregamento** (Novo jogo, Carregar e voltar ao menu): arte, uma dica e uma barra, em vez de tela
   preta ou mundo parado.

**Nome decidido (Sergio, 07/11): "Coconut Simulator"** (logo, título, Steam). "Maré Alta" segue como o resort dentro do jogo.

## O que vem do Canva

- O logo (PNG com fundo transparente, "Coconut Simulator", com e sem o selo DEMO).
- Os 5 quadros da abertura e 2 fundos de carregamento, em 1920×1080, exportados do design (a prévia
  `generate-image` sai com só ~200 px; para resolução cheia, exportar o design).
- O mesmo logo serve à cápsula da Steam e ao trailer.
- O que for gerado por IA entra nos créditos, sem citar ferramentas de texto (regra de 07/11).

## Parte técnica (C++)

- `SMareTitleScreen` substitui o uso do `SMareMainMenu` no início (que continua sendo o menu de pausa e de Opções),
  em `MareNotebookStyle`.
- `AMareTitleCamera`: trajeto de câmera no mundo, lido de `Content/Data/title.json` (pontos, tempo e hora do dia
  fixa no pôr do sol).
- `SMareStoryIntro` mostra os quadros (texturas em `/Game/UI/Intro`, incluídas em DirectoriesToAlwaysCook) com
  movimento lento e legenda traduzível.
- Checagens do QA: a tela de título aparece sem o jogo pausado; Esc pula a abertura; o Novo jogo chega à cena do
  ônibus; e foto de cada tela.

## Ordem

1. Logo e quadros no Canva (decidir o nome e o estilo antes).
2. Tela de título e câmera.
3. Abertura da história.
4. Tela de carregamento.
5. Novo .exe e instalação em `D:\Games\MareAltaResort_Demo`.
