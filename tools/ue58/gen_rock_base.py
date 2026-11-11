"""Rock feet under the lighthouse slabs (see Content/Python/mare_rock_base.py). Reads D:/CodexTemp/rock_base.json (the
scan of each slab's top on a 30 cm grid, UE cm) and writes one model per slab: a ring of rock that starts 8 cm under
the slab's surface along its rim (a few cells in under the plate, so no gap shows) and falls away outside it at about
65 degrees, with a rough face, down to 4 m under the sea level. Built in world coordinates (metres, Blender y = -UE y):
the level places it at the origin.
  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_rock_base.py
Output: D:/Assets/Mare/mare_rock_base_<k>/mare_rock_base_<k>.glb."""
import json
from pathlib import Path
import bpy
import bmesh
import numpy as np

SRC = Path('D:/CodexTemp/rock_base.json')
OUT = Path('D:/Assets/Mare')
PAD, INNER = 14, 4          # cells of slope outside the rim, cells kept under the plate
SLOPE, FLOOR = 1.5, -4.0   # metres down per metre out; where the foot stops


def noise(shape, seed, beta=1.6):
    rng = np.random.default_rng(seed)
    n = 1
    while n < max(shape):
        n *= 2
    fx = np.fft.fftfreq(n)[:, None]
    fy = np.fft.rfftfreq(n)[None, :]
    f = np.hypot(fx, fy)
    f[0, 0] = 1
    spec = (rng.normal(size=f.shape) + 1j * rng.normal(size=f.shape)) / f ** beta
    spec[0, 0] = 0
    out = np.fft.irfft2(spec, s=(n, n))
    return (out / np.abs(out).max())[:shape[0], :shape[1]]


def build(k, row):
    step = row['step'] / 100
    g = np.array([[np.nan if v is None else v / 100 for v in line] for line in row['grid']], np.float64)
    g = np.pad(g, PAD, constant_values=np.nan)
    ny, nx = g.shape
    inside = ~np.isnan(g)
    if inside.sum() < 20:
        return None
    # true (Euclidean) distance in cells from the plate and the height of the nearest plate cell: the chamfer walk used
    # first gave a staircase rim, which showed as a row of saw teeth along the wall
    dist = np.where(inside, 0.0, np.inf)
    rim = np.where(inside, g, 0.0)
    for dy in range(-PAD, PAD + 1):
        for dx in range(-PAD, PAD + 1):
            d = float(np.hypot(dy, dx))
            if d == 0 or d > PAD:
                continue
            src_in = np.roll(np.roll(inside, dy, 0), dx, 1)
            src_g = np.roll(np.roll(np.where(inside, g, 0.0), dy, 0), dx, 1)
            take = src_in & ~inside & (d < dist)
            dist = np.where(take, d, dist)
            rim = np.where(take, src_g, rim)

    def blur(a, r, mask):
        acc = np.zeros(a.shape)
        cnt = np.zeros(a.shape)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                acc += np.roll(np.roll(np.where(mask, a, 0.0), dy, 0), dx, 1)
                cnt += np.roll(np.roll(mask, dy, 0), dx, 1)
        return acc / np.maximum(cnt, 1)
    reach = np.isfinite(dist)
    rim = np.where(inside, g, blur(rim, 2, reach))
    dist = np.where(inside, 0.0, np.where(reach, blur(np.where(reach, dist, 0.0), 1, reach), np.inf))
    # depth inside the plate: how many cells in from its rim
    inner = np.where(inside, np.inf, 0.0)
    for n in range(1, INNER + 2):
        m = np.full(g.shape, np.inf)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            m = np.minimum(m, np.roll(np.roll(inner, dy, 0), dx, 1) + 1)
        inner = np.where(inside, np.minimum(inner, m), 0.0)
    rough = noise(g.shape, 100 + k) * .45 + noise(g.shape, 200 + k, 1.0) * .12
    # a ledge just under the rim, then the fall: steeper where the noise says so (buttresses and gullies)
    fall = SLOPE * (1 + .45 * noise(g.shape, 300 + k, 2.2))
    z = np.where(inside, g - .08, rim - .08 - fall * np.maximum(dist - .6, 0) * step + rough * np.minimum(dist, 4) / 4)
    keep = (inside & (inner <= INNER)) | (~inside & np.isfinite(dist) & (dist <= PAD))
    z = np.maximum(z, FLOOR)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    verts = {}
    for j in range(ny):
        for i in range(nx):
            if keep[j, i]:
                x = (row['x0'] / 100) + (i - PAD) * step
                y = (row['y0'] / 100) + (j - PAD) * step
                verts[(j, i)] = bm.verts.new((x, -y, float(z[j, i])))
    for j in range(ny - 1):
        for i in range(nx - 1):
            q = [verts.get((j, i)), verts.get((j, i + 1)), verts.get((j + 1, i + 1)), verts.get((j + 1, i))]
            if all(q):
                f = bm.faces.new(q)
                f.smooth = True
    bm.normal_update()
    up = sum(f.normal.z for f in bm.faces)
    if up < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    for f in bm.faces:
        for loop in f.loops:
            c = loop.vert.co        # the fall adds to both axes: the rock's picture is not smeared down the wall
            loop[uv].uv = ((c.x + c.z * .7) / 4.0, (c.y + c.z * .7) / 4.0)
    slug = f'mare_rock_base_{k}'
    me = bpy.data.meshes.new(slug)
    bm.to_mesh(me)
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    bm.free()
    o = bpy.data.objects.new(slug, me)
    bpy.context.scene.collection.objects.link(o)
    mat = bpy.data.materials.new(f'{slug}_Rock')
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.36, .30, .24, 1)
    mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .9
    me.materials.append(mat)
    folder = OUT / slug
    folder.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.gltf(filepath=str(folder / f'{slug}.glb'), export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
    (folder / 'info.json').write_text(json.dumps({'slug': slug, 'name': f'Base de rocha {row["name"]} (bpy)', 'gltf': f'{slug}.glb',
                                                  'license': 'Original model'}, indent=1), encoding='utf-8')
    bpy.data.objects.remove(o, do_unlink=True)
    return tris


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rows = json.loads(SRC.read_text(encoding='utf-8'))
    for k, row in enumerate(rows):
        print('ROCK', k, row['name'], row['cells'], build(k, row))


if __name__ == '__main__':
    main()
