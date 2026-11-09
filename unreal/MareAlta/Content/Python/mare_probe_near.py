"""Editor probe: static mesh components near a point (QA helper, 09/11). arg "x,y,z,radius" (cm)."""
import json
import unreal


def near(arg=''):
    x, y, z, r = (float(v) for v in arg.split(','))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in actor.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if not m:
                continue
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                n = c.get_instance_count()
                for i in range(min(n, 4000)):
                    l = c.get_instance_transform(i, True).translation
                    if (l.x - x) ** 2 + (l.y - y) ** 2 + (l.z - z) ** 2 < r * r:
                        out.append({'actor': actor.get_actor_label(), 'mesh': m.get_path_name(), 'inst': i, 'at': [round(l.x), round(l.y), round(l.z)],
                                    'mats': [c.get_material(k).get_path_name() if c.get_material(k) else None for k in range(c.get_num_materials())]})
                        break
            else:
                l = c.get_world_location()
                if (l.x - x) ** 2 + (l.y - y) ** 2 + (l.z - z) ** 2 < r * r:
                    out.append({'actor': actor.get_actor_label(), 'mesh': m.get_path_name(), 'at': [round(l.x), round(l.y), round(l.z)],
                                'mats': [c.get_material(k).get_path_name() if c.get_material(k) else None for k in range(c.get_num_materials())]})
    open("D:/CodexTemp/probe_near.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=0))
    return len(out)


def mat_info(arg=''):
    """Textures and scalar/vector values a material (or instance) uses. arg: asset path or name fragment under /Game."""
    path = arg
    if not path.startswith('/'):
        hits = [a for a in unreal.EditorAssetLibrary.list_assets('/Game', recursive=True) if arg in a]
        path = hits[0] if hits else ''
    m = unreal.load_asset(path)
    out = {'path': path, 'class': m.get_class().get_name() if m else None}
    if isinstance(m, unreal.MaterialInstance):
        out['parent'] = m.get_editor_property('parent').get_path_name()
        out['tex'] = [[str(p.parameter_info.name), p.parameter_value.get_path_name() if p.parameter_value else None] for p in m.get_editor_property('texture_parameter_values')]
        out['scal'] = [[str(p.parameter_info.name), p.parameter_value] for p in m.get_editor_property('scalar_parameter_values')]
    if isinstance(m, unreal.Material):
        out['used_tex'] = [t.get_path_name() for t in unreal.MaterialEditingLibrary.get_used_textures(m)]
    return json.dumps(out, default=str)


def mesh_uv(arg=''):
    """UV0 extent and triangle count of a static mesh (LOD0 section 0) via the mesh description. arg: asset path."""
    m = unreal.load_asset(arg)
    sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    bb = m.get_bounding_box()
    return json.dumps({'tris': m.get_num_triangles(0), 'box': [str(bb.min), str(bb.max)], 'uv_channels': sub.get_num_uv_channels(m, 0),
                       'nanite': m.get_editor_property('nanite_settings').enabled})


def tex_info(arg=''):
    t = unreal.load_asset(arg)
    return json.dumps({'size': [t.blueprint_get_size_x(), t.blueprint_get_size_y()], 'srgb': t.get_editor_property('srgb'),
                       'source': t.get_editor_property('asset_import_data').get_first_filename() if t.get_editor_property('asset_import_data') else None})


def forest_meshes(arg=''):
    """Nanite settings, LODs and material blend modes of the island forest trees (far trees losing leaves, 09/11)."""
    import mare_mountains as mm
    out = {}
    for slug in (arg or 'World_0507,tree_small_02,World_0505,jacaranda_tree,World_0504,World_1206').split(','):
        m = mm._mesh(slug)
        ns = m.get_editor_property('nanite_settings')
        mats = []
        for sm in m.get_editor_property('static_materials'):
            mi = sm.material_interface
            base = mi.get_base_material() if mi else None
            mats.append([mi.get_name() if mi else None, str(base.get_editor_property('blend_mode')).split('.')[-1] if base else None,
                         base.get_editor_property('two_sided') if base else None])
        props = {}
        for p in ('enabled', 'preserve_area', 'explicit_tangents', 'fallback_percent_triangles', 'keep_percent_triangles', 'position_precision', 'shape_preservation'):
            try:
                v = ns.get_editor_property(p)
                props[p] = str(v)
            except Exception:
                pass
        out[slug] = {'path': m.get_path_name(), 'tris': m.get_num_triangles(0), 'lods': m.get_num_lods(), 'nanite': props, 'mats': mats}
    return json.dumps(out)


def forest_preserve_area(arg=''):
    """Far trees lost their leaves (09/11): Nanite simplified the leaf cards away at ~1 km. Shape preservation
    'Preserve Area' (made for foliage) keeps the leaf area as it simplifies. PIE stopped; saves the meshes."""
    import mare_mountains as mm
    sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    done = []
    for slug in (arg or 'World_0507,tree_small_02,World_0505,jacaranda_tree,World_0504,World_1206').split(','):
        m = mm._mesh(slug)
        ns = m.get_editor_property('nanite_settings')
        ns.set_editor_property('shape_preservation', unreal.NaniteShapePreservation.PRESERVE_AREA)
        sub.set_nanite_settings(m, ns, True)
        unreal.EditorAssetLibrary.save_loaded_asset(m, False)
        done.append([slug, str(m.get_editor_property('nanite_settings').get_editor_property('shape_preservation'))])
    return json.dumps(done)


def texts(arg=''):
    """TextRender components in the editor world whose text contains arg (case-insensitive)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in actor.get_components_by_class(unreal.TextRenderComponent):
            t = str(c.get_editor_property('text'))
            if arg.lower() in t.lower():
                l = c.get_world_location()
                out.append({'actor': actor.get_actor_label(), 'comp': c.get_name(), 'text': t, 'at': [round(l.x), round(l.y), round(l.z)]})
    return json.dumps(out, ensure_ascii=False, default=str)


def pool_sign(_=''):
    """09/11: the pool sign read 'duche' (European Portuguese) in the Brazilian game: 'ducha'. PIE stopped; saves the level."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    n = 0
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in actor.get_components_by_class(unreal.TextRenderComponent):
            if str(c.get_editor_property('text')) == 'PISCINA<br>duche antes de entrar':
                c.set_editor_property('text', 'PISCINA<br>ducha antes de entrar')
                n += 1
    if n:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return n


def count_near(arg=''):
    """Instances per (actor, mesh) within radius of x,y (any z). arg 'x,y,r'."""
    x, y, r = (float(v) for v in arg.split(','))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = {}
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not c.static_mesh:
                continue
            n = 0
            for i in range(c.get_instance_count()):
                l = c.get_instance_transform(i, True).translation
                if (l.x - x) ** 2 + (l.y - y) ** 2 < r * r:
                    n += 1
            if n:
                out[actor.get_actor_label()[:50] + ' | ' + c.static_mesh.get_name()] = n
    return json.dumps(out, ensure_ascii=False, default=str)


def mesh_mats(arg=''):
    m = unreal.load_asset(arg)
    out = []
    for sm in m.get_editor_property('static_materials'):
        mi = sm.material_interface
        row = {'slot': str(sm.material_slot_name), 'mat': mi.get_path_name() if mi else None}
        if isinstance(mi, unreal.MaterialInstance):
            row['tex'] = [p.parameter_value.get_path_name() for p in mi.get_editor_property('texture_parameter_values') if p.parameter_value]
            row['vec'] = [[str(p.parameter_info.name), str(p.parameter_value)] for p in mi.get_editor_property('vector_parameter_values')]
        out.append(row)
    b = m.get_bounds()
    return json.dumps({'mats': out, 'extent': [round(b.box_extent.x), round(b.box_extent.y), round(b.box_extent.z)]})


def pie_hide(arg=''):
    """PIE: hide/show actors whose label contains a text. arg 'text|1' hides, 'text|0' shows. Returns how many."""
    text, on = (arg.split('|') + ['1'])[:2]
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    n = 0
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if text in a.get_actor_label():
            a.set_actor_hidden_in_game(on == '1')
            n += 1
    return n


def covering(arg=''):
    """Primitive components whose world bounds contain the point x,y (any z <= 300): name, actor, extent, collision."""
    x, y = (float(v) for v in arg.split(','))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if isinstance(c, unreal.InstancedStaticMeshComponent) or not c.static_mesh:
                continue
            o, e, _r = unreal.SystemLibrary.get_component_bounds(c)
            if abs(x - o.x) < e.x and abs(y - o.y) < e.y and o.z - e.z < 300:
                out.append([a.get_actor_label()[:40], c.static_mesh.get_name(), [round(o.z), round(e.x), round(e.y), round(e.z)], str(c.get_collision_enabled()).split('.')[-1], [str(t) for t in a.tags][:3]])
    return json.dumps(out, ensure_ascii=False, default=str)


def trace(arg=''):
    """Editor trace down at x,y: actor, component, mesh, hit z, instance index (ISM)."""
    out = []
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for spec in arg.split(';'):
        x, y = (float(v) for v in spec.split(','))
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 3000), unreal.Vector(x, y, -500),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        if not hit:
            out.append([x, y, None])
            continue
        t = hit.to_tuple()
        comp = t[10]
        mesh = comp.static_mesh.get_name() if isinstance(comp, unreal.StaticMeshComponent) and comp.static_mesh else None
        mat = comp.get_material(0).get_name() if comp and comp.get_num_materials() else None
        out.append([x, y, round(t[4].z), t[9].get_actor_label()[:40] if t[9] else None, comp.get_name() if comp else None, mesh, mat, t[11] if len(t) > 11 else None])
    return json.dumps(out, ensure_ascii=False, default=str)


def lawn_at(arg=''):
    """Lawn instances within r of x,y with their z and what a short trace finds over them."""
    x, y, r = (float(v) for v in arg.split(','))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if 'Gramado' not in a.get_actor_label():
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            for i in range(c.get_instance_count()):
                l = c.get_instance_transform(i, True).translation
                if (l.x - x) ** 2 + (l.y - y) ** 2 < r * r:
                    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(l.x, l.y, l.z + 80), unreal.Vector(l.x, l.y, l.z - 30),
                                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
                    t = hit.to_tuple() if hit else None
                    out.append([a.get_actor_label()[-14:], c.get_name(), [round(l.x), round(l.y), round(l.z)],
                                [round(t[4].z), t[9].get_actor_label()[:30] if t[9] else None, t[10].get_material(0).get_name() if t[10] and t[10].get_num_materials() else None] if t else None])
    return json.dumps(out[:40], ensure_ascii=False, default=str)


def pie_pick(arg=''):
    """PIE: what is under screen points given as fractions 'u,v;u,v' (0..1): world hit, actor, component, material."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    size = unreal.WidgetLayoutLibrary.get_viewport_size(world)
    out = []
    for spec in arg.split(';'):
        u, v = (float(t) for t in spec.split(','))
        r = unreal.GameplayStatics.deproject_screen_to_world(pc, unreal.Vector2D(u * size.x, v * size.y))
        origin, direction = (r[-2], r[-1]) if isinstance(r, tuple) else (r.world_position, r.world_direction)
        hit = unreal.SystemLibrary.line_trace_single(world, origin, origin + direction * 300000, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                     True, [unreal.GameplayStatics.get_player_pawn(world, 0)], unreal.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else None
        out.append([u, v, [round(t[4].x), round(t[4].y), round(t[4].z)] if t else None, t[9].get_actor_label()[:40] if t and t[9] else None,
                    t[10].get_material(0).get_name() if t and t[10] and t[10].get_num_materials() else None])
    return json.dumps(out, ensure_ascii=False, default=str)


def by_label(arg=''):
    """Editor actors whose label contains arg: location, scale, mesh, materials, bounds."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if arg in a.get_actor_label():
            l, s = a.get_actor_location(), a.get_actor_scale3d()
            o, e = a.get_actor_bounds(False)
            c = a.get_component_by_class(unreal.StaticMeshComponent)
            out.append({'label': a.get_actor_label(), 'at': [round(l.x), round(l.y), round(l.z)], 'scale': [round(s.x, 2), round(s.y, 2), round(s.z, 2)],
                        'extent': [round(e.x), round(e.y), round(e.z)], 'mesh': c.static_mesh.get_path_name() if c and c.static_mesh else None,
                        'mats': [c.get_material(i).get_path_name() for i in range(c.get_num_materials())] if c else []})
    return json.dumps(out, ensure_ascii=False)


def tex_groups(arg='/Game/People/MetaHumans'):
    """Texture2D under a path from the asset registry (no loading): count and approximate MB by LOD group and by size."""
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    flt = unreal.ARFilter(package_paths=[arg], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath('/Script/Engine', 'Texture2D')])
    by = {}
    for ad in reg.get_assets(flt):
        dims = str(ad.get_tag_value('Dimensions') or '')
        group = str(ad.get_tag_value('LODGroup') or '?')
        try:
            w, h = (int(v) for v in dims.split('x')[:2])
        except Exception:
            w = h = 0
        key = f'{group} {max(w, h)}'
        n, mb = by.get(key, (0, 0.0))
        by[key] = (n + 1, mb + w * h * 1.33 / 1048576)   # ~1 byte/texel compressed with mips
    return json.dumps(dict(sorted(by.items(), key=lambda kv: -kv[1][1])[:25]))


def rebuild_grounds(_=''):
    """Rebuild the three ground materials (village, island, seabed) from mare_materials.build_ground (PIE stopped)."""
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    out = []
    for kw in ({}, {'island': True}, {'seabed': True}):
        m = mare_materials.build_ground(**kw)
        out.append(m.get_path_name() if hasattr(m, 'get_path_name') else str(m))
    return json.dumps(out)


def cap_textures(arg=''):
    """B16 (09/11): MetaHuman textures above 2048 (39 at 8K, ~30 at 4K: ~4 GB of the 6 GB demo package) get
    MaxTextureSize 2048 (the cook drops the larger mips). arg 'path|limit|max_n' (dry: 'path|limit|0'). Saves each one."""
    path, limit, max_n = (arg.split('|') + ['/Game/People/MetaHumans', '2048', '12'])[:3] if arg else ('/Game/People/MetaHumans', '2048', '12')
    limit, max_n = int(limit), int(max_n)
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    flt = unreal.ARFilter(package_paths=[path], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath('/Script/Engine', 'Texture2D')])
    todo = []
    for ad in reg.get_assets(flt):
        try:
            w, h = (int(v) for v in str(ad.get_tag_value('Dimensions')).split('x')[:2])
        except Exception:
            continue
        if max(w, h) > limit:
            todo.append(str(ad.package_name) + '.' + str(ad.asset_name))
    done = []
    for p in todo:
        if len(done) >= max_n:
            break
        t = unreal.load_asset(p)
        if t.get_editor_property('max_texture_size') == limit:
            continue
        t.set_editor_property('max_texture_size', limit)
        unreal.EditorAssetLibrary.save_loaded_asset(t, False)
        done.append(p.split('/')[-1])
    left = sum(1 for p in todo) - len(done)
    return json.dumps({'over_limit': len(todo), 'capped_now': done, 'dry': max_n == 0})


def import_book(_=''):
    """C13 (09/11): the open paperback (tools/ue58/gen_open_book.py) for the sunbathers reading on their towels."""
    import mare_hotel_lobby
    from pathlib import Path
    src = Path(unreal.Paths.project_dir()).resolve() / 'SourceArt/Models/Leisure/mare_open_book.glb'
    mesh = mare_hotel_lobby._import(src, '/Game/Custom/Leisure/mare_open_book', 'mare_open_book', False, search=False)
    unreal.EditorAssetLibrary.save_directory('/Game/Custom/Leisure/mare_open_book')
    b = mesh.get_bounds()
    return json.dumps({'mesh': mesh.get_path_name(), 'extent': [round(b.box_extent.x, 1), round(b.box_extent.y, 1), round(b.box_extent.z, 1)]})


def shaft_material(_=''):
    """C19 (09/11): M_UnderwaterShaft, additive unlit light shaft for the sun rays under water (AMareCharacter spawns a
    few long planes along the sun direction around the eyes while they are under the surface). U across the shaft,
    V along it (0 = surface end); soft edges, fading with depth, flickering slowly. Parameter Strength (0..1)."""
    import mare_materials as mm
    MEL = unreal.MaterialEditingLibrary
    path = '/Game/World/Materials/M_UnderwaterShaft'
    mat = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_UnderwaterShaft', '/Game/World/Materials', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property('shading_model', unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property('two_sided', True)
    mat.set_editor_property('used_with_nanite', False)
    uv = mm.expression(mat, unreal.MaterialExpressionTextureCoordinate)
    t = mm.expression(mat, unreal.MaterialExpressionTime)
    pos = mm.expression(mat, unreal.MaterialExpressionWorldPosition)
    strength = mm.expression(mat, unreal.MaterialExpressionScalarParameter, parameter_name='Strength', default_value=1.0)
    e = mm.custom(mat, 'float a=pow(saturate(1-abs(UV.y*2-1)),2.2); float l=smoothstep(0,.08,UV.x)*(1-smoothstep(.25,1,UV.x));'
                       'float f=.55+.45*sin(T*.6+P.x*.004+P.y*.003)*sin(T*.37+UV.y*5);'
                       'return float3(.6,.9,.85)*a*l*f*.32*S;', unreal.CustomMaterialOutputType.CMOT_FLOAT3,
                  {'UV': uv, 'T': t, 'P': pos, 'S': strength})
    MEL.connect_material_property(e, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat.get_path_name()


def hero_shafts(_=''):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    out = {'hero_z': round(hero.get_actor_location().z), 'swimming': hero.get_movement_component().is_swimming()}
    rows = []
    for c in hero.get_components_by_class(unreal.StaticMeshComponent):
        if c.static_mesh and c.static_mesh.get_name() == 'Plane':
            l = c.get_world_location()
            rows.append([round(l.x), round(l.y), round(l.z), c.is_visible()])
    out['shafts'] = rows
    cam = hero.get_component_by_class(unreal.CameraComponent)
    out['eye_z'] = round(cam.get_world_location().z) if cam else None
    return json.dumps(out)


def show_shafts(arg='1'):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    n = 0
    for c in hero.get_components_by_class(unreal.StaticMeshComponent):
        if c.static_mesh and c.static_mesh.get_name() == 'Plane':
            c.set_visibility(arg == '1')
            m = c.get_material(0)
            if isinstance(m, unreal.MaterialInstanceDynamic):
                m.set_scalar_parameter_value('Strength', 1.0)
            n += 1
    return n


def hero_swim(arg='4000,-7600,-300,10,90'):
    """PIE: put the hero in the sea really swimming (movement mode) at x,y,z looking pitch,yaw."""
    x, y, z, pitch, yaw = (float(v) for v in arg.split(','))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    for c in world.get_all_actors_of_class(unreal.CameraActor) if hasattr(world, 'get_all_actors_of_class') else []:
        pass
    pc.set_view_target_with_blend(hero, 0.0)
    hero.set_actor_location(unreal.Vector(x, y, z), False, True)
    mv = hero.get_movement_component()
    mv.set_movement_mode(unreal.MovementMode.MOVE_SWIMMING)
    pc.set_control_rotation(unreal.Rotator(pitch=pitch, yaw=yaw, roll=0))
    return json.dumps({'swimming': mv.is_swimming(), 'z': round(hero.get_actor_location().z)})


def ground_tiles(arg=''):
    """Editor: instances of the 'Maré · Ground' ISM: count, z range, and how many have their top under the water
    (bounds max z < arg, default -40 cm)."""
    limit = float(arg or -40)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = {}
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if a.get_actor_label() != 'Maré · Ground':
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            b = c.static_mesh.get_bounds()
            n = c.get_instance_count()
            zs, under = [], []
            for i in range(n):
                t = c.get_instance_transform(i, True)
                top = t.translation.z + (b.origin.z + b.box_extent.z) * t.scale3d.z
                zs.append(top)
                if top < limit:
                    under.append([i, round(t.translation.x), round(t.translation.y), round(top)])
            out[c.get_name()] = {'mesh': c.static_mesh.get_name(), 'n': n, 'extent': [round(b.box_extent.x), round(b.box_extent.y), round(b.box_extent.z)],
                                 'top_min': round(min(zs)) if zs else None, 'top_max': round(max(zs)) if zs else None, 'under': len(under), 'sample': under[:8]}
    return json.dumps(out)


def two_floors(arg=''):
    """Editor: at points 'x,y;...' the island terrain's z and the sea floor planes' z (traced separately)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    every = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    terrain = [a for a in every if 'terreno novo' in a.get_actor_label()]
    others = [a for a in every if 'fundo de areia' not in a.get_actor_label() and 'terreno novo' not in a.get_actor_label()]
    out = []
    for spec in arg.split(';'):
        x, y = (float(v) for v in spec.split(','))
        row = [x, y]
        for ignore in (others + [a for a in every if 'fundo de areia' in a.get_actor_label()], others + terrain):
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 2000), unreal.Vector(x, y, -3000),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore, unreal.DrawDebugTrace.NONE, True)
            row.append(round(hit.to_tuple()[4].z) if hit else None)
        out.append(row)
    return json.dumps(out)


def comps_near(arg=''):
    """PIE or editor ('pie|x,y,r' / 'x,y,r'): non-instanced static mesh components near x,y with mesh, location,
    rotation, world bounds extent; also instances of ISMs."""
    use_pie = arg.startswith('pie|')
    x, y, r = (float(v) for v in arg.replace('pie|', '').split(','))
    sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = sub.get_game_world() if use_pie else sub.get_editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if not c.static_mesh:
                continue
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                for i in range(min(c.get_instance_count(), 3000)):
                    t = c.get_instance_transform(i, True)
                    l = t.translation
                    if (l.x - x) ** 2 + (l.y - y) ** 2 < r * r:
                        rr = t.rotation.rotator()
                        out.append([a.get_actor_label()[:34], c.static_mesh.get_name(), 'inst%d' % i, [round(l.x), round(l.y), round(l.z)], [round(rr.pitch), round(rr.yaw), round(rr.roll)]])
                continue
            l = c.get_world_location()
            if (l.x - x) ** 2 + (l.y - y) ** 2 < r * r:
                o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
                rr = c.get_world_rotation()
                out.append([a.get_actor_label()[:34], c.static_mesh.get_name(), c.get_name()[:20], [round(l.x), round(l.y), round(l.z)], [round(rr.pitch), round(rr.yaw), round(rr.roll)], [round(e.x), round(e.y), round(e.z)]])
    return json.dumps(out, ensure_ascii=False)


def _settle(c, i, rot, xy, floor):
    """Give ISM instance i of component c a new rotation and xy, then lift/lower it so its lowest corner is on floor."""
    import itertools
    m = c.static_mesh
    b = m.get_bounds()
    t = c.get_instance_transform(i, True)
    nt = unreal.Transform(unreal.Vector(xy[0], xy[1], 0), rot, t.scale3d)
    lo = min(nt.transform_location(unreal.Vector(b.origin.x + sx * b.box_extent.x, b.origin.y + sy * b.box_extent.y, b.origin.z + sz * b.box_extent.z)).z
             for sx, sy, sz in itertools.product((-1, 1), repeat=3))
    nt = unreal.Transform(unreal.Vector(xy[0], xy[1], floor - lo), rot, t.scale3d)
    c.update_instance_transform(i, nt, True, True, True)
    return [round(xy[0]), round(xy[1]), round(floor - lo)]


def pier_props(_=''):
    """09/11 (Sergio's photos of the pier end): the loose fishing rod (World_2013, 2.2 m) stood leaning at 52 degrees
    against nothing: it lies on the boards now; the lifebuoy stood on its edge through the lamp post: it lies flat on
    the deck beside the post. Deck top z 37. PIE stopped; saves the level."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    done = {}
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not c.static_mesh:
                continue
            name = c.static_mesh.get_name()
            for i in range(c.get_instance_count()):
                l = c.get_instance_transform(i, True).translation
                if name == 'World_2013' and abs(l.x - 7080) < 30 and abs(l.y + 4830) < 30:
                    done['rod'] = _settle(c, i, unreal.Rotator(roll=-89, pitch=0, yaw=-8), (7085, -4775), 37.5)
                if name == 'World_0095' and abs(l.x - 7340) < 30 and abs(l.y + 4660) < 30:
                    done['lifebuoy'] = _settle(c, i, unreal.Rotator(roll=90, pitch=0, yaw=-23), (7365, -4735), 37.5)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(done)


def moulding_fix(_=''):
    """09/11 (photo tour): the hero house's back wall moulding pieces carried another material and one read as a
    red-brown bar across the wall; they take the cream crown moulding material of the rest of the room."""
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    hits = [str(a.package_name) + '.' + str(a.asset_name) for a in reg.get_assets_by_package_name('', False)] if False else []
    cream = None
    for p in unreal.EditorAssetLibrary.list_assets('/Game/World/Models', recursive=True):
        if p.endswith('MA_771fc049788c61dd623d8e61.MA_771fc049788c61dd623d8e61') or p.split('/')[-1].startswith('MA_771fc049788c61dd623d8e61'):
            cream = unreal.load_asset(p)
            break
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    done = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if 'Back wall moulding' in a.get_actor_label():
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                for k in range(c.get_num_materials()):
                    c.set_material(k, cream)
                done.append(a.get_actor_label())
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'material': cream.get_path_name() if cream else None, 'actors': done}, ensure_ascii=False)


def summit_view(arg=''):
    """09/11 (photo tour): Seu Tiburcio's bench on the summit (4000,37900, facing -Y, the sea) looked into tree crowns.
    Tree instances in a 70 degree wedge in front of the bench out to 45 m are removed (instanced foliage of the forest
    and mountain vegetation; shrubs and ferns stay). arg 'dry' counts. PIE stopped; saves."""
    import math
    bx, by, bz = 4000.0, 37900.0, 10720.0
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    trees = ('tree', 'jacaranda', 'World_0504', 'World_0505', 'World_0507', 'World_1206', 'palm', 'Palm')
    out = {}
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not c.static_mesh or not any(t in c.static_mesh.get_name() or t in c.get_name() for t in trees):
                continue
            drop = []
            for i in range(c.get_instance_count()):
                l = c.get_instance_transform(i, True).translation
                dx, dy = l.x - bx, l.y - by
                d = math.hypot(dx, dy)
                if d < 300 or d > 4500:
                    continue
                ang = math.degrees(math.atan2(dx, -dy))   # 0 = straight towards -Y
                if abs(ang) < 35:
                    drop.append(i)
            if drop:
                out[a.get_actor_label()[:30] + '|' + c.static_mesh.get_name()] = len(drop)
                if arg != 'dry':
                    c.remove_instances(drop)
    if arg != 'dry':
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out, ensure_ascii=False)


def hide_red_beam(_=''):
    """09/11 (photo tour): a terracotta 3.7 m piece of the Godot export (World_1141, '@MeshInstance3D@2942') hung at the
    ceiling of the hero's living room and read as a red bar across the back wall. Hidden in game, no collision.
    SUPERSEDED (09/11 16:30): it is the bathroom annex roof; do not run this, see annex_roof."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    n = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if a.get_actor_label() == 'Maré · @MeshInstance3D@2942':
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                c.set_visibility(False)
                c.set_hidden_in_game(True)
                c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            n.append(a.get_actor_label())
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(n, ensure_ascii=False)


def find_labels(arg='bangal,hero'):
    """Editor: level actors whose label contains any of the comma-separated words, with their location (tour poses)."""
    import unreal
    keys = [k.strip().lower() for k in arg.split(',') if k.strip()]
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = a.get_actor_label()
        if any(k in label.lower() for k in keys):
            p = a.get_actor_location()
            out.append('%s %d %d %d' % (label, p.x, p.y, p.z))
    return '\n'.join(out[:80]) + '\n#%d' % len(out)


def ground(arg=''):
    """Editor: at points 'x,y;...' the highest hit from 30 km down (terrain, hills, roofs): label and z (tour poses)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for spec in arg.split(';'):
        x, y = (float(v) for v in spec.split(','))
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 30000), unreal.Vector(x, y, -3000),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else None
        out.append([x, y, round(t[4].z) if t else None, (t[9].get_actor_label()[:30] if t and t[9] else None)])
    return json.dumps(out, ensure_ascii=False)


def annex_roof(arg='info'):
    """09/11 16:30: the hero house's bathroom annex roof (World_1141, '@MeshInstance3D@2942') was hidden in the morning as
    a 'red bar' in the living room: it is the annex roof, 3.7 m long, poking ~27 cm through the house's south wall
    (y ~1748) under the living room ceiling. arg 'info' reports it; 'fix:<dy>:<sx>' shows it again at y 1590+dy with its length along y scaled by sx (fix:-14:0.925 keeps
    the south eave and ends the north edge at the wall)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if a.get_actor_label() != 'Maré · @MeshInstance3D@2942':
            continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
            row = {'comp': c.get_name(), 'mesh': c.static_mesh.get_name() if c.static_mesh else None, 'visible': c.is_visible(),
                   'center': [round(o.x), round(o.y), round(o.z)], 'extent': [round(e.x), round(e.y), round(e.z)],
                   'mesh_box': str(c.static_mesh.get_bounding_box()) if c.static_mesh else None}
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                t = c.get_instance_transform(0, True)
                row['inst'] = [round(t.translation.x), round(t.translation.y), round(t.translation.z), str(t.rotation.rotator()), str(t.scale3d)]
                if arg.startswith('fix:'):
                    dy, sx = (float(v) for v in arg[4:].split(':'))
                    t.translation = unreal.Vector(4775, 1590 + dy, t.translation.z)
                    t.scale3d = unreal.Vector(sx, 1, 1)   # local X runs along world Y (yaw -90)
                    c.update_instance_transform(0, t, True, True, True)
            if arg.startswith('fix:'):
                c.set_visibility(True)
                c.set_hidden_in_game(False)
                c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            out.append(row)
    if arg.startswith('fix:'):
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out, ensure_ascii=False)


def lights_near(arg='7300,-4300,1500'):
    """Editor: light components within r of x,y: owner label, class, color, intensity, radius, location."""
    x, y, r = (float(v) for v in arg.split(','))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.LocalLightComponent):
            l = c.get_world_location()
            if (l.x - x) ** 2 + (l.y - y) ** 2 < r * r:
                col = c.get_editor_property('light_color')
                out.append([a.get_actor_label()[:36], c.get_class().get_name(), [col.r, col.g, col.b], round(c.intensity, 1),
                            round(c.get_editor_property('attenuation_radius')), [round(l.x), round(l.y), round(l.z)],
                            [str(t) for t in a.tags][:3]])
    return json.dumps(out, ensure_ascii=False)


def island_ground(_=''):
    """Editor, PIE stopped: rebuild M_IslandGround_PBR from mare_materials (reloaded first: modules stay cached)."""
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    return mare_materials.build_ground(island=True).get_path_name()


def hide_entrada(_=''):
    """09/11 (detail survey): the two Godot 'ENTRADA' labels of the kiosk sides (y -1225, z 145) now sit on the stove
    and the fridge fronts: the new kitchen stands where the side entrances were. Hidden in game, saved."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    n = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if a.get_actor_label() == 'Letreiro · ENTRADA':
            a.set_actor_hidden_in_game(True)
            for c in a.get_components_by_class(unreal.TextRenderComponent):
                c.set_visibility(False)
            n.append(a.get_actor_label())
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(n, ensure_ascii=False)
