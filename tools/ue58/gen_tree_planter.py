"""Round tree planter of the village square (replaces the Godot export World_1205: a plain beige cylinder 4.6 m wide).
A curb of 30 dressed stone blocks with mortar gaps and slightly uneven heights around a domed bed of soil and fallen
leaves; stone and soil are CC0 Poly Haven scans (plaster_stone_wall_01, brown_mud_leaves_01). Built in the old
mesh's frame: 4.6 m across, 45 cm tall, centred on the origin (z from -0.225 to 0.225).
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_tree_planter.py
Output: D:/Assets/Mare/square_tree_planter/square_tree_planter.glb."""
import math
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import noise, Vector  # noqa: E402
from gen_custom_furniture import export, finish, material, mesh_obj, reset  # noqa: E402

R_OUT, R_IN, BOTTOM, TOP = 2.30, 2.02, -.225, .225
BLOCKS, GAP = 30, .008


def curb(stone, rnd):
    for k in range(BLOCKS):
        a0 = 2 * math.pi * k / BLOCKS + GAP / R_OUT
        a1 = 2 * math.pi * (k + 1) / BLOCKS - GAP / R_OUT
        top = TOP - rnd.uniform(0, .008)
        bm = bmesh.new()
        # a curved block: 4 steps along the arc so the ring reads round, not faceted
        steps = 4
        rows = []
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            c, s = math.cos(a), math.sin(a)
            rows.append([bm.verts.new((r * c, r * s, z)) for r, z in ((R_IN, BOTTOM), (R_OUT, BOTTOM), (R_OUT, top), (R_IN, top))])
        for r0, r1 in zip(rows, rows[1:]):
            for j in range(4):
                bm.faces.new((r0[j], r0[(j + 1) % 4], r1[(j + 1) % 4], r1[j]))
        bm.faces.new(list(reversed(rows[0])))
        bm.faces.new(rows[-1])
        obj = mesh_obj(f'block{k}', bm)
        finish(obj, stone, uv=.9, bevel=.012, smooth=False)


def soil_bed(earth):
    """Polar grid domed a little in the middle, with a soft lumpy surface; its rim tucks under the curb."""
    bm = bmesh.new()
    rings, segs = 14, 96
    centre = bm.verts.new((0, 0, .175))
    grid = []
    for i in range(1, rings + 1):
        r = (R_IN + .02) * i / rings
        row = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            x, y = r * math.cos(a), r * math.sin(a)
            z = .14 + .035 * (1 - (r / R_IN) ** 2) + .008 * noise.noise(Vector((x * 2.2, y * 2.2, 0)))
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for j in range(segs):
        bm.faces.new((centre, grid[0][j], grid[0][(j + 1) % segs]))
    for r0, r1 in zip(grid, grid[1:]):
        for j in range(segs):
            bm.faces.new((r0[j], r1[j], r1[(j + 1) % segs], r0[(j + 1) % segs]))
    obj = mesh_obj('soil', bm)
    finish(obj, earth, uv=1.4, smooth=True)


def main():
    reset()
    rnd = random.Random(11)
    out = Path('D:/Assets/Mare/square_tree_planter')
    out.mkdir(parents=True, exist_ok=True)
    stone = material('stone', 'plaster_stone_wall_01', rough=.85)
    earth = material('soil', 'brown_mud_leaves_01', rough=.95)
    curb(stone, rnd)
    soil_bed(earth)
    for o in bpy.context.scene.objects:
        o.select_set(True)
        for mod in list(o.modifiers):
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.view_layer.objects.active = bpy.data.objects['soil']
    bpy.ops.object.join()
    bpy.context.active_object.name = 'square_tree_planter'
    export('square_tree_planter', 'Village square tree planter (bpy)')


if __name__ == '__main__':
    main()
