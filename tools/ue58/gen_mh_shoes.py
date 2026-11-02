"""Footwear fitted to an exported MetaHuman body (same pipeline as gen_mh_swimwear.py): flip-flops or sneakers,
skinned with the body's weights. Run with the bpy venv:
  D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_mh_shoes.py -- <body.fbx> <out.fbx> flipflops|sneakers
Feet rest on z=0 in the exported body (Blender metres, front = -Y)."""
import sys
import math
from pathlib import Path
sys.argv = sys.argv[:1] + ['--'] + sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402
import gen_mh_swimwear as sw  # noqa: E402  (reuses load_body, tube_rows, patch helpers; its main() is guarded below)

args = sys.argv[sys.argv.index('--') + 1:]
SRC, DST, KIND = args[0], args[1], args[2] if len(args) > 2 else 'flipflops'


def foot_outline(bm, side):
    """2D outline (x, y) of one foot's sole: the lowest vertices, convex-hulled, slightly grown."""
    pts = [(v.co.x, v.co.y) for v in bm.verts if v.co.z < .025 and side * v.co.x > .02]
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in pts))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    cx = sum(p[0] for p in hull) / len(hull)
    cy = sum(p[1] for p in hull) / len(hull)
    return [(cx + (x - cx) * 1.08, cy + (y - cy) * 1.06) for x, y in hull], (cx, cy)


def sole(bm_out, outline, thick, z0=0.0):
    """Extruded sole slab under the foot; its faces use material slot 1 (rubber), the upper/strap slot 0."""
    top = [bm_out.verts.new((x, y, z0 + thick)) for x, y in outline]
    bot = [bm_out.verts.new((x, y, z0)) for x, y in outline]
    n = len(outline)
    faces = [bm_out.faces.new((bot[k], bot[(k + 1) % n], top[(k + 1) % n], top[k])) for k in range(n)]
    faces += [bm_out.faces.new(top), bm_out.faces.new(bot[::-1])]
    for f in faces:
        f.material_index = 1


def flipflops(bm_out, tree, bm):
    for side in (1, -1):
        outline, (cx, cy) = foot_outline(bm, side)
        sole(bm_out, outline, .012, -.004)
        # Thong: from between the first toes up over the instep to both sides of the foot (a Y of straps).
        toe = Vector((cx - side * .012, min(p[1] for p in outline) + .035, .015))
        for sx in (1, -1):
            end = Vector((cx + sx * .042, cy - .01, .012))
            mid = toe.lerp(end, .5) + Vector((0, 0, .03))
            guide = sw.catmull([toe, mid, end], 10)
            sw.ribbon(bm_out, tree, guide, .014)


def hull2d(pts):
    pts = sorted(set(pts))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def ray_hull(poly, cx, cy, a):
    """Distance from (cx, cy) along angle a to the polygon's boundary (farthest crossing)."""
    dx, dy = math.sin(a), -math.cos(a)
    best = 0.0
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i - 1], poly[i]
        ex, ey = x2 - x1, y2 - y1
        den = dx * ey - dy * ex
        if abs(den) < 1e-12:
            continue
        t = ((x1 - cx) * ey - (y1 - cy) * ex) / den
        u = ((x1 - cx) * dy - (y1 - cy) * dx) / den
        if t > 0 and -1e-6 <= u <= 1 + 1e-6:
            best = max(best, t)
    return best


def sneakers(bm_out, tree, bm):
    """Closed shoe lofted like a last: each height's slice of the foot is convex-hulled (toes merge into one toe
    box), sampled by angle from a common axis, pushed out 6 mm and joined to the next slice; the top slice is
    the collar around the ankle. A thicker sole goes under it."""
    steps = 96
    for side in (1, -1):
        outline, (cx, cy) = foot_outline(bm, side)
        foot = [v.co for v in bm.verts if side * v.co.x > .02 and v.co.z < .095]
        rows = [.006 + k * .006 for k in range(13)]
        polys = [hull2d([(round(c.x, 4), round(c.y, 4)) for c in foot if abs(c.z - z) < .005]) for z in rows]
        # Each slice is sampled from its own centre (the ankle slice lies behind the toe slices' centre).
        centres = [(sum(q[0] for q in pl) / len(pl), sum(q[1] for q in pl) / len(pl)) for pl in polys]
        centres = [centres[0]] + [((a[0] + 2 * b[0] + c[0]) / 4, (a[1] + 2 * b[1] + c[1]) / 4)
                                  for a, b, c in zip(centres, centres[1:], centres[2:])] + [centres[-1]]
        radii = [[ray_hull(pl, c[0], c[1], 2 * math.pi * k / steps) + .006 + .003 * (z > .045) for k in range(steps)]
                 for pl, c, z in zip(polys, centres, rows)]
        for k in range(steps):      # rounder toe box: a slice may not be smaller than 85% of the one above it
            for r in range(len(rows) - 2, -1, -1):
                radii[r][k] = max(radii[r][k], radii[r + 1][k] * .85)
        for _ in range(2):          # vertical smoothing: no ripples between slices at the heel
            radii = [radii[0]] + [[(a[k] + 2 * b[k] + c[k]) / 4 for k in range(steps)]
                                  for a, b, c in zip(radii, radii[1:], radii[2:])] + [radii[-1]]
        def at(r, k, rad):
            a = 2 * math.pi * k / steps
            return Vector((centres[r][0] + math.sin(a) * rad, centres[r][1] - math.cos(a) * rad, rows[r]))
        for _ in range(4):          # skin poking through (heel, ankle bones): grow those radii, then re-smooth
            for r in range(1, len(rows)):
                for k in range(steps):
                    a = 2 * math.pi * k / steps
                    hit = tree.ray_cast(at(r, k, radii[r][k]), Vector((math.sin(a), -math.cos(a), 0)), .05)
                    if hit[0] is not None:
                        radii[r][k] += hit[3] + .005
            radii = [[(rr[k - 1] + 2 * rr[k] + rr[(k + 1) % steps]) / 4 for k in range(steps)] for rr in radii]
            radii = [radii[0]] + [[max(b[k], (a[k] + 2 * b[k] + c[k]) / 4) for k in range(steps)]
                                  for a, b, c in zip(radii, radii[1:], radii[2:])] + [radii[-1]]
        rings = [[bm_out.verts.new(at(r, k, radii[r][k])) for k in range(steps)] for r in range(len(rows))]
        for r0, r1 in zip(rings, rings[1:]):
            for k in range(steps):
                bm_out.faces.new((r0[k], r0[(k + 1) % steps], r1[(k + 1) % steps], r1[k]))
        sole(bm_out, outline, .024, -.006)


def main():
    body, arm, bm, tree = sw.load_body()
    out = bmesh.new()
    (flipflops if KIND == 'flipflops' else sneakers)(out, tree, bm)
    bmesh.ops.remove_doubles(out, verts=out.verts, dist=.0005)
    mesh = bpy.data.meshes.new(f'SKM_{KIND}')
    out.to_mesh(mesh)
    shoe = bpy.data.objects.new(f'SKM_{KIND}', mesh)
    bpy.context.scene.collection.objects.link(shoe)
    shoe.data.uv_layers.new(name='UVMap')
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(bpy.data.materials.new(f'MI_MH_{KIND.capitalize()}_Upper'))
    mesh.materials.append(bpy.data.materials.new(f'MI_MH_{KIND.capitalize()}_Sole'))
    bpy.context.view_layer.objects.active = shoe
    for g in body.vertex_groups:
        shoe.vertex_groups.new(name=g.name)
    dt = shoe.modifiers.new('Weights', 'DATA_TRANSFER')
    dt.object = body
    dt.use_object_transform = True
    dt.use_vert_data = True
    dt.data_types_verts = {'VGROUP_WEIGHTS'}
    dt.vert_mapping = 'POLYINTERP_NEAREST'
    dt.layers_vgroup_select_src = 'ALL'
    dt.layers_vgroup_select_dst = 'NAME'
    shoe.matrix_world = body.matrix_world.copy()
    shoe.data.transform(body.matrix_world.inverted())
    shoe.parent = body.parent
    shoe.matrix_world = body.matrix_world.copy()
    bpy.ops.object.modifier_apply(modifier='Weights')
    am = shoe.modifiers.new('Armature', 'ARMATURE')
    am.object = arm
    bpy.data.objects.remove(body, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    shoe.select_set(True)
    arm.select_set(True)
    bpy.ops.export_scene.fbx(filepath=DST, use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                             bake_anim=False, mesh_smooth_type='FACE')
    print('WROTE', DST, len(mesh.vertices))


main()
