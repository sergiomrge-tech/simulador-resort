"""The player's house, step 2 (11/11, Sergio: "está muito simples... quero mais realista"): the volumes a real house
has and the Godot box did not. One model laid over the house (placed at its centre, UE 4600, 2100, 0; local x = east,
v = north (Blender y = -v), z up, metres):
 - rafter tails under the eaves on the west, south and street sides, following the roof's underside (measured: 3.77 m
   at the wall face, falling 48 cm per metre), weathered wood;
 - zinc gutters on the west and south eaves with a downpipe at the south-west corner, on brackets;
 - the west window: plaster surround, a projecting sill and two open louvred shutters in faded green paint;
 - the big south window: surround and sill;
 - an electricity meter box with its conduit on the west wall, a garden tap on the south wall.
Openings measured in the level (mare_home.openings): west window v -0.6..0.6, z 1.16..2.42; south window x -2.6..-0.2,
z 1.01..2.47. Outer wall faces at 3.63 m from the centre. No collision wanted.
  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_home_dress.py
Output: D:/Assets/Mare/mare_home_dress/mare_home_dress.glb."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from gen_custom_furniture import OUT, box, export, lathe, material, reset, tube  # noqa: E402

SLUG = 'mare_home_dress'
F = 3.63                       # outer wall face from the centre
SLOPE = .48                    # roof underside: metres down per metre out
Z_FACE = 3.77                  # roof underside at the wall face
TH = math.atan(SLOPE)


def B(x, v, z):
    return (x, -v, z)


def main():
    reset()
    out = OUT / SLUG
    out.mkdir(parents=True, exist_ok=True)
    wood = material('Wood', 'oak_wood_planks', (.30, .22, .15), rough=.85, out=out)
    paint = material('Shutter', 'oak_wood_planks', (.36, .52, .46), rough=.75, out=out)
    plaster = material('Trim', 'painted_plaster_wall', (.80, .76, .66), rough=.9, out=out)
    zinc = material('Zinc', 'metal_plate', (.52, .54, .55), rough=.55, out=out)
    grey = material('Box', 'metal_plate', (.42, .43, .42), rough=.7, out=out)

    # ---- rafter tails: 7 x 10 cm, from 6 cm inside the wall face to 88 cm out, under the roof
    L = math.hypot(.94, .94 * SLOPE)
    mid_out = .41
    zc = Z_FACE - SLOPE * mid_out - .06
    k = 0
    for i in range(13):
        p = -3.3 + i * .55
        # west (outward = -x)
        box(f'raft_w{i}', (L, .07, .10), B(-F - mid_out, p, zc), wood, rot=(0, -TH, 0), bevel=.006, uv=.8)
        # street side, north (outward = +v = Blender -y)
        box(f'raft_n{i}', (.07, L, .10), B(p, F + mid_out, zc), wood, rot=(TH, 0, 0), bevel=.006, uv=.8)
        # south (outward = -v = Blender +y), not where the bathroom annex stands (x 0.05 .. 3.45)
        if p < -.1:
            box(f'raft_s{i}', (.07, L, .10), B(p, -F - mid_out, zc), wood, rot=(-TH, 0, 0), bevel=.006, uv=.8)
        k += 1
    # fascia boards closing the rafter ends
    zf = Z_FACE - SLOPE * .9 - .06
    box('fascia_w', (.025, 2 * F + 1.9, .14), B(-F - .9, 0, zf), wood, bevel=.004, uv=.8)
    box('fascia_n', (2 * F + 1.9, .025, .14), B(0, F + .9, zf), wood, bevel=.004, uv=.8)
    box('fascia_s', (F + .95, .025, .14), B(-(F + .95) / 2 + .0 - .0, -F - .9, zf), wood, bevel=.004, uv=.8)

    # ---- gutters (zinc) on the west and south eaves, downpipe at the south-west corner
    zg = zf - .05
    gx = F + .97
    tube('gutter_w', B(-gx, -gx, zg), B(-gx, F + .95, zg + .03), .055, zinc, 12)
    tube('gutter_s', B(-gx, -gx, zg), B(-.05, -gx, zg + .03), .055, zinc, 12)
    for i in range(6):
        v = -4.2 + i * 1.6
        box(f'gbracket_w{i}', (.07, .02, .10), B(-gx + .04, v, zg + .03), grey, bevel=.003)
        if i < 3:
            box(f'gbracket_s{i}', (.02, .07, .10), B(-4.2 + i * 1.6, -gx + .04, zg + .03), grey, bevel=.003)
    cx, cv = -F - .06, -F - .06
    tube('down_elbow', B(-gx, -gx, zg - .03), B(cx, cv, zg - .55), .04, zinc, 10)
    tube('down_pipe', B(cx, cv, zg - .55), B(cx, cv, .22), .04, zinc, 10)
    tube('down_shoe', B(cx, cv, .22), B(cx - .14, cv - .14, .08), .04, zinc, 10)
    for z in (.7, 1.7, 2.6):
        box(f'down_clip{z}', (.11, .11, .025), B(cx, cv, z), grey, bevel=.003)

    # ---- west window: surround, sill, two open shutters
    v0, v1, z0, z1 = -.6, .6, 1.16, 2.42
    xw = -F
    box('ww_sill', (.16, v1 - v0 + .24, .06), B(xw - .06, 0, z0 - .03), plaster, bevel=.012, uv=1.0)
    box('ww_sill_drip', (.10, v1 - v0 + .16, .03), B(xw - .04, 0, z0 - .075), plaster, bevel=.006, uv=1.0)
    box('ww_head', (.05, v1 - v0 + .2, .10), B(xw - .02, 0, z1 + .05), plaster, bevel=.008, uv=1.0)
    for sv in (-1, 1):
        box(f'ww_jamb{sv}', (.05, .09, z1 - z0), B(xw - .02, sv * (v1 + .045), (z0 + z1) / 2), plaster, bevel=.008, uv=1.0)
        # shutter leaf folded back on the wall beside the opening: 58 x 126 cm
        sc = sv * (v1 + .09 + .31)
        sx = xw - .035
        for dv in (-1, 1):
            box(f'sh_stile{sv}{dv}', (.035, .06, 1.26), B(sx, sc + dv * .26, (z0 + z1) / 2), paint, bevel=.004, uv=.7)
        for dz, nm in ((-.6, 'b'), (0, 'm'), (.6, 't')):
            box(f'sh_rail{sv}{nm}', (.035, .46, .07), B(sx, sc, (z0 + z1) / 2 + dz), paint, bevel=.004, uv=.7)
        for j in range(18):
            zz = z0 + .10 + j * .061
            if abs(zz - (z0 + z1) / 2) < .05:
                continue
            box(f'sh_slat{sv}{j}', (.03, .46, .012), B(sx, sc, zz), paint, rot=(0, math.radians(32), 0), bevel=.002, uv=.7)
        for dz in (-.4, .4):                              # hinges
            box(f'sh_hinge{sv}{dz}', (.02, .05, .09), B(xw - .012, sv * (v1 + .1), (z0 + z1) / 2 + dz), grey, bevel=.003)

    # ---- south window (x -2.6 .. -0.2, z 1.01 .. 2.47): surround and sill
    x0, x1, z0, z1 = -2.6, -.2, 1.01, 2.47
    vs = -F
    box('sw_sill', (x1 - x0 + .24, .16, .06), B((x0 + x1) / 2, vs - .06, z0 - .03), plaster, bevel=.012, uv=1.0)
    box('sw_sill_drip', (x1 - x0 + .16, .10, .03), B((x0 + x1) / 2, vs - .04, z0 - .075), plaster, bevel=.006, uv=1.0)
    box('sw_head', (x1 - x0 + .2, .05, .10), B((x0 + x1) / 2, vs - .02, z1 + .05), plaster, bevel=.008, uv=1.0)
    for sxn, xx in ((-1, x0 - .045), (1, x1 + .045)):
        box(f'sw_jamb{sxn}', (.09, .05, z1 - z0), B(xx, vs - .02, (z0 + z1) / 2), plaster, bevel=.008, uv=1.0)

    # ---- electricity meter box on the west wall near the street corner, conduit up to the eaves
    mv, mz = 2.55, 1.5
    box('meter', (.13, .34, .46), B(xw - .065, mv, mz), grey, bevel=.012)
    box('meter_door', (.012, .28, .34), B(xw - .135, mv, mz + .02), zinc, bevel=.004)
    box('meter_glass', (.014, .12, .10), B(xw - .137, mv, mz + .09), wood, bevel=.002)
    tube('meter_conduit', B(xw - .03, mv, mz + .23), B(xw - .03, mv, Z_FACE - .1), .014, grey, 8)
    tube('meter_earth', B(xw - .03, mv + .1, mz - .23), B(xw - .03, mv + .1, .05), .01, grey, 8)
    # ---- garden tap on the south wall
    tx = -3.1
    tube('tap_pipe', B(tx, vs - .03, .0), B(tx, vs - .03, .62), .012, zinc, 8)
    tube('tap_spout', B(tx, vs - .03, .62), B(tx, vs - .13, .60), .012, zinc, 8)
    lathe('tap_handle', [(0, 0), (.03, 0), (.03, .012), (0, .012)], B(tx, vs - .06, .64), grey, 10)
    for z in (.2, .5):
        box(f'tap_clip{z}', (.05, .02, .02), B(tx, vs - .012, z), grey, bevel=.002)
    export(SLUG, 'Casa do jogador: beiral, calhas, janelas (bpy)')


if __name__ == '__main__':
    main()
