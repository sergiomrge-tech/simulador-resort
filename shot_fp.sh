#!/bin/bash
# Capturas Forward+ (qualidade Ultra) via lavapipe — lento (~5-7 min cada). Saída: shots/fp/<nome>.png
cd "$(dirname "$0")"
mkdir -p shots/fp
one() {
  n=$1
  rm -f shots/fp/$n.png
  timeout -k 5 ${TMO:-600} xvfb-run -a -s "-screen 0 1280x720x24" $HOME/.local/bin/godot --path . --rendering-driver vulkan --rendering-method forward_plus --resolution ${RES:-960x540} -- --shot=$n --quality=3 --out=res://shots/fp/$n.png > shots/fp/$n.log 2>&1
  [ -f shots/fp/$n.png ] && echo "OK $n" || echo "FAIL $n"
}
export -f one
printf "%s\n" ${@:-vila praca casa quiosque noite_vila aerea interior piscina menu bar entrada} | xargs -P ${PAR:-2} -I{} bash -c 'one {}'
echo ALL_DONE
