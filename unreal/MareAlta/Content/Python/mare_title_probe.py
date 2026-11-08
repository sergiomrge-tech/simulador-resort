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
