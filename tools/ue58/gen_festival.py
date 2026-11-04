"""Festival props for the calendar parties (quermesse, festa junina, show do DJ):
- festa_bunting: 6 m string of paper flags (bandeirinhas) sagging between two bamboo poles, poles included;
- festa_stall: quermesse stall with a wooden frame, striped canvas roof with scalloped valance, counter and sign board.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_festival.py
Output: unreal/MareAlta/SourceArt/Models/Festival/{festa_bunting,festa_stall}.glb (metres, base z=0, front = -Y).
- festa_banner: printed canvas banner between bamboo poles (print from tools/ue58/gen_banner_print.py), 04/11.
The other party props (dj_booth, campfire_logs, flame and the old blank party_banner) are the Godot-era bpy models
copied from assets/models/gen by this script."""
import math
import shutil
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'unreal/MareAlta/SourceArt/Models/Festival'
FLAG_COLOURS = [(.85, .1, .12), (.98, .78, .1), (.1, .45, .8), (.1, .62, .3), (.95, .45, .1), (.62, .2, .62), (.98, .98, .95)]


def mat(name, colour, rough=.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    return m


def link(bm, name, mats, smooth=True, keep_uv=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    for m in mats:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = smooth
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    if not keep_uv:   # keep_uv: UVs already laid out in the bmesh (a printed face)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.cube_project(cube_size=.5)
        bpy.ops.object.mode_set(mode='OBJECT')
    o.select_set(False)
    return o


def tube(bm, a, b, r, seg=12, mi=0):
    a, b = Vector(a), Vector(b)
    axis = (b - a).normalized()
    side = axis.orthogonal().normalized()
    up = axis.cross(side)
    rings = [[bm.verts.new(e + (side * math.cos(2 * math.pi * k / seg) + up * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)] for e in (a, b)]
    for k in range(seg):
        f = bm.faces.new((rings[0][k], rings[0][(k + 1) % seg], rings[1][(k + 1) % seg], rings[1][k]))
        f.material_index = mi
    bm.faces.new(rings[0][::-1]).material_index = mi
    bm.faces.new(rings[1]).material_index = mi


def block(bm, size, loc, mi=0, rot=0.0):
    out = bmesh.ops.create_cube(bm, size=1)
    c, s = math.cos(rot), math.sin(rot)
    for v in out['verts']:
        x, y, z = v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]
        v.co = Vector((loc[0] + x * c - y * s, loc[1] + x * s + y * c, loc[2] + z))
    for f in {f for v in out['verts'] for f in v.link_faces}:
        f.material_index = mi


def export(o, name):
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.gltf(filepath=str(OUT / f'{name}.glb'), export_format='GLB', use_selection=True, export_apply=True)
    print('wrote', name, len(o.data.vertices))


def bunting():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    span, top, sag = 6.0, 3.2, .45
    mats = [mat('festa_bunting_pole', (.55, .45, .22), .7), mat('festa_bunting_string', (.85, .82, .72), .8)]
    mats += [mat(f'festa_bunting_flag_{i}', c, .65) for i, c in enumerate(FLAG_COLOURS)]
    bm = bmesh.new()
    for x in (-span / 2, span / 2):
        tube(bm, (x, 0, 0), (x, 0, top + .15), .045, 14, 0)
        for k in range(1, 6):    # bamboo nodes
            tube(bm, (x, 0, k * top / 6 - .02), (x, 0, k * top / 6 + .02), .052, 14, 0)

    def rope(t):
        return Vector((-span / 2 + span * t, 0, top - sag * 4 * t * (1 - t)))
    n = 40
    for k in range(n):
        tube(bm, rope(k / n), rope((k + 1) / n), .006, 6, 1)
    # Triangular paper flags hanging from the rope, slightly turned and cupped like real paper.
    flags = 22
    for k in range(flags):
        t0, t1 = (k + .15) / flags, (k + .85) / flags
        a, b = rope(t0), rope(t1)
        tip = (a + b) / 2 + Vector((0, .03 * math.sin(k * 1.7), -.24))
        mid_l, mid_r = a.lerp(tip, .5) + Vector((0, .012, 0)), b.lerp(tip, .5) + Vector((0, .012, 0))
        vs = [bm.verts.new(p) for p in (a, b, mid_r, tip, mid_l)]
        f = bm.faces.new(vs)
        f.material_index = 2 + k % len(FLAG_COLOURS)
    # Clean, triangulated and consistently wound (the flag pentagons and tube caps confuse the importer otherwise).
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = link(bm, 'festa_bunting', mats, smooth=False)
    sol = o.modifiers.new('Paper', 'SOLIDIFY')
    sol.thickness = .002
    export(o, 'festa_bunting')


def stall():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    W, D, H = 2.4, 1.6, 2.5
    mats = [mat('festa_stall_wood', (.48, .32, .18), .65), mat('festa_stall_canvas_red', (.82, .15, .14), .8),
            mat('festa_stall_canvas_white', (.95, .93, .88), .8), mat('festa_stall_counter', (.62, .45, .28), .55),
            mat('festa_stall_sign', (.98, .8, .2), .6)]
    bm = bmesh.new()
    # Four posts, counter at the front, shelf at the back.
    for x in (-W / 2 + .06, W / 2 - .06):
        for y in (-D / 2 + .06, D / 2 - .06):
            block(bm, (.08, .08, H), (x, y, H / 2), 0)
    block(bm, (W, .5, .06), (0, -D / 2 + .25, 1.0), 3)
    block(bm, (W - .1, .06, .95), (0, -D / 2 + .03, .5), 3)
    block(bm, (W - .2, .35, .04), (0, D / 2 - .2, 1.3), 0)
    # Gabled striped roof: red and white strips, each a slightly sagging quad strip.
    strips = 12
    ridge = H + .55
    for k in range(strips):
        x0, x1 = -W / 2 - .1 + (W + .2) * k / strips, -W / 2 - .1 + (W + .2) * (k + 1) / strips
        for side in (-1, 1):
            rows = 6
            vs = []
            for r in range(rows + 1):
                t = r / rows
                y = side * (D / 2 + .15) * t
                z = ridge - .55 * t - .04 * math.sin(math.pi * t)
                vs.append((bm.verts.new((x0, y, z)), bm.verts.new((x1, y, z))))
            for r in range(rows):
                f = bm.faces.new((vs[r][0], vs[r][1], vs[r + 1][1], vs[r + 1][0]) if side > 0 else (vs[r][1], vs[r][0], vs[r + 1][0], vs[r + 1][1]))
                f.material_index = 1 + k % 2
    # Scalloped valance along the front and back eaves.
    for side in (-1, 1):
        y = side * (D / 2 + .15)
        for k in range(16):
            x0, x1 = -W / 2 - .1 + (W + .2) * k / 16, -W / 2 - .1 + (W + .2) * (k + 1) / 16
            pts = [(x0, y, ridge - .55), (x1, y, ridge - .55)] + [(x1 - (x1 - x0) * j / 6, y, ridge - .55 - .14 * math.sin(math.pi * j / 6)) for j in range(1, 6)]
            f = bm.faces.new([bm.verts.new(p) for p in pts])
            f.material_index = 1 + k % 2
    # Sign board on the front of the roof.
    block(bm, (1.2, .04, .3), (0, -D / 2 - .17, ridge - .3), 4)
    o = link(bm, 'festa_stall', mats, smooth=False)
    sol = o.modifiers.new('Canvas', 'SOLIDIFY')
    sol.thickness = .004
    bev = o.modifiers.new('Bevel', 'BEVEL')
    bev.width = .006
    bev.segments = 2
    export(o, 'festa_stall')


def fire():
    """Bonfire flames: three layers of curling flame tongues (red outside, orange, yellow core), emissive, ~1.4 m tall
    over the campfire logs (base at z=0)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    layers = [((.95, .22, .05), 1.0, .42, 9, 6.0), ((1.0, .5, .08), .82, .32, 7, 9.0), ((1.0, .85, .3), .6, .2, 5, 14.0)]
    objs = []
    for li, (colour, height, radius, tongues, glow) in enumerate(layers):
        m = mat(f'festa_fire_{li}', colour, .5)
        p_ = m.node_tree.nodes['Principled BSDF']
        p_.inputs['Emission Color'].default_value = (*colour, 1)
        p_.inputs['Emission Strength'].default_value = glow
        bm = bmesh.new()
        for t in range(tongues):
            a0 = 2 * math.pi * t / tongues + li * .4
            h = height * (.75 + .25 * math.sin(t * 2.3 + li))
            rings = []
            steps = 10
            for k in range(steps + 1):
                u = k / steps
                r = radius * .35 * (1 - u) ** 1.2 + .01
                twist = a0 + u * 1.3
                cx = math.cos(twist) * radius * .45 * (1 - u * .7)
                cy = math.sin(twist) * radius * .45 * (1 - u * .7)
                rings.append([bm.verts.new((cx + r * math.cos(2 * math.pi * j / 8), cy + r * math.sin(2 * math.pi * j / 8), .08 + u * h)) for j in range(8)])
            for ra, rb in zip(rings, rings[1:]):
                for j in range(8):
                    bm.faces.new((ra[j], ra[(j + 1) % 8], rb[(j + 1) % 8], rb[j]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        objs.append(link(bm, f'fire_{li}', [m]))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    export(objs[0], 'festa_fire')


def banner():
    """festa_banner: printed canvas banner (3.6 x 0.9 m, tools/ue58/gen_banner_print.py) between two bamboo poles,
    hemmed, with brass grommets and ropes tied round the poles; the back is plain canvas (the print reads only from
    the front). Replaces the Godot-era blank banner (party_banner)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    span, w, h, mid = 4.3, 3.6, .9, 2.35
    print_img = bpy.data.images.load(str(OUT / 'festa_banner_print.png'))
    print_img.name = 'festa_banner_print'
    print_img.pack()
    printed = bpy.data.materials.new('festa_banner_print')
    printed.use_nodes = True
    nodes = printed.node_tree.nodes
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = print_img
    bsdf = nodes['Principled BSDF']
    printed.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = .85
    mats = [mat('festa_banner_bamboo', (.55, .45, .22), .7), printed, mat('festa_banner_canvas', (.86, .8, .66), .9),
            mat('festa_banner_rope', (.78, .72, .58), .85), mat('festa_banner_brass', (.72, .55, .25), .35, 1.0)]
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new('UVMap')
    for x in (-span / 2, span / 2):
        tube(bm, (x, 0, 0), (x, 0, mid + h / 2 + .45), .05, 16, 0)
        for k in range(1, 7):
            z = k * (mid + h / 2 + .45) / 7
            tube(bm, (x, 0, z - .02), (x, 0, z + .02), .057, 16, 0)
    # Cloth: a gentle sag and wind ripple; front grid printed (UV 0..1), the back 3 mm behind in plain canvas.
    nx, nz = 48, 12

    def cloth_point(i, j, back):
        u, v = i / nx, j / nz
        x = -w / 2 + w * u
        z = mid - h / 2 + h * v - .06 * 4 * u * (1 - u) * (1 - .4 * v)
        y = .035 * math.sin(u * math.pi * 3 + v * .8) * 4 * u * (1 - u) + (.003 if back else 0)
        return Vector((x, y, z))
    for back, mi in ((False, 1), (True, 2)):
        grid = [[bm.verts.new(cloth_point(i, j, back)) for j in range(nz + 1)] for i in range(nx + 1)]
        for i in range(nx):
            for j in range(nz):
                quad = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
                uvs = [(i / nx, j / nz), ((i + 1) / nx, j / nz), ((i + 1) / nx, (j + 1) / nz), (i / nx, (j + 1) / nz)]
                f = bm.faces.new(quad if back else quad[::-1])
                f.material_index = mi
                # UV written with the face: each loop gets the UV of its own vertex.
                lookup = dict(zip(quad, uvs))
                for loop in f.loops:
                    loop[uv_layer].uv = lookup[loop.vert]
                f.tag = True
    # Hems (rolled canvas along the top and bottom edges) and the side seams.
    for j, r in ((0, .012), (nz, .012)):
        for i in range(nx):
            tube(bm, cloth_point(i, j, False) + Vector((0, .0015, 0)), cloth_point(i + 1, j, False) + Vector((0, .0015, 0)), r, 8, 2)
    for i in (0, nx):
        for j in range(nz):
            tube(bm, cloth_point(i, j, False) + Vector((0, .0015, 0)), cloth_point(i, j + 1, False) + Vector((0, .0015, 0)), .01, 8, 2)
    # Brass grommets at the four corners and a rope from each to its pole, wrapped twice round the bamboo.
    for i, j in ((0, 0), (0, nz), (nx, 0), (nx, nz)):
        c = cloth_point(i, j, False) + Vector((.05 if i == 0 else -.05, .0015, .05 if j == 0 else -.05))
        ring = bmesh.ops.create_circle(bm, cap_ends=False, radius=.018, segments=16)['verts']
        for v in ring:
            v.co = Vector((c.x + v.co.x, c.y, c.z + v.co.y))
        thick = bmesh.ops.extrude_edge_only(bm, edges=list({e for v in ring for e in v.link_edges}))['geom']
        for v in [g for g in thick if isinstance(g, bmesh.types.BMVert)]:
            v.co.y += .006
        for f in {f for v in ring for f in v.link_faces}:
            f.material_index = 4
        pole_x = -span / 2 if i == 0 else span / 2
        tie = Vector((pole_x + (.055 if i == 0 else -.055), 0, c.z + (.03 if j == 0 else -.03)))
        tube(bm, c, tie, .012, 8, 3)   # ropes at least 12 mm radius (project rule: thin cords vanish)
        for k in range(2):
            z = tie.z + (k - .5) * .026
            for s in range(12):
                a0, a1 = 2 * math.pi * s / 12, 2 * math.pi * (s + 1) / 12
                tube(bm, (pole_x + .064 * math.cos(a0), .064 * math.sin(a0), z), (pole_x + .064 * math.cos(a1), .064 * math.sin(a1), z), .012, 6, 3)
    for f in bm.faces:
        if not f.tag:   # poles, hems, ropes: a simple planar map for the solid colours
            for loop in f.loops:
                loop[uv_layer].uv = (loop.vert.co.x * .3, loop.vert.co.z * .3)
    bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if not f.tag])
    o = link(bm, 'festa_banner', mats, keep_uv=True)
    export(o, 'festa_banner')


def copy_godot_models():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ('dj_booth', 'campfire_logs', 'flame', 'party_banner'):
        shutil.copy(ROOT / 'assets/models/gen' / f'{name}.glb', OUT / f'festa_{name}.glb')
        print('copied', name)


if __name__ == '__main__':
    import sys
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for name, fn in (('bunting', bunting), ('stall', stall), ('fire', fire), ('banner', banner), ('copy', copy_godot_models)):
        if not only or name in only:
            fn()
