"""Beach sports props (10/11, Sergio: "para deixar a praia mais viva faça pessoas jogando vôlei, peteca, futebol de
praia, cada um em dias diferentes"). Five models, each its own GLB in D:/Assets/Mare/<slug>/ (UMareBeachSportsWorld
places them on the sand on the day of their sport):
  mare_volley_net    beach volleyball net: two oak posts 9.2 m apart, guy ropes, an 8.5 x 1 m knotted net with white
                     tape on the four sides, top at 2.24 m. Net along X, origin on the sand under its middle.
  mare_volleyball    r 10.5 cm, the classic 18 panels (six groups of three strips) in white, yellow and blue.
  mare_soccer_ball   r 11 cm, truncated icosahedron: black pentagons, white hexagons, stitched seams.
  mare_peteca        Brazilian shuttlecock: stacked leather base, felt band, four feathers. Origin at the base bottom,
                     feathers up (+Z); about 21 cm tall.
  mare_beach_goal    small beach-soccer goal 1.8 x 1.1 x 0.7 m in white tube with a knotted net. Goal line along Y,
                     mouth to +X, origin on the sand at the middle of the goal line.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_beach_sports.py [slug ...]"""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402
from gen_custom_furniture import box, export, finish, lathe, material, mesh_obj, reset, tube  # noqa: E402

OUT = Path('D:/Assets/Mare')


def plain(name, color, rough=.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m


def start(slug):
    reset()
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    return out


def cords(prefix, origin, u_axis, v_axis, nu, nv, mat, r=.0028, skip=lambda i, j: False):
    """A knotted net on a parallelogram: nu+1 cords along v, nv+1 along u (4-sided tubes, real bars: a wireframe modifier
    disappears in the render)."""
    o, u, v = Vector(origin), Vector(u_axis), Vector(v_axis)
    for i in range(nu + 1):
        a = o + u * (i / nu)
        tube(f'{prefix}_v{i}', tuple(a), tuple(a + v), r, mat, 4)
    for j in range(nv + 1):
        a = o + v * (j / nv)
        tube(f'{prefix}_u{j}', tuple(a), tuple(a + u), r, mat, 4)


def volley_net():
    slug = 'mare_volley_net'
    out = start(slug)
    oak = material('Post', 'oak_wood_planks', (.50, .36, .22), rough=.7, out=out)
    tape = material('Tape', 'rough_linen', (.93, .92, .88), rough=.85, out=out)
    cord = material('Cord', 'rough_linen', (.12, .12, .13), rough=.9, out=out)
    rope = material('Rope', 'rough_linen', (.70, .58, .38), rough=.9, out=out)
    steel = plain('Steel', (.55, .56, .57), .35, .9)
    pad = plain('Pad', (.10, .32, .62), .8)
    ant = (plain('AntRed', (.85, .1, .08), .5), plain('AntWhite', (.95, .95, .95), .5))   # one material each: draw calls
    half, top, bottom = 4.25, 2.24, 1.24
    for s in (-1, 1):
        x = s * 4.6
        tube(f'post{s}', (x, 0, -.5), (x, 0, 2.55), .05, oak, 16, uv=.6)
        lathe(f'cap{s}', [(0, 0), (.058, 0), (.058, .02), (.03, .05), (0, .055)], (x, 0, 2.55), oak, 16)
        # padded sleeve where players may run into the post
        tube(f'pad{s}', (x, 0, .25), (x, 0, 1.75), .075, pad, 16, uv=.6)
        # two guy ropes to pegs in the sand, an eye bolt on the post
        for d in (-1, 1):
            tube(f'guy{s}{d}', (x, 0, 2.42), (x + s * 1.25, d * 1.0, .02), .008, rope, 6)
            tube(f'peg{s}{d}', (x + s * 1.2, d * .96, .12), (x + s * 1.3, d * 1.04, -.2), .014, steel, 8)
        tube(f'eye{s}', (x - s * .06, 0, 2.42), (x + s * .07, 0, 2.42), .012, steel, 8)
        # net cables from the post to the tape
        for z in (top - .03, bottom + .03):
            tube(f'cable{s}{z}', (x, 0, z + (.12 if z > 2 else -.05)), (s * half, 0, z), .006, rope, 6)
        box(f'side_tape{s}', (.06, .012, top - bottom), (s * half, 0, (top + bottom) / 2), tape, bevel=.003, uv=.3)
        # antenna above the side tape (red and white bands)
        for k in range(8):
            tube(f'ant{s}{k}', (s * half, 0, top + k * .1), (s * half, 0, top + (k + 1) * .1), .006, ant[k % 2], 6)
    box('top_tape', (2 * half, .014, .075), (0, 0, top - .0375), tape, bevel=.004, uv=.3)
    box('bottom_tape', (2 * half, .012, .05), (0, 0, bottom + .025), tape, bevel=.003, uv=.3)
    cords('net', (-half, 0, bottom + .05), (2 * half, 0, 0), (0, 0, top - bottom - .125), 85, 9, cord)
    export(slug, 'Beach volleyball net with posts and guy ropes')


def sphere_panels(name, radius, panel_of, mats, groove=.0016, n=14):
    """Cube sphere of 6 faces x n x n quads; panel_of(face, u, v) -> (material index, distance to the nearest seam 0..1)."""
    bm = bmesh.new()
    faces = [((1, 0, 0), (0, 1, 0), (0, 0, 1)), ((-1, 0, 0), (0, 0, 1), (0, 1, 0)), ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
             ((0, -1, 0), (1, 0, 0), (0, 0, 1)), ((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (0, 1, 0), (1, 0, 0))]
    cache = {}

    def vert(p, depth):
        key = tuple(round(c, 5) for c in p)
        if key not in cache:
            cache[key] = [bm.verts.new(p), depth]
        else:
            cache[key][1] = min(cache[key][1], depth)
        return cache[key][0]
    quads = []
    for fi, (nrm, ua, va) in enumerate(faces):
        N, U, V = Vector(nrm), Vector(ua), Vector(va)
        for i in range(n):
            for j in range(n):
                corner = []
                for (a, b) in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)):
                    # equal-angle mapping keeps the quads even on the sphere
                    su, sv = math.tan((a / n - .5) * math.pi / 2), math.tan((b / n - .5) * math.pi / 2)
                    p = (N + U * su + V * sv).normalized()
                    _, seam = panel_of(fi, a / n, b / n)
                    corner.append(vert(tuple(p), seam))
                mat_i, _ = panel_of(fi, (i + .5) / n, (j + .5) / n)
                quads.append((corner, mat_i))
    for v, seam in cache.values():
        v.co = v.co * (radius - groove * (1 - min(seam * 6, 1.0)))
    for corner, mat_i in quads:
        try:
            f = bm.faces.new(corner)
            f.material_index = mat_i
            f.smooth = True
        except ValueError:
            pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for loop in f.loops:
            c = loop.vert.co.normalized()
            loop[uv].uv = (.5 + math.atan2(c.y, c.x) / (2 * math.pi), .5 + math.asin(max(-1, min(1, c.z))) / math.pi)
    obj = mesh_obj(name, bm)
    for m in mats:
        obj.data.materials.append(m)
    return obj


def volleyball():
    slug = 'mare_volleyball'
    out = start(slug)
    white = material('White', 'leather_white', (.94, .93, .90), rough=.55, out=out)
    yellow = material('Yellow', 'leather_white', (.95, .78, .12), rough=.55, out=out)
    blue = material('Blue', 'leather_white', (.10, .28, .62), rough=.55, out=out)

    def panel(face, u, v):
        # three strips per cube face, running along u on even faces and along v on odd ones (the classic 18 panels)
        t = u if face % 2 == 0 else v
        strip = min(int(t * 3), 2)
        edge = min(abs(t * 3 - round(t * 3)), 1.0) if 0 < t < 1 else 0.0
        border = min(u, 1 - u, v, 1 - v) * 3
        return (0, 1, 2)[(strip + face // 2) % 3], min(edge, border)
    sphere_panels('ball', .105, panel, [white, yellow, blue])
    export(slug, 'Beach volleyball (18 panels)')


def soccer_ball():
    slug = 'mare_soccer_ball'
    out = start(slug)
    white = material('White', 'leather_white', (.93, .93, .91), rough=.5, out=out)
    black = material('Black', 'leather_white', (.05, .05, .055), rough=.5, out=out)
    seam = plain('Seam', (.16, .15, .14), .8)
    r = .11
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    bm.edges.ensure_lookup_table()
    edge = bm.edges[0].calc_length()
    bmesh.ops.bevel(bm, geom=bm.verts[:], offset=edge / 3, offset_type='OFFSET', segments=1, affect='VERTICES')
    bm.faces.ensure_lookup_table()
    sides = {f: len(f.verts) for f in bm.faces}
    # a seam ring round every panel, then the panel fanned and rounded
    res = bmesh.ops.inset_individual(bm, faces=bm.faces[:], thickness=.022, depth=0.0)
    ring = set(res['faces'])
    inner = [f for f in bm.faces if f not in ring]
    for f in bm.faces:
        f.material_index = 2 if f in ring else (1 if len(f.verts) == 5 else 0)
    poked = bmesh.ops.poke(bm, faces=inner)
    for _ in range(2):
        tri = [f for f in bm.faces if f.material_index != 2]
        bmesh.ops.subdivide_edges(bm, edges=list({e for f in tri for e in f.edges}), cuts=1, use_grid_fill=False)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    seam_verts = {v for f in bm.faces if f.material_index == 2 for v in f.verts}
    for v in bm.verts:
        only_seam = all(f.material_index == 2 for f in v.link_faces)
        v.co = v.co.normalized() * (r - (.0018 if only_seam else 0.0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        f.smooth = True
        for loop in f.loops:
            c = loop.vert.co.normalized()
            loop[uv].uv = (c.x * 2, c.y * 2 + c.z)
    obj = mesh_obj('ball', bm)
    for m in (white, black, seam):
        obj.data.materials.append(m)
    export(slug, 'Soccer ball (32 panels)')


def peteca():
    slug = 'mare_peteca'
    out = start(slug)
    leather = material('Leather', 'brown_leather', None, rough=.6)
    felt = material('Felt', 'rough_linen', (.72, .10, .08), rough=.95, out=out)
    quill = plain('Quill', (.92, .90, .84), .5)
    # base: four stacked leather discs with rounded edges, a felt band, the collar that holds the feathers
    prof = [(0, 0), (.022, 0), (.027, .004), (.027, .007), (.025, .008), (.028, .010), (.028, .014), (.026, .015),
            (.028, .017), (.028, .021), (.026, .022), (.027, .024), (.027, .028), (0, .028)]
    lathe('base', prof, (0, 0, 0), leather, 20, uv=.08)
    lathe('band', [(0, .028), (.024, .028), (.024, .036), (.014, .040), (0, .040)], (0, 0, 0), felt, 20, uv=.08)
    lathe('collar', [(0, .040), (.012, .040), (.011, .058), (0, .058)], (0, 0, 0), leather, 12, uv=.08)
    colors = [(.95, .95, .93), (.85, .12, .10), (.95, .80, .12), (.10, .52, .26)]
    for k, col in enumerate(colors):
        a = k * math.pi / 2 + math.pi / 4
        out_dir = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-math.sin(a), math.cos(a), 0))
        root = Vector((0, 0, .05)) + out_dir * .006
        tip = root + Vector((0, 0, .16)) + out_dir * .045
        tube(f'quill{k}', tuple(root), tuple(tip), .0013, quill, 6)
        mat = plain(f'Feather{k}', col, .7)
        # vane: a leaf-shaped double-sided sheet along the quill, slightly cupped
        bm = bmesh.new()
        rows = 9
        axis = (tip - root)
        prev = None
        for i in range(rows + 1):
            t = i / rows
            w = .019 * math.sin(math.pi * (.12 + .88 * t) ** .8) * (1.0 if t < .92 else .6) + .001
            c = root + axis * (.14 + .86 * t)
            cup = out_dir * (-.004 * math.sin(math.pi * t))
            row = [bm.verts.new(c - side * w + cup), bm.verts.new(c + out_dir * .0012), bm.verts.new(c + side * w + cup)]
            if prev:
                for j in range(2):
                    bm.faces.new((prev[j], prev[j + 1], row[j + 1], row[j]))
            prev = row
        obj = mesh_obj(f'vane{k}', bm)
        finish(obj, mat, .05)
        sol = obj.modifiers.new('Solidify', 'SOLIDIFY')   # a single sheet vanishes seen from behind
        sol.thickness = .0009
        sol.offset = 0
    export(slug, 'Peteca (Brazilian shuttlecock)')


def beach_goal():
    slug = 'mare_beach_goal'
    out = start(slug)
    pvc = material('Frame', 'painted_plaster_wall', (.93, .93, .91), rough=.45, out=out)
    cord = material('Cord', 'rough_linen', (.90, .90, .88), rough=.9, out=out)
    w, h, d, r = .9, 1.1, .7, .028       # half width, height, depth, tube radius
    for s in (-1, 1):
        y = s * w
        tube(f'post{s}', (0, y, -.12), (0, y, h), r, pvc, 14, uv=.5)
        tube(f'floor{s}', (0, y, .02), (-d, y, .02), r, pvc, 14, uv=.5)
        tube(f'stay{s}', (0, y, h), (-d, y, .02), r * .8, pvc, 12, uv=.5)
        lathe(f'elbow{s}', [(0, -.03), (r * 1.25, -.03), (r * 1.25, .03), (0, .03)], (0, y, h), pvc, 14)
        # side net: the triangle between post, floor bar and stay
        for k in range(1, 7):
            t = k / 7
            tube(f'side_v{s}{k}', (-d * t, y, .02), (-d * t, y, h * (1 - t)), .0026, cord, 4)
        for k in range(1, 10):
            z = h * k / 10
            tube(f'side_h{s}{k}', (0, y, z), (-d * (1 - z / h), y, z), .0026, cord, 4)
    tube('bar', (0, -w, h), (0, w, h), r, pvc, 14, uv=.5)
    tube('back', (-d, -w, .02), (-d, w, .02), r, pvc, 14, uv=.5)
    # back net on the slanted plane from the crossbar down to the back bar
    cords('back_net', (0, -w, h), (0, 2 * w, 0), (-d, 0, .02 - h), 18, 11, cord, r=.0026)
    export(slug, 'Small beach soccer goal')


MODELS = {'mare_volley_net': volley_net, 'mare_volleyball': volleyball, 'mare_soccer_ball': soccer_ball,
          'mare_peteca': peteca, 'mare_beach_goal': beach_goal}

if __name__ == '__main__':
    for name in ([a for a in sys.argv[1:] if a in MODELS] or list(MODELS)):
        MODELS[name]()
        print('ok', name)
