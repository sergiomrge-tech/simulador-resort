"""Small triangle bikini (or swim trunks) fitted to an exported MetaHuman body, skinned to its skeleton.

Run with the isolated bpy 5.0.1 venv (Blender is not installed):
  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_mh_swimwear.py -- <body.fbx> <out.fbx> bikini|trunks

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
    bust = min((w for w in ws if .03 < w.x < .15 and 1.05 < w.z < 1.36), key=lambda w: w.y)
    crotch = min((w for w in ws if abs(w.x) < .015 and .55 < w.z < 1.0), key=lambda w: w.z)
    hips = max((w for w in ws if .75 < w.z < 1.0 and abs(w.x) < .26), key=lambda w: abs(w.x))
    neck = max(w.z for w in ws if abs(w.x) < .05)
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
    # Bottom: small front triangle, cheeky back, gusset under the crotch.
    front = patch(bm_out, tree, curve((-.085, top), (-.022, cz + .014), -.018) + [(-.02, cz + .007), (.02, cz + .007)] +
          curve((.022, cz + .014), (.085, top), -.018) + curve((.085, top), (-.085, top), .006), 'front')
    back = patch(bm_out, tree, curve((.10, top + .008), (.028, cz + .03), .02) + [(.025, cz + .012), (-.025, cz + .012)] +
          curve((-.028, cz + .03), (-.10, top + .008), .02) + curve((-.10, top + .008), (.10, top + .008), -.008), 'back')
    drape(bm_out, tree, front, cz + .05)   # the narrow part between the legs may tighten like fabric
    drape(bm_out, tree, back, cz + .05)
    fy = cast(tree, Vector((0, -.6, cz + .012)), Vector((0, 1, 0)))
    by = cast(tree, Vector((0, .6, cz + .03)), Vector((0, -1, 0)))
    if fy and by:
        patch(bm_out, tree, [(-.022, fy.y - .01), (.022, fy.y - .01), (.026, by.y + .01), (-.026, by.y + .01)], 'under', .0006)
    # Side strings over the hips, front corner to back corner.
    for s in (1, -1):
        f = cast(tree, Vector((s * .083, -.6, top - .002)), Vector((0, 1, 0)))
        b = cast(tree, Vector((s * .098, .6, top + .006)), Vector((0, -1, 0)))
        if f and b:
            a0, a1 = angle_of(f), angle_of(b)
            path = [p.lerp(Vector((p.x, p.y, top + .012)), math.sin(math.pi * k / 30) * .6)
                    for k, p in enumerate(ring_path(tree, top + .002, a0, a1, steps=30))]
            ribbon(bm_out, tree, path, .011, Vector((0, 0, 1)))
    # Top: two triangle cups, an under-bust band and halter straps to the back of the neck.
    under = bust.z - .058
    apexes = []
    for s in (1, -1):
        ax = s * abs(bust.x)
        apex = (ax + s * .004, bust.z + .085)
        poly = curve((s * .012, under), (s * .128, under + .006), -.004 * s) + \
            curve((s * .128, under + .006), apex, .012 * s) + curve(apex, (s * .012, under), .010 * s)
        if s < 0:
            poly = poly[::-1]
        patch(bm_out, tree, poly, 'front')
        apexes.append(cast(tree, Vector((apex[0], -.6, apex[1] - .006)), Vector((0, 1, 0))))
    band = ring_path(tree, under + .004, 62, 298, steps=70)   # cup side edge, around the back, other cup
    ribbon(bm_out, tree, band, .012, Vector((0, 0, 1)))
    nz = m['neck']
    for s, a in zip((1, -1), apexes):
        if a is None:
            continue
        # Up beside the neck and tied at its back (halter), never across the throat.
        keys = [a, Vector((s * .066, -.05, nz - .07)), Vector((s * .064, -.008, nz - .04)), Vector((s * .04, .045, nz - .035)),
                Vector((0, .06, nz - .04))]
        guide = catmull(keys, 8)
        ribbon(bm_out, tree, guide, .009)


def trunks(bm_out, tree, m):
    cz = m['crotch'].z
    top = cz + .19
    leg = cz - .015
    for plane, sy in (('front', -1), ('back', 1)):
        w = m['hip_x'] + .01
        patch(bm_out, tree, [(-w, top), (w, top), (w, leg - .06), (.012, leg), (-.012, leg), (-w, leg - .06)], plane)
    for s in (1, -1):
        ring = ring_path(tree, top - .005, 70 * s, 110 * s, steps=12)
        for z in [top - .01 - k * .012 for k in range(int((top - leg + .06) / .012))]:
            ribbon(bm_out, tree, ring_path(tree, z, 60 * s, 120 * s, steps=12), .013, Vector((0, 0, 1)))


def main():
    body, arm, bm, tree = load_body()
    m = measure(bm)
    out = bmesh.new()
    (bikini if KIND == 'bikini' else trunks)(out, tree, m)
    bmesh.ops.remove_doubles(out, verts=out.verts, dist=.0008)
    mesh = bpy.data.meshes.new(f'SKM_{KIND}')
    out.to_mesh(mesh)
    garment = bpy.data.objects.new(f'SKM_{KIND}', mesh)
    bpy.context.scene.collection.objects.link(garment)
    garment.data.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        poly.use_smooth = True
    mat = bpy.data.materials.new(f'MI_MH_{KIND.capitalize()}')
    mesh.materials.append(mat)
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


main()
