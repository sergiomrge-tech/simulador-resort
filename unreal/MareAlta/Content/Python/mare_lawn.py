"""Lawn dressing for the open green areas of the resort (hotel lot, back lawns): tall grass tufts,
ferns and CC0 Poly Haven shrubs on real surface hits. Plants on a lot that an expansion builds over
are tagged Lot_<id>, so UMareVisualWorld hides them with the lot cover once it is purchased."""
import json
import random
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
DATA = ROOT / 'Content/Data'
LABEL = 'Mare · Gramado e arbustos'


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _hit(world, x, y):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 6000), unreal.Vector(x, y, -2000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    if not hit:
        return None
    t = hit.to_tuple()
    return t[4], t[7], t[9]


def probe(arg):
    out = []
    for spec in arg.split(';'):
        x, y = [float(v) for v in spec.split(',')]
        h = _hit(_world(), x, y)
        out.append({'at': [x, y], 'z': round(h[0].z) if h else None, 'nz': round(h[1].z, 2) if h else None,
                    'actor': h[2].get_actor_label() if h and h[2] else None, 'tags': [str(t) for t in h[2].tags] if h and h[2] else []})
    return out


REGION = (-20000, 22500, -1000, 15500)  # x0, x1, y0, y1 (cm): resort, village, lots and the foothills
MAX_Z = 1500                              # up into the lower edge of the hill forest (trees start at 600)
CENTRE, CORE = (3000, 3000), 9000         # outside this radius grass clumps are a bit larger
# slug, weight, scale range (real-size understorey; mountain_vegetation uses 2-3x for the far hills)
SHRUBS = [('shrub_01', 3, (0.8, 1.3)), ('shrub_02', 3, (0.8, 1.3)), ('shrub_03', 2, (0.7, 1.1)), ('shrub_04', 2, (0.7, 1.1)),
          ('fern_02', 3, (0.9, 1.5))]   # wild_rooibos_bush / shrub_sorrel_01 read as black blots at mid range
FLOWERS = [('flower_gazania', 1, (0.9, 1.3)), ('periwinkle_plant', 1, (0.9, 1.3))]
# Full green clumps (Poly Haven grass_medium) over every open lawn; the older inland PCG wisps stay as variety.
GRASS = [('grass_medium_01', 1, (0.8, 1.25)), ('grass_medium_02', 1, (0.8, 1.25))]
GRASS_STEP = {'': 60}   # cm between clumps on open lawn; lots (no PCG grass there) get three per cell


def _mesh(slug):
    """Shared Poly Haven import; plants already imported for the hills are reused from there."""
    import mare_mountains
    for root in ('/Game/Nature/Mountain/', '/Game/Nature/Lawn/'):
        if unreal.EditorAssetLibrary.does_directory_exist(root + slug):
            found = [unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(root + slug, recursive=True)]
            found = [m for m in found if isinstance(m, unreal.StaticMesh)]
            if found:
                return found[0]
    import mare_hotel_lobby
    info = json.loads((mare_mountains.LIB / slug / 'info.json').read_text(encoding='utf-8'))
    mesh = mare_hotel_lobby._import(mare_mountains.LIB / slug / info['gltf'], '/Game/Nature/Lawn/' + slug, slug, True)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return mesh


def _tag_ids(actor, prefix):
    return [str(t)[len(prefix):] for t in actor.tags if str(t).startswith(prefix) and len(str(t)) > len(prefix)]


def _clear(x, y, blocks):
    """Off the sand band and outside building blocks (same rule as mare_grass.excluded)."""
    import math
    edge = math.sin(x * .0017) * 90 + math.sin(x * .0041) * 35
    if y + edge * .6 < -1050:
        return False
    return not any(abs(x - bx * 100) < w * 50 + 120 and abs(y - by * 100) < d * 50 + 120 for bx, by, w, d in blocks)


def populate(seed=20261102):
    from editor_toolset.toolsets.actor import ActorTools
    import mare_mountains
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE before dressing the lawn')
    world = _world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if a.get_actor_label().startswith(LABEL):
            actors.destroy_actor(a)
    every = actors.get_all_level_actors()
    buildings = [a for a in every if _tag_ids(a, 'Region_')]
    manifest = json.loads((DATA / 'world.json').read_text(encoding='utf-8-sig'))
    # Godot block_rects mix buildings with big reserved open lots (41x25 m west of the hotel); only
    # building-sized blocks keep plants away.
    blocks = [r for r in manifest['blocks'] if r[2] * r[3] < 600]
    # Village ground plus the tall hill tiles around it (same selection as mare_mountains.populate).
    terrain = {a.get_actor_label() for a in every if a.get_actor_label() == 'Maré · Ground' or
               a.get_actor_label().startswith('Maré · Preenchimento costeiro') or
               (a.get_actor_label().startswith('Maré · @MeshInstance3D') and a.get_actor_bounds(False)[1].z > 1500)}
    # Pedestrian routes (Godot x,z in m) stay free of shrubs: segments as UE cm.
    routes = [((a[0] * 100, a[2] * 100), (b[0] * 100, b[2] * 100)) for path in manifest['paths'] for a, b in zip(path, path[1:])]

    def near_route(x, y, r=180):
        for (ax, ay), (bx, by) in routes:
            dx, dy = bx - ax, by - ay
            t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / max(dx * dx + dy * dy, 1)))
            if (x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2 < r * r:
                return True
        return False

    def surface(x, y):
        """(point, normal, lot id or '') of open lawn at x,y, or None. Lawn under an expansion that is
        built later belongs to that lot and disappears with it."""
        h = _hit(world, x, y)
        if not h or not h[2]:
            return None
        lot = ''
        regions = _tag_ids(h[2], 'Region_')
        if regions:
            lot = regions[0]
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 6000), unreal.Vector(x, y, -2000),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, buildings, unreal.DrawDebugTrace.NONE, True)
            if not hit:
                return None
            t = hit.to_tuple()
            h = (t[4], t[7], t[9])
            if not h[2]:
                return None
        lots = _tag_ids(h[2], 'Lot_')
        if lots:
            lot = lots[0]
        elif h[2].get_actor_label() not in terrain:
            return None
        if h[0].z > MAX_Z or h[1].z < 0.72:
            return None
        return h[0], h[1], lot

    # Poly Haven grass_medium_01/02 glTFs hold their 17/5 clump variants side by side, so one instance is a row
    # 5.6 m (1.3 m) long along local X: test the whole row, not just its pivot, or it runs over curbs and streets.
    row_x = {}

    def strip_ok(slug, centre, x, y, yaw, scale):
        import math
        if slug not in row_x:
            b = _mesh(slug).get_bounds()
            row_x[slug] = (b.origin.x - b.box_extent.x, b.origin.x + b.box_extent.x)
        lo, hi = row_x[slug]
        c, s_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        n = max(2, int((hi - lo) * scale / 60))
        for i in range(n + 1):
            d = (lo + (hi - lo) * i / n) * scale
            px, py = x + c * d, y + s_ * d
            if abs(d) < 1:
                continue
            if not _clear(px, py, blocks) or near_route(px, py, 130):
                return False
            k = surface(px, py)
            if not k or k[2] != centre[2] or abs(k[0].z - centre[0].z) > 25:
                return False
        return True

    rng = random.Random(seed)
    rows = {}   # (lot, kind) -> [(x, y, z, yaw, scale)]
    x0, x1, y0, y1 = REGION
    # Understorey: loose clumps of 2-4 shrubs/ferns every ~4.5 m on open lawn.
    for x in range(x0, x1, 450):
        for y in range(y0, y1, 450):
            if rng.random() > 0.75:
                continue
            cx, cy = x + rng.uniform(-240, 240), y + rng.uniform(-240, 240)
            for _ in range(rng.choice((2, 3, 3, 4))):
                px, py = cx + rng.uniform(-140, 140), cy + rng.uniform(-140, 140)
                if not _clear(px, py, blocks) or near_route(px, py):
                    continue
                s = surface(px, py)
                if not s:
                    continue
                slug, (a, b) = mare_mountains._pick(rng, SHRUBS)
                rows.setdefault((s[2], slug), []).append((s[0].x, s[0].y, s[0].z - 6, rng.uniform(-180, 180), rng.uniform(a, b)))
            # Small flower patches between the shrubs.
            if rng.random() < 0.35:
                slug, (a, b) = mare_mountains._pick(rng, FLOWERS)
                for _ in range(rng.randint(3, 6)):
                    px, py = cx + rng.uniform(-220, 220), cy + rng.uniform(-220, 220)
                    s = surface(px, py) if _clear(px, py, blocks) and not near_route(px, py, 90) else None
                    if s:
                        rows.setdefault((s[2], slug), []).append((s[0].x, s[0].y, s[0].z - 2, rng.uniform(-180, 180), rng.uniform(a, b)))
    # Grass clumps on every open lawn, denser on lots where the inland grass PCG never reached.
    step = GRASS_STEP['']
    for x in range(x0, x1, step):
        for y in range(y0, y1, step):
            far = (x - CENTRE[0]) ** 2 + (y - CENTRE[1]) ** 2 > CORE * CORE
            jx, jy = x + rng.uniform(-22, 22), y + rng.uniform(-22, 22)
            s = surface(jx, jy) if _clear(jx, jy, blocks) and not near_route(jx, jy, 130) else None
            if not s:
                continue
            pts = [(s, jx, jy)]
            if s[2]:   # lot: two more clumps in this cell
                for _ in range(2):
                    kx, ky = x + rng.uniform(-30, 30), y + rng.uniform(-30, 30)
                    k = surface(kx, ky)
                    if k:
                        pts.append((k, kx, ky))
            for k, kx, ky in pts:
                slug, (a, b) = mare_mountains._pick(rng, GRASS)
                yaw, sc = rng.uniform(-180, 180), rng.uniform(a, b) * (1.35 if far else 1)
                if strip_ok(slug, k, kx, ky, yaw, sc):
                    rows.setdefault((k[2], slug), []).append((k[0].x, k[0].y, k[0].z - 3, yaw, sc))
    roots, summary = {}, {}
    for (lot, kind), items in sorted(rows.items()):
        root = roots.get(lot)
        if not root:
            root = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector())
            root.set_actor_label(LABEL + (' · lote ' + lot if lot else ''))
            root.tags = [unreal.Name('MareGenerated'), unreal.Name('MareLawn')] + ([unreal.Name('Lot_' + lot)] if lot else [])
            root.set_folder_path('Nature/Lawn')
            roots[lot] = root
        comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_' + kind)
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        mesh = _mesh(kind)
        comp.set_static_mesh(mesh)
        low = any(kind == g[0] for g in GRASS + FLOWERS)
        comp.set_editor_property('cast_shadow', not low)
        comp.set_editor_property('instance_start_cull_distance', 7000 if low else 10000)
        comp.set_editor_property('instance_end_cull_distance', 9000 if low else 14000)
        b = mesh.get_bounds()
        base = b.origin.z - b.box_extent.z
        transforms = [unreal.Transform(unreal.Vector(x, y, z - base * s), unreal.Rotator(yaw=yaw), unreal.Vector(s, s, s)) for x, y, z, yaw, s in items]
        comp.add_instances(transforms, False, True)
        summary[(lot or 'aberto') + '/' + kind] = len(transforms)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report = {'region': REGION, 'seed': seed, 'instances': summary, 'total': sum(summary.values())}
    (DATA / 'lawn_dressing.json').write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding='utf-8')
    return report


def run(action, arg=''):
    if action == 'probe':
        return probe(arg)
    if action == 'populate':
        return populate()
    raise ValueError(action)
