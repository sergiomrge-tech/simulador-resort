"""Tsunami / daily offering (04/11, Sergio): editor helpers to survey the mountain behind the village, place the old
man's wooden house on its top and the trail up to it."""
import json
import unreal


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _hit(x, y, top=60000):
    hit = unreal.SystemLibrary.line_trace_single(_world(), unreal.Vector(x, y, top), unreal.Vector(x, y, -3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    if not hit:
        return None
    t = hit.to_tuple()
    a = t[9]
    return [round(t[4].z), round(t[7].z, 2), a.get_actor_label() if a else '']


def profile(arg=''):
    """'x0,y0,x1,y1,step' -> heights along the line (first blocking hit from above)."""
    x0, y0, x1, y1, step = [float(v) for v in (arg or '4000,8000,4000,46000,1000').split(',')]
    n = int(max(abs(x1 - x0), abs(y1 - y0)) / step)
    rows = []
    for i in range(n + 1):
        x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
        rows.append([round(x), round(y)] + (_hit(x, y) or [None]))
    return json.dumps(rows, ensure_ascii=False)


def grid(arg=''):
    """'x0,x1,y0,y1,step' -> highest points of the area."""
    x0, x1, y0, y1, step = [float(v) for v in (arg or '-20000,30000,10000,50000,2000').split(',')]
    rows = []
    x = x0
    while x <= x1:
        y = y0
        while y <= y1:
            h = _hit(x, y)
            if h:
                rows.append([round(x), round(y)] + h)
            y += step
        x += step
    rows.sort(key=lambda r: -r[2])
    return json.dumps(rows[:30], ensure_ascii=False)


def heightmap(arg=''):
    """'x0,x1,y0,y1,step' -> full grid [x,y,z,nz] (all points) for offline analysis."""
    x0, x1, y0, y1, step = [float(v) for v in arg.split(',')]
    rows = []
    x = x0
    while x <= x1:
        y = y0
        while y <= y1:
            h = _hit(x, y)
            rows.append([round(x), round(y)] + (h[:2] if h else [None, None]))
            y += step
        x += step
    from pathlib import Path
    Path('D:/CodexTemp/tsunami').mkdir(parents=True, exist_ok=True)
    Path('D:/CodexTemp/tsunami/heightmap.json').write_text(json.dumps(rows), encoding='utf-8')
    return len(rows)


HOUSE_AT = (4000, 38900, 10800)   # summit pad, porch facing the sea (-Y)
HOUSE_YAW = 180.0
FOLDER = '/Game/Summit'
LABEL = 'Cume · casa do velho'


def _actor(label, at, yaw=0.0):
    world = _world()
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        if a.get_actor_label() == label:
            break
    else:
        a = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*at))
        a.set_actor_label(label)
    a.set_actor_location(unreal.Vector(*at), False, False)
    a.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), False)
    return a


def house(arg=''):
    """Import the prepared Wooden House (tools/ue58/prep_wood_house.py) and set it on the summit."""
    import mare_hotel_lobby as hl
    from pathlib import Path
    src = Path(unreal.Paths.project_dir()) / 'SourceArt/Models/Summit/WoodHouse.glb'
    mesh = unreal.load_asset(FOLDER + '/WoodHouse/WoodHouse') if arg != 'reimport' else None
    if not mesh:
        mesh = hl._import(src, FOLDER + '/WoodHouse', 'WoodHouse', False, search=False)   # glass: no Nanite
        hl._complex_collision(mesh)
    a = _actor(LABEL, HOUSE_AT, HOUSE_YAW)
    comp = a.static_mesh_component
    comp.set_static_mesh(mesh)
    a.tags = [unreal.Name('MareSummit')]
    o, e = a.get_actor_bounds(False)
    unreal.EditorLevelLibrary.save_current_level()
    return json.dumps({'origin': [round(o.x), round(o.y), round(o.z)], 'extent': [round(e.x), round(e.y), round(e.z)]})


def _veg_components():
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        tags = [str(t) for t in a.tags]
        label = a.get_actor_label()
        # Trees, shrubs, ferns and rocks only: the lawn's grass and flowers stay (no bald patches, 29/10).
        if 'MareMountainVegetation' in tags or 'MareLawn' in tags:
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                name = c.static_mesh.get_name().lower() if c.static_mesh else ''
                if 'MareLawn' in tags and not any(w in name for w in ('shrub', 'fern', 'rock')):
                    continue
                out.append((label, c))
    return out


def clear(arg=''):
    """'x,y,r[;x,y,r...]' (cm): removes the hill vegetation/rock instances whose base lies inside the circles."""
    circles = [[float(v) for v in c.split(',')] for c in arg.split(';') if c]
    removed = {}
    for label, comp in _veg_components():
        doomed = []
        for i in range(comp.get_instance_count()):
            t = comp.get_instance_transform(i, True)
            p = t.translation
            s = max(t.scale3d.x, t.scale3d.y)
            for x, y, r in circles:
                if (p.x - x) ** 2 + (p.y - y) ** 2 < (r + 150 * s) ** 2:
                    doomed.append(i)
                    break
        for i in sorted(doomed, reverse=True):
            comp.remove_instance(i)
        if doomed:
            key = f'{label}/{comp.static_mesh.get_name() if comp.static_mesh else "?"}'
            removed[key] = removed.get(key, 0) + len(doomed)
    unreal.EditorLevelLibrary.save_current_level()
    return json.dumps(removed, ensure_ascii=False)


def vlist(arg='4000,38600,2500'):
    x, y, r = [float(v) for v in (arg or '4000,38600,2500').split(',')]
    out = {}
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            n = 0
            for i in range(c.get_instance_count()):
                p = c.get_instance_transform(i, True).translation
                if (p.x - x) ** 2 + (p.y - y) ** 2 < r * r:
                    n += 1
            if n:
                out[f'{a.get_actor_label()} | {[str(t) for t in a.tags]} | {c.get_class().get_name()} | {c.static_mesh.get_name() if c.static_mesh else "?"}'] = n
    return json.dumps(out, ensure_ascii=False)


def vdebug(arg=''):
    w = _world()
    acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    n_ism, samples = 0, []
    for a in acts:
        cs = a.get_components_by_class(unreal.InstancedStaticMeshComponent)
        if cs:
            n_ism += len(cs)
            if len(samples) < 6:
                c = cs[0]
                samples.append([a.get_actor_label(), c.get_instance_count(), str(c.get_instance_transform(0, True).translation) if c.get_instance_count() else ''])
    return json.dumps({'world': w.get_path_name(), 'actors': len(acts), 'ism': n_ism, 'samples': samples}, ensure_ascii=False)


def reload_map(arg=''):
    """Reload Coast from disk (after a git checkout of the .umap)."""
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Maps/Entry')
    ok = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Maps/Coast')
    return str(ok)


def drop_cablecar(arg=''):
    """04/11: Sergio cancelled the cable car (a walking trail instead): delete its imported assets."""
    out = []
    for name in ('Bondinho_Station', 'Bondinho_Cabin', 'Bondinho_Cable'):
        d = f'{FOLDER}/{name}'
        if unreal.EditorAssetLibrary.does_directory_exist(d):
            out.append([d, unreal.EditorAssetLibrary.delete_directory(d)])
    return json.dumps(out)


def terrain_grid(arg=''):
    """'x0,x1,y0,y1,step,file' -> terrain-only heights (cm) as rows [x,y,z]; trees, roofs and lamps are skipped by tracing
    again from just below them. Written to D:/CodexTemp/tsunami/<file>.json for the trail planner."""
    x0, x1, y0, y1, step = [float(v) for v in arg.split(',')[:5]]
    name = arg.split(',')[5]
    rows = []
    x = x0
    while x <= x1:
        y = y0
        while y <= y1:
            top, z = 60000, None
            for _ in range(6):
                h = _hit(x, y, top)
                if not h:
                    break
                if 'MeshInstance3D' in h[2] or 'Ground' in h[2] or 'Mare' in h[2] and 'Ground' in h[2]:
                    z = h[0]
                    break
                top = h[0] - 5
            rows.append([round(x), round(y), z])
            y += step
        x += step
    from pathlib import Path
    Path(f'D:/CodexTemp/tsunami/{name}.json').write_text(json.dumps(rows), encoding='utf-8')
    return len(rows)


def trail(arg=''):
    """Import the summit trail (tools/ue58/gen_summit_trail.py, world coordinates), place it at the origin with
    complex collision, and clear trees/shrubs/rocks within 2.6 m of its centre line (the lawn grass stays)."""
    import mare_hotel_lobby as hl
    from pathlib import Path
    src = Path(unreal.Paths.project_dir()) / 'SourceArt/Models/Summit/SummitTrail.glb'
    # Reimporting over an asset keeps its old materials (CLAUDE.md): each build goes to a fresh folder, the old one is
    # deleted after the actor points to the new mesh.
    a = _actor('Cume · trilha', (0, 0, 0), 0.0)
    old = a.static_mesh_component.static_mesh
    old_dir = old.get_path_name().rsplit('/', 1)[0] if old else None
    import re
    vers = [int(m.group(1)) for p in unreal.EditorAssetLibrary.list_assets(FOLDER, recursive=True, include_folder=True)
            for m in [re.search(r'/SummitTrail_v(\d+)', p)] if m]
    ver = 1 + max(vers or [1])
    mesh = hl._import(src, f'{FOLDER}/SummitTrail_v{ver}', 'SummitTrail', True, search=False)
    hl._complex_collision(mesh)
    a.static_mesh_component.set_static_mesh(mesh)
    if old_dir and old_dir != f'{FOLDER}/SummitTrail_v{ver}':
        unreal.EditorAssetLibrary.delete_directory(old_dir)
    a.tags = [unreal.Name('MareSummitTrail')]
    pts = json.loads(Path('D:/CodexTemp/tsunami/trail.json').read_text())
    cell = 600.0
    grid = {}
    for x, y, _ in pts[::2]:
        grid.setdefault((int(x // cell), int(y // cell)), []).append((x, y))
    removed = {}
    # Footprint of each mesh (big rock slabs reach far from their pivot), measured from its bounds.
    radius = {}
    for label, comp in _veg_components():
        if comp.static_mesh:
            b = comp.static_mesh.get_bounds()
            radius[comp.get_name()] = .8 * max(b.box_extent.x, b.box_extent.y)
    for label, comp in _veg_components():
        doomed = []
        for i in range(comp.get_instance_count()):
            t = comp.get_instance_transform(i, True)
            p = t.translation
            r = 260 + radius.get(comp.get_name(), 150) * max(t.scale3d.x, t.scale3d.y)
            gx, gy = int(p.x // cell), int(p.y // cell)
            hit = False
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for x, y in grid.get((gx + dx, gy + dy), ()):
                        if (p.x - x) ** 2 + (p.y - y) ** 2 < r * r:
                            hit = True
                            break
                    if hit:
                        break
                if hit:
                    break
            if hit:
                doomed.append(i)
        for i in sorted(doomed, reverse=True):
            comp.remove_instance(i)
        if doomed:
            key = comp.static_mesh.get_name() if comp.static_mesh else '?'
            removed[key] = removed.get(key, 0) + len(doomed)
    # Grass carpet (PCG inland grass and the lawn's grass/flowers, no collision) grew through the path: removed only on
    # the path strip itself (centre line within 1.15 m), never around it.
    dense = {}
    for x, y, _ in pts:
        dense.setdefault((int(x // cell), int(y // cell)), []).append((x, y))
    for act in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        tags = [str(t) for t in act.tags]
        if 'MareGrassPCG' not in tags and 'MareLawn' not in tags:
            continue
        for comp in act.get_components_by_class(unreal.InstancedStaticMeshComponent):
            doomed = []
            for i in range(comp.get_instance_count()):
                p = comp.get_instance_transform(i, True).translation
                gx, gy = int(p.x // cell), int(p.y // cell)
                if any((p.x - x) ** 2 + (p.y - y) ** 2 < 115 ** 2
                       for dx in (-1, 0, 1) for dy in (-1, 0, 1) for x, y in dense.get((gx + dx, gy + dy), ())):
                    doomed.append(i)
            for i in sorted(doomed, reverse=True):
                comp.remove_instance(i)
            if doomed:
                key = 'grass:' + (comp.static_mesh.get_name() if comp.static_mesh else '?')
                removed[key] = removed.get(key, 0) + len(doomed)
    o, e = a.get_actor_bounds(False)
    unreal.EditorLevelLibrary.save_current_level()
    return json.dumps({'bounds': [[round(o.x - e.x), round(o.y - e.y), round(o.z - e.z)], [round(o.x + e.x), round(o.y + e.y), round(o.z + e.z)]], 'removed': removed})


TRAIL_CROSS = [-1.9, -1.0, -.6, -.2, .2, .6, 1.0, 1.9]


def trail_cross(arg=''):
    """Exact terrain heights across the trail at every planned point (the 2.5 m grid's bilinear heights left a berm
    on the plateau). Same tangents as gen_summit_trail.py; written to D:/CodexTemp/tsunami/trail_cross.json."""
    from pathlib import Path
    pts = json.loads(Path('D:/CodexTemp/tsunami/trail.json').read_text())
    n = len(pts)
    out = []
    for i in range(n):
        a, b = pts[max(0, i - 2)], pts[min(n - 1, i + 2)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = max((dx * dx + dy * dy) ** .5, 1e-6)
        sx, sy = -dy / L, dx / L
        row = []
        for c in TRAIL_CROSS:
            x, y = pts[i][0] + sx * 90 * c, pts[i][1] + sy * 90 * c
            top, z = 60000, None
            for _ in range(6):
                h = _hit(x, y, top)
                if not h:
                    break
                if 'MeshInstance3D' in h[2] or 'Ground' in h[2]:
                    z = h[0]
                    break
                top = h[0] - 5
            row.append(z)
        out.append(row)
    Path('D:/CodexTemp/tsunami/trail_cross.json').write_text(json.dumps(out))
    return sum(1 for r in out for z in r if z is None)


def probe_terrain(arg='5180,19700'):
    """Collision vs render mesh at one point: the traced height and the render triangle under it."""
    x, y = [float(v) for v in arg.split(',')]
    ignore = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label() == 'Cume · trilha']
    hit = unreal.SystemLibrary.line_trace_single(_world(), unreal.Vector(x, y, 60000), unreal.Vector(x, y, -3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore, unreal.DrawDebugTrace.NONE, True)
    t = hit.to_tuple()
    comp = t[10] if len(t) > 10 else None
    out = {'trace_z': round(t[4].z), 'actor': t[9].get_actor_label(), 'tuple_len': len(t)}
    comps = t[9].get_components_by_class(unreal.StaticMeshComponent)
    c = comps[0]
    mesh = c.static_mesh
    body = mesh.get_editor_property('body_setup')
    out['mesh'] = mesh.get_name()
    out['trace_flag'] = str(body.get_editor_property('collision_trace_flag'))
    out['nanite'] = mesh.get_editor_property('nanite_settings').enabled
    desc = mesh.get_static_mesh_description(0)
    xf = c.get_world_transform()
    best = None
    for vid in range(desc.get_vertex_count()):
        p = xf.transform_location(desc.get_vertex_position(unreal.VertexID(vid)))
        d = (p.x - x) ** 2 + (p.y - y) ** 2
        if best is None or d < best[0]:
            best = (d, p.z, p.x, p.y)
    out['nearest_render_vertex'] = [round(best[2]), round(best[3]), round(best[1]), round(best[0] ** .5)]
    out['verts'] = desc.get_vertex_count()
    return json.dumps(out)


_RENDER = {}


def _render_grid(actor):
    """World-space render vertices of a terrain tile (LOD0), bucketed in 50 cm cells (collision uses a simpler LOD and
    sat 20-30 cm below the visible surface in hollows, 04/11)."""
    name = actor.get_actor_label()
    if name in _RENDER:
        return _RENDER[name]
    grid = {}
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        if not c.static_mesh:
            continue
        desc = c.static_mesh.get_static_mesh_description(0)
        xf = c.get_world_transform()
        for vid in range(desc.get_vertex_count()):
            p = xf.transform_location(desc.get_vertex_position(unreal.VertexID(vid)))
            grid.setdefault((int(p.x // 50), int(p.y // 50)), []).append((p.x, p.y, p.z))
    _RENDER[name] = grid
    return grid


def render_height(x, y, ignore):
    hit = unreal.SystemLibrary.line_trace_single(_world(), unreal.Vector(x, y, 60000), unreal.Vector(x, y, -3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore, unreal.DrawDebugTrace.NONE, True)
    if not hit:
        return None
    t = hit.to_tuple()
    a = t[9]
    label = a.get_actor_label() if a else ''
    if not ('MeshInstance3D' in label or 'Ground' in label):
        return None
    grid = _render_grid(a)
    best = None
    gx, gy = int(x // 50), int(y // 50)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for px, py, pz in grid.get((gx + dx, gy + dy), ()):
                if (px - x) ** 2 + (py - y) ** 2 < 60 ** 2 and (best is None or pz > best):
                    best = pz
    return max(best, t[4].z) if best is not None else t[4].z


def trail_cross_render(arg=''):
    """trail_cross with the visible surface: highest render vertex within 60 cm (or the trace if higher)."""
    from pathlib import Path
    ignore = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
              if a.get_actor_label() in ('Cume · trilha', 'Cume · casa do velho') or 'Vegeta' in a.get_actor_label()
              or 'Gramado' in a.get_actor_label() or 'PCG' in a.get_actor_label()]
    pts = json.loads(Path('D:/CodexTemp/tsunami/trail.json').read_text())
    n = len(pts)
    out = []
    for i in range(n):
        a, b = pts[max(0, i - 2)], pts[min(n - 1, i + 2)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = max((dx * dx + dy * dy) ** .5, 1e-6)
        sx, sy = -dy / L, dx / L
        out.append([render_height(pts[i][0] + sx * 90 * c, pts[i][1] + sy * 90 * c, ignore) for c in TRAIL_CROSS])
    Path('D:/CodexTemp/tsunami/trail_cross.json').write_text(json.dumps(out))
    return sum(1 for r in out for z in r if z is None)


def house_no_nanite(arg=''):
    """The Wooden House has translucent window glass: Nanite does not render translucency (warning in the gate)."""
    mesh = unreal.load_asset(FOLDER + '/WoodHouse/WoodHouse')
    s = mesh.get_editor_property('nanite_settings')
    s.enabled = False
    mesh.set_editor_property('nanite_settings', s)
    return str(unreal.EditorAssetLibrary.save_loaded_asset(mesh, False))


def import_sound(arg='forest_loop'):
    """Import SourceArt/Audio/<name>.wav as /Game/Audio/<name> (looping ambience)."""
    from pathlib import Path
    src = Path(unreal.Paths.project_dir()) / f'SourceArt/Audio/{arg}.wav'
    task = unreal.AssetImportTask()
    task.filename = str(src)
    task.destination_path = '/Game/Audio'
    task.destination_name = arg
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    w = unreal.load_asset(f'/Game/Audio/{arg}')
    w.set_editor_property('looping', True)
    unreal.EditorAssetLibrary.save_loaded_asset(w, False)
    return f'{w.get_path_name()} {w.get_editor_property("duration")}'
