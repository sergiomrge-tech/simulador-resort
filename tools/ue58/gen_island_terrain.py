"""New land of the island (08/11, docs/ue58/ILHA_PLANO.md step 4): the slopes and beaches grown around the existing
land (the summit walls, the headlands), from Content/Data/island.json (coast distance) and the land survey.

Height of a new-land point: a short slope (20-80 m) from the height of the nearest existing edge down to a low
coastal plain: the beach rises from the water level (-30 cm) at the coast to +80 cm 40 m inland, then the plain to
1-4 m with soft swells (08/11, Sergio: "não faça tudo montanha": the hill stays the old summit in the middle).
It reaches 2 cells (10 m) under the old land's edge 40 cm below it (no gap at the seam) and 15 m out to sea, down to
-1.2 m, where the sea floor mesh takes over. 5 m grid, glTF in the Godot axes like gen_ocean.py (x, up, UE y / 100).
  python tools/ue58/gen_island_terrain.py -> unreal/MareAlta/SourceArt/Island/IslandTerrain.gltf + .bin
"""
import json
import struct
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2] / 'unreal' / 'MareAlta'
DATA = ROOT / 'Content' / 'Data'
OUT = ROOT / 'SourceArt' / 'Island'


def main():
    cfg = json.loads((DATA / 'island.json').read_text(encoding='utf-8'))
    s = cfg['sdf']
    w, h = s['size']
    step = float(s['cell'])
    ox, oy = s['origin']
    sdf = np.frombuffer((DATA / s['file']).read_bytes(), '<f2').reshape(h, w).astype(np.float64) * 100.0
    survey = json.loads((ROOT / cfg['survey']).read_text(encoding='utf-8'))
    sx0, sx1, sy0, sy1, sstep = [float(v) for v in survey['arg'].split(',')]
    z = np.array([[np.nan if v is None else v for v in row] for row in survey['z']], np.float64)
    grid = np.full((h, w), np.nan)
    gx0, gy0 = int(round((sx0 - ox) / step)), int(round((sy0 - oy) / step))
    grid[gy0:gy0 + z.shape[0], gx0:gx0 + z.shape[1]] = z
    # 08/11 (Sergio: "essa parte marcada vira planície e floresta"): the dome tiles 1877-1936 north of the summit house
    # were removed from the level (mare_island.remove_dome); their ground counts as new land to fill.
    who = np.full((h, w), -1)
    who[gy0:gy0 + z.shape[0], gx0:gx0 + z.shape[1]] = np.array(survey['who'])
    dome_ids = [k for k, name in enumerate(survey['labels']) if '@MeshInstance3D@' in name and name.rsplit('@', 1)[-1].isdigit()
                and 1877 <= int(name.rsplit('@', 1)[-1]) <= 1936]
    grid[np.isin(who, dome_ids)] = np.nan
    land = grid > cfg['water_z']
    land |= np.isnan(grid) & ndimage.binary_closing(land, iterations=3)
    old_z = np.where(land, np.nan_to_num(grid, nan=0.0), 0.0)
    # fill the closed-gap cells of old land with the neighbours' height
    holes = land & np.isnan(grid)
    if holes.any():
        _, (iy, ix) = ndimage.distance_transform_edt(holes | ~land, return_indices=True)
        old_z[holes] = np.nan_to_num(grid, nan=0.0)[iy[holes], ix[holes]]

    d_old, (iy, ix) = ndimage.distance_transform_edt(~land, return_indices=True)
    d_old *= step
    edge_h = np.clip(old_z[iy, ix], -30, None)
    D = sdf                                     # cm, < 0 on the island
    inland = np.clip(-D, 0, None)

    def beach(a):                               # a = cm inland of the waterline (negative = at sea)
        return np.where(a >= 0, -30.0 + np.minimum(a, 4000.0) / 4000.0 * 110.0, -30.0 + a / 1500.0 * 90.0)

    # 08/11 (Sergio: "não faça tudo montanha"): the old edge drops over a short slope (20-80 m, steeper under the high
    # walls) to a low coastal plain (beach, then 1-4 m with soft swells), instead of one long slope down to the sea.
    rng = np.random.default_rng(11)
    swell = ndimage.gaussian_filter(rng.standard_normal((h, w)), 6000.0 / step / 2.5)
    swell /= np.abs(swell).max() or 1
    plain = np.where(inland < 4000, beach(inland), 80.0 + np.clip((inland - 4000.0) / 6000.0, 0, 1) * (220.0 + swell * 140.0))
    reach = np.clip(edge_h * .9, 2000.0, 8000.0)
    t = np.clip(d_old / reach, 0.0, 1.0)
    st = t * t * (3 - 2 * t)
    height = np.where(edge_h > plain, plain + (edge_h - plain) * (1.0 - st), plain)
    height = np.where(D > 0, beach(-D), height)  # at sea: on down to -1.2 m at 15 m out
    # 09/11 (Sergio's photo, a dark strip in the water by the pier): the terrain stopped 15 m out at -1.2 m, 1.5-2 m
    # above the sea floor planes (-2.7 to -3.5 m there): its stepped edge cast a dark line seen through the clear water.
    # It now keeps going down to -4.5 m at 60 m out, ending under the sea floor, which it meets without a step.
    height = np.where(D > 1500, -120.0 - np.clip((D - 1500.0) / 4500.0, 0, 1) * 330.0, height)

    # 10/11 (Sergio's photo by the lighthouse, "flutuando"): a thin arm of the coast_rocks_02 shelf lies over the beach where
    # the sand drops towards the water, with up to 40 cm of dark air under it. The sand rises there to meet it (a soft
    # mound under the arm: world cm x, y, target height, radius), so the rock rests on the beach. The lighthouse trail
    # walks on the shelf itself, so no rock could go there.
    gy_, gx_ = np.mgrid[0:h, 0:w].astype(np.float64)
    for bx, by, bz, br in ((9350, -3700, 26.0, 520.0), (9550, -3760, 20.0, 380.0)):
        d = np.hypot(ox + gx_ * step - bx, oy + gy_ * step - by)
        t = np.clip((d - br * .45) / (br * .55), 0, 1)
        wgt = 1 - t * t * (3 - 2 * t)
        height = np.maximum(height, height * (1 - wgt) + bz * wgt)
    new_land = (D < 0) & ~land
    seam = land & ndimage.binary_dilation(new_land, iterations=2)
    height = np.where(seam, old_z - 40.0, height)
    use = new_land | seam | ((D > 0) & (D < 6000) & ~land)
    use = ndimage.binary_dilation(use, iterations=1) & ~(land & ~seam)
    # 10/11 (Sergio, "todas as rochas ao redor do farol estão erradas"): on the beach between the pier and the lighthouse
    # the old ground lies at -24..-31 cm, right at the sea surface (-30), and the sea showed through it in glassy strips
    # with the old tiles' straight edges. The terrain covers that beach at -12 cm at least, down to the waterline.
    bxw = ox + gx_ * step
    byw = oy + gy_ * step
    lbox = (bxw >= 7500) & (bxw <= 10500) & (byw >= -3260) & (byw <= -2300) & (D < 0)
    height = np.where(lbox, np.maximum(height, -12.0), height)
    use |= lbox & land & (old_z < -8.0)
    # 09/11 (checklist: stair-step rectangles in the west cove): where the survey found an old hill tile under the sea, the
    # hill itself is the sea floor (its material turns to sand and is lifted under the water, M_HillGround_PBR); new-land
    # sea cells over it made flat shelves with the grid's straight edges. No new sea floor over a hill tile.
    hill_ids = [k for k, name in enumerate(survey['labels']) if name.rsplit('@', 1)[-1] in
                {'1869', '1870', '1871', '1872', '1873', '1874', '1875', '1876', '1937', '1938'}]
    hole = np.isin(who, hill_ids) & ~land & (D > 0)
    use &= ~hole
    # 10/11 (west coast from the air: a thin straight dark line in the water): the sea floor stopped at that cut, -0.6 to
    # -0.9 m, on a straight grid line beside the bare sea floor at -1.9 m. Its last points at the cut dip to -2.6 m, under it.
    rim = use & ndimage.binary_dilation(hole, iterations=1) & (D > 0)
    height = np.where(rim, np.minimum(height, -260.0), height)

    # vertices for every used cell corner (the grid points themselves), quads where all four are used
    ys, xs = np.nonzero(use)
    j0, j1, i0, i1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    sub = use[j0:j1 + 1, i0:i1 + 1]
    H = height[j0:j1 + 1, i0:i1 + 1]
    nyv, nxv = sub.shape
    index = -np.ones(sub.shape, np.int64)
    index[sub] = np.arange(sub.sum())
    pos, nrm, uv, idx = bytearray(), bytearray(), bytearray(), bytearray()
    gy, gx = np.gradient(H, step)
    for (j, i) in zip(*np.nonzero(sub)):
        X = ox + (i0 + i) * step
        Y = oy + (j0 + j) * step
        pos += struct.pack('<3f', X / 100.0, H[j, i] / 100.0, Y / 100.0)
        n = np.array([-gx[j, i], 1.0, -gy[j, i]])
        n /= np.linalg.norm(n)
        nrm += struct.pack('<3f', *n)
        uv += struct.pack('<2f', X / 1000.0, Y / 1000.0)
    tris = 0
    # 10/11 (Sergio, "todas as rochas ao redor do farol estão erradas"): the lighthouse shelves are thin slabs with up to
    # 60 cm of dark hollow under their lips; the 5 m grid cannot follow them (a low arm and a high slab 2.6 m apart), so the
    # 5 m cells round them are replaced by a 50 cm patch (same mesh, same material) whose border matches the cells around.
    dune = shelf_dune(height, use, D, ox, oy, step)
    for j in range(nyv - 1):
        for i in range(nxv - 1):
            a, b, c, d = index[j, i], index[j, i + 1], index[j + 1, i], index[j + 1, i + 1]
            if min(a, b, c, d) < 0 or (dune is not None and dune['cells'][j0 + j, i0 + i]):
                continue
            idx += struct.pack('<6I', a, c, b, b, c, d)
            tris += 2
    count = int(sub.sum())
    if dune is not None:
        ppos, pnrm, puv, pidx, pn, ptris = dune_chunks(dune, count)
        pos += ppos
        nrm += pnrm
        uv += puv
        idx += pidx
        count += pn
        tris += ptris
    p = np.frombuffer(bytes(pos), '<f4').reshape(-1, 3)
    blob = bytes(pos + nrm + uv + idx)
    views, offset = [], 0
    for chunk in (pos, nrm, uv, idx):
        views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(chunk)})
        offset += len(chunk)
    gltf = {'asset': {'version': '2.0', 'generator': 'MareAlta island terrain (tools/ue58/gen_island_terrain.py)'},
            'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0, 'name': 'IslandTerrain'}],
            'materials': [{'name': 'IslandTerrain_ground'}],
            'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1, 'TEXCOORD_0': 2}, 'indices': 3, 'material': 0}]}],
            'buffers': [{'uri': 'IslandTerrain.bin', 'byteLength': len(blob)}], 'bufferViews': views,
            'accessors': [{'bufferView': 0, 'componentType': 5126, 'count': count, 'type': 'VEC3',
                           'min': p.min(0).tolist(), 'max': p.max(0).tolist()},
                          {'bufferView': 1, 'componentType': 5126, 'count': count, 'type': 'VEC3'},
                          {'bufferView': 2, 'componentType': 5126, 'count': count, 'type': 'VEC2'},
                          {'bufferView': 3, 'componentType': 5125, 'count': len(idx) // 4, 'type': 'SCALAR'}]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'IslandTerrain.bin').write_bytes(blob)
    (OUT / 'IslandTerrain.gltf').write_text(json.dumps(gltf), encoding='utf-8')
    print(json.dumps({'vertices': count, 'triangles': tris, 'height_cm': [float(np.min(H[sub])), float(np.max(H[sub]))]}))


def shelf_dune(height, use, D, ox, oy, step, sub=10):
    """Sand that beds the rock shelves round the lighthouse into the beach (10/11). SourceArt/Island/shelf_tops.json
    (mare_probe_near.shelf_map) holds the shelf tops on a 50 cm grid. Under a shelf the sand comes to 20 cm below the
    lowest top within 60 cm; outside it falls from 15 cm under the nearest lip at 45 % until it meets the terrain.
    The 5 m cells where it rises (and one cell round them) are rebuilt on a fine lattice (sub x sub per cell) whose
    points lie on the same triangles as the coarse mesh; the rise fades to nothing over 2.5 m before the border of those
    cells and where the terrain dips under the sea, so the border matches the coarse cells around exactly. Returns the plan or None."""
    f = ROOT / 'SourceArt' / 'Island' / 'shelf_tops.json'
    if not f.exists():
        return None
    sj = json.loads(f.read_text(encoding='utf-8'))
    tops = np.array([[np.nan if v is None else v for v in r] for r in sj['tops']], np.float64)
    st = float(sj['step'])
    sx, sy = sj['origin']
    ny, nx = tops.shape
    # only shelves standing above the terrain count: a lower shelf already lying in the sand (the coast_rocks_02 arm under
    # the lighthouse slab) would otherwise pull the sand down under the higher slab next to it
    sjj, sii = np.mgrid[0:ny, 0:nx]
    sfi, sfj = (sx + sii * st - ox) / step, (sy + sjj * st - oy) / step
    sci, scj = np.floor(sfi).astype(int), np.floor(sfj).astype(int)
    su, sv = sfi - sci, sfj - scj
    qa, qb, qc, qd = height[scj, sci], height[scj, sci + 1], height[scj + 1, sci], height[scj + 1, sci + 1]
    ground_s = np.where(su + sv <= 1, qa + su * (qb - qa) + sv * (qc - qa), qd + (1 - su) * (qc - qd) + (1 - sv) * (qb - qd))
    has = ~np.isnan(tops) & (np.nan_to_num(tops, nan=-1e9) > ground_s + 5.0)
    if not has.any():
        return None
    # lowest top of the SAME slab round each point (neighbours within 20 cm of its height), so a lower shelf lying next
    # to a higher one does not pull the sand down under the higher one's lip
    hv = np.where(has, tops, np.nan)
    low = np.where(has, tops, 1e9)
    pad = np.pad(hv, 1, constant_values=np.nan)
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            nb = pad[1 + dj:1 + dj + ny, 1 + di:1 + di + nx]
            same = has & ~np.isnan(nb) & (np.abs(np.nan_to_num(nb) - np.nan_to_num(hv)) < 20.0)
            low = np.where(same, np.minimum(low, nb), low)
    dist, (iy, ix) = ndimage.distance_transform_edt(~has, return_indices=True)
    target_s = np.where(has, low - 20.0, tops[iy, ix] - 15.0 - dist * st * .45)
    # fine lattice aligned with the coarse grid, over the shelf survey plus one cell
    ci0 = int(np.floor((sx - ox) / step)) - 1
    ci1 = int(np.ceil((sx + (nx - 1) * st - ox) / step)) + 1
    cj0 = int(np.floor((sy - oy) / step)) - 1
    cj1 = int(np.ceil((sy + (ny - 1) * st - oy) / step)) + 1
    J, I = np.mgrid[cj0 * sub:cj1 * sub + 1, ci0 * sub:ci1 * sub + 1]
    fi, fj = I / sub, J / sub
    X, Y = ox + fi * step, oy + fj * step
    ci = np.minimum(I // sub, ci1 - 1)
    cj = np.minimum(J // sub, cj1 - 1)
    u, v = fi - ci, fj - cj
    ha, hb, hc, hd = height[cj, ci], height[cj, ci + 1], height[cj + 1, ci], height[cj + 1, ci + 1]
    base = np.where(u + v <= 1, ha + u * (hb - ha) + v * (hc - ha), hd + (1 - u) * (hc - hd) + (1 - v) * (hb - hd))
    tgt = ndimage.map_coordinates(target_s, [(Y - sy) / st, (X - sx) / st], order=1, mode='constant', cval=-1e9)
    # out at sea it fades by the terrain's own depth (the 5 m coast field is too coarse at the shelves' sea edge):
    # full where the beach is above -20 cm, none below -60 cm (no sand banks rising from the sea floor)
    w_sea = np.clip((base + 60.0) / 40.0, 0.0, 1.0)
    rise = np.maximum(tgt - base, 0.0) * w_sea
    # coarse cells (lower-left corner index) that need it, one cell round them, all four corners with terrain
    cell_used = use[:-1, :-1] & use[:-1, 1:] & use[1:, :-1] & use[1:, 1:]
    need = np.zeros(height.shape, bool)
    hit = rise > 1.0
    need[cj[hit], ci[hit]] = True
    cells = ndimage.binary_dilation(need, iterations=1)
    cells[:-1, :-1] &= cell_used
    cells[-1, :] = False
    cells[:, -1] = False
    if not cells.any():
        return None
    # a lattice point is in the patch if any of the (up to 4) cells round it is replaced; inside if all of them are
    def cell_at(dj, di):
        return cells[np.clip((J - dj) // sub, 0, cells.shape[0] - 1), np.clip((I - di) // sub, 0, cells.shape[1] - 1)]
    on_line_x = (I % sub) == 0
    on_line_y = (J % sub) == 0
    around = [cells[cj, ci]]
    around.append(np.where(on_line_x, cell_at(0, 1), cells[cj, ci]))
    around.append(np.where(on_line_y, cell_at(1, 0), cells[cj, ci]))
    around.append(np.where(on_line_x & on_line_y, cell_at(1, 1), cells[cj, ci]))
    inpatch = np.logical_or.reduce(around)
    # the rise fades only towards terrain cells that stay coarse; next to cells with no terrain at all (old ground,
    # under the shelves) there is nothing to meet, so it keeps its height to the border
    open_ = ~cells.copy()
    open_[:-1, :-1] &= cell_used
    open_[-1, :] = True
    open_[:, -1] = True
    def open_at(dj, di):
        return open_[np.clip((J - dj) // sub, 0, open_.shape[0] - 1), np.clip((I - di) // sub, 0, open_.shape[1] - 1)]
    meets = open_[cj, ci] | np.where(on_line_x, open_at(0, 1), False) | np.where(on_line_y, open_at(1, 0), False) \
        | np.where(on_line_x & on_line_y, open_at(1, 1), False)
    interior = ~meets
    edge = np.clip(ndimage.distance_transform_edt(interior) * (step / sub) / 250.0, 0.0, 1.0)
    P = base + rise * edge
    return {'cells': cells, 'X': X, 'Y': Y, 'P': P, 'base': base, 'inpatch': inpatch, 'ci': ci, 'cj': cj,
            'step': step / sub}


def dune_chunks(dune, first):
    """glTF chunks (pos, normal, uv, index) of the fine patch planned by shelf_dune, its quads only in replaced cells."""
    X, Y, P, inpatch, cells, ci, cj = (dune[k] for k in ('X', 'Y', 'P', 'inpatch', 'cells', 'ci', 'cj'))
    gy, gx = np.gradient(P, dune['step'])
    index = -np.ones(P.shape, np.int64)
    index[inpatch] = first + np.arange(inpatch.sum())
    pos, nrm, uvb, idx = bytearray(), bytearray(), bytearray(), bytearray()
    for (j, i) in zip(*np.nonzero(inpatch)):
        pos += struct.pack('<3f', X[j, i] / 100.0, P[j, i] / 100.0, Y[j, i] / 100.0)
        n = np.array([-gx[j, i], 1.0, -gy[j, i]])
        n /= np.linalg.norm(n)
        nrm += struct.pack('<3f', *n)
        uvb += struct.pack('<2f', X[j, i] / 1000.0, Y[j, i] / 1000.0)
    tris = 0
    ny, nx = P.shape
    for j in range(ny - 1):
        for i in range(nx - 1):
            if not cells[cj[j, i], ci[j, i]]:
                continue
            a, b, c, d = index[j, i], index[j, i + 1], index[j + 1, i], index[j + 1, i + 1]
            if min(a, b, c, d) < 0:
                continue
            idx += struct.pack('<6I', a, c, b, b, c, d)
            tris += 2
    lift = (P - dune['base'])[inpatch]
    print(json.dumps({'shelf_dune': {'cells': int(cells.sum()), 'points': int(inpatch.sum()),
                                     'raised': int((lift > 1).sum()), 'max_raise_cm': float(lift.max())}}))
    return pos, nrm, uvb, idx, int(inpatch.sum()), tris

if __name__ == '__main__':
    main()
