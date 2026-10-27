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
        near[0]=-1.0
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
            pipeline.mesh_pipeline.fallback_collision_type=unreal.InterchangeMeshCollision.NONE
            pipeline.common_meshes_properties.bake_meshes=True
            pipeline.material_pipeline.search_location=unreal.InterchangeMaterialSearchLocation.ALL_ASSETS
            stack=unreal.InterchangePipelineStackOverride()
            stack.set_editor_property("override_pipelines",[unreal.SoftObjectPath(pipeline.get_path_name())])
            task.options=stack
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            meshes=[]
            for asset_path in unreal.EditorAssetLibrary.list_assets(task.destination_path):
                asset=unreal.EditorAssetLibrary.load_asset(asset_path)
                if isinstance(asset,unreal.StaticMesh):meshes.append(asset.get_path_name())
            if len(meshes)!=1:raise RuntimeError(f'{name}: expected one static mesh, got {meshes}')
            mesh=unreal.load_asset(meshes[0])
            body=mesh.get_editor_property('body_setup')
            if not body:raise RuntimeError(name+': missing static collision body')
            body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            if not unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).remove_collisions_with_notification(mesh,False):
                raise RuntimeError(name+': failed to refresh triangle collision')
            unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
            mapping[name]=meshes[0]
            (DATA/'imported_meshes.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
            results.append(name)
            if len(results)>=max(1,min(32,limit)):break
        # Editor time barely advances during synchronous Interchange batches;
        # reclaim unreferenced import packages between batches instead of paging.
        unreal.SystemLibrary.collect_garbage()
        return json.dumps({'imported':results,'total':len(mapping)})

    @toolset_registry.tool_call
    @staticmethod
    def validate_imports() -> str:
        """Validate every imported mapping resolves to a native StaticMesh with material slots."""
        mapping=read('imported_meshes.json',{})
        errors=[]
        editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        for name,path in mapping.items():
            mesh=unreal.load_asset(path)
            if not isinstance(mesh,unreal.StaticMesh):errors.append(name+': missing mesh')
            else:
                if not mesh.static_materials:errors.append(name+': no materials')
                if any(not slot.material_interface for slot in mesh.static_materials):errors.append(name+': empty material slot')
                body=mesh.get_editor_property('body_setup')
                if not body or body.get_editor_property('collision_trace_flag')!=unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
                    errors.append(name+': scenery must use triangle collision')
                if editor.get_simple_collision_count(mesh)+editor.get_convex_collision_count(mesh):errors.append(name+': auto-hull would obstruct navigation')
        return json.dumps({'checked':len(mapping),'errors':errors,'passed':bool(mapping) and not errors})

    @toolset_registry.tool_call
    @staticmethod
    def prepare_world_rendering() -> str:
        """Disable Nanite only on static meshes with unsupported translucent/additive material slots."""
        editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        changed=[]
        for name,path in read('imported_meshes.json',{}).items():
            mesh=unreal.load_asset(path)
            unsupported=any(slot.material_interface and slot.material_interface.get_blend_mode() not in (unreal.BlendMode.BLEND_OPAQUE,unreal.BlendMode.BLEND_MASKED) for slot in mesh.static_materials)
            settings=mesh.get_editor_property('nanite_settings')
            if unsupported and settings.enabled:
                settings.enabled=False
                editor.set_nanite_settings(mesh,settings,True)
                unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
                changed.append(name)
        return json.dumps({'checked':len(read('imported_meshes.json',{})),'nanite_disabled_for_transparency':changed})

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


    @toolset_registry.tool_call
    @staticmethod
    def build_coast_materials() -> str:
        """Build native terrain/ocean PBR shaders and import the authored ocean surface."""
        import mare_materials,importlib
        importlib.reload(mare_materials)
        try:
            ground=mare_materials.build_ground()
            water=mare_materials.build_water()
        except Exception:
            import traceback
            return json.dumps({'error':traceback.format_exc()})
        folder='/Game/World/Ocean'
        if not unreal.EditorAssetLibrary.does_directory_exist(folder):
            task=unreal.AssetImportTask();task.filename=str(ROOT/'SourceArt'/'Ocean'/'Ocean.gltf');task.destination_path=folder;task.automated=True;task.save=True
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        return json.dumps({'ground':ground.get_path_name(),'water':water.get_path_name(),'ocean_assets':list(unreal.EditorAssetLibrary.list_assets(folder))})


    @toolset_registry.tool_call
    @staticmethod
    def inspect_coast_render() -> str:
        """Inspect actual coast mesh materials, Nanite flags and material shader statistics."""
        result=[]
        for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            if not actor.get_actor_label().startswith('Oceano'):continue
            c=actor.static_mesh_component
            mat=c.get_material(0)
            settings=c.static_mesh.get_editor_property('nanite_settings')
            stats=mat.get_editor_property("shading_model")
            result.append({'actor':actor.get_path_name(),'materials':c.get_num_materials(),'material':mat.get_path_name() if mat else None,'nanite_enabled':settings.enabled,'disallow_nanite':c.get_editor_property('disallow_nanite'),'used_with_nanite':mat.get_editor_property('used_with_nanite'),'stats':str(stats)})
        return json.dumps(result)


    @toolset_registry.tool_call
    @staticmethod
    def inspect_lighting() -> str:
        """Report effective lighting and Lumen configuration in the generated level."""
        out=[]
        for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            if not isinstance(actor,unreal.SkyLight):continue
            c=actor.light_component
            out.append({key:str(c.get_editor_property(key)) for key in ('source_type','cubemap','intensity','affects_world','cast_shadows','indirect_lighting_intensity','mobility','visible')})
        out.append({key:unreal.SystemLibrary.get_console_variable_int_value(key) for key in ('r.DynamicGlobalIlluminationMethod','r.Lumen.DiffuseIndirect.Allow','r.SkyLightingQuality')})
        return json.dumps(out)


    @toolset_registry.tool_call
    @staticmethod
    def import_actor_assets() -> str:
        """Import rigged people/animations and authored door/food props for native interactions."""
        catalog=read('actors.json',{})
        for source in sorted((ROOT/'SourceArt'/'Actors').glob('*.glb')):
            if source.stem in catalog and (catalog[source.stem]["skeletal_meshes"] if source.stem.startswith("Human_") else len(catalog[source.stem]["static_meshes"])==1):continue
            task=unreal.AssetImportTask();task.filename=str(source);task.destination_path='/Game/Actors/Combined/'+source.stem;task.automated=True;task.save=True
            pipeline=unreal.InterchangeGenericAssetsPipeline()
            pipeline.common_meshes_properties.bake_meshes=True
            if not source.stem.startswith('Human_'):
                pipeline.mesh_pipeline.combine_static_meshes_behavior=unreal.InterchangeCombineStaticMeshesBehavior.ALL
            else:pipeline.mesh_pipeline.combine_skeletal_meshes_behavior=unreal.InterchangeCombineSkeletalMeshesBehavior.BY_SKELETON
            stack=unreal.InterchangePipelineStackOverride()
            stack.set_editor_property("override_pipelines",[unreal.SoftObjectPath(pipeline.get_path_name())])
            task.options=stack
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            row={'static_meshes':[],'skeletal_meshes':[],'animations':{}}
            for path in unreal.EditorAssetLibrary.list_assets(task.destination_path):
                asset=unreal.load_asset(path)
                if isinstance(asset,unreal.SkeletalMesh):row['skeletal_meshes'].append(asset.get_path_name())
                elif isinstance(asset,unreal.StaticMesh):row['static_meshes'].append(asset.get_path_name())
                elif isinstance(asset,unreal.AnimSequence):row['animations'][asset.get_name()]=asset.get_path_name()
            if source.stem.startswith('Human_') and (not row['skeletal_meshes'] or not row['animations']):raise RuntimeError('Missing rig/animations: '+source.stem)
            if not source.stem.startswith('Human_') and len(row['static_meshes'])!=1:raise RuntimeError('Props must import combined: '+source.stem)
            catalog[source.stem]=row
            (DATA/'actors.json').write_text(json.dumps(catalog,indent=2),encoding='utf-8')
        return json.dumps(catalog)


    @toolset_registry.tool_call
    @staticmethod
    def inspect_people_assets() -> str:
        """Inspect actual person mesh bounds and material slots before placing runtime characters."""
        result={}
        for name,row in read('actors.json',{}).items():
            if not name.startswith('Human_'):continue
            parts=[]
            for path in row['skeletal_meshes']+row['static_meshes']:
                asset=unreal.load_asset(path)
                if isinstance(asset,unreal.StaticMesh):bounds=asset.get_bounds()
                else:bounds=asset.get_bounds()
                parts.append({'path':path,'bounds':str(bounds)})
            result[name]=parts
        return json.dumps(result)


    @toolset_registry.tool_call
    @staticmethod
    def gameplay_probe(phase: str='inspect', dish: str='') -> str:
        """Exercise native interactions in PIE using the explicit isolated QA save profile.

        Args:
            phase: inspect, open_kiosk, tables, capture, position_fridge, position_cupboard, position_customer, position_door, door_inside, door_outside, interact, close_panel, pickup, hire, close_kiosk.
            dish: Ready product id for the pickup phase.
        """
        editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        world=editor.get_game_world()
        if not world:return json.dumps({'pie':False})
        controller=unreal.GameplayStatics.get_player_controller(world,0)
        player=unreal.GameplayStatics.get_player_pawn(world,0)
        if not player:return json.dumps({'pie':True,'player':False})
        if phase not in ('inspect','capture') and '-MareSaveRoot=D:/CodexTemp/' not in unreal.SystemLibrary.get_command_line():
            raise RuntimeError('QA mutations require an isolated D:/CodexTemp save root')
        sim=controller.get_simulation()
        actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.MareServiceTarget)
        people=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.MarePerson)
        def point(v):return [v.x,v.y,v.z]
        def aim(target,position):
            controller.close_phone()
            player.set_actor_location(position,False,False)
            focus=target.get_actor_transform().transform_location(target.get_editor_property('focus_offset'))
            controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(position+unreal.Vector(0,0,64),focus))
        if phase in ('position_fridge','position_cupboard'):
            action='Fridge' if phase.endswith('fridge') else 'Cupboard'
            target=next(a for a in actors if str(a.get_editor_property('action'))==action)
            location=target.get_actor_location();aim(target,unreal.Vector(location.x,-1280,98))
        elif phase=='position_customer':
            customers=[p for p in people if not p.get_editor_property('employee') and p.get_editor_property('counter_index')>=0]
            if not customers:return json.dumps({'pending':'customer arrival'})
            person=customers[0];target=next(a for a in actors if a.get_owner()==person)
            spots=read('world.json',{})['tables'];position=spots[person.get_editor_property('counter_index')]['staff_approach']
            aim(target,unreal.Vector(position[0]*100,position[2]*100,position[1]*100+88))
        elif phase=='position_seated':
            seated=[p for p in people if not p.get_editor_property('employee') and 'EATING' in str(p.get_editor_property('stage')) and p.get_editor_property('table_index')>=0]
            if not seated:return json.dumps({'pending':'seated customer'})
            person=seated[0];location=person.get_actor_location();position=location+person.get_actor_forward_vector()*230
            position.z=100;controller.close_phone();player.set_actor_location(position,False,False)
            controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(position+unreal.Vector(0,0,64),location+unreal.Vector(0,0,60)))
        elif phase in ('position_door','door_inside','door_outside'):
            target=next(a for a in actors if str(a.get_editor_property('action'))=='Door' and a.get_editor_property('auto_close'))
            offset={'position_door':unreal.Vector(-57.5,190,100),'door_inside':unreal.Vector(-57.5,-150,100),'door_outside':unreal.Vector(-57.5,200,100)}[phase]
            aim(target,target.get_actor_transform().transform_location(offset))
        elif phase=='interact':
            target=unreal.MareServiceTarget.find_focused(controller)
            if not target:return json.dumps({'error':'No focused target'})
            target.use(controller)
        elif phase=='close_panel':controller.close_phone()
        elif phase=='phone':controller.toggle_phone()
        elif phase=='pickup':
            if not controller.get_editor_property('phone_open'):return json.dumps({'error':'Physical station panel must be open'})
            if not sim.pickup(dish,False):return json.dumps({'error':'Pickup refused'})
        elif phase=='hire':sim.hire_attendant()
        elif phase=='tables':sim.buy_expansion('kiosk_tables')
        elif phase=='capture':
            unreal.SystemLibrary.execute_console_command(world,'r.HighResScreenshotDelay 32')
            unreal.SystemLibrary.execute_console_command(world,'HighResShot 1280x720 filename=D:/CodexTemp/ue58-service-runtime.png')
        elif phase=='open_kiosk':
            if '-MareSaveRoot=D:/CodexTemp/' not in unreal.SystemLibrary.get_command_line():
                raise RuntimeError('QA mutations require an isolated D:/CodexTemp save root')
            sim.create_company('Maré QA')
            sim.advance_minutes(45)
            sim.set_open(True)
        elif phase=='close_kiosk':sim.set_open(False)
        focus=unreal.MareServiceTarget.find_focused(controller)
        return json.dumps({'pie':True,'time':unreal.GameplayStatics.get_time_seconds(world),'paused':unreal.GameplayStatics.is_game_paused(world),'open':sim.is_open(),'game_mode':str(unreal.GameplayStatics.get_game_mode(world)),'mode_tick':unreal.GameplayStatics.get_game_mode(world).is_actor_tick_enabled(),'location':point(player.get_actor_location()),'velocity':point(player.get_velocity()),'cash':sim.money(),'carry':sim.carry(False),'panel_open':controller.get_editor_property('phone_open'),'focus':str(focus.get_editor_property('action')) if focus else None,'people':[{'id':p.get_name(),'name':p.get_editor_property('person_name'),'stage':str(p.get_editor_property('stage')),'counter':p.get_editor_property('counter_index'),'table':p.get_editor_property('table_index'),'employee':p.get_editor_property('employee'),'plan':list(p.get_editor_property('plan')),'delivered':list(p.get_editor_property('delivered')),'position':point(p.get_actor_location())} for p in people],'doors':[{'name':a.get_editor_property('label'),'opened':a.is_open()} for a in actors if str(a.get_editor_property('action'))=='Door']},ensure_ascii=False)


    @toolset_registry.tool_call
    @staticmethod
    def inspect_navigation() -> str:
        """Inspect navigation bounds/data and projection in the active game or editor world."""
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if world:
            return json.dumps({'runtime':True,'query_skipped':'UE5.8 Python static navigation calls use a CDO during PIE; inspect editor navigation after StopPIE and verify physical customer movement with gameplay_probe.'})
        world=unreal.EditorLevelLibrary.get_editor_world()
        nav=next((item for item in unreal.ObjectIterator(unreal.NavigationSystemV1) if item.get_outer()==world),None)
        result={'system':str(nav),'data':[a.get_path_name() for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.RecastNavMesh)],'volumes':[str(a.get_actor_bounds(False)) for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.NavMeshBoundsVolume)]}
        try:
            result['projection']=str(nav.project_point_to_navigation(world,unreal.Vector(3870,-1635,98),None,None,unreal.Vector(500,500,1000)))
            routes=[]
            for start,end in [(unreal.Vector(4520,-1815,98),unreal.Vector(3870,-1635,98)),(unreal.Vector(3700,-1230,98),unreal.Vector(3870,-1405,98))]:
                path=nav.find_path_to_location_synchronously(world,start,end)
                routes.append({'valid':bool(path and path.is_valid()),'partial':bool(path and path.is_partial()),'points':[[p.x,p.y,p.z] for p in path.path_points] if path else []})
            result['routes']=routes
        except Exception as error:result['projection_error']=str(error)
        return json.dumps(result)


    @toolset_registry.tool_call
    @staticmethod
    def repair_world_navigation_collision(limit: int=32) -> str:
        """Remove imported simple hulls from complex static scenery and refresh navigation collision."""
        subsystem=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        repaired=[]
        pending=[]
        for name,path in sorted(read('imported_meshes.json',{}).items()):
            mesh=unreal.load_asset(path)
            if subsystem.get_simple_collision_count(mesh)+subsystem.get_convex_collision_count(mesh)<=0:continue
            if len(repaired)>=max(1,min(limit,64)):
                pending.append(name);continue
            body=mesh.get_editor_property('body_setup')
            body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            if not subsystem.remove_collisions_with_notification(mesh,False):raise RuntimeError('Collision refresh failed: '+name)
            if subsystem.get_simple_collision_count(mesh)+subsystem.get_convex_collision_count(mesh):raise RuntimeError('Simple hull remains: '+name)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
            repaired.append(name)
        world=unreal.EditorLevelLibrary.get_editor_world()
        unreal.SystemLibrary.execute_console_command(world,'RebuildNavigation')
        return json.dumps({'repaired':repaired,'remaining':len(pending)})

    @toolset_registry.tool_call
    @staticmethod
    def clean_rejected_actor_imports() -> str:
        """Remove only known rejected import folders if no catalog/external asset references them."""
        catalog=json.dumps(read('actors.json',{}))
        removed=[];blocked=[]
        for name in ('dish_fries','dish_fish_portion','player_home_door','Human_0','Human_1','Human_2','Human_3'):
            folder='/Game/Actors/'+name
            if folder+'/' in catalog:blocked.append(folder);continue
            if not unreal.EditorAssetLibrary.does_directory_exist(folder):continue
            files=list(unreal.EditorAssetLibrary.list_assets(folder))
            external=set()
            for asset in files:
                external.update(str(r) for r in unreal.EditorAssetLibrary.find_package_referencers_for_asset(asset,False) if not str(r).startswith(folder+'/'))
            if external:blocked.append({'folder':folder,'references':sorted(external)});continue
            if unreal.EditorAssetLibrary.delete_directory(folder):removed.append(folder)
        return json.dumps({'removed':removed,'blocked':blocked})


_registration=Registration([MareMigrationTools])
_registration.register()
unreal.log('MARE_MCP_READY '+str(ROOT))
