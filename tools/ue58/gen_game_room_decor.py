"""Grand Hotel game room decoration (CHECKLIST 5.4 "Decoração: piso, parede com papel ou ripado, iluminação, quadros e
balcão de fichas"), modelled with bpy where Poly Haven has nothing (dartboard, clock, frames, cash register and the
chalkboard come from Poly Haven, CC0; placed by Content/Python/mare_game_room.py).

The game room is the middle of the hotel's ground-floor hall (x -2500..-1700 world cm, north wall face y 6890, floor 45,
ceiling 462 between the ribs). Every model: real metres, base at z=0 (the lamp hangs from its canopy at z=0), centred
on x. Wall-side models have their back at Blender y=0 and their front at +Y (Blender +Y arrives as UE -Y, so with
yaw 0 they face south, into the room).
  mare_gameroom_wall      accent wall 7.8 x 3.6 m: petrol-blue plaster, walnut slats (ripado) on felt at both ends,
                          walnut skirting and cap with a warm LED strip under it (100 mm deep: covers the chair rail)
  mare_gameroom_sign      "SALÃO DE JOGOS" channel letters (warm light) on standoffs
  mare_gameroom_sign_fichas  "FICHAS" in the same letters
  mare_billiard_lamp      three dark-green enamel domes on a brass bar, two steel cables to ceiling canopies
  mare_token_counter      1.3 m token counter: walnut slatted front, quartz top, back shelf, tray of brass tokens
  mare_cue_rack           free-standing walnut cue rack with six cues and chalk
  mare_gameroom_rug       4.4 x 3.4 m wool herringbone rug with a cream border (under the pool table)
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_game_room_decor.py [slug ...]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from gen_custom_furniture import OUT, box, export, finish, lathe, material, mesh_obj, reset, tube  # noqa: E402


def mats(slug):
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    return out


def plain(name, rgb, rough=.5, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    return m


def textured(name, slug, tint, rough, out, metal=0.0):
    m = material(name, slug, tint, rough, out)
    m.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value = metal
    return m


def walnut(out):
    return textured('walnut', 'teak_veneer', (.36, .22, .13), .55, out)


def shell(name, outer, thick, loc, mat, sides=48, uv=.3):
    """Turned shell (lamp shade): outer profile (radius, z) from the top down, the inside offset by thick, closed at
    the rim with a rounded lip; open on top around the stem."""
    inner = [(max(r - thick, .002), z - (thick if i == 0 else 0)) for i, (r, z) in enumerate(outer)]
    prof = outer + [(outer[-1][0] + thick * .4, outer[-1][1] + thick * .5)] + list(reversed(inner))
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        rings.append([bm.verts.new((loc[0] + r * math.cos(2 * math.pi * i / sides), loc[1] + r * math.sin(2 * math.pi * i / sides), loc[2] + z))
                      for i in range(sides)])
    for r0, r1 in zip(rings, rings[1:] + [rings[0]]):
        for i in range(sides):
            bm.faces.new((r0[i], r0[(i + 1) % sides], r1[(i + 1) % sides], r1[i]))
    obj = mesh_obj(name, bm)
    return finish(obj, mat, uv)


def letters(name, text, height, depth, loc, mat):
    """Channel letters: the text extruded `depth` metres toward +Y from the back plane y=loc[1], centred on loc[0]."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = text
    cu.size = height / .72          # cap height of the built-in font is ~0.72 of the size
    cu.align_x = 'CENTER'
    cu.extrude = depth / 2
    cu.bevel_depth = .0015
    cu.bevel_resolution = 2
    cu.resolution_u = 6
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    # Text lies in XY facing +Z: Rx(+90) stands it up facing -Y (readable from -Y), Rz(180) turns it to face +Y and still read
    # left to right from the front.
    ob.rotation_euler = (math.radians(90), 0, math.radians(180))
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.active_object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    me = ob.data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    cx, y0, z0 = (min(xs) + max(xs)) / 2, min(ys), min(zs)
    for v in me.vertices:
        v.co.x += loc[0] - cx
        v.co.y += loc[1] - y0
        v.co.z += loc[2] - z0
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = False
    ob.select_set(False)
    return ob, (min(xs) - cx + loc[0], max(xs) - cx + loc[0]), max(zs) - z0


# ---------------------------------------------------------------- models
def gameroom_wall():
    slug = 'mare_gameroom_wall'
    out = mats(slug)
    # 10 cm deep: the lobby's chair rail (part of the tower mesh, z 106-115) stands 8 cm off the wall, and with 5 cm it
    # crossed the plaster and the slats (06/11 photo).
    W, H, D = 7.8, 3.6, .10
    plaster = textured('plaster', 'painted_plaster_wall', (.075, .2, .23), .85, out)
    wood = walnut(out)
    felt = textured('felt', 'velour_velvet', (.03, .035, .04), .95, out)
    led = plain('led_glow', (1, .86, .62), .4, emit=(1, .78, .5), strength=6.0)
    box('base', (W, D, H), (0, D / 2, H / 2), plaster, bevel=.004, uv=1.2)
    band = 1.6
    sl_w, sl_d, gap = .04, .03, .022
    for side in (-1, 1):
        cx = side * (W / 2 - band / 2)
        box(f'felt{side}', (band, .012, H - .16), (cx, D + .006, .1 + (H - .16) / 2), felt, bevel=.002, uv=.6)
        n = int((band - .02) / (sl_w + gap))
        x0 = cx - (n - 1) * (sl_w + gap) / 2
        for i in range(n):
            box(f'slat{side}_{i}', (sl_w, sl_d, H - .16), (x0 + i * (sl_w + gap), D + .012 + sl_d / 2, .1 + (H - .16) / 2), wood, bevel=.003, uv=.9)
    box('skirting', (W + .02, D + .06, .1), (0, (D + .06) / 2, .05), wood, bevel=.004, uv=.9)
    box('cap', (W + .02, D + .07, .06), (0, (D + .07) / 2, H - .03), wood, bevel=.004, uv=.9)
    box('led', (W - .1, .012, .008), (0, D + .055, H - .064), led, bevel=.001)
    export(slug, 'Parede do salão de jogos (ripado)')


def sign(slug='mare_gameroom_sign', text='SALÃO DE JOGOS', height=.30, desc='Letreiro do salão de jogos'):
    out = mats(slug)
    face = plain('letters_glow', (1, .93, .8), .35, emit=(1, .8, .55), strength=12.0)
    side = plain('letters_side', (.06, .05, .045), .45, metal=.6)
    ob, (x0, x1), h = letters('letters', text, height, .03, (0, .025, 0), face)
    # The sides of the channel letters are dark metal, the face lights: a second slot by face normal.
    ob.data.materials.append(side)
    for p in ob.data.polygons:
        p.material_index = 0 if p.normal.y > .7 else 1
    # Standoffs behind each end and the middle (the letters stand 25 mm off the wall).
    steel = plain('standoff', (.6, .6, .62), .3, metal=1.0)
    for x in (x0 + .05, (x0 + x1) / 2, x1 - .05):
        tube(f'standoff{x:.2f}', (x, 0, h * .5), (x, .026, h * .5), .006, steel, sides=16)
    export(slug, desc)


def billiard_lamp():
    slug = 'mare_billiard_lamp'
    out = mats(slug)
    brass = textured('brass', 'metal_plate', (.78, .58, .3), .3, out, metal=1.0)
    enamel = textured('enamel', 'metal_plate', (.04, .16, .1), .28, out, metal=.3)
    lining = plain('lining', (.92, .9, .86), .5)
    steel = plain('cable', (.55, .55, .57), .35, metal=1.0)
    bulb = plain('bulb_glow', (1, .95, .85), .2, emit=(1, .85, .6), strength=3.0)
    drop = 2.05
    for x in (-.6, .6):
        lathe(f'canopy{x}', [(.0, 0), (.07, 0), (.07, -.006), (.06, -.022), (.012, -.026), (.0, -.026)], (x, 0, 0), brass, sides=48)
        tube(f'cable{x}', (x, 0, -.026), (x, 0, -drop + .02), .0016, steel, sides=8)
        lathe(f'grip{x}', [(.0, 0), (.008, 0), (.008, -.03), (.0, -.03)], (x, 0, -drop + .045), brass, sides=24)
    box('bar', (1.5, .036, .026), (0, 0, -drop - .013), brass, bevel=.006, uv=.5)
    for cap in (-1, 1):
        lathe(f'endcap{cap}', [(.0, 0), (.021, 0), (.021, -.012), (.0, -.012)], (cap * .755, 0, -drop + .006), brass, sides=24)
    for i, x in enumerate((-.55, 0, .55)):
        top = -drop - .026
        lathe(f'stem{i}', [(.0, 0), (.011, 0), (.011, -.05), (.0, -.05)], (x, 0, top), brass, sides=24)
        lathe(f'collar{i}', [(.0, 0), (.03, 0), (.034, -.02), (.0, -.02)], (x, 0, top - .05), brass, sides=48)
        st = top - .07
        dome = [(.032, 0), (.07, -.012), (.11, -.04), (.145, -.08), (.168, -.125), (.18, -.17), (.184, -.2)]
        shell(f'shade{i}', dome, .004, (x, 0, st), enamel, sides=64)
        shell(f'lining{i}', [(r - .0045, z - .002) for r, z in dome[:-1]] + [(dome[-1][0] - .0045, dome[-1][1] + .002)], .002, (x, 0, st), lining, sides=64)
        lathe(f'socket{i}', [(.0, 0), (.02, 0), (.02, -.05), (.016, -.055), (.0, -.055)], (x, 0, st - .005), brass, sides=32)
        lathe(f'bulb{i}', [(.0, 0), (.014, 0), (.016, -.012), (.03, -.04), (.036, -.065), (.03, -.09), (.016, -.105), (.0, -.11)], (x, 0, st - .06), bulb, sides=40)
    export(slug, 'Luminária da sinuca (3 cúpulas)')


def token_counter():
    slug = 'mare_token_counter'
    out = mats(slug)
    wood = walnut(out)
    quartz = textured('quartz', 'marble_01', (.86, .85, .82), .25, out)
    black = textured('black', 'metal_plate', (.035, .035, .035), .5, out, metal=.4)
    brass = textured('brass', 'metal_plate', (.8, .6, .28), .3, out, metal=1.0)
    W, D, H = 1.3, .55, 1.05
    box('plinth', (W - .1, D - .1, .1), (0, D / 2, .05), black, bevel=.003)
    box('back', (W - .04, .02, H - .13), (0, .01 + .03, .1 + (H - .13) / 2), wood, bevel=.003, uv=.9)
    for s in (-1, 1):
        box(f'side{s}', (.03, D, H - .1 - .03), (s * (W / 2 - .03), D / 2, .1 + (H - .13) / 2), wood, bevel=.004, uv=.9)
    box('front', (W - .06, .02, H - .13), (0, D - .05, .1 + (H - .13) / 2), wood, bevel=.003, uv=.9)
    n = 19
    for i in range(n):
        x = -(W - .1) / 2 + .02 + i * ((W - .14) / (n - 1))
        box(f'slat{i}', (.035, .025, H - .17), (x, D - .028, .12 + (H - .17) / 2), wood, bevel=.004, uv=.9)
    box('shelf', (W - .1, D - .12, .025), (0, D / 2 - .02, .72), wood, bevel=.003, uv=.9)
    box('top', (W + .06, D + .06, .03), (0, D / 2 + .01, H - .015), quartz, bevel=.006, uv=.8)
    # Tray of brass tokens on the top, to the right of the cash register.
    ty = D / 2 + .08
    box('tray', (.26, .18, .02), (.4, ty, H + .01), wood, bevel=.004, uv=.5)
    import random
    rnd = random.Random(7)
    k = 0
    for row in range(4):
        for col in range(6):
            for h in range(rnd.randint(1, 4)):
                cx, cy = .4 - .1 + col * .04 + rnd.uniform(-.003, .003), ty - .06 + row * .04 + rnd.uniform(-.003, .003)
                lathe(f'token{k}', [(.0, 0), (.0145, 0), (.0155, .0012), (.0155, .0022), (.0145, .0034), (.0, .0034)], (cx, cy, H + .02 + h * .0034), brass, sides=28)
                k += 1
    export(slug, 'Balcão de fichas do salão de jogos')


def cue_rack():
    slug = 'mare_cue_rack'
    out = mats(slug)
    wood = walnut(out)
    maple = textured('maple', 'teak_veneer', (.78, .58, .36), .45, out)
    ebony = textured('ebony', 'teak_veneer', (.07, .045, .035), .35, out)
    white = plain('ferrule', (.92, .9, .85), .3)
    tip = plain('tip', (.12, .2, .45), .8)
    chalk = plain('chalk', (.1, .3, .7), .9)
    box('base', (.6, .32, .05), (0, .16, .025), wood, bevel=.006, uv=.8)
    box('backboard', (.52, .03, 1.5), (0, .015, .05 + .75), wood, bevel=.005, uv=.9)
    box('crown', (.6, .07, .05), (0, .035, 1.575), wood, bevel=.006, uv=.8)
    box('cup_rail', (.5, .12, .07), (0, .11, .085), wood, bevel=.006, uv=.8)
    box('clip_rail', (.5, .07, .04), (0, .065, 1.2), wood, bevel=.005, uv=.8)
    box('chalk_shelf', (.3, .08, .02), (0, .07, .62), wood, bevel=.004, uv=.6)
    for i, x in enumerate((-.06, .06)):
        box(f'chalk{i}', (.022, .022, .022), (x, .08, .641), chalk, bevel=.003)
    for i in range(6):
        x = -.2 + i * .08
        a, b = (x, .115, .07), (x, .07, 1.53)
        L = math.dist(a, b)
        prof = [(.0, 0), (.0155, 0), (.0152, .02), (.0148, .45), (.0135, .7), (.011, 1.0), (.0075, L - .03), (.0072, L - .03),
                (.0072, L - .01), (.0068, L - .01), (.0068, L), (.0, L)]
        dirn = [b[k] - a[k] for k in range(3)]
        tilt = math.atan2(dirn[1], dirn[2])
        parts = [('butt', ebony, 0, 6), ('shaft', maple, 5, 9), ('ferrule', white, 8, 10), ('tip', tip, 9, 12)]
        for nm, mat, i0, i1 in parts:
            seg = prof[i0:i1]
            if seg[0][0] > 0:
                seg = [(0.0, seg[0][1])] + seg
            if seg[-1][0] > 0:
                seg = seg + [(0.0, seg[-1][1])]
            ob = lathe(f'cue{i}_{nm}', seg, (0, 0, 0), mat, sides=24)
            ob.rotation_euler = (-tilt, 0, 0)
            ob.location = a
    export(slug, 'Porta-tacos de sinuca')


def gameroom_rug():
    slug = 'mare_gameroom_rug'
    out = mats(slug)
    field = textured('field', 'poly_wool_herringbone', (.07, .22, .2), .95, out)
    border = textured('border', 'poly_wool_herringbone', (.8, .73, .58), .95, out)
    W, L, T, B = 3.4, 4.4, .009, .16
    box('border', (L, W, T), (0, 0, T / 2), border, bevel=.004, uv=.35)
    box('field', (L - 2 * B, W - 2 * B, T), (0, 0, T / 2 + .0008), field, bevel=.003, uv=.35)
    box('line', (L - 2 * B - .1, W - 2 * B - .1, T), (0, 0, T / 2 + .0004), border, bevel=.002, uv=.35)
    box('inner', (L - 2 * B - .14, W - 2 * B - .14, T), (0, 0, T / 2 + .0012), field, bevel=.002, uv=.35)
    export(slug, 'Tapete do salão de jogos')


BUILD = {
    'mare_gameroom_wall': gameroom_wall,
    'mare_gameroom_sign': sign,
    'mare_gameroom_sign_fichas': lambda: sign('mare_gameroom_sign_fichas', 'FICHAS', .16, 'Letreiro FICHAS'),
    'mare_billiard_lamp': billiard_lamp,
    'mare_token_counter': token_counter,
    'mare_cue_rack': cue_rack,
    'mare_gameroom_rug': gameroom_rug,
}

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a in BUILD]
    for slug in args or BUILD:
        reset()
        BUILD[slug]()
        print('built', slug)
