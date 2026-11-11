"""Flowers in the village gardens (11/11, Sergio: "coloque flores nos jardins"): the raised round beds under the square
trees were bare earth and the wooden planter boxes stood empty. build('dry'|'apply') plants Poly Haven gazanias and
periwinkles (CC0, already in the project for the lawns: mare_lawn.FLOWERS):
 - tree beds: every village tree is scanned in rings; where the ground is a raised bed (20-70 cm above the pavement
   around it) flowers go in loose drifts, clear of the trunk and of the kerb;
 - planter boxes (planter_box_01): a row of flowers on the soil inside each box, at the height traced there.
One actor ('Mare · Flores dos canteiros', tag MareGardenFlowers), one HISM per plant, no collision, no shadows.
Re-runnable: the previous actor is replaced. PIE stopped."""
import json
import math
import random
import unreal

TAG = 'MareGardenFlowers'
LABEL = 'Mare · Flores dos canteiros'
VILLAGE = (-600, 10800, 1800, 7300)          # x0, x1, y0, y1
PLANTS = (('flower_gazania', (.85, 1.2)), ('periwinkle_plant', (.8, 1.15)))


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _instances(world, wanted):
    """World transforms of every ISM instance whose actor label contains one of the wanted names."""
    out = {w: [] for w in wanted}
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        label = a.get_actor_label()
        hit = next((w for w in wanted if w in label), None)
        if not hit:
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            for i in range(c.get_instance_count()):
                out[hit].append((c.get_instance_transform(i, True), c.static_mesh, a))
    return out


def build(arg='dry'):
    import mare_lawn
    apply = arg.strip() == 'apply'
    world = _world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    old = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor) if TAG in [str(t) for t in a.tags]]
    lawn = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor) if 'MareLawn' in [str(t) for t in a.tags]]
    ignore = old + lawn
    rng = random.Random(20261111)

    def ground(x, y, top=150.0, extra=()):
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, top), unreal.Vector(x, y, -60), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                     True, ignore + list(extra), unreal.DrawDebugTrace.NONE, True)
        return hit.to_tuple()[4].z if hit else None

    found = _instances(world, ('tree_amendoeira', 'island_tree', 'planter_box_01', '@MeshInstance3D@6206', ' canteiro'))
    rows = {p[0]: [] for p in PLANTS}
    report = {'beds': [], 'boxes': []}
    # --- raised beds under trees
    for name in ('tree_amendoeira', 'island_tree'):
        for t, mesh, actor in found[name]:
            cx, cy = t.translation.x, t.translation.y
            if not (VILLAGE[0] < cx < VILLAGE[1] and VILLAGE[2] < cy < VILLAGE[3]):
                continue
            far = [ground(cx + math.cos(a) * 480, cy + math.sin(a) * 480, extra=[actor]) for a in (0, 1.57, 3.14, 4.71)]
            far = sorted(z for z in far if z is not None)
            if not far:
                continue
            pave = far[len(far) // 2]
            spots = []
            for r in range(75, 330, 22):
                n = max(6, int(2 * math.pi * r / 26))
                for k in range(n):
                    a = 2 * math.pi * (k + rng.random() * .6) / n
                    x, y = cx + math.cos(a) * (r + rng.uniform(-8, 8)), cy + math.sin(a) * (r + rng.uniform(-8, 8))
                    z = ground(x, y, extra=[actor])
                    if z is None or not (pave + 20 < z < pave + 70):
                        continue
                    # clear of the kerb: the bed must still be there 14 cm further out
                    # (36 cm: a plant is ~25 cm across; with 14 cm some stood on the kerb and hung over the pavement)
                    zo = ground(cx + math.cos(a) * (r + 36), cy + math.sin(a) * (r + 36), extra=[actor])
                    zm = ground(cx + math.cos(a) * (r + 18), cy + math.sin(a) * (r + 18), extra=[actor])
                    if zo is None or zm is None or abs(zo - z) > 6 or abs(zm - z) > 6:
                        continue
                    spots.append((x, y, z, a, r))
            if len(spots) < 12:
                continue
            # loose drifts: four to six sectors keep their flowers, each sector one kind
            sectors = rng.sample(range(8), rng.randint(5, 6))
            kinds = {s: PLANTS[i % 2] for i, s in enumerate(sectors)}
            used = 0
            for x, y, z, a, r in spots:
                s = int((a % (2 * math.pi)) / (2 * math.pi) * 8)
                if s not in kinds or rng.random() < .25:
                    continue
                slug, (lo, hi) = kinds[s]
                rows[slug].append((x, y, z - 1.5, rng.uniform(-180, 180), rng.uniform(lo, hi)))
                used += 1
            report['beds'].append([round(cx), round(cy), round(pave), len(spots), used])
    # --- planter boxes
    # The church's blue troughs ('@MeshInstance3D@6206') carried lollipop flowers (the Godot 'canteiro' mesh: a stick
    # and a ball): those instances go, real flowers are planted in the trough like in a planter box.
    troughs = [row for row in found['@MeshInstance3D@6206']
               if any((row[0].translation.x - c[0].translation.x) ** 2 + (row[0].translation.y - c[0].translation.y) ** 2 < 60 * 60 for c in found[' canteiro'])]
    report['troughs'] = len(troughs)
    if apply:
        doomed = {}
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
            if not a.get_actor_label().endswith(' canteiro'):
                continue
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                for i in range(c.get_instance_count()):
                    l = c.get_instance_transform(i, True).translation
                    if any((l.x - t[0].translation.x) ** 2 + (l.y - t[0].translation.y) ** 2 < 60 * 60 for t in troughs):
                        doomed.setdefault(c, []).append(i)
        for c, idx in doomed.items():
            for i in sorted(idx, reverse=True):
                c.remove_instance(i)
        report['lollipops_removed'] = sum(len(v) for v in doomed.values())
    for t, mesh, actor in found['planter_box_01'] + troughs:
        b = mesh.get_bounds()
        sx, sy = b.box_extent.x * t.scale3d.x, b.box_extent.y * t.scale3d.y
        yaw = math.radians(t.rotation.rotator().yaw)
        long_x = sx >= sy
        half, cross = (sx, sy) if long_x else (sy, sx)
        n = max(3, int((half * 2 - 16) / 17))
        placed = 0
        for k in range(n):
            wide = cross > 35          # the church troughs (90 cm across): three rows that fill the width
            for row in ((-1, 0, 1) if wide else (-1, 1) if cross > 20 else (0,)):
                u = -half + 10 + (half * 2 - 20) * (k + .5) / n + rng.uniform(-2, 2) + (8 if wide and row == 0 else 0)
                v = row * (cross * .52 if wide else min(cross * .32, 9)) + rng.uniform(-1.5, 1.5)
                lx, ly = (u, v) if long_x else (v, u)
                x = t.translation.x + lx * math.cos(yaw) - ly * math.sin(yaw)
                y = t.translation.y + lx * math.sin(yaw) + ly * math.cos(yaw)
                # the boxes have no collision: the soil is 5 cm under the rim (top of the mesh bounds)
                z = t.translation.z + (b.origin.z + b.box_extent.z) * t.scale3d.z - 5
                slug, (lo, hi) = PLANTS[(k + (row > 0)) % 2]
                rows[slug].append((x, y, z - 1.0, rng.uniform(-180, 180), rng.uniform(lo, hi) * .8))
                placed += 1
        report['boxes'].append([round(t.translation.x), round(t.translation.y), round(sx * 2), round(sy * 2), placed])
    report['total'] = {k: len(v) for k, v in rows.items()}
    if not apply:
        return json.dumps(report)
    for a in old:
        actors.destroy_actor(a)
    root = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector())
    root.set_actor_label(LABEL)
    root.tags = [unreal.Name('MareGenerated'), unreal.Name(TAG)]
    root.set_folder_path('Nature/Gardens')
    for slug, items in rows.items():
        if not items:
            continue
        from editor_toolset.toolsets.actor import ActorTools
        comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_' + slug)
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        mesh = mare_lawn._mesh(slug)
        comp.set_static_mesh(mesh)
        comp.set_editor_property('cast_shadow', False)
        comp.set_editor_property('instance_start_cull_distance', 7000)
        comp.set_editor_property('instance_end_cull_distance', 9000)
        b = mesh.get_bounds()
        base = b.origin.z - b.box_extent.z
        comp.add_instances([unreal.Transform(unreal.Vector(x, y, z - base * s), unreal.Rotator(yaw=yaw), unreal.Vector(s, s, s)) for x, y, z, yaw, s in items], False, True)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(report)
