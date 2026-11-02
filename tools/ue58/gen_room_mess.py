"""Room mess for the pousada cleaning tasks: a crumpled bath towel and a tied trash bag (GLB, metres, base at z=0).
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_room_mess.py
Output: unreal/MareAlta/SourceArt/Models/RoomMess/{mess_towel,mess_trash_bag}.glb (unique material/image names)."""
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector, noise

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models/RoomMess'


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, colour, rough, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    if 'Sheen Weight' in p.inputs:
        p.inputs['Sheen Weight'].default_value = sheen
    return m


def export(obj, name):
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(OUT / f'{name}.glb'), export_format='GLB', use_selection=True, export_apply=True)
    print('wrote', name, len(obj.data.vertices), 'verts')


def towel():
    """70 x 40 cm terry towel dropped in a heap: grid draped with folds, terry loops from displacement."""
    reset()
    bm = bmesh.new()
    nx, ny, w, d = 70, 40, .70, .40
    verts = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            u, v = i / nx, j / ny
            x, y = (u - .5) * w, (v - .5) * d
            # Heap: the cloth is gathered toward the middle with ridged folds, as if dropped on the floor.
            n1 = noise.noise(Vector((u * 3, v * 3, 1)))
            n2 = noise.noise(Vector((u * 3, v * 3, 7)))
            x, y = x * (.55 + .2 * n1), y * (.7 + .2 * n2)
            heap = math.exp(-((x / .17) ** 2 + (y / .12) ** 2))
            ridges = abs(math.sin(x * 38 + 4 * noise.noise(Vector((u * 4, v * 4, 3))))) * .022 * (.3 + heap)
            z = .006 + .075 * heap * (.7 + .3 * noise.noise(Vector((u * 5, v * 5, 9)))) + ridges + max(0.0, noise.noise(Vector((x * 20, y * 20, 2)))) * .01
            verts[i, j] = bm.verts.new((x, y, z))
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((verts[i, j], verts[i + 1, j], verts[i + 1, j + 1], verts[i, j + 1]))
    bm.normal_update()
    me = bpy.data.meshes.new('mess_towel')
    bm.to_mesh(me)
    me.uv_layers.new(name='UVMap')
    for k, loop in enumerate(me.loops):
        co = me.vertices[loop.vertex_index].co
        me.uv_layers[0].data[k].uv = (co.x / w + .5, co.y / d + .5)
    obj = bpy.data.objects.new('mess_towel', me)
    bpy.context.scene.collection.objects.link(obj)
    sol = obj.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = .006
    sol.offset = -1
    tex = bpy.data.textures.new('mess_towel_terry', 'CLOUDS')
    tex.noise_scale = .004
    disp = obj.modifiers.new('Terry', 'DISPLACE')
    disp.texture = tex
    disp.strength = .0025
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(material('mess_towel_cotton', (.93, .91, .86), .95, .6))
    export(obj, 'mess_towel')


def trash_bag():
    """Tied 30 L bag (about 32 cm high): lathe profile with lumpy contents, gathered neck and knot."""
    reset()
    profile = [(.0, .0), (.13, .004), (.18, .025), (.19, .07), (.185, .13), (.165, .19), (.13, .235), (.085, .265), (.04, .285),
               (.024, .298), (.03, .31), (.024, .322), (.0, .326)]
    # Densify the profile so the plastic creases have vertices to live on.
    dense = []
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        for t in range(3):
            dense.append((r0 + (r1 - r0) * t / 3, z0 + (z1 - z0) * t / 3))
    dense.append(profile[-1])
    seg = 72
    bm = bmesh.new()
    rings = []
    for r, z in dense:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            # Slumped, slightly oval bag with lumpy contents, vertical plastic creases and the gathered neck.
            lump = 1 + .08 * noise.noise(Vector((math.cos(a) * 2.5, math.sin(a) * 2.5, z * 8)))
            crease = .025 * noise.noise(Vector((math.cos(a) * 14, math.sin(a) * 14, z * 3))) * (z / .3)
            gather = .12 * math.sin(a * 11) if z > .25 else 0
            rr = max(0.0, r * (lump + crease + gather))
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a) * .82, z - .012 * max(0.0, math.cos(a)) * (z / .3))))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    # The two "ears" of the knot: flattened plastic flaps above the tie.
    for side in (1, -1):
        flap = []
        for i in range(7):
            row = []
            for j in range(5):
                t, w = i / 6, (j / 4 - .5)
                row.append(bm.verts.new((side * (.012 + .05 * t), w * (.035 - .02 * t) + .006 * math.sin(t * 6), .318 + .035 * math.sin(t * 2.2) - .02 * t * t)))
            flap.append(row)
        for i in range(6):
            for j in range(4):
                bm.faces.new((flap[i][j], flap[i + 1][j], flap[i + 1][j + 1], flap[i][j + 1]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('mess_trash_bag')
    bm.to_mesh(me)
    obj = bpy.data.objects.new('mess_trash_bag', me)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.cylinder_project()
    bpy.ops.object.mode_set(mode='OBJECT')
    sol = obj.modifiers.new('Plastic', 'SOLIDIFY')
    sol.thickness = .0012
    sub = obj.modifiers.new('Smooth', 'SUBSURF')
    sub.levels = 1
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(material('mess_trash_plastic', (.05, .055, .06), .35))
    export(obj, 'mess_trash_bag')


towel()
trash_bag()
