#!/usr/bin/env python3
"""Remove imports de JPG/PNG órfãos de modelos GLB gerados pelo Blender.

As texturas já são embutidas nos GLBs (export_format='GLB'), mas o
repositório mantém *.jpg.import de builds antigos enquanto o JPG fonte é
ignorado pelo Git. O Godot tentava ler .godot/imported/*.ctex inexistentes,
emitindo centenas de erros falsos na importação do clone limpo.

Só remove sidecars de imagem sem fonte em assets/models/gen/.
Não apaga .glb, .glb.import, modelos ou texturas existentes.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "assets" / "models" / "gen"
removed = []
for ext in (".jpg.import", ".jpeg.import", ".png.import", ".webp.import"):
    for sidecar in root.rglob("*" + ext):
        source = Path(str(sidecar)[:-len(".import")])
        if not source.is_file():
            sidecar.unlink()
            removed.append(str(sidecar.relative_to(root)))
print("limpeza de imports de imagens órfãs:", len(removed))
if removed:
    print("exemplos:", ", ".join(removed[:8]))
