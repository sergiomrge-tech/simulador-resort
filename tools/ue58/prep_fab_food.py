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
import math
import os
import zipfile
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

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


BIKE_COLORS = {'red': (.78, .16, .14), 'blue': (.12, .38, .72), 'yellow': (.93, .72, .12), 'green': (.16, .52, .3),
               'white': (.88, .88, .86)}


def bike(colour):
    """Village bicycle (replaces the generated bike_<colour>, whose wheels read as low poly): Fab "Vintage Bicycle 3D
    Model" (Patrick Goud, "Swapfiets", CC-BY 4.0). Turned to the old bike's frame (length on Y, front -Y, base z=0,
    1.70 m long) so the existing placements fit; frame repainted to the colour (hue 0-45/330-360 of the atlas keeps its
    shading) and the brand's blue front tyre made black rubber like the rear one. Atlas 4096 -> 2048."""
    reset()
    bpy.ops.import_scene.gltf(filepath='D:/CodexTemp/fab/bike/x/source/s/scene.gltf')
    # Sketchfab glTFs nest the meshes under scaled/rotated empties: bake those into the meshes before joining,
    # otherwise the later rotate/scale/centre only touch the child and the export scatters the parts.
    for m in meshes():
        w = m.matrix_world.copy()
        m.parent = None
        m.matrix_world = w
    for e in [x for x in bpy.data.objects if x.type != 'MESH']:
        bpy.data.objects.remove(e, do_unlink=True)
    o = join_all(f'fab_bike_{colour}')
    # Turn, scale and centre the mesh data itself (object-level transform_apply did not take here); the object
    # stays at the origin so world = mesh data.
    o.data.transform(o.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    o.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'Z'))       # front +X -> -Y
    o.data.update()
    decimate(o, 60000)

    def vbounds():   # from the vertices: bound_box stays stale after mesh.transform
        co = np.array([v.co for v in o.data.vertices])
        return Vector(co.min(0)), Vector(co.max(0))
    lo, hi = vbounds()
    o.data.transform(Matrix.Scale(1.70 / (hi.y - lo.y), 4))
    lo, hi = vbounds()
    o.data.transform(Matrix.Translation(-Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))))
    o.data.update()
    bpy.context.view_layer.update()
    for m in bpy.data.materials:                   # the emissive map only lit grey patches (reflectors) in Lumen
        bsdf = m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
        if bsdf:
            for link in list(bsdf.inputs['Emission Color'].links):
                m.node_tree.links.remove(link)
            bsdf.inputs['Emission Strength'].default_value = 0
    target = np.array(BIKE_COLORS[colour], dtype=np.float32)
    for img in [i for i in bpy.data.images if 'basecolor' in i.name.lower()]:
        if not img.has_data:
            img.reload()
        img.scale(2048, 2048)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)
        rgb = px[:, :3]
        mx, mn = rgb.max(1), rgb.min(1)
        d = np.maximum(mx - mn, 1e-6)
        r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
        hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
        sat = (mx - mn) / np.maximum(mx, 1e-3)
        lum = rgb @ np.array([.299, .587, .114], dtype=np.float32)
        frame = (sat > .3) & (mx > .08) & ((hue < 45) | (hue > 330))
        tyre = (sat > .3) & (hue > 180) & (hue < 260)
        ref = float(lum[frame].mean()) if frame.any() else .3
        rgb[frame] = np.clip(target[None, :] * (lum[frame] / ref)[:, None], 0, 1)
        rgb[tyre] = (lum[tyre] * .35)[:, None] * np.array([1, 1, 1.05], dtype=np.float32)[None, :]
        px[:, :3] = rgb
        # A new image with the edited pixels, saved as PNG, replaces the original in every material: editing the
        # original in place was lost when the helpers reloaded it from its file.
        new = bpy.data.images.new(f'fab_bike_{colour}_base', 2048, 2048, alpha=True)
        new.pixels[:] = px.ravel()
        path = f'{OUT}/tex/fab_bike_{colour}_base.png'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        new.filepath_raw = path
        new.file_format = 'PNG'
        new.save()
        for m in bpy.data.materials:
            if m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and n.image == img:
                        n.image = new
        print('BIKE', colour, 'frame px', int(frame.sum()), 'tyre px', int(tyre.sum()))
    for img in [i for i in bpy.data.images if i.users == 0]:
        bpy.data.images.remove(img)
    for img in [i for i in bpy.data.images if i.size[0] > 2048]:   # the other maps at 2048 too, same new-image way
        if not img.has_data:
            img.reload()
        img.scale(2048, 2048)
        small = bpy.data.images.new(f'fab_bike_{colour}_{img.name.split(".")[0][-12:]}', 2048, 2048, alpha=True)
        small.colorspace_settings.name = img.colorspace_settings.name
        small.pixels[:] = img.pixels[:]
        small.filepath_raw = f'{OUT}/tex/{small.name}.png'
        small.file_format = 'PNG'
        small.save()
        for m in bpy.data.materials:
            if m.use_nodes:
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and n.image == img:
                        n.image = small
    unique(f'fab_bike_{colour}', 2048)
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/fab_bike_{colour}.glb', export_format='GLB', export_apply=True)
    print('WROTE bike', colour, sum(len(p.vertices) - 2 for p in o.data.polygons), 'tris', tuple(round(v, 3) for v in bounds()[1] - bounds()[0]))


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
             **{f'bike_{c}': (lambda c=c: bike(c)) for c in BIKE_COLORS},
             'sofa': lambda: furniture('woven_rattan_sofa.glb', 'fab_rattan_sofa', .80, 60000), 'morango': lambda: sorvete('morango', (.95, .45, .55)), 'chocolate': lambda: sorvete('chocolate', (.42, .24, .14))}[job]()
        raise SystemExit
    coco()
    sorvete('morango', (.95, .45, .55))
    sorvete('chocolate', (.42, .24, .14))
    acai()
