"""Persist required rendering usage on project-owned imported materials."""
import json,struct
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()


def deduplicate_actor_slots():
    catalog=json.loads((ROOT/'Content/Data/actors.json').read_text(encoding='utf-8-sig'));changed=[];merged=0
    for name,row in catalog.items():
        source=ROOT/'SourceArt/Actors'/(name+'.glb')
        if not source.exists():continue
        with source.open('rb') as stream:
            header=stream.read(20);length=struct.unpack_from('<I',header,12)[0]
            gltf=json.loads(stream.read(length).decode('utf-8'))
        signatures={m['name']:json.dumps({k:v for k,v in m.items() if k not in ['name','extras']},sort_keys=True) for m in gltf.get('materials',[]) if 'name' in m}
        for kind in ['static_meshes','skeletal_meshes']:
            for path in row.get(kind,[]):
                mesh=unreal.load_asset(path);field='static_materials' if kind=='static_meshes' else 'materials'
                slots=list(mesh.get_editor_property(field));canonical={};count=0
                for i,slot in enumerate(slots):
                    mat=slot.material_interface
                    if not mat:continue
                    key=signatures.get(mat.get_name(),signatures.get(str(slot.material_slot_name)))
                    if key is None:continue
                    first=canonical.setdefault(key,mat)
                    if first==mat:continue
                    if kind=='static_meshes':mesh.set_material(i,first)
                    else:slot.material_interface=first;slots[i]=slot
                    count+=1
                if count:
                    if kind=='skeletal_meshes':mesh.set_editor_property(field,slots)
                    unreal.EditorAssetLibrary.save_loaded_asset(mesh);merged+=count;changed.append(path)
    return {'slots_reused':merged,'meshes':changed,'source_material_parameters_preserved':True}


def actor_materials(fix=False):
    catalog=json.loads((ROOT/'Content/Data/actors.json').read_text(encoding='utf-8-sig'))
    roots={};instances={};meshes=0;skeletal={}
    for row in catalog.values():
        for kind in ['static_meshes','skeletal_meshes']:
            for path in row.get(kind,[]):
                mesh=unreal.load_asset(path)
                if not mesh:raise RuntimeError('Missing catalog mesh: '+path)
                meshes+=1
                slots=mesh.get_editor_property('static_materials' if kind=='static_meshes' else 'materials')
                if kind=='skeletal_meshes':skeletal[path]=[{'slot':str(s.material_slot_name),'material':s.material_interface.get_path_name() if s.material_interface else None} for s in slots]
                nanite=mesh.get_editor_property('nanite_settings').enabled if 'nanite_settings' in dir(mesh) else False
                for slot in slots:
                    mat=slot.material_interface
                    chain=[]
                    while isinstance(mat,unreal.MaterialInstanceConstant):chain.append(mat);mat=mat.get_editor_property('parent')
                    if not isinstance(mat,unreal.Material):raise RuntimeError('Missing material on '+path)
                    key=mat.get_path_name();entry=roots.setdefault(key,{'root':mat,'nanite':False,'skeletal':False,'paths':[]})
                    entry['nanite']|=nanite;entry['skeletal']|=kind=='skeletal_meshes';entry['paths'].append(path)
                    if chain:instances.setdefault(key,[]).append(chain[-1])
    changes=[]
    for path,entry in roots.items():
        mat=entry['root'];needed=[name for name in ['nanite','skeletal_mesh'] if entry['nanite' if name=='nanite' else 'skeletal'] and not mat.get_editor_property('used_with_'+name)]
        if not needed:
            if fix and path.startswith('/Game/'):unreal.EditorAssetLibrary.save_loaded_asset(mat,True)
            continue
        changes.append({'material':path,'required':needed,'mesh_count':len(set(entry['paths']))})
        if not fix:continue
        if not path.startswith('/Game/'):
            clone_path='/Game/Actors/Combined/Shared/Mare_'+mat.get_name()
            clone=unreal.load_asset(clone_path) or unreal.EditorAssetLibrary.duplicate_asset(path,clone_path)
            if not clone:raise RuntimeError('Cannot create project copy: '+path)
            for instance in instances.get(path,[]):
                instance.set_editor_property('parent',clone);unreal.EditorAssetLibrary.save_loaded_asset(instance)
            mat=clone
        for name in needed:mat.set_editor_property('used_with_'+name,True)
        errors=list(unreal.MaterialEditingLibrary.recompile_material(mat))
        if errors:raise RuntimeError(str(errors))
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
    result={'catalog_meshes':meshes,'root_materials':len(roots),'required_changes':changes,'fixed':fix,'skeletal_slots':skeletal}
    if fix:(ROOT/'Content/Data/actor_material_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
