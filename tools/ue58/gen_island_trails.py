"""Earth paths of the island trails West and North (08/11; plan_island_trails.py routes them, mare_island.trail_heights
traces the exact ground across them into D:/CodexTemp/island/trail_cross.json). Like the summit trail: an earth path
1.8 m wide with a slight crown, never below the ground across its width (+4 cm), smoothed along, and banks on both
edges that sink 30 cm into the ground so no gap shows. Texture: the summit trail's earth (Poly Haven
brown_mud_leaves_01, CC0). One mesh in world coordinates (actor at the UE origin), Blender (x, y, z) m = UE (x, -y, z)/100.
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_island_trails.py"""
import json
import sys
from pathlib import Path

import bpy
import bmesh

sys.path.insert(0, str(Path(__file__).parent))
from gen_summit_trail import material   # noqa: E402

SRC = Path('D:/CodexTemp/island/trail_cross.json')
OUT = Path('D:/Assets/Mare/mare_island_trails')
# across (cm, as traced), the path surface between -90 and +90, banks out to +-190
CROSS = [-190, -100, -60, -20, 20, 60, 100, 190]
CROWN = {-100: 0, -60: 3, -20: 5, 20: 5, 60: 3, 100: 0}


def smooth(vals, win):
    out = []
    for i in range(len(vals)):
        a, b = max(0, i - win), min(len(vals), i + win + 1)
        out.append(sum(vals[a:b]) / (b - a))
    return out


def main():
    data = json.loads(SRC.read_text(encoding='utf-8'))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    earth = material('IslandEarth', 'brown_mud_leaves_01')
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    for key, t in data.items():
        pts, rows = t['points'], t['z']
        wf = t.get('w') or [1.0] * len(pts)   # width factor along the way (plan_island_trails.py)
        # path level per point: the highest traced ground under the path width (+4 cm), smoothed along
        level = []
        for row in rows:
            core = [v for c, v in zip(CROSS, row) if v is not None and -100 <= c <= 100]
            level.append(max(core) + 4 if core else (level[-1] if level else 0))
        level = smooth(level, 2)
        ring_prev = None
        dist = 0.0
        for k, (x, y, _) in enumerate(pts):
            a, b = pts[max(0, k - 1)], pts[min(len(pts) - 1, k + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = (dx * dx + dy * dy) ** .5 or 1.0
            sx, sy = dy / n, -dx / n
            if k:
                dist += ((x - pts[k - 1][0]) ** 2 + (y - pts[k - 1][1]) ** 2) ** .5
            ring = []
            for c, gz in zip(CROSS, rows[k]):
                if c in CROWN:
                    z = level[k] + CROWN[c]
                else:   # bank: down to 30 cm under the ground beside the path
                    g = gz if gz is not None else level[k] - 40
                    z = min(g, level[k]) - 30
                ring.append(bm.verts.new(((x + sx * c * wf[k]) / 100.0, -(y + sy * c * wf[k]) / 100.0, z / 100.0)))
            if ring_prev:
                for i in range(len(CROSS) - 1):
                    f = bm.faces.new((ring_prev[i], ring_prev[i + 1], ring[i + 1], ring[i]))
                    for loop, (u, v) in zip(f.loops, ((CROSS[i], dist_prev), (CROSS[i + 1], dist_prev), (CROSS[i + 1], dist), (CROSS[i], dist))):
                        loop[uv_layer].uv = (u * wf[k] / 180.0, v / 180.0)
            ring_prev, dist_prev = ring, dist
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    mesh = bpy.data.meshes.new('mare_island_trails')
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(earth)
    obj = bpy.data.objects.new('mare_island_trails', mesh)
    bpy.context.scene.collection.objects.link(obj)
    OUT.mkdir(parents=True, exist_ok=True)
    for m in bpy.data.materials:
        if not m.name.startswith('mare_island_trails'):
            m.name = 'mare_island_trails_' + m.name
    for im in bpy.data.images:
        if im.users and not im.name.startswith('mare_island_trails'):
            im.name = 'mare_island_trails_' + im.name
    bpy.ops.export_scene.gltf(filepath=str(OUT / 'mare_island_trails.glb'), export_format='GLB', export_apply=True)
    print('faces', len(mesh.polygons))


if __name__ == '__main__':
    main()
