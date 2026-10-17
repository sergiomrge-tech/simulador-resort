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
| Loja | B | Y |
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
docs/      GDD.md, STEAM_PLAN.md
```

## Licenças
- **Código:** © Sérgio Cancella. Todos os direitos reservados, a menos que um arquivo `LICENSE` diga outra coisa.
- **Assets de terceiros:** todos CC0. Veja [`CREDITS.md`](CREDITS.md).
