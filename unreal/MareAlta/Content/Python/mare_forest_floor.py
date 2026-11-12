"""Island forest floor (08/11, Sergio: "procure assets de galhos para colocar no chão, galhos e folhas"): the island
ground material with the leaf litter (mare_materials.build_ground(island=True)) and Poly Haven CC0 debris scattered on
the forest floor: dry branches, bark debris, fallen trunks, stumps, roots and moss (tools/ue58/fetch_polyhaven.py
--set forest_floor). Non-colliding HISMs without shadows for the small pieces, culled by distance; the trunks and
stumps cast shadows. Same exclusions as the forest (village, trails, summit house, steep, sand). PIE stopped; saves."""
import json


def island_ground(_=''):
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    m = mare_materials.build_ground(island=True)
    import mare_usage_fix
    return json.dumps({'material': m.get_path_name(), 'usage': mare_usage_fix.assets(m.get_path_name())})


LABEL = 'Ilha · galhos, troncos e folhas do chão da mata'
# slug, grid step (cm), keep fraction, target size range (m, the model's longest side), sink (fraction of its height),
# casts shadow, cull distance (cm)
DEBRIS = [('dry_branches_medium_01', 450, .45, (1.2, 2.4), .15, False, 4500),
          ('bark_debris_01', 600, .35, (.5, 1.1), .2, False, 3500),
          # moss_01 left out (08/11): its Poly Haven material is alpha-blended (invisible on Nanite) and it read as a blob
          ('root_cluster_01', 1900, .4, (1.2, 2.2), .35, True, 7000),
          ('root_cluster_02', 1900, .4, (1.2, 2.2), .35, True, 7000),
          ('tree_stump_01', 2100, .45, (.7, 1.2), .08, True, 9000),
          ('tree_stump_02', 2100, .45, (.7, 1.2), .08, True, 9000),
          ('dead_tree_trunk', 2600, .5, (3.0, 6.0), .25, True, 12000),
          ('dead_tree_trunk_02', 2600, .5, (3.0, 6.0), .25, True, 12000)]


def scatter(seed='20261108'):
    """Debris on the forest floor (the forest's ground: 45 m and more from the coast), not on the trails, the village,
    the summit clearing or steep ground; each piece leans with the slope and sinks a little into it."""
    import math
    import random
    import struct
    from pathlib import Path
    import unreal
    import mare_mountains as mm
    import mare_island as mi
    world = mi._world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if a.get_actor_label() == LABEL:
            actors.destroy_actor(a)
    ground_ok = {a.get_actor_label() for a in actors.get_all_level_actors() if a.get_actor_label() == 'Ilha · terreno novo'
                 or (a.get_actor_label().startswith('Maré · @MeshInstance3D') and a.get_actor_bounds(False)[1].z > 1500)}
    data = mi.DATA
    cfg = json.loads((data / 'island.json').read_text(encoding='utf-8'))['sdf']
    w, h = cfg['size']
    halfs = struct.unpack('<%de' % (w * h), (data / cfg['file']).read_bytes())

    def shore(x, y):
        i = int(round((x - cfg['origin'][0]) / cfg['cell']))
        j = int(round((y - cfg['origin'][1]) / cfg['cell']))
        return halfs[j * w + i] * 100.0 if (0 <= i < w and 0 <= j < h) else 1e6

    trail = {}
    for tr in json.loads((data / 'island_trails.json').read_text(encoding='utf-8'))['trails'].values():
        for (x_, y_, _), wf in zip(tr['points'], tr.get('w') or [1.0] * len(tr['points'])):
            trail.setdefault((int(x_ // 500), int(y_ // 500)), []).append((x_, y_, (wf * 100 + 120) ** 2))

    def near_trail(x, y):
        gx, gy = int(x // 500), int(y // 500)
        return any((qx - x) ** 2 + (qy - y) ** 2 < r2 for i in (gx - 1, gx, gx + 1) for j in (gy - 1, gy, gy + 1)
                   for qx, qy, r2 in trail.get((i, j), ()))

    rng = random.Random(int(seed))
    rows, rejected = {}, {}
    X0, X1, Y0, Y1 = -48000, 56000, -12000, 114000
    for slug, step, keep, (s0, s1), sink, shadow, cull in DEBRIS:
        x = X0
        while x <= X1:
            y = Y0
            while y <= Y1:
                px, py = x + rng.uniform(-step * .45, step * .45), y + rng.uniform(-step * .45, step * .45)
                y += step
                if shore(px, py) > -4500 or rng.random() > keep:
                    continue
                if (px - 4000) ** 2 + (py - 38900) ** 2 < 2200 ** 2 or near_trail(px, py):
                    rejected['clear'] = rejected.get('clear', 0) + 1
                    continue
                hit = mm._hit(world, px, py, [])
                if not hit or not hit[2] or hit[2].get_actor_label() not in ground_ok:
                    rejected['ground'] = rejected.get('ground', 0) + 1
                    continue
                if hit[1].z < .8 or hit[0].z < 20:
                    rejected['steep'] = rejected.get('steep', 0) + 1
                    continue
                n = hit[1]
                rows.setdefault(slug, []).append((hit[0].x, hit[0].y, hit[0].z, rng.uniform(-180, 180), rng.uniform(s0, s1) * 100, (n.x, n.y, n.z)))
            x += step
    root = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector())
    root.set_actor_label(LABEL)
    root.tags = [unreal.Name('MareGenerated'), unreal.Name('MareIslandDebris')]
    root.set_folder_path('Nature/Island')
    from editor_toolset.toolsets.actor import ActorTools
    summary = {}
    for slug, step, keep, size, sink, shadow, cull in DEBRIS:
        items = rows.get(slug, [])
        if not items:
            continue
        mesh = mm._mesh(slug)
        comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_debris_' + slug)
        comp.set_static_mesh(mesh)
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_editor_property('cast_shadow', shadow)
        # out of the Lumen surface cache like the forest (stale daylight at night, 08/11); they still receive GI
        comp.set_editor_property('affect_dynamic_indirect_lighting', False)
        comp.set_editor_property('affect_distance_field_lighting', False)
        comp.set_editor_property('instance_start_cull_distance', int(cull * .75))
        comp.set_editor_property('instance_end_cull_distance', cull)
        b = mesh.get_bounds()
        longest = 2 * max(b.box_extent.x, b.box_extent.y, b.box_extent.z) or 1.0
        base = b.origin.z - b.box_extent.z
        tall = 2 * b.box_extent.z
        transforms = []
        for x, y, z, yaw, length, nn in items:
            s = length / longest
            up = unreal.Vector(*nn)
            rot = unreal.MathLibrary.compose_rotators(unreal.Rotator(roll=0, pitch=0, yaw=yaw), unreal.MathLibrary.make_rot_from_z(up))
            d = -base * s + sink * tall * s
            transforms.append(unreal.Transform(unreal.Vector(x - up.x * d, y - up.y * d, z - up.z * d), rot, unreal.Vector(s, s, s)))
        comp.add_instances(transforms, False, True)
        summary[slug] = len(items)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report = {'seed': seed, 'instances': summary, 'total': sum(summary.values()), 'rejected': rejected}
    (data / 'island_debris.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    return json.dumps(report)


def sample(arg='dry_branches_medium_01,2'):
    """QA: world locations of the first instances of one debris kind ("slug,count"), to frame close-up photos."""
    import unreal
    slug, n = arg.split(',')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if a.get_actor_label() == LABEL:
            for c in a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
                if c.static_mesh and c.static_mesh.get_name().startswith(slug):
                    out = []
                    for i in range(0, c.get_instance_count(), max(1, c.get_instance_count() // int(n))):
                        t = c.get_instance_transform(i, True)
                        out.append([round(t.translation.x), round(t.translation.y), round(t.translation.z), round(t.scale3d.x, 3)])
                    return json.dumps(out[:int(n)])
    return '[]'


def drop_moss(_=''):
    """Deletes the moss import (no longer scattered)."""
    import unreal
    return json.dumps(unreal.EditorAssetLibrary.delete_directory('/Game/Nature/Mountain/moss_01'))
