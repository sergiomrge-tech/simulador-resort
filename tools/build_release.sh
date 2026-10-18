#!/bin/bash
# Gera o instalador do Maré Alta Resort a partir do repositório limpo.
# uso: tools/build_release.sh [--sem-smoke]
# Passos: baixa os assets CC0 (não ficam no git) -> importa -> confere -> exporta -> smoke test -> makensis.
set -euo pipefail
cd "$(dirname "$0")/.."
GODOT=${GODOT:-/home/claude/godot/godot}
STAGE=${STAGE:-/home/claude/inst}
VER=$(grep -m1 '^config/version=' project.godot | sed 's/.*"\(.*\)".*/\1/')
echo "== Maré Alta Resort v$VER =="

echo "-- 1/6 assets"
python3 tools/fetch_assets.py

echo "-- 2/6 importar"
timeout 1800 "$GODOT" --headless --path . --import >/dev/null 2>&1 || true
python3 tools/vram_textures.py
timeout 3600 "$GODOT" --headless --path . --import >/dev/null 2>&1 || true

echo "-- 3/6 conferir arquivos que o jogo precisa"
faltando=0
for f in assets/tex/coast_sand_01_diff.jpg assets/tex/rock_face_diff.jpg assets/tex/canopy_diff.jpg \
         assets/tex/blue_floor_tiles_01_diff.jpg assets/models/GothicBed_01/GothicBed_01.gltf \
         assets/models/ubc/Superhero_Male_FullBody.gltf assets/models/ual/guest.glb; do
  if [ ! -f "$f" ]; then echo "FALTA: $f"; faltando=1; fi
done
[ "$faltando" = 0 ] || { echo "Abortado: asset faltando. Rode tools/fetch_assets.py e confira a rede."; exit 1; }

echo "-- 4/6 exportar"
mkdir -p build/win
rm -f build/win/MareAltaResort.exe build/win/MareAltaResort.pck
"$GODOT" --headless --path . --export-release "Windows Desktop" build/win/MareAltaResort.exe 2>&1 | tail -3
[ -f build/win/MareAltaResort.pck ] || { echo "Abortado: exportação não gerou o .pck"; exit 1; }

if [ "${1:-}" != "--sem-smoke" ]; then
  echo "-- 5/6 smoke test (vila): nenhum 'not found' no log"
  rm -f shots/smoke.png
  timeout -k 5 400 xvfb-run -a -s "-screen 0 1280x720x24" "$GODOT" --path . --rendering-driver vulkan --rendering-method mobile \
    --resolution 1280x720 -- --shot=vila > shots/smoke.log 2>&1 || true
  n=$(grep -c "not found\|SCRIPT ERROR" shots/smoke.log || true)
  [ "$n" = 0 ] || { echo "Abortado: $n erros no log (shots/smoke.log)"; grep "not found\|SCRIPT ERROR" shots/smoke.log | sort -u | head; exit 1; }
fi

echo "-- 6/6 instalador"
mkdir -p "$STAGE"
cp build/win/MareAltaResort.exe build/win/MareAltaResort.pck "$STAGE/"
cp installer/setup.nsi installer/Jogar.vbs installer/icon.ico installer/LEIA-ME.txt "$STAGE/"
(cd "$STAGE" && makensis -V2 setup.nsi)
ls -la "$STAGE/Instalar_MareAltaResort_v${VER}.exe"
