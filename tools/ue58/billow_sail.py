"""Give a flat exported sail a wind-filled billow (max draft mid-sail, zero at the mast and boom).

  blender -b --factory-startup --python tools/ue58/billow_sail.py -- World_1373 MA_64d59c041af 0.22
(mesh, prefix of the sail material, draft in metres). Original copied to D:/CodexTemp/sails/orig.
"""
import json
import math
import shutil
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix

MODELS = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models'
BACKUP = Path('D:/CodexTemp/sails/orig')


def main(name, prefix, draft):
    BACKUP.mkdir(parents=True, exist_ok=True)
    src, dst = MODELS / (name + '.gltf'), BACKUP / (name + '.gltf')
    if not dst.exists():
        data = json.loads(src.read_text(encoding='utf-8'))
        shutil.copy2(src, dst)
        for buf in data.get('buffers', []):
            if not (BACKUP / buf['uri']).exists():
                shutil.copy2(MODELS / buf['uri'], BACKUP / buf['uri'])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(dst))
    obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    obj.data.transform(obj.matrix_world)
    obj.parent = None
    obj.matrix_world = Matrix.Identity(4)
    me = obj.data
    idx = next(i for i, m in enumerate(me.materials) if m.name.startswith(prefix))
    bm = bmesh.new()
    bm.from_mesh(me)
    sail = [f for f in bm.faces if f.material_index == idx]
    edges = list({e for f in sail for e in f.edges})
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=3, use_grid_fill=True)
    sail = [f for f in bm.faces if f.material_index == idx]
    verts = list({v for f in sail for v in f.verts})
    lo = [min(v.co[i] for v in verts) for i in range(3)]
    hi = [max(v.co[i] for v in verts) for i in range(3)]
    size = [hi[i] - lo[i] for i in range(3)]
    thin = min(range(3), key=lambda i: size[i])
    a, b = [i for i in range(3) if i != thin]
    for v in verts:
        u = (v.co[a] - lo[a]) / max(size[a], 1e-6)
        w = (v.co[b] - lo[b]) / max(size[b], 1e-6)
        # Deepest a third back from the luff and a bit above the foot, like a real mainsail.
        belly = math.sin(math.pi * u) ** 1.2 * math.sin(math.pi * min(1.0, w * 1.05)) ** 0.9
        v.co[thin] += draft * belly
    for f in sail:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    me.update()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(src), export_format='GLTF_SEPARATE', use_selection=True, export_yup=True,
                              export_apply=True, export_image_format='NONE')
    old = json.loads(dst.read_text(encoding='utf-8'))
    new = json.loads(src.read_text(encoding='utf-8'))
    by_name = {m['name']: m for m in old.get('materials', [])}
    new['materials'] = [by_name.get(m['name'], m) for m in new.get('materials', [])]
    for key in ('images', 'textures', 'samplers'):
        if key in old:
            new[key] = old[key]
    src.write_text(json.dumps(new), encoding='utf-8')
    print(json.dumps({'mesh': name, 'sail_faces': len(sail), 'draft_m': draft, 'thin_axis': thin}))


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    main(args[0], args[1], float(args[2]))
