"""Key rack behind the pousada counter (replaces the Godot export World_0052 board + World_0053 green squares).
A framed varnished board with a small top shelf, two rows of brass hooks and room keys hanging on them, each with a
turned wooden fob. Built in World_0052's frame: centred on the origin; the wall is on Blender +Y, 15 cm behind the
centre, so the board's back sits at y = +0.15 and everything hangs toward -Y (the room).
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_key_rack.py
Output: D:/Assets/Mare/pousada_key_rack/pousada_key_rack.glb."""
import math
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from gen_custom_furniture import box, export, lathe, material, reset, tube  # noqa: E402

OUT = Path('D:/Assets/Mare/pousada_key_rack')
W, H = 1.10, .62                   # board
BACK = .15                         # wall plane (Blender +Y)
COLS, ROWS = 6, 2


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
    rnd = random.Random(5)
    wood = material('board', 'oak_wood_planks', tint=(.52, .34, .2), rough=.45, out=OUT)
    frame = material('frame', 'oak_wood_planks', tint=(.33, .2, .12), rough=.5, out=OUT)
    brass = plain('brass', (.80, .60, .28), .3, .95)
    fob_colours = [(.75, .16, .12), (.12, .42, .55), (.86, .63, .18), (.2, .45, .25)]
    fobs = [plain(f'fob{i}', c, .55) for i, c in enumerate(fob_colours)]
    y0 = BACK - .012                                  # board centre (2.4 cm thick)
    box('board', (W, .024, H), (0, y0, 0), wood, bevel=.004, uv=1.5)
    for name, size, loc in (('top', (W + .06, .045, .04), (0, y0 - .01, H / 2 + .02)),
                            ('bottom', (W + .06, .045, .04), (0, y0 - .01, -H / 2 - .02)),
                            ('left', (.04, .045, H + .08), (-W / 2 - .02, y0 - .01, 0)),
                            ('right', (.04, .045, H + .08), (W / 2 + .02, y0 - .01, 0))):
        box(f'frame_{name}', size, loc, frame, bevel=.006, uv=1.5)
    # little shelf on top for the guest book and the bell (empty: props go on the counter)
    box('shelf', (W + .1, .12, .022), (0, BACK - .06, H / 2 + .055), frame, bevel=.004, uv=1.5)
    front = y0 - .012
    for r in range(ROWS):
        z = H / 2 - .16 - r * .27
        for c in range(COLS):
            x = -W / 2 + .1 + c * (W - .2) / (COLS - 1)
            # hook: round base plate + bent arm
            tube(f'rose{r}{c}', (x, front, z), (x, front - .006, z), .011, brass, sides=16)
            tube(f'arm{r}{c}', (x, front - .005, z), (x, front - .04, z + .004), .0035, brass, sides=10)
            tube(f'tip{r}{c}', (x, front - .04, z + .004), (x, front - .043, z + .018), .0035, brass, sides=10)
            if rnd.random() < .2:                    # a free room: the key is out
                continue
            # key ring + key + wooden fob hanging below the hook
            sway = rnd.uniform(-.02, .02)
            tube(f'ring{r}{c}', (x, front - .036, z - .002), (x + sway * .3, front - .036, z - .03), .0025, brass, sides=8)
            tube(f'key{r}{c}', (x + sway * .3, front - .036, z - .03), (x + sway * .6, front - .036, z - .085), .004, brass, sides=8)
            lathe(f'fob{r}{c}', [(.0005, 0), (.012, -.006), (.016, -.03), (.012, -.06), (.0005, -.066)],
                  (x + sway * .6, front - .036, z - .085), fobs[(r * COLS + c) % len(fobs)], sides=14)
    for o in bpy.context.scene.objects:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        for mod in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.view_layer.objects.active = bpy.data.objects['board']
    bpy.ops.object.join()
    bpy.context.active_object.name = 'pousada_key_rack'
    export('pousada_key_rack', 'Pousada key rack (bpy)')


if __name__ == '__main__':
    main()
