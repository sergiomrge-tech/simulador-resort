#!/bin/bash
# Capturas de tela com renderização por software (lavapipe/llvmpipe) via xvfb, com timeout por captura.
# uso: ./shot.sh [nome...]   (padrão: todas)
cd "$(dirname "$0")"
GODOT=${GODOT:-$HOME/.local/bin/godot}
NAMES=${@:-entrada recepcao piscina bangalo interior bar praia noite}
mkdir -p shots
for n in $NAMES; do
  rm -f shots/$n.png
  timeout -k 5 ${TMO:-150} xvfb-run -a -s "-screen 0 1280x720x24" $GODOT --path . --rendering-driver vulkan --rendering-method ${RENDER:-mobile} --resolution ${RES:-1280x720} -- --shot=$n $EXTRA > shots/$n.log 2>&1
  if [ -f shots/$n.png ]; then echo "OK $n"; else echo "FAIL $n (rc=$?)"; tail -5 shots/$n.log; fi
done
