"""Grand Hotel guest-room door that opens (08/11, reference tip 11 / C16: room service is handed over at the door and
the guest opens it). The standard and luxury rooms had their leaves modelled open and fixed in the floor mesh
(gen_hotel_rooms.py); now each is this leaf on its own, hinged, swung by AMareServiceTarget (Action "RoomDoor").
Teak leaf 0.90 x 2.13 m, 4.5 cm thick, two raised panels each side, brass lever handles both faces at 1.02 m, three
brass hinges. Pivot = hinge edge at the floor; the closed leaf runs along -X (the UE door convention of
AMareServiceTarget: FocusOffset (-w/2, 0, 1.1 m)).
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_hotel_door.py
Output: D:/Assets/Mare/mare_hotel_door/mare_hotel_door.glb."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from gen_custom_furniture import box, export, material, reset, tube  # noqa: E402

SLUG = 'mare_hotel_door'
W, H, T = .90, 2.13, .045


def main():
    reset()
    out = Path('D:/Assets/Mare') / SLUG
    out.mkdir(parents=True, exist_ok=True)
    teak = material('Teak', 'oak_wood_planks', (.55, .38, .24), rough=.45, out=out)
    panel = material('Panel', 'oak_wood_planks', (.47, .32, .2), rough=.5, out=out)
    brass = material('Brass', 'metal_plate', (.78, .62, .34), rough=.25, out=out)
    cx = -W / 2
    box('leaf', (W - .004, T, H), (cx, 0, H / 2), teak, bevel=.004, uv=.7)
    # two raised panels on each face (upper and lower), with a moulding step
    for side in (-1, 1):
        y = side * (T / 2 + .006)
        for zc, ph in ((1.52, .95), (.52, .72)):
            box(f'panel{side}{zc}', (W - .26, .012, ph), (cx, y, zc), panel, bevel=.003, uv=.7)
            box(f'mould{side}{zc}', (W - .2, .006, ph + .06), (cx, side * (T / 2 + .002), zc), teak, bevel=.002, uv=.7)
    # lever handles near the free edge (x = -W + 0.08), both faces, with rose plates and the lock
    fx = -W + .08
    for side in (-1, 1):
        y0 = side * (T / 2)
        tube(f'rose{side}', (fx, y0, 1.02), (fx, y0 + side * .012, 1.02), .028, brass, 20)
        tube(f'neck{side}', (fx, y0 + side * .012, 1.02), (fx, y0 + side * .055, 1.02), .009, brass, 12)
        tube(f'lever{side}', (fx, y0 + side * .055, 1.02), (fx + .12, y0 + side * .055, 1.02), .01, brass, 12)
        tube(f'lock{side}', (fx, y0, .9), (fx, y0 + side * .008, .9), .016, brass, 16)
    # hinges on the pivot edge
    for z in (.25, 1.07, 1.88):
        tube(f'hinge{z}', (.004, 0, z - .06), (.004, 0, z + .06), .011, brass, 12)
    export(SLUG, 'Hotel guest-room door leaf')


if __name__ == '__main__':
    main()
