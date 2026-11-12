"""Beach walkway board to the kiosk (replaces the Godot export World_1274: a plain dark rounded box 160 x 40 x 6 cm).
Three weathered planks with gaps, slightly uneven, nailed on two battens; oak planks scan (Poly Haven, CC0) tinted
to sun-bleached wood. Built in the old mesh's frame: length along Blender X (UE X), centred, base at z=0.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_beach_walkway.py
Output: D:/Assets/Mare/beach_walk_board/beach_walk_board.glb."""
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from gen_custom_furniture import box, export, lathe, material, reset  # noqa: E402

LENGTH, WIDTH, HEIGHT = 1.60, .40, .06


def board():
    reset()
    rnd = random.Random(7)
    wood = material('planks', 'oak_wood_planks', tint=(.66, .58, .47), rough=.85, out=Path('D:/Assets/Mare/beach_walk_board'))
    batten = material('battens', 'oak_wood_planks', tint=(.48, .40, .31), rough=.9, out=Path('D:/Assets/Mare/beach_walk_board'))
    iron = bpy.data.materials.new('nails')
    iron.use_nodes = True
    p = iron.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (.22, .2, .18, 1)
    p.inputs['Roughness'].default_value = .55
    p.inputs['Metallic'].default_value = .6
    # two battens under the planks, near the ends
    for x in (-.62, .62):
        box(f'batten{x}', (.07, WIDTH - .02, .025), (x, 0, .0125), batten, bevel=.004, uv=1.5)
    plank_w, gap = .124, .014
    for k in range(3):
        y = (k - 1) * (plank_w + gap)
        length = LENGTH - rnd.uniform(0, .03)
        box(f'plank{k}', (length, plank_w, .034), (rnd.uniform(-.01, .01), y, .025 + .017 + rnd.uniform(-.002, .002)), wood,
            rot=(rnd.uniform(-.006, .006), rnd.uniform(-.004, .004), rnd.uniform(-.006, .006)), bevel=.005, uv=2.0)
        for x in (-.62, .62):
            for dy in (-.035, .035):
                lathe(f'nail{k}{x}{dy}', [(.0005, 0), (.0055, 0), (.0055, .002), (.004, .003), (.0005, .0032)],
                      (x + rnd.uniform(-.006, .006), y + dy, .059), iron, sides=12)
    # one mesh: the importer expects a single static mesh per file
    for o in bpy.context.scene.objects:
        o.select_set(True)
        for mod in list(o.modifiers):
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.view_layer.objects.active = bpy.data.objects['plank0']
    bpy.ops.object.join()
    bpy.context.active_object.name = 'beach_walk_board'
    export('beach_walk_board', 'Beach walkway board (bpy)')


if __name__ == '__main__':
    board()
