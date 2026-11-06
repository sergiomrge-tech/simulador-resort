"""Night lighting audit (06/11/2026, Sergio: "a luz dos imóveis tem que vir das LÂMPADAS, não das paredes").
Entry through the MCP: hotel_lobby hud_module "mare_light_audit.<function>|<arg>".

lights(arg)  - every light actor of the editor level (or of the PIE world with arg 'pie'): label, class, tags,
               location, intensity, radius, and the nearest lamp-like mesh within 120 cm (a light with no fixture
               nearby is a "light from the walls"). -> D:/CodexTemp/lights/lights.json
"""
import json
from pathlib import Path

import unreal

OUT = Path(r'D:/CodexTemp/lights')
LAMPS = ('lamp', 'lantern', 'bulb', 'globe', 'pendant', 'chandelier', 'fan', 'luminaria', 'lustre', 'sconce', 'MeshInstance3D@3064',
         'MeshInstance3D@3086')


def _world(arg):
    if arg == 'pie':
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w:
            return w
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _lamp_points(world):
    pts = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        label = a.get_actor_label() if hasattr(a, 'get_actor_label') else a.get_name()
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if not m:
                continue
            name = m.get_name()
            if not any(k.lower() in (name + ' ' + label).lower() for k in LAMPS):
                continue
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                for i in range(c.get_instance_count()):
                    pts.append((c.get_instance_transform(i, True).translation, label + ' / ' + name))
            else:
                pts.append((c.get_world_location(), label + ' / ' + name))
    return pts


def lights(arg=''):
    world = _world(arg)
    lamps = _lamp_points(world)
    rows = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Light):
        c = a.light_component
        p = a.get_actor_location()
        near = None
        for q, what in lamps:
            d = (q - p).length()
            if d < 160 and (near is None or d < near[0]):
                near = (round(d), what)
        rows.append({'label': a.get_actor_label() if hasattr(a, 'get_actor_label') else a.get_name(), 'class': a.get_class().get_name(),
                     'tags': [str(t) for t in a.tags], 'at': [round(p.x), round(p.y), round(p.z)],
                     'intensity': round(c.intensity, 1),
                     'radius': round(c.get_editor_property('attenuation_radius')) if isinstance(c, unreal.LocalLightComponent) else None,
                     'hidden': a.is_hidden_ed() if arg != 'pie' else a.get_editor_property('hidden'), 'on': c.is_visible() and c.intensity > 0,
                     'tagsc': [str(t) for t in a.tags][:4], 'fixture': near})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'lights.json').write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding='utf-8')
    local = [r for r in rows if r['class'] not in ('DirectionalLight', 'SkyLight')]
    return json.dumps({'lights': len(rows), 'local': len(local), 'without_fixture': len([r for r in local if not r['fixture']]),
                       'file': str(OUT / 'lights.json')}, ensure_ascii=False)


def room(arg='4600,2100,150'):
    """Distances to the walls around a point (traces along +-X, +-Y, up and down): 'x,y,z'."""
    x, y, z = [float(v) for v in arg.split(',')]
    world = _world('pie')   # editor-world traces return nothing while PIE runs
    out = {}
    for name, d in (('+x', (1, 0, 0)), ('-x', (-1, 0, 0)), ('+y', (0, 1, 0)), ('-y', (0, -1, 0)), ('up', (0, 0, 1)), ('down', (0, 0, -1))):
        end = unreal.Vector(x + d[0] * 3000, y + d[1] * 3000, z + d[2] * 3000)
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, z), end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                     True, [], unreal.DrawDebugTrace.NONE, True)
        if hit:
            t = hit.to_tuple()
            out[name] = [round(t[4].x), round(t[4].y), round(t[4].z), t[9].get_actor_label() if t[9] else None]
    return json.dumps(out, ensure_ascii=False)


def mats(arg):
    """Material slots of meshes (paths or World_NNNN names separated by ';'): slot name, material, parent, blend mode."""
    out = {}
    for path in arg.split(';'):
        if path.startswith('World_'):
            path = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data/imported_meshes.json').read_text(encoding='utf-8-sig')).get(path, path)
        m = unreal.load_asset(path)
        if not m:
            out[path] = None
            continue
        rows = []
        for sm in m.static_materials:
            mi = sm.material_interface
            parent = mi.get_editor_property('parent') if isinstance(mi, unreal.MaterialInstance) else None
            base = mi.get_base_material() if mi else None
            rows.append([str(sm.material_slot_name), mi.get_path_name() if mi else None, parent.get_path_name() if parent else None,
                         str(base.get_editor_property('blend_mode')) if base else None])
        b = m.get_bounds()
        out[path] = {'slots': rows, 'bounds_origin': [round(b.origin.x), round(b.origin.y), round(b.origin.z)],
                     'extent': [round(b.box_extent.x), round(b.box_extent.y), round(b.box_extent.z)]}
    return json.dumps(out, ensure_ascii=False)


def ray(arg):
    """Meshes whose instance bounds a view ray crosses (finds thin things without collision, e.g. a wire across the
    camera): 'x,y,z,pitch,yaw[,max_cm]' from the eye. PIE world when running. Nearest first."""
    import math
    v = [float(t) for t in arg.split(',')]
    x, y, z, pitch, yaw = v[:5]
    reach = v[5] if len(v) > 5 else 3000
    biggest = v[6] if len(v) > 6 else 5000   # skip instances whose bounds diagonal is larger (cm)
    d = unreal.Vector(math.cos(math.radians(pitch)) * math.cos(math.radians(yaw)), math.cos(math.radians(pitch)) * math.sin(math.radians(yaw)),
                      math.sin(math.radians(pitch)))
    o = unreal.Vector(x, y, z)
    world = _world('pie')
    hits = []

    def slab(lo, hi):
        t0, t1 = 0.0, reach
        for k in ('x', 'y', 'z'):
            ok, dk, lk, hk = getattr(o, k), getattr(d, k), getattr(lo, k), getattr(hi, k)
            if abs(dk) < 1e-6:
                if ok < lk or ok > hk:
                    return None
                continue
            a, b = (lk - ok) / dk, (hk - ok) / dk
            if a > b:
                a, b = b, a
            t0, t1 = max(t0, a), min(t1, b)
            if t0 > t1:
                return None
        return t0

    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if a.get_editor_property('hidden'):
            continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if not m or not c.is_visible():
                continue
            b = m.get_bounds()
            ts = [c.get_instance_transform(i, True) for i in range(c.get_instance_count())] if isinstance(c, unreal.InstancedStaticMeshComponent) else [c.get_world_transform()]
            for i, t in enumerate(ts):
                pts = [t.transform_location(b.origin + unreal.Vector(sx * b.box_extent.x, sy * b.box_extent.y, sz * b.box_extent.z))
                       for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
                lo = unreal.Vector(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))
                hi = unreal.Vector(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
                if (hi - lo).length() > biggest:
                    continue
                hit = slab(lo, hi)
                if hit is not None:
                    hits.append([round(hit), a.get_name(), a.get_actor_label() if hasattr(a, 'get_actor_label') else '', m.get_name(), i,
                                 [round(lo.x), round(lo.y), round(lo.z)], [round(hi.x - lo.x), round(hi.y - lo.y), round(hi.z - lo.z)]])
    hits.sort()
    return json.dumps(hits[:40], ensure_ascii=False)


def hide(arg):
    """PIE only, for identification shots: 'Actor_1,Actor_2[=0]' hides (or with =0 shows) actors by object name."""
    world = _world('pie')
    done = []
    for item in arg.split(','):
        name, _, flag = item.partition('=')
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            if a.get_name() == name:
                a.set_actor_hidden_in_game(flag != '0')
                done.append([name, a.get_actor_label(), flag != '0'])
    return json.dumps(done, ensure_ascii=False)


def ray_any(arg):
    """Like ray, but every primitive component (cables, splines, skeletal meshes...) by its world bounds; skips the
    instanced ones (ray covers them per instance) and anything over 50 m. 'x,y,z,pitch,yaw[,max_cm]'."""
    import math
    v = [float(t) for t in arg.split(',')]
    x, y, z, pitch, yaw = v[:5]
    reach = v[5] if len(v) > 5 else 3000
    d = (math.cos(math.radians(pitch)) * math.cos(math.radians(yaw)), math.cos(math.radians(pitch)) * math.sin(math.radians(yaw)),
         math.sin(math.radians(pitch)))
    o = (x, y, z)
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(_world('pie'), unreal.Actor):
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            if isinstance(c, unreal.InstancedStaticMeshComponent) or not c.is_visible():
                continue
            origin, ext, _ = unreal.SystemLibrary.get_component_bounds(c)
            if max(ext.x, ext.y, ext.z) > (v[6] if len(v) > 6 else 2500):
                continue
            lo = (origin.x - ext.x, origin.y - ext.y, origin.z - ext.z)
            hi = (origin.x + ext.x, origin.y + ext.y, origin.z + ext.z)
            t0, t1, ok = 0.0, reach, True
            for k in range(3):
                if abs(d[k]) < 1e-6:
                    if not lo[k] <= o[k] <= hi[k]:
                        ok = False
                    continue
                p0, p1 = sorted(((lo[k] - o[k]) / d[k], (hi[k] - o[k]) / d[k]))
                t0, t1 = max(t0, p0), min(t1, p1)
            if ok and t0 <= t1:
                out.append([round(t0), a.get_name(), a.get_actor_label() if hasattr(a, 'get_actor_label') else '', c.get_class().get_name(),
                            c.get_name(), [round(2 * ext.x), round(2 * ext.y), round(2 * ext.z)]])
    out.sort()
    return json.dumps(out[:40], ensure_ascii=False)


def eye(arg=''):
    """PIE camera location and rotation (for ray/ray_any)."""
    cam = unreal.GameplayStatics.get_player_camera_manager(_world('pie'), 0)
    p, r = cam.get_camera_location(), cam.get_camera_rotation()
    return json.dumps({'at': [round(p.x, 1), round(p.y, 1), round(p.z, 1)], 'pitch': round(r.pitch, 2), 'yaw': round(r.yaw, 2), 'fov': cam.get_fov_angle()})


def glow(arg=''):
    """Lamp globes glow when the lamp is lit (06/11, CHECKLIST 0: "globo das luminárias não brilha quando a luz acende"):
    'mesh:slot ...' (World_NNNN names or asset paths) -> that slot gets M_LampGlow_PBR (frosted warm glass by day,
    emissive with MPC_MareTime.Night). Saved with the PIE stopped (CLAUDE.md 03/11). Re-executable."""
    mapping = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data/imported_meshes.json').read_text(encoding='utf-8-sig'))
    mat = unreal.load_asset('/Game/World/Materials/M_LampGlow_PBR')
    out = []
    for spec in arg.split():
        name, _, slot = spec.rpartition(':')
        mesh = unreal.load_asset(mapping.get(name, name))
        if not mesh:
            out.append([spec, 'missing'])
            continue
        mesh.set_material(int(slot), mat)
        out.append([spec, unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)])
    return json.dumps(out)

def near(arg):
    """Meshes (components and instances) within r cm of a point: 'x,y,z,r[,1]' (PIE world when running; a 5th value 1
    skips hidden actors). Nearest first."""
    vals = [float(v) for v in arg.split(',')]
    x, y, z, r = vals[:4]
    visible_only = len(vals) > 4 and vals[4] > 0
    p = unreal.Vector(x, y, z)
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(_world('pie'), unreal.Actor):
        if visible_only and a.get_editor_property('hidden'):
            continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if not m:
                continue
            ts = [c.get_instance_transform(i, True) for i in range(c.get_instance_count())] if isinstance(c, unreal.InstancedStaticMeshComponent) else [c.get_world_transform()]
            for t in ts:
                d = (t.translation - p).length()
                if d < r:
                    q = t.translation
                    out.append([round(d), a.get_actor_label() if hasattr(a, 'get_actor_label') else a.get_name(), m.get_name(), [round(q.x), round(q.y), round(q.z)],
                                a.get_editor_property('hidden')])
    out.sort()
    return json.dumps(out[:60], ensure_ascii=False)


def fix_level(arg=''):
    """06/11, CHECKLIST 0 (light only from fixtures). Editor level, PIE stopped. Re-executable:
    - removes the six bare 'Hotel lobby · luz' point lights (the lobby's ceiling lamps light it: MareVisualWorld::BuildLamps);
    - tags MareBareLight the practical point lights with no fixture (bungalow ceilings at z 290, the pousada reception
      light by the door at 0,1400,290): day fill only, off at night;
    - the lobby lamp globe gets the night glow material.
    'dry' only reports."""
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    removed, tagged = [], []
    for a in actors.get_all_level_actors():
        if not isinstance(a, unreal.PointLight):
            continue
        label, p, tags = a.get_actor_label(), a.get_actor_location(), [str(t) for t in a.tags]
        if label == 'Hotel lobby · luz':
            removed.append([round(p.x), round(p.y)])
            if arg != 'dry':
                actors.destroy_actor(a)
            continue
        bungalow_ceiling = 'MareHomeLight' in tags and 'MareInteriorPart' in tags and p.z > 250
        pousada_door = label == 'Pousada recepção · luz' and abs(p.x) < 5 and abs(p.y - 1400) < 5
        if (bungalow_ceiling or pousada_door) and 'MareBareLight' not in tags:
            tagged.append([label, round(p.x), round(p.y), round(p.z)])
            if arg != 'dry':
                a.tags = list(a.tags) + [unreal.Name('MareBareLight')]
    glow_done = None
    if arg != 'dry':
        glow_done = glow('/Game/Hotel/Lobby/modern_ceiling_lamp_01/modern_ceiling_lamp_011:2')
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'removed': removed, 'tagged': tagged, 'glow': glow_done}, ensure_ascii=False)


def volumes(arg=''):
    """Post-process volumes: label, tags, unbound, bounds, priority, exposure overrides."""
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(_world(arg), unreal.PostProcessVolume):
        o, e = a.get_actor_bounds(False)
        s = a.settings
        out.append([a.get_actor_label() if hasattr(a, 'get_actor_label') else a.get_name(), [str(t) for t in a.tags], a.unbound, a.priority,
                    [round(o.x), round(o.y), round(o.z)], [round(e.x), round(e.y), round(e.z)],
                    [s.auto_exposure_min_brightness if s.override_auto_exposure_min_brightness else None,
                     s.auto_exposure_max_brightness if s.override_auto_exposure_max_brightness else None,
                     s.auto_exposure_bias if s.override_auto_exposure_bias else None]])
    return json.dumps(out, ensure_ascii=False)


def house_volume(arg=''):
    """06/11: the player's house gets a MareInterior post-process volume like the lobby, suite and bungalows (one night eye
    for every room, MareVisualWorld mare.InteriorNightEV). Inner walls measured with room(): x 4263..4933, y 1432..2437,
    floor 12, ceiling 319. Editor level, PIE stopped; re-executable (replaces 'Interior · casa')."""
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    template = None
    for a in actors.get_all_level_actors():
        if isinstance(a, unreal.PostProcessVolume):
            if a.get_actor_label() == 'Interior · casa':
                actors.destroy_actor(a)
            elif a.get_actor_label() == 'Interior · lobby':
                template = a
    lo, hi = unreal.Vector(4263, 1432, 12), unreal.Vector(4933, 2437, 319)
    centre, ext = (lo + hi) * .5, (hi - lo) * .5
    v = actors.duplicate_actor(template)
    v.set_actor_label('Interior · casa')
    v.tags = [unreal.Name('MareInterior'), unreal.Name('MareInteriorPart')]
    o, e = template.get_actor_bounds(False)
    s = template.get_actor_scale3d()
    v.set_actor_scale3d(unreal.Vector(s.x * ext.x / e.x, s.y * ext.y / e.y, s.z * ext.z / e.z))
    v.set_actor_location(centre, False, False)
    o2, e2 = v.get_actor_bounds(False)
    v.set_actor_location(centre + (centre - o2), False, False)
    o2, e2 = v.get_actor_bounds(False)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'bounds_origin': [round(o2.x), round(o2.y), round(o2.z)], 'extent': [round(e2.x), round(e2.y), round(e2.z)]})


def hero_parts(arg=''):
    """Components of the player pawn: class, name, mesh, visible, world location, attach parent/socket."""
    hero = unreal.GameplayStatics.get_player_pawn(_world('pie'), 0)
    out = []
    for c in hero.get_components_by_class(unreal.PrimitiveComponent):
        m = c.static_mesh.get_path_name() if isinstance(c, unreal.StaticMeshComponent) and c.static_mesh else (c.skeletal_mesh_asset.get_name() if isinstance(c, unreal.SkeletalMeshComponent) and c.skeletal_mesh_asset else None)
        p = c.get_world_location()
        out.append([c.get_class().get_name(), c.get_name(), m, c.is_visible(), [round(p.x), round(p.y), round(p.z)],
                    c.get_attach_parent().get_name() if c.get_attach_parent() else None, str(c.get_attach_socket_name())])
    return json.dumps(out, ensure_ascii=False)


def actor_info(arg):
    """'Name1,Name2': object name -> label, class, tags, location, meshes, hidden (PIE world)."""
    out = {}
    names = arg.split(',')
    for a in unreal.GameplayStatics.get_all_actors_of_class(_world('pie'), unreal.Actor):
        if a.get_name() in names:
            p = a.get_actor_location()
            out[a.get_name()] = {'label': a.get_actor_label() if hasattr(a, 'get_actor_label') else '', 'class': a.get_class().get_name(),
                                 'tags': [str(t) for t in a.tags], 'at': [round(p.x), round(p.y), round(p.z)], 'hidden': a.get_editor_property('hidden'),
                                 'meshes': [[c.get_name(), c.static_mesh.get_path_name() if c.static_mesh else None, c.is_visible(),
                                             [str(m.get_path_name()) if m else None for m in c.get_materials()]]
                                            for c in a.get_components_by_class(unreal.StaticMeshComponent)]}
    return json.dumps(out, ensure_ascii=False)


def hero_hide(arg):
    """PIE: 'Hair_SimpleParted,Hair_Beard[=0]' hides (=0 shows) the player's static mesh parts by mesh name."""
    hero = unreal.GameplayStatics.get_player_pawn(_world('pie'), 0)
    names, _, flag = arg.partition('=')
    done = []
    for c in hero.get_components_by_class(unreal.StaticMeshComponent):
        if c.static_mesh and c.static_mesh.get_name() in names.split(','):
            c.set_visibility(flag != '0')
            done.append([c.get_name(), c.static_mesh.get_name(), flag != '0'])
    return json.dumps(done)


def bare_check(arg=''):
    """QA gate (06/11, CHECKLIST 0: "a iluminação dos imóveis precisa ser das lâmpadas"): editor-level point/spot lights that
    shine at night without a fixture. Allowed: rectangular panels (day fill, off at night), tags MareBareLight and
    MareSuitePart (day fill, off at night: MareVisualWorld), a lamp-like mesh within 160 cm, and the bungalow bedside
    lamps (modelled inside mare_bungalow, lights under 2 m within 3 m of its pivot). Returns the offenders."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    lamps = _lamp_points(world)
    bungalows = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if c.static_mesh and c.static_mesh.get_name() == 'mare_bungalow':
                ts = [c.get_instance_transform(i, True) for i in range(c.get_instance_count())] if isinstance(c, unreal.InstancedStaticMeshComponent) else [c.get_world_transform()]
                bungalows += [t.translation for t in ts]
    bad = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Light):
        if not isinstance(a, (unreal.PointLight, unreal.SpotLight)):
            continue
        tags = [str(t) for t in a.tags]
        if 'MareBareLight' in tags or 'MareSuitePart' in tags:
            continue
        p = a.get_actor_location()
        if any((q - p).length() < 160 for q, _ in lamps):
            continue
        if p.z < 200 and any((b - p).length() < 300 for b in bungalows):
            continue
        bad.append([a.get_actor_label(), round(p.x), round(p.y), round(p.z)])
    return json.dumps({'bare': bad, 'pass': not bad}, ensure_ascii=False)
