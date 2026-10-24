"""Variantes vazias dos recipientes autorais existentes; sem bebida/gelo/fruta.
Mantém a geometria detalhada do vidro e os canudos. Fontes Blender portáveis.
"""
from pathlib import Path
import bpy, bmesh, shutil, tempfile

ROOT = Path(__file__).resolve().parents[1]
for source in ['glass_juice', 'cocktail', 'dish_batida']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(ROOT / 'assets/models/gen' / (source+'.glb')))
    count = 0
    for obj in list(bpy.context.scene.objects):
        if obj.type != 'MESH': continue
        bm = bmesh.new(); bm.from_mesh(obj.data)
        remove = [f for f in bm.faces if not obj.data.materials[f.material_index].name.startswith(('vidro', 'canudo'))]
        bmesh.ops.delete(bm, geom=remove, context='FACES')
        bm.to_mesh(obj.data); bm.free()
        if not obj.data.polygons:
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            count += len(obj.data.polygons)
            obj.name = 'Used_'+source
    assert count > 100, (source, count)
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version = 0
    name = 'used_'+source
    stage = Path(tempfile.gettempdir())/(name+'.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(stage))
    target = ROOT/'art/blender'/(name+'.blend')
    shutil.copyfile(stage, target)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/models/gen'/(name+'.glb')), export_format='GLB')
    bpy.ops.wm.open_mainfile(filepath=str(target))
    assert all(im.packed_file for im in bpy.data.images if im.source=='FILE')
    print('USED_DRINK_PORTABLE PASS', name, count)

# Recipientes de cerâmica vazios: o plate-dinner antigo incluía comida no próprio modelo.
from gen_code_props import fresh, mat, lathe
for name, depth in [('table_plate',.018),('table_bowl',.050)]:
    fresh()
    ceramic=mat('porcelana_vazia',(.90,.89,.84),.26)
    profile=[(0,.004),(.060,.004),(.063,.001),(.067,.001),(.070,.005),(.090,.006),(.116,depth*.65),(.135,depth),(.140,depth+.003),(.142,depth+.006),(.140,depth+.009),(.135,depth+.009),(.115,depth*.65+.006),(.088,.013),(.060,.011),(0,.011)]
    ob=lathe(profile,ceramic,verts=96);ob.name=name
    bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
    stage=Path(tempfile.gettempdir())/(name+'.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(stage))
    target=ROOT/'art/blender'/(name+'.blend');shutil.copyfile(stage,target)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/models/gen'/(name+'.glb')),export_format='GLB')
    bpy.ops.wm.open_mainfile(filepath=str(target))
    assert any(o.type=='MESH' and len(o.data.polygons)>100 for o in bpy.context.scene.objects)
    print('EMPTY_CERAMIC_PORTABLE PASS',name)
