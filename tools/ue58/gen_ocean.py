"""Graded ocean surface for the Unreal port (Godot axes, metres, y = sea level).

The first mesh used ~10 m quads, so the 7 m shoreline swell in M_CoastalWater_PBR was
sampled once per quad and showed as square facets. This grid is 0.75 m across the playable
beach and grows geometrically offshore and towards the side edges, keeping the same
extent [-1000, 1000] x [-2432, -32] so placement and collisions are unchanged.

  python tools/ue58/gen_ocean.py   ->  unreal/MareAlta/SourceArt/Ocean/Ocean.gltf + .bin

08/11 (the full island, ILHA_PLANO step 3): the grid now surrounds the island (x -1300..1350 m, south -2432 m to north
2050 m in the UE y). Quads stay 0.75 m in the bay, grow to at most 3 m over the whole ring around the island (MID) and
to 24 m only in the open sea; quads whose corners are all more than 15 m inland (Content/Data/island_sdf.bin) are left
out. One mesh, so the rows and columns meet with no cracks.
"""
import json
import struct
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Ocean'
X_RANGE, Z_RANGE, Y = (-1300.0, 1350.0), (-2432.0, 2050.0), -0.3
DENSE_X, DENSE_Z, STEP = (-120.0, 200.0), (-95.0, -32.0), 0.75
MID_X, MID_Z, MID_CAP = (-750.0, 800.0), (-400.0, 1300.0), 3.0
DATA = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/Content/Data'


def axis(lo, hi, dense_lo, dense_hi, step, grow=1.09, cap=24.0, mid=None):
    """Coordinates with uniform `step` inside [dense_lo, dense_hi], growing outwards (at most MID_CAP inside mid)."""
    pts = []
    x = dense_lo
    while x < dense_hi - 1e-6:
        pts.append(x)
        x += step
    pts.append(dense_hi)
    for direction, limit in ((1, hi), (-1, lo)):
        s, x = step, (dense_hi if direction > 0 else dense_lo)
        while (limit - x) * direction > 1e-6:
            s = min(s * grow, MID_CAP if mid and mid[0] <= x <= mid[1] else cap)
            x = x + s * direction
            if (limit - x) * direction < s * 0.35:
                x = limit
            pts.append(x)
    return sorted(set(round(p, 4) for p in pts))


def main():
    xs = axis(*X_RANGE, *DENSE_X, STEP, mid=MID_X)
    zs = axis(*Z_RANGE, *DENSE_Z, STEP, mid=MID_Z)
    # coast distance (cm, < 0 on land) at every vertex, to leave out the island's interior
    import numpy as np
    isl = json.loads((DATA / 'island.json').read_text(encoding='utf-8'))
    s = isl['sdf']
    w, h = s['size']
    sdf = np.frombuffer((DATA / s['file']).read_bytes(), '<f2').reshape(h, w).astype(np.float64) * 100.0
    gx, gz = np.meshgrid(np.array(xs) * 100.0, np.array(zs) * 100.0)
    ix = np.clip(np.round((gx - s['origin'][0]) / s['cell']).astype(int), 0, w - 1)
    iy = np.clip(np.round((gz - s['origin'][1]) / s['cell']).astype(int), 0, h - 1)
    shore = sdf[iy, ix]
    nx = len(xs)
    pos, nrm, uv, idx = bytearray(), bytearray(), bytearray(), bytearray()
    for z in zs:
        for x in xs:
            pos += struct.pack('<3f', x, Y, z)
            nrm += struct.pack('<3f', 0.0, 1.0, 0.0)
            uv += struct.pack('<2f', x / 20.0, z / 20.0)
    for j in range(len(zs) - 1):
        for i in range(nx - 1):
            if max(shore[j, i], shore[j, i + 1], shore[j + 1, i], shore[j + 1, i + 1]) < -1500:
                continue   # well inland: the terrain covers it
            a, b = j * nx + i, j * nx + i + 1
            c, d = a + nx, b + nx
            # Counter-clockwise seen from +Y (glTF front face), as in the original surface.
            idx += struct.pack('<6I', a, c, b, b, c, d)
    count = len(xs) * len(zs)
    blob = bytes(pos + nrm + uv + idx)
    views, offset = [], 0
    for chunk in (pos, nrm, uv, idx):
        views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(chunk)})
        offset += len(chunk)
    gltf = {'asset': {'version': '2.0', 'generator': 'MareAlta graded ocean (tools/ue58/gen_ocean.py)'},
            'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0, 'name': 'OceanSurface'}],
            'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1, 'TEXCOORD_0': 2}, 'indices': 3}]}],
            'buffers': [{'uri': 'Ocean.bin', 'byteLength': len(blob)}], 'bufferViews': views,
            'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': count, 'type': 'VEC3',
                           'min': [X_RANGE[0], Y, Z_RANGE[0]], 'max': [X_RANGE[1], Y, Z_RANGE[1]]},
                          {'bufferView': 1, 'componentType': 5126, 'count': count, 'type': 'VEC3'},
                          {'bufferView': 2, 'componentType': 5126, 'count': count, 'type': 'VEC2'},
                          {'bufferView': 3, 'componentType': 5125, 'count': len(idx) // 4, 'type': 'SCALAR'}]}
    (OUT / 'Ocean.bin').write_bytes(blob)
    (OUT / 'Ocean.gltf').write_text(json.dumps(gltf), encoding='utf-8')
    print(json.dumps({'columns': nx, 'rows': len(zs), 'vertices': count, 'triangles': len(idx) // 12}))


if __name__ == '__main__':
    main()
