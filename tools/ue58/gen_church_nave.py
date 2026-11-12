"""Interior of the village church (11/11, Sergio: "faça o interior da igreja como essas referências da igreja da Sé",
keeping the church's size: 10 x 12 m outside, walls 7 m).

mare_church_nave: everything inside the four walls, as one model. A hall church in three aisles: clustered piers with
moulded bases and capitals, a pointed arcade, pointed brick vaults with stone ribs (transverse, diagonal, ridge, bosses),
ashlar wall lining, a chequered stone floor, a raised chancel with a marble altar, ten dark pews, the open door
leaves and the stone that closes the front wall around the door arch. Kept under 6.62 m (the cornice plates of the
old box stay above it). The stained-glass windows and the rose are separate models placed in the level.
mare_church_rose: the rose window over the door (stone tracery, own glass picture).

Local frame used below: x across (east +), v along the nave (door at v = -5.7, altar end at +5.7), z up from the
ground; the model's origin is the church's centre on the ground. Blender y = -v (the importer mirrors y: Blender -Y = UE +Y).
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_church_nave.py [nave|rose]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from gen_custom_furniture import OUT, box, export, finish, lathe, material, mesh_obj, reset, tube  # noqa: E402

HW, HV = 4.7, 5.7          # inner half width and half length
FL = .20                   # floor level
TOP = 6.62                 # nothing rises above this
PX = 1.9                   # pier lines (x = +-PX)
WALL = .22                 # half thickness of the arcade wall
LINES = (-5.4, -1.8, 1.8, 5.4)   # pier / rib lines along the nave (the outer pilasters stand on the same lines)
CAP = 2.6                  # arcade springing (top of the pier capitals)
ARC_A, ARC_RISE = 1.52, 1.65
NAVE_A, NAVE_SPRING, NAVE_RISE = PX - WALL, 4.4, 2.2
AISLE_C, AISLE_A, AISLE_SPRING, AISLE_RISE = (PX + WALL + HW) / 2, (HW - PX - WALL) / 2, 5.2, 1.4


def B(x, v, z):
    return (x, -v, z)


def bx(name, size, loc, mat, **kw):
    return box(name, size, B(*loc), mat, **kw)


def tb(name, a, b, r, mat, sides=10):
    return tube(name, B(*a), B(*b), r, mat, sides)


def arch_pts(half, rise, off=0.0, n=12):
    """Pointed arch about (0, 0): from (-half-off, 0) over the apex to (+half+off, 0); the two arcs have their centres
    on the springing line, `c` past the axis (c = half gives the equilateral arch)."""
    c = (rise * rise - half * half) / (2 * half)
    R = half + c + off
    end = math.acos(-c / R)
    left = [(c + R * math.cos(math.pi - (math.pi - end) * i / n), R * math.sin(math.pi - (math.pi - end) * i / n)) for i in range(n + 1)]
    return left + [(-x, z) for x, z in reversed(left[:-1])]


def arch_z(half, rise, x):
    c = (rise * rise - half * half) / (2 * half)
    R = half + c
    return math.sqrt(max(R * R - (abs(x) + c) ** 2, 0.0))


def band(name, inner, outer, d0, d1, mat, to3d, uv=1.0, closed=False, bevel=.008):
    """Solid strip between two outlines of the same length in a plane, from depth d0 to d1; to3d(p, q, d) -> Blender xyz."""
    bm = bmesh.new()
    n = len(inner)
    rows = [[bm.verts.new(to3d(p, q, d)) for p, q in line] for line in (inner, outer) for d in (d0, d1)]
    fi, bi, fo, bo = rows
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        for quad in ((fi[i], fi[j], fo[j], fo[i]), (bi[i], bo[i], bo[j], bi[j]), (fo[i], fo[j], bo[j], bo[i]), (fi[i], bi[i], bi[j], fi[j])):
            if len({v.co.copy().freeze() for v in quad}) == 4:
                bm.faces.new(quad)
    if not closed:
        for quad in ((fi[0], fo[0], bo[0], bi[0]), (fi[-1], bi[-1], bo[-1], fo[-1])):
            if len({v.co.copy().freeze() for v in quad}) == 4:
                bm.faces.new(quad)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    return finish(mesh_obj(name, bm), mat, uv, bevel=bevel, seg=2, smooth=False)


def xz(v):          # outline in the (x, z) plane, depth along the nave
    return lambda p, q, d: B(p, d, q)


def vz(x_sign=1):   # outline in the (v, z) plane, depth across
    return lambda p, q, d: B(d * x_sign, p, q)


def shell(name, cx, half, spring, rise, v0, v1, mat, tile=1.2, n=14):
    """Vault web: the underside of a pointed barrel, facing down into the room; the brick courses run along the nave."""
    prof = arch_pts(half, rise, 0.0, n)
    arc = [0.0]
    for a, b in zip(prof, prof[1:]):
        arc.append(arc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    steps = max(2, int(round((v1 - v0) / .9)))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.verify()
    grid = [[bm.verts.new(B(cx + p, v0 + (v1 - v0) * k / steps, spring + q)) for p, q in prof] for k in range(steps + 1)]
    axis_z = spring
    for k in range(steps):
        for i in range(len(prof) - 1):
            quad = [grid[k][i], grid[k][i + 1], grid[k + 1][i + 1], grid[k + 1][i]]
            f = bm.faces.new(quad)
            f.normal_update()
            centre = f.calc_center_median()
            inward = Vector((cx - centre.x, 0, axis_z - centre.z))
            if f.normal.dot(inward) < 0:
                bmesh.ops.reverse_faces(bm, faces=[f])
            for loop in f.loops:
                kk = next(r for r in range(steps + 1) if loop.vert in grid[r])
                ii = grid[kk].index(loop.vert)
                loop[uvl].uv = ((v0 + (v1 - v0) * kk / steps) / tile, arc[ii] / tile)
            f.smooth = True
    obj = mesh_obj(name, bm)
    obj.data.materials.append(mat)
    return obj


def rib_curve(name, cx, half, spring, rise, v0, v1, mat, r=.05, n=10):
    """A diagonal rib: straight in plan from one corner of the bay to the opposite one, lying on the vault."""
    pts = []
    for i in range(n + 1):
        t = i / n
        x = -half + 2 * half * t
        pts.append((cx + x, v0 + (v1 - v0) * t, spring + arch_z(half, rise, x) - r * .5))
    for i in range(n):
        tb(f'{name}{i}', pts[i], pts[i + 1], r, mat, 8)


def pier(name, x, v, stone, pale, engaged=0):
    """Clustered pier: a round core with eight shafts, moulded base on a plinth, bell capital under an abacus.
    engaged = +-1: against an end wall, only the half that looks into the church."""
    lathe(f'{name}_plinth', [(0, 0), (.42, 0), (.42, .22), (.38, .26), (0, .26)], B(x, v, FL), stone, 8)
    lathe(f'{name}_base', [(0, 0), (.37, 0), (.385, .04), (.37, .08), (.33, .10), (.345, .14), (.33, .18), (.29, .20), (0, .20)], B(x, v, FL + .26), pale, 24)
    lathe(f'{name}_core', [(0, 0), (.25, 0), (.25, CAP - FL - .46 - .34), (0, CAP - FL - .46 - .34)], B(x, v, FL + .46), stone, 20)
    for k in range(8):
        a = math.radians(22.5 + 45 * k)
        sx, sv = x + .27 * math.cos(a), v + .27 * math.sin(a)
        tb(f'{name}_shaft{k}', (sx, sv, FL + .46), (sx, sv, CAP - .34), .07, SHAFT[0] or pale, 10)
    lathe(f'{name}_neck', [(0, 0), (.36, 0), (.375, .025), (.36, .05), (0, .05)], B(x, v, CAP - .36), pale, 24)
    lathe(f'{name}_bell', [(0, 0), (.33, 0), (.34, .06), (.37, .13), (.42, .19), (.45, .22), (0, .22)], B(x, v, CAP - .31), pale, 24)
    lathe(f'{name}_abacus', [(0, 0), (.47, 0), (.49, .03), (.49, .07), (.46, .09), (0, .09)], B(x, v, CAP - .09), stone, 8)


def pew(name, x0, x1, v, wood, dark):
    """A pew 3 m long facing the altar (+v): seat, reclined back, shaped ends with a pointed head, kneeler, book ledge."""
    cx, L = (x0 + x1) / 2, abs(x1 - x0)
    bx(f'{name}_seat', (L - .08, .42, .045), (cx, v, FL + .45), wood, uv=.9)
    bx(f'{name}_apron', (L - .1, .03, .12), (cx, v + .19, FL + .37), dark, uv=.9)
    back = bx(f'{name}_back', (L - .08, .04, .52), (cx, v - .235, FL + .72), wood, uv=.9)
    back.rotation_euler = (math.radians(-7), 0, 0)
    bx(f'{name}_rail', (L - .04, .07, .05), (cx, v - .27, FL + .99), dark, uv=.9)
    bx(f'{name}_ledge', (L - .1, .13, .025), (cx, v - .33, FL + .78), dark, uv=.9)
    bx(f'{name}_kneeler', (L - .2, .18, .04), (cx, v + .52, FL + .14), dark, uv=.9)
    for i, ex in enumerate((x0, x1)):
        # end panel: a tall board with a pointed head (profile in the v-z plane)
        prof = [(-.36, 0), (-.36, .98), (-.30, 1.08), (-.22, 1.16), (-.14, 1.08), (-.06, .98), (.02, .72), (.26, .66), (.30, .5), (.30, 0)]
        bm = bmesh.new()
        front = [bm.verts.new(B(ex - .03, v + p, FL + q)) for p, q in prof]
        rear = [bm.verts.new(B(ex + .03, v + p, FL + q)) for p, q in prof]
        bm.faces.new(front)
        bm.faces.new(list(reversed(rear)))
        for k in range(len(prof)):
            j = (k + 1) % len(prof)
            bm.faces.new((front[k], rear[k], rear[j], front[j]))
        finish(mesh_obj(f'{name}_end{i}', bm), dark, .9, bevel=.008, seg=2, smooth=False)
        for kv in (.33, .62):
            bx(f'{name}_kleg{i}{kv}', (.04, .04, .14), (ex + (.12 if i == 0 else -.12), v + kv - .1, FL + .07), dark, bevel=.004)


# ---------------------------------------------------------------- pictures drawn here
def _save(name, img, out):
    h, w = img.shape[:2]
    rgba = np.concatenate([img[::-1], np.ones((h, w, 1), np.float32)], 2)
    rgba[:, :, :3] = np.where(rgba[:, :, :3] <= .04045, rgba[:, :, :3] / 12.92, ((rgba[:, :, :3] + .055) / 1.055) ** 2.4)
    im = bpy.data.images.new(name, w, h, alpha=False)
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = str(out / f'{name}.png')
    im.file_format = 'PNG'
    im.save()
    return im


def _pic_material(name, im, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = im
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    return m


def _fft_noise(n, beta, seed):
    """Periodic smooth noise in -1..1 (random phases under a 1/f^beta spectrum): tiles without a seam."""
    rng = np.random.default_rng(seed)
    fx = np.fft.fftfreq(n)[:, None]
    fy = np.fft.rfftfreq(n)[None, :]
    f = np.hypot(fx, fy)
    f[0, 0] = 1
    spec = (rng.normal(size=f.shape) + 1j * rng.normal(size=f.shape)) / f ** beta
    spec[0, 0] = 0
    out = np.fft.irfft2(spec, s=(n, n)).astype(np.float32)
    return out / np.abs(out).max()


def marble_image(base, vein, seed, n=2048, second=None, veins=1.0):
    """Polished marble with lightning veins (11/11, Sergio: "mármore com traços de raio"): the veins are the zero lines
    of a smooth field read through a strong domain warp, so they run long, fork and break like cracks; a finer second
    family crosses them (in `second` colour: gold in the white marble); soft clouds vary the ground."""
    ii, jj = np.meshgrid(np.arange(n), np.arange(n), indexing='ij')
    wx, wy = _fft_noise(n, 2.4, seed), _fft_noise(n, 2.4, seed + 1)

    def warped(field, amp):
        return field[(ii + (wx * amp).astype(np.int32)) % n, (jj + (wy * amp).astype(np.int32)) % n]
    f1 = warped(_fft_noise(n, 1.9, seed + 2), n * .11)
    f2 = warped(_fft_noise(n, 1.6, seed + 3), n * .06)
    f3 = warped(_fft_noise(n, 1.7, seed + 6), n * .09)
    cloud = _fft_noise(n, 2.6, seed + 4)
    thick = .008 + .010 * np.clip(_fft_noise(n, 2.2, seed + 5), 0, 1)             # veins swell and thin out
    # several vein families: the level lines of one warped field at different heights run side by side and never cross,
    # like the bedding of real marble; a second field cuts across them (the forks), a third gives the hair veins
    v1 = np.zeros((n, n), np.float32)
    for level, strength, width in ((0, 1.0, 1.0), (.2, .75, .7), (-.23, .7, .7), (.42, .5, .5), (-.47, .5, .5), (.62, .35, .4), (-.68, .35, .4)):
        v1 = np.maximum(v1, strength * np.clip(1 - np.abs(f1 - level) / (thick * width), 0, 1) ** 1.4)
    for level, strength in ((0, .7), (.3, .45), (-.33, .45)):
        v1 = np.maximum(v1, strength * np.clip(1 - np.abs(f3 - level) / (thick * .55), 0, 1) ** 1.4)
    v2 = np.zeros((n, n), np.float32)
    for level in (0, .25, -.27, .5, -.52):
        v2 = np.maximum(v2, np.clip(1 - np.abs(f2 - level) / .005, 0, 1) ** 2 * .7)
    halo = np.zeros((n, n), np.float32)
    for level in (0, .2, -.23):
        halo = np.maximum(halo, np.clip(1 - np.abs(f1 - level) / (thick * 7), 0, 1) * .16)   # the stone is stained along a vein
    img = np.asarray(base, np.float32)[None, None, :] * (.90 + .10 * cloud)[:, :, None]
    for mask, col in ((halo * veins, vein), (np.clip(v1, 0, 1) * veins, vein), (v2 * veins, second if second is not None else vein)):
        img = img * (1 - mask[:, :, None]) + np.asarray(col, np.float32)[None, None, :] * mask[:, :, None]
    return np.clip(img, 0, 1)


def marble_floor_image(n=2048):
    """One 1.6 m tile of the paving in polished marble: white and black squares set on the diagonal, each cut from its
    own slab (veins do not run across the joints), gold-veined black; a thin dark joint."""
    white = marble_image((.90, .89, .86), (.36, .37, .40), 21, n, second=(.70, .58, .34))
    black = marble_image((.035, .035, .04), (.82, .80, .74), 22, n, second=(.72, .56, .24), veins=.8)
    u, v = np.meshgrid((np.arange(n) + .5) / n * 4, (np.arange(n) + .5) / n * 4)
    a, b = (u + v) / 2 * 2, (u - v) / 2 * 2                    # diagonal lattice: 28 cm squares
    ca, cb = np.floor(a), np.floor(b)
    fa, fb = a - ca, b - cb
    dark = ((ca + cb) % 2 == 0)
    # each square reads the slab at its own offset
    off = ((ca * 37 + cb * 91) % 13).astype(np.int32) * (n // 13)
    ii, jj = np.meshgrid(np.arange(n), np.arange(n), indexing='ij')
    w2 = white[(ii + off) % n, (jj + off * 3) % n]
    b2 = black[(ii + off * 5) % n, (jj + off) % n]
    img = np.where(dark[:, :, None], b2, w2)
    joint = (np.minimum(fa, 1 - fa) < .012) | (np.minimum(fb, 1 - fb) < .012)
    img[joint] *= .55
    return np.clip(img, 0, 1)


def _gold():
    m = bpy.data.materials.new('Gold')
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (1.0, .74, .30, 1)
    p.inputs['Metallic'].default_value = 1.0
    p.inputs['Roughness'].default_value = .26
    return m


SHAFT = [None]     # material of the slender shafts (set in nave(): dark green marble)


def floor_image(n=1024):
    """One 1.6 m tile of the paving: cream stone squares in a lattice of grey bands with black squares at the crossings
    and a small black diamond in every other cream square."""
    u, v = np.meshgrid((np.arange(n) + .5) / n * 4, (np.arange(n) + .5) / n * 4)      # four 40 cm modules per tile
    fu, fv = u - np.floor(u), v - np.floor(v)
    cu, cv = np.floor(u), np.floor(v)
    rng = np.random.default_rng(3)
    grain = np.kron(rng.random((n // 8, n // 8)).astype(np.float32), np.ones((8, 8), np.float32))
    img = np.empty((n, n, 3), np.float32)
    cream = np.array((.80, .76, .66), np.float32) * (.93 + .1 * grain)[:, :, None]
    img[:] = cream
    bandu, bandv = fu < .26, fv < .26
    img[bandu | bandv] = np.array((.47, .46, .44), np.float32)
    img[bandu & bandv] = (.07, .07, .075)
    dia = (np.abs(fu - .63) + np.abs(fv - .63) < .16) & ((cu + cv) % 2 == 0)
    img[dia] = (.08, .08, .085)
    joint = (np.minimum(fu, 1 - fu) < .012) | (np.minimum(fv, 1 - fv) < .012) | (np.abs(fu - .26) < .01) | (np.abs(fv - .26) < .01)
    img[joint] *= .72
    img *= (.96 + .08 * rng.random((n, n)).astype(np.float32))[:, :, None]
    return np.clip(img, 0, 1)


def ashlar_image(n=1024):
    """2.4 m of pale granite ashlar: eight 30 cm courses of 60 cm blocks in running bond, fine joints, each block its own tone."""
    u, v = np.meshgrid((np.arange(n) + .5) / n * 4, (np.arange(n) + .5) / n * 8)
    row = np.floor(v)
    uu = u + .5 * (row % 2)
    col = np.floor(uu) % 4
    fu, fv = uu - np.floor(uu), v - row
    rng = np.random.default_rng(5)
    tone = (.93 + .12 * (np.abs(np.sin(col * 12.9898 + row * 78.233) * 43758.5453) % 1.0)).astype(np.float32)
    grain = np.kron(rng.random((n // 4, n // 4)).astype(np.float32), np.ones((4, 4), np.float32))
    speck = rng.random((n, n)).astype(np.float32)
    img = np.array((.74, .71, .65), np.float32)[None, None, :] * (tone * (.95 + .08 * grain) * (.97 + .06 * speck))[:, :, None]
    joint = (np.minimum(fu, 1 - fu) * .6 < .006) | (np.minimum(fv, 1 - fv) * .3 < .006)
    img[joint] *= .62
    return np.clip(img, 0, 1)


def rose_image(n=1024):
    """The rose: a gold eye, twelve petals in ruby and sapphire, a ring of twelve roundels, a border of small blocks."""
    c = (np.arange(n) + .5) / n * 2 - 1
    X, Y = np.meshgrid(c, -c)
    r, th = np.hypot(X, Y), np.arctan2(Y, X)
    ruby, sapph, gold, emer, pearl, deep = (.62, .05, .09), (.07, .19, .64), (.93, .68, .12), (.08, .46, .22), (.95, .93, .84), (.05, .11, .40)
    img = np.zeros((n, n, 3), np.float32)
    lead = np.zeros((n, n), bool)
    LW = .008

    def h(a, b):
        return np.abs(np.sin(a * 127.1 + b * 311.7) * 43758.5453) % 1.0

    def paint(mask, colour, tone=None):
        col = np.asarray(colour, np.float32)
        img[mask] = col if tone is None else col * tone[mask][:, None]

    s12 = np.floor(th / (math.pi / 6) + .5)
    s24 = np.floor(th / (math.pi / 12))
    paint(r < 1, deep, .85 + .3 * h(s24, 1.0))
    border = (r >= .86) & (r < 1)
    paint(border & (s24 % 2 == 0), gold, .85 + .25 * h(s24, 2.0))
    paint(border & (s24 % 2 == 1), emer, .8 + .4 * h(s24, 3.0))
    f24 = th / (math.pi / 12) - s24
    lead |= border & (np.minimum(f24, 1 - f24) * (math.pi / 12) * r < LW)
    # ring of roundels between the petals' tips and the border
    ang = s12 * (math.pi / 6)
    rx, ry = X - .70 * np.cos(ang), Y - .70 * np.sin(ang)
    rr = np.hypot(rx, ry)
    paint(rr < .13, pearl)
    paint(rr < .10, ruby, .85 + .3 * h(s12, 5.0))
    paint((rr < .10) & (s12 % 2 == 0), sapph, .85 + .3 * h(s12, 6.0))
    paint(rr < .035, gold)
    lead |= (np.abs(rr - .13) < LW) | (np.abs(rr - .10) < LW * .8) | (np.abs(rr - .035) < LW * .7)
    # petals
    pet = .50 * np.abs(np.cos(6 * (th - ang) * .5 * 2 / 2 * 1.0)) ** .45 * (np.abs(th - ang) < math.pi / 12 + 1) + .06
    d = np.abs(((th - ang + math.pi) % (2 * math.pi)) - math.pi)
    pet = .56 * np.clip(1 - (d / (math.pi / 12)) ** 2.2, 0, 1) ** .5
    inp = (r < pet) & (r > .12) & (r < .58)
    paint(inp & (s12 % 2 == 0), ruby, .85 + .3 * h(s12, 7.0))
    paint(inp & (s12 % 2 == 1), pearl, .88 + .15 * h(s12, 8.0))
    paint(inp & (r < .30), gold, .88 + .2 * h(s12, 9.0))
    paint(inp & (r < .30) & (s12 % 2 == 1), sapph, .85 + .3 * h(s12, 10.0))
    lead |= (np.abs(r - pet) < LW) & (r > .12) & (r < .6) | inp & (np.abs(r - .30) < LW * .8)
    paint(r < .12, gold)
    paint(r < .06, ruby)
    lead |= (np.abs(r - .12) < LW) | (np.abs(r - .06) < LW * .7) | (np.abs(r - .86) < LW) | (np.abs(r - .6) < LW * .0)
    img[lead] = (.035, .032, .03)
    img[r >= 1] = (.03, .03, .03)
    return np.clip(img, 0, 1)


# ---------------------------------------------------------------- models
def nave():
    reset()
    slug = 'mare_church_nave'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    # 11/11 (Sergio: "mármore com traços de raio, com detalhes em ouro, precisa ser imponente"): walls, piers, altar and
    # chancel in white marble with lightning veins, the slender shafts in dark green marble, every moulding, capital, rib
    # and boss gilded, the vault webs in ivory plaster, the paving in polished black and white marble.
    stone = _pic_material('Stone', _save(f'{slug}_Marmore', marble_image((.90, .89, .86), (.36, .37, .40), 11, second=(.74, .60, .32)), out), .22)
    pale = _gold()                                                                                 # mouldings, capitals, ribs, bosses
    SHAFT[0] = _pic_material('Verde', _save(f'{slug}_MarmoreVerde', marble_image((.10, .24, .17), (.86, .88, .80), 12, second=(.80, .64, .30), veins=.9), out), .18)
    shaft = SHAFT[0]
    brick = material('Vault', 'painted_plaster_wall', (.90, .86, .76), rough=.75, out=out)         # vault webs: ivory plaster
    marble = _pic_material('Marble', _save(f'{slug}_MarmoreAltar', marble_image((.93, .92, .90), (.42, .42, .45), 13, second=(.78, .62, .30)), out), .15)
    wood = material('Wood', 'oak_wood_planks', (.24, .11, .06), rough=.5, out=out)
    dark = material('WoodDark', 'oak_wood_planks', (.13, .06, .035), rough=.45, out=out)
    cloth = material('Cloth', 'rough_linen', (.95, .94, .90), rough=.9, out=out)
    iron = material('Iron', 'metal_plate', (.09, .09, .10), rough=.5, out=out)
    brass = material('Brass', 'metal_plate', (.72, .52, .18), rough=.35, out=out)
    floor = _pic_material('Floor', _save(f'{slug}_Piso', marble_floor_image(), out), .14)

    # floor and chancel
    bx('floor', (2 * HW, 2 * HV, FL), (0, 0, FL / 2), floor, uv=1.6, bevel=0)
    bx('chancel1', (2 * HW, HV - 2.35, .15), (0, (HV + 2.35) / 2, FL + .075), marble, uv=1.4, bevel=.01)
    bx('chancel2', (2 * HW, HV - 2.75, .15), (0, (HV + 2.75) / 2, FL + .225), marble, uv=1.4, bevel=.01)
    CH = FL + .30

    # wall lining (6 cm of ashlar on the four walls), the front in pieces around the door arch
    T = .06
    for sx in (-1, 1):
        bx(f'lining_side{sx}', (T, 2 * HV, TOP - FL), (sx * (HW - T / 2), 0, (TOP + FL) / 2), stone, uv=2.4, bevel=0)
        bx(f'lining_front{sx}', (HW - 1.0, T, TOP - FL), (sx * (HW + 1.0) / 2, -HV + T / 2, (TOP + FL) / 2), stone, uv=2.4, bevel=0)
    bx('lining_back', (2 * HW, T, TOP - FL), (0, HV - T / 2, (TOP + FL) / 2), stone, uv=2.4, bevel=0)
    # the front wall around the door: the old box wall is rebuilt in slabs that leave x -1..1 open up to 4.62 m; this
    # stone fills between the round door arch (radius 1 m, springing 3.6 m) and that height, through the whole wall
    semi = [(math.cos(math.pi - math.pi * i / 16), 3.6 + math.sin(math.pi * i / 16)) for i in range(17)]
    band('door_spandrel', semi, [(p, 4.62) for p, q in semi], -HV - .30, -HV + T, stone, xz(0), uv=2.4)
    bx('lining_overdoor', (2.0, T, TOP - 4.62), (0, -HV + T / 2, (TOP + 4.62) / 2), stone, uv=2.4, bevel=0)
    # door arch moulding inside and a threshold
    ring_in = [(.99 * (p), 3.6 + (q - 3.6) * .99) for p, q in semi]
    ring_out = [(1.14 * p, 3.6 + (q - 3.6) * 1.14) for p, q in semi]
    band('door_arch', ring_in, ring_out, -HV + T - .01, -HV + T + .07, pale, xz(0), uv=1.0)
    for sx in (-1, 1):
        bx(f'door_jamb{sx}', (.14, .08, 3.6 - FL), (sx * 1.07, -HV + T + .03, (3.6 + FL) / 2), pale, uv=1.0)
        # open leaves, folded flat against the front wall (swung half open they stood on the first pews)
        bx(f'leaf{sx}', (.98, .07, 3.45), (sx * 1.66, -HV + T + .045, FL + 1.74), wood, uv=.9, bevel=.01)
        for z in (FL + .55, FL + 1.75, FL + 2.95):
            bx(f'strap{sx}{z:.1f}', (.78, .012, .07), (sx * 1.6, -HV + T + .086, z), iron, bevel=.004)
        pull = lathe(f'pull{sx}', [(0, 0), (.035, .01), (.05, .04), (.035, .07), (0, .08)], (0, 0, 0), brass, 14)
        pull.rotation_euler = (math.pi / 2, 0, 0)
        pull.location = B(sx * 2.02, -HV + T + .08, FL + 1.25)
    bx('threshold', (2.0, .36, .03), (0, -HV - .12, FL - .012), marble, uv=1.2, bevel=.006)

    # piers: four free, four against the end walls
    for sx in (-1, 1):
        for v in LINES:
            pier(f'pier{sx}{v}', sx * PX, max(min(v, HV - .12), -HV + .12), stone, pale)
    # arcade: arches between the piers, the wall above them up to the top, the moulding on both faces
    arc = arch_pts(ARC_A, ARC_RISE)
    for sx in (-1, 1):
        for k in range(3):
            vc = (LINES[k] + LINES[k + 1]) / 2
            inner = [(vc + p, CAP + q) for p, q in arc]
            band(f'arcade_wall{sx}{k}', inner, [(p, TOP) for p, q in inner], sx * (PX - WALL), sx * (PX + WALL), stone, vz(), uv=2.4, bevel=0)
            mould = [(vc + p, CAP + q) for p, q in arch_pts(ARC_A, ARC_RISE, .13)]
            band(f'arcade_mould{sx}{k}', inner, mould, sx * (PX - WALL - .035), sx * (PX + WALL + .035), pale, vz(), uv=1.0)
        for v in LINES:   # the wall over each pier
            lo, hi = max(v - .28, -HV + T), min(v + .28, HV - T)
            bx(f'arcade_over{sx}{v}', (2 * WALL, hi - lo, TOP - CAP), (sx * PX, (lo + hi) / 2, (TOP + CAP) / 2), stone, uv=2.4, bevel=0)
            # vaulting shaft from the capital to the nave springing, with its own small capital
            tb(f'vshaft{sx}{v}', (sx * (PX - WALL - .06), (lo + hi) / 2, CAP), (sx * (PX - WALL - .06), (lo + hi) / 2, NAVE_SPRING - .12), .07, shaft, 10)
            lathe(f'vcap{sx}{v}', [(0, 0), (.08, 0), (.10, .05), (.15, .10), (.15, .13), (0, .13)], B(sx * (PX - WALL - .06), (lo + hi) / 2, NAVE_SPRING - .13), pale, 14)
        bx(f'string{sx}', (.05, 2 * HV - 2 * T, .07), (sx * (PX - WALL - .02), 0, NAVE_SPRING - .06), pale, uv=1.0, bevel=.01)
        # responds on the side walls and their capitals at the aisle springing
        for v in LINES:
            vv = max(min(v, HV - .14), -HV + .14)
            tb(f'respond{sx}{v}', (sx * (HW - T - .07), vv, FL), (sx * (HW - T - .07), vv, AISLE_SPRING - .12), .08, shaft, 10)
            lathe(f'rcap{sx}{v}', [(0, 0), (.09, 0), (.11, .05), (.16, .10), (.16, .13), (0, .13)], B(sx * (HW - T - .07), vv, AISLE_SPRING - .13), pale, 14)
            lathe(f'rbase{sx}{v}', [(0, 0), (.14, 0), (.14, .12), (.10, .18), (0, .18)], B(sx * (HW - T - .07), vv, FL), pale, 14)
            tb(f'respond_in{sx}{v}', (sx * (PX + WALL + .06), vv, CAP), (sx * (PX + WALL + .06), vv, AISLE_SPRING - .12), .07, shaft, 10)
            lathe(f'rcap_in{sx}{v}', [(0, 0), (.08, 0), (.10, .05), (.15, .10), (.15, .13), (0, .13)], B(sx * (PX + WALL + .06), vv, AISLE_SPRING - .13), pale, 14)

    # vaults: brick webs, transverse ribs on the pier lines, diagonal ribs and a boss in every bay, a ridge rib
    vaults = [('nave', 0.0, NAVE_A, NAVE_SPRING, NAVE_RISE), ('aisleW', -AISLE_C, AISLE_A, AISLE_SPRING, AISLE_RISE), ('aisleE', AISLE_C, AISLE_A, AISLE_SPRING, AISLE_RISE)]
    for name, cx, a, spring, rise in vaults:
        shell(f'{name}_web', cx, a, spring, rise, -HV + T, HV - T, brick)
        outer = [(cx + p, spring + q) for p, q in arch_pts(a, rise)]
        inner = [(cx + p * (a - .13) / a, spring + q * (rise - .13) / rise) for p, q in arch_pts(a, rise)]
        for v in LINES:
            vv = max(min(v, HV - T - .08), -HV + T + .08)
            band(f'{name}_rib{v}', inner, outer, vv - .08, vv + .08, pale, xz(0), uv=1.0)
        for k in range(3):
            v0, v1 = LINES[k], LINES[k + 1]
            rib_curve(f'{name}_diagA{k}', cx, a - .02, spring, rise - .02, v0, v1, pale)
            rib_curve(f'{name}_diagB{k}', cx, a - .02, spring, rise - .02, v1, v0, pale)
            boss = lathe(f'{name}_boss{k}', [(0, 0), (.06, .0), (.13, .03), (.15, .07), (.10, .12), (0, .14)], (0, 0, 0), pale, 16)
            boss.rotation_euler = (math.pi, 0, 0)
            boss.location = B(cx, (v0 + v1) / 2, spring + rise - .01)
        tb(f'{name}_ridge', (cx, -HV + T, spring + rise - .04), (cx, HV - T, spring + rise - .04), .045, pale, 8)

    # chancel: marble altar under a cloth, two steps up; a standing brass cross and a lectern
    av = 3.95      # (4.35 before the reredos: the priest stands between the table and the gradine, 77 cm)
    for sx in (-1, 1):
        bx(f'altar_leg{sx}', (.34, .62, .82), (sx * .72, av, CH + .41), marble, uv=1.0, bevel=.03)
    bx('altar_base', (2.1, .8, .08), (0, av, CH + .04), marble, uv=1.0, bevel=.015)
    bx('altar_slab', (2.3, .95, .1), (0, av, CH + .87), marble, uv=1.0, bevel=.02)
    bx('altar_cloth', (2.36, 1.01, .012), (0, av, CH + .927), cloth, uv=.6, bevel=.004)
    for sx in (-1, 1):
        bx(f'altar_fall{sx}', (.012, 1.01, .34), (sx * 1.18, av, CH + .76), cloth, uv=.6, bevel=.004)
    # altar frontal: a gilded panel with a cross in a ring, gilt edges on the slab
    bx('altar_frontal', (1.06, .02, .62), (0, av - .32, CH + .43), pale, bevel=.004)
    bx('altar_front_field', (.96, .012, .52), (0, av - .336, CH + .43), SHAFT[0], uv=1.2, bevel=.002)
    bx('altar_cross_v', (.05, .014, .34), (0, av - .345, CH + .43), pale, bevel=.004)
    bx('altar_cross_h', (.22, .014, .05), (0, av - .345, CH + .48), pale, bevel=.004)
    bx('altar_edge', (2.32, .97, .02), (0, av, CH + .815), pale, bevel=.004)
    # reredos against the east wall: a green marble field in a gilded frame under a gable, gilded columns, a sunburst
    # behind the crucifix (its own model, hung in the level at RC), the tabernacle on a marble shelf
    rv = HV - T - .07                      # centre of the 14 cm thick panel
    RW, RH = 1.45, 3.55                    # half width, height above the chancel floor
    bx('reredos_field', (2 * RW, .14, RH), (0, rv, CH + RH / 2), SHAFT[0], uv=2.0, bevel=.004)
    for sx in (-1, 1):
        bx(f'reredos_frame{sx}', (.10, .18, RH), (sx * (RW + .05), rv, CH + RH / 2), pale, bevel=.01)
        tb(f'reredos_col{sx}', (sx * (RW + .26), rv - .08, CH + .32), (sx * (RW + .26), rv - .08, CH + RH - .5), .085, marble, 16)
        lathe(f'reredos_colbase{sx}', [(0, 0), (.15, 0), (.15, .1), (.11, .16), (.13, .22), (.10, .32), (0, .32)], B(sx * (RW + .26), rv - .08, CH), pale, 20)
        lathe(f'reredos_colcap{sx}', [(0, 0), (.095, 0), (.11, .05), (.15, .14), (.17, .2), (.17, .26), (0, .26)], B(sx * (RW + .26), rv - .08, CH + RH - .5), pale, 20)
        lathe(f'reredos_finial{sx}', [(0, 0), (.08, 0), (.10, .06), (.05, .14), (.07, .2), (.02, .32), (0, .34)], B(sx * (RW + .26), rv - .08, CH + RH - .24), pale, 16)
    bx('reredos_sill', (2 * RW + .9, .26, .09), (0, rv - .04, CH + RH - .045 - .0), pale, bevel=.012)
    gx = [(-RW - .15 + (2 * RW + .3) * i / 16) for i in range(17)]
    band('reredos_gable', [(x, CH + RH) for x in gx], [(x, CH + RH + .78 * (1 - abs(x) / (RW + .15))) for x in gx], rv - .09, rv + .07, SHAFT[0], xz(0), uv=2.0, bevel=.004)
    band('reredos_gable_rim', [(x, CH + RH + .78 * (1 - abs(x) / (RW + .15))) for x in gx],
         [(x, CH + RH + .09 + .78 * (1 - abs(x) / (RW + .15))) for x in gx], rv - .12, rv + .07, pale, xz(0), bevel=.006)
    lathe('reredos_top', [(0, 0), (.07, 0), (.09, .05), (.04, .12), (.06, .18), (.015, .3), (0, .31)], B(0, rv - .02, CH + RH + .86), pale, 16)
    RC = CH + 2.78                         # centre of the sunburst = the crossing of the crucifix
    for i in range(36):
        a = 2 * math.pi * i / 36
        r0, r1 = .50, (1.18 if i % 2 == 0 else .86)
        if abs(math.cos(a)) * r1 > RW - .06:      # the rays stay inside the frame
            r1 = (RW - .06) / abs(math.cos(a))
        tb(f'ray{i}', (math.cos(a) * r0, rv - .08, RC + math.sin(a) * r0), (math.cos(a) * r1, rv - .08, RC + math.sin(a) * r1), .026 if i % 2 == 0 else .016, pale, 6)
    ring = [(math.cos(2 * math.pi * i / 40) * .47, RC + math.sin(2 * math.pi * i / 40) * .47) for i in range(41)]
    ring2 = [(math.cos(2 * math.pi * i / 40) * .52, RC + math.sin(2 * math.pi * i / 40) * .52) for i in range(41)]
    band('ray_ring', ring, ring2, rv - .095, rv - .07, pale, xz(0), bevel=.003)
    # gradine (the shelf behind the altar table) and the tabernacle on it
    bx('gradine', (2.5, .30, .22), (0, rv - .22, CH + 1.03), marble, uv=1.2, bevel=.012)
    bx('gradine_foot', (2.3, .26, .92), (0, rv - .22, CH + .46), marble, uv=1.2, bevel=.01)
    bx('tabernacle', (.42, .26, .40), (0, rv - .22, CH + 1.34), pale, bevel=.012)
    bx('tabernacle_door', (.26, .012, .30), (0, rv - .355, CH + 1.33), SHAFT[0], uv=1.0, bevel=.003)
    bx('tabernacle_cross_v', (.03, .012, .2), (0, rv - .362, CH + 1.33), pale, bevel=.003)
    bx('tabernacle_cross_h', (.12, .012, .03), (0, rv - .362, CH + 1.36), pale, bevel=.003)
    lathe('tabernacle_dome', [(0, 0), (.20, 0), (.20, .03), (.14, .08), (.05, .11), (0, .12)], B(0, rv - .22, CH + 1.54), pale, 20)
    cx_, cv_ = -1.75, 3.75
    lathe('cross_foot', [(0, 0), (.16, 0), (.17, .03), (.10, .07), (.04, .12), (.03, .2), (0, .2)], B(cx_, cv_, CH), brass, 18)
    tb('cross_staff', (cx_, cv_, CH + .2), (cx_, cv_, CH + 2.05), .018, brass, 10)
    lathe('cross_knop', [(0, 0), (.03, .01), (.045, .04), (.03, .07), (0, .08)], B(cx_, cv_, CH + 1.72), brass, 14)
    bx('cross_post', (.035, .02, .46), (cx_, cv_, CH + 2.2), brass, bevel=.004)
    bx('cross_arm', (.30, .02, .035), (cx_, cv_, CH + 2.28), brass, bevel=.004)
    lx, lv = 1.9, 3.3
    bx('lectern_foot', (.42, .42, .05), (lx, lv, CH + .025), dark, bevel=.01)
    bx('lectern_post', (.09, .09, 1.02), (lx, lv, CH + .56), dark, bevel=.01)
    top = bx('lectern_top', (.5, .4, .03), (lx, lv + .03, CH + 1.12), wood, bevel=.006)
    top.rotation_euler = (math.radians(-24), 0, 0)
    bx('lectern_book', (.3, .22, .035), (lx, lv + .03, CH + 1.16), cloth, bevel=.006).rotation_euler = (math.radians(-24), 0, 0)
    # communion rail: turned balusters under a rail, open in the middle
    for sx in (-1, 1):
        bx(f'rail{sx}', (1.9, .07, .05), (sx * 2.45, 2.3, FL + .82), dark, uv=.9, bevel=.01)   # a way round it by the wall
        for i in range(8):
            px = sx * (1.56 + i * 1.78 / 7)
            lathe(f'baluster{sx}{i}', [(0, 0), (.035, 0), (.035, .06), (.02, .12), (.04, .3), (.02, .5), (.035, .7), (.035, .78), (0, .78)], B(px, 2.3, FL), dark, 12)

    # pews: 3 m long, crossing under the arcade between the pier lines
    # five rows a side: with a sixth by the door the pews and the piers closed every way into the side aisles
    for r, v in enumerate((-3.72, -2.84, -.9, -.02, .76)):   # clear of the piers at v = +-1.8 (plinth 42 cm)
        for sx in (-1, 1):
            pew(f'pew{sx}{r}', sx * .62, sx * 3.5, v, wood, dark)   # 90 cm left to the wall shafts
    # chains for the three chandeliers (the fixtures hang at 4.3 m, placed in the level)
    for v in (-3.6, 0.0, 3.6):
        tb(f'chain{v}', (0, v, NAVE_SPRING + NAVE_RISE - .08), (0, v, 4.95), .012, iron, 6)
    export(slug, 'Nave da igreja (interior)')


def rose():
    reset()
    slug = 'mare_church_rose'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    pale = material('Tracery', 'painted_plaster_wall', (.84, .81, .74), rough=.8, out=out)
    glass = _pic_material('Rosacea', _save(f'{slug}_Rosacea', rose_image(), out), .2)
    R = .85

    def circle(r, n=48):
        return [(r * math.cos(2 * math.pi * i / n), R + .12 + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    plane = lambda p, q, d: (p, d, q)     # front = -Y, origin on the wall under the rose's lowest point
    band('rim_outer', circle(R - .02), circle(R + .12), -.14, .0, pale, plane, uv=.8, closed=True)
    band('rim_inner', circle(R - .08), circle(R - .02), -.09, .0, pale, plane, uv=.8, closed=True)
    band('eye', circle(.085), circle(.13), -.09, -.01, pale, plane, uv=.6, closed=True)
    band('ring', circle(.50), circle(.535), -.075, -.01, pale, plane, uv=.6, closed=True)
    for k in range(12):
        a = math.pi / 12 + k * math.pi / 6
        ca, sa = math.cos(a), math.sin(a)
        tube(f'spoke{k}', (ca * .13, -.045, R + .12 + sa * .13), (ca * (R - .06), -.045, R + .12 + sa * (R - .06)), .022, pale, 8)
        ang = k * math.pi / 6
        rc = [(.70 * math.cos(ang) + r_ * math.cos(2 * math.pi * i / 20), R + .12 + .70 * math.sin(ang) + r_ * math.sin(2 * math.pi * i / 20)) for r_ in (.105, .135) for i in range(20)]
        band(f'roundel{k}', rc[:20], rc[20:], -.07, -.01, pale, plane, uv=.6, closed=True)
    bm = bmesh.new()
    vs = [bm.verts.new((p, -.02, q)) for p, q in circle(R - .05, 64)]
    face = bm.faces.new(vs)
    face.normal_update()
    if face.normal.y > 0:
        bmesh.ops.reverse_faces(bm, faces=[face])
    uvl = bm.loops.layers.uv.verify()
    for loop in face.loops:
        co = loop.vert.co
        loop[uvl].uv = (.5 + co.x / (2 * (R - .05)), .5 + (co.z - R - .12) / (2 * (R - .05)))
    bmesh.ops.triangulate(bm, faces=bm.faces)
    pane = mesh_obj('glass', bm)
    pane.data.materials.append(glass)
    export(slug, 'Rosácea da igreja')


if __name__ == '__main__':
    which = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [a for a in sys.argv[1:] if a in ('nave', 'rose')]
    for w in (which or ['nave', 'rose']):
        {'nave': nave, 'rose': rose}[w]()
        print('exported', w)
