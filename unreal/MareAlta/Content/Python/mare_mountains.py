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


REGION = (-34000, 42000, 6000, 72000)    # x0, x1, y0, y1 (cm): hills around the village
MIN_Z = 600                               # above the village/beach ground
# slug, weight, scale range, cull distance (0 = never), casts shadow
# Backdrop hills are seen from 150-400 m: trees are scaled up so the canopy reads as forest.
TREES = [('island_tree_01', 3, (1.6, 2.5)), ('island_tree_02', 3, (1.6, 2.5)), ('island_tree_03', 2, (1.6, 2.3)),
         ('tree_small_02', 2, (1.8, 2.6)), ('jacaranda_tree', 1, (1.3, 1.8))]
UNDER = [('shrub_01', 3, (2.0, 3.0)), ('shrub_02', 3, (2.0, 3.0)), ('shrub_03', 2, (2.0, 2.8)), ('shrub_04', 2, (2.0, 2.8)), ('fern_02', 2, (2.0, 3.0))]
MAX_SLOPE_NZ = 0.60


def _mesh(slug):
    dest = '/Game/Nature/Mountain/' + slug
    found = [unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(dest, recursive=True)] if unreal.EditorAssetLibrary.does_directory_exist(dest) else []
    found = [m for m in found if isinstance(m, unreal.StaticMesh)]
    if found:
        return found[0]
    import mare_hotel_lobby
    info = json.loads((LIB / slug / 'info.json').read_text(encoding='utf-8'))
    mesh = mare_hotel_lobby._import(LIB / slug / info['gltf'], dest, slug, True)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
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
        if label == 'Maré · Ground' or (label.startswith('Maré · @MeshInstance3D') and a.get_actor_bounds(False)[1].z > 1500):
            hills.add(label)
    rng = random.Random(seed)
    placements = {}
    rejected = {'miss': 0, 'low': 0, 'steep': 0}
    x0, x1, y0, y1 = REGION
    for layer, table, step, jitter in (('tree', TREES, 520, 220), ('under', UNDER, 400, 170)):
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
                else:
                    slug, (s0, s1) = _pick(rng, table)
                    s = rng.uniform(s0, s1)
                    placements.setdefault(slug, []).append((h[0].x, h[0].y, h[0].z - 15, rng.uniform(-180, 180), s))
                y += step
            x += step
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
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report = {'region': REGION, 'min_z': MIN_Z, 'seed': seed, 'instances': summary, 'total': sum(summary.values()), 'rejected': rejected}
    (DATA / 'mountain_vegetation.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    return report


VIEWS = {'village-north': ((3800, 2500, 600), (8, 95)), 'beach-back': ((3800, -2600, 300), (6, 95)),
         'hill-close': ((4000, 18000, 1800), (-6, 90)), 'aerial': ((4000, -8000, 9000), (-28, 92))}


def view(name):
    (x, y, z), (pitch, yaw) = VIEWS[name]
    return {'location': {'x': x, 'y': y, 'z': z}, 'rotation': {'pitch': pitch, 'yaw': yaw, 'roll': 0}, 'scale': {'x': 1, 'y': 1, 'z': 1}}


def run(action, arg=''):
    if action == 'populate':
        return populate()
    if action == 'view':
        return view(arg)
    if action == 'big':
        return big_actors(int(arg or 4000))
    if action == 'survey':
        return survey(int(arg or 1000))
    raise ValueError(action)
