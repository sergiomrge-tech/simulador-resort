"""Editor-authored grass coverage on exposed inland terrain, never on built surfaces."""
import json
import math
import random
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()


def grass_material(source, name):
    """Keep the imported atlas/normal/cutout, recoloring only the generated lawn."""
    from mare_materials import custom, MEL
    path = '/Game/Graphics/Grass/Materials/M_'+name
    result = unreal.load_asset(path)
    if result:return result
    root = source
    while isinstance(root, unreal.MaterialInstanceConstant):root=root.get_editor_property('parent')
    if not isinstance(root, unreal.Material):raise RuntimeError('Unresolved grass material root')
    shader = unreal.EditorAssetLibrary.duplicate_asset(root.get_path_name(),path+'_Shader')
    if isinstance(source, unreal.MaterialInstanceConstant):
        result=unreal.EditorAssetLibrary.duplicate_asset(source.get_path_name(),path)
        result.set_editor_property('parent',shader)
    else:
        result=shader
    original = MEL.get_material_property_input_node(shader, unreal.MaterialProperty.MP_BASE_COLOR)
    output = MEL.get_material_property_input_node_output_name(shader, unreal.MaterialProperty.MP_BASE_COLOR)
    if not original:raise RuntimeError('Missing grass atlas color')
    # Preserve the full source shader, including cutouts and wind, then route
    # its existing color through a natural green hue with texture variation.
    node = custom(shader,'float l=dot(Base,float3(.2126,.7152,.0722)); return float3(.055,.20,.025)*clamp(l*3,.65,1.5);',
                  unreal.CustomMaterialOutputType.CMOT_FLOAT3,{'Base':original})
    if output: MEL.connect_material_expressions(original,output,node,'Base')
    MEL.connect_material_property(node,'',unreal.MaterialProperty.MP_BASE_COLOR)
    shader.set_editor_property('used_with_instanced_static_meshes',True)
    shader.set_editor_property('used_with_nanite',True)
    errors=list(MEL.recompile_material(shader))
    if errors:raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(shader,False)
    unreal.EditorAssetLibrary.save_loaded_asset(result,False)
    return result


def excluded(x, y, manifest):
    """Centimetres in UE XY. Leave generous clearances around paths/doors."""
    if y < -500:
        return True
    for bx, by, width, depth in manifest['blocks']:
        if abs(x-bx*100) < width*50+60 and abs(y-by*100) < depth*50+60:
            return True
    routes = manifest['paths']+[manifest['points']['kiosk_approach']]
    for route in routes:
        for a, b in zip(route, route[1:]):
            ax, ay, bx, by = a[0]*100, a[2]*100, b[0]*100, b[2]*100
            dx, dy = bx-ax, by-ay
            t = max(0, min(1, ((x-ax)*dx+(y-ay)*dy)/max(1, dx*dx+dy*dy)))
            if math.hypot(x-ax-t*dx, y-ay-t*dy) < 160:
                return True
    return False


def build():
    """Generate fixed editor points from actual ground hits; preserve existing flora."""
    from editor_toolset.toolsets.actor import ActorTools
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if '/Coast.' not in world.get_path_name():
        raise RuntimeError('Generate only in the approved Coast map')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    manifest = json.loads((ROOT/'Content/Data/world.json').read_text(encoding='utf-8-sig'))
    mapping = json.loads((ROOT/'Content/Data/imported_meshes.json').read_text(encoding='utf-8-sig'))
    aliases = json.loads((ROOT/'Content/Data/model_aliases.json').read_text(encoding='utf-8-sig'))
    ground = next(a for a in actors.get_all_level_actors() if a.get_actor_label().endswith(' Ground'))
    ground_component = ground.get_component_by_class(unreal.InstancedStaticMeshComponent)
    material = unreal.load_asset('/Game/World/Materials/M_CoastGround_PBR')
    ground_component.set_material(0, material)
    ignore = [a for a in actors.get_all_level_actors() if any(
        term in a.get_actor_label().lower() for term in ('grass', 'bush', 'fern', 'palm', 'tree', 'plant', 'pcg'))]
    center, extent = ground.get_actor_bounds(False)
    rng = random.Random(20261029)
    points = [[], []]
    rejected = {'mask': 0, 'surface': 0, 'slope': 0}
    samples = []
    spacing = 30
    for xi in range(math.ceil((center.x-extent.x)/spacing), math.floor((center.x+extent.x)/spacing)):
        for yi in range(math.ceil(-500/spacing), math.floor((center.y+extent.y)/spacing)):
            x, y = xi*spacing+rng.uniform(-4,4), yi*spacing+rng.uniform(-4,4)
            if excluded(x, y, manifest):
                rejected['mask'] += 1
                continue
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x,y,5000),
                unreal.Vector(x,y,-3000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                True, ignore, unreal.DrawDebugTrace.NONE)
            values = hit.to_tuple() if hit else None
            if not values or values[10] != ground_component:
                rejected['surface'] += 1
                continue
            position, normal = values[5], values[7]
            if normal.z < math.cos(math.radians(32)):
                rejected['slope'] += 1
                continue
            category = rng.randrange(2)
            point = unreal.PCGPoint()
            width, height = rng.uniform(.65,.85), rng.uniform(.10,.16)
            point.transform = unreal.Transform(position+unreal.Vector(0,0,.6),
                unreal.Rotator(yaw=rng.uniform(-180,180)), unreal.Vector(width,width,height))
            point.density = 1
            point.seed = xi*1009+yi*9176
            points[category].append(point)
            samples.append([round(position.x,2),round(position.y,2),round(position.z,2)])
    report = {'seed': 20261029, 'grid_cm': spacing, 'max_slope_degrees': 32,
              'rejected': rejected, 'instances': sum(map(len,points)), 'graphs': []}
    for category, name in enumerate(('Grass_Common_Short','Grass_Wispy_Short')):
        template = next(r for r in manifest['instances'] if r['name'] == name)
        key = f"World_{template['mesh_index']:04d}"
        mesh = unreal.load_asset(mapping[aliases.get(key,key)])
        path = '/Game/Graphics/Grass/PCG_'+name
        graph = unreal.load_asset(path)
        if graph:
            for node in list(graph.get_editor_property('nodes')): graph.remove_node(node)
        else:
            graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset('PCG_'+name,
                '/Game/Graphics/Grass', unreal.PCGGraph, unreal.PCGGraphFactory())
        node, settings = graph.add_node_of_type(unreal.PCGCreatePointsSettings)
        settings.set_editor_property('points_to_create', points[category])
        spawn, settings = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
        selector = settings.get_editor_property('mesh_selector_parameters')
        entry = unreal.PCGMeshSelectorWeightedEntry()
        descriptor = entry.get_editor_property('descriptor')
        descriptor.set_editor_property('static_mesh', mesh)
        lawn_materials=[grass_material(slot.material_interface,name+'_'+str(i))
                        for i,slot in enumerate(mesh.static_materials)]
        descriptor.set_editor_property('override_materials', lawn_materials)
        body = descriptor.get_editor_property('body_instance')
        body.set_editor_property('collision_enabled', unreal.CollisionEnabled.NO_COLLISION)
        descriptor.set_editor_property('body_instance', body)
        descriptor.set_editor_property('cast_shadow', False)
        descriptor.set_editor_property('affect_distance_field_lighting', False)
        descriptor.set_editor_property('affect_dynamic_indirect_lighting', False)
        descriptor.set_editor_property('component_class', unreal.HierarchicalInstancedStaticMeshComponent.static_class())
        descriptor.set_editor_property('instance_start_cull_distance', 1800)
        descriptor.set_editor_property('instance_end_cull_distance', 3000)
        entry.set_editor_property('descriptor', descriptor)
        selector.set_editor_property('mesh_entries', [entry])
        graph.add_edge(node,'Out',spawn,'In')
        graph.add_edge(spawn,'Out',graph.get_output_node(),'Out')
        unreal.EditorAssetLibrary.save_loaded_asset(graph)
        label = 'PCG Inland Grass '+str(category)
        actor = next((a for a in actors.get_all_level_actors() if a.get_actor_label()==label),None)
        if not actor:
            actor = actors.spawn_actor_from_class(unreal.Actor,unreal.Vector())
            actor.set_actor_label(label)
            actor.tags = ['MareGrassPCG']
            component = ActorTools.add_component(actor,unreal.PCGComponent.static_class(),'GrassPCG')
            box = ActorTools.add_component(actor,unreal.BoxComponent.static_class(),'GenerationBounds')
            box.set_box_extent(extent+unreal.Vector(100,100,1000),False)
            box.set_world_location(center,False,False)
            box.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            box.set_hidden_in_game(True)
        else:
            component = actor.get_component_by_class(unreal.PCGComponent)
        component.set_editor_property('generation_trigger',unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
        component.set_graph(graph)
        component.generate_local(True)
        report['graphs'].append({'graph':path,'mesh':mesh.get_path_name(),'points':len(points[category])})
    (ROOT/'Content/Data/grass_coverage.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    out=Path('D:/CodexTemp/ue58-graphics');out.mkdir(exist_ok=True)
    (out/'grass-samples.json').write_text(json.dumps(samples),encoding='utf-8')
    return report


def status():
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    result=[]
    for actor in actors:
        if 'MareGrassPCG' not in [str(t) for t in actor.tags]:continue
        for component in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            result.append({'actor':actor.get_actor_label(),'instances':component.get_instance_count(),
                'collision':str(component.get_collision_enabled()),
                'end_cull_cm':component.get_editor_property('instance_end_cull_distance')})
    expected=json.loads((ROOT/'Content/Data/grass_coverage.json').read_text(encoding='utf-8'))['instances']
    if sum(r['instances'] for r in result)!=expected:raise RuntimeError('Grass generation incomplete: '+str(result))
    if any('NO_COLLISION' not in r['collision'] for r in result):raise RuntimeError('Grass blocks circulation')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return result


def inspect():
    """Inspect the installed API and source ground before generating anything."""
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ground = next(a for a in actors.get_all_level_actors()
                  if a.get_actor_label().endswith(' Ground'))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(2000,0,3000),
        unreal.Vector(2000,0,-3000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
        True, [], unreal.DrawDebugTrace.NONE)
    return {'ground': ground.get_path_name(), 'bounds': str(ground.get_actor_bounds(False)),
            'sample_hit': str(hit.to_tuple()), 'hit_text': hit.export_text(),
            'trace_api': unreal.SystemLibrary.line_trace_single.__doc__,
            'hit_api': unreal.HitResult.__doc__}
