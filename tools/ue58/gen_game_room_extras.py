"""Foosball table (pebolim) and an upright arcade cabinet (fliperama) for the Grand Hotel game room.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_game_room_extras.py
Output: unreal/MareAlta/SourceArt/Models/GameRoom/{foosball_table,arcade_cabinet}.glb (metres, base z=0, front = -Y).

Foosball: 1.40 x 0.75 m cabinet, field at 0.80 m, 8 rods (1-2-5-3-3-5-2-1 players, red and blue teams), chrome rods,
black grips. Arcade: 1.75 m upright, angled screen with a title screen, lit marquee, joystick and six buttons.
"""
import math
from pathlib import Path
import bpy
import bmesh
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models/GameRoom'
TMP = Path('D:/CodexTemp/gameroom_tex')


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, colour, rough, metal=0.0, image=None, emit=0.0):
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
        if emit:
            m.node_tree.links.new(tex.outputs['Color'], p.inputs['Emission Color'])
    if emit:
        p.inputs['Emission Strength'].default_value = emit
        if not image:
            p.inputs['Emission Color'].default_value = (*colour, 1)
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


def uv_box(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=.5)
    bpy.ops.object.mode_set(mode='OBJECT')
    o.select_set(False)


def box(name, size, loc, m, bevel=.004):
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
        b.segments = 3
    uv_box(o)
    return o


def cylinder(name, radius, a, b, m, seg=24):
    """Round bar from point a to point b (axis along any direction)."""
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
    uv_box(o)
    return o


def lathe(name, profile, loc, m, seg=28, axis='z'):
    bm = bmesh.new()
    rings = []
    for r, h in profile:
        ring = []
        for k in range(seg):
            c, s = r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg)
            p = (loc[0] + c, loc[1] + s, loc[2] + h) if axis == 'z' else (loc[0] + c, loc[1] + h, loc[2] + s)
            ring.append(bm.verts.new(p))
        rings.append(ring)
    for ra, rb in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((ra[k], ra[(k + 1) % seg], rb[(k + 1) % seg], rb[k]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from(bm, name, m)
    uv_box(o)
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


def field_texture():
    """Green felt with white lines, centre circle and goal areas (1.20 x 0.68 m field)."""
    TMP.mkdir(parents=True, exist_ok=True)
    W, H = 1024, 580
    img = Image.new('RGB', (W, H), (34, 120, 52))
    d = ImageDraw.Draw(img)
    for k in range(0, W, 64):
        d.rectangle([k, 0, k + 31, H], fill=(38, 130, 57))
    d.rectangle([12, 12, W - 12, H - 12], outline=(240, 240, 235), width=6)
    d.line([W // 2, 12, W // 2, H - 12], fill=(240, 240, 235), width=6)
    d.ellipse([W // 2 - 80, H // 2 - 80, W // 2 + 80, H // 2 + 80], outline=(240, 240, 235), width=6)
    for x0, x1 in ((12, 120), (W - 120, W - 12)):
        d.rectangle([x0, H // 2 - 130, x1, H // 2 + 130], outline=(240, 240, 235), width=6)
    path = TMP / 'foosball_field_felt.png'
    img.save(path)
    return path


def foosball():
    reset()
    L, W, FIELD = 1.40, .75, .80
    wood = mat('foosball_wood', (.42, .24, .12), .55)
    dark = mat('foosball_dark', (.08, .08, .09), .5)
    chrome = mat('foosball_chrome', (.85, .86, .88), .18, 1.0)
    grip = mat('foosball_grip', (.05, .05, .05), .8)
    red = mat('foosball_red_team', (.75, .08, .08), .4)
    blue = mat('foosball_blue_team', (.1, .22, .7), .4)
    felt = mat('foosball_felt', (1, 1, 1), .9, image=field_texture())
    objs = []
    # Cabinet walls (2.5 cm thick) around the field, a raised rim and the floor of the field.
    t = .025
    objs.append(box('side_n', (L, t, .22), (0, W / 2 - t / 2, FIELD + .06), wood))
    objs.append(box('side_s', (L, t, .22), (0, -W / 2 + t / 2, FIELD + .06), wood))
    for sx in (-1, 1):
        # End walls with the goal mouth: two blocks beside the goal and one above it.
        objs.append(box(f'end_{sx}_a', (t, (W - .22) / 2, .22), (sx * (L / 2 - t / 2), (W + .22) / 4, FIELD + .06), wood))
        objs.append(box(f'end_{sx}_b', (t, (W - .22) / 2, .22), (sx * (L / 2 - t / 2), -(W + .22) / 4, FIELD + .06), wood))
        objs.append(box(f'end_{sx}_top', (t, .22, .12), (sx * (L / 2 - t / 2), 0, FIELD + .11), wood))
        objs.append(box(f'goal_{sx}', (.08, .22, .1), (sx * (L / 2 + .03), 0, FIELD), dark))
    field = box('field', (L - 2 * t, W - 2 * t, .02), (0, 0, FIELD - .05), felt, bevel=0)
    objs.append(field)
    objs.append(box('apron', (L, W, .12), (0, 0, FIELD - .12), wood))
    # Legs, feet and a stretcher bar.
    for sx in (-1, 1):
        for sy in (-1, 1):
            objs.append(box(f'leg_{sx}{sy}', (.07, .07, FIELD - .18), (sx * (L / 2 - .08), sy * (W / 2 - .08), (FIELD - .18) / 2), wood))
            objs.append(box(f'foot_{sx}{sy}', (.1, .1, .03), (sx * (L / 2 - .08), sy * (W / 2 - .08), .015), dark))
        objs.append(box(f'stretch_{sx}', (.04, W - .16, .05), (sx * (L / 2 - .08), 0, .18), wood))
    objs.append(box('stretch_mid', (L - .16, .04, .05), (0, 0, .18), wood))
    # Eight rods across the field: goalkeeper, defence, midfield, attack for each team, alternating sides.
    counts = [1, 2, 5, 3, 3, 5, 2, 1]
    teams = [red, red, blue, red, blue, red, blue, blue]
    rod_z = FIELD + .10
    for i, (n, team) in enumerate(zip(counts, teams)):
        x = -L / 2 + .09 + i * (L - .18) / 7
        handle_side = -1 if team is red else 1
        objs.append(cylinder(f'rod_{i}', .008, (x, -W / 2 - .18, rod_z), (x, W / 2 + .18, rod_z), chrome))
        hy = handle_side * (W / 2 + .2)
        objs.append(lathe(f'grip_{i}', [(0, -.07), (.016, -.069), (.018, -.06), (.017, 0), (.018, .06), (.016, .069), (0, .07)], (x, hy, rod_z), grip, axis='y'))
        objs.append(lathe(f'bumper_{i}', [(0, -.006), (.02, -.005), (.02, .005), (0, .006)], (x, -handle_side * (W / 2 + .02), rod_z), dark, axis='y'))
        span = W - .16
        for k in range(n):
            y = 0 if n == 1 else -span / 2 + span * (k + .5) / n * (1 if n > 2 else 1) if n > 2 else (k - .5) * .2
            # Player: rounded torso hanging from the rod, head above it, legs and a foot block below.
            objs.append(lathe(f'p{i}_{k}_body', [(0, -.07), (.014, -.068), (.017, -.04), (.02, -.01), (.022, .02), (.019, .035), (0, .04)], (x, y, rod_z), team))
            objs.append(lathe(f'p{i}_{k}_head', [(0, .04), (.012, .045), (.015, .056), (.012, .067), (0, .071)], (x, y, rod_z), team))
            objs.append(box(f'p{i}_{k}_foot', (.03, .028, .025), (x + .004, y, rod_z - .085), team, bevel=.004))
    for o in objs:
        pass
    export(objs, 'foosball_table')


def screen_texture():
    """Title screen of the arcade: night sky, pixel palm, wave and the game title."""
    TMP.mkdir(parents=True, exist_ok=True)
    W, H = 512, 400
    img = Image.new('RGB', (W, H), (12, 14, 40))
    d = ImageDraw.Draw(img)
    for k in range(40):
        x, y = (k * 97) % W, (k * 53) % 220
        d.rectangle([x, y, x + 3, y + 3], fill=(240, 240, 200))
    d.rectangle([0, 300, W, H], fill=(20, 80, 160))
    for k in range(0, W, 32):
        d.polygon([(k, 300), (k + 16, 284), (k + 32, 300)], fill=(240, 250, 255))
    d.rectangle([80, 170, 92, 300], fill=(120, 70, 30))
    for a in range(5):
        ang = math.radians(150 + a * 40)
        d.line([86, 170, 86 + 70 * math.cos(ang), 170 - 40 * math.sin(ang)], fill=(40, 170, 60), width=12)
    d.rectangle([150, 60, 470, 150], fill=(230, 60, 120))
    d.rectangle([160, 70, 460, 140], fill=(250, 210, 40))
    for i, ch in enumerate('MARE ATTACK'):
        x = 172 + i * 26
        d.rectangle([x, 88, x + 18, 122], outline=(30, 20, 60), width=5)
    d.rectangle([200, 220, 420, 250], fill=(255, 255, 255))
    path = TMP / 'arcade_screen_title.png'
    img.save(path)
    return path


def marquee_texture():
    TMP.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGB', (512, 128), (250, 120, 30))
    d = ImageDraw.Draw(img)
    for k in range(0, 512, 40):
        d.polygon([(k, 128), (k + 20, 0), (k + 40, 128)], fill=(240, 70, 110))
    d.rectangle([60, 30, 452, 98], fill=(255, 230, 80))
    for i in range(11):
        d.rectangle([80 + i * 34, 44, 100 + i * 34, 84], outline=(40, 20, 80), width=5)
    path = TMP / 'arcade_marquee_art.png'
    img.save(path)
    return path


def arcade():
    reset()
    W, D = .64, .78
    body = mat('arcade_body', (.08, .1, .35), .45)
    side = mat('arcade_side_art', (.9, .32, .1), .5)
    black = mat('arcade_black', (.03, .03, .035), .6)
    screen = mat('arcade_screen', (1, 1, 1), .2, image=screen_texture(), emit=1.2)
    marquee = mat('arcade_marquee', (1, 1, 1), .4, image=marquee_texture(), emit=2.0)
    chrome = mat('arcade_chrome', (.8, .8, .82), .2, 1.0)
    red = mat('arcade_button_red', (.85, .08, .08), .3)
    yellow = mat('arcade_button_yellow', (.95, .78, .1), .3)
    objs = []
    # Side panels: classic profile (deep base, control-panel step, slanted screen, overhanging marquee).
    profile = [(-.39, 0), (.39, 0), (.39, 1.75), (-.08, 1.75), (-.14, 1.55), (-.06, 1.5), (-.14, 1.12), (-.39, 1.0), (-.39, .95), (-.3, .9)]
    for sx in (-1, 1):
        bm = bmesh.new()
        front = [bm.verts.new((sx * (W / 2 - .01), y, z)) for y, z in profile]
        back = [bm.verts.new((sx * (W / 2 + .01), y, z)) for y, z in profile]
        bm.faces.new(front if sx < 0 else front[::-1])
        bm.faces.new(back[::-1] if sx < 0 else back)
        n = len(profile)
        for k in range(n):
            bm.faces.new((front[k], front[(k + 1) % n], back[(k + 1) % n], back[k]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = obj_from(bm, f'side_{sx}', side, smooth=False)
        uv_box(o)
        objs.append(o)
    # Cabinet shell between the sides.
    objs.append(box('back', (W - .02, .02, 1.75), (0, .38, .875), body))
    objs.append(box('base_front', (W - .02, .02, .9), (0, -.3, .45), body))
    objs.append(box('top', (W - .02, .31, .02), (0, .155, 1.74), body))
    objs.append(box('coin_door', (.28, .01, .3), (0, -.312, .55), black))
    for k in (-1, 1):
        objs.append(box(f'coin_slot_{k}', (.04, .012, .07), (k * .06, -.318, .62), chrome, bevel=.002))
    # Control panel (sloped), joystick and buttons.
    panel = box('panel', (W - .02, .3, .03), (0, -.25, .97), black)
    panel.rotation_euler = (math.radians(-12), 0, 0)
    objs.append(panel)
    objs.append(lathe('stick', [(0, 0), (.006, 0), (.006, .09), (0, .09)], (-.14, -.26, .985), chrome))
    objs.append(lathe('stick_ball', [(0, .075), (.018, .085), (.022, .1), (.018, .115), (0, .125)], (-.14, -.26, .985), red))
    for i in range(6):
        bx, by = .02 + (i % 3) * .06, -.29 + (i // 3) * .06
        objs.append(lathe(f'button_{i}', [(0, 0), (.016, 0), (.016, .012), (.013, .016), (0, .017)], (bx, by, .99 - (by + .25) * .2), red if i % 2 else yellow))
    # Slanted screen with its bezel, and the lit marquee on top.
    bez = box('bezel', (W - .04, .02, .42), (0, -.1, 1.33), black)
    bez.rotation_euler = (math.radians(-18), 0, 0)
    objs.append(bez)
    bm = bmesh.new()
    sw, sh = .46, .36
    vs = [bm.verts.new((x, -.112, z)) for x, z in ((-sw / 2, -sh / 2), (sw / 2, -sh / 2), (sw / 2, sh / 2), (-sw / 2, sh / 2))]
    f = bm.faces.new(vs)
    o = obj_from(bm, 'screen', screen, smooth=False)
    uv = o.data.uv_layers.new(name='UVMap')
    for loop, (u, v) in zip(o.data.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[loop.index].uv = (u, v)
    o.location = (0, 0, 1.33)
    o.rotation_euler = (math.radians(-18), 0, 0)
    objs.append(o)
    bm = bmesh.new()
    mw, mh = W - .04, .16
    vs = [bm.verts.new((x, -.081, z)) for x, z in ((-mw / 2, 1.58), (mw / 2, 1.58), (mw / 2, 1.58 + mh), (-mw / 2, 1.58 + mh))]
    bm.faces.new(vs)
    o = obj_from(bm, 'marquee', marquee, smooth=False)
    uv = o.data.uv_layers.new(name='UVMap')
    for loop, (u, v) in zip(o.data.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[loop.index].uv = (u, v)
    objs.append(o)
    objs.append(box('marquee_box', (W - .02, .1, .2), (0, -.03, 1.66), body))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    export(objs, 'arcade_cabinet')


foosball()
arcade()
