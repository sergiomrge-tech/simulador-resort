"""Guided snorkel (CHECKLIST_EXPANSOES 2.3): QA helpers. The tour itself is UMareSnorkelWorld (C++), its values
in Content/Data/tours.json "snorkel_tour"."""
import json

import unreal


def _editor_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _game_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()


def depth(arg='7000,-6000,11000,-4200,400'):
    """Bottom height (cm) on a grid 'x0,y0,x1,y1,step' (editor or PIE world)."""
    x0, y0, x1, y1, step = [float(v) for v in arg.split(',')]
    world = _game_world() or _editor_world()
    rows = []
    y = y0
    while y <= y1:
        row = []
        x = x0
        while x <= x1:
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 1000), unreal.Vector(x, y, -3000),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
                                                         unreal.DrawDebugTrace.NONE, True)
            t = hit.to_tuple() if hit else None
            row.append([round(t[4].z), t[9].get_name() if t[9] else '', t[10].get_name() if t[10] else ''] if t and t[0] else None)
            x += step
        rows.append([round(y)] + row)
        y += step
    return json.dumps(rows)


def qa(arg=''):
    """PIE: commands for AMareController::SnorkelQA separated by ';' ('start', 'state', 'present:<i>', ...)."""
    world = _game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    return json.dumps([[c, pc.snorkel_qa(c)] for c in arg.split(';') if c])


def who(arg=''):
    world = _game_world()
    out = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
        sid = str(p.get_editor_property('save_id'))
        if sid.startswith('snorkel_'):
            l = p.get_actor_location()
            out.append([sid, round(l.x), round(l.y), round(l.z)])
    pawn = unreal.GameplayStatics.get_player_controller(world, 0).get_controlled_pawn()
    l = pawn.get_actor_location()
    out.append(['hero', round(l.x), round(l.y), round(l.z)])
    return json.dumps(out)


def what(arg='9000,-4700'):
    x, y = [float(v) for v in arg.split(',')]
    world = _game_world() or _editor_world()
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 1000), unreal.Vector(x, y, -3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
    t = hit.to_tuple()
    c = t[10]
    mesh = c.static_mesh.get_path_name() if hasattr(c, 'static_mesh') and c.static_mesh else ''
    b = c.bounds if hasattr(c, 'bounds') else None
    return json.dumps([t[9].get_actor_label(), c.get_name(), mesh, str(c.get_class().get_name()),
                       round(t[4].z), str(t[11]) if len(t) > 11 else None])


def view(arg='0,0'):
    """PIE: absolute control rotation 'pitch,yaw' and optional hero location ',x,y,z' (QA captures)."""
    v = [float(x) for x in arg.split(',')]
    world = _game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    if len(v) >= 5:
        pawn = pc.get_controlled_pawn()
        pawn.set_actor_location(unreal.Vector(v[2], v[3], v[4]), False, True)
    pc.set_control_rotation(unreal.Rotator(roll=0, pitch=v[0], yaw=v[1]))
    return 'ok'


def corals(arg='World_0538,World_0566,World_0544,World_0564'):
    world = _game_world() or _editor_world()
    names = set(arg.split(','))
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if m and m.get_name() in names:
                n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else -1
                o, e, r = unreal.SystemLibrary.get_component_bounds(c)
                first = None
                if n > 0:
                    t = c.get_instance_transform(0, True)
                    first = [round(t.translation.x), round(t.translation.y), round(t.translation.z)]
                out.append([m.get_name(), a.get_actor_label(), n, [round(o.x), round(o.y), round(o.z)], [round(e.x), round(e.y), round(e.z)], first])
    return json.dumps(out)


def layout(arg=''):
    """Real positions of reef corals (per kind) and fish instances (per body mesh), rounded to 1 m."""
    world = _game_world() or _editor_world()
    d = json.load(open(unreal.Paths.project_content_dir() + 'Data/tours.json', encoding='utf-8'))
    kinds = {}
    for s in d['snorkel_tour']['species']:
        for n in s.get('coral', []):
            kinds[n] = s['id']
        if 'fish' in s:
            kinds[s['fish']] = s['id']
    out = {}
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if not m or m.get_name() not in kinds:
                continue
            k = kinds[m.get_name()]
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                for i in range(c.get_instance_count()):
                    t = c.get_instance_transform(i, True).translation
                    out.setdefault(k, []).append([round(t.x / 100), round(t.y / 100), round(t.z / 10) / 10])
            else:
                t = c.get_world_location()
                out.setdefault(k, []).append([round(t.x / 100), round(t.y / 100), round(t.z / 10) / 10])
    return json.dumps(out)


def looks(arg=''):
    world = _game_world()
    out = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
        sid = str(p.get_editor_property('save_id'))
        if not sid.startswith('snorkel_'):
            continue
        comps = []
        for c in p.get_components_by_class(unreal.SkeletalMeshComponent):
            m = c.get_skeletal_mesh_asset() if hasattr(c, 'get_skeletal_mesh_asset') else None
            comps.append([c.get_name(), m.get_name() if m else None, c.is_visible(), round(c.get_world_location().z)])
        out.append([sid, p.is_hidden_ed(), comps[:8]])
    return json.dumps(out)


def trail(arg='7200,-4700,100,10800,-4000,900'):
    """Editor (PIE stopped): navmesh path between two points: length (m) and the points (m)."""
    v = [float(x) for x in arg.split(',')]
    world = _editor_world()
    p = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, unreal.Vector(*v[:3]), unreal.Vector(*v[3:6]))
    if not p:
        return 'no path'
    pts = [[round(q.x), round(q.y), round(q.z)] for q in p.path_points]
    import math
    L = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) / 100
    return json.dumps({'len_m': round(L), 'partial': p.is_partial(), 'n': len(pts), 'pts': pts})


def find_mesh(arg='mare_lighthouse'):
    world = _game_world() or _editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if m and arg.lower() in m.get_name().lower():
                if isinstance(c, unreal.InstancedStaticMeshComponent):
                    for i in range(min(c.get_instance_count(), 5)):
                        t = c.get_instance_transform(i, True).translation
                        out.append([a.get_actor_label(), m.get_name(), round(t.x), round(t.y), round(t.z)])
                else:
                    t = c.get_world_location()
                    out.append([a.get_actor_label(), m.get_name(), round(t.x), round(t.y), round(t.z)])
    return json.dumps(out[:20])


def sun(arg=''):
    """PIE: sun elevation (deg) now, from the MareSun light."""
    import math
    world = _game_world()
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if a.actor_has_tag('MareSun'):
            f = a.get_actor_forward_vector()
            return json.dumps([round(math.degrees(math.asin(-f.z)), 1), round(math.degrees(math.atan2(-f.y, -f.x)))])
    return 'no sun'


def trailqa(arg=''):
    pc = unreal.GameplayStatics.get_player_controller(_game_world(), 0)
    return json.dumps([[c, pc.trail_qa(c)] for c in arg.split(';') if c])


def trailwho(arg=''):
    world = _game_world()
    out = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
        sid = str(p.get_editor_property('save_id'))
        if sid.startswith('trail_'):
            l = p.get_actor_location()
            out.append([sid, round(l.x), round(l.y), round(l.z), round(p.get_velocity().length())])
    l = unreal.GameplayStatics.get_player_controller(world, 0).get_controlled_pawn().get_actor_location()
    out.append(['hero', round(l.x), round(l.y), round(l.z)])
    return json.dumps(out)


def walktest(arg='8600,-3500,100'):
    world = _game_world()
    v = [float(x) for x in arg.split(',')]
    out = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
        if str(p.get_editor_property('save_id')).startswith('trail_'):
            c = p.get_controller()
            out.append([str(p.get_editor_property('save_id')), c.get_name() if c else None, p.walk_to(unreal.Vector(*v)),
                        str(p.character_movement.movement_mode), p.character_movement.max_walk_speed])
    return json.dumps(out)


def phone(arg='8'):
    pc = unreal.GameplayStatics.get_player_controller(_game_world(), 0)
    if arg == 'close':
        pc.close_phone()
    else:
        pc.open_phone(int(arg))
    return 'ok'


def ice(arg=''):
    pc = unreal.GameplayStatics.get_player_controller(_game_world(), 0)
    return json.dumps([[c, pc.ice_cream_qa(c)] for c in arg.split(';') if c])


def pastel(arg=''):
    pc = unreal.GameplayStatics.get_player_controller(_game_world(), 0)
    return json.dumps([[c, pc.pastel_qa(c)] for c in arg.split(';') if c])


def import_rental(arg=''):
    """Imports tools/ue58/gen_rental.py models (SourceArt/Models/Rental) to /Game/Custom/Rental/<name> (PIE stopped)."""
    import mare_hotel_lobby as hl
    import mare_boat_tour as bt
    from pathlib import Path
    src = Path(unreal.Paths.project_dir()) / 'SourceArt/Models/Rental'
    out = {}
    for p in sorted(src.glob('*.glb')):
        folder = f'/Game/Custom/Rental/{p.stem}'
        if unreal.EditorAssetLibrary.does_directory_exist(folder):
            unreal.EditorAssetLibrary.delete_directory(folder)
        mesh = hl._import(p, folder, p.stem, True, search=False)
        b = mesh.get_bounds()
        out[p.stem] = [round(b.box_extent.x * 2), round(b.box_extent.y * 2), round(b.box_extent.z * 2)]
    out['fixed'] = len(bt.fix_usage('/Game/Custom/Rental'))
    return json.dumps(out)


def rental(arg=''):
    pc = unreal.GameplayStatics.get_player_controller(_game_world(), 0)
    return json.dumps([[c, pc.rental_qa(c)] for c in arg.split(';') if c])


def souvenir(arg=''):
    """Souvenir shop QA (3.5): commands of AMareController::SouvenirQA separated by ';'."""
    pc = unreal.GameplayStatics.get_player_controller(_game_world(), 0)
    return json.dumps([[c, pc.souvenir_qa(c)] for c in arg.split(';') if c], ensure_ascii=False)


def lights(arg='3800,-1200,1200'):
    """Local lights within r cm of x,y: class, label, tags, location, intensity, units, radius, shadows."""
    x, y, r = [float(v) for v in arg.split(',')]
    world = _game_world() or _editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.LocalLightComponent):
            l = c.get_world_location()
            if (l.x - x) ** 2 + (l.y - y) ** 2 > r * r:
                continue
            out.append([a.get_actor_label()[:30], c.get_class().get_name(), [str(t) for t in a.tags][:3], [round(l.x), round(l.y), round(l.z)],
                        round(c.intensity, 1), str(c.get_editor_property('intensity_units')).split('.')[-1][:10], round(c.attenuation_radius), bool(c.cast_shadows), c.is_visible()])
    return json.dumps(out)


def meshes_near(arg='3800,-1200,600,180'):
    """Static meshes within r cm of x,y and above z: label, mesh, location (instances one by one)."""
    x, y, r, zmin = [float(v) for v in arg.split(',')]
    world = _game_world() or _editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if not m:
                continue
            pts = []
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                for i in range(min(c.get_instance_count(), 400)):
                    pts.append(c.get_instance_transform(i, True).translation)
            else:
                pts.append(c.get_world_location())
            for l in pts:
                if (l.x - x) ** 2 + (l.y - y) ** 2 <= r * r and l.z >= zmin:
                    out.append([a.get_actor_label()[:28], m.get_name(), [round(l.x), round(l.y), round(l.z)]])
    return json.dumps(out[:80])


def import_lamp(arg=''):
    """Poly Haven modern_ceiling_lamp_01 (CC0) -> /Game/Custom/Lighting/modern_ceiling_lamp_01 (PIE stopped)."""
    import mare_hotel_lobby as hl
    import mare_boat_tour as bt
    from pathlib import Path
    src = Path(unreal.Paths.project_dir()) / 'SourceArt/Models/Lighting/modern_ceiling_lamp_01/modern_ceiling_lamp_01_1k.gltf'
    folder = '/Game/Custom/Lighting/modern_ceiling_lamp_01'
    if unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.delete_directory(folder)
    mesh = hl._import(src, folder, 'modern_ceiling_lamp_01', True, search=False)
    b = mesh.get_bounds()
    return json.dumps([[round(b.origin.x), round(b.origin.y), round(b.origin.z)], [round(b.box_extent.x * 2), round(b.box_extent.y * 2), round(b.box_extent.z * 2)], bt.fix_usage('/Game/Custom/Lighting')])


def ceiling(arg='4780,2310,150'):
    x, y, z = [float(v) for v in arg.split(',')]
    world = _game_world() or _editor_world()
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, z), unreal.Vector(x, y, z + 800), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
    t = hit.to_tuple()
    return json.dumps([round(t[4].z), t[9].get_actor_label() if t[9] else None] if t[0] else None)


def mesh_info(arg='World_0546'):
    """Asset path, bounds size (cm) and material names of World_* meshes (comma separated names)."""
    out = []
    for n in arg.split(','):
        hits = unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_package_name('/Game/World/Models/%s/%s' % (n, n))
        if not hits:
            hits = unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_package_name('/Game/World/Models/%s/%s/StaticMeshes/%s' % (n, n, n))
        for h in hits:
            m = h.get_asset()
            if not isinstance(m, unreal.StaticMesh):
                continue
            b = m.get_bounding_box()
            s = b.max - b.min
            out.append([n, str(h.package_name), [round(s.x), round(s.y), round(s.z)], [str(mat.material_slot_name) for mat in m.static_materials][:3]])
    return json.dumps(out)


def hero(arg=''):
    """'x,y,z' puts the hero there (stopped); empty: hero location, velocity and movement mode."""
    world = _game_world()
    p = unreal.GameplayStatics.get_player_pawn(world, 0)
    if arg:
        x, y, z = [float(v) for v in arg.split(',')]
        p.set_actor_location(unreal.Vector(x, y, z), False, True)
        p.character_movement.stop_movement_immediately()
    l, v = p.get_actor_location(), p.get_velocity()
    return json.dumps([round(l.z, 1), round(v.z, 1), str(p.character_movement.movement_mode).split('.')[-1], round(l.x), round(l.y)])
