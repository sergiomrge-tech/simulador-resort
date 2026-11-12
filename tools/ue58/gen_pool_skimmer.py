"""Pool skimmer net for the pool attendant (03/11, PENDENCIAS "limpar e atender": he only reached into the air). No CC0
model was found (CGTrader's free one is royalty-free with restrictions, others paid), so it is modelled here at real size.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_pool_skimmer.py
Output: unreal/MareAlta/SourceArt/Models/PoolStaff/pool_skimmer.glb (metres; the butt of the pole at the origin, the pole
along +X, the net head at x 2.40-2.86 with its frame in the XY plane and the bag hanging towards -Z).

Pole: 2.4 m anodised aluminium tube (r 14 mm) in two telescopic sections with a twist-lock collar, a rubber end cap
and a ribbed hand grip near the butt. Head: moulded blue plastic connector, rounded-rectangle frame 44 x 34 cm (tube
r 7 mm) and a shallow bag (10 cm deep) of real mesh threads every 12 mm, so it reads as a net from every distance.
"""
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector, Matrix

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models/PoolStaff'


def mat(name, colour, rough, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    return m


def obj_from(bm, name, m, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    me.materials.append(m)
    for poly in me.polygons:
        poly.use_smooth = smooth
    return o


def lathe(name, profile, m, segs=32, x0=0.0):
    """Surface of revolution around the X axis: profile = [(x, radius), ...]."""
    bm = bmesh.new()
    rings = []
    for x, r in profile:
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            ring.append(bm.verts.new((x0 + x, r * math.cos(a), r * math.sin(a))))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(segs):
            bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]))
    # caps
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        if ring[0].co.y ** 2 + ring[0].co.z ** 2 > 1e-10:
            f = bm.faces.new(ring[::-1] if flip else ring)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from(bm, name, m)


def tube_path(name, points, r, m, segs=12, closed=False):
    """Round tube along a polyline (parallel-transported frames)."""
    bm = bmesh.new()
    pts = [Vector(p) for p in points]
    n = len(pts)
    rings = []
    prev_normal = None
    for i in range(n):
        if closed:
            t = (pts[(i + 1) % n] - pts[i - 1]).normalized()
        else:
            t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        if prev_normal is None:
            ref = Vector((0, 0, 1)) if abs(t.z) < .9 else Vector((1, 0, 0))
            normal = (ref - t * ref.dot(t)).normalized()
        else:
            normal = (prev_normal - t * prev_normal.dot(t)).normalized()
        prev_normal = normal
        binormal = t.cross(normal)
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            ring.append(bm.verts.new(pts[i] + (normal * math.cos(a) + binormal * math.sin(a)) * r))
        rings.append(ring)
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for a, b in pairs:
        for k in range(segs):
            bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]))
    if not closed:
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from(bm, name, m)


def rounded_rect(cx, cy, w, h, rad, z=0.0, per_corner=10):
    pts = []
    for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oy = cx + sx * (w / 2 - rad), cy + sy * (h / 2 - rad)
        for k in range(per_corner + 1):
            a = math.radians(a0 + 90 * k / per_corner)
            pts.append((ox + rad * math.cos(a), oy + rad * math.sin(a), z))
    return pts


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    alu = mat('skimmer_alu', (.78, .80, .83), .32, 1.0)
    alu_dark = mat('skimmer_alu_dark', (.55, .58, .62), .38, 1.0)
    blue = mat('skimmer_blue_plastic', (.05, .32, .62), .45)
    rubber = mat('skimmer_grip_rubber', (.05, .06, .07), .85)
    net = mat('skimmer_net', (.80, .88, .92), .7)
    parts = []
    # Pole: butt section 1.25 m (r 14 mm) and the inner section to 2.40 m (r 12.5 mm); collar at the joint.
    parts.append(lathe('pole_outer', [(0.0, .0), (0.0, .014), (1.25, .014), (1.25, .0)], alu))
    parts.append(lathe('pole_inner', [(1.20, .0), (1.20, .0125), (2.40, .0125), (2.40, .0)], alu_dark))
    parts.append(lathe('collar', [(1.21, .0), (1.21, .0165), (1.215, .019), (1.285, .019), (1.29, .0165), (1.29, .0)], blue))
    # Rubber end cap and a ribbed grip 10-40 cm from the butt.
    parts.append(lathe('cap', [(-.012, .0), (-.012, .010), (-.008, .0155), (.04, .0158), (.04, .0)], rubber))
    grip = [(.10, .0)]
    for k in range(13):
        x = .10 + k * .023
        grip += [(x, .0162), (x + .008, .0172), (x + .015, .0172), (x + .023, .0162)]
    grip.append((.40, .0))
    parts.append(lathe('grip', grip, rubber, segs=28))
    # Head connector: a moulded sleeve that flares into a yoke holding the frame.
    parts.append(lathe('connector', [(2.30, .0), (2.30, .0145), (2.38, .0150), (2.42, .0190), (2.46, .0130), (2.46, .0)], blue))
    # Frame 44 x 34 cm, rounded, slightly ahead of the connector, in the XY plane at the pole axis height.
    cx = 2.46 + .22
    frame = rounded_rect(cx, 0, .44, .34, .07)
    parts.append(tube_path('frame', frame, .007, blue, segs=10, closed=True))
    # Bag: depth 10 cm at the centre (cosine falloff to the frame), threads every 12 mm both ways.
    def bag_z(x, y):
        u = (x - cx) / .22
        v = y / .17
        d = max(0.0, 1 - max(abs(u) ** 2.2, abs(v) ** 2.2))
        return -.10 * math.sin(d * math.pi / 2)
    step = .012
    xs = [cx - .22 + .006 + i * step for i in range(int(.428 / step) + 1)]
    ys = [-.17 + .006 + j * step for j in range(int(.328 / step) + 1)]
    inside = lambda x, y: abs(x - cx) <= .215 and abs(y) <= .165
    bm = bmesh.new()
    def thread(pts, r=.0009):
        # thin square tube between consecutive points (4 sides keep the count down for ~60 threads)
        ring_prev = None
        for i, p in enumerate(pts):
            p = Vector(p)
            t = (Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(i - 1, 0)])).normalized()
            ref = Vector((0, 0, 1)) if abs(t.z) < .9 else Vector((1, 0, 0))
            nrm = (ref - t * ref.dot(t)).normalized()
            bi = t.cross(nrm)
            ring = [bm.verts.new(p + (nrm * math.cos(a) + bi * math.sin(a)) * r) for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)]
            if ring_prev:
                for k in range(4):
                    bm.faces.new((ring_prev[k], ring_prev[(k + 1) % 4], ring[(k + 1) % 4], ring[k]))
            ring_prev = ring
    for x in xs:
        pts = [(x, y, bag_z(x, y)) for y in [-.165 + k * .011 for k in range(31)] if inside(x, y)]
        if len(pts) > 1:
            thread(pts)
    for y in ys:
        pts = [(x, y, bag_z(x, y)) for x in [cx - .215 + k * .0143 for k in range(31)] if inside(x, y)]
        if len(pts) > 1:
            thread(pts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(obj_from(bm, 'net', net, smooth=False))
    # Join and export.
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / 'pool_skimmer.glb'
    bpy.ops.export_scene.gltf(filepath=str(out), export_format='GLB', export_apply=True)
    me = bpy.context.view_layer.objects.active.data
    print('WROTE', out, 'verts', len(me.vertices), 'tris', sum(len(p.vertices) - 2 for p in me.polygons))


main()
