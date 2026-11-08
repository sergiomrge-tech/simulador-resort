"""Small island (06/11/2026, Sergio: "transformar o mapa numa ILHA PEQUENA"): survey of the current map, then the
re-executable generator (terrain, sea floor, vegetation). Entry through the MCP: hotel_lobby hud_module
"mare_island.<function>|<arg>"."""
import json
import math
import random
from pathlib import Path

import unreal

OUT = Path(r'D:/CodexTemp/island')
DATA = Path(unreal.Paths.project_dir()).resolve() / 'Content/Data'


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _actors():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()


def survey(arg=''):
    """Bounds of the terrain and of every built thing, so the island can be drawn around them without moving any."""
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    ground = None
    for a in _actors():
        label = a.get_actor_label()
        try:
            origin, ext = a.get_actor_bounds(False)
        except Exception:
            continue
        tags = [str(t) for t in a.tags]
        cls = a.get_class().get_name()
        meshes = []
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if c.static_mesh:
                n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
                meshes.append([c.static_mesh.get_path_name(), n])
        rows.append({'label': label, 'name': a.get_name(), 'class': cls, 'tags': tags,
                     'o': [round(origin.x), round(origin.y), round(origin.z)], 'e': [round(ext.x), round(ext.y), round(ext.z)],
                     'meshes': meshes[:6], 'nmesh': len(meshes)})
        if a.get_name() == 'World_0000' or label == 'Ground':
            ground = a
    info = {}
    if ground:
        c = ground.get_components_by_class(unreal.StaticMeshComponent)[0]
        sm = c.static_mesh
        info = {'label': ground.get_actor_label(), 'mesh': sm.get_path_name(), 'loc': str(ground.get_actor_location()),
                'rot': str(ground.get_actor_rotation()), 'scale': str(ground.get_actor_scale3d()),
                'bounds': str(sm.get_bounding_box()), 'mats': [m.get_path_name() if m else None for m in c.get_materials()],
                'nanite': sm.get_editor_property('nanite_settings').enabled,
                'verts': unreal.EditorStaticMeshLibrary.get_number_verts(sm, 0) if hasattr(unreal, 'EditorStaticMeshLibrary') else -1}
    (OUT / 'actors.json').write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
    xs = [r for r in rows if r['e'][0] < 30000 and r['e'][1] < 30000]
    return json.dumps({'actors': len(rows), 'ground': info,
                       'x': [min(r['o'][0] - r['e'][0] for r in xs), max(r['o'][0] + r['e'][0] for r in xs)],
                       'y': [min(r['o'][1] - r['e'][1] for r in xs), max(r['o'][1] + r['e'][1] for r in xs)],
                       'big': [[r['label'], r['o'], r['e']] for r in rows if r['e'][0] >= 30000 or r['e'][1] >= 30000][:20]},
                      ensure_ascii=False)


def heights(arg='-40000,40000,-20000,40000,500'):
    """Height grid of the terrain by vertical traces (only the Ground actor counts): x0,x1,y0,y1,step in cm."""
    x0, x1, y0, y1, step = [float(v) for v in arg.split(',')]
    world = _world()
    ground = [a for a in _actors() if a.get_name() == 'World_0000' or a.get_actor_label() == 'Ground']
    grid = []
    y = y0
    while y <= y1:
        row = []
        x = x0
        while x <= x1:
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 60000), unreal.Vector(x, y, -60000),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
            z = None
            if hit:
                t = hit.to_tuple()
                actor = t[9] if len(t) > 9 else None
                z = round(t[4].z) if actor and ground and actor == ground[0] else ('B' + str(round(t[4].z)))
            row.append(z)
            x += step
        grid.append(row)
        y += step
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'heights.json').write_text(json.dumps({'arg': arg, 'grid': grid}), encoding='utf-8')
    return json.dumps({'rows': len(grid), 'cols': len(grid[0]) if grid else 0})


def land(arg='-45000,45000,-20000,60000,500'):
    """Height of the first blocking surface at every grid point (any actor except water and people), with the label of
    what was hit, for drawing the island contour around ALL existing land: x0,x1,y0,y1,step in cm.
    Writes D:/CodexTemp/island/land.json {arg, z: rows of height or null, who: rows of label index, labels}."""
    x0, x1, y0, y1, step = [float(v) for v in arg.split(',')]
    world = _world()
    skip = [a for a in _actors() if 'Oceano' in a.get_actor_label() or 'nata' in a.get_actor_label()]
    labels, index, zs, who = [], {}, [], []
    y = y0
    while y <= y1:
        zr, wr = [], []
        x = x0
        while x <= x1:
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 30000), unreal.Vector(x, y, -30000),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, skip,
                                                         unreal.DrawDebugTrace.NONE, True)
            z, w = None, -1
            if hit:
                t = hit.to_tuple()
                actor = t[9] if len(t) > 9 else None
                z = round(t[4].z)
                name = actor.get_actor_label() if actor else '?'
                if name not in index:
                    index[name] = len(labels)
                    labels.append(name)
                w = index[name]
            zr.append(z)
            wr.append(w)
            x += step
        zs.append(zr)
        who.append(wr)
        y += step
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'land.json').write_text(json.dumps({'arg': arg, 'z': zs, 'who': who, 'labels': labels}, ensure_ascii=False), encoding='utf-8')
    return json.dumps({'rows': len(zs), 'cols': len(zs[0]) if zs else 0, 'labels': len(labels)})


def seabed(_=''):
    """Step 2 (08/11): the island's sand floor (tools/ue58/gen_island_seabed.py) in place of the four straight
    planes of mare_water.ensure_seabed (same tag MareSeabed, same wet-sand material, no collision: swimming uses
    UMareReefWorld::SeabedZ). PIE stopped; saves the level."""
    import mare_hotel_lobby as hl
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    folder = '/Game/World/Island/mare_island_seabed'
    if unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.delete_directory(folder)
    mesh = hl._import(Path('D:/Assets/Mare/mare_island_seabed/mare_island_seabed.glb'), folder, 'mare_island_seabed', False, search=False)
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    ground = mare_materials.build_ground(seabed=True)   # M_IslandSeabed_PBR: all wet sand
    mesh.set_material(0, ground)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    removed = []
    for a in actors.get_all_level_actors():
        if 'MareSeabed' in [str(t) for t in a.tags]:
            removed.append(a.get_actor_label())
            actors.destroy_actor(a)
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    a.set_actor_label('Mar · fundo de areia · ilha')
    a.tags = ['MareGenerated', 'MareSeabed']
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property('cast_shadow', False)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    b = mesh.get_bounds()
    return json.dumps({'removed': removed, 'mesh': mesh.get_path_name(), 'tris': mesh.get_num_triangles(0),
                       'origin': [round(b.origin.x), round(b.origin.y), round(b.origin.z)]}, ensure_ascii=False)


def sea_info(_=''):
    """Ocean plane and swim volume actors: transform and the mesh's own bounds (step 3 survey)."""
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        l = a.get_actor_label()
        if 'Oceano' in l or 'nata' in l or 'Ocean' in l:
            row = {'label': l, 'class': a.get_class().get_name(), 'loc': str(a.get_actor_location()), 'scale': str(a.get_actor_scale3d())}
            if isinstance(a, unreal.StaticMeshActor):
                m = a.static_mesh_component.static_mesh
                row['mesh'] = m.get_path_name()
                row['verts'] = m.get_num_vertices(0)
                bb = m.get_bounding_box()
                row['mesh_box'] = [str(bb.min), str(bb.max)]
            out.append(row)
    return json.dumps(out, ensure_ascii=False)


def sea(_=''):
    """Step 3 (08/11): the ocean all round the island. Re-imports the graded grid (tools/ue58/gen_ocean.py), rebuilds
    M_CoastalWater_PBR on the coast distance (T_IslandSDF) and stretches the swim volume over the whole ring of sea
    (x +-1300 m, y -2432..+2050 m, below the water level as before). PIE stopped; saves the level."""
    import importlib
    import mare_beach
    import mare_materials
    importlib.reload(mare_materials)
    importlib.reload(mare_beach)
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    ocean = mare_beach.reimport_ocean()
    water = mare_materials.build_water().get_path_name()
    vol = None
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if isinstance(a, unreal.PhysicsVolume) and 'nata' in a.get_actor_label():
            vol = a
    if vol:
        vol.set_actor_location(unreal.Vector(0, -19100, -5030), False, False)
        vol.set_actor_scale3d(unreal.Vector(1300, 2241, 50))
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'ocean': ocean, 'water': water, 'volume': str(vol.get_actor_location()) if vol else None}, default=str)


def terrain(_=''):
    """Step 4 (08/11): the new land of the island (tools/ue58/gen_island_terrain.py) with the coast-aware ground
    material (sand at the coast, grass inland), walkable (complex collision). PIE stopped; saves the level."""
    import importlib
    import mare_hotel_lobby as hl
    import mare_materials
    importlib.reload(mare_materials)
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    folder = '/Game/World/Island/IslandTerrain'
    if unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.delete_directory(folder)
    src = Path(unreal.Paths.project_dir()).resolve() / 'SourceArt/Island/IslandTerrain.gltf'
    mesh = hl._import(src, folder, 'IslandTerrain', False, search=False)
    mat = mare_materials.build_ground(island=True)
    mesh.set_material(0, mat)
    hl._complex_collision(mesh)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if 'MareIslandTerrain' in [str(t) for t in a.tags]:
            actors.destroy_actor(a)
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    a.set_actor_label('Ilha · terreno novo')
    a.tags = ['MareGenerated', 'MareIslandTerrain']
    a.static_mesh_component.set_static_mesh(mesh)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    b = mesh.get_bounds()
    return json.dumps({'mesh': mesh.get_path_name(), 'tris': mesh.get_num_triangles(0), 'material': mat.get_path_name(),
                       'origin': [round(b.origin.x), round(b.origin.y), round(b.origin.z)], 'extent': [round(b.box_extent.x), round(b.box_extent.y), round(b.box_extent.z)]})


def palms(_=''):
    """The four beach coconut-palm meshes (the ones using M_PalmLeaflets_PBR) and their sizes."""
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    opts = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True, include_searchable_names=False, include_soft_management_references=False, include_hard_management_references=False)
    out = []
    mat_pkg = None
    for p in unreal.EditorAssetLibrary.list_assets('/Game/World', True, False):
        if p.split('.')[-1] == 'M_PalmLeaflets_PBR':
            mat_pkg = p.split('.')[0]
    for r in reg.get_referencers(unreal.Name(mat_pkg), opts) if mat_pkg else []:
        assets = reg.get_assets_by_package_name(r)
        m = assets[0].get_asset() if assets else None
        if isinstance(m, unreal.StaticMesh):
            b = m.get_bounds()
            out.append([m.get_path_name(), round(b.box_extent.z * 2)])
    return json.dumps({'material': mat_pkg, 'palms': out})


def find_meshes(arg='palm'):
    """Static meshes used in the level by actors whose label contains arg (any case), with counts and heights."""
    out = {}
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if arg.lower() not in a.get_actor_label().lower():
            continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if not m:
                continue
            n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
            row = out.setdefault(m.get_path_name(), [0, round(m.get_bounds().box_extent.z * 2), a.get_actor_label()[:40]])
            row[0] += n
    return json.dumps(out, ensure_ascii=False)


def profile_line(arg='0,3000,-45000,3000,200'):
    """Heights along a line (x0,y0,x1,y1,step cm) in PIE: the steps bigger than 60 cm between neighbours (walls)."""
    x0, y0, x1, y1, step = [float(v) for v in arg.split(',')]
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() or _world()
    n = int(math.hypot(x1 - x0, y1 - y0) / step)
    prev, jumps, pts = None, [], []
    for k in range(n + 1):
        x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 30000), unreal.Vector(x, y, -3000),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        z = round(hit.to_tuple()[4].z) if hit else None
        who = hit.to_tuple()[9].get_actor_label()[:24] if hit and hit.to_tuple()[9] else None
        if prev is not None and z is not None and abs(z - prev) > 60:
            jumps.append([round(x), round(y), prev, z, who])
        if k % 25 == 0:
            pts.append([round(x), round(y), z, who])
        prev = z
    return json.dumps({'jumps': jumps[:30], 'samples': pts}, ensure_ascii=False)


FOREST_LABEL = 'Ilha · floresta e coqueiros'
PALM = 'World_0507'          # the beach coconut palm (PCG Pilot · Palms), 8.7 m


def forest(seed='20261108'):
    """Step 5 (08/11, Sergio: "faça uma grande floresta", "floresta no meio e na praia coqueiros", "mantenha o morro da
    Vila, precisa ter acesso da Vila à floresta"): a dense forest over the middle of the island (the summit range and
    the new plains) and coconut palms along the new beaches. Kept clear: the village and its hill (y < 12000 inside the
    old ground), the summit trail (the access from the village into the forest, 4 m each side), the old man's house
    and buildings. Non-colliding HISMs with distance culling, like the mountain vegetation. PIE stopped; saves."""
    import mare_mountains as mm
    import importlib
    importlib.reload(mm)
    world = _world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if a.get_actor_label() == FOREST_LABEL:
            actors.destroy_actor(a)
    ground_ok = set()
    for a in actors.get_all_level_actors():
        l = a.get_actor_label()
        if l == 'Ilha · terreno novo' or l.startswith('Maré · Preenchimento costeiro') or l == 'Maré · Ground' or \
                (l.startswith('Maré · @MeshInstance3D') and a.get_actor_bounds(False)[1].z > 1500):
            ground_ok.add(l)
    rng = random.Random(int(seed))
    sdf_cfg = json.loads((DATA / 'island.json').read_text(encoding='utf-8'))['sdf']
    import array
    raw = (DATA / sdf_cfg['file']).read_bytes()
    import struct as _st
    w, h = sdf_cfg['size']
    halfs = _st.unpack('<%de' % (w * h), raw)

    def shore(x, y):
        i = int(round((x - sdf_cfg['origin'][0]) / sdf_cfg['cell']))
        j = int(round((y - sdf_cfg['origin'][1]) / sdf_cfg['cell']))
        if not (0 <= i < w and 0 <= j < h):
            return 1e6
        return halfs[j * w + i] * 100.0

    # the three trails stay clear: the summit trail (its mesh, by traces) and West/North (island_trails.json points)
    trail_grid = {}
    for tr in json.loads((DATA / 'island_trails.json').read_text(encoding='utf-8'))['trails'].values():
        for x_, y_, _ in tr['points']:
            trail_grid.setdefault((int(x_ // 1000), int(y_ // 1000)), []).append((x_, y_))

    def near_trail(x, y):
        gx, gy = int(x // 1000), int(y // 1000)
        for i in (gx - 1, gx, gx + 1):
            for j in (gy - 1, gy, gy + 1):
                for qx, qy in trail_grid.get((i, j), ()):
                    if (qx - x) ** 2 + (qy - y) ** 2 < 450 ** 2:
                        return True
        for dx, dy in ((0, 0), (400, 0), (-400, 0), (0, 400), (0, -400)):
            q = mm._hit(world, x + dx, y + dy, [])
            if q and q[2] and 'trilha' in q[2].get_actor_label():
                return True
        return False

    placements, rejected = {}, {}

    def reject(k):
        rejected[k] = rejected.get(k, 0) + 1

    X0, X1, Y0, Y1 = -48000, 56000, -12000, 114000
    layers = (('palm', None, 900, 300), ('tree', mm.TREES, 620, 260), ('under', mm.UNDER, 520, 220))
    for layer, table, step, jitter in layers:
        x = X0
        while x <= X1:
            y = Y0
            while y <= Y1:
                px, py = x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter)
                d = shore(px, py)
                if layer == 'palm':
                    ok_band = -3000 < d < -500
                else:
                    ok_band = d < -3500
                if not ok_band:
                    y += step
                    continue
                hit = mm._hit(world, px, py, [])
                if not hit or not hit[2]:
                    reject('miss')
                elif hit[2].get_actor_label() not in ground_ok:
                    reject('other')         # roofs, props, roads: buildings stay clear
                elif layer == 'palm' and hit[2].get_actor_label() != 'Ilha · terreno novo':
                    reject('old beach')     # the bay keeps its own palms
                elif hit[2].get_actor_label() == 'Maré · Ground' and py < 12000:
                    reject('village')       # the village and its hill stay as they are
                elif math.hypot(px - 4000, py - 38900) < 2000:
                    reject('summit house')
                elif hit[1].z < (.75 if layer == 'palm' else .45 if layer == 'tree' else .5):
                    reject('steep')
                elif hit[0].z < -10:
                    reject('wet')
                elif layer == 'palm' and rng.random() > .65:
                    reject('gap')
                elif layer == 'tree' and mm._clearing(px, py, int(seed)) < .1:
                    reject('clearing')
                elif near_trail(px, py):
                    reject('trail')
                else:
                    if layer == 'palm':
                        slug, s = PALM, rng.uniform(.85, 1.2)
                    else:
                        slug, (s0, s1) = mm._pick(rng, table)
                        s = rng.uniform(s0, s1)
                    placements.setdefault(slug, []).append((hit[0].x, hit[0].y, hit[0].z - 15, rng.uniform(-180, 180), s, layer))
                y += step
            x += step
    # rocky outcrops on the slopes too steep for trees (the hill's faces), like the mountain vegetation
    rocks = {}
    x = X0
    while x <= X1:
        y = Y0
        while y <= Y1:
            px, py = x + rng.uniform(-300, 300), y + rng.uniform(-300, 300)
            if shore(px, py) < -3000:
                hit = mm._hit(world, px, py, [])
                if hit and hit[2] and hit[2].get_actor_label() == 'Ilha · terreno novo' and .25 < hit[1].z < .6 and rng.random() < .6                         and not near_trail(px, py):
                    slug, (a, b) = mm._pick(rng, mm.ROCKS)
                    # 08/11 (Sergio: "rochas flutuando no morro"): lean with the slope (up = ground normal), sunk below
                    n = hit[1]
                    rocks.setdefault(slug, []).append((hit[0].x, hit[0].y, hit[0].z, rng.uniform(-180, 180), rng.uniform(a, b) * 100,
                                                       (n.x, n.y, n.z), 0))
            y += 800
        x += 800
    root = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector())
    root.set_actor_label(FOREST_LABEL)
    root.tags = [unreal.Name('MareGenerated'), unreal.Name('MareIslandForest')]
    root.set_folder_path('Nature/Island')
    from editor_toolset.toolsets.actor import ActorTools
    summary = {}
    for slug, rows in placements.items():
        mesh = mm._mesh(slug)
        comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_' + slug)
        comp.set_static_mesh(mesh)
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        big = rows[0][5] in ('tree', 'palm')
        comp.set_editor_property('cast_shadow', big)
        if not big:
            comp.set_editor_property('instance_start_cull_distance', 12000)
            comp.set_editor_property('instance_end_cull_distance', 16000)
        b = mesh.get_bounds()
        base = b.origin.z - b.box_extent.z
        comp.add_instances([unreal.Transform(unreal.Vector(x, y, z - base * s), unreal.Rotator(roll=0, pitch=0, yaw=yaw), unreal.Vector(s, s, s))
                            for x, y, z, yaw, s, _ in rows], False, True)
        summary[slug] = len(rows)
    for slug, rows in rocks.items():
        mesh = mm._mesh(slug)
        comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_rock_' + slug)
        comp.set_static_mesh(mesh)
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        b = mesh.get_bounds()
        span = 2 * max(b.box_extent.x, b.box_extent.y)
        base = b.origin.z - b.box_extent.z
        transforms = []
        for x, y, z, yaw, size, normal, _ in rows:
            s = size / span
            up = unreal.Vector(*normal)
            rot = unreal.MathLibrary.compose_rotators(unreal.Rotator(roll=0, pitch=0, yaw=yaw), unreal.MathLibrary.make_rot_from_z(up))
            # the base sinks along the normal: below the pivot by the model's base, then 45% of its height into the slope
            sink = (-base * s + .45 * 2 * b.box_extent.z * s)
            transforms.append(unreal.Transform(unreal.Vector(x - up.x * sink, y - up.y * sink, z - up.z * sink), rot, unreal.Vector(s, s, s)))
        comp.add_instances(transforms, False, True)
        summary['rock_' + slug] = len(rows)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report = {'seed': seed, 'instances': summary, 'total': sum(summary.values()), 'rejected': rejected}
    (DATA / 'island_forest.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    return json.dumps(report)


def north_actors(arg='30000'):
    """Actors whose bounds reach north of y = arg (cm), except the generated island/sea pieces: label, centre, extent."""
    y0 = float(arg)
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        l = a.get_actor_label()
        if any(k in l for k in ('Ilha', 'Mar ·', 'Oceano', 'nata', 'Navega', 'Ocean')):
            continue
        try:
            o, e = a.get_actor_bounds(False)
        except Exception:
            continue
        if o.y + e.y > y0 and e.x < 60000:
            out.append([l[:40], round(o.x), round(o.y), round(o.z), round(e.x), round(e.y), round(e.z)])
    return json.dumps(sorted(out, key=lambda r: r[2]), ensure_ascii=False)


DOME = ['Maré · @MeshInstance3D@%d' % n for n in range(1877, 1937)]


def remove_dome(_=''):
    """08/11 (Sergio, on the aerial photo: "essa parte marcada vira planície e floresta"): the big dome north of the
    old man's house (terrain tiles 1877-1936, y 470-860 m, up to 294 m) goes; the summit ridge with the house and the
    trail stays. The mountain vegetation planted on the dome goes with it. PIE stopped; saves the level."""
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    gone = []
    for a in actors.get_all_level_actors():
        if a.get_actor_label() in DOME:
            gone.append(a.get_actor_label())
            actors.destroy_actor(a)
    trimmed = 0
    for a in actors.get_all_level_actors():
        if a.get_actor_label() == 'Mare · Vegetação das montanhas':
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                drop = [i for i in range(c.get_instance_count()) if c.get_instance_transform(i, True).translation.y > 46500]
                if drop:
                    c.remove_instances(drop)
                    trimmed += len(drop)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'removed': len(gone), 'vegetation_removed': trimmed})


TRAIL_CROSS = [-190, -100, -60, -20, 20, 60, 100, 190]


def trail_heights(_=''):
    """Exact ground heights across the island trails (Content/Data/island_trails.json), every 2 m at the TRAIL_CROSS
    offsets (cm, left to right): D:/CodexTemp/island/trail_cross.json for tools/ue58/gen_island_trails.py. PIE stopped."""
    world = _world()
    trails = json.loads((DATA / 'island_trails.json').read_text(encoding='utf-8'))['trails']
    out = {}
    for key, t in trails.items():
        pts = t['points']
        wf = t.get('w') or [1.0] * len(pts)      # width factor along the trail (08/11: not a straight even band)
        rows = []
        for k, (x, y, _) in enumerate(pts):
            a, b = pts[max(0, k - 1)], pts[min(len(pts) - 1, k + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy) or 1.0
            sx, sy = dy / n, -dx / n        # to the right of the walking direction
            row = []
            for c in TRAIL_CROSS:
                px, py = x + sx * c * wf[k], y + sy * c * wf[k]
                hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(px, py, 30000), unreal.Vector(px, py, -3000),
                                                             unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
                row.append(round(hit.to_tuple()[4].z, 1) if hit else None)
            rows.append(row)
        out[key] = {'points': pts, 'w': wf, 'cross': TRAIL_CROSS, 'z': rows}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'trail_cross.json').write_text(json.dumps(out), encoding='utf-8')
    return json.dumps({k: len(v['z']) for k, v in out.items()})


def trails(_=''):
    """The West and North trail paths (tools/ue58/gen_island_trails.py) placed at the origin. PIE stopped; saves."""
    import mare_hotel_lobby as hl
    folder = '/Game/World/Island/mare_island_trails'
    if unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.delete_directory(folder)
    mesh = hl._import(Path('D:/Assets/Mare/mare_island_trails/mare_island_trails.glb'), folder, 'mare_island_trails', False, search=False)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if 'MareIslandTrails' in [str(x) for x in a.tags]:
            actors.destroy_actor(a)
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    a.set_actor_label('Ilha · trilhas Oeste e Norte')
    a.tags = ['MareGenerated', 'MareIslandTrails']
    a.static_mesh_component.set_static_mesh(mesh)
    a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'mesh': mesh.get_path_name(), 'tris': mesh.get_num_triangles(0)})


COVER_LABEL = 'Ilha · capim e plantas rasteiras'
# slug, weight, target height (m) range, width stretch: the forest floor and the plains (08/11, Sergio: "falta um pouco
# de vegetação no terreno da ilha", "não esqueça das gramas/vegetação"): Quaternius grass clumps (CC0, already in the
# village lawn), ferns and low plants, in patches (~30 m noise) so it reads as natural ground, not an even carpet.
COVER_GRASS = [('World_2062', 3, (.45, .8), 2.4), ('World_2071', 3, (.5, .9), 2.0)]
COVER_PLANTS = [('World_0503', 2, (.6, 1.0), 1.0), ('World_2069', 2, (.6, 1.0), 1.0), ('World_2067', 2, (.6, 1.0), 1.0),
                ('World_0502', 1, (.8, 1.3), 1.0), ('World_2063', 1, (.3, .5), 1.2), ('World_2064', 1, (.3, .5), 1.2)]


COVER_LAWN_GREEN = False   # the village lawn recolour turned the standing clumps blue-grey (08/11 photo)


def _pick_cover(rng, table):
    total = sum(r[1] for r in table)
    r = rng.uniform(0, total)
    for slug, wgt, hr, stretch in table:
        r -= wgt
        if r <= 0:
            return slug, hr, stretch
    return table[-1][0], table[-1][2], table[-1][3]


def ground_cover(seed='20261108'):
    """Grass clumps every ~85 cm and ferns/plants every ~2.2 m on the island's natural ground (the new land and the
    old summit range), off the beach sand (from 22 m inland, thinning out to 37 m), the village and its hill, the trails and steep faces.
    Non-colliding HISMs without shadows, culled at 25-40 m (grass) and 50-70 m (plants). PIE stopped; saves."""
    import mare_mountains as mm
    import mare_grass
    import struct as _st
    world = _world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in actors.get_all_level_actors():
        if a.get_actor_label() == COVER_LABEL:
            actors.destroy_actor(a)
    ground_ok = set()
    for a in actors.get_all_level_actors():
        l = a.get_actor_label()
        if l == 'Ilha · terreno novo' or l.startswith('Maré · Preenchimento costeiro') or l == 'Maré · Ground' or \
                (l.startswith('Maré · @MeshInstance3D') and a.get_actor_bounds(False)[1].z > 1500):
            ground_ok.add(l)
    cfg = json.loads((DATA / 'island.json').read_text(encoding='utf-8'))['sdf']
    w, h = cfg['size']
    halfs = _st.unpack('<%de' % (w * h), (DATA / cfg['file']).read_bytes())

    def shore(x, y):
        i = int(round((x - cfg['origin'][0]) / cfg['cell']))
        j = int(round((y - cfg['origin'][1]) / cfg['cell']))
        return halfs[j * w + i] * 100.0 if (0 <= i < w and 0 <= j < h) else 1e6

    trail_grid = {}
    for tr in json.loads((DATA / 'island_trails.json').read_text(encoding='utf-8'))['trails'].values():
        for (x_, y_, _), wf in zip(tr['points'], tr.get('w') or [1.0] * len(tr['points'])):
            trail_grid.setdefault((int(x_ // 500), int(y_ // 500)), []).append((x_, y_, (wf * 100 + 25) ** 2))

    def on_trail(x, y):
        gx, gy = int(x // 500), int(y // 500)
        for i in (gx - 1, gx, gx + 1):
            for j in (gy - 1, gy, gy + 1):
                for qx, qy, r2 in trail_grid.get((i, j), ()):
                    if (qx - x) ** 2 + (qy - y) ** 2 < r2:
                        return True
        return False

    rng = random.Random(int(seed))
    rows, rejected = {}, {}

    def reject(k):
        rejected[k] = rejected.get(k, 0) + 1

    X0, X1, Y0, Y1 = -48000, 56000, -12000, 114000
    for layer, table, step, jitter in (('grass', COVER_GRASS, 85, 38), ('plant', COVER_PLANTS, 220, 95)):
        x = X0
        while x <= X1:
            y = Y0
            while y <= Y1:
                px, py = x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter)
                y += step
                d = shore(px, py)
                if d > -2200:
                    continue
                patch = mm._clearing(px, py, int(seed) + 7)        # 0..1, ~30 m cells
                fine = mm._clearing(px * 3.1, py * 3.1, int(seed) + 11)
                if layer == 'grass':
                    keep = (.45 + .55 * patch) * (.7 + .3 * fine)
                else:
                    keep = .25 + .5 * (1 - patch) * fine
                keep *= min(1.0, (-d - 2200) / 1500.0)               # thins out towards the beach sand
                if layer == 'grass':   # 08/11 (Sergio, photo: "galhos e folhas no chão"): under the canopy (60 m+ inland)
                    keep *= .25 + .75 * (1 - min(1.0, max(0.0, (-d - 6000) / 3000.0)))   # the grass gives way to the leaf litter
                if rng.random() > keep:
                    continue
                if (px - 4000) ** 2 + (py - 38900) ** 2 < 1500 ** 2:
                    reject('summit house')
                    continue
                if on_trail(px, py):
                    reject('trail')
                    continue
                hit = mm._hit(world, px, py, [])
                if not hit or not hit[2]:
                    reject('miss')
                    continue
                label = hit[2].get_actor_label()
                if label not in ground_ok:
                    reject('trail' if 'trilha' in label else 'other')
                elif label == 'Maré · Ground' and py < 12000:
                    reject('village')
                elif hit[1].z < .7:
                    reject('steep')
                elif hit[0].z < 20:
                    reject('wet')
                else:
                    slug, (h0, h1), stretch = _pick_cover(rng, table)
                    n = hit[1]
                    rows.setdefault(slug, []).append((hit[0].x, hit[0].y, hit[0].z, rng.uniform(-180, 180),
                                                      rng.uniform(h0, h1) * 100, stretch, layer, (n.x, n.y, n.z)))
            x += step
    root = actors.spawn_actor_from_class(unreal.Actor, unreal.Vector())
    root.set_actor_label(COVER_LABEL)
    root.tags = [unreal.Name('MareGenerated'), unreal.Name('MareIslandCover')]
    root.set_folder_path('Nature/Island')
    from editor_toolset.toolsets.actor import ActorTools
    summary = {}
    for slug, items in rows.items():
        mesh = mm._mesh(slug)
        comp = ActorTools.add_component(root, unreal.HierarchicalInstancedStaticMeshComponent.static_class(), 'HISM_cover_' + slug)
        comp.set_static_mesh(mesh)
        if COVER_LAWN_GREEN and slug in ('World_2062', 'World_2071'):     # the lawn green of the village grass (mare_grass)
            name = 'Grass_Common_Short' if slug == 'World_2062' else 'Grass_Wispy_Short'
            for i, slot in enumerate(mesh.static_materials):
                comp.set_material(i, mare_grass.grass_material(slot.material_interface, name + '_' + str(i)))
        comp.set_mobility(unreal.ComponentMobility.STATIC)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_editor_property('cast_shadow', False)
        comp.set_editor_property('affect_distance_field_lighting', False)
        comp.set_editor_property('affect_dynamic_indirect_lighting', False)
        grass = items[0][6] == 'grass'
        comp.set_editor_property('instance_start_cull_distance', 2500 if grass else 5000)
        comp.set_editor_property('instance_end_cull_distance', 4000 if grass else 7000)
        b = mesh.get_bounds()
        tall = 2 * b.box_extent.z or 1.0
        base = b.origin.z - b.box_extent.z
        transforms = []
        for x, y, z, yaw, height, stretch, _, n in items:
            s = height / tall
            up = unreal.Vector(*n)
            rot = unreal.MathLibrary.compose_rotators(unreal.Rotator(roll=0, pitch=0, yaw=yaw), unreal.MathLibrary.make_rot_from_z(up))
            sink = -base * s + 4           # the clump's base 4 cm into the ground
            transforms.append(unreal.Transform(unreal.Vector(x - up.x * sink, y - up.y * sink, z - up.z * sink), rot,
                                               unreal.Vector(s * stretch, s * stretch, s)))
        comp.add_instances(transforms, False, True)
        summary[slug] = len(items)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report = {'seed': seed, 'instances': summary, 'total': sum(summary.values()), 'rejected': rejected}
    (DATA / 'island_cover.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    return json.dumps(report)


def forest_lumen(arg='0'):
    """08/11: the island forest (33k trees, shrubs, palms, rocks) out of the Lumen surface cache ('0') or back in ('1').
    With them in, the woods first seen at night showed the daylight still cached on their cards (the cache only updates
    near the camera): bright green at 22h. Out, they still receive Lumen GI; the terrain keeps its cards. Saves."""
    on = arg.strip() == '1'
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in actors.get_all_level_actors():
        if a.get_actor_label() in (FOREST_LABEL, COVER_LABEL):
            for c in a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
                c.set_editor_property('affect_dynamic_indirect_lighting', on)
                c.set_editor_property('affect_distance_field_lighting', on and a.get_actor_label() == FOREST_LABEL)
                n += 1
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'components': n, 'lumen': on})
