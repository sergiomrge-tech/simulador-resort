"""Detailed replacements for two simple exported props, modelled with bpy.

- mare_lighthouse: 17.4 m tower (same footprint/height as World_2020), lantern room glazed around the
  fresnel lens that sits 14.45-15.25 m above the base, gallery with railing, copper dome.
- mare_stall_souvenir / mare_stall_plain: 2.8 x 2.3 m market stall (same footprint as World_2363/2409)
  with counters on both long sides, shelves of souvenirs, clay-tile hip roof and striped valance.
Base at z=0, centred. Textures: CC0 Poly Haven photo scans (tinted copies baked next to the model).
Run: blender -b --factory-startup --python tools/ue58/gen_landmarks.py -- [slug ...]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402  (bpy before bmesh, as in the furniture generator)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402
from gen_custom_furniture import OUT, box, cushion, export, finish, lathe, material, mesh_obj, reset, tube  # noqa: E402


def ring(name, radius, z, r, mat, sides=48):
    """Torus-like moulding ring made with the lathe (small half-round profile)."""
    prof = [(radius, z - r), (radius + r * .7, z - r * .7), (radius + r, z), (radius + r * .7, z + r * .7), (radius, z + r)]
    return lathe(name, prof, (0, 0, 0), mat, sides)


def lighthouse():
    reset()
    slug = 'mare_lighthouse'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    white = material('White', 'painted_plaster_wall', (.93, .92, .88), rough=.8, out=out)
    red = material('Red', 'painted_plaster_wall', (.70, .15, .13), rough=.75, out=out)
    stone = material('Stone', 'plaster_stone_wall_01', None, rough=.9)
    metal = material('Metal', 'metal_plate', (.16, .17, .18), rough=.45, out=out)
    copper = material('Copper', 'metal_plate', (.22, .36, .30), rough=.5, out=out)
    door = material('Door', 'distressed_painted_planks', (.14, .36, .30), rough=.7, out=out)
    glass = bpy.data.materials.new('Glass')
    glass.use_nodes = True
    g = glass.node_tree.nodes['Principled BSDF']
    g.inputs['Base Color'].default_value = (.75, .85, .88, 1)
    g.inputs['Roughness'].default_value = .05
    g.inputs['Alpha'].default_value = .22
    glass.blend_method = 'BLEND' if hasattr(glass, 'blend_method') else glass.blend_method

    # Octagonal stone plinth with three steps at the door (+Y).
    lathe('plinth', [(0, 0), (2.45, 0), (2.45, .55), (2.2, .62), (0, .62)], (0, 0, 0), stone, 8)
    for i in range(3):
        box(f'step{i}', (1.3, .32, .2), (0, 2.45 + .32 * (2 - i) + .16 - .3, .1 + .2 * i - .1 * 0), stone, uv=1.2)
    # Tapered tower in five bands, moulding rings between them.
    z0, z1, r0, r1 = .62, 14.05, 1.95, 1.42
    bands = 5
    for i in range(bands):
        za, zb = z0 + (z1 - z0) * i / bands, z0 + (z1 - z0) * (i + 1) / bands
        ra, rb = r0 + (r1 - r0) * i / bands, r0 + (r1 - r0) * (i + 1) / bands
        lathe(f'band{i}', [(0, za), (ra, za), (rb, zb), (0, zb)], (0, 0, 0), red if i % 2 else white, 48)
        if i:
            ring(f'mould{i}', ra, za, .05, white, 48)
    # Arched door with frame, small framed windows climbing the tower.
    box('doorframe', (1.15, .22, 2.25), (0, r0 - .02, z0 + 1.1), white, uv=1)
    box('door', (.9, .12, 2.0), (0, r0 + .06, z0 + 1.0), door, uv=.8)
    lathe('doorarch', [(0, -.06), (.45, -.06), (.45, .06), (0, .06)], (0, 0, 0), white, 24)
    arch = bpy.context.collection.objects['doorarch']
    arch.rotation_euler = (math.pi / 2, 0, 0)
    arch.location = (0, r0 + .1, z0 + 2.0)
    for i, (z, a) in enumerate([(4.2, 30), (7.4, 150), (10.6, 270)]):
        t = (z - z0) / (z1 - z0)
        r = r0 + (r1 - r0) * t
        ang = math.radians(a)
        x, y = math.cos(ang) * r, math.sin(ang) * r
        box(f'win{i}', (.55, .5, .8), (x * 1.0, y * 1.0, z), white, rot=(0, 0, ang), uv=1)
        box(f'glass{i}', (.38, .52, .6), (x * 1.01, y * 1.01, z), metal, rot=(0, 0, ang), uv=1)
    # Gallery deck on corbels, railing posts and two rails.
    lathe('deck', [(0, 14.0), (2.3, 14.0), (2.35, 14.1), (2.3, 14.22), (0, 14.22)], (0, 0, 0), white, 48)
    for i in range(16):
        a = 2 * math.pi * i / 16
        box(f'corbel{i}', (.75, .16, .35), (math.cos(a) * 1.75, math.sin(a) * 1.75, 13.82), white, rot=(0, 0, a), uv=1)
    posts = 24
    pts = [(math.cos(2 * math.pi * i / posts) * 2.2, math.sin(2 * math.pi * i / posts) * 2.2) for i in range(posts)]
    for i, (x, y) in enumerate(pts):
        tube(f'post{i}', (x, y, 14.22), (x, y, 15.25), .028, metal, 8)
    for h in (14.7, 15.22):
        for i in range(posts):
            a, b = pts[i], pts[(i + 1) % posts]
            tube(f'rail{h}_{i}', (a[0], a[1], h), (b[0], b[1], h), .03, metal, 8)
    # Lantern room: red base wall, mullions, glazing around the lens (14.45-15.25 m), cornice.
    lathe('lanternwall', [(0, 14.22), (1.32, 14.22), (1.32, 14.62), (0, 14.62)], (0, 0, 0), red, 32)
    for i in range(10):
        a = 2 * math.pi * i / 10
        tube(f'mullion{i}', (math.cos(a) * 1.28, math.sin(a) * 1.28, 14.62), (math.cos(a) * 1.28, math.sin(a) * 1.28, 15.95), .035, metal, 8)
    glazing = lathe('glazing', [(1.25, 14.62), (1.25, 15.95)], (0, 0, 0), glass, 40)
    glazing.data.materials.clear()
    glazing.data.materials.append(glass)
    lathe('cornice', [(0, 15.92), (1.5, 15.92), (1.55, 16.0), (1.45, 16.08), (0, 16.08)], (0, 0, 0), metal, 40)
    # Copper dome with a ventilator ball and lightning rod (top at 17.4 m).
    dome = [(1.45, 16.08)] + [(1.45 * math.cos(t * math.pi / 2), 16.08 + .95 * math.sin(t * math.pi / 2)) for t in [i / 10 for i in range(1, 11)]]
    lathe('dome', dome, (0, 0, 0), copper, 40)
    lathe('vent', [(0, 16.98), (.1, 17.0), (.2, 17.1), (.22, 17.18), (.2, 17.26), (.1, 17.32), (0, 17.34)], (0, 0, 0), copper, 20)
    tube('rod', (0, 0, 17.3), (0, 0, 17.4), .015, metal, 6)
    export(slug, 'Farol detalhado')


def hip_roof(name, w, d, z, rise, overhang, mat):
    """Four-sided roof: rectangle eaves rising to a short ridge along X."""
    bm = bmesh.new()
    hw, hd = w / 2 + overhang, d / 2 + overhang
    ridge = max(.05, hw - hd)
    e = [bm.verts.new(v) for v in [(-hw, -hd, z), (hw, -hd, z), (hw, hd, z), (-hw, hd, z)]]
    r = [bm.verts.new(v) for v in [(-ridge, 0, z + rise), (ridge, 0, z + rise)]]
    bm.faces.new((e[0], e[1], r[1], r[0]))
    bm.faces.new((e[1], e[2], r[1]))
    bm.faces.new((e[2], e[3], r[0], r[1]))
    bm.faces.new((e[3], e[0], r[0]))
    obj = mesh_obj(name, bm)
    finish(obj, mat, 1.0, smooth=False)
    sol = obj.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = .05
    return obj


def stall(slug, sign, pastel=False):
    reset()
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    wood = material('Wood', 'oak_wood_planks', None, rough=.6)
    # 10/11 pastel stall (replaces the village food truck): the truck's warm red on the plank fronts.
    teal = material('Teal', 'distressed_painted_planks', (.72, .20, .14) if pastel else (.12, .52, .50), rough=.7, out=out)
    cream = material('Cream', 'distressed_painted_planks', (.92, .86, .72), rough=.7, out=out)
    roof = material('Roof', 'clay_roof_tiles_02', None, rough=.75)
    coral = material('Coral', 'rough_linen', (.90, .38, .30), rough=.9, out=out)
    sand = material('Sand', 'rough_linen', (.95, .90, .80), rough=.9, out=out)
    W, D = 2.8, 2.28
    box('deck', (W + .1, D + .1, .12), (0, 0, .06), wood, uv=1.2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f'post{sx}{sy}', (.11, .11, 2.35), (sx * (W / 2 - .06), sy * (D / 2 - .06), 1.29), cream, uv=1)
    # Counters on both long sides (the stall is used from either side), plank fronts and thick tops.
    for sy in (-1, 1):
        box(f'counter{sy}', (W - .22, .42, .9), (0, sy * (D / 2 - .27), .57), teal, uv=.9)
        box(f'top{sy}', (W - .1, .56, .06), (0, sy * (D / 2 - .24), 1.05), wood, uv=1.2)
    # Short sides: louvred panels.
    for sx in (-1, 1):
        for i in range(9):
            box(f'louvre{sx}_{i}', (.03, D - .24, .14), (sx * (W / 2 - .06), 0, .3 + i * .21), cream, rot=(math.radians(25), 0, 0), uv=1)
    if pastel:
        # A frying station instead of the souvenir shelves: a tiled worktop between the two counters, a glass-fronted
        # warmer with rows of fried pasteis (half-moons with a crimped edge), oil and sauce bottles on a high shelf.
        steel = material('Steel', 'rough_linen', (.74, .75, .76), rough=.35, out=out)
        dough = material('Dough', 'rough_linen', (.86, .62, .30), rough=.8, out=out)
        box('worktop', (W - .5, .62, .05), (0, 0, 1.0), steel, uv=1)
        for sx in (-1, 1):
            box(f'workleg{sx}', (.05, .58, .88), (sx * (W / 2 - .32), 0, .56), steel, uv=1)
        # warmer: steel base, four slim posts, a steel top; the pasteis lie on two tilted trays inside
        box('warmer_base', (1.1, .5, .06), (-.55, 0, 1.06), steel, uv=1)
        box('warmer_top', (1.1, .5, .04), (-.55, 0, 1.52), steel, uv=1)
        for sx in (-1, 1):
            for sy in (-1, 1):
                box(f'warmer_post{sx}{sy}', (.03, .03, .44), (-.55 + sx * .53, sy * .23, 1.3), steel, uv=1)
        for k, z in enumerate((1.14, 1.32)):
            box(f'tray{k}', (1.0, .4, .02), (-.55, 0, z), steel, rot=(math.radians(10), 0, 0), uv=1)
            for i in range(5):
                x = -.95 + i * .2
                # half-moon: a flattened disc cut by the tray, with a raised crimped rim
                lathe(f'pastel{k}{i}', [(0, 0), (.085, 0), (.095, .012), (.085, .028), (.03, .036), (0, .036)], (x, .02, z + .03), dough, 14)
        # fryer vat place: a round stand on the worktop (the Poly Haven brass pan sits on it in the level)
        lathe('burner', [(0, 0), (.17, 0), (.17, .05), (.13, .07), (0, .07)], (.65, 0, 1.025), steel, 20)
        box('shelf_hi', (W - .5, .26, .04), (0, 0, 1.9), wood, uv=1)
        for i in range(6):
            x = -.95 + i * .38
            lathe(f'bottle{i}', [(0, 0), (.04, 0), (.045, .04), (.045, .17), (.018, .22), (.018, .27), (0, .27)], (x, 0, 1.92), [coral, sand, dough][i % 3], 14)
    # Back shelves in the middle with souvenirs: jars, shells, folded shirts, tiny boats.
    for k, z in enumerate(() if pastel else (1.35, 1.75)):
        box(f'shelf{k}', (W - .5, .3, .04), (0, 0, z), wood, uv=1)
        for i in range(7):
            x = -1.05 + i * .35
            kind = (i + k) % 3
            colour = [teal, coral, cream][(i + 2 * k) % 3]
            if kind == 0:
                lathe(f'jar{k}{i}', [(0, 0), (.06, 0), (.07, .05), (.05, .14), (.04, .16), (0, .16)], (x, 0, z + .02), colour, 16)
            elif kind == 1:
                cushion(f'shirt{k}{i}', (.24, .2, .05), (x, 0, z + .045), colour, puff=.01)
            else:
                box(f'boat{k}{i}', (.22, .07, .06), (x, 0, z + .05), colour, uv=.4)
                tube(f'mast{k}{i}', (x, 0, z + .08), (x, 0, z + .22), .006, wood, 6)
    tube('rod', (-(W / 2 - .1), 0, 2.2), ((W / 2 - .1), 0, 2.2), .02, wood, 8)
    for i in range(0 if pastel else 8):
        x = -1.15 + i * .33
        cushion(f'hang{i}', (.18, .02, .26), (x, 0, 2.02), [coral, sand, teal][i % 3], puff=.006)
    # Hip roof with clay tiles, fascia and a striped scalloped valance along both long eaves.
    hip_roof('roof', W, D, 2.47, .72, .35, roof)
    for sy in (-1, 1):
        box(f'fascia{sy}', (W + .76, .04, .14), (0, sy * (D / 2 + .35), 2.42), cream, uv=1)
        for i in range(12):
            x = -(W / 2 + .3) + (i + .5) * (W + .6) / 12
            cushion(f'valance{sy}_{i}', ((W + .6) / 12 - .01, .015, .2), (x, sy * (D / 2 + .37), 2.26), coral if i % 2 else sand, puff=.004)
    for sx in (-1, 1):
        box(f'fasciaX{sx}', (.04, D + .76, .14), (sx * (W / 2 + .35), 0, 2.42), cream, uv=1)
    if pastel:
        # Sign boards over both long eaves, in the red of the counters: the name is a game text (white, translated) put
        # on them in the level, not baked into the mesh.
        for sy in (-1, 1):
            box(f'signboard{sy}', (2.1, .06, .42), (0, sy * (D / 2 + .32), 2.98), teal, uv=1)
            for post in (-.85, .85):
                tube(f'signpost{sy}{post}', (post, sy * (D / 2 + .32), 2.55), (post, sy * (D / 2 + .32), 2.8), .02, wood, 8)
    if sign:
        box('signboard', (1.7, .06, .38), (0, -(D / 2 + .32), 2.98), cream, uv=1)
        bpy.ops.object.text_add(location=(0, -(D / 2 + .36), 2.98), rotation=(math.pi / 2, 0, 0))
        txt = bpy.context.active_object
        txt.data.body = 'LEMBRANCINHAS'
        txt.data.align_x = 'CENTER'
        txt.data.align_y = 'CENTER'
        txt.data.size = .2
        txt.data.extrude = .01
        bpy.ops.object.convert(target='MESH')
        txt.data.materials.append(teal)
        for post in (-.7, .7):
            tube(f'signpost{post}', (post, -(D / 2 + .32), 2.6), (post, -(D / 2 + .32), 2.8), .02, wood, 8)
    export(slug, 'Barraca do pastel' if pastel else 'Barraca de lembrancinhas' if sign else 'Barraca de madeira')


BUILD = {
    'mare_lighthouse': lighthouse,
    'mare_stall_souvenir': lambda: stall('mare_stall_souvenir', True),
    'mare_stall_plain': lambda: stall('mare_stall_plain', False),
    'mare_stall_pastel': lambda: stall('mare_stall_pastel', False, True),
}

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for slug in args or BUILD:
        BUILD[slug]()
        print('built', slug)
