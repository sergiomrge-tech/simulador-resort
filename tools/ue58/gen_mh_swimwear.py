"""Small triangle bikini (or swim trunks) fitted to an exported MetaHuman body, skinned to its skeleton.

Run with the isolated bpy 5.0.1 venv (Blender is not installed):
  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_mh_swimwear.py -- <body.fbx> <out.fbx> bikini|trunks|tank|boardshorts|coverup|chasuble

The body comes from mare_metahuman.export (UE FBX, metres in Blender, front = -Y, up = +Z). Every piece is a
surface patch: a regular grid of guide points is ray cast onto the body (front pieces along +Y, back pieces
along -Y, the gusset along +Z, strings radially toward the body axis), lifted a few millimetres along the
surface normal, then thickened. Weights are copied from the body (nearest face, interpolated), so the garment
follows the MetaHuman skeleton exactly like the skin underneath it. Landmarks are measured per body, so the same
script fits every MetaHuman body shape.
"""
import sys
import math
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args = sys.argv[sys.argv.index('--') + 1:]
SRC, DST, KIND = args[0], args[1], (args[2] if len(args) > 2 else 'bikini')
LIFT = .0032
STEP = .0035
BODY = None   # body skin (world space bmesh), set in main
DOM_FACE = []  # dominant bone of every BODY face (ray hits report face indices)


def load_body():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=SRC)
    body = next(o for o in bpy.data.objects if o.type == 'MESH')
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    deps = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    bm.from_object(body, deps)
    bm.transform(body.matrix_world)
    bm.normal_update()
    return body, arm, bm, BVHTree.FromBMesh(bm)


def measure(bm):
    ws = [v.co.copy() for v in bm.verts]
    neck = max(w.z for w in ws if abs(w.x) < .05)
    # The bust sits 12-23 cm below the neck cut; searching lower picks a rounder belly (Asha: belly at 29 cm).
    bust = min((w for w in ws if .03 < w.x < .15 and neck - .23 < w.z < neck - .12), key=lambda w: w.y)
    crotch = min((w for w in ws if abs(w.x) < .015 and .55 < w.z < 1.0), key=lambda w: w.z)
    hips = max((w for w in ws if .75 < w.z < 1.0 and abs(w.x) < .26), key=lambda w: abs(w.x))
    return {'bust': bust, 'crotch': crotch, 'hip_z': hips.z, 'hip_x': abs(hips.x), 'neck': neck}


def cast(tree, origin, direction):
    hit = tree.ray_cast(origin, direction)
    if hit[0] is None:
        return None
    return hit[0] + hit[1] * LIFT


def inside(poly, x, y):
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def closest_on(poly, x, y):
    best, bd = (x, y), 1e9
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i - 1], poly[i]
        dx, dy = x2 - x1, y2 - y1
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy or 1e-12)))
        px, py = x1 + t * dx, y1 + t * dy
        d = math.hypot(x - px, y - py)
        if d < bd:
            best, bd = (px, py), d
    return best, bd


def patch(bm_out, tree, poly, plane, lift=0.0):
    """Grid patch inside a 2D outline. plane: 'front' (x,z; rays +Y), 'back' (x,z; rays -Y), 'under' (x,y; rays +Z)."""
    us = [p[0] for p in poly]
    vs = [p[1] for p in poly]
    nu = int((max(us) - min(us)) / STEP) + 2
    nv = int((max(vs) - min(vs)) / STEP) + 2
    grid = {}
    for i in range(-1, nu + 1):
        for j in range(-1, nv + 1):
            u, v = min(us) + i * STEP, min(vs) + j * STEP
            if not inside(poly, u, v):
                # Grid points just outside are pulled onto the outline, so edges follow the design, not the grid.
                q, d = closest_on(poly, u, v)
                if d > STEP * 1.05:
                    continue
                u, v = q
            if plane == 'front':
                p = cast(tree, Vector((u, -.6, v)), Vector((0, 1, 0)))
            elif plane == 'back':
                p = cast(tree, Vector((u, .6, v)), Vector((0, -1, 0)))
            else:
                p = cast(tree, Vector((u, v, .3)), Vector((0, 0, 1)))
            if p is not None:
                n = tree.find_nearest(p)[1]
                grid[i, j] = bm_out.verts.new(p + n * lift)
    for (i, j), a in grid.items():
        b, c, d = grid.get((i + 1, j)), grid.get((i + 1, j + 1)), grid.get((i, j + 1))
        if b and c and d:
            bm_out.faces.new((a, b, c, d))
    return list(grid.values())


def drape(bm_out, tree, verts, cz_bridge=-1.0, rounds=24):
    """Let a patch span body creases like fabric: smooth it, then push any point that sank back above the skin."""
    inner = [v for v in verts if v.is_valid and v.link_faces and (not v.is_boundary or v.co.z < cz_bridge)]
    for _ in range(rounds):
        bmesh.ops.smooth_vert(bm_out, verts=inner, factor=.6, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        for v in verts:
            if not v.is_valid:
                continue
            q, n = tree.find_nearest(v.co)[:2]
            if (v.co - q).dot(n) < LIFT:
                v.co = q + n * LIFT


def ribbon(bm_out, tree, path, width, up=None):
    """Narrow strip through guide points, each snapped to the body; `up` gives the strip's cross direction."""
    pts = []
    for g in path:
        p, n = tree.find_nearest(g)[:2]
        pts.append((p + n * (LIFT + .0004), n))
    rows = []
    for k, (p, n) in enumerate(pts):
        t = (pts[min(k + 1, len(pts) - 1)][0] - pts[max(k - 1, 0)][0]).normalized()
        side = (up or n.cross(t)).normalized() * (width / 2)
        rows.append((bm_out.verts.new(p - side), bm_out.verts.new(p + side)))
    for (a, b), (c, d) in zip(rows, rows[1:]):
        bm_out.faces.new((a, c, d, b))


def ring_path(tree, z, a0, a1, cx=0.0, cy=-.01, steps=40):
    """Guide points around the torso at height z between angles a0..a1 (0 = front, +90 = left side)."""
    out = []
    for k in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * k / steps)
        d = Vector((math.sin(a), -math.cos(a), 0))
        hit = tree.ray_cast(Vector((cx, cy, z)), d)     # from the torso axis outward: the torso is hit before the arms
        if hit[0] is not None:
            out.append(hit[0])
    return out


def curve(a, b, bulge, n=8):
    """Points from a to b bowed sideways by `bulge` (2D)."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1
    cx, cy = mx - dy / ln * bulge, my + dx / ln * bulge
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * cx + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * cy + t * t * b[1])
            for t in (k / n for k in range(n))]


def catmull(keys, n):
    """Smooth guide through the key points (Catmull-Rom, end points repeated)."""
    k = [keys[0]] + keys + [keys[-1]]
    out = []
    for i in range(1, len(k) - 2):
        p0, p1, p2, p3 = k[i - 1], k[i], k[i + 1], k[i + 2]
        for j in range(n):
            t = j / n
            out.append(.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3))
    return out + [keys[-1]]


def angle_of(p):
    return math.degrees(math.atan2(-p.x, -(p.y + .01))) * -1


def bikini(bm_out, tree, m):
    bust, cz = m['bust'], m['crotch'].z
    top = cz + .155                     # low-rise waistline, ~15 cm above the crotch
    # Bottom: small front triangle whose leg openings follow the groin crease (curving in toward the centre, so
    # the cloth never reaches the front of the thighs), cheeky back, gusset under the crotch.
    front = patch(bm_out, tree, curve((-.085, top), (-.03, cz + .075), .022) + curve((-.03, cz + .075), (-.015, cz + .03), .004) + [(-.013, cz + .026), (.013, cz + .026)] +
          curve((.015, cz + .03), (.03, cz + .075), .004) + curve((.03, cz + .075), (.085, top), .022) + curve((.085, top), (-.085, top), .006), 'front')
    back = patch(bm_out, tree, curve((.10, top + .008), (.026, cz + .05), .02) + [(.02, cz + .03), (-.02, cz + .03)] +
          curve((-.026, cz + .05), (-.10, top + .008), .02) + curve((-.10, top + .008), (.10, top + .008), -.008), 'back')
    drape(bm_out, tree, front, cz + .05)   # the narrow part between the legs may tighten like fabric
    drape(bm_out, tree, back, cz + .05)
    # Narrow gusset joining both pieces under the crotch, kept between the thighs.
    fy = cast(tree, Vector((0, -.6, cz + .03)), Vector((0, 1, 0)))
    by = cast(tree, Vector((0, .6, cz + .03)), Vector((0, -1, 0)))
    if fy and by:
        patch(bm_out, tree, [(-.016, fy.y - .006), (.016, fy.y - .006), (.018, by.y + .006), (-.018, by.y + .006)], 'under', .0006)
    # Side strings over the hips, front corner to back corner.
    for s in (1, -1):
        f = cast(tree, Vector((s * .083, -.6, top - .002)), Vector((0, 1, 0)))
        b = cast(tree, Vector((s * .098, .6, top + .006)), Vector((0, -1, 0)))
        if f and b:
            a0, a1 = angle_of(f), angle_of(b)
            path = [p.lerp(Vector((p.x, p.y, top + .012)), math.sin(math.pi * k / 30) * .6)
                    for k, p in enumerate(ring_path(tree, top + .002, a0, a1, steps=30))]
            ribbon(bm_out, tree, path, .011, Vector((0, 0, 1)))
    # Top: strapless bandeau (user's choice, 02/11): a band of fabric around the chest from just under the bust
    # to above the nipple line, settled over the breasts and across the cleavage like stretched cloth.
    under = bust.z - .06
    rows = [bust.z + .05 - k * .011 for k in range(int((bust.z + .05 - under) / .011) + 1)]
    band = tube_rows(bm_out, tree, rows, lambda z: (0.0, -.01), lift=.0012)
    drape(bm_out, tree, [v for ring in band for v in ring], -1.0, rounds=10)


def tube_rows(bm_out, tree, rows, centre_of, steps=72, lift=.001):
    """Continuous fabric through stacked rings: each row is cast from an axis point outward (so the cloth hugs
    the hips or a thigh), lifted off the skin, and consecutive rows are joined into quads. Where a ray finds no
    skin (between the legs, below the crotch) the cloth hangs straight down from the row above, like real fabric
    bridging the gap."""
    rings, prev = [], None
    for z in rows:
        cx, cy = centre_of(z)
        ring, pts = [], []
        for k in range(steps):
            a = 2 * math.pi * k / steps
            d = Vector((math.sin(a), -math.cos(a), 0))
            hit = tree.ray_cast(Vector((cx, cy, z)), d)
            if hit[0] is not None and (prev is None or (hit[0] - prev[k]).length < .08):
                pts.append(hit[0] + hit[1] * (LIFT + lift))
            elif prev is not None:
                pts.append(Vector((prev[k].x, prev[k].y, z)))
            else:
                pts = None
                break
        if pts is None:
            continue
        # Points that landed on an arm (far out near the armpit) take the average of their nearest torso neighbours.
        radii = [math.hypot(q.x - cx, q.y - cy) for q in pts]
        limit = sorted(radii)[len(radii) // 2] * 1.22
        good = [r <= limit for r in radii]
        for k in range(steps):
            if not good[k]:
                lo = next((pts[(k - d) % steps] for d in range(1, steps) if good[(k - d) % steps]), pts[k])
                hi = next((pts[(k + d) % steps] for d in range(1, steps) if good[(k + d) % steps]), pts[k])
                pts[k] = (lo + hi) / 2
        ring = [bm_out.verts.new(q) for q in pts]
        rings.append(ring)
        prev = pts
    for a, b in zip(rings, rings[1:]):
        for k in range(steps):
            bm_out.faces.new((a[k], a[(k + 1) % steps], b[(k + 1) % steps], b[k]))
    return rings


def trunks(bm_out, tree, m):
    """Boxer swim trunks as ONE continuous surface: the body's own skin between the waistband and the leg hems,
    cut by straight planes, lifted off the skin and draped over the groin and buttock creases. Earlier versions
    built a hip tube and separate thigh tubes, which always left a visible step or seam where they met."""
    cz = m['crotch'].z
    top, hem = cz + .17, cz - .11
    skin = BODY.copy()
    geom = skin.verts[:] + skin.edges[:] + skin.faces[:]
    bmesh.ops.bisect_plane(skin, geom=geom, plane_co=(0, 0, top), plane_no=(0, 0, 1), clear_outer=True)
    geom = skin.verts[:] + skin.edges[:] + skin.faces[:]
    bmesh.ops.bisect_plane(skin, geom=geom, plane_co=(0, 0, hem), plane_no=(0, 0, -1), clear_outer=True)
    # Hands hang beside the hips in the A pose: keep only the trunk and the thighs.
    far = [f for f in skin.faces if abs(f.calc_center_median().x) > m['hip_x'] + .04]
    bmesh.ops.delete(skin, geom=far, context='FACES')
    loose = [v for v in skin.verts if not v.link_faces]
    bmesh.ops.delete(skin, geom=loose, context='VERTS')
    # One smooth subdivision: the body is a game mesh, and its coarse faces let skin poke through the cloth.
    # The MetaHuman body is split along its UV seams (the mid line too): weld it so the cloth is one sheet.
    bmesh.ops.remove_doubles(skin, verts=skin.verts[:], dist=.0005)
    bmesh.ops.subdivide_edges(skin, edges=skin.edges[:], cuts=1, use_grid_fill=True, smooth=1.0)
    # The smooth subdivision moves the cut edges off their planes (a frayed look): put them back.
    for v in skin.verts:
        if v.is_boundary and min(abs(v.co.z - top), abs(v.co.z - hem)) < .012:
            v.co.z = top if abs(v.co.z - top) < abs(v.co.z - hem) else hem
    skin.normal_update()
    for v in skin.verts:
        v.co += v.normal * (LIFT + .001)
    mesh = bpy.data.meshes.new('trunks_tmp')
    skin.to_mesh(mesh)
    skin.free()
    first = len(bm_out.verts)
    bm_out.from_mesh(mesh)
    bpy.data.meshes.remove(mesh)
    bm_out.verts.ensure_lookup_table()
    verts = bm_out.verts[first:]
    # Fabric bridges the creases instead of following them (boundary rows stay on the cut planes).
    drape(bm_out, tree, verts, -1.0, rounds=12)



# ---------------------------------------------------------------- beachwear worn over the swimwear (02/11)
ARM_WORDS = ('arm', 'hand', 'thumb', 'index_', 'middle_', 'ring_', 'pinky')
DOM = []          # dominant deform bone of every body vertex (same order as BODY)


def is_arm(name):
    return any(w in name for w in ARM_WORDS)


def face_bones(f):
    return [DOM[v.index] for v in f.verts]


def skin_piece(bm_out, tree, top, hem, keep, offset, rounds=8):
    """Fabric copied from the body's skin between two horizontal cuts, keeping only the faces keep(face) accepts
    (armholes and necklines follow the body's own topology), welded, subdivided once, its free edges smoothed,
    lifted by offset(point) and draped. Returns the new garment vertices in bm_out."""
    skin = BODY.copy()
    skin.verts.ensure_lookup_table()
    skin.faces.ensure_lookup_table()
    bmesh.ops.delete(skin, geom=[f for f in skin.faces if not keep(f)], context='FACES')
    for z, n in ((top, (0, 0, 1)), (hem, (0, 0, -1))):
        geom = skin.verts[:] + skin.edges[:] + skin.faces[:]
        bmesh.ops.bisect_plane(skin, geom=geom, plane_co=(0, 0, z), plane_no=n, clear_outer=True)
    bmesh.ops.delete(skin, geom=[v for v in skin.verts if not v.link_faces], context='VERTS')
    bmesh.ops.remove_doubles(skin, verts=skin.verts[:], dist=.0005)
    # Small islands (finger tips, a stray face) are not part of the garment.
    seen, islands = set(), []
    for f in skin.faces:
        if f in seen:
            continue
        stack, island = [f], []
        seen.add(f)
        while stack:
            g = stack.pop()
            island.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h not in seen:
                        seen.add(h)
                        stack.append(h)
        islands.append(island)
    big = max(len(i) for i in islands)
    bmesh.ops.delete(skin, geom=[f for i in islands if len(i) < big * .2 for f in i], context='FACES')
    bmesh.ops.delete(skin, geom=[v for v in skin.verts if not v.link_faces], context='VERTS')
    bmesh.ops.subdivide_edges(skin, edges=skin.edges[:], cuts=1, use_grid_fill=True, smooth=1.0)
    # Free edges: the straight cuts go back on their planes; armholes and necklines are evened out along the edge.
    for _ in range(4):
        moves = {}
        for v in skin.verts:
            if not v.is_boundary or min(abs(v.co.z - top), abs(v.co.z - hem)) < .012:
                continue
            ring = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(ring) == 2:
                moves[v] = (ring[0].co + ring[1].co + v.co * 2) / 4
        for v, c in moves.items():
            v.co = c
    for v in skin.verts:
        if v.is_boundary and min(abs(v.co.z - top), abs(v.co.z - hem)) < .012:
            v.co.z = top if abs(v.co.z - top) < abs(v.co.z - hem) else hem
    for v in skin.verts:
        q, n = tree.find_nearest(v.co)[:2]
        v.co = q + n * offset(q)
    mesh = bpy.data.meshes.new('piece_tmp')
    skin.to_mesh(mesh)
    skin.free()
    first = len(bm_out.verts)
    bm_out.from_mesh(mesh)
    bpy.data.meshes.remove(mesh)
    bm_out.verts.ensure_lookup_table()
    verts = list(bm_out.verts[first:])
    drape(bm_out, tree, verts, -1.0, rounds=rounds)
    return verts


def torso_keep(m, strap_x, scoop):
    """Faces of the chest, belly and back plus shoulder straps (clavicle faces near the neck); arms and neck out,
    with a scooped neckline (deeper in front)."""
    neck = m['neck']

    def keep(f):
        bones = face_bones(f)
        if any(is_arm(b) or 'neck' in b or 'head' in b for b in bones):
            return False
        c = f.calc_center_median()
        if any('clavicle' in b for b in bones) and abs(c.x) > strap_x:
            return False
        front = 1.0 if c.y < -.02 else 0.0
        if abs(c.x) < .065 and c.z > neck - .06 - scoop * front:   # the straps (|x| .065 .. strap_x) stay
            return False
        return True
    return keep


def tank(bm_out, tree, m):
    """Tank top (regata) worn over the swimwear: chest to hips, wide straps, scooped neck, a little loose."""
    cz = m['crotch'].z
    skin_piece(bm_out, tree, m['neck'] - .01, cz + .11, torso_keep(m, .12, .07), lambda q: LIFT + .009, rounds=20)


def boardshorts(bm_out, tree, m):
    """Surf shorts (bermuda de surfe): waist to above the knee, the legs widening toward the hem like real board
    shorts; replaces the trunks of the swim build."""
    cz = m['crotch'].z
    top, hem = cz + .15, cz - .27
    skin_piece(bm_out, tree, top, hem, lambda f: not any(is_arm(b) for b in face_bones(f)),
               lambda q: LIFT + .006 + .018 * min(1.0, max(0.0, (cz - q.z) / (cz - hem))))


def hull_radius(tree, z, a, cx, cy):
    """Outer silhouette of the body at height z in direction a (0 = front): a ray from outside inward, passing
    through the arms and hands (they hang beside the hips in the A pose)."""
    d = Vector((math.sin(a), -math.cos(a), 0))
    o = Vector((cx, cy, z)) + d * 1.0
    for _ in range(6):
        hit = tree.ray_cast(o, -d)
        if hit[0] is None:
            return None
        if not is_arm(DOM_FACE[hit[2]]):
            return Vector((hit[0].x - cx, hit[0].y - cy, 0)).length
        o = hit[0] - d * .002
    return None


def convex_radii(points, angles, cx, cy):
    """Distance from (cx, cy) to the convex hull of the 2D points along each angle (0 = front): cloth spans the
    gap between the legs straight, as fabric does, instead of dipping into it."""
    pts = sorted(set((round(x, 5), round(y, 5)) for x, y in points))
    if len(pts) < 3:
        return None

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for q in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    for q in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    hull = lower[:-1] + upper[:-1]
    out = []
    for a in angles:
        dx, dy = math.sin(a), -math.cos(a)
        best = None
        for i in range(len(hull)):
            (x1, y1), (x2, y2) = hull[i - 1], hull[i]
            ex, ey = x2 - x1, y2 - y1
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t = ((x1 - cx) * ey - (y1 - cy) * ex) / den
            u = ((x1 - cx) * dy - (y1 - cy) * dx) / den
            if t > 0 and -1e-6 <= u <= 1 + 1e-6 and (best is None or t > best):
                best = t
        out.append(best)
    return out


def convexify(verts, z_from, z_to, cx=0.0, cy=-.01):
    """Bridge the body's creases (groin, navel, small of the back) in the lower part of a bodice: every vertex
    between z_from (untouched) and z_to (fully on the outline) moves out toward the convex outline of its 1 cm
    band, like cloth stretched across a hollow."""
    bands = {}
    for v in verts:
        if v.is_valid and z_to <= v.co.z <= z_from:
            bands.setdefault(int(v.co.z / .01), []).append(v)
    for band in bands.values():
        if len(band) < 6:
            continue
        angles = [math.atan2(v.co.x - cx, -(v.co.y - cy)) for v in band]
        hull = convex_radii([(v.co.x, v.co.y) for v in band], angles, cx, cy)
        if not hull:
            continue
        for v, a, h in zip(band, angles, hull):
            if h is None:
                continue
            r = math.hypot(v.co.x - cx, v.co.y - cy)
            t = min(1.0, max(0.0, (z_from - v.co.z) / (z_from - z_to)))
            w = t * t * (3 - 2 * t)
            if h > r:
                r += (h - r) * w
                v.co.x, v.co.y = cx + math.sin(a) * r, cy - math.cos(a) * r


def coverup(bm_out, tree, m):
    """Beach cover-up (saida de praia): a short dress over the bikini. The bodice is the tank's (straps, scooped
    neck) down to the hips; the skirt is its own tube of regular rings that starts 2 cm above the bodice's edge and
    covers it (a waist seam, as on a real dress). Each ring follows the convex outline of the hips and both legs,
    never narrows and opens at most ~20 degrees, to mid-thigh."""
    cz = m['crotch'].z
    waist = cz + .10            # bodice edge: above the groin crease and the top of the buttocks
    verts = skin_piece(bm_out, tree, m['neck'] - .01, waist, torso_keep(m, .11, .09), lambda q: LIFT + .007, rounds=20)
    convexify(verts, cz + .27, waist + .02)
    cx, cy, n = 0.0, -.01, 96
    angles = [2 * math.pi * i / n for i in range(n)]
    top, bottom = waist + .02, cz - .22
    rows = int((top - bottom) / .012) + 1
    table, last = [], None
    for k in range(rows):
        z = top - k * .012
        hits = [hull_radius(tree, z, a, cx, cy) for a in angles]
        pts = [(cx + math.sin(a) * r, cy - math.cos(a) * r) for a, r in zip(angles, hits) if r is not None]
        hull = convex_radii(pts, angles, cx, cy) or hits
        row = []
        for i in range(n):
            r = hull[i] if hull[i] is not None else (last[i] if last else .15)
            r += LIFT + .0085
            if last:
                r = max(last[i] * .995, min(r, last[i] + .0045))
            row.append(r)
        table.append(row)
        last = row
    raw_first = list(table[0])
    for _ in range(4):
        table = [[(row[i - 1] + 2 * row[i] + row[(i + 1) % n]) / 4 for i in range(n)] for row in table]
    for _ in range(2):
        table = [[(table[max(k - 1, 0)][i] + 2 * table[k][i] + table[min(k + 1, len(table) - 1)][i]) / 4 for i in range(n)] for k in range(len(table))]
    # The first ring tucks just inside the bodice (which covers it down to the waist) and the next four ease out.
    first = [r - .003 for r in raw_first]
    for k in range(min(5, len(table))):
        e = k / 5
        e = e * e * (3 - 2 * e)
        table[k] = [first[i] + (table[k][i] - first[i]) * e for i in range(n)]
    rings = [[bm_out.verts.new(Vector((cx + math.sin(a) * r, cy - math.cos(a) * r, top - k * .012))) for a, r in zip(angles, row)]
             for k, row in enumerate(table)]
    for ra, rb in zip(rings, rings[1:]):
        for i in range(n):
            bm_out.faces.new((ra[i], rb[i], rb[(i + 1) % n], ra[(i + 1) % n]))


def skirt_rings(bm_out, tree, top, bottom, lift, grow=.0045, n=96, cx=0.0, cy=-.01):
    """A tube of regular rings from top down to bottom that follows the convex outline of the hips and both legs
    (arms ignored), never narrows and opens at most `grow` per 1.2 cm ring. Returns its faces."""
    angles = [2 * math.pi * i / n for i in range(n)]
    rows = int((top - bottom) / .012) + 1
    table, last = [], None
    for k in range(rows):
        z = top - k * .012
        hits = [hull_radius(tree, z, a, cx, cy) for a in angles]
        pts = [(cx + math.sin(a) * r, cy - math.cos(a) * r) for a, r in zip(angles, hits) if r is not None]
        hull = convex_radii(pts, angles, cx, cy) or hits
        row = []
        for i in range(n):
            r = (hull[i] if hull[i] is not None else (last[i] - lift if last else .15)) + lift
            if last:
                r = max(last[i], min(r, last[i] + grow))
            row.append(r)
        table.append(row)
        last = row
    for _ in range(4):
        table = [[(row[i - 1] + 2 * row[i] + row[(i + 1) % n]) / 4 for i in range(n)] for row in table]
    for _ in range(2):
        table = [[(table[max(k - 1, 0)][i] + 2 * table[k][i] + table[min(k + 1, len(table) - 1)][i]) / 4 for i in range(n)] for k in range(len(table))]
    rings = [[bm_out.verts.new(Vector((cx + math.sin(a) * r, cy - math.cos(a) * r, top - k * .012))) for a, r in zip(angles, row)]
             for k, row in enumerate(table)]
    faces = []
    for ra, rb in zip(rings, rings[1:]):
        for i in range(n):
            faces.append(bm_out.faces.new((ra[i], rb[i], rb[(i + 1) % n], ra[(i + 1) % n])))
    return faces


def chasuble(bm_out, tree, m):
    """Mass vestments of the village priest (11/11, Sergio's reference photo): a loose red chasuble from the shoulders
    to mid-shin with wide sleeves to the forearm, the white alb showing at the neck, the forearms and the hem, and a
    silver pectoral cross on its chain. Material slots: 0 red, 1 white, 2 metal."""
    cz, neck = m['crotch'].z, m['neck']
    waist = cz + .10

    def tag(start, index):
        bm_out.faces.ensure_lookup_table()
        for f in bm_out.faces[start:]:
            f.material_index = index

    # forearm extent per side (A pose: the wrist is the low end)
    fore = {}
    for f in BODY.faces:
        b = DOM_FACE[f.index]
        if 'lowerarm' in b:
            c = f.calc_center_median()
            lo, hi = fore.get(c.x > 0, (9, -9))
            fore[c.x > 0] = (min(lo, c.z), max(hi, c.z))

    def bone_of(q):
        return DOM_FACE[tree.find_nearest(q)[2]]

    # 1. the alb (white): neck and upper chest, whole forearms, and a skirt from the knee to the ankle
    n0 = len(bm_out.faces)

    def alb_neck(f):
        bones = face_bones(f)
        c = f.calc_center_median()
        return not any(is_arm(b) or 'head' in b for b in bones) and abs(c.x) < .15
    skin_piece(bm_out, tree, neck - .004, neck - .17, alb_neck, lambda q: LIFT + .010, rounds=12)

    def alb_sleeve(f):
        bones = face_bones(f)
        return all('lowerarm' in b for b in bones)
    skin_piece(bm_out, tree, neck, .3, alb_sleeve, lambda q: LIFT + .008, rounds=8)
    skirt_rings(bm_out, tree, cz - .28, .085, LIFT + .014, grow=.0016)
    tag(n0, 1)

    # 2. the chasuble (red): torso and arms down to 45 % of the forearm, a round neckline, then the skirt
    n1 = len(bm_out.faces)

    def red_keep(f):
        bones = face_bones(f)
        c = f.calc_center_median()
        if any(w in b for b in bones for w in ('hand', 'thumb', 'index_', 'middle_', 'ring_', 'pinky', 'neck', 'head')):
            return False
        if any('lowerarm' in b for b in bones):
            lo, hi = fore.get(c.x > 0, (0, 1))
            return c.z > lo + .55 * (hi - lo)
        front = 1.0 if c.y < -.02 else 0.0
        if math.hypot(c.x, 0) < .085 and c.z > neck - .045 - .055 * front:
            return False
        return True

    def red_offset(q):
        b = bone_of(q)
        if 'lowerarm' in b:
            return LIFT + .045
        if 'upperarm' in b:
            return LIFT + .034
        return LIFT + .024
    verts = skin_piece(bm_out, tree, neck - .012, waist, red_keep, red_offset, rounds=26)
    convexify([v for v in verts if abs(v.co.x) < .2], cz + .30, waist + .02)
    skirt_rings(bm_out, tree, waist + .03, .30, LIFT + .026, grow=.0030)
    tag(n1, 0)

    # 3. pectoral cross and chain (metal), lying on the chasuble
    n2 = len(bm_out.faces)

    def on_cloth(x, z, lift):
        hit = tree.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))[0]
        return Vector((x, (hit.y if hit else -.12) - lift, z))
    cx_z = neck - .30
    top = on_cloth(0, cx_z + .045, .034)

    def slab(c, sx, sy, sz):
        vs = [bm_out.verts.new(c + Vector((dx * sx / 2, dy * sy / 2, dz * sz / 2))) for dz in (-1, 1) for dy in (-1, 1) for dx in (-1, 1)]
        for a, b, c2, d in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            bm_out.faces.new((vs[a], vs[b], vs[c2], vs[d]))
    body_c = on_cloth(0, cx_z, .034)
    slab(body_c, .016, .006, .088)
    slab(body_c + Vector((0, 0, .014)), .056, .006, .016)
    for side in (-1, 1):
        prev = None
        for k in range(15):
            t = k / 14
            x = side * (.082 * (1 - t) + .004 * t)
            z = (neck - .05) * (1 - t) + (cx_z + .046) * t - .02 * math.sin(math.pi * t)
            c = on_cloth(x, z, .031)
            pair = (bm_out.verts.new(c + Vector((-.002, 0, 0))), bm_out.verts.new(c + Vector((.002, 0, 0))))
            if prev:
                bm_out.faces.new((prev[0], prev[1], pair[1], pair[0]))
            prev = pair
    del top
    tag(n2, 2)


def smooth_skirt_weights(garment, below_z, rounds=12):
    """Skirt below the crotch: weights averaged with the neighbours so the cloth spans both legs instead of tearing
    between them when walking."""
    me = garment.data
    nbr = [[] for _ in me.vertices]
    for e in me.edges:
        a, b = e.vertices
        nbr[a].append(b)
        nbr[b].append(a)
    idx = [v.index for v in me.vertices if v.co.z < below_z]
    if not idx:
        return
    groups = {g.index: g for g in garment.vertex_groups}
    w = [{g.group: g.weight for g in v.groups} for v in me.vertices]
    for _ in range(rounds):
        new = {}
        for i in idx:
            acc = {k: v * .5 for k, v in w[i].items()}
            for j in nbr[i]:
                for k, v in w[j].items():
                    acc[k] = acc.get(k, 0) + v * .5 / max(1, len(nbr[i]))
            tot = sum(acc.values()) or 1
            new[i] = {k: v / tot for k, v in acc.items() if v / tot > .01}
        for i, d in new.items():
            w[i] = d
    for i in idx:
        for g in garment.vertex_groups:
            g.remove([i])
        for k, v in w[i].items():
            groups[k].add([i], v, 'REPLACE')


def main():
    global BODY, DOM, DOM_FACE
    body, arm, bm, tree = load_body()
    BODY = bm
    names = {g.index: g.name for g in body.vertex_groups}
    DOM = [names[max(v.groups, key=lambda x: x.weight).group] if v.groups else '' for v in body.data.vertices]
    bm.faces.ensure_lookup_table()
    DOM_FACE = [max((DOM[v.index] for v in f.verts), key=lambda b: sum(1 for v in f.verts if DOM[v.index] == b)) for f in bm.faces]
    m = measure(bm)
    out = bmesh.new()
    {'bikini': bikini, 'trunks': trunks, 'tank': tank, 'boardshorts': boardshorts, 'coverup': coverup, 'chasuble': chasuble}[KIND](out, tree, m)
    bmesh.ops.remove_doubles(out, verts=out.verts, dist=.0008)
    # One consistent outward winding for pieces built separately (the cover-up's top and its skirt rings).
    bmesh.ops.recalc_face_normals(out, faces=out.faces[:])
    mesh = bpy.data.meshes.new(f'SKM_{KIND}')
    out.to_mesh(mesh)
    garment = bpy.data.objects.new(f'SKM_{KIND}', mesh)
    bpy.context.scene.collection.objects.link(garment)
    garment.data.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        poly.use_smooth = True
    mat = bpy.data.materials.new(f'MI_MH_{KIND.capitalize()}')
    mesh.materials.append(mat)
    if KIND == 'chasuble':   # slots 1 and 2: the white alb and the metal of the cross (face material_index set while building)
        for extra in ('White', 'Metal'):
            mesh.materials.append(bpy.data.materials.new(f'MI_MH_{KIND.capitalize()}_{extra}'))
    # Thickness, then the body's weights (nearest face, interpolated) and the same armature deform.
    sol = garment.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = .0016
    sol.offset = 1
    bpy.context.view_layer.objects.active = garment
    bpy.ops.object.modifier_apply(modifier='Solidify')
    for g in body.vertex_groups:
        garment.vertex_groups.new(name=g.name)
    dt = garment.modifiers.new('Weights', 'DATA_TRANSFER')
    dt.object = body
    dt.use_object_transform = True
    dt.use_vert_data = True
    dt.data_types_verts = {'VGROUP_WEIGHTS'}
    dt.vert_mapping = 'POLYINTERP_NEAREST'
    dt.layers_vgroup_select_src = 'ALL'
    dt.layers_vgroup_select_dst = 'NAME'
    # The garment was built in world space; express it in the body's parent space like the body mesh.
    garment.matrix_world = body.matrix_world.copy()
    garment.data.transform(body.matrix_world.inverted())
    garment.parent = body.parent
    garment.matrix_world = body.matrix_world.copy()
    bpy.ops.object.modifier_apply(modifier='Weights')
    if KIND in ('coverup', 'chasuble'):
        smooth_skirt_weights(garment, m['crotch'].z + .02)
    am = garment.modifiers.new('Armature', 'ARMATURE')
    am.object = arm
    print('MEASURE', {k: (list(v) if hasattr(v, 'x') else v) for k, v in m.items()}, 'VERTS', len(mesh.vertices))
    bpy.data.objects.remove(body, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    garment.select_set(True)
    arm.select_set(True)
    bpy.ops.export_scene.fbx(filepath=DST, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             use_armature_deform_only=False, bake_anim=False, mesh_smooth_type='FACE')
    print('WROTE', DST)


if __name__ == '__main__':
    main()
