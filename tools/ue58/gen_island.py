"""Island contour and coast distance field (08/11/2026, docs/ue58/ILHA_PLANO.md step 1).

Reads Content/Data/island.json (parameters) and the land survey it names (mare_island.land in the editor: first
blocking surface on a grid). Existing land (above water_z) is kept as it is; new land grows only into the void (no
surface at all), never over the bay's sea floor. Writes:
  Content/Data/island_sdf.bin   float16 signed distance to the coast in METRES (negative on land), row-major, rows
                                along +y from the domain origin; island.json "sdf" gets origin/cell/size.
  SourceArt/Island/T_IslandSDF.png  16-bit grey, the same field clamped to +-texture.range for the sea material
                                (0.5 = coast, 0 = deep inland, 1 = far at sea); island.json "texture" gets its domain.
  SourceArt/Island/island_preview.png  map for review (old land, new land, sea).
Run with the system Python (numpy, scipy, Pillow): python tools/ue58/gen_island.py"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2] / 'unreal' / 'MareAlta'
DATA = ROOT / 'Content' / 'Data'
ART = ROOT / 'SourceArt' / 'Island'


def main():
    cfg = json.loads((DATA / 'island.json').read_text(encoding='utf-8'))
    survey = json.loads((ROOT / cfg['survey']).read_text(encoding='utf-8'))   # copy of mare_island.land's output
    sx0, sx1, sy0, sy1, step = [float(v) for v in survey['arg'].split(',')]
    z = np.array([[np.nan if v is None else v for v in row] for row in survey['z']], np.float64)
    dx0, dy0, dx1, dy1 = [float(v) for v in cfg['domain']]
    w, h = int(round((dx1 - dx0) / step)) + 1, int(round((dy1 - dy0) / step)) + 1
    grid = np.full((h, w), np.nan)
    ox, oy = int(round((sx0 - dx0) / step)), int(round((sy0 - dy0) / step))
    grid[oy:oy + z.shape[0], ox:ox + z.shape[1]] = z

    water = cfg['water_z']
    land = grid > water
    # The bay's sea floor = the sand planes of the sea (labels with 'fundo'); anything else below the water (the skirts of
    # the summit pieces along their walls) is treated as empty, where new land may grow.
    who = np.full((h, w), -1)
    who[oy:oy + z.shape[0], ox:ox + z.shape[1]] = np.array(survey['who'])
    floor_ids = [i for i, name in enumerate(survey['labels']) if 'fundo' in name]
    ys_cm = dy0 + np.arange(h)[:, None] * step
    seabed = ~land & ((np.isin(who, floor_ids)) | ((who >= 0) & (ys_cm < 0)))   # + the bay's own beach below the water
    void = ~land & ~seabed
    # Holes of a few cells inside the old land (traces through seams between terrain pieces) are land.
    land |= void & ndimage.binary_closing(land, iterations=3)
    void &= ~land

    m = cfg['margin']
    dist, (iy, ix) = ndimage.distance_transform_edt(~land, return_indices=True)
    dist *= step
    edge = np.clip(np.nan_to_num(grid[iy, ix], nan=0.0), 0, None)
    rng = np.random.default_rng(m['seed'])
    noise = ndimage.gaussian_filter(rng.standard_normal((h, w)), m['noise_size'] / step / 2.5)
    noise /= np.abs(noise).max() or 1
    margin = np.minimum(m['base'] + m['per_height'] * edge, m['max']) + noise * m['noise']
    # Keep the bay open: no new land within sea_clear of the existing sea floor (its planes end in straight edges, and
    # land grown along them would turn the bay into a square channel).
    near_sea = ndimage.distance_transform_edt(~seabed) * step < m.get('sea_clear', 0)
    grow = void & (dist < margin) & ~near_sea
    island = land | grow
    soft = ndimage.gaussian_filter(island.astype(np.float64), m['smooth'] / step / 2.0) > .5
    island = land | (soft & void & ~near_sea)
    # Only the main island: drop crumbs of new land and fill closed lagoons made of void.
    lab, n = ndimage.label(island)
    if n > 1:
        sizes = ndimage.sum(island, lab, range(1, n + 1))
        main_label = 1 + int(np.argmax(sizes))
        island = (lab == main_label) | land
    island = ndimage.binary_fill_holes(island) & ~seabed | land

    inside = ndimage.distance_transform_edt(island) * step
    outside = ndimage.distance_transform_edt(~island) * step
    sdf = outside - inside   # cm, <0 on land
    sdf = ndimage.gaussian_filter(sdf, 1.0)

    (DATA / 'island_sdf.bin').write_bytes((sdf / 100.0).astype('<f2').tobytes())
    cfg['sdf'] = {'file': 'island_sdf.bin', 'unit': 'm', 'origin': [dx0, dy0], 'cell': step, 'size': [w, h]}

    t = cfg['texture']
    size, rng_cm = t['size'], t['range']
    zoom = (size / h, size / w)
    small = ndimage.zoom(sdf, zoom, order=1)[:size, :size]
    grey = np.clip(.5 + small / (2 * rng_cm), 0, 1)
    ART.mkdir(parents=True, exist_ok=True)
    # Row 0 of the image = lowest y (the material samples UV = (pos - origin) / extent with no flip).
    Image.fromarray((grey * 65535).astype(np.uint16)).save(ART / 'T_IslandSDF.png')
    t['domain'] = [dx0, dy0, dx0 + (w - 1) * step, dy0 + (h - 1) * step]

    pre = np.zeros((h, w, 3), np.uint8)
    pre[:] = (24, 70, 140)
    pre[seabed] = (40, 110, 170)
    pre[grow & island] = (196, 180, 110)
    pre[island & ~land] = (120, 170, 80)
    pre[land] = (70, 120, 60)
    coast = np.abs(sdf) < step * 1.2
    pre[coast & ~land] = (240, 225, 170)
    Image.fromarray(pre[::-1]).save(ART / 'island_preview.png')

    ys, xs = np.nonzero(island)
    cfg['summary'] = {'island_x': [dx0 + xs.min() * step, dx0 + xs.max() * step],
                      'island_y': [dy0 + ys.min() * step, dy0 + ys.max() * step],
                      'area_km2': round(island.sum() * step * step / 1e10, 3),
                      'new_land_km2': round((island & ~land).sum() * step * step / 1e10, 3)}
    (DATA / 'island.json').write_text(json.dumps(cfg, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(cfg['summary']))


if __name__ == '__main__':
    main()
