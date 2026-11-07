"""Plan the walking trail from the back of the village to the old man's house on the summit (04/11, Sergio: "faça só
uma trilha"). Input: terrain grids D:/CodexTemp/tsunami/tg_*.json (mare_tsunami.terrain_grid, UE cm). A* on the 2.5 m
grid with 16 directions: grade above 25% costs more (log steps there), above 62% (~32 deg) is forbidden, cross-slope and turns cost a
little, so the steep face gets switchbacks. The route is smoothed (Chaikin), resampled every 1 m and written to
D:/CodexTemp/tsunami/trail.json as [x, y, z_terrain] (UE cm)."""
import heapq
import json
import math
from pathlib import Path

D = Path('D:/CodexTemp/tsunami')
STEP = 250.0
START = (5000.0, 8250.0)
GOAL = (4000.0, 37750.0)

H = {}
for f in sorted(D.glob('tg_*.json')):
    for x, y, z in json.loads(f.read_text()):
        if z is not None:
            H[(int(x), int(y))] = float(z)
xs = sorted({k[0] for k in H})
ys = sorted({k[1] for k in H})
X0, Y0 = xs[0], ys[0]


def key(i, j):
    return (int(X0 + i * STEP), int(Y0 + j * STEP))


def h_at(x, y):
    """Bilinear terrain height (cm) at a UE point."""
    fi, fj = (x - X0) / STEP, (y - Y0) / STEP
    i, j = int(math.floor(fi)), int(math.floor(fj))
    u, v = fi - i, fj - j
    zs = [H.get(key(i + a, j + b)) for a in (0, 1) for b in (0, 1)]
    if None in zs:
        zs = [z for z in zs if z is not None] or [0.0]
        return sum(zs) / len(zs)
    return (zs[0] * (1 - u) * (1 - v) + zs[1] * (1 - u) * v + zs[2] * u * (1 - v) + zs[3] * u * v)


def slope_vec(i, j):
    a, b = H.get(key(i + 1, j)), H.get(key(i - 1, j))
    c, d = H.get(key(i, j + 1)), H.get(key(i, j - 1))
    if None in (a, b, c, d):
        return 0.0, 0.0
    return (a - b) / (2 * STEP), (c - d) / (2 * STEP)


DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1),
        (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1)]
NI, NJ = len(xs), len(ys)


def plan():
    s = (round((START[0] - X0) / STEP), round((START[1] - Y0) / STEP))
    g = (round((GOAL[0] - X0) / STEP), round((GOAL[1] - Y0) / STEP))
    openq = [(0.0, 0.0, s, -1)]
    best = {(s, -1): 0.0}
    came = {}
    while openq:
        f, cost, n, d_in = heapq.heappop(openq)
        if n == g:
            path, st = [n], (n, d_in)
            while st in came:
                st = came[st]
                path.append(st[0])
            return path[::-1]
        if cost > best.get((n, d_in), 1e18):
            continue
        z0 = H.get(key(*n))
        for di, (a, b) in enumerate(DIRS):
            m = (n[0] + a, n[1] + b)
            if not (0 <= m[0] < NI and 0 <= m[1] < NJ):
                continue
            z1 = H.get(key(*m))
            if z0 is None or z1 is None:
                continue
            run = STEP * math.hypot(a, b)
            grade = abs(z1 - z0) / run
            if grade > .62:          # ~32 deg: log steps on the steep stretches
                continue
            sx, sy = slope_vec(*m)
            ux, uy = a / math.hypot(a, b), b / math.hypot(a, b)
            cross = abs(-uy * sx + ux * sy)          # slope across the path: embankment height
            turn = 0.0
            if d_in >= 0:
                pa, pb = DIRS[d_in]
                cosang = (pa * a + pb * b) / (math.hypot(pa, pb) * math.hypot(a, b))
                turn = (1 - cosang) * 120
            c = run * (1 + 25 * max(0.0, grade - .25) ** 2 + 4 * max(0.0, grade - .5) + .6 * cross) + turn
            nc = cost + c
            st = (m, di)
            if nc < best.get(st, 1e18):
                best[st] = nc
                came[st] = (n, d_in)
                hdist = STEP * math.hypot(m[0] - g[0], m[1] - g[1])
                heapq.heappush(openq, (nc + hdist, nc, m, di))
    raise RuntimeError('no route')


def chaikin(pts, it=3):
    for _ in range(it):
        out = [pts[0]]
        for p, q in zip(pts, pts[1:]):
            out.append((.75 * p[0] + .25 * q[0], .75 * p[1] + .25 * q[1]))
            out.append((.25 * p[0] + .75 * q[0], .25 * p[1] + .75 * q[1]))
        out.append(pts[-1])
        pts = out
    return pts


def resample(pts, step=100.0):
    cum = [0.0]
    for p, q in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    out, k = [], 0
    n = int(cum[-1] // step)
    for i in range(n + 1):
        t = i * step
        while k < len(cum) - 2 and cum[k + 1] < t:
            k += 1
        seg = max(cum[k + 1] - cum[k], 1e-6)
        u = (t - cum[k]) / seg
        p, q = pts[k], pts[k + 1]
        out.append((p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u))
    out.append(pts[-1])
    return out


if __name__ == '__main__':
    cells = plan()
    pts = [(X0 + i * STEP, Y0 + j * STEP) for i, j in cells]
    pts = resample(chaikin(pts), 100.0)
    # Open the hairpins (radius > path half width + bank): Laplacian smoothing, ends pinned, then resample again.
    for _ in range(60):
        pts = [pts[0]] + [((a[0] + 2 * b[0] + c[0]) / 4, (a[1] + 2 * b[1] + c[1]) / 4) for a, b, c in zip(pts, pts[1:], pts[2:])] + [pts[-1]]
    pts = resample(pts, 100.0)
    rows = [[round(x, 1), round(y, 1), round(h_at(x, y), 1)] for x, y in pts]
    length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(rows, rows[1:])) / 100
    grades = [abs(b[2] - a[2]) / max(1, math.hypot(b[0] - a[0], b[1] - a[1])) for a, b in zip(rows, rows[1:])]
    (D / 'trail.json').write_text(json.dumps(rows))
    print('points', len(rows), 'length_m', round(length), 'rise_m', round((rows[-1][2] - rows[0][2]) / 100, 1),
          'max_grade', round(max(grades), 2), 'p95', round(sorted(grades)[int(.95 * len(grades))], 2))
    print('walk at 2.6 m/s:', round(length / 2.6), 's; sprint 4.2 m/s:', round(length / 4.2), 's')
