# Feedback de jogo

## 2026-10-17 — escritório, fechamento do dia e interior do bangalô (v0.3 → v0.4)

Captura: `2026-10-17_escritorio_fechamento_interior.jpg`

> "Letra pequena, muitos espaços vazios, em branco, muito quadrado, móveis sem textura e assets low poly,
> precisa ter assets mais realista estilizado, principalmente da mobília" — Sérgio

O que a v0.4 mudou em resposta:

- **Letra pequena** → tema `scripts/ui_theme.gd` com a fonte Nunito (OFL): corpo 22 px, subtítulos 26 px,
  títulos 36 px na base 1280×720 (33/39/54 px em 1080p, 44/52/72 px em 1440p). Configuração nova
  "Escala da interface" (75–150 %) em Configurações → Vídeo.
- **Espaços vazios / em branco** → o escritório e o fechamento agora têm o tamanho do conteúdo (a área com
  rolagem acompanha a altura do que tem dentro), conteúdo em cartões e grades de 2–3 colunas.
- **Muito quadrado** → painéis com cantos de 14–24 px, sombra suave, cabeçalho de madeira, abas com ícone,
  chips arredondados para saldo, estoque e ganhos; ícones game-icons.net (CC BY 3.0) em abas, insumos,
  melhorias, equipe e categorias do caixa.
- **Móveis sem textura / low poly** → interior do bangalô com modelos PBR da Poly Haven (texturas até 2K):
  cama entalhada (casal → king → king com dossel de voal), criado-mudo pintado, ventilador de teto com pás
  girando, espelho ornamentado, cadeira de balanço, almofadas, quadro, vaso de cerâmica, lamparina,
  planta pachira; piso de tábuas, tapete de tecido, bancada em madeira escura e pedra. Espreguiçadeiras da
  praia em rattan (ambientCG, CC0). Créditos em `CREDITS.md`.
