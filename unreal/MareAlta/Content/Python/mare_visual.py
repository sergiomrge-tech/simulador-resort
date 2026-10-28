"""Targeted visual pass: natural exposure, contact shadows and practical lights."""
import unreal
def refine():
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors=actors.get_all_level_actors()
    for actor in all_actors:
        if 'MareVisualExtra' in [str(t) for t in actor.tags]:actors.destroy_actor(actor)
    touched=[]
    for actor in actors.get_all_level_actors():
        if isinstance(actor,unreal.DirectionalLight):
            actor.set_actor_rotation(unreal.Rotator(pitch=-42,yaw=-30,roll=0),False)
            actor.tags=list(actor.tags)+['MareSun']
            light=actor.light_component
            light.set_editor_property('contact_shadow_length',.15)
            light.set_editor_property('light_source_angle',.65)
        if isinstance(actor,unreal.RectLight):
            actor.tags=list(actor.tags)+['MarePractical']
            actor.set_actor_rotation(unreal.Rotator(pitch=-90,yaw=0,roll=0),False)
        if isinstance(actor,unreal.PlayerStart):actor.set_actor_rotation(unreal.Rotator(pitch=0,yaw=-90,roll=0),False)
        if isinstance(actor,unreal.PostProcessVolume):
            settings=actor.settings
            for key,value in {'auto_exposure_min_brightness':-2.,'auto_exposure_max_brightness':14.,'auto_exposure_low_percent':70.,'auto_exposure_high_percent':95.,'auto_exposure_speed_up':3.,'auto_exposure_speed_down':2.,'local_exposure_shadow_contrast_scale':.4,'ambient_occlusion_intensity':.65,'ambient_occlusion_radius':70.,'bloom_intensity':.15}.items():
                settings.set_editor_property('override_'+key,True);settings.set_editor_property(key,value)
            actor.settings=settings
        for component in actor.get_components_by_class(unreal.PrimitiveComponent):
            if isinstance(component,(unreal.StaticMeshComponent,unreal.InstancedStaticMeshComponent)):
                component.set_editor_property('cast_contact_shadow',True)
        touched.append(actor.get_name())
    moon=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(),unreal.Rotator(pitch=-40,yaw=140,roll=0))
    moon.set_actor_label('Luar · luz natural');moon.tags=['MareGenerated','MareVisualExtra','MareMoon']
    moon.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    moon.light_component.set_editor_property('intensity',0.)
    moon.light_component.set_editor_property('light_color',unreal.Color(235,242,255,255))
    fill=actors.spawn_actor_from_class(unreal.RectLight,unreal.Vector(3800,-1230,160),unreal.Rotator(pitch=-15,yaw=-90,roll=0))
    fill.set_actor_label('Quiosque · preenchimento indireto');fill.tags=['MareGenerated','MareVisualExtra','MarePractical','MareBounce']
    fill.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    for key,value in {'intensity':2500.,'attenuation_radius':520.,'source_width':300.,'source_height':140.,'cast_shadows':False,'use_temperature':True,'temperature':5200.}.items():fill.light_component.set_editor_property(key,value)
    for name,position in [('Sala',unreal.Vector(4600,1990,240)),('Cozinha',unreal.Vector(4780,2310,240)),('Banheiro',unreal.Vector(4570,2940,240))]:
        light=actors.spawn_actor_from_class(unreal.RectLight,position,unreal.Rotator(pitch=-90,yaw=0,roll=0))
        light.set_actor_label('Casa · luz '+name);light.tags=['MareGenerated','MareVisualExtra','MarePractical','MareHomeLight']
        comp=light.light_component;comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        comp.set_editor_property('intensity_units',unreal.LightUnits.LUMENS);comp.set_editor_property('intensity',120.)
        comp.set_editor_property('attenuation_radius',520.);comp.set_editor_property('source_width',70.);comp.set_editor_property('source_height',70.)
        comp.set_editor_property('use_temperature',True);comp.set_editor_property('temperature',4800.)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'actors_reviewed':len(touched),'home_practicals':3,'moon':True}
