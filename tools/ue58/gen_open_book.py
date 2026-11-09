"""Open paperback held by a sunbather reading on the towel (C13, 09/11). No free open-book model exists (Poly Haven has
closed sets only), so it is modelled here: a soft cover and two curved page blocks fanning from the spine.
Model axes: spine along X, the open pages face +Z (towards the reader), origin at the spine's centre.
Materials prefixed (mare_book_*) and images packed (Interchange matches materials by name across the project).

  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_open_book.py
-> unreal/MareAlta/SourceArt/Models/Leisure/mare_open_book.glb"""
import math
from pathlib import Path

import bpy
import bmesh

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models/Leisure/mare_open_book.glb'
W, H = 0.13, 0.20          # one page: 13 x 20 cm
COVER, PAGES = 0.003, 0.012


def mat(name, rgb, rough=.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    return m


def page_block(name, side, thickness, lift, material, steps=16):
    """A curved block from the spine (x=0) out to x=side*W: the page surface rises then flattens (a held paperback)."""
    bm = bmesh.new()
    rows = []
    for i in range(steps + 1):
        u = i / steps
        x = side * W * u
        z = lift + 0.035 * math.sin(u * math.pi * .9) * (1 - .35 * u)
        rows.append((x, z))
    top, bot = [], []
    for x, z in rows:
        for y in (-H / 2, H / 2):
            top.append(bm.verts.new((x, y, z)))
            bot.append(bm.verts.new((x, y, z - thickness)))
    for i in range(steps):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2
        f = [(top[a], top[d], top[c], top[b]), (bot[a], bot[b], bot[c], bot[d])]
        for q in f:
            bm.faces.new(q if side > 0 else q[::-1])
        for e0, e1 in ((a, d), (b, c)):   # long edges
            q = (top[e0], bot[e0], bot[e1], top[e1])
            bm.faces.new(q if (side > 0) == (e0 == a) else q[::-1])
    for e in ((0, 1), (2 * steps, 2 * steps + 1)):   # ends
        q = (top[e[0]], top[e[1]], bot[e[1]], bot[e[0]])
        bm.faces.new(q if (side > 0) == (e[0] == 0) else q[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uv = bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        for lp in f.loops:
            co = lp.vert.co
            lp[uv].uv = (abs(co.x) / W, co.y / H + .5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(material)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


bpy.ops.wm.read_factory_settings(use_empty=True)
paper = mat('mare_book_paper', (.93, .9, .82), .9)
# printed lines: a small packed image (rows of grey "text" with a margin), mapped across each page
img = bpy.data.images.new('mare_book_text', 256, 256)
px = []
for yy in range(256):
    for xx in range(256):
        line = 22 < yy < 236 and (yy % 9) in (0, 1, 2) and 26 < xx < 230 - (37 if (yy // 9) % 5 == 4 else 0)
        v = (.42, .40, .37) if line else (.93, .9, .82)
        px += [v[0], v[1], v[2], 1.0]
img.pixels = px
img.pack()
img.filepath = ''
tex = paper.node_tree.nodes.new('ShaderNodeTexImage')
tex.image = img
paper.node_tree.links.new(tex.outputs['Color'], paper.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
cover = mat('mare_book_cover', (.12, .38, .55), .6)
parts = [page_block('pages_l', -1, PAGES, COVER + PAGES + .0005, paper), page_block('pages_r', 1, PAGES, COVER + PAGES + .0005, paper),
         page_block('cover_l', -1, COVER, 0, cover), page_block('cover_r', 1, COVER, 0, cover)]
bpy.ops.object.select_all(action='DESELECT')
for p in parts:
    p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
book = bpy.context.view_layer.objects.active
book.name = 'mare_open_book'
# text lines on the pages: thin darker strips as a second material would need UVs; the paper tone is enough at arm's length
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format='GLB', use_selection=False, export_yup=True)
print('ok', OUT, len(book.data.polygons))
