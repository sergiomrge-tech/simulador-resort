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
            slug = rng.choice(('rock_face_01', 'rock_face_02'))
            rows.setdefault(slug, []).append((t[4].x, t[4].y, t[4].z, rng.uniform(-180, 180), rng.uniform(160, 260), rng.uniform(-3, 3), rng.uniform(-3, 3)))
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
            # wider than tall (x1.5 across): a rounded boulder sitting deep in the shelf, not a standing flake
            tr.append(unreal.Transform(unreal.Vector(x, y, z - base * s * .8 - .35 * tall * s * .8), unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw), unreal.Vector(s * 1.5, s * 1.5, s * .8)))
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
