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


def stand_audit(arg=''):
    """PIE: people standing (not seated) whose body is inside furniture. Furniture = static meshes 40-110 cm tall
    with a footprint under 4 m (tables, counters, chairs, stools); the pelvis inside a mesh's oriented box (shrunk by
    5 cm) with the mesh top above the feet = walking through it. Returns the offenders with the mesh and position."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    boxes = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if isinstance(a, unreal.MarePerson):
            continue
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.static_mesh
            if not mesh or not comp.is_visible():
                continue
            bb = mesh.get_bounding_box()
            ts = ([comp.get_instance_transform(i, True) for i in range(comp.get_instance_count())]
                  if isinstance(comp, unreal.InstancedStaticMeshComponent) else [comp.get_world_transform()])
            for t in ts:
                size = (bb.max - bb.min) * t.scale3d
                if 40 < abs(size.z) < 110 and abs(size.x) < 400 and abs(size.y) < 400 and max(abs(size.x), abs(size.y)) > 30:
                    boxes.append((mesh.get_name(), a.get_actor_label(), t, bb))
    out = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
        if p.get_editor_property('seated') or str(p.get_editor_property('stage')).find('EATING') >= 0:
            continue
        rig = p.get_component_by_class(unreal.SkeletalMeshComponent)
        for bone in ('pelvis', 'spine_03'):
            q = rig.get_socket_location(bone)
            hit = None
            for name, label, t, bb in boxes:
                l = t.inverse_transform_location(q)
                sc = t.scale3d
                if (bb.min.x * abs(sc.x) + 5 < l.x * abs(sc.x) < bb.max.x * abs(sc.x) - 5 and
                        bb.min.y * abs(sc.y) + 5 < l.y * abs(sc.y) < bb.max.y * abs(sc.y) - 5 and
                        bb.min.z <= l.z <= bb.max.z + 15):
                    hit = (name, label)
                    break
            if hit:
                out.append({'name': p.get_editor_property('person_name'), 'employee': p.get_editor_property('employee'),
                            'bone': bone, 'at': [round(q.x), round(q.y), round(q.z)], 'inside': hit[0], 'actor': hit[1]})
                break
    return out


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
    if action == 'foliagealpha':
        # Reimport the foliage base colours with their alpha (tools/ue58/fix_foliage_alpha.py writes <image>_rgba.png
        # next to the Poly Haven originals) over the texture assets of the same name under /Game/Nature, then make
        # every material using them Masked with the base colour alpha as opacity mask.
        import glob
        lib = unreal.MaterialEditingLibrary
        pngs = {Path(f).name[:-len('_rgba.png')]: f for f in glob.glob('D:/Assets/PolyHaven/*/textures/*_rgba.png')}
        out = []
        for path in unreal.EditorAssetLibrary.list_assets('/Game/Nature', True, False):
            name = path.split('/')[-1].split('.')[0]
            if name not in pngs or str(unreal.EditorAssetLibrary.find_asset_data(path).asset_class_path.asset_name) != 'Texture2D':
                continue
            folder = '/'.join(path.split('/')[:-1])
            task = unreal.AssetImportTask()
            task.set_editor_property('filename', pngs[name])
            task.set_editor_property('destination_path', folder)
            task.set_editor_property('destination_name', name)
            task.set_editor_property('replace_existing', True)
            task.set_editor_property('automated', True)
            task.set_editor_property('save', True)
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            tex = unreal.load_asset(path.split('.')[0])
            row = {'texture': name, 'size': [tex.blueprint_get_size_x(), tex.blueprint_get_size_y()], 'materials': []}
            for ref in unreal.EditorAssetLibrary.find_package_referencers_for_asset(path.split('.')[0], False):
                m = unreal.load_asset(ref)
                if not isinstance(m, unreal.Material):
                    continue
                if m.get_editor_property('blend_mode') != unreal.BlendMode.BLEND_MASKED:
                    node = lib.get_material_property_input_node(m, unreal.MaterialProperty.MP_OPACITY)
                    if node:
                        lib.connect_material_property(node, lib.get_material_property_input_node_output_name(m, unreal.MaterialProperty.MP_OPACITY),
                                                      unreal.MaterialProperty.MP_OPACITY_MASK)
                    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
                has_mask = lib.get_material_property_input_node(m, unreal.MaterialProperty.MP_OPACITY_MASK) is not None
                m.set_editor_property('opacity_mask_clip_value', .33)
                errors = lib.recompile_material(m)
                unreal.EditorAssetLibrary.save_loaded_asset(m, False)
                row['materials'].append({'mat': m.get_name(), 'mask_input': has_mask, 'errors': len(errors or [])})
            out.append(row)
        return out
    if action == 'translucent':
        # "folder[,fix]": materials under the folder with translucent blend. With ",fix": foliage cut-outs become
        # Masked (Lumen leaves translucent leaves unlit and badly sorted: black shards in the lawn), the node feeding
        # Opacity also feeds Opacity Mask, recompiled and saved.
        parts = arg.split(',')
        out = []
        for path in unreal.EditorAssetLibrary.list_assets(parts[0], True, False):
            if not path.endswith(path.split('/')[-1].split('.')[0]) and '.' in path.split('/')[-1]:
                pass
            data = unreal.EditorAssetLibrary.find_asset_data(path)
            if str(data.asset_class_path.asset_name) != 'Material':
                continue
            m = unreal.load_asset(path)
            if m.get_editor_property('blend_mode') != unreal.BlendMode.BLEND_TRANSLUCENT:
                continue
            row = {'mat': m.get_path_name()}
            if len(parts) > 1 and parts[1] == 'fix':
                lib = unreal.MaterialEditingLibrary
                node = lib.get_material_property_input_node(m, unreal.MaterialProperty.MP_OPACITY)
                if node:
                    out_name = lib.get_material_property_input_node_output_name(m, unreal.MaterialProperty.MP_OPACITY)
                    lib.connect_material_property(node, out_name, unreal.MaterialProperty.MP_OPACITY_MASK)
                m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
                m.set_editor_property('opacity_mask_clip_value', .33)
                lib.recompile_material(m)
                unreal.EditorAssetLibrary.save_loaded_asset(m, False)
                row['fixed'] = bool(node)
            out.append(row)
        return out
    if action == 'meshmats':
        # "mesh_name": materials of the placed mesh with that name (any world), their parents, blend mode and textures.
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() or             unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            for comp in a.get_components_by_class(unreal.StaticMeshComponent):
                mesh = comp.static_mesh
                if not mesh or mesh.get_name() != arg:
                    continue
                out = {'mesh': mesh.get_path_name(), 'actor': a.get_actor_label(), 'slots': []}
                for i in range(comp.get_num_materials()):
                    m = comp.get_material(i)
                    row = {'mat': m.get_path_name() if m else None}
                    if isinstance(m, unreal.MaterialInstance):
                        row['parent'] = m.get_editor_property('parent').get_path_name()
                        row['textures'] = [f"{t.get_editor_property('parameter_info').name}={t.get_editor_property('parameter_value').get_name() if t.get_editor_property('parameter_value') else None}"
                                           for t in m.get_editor_property('texture_parameter_values')]
                    base = m.get_base_material() if m else None
                    if base:
                        row['blend'] = str(base.get_editor_property('blend_mode'))
                        row['two_sided'] = base.get_editor_property('two_sided')
                    out['slots'].append(row)
                return out
        return 'not found'
    if action == 'tops':
        # "mesh_name,x,y,r,zmin,zmax": upward faces of the placed mesh of that name nearest (x, y) within r, between
        # zmin and zmax (world), as world x/y ranges per 5 cm slice: where a counter or table top really is.
        name, x, y, r, zmin, zmax = arg.split(',')
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() or             unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        found = None
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            for comp in a.get_components_by_class(unreal.StaticMeshComponent):
                if comp.static_mesh and comp.static_mesh.get_name() == name:
                    ts = ([comp.get_instance_transform(i, True) for i in range(comp.get_instance_count())]
                          if isinstance(comp, unreal.InstancedStaticMeshComponent) else [comp.get_world_transform()])
                    for t in ts:
                        d = ((t.translation.x - float(x)) ** 2 + (t.translation.y - float(y)) ** 2) ** .5
                        if d < float(r) and (found is None or d < found[0]):
                            found = (d, comp.static_mesh, t)
        if not found:
            return 'not found'
        _, mesh, t = found
        slices = {}
        for sec in range(mesh.get_num_sections(0)):
            v, tri, nrm = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(mesh, 0, sec)[:3]
            for q, n in zip(v, nrm):
                w = t.transform_location(q)
                if n.z > .85 and float(zmin) <= w.z <= float(zmax):
                    k = round(w.z / 5) * 5
                    lo, hi = slices.get(k, ([1e9, 1e9], [-1e9, -1e9]))
                    slices[k] = ([min(lo[0], w.x), min(lo[1], w.y)], [max(hi[0], w.x), max(hi[1], w.y)])
        return {k: [[round(c) for c in v[0]], [round(c) for c in v[1]]] for k, v in sorted(slices.items())}
    if action == 'standaudit':
        return stand_audit(arg)
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
    if action == 'fabbikes':
        # Fab bicycles (tools/ue58/prep_fab_food.py bike_<colour>) replace the generated bike_<colour> meshes: import,
        # cap their maps at 2048, swap the mesh of the level's bike instances and point imported_meshes.json at the
        # new meshes so a rebuild keeps them. The new bike is built in the old one's frame (length on Y, base z=0).
        import json
        out = import_models('FabBikes', '/Game/Custom/Bikes') if arg != 'swap' else {}
        for path in unreal.EditorAssetLibrary.list_assets('/Game/Custom/Bikes', True, False):
            if str(unreal.EditorAssetLibrary.find_asset_data(path).asset_class_path.asset_name) == 'Texture2D':
                t = unreal.load_asset(path)
                t.set_editor_property('max_texture_size', 2048)
                unreal.EditorAssetLibrary.save_loaded_asset(t, False)
        data = Path(unreal.Paths.project_content_dir()) / 'Data'
        world = json.loads((data / 'world.json').read_text(encoding='utf-8-sig'))
        mapping = json.loads((data / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
        index = {}
        for r in world['instances']:
            if r['name'].startswith('bike_') and r['name'] != 'gym_bike':
                index[r['name']] = f"World_{r['mesh_index']:04d}"
        swapped = []
        for name, world_mesh in index.items():
            colour = name.split('_', 1)[1]
            new_path = f'/Game/Custom/Bikes/fab_bike_{colour}/fab_bike_{colour}.fab_bike_{colour}'
            mesh = unreal.load_asset(new_path)
            if not mesh:
                swapped.append(f'{name}: missing {new_path}')
                continue
            mapping[world_mesh] = new_path
            for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
                if a.get_actor_label() == 'Maré · ' + name:
                    for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                        c.set_static_mesh(mesh)
                        swapped.append(f'{name}: {c.get_instance_count()} instances')
        (data / 'imported_meshes.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return {'imported': out, 'swapped': swapped}
    if action == 'instances':
        # "label prefix": every instance of the editor-world actors whose label starts with it: [label, x, y, z, yaw].
        out = []
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            if a.get_actor_label().startswith(arg):
                for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                    for i in range(c.get_instance_count()):
                        t = c.get_instance_transform(i, True)
                        out.append([a.get_actor_label()[7:] + str(i), round(t.translation.x), round(t.translation.y), round(t.translation.z), round(t.rotation.rotator().yaw)])
        return out
    if action == 'clearbikes':
        # After fitbikes: the old spots leaned the bikes against posts, chairs and benches. Ground = the lowest surface
        # under the base (not a bench top); then the smallest shift (sideways first, then along the length) that keeps
        # sample points of the bike (wheels and frame) out of every nearby prop box. Level and world.json both change.
        import json
        from mare_world_builder import transform
        world_ = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        data = Path(unreal.Paths.project_content_dir()) / 'Data'
        doc = json.loads((data / 'world.json').read_text(encoding='utf-8-sig'))
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        # 5 cm steps along the bike: a 9 cm post fitted between 12 cm samples and stayed inside the frame.
        # Full width: handlebar +-27 cm at the front top, pedals +-16 cm at the crank.
        samples = ([unreal.Vector(x, y, z) for x in (-9, 0, 9) for y in range(-84, 85, 5) for z in (8, 30, 55, 80, 100)] +
                   [unreal.Vector(x, y, z) for x in range(-27, 28, 6) for y in range(-62, -34, 5) for z in (95, 105)] +
                   [unreal.Vector(x, y, z) for x in (-16, -12, 12, 16) for y in range(-15, 16, 5) for z in (20, 32)])
        out = []
        for a in actors:
            label = a.get_actor_label()
            if not label.startswith('Maré · bike_'):
                continue
            name = label[7:]
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                for i in range(c.get_instance_count()):
                    t = c.get_instance_transform(i, True)
                    base = t.translation
                    boxes = []
                    for b_ in actors:
                        if b_ == a or b_.get_actor_label().startswith(('PCG', 'Mare · Gramado', 'Maré · Ground')):
                            continue
                        for comp in b_.get_components_by_class(unreal.StaticMeshComponent):
                            mesh = comp.static_mesh
                            if not mesh or not comp.is_visible() or 'grass' in mesh.get_name().lower():
                                continue
                            bb = mesh.get_bounding_box()
                            ts = ([comp.get_instance_transform(k, True) for k in range(comp.get_instance_count())]
                                  if isinstance(comp, unreal.InstancedStaticMeshComponent) else [comp.get_world_transform()])
                            for tt in ts:
                                if (tt.translation - base).length() > 900:
                                    continue
                                pts = [tt.transform_location(unreal.Vector(x, y, z)) for x in (bb.min.x, bb.max.x)
                                       for y in (bb.min.y, bb.max.y) for z in (bb.min.z, bb.max.z)]
                                lo = unreal.Vector(min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts))
                                hi = unreal.Vector(max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts))
                                if hi.z - lo.z < 8 or (hi.x - lo.x > 400 and hi.y - lo.y > 400):
                                    continue        # ground plates and whole buildings
                                if hi.x < base.x - 300 or lo.x > base.x + 300 or hi.y < base.y - 300 or lo.y > base.y + 300:
                                    continue
                                boxes.append((lo, hi, mesh.get_name()))
                    side = t.rotation.rotate_vector(unreal.Vector(1, 0, 0))
                    along = t.rotation.rotate_vector(unreal.Vector(0, 1, 0))

                    def ground(at):
                        hits = unreal.SystemLibrary.line_trace_multi(world_, at + unreal.Vector(0, 0, 80), at - unreal.Vector(0, 0, 150),
                                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a], unreal.DrawDebugTrace.NONE, True) or []
                        zs = [h.to_tuple()[5].z for h in hits]
                        return min(zs) if zs else at.z

                    def hit_by(tr):
                        for q in samples:
                            w = tr.transform_location(q)
                            for lo, hi, n in boxes:
                                if lo.x - 4 < w.x < hi.x + 4 and lo.y - 4 < w.y < hi.y + 4 and lo.z < w.z < hi.z:   # 4 cm clearance
                                    return n
                        return None
                    best = None
                    cands = sorted(((sd, ln) for sd in range(-90, 91, 10) for ln in (0, -20, 20, -40, 40)), key=lambda v: abs(v[0]) + 1.5 * abs(v[1]))
                    for sd, ln in cands:
                        at = base + side * sd + along * ln
                        at.z = ground(at)
                        tr = unreal.Transform(at, t.rotation.rotator(), unreal.Vector(1, 1, 1))
                        blocker = hit_by(tr)
                        if not blocker:
                            best = (tr, sd, ln)
                            break
                    if not best:
                        out.append(f'{name}[{i}] no free spot (blocked by {hit_by(t)})')
                        continue
                    tr, sd, ln = best
                    first = hit_by(unreal.Transform(base, t.rotation.rotator(), unreal.Vector(1, 1, 1)))
                    old = unreal.Vector(base.x, base.y, base.z)
                    c.update_instance_transform(i, tr, True, True, True)
                    for row in doc['instances']:
                        if row['name'] == name:
                            rt = transform(row['transform'])
                            if rt is not None and (rt.translation - old).length() < 1.0:
                                q = tr.translation
                                row['transform']['position'] = [q.x / 100, q.z / 100, q.y / 100]
                                break
                    out.append(f'{name}[{i}] was touching {first}; moved side {sd} along {ln}, z {round(old.z)}->{round(tr.translation.z)}')
        (data / 'world.json').write_text(json.dumps(doc, ensure_ascii=False, indent='	'), encoding='utf-8')
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return out
    if action == 'fitbikes':
        # Stand every Fab bike where the old generated one was: the old World_ mesh had its height on local X with an
        # off-centre origin (bbox x -74..35, y -35..141) and leaned 10 degrees; the new one has length on Y, height
        # on Z, origin at the base centre and a centre stand, so it stands upright on the ground below the old base,
        # along the old length. world.json gets the same transform (inverse of mare_world_builder.transform).
        import json
        from mare_world_builder import transform
        world_ = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        data = Path(unreal.Paths.project_content_dir()) / 'Data'
        doc = json.loads((data / 'world.json').read_text(encoding='utf-8-sig'))
        old_lo, old_hi = unreal.Vector(-74, -35, -32), unreal.Vector(35, 141, 32)
        out = []
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            label = a.get_actor_label()
            if not (label.startswith('Maré · bike_') and label != 'Maré · bike_gym'):
                continue
            name = label[7:]
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                for i in range(c.get_instance_count()):
                    t = c.get_instance_transform(i, True)
                    ux = t.rotation.rotate_vector(unreal.Vector(1, 0, 0))
                    uy = t.rotation.rotate_vector(unreal.Vector(0, 1, 0))
                    if abs(ux.z) < .5:
                        out.append(f'{name}[{i}] skipped (already upright)')
                        continue
                    base_x = old_lo.x if ux.z > 0 else old_hi.x
                    base = t.transform_location(unreal.Vector(base_x, (old_lo.y + old_hi.y) / 2, 0))
                    hit = unreal.SystemLibrary.line_trace_single(world_, base + unreal.Vector(0, 0, 60), base - unreal.Vector(0, 0, 120),
                                                                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a], unreal.DrawDebugTrace.NONE, True)
                    if hit:
                        base.z = hit.to_tuple()[5].z
                    fwd = unreal.Vector(uy.x, uy.y, 0)
                    fwd = fwd * (1.0 / max(fwd.length(), 1e-6))
                    rot = unreal.MathLibrary.make_rot_from_yz(fwd, unreal.Vector(0, 0, 1))
                    new = unreal.Transform(base, rot, unreal.Vector(1, 1, 1))
                    old_loc = unreal.Vector(t.translation.x, t.translation.y, t.translation.z)
                    c.update_instance_transform(i, new, True, True, True)
                    q = rot.quaternion()
                    X, Y, Z = (q.rotate_vector(v) for v in (unreal.Vector(1, 0, 0), unreal.Vector(0, 1, 0), unreal.Vector(0, 0, 1)))
                    for row in doc['instances']:
                        if row['name'] == name:
                            rt = transform(row['transform'])
                            if rt is not None and (rt.translation - old_loc).length() < 1.0:
                                row['transform']['basis'] = [[X.x, X.z, X.y], [Z.x, Z.z, Z.y], [Y.x, Y.z, Y.y]]
                                row['transform']['position'] = [base.x / 100, base.z / 100, base.y / 100]
                                chk = transform(row['transform'])
                                out.append(f'{name}[{i}] -> {[round(base.x), round(base.y), round(base.z)]} yaw {round(rot.yaw)} '
                                           f'json ok {(chk.translation - base).length() < 1 and abs(chk.rotation.rotator().yaw - rot.yaw) % 360 < 1}')
                                break
        (data / 'world.json').write_text(json.dumps(doc, ensure_ascii=False, indent='	'), encoding='utf-8')
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return out
    if action == 'fabfurniture':
        return import_models('FabFurniture', '/Game/Custom/FabFurniture')
    if action == 'fabfestival':
        return import_models('FabFestival', '/Game/Custom/Festival')
    if action == 'staffmodels':
        return import_models('Staff', '/Game/Custom/Staff')
    if action == 'desk':
        return import_models('Reception', '/Game/Custom/Reception')
    raise ValueError(action)
