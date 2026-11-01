"""Fill the two gaps between the resort ground tile and the hills (the ocean plane showed through as
flat blue 'lagoons', and the ground tile ended in square sand corners in the sea).

Input: a downward-trace grid from the editor (float_audit grid -26000,26000,-8000,14000,500).
For each side the surface blends from the ground edge height to the first hill height met going
outward, with gentle noise in the middle; south of the beach it follows the ground's slope under
the water. Output: SourceArt/Models/CoastFill_W.gltf and CoastFill_E.gltf (UE cm via the project
glTF mapping: Blender (x, -y, z) = UE (x, y, z) / 100).

  blender -b --factory-startup --python tools/ue58/coast_fill.py -- D:/CodexTemp/terrain/grid_-26000_26000_-8000_14000_500.json
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy

MODELS = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models'
GROUND = 'Maré · Ground'
STEP = 250                      # cm between filler vertices
SIDES = {'W': (-1, -12500), 'E': (1, 12500)}   # outward direction, last ground column (cm)


def is_hill(label):
    return label.startswith('Maré · @MeshInstance3D@18') or label.startswith('Maré · @MeshInstance3D@19')


def noise(x, y):
    return (math.sin(x * .0011 + 1.7) * math.sin(y * .0013 + .4) + .5 * math.sin(x * .0031 + y * .0023)) / 1.5


def build(grid, side):
    sign, inner = SIDES[side]
    cells = {(r[0], r[1]): r for r in grid}
    ys = sorted({r[1] for r in grid})
    profile = []
    for y in ys:
        g = cells.get((inner, y))
        if not g or g[3] != GROUND or g[2] is None:
            continue
        x, hill = inner, None
        while abs(x) < 26000:
            x += sign * 500
            c = cells.get((x, y))
            if c and c[2] is not None and is_hill(c[3]):
                hill = (x, c[2])
                break
        profile.append((y, g[2], hill))
    if not profile:
        return None
    # Outer edge: first hill met, or 4.5 km out if this row reaches the open sea (keeps following the beach).
    def at(y):
        lo = max((p for p in profile if p[0] <= y), key=lambda p: p[0], default=profile[0])
        hi = min((p for p in profile if p[0] >= y), key=lambda p: p[0], default=profile[-1])
        f = 0 if hi[0] == lo[0] else (y - lo[0]) / (hi[0] - lo[0])
        g = lo[1] + (hi[1] - lo[1]) * f
        def outer(p):
            return p[2] if p[2] else (inner + sign * 4500, p[1])
        xo = outer(lo)[0] + (outer(hi)[0] - outer(lo)[0]) * f
        zo = outer(lo)[1] + (outer(hi)[1] - outer(lo)[1]) * f
        return g, xo, zo
    # North of the last ground row the gap still runs into the hills: carry the last profile on.
    y0, y1 = profile[0][0], profile[-1][0] + 2000
    bm = bmesh.new()
    rows = []
    y = y0
    while y <= y1:
        g, xo, zo = at(y)
        x_start = inner - sign * 250             # tuck 2.5 m under the ground tile
        x_end = xo + sign * 600                  # and 6 m into the hill
        n = max(2, int(abs(x_end - x_start) / STEP))
        row = []
        for i in range(n + 1):
            x = x_start + (x_end - x_start) * i / n
            t = min(1, max(0, (x - inner) / (xo - inner))) if xo != inner else 0
            s = t * t * (3 - 2 * t)
            z = g + (zo - g) * s - 4 + noise(x, y) * 55 * math.sin(math.pi * t)
            row.append(bm.verts.new((x / 100, -y / 100, z / 100)))
        rows.append(row)
        y += STEP
    for a, b in zip(rows, rows[1:]):
        m = min(len(a), len(b))
        for i in range(m - 1):
            f = bm.faces.new((a[i], a[i + 1], b[i + 1], b[i])) if sign > 0 else bm.faces.new((a[i], b[i], b[i + 1], a[i + 1]))
            f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    me = bpy.data.meshes.new('CoastFill_' + side)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new('CoastFill_' + side, me)
    bpy.context.scene.collection.objects.link(obj)
    uv = me.uv_layers.new(name='UVMap')
    for loop in me.loops:
        v = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (v.x / 4.5, v.y / 4.5)
    me.materials.append(bpy.data.materials.new('MA_coast_fill'))
    return obj


if __name__ == '__main__':
    grid = json.loads(Path(sys.argv[sys.argv.index('--') + 1]).read_text(encoding='utf-8'))
    report = []
    for side in SIDES:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = build(grid, side)
        if not obj:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.export_scene.gltf(filepath=str(MODELS / (obj.name + '.gltf')), export_format='GLTF_SEPARATE', use_selection=True,
                                  export_yup=True, export_apply=True, export_image_format='NONE')
        report.append({'mesh': obj.name, 'faces': len(obj.data.polygons), 'dims_m': [round(v) for v in obj.dimensions]})
    print('COAST_FILL', json.dumps(report))
