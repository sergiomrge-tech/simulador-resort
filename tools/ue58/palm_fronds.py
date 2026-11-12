"""Replace the flat alpha-card palm fronds with modelled fronds (curved rachis + real leaflets).

Trunk and coconuts of each exported palm variant are kept; the frond primitive is removed and
rebuilt around the same crown point with the same spread, so every instance in the level keeps its
transform. Originals are copied to D:/CodexTemp/palms/orig first.

  blender -b --factory-startup --python tools/ue58/palm_fronds.py -- World_0507 World_0508 ...
"""
import json
import math
import random
import shutil
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Matrix

MODELS = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models'
BACKUP = Path('D:/CodexTemp/palms/orig')
FROND_MAT = 'MA_f68de0934'      # prefix of the exported alpha-card frond material
NEW_MAT = 'MA_palm_frond_geo'


def backup(name):
    BACKUP.mkdir(parents=True, exist_ok=True)
    src = MODELS / (name + '.gltf')
    dst = BACKUP / (name + '.gltf')
    if not dst.exists():
        data = json.loads(src.read_text(encoding='utf-8'))
        shutil.copy2(src, dst)
        for buf in data.get('buffers', []):
            if not (BACKUP / buf['uri']).exists():
                shutil.copy2(MODELS / buf['uri'], BACKUP / buf['uri'])
    return dst


def frond_material():
    m = bpy.data.materials.new(NEW_MAT)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.085, 0.235, 0.055, 1)
    bsdf.inputs['Roughness'].default_value = 0.55
    m.use_backface_culling = False
    return m


def rachis_point(origin, yaw, pitch0, length, droop, t):
    """Curved midrib: starts rising at pitch0 and bends down by droop towards the tip."""
    steps = 24
    p = Vector(origin)
    d = None
    for i in range(int(t * steps)):
        a = pitch0 - droop * (i / steps) ** 1.6
        d = Vector((math.cos(a) * math.cos(yaw), math.cos(a) * math.sin(yaw), math.sin(a)))
        p = p + d * (length / steps)
    if d is None:
        d = Vector((math.cos(pitch0) * math.cos(yaw), math.cos(pitch0) * math.sin(yaw), math.sin(pitch0)))
    return p, d


def add_frond(bm, mat_index, uv, origin, yaw, pitch0, length, droop, rnd):
    # Midrib: tapered quad strip.
    prev = None
    for i in range(25):
        t = i / 24
        p, d = rachis_point(origin, yaw, pitch0, length, droop, t)
        side = Vector((-math.sin(yaw), math.cos(yaw), 0)) * (0.03 * (1 - t) + 0.006)
        a, b = bm.verts.new(p - side), bm.verts.new(p + side)
        if prev:
            f = bm.faces.new((prev[0], prev[1], b, a))
            f.material_index = mat_index
            f.smooth = True
        prev = (a, b)
    # Leaflets on both sides, forward-angled and drooping in a V, longest mid-frond.
    count = 46
    for i in range(count):
        t = 0.1 + 0.88 * i / (count - 1)
        p, d = rachis_point(origin, yaw, pitch0, length, droop, t)
        side = d.cross(Vector((0, 0, 1)))
        if side.length < 1e-4:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(d).normalized()
        llen = 0.95 * (math.sin(math.pi * min(1, t * 1.05)) ** 0.6) * (0.85 + 0.3 * rnd.random()) * (length / 4.0)
        for s in (-1, 1):
            dirv = (side * s * 0.78 + d * 0.42 - up * 0.32).normalized()
            width = 0.075 * (length / 4.0)
            segs = 4
            row = []
            for k in range(segs + 1):
                u = k / segs
                q = p + dirv * (llen * u) - up * (0.18 * llen * u * u)   # leaflet tip bends down
                w = width * (1 - u) ** 0.8 + 0.002
                across = d * w
                row.append((bm.verts.new(q - across), bm.verts.new(q + across)))
            for k in range(segs):
                f = bm.faces.new((row[k][0], row[k][1], row[k + 1][1], row[k + 1][0]))
                f.material_index = mat_index
                f.smooth = True
                for loop, (uu, vv) in zip(f.loops, ((0, k / segs), (1, k / segs), (1, (k + 1) / segs), (0, (k + 1) / segs))):
                    loop[uv].uv = (uu, vv)


def rebuild(name, seed):
    src = backup(name)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(src))
    obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    obj.data.transform(obj.matrix_world)
    obj.parent = None
    obj.matrix_world = Matrix.Identity(4)
    me = obj.data
    frond_index = next(i for i, m in enumerate(me.materials) if m.name.startswith(FROND_MAT))
    verts = [me.vertices[v].co.copy() for p in me.polygons if p.material_index == frond_index for v in p.vertices]
    lo = Vector([min(v[i] for v in verts) for i in range(3)])
    hi = Vector([max(v[i] for v in verts) for i in range(3)])
    spread = max(hi.x - lo.x, hi.y - lo.y) / 2
    # Crown = top of the trunk (highest trunk vertices) under the frond cluster.
    trunk_index = next(i for i, m in enumerate(me.materials) if m.name.startswith('MA_bc468080f'))
    trunk = [me.vertices[v].co.copy() for p in me.polygons if p.material_index == trunk_index for v in p.vertices]
    top_z = max(v.z for v in trunk)
    crown_pts = [v for v in trunk if v.z > top_z - 0.25]
    crown = Vector((sum(v.x for v in crown_pts) / len(crown_pts), sum(v.y for v in crown_pts) / len(crown_pts), top_z - 0.05))
    me.materials.append(frond_material())
    new_index = len(me.materials) - 1
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == frond_index], context='FACES')
    uv = bm.loops.layers.uv.active or bm.loops.layers.uv.new('UVMap')
    rnd = random.Random(seed)
    length = spread * 1.02
    fronds = 18
    for i in range(fronds):
        yaw = 2 * math.pi * i / fronds + rnd.uniform(-0.18, 0.18)
        pitch0 = math.radians(rnd.uniform(18, 42))
        droop = math.radians(rnd.uniform(70, 105))
        add_frond(bm, new_index, uv, crown, yaw, pitch0, length * rnd.uniform(0.85, 1.05), droop, rnd)
    for i in range(4):   # young upright fronds in the centre
        yaw = 2 * math.pi * i / 4 + 0.4
        add_frond(bm, new_index, uv, crown + Vector((0, 0, 0.05)), yaw, math.radians(68), length * 0.55, math.radians(35), rnd)
    bm.to_mesh(me)
    bm.free()
    me.update()
    # Drop the now-unused frond slot so the exported material list is clean.
    obj.active_material_index = frond_index
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.material_slot_remove()
    faces = len(me.polygons)
    out = MODELS / (name + '.gltf')
    bpy.ops.export_scene.gltf(filepath=str(out), export_format='GLTF_SEPARATE', use_selection=True, export_yup=True,
                              export_apply=True, export_image_format='NONE')
    old = json.loads(src.read_text(encoding='utf-8'))
    new = json.loads(out.read_text(encoding='utf-8'))
    by_name = {m['name']: m for m in old.get('materials', [])}
    new['materials'] = [by_name.get(m['name'], m) for m in new.get('materials', [])]
    for key in ('images', 'textures', 'samplers'):
        if key in old:
            new[key] = old[key]
    out.write_text(json.dumps(new), encoding='utf-8')
    return {'mesh': name, 'faces': faces, 'crown': list(crown), 'spread_m': round(spread, 2)}


if __name__ == '__main__':
    names = sys.argv[sys.argv.index('--') + 1:]
    report = [rebuild(n, 20261101 + i) for i, n in enumerate(names)]
    Path('D:/CodexTemp/palms').mkdir(parents=True, exist_ok=True)
    Path('D:/CodexTemp/palms/report.json').write_text(json.dumps(report, indent=1, default=str), encoding='utf-8')
    print(json.dumps(report, default=str))
