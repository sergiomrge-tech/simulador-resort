"""Pier measurements (11/11, people leaning at the pier): scan('x0,x1,y0,y1,step') traces across the pier (along X) at
several heights for each y and returns, per y, the highest z at which something on each side is hit: the posts and the
rope of pier_segment (World_2011). Editor, PIE stopped."""
import json
import unreal


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def scan(arg='6950,7450,-3550,-3250,15'):
    x0, x1, y0, y1, step = (float(v) for v in arg.split(','))
    w = _world()
    out = []
    y = y0
    while y <= y1:
        row = {'y': round(y)}
        for side, (a, b) in (('w', (x0, (x0 + x1) / 2)), ('e', (x1, (x0 + x1) / 2))):
            top, at = None, None
            for z in range(150, 30, -5):
                hit = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(a, y, z), unreal.Vector(b, y, z), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                             True, [], unreal.DrawDebugTrace.NONE, True)
                if hit:
                    top, at = z, round(hit.to_tuple()[4].x)
                    break
            row[side] = [top, at]
        # deck height in the middle
        hit = unreal.SystemLibrary.line_trace_single(w, unreal.Vector((x0 + x1) / 2, y, 300), unreal.Vector((x0 + x1) / 2, y, -100),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        row['deck'] = round(hit.to_tuple()[4].z) if hit else None
        out.append(row)
        y += step
    return json.dumps(out)


def hands(_=''):
    """PIE running: for each pier person (tag MarePierPerson) the actor location and both hand sockets (world)."""
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_with_tag(w, 'MarePierPerson'):
        m = a.mesh
        l = a.get_actor_location()
        row = {'at': [round(l.x), round(l.y), round(l.z)], 'yaw': round(a.get_actor_rotation().yaw)}
        for s in ('hand_l', 'hand_r', 'head', 'pelvis'):
            p = m.get_socket_location(s)
            row[s] = [round(p.x), round(p.y), round(p.z)]
        out.append(row)
    return json.dumps(out)


def posts(arg='dry'):
    """11/11 (Sergio: "está sem base as cordas"): the last pier_segment's ropes run to y -4600, where the end platform
    has no post. Places the mare_pier_post model (tools/ue58/gen_pier_post.py) under the four rope ends, one per side.
    'apply' places and saves (PIE stopped). Re-runnable."""
    from pathlib import Path
    data = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data' / 'custom_assets.json').read_text(encoding='utf-8'))
    mesh = unreal.load_asset(data['mare_pier_post'])
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mine = [a for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.StaticMeshActor) if 'MarePierPost' in [str(t) for t in a.tags]]
    if arg.strip() != 'apply' or not mesh:
        return json.dumps({'mesh': bool(mesh), 'mine': len(mine)})
    for a in mine:
        actors.destroy_actor(a)
    for k, x in enumerate((7075.0, 7325.0)):
        a = actors.spawn_actor_from_object(mesh, unreal.Vector(x, -4600.0, 37.0), unreal.Rotator(roll=0, pitch=0, yaw=90 * k))
        a.set_actor_label('Mourão do píer %d' % (k + 1))
        a.tags = ['MarePierPost']
        a.set_folder_path('Praia/Pier')
        a.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'placed': 2})


def rail(arg='dry'):
    """11/11: the timber guard rail on the sea side of the end platform (tools/ue58/gen_pier_rail.py), where one of the
    pier people leans (pier_people.json, clip Idle_Rail). The deck height and the free edge are traced first.
    'apply' places and saves (PIE stopped). Re-runnable."""
    from pathlib import Path
    data = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data' / 'custom_assets.json').read_text(encoding='utf-8'))
    mesh = unreal.load_asset(data.get('mare_pier_rail', ''))
    w = _world()
    out = {'mesh': bool(mesh), 'deck': []}
    for y in (-4800, -4820, -4840, -4850, -4860, -4870, -4880):
        hit = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(7200, y, 200), unreal.Vector(7200, y, -50), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                     True, [], unreal.DrawDebugTrace.NONE, True)
        out['deck'].append([y, round(hit.to_tuple()[4].z, 1) if hit else None])
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mine = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.StaticMeshActor) if 'MarePierRail' in [str(t) for t in a.tags]]
    if arg.strip() != 'apply' or not mesh:
        return json.dumps(out)
    for a in mine:
        actors.destroy_actor(a)
    # west half of the sea edge: the player's fishing spot (bucket and rod) is at x 7200; 2 m long (x scale .8) to stay on the platform (x 6971..)
    a = actors.spawn_actor_from_object(mesh, unreal.Vector(7075, -4890, 37), unreal.Rotator(roll=0, pitch=0, yaw=0))
    a.set_actor_scale3d(unreal.Vector(.8, 1, 1))
    a.set_actor_label('Píer · guarda-corpo da ponta')
    a.tags = ['MarePierRail']
    a.set_folder_path('Praia/Pier')
    a.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    out['placed'] = True
    return json.dumps(out)
