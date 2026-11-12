"""Rock under the lighthouse slabs (11/11, Sergio's photo: "rochas ainda suspensas na água? faça que a rocha comece na
água e suba até a superfície"). The Poly Haven coast slabs round the lighthouse are thin plates: over the water their
rim hangs in the air with a dark gap under it. Every slab gets a solid FOOT of rock: scan() measures the plate from
above on a 30 cm grid (D:/CodexTemp/rock_base.json), tools/ue58/gen_rock_base.py builds one mesh per slab from that
footprint (its top just under the plate's surface, walls that widen down to 4 m under the sea level with a rough
face), place() puts the meshes in the level with the slab's own material. Editor, PIE stopped."""
import json
from pathlib import Path
import unreal

TAG = 'MareRockBase'
OUT = Path('D:/CodexTemp/rock_base.json')
SLABS = ('coast_rocks_02', 'coast_land_rocks_03', 'coast_rocks_05', 'coast_land_rocks_02', 'coast_rocks_03')
NEAR = (10800.0, -4000.0, 2600.0)       # the lighthouse and how far from it a slab counts
STEP = 30.0


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _slabs():
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.Actor):
        label = a.get_actor_label()
        name = next((s for s in SLABS if label.endswith(s)), None)
        if not name:
            continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            o, e = c.get_local_bounds()
            b = unreal.SystemLibrary.get_component_bounds(c)
            if (b[0].x - NEAR[0]) ** 2 + (b[0].y - NEAR[1]) ** 2 < NEAR[2] ** 2:
                out.append((name, a, c, b[0], b[1]))
    return out


def scan(_=''):
    world = _world()
    rows = []
    for name, actor, comp, origin, ext in _slabs():
        x0, y0 = origin.x - ext.x - STEP, origin.y - ext.y - STEP
        nx, ny = int((2 * ext.x) / STEP) + 3, int((2 * ext.y) / STEP) + 3
        grid = []
        for j in range(ny):
            line = []
            for i in range(nx):
                x, y = x0 + i * STEP, y0 + j * STEP
                hits = unreal.SystemLibrary.line_trace_multi(world, unreal.Vector(x, y, origin.z + ext.z + 200), unreal.Vector(x, y, origin.z - ext.z - 200),
                                                             unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True) or []
                top = None
                for h in hits:
                    t = h.to_tuple()
                    if t[9] == actor:
                        top = round(t[4].z, 1)
                        break
                line.append(top)
            grid.append(line)
        mat = comp.get_material(0)
        rows.append({'name': name, 'x0': x0, 'y0': y0, 'step': STEP, 'grid': grid, 'material': mat.get_path_name() if mat else '',
                     'cells': sum(1 for l in grid for v in l if v is not None), 'z': [round(origin.z - ext.z), round(origin.z + ext.z)]})
    OUT.write_text(json.dumps(rows), encoding='utf-8')
    return json.dumps([[r['name'], r['cells'], r['z'], len(r['grid'][0]), len(r['grid'])] for r in rows])


def place(arg='dry'):
    data = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data' / 'custom_assets.json').read_text(encoding='utf-8'))
    rows = json.loads(OUT.read_text(encoding='utf-8'))
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mine = [a for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.StaticMeshActor) if TAG in [str(t) for t in a.tags]]
    out = {'mine': len(mine), 'placed': []}
    if arg.strip() != 'apply':
        return json.dumps(out)
    for a in mine:
        actors.destroy_actor(a)
    for k, r in enumerate(rows):
        mesh = unreal.load_asset(data.get(f'mare_rock_base_{k}', ''))
        if not mesh:
            continue
        # the model is in world metres with Blender y = -UE y: placed at the origin, no rotation
        a = actors.spawn_actor_from_object(mesh, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=0))
        a.set_actor_label('Farol · base de rocha ' + r['name'])
        a.tags = [unreal.Name('MareGenerated'), unreal.Name(TAG)]
        a.set_folder_path('Praia/Farol')
        c = a.static_mesh_component
        c.set_mobility(unreal.ComponentMobility.STATIC)
        mat = unreal.load_asset(r['material']) if r['material'] else None
        if mat:
            for s in range(c.get_num_materials()):
                c.set_material(s, mat)
        out['placed'].append(r['name'])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out)


def boulders(arg='dry'):
    """11/11: the generated foot still read as a smooth embankment with a saw-toothed rim. Real boulders (the Poly
    Haven rocks already lying on the slabs: rock_07, rock_09, boulder_01) are piled along every stretch of rim that
    stands over water, half in the sea, random size and turn: they hide the seam like a natural rock fall.
    One actor (tag MareRockBoulders), one HISM per rock, no collision. 'apply' places and saves; re-runnable."""
    import math
    import random
    from editor_toolset.toolsets.actor import ActorTools
    world = _world()
    rows = json.loads(OUT.read_text(encoding='utf-8'))
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    meshes = []
    for name in ('rock_071', 'rock_091', 'boulder_011'):
        for d in reg.get_assets_by_class(unreal.TopLevelAssetPath('/Script/Engine', 'StaticMesh'), False):
            if str(d.asset_name) == name:
                meshes.append(unreal.load_asset(str(d.package_name)))
                break
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    every = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    mine = [a for a in every if 'MareRockBoulders' in [str(t) for t in a.tags]]
    ignore = mine + [a for a in every if TAG in [str(t) for t in a.tags] or any(a.get_actor_label().endswith(s) for s in SLABS)]
    rng = random.Random(1111)
    spots = []
    for r in rows:
        g = r['grid']
        ny, nx = len(g), len(g[0])
        step = r['step']
        last = None
        for j in range(ny):
            for i in range(nx):
                if g[j][i] is None:
                    continue
                out_x = out_y = 0
                for dj, di in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    jj, ii = j + dj, i + di
                    if not (0 <= jj < ny and 0 <= ii < nx) or g[jj][ii] is None:
                        out_x += di
                        out_y += dj
                if not (out_x or out_y):
                    continue
                n = math.hypot(out_x, out_y)
                x, y = r['x0'] + i * step, r['y0'] + j * step
                if any((x - sx) ** 2 + (y - sy) ** 2 < 150 ** 2 for sx, sy, _ in spots[-400:]):
                    continue
                px, py = x + out_x / n * 120, y + out_y / n * 120
                hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(px, py, 300), unreal.Vector(px, py, -600), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                             True, ignore, unreal.DrawDebugTrace.NONE, True)
                ground = hit.to_tuple()[4].z if hit else -400
                if ground > -15:          # dry land beside the slab: nothing hangs there
                    continue
                spots.append((x + out_x / n * rng.uniform(20, 90), y + out_y / n * rng.uniform(20, 90), g[j][i]))
    out = {'meshes': [m.get_name() for m in meshes], 'spots': len(spots)}
    if arg.strip() != 'apply' or not meshes:
        return json.dumps(out)
    for a in mine:
        actors.destroy_actor(a)
    root = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector())
    root.set_actor_label('Farol · pedras da beirada')
    root.tags = [unreal.Name('MareGenerated'), unreal.Name('MareRockBoulders')]
    root.set_folder_path('Praia/Farol')
    per = {m: [] for m in meshes}
    for x, y, top in spots:
        for k in range(rng.randint(1, 2)):
            m = rng.choice(meshes)
            b = m.get_bounds()
            size = max(b.box_extent.x, b.box_extent.y, b.box_extent.z) * 2
            want = rng.uniform(110, 230) if k == 0 else rng.uniform(60, 120)
            s = want / max(size, 1)
            z = rng.uniform(-70, -10) if k == 0 else rng.uniform(-40, 20)
            per[m].append(unreal.Transform(unreal.Vector(x + rng.uniform(-50, 50), y + rng.uniform(-50, 50), z),
                                           unreal.Rotator(roll=rng.uniform(-25, 25), pitch=rng.uniform(-25, 25), yaw=rng.uniform(-180, 180)),
                                           unreal.Vector(s * rng.uniform(.85, 1.2), s * rng.uniform(.85, 1.2), s * rng.uniform(.7, 1.0))))
    for m, ts in per.items():
        comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_' + m.get_name())
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_static_mesh(m)
        comp.add_instances(ts, False, True)
        out[m.get_name()] = len(ts)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out)
