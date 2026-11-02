"""Grand Hotel suite on the tower's 3rd floor (inside the hollow storey above the lobby), modelled with bpy.

Local frame = UE world axes (Blender y = -UE y); origin on the floor slab at the centre of the suite area,
which the level places at UE (-2800, 6342, 851). Suite: 17 x 11.5 m, 3.08 m ceiling (the tower's own).
South (UE -Y) is the facade: tall windows with sheer curtains in front of a daylight panel ('DaylightPanel'
material is replaced in UE by a night-aware glow). North (UE +Y): elevator door. West: bedroom with a slatted
feature wall (the bed itself is a customization tier). East: bathroom behind glass.
Run: blender -b --factory-startup --python tools/ue58/gen_suite.py
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from gen_custom_furniture import OUT, box, cushion, drape, export, lathe, material, mesh_obj, reset, tube  # noqa: E402

ART = Path('D:/Assets/Canva/beach_art/beach_watercolor.png')
HW, HD, H = 8.5, 5.77, 3.08   # half width (x), half depth (y), ceiling height


def B(x, y, z=0.0):
    """UE local cm-free metres (x, y up-is-north) -> Blender coordinates (y flipped)."""
    return (x, -y, z)


def suite():
    reset()
    slug = 'mare_suite'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    plaster = material('Plaster', 'painted_plaster_wall', (.95, .93, .88), rough=.85, out=out)
    floor = material('Floor', 'teak_veneer', None, rough=.35)
    tiles = material('BathFloor', 'blue_floor_tiles_01', None, rough=.3)
    teak = material('Teak', 'oak_wood_planks', (.55, .38, .24), rough=.45, out=out)
    stone = material('Stone', 'plaster_stone_wall_01', (.86, .84, .80), rough=.5, out=out)
    metal = material('Steel', 'metal_plate', (.62, .63, .64), rough=.3, out=out)
    sheer = material('Sheer', 'rough_linen', (.97, .96, .92), rough=.9, out=out)
    drapes = material('Drapes', 'velour_velvet', (.20, .32, .36), rough=.8, out=out)
    towel = material('Towel', 'waffle_pique_cotton', (.97, .97, .95), rough=.95, out=out)
    glass = bpy.data.materials.new('Glass')
    glass.use_nodes = True
    g = glass.node_tree.nodes['Principled BSDF']
    g.inputs['Base Color'].default_value = (.85, .92, .95, 1)
    g.inputs['Roughness'].default_value = .03
    g.inputs['Alpha'].default_value = .18
    daylight = bpy.data.materials.new('DaylightPanel')
    daylight.use_nodes = True
    d = daylight.node_tree.nodes['Principled BSDF']
    d.inputs['Base Color'].default_value = (.82, .90, .96, 1)
    d.inputs['Emission Color'].default_value = (.82, .90, .96, 1)
    d.inputs['Emission Strength'].default_value = 2.0

    # Floors: teak in living/bedroom, tiles in the bathroom (east block x 3..8.5, y 0..5.77).
    box('floor', (2 * HW, 2 * HD, .03), B(0, 0, .015), floor, uv=1.4)
    box('bathfloor', (5.5, HD, .032), B(5.75, HD / 2, .016), tiles, uv=.8)
    # Partition walls closing the suite inside the open storey, inner skin on facade/north walls.
    for sx in (-1, 1):
        box(f'part{sx}', (.15, 2 * HD, H), B(sx * HW, 0, H / 2), plaster, uv=1.5)
    box('north', (2 * HW, .12, H), B(0, HD - .06, H / 2), plaster, uv=1.5)
    # Bathroom: glass wall with door gap along y=0 and x=3, vanity, mirror, freestanding tub, shower.
    box('bathwall', (.12, HD, H), B(3.0, HD / 2, H / 2), plaster, uv=1.5)
    box('bathfront_a', (1.6, .1, H), B(3.8, 0, H / 2), plaster, uv=1.5)
    box('bathglass', (3.2, .03, 2.4), B(6.9, 0, 1.2), glass, uv=1)
    box('bathglassframe', (3.2, .06, .06), B(6.9, 0, 2.43), metal, uv=1)
    box('vanity', (2.2, .6, .85), B(5.2, HD - .4, .425), teak, uv=.9)
    box('vanitytop', (2.3, .66, .05), B(5.2, HD - .4, .875), stone, uv=.8)
    for x in (4.65, 5.75):
        lathe(f'basin{x}', [(0, 0), (.2, 0), (.22, .03), (.2, .14), (.17, .15), (.03, .02), (0, .02)], B(x, HD - .4, .9), stone, 28)
        tube(f'tap{x}', B(x, HD - .15, .9), B(x, HD - .15, 1.15), .015, metal, 8)
        tube(f'spout{x}', B(x, HD - .15, 1.15), B(x, HD - .3, 1.15), .012, metal, 8)
    box('mirror', (2.0, .03, 1.1), B(5.2, HD - .13, 1.65), glass, uv=1)
    box('mirrorframe', (2.08, .04, 1.18), B(5.2, HD - .11, 1.65), teak, uv=.8)
    tub = [(0, .02), (.75, .02), (.8, .15), (.82, .5), (.8, .55), (.74, .56), (.68, .14), (0, .1)]
    lathe('tub', tub, B(0, 0, 0), stone, 40)
    t = bpy.context.collection.objects['tub']
    t.scale = (1.0, .55, 1.0)
    t.location = B(7.3, 3.2, 0)
    tube('tubtap', B(7.3, 3.2 + .7, 0), B(7.3, 3.2 + .7, 1.0), .02, metal, 8)
    box('showertray', (1.3, 1.3, .05), B(7.75, 1.0, .025), stone, uv=.6)
    box('showerglassA', (.02, 1.3, 2.1), B(7.1, 1.0, 1.1), glass, uv=1)
    lathe('showerhead', [(0, 0), (.15, 0), (.15, .02), (0, .02)], B(7.75, 1.0, 2.2), metal, 24)
    tube('showerpipe', B(8.4, 1.0, 1.0), B(8.4, 1.0, 2.25), .015, metal, 8)
    tube('showerarm', B(8.4, 1.0, 2.25), B(7.75, 1.0, 2.25), .015, metal, 8)
    for i in range(3):
        cushion(f'towel{i}', (.4, .28, .06), B(3.6, HD - .4, 1.05 + i * .07), towel, puff=.01)
    tube('towelbar', B(8.45, 4.0, 1.2), B(8.45, 5.0, 1.2), .015, metal, 8)
    cushion('hangtowel', (.04, .9, .55), B(8.42, 4.5, .95), towel, puff=.006)
    # Elevator door on the north wall (UE x = 0 -> world -2800), frame and call panel.
    box('elevdoor', (1.5, .06, 2.45), B(0, HD - .14, 1.225), metal, uv=.6)
    box('elevseam', (.03, .07, 2.3), B(0, HD - .17, 1.16), plaster, uv=.6)
    for sx in (-1, 1):
        box(f'elevjamb{sx}', (.14, .14, 2.6), B(sx * .82, HD - .14, 1.3), metal, uv=.6)
    box('elevhead', (1.78, .14, .16), B(0, HD - .14, 2.53), metal, uv=.6)
    box('elevpanel', (.12, .05, .3), B(1.05, HD - .15, 1.2), metal, uv=.4)
    # Bedroom feature wall: vertical teak slats on the west partition behind the bed.
    for k in range(26):
        y = -3.2 + k * .2
        box(f'slat{k}', (.08, .1, H - .3), B(-HW + .12, y, (H - .3) / 2 + .05), teak, uv=.8)
    if ART.exists():
        art = bpy.data.materials.new('Painting')
        art.use_nodes = True
        node = art.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(ART))
        art.node_tree.links.new(node.outputs['Color'], art.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        box('artframe', (1.6, .05, 1.08), B(-2.0, HD - .17, 1.75), teak, uv=.6)
        bm = bmesh.new()
        v = [bm.verts.new(p) for p in [(-.75, 0, -.5), (.75, 0, -.5), (.75, 0, .5), (-.75, 0, .5)]]
        f = bm.faces.new(v)
        uv = bm.loops.layers.uv.verify()
        for loop, co in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            loop[uv].uv = co
        canvas = mesh_obj('canvas', bm)
        canvas.data.materials.append(art)
        canvas.location = B(-2.0, HD - .2, 1.75)
        canvas.rotation_euler = (0, 0, math.pi)
    # Facade: four tall windows with frames, sheer curtains and velvet side drapes before a daylight panel.
    for k, x in enumerate((-6.6, -3.2, .2, 2.0)):
        w = 2.2 if k < 3 else 1.4
        box(f'day{k}', (w, .02, 2.3), B(x, -HD + .04, 1.35), plaster, uv=1).data.materials[0] = daylight
        box(f'wframe{k}', (w + .16, .1, .1), B(x, -HD + .08, 2.55), teak, uv=.6)
        box(f'wsill{k}', (w + .2, .2, .06), B(x, -HD + .12, .17), teak, uv=.6)
        for sx in (-1, 1):
            box(f'wjamb{k}{sx}', (.08, .1, 2.42), B(x + sx * (w / 2 + .04), -HD + .08, 1.38), teak, uv=.6)
        for m in range(1, 3):
            box(f'mullion{k}{m}', (.04, .06, 2.3), B(x - w / 2 + m * w / 3, -HD + .07, 1.35), teak, uv=.6)
        tube(f'rod{k}', B(x - w / 2 - .45, -HD + .3, 2.75), B(x + w / 2 + .45, -HD + .3, 2.75), .015, metal, 8)
        drape(f'sheer{k}', w * .95, 2.6, B(x, -HD + .26, 2.72), 0, sheer, folds=int(w * 5), amp=.03)
        for sx in (-1, 1):
            drape(f'drape{k}{sx}', .5, 2.62, B(x + sx * (w / 2 + .2), -HD + .34, 2.72), 0, drapes, folds=4, amp=.05)
    # Built-in wardrobe in the foyer (north-west), TV wall in the living area, ceiling cove.
    box('wardrobe', (2.4, .62, 2.6), B(-4.2, HD - .45, 1.3), teak, uv=.8)
    for k in range(4):
        box(f'wseam{k}', (.012, .63, 2.5), B(-5.4 + .6 * (k + 1) - .0, HD - .45, 1.3), metal, uv=.4)
    box('tvwall', (3.4, .12, 2.2), B(-.5, -1.2, 1.1), stone, uv=.9)
    box('tvconsole', (2.6, .45, .45), B(-.5, -.95, .3), teak, uv=.8)
    box('tv', (1.65, .05, .95), B(-.5, -1.12, 1.5), metal, uv=.4)
    box('tvscreen', (1.58, .01, .88), B(-.5, -1.09, 1.5), glass, uv=.4)
    box('cove', (2 * HW - .3, 2 * HD - .3, .06), B(0, 0, H - .05), plaster, uv=1.5)
    export(slug, 'Suíte do Grand Hotel')


if __name__ == '__main__':
    suite()
    print('built mare_suite')
