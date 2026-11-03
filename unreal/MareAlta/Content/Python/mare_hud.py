import math
"""HUD assets for the gameplay plan (docs/ue58/GAMEPLAY_PLANO_2026-11-02.md).
Run through the editor MCP: hotel_lobby action "hud_<name>" -> run(<name>, arg)."""
from pathlib import Path
import unreal

ICONS = Path(unreal.Paths.project_dir()).resolve() / 'SourceArt/UI/Icons'
DEST = '/Game/UI/Icons'


def import_icons():
    """White icons from tools/ue58/gen_hud_icons.py as UI textures (no mips, UI group, alpha kept)."""
    out = {}
    for png in sorted(ICONS.glob('T_Icon_*.png')):
        task = unreal.AssetImportTask()
        task.filename = str(png)
        task.destination_path = DEST
        task.destination_name = png.stem
        task.automated = True
        task.replace_existing = True
        task.save = False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.load_asset(f'{DEST}/{png.stem}')
        tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
        out[png.stem] = [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()]
    return out


MODELS = Path(unreal.Paths.project_dir()).resolve() / 'SourceArt/Models'


def import_models(folder, dest):
    """Every GLB of SourceArt/Models/<folder> as <dest>/<name>/<name> (one folder each), with local material search
    so generic names never pick up another model's material. RoomMess (gen_room_mess.py) -> /Game/Custom/RoomMess,
    GameRoom (gen_pool_table.py) -> /Game/Custom/GameRoom."""
    import mare_hotel_lobby
    out = {}
    for glb in sorted((MODELS / folder).glob('*.glb')):
        # Fresh folder: reimporting over an old import keeps stale materials and renamed meshes.
        if unreal.EditorAssetLibrary.does_directory_exist(f'{dest}/{glb.stem}'):
            unreal.EditorAssetLibrary.delete_directory(f'{dest}/{glb.stem}')
        mesh = mare_hotel_lobby._import(glb, f'{dest}/{glb.stem}', glb.stem, False, search=False)
        out[glb.stem] = mesh.get_path_name()
    return out


def import_sfx():
    """Action sounds of SourceArt/Audio/Actions (tools/ue58/fetch_action_sfx.py) -> /Game/Audio/Actions, listed in
    Content/Data/audio.json with their action group and volume (UMareAudioWorld::PlayAction)."""
    import json
    src = Path(unreal.Paths.project_dir()).resolve() / 'SourceArt/Audio/Actions'
    manifest = json.loads((src / 'manifest.json').read_text(encoding='utf-8'))
    actions = manifest.get('actions', manifest)
    catalog_path = Path(unreal.Paths.project_content_dir()).resolve() / 'Data/audio.json'
    catalog = [row for row in json.loads(catalog_path.read_text(encoding='utf-8')) if not row.get('group')]
    done = 0
    for group, info in actions.items():
        for f in info['files']:
            name = Path(f['file'] if isinstance(f, dict) else f).stem
            task = unreal.AssetImportTask()
            task.filename = str(src / f'{name}.wav')
            task.destination_path = '/Game/Audio/Actions'
            task.destination_name = name
            task.automated = True
            task.replace_existing = True
            task.save = True
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            wave = unreal.load_asset(f'/Game/Audio/Actions/{name}')
            if not isinstance(wave, unreal.SoundWave):
                raise RuntimeError(f'{name}: import gave {wave}')
            catalog.append({'id': name, 'path': f'/Game/Audio/Actions/{name}.{name}', 'duration': wave.get_editor_property('duration'),
                            'loop': False, 'group': group, 'volume': info['volume']})
            done += 1
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return {'imported': done, 'catalog': len(catalog)}


def bar_qa(arg):
    """PIE: 'orders' seats four guests at the bar, 'stand' puts the player inside the counter looking at the
    station, 'open' uses the station (bar page), 'close' closes it."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    sim = pc.get_simulation()
    if arg == 'orders':
        return [sim.add_bar_order('') for _ in range(4)]
    target = next((a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MareServiceTarget)
                   if str(a.get_editor_property('action')) == 'BarCounter'), None)
    if arg == 'stand' and target:
        hero.set_actor_location(unreal.Vector(1340, -1300, 100), False, True)
        focus = target.get_actor_location()
        pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(1340, -1300, 164), focus))
    if arg == 'open' and target:
        target.use(pc)
    if arg == 'close':
        pc.close_phone()
    if arg == 'shot':
        unreal.SystemLibrary.execute_console_command(world, 'Shot showui')
    return {'target': bool(target), 'phone': pc.get_editor_property('phone_open')}


def biz_bounds():
    """World bounds of the actors tagged Biz_<id> (the business buildings), per business."""
    out = {}
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for t in a.tags:
            t = str(t)
            if t.startswith('Region_Biz_'):
                o, e = a.get_actor_bounds(True)
                if e.x > 2000 or e.y > 2000:
                    continue
                b = out.setdefault(t[11:], [1e9, 1e9, 1e9, -1e9, -1e9, -1e9, 0])
                b[0] = min(b[0], o.x - e.x); b[1] = min(b[1], o.y - e.y); b[2] = min(b[2], o.z - e.z)
                b[3] = max(b[3], o.x + e.x); b[4] = max(b[4], o.y + e.y); b[5] = max(b[5], o.z + e.z); b[6] += 1
    return {k: [round(v) for v in b] for k, b in out.items()}


def biz_qa(arg):
    """PIE: 'buy:<id>' buys a business, 'stand:<id>' puts the player at its counter, 'use:<id>' starts the counter
    task, 'shot' takes a screenshot with the UI, 'people' lists persons near the counters."""
    import json
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    sim = pc.get_simulation()
    what, _, biz = arg.partition(':')
    if what == 'buy':
        return sim.buy_business(biz)
    if what == 'shot':
        unreal.SystemLibrary.execute_console_command(world, 'Shot showui')
        return 'shot'
    target = next((a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MareServiceTarget)
                   if 'biz:' + biz in [str(t) for t in a.tags]), None)
    if not target:
        return 'no counter'
    if what == 'stand':
        fwd = target.get_actor_forward_vector()
        at = target.get_actor_location() + fwd * 180
        hero.set_actor_location(unreal.Vector(at.x, at.y, target.get_actor_location().z), False, True)
        pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(hero.get_actor_location() + unreal.Vector(0, 0, 64), target.get_actor_location()))
        return [round(at.x), round(at.y)]
    if what == 'use':
        target.use(pc)
        return 'used'


def find_actors(text):
    """Level actors and ISM instances whose label or mesh name contains text: [label, [x, y, z]] (first 80)."""
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = a.get_actor_label()
        if text.lower() in label.lower():
            o, e = a.get_actor_bounds(False)
            out.append([label[-50:], [round(o.x), round(o.y), round(o.z)], [round(e.x), round(e.y), round(e.z)]])
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if c.static_mesh and text.lower() in c.static_mesh.get_name().lower():
                for i in range(min(c.get_instance_count(), 20)):
                    q = c.get_instance_transform(i, True).translation
                    out.append([c.static_mesh.get_name(), [round(q.x), round(q.y), round(q.z)]])
        if len(out) > 80:
            break
    return out[:80]


def actor_instances(text):
    """Instance positions of the ISM components of actors whose label contains text."""
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if text.lower() not in a.get_actor_label().lower():
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            for i in range(c.get_instance_count()):
                q = c.get_instance_transform(i, True).translation
                out.append([a.get_actor_label()[-20:], [round(q.x), round(q.y), round(q.z)]])
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if not isinstance(c, unreal.InstancedStaticMeshComponent) and c.static_mesh:
                q = c.get_world_location()
                out.append([a.get_actor_label()[-20:] + '/' + c.static_mesh.get_name(), [round(q.x), round(q.y), round(q.z)]])
    return out[:60]


def target_qa(arg):
    """PIE: 'stand:<Action>' puts the player 1.8 m in front of the first E target with that action, looking at it;
    'use:<Action>' uses it; 'shot' takes a screenshot with the UI."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    what, _, action = arg.partition(':')
    if what == 'shot':
        unreal.SystemLibrary.execute_console_command(world, 'Shot showui')
        return 'shot'
    target = next((a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MareServiceTarget)
                   if str(a.get_editor_property('action')) == action), None)
    if not target:
        return 'no target'
    if what == 'stand':
        at = target.get_actor_location() + target.get_actor_forward_vector() * 180
        hero.set_actor_location(unreal.Vector(at.x, at.y, target.get_actor_location().z), False, True)
        pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(hero.get_actor_location() + unreal.Vector(0, 0, 64), target.get_actor_location()))
        return [round(at.x), round(at.y)]
    if what == 'use':
        target.use(pc)
        return 'used'


def trace_fan(arg):
    """PIE: traces from the camera at yaw offsets (arg "pitch,from,to,step"): hit point, actor label and mesh."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    loc, rot = pc.get_player_view_point()
    pitch, a, b, step = [float(v) for v in arg.split(',')]
    out = []
    y = a
    while y <= b:
        d = unreal.MathLibrary.get_forward_vector(unreal.Rotator(roll=0, pitch=pitch, yaw=rot.yaw + y))
        hit = unreal.SystemLibrary.line_trace_single(world, loc, loc + d * 3000, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False,
                                                    [unreal.GameplayStatics.get_player_pawn(world, 0)], unreal.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else None
        if t and t[0]:
            comp = t[10]
            mesh = comp.static_mesh.get_name() if comp and hasattr(comp, 'static_mesh') and comp.static_mesh else ''
            out.append([y, [round(t[4].x), round(t[4].y), round(t[4].z)], t[9].get_actor_label()[-30:] if t[9] else '', mesh])
        y += step
    return {'cam': [round(loc.x), round(loc.y), round(loc.z), round(rot.yaw)], 'hits': out}


def import_game_room_extras():
    """Foosball and arcade (tools/ue58/gen_game_room_extras.py) only, each in a fresh folder of /Game/Custom/GameRoom."""
    import mare_hotel_lobby
    out = {}
    for name in ('foosball_table', 'arcade_cabinet'):
        glb = MODELS / 'GameRoom' / f'{name}.glb'
        dest = f'/Game/Custom/GameRoom/{name}'
        if unreal.EditorAssetLibrary.does_directory_exist(dest):
            unreal.EditorAssetLibrary.delete_directory(dest)
        out[name] = mare_hotel_lobby._import(glb, dest, name, False, search=False).get_path_name()
    return out


def rays(arg):
    """Editor world: horizontal traces in 16 directions from "x,y,z": distance to the first hit and what it hit."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    x, y, z = [float(v) for v in arg.split(',')]
    o = unreal.Vector(x, y, z)
    out = []
    for k in range(16):
        a = math.radians(k * 22.5)
        e = o + unreal.Vector(math.cos(a), math.sin(a), 0) * 1500
        hit = unreal.SystemLibrary.line_trace_single(world, o, e, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else None
        out.append([k * 22.5, round(t[3]) if t and t[0] else None, (t[9].get_actor_label()[-25:] if t and t[0] and t[9] else '')])
    return out


def photo_qa(arg):
    """PIE: "x,y,z,pitch,yaw" places the player and takes a photo (P); returns the message and the album size."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    x, y, z, pitch, yaw = [float(v) for v in arg.split(',')]
    hero.set_actor_location(unreal.Vector(x, y, z), False, True)
    pc.set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
    return 'placed'


def photo_sun():
    """PIE: turns the player's view to the sun (MareSun light) and takes a photo; returns the sim's message."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    sun = next(iter(unreal.GameplayStatics.get_all_actors_with_tag(world, 'MareSun')), None)
    if not sun:
        return 'no sun'
    f = sun.get_actor_forward_vector()
    to_sun = unreal.Vector(-f.x, -f.y, -f.z)
    pc.set_control_rotation(unreal.MathLibrary.make_rot_from_x(to_sun))
    return [round(to_sun.x, 3), round(to_sun.y, 3), round(to_sun.z, 3)]


def photo_take():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    pc.take_photo()
    return 'taken'


def staff_qa(arg):
    """PIE: 'hire' hires every staff role, 'list' gives each visible worker (MareStaff tag) with its place and look,
    'look:<role>' puts the player 4 m from that worker looking at it (for a screenshot)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    sim = pc.get_simulation()
    if arg == 'hire':
        return {r: sim.hire_staff(r) for r in ('bartender', 'recepcionista', 'camareira', 'piscineiro', 'guia', 'garcom_hotel')}
    workers = list(unreal.GameplayStatics.get_all_actors_with_tag(world, 'MareStaff'))
    if arg == 'list':
        return [[str(w.get_editor_property('save_id')), [round(v) for v in (w.get_actor_location().x, w.get_actor_location().y, w.get_actor_location().z)],
                 str(w.get_editor_property('meta_human'))] for w in workers]
    what, _, role = arg.partition(':')
    if what == 'probe':
        w = next((w for w in workers if str(w.get_editor_property('save_id')) == 'staff_' + role), None)
        if not w:
            return 'none'
        out = {'hidden': w.is_hidden_ed(), 'meta': str(w.get_editor_property('meta_human'))}
        for c in w.get_components_by_class(unreal.ChildActorComponent):
            child = c.get_editor_property('child_actor')
            out['child'] = str(child.get_class().get_name()) if child else None
            if child:
                out['parts'] = [[m.get_name(), str(m.get_editor_property('skeletal_mesh_asset').get_name()) if isinstance(m, unreal.SkeletalMeshComponent) and m.get_editor_property('skeletal_mesh_asset') else '', m.is_visible()]
                                for m in child.get_components_by_class(unreal.MeshComponent)][:12]
        return out
    if what == 'look':
        role, _, dist = role.partition(':')
        dist = float(dist or 380)
        w = next((w for w in workers if str(w.get_editor_property('save_id')) == 'staff_' + role), None)
        if not w:
            return 'none'
        at = w.get_actor_location()
        fwd = w.get_actor_forward_vector()
        eye = unreal.Vector(at.x + fwd.x * dist + fwd.y * dist * .3, at.y + fwd.y * dist - fwd.x * dist * .3, at.z + 30 * dist / 380)
        hero.set_actor_location(eye, False, True)
        pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(eye.x, eye.y, eye.z + 64), unreal.Vector(at.x, at.y, at.z + 40)))
        return [round(at.x), round(at.y), round(at.z)]
    raise ValueError(arg)


def person_qa(arg):
    """PIE: 'list' = MetaHuman of every person; 'look:<MetaHuman>[:n]' = the player 2.2 m in front of the n-th such person."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    people = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson))
    if arg == 'list':
        from collections import Counter
        return dict(Counter(str(p.get_editor_property('meta_human')) for p in people))
    _, name, *rest = arg.split(':')
    match = [p for p in people if str(p.get_editor_property('meta_human')) == name]
    if not match:
        return 'none'
    w = match[int(rest[0]) % len(match) if rest else 0]
    at = w.get_actor_location()
    fwd = w.get_actor_forward_vector()
    eye = unreal.Vector(at.x + fwd.x * 220, at.y + fwd.y * 220, at.z + 10)
    hero.set_actor_location(eye, False, True)
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(eye.x, eye.y, eye.z + 64), unreal.Vector(at.x, at.y, at.z + 10)))
    return [round(at.x), round(at.y), round(at.z), len(match)]


def party_qa(arg):
    """PIE: "show_dj" sets today's party (mare.Event) and brings the nearest walking people around the party spot
    (events.json party_spot), so the dancers can be seen; returns who was moved."""
    import json
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    unreal.SystemLibrary.execute_console_command(world, f'mare.Event {arg}')
    spot = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data/events.json').read_text(encoding='utf-8'))['party_spot']
    centre = unreal.Vector(spot[0], spot[1], 0)
    people = [p for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson)
              if p.get_editor_property('ambient') and not p.get_editor_property('seated') and not p.get_editor_property('employee')]
    people.sort(key=lambda p: (p.get_actor_location() - centre).length())
    out = []
    for i, p in enumerate(people[:6]):
        at = centre + unreal.Vector(300 * ((i % 3) - 1), -350 - 250 * (i // 3), 0)
        hit = unreal.SystemLibrary.line_trace_single(world, at + unreal.Vector(0, 0, 800), at - unreal.Vector(0, 0, 800),
                                                    unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
        z = hit.to_tuple()[4].z if hit else 0
        p.set_actor_location(unreal.Vector(at.x, at.y, z + 95), False, True)
        p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=90), True)
        c = p.get_controller()
        if c:
            c.stop_movement()
        out.append(p.get_editor_property('person_name'))
    return out


def seat_audit(arg=''):
    """PIE: every seated person (ambient chairs, kiosk diners eating) against the seat geometry under them. The seat
    point of each chair-sized mesh near the pelvis comes from its vertices (_seat_local, independent of collision).
    Pelvis bone rides 4-20 cm above the seat top; the pelvis must be within 15 cm (horizontal) of the seat centre.
    FAIL: no chair near (sitting in the air), too high/low, or off the seat (edge/backrest)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    rows, fails = [], []
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
        if not (p.get_editor_property('seated') or str(p.get_editor_property('stage')).find('EATING') >= 0):
            continue
        pel = p.get_component_by_class(unreal.SkeletalMeshComponent).get_socket_location('pelvis')
        row = {'name': p.get_editor_property('person_name'), 'pelvis': [round(pel.x), round(pel.y), round(pel.z)]}
        seats = _chair_seats_world(world, pel, 120)
        if not seats:
            row['verdict'] = 'FAIL no chair near (sitting in the air)'
        else:
            name, seat = min(seats, key=lambda s: (s[1].x - pel.x) ** 2 + (s[1].y - pel.y) ** 2)
            off = ((seat.x - pel.x) ** 2 + (seat.y - pel.y) ** 2) ** .5
            gap = pel.z - seat.z
            row.update({'chair': name, 'gap_cm': round(gap), 'off_cm': round(off)})
            bad = []
            if gap > 20:
                bad.append(f'in the air ({round(gap)} cm above the seat)')
            if gap < 4:
                bad.append(f'sunk into the seat ({round(gap)} cm)')
            if off > 15:
                bad.append(f'{round(off)} cm off the seat centre (edge/backrest)')
            row['verdict'] = 'FAIL ' + '; '.join(bad) if bad else 'ok'
        rows.append(row)
        if row['verdict'] != 'ok':
            fails.append(row['name'])
    return {'checked': len(rows), 'fails': fails, 'rows': rows}


_SEAT_CACHE = {}


def _seat_local(mesh):
    """Seat top of a chair/stool/bench mesh in its own space: the most populated 4 cm slice of upward faces above
    30% of its height (a chair's seat beats the thin top of its backrest; a stool's seat is its top). Vertices, so
    it works with or without collision. None if it has no such surface."""
    if mesh.get_name() in _SEAT_CACHE:
        return _SEAT_CACHE[mesh.get_name()]
    lo = hi = None
    pts = []
    for sec in range(mesh.get_num_sections(0)):
        v, tri, nrm = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(mesh, 0, sec)[:3]
        if not v:
            continue
        zs = [q.z for q in v]
        lo = min(zs) if lo is None else min(lo, min(zs))
        hi = max(zs) if hi is None else max(hi, max(zs))
        pts += [q for q, n in zip(v, nrm) if n.z > .85]
    seat = None
    if pts:
        h = hi - lo
        band = [q for q in pts if q.z >= lo + .3 * h]
        if band:
            slices = {}
            for q in band:
                slices.setdefault(round(q.z / 4), []).append(q)
            top = max(slices.values(), key=len)
            seat = unreal.Vector(sum(q.x for q in top) / len(top), sum(q.y for q in top) / len(top), max(q.z for q in top))
    _SEAT_CACHE[mesh.get_name()] = seat
    return seat


def _chair_seats_world(world, near=None, radius=150):
    """World seat points of every chair-sized mesh (60-110 cm tall, footprint under 80 cm; actors and instances),
    optionally only within radius (horizontal) of near."""
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.static_mesh
            if not mesh:
                continue
            ts = ([comp.get_instance_transform(i, True) for i in range(comp.get_instance_count())]
                  if isinstance(comp, unreal.InstancedStaticMeshComponent) else [comp.get_world_transform()])
            bb = mesh.get_bounding_box()
            for t in ts:
                size = (bb.max - bb.min) * t.scale3d
                if not (60 < abs(size.z) < 110 and abs(size.x) < 80 and abs(size.y) < 80):
                    continue
                if near is not None:
                    c = t.transform_location((bb.min + bb.max) * .5)
                    if ((c.x - near.x) ** 2 + (c.y - near.y) ** 2) ** .5 > radius:
                        continue
                local = _seat_local(mesh)
                if local is not None:
                    out.append((mesh.get_name(), t.transform_location(local)))
    return out


def chair_seats(arg=''):
    """Seats of the real chairs around the hotel restaurant tables (Content/Data/restaurant.json "tables"): every
    chair-sized mesh part (60-110 cm tall, footprint under 80 cm) within 130 cm of a table centre. The seat is the
    largest group of upward faces between 30% and 65% of the chair height (mesh vertices, so it works without
    collision); its centroid and height are written as [x, y, z_top, yaw facing the table] to
    Content/Data/hotel_seats.json. Run in the editor world (not PIE)."""
    import json, math
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    data = Path(unreal.Paths.project_content_dir()) / 'Data'
    tables = json.loads((data / 'restaurant.json').read_text(encoding='utf-8'))['tables']
    seats = []
    def add_seat(mesh, t):
        bb = mesh.get_bounding_box()
        size = (bb.max - bb.min) * t.scale3d
        if not (60 < abs(size.z) < 110 and abs(size.x) < 80 and abs(size.y) < 80):
            return
        centre = t.transform_location((bb.min + bb.max) * .5)
        near = [i for i, tb in enumerate(tables) if math.hypot(centre.x - tb[0], centre.y - tb[1]) < 130]
        if not near:
            return
        local = _seat_local(mesh)
        if local is None:
            return
        w = t.transform_location(local)
        tb = tables[near[0]]
        yaw = math.degrees(math.atan2(tb[1] - w.y, tb[0] - w.x))
        seats.append({'table': near[0], 'mesh': mesh.get_name(), 'seat': [round(w.x, 1), round(w.y, 1), round(w.z, 1), round(yaw, 1)]})

    def finish(seats):
        doc = {'_doc': 'Real chair seats of the hotel restaurant (mare_hud.chair_seats from the chair meshes in Coast): '
                       '[x, y, seat top z, yaw facing the table] in world cm, by restaurant.json table index.',
               'seats': seats}
        (data / 'hotel_seats.json').write_text(json.dumps(doc, ensure_ascii=False, indent=1) + chr(10), encoding='utf-8')
        return seats
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.static_mesh
            if not mesh:
                continue
            ts = ([comp.get_instance_transform(i, True) for i in range(comp.get_instance_count())]
                  if isinstance(comp, unreal.InstancedStaticMeshComponent) else [comp.get_world_transform()])
            for t in ts:
                add_seat(mesh, t)
    seats.sort(key=lambda s: (s['table'], s['seat'][0], s['seat'][1]))
    return finish(seats)


def run(action, arg=''):
    if action == 'badges':
        # PIE: every staff badge with its owner, role and where it sits relative to the owner's chest (spine_05),
        # in the owner's frame [forward, left, up] cm: a badge belongs ~13-15 cm ahead, ~10 left of the spine.
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
            for c in p.get_components_by_class(unreal.StaticMeshComponent):
                if c.static_mesh and 'badge' in c.static_mesh.get_name():
                    rig = p.get_component_by_class(unreal.SkeletalMeshComponent)
                    sp = rig.get_socket_location('spine_05')
                    d = c.get_world_location() - sp
                    f, r = p.get_actor_forward_vector(), p.get_actor_right_vector()
                    out.append({'name': p.get_editor_property('person_name'), 'visible': c.is_visible(),
                                'rel_cm': [round(d.x * f.x + d.y * f.y), round(-(d.x * r.x + d.y * r.y)), round(d.z)],
                                'attach': str(c.get_attach_socket_name()), 'parent': c.get_attach_parent().get_name() if c.get_attach_parent() else ''})
        return out
    if action == 'seated':
        # PIE: seated people (ambient chairs and kiosk tables) with position, yaw and the clip playing.
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
            if p.get_editor_property('seated') or p.get_editor_property('table_index') >= 0:
                inst = p.get_component_by_class(unreal.SkeletalMeshComponent).get_anim_instance()
                clip = ''
                try:
                    clip = inst.get_current_asset().get_name()
                except Exception:
                    pass
                l = p.get_actor_location()
                out.append({'name': p.get_editor_property('person_name'), 'pos': [round(l.x), round(l.y), round(l.z)],
                            'yaw': round(p.get_actor_rotation().yaw), 'clip': clip})
        return out
    if action == 'near':
        # PIE: static meshes (actors and instances) within r cm of "x,y,z,r": name, distance, bounds height.
        x, y, z, r = (float(v) for v in arg.split(','))
        at = unreal.Vector(x, y, z)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for c in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            for comp in c.get_components_by_class(unreal.StaticMeshComponent):
                mesh = comp.static_mesh
                if not mesh:
                    continue
                ts = ([comp.get_instance_transform(i, True) for i in range(comp.get_instance_count())]
                  if isinstance(comp, unreal.InstancedStaticMeshComponent) else [comp.get_world_transform()])
                for t in ts:
                    d = (t.translation - at).length()
                    if d < r:
                        bb = mesh.get_bounding_box()
                        size = (bb.max - bb.min) * t.scale3d
                        out.append([round(d), mesh.get_name(), [round(v) for v in (t.translation.x, t.translation.y, t.translation.z)], round(t.rotation.rotator().yaw),
                                    [round(abs(v)) for v in (size.x, size.y, size.z)], round(bb.min.z * t.scale3d.z + t.translation.z), round(bb.max.z * t.scale3d.z + t.translation.z)])
        return sorted(out)[:40]
    if action == 'seataudit':
        return seat_audit(arg)
    if action == 'chairseats':
        return chair_seats(arg)
    if action == 'party':
        return party_qa(arg)
    if action == 'person':
        return person_qa(arg)
    if action == 'cmd':
        # PIE console command(s), separated by ';' (QA: mare.PoolAutoPlay 1; mare.PoolQA).
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        for c in arg.split(';'):
            unreal.SystemLibrary.execute_console_command(world, c.strip())
        return 'ok'
    if action == 'staff':
        return staff_qa(arg)
    if action == 'loops':
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        audio = next(o for o in unreal.ObjectIterator(unreal.MareAudioWorld) if o.get_outer() == world)
        return {n: round(audio.loop_level(n), 3) for n in arg.split(',')}
    if action == 'phone':
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        pc.open_phone(int(arg))
        return 'open'
    if action == 'festival':
        return import_models('Festival', '/Game/Custom/Festival')
    if action == 'festival1':
        import mare_hotel_lobby
        glb = MODELS / 'Festival' / f'{arg}.glb'
        dest = f'/Game/Custom/Festival/{arg}'
        if unreal.EditorAssetLibrary.does_directory_exist(dest):
            unreal.EditorAssetLibrary.delete_directory(dest)
        return mare_hotel_lobby._import(glb, dest, arg, False, search=False).get_path_name()
    if action == 'sunphoto':
        return photo_sun()
    if action == 'photo':
        return photo_qa(arg) if arg else photo_take()
    if action == 'rays':
        return rays(arg)
    if action == 'gameroomx':
        return import_game_room_extras()
    if action == 'fan':
        return trace_fan(arg)
    if action == 'target':
        return target_qa(arg)
    if action == 'inst':
        return actor_instances(arg)
    if action == 'find':
        return find_actors(arg)
    if action == 'bizqa':
        return biz_qa(arg)
    if action == 'biz':
        return biz_bounds()
    if action == 'bar':
        return bar_qa(arg)
    if action == 'sfx':
        return import_sfx()
    if action == 'icons':
        return import_icons()
    if action == 'poolmess':
        return import_models('PoolMess', '/Game/Custom/PoolMess')
    if action == 'mess':
        return import_models('RoomMess', '/Game/Custom/RoomMess')
    if action == 'pool':
        return import_models('GameRoom', '/Game/Custom/GameRoom')
    if action == 'boats':
        return import_models('Boats', '/Game/Custom/Boats')
    if action == 'fabfood':
        return import_models('FabFood', '/Game/Custom/FabFood')
    if action == 'fabfurniture':
        return import_models('FabFurniture', '/Game/Custom/FabFurniture')
    if action == 'fabfestival':
        return import_models('FabFestival', '/Game/Custom/Festival')
    if action == 'staffmodels':
        return import_models('Staff', '/Game/Custom/Staff')
    if action == 'desk':
        return import_models('Reception', '/Game/Custom/Reception')
    raise ValueError(action)
