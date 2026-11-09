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


def summit_props(arg=''):
    """The old man's bench in front of the house, facing the sea and the volcano, and the offering basket beside it
    (Poly Haven CC0 painted_wooden_bench / wicker_basket_01). arg 'yaw=<deg>' turns the bench."""
    import mare_hotel_lobby as hl
    from pathlib import Path
    lib = Path('D:/Assets/PolyHaven')
    out = {}
    yaw = float(arg.split('=')[1]) if arg.startswith('yaw=') else 0.0
    for slug, label, xy, rot in (('painted_wooden_bench', 'Cume · banco do velho', (4000, 37900), yaw),
                                 ('wicker_basket_01', 'Cume · cesto da oferenda', (3640, 37860), 20.0)):
        mesh = next((m for m in (unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(f'{FOLDER}/{slug}', recursive=True))
                     if isinstance(m, unreal.StaticMesh)), None)   # the material shares the mesh's name
        if not mesh:
            info = json.loads((lib / slug / 'info.json').read_text(encoding='utf-8'))
            mesh = hl._import(lib / slug / info['gltf'], f'{FOLDER}/{slug}', slug, False, search=False)
        ignore = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label() == label]
        hit = unreal.SystemLibrary.line_trace_single(_world(), unreal.Vector(xy[0], xy[1], 20000), unreal.Vector(xy[0], xy[1], 0),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore, unreal.DrawDebugTrace.NONE, True)
        z = hit.to_tuple()[4].z if hit else 10700
        hl._complex_collision(mesh)   # the old man's seat is found by a trace, and the hero must not walk through it
        a = _actor(label, (xy[0], xy[1], z), rot)
        a.static_mesh_component.set_static_mesh(mesh)
        a.tags = [unreal.Name('MareSummit')]
        b = mesh.get_bounds()
        out[label] = {'z': round(z), 'mesh_origin': [round(b.origin.x), round(b.origin.y), round(b.origin.z)],
                      'mesh_extent': [round(b.box_extent.x), round(b.box_extent.y), round(b.box_extent.z)]}
    unreal.EditorLevelLibrary.save_current_level()
    return json.dumps(out, ensure_ascii=False)


# 08/11 (Sergio: "o tsunami ficou umas linhas... quando chegar perto da praia, tem que dar uma quebrada"; references: a
# dark water wall, white crest, spray, breaking over the beach). Shared by the wave and its spray: the break (scalar
# 'Break' 0..1 and 'Height' in cm, set by UMareSummitWorld) bends the upper part of the wave (UV1.y = height / crest)
# forward (+Y, towards the beach) and down until the crest collapses; each stretch of the 3 km front breaks a little
# earlier or later; the spray (S = 0..1 up its curtain) rides on the crest and bursts upwards at the break.
_BREAK_HLSL = ('float hn=L.y; float u=UV.x; float nx=sin(u*.9+1.7)*.5+.5; nx=nx*.6+.4*(sin(u*2.3+4.1)*.5+.5); '
               'float bl=saturate(B*1.45-.45*nx); float c=smoothstep(.45,1.0,min(hn,1.0)); ')
_WPO = _BREAK_HLSL + ('float fw=H*(.34*c*smoothstep(0,.55,bl)+.12*L.x*bl); float dn=H*(.8*c*c*smoothstep(.2,1.0,bl)); '
                      'float burst=smoothstep(0,.3,bl)*(1-.55*smoothstep(.7,1,bl)); '
                      'float churn=H*.035*bl*c*sin(u*6.0+T*1.4+hn*5.0); '
                      'return float3(0, fw + H*.14*S*burst, -dn + H*.5*S*burst + churn);')
# Value noise / fbm inside a Custom node (a local struct: Custom nodes cannot declare free functions).
_NOISE = ('struct NZ{ float h(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);} '
          'float v(float2 p){float2 i=floor(p); float2 f=frac(p); f=f*f*(3-2*f); '
          'return lerp(lerp(h(i),h(i+float2(1,0)),f.x),lerp(h(i+float2(0,1)),h(i+float2(1,1)),f.x),f.y);} '
          'float fbm(float2 p){float s=0; float a=.5; for(int k=0;k<5;k++){s+=a*v(p); p=p*2.07+float2(17.1,9.3); a*=.5;} return s;} }; NZ nz; ')


def _scalar(mat, name, default):
    import mare_materials as mm
    return mm.expression(mat, unreal.MaterialExpressionScalarParameter, parameter_name=name, default_value=default)


def wave_material():
    """M_TsunamiWave (08/11): a dark storm-sea wall (deep blue-green, a little light through the water just under the
    lip), glossy, ripples running up the face; foam from a value-noise fbm (no regular stripes) on the lip, in blotches
    on the face, at the foot and over the whole upper wave once it breaks. No glow (it comes by day now)."""
    import mare_materials as mm
    MEL = unreal.MaterialEditingLibrary
    mat = mm.material('M_TsunamiWave')
    mat.set_editor_property('two_sided', True)
    uv0 = mm.expression(mat, unreal.MaterialExpressionTextureCoordinate, coordinate_index=0)
    uv1 = mm.expression(mat, unreal.MaterialExpressionTextureCoordinate, coordinate_index=1)
    time = mm.expression(mat, unreal.MaterialExpressionTime)
    brk = _scalar(mat, 'Break', 0.0)
    height = _scalar(mat, 'Height', 6000.0)
    zero = mm.expression(mat, unreal.MaterialExpressionConstant, r=0.0)
    water_n = unreal.load_asset('/Engine/Functions/Engine_MaterialFunctions02/ExampleContent/Textures/water_n')
    ruv = mm.custom(mat, 'return float2(UV.x*3.0+sin(UV.y*31.0)*.15, UV.y*18.0 + T*0.22);', unreal.CustomMaterialOutputType.CMOT_FLOAT2, {'UV': uv0, 'T': time})
    tex = mm.expression(mat, unreal.MaterialExpressionTextureSample, texture=water_n, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    mm.connect(ruv, '', tex, 'UVs')
    ruv2 = mm.custom(mat, 'return float2(UV.x*8.0-UV.y*3.0, UV.y*45.0 + T*0.45);', unreal.CustomMaterialOutputType.CMOT_FLOAT2, {'UV': uv0, 'T': time})
    tex2 = mm.expression(mat, unreal.MaterialExpressionTextureSample, texture=water_n, sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    mm.connect(ruv2, '', tex2, 'UVs')
    # foam 0..1 (x) and a thin-water light mask (y)
    code = (_NOISE + _BREAK_HLSL +
            'float v=UV.y; float lip=L.x; float front=smoothstep(.70,.76,v); float crestband=smoothstep(.60,.70,v); '
            'float2 p=float2(UV.x*3.0, v*40.0); float f1=nz.fbm(p+float2(0,T*.25)); float f2=nz.fbm(p*2.3+float2(T*.04,T*.5)); '
            'float st=nz.fbm(float2(UV.x*7.0, v*22.0+T*.3)); '
            'float lipF=saturate(lip*1.6)*smoothstep(.15,.4,f1*.6+lip*.5); '
            'float faceF=front*smoothstep(.58,.74,st)*smoothstep(.35,.9,hn)*(.4+.6*smoothstep(.6,1,hn)); '
            'float topF=crestband*smoothstep(.9,.985,hn)*smoothstep(.35,.6,f1); '
            'float footF=0; '
            'float brkF=bl*crestband*smoothstep(.1,.4,hn)*smoothstep(.62,.40,f1*.8+.25-bl*.4); '
            'float foam=saturate(max(max(lipF,faceF),max(max(topF,footF),brkF))); '
            'float thin=front*smoothstep(.6,.85,hn)*(1-smoothstep(.93,1.0,hn))*(.35+.65*f2); '
            'float shade=.62+.38*smoothstep(.2,.8,f2*.6+st*.4); '
            'return float3(foam,thin,shade);')
    fm = mm.custom(mat, code, unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'UV': uv0, 'L': uv1, 'T': time, 'B': brk})
    color = mm.custom(mat, 'float v=UV.y; float hollow=smoothstep(.745,.77,v)*(1-smoothstep(.80,.84,v)); '
                           'float3 deep=float3(.003,.014,.019); float3 body=float3(.006,.034,.04); float3 lit=float3(.02,.15,.12); '
                           'float3 c=lerp(deep,body,smoothstep(.0,.7,L.y)*(1-.6*smoothstep(.70,.78,v))); c=lerp(c,lit,F.y); c*=1-.55*hollow; '
                           'return lerp(c,float3(.86,.89,.9)*F.z,F.x);',
                      unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'F': fm, 'L': uv1, 'UV': uv0})
    rough = mm.custom(mat, 'return lerp(.26,.8,F.x);', unreal.CustomMaterialOutputType.CMOT_FLOAT1, {'F': fm})
    normal = mm.custom(mat, 'float3 n=float3(A.xy*1.5+C.xy*.7,A.z*C.z); return normalize(lerp(n,float3(0,0,1),F.x*.7));',
                       unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'A': tex, 'C': tex2, 'F': fm})
    wpo = mm.custom(mat, _WPO, unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'UV': uv0, 'L': uv1, 'T': time, 'B': brk, 'H': height, 'S': zero})
    spec = mm.expression(mat, unreal.MaterialExpressionConstant, r=.28)
    for node, prop in ((color, unreal.MaterialProperty.MP_BASE_COLOR), (rough, unreal.MaterialProperty.MP_ROUGHNESS),
                       (normal, unreal.MaterialProperty.MP_NORMAL), (wpo, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET),
                       (spec, unreal.MaterialProperty.MP_SPECULAR)):
        MEL.connect_material_property(node, '', prop)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def spray_material():
    """M_TsunamiSpray (08/11): the spray curtains over the crest: translucent white mist from the fbm, fading at the
    crest and at the top, light before the break and bursting with it."""
    import mare_materials as mm
    MEL = unreal.MaterialEditingLibrary
    mat = mm.material('M_TsunamiSpray')
    mat.set_editor_property('two_sided', True)
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property('used_with_nanite', False)
    uv0 = mm.expression(mat, unreal.MaterialExpressionTextureCoordinate, coordinate_index=0)
    uv1 = mm.expression(mat, unreal.MaterialExpressionTextureCoordinate, coordinate_index=1)
    time = mm.expression(mat, unreal.MaterialExpressionTime)
    brk = _scalar(mat, 'Break', 0.0)
    height = _scalar(mat, 'Height', 6000.0)
    s = mm.custom(mat, 'return UV.y;', unreal.CustomMaterialOutputType.CMOT_FLOAT1, {'UV': uv0})
    opacity = mm.custom(mat, _NOISE + _BREAK_HLSL +
                        'float sv=UV.y; float burst=smoothstep(0,.3,bl)*(1-.55*smoothstep(.7,1,bl)); '
                        'float n=nz.fbm(float2(UV.x*5.0+T*.05, sv*3.0-T*.7)); float n2=nz.fbm(float2(UV.x*13.0, sv*7.0-T*1.3)); '
                        'float m=smoothstep(.42-.18*burst,.75,n*.75+n2*.35); '
                        'float fade=smoothstep(0,.18,sv)*(1-smoothstep(.55,1,sv)); '
                        'return saturate(m*fade*(.5+.45*burst));',
                        unreal.CustomMaterialOutputType.CMOT_FLOAT1, {'UV': uv0, 'L': uv1, 'T': time, 'B': brk})
    color = mm.expression(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.82, .86, .87, 1))
    rough = mm.expression(mat, unreal.MaterialExpressionConstant, r=.9)
    wpo = mm.custom(mat, _WPO, unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'UV': uv0, 'L': uv1, 'T': time, 'B': brk, 'H': height, 'S': s})
    for node, prop in ((color, unreal.MaterialProperty.MP_BASE_COLOR), (rough, unreal.MaterialProperty.MP_ROUGHNESS),
                       (opacity, unreal.MaterialProperty.MP_OPACITY), (wpo, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)):
        MEL.connect_material_property(node, '', prop)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def wave(arg=''):
    """Import the tsunami wave mesh (tools/ue58/gen_tsunami_wave.py) to /Game/Summit/TsunamiWave with M_TsunamiWave."""
    import mare_hotel_lobby as hl
    from pathlib import Path
    src = Path(unreal.Paths.project_dir()) / 'SourceArt/Models/Summit/TsunamiWave.glb'
    mesh = next((m for m in (unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(f'{FOLDER}/TsunamiWave', recursive=True))
                 if isinstance(m, unreal.StaticMesh)), None) if unreal.EditorAssetLibrary.does_directory_exist(f'{FOLDER}/TsunamiWave') else None
    if not mesh or arg == 'reimport':
        mesh = hl._import(src, f'{FOLDER}/TsunamiWave', 'TsunamiWave', False, search=False)
    mesh.set_material(0, wave_material())
    if len(mesh.static_materials) > 1:
        mesh.set_material(1, spray_material())
    # the spray is translucent: no Nanite (it would not draw)
    ns = mesh.get_editor_property('nanite_settings')
    if ns.enabled:
        ns.enabled = False
        mesh.set_editor_property('nanite_settings', ns)
    body = mesh.get_editor_property('body_setup')
    if body:
        body.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    b = mesh.get_bounds()
    return json.dumps({'mesh': mesh.get_path_name(), 'slots': len(mesh.static_materials), 'extent': [round(b.box_extent.x), round(b.box_extent.y), round(b.box_extent.z)]})


def rain_material(arg=''):
    """Rebuild M_RainCurtain (mare_materials.build_rain): Sergio 04/11 "diminua a intensidade da chuva"."""
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    return mare_materials.build_rain().get_path_name()


def talk_elder(arg=''):
    """QA in PIE: use Seu Tibúrcio's interaction as the player would (E). arg 'carry=<dish>' puts a product in hand."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    for t in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MareServiceTarget):
        if str(t.get_editor_property('action')) == 'Elder':
            t.use(pc)
            return 'used ' + str(t.get_editor_property('label'))
    return 'no elder target'


def brazil_food(arg=''):
    """Import the Brazilian kiosk dishes (tools/ue58/gen_brazil_food.py) to /Game/Custom/BrazilFood/Dish_<id>."""
    import mare_hotel_lobby as hl
    from pathlib import Path
    out = {}
    for name in ('Dish_milho_verde', 'Dish_espetinho', 'Dish_queijo_coalho', 'Dish_guarana'):
        src = Path(unreal.Paths.project_dir()) / f'SourceArt/Models/BrazilFood/{name}.glb'
        mesh = hl._import(src, f'/Game/Custom/BrazilFood/{name}', name, False, search=False)
        b = mesh.get_bounds()
        out[name] = [round(b.box_extent.x * 2), round(b.box_extent.y * 2), round(b.box_extent.z * 2)]
    return json.dumps(out)


def hold_food(arg=''):
    """QA in PIE: the people nearest to (x,y) hold the new dishes, one each. arg 'x,y'."""
    x, y = [float(v) for v in (arg or '3700,-1230').split(',')]
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    people = sorted(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson),
                    key=lambda p: (p.get_actor_location().x - x) ** 2 + (p.get_actor_location().y - y) ** 2)
    out = []
    for p, dish in zip(people, ('milho_verde', 'espetinho', 'queijo_coalho', 'guarana')):
        p.hold_product(dish)
        l = p.get_actor_location()
        out.append([dish, p.get_editor_property('person_name'), round(l.x), round(l.y), round(l.z)])
    return json.dumps(out, ensure_ascii=False)


def sea(arg=''):
    """Rebuild MPC_MareTime (adds Drawback) and M_CoastalWater (mare_materials.build_water) from the hud module call."""
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    mare_materials.time_collection()
    return mare_materials.build_water().get_path_name()


def cloud_info(arg=''):
    """Probe: the level's volumetric cloud material, its parent chain and scalar parameters (08/11, storm sky)."""
    out = []
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() or unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        c = a.get_component_by_class(unreal.VolumetricCloudComponent)
        if not c:
            continue
        m = c.get_editor_property('material')
        info = {'actor': a.get_name(), 'material': m.get_path_name() if m else None,
                'layer_bottom': c.get_editor_property('layer_bottom_altitude'), 'layer_height': c.get_editor_property('layer_height')}
        chain = []
        while m:
            chain.append(m.get_path_name())
            if isinstance(m, unreal.MaterialInstance):
                info.setdefault('scalars', {})
                for p in m.get_editor_property('scalar_parameter_values'):
                    info['scalars'][str(p.parameter_info.name)] = p.parameter_value
                m = m.get_editor_property('parent')
            else:
                info['params'] = [str(n) for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(m)]
                m = None
        info['chain'] = chain
        out.append(info)
    return json.dumps(out)


def hero(arg=''):
    """Probe (PIE): the hero's location and movement mode."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    h = unreal.GameplayStatics.get_player_pawn(world, 0)
    m = h.get_component_by_class(unreal.CharacterMovementComponent)
    l = h.get_actor_location()
    cam = unreal.GameplayStatics.get_player_camera_manager(world, 0).get_camera_location()
    return json.dumps({'hero': [round(l.x), round(l.y), round(l.z)], 'cam': [round(cam.x), round(cam.y), round(cam.z)], 'mode': str(m.movement_mode)})
