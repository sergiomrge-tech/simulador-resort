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


def footprint_material():
    """The glTF importer's BLEND material leaves the alpha input unwired (Interchange: "AlphaMode invalid for
    MF_Default_Body"); rebuild it by hand: translucent, colour + opacity from the RGBA mask, normal map of the dent."""
    mel = unreal.MaterialEditingLibrary
    folder = '/Game/Custom/Beach/beach_footprint'
    m = unreal.load_asset(f'{folder}/beach_footprint.beach_footprint')
    for e in list(mel.get_material_expressions(m)) if hasattr(mel, 'get_material_expressions') else []:
        mel.delete_material_expression(m, e)
    m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE)
    m.set_editor_property('used_with_instanced_static_meshes', True)
    col = mel.create_material_expression(m, unreal.MaterialExpressionTextureSample, -400, 0)
    col.texture = unreal.load_asset(f'{folder}/beach_footprint_color')
    nor = mel.create_material_expression(m, unreal.MaterialExpressionTextureSample, -400, 300)
    tex = unreal.load_asset(f'{folder}/beach_footprint_normal')
    tex.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
    tex.set_editor_property('srgb', False)
    unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
    nor.texture = tex
    nor.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    rough = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -200, 200)
    rough.set_editor_property('r', .95)
    mel.connect_material_property(col, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(col, 'A', unreal.MaterialProperty.MP_OPACITY)
    mel.connect_material_property(nor, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, False)
    return {'errors': [str(e) for e in errors] if errors else []}


# Paved surfaces that collect water (exported village streets and the square); sidewalks (World_0674) drain.
PUDDLE_SURFACES = ('World_0673', 'World_0675', 'World_1175', 'World_1418', 'World_1420', 'World_1415', 'World_1417',
                   'World_2023', 'World_2024', 'World_0676', 'World_1881')


def place_puddles(count=70, seed=31):
    """Rain puddles (M_Puddle on the engine plane, one HISM) on the village streets and the square: random points
    whose first hit is one of PUDDLE_SURFACES, 1.2-2.6 m wide, 3 m apart. The material shows them only while it
    rains (MPC Rain), so the actor stays in the level. Rebuilt from scratch on each run."""
    import random
    from editor_toolset.toolsets.actor import ActorTools
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if 'MarePuddles' in [str(t) for t in a.tags]:
            actors.destroy_actor(a)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    rnd = random.Random(seed)
    points = []
    tries = 0
    while len(points) < count and tries < 20000:
        tries += 1
        x, y = rnd.uniform(-500, 10800), rnd.uniform(1500, 7200)
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 1500), unreal.Vector(x, y, -300),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        if not hit:
            continue
        t = hit.to_tuple()
        comp = t[10]
        name = comp.static_mesh.get_name() if isinstance(comp, unreal.StaticMeshComponent) and comp.static_mesh else ''
        if name not in PUDDLE_SURFACES or t[7].z < .97:
            continue
        if any((x - px) ** 2 + (y - py) ** 2 < 300 ** 2 for px, py, _ in points):
            continue
        points.append((x, y, t[5].z))
    root = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector())
    root.set_actor_label('Mare · Poças de chuva')
    root.tags = [unreal.Name('MareGenerated'), unreal.Name('MarePuddles')]
    root.set_folder_path('Weather')
    comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_Puddles')
    comp.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Plane'))
    comp.set_material(0, unreal.load_asset('/Game/World/Materials/M_Puddle'))
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    comp.set_editor_property('cast_shadow', False)
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    transforms = []
    for x, y, z in points:
        s = rnd.uniform(1.2, 2.6)
        transforms.append(unreal.Transform(unreal.Vector(x, y, z + .4), unreal.Rotator(yaw=rnd.uniform(-180, 180)),
                                           unreal.Vector(s, s * rnd.uniform(.7, 1.0), 1)))
    comp.add_instances(transforms, False, True)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'puddles': len(points), 'tries': tries}


def pousada_floor():
    """Pousada reception floor (World_0009, a teal paint with green blotches): Poly Haven patterned_terracotta_tiling
    (CC0, 2.15 m per tile of the scan), world-aligned so the tiles keep their size whatever the mesh UVs are."""
    mel = unreal.MaterialEditingLibrary
    folder = '/Game/Custom/Pousada/floor'
    src = Path('D:/Assets/PolyHaven/patterned_terracotta_tiling')
    tex = {}
    for kind in ('diff', 'nor_gl', 'rough'):
        task = unreal.AssetImportTask()
        task.filename = str(src / f'patterned_terracotta_tiling_{kind}_2k.jpg')
        task.destination_path = folder
        task.destination_name = f'T_PousadaFloor_{kind}'
        task.automated = task.replace_existing = task.save = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        t = unreal.load_asset(f'{folder}/T_PousadaFloor_{kind}')
        if kind != 'diff':
            t.set_editor_property('srgb', False)
        if kind == 'nor_gl':
            t.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
        unreal.EditorAssetLibrary.save_loaded_asset(t, False)
        tex[kind] = t
    path = f'{folder}/M_PousadaFloor'
    m = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_PousadaFloor', folder, unreal.Material, unreal.MaterialFactoryNew())
    for e in list(mel.get_material_expressions(m)):
        mel.delete_material_expression(m, e)
    m.set_editor_property('used_with_instanced_static_meshes', True)
    m.set_editor_property('used_with_nanite', True)
    wp = mel.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -900, 0)
    mask = mel.create_material_expression(m, unreal.MaterialExpressionComponentMask, -750, 0)
    mask.set_editor_property('r', True)
    mask.set_editor_property('g', True)
    mask.set_editor_property('b', False)
    mel.connect_material_expressions(wp, '', mask, '')
    div = mel.create_material_expression(m, unreal.MaterialExpressionDivide, -600, 0)
    div.set_editor_property('const_b', 215.0)
    mel.connect_material_expressions(mask, '', div, 'A')
    samples = {}
    for i, (kind, t) in enumerate(tex.items()):
        s = mel.create_material_expression(m, unreal.MaterialExpressionTextureSample, -400, i * 250)
        s.texture = t
        if kind == 'nor_gl':
            s.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        elif kind == 'rough':
            s.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        mel.connect_material_expressions(div, '', s, 'UVs')
        samples[kind] = s
    mel.connect_material_property(samples['diff'], 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(samples['nor_gl'], 'RGB', unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(samples['rough'], 'R', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = mel.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, False)
    mesh = unreal.load_asset('/Game/World/Models/World_0009/World_0009.World_0009')
    mesh.set_material(0, m)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return {'errors': [str(e) for e in errors] if errors else [], 'material': m.get_path_name()}


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


def import_voices():
    """Short wordless voices of SourceArt/Audio/Voices (tools/ue58/fetch_murmurs.py) -> /Game/Audio/Voices, listed in
    Content/Data/audio.json as groups voice_<mood>_<f|m> at a soft volume (AMarePerson::Express plays them)."""
    import json
    src = Path(unreal.Paths.project_dir()).resolve() / 'SourceArt/Audio/Voices'
    manifest = json.loads((src / 'manifest.json').read_text(encoding='utf-8'))
    catalog_path = Path(unreal.Paths.project_content_dir()).resolve() / 'Data/audio.json'
    catalog = [row for row in json.loads(catalog_path.read_text(encoding='utf-8')) if not str(row.get('group', '')).startswith('voice_')]
    done = 0
    for name in sorted(manifest):
        task = unreal.AssetImportTask()
        task.filename = str(src / f'{name}.wav')
        task.destination_path = '/Game/Audio/Voices'
        task.destination_name = name
        task.automated = True
        task.replace_existing = True
        task.save = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        wave = unreal.load_asset(f'/Game/Audio/Voices/{name}')
        if not isinstance(wave, unreal.SoundWave):
            raise RuntimeError(f'{name}: import gave {wave}')
        mood, sex, _ = name.split('_')
        catalog.append({'id': name, 'path': f'/Game/Audio/Voices/{name}.{name}', 'duration': wave.get_editor_property('duration'),
                        'loop': False, 'group': f'voice_{mood}_{sex}', 'volume': 0.14})
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


def import_game_room_extras(names=None):
    """Foosball and arcade (tools/ue58/gen_game_room_extras.py), or the given names (table tennis set,
    tools/ue58/gen_table_tennis.py), each in a fresh folder of /Game/Custom/GameRoom."""
    import mare_hotel_lobby
    out = {}
    for name in names or ('foosball_table', 'arcade_cabinet'):
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
    if action == 'shapes':
        # PIE: static meshes whose scaled size fits "minxy,maxxy,minz,maxz" inside the box "x0,y0,x1,y1": name -> [count, first position, size]
        v = [float(t) for t in arg.split(',')]
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = {}
        for c in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            for comp in c.get_components_by_class(unreal.StaticMeshComponent):
                mesh = comp.static_mesh
                if not mesh:
                    continue
                bb = mesh.get_bounding_box()
                ts = ([comp.get_instance_transform(i, True) for i in range(comp.get_instance_count())]
                      if isinstance(comp, unreal.InstancedStaticMeshComponent) else [comp.get_world_transform()])
                for t in ts:
                    p = t.translation
                    if not (v[4] <= p.x <= v[6] and v[5] <= p.y <= v[7]):
                        continue
                    size = [abs(q) for q in ((bb.max - bb.min) * t.scale3d).to_tuple()]
                    if v[0] <= size[0] <= v[1] and v[0] <= size[1] <= v[1] and v[2] <= size[2] <= v[3]:
                        e = out.setdefault(mesh.get_name(), [0, [round(p.x), round(p.y), round(p.z)], [round(q) for q in size], c.get_class().get_name()])
                        e[0] += 1
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
    if action == 'mpcdefault':
        # "Name=value": the MPC default (what the editor viewport shows), for QA of the weather materials
        name, value = arg.split('=')
        mpc = unreal.load_asset('/Game/World/Materials/MPC_MareTime')
        params = list(mpc.get_editor_property('scalar_parameters'))
        for p in params:
            if str(p.get_editor_property('parameter_name')) == name:
                p.set_editor_property('default_value', float(value))
        mpc.set_editor_property('scalar_parameters', params)
        return 'ok'
    if action == 'palmlods':
        # Wind on the palms (M_PalmFab_PBR WPO) is ignored by Nanite here: plain meshes with automatic LODs
        # (100/50/25/12 %), and the sway stops beyond 80 m where it cannot be seen.
        import json as _j
        palms = _j.loads((Path(unreal.Paths.project_content_dir()) / 'Data/foliage_visual.json').read_text(encoding='utf-8'))['palms']
        editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        out = {}
        for path in palms:
            m = unreal.load_asset(path)
            st = m.get_editor_property('nanite_settings')
            st.set_editor_property('enabled', False)
            editor.set_nanite_settings(m, st, True)
            opts = unreal.StaticMeshReductionOptions()
            opts.set_editor_property('auto_compute_lod_screen_size', False)
            settings = []
            for pct, screen in ((1.0, 1.0), (.5, .45), (.25, .2), (.12, .08)):
                r = unreal.StaticMeshReductionSettings()
                r.set_editor_property('percent_triangles', pct)
                r.set_editor_property('screen_size', screen)
                settings.append(r)
            opts.set_editor_property('reduction_settings', settings)
            editor.set_lods(m, opts)
            unreal.EditorAssetLibrary.save_loaded_asset(m, False)
            out[m.get_name()] = [m.get_num_triangles(i) for i in range(m.get_num_lods())]
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                if c.static_mesh and c.static_mesh.get_path_name() in palms:
                    c.set_editor_property('evaluate_world_position_offset', True)
                    c.set_editor_property('world_position_offset_disable_distance', 8000)
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return out
    if action == 'palmwpo':
        # palm instance components: WPO evaluation flags (wind needs them); arg 'fix' turns them on
        import json as _j
        palms = set(_j.loads((Path(unreal.Paths.project_content_dir()) / 'Data/foliage_visual.json').read_text(encoding='utf-8'))['palms'])
        out = []
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                if c.static_mesh and c.static_mesh.get_path_name() in palms:
                    row = [a.get_actor_label(), c.static_mesh.get_name(), c.get_material(0).get_path_name() if c.get_material(0) else None, c.static_mesh.get_editor_property('nanite_settings').enabled, c.get_editor_property('evaluate_world_position_offset'),
                           c.get_editor_property('world_position_offset_disable_distance')]
                    if arg == 'fix':
                        c.set_editor_property('evaluate_world_position_offset', True)
                        c.set_editor_property('world_position_offset_disable_distance', 0)
                    out.append(row)
        if arg == 'fix':
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return out[:20]
    if action == 'skyinfo':
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        out = {}
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.VolumetricCloud):
            comp = a.get_component_by_class(unreal.VolumetricCloudComponent)
            m = comp.get_editor_property('material')
            out['cloud'] = m.get_path_name() if m else None
            if isinstance(m, unreal.MaterialInstance):
                out['scalars'] = [[str(v.parameter_info.name), v.parameter_value] for v in m.get_editor_property('scalar_parameter_values')]
                base = m
                while isinstance(base, unreal.MaterialInstance):
                    base = base.get_editor_property('parent')
                out['base'] = base.get_path_name()
                out['params'] = {str(n): unreal.MaterialEditingLibrary.get_material_default_scalar_parameter_value(base, n) for n in unreal.MaterialEditingLibrary.get_scalar_parameter_names(base)}
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SkyAtmosphere):
            comp = a.get_component_by_class(unreal.SkyAtmosphereComponent)
            out['atmo'] = {k: str(comp.get_editor_property(k)) for k in ('rayleigh_scattering_scale', 'mie_scattering_scale', 'mie_absorption_scale')}
        return out
    if action == 'deleteassets':
        # "path,path": remove assets that nothing uses any more (e.g. the dog bark, 03/11)
        return {p: unreal.EditorAssetLibrary.delete_asset(p) for p in arg.split(',')}
    if action == 'foottest':
        # editor: two loose footprints side by side (sand material / wet material) to compare; 'clear' removes them
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for a in actors.get_all_level_actors():
            if 'MareFootTest' in [str(t) for t in a.tags]:
                actors.destroy_actor(a)
        if arg == 'clear':
            return 'cleared'
        mesh = unreal.load_asset('/Game/Custom/Beach/beach_footprint/beach_footprint1')
        out = []
        for dx, mat in ((0, '/Game/World/Materials/M_SandFootprint'), (60, '/Game/Custom/Beach/beach_footprint/beach_footprint')):
            a = actors.spawn_actor_from_object(mesh, unreal.Vector(2600 + dx, -2400, 2), unreal.Rotator())
            a.static_mesh_component.set_material(0, unreal.load_asset(mat))
            a.tags = [unreal.Name('MareFootTest')]
            out.append(mat)
        return out
    if action == 'usetarget':
        # PIE: press E on the first service target with this action (e.g. KioskSign opens the kiosk)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        for t in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MareServiceTarget):
            if str(t.get_editor_property('action')) == arg:
                t.use(pc)
                return 'used ' + arg
        return 'none'
    if action == 'people':
        # PIE: people within "x,y,r": name, position, seated, what they hold (static mesh components)
        x, y, r = [float(v) for v in arg.split(',')]
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
            p = a.get_actor_location()
            if (p.x - x) ** 2 + (p.y - y) ** 2 > r * r:
                continue
            held = [c.static_mesh.get_name() for c in a.get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh]
            out.append([a.get_name()[-14:], round(p.x), round(p.y), round(p.z), a.get_editor_property('consumed'), held])
        return out
    if action == 'comic':
        # PIE QA of the comic events: where the caller is; 'use' presses E on it (opens the exchange)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        out = []
        for t in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MareServiceTarget):
            if str(t.get_editor_property('action')) == 'Comic':
                p = t.get_actor_location()
                out.append({'label': t.get_editor_property('label'), 'at': [round(p.x), round(p.y), round(p.z)]})
                if arg == 'use':
                    t.use(pc)
        return out
    if action == 'footinfo':
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                if c.get_name() == 'Footprints':
                    if arg:
                        c.set_material(0, unreal.load_asset(arg))
                    o, e, r = unreal.SystemLibrary.get_component_bounds(c)
                    m = c.get_material(0)
                    return {'mat': m.get_path_name() if m else None, 'mesh': c.static_mesh.get_path_name() if c.static_mesh else None,
                            'visible': c.is_visible(), 'hidden_game': c.get_editor_property('hidden_in_game'), 'bounds': [str(o), str(e)],
                            'custom': c.get_editor_property('num_custom_data_floats'), 'count': c.get_instance_count()}
        return None
    if action == 'footprints':
        # PIE: how many sand footprints the player left (UMareVisualWorld) and the pawn position
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        n = 0
        comps = []
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                if c.get_name() == 'Footprints':
                    n += c.get_instance_count()
                    comps.append(c.get_owner().get_name())
                    comps += [str([round(v) for v in (c.get_instance_transform(i, True).translation.x, c.get_instance_transform(i, True).translation.y, c.get_instance_transform(i, True).translation.z)]) for i in range(0, c.get_instance_count(), max(1, c.get_instance_count() // 5))]
        pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
        if arg.startswith('walk,'):
            # "walk,x,y,yaw": stand the player on the ground there, walking mode, facing yaw (then mare.WalkTest 1)
            _, x, y, yaw = arg.split(',')
            move = pawn.get_component_by_class(unreal.CharacterMovementComponent)
            pawn.set_actor_location(unreal.Vector(float(x), float(y), 200), False, True)
            move.set_movement_mode(unreal.MovementMode.MOVE_WALKING)
            pawn.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=float(yaw)), True)
            unreal.GameplayStatics.get_player_controller(world, 0).set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=float(yaw)))
        p = pawn.get_actor_location() if pawn else None
        mv = pawn.get_component_by_class(unreal.CharacterMovementComponent) if pawn else None
        return {'mode': str(mv.movement_mode) if mv else None, 'vel': round(pawn.get_velocity().length()) if pawn else 0, 'maxwalk': mv.max_walk_speed if mv else 0, 'footprints': n, 'components': comps, 'walktest': unreal.SystemLibrary.get_console_variable_int_value('mare.WalkTest'), 'pawn': [round(p.x), round(p.y), round(p.z)] if p else None}
    if action == 'gliders':
        # PIE: people and their clip, position and velocity (QA of "walking without moving the legs": compare two calls)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
            inst = p.get_component_by_class(unreal.SkeletalMeshComponent).get_anim_instance()
            clip = ''
            try:
                clip = inst.get_current_asset().get_name()
            except Exception:
                pass
            l, v = p.get_actor_location(), p.get_velocity()
            out.append([p.get_name()[-16:], p.get_editor_property('person_name'), [round(l.x), round(l.y), round(l.z)], round((v.x ** 2 + v.y ** 2) ** .5), clip,
                        bool(p.get_editor_property('ambient')), bool(p.get_editor_property('employee')), str(p.get_attach_parent_actor().get_name() if p.get_attach_parent_actor() else '')])
        return out
    if action == 'gait':
        # PIE: every person's location and both feet relative to the actor, from the rig that drives the pose (QA of
        # natural walking: call twice; a person that moved while the feet stayed put is gliding)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
            rig = p.get_editor_property('mesh')
            t = p.get_actor_transform()
            feet = []
            for bone in ('foot_l', 'foot_r', 'hand_l', 'hand_r'):
                q = t.inverse_transform_location(rig.get_socket_location(bone))
                feet += [round(q.x, 1), round(q.y, 1), round(q.z, 1)]
            l = p.get_actor_location()
            out.append([p.get_name()[-16:], p.get_editor_property('person_name'), [round(l.x), round(l.y), round(l.z)], feet,
                        p.get_editor_property('meta_human'), bool(p.get_editor_property('seated'))])
        return out
    if action == 'wearing':
        # PIE: the skeletal meshes (and first material) each MetaHuman near a point wears: "x,y,radius".
        x, y, rad = (float(v) for v in arg.split(','))
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
            l = a.get_actor_location()
            if (l.x - x) ** 2 + (l.y - y) ** 2 > rad * rad:
                continue
            child = next((c.get_editor_property('child_actor') for c in a.get_components_by_class(unreal.ChildActorComponent) if c.get_editor_property('child_actor')), None)
            parts = []
            for owner in (a, child):
                if not owner:
                    continue
                for c in owner.get_components_by_class(unreal.SkeletalMeshComponent):
                    m = c.get_editor_property('skeletal_mesh_asset') if hasattr(c, 'skeletal_mesh_asset') else c.get_editor_property('skinned_asset')
                    if m and c.is_visible():
                        mat = c.get_material(0)
                        parts.append([c.get_name()[:18], ('HI ' if '_HiGarments' in m.get_path_name() else '') + m.get_path_name().split('/')[-1][:48], mat.get_path_name().split('/')[-1][:40] if mat else None])
            out.append({'who': child.get_name()[:22] if child else a.get_name(), 'at': [round(l.x), round(l.y)], 'parts': parts})
        return out
    if action == 'facebones':
        # PIE: distance (cm) between the face mesh bones and the same bones of the body rig, per nearby MetaHuman.
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        hero = unreal.GameplayStatics.get_player_pawn(world, 0)
        out = []
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
            if (a.get_actor_location() - hero.get_actor_location()).length() > float(arg or 800):
                continue
            body = a.get_component_by_class(unreal.SkeletalMeshComponent)
            child = next((c.get_editor_property('child_actor') for c in a.get_components_by_class(unreal.ChildActorComponent) if c.get_editor_property('child_actor')), None)
            if not child:
                continue
            face = next((c for c in child.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == 'Face'), None)
            if not face:
                continue
            row = {'who': child.get_name()[:20], 'anim': face.get_anim_instance().get_class().get_name() if face.get_anim_instance() else None}
            for bone in ('neck_01', 'neck_02', 'head', 'spine_05'):
                if face.get_bone_index(bone) >= 0 and body.get_bone_index(bone) >= 0:
                    row[bone] = round((face.get_socket_location(bone) - body.get_socket_location(bone)).length(), 2)
            out.append(row)
        return out
    if action == 'bathers':
        # PIE: sunbathers (tag MareBather): clip, play time and the world head/pelvis/feet of the driving rig.
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for a in unreal.GameplayStatics.get_all_actors_with_tag(world, 'MareBather'):
            m = a.get_component_by_class(unreal.SkeletalMeshComponent)
            inst = m.get_anim_instance()
            row = {'at': [round(v) for v in (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z)],
                   'yaw': round(a.get_actor_rotation().yaw), 'mesh': m.get_name(), 'asset': None}
            try:
                row['asset'] = inst.get_current_asset().get_name() if inst and inst.get_current_asset() else None
                row['time'] = round(inst.get_current_time(), 2)
            except Exception as e:
                row['err'] = str(e)[:80]
            for bone in ('pelvis', 'head', 'foot_l', 'foot_r'):
                q = m.get_socket_location(bone)
                row[bone] = [round(q.x), round(q.y), round(q.z)]
            out.append(row)
        return out
    if action == 'importvoices':
        return import_voices()
    if action == 'allpeople':
        # PIE: every actor with a visible skeletal mesh (people, animals, any rig), not only MarePerson: per visible
        # skeletal component, head/hands/feet relative to the actor. Two calls a second apart find who glides (moved,
        # limbs still) and who is frozen (standing, no idle motion at all) on the mesh the player actually sees.
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            comps = [c for c in a.get_components_by_class(unreal.SkeletalMeshComponent) if c.is_visible() and c.get_editor_property('skeletal_mesh_asset' if hasattr(c, 'skeletal_mesh_asset') else 'skinned_asset')]
            if not comps or a.is_hidden_ed() if hasattr(a, 'is_hidden_ed') else False:
                continue
            if a.get_editor_property('hidden'):
                continue
            t = a.get_actor_transform()
            rows = []
            for c in comps:
                names = [str(n) for n in c.get_all_socket_names()] if hasattr(c, 'get_all_socket_names') else []
                pts = []
                for bone in ('head', 'hand_l', 'hand_r', 'foot_l', 'foot_r'):
                    if bone in names or c.get_bone_index(bone) >= 0:
                        q = t.inverse_transform_location(c.get_socket_location(bone))
                        pts += [round(q.x, 2), round(q.y, 2), round(q.z, 2)]
                if pts:
                    rendered = c.was_recently_rendered(0.2) if hasattr(c, 'was_recently_rendered') else None
                    rows.append([c.get_name()[:24], pts, rendered, str(c.get_editor_property('visibility_based_anim_tick_option')).split('.')[-1][:28]])
            if not rows:
                continue
            l = a.get_actor_location()
            name = a.get_editor_property('person_name') if isinstance(a, unreal.MarePerson) else a.get_actor_label()
            seated = bool(a.get_editor_property('seated')) if isinstance(a, unreal.MarePerson) else None
            out.append([a.get_name()[-20:], a.get_class().get_name(), str(name)[:30], [round(l.x), round(l.y), round(l.z)], seated, rows])
        return out
    if action == 'partinfo':
        # PIE: mesh parts whose origin is at "x,y" (within 5 cm): component class, materials, custom data per instance
        x, y = (float(v) for v in arg.split(','))
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for c in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            for comp in c.get_components_by_class(unreal.StaticMeshComponent):
                if not comp.static_mesh:
                    continue
                ism = isinstance(comp, unreal.InstancedStaticMeshComponent)
                ts = [comp.get_instance_transform(i, True) for i in range(comp.get_instance_count())] if ism else [comp.get_world_transform()]
                for i, t in enumerate(ts):
                    if abs(t.translation.x - x) < 5 and abs(t.translation.y - y) < 5:
                        n = comp.get_editor_property('num_custom_data_floats') if ism else 0
                        out.append([c.get_name(), comp.get_class().get_name(), comp.static_mesh.get_name(), i,
                                    [m.get_path_name() if m else None for m in comp.get_materials()], n,
                                    [round(v, 3) for v in comp.get_custom_primitive_data_float_array()] if hasattr(comp, 'get_custom_primitive_data_float_array') else None])
        return out
    if action == 'carrywalk':
        # PIE QA: the person named "name,dish,x,y" holds the dish and walks to x,y (e.g. the kiosk attendant with a tray)
        name, dish, x, y = arg.split(',')
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
            if p.get_editor_property('person_name') == name:
                p.hold_product(dish)
                ok = p.walk_to(unreal.Vector(float(x), float(y), p.get_actor_location().z))
                l = p.get_actor_location()
                return [p.get_name(), [round(l.x), round(l.y), round(l.z)], ok]
        return None
    if action == 'frametime':
        # PIE: world delta seconds sampled "n" times (ms); the editor caps/throttles unfocused, so this is an indicator
        import time as _t
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for _ in range(int(arg or 20)):
            out.append(round(unreal.GameplayStatics.get_world_delta_seconds(world) * 1000, 1))
            _t.sleep(0.05)
        return out
    if action == 'importmusic':
        # import looping music tracks from SourceArt/Audio ("radio_havaiana,music_tema")
        import importlib, mare_audio
        importlib.reload(mare_audio)
        return mare_audio.import_tracks(arg.split(','))
    if action == 'instances_of':
        # PIE: every instance/actor of a mesh name: position and material names (first 60)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for c in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            for comp in c.get_components_by_class(unreal.StaticMeshComponent):
                name, _, box = arg.partition('|')
                if not comp.static_mesh or (name and comp.static_mesh.get_name() != name):
                    continue
                ts = ([comp.get_instance_transform(i, True) for i in range(comp.get_instance_count())]
                      if isinstance(comp, unreal.InstancedStaticMeshComponent) else [comp.get_world_transform()])
                mats = [m.get_name() if m else None for m in comp.get_materials()]
                for t in ts:
                    if box:
                        x0, y0, x1, y1 = (float(v) for v in box.split(','))
                        if not (x0 <= t.translation.x <= x1 and y0 <= t.translation.y <= y1):
                            continue
                    out.append([round(t.translation.x), round(t.translation.y), round(t.translation.z), mats, comp.static_mesh.get_name()])
                    if len(out) >= 60:
                        return out
        return out[:60]
    if action == 'meshes_in':
        # PIE: mesh names inside "x0,y0,x1,y1" with instance count, first position and scaled height (cm)
        x0, y0, x1, y1 = (float(v) for v in arg.split(','))
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = {}
        for c in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            for comp in c.get_components_by_class(unreal.StaticMeshComponent):
                m = comp.static_mesh
                if not m:
                    continue
                h = m.get_bounding_box().max.z - m.get_bounding_box().min.z
                ts = ([comp.get_instance_transform(i, True) for i in range(comp.get_instance_count())]
                      if isinstance(comp, unreal.InstancedStaticMeshComponent) else [comp.get_world_transform()])
                for t in ts:
                    if x0 <= t.translation.x <= x1 and y0 <= t.translation.y <= y1:
                        e = out.setdefault(m.get_name(), [0, [round(t.translation.x), round(t.translation.y), round(t.translation.z)], round(h * t.scale3d.z), [x.get_name() if x else None for x in comp.get_materials()][:3]])
                        e[0] += 1
        return out
    if action == 'traceview':
        # PIE: what a ray from "x,y,z,pitch,yaw" hits first (actor label, mesh, material, distance)
        import math
        x, y, z, pitch, yaw = (float(v) for v in arg.split(','))
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        d = unreal.Vector(math.cos(math.radians(pitch)) * math.cos(math.radians(yaw)), math.cos(math.radians(pitch)) * math.sin(math.radians(yaw)), math.sin(math.radians(pitch)))
        start = unreal.Vector(x, y, z)
        hit = unreal.SystemLibrary.line_trace_single(world, start, start + d * 20000, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        if not hit:
            return None
        t = hit.to_tuple()
        comp = t[10]
        mesh = comp.static_mesh.get_name() if isinstance(comp, unreal.StaticMeshComponent) and comp.static_mesh else str(comp.get_class().get_name())
        mat = comp.get_material(0).get_name() if comp and comp.get_material(0) else None
        return [t[9].get_actor_label() if t[9] else None, mesh, mat, round(t[3]), [round(t[4].x), round(t[4].y), round(t[4].z)]]
    if action == 'tintmat':
        # "material path|r,g,b": multiply the base colour of an imported material by a tint (a Multiply node between
        # whatever feeds Base Color and the output); re-running replaces the tint value instead of stacking nodes.
        path, _, rgb = arg.partition('|')
        r, g, b = (float(v) for v in rgb.split(','))
        mat = unreal.load_asset(path)
        mel = unreal.MaterialEditingLibrary
        src = mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_BASE_COLOR)
        if isinstance(src, unreal.MaterialExpressionMultiply) and src.get_editor_property('desc') == 'MareTint':
            for e in mel.get_material_expressions(mat) if hasattr(mel, 'get_material_expressions') else []:
                if isinstance(e, unreal.MaterialExpressionConstant3Vector) and e.get_editor_property('desc') == 'MareTint':
                    e.set_editor_property('constant', unreal.LinearColor(r, g, b, 1))
        else:
            out_name = mel.get_material_property_input_node_output_name(mat, unreal.MaterialProperty.MP_BASE_COLOR) if hasattr(mel, 'get_material_property_input_node_output_name') else ''
            mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -400, 0)
            mul.set_editor_property('desc', 'MareTint')
            tint = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -650, 120)
            tint.set_editor_property('constant', unreal.LinearColor(r, g, b, 1))
            tint.set_editor_property('desc', 'MareTint')
            mel.connect_material_expressions(src, out_name or 'BaseColor', mul, 'A')
            mel.connect_material_expressions(tint, '', mul, 'B')
            mel.connect_material_property(mul, '', unreal.MaterialProperty.MP_BASE_COLOR)
        errors = list(mel.recompile_material(mat))
        unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
        return {'errors': errors, 'source': src.get_class().get_name() if src else None}
    if action == 'armaudit':
        # PIE: seated people whose forearms/hands are inside a table. A table = static mesh 60-82 cm tall (chairs with a back are taller) with a top
        # 40-250 cm wide; a bone inside its oriented box (top 2 cm under the surface) is an arm through the table.
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        people = [p for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson) if p.get_editor_property('seated')]
        tables = []
        for c in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            if isinstance(c, unreal.MarePerson):
                continue
            for comp in c.get_components_by_class(unreal.StaticMeshComponent):
                m = comp.static_mesh
                if not m or not comp.is_visible():
                    continue
                bb = m.get_bounding_box()
                ts = ([comp.get_instance_transform(i, True) for i in range(comp.get_instance_count())]
                      if isinstance(comp, unreal.InstancedStaticMeshComponent) else [comp.get_world_transform()])
                for t in ts:
                    size = (bb.max - bb.min) * t.scale3d
                    if 60 <= abs(size.z) <= 82 and 55 <= min(abs(size.x), abs(size.y)) and max(abs(size.x), abs(size.y)) <= 250 and 'chair' not in m.get_name().lower():
                        if any((t.translation - p.get_actor_location()).length() < 250 for p in people):
                            tables.append((m.get_name(), t, bb))
        out = []
        for p in people:
            rig = p.get_editor_property('mesh')
            hits = []
            for bone in ('lowerarm_l', 'lowerarm_r', 'hand_l', 'hand_r'):
                w = rig.get_socket_location(bone)
                for name, t, bb in tables:
                    q = t.inverse_transform_location(w)
                    if bb.min.x < q.x < bb.max.x and bb.min.y < q.y < bb.max.y and bb.min.z < q.z < bb.max.z - 2 / max(t.scale3d.z, .01):
                        hits.append([bone, name, round((bb.max.z - q.z) * t.scale3d.z)])
            if hits:
                l = p.get_actor_location()
                out.append([p.get_editor_property('person_name'), [round(l.x), round(l.y), round(l.z)], hits])
        return {'seated': len(people), 'tables_near': len(tables), 'arms_in_tables': out}
    if action == 'hidemesh':
        # PIE only (isolation for visual debugging): "name,0|1" hides/shows every component using that mesh
        name, _, show = arg.partition(',')
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        n = 0
        for c in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            for comp in c.get_components_by_class(unreal.StaticMeshComponent):
                if comp.static_mesh and comp.static_mesh.get_name() == name:
                    comp.set_visibility(show == '1', False)
                    n += 1
        return n
    if action == 'matcheck':
        # a material's Nanite override and usage flags, and a mesh's Nanite state ("material path|mesh path")
        mpath, _, meshpath = arg.partition('|')
        m = unreal.load_asset(mpath)
        out = {'class': m.get_class().get_name()}
        for prop in ('nanite_override_material', 'blend_mode', 'shading_model', 'two_sided', 'used_with_nanite'):
            try:
                v = m.get_editor_property(prop)
                out[prop] = v.get_path_name() if hasattr(v, 'get_path_name') else str(v)
            except Exception as e:
                out[prop] = 'n/a'
        if meshpath:
            mesh = unreal.load_asset(meshpath)
            ns = mesh.get_editor_property('nanite_settings')
            out['mesh_nanite'] = ns.get_editor_property('enabled')
            out['slots'] = [str(sm.material_interface.get_path_name()) if sm.material_interface else None for sm in mesh.get_editor_property('static_materials')]
        return out
    if action == 'grasscull':
        # "start,end,pie|editor": cull distances (cm) of the inland PCG grass HISMs; in the editor world it saves the level
        s, e, where = arg.split(',')
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        world = ues.get_game_world() if where == 'pie' else ues.get_editor_world()
        n = 0
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            if 'MareGrassPCG' not in [str(t) for t in a.tags]:
                continue
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                c.set_editor_property('instance_start_cull_distance', int(s))
                c.set_editor_property('instance_end_cull_distance', int(e))
                if where == 'pie':
                    c.set_cull_distances(int(s), int(e))
                n += 1
        if where != 'pie':
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return n
    if action == 'trunkbox':
        # "mesh path|half_xy|height": replace a plant's whole-canopy box with a box around the trunk/pot only
        # (pivot = trunk base), so the crown never blocks the aim or the player's way above the pot
        p, half, height = arg.split('|')
        m = unreal.load_asset(p)
        body = m.get_editor_property('body_setup')
        try:
            geom = body.get_editor_property('agg_geom')
        except Exception as e:
            return 'no agg_geom: ' + str(e)
        box = unreal.KBoxElem()
        box.set_editor_property('center', unreal.Vector(0, 0, float(height) / 2))
        box.set_editor_property('x', float(half) * 2)
        box.set_editor_property('y', float(half) * 2)
        box.set_editor_property('z', float(height))
        geom.set_editor_property('box_elems', [box])
        geom.set_editor_property('sphyl_elems', [])
        geom.set_editor_property('convex_elems', [])
        geom.set_editor_property('sphere_elems', [])
        body.set_editor_property('agg_geom', geom)
        body.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
        m.set_editor_property('body_setup', body)
        m.post_edit_change() if hasattr(m, 'post_edit_change') else None
        unreal.EditorAssetLibrary.save_loaded_asset(m, False)
        b = m.get_editor_property('body_setup').get_editor_property('agg_geom').get_editor_property('box_elems')
        return [[e.get_editor_property('x'), e.get_editor_property('y'), e.get_editor_property('z'), str(e.get_editor_property('center'))] for e in b]
    if action == 'leafcollision':
        # "mesh path|mesh path|...[|apply]": collision of foliage meshes (simple shapes, trace flag); with a last
        # "apply", leaves get no collision at all (simple removed, simple-as-complex) so canopies never block aim
        parts = arg.split('|')
        apply = parts[-1] == 'apply'
        out = {}
        for p in [x for x in parts if x != 'apply']:
            m = unreal.load_asset(p)
            sl = unreal.EditorStaticMeshLibrary
            row = {'simple': sl.get_simple_collision_count(m), 'convex': sl.get_convex_collision_count(m),
                   'flag': str(m.get_editor_property('body_setup').get_editor_property('collision_trace_flag'))}
            if apply:
                sl.remove_collisions(m)
                body = m.get_editor_property('body_setup')
                body.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
                m.set_editor_property('body_setup', body)
                unreal.EditorAssetLibrary.save_loaded_asset(m, False)
                row['after'] = [sl.get_simple_collision_count(m), sl.get_convex_collision_count(m), str(m.get_editor_property('body_setup').get_editor_property('collision_trace_flag'))]
            out[p.split('/')[-1]] = row
        return out
    if action == 'saveassets':
        # "path|path": save loaded assets (edits made while PIE runs can stay only in memory)
        out = {}
        for p in arg.split('|'):
            a = unreal.load_asset(p)
            if a:
                a.modify()
            out[p] = bool(a) and unreal.EditorAssetLibrary.save_loaded_asset(a, False)
        return out
    if action == 'faceactors':
        # Editor level: "mesh|tx,ty|front_offset" turns every actor of that static mesh to face the point (tx, ty);
        # without the target it only reports location and yaw. Saves the level when it turns something.
        import math as _m
        parts = arg.split('|')
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        out = []
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
            m = a.static_mesh_component.static_mesh
            if not m or m.get_name() != parts[0]:
                continue
            l = a.get_actor_location()
            row = [a.get_actor_label(), round(l.x), round(l.y), round(l.z), round(a.get_actor_rotation().yaw, 1)]
            if len(parts) > 2 and abs(l.z) < 300:
                tx, ty = (float(v) for v in parts[1].split(','))
                yaw = _m.degrees(_m.atan2(ty - l.y, tx - l.x)) + float(parts[2])
                a.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), False)
                row.append(round(yaw, 1))
            out.append(row)
        if len(parts) > 2:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return out
    if action == 'woodfloor':
        import importlib, mare_materials
        importlib.reload(mare_materials)
        return {p: mare_materials.wood_floor(p) for p in arg.split('|')}
    if action == 'lightshadows':
        # Editor level: interior and practical point lights cast shadows (with a short contact shadow); saves the level
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        n = 0
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PointLight):
            c = a.point_light_component
            if not c.get_editor_property('cast_shadows'):
                c.set_editor_property('cast_shadows', True)
                c.set_editor_property('contact_shadow_length', .08)
                n += 1
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return n
    if action == 'movereef':
        import importlib, mare_water
        importlib.reload(mare_water)
        return mare_water.move_reef(float(arg.split(',')[0]) if arg else -8500.0, arg.endswith('dry'))
    if action == 'seabed':
        import importlib, mare_water
        importlib.reload(mare_water)
        return mare_water.ensure_seabed()
    if action == 'seawater':
        import importlib, mare_materials
        importlib.reload(mare_materials)
        return mare_materials.build_water().get_path_name()
    if action == 'underwaterfog':
        import importlib, mare_materials
        importlib.reload(mare_materials)
        return mare_materials.build_underwater_fog()
    if action == 'grasstone':
        # "path|path": deeper textured green on grass materials (mare_materials.grass_tone)
        import importlib, mare_materials
        importlib.reload(mare_materials)
        return {p: mare_materials.grass_tone(p) for p in arg.split('|')}
    if action == 'grasshue':
        # "path|path": natural green recolour of imported grass materials (mare_materials.grass_hue)
        import importlib, mare_materials
        importlib.reload(mare_materials)
        return {p: mare_materials.grass_hue(p) for p in arg.split('|')}
    if action == 'plaster':
        # "path|path": fine plaster finish on facade materials (mare_materials.plaster_finish)
        import importlib, mare_materials
        importlib.reload(mare_materials)
        return {p: mare_materials.plaster_finish(p) for p in arg.split('|')}
    if action == 'matparams':
        # materials of a World_/Graphics mesh name found in PIE or by asset path: class, parent, vector/scalar/texture params
        out = {}
        for path in arg.split('|'):
            m = unreal.load_asset(path)
            if not m:
                out[path] = None
                continue
            row = {'class': m.get_class().get_name()}
            if isinstance(m, unreal.MaterialInstanceConstant):
                row['parent'] = m.get_editor_property('parent').get_path_name()
                row['vectors'] = {str(v.parameter_info.name): [round(v.parameter_value.r, 3), round(v.parameter_value.g, 3), round(v.parameter_value.b, 3)] for v in m.get_editor_property('vector_parameter_values')}
                row['scalars'] = {str(v.parameter_info.name): v.parameter_value for v in m.get_editor_property('scalar_parameter_values')}
                row['textures'] = {str(v.parameter_info.name): v.parameter_value.get_path_name() if v.parameter_value else None for v in m.get_editor_property('texture_parameter_values')}
            if isinstance(m, unreal.Material):
                node = unreal.MaterialEditingLibrary.get_material_property_input_node(m, unreal.MaterialProperty.MP_BASE_COLOR)
                row['base'] = node.get_class().get_name() if node else None
                for prop in ('constant', 'default_value', 'texture'):
                    try:
                        v = node.get_editor_property(prop)
                        row['base_' + prop] = [round(v.r, 3), round(v.g, 3), round(v.b, 3)] if hasattr(v, 'r') else (v.get_path_name() if v else None)
                    except Exception:
                        pass
                row['used_by'] = len(unreal.EditorAssetLibrary.find_package_referencers_for_asset(path.split('.')[0], False))
            out[path] = row
        return out
    if action == 'meshmat':
        # "Target|Source[|slot]": World_ mesh Target takes Source's slot-0 material in that slot (saved asset)
        import json as _json
        parts = arg.split('|')
        mapping = _json.loads((Path(unreal.Paths.project_content_dir()) / 'Data' / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
        target, source = unreal.load_asset(mapping[parts[0]]), unreal.load_asset(mapping[parts[1]])
        mat = source.get_material(0)
        target.set_material(int(parts[2]) if len(parts) > 2 else 0, mat)
        unreal.EditorAssetLibrary.save_loaded_asset(target, False)
        return [target.get_path_name(), mat.get_path_name()]
    if action == 'meshbounds':
        # size of a static mesh asset (cm): origin and extent of its bounds
        b = unreal.load_asset(arg).get_bounds()
        return [[round(v, 1) for v in (b.origin.x, b.origin.y, b.origin.z)], [round(v, 1) for v in (b.box_extent.x, b.box_extent.y, b.box_extent.z)]]
    if action == 'whereis':
        # PIE: location of the static-mesh actors using a mesh (QA of moving props: passing boats)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        out = []
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
            m = a.static_mesh_component.static_mesh
            if m and m.get_name() in arg.split(','):
                p = a.get_actor_location()
                out.append([m.get_name(), round(p.x), round(p.y), round(p.z), a.is_hidden_ed() if False else a.get_editor_property('hidden')])
        return out
    if action == 'mpc':
        # PIE: current MPC_MareTime values, the mare.Weather CVar and the rain curtain actors
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        mpc = unreal.load_asset('/Game/World/Materials/MPC_MareTime')
        out = {n: unreal.MaterialLibrary.get_scalar_parameter_value(world, mpc, n) for n in ('Night', 'Rain', 'Wind', 'Storm')}
        out['cvar'] = unreal.SystemLibrary.get_console_variable_int_value('mare.Weather')
        out['time'] = unreal.GameplayStatics.get_time_seconds(world)
        out['paused'] = unreal.GameplayStatics.is_game_paused(world)
        out['curtains'] = [[a.get_actor_label(), str(a.get_actor_location()), a.is_hidden_ed(), a.is_temporarily_hidden_in_editor()] for a in unreal.GameplayStatics.get_all_actors_with_tag(world, 'MareRain')]
        out['hidden_game'] = [a.get_editor_property('hidden') for a in unreal.GameplayStatics.get_all_actors_with_tag(world, 'MareRain')]
        return out
    if action == 'cmd':
        # PIE console command(s), separated by ';' (QA: mare.PoolAutoPlay 1; mare.PoolQA).
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        for c in arg.split(';'):
            unreal.SystemLibrary.execute_console_command(world, c.strip())
        return 'ok'
    if action == 'staff':
        return staff_qa(arg)
    if action == 'radio':
        # PIE: tune the radio ("radio_havaiana") and report the loop levels a moment later
        import time as _t
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        audio = next(o for o in unreal.ObjectIterator(unreal.MareAudioWorld) if o.get_outer() == world)
        audio.set_radio_station(arg)
        return 'tuned ' + arg
    if action == 'loops':
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        audio = next(o for o in unreal.ObjectIterator(unreal.MareAudioWorld) if o.get_outer() == world)
        return {n: round(audio.loop_level(n), 3) for n in arg.split(',')}
    if action == 'station':
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        pc.close_phone() if arg == 'close' else pc.open_station(arg)
        return 'station ' + arg
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
        return import_game_room_extras(arg.split(',') if arg else None)
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
    if action == 'beachball':
        # tools/ue58/gen_beach_ball.py (smooth, same 1 m frame and centre pivot) replaces World_0137 (392 triangles);
        # each ball then rests on what is below it (traced ignoring the ball itself), level and world.json alike.
        import json
        from mare_world_builder import transform
        out = import_models('Props', '/Game/Custom/Props') if arg != 'swap' else {}
        new_path = '/Game/Custom/Props/beach_ball_hd/beach_ball_hd.beach_ball_hd'
        mesh = unreal.load_asset(new_path)
        data = Path(unreal.Paths.project_content_dir()) / 'Data'
        world = json.loads((data / 'world.json').read_text(encoding='utf-8-sig'))
        mapping = json.loads((data / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
        mapping['World_0137'] = new_path
        ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        moved = []
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            if a.get_actor_label() != 'Maré · beach_ball':
                continue
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                c.set_static_mesh(mesh)
                for i in range(c.get_instance_count()):
                    t = c.get_instance_transform(i, True)
                    old = unreal.Vector(t.translation.x, t.translation.y, t.translation.z)
                    hit = unreal.SystemLibrary.line_trace_single(ed, old + unreal.Vector(0, 0, 150), old - unreal.Vector(0, 0, 300),
                                                                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a],
                                                                unreal.DrawDebugTrace.NONE, True)
                    if not hit:
                        moved.append({'at': [round(old.x), round(old.y)], 'error': 'no floor'})
                        continue
                    floor = hit.to_tuple()[5].z
                    radius = (mesh.get_bounds().box_extent.z) * t.scale3d.z
                    t.translation = unreal.Vector(old.x, old.y, floor + radius - .3)    # vinyl flattens a little
                    c.update_instance_transform(i, t, True, True, True)
                    for row in world['instances']:
                        rt = transform(row['transform']) if row['name'] == 'beach_ball' else None
                        if rt is not None and (rt.translation - old).length() < 1.0:
                            row['transform']['position'][1] += (t.translation.z - old.z) / 100
                    moved.append({'at': [round(old.x), round(old.y)], 'floor': round(floor, 1),
                                  'on': hit.to_tuple()[9].get_actor_label() if hit.to_tuple()[9] else '',
                                  'diameter': round(radius * 2), 'z': round(t.translation.z, 1)})
        (data / 'world.json').write_text(json.dumps(world, ensure_ascii=False, indent='\t'), encoding='utf-8')
        (data / 'imported_meshes.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return {'imported': out, 'moved': moved}
    if action == 'beachprops':
        # Real models for the code-made beach primitives (float_audit swapfit places them): the wet-sand footprint
        # (tools/ue58/gen_footprints.py) and Poly Haven rocks (CC0, fetch_polyhaven.py) for the Quaternius pebbles.
        import mare_hotel_lobby, mare_custom
        out = import_models('Beach', '/Game/Custom/Beach')
        for slug in ('rock_07', 'rock_09'):
            dest = f'/Game/Custom/Beach/{slug}'
            if unreal.EditorAssetLibrary.does_directory_exist(dest):
                unreal.EditorAssetLibrary.delete_directory(dest)
            out[slug] = mare_hotel_lobby._import(Path(f'D:/Assets/PolyHaven/{slug}/{slug}_2k.gltf'), dest, slug, True, search=False).get_path_name()
        out['_footprint'] = footprint_material()
        out['_usage'] = mare_custom.fix_usage()['fixed']
        return out
    if action == 'importmare':
        # "slug|/Game/Custom/<Folder>": a bpy model from D:/Assets/Mare/<slug>/<slug>.glb (gen_beach_walkway.py,
        # gen_tree_planter.py...) into its own fresh folder; float_audit swapfit ...:same puts it in the level.
        import mare_hotel_lobby, mare_custom
        slug, folder = (arg.split('|') + ['/Game/Custom/Beach'])[:2]
        dest = f'{folder}/{slug}'
        if unreal.EditorAssetLibrary.does_directory_exist(dest):
            unreal.EditorAssetLibrary.delete_directory(dest)
        mesh = mare_hotel_lobby._import(Path(f'D:/Assets/Mare/{slug}/{slug}.glb'), dest, slug, True, search=False)
        return {'mesh': mesh.get_path_name(), 'tris': mesh.get_num_triangles(0), '_usage': mare_custom.fix_usage()['fixed']}
    if action == 'sand':
        import importlib, mare_materials
        importlib.reload(mare_materials)
        return [mare_materials.build_ground().get_path_name(), mare_materials.build_sand_footprint().get_path_name()]
    if action == 'weather':
        import importlib, mare_materials
        importlib.reload(mare_materials)
        return mare_materials.build_weather()
    if action == 'puddles':
        return place_puddles(int(arg or 70))
    if action == 'pousadafloor':
        return pousada_floor()
    if action == 'footprintmat':
        if arg == 'reimport':
            # new PNGs from gen_footprints.py over the same texture assets (the level keeps its references)
            for name in ('beach_footprint_color', 'beach_footprint_normal'):
                task = unreal.AssetImportTask()
                task.filename = str(MODELS / 'Beach' / f'{name}.png')
                task.destination_path = '/Game/Custom/Beach/beach_footprint'
                task.destination_name = name
                task.automated = task.replace_existing = task.save = True
                unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        return footprint_material()
    if action == 'freecam':
        # "label,x,y,z[;...]": a camera spec "label,cx,cy,cz,pitch,yaw" per target that sees it without a wall in
        # between: 16 directions at three elevations, the clearest line of sight (trace from the target outwards),
        # 70-220 cm away. Avoids captures from inside walls, roofs and furniture.
        import math
        world_ = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() or             unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        specs = []
        for item in arg.split(';'):
            label, x, y, z = item.split(',')
            t = unreal.Vector(float(x), float(y), float(z))
            best = None
            for k in range(16):
                a = k * math.pi / 8
                for el in (.35, .6, .15):
                    d = unreal.Vector(math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el))
                    start = t + d * 15
                    end = t + d * 240
                    hit = unreal.SystemLibrary.line_trace_single(world_, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
                                                                unreal.DrawDebugTrace.NONE, True)
                    free = (hit.to_tuple()[5] - t).length() - 25 if hit else 220
                    score = min(free, 220) - abs(el - .35) * 30
                    if free >= 70 and (best is None or score > best[0]):
                        best = (score, d, min(free, 220))
            if not best:
                specs.append(f'{label},none')
                continue
            _, d, dist = best
            c = t + d * dist
            yaw = math.degrees(math.atan2(-d.y, -d.x))
            pitch = -math.degrees(math.asin(d.z))
            specs.append(f'{label},{c.x:.0f},{c.y:.0f},{c.z:.0f},{pitch:.0f},{yaw:.0f}')
        return specs
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
