#!/bin/bash
# Gera um PATCH de atualização (só os arquivos que mudaram desde uma versão instalada) + instalador NSIS pequeno.
# uso: tools/build_patch.sh <commit_base>   ex.: tools/build_patch.sh 477454d   (v0.9.2)
# O patch vira patch_<VER>.pck ao lado do jogo; installer/patch_loader.gd (autoload via override.cfg) monta todos os patch_*.pck.
set -euo pipefail
cd "$(dirname "$0")/.."
BASE=${1:?commit base}
GODOT=${GODOT:-/home/claude/godot/godot}
STAGE=${STAGE:-/home/claude/inst/patch}
PYTHON=${PYTHON:-python3}
MAKENSIS=${MAKENSIS:-makensis}
VER=$(grep -m1 '^config/version=' project.godot | sed 's/.*"\(.*\)".*/\1/')
BASEVER=$(git show "$BASE:project.godot" | grep -m1 '^config/version=' | sed 's/.*"\(.*\)".*/\1/')
echo "== patch $BASEVER -> $VER =="
FILES=$("$PYTHON" tools/patch_files.py "$BASE")
N=$(echo "$FILES" | grep -c . || true)
echo "arquivos alterados: $N"
LIST=$(echo "$FILES" | sed 's/^/"res:\/\//; s/$/"/' | paste -sd, -)
cp export_presets.cfg export_presets.cfg.patchbak
trap 'mv -f export_presets.cfg.patchbak export_presets.cfg' EXIT
OPTS=$(sed -n '/^\[preset.0.options\]/,$p' export_presets.cfg | tail -n +2)
cat >> export_presets.cfg <<EOC

[preset.1]

name="Patch"
platform="Windows Desktop"
runnable=false
advanced_options=false
dedicated_server=false
custom_features=""
export_filter="resources"
export_files=PackedStringArray($LIST)
include_filter=""
exclude_filter=""
export_path="build/patch/patch.pck"
patches=PackedStringArray()
encryption_include_filters=""
encryption_exclude_filters=""
seed=0
encrypt_pck=false
encrypt_directory=false
script_export_mode=2

[preset.1.options]

$OPTS
EOC
mkdir -p build/patch "$STAGE"
rm -f build/patch/patch_*.pck
"$GODOT" --headless --path . --export-pack "Patch" "build/patch/patch_${VER}.pck" 2>&1 | tail -2
ls -la "build/patch/patch_${VER}.pck"
cp "build/patch/patch_${VER}.pck" installer/patch_loader.gd installer/patch.nsi installer/icon.ico "$STAGE/"
(cd "$STAGE" && "$MAKENSIS" -V2 -DVER="$VER" -DBASE="$BASEVER" patch.nsi)
ls -la "$STAGE/Atualizar_MareAltaResort_v${VER}.exe"
