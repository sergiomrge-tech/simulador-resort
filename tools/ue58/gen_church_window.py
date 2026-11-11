"""Cathedral window for the village church (11/11, Sergio: "coloque vidraça de catedral, ornamentada").

mare_church_window: pointed (equilateral) arch 1.24 m wide, sill at 1.5 m, apex at 5.37 m; moulded stone surround with
a hood mould and label stops, sloped sill on an apron, stone tracery (two lancets under a foiled oculus), iron saddle
bars, and one glass pane with an original stained-glass picture drawn here: jewel borders, diamond quarries, three
medallions per lancet, sunburst heads, a rose in the oculus, starred blue spandrels, black lead lines.
Origin on the wall face at ground level, under the middle of the window; front = -Y (out of the wall).
No free CC0 stained-glass asset was found (ambientCG: none; Poly Haven: church panoramas only).
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_church_window.py
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from gen_custom_furniture import OUT, box, export, finish, lathe, material, mesh_obj, reset, tube  # noqa: E402

SLUG = 'mare_church_window'
A = .62            # half width of the opening
Z0 = 1.5           # sill
ZS = 4.3           # springing of the main arch
APEX = ZS + A * math.sqrt(3)
MULL = .035        # half width of the middle mullion
B = (A - MULL) / 2  # half width of a lancet
LX = MULL + B      # lancet centre (+-)
ZL = 3.55          # springing of the lancets
OC = (0.0, 4.62)   # oculus centre (x, z)
OR = .33           # oculus radius
MED = (2.05, 2.75, 3.4)   # medallion heights


def arch_path(cx, half, z_bot, z_spring, off=0.0, n=14):
    """Pointed arch outline, bottom-left up over the apex down to bottom-right, pushed outwards by `off`."""
    pts = [(cx - half - off, z_bot)]
    R = 2 * half + off
    end = math.acos(-half / R)          # angle (from the right-hand centre) where the left arc reaches the axis
    for i in range(n + 1):
        t = math.pi - (math.pi - end) * i / n
        pts.append((cx + half + R * math.cos(t), z_spring + R * math.sin(t)))
    right = [(2 * cx - x, z) for x, z in reversed(pts[:-1])]
    return pts + right


def band(name, inner, outer, y_front, y_back, mat, uv=.8, closed=False):
    """Solid strip between two outlines with the same number of points (x, z), from y_front to y_back."""
    bm = bmesh.new()
    n = len(inner)
    rows = [[bm.verts.new((x, y, z)) for x, z in line] for line in (inner, outer) for y in (y_front, y_back)]
    fi, bi, fo, bo = rows[0], rows[1], rows[2], rows[3]
    last = n if closed else n - 1
    for i in range(last):
        j = (i + 1) % n
        bm.faces.new((fi[i], fi[j], fo[j], fo[i]))     # front
        bm.faces.new((bi[i], bo[i], bo[j], bi[j]))     # back
        bm.faces.new((fo[i], fo[j], bo[j], bo[i]))     # outer side
        bm.faces.new((fi[i], bi[i], bi[j], fi[j]))     # inner side
    if not closed:
        bm.faces.new((fi[0], fo[0], bo[0], bi[0]))
        bm.faces.new((fi[-1], bi[-1], bo[-1], fo[-1]))
    obj = mesh_obj(name, bm)
    return finish(obj, mat, uv, bevel=.006, seg=2, smooth=False)


def circle(cx, cz, r, n=40):
    return [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


# ---------------------------------------------------------------- stained glass picture
def _hash(a, b):
    return np.abs(np.sin(a * 127.1 + b * 311.7) * 43758.5453) % 1.0


def glass_image(W=1024, H=2048, ss=2):
    w, h = W * ss, H * ss
    xs = (np.arange(w) + .5) / w * 2 * A - A
    zs = Z0 + (1 - (np.arange(h) + .5) / h) * (APEX - Z0)
    X, Z = np.meshgrid(xs.astype(np.float32), zs.astype(np.float32))
    img = np.zeros((h, w, 3), np.float32)
    lead = np.zeros((h, w), bool)
    LW = .0075   # half width of a lead line (m)
    ruby, sapph, gold, emer = np.array((.62, .05, .09)), np.array((.07, .19, .64)), np.array((.93, .68, .12)), np.array((.08, .46, .22))
    pale = np.array([(.62, .84, .86), (.94, .83, .55), (.70, .88, .68), (.93, .92, .86), (.78, .74, .90)], np.float32)
    deep = np.array((.05, .11, .40))

    def paint(mask, colour, tone=None):
        c = np.asarray(colour, np.float32)
        img[mask] = c if tone is None else c * tone[mask][:, None]

    # spandrels: deep blue bricks with a gold star on every other one
    bu, bv = X / .11, Z / .075
    bu = bu + .5 * (np.floor(bv) % 2)
    tone = .8 + .35 * _hash(np.floor(bu), np.floor(bv))
    paint(np.ones((h, w), bool), deep, tone)
    fu, fv = bu - np.floor(bu), bv - np.floor(bv)
    lead |= (np.minimum(fu, 1 - fu) * .11 < LW * .8) | (np.minimum(fv, 1 - fv) * .075 < LW * .8)
    star = (np.hypot((fu - .5) * .11, (fv - .5) * .075) < .013) & ((np.floor(bu) + np.floor(bv)) % 2 == 0)
    paint(star, gold)

    for side, cx in ((0, -LX), (1, LX)):
        u = X - cx
        au = np.abs(u)
        arc = 2 * B - np.sqrt((au + B) ** 2 + np.maximum(Z - ZL, 0) ** 2)
        de = np.minimum(np.where(Z <= ZL, B - au, arc), Z - Z0)
        inside = de > 0
        # border of jewel blocks
        s = np.where(Z <= ZL, Z, ZL + 2 * B * np.arctan2(Z - ZL, au + B))
        s = np.where((Z - Z0) < np.minimum(B - au, 1e9), np.where((Z - Z0) < (B - au), u + 10, s), s)
        blk = np.floor(s / .085)
        border = inside & (de < .05)
        k = (blk + side) % 4
        paint(border & (k == 0), ruby, .8 + .4 * _hash(blk, side + 1.0))
        paint(border & (k == 1), gold, .85 + .25 * _hash(blk, side + 2.0))
        paint(border & (k == 2), sapph, .8 + .4 * _hash(blk, side + 3.0))
        paint(border & (k == 3), gold, .85 + .25 * _hash(blk, side + 4.0))
        fs = s / .085 - blk
        lead |= border & (np.minimum(fs, 1 - fs) * .085 < LW * .8)
        lead |= inside & ((de < LW * 1.6) | (np.abs(de - .05) < LW))
        # pearl fillet
        fil = inside & (de >= .05) & (de < .068)
        paint(fil, (.95, .93, .80))
        lead |= inside & (np.abs(de - .068) < LW * .8)
        ground = inside & (de >= .068)
        # diamond quarries
        p, q = (u + Z) / .075, (u - Z) / .075
        cp, cq = np.floor(p), np.floor(q)
        pick = (_hash(cp, cq + side * 7.0) * 3.999).astype(int)   # the violet tone stays for the accents
        tone = .82 + .3 * _hash(cq, cp)
        for i in range(4):
            paint(ground & (pick == i), pale[i], tone)
        acc = ground & (cp % 3 == 0) & (cq % 3 == 0)
        paint(acc, ruby if side == 0 else sapph, tone)
        fp, fq = p - cp, q - cq
        lead |= ground & ((np.minimum(fp, 1 - fp) * .075 < LW * .7) | (np.minimum(fq, 1 - fq) * .075 < LW * .7))
        # sunburst in the head
        head = ground & (Z > ZL - .02)
        hr = np.hypot(u, Z - (ZL - .02))
        phi = np.arctan2(Z - (ZL - .02), u)
        sec = np.floor(phi / (math.pi / 9))
        lead[head] = False   # the quarry lattice stops under the sunburst
        ray = head & (hr > .075)
        m3 = sec % 3
        paint(ray & (m3 == 0), gold, .85 + .25 * _hash(sec, 3.0))
        paint(ray & (m3 == 1), ruby if side == 0 else sapph, .85 + .3 * _hash(sec, 5.0))
        paint(ray & (m3 == 2), pale[1], .9 + .15 * _hash(sec, 9.0))
        fsec = phi / (math.pi / 9) - sec
        lead |= ray & (np.minimum(fsec, 1 - fsec) * (math.pi / 9) * hr < LW * .8)
        sun = head & (hr <= .075)
        paint(sun, (.98, .86, .35))
        lead |= head & (np.abs(hr - .075) < LW)
        lead |= ground & (np.abs(Z - (ZL - .02)) < LW)
        # medallions
        for mi, zc in enumerate(MED):
            r = np.hypot(u, Z - zc)
            th = np.arctan2(Z - zc, u)
            alt = (mi + side) % 2
            c_ring, c_ground = (ruby, sapph) if alt == 0 else (sapph, ruby)
            disc = inside & (r < .215)
            lead[disc] = False   # nor does it cross the medallions
            paint(disc & (r >= .185), c_ring, .8 + .4 * _hash(np.floor(th / (math.pi / 8)), mi + 1.0))
            ft = th / (math.pi / 8) - np.floor(th / (math.pi / 8))
            lead |= disc & (r >= .185) & (np.minimum(ft, 1 - ft) * (math.pi / 8) * r < LW * .8)
            paint(disc & (r >= .165) & (r < .185), (.96, .92, .74))
            paint(disc & (r < .165), c_ground, .8 + .35 * _hash(np.floor(th / (math.pi / 4) + .5), mi + 11.0))
            petal = .15 * np.abs(np.cos(2 * th)) ** .55 + .02          # four-petal flower
            leaf = .135 * np.abs(np.sin(2 * th)) ** 1.6                 # four small leaves between the petals
            paint(disc & (r < leaf) & (r >= petal * .0), emer)
            paint(disc & (r < petal) & (r < .16), gold if alt == 0 else (.95, .93, .84), .88 + .2 * _hash(np.floor(th / (math.pi / 2) + .5), mi + 21.0))
            paint(disc & (r < .042), ruby if alt else sapph)
            lead |= disc & ((np.abs(r - .215) < LW) | (np.abs(r - .185) < LW * .8) | (np.abs(r - .165) < LW * .8) | (np.abs(r - .042) < LW * .8))
            lead |= disc & (r < .165) & ((np.abs(r - petal) < LW * .8) | ((np.abs(r - leaf) < LW * .7) & (r > petal)))
            lead |= inside & (np.abs(r - .215) < LW)

    # oculus: an eight-petal rose inside a border of small blocks
    ro = np.hypot(X - OC[0], Z - OC[1])
    th = np.arctan2(Z - OC[1], X - OC[0])
    oc = ro < OR
    lead[oc] = False
    sec = np.floor(th / (math.pi / 8))
    paint(oc & (ro >= .265), emer, .8 + .4 * _hash(sec, 31.0))
    paint(oc & (ro >= .265) & (sec % 2 == 0), gold, .85 + .25 * _hash(sec, 33.0))
    fsec = th / (math.pi / 8) - sec
    lead |= oc & (ro >= .265) & (np.minimum(fsec, 1 - fsec) * (math.pi / 8) * ro < LW * .8)
    paint(oc & (ro < .265), deep, .9 + .3 * _hash(np.floor(th / (math.pi / 4)), 41.0))
    pet = .235 * np.abs(np.cos(4 * th)) ** .5 + .03
    s8 = np.floor(th / (math.pi / 4) + .5)
    paint(oc & (ro < pet) & (ro < .25) & (s8 % 2 == 0), ruby, .85 + .3 * _hash(s8, 43.0))
    paint(oc & (ro < pet) & (ro < .25) & (s8 % 2 != 0), (.95, .93, .84), .88 + .15 * _hash(s8, 45.0))
    paint(oc & (ro < .07), gold)
    paint(oc & (ro < .03), ruby)
    lead |= oc & ((np.abs(ro - .265) < LW) | (np.abs(ro - pet) < LW * .8) & (ro < .26) | (np.abs(ro - .07) < LW * .8) | (np.abs(ro - .03) < LW * .6))
    lead |= np.abs(ro - OR) < LW * 1.5

    # hand-made glass: slow streaks and a fine grain, then the lead
    rng = np.random.default_rng(7)
    low = rng.random((h // 64 + 2, w // 64 + 2)).astype(np.float32)
    streak = np.kron(low, np.ones((64, 64), np.float32))[:h, :w]
    for _ in range(2):
        streak = (streak + np.roll(streak, 24, 0) + np.roll(streak, -24, 0) + np.roll(streak, 24, 1) + np.roll(streak, -24, 1)) / 5
    img *= (.9 + .22 * (streak - .5))[:, :, None]
    img *= (1 + .05 * (rng.random((h, w)).astype(np.float32) - .5))[:, :, None]
    img[lead] = (.035, .032, .03)
    img = np.clip(img, 0, 1).reshape(H, ss, W, ss, 3).mean((1, 3))
    return img


def glass_material(out):
    img = glass_image()
    h, w = img.shape[:2]
    rgba = np.concatenate([img[::-1], np.ones((h, w, 1), np.float32)], 2)   # Blender images start at the bottom row
    im = bpy.data.images.new(f'{SLUG}_Vitral', w, h, alpha=False)
    # the picture was drawn in display (sRGB) values
    lin = np.where(rgba[:, :, :3] <= .04045, rgba[:, :, :3] / 12.92, ((rgba[:, :, :3] + .055) / 1.055) ** 2.4)
    rgba[:, :, :3] = lin
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = str(out / f'{SLUG}_Vitral.png')
    im.file_format = 'PNG'
    im.save()
    m = bpy.data.materials.new('Vitral')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = im
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = .2
    return m


def window():
    reset()
    out = OUT / SLUG
    out.mkdir(parents=True, exist_ok=True)
    stone = material('Stone', 'painted_plaster_wall', (.80, .76, .66), rough=.85, out=out)
    tracery = material('Tracery', 'painted_plaster_wall', (.90, .87, .79), rough=.8, out=out)
    iron = material('Iron', 'metal_plate', (.10, .10, .11), rough=.5, out=out)
    glass = glass_material(out)

    # moulded surround in three steps (each one nearer the glass sits deeper), then the hood mould
    band('surround_outer', arch_path(0, A, Z0, ZS, .07), arch_path(0, A, Z0, ZS, .17), -.17, .02, stone)
    band('surround_mid', arch_path(0, A, Z0, ZS, .025), arch_path(0, A, Z0, ZS, .07), -.125, .02, stone)
    band('surround_inner', arch_path(0, A, Z0, ZS, -.02), arch_path(0, A, Z0, ZS, .025), -.085, .02, tracery)
    hood_in, hood_out = arch_path(0, A, ZS - .12, ZS, .17), arch_path(0, A, ZS - .12, ZS, .245)
    band('hood', hood_in, hood_out, -.215, .02, tracery)
    for sx in (-1, 1):   # label stops: a small carved block and a ball under each end of the hood
        box(f'label{sx}', (.13, .2, .13), (sx * (A + .21), -.11, ZS - .18), tracery, bevel=.02, uv=.6)
        lathe(f'labelball{sx}', [(0, -.045), (.03, -.035), (.045, 0), (.03, .035), (0, .045)], (sx * (A + .21), -.12, ZS - .29), tracery, 16)
    lathe('finial', [(0, 0), (.05, .01), (.07, .06), (.04, .11), (.06, .16), (.02, .21), (0, .25)], (0, -.12, APEX + .2), tracery, 16)

    # sill: sloped stone on an apron with two corbels
    bm = bmesh.new()
    hw = A + .3
    v = [bm.verts.new(p) for p in [(-hw, -.3, Z0 - .13), (hw, -.3, Z0 - .13), (hw, .02, Z0 - .13), (-hw, .02, Z0 - .13),
                                    (-hw, -.3, Z0 - .05), (hw, -.3, Z0 - .05), (hw, .02, Z0 + .02), (-hw, .02, Z0 + .02)]]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([v[i] for i in f])
    finish(mesh_obj('sill', bm), tracery, .8, bevel=.012, seg=2, smooth=False)
    box('apron', (2 * A + .34, .16, .14), (0, -.06, Z0 - .2), stone, bevel=.015, uv=.8)
    for sx in (-1, 1):
        box(f'corbel{sx}', (.14, .2, .26), (sx * (A + .05), -.08, Z0 - .36), tracery, bevel=.03, uv=.6)

    # tracery: mullion, two lancet heads, the oculus with four foils and a boss
    box('mullion', (2 * MULL, .11, ZL - Z0), (0, -.075, (ZL + Z0) / 2), tracery, bevel=.012, uv=.6)
    for sx in (-1, 1):
        band(f'lancet{sx}', arch_path(sx * LX, B, ZL - .02, ZL, 0.0, 10), arch_path(sx * LX, B, ZL - .02, ZL, .05, 10), -.13, -.02, tracery, uv=.6)
    band('oculus', circle(OC[0], OC[1], OR), circle(OC[0], OC[1], OR + .055), -.13, -.02, tracery, uv=.6, closed=True)
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        cx, cz = OC[0] + .165 * math.cos(a), OC[1] + .165 * math.sin(a)
        band(f'foil{i}', circle(cx, cz, .148, 28), circle(cx, cz, .168, 28), -.105, -.02, tracery, uv=.6, closed=True)
    boss = lathe('boss', [(0, 0), (.035, .004), (.05, .02), (.03, .04), (0, .05)], (0, 0, 0), tracery, 16)
    boss.rotation_euler = (math.pi / 2, 0, 0)
    boss.location = (OC[0], -.105, OC[1])
    # iron saddle bars across each lancet
    z = Z0 + .38
    while z < ZL - .05:
        for sx in (-1, 1):
            tube(f'bar{sx}{z:.2f}', (sx * LX - B, -.045, z), (sx * LX + B, -.045, z), .008, iron, 8)
        z += .44

    # the glass: one pane filling the opening, the picture mapped over its bounding box
    bm = bmesh.new()
    pts = arch_path(0, A, Z0, ZS, 0.0, 16)
    vs = [bm.verts.new((x, -.03, zz)) for x, zz in pts]
    face = bm.faces.new(vs)
    face.normal_update()   # a new face has no normal yet: without this the pane faced the wall and UE culled it
    if face.normal.y > 0:
        bmesh.ops.reverse_faces(bm, faces=[face])
    uv = bm.loops.layers.uv.verify()
    for loop in face.loops:
        co = loop.vert.co
        loop[uv].uv = ((co.x + A) / (2 * A), (co.z - Z0) / (APEX - Z0))
    bmesh.ops.triangulate(bm, faces=bm.faces)
    pane = mesh_obj('glass', bm)
    pane.data.materials.append(glass)
    export(SLUG, 'Vitral gótico da igreja')


if __name__ == '__main__':
    window()
    print('exported', OUT / SLUG)
