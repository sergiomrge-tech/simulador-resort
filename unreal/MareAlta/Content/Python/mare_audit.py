"""Read-only geometry/animation evidence and isolated-profile camera inspection."""
import json,math,re
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()


def inspect():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:return {'pie':False}
    people=[]
    for p in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.MarePerson):
        mesh=p.mesh;anim=mesh.get_anim_instance()
        people.append({'name':p.person_name,'id':p.get_name(),'stage':str(p.stage),'position':str(p.get_actor_location()),'mesh':mesh.skeletal_mesh_asset.get_path_name(),'animation_class':anim.get_class().get_name() if anim else None,
                       'animation_methods':[n for n in dir(anim) if any(s in n for s in ['position','asset','current_time'])] if anim else [],
                       'bones':{b:str(mesh.get_socket_transform(b,unreal.RelativeTransformSpace.RTS_COMPONENT).translation) for b in ['Head','hand_r','hand_l','foot_r','foot_l']},
                       'parts':[{'mesh':c.static_mesh.get_name(),'socket':str(c.get_attach_socket_name()),'world':str(c.get_world_location()),'relative':str(c.relative_location),'transform':str(c.get_world_transform()),'visible':c.visible,'hidden':c.hidden_in_game,'mobility':str(c.mobility)} for c in p.get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh]})
    data=ROOT/'Content/Data';source=json.loads((data/'world.json').read_text(encoding='utf-8-sig'))
    mapping=json.loads((data/'imported_meshes.json').read_text(encoding='utf-8-sig'));aliases=json.loads((data/'model_aliases.json').read_text(encoding='utf-8-sig'))
    props=[]
    from mare_world_builder import transform
    for i,row in enumerate(source['instances']):
        x,y,z=row['transform']['position']
        if row['name'] not in ['wicker_basket_02_base','cup_plastic'] or not (34<x<42 and -18<z<-8):continue
        name=f"World_{row['mesh_index']:04d}";path=mapping[aliases.get(name,name)];mesh=unreal.load_asset(path);b=mesh.get_bounds();t=transform(row['transform'])
        corners=[t.transform_location(b.origin+unreal.Vector(dx*b.box_extent.x,dy*b.box_extent.y,dz*b.box_extent.z)) for dx in (-1,1) for dy in (-1,1) for dz in (-1,1)]
        props.append({'row':i,'name':row['name'],'pivot':row['transform']['position'],'bounds_min':[min(getattr(v,k) for v in corners) for k in ['x','y','z']],'bounds_max':[max(getattr(v,k) for v in corners) for k in ['x','y','z']]})
    catalog=json.loads((data/'actors.json').read_text(encoding='utf-8-sig'));products={}
    for name,row in catalog.items():
        if name.startswith('Dish_') and row.get('static_meshes'):
            b=unreal.load_asset(row['static_meshes'][0]).get_bounds();products[name]={'origin':str(b.origin),'extent':str(b.box_extent)}
    return {'pie':True,'people':people,'props':props,'products':products}


def view(name,capture=False):
    if '-MareSaveRoot=D:/CodexTemp/' not in unreal.SystemLibrary.get_command_line():raise RuntimeError('Disposable QA profile required')
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:return {'pie':False}
    views={'grip_close':((2750,-2720,100),(-5,90,0)),
           'kiosk':((3800,-1200,100),(-6,-90,0)),
           'counter':((3800,-1380,100),(-7,-90,0)),
           'front':((3800,-2350,100),(-4,90,0)),
           'sea':((3800,-2600,100),(-3,-90,0)),
           'village':((4800,2780,110),(-4,0,0)),
           'home':((4520,2120,100),(-8,25,0)),
           'bathroom':((4770,1580,100),(-8,90,0)),
           'pier':((7200,-3800,140),(-5,-90,0))}
    if name not in views:raise ValueError(name)
    pc=unreal.GameplayStatics.get_player_controller(world,0);pawn=unreal.GameplayStatics.get_player_pawn(world,0)
    if capture:
        folder=Path('D:/CodexTemp/ue58-world-audit-20261028');folder.mkdir(exist_ok=True)
        unreal.SystemLibrary.execute_console_command(world,f'HighResShot 1280x720 filename={folder/name}.png')
        return {'capture':str(folder/(name+'.png'))}
    pc.close_phone();p,r=views[name]
    sim=pc.get_simulation();sim.save()
    match=re.search(r'-MareSaveRoot=(?:"([^"]+)"|(\S+))',unreal.SystemLibrary.get_command_line())
    state=json.loads((Path(match.group(1) or match.group(2))/'slot1.json').read_text(encoding='utf-8-sig'))
    sim.advance_minutes(720-state['minutes'])
    unreal.GameplayStatics.get_game_mode(world).set_actor_tick_enabled(False)
    pawn.character_movement.set_movement_mode(unreal.MovementMode.MOVE_FLYING)
    pawn.set_actor_location(unreal.Vector(*p),False,False)
    pc.set_control_rotation(unreal.Rotator(pitch=r[0],yaw=r[1],roll=r[2]))
    return {'view':name,'position':p}


def fixture(mode):
    if '-MareSaveRoot=D:/CodexTemp/' not in unreal.SystemLibrary.get_command_line():raise RuntimeError('Disposable QA profile required')
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:return {'pie':False}
    previous=[a for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.MarePerson) if 'MareAuditFixture' in [str(t) for t in a.tags]]
    if mode=='clear':
        for p in previous:p.destroy_actor()
        return {'cleared':len(previous)}
    if previous:return {'existing':[p.get_name() for p in previous]}
    dishes=['coco_gelado','coco_gelado','suco','batata_frita'] if mode=='fallback' else ['coco_gelado','suco','batata_frita','sorvete_morango']
    for i,dish in enumerate(dishes):
        p=unreal.MarePreviewQA.spawn_inspection_person(world,unreal.Vector(2750+i*150,-2500,88),i,dish)
        if p is None:raise RuntimeError('Runtime fixture refused')
        if mode=='fallback' and i%2==1:
            for part in p.get_components_by_class(unreal.StaticMeshComponent):
                if part.static_mesh and part.static_mesh.get_name().startswith('Dish_'):part.set_editor_property('disallow_nanite',True)
    pc=unreal.GameplayStatics.get_player_controller(world,0);hero=unreal.GameplayStatics.get_player_pawn(world,0)
    hero.character_movement.set_movement_mode(unreal.MovementMode.MOVE_FLYING)
    hero.set_actor_location(unreal.Vector(2970,-2930,100),False,False);pc.set_control_rotation(unreal.Rotator(pitch=-5,yaw=90,roll=0))
    return {'fixtures':4}
