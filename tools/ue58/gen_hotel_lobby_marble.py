"""Marble dressing of the Grand Hotel's main reception (11/11, Sergio: "na recepção principal do hotel faça esse
acabamento em mármore, ficou muito bom na igreja; dá uma caprichada com bastante detalhes e cores em mármore").

One model laid over the lobby shell of tools/ue58/hotel_lobby_shell.py (same Blender frame: front = -Y, z up, origin
the tower's; the level places it at the tower's transform). Nothing of the shell is removed:
 - floor: a 1.2 cm slab of polished marble drawn as ONE picture (31 x 11 m): cream field in 1 m tiles with black
   cabochons, a red border between yellow fillets, a 16-point compass rose in red, green, black and yellow on the
   entrance axis and two smaller roses between the columns;
 - walls (back and sides): a green marble dado under a gilded rail, book-matched cream panels between gilded strips,
   a red feature wall in a gilded frame behind the reception, black marble round the lift doors, a gilded cornice;
 - the four columns: red marble shafts on gilded bases under gilded bell capitals;
 - the reception desk: green panels in gilded frames on a black plinth, a black top; the entrance planters in black.
Marbles are drawn here with the church's vein generator (gen_church_nave.marble_image).
  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_hotel_lobby_marble.py
Output: D:/Assets/Mare/mare_lobby_marble/mare_lobby_marble.glb (no collision wanted: visual only)."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
import gen_church_nave as N  # noqa: E402
from gen_custom_furniture import OUT, box, export, finish, lathe, mesh_obj, reset  # noqa: E402

SLUG = 'mare_lobby_marble'
X0, X1, Y0, Y1 = -15.5, 15.5, -5.12, 5.8        # inner faces: side walls, glass line, back wall
Z0, CEIL = .45, 4.5                              # floor, underside of the wood ribs
PAL = {'crema': ((.90, .84, .72), (.55, .42, .30), (.80, .62, .30)), 'rosso': ((.50, .11, .08), (.92, .86, .80), (.80, .60, .28)),
       'verde': ((.10, .25, .17), (.86, .88, .80), (.80, .64, .30)), 'nero': ((.035, .035, .04), (.85, .83, .78), (.78, .58, .24)),
       'giallo': ((.82, .60, .22), (.46, .26, .10), (.95, .88, .70))}


def slab(name, seed, n=1024, veins=1.0):
    base, vein, second = PAL[name]
    return N.marble_image(base, vein, seed, n, second=second, veins=veins)


def floor_picture(w=4096):
    """The whole floor, 1 px = 7.6 mm across, 5.3 mm deep. Pixel (0, 0) = (X0, Y1) (the back left corner seen from the entrance)."""
    h = w // 2          # power of two for Unreal (4096 x 1454 was rejected); the slab's UV runs 0..1, so the pixels are just not square
    xs = X0 + (np.arange(w) + .5) / w * (X1 - X0)
    ys = Y1 - (np.arange(h) + .5) / h * (Y1 - Y0)
    X, Y = np.meshgrid(xs, ys)
    tiles = {k: slab(k, 40 + i, 2048, .9 if k != 'crema' else 1.0) for i, k in enumerate(PAL)}
    ii, jj = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')

    def sample(name, off=0):
        t = tiles[name]
        return t[(ii + off * 331) % 2048, (jj + off * 173) % 2048]
    # field: 1 m cream tiles, every tile from its own slab
    cu, cv = np.floor(X + 100), np.floor(Y + 100)
    off = ((cu * 7 + cv * 13) % 11).astype(np.int64)
    img = tiles['crema'][(ii + off * 331) % 2048, (jj + off * 173) % 2048].copy()
    fu, fv = X - np.floor(X), Y - np.floor(Y)
    joint = (np.minimum(fu, 1 - fu) < .004) | (np.minimum(fv, 1 - fv) < .004)
    cab = (np.abs(fu - np.round(fu)) + np.abs(fv - np.round(fv))) < .085          # black diamonds on the tile corners
    img[cab] = sample('nero', 3)[cab]
    # border: yellow fillet, red band, yellow fillet, 35 cm in from the walls
    d = np.minimum(np.minimum(X - X0, X1 - X), np.minimum(Y - Y0, Y1 - Y))
    for lo, hi, name in ((.35, .41, 'giallo'), (.41, .86, 'rosso'), (.86, .92, 'giallo'), (.0, .35, 'nero')):
        m = (d >= lo) & (d < hi)
        img[m] = sample(name, 5)[m]
    joint |= (np.abs(d - .35) < .004) | (np.abs(d - .92) < .004) | (np.abs(d - .41) < .003) | (np.abs(d - .86) < .003)

    def rose(cx, cy, R, points):
        dx, dy = X - cx, Y - cy
        r, th = np.hypot(dx, dy), np.arctan2(dy, dx)
        inside = r < R
        img[inside] = sample('crema', 7)[inside]
        ring = (r >= R * .88) & (r < R)
        img[ring] = sample('rosso', 2)[ring]
        ring2 = ((r >= R * .84) & (r < R * .88)) | ((r >= R * .985) & (r < R * 1.03))
        img[ring2] = sample('giallo', 4)[ring2]
        for k, (length, half, name) in enumerate(((.82, math.pi / points, 'rosso'), (.60, math.pi / points, 'verde'))):
            a = (th + (math.pi / points if k else 0)) % (2 * math.pi / (points / 2))
            a = np.abs(a - math.pi / (points / 2))                                 # angle from the nearest point axis
            edge = R * length * (1 - a / half) / (1 + a / half * 1.6)              # a slim star point
            m = (r < np.maximum(edge, 0)) & (a < half) & (r > R * .16)
            img[m] = sample(name, 6 + k)[m]
            dark = m & (((th + (math.pi / points if k else 0)) % (2 * math.pi / (points / 2))) > math.pi / (points / 2))
            img[dark] = sample('nero', 8)[dark] if k == 0 else img[dark] * .78       # each point in two halves
        c1 = r < R * .16
        img[c1] = sample('nero', 9)[c1]
        c2 = (r >= R * .16) & (r < R * .2)
        img[c2] = sample('giallo', 4)[c2]
        return (np.abs(r - R * .88) < .004) | (np.abs(r - R) < .004) | (np.abs(r - R * .2) < .003)
    joint |= rose(0.0, -1.3, 2.35, 16)
    joint |= rose(-7.0, -1.3, 1.25, 8)
    joint |= rose(7.0, -1.3, 1.25, 8)
    img[joint] *= .6
    return np.clip(img, 0, 1)


FRESCO_SRC = Path('D:/Assets/Mare/mare_lobby_marble/fresco_src.png')


def fresco_picture(w=4096):
    """11/11 (Sergio: "no teto da recepção faça uma pintura estilo afresco da paisagem do mar com a vila"): the ceiling
    painting. The subject is the game's own village seen from the sea (a screenshot taken in the level, FRESCO_SRC);
    here it becomes a fresco: the detail is brushed out into flat patches of colour, the palette goes chalky (lifted
    darks, lower saturation, a warm lime-plaster cast), the pigment has faded in blotches, the plaster shows its grain
    and a net of fine cracks, and the picture dies into bare plaster towards the frame."""
    from PIL import Image, ImageFilter
    h = w // 2
    src = Image.open(FRESCO_SRC).convert('RGB')
    # the ceiling is 31 x 11 m: take the widest 2.82 : 1 band of the photo, then fit it to the 2 : 1 picture
    sw, sh = src.size
    band = min(sh, int(sw / ((X1 - X0) / (Y1 - Y0))))
    top = max(0, int((sh - band) * .45))
    src = src.crop((0, top, sw, top + band))
    small = src.resize((w // 5, h // 5), Image.LANCZOS)
    for _ in range(2):                                   # brush the detail out
        small = small.filter(ImageFilter.ModeFilter(7)).filter(ImageFilter.MedianFilter(5))
    paint = np.asarray(small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    # brush strokes: the colour is nudged along a smooth noise direction
    ii, jj = np.meshgrid(np.arange(h), np.arange(w), indexing='ij')
    n1 = np.kron(N._fft_noise(1024, 2.0, 71), np.ones((4, 4), np.float32))[:h, :w]
    n2 = np.kron(N._fft_noise(1024, 2.0, 72), np.ones((4, 4), np.float32))[:h, :w]
    paint = paint[(ii + (n1 * 9).astype(np.int32)) % h, (jj + (n2 * 14).astype(np.int32)) % w]
    lum = paint @ np.array((.3, .59, .11), np.float32)
    paint = lum[:, :, None] + (paint - lum[:, :, None]) * .78                     # less saturated
    paint = .10 + paint * .84                                                    # chalky: no deep darks
    paint *= np.array((1.04, 1.0, .92), np.float32)                              # the warm cast of lime plaster
    plaster = np.array((.86, .82, .72), np.float32)
    fade = np.clip(N._fft_noise(1024, 2.6, 73), 0, 1)
    fade = np.kron(fade, np.ones((4, 4), np.float32))[:h, :w] * .38              # blotches where the pigment has gone
    paint = paint * (1 - fade[:, :, None]) + plaster[None, None, :] * fade[:, :, None]
    grain = np.kron(N._fft_noise(1024, 1.1, 74), np.ones((4, 4), np.float32))[:h, :w]
    paint *= (1 + .05 * grain)[:, :, None]
    crack = N._fft_noise(1024, 1.7, 75)
    cw_ = np.kron(np.clip(1 - np.abs(crack) / .006, 0, 1) + .6 * np.clip(1 - np.abs(crack - .3) / .004, 0, 1), np.ones((4, 4), np.float32))[:h, :w]
    paint *= (1 - .32 * np.clip(cw_, 0, 1))[:, :, None]
    # towards the frame the painting gives way to bare plaster
    u, v = (jj + .5) / w, (ii + .5) / h
    edge = np.minimum(np.minimum(u, 1 - u) * (X1 - X0), np.minimum(v, 1 - v) * (Y1 - Y0))      # metres from the frame
    keep = np.clip(edge / .55, 0, 1) ** .8
    paint = paint * keep[:, :, None] + (plaster * (1 + .04 * grain[:, :, None])) * (1 - keep[:, :, None])
    return np.clip(paint, 0, 1)


def ceiling_uv(name, x0, x1, y0, y1, z, mat):
    """The painted ceiling: a plane facing DOWN, the picture read from the entrance (its top towards the back wall)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    vs = [bm.verts.new(p) for p in ((x0, y0, z), (x0, y1, z), (x1, y1, z), (x1, y0, z))]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.z > 0:
        bmesh.ops.reverse_faces(bm, faces=[f])
    for loop in f.loops:
        loop[uv].uv = ((loop.vert.co.x - x0) / (x1 - x0), (loop.vert.co.y - y0) / (y1 - y0))
    o = mesh_obj(name, bm)
    o.data.materials.append(mat)
    return o


def pic_mat(name, img, out, rough, metal=0.0):
    m = N._pic_material(name, N._save(f'{SLUG}_{name}', img, out), rough)
    return m


def gold():
    m = bpy.data.materials.new('Gold')
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (1.0, .74, .30, 1)
    p.inputs['Metallic'].default_value = 1.0
    p.inputs['Roughness'].default_value = .26
    return m


def plane_uv(name, x0, x1, y0, y1, z, mat):
    """The floor slab: top face mapped 0..1 on the picture."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    vs = [bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    f = bm.faces.new(vs)
    for loop in f.loops:
        loop[uv].uv = ((loop.vert.co.x - x0) / (x1 - x0), (loop.vert.co.y - y0) / (y1 - y0))
    f.normal_update()
    if f.normal.z < 0:
        bmesh.ops.reverse_faces(bm, faces=[f])
    o = mesh_obj(name, bm)
    o.data.materials.append(mat)
    return o


def main():
    reset()
    out = OUT / SLUG
    out.mkdir(parents=True, exist_ok=True)
    m = {k: pic_mat(k.capitalize(), slab(k, 60 + i, 2048), out, .16) for i, k in enumerate(PAL)}
    g = gold()
    floor = pic_mat('Floor', floor_picture(), out, .12)
    plane_uv('floor', X0, X1, Y0, Y1, Z0 + .012, floor)

    # ---- the painted ceiling between the wood ribs (their underside is at 4.5, the plaster at 4.62), in a gilded frame
    if FRESCO_SRC.exists():
        fres = pic_mat('Fresco', fresco_picture(), out, .92)
        ceiling_uv('ceiling_fresco', X0 + .16, X1 - .16, Y0 + .02, Y1 - .16, 4.612, fres)
        for sx in (-1, 1):
            box(f'fresco_frame_x{sx}', (.10, Y1 - Y0 - .2, .05), (sx * (X1 - .2), (Y0 + Y1) / 2, 4.59), g, bevel=.012)
        for sy, yy in ((-1, Y0 + .06), (1, Y1 - .2)):
            box(f'fresco_frame_y{sy}', (X1 - X0 - .3, .10, .05), (0, yy, 4.59), g, bevel=.012)
    T = .05                                                     # cladding thickness (the old wood panels stand 4 cm proud)
    # ---- back wall (y = Y1), leaving the lift doors (x 4.12..5.88 and 7.12..8.88, to z0 + 2.6) open
    doors = ((4.1, 5.9), (7.1, 8.9))
    spans, x = [], X0
    for a, b in doors:
        spans.append((x, a))
        x = b
    spans.append((x, X1))
    DADO = Z0 + 1.0
    for i, (a, b) in enumerate(spans):
        box(f'back_dado{i}', (b - a, T, DADO - Z0), ((a + b) / 2, Y1 - T / 2, (Z0 + DADO) / 2), m['verde'], uv=2.0, bevel=.004)
        box(f'back_plinth{i}', (b - a, T + .03, .14), ((a + b) / 2, Y1 - T / 2 - .015, Z0 + .07), m['nero'], uv=2.0, bevel=.006)
        box(f'back_rail{i}', (b - a, T + .04, .07), ((a + b) / 2, Y1 - T / 2 - .02, DADO + .035), g, bevel=.012)
        # cream panels 2.2 m wide between gilded strips; the feature wall behind the reception is red
        n = max(1, int(round((b - a) / 2.2)))
        for k in range(n):
            pa, pb = a + (b - a) * k / n, a + (b - a) * (k + 1) / n
            feature = -10.1 < (pa + pb) / 2 < -4.1
            box(f'back_panel{i}_{k}', (pb - pa - .06, T, CEIL - .22 - DADO - .07), ((pa + pb) / 2, Y1 - T / 2, (CEIL - .22 + DADO + .07) / 2),
                m['rosso' if feature else 'crema'], uv=2.4, bevel=.004)
            box(f'back_strip{i}_{k}', (.06, T + .025, CEIL - .22 - DADO - .07), (pa + .0, Y1 - T / 2 - .012, (CEIL - .22 + DADO + .07) / 2), g, bevel=.008)
        box(f'back_strip{i}_end', (.06, T + .025, CEIL - .22 - DADO - .07), (b, Y1 - T / 2 - .012, (CEIL - .22 + DADO + .07) / 2), g, bevel=.008)
    for a, b in doors:                                           # black marble architrave round each lift, the wall over it
        box(f'lift_over{a}', (b - a, T, CEIL - .22 - (Z0 + 2.6)), ((a + b) / 2, Y1 - T / 2, (CEIL - .22 + Z0 + 2.6) / 2), m['crema'], uv=2.4, bevel=.004)
        for sx, xx in ((-1, a), (1, b)):
            box(f'lift_jamb{a}{sx}', (.16, T + .05, 2.74), (xx, Y1 - T / 2 - .025, Z0 + 1.37), m['nero'], uv=1.5, bevel=.012)
        box(f'lift_head{a}', (b - a + .32, T + .05, .16), ((a + b) / 2, Y1 - T / 2 - .025, Z0 + 2.68), m['nero'], uv=1.5, bevel=.012)
        box(f'lift_key{a}', (.24, T + .08, .24), ((a + b) / 2, Y1 - T / 2 - .04, Z0 + 2.68), g, bevel=.02)
    # the hotel's emblem on the feature wall: a gilded sun over waves, in a gilded frame
    fx, fz = -7.1, Z0 + 2.75
    for sx in (-1, 1):
        box(f'feat_frame_v{sx}', (.07, T + .03, 2.5), (fx + sx * 2.7, Y1 - T - .015, fz), g, bevel=.012)
        box(f'feat_frame_h{sx}', (5.47, T + .03, .07), (fx, Y1 - T - .015, fz + sx * 1.25), g, bevel=.012)
    lathe('emblem_sun', [(0, 0), (.34, 0), (.36, .012), (.30, .03), (0, .034)], (0, 0, 0), g, 40).rotation_euler = (math.pi / 2, 0, 0)
    bpy.data.objects['emblem_sun'].location = (fx, Y1 - T - .0, fz + .22)
    for i in range(16):
        a = math.pi * i / 15
        o = box(f'emblem_ray{i}', (.035, .02, .30 if i % 2 == 0 else .18), (0, 0, 0), g, bevel=.006)
        r = .44 + (.15 if i % 2 == 0 else .09)
        o.rotation_euler = (0, math.pi / 2 - a, 0)
        o.location = (fx + math.cos(a) * r, Y1 - T - .015, fz + .22 + math.sin(a) * r)
    for k in range(3):
        box(f'emblem_wave{k}', (1.5 - k * .3, .02, .04), (fx, Y1 - T - .015, fz - .18 - k * .12), g, bevel=.012)

    # ---- side walls: dado, panels between gilded strips (the old wood panels and their 8 cm are covered)
    T2 = .07
    for sx in (-1, 1):
        xw = sx * (X1 - T2 / 2)
        L = Y1 - Y0
        box(f'side_dado{sx}', (T2, L, DADO - Z0), (xw, (Y0 + Y1) / 2, (Z0 + DADO) / 2), m['verde'], uv=2.0, bevel=.004)
        box(f'side_plinth{sx}', (T2 + .03, L, .14), (xw - sx * .015, (Y0 + Y1) / 2, Z0 + .07), m['nero'], uv=2.0, bevel=.006)
        box(f'side_rail{sx}', (T2 + .04, L, .07), (xw - sx * .02, (Y0 + Y1) / 2, DADO + .035), g, bevel=.012)
        for k in range(5):
            pa, pb = Y0 + L * k / 5, Y0 + L * (k + 1) / 5
            box(f'side_panel{sx}{k}', (T2, pb - pa - .06, CEIL - .22 - DADO - .07), (xw, (pa + pb) / 2, (CEIL - .22 + DADO + .07) / 2),
                m['giallo' if k % 2 else 'crema'], uv=2.4, bevel=.004)
            box(f'side_strip{sx}{k}', (T2 + .025, .06, CEIL - .22 - DADO - .07), (xw - sx * .012, pa, (CEIL - .22 + DADO + .07) / 2), g, bevel=.008)
    # ---- cornice all round under the ceiling (back and sides)
    box('cornice_back', (X1 - X0, .16, .22), (0, Y1 - .08, CEIL - .11), g, bevel=.03)
    for sx in (-1, 1):
        box(f'cornice_side{sx}', (.16, Y1 - Y0, .22), (sx * (X1 - .08), (Y0 + Y1) / 2, CEIL - .11), g, bevel=.03)

    # ---- columns: red shafts over the old plaster ones (r 24 cm), gilded base and capital
    for cx in (-10.5, -3.5, 3.5, 10.5):
        cy = .6
        lathe(f'col_base{cx}', [(0, 0), (.42, 0), (.42, .10), (.37, .14), (.40, .20), (.34, .27), (.33, .32), (0, .32)], (cx, cy, Z0), g, 32)
        lathe(f'col_plinth{cx}', [(0, 0), (.46, 0), (.46, .06), (0, .06)], (cx, cy, Z0 - .0), m['nero'], 8)
        lathe(f'col_shaft{cx}', [(0, 0), (.30, 0), (.305, 1.3), (.285, 3.34), (0, 3.34)], (cx, cy, Z0 + .32), m['rosso'], 40, uv=1.2)
        lathe(f'col_cap{cx}', [(0, 0), (.30, 0), (.32, .04), (.30, .08), (.33, .12), (.42, .28), (.48, .36), (.50, .40), (.50, .44), (0, .44)],
              (cx, cy, Z0 + 3.66), g, 32)
        box(f'col_abacus{cx}', (1.04, 1.04, .08), (cx, cy, Z0 + 4.11), m['nero'], uv=1.5, bevel=.012)

    # ---- reception desk (body x -9.6..-4.6, y 1.3..2.1, 1.02 high, stone top to 1.10)
    dx0, dx1, dy0, dy1 = -9.6, -4.6, 1.3, 2.1
    F = dy0 - .075                                              # in front of the old fluting (it reaches y0 - .04)
    box('desk_plinth', (dx1 - dx0 + .1, .05, .16), ((dx0 + dx1) / 2, F - .0, Z0 + .08), m['nero'], uv=1.5, bevel=.008)
    for k in range(5):
        pa, pb = dx0 + (dx1 - dx0) * k / 5, dx0 + (dx1 - dx0) * (k + 1) / 5
        box(f'desk_panel{k}', (pb - pa - .1, .035, .70), ((pa + pb) / 2, F + .01, Z0 + .57), m['verde' if k % 2 == 0 else 'rosso'], uv=1.5, bevel=.004)
        for sx in (-1, 1):
            box(f'desk_fv{k}{sx}', (.03, .05, .76), ((pa + pb) / 2 + sx * (pb - pa - .1) / 2, F, Z0 + .57), g, bevel=.008)
            box(f'desk_fh{k}{sx}', (pb - pa - .07, .05, .03), ((pa + pb) / 2, F, Z0 + .57 + sx * .365), g, bevel=.008)
    box('desk_front', (dx1 - dx0 + .06, .03, .86), ((dx0 + dx1) / 2, F + .035, Z0 + .59), m['crema'], uv=1.5, bevel=.003)
    for sx, xx in ((-1, dx0), (1, dx1)):                        # the two ends of the desk
        box(f'desk_end{sx}', (.035, dy1 - dy0 + .1, .98), (xx + sx * .03, (dy0 + dy1) / 2 - .03, Z0 + .51), m['crema'], uv=1.5, bevel=.004)
    box('desk_top', (dx1 - dx0 + .26, dy1 - dy0 + .27, .035), ((dx0 + dx1) / 2, (dy0 + dy1) / 2 - .035, Z0 + 1.118), m['nero'], uv=1.5, bevel=.012)
    box('desk_top_edge', (dx1 - dx0 + .28, .02, .02), ((dx0 + dx1) / 2, dy0 - .175, Z0 + 1.09), g, bevel=.006)
    # ---- entrance planters (x +-2.4, y -4.9..-4.3, 50 cm): black marble with a gilded band
    for sx in (-1, 1):
        for name, size, loc, mat in (('f', (1.26, .03, .5), (sx * 2.4, -4.27, Z0 + .25), m['nero']), ('b', (1.26, .03, .5), (sx * 2.4, -4.93, Z0 + .25), m['nero']),
                                     ('l', (.03, .66, .5), (sx * 2.4 - .63, -4.6, Z0 + .25), m['nero']), ('r', (.03, .66, .5), (sx * 2.4 + .63, -4.6, Z0 + .25), m['nero'])):
            box(f'planter{sx}{name}', size, loc, mat, uv=1.5, bevel=.004)
        box(f'planter_band{sx}', (1.30, .70, .03), (sx * 2.4, -4.6, Z0 + .47), g, bevel=.008)
    export(SLUG, 'Recepção do Grand Hotel: revestimento em mármore')


if __name__ == '__main__':
    main()
