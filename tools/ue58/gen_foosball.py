"""Playable foosball (pebolim) for the Grand Hotel game room (CHECKLIST 5.4 "Pebolim com controle real (girar as
barras)"): the cabinet without rods, one mesh per rod (chrome rod, rubber grip, bumpers and its players) and the ball,
so UMareFoosball (Source/MareAlta/MareFoosball.cpp) slides and turns every rod and rolls the ball.

Real metres. Cabinet: 1.40 x 0.75 m, base at z=0, playfield surface at FIELD (0.76 m), inner field 1.35 x 0.70 m,
goal mouths 0.22 m. Rods: pivot on the rod axis at the middle of the field (the axis is Blender Y, z=0 on the axis),
handle on Blender +Y (arrives as UE -Y: the player's side; the guest's rods are turned 180 degrees in yaw). Players hang
from the rod: the foot block's bottom is ROD_H - 0.002 m below the axis (2 mm above the playfield at rest).
Keep FIELD, ROD_H, the men's offsets and the rod travel in sync with MareFoosball.h (namespace MareFB).
  mare_foosball_body          cabinet, playfield, goals with ball trays, corner ramps, bearings, score beads, legs
  mare_foosball_rod_<n>_<team> rod with n players (n = 1, 2, 3, 5; team = coral (player) or mar (guest))
  mare_foosball_ball          35 mm ball
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_foosball.py [slug ...]
Textures: Poly Haven CC0 (teak_veneer, metal_plate); the playfield print is drawn here.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402
import random  # noqa: E402
from gen_custom_furniture import OUT, box, export, finish, lathe, material, mesh_obj, reset, tube  # noqa: E402

L, W, T = 1.40, .75, .025          # cabinet outer length, width, wall thickness
FIELD = .76                        # playfield surface
ROD_H = .105                       # rod axis above the playfield
GOAL = .22                         # goal mouth width
BALL_R = .0175
MEN = {1: [0.0], 2: [-.12, .12], 3: [-.185, 0.0, .185], 5: [-.24, -.12, 0.0, .12, .24]}
TRAVEL = {1: .10, 2: .20, 3: .125, 5: .08}
TEAM = {'coral': (.86, .26, .12), 'mar': (.06, .2, .55)}
SHORTS = {'coral': (.95, .94, .9), 'mar': (.95, .94, .9)}
SKIN = [(.80, .58, .44), (.55, .36, .25), (.92, .74, .6), (.38, .24, .16)]


def plain(name, rgb, rough=.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m


def textured(name, slug, tint, rough, out, metal=0.0):
    m = material(name, slug, tint, rough, out)
    m.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = metal
    return m


def image_material(name, path, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(path))
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    return m


def folder(slug):
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    return out


def ellipsoid(name, r, loc, mat, seg=20, rings=12):
    """Sphere scaled to the radii r = (rx, ry, rz)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in bm.verts:
        v.co.x = v.co.x * r[0] + loc[0]
        v.co.y = v.co.y * r[1] + loc[1]
        v.co.z = v.co.z * r[2] + loc[2]
    return finish(mesh_obj(name, bm), mat, .05)


def scaled_lathe(name, profile, loc, mat, sy=1.0, sx=1.0, sides=24):
    """Turned piece around Z (radius, z), squashed into an ellipse: sy across the rod (shoulders), sx along the table."""
    ob = lathe(name, profile, (0, 0, 0), mat, sides=sides, uv=.05)
    for v in ob.data.vertices:
        v.co.x = v.co.x * sx + loc[0]
        v.co.y = v.co.y * sy + loc[1]
        v.co.z += loc[2]
    return ob


def playfield_texture(out):
    """Printed playfield: green stripes, white lines, centre circle, goal areas and the spots (2048 x 1024)."""
    Wp, Hp = 2048, 1024
    img = Image.new('RGB', (Wp, Hp), (36, 118, 54))
    d = ImageDraw.Draw(img)
    for k in range(0, Wp, 128):
        d.rectangle([k, 0, k + 63, Hp], fill=(40, 128, 58))
    m = 22
    white = (236, 238, 230)
    d.rectangle([m, m, Wp - m, Hp - m], outline=white, width=9)
    d.line([Wp // 2, m, Wp // 2, Hp - m], fill=white, width=9)
    d.ellipse([Wp // 2 - 150, Hp // 2 - 150, Wp // 2 + 150, Hp // 2 + 150], outline=white, width=9)
    d.ellipse([Wp // 2 - 12, Hp // 2 - 12, Wp // 2 + 12, Hp // 2 + 12], fill=white)
    for x0, x1 in ((m, 300), (Wp - 300, Wp - m)):
        d.rectangle([x0, Hp // 2 - 300, x1, Hp // 2 + 300], outline=white, width=9)
    for x0, x1 in ((m, 120), (Wp - 120, Wp - m)):
        d.rectangle([x0, Hp // 2 - 170, x1, Hp // 2 + 170], outline=white, width=9)
    rnd = random.Random(3)
    px = img.load()
    for _ in range(60000):        # print grain
        x, y = rnd.randrange(Wp), rnd.randrange(Hp)
        r, g, b = px[x, y]
        k = rnd.randint(-10, 10)
        px[x, y] = (max(0, min(255, r + k)), max(0, min(255, g + k)), max(0, min(255, b + k)))
    img = img.filter(ImageFilter.GaussianBlur(.6))
    path = out / 'mare_foosball_playfield_print.png'
    img.save(path)
    return path


def ball_texture(out):
    img = Image.new('RGB', (512, 256), (238, 236, 228))
    rnd = random.Random(5)
    px = img.load()
    for _ in range(20000):
        x, y = rnd.randrange(512), rnd.randrange(256)
        k = rnd.randint(-14, 6)
        r, g, b = px[x, y]
        px[x, y] = (r + k, g + k, b + k)
    img = img.filter(ImageFilter.GaussianBlur(.8))
    path = out / 'mare_foosball_ball_cork.png'
    img.save(path)
    return path


# ---------------------------------------------------------------- cabinet
def body():
    slug = 'mare_foosball_body'
    out = folder(slug)
    wood = textured('wood', 'teak_veneer', (.42, .25, .13), .5, out)
    dark = textured('black', 'metal_plate', (.04, .04, .045), .55, out, metal=.2)
    chrome = plain('chrome', (.9, .91, .93), .12, metal=1.0)     # polished: a scanned plate texture looked marbled
    rubber = plain('rubber', (.03, .03, .03), .85)
    field = image_material('playfield', playfield_texture(out), .55)
    bead_c = plain('bead_coral', TEAM['coral'], .35)
    bead_m = plain('bead_mar', TEAM['mar'], .35)
    wall_h = .2                                     # walls rise 0.20 m above... from the apron to the rim
    z0 = FIELD - .06
    zc = z0 + wall_h / 2
    # Side walls (the rods pass through them).
    for s in (-1, 1):
        box(f'side{s}', (L, T, wall_h), (0, s * (W / 2 - T / 2), zc), wood, bevel=.004, uv=.7)
        box(f'rim{s}', (L + .02, T + .03, .02), (0, s * (W / 2 - T / 2 + .005), z0 + wall_h + .01), wood, bevel=.006, uv=.7)
    # End walls with the goal mouth (blocks beside and above it), the goal box behind and a ball tray under it.
    for s in (-1, 1):
        side_w = (W - GOAL) / 2
        for k in (-1, 1):
            box(f'end{s}{k}', (T, side_w, wall_h), (s * (L / 2 - T / 2), k * (GOAL / 2 + side_w / 2), zc), wood, bevel=.004, uv=.7)
        box(f'lintel{s}', (T, GOAL, wall_h - .075), (s * (L / 2 - T / 2), 0, z0 + .075 + (wall_h - .075) / 2 + .0), wood, bevel=.003, uv=.7)
        box(f'goalbox{s}', (.09, GOAL + .04, .12), (s * (L / 2 + .045), 0, FIELD - .01), dark, bevel=.004)
        box(f'goalmouth{s}', (.004, GOAL - .006, .07), (s * (L / 2 - .001), 0, FIELD + .035), dark, bevel=0)
        # The tray comes out of the apron's end face (at z=0.5 it hung 10 cm under the cabinet, in the air).
        box(f'tray{s}', (.12, .16, .035), (s * (L / 2 + .045), .2 * s, FIELD - .115), dark, bevel=.006)
        box(f'trayball{s}', (.10, .14, .004), (s * (L / 2 + .045), .2 * s, FIELD - .0955), rubber, bevel=0)
        # Score beads: a chrome bar on the end rim with ten beads (five per team, pushed to the ends).
        box(f'rimend{s}', (T + .03, W + .02, .02), (s * (L / 2 - T / 2 + .005), 0, z0 + wall_h + .01), wood, bevel=.006, uv=.7)
        tube(f'scorebar{s}', (s * (L / 2 - .01), -.3, z0 + wall_h + .038), (s * (L / 2 - .01), .3, z0 + wall_h + .038), .003, chrome, sides=12)
        for k in range(5):
            for team, sign, mat in (('c', 1, bead_c), ('m', -1, bead_m)):
                y = sign * (.28 - k * .028)
                ellipsoid(f'bead{s}{team}{k}', (.011, .012, .011), (s * (L / 2 - .01), y, z0 + wall_h + .038), mat, seg=16, rings=8)
    # Playfield board, the apron under it and four corner ramps (the ball never stops in a corner).
    box('playfield', (L - 2 * T, W - 2 * T, .02), (0, 0, FIELD - .01), field, bevel=0, uv=10.0)
    pf = bpy.data.objects['playfield']
    # Planar UV over the whole field so the print fits once.
    me = pf.data
    uv = me.uv_layers.active
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co.x + (L - 2 * T) / 2) / (L - 2 * T), (co.y + (W - 2 * T) / 2) / (W - 2 * T))
    box('apron', (L, W, .1), (0, 0, FIELD - .11), wood, bevel=.006, uv=.7)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm = bmesh.new()
            cx, cy = sx * (L / 2 - T), sy * (W / 2 - T)
            a = bm.verts.new((cx, cy, FIELD))
            b = bm.verts.new((cx - sx * .05, cy, FIELD))
            c = bm.verts.new((cx, cy - sy * .05, FIELD))
            d = bm.verts.new((cx, cy, FIELD + .03))
            for f in ((a, c, b), (a, b, d), (a, d, c), (b, c, d)):
                bm.faces.new(f)
            finish(mesh_obj(f'ramp{sx}{sy}', bm), dark, .2, smooth=False)
    # Bearings where each rod passes the side walls (8 rods, both walls).
    for i in range(8):
        x = -.6125 + i * .175
        for s in (-1, 1):
            ob = lathe(f'bearing{i}{s}', [(0, -.006), (.017, -.006), (.019, -.002), (.019, .006), (0, .006)], (0, 0, 0), chrome, sides=24)
            ob.rotation_euler = (math.radians(90), 0, 0)
            ob.location = (x, s * (W / 2 + .004), FIELD + ROD_H)
    # Legs (tapered, with levelling feet), stretchers and a cross bar.
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (L / 2 - .09), sy * (W / 2 - .09)
            box(f'leg{sx}{sy}', (.075, .075, FIELD - .16), (x, y, .04 + (FIELD - .16) / 2), wood, bevel=.006, uv=.7)
            lathe(f'foot{sx}{sy}', [(0, 0), (.035, 0), (.035, .015), (.012, .022), (.01, .04), (0, .04)], (x, y, 0), rubber, sides=20)
        box(f'stretch{sx}', (.05, W - .2, .06), (sx * (L / 2 - .09), 0, .2), wood, bevel=.005, uv=.7)
    box('crossbar', (L - .22, .05, .06), (0, 0, .2), wood, bevel=.005, uv=.7)
    export(slug, 'Mesa de pebolim (gabinete, campo, gols, placar de contas)')


# ---------------------------------------------------------------- rods and players
def man(prefix, x, y, jersey, shorts, skin, hair, boots, sock):
    """One player hanging from the rod axis (z=0), facing +X (the attack). Foot bottom at -(ROD_H - 0.002)."""
    fb = -(ROD_H - .002)
    parts = []
    parts.append(ellipsoid(f'{prefix}_head', (.0125, .0118, .0138), (x + .001, y, .036), skin, seg=20, rings=12))
    parts.append(ellipsoid(f'{prefix}_hair', (.0128, .0122, .009), (x - .0015, y, .043), hair, seg=20, rings=10))
    parts.append(scaled_lathe(f'{prefix}_neck', [(0, .016), (.006, .016), (.006, .026), (0, .026)], (x, y, 0), skin))
    # Torso: chest wider across the rod (shoulders), waist narrower; the rod passes through the chest.
    parts.append(scaled_lathe(f'{prefix}_torso', [(0, -.034), (.0135, -.034), (.0145, -.02), (.0155, -.004), (.017, .008), (.0165, .015),
                                                  (.012, .019), (0, .02)], (x, y, 0), jersey, sy=1.35, sx=.92))
    parts.append(scaled_lathe(f'{prefix}_shorts', [(0, -.052), (.0138, -.052), (.0148, -.044), (.0145, -.034), (0, -.032)], (x, y, 0), shorts, sy=1.3, sx=.92))
    for s in (-1, 1):
        # Arms hang beside the body, slightly forward; hands at the hips.
        parts.append(tube(f'{prefix}_arm{s}', (x, y + s * .0215, .011), (x + .004, y + s * .0235, -.016), .0052, jersey, sides=10))
        parts.append(tube(f'{prefix}_fore{s}', (x + .004, y + s * .0235, -.016), (x + .007, y + s * .0225, -.034), .0045, skin, sides=10))
        parts.append(ellipsoid(f'{prefix}_hand{s}', (.0048, .004, .0055), (x + .0075, y + s * .0222, -.038), skin, seg=10, rings=6))
        # Legs to the foot block, socks in the team colour.
        parts.append(tube(f'{prefix}_thigh{s}', (x, y + s * .0075, -.05), (x + .002, y + s * .0078, -.072), .0068, skin, sides=12))
        parts.append(tube(f'{prefix}_sock{s}', (x + .002, y + s * .0078, -.072), (x + .003, y + s * .008, fb + .016), .0058, sock, sides=12))
    # The kicking block (both boots moulded together, toe forward), as on real foosball men.
    parts.append(box(f'{prefix}_boots', (.034, .03, .017), (x + .006, y, fb + .0085), boots, bevel=.005, uv=.1))
    parts.append(box(f'{prefix}_studs', (.03, .026, .002), (x + .006, y, fb + .001), boots, bevel=.0008, uv=.1))
    return parts


def rod(n, team):
    slug = f'mare_foosball_rod_{n}_{team}'
    out = folder(slug)
    chrome = plain('chrome', (.9, .91, .93), .1, metal=1.0)
    grip = plain('grip', (.025, .025, .025), .82)
    bump = plain('bumper', (.04, .04, .04), .7)
    jersey = plain('jersey', TEAM[team], .38)
    sock = plain('sock', TEAM[team], .55)
    shorts = plain('shorts', SHORTS[team], .4)
    boots = plain('boots', (.03, .03, .03), .45)
    hair = plain('hair', (.06, .04, .03), .6)
    skins = [plain(f'skin{i}', c, .45) for i, c in enumerate(SKIN)]
    travel = TRAVEL[n]
    inner = W / 2 - T
    # Handle side (+Y): the rod leaves the wall, passes the travel and ends in the grip.
    y_hand0 = W / 2 + travel + .03
    y_end = y_hand0 + .13
    y_far = -(W / 2 + travel + .025)
    tube('rod', (0, y_far, 0), (0, y_end - .01, 0), .008, chrome, sides=20)
    ob = lathe('grip', [(0, 0), (.015, .002), (.0175, .012), (.0168, .03), (.0178, .05), (.0168, .07), (.0178, .09), (.0172, .112), (.019, .122),
                        (.0175, .13), (0, .13)], (0, 0, 0), grip, sides=28)
    ob.rotation_euler = (math.radians(-90), 0, 0)
    ob.location = (0, y_hand0, 0)
    lathe('endcap', [(0, -.002), (.0082, -.002), (.0082, .004), (0, .006)], (0, 0, 0), chrome, sides=16).location = (0, 0, 0)
    bpy.data.objects['endcap'].rotation_euler = (math.radians(90), 0, 0)
    bpy.data.objects['endcap'].location = (0, y_far, 0)
    # Rubber bumpers inside the field: they touch the walls at full travel.
    men = MEN[n]
    for s in (-1, 1):
        yb = s * (inner - travel) - s * .008
        ob = lathe(f'bumper{s}', [(0, -.008), (.0125, -.008), (.0135, -.004), (.0135, .004), (.0125, .008), (0, .008)], (0, 0, 0), bump, sides=20)
        ob.rotation_euler = (math.radians(90), 0, 0)
        ob.location = (0, yb, 0)
    for k, y in enumerate(men):
        man(f'm{k}', 0, y, jersey, shorts, skins[(k + n + (0 if team == 'coral' else 2)) % len(skins)], hair, boots, sock)
    # Every object in its final place: bake transforms so the rod pivot stays on the axis.
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects['rod']
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    export(slug, f'Barra de pebolim com {n} jogador(es), time {team}')


def ball():
    slug = 'mare_foosball_ball'
    out = folder(slug)
    m = image_material('cork', ball_texture(out), .55)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=BALL_R)
    ob = mesh_obj('ball', bm)
    ob.data.materials.append(m)
    me = ob.data
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (.5 + math.atan2(co.y, co.x) / (2 * math.pi), .5 + math.asin(max(-1, min(1, co.z / BALL_R))) / math.pi)
    export(slug, 'Bola de pebolim')


BUILD = {'mare_foosball_body': body, 'mare_foosball_ball': ball}
for _n in (1, 2, 3, 5):
    for _t in ('coral', 'mar'):
        BUILD[f'mare_foosball_rod_{_n}_{_t}'] = (lambda n=_n, t=_t: rod(n, t))

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a in BUILD]
    for slug in args or BUILD:
        reset()
        BUILD[slug]()
        print('built', slug)
