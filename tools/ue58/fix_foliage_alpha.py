"""Poly Haven foliage came with JPG base colours and no alpha: the glTF asks for alpha cut-outs (BLEND/MASK), but
without an alpha channel every leaf card renders whole with the black texture background (the "black confetti" in
the lawns). Poly Haven publishes the cut-out as a separate Alpha map (CC0): download it to D: and write the base
colour as RGBA PNG next to the original, <image name>_rgba.png. The editor side (mare_hud foliagealpha) reimports
the textures from those PNGs.

  python tools/ue58/fix_foliage_alpha.py            (all foliage under D:/Assets/PolyHaven)
"""
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path('D:/Assets/PolyHaven')
HEADERS = {'User-Agent': 'MareAltaResort-tools/1.0'}   # the API refuses urllib's default agent
FOLIAGE = ('grass', 'tree', 'leaves', 'shrub', 'fern', 'plant', 'botany', 'calathea', 'anthurium', 'periwinkle', 'rooibos',
           'bush', 'sorrel')


def alpha_url(asset, diff_uri):
    """The Alpha map matching a base colour image (trees have separate leaves maps)."""
    files = json.load(urllib.request.urlopen(urllib.request.Request(f'https://api.polyhaven.com/files/{asset}', headers=HEADERS)))
    keys = [k for k in files if 'alpha' in k.lower() or 'opacity' in k.lower()]
    stem = Path(diff_uri).stem.lower()
    # "leaves_alpha" for "<tree>_leaves_diff_2k", plain "Alpha" otherwise
    key = (next((k for k in keys if k.lower() not in ('alpha', 'opacity') and k.lower().replace('_alpha', '') in stem), None) or
           next((k for k in keys if k.lower() in ('alpha', 'opacity')), None))
    if not key:
        return None
    res = '2k' if '2k' in files[key] else sorted(files[key])[0]
    return files[key][res]['jpg']['url']


def main():
    out = []
    for gltf in sorted(ROOT.glob('*/*.gltf')):
        asset = gltf.parent.name
        g = json.loads(gltf.read_text(encoding='utf-8'))
        for m in g.get('materials', []):
            if m.get('alphaMode') not in ('BLEND', 'MASK') or not any(w in m['name'].lower() for w in FOLIAGE):
                continue
            bc = m.get('pbrMetallicRoughness', {}).get('baseColorTexture')
            if not bc:
                continue
            img = g['images'][g['textures'][bc['index']]['source']]
            diff = gltf.parent / img['uri']
            dest = diff.with_name(img['name'] + '_rgba.png')
            if dest.exists():
                out.append((asset, img['name'], str(dest), 'exists'))
                continue
            url = alpha_url(asset, img['uri'])
            if not url:
                out.append((asset, img['name'], '', 'no alpha map'))
                continue
            alpha_file = diff.with_name(Path(url).name)
            if not alpha_file.exists():
                alpha_file.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)).read())
            rgb = Image.open(diff).convert('RGB')
            a = Image.open(alpha_file).convert('L').resize(rgb.size, Image.LANCZOS)
            # Bleed leaf colour into the cut-away area so mip maps and filtering do not darken the leaf edges.
            arr = np.asarray(rgb).astype(np.float32)
            al = np.asarray(a).astype(np.float32) / 255
            mean = (arr * al[..., None]).sum((0, 1)) / max(al.sum(), 1)
            arr = arr * al[..., None] + mean * (1 - al[..., None])
            Image.fromarray(np.dstack([arr.clip(0, 255).astype(np.uint8), np.asarray(a)]), 'RGBA').save(dest)
            out.append((asset, img['name'], str(dest), f'alpha cover {al.mean():.2f}'))
    for row in out:
        print(*row, sep=' | ')


if __name__ == '__main__':
    sys.exit(main())
