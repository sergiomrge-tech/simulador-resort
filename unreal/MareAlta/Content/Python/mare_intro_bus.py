"""Import the edited CC0 bus without replacing the approved original model."""
import json,hashlib
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()


def refine_materials(mesh):
    # Interchange reimport can preserve the original Blender-2.x white shaders.
    # Author explicit PBR surfaces for those legacy slots, keeping the geometry.
    palette={'Body':((.62,.66,.63),.35,.4), 'Windows':((.36,.38,.37),0,.08),
             'karmi':((.055,.07,.07),.5,.35),'RearLights':((.4,.025,.01),.1,.3),
             'FrontLights':((.8,.78,.64),.2,.18),'Indicators':((.7,.24,.015),.1,.25),
             'Metal':((.3,.34,.34),.85,.3),'Tire':((.018,.022,.021),0,.87),
             'Bolt':((.25,.28,.27),.9,.3)}
    mel=unreal.MaterialEditingLibrary;changed=[]
    for i,slot in enumerate(mesh.get_editor_property('static_materials')):
        name=str(slot.material_slot_name)
        if name not in palette:continue
        color,metal,rough=palette[name];path='/Game/Intro/Refined/Materials/M_Bus_'+name
        mat=unreal.load_asset(path)
        if not mat:mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_Bus_'+name,'/Game/Intro/Refined/Materials',unreal.Material,unreal.MaterialFactoryNew())
        mel.delete_all_material_expressions(mat);mat.set_editor_property('two_sided',True)
        def scalar(value,property):
            node=mel.create_material_expression(mat,unreal.MaterialExpressionConstant);node.r=value;mel.connect_material_property(node,'',property)
        node=mel.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector);node.constant=unreal.LinearColor(*color,1)
        mel.connect_material_property(node,'',unreal.MaterialProperty.MP_BASE_COLOR)
        scalar(metal,unreal.MaterialProperty.MP_METALLIC);scalar(rough,unreal.MaterialProperty.MP_ROUGHNESS)
        if name=='Windows':
            mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
            mat.set_editor_property('translucency_lighting_mode',unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
            scalar(.10,unreal.MaterialProperty.MP_OPACITY)
        else:mat.set_editor_property('blend_mode',unreal.BlendMode.BLEND_OPAQUE)
        mel.recompile_material(mat)
        if not unreal.EditorAssetLibrary.save_loaded_asset(mat,False):raise RuntimeError('Bus surface not saved: '+name)
        mesh.set_material(i,mat);changed.append(name)
    if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,False):raise RuntimeError('Bus slots not saved')
    return changed


def import_part(name):
    folder='/Game/Intro/Refined/'+name
    file=ROOT/'SourceArt/Intro/Refined'/(name+'.glb')
    stamp=ROOT/'Content/Data/intro_import_hashes.json'
    hashes=json.loads(stamp.read_text(encoding='utf-8')) if stamp.exists() else {}
    digest=hashlib.sha256(file.read_bytes()).hexdigest()
    meshes=[unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(folder,recursive=True)]
    meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
    if not meshes or hashes.get(name)!=digest:
        task=unreal.AssetImportTask();task.filename=str(ROOT/'SourceArt/Intro/Refined'/(name+'.glb'))
        task.destination_path=folder;task.automated=True;task.save=True;task.replace_existing=True
        pipeline=unreal.InterchangeGenericAssetsPipeline();pipeline.common_meshes_properties.bake_meshes=True
        pipeline.mesh_pipeline.combine_static_meshes_behavior=unreal.InterchangeCombineStaticMeshesBehavior.ALL
        stack=unreal.InterchangePipelineStackOverride();stack.set_editor_property('override_pipelines',[unreal.SoftObjectPath(pipeline.get_path_name())]);task.options=stack
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        meshes=[unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(folder,recursive=True)]
        meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
    if len(meshes)!=1:raise RuntimeError(name+' expected one mesh')
    mesh=meshes[0];settings=mesh.get_editor_property('nanite_settings')
    settings.enabled=False
    unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).set_nanite_settings(mesh,settings,True)
    refine_materials(mesh)
    if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,False):raise RuntimeError('Mesh not saved: '+name)
    hashes[name]=digest;stamp.write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    return mesh


def build():
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():raise RuntimeError('Stop PIE before import')
    source=json.loads((ROOT/'SourceArt/Intro/Refined/manifest.json').read_text(encoding='utf-8'))
    probe=import_part('AxisProbe');p=probe.get_bounds().origin
    signs=[round(p.x/100),round(p.y/200),round(p.z/300)]
    if any(abs(abs(a)-b)>1 for a,b in zip([p.x,p.y,p.z],[100,200,300])):raise RuntimeError('Unexpected bus axis conversion '+str(p))
    def native(values):return [v*s*100 for v,s in zip(values,signs)]
    parts={}
    for name in ('Bus_Cabin','Bus_Door','wheelFL','wheelFR','wheelLR','wheelRR'):
        mesh=import_part(name)
        parts[name]={'mesh':mesh.get_path_name(),'triangles':mesh.get_num_triangles(0)}
        if name.startswith('wheel'):parts[name]['position']=native(source['wheels_blender'][name])
    parts['Bus_Door']['position']=native(source['door_pivot_blender'])
    letter=import_part('Letter_Home')
    result={'parts':parts,'letter_mesh':letter.get_path_name(),'steps':[native(p) for p in source['steps_blender']],
            'interior_camera':native([2.50,0,1.48]),'front_look':native([5.5,0,1.40]),
            'door_swing_yaw':85*signs[1],'seats':source['seat_count'],
            'source':'CC0 ajanhallinta, original project edits; editable bus_refined.blend',
            'axis_signs':signs}
    (ROOT/'Content/Data/intro_refined_bus.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    import mare_audio
    result['audio']=mare_audio.build()
    return result
