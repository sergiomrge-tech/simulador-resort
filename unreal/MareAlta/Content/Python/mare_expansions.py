"""Repair missing ownership metadata in the original full-unlock Godot export.

Preserves every canonical mesh and instance. Splits only affected ISM groups;
does not reimport models or remove any asset. Regionless commercial geometry was
exported from --v1. Semantic block markers are checked before modifying data.
"""
import json
from collections import defaultdict
from pathlib import Path
import unreal
from editor_toolset.toolsets.actor import ActorTools
from mare_world_builder import transform

ROOT=Path(unreal.Paths.project_dir()).resolve()


def classify(world):
    rows=world['instances']
    hotel=next(i for i,r in enumerate(rows) if r['name']=='hotel_tower')
    operations=next(i for i in range(hotel+1,len(rows)) if rows[i]['name']=='Cube' and rows[i]['transform']['position'][0]>30 and rows[i]['transform']['position'][2]<0)
    if not any(r['name']=='hotel_gym' for r in rows[hotel:operations]):
        raise RuntimeError('Hotel export boundary does not match the canonical source')
    blocks=[('Biz_sorveteria','biz_gelato','biz_booth'),
            ('Biz_aluguel','biz_booth','biz_canopy'),
            ('Biz_surfe','biz_canopy','biz_food_truck'),
            ('Biz_food_truck','biz_food_truck','biz_booth'),
            ('Biz_souvenir','biz_booth','hotel_tower')]
    business_start=next(i for i,r in enumerate(rows) if r['name']=='biz_gelato')
    cursor=business_start
    for region,start_name,end_name in blocks:
        if rows[cursor]['name']!=start_name:raise RuntimeError('Business boundary mismatch: '+region)
        end=next(i for i in range(cursor+1,hotel+1) if rows[i]['name']==end_name)
        for row in rows[cursor:end]:row['region']=region
        cursor=end
    for row in rows[hotel:operations]:row['region']='grand_hotel'
    for row in world['texts']:
        text=row['text']
        if any(k in text for k in ['★★★★★','LOBBY','RESTAURANTE','ACADEMIA','BAR DA PISCINA']):row['region']='grand_hotel'
        for word,region in [('Gelato','sorveteria'),('Aluguel de','aluguel'),('Escolinha','surfe'),('Food truck','food_truck'),('souvenires','souvenir')]:
            if word.lower() in text.lower():row['region']='Biz_'+region
    return {'hotel_instances':operations-hotel,'business_instances':hotel-business_start}


def ensure_pool_lot():
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    lot=next((a for a in actors.get_all_level_actors() if 'MarePoolLot' in [str(t) for t in a.tags]),None)
    if lot is None:lot=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,400,-19))
    lot.set_actor_label('Terreno da futura piscina · gramado contínuo')
    lot.tags=['MareGenerated','MarePoolLot','Lot_pool']
    comp=lot.static_mesh_component
    comp.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    comp.set_material(0,unreal.load_asset('/Game/World/Materials/M_CoastGround_PBR'))
    lot.set_actor_scale3d(unreal.Vector(12.4,8.4,.4))
    comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)


def repair():
    data=ROOT/'Content/Data'
    world=json.loads((data/'world.json').read_text(encoding='utf-8-sig'))
    original=[r['region'] for r in world['instances']]
    result=classify(world)
    mapping=json.loads((data/'imported_meshes.json').read_text(encoding='utf-8-sig'))
    aliases=json.loads((data/'model_aliases.json').read_text(encoding='utf-8-sig'))
    def native(row):
        source='World_'+str(row['mesh_index']).zfill(4)
        return mapping[aliases.get(source,source)]
    affected={native(row) for before,row in zip(original,world['instances']) if before!=row['region']}
    # Include classified groups on repeat runs so this operation stays idempotent.
    affected.update(native(r) for r in world['instances'] if r['region']=='grand_hotel' or r['region'].startswith('Biz_'))
    groups=defaultdict(list)
    for row in world['instances']:
        path=native(row)
        if path in affected:groups[(path,row['region'])].append(row)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing={}
    before_count=0
    for actor in actors.get_all_level_actors():
        comp=actor.get_component_by_class(unreal.InstancedStaticMeshComponent)
        if not comp:continue
        before_count+=comp.get_instance_count()
        if not comp.static_mesh or comp.static_mesh.get_path_name() not in affected:continue
        regions=[str(t)[7:] for t in actor.tags if str(t).startswith('Region_')]
        if regions:existing[(comp.static_mesh.get_path_name(),regions[0])]=(actor,comp)
    for key in set(existing)|set(groups):
        rows=groups.get(key,[])
        if key in existing:actor,comp=existing[key];comp.clear_instances()
        else:
            actor=actors.spawn_actor_from_class(unreal.Actor,unreal.Vector())
            comp=ActorTools.add_component(actor,unreal.InstancedStaticMeshComponent.static_class(),'Instances')
            comp.set_static_mesh(unreal.load_asset(key[0]))
            comp.set_mobility(unreal.ComponentMobility.STATIC)
            comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            comp.set_editor_property('cast_shadow',True)
        actor.tags=['MareGenerated','Region_'+key[1]]
        actor.set_actor_label('Maré · '+(rows[0]['name'] if rows else 'grupo vazio preservado'))
        if rows:comp.add_instances([transform(r['transform']) for r in rows],False,True)
    after_count=sum(c.get_instance_count() for a in actors.get_all_level_actors() if (c:=a.get_component_by_class(unreal.InstancedStaticMeshComponent)))
    if before_count!=after_count:raise RuntimeError('Instance conservation failed: '+str((before_count,after_count)))
    (data/'world.json').write_text(json.dumps(world,ensure_ascii=False,indent='\t'),encoding='utf-8')
    ensure_pool_lot()
    import mare_signs
    mare_signs.build()
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    result.update(instances_before=before_count,instances_after=after_count,groups_reclassified=len(groups))
    map_path=data/'map_build.json'
    info=json.loads(map_path.read_text(encoding='utf-8'))
    info.update(model_groups=sum(1 for a in actors.get_all_level_actors() if (c:=a.get_component_by_class(unreal.InstancedStaticMeshComponent)) and c.get_instance_count()>0),instances=after_count,pool_lot=True)
    map_path.write_text(json.dumps(info,indent=2),encoding='utf-8')
    return result
