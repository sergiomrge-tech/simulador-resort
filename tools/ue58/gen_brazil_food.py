"""Brazilian beach-kiosk food (04/11, Sergio: "o tema é brasileiro... açaí, milho, churrasco"). No free commercial
models of these (Poly Haven has none; the Fab corn scans are a concrete statue or paid for commercial use), so they are
modelled here with real relief and their own painted textures:
  Dish_milho_verde      corn on the cob, kernels in relief, melting butter, on a paper tray
  Dish_espetinho        churrasco skewer: beef cubes with grill marks, onion and pepper on a bamboo stick, on a tray
  Dish_queijo_coalho    grilled coalho cheese on a stick (golden, grill marks), on a tray
  Dish_guarana          355 ml can, green with a red/white label band
Metres, Blender Z up, base at z=0 (they sit on tables and in hands like the other Dish_* meshes); unique names
(Food_<dish>_*) for materials and images. Output D:/CodexTemp/food/<name>.glb
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_brazil_food.py"""
import math
import os
import random

import bpy
import bmesh
import numpy as np
from mathutils import Vector

OUT = 'D:/CodexTemp/food'
os.makedirs(OUT, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def image(name, w, h, fill):
    """fill(u, v) -> (r, g, b) arrays over the grid; packed into the .blend so the GLB embeds it."""
    u, v = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    r, g, b = fill(u, v)
    px = np.stack([np.clip(r, 0, 1), np.clip(g, 0, 1), np.clip(b, 0, 1), np.ones_like(r)], -1).astype(np.float32)
    img = bpy.data.images.new(name, w, h)
    img.pixels.foreach_set(px.ravel())
    img.pack()
    return img


def mat(name, img=None, color=(1, 1, 1), rough=.6, metal=0.0, spec=.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if img:
        t = m.node_tree.nodes.new('ShaderNodeTexImage')
        t.image = img
        m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    return m


def link(bm, name, m, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = smooth
    return o


def uv_cyl(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=.1)
    bpy.ops.object.mode_set(mode='OBJECT')
    o.select_set(False)


def rbox(size, loc, m, bevel=.004, name='box', rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for vv in bm.verts:
        vv.co = Vector((vv.co.x * size[0], vv.co.y * size[1], vv.co.z * size[2]))
    o = link(bm, name, m)
    if bevel:
        md = o.modifiers.new('b', 'BEVEL')
        md.width = bevel
        md.segments = 3
    o.rotation_euler = rot
    o.location = loc
    uv_cyl(o)
    return o


def cyl(r, depth, loc, m, rot=(0, 0, 0), seg=16, name='cyl', r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    o = link(bm, name, m)
    o.rotation_euler = rot
    o.location = loc
    uv_cyl(o)
    return o


def tray(prefix, w=.2, d=.09):
    """Paper food tray (boat) with folded walls."""
    paper = image(f'{prefix}_paper', 128, 128, lambda u, v: (.93 - .03 * np.sin(u * 60), .91 - .03 * np.sin(u * 60), .86 + 0 * u))
    m = mat(f'{prefix}_Tray', paper, rough=.85)
    rbox((w, d, .004), (0, 0, .002), m, .001, 'tray_base')
    for s in (-1, 1):
        # Walls a little shorter than the base so the flared corners do not cross each other.
        rbox((w - .012, .004, .025), (0, s * (d / 2 - .002), .014), m, .001, 'tray_wall', (s * .35, 0, 0))
        rbox((.004, d - .012, .025), (s * (w / 2 - .002), 0, .014), m, .001, 'tray_wall', (0, -s * .35, 0))


def finish(name):
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for md in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = o.data.name = name
    lo = min(v.co.z for v in o.data.vertices)
    for v in o.data.vertices:
        v.co.z -= lo
    dims = [round(max(v.co[i] for v in o.data.vertices) - min(v.co[i] for v in o.data.vertices), 3) for i in range(3)]
    print(name, 'dims', dims, 'verts', len(o.data.vertices))
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/{name}.glb', export_format='GLB', export_apply=True)


def milho():
    reset()
    P = 'Food_milho'
    tray(P, .21, .085)
    kern = image(f'{P}_kernels', 256, 256, lambda u, v: (.98 - .05 * np.sin(u * 160) ** 2, .80 - .08 * np.sin(v * 120) ** 2, .25 + .05 * np.sin(u * 160)))
    m = mat(f'{P}_Kernel', kern, rough=.35)
    # Cob: radial rows of kernels (each a bulge), along X, tapered ends.
    L, R, rows, cols = .17, .026, 14, 34
    bm = bmesh.new()
    rings = []
    for i in range(cols * 3 + 1):
        x = -L / 2 + L * i / (cols * 3)
        t = abs(x) / (L / 2)
        taper = math.sqrt(max(0.0, 1 - t ** 6)) * (1 - .12 * (x > 0) * t)
        ring = []
        for j in range(rows * 3):
            a = 2 * math.pi * j / (rows * 3)
            bump = .0026 * abs(math.sin(math.pi * (i % 3) / 3 + .5)) * abs(math.sin(math.pi * (j % 3) / 3 + .5))
            r = (R + bump) * taper + .002
            ring.append(bm.verts.new((x, r * math.cos(a), r * math.sin(a))))
        rings.append(ring)
    n = rows * 3
    for i in range(len(rings) - 1):
        for j in range(n):
            bm.faces.new((rings[i][j], rings[i][(j + 1) % n], rings[i + 1][(j + 1) % n], rings[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cob = link(bm, 'cob', m)
    uv_cyl(cob)
    cob.location = (0, 0, .034)
    # Melting butter on top and the cob's stem end.
    butter = mat(f'{P}_Butter', None, (.99, .9, .45), .2)
    rbox((.035, .022, .009), (.01, 0, .062), butter, .004, 'butter', (0, .1, .2))
    stem = mat(f'{P}_Stem', None, (.62, .58, .38), .8)
    cyl(.012, .025, (-L / 2 - .006, 0, .034), stem, (0, math.pi / 2, 0), 12, 'stem')
    finish('Dish_milho_verde')


def espeto(prefix, pieces, stick_len=.24):
    bamboo = mat(f'{prefix}_Bamboo', None, (.78, .66, .44), .7)
    cyl(.0028, stick_len, (0, 0, .03), bamboo, (0, math.pi / 2, 0), 8, 'stick', None)
    x = -stick_len / 2 + .05
    for m, size in pieces:
        rbox(size, (x + size[0] / 2, 0, .03), m, min(size) * .25, 'piece', (random.uniform(-.15, .15), 0, random.uniform(-.2, .2)))
        x += size[0] + .004


def espetinho():
    reset()
    random.seed(7)
    P = 'Food_espetinho'
    tray(P, .27, .07)
    meat = image(f'{P}_meat', 128, 128, lambda u, v: (
        .42 - .28 * (np.sin(u * 40) > .7) + .05 * np.sin(v * 90), .18 - .12 * (np.sin(u * 40) > .7), .1 - .07 * (np.sin(u * 40) > .7)))
    mm = mat(f'{P}_Beef', meat, rough=.55)
    onion = mat(f'{P}_Onion', None, (.92, .86, .74), .4)
    pepper = mat(f'{P}_Pepper', None, (.12, .45, .1), .35)
    seq = [(mm, (.028, .026, .026)), (onion, (.012, .03, .03)), (mm, (.028, .027, .025)), (pepper, (.01, .03, .028)),
           (mm, (.027, .026, .027)), (onion, (.012, .03, .03)), (mm, (.028, .026, .026))]
    espeto(P, seq)
    finish('Dish_espetinho')


def queijo():
    reset()
    random.seed(3)
    P = 'Food_queijo'
    tray(P, .24, .07)
    cheese = image(f'{P}_cheese', 128, 128, lambda u, v: (
        .95 - .5 * (np.sin(u * 34) > .75), .7 - .45 * (np.sin(u * 34) > .75) + .05 * np.sin(v * 40), .3 - .22 * (np.sin(u * 34) > .75)))   # golden grilled crust
    mc = mat(f'{P}_Cheese', cheese, rough=.5)
    bamboo = mat(f'{P}_Bamboo', None, (.78, .66, .44), .7)
    cyl(.003, .24, (0, 0, .025), bamboo, (0, math.pi / 2, 0), 8, 'stick')
    rbox((.1, .03, .022), (.035, 0, .025), mc, .006, 'cheese')
    finish('Dish_queijo_coalho')


def guarana():
    reset()
    P = 'Food_guarana'

    def label(u, v):
        band = (v > .32) & (v < .7)
        stripe = (v > .48) & (v < .54)
        r = np.where(band, np.where(stripe, .95, .78), .08)
        g = np.where(band, np.where(stripe, .95, .1), .48)
        b = np.where(band, np.where(stripe, .95, .1), .12)
        return r, g, b
    m = mat(f'{P}_Can', image(f'{P}_label', 256, 128, label), rough=.25, metal=.6)
    alu = mat(f'{P}_Lid', None, (.8, .8, .82), .3, .9)
    # Lathe profile of a 355 ml can (radius, z) in metres.
    prof = [(.0, .0), (.024, .0), (.0315, .006), (.033, .014), (.033, .108), (.03, .116), (.027, .121), (.0265, .123)]
    seg = 40
    bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)] for r, z in prof]
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    body = link(bm, 'can', m)
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cylinder_project()
    bpy.ops.object.mode_set(mode='OBJECT')
    cyl(.0265, .004, (0, 0, .123), alu, (0, 0, 0), seg, 'lid')
    rbox((.018, .009, .0015), (.006, 0, .1255), alu, .0007, 'tab')
    finish('Dish_guarana')


if __name__ == '__main__':
    for f in (milho, espetinho, queijo, guarana):
        f()
