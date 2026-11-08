"""Fishing spot at the end of the pier (08/11, Sergio: "tudo que for clicável precisa ter essa borda"): the "Pescar na
ponta do píer" target had nothing to look at, so there is now a fishing rod leaning on a wooden bait bucket. No CC0 rod
exists on Poly Haven (searched 08/11), so it is modelled here: a tapered dark blank with a cork grip, a reel seat and a
spinning reel, line guides and the line down to a hook by the bucket; the bucket is staved oak with two iron hoops and
a rope handle laid down. Origin = the bucket's base centre on the deck; the rod rests on the near (-X) rim and rises over
the bucket toward +X.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_fishing_spot.py
Output: D:/Assets/Mare/mare_fishing_spot/mare_fishing_spot.glb."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from gen_custom_furniture import export, lathe, material, reset, tube  # noqa: E402

SLUG = 'mare_fishing_spot'


def plain(name, colour, rough, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    return m


def ring(name, centre, axis, radius, thick, mat, sides=28):
    """A thin hoop/guide ring as a chain of short tubes."""
    axis = Vector(axis).normalized()
    a = axis.orthogonal().normalized()
    b = axis.cross(a)
    pts = [Vector(centre) + (a * math.cos(2 * math.pi * i / sides) + b * math.sin(2 * math.pi * i / sides)) * radius for i in range(sides + 1)]
    for i in range(sides):
        tube(f'{name}_{i}', pts[i], pts[i + 1], thick, mat, sides=6)


def along(base, direction, length, profile, name, mat, sides=16):
    """Lathe along a direction: profile (radius, distance) from base."""
    obj = lathe(name, profile, (0, 0, 0), mat, sides=sides, uv=.2)
    d = Vector(direction).normalized()
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    obj.location = base
    return obj


def main():
    reset()
    OUTDIR = Path('D:/Assets/Mare') / SLUG
    OUTDIR.mkdir(parents=True, exist_ok=True)
    wood = material('stave', 'oak_wood_planks', tint=(.55, .38, .22), rough=.6, out=OUTDIR)
    iron = plain('iron', (.12, .11, .1), .55, .8)
    rope = plain('rope', (.62, .52, .36), .9)
    cork = plain('cork', (.62, .46, .3), .85)
    blank = plain('blank', (.05, .08, .11), .25)
    chrome = plain('chrome', (.75, .76, .78), .25, .95)
    reelbody = plain('reel', (.1, .1, .11), .35, .4)
    line = plain('line', (.85, .85, .8), .4)
    water = plain('bait_water', (.12, .16, .14), .1)

    # Bucket: outer wall and inner wall in one turned shell, staves suggested by the oak texture; water inside.
    prof = [(0.0, 0.0), (.135, 0.0), (.138, .01), (.158, .30), (.146, .30), (.127, .03), (0.0, .03)]
    lathe('bucket', prof, (0, 0, 0), wood, sides=32, uv=.4)
    lathe('bait', [(0.0, .2), (.143, .2), (0.0, .2001)], (0, 0, 0), water, sides=32)
    for z, r in ((.06, .1415), (.25, .1555)):
        lathe(f'hoop{z}', [(r, z - .012), (r + .004, z - .01), (r + .004, z + .01), (r, z + .012)], (0, 0, 0), iron, sides=32)
    # rope handle over the top, tied to two lugs
    for s in (-1, 1):
        tube(f'lug{s}', (0, s * .158, .27), (0, s * .175, .27), .012, iron, sides=10)
    # the handle lies down over the far side (+X), clear of the rod
    lean = Vector((math.cos(math.radians(15)), 0, math.sin(math.radians(15))))
    pts = [Vector((0, math.cos(t) * .175, .27)) + lean * math.sin(t) * .13 for t in [i * math.pi / 10 for i in range(11)]]
    for i in range(10):
        tube(f'handle{i}', pts[i], pts[i + 1], .007, rope, sides=8)

    # Rod: butt on the deck at -X, resting on the bucket rim at +X, tip high over the water.
    butt = Vector((-.75, .02, .015))
    rest = Vector((-.165, .0, .312))   # on the near rim: past it the rod rises clear over the bucket
    d = (rest - butt).normalized()
    L = 2.3
    along(butt, d, L, [(.0, 0), (.017, 0), (.018, .02), (.018, .30), (.012, .32), (.011, .40), (.0115, .46),
                        (.0095, .48), (.0085, .9), (.0065, 1.5), (.0042, 2.0), (.0025, L), (0.0, L + .001)], 'rod', blank)
    along(butt, d, .3, [(.0, .02), (.0186, .02), (.0186, .30), (.0, .30)], 'grip', cork)
    along(butt, d, .1, [(.0, .33), (.0128, .33), (.0128, .44), (.0, .44)], 'seat', chrome)
    # spinning reel under the seat: foot, body, spool and crank
    up = Vector((0, 0, 1))
    side = d.cross(up).normalized()
    down = side.cross(d).normalized() * -1
    seat = butt + d * .385
    tube('reel_foot', seat, seat + down * .05, .006, chrome, sides=10)
    body_c = seat + down * .075
    tube('reel_body', body_c - d * .03, body_c + d * .03, .028, reelbody, sides=24)
    tube('reel_spool', body_c + d * .03, body_c + d * .065, .024, chrome, sides=24)
    tube('reel_line', body_c + d * .033, body_c + d * .062, .0245, line, sides=24)
    tube('crank', body_c, body_c + side * .06, .004, chrome, sides=8)
    tube('knob', body_c + side * .06, body_c + side * .06 + down * .025, .007, reelbody, sides=10)
    # guides, shrinking toward the tip, and the line through them down to a hook by the bucket
    guide_pts = []
    for i, t in enumerate((.75, 1.1, 1.45, 1.75, 2.0, 2.2)):
        c = butt + d * t + down * (.022 - i * .002)
        ring(f'guide{i}', c, d, .012 - i * .0012, .0012, chrome, sides=14)
        tube(f'guide_leg{i}', butt + d * t, c, .0012, chrome, sides=6)
        guide_pts.append(c)
    tip = butt + d * L
    pts = [body_c + d * .05] + guide_pts + [tip]
    for i in range(len(pts) - 1):
        tube(f'line{i}', pts[i], pts[i + 1], .0006, line, sides=4)
    hook = Vector((tip.x + .02, tip.y, .45))
    tube('line_drop', tip, hook, .0006, line, sides=4)
    tube('sinker', hook, hook - Vector((0, 0, .025)), .006, iron, sides=10)
    export(SLUG, 'Fishing rod on a bait bucket')


if __name__ == '__main__':
    main()
