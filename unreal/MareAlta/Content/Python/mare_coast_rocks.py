"""Big coastal rocks along the island's new beaches (08/11, Sergio: "espalhe grandes rochas muito realistas ao longo da
praia, procure assets de rochas naturais costeiras, a água bate nas rochas e faz espuma"). Poly Haven CC0 coastal
rocks (smugglers_cove collection: coast_rocks_*, coast_land_rocks_*, coast_line_*) in clusters of 1-3 every ~25 m
along the waterline (-4 m inland to +12 m out, by the coast distance of island_sdf.bin), outside the village bay; each
stands on the ground or sea floor found by a trace, leans a little and sinks a third of its height. The sea's shore
foam (mare_materials.build_water: water depth behind the surface) rings them by itself. Blocking collision.
PIE stopped; saves."""
import json
import math
import random
import struct
from pathlib import Path

import unreal

LABEL = 'Ilha · rochas da costa'
# slug, weight, size range (m), 'h' = by height (tall boulders and cliffs) or 'l' = by the longest side (the low rock
# shelves of the smugglers_cove set: 30 x 21 m and 1.6 m high, kept near their real size), shore band (cm of coast
# distance, - inland), sink (fraction of the height)
# 08/11 (Sergio, photo of two rocks in the shallows: "quero rochas assim, maior que isso não"): ~4 m at most.
ROCKS = [('rock_face_01', 4, (2.6, 4.0), 'h', (-500, 600), .18), ('rock_face_02', 4, (2.2, 3.6), 'h', (-500, 600), .18),
         # rock_07/rock_09 left out (08/11 photo): blocky, like cut stone next to the rounded rock faces Sergio chose
         # coastal_cliff_01/04 left out (08/11 photo): scaled by height they became 30 m flat walls across the sand
         ('coast_rocks_01', 2, (8.0, 13.0), 'l', (-200, 900), .35), ('coast_rocks_02', 2, (8.0, 13.0), 'l', (-200, 900), .35),
         ('coast_land_rocks_03', 2, (6.0, 9.0), 'l', (-300, 700), .3), ('coast_land_rocks_04', 2, (6.0, 9.0), 'l', (-300, 700), .3),
         ('coast_line_01', 1, (9.0, 14.0), 'l', (-200, 900), .35)]


def _in_bay(x, y):
    # the village bay (kiosk, pier, beach of the demo) keeps its sand clear
    return -26000 < x < 36000 and y < 6000


def run(seed='20261108'):
    import mare_mountains as mm
    import mare_island as mi
    world = mi._world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if a.get_actor_label() == LABEL:
            actors.destroy_actor(a)
    cfg = json.loads((mi.DATA / 'island.json').read_text(encoding='utf-8'))['sdf']
    w, h = cfg['size']
    halfs = struct.unpack('<%de' % (w * h), (mi.DATA / cfg['file']).read_bytes())

    def shore(x, y):
        i = int(round((x - cfg['origin'][0]) / cfg['cell']))
        j = int(round((y - cfg['origin'][1]) / cfg['cell']))
        return halfs[j * w + i] * 100.0 if (0 <= i < w and 0 <= j < h) else 1e6

    rng = random.Random(int(seed))
    centres = []
    X0, X1, Y0, Y1 = -60000, 70000, -15000, 125000
    for _ in range(60000):
        x, y = rng.uniform(X0, X1), rng.uniform(Y0, Y1)
        d = shore(x, y)
        if not -500 < d < 900 or _in_bay(x, y):
            continue
        if any((x - cx) ** 2 + (y - cy) ** 2 < 2500 ** 2 for cx, cy in centres):
            continue
        if rng.random() < .45:
            centres.append((x, y))
    rows, rejected = {}, {}
    total_w = sum(r[1] for r in ROCKS)
    for cx, cy in centres:
        for k in range(rng.choice((1, 2, 2, 3))):
            r = rng.uniform(0, total_w)
            for kind in ROCKS:
                r -= kind[1]
                if r <= 0:
                    break
            slug, wgt, size, mode, band, sink = kind
            for _try in range(6):   # a spot of this cluster inside the kind's shore band
                x, y = cx + rng.uniform(-900, 900) * (k > 0 or _try > 0), cy + rng.uniform(-900, 900) * (k > 0 or _try > 0)
                if band[0] < shore(x, y) < band[1]:
                    break
            else:
                rejected['band'] = rejected.get('band', 0) + 1
                continue
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 5000), unreal.Vector(x, y, -4000),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
            t = hit.to_tuple() if hit else None
            if not t or t[4].z > 400:
                rejected['ground'] = rejected.get('ground', 0) + 1
                continue
            rows.setdefault(slug, []).append((t[4].x, t[4].y, t[4].z, rng.uniform(-180, 180), rng.uniform(*size) * 100,
                                              rng.uniform(-6, 6), rng.uniform(-6, 6), mode, sink))
    root = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector())
    root.set_actor_label(LABEL)
    root.tags = [unreal.Name('MareGenerated'), unreal.Name('MareCoastRocks')]
    root.set_folder_path('Nature/Island')
    from editor_toolset.toolsets.actor import ActorTools
    summary = {}
    for slug, items in rows.items():
        mesh = mm._mesh(slug)
        comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_coast_' + slug)
        comp.set_static_mesh(mesh)
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        comp.set_collision_profile_name('BlockAll')
        comp.set_editor_property('cast_shadow', True)
        b = mesh.get_bounds()
        longest = 2 * max(b.box_extent.x, b.box_extent.y) or 1.0
        base = b.origin.z - b.box_extent.z
        tall = 2 * b.box_extent.z or 1.0
        tr = []
        for x, y, z, yaw, size, pitch, roll, mode, sink in items:
            s = size / (tall if mode == 'h' else longest)
            tr.append(unreal.Transform(unreal.Vector(x, y, z - base * s - sink * tall * s), unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw), unreal.Vector(s, s, s)))
        comp.add_instances(tr, False, True)
        summary[slug] = len(items)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report = {'seed': seed, 'clusters': len(centres), 'instances': summary, 'total': sum(summary.values()), 'rejected': rejected}
    (mi.DATA / 'island_coast_rocks.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    return json.dumps(report)


def slab_material(_=''):
    """B8 (09/11): the rocky point between the pier and the lighthouse (World_2019, coast_rocks_02 from the Godot export,
    a 46 x 50 m slab only 1.6 m high) carried one rock picture stretched over all of it and read as a smooth brown
    ledge. It now takes the CC0 Poly Haven rock_face maps projected in world space every 2.6 m, slightly warmer.
    PIE stopped; saves the mesh."""
    import importlib
    import json
    import unreal
    import mare_materials
    importlib.reload(mare_materials)
    mat_path = mare_materials._custom_pbr('M_Custom_CoastSlab', 'rock_face', 260,
                                     'float3 c=A.rgb; float l=dot(c,float3(.3,.59,.11)); float3 rock=lerp(c,float3(.40,.37,.33)*clamp(l*2.2,.55,1.3),.45);'
                                     # 09/11 (Sergio's photo): under the water the shelf's steps read as black bands: below the
                                     # waterline it turns into the wet sand of the sea floor around it.
                                     'float3 sand=float3(.62,.55,.42)*clamp(l*2.0,.7,1.2); return lerp(rock,sand,smoothstep(5,-45,P.z));')
    mat = unreal.load_asset(mat_path)
    mesh = unreal.load_asset('/Game/World/Models/World_2019/World_2019.World_2019')
    mesh.set_material(0, mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return json.dumps({'mesh': mesh.get_path_name(), 'material': mat.get_path_name()})


POINT_LABEL = 'Ilha · rochas da ponta do píer'


def point_boulders(seed='20261109'):
    """B8 (09/11): the rocky point between the pier and the lighthouse is the Poly Haven coast_rocks_02 shelf (46 x 50 m,
    1.6 m high) from the Godot export: real, but flat, it read as a smooth brown slab. Rounded rock_face boulders
    (2.2-4 m, as the coast rocks) stand on it in two loose groups, so it reads as a rocky point. Re-runnable; PIE
    stopped; saves."""
    import random
    import mare_mountains as mm
    from editor_toolset.toolsets.actor import ActorTools
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if a.get_actor_label() == POINT_LABEL:
            actors.destroy_actor(a)
    rng = random.Random(int(seed))
    groups = [(9000, -4500, 900, 5), (9900, -4950, 700, 4), (8600, -4100, 500, 2)]   # centre x, y, spread, count
    rows = {}
    for gx, gy, spread, count in groups:
        for _ in range(count):
            for _try in range(8):
                x, y = gx + rng.uniform(-spread, spread), gy + rng.uniform(-spread, spread)
                hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 3000), unreal.Vector(x, y, -500),
                                                             unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
                t = hit.to_tuple() if hit else None
                if t and t[4].z > -60:   # on the shelf or the sand, not in the water
                    break
            else:
                continue
            # 10/11 (Sergio: "todas as rochas ao redor do farol estão erradas"): rounded boulders in their own shape (the
            # squashed rock_face flakes read as flat cakes)
            slug = rng.choice(('namaqualand_boulder_02', 'namaqualand_boulder_03', 'namaqualand_boulder_04', 'boulder_01'))
            rows.setdefault(slug, []).append((t[4].x, t[4].y, t[4].z, rng.uniform(-180, 180), rng.uniform(110, 210), rng.uniform(-8, 8), rng.uniform(-8, 8)))
    root = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector())
    root.set_actor_label(POINT_LABEL)
    root.tags = [unreal.Name('MareGenerated'), unreal.Name('MareCoastRocks')]
    root.set_folder_path('Nature/Island')
    root.root_component.set_mobility(unreal.ComponentMobility.STATIC)   # the cook warned: static HISM on a movable root
    summary = {}
    for slug, items in rows.items():
        mesh = mm._mesh(slug)
        comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_point_' + slug)
        comp.set_static_mesh(mesh)
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        comp.set_collision_profile_name('BlockAll')
        b = mesh.get_bounds()
        base, tall = b.origin.z - b.box_extent.z, 2 * b.box_extent.z or 1.0
        tr = []
        for x, y, z, yaw, size, pitch, roll in items:
            s = size / tall
            # its own proportions, sunk a quarter of its height into the shelf
            tr.append(unreal.Transform(unreal.Vector(x, y, z - base * s - .25 * tall * s), unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw), unreal.Vector(s, s, s)))
        comp.add_instances(tr, False, True)
        summary[slug] = len(items)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(summary)


def drop_slab(_=''):
    """B8 (09/11, Sergio's photo): the coast_rocks_02 shelf scaled to 46 x 50 m by the Godot export reads as a flat brown
    slab whatever its material. It is hidden in game and loses its collision (kept in the level, reversible); the rocky
    point is the beach, the coast rocks and the boulders of point_boulders (re-run after this). PIE stopped; saves."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    n = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if c.static_mesh and c.static_mesh.get_name() == 'World_2019':
                c.set_visibility(False)
                c.set_hidden_in_game(True)
                c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                n.append([a.get_actor_label(), c.get_name(), c.get_class().get_name()])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(n, ensure_ascii=False)


def restore_slab(_=''):
    """09/11: without the shelf the old Godot ground under it showed stepped, square-edged sand at the waterline. The
    shelf comes back (rock above the water, wet sand below it: slab_material); point_boulders is re-run on it."""
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    n = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if c.static_mesh and c.static_mesh.get_name() == 'World_2019':
                c.set_visibility(True)
                c.set_hidden_in_game(False)
                c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
                n.append(a.get_actor_label())
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(n, ensure_ascii=False)


RIM_LABEL = 'Ilha · rochas da beirada do farol'
BOULDERS = ('namaqualand_boulder_02', 'namaqualand_boulder_03', 'namaqualand_boulder_04', 'boulder_01')
RIM_SHELVES = ('Maré · coast_rocks_02', 'Maré · coast_rocks_03', 'Maré · coast_rocks_05', 'Maré · coast_land_rocks_02')
RIM_REGION = (7700, 13500, -8000, -1500)
TRAIL = [(7750, -2500), (8740, -3629), (9960, -3930), (10150, -3880), (10430, -3860)]


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy or 1.0
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** .5


def point_rim(arg='apply:20261110'):
    """10/11, Sergio: "todas as rochas ao redor do farol estão erradas, corrigir". The lighthouse stands on the Godot
    coast shelves (coast_rocks_02/03/05, coast_land_rocks_02: Poly Haven rock shelves scaled to tens of metres). Their
    thin edges hang over the sand and the clear water, so from the beach and from the sea they read as boards lying on
    the ground (and dropping the shelf showed the old stepped ground, 09/11). Their whole outline gets a ring of big
    rounded rocks (rock_face_01/02, coast_land_rocks_03/04) wherever the edge stands more than 35 cm over the ground
    under it: each from below the sand or the sea floor up to a little over the shelf top, half outside the edge, so
    the point reads as a rocky headland. Keeps 3.5 m off the lighthouse trail and the pier. 'dry:' counts only;
    'apply:<seed>' builds (re-runnable). Also removes mare_fix_0911.farol_slab_base's copy. PIE stopped; saves."""
    import random
    import mare_mountains as mm
    from editor_toolset.toolsets.actor import ActorTools
    mode, _, seed = arg.partition(':')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if mode == 'apply':   # the old copy and the old rim go first: a destroyed actor in the ignore list breaks the traces
        import mare_fix_0911
        mare_fix_0911.farol_slab_base('revert')
        for a in actors.get_all_level_actors():
            if a.get_actor_label() == RIM_LABEL:
                actors.destroy_actor(a)
    every = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    shelves = [a for a in every if a.get_actor_label() in RIM_SHELVES]
    comps = []
    for a in shelves:
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
            if RIM_REGION[0] - e.x < o.x < RIM_REGION[1] + e.x and RIM_REGION[2] - e.y < o.y < RIM_REGION[3] + e.y:
                comps.append(c)
    rockish = [a for a in every if 'rocha' in a.get_actor_label() or 'rock' in a.get_actor_label().lower()
               or a.get_actor_label() in ('Maré · farol', 'Ilha · base submersa da laje do farol')]

    per_comp = {}

    def shelf_top(x, y):
        best, who = None, None
        for c in comps:
            r = c.line_trace_component(unreal.Vector(x, y, 3000), unreal.Vector(x, y, -800), True, False, False)
            hit = r[0] if isinstance(r, tuple) else r
            if hit:
                z = r[1].z
                if best is None or z > best:
                    best, who = z, c.get_owner().get_actor_label() + '/' + c.get_name()
        if who:
            per_comp[who] = per_comp.get(who, 0) + 1
        return best

    def ground(x, y):
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 3000), unreal.Vector(x, y, -800),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, rockish, unreal.DrawDebugTrace.NONE, True)
        t = hit.to_tuple() if hit else None
        return t[4].z if t and t[0] else None

    step = 100.0
    x0, x1, y0, y1 = RIM_REGION
    nx, ny = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1
    top = {}
    for j in range(ny):
        for i in range(nx):
            z = shelf_top(x0 + i * step, y0 + j * step)
            if z is not None:
                top[(i, j)] = z
    edge = []
    for (i, j), z in top.items():
        out = [(di, dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (i + di, j + dj) not in top]
        if not out:
            continue
        x, y = x0 + i * step, y0 + j * step
        if x < 7700:   # the pier
            continue
        nxo = sum(d[0] for d in out)
        nyo = sum(d[1] for d in out)
        n = (nxo * nxo + nyo * nyo) ** .5 or 1.0
        # ground just outside the edge: how high the edge stands
        g = ground(x + nxo / n * 150, y + nyo / n * 150)
        if g is None or z - g < 20:
            continue
        trail = min(_seg_dist(x, y, *TRAIL[k], *TRAIL[k + 1]) for k in range(len(TRAIL) - 1))
        edge.append((x, y, z, g, nxo / n, nyo / n, trail))
    rng = random.Random(int(seed or 20261110))
    rng.shuffle(edge)
    picked = []
    for p in edge:
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > 220 ** 2 for q in picked):
            picked.append(p)
    if mode == 'dry':
        return json.dumps({'shelf_cells': len(top), 'per_shelf': per_comp, 'edge_cells': len(edge), 'rocks': len(picked),
                           'near_trail': sum(1 for p in picked if p[6] < 350), 'tallest_edge': max([p[2] - p[3] for p in picked] or [0])}, ensure_ascii=False)
    # Rounded boulders (Poly Haven CC0, namaqualand_boulder_02/03/04 and boulder_01, about as tall as they are wide):
    # the coast_land_rocks are long low shelves (scaled by height they became 20 m carpets) and the rock_face are thin
    # cliff flakes (they stood round the slab like blades, 10/11 photos).
    slugs = BOULDERS
    rows = {}
    for x, y, z, g, ox, oy, trail in picked:
        slug = rng.choice(slugs)
        need = (z - g) + rng.uniform(40, 90)             # from under the ground to a little over the shelf top
        size = max(150.0, min(420.0, need / .75))       # sinks 25% of its height into the ground
        push = .22
        if trail < 350:
            # by the lighthouse trail: smaller, just reaching the shelf top, pushed out past the edge so the path stays free
            size = max(110.0, min(size, (z - g + 25) / .75, 200.0))
            push = .5
            if trail + push * size < size * .6 + 120:
                continue
        cx, cy = x + ox * size * push, y + oy * size * push  # half outside the edge (all of it by the trail)
        gz = ground(cx, cy)
        rows.setdefault(slug, []).append((cx, cy, gz if gz is not None else g, size, rng.uniform(-180, 180), rng.uniform(-6, 6), rng.uniform(-6, 6)))
    root = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector())
    root.set_actor_label(RIM_LABEL)
    root.tags = [unreal.Name('MareGenerated'), unreal.Name('MareCoastRocks')]
    root.set_folder_path('Nature/Island')
    root.root_component.set_mobility(unreal.ComponentMobility.STATIC)
    summary = {}
    for slug, items in rows.items():
        mesh = mm._mesh(slug)
        comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_rim_' + slug)
        comp.set_static_mesh(mesh)
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        comp.set_collision_profile_name('BlockAll')
        b = mesh.get_bounds()
        base, tall = b.origin.z - b.box_extent.z, 2 * b.box_extent.z or 1.0
        wide = 2 * max(b.box_extent.x, b.box_extent.y) or 1.0
        tr = []
        for x, y, gz, size, yaw, pitch, roll in items:
            s = size / tall
            sxy = min(s * 1.1, size * 1.6 / wide)   # never wider than 1.6 times its height
            tr.append(unreal.Transform(unreal.Vector(x, y, gz - base * s - .25 * size), unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw),
                                       unreal.Vector(sxy, sxy, s)))
        comp.add_instances(tr, False, True)
        summary[slug] = len(items)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'rocks': summary, 'edge_cells': len(edge)})
