"""Troca as texturas baixadas (assets/models*, assets/tex*) de 'lossless' para VRAM comprimido com mipmaps.
Sem isso a GPU guarda tudo sem compressão (RGBA 8 bits): dezenas de GB nos modelos 2k e estouro de memória.
Rode DEPOIS de `godot --headless --import` (ele cria os .import) e rode o import de novo em seguida."""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
n = 0
for base in ("assets/models", "assets/models_hd", "assets/tex", "assets/tex_hd"):
    for dp, dn, fn in os.walk(os.path.join(ROOT, base)):
        for f in fn:
            if not f.endswith((".jpg.import", ".png.import")):
                continue
            p = os.path.join(dp, f)
            s = open(p, encoding="utf-8").read()
            t = s.replace("compress/mode=0", "compress/mode=2").replace("mipmaps/generate=false", "mipmaps/generate=true")
            if "_nor_" in f or "_nor." in f:
                t = t.replace("compress/normal_map=0", "compress/normal_map=1")
            if t != s:
                open(p, "w", encoding="utf-8").write(t)
                n += 1
print("texturas ajustadas:", n)
