"""Rope-rail post of the pier (11/11, Sergio: "está sem base as cordas"): each pier_segment carries one post per side
and two ropes that run 3 m to the NEXT segment's post; the last segment meets the end platform, which has no post
there, so its four rope ends hung in the air. This is that missing post: same size as the segment's (82 cm above the
deck, 5.5 cm radius, the wider cap), brown bark (Poly Haven bark_brown_02, CC0), with the two ropes tied round it (three turns each at 68 and 33 cm, where
the ropes arrive). Origin on the deck top; the shaft goes 30 cm below it (through the boards).
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_pier_post.py
Output: D:/Assets/Mare/mare_pier_post/mare_pier_post.glb."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from gen_custom_furniture import export, lathe, material, reset  # noqa: E402

SLUG = 'mare_pier_post'
OUT = Path('D:/Assets/Mare') / SLUG


def main():
    reset()
    OUT.mkdir(parents=True, exist_ok=True)
    bark = material('bark', 'bark_brown_02', tint=(.4, .29, .2), rough=.9, out=OUT)
    rope = bpy.data.materials.new('rope')
    rope.use_nodes = True
    p = rope.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (.66, .52, .32, 1)
    p.inputs['Roughness'].default_value = .95
    # shaft: slightly tapered, a worn shoulder and a domed cap like the segment's posts
    lathe('shaft', [(.0, -.30), (.058, -.30), (.056, .0), (.052, .40), (.05, .68), (.056, .73), (.066, .775), (.064, .80), (.045, .822), (.0, .83)],
          (0, 0, 0), bark, sides=20, uv=.8)
    # the ropes tied round the post: three turns each, where the upper and the lower rope arrive
    for z0 in (.68, .33):
        for k in (-1, 0, 1):
            z = z0 + k * .03
            r = .052 + (.001 if z0 < .5 else 0)
            lathe(f'turn_{int(z0 * 100)}_{k + 1}', [(r - .002, z - .015), (r + .011, z - .011), (r + .016, z), (r + .011, z + .011), (r - .002, z + .015)],
                  (0, 0, 0), rope, sides=20, uv=.4)
    for o in bpy.context.scene.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['shaft']
    bpy.ops.object.join()
    bpy.context.active_object.name = SLUG
    export(SLUG, 'Pier rope-rail post (bpy)')


if __name__ == '__main__':
    main()
