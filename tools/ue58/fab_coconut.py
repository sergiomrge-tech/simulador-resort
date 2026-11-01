"""Replace the loose green coconuts with the Fab "Coconut" by Rabeya Akter (Fab Standard License).

The download carries geometry only (husk sphere + fibre strands, flat colour); the husk gets the
CC0 Poly Haven palm_bark maps in Unreal (M_CoconutHusk_PBR). Each variant keeps the footprint of the
exported Godot coconut: same width, centre and resting base.

  blender -b --factory-startup --python tools/ue58/fab_coconut.py -- World_0326 World_1414
"""
import json
import math
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

MODELS = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models'
SRC = Path('D:/Assets/Fab/coconut_rabeya/n1.glb')
BACKUP = Path('D:/CodexTemp/coconuts/orig')
LAY_YAW = {'World_0326': 0, 'World_1414': 70}


def backup(name):
    BACKUP.mkdir(parents=True, exist_ok=True)
    src = MODELS / (name + '.gltf')
    if not (BACKUP / src.name).exists():
        shutil.copy2(src, BACKUP / src.name)
        for buf in json.loads(src.read_text(encoding='utf-8')).get('buffers', []):
            shutil.copy2(MODELS / buf['uri'], BACKUP / buf['uri'])
    return BACKUP / src.name


def bounds(objs):
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def build(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(backup(name)))
    lo_o, hi_o = bounds([o for o in bpy.context.scene.objects if o.type == 'MESH'])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SRC))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    husk = max(meshes, key=lambda o: len(o.data.polygons) if o.name.startswith('Sphere') else -1)
    for o in meshes:
        o.data.transform(o.matrix_world)
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
        mat = bpy.data.materials.new('MA_coconut_husk' if o == husk else 'MA_coconut_fiber')
        o.data.materials.clear()
        o.data.materials.append(mat)
    for o in [o for o in bpy.context.scene.objects if o.type != 'MESH']:
        bpy.data.objects.remove(o)
    # A dry coconut is egg-shaped and never balances on its tip: lay the long axis down, turned a
    # little differently per variant, slightly rolled so the three eyes face sideways.
    lay = Matrix.Rotation(math.radians(LAY_YAW.get(name, 0)), 4, 'Z') @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Rotation(math.radians(25), 4, 'Z')
    for o in meshes:
        o.data.transform(lay)
    # Fit on the husk (fibres stick out a little, as on a real dry coconut).
    lo_n, hi_n = bounds([husk])
    # Longest horizontal side to the old width: the coconuts sit in tight piles (16 cm apart).
    s = .95 * (hi_o.x - lo_o.x) / max(hi_n.x - lo_n.x, hi_n.y - lo_n.y)
    centre_o = (lo_o + hi_o) / 2
    centre_n = (lo_n + hi_n) / 2
    m = Matrix.Translation((centre_o.x, centre_o.y, lo_o.z)) @ Matrix.Scale(s, 4) @ Matrix.Translation((-centre_n.x, -centre_n.y, -lo_n.z))
    for o in meshes:
        o.data.transform(m)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = husk
    bpy.ops.object.join()
    husk.name = husk.data.name = name
    bpy.ops.export_scene.gltf(filepath=str(MODELS / (name + '.gltf')), export_format='GLTF_SEPARATE', use_selection=True,
                              export_yup=True, export_apply=True, export_image_format='NONE')
    return {'mesh': name, 'faces': len(husk.data.polygons), 'scale': round(s, 4), 'size_cm': [round(v * 100) for v in husk.dimensions]}


if __name__ == '__main__':
    print('FAB_COCONUT', json.dumps([build(n) for n in sys.argv[sys.argv.index('--') + 1:]]))
