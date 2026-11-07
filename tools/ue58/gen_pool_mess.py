"""Pool mess for the pool-cleaning task: a cluster of fallen almond-tree and palm leaves floating flat on the water
(GLB, metres, waterline at z=0, about 0.9 m across). D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_pool_mess.py
Output: unreal/MareAlta/SourceArt/Models/PoolMess/pool_leaves.glb (unique material names)."""
import math
import random
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models/PoolMess'


def material(name, colour, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    return m


def leaf(bm, centre, yaw, length, width, curl, mat):
    """Elliptic leaf with a raised midrib and edges curling up; a ring of rows along the length."""
    rows, cols = 14, 7
    grid = []
    for i in range(rows + 1):
        t = i / rows
        half = width * .5 * math.sin(math.pi * t) ** .8          # pointed tip and stalk end
        row = []
        for j in range(cols + 1):
            s = j / cols * 2 - 1
            x = (t - .5) * length
            y = s * half
            z = .004 * (1 - abs(s)) + curl * s * s * half + .01 * math.sin(math.pi * t)
            p = Vector((x, y, z))
            p.rotate(__import__('mathutils').Euler((0, 0, yaw)))
            row.append(bm.verts.new(p + centre))
        grid.append(row)
    for i in range(rows):
        for j in range(cols):
            f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
            f.material_index = mat
    # Stalk: a thin strip past the leaf base.
    base = grid[0][cols // 2].co.copy()
    d = Vector((-1, 0, 0))
    d.rotate(__import__('mathutils').Euler((0, 0, yaw)))
    a = bm.verts.new(base + Vector((0, .002, .004)))
    b = bm.verts.new(base + Vector((0, -.002, .004)))
    c = bm.verts.new(base + d * .05 + Vector((0, -.002, .006)))
    e = bm.verts.new(base + d * .05 + Vector((0, .002, .006)))
    bm.faces.new((a, b, c, e)).material_index = mat


def leaves():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    random.seed(7)
    bm = bmesh.new()
    for k in range(9):
        r = random.uniform(0, .38)
        a = random.uniform(0, 2 * math.pi)
        centre = Vector((math.cos(a) * r, math.sin(a) * r, k * .0015))
        kind = k % 3
        leaf(bm, centre, random.uniform(0, 2 * math.pi), random.uniform(.16, .26), random.uniform(.07, .11),
             random.uniform(.05, .2), kind)
    bm.normal_update()
    me = bpy.data.meshes.new('pool_leaves')
    bm.to_mesh(me)
    obj = bpy.data.objects.new('pool_leaves', me)
    bpy.context.scene.collection.objects.link(obj)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(material('pool_leaves_green', (.16, .3, .07), .55))
    me.materials.append(material('pool_leaves_yellow', (.62, .5, .14), .6))
    me.materials.append(material('pool_leaves_brown', (.35, .2, .09), .7))
    sol = obj.modifiers.new('Thick', 'SOLIDIFY')
    sol.thickness = .002
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(OUT / 'pool_leaves.glb'), export_format='GLB', use_selection=True, export_apply=True)
    print('wrote pool_leaves', len(me.vertices))


leaves()
