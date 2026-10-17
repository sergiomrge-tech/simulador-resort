# Maré Alta Resort 🌴

Um simulador de pousada em primeira pessoa numa **vila de pescadores do Nordeste brasileiro**, feito em **Godot 4.5.1** para PC (Windows, pensado para a Steam).

Você mora numa casinha da vila e acorda às 06:30. Desce pela calçada de pedra portuguesa até o **Quiosque Maré Alta** na praia para servir coco gelado, caipirinha e petiscos, e ainda ajuda na **Pousada Maré Alta**: check-in na recepção, limpeza dos bangalôs, bar e redes. Depois das 20:00 você volta para casa e dorme; o dia avança e o jogo salva.

## Recursos
- **Gráficos (Forward+):**
  - SDFGI, SSIL, SSR, SSAO, neblina volumétrica e glow
  - sombras suaves 4096, TAA + MSAA e FSR 2
  - texturas até **2K**; o preset Ultra é o padrão
- **Mundo:**
  - pousada com piscina (cáusticas), bangalôs, bar de praia e mar com espuma e refração
  - vila com rua de paralelepípedo, casas coloniais coloridas, igreja com sino, praça, padaria, barraca de praia, jangadas e postes que acendem à noite
- **Interiores (v0.4):** bangalôs mobiliados com modelos PBR realistas-estilizados (Poly Haven, até 2K): cama entalhada com dossel de voal, ventilador de teto, espelho ornamentado, cadeira de balanço, almofadas, quadro, lamparina e plantas; cada melhoria muda o quarto de forma visível.
- **Interface (v0.4):** fonte Nunito grande e legível em 1080p/1440p, painéis arredondados em tons de areia e madeira, ícones, escritório e fechamento do dia em cartões; escala da interface ajustável (75–150 %). Menus de pausa, configurações e o cartão de check-in da recepção usam o mesmo tema.
- **Praia e quiosque (v0.5.1):** sombrinhas redondas de tecido listrado (gomos que cedem, varetas e franja) e algumas de palha; areia bege clara com ondulação; areia molhada na linha d'água, arrebentação, espreguiçadeiras e quiosque com balcão, banquetas, lousa e petiscos.
- **Hóspedes (v0.7.0):** corpos MakeHuman (CC0, hm08) com pele, olhos, cabelo e roupa, no esqueleto humanóide do Quaternius UAL (CC0). Andar, correr, sentar, nadar, conversar, beber e comer continuam nos mesmos clipes. Piscar, LOD por distância. Sem Mixamo. Gere de novo com `python3 tools/gen_people.py` (Blender 4.x).
- **Vila (v0.6):** casas coloniais de reboco pastel com beiral de telha, venezianas, floreiras e buganvílias; calçada de pedra portuguesa com meio-fio; igreja e praça; padaria/mercadinho ligado aos insumos; barcos de pesca, redes e caixotes; casa do herói mobiliada como os bangalôs; moradores que contornam as casas; janelas e postes acesos à noite.
- **Serra (v0.6.5):** a crista de trás também é floresta, verde-azulada na distância. A copa é oliva, sem roxo e sem o domo de pedra.
- **Vida:** hóspedes com rotina (fila, quarto, piscina, bar, check-out), moradores andando pelas calçadas e clientes no quiosque.
- **Pronto para Steam:**
  - menu principal, 3 slots de save e pausa
  - configurações completas: vídeo, áudio (Master/Música/Efeitos), controles com troca de teclas, FOV, sensibilidade
  - controle (gamepad) e **PT-BR / English**
- Plano de lançamento na Steam em [`docs/STEAM_PLAN.md`](docs/STEAM_PLAN.md) e design do jogo em [`docs/GDD.md`](docs/GDD.md).

## Como rodar a partir do código
1. Instale o **Godot 4.5.1** (versão padrão, não .NET) e o **Python 3** (com `pip`).
2. Baixe os assets CC0. Eles não ficam no repositório por serem grandes, ~430 MB.
   - Linux/macOS/Git Bash: `./tools/fetch_assets.sh`
   - Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File tools\fetch_assets.ps1`

   O script baixa texturas e modelos do Poly Haven nos caminhos exatos (`assets/tex`, `assets/tex_hd`, `assets/models`, `assets/models_hd`) e gera as texturas procedurais. O áudio e o manequim (Quaternius) já vêm no repositório.
3. Abra o `project.godot` no Godot. A primeira importação leva alguns minutos.
4. Aperte **F5**.

### Exportar para Windows
Instale os *export templates* 4.5.1 e rode:
```
godot --headless --export-release "Windows Desktop" build/win/MareAltaResort.exe
```
Distribua `MareAltaResort.exe` e `MareAltaResort.pck` juntos.

### Testes
```
godot --headless --path . -- --loop-test      # ciclo completo: check-in, estadia, limpeza, loja, save, quiosque, dormir
./shot.sh vila                               # captura de tela (xvfb); ./shot_fp.sh usa Forward+/Ultra
```

## Controles
| Ação | Teclado/mouse | Controle |
|---|---|---|
| Andar / olhar | WASD / mouse | analógico esquerdo / direito |
| Interagir | E | A |
| Escritório (caixa, insumos, melhorias, equipe) | B | Y |
| Correr | Shift | L3 |
| Pausa | Esc | Start |
| Tela cheia | F11 | — |

## Estrutura
```
scripts/   GDScript: core (economia/save), world + world_village (mundo procedural), guests, village_life,
           player, hud, menus, quality (configurações), i18n, audio, daycycle
shaders/   oceano, piscina e cáusticas, areia, folhagem, hóspedes
tests/     loop_test.gd
tools/     fetch_assets.* e geradores de textura (Python)
docs/      GDD.md, STEAM_PLAN.md, DEV_NOTES.md, feedback/ (capturas e respostas ao feedback)
assets/    fonts/ (Nunito, OFL) e ui/icons/ (game-icons.net) ficam no git; texturas e modelos vêm do fetch
```

## Licenças
- **Código:** © Sérgio Cancella. Todos os direitos reservados, a menos que um arquivo `LICENSE` diga outra coisa.
- **Assets de terceiros:** CC0, exceto a fonte Nunito (SIL OFL 1.1) e os ícones do game-icons.net (CC BY 3.0). Veja [`CREDITS.md`](CREDITS.md).
