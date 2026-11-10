"""Vegetation on the surrounding hills: CC0 Poly Haven trees/shrubs placed on real terrain hits.

Survey first (grid of downward traces), then populate slopes above the village/beach band,
outside buildings and routes. Instances are non-colliding HISMs with distance culling."""
import json
import math
import random
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
DATA = ROOT / 'Content/Data'
LIB = Path('D:/Assets/PolyHaven')
LABEL = 'Mare · Vegetação das montanhas'


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _terrain_actor():
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label() == 'Maré · Ground':
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                return a, c
    return None, None


def _hit(world, x, y, ignore):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 20000), unreal.Vector(x, y, -2000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore, unreal.DrawDebugTrace.NONE, True)
    if not hit:
        return None
    t = hit.to_tuple()
    return t[4], t[7], t[9]   # impact point, impact normal, actor


def survey(step=1000):
    world = _world()
    actor, comp = _terrain_actor()
    if not actor:
        raise RuntimeError('terrain not found')
    origin, extent = actor.get_actor_bounds(False)
    lo, hi = origin - extent, origin + extent
    rows = []
    x = lo.x
    while x <= hi.x:
        y = lo.y
        while y <= hi.y:
            h = _hit(world, x, y, [])
            if h and h[2] == actor:
                rows.append([round(x), round(y), round(h[0].z), round(h[1].z, 3)])
            y += step
        x += step
    zs = sorted(r[2] for r in rows)
    hist = {f'>{t}': sum(1 for z in zs if z > t) for t in (200, 500, 1000, 2000, 4000)}
    out = {'terrain': actor.get_actor_label(), 'mesh': comp.static_mesh.get_path_name(), 'bounds': [[lo.x, lo.y, lo.z], [hi.x, hi.y, hi.z]],
           'samples': len(rows), 'height_hist': hist, 'max_z': zs[-1] if zs else None}
    (Path('D:/CodexTemp/mountains')).mkdir(parents=True, exist_ok=True)
    Path('D:/CodexTemp/mountains/survey.json').write_text(json.dumps({'summary': out, 'rows': rows}), encoding='utf-8')
    return out


def big_actors(min_extent=4000):
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        o, e = a.get_actor_bounds(False)
        if max(e.x, e.y) > min_extent and e.z > 300:
            meshes = sorted({c.static_mesh.get_name() for c in a.get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh})
            out.append({'label': a.get_actor_label(), 'origin': [round(o.x), round(o.y), round(o.z)], 'extent': [round(e.x), round(e.y), round(e.z)], 'meshes': meshes[:4], 'tags': [str(x) for x in a.tags][:3]})
    return out


REGION = (-34000, 42000, -20000, 72000)  # x0, x1, y0, y1 (cm): hills and headlands around the village
MIN_Z = 600                               # above the village/beach ground
# slug, weight, scale range, cull distance (0 = never), casts shadow
# Backdrop hills are seen from 150-400 m: trees are scaled up so the canopy reads as forest.
# The Poly Haven island_tree_0x are stylised low-poly (big flat leaf facets): replaced by the realistic
# Fab HighPoly Tree (Next Spring, CC BY 4.0) already fitted to the village almond variants.
TREES = [('World_0504', 3, (.8, 1.25)), ('World_0505', 3, (.8, 1.25)), ('World_1206', 2, (.8, 1.2)),
         ('tree_small_02', 2, (1.8, 2.6)), ('jacaranda_tree', 1, (1.3, 1.8))]
# Poly Haven CC0 rocks; the range is the target size in metres (the scale is derived per mesh).
ROCKS = [('rock_face_01', 2, (4.0, 9.0)), ('rock_face_02', 2, (4.0, 9.0)), ('coast_rocks_01', 2, (2.5, 6.0)),
         ('coast_rocks_02', 2, (2.5, 6.0)), ('coast_rocks_05', 2, (2.0, 5.0)), ('coast_rocks_03', 1, (6.0, 12.0))]
UNDER = [('shrub_01', 3, (2.0, 3.0)), ('shrub_02', 3, (2.0, 3.0)), ('shrub_03', 2, (2.0, 2.8)), ('shrub_04', 2, (2.0, 2.8)), ('fern_02', 2, (2.0, 3.0))]
MAX_SLOPE_NZ = 0.60
# 04/11 (Sergio: "tem muitas", photo of the hill behind the kiosk as one dark speckled carpet; the trees' shadows also
# cost ~5 FPS on the beach): trees every 5.6 m instead of 4.2, shrubs every 4.6 m instead of 3.6, and soft clearings
# (CLEARING of the hill without trees, in patches ~30 m across) so the slope reads as woods and open ground.
TREE_STEP, UNDER_STEP, CLEARING = 560, 460, .22


def _clearing(x, y, seed):
    """Smooth value noise in 0..1 with ~30 m cells: below CLEARING the spot is a clearing (no tree)."""
    def rnd(i, j):
        return random.Random(hash((i, j, seed)) & 0xffffffff).random()
    cell = 3000.0
    gx, gy = x / cell, y / cell
    i, j = math.floor(gx), math.floor(gy)
    fx, fy = gx - i, gy - j
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = rnd(i, j), rnd(i + 1, j), rnd(i, j + 1), rnd(i + 1, j + 1)
    return (a + (b - a) * sx) + ((c + (d - c) * sx) - (a + (b - a) * sx)) * sy


def _mesh(slug):
    if slug.startswith('World_'):
        mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
        return unreal.load_asset(mapping[slug])
    dest = '/Game/Nature/Mountain/' + slug
    found = [unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(dest, recursive=True)] if unreal.EditorAssetLibrary.does_directory_exist(dest) else []
    found = [m for m in found if isinstance(m, unreal.StaticMesh)]
    if found:
        return found[0]
    import mare_hotel_lobby
    info = json.loads((LIB / slug / 'info.json').read_text(encoding='utf-8'))
    mesh = mare_hotel_lobby._import(LIB / slug / info['gltf'], dest, slug, True)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    # 08/11: the import turns Nanite on, but its materials lacked the usage flag: the cooked game drew the default
    # checker (packaged QA). Flag them right away.
    import mare_boat_tour
    mare_boat_tour.fix_usage(dest)
    return mesh


def _pick(rng, table):
    total = sum(w for _, w, _ in table)
    r = rng.uniform(0, total)
    for slug, w, scale in table:
        r -= w
        if r <= 0:
            return slug, scale
    return table[-1][0], table[-1][2]


def populate(seed=20261101):
    world = _world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if a.get_actor_label() == LABEL:
            actors.destroy_actor(a)
    # Only the backdrop hill tiles (tall terrain chunks) and the ground mesh may receive plants.
    hills = set()
    for a in actors.get_all_level_actors():
        label = a.get_actor_label()
        if label == 'Maré · Ground' or label.startswith('Maré · Preenchimento costeiro') or (label.startswith('Maré · @MeshInstance3D') and a.get_actor_bounds(False)[1].z > 1500):
            hills.add(label)
    rng = random.Random(seed)
    placements = {}
    rejected = {'miss': 0, 'low': 0, 'steep': 0}
    x0, x1, y0, y1 = REGION
    rejected['clearing'] = 0
    for layer, table, step, jitter in (('tree', TREES, TREE_STEP, 240), ('under', UNDER, UNDER_STEP, 190)):
        x = x0
        while x <= x1:
            y = y0
            while y <= y1:
                px, py = x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter)
                h = _hit(world, px, py, [])
                if not h or not h[2] or h[2].get_actor_label() not in hills:
                    rejected['miss'] += 1
                elif h[0].z < MIN_Z:
                    rejected['low'] += 1
                elif h[1].z < MAX_SLOPE_NZ:
                    rejected['steep'] += 1
                elif layer == 'tree' and _clearing(px, py, seed) < CLEARING:
                    rejected['clearing'] += 1
                else:
                    slug, (s0, s1) = _pick(rng, table)
                    s = rng.uniform(s0, s1)
                    placements.setdefault(slug, []).append((h[0].x, h[0].y, h[0].z - 15, rng.uniform(-180, 180), s))
                y += step
            x += step
    # Rocks: more on steep ground, never in the water or on flat lawn.
    rocks = {}
    x = x0
    while x <= x1:
        y = y0
        while y <= y1:
            px, py = x + rng.uniform(-300, 300), y + rng.uniform(-300, 300)
            h = _hit(world, px, py, [])
            if h and h[2] and h[2].get_actor_label() in hills and h[0].z > 80 and .3 < h[1].z < .97:
                if rng.random() < .3 + .7 * (.97 - h[1].z) / .67:
                    # Outcrops come in groups: one big rock and a few smaller ones around it.
                    for k in range(rng.choice((1, 2, 3, 3, 4))):
                        qx, qy = (px, py) if k == 0 else (px + rng.uniform(-350, 350), py + rng.uniform(-350, 350))
                        q = _hit(world, qx, qy, []) if k else h
                        if not q or not q[2] or q[2].get_actor_label() not in hills or q[0].z < 60:
                            continue
                        slug, (a, b) = _pick(rng, ROCKS)
                        rocks.setdefault(slug, []).append((q[0].x, q[0].y, q[0].z, rng.uniform(-180, 180), rng.uniform(a, b) * 100 * (1 if k == 0 else .55),
                                                           rng.uniform(-12, 12), rng.uniform(-12, 12)))
            y += 600
        x += 600
    root = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector())
    root.set_actor_label(LABEL)
    root.tags = [unreal.Name('MareGenerated'), unreal.Name('MareMountainVegetation')]
    root.set_folder_path('Nature/Mountains')
    from editor_toolset.toolsets.actor import ActorTools
    summary = {}
    for slug, rows in placements.items():
        mesh = _mesh(slug)
        comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_' + slug)
        comp.set_static_mesh(mesh)
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        tree = any(slug == t[0] for t in TREES)
        comp.set_editor_property('cast_shadow', tree)
        if not tree:
            comp.set_editor_property('instance_end_cull_distance', 16000)
            comp.set_editor_property('instance_start_cull_distance', 12000)
        b = mesh.get_bounds()
        base = b.origin.z - b.box_extent.z
        transforms = [unreal.Transform(unreal.Vector(x, y, z - base * s), unreal.Rotator(roll=0, pitch=0, yaw=yaw), unreal.Vector(s, s, s)) for x, y, z, yaw, s in rows]
        comp.add_instances(transforms, False, True)
        summary[slug] = len(rows)
    for slug, rows in rocks.items():
        mesh = _mesh(slug)
        comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_' + slug)
        comp.set_static_mesh(mesh)
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_editor_property('cast_shadow', True)
        b = mesh.get_bounds()
        span = 2 * max(b.box_extent.x, b.box_extent.y)
        base = b.origin.z - b.box_extent.z
        transforms = []
        for x, y, z, yaw, size, pitch, roll in rows:
            s = size / span
            # Bedded a quarter of its height into the slope so it reads as outcrop, not a pebble on top.
            transforms.append(unreal.Transform(unreal.Vector(x, y, z - base * s - .25 * 2 * b.box_extent.z * s),
                                               unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw), unreal.Vector(s, s, s)))
        comp.add_instances(transforms, False, True)
        summary[slug] = len(rows)
    seated = json.loads(seat_rocks('apply'))   # beds the rocks in the slope and saves the level
    seated['trunks'] = json.loads(clear_trunks('apply'))   # no tree growing out of a rock
    report = {'region': REGION, 'min_z': MIN_Z, 'seed': seed, 'instances': summary, 'seated': seated, 'total': sum(summary.values()), 'rejected': rejected}
    (DATA / 'mountain_vegetation.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    return report


TERRAIN = ('Maré · @MeshInstance3D', 'Maré · Ground', 'Maré · Preenchimento costeiro', 'Ilha · terreno novo', 'Mar · fundo')
TRAILS = 'Ilha · trilhas'
SEAT_POINTS = ((.5, .5), (.2, .2), (.8, .2), (.8, .8), (.2, .8))


def _seat(world, t, box, ignore, sink=.35):
    """Beds one rock in the slope. 09/11, Sergio: "rochas flutuando": the rocks were tilted at random (±12°) and sunk a
    quarter of their height whatever the slope, so on 45–60° hillsides the downhill corners of wide slabs hung metres
    in the air. Here the rock takes the plane of the ground under its own footprint (flat slabs fully, tall boulders
    60%), keeps yaw and size, sinks `sink` of its height along the normal and is then lowered until no footprint
    sample has air under it. Returns (transform, state): state 'ok', 'trail' (sits on a path), 'buried' (bedding it
    hides it), 'other' (not on terrain: left alone, transform None)."""
    ml = unreal.MathLibrary
    s = t.scale3d
    cx, cy = (box.min.x + box.max.x) / 2, (box.min.y + box.max.y) / 2
    wx, wy, h = (box.max.x - box.min.x) * s.x, (box.max.y - box.min.y) * s.y, (box.max.z - box.min.z) * s.z
    p0 = ml.transform_location(t, unreal.Vector(cx, cy, box.min.z))

    def ground(x, y):
        g = _hit(world, x, y, ignore)
        if not g or not g[2]:
            return None
        label = g[2].get_actor_label()
        if label.startswith(TRAILS):
            return 'trail'
        return (g[0].z, g[1]) if label.startswith(TERRAIN) else None

    g0 = ground(p0.x, p0.y)
    if g0 == 'trail':
        return None, 'trail'
    if not g0:
        return None, 'other'
    yaw = math.radians(t.rotation.rotator().yaw)
    fx, fy = math.cos(yaw), math.sin(yaw)
    pts = []
    for ax, ay in ((1, 1), (-1, -1), (-1, 1), (1, -1)):
        dx, dy = ax * .3 * wx, ay * .3 * wy
        x, y = p0.x + dx * fx - dy * fy, p0.y + dx * fy + dy * fx
        g = ground(x, y)
        if g == 'trail':
            return None, 'trail'
        pts.append(unreal.Vector(x, y, g[0]) if g else None)
    n = g0[1]
    if all(pts):
        c = ml.cross_vector_vector(pts[0] - pts[1], pts[2] - pts[3])
        if c.z < 0:
            c = c * -1
        if c.length() > 1 and c.z / c.length() > .15:
            n = c / c.length()
    k = 1.0 if h < .25 * min(wx, wy) else .6          # a tall boulder leaning 50° with the slope looks toppled
    n = unreal.Vector(n.x * k, n.y * k, n.z * k + (1 - k))
    n = n / n.length()
    fwd = unreal.Vector(fx, fy, 0)
    d = fwd.x * n.x + fwd.y * n.y
    rot = ml.make_rot_from_zx(n, unreal.Vector(fwd.x - n.x * d, fwd.y - n.y * d, -n.z * d))
    depth = max(4.0, sink * h)
    target = unreal.Vector(p0.x - n.x * depth, p0.y - n.y * depth, g0[0] - n.z * depth)
    off = ml.transform_location(unreal.Transform(unreal.Vector(), rot, s), unreal.Vector(cx, cy, box.min.z))
    new = unreal.Transform(target - off, rot, s)
    worst = 0.0
    for u, v in SEAT_POINTS:
        p = ml.transform_location(new, unreal.Vector(box.min.x + (box.max.x - box.min.x) * u, box.min.y + (box.max.y - box.min.y) * v, box.min.z))
        g = ground(p.x, p.y)
        if g == 'trail':
            return None, 'trail'
        if g:
            worst = max(worst, p.z - g[0])
    if worst > 3:
        new = unreal.Transform(target - off - unreal.Vector(0, 0, worst - 3), rot, s)
    top = ml.transform_location(new, unreal.Vector(cx, cy, box.max.z))
    g = ground(top.x, top.y)
    if g and g != 'trail' and top.z - g[0] < .22 * h * n.z:
        return None, 'buried'
    return new, 'ok'


def seat_rocks(arg='dry'):
    """'dry' | 'apply' [':' label ['!' only rocks whose footprint floats more than 30 cm]]: beds every rock instance of
    the actor (default: the mountain vegetation) with `_seat`; rocks on a trail or that bedding would hide are
    removed. Run with the PIE stopped; 'apply' saves the level."""
    mode, _, rest = arg.partition(':')
    label, only_floating = (rest[:-1], True) if rest.endswith('!') else (rest or LABEL, False)
    world = _world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ignore = [a for a in actors.get_all_level_actors() if a.get_actor_label() in (LABEL, 'Ilha · rochas da costa')]
    ml = unreal.MathLibrary
    out = {}
    for a in ignore:
        if a.get_actor_label() != label:
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            m = c.static_mesh
            if not m or 'rock' not in m.get_name().lower():
                continue
            box = m.get_bounding_box()
            stat = {'n': c.get_instance_count(), 'ok': 0, 'trail': 0, 'buried': 0, 'other': 0, 'skipped': 0, 'tilt': []}
            moves, drop = [], []
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                if only_floating:
                    gap = 0.0
                    for u, v in SEAT_POINTS:
                        p = ml.transform_location(t, unreal.Vector(box.min.x + (box.max.x - box.min.x) * u, box.min.y + (box.max.y - box.min.y) * v, box.min.z))
                        g = _hit(world, p.x, p.y, ignore)
                        if g:
                            gap = max(gap, p.z - g[0].z)
                    if gap <= 30:
                        stat['skipped'] += 1
                        continue
                new, state = _seat(world, t, box, ignore)
                stat[state] += 1
                if state == 'ok':
                    moves.append((i, new))
                    up = ml.get_up_vector(new.rotation.rotator())
                    stat['tilt'].append(round(math.degrees(math.acos(max(-1.0, min(1.0, up.z))))))
                elif state in ('trail', 'buried'):
                    drop.append(i)
            tilt = sorted(stat.pop('tilt'))
            stat['tilt_med'] = tilt[len(tilt) // 2] if tilt else None
            stat['tilt_max'] = tilt[-1] if tilt else None
            if mode == 'apply':
                for j, (i, new) in enumerate(moves):
                    c.update_instance_transform(i, new, True, j == len(moves) - 1, True)
                for i in sorted(drop, reverse=True):
                    c.remove_instance(i)
                stat['left'] = c.get_instance_count()
            out[m.get_name()] = stat
    if mode == 'apply':
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out, ensure_ascii=False)


def clear_trunks(arg='dry'):
    """'dry' | 'apply': removes the trees whose trunk comes up through a rock (09/11, photo of the west slope: a trunk
    growing out of the middle of a flat slab). A tree counts when its base falls inside the central 70% of a rock's
    footprint and below the rock's top. The rock stays (outcrops are rarer than trees). PIE stopped; 'apply' saves."""
    ml = unreal.MathLibrary
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    root = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == LABEL), None)
    if not root:
        return json.dumps({'error': 'no actor'})
    tree_names = set()
    for slug, _, _ in TREES:
        m = _mesh(slug)
        if m:
            tree_names.add(m.get_name())
    comps = root.get_components_by_class(unreal.InstancedStaticMeshComponent)
    cell = 1000.0
    grid = {}
    for c in comps:
        m = c.static_mesh
        if not m or m.get_name() not in tree_names:
            continue
        for i in range(c.get_instance_count()):
            p = c.get_instance_transform(i, True).translation
            grid.setdefault((int(p.x // cell), int(p.y // cell)), []).append((c, i, p))
    hit = {}
    rocks = 0
    for c in comps:
        m = c.static_mesh
        if not m or 'rock' not in m.get_name().lower():
            continue
        box = m.get_bounding_box()
        dx, dy = box.max.x - box.min.x, box.max.y - box.min.y
        for i in range(c.get_instance_count()):
            t = c.get_instance_transform(i, True)
            r = .5 * max(dx * t.scale3d.x, dy * t.scale3d.y)
            inv = t.inverse()
            found = False
            for gx in range(int((t.translation.x - r) // cell), int((t.translation.x + r) // cell) + 1):
                for gy in range(int((t.translation.y - r) // cell), int((t.translation.y + r) // cell) + 1):
                    for tc, ti, p in grid.get((gx, gy), ()):
                        q = ml.transform_location(inv, p)
                        if (box.min.x + .15 * dx < q.x < box.max.x - .15 * dx and box.min.y + .15 * dy < q.y < box.max.y - .15 * dy
                                and q.z < box.max.z):
                            hit.setdefault(tc, set()).add(ti)
                            found = True
            rocks += found
    out = {'rocks_with_trunk': rocks, 'trees': {c.static_mesh.get_name(): len(v) for c, v in hit.items()}}
    if arg == 'apply':
        for c, ids in hit.items():
            for i in sorted(ids, reverse=True):
                c.remove_instance(i)
        out['left'] = {c.static_mesh.get_name(): c.get_instance_count() for c in hit}
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out, ensure_ascii=False)


VIEWS = {'village-north': ((3800, 2500, 600), (8, 95)), 'beach-back': ((3800, -2600, 300), (6, 95)),
         'hill-close': ((4000, 18000, 1800), (-6, 90)), 'aerial': ((4000, -8000, 9000), (-28, 92))}


def view(name):
    (x, y, z), (pitch, yaw) = VIEWS[name]
    return {'location': {'x': x, 'y': y, 'z': z}, 'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}


def run(action, arg=''):
    if action == 'populate':
        return populate()
    if action == 'seat':
        return seat_rocks(arg or 'dry')
    if action == 'trunks':
        return clear_trunks(arg or 'dry')
    if action == 'view':
        return view(arg)
    if action == 'big':
        return big_actors(int(arg or 4000))
    if action == 'survey':
        return survey(int(arg or 1000))
    raise ValueError(action)
