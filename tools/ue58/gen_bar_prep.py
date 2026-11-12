"""Bar do Coqueiro physical prep (CHECKLIST_EXPANSOES 1.1, 04/11). Free first: the lime is Poly Haven food_lime_01
(CC0, downloaded to D:/CodexTemp/barprep/dl); nothing free with a commercial licence covers the rest (bottles with
Brazilian labels, passion fruit, mint, condensed milk, a highball whose contents show in layers), so it is modelled
here: turned profiles with relief, painted textures, no bare primitives.

Shelf props (the player aims at one and presses E to pick the ingredient up):
  BarPrep_bench                 rustic prep bench with a lower shelf, set against the back panel
  BarPrep_cachaca / _vodka / _rum / _agua_gas   bottles with labels
  BarPrep_limao / _morango / _maracuja           small wooden crates of fruit
  BarPrep_abacaxi               pineapple on a cutting board
  BarPrep_coco                  coconut-milk bottle;  BarPrep_leite_condensado  can
  BarPrep_hortela               mint sprigs in a glass of water;  BarPrep_acucar  sugar jar with a spoon
  BarPrep_gelo                  ice bucket full of cubes
  BarPrep_shaker / _muddler / _blender            the tools of the three mini-actions
In the hand (Dish_bar_<id>): one bottle, one fruit, a sprig, a spoon of sugar, an ice scoop...
The work glass and its layers, each its own mesh so the bar shows exactly what is in it:
  BarPrep_glass (clear highball), BarPrep_layer_ice, BarPrep_layer_fruit, BarPrep_layer_liquid (tinted in game),
  BarPrep_layer_foam.
Metres, Blender Z up, base at z=0, front -Y. Unique BarPrep_<model>_* names for materials and images (Interchange
reuses names project-wide). Output D:/CodexTemp/barprep/<name>.glb
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_bar_prep.py [name ...]"""
import math
import os
import random
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix

OUT = 'D:/CodexTemp/barprep'
LIME = 'D:/CodexTemp/barprep/dl/food_lime_01_1k.gltf'
os.makedirs(OUT, exist_ok=True)
TAU = 2 * math.pi


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def image(name, w, h, fill):
    u, v = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    r, g, b = fill(u, v)
    px = np.stack([np.clip(r, 0, 1), np.clip(g, 0, 1), np.clip(b, 0, 1), np.ones_like(r)], -1).astype(np.float32)
    img = bpy.data.images.new(name, w, h)
    img.pixels.foreach_set(px.ravel())
    img.pack()
    return img


def mat(name, img=None, color=(1, 1, 1), rough=.6, metal=0.0, alpha=1.0):
    if isinstance(color, (int, float)):
        color, rough = (1, 1, 1), color
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
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    return m


def obj(bm, name, m, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    if isinstance(m, (list, tuple)):
        for x in m:
            o.data.materials.append(x)
    else:
        o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = smooth
    return o


def lathe(prof, m, seg=32, name='lathe', radial=None, uv_v=None):
    """Turned surface from (radius, z) pairs, bottom to top; first/last radius 0 close it. radial(a, z, r) -> r'
    adds relief. UV: u around, v along the profile length (or uv_v(z))."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new()
    rings = []
    for r, z in prof:
        ring = []
        for k in range(seg):
            a = TAU * k / seg
            rr = radial(a, z, r) if (radial and r > 0) else r
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        rings.append(ring)
    L = [0.0]
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        L.append(L[-1] + math.hypot(r1 - r0, z1 - z0))
    tot = L[-1] or 1
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(seg):
            k2 = (k + 1) % seg
            f = bm.faces.new((a[k], a[k2], b[k2], b[k]))
            for lp, (uu, vv) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                lp[uvl].uv = (uu / seg, uv_v(prof[vv][1]) if uv_v else L[vv] / tot)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj(bm, name, m)


def rbox(size, loc, m, bevel=.004, name='box', rot=(0, 0, 0), uvscale=1.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for vv in bm.verts:
        vv.co = Vector((vv.co.x * size[0], vv.co.y * size[1], vv.co.z * size[2]))
    o = obj(bm, name, m, smooth=False)
    if bevel:
        md = o.modifiers.new('b', 'BEVEL')
        md.width = bevel
        md.segments = 2
        md.limit_method = 'ANGLE'
    o.rotation_euler = rot
    o.location = loc
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=uvscale)
    bpy.ops.object.mode_set(mode='OBJECT')
    o.select_set(False)
    return o


def place(o, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0):
    o.location = loc
    o.rotation_euler = rot
    o.scale = (scale, scale, scale) if not isinstance(scale, tuple) else scale
    return o


def dup(o, loc, rot=(0, 0, 0), scale=1.0):
    c = o.copy()
    c.data = o.data.copy()
    bpy.context.collection.objects.link(c)
    return place(c, loc, rot, scale)


def finish(name, keep_base=True):
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for md in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=md.name)
    for o in objs:
        o.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = o.data.name = name
    if keep_base:
        lo = min(v.co.z for v in o.data.vertices)
        for v in o.data.vertices:
            v.co.z -= lo
    dims = [round(max(v.co[i] for v in o.data.vertices) - min(v.co[i] for v in o.data.vertices), 3) for i in range(3)]
    print(name, 'dims', dims, 'verts', len(o.data.vertices))
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/{name}.glb', export_format='GLB', export_apply=True)


# ---------------------------------------------------------------- textures
def wood_img(P, base=(.42, .27, .15), w=256, h=256, planks=1):
    def fill(u, v):
        grain = .5 + .5 * np.sin(v * 90 + 6 * np.sin(u * 7 + v * 3) + 3 * np.sin(u * 23))
        rings = .5 + .5 * np.sin(u * 40 + 2 * np.sin(v * 11))
        seam = (np.mod(u * planks, 1) < .015).astype(float) * .35
        k = .78 + .14 * grain + .08 * rings - seam
        return base[0] * k, base[1] * k, base[2] * k
    return image(f'{P}_wood', w, h, fill)


def label_img(P, bg, band, ink, w=256, h=128, stripes=3):
    """Bottle label: background with a central band and lines of 'lettering' (thin dark dashes)."""
    def fill(u, v):
        r = np.full_like(u, bg[0]); g = np.full_like(u, bg[1]); b = np.full_like(u, bg[2])
        inband = (v > .38) & (v < .62)
        for c, src in ((r, 0), (g, 1), (b, 2)):
            c[inband] = band[src]
        letters = np.zeros_like(u, dtype=bool)
        for s in range(stripes):
            y0 = .2 + s * .24 if s != 1 else .46
            row = (v > y0) & (v < y0 + (.07 if s == 1 else .035))
            dash = np.mod(u * (26 if s == 1 else 46) + s * .3, 1) < .62
            front = (u > .3) & (u < .7)
            letters |= row & dash & front
        for c, src in ((r, 0), (g, 1), (b, 2)):
            c[letters] = ink[src]
        frame = ((np.abs(v - .06) < .015) | (np.abs(v - .94) < .015))
        for c, src in ((r, 0), (g, 1), (b, 2)):
            c[frame] = band[src]
        return r, g, b
    return image(f'{P}_label', w, h, fill)


# ---------------------------------------------------------------- bench
def bench():
    reset()
    P = 'BarPrep_bench'
    top = mat(f'{P}_Top', wood_img(P + 'top', (.47, .31, .18), planks=5), rough=.55)
    frame = mat(f'{P}_Frame', wood_img(P + 'frame', (.33, .21, .12)), rough=.7)
    W, D, H = 2.6, .42, .95
    # Top of five planks with small gaps, a front lip, legs, rails and a slatted lower shelf.
    for i in range(5):
        rbox((W, D / 5 - .004, .035), (0, -D / 2 + D / 10 + i * D / 5, H - .0175), top, .004, 'plank', uvscale=.6)
    rbox((W + .02, .03, .05), (0, -D / 2 - .012, H - .03), frame, .006, 'lip')
    for sx in (-1, 0, 1):
        for sy in (-1, 1):
            rbox((.06, .06, H - .035), (sx * (W / 2 - .05), sy * (D / 2 - .05), (H - .035) / 2), frame, .006, 'leg')
    for sy in (-1, 1):
        rbox((W - .1, .04, .07), (0, sy * (D / 2 - .05), H - .09), frame, .005, 'rail')
        rbox((W - .1, .04, .05), (0, sy * (D / 2 - .05), .3), frame, .005, 'rail_low')
    for i in range(7):
        rbox((W - .14, .052, .02), (0, -D / 2 + .08 + i * .045, .335), top, .003, 'slat', uvscale=.6)
    # Back splash board against the panel, with a rail for the tools.
    rbox((W, .025, .16), (0, D / 2 - .012, H + .08), frame, .005, 'splash')
    finish('BarPrep_bench')


# ---------------------------------------------------------------- bottles
BOTTLES = {
    # id: (glass rgb, liquid rgb or None, label bg, band, ink, profile kind)
    'cachaca': ((.82, .86, .78), (.93, .82, .55), (.95, .9, .74), (.2, .45, .25), (.15, .12, .08), 'tall'),
    'vodka': ((.86, .9, .93), (.92, .95, .97), (.97, .97, .97), (.12, .25, .55), (.1, .1, .15), 'slim'),
    'rum': ((.42, .24, .1), None, (.92, .86, .7), (.55, .12, .08), (.12, .08, .05), 'squat'),
    'agua_gas': ((.25, .55, .35), None, (.85, .93, .97), (.15, .45, .75), (.05, .15, .3), 'small'),
}
PROFILES = {
    'tall': [(0, 0), (.036, 0), (.039, .006), (.039, .2), (.035, .228), (.019, .262), (.0135, .275), (.0135, .312), (.016, .316), (.016, .322), (.0135, .324)],
    'slim': [(0, 0), (.033, 0), (.035, .006), (.035, .215), (.03, .24), (.016, .268), (.013, .28), (.013, .318), (.0155, .322), (.0155, .328), (.013, .33)],
    'squat': [(0, 0), (.046, 0), (.049, .008), (.049, .155), (.041, .182), (.019, .205), (.0155, .222), (.0155, .245), (.018, .249), (.018, .255), (.015, .257)],
    'small': [(0, 0), (.03, 0), (.032, .005), (.032, .12), (.027, .15), (.013, .185), (.0115, .215), (.0135, .219), (.0135, .224), (.011, .226)],
}


def bottle_parts(bid, P):
    glass_rgb, liquid, bg, band, ink, kind = BOTTLES[bid]
    prof = PROFILES[kind]
    gl = mat(f'{P}_Glass', None, glass_rgb, rough=.08, metal=.1)
    lb = mat(f'{P}_Label', label_img(P, bg, band, ink), rough=.6)
    cap = mat(f'{P}_Cap', None, (.75, .6, .25) if kind != 'small' else (.8, .8, .82), rough=.35, metal=.7)
    body = prof[:-3] + [(prof[-4][0] - .002, prof[-4][1] + .001), (0, prof[-4][1] + .001)]
    lathe(body, gl, 36, 'glass')
    if liquid:
        # The spirit visible through the shoulder: a slightly smaller turned volume, 85% full.
        li = mat(f'{P}_Spirit', None, liquid, rough=.05)
        h = prof[3][1] * .9
        lathe([(0, .004), (prof[3][0] - .004, .004), (prof[3][0] - .004, h), (0, h)], li, 36, 'spirit')
    r = prof[3][0]
    z0, z1 = prof[3][1] * .28, prof[3][1] * .72
    lathe([(r + .0008, z0), (r + .0008, z1)], lb, 36, 'label', uv_v=lambda z: (z - z0) / (z1 - z0))
    nz = prof[-4][1]
    lathe([(0, nz - .006), (prof[-3][0] + .0015, nz - .006), (prof[-3][0] + .0015, prof[-1][1] + .006), (0, prof[-1][1] + .007)], cap, 20, 'cap')
    # Neck strip label.
    lathe([(prof[6][0] + .0006, prof[5][1] + .004), (prof[6][0] + .0006, prof[5][1] + .02)], lb, 24, 'neck',
          uv_v=lambda z: .45 + (z - prof[5][1]) * 2)


def bottle(bid):
    reset()
    P = f'BarPrep_{bid}'
    bottle_parts(bid, P)
    finish(P)


# ---------------------------------------------------------------- fruit
def import_lime():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=LIME)
    lime = [o for o in bpy.data.objects if o.type == 'MESH' and o not in before][0]
    if lime.parent:
        mw = lime.matrix_world.copy()
        lime.parent = None
        lime.matrix_world = mw
    bpy.ops.object.select_all(action='DESELECT')
    lime.select_set(True)
    bpy.context.view_layer.objects.active = lime
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    lo = min(v.co.z for v in lime.data.vertices)
    for v in lime.data.vertices:
        v.co.z -= lo
    for m in lime.data.materials:
        if m.name.startswith('BarPrep'):
            continue
        m.name = 'BarPrep_limao_Peel'
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image and not n.image.name.startswith('BarPrep'):
                n.image.name = 'BarPrep_limao_' + n.image.name
                n.image.pack()
    return lime


def strawberry(P, m_red, m_leaf, seed=0):
    """Heart-shaped turned berry with seed dimples and a five-leaf calyx; tip down at z=0."""
    rnd = random.Random(seed)
    prof = [(0, 0), (.006, .002), (.012, .008), (.016, .016), (.0175, .024), (.0165, .031), (.012, .036), (.004, .038), (0, .0382)]

    def bumps(a, z, r):
        return r * (1 + .03 * math.sin(a * 9 + z * 400) * math.sin(z * 520))
    s = lathe(prof, m_red, 18, 'berry', bumps)
    for k in range(5):
        a = TAU * k / 5 + rnd.random() * .3
        bm = bmesh.new()
        pts = [(0, 0), (.004, .006), (.003, .013), (0, .016), (-.003, .013), (-.004, .006)]
        vs = [bm.verts.new((x, y, 0)) for x, y in pts]
        bm.faces.new(vs)
        leaf = obj(bm, 'sepal', m_leaf)
        md = leaf.modifiers.new('s', 'SOLIDIFY')
        md.thickness = .0008
        place(leaf, (0, 0, .0375), (0.35, 0, a - math.pi / 2))
    st = lathe([(0, .036), (.0012, .036), (.0012, .046), (0, .0465)], m_leaf, 8, 'stem')
    return s


def passion_fruit(P, m_skin, m_stem, seed=0):
    rnd = random.Random(seed)
    prof = [(0, 0)] + [(.034 * math.sin(math.pi * t), .072 * (1 - math.cos(math.pi * t)) / 2) for t in np.linspace(.08, .92, 12)] + [(0, .072)]

    def wrinkle(a, z, r):
        return r * (1 + .025 * math.sin(a * 5 + rnd.random() * .2 + z * 90) * math.sin(z * 140 + a * 3) + .012 * math.sin(a * 13 + z * 300))
    f = lathe(prof, m_skin, 28, 'fruit', wrinkle)
    lathe([(0, .07), (.0025, .07), (.0018, .082), (0, .083)], m_stem, 8, 'stem')
    return f


def crate(P, W=.26, D=.18, H=.09):
    """Small open slatted wooden crate (fruit boxes on the bench)."""
    m = mat(f'{P}_Crate', wood_img(P + 'crate', (.62, .47, .3), 128, 128, 3), rough=.8)
    rbox((W, D, .008), (0, 0, .004), m, .002, 'floor')
    for sy in (-1, 1):
        for z in (.025, .06):
            rbox((W, .008, .026), (0, sy * (D / 2 - .004), z), m, .002, 'slat')
    for sx in (-1, 1):
        rbox((.012, D, H), (sx * (W / 2 - .006), 0, H / 2), m, .002, 'end')
        rbox((.008, .05, .015), (sx * (W / 2 - .006), 0, H - .025), mat(f'{P}_Hole', None, (.08, .06, .04), .9), 0, 'grip')
    return W, D, H


def fill_crate(objs_fn, W, D, n, z0=.008, seed=1):
    rnd = random.Random(seed)
    cols = max(1, int(round(math.sqrt(n * W / D))))
    rows = max(1, int(math.ceil(n / cols)))
    i = 0
    for r in range(rows):
        for c in range(cols):
            if i >= n:
                break
            x = -W / 2 + W * (c + .5) / cols + rnd.uniform(-.006, .006)
            y = -D / 2 + D * (r + .5) / rows + rnd.uniform(-.006, .006)
            objs_fn(x, y, z0, rnd)
            i += 1


def limao():
    reset()
    P = 'BarPrep_limao'
    W, D, H = crate(P)
    lime = import_lime()

    def put(x, y, z, rnd):
        dup(lime, (x, y, z + .028), (rnd.uniform(1.3, 1.8), rnd.uniform(-.3, .3), rnd.uniform(0, TAU)), .98)
    fill_crate(put, W - .03, D - .03, 8)
    fill_crate(lambda x, y, z, rnd: dup(lime, (x + .02, y, z + .075), (rnd.uniform(1.3, 1.8), 0, rnd.uniform(0, TAU))), W - .1, D - .07, 3, seed=5)
    bpy.data.objects.remove(lime)
    finish(P)


def morango():
    reset()
    P = 'BarPrep_morango'
    W, D, H = crate(P, .22, .16, .075)
    red = mat(f'{P}_Berry', image(f'{P}_berry', 128, 128, lambda u, v: (
        .78 - .25 * ((np.mod(u * 14 + .5 * np.floor(v * 9), 1) < .12) & (np.mod(v * 9, 1) < .25)) + .1 * v,
        .06 + .2 * ((np.mod(u * 14 + .5 * np.floor(v * 9), 1) < .12) & (np.mod(v * 9, 1) < .25)) + .02 * v,
        .08 + 0 * u)), rough=.35)
    leaf = mat(f'{P}_Calyx', None, (.18, .45, .12), .6)
    berry = strawberry(P, red, leaf)
    parts = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(('berry', 'sepal', 'stem'))]
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = berry
    for o in parts:
        bpy.context.view_layer.objects.active = o
        for md in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = berry
    bpy.ops.object.join()

    def put(x, y, z, rnd):
        dup(berry, (x, y, z + .018), (rnd.uniform(1.2, 1.9), 0, rnd.uniform(0, TAU)))
    fill_crate(put, W - .03, D - .03, 14)
    fill_crate(lambda x, y, z, rnd: dup(berry, (x, y, z + .045), (rnd.uniform(1.2, 1.9), 0, rnd.uniform(0, TAU))), W - .08, D - .07, 5, seed=7)
    bpy.data.objects.remove(berry)
    finish(P)


def maracuja():
    reset()
    P = 'BarPrep_maracuja'
    W, D, H = crate(P)
    skin = mat(f'{P}_Skin', image(f'{P}_skin', 256, 128, lambda u, v: (
        .85 + .1 * np.sin(u * 50) * np.sin(v * 40) - .25 * (np.mod(u * 37 + v * 13, 1) < .04),
        .7 + .1 * np.sin(u * 30 + v * 20) - .3 * (np.mod(u * 37 + v * 13, 1) < .04),
        .18 + .05 * np.sin(u * 70) + 0 * v)), rough=.45)
    stem = mat(f'{P}_Stem', None, (.35, .4, .18), .7)
    fruit = passion_fruit(P, skin, stem)
    st = [o for o in bpy.data.objects if o.name.startswith('stem')][0]
    bpy.ops.object.select_all(action='DESELECT')
    fruit.select_set(True)
    st.select_set(True)
    bpy.context.view_layer.objects.active = fruit
    bpy.ops.object.join()

    def put(x, y, z, rnd):
        dup(fruit, (x, y, z + .036), (math.pi / 2 + rnd.uniform(-.3, .3), 0, rnd.uniform(0, TAU)))
    fill_crate(put, W - .04, D - .04, 6)
    fill_crate(lambda x, y, z, rnd: dup(fruit, (x, y, z + .095), (math.pi / 2, 0, rnd.uniform(0, TAU))), W - .12, D - .09, 2, seed=3)
    bpy.data.objects.remove(fruit)
    finish(P)


def pineapple_parts(P, scale=1.0, loc=(0, 0, 0)):
    peel = mat(f'{P}_Peel', image(f'{P}_peel', 256, 256, lambda u, v: (
        .62 + .2 * np.abs(np.sin((u * 16 + v * 9) * math.pi) * np.sin((u * 16 - v * 9) * math.pi)) ** .5 - .2 * (np.abs(np.sin((u * 16 + v * 9) * math.pi)) < .15),
        .42 + .15 * np.abs(np.sin((u * 16 + v * 9) * math.pi) * np.sin((u * 16 - v * 9) * math.pi)) ** .5 - .15 * (np.abs(np.sin((u * 16 + v * 9) * math.pi)) < .15),
        .12 + 0 * u)), rough=.6)
    leaf = mat(f'{P}_Crown', None, (.22, .42, .2), .55)
    H, R = .2 * scale, .065 * scale
    prof = [(0, 0), (R * .55, 0)] + [(R * math.sin(math.pi * (.15 + .7 * t)) ** .7, H * t) for t in np.linspace(.04, .96, 14)] + [(R * .5, H), (0, H)]

    def eyes(a, z, r):
        return r * (1 + .05 * abs(math.sin(a * 8 + z / H * 9 * math.pi) * math.sin(a * 8 - z / H * 9 * math.pi)))
    body = lathe(prof, peel, 40, 'pine', eyes)
    body.location = loc
    rnd = random.Random(4)
    for k in range(22):
        a = TAU * k / 11 + (k // 11) * .3
        L = (.09 + .06 * rnd.random() - .03 * (k // 11)) * scale
        bm = bmesh.new()
        pts = [(-.008 * scale, 0), (.008 * scale, 0), (.004 * scale, L * .6), (0, L), (-.004 * scale, L * .6)]
        vs = [bm.verts.new((x, 0, y)) for x, y in pts]
        bm.faces.new(vs)
        o = obj(bm, 'leaf', leaf)
        md = o.modifiers.new('s', 'SOLIDIFY')
        md.thickness = .0015 * scale
        tilt = .25 + .35 * (k // 11) + rnd.uniform(-.1, .1)
        place(o, (loc[0], loc[1], loc[2] + H - .01 * scale), (tilt, 0, a))


def abacaxi():
    reset()
    P = 'BarPrep_abacaxi'
    board = mat(f'{P}_Board', wood_img(P + 'board', (.66, .48, .3), 128, 128), rough=.65)
    rbox((.32, .2, .022), (0, 0, .011), board, .006, 'board', uvscale=.4)
    rbox((.05, .035, .012), (.17, 0, .011), board, .004, 'handle')
    pineapple_parts(P, 1.0, (-.04, 0, .022))
    # Two cut rings next to it (yellow flesh with the core and the peel rim).
    flesh = mat(f'{P}_Flesh', image(f'{P}_flesh', 128, 128, lambda u, v: (.98 - .1 * v, .85 - .15 * v, .35 + .1 * np.sin(u * 60))), rough=.4)
    for i, (x, y) in enumerate(((.085, -.03), (.1, .045))):
        r = lathe([(0, 0), (.055, 0), (.058, .008), (.055, .016), (0, .016)], flesh, 32, 'ring')
        place(r, (x, y, .022 + i * .004), (0, .08 * i, 0))
    finish(P)


# ---------------------------------------------------------------- other ingredients
def coco():
    reset()
    P = 'BarPrep_coco'
    gl = mat(f'{P}_Glass', None, (.93, .93, .9), .12)
    lb = mat(f'{P}_Label', label_img(P, (.35, .22, .12), (.97, .95, .9), (.25, .15, .08)), .6)
    cap = mat(f'{P}_Cap', None, (.95, .95, .95), .4)
    prof = [(0, 0), (.032, 0), (.034, .006), (.034, .13), (.028, .155), (.017, .17), (.017, .19), (0, .19)]
    lathe(prof, gl, 32, 'bottle')
    lathe([(.0348, .03), (.0348, .11)], lb, 32, 'label', uv_v=lambda z: (z - .03) / .08)
    lathe([(0, .183), (.019, .183), (.019, .2), (0, .201)], cap, 20, 'cap')
    finish(P)


def can_parts(P, bg, band, ink, R=.038, H=.1):
    m = mat(f'{P}_Can', label_img(P, bg, band, ink, 256, 128, 2), rough=.3, metal=.55)
    lid = mat(f'{P}_Lid', None, (.8, .8, .82), .3, .9)
    prof = [(0, 0), (R - .006, 0), (R, .006), (R, H - .006), (R - .002, H - .002), (R - .004, H)]
    lathe(prof, m, 40, 'can', uv_v=lambda z: z / H)
    lathe([(0, H - .002), (R - .0035, H - .002), (R - .0035, H + .001), (0, H + .001)], lid, 40, 'lid')


def leite_condensado():
    reset()
    P = 'BarPrep_leite_condensado'
    can_parts(P, (.2, .35, .7), (.97, .95, .88), (.12, .2, .45))
    finish(P)


def mint_sprig(P, m_leaf, m_stem, rnd, L=.15):
    """A mint sprig: thin stem with opposite pairs of serrated ovate leaves, smaller near the tip."""
    lathe([(0, 0), (.0018, 0), (.0014, L), (0, L + .001)], m_stem, 6, 'mstem')
    pairs = 5
    for i in range(pairs):
        z = L * (.55 + .43 * i / pairs)
        s = 1.0 - .55 * i / pairs
        for side in (0, 1):
            a = side * math.pi + i * math.pi / 2
            bm = bmesh.new()
            n = 14
            pts = []
            for k in range(n + 1):
                t = k / n
                w = .011 * s * math.sin(math.pi * t) ** .8 * (1 + .12 * (k % 2))
                pts.append((w, .03 * s * t))
            pts += [(-x, y) for x, y in reversed(pts[1:-1])]
            vs = [bm.verts.new((x, y, .003 * math.sin(math.pi * y / (.03 * s)))) for x, y in pts]
            bm.faces.new(vs)
            o = obj(bm, 'mleaf', m_leaf)
            md = o.modifiers.new('s', 'SOLIDIFY')
            md.thickness = .0006
            place(o, (math.cos(a) * .002, math.sin(a) * .002, z), (-.5 - .3 * rnd.random(), 0, a - math.pi / 2))


def hortela():
    reset()
    P = 'BarPrep_hortela'
    gl = mat(f'{P}_Glass', None, (.88, .93, .95), .06, .1)
    water = mat(f'{P}_Water', None, (.75, .88, .92), .03)
    leaf = mat(f'{P}_Leaf', image(f'{P}_leaf', 64, 64, lambda u, v: (.2 + .05 * np.sin(u * 30), .5 + .08 * np.sin(v * 20) - .12 * (np.abs(u - .5) < .03), .18 + 0 * u)), .55)
    stem = mat(f'{P}_Stem', None, (.3, .45, .2), .6)
    lathe([(0, 0), (.032, 0), (.034, .004), (.036, .11), (.033, .11), (.031, .006), (0, .006)], gl, 32, 'cup')
    lathe([(0, .006), (.031, .006), (.033, .07), (0, .07)], water, 32, 'water')
    rnd = random.Random(2)
    for k in range(6):
        before = set(bpy.data.objects)
        mint_sprig(P, leaf, stem, rnd, .14 + .04 * rnd.random())
        new = [o for o in bpy.data.objects if o not in before]
        bpy.context.view_layer.update()
        a = TAU * k / 6
        rot = Matrix.Rotation(.12 + .1 * rnd.random(), 4, Vector((math.cos(a + 1.57), math.sin(a + 1.57), 0)))
        for o in new:
            o.matrix_world = Matrix.Translation((math.cos(a) * .012, math.sin(a) * .012, .02)) @ rot @ o.matrix_world
    finish(P)


def acucar():
    reset()
    P = 'BarPrep_acucar'
    gl = mat(f'{P}_Glass', None, (.88, .92, .93), .06, .1)
    sugar = mat(f'{P}_Sugar', image(f'{P}_sugar', 128, 128, lambda u, v: (
        .95 - .08 * (np.mod(u * 97 + v * 61, 1) < .3), .94 - .08 * (np.mod(u * 97 + v * 61, 1) < .3), .9 - .08 * (np.mod(u * 97 + v * 61, 1) < .3))), .8)
    wood = mat(f'{P}_Lid', wood_img(P + 'lid', (.55, .38, .22), 64, 64), .6)
    lathe([(0, 0), (.045, 0), (.048, .006), (.048, .12), (.044, .126), (.044, .135), (0, .135)], gl, 36, 'jar')
    lathe([(0, .006), (.045, .006), (.045, .085), (.03, .09), (0, .092)], sugar, 36, 'sugar',
          lambda a, z, r: r * (1 + (.04 * math.sin(a * 7) if z > .084 else 0)))
    # Lid leaning against the jar and a wooden spoon in the sugar.
    lid = lathe([(0, 0), (.05, 0), (.05, .012), (.046, .016), (0, .016)], wood, 36, 'lid')
    place(lid, (.07, 0, .045), (0, 1.3, 0))
    sp = lathe([(0, 0), (.004, .001), (.004, .16), (0, .161)], wood, 8, 'spoon_handle')
    place(sp, (0.0, 0.0, .07), (.35, 0, 0))
    bowl = lathe([(0, 0), (.012, .004), (.016, .012), (.0, .013)], wood, 16, 'spoon_bowl')
    place(bowl, (0, -.005, .075), (.35, 0, 0))
    finish(P)


def ice_cube(m, size=.024, seed=0):
    rnd = random.Random(seed)
    o = rbox((size, size * rnd.uniform(.85, 1), size * rnd.uniform(.8, 1)), (0, 0, 0), m, size * .18, 'ice', uvscale=.05)
    return o


def gelo():
    reset()
    P = 'BarPrep_gelo'
    metal = mat(f'{P}_Bucket', None, (.78, .78, .8), .25, .95)
    ice = mat(f'{P}_Ice', image(f'{P}_ice', 64, 64, lambda u, v: (.82 + .1 * np.sin(u * 20 + v * 13), .9 + .06 * np.sin(v * 17), .97 + 0 * u)), .08)
    lathe([(0, 0), (.08, 0), (.085, .006), (.095, .15), (.1, .155), (.1, .162), (.092, .162), (.087, .01), (0, .01)], metal, 40, 'bucket')
    for s in (-1, 1):
        lathe([(0, 0), (.012, 0), (.012, .01), (0, .01)], metal, 12, 'lug').location = (s * .1, 0, .13)
    h = bpy.data.curves.new('handle', 'CURVE')
    h.dimensions = '3D'
    sp = h.splines.new('BEZIER')
    sp.bezier_points.add(2)
    for p, co in zip(sp.bezier_points, ((-.1, 0, .135), (0, 0, .245), (.1, 0, .135))):
        p.co = co
        p.handle_left_type = p.handle_right_type = 'AUTO'
    h.bevel_depth = .003
    ho = bpy.data.objects.new('handle', h)
    bpy.context.collection.objects.link(ho)
    ho.data.materials.append(metal)
    bpy.context.view_layer.objects.active = ho
    ho.select_set(True)
    bpy.ops.object.convert(target='MESH')
    rnd = random.Random(3)
    cube = ice_cube(ice)
    for k in range(26):
        r = .07 * math.sqrt(rnd.random())
        a = rnd.random() * TAU
        dup(cube, (r * math.cos(a), r * math.sin(a), .1 + .05 * rnd.random() + (.03 if r < .03 else 0)),
            (rnd.random() * 3, rnd.random() * 3, rnd.random() * 3))
    bpy.data.objects.remove(cube)
    finish(P)


# ---------------------------------------------------------------- tools
def shaker():
    reset()
    P = 'BarPrep_shaker'
    steel = mat(f'{P}_Steel', None, (.85, .85, .87), .18, 1.0)
    lathe([(0, 0), (.034, 0), (.036, .004), (.046, .17), (.046, .175), (.0, .175)], steel, 40, 'tin')
    # Mixing glass cap on top, upside down and offset like a Boston shaker set down.
    gl = mat(f'{P}_Glass', None, (.85, .9, .92), .05, .1)
    lathe([(0, .17), (.044, .17), (.04, .27), (.03, .272), (0, .272)], gl, 36, 'cup')
    finish(P)


def muddler():
    reset()
    P = 'BarPrep_muddler'
    wood = mat(f'{P}_Wood', wood_img(P, (.5, .33, .18), 64, 128), .55)
    m = lathe([(0, 0), (.014, 0), (.015, .004), (.013, .03), (.009, .06), (.009, .19), (.012, .2), (.012, .215), (0, .216)], wood, 20, 'muddler')
    # Lying on the bench.
    place(m, (0, 0, .015), (0, math.pi / 2, 0))
    finish(P)


def blender():
    reset()
    P = 'BarPrep_blender'
    body = mat(f'{P}_Body', None, (.85, .3, .2), .35)
    dark = mat(f'{P}_Dark', None, (.08, .08, .09), .5)
    steel = mat(f'{P}_Steel', None, (.8, .8, .82), .2, 1.0)
    gl = mat(f'{P}_Jar', None, (.86, .9, .92), .05, .1)
    rbox((.16, .16, .1), (0, 0, .05), body, .025, 'base')
    rbox((.03, .012, .02), (0, -.085, .05), dark, .004, 'knob')
    for i, x in enumerate((-.045, .0, .045)):
        rbox((.022, .008, .012), (x, -.081, .075), steel if i == 1 else dark, .003, 'button')
    lathe([(0, .1), (.055, .1), (.06, .115), (.07, .3), (.072, .31), (0, .31)], gl, 32, 'jar')
    lathe([(0, .31), (.074, .31), (.074, .325), (.04, .33), (.03, .345), (0, .346)], dark, 32, 'lid')
    rbox((.02, .05, .12), (.085, 0, .22), gl, .008, 'handle')
    finish(P)


# ---------------------------------------------------------------- the work glass and its layers
GLASS_PROF = [(0, 0), (.032, 0), (.034, .004), (.036, .02), (.038, .14), (.036, .14), (.034, .022), (.03, .012), (0, .012)]


def glass():
    reset()
    P = 'BarPrep_glass'
    gl = mat(f'{P}_Clear', None, (.92, .96, .98), .03, 0, alpha=.12)
    lathe(GLASS_PROF, gl, 40, 'glass')
    finish(P)


def layer_liquid():
    reset()
    P = 'BarPrep_layer_liquid'
    li = mat(f'{P}_Drink', None, (1, 1, 1), .05)
    # Full inner volume to the top (the game scales Z by the fill); white so the game tints it per mix.
    lathe([(0, .012), (.0335, .012), (.0355, .13), (0, .13)], li, 40, 'liquid')
    finish(P, keep_base=False)


def layer_ice():
    reset()
    P = 'BarPrep_layer_ice'
    ice = mat(f'{P}_Ice', image(f'{P}_ice', 64, 64, lambda u, v: (.85 + .08 * np.sin(u * 20 + v * 13), .92 + .05 * np.sin(v * 17), .98 + 0 * u)), .05)
    cube = ice_cube(ice, .022)
    rnd = random.Random(9)
    for k, (x, y, z) in enumerate(((-.012, -.01, .03), (.012, .008, .032), (-.006, .013, .058), (.01, -.012, .06), (0, 0, .088), (-.011, -.004, .11), (.01, .01, .115))):
        dup(cube, (x, y, z), (rnd.random() * 1.5, rnd.random() * 1.5, rnd.random() * 3))
    bpy.data.objects.remove(cube)
    finish(P, keep_base=False)


def layer_fruit():
    reset()
    P = 'BarPrep_layer_fruit'
    flesh = mat(f'{P}_Fruit', image(f'{P}_pulp', 64, 64, lambda u, v: (.95 + 0 * u, .95 + 0 * u, .95 + 0 * u)), .4)
    peel = mat(f'{P}_Peel', None, (.3, .3, .3), .5)
    rnd = random.Random(1)
    # Muddled wedges from the bottom up through the drink (white flesh tinted per fruit in game, darker peel): they
    # show through the translucent liquid and against the glass, like the lime of a caipirinha.
    for k in range(9):
        bm = bmesh.new()
        a0, a1 = 0, math.pi * .55
        n = 6
        rim = [bm.verts.new((.016 * math.cos(a0 + (a1 - a0) * t / n), .016 * math.sin(a0 + (a1 - a0) * t / n), 0)) for t in range(n + 1)]
        c = bm.verts.new((0, 0, 0))
        for i in range(n):
            bm.faces.new((c, rim[i], rim[i + 1]))
        bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
        bmesh.ops.translate(bm, vec=(0, 0, .01), verts=[v for v in bm.verts if v not in rim and v is not c])
        o = obj(bm, 'wedge', [flesh, peel])
        a = k * 2.4
        r = .006 + .016 * rnd.random()
        place(o, (r * math.cos(a), r * math.sin(a), .016 + .0085 * k), (rnd.uniform(-.8, .8), rnd.uniform(-.8, .8), rnd.uniform(0, TAU)))
    finish(P, keep_base=False)


def layer_foam():
    reset()
    P = 'BarPrep_layer_foam'
    foam = mat(f'{P}_Foam', image(f'{P}_foam', 64, 64, lambda u, v: (.97 - .05 * (np.mod(u * 23 + v * 17, 1) < .2), .95 - .05 * (np.mod(u * 23 + v * 17, 1) < .2), .9 + 0 * u)), .7)
    lathe([(0, .118), (.0355, .118), (.0365, .128), (.03, .134), (.015, .137), (0, .1375)], foam, 40, 'foam',
          lambda a, z, r: r * (1 + .03 * math.sin(a * 11) * math.sin(z * 900)))
    finish(P, keep_base=False)


# ---------------------------------------------------------------- what the hand holds
def hand_item(iid):
    """Dish_bar_<id>: one bottle, one fruit, a sprig, the jar, the scoop of ice..."""
    reset()
    P = f'BarPrep_hand_{iid}'
    if iid in BOTTLES:
        bottle_parts(iid, P)
    elif iid == 'limao':
        import_lime()
    elif iid == 'morango':
        red = mat(f'{P}_Berry', None, (.78, .08, .08), .35)
        strawberry(P, red, mat(f'{P}_Calyx', None, (.18, .45, .12), .6))
    elif iid == 'maracuja':
        passion_fruit(P, mat(f'{P}_Skin', None, (.85, .68, .2), .45), mat(f'{P}_Stem', None, (.35, .4, .18), .7))
    elif iid == 'abacaxi':
        pineapple_parts(P, .9)
    elif iid == 'coco':
        coco_parts = None
        gl = mat(f'{P}_Glass', None, (.93, .93, .9), .12)
        lathe([(0, 0), (.032, 0), (.034, .006), (.034, .13), (.028, .155), (.017, .17), (.017, .19), (0, .19)], gl, 32, 'bottle')
        lathe([(.0348, .03), (.0348, .11)], mat(f'{P}_Label', label_img(P, (.35, .22, .12), (.97, .95, .9), (.25, .15, .08)), .6), 32, 'label', uv_v=lambda z: (z - .03) / .08)
    elif iid == 'leite_condensado':
        can_parts(P, (.2, .35, .7), (.97, .95, .88), (.12, .2, .45))
    elif iid == 'hortela':
        mint_sprig(P, mat(f'{P}_Leaf', None, (.22, .52, .2), .55), mat(f'{P}_Stem', None, (.3, .45, .2), .6), random.Random(3), .16)
    elif iid == 'acucar':
        wood = mat(f'{P}_Wood', wood_img(P, (.55, .38, .22), 64, 64), .6)
        sugar = mat(f'{P}_Sugar', None, (.95, .94, .9), .8)
        lathe([(0, 0), (.004, .001), (.004, .16), (0, .161)], wood, 8, 'handle')
        b = lathe([(0, 0), (.016, .005), (.022, .016), (0, .017)], wood, 16, 'bowl')
        place(b, (0, 0, .155))
        s = lathe([(0, 0), (.018, 0), (.01, .01), (0, .012)], sugar, 16, 'heap', lambda a, z, r: r * (1 + .1 * math.sin(a * 7)))
        place(s, (0, 0, .166))
    elif iid == 'gelo':
        metal = mat(f'{P}_Scoop', None, (.8, .8, .82), .25, .95)
        ice = mat(f'{P}_Ice', None, (.85, .93, .98), .05)
        # Bar ice scoop lying on its side: open mouth toward -Y, round back, handle out of the back along +Y.
        body = lathe([(0, 0), (.036, 0), (.04, .1), (.036, .1), (.032, .006), (0, .006)], metal, 24, 'scoop')
        place(body, (0, .05, .04), (math.pi / 2, 0, 0))
        grip = lathe([(0, 0), (.009, 0), (.009, .1), (0, .101)], metal, 10, 'grip')
        place(grip, (0, .045, .04), (-math.pi / 2, 0, 0))
        c = ice_cube(ice, .022)
        for k, (x, y, z) in enumerate(((-.013, -.03, .03), (.013, -.025, .032), (0, -.01, .045), (0, -.042, .028))):
            dup(c, (x, y, z), (k, k * .7, k * 1.3))
        bpy.data.objects.remove(c)
    finish(P)


INGREDIENTS = ['cachaca', 'vodka', 'rum', 'limao', 'maracuja', 'morango', 'abacaxi', 'coco', 'leite_condensado', 'hortela', 'acucar', 'agua_gas', 'gelo']
ALL = {'bench': bench, 'cachaca': lambda: bottle('cachaca'), 'vodka': lambda: bottle('vodka'), 'rum': lambda: bottle('rum'),
       'agua_gas': lambda: bottle('agua_gas'), 'limao': limao, 'morango': morango, 'maracuja': maracuja, 'abacaxi': abacaxi,
       'coco': coco, 'leite_condensado': leite_condensado, 'hortela': hortela, 'acucar': acucar, 'gelo': gelo,
       'shaker': shaker, 'muddler': muddler, 'blender': blender, 'glass': glass, 'layer_liquid': layer_liquid,
       'layer_ice': layer_ice, 'layer_fruit': layer_fruit, 'layer_foam': layer_foam,
       **{f'hand_{i}': (lambda i=i: hand_item(i)) for i in INGREDIENTS}}


# ---------------------------------------------------------------- upgrades (CHECKLIST_EXPANSOES 1.4)
def neon():
    """Neon sign 'Bar do Coqueiro' for the back panel: dark backing board, the script in glowing tubes and a tube
    border; front -Y, base at z=0 (mounted on the panel face)."""
    reset()
    P = 'BarPrep_neon'
    board = mat(f'{P}_Board', wood_img(P + 'board', (.16, .1, .07), 128, 64), rough=.7)
    glow = mat(f'{P}_Glow', None, (1, .45, .75), .3)
    b = glow.node_tree.nodes['Principled BSDF']
    b.inputs['Emission Color'].default_value = (1, .35, .7, 1)
    b.inputs['Emission Strength'].default_value = 6.0
    glow2 = mat(f'{P}_GlowCyan', None, (.4, 1, .95), .3)
    b2 = glow2.node_tree.nodes['Principled BSDF']
    b2.inputs['Emission Color'].default_value = (.3, 1, .9, 1)
    b2.inputs['Emission Strength'].default_value = 6.0
    W, H = 1.2, .26
    rbox((W, .025, H), (0, .0125, H / 2), board, .008, 'board', uvscale=.5)
    bpy.ops.object.text_add(location=(0, 0, 0))
    t = bpy.context.object
    t.data.body = 'Bar do Coqueiro'
    t.data.align_x = 'CENTER'
    t.data.align_y = 'CENTER'
    t.data.size = .085
    t.data.extrude = .004
    t.data.bevel_depth = .004
    t.rotation_euler = (math.pi / 2, 0, 0)
    t.location = (0, -.006, H / 2 + .005)
    bpy.ops.object.convert(target='MESH')
    t.data.materials.clear()
    t.data.materials.append(glow)
    # Tube border with rounded corners.
    c = bpy.data.curves.new('frame', 'CURVE')
    c.dimensions = '3D'
    sp = c.splines.new('POLY')
    pts = []
    r, w, h = .025, W / 2 - .03, H / 2 - .025
    for cx, cz, a0 in ((w - r, h - r, 0), (-w + r, h - r, 90), (-w + r, -h + r, 180), (w - r, -h + r, 270)):
        for k in range(5):
            a = math.radians(a0 + 22.5 * k)
            pts.append((cx + r * math.cos(a), -.008, H / 2 + cz + r * math.sin(a)))
    sp.points.add(len(pts) - 1)
    for p_, co in zip(sp.points, pts):
        p_.co = (*co, 1)
    sp.use_cyclic_u = True
    c.bevel_depth = .004
    fo = bpy.data.objects.new('frame', c)
    bpy.context.collection.objects.link(fo)
    fo.data.materials.append(glow2)
    bpy.context.view_layer.objects.active = fo
    fo.select_set(True)
    bpy.ops.object.convert(target='MESH')
    # Small standoffs holding it.
    steel = mat(f'{P}_Steel', None, (.7, .7, .72), .3, .9)
    for sx in (-1, 1):
        for sz in (-1, 1):
            o = lathe([(0, 0), (.006, 0), (.006, .02), (0, .02)], steel, 10, 'stand')
            place(o, (sx * (W / 2 - .05), .045, H / 2 + sz * (H / 2 - .04)), (math.pi / 2, 0, 0))
    finish(P)


def chopeira():
    """Beer tap tower on a drip tray: chrome T column, two taps with black handles; front -Y, base at z=0."""
    reset()
    P = 'BarPrep_chopeira'
    chrome = mat(f'{P}_Chrome', None, (.85, .86, .88), .12, 1.0)
    black = mat(f'{P}_Handle', None, (.05, .05, .05), .4)
    tray = mat(f'{P}_Tray', None, (.25, .25, .27), .3, .9)
    label = mat(f'{P}_Label', label_img(P, (.95, .78, .15), (.75, .1, .08), (.15, .08, .05), 128, 64, 1), .5)
    rbox((.32, .16, .015), (0, -.04, .0075), tray, .004, 'tray')
    for i in range(9):
        rbox((.3, .006, .004), (0, -.11 + i * .017, .016), chrome, .001, 'grid')
    lathe([(0, 0), (.04, 0), (.04, .01), (.022, .02), (.02, .3), (0, .3)], chrome, 24, 'column')
    for sx in (-1, 1):
        arm = lathe([(0, 0), (.016, 0), (.016, .12), (0, .12)], chrome, 16, 'arm')
        place(arm, (0, 0, .29), (0, sx * math.pi / 2, 0))
        sp = lathe([(0, 0), (.01, 0), (.008, .05), (.004, .06), (0, .06)], chrome, 12, 'spout')
        place(sp, (sx * .11, -.01, .29), (math.pi, 0, 0))
        hd = lathe([(0, 0), (.009, 0), (.012, .08), (.011, .1), (0, .102)], black, 12, 'handle')
        place(hd, (sx * .11, -.02, .3), (-.25, 0, 0))
        lb = rbox((.03, .004, .04), (sx * .11, -.032, .36), label, .002, 'badge', (-.25, 0, 0))
    finish(P)


def freezer():
    """Low chest freezer for under the prep bench: white rounded body, lid with handle, vent strip and a blue stripe."""
    reset()
    P = 'BarPrep_freezer'
    white = mat(f'{P}_Body', None, (.93, .94, .95), .35)
    grey = mat(f'{P}_Trim', None, (.35, .37, .4), .5)
    blue = mat(f'{P}_Stripe', None, (.12, .38, .75), .4)
    L, D, H = 1.0, .36, .46
    rbox((L, D, H - .04), (0, 0, (H - .04) / 2), white, .03, 'body', uvscale=.5)
    rbox((L + .01, D + .01, .045), (0, 0, H - .022), white, .018, 'lid')
    rbox((.3, .025, .025), (0, -D / 2 - .012, H - .045), grey, .008, 'handle')
    rbox((L - .06, .004, .03), (0, -D / 2 - .001, .3), blue, .002, 'stripe')
    for i in range(10):
        rbox((.05, .004, .008), (L / 2 - .12 - i * .02, -D / 2 - .001, .08), grey, .001, 'vent')
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe([(0, 0), (.015, 0), (.015, .012), (0, .012)], grey, 10, 'foot').location = (sx * (L / 2 - .05), sy * (D / 2 - .05), -.012)
    finish(P)


ALL.update({'neon': neon, 'chopeira': chopeira, 'freezer': freezer, 'hand_chope': lambda: hand_chope()})


def hand_chope():
    """A glass of draught beer (falls into the glass, and the drink in the guest's hand)."""
    reset()
    P = 'BarPrep_hand_chope'
    gl = mat(f'{P}_Glass', None, (.9, .93, .95), .05, 0)
    beer = mat(f'{P}_Beer', None, (.95, .68, .12), .1)
    foam = mat(f'{P}_Foam', None, (.98, .96, .9), .7)
    lathe([(0, 0), (.03, 0), (.036, .14), (.033, .14), (.027, .006), (0, .006)], gl, 28, 'glass')
    lathe([(0, .006), (.027, .006), (.0335, .115), (0, .115)], beer, 28, 'beer')
    lathe([(0, .115), (.0335, .115), (.0345, .13), (.02, .136), (0, .137)], foam, 28, 'foam')
    finish(P)

if __name__ == '__main__':
    for n in sys.argv[1:] or list(ALL):
        ALL[n]()
    print('gen_bar_prep ok')
