#!/usr/bin/env bash
# Baixa os assets CC0 (Poly Haven) e gera as texturas procedurais. Linux/macOS/Git Bash.
set -e
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}
command -v $PY >/dev/null || { echo "Python 3 não encontrado"; exit 1; }
$PY -c "import PIL, numpy" 2>/dev/null || $PY -m pip install --user pillow numpy
$PY tools/fetch_assets.py "$@"
