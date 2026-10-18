# Notas de desenvolvimento — Maré Alta Resort

Godot **4.5.1** (versão padrão, não .NET), Windows como alvo da Steam. O jogo roda em pt-BR e tem localização em inglês.

## Setup

1. Instale o Godot 4.5.1 e o Python 3.8+ com `pillow` e `numpy` (`pip install pillow numpy`).
2. Na raiz do repositório (onde está o `project.godot`):

```bash
./tools/fetch_assets.sh
```

No Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File tools\fetch_assets.ps1`.

O script baixa texturas e modelos CC0 do Poly Haven (~430 MB) para `assets/tex`, `assets/tex_hd`, `assets/models` e `assets/models_hd`, e gera as texturas procedurais (calçada, reboco, folha de coqueiro, ícone). Áudio e o manequim (`assets/models/ual/guest.glb`) já vêm no git. Esses binários baixados ficam de fora do repositório (ver `.gitignore`).

3. Abra `project.godot` no Godot. A primeira importação leva alguns minutos.
4. F5. No menu: Novo jogo. WASD + mouse, E interage, B loja, Shift corre, Esc pausa, F11 tela cheia.

## Teste headless

Com os assets já importados:

```bash
godot --headless --audio-driver Dummy --path . -- --loop-test
```

O ciclo (check-in, estadia, limpeza, rede, save/load, quiosque, dormir, estoque, upgrade de quarto e novo bangalô) imprime `LOOP_TEST PASS` e sai com código 0. Use `user://` de teste (`user://test_save.json`); o save normal do jogador não é apagado.

Os preços, diárias, margens e salários estão só em `scripts/economy.gd`. No jogo, a tecla B abre o escritório (caixa do dia, insumos, melhorias, equipe). O mercadinho fica na padaria da vila; a placa de melhorias fica na lateral de cada bangalô. Dormir mostra o fechamento do dia.

## Exportar para Windows

Instale os export templates **4.5.1** (Editor → Manage Export Templates) e rode, de preferência no Windows ou com os templates de Windows no editor:

```bash
godot --headless --export-release "Windows Desktop" build/win/MareAltaResort.exe
```

Distribua `MareAltaResort.exe` e `MareAltaResort.pck` juntos. A saída fica em `build/` (não versionar). Não commite keystore, `export_credentials.cfg` nem a pasta `.godot/`.
