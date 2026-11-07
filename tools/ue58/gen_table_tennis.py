"""Table tennis set for the Grand Hotel game room: official table, net, two bats and a ball (03/11, "tênis de mesa com
gameplay completo"). No free CC0/CC-BY download was reachable without a login, so it is modelled here at real size.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_table_tennis.py
Output: unreal/MareAlta/SourceArt/Models/GameRoom/{tt_table,tt_bat_red,tt_bat_black,tt_ball}.glb
(metres, base z=0; the table's length runs along X, the net across it at x=0; the bat blade along +Z from the grip).

Table: 2.74 x 1.525 m, top surface at 0.76 m, 25 mm top in matt blue with 20 mm white edge lines and a 3 mm centre
line, a steel apron, folding undercarriage with square tubes, four braked castors. Net assembly 152.5 mm high with
clamps and a woven mesh of real bars. Bat: 157 x 150 mm blade (five-ply wood edge), 2 mm red or black pimpled rubber,
flared anatomic handle. Ball: 40 mm, white with a faint seam.
"""
import math
from pathlib import Path
import bpy
import bmesh
from PIL import Image, ImageDraw, ImageFilter
import random

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models/GameRoom'
TMP = Path('D:/CodexTemp/gameroom_tex')
L, W, TOP, THICK = 2.74, 1.525, .76, .025


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, colour, rough, metal=0.0, image=None, normal=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if image:
        tex = m.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(image))
        tex.image.name = Path(image).stem
        tex.image.pack()
        tex.image.filepath = ''
        m.node_tree.links.new(tex.outputs['Color'], p.inputs['Base Color'])
    if normal:
        tex = m.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(normal))
        tex.image.name = Path(normal).stem
        tex.image.colorspace_settings.name = 'Non-Color'
        tex.image.pack()
        tex.image.filepath = ''
        nm = m.node_tree.nodes.new('ShaderNodeNormalMap')
        m.node_tree.links.new(tex.outputs['Color'], nm.inputs['Color'])
        m.node_tree.links.new(nm.outputs['Normal'], p.inputs['Normal'])
    return m


def obj_from(bm, name, m=None, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if m:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = smooth
    return o


def uv_box(o, size=.5):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=size)
    bpy.ops.object.mode_set(mode='OBJECT')
    o.select_set(False)


def box(name, size, loc, m, bevel=.003, segs=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co.x = v.co.x * size[0] + loc[0]
        v.co.y = v.co.y * size[1] + loc[1]
        v.co.z = v.co.z * size[2] + loc[2]
    o = obj_from(bm, name, m, smooth=False)
    if bevel:
        b = o.modifiers.new('Bevel', 'BEVEL')
        b.width = bevel
        b.segments = segs
        o.modifiers.new('Smooth', 'WEIGHTED_NORMAL') if hasattr(bpy.types, 'WeightedNormalModifier') else None
    uv_box(o)
    return o


def tube(name, radius, a, b, m, seg=20):
    from mathutils import Vector
    a, b = Vector(a), Vector(b)
    axis = (b - a).normalized()
    side = axis.orthogonal().normalized()
    up = axis.cross(side)
    bm = bmesh.new()
    rings = []
    for end in (a, b):
        rings.append([bm.verts.new(end + (side * math.cos(2 * math.pi * k / seg) + up * math.sin(2 * math.pi * k / seg)) * radius) for k in range(seg)])
    for k in range(seg):
        bm.faces.new((rings[0][k], rings[0][(k + 1) % seg], rings[1][(k + 1) % seg], rings[1][k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[1])
    o = obj_from(bm, name, m)
    uv_box(o, .2)
    return o


def lathe(name, profile, loc, m, seg=32, axis='z'):
    bm = bmesh.new()
    rings = []
    for r, h in profile:
        ring = []
        for k in range(seg):
            c, s = r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg)
            p = {'z': (loc[0] + c, loc[1] + s, loc[2] + h), 'y': (loc[0] + c, loc[1] + h, loc[2] + s), 'x': (loc[0] + h, loc[1] + c, loc[2] + s)}[axis]
            ring.append(bm.verts.new(p))
        rings.append(ring)
    for ra, rb in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((ra[k], ra[(k + 1) % seg], rb[(k + 1) % seg], rb[k]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from(bm, name, m)
    uv_box(o, .1)
    return o


def export(objs, name):
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    bpy.ops.export_scene.gltf(filepath=str(OUT / f'{name}.glb'), export_format='GLB', use_selection=True, export_apply=True)
    print('wrote', name)


def top_texture():
    """Matt blue playing surface with a fine speckle, 20 mm white edges and the 3 mm centre line."""
    TMP.mkdir(parents=True, exist_ok=True)
    w, h = 1024, 512   # power of two: the engine drops other sizes on import (stretched over the 2.74 x 1.525 top by UV)
    rnd = random.Random(7)
    img = Image.new('RGB', (w, h), (22, 58, 108))
    px = img.load()
    for _ in range(60000):
        x, y = rnd.randrange(w), rnd.randrange(h)
        d = rnd.randint(-7, 7)
        r, g, b = px[x, y]
        px[x, y] = (max(0, r + d), max(0, g + d), max(0, b + d))
    img = img.filter(ImageFilter.GaussianBlur(.6))
    d = ImageDraw.Draw(img)
    ex, ey = round(.02 / L * w), round(.02 / W * h)   # 20 mm white edges, measured on each axis
    white = (236, 236, 230)
    d.rectangle([0, 0, w - 1, ey], fill=white)
    d.rectangle([0, h - 1 - ey, w - 1, h - 1], fill=white)
    d.rectangle([0, 0, ex, h - 1], fill=white)
    d.rectangle([w - 1 - ex, 0, w - 1, h - 1], fill=white)
    c = max(1, round(.003 / W * h))
    d.rectangle([0, h // 2 - c // 2, w - 1, h // 2 + c // 2], fill=white)
    path = TMP / 'tt_table_top.png'
    img.save(path)
    return path


def rubber_maps(colour, name):
    """Pimpled rubber: colour with a soft grain and a normal map of tiny dimples."""
    TMP.mkdir(parents=True, exist_ok=True)
    n = 256
    img = Image.new('RGB', (n, n), colour)
    nrm = Image.new('RGB', (n, n), (128, 128, 255))
    pc, pn = img.load(), nrm.load()
    for y in range(n):
        for x in range(n):
            u, v = (x % 8) - 3.5, (y % 8) - 3.5
            r2 = u * u + v * v
            if r2 < 9:
                k = math.sqrt(max(0, 9 - r2)) / 3
                pn[x, y] = (int(128 + 70 * u / 3.5 * k), int(128 + 70 * v / 3.5 * k), 230)
                pc[x, y] = tuple(max(0, int(c * (.9 + .1 * k))) for c in colour)
    a, b = TMP / f'tt_{name}_rubber.png', TMP / f'tt_{name}_rubber_nor.png'
    img.save(a)
    nrm.save(b)
    return a, b


def table():
    reset()
    top = mat('tt_table_top', (1, 1, 1), .55, image=top_texture())
    edge = mat('tt_table_edge', (.86, .86, .83), .5)
    steel = mat('tt_table_steel', (.1, .11, .12), .45, .6)
    grey = mat('tt_table_grey', (.55, .56, .58), .35, .9)
    rubber = mat('tt_table_castor', (.06, .06, .06), .8)
    netm = mat('tt_table_net', (.92, .92, .9), .8)
    post = mat('tt_table_post', (.08, .08, .09), .35, .5)
    objs = []
    # The top (two halves with a hairline gap at the net, like a folding table) with UVs over the whole length.
    for sx in (-1, 1):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        x0, x1 = (-L / 2, -.002) if sx < 0 else (.002, L / 2)
        for v in bm.verts:
            v.co.x = x0 if v.co.x < 0 else x1
            v.co.y *= W
            v.co.z = TOP - THICK / 2 + v.co.z * THICK
        o = obj_from(bm, f'top_{sx}', top, smooth=False)
        uv = o.data.uv_layers.new(name='UVMap')
        for poly in o.data.polygons:
            for li in poly.loop_indices:
                co = o.data.vertices[o.data.loops[li].vertex_index].co
                uv.data[li].uv = ((co.x + L / 2) / L, (co.y + W / 2) / W)
        bev = o.modifiers.new('Bevel', 'BEVEL')
        bev.width = .002
        bev.segments = 2
        objs.append(o)
        # Steel apron under the top, 6 cm deep, set 3 cm in from the edges.
        cx = sx * L / 4
        objs.append(box(f'apron_l_{sx}', (L / 2 - .1, .025, .06), (cx, W / 2 - .05, TOP - THICK - .03), steel))
        objs.append(box(f'apron_r_{sx}', (L / 2 - .1, .025, .06), (cx, -W / 2 + .05, TOP - THICK - .03), steel))
        objs.append(box(f'apron_e_{sx}', (.025, W - .1, .06), (sx * (L / 2 - .05), 0, TOP - THICK - .03), steel))
        objs.append(box(f'apron_m_{sx}', (.025, W - .1, .06), (sx * .06, 0, TOP - THICK - .03), steel))
        # Undercarriage: two square-tube legs per half, a cross bar, a diagonal brace and braked castors.
        for sy in (-1, 1):
            lx, ly = sx * (L / 2 - .32), sy * (W / 2 - .2)
            objs.append(box(f'leg_{sx}{sy}', (.04, .04, TOP - THICK - .1), (lx, ly, (TOP - THICK + .1) / 2), steel, .004))
            objs.append(tube(f'brace_{sx}{sy}', .011, (lx, ly, .3), (sx * .18, ly * .9, TOP - THICK - .06), grey))
            objs.append(lathe(f'castor_{sx}{sy}', [(0, -.035), (.03, -.033), (.035, -.02), (.035, .02), (.03, .033), (0, .035)], (lx, ly, .045), rubber, axis='y'))
            objs.append(box(f'fork_{sx}{sy}', (.05, .045, .05), (lx, ly, .095), grey, .004))
        objs.append(box(f'crossbar_{sx}', (.03, W - .4, .03), (sx * (L / 2 - .32), 0, .2), steel, .003))
    # Net assembly: posts with screw clamps 15.25 cm outside the sidelines, a cord on top, a woven mesh below it.
    H = .1525
    for sy in (-1, 1):
        y = sy * (W / 2 + .1525)
        objs.append(box(f'post_{sy}', (.018, .018, H + .02), (0, y, TOP + (H + .02) / 2 - .01), post, .003))
        objs.append(box(f'clamp_{sy}', (.05, .12, .03), (0, sy * (W / 2 + .1), TOP - THICK - .005), post, .004))
        objs.append(lathe(f'screw_{sy}', [(0, -.012), (.013, -.011), (.013, .011), (0, .012)], (0, sy * (W / 2 + .1), TOP - THICK - .04), post, seg=16))
    span = W + 2 * .1525
    objs.append(tube('net_cord', .0035, (0, -span / 2, TOP + H - .003), (0, span / 2, TOP + H - .003), netm, 12))
    objs.append(box('net_band', (.004, span, .015), (0, 0, TOP + H - .012), netm, 0))
    cell = .012
    ny = int(span / cell)
    for k in range(ny + 1):
        y = -span / 2 + k * cell
        objs.append(box(f'mesh_v{k}', (.0018, .0018, H - .02), (0, y, TOP + (H - .02) / 2), netm, 0))
    for k in range(int((H - .02) / cell) + 1):
        z = TOP + .002 + k * cell
        objs.append(box(f'mesh_h{k}', (.0018, span, .0018), (0, 0, z), netm, 0))
    objs.append(box('net_bottom', (.003, span, .006), (0, 0, TOP + .003), netm, 0))
    export(objs, 'tt_table')


def bat(colour, name, back):
    reset()
    face, face_n = rubber_maps(colour, name)
    back_c, back_n = rubber_maps(back, name + '_back')
    front = mat(f'tt_bat_{name}_front', (1, 1, 1), .7, image=face, normal=face_n)
    rear = mat(f'tt_bat_{name}_back', (1, 1, 1), .7, image=back_c, normal=back_n)
    wood = mat(f'tt_bat_{name}_wood', (.72, .55, .34), .55)
    ply = mat(f'tt_bat_{name}_ply', (.45, .3, .16), .6)
    handle = mat(f'tt_bat_{name}_handle', (.62, .44, .25), .45)
    objs = []
    # Blade outline: the classic rounded paddle, 157 x 150 mm, blade along +Z above the grip at the origin.
    pts = []
    for k in range(48):
        a = 2 * math.pi * k / 48
        rx, rz = .075, .0785
        x = rx * math.sin(a)
        z = .1 + .0785 + rz * math.cos(a)
        if z < .115:
            x *= .55 + .45 * (z - .1) / .015 if z > .1 else .55
        pts.append((x, z))
    for layer, (y0, y1, m) in enumerate(((-.0028, .0028, wood), (.0028, .0048, front), (-.0048, -.0028, rear))):
        bm = bmesh.new()
        top = [bm.verts.new((x, y1, z)) for x, z in pts]
        bot = [bm.verts.new((x, y0, z)) for x, z in pts]
        bm.faces.new(top)
        bm.faces.new(bot[::-1])
        n = len(pts)
        for k in range(n):
            bm.faces.new((bot[k], bot[(k + 1) % n], top[(k + 1) % n], top[k]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = obj_from(bm, f'blade_{layer}', m, smooth=False)
        uvl = o.data.uv_layers.new(name='UVMap')
        for poly in o.data.polygons:
            for li in poly.loop_indices:
                co = o.data.vertices[o.data.loops[li].vertex_index].co
                uvl.data[li].uv = (co.x / .16 + .5, (co.z - .1) / .16)
        objs.append(o)
    # Five-ply edge band and the flared handle with a wooden cap.
    objs.append(lathe('handle', [(0, -.002), (.012, 0), (.0135, .02), (.0125, .05), (.015, .085), (.017, .1), (0, .101)], (0, 0, 0), handle, seg=24))
    objs.append(box('handle_flat', (.03, .0115, .1), (0, 0, .05), ply, .004))
    export(objs, f'tt_bat_{name}')


def ball():
    reset()
    m = mat('tt_ball_white', (.96, .95, .92), .35)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=.02, location=(0, 0, .02))
    o = bpy.context.active_object
    o.name = 'ball'
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    export([o], 'tt_ball')


table()
bat((150, 18, 20), 'red', (12, 12, 12))
bat((12, 12, 12), 'black', (150, 18, 20))
ball()
