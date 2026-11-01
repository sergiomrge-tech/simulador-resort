"""Detailed furniture that Poly Haven does not offer, modelled with bpy for the customization tiers.

Loungers (pool and hotel), the beach daybed and two beds for the home. Real-world metres, base at z=0,
length along Blender Y (head / backrest at +Y), centred on the origin. Textures are CC0 Poly Haven
photo scans from D:/Assets/PolyHaven (tinted copies are baked next to each model).
Output: D:/Assets/Mare/<slug>/<slug>.glb + info.json, read by Content/Python/mare_custom.py.
Run: blender -b --factory-startup --python tools/ue58/gen_custom_furniture.py -- [slug ...]
"""
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np

LIB = Path('D:/Assets/PolyHaven')
OUT = Path('D:/Assets/Mare')


# ---------------------------------------------------------------- materials
def texture(slug, kind='diff', tint=None, out=None):
    src = LIB / slug / f'{slug}_{kind}_1k.jpg'
    img = bpy.data.images.load(str(src))
    if tint is None:
        return img
    # Bake the tint into a copy: glTF keeps a plain image texture, not a Multiply node.
    px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)
    lum = px[:, :3] @ np.array([.2126, .7152, .0722], dtype=np.float32)
    detail = np.clip(lum / max(float(lum.mean()), 1e-3), .55, 1.45)[:, None]
    px[:, :3] = np.clip(np.array(tint, dtype=np.float32)[None, :] * detail, 0, 1)
    tinted = bpy.data.images.new(f'{slug}_{"_".join(str(int(c * 255)) for c in tint)}', img.size[0], img.size[1])
    tinted.pixels[:] = px.ravel()
    path = out / f'{tinted.name}.png'
    tinted.filepath_raw = str(path)
    tinted.file_format = 'PNG'
    tinted.save()
    return tinted


def material(name, slug, tint=None, rough=.6, out=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = texture(slug, 'diff', tint, out)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    nor = nt.nodes.new('ShaderNodeTexImage')
    nor.image = texture(slug, 'nor')
    nor.image.colorspace_settings.name = 'Non-Color'
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(nor.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = rough
    return m


# ---------------------------------------------------------------- geometry helpers
def box_uv(bm, size):
    """Box mapping by dominant normal, size = metres per texture tile."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for loop in f.loops:
            co = loop.vert.co
            u, v = [(co.y, co.z), (co.x, co.z), (co.x, co.y)][ax]
            loop[uv].uv = (u / size, v / size)


def finish(obj, mat, uv=1.0, bevel=0.0, seg=3, subsurf=0, smooth=True):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    box_uv(bm, uv)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.materials.append(mat)
    if bevel:
        b = obj.modifiers.new('Bevel', 'BEVEL')
        b.width = bevel
        b.segments = seg
        b.limit_method = 'ANGLE'
    if subsurf:
        s = obj.modifiers.new('Subsurf', 'SUBSURF')
        s.levels = s.render_levels = subsurf
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def mesh_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    return obj


def box(name, size, loc, mat, rot=(0, 0, 0), bevel=.006, uv=1.0, subsurf=0, cuts=0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    if cuts:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    from mathutils import Euler, Vector
    m = Euler(rot).to_matrix()
    for v in bm.verts:
        v.co = m @ v.co + Vector(loc)
    obj = mesh_obj(name, bm)
    return finish(obj, mat, uv, bevel, 3, subsurf, smooth=bool(subsurf))


def cushion(name, size, loc, mat, rot=(0, 0, 0), puff=.012, uv=.5):
    """Soft cushion: subdivided box with rounded edges and a slight bulge on the faces."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    for v in bm.verts:
        x, y, z = v.co.x * 2, v.co.y * 2, v.co.z * 2
        bulge = puff * (1 - x * x) * (1 - y * y)
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z = v.co.z * size[2] + (bulge if z > 0 else -bulge * .4)
    from mathutils import Euler, Vector
    m = Euler(rot).to_matrix()
    for v in bm.verts:
        v.co = m @ v.co + Vector(loc)
    obj = mesh_obj(name, bm)
    finish(obj, mat, uv, bevel=min(size) * .3, seg=3, subsurf=1)
    return obj


def tube(name, a, b, r, mat, sides=12, uv=.5):
    from mathutils import Vector
    a, b = Vector(a), Vector(b)
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=sides, radius1=r, radius2=r, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix()
    for v in bm.verts:
        v.co = rot @ v.co + (a + b) / 2
    obj = mesh_obj(name, bm)
    return finish(obj, mat, uv, bevel=r * .3, seg=2)


def lathe(name, profile, loc, mat, sides=24, uv=.3):
    """Turned piece from (radius, z) pairs, e.g. bed posts and finials."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        ring = [bm.verts.new((loc[0] + r * math.cos(2 * math.pi * i / sides), loc[1] + r * math.sin(2 * math.pi * i / sides), loc[2] + z)) for i in range(sides)]
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(sides):
            bm.faces.new((r0[i], r0[(i + 1) % sides], r1[(i + 1) % sides], r1[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    obj = mesh_obj(name, bm)
    return finish(obj, mat, uv)


def drape(name, width, height, loc, yaw, mat, folds=7, amp=.035):
    """Hanging curtain: grid with sine folds, gathered at the top, solidified 8 mm."""
    bm = bmesh.new()
    nx, nz = 48, 24
    verts = []
    for j in range(nz + 1):
        z = height * j / nz
        gather = .55 + .45 * (1 - j / nz)  # wider at the bottom
        row = []
        for i in range(nx + 1):
            u = i / nx - .5
            x = u * width * gather
            y = amp * math.sin(u * folds * 2 * math.pi) * (.6 + .4 * (1 - j / nz))
            row.append(bm.verts.new((x, y, -z)))
        verts.append(row)
    for j in range(nz):
        for i in range(nx):
            bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
    c, s = math.cos(yaw), math.sin(yaw)
    for v in bm.verts:
        x, y, z = v.co
        v.co = (loc[0] + x * c - y * s, loc[1] + x * s + y * c, loc[2] + z)
    obj = mesh_obj(name, bm)
    finish(obj, mat, .6)
    sol = obj.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = .008
    return obj


def weave(name, x0, x1, y0, y1, z, mat, tilt=0.0, pivot_y=0.0, step=.028, r=.006):
    """Real woven rattan: strips along X and Y passing over and under each other."""
    objs = []
    from mathutils import Vector

    def place(p):
        # Optional backrest tilt around the X axis at pivot_y.
        y, zz = p.y - pivot_y, p.z - z
        c, s = math.cos(tilt), math.sin(tilt)
        return Vector((p.x, pivot_y + y * c - zz * s, z + y * s + zz * c))
    nx = int((x1 - x0) / step)
    ny = int((y1 - y0) / step)
    bm = bmesh.new()
    for k, (count, along_x) in enumerate([(ny, True), (nx, False)]):
        for i in range(count + 1):
            pts = []
            n = (nx if along_x else ny) * 2
            for t in range(n + 1):
                f = t / n
                if along_x:
                    p = Vector((x0 + (x1 - x0) * f, y0 + (y1 - y0) * i / count, z))
                else:
                    p = Vector((x0 + (x1 - x0) * i / count, y0 + (y1 - y0) * f, z))
                p.z += (1 if (t // 2 + i + k) % 2 else -1) * r * .9 * abs(math.sin(math.pi * t / 2 + .5))
                pts.append(place(p))
            ring_prev = None
            for p0, p1 in zip(pts, pts[1:] + [pts[-1] + (pts[-1] - pts[-2])]):
                d = (p1 - p0).normalized()
                side = d.cross(Vector((0, 0, 1)))
                if side.length < 1e-4:
                    side = Vector((1, 0, 0))
                side.normalize()
                up = side.cross(d)
                ring = [bm.verts.new(p0 + side * (r * 1.6 * math.cos(a)) + up * (r * .55 * math.sin(a))) for a in [2 * math.pi * q / 6 for q in range(6)]]
                if ring_prev:
                    for q in range(6):
                        bm.faces.new((ring_prev[q], ring_prev[(q + 1) % 6], ring[(q + 1) % 6], ring[q]))
                ring_prev = ring
    obj = mesh_obj(name, bm)
    return finish(obj, mat, .25)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def export(slug, desc):
    folder = OUT / slug
    folder.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(folder / f'{slug}.glb'), export_format='GLB', export_apply=True)
    (folder / 'info.json').write_text(json.dumps({'slug': slug, 'name': desc, 'gltf': f'{slug}.glb',
        'authors': {'Maré Alta (bpy)': 'model'}, 'license': 'Original model; textures CC0 1.0 Poly Haven',
        'source': 'tools/ue58/gen_custom_furniture.py'}, indent=1), encoding='utf-8')


# ---------------------------------------------------------------- furniture
def lounger_frame(wood, back_angle=math.radians(42)):
    """Teak lounger: side rails, legs, wheels at the head, slatted seat and tilted backrest."""
    L, W, H = 1.95, .66, .32
    for sx in (-1, 1):
        box(f'rail{sx}', (.045, L, .09), (sx * (W / 2 - .022), 0, H), wood, uv=.8)
        for y in (-L / 2 + .08, L / 2 - .12):
            box(f'leg{sx}{y}', (.05, .05, H - .02), (sx * (W / 2 - .03), y, (H - .02) / 2), wood, uv=.8)
        # Wheels at the head end (+Y) to drag the lounger.
        wheel = bpy.data.objects.get('wheel')
        lathe(f'wheel{sx}', [(0, -.025), (.07, -.025), (.075, -.015), (.075, .015), (.07, .025), (0, .025)], (0, 0, 0), wood, 20)
        w = bpy.context.collection.objects[f'wheel{sx}']
        w.rotation_euler = (0, math.radians(90), 0)
        w.location = (sx * (W / 2 + .03), L / 2 - .12, .075)
    box('foot', (W, .05, .09), (0, -L / 2 + .025, H), wood, uv=.8)
    return L, W, H, back_angle


def lounger_slats(seat_end=.35, slats=True):
    reset()
    out = OUT / 'mare_lounger_slats'
    out.mkdir(parents=True, exist_ok=True)
    wood = material('Teak', 'teak_veneer', rough=.45)
    L, W, H, a = lounger_frame(wood)
    if slats:
        y = -L / 2 + .07
        while y < seat_end:
            box(f'slat{y:.2f}', (W - .07, .07, .022), (0, y + .035, H + .05), wood, uv=.7)
            y += .085
        back = L / 2 - seat_end
        for i in range(8):
            t = (i + .5) / 8 * back
            box(f'bslat{i}', (W - .07, .07, .022), (0, seat_end + t * math.cos(a), H + .05 + t * math.sin(a)), wood, rot=(a, 0, 0), uv=.7)
        for sx in (-1, 1):
            box(f'bside{sx}', (.04, back + .04, .05), (sx * (W / 2 - .05), seat_end + back / 2 * math.cos(a), H + .03 + back / 2 * math.sin(a)), wood, rot=(a, 0, 0), uv=.8)
        # Prop under the backrest.
        box('prop', (W - .14, .035, .3), (0, seat_end + .25, H + .15), wood, rot=(-.5, 0, 0), uv=.8)
    return L, W, H, a, wood


def lounger_cushion(slug='mare_lounger_cushion', fabric=('fabric_pattern_07', None), frame='slats'):
    if frame == 'slats':
        L, W, H, a, wood = lounger_slats()
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    cloth = material('Cushion', fabric[0], fabric[1], rough=.85, out=out)
    seat_end = .35
    seat = seat_end + L / 2 - .05
    cushion('seat', (W - .06, seat, .075), (0, -L / 2 + .04 + seat / 2, H + .1), cloth)
    back = L / 2 - seat_end - .02
    cushion('back', (W - .06, back, .075), (0, seat_end + back / 2 * math.cos(a) - .02, H + .1 + back / 2 * math.sin(a) + .02), cloth, rot=(a, 0, 0))
    cushion('pillow', (.42, .14, .26), (0, L / 2 - .3, H + .55), cloth, rot=(a, 0, 0), puff=.03)
    export(slug, 'Espreguiçadeira com colchonete')


def lounger_wicker():
    reset()
    slug = 'mare_lounger_wicker'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    rattan = material('Rattan', 'brown_leather', (.62, .45, .27), rough=.7, out=out)
    cotton = material('Cotton', 'waffle_pique_cotton', (.93, .91, .86), rough=.9, out=out)
    L, W, H, a = 1.98, .70, .30, math.radians(40)
    seat_end = .32
    # Curved rattan frame: rounded side rails following seat and backrest, sled feet.
    for sx in (-1, 1):
        x = sx * (W / 2)
        pts = [(x, -L / 2, H - .1), (x, -L / 2 + .05, H + .05), (x, seat_end, H + .05)]
        back = L / 2 - seat_end
        pts += [(x, seat_end + back * math.cos(a) * f, H + .05 + back * math.sin(a) * f) for f in (.5, 1.0)]
        for p0, p1 in zip(pts, pts[1:]):
            tube(f'frame{sx}{p0[1]:.2f}', p0, p1, .028, rattan)
        tube(f'sled{sx}', (x, -L / 2 + .05, .02), (x, L / 2 - .25, .02), .025, rattan)
        for y in (-L / 2 + .1, 0, seat_end):
            tube(f'post{sx}{y}', (x, y, .02), (x, y, H + .05), .022, rattan)
    weave('seatweave', -W / 2 + .02, W / 2 - .02, -L / 2 + .05, seat_end, H + .05, rattan)
    weave('backweave', -W / 2 + .02, W / 2 - .02, seat_end, L / 2 - .02, H + .05, rattan, tilt=a, pivot_y=seat_end)
    cushion('seat', (W - .1, seat_end + L / 2 - .1, .09), (0, (seat_end - L / 2) / 2 + .02, H + .11), cotton)
    back = L / 2 - seat_end - .06
    cushion('back', (W - .1, back, .08), (0, seat_end + back / 2 * math.cos(a), H + .11 + back / 2 * math.sin(a)), cotton, rot=(a, 0, 0))
    cushion('pillow', (.46, .16, .28), (0, L / 2 - .32, H + .6), cotton, rot=(a, 0, 0), puff=.03)
    export(slug, 'Espreguiçadeira de vime')


def bed_core(out, L, W, mattress_top, duvet, linen, frame_mat):
    """Mattress, duvet with a folded edge and pillows; head of the bed at +Y."""
    cushion('mattress', (W - .04, L - .04, .24), (0, 0, mattress_top - .12), linen, puff=.008)
    cushion('duvet', (W + .02, L * .72, .05), (0, -L * .13, mattress_top + .02), duvet, puff=.02)
    cushion('fold', (W + .02, .22, .06), (0, -L * .13 + L * .36 - .05, mattress_top + .06), linen, puff=.02)
    for i, x in enumerate([-W / 4, W / 4]):
        cushion(f'pillow{i}', (W / 2 - .08, .4, .16), (x, L / 2 - .3, mattress_top + .09), linen, rot=(math.radians(-12), 0, 0), puff=.05)
    cushion('throw', (W + .06, .5, .02), (0, -L / 2 + .35, mattress_top + .055), duvet, puff=.005)


def daybed():
    reset()
    slug = 'mare_daybed'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    wood = material('Teak', 'teak_veneer', rough=.45)
    linen = material('Linen', 'rough_linen', (.95, .93, .88), rough=.9, out=out)
    cotton = material('Cotton', 'waffle_pique_cotton', (.92, .9, .84), rough=.9, out=out)
    stripe = material('Stripe', 'fabric_pattern_07', None, rough=.85, out=out)
    L, W, top = 2.0, 1.45, .42
    box('base', (W, L, .2), (0, 0, .18), wood, uv=.8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = (sx * (W / 2 - .04), sy * (L / 2 - .04))
            box(f'post{sx}{sy}', (.07, .07, 2.15), (p[0], p[1], 1.075), wood, uv=.8)
            if sy > 0:  # tied back at the head posts so the bed stays open to the sea
                drape(f'curtain{sx}{sy}', .4, 1.85, (p[0] - sx * .14, p[1] - .03, 2.08), 0, linen, folds=6)
    for sy in (-1, 1):
        box(f'top_y{sy}', (W, .07, .08), (0, sy * (L / 2 - .04), 2.12), wood, uv=.8)
    for sx in (-1, 1):
        box(f'top_x{sx}', (.07, L, .08), (sx * (W / 2 - .04), 0, 2.12), wood, uv=.8)
    # Linen canopy roof with a soft sag between slats.
    for i in range(5):
        box(f'roofslat{i}', (W - .1, .05, .03), (0, -L / 2 + .2 + i * (L - .4) / 4, 2.17), wood, uv=.8)
    cushion('roof', (W - .1, L - .1, .03), (0, 0, 2.2), linen, puff=-.04)
    cushion('mattress', (W - .06, L - .06, .18), (0, 0, top), cotton, puff=.01)
    for i, x in enumerate([-.45, 0, .45]):
        cushion(f'back{i}', (.42, .16, .4), (x, L / 2 - .2, top + .3), stripe if i == 1 else cotton, rot=(math.radians(-15), 0, 0), puff=.05)
    cushion('roll', (.9, .2, .18), (0, -L / 2 + .3, top + .16), stripe, puff=.04)
    export(slug, 'Daybed com dossel')


def bed_upholstered():
    reset()
    slug = 'mare_bed_upholstered'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    velvet = material('Velvet', 'velour_velvet', (.42, .52, .55), rough=.8, out=out)
    wood = material('Teak', 'teak_veneer', rough=.45)
    linen = material('Linen', 'rough_linen', (.96, .95, .92), rough=.9, out=out)
    duvet = material('Duvet', 'waffle_pique_cotton', (.86, .80, .70), rough=.9, out=out)
    L, W = 2.1, 1.65
    cushion('frame', (W + .1, L, .28), (0, 0, .24), velvet, puff=.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(f'leg{sx}{sy}', [(.03, 0), (.025, .08), (.035, .1), (.035, .11), (0, .11)], (sx * (W / 2 - .02), sy * (L / 2 - .08), 0), wood, 16)
    # Tall tufted headboard: padded panel with button dimples.
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=40, y_segments=24, size=.5)
    hb_w, hb_h = W + .2, 1.15
    for v in bm.verts:
        u, w = v.co.x * 2, v.co.y * 2  # -1..1
        x, z = u * hb_w / 2, (w + 1) / 2 * hb_h
        dimple = 0.0
        for bx in range(-3, 4):
            for bz in range(1, 4):
                cx, cz = bx * hb_w / 7 + (hb_w / 14 if bz % 2 else 0), bz * hb_h / 4
                d2 = (x - cx) ** 2 + (z - cz) ** 2
                dimple = max(dimple, math.exp(-d2 / .0025))
        edge = min(1, (1 - abs(u)) * 8) * min(1, (1 - abs(w)) * 8)
        v.co = (x, .06 * edge - .035 * dimple, z)
    obj = mesh_obj('headboard', bm)
    finish(obj, velvet, .35)
    sol = obj.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = .09
    obj.location = (0, L / 2 + .02, .2)
    obj.rotation_euler = (0, 0, math.pi)
    box('headframe', (hb_w + .05, .1, .05), (0, L / 2 + .05, 1.36), velvet, bevel=.02, uv=.4)
    bed_core(out, L, W, .62, duvet, linen, wood)
    export(slug, 'Cama estofada')


def bed_canopy():
    reset()
    slug = 'mare_bed_canopy'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    wood = material('Teak', 'teak_veneer', rough=.4)
    linen = material('Linen', 'rough_linen', (.97, .96, .93), rough=.9, out=out)
    duvet = material('Duvet', 'quatrefoil_jacquard_fabric', (.82, .78, .66), rough=.85, out=out)
    L, W = 2.15, 1.75
    box('base', (W, L, .3), (0, 0, .3), wood, uv=.8)
    post = [(.055, 0), (.06, .04), (.045, .08), (.045, .45), (.065, .5), (.065, .56), (.04, .62), (.04, 2.1), (.055, 2.14), (.055, 2.2), (.03, 2.26), (.045, 2.3), (0, 2.34)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(f'post{sx}{sy}', post, (sx * (W / 2), sy * (L / 2), 0), wood, 20)
    for sy in (-1, 1):
        box(f'rail_y{sy}', (W, .06, .09), (0, sy * L / 2, 2.15), wood, uv=.8)
    for sx in (-1, 1):
        box(f'rail_x{sx}', (.06, L, .09), (sx * W / 2, 0, 2.15), wood, uv=.8)
    # Carved headboard with vertical spindles.
    box('head_top', (W, .08, .1), (0, L / 2, 1.2), wood, uv=.8)
    box('head_mid', (W, .06, .06), (0, L / 2, .55), wood, uv=.8)
    for i in range(11):
        x = -W / 2 + .12 + i * (W - .24) / 10
        lathe(f'spindle{i}', [(.018, 0), (.026, .1), (.016, .2), (.026, .32), (.018, .45), (.018, .62)], (x, L / 2, .58), wood, 12)
    box('foot_board', (W, .06, .35), (0, -L / 2, .5), wood, uv=.8)
    # Linen drapes tied back at each post, and a valance on the canopy.
    for sx in (-1, 1):
        for sy in (-1, 1):
            drape(f'drape{sx}{sy}', .7, 1.95, (sx * (W / 2 - .2), sy * (L / 2 + .02), 2.12), 0, linen, folds=8)
    for sy in (-1, 1):
        drape(f'valance_y{sy}', W, .22, (0, sy * (L / 2 + .04), 2.22), 0, linen, folds=14, amp=.02)
    for sx in (-1, 1):
        drape(f'valance_x{sx}', L, .22, (sx * (W / 2 + .04), 0, 2.22), math.pi / 2, linen, folds=16, amp=.02)
    bed_core(out, L - .08, W - .1, .72, duvet, linen, wood)
    export(slug, 'Cama com dossel')


def lounger_slats_only():
    lounger_slats()
    export('mare_lounger_slats', 'Espreguiçadeira de ripas')


BUILD = {
    'mare_lounger_slats': lounger_slats_only,
    'mare_lounger_cushion': lambda: lounger_cushion(),
    'mare_lounger_wicker': lounger_wicker,
    'mare_daybed': daybed,
    'mare_bed_upholstered': bed_upholstered,
    'mare_bed_canopy': bed_canopy,
}

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for slug in args or BUILD:
        BUILD[slug]()
        print('built', slug)
