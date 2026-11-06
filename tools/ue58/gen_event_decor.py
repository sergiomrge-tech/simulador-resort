"""Decoration of the Grand Hotel events (CHECKLIST 5.2 "Eventos com montagem: casamento na praia, aniversário,
congresso"): the pieces the player sets up from the event's plan. Searched first: Poly Haven has no wedding arch,
lectern, projector screen nor tiered cake (only carrot_cake, vases and flowers), so these are modelled here with the
Poly Haven textures of gen_custom_furniture. Chairs and the round tables are the existing Poly Haven ones.

Real metres, base at z=0, centred on the origin, FRONT = Blender -Y (arrives as UE +Y).
  mare_event_arch        wedding arch 1.9 x 2.65 m: teak posts and half-round top, greenery and white/pink blossoms,
                         sheer white drapes on both sides
  mare_event_cake_table  round table 1.0 m with a white tablecloth to the floor and a three-tier wedding cake
  mare_event_lectern     teak lectern 0.65 m wide, slanted desk and a gooseneck microphone
  mare_event_screen      projector screen 1.8 x 1.2 m on a tripod stand
  mare_event_gifts       pile of three wrapped gifts with ribbons and bows
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_event_decor.py [slug ...]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from gen_custom_furniture import OUT, box, drape, export, finish, lathe, material, mesh_obj, reset, tube  # noqa: E402


def flat(name, rgb, rough=.55, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m


def blossom(name, loc, r, mat, petals=6, tilt=(0.0, 0.0), centre=None):
    """A flower: curved petals around a small centre (not a ball)."""
    from mathutils import Euler, Vector
    bm = bmesh.new()
    rot = Euler((tilt[0], tilt[1], 0)).to_matrix()
    for p in range(petals):
        a = 2 * math.pi * p / petals
        grid = []
        for j in range(4):           # along the petal
            t = j / 3
            row = []
            for i in range(3):       # across
                s = (i - 1) * .5
                w = math.sin(math.pi * max(t, .08)) * .42 * r
                x = (t * r) * math.cos(a) - s * w * math.sin(a)
                y = (t * r) * math.sin(a) + s * w * math.cos(a)
                z = .35 * r * t * t - .08 * r * abs(s)
                row.append(bm.verts.new(rot @ Vector((x, y, z)) + Vector(loc)))
            grid.append(row)
        for j in range(3):
            for i in range(2):
                bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    obj = mesh_obj(name, bm)
    finish(obj, mat, .2)
    s = obj.modifiers.new('Solidify', 'SOLIDIFY')
    s.thickness = .002
    if centre:
        c = lathe(name + '_c', [(0, .0), (r * .18, r * .05), (r * .14, r * .14), (0, r * .17)], (0, 0, 0), centre, sides=10)
        for v in c.data.vertices:
            v.co = rot @ v.co + Vector(loc)
    return obj


def leaf(name, loc, length, yaw, pitch, mat):
    """A pointed leaf, slightly folded along its midrib."""
    from mathutils import Euler, Vector
    bm = bmesh.new()
    rot = Euler((pitch, 0, yaw)).to_matrix()
    rows = []
    for j in range(5):
        t = j / 4
        w = math.sin(math.pi * t) * length * .22
        rows.append([bm.verts.new(rot @ Vector((s * w, t * length, abs(s) * w * .35 - .1 * length * t * t)) + Vector(loc)) for s in (-1, 0, 1)])
    for j in range(4):
        for i in range(2):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    obj = mesh_obj(name, bm)
    finish(obj, mat, .3)
    s = obj.modifiers.new('Solidify', 'SOLIDIFY')
    s.thickness = .0015
    return obj


def arch():
    reset()
    out = OUT / 'mare_event_arch'
    out.mkdir(parents=True, exist_ok=True)
    teak = material('Teak', 'teak_veneer', rough=.5)
    green = flat('Leaf', (.12, .32, .1), .55)
    white = flat('Petal', (.95, .94, .9), .6)
    pink = flat('PetalPink', (.92, .62, .68), .6)
    gold = flat('Pollen', (.85, .66, .2), .5)
    sheer = material('Sheer', 'rough_linen', (.97, .97, .95), rough=.9, out=out)
    W, H, R = .95, 2.0, .95
    for sx in (-1, 1):
        box(f'post{sx}', (.09, .09, H), (sx * W, 0, H / 2), teak, bevel=.008)
        box(f'foot{sx}', (.34, .34, .05), (sx * W, 0, .025), teak, bevel=.006)
    n = 18
    pts = [(R * math.cos(math.pi * i / n), 0, H + R * math.sin(math.pi * i / n)) for i in range(n + 1)]
    for i in range(n):
        tube(f'arc{i}', pts[i], pts[i + 1], .045, teak, sides=12)
    import random
    rnd = random.Random(5)
    # greenery climbing the posts and covering the arc, blossoms in clusters
    spots = [(sx * W + rnd.uniform(-.06, .06), rnd.uniform(-.07, .07), rnd.uniform(.15, H)) for sx in (-1, 1) for _ in range(90)]
    for i in range(260):
        a = math.pi * rnd.random()
        spots.append((R * math.cos(a) + rnd.uniform(-.05, .05), rnd.uniform(-.07, .07), H + R * math.sin(a) + rnd.uniform(-.05, .05)))
    for k, (x, y, z) in enumerate(spots):
        leaf(f'leaf{k}', (x, y, z), rnd.uniform(.08, .15), rnd.uniform(0, 6.28), rnd.uniform(-1.4, 1.4), green)
    for k in range(150):
        x, y, z = spots[rnd.randrange(len(spots))]
        blossom(f'fl{k}', (x, y - .04, z), rnd.uniform(.045, .08), white if k % 3 else pink, petals=rnd.choice((5, 6, 8)),
                tilt=(math.radians(rnd.uniform(70, 110)), rnd.uniform(-.4, .4)), centre=gold)
    for sx in (-1, 1):
        d = drape(f'drape{sx}', .55, 1.9, (sx * (W + .02), .06, H + .55), 0, sheer, folds=5, amp=.03)
    export('mare_event_arch', 'Arco de casamento com flores')


def cake_table():
    reset()
    out = OUT / 'mare_event_cake_table'
    out.mkdir(parents=True, exist_ok=True)
    cloth = material('Cloth', 'waffle_pique_cotton', (.96, .95, .92), rough=.9, out=out)
    icing = flat('Icing', (.97, .95, .9), .45)
    silver = flat('Stand', (.78, .78, .8), .25, .9)
    pink = flat('SugarRose', (.93, .66, .7), .5)
    green = flat('SugarLeaf', (.35, .55, .3), .5)
    # tablecloth to the floor with soft folds
    prof = []
    sides = 64
    bm = bmesh.new()
    rings = []
    for j, (r, z) in enumerate([(0, .76), (.5, .76), (.52, .74), (.53, .6), (.55, .3), (.57, .02)]):
        ring = []
        for i in range(sides):
            a = 2 * math.pi * i / sides
            rr = r + (.012 * math.sin(a * 14) if z < .7 else 0) * (1 - z / .76)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(sides):
            bm.faces.new((r0[i], r0[(i + 1) % sides], r1[(i + 1) % sides], r1[i]))
    obj = mesh_obj('cloth', bm)
    finish(obj, cloth, .6)
    s = obj.modifiers.new('Solidify', 'SOLIDIFY')
    s.thickness = .006
    # cake stand and three tiers with piped icing rims
    lathe('stand', [(0, .76), (.07, .76), (.03, .78), (.025, .86), (.2, .87), (.2, .885), (0, .885)], (0, 0, 0), silver, sides=40)
    z = .885
    for k, (r, h) in enumerate(((.17, .13), (.125, .12), (.085, .11))):
        lathe(f'tier{k}', [(0, z), (r, z), (r + .006, z + .01), (r, z + .02), (r, z + h - .01), (r - .004, z + h), (0, z + h)], (0, 0, 0), icing, sides=48)
        for i in range(24):   # piped pearls on the base of each tier (sugar beads, not spheres stuck on: lathe beads)
            a = 2 * math.pi * i / 24
            lathe(f'pearl{k}_{i}', [(0, -.009), (.007, -.006), (.009, 0), (.007, .006), (0, .009)], (r * math.cos(a), r * math.sin(a), z + .01), icing, sides=8)
        z += h
    for k in range(5):
        a = 2 * math.pi * k / 5
        blossom(f'rose{k}', (.05 * math.cos(a), .05 * math.sin(a), z + .01), .028, pink, petals=8, centre=pink)
        leaf(f'sl{k}', (.06 * math.cos(a + .3), .06 * math.sin(a + .3), z + .005), .04, a, 1.2, green)
    export('mare_event_cake_table', 'Mesa do bolo com toalha e bolo de três andares')


def lectern():
    reset()
    teak = material('Teak', 'teak_veneer', rough=.45)
    black = flat('Black', (.04, .04, .045), .4, .6)
    box('plinth', (.62, .46, .06), (0, 0, .03), teak, bevel=.008)
    # Desk sloping down toward the speaker (+Y): its underside rests on the front panel and the back box.
    t = math.tan(math.radians(14))
    zf, zb = 1.08 + .14 * t - .02, 1.08 - .21 * t - .02
    box('front', (.56, .05, zf - .06), (0, -.18, .06 + (zf - .06) / 2), teak, bevel=.01)
    box('back', (.5, .3, zb - .06), (0, .02, .06 + (zb - .06) / 2), teak, bevel=.008)
    box('sides', (.56, .34, .03), (0, -.01, zb - .015), teak, bevel=.004)
    box('desk', (.65, .5, .04), (0, -.04, 1.08), teak, rot=(math.radians(-14), 0, 0), bevel=.008)
    box('lip', (.6, .03, .035), (0, .2, 1.08 - .24 * t + .02), teak, bevel=.004)
    box('panel', (.4, .01, .55), (0, -.21, .62), teak, bevel=.004)
    pts = [(.22, .1, 1.13), (.22, .08, 1.22), (.2, .03, 1.3), (.16, -.05, 1.35), (.12, -.12, 1.36)]
    for i in range(len(pts) - 1):
        tube(f'neck{i}', pts[i], pts[i + 1], .006, black, sides=10)
    lathe('mic', [(0, 0), (.012, .005), (.016, .03), (.016, .05), (0, .06)], pts[-1], black, sides=16)
    export('mare_event_lectern', 'Púlpito de madeira com microfone')


def screen():
    reset()
    white = flat('Screen', (.93, .93, .92), .85)
    grey = flat('Case', (.25, .26, .28), .4, .6)
    box('screen', (1.8, .012, 1.2), (0, 0, 1.35), white, bevel=.003)
    box('border', (1.84, .016, .03), (0, .002, 1.965), grey, bevel=.004)
    box('bar', (1.84, .016, .03), (0, .002, .735), grey, bevel=.004)
    lathe('case', [(0, 0), (.04, 0), (.045, .04), (.045, 1.9), (.04, 1.94), (0, 1.94)], (0, 0, 0), grey, sides=16)
    for o in bpy.data.objects:
        if o.name == 'case':
            o.rotation_euler = (0, math.pi / 2, 0)
            o.location = (-.97, .04, .7)
    tube('pole', (0, .05, 0.08), (0, .05, 2.0), .016, grey)
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 2
        tube(f'leg{k}', (0, .05, .55), (.55 * math.cos(a), .05 + .55 * math.sin(a), 0.0), .013, grey)
    export('mare_event_screen', 'Tela de projeção em tripé')


def gifts():
    reset()
    out = OUT / 'mare_event_gifts'
    out.mkdir(parents=True, exist_ok=True)
    papers = [flat('PaperRed', (.75, .12, .14), .5), flat('PaperBlue', (.15, .35, .7), .5), flat('PaperYellow', (.95, .78, .2), .5)]
    ribbon = flat('Ribbon', (.96, .92, .85), .35)
    boxes = [((.34, .3, .24), (0, 0, .12)), ((.24, .22, .2), (.05, -.02, .34)), ((.2, .2, .16), (.3, .05, .08))]
    for k, (size, loc) in enumerate(boxes):
        box(f'gift{k}', size, loc, papers[k], bevel=.004)
        x, y, z = loc
        top = z + size[2] / 2
        box(f'rib{k}a', (size[0] + .004, .03, size[2] + .004), loc, ribbon, bevel=.001)
        box(f'rib{k}b', (.03, size[1] + .004, size[2] + .004), loc, ribbon, bevel=.001)
        for s in (-1, 1):   # bow loops
            pts = [(x, y, top), (x + s * .05, y, top + .045), (x + s * .085, y, top + .02), (x + s * .03, y, top + .005)]
            for i in range(len(pts) - 1):
                tube(f'bow{k}{s}{i}', pts[i], pts[i + 1], .012, ribbon, sides=8)
    export('mare_event_gifts', 'Presentes embrulhados com laço')


ALL = {'mare_event_arch': arch, 'mare_event_cake_table': cake_table, 'mare_event_lectern': lectern,
       'mare_event_screen': screen, 'mare_event_gifts': gifts}

if __name__ == '__main__':
    for slug in (sys.argv[1:] or list(ALL)):
        ALL[slug]()
        print('ok', slug)
