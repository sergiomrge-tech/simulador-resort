"""Boat tour models (CHECKLIST_EXPANSOES 2.2, 05/11). Nothing free with a commercial licence fits (Poly Haven has no
boats; Kenney/Quaternius watercraft are low poly), so they are modelled here:
  TourBoat_lancha   8 m open tour boat: lofted fibreglass V hull (white, blue band), deck, cushioned side benches for
                    eight, bimini canopy on steel poles, helm console with wheel and windscreen, outboard engine
  TourBoat_buoy     channel buoy (red/white striped float, cage, top mark)
  TourBoat_stop     stop buoy (yellow float, flag) where the boat halts for a tour stop
  TourBoat_dolphin  bottlenose dolphin (lofted body, beak, melon, dorsal fin, flippers, flukes, counter-shaded skin)
Metres, Blender Z up, waterline at z=0, bow toward +Y (arrives as UE -Y). Unique TourBoat_* material/image names.
Prints the passenger seat and helm positions (Blender metres) for tours.json.
Output D:/CodexTemp/tourboat/<name>.glb.
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_tour_boat.py [name ...]"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
import gen_bar_prep as G  # noqa: E402

G.OUT = 'D:/CodexTemp/tourboat'
os.makedirs(G.OUT, exist_ok=True)
mat, rbox, lathe, obj, place, finish, image, reset = G.mat, G.rbox, G.lathe, G.obj, G.place, G.finish, G.image, G.reset
TAU = 2 * math.pi


def hull_surface(L, W, D, m_hull, m_band, m_inside):
    """Lofted V hull: sections from the transom (y=0) to the stem (y=L). Outer skin, sheer band, inner skin."""
    n_sec, n_side = 28, 9
    secs = []
    for i in range(n_sec + 1):
        t = i / n_sec
        bow = max(0.0, (t - .5) / .5)
        half = W / 2 * (1 - bow ** 2.2) * (.96 + .04 * math.sin(math.pi * min(t * 2, 1)))
        half = max(half, .015)
        keel = -.38 * (1 - t ** 4) + .1 * t ** 6
        sheer = D - .38 + .22 * t ** 2.5
        pts = []
        for k in range(n_side + 1):
            s = k / n_side
            # From the keel out to the chine, then up the topside to the sheer.
            if s < .45:
                u = s / .45
                y_off = half * .78 * u
                z = keel + (.16 + .12 * (1 - bow)) * u ** 1.4
            else:
                u = (s - .45) / .55
                y_off = half * (.78 + .22 * math.sin(u * math.pi / 2))
                z = keel + .16 + .12 * (1 - bow) + (sheer - keel - .28 + .12 * bow) * u
            pts.append((y_off, z))
        secs.append((t * L, pts))
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    rows = []
    for y, pts in secs:
        right = [bm.verts.new((x, y, z)) for x, z in pts]
        left = [bm.verts.new((-x, y, z)) for x, z in reversed(pts[1:])]
        rows.append(list(reversed(left)) + right)
    for i in range(len(rows) - 1):
        a, b = rows[i], rows[i + 1]
        for k in range(len(a) - 1):
            f = bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))
            for lp, (uu, vv) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                lp[uv].uv = (uu / (len(a) - 1), vv / n_sec)
    # Transom.
    bm.faces.new(list(reversed(rows[0])))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    hull = obj(bm, 'hull', m_hull)
    md = hull.modifiers.new('s', 'SOLIDIFY')
    md.thickness = .04
    md.offset = -1
    md = hull.modifiers.new('sub', 'SUBSURF')
    md.levels = 1
    # Blue band below the sheer and the rub rail.
    for i, (y, pts) in enumerate(secs[:-1]):
        pass
    band_pts = []
    for y, pts in secs:
        band_pts.append((y, pts[-1][0] + .006, pts[-1][1] - .12, pts[-1][1] - .02))
    bm = bmesh.new()
    for side in (1, -1):
        prev = None
        for y, x, z0, z1 in band_pts:
            v0, v1 = bm.verts.new((side * x, y, z0)), bm.verts.new((side * x, y, z1))
            if prev:
                bm.faces.new((prev[0], v0, v1, prev[1]) if side > 0 else (prev[1], v1, v0, prev[0]))
            prev = (v0, v1)
    obj(bm, 'band', m_band)
    rail = bpy.data.curves.new('rail', 'CURVE')
    rail.dimensions = '3D'
    for side in (1, -1):
        sp = rail.splines.new('POLY')
        sp.points.add(len(band_pts) - 1)
        for p_, (y, x, z0, z1) in zip(sp.points, band_pts):
            p_.co = (side * (x + .01), y, z1 + .02, 1)
    rail.bevel_depth = .025
    ro = bpy.data.objects.new('rail', rail)
    bpy.context.collection.objects.link(ro)
    ro.data.materials.append(m_inside)
    bpy.context.view_layer.objects.active = ro
    ro.select_set(True)
    bpy.ops.object.convert(target='MESH')
    ro.select_set(False)
    return secs


def lancha():
    reset()
    P = 'TourBoat_lancha'
    L, W, D = 8.0, 2.6, 1.05
    hull_img = image(f'{P}_gel', 256, 256, lambda u, v: (.94 - .02 * np.sin(v * 40), .95 - .02 * np.sin(v * 40), .96 + 0 * u))
    m_hull = mat(f'{P}_Hull', hull_img, rough=.25)
    m_band = mat(f'{P}_Band', None, (.08, .33, .62), .35)
    m_in = mat(f'{P}_Rail', None, (.82, .83, .85), .25, .9)
    deck_img = G.wood_img(P + 'teak', (.55, .37, .2), 256, 256, 8)
    m_deck = mat(f'{P}_Deck', deck_img, rough=.6)
    m_cush = mat(f'{P}_Cushion', image(f'{P}_vinyl', 64, 64, lambda u, v: (.92 - .03 * (np.mod(u * 8, 1) < .05), .9 - .03 * (np.mod(u * 8, 1) < .05), .85 + 0 * u)), .5)
    m_canvas = mat(f'{P}_Canvas', image(f'{P}_canvas', 128, 128, lambda u, v: (.1 + .02 * np.sin(u * 90), .32 + .02 * np.sin(v * 90), .58 + 0 * u)), .8)
    m_steel = mat(f'{P}_Steel', None, (.85, .86, .88), .2, 1.0)
    m_black = mat(f'{P}_Black', None, (.05, .05, .06), .45)
    m_glass = mat(f'{P}_Screen', None, (.35, .45, .5), .05, .3)
    m_engine = mat(f'{P}_Engine', None, (.92, .93, .95), .3)
    hull_surface(L, W, D, m_hull, m_band, m_in)
    deck_z = .12
    # Teak deck inside the hull (planks), clear of the bow.
    for i in range(9):
        x = -1.0 + i * .25
        rbox((.24, 5.6, .03), (x, 3.1, deck_z), m_deck, .004, 'plank', uvscale=1.5)
    seats = []
    # Side benches with cushions: four per side between y 1.6 and 5.0.
    for side in (1, -1):
        for j in range(4):
            y = 1.75 + j * .9
            rbox((.48, .82, .4), (side * .82, y, deck_z + .2), m_hull, .03, 'bench', uvscale=.5)
            rbox((.46, .78, .09), (side * .82, y, deck_z + .44), m_cush, .03, 'cushion', uvscale=.5)
            rbox((.1, .78, .32), (side * 1.06, y, deck_z + .62), m_cush, .03, 'back', uvscale=.5)
            seats.append((side * .8, y, deck_z + .485, 90 if side > 0 else -90))
    # Helm console at the stern quarter, low enough to see over (the pilot's eye is ~1.64 m above the deck): wheel and
    # a small tilted windscreen.
    rbox((.62, .5, .66), (.45, .82, deck_z + .33), m_hull, .05, 'console', uvscale=.5)
    rbox((.58, .03, .2), (.45, 1.05, deck_z + .76), m_glass, .008, 'screen', (-.55, 0, 0))
    wheel = lathe([(0.0, -.012), (.17, -.012), (.19, 0), (.17, .012), (0.0, .012)], m_black, 32, 'wheel')
    place(wheel, (.45, .6, deck_z + .7), (math.radians(55), 0, 0))
    G.lathe([(0, 0), (.02, 0), (.02, .16), (0, .16)], m_black, 10, 'column').location = (.45, .62, deck_z + .56)
    rbox((.5, .3, .08), (.45, .32, deck_z + .42), m_cush, .03, 'helm_seat', uvscale=.5)
    helm = (.45, .3, deck_z + .46)
    # Bimini canopy on four steel poles.
    for sx in (-1, 1):
        for sy in (1.4, 4.7):
            G.lathe([(0, 0), (.022, 0), (.022, 1.55), (0, 1.55)], m_steel, 12, 'pole').location = (sx * 1.0, sy, deck_z)
    bm = bmesh.new()
    nx, ny = 10, 14
    vs = [[bm.verts.new((-1.08 + 2.16 * i / nx, 1.3 + 3.5 * j / ny, deck_z + 1.55 + .12 * math.sin(math.pi * i / nx))) for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
    top = obj(bm, 'canopy', m_canvas)
    md = top.modifiers.new('s', 'SOLIDIFY')
    md.thickness = .015
    # Outboard engine on the transom.
    rbox((.42, .5, .55), (0, -.28, .55), m_engine, .09, 'cowl', uvscale=.5)
    rbox((.32, .3, .12), (0, -.3, .24), m_black, .03, 'midsection', uvscale=.5)
    G.lathe([(0, 0), (.05, 0), (.05, .55), (0, .55)], m_black, 12, 'shaft').location = (0, -.32, -.45)
    for k in range(3):
        b = rbox((.06, .16, .015), (0, -.32, -.45), m_steel, .005, 'blade')
        b.rotation_euler = (0, math.radians(k * 120), 0)
    # Bow cleat and a navigation light.
    rbox((.12, .04, .03), (0, L - .5, D - .1), m_steel, .01, 'cleat')
    finish(P, keep_base=False)
    print('SEATS', [(round(x, 3), round(y, 3), round(z, 3), yaw) for x, y, z, yaw in seats])
    print('HELM', [round(v, 3) for v in helm])


def buoy_parts(P, colours, flag=False):
    m_a = mat(f'{P}_A', None, colours[0], .45)
    m_b = mat(f'{P}_B', None, colours[1], .45)
    m_steel = mat(f'{P}_Steel', None, (.6, .6, .62), .4, .8)
    # Striped float: alternate bands.
    bands = [(-.35, -.15), (-.15, .05), (.05, .25), (.25, .4)]
    for i, (z0, z1) in enumerate(bands):
        r0 = .45 * math.cos(z0 * 1.3)
        r1 = .45 * math.cos(z1 * 1.3)
        lathe([(0, z0), (r0, z0), (r1, z1), (0, z1)], m_a if i % 2 == 0 else m_b, 36, 'float')
    lathe([(0, .4), (.3, .4), (.26, .48), (0, .48)], m_b, 30, 'cap')
    # Cage of bars up to the top mark.
    for k in range(4):
        a = TAU * k / 4
        bar = lathe([(0, 0), (.02, 0), (.02, .9), (0, .9)], m_steel, 8, 'bar')
        place(bar, (.18 * math.cos(a), .18 * math.sin(a), .45), (math.radians(8) * math.sin(a), -math.radians(8) * math.cos(a), 0))
    lathe([(0, 1.3), (.2, 1.3), (.2, 1.34), (0, 1.34)], m_steel, 20, 'ring')
    if flag:
        lathe([(0, 1.34), (.015, 1.34), (.015, 2.0), (0, 2.0)], m_steel, 8, 'mast')
        bm = bmesh.new()
        vs = [[bm.verts.new((0, .02 + .45 * i / 8, 1.6 + .32 * j / 4 + .03 * math.sin(i * .9))) for i in range(9)] for j in range(5)]
        for j in range(4):
            for i in range(8):
                bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
        f = obj(bm, 'flag', m_b)
        f.modifiers.new('s', 'SOLIDIFY').thickness = .006
    else:
        G.lathe([(0, 0), (.16, 0), (.0, .3)], m_a, 24, 'cone').location = (0, 0, 1.34)


def buoy():
    reset()
    buoy_parts('TourBoat_buoy', ((.85, .12, .1), (.96, .96, .94)))
    finish('TourBoat_buoy', keep_base=False)


def stop():
    reset()
    buoy_parts('TourBoat_stop', ((.98, .78, .1), (.95, .2, .15)), flag=True)
    finish('TourBoat_stop', keep_base=False)


def dolphin():
    """Bottlenose dolphin ~2.4 m: lofted elliptical sections along +Y (tail at y=0, beak at y=L)."""
    reset()
    P = 'TourBoat_dolphin'
    L = 2.4
    skin = image(f'{P}_skin', 128, 128, lambda u, v: (
        .34 + .45 * (np.abs(u - .5) > .32) - .04 * np.sin(v * 20),
        .38 + .45 * (np.abs(u - .5) > .32) - .04 * np.sin(v * 20),
        .44 + .42 * (np.abs(u - .5) > .32) + 0 * v))
    m = mat(f'{P}_Skin', skin, rough=.3)
    m_eye = mat(f'{P}_Eye', None, (.02, .02, .02), .1)
    n_sec, n_ring = 30, 20
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    rings = []
    for i in range(n_sec + 1):
        t = i / n_sec
        # Radius profile: thin peduncle, thick chest, melon, then the short beak.
        if t < .12:
            r = .05 + .03 * t / .12
        elif t < .55:
            r = .08 + .17 * math.sin((t - .12) / .43 * math.pi / 2)
        elif t < .86:
            r = .25 - .1 * ((t - .55) / .31) ** 1.6
        else:
            r = .15 - .11 * ((t - .86) / .14) ** .7
        r = max(r, .012)
        z_c = .02 * math.sin(t * math.pi) - (.03 if t > .88 else 0)
        ring = []
        for k in range(n_ring):
            a = TAU * k / n_ring
            ring.append(bm.verts.new((r * .82 * math.cos(a), t * L, z_c + r * math.sin(a))))
        rings.append(ring)
    for i in range(n_sec):
        for k in range(n_ring):
            k2 = (k + 1) % n_ring
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            for lp, (uu, vv) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                lp[uv].uv = ((uu / n_ring + .25) % 1, vv / n_sec)
    tip = bm.verts.new((0, L + .015, -.03))
    for k in range(n_ring):
        bm.faces.new((rings[-1][k], rings[-1][(k + 1) % n_ring], tip))
    tail = bm.verts.new((0, -.01, .02))
    for k in range(n_ring):
        bm.faces.new((rings[0][(k + 1) % n_ring], rings[0][k], tail))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    body = obj(bm, 'body', m)
    body.modifiers.new('sub', 'SUBSURF').levels = 1

    def fin(name, pts, thick, loc, rot):
        bm2 = bmesh.new()
        vs = [bm2.verts.new((x, 0, z)) for x, z in pts]
        bm2.faces.new(vs)
        o = obj(bm2, name, m)
        md = o.modifiers.new('s', 'SOLIDIFY')
        md.thickness = thick
        md.offset = 0
        o.modifiers.new('sub', 'SUBSURF').levels = 2
        place(o, loc, rot)
        return o
    # Dorsal fin (swept back), two flippers, the flukes.
    fin('dorsal', [(-.0, 0), (.32, 0), (.12, .1), (-.06, .3), (-.04, .12)], .03, (0, 1.05, .24), (0, 0, math.pi / 2))
    for s in (-1, 1):
        fin('flipper', [(0, 0), (.22, -.05), (.3, -.12), (.12, -.08)], .025, (s * .16, 1.55, -.1), (math.radians(15) * s, math.radians(25) * s, math.pi / 2 + s * .6))
    bm3 = bmesh.new()
    pts = [(0, 0), (.32, -.12), (.42, -.06), (.2, .05), (0, .04), (-.2, .05), (-.42, -.06), (-.32, -.12)]
    vs = [bm3.verts.new((x, y, 0)) for x, y in pts]
    bm3.faces.new(vs)
    fl = obj(bm3, 'flukes', m)
    md = fl.modifiers.new('s', 'SOLIDIFY')
    md.thickness = .03
    md.offset = 0
    fl.modifiers.new('sub', 'SUBSURF').levels = 2
    place(fl, (0, .02, .02))
    for s in (-1, 1):
        e = G.lathe([(0, -.012), (.012, -.008), (.012, .008), (0, .012)], m_eye, 10, 'eye')
        place(e, (s * .135, 2.05, .02), (0, math.pi / 2, 0))
    finish(P, keep_base=False)


ALL = {'lancha': lancha, 'buoy': buoy, 'stop': stop, 'dolphin': dolphin}
if __name__ == '__main__':
    for n in sys.argv[1:] or list(ALL):
        ALL[n]()
    print('gen_tour_boat ok')
