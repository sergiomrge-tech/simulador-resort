"""Bellhop luggage cart of the pousada (replaces the Godot export World_0061-0064: a pink slab and three yellow rods).
Carpeted platform with a brass bumper rim, four swivel casters, two brass uprights joined by an arched top bar and
a hanging rail. No free CC0/CC-BY cart was found (03/11/2026), so it is modelled here; carpet from Poly Haven
denim_fabric (CC0) tinted burgundy. Built in World_0061's frame: platform 90 x 60 x 6 cm centred on the origin,
uprights at x = +-0.40, casters reaching 17 cm below the platform centre.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_luggage_cart.py
Output: D:/Assets/Mare/luggage_cart/luggage_cart.glb."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from gen_custom_furniture import box, export, lathe, material, reset, tube  # noqa: E402

OUT = Path('D:/Assets/Mare/luggage_cart')
L, W, T = .90, .60, .06          # platform
POST_X, TOP = .40, 1.40          # uprights and the top of the arch, from the platform centre
WHEEL_R = .05
CASTER_DROP = .17                # platform centre -> floor


def plain(name, colour, rough, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    return m


def main():
    reset()
    OUT.mkdir(parents=True, exist_ok=True)
    carpet = material('carpet', 'denim_fabric', tint=(.42, .07, .09), rough=.95, out=OUT)
    brass = plain('brass', (.80, .60, .28), .28, .95)
    rubber = plain('rubber', (.05, .05, .05), .7)
    steel = plain('steel', (.55, .55, .56), .35, .9)
    # platform: wooden core under the carpet, the bumper rim of brass tube around it
    box('platform', (L, W, T), (0, 0, 0), carpet, bevel=.012, uv=.6)
    rim_z, r = 0, .014
    corners = [(-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2)]
    for k in range(4):
        (x0, y0), (x1, y1) = corners[k], corners[(k + 1) % 4]
        tube(f'rim{k}', (x0, y0, rim_z), (x1, y1, rim_z), r, brass, sides=16)
        lathe(f'corner{k}', [(.0005, -r), (r * .8, -r * .6), (r, 0), (r * .8, r * .6), (.0005, r)], (x0, y0, rim_z), brass, sides=16)
    # casters: swivel plate, fork, wheel
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (L / 2 - .07), sy * (W / 2 - .07)
            z0 = -T / 2
            lathe(f'swivel{sx}{sy}', [(.0005, 0), (.032, 0), (.032, -.008), (.018, -.016), (.0005, -.016)], (x, y, z0), steel, sides=20)
            hub_z = -CASTER_DROP + WHEEL_R
            for side in (-1, 1):
                box(f'fork{sx}{sy}{side}', (.012, .004, z0 - .016 - hub_z + .012), (x, y + side * .021, (z0 - .016 + hub_z) / 2), steel, bevel=.0015)
            tube(f'wheel{sx}{sy}', (x, y - .016, hub_z), (x, y + .016, hub_z), WHEEL_R, rubber, sides=28)
            tube(f'hub{sx}{sy}', (x, y - .019, hub_z), (x, y + .019, hub_z), .014, steel, sides=16)
    # uprights with a base flange, the arched top bar and the hanging rail
    post_top = TOP - .10
    for sx in (-1, 1):
        x = sx * POST_X
        lathe(f'flange{sx}', [(.0005, 0), (.035, 0), (.035, .008), (.02, .016), (.0005, .016)], (x, 0, T / 2), brass, sides=20)
        tube(f'post{sx}', (x, 0, T / 2), (x, 0, post_top), .017, brass, sides=18)
    steps = 16
    pts = []
    for i in range(steps + 1):
        a = math.pi * i / steps
        pts.append((-POST_X * math.cos(a), 0, post_top + (TOP - post_top) * math.sin(a)))
    for i in range(steps):
        tube(f'arch{i}', pts[i], pts[i + 1], .017, brass, sides=18)
    tube('rail', (-POST_X, 0, post_top - .08), (POST_X, 0, post_top - .08), .011, brass, sides=16)
    for o in bpy.context.scene.objects:
        o.select_set(True)
        for mod in list(o.modifiers):
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.view_layer.objects.active = bpy.data.objects['platform']
    bpy.ops.object.join()
    bpy.context.active_object.name = 'luggage_cart'
    export('luggage_cart', 'Pousada bellhop luggage cart (bpy)')


if __name__ == '__main__':
    main()
