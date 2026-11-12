"""Eight sea fish for the pier fishing game, modelled with bpy (no Blender install needed).

Each fish is ONE mesh with five materials (body, mouth, fins, eye, teeth):
  - body: 150 elliptical cross sections x 32 sides, own dorsal/ventral/width profile per species, mouth cut as a real
    slit (upper and lower jaw are separate rows of vertices and the lower jaw is rotated open), raised gill cover,
    eye socket, optional keel of scutes;
  - fins: thin blades with thickness built from a fan of rays (base line follows the body profile);
  - eyes: spheres seated in the socket with an iris/pupil texture;
  - texture 1024x512 drawn with numpy (gradient, overlapping scales, species marks), planar profile UV.
Convention: fish along X, head at +X, lying flat, the side seen by the player is -Y, centred on the origin, metres.
Output: D:/Assets/Mare/mare_fish_<id>/mare_fish_<id>.glb + info.json (via gen_custom_furniture.export) and the
UI profile pictures D:/Assets/Mare/fish_icons/<id>.png (head on the LEFT, transparent background).
Run: python gen_fish.py [id ...]     (bpy venv: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I)
"""
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_custom_furniture import reset, export, OUT   # noqa: E402

TMP = Path('D:/CodexTemp/claude/fish')
ICONS = OUT / 'fish_icons'
NSEC, NSIDE = 150, 32          # cross sections x sides
HALF = NSIDE // 2              # ring index of the -Y flank (theta = pi)
FIN_TH = .0015


# ---------------------------------------------------------------- numeric helpers
def pchip(xs, ys):
    xs = np.array(xs, float)
    ys = np.array(ys, float)
    h = np.diff(xs)
    d = np.diff(ys) / h
    m = np.zeros(len(xs))
    m[0], m[-1] = d[0], d[-1]
    for k in range(1, len(xs) - 1):
        if d[k - 1] * d[k] > 0:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k])

    def f(t):
        t = np.asarray(t, float)
        k = np.clip(np.searchsorted(xs, t) - 1, 0, len(xs) - 2)
        hh = h[k]
        s = (t - xs[k]) / hh
        return ((2 * s ** 3 - 3 * s ** 2 + 1) * ys[k] + (s ** 3 - 2 * s ** 2 + s) * hh * m[k]
                + (-2 * s ** 3 + 3 * s ** 2) * ys[k + 1] + (s ** 3 - s ** 2) * hh * m[k + 1])
    return f


def ss(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def soft(d, r, s):
    """1 inside radius r, falling to 0 over s."""
    return 1 - ss(r, r + s, d)


def mix(col, rgb, a):
    a = np.asarray(a)[..., None]
    return col * (1 - a) + np.array(rgb, float)[None, None, :] * a


def vnoise(X, Z, sc, seed):
    g = np.random.default_rng(seed).random((64, 64)).astype(np.float32)
    x, z = X / sc, Z / sc
    ix, iz = np.floor(x).astype(int), np.floor(z).astype(int)
    fx, fz = x - ix, z - iz
    fx, fz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a, b = g[iz % 64, ix % 64], g[iz % 64, (ix + 1) % 64]
    c, d = g[(iz + 1) % 64, ix % 64], g[(iz + 1) % 64, (ix + 1) % 64]
    return (a * (1 - fx) + b * fx) * (1 - fz) + (c * (1 - fx) + d * fx) * fz


def hash2(m, k, seed):
    return np.modf(np.sin(m * 127.1 + k * 311.7 + seed * 74.7) * 43758.5453)[0] % 1.0


# ---------------------------------------------------------------- textures
def scales(Xp, Zp, ws, seed=1):
    """Overlapping scales: the head-most scale that contains the pixel wins, so rear arcs show (free edges)."""
    rs = .55 * ws
    Rx, Rz = .85 * ws, 1.25 * rs
    best = np.full(Xp.shape, -1e9)
    dd = np.ones(Xp.shape)
    tone = np.full(Xp.shape, .5)
    rear = np.zeros(Xp.shape)
    k0 = np.floor(Zp / rs).astype(int)
    for dk in range(-2, 3):
        k = k0 + dk
        cz = (k + .5) * rs
        mc = np.floor(Xp / ws - .5 * (k % 2)).astype(int)
        for dm in range(-1, 3):
            m = mc + dm
            cx = (m + .5 * (k % 2) + .5) * ws
            dx, dz = (Xp - cx) / Rx, (Zp - cz) / Rz
            d = np.sqrt(dx * dx + dz * dz)
            win = (d < 1) & (cx > best)
            best = np.where(win, cx, best)
            dd = np.where(win, d, dd)
            tone = np.where(win, hash2(m, k, seed), tone)
            rear = np.where(win, ss(.1, -.5, dx), rear)
    return dd, tone, rear


def gradient(V, stops):
    vs = [s[0] for s in stops]
    return np.stack([np.interp(V, vs, [s[1][c] for s in stops]) for c in range(3)], -1)


class Ctx:
    pass


def body_texture(sp):
    W, H = 1024, 512
    L, Lb = sp['L'], sp['bf'] * sp['L']
    c = Ctx()
    c.sp, c.L, c.Lb = sp, L, Lb
    t = (np.arange(W) + .5) / W
    v = (np.arange(H) + .5) / H
    c.T = t[None, :] * np.ones((H, 1))
    c.V = v[:, None] * np.ones((1, W))
    Hl = (sp['ftop'](t) - sp['fbot'](t)) * L
    c.Hl = Hl[None, :] * np.ones((H, 1))
    c.Xp, c.Zp = c.T * Lb, c.V * c.Hl
    col = gradient(c.V, sp['grad'])
    # slow colour drift along the body so the silver is never flat
    col = col * (1 + .05 * (vnoise(c.Xp, c.Zp, .05 * L, 3) - .5))[..., None]
    sc = sp['scale']
    sc = dict(sc, str=sc['str'] * .5)
    if sc['str'] > 0:
        dd, tone, rear = scales(c.Xp, c.Zp, sc['ws'] * L, seed=sp['seed'])
        head = 1 - .75 * ss(sp['tg'] - .01, sp['tg'] + .02, c.T)
        rim = ss(.55, 1.0, dd) * (.35 + .65 * rear)
        shade = (1 + sc['tone'] * (tone - .5)) * (1 - sc['rim'] * rim) * (1 + .10 * (1 - dd) * sc['str'])
        col = col * (1 + (shade - 1)[..., None] * (sc['str'] * head)[..., None])
        # faint bright edge on top of each rear arc: wet shine
        col = col + (.05 * sc['str'] * ss(.8, .92, dd) * (1 - ss(.92, 1., dd)) * head)[..., None]
    c.col = col
    opercle(c, sp['oper'], sp.get('oper_a', .3))
    if 'paint' in sp:
        sp['paint'](c)
    # tip of the snout and the lips a bit darker
    c.col = mix(c.col, (.12, .08, .07), .35 * ss(.975, .995, c.T))
    return np.clip(c.col, 0, 1)


def opercle_edge(c):
    """Rear edge of the gill cover: a soft arc, centre towards the head (open to the rear)."""
    return c.sp['tg'] + .03 * np.clip(1 - ((c.V - .5) / .40) ** 2, 0, 1)


def opercle(c, color, a):
    T, V = c.T, c.V
    edge = opercle_edge(c)
    m = ss(edge - .006, edge + .008, T) * (1 - ss(edge + .08, edge + .15, T)) * soft(np.abs(V - .5), .34, .12)
    c.col = mix(c.col, color, a * m)
    g = np.exp(-((T - (edge - .005)) / .006) ** 2) * soft(np.abs(V - .5), .36, .05) * (T < edge + .003)
    c.col = c.col * (1 - .14 * g)[..., None]


def eye_texture(iris, ring):
    n = 256
    y, x = np.mgrid[0:n, 0:n]
    x, y = (x + .5) / n - .5, (y + .5) / n - .5
    r = np.sqrt(x * x + y * y)
    ang = np.arctan2(y, x)
    col = np.zeros((n, n, 3))
    col[:] = ring
    ir = np.array(iris)
    streak = .85 + .15 * np.sin(ang * 22)
    ic = ir[None, None, :] * streak[..., None] * (1 - .35 * ss(.30, .40, r))[..., None]
    mask = (r < .38)[..., None]
    col = np.where(mask, ic, col)
    col = np.where(((r < .385) & (r > .35))[..., None], ir[None, None, :] * .35, col)   # limbus
    col = np.where((r < .17)[..., None], np.array([.01, .01, .012])[None, None, :], col)   # pupil
    hl = np.sqrt((x + .09) ** 2 + (y - .10) ** 2)
    col = np.where((hl < .035)[..., None], 1.0, col)
    return np.clip(col, 0, 1)


def fin_texture(base, mid, tip, ray, edge):
    W, H = 128, 256
    u = (np.arange(W) + .5) / W
    v = (np.arange(H) + .5) / H
    U, V = u[None, :] * np.ones((H, 1)), v[:, None] * np.ones((1, W))
    col = gradient(V, [(0, base), (.35, mid), (1, tip)])
    line = np.exp(-((U - .5) / .10) ** 2)
    col = col * (1 - ray * line)[..., None]
    col = col * (1 + .10 * (1 - line) * (1 - V))[..., None]          # membrane a little lighter near the base
    col = col * (1 - edge * ss(.90, 1.0, V))[..., None]
    return np.clip(col, 0, 1)


def make_image(name, arr, path):
    h, w = arr.shape[:2]
    lin = np.where(arr <= .04045, arr / 12.92, ((arr + .055) / 1.055) ** 2.4)
    rgba = np.concatenate([lin, np.ones((h, w, 1))], 2).astype(np.float32)
    im = bpy.data.images.new(name, w, h, alpha=False)
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = str(path)
    im.file_format = 'PNG'
    im.save()
    return im


def img_material(name, im, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = im
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = 0.0
    return m


def flat_material(name, rgb, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    lin = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb]
    b.inputs['Base Color'].default_value = (*lin, 1)
    b.inputs['Roughness'].default_value = rough
    return m


# ---------------------------------------------------------------- species painters (marks on top of the base)
def paint_sardinha(c):
    g = soft(np.abs(c.V - .60), .02, .035) * ss(.12, .3, c.T) * (1 - ss(.74, .78, c.T))
    c.col = mix(c.col, (.86, .70, .34), .32 * g)
    # faint dark spots along the upper flank, behind the gill cover
    for i in range(6):
        cx, cz = (.66 - i * .045) * c.Lb, .70 * c.Hl[0, 0]
        d = np.sqrt((c.Xp - cx) ** 2 + ((c.Zp - .70 * c.Hl) / 1.0) ** 2)
        c.col = mix(c.col, (.12, .24, .30), .30 * soft(d, .0016 * c.L / .16, .0014 * c.L / .16))


def paint_pargo(c):
    # tiny bluish pearls on the flank
    cell = .030 * c.L
    gx, gz = np.floor(c.Xp / cell), np.floor(c.Zp / cell)
    ox, oz = hash2(gx, gz, 5), hash2(gx, gz, 9)
    on = hash2(gx, gz, 13) < .35
    d = np.sqrt((c.Xp - (gx + .2 + .6 * ox) * cell) ** 2 + (c.Zp - (gz + .2 + .6 * oz) * cell) ** 2)
    m = soft(d, .0016 * c.L, .0012 * c.L) * on * soft(np.abs(c.V - .55), .2, .12) * ss(.1, .2, c.T)
    c.col = mix(c.col, (.45, .66, .86), .55 * m)


def paint_robalo(c):
    edge = opercle_edge(c)
    arch = np.clip((c.T - .05) / (c.sp['tg'] - .05), 0, 1)
    vll = .50 + .09 * ss(0, .6, c.T) + .035 * np.sin(np.pi * arch)
    dz = np.abs(c.Zp - vll * c.Hl)
    hw = .0017 * c.L * (.35 + .65 * ss(.0, .25, c.T))
    m = soft(dz, hw, .0010 * c.L) * ss(.02, .08, c.T) * (1 - ss(edge - .006, edge, c.T))
    c.col = mix(c.col, (.04, .04, .045), .95 * m)
    # dusky back, pale chin
    c.col = mix(c.col, (.30, .32, .27), .25 * ss(.70, .95, c.V))


def paint_cioba(c):
    dx, dz = (c.Xp - .47 * c.Lb) / (.0125 * c.L), (c.Zp - .66 * c.Hl) / (.0115 * c.L)
    c.col = mix(c.col, (.07, .06, .06), .97 * soft(np.sqrt(dx * dx + dz * dz), 1.0, .35))
    # blue line under the eye
    y = .46 + .08 * np.clip((.975 - c.T) / .10, 0, 1.2) ** 2
    m = soft(np.abs(c.V - y) * c.Hl / c.L, .0014, .0012) * ss(.872, .885, c.T) * (1 - ss(.972, .978, c.T))
    c.col = mix(c.col, (.40, .62, .88), .85 * m)
    # faint yellow-rose streaks following the scale rows
    st = .5 + .5 * np.sin(c.Zp / (.0095 * c.L) * 2 * np.pi)
    c.col = mix(c.col, (.88, .70, .45), .10 * st * soft(np.abs(c.V - .45), .2, .15))


def paint_garoupa(c):
    L = c.L
    n1 = vnoise(c.Xp, c.Zp, .070 * L, 11) * .65 + vnoise(c.Xp, c.Zp, .030 * L, 12) * .35
    dark = ss(.56, .66, n1)
    light = ss(.40, .30, n1)
    c.col = mix(c.col, (.28, .18, .12), .6 * dark)
    c.col = mix(c.col, (.72, .60, .45), .55 * light * (1 - dark))
    sp = vnoise(c.Xp, c.Zp, .013 * L, 15)
    c.col = mix(c.col, (.16, .09, .06), .65 * ss(.74, .80, sp) * soft(np.abs(c.V - .5), .40, .1))
    # darker head with pale mottles
    h = ss(c.sp['tg'], c.sp['tg'] + .05, c.T)
    c.col = mix(c.col, (.45, .32, .22), .20 * h)
    # faint broad bars
    bars = .5 + .5 * np.cos((c.T - .55) * 2 * np.pi * 4.2)
    c.col = mix(c.col, (.24, .15, .10), .18 * bars * (c.T > .1) * (c.T < .78))


def paint_carapeba(c):
    for k, vv in enumerate((.30, .40, .50, .60, .70)):
        m = soft(np.abs(c.V - vv) * c.Hl / c.L, .0018, .0016) * ss(.12, .25, c.T) * (1 - ss(.70, .78, c.T))
        c.col = mix(c.col, (.42, .44, .38), .12 * m)
    c.col = mix(c.col, (.50, .55, .36), .22 * ss(.72, .95, c.V))


def paint_xareu(c):
    tg = c.sp['tg']
    dx, dz = (c.T - (tg + .05)) * c.Lb / (.0060 * c.L), (c.V - .62) * c.Hl / (.0105 * c.L)
    c.col = mix(c.col, (.04, .05, .05), .95 * soft(np.sqrt(dx * dx + dz * dz), 1.0, .4))
    vll = .56 + .08 * np.sin((c.T - .35) * 3.0) * ss(.3, .6, c.T) + .02
    vll = np.where(c.T < .45, .5 + .03 * ss(.1, .45, c.T), vll)
    dzl = np.abs(c.Zp - vll * c.Hl)
    thick = .0020 * c.L + .0040 * c.L * (1 - ss(.02, .40, c.T))
    m = soft(dzl, thick, .0014 * c.L) * ss(.02, .06, c.T) * (1 - ss(tg - .004, tg + .002, c.T))
    saw = .5 + .5 * np.cos(2 * np.pi * c.Xp / (.020 * c.L))
    sc = (1 - ss(.30, .42, c.T))
    c.col = mix(c.col, (.16, .22, .20), m * (.45 + .45 * sc * saw))
    c.col = mix(c.col, (.93, .91, .72), .10 * soft(np.abs(c.V - .30), .08, .15) * ss(.1, .3, c.T))


def paint_espada(c):
    streak = vnoise(c.Xp * .12, c.Zp * 3.0, .06 * c.L, 21)
    c.col = c.col * (1 + .05 * (streak - .5))[..., None]
    c.col = mix(c.col, (.42, .46, .52), .35 * ss(.80, 1.0, c.V))
    

# ---------------------------------------------------------------- species table (heights/widths: fractions of total L)
TT = [0, .06, .16, .32, .50, .66, .80, .90, .97, 1]
SPECIES = {
    'sardinha': dict(
        name='Sardinha', L=.16, bf=.83, seed=2,
        t=TT, top=[.012, .014, .040, .080, .104, .108, .094, .068, .040, .020],
        bot=[-.012, -.014, -.042, -.085, -.110, -.112, -.098, -.070, -.040, -.024],
        wid=[.008, .012, .028, .050, .062, .064, .056, .040, .024, .012],
        tg=.76, mouth=dict(tc=.935, gape=12, f=.40, prog=0), eye=(.895, .12, .018),
        iris=(.92, .80, .45), ring=(.18, .20, .20),
        grad=[(0, (.92, .93, .92)), (.30, (.90, .92, .92)), (.50, (.80, .85, .86)), (.70, (.55, .68, .70)),
              (.84, (.20, .40, .46)), (1, (.09, .22, .32))],
        scale=dict(ws=.036, str=1.0, rim=.34, tone=.20), oper=(.95, .92, .78), oper_a=.35, paint=paint_sardinha,
        fin=dict(base=(.62, .68, .66), mid=(.68, .74, .72), tip=(.50, .56, .56), ray=.35, edge=.25),
        fins=[
            dict(kind='dorsal', t1=.60, t0=.40, hs=[(0, .075), (.4, .062), (1, .042)], lean=(22, 38), rays=14),
            dict(kind='anal', t1=.34, t0=.17, hs=[(0, .035), (.4, .040), (1, .034)], lean=(25, 40), rays=14),
            dict(kind='caudal', spread=30, prof=[(0, .120), (.5, .150), (1, .200)], rays=26, ext=.01),
            dict(kind='pair', t=.80, z=(-.060, -.034), phi=(-8, -26), flare=16, prof=[(0, .062), (.5, .056), (1, .044)], rays=12),
            dict(kind='pair', t=.52, z=(-0.100, -0.090), phi=(-12, -34), flare=14, k=1.9, belly=True, prof=[(0, .040), (1, .030)], rays=8),
        ]),
    'pargo': dict(
        name='Pargo', L=.35, bf=.80, seed=4,
        t=TT, top=[.030, .032, .075, .140, .198, .205, .180, .135, .075, .038],
        bot=[-.030, -.032, -.065, -.115, -.160, -.175, -.165, -.130, -.082, -.040],
        wid=[.012, .016, .040, .072, .090, .092, .082, .060, .036, .016],
        tg=.72, mouth=dict(tc=.90, gape=10, f=.36, prog=0), eye=(.86, .20, .021),
        iris=(.90, .62, .35), ring=(.30, .12, .10),
        grad=[(0, (.94, .92, .91)), (.28, (.92, .82, .80)), (.52, (.88, .67, .64)), (.78, (.82, .56, .54)),
              (1, (.68, .44, .44))],
        scale=dict(ws=.015, str=.9, rim=.30, tone=.18), oper=(.95, .70, .66), oper_a=.30, paint=paint_pargo,
        fin=dict(base=(.82, .60, .58), mid=(.84, .62, .60), tip=(.66, .46, .44), ray=.30, edge=.30),
        fins=[
            dict(kind='dorsal', t1=.84, t0=.20, hs=[(0, .066), (.2, .098), (.46, .095), (.56, .108), (.80, .092), (1, .040)],
                 lean=(26, 52), rays=24),
            dict(kind='anal', t1=.42, t0=.26, hs=[(0, .070), (.3, .088), (1, .052)], lean=(22, 45), rays=14),
            dict(kind='caudal', spread=36, prof=[(0, .120), (.5, .160), (1, .215)], rays=30, ext=.01),
            dict(kind='pair', t=.72, z=(-.015, -.085), phi=(30, -12), flare=16, prof=[(0, .130), (.5, .120), (1, .090)], rays=22),
            dict(kind='pair', t=.60, z=(-0.148, -0.136), phi=(-12, -34), flare=14, k=1.9, belly=True, prof=[(0, .088), (1, .060)], rays=10),
        ]),
    'robalo': dict(
        name='Robalo', L=.52, bf=.82, seed=6,
        t=[0, .06, .18, .34, .52, .68, .80, .90, .95, .985, 1],
        top=[.016, .018, .044, .082, .106, .108, .098, .074, .052, .034, .018],
        bot=[-.016, -.018, -.040, -.078, -.100, -.104, -.092, -.070, -.048, -.036, -.030],
        wid=[.008, .011, .026, .044, .054, .055, .050, .038, .026, .016, .010],
        tg=.80, mouth=dict(tc=.84, gape=11, f=.34, prog=.020), eye=(.905, .28, .0125),
        iris=(.86, .78, .45), ring=(.12, .14, .13),
        grad=[(0, (.93, .94, .93)), (.30, (.90, .92, .91)), (.50, (.82, .85, .83)), (.68, (.66, .70, .62)),
              (.84, (.45, .50, .38)), (1, (.30, .34, .26))],
        scale=dict(ws=.011, str=.9, rim=.30, tone=.16), oper=(.92, .93, .90), oper_a=.30, paint=paint_robalo,
        fin=dict(base=(.80, .72, .42), mid=(.78, .72, .48), tip=(.56, .52, .36), ray=.32, edge=.30),
        fins=[
            dict(kind='dorsal', t1=.72, t0=.50, hs=[(0, .060), (.3, .085), (1, .052)], lean=(22, 45), rays=9),
            dict(kind='dorsal', t1=.38, t0=.22, hs=[(0, .050), (.5, .046), (1, .030)], lean=(18, 35), rays=14),
            dict(kind='anal', t1=.34, t0=.22, hs=[(0, .048), (.4, .046), (1, .030)], lean=(18, 35), rays=14),
            dict(kind='caudal', spread=28, prof=[(0, .105), (.5, .138), (1, .170)], rays=26, ext=.01),
            dict(kind='pair', t=.79, z=(-.025, -.070), phi=(10, -22), flare=16, prof=[(0, .076), (.5, .070), (1, .050)], rays=14),
            dict(kind='pair', t=.70, z=(-.102, -.094), phi=(-32, -56), flare=22, prof=[(0, .062), (1, .042)], rays=7),
        ]),
    'cioba': dict(
        name='Cioba', L=.42, bf=.80, seed=8,
        t=TT, top=[.024, .026, .062, .118, .162, .170, .152, .112, .062, .034],
        bot=[-.024, -.026, -.058, -.104, -.148, -.160, -.150, -.118, -.072, -.042],
        wid=[.010, .014, .034, .060, .076, .078, .068, .050, .030, .014],
        tg=.74, mouth=dict(tc=.905, gape=10, f=.36, prog=0), eye=(.87, .22, .0165),
        iris=(.92, .45, .20), ring=(.30, .10, .08),
        grad=[(0, (.92, .86, .82)), (.28, (.88, .76, .72)), (.52, (.80, .62, .58)), (.72, (.62, .54, .40)),
              (.88, (.46, .44, .30)), (1, (.36, .35, .24))],
        scale=dict(ws=.013, str=.9, rim=.30, tone=.18), oper=(.88, .72, .66), oper_a=.30, paint=paint_cioba,
        fin=dict(base=(.72, .50, .44), mid=(.76, .52, .44), tip=(.58, .38, .34), ray=.28, edge=.30),
        fins=[
            dict(kind='dorsal', t1=.80, t0=.26, hs=[(0, .066), (.2, .092), (.45, .088), (.55, .102), (.80, .094), (1, .045)],
                 lean=(24, 50), rays=22),
            dict(kind='anal', t1=.34, t0=.22, hs=[(0, .068), (.4, .074), (1, .050)], lean=(18, 40), rays=11),
            dict(kind='caudal', spread=30, prof=[(0, .135), (.5, .150), (1, .190)], rays=28, ext=.01),
            dict(kind='pair', t=.74, z=(-.010, -.078), phi=(34, -10), flare=16, prof=[(0, .135), (.5, .120), (1, .085)], rays=19),
            dict(kind='pair', t=.62, z=(-0.136, -0.126), phi=(-12, -34), flare=14, k=1.9, belly=True, prof=[(0, .090), (1, .060)], rays=8),
        ]),
    'garoupa': dict(
        name='Garoupa', L=.72, bf=.86, seed=10,
        t=[0, .04, .12, .24, .38, .5, .62, .74, .86, .94, .985, 1],
        top=[.050, .064, .084, .110, .136, .156, .168, .158, .134, .098, .062, .040],
        bot=[-.050, -.063, -.080, -.102, -.126, -.144, -.158, -.148, -.122, -.090, -.060, -.045],
        wid=[.026, .036, .048, .064, .084, .100, .115, .110, .092, .066, .036, .022],
        tg=.58, mouth=dict(tc=.80, gape=12, f=.36, prog=.034), lip=.008, eye=(.86, .28, .025), mouthcol=(.20, .13, .09),
        iris=(.80, .62, .25), ring=(.14, .09, .06),
        grad=[(0, (.80, .70, .56)), (.30, (.70, .56, .42)), (.55, (.60, .45, .32)), (.80, (.50, .37, .26)),
              (1, (.40, .29, .20))],
        scale=dict(ws=.010, str=.35, rim=.22, tone=.12), oper=(.60, .46, .34), oper_a=.20, paint=paint_garoupa,
        fin=dict(base=(.56, .42, .30), mid=(.60, .45, .32), tip=(.40, .29, .20), ray=.32, edge=.35),
        fins=[
            dict(kind='dorsal', t1=.72, t0=.16, hs=[(0, .055), (.15, .075), (.5, .068), (.8, .074), (1, .042)], lean=(22, 40), rays=22),
            dict(kind='anal', t1=.34, t0=.14, hs=[(0, .060), (.4, .085), (1, .050)], lean=(15, 30), rays=12),
            dict(kind='caudal', spread=52, prof=[(0, .130), (.6, .125), (.9, .108), (1, .095)], rays=28, ext=.04, rounded=True),
            dict(kind='pair', t=.55, z=(-.010, -.100), phi=(42, -50), flare=18, prof=[(0, .090), (.5, .110), (1, .085)], rays=18),
            dict(kind='pair', t=.52, z=(0, 0), phi=(-12, -34), flare=14, k=1.9, belly=True, prof=[(0, .098), (1, .070)], rays=7),
        ]),
    'carapeba': dict(
        name='Carapeba', L=.20, bf=.80, seed=12,
        t=[0, .06, .16, .30, .45, .58, .70, .82, .92, .98, 1],
        top=[.024, .026, .060, .140, .206, .222, .200, .150, .092, .045, .030],
        bot=[-.024, -.026, -.055, -.120, -.180, -.200, -.178, -.132, -.082, -.050, -.034],
        wid=[.010, .012, .030, .055, .070, .074, .068, .052, .034, .016, .010],
        tg=.72, mouth=dict(tc=.955, gape=10, f=.32, prog=0), eye=(.87, .22, .020),
        iris=(.88, .80, .50), ring=(.18, .20, .18),
        grad=[(0, (.94, .94, .91)), (.30, (.90, .91, .88)), (.52, (.82, .84, .80)), (.74, (.66, .70, .58)),
              (.90, (.48, .52, .36)), (1, (.36, .40, .27))],
        scale=dict(ws=.030, str=.75, rim=.28, tone=.14), oper=(.92, .93, .88), oper_a=.30, paint=paint_carapeba,
        fin=dict(base=(.70, .72, .62), mid=(.74, .76, .64), tip=(.50, .52, .42), ray=.34, edge=.30),
        fins=[
            dict(kind='dorsal', t1=.74, t0=.22, hs=[(0, .112), (.15, .140), (.35, .115), (.55, .090), (1, .058)],
                 lean=(34, 56), rays=20),
            dict(kind='anal', t1=.36, t0=.20, hs=[(0, .078), (.3, .076), (1, .048)], lean=(24, 44), rays=12),
            dict(kind='caudal', spread=30, prof=[(0, .095), (.5, .120), (1, .150)], rays=24, ext=.01),
            dict(kind='pair', t=.69, z=(-.030, -.092), phi=(14, -22), flare=16, prof=[(0, .092), (.5, .086), (1, .060)], rays=14),
            dict(kind='pair', t=.58, z=(-0.182, -0.172), phi=(-12, -34), flare=14, k=1.9, belly=True, prof=[(0, .092), (1, .060)], rays=7),
        ]),
    'xareu': dict(
        name='Xareu', L=.60, bf=.83, seed=14,
        t=TT, top=[.014, .016, .052, .120, .168, .175, .160, .122, .062, .030],
        bot=[-.014, -.016, -.050, -.115, -.158, -.168, -.158, -.130, -.082, -.050],
        wid=[.007, .010, .026, .052, .068, .072, .066, .050, .030, .014],
        tg=.76, mouth=dict(tc=.90, gape=10, f=.36, prog=0), eye=(.905, .25, .0165),
        iris=(.88, .74, .30), ring=(.12, .13, .10),
        grad=[(0, (.90, .90, .80)), (.28, (.88, .89, .84)), (.50, (.80, .84, .82)), (.70, (.55, .66, .64)),
              (.86, (.30, .42, .44)), (1, (.22, .34, .38))],
        scale=dict(ws=.010, str=.35, rim=.2, tone=.10), oper=(.88, .90, .84), oper_a=.25, paint=paint_xareu,
        keel=dict(t0=.02, t1=.42, amp=.0055, n=14),
        fin=dict(base=(.60, .62, .50), mid=(.70, .70, .52), tip=(.48, .50, .40), ray=.30, edge=.30),
        fins=[
            dict(kind='dorsal', t1=.70, t0=.54, hs=[(0, .048), (.4, .064), (1, .030)], lean=(30, 52), rays=8),
            dict(kind='dorsal', t1=.48, t0=.16, hs=[(0, .062), (.2, .078), (.6, .045), (1, .026)], lean=(25, 48), rays=24),
            dict(kind='anal', t1=.48, t0=.16, hs=[(0, .062), (.2, .072), (.6, .042), (1, .026)], lean=(25, 48), rays=22),
            dict(kind='caudal', spread=24, prof=[(0, .150), (.5, .185), (1, .225)], rays=26, ext=.01),
            dict(kind='pair', t=.76, z=(.000, -.052), phi=(30, 12), flare=14, prof=[(0, .180), (.5, .130), (1, .050)], rays=16),
            dict(kind='pair', t=.64, z=(-0.148, -0.142), phi=(-12, -34), flare=14, k=1.9, belly=True, prof=[(0, .056), (1, .040)], rays=6),
        ]),
    'peixe_espada': dict(
        name='Peixe-espada', L=.85, bf=1.0, seed=16,
        t=[0, .04, .12, .30, .50, .65, .80, .90, .96, 1],
        top=[.0012, .0022, .0065, .020, .034, .038, .036, .030, .021, .009],
        bot=[-.0012, -.0022, -.0065, -.020, -.034, -.038, -.036, -.030, -.023, -.017],
        wid=[.0012, .0020, .0042, .0105, .0165, .0185, .0175, .0140, .0090, .0040],
        tg=.865, mouth=dict(tc=.885, gape=14, f=.46, prog=.014), eye=(.935, .30, .0105),
        iris=(.78, .80, .82), ring=(.10, .10, .11),
        grad=[(0, (.88, .90, .92)), (.30, (.84, .87, .90)), (.60, (.78, .81, .85)), (.85, (.66, .70, .76)),
              (1, (.52, .56, .64))],
        scale=dict(ws=.02, str=0, rim=0, tone=0), oper=(.90, .92, .95), oper_a=.25, paint=paint_espada,
        teeth=dict(n=4, length=.017),
        fin=dict(base=(.74, .72, .56), mid=(.80, .78, .60), tip=(.64, .62, .48), ray=.22, edge=.15),
        fins=[
            dict(kind='dorsal', t1=.88, t0=.012, hs=[(0, .024), (.15, .030), (1, .013)], k=1.0, lean=(55, 75), rays=60, ns=90),
            dict(kind='pair', t=.855, z=(-.018, -.030), phi=(-5, -20), flare=14, prof=[(0, .030), (1, .022)], rays=8),
        ]),
}


# ---------------------------------------------------------------- mesh building
class Builder:
    def __init__(self, sp):
        self.sp = sp
        self.L = sp['L']
        self.Lb = sp['bf'] * sp['L']
        self.x0 = self.L / 2 - self.Lb
        self.ftop = pchip(sp['t'], sp['top'])
        self.fbot = pchip(sp['t'], sp['bot'])
        self.fwid = pchip(sp['t'], sp['wid'])
        self.bm = bmesh.new()
        self.uv = {}
        self.mats = ['body', 'mouth', 'fin', 'eye', 'teeth']

    def vert(self, p, uv=(0, 0)):
        v = self.bm.verts.new(tuple(p))
        self.uv[v] = uv
        return v

    def face(self, vs, mat):
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return None
        f.material_index = self.mats.index(mat)
        return f

    # ---- body ---------------------------------------------------------------------------------------------
    def body(self):
        sp, L, Lb, x0 = self.sp, self.L, self.Lb, self.x0
        n, m = NSEC, NSIDE
        t = np.linspace(0, 1, n)
        top, bot, b = self.ftop(t) * L, self.fbot(t) * L, self.fwid(t) * L
        zc, a = (top + bot) / 2, (top - bot) / 2
        th = 2 * np.pi * np.arange(m) / m
        c, s = np.cos(th)[None, :], np.sin(th)[None, :]
        mo = sp['mouth']
        tc, f = mo['tc'], mo['f']
        wm = ss(tc - .10, tc, t)[:, None]
        hz0 = float(np.interp(tc, t, zc + (f - .5) * 2 * a))
        zfull = np.clip(hz0, bot + .15 * (top - bot), top - .15 * (top - bot))
        zm = zc + (zfull - zc) * wm[:, 0]
        dl = (zm - zc)[:, None]
        X = (x0 + t * Lb)[:, None] * np.ones((1, m))
        Z = zc[:, None] + a[:, None] * s + dl * (1 - s * s)
        Y = b[:, None] * c
        U = t[:, None] * np.ones((1, m))
        V = np.clip((Z - bot[:, None]) / (top - bot)[:, None], 0, 1)
        sgn = np.sign(c) * np.ones((n, 1))
        sw = np.abs(c) ** .8
        # gill cover: raised plate with an abrupt rear edge and a groove just behind it
        tg = sp['tg']
        E = ss(tg - .06, tg + .03, t) * (1 - ss(tg + .04, tg + .14, t))
        sn = np.clip((Z - zc[:, None]) / a[:, None], -1, 1)
        Y = Y + sgn * (.022 * b * E)[:, None] * np.sqrt(np.maximum(0, 1 - sn * sn)) * sw
        # eye
        te, sf, er = sp['eye']
        er *= L
        ex = x0 + te * Lb
        ie = int(round(te * (n - 1)))
        ring_z = Z[ie, HALF // 2:HALF + HALF // 2 + 1]     # j = 8..24, near side top -> bottom
        ring_y = np.abs(Y[ie, HALF // 2:HALF + HALF // 2 + 1])
        ez = zc[ie] + a[ie] * sf
        ys = float(np.interp(ez, ring_z[::-1], ring_y[::-1]))
        depth = .75 * er
        R = 1.9 * er
        dist = np.sqrt((X - ex) ** 2 + (Z - ez) ** 2)
        dep = np.cos(.5 * np.pi * np.clip(dist / R, 0, 1)) ** 2 * depth
        Y = Y - sgn * dep * (np.abs(c) > .05)
        self.eye_pos = (ex, ys - depth + .30 * er, ez, er)
        # keel of scutes (xareu)
        if 'keel' in sp:
            k = sp['keel']
            saw = ((t - k['t0']) * k['n'] / (k['t1'] - k['t0'])) % 1.0
            amp = k['amp'] * L * ss(k['t1'], k['t0'] + .05, t) * ((t > k['t0']) & (t < k['t1']))
            prof = amp * (.25 + .75 * saw)
            w = np.exp(-(((th + np.pi) % (2 * np.pi) - np.pi) / .16) ** 2) + np.exp(-((th - np.pi) / .16) ** 2)
            Y = Y + sgn * prof[:, None] * w[None, :]
        lip = sp.get('lip', 0)
        if lip:      # fleshy lips: a raised rim above and below the mouth slit
            wl = ss(tc, tc + .08, t) * (1 - ss(.985, 1.0, t))
            for dj, wt in ((1, 1.0), (2, .55), (-1, 1.0), (-2, .55)):
                for base in (0, HALF):
                    j = (base + dj) % m
                    Y[:, j] += sgn[:, j] * lip * L * wt * wl
        # jaws: lower half rotates open around the corner of the mouth; lower jaw may protrude
        ic = int(np.searchsorted(t, tc))
        hx = x0 + tc * Lb
        hz = float(np.interp(tc, t, zm))
        wj = ss(tc, tc + .75 * (1 - tc), t)[:, None]
        phi = np.radians(mo['gape']) * wj
        XL = hx + (X - hx) * np.cos(phi) + (Z - hz) * np.sin(phi) + mo['prog'] * L * wj
        ZL = hz - (X - hx) * np.sin(phi) + (Z - hz) * np.cos(phi)
        lower = np.zeros((n, m), bool)
        lower[:, HALF + 1:] = True
        Xf, Zf = np.where(lower, XL, X), np.where(lower, ZL, Z)
        # vertices
        vid = np.empty((n, m), object)
        lid = np.empty((n, m), object)
        for i in range(n):
            for j in range(m):
                p = (Xf[i, j], Y[i, j], Zf[i, j])
                v = self.vert(p, (U[i, j], V[i, j]))
                vid[i, j] = v
                lid[i, j] = v
                if i >= ic and j in (0, HALF):
                    lid[i, j] = self.vert((XL[i, j], Y[i, j], ZL[i, j]), (U[i, j], V[i, j]))
        for i in range(n - 1):
            for j in range(m):
                j2 = (j + 1) % m
                A = vid if j < HALF else lid
                self.face([A[i, j], A[i, j2], A[i + 1, j2], A[i + 1, j]], 'body')
        # mouth pocket
        mouth_mat = 'mouth'
        M = {}
        for j in (0, HALF):
            for i in range(ic, n):
                pu, pl = np.array(vid[i, j].co), np.array(lid[i, j].co)
                mid = (pu + pl) / 2
                mid[1] *= .35
                M[i, j] = self.vert(mid)
            for i in range(ic, n - 1):
                self.face([vid[i, j], vid[i + 1, j], M[i + 1, j], M[i, j]], mouth_mat)
                self.face([M[i, j], M[i + 1, j], lid[i + 1, j], lid[i, j]], mouth_mat)
        # caps: tail end (closed), snout (upper and lower jaw plus the pocket in between)
        self.face([vid[0, j] for j in range(m)][::-1], 'body')
        up = [vid[n - 1, j] for j in range(0, HALF + 1)]
        lo = [lid[n - 1, j] for j in range(HALF, m)] + [lid[n - 1, 0]]
        self.face(up, 'body')
        self.face(lo, 'body')
        self.face([vid[n - 1, HALF], vid[n - 1, 0], M[n - 1, 0], lid[n - 1, 0], lid[n - 1, HALF], M[n - 1, HALF]], mouth_mat)
        self.P = (Xf, Y, Zf, XL, ZL)
        self.grid = (t, zc, a, b)

    def surf_y(self, t, z):
        """Approximate half width of the body surface at (t, z) for fin roots."""
        zc = float(self.ftop(t) + self.fbot(t)) * self.L / 2
        a = float(self.ftop(t) - self.fbot(t)) * self.L / 2
        b = float(self.fwid(t)) * self.L
        sf = np.clip((z - zc) / a, -.97, .97)
        return b * math.sqrt(1 - sf * sf)

    # ---- eyes ---------------------------------------------------------------------------------------------
    def eyes(self):
        ex, ey, ez, er = self.eye_pos
        for sy in (-1, 1):
            r = bmesh.ops.create_uvsphere(self.bm, u_segments=28, v_segments=18, radius=er)
            vs = r['verts']
            for v in vs:
                x, y, z = v.co
                self.uv[v] = (.5 + x / (2 * er), .5 + z / (2 * er))
                v.co = (ex + x * 1.0, sy * ey + y * 1.0, ez + z)
            for f in {f for v in vs for f in v.link_faces}:
                f.material_index = self.mats.index('eye')

    # ---- teeth --------------------------------------------------------------------------------------------
    def teeth(self):
        tt = self.sp.get('teeth')
        if not tt:
            return
        Xf, Y, Zf, XL, ZL = self.P
        n = NSEC
        for k in range(tt['n']):
            i = n - 2 - 6 * k
            for j in (0, HALF):
                for upper in (True, False):
                    if upper:
                        p = np.array([Xf[i, j], Y[i, j] * .90, Zf[i, j]])
                        d = -1
                    else:
                        p = np.array([XL[i, j], Y[i, j] * .90, ZL[i, j]])
                        d = 1
                    ln = tt['length'] * self.L * (1.0 if k % 2 == 0 else .7)
                    r = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=True, segments=8, radius1=.0030 * self.L,
                                              radius2=0, depth=ln)
                    for v in r['verts']:
                        x, y, z = v.co
                        zz = z + ln / 2                      # 0 at the root, ln at the tip
                        v.co = (p[0] + x, p[1] + y, p[2] - zz if upper else p[2] + zz)
                        self.uv[v] = (0, 0)
                    for f in {f for v in r['verts'] for f in v.link_faces}:
                        f.material_index = self.mats.index('teeth')

    # ---- fins ---------------------------------------------------------------------------------------------
    def blade(self, P, rays):
        """P: (ns, nr, 3) points of the fin surface (j = 0 is the root). Thin solid with rim."""
        bm = self.bm
        ns, nr = P.shape[:2]
        Fv, Bv = {}, {}
        for i in range(ns):
            for j in range(nr):
                th = FIN_TH * (1 - .45 * j / (nr - 1))
                uv = (i / (ns - 1) * rays, j / (nr - 1))
                Fv[i, j] = self.vert(P[i, j] + np.array([0, -th / 2, 0]), uv)
                Bv[i, j] = self.vert(P[i, j] + np.array([0, th / 2, 0]), uv)
        for i in range(ns - 1):
            for j in range(nr - 1):
                self.face([Fv[i, j], Fv[i + 1, j], Fv[i + 1, j + 1], Fv[i, j + 1]], 'fin')
                self.face([Bv[i, j + 1], Bv[i + 1, j + 1], Bv[i + 1, j], Bv[i, j]], 'fin')
        for i in range(ns - 1):
            self.face([Fv[i, nr - 1], Fv[i + 1, nr - 1], Bv[i + 1, nr - 1], Bv[i, nr - 1]], 'fin')
            self.face([Bv[i, 0], Bv[i + 1, 0], Fv[i + 1, 0], Fv[i, 0]], 'fin')
        for j in range(nr - 1):
            self.face([Fv[0, j + 1], Fv[0, j], Bv[0, j], Bv[0, j + 1]], 'fin')
            self.face([Bv[ns - 1, j + 1], Bv[ns - 1, j], Fv[ns - 1, j], Fv[ns - 1, j + 1]], 'fin')

    def fan(self, base, dirs, lens, curve, nr=8):
        r = np.linspace(0, 1, nr)[None, :, None]
        base, dirs, lens = base[:, None, :], dirs[:, None, :], lens[:, None, None]
        return base + lens * (dirs * r + np.array(curve)[None, None, :] * r * r)

    def median_fin(self, sp_f, up):
        L, Lb, x0 = self.L, self.Lb, self.x0
        ns = sp_f.get('ns', 30)
        s = np.linspace(0, 1, ns)
        t = sp_f['t1'] + (sp_f['t0'] - sp_f['t1']) * s
        prof = self.ftop(t) if up else self.fbot(t)
        z = prof * L - (1 if up else -1) * .005 * L
        base = np.stack([x0 + t * Lb, np.zeros(ns), z], 1)
        hs = sp_f['hs']
        lens = pchip([h[0] for h in hs], [h[1] for h in hs])(s) * L * sp_f.get('k', .72)
        ang = np.radians(sp_f['lean'][0] + (sp_f['lean'][1] - sp_f['lean'][0]) * s)
        dz = 1 if up else -1
        dirs = np.stack([-np.sin(ang), np.zeros(ns), dz * np.cos(ang)], 1)
        P = self.fan(base, dirs, lens, (-.10, 0, 0))
        self.blade(P, sp_f['rays'])

    def caudal(self, sp_f):
        L, x0 = self.L, self.x0
        ns = 34
        s = np.linspace(0, 1, ns)
        u = 2 * s - 1
        zt, zb = float(self.ftop(0)) * L, float(self.fbot(0)) * L
        z = zb + (zt - zb) * s
        xb = x0 + (sp_f.get('ext', .01) + .004) * L
        base = np.stack([np.full(ns, xb), np.zeros(ns), z], 1)
        pr = sp_f['prof']
        lens = pchip([p[0] for p in pr], [p[1] for p in pr])(np.abs(u)) * L
        ang = np.radians(sp_f['spread']) * u
        dirs = np.stack([-np.cos(ang), np.zeros(ns), np.sin(ang)], 1)
        P = self.fan(base, dirs, lens, (-.03 * L, 0, 0), nr=10)
        self.blade(P, sp_f['rays'])

    def pair(self, sp_f):
        L, Lb, x0 = self.L, self.Lb, self.x0
        ns = 14
        s = np.linspace(0, 1, ns)
        t = sp_f['t']
        zhi, zlo = sp_f['z']
        if sp_f.get('belly'):
            zb = float(self.fbot(sp_f['t']))
            zhi, zlo = zb + .024, zb + .010
        z = (zhi + (zlo - zhi) * s) * L
        xr = x0 + t * Lb
        phi = np.radians(sp_f['phi'][0] + (sp_f['phi'][1] - sp_f['phi'][0]) * s)
        fl = math.radians(sp_f['flare'])
        pr = sp_f['prof']
        lens = pchip([p[0] for p in pr], [p[1] for p in pr])(s) * L * sp_f.get('k', 1.0)
        for sy in (-1, 1):
            ys = np.array([self.surf_y(t, zz) for zz in z]) * .94
            base = np.stack([np.full(ns, xr), sy * ys, z], 1)
            dirs = np.stack([-np.cos(phi) * math.cos(fl), np.full(ns, sy * math.sin(fl)), np.sin(phi) * math.cos(fl)], 1)
            P = self.fan(base, dirs, lens, (-.10 * L, 0, 0), nr=8)
            self.blade(P, sp_f['rays'])

    def fins(self):
        for fspec in self.sp['fins']:
            k = fspec['kind']
            if k == 'dorsal':
                self.median_fin(fspec, True)
            elif k == 'anal':
                self.median_fin(fspec, False)
            elif k == 'caudal':
                self.caudal(fspec)
            else:
                self.pair(fspec)


def build(sid):
    sp = SPECIES[sid]
    slug = f'mare_fish_{sid}'
    reset()
    TMP.mkdir(parents=True, exist_ok=True)
    bd = Builder(sp)
    sp['ftop'], sp['fbot'] = bd.ftop, bd.fbot
    bd.body()
    bd.eyes()
    bd.teeth()
    bd.fins()
    bm = bd.bm
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # report on outward normals of the body surface
    bad, tot = 0, 0
    for f in bm.faces:
        if f.material_index != 0:
            continue
        cx = f.calc_center_median()
        zc = float(bd.ftop(max(0, min(1, (cx.x - bd.x0) / bd.Lb))) + bd.fbot(max(0, min(1, (cx.x - bd.x0) / bd.Lb)))) * bd.L / 2
        out = Vector((0, cx.y, cx.z - zc))
        tot += 1
        if len(f.verts) > 4:      # caps: snout caps must face +X, the tail cap -X
            if (f.normal.x > 0) != (cx.x > bd.x0 + bd.Lb / 2):
                bad += 1
            continue
        if out.length > 1e-6 and f.normal.dot(out) < 0:
            bad += 1
    # scale so the bounding box is exactly the requested length and centre the model
    xs = [v.co.x for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    k = sp['L'] / (max(xs) - min(xs))
    cx, cz = (max(xs) + min(xs)) / 2, (max(zs) + min(zs)) / 2
    for v in bm.verts:
        v.co = ((v.co.x - cx) * k, v.co.y * k, (v.co.z - cz) * k)
    uvl = bm.loops.layers.uv.verify()
    for f in bm.faces:
        f.smooth = True
        for lp in f.loops:
            lp[uvl].uv = bd.uv.get(lp.vert, (0, 0))
    me = bpy.data.meshes.new(slug)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(slug, me)
    bpy.context.collection.objects.link(obj)
    # materials
    im_b = make_image('Body', body_texture(sp), TMP / f'{slug}_body.png')
    im_e = make_image('Eye', eye_texture(sp['iris'], sp['ring']), TMP / f'{slug}_eye.png')
    fn = sp['fin']
    im_f = make_image('Fin', fin_texture(fn['base'], fn['mid'], fn['tip'], fn['ray'], fn['edge']), TMP / f'{slug}_fin.png')
    for m in (img_material('Body', im_b, .30), flat_material('Mouth', sp.get('mouthcol', (.17, .07, .06)), .5),
              img_material('Fin', im_f, .45), img_material('Eye', im_e, .12), flat_material('Teeth', (.96, .95, .90), .2)):
        me.materials.append(m)
    me.update()
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    dims = [max(c[i] for c in bb) - min(c[i] for c in bb) for i in range(3)]
    export(slug, sp['name'])
    info = dict(id=sid, tris=tris, dims_m=[round(d, 4) for d in dims], bad_normals=bad, body_faces=tot, k=round(k, 4))
    print('FISH', json.dumps(info))
    return obj, info


# ---------------------------------------------------------------- pictures
def setup_render(res):
    sc = bpy.context.scene
    for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'CYCLES'):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    if sc.render.engine == 'CYCLES':
        sc.cycles.samples = 48
        sc.cycles.device = 'CPU'
    else:
        try:
            sc.eevee.taa_render_samples = 48
        except Exception:
            pass
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W')
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (.75, .78, .82, 1)
    bg.inputs['Strength'].default_value = .55
    sc.world = w
    for o in [o for o in bpy.data.objects if o.type in ('LIGHT', 'CAMERA')]:
        bpy.data.objects.remove(o)
    for rot, st in (((math.radians(48), 0, math.radians(12)), 2.6), ((math.radians(80), 0, math.radians(-25)), 1.1)):
        ld = bpy.data.lights.new('sun', 'SUN')
        ld.energy = st
        lo = bpy.data.objects.new('sun', ld)
        bpy.context.collection.objects.link(lo)
        lo.rotation_euler = rot
    return sc


def render_views(sid, L):
    sc = setup_render((1024, 512))
    cd = bpy.data.cameras.new('cam')
    cd.type = 'ORTHO'
    cd.ortho_scale = L / .90
    co = bpy.data.objects.new('cam', cd)
    bpy.context.collection.objects.link(co)
    co.location = (0, -3 * L - 1, 0)
    co.rotation_euler = (math.pi / 2, 0, 0)
    sc.camera = co
    ICONS.mkdir(parents=True, exist_ok=True)
    tmp = TMP / f'{sid}_raw.png'
    sc.render.filepath = str(tmp)
    bpy.ops.render.render(write_still=True)
    from PIL import Image, ImageOps
    im = Image.open(tmp).convert('RGBA')
    # camera at -Y looks towards +Y: +X (the head) lands on the right; mirror so every head is on the left
    ImageOps.mirror(im).save(ICONS / f'{sid}.png')
    # three-quarter view: from the front and above
    sc.render.resolution_x, sc.render.resolution_y = 900, 600
    cd.type = 'PERSP'
    cd.lens = 50
    d = Vector((.55, -1.0, .62)).normalized() * (1.45 * L + .05)
    co.location = d
    q = (-d).to_track_quat('-Z', 'Y')
    co.rotation_euler = q.to_euler()
    tmp3 = TMP / f'{sid}_3q.png'
    sc.render.filepath = str(tmp3)
    bpy.ops.render.render(write_still=True)


def sheets(ids):
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
    except Exception:
        font = ImageFont.load_default()

    def sheet(paths, size, out, cols=2):
        cw, ch = size
        rows = (len(ids) + cols - 1) // cols
        im = Image.new('RGB', (cw * cols, (ch + 32) * rows), (128, 128, 128))
        dr = ImageDraw.Draw(im)
        for k, sid in enumerate(ids):
            x, y = (k % cols) * cw, (k // cols) * (ch + 32)
            f = Image.open(paths(sid)).convert('RGBA')
            f.thumbnail((cw, ch))
            im.paste(f, (x + (cw - f.width) // 2, y + (ch - f.height) // 2), f)
            dr.text((x + 10, y + ch + 4), SPECIES[sid]['name'], fill=(255, 255, 255), font=font)
        im.save(out, quality=92)
    sheet(lambda s: ICONS / f'{s}.png', (700, 350), TMP / 'folha.jpg')
    sheet(lambda s: TMP / f'{s}_3q.png', (700, 490), TMP / 'folha_3q.jpg')


def main():
    ids = sys.argv[1:] or list(SPECIES)
    for sid in ids:
        obj, info = build(sid)
        render_views(sid, SPECIES[sid]['L'])
    sheets([s for s in SPECIES if (ICONS / f'{s}.png').exists() and (TMP / f'{s}_3q.png').exists()])


if __name__ == '__main__':
    main()
