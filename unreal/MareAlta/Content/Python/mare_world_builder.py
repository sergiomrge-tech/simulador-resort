"""Construct the native level from the source manifest; metres/Y-up -> cm/Z-up.
Axis conversion was checked against Calibration.glb imported by UE 5.8.3.
"""
import json,math
from collections import defaultdict
from pathlib import Path
import unreal
from editor_toolset.toolsets.actor import ActorTools

ROOT=Path(unreal.Paths.project_dir()).resolve()

def transform(row):
    p=row['position'];bx,by,bz=row['basis'];axes=[[bx[0],bx[2],bx[1]],[bz[0],bz[2],bz[1]],[by[0],by[2],by[1]]]
    scales=[math.sqrt(sum(v*v for v in axis)) for axis in axes]
    determinant=(axes[0][0]*(axes[1][1]*axes[2][2]-axes[1][2]*axes[2][1])-axes[0][1]*(axes[1][0]*axes[2][2]-axes[1][2]*axes[2][0])+axes[0][2]*(axes[1][0]*axes[2][1]-axes[1][1]*axes[2][0]))
    if determinant<0:scales[0]*=-1
    if min(abs(v) for v in scales)<1e-7:return None
    vectors=[unreal.Vector(*(a/max(abs(s),1e-7)*(1 if s>0 else -1) for a in axis)) for axis,s in zip(axes,scales)]
    rotation=unreal.MathLibrary.make_rotation_from_axes(*vectors)
    return unreal.Transform(unreal.Vector(p[0]*100,p[2]*100,p[1]*100),rotation,unreal.Vector(*scales))

def build():
    data=ROOT/'Content'/'Data'
    world=json.loads((data/'world.json').read_text(encoding='utf-8-sig'))
    mapping=json.loads((data/'imported_meshes.json').read_text(encoding='utf-8-sig'))
    aliases=json.loads((data/'model_aliases.json').read_text(encoding='utf-8-sig'))
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    path='/Game/Maps/Coast'
    if unreal.EditorAssetLibrary.does_asset_exist(path):level.load_level(path)
    else:level.new_level(path)
    for actor in actors.get_all_level_actors():
        if 'MareGenerated' in [str(tag) for tag in actor.tags]:actors.destroy_actor(actor)
    groups=defaultdict(list)
    missing=set()
    for row in world['instances']:
        name=f"World_{row['mesh_index']:04d}";canonical=aliases.get(name,name)
        native=mapping.get(canonical,mapping.get(name))
        if not native:missing.add(canonical);continue
        groups[(native,row.get('region',''))].append(row)
    count=0
    mesh_editor=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    for (native,region),rows in groups.items():
        mesh=unreal.load_asset(native)
        body=mesh.get_editor_property('body_setup')
        if body and body.get_editor_property('collision_trace_flag')!=unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
            body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
        # Recast exports convex hulls even when physics uses complex triangles.
        # Imported auto-hulls can bridge doors and turn the whole coast into a box.
        if mesh_editor.get_simple_collision_count(mesh)+mesh_editor.get_convex_collision_count(mesh)>0:
            if not mesh_editor.remove_collisions_with_notification(mesh,False):raise RuntimeError('Cannot refresh scenery collision: '+native)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh,False)
        actor=actors.spawn_actor_from_class(unreal.Actor,unreal.Vector())
        actor.set_actor_label('Maré · '+rows[0]['name'])
        actor.tags=['MareGenerated','Region_'+region]
        component=ActorTools.add_component(actor,unreal.InstancedStaticMeshComponent.static_class(),"Instances")
        component.set_static_mesh(mesh)
        if any(row['name']=='Ground' for row in rows):
            ground=unreal.load_asset('/Game/World/Materials/M_CoastGround_PBR')
            if ground:component.set_material(0,ground)
        component.set_mobility(unreal.ComponentMobility.STATIC)
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        component.set_editor_property('cast_shadow',True)
        instances=[t for row in rows if (t:=transform(row['transform'])) is not None]
        component.add_instances(instances,False,True)
        count+=len(instances)
    def spawn(cls,name,location=unreal.Vector(),rotation=unreal.Rotator()):
        a=actors.spawn_actor_from_class(cls,location,rotation);a.set_actor_label(name);a.tags=['MareGenerated'];return a
    ocean_assets=unreal.EditorAssetLibrary.list_assets('/Game/World/Ocean')
    for ocean_path in ocean_assets:
        ocean_mesh=unreal.load_asset(ocean_path)
        if isinstance(ocean_mesh,unreal.StaticMesh):
            ocean=spawn(unreal.StaticMeshActor,'Oceano · água costeira')
            settings=ocean_mesh.get_editor_property('nanite_settings')
            if settings.enabled:
                settings.enabled=False
                unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).set_nanite_settings(ocean_mesh,settings,True)
                unreal.EditorAssetLibrary.save_loaded_asset(ocean_mesh)
            ocean.static_mesh_component.set_static_mesh(ocean_mesh)
            ocean.static_mesh_component.set_editor_property('disallow_nanite',True)
            ocean.static_mesh_component.set_material(0,unreal.load_asset('/Game/World/Materials/M_CoastalWater_PBR'))
            ocean.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            ocean.static_mesh_component.set_editor_property('use_default_collision',False)
            ocean.static_mesh_component.set_collision_profile_name('NoCollision')
            ocean.static_mesh_component.set_editor_property('cast_shadow',False)
            ocean.static_mesh_component.set_editor_property('bounds_scale',1.1)
            break
    sun=spawn(unreal.DirectionalLight,'Sol · luz natural',rotation=unreal.Rotator(pitch=-42,yaw=-30,roll=0))
    sun.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sun.light_component.set_editor_property('intensity',65000.)
    sun.light_component.set_editor_property('light_color',unreal.Color(255,248,235,255))
    sun.light_component.set_editor_property('atmosphere_sun_light',True)
    sun.light_component.set_editor_property('light_source_angle',1.2)
    sky=spawn(unreal.SkyLight,'Céu · preenchimento suave')
    sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_CAPTURED_SCENE)
    sky.light_component.set_editor_property('real_time_capture',True)
    sky.light_component.set_editor_property('intensity',1.)
    spawn(unreal.SkyAtmosphere,'Atmosfera da costa')
    spawn(unreal.VolumetricCloud,'Nuvens costeiras')
    fog=spawn(unreal.ExponentialHeightFog,'Bruma marítima').get_component_by_class(unreal.ExponentialHeightFogComponent)
    fog.set_editor_property('fog_density',.0008)
    fog.set_editor_property('start_distance',5000.)
    post=spawn(unreal.PostProcessVolume,'Exposição e cor neutra')
    post.set_editor_property('unbound',True)
    settings=post.settings
    settings.set_editor_property('override_auto_exposure_method',True)
    settings.set_editor_property('auto_exposure_method',unreal.AutoExposureMethod.AEM_HISTOGRAM)
    settings.set_editor_property('override_auto_exposure_apply_physical_camera_exposure',True)
    settings.set_editor_property('auto_exposure_apply_physical_camera_exposure',True)
    settings.set_editor_property('override_depth_of_field_fstop',True)
    settings.set_editor_property('depth_of_field_fstop',8.)
    settings.set_editor_property('override_camera_shutter_speed',True)
    settings.set_editor_property('camera_shutter_speed',60.)
    settings.set_editor_property('override_camera_iso',True)
    settings.set_editor_property('camera_iso',100.)
    settings.set_editor_property('override_auto_exposure_bias',True)
    settings.set_editor_property('auto_exposure_bias',0.)
    for key,value in {'auto_exposure_min_brightness':7.,'auto_exposure_max_brightness':14.,'auto_exposure_low_percent':10.,'auto_exposure_high_percent':60.,'local_exposure_shadow_contrast_scale':.65,'local_exposure_highlight_contrast_scale':.6}.items():
        settings.set_editor_property('override_'+key,True)
        settings.set_editor_property(key,value)
    post.settings=settings
    fill=spawn(unreal.RectLight,'Luminária do quiosque',unreal.Vector(3800,-1300,245),unreal.Rotator(pitch=-90,yaw=0,roll=0))
    fill.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    fill.light_component.set_editor_property('intensity_units',unreal.LightUnits.LUMENS)
    fill.light_component.set_editor_property('intensity',4500.)
    fill.light_component.set_editor_property('source_width',350.)
    fill.light_component.set_editor_property('source_height',230.)
    fill.light_component.set_editor_property('attenuation_radius',750.)
    fill.light_component.set_editor_property('use_temperature',True)
    fill.light_component.set_editor_property('temperature',5200.)
    start=spawn(unreal.PlayerStart,'Entrada do quiosque',unreal.Vector(3800,-1200,100),unreal.Rotator(pitch=0,yaw=-90,roll=0))
    target_class=unreal.load_class(None,'/Script/MareAlta.MareServiceTarget')
    if target_class:
        for action,label,position in [('Fridge','Geladeira',unreal.Vector(3920,-1120,105)),('Cupboard','Porções prontas',unreal.Vector(3800,-1120,85)),('Bed','Dormir e encerrar o dia',unreal.Vector(4385,1945,90))]:
            target=spawn(target_class,label,position)
            target.set_editor_property('action',action);target.set_editor_property('label',label)
        actor_catalog=json.loads((data/'actors.json').read_text(encoding='utf-8-sig'))
        leaf=unreal.load_asset(actor_catalog['player_home_door']['static_meshes'][0])
        for row in world['doors']:
            target=spawn(target_class,row['label'])
            target.set_actor_transform(transform(row['transform']),False,False)
            target.set_editor_property('action','Door');target.set_editor_property('label',row['label'])
            target.set_editor_property('auto_close',row['auto_close']);target.set_editor_property('focus_offset',unreal.Vector(-57.5,0,110))
            target.get_editor_property('door_mesh').set_static_mesh(leaf)
            target.get_editor_property('door_mesh').set_relative_scale3d(unreal.Vector(1.04 if row['auto_close'] else 1,1,1.065))
    nav=spawn(unreal.NavMeshBoundsVolume,'Navegação do quiosque e da casa',unreal.Vector(4200,300,250))
    nav.set_actor_scale3d(unreal.Vector(30,45,10))
    origin,extent=nav.get_actor_bounds(False)
    if extent.x<100:raise RuntimeError('Navigation bounds have no brush geometry')
    navigation=unreal.NavigationSystemV1.get_navigation_system(unreal.EditorLevelLibrary.get_editor_world())
    if navigation:navigation.on_navigation_bounds_updated(nav)
    unreal.SystemLibrary.execute_console_command(unreal.EditorLevelLibrary.get_editor_world(),'RebuildNavigation')
    mode=unreal.load_class(None,'/Script/MareAlta.MareGameMode')
    if mode:unreal.EditorLevelLibrary.get_editor_world().get_world_settings().set_editor_property('default_game_mode',mode)
    import mare_expansions
    mare_expansions.ensure_pool_lot()
    import mare_water
    mare_water.ensure_volume()
    import mare_visual
    mare_visual.refine()
    import mare_signs
    mare_signs.build()
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(3900,-1130,165),unreal.Rotator(pitch=-8,yaw=-100,roll=0))
    level.save_current_level()
    result={'map':path,'model_groups':len(groups),'instances':count,'missing_models':len(missing),'visual_approval':False}
    (data/'map_build.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
