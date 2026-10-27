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
    for (native,region),rows in groups.items():
        mesh=unreal.load_asset(native)
        actor=actors.spawn_actor_from_class(unreal.Actor,unreal.Vector())
        actor.set_actor_label('Maré · '+rows[0]['name'])
        actor.tags=['MareGenerated','Region_'+region]
        component=ActorTools.add_component(actor,unreal.InstancedStaticMeshComponent.static_class(),"Instances")
        component.set_static_mesh(mesh)
        component.set_mobility(unreal.ComponentMobility.STATIC)
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        component.set_editor_property('cast_shadow',True)
        instances=[t for row in rows if (t:=transform(row['transform'])) is not None]
        component.add_instances(instances,False,True)
        count+=len(instances)
    def spawn(cls,name,location=unreal.Vector(),rotation=unreal.Rotator()):
        a=actors.spawn_actor_from_class(cls,location,rotation);a.set_actor_label(name);a.tags=['MareGenerated'];return a
    sun=spawn(unreal.DirectionalLight,'Sol · luz natural',rotation=unreal.Rotator(-42,-30,0))
    sun.light_component.set_editor_property('intensity',65000.)
    sun.light_component.set_editor_property('light_color',unreal.Color(255,248,235,255))
    sun.light_component.set_editor_property('atmosphere_sun_light',True)
    sun.light_component.set_editor_property('light_source_angle',1.2)
    sky=spawn(unreal.SkyLight,'Céu · preenchimento suave')
    sky.light_component.set_editor_property('real_time_capture',True)
    sky.light_component.set_editor_property('intensity',.65)
    spawn(unreal.SkyAtmosphere,'Atmosfera da costa')
    spawn(unreal.VolumetricCloud,'Nuvens costeiras')
    spawn(unreal.ExponentialHeightFog,'Bruma marítima').get_component_by_class(unreal.ExponentialHeightFogComponent).set_editor_property('fog_density',.008)
    post=spawn(unreal.PostProcessVolume,'Exposição e cor neutra')
    post.set_editor_property('unbound',True)
    settings=post.settings
    settings.set_editor_property('override_auto_exposure_method',True)
    settings.set_editor_property('auto_exposure_method',unreal.AutoExposureMethod.AEM_HISTOGRAM)
    settings.set_editor_property('override_auto_exposure_bias',True)
    settings.set_editor_property('auto_exposure_bias',0.)
    post.settings=settings
    start=spawn(unreal.PlayerStart,'Entrada do quiosque',unreal.Vector(3800,-1200,100),unreal.Rotator(0,-90,0))
    mode=unreal.load_class(None,'/Script/MareAlta.MareGameMode')
    if mode:unreal.EditorLevelLibrary.get_editor_world().get_world_settings().set_editor_property('default_game_mode',mode)
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(3900,-1130,165),unreal.Rotator(-8,-100,0))
    level.save_current_level()
    result={'map':path,'model_groups':len(groups),'instances':count,'missing_models':len(missing),'visual_approval':False}
    (data/'map_build.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
