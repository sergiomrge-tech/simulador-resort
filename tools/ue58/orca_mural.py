"""Pool-floor orca mural: the Canva-generated tile mosaic (D:/Assets/Canva/orca) reduced to one colour
per 5 cm pool tile (120 x 60 tiles) and snapped to a tile palette; background aqua becomes transparent
so the normal pool tiles show. Output: SourceArt/Textures/Custom/orca_mural.png (read by M_PoolTiles_PBR).
Run: python tools/ue58/orca_mural.py"""
from pathlib import Path
from PIL import Image

SRC = Path('D:/Assets/Canva/orca/canva_orca_preview.png')
OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Textures/Custom/orca_mural.png'
W, H = 120, 60
PALETTE = {'black': (12, 13, 16), 'white': (250, 250, 247), 'grey': (168, 174, 176), 'aqua': None}
REF = {'black': (30, 30, 30), 'white': (235, 235, 235), 'grey': (160, 165, 165), 'aqua': (127, 211, 216)}

img = Image.open(SRC).convert('RGB').resize((W, H), Image.BOX)
out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
for y in range(H):
    for x in range(W):
        p = img.getpixel((x, y))
        name = min(REF, key=lambda k: sum((a - b) ** 2 for a, b in zip(p, REF[k])))
        if PALETTE[name]:
            out.putpixel((x, y), PALETTE[name] + (255,))
OUT.parent.mkdir(parents=True, exist_ok=True)
out.save(OUT)
print(OUT, sum(1 for px in out.getdata() if px[3]))
