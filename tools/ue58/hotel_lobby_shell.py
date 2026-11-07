"""Open the Grand Hotel ground floor: remove the solid core, cut a glass entrance and
build a lobby shell (walls, ceiling, reception, elevators) reusing the tower's own
materials. Also splits the result into Nanite opaque / glass glTF render proxies.

Run with the isolated bpy venv:
  D:/Tools/blender-5.2.2-windows-x64/blender.exe -b --factory-startup --python tools/ue58/hotel_lobby_shell.py -- inspect|build
Coordinates are the original Blender frame of tools/gen_hotel.py (front = -Y, base z=0).
"""
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: E402  (bpy must load before bmesh/mathutils in this package)
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
UE = ROOT / 'unreal/MareAlta'
MODELS = UE / 'SourceArt/Models'
SOURCE = MODELS / 'World_2365.gltf'
# Untouched copy of the imported source (gltf + bin) so the build is repeatable.
BACKUP = Path('D:/CodexTemp/hotel-lobby/orig/World_2365.gltf')
# Hashed material names of the imported tower (same order as gen_hotel.hotel_tower).
MAT = {'reboco': 'MA_ce2523fac531c072ae83f219', 'pedra': 'MA_f0b4c91d222df43b754da5de',
       'reboco_areia': 'MA_e27dc8c30fdd83877248f30e', 'clear_window_glass': 'MA_a3573534a1ac032b2a83b215',
       'vidro': 'MA_267fb69ef073ee86a78de3dd', 'metal': 'MA_ccb4eadda740e328c44ba6fd',
       'madeira': 'MA_678a254b5911781a067329d8', 'planta': 'MA_57684429ae8753e59855d9f5'}
GLASS = {MAT['vidro'], MAT['clear_window_glass']}
W, D, G = 32.0, 13.0, 4.5
# Solid ground-floor core of gen_hotel.hotel_tower plus the painted "lobby" plane behind the glass.
CORE = (Vector((-15.85, -5.2, 0.44)), Vector((15.85, 6.3, 4.96)))
DOOR_HALF = 1.6


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if len(meshes) != 1:
        raise SystemExit('expected one hotel mesh, got %d' % len(meshes))
    obj = meshes[0]
    # glTF import may parent under an empty with the Godot->Blender axis change; bake it.
    obj.data.transform(obj.matrix_world)
    obj.parent = None
    obj.matrix_world.identity()
    return obj


def inspect():
    obj = load(SOURCE)
    lo = Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])
    mats = [(i, m.name, m.blend_method if hasattr(m, 'blend_method') else '') for i, m in enumerate(obj.data.materials)]
    inside = sum(1 for p in obj.data.polygons if all(CORE[0].x <= obj.data.vertices[v].co.x <= CORE[1].x and CORE[0].y <= obj.data.vertices[v].co.y <= CORE[1].y and CORE[0].z <= obj.data.vertices[v].co.z <= CORE[1].z for v in p.vertices))
    print(json.dumps({'min': list(lo), 'max': list(hi), 'polys': len(obj.data.polygons), 'materials': mats, 'core_faces': inside}, indent=1, default=str))


def inside(co, lo, hi):
    return all(lo[i] - 1e-4 <= co[i] <= hi[i] + 1e-4 for i in range(3))


def uv_box(bm, uv, scale=0.5):
    """World-space box projection so plaster/stone/wood textures keep real-world size."""
    for f in bm.faces:
        n = f.normal
        a = max(range(3), key=lambda i: abs(n[i]))
        u, v = [(1, 2), (0, 2), (0, 1)][a]
        for loop in f.loops:
            loop[uv].uv = (loop.vert.co[u] * scale, loop.vert.co[v] * scale)


class Builder:
    """Adds bevelled, UV-mapped parts directly into the tower mesh with its own materials."""

    def __init__(self, obj):
        self.obj = obj
        self.mat = {m.name: i for i, m in enumerate(obj.data.materials)}
        self.bm = bmesh.new()
        self.bm.from_mesh(obj.data)
        self.uv = self.bm.loops.layers.uv.active or self.bm.loops.layers.uv.new('UVMap')
        self.added = 0

    def box(self, lo, hi, material, bevel=0.015):
        tmp = bmesh.new()
        bmesh.ops.create_cube(tmp, size=1.0)
        size = Vector(hi) - Vector(lo)
        center = (Vector(hi) + Vector(lo)) * 0.5
        for v in tmp.verts:
            v.co = Vector((v.co.x * size.x, v.co.y * size.y, v.co.z * size.z)) + center
        if bevel > 0:
            bmesh.ops.bevel(tmp, geom=list(tmp.edges), offset=min(bevel, min(size) * 0.3), segments=2, affect='EDGES', profile=0.5)
        self._merge(tmp, material)

    def lathe(self, profile, center, material, segments=32):
        """Turned column: profile [(radius, height)] revolved around Z."""
        tmp = bmesh.new()
        rings = [[tmp.verts.new((center[0] + r * math.cos(2 * math.pi * s / segments), center[1] + r * math.sin(2 * math.pi * s / segments), center[2] + h))
                  for s in range(segments)] for r, h in profile]
        for a, b in zip(rings, rings[1:]):
            for s in range(segments):
                tmp.faces.new((a[s], a[(s + 1) % segments], b[(s + 1) % segments], b[s]))
        bmesh.ops.remove_doubles(tmp, verts=tmp.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(tmp, faces=tmp.faces)
        self._merge(tmp, material)

    def _merge(self, tmp, material):
        tmp.normal_update()
        index = self.mat[MAT[material]]
        tmp_uv = tmp.loops.layers.uv.new('UVMap')
        uv_box(tmp, tmp_uv)
        mapping = {v: self.bm.verts.new(v.co) for v in tmp.verts}
        for f in tmp.faces:
            nf = self.bm.faces.new([mapping[v] for v in f.verts])
            nf.material_index = index
            for l_new, l_old in zip(nf.loops, f.loops):
                l_new[self.uv].uv = l_old[tmp_uv].uv
            self.added += 1
        tmp.free()

    def finish(self):
        self.bm.normal_update()
        self.bm.to_mesh(self.obj.data)
        self.bm.free()
        self.obj.data.update()


def open_ground_floor(b):
    bm = b.bm
    lo, hi = CORE
    core = [f for f in bm.faces if all(inside(v.co, lo, hi) for v in f.verts)]
    bmesh.ops.delete(bm, geom=core, context='FACES_ONLY')
    # Entrance: cut the front glass skin and its mullions in the centre bay, below the transom.
    skin_lo, skin_hi = Vector((-16, -5.45, 0.4)), Vector((16, -5.1, 4.6))
    skin = [f for f in bm.faces if all(inside(v.co, skin_lo, skin_hi) for v in f.verts)]
    geom = list({e for f in skin for e in f.edges} | set(skin) | {v for f in skin for v in f.verts})
    for plane_co, plane_no in (((-DOOR_HALF, 0, 0), (1, 0, 0)), ((DOOR_HALF, 0, 0), (1, 0, 0)), ((0, 0, 2.85), (0, 0, 1))):
        cut = bmesh.ops.bisect_plane(bm, geom=[g for g in geom if g.is_valid], plane_co=plane_co, plane_no=plane_no)
        geom = [g for g in set(geom) | set(cut['geom']) if g.is_valid]
    # The front gallery column at x=0 stood in the entrance axis; the bay now opens to the canopy.
    column = [f for f in bm.faces if f.is_valid and all(inside(v.co, Vector((-0.45, -6.6, 0.4)), Vector((0.45, -5.7, 4.97))) for v in f.verts)]
    bmesh.ops.delete(bm, geom=column, context='FACES')
    door_hi = Vector((DOOR_HALF + 0.01, skin_hi.y, 2.86))
    door = [f for f in bm.faces if all(inside(v.co, Vector((-DOOR_HALF - 0.01, skin_lo.y, skin_lo.z)), door_hi) for v in f.verts)]
    bmesh.ops.delete(bm, geom=door, context='FACES')
    return len(core), len(door)


def lobby(b):
    z0, ceil = 0.45, 4.78
    # Exterior skin of the ground floor is restored by the walls (same outline as the old core).
    b.box((-15.8, 5.9, z0), (15.8, 6.2, ceil), 'reboco_areia')
    b.box((-15.8, -5.2, z0), (-15.5, 6.2, ceil), 'reboco_areia')
    b.box((15.5, -5.2, z0), (15.8, 6.2, ceil), 'reboco_areia')
    for sx in (-1, 1):
        for k in range(4):                                       # wood wall panels on the side walls
            y = -3.5 + k * 2.6
            b.box((sx * 15.5 - 0.04, y - 0.6, 1.0), (sx * 15.5 + 0.04, y + 0.6, 3.1), 'madeira', 0.01)
    # Ceiling below the first slab with wood ribs.
    b.box((-15.5, -5.1, 4.62), (15.5, 5.9, 4.7), 'reboco', 0.01)
    for k in range(9):
        x = -14 + k * 3.5
        b.box((x - 0.08, -5.0, 4.5), (x + 0.08, 5.8, 4.62), 'madeira', 0.01)
    # Skirting and dado rail.
    b.box((-15.5, 5.8, z0), (15.5, 5.9, z0 + 0.12), 'madeira', 0.005)
    b.box((-15.5, 5.82, 1.05), (15.5, 5.9, 1.12), 'madeira', 0.005)
    # Turned interior columns carrying the first floor, like the front gallery.
    for x in (-10.5, -3.5, 3.5, 10.5):
        r = 0.24
        b.lathe([(r * 1.45, 0), (r * 1.45, 0.08), (r * 1.2, 0.18), (r, 0.28), (r * 1.03, 1.6), (r * 0.96, 3.7),
                 (r * 1.15, 3.85), (r * 1.4, 3.95), (r * 1.4, 4.05), (0.0, 4.05)], (x, 0.6, z0), 'reboco')
    # Reception desk: wood body with fluted front, stone top, metal kick plate, staff work top.
    x0, x1, y0, y1 = -9.6, -4.6, 1.3, 2.1
    b.box((x0, y0, z0), (x1, y1, z0 + 1.02), 'madeira', 0.03)
    for k in range(25):
        x = x0 + 0.1 + k * (x1 - x0 - 0.2) / 24
        b.box((x - 0.03, y0 - 0.04, z0 + 0.12), (x + 0.03, y0, z0 + 0.98), 'madeira', 0.01)
    b.box((x0 - 0.08, y0 - 0.12, z0 + 1.02), (x1 + 0.08, y1 + 0.05, z0 + 1.1), 'pedra', 0.02)
    b.box((x0 + 0.05, y0 - 0.05, z0), (x1 - 0.05, y0 + 0.02, z0 + 0.1), 'metal', 0.005)
    b.box((x0 + 0.3, y1 - 0.25, z0 + 0.72), (x1 - 0.3, y1 + 0.02, z0 + 0.78), 'pedra', 0.01)
    # Feature wall behind reception: vertical wood slats.
    for k in range(30):
        x = x0 - 0.4 + k * 0.2
        b.box((x - 0.05, 5.78, z0 + 0.15), (x + 0.05, 5.86, ceil - 0.25), 'madeira', 0.008)
    # Elevator lobby: two framed stainless doors with call panels.
    for cx in (5.0, 8.0):
        b.box((cx - 0.75, 5.82, z0), (cx + 0.75, 5.9, z0 + 2.45), 'metal', 0.01)
        b.box((cx - 0.02, 5.8, z0 + 0.02), (cx + 0.02, 5.83, z0 + 2.3), 'reboco_areia', 0.0)
        b.box((cx - 0.88, 5.78, z0), (cx - 0.75, 5.9, z0 + 2.6), 'metal', 0.01)
        b.box((cx + 0.75, 5.78, z0), (cx + 0.88, 5.9, z0 + 2.6), 'metal', 0.01)
        b.box((cx - 0.88, 5.78, z0 + 2.45), (cx + 0.88, 5.9, z0 + 2.6), 'metal', 0.01)
        b.box((cx + 0.98, 5.84, z0 + 1.05), (cx + 1.1, 5.9, z0 + 1.35), 'metal', 0.005)
    # Low stone planters flanking the entrance inside (plants are placed as CC0 models in UE).
    for sx in (-1, 1):
        b.box((sx * 2.4 - 0.6, -4.9, z0), (sx * 2.4 + 0.6, -4.3, z0 + 0.5), 'pedra', 0.03)


def export_gltf(obj, name):
    """Export geometry only, then restore the original material/texture records by name so
    Interchange reuses the shared ../Textures images and the audited MA_ materials."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    path = MODELS / (name + '.gltf')
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLTF_SEPARATE', use_selection=True, export_apply=True,
                              export_yup=True, export_image_format='NONE')
    original = json.loads(BACKUP.read_text(encoding='utf-8'))
    data = json.loads(path.read_text(encoding='utf-8'))
    by_name = {m['name']: m for m in original['materials']}
    data['materials'] = [by_name[m['name']] for m in data['materials']]
    for key in ('images', 'textures', 'samplers', 'extensionsUsed'):
        if key in original:
            data[key] = original[key]
    path.write_text(json.dumps(data), encoding='utf-8')
    return path


def build():
    obj = load(BACKUP)
    before = len(obj.data.polygons)
    b = Builder(obj)
    removed, door = open_ground_floor(b)
    lobby(b)
    added = b.added
    b.finish()
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode='OBJECT')
    tris = len(obj.data.polygons)
    export_gltf(obj, 'World_2365')
    # Render proxies: glass separated from the opaque Nanite part.
    glass = {i for i, m in enumerate(obj.data.materials) if m.name in GLASS}
    parts = {}
    for name, keep_glass in (('Opaque', False), ('Glass', True)):
        o = obj.copy()
        o.data = obj.data.copy()
        bpy.context.collection.objects.link(o)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if (f.material_index in glass) != keep_glass], context='FACES')
        bm.to_mesh(o.data)
        bm.free()
        parts[name] = len(o.data.polygons)
        export_gltf(o, 'HotelTower_' + name)
    lo = [min(v.co[i] for v in obj.data.vertices) for i in range(3)]
    hi = [max(v.co[i] for v in obj.data.vertices) for i in range(3)]
    report = {'polys_before': before, 'core_faces_removed': removed, 'door_faces_removed': door, 'faces_added': added,
              'triangles': tris, 'split': parts, 'bounds': [lo, hi]}
    (BACKUP.parent / 'build.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    {'inspect': inspect, 'build': build}[args[0]]()
