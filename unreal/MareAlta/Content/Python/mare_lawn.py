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
SHRUBS = [('shrub_01', 4, (0.8, 1.3)), ('shrub_03', 3, (0.7, 1.1)),   # 09/11: shrub_02/04 read as dry brown clumps (B12)
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


def fix_0911(arg=''):
    """B12 (09/11): the pousada lawn showed dry brown clumps and plants on the concrete path. shrub_02 and shrub_04
    have grey-brown leaves and red stems (dry from a distance): their instances become shrub_01 / shrub_03. Plants
    placed under an expansion's floor, path or deck (populate traces through the Region_ buildings so a lot keeps its
    lawn until bought) are removed. arg 'dry' only counts. PIE stopped; saves the level."""
    from editor_toolset.toolsets.actor import ActorTools
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    dry = arg == 'dry'
    world = _world()
    swap = {'shrub_02': 'shrub_01', 'shrub_04': 'shrub_03'}
    removed, swapped, kept = {}, {}, 0
    every = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    soft = [a for a in every if any(t in a.get_actor_label().lower() for t in ('grass', 'gramado', 'bush', 'fern', 'palm', 'tree', 'plant', 'pcg', 'galhos', 'arbust'))]
    terrain = {a.get_actor_label() for a in every if a.get_actor_label() == 'Maré · Ground' or
               a.get_actor_label().startswith('Maré · Preenchimento costeiro') or
               (a.get_actor_label().startswith('Maré · @MeshInstance3D') and a.get_actor_bounds(False)[1].z > 1500)}
    over = {}
    # Flat built pieces without collision (the pousada path): plants inside their footprint go too.
    flat = []
    for a in every:
        if a in soft or a.get_actor_label() in terrain or not isinstance(a, unreal.StaticMeshActor):
            continue
        o, e = a.get_actor_bounds(False)
        if e.z < 20 and e.x * e.y > 20000 and e.x * e.y < 4.0e6:
            flat.append((o.x - e.x, o.x + e.x, o.y - e.y, o.y + e.y, o.z - e.z - 30, o.z + e.z + 10, a.get_actor_label()[:40]))
    half = {}

    def over_paving(kind, tr):
        import math
        if kind not in half:
            b = _mesh(kind).get_bounds()
            half[kind] = max(b.box_extent.x, b.box_extent.y) * .8
        r = half[kind] * tr.scale3d.x
        l = tr.translation
        for k in range(8):
            a = k * math.pi / 4
            px, py = l.x + math.cos(a) * r, l.y + math.sin(a) * r
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(px, py, l.z + 120), unreal.Vector(px, py, l.z - 60),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, soft, unreal.DrawDebugTrace.NONE, True)
            if hit:
                t = hit.to_tuple()
                if t[10] and t[10].get_num_materials() and t[10].get_material(0) and t[10].get_material(0).get_name() in PAVED_ALL:
                    return True
        return False
    PAVED_ALL = ('MA_0707ebbc10476ed7b24d2463',)
    for root in [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label().startswith(LABEL)]:
        comps = {c.get_name().replace('HISM_', ''): c for c in root.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent)}
        # A lot's own lawn (tag Lot_<id>) is hidden with the lot once bought: only the open lawn can poke through floors.
        open_lawn = not _tag_ids(root, 'Lot_')
        PAVED = ('MA_0707ebbc10476ed7b24d2463',)   # the village's concrete paths (World_0002/0004)
        for kind, comp in list(comps.items()):
            drop, move = [], []
            for i in range(comp.get_instance_count()):
                tr = comp.get_instance_transform(i, True)
                l = tr.translation
                # A path, deck or floor right over the plant's base (3-80 cm above it; roofs and canopies are higher
                # and plants are ignored): the plant pokes through it. The pousada path is not a Region_ piece.
                hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(l.x, l.y, l.z + 80), unreal.Vector(l.x, l.y, l.z - 30),
                                                             unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, soft, unreal.DrawDebugTrace.NONE, True)
                if hit:
                    t = hit.to_tuple()
                    # Paved paths are instances in the same Godot ISM actors as the hill tiles (counted as terrain by
                    # populate): their concrete material marks them.
                    paved = t[10] and t[10].get_num_materials() and t[10].get_material(0) and t[10].get_material(0).get_name() in PAVED
                    if t[9] and (paved or t[9].get_actor_label() not in terrain) and t[4].z > l.z + 3 and (open_lawn or not _tag_ids(t[9], 'Region_')):
                        drop.append(i)
                        k = ('caminho · ' if paved else '') + t[9].get_actor_label()[:40]
                        over[k] = over.get(k, 0) + 1
                        continue
                # Shrubs, ferns and flowers spread: a 1.5x fern rooted 1.2 m from the pousada path covered it. Test the
                # crown's edge (the mesh's half width at this scale) for paving too.
                if kind not in ('grass_medium_01', 'grass_medium_02') and over_paving(kind, tr):
                    drop.append(i)
                    over['copa sobre o caminho'] = over.get('copa sobre o caminho', 0) + 1
                    continue
                inside = next((f for f in flat if f[0] < l.x < f[1] and f[2] < l.y < f[3] and f[4] < l.z < f[5]), None)
                if inside:
                    drop.append(i)
                    over[inside[6]] = over.get(inside[6], 0) + 1
                    continue
                if kind in swap:
                    move.append(tr)
            removed[kind] = removed.get(kind, 0) + len(drop)
            kept += comp.get_instance_count() - len(drop)
            if kind in swap:
                swapped[kind] = swapped.get(kind, 0) + len(move)
            if dry:
                continue
            if kind in swap:
                comp.clear_instances()
                target = comps.get(swap[kind])
                if not target:
                    target = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_' + swap[kind])
                    target.set_mobility(unreal.ComponentMobility.STATIC)
                    target.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                    target.set_static_mesh(_mesh(swap[kind]))
                    target.set_editor_property('instance_start_cull_distance', 10000)
                    target.set_editor_property('instance_end_cull_distance', 14000)
                    comps[swap[kind]] = target
                # same pivot height rule as populate: base of the new mesh on the ground
                old_b, new_b = _mesh(kind).get_bounds(), _mesh(swap[kind]).get_bounds()
                d = (old_b.origin.z - old_b.box_extent.z) - (new_b.origin.z - new_b.box_extent.z)
                target.add_instances([unreal.Transform(unreal.Vector(t.translation.x, t.translation.y, t.translation.z + d * t.scale3d.z),
                                                       t.rotation.rotator(), t.scale3d) for t in move], False, True)
            elif drop:
                comp.remove_instances(drop)
    if not dry:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'removed_under_buildings': removed, 'swapped': swapped, 'kept': kept, 'dry': dry,
                       'over': dict(sorted(over.items(), key=lambda kv: -kv[1])[:25])}, ensure_ascii=False)
