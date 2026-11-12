"""Beach boats of Maré Alta (replace the simple jangada/bote of the Godot export): a north-eastern Brazilian
jangada and a planked fishing boat, both detailed. Base at the waterline z=0, bow toward +Y, metres.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_boats.py
Output: D:/Assets/Mare/<slug>/<slug>.glb (mare_jangada, mare_bote)."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector, noise  # noqa: E402
from gen_custom_furniture import box, export, lathe, material, mesh_obj, reset, tube  # noqa: E402


def plain(name, colour, rough=.7, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    return m


def log(name, length, r, loc, mat, bow_lift=.0, sides=16, rings=36):
    """A peeled-bark log along +Y with knots and a slight upturned bow (jangada 'pau')."""
    bm = bmesh.new()
    verts = []
    for i in range(rings + 1):
        t = i / rings
        y = loc[1] + (t - .5) * length
        lift = bow_lift * max(0.0, t - .7) ** 2 / .09
        rr = r * (1 - .25 * max(0.0, t - .85) / .15) * (1 + .04 * noise.noise(Vector((loc[0] * 9, y * 3, 0))))
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            bump = 1 + .035 * noise.noise(Vector((math.cos(a) * 3, y * 6, loc[0] * 5)))
            ring.append(bm.verts.new((loc[0] + rr * bump * math.cos(a), y, loc[2] + lift + rr * bump * math.sin(a))))
        verts.append(ring)
    for a, b in zip(verts, verts[1:]):
        for k in range(sides):
            bm.faces.new((a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]))
    for ring in (verts[0], verts[-1][::-1]):
        bm.faces.new(ring)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm)
    uv = o.data.uv_layers.new(name='UVMap')
    for loop in o.data.loops:
        co = o.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (math.atan2(co.z - loc[2], co.x - loc[0]) / (2 * math.pi), co.y * .8)
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def sail(name, pts, mat, cols=14, rows=20, belly=.18, battens=None, batten_mat=None):
    """Triangular canvas between three points with a wind belly and seams; optional battens across it."""
    a, b, c = (Vector(p) for p in pts)        # a tack (bottom front), b head (top), c clew (bottom back)
    bm = bmesh.new()
    grid = []
    for i in range(rows + 1):
        u = i / rows
        row = []
        for j in range(cols + 1):
            v = j / cols
            p = a.lerp(b, u).lerp(c.lerp(b, u), v)
            # Belly: deepest mid-sail, vanishing at the edges; a few horizontal wrinkles.
            depth = belly * math.sin(math.pi * v) * math.sin(math.pi * min(1.0, u * 1.1 + .05)) * (1 - u) ** .3
            p = p + Vector((depth, 0, 0)) + Vector((.006 * math.sin(u * 40), 0, 0))
            row.append(bm.verts.new(p))
        grid.append(row)
    for i in range(rows):
        for j in range(cols):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    coords = [[v.co.copy() for v in row] for row in grid]   # the bmesh is freed by mesh_obj
    o = mesh_obj(name, bm)
    uv = o.data.uv_layers.new(name='UVMap')
    for loop in o.data.loops:
        co = o.data.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (co.y * .5, co.z * .5)
    sol = o.modifiers.new('Canvas', 'SOLIDIFY')
    sol.thickness = .004
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    if battens:
        for k, u in enumerate(battens):
            p0, p1 = coords[int(u * rows)][0], coords[int(u * rows)][cols]
            tube(f'{name}_batten{k}', tuple(p0 + Vector((.012, 0, 0))), tuple(p1 + Vector((.012, 0, 0))), .008, batten_mat, 6)
    return o


def jangada():
    reset()
    slug = 'mare_jangada'
    out = Path('D:/Assets/Mare') / slug
    out.mkdir(parents=True, exist_ok=True)
    piuba = material('Log', 'bark_brown_02', (.62, .5, .38), rough=.85, out=out)
    wood = material('Wood', 'oak_wood_planks', (.55, .4, .26), rough=.7, out=out)
    canvas = material('Sail', 'rough_linen', (.93, .88, .78), rough=.95, out=out)
    patch = material('Patch', 'rough_linen', (.78, .62, .45), rough=.95, out=out)
    rope = material('Rope', 'rough_linen', (.72, .6, .42), rough=.9, out=out)
    # Six logs, the middle ones longer, lashed by three cross-pegs ('tornos').
    for k, (x, length) in enumerate([(-.39, 5.4), (-.24, 5.9), (-.08, 6.2), (.08, 6.2), (.24, 5.9), (.39, 5.4)]):
        log(f'log{k}', length, .085, (x, 0, .03), piuba, bow_lift=.12)
    for y in (-1.8, 0, 1.6):
        tube(f'torno{y}', (-.5, y, .1), (.5, y, .1), .025, wood, 10)
        for x in (-.39, -.24, -.08, .08, .24, .39):
            lathe(f'lash{y}{x}', [(.0, -.03), (.03, -.025), (.034, 0), (.03, .025), (0, .03)], (x, y, .1), rope, 10)
    # Bench, mast step and raked mast, boom, the big lateen-cut sail with battens, steering oar.
    box('bench', (.9, .32, .04), (0, .6, .42), wood, uv=.8)
    for sx in (-1, 1):
        box(f'bench_leg{sx}', (.05, .3, .3), (sx * .38, .6, .25), wood, uv=.8)
    tube('mast', (0, 1.2, .1), (0, 1.55, 5.6), .055, wood, 14)
    tube('boom', (0, 1.25, .9), (0, -1.9, 1.05), .04, wood, 12)
    sail('sail', [(.0, 1.3, .95), (.0, 1.55, 5.4), (.0, -1.85, 1.08)], canvas, belly=.25, battens=[.25, .45, .62], batten_mat=wood)
    box('patch1', (.01, .5, .4), (.09, .4, 2.0), patch, uv=.5)
    box('patch2', (.01, .35, .3), (.07, .9, 3.2), patch, uv=.5)
    tube('sheet', (0, -1.85, 1.05), (.2, -2.4, .2), .008, rope, 6)
    tube('stay', (0, 1.55, 5.55), (0, 3.0, .15), .007, rope, 6)
    tube('oar', (.1, -2.9, .1), (.3, -1.6, .9), .03, wood, 10)
    box('oar_blade', (.03, .55, .2), (.08, -3.1, .02), wood, rot=(math.radians(-25), 0, 0), uv=.6)
    # Fishing basket (samburá) and a water jug on the deck.
    lathe('basket', [(0, 0), (.16, 0), (.2, .12), (.18, .25), (.12, .3), (0, .3)], (.2, -.6, .12), rope, 20)
    lathe('jug', [(0, 0), (.09, 0), (.11, .1), (.08, .22), (.03, .27), (.035, .32), (0, .32)], (-.22, -.3, .12), wood, 18)
    export(slug, 'Jangada nordestina')


def plank_hull(name, L, W, D, strakes, mat, mat_band, band_strake):
    """Clinker-planked open boat: each strake is a strip lofted from section curves (keel to sheer)."""
    def section(y, t):
        # y along length -L/2..L/2, t 0 (keel) .. 1 (sheer); returns (x, z) for the starboard side.
        u = y / (L / 2)
        width = W / 2 * (1 - abs(u) ** 2.4) ** .55
        rise = .12 * max(0.0, u) ** 2 + .06 * max(0.0, -u) ** 2
        x = width * math.sin(t * math.pi / 2) ** .8
        z = -D + D * t ** 1.3 + rise * t
        return x, z
    parts = []
    nseg = 40
    for s in range(strakes):
        t0, t1 = s / strakes, (s + 1) / strakes + .02         # overlap: clinker lap
        for side in (1, -1):
            bm = bmesh.new()
            rows = []
            for i in range(nseg + 1):
                y = -L / 2 + L * i / nseg
                r = []
                for t in (t0, t1):
                    x, z = section(y, t)
                    r.append(bm.verts.new((side * (x + .006 * (t == t1)), y, z)))
                rows.append(r)
            for a, b in zip(rows, rows[1:]):
                bm.faces.new((a[0], b[0], b[1], a[1]) if side > 0 else (a[0], a[1], b[1], b[0]))
            o = mesh_obj(f'{name}_s{s}{side}', bm)
            o.data.materials.append(mat_band if s == band_strake else mat)
            sol = o.modifiers.new('Plank', 'SOLIDIFY')
            sol.thickness = .018
            uv = o.data.uv_layers.new(name='UVMap')
            for loop in o.data.loops:
                co = o.data.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (co.y * .6, co.z * 2)
            parts.append(o)
    return section


def bote():
    reset()
    slug = 'mare_bote'
    out = Path('D:/Assets/Mare') / slug
    out.mkdir(parents=True, exist_ok=True)
    paint = material('Hull', 'distressed_painted_planks', (.12, .36, .62), rough=.6, out=out)
    band = material('Band', 'distressed_painted_planks', (.86, .2, .16), rough=.6, out=out)
    inside = material('Inside', 'oak_wood_planks', (.6, .45, .3), rough=.7, out=out)
    wood = material('Trim', 'oak_wood_planks', (.48, .33, .2), rough=.6, out=out)
    rope = material('Rope', 'rough_linen', (.72, .6, .42), rough=.9, out=out)
    brass = plain('Brass', (.7, .55, .3), .35, 1.0)
    L, W, D = 4.2, 1.45, .62
    section = plank_hull('hull', L, W, D, 7, paint, band, 5)
    # Keel, stem, transom, ribs, gunwales, thwarts, oars on tholes, a coil of rope and a small anchor.
    tube('keel', (0, -L / 2, -D), (0, L / 2, -D + .1), .035, wood, 8)
    tube('stem', (0, L / 2 - .02, -D + .1), (0, L / 2 + .06, .2), .045, wood, 8)
    tube('sternpost', (0, -L / 2 + .02, -D + .1), (0, -L / 2 - .05, .16), .045, wood, 8)   # double-ended hull
    for i in range(1, 12):
        y = -L / 2 + L * i / 12
        pts = [section(y, t / 8) for t in range(9)]
        for sx in (1, -1):
            for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
                tube(f'rib{i}{sx}{z0:.2f}', (sx * x0 * .97, y, z0 + .02), (sx * x1 * .97, y, z1 + .02), .016, inside, 6)
    for sx in (1, -1):
        rail = [(sx * section(-L / 2 + L * i / 30, 1)[0], -L / 2 + L * i / 30, section(-L / 2 + L * i / 30, 1)[1] + .015) for i in range(31)]
        for p0, p1 in zip(rail, rail[1:]):
            tube(f'gunwale{sx}{p0[1]:.2f}', p0, p1, .03, wood, 8)
    for y, h in ((-.9, -.22), (.2, -.22), (1.2, -.2)):
        w = section(y, 1)[0] * 2 - .08
        box(f'thwart{y}', (w, .26, .035), (0, y, h), wood, uv=.7)
    for sx in (1, -1):
        x, z = section(-.2, 1)
        lathe(f'thole{sx}', [(0, 0), (.015, 0), (.015, .12), (0, .12)], (sx * x, -.2, z + .02), brass, 8)
        # Oars shipped: lying along the boat on the thwarts, blades toward the bow.
        tube(f'oar{sx}', (sx * .2, -1.45, -.18), (sx * .24, .95, -.16), .022, wood, 8)
        box(f'oar_blade{sx}', (.14, .5, .015), (sx * .245, 1.2, -.158), wood, uv=.6)
    lathe('rope_coil', [(.08, 0), (.16, 0), (.17, .03), (.16, .06), (.08, .06), (.07, .03)], (.2, -1.5, -D + .12), rope, 24)
    export(slug, 'Bote de pesca de tábuas')


jangada()
bote()
