"""Kiosk dishes from free Fab models (docs/ue58/ROUPAS_FAB.md lists the sources; CREDITS.md): downloaded to
D:/CodexTemp/fab/props, prepared here for the game and written as GLB to D:/CodexTemp/fab/props/game:

  coco_gelado      green coconut (LucasMaia "Realistic Coconut"), decimated from 940k triangles, 20 cm tall
  sorvete_morango  ice cream in a marble bowl (HQ3DMOD), scoops recoloured strawberry
  sorvete_chocolate  same bowl, chocolate scoops
  acai             wooden bowl (Kollapse3D "Realistic Wooden Bowl and Spoon") filled with acai cream

Every material and image gets a unique fab_<dish>_ prefix (Interchange reuses assets by name) and textures are
resized to a power of two (max 1024). Run with the bpy venv:
  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/prep_fab_food.py
"""
import os
import zipfile
import bpy
import bmesh
import numpy as np
from mathutils import Vector

SRC = 'D:/CodexTemp/fab/props'
OUT = 'D:/CodexTemp/fab/props/game'


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def meshes():
    return [o for o in bpy.data.objects if o.type == 'MESH']


def bounds():
    pts = [o.matrix_world @ Vector(c) for o in meshes() for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def join_all(name):
    # One UV map name everywhere before joining: material UV nodes that point at a map lost in the join make the
    # glTF exporter drop the texture (the rattan of the sofa came out white).
    for o in meshes():
        if o.data.uv_layers:
            o.data.uv_layers.active.name = 'UVMap'
    for m in bpy.data.materials:
        if m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == 'UVMAP':
                    n.uv_map = 'UVMap'
    bpy.ops.object.select_all(action='DESELECT')
    ms = meshes()
    for o in ms:
        o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return o


def decimate(o, tris):
    now = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if now <= tris:
        return
    m = o.modifiers.new('dec', 'DECIMATE')
    m.ratio = tris / now
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier='dec')


def fit(o, height):
    """Base on z = 0, centred in x/y, scaled to the real height."""
    lo, hi = bounds()
    s = height / (hi.z - lo.z)
    o.scale = (s, s, s)
    bpy.ops.object.transform_apply(scale=True)
    lo, hi = bounds()
    o.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    bpy.ops.object.transform_apply(location=True)


def bake_pixels(img, tag):
    """Write an image's current pixel buffer to its own PNG and reload it from there: pack() packs the original
    file, not edited or rescaled pixels."""
    path = f'{OUT}/tex/{tag}.png'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    img.reload()


def unique(prefix, max_size=1024):
    for m in bpy.data.materials:
        m.name = f'{prefix}_{m.name}'[:60]
    for img in bpy.data.images:
        if img.size[0] == 0 and img.source in ('FILE', 'GENERATED') and (img.packed_file or img.filepath):
            img.reload()   # images used only through texture transforms are still unloaded: the exporter drops those
            _ = img.pixels[0] if len(img.pixels) else None
        if img.size[0] == 0:
            continue
        w, h = img.size
        p2 = lambda v: 1 << (min(v, max_size).bit_length() - 1)
        if not img.has_data:
            img.reload()
        if (w, h) != (p2(w), p2(h)) or img.is_dirty:
            img.scale(p2(w), p2(h))
            bake_pixels(img, f'{prefix}_{len(img.name)}_{abs(hash(img.name)) % 99999}')
        img.name = f'{prefix}_{img.name}'[:60]
        if not img.packed_file:   # images embedded in a GLB are already packed; packing again empties them
            img.pack()
            img.filepath = ''


def recolour(image_name_part, rgb, keep=0.06):
    """Recolour a base colour texture: keep its shading (luminance) and replace the hue with rgb."""
    for img in bpy.data.images:
        if image_name_part not in img.name.lower():
            continue
        if not img.has_data:
            img.reload()
        if img.size[0]:
            print('RECOLOUR', img.name, rgb)
            px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)
            lum = (px[:, :3] @ np.array([.299, .587, .114], dtype=np.float32))[:, None]
            tint = np.array(rgb, dtype=np.float32)[None, :] * (lum / max(float(lum.mean()), 1e-3))
            px[:, :3] = np.clip(px[:, :3] * keep + tint * (1 - keep), 0, 1)
            img.pixels[:] = px.ravel()
            img.update()


def export(name):
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/fab_{name}.glb', export_format='GLB', export_apply=True)
    o = meshes()[0]
    print('WROTE', name, sum(len(p.vertices) - 2 for p in o.data.polygons), 'tris', tuple(round(v, 3) for v in bounds()[1] - bounds()[0]))


def coco():
    reset()
    bpy.ops.import_scene.gltf(filepath=f'{SRC}/coconut_realistic.glb')
    o = join_all('fab_coco_gelado')
    decimate(o, 30000)
    fit(o, .2)
    unique('fab_coco')
    export('coco_gelado')


def sorvete(flavour, rgb):
    reset()
    d = f'{SRC}/icecream_marble_x'
    if not os.path.isdir(d):
        zipfile.ZipFile(f'{SRC}/icecream_marble.zip').extractall(d)
    fbx = next(os.path.join(r, n) for r, _, ns in os.walk(d) for n in ns if n.lower().endswith('.fbx'))
    bpy.ops.import_scene.fbx(filepath=fbx)
    o = join_all(f'fab_sorvete_{flavour}')
    decimate(o, 40000)
    fit(o, .14)
    recolour('ice_cream_mat_basecolor', rgb)
    unique(f'fab_sorvete_{flavour}')
    export(f'sorvete_{flavour}')


def campfire():
    """Junina bonfire base: the Quixel Megascans "Campfire" scan (logs, ashes, stones), 2048 px textures."""
    reset()
    bpy.ops.import_scene.gltf(filepath=f'{SRC}/../megascans/campfire_uenpfeifa_high.glb')
    o = join_all('festa_campfire_scan')
    decimate(o, 60000)
    lo, hi = bounds()
    o.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    bpy.ops.object.transform_apply(location=True)
    unique('festa_campfire_scan', 2048)
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/festa_campfire_scan.glb', export_format='GLB', export_apply=True)
    print('WROTE campfire', sum(len(p.vertices) - 2 for p in o.data.polygons), 'tris', tuple(round(v, 3) for v in bounds()[1] - bounds()[0]))


def furniture(src, name, height, tris):
    """A Fab furniture model (D:/CodexTemp/fab/furniture) for the customization tiers: real height, base on the
    floor, decimated, unique names, 2048 px textures; written to OUT/<name>.glb."""
    reset()
    bpy.ops.import_scene.gltf(filepath=f'D:/CodexTemp/fab/furniture/{src}')
    o = join_all(name)
    decimate(o, tris)
    fit(o, height)
    unique(name, 2048)
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/{name}.glb', export_format='GLB', export_apply=True)
    print('WROTE', name, sum(len(p.vertices) - 2 for p in o.data.polygons), 'tris', tuple(round(v, 3) for v in bounds()[1] - bounds()[0]))


def stall():
    """Party stall (quermesse/junina): the Fab "Japanese Market Stall" (striped awning, bamboo walls) without its
    concrete ground slab, decimated; replaces the generated festa_stall."""
    reset()
    bpy.ops.import_scene.gltf(filepath='D:/CodexTemp/fab/festa/japanese_market_stall.glb')
    for o in list(meshes()):
        lo = [o.matrix_world @ Vector(c) for c in o.bound_box]
        dz = max(p.z for p in lo) - min(p.z for p in lo)
        dx = max(p.x for p in lo) - min(p.x for p in lo)
        if dz < .03 and dx > 3:          # the flat slab under the stall
            bpy.data.objects.remove(o, do_unlink=True)
    o = join_all('festa_stall_fab')
    decimate(o, 80000)
    lo, hi = bounds()
    o.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    bpy.ops.object.transform_apply(location=True)
    unique('festa_stall_fab', 1024)
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/festa_stall_fab.glb', export_format='GLB', export_apply=True)
    print('WROTE stall', sum(len(p.vertices) - 2 for p in o.data.polygons), 'tris', tuple(round(v, 3) for v in bounds()[1] - bounds()[0]))


def acai():
    reset()
    bpy.ops.import_scene.gltf(filepath=f'{SRC}/wooden_bowl.glb')
    o = join_all('fab_acai')
    fit(o, .16)
    lo, hi = bounds()
    # Acai cream: a shallow dome filling the bowl a little below the rim, with a soft lumpy surface.
    rim = min(hi.x - lo.x, hi.y - lo.y) * .5 * .78
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=24, radius=1.0)
    for v in bm.verts:
        v.co.x *= rim
        v.co.y *= rim
        v.co.z = hi.z * .72 + v.co.z * .02 + .002 * np.sin(v.co.x * 90) * np.cos(v.co.y * 70)
    me = bpy.data.meshes.new('fab_acai_cream')
    bm.to_mesh(me)
    cream = bpy.data.objects.new('fab_acai_cream', me)
    bpy.context.scene.collection.objects.link(cream)
    for p in me.polygons:
        p.use_smooth = True
    mat = bpy.data.materials.new('acai_cream')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (.045, .006, .03, 1)   # deep acai purple
    bsdf.inputs['Roughness'].default_value = .55
    me.materials.append(mat)
    join_all('fab_acai')
    unique('fab_acai')
    export('acai')


if __name__ == '__main__':
    import sys
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if only:
        for job in only:
            {'coco': coco, 'acai': acai, 'campfire': campfire, 'stall': stall,
             'stool': lambda: furniture('rattan_bar_stool.glb', 'fab_rattan_bar_stool', .874, 45000),
             'sofa': lambda: furniture('woven_rattan_sofa.glb', 'fab_rattan_sofa', .80, 60000), 'morango': lambda: sorvete('morango', (.95, .45, .55)), 'chocolate': lambda: sorvete('chocolate', (.42, .24, .14))}[job]()
        raise SystemExit
    coco()
    sorvete('morango', (.95, .45, .55))
    sorvete('chocolate', (.42, .24, .14))
    acai()
