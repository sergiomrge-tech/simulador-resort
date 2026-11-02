"""Pousada bungalow and its room furniture, modelled with bpy.

mare_bungalow: enterable room 4.8 x 4.0 m (floor 0.45 m above the ground, 2.7 m walls), front deck with
steps facing Blender -Y (UE +Y), door opening, shuttered windows, thatched hip roof, plank ceiling,
built-in wardrobe and two nightstands. Origin: ground level at the centre of the room.
Room tiers: beds (simple, iron, upholstered queen, king, canopy), ceiling fan, wall AC unit, woven rug.
Textures: CC0 Poly Haven photo scans. Run:
  blender -b --factory-startup --python tools/ue58/gen_rooms.py -- [slug ...]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from gen_custom_furniture import OUT, bed_core, box, cushion, drape, export, finish, lathe, material, mesh_obj, reset, tube  # noqa: E402
ART = Path('D:/Assets/Canva/beach_art/beach_watercolor.png')
from gen_landmarks import hip_roof  # noqa: E402

FLOOR = .45
WALL = 2.7
W, D, T = 4.8, 4.0, .15


def wall_with_holes(name, length, height, thickness, holes, mat, axis='x', at=(0, 0, 0)):
    """Wall slab along X (or Y) with rectangular openings [(centre, bottom, width, height)]."""
    bm = bmesh.new()
    xs = sorted({0, length} | {h[0] - h[2] / 2 + length / 2 for h in holes} | {h[0] + h[2] / 2 + length / 2 for h in holes})
    for x0, x1 in zip(xs, xs[1:]):
        cx = (x0 + x1) / 2 - length / 2
        cuts = [h for h in holes if abs(h[0] - cx) < h[2] / 2]
        spans = [(0, height)]
        for c, b, w, h in cuts:
            spans = [s for sp in spans for s in ((sp[0], min(sp[1], b)), (max(sp[0], b + h), sp[1])) if s[1] - s[0] > 1e-3]
        for z0, z1 in spans:
            res = bmesh.ops.create_cube(bm, size=1.0)
            for v in res['verts']:
                v.co.x = v.co.x * (x1 - x0) + cx
                v.co.y *= thickness
                v.co.z = v.co.z * (z1 - z0) + (z0 + z1) / 2
    if axis == 'y':
        for v in bm.verts:
            v.co.x, v.co.y = -v.co.y, v.co.x
    for v in bm.verts:
        v.co.x += at[0]
        v.co.y += at[1]
        v.co.z += at[2]
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    obj = mesh_obj(name, bm)
    return finish(obj, mat, 1.0, bevel=.01, seg=2, smooth=False)


def bungalow():
    reset()
    slug = 'mare_bungalow'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    plaster = material('Plaster', 'painted_plaster_wall', (.94, .91, .84), rough=.85, out=out)
    stone = material('Stone', 'plaster_stone_wall_01', None, rough=.9)
    planks = material('Planks', 'oak_wood_planks', None, rough=.6)
    trim = material('Trim', 'distressed_painted_planks', (.18, .44, .46), rough=.7, out=out)
    thatch = material('Thatch', 'thatch_roof_angled', (.74, .58, .36), rough=.95, out=out)
    cream = material('Cream', 'distressed_painted_planks', (.92, .87, .76), rough=.7, out=out)
    glass = bpy.data.materials.new('Glass')
    glass.use_nodes = True
    g = glass.node_tree.nodes['Principled BSDF']
    g.inputs['Base Color'].default_value = (.7, .82, .86, 1)
    g.inputs['Roughness'].default_value = .05
    g.inputs['Alpha'].default_value = .2
    deck_d = 1.7
    # Stone plinth under room and deck (reaches below the ground for uneven terrain), plank floors.
    box('plinth', (W + .3, D + deck_d + .3, FLOOR + .5), (0, -deck_d / 2, (FLOOR - .5) / 2), stone, uv=1.5)
    box('floor', (W - .02, D - .02, .04), (0, 0, FLOOR + .02), planks, uv=1.2)
    box('deck', (W, deck_d, .06), (0, -D / 2 - deck_d / 2, FLOOR + .03), planks, uv=1.2)
    for i in range(3):
        box(f'step{i}', (1.4, .32, .15), (0, -D / 2 - deck_d - .16 - .32 * (2 - i), .075 + .15 * i), stone, uv=1)
    # Walls: front with door, sides with a window each, plain back.
    door_w, door_h = 1.0, 2.1
    wall_with_holes('front', W, WALL, T, [(0, 0, door_w, door_h), (-1.55, .9, 1.0, 1.1), (1.55, .9, 1.0, 1.1)], plaster, 'x', (0, -D / 2 + T / 2, FLOOR))
    wall_with_holes('back', W, WALL, T, [], plaster, 'x', (0, D / 2 - T / 2, FLOOR))
    for sx in (-1, 1):
        wall_with_holes(f'side{sx}', D - 2 * T, WALL, T, [(.4, .9, 1.0, 1.1)], plaster, 'y', (sx * (W / 2 - T / 2), 0, FLOOR))
    # Timber trim: corner posts, door and window frames, open shutters.
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f'corner{sx}{sy}', (.16, .16, WALL + .05), (sx * W / 2, sy * D / 2, FLOOR + WALL / 2), trim, uv=1)
    for (cx, cy, rot, w, h, b) in [(0, -D / 2, 0, door_w, door_h, 0), (-1.55, -D / 2, 0, 1.0, 1.1, .9), (1.55, -D / 2, 0, 1.0, 1.1, .9),
                                    (-W / 2, .4, math.pi / 2, 1.0, 1.1, .9), (W / 2, .4, math.pi / 2, 1.0, 1.1, .9)]:
        c, s = math.cos(rot), math.sin(rot)
        for side in (-1, 1):
            dx = side * (w / 2 + .04)
            box(f'jamb{cx}{cy}{side}', (.08, T + .06, h), (cx + dx * c, cy + dx * s, FLOOR + b + h / 2), trim, rot=(0, 0, rot), uv=1)
        box(f'head{cx}{cy}', (w + .24, T + .06, .1), (cx, cy, FLOOR + b + h + .05), trim, rot=(0, 0, rot), uv=1)
        if b > 0:
            box(f'sill{cx}{cy}', (w + .24, T + .14, .06), (cx, cy, FLOOR + b - .03), trim, rot=(0, 0, rot), uv=1)
            box(f'pane{cx}{cy}', (w, .02, h), (cx, cy, FLOOR + b + h / 2), trim, rot=(0, 0, rot), uv=1).data.materials[0] = glass
            out_n = (-s, c) if rot else (0, -1)
            for side in (-1, 1):
                dx = side * (w / 2 + .3)
                box(f'shutter{cx}{cy}{side}', (.48, .04, h), (cx + dx * c + out_n[0] * .12 * (1 if rot == 0 else -cx / abs(cx)), cy + dx * s + out_n[1] * .12, FLOOR + b + h / 2), cream, rot=(0, 0, rot), uv=.8)
    # Plank ceiling, deck railing with posts, a small table and two chairs on the deck.
    box('ceiling', (W - .3, D - .3, .05), (0, 0, FLOOR + WALL - .03), planks, uv=1.2)
    for sx in (-1, 1):
        for y in (-D / 2 - deck_d + .1, -D / 2 - .1):
            tube(f'dpost{sx}{y}', (sx * (W / 2 - .08), y, FLOOR), (sx * (W / 2 - .08), y, FLOOR + WALL + .1), .07, trim, 10)
        tube(f'rail{sx}', (sx * (W / 2 - .08), -D / 2 - deck_d + .1, FLOOR + .9), (sx * (W / 2 - .08), -D / 2 - .1, FLOOR + .9), .035, trim, 8)
        for k in range(6):
            y = -D / 2 - deck_d + .15 + k * (deck_d - .3) / 5
            tube(f'baluster{sx}{k}', (sx * (W / 2 - .08), y, FLOOR), (sx * (W / 2 - .08), y, FLOOR + .9), .02, trim, 6)
    lathe('dtable', [(0, 0), (.22, 0), (.22, .03), (.04, .05), (.04, .68), (.32, .7), (.32, .74), (0, .74)], (1.4, -D / 2 - deck_d / 2, FLOOR + .06), planks, 20)
    for k, x in enumerate((.85, 1.95)):
        box(f'dseat{k}', (.45, .45, .05), (x, -D / 2 - deck_d / 2, FLOOR + .5), planks, uv=.8)
        box(f'dback{k}', (.05, .45, .5), (x + (-.22 if k == 0 else .22), -D / 2 - deck_d / 2, FLOOR + .78), planks, uv=.8)
        for lx in (-.18, .18):
            for ly in (-.18, .18):
                box(f'dleg{k}{lx}{ly}', (.04, .04, .48), (x + lx, -D / 2 - deck_d / 2 + ly, FLOOR + .3), planks, uv=.8)
    # Thatched hip roof over room and deck, with fascia.
    hip_roof('roof', W, D + deck_d, FLOOR + WALL + .02, 1.8, .55, thatch)
    bpy.context.collection.objects['roof'].location.y = -deck_d / 2
    # Built-in wardrobe on the left wall near the door, two nightstands by the bed (bed is a room tier).
    box('wardrobe', (.6, 1.3, 2.1), (-W / 2 + T + .32, -D / 2 + T + 1.05, FLOOR + 1.05), cream, uv=.9)
    for k, y in enumerate((-.33, .33)):
        box(f'wdoor{k}', (.02, .62, 1.9), (-W / 2 + T + .63, -D / 2 + T + 1.05 + y, FLOOR + 1.05), trim, uv=.9)
        lathe(f'knob{k}', [(0, 0), (.02, 0), (.02, .03), (0, .03)], (-W / 2 + T + .65, -D / 2 + T + 1.05 + y * .2, FLOOR + 1.05), planks, 10)
    for sx in (-1, 1):
        box(f'night{sx}', (.46, .4, .55), (sx * 1.35, D / 2 - T - .22, FLOOR + .275), cream, uv=.8)
        box(f'nighttop{sx}', (.5, .44, .03), (sx * 1.35, D / 2 - T - .22, FLOOR + .565), planks, uv=.8)
        lathe(f'lamp{sx}', [(0, 0), (.08, 0), (.05, .03), (.02, .25), (.14, .27), (.1, .45), (0, .45)], (sx * 1.35, D / 2 - T - .22, FLOOR + .58), cream, 20)
    # Interior finish: sage wainscot up to the window sills with a chair rail, exposed ceiling beams,
    # linen curtains on rods at every window and a framed watercolour (Canva) above the bed.
    sage = material('Wainscot', 'distressed_painted_planks', (.60, .70, .60), rough=.7, out=out)
    teak = material('Beams', 'teak_veneer', None, rough=.45)
    linen = material('Curtain', 'rough_linen', (.95, .93, .87), rough=.9, out=out)
    inner_w, inner_d = W - 2 * T, D - 2 * T
    box('wain_back', (inner_w, .02, .9), (0, D / 2 - T - .01, FLOOR + .45), sage, uv=.9)
    box('rail_back', (inner_w, .04, .05), (0, D / 2 - T - .02, FLOOR + .92), teak, uv=.9)
    for sx in (-1, 1):
        box(f'wain_side{sx}', (.02, inner_d, .9), (sx * (W / 2 - T - .01), 0, FLOOR + .45), sage, uv=.9)
        box(f'rail_side{sx}', (.04, inner_d, .05), (sx * (W / 2 - T - .02), 0, FLOOR + .92), teak, uv=.9)
        seg = (inner_w - 1.0) / 2
        box(f'wain_front{sx}', (seg, .02, .9), (sx * (.5 + seg / 2), -D / 2 + T + .01, FLOOR + .45), sage, uv=.9)
        box(f'rail_front{sx}', (seg, .04, .05), (sx * (.5 + seg / 2), -D / 2 + T + .02, FLOOR + .92), teak, uv=.9)
    for i in range(4):
        box(f'beam{i}', (inner_w, .14, .18), (0, -D / 2 + .55 + i * (D - 1.1) / 3, FLOOR + WALL - .14), teak, uv=1)
    for (cx, cy, rot) in [(-1.55, -D / 2 + T + .06, 0), (1.55, -D / 2 + T + .06, 0), (-W / 2 + T + .06, .4, math.pi / 2), (W / 2 - T - .06, .4, math.pi / 2)]:
        c, s = math.cos(rot), math.sin(rot)
        tube(f'crod{cx}{cy}', (cx - .75 * c, cy - .75 * s, FLOOR + 2.15), (cx + .75 * c, cy + .75 * s, FLOOR + 2.15), .012, teak, 8)
        for side in (-1, 1):
            drape(f'curtain{cx}{cy}{side}', .38, 1.55, (cx + side * .58 * c, cy + side * .58 * s, FLOOR + 2.12), rot, linen, folds=5, amp=.025)
    if ART.exists():
        art = bpy.data.materials.new('Painting')
        art.use_nodes = True
        node = art.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(ART))
        art.node_tree.links.new(node.outputs['Color'], art.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        art.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .7
        box('frame', (1.12, .05, .8), (0, D / 2 - T - .03, FLOOR + 1.75), teak, uv=.6)
        bm = bmesh.new()
        v = [bm.verts.new(p) for p in [(-.5, 0, -.34), (.5, 0, -.34), (.5, 0, .34), (-.5, 0, .34)]]
        f = bm.faces.new(v)
        uv = bm.loops.layers.uv.verify()
        for loop, co in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            loop[uv].uv = co
        canvas = mesh_obj('canvas', bm)
        canvas.data.materials.append(art)
        canvas.location = (0, D / 2 - T - .06, FLOOR + 1.75)
    export(slug, 'Bangalô da pousada')


def bed_simple(slug='mare_bed_simple', iron=False):
    reset()
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    wood = material('Wood', 'oak_wood_planks', None, rough=.55)
    metal = material('Iron', 'metal_plate', (.85, .85, .82), rough=.4, out=out)
    linen = material('Linen', 'rough_linen', (.96, .95, .92), rough=.9, out=out)
    duvet = material('Duvet', 'rough_linen', (.55, .70, .78) if iron else (.86, .78, .62), rough=.9, out=out)
    L, Wd = 2.0, 1.45
    box('frame', (Wd + .08, L + .04, .22), (0, 0, .3), wood, uv=1)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f'leg{sx}{sy}', (.07, .07, .3), (sx * (Wd / 2), sy * (L / 2), .15), wood, uv=1)
    if iron:
        for sx in (-1, 1):
            tube(f'hpost{sx}', (sx * Wd / 2, L / 2 + .02, 0), (sx * Wd / 2, L / 2 + .02, 1.25), .025, metal, 10)
            tube(f'fpost{sx}', (sx * Wd / 2, -L / 2 - .02, 0), (sx * Wd / 2, -L / 2 - .02, .85), .025, metal, 10)
        for z in (.8, 1.2):
            tube(f'hbar{z}', (-Wd / 2, L / 2 + .02, z), (Wd / 2, L / 2 + .02, z), .02, metal, 8)
        tube('fbar', (-Wd / 2, -L / 2 - .02, .8), (Wd / 2, -L / 2 - .02, .8), .02, metal, 8)
        for i in range(9):
            x = -Wd / 2 + (i + 1) * Wd / 10
            tube(f'spindle{i}', (x, L / 2 + .02, .8), (x, L / 2 + .02, 1.2), .01, metal, 6)
    else:
        box('headboard', (Wd + .1, .06, .9), (0, L / 2 + .02, .75), wood, uv=1)
        for i in range(6):
            box(f'slat{i}', (.05, .07, .5), (-Wd / 2 + .2 + i * (Wd - .4) / 5, L / 2 - .01, .85), wood, uv=1)
    bed_core(out, L, Wd, .62, duvet, linen, wood)
    export(slug, 'Cama de ferro' if iron else 'Cama de madeira')


def bed_king():
    """Upholstered king bed: the queen model widened, sand linen and a deep-blue throw."""
    import gen_custom_furniture as g
    reset()
    slug = 'mare_bed_king'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    fabric = material('Headboard', 'brown_leather', (.30, .22, .16), rough=.6, out=out)
    wood = material('Wood', 'teak_veneer', None, rough=.4)
    linen = material('Linen', 'rough_linen', (.95, .93, .88), rough=.9, out=out)
    duvet = material('Duvet', 'waffle_pique_cotton', (.18, .27, .42), rough=.9, out=out)
    L, Wd = 2.1, 1.95
    cushion('frame', (Wd + .12, L, .28), (0, 0, .24), fabric, puff=.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f'leg{sx}{sy}', (.06, .06, .1), (sx * (Wd / 2 - .02), sy * (L / 2 - .08), .05), wood, uv=1)
    for i in range(5):
        cushion(f'panel{i}', ((Wd + .2) / 5 - .02, .12, 1.05), (-(Wd + .2) / 2 + (i + .5) * (Wd + .2) / 5, L / 2 + .06, .72), fabric, puff=.02)
    box('headtop', (Wd + .26, .16, .05), (0, L / 2 + .06, 1.27), wood, uv=1)
    bed_core(out, L, Wd, .62, duvet, linen, wood)
    export(slug, 'Cama king')


def ceiling_fan():
    reset()
    slug = 'mare_ceiling_fan'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    wood = material('Wood', 'teak_veneer', None, rough=.4)
    metal = material('Brass', 'metal_plate', (.62, .50, .30), rough=.35, out=out)
    # Origin at the bottom; rod reaches up to the ceiling (0.45 m).
    lathe('motor', [(0, 0), (.06, 0), (.13, .04), (.15, .1), (.12, .16), (.04, .19), (0, .19)], (0, 0, 0), metal, 24)
    tube('rod', (0, 0, .18), (0, 0, .45), .015, metal, 8)
    lathe('canopy', [(0, .4), (.08, .4), (.06, .45), (0, .45)], (0, 0, 0), metal, 16)
    for i in range(5):
        a = 2 * math.pi * i / 5
        box(f'blade{i}', (.6, .14, .012), (math.cos(a) * .45, math.sin(a) * .45, .1), wood, rot=(math.radians(8), 0, a), uv=.6)
        box(f'iron{i}', (.16, .03, .015), (math.cos(a) * .17, math.sin(a) * .17, .11), metal, rot=(0, 0, a), uv=.4)
    lathe('light', [(0, -.08), (.07, -.06), (.08, 0), (0, 0)], (0, 0, 0), material('Glass', 'rough_linen', (.95, .93, .86), rough=.3, out=out), 16)
    export(slug, 'Ventilador de teto')


def ac_unit():
    reset()
    slug = 'mare_ac_unit'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    white = material('Plastic', 'rough_linen', (.95, .95, .94), rough=.35, out=out)
    grey = material('Grille', 'metal_plate', (.55, .57, .58), rough=.5, out=out)
    # Split unit: origin at the bottom-back centre, front towards Blender -Y (into the room).
    cushion('body', (.9, .22, .3), (0, -.11, .15), white, puff=.004)
    for i in range(14):
        box(f'louvre{i}', (.8, .03, .006), (0, -.215, .03 + i * .004), grey, rot=(math.radians(30), 0, 0), uv=.3)
    box('flap', (.82, .02, .06), (0, -.22, .03), white, rot=(math.radians(-25), 0, 0), uv=.3)
    box('led', (.03, .005, .01), (.36, -.222, .16), grey, uv=.2)
    export(slug, 'Ar-condicionado split')


def rug():
    reset()
    slug = 'mare_rug'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    weave = material('Rug', 'fabric_pattern_07', (.72, .52, .32), rough=.95, out=out)
    fringe = material('Fringe', 'rough_linen', (.9, .86, .76), rough=.95, out=out)
    cushion('rug', (2.0, 1.4, .015), (0, 0, .008), weave, puff=.002)
    for sx in (-1, 1):
        for i in range(24):
            y = -.68 + i * 1.36 / 23
            box(f'tassel{sx}{i}', (.06, .012, .006), (sx * 1.03, y, .004), fringe, uv=.2)
    export(slug, 'Tapete trançado')


def hang_chain():
    """Short brass chain for hanging lamps: 12 cm of interlocked links plus a hook. Origin at the bottom."""
    reset()
    slug = 'mare_hang_chain'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    brass = material('Brass', 'metal_plate', (.66, .52, .28), rough=.35, out=out)
    for i in range(6):
        z = .012 + i * .018
        bpy.ops.mesh.primitive_torus_add(major_radius=.009, minor_radius=.0022, major_segments=16, minor_segments=8,
                                         location=(0, 0, z), rotation=(math.pi / 2, 0, (math.pi / 2) * (i % 2)))
        link = bpy.context.active_object
        link.scale = (1, 1, 1.4)
        link.data.materials.append(brass)
    lathe('hook', [(0, 0), (.006, 0), (.006, .015), (.012, .02), (0, .02)], (0, 0, .105), brass, 12)
    export(slug, 'Corrente de lampião')


BUILD = {
    'mare_hang_chain': hang_chain,
    'mare_bungalow': bungalow,
    'mare_bed_simple': lambda: bed_simple(),
    'mare_bed_iron': lambda: bed_simple('mare_bed_iron', True),
    'mare_bed_king': bed_king,
    'mare_ceiling_fan': ceiling_fan,
    'mare_ac_unit': ac_unit,
    'mare_rug': rug,
}

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for slug in args or BUILD:
        BUILD[slug]()
        print('built', slug)
