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


def run(action, arg=''):
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
    if action == 'staffmodels':
        return import_models('Staff', '/Game/Custom/Staff')
    if action == 'desk':
        return import_models('Reception', '/Game/Custom/Reception')
    raise ValueError(action)
