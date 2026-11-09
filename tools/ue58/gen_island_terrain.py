"""New land of the island (08/11, docs/ue58/ILHA_PLANO.md step 4): the slopes and beaches grown around the existing
land (the summit walls, the headlands), from Content/Data/island.json (coast distance) and the land survey.

Height of a new-land point: a short slope (20-80 m) from the height of the nearest existing edge down to a low
coastal plain: the beach rises from the water level (-30 cm) at the coast to +80 cm 40 m inland, then the plain to
1-4 m with soft swells (08/11, Sergio: "não faça tudo montanha": the hill stays the old summit in the middle).
It reaches 2 cells (10 m) under the old land's edge 40 cm below it (no gap at the seam) and 15 m out to sea, down to
-1.2 m, where the sea floor mesh takes over. 5 m grid, glTF in the Godot axes like gen_ocean.py (x, up, UE y / 100).
  python tools/ue58/gen_island_terrain.py -> unreal/MareAlta/SourceArt/Island/IslandTerrain.gltf + .bin
"""
import json
import struct
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2] / 'unreal' / 'MareAlta'
DATA = ROOT / 'Content' / 'Data'
OUT = ROOT / 'SourceArt' / 'Island'


def main():
    cfg = json.loads((DATA / 'island.json').read_text(encoding='utf-8'))
    s = cfg['sdf']
    w, h = s['size']
    step = float(s['cell'])
    ox, oy = s['origin']
    sdf = np.frombuffer((DATA / s['file']).read_bytes(), '<f2').reshape(h, w).astype(np.float64) * 100.0
    survey = json.loads((ROOT / cfg['survey']).read_text(encoding='utf-8'))
    sx0, sx1, sy0, sy1, sstep = [float(v) for v in survey['arg'].split(',')]
    z = np.array([[np.nan if v is None else v for v in row] for row in survey['z']], np.float64)
    grid = np.full((h, w), np.nan)
    gx0, gy0 = int(round((sx0 - ox) / step)), int(round((sy0 - oy) / step))
    grid[gy0:gy0 + z.shape[0], gx0:gx0 + z.shape[1]] = z
    # 08/11 (Sergio: "essa parte marcada vira planície e floresta"): the dome tiles 1877-1936 north of the summit house
    # were removed from the level (mare_island.remove_dome); their ground counts as new land to fill.
    who = np.full((h, w), -1)
    who[gy0:gy0 + z.shape[0], gx0:gx0 + z.shape[1]] = np.array(survey['who'])
    dome_ids = [k for k, name in enumerate(survey['labels']) if '@MeshInstance3D@' in name and name.rsplit('@', 1)[-1].isdigit()
                and 1877 <= int(name.rsplit('@', 1)[-1]) <= 1936]
    grid[np.isin(who, dome_ids)] = np.nan
    land = grid > cfg['water_z']
    land |= np.isnan(grid) & ndimage.binary_closing(land, iterations=3)
    old_z = np.where(land, np.nan_to_num(grid, nan=0.0), 0.0)
    # fill the closed-gap cells of old land with the neighbours' height
    holes = land & np.isnan(grid)
    if holes.any():
        _, (iy, ix) = ndimage.distance_transform_edt(holes | ~land, return_indices=True)
        old_z[holes] = np.nan_to_num(grid, nan=0.0)[iy[holes], ix[holes]]

    d_old, (iy, ix) = ndimage.distance_transform_edt(~land, return_indices=True)
    d_old *= step
    edge_h = np.clip(old_z[iy, ix], -30, None)
    D = sdf                                     # cm, < 0 on the island
    inland = np.clip(-D, 0, None)

    def beach(a):                               # a = cm inland of the waterline (negative = at sea)
        return np.where(a >= 0, -30.0 + np.minimum(a, 4000.0) / 4000.0 * 110.0, -30.0 + a / 1500.0 * 90.0)

    # 08/11 (Sergio: "não faça tudo montanha"): the old edge drops over a short slope (20-80 m, steeper under the high
    # walls) to a low coastal plain (beach, then 1-4 m with soft swells), instead of one long slope down to the sea.
    rng = np.random.default_rng(11)
    swell = ndimage.gaussian_filter(rng.standard_normal((h, w)), 6000.0 / step / 2.5)
    swell /= np.abs(swell).max() or 1
    plain = np.where(inland < 4000, beach(inland), 80.0 + np.clip((inland - 4000.0) / 6000.0, 0, 1) * (220.0 + swell * 140.0))
    reach = np.clip(edge_h * .9, 2000.0, 8000.0)
    t = np.clip(d_old / reach, 0.0, 1.0)
    st = t * t * (3 - 2 * t)
    height = np.where(edge_h > plain, plain + (edge_h - plain) * (1.0 - st), plain)
    height = np.where(D > 0, beach(-D), height)  # at sea: on down to -1.2 m at 15 m out
    # 09/11 (Sergio's photo, a dark strip in the water by the pier): the terrain stopped 15 m out at -1.2 m, 1.5-2 m
    # above the sea floor planes (-2.7 to -3.5 m there): its stepped edge cast a dark line seen through the clear water.
    # It now keeps going down to -4.5 m at 60 m out, ending under the sea floor, which it meets without a step.
    height = np.where(D > 1500, -120.0 - np.clip((D - 1500.0) / 4500.0, 0, 1) * 330.0, height)

    new_land = (D < 0) & ~land
    seam = land & ndimage.binary_dilation(new_land, iterations=2)
    height = np.where(seam, old_z - 40.0, height)
    use = new_land | seam | ((D > 0) & (D < 6000) & ~land)
    use = ndimage.binary_dilation(use, iterations=1) & ~(land & ~seam)

    # vertices for every used cell corner (the grid points themselves), quads where all four are used
    ys, xs = np.nonzero(use)
    j0, j1, i0, i1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sub = use[j0:j1 + 1, i0:i1 + 1]
    H = height[j0:j1 + 1, i0:i1 + 1]
    nyv, nxv = sub.shape
    index = -np.ones(sub.shape, np.int64)
    index[sub] = np.arange(sub.sum())
    pos, nrm, uv, idx = bytearray(), bytearray(), bytearray(), bytearray()
    gy, gx = np.gradient(H, step)
    for (j, i) in zip(*np.nonzero(sub)):
        X = ox + (i0 + i) * step
        Y = oy + (j0 + j) * step
        pos += struct.pack('<3f', X / 100.0, H[j, i] / 100.0, Y / 100.0)
        n = np.array([-gx[j, i], 1.0, -gy[j, i]])
        n /= np.linalg.norm(n)
        nrm += struct.pack('<3f', *n)
        uv += struct.pack('<2f', X / 1000.0, Y / 1000.0)
    tris = 0
    for j in range(nyv - 1):
        for i in range(nxv - 1):
            a, b, c, d = index[j, i], index[j, i + 1], index[j + 1, i], index[j + 1, i + 1]
            if min(a, b, c, d) < 0:
                continue
            idx += struct.pack('<6I', a, c, b, b, c, d)
            tris += 2
    count = int(sub.sum())
    p = np.frombuffer(bytes(pos), '<f4').reshape(-1, 3)
    blob = bytes(pos + nrm + uv + idx)
    views, offset = [], 0
    for chunk in (pos, nrm, uv, idx):
        views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(chunk)})
        offset += len(chunk)
    gltf = {'asset': {'version': '2.0', 'generator': 'MareAlta island terrain (tools/ue58/gen_island_terrain.py)'},
            'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0, 'name': 'IslandTerrain'}],
            'materials': [{'name': 'IslandTerrain_ground'}],
            'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1, 'TEXCOORD_0': 2}, 'indices': 3, 'material': 0}]}],
            'buffers': [{'uri': 'IslandTerrain.bin', 'byteLength': len(blob)}], 'bufferViews': views,
            'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': count, 'type': 'VEC3',
                           'min': p.min(0).tolist(), 'max': p.max(0).tolist()},
                          {'bufferView': 1, 'componentType': 5126, 'count': count, 'type': 'VEC3'},
                          {'bufferView': 2, 'componentType': 5126, 'count': count, 'type': 'VEC2'},
                          {'bufferView': 3, 'componentType': 5125, 'count': len(idx) // 4, 'type': 'SCALAR'}]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'IslandTerrain.bin').write_bytes(blob)
    (OUT / 'IslandTerrain.gltf').write_text(json.dumps(gltf), encoding='utf-8')
    print(json.dumps({'vertices': count, 'triangles': tris, 'height_cm': [float(np.min(H[sub])), float(np.max(H[sub]))]}))


if __name__ == '__main__':
    main()
