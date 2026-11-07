"""Rustic check-in counter of the pousada (gameplay plan M2), in the style of the bungalows: oak plank counter
with a teal trim, a thatched shade on four posts, key board with hooks, brass service bell and guest book.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_reception_desk.py
Output: D:/Assets/Mare/mare_reception_desk/mare_reception_desk.glb (origin at the floor, front = -Y, 2.4 x 1.6 m)."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402  (bpy before the helpers that import bmesh/mathutils)
from gen_custom_furniture import OUT, box, export, lathe, material, reset, tube  # noqa: E402

SLUG = 'mare_reception_desk'


def desk():
    reset()
    out = OUT / SLUG
    out.mkdir(parents=True, exist_ok=True)
    oak = material('Oak', 'oak_wood_planks', None, rough=.6)
    trim = material('Trim', 'distressed_painted_planks', (.18, .44, .46), rough=.7, out=out)
    top = material('Top', 'oak_wood_planks', (.55, .38, .22), rough=.45, out=out)
    thatch = material('Thatch', 'thatch_roof_angled', (.74, .58, .36), rough=.95, out=out)
    brass = bpy.data.materials.new('Brass')
    brass.use_nodes = True
    p = brass.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (.78, .6, .3, 1)
    p.inputs['Metallic'].default_value = 1.0
    p.inputs['Roughness'].default_value = .3
    paper = material('Book', 'rough_linen', (.9, .86, .76), rough=.8, out=out)
    # Counter: front panel of vertical planks, plinth, trim rail and an overhanging top.
    W, D, H = 1.8, .6, 1.05
    for k in range(12):
        x = -W / 2 + W / 12 * (k + .5)
        box(f'plank{k}', (W / 12 - .006, .04, H - .1), (x, -D / 2, (H - .1) / 2 + .06), oak, uv=1.2, bevel=.004)
    box('plinth', (W + .04, D + .04, .08), (0, 0, .04), trim, uv=1.0)
    box('rail', (W + .02, .05, .06), (0, -D / 2 - .01, H - .14), trim, uv=1.0)
    for sx in (-1, 1):
        box(f'side{sx}', (.04, D, H - .1), (sx * W / 2, 0, (H - .1) / 2 + .06), oak, uv=1.2)
    box('back_shelf', (W - .1, .04, .5), (0, D / 2 - .05, .45), oak, uv=1.2)
    box('top', (W + .12, D + .14, .05), (0, -.02, H), top, uv=1.0, bevel=.012)
    # Thatched shade on four turned posts.
    for sx in (-1, 1):
        for sy in (-1, 1):
            lathe(f'post{sx}{sy}', [(.0, 0), (.06, 0), (.06, .05), (.045, .1), (.04, 2.35), (.055, 2.4), (0, 2.4)], (sx * 1.05, sy * .65 + .1, 0), oak, 16)
    box('beam_f', (2.3, .1, .12), (0, -.55, 2.42), oak, uv=1.2)
    box('beam_b', (2.3, .1, .12), (0, .75, 2.42), oak, uv=1.2)
    roof = box('roof', (2.6, 1.7, .22), (0, .1, 2.62), thatch, uv=.8, cuts=6)
    for v in roof.data.vertices:          # hip the thatch toward the edges
        e = max(abs(v.co.x) / 1.3, abs(v.co.y - .1) / .85)
        v.co.z -= .25 * e * e
    # Key board with brass hooks and tags, a service bell and the guest book.
    # The key board hangs on two rails between the back posts (nothing floats).
    for z in (1.3, 1.8):
        box(f'back_rail{z}', (2.1, .06, .07), (0, .72, z), oak, uv=1.2)
    box('keyboard', (.7, .03, .45), (0, .68, 1.55), trim, uv=1.0)
    for k in range(6):
        x = -.27 + k * .108
        lathe(f'hook{k}', [(0, 0), (.006, 0), (.006, .03), (0, .03)], (x, .655, 1.62), brass, 8)
        box(f'tag{k}', (.035, .006, .05), (x, .652, 1.57), top, uv=.3)
    lathe('bell_base', [(0, 0), (.045, 0), (.045, .01), (.0, .012)], (.55, -.12, H + .025), brass, 24)
    lathe('bell', [(.0, .01), (.04, .012), (.038, .03), (.026, .05), (.008, .062), (.006, .075), (0, .078)], (.55, -.12, H + .025), brass, 24)
    box('book', (.3, .22, .035), (-.35, -.08, H + .043), paper, rot=(0, 0, math.radians(8)), uv=.4)
    box('book_cover', (.31, .23, .01), (-.35, -.08, H + .028), trim, rot=(0, 0, math.radians(8)), uv=.4)
    export(SLUG, 'Balcão de recepção da pousada')


desk()
