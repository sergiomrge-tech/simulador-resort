"""Walking trail to the old man's house (04/11). Reads D:/CodexTemp/tsunami/trail.json (plan_summit_trail.py: UE cm,
[x, y, terrain z]) and the terrain grids, builds one mesh in WORLD coordinates (place the actor at the UE origin):
  - an earth path 1.8 m wide with a slight crown, never below the terrain across its width (+4 cm), smoothed along;
  - earth banks on both edges down into the ground (the low side shows where the path is cut into the slope);
  - log steps (bark) every 0.7 m where the path is steeper than 22%.
Poly Haven CC0 textures: brown_mud_leaves_01 (path), bark_brown_02 (logs). Blender (x, y, z) m = UE (x, -y, z) / 100.
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_summit_trail.py"""
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
import plan_summit_trail as plan   # noqa: E402  (terrain sampler h_at)

D = Path('D:/CodexTemp/tsunami')
PH = 'D:/Assets/PolyHaven'
HALF = 90.0          # half width, cm
CROSS = [-1.0, -.6, -.2, .2, .6, 1.0]


def material(name, tex, tile_note=''):
    m = bpy.data.materials.new('Trail_' + name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = .92
    for kind in ('diff', 'nor'):
        path = earth_texture() if (tex == 'brown_mud_leaves_01' and kind == 'diff') else f'{PH}/{tex}/{tex}_{kind}_1k.jpg'
        img = bpy.data.images.load(path)
        img.name = f'Trail_{name}_{kind}'
        if kind == 'nor':
            img.colorspace_settings.name = 'Non-Color'
        img.pack()
        node = nt.nodes.new('ShaderNodeTexImage')
        node.image = img
        if kind == 'diff':
            nt.links.new(node.outputs['Color'], b.inputs['Base Color'])
        else:
            nm = nt.nodes.new('ShaderNodeNormalMap')
            nt.links.new(node.outputs['Color'], nm.inputs['Color'])
            nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m


TRAIL_CROSS = [-1.9, -1.0, -.6, -.2, .2, .6, 1.0, 1.9]
_CROSS_Z = json.loads((D / 'trail_cross.json').read_text()) if (D / 'trail_cross.json').exists() else None


def terrain(i, p, c):
    """Exact traced terrain height across the trail (mare_tsunami.trail_cross), grid sample where the trace missed."""
    if _CROSS_Z and c in TRAIL_CROSS:
        row = [v for v in _CROSS_Z[i] if v is not None]
        v = _CROSS_Z[i][TRAIL_CROSS.index(c)]
        # A trace through a seam between terrain tiles lands on the flat village ground far below: discard it.
        if v is not None and row and v > sorted(row)[len(row) // 2] - 150:
            return v
    return plan.h_at(p.x, p.y)


def earth_texture():
    """brown_mud_leaves_01 read orange-red in the game: a less saturated, slightly darker copy."""
    from PIL import Image, ImageEnhance
    src = f'{PH}/brown_mud_leaves_01/brown_mud_leaves_01_diff_1k.jpg'
    dst = D / 'trail_earth_diff_1k.jpg'
    img = ImageEnhance.Color(Image.open(src).convert('RGB')).enhance(.55)
    ImageEnhance.Brightness(img).enhance(.85).save(dst, quality=92)
    return str(dst)


def smooth(vals, win):
    out = []
    for i in range(len(vals)):
        a, b = max(0, i - win), min(len(vals), i + win + 1)
        out.append(sum(vals[a:b]) / (b - a))
    return out


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rows = json.loads((D / 'trail.json').read_text())
    pts = [Vector((r[0], r[1])) for r in rows]
    n = len(pts)
    tang = []
    for i in range(n):
        a, b = pts[max(0, i - 2)], pts[min(n - 1, i + 2)]
        t = (b - a).normalized()
        tang.append(t)
    side = [Vector((-t.y, t.x)) for t in tang]
    # Path height: highest terrain across the width (+4 cm), smoothed along, then lifted again where smoothing dipped.
    lift = [max(terrain(i, pts[i] + side[i] * HALF * c, c) for c in CROSS) + 4 for i in range(n)]
    z = smooth(lift, 3)
    z = [max(a, b) for a, b in zip(z, lift)]
    z = smooth(z, 1)
    z = [max(a, b - 2) for a, b in zip(z, lift)]
    # Grade cap 0.6 (~31 deg, well under the 44.8 deg walkable limit): raise the lower side of any steeper stretch
    # (fill, never cut, so the path is never buried).
    gd = [0.0] + [(pts[i] - pts[i - 1]).length for i in range(1, n)]
    for _ in range(3):
        for i in range(n - 2, -1, -1):
            z[i] = max(z[i], z[i + 1] - .6 * gd[i + 1])
        for i in range(1, n):
            z[i] = max(z[i], z[i - 1] - .6 * gd[i])
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    path_m = material('Earth', 'brown_mud_leaves_01')
    log_m = material('Log', 'bark_brown_02')
    dist = [0.0]
    for i in range(1, n):
        dist.append(dist[-1] + (pts[i] - pts[i - 1]).length)
    # Cross-section: bank bottom, edge, crown points, edge, bank bottom (u in metres across, v along).
    rings = []
    for i in range(n):
        ring = []
        for k, c in enumerate([-1.9] + CROSS + [1.9]):
            p = pts[i] + side[i] * HALF * max(-1.0, min(1.0, c)) * (1.0 if abs(c) <= 1 else 1.0)
            if abs(c) > 1:
                p = pts[i] + side[i] * HALF * c
                zz = terrain(i, p, c) - 8              # bank ramps down to the ground ~80 cm out (no vertical wall)
            else:
                zz = z[i] + 3 * (1 - c * c)            # 3 cm crown
            ring.append(bm.verts.new((p.x / 100, -p.y / 100, zz / 100)))
        rings.append(ring)
    us = [-1.8, -.9, -.54, -.18, .18, .54, .9, 1.8]
    for i in range(n - 1):
        for k in range(len(us) - 1):
            # Blender mirrors Y (UE -> Blender), so this winding faces up after the mirror.
            f = bm.faces.new((rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]))
            f.smooth = True
            for loop, (a, b) in zip(f.loops, ((i, k), (i, k + 1), (i + 1, k + 1), (i + 1, k))):
                loop[uv].uv = (us[b] * .7, dist[a] / 100 * .7)
    bm.normal_update()
    up = sum((f.normal.z for f in bm.faces), 0.0)
    if up < 0:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new('SummitTrail')
    bm.to_mesh(me)
    bm.free()
    trail = bpy.data.objects.new('SummitTrail', me)
    bpy.context.collection.objects.link(trail)
    trail.data.materials.append(path_m)
    # Log steps on the steep stretches.
    logs = 0
    last = -1e9
    for i in range(1, n - 1):
        g = abs(z[i + 1] - z[i - 1]) / max(1.0, dist[i + 1] - dist[i - 1])
        bend = tang[max(0, i - 3)].dot(tang[min(n - 1, i + 3)])
        if g < .22 or dist[i] - last < 70 or bend < .93:     # no logs in the bends (they splayed along the path)
            continue
        last = dist[i]
        a = pts[i] - side[i] * (HALF - 4)
        b = pts[i] + side[i] * (HALF - 4)
        za, zb = plan.h_at(a.x, a.y), plan.h_at(b.x, b.y)
        zc = z[i] + 2
        bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=.075, depth=(b - a).length / 100,
                                            location=((a.x + b.x) / 200, -(a.y + b.y) / 200, zc / 100))
        o = bpy.context.active_object
        d = Vector(((b.x - a.x), -(b.y - a.y), 0)).normalized()
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
        o.data.materials.append(log_m)
        for p in o.data.polygons:
            p.use_smooth = True
        logs += 1
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    for o in objs:
        o.select_set(True)
        bpy.context.view_layer.objects.active = trail
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    out = D / 'SummitTrail.glb'
    bpy.ops.export_scene.gltf(filepath=str(out), export_format='GLB', export_apply=True)
    grades = [abs(z[i + 1] - z[i]) / max(1, dist[i + 1] - dist[i]) for i in range(n - 1)]
    bank = max(z[i] - min(terrain(i, pts[i] + side[i] * HALF * c, c) for c in (-1.0, 1.0)) for i in range(n))
    print('trail', round(dist[-1] / 100), 'm, logs', logs, 'max grade', round(max(grades), 2), 'max bank', round(bank / 100, 2), 'm')
    (D / 'trail_z.json').write_text(json.dumps([[round(p.x), round(p.y), round(v)] for p, v in zip(pts, z)]))


if __name__ == '__main__':
    build()
