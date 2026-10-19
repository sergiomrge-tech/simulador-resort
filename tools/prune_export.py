"""Acrescenta ao exclude_filter do export_presets.cfg as pastas de modelos que nenhum script cita (baixadas "por garantia").
Sem isso o .pck passou de 4 GB (limite do NSIS ~2 GB). uso: prune_export.py apply|restore"""
import os, re, sys, glob, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "export_presets.cfg")
BAK = CFG + ".bak"
if sys.argv[1:] == ["restore"]:
    if os.path.exists(BAK):
        shutil.move(BAK, CFG)
    sys.exit(0)
src = "".join(open(f, encoding="utf-8").read() for f in glob.glob(ROOT + "/scripts/*.gd") + glob.glob(ROOT + "/scenes/*.tscn") + glob.glob(ROOT + "/tests/*.gd"))
# v1.0.1: "qnat" (Quaternius: arbustos, samambaias, capim) é citado como caminho ("res://assets/models/qnat/%s.gltf"),
# não como "qnat" entre aspas, e foi excluído do instalador: o jogo instalado mostrava placas redondas no lugar dos arbustos.
skip = {"kenney", "gen", "ual", "ubc", "qnat", "beach"}
ex = []
for base in ("models", "models_hd"):
    b = os.path.join(ROOT, "assets", base)
    for d in sorted(os.listdir(b)):
        used = f'"{d}"' in src or f"'{d}'" in src or f"/{base}/{d}/" in src or f"{base}/{d}" in src
        if os.path.isdir(os.path.join(b, d)) and d not in skip and not used:
            ex.append(f"assets/{base}/{d}/*")
if os.environ.get("LITE") == "1":
    ex += ["assets/models_hd/*", "assets/tex_hd/*"]  # versão leve: sem modelos/texturas HD
shutil.copyfile(CFG, BAK)
s = open(CFG, encoding="utf-8").read()
s = re.sub(r'exclude_filter="([^"]*)"', lambda m: 'exclude_filter="%s, %s"' % (m.group(1), ", ".join(ex)), s, count=1)
open(CFG, "w", encoding="utf-8").write(s)
print("excluidos do pacote:", len(ex), "pastas de modelos sem uso")
