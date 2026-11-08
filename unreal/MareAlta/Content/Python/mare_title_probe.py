"""Title QA (08/11): texture sizes as the game sees them and the geometry of the title widgets."""
import json
import unreal


def run(_=''):
    out = {}
    for name in ['T_TitleArt', 'T_TitleLogo']:
        t = unreal.load_asset('/Game/UI/Title/' + name)
        out[name] = {'size': [t.blueprint_get_size_x(), t.blueprint_get_size_y()],
                     'pow2': str(t.get_editor_property('power_of_two_mode')),
                     'max': t.get_editor_property('max_texture_size')}
    vp = unreal.WidgetLayoutLibrary.get_viewport_size(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world())
    scale = unreal.WidgetLayoutLibrary.get_viewport_scale(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world())
    out['viewport'] = [vp.x, vp.y, scale]
    return json.dumps(out, default=str)


def outline(arg=''):
    """QA: blendables on the hero camera; with arg 'label' also outlines that actor's meshes."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    cam = pawn.get_component_by_class(unreal.CameraComponent)
    pp = cam.get_editor_property('post_process_settings')
    blend = pp.get_editor_property('weighted_blendables').get_editor_property('array')
    out = {'blendables': [str(b.get_editor_property('object')) for b in blend],
           'cvar': unreal.SystemLibrary.get_console_variable_int_value('r.CustomDepth')}
    if arg:
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            if arg in a.get_actor_label():
                for c in a.get_components_by_class(unreal.PrimitiveComponent):
                    c.set_render_custom_depth(True)
                out['lit'] = a.get_actor_label()
                break
    return json.dumps(out)


def cameras(arg=''):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    out = {'view_target': str(pc.get_view_target().get_name()) if pc.get_view_target() else None,
           'cams': [[c.get_name(), c.is_active(), c.get_editor_property('post_process_blend_weight'),
                     len(c.get_editor_property('post_process_settings').get_editor_property('weighted_blendables').get_editor_property('array'))]
                    for c in pawn.get_components_by_class(unreal.CameraComponent)]}
    vols = [a.get_actor_label() for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume)]
    out['volumes'] = vols[:20]
    return json.dumps(out)


def ceiling(arg='3650,-1450,150'):
    """QA: first hit straight up and down from points (x,y,z;...) in the PIE world."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    out = []
    for spec in arg.split(';'):
        x, y, z = [float(v) for v in spec.split(',')]
        row = [spec]
        for dz in (2000, -2000):
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, z), unreal.Vector(x, y, z + dz),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
            t = hit.to_tuple() if hit else None
            row.append([round(t[4].z), t[9].get_actor_label()] if t and len(t) > 9 and t[9] else None)
        out.append(row)
    lamps = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if m and m.get_name() in ('World_1211', 'World_1229', 'World_0199'):
                l = c.get_world_location()
                lamps.append([m.get_name(), a.get_actor_label(), round(l.x), round(l.y), round(l.z)])
    return json.dumps({'traces': out, 'lamps': lamps[:12]}, ensure_ascii=False)


def near(arg='4385,1945,90,150'):
    """QA: mesh components whose bounds come within r of a point (x,y,z,r)."""
    x, y, z, r = [float(v) for v in arg.split(',')]
    p = unreal.Vector(x, y, z)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            o, e = c.get_local_bounds()
            tr = c.get_world_transform()
            lo, hi = tr.transform_location(o), tr.transform_location(e)
            o = unreal.Vector((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (lo.z + hi.z) / 2)
            e = unreal.Vector(abs(hi.x - lo.x) / 2, abs(hi.y - lo.y) / 2, abs(hi.z - lo.z) / 2)
            rad = (e.x * e.x + e.y * e.y + e.z * e.z) ** .5
            dx = max(abs(p.x - o.x) - e.x, 0); dy = max(abs(p.y - o.y) - e.y, 0); dz = max(abs(p.z - o.z) - e.z, 0)
            d = (dx * dx + dy * dy + dz * dz) ** .5
            if d < r:
                n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else -1
                mesh = c.static_mesh.get_name() if isinstance(c, unreal.StaticMeshComponent) and c.static_mesh else c.get_class().get_name()
                out.append([round(d), a.get_actor_label()[:30], mesh, round(rad), n, c.is_visible()])
    return json.dumps(sorted(out)[:25], ensure_ascii=False)


def hit(arg='4385,1750,184,4385,1960,70'):
    """QA: line trace a->b (visibility, complex) in PIE; the component hit and its class/mesh."""
    v = [float(x) for x in arg.split(',')]
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    h = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(*v[:3]), unreal.Vector(*v[3:]), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                               True, [unreal.GameplayStatics.get_player_pawn(world, 0)], unreal.DrawDebugTrace.NONE, True)
    if not h:
        return 'no hit'
    t = h.to_tuple()
    comp = t[10] if len(t) > 10 else None
    mesh = comp.static_mesh.get_path_name() if isinstance(comp, unreal.StaticMeshComponent) and comp.static_mesh else ''
    n = comp.get_instance_count() if isinstance(comp, unreal.InstancedStaticMeshComponent) else -1
    return json.dumps([str(t[4]), t[9].get_actor_label() if t[9] else None, comp.get_name() if comp else None, comp.get_class().get_name() if comp else None, mesh, n])


def people(arg='Morador'):
    """QA: name, position and speed of the people whose name contains arg (PIE)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    out = []
    for p in unreal.ObjectIterator(unreal.MarePerson):
        if p.get_world() != world:
            continue
        name = str(p.get_editor_property('person_name')) if hasattr(p, 'person_name') else p.get_name()
        l = p.get_actor_location()
        out.append([name[:18], round(l.x), round(l.y), round(l.z), round(p.get_velocity().length())])
    return json.dumps(out)


def ual_sit(_=''):
    """08/11 (reference tip 9, C11): the UAL sit-down and stand-up clips, retargeted to the MetaHumans."""
    import importlib
    import mare_metahuman
    importlib.reload(mare_metahuman)
    return str(mare_metahuman.import_ual(clips='Sitting_Enter,Sitting_Exit'))


def use(arg='RoomDoor'):
    """QA: uses the first visible interaction target whose action (or label) contains arg, as the player would (PIE)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    for t in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MareServiceTarget):
        if arg in str(t.get_editor_property('action')) or arg in str(t.get_editor_property('label')):
            t.use(pc)
            return json.dumps({'used': str(t.get_editor_property('label')), 'at': str(t.get_actor_location())})
    return 'none'


def state(arg=''):
    """QA: is the PIE game paused, its time dilation and game seconds (to tell a frozen world from slow walkers)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:
        return 'no pie'
    return json.dumps({'paused': unreal.GameplayStatics.is_game_paused(world),
                       'dilation': unreal.GameplayStatics.get_global_time_dilation(world),
                       'seconds': unreal.GameplayStatics.get_time_seconds(world),
                       'real': unreal.GameplayStatics.get_real_time_seconds(world)})


def navpath(arg='2000,3000,100,9000,6000,100'):
    """QA (PIE stopped): path on the saved navigation between two points: points count and length, or 'no path'."""
    v = [float(x) for x in arg.split(',')]
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    p = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, unreal.Vector(*v[:3]), unreal.Vector(*v[3:]))
    if not p:
        return 'no path object'
    pts = p.get_editor_property('path_points')
    return json.dumps({'points': len(pts), 'partial': p.is_partial(), 'valid': p.is_valid()})


def navactors(arg=''):
    """QA (PIE stopped): the navigation actors of the editor level (RecastNavMesh, NavMeshBoundsVolume) with bounds."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        c = a.get_class().get_name()
        if 'Nav' in c or 'Recast' in c:
            o, e = a.get_actor_bounds(False)
            out.append([c, a.get_actor_label(), a.get_name(), [round(o.x), round(o.y), round(o.z)], [round(e.x), round(e.y), round(e.z)]])
    return json.dumps(out)


def walkers(arg=''):
    """QA (PIE): every MarePerson with its speed, AI move status and location (why nobody walks by day)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Character):
        if a.get_class().get_name() != 'MarePerson':
            continue
        c = a.get_controller()
        st = str(c.get_move_status()) if isinstance(c, unreal.AIController) else '-'
        l = a.get_actor_location()
        out.append([a.get_editor_property('person_name') if hasattr(a, 'person_name') else a.get_name(), round(a.get_velocity().length()), st,
                    [round(l.x), round(l.y), round(l.z)], a.is_hidden_ed() if hasattr(a, 'is_hidden_ed') else None])
    return json.dumps(out[:40])


def nanite_of_instances(arg=''):
    """QA (PIE stopped): every instanced component of the level grouped by mesh: instance count, Nanite on, shadow,
    cull distances, material blend modes (what is drawn by the CPU-culled path)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    rows = {}
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            m = c.static_mesh
            if not m:
                continue
            k = m.get_path_name()
            r = rows.setdefault(k, [0, None, False, 0, set(), a.get_actor_label()[:30]])
            r[0] += c.get_instance_count()
            r[1] = bool(m.get_editor_property('nanite_settings').enabled)
            r[2] = r[2] or c.cast_shadow
            r[3] = c.get_editor_property('instance_end_cull_distance')
            for i in range(len(m.static_materials)):
                mi = c.get_material(i)
                if mi:
                    r[4].add(str(mi.get_blend_mode()).split('.')[-1][:12])
    out = sorted(([v[0], k.split('/')[-1], v[1], v[2], v[3], sorted(v[4]), v[5]] for k, v in rows.items()), reverse=True)
    return json.dumps(out[:60])


def mesh_info(arg=''):
    """QA: triangles (LOD0), LOD count and Nanite of meshes by path (comma separated)."""
    out = []
    for p in [x for x in arg.split(',') if x]:
        m = unreal.load_asset(p)
        if not m:
            out.append([p, 'missing'])
            continue
        out.append([m.get_name(), m.get_num_triangles(0), m.get_num_lods(), bool(m.get_editor_property('nanite_settings').enabled)])
    return json.dumps(out)


def primitives(arg=''):
    """QA (PIE stopped): census of the level's primitive components: per class, single static mesh components grouped by
    mesh (copies, Nanite, shadow, movable), and actors with many components (what a merge into instances would save)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    by_class, by_mesh, heavy = {}, {}, []
    n_actors = 0
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        n_actors += 1
        comps = a.get_components_by_class(unreal.PrimitiveComponent)
        if len(comps) > 40:
            heavy.append([a.get_actor_label()[:40], len(comps)])
        for c in comps:
            k = c.get_class().get_name()
            by_class[k] = by_class.get(k, 0) + 1
            if type(c) is unreal.StaticMeshComponent and c.static_mesh:
                m = c.static_mesh
                r = by_mesh.setdefault(m.get_name(), [0, bool(m.get_editor_property('nanite_settings').enabled), 0, 0])
                r[0] += 1
                r[2] += int(c.cast_shadow)
                r[3] += int(c.mobility != unreal.ComponentMobility.STATIC)
    top = sorted(([v[0], k, v[1], v[2], v[3]] for k, v in by_mesh.items()), reverse=True)
    single = sum(v[0] for v in by_mesh.values())
    repeated = sum(v[0] for v in by_mesh.values() if v[0] > 1)
    non_nanite = sum(v[0] for v in by_mesh.values() if not v[1])
    return json.dumps({'actors': n_actors, 'by_class': sorted(by_class.items(), key=lambda x: -x[1])[:12],
                       'static_mesh_components': single, 'in_meshes_used_2plus': repeated, 'non_nanite': non_nanite,
                       'distinct_meshes': len(by_mesh), 'top_meshes': top[:25], 'heavy_actors': sorted(heavy, key=lambda x: -x[1])[:15]})


def ism_census(arg=''):
    """QA (PIE stopped): instanced components (ISM, not HISM) grouped by mesh+materials+shadow: how many components and
    instances each group has (components of one group could be one component)."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    groups, sizes = {}, {}
    total = 0
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if isinstance(c, unreal.HierarchicalInstancedStaticMeshComponent) or not c.static_mesh:
                continue
            total += 1
            n = c.get_instance_count()
            sizes[min(n, 10)] = sizes.get(min(n, 10), 0) + 1
            mats = tuple(m.get_name() if m else '' for m in c.get_materials())
            key = (c.static_mesh.get_name(), mats, bool(c.cast_shadow), str(c.mobility).split('.')[-1], a.get_class().get_name())
            g = groups.setdefault(key, [0, 0, bool(c.static_mesh.get_editor_property('nanite_settings').enabled)])
            g[0] += 1
            g[1] += n
    multi = [(v[0], v[1], k[0], v[2], k[3], k[4]) for k, v in groups.items() if v[0] > 1]
    multi.sort(reverse=True)
    return json.dumps({'ism_components': total, 'instances_per_component': sorted(sizes.items()), 'groups': len(groups),
                       'components_in_shared_groups': sum(m[0] for m in multi), 'top': multi[:20]})


def volumes_at(arg='20413,62458,445'):
    """QA (PIE): post-process volumes (and their exposure overrides) that contain a point, unbound ones included."""
    x, y, z = [float(v) for v in arg.split(',')]
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() or \
        unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for v in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume):
        o, e = v.get_actor_bounds(False)
        inside = abs(x - o.x) <= e.x and abs(y - o.y) <= e.y and abs(z - o.z) <= e.z
        if v.unbound or inside:
            s = v.settings
            out.append([v.get_name(), v.unbound, v.priority, v.blend_weight, s.auto_exposure_min_brightness if s.override_auto_exposure_min_brightness else None,
                        s.auto_exposure_max_brightness if s.override_auto_exposure_max_brightness else None, s.auto_exposure_bias if s.override_auto_exposure_bias else None,
                        [round(o.x), round(o.y), round(e.x), round(e.y)]])
    return json.dumps(out)


def tagged(arg='MareIslandDebris'):
    """QA (PIE or editor): actors with a tag, their HISM components, instance counts, visibility and the mesh's Nanite."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() or unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if arg in [str(t) for t in a.tags]:
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                m = c.static_mesh
                out.append([a.get_name(), m.get_name() if m else None, c.get_instance_count(), c.is_visible(), bool(m and m.get_editor_property('nanite_settings').enabled),
                            [str(x.get_name()) if x else None for x in c.get_materials()][:3]])
    return json.dumps(out)


def bounds(arg=''):
    """QA: a mesh's bounding box (cm): origin and extent."""
    m = unreal.load_asset(arg)
    b = m.get_bounds()
    return json.dumps({'origin': [round(b.origin.x, 1), round(b.origin.y, 1), round(b.origin.z, 1)], 'extent': [round(b.box_extent.x, 1), round(b.box_extent.y, 1), round(b.box_extent.z, 1)]})


def posture(arg=''):
    """QA (PIE): forward lean of every person: angle (deg) of pelvis->head from vertical, of pelvis->spine_05 and of
    spine_05->head, plus speed and the playing pose (why villagers look hunched walking)."""
    import math
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    out = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
        rig = p.get_editor_property('mesh')
        try:
            pel, sp, nk, hd = [rig.get_socket_location(b) for b in ('pelvis', 'spine_05', 'neck_01', 'head')]
        except Exception:
            continue
        fwd = p.get_actor_forward_vector()

        def lean(a, b):
            v = b - a
            l = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z) or 1
            ang = math.degrees(math.acos(max(-1, min(1, v.z / l))))
            sign = 1 if (v.x * fwd.x + v.y * fwd.y) >= 0 else -1
            return round(ang * sign, 1)
        out.append([p.get_editor_property('person_name'), round(p.get_velocity().length()), lean(pel, hd), lean(pel, sp), lean(sp, hd), lean(nk, hd)])
    return json.dumps(out)
