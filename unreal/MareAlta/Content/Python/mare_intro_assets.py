"""Import the attributed CC0 bus as an editable project asset."""
import json
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()

def import_bus():
    task=unreal.AssetImportTask();task.filename=str(ROOT/'SourceArt/Intro/bus.fbx')
    task.destination_path='/Game/Intro/Bus';task.automated=True;task.save=True
    options=unreal.FbxImportUI();options.set_editor_property('import_mesh',True);options.set_editor_property('import_as_skeletal',False)
    options.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.static_mesh_import_data.set_editor_property('combine_meshes',True)
    task.options=options;unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes=[unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets('/Game/Intro/Bus',recursive=True)]
    meshes=[m for m in meshes if isinstance(m,unreal.StaticMesh)]
    if len(meshes)!=1:raise RuntimeError('Expected one combined bus mesh: '+str([m.get_path_name() for m in meshes]))
    mesh=meshes[0];b=mesh.get_bounds()
    info={'path':mesh.get_path_name(),'origin':[b.origin.x,b.origin.y,b.origin.z],'extent':[b.box_extent.x,b.box_extent.y,b.box_extent.z],
          'source':'https://opengameart.org/content/3d-bus','author':'ajanhallinta','license':'CC0','has_interior':False}
    (ROOT/'Content/Data/intro_bus.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    return info
