"""Board and kayak rental props (CHECKLIST_EXPANSOES 3.3). No free sit-on-top kayak with a commercial licence and real
detail was found (the rack model has them merged in), so:
  Rental_kayak   3.1 m sit-on-top kayak: lofted hull with keel and pointed bow/stern, recessed seat and foot wells,
                 carry handles, a deck bungee, and a double paddle lying across; orange plastic, black fittings.
Metres, Blender Z up, waterline near z=0.12, bow toward +Y (arrives as UE -Y), origin at the stern.
Output D:/CodexTemp/rental/<name>.glb.
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_rental.py"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import gen_bar_prep as G  # noqa: E402

G.OUT = 'D:/CodexTemp/rental'
os.makedirs(G.OUT, exist_ok=True)
mat, obj, place, finish, reset = G.mat, G.obj, G.place, G.finish, G.reset
TAU = 2 * math.pi


def kayak():
    reset()
    P = 'Rental_kayak'
    L = 3.1
    m = mat(f'{P}_Hull', None, (0.95, 0.42, 0.08), 0.35)
    m_dark = mat(f'{P}_Fit', None, (0.05, 0.05, 0.06), 0.5)
    m_seat = mat(f'{P}_Seat', None, (0.18, 0.2, 0.24), 0.6)
    n_sec, n_ring = 40, 28
    bm = bmesh.new()
    rings = []
    for i in range(n_sec + 1):
        t = i / n_sec
        w = 0.40 * math.sin(math.pi * t) ** 0.55          # half beam
        d = 0.17 * math.sin(math.pi * t) ** 0.45          # depth under the deck line
        rise = 0.10 * (abs(t - 0.5) * 2) ** 3             # rocker: ends lift
        ring = []
        for k in range(n_ring):
            a = TAU * k / n_ring
            c, s = math.cos(a), math.sin(a)
            if s >= 0:   # deck, slightly domed
                z = 0.30 + rise + 0.05 * s * math.sin(math.pi * t)
                x = w * c
            else:        # hull, V near the keel
                z = 0.30 + rise - d * (abs(s) ** 0.8)
                x = w * c * (1 - 0.15 * abs(s))
            ring.append(bm.verts.new((max(x, -0.6) if w > 0.004 else 0, t * L, z)))
        rings.append(ring)
    for i in range(n_sec):
        for k in range(n_ring):
            k2 = (k + 1) % n_ring
            bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    hull = obj(bm, 'hull', m)
    hull.modifiers.new('sub', 'SUBSURF').levels = 1
    # Seat recess and foot well (dark inset pads on the deck).
    for y, sx, sy in ((1.28, 0.26, 0.36), (1.85, 0.2, 0.32)):
        G.rbox((sx * 2, sy * 2, 0.025), (0, y, 0.345), m_seat, bevel=0.02, name='well')
    G.rbox((0.34, 0.08, 0.16), (0, 1.0, 0.42), m_seat, bevel=0.03, name='backrest')
    # Carry handles at bow and stern, deck bungee.
    for y in (0.12, L - 0.12):
        G.tube_handle = None
        h = G.lathe([(0, 0), (0.025, 0), (0.025, 0.12), (0, 0.12)], m_dark, 12, 'handle')
        place(h, (0, y, 0.38), (math.pi / 2, 0, 0))
    for k in range(4):
        G.rbox((0.012, 0.5, 0.012), (-0.18 + k * 0.12, 2.45, 0.365), m_dark, bevel=0.003, name='bungee')
    # Double paddle across the deck.
    shaft = G.lathe([(0, 0), (0.016, 0), (0.016, 2.1), (0, 2.1)], m_dark, 14, 'shaft')
    place(shaft, (-1.05, 1.62, 0.39), (0, math.pi / 2, 0))
    for sx in (-1, 1):
        blade = G.rbox((0.42, 0.17, 0.012), (sx * 1.18, 1.62, 0.39), m, bevel=0.03, name='blade')
    finish(P, keep_base=False)


ALL = {'kayak': kayak}
if __name__ == '__main__':
    for n in sys.argv[1:] or list(ALL):
        ALL[n]()
    print('gen_rental ok')
