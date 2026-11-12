"""Rear of the village food truck (09/11 visual checklist: "caixote vermelho liso, sem portas nem lanternas").
The truck itself is the Godot-era model `biz_food_truck` (tools/gen_business.py): its box body ends in a flat cap at
x = -2.6 m with a thin bumper and two 12 cm lamps, which from the main street reads as a plain red crate. This is an
add-on in the truck's own frame (same origin, zero rotation), placed over that cap: door frame with a chrome sill, two
door leaves with rails and recessed panels, rubber centre seam, the white stripe carried across the doors, hinges, two
chrome lock bars with guides, keepers and lever handles, three-lens lamp clusters over the old lamps, roof marker
lamps, bumper reflectors, a licence plate and a hanging tread step.
The add-on keeps its own materials (checked in game: the paint matches the truck body); mare_fix_0911.truck_rear
places it and can re-point `Paint`, `Stripe` and `Chrome` to the truck's materials if they ever drift apart.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_truck_rear.py
Output: D:/Assets/Mare/mare_truck_rear/mare_truck_rear.glb."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from gen_custom_furniture import box, export, finish, material, reset, tube  # noqa: E402

SLUG = 'mare_truck_rear'
X0 = -2.6            # rear cap of the truck body
HALF = .74           # half width of the door opening
Z0, Z1 = .78, 2.58   # door opening


def plain(name, color, rough=.4, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m


def plate_text(body, mat, z, size):
    """Text as mesh on the plane x = const facing -X (read from behind the truck: right is -Y, up is +Z)."""
    cu = bpy.data.curves.new('plate_txt', 'FONT')
    cu.body = body
    cu.size = size
    cu.extrude = .0012
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.space_character = 1.15
    src = bpy.data.objects.new('plate_txt_src', cu)
    bpy.context.collection.objects.link(src)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(src.evaluated_get(dg))
    bpy.data.objects.remove(src)
    for v in me.vertices:
        u, w, d = v.co.x, v.co.y, v.co.z
        v.co = (-2.7575 - d, -u, z + w)
    ob = bpy.data.objects.new('plate_txt', me)
    bpy.context.collection.objects.link(ob)
    return finish(ob, mat, .2, smooth=False)


def main():
    reset()
    out = Path('D:/Assets/Mare') / SLUG
    out.mkdir(parents=True, exist_ok=True)
    paint = plain('Paint', (.78, .16, .1), .38)
    stripe = plain('Stripe', (.92, .9, .86), .4)
    chrome = plain('Chrome', (.8, .81, .82), .2, .9)   # plain: the metal_plate texture is a tread pattern
    tread = material('Tread', 'metal_plate', (.5, .51, .52), rough=.5, out=out)
    rubber = plain('Rubber', (.03, .03, .03), .8)
    housing = plain('Housing', (.05, .05, .055), .45)
    red = plain('LensRed', (.62, .02, .02), .12)
    amber = plain('LensAmber', (.85, .38, .03), .12)
    clear = plain('LensClear', (.86, .87, .88), .1)
    plate = plain('Plate', (.9, .9, .9), .35)
    blue = plain('PlateBlue', (.03, .12, .5), .35)
    ink = plain('PlateInk', (.02, .02, .02), .5)

    # ---- frame around the opening, 3.5 cm proud of the cap, and a chrome sill
    fx = X0 - .0125
    for s in (-1, 1):
        box(f'frame_side{s}', (.045, .05, Z1 - Z0 + .1), (fx, s * (HALF + .025), (Z0 + Z1) / 2), paint, bevel=.008)
    box('frame_top', (.045, 2 * HALF + .1, .05), (fx, 0, Z1 + .025), paint, bevel=.008)
    box('sill', (.06, 2 * HALF + .1, .05), (fx - .008, 0, Z0 - .025), chrome, bevel=.006, uv=.4)
    # drip rail over the doors
    box('drip', (.05, 2 * HALF + .16, .018), (X0 - .03, 0, Z1 + .062), chrome, rot=(0, .25, 0), bevel=.004, uv=.4)

    # ---- two leaves: plate, raised stiles and rails (recessed panels between them), stripe, hinges
    lw = HALF - .008                  # leaf width
    lh = Z1 - Z0 - .006
    zc = (Z0 + Z1) / 2
    px = X0 - .015                    # plate centre (5 cm thick: -2.59 .. -2.64)
    rx = X0 - .046                    # rails centre (1.2 cm proud)
    for s in (-1, 1):
        yc = s * (.006 + lw / 2)
        box(f'leaf{s}', (.05, lw, lh), (px, yc, zc), paint, bevel=.006)
        for k, y in enumerate((s * (.006 + .035), s * (.006 + lw - .035))):
            box(f'stile{s}{k}', (.012, .07, lh), (rx, y, zc), paint, bevel=.004)
        for k, (z, h) in enumerate(((Z1 - .04, .07), (1.76, .08), (1.125, .07), (Z0 + .04, .07))):
            box(f'rail{s}{k}', (.012, lw - .14, h), (rx, yc, z), paint, bevel=.004)
        # the truck's white stripe (z 0.91 .. 1.09) carried across the leaf
        box(f'stripe{s}', (.006, lw - .14, .18), (X0 - .042, yc, 1.0), stripe, bevel=.002)
        # pressed ribs inside each panel: reads as sheet metal instead of a flat board
        for k, (za, zb) in enumerate(((1.20, 1.70), (1.84, 2.48))):
            for j in range(3):
                z = za + (zb - za) * (j + .5) / 3
                box(f'rib{s}{k}{j}', (.008, lw - .24, .035), (X0 - .04, yc, z), paint, bevel=.008)
        # hinges on the outer edge: knuckle on the frame, strap on the leaf
        for z in (.98, 1.68, 2.40):
            y = s * (HALF + .002)
            tube(f'hinge{s}{z}', (X0 - .05, y, z - .06), (X0 - .05, y, z + .06), .013, chrome, 12)
            box(f'strap{s}{z}', (.006, .11, .05), (X0 - .055, s * (HALF - .05), z), chrome, bevel=.003, uv=.4)
        # lock bar with guides, keepers on the frame and the lever handle
        by = s * .30
        bx = X0 - .068
        tube(f'bar{s}', (bx, by, Z0 - .035), (bx, by, Z1 + .035), .013, chrome, 14)
        for z in (.86, 1.50, 2.12, 2.50):
            box(f'guide{s}{z}', (.034, .06, .04), (X0 - .062, by, z), chrome, bevel=.006, uv=.4)
        for z in (Z0 - .03, Z1 + .03):
            box(f'keeper{s}{z}', (.05, .085, .045), (X0 - .055, by, z), chrome, bevel=.008, uv=.4)
        hz = 1.32
        tube(f'hub{s}', (bx, by, hz - .03), (bx, by, hz + .03), .02, chrome, 14)
        tube(f'lever{s}', (bx - .012, by, hz), (bx - .012, by + s * .27, hz), .009, chrome, 12)
        box(f'grip{s}', (.02, .1, .028), (bx - .014, by + s * .25, hz), rubber, bevel=.008)
        box(f'catch{s}', (.03, .04, .075), (X0 - .058, by + s * .31, hz), chrome, bevel=.006, uv=.4)
    box('seam', (.016, .014, lh), (X0 - .036, 0, zc), rubber, bevel=.004)

    # ---- lamp clusters over the old 12 cm lamps (pillars beside the doors)
    for s in (-1, 1):
        y = s * .905
        box(f'cluster{s}', (.1, .16, .62), (X0 - .04, y, 1.1), housing, bevel=.02)
        box(f'bezel{s}', (.012, .135, .59), (X0 - .09, y, 1.1), chrome, bevel=.004, uv=.4)
        for k, (z, mat) in enumerate(((1.29, red), (1.10, amber), (.91, clear))):
            box(f'lens{s}{k}', (.022, .115, .165), (X0 - .096, y, z), mat, bevel=.01, subsurf=2, cuts=1)
        # reflector on the bumper end
        box(f'reflector{s}', (.008, .11, .045), (-2.756, s * .86, .6), red, bevel=.004)
    # roof marker lamps
    for y in (-.24, 0, .24):
        box(f'marker_base{y}', (.02, .11, .05), (X0 - .008, y, 2.685), housing, bevel=.008)
        box(f'marker{y}', (.02, .09, .034), (X0 - .02, y, 2.685), red, bevel=.008, subsurf=2, cuts=1)

    # ---- licence plate on the bumper (Mercosul layout: blue band on top)
    box('plate', (.006, .4, .13), (-2.754, 0, .6), plate, bevel=.003)
    box('plate_band', (.007, .4, .03), (-2.7545, 0, .65), blue, bevel=.002)
    plate_text('MAR3A17', ink, .583, .062)
    tube('plate_lamp', (-2.765, -.06, .69), (-2.765, .06, .69), .011, housing, 10)

    # ---- hanging tread step under the bumper
    box('step', (.24, .8, .025), (-2.83, 0, .36), tread, bevel=.006, uv=.35)
    box('step_lip', (.02, .8, .05), (-2.945, 0, .355), tread, bevel=.006, uv=.35)
    for s in (-1, 1):
        tube(f'hanger{s}', (-2.74, s * .34, .56), (-2.76, s * .34, .37), .012, chrome, 10)
        tube(f'brace{s}', (-2.74, s * .34, .52), (-2.92, s * .34, .37), .009, chrome, 10)
    export(SLUG, 'Food truck rear: doors, lock bars, lamp clusters, plate and step')


if __name__ == '__main__':
    main()
