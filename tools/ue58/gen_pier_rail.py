"""Guard rail at the pier's end (11/11, open item "gesto de apoiar no corrimão"): the pier only has rope rails 78 cm
tall, too low for the leaning clip (wrists at 92-95 cm). A 2.4 m stretch of weathered timber rail on the sea side of
the end platform: three 9 cm posts, a 12 x 4 cm top rail whose top is 93 cm above the deck, a mid rail, and the posts
going 25 cm down through the boards. Length along X, origin on the deck under the middle of the rail.
  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_pier_rail.py
Output: D:/Assets/Mare/mare_pier_rail/mare_pier_rail.glb."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from gen_custom_furniture import OUT, box, export, material, reset  # noqa: E402

SLUG = 'mare_pier_rail'


def main():
    reset()
    out = OUT / SLUG
    out.mkdir(parents=True, exist_ok=True)
    wood = material('Wood', 'oak_wood_planks', (.34, .26, .19), rough=.9, out=out)
    for i, x in enumerate((-1.15, 0, 1.15)):
        box(f'post{i}', (.09, .09, 1.14), (x, 0, .32), wood, bevel=.008, uv=.8)
        box(f'cap{i}', (.11, .11, .025), (x, 0, .90), wood, bevel=.006, uv=.8)
    box('top', (2.5, .12, .04), (0, 0, .91), wood, bevel=.012, uv=.8)
    box('mid', (2.4, .035, .09), (0, 0, .48), wood, bevel=.006, uv=.8)
    export(SLUG, 'Guarda-corpo da ponta do píer (bpy)')


if __name__ == '__main__':
    main()
