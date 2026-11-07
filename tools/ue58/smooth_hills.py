"""Round and smooth the low-poly Godot backdrop hill tiles (70 meshes, ~240 triangles each).

Catmull-Clark subdivision (2 levels) with smooth boundaries that keep the tile corners: the boundary
rule only uses the boundary polyline, which neighbouring tiles share, so no gaps open between tiles.
Smooth shading on top. Originals copied to D:/CodexTemp/hills/orig; materials/images restored from
them after export.

  blender -b --factory-startup --python tools/ue58/smooth_hills.py -- World_0601 World_0602 ...
"""
import json
import shutil
import sys
from pathlib import Path

import bpy

MODELS = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models'
BACKUP = Path('D:/CodexTemp/hills/orig')


def smooth(name):
    BACKUP.mkdir(parents=True, exist_ok=True)
    src = MODELS / (name + '.gltf')
    if not (BACKUP / src.name).exists():
        shutil.copy2(src, BACKUP / src.name)
        for buf in json.loads(src.read_text(encoding='utf-8')).get('buffers', []):
            shutil.copy2(MODELS / buf['uri'], BACKUP / buf['uri'])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(BACKUP / src.name))
    obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    # Triangles from the Godot export: merge coplanar-ish pairs into quads first for a cleaner limit surface.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.mesh.tris_convert_to_quads(face_threshold=0.698, shape_threshold=0.698)
    bpy.ops.object.mode_set(mode='OBJECT')
    mod = obj.modifiers.new('round', 'SUBSURF')
    mod.levels = mod.render_levels = 2
    mod.boundary_smooth = 'PRESERVE_CORNERS'
    mod.uv_smooth = 'PRESERVE_BOUNDARIES'
    bpy.ops.object.modifier_apply(modifier=mod.name)
    for p in obj.data.polygons:
        p.use_smooth = True
    faces = len(obj.data.polygons)
    bpy.ops.export_scene.gltf(filepath=str(src), export_format='GLTF_SEPARATE', use_selection=True, export_yup=True,
                              export_apply=True, export_image_format='NONE')
    old = json.loads((BACKUP / src.name).read_text(encoding='utf-8'))
    new = json.loads(src.read_text(encoding='utf-8'))
    by_name = {m['name']: m for m in old.get('materials', [])}
    new['materials'] = [by_name.get(m['name'], m) for m in new.get('materials', [])]
    for key in ('images', 'textures', 'samplers'):
        if key in old:
            new[key] = old[key]
    src.write_text(json.dumps(new), encoding='utf-8')
    return faces


if __name__ == '__main__':
    names = sys.argv[sys.argv.index('--') + 1:]
    print('SMOOTH_HILLS', json.dumps({n: smooth(n) for n in names}))
