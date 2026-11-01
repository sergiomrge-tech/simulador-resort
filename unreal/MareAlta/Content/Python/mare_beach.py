"""Caribbean-style coast pass: pale coral sand, clear turquoise shallows, white foam.
Materials are authored in mare_materials; this module rebuilds them and frames comparison views."""
import importlib
import unreal

VIEWS = {
    'kiosk-sea': ((3800, -1650, 260), (-12, -90)),
    'shore-low': ((3000, -2700, 170), (-8, -70)),
    'beach-wide': ((5200, -900, 900), (-22, -125)),
    'shallows': ((3600, -3300, 420), (-35, -95)),
    'swell-low': ((3900, -2550, 60), (-3, -100)),
    'shoreline-side': ((2200, -2900, 140), (-10, -20)),
}


def rebuild():
    import mare_materials
    importlib.reload(mare_materials)
    ground = mare_materials.build_ground()
    water = mare_materials.build_water()
    return {'ground': ground.get_path_name(), 'water': water.get_path_name()}


def reimport_ocean():
    """Replace the ocean surface with the graded grid from tools/ue58/gen_ocean.py."""
    from pathlib import Path
    root = Path(unreal.Paths.project_dir()).resolve()
    meshes = [unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets('/Game/World/Ocean', recursive=True)]
    meshes = [m for m in meshes if isinstance(m, unreal.StaticMesh)]
    if len(meshes) != 1:
        raise RuntimeError('ocean mesh: ' + str(meshes))
    task = unreal.AssetImportTask()
    task.filename = str(root / 'SourceArt/Ocean/Ocean.gltf')
    task.destination_path = '/Game/World/Ocean'
    task.destination_name = meshes[0].get_name()
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(meshes[0].get_path_name())
    settings = mesh.get_editor_property('nanite_settings')
    settings.enabled = False
    unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).set_nanite_settings(mesh, settings, True)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return {'mesh': mesh.get_path_name(), 'triangles': mesh.get_num_triangles(0)}


def view(name):
    (x, y, z), (pitch, yaw) = VIEWS[name]
    return {'location': {'x': x, 'y': y, 'z': z}, 'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}


def pie_shot(arg):
    """QA PIE: place the player camera (x,y,z,pitch,yaw) and write a HighResShot to the QA folder."""
    if '-MareSaveRoot=D:/CodexTemp/' not in unreal.SystemLibrary.get_command_line():
        raise RuntimeError('QA profile required')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:
        raise RuntimeError('Start PIE first')
    name, x, y, z, pitch, yaw = arg.split(',')
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    if name.endswith('>'):
        # Swim-stroke QA: shove the swimmer forward so the stroke (not treading) pose is shown.
        move = hero.get_component_by_class(unreal.CharacterMovementComponent)
        move.set_editor_property('velocity', hero.get_actor_forward_vector() * 200)
        return {'pushed': move.is_swimming()}
    if name.endswith('^'):
        # Viewport shot (first-person body and HUD included) to Saved/Screenshots/WindowsEditor.
        move = hero.get_component_by_class(unreal.CharacterMovementComponent)
        unreal.SystemLibrary.execute_console_command(world, 'Shot showui')
        return {'shot': name[:-1], 'swimming': move.is_swimming(), 'z': hero.get_actor_location().z}
    if name.endswith('!'):
        unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1280x720 filename=D:/CodexTemp/beach/pie-' + name[:-1] + '.png')
        return {'shot': name[:-1]}
    move = hero.get_component_by_class(unreal.CharacterMovementComponent)
    move.set_movement_mode(unreal.MovementMode.MOVE_SWIMMING if name.startswith('swim') else unreal.MovementMode.MOVE_FLYING)
    hero.set_actor_location(unreal.Vector(float(x), float(y), float(z)), False, True)
    pc.set_control_rotation(unreal.Rotator(roll=0, pitch=float(pitch), yaw=float(yaw)))
    return {'placed': name}


def outfit_probe(arg):
    """QA PIE: 'look,style' -> dress the nearest ambient person and stand the camera in front of them."""
    look, style = [int(v) for v in arg.split(',')]
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    people = [p for p in unreal.ObjectIterator(unreal.MarePerson) if p.get_world() == world]
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    people.sort(key=lambda p: (p.get_actor_location() - hero.get_actor_location()).length())
    p = people[0]
    p.set_appearance(look)
    p.set_outfit_style(style)
    loc, fwd = p.get_actor_location(), p.get_actor_forward_vector()
    hero.get_component_by_class(unreal.CharacterMovementComponent).set_movement_mode(unreal.MovementMode.MOVE_FLYING)
    hero.set_actor_location(unreal.Vector(loc.x + fwd.x * 260, loc.y + fwd.y * 260, loc.z + 40), False, True)
    import math
    unreal.GameplayStatics.get_player_controller(world, 0).set_control_rotation(unreal.Rotator(roll=0, pitch=-6, yaw=math.degrees(math.atan2(-fwd.y, -fwd.x))))
    return {'person': p.get_editor_property('person_name'), 'look': look, 'style': style}


def radio_probe(station):
    """QA PIE: select a station and report the current loop levels of all stations."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:
        raise RuntimeError('Start PIE first')
    # World subsystems are reached through ObjectIterator filtered by outer in this engine build.
    audio = next(a for a in unreal.ObjectIterator(unreal.MareAudioWorld) if a.get_outer() == world)
    if station:
        audio.set_radio_station(station)
    names = ['reggae_praia', 'radio_reggae_roots', 'radio_calypso', 'radio_beach_pop', 'music_bossa', 'music_relax']
    return {'station': str(audio.get_radio_station()), 'sounds': audio.loaded_sounds(), 'levels': {n: round(audio.loop_level(n), 4) for n in names}}


POOL_WATER = ('World_0086', 'World_2401')   # pousada pool, Grand Hotel pool (flat water planes)


def pool_water():
    import mare_materials
    importlib.reload(mare_materials)
    mat = mare_materials.build_pool_water()
    changed = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if c.static_mesh and c.static_mesh.get_name() in POOL_WATER:
                c.set_material(0, mat)
                c.set_editor_property('disallow_nanite', True)
                c.set_editor_property('cast_shadow', False)
                changed.append([a.get_actor_label(), c.static_mesh.get_name(), c.get_instance_count()])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'material': mat.get_path_name(), 'components': changed}


def window_glass():
    """All building windows: the exported glass slot (MA_a357...) imported milky/opaque; use the
    neutral clear glass on every component that carries it (village, shops, hotel, kiosk)."""
    import mare_materials
    importlib.reload(mare_materials)
    glass = unreal.load_asset('/Game/World/Materials/M_ClearWindowGlass')
    pane = mare_materials.build_window_pane()
    facade = ('World_0688', 'World_0683')   # village 'janela' and 'batente' panes flush on walls
    changed = 0
    meshes = set()
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if not c.static_mesh:
                continue
            for j, slot in enumerate(c.static_mesh.static_materials):
                if slot.material_interface and 'a3573534a1ac' in slot.material_interface.get_name():
                    flush = c.static_mesh.get_name() in facade
                    c.set_material(j, pane if flush else glass)
                    if isinstance(c, unreal.InstancedStaticMeshComponent) and not flush:
                        c.set_editor_property('disallow_nanite', True)
                    changed += 1
                    meshes.add(c.static_mesh.get_name())
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'slots': changed, 'meshes': len(meshes)}


def clock(minutes):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    sim = unreal.GameplayStatics.get_player_controller(world, 0).get_simulation()
    sim.advance_minutes(-5000)
    sim.advance_minutes(float(minutes))
    return {'minutes': float(minutes)}


def run(action, arg=''):
    if action == 'clock':
        return clock(arg)
    if action == 'windows':
        return window_glass()
    if action == 'pool':
        return pool_water()
    if action == 'radio':
        return radio_probe(arg)
    if action == 'audio':
        import mare_audio
        importlib.reload(mare_audio)
        return mare_audio.build()
    if action == 'pie':
        return pie_shot(arg)
    if action == 'outfit':
        return outfit_probe(arg)
    if action == 'custom':
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        custom = next(c for c in unreal.ObjectIterator(unreal.MareCustomWorld) if c.get_outer() == world)
        place, tier = arg.split(',')
        custom.preview_place(place, int(tier))
        return {'preview': place, 'tier': int(tier)}
    if action == 'phone':
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        pc = unreal.GameplayStatics.get_player_controller(world, 0)
        pc.open_phone(int(arg))
        return {'phone': int(arg)}
    if action == 'rebuild':
        return rebuild()
    if action == 'ocean':
        return reimport_ocean()
    if action == 'view':
        return view(arg)
    if action == 'views':
        return list(VIEWS)
    raise ValueError(action)
