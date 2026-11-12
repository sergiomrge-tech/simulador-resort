"""Upright arcade cabinets of the Grand Hotel game room (CHECKLIST 5.4 "2 fliperamas jogáveis em tela"): one per game,
"Corrida de Jangada" and "Pega-Siri". The game itself is drawn by UMareArcade (Source/MareAlta/MareArcade.cpp) on a
render target that replaces the screen material at run time; the model's own screen shows the title (attract) image.

Real metres, base at z=0, centre of the footprint at the origin, FRONT = Blender -Y (arrives as UE +Y; the cabinets
stand at yaw 180 against the north wall, business_games.json game_room.arcades). 0.66 m wide, 0.80 m deep (the control
panel juts out to y -0.47), 1.84 m tall.
Screen (keep in sync with MareArcade.h, namespace MareArc): 0.40 x 0.30 m (4:3), centre Blender (0, -0.2097, 1.2905)
= UE local (0, 20.97, 129.05) cm, tilted back 12.9 degrees: outward normal Blender (0, -0.9749, 0.2225) = UE (0, 0.9749,
0.2225). UVs: u left->right and v top->bottom as seen from the front (UE convention), the title image upright.

  mare_arcade_jangada   blue cabinet, yellow T-molding, "JANGADA" marquee
  mare_arcade_siri      red cabinet, orange T-molding, "PEGA-SIRI" marquee
Art: tools/ue58/gen_arcade_art.py (SourceArt/UI/Arcade/T_Arc_*.png). Shape and parts are this script's own.
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_arcade_cabinet.py [slug ...]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from gen_custom_furniture import OUT, box, export, finish, lathe, mesh_obj, reset, tube  # noqa: E402

ART = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/UI/Arcade'
W, ST = .66, .019                     # outer width, side panel thickness
IN = W / 2 - ST                       # inner half width
# Side profile (y, z), counter-clockwise seen from +X; front is -Y.
PROFILE = [(.33, 0.0), (-.33, 0.0), (-.33, .84), (-.47, .90), (-.47, .97), (-.28, 1.03), (-.26, 1.06),
           (-.155, 1.52), (-.24, 1.56), (-.26, 1.84), (.33, 1.84)]
BEZ0, BEZ1 = (-.26, 1.06), (-.155, 1.52)          # bezel line (bottom, top)
SCREEN_W, SCREEN_H = .40, .30
GAMES = {
    'mare_arcade_jangada': {'name': 'Fliperama "Corrida de Jangada"', 'key': 'J', 'body': (.02, .07, .2),
                            'mold': (.95, .74, .12), 'panel': (.03, .16, .42), 'ball': (.85, .1, .08),
                            'buttons': [(.95, .78, .1), (.9, .12, .1), (.1, .55, .9)]},
    'mare_arcade_siri': {'name': 'Fliperama "Pega-Siri"', 'key': 'S', 'body': (.2, .04, .02),
                         'mold': (.98, .5, .1), 'panel': (.5, .1, .05), 'ball': (.1, .1, .12),
                         'buttons': [(.98, .55, .1), (.95, .9, .2), (.2, .7, .3)]},
}


def plain(name, rgb, rough=.5, metal=0.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = emit
    return m


def image_mat(name, path, rough=.4, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(path))
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    if emit:
        nt.links.new(tex.outputs['Color'], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = emit
    return m


def bezel_frame():
    """Bezel axes: origin at the bezel centre, u across (+X), v up the bezel, n outward."""
    (y0, z0), (y1, z1) = BEZ0, BEZ1
    L = math.hypot(y1 - y0, z1 - z0)
    v = ((y1 - y0) / L, (z1 - z0) / L)
    n = (-v[1], v[0])                  # outward: -Y and +Z
    c = ((y0 + y1) / 2, (z0 + z1) / 2)
    return c, v, n, L


def at(c, v, n, u, s, d):
    """Point on the bezel: u across (x), s up the bezel, d out along the normal."""
    return (u, c[0] + v[0] * s + n[0] * d, c[1] + v[1] * s + n[1] * d)


def side_panels(art, mold, inner):
    """Both side panels: the profile extruded 19 mm; the outer face carries the side art, the 19 mm edge is the
    T-molding, the inner face is plain laminate."""
    ys = [p[0] for p in PROFILE]
    y_min, y_max, z_max = min(ys), max(ys), max(p[1] for p in PROFILE)
    for s in (-1, 1):
        bm = bmesh.new()
        x_out, x_in = s * W / 2, s * IN
        ring_o = [bm.verts.new((x_out, y, z)) for y, z in PROFILE]
        ring_i = [bm.verts.new((x_in, y, z)) for y, z in PROFILE]
        f_out = bm.faces.new(ring_o if s > 0 else list(reversed(ring_o)))
        f_in = bm.faces.new(list(reversed(ring_i)) if s > 0 else ring_i)
        edges = []
        n = len(PROFILE)
        for i in range(n):
            a, b = i, (i + 1) % n
            q = [ring_o[a], ring_i[a], ring_i[b], ring_o[b]] if s > 0 else [ring_o[b], ring_i[b], ring_i[a], ring_o[a]]
            edges.append(bm.faces.new(q))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        uv = bm.loops.layers.uv.verify()
        for f in bm.faces:
            for loop in f.loops:
                x, y, z = loop.vert.co
                if f in (f_out, f_in):
                    # u = 0 at the front edge on both sides (the art is mirrored on one side, as on real cabinets):
                    # gen_arcade_art.side_art keeps its sprite in the back half, clear of the profile's cut-outs.
                    loop[uv].uv = ((y - y_min) / (y_max - y_min), z / z_max)
                else:
                    loop[uv].uv = ((loop.vert.co.y + loop.vert.co.z) * 2, x * 20)
        f_out.material_index = 0
        f_in.material_index = 2
        for f in edges:
            f.material_index = 1
        ob = mesh_obj(f'side{s}', bm)
        for m in (art, mold, inner):
            ob.data.materials.append(m)
        b = ob.modifiers.new('Bevel', 'BEVEL')
        b.width, b.segments, b.limit_method = .004, 3, 'ANGLE'


def body(lam, panel, black):
    """The box between the side panels: the same profile extruded over the inner width (closed), with the control panel
    top in the panel colour and the rest in laminate."""
    bm = bmesh.new()
    ring_l = [bm.verts.new((-IN, y, z)) for y, z in PROFILE]
    ring_r = [bm.verts.new((IN, y, z)) for y, z in PROFILE]
    bm.faces.new(list(reversed(ring_l)))
    bm.faces.new(ring_r)
    n = len(PROFILE)
    for i in range(n):
        a, b = i, (i + 1) % n
        f = bm.faces.new([ring_l[a], ring_l[b], ring_r[b], ring_r[a]])
        f.material_index = 1 if PROFILE[a] == (-.47, .97) else 2 if PROFILE[a] in ((-.155, 1.52), (-.28, 1.03)) else 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = mesh_obj('body', bm)
    for m in (lam, panel, black):
        ob.data.materials.append(m)
    finish(ob, lam, .6)
    ob.data.materials.pop(index=3)    # finish() appended lam again
    return ob


def screen_and_bezel(screen, black, glass_rim):
    c, v, n, L = bezel_frame()
    # CRT face: a 24 x 18 grid bulging 9 mm at the centre, 4 mm in front of the bezel plane.
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    nu, nv = 24, 18
    grid = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            a, b = i / nu, j / nv
            bulge = .009 * (1 - (2 * a - 1) ** 2) * (1 - (2 * b - 1) ** 2)
            row.append(bm.verts.new(at(c, v, n, -SCREEN_W / 2 + SCREEN_W * a, -SCREEN_H / 2 + SCREEN_H * b, .004 + bulge)))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for loop, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                # Blender v up; the glTF export flips it, so UE gets v = 0 at the top of the screen.
                loop[uv].uv = (ii / nu, jj / nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = mesh_obj('screen', bm)
    for f in ob.data.polygons:
        f.use_smooth = True
    # Normals must face out (toward the player).
    me = ob.data
    p = me.polygons[0]
    if (p.normal.y * n[0] + p.normal.z * n[1]) < 0:
        me.flip_normals()
    ob.data.materials.append(screen)
    # Bezel frame: four bars 16 mm proud of the bezel around the tube, bevelled, glossy black.
    t, depth = .03, .016
    bars = [(0, SCREEN_H / 2 + t / 2, SCREEN_W + 2 * t, t), (0, -SCREEN_H / 2 - t / 2, SCREEN_W + 2 * t, t),
            (-SCREEN_W / 2 - t / 2, 0, t, SCREEN_H), (SCREEN_W / 2 + t / 2, 0, t, SCREEN_H)]
    tilt = math.atan2(v[0], v[1])     # rotation about X from vertical
    for k, (u0, s0, wu, ws) in enumerate(bars):
        p = at(c, v, n, u0, s0, depth / 2)
        box(f'bezel{k}', (wu, depth, ws), p, glass_rim, rot=(-tilt, 0, 0), bevel=.003)
    return c, v, n


def marquee(lit, black):
    """Marquee: a black frame on the box above the screen with the lit 4:1 artwork panel (0.60 x 0.15 m)."""
    (y0, z0), (y1, z1) = (-.24, 1.56), (-.26, 1.84)
    zc = (z0 + z1) / 2
    yc = y0 + (y1 - y0) * (zc - z0) / (z1 - z0) - .006
    lean = math.atan2(y0 - y1, z1 - z0)
    box('marquee_glass', (.60, .006, .15), (0, yc, zc), lit, rot=(lean, 0, 0), bevel=0)
    pane = bpy.data.objects['marquee_glass']
    me = pane.data
    uvl = me.uv_layers.active
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = ((co.x + .30) / .60, (co.z - (zc - .075)) / .15 if abs(co.z - zc) < .2 else 0)
    for k, (dz, h) in enumerate(((.095, .04), (-.095, .04))):
        box(f'marquee_trim{k}', (.622, .02, h), (0, yc - .004, zc + dz), black, rot=(lean, 0, 0), bevel=.003)


def controls(g, chrome, black, ball_m, button_ms, white):
    """Control panel: joystick with a ball top and a dust washer on the left, three concave buttons in an arc on the
    right, a small 1P start button. The panel top slopes up 17.5 degrees from its front edge."""
    (y0, z0), (y1, z1) = (-.47, .97), (-.28, 1.03)
    slope = math.atan2(z1 - z0, y1 - y0)

    def on_panel(x, f, h=0.0):
        y = y0 + (y1 - y0) * f
        z = z0 + (z1 - z0) * f
        nrm = (-math.sin(slope), math.cos(slope))   # outward normal of the panel top (y, z)
        return (x, y + nrm[0] * h, z + nrm[1] * h)

    tilt = -slope           # pieces stand perpendicular to the panel (rotation_euler uses -tilt)
    jx, jf = -.15, .5
    base = on_panel(jx, jf)
    washer = lathe('washer', [(0, 0), (.03, 0), (.03, .002), (0, .003)], (0, 0, 0), black, sides=28)
    shaft = lathe('shaft', [(0, 0), (.0055, 0), (.0055, .07), (0, .07)], (0, 0, 0), chrome, sides=16)
    ball = lathe('balltop', [(0, -.017)] + [(.018 * math.sin(math.pi * k / 12), -.018 * math.cos(math.pi * k / 12)) for k in range(1, 12)] + [(0, .018)],
                 (0, 0, .085), ball_m, sides=24)
    for ob in (washer, shaft, ball):
        ob.rotation_euler = (-tilt, 0, 0)
        ob.location = base
        for p in ob.data.polygons:
            p.use_smooth = True
    cap = [(0, .008), (.012, .010), (.0155, .012), (.0165, .012), (.0165, 0), (0, 0)]
    for k, (bx, bf) in enumerate(((-.02, .42), (.04, .55), (.10, .62))):
        ob = lathe(f'button{k}', list(reversed(cap)), (0, 0, 0), button_ms[k], sides=24)
        ob.rotation_euler = (-tilt, 0, 0)
        ob.location = on_panel(bx, bf)
        for p in ob.data.polygons:
            p.use_smooth = True
    st = lathe('start', [(0, 0), (.009, 0), (.009, .006), (0, .007)], (0, 0, 0), white, sides=20)
    st.rotation_euler = (-tilt, 0, 0)
    st.location = on_panel(.2, .8)


def coin_door(steel, black, coin_lit):
    """Coin door on the lower front: steel plate with two lit coin slots and their return buttons, a lock."""
    y = -.33 - .004
    box('coin_plate', (.26, .008, .30), (0, y, .58), steel, bevel=.003)
    for k, x in enumerate((-.06, .06)):
        box(f'coin_slot{k}', (.038, .006, .06), (x, y - .006, .64), coin_lit, bevel=.002)
        box(f'coin_return{k}', (.035, .008, .025), (x, y - .006, .565), black, bevel=.003)
    lathe('coin_lock', [(0, 0), (.009, 0), (.009, .008), (0, .009)], (0, 0, 0), steel, sides=16)
    lk = bpy.data.objects['coin_lock']
    lk.rotation_euler = (math.radians(90), 0, 0)
    lk.location = (0, y - .004, .47)
    # Kick plate and a speaker grille under the marquee.
    box('kick', (W - .004, .006, .09), (0, -.333, .045), black, bevel=.002)


def build(slug):
    g = GAMES[slug]
    k = g['key']
    side = image_mat('side_art', ART / f'T_Arc_{k}_Side.png', .35)
    mold = plain('t_molding', g['mold'], .3)
    lam = plain('laminate', (.02, .02, .022), .45)
    panel = plain('control_panel', g['panel'], .35)
    black = plain('black_gloss', (.01, .01, .012), .2)
    rim = plain('bezel', (.006, .006, .008), .12)
    screen = image_mat('screen', ART / f'T_Arc_{k}_Title.png', .1, emit=1.5)
    lit = image_mat('marquee_lit', ART / f'T_Arc_{k}_Marquee.png', .3, emit=2.5)
    chrome = plain('chrome', (.9, .91, .93), .12, metal=1.0)
    steel = plain('steel', (.55, .56, .58), .35, metal=1.0)
    ball_m = plain('ball', g['ball'], .25)
    buttons = [plain(f'button{i}', c, .3) for i, c in enumerate(g['buttons'])]
    white = plain('start', (.95, .95, .95), .3)
    coin = plain('coin_lit', (.95, .1, .05), .4, emit=4.0)
    side_panels(side, mold, lam)
    body(lam, panel, black)
    screen_and_bezel(screen, black, rim)
    marquee(lit, black)
    controls(g, chrome, black, ball_m, buttons, white)
    coin_door(steel, black, coin)
    export(slug, g['name'])
    c, v, n, L = bezel_frame()
    print(f'{slug}: screen centre UE cm (0, {-(c[0] + n[0] * .004) * 100:.2f}, {(c[1] + n[1] * .004) * 100:.2f}) normal UE (0, {-n[0]:.4f}, {n[1]:.4f})')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a in GAMES]
    for s in args or GAMES:
        reset()
        build(s)
        print('built', s)
