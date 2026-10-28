"""Native water physics under the rendered ocean; keeps the pier and dry land outside."""
import unreal

def ensure_volume():
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    oceans=[]
    for actor in actors.get_all_level_actors():
        if 'MareWater' in [str(tag) for tag in actor.tags]:actors.destroy_actor(actor)
        if isinstance(actor,unreal.StaticMeshActor) and actor.static_mesh_component.static_mesh and actor.static_mesh_component.static_mesh.get_path_name().startswith('/Game/World/Ocean/'):
            component=actor.static_mesh_component
            component.set_editor_property('use_default_collision',False)
            component.set_collision_profile_name('NoCollision')
            component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            oceans.append(actor.get_actor_label())
    water=actors.spawn_actor_from_class(unreal.PhysicsVolume,unreal.Vector(0,-123200,-5030))
    water.set_actor_label('Mar · natação e flutuação')
    water.tags=['MareGenerated','MareWater']
    water.set_actor_scale3d(unreal.Vector(1000,1200,50))
    water.set_editor_property('water_volume',True)
    water.set_editor_property('physics_on_contact',False)
    water.set_editor_property('priority',100)
    water.set_editor_property('fluid_friction',.6)
    origin,extent=water.get_actor_bounds(False)
    if extent.x<90000 or abs(origin.z+extent.z+30)>1:
        raise RuntimeError('Water brush bounds do not match the rendered sea')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'volume':water.get_path_name(),'surface_z_cm':origin.z+extent.z,'origin':str(origin),'extent':str(extent),'non_solid_oceans':oceans}
