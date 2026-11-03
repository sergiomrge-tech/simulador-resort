"""Grand Hotel lobby: reimport the opened tower (collider + Nanite proxies), furnish it with
CC0 Poly Haven models and inspect it. Geometry comes from tools/ue58/hotel_lobby_shell.py."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
MODELS = ROOT / 'SourceArt/Models'
DATA = ROOT / 'Content/Data'
LIB = Path('D:/Assets/PolyHaven')
TOWER = '/Game/World/Models/World_2365/World_2365.World_2365'


def _pipeline(nanite, search=True):
    p = unreal.InterchangeGenericAssetsPipeline()
    p.mesh_pipeline.combine_static_meshes_behavior = unreal.InterchangeCombineStaticMeshesBehavior.ALL
    p.mesh_pipeline.build_nanite = nanite
    p.mesh_pipeline.fallback_collision_type = unreal.InterchangeMeshCollision.NONE
    p.common_meshes_properties.bake_meshes = True
    # Own models (bpy) must not pick up same-named textures elsewhere (a linen normal map became the colour).
    p.material_pipeline.search_location = unreal.InterchangeMaterialSearchLocation.ALL_ASSETS if search else unreal.InterchangeMaterialSearchLocation.LOCAL
    stack = unreal.InterchangePipelineStackOverride()
    stack.set_editor_property('override_pipelines', [unreal.SoftObjectPath(p.get_path_name())])
    return stack


def _import(source, destination, name, nanite, search=True):
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = destination
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    task.options = _pipeline(nanite, search)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes = [unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(destination, recursive=True)]
    meshes = [m for m in meshes if isinstance(m, unreal.StaticMesh)]
    if len(meshes) != 1:
        raise RuntimeError(f'{name}: expected one mesh, got {[m.get_name() for m in meshes]}')
    return meshes[0]


def _complex_collision(mesh):
    body = mesh.get_editor_property('body_setup')
    body.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    editor = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    # Recast exports convex hulls even with complex-as-simple; the lobby must stay walkable.
    if editor.get_simple_collision_count(mesh) + editor.get_convex_collision_count(mesh) > 0:
        editor.remove_collisions_with_notification(mesh, False)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)


def reimport():
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    tower = _import(MODELS / 'World_2365.gltf', '/Game/World/Models/World_2365', 'World_2365', True)
    _complex_collision(tower)
    for name in ('HotelTower_Opaque', 'HotelTower_Glass'):
        _import(MODELS / (name + '.gltf'), '/Game/Graphics/Architecture/' + name, name, name.endswith('Opaque'))
    import importlib, mare_nanite_architecture
    importlib.reload(mare_nanite_architecture)
    return {'tower_triangles': tower.get_num_triangles(0), 'proxies': mare_nanite_architecture.build()}


def tower_instances():
    """World transforms of the (hidden) tower collider instances in the open editor level."""
    rows = []
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if c.static_mesh and c.static_mesh.get_name() == 'World_2365':
                for i in range(c.get_instance_count()):
                    t = c.get_instance_transform(i, True)
                    rows.append({'actor': actor.get_actor_label(), 'tags': [str(x) for x in actor.tags],
                                 'location': [t.translation.x, t.translation.y, t.translation.z],
                                 'rotation': [t.rotation.rotator().roll, t.rotation.rotator().pitch, t.rotation.rotator().yaw],
                                 'scale': [t.scale3d.x, t.scale3d.y, t.scale3d.z], 'collision': str(c.get_collision_enabled())})
    return rows


TOWER_ORIGIN = unreal.Vector(-2100, 6300, 0)
FLOOR = 45.0      # top of the stone base inside the lobby (cm)
CEILING = 450.0   # underside of the wood ribs
PLANTS = {'pachira_aquatica_01', 'calathea_orbifolia_01', 'anthurium_botany_01', 'potted_plant_01', 'potted_plant_02', 'potted_plant_04'}
# (slug, x, y in the tower Blender frame [m], base: 'floor'|'ceiling'|height cm, facing [dx,dy] in that frame, scale)
LAYOUT = [
    ('sofa_03', -12.6, -2.5, 'floor', (1, 0), 1.0),
    ('modern_coffee_table_01', -10.9, -2.5, 'floor', (1, 0), 1.0),
    ('ArmChair_01', -9.2, -3.6, 'floor', (-1, 0.3), 1.0),
    ('ArmChair_01', -9.2, -1.4, 'floor', (-1, -0.3), 1.0),
    ('Sofa_01', 12.6, -2.5, 'floor', (-1, 0), 1.0),
    ('modern_coffee_table_02', 10.9, -2.5, 'floor', (-1, 0), 1.0),
    ('mid_century_lounge_chair', 9.2, -3.6, 'floor', (1, 0.3), 1.0),
    ('mid_century_lounge_chair', 9.2, -1.4, 'floor', (1, -0.3), 1.0),
    ('Ottoman_01', 11.0, -0.6, 'floor', (0, -1), 1.0),
    ('side_table_tall_01', -14.6, -2.5, 'floor', (1, 0), 1.0),
    ('modern_arm_chair_01', 2.2, 3.6, 'floor', (0, -1), 1.0),
    ('modern_arm_chair_01', 11.5, 3.8, 'floor', (0, -1), 1.0),
    ('pachira_aquatica_01', -14.7, -4.6, 'floor', (1, 0), 1.0),
    ('pachira_aquatica_01', 14.7, -4.6, 'floor', (-1, 0), 1.0),
    ('pachira_aquatica_01', -14.7, 5.2, 'floor', (1, 0), 1.0),
    ('pachira_aquatica_01', 14.7, 5.2, 'floor', (-1, 0), 1.0),
    ('pachira_aquatica_01', -2.4, -4.6, 95.0, (0, -1), 1.0),
    ('pachira_aquatica_01', 2.4, -4.6, 95.0, (0, -1), 1.0),
    ('calathea_orbifolia_01', -5.6, 5.4, 'floor', (0, -1), 1.0),
    ('calathea_orbifolia_01', 9.6, 5.4, 'floor', (0, -1), 1.0),
    ('potted_plant_01', -3.5, 1.2, 'floor', (0, -1), 1.0),
    ('potted_plant_01', 3.5, 1.2, 'floor', (0, -1), 1.0),
    ('potted_plant_02', 6.5, 5.3, 'floor', (0, -1), 1.0),
    ('anthurium_botany_01', -4.9, 1.7, 155.0, (0, -1), 1.0),
    ('ceramic_vase_01', -9.2, 1.6, 155.0, (0, -1), 1.0),
    ('standing_picture_frame_01', -7.6, 1.75, 155.0, (0, -1), 1.0),
    ('hanging_picture_frame_01', -15.45, -0.5, 170.0, (1, 0), 1.0),
    ('hanging_picture_frame_03', 15.45, 1.8, 170.0, (-1, 0), 1.0),
    ('ceramic_vase_03', -14.6, -2.5, 'on:side_table_tall_01', (1, 0), 1.0),
    ('fab:145', -6.5, -4.6, 'floor', (0, -1), 1.0),
    ('fab:145', 6.5, -4.6, 'floor', (0, -1), 1.0),
    ('fab:143', -11.6, 5.2, 'floor', (0, -1), 1.0),
    ('fab:144', 12.4, 5.0, 'floor', (0, -1), 1.0),
    ('fab:242', -12.6, -4.3, 'floor', (1, 0), 1.0),
    ('fab:242', 12.6, -4.3, 'floor', (-1, 0), 1.0),
    ('fab:84', -14.8, 1.2, 'floor', (1, 0), 1.0),
    ('fab:84', 14.8, -0.4, 'floor', (-1, 0), 1.0),
] + [('modern_ceiling_lamp_01', x, y, 'ceiling', (0, -1), 1.0) for x in (-12.5, -7.0, 0.0, 7.0, 12.5) for y in (-2.5, 2.5)]


def _to_world(x, y):
    # Blender (x, y) -> UE local (x, -y)*100 -> tower yaw 180 -> world.
    return unreal.Vector(TOWER_ORIGIN.x - x * 100, TOWER_ORIGIN.y + y * 100, 0)


def _lib_mesh(slug):
    dest = '/Game/Hotel/Lobby/' + slug
    meshes = [unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(dest, recursive=True)] if unreal.EditorAssetLibrary.does_directory_exist(dest) else []
    meshes = [m for m in meshes if isinstance(m, unreal.StaticMesh)]
    if meshes:
        return meshes[0]
    info = json.loads((LIB / slug / 'info.json').read_text(encoding='utf-8'))
    mesh = _import(LIB / slug / info['gltf'], dest, slug, slug not in PLANTS)
    body = mesh.get_editor_property('body_setup')
    if body:
        body.set_editor_property('collision_trace_flag', unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).add_simple_collisions_with_notification(mesh, unreal.ScriptCollisionShapeType.BOX, False)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    if slug == 'pachira_aquatica_01':
        # The whole-bounds box spanned the crown and blocked the aim across the lobby: trunk and pot only.
        import mare_hud
        mare_hud.run('trunkbox', mesh.get_path_name() + '|30|110')
    return mesh


def furnish(front_offset=0.0):
    """Spawn the lobby set as tagged actors so the hotel region hides them until purchase."""
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if 'MareHotelLobby' in [str(t) for t in a.tags]:
            actors.destroy_actor(a)
    placed, tops = [], {}
    import importlib, mare_fab
    importlib.reload(mare_fab)
    for slug, x, y, base, face, scale in LAYOUT:
        if slug.startswith('fab:'):
            import math
            w = _to_world(x, y)
            yaw = math.degrees(math.atan2(face[1], -face[0])) + front_offset
            actor, height = mare_fab.place(actors, slug, w.x, w.y, FLOOR if base == 'floor' else base, yaw, scale)
            actor.set_actor_label('Hotel lobby · ' + slug)
            actor.tags = [unreal.Name('MareGenerated'), unreal.Name('Region_grand_hotel'), unreal.Name('MareHotelLobby')]
            actor.set_folder_path('Hotel/Lobby')
            placed.append({'slug': slug, 'location': [w.x, w.y], 'yaw': yaw, 'height_cm': height})
            continue
        mesh = _lib_mesh(slug)
        b = mesh.get_bounds()
        lo_z = (b.origin.z - b.box_extent.z) * scale
        hi_z = (b.origin.z + b.box_extent.z) * scale
        if base == 'floor':
            z = FLOOR - lo_z
        elif base == 'ceiling':
            z = CEILING - hi_z
        elif isinstance(base, str) and base.startswith('on:'):
            z = tops[base[3:]] - lo_z
        else:
            z = base - lo_z
        world = _to_world(x, y)
        import math
        # Facing in the Blender frame -> world: (dx, dy) -> (-dx, dy) after mirror + yaw 180.
        yaw = math.degrees(math.atan2(face[1], -face[0])) + front_offset
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(world.x, world.y, z), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        actor.set_actor_label('Hotel lobby · ' + slug)
        actor.tags = [unreal.Name('MareGenerated'), unreal.Name('Region_grand_hotel'), unreal.Name('MareHotelLobby')]
        actor.set_folder_path('Hotel/Lobby')
        tops[slug] = z + hi_z
        placed.append({'slug': slug, 'location': [world.x, world.y, z], 'yaw': yaw, 'height_cm': hi_z - lo_z})
    # Warm interior lights (Lumen GI carries them through the hall).
    for x in (-10.0, 0.0, 10.0):
        for y in (-2.0, 3.0):
            w = _to_world(x, y)
            light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(w.x, w.y, 400))
            c = light.point_light_component
            c.set_intensity(2500.0)
            c.set_light_color(unreal.LinearColor(1.0, 0.86, 0.68, 1.0))
            c.set_attenuation_radius(900.0)
            c.set_editor_property('cast_shadows', True)
            c.set_editor_property('contact_shadow_length', .08)   # 03/11, Sergio: "nada tem sombra, fica artificial"
            light.tags = [unreal.Name('MareGenerated'), unreal.Name('Region_grand_hotel'), unreal.Name('MareHotelLobby')]
            light.set_folder_path('Hotel/Lobby')
            light.set_actor_label('Hotel lobby · luz')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    layout = {'tower': [TOWER_ORIGIN.x, TOWER_ORIGIN.y], 'placed': placed}
    (DATA / 'hotel_lobby.json').write_text(json.dumps(layout, indent=1), encoding='utf-8')
    return layout


def view(name):
    """Editor camera views of the lobby (PIE stopped); returns the camera for CaptureViewport."""
    views = {'entrance': ((0.0, -12.0, 1.7), (0.0, 1.0)), 'lounge': ((6.0, -4.5, 1.7), (-1.0, 0.4)),
             'reception': ((-4.0, -2.0, 1.7), (-0.6, 1.0)), 'elevators': ((2.0, -1.0, 1.7), (0.6, 1.0))}
    if name not in views:
        x, y, z, dx, dy = [float(v) for v in name.split(',')]
    else:
        (x, y, z), (dx, dy) = views[name]
    import math
    w = _to_world(x, y)
    yaw = math.degrees(math.atan2(dy, -dx))
    return {'location': {'x': w.x, 'y': w.y, 'z': z * 100 + FLOOR}, 'rotation': {'pitch': -12, 'yaw': yaw, 'roll': 0}}


def near(x, y, radius):
    """Level actors/instances whose location lies within radius metres of a lobby point."""
    w = _to_world(x, y)
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not c.static_mesh:
                continue
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True).translation
                if (t.x - w.x) ** 2 + (t.y - w.y) ** 2 < (radius * 100) ** 2 and t.z < 600:
                    out.append({'actor': a.get_actor_label(), 'mesh': c.static_mesh.get_name(), 'at': [round(t.x), round(t.y), round(t.z)], 'visible': c.is_visible()})
    return out


def clear_grass():
    """Remove lawn instances generated under the old solid ground floor (now the lobby)."""
    removed = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if not a.get_actor_label().startswith('PCG Inland Grass'):
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            doomed = [i for i in range(c.get_instance_count())
                      if -3740 < c.get_instance_transform(i, True).translation.x < -460 and 5610 < c.get_instance_transform(i, True).translation.y < 6990]
            if doomed:
                c.remove_instances(doomed)
                removed += len(doomed)
    path = DATA / 'grass_coverage.json'
    manifest = json.loads(path.read_text(encoding='utf-8-sig'))
    total = sum(c.get_instance_count() for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
                if a.get_actor_label().startswith('PCG Inland Grass') for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent))
    manifest['instances'] = total
    manifest['hotel_lobby_removed'] = manifest.get('hotel_lobby_removed', 0) + removed
    path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'removed': removed, 'instances': total}


def glass_info():
    out = {}
    for path in ('/Game/Graphics/Architecture/HotelTower_Glass/MA_267fb69ef073ee86a78de3dd', '/Game/World/Models/World_2365/MA_267fb69ef073ee86a78de3dd'):
        m = unreal.load_asset(path)
        if not m:
            continue
        row = {'class': m.get_class().get_name()}
        if isinstance(m, unreal.MaterialInstanceConstant):
            row['parent'] = m.get_editor_property('parent').get_path_name()
            row['vectors'] = {str(p.parameter_info.name): [p.parameter_value.r, p.parameter_value.g, p.parameter_value.b, p.parameter_value.a] for p in m.get_editor_property('vector_parameter_values')}
            row['scalars'] = {str(p.parameter_info.name): p.parameter_value for p in m.get_editor_property('scalar_parameter_values')}
        out[path] = row
    return out


def hotel_window_glass():
    """Hotel tower windows: the clear kiosk glass showed the empty, evenly lit beige rooms behind it, so from outside
    every balcony door read as a solid wall. Real hotel glazing seen by day is darker and reflective: a grey-green
    tint, mostly opaque face-on and a mirror at grazing angles. Own material, the kiosk and house keep the clear one."""
    from mare_materials import material, expression, custom, MEL
    mat = material('M_HotelWindowGlass')
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property('two_sided', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    mat.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(.035, .05, .055, 1)), '', unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.04), '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=1.0), '', unreal.MaterialProperty.MP_SPECULAR)
    MEL.connect_material_property(expression(mat, unreal.MaterialExpressionConstant, r=.9), '', unreal.MaterialProperty.MP_METALLIC)
    fresnel = expression(mat, unreal.MaterialExpressionFresnel, exponent=4., base_reflect_fraction=.08)
    MEL.connect_material_property(custom(mat, 'return .72 + F*.26;', unreal.CustomMaterialOutputType.CMOT_FLOAT1, {'F': fresnel}), '', unreal.MaterialProperty.MP_OPACITY)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    changed = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if not c.static_mesh or 'HotelTower_Glass' not in c.static_mesh.get_name():
                continue
            for j in range(c.get_num_materials()):
                c.set_material(j, mat)
                changed.append([a.get_actor_label(), j])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return changed


def neutral_glass():
    """Override only the glass slots of the hotel glass proxy with the clear neutral glass."""
    glass = unreal.load_asset('/Game/World/Materials/M_ClearWindowGlass')
    if not glass:
        raise RuntimeError('M_ClearWindowGlass missing')
    if not glass.get_editor_property('used_with_instanced_static_meshes'):
        glass.set_editor_property('used_with_instanced_static_meshes', True)
        unreal.MaterialEditingLibrary.recompile_material(glass)
        unreal.EditorAssetLibrary.save_loaded_asset(glass, False)
    changed = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if 'HotelTower_Glass' not in str(c.get_editor_property('component_tags')) or not c.static_mesh:
                continue
            for j, slot in enumerate(c.static_mesh.static_materials):
                name = slot.material_interface.get_name() if slot.material_interface else ''
                if '267fb69ef073' in name or 'a3573534a1ac' in name:
                    c.set_material(j, glass)
                    changed.append([a.get_actor_label(), j, name])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return changed


def save_and_quit():
    """Save dirty maps/assets and close the editor cleanly (needed before compiling C++)."""
    saved = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.SystemLibrary.quit_editor()
    return {'saved': saved}


def pie(step):
    """QA PIE checks for the lobby: capsule path through the entrance, reception focus/use."""
    if '-MareSaveRoot=D:/CodexTemp/' not in unreal.SystemLibrary.get_command_line():
        raise RuntimeError('QA profile required')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:
        raise RuntimeError('Start PIE first')
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    out = {'step': step}
    if step == 'entrance':
        a, b = _to_world(0, -9.5), _to_world(0, 2.5)
        hit = unreal.SystemLibrary.capsule_trace_single(world, unreal.Vector(a.x, a.y, 140), unreal.Vector(b.x, b.y, 140), 32, 70,
                                                        unreal.TraceTypeQuery.TRACE_TYPE_QUERY2, False, [hero], unreal.DrawDebugTrace.NONE, True)
        out['blocked'] = bool(hit)
        if hit:
            t = hit.to_tuple()
            out['hit_at'] = [round(t[4].x), round(t[4].y), round(t[4].z)]
            out['hit_actor'] = t[9].get_actor_label() if t[9] else None
        hero.set_actor_location(unreal.Vector(a.x, a.y, 140), False, True)
        pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-5, yaw=90))
    elif step == 'inside':
        p = _to_world(-7.1, -0.4)
        hero.set_actor_location(unreal.Vector(p.x, p.y, 140), False, True)
        pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(p.x, p.y, 214), unreal.Vector(-1390, 6470, 160)))
    elif step == 'use':
        target = unreal.MareServiceTarget.find_focused(pc)
        out['focused'] = str(target.label) if target else None
        if target and str(target.action) == 'HotelReception':
            target.use(pc)
        out['phone_open'] = pc.get_editor_property('phone_open')
    elif step == 'shot':
        unreal.SystemLibrary.execute_console_command(world, 'Shot showui')
    elif step == 'close':
        pc.close_phone()
    loc = hero.get_actor_location()
    out['hero'] = [round(loc.x), round(loc.y), round(loc.z)]
    return out


def run(action, arg=''):
    if action == 'pie':
        return pie(arg)
    if action == 'quit':
        return save_and_quit()
    if action == 'hotelglass':
        return hotel_window_glass()
    if action == 'neutralglass':
        return neutral_glass()
    if action == 'glass':
        return glass_info()
    if action == 'cleargrass':
        return clear_grass()
    if action == 'reimport':
        return reimport()
    if action == 'instances':
        return tower_instances()
    if action == 'furnish':
        return furnish(float(arg or 0))
    if action == 'near':
        x, y, r = [float(v) for v in arg.split(',')]
        return near(x, y, r)
    if action == 'view':
        return view(arg)
    if action.startswith('hud_'):
        import importlib, mare_hud
        importlib.reload(mare_hud)
        return mare_hud.run(action[4:], arg)
    if action.startswith('mh_'):
        import importlib, mare_metahuman
        importlib.reload(mare_metahuman)
        return mare_metahuman.run(action[3:], arg)
    if action.startswith('fab'):
        import importlib, mare_fab
        importlib.reload(mare_fab)
        return mare_fab.run(action[4:], arg)
    raise ValueError(action)
