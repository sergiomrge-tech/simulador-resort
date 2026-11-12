"""Island trails (08/11, Sergio: "precisa ter acesso da Vila à floresta", "com 3 trilhas"): besides the summit trail
(village -> old man's house), two new earth trails from the north edge of the village into the forest: West (to the
western plain) and North (to the plain where the dome was). Route = the cheapest path on the 5 m height survey of the
finished island (mare_island.land): only terrain (no houses, props or water), slopes above 40% forbidden, flatter
ground preferred. 08/11 (Sergio: "não deixa tanto reto, precisa ser mais natural, sinuosa"): the cost also follows a
smooth random field (~30 m blobs), so the cheapest route wanders like a path worn by feet, then a gentle meander
(2-4 m either side, 35-70 m waves) is laid over it, and the width changes along the way ('w', factor .75-1.25).
Output Content/Data/island_trails.json: per trail the points every 2 m [x, y, ground z] (UE cm),
read by gen_island_trails.py (the path mesh) and mare_island.forest (kept clear).
  python tools/ue58/plan_island_trails.py [survey.json]"""
import heapq
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2] / 'unreal' / 'MareAlta'
SURVEY = Path(sys.argv[1] if len(sys.argv) > 1 else 'D:/CodexTemp/island/land_after.json')
TRAILS = {
    'oeste': {'name': 'Trilha Oeste', 'start': (2500, 9000), 'goal': (-38000, 42000)},
    'norte': {'name': 'Trilha Norte', 'start': (5500, 9000), 'goal': (5000, 98000)},
}
MAX_SLOPE = .40


def terrain_label(name):
    if 'terreno novo' in name or 'Ground' in name or 'Preenchimento' in name or 'trilha' in name:
        return True
    tail = name.rsplit('@', 1)[-1]
    return '@MeshInstance3D@' in name and tail.isdigit() and 1869 <= int(tail) <= 1938


def main():
    s = json.loads(SURVEY.read_text(encoding='utf-8'))
    x0, x1, y0, y1, step = [float(v) for v in s['arg'].split(',')]
    z = np.array([[np.nan if v is None else v for v in row] for row in s['z']], np.float64)
    who = np.array(s['who'])
    ok_ids = [k for k, n in enumerate(s['labels']) if terrain_label(n)]
    ok = np.isin(who, ok_ids) & (z > 20)
    ok = ndimage.binary_erosion(ok, iterations=1)          # keep a cell's width away from walls and water
    h, w = z.shape
    rng = np.random.default_rng(20261108)
    field = ndimage.gaussian_filter(rng.standard_normal((h, w)), 6.0)
    field = (field - field.min()) / (np.ptp(field) or 1)          # 0..1, ~30 m blobs
    apart = np.ones((h, w))                  # each trail keeps its own way: 60 m from the ones already laid cost x4
    out = {'_doc': __doc__.split('\n\n')[0], 'trails': {}}

    def cell(x, y):
        i, j = int(round((x - x0) / step)), int(round((y - y0) / step))
        # nearest usable cell
        best, bd = None, 1e18
        for dj in range(-12, 13):
            for di in range(-12, 13):
                a, b = j + dj, i + di
                if 0 <= a < h and 0 <= b < w and ok[a, b] and di * di + dj * dj < bd:
                    best, bd = (a, b), di * di + dj * dj
        return best

    for key, t in TRAILS.items():
        start, goal = cell(*t['start']), cell(*t['goal'])
        if not start or not goal:
            raise SystemExit(f'{key}: no usable start/goal cell')
        dist = {start: 0.0}
        prev = {}
        pq = [(0.0, start)]
        moves = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
        while pq:
            d, (j, i) = heapq.heappop(pq)
            if (j, i) == goal:
                break
            if d > dist.get((j, i), 1e18):
                continue
            for dj, di, l in moves:
                a, b = j + dj, i + di
                if not (0 <= a < h and 0 <= b < w) or not ok[a, b]:
                    continue
                run = l * step
                slope = abs(z[a, b] - z[j, i]) / run
                if slope > MAX_SLOPE:
                    continue
                c = run * (1 + 25 * max(0.0, slope - .06) ** 1.5 * 4) * (.6 + 1.1 * field[a, b]) * apart[a, b]
                nd = d + c
                if nd < dist.get((a, b), 1e18):
                    dist[(a, b)] = nd
                    prev[(a, b)] = (j, i)
                    heapq.heappush(pq, (nd, (a, b)))
        if goal not in prev:
            raise SystemExit(f'{key}: no route')
        path = [goal]
        while path[-1] != start:
            path.append(prev[path[-1]])
        path.reverse()
        pts = np.array([[x0 + i * step, y0 + j * step] for j, i in path], np.float64)
        # smooth the staircase, then resample every 2 m
        for _ in range(4):
            pts[1:-1] = (pts[:-2] + 2 * pts[1:-1] + pts[2:]) / 4
        seg = np.hypot(*np.diff(pts, axis=0).T)
        cum = np.concatenate([[0], np.cumsum(seg)])
        n = max(2, int(cum[-1] / 200))
        u = np.linspace(0, cum[-1], n)
        xs, ys = np.interp(u, cum, pts[:, 0]), np.interp(u, cum, pts[:, 1])
        # gentle meander across the walking direction, fading in/out at both ends
        tx, ty = np.gradient(xs), np.gradient(ys)
        tn = np.hypot(tx, ty) + 1e-9
        nx, ny = ty / tn, -tx / tn
        lam = 3500 + 3500 * rng.random()                 # cm per wave, one per trail
        phase = np.cumsum(2 * np.pi * (u[1] - u[0]) / (lam * (.8 + .4 * ndimage.gaussian_filter1d(rng.random(n), 15) * 2)))
        amp = 250 + 250 * ndimage.gaussian_filter1d(rng.random(n), 20) * 2
        fade = np.clip(np.minimum(u, u[-1] - u) / 1500.0, 0, 1)
        off = np.sin(phase) * np.clip(amp, 200, 500) * fade
        for k in range(n):                      # keep the offset only where the ground is usable
            for f in (1.0, .5, 0.0):
                qx, qy = xs[k] + nx[k] * off[k] * f, ys[k] + ny[k] * off[k] * f
                i, j = int(round((qx - x0) / step)), int(round((qy - y0) / step))
                if f == 0.0 or (0 <= j < h and 0 <= i < w and ok[j, i]):
                    off[k] *= f
                    break
        off = ndimage.gaussian_filter1d(off, 3)
        xs, ys = xs + nx * off, ys + ny * off
        mask = np.zeros((h, w), bool)
        for qx, qy in zip(xs, ys):
            i, j = int(round((qx - x0) / step)), int(round((qy - y0) / step))
            if 0 <= j < h and 0 <= i < w:
                mask[j, i] = True
        apart[ndimage.distance_transform_edt(~mask) * step < 6000] = 4.0
        width = np.clip(1.0 + .25 * ndimage.gaussian_filter1d(rng.standard_normal(n), 3) * 2.2, .75, 1.25)
        zz = ndimage.map_coordinates(np.nan_to_num(z, nan=0.0), [(ys - y0) / step, (xs - x0) / step], order=1)
        out['trails'][key] = {'name': t['name'], 'length_m': round(cum[-1] / 100),
                              'points': [[round(a), round(b), round(c)] for a, b, c in zip(xs, ys, zz)],
                              'w': [round(float(v), 2) for v in width]}
        print(key, 'length m', round(cum[-1] / 100), 'points', n, 'z', int(zz.min()), int(zz.max()))
    (ROOT / 'Content' / 'Data' / 'island_trails.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
