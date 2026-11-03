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


def ensure_seabed():
    """Sand sea floor beyond the modelled beach (03/11, Sergio: "a areia da praia também fica no fundo do mar"): the
    terrain ends about 12 m out (y -5500, z -2 m) and the clear water showed nothing behind it. Two planes with the
    beach material (wet sand under water, caustics): a ramp down to -9 m at y -12000, then a flat floor to the
    horizon. No collision (swimming is unaffected)."""
    import math
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actors.get_all_level_actors():
        if 'MareSeabed' in [str(tag) for tag in actor.tags]:actors.destroy_actor(actor)
    plane=unreal.load_asset('/Engine/BasicShapes/Plane')
    ground=unreal.load_asset('/Game/World/Materials/M_CoastGround_PBR')
    made=[]
    # (label, y0, z0, y1, z1): the ramp starts 20 cm under the end of the terrain so there is no visible step.
    for label,y0,z0,y1,z1 in (('rampa',-5450,-215,-12000,-900),('plano',-12000,-900,-60000,-900)):
        cy,cz=(y0+y1)/2,(z0+z1)/2
        length=math.hypot(y1-y0,z1-z0)
        pitch=math.degrees(math.atan2(z0-z1,y0-y1))
        a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(4000,cy,cz))
        a.set_actor_label('Mar · fundo de areia · '+label)
        a.tags=['MareGenerated','MareSeabed']
        c=a.static_mesh_component
        c.set_static_mesh(plane)
        c.set_material(0,ground)
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        c.set_editor_property('cast_shadow',False)
        a.set_actor_rotation(unreal.Rotator(roll=-pitch,pitch=0,yaw=0),False)
        a.set_actor_scale3d(unreal.Vector(480,length/100,1))
        made.append([label,round(cy),round(cz),round(pitch,2)])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return made


def move_reef(dy=-8500.0, dry=False):
    """Coral reef and its fish moved far out (03/11, Sergio: "tire esses corais, coloque bem mais ao fundo, bem longe
    da praia"): every underwater piece of the old reef (base below -40 cm, within 20 m of the beach line) slides dy
    along y and keeps its height above the sea floor (terrain slope near the shore, the -9 m sand floor out there)."""
    def floor(y):
        if y > -5450:
            return -104 - max(0.0, -4400 - y) * .09
        if y > -12000:
            return -215 - (-5450 - y) * (685 / 6550)
        return -900.0
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    moved, comps = 0, set()
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if 'MareSeabed' in [str(t) for t in actor.tags]:
            continue
        for c in actor.get_components_by_class(unreal.StaticMeshComponent):
            if not c.static_mesh:
                continue
            # Reef pieces only (corals, sea fans, reef fish: World_0537..0600); the pier modules also stand in the water.
            name = c.static_mesh.get_name()
            if not (name.startswith('World_0') and 537 <= int(name[6:] or 0) <= 600):
                continue
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                for i in range(c.get_instance_count()):
                    tr = c.get_instance_transform(i, True)
                    l = tr.translation
                    if -6500 < l.y < -4200 and -400 < l.z < -40:
                        nl = unreal.Vector(l.x, l.y + dy, l.z - floor(l.y) + floor(l.y + dy))
                        if not dry:
                            c.update_instance_transform(i, unreal.Transform(nl, tr.rotation.rotator(), tr.scale3d), True, True, True)
                        moved += 1
                        comps.add(c.static_mesh.get_name())
            else:
                l = c.get_world_location()
                if -6500 < l.y < -4200 and -400 < l.z < -40 and c.get_owner().get_root_component() == c:
                    nl = unreal.Vector(l.x, l.y + dy, l.z - floor(l.y) + floor(l.y + dy))
                    if not dry:
                        actor.set_actor_location(nl, False, False)
                    moved += 1
                    comps.add(c.static_mesh.get_name())
    if not dry:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'moved': moved, 'meshes': sorted(comps)}
