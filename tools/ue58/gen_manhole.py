"""Cast-iron manhole cover for the village pavements (09/11 visual checklist: "Tampas de bueiro redondas e lisas no
calçamento"). Replaces the Godot plain cylinder (World_2263, r 0.32 m, 2 cm thick, centred pivot) on the 24 instances
of the 'Maré · Bueiro' ISM: a recessed frame ring, the lid with a cast tread pattern (Poly Haven metal_plate, CC0),
a raised outer rim, a raised inner ring, two lift slots and a centre boss. Same footprint and pivot (centre, the lid
top 1 cm above it, so it keeps sitting flush where the cylinder did).
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_manhole.py
Output: D:/Assets/Mare/mare_manhole/mare_manhole.glb (applied by mare_fix_0911.manholes)."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from gen_custom_furniture import box, export, lathe, material, reset  # noqa: E402

SLUG = 'mare_manhole'
R = .32


def main():
    reset()
    out = Path('D:/Assets/Mare') / SLUG
    out.mkdir(parents=True, exist_ok=True)
    iron = material('Iron', 'metal_plate', (.22, .22, .23), rough=.55, out=out)
    rim = material('Rim', 'metal_plate', (.30, .29, .28), rough=.45, out=out)
    dark = material('Slot', 'metal_plate', (.04, .04, .04), rough=.9, out=out)
    # frame ring: outer edge flush with the pavement, slightly above the lid at the very rim
    lathe('frame', [(R - .035, -.01), (R, -.01), (R, .012), (R - .035, .012)], (0, 0, 0), rim, sides=48)
    # lid disc with the tread texture
    lathe('lid', [(0, -.01), (R - .036, -.01), (R - .036, .008), (0, .008)], (0, 0, 0), iron, sides=48)
    # raised rings (cast ribs) and centre boss
    for r0, r1 in ((R - .07, R - .055), (.12, .135)):
        lathe(f'rib{r0:.2f}', [(r0, .008), (r1, .008), (r1, .014), (r0, .014)], (0, 0, 0), rim, sides=48)
    lathe('boss', [(0, .008), (.04, .008), (.035, .016), (0, .016)], (0, 0, 0), rim, sides=24)
    # radial ribs between the rings
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        rr = (.135 + R - .07) / 2
        box(f'spoke{k}', (R - .07 - .135, .014, .006), (math.cos(a) * rr, math.sin(a) * rr, .011), rim, rot=(0, 0, a), bevel=.002, uv=.3)
    # two lift slots
    for s in (-1, 1):
        box(f'slot{s}', (.06, .016, .004), (s * (R - .1), 0, .0085), dark, bevel=.004, uv=.3)
    export(SLUG, 'Cast-iron manhole cover')


if __name__ == '__main__':
    main()
