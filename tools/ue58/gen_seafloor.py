"""Reef seafloor life (05/11, Sergio: 'tubarões próximo aos recifes', 'fundo do mar precisa de rochas', 'vida marinha,
algas etc'). Searched first: no free seaweed/anemone/urchin with a commercial licence and real detail; the only CC0
shark (Quaternius Lowpoly Animated Fish) is low poly, which the project rules reject. The rocks come from Poly Haven
(CC0, already in the project); these are modelled here:
  Sea_shark       blacktip reef shark ~1.6 m (lofted fusiform body, pointed snout, gill slits, eyes, two dorsals,
                  pectorals, pelvics, anal fin, heterocercal tail; counter-shaded skin, black fin tips). Snout +Y,
                  origin at the tail base (y=0); the tail sways in the UE material (WPO).
  Sea_kelp_a/b    kelp stalks 1.6 / 2.4 m: curved stipe, ruffled blades and gas bladders (sway in the material)
  Sea_seagrass    tuft of ~22 turtle-grass blades
  Sea_anemone     sea anemone: column, oral disc and ~60 curling tentacles with violet tips
  Sea_urchin      long-spined urchin: body and ~110 spines
  Sea_starfish    five-armed starfish with bumps
  Sea_sponge      cluster of four tube sponges (open, porous)
Metres, Blender Z up, base at z=0 (the shark centred on its axis). Unique Sea_* material/image names, power-of-two
textures. Output D:/CodexTemp/seafloor/<name>.glb.
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_seafloor.py [name ...]"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
import gen_bar_prep as G  # noqa: E402

G.OUT = 'D:/CodexTemp/seafloor'
os.makedirs(G.OUT, exist_ok=True)
mat, obj, place, finish, image, reset = G.mat, G.obj, G.place, G.finish, G.image, G.reset
TAU = 2 * math.pi


def two_sided(m):
    m.use_backface_culling = False
    return m


def tube(name, pts, radius, m, taper=1.0, res=8):
    """Curve tube through pts (bevelled, optionally tapering to `taper` x radius at the end), as a mesh."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        bp = sp.bezier_points[i]
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
        bp.radius = 1 + (taper - 1) * i / max(1, len(pts) - 1)
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    cu.resolution_u = res
    cu.use_fill_caps = True
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.ops.object.convert(target='MESH')
    return o


def ribbon(name, path, width, m, ruffle=0.0, seg=None):
    """Flat blade along a list of points: width(t) profile, edges ruffled up/down by `ruffle`; UV u across, v along."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    n = len(path)
    rows = []
    for i, p in enumerate(path):
        t = i / (n - 1)
        a = Vector(path[min(i + 1, n - 1)]) - Vector(path[max(i - 1, 0)])
        side = a.cross(Vector((0, 0, 1)))
        if side.length < 1e-6:
            side = Vector((1, 0, 0))
        side.normalize()
        w = width(t)
        lift = Vector((0, 0, 1)).cross(side).normalized() if False else Vector((0, 0, 0))
        r0 = Vector(p) - side * w + a.normalized().cross(side) * ruffle * math.sin(t * 40) * w
        r1 = Vector(p) + side * w + a.normalized().cross(side) * ruffle * math.sin(t * 40 + 2) * w
        rows.append((bm.verts.new(r0), bm.verts.new(Vector(p)), bm.verts.new(r1), t))
    for i in range(n - 1):
        for j in range(2):
            f = bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
            for lp, (uu, vv) in zip(f.loops, ((j / 2, rows[i][3]), ((j + 1) / 2, rows[i][3]), ((j + 1) / 2, rows[i + 1][3]), (j / 2, rows[i + 1][3]))):
                lp[uv].uv = (uu, vv)
    o = obj(bm, name, m)
    return o


# ---------------------------------------------------------------- shark
def shark():
    """Blacktip reef shark, 1.6 m: snout toward +Y, tail base at y=0, body axis at z=0."""
    reset()
    P = 'Sea_shark'
    L = 1.6

    def skin_fill(u, v):
        top = np.clip((np.cos((u - .5) * TAU) - .05) * 2.2, 0, 1)   # u=.5 is the back
        grey = np.array([.40, .41, .40])
        belly = np.array([.86, .86, .84])
        r = belly[0] + (grey[0] - belly[0]) * top
        g = belly[1] + (grey[1] - belly[1]) * top
        b = belly[2] + (grey[2] - belly[2]) * top
        # Five gill slits on each flank (v ~ .70-.78), a faint lateral line.
        gills = ((np.abs(np.mod((v - .70) * 62, 1) - .5) < .12) & (v > .70) & (v < .78)
                 & (np.abs(np.abs(u - .5) - .26) < .05))
        k = np.where(gills, .45, 1.0) * (1 - .05 * np.exp(-((np.abs(u - .5) - .2) ** 2) / .0004))
        return r * k, g * k, b * k
    m = mat(f'{P}_Skin', image(f'{P}_skin', 256, 256, skin_fill), rough=.42)

    def fin_fill(u, v):
        tip = np.clip((v - .7) * 6, 0, 1)
        base = .40 * (1 - tip) + .05 * tip
        return base, base * 1.02, base
    m_fin = mat(f'{P}_Fin', image(f'{P}_fin', 64, 128, fin_fill), rough=.45)
    m_eye = mat(f'{P}_Eye', None, (.02, .02, .025), .08)

    n_sec, n_ring = 36, 24
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    rings = []
    for i in range(n_sec + 1):
        t = i / n_sec
        if t < .1:
            r = .035 + .02 * t / .1
        elif t < .62:
            r = .055 + .105 * math.sin((t - .1) / .52 * math.pi / 2)
        elif t < .9:
            r = .16 - .06 * ((t - .62) / .28) ** 1.4
        else:
            r = .10 * max(0.0, 1 - ((t - .9) / .1) ** 1.8) ** .6
        r = max(r, .01)
        zc = -.03 * max(0.0, (t - .85) / .15)   # snout slightly down-turned
        ring = []
        for k in range(n_ring):
            a = TAU * k / n_ring
            s = math.sin(a)
            ring.append(bm.verts.new((r * .78 * math.cos(a), t * L, zc + r * s * (1.0 if s > 0 else .82))))
        rings.append(ring)
    for i in range(n_sec):
        for k in range(n_ring):
            k2 = (k + 1) % n_ring
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
            for lp, (uu, vv) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                lp[uv].uv = (((uu / n_ring) + .25) % 1 if uu < n_ring else 1.25 % 1 + (0 if k2 else 0), vv / n_sec)
    tip = bm.verts.new((0, L + .01, -.03))
    for k in range(n_ring):
        bm.faces.new((rings[-1][k], rings[-1][(k + 1) % n_ring], tip))
    tail = bm.verts.new((0, -.01, 0))
    for k in range(n_ring):
        bm.faces.new((rings[0][(k + 1) % n_ring], rings[0][k], tail))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    body = obj(bm, 'body', m)
    body.modifiers.new('sub', 'SUBSURF').levels = 1

    def fin(name, pts, thick, loc, rot):
        bm2 = bmesh.new()
        uv2 = bm2.loops.layers.uv.new()
        zs = [z for _, z in pts]
        lo, hi = min(zs), max(zs)
        base_z = 0.0
        span = max(abs(hi - base_z), abs(lo - base_z), 1e-3)
        vs = [bm2.verts.new((x, 0, z)) for x, z in pts]
        f = bm2.faces.new(vs)
        for lp in f.loops:
            lp[uv2].uv = (.5, abs(lp.vert.co.z - base_z) / span)
        bmesh.ops.triangulate(bm2, faces=bm2.faces)
        o = obj(bm2, name, m_fin)
        md = o.modifiers.new('s', 'SOLIDIFY')
        md.thickness = thick
        md.offset = 0
        o.modifiers.new('sub', 'SUBSURF').levels = 2
        place(o, loc, rot)
        return o
    up = (0, 0, math.pi / 2)
    # First dorsal: tall, swept back, black tip.
    fin('dorsal1', [(.15, 0), (.07, .1), (-.03, .2), (-.07, .2), (-.06, .13), (-.09, .04), (-.13, 0)], .018, (0, .9, .13), up)
    fin('dorsal2', [(.04, 0), (.0, .035), (-.03, .05), (-.04, .03), (-.05, 0)], .01, (0, .33, .05), up)
    fin('anal', [(.04, 0), (.0, -.035), (-.03, -.05), (-.04, -.03), (-.05, 0)], .01, (0, .3, -.045), up)
    for s in (-1, 1):
        fin('pectoral', [(.12, 0), (.02, -.08), (-.08, -.26), (-.11, -.25), (-.06, -.12), (-.06, 0)], .016,
            (s * .1, 1.08, -.07), (math.radians(-55) * s, 0, math.pi / 2))
        fin('pelvic', [(.05, 0), (.0, -.04), (-.05, -.07), (-.07, -.05), (-.06, 0)], .01,
            (s * .045, .52, -.07), (math.radians(-30) * s, 0, math.pi / 2))
    # Heterocercal tail: long upper lobe, shorter lower lobe; black tips.
    fin('caudal', [(.04, .03), (-.12, .16), (-.26, .3), (-.3, .28), (-.2, .1), (-.1, .0), (-.17, -.13), (-.2, -.15),
                   (-.12, -.11), (.04, -.03)], .02, (0, .02, 0), up)
    for s in (-1, 1):
        e = G.lathe([(0, -.008), (.009, -.005), (.009, .005), (0, .008)], m_eye, 12, 'eye')
        place(e, (s * .058, 1.47, .015), (0, math.pi / 2, 0))
    finish(P, keep_base=False)


# ---------------------------------------------------------------- algae
def kelp(P, H, blades, seed):
    reset()
    rnd = random.Random(seed)
    m_st = mat(f'{P}_Stipe', None, (.34, .27, .1), .6)

    def blade_fill(u, v):
        vein = np.exp(-((u - .5) ** 2) / .002) * .18
        k = .8 + .2 * np.sin(v * 60 + u * 9) * .5 + vein
        return .42 * k, .36 * k, .12 * k
    m_bl = two_sided(mat(f'{P}_Blade', image(f'{P}_blade', 64, 256, blade_fill), rough=.45))
    m_bd = mat(f'{P}_Bladder', None, (.5, .42, .15), .3)
    pts = []
    lean = Vector((rnd.uniform(-.15, .15), rnd.uniform(-.15, .15), 0))
    for i in range(9):
        t = i / 8
        pts.append(Vector((math.sin(t * 2.4 + seed) * .08 + lean.x * t * t * H, math.cos(t * 1.9 + seed) * .06 + lean.y * t * t * H, t * H)))
    tube('stipe', [tuple(p) for p in pts], .011, m_st, taper=.55)
    # Holdfast at the foot.
    for k in range(7):
        a = TAU * k / 7 + rnd.uniform(-.3, .3)
        tube('hold', [(0, 0, .04), (math.cos(a) * .06, math.sin(a) * .06, .015), (math.cos(a) * .11, math.sin(a) * .11, 0)], .007, m_st, taper=.4)
    for b in range(blades):
        t = .12 + .86 * b / blades
        i = min(int(t * 8), 7)
        f = t * 8 - i
        base = pts[i].lerp(pts[i + 1], f)
        a = b * 2.4 + rnd.uniform(-.4, .4)
        out = Vector((math.cos(a), math.sin(a), 0))
        ln = rnd.uniform(.35, .6) * (1.15 - .4 * t)
        path = [tuple(base + out * (ln * s) + Vector((0, 0, ln * s * .7 + .05 * math.sin(s * 3)))) for s in [j / 10 for j in range(11)]]
        ribbon('blade', path, lambda s: .065 * math.sin(math.pi * min(1, s * 1.1 + .05)) ** .6 + .004, m_bl, ruffle=.25)
        bd = G.lathe([(0, 0), (.014, .006), (.018, .02), (.011, .034), (0, .038)], m_bd, 12, 'bladder')
        place(bd, tuple(base + out * .012 - Vector((0, 0, .02))))
    finish(P)


def kelp_a():
    kelp('Sea_kelp_a', 1.6, 16, 3)


def kelp_b():
    kelp('Sea_kelp_b', 2.4, 22, 7)


def seagrass():
    reset()
    P = 'Sea_seagrass'
    rnd = random.Random(11)

    def fill(u, v):
        k = .75 + .25 * v
        return .16 * k + .1 * v, .42 * k, .12 * k
    m = two_sided(mat(f'{P}_Blade', image(f'{P}_blade', 32, 128, fill), rough=.5))
    for b in range(22):
        a = rnd.uniform(0, TAU)
        r0 = rnd.uniform(0, .07)
        base = Vector((math.cos(a) * r0, math.sin(a) * r0, 0))
        ln = rnd.uniform(.28, .5)
        bend = Vector((math.cos(a), math.sin(a), 0)) * rnd.uniform(.05, .16)
        path = [tuple(base + bend * (s * s) * ln * 2 + Vector((0, 0, s * ln))) for s in [j / 8 for j in range(9)]]
        ribbon('blade', path, lambda s: .0065 * (1 - .5 * s) + .001, m)
    finish(P)


# ---------------------------------------------------------------- animals
def anemone():
    reset()
    P = 'Sea_anemone'
    rnd = random.Random(5)
    m_col = mat(f'{P}_Column', None, (.62, .42, .36), .5)
    m_t = mat(f'{P}_Tentacle', image(f'{P}_tent', 16, 128, lambda u, v: (.78 - .2 * v, .55 - .25 * v, .62 + .1 * v)), rough=.35)
    G.lathe([(0, 0), (.07, 0), (.075, .02), (.06, .06), (.065, .09), (.085, .11), (.0, .105)], m_col, 32, 'column')
    for ring, (n, rr, ln) in enumerate(((22, .075, .12), (20, .055, .1), (16, .032, .08))):
        for k in range(n):
            a = TAU * k / n + ring * .3 + rnd.uniform(-.08, .08)
            o = Vector((math.cos(a), math.sin(a), 0))
            l = ln * rnd.uniform(.85, 1.15)
            curl = rnd.uniform(.2, .5)
            p0 = o * rr + Vector((0, 0, .108))
            pts = [p0, p0 + o * l * .35 + Vector((0, 0, l * .5)), p0 + o * l * (.75 + curl * .3) + Vector((0, 0, l * .8)),
                   p0 + o * l * (1.05 + curl * .4) + Vector((0, 0, l * (.75 - curl * .4)))]
            t = tube('tentacle', [tuple(p) for p in pts], .0055, m_t, taper=.35, res=5)
            # UV along the tentacle so the tips take the violet end of the texture.
            me = t.data
            uvl = me.uv_layers.new(name='UVMap') if not me.uv_layers else me.uv_layers[0]
            for poly in me.polygons:
                for li in poly.loop_indices:
                    z = me.vertices[me.loops[li].vertex_index].co.z
                    uvl.data[li].uv = (.5, min(1, max(0, (z - .108) / (l * .8))))
    finish(P)


def urchin():
    reset()
    P = 'Sea_urchin'
    rnd = random.Random(9)
    m_b = mat(f'{P}_Body', None, (.12, .06, .12), .35)
    m_s = mat(f'{P}_Spine', None, (.08, .04, .09), .25)
    G.lathe([(0, 0), (.04, .004), (.055, .025), (.05, .045), (.03, .06), (0, .064)], m_b, 28, 'body')
    n = 110
    for i in range(n):
        y = 1 - (i + .5) / n * 1.15      # upper sphere and the sides
        if y < -.15:
            continue
        r = math.sqrt(max(0, 1 - y * y))
        a = i * math.pi * (3 - math.sqrt(5))
        d = Vector((math.cos(a) * r, math.sin(a) * r, y))
        base = Vector((0, 0, .032)) + Vector((d.x * .05, d.y * .05, d.z * .032))
        ln = rnd.uniform(.08, .14)
        sp = G.lathe([(0, 0), (.0025, 0), (.0, ln)], m_s, 6, 'spine')
        sp.rotation_mode = 'QUATERNION'
        sp.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
        sp.location = base
    finish(P)


def starfish():
    reset()
    P = 'Sea_starfish'

    def fill(u, v):
        dots = (np.mod(u * 40, 1) - .5) ** 2 + (np.mod(v * 40, 1) - .5) ** 2 < .07
        k = np.where(dots, 1.15, .9)
        return .86 * k, .32 * k, .14 * k
    m = mat(f'{P}_Skin', image(f'{P}_skin', 128, 128, fill), rough=.6)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    na, nr = 120, 12

    def arm(t):
        return .025 + .095 * ((.5 + .5 * math.cos(5 * t)) ** 2.2)
    top = []
    for j in range(1, nr + 1):
        s = j / nr
        row = []
        for i in range(na):
            t = TAU * i / na
            R = arm(t) * s
            h = .024 * (1 - s ** 1.6) * (.55 + .45 * (.5 + .5 * math.cos(5 * t))) + .004
            row.append(bm.verts.new((R * math.cos(t), R * math.sin(t), h)))
        top.append(row)
    c = bm.verts.new((0, 0, .03))
    for i in range(na):
        bm.faces.new((c, top[0][i], top[0][(i + 1) % na]))
    for j in range(nr - 1):
        for i in range(na):
            bm.faces.new((top[j][i], top[j + 1][i], top[j + 1][(i + 1) % na], top[j][(i + 1) % na]))
    bot = [bm.verts.new((v.co.x, v.co.y, 0)) for v in top[-1]]
    for i in range(na):
        bm.faces.new((top[-1][i], bot[i], bot[(i + 1) % na], top[-1][(i + 1) % na]))
    bm.faces.new(list(reversed(bot)))
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = (lp.vert.co.x * 4 + .5, lp.vert.co.y * 4 + .5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj(bm, 'star', m)
    finish(P)


def sponge():
    reset()
    P = 'Sea_sponge'
    rnd = random.Random(4)

    def fill(u, v):
        n = np.sin(u * 151 + np.sin(v * 37) * 3) * np.sin(v * 97 + np.sin(u * 59) * 3) + .35 * np.sin(u * 23 + v * 31)
        pores = np.clip((n - .55) * 5, 0, 1)
        tone = .9 + .1 * np.sin(v * 7 + u * 3)
        k = (1 - .45 * pores) * tone
        return .9 * k, .58 * k, .14 * k
    m = mat(f'{P}_Skin', image(f'{P}_skin', 128, 128, fill), rough=.8)
    for k, (dx, dy, h, r) in enumerate(((0, 0, .42, .06), (.09, .03, .3, .05), (-.06, .07, .24, .045), (.02, -.08, .18, .04))):
        prof = [(0, 0), (r * .8, 0), (r, h * .3), (r * 1.15, h * .85), (r * 1.2, h), (r * .9, h), (r * .82, h * .75), (r * .7, h * .5), (0, h * .45)]
        o = G.lathe(prof, m, 24, 'tube')
        place(o, (dx, dy, 0), (rnd.uniform(-.12, .12), rnd.uniform(-.12, .12), 0))
    finish(P)


ALL = {'shark': shark, 'kelp_a': kelp_a, 'kelp_b': kelp_b, 'seagrass': seagrass, 'anemone': anemone, 'urchin': urchin,
       'starfish': starfish, 'sponge': sponge}
if __name__ == '__main__':
    for n in sys.argv[1:] or list(ALL):
        ALL[n]()
    print('gen_seafloor ok')
