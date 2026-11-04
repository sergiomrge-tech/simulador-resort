"""Prepare the Fab "Wooden House" (Helindu.Art, CC BY 4.0) for Unreal: unique material/image names (Interchange
reuses assets by name), no camera, one joined mesh, base at z=0 centred on the footprint, power-of-two textures.
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/prep_wood_house.py"""
import bpy
import bmesh  # noqa: F401  (bpy must come first)
from mathutils import Vector

SRC = 'D:/Assets/Fab/wooden_house/wooden_house.glb'
OUT = 'D:/CodexTemp/tsunami/WoodHouse.glb'
P = 'WoodHouse_'

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
for o in list(bpy.data.objects):
    if o.type != 'MESH':
        continue
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT'):
        bpy.data.objects.remove(o)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
# Bake the parent transforms into the meshes, then join.
for o in meshes:
    m = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = m
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join()
house = bpy.context.view_layer.objects.active
house.name = house.data.name = 'WoodHouse'
for o in list(bpy.data.objects):
    if o != house:
        bpy.data.objects.remove(o)
for i, mat in enumerate(house.data.materials):
    mat.name = f'{P}M{i:02d}'
for i, img in enumerate(list(bpy.data.images)):
    w, h = img.size

    pw, ph = 1 << (max(w, 1) - 1).bit_length(), 1 << (max(h, 1) - 1).bit_length()
    if w and (pw, ph) != (w, h):
        img.scale(pw, ph)
        img.pack()
    elif not img.packed_file:
        img.pack()
    img.name = f'{P}T{i:02d}'
# Base at z=0, footprint centred on the origin.
vs = [house.matrix_world @ v.co for v in house.data.vertices]
lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
c = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
for v in house.data.vertices:
    v.co -= c
print('DIM', tuple(round(x, 3) for x in (hi - lo)), 'verts', len(house.data.vertices), 'mats', len(house.data.materials))
# Where is the porch? Count vertices per side band (the porch side has many low vertices outside the walls).
vs = [v.co for v in house.data.vertices]
for name, f in (('+X', lambda v: v.x), ('-X', lambda v: -v.x), ('+Y', lambda v: v.y), ('-Y', lambda v: -v.y)):
    far = max(f(v) for v in vs)
    print('SIDE', name, 'extent', round(far, 2), 'low verts near edge', sum(1 for v in vs if f(v) > far - 1.0 and v.z < 1.0))
import os
os.makedirs('D:/CodexTemp/tsunami', exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=False, export_apply=True)
print('OUT', OUT)
