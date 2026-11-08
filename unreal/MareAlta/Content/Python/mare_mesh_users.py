"""Which actors/components draw these meshes, and how many instances on the beach sand (y < -1050).
mare_hud module "mare_mesh_users.find|World_2073,World_2078"."""
import json
import unreal


def find(arg=''):
    names = set(arg.split(','))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() or \
        unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if not m or m.get_name() not in names:
                continue
            n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
            beach = 0
            for i in range(n):
                t = c.get_instance_transform(i, True) if isinstance(c, unreal.InstancedStaticMeshComponent) else c.get_world_transform()
                if t.translation.y < -1050 and t.scale3d.z > .01:
                    beach += 1
            out.append({'actor': a.get_actor_label(), 'comp': c.get_name(), 'mesh': m.get_name(), 'n': n, 'beach': beach})
    return json.dumps(out, ensure_ascii=False)


def _base_gap(world, actor, mesh, t):
    b = mesh.get_bounds()
    pts = [t.transform_location(b.origin + unreal.Vector(dx * b.box_extent.x, dy * b.box_extent.y, dz * b.box_extent.z))
           for dx in (-1, 1) for dy in (-1, 1) for dz in (-1, 1)]
    lo = min(p.z for p in pts)
    gaps = []
    for fx, fy in ((0, 0), (-.35, -.35), (.35, -.35), (-.35, .35), (.35, .35)):
        p = t.transform_location(b.origin + unreal.Vector(fx * b.box_extent.x, fy * b.box_extent.y, 0))
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(p.x, p.y, lo + 30), unreal.Vector(p.x, p.y, lo - 300),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [actor], unreal.DrawDebugTrace.NONE, True)
        if hit:
            gaps.append(lo - hit.to_tuple()[4].z)
    return (min(gaps) if gaps else None), lo


def plants(arg='PCG'):
    """Gap under every instance of actors whose label contains arg (PCG gardens, vegetation), worst first."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() or \
        unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    rows = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        label = a.get_actor_label()
        if not any(k in label for k in arg.split(',')):
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            m = c.static_mesh
            if not m:
                continue
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                if t.scale3d.z < .01:
                    continue
                gap, lo = _base_gap(world, a, m, t)
                if gap is not None and gap > 4:
                    rows.append({'actor': label, 'comp': c.get_name(), 'mesh': m.get_name(), 'i': i, 'gap': round(gap, 1),
                                 'at': [round(t.translation.x), round(t.translation.y), round(lo)]})
    rows.sort(key=lambda r: -r['gap'])
    return json.dumps({'n': len(rows), 'worst': rows[:25]}, ensure_ascii=False)


def where(arg=''):
    """Positions of the instances of actors whose label contains arg."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() or \
        unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if arg not in a.get_actor_label():
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                out.append([a.get_actor_label()[-16:], i, round(t.translation.x), round(t.translation.y), round(t.translation.z), round(t.scale3d.z, 2)])
    return json.dumps(out)


def hide_label(arg=''):
    """07/11 (Sergio: "florzinhas nascendo na areia"): shrink (epsilon keeps bounds/culling sane) every instance of the
    level actors whose label starts with arg ('Maré · periwinkle'), and the matching Content/Data/world.json rows.
    Editor, PIE stopped."""
    from pathlib import Path
    from mare_world_builder import transform
    from mare_float_audit import _row, DATA
    data = json.loads((DATA / 'world.json').read_text(encoding='utf-8-sig'))
    n = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = a.get_actor_label()
        if not label.startswith(arg):
            continue
        rows = [r for r in data['instances'] if 'Maré · ' + r['name'] == label]
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                old = unreal.Vector(t.translation.x, t.translation.y, t.translation.z)
                t.scale3d = unreal.Vector(.001, .001, .001)
                c.update_instance_transform(i, t, True, True, True)
                for row in rows:
                    rt = transform(row['transform'])
                    if rt is not None and (rt.translation - old).length() < 1.0:
                        row['transform'] = _row(t)
                        break
                n += 1
    (DATA / 'world.json').write_text(json.dumps(data, ensure_ascii=False, indent='\t'), encoding='utf-8')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'hidden': n})
