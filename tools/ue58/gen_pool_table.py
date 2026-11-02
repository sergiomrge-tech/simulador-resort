"""Bar pool table (7 ft), 16 numbered balls and a cue for the Grand Hotel game room (gameplay plan M5).
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_pool_table.py
Output: unreal/MareAlta/SourceArt/Models/GameRoom/{pool_table,pool_cue,pool_ball_00..15}.glb (metres, base z=0).

Real dimensions (WPA bar table): playing surface 1.98 x 0.99 m, cushion nose 2.4 cm above the cloth, ball 57.15 mm,
cloth top at 0.78 m. The physics in Unreal uses these same numbers (MareGameRoom), so keep them in sync.
"""
import math
from pathlib import Path
import bpy
import bmesh
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models/GameRoom'
PLAY_L, PLAY_W, CLOTH_Z = 1.98, .99, .78
RAIL, CUSHION, BALL_R = .13, .05, .028575
POCKET_R = .062
COLOURS = {1: (240, 196, 25), 2: (24, 70, 170), 3: (205, 35, 35), 4: (95, 40, 140), 5: (240, 120, 25), 6: (20, 120, 60), 7: (125, 30, 30), 8: (15, 15, 15)}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, colour, rough, metal=0.0, image=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if image:
        tex = m.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(image))
        tex.image.name = Path(image).stem            # unique image name (UE matches textures by name)
        tex.image.pack()
        tex.image.filepath = ''
        m.node_tree.links.new(tex.outputs['Color'], p.inputs['Base Color'])
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


def box(name, size, loc, m, bevel=.004):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts:
        v.co = v.co * 1
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
        v.co.x += loc[0]; v.co.y += loc[1]; v.co.z += loc[2]
    o = obj_from(bm, name, m, smooth=False)
    if bevel:
        b = o.modifiers.new('Bevel', 'BEVEL'); b.width = bevel; b.segments = 3
    uv_box(o)
    return o


def uv_box(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=.5)
    bpy.ops.object.mode_set(mode='OBJECT')
    o.select_set(False)


def lathe(name, profile, loc, m, seg=32):
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        rings.append([bm.verts.new((loc[0] + r * math.cos(2 * math.pi * k / seg), loc[1] + r * math.sin(2 * math.pi * k / seg), loc[2] + z)) for k in range(seg)])
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from(bm, name, m)
    me = o.data
    uv = me.uv_layers.new(name='UVMap')
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = ((math.atan2(co.y - loc[1], co.x - loc[0]) / (2 * math.pi)) % 1, (co.z - loc[2]))
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


def table():
    reset()
    wood = mat('pool_table_walnut', (.24, .12, .06), .45)
    cloth = mat('pool_table_cloth', (.012, .12, .15), .95)
    rubber = mat('pool_table_cushion', (.01, .1, .13), .9)
    leather = mat('pool_table_pocket', (.04, .03, .025), .6)
    brass = mat('pool_table_brass', (.78, .6, .3), .3, 1.0)
    pearl = mat('pool_table_sight', (.92, .9, .84), .25)
    parts = []
    L, W = PLAY_L, PLAY_W
    # Slate bed with cloth, rails, apron and turned legs.
    parts.append(box('bed', (L + .02, W + .02, .045), (0, 0, CLOTH_Z - .0225), cloth, .002))
    for sx in (-1, 1):
        parts.append(box(f'rail_long{sx}', (L + 2 * RAIL, RAIL, .065), (0, sx * (W / 2 + RAIL / 2), CLOTH_Z + .0125), wood, .008))
        parts.append(box(f'rail_end{sx}', (RAIL, W, .065), (sx * (L / 2 + RAIL / 2), 0, CLOTH_Z + .0125), wood, .008))
    # Cushions: wedge profile, nose 2.4 cm above the cloth, gaps for the six pockets.
    def cushion(x0, x1, y, inward):
        bm = bmesh.new()
        prof = [(0, 0), (CUSHION, 0), (CUSHION * .2, .036), (0, .044)]
        a = [bm.verts.new((x0, y + inward * p[0] * 0 + inward * 0, CLOTH_Z + p[1])) for p in prof]
        for v, p in zip(a, prof):
            v.co.y = y - inward * (CUSHION - p[0]) * 0 + inward * p[0] - inward * 0
        b = [bm.verts.new((x1, v.co.y, v.co.z)) for v in a]
        for i in range(len(prof)):
            j = (i + 1) % len(prof)
            bm.faces.new((a[i], a[j], b[j], b[i]))
        bm.faces.new(a[::-1]); bm.faces.new(b)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return obj_from(bm, 'cushion', rubber, smooth=False)
    gap = POCKET_R * 1.1
    for sy in (-1, 1):
        y = sy * W / 2
        parts.append(cushion(-L / 2 + gap, -gap * .8, y, -sy))
        parts.append(cushion(gap * .8, L / 2 - gap, y, -sy))
    for sx in (-1, 1):
        bm = bmesh.new()
        x = sx * L / 2
        prof = [(0, 0), (CUSHION, 0), (CUSHION * .2, .036), (0, .044)]
        a = [bm.verts.new((x - sx * p[0], -W / 2 + gap, CLOTH_Z + p[1])) for p in prof]
        b = [bm.verts.new((v.co.x, W / 2 - gap, v.co.z)) for v in a]
        for i in range(len(prof)):
            j = (i + 1) % len(prof)
            bm.faces.new((a[i], a[j], b[j], b[i]))
        bm.faces.new(a[::-1]); bm.faces.new(b)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(obj_from(bm, 'cushion_end', rubber, smooth=False))
    # Pockets: holes cut through bed, rails and cushions; leather cups hang below the cloth, brass rims on the rails.
    pockets = [(px * 1.012, py * 1.03) for px, py in [(-L / 2, -W / 2), (0, -W / 2), (L / 2, -W / 2), (-L / 2, W / 2), (0, W / 2), (L / 2, W / 2)]]
    for px, py in pockets:
        bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=POCKET_R * 1.12, depth=.4, location=(px, py, CLOTH_Z))
        cutter = bpy.context.active_object
        for o in parts:
            if o.name.startswith(('bed', 'rail', 'cushion')):
                m = o.modifiers.new('Pocket', 'BOOLEAN'); m.object = cutter; m.operation = 'DIFFERENCE'; m.solver = 'EXACT'
                bpy.context.view_layer.objects.active = o
                for mod in list(o.modifiers):
                    bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
    for px, py in pockets:
        parts.append(lathe('pocket', [(.0, -.15), (POCKET_R * .75, -.14), (POCKET_R * 1.05, -.07), (POCKET_R * 1.12, -.01), (POCKET_R * 1.12, .0)], (px, py, CLOTH_Z), leather, 32))
        parts.append(lathe('pocket_rim', [(POCKET_R * 1.12, .044), (POCKET_R * 1.32, .047), (POCKET_R * 1.32, .053), (POCKET_R * 1.12, .054), (POCKET_R * 1.12, .044)], (px, py, CLOTH_Z), brass, 32))
    # Diamond sights on the rails.
    for k in (-3, -2, -1, 1, 2, 3):
        for sy in (-1, 1):
            parts.append(lathe('sight', [(0, 0), (.007, 0), (.007, .002), (0, .003)], (k * L / 8, sy * (W / 2 + RAIL * .55), CLOTH_Z + .045), pearl, 12))
    for k in (-1, 0, 1):
        for sx in (-1, 1):
            parts.append(lathe('sight', [(0, 0), (.007, 0), (.007, .002), (0, .003)], (sx * (L / 2 + RAIL * .55), k * W / 4, CLOTH_Z + .045), pearl, 12))
    # Apron (frame under the rails) and turned legs.
    parts.append(box('apron', (L + 2 * RAIL - .04, W + 2 * RAIL - .04, .16), (0, 0, CLOTH_Z - .125), wood, .01))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(lathe('leg', [(.0, 0), (.075, 0), (.075, .05), (.055, .07), (.05, .2), (.065, .3), (.045, .42), (.04, .5), (.06, .56), (.06, .58), (.0, .58)],
                               (sx * (L / 2 - .05), sy * (W / 2 - .02), 0), wood, 24))
    export(parts, 'pool_table')


def ball_texture(n):
    """Equirectangular 512x256: solid (1-8), striped (9-15), white cue ball (0), number in a white circle twice."""
    img = Image.new('RGB', (512, 256), (245, 242, 232))
    d = ImageDraw.Draw(img)
    if n:
        c = COLOURS[n if n <= 8 else n - 8]
        if n <= 8:
            d.rectangle((0, 0, 512, 256), fill=c)
        else:
            d.rectangle((0, 70, 512, 186), fill=c)
        font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 34)
        for cx in (128, 384):
            d.ellipse((cx - 30, 98, cx + 30, 158), fill=(245, 242, 232))
            t = str(n)
            w = d.textlength(t, font=font)
            d.text((cx - w / 2, 108), t, fill=(20, 20, 20), font=font)
    path = OUT / 'textures' / f'T_pool_ball_{n:02d}.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def balls():
    for n in range(16):
        reset()
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=BALL_R, location=(0, 0, BALL_R))
        o = bpy.context.active_object
        o.name = f'pool_ball_{n:02d}'
        for p in o.data.polygons:
            p.use_smooth = True
        o.data.materials.append(mat(f'pool_ball_{n:02d}_ivory', (1, 1, 1), .08, image=ball_texture(n)))
        bpy.ops.export_scene.gltf(filepath=str(OUT / f'pool_ball_{n:02d}.glb'), export_format='GLB', use_selection=True, export_apply=True)
    print('wrote 16 balls')


def cue():
    reset()
    maple = mat('pool_cue_maple', (.86, .72, .5), .4)
    ebony = mat('pool_cue_butt', (.08, .05, .04), .35)
    tip = mat('pool_cue_tip', (.15, .35, .55), .9)
    ferrule = mat('pool_cue_ferrule', (.94, .93, .9), .3)
    # Lying along +X, 1.47 m: butt at x=0 (cue axis built along z then rotated).
    parts = [lathe('butt', [(0, 0), (.0145, 0), (.0145, .005), (.0142, .55), (.0125, .72)], (0, 0, 0), ebony, 28),
             lathe('shaft', [(.0125, .72), (.0105, 1.1), (.0065, 1.44)], (0, 0, 0), maple, 28),
             lathe('ferrule', [(.0065, 1.44), (.0065, 1.465), (.0062, 1.465)], (0, 0, 0), ferrule, 20),
             lathe('tip', [(.0062, 1.465), (.0062, 1.475), (.004, 1.479), (0, 1.48)], (0, 0, 0), tip, 20)]
    for o in parts:
        o.rotation_euler = (0, math.radians(90), 0)
    export(parts, 'pool_cue')


table()
balls()
cue()
