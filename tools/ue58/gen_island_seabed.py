"""Sea floor all round the island (08/11, docs/ue58/ILHA_PLANO.md step 2): one sand mesh in place of the four
straight planes of mare_water.ensure_seabed. Height = the reef.json floor profile along the distance to the nearest
coast (Content/Data/island.json sdf), the same rule as UMareReefWorld::SeabedZ(X,Y): within 25 m of the waterline it
runs from the water level (-30) down to the profile's first point; under land it stays at the water level (the
terrain covers it). Grid every 6 m, UVs in world metres / 10. World origin, UE cm -> Blender m with y mirrored.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_island_seabed.py
Output: D:/Assets/Mare/mare_island_seabed/mare_island_seabed.glb (imported by mare_island.seabed)."""
import json
import sys
from pathlib import Path

import numpy as np
import bpy
import bmesh

ROOT = Path(__file__).resolve().parents[2] / 'unreal' / 'MareAlta'
DATA = ROOT / 'Content' / 'Data'
OUT = Path('D:/Assets/Mare/mare_island_seabed')
STEP = 600.0                                   # cm
X0, X1, Y0, Y1 = -90000.0, 95000.0, -70000.0, 160000.0


def main():
    isl = json.loads((DATA / 'island.json').read_text(encoding='utf-8'))
    s = isl['sdf']
    w, h = s['size']
    sdf = np.frombuffer((DATA / s['file']).read_bytes(), '<f2').reshape(h, w).astype(np.float64) * 100.0   # cm
    ox, oy = s['origin']
    cell = s['cell']
    prof = json.loads((DATA / 'reef.json').read_text(encoding='utf-8'))['floor_fill']['profile']
    bay = isl.get('bay_waterline_y', -2950)

    def profile(y):
        if y >= prof[0][0]:
            return prof[0][1]
        for (ya, za), (yb, zb) in zip(prof, prof[1:]):
            if y >= yb:
                return za + (zb - za) * (y - ya) / (yb - ya)
        return prof[-1][1]

    near = profile(bay - 2500)

    def shore(x, y):
        fx = np.clip((x - ox) / cell, 0, w - 1.001)
        fy = np.clip((y - oy) / cell, 0, h - 1.001)
        ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int)
        ax, ay = fx - ix, fy - iy
        v = (sdf[iy, ix] * (1 - ax) + sdf[iy, ix + 1] * ax) * (1 - ay) + (sdf[iy + 1, ix] * (1 - ax) + sdf[iy + 1, ix + 1] * ax) * ay
        out = np.hypot((x - ox) / cell - np.clip((x - ox) / cell, 0, w - 1), (y - oy) / cell - np.clip((y - oy) / cell, 0, h - 1)) * cell
        return v + out

    xs = np.arange(X0, X1 + 1, STEP)
    ys = np.arange(Y0, Y1 + 1, STEP)
    gx, gy = np.meshgrid(xs, ys)
    d = shore(gx, gy)
    z = np.empty_like(d)
    land = d <= 0
    coastal = (d > 0) & (d < 2500)
    z[land] = -30.0
    z[coastal] = -30.0 + (near + 30.0) * (d[coastal] / 2500.0)
    far = d >= 2500
    vprof = np.vectorize(profile)
    z[far] = vprof(bay - d[far])

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bm = bmesh.new()
    ny, nx = gx.shape
    verts = [[None] * nx for _ in range(ny)]
    for j in range(ny):
        for i in range(nx):
            verts[j][i] = bm.verts.new((gx[j, i] / 100.0, -gy[j, i] / 100.0, z[j, i] / 100.0))
    uv_layer = bm.loops.layers.uv.new('UVMap')
    for j in range(ny - 1):
        for i in range(nx - 1):
            # winding so the face points up after the y mirror
            f = bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
            for loop in f.loops:
                co = loop.vert.co
                loop[uv_layer].uv = (co.x / 10.0, co.y / 10.0)
    bm.normal_update()
    # every face up (open terrain: recalc can flip them down, lesson 04/11)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    mesh = bpy.data.meshes.new('mare_island_seabed')
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new('mare_island_seabed', mesh)
    bpy.context.scene.collection.objects.link(obj)
    mat = bpy.data.materials.new('mare_island_seabed_sand')
    mesh.materials.append(mat)
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / 'mare_island_seabed.glb'), export_format='GLB', export_apply=True)
    print('verts', nx * ny, 'z range', float(z.min()), float(z.max()))


if __name__ == '__main__':
    main()
