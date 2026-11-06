"""Grand Hotel game room decoration (CHECKLIST 5.4 "Decoração: piso, parede com papel ou ripado, iluminação, quadros e
balcão de fichas"). The room is the middle of the hotel's ground-floor hall (x -2500..-1700, north wall face y 6890,
floor 45, ceiling 462). Models: tools/ue58/gen_game_room_decor.py (bpy) and Poly Haven CC0 (dartboard, wall clock,
picture frame, cash register, chalkboard), all imported to /Game/Custom/GameRoom/<slug> (always cooked).
The billiard lamp is a lighting.json fixture (unlock salao_jogos) so it lights at night like every lamp.
Re-runnable: place() removes every actor tagged MareGameRoomDecor first. Every piece carries Region_salao_jogos (hidden
until the game room is bought) and never touches the static navigation (can_ever_affect_navigation off).
  mare_game_room.cmd('import')        -> imports the models that are not in /Game/Custom/GameRoom yet ('import:force' all,
                                         'import:slug,slug' just those)
  mare_game_room.cmd('glass')         -> clear glass on the picture frame
  mare_game_room.cmd('sizes')         -> bounds of every model (cm)
  mare_game_room.cmd('place')         -> spawns the set (PIE stopped) and saves the level
"""
import json
import math
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
DATA = ROOT / 'Content/Data'
TAG = 'MareGameRoomDecor'
DEST = '/Game/Custom/GameRoom/'
MARE = Path('D:/Assets/Mare')
POLY = Path('D:/Assets/PolyHaven')
OWN = ['mare_gameroom_wall', 'mare_gameroom_sign', 'mare_gameroom_sign_fichas', 'mare_billiard_lamp', 'mare_token_counter',
       'mare_cue_rack', 'mare_gameroom_rug']
# Playable foosball (tools/ue58/gen_foosball.py): spawned and moved by UMareFoosball, not placed in the level.
FOOSBALL = ['mare_foosball_body', 'mare_foosball_ball'] + [f'mare_foosball_rod_{n}_{t}' for n in (1, 2, 3, 5) for t in ('coral', 'mar')]
OWN += FOOSBALL
POLYHAVEN = ['dartboard', 'wall_clock', 'hanging_picture_frame_02', 'standing_chalkboard_01']
SOLID = {'mare_token_counter', 'mare_cue_rack', 'standing_chalkboard_01'}   # the player bumps into these
FLOOR, WALL = 45.0, 6890.0

# (slug, x, y, z of the base, yaw). bpy models face UE -Y at yaw 0 (back at their origin); see gen_game_room_decor.py.
# Poly Haven wall pieces face UE +Y (back at y 0): yaw 180. Wall face y 6890; the accent wall's plaster is 10 cm thick
# (front 6880, in front of the lobby chair rail at 6882) and its slats stand 14.2 cm off the wall (front 6875.8).
# The arcades stand at x -2100 / -1950, y 6780.
DECOR = [
    ('mare_gameroom_wall', -2100, WALL, FLOOR, 0),             # x -2490..-1710: from the elevator frame to the reception slats
    ('mare_gameroom_sign', -2100, WALL - 10, FLOOR + 305, 0),  # "SALÃO DE JOGOS" above the arcades
    ('mare_token_counter', -2400, 6810, FLOOR, 0),             # where the lobby armchair stood (static navigation hole)
    # CashRegister_01 (Poly Haven) is a 60 x 62 cm vintage till, deeper than the 61 cm counter top: left out.
    ('mare_gameroom_sign_fichas', -2400, WALL - 14.5, FLOOR + 180, 0),
    ('hanging_picture_frame_02', -2240, WALL - 10, FLOOR + 185, 180),
    ('dartboard', -1790, WALL - 14.5, FLOOR + 173, 180),       # centre 1.73 m: the regulation height
    ('wall_clock', -1790, WALL - 14.5, FLOOR + 300, 180),
    ('mare_gameroom_rug', -2050, 6050, FLOOR, 0),              # under the pool table (game_room.json table)
    ('mare_cue_rack', -2470, 6050, FLOOR, 90),                 # facing the table, 3 m from its west end
    ('standing_chalkboard_01', -2440, 6215, FLOOR, 90),
]


def _game_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()


def _source(slug):
    for lib in (MARE, POLY):
        info = lib / slug / 'info.json'
        if info.exists():
            return lib / slug / json.loads(info.read_text(encoding='utf-8'))['gltf']
    raise FileNotFoundError(slug)


def _mesh(slug):
    for p in unreal.EditorAssetLibrary.list_assets(DEST + slug, recursive=True) if unreal.EditorAssetLibrary.does_directory_exist(DEST + slug) else []:
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            return a
    return None


def _flags(folder):
    """Nanite + instanced usage on this folder's materials only (never the whole /Game/Custom: CLAUDE.md 06/11)."""
    fixed = []
    for path in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
        asset = unreal.load_asset(path)
        while isinstance(asset, unreal.MaterialInstance):
            parent = asset.get_editor_property('parent')
            if not parent or not parent.get_path_name().startswith(folder):
                asset = None
                break
            asset = parent
        if not isinstance(asset, unreal.Material):
            continue
        changed = False
        for flag in ('used_with_instanced_static_meshes', 'used_with_nanite'):
            if not asset.get_editor_property(flag):
                asset.set_editor_property(flag, True)
                changed = True
        if changed:
            unreal.MaterialEditingLibrary.recompile_material(asset)
            unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
            fixed.append(asset.get_name())
    return fixed


def import_models(force=False):
    import importlib
    import mare_hotel_lobby
    importlib.reload(mare_hotel_lobby)
    if _game_world():
        raise RuntimeError('Stop PIE first')
    path = DATA / 'custom_assets.json'
    assets = json.loads(path.read_text(encoding='utf-8'))
    report = {}
    for slug in OWN + POLYHAVEN:
        if isinstance(force, list) and slug not in force:
            continue
        if _mesh(slug) and not force:
            report[slug] = 'kept'
            continue
        folder = DEST + slug
        unreal.EditorAssetLibrary.delete_directory(folder)
        mesh = mare_hotel_lobby._import(_source(slug), folder, slug, True, slug not in OWN)
        editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        body = mesh.get_editor_property('body_setup')
        if slug in SOLID:
            body.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
            editor.remove_collisions_with_notification(mesh, False)
            editor.add_simple_collisions_with_notification(mesh, unreal.ScriptCollisionShapeType.BOX, False)
        # Glass slots (clock, frame, register) are translucent: a Nanite mesh drops them in the packaged game.
        if any('glass' in str(s.material_slot_name).lower() for s in mesh.static_materials):
            nanite = mesh.get_editor_property('nanite_settings')
            nanite.set_editor_property('enabled', False)
            mesh.set_editor_property('nanite_settings', nanite)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
        assets[slug] = mesh.get_path_name()
        b = mesh.get_bounding_box()
        report[slug] = {'tris': mesh.get_num_triangles(0), 'materials': len(mesh.static_materials), 'flags': _flags(folder),
                        'min': [round(b.min.x), round(b.min.y), round(b.min.z)], 'max': [round(b.max.x), round(b.max.y), round(b.max.z)]}
    path.write_text(json.dumps(assets, indent=1), encoding='utf-8')
    return report


def sizes():
    out = {}
    for slug in OWN + POLYHAVEN:
        m = _mesh(slug)
        if not m:
            out[slug] = None
            continue
        b = m.get_bounding_box()
        out[slug] = {'min': [round(b.min.x, 1), round(b.min.y, 1), round(b.min.z, 1)], 'max': [round(b.max.x, 1), round(b.max.y, 1), round(b.max.z, 1)],
                     'path': m.get_path_name(), 'slots': [str(s.material_slot_name) for s in m.static_materials]}
    return out


def _drop_lobby_spots(actors):
    """The token counter and the billiard lamp took two spots of the lobby layout (mare_hotel_lobby.LAYOUT, 06/11)."""
    gone = []
    for a in actors.get_all_level_actors():
        label = a.get_actor_label()
        p = a.get_actor_location()
        if ('modern_arm_chair_01' in label and abs(p.x + 2328) < 40 and abs(p.y - 6660) < 40) or \
           ('modern_ceiling_lamp_01' in label and abs(p.x + 2100) < 20 and abs(p.y - 6050) < 20):
            gone.append([label, round(p.x), round(p.y), round(p.z)])
            actors.destroy_actor(a)
    path = DATA / 'hotel_lobby.json'
    lobby = json.loads(path.read_text(encoding='utf-8'))
    keep = [e for e in lobby['placed'] if not ((e['slug'] == 'modern_arm_chair_01' and abs(e['location'][0] + 2328) < 40 and abs(e['location'][1] - 6660) < 40)
                                               or (e['slug'] == 'modern_ceiling_lamp_01' and abs(e['location'][0] + 2100) < 20 and abs(e['location'][1] - 6050) < 20))]
    if len(keep) != len(lobby['placed']):
        lobby['placed'] = keep
        path.write_text(json.dumps(lobby, indent=1), encoding='utf-8')
    return gone


def place():
    if _game_world():
        raise RuntimeError('Stop PIE first')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if TAG in [str(t) for t in a.tags]:
            actors.destroy_actor(a)
    gone = _drop_lobby_spots(actors)
    tags = [unreal.Name('MareGenerated'), unreal.Name('Region_salao_jogos'), unreal.Name(TAG)]
    placed = []
    for slug, x, y, z, yaw in DECOR:
        mesh = _mesh(slug)
        if not mesh:
            raise RuntimeError(f'{slug}: run import first')
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
        comp = actor.static_mesh_component
        comp.set_static_mesh(mesh)
        comp.set_editor_property('can_ever_affect_navigation', False)
        if slug not in SOLID:
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        actor.set_actor_label('Salão de jogos · ' + slug)
        actor.tags = tags
        actor.set_folder_path('Hotel/GameRoom')
        placed.append(slug)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'placed': placed, 'removed_from_lobby': gone}


def lobby_lamp():
    """Pivot and mesh of the lobby ceiling lamp over the pool table (for its lighting.json replacement)."""
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if 'modern_ceiling_lamp_01' in a.get_actor_label():
            p = a.get_actor_location()
            out.append([round(p.x, 1), round(p.y, 1), round(p.z, 2), a.static_mesh_component.static_mesh.get_path_name()])
    return out


def clear_glass():
    """The Poly Haven frame's glass came in from glTF nearly opaque and mirror-like: the painting behind it was a blurry
    grey-blue reflection (06/11 photo). Its glass slot gets M_GameRoomGlassClear (translucent, 6% opacity, glossy)."""
    path = DEST + 'M_GameRoomGlassClear'
    mel = unreal.MaterialEditingLibrary
    mat = unreal.load_asset(path)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_GameRoomGlassClear', DEST.rstrip('/'), unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE)
    mat.set_editor_property('used_with_nanite', True)
    for prop, value, y in ((unreal.MaterialProperty.MP_OPACITY, .06, 0), (unreal.MaterialProperty.MP_ROUGHNESS, .05, 100),
                           (unreal.MaterialProperty.MP_SPECULAR, .5, 200)):
        node = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, y)
        node.set_editor_property('r', value)
        mel.connect_material_property(node, '', prop)
    color = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 300)
    color.set_editor_property('constant', unreal.LinearColor(.9, .95, 1.0, 1))
    mel.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    done = []
    for slug in ('hanging_picture_frame_02',):
        mesh = _mesh(slug)
        for i, s in enumerate(mesh.static_materials):
            if 'glass' in str(s.material_slot_name).lower():
                mesh.set_material(i, mat)
                done.append([slug, i])
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return done


def check(arg=''):
    """QA gate (06/11 defects of the first decoration photos), editor level:
    - rail: the lobby chair rail (tower mesh, z 106-115, 8 cm off the wall) crossed the 5 cm accent wall; a trace at rail
      height every 40 cm along the wall (from 30 cm off it, behind the counter and arcades) must hit the accent wall
      before the tower;
    - plants: no lobby actor uses calathea_orbifolia_01 (a row of loose leaves with no pot, sprigs out of the floor);
    - glass: the picture frame glass is the clear one (the glTF glass hid the painting)."""
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    wall = [a for a in actors if a.get_actor_label() == 'Salão de jogos · mare_gameroom_wall']
    bad_rail = []
    if wall:
        # The decoration has no collision (only the counter, rack and chalkboard): query-only while tracing.
        comp = wall[0].static_mesh_component
        comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
        x0 = wall[0].get_actor_location().x
        for i in range(19):
            x = x0 - 360 + i * 40
            for z in (108.0, 111.0, 114.0):
                hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, WALL - 30, z), unreal.Vector(x, WALL + 60, z),
                                                             unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
                who = hit.to_tuple()[9] if hit else None
                if not who or who != wall[0]:
                    bad_rail.append([round(x), z, who.get_actor_label() if who else None])
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    plants = [a.get_actor_label() for a in actors if 'calathea_orbifolia_01' in a.get_actor_label()]
    frame = _mesh('hanging_picture_frame_02')
    glass = [str(s.material_interface.get_name()) for s in frame.static_materials if 'glass' in str(s.material_slot_name).lower()] if frame else ['missing']
    ok = bool(wall) and not bad_rail and not plants and glass == ['M_GameRoomGlassClear']
    return json.dumps({'wall': bool(wall), 'rail_hits': bad_rail[:8], 'plants': plants, 'glass': glass, 'pass': ok}, ensure_ascii=False)


def cmd(text):
    action, _, arg = text.partition(':')
    if action == 'import':
        return import_models(arg == 'force' or arg.split(',') if arg else False)
    if action == 'sizes':
        return sizes()
    if action == 'place':
        return place()
    if action == 'check':
        return check()
    if action == 'glass':
        return clear_glass()
    if action == 'lobbylamp':
        return lobby_lamp()
    raise ValueError(action)
