"""Slatted oak wall panel for the Grand Hotel lobby (09/11 visual checklist: "Saguão, lado oeste: três 'portas' que são
só placas marrons na parede, sem batente nem maçaneta"). The west wall of the lobby (Godot hotel_tower mesh) carries
three flat brown slabs, 0.83 x 2.07 m, raised 0.6 m off the floor: too high for doors, so each one gets a slatted panel
over it (painel ripado, common in Brazilian hotel lobbies): a dark backing board, an oak frame and 11 vertical oak slats
with shadow gaps between them.
Built facing -Y in Blender (UE +Y), base at z = 0, back at y = 0; mare_fix_0911.lobby_panels places three of them.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_lobby_slat_panel.py
Output: D:/Assets/Mare/mare_lobby_slat_panel/mare_lobby_slat_panel.glb."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402,F401
from gen_custom_furniture import box, export, material, reset  # noqa: E402

SLUG = 'mare_lobby_slat_panel'
W, H = .90, 2.13            # a little larger than the 0.83 x 2.07 m slab it covers
FRAME = .045
SLATS = 11


def main():
    reset()
    out = Path('D:/Assets/Mare') / SLUG
    out.mkdir(parents=True, exist_ok=True)
    oak = material('Oak', 'oak_wood_planks', (.62, .43, .26), rough=.55, out=out)
    dark = material('Backing', 'oak_wood_planks', (.16, .11, .07), rough=.7, out=out)
    # backing board, 1.5 cm, against the wall
    box('backing', (W, .015, H), (0, -.0075, H / 2), dark, bevel=.003, uv=.6)
    # frame, 3.5 cm deep
    d = .035
    box('frame_top', (W, d, FRAME), (0, -d / 2, H - FRAME / 2), oak, bevel=.005, uv=.6)
    box('frame_bottom', (W, d, FRAME), (0, -d / 2, FRAME / 2), oak, bevel=.005, uv=.6)
    for s in (-1, 1):
        box(f'frame_side{s}', (FRAME, d, H - 2 * FRAME), (s * (W - FRAME) / 2, -d / 2, H / 2), oak, bevel=.005, uv=.6)
    # slats, 4 cm wide, 2.5 cm proud of the backing, evenly spread inside the frame
    inner = W - 2 * FRAME
    sw = .04
    gap = (inner - SLATS * sw) / (SLATS + 1)
    for i in range(SLATS):
        x = -inner / 2 + gap + sw / 2 + i * (sw + gap)
        box(f'slat{i}', (sw, .025, H - 2 * FRAME - .01), (x, -.015 - .0125, H / 2), oak, bevel=.004, uv=.6)
    export(SLUG, 'Slatted oak wall panel (hotel lobby)')


if __name__ == '__main__':
    main()
