# Instalador Windows

1. Exporte: `godot --headless --path . --export-release "Windows Desktop" build/win/MareAltaResort.exe`
2. Copie `build/win/MareAltaResort.exe`, `MareAltaResort.pck`, `icon.ico` e um `LEIA-ME.txt` para esta pasta.
3. `makensis setup.nsi` → `Instalar_MareAltaResort_vX.exe`

Instala em `D:\Games\MareAltaResort` (ou `%LOCALAPPDATA%\Programs` se não houver D:), sem pedir admin.
O atalho abre `Jogar.vbs`, que guarda saves/config/cache em `userdata\` dentro da pasta do jogo.
