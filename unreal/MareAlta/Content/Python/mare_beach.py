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
    parts = [float(v) for v in arg.split(',')]
    look, style = int(parts[0]), int(parts[1])
    dist = parts[2] if len(parts) > 2 else 260.0
    pitch = parts[3] if len(parts) > 3 else -6.0
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    people = [p for p in unreal.ObjectIterator(unreal.MarePerson) if p.get_world() == world]
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    people.sort(key=lambda p: (p.get_actor_location() - hero.get_actor_location()).length())
    p = people[0]
    p.set_appearance(look)
    p.set_outfit_style(style)
    loc, fwd = p.get_actor_location(), p.get_actor_forward_vector()
    hero.get_component_by_class(unreal.CharacterMovementComponent).set_movement_mode(unreal.MovementMode.MOVE_FLYING)
    hero.set_actor_location(unreal.Vector(loc.x + fwd.x * dist, loc.y + fwd.y * dist, loc.z + 40), False, True)
    import math
    unreal.GameplayStatics.get_player_controller(world, 0).set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=math.degrees(math.atan2(-fwd.y, -fwd.x))))
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
POOL_SHELL = ('World_0083', 'World_0084', 'World_0085', 'World_2398', 'World_2399', 'World_2400')   # floors and inner walls


def pool_water():
    import mare_materials
    importlib.reload(mare_materials)
    mat = mare_materials.build_pool_water()
    tiles = mare_materials.build_pool_tiles()
    changed = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if c.static_mesh and c.static_mesh.get_name() in POOL_WATER:
                c.set_material(0, mat)
                c.set_editor_property('disallow_nanite', True)
                c.set_editor_property('cast_shadow', False)
                changed.append([a.get_actor_label(), c.static_mesh.get_name(), c.get_instance_count()])
            if c.static_mesh and c.static_mesh.get_name() in POOL_SHELL:
                for slot in range(c.get_num_materials()):
                    c.set_material(slot, tiles)
                changed.append([a.get_actor_label(), c.static_mesh.get_name(), 'tiles'])
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


def swap_mesh(arg):
    """'World_2020:mare_lighthouse,...': every instanced component of an exported mesh gets the custom
    model (Data/custom_assets.json) in its place, keeping the instance transforms; overrides cleared."""
    import json
    from pathlib import Path
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    assets = json.loads((Path(unreal.Paths.project_dir()) / 'Content/Data/custom_assets.json').read_text(encoding='utf-8'))
    pairs = dict(p.split(':') for p in arg.split(','))
    changed = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        # Instanced pieces and plain mesh components (business booths are separate actors).
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            name = c.static_mesh.get_name() if c.static_mesh else ''
            if name in pairs and pairs[name] == 'none':
                # Superseded prop (e.g. the flat souvenir display in front of the new stall).
                c.set_visibility(False)
                c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                changed.append([a.get_actor_label(), name, 'hidden'])
                continue
            if name in pairs:
                mesh = unreal.load_asset(assets[pairs[name]])
                c.set_static_mesh(mesh)
                c.set_editor_property('override_materials', [])
                changed.append([a.get_actor_label(), name, pairs[name]])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return changed


# Pousada bungalows in the palm grove west of the reception, doors (model +Y) turned to the sea (-Y).
# The first comes with the pousada, the other two with the pool (definitions: pool "rooms": 2).
BUNGALOWS = [(-1600, 1620, 'Region_pousada'), (-2380, 1620, 'Region_pool'), (-3160, 1620, 'Region_pool')]


def place_bungalows():
    import json
    from pathlib import Path
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    assets = json.loads((Path(unreal.Paths.project_dir()) / 'Content/Data/custom_assets.json').read_text(encoding='utf-8'))
    mesh = unreal.load_asset(assets['mare_bungalow'])
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for a in actors.get_all_level_actors():
        if 'MareBungalow' in [str(t) for t in a.tags]:
            actors.destroy_actor(a)
    report = []
    for i, (x, y, region) in enumerate(BUNGALOWS):
        # Ground under the room centre (the stone plinth reaches 0.5 m below for uneven lawn).
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 3000), unreal.Vector(x, y, -2000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        z = hit.to_tuple()[4].z if hit else 0.0
        actor = actors.spawn_actor_from_object(mesh, unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=0, yaw=180))
        actor.set_actor_label(f'Bangalô {i + 1}')
        actor.tags = [unreal.Name('MareBungalow'), unreal.Name(region)]
        comp = actor.static_mesh_component
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        report.append([x, y, round(z), region])
    # Palms and trees that would grow through a room or its deck: shrink those instances to epsilon.
    removed = 0
    for a in actors.get_all_level_actors():
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            name = c.static_mesh.get_name().lower() if c.static_mesh else ''
            if not any(k in name for k in ('palm', 'coconut', 'tree', 'shrub', 'bush')):
                continue
            for i in range(c.get_instance_count()):
                tr = c.get_instance_transform(i, True)
                p = tr.translation
                if any(abs(p.x - bx) < 400 and (by - 520) < p.y < (by + 280) for bx, by, _ in BUNGALOWS):
                    tr.scale3d = unreal.Vector(.001, .001, .001)
                    c.update_instance_transform(i, tr, True, True, True)
                    removed += 1
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'bungalows': report, 'vegetation_removed': removed}


# Grand Hotel suite on the 3rd floor (tools/ue58/gen_suite.py); furniture in suite metres, facing in world axes.
SUITE_ORIGIN = (-2800.0, 6342.0, 851.0)
SUITE_FURNITURE = [
    ('sofa_03', -0.5, 1.6, (0, -1)), ('modern_coffee_table_01', -0.5, .45, (0, -1)),
    ('ArmChair_01', -2.6, -4.4, (1, .4)), ('mid_century_lounge_chair', 1.6, -4.4, (-1, .4)),
    ('modern_coffee_table_02', -.5, -4.5, (0, 1)), ('ClassicNightstand_01', -7.85, -1.65, (1, 0)),
    ('ClassicNightstand_01', -7.85, .55, (1, 0)), ('pachira_aquatica_01', -8.0, -5.1, (1, 0)),
    ('pachira_aquatica_01', 2.6, -5.1, (-1, 0)), ('potted_plant_01', -5.6, 5.2, (0, -1)),
    ('calathea_orbifolia_01', 1.6, 5.2, (0, -1)), ('potted_plant_02', -2.6, -1.6, (0, 1)),
]
SUITE_LIGHTS = [(-6.0, -.5), (-.5, .6), (-.5, -3.6), (5.7, 2.8), (-4.0, 4.3), (2.0, 3.8)]


def place_suite():
    import json, math, importlib
    from pathlib import Path
    import mare_hotel_lobby, mare_materials
    importlib.reload(mare_hotel_lobby)
    importlib.reload(mare_materials)
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    assets = json.loads((Path(unreal.Paths.project_dir()) / 'Content/Data/custom_assets.json').read_text(encoding='utf-8'))
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if 'MareSuitePart' in [str(t) for t in a.tags]:
            actors.destroy_actor(a)
    ox, oy, oz = SUITE_ORIGIN
    tags = [unreal.Name('MareGenerated'), unreal.Name('Region_grand_hotel'), unreal.Name('MareSuitePart')]
    room = actors.spawn_actor_from_object(unreal.load_asset(assets['mare_suite']), unreal.Vector(ox, oy, oz), unreal.Rotator(roll=0, pitch=0, yaw=0))
    room.set_actor_label('Hotel · suíte')
    room.tags = tags + [unreal.Name('MareSuite')]
    room.set_folder_path('Hotel/Suite')
    comp = room.static_mesh_component
    daylight = mare_materials.build_suite_daylight()
    for i, slot in enumerate(comp.static_mesh.static_materials):
        if slot.material_interface and 'DaylightPanel' in slot.material_interface.get_name():
            comp.set_material(i, daylight)
    placed = []
    for slug, x, y, face in SUITE_FURNITURE:
        mesh = mare_hotel_lobby._lib_mesh(slug)
        b = mesh.get_bounds()
        z = oz + 3 - (b.origin.z - b.box_extent.z)
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(ox + x * 100, oy + y * 100, z), unreal.Rotator(roll=0, pitch=0, yaw=math.degrees(math.atan2(face[1], face[0]))))
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.set_actor_label('Hotel suíte · ' + slug)
        actor.tags = tags
        actor.set_folder_path('Hotel/Suite')
        placed.append(slug)
    rug = actors.spawn_actor_from_object(unreal.load_asset(assets['mare_rug']), unreal.Vector(ox - 50, oy + 80, oz + 3), unreal.Rotator(roll=0, pitch=0, yaw=0))
    rug.tags = tags
    rug.set_folder_path('Hotel/Suite')
    for x, y in SUITE_LIGHTS:
        light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(ox + x * 100, oy + y * 100, oz + 270))
        c = light.point_light_component
        c.set_intensity(1800.0)
        c.set_light_color(unreal.LinearColor(1.0, .86, .70, 1.0))
        c.set_attenuation_radius(750.0)
        c.set_editor_property('cast_shadows', False)
        light.tags = tags
        light.set_folder_path('Hotel/Suite')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'suite': True, 'furniture': placed, 'lights': len(SUITE_LIGHTS)}


def interiors():
    """Bounded post-process volumes for every interior (lobby, suite, bungalows) plus bungalow lamps.
    UMareVisualWorld drives their exposure (tag MareInterior) and the lamps (MarePractical/MareHomeLight)."""
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if 'MareInteriorPart' in [str(t) for t in a.tags]:
            actors.destroy_actor(a)
    ox, oy, oz = SUITE_ORIGIN
    boxes = [('lobby', (-2100, 6342, 255), (1630, 577, 210), 'Region_grand_hotel'),
             ('suite', (ox, oy, oz + 154), (850, 577, 154), 'Region_grand_hotel')]
    boxes += [(f'bangalo{i + 1}', (x, y + 8, 200), (240, 207, 150), region) for i, (x, y, region) in enumerate(BUNGALOWS)]
    for name, centre, extent, region in boxes:
        vol = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(*centre))
        vol.set_actor_scale3d(unreal.Vector(extent[0] / 100, extent[1] / 100, extent[2] / 100))
        vol.set_editor_property('unbound', False)
        vol.set_editor_property('priority', 5.0)
        vol.set_editor_property('blend_radius', 60.0)
        vol.set_actor_label('Interior · ' + name)
        vol.tags = [unreal.Name('MareInterior'), unreal.Name('MareInteriorPart')]
        vol.set_folder_path('Interiors')
    lamps = 0
    for i, (x, y, region) in enumerate(BUNGALOWS):
        # Bungalow yaw 180: local (lx, ly) -> world (x - lx, y - ly). Ceiling light and the two bedside lamps.
        for lx, ly, lz, power in [(0, 0, 290, 1.0), (135, -178, 110, .35), (-135, -178, 110, .35)]:
            light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x - lx, y - ly, lz))
            c = light.point_light_component
            c.set_intensity(1000.0 * power)
            c.set_light_color(unreal.LinearColor(1.0, .82, .62, 1.0))
            c.set_attenuation_radius(520.0)
            c.set_editor_property('cast_shadows', False)
            light.tags = [unreal.Name('MarePractical'), unreal.Name('MareHomeLight'), unreal.Name(region), unreal.Name('MareInteriorPart')]
            light.set_folder_path('Interiors')
            lamps += 1
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'volumes': len(boxes), 'lamps': lamps}


def run(action, arg=''):
    if action == 'interiors':
        return interiors()
    if action == 'suite':
        return place_suite()
    if action == 'bungalows':
        return place_bungalows()
    if action == 'swapmesh':
        return swap_mesh(arg)
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
