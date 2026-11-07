"""Refine faceted low-poly beach props (umbrella canopies, frames, poles) in place.

Catmull-Clark subdivision + smooth shading keeps UVs (stripe textures), materials and pivot,
so every instance in the level updates when the asset is reimported. Originals are copied to
D:/CodexTemp/smooth-props/orig before the first change.

  blender -b --factory-startup --python tools/ue58/smooth_props.py -- World_0100 World_2035 ...
"""
import json
import shutil
import sys
from pathlib import Path

import bpy

MODELS = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models'
BACKUP = Path('D:/CodexTemp/smooth-props/orig')


def refine(name):
    src = MODELS / (name + '.gltf')
    original = BACKUP / (name + '.gltf')
    BACKUP.mkdir(parents=True, exist_ok=True)
    if not original.exists():
        data = json.loads(src.read_text(encoding='utf-8'))
        shutil.copy2(src, original)
        for buf in data.get('buffers', []):
            if buf.get('uri') and not (BACKUP / buf['uri']).exists():
                shutil.copy2(MODELS / buf['uri'], BACKUP / buf['uri'])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(original))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    before = sum(len(o.data.polygons) for o in meshes)
    verts = sum(len(o.data.vertices) for o in meshes)
    levels = 2 if verts < 600 else 1
    for o in meshes:
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        # Merge split seams first so the surface subdivides as one piece (UV seams are kept).
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.0005)
        bpy.ops.object.mode_set(mode='OBJECT')
        mod = o.modifiers.new('Subsurf', 'SUBSURF')
        mod.levels = levels
        mod.render_levels = levels
        mod.uv_smooth = 'PRESERVE_BOUNDARIES'
        mod.boundary_smooth = 'PRESERVE_CORNERS'
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.ops.object.shade_smooth()
    after = sum(len(o.data.polygons) for o in meshes)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(src), export_format='GLTF_SEPARATE', use_selection=True,
                              export_yup=True, export_apply=True, export_image_format='NONE')
    # Restore the original material/texture records so the imported MA_/T_ assets are reused.
    old = json.loads(original.read_text(encoding='utf-8'))
    new = json.loads(src.read_text(encoding='utf-8'))
    by_name = {m['name']: m for m in old.get('materials', [])}
    new['materials'] = [by_name.get(m['name'], m) for m in new.get('materials', [])]
    for key in ('images', 'textures', 'samplers'):
        if key in old:
            new[key] = old[key]
    src.write_text(json.dumps(new), encoding='utf-8')
    return {'mesh': name, 'faces_before': before, 'faces_after': after, 'levels': levels}


if __name__ == '__main__':
    names = sys.argv[sys.argv.index('--') + 1:]
    report = [refine(n) for n in names]
    out = Path('D:/CodexTemp/smooth-props/report.json')
    out.write_text(json.dumps(report, indent=1), encoding='utf-8')
    print(json.dumps(report))
