"""Project-owned native MCP tools. No shell, arbitrary script, or external paths."""
import json
from pathlib import Path
import unreal
import toolset_registry
from toolset_registry.registration import Registration

ROOT=Path(unreal.Paths.project_dir()).resolve()
DATA=ROOT/'Content'/'Data'
SOURCE=ROOT/'SourceArt'/'Models'

def read(name,default):
    path=DATA/name
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else default

def distance(instance):
    p=instance['transform']['position']
    return ((p[0]-38)**2+(p[2]+13)**2)**0.5

@unreal.uclass()
class MareMigrationTools(unreal.ToolsetDefinition):
    """Import and validate the Maré Alta conversion in the currently open UE project."""

    @toolset_registry.tool_call
    @staticmethod
    def migration_status() -> str:
        """Report engine, current project, available source models and imported native meshes."""
        world=read('world.json',{})
        return json.dumps({'engine':unreal.SystemLibrary.get_engine_version(),'project':str(ROOT),'direction':'realista estilizado','source_models':len(list(SOURCE.glob('World_*.gltf'))),'manifest_models':len(world.get('chunks',[])),'instances':len(world.get('instances',[])),'imported_models':len(read('imported_meshes.json',{}))},ensure_ascii=False)

    @toolset_registry.tool_call
    @staticmethod
    def import_world_batch(limit: int=8, radius_metres: float=15.0) -> str:
        """Import at most limit ready source models near the kiosk, preserving PBR textures.

        Args:
            limit: Maximum models per call, from 1 to 32.
            radius_metres: Distance from kiosk; use 10000 for complete exported world.
        """
        world=read('world.json',{})
        mapping=read('imported_meshes.json',{})
        aliases=read('model_aliases.json',{})
        near={}
        for row in world.get('instances',[]):
            source=f"World_{row['mesh_index']:04d}"
            index=int(aliases.get(source,source).split('_')[-1])
            near[index]=min(near.get(index,1e9),distance(row))
        results=[]
        for index in sorted(near,key=near.get):
            name=f'World_{index:04d}'
            path=SOURCE/(name+'.gltf')
            if name in mapping or near[index]>radius_metres or not path.exists():continue
            task=unreal.AssetImportTask()
            task.filename=str(path)
            task.destination_path='/Game/World/Models/'+name
            task.destination_name=name
            task.automated=True
            task.replace_existing=False
            task.save=True
            pipeline=unreal.InterchangeGenericAssetsPipeline()
            pipeline.mesh_pipeline.combine_static_meshes_behavior=unreal.InterchangeCombineStaticMeshesBehavior.ALL
            pipeline.mesh_pipeline.build_nanite=True
            pipeline.common_meshes_properties.bake_meshes=True
            pipeline.material_pipeline.search_location=unreal.InterchangeMaterialSearchLocation.ALL_ASSETS
            task.options=pipeline
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            meshes=[]
            for asset_path in unreal.EditorAssetLibrary.list_assets(task.destination_path):
                asset=unreal.EditorAssetLibrary.load_asset(asset_path)
                if isinstance(asset,unreal.StaticMesh):meshes.append(asset.get_path_name())
            if len(meshes)!=1:raise RuntimeError(f'{name}: expected one static mesh, got {meshes}')
            mapping[name]=meshes[0]
            (DATA/'imported_meshes.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
            results.append(name)
            if len(results)>=max(1,min(32,limit)):break
        return json.dumps({'imported':results,'total':len(mapping)})

    @toolset_registry.tool_call
    @staticmethod
    def validate_imports() -> str:
        """Validate every imported mapping resolves to a native StaticMesh with material slots."""
        mapping=read('imported_meshes.json',{})
        errors=[]
        for name,path in mapping.items():
            mesh=unreal.load_asset(path)
            if not isinstance(mesh,unreal.StaticMesh):errors.append(name+': missing mesh')
            elif not mesh.static_materials:errors.append(name+': no materials')
        return json.dumps({'checked':len(mapping),'errors':errors,'passed':bool(mapping) and not errors})

    @toolset_registry.tool_call
    @staticmethod
    def build_coast_level() -> str:
        """Build and save the native coast level using currently imported assets. Reports missing models."""
        import mare_world_builder,importlib
        importlib.reload(mare_world_builder)
        return json.dumps(mare_world_builder.build())


    @toolset_registry.tool_call
    @staticmethod
    def refresh_project_tools() -> bool:
        """Reload only this project's checked-in MCP tools after a source update."""
        import sys
        toolset_registry.reload_module(sys.modules[__name__])
        return True


_registration=Registration([MareMigrationTools])
_registration.register()
unreal.log('MARE_MCP_READY '+str(ROOT))
