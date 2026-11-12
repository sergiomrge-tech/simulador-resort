"""Grand Hotel guest floor (5.1): corridor, standard room, luxury room and linen room next to the suite, modelled with bpy.

The tower's 3rd storey is hollow (traces 06/11: x -3670..-530, y 5765..6920, floor 851, ceiling 1159). The suite
(gen_suite.py) fills the west 17 m; this block fills the east 14.1 m, x -1942..-530.
Local frame = UE world axes in metres (Blender y = -UE y), origin at UE (-1236, 6342, 851) on the floor slab.
South (UE -Y) is the facade with the balcony doors every 4 m (doors at world x -1987..-1742, -1587..-1342,
-1187..-942, -787..-542): each gets a daylight panel ('DaylightPanel', replaced in UE by the night-aware glow) behind
sheer curtains and side drapes, as in the suite. North: corridor 2 m wide with the elevator door.
  linen room  x -7.06..-4.28   (shelves, housekeeping cart)
  standard    x -4.28..-0.28   (bath in the north-west corner, entry hall with wardrobe, queen bed on the west wall)
  luxury      x -0.28..+7.06   (bath with tub in the north-east, hall with wardrobe, king bed facing the sea)
Beds, TVs, the air conditioner, nightstands, chairs and plants are library models placed by
Content/Python/mare_hotel_rooms.py; this mesh holds the architecture, bathrooms, wardrobes, consoles and minibars.
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_hotel_rooms.py
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from gen_custom_furniture import OUT, box, cushion, drape, export, lathe, material, mesh_obj, reset, tube  # noqa: E402

ART = Path('D:/Assets/Canva/beach_art/beach_watercolor.png')
X0, X1 = -7.06, 7.06          # west (suite partition face) .. east (tower wall)
YS, YC, YN = -5.77, 3.78, 5.78  # facade .. corridor south wall .. tower north wall
H = 3.06                      # walls up to the tower ceiling (1159 - 851 = 3.08)
DOOR_H = 2.15
T = .12                       # partition thickness
XL, XS = -4.28, -0.28         # linen | standard, standard | luxury


def B(x, y, z=0.0):
    """UE-axis metres -> Blender coordinates (y flipped)."""
    return (x, -y, z)


def disc(name, r, h, at, rot, mat, sides=16):
    """Flat round piece (button, wheel, mixer plate) built at the origin, then rotated and moved (lathe bakes its location)."""
    o = lathe(name, [(0, 0), (r, 0), (r, h), (0, h)], (0, 0, 0), mat, sides)
    o.rotation_euler = rot
    o.location = at
    return o


def wall_x(name, y, x0, x1, mat, openings=(), uv=1.5, h=H, t=T):
    """Wall along X at y from x0 to x1 with door openings [(centre x, width)] and a lintel above each."""
    cuts = sorted(openings)
    edges = [x0]
    for cx, w in cuts:
        edges += [cx - w / 2, cx + w / 2]
    edges.append(x1)
    for i in range(0, len(edges), 2):
        a, b = edges[i], edges[i + 1]
        if b - a > .01:
            box(f'{name}_s{i}', (b - a, t, h), B((a + b) / 2, y, h / 2), mat, uv=uv)
    for k, (cx, w) in enumerate(cuts):
        box(f'{name}_l{k}', (w, t, h - DOOR_H), B(cx, y, (h + DOOR_H) / 2), mat, uv=uv)


def wall_y(name, x, y0, y1, mat, openings=(), uv=1.5, h=H, t=T):
    """Wall along Y at x from y0 to y1 with door openings [(centre y, width)]."""
    cuts = sorted(openings)
    edges = [y0]
    for cy, w in cuts:
        edges += [cy - w / 2, cy + w / 2]
    edges.append(y1)
    for i in range(0, len(edges), 2):
        a, b = edges[i], edges[i + 1]
        if b - a > .01:
            box(f'{name}_s{i}', (t, b - a, h), B(x, (a + b) / 2, h / 2), mat, uv=uv)
    for k, (cy, w) in enumerate(cuts):
        box(f'{name}_l{k}', (t, w, h - DOOR_H), B(x, cy, (h + DOOR_H) / 2), mat, uv=uv)


def casing(name, cx, cy, along_x, w, wood, depth=T + .04):
    """Door casing (two jambs and a head) around an opening in a wall along X (along_x) or along Y."""
    if along_x:
        for sx in (-1, 1):
            box(f'{name}_j{sx}', (.07, depth, DOOR_H + .05), B(cx + sx * (w / 2 + .035), cy, (DOOR_H + .05) / 2), wood, uv=.6)
        box(f'{name}_h', (w + .14, depth, .08), B(cx, cy, DOOR_H + .04), wood, uv=.6)
    else:
        for sy in (-1, 1):
            box(f'{name}_j{sy}', (depth, .07, DOOR_H + .05), B(cx, cy + sy * (w / 2 + .035), (DOOR_H + .05) / 2), wood, uv=.6)
        box(f'{name}_h', (depth, w + .14, .08), B(cx, cy, DOOR_H + .04), wood, uv=.6)


def door_leaf(name, hinge, w, open_dir, wood, metal):
    """Door standing open at 90 degrees against the wall: hinge (x, y), leaf running along open_dir (dx, dy) unit."""
    hx, hy = hinge
    dx, dy = open_dir
    cx, cy = hx + dx * w / 2, hy + dy * w / 2
    size = (w, .045, DOOR_H - .02) if abs(dx) > .5 else (.045, w, DOOR_H - .02)
    box(f'{name}', size, B(cx, cy, DOOR_H / 2), wood, uv=.7)
    # Lever handle near the free edge, both faces.
    fx, fy = hx + dx * (w - .08), hy + dy * (w - .08)
    for s in (-1, 1):
        off = (0, s * .05) if abs(dx) > .5 else (s * .05, 0)
        tube(f'{name}_h{s}', B(fx + off[0], fy + off[1], 1.02), B(fx + off[0] - dx * .12, fy + off[1] - dy * .12, 1.02), .01, metal, 8)


def skirting(name, segs, wood):
    """Skirting boards: [(x0, y0, x1, y1)] along the walls (inner faces)."""
    for k, (x0, y0, x1, y1) in enumerate(segs):
        if abs(y1 - y0) < 1e-3:
            box(f'{name}{k}', (abs(x1 - x0), .02, .09), B((x0 + x1) / 2, y0, .045), wood, uv=.6)
        else:
            box(f'{name}{k}', (.02, abs(y1 - y0), .09), B(x0, (y0 + y1) / 2, .045), wood, uv=.6)


def window(name, x, w, sheer, drapes, teak, metal, daylight, plaster, closed=.0):
    """Facade balcony door seen from inside: daylight panel, frame, mullion, rod, sheer and two side drapes."""
    y = YS
    box(f'{name}_day', (w, .02, 2.3), B(x, y + .04, 1.3), plaster, uv=1).data.materials[0] = daylight
    box(f'{name}_head', (w + .16, .1, .1), B(x, y + .08, 2.5), teak, uv=.6)
    box(f'{name}_sill', (w + .2, .14, .04), B(x, y + .09, .17), teak, uv=.6)
    for sx in (-1, 1):
        box(f'{name}_jamb{sx}', (.08, .1, 2.36), B(x + sx * (w / 2 + .04), y + .08, 1.33), teak, uv=.6)
    box(f'{name}_mull', (.05, .06, 2.3), B(x, y + .07, 1.3), teak, uv=.6)
    box(f'{name}_rail', (w, .05, .05), B(x, y + .07, 1.05), teak, uv=.6)
    tube(f'{name}_rod', B(x - w / 2 - .4, y + .28, 2.78), B(x + w / 2 + .4, y + .28, 2.78), .014, metal, 8)
    drape(f'{name}_sheer', w * (.55 + .4 * closed), 2.62, B(x - w * .2 * (1 - closed), y + .24, 2.75), 0, sheer, folds=int(w * 5), amp=.03)
    for sx in (-1, 1):
        drape(f'{name}_drape{sx}', .5, 2.64, B(x + sx * (w / 2 + .22), y + .33, 2.75), 0, drapes, folds=4, amp=.05)


def ceiling(name, x0, x1, y0, y1, mat):
    box(name, (x1 - x0, y1 - y0, .02), B((x0 + x1) / 2, (y0 + y1) / 2, H - .03), mat, uv=1.5)


def toilet(name, x, y, facing, porcelain, metal):
    """Floor-standing toilet: bowl (lathe, oval), seat, cistern against the wall behind; facing = (dx, dy)."""
    dx, dy = facing
    yaw = math.atan2(dy, dx)
    bowl = lathe(f'{name}_bowl', [(0, 0), (.13, 0), (.15, .05), (.16, .2), (.2, .36), (.21, .4), (.17, .41), (.14, .3), (0, .26)], (0, 0, 0), porcelain, 32)
    bowl.scale = (1.0, .78, 1.0)
    bowl.rotation_euler = (0, 0, -yaw + math.pi / 2)
    bowl.location = B(x + dx * .3, y + dy * .3, 0)
    seat = lathe(f'{name}_seat', [(.13, 0), (.2, 0), (.21, .02), (.13, .02)], (0, 0, 0), porcelain, 32)
    seat.scale = (1.0, .8, 1.0)
    seat.rotation_euler = (0, 0, -yaw + math.pi / 2)
    seat.location = B(x + dx * .3, y + dy * .3, .41)
    size = (.2, .42, .4) if abs(dx) > .5 else (.42, .2, .4)
    box(f'{name}_tank', size, B(x + dx * .06, y + dy * .06, .62), porcelain, uv=.5)
    box(f'{name}_lid', (size[0] + .02, size[1] + .02, .03), B(x + dx * .06, y + dy * .06, .835), porcelain, uv=.5)
    lathe(f'{name}_flush', [(0, 0), (.025, 0), (.025, .012), (0, .012)], B(x + dx * .06, y + dy * .06, .85), metal, 16)


def vanity(name, x, y, length, along_x, wood, stone, porcelain, metal, glass, basins=1, mirror=True):
    """Wall vanity: cabinet, stone top, basin(s) with tap, mirror; along_x = against a wall along X (front faces -y)."""
    depth = .5
    if along_x:
        box(f'{name}_cab', (length, depth, .78), B(x, y, .39), wood, uv=.7)
        box(f'{name}_top', (length + .04, depth + .04, .04), B(x, y, .8), stone, uv=.6)
        xs = [x + (k - (basins - 1) / 2) * length / basins for k in range(basins)]
        for k, bx in enumerate(xs):
            lathe(f'{name}_basin{k}', [(0, 0), (.17, 0), (.2, .03), (.19, .13), (.16, .14), (.03, .02), (0, .02)], B(bx, y - .02, .82), porcelain, 28)
            tube(f'{name}_tap{k}', B(bx, y + .2, .82), B(bx, y + .2, 1.06), .014, metal, 8)
            tube(f'{name}_spout{k}', B(bx, y + .2, 1.06), B(bx, y + .07, 1.06), .011, metal, 8)
        if mirror:
            box(f'{name}_mirror', (length - .1, .02, 1.0), B(x, y + depth / 2 - .02, 1.65), glass, uv=1)
            box(f'{name}_mframe', (length - .04, .03, 1.06), B(x, y + depth / 2 - .005, 1.65), wood, uv=.6)
    else:
        box(f'{name}_cab', (depth, length, .78), B(x, y, .39), wood, uv=.7)
        box(f'{name}_top', (depth + .04, length + .04, .04), B(x, y, .8), stone, uv=.6)
        ys = [y + (k - (basins - 1) / 2) * length / basins for k in range(basins)]
        for k, by in enumerate(ys):
            lathe(f'{name}_basin{k}', [(0, 0), (.17, 0), (.2, .03), (.19, .13), (.16, .14), (.03, .02), (0, .02)], B(x - .02, by, .82), porcelain, 28)
            tube(f'{name}_tap{k}', B(x + .2, by, .82), B(x + .2, by, 1.06), .014, metal, 8)
            tube(f'{name}_spout{k}', B(x + .2, by, 1.06), B(x + .07, by, 1.06), .011, metal, 8)
        if mirror:
            box(f'{name}_mirror', (.02, length - .1, 1.0), B(x + depth / 2 - .02, y, 1.65), glass, uv=1)
            box(f'{name}_mframe', (.03, length - .04, 1.06), B(x + depth / 2 - .005, y, 1.65), wood, uv=.6)


def shower(name, x0, x1, y0, y1, glass_sides, stone, glass, metal, head_at):
    """Shower corner: tray, glass panels on the given sides ('x0', 'x1', 'y0', 'y1'), rain head on a wall arm."""
    box(f'{name}_tray', (x1 - x0, y1 - y0, .05), B((x0 + x1) / 2, (y0 + y1) / 2, .025), stone, uv=.6)
    for side in glass_sides:
        if side in ('x0', 'x1'):
            gx = x0 if side == 'x0' else x1
            box(f'{name}_g{side}', (.02, y1 - y0, 2.05), B(gx, (y0 + y1) / 2, 1.08), glass, uv=1)
            box(f'{name}_f{side}', (.03, y1 - y0, .03), B(gx, (y0 + y1) / 2, 2.12), metal, uv=.5)
        else:
            gy = y0 if side == 'y0' else y1
            box(f'{name}_g{side}', (x1 - x0, .02, 2.05), B((x0 + x1) / 2, gy, 1.08), glass, uv=1)
            box(f'{name}_f{side}', (x1 - x0, .03, .03), B((x0 + x1) / 2, gy, 2.12), metal, uv=.5)
    hx, hy, wx, wy = head_at   # head centre and its wall point
    tube(f'{name}_pipe', B(wx, wy, 1.0), B(wx, wy, 2.2), .013, metal, 8)
    tube(f'{name}_arm', B(wx, wy, 2.2), B(hx, hy, 2.2), .013, metal, 8)
    lathe(f'{name}_head', [(0, 0), (.13, 0), (.13, .015), (0, .02)], B(hx, hy, 2.17), metal, 24)
    disc(f'{name}_mixer', .04, .03, B(wx, wy, 1.1), (math.pi / 2, 0, 0), metal)


def folded(name, x, y, z, n, mat, size=(.34, .26, .05)):
    """A stack of folded towels / linen."""
    for i in range(n):
        cushion(f'{name}{i}', size, B(x, y, z + size[2] / 2 + i * (size[2] + .004)), mat, puff=.008)


def console_minibar(name, x, y, length, along_y, front, wood, stone, dark, metal):
    """Low TV console with a built-in minibar fridge at one end (glossy dark door with a steel handle).
    along_y: the console runs along Y against a wall along Y; front = +1 / -1 on X (or Y) where it faces."""
    depth, high = .5, .62
    if along_y:
        box(f'{name}_body', (depth, length, high), B(x, y, high / 2 + .08), wood, uv=.7)
        box(f'{name}_top', (depth + .02, length + .02, .03), B(x, y, high + .095), stone, uv=.6)
        for sy in (-1, 1):
            box(f'{name}_leg{sy}', (depth - .06, .05, .08), B(x, y + sy * (length / 2 - .08), .04), dark, uv=.5)
        fx = x + front * (depth / 2 + .004)
        my = y - length / 2 + .3
        box(f'{name}_fridge', (.012, .5, .52), B(fx, my, .36), dark, uv=.5)
        tube(f'{name}_handle', B(fx + front * .025, my + .17, .2), B(fx + front * .025, my + .17, .5), .009, metal, 8)
        for k in range(2):
            box(f'{name}_drawer{k}', (.012, (length - .7) / 2 - .02, .5), B(fx, y + .1 + (k - .5) * ((length - .7) / 2), .36), wood, uv=.6)
    else:
        box(f'{name}_body', (length, depth, high), B(x, y, high / 2 + .08), wood, uv=.7)
        box(f'{name}_top', (length + .02, depth + .02, .03), B(x, y, high + .095), stone, uv=.6)
        fy = y + front * (depth / 2 + .004)
        mx = x - length / 2 + .3
        box(f'{name}_fridge', (.5, .012, .52), B(mx, fy, .36), dark, uv=.5)
        tube(f'{name}_handle', B(mx + .17, fy + front * .025, .2), B(mx + .17, fy + front * .025, .5), .009, metal, 8)


def wardrobe(name, x, y, length, along_y, front, wood, metal):
    """Built-in wardrobe with four doors and slim steel pulls."""
    depth, high = .6, 2.45
    if along_y:
        box(f'{name}_body', (depth, length, high), B(x, y, high / 2), wood, uv=.8)
        n = max(2, round(length / .55))
        for k in range(1, n):
            box(f'{name}_seam{k}', (depth + .004, .01, high - .1), B(x, y - length / 2 + k * length / n, high / 2), metal, uv=.4)
        for k in range(n):
            cy = y - length / 2 + (k + .5) * length / n + (.18 if k % 2 == 0 else -.18) * length / n
            tube(f'{name}_pull{k}', B(x + front * (depth / 2 + .02), cy, 1.0), B(x + front * (depth / 2 + .02), cy, 1.35), .008, metal, 8)
    else:
        box(f'{name}_body', (length, depth, high), B(x, y, high / 2), wood, uv=.8)
        n = max(2, round(length / .55))
        for k in range(1, n):
            box(f'{name}_seam{k}', (.01, depth + .004, high - .1), B(x - length / 2 + k * length / n, y, high / 2), metal, uv=.4)


def cart(name, x, y, linen, towel, metal, bag):
    """Housekeeping cart: steel frame with three shelves of towels and linen, laundry bag and trash bag at the ends."""
    L, W = 1.2, .5
    for sx in (-1, 1):
        for sy in (-1, 1):
            tube(f'{name}_post{sx}{sy}', B(x + sx * L / 2, y + sy * W / 2, .1), B(x + sx * L / 2, y + sy * W / 2, 1.1), .013, metal, 8)
            disc(f'{name}_wheel{sx}{sy}', .05, .04, B(x + sx * L / 2, y + sy * W / 2 - .02, .05), (math.pi / 2, 0, 0), metal, 12)
    for k, z in enumerate((.15, .55, .95)):
        box(f'{name}_shelf{k}', (L, W, .02), B(x, y, z), metal, uv=.5)
    folded(f'{name}_tow', x - .3, y, .56, 5, towel)
    folded(f'{name}_lin', x + .25, y, .56, 4, linen, (.4, .3, .06))
    folded(f'{name}_tow2', x - .25, y, .96, 3, towel)
    folded(f'{name}_lin2', x + .3, y, .16, 3, linen, (.4, .3, .06))
    cushion(f'{name}_bag', (.4, .45, .7), B(x - L / 2 - .22, y, .48), bag, puff=.04)
    tube(f'{name}_bagring', B(x - L / 2 - .42, y, .85), B(x - L / 2 - .02, y, .85), .01, metal, 8)


def rooms():
    reset()
    slug = 'mare_hotel_rooms'
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    plaster = material('Plaster', 'painted_plaster_wall', (.95, .93, .88), rough=.85, out=out)
    sandwall = material('SandWall', 'painted_plaster_wall', (.90, .84, .74), rough=.85, out=out)
    carpet = material('Carpet', 'poly_wool_herringbone', (.20, .34, .38), rough=.95, out=out)
    parquet = material('Parquet', 'herringbone_parquet', None, rough=.4)
    marble = material('Marble', 'marble_01', None, rough=.15)
    tiles = material('Tiles', 'long_white_tiles', None, rough=.2)
    teak = material('Teak', 'oak_wood_planks', (.55, .38, .24), rough=.45, out=out)
    pale = material('PaleWood', 'oak_wood_planks', (.80, .68, .52), rough=.5, out=out)
    metal = material('Steel', 'metal_plate', (.62, .63, .64), rough=.3, out=out)
    brass = material('Brass', 'metal_plate', (.78, .62, .34), rough=.25, out=out)
    dark = material('DarkGloss', 'metal_plate', (.06, .06, .07), rough=.15, out=out)
    porcelain = material('Porcelain', 'painted_plaster_wall', (.97, .97, .96), rough=.12, out=out)
    sheer = material('Sheer', 'rough_linen', (.97, .96, .92), rough=.9, out=out)
    drape_sand = material('DrapeSand', 'velour_velvet', (.66, .55, .40), rough=.8, out=out)
    drape_teal = material('DrapeTeal', 'velour_velvet', (.20, .32, .36), rough=.8, out=out)
    padded = material('Padded', 'velour_velvet', (.78, .72, .62), rough=.85, out=out)
    towel = material('Towel', 'waffle_pique_cotton', (.97, .97, .95), rough=.95, out=out)
    linen = material('Linen', 'rough_linen', (.93, .93, .90), rough=.9, out=out)
    bag = material('Bag', 'denim_fabric', (.55, .58, .62), rough=.9, out=out)
    glass = bpy.data.materials.new('Glass')
    glass.use_nodes = True
    g = glass.node_tree.nodes['Principled BSDF']
    g.inputs['Base Color'].default_value = (.85, .92, .95, 1)
    g.inputs['Roughness'].default_value = .03
    g.inputs['Alpha'].default_value = .18
    mirror = bpy.data.materials.new('Mirror')
    mirror.use_nodes = True
    mm = mirror.node_tree.nodes['Principled BSDF']
    mm.inputs['Base Color'].default_value = (.9, .92, .93, 1)
    mm.inputs['Metallic'].default_value = 1.0
    mm.inputs['Roughness'].default_value = .02
    daylight = bpy.data.materials.new('DaylightPanel')
    daylight.use_nodes = True
    d = daylight.node_tree.nodes['Principled BSDF']
    d.inputs['Base Color'].default_value = (.82, .90, .96, 1)
    d.inputs['Emission Color'].default_value = (.82, .90, .96, 1)
    d.inputs['Emission Strength'].default_value = 2.0

    # ---------------------------------------------------------------- floors and ceilings
    box('floor_corr', (X1 - X0, YN - YC, .03), B(0, (YC + YN) / 2, .015), carpet, uv=1.2)
    box('runner_edge_n', (X1 - X0 - .4, .05, .032), B(0, YN - .32, .016), pale, uv=.6)
    box('floor_linen', (XL - X0, YC - YS, .03), B((X0 + XL) / 2, (YS + YC) / 2, .015), tiles, uv=.9)
    box('floor_std', (XS - XL, YC - YS, .03), B((XL + XS) / 2, (YS + YC) / 2, .015), parquet, uv=1.6)
    box('floor_lux', (X1 - XS, YC - YS, .03), B((XS + X1) / 2, (YS + YC) / 2, .015), parquet, uv=1.6)
    box('floor_stdbath', (2.0, 2.4, .033), B(-3.28, 2.58, .017), marble, uv=1.2)
    box('floor_luxbath', (3.7, 3.4, .033), B(5.21, 2.08, .017), marble, uv=1.2)
    ceiling('ceil_all', X0, X1, YS, YN, plaster)

    # ---------------------------------------------------------------- walls
    # Corridor south wall with the three doors (linen room, standard, luxury); north and end walls are the tower's,
    # lined here so the finish is ours.
    D_LIN, D_STD, D_LUX = -5.67, -1.28, 1.2
    wall_x('corr_s', YC, X0, X1, plaster, [(D_LIN, .9), (D_STD, .9), (D_LUX, .95)])
    box('corr_n', (X1 - X0, .04, H), B(0, YN - .02, H / 2), plaster, uv=1.5)
    box('corr_w', (.04, YN - YC, H), B(X0 + .02, (YC + YN) / 2, H / 2), plaster, uv=1.5)
    box('corr_e', (.04, YN - YC, H), B(X1 - .02, (YC + YN) / 2, H / 2), plaster, uv=1.5)
    # Room partitions down to the facade; the inner faces of the facade and of the end walls are lined too.
    wall_y('part_ls', XL, YS, YC, plaster)
    wall_y('part_sl', XS, YS, YC, plaster)
    box('line_w', (.04, YC - YS, H), B(X0 + .02, (YS + YC) / 2, H / 2), plaster, uv=1.5)
    box('line_e', (.04, YC - YS, H), B(X1 - .02, (YS + YC) / 2, H / 2), sandwall, uv=1.5)
    box('line_s', (X1 - X0, .03, H), B(0, YS + .015, H / 2), plaster, uv=1.5)
    # Standard bathroom (x -4.28..-2.28, y 1.38..3.78): door from the entry hall on its east wall.
    wall_y('stdbath_e', -2.28, 1.38, YC, plaster, [(2.4, .8)])
    wall_x('stdbath_s', 1.38, XL, -2.28, plaster)
    # Luxury bathroom (x 3.36..7.06, y 0.38..3.78): door from the hall on its west wall.
    wall_y('luxbath_w', 3.36, .38, YC, plaster, [(2.6, .9)])
    wall_x('luxbath_s', .38, 3.36, X1, plaster)
    # Wall tiles to 2.1 m inside both bathrooms (thin skins on the inner faces).
    for nm, (x0, x1, y0, y1) in {'std': (XL, -2.28, 1.38, YC), 'lux': (3.36, X1, .38, YC)}.items():
        box(f'tile_{nm}_n', (x1 - x0 - .14, .012, 2.1), B((x0 + x1) / 2, y1 - .066, 1.05), tiles, uv=.9)
        box(f'tile_{nm}_s', (x1 - x0 - .14, .012, 2.1), B((x0 + x1) / 2, y0 + .066, 1.05), tiles, uv=.9)
        box(f'tile_{nm}_w', (.012, y1 - y0 - .14, 2.1), B(x0 + .066, (y0 + y1) / 2, 1.05), tiles, uv=.9)
        box(f'tile_{nm}_e', (.012, y1 - y0 - .14, 2.1), B(x1 - .066, (y0 + y1) / 2, 1.05), tiles, uv=.9)

    # ---------------------------------------------------------------- doors, casings, plaques
    for nm, cx, w in (('lin', D_LIN, .9), ('std', D_STD, .9), ('lux', D_LUX, .95)):
        casing(f'cas_{nm}', cx, YC, True, w, teak)
        box(f'plaque_{nm}', (.16, .015, .11), B(cx + w / 2 + .2, YC + T / 2 + .008, 1.5), brass, uv=.3)
    # Room doors open inwards against the hall walls; the bathroom doors open into the bathroom.
    door_leaf('door_lin', (D_LIN - .45, YC - T / 2), .9, (0, -1), teak, brass)
    # 08/11 (C16): the standard and luxury room leaves are separate swinging doors now (gen_hotel_door.py,
    # AMareServiceTarget "RoomDoor"), so the guest can open them for room service.
    casing('cas_stdbath', -2.28, 2.4, False, .8, teak)
    door_leaf('door_stdbath', (-2.28 - T / 2, 2.8), .8, (-1, 0), pale, brass)
    casing('cas_luxbath', 3.36, 2.6, False, .9, teak)
    door_leaf('door_luxbath', (3.36 + T / 2, 3.05), .9, (1, 0), pale, brass)

    # ---------------------------------------------------------------- corridor
    # Teak wainscot to 1 m with a rail, on both long walls (broken at the doors), and the elevator door.
    def wainscot(name, y, face, gaps):
        edges = [X0 + .04]
        for cx, w in sorted(gaps):
            edges += [cx - w / 2 - .1, cx + w / 2 + .1]
        edges.append(X1 - .04)
        for i in range(0, len(edges), 2):
            a, b = edges[i], edges[i + 1]
            if b - a < .05:
                continue
            box(f'{name}{i}', (b - a, .02, .95), B((a + b) / 2, y + face * .01, .5), teak, uv=.9)
            box(f'{name}rail{i}', (b - a, .045, .04), B((a + b) / 2, y + face * .022, .99), teak, uv=.6)
    wainscot('wain_s', YC + T / 2, 1, [(D_LIN, .9), (D_STD, .9), (D_LUX, .95)])
    EV = -5.0
    wainscot('wain_n', YN - .04, -1, [(EV, 1.9)])
    box('elevdoor', (1.5, .05, 2.45), B(EV, YN - .07, 1.225), metal, uv=.6)
    box('elevseam', (.02, .06, 2.3), B(EV, YN - .09, 1.16), dark, uv=.6)
    for sx in (-1, 1):
        box(f'elevjamb{sx}', (.14, .14, 2.6), B(EV + sx * .82, YN - .08, 1.3), metal, uv=.6)
    box('elevhead', (1.78, .14, .16), B(EV, YN - .08, 2.53), metal, uv=.6)
    box('elevpanel', (.12, .04, .3), B(EV + 1.05, YN - .06, 1.2), brass, uv=.4)
    for k in range(2):
        disc(f'elevbtn{k}', .018, .012, B(EV + 1.05, YN - .09, 1.13 + k * .12), (math.pi / 2, 0, 0), plaster, 12)
    # Console with a mirror at the west end and a bench at the east end.
    box('console', (.4, 1.2, .08), B(X0 + .26, 4.78, .82), teak, uv=.6)
    for sy in (-1, 1):
        box(f'console_leg{sy}', (.05, .05, .78), B(X0 + .4, 4.78 + sy * .55, .39), brass, uv=.4)
    box('console_mirror', (.02, 1.0, 1.1), B(X0 + .06, 4.78, 1.65), mirror, uv=1)
    box('console_mframe', (.03, 1.08, 1.18), B(X0 + .05, 4.78, 1.65), brass, uv=.5)
    box('bench', (.45, 1.3, .1), B(X1 - .3, 4.78, .45), teak, uv=.6)
    cushion('bench_pad', (.42, 1.26, .07), B(X1 - .3, 4.78, .53), padded, puff=.01)
    for sy in (-1, 1):
        box(f'bench_leg{sy}', (.38, .05, .4), B(X1 - .3, 4.78 + sy * .58, .2), teak, uv=.5)

    # ---------------------------------------------------------------- linen room (x -7.06..-4.28)
    for k, z in enumerate((.12, .6, 1.08, 1.56, 2.04)):
        box(f'shelf_w{k}', (.5, 4.2, .025), B(X0 + .3, 0, z), metal, uv=.5)
        box(f'shelf_e{k}', (.5, 3.0, .025), B(XL - .3, -1.0, z), metal, uv=.5)
    for sy in (-2.1, 0, 2.1):
        for sx in (-.24, .24):
            tube(f'upr_w{sy}{sx}', B(X0 + .3 + sx, sy, 0), B(X0 + .3 + sx, sy, 2.1), .012, metal, 8)
    for sy in (-2.5, -1.0, .5):
        for sx in (-.24, .24):
            tube(f'upr_e{sy}{sx}', B(XL - .3 + sx, sy, 0), B(XL - .3 + sx, sy, 2.1), .012, metal, 8)
    for k, z in enumerate((.6, 1.08, 1.56)):
        for j, sy in enumerate((-1.6, -.8, 0, .8, 1.6)):
            folded(f'stack_w{k}{j}', X0 + .3, sy, z + .013, 4 + (j + k) % 3, towel if (j + k) % 2 else linen, (.34, .3, .05))
        for j, sy in enumerate((-2.2, -1.4, -.6, .2)):
            folded(f'stack_e{k}{j}', XL - .3, sy, z + .013, 3 + (j * 2 + k) % 3, linen if j % 2 else towel, (.34, .3, .05))
    cart('cart', -5.45, 1.6, linen, towel, metal, bag)
    cushion('hamper', (.5, .5, .65), B(-6.6, -4.9, .34), bag, puff=.03)
    window('win_lin', -6.06, 1.95, sheer, drape_sand, teak, metal, daylight, plaster, closed=.6)

    # ---------------------------------------------------------------- standard room (x -4.28..-0.28)
    # Entry hall: wardrobe on the east wall; bedroom: padded headboard panel on the west wall, minibar console on the east.
    wardrobe('std_ward', XS - T / 2 - .3, 2.55, 1.9, True, -1, teak, metal)
    box('std_headpanel', (.06, 2.6, 1.3), B(XL + T / 2 + .03, -1.6, 1.15), teak, uv=.8)
    for k in range(5):
        cushion(f'std_pad{k}', (.06, .48, 1.1), B(XL + T / 2 + .08, -1.6 + (k - 2) * .51, 1.15), padded, puff=.012)
    console_minibar('std_tv', XS - T / 2 - .26, -1.6, 1.6, True, -1, teak, marble, dark, metal)
    box('std_desk', (.55, 1.2, .04), B(XS - T / 2 - .3, -4.55, .75), teak, uv=.6)
    for sy in (-1, 1):
        box(f'std_deskleg{sy}', (.5, .04, .73), B(XS - T / 2 - .3, -4.55 + sy * .56, .365), teak, uv=.5)
    window('win_std', -2.285, 2.45, sheer, drape_sand, teak, metal, daylight, plaster)
    skirting('std_sk', [(XL + .07, YS + .04, XS - .07, YS + .04), (XL + T / 2 + .01, YS, XL + T / 2 + .01, 1.38)], teak)
    # Bathroom: shower in the south-west corner, toilet on the west wall, vanity on the north wall.
    shower('std_sh', XL + T / 2, -3.28, 1.38 + T / 2, 2.38, ['x1', 'y1'], marble, glass, metal, (-3.8, 1.75, XL + T / 2 + .08, 1.75))
    toilet('std_wc', XL + T / 2 + .02, 3.0, (1, 0), porcelain, metal)
    vanity('std_van', -3.0, YC - T / 2 - .27, .9, True, pale, marble, porcelain, metal, mirror)
    tube('std_towelbar', B(-2.36, 1.6, 1.25), B(-2.36, 1.95, 1.25), .012, metal, 8)
    cushion('std_towelhang', (.04, .32, .5), B(-2.39, 1.78, 1.0), towel, puff=.005)
    folded('std_towels', -3.35, YC - T / 2 - .27, .82, 2, towel, (.28, .2, .04))

    # ---------------------------------------------------------------- luxury room (x -0.28..7.06)
    wardrobe('lux_ward', XS + T / 2 + .3, 2.15, 2.3, True, 1, teak, metal)
    # Slatted teak feature wall behind the king bed (on the bathroom's south wall), TV console on the west partition.
    for k in range(17):
        box(f'lux_slat{k}', (.08, .1, H - .35), B(3.75 + k * .2, .38 - T / 2 - .06, (H - .35) / 2 + .06), teak, uv=.8)
    console_minibar('lux_tv', XS + T / 2 + .26, -2.0, 1.9, True, 1, teak, marble, dark, metal)
    window('win_lux1', 1.715, 2.45, sheer, drape_teal, teak, metal, daylight, plaster)
    window('win_lux0', 5.715, 2.45, sheer, drape_teal, teak, metal, daylight, plaster)
    skirting('lux_sk', [(XS + .07, YS + .04, X1 - .07, YS + .04), (X1 - .05, YS, X1 - .05, .38)], teak)
    # Bathroom: built-in tub along the south wall, shower in the north-east corner, double vanity on the east wall, toilet north.
    tub = lathe('lux_tub', [(0, 0), (.66, 0), (.68, .52), (.72, .57), (.66, .58), (.58, .22), (0, .18)], (0, 0, 0), porcelain, 40)
    tub.scale = (1.15, .5, 1.0)
    tub.location = B(4.4, .38 + T / 2 + .4, 0)
    tube('lux_tubtap', B(5.15, .38 + T / 2 + .06, .56), B(5.15, .38 + T / 2 + .06, .8), .016, metal, 8)
    tube('lux_tubspout', B(5.15, .38 + T / 2 + .06, .8), B(5.15, .38 + T / 2 + .2, .8), .013, metal, 8)
    shower('lux_sh', 5.96, X1 - .07, 2.68, YC - T / 2, ['x0', 'y0'], marble, glass, metal, (6.5, 3.25, 6.5, YC - T / 2 - .08))
    vanity('lux_van', X1 - .32, 1.55, 1.6, False, pale, marble, porcelain, metal, mirror, basins=2)
    toilet('lux_wc', 4.7, YC - T / 2 - .02, (0, -1), porcelain, metal)
    tube('lux_towelbar', B(3.44, 1.0, 1.25), B(3.44, 1.7, 1.25), .012, metal, 8)
    cushion('lux_towelhang', (.04, .6, .55), B(3.47, 1.35, .98), towel, puff=.005)
    folded('lux_towels', 4.0, .38 + T / 2 + .25, .56, 3, towel, (.3, .22, .045))

    # ---------------------------------------------------------------- art
    if ART.exists():
        art = bpy.data.materials.new('Painting')
        art.use_nodes = True
        node = art.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(str(ART))
        art.node_tree.links.new(node.outputs['Color'], art.node_tree.nodes['Principled BSDF'].inputs['Base Color'])

        def canvas(name, x, y, w, h, yaw):
            bm = bmesh.new()
            v = [bm.verts.new(p) for p in [(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)]]
            f = bm.faces.new(v)
            uv = bm.loops.layers.uv.verify()
            for loop, co in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
                loop[uv].uv = co
            o = mesh_obj(name, bm)
            o.data.materials.append(art)
            o.location = B(x, y, 1.75)
            o.rotation_euler = (0, 0, yaw)
            return o
        # Corridor (north wall, facing south), standard (over the minibar console, facing west).
        box('art_corr_f', (1.3, .04, .9), B(1.5, YN - .06, 1.75), teak, uv=.6)
        canvas('art_corr', 1.5, YN - .085, 1.2, .8, math.pi)
        box('art_std_f', (.04, 1.1, .76), B(XS - T / 2 - .03, -4.55, 1.75), teak, uv=.6)
        canvas('art_std', XS - T / 2 - .055, -4.55, 1.0, .66, -math.pi / 2)
    export(slug, 'Andar de quartos do Grand Hotel')


if __name__ == '__main__':
    rooms()
    print('built mare_hotel_rooms')
