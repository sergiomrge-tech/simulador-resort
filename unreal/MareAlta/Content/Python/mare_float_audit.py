"""Global floating-prop audit: compare each prop instance's real mesh base with the surface below.

scan -> D:/CodexTemp/float-audit/report.json ; fix -> lower props resting 3..120 cm above a support,
updating both the level instances and Content/Data/world.json (so a rebuild keeps the fix)."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
DATA = ROOT / 'Content/Data'
OUT = Path('D:/CodexTemp/float-audit')
# Things that legitimately hang, fly, float on water or are attached to people/buildings.
SKIP = ('lamp', 'lantern', 'bulb', 'globe', 'sign', 'placa', 'flag', 'bandeir', 'bunting', 'rope', 'corda', 'net', 'rede',
        'cloud', 'gull', 'gaivota', 'bird', 'boat', 'barco', 'ship', 'navio', 'cruise', 'whale', 'baleia', 'hair', 'chama', 'flame',
        'fan', 'ventilador', 'shelf', 'prateleira', 'frame', 'quadro', 'curtain', 'cortina', 'window', 'janela', 'door', 'porta',
        'roof', 'telhado', 'awning', 'toldo', 'wire', 'fio', 'neon', 'letreiro', 'text', 'clock', 'buoy', 'boia', 'kite', 'pipa',
        'umbrella_top', 'canopy', 'ac_unit', 'antenna', 'antena', 'bracket', 'hanging', 'pendant', 'chain', 'swing', 'balanço',
        'venezianas', 'shutter', 'balcony', 'sacada', 'gutter', 'calha', 'pier', 'cais', 'deck', 'stair', 'escada', 'step', 'degrau')
GROUND_ACTORS = ('Maré · Ground', 'PCG', 'Mare · Vegetação', 'Hotel lobby')


def _skip(label):
    low = label.lower()
    return any(s in low for s in SKIP) or any(label.startswith(g) for g in GROUND_ACTORS)


def _bottom(mesh, t):
    b = mesh.get_bounds()
    pts = [t.transform_location(b.origin + unreal.Vector(dx * b.box_extent.x, dy * b.box_extent.y, dz * b.box_extent.z))
           for dx in (-1, 1) for dy in (-1, 1) for dz in (-1, 1)]
    lo = min(p.z for p in pts)
    cx = sum(p.x for p in pts) / 8
    cy = sum(p.y for p in pts) / 8
    span = max(max(p.x for p in pts) - min(p.x for p in pts), max(p.y for p in pts) - min(p.y for p in pts))
    return lo, cx, cy, span, max(p.z for p in pts) - lo


def scan():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    rows = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = a.get_actor_label()
        if not label.startswith('Maré · ') or _skip(label) or label.startswith('Maré · @'):
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh = c.static_mesh
            if not mesh or not c.is_visible():
                continue
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                lo, cx, cy, span, height = _bottom(mesh, t)
                if span > 600 or height > 800:          # buildings and big structures
                    continue
                # Supported if any of five footprint samples touches something below the mesh base.
                gaps, support = [], None
                b = mesh.get_bounds()
                for fx, fy in ((0, 0), (-.6, -.6), (.6, -.6), (-.6, .6), (.6, .6)):
                    p = t.transform_location(b.origin + unreal.Vector(fx * b.box_extent.x, fy * b.box_extent.y, 0))
                    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(p.x, p.y, lo + 15), unreal.Vector(p.x, p.y, lo - 300),
                                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a], unreal.DrawDebugTrace.NONE, True)
                    if hit:
                        tt = hit.to_tuple()
                        gaps.append(lo - tt[4].z)
                        support = tt[9].get_actor_label() if tt[9] else support
                if not gaps:
                    continue
                gap = min(gaps)
                if gap > 3:
                    rows.append({'actor': label, 'mesh': mesh.get_name(), 'index': i, 'gap_cm': round(gap, 1),
                                 'at': [round(cx), round(cy), round(lo)], 'support': support, 'size_cm': [round(span), round(height)]})
    rows.sort(key=lambda r: -r['gap_cm'])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'report.json').write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding='utf-8')
    summary = {}
    for r in rows:
        summary[r['actor']] = summary.get(r['actor'], 0) + 1
    return {'floating': len(rows), 'by_actor': dict(sorted(summary.items(), key=lambda kv: -kv[1])[:40]),
            'worst': rows[:15]}


LOOSE = ('orange', 'lemon', 'food_lime_01', 'food_lychee_01', 'food_apple_01', 'food_pomegranate_01', 'coconut_green',
         'food_pears_asian_01_a', 'food_pears_asian_01_b', 'food_pears_asian_01_c', 'food_pears_asian_01_d', 'food_pears_asian_01_e',
         'cup_plastic', 'glass_juice', 'pineapple', 'shell_a', 'shell_b', 'shell_c')


def _support_gap(world, comp, index, mesh, t, lo):
    """Smallest gap below five footprint samples, counting other instances of the same pile."""
    b = mesh.get_bounds()
    best = None
    for fx, fy in ((0, 0), (-.5, -.5), (.5, -.5), (-.5, .5), (.5, .5)):
        p = t.transform_location(b.origin + unreal.Vector(fx * b.box_extent.x, fy * b.box_extent.y, 0))
        hits = unreal.SystemLibrary.line_trace_multi(world, unreal.Vector(p.x, p.y, lo + 6), unreal.Vector(p.x, p.y, lo - 120),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True) or []
        for h in hits:
            tt = h.to_tuple()
            if tt[10] == comp and tt[13] == index:      # the instance itself
                continue
            gap = lo - tt[4].z
            best = gap if best is None else min(best, gap)
            break
    return best


def fix():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    from mare_world_builder import transform
    data = json.loads((DATA / 'world.json').read_text(encoding='utf-8-sig'))
    moved = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = a.get_actor_label()
        if not label.startswith('Maré · ') or label[7:] not in LOOSE:
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh = c.static_mesh
            if not mesh:
                continue
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                lo = _bottom(mesh, t)[0]
                gap = _support_gap(world, c, i, mesh, t, lo)
                if gap is None or not (2.5 < gap <= 40):
                    continue
                old = unreal.Vector(t.translation.x, t.translation.y, t.translation.z)
                t.translation = unreal.Vector(old.x, old.y, old.z - gap + 0.4)
                c.update_instance_transform(i, t, True, True, True)
                # Keep the exported layout in sync (Godot axes, metres: UE z is Godot y).
                for row in data['instances']:
                    if row['name'] != label[7:]:
                        continue
                    rt = transform(row['transform'])
                    if rt is not None and (rt.translation - old).length() < 1.0:
                        row['transform']['position'][1] -= (gap - 0.4) / 100
                        break
                moved.append({'actor': label, 'index': i, 'lowered_cm': round(gap - 0.4, 1), 'at': [round(old.x), round(old.y), round(old.z)]})
    (DATA / 'world.json').write_text(json.dumps(data, ensure_ascii=False, indent='\t'), encoding='utf-8')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'fixed.json').write_text(json.dumps(moved, indent=1, ensure_ascii=False), encoding='utf-8')
    return {'moved': len(moved), 'sample': moved[:12]}


def place(spec):
    """Move prop instances onto a surface: "name|x0|y0|z0|x|y|z_surface[|scale];..." (world cm). The instance is the one
    of that prop name whose pivot is within 5 cm of (x0, y0, z0) - names repeat across actors, so never by index. It keeps
    its rotation (an optional factor rescales it); its mesh base lands on z_surface. Level instance and
    Content/Data/world.json both change."""
    from mare_world_builder import transform
    data = json.loads((DATA / 'world.json').read_text(encoding='utf-8-sig'))
    moved = []
    for item in spec.split(';'):
        name, x0, y0, z0, x, y, z, *factor = item.split('|')
        factor = float(factor[0]) if factor else 1.0
        at = unreal.Vector(float(x0), float(y0), float(z0))
        x, y, z = float(x), float(y), float(z)
        hits = []
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            if a.get_actor_label() != 'Maré · ' + name:
                continue
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                for i in range(c.get_instance_count()):
                    if (c.get_instance_transform(i, True).translation - at).length() < 5:
                        hits.append((c, i))
        if len(hits) != 1:
            moved.append({'name': name, 'at': [x0, y0, z0], 'error': f'{len(hits)} instances match'})
            continue
        c, index = hits[0]
        t = c.get_instance_transform(index, True)
        t.scale3d = t.scale3d * factor
        lo = _bottom(c.static_mesh, t)[0]
        old = unreal.Vector(t.translation.x, t.translation.y, t.translation.z)
        new = unreal.Vector(x, y, old.z + (z - lo))
        t.translation = new
        c.update_instance_transform(index, t, True, True, True)
        for row in data['instances']:
            if row['name'] != name:
                continue
            rt = transform(row['transform'])
            if rt is not None and (rt.translation - old).length() < 1.0:
                pos = row['transform']['position']      # Godot metres: UE (x, y, z) cm = (p0, p2, p1) * 100
                pos[0], pos[2], pos[1] = new.x / 100, new.y / 100, pos[1] + (new.z - old.z) / 100
                row['transform']['basis'] = [[v * factor for v in r] for r in row['transform']['basis']]
                break
        moved.append({'name': name, 'from': [round(old.x), round(old.y), round(old.z)], 'to': [round(new.x), round(new.y), round(new.z)]})
    if any('error' not in m for m in moved):
        (DATA / 'world.json').write_text(json.dumps(data, ensure_ascii=False, indent='	'), encoding='utf-8')
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return moved


def debug(name):
    from mare_world_builder import transform
    data = json.loads((DATA / 'world.json').read_text(encoding='utf-8-sig'))
    rows = [transform(r['transform']).translation for r in data['instances'] if r['name'] == name]
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label() != 'Maré · ' + name:
            continue
        out.append({'actor_loc': str(a.get_actor_location())})
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            for i in range(min(4, c.get_instance_count())):
                p = c.get_instance_transform(i, True).translation
                out.append({'i': i, 'pivot': [p.x, p.y, p.z], 'nearest_row_cm': min((r - p).length() for r in rows)})
    return out


def sync():
    """Copy current instance heights of loose props back to world.json (same name, same X/Y)."""
    from mare_world_builder import transform
    data = json.loads((DATA / 'world.json').read_text(encoding='utf-8-sig'))
    updated = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = a.get_actor_label()
        if not label.startswith('Maré · ') or label[7:] not in LOOSE:
            continue
        rows = [r for r in data['instances'] if r['name'] == label[7:]]
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            for i in range(c.get_instance_count()):
                p = c.get_instance_transform(i, True).translation
                for r in rows:
                    rt = transform(r['transform'])
                    if rt is None:
                        continue
                    q = rt.translation
                    if abs(q.x - p.x) < 0.5 and abs(q.y - p.y) < 0.5 and 0.5 < abs(q.z - p.z) < 41:
                        r['transform']['position'][1] = p.z / 100
                        updated += 1
                        break
    (DATA / 'world.json').write_text(json.dumps(data, ensure_ascii=False, indent='	'), encoding='utf-8')
    return {'rows_updated': updated}


def near(x, y, r):
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            m = c.static_mesh
            if not m:
                continue
            for i in range(c.get_instance_count()):
                p = c.get_instance_transform(i, True).translation
                if (p.x - x) ** 2 + (p.y - y) ** 2 < r * r and p.z < 900:
                    b = m.get_bounds()
                    out.append({'actor': a.get_actor_label(), 'mesh': m.get_name(), 'at': [round(p.x), round(p.y), round(p.z)],
                                'tris': m.get_num_triangles(0), 'size': [round(b.box_extent.x * 2), round(b.box_extent.y * 2), round(b.box_extent.z * 2)]})
    return out


def lowpoly(limit=600):
    """Meshes with few triangles for their size, per mesh: triangles, world size of the biggest instance (cm),
    instance count, actors and one location. Boxes (12 triangles) are walls/floors and stay out. Report in
    D:/CodexTemp/float-audit/lowpoly.json, biggest first, for triage by capture."""
    rows = {}
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            m = c.static_mesh
            if not m or c.get_instance_count() == 0:
                continue
            tris = m.get_num_triangles(0)
            if tris <= 12 or tris > limit:
                continue
            e = m.get_bounds().box_extent
            r = rows.setdefault(m.get_name(), {'mesh': m.get_name(), 'path': m.get_path_name(), 'tris': tris, 'size': 0, 'count': 0, 'actors': set(), 'at': None})
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                s = t.scale3d
                size = 2 * max(e.x * abs(s.x), e.y * abs(s.y), e.z * abs(s.z))
                r['count'] += 1
                if size > r['size']:
                    r['size'], p = size, t.translation
                    r['at'] = [round(p.x), round(p.y), round(p.z)]
            r['actors'].add(a.get_actor_label())
    out = sorted(rows.values(), key=lambda r: -r['size'])
    for r in out:
        r['size'] = round(r['size'])
        r['actors'] = sorted(r['actors'])[:4]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'lowpoly.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    return {'meshes': len(out), 'file': str(OUT / 'lowpoly.json')}


def primitives():
    """Shape of every mesh in lowpoly.json, from its vertices normalised to the bounds: 'sphere' (constant distance
    from the centre) or 'cylinder_<axis>' (constant distance from an axis, caps aside). Code-made spheres and
    cylinders are banned as props (CLAUDE.md); walls and floors are boxes and stay out. -> primitives.json."""
    import statistics
    rows = json.loads((OUT / 'lowpoly.json').read_text(encoding='utf-8'))
    out = []
    for r in rows:
        m = unreal.load_asset(r['path'])
        if not m:
            r['shape'] = 'no asset'
            out.append(r)
            continue
        b = m.get_bounds()
        o, e = b.origin, b.box_extent
        if min(e.x, e.y, e.z) < .01:
            continue
        verts = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(m, 0, 0)[0]
        pts = [((v.x - o.x) / e.x, (v.y - o.y) / e.y, (v.z - o.z) / e.z) for v in verts]
        if len(pts) < 8:
            continue
        shape = ''
        d3 = [(x * x + y * y + z * z) ** .5 for x, y, z in pts]
        if statistics.pstdev(d3) < .04 and .93 < statistics.mean(d3) < 1.03:     # rounded-box corners sit at ~1.7
            shape = 'sphere'
        else:
            for axis, (i, j) in (('x', (1, 2)), ('y', (0, 2)), ('z', (0, 1))):
                rad = [(p[i] ** 2 + p[j] ** 2) ** .5 for p in pts]
                rim = [q for q in rad if q > .5]
                if len(rim) > .7 * len(rad) and statistics.pstdev(rim) < .03 and .95 < statistics.mean(rim) < 1.03:
                    shape = 'cylinder_' + axis
                    break
        if shape:
            r['shape'] = shape
            out.append(r)
    (OUT / 'primitives.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    return {'primitives': len(out)}


def _row(t):
    """UE transform -> world.json row (inverse of mare_world_builder.transform): Godot basis rows and metres."""
    X = t.rotation.rotate_vector(unreal.Vector(1, 0, 0)) * t.scale3d.x
    Y = t.rotation.rotate_vector(unreal.Vector(0, 1, 0)) * t.scale3d.y
    Z = t.rotation.rotate_vector(unreal.Vector(0, 0, 1)) * t.scale3d.z
    return {'basis': [[X.x, X.z, X.y], [Z.x, Z.z, Z.y], [Y.x, Y.z, Y.y]],
            'position': [t.translation.x / 100, t.translation.z / 100, t.translation.y / 100]}


def _hide_mesh(name, rows):
    from mare_world_builder import transform
    n = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not c.static_mesh or c.static_mesh.get_name() != name:
                continue
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                old_at = unreal.Vector(t.translation.x, t.translation.y, t.translation.z)
                t.scale3d = unreal.Vector(.001, .001, .001)
                c.update_instance_transform(i, t, True, True, True)
                for row in rows:
                    rt = transform(row['transform'])
                    if rt is not None and (rt.translation - old_at).length() < 1.0:
                        row['transform'] = _row(t)
                        break
                n += 1
    return n


def swapfit(spec):
    """Replace a code-made primitive prop by a real model, refitted per instance: "World_NNNN=/Game/path:mode[:sink];..."
    mode fit  - uniform scale to the old footprint, old yaw kept (rocks; Nanite meshes);
         log  - the new mesh's long axis along the old one, same length (driftwood for the cylinder logs);
         same - the old rotation at scale 1 (new model built in the old mesh's frame);
         hide - (path ignored) shrink a part that the replacement model already includes;
         keep - as same, without re-seating on the surface (stacked pieces such as luggage on a cart);
         foot - real size, old yaw, tilted to the sand normal, every other instance mirrored (left/right).
    Each instance then rests on what is below it (traced ignoring its own actor), sunk by `sink` cm. Level
    instances, Content/Data/world.json rows and imported_meshes.json (old mesh -> new path) all change."""
    import math, random
    from mare_world_builder import transform
    data = json.loads((DATA / 'world.json').read_text(encoding='utf-8-sig'))
    mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    rows_by_mesh = {}
    for row in data['instances']:
        rows_by_mesh.setdefault(f"World_{row['mesh_index']:04d}", []).append(row)
    report = {}
    for item in spec.split(';'):
        old_name, rest = item.split('=')
        path, mode, *sink = rest.split(':')
        sink = float(sink[0]) if sink else 0.0
        if mode == 'hide':   # part absorbed by a replacement model: shrink it (epsilon keeps bounds/culling sane)
            report[old_name] = _hide_mesh(old_name, rows_by_mesh.get(old_name, []))
            continue
        new = unreal.load_asset(path)
        ne = new.get_bounds().box_extent
        long_axis = max(range(3), key=lambda k: (ne.x, ne.y, ne.z)[k])
        done = 0
        rnd = random.Random(old_name)
        old_mesh = unreal.load_asset(mapping.get(old_name, ''))
        labels = {'Maré · ' + r['name'] for r in rows_by_mesh.get(old_name, [])}
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                # by mesh, or (a rerun after a partial swap) by the actor label exported from Godot
                if not c.static_mesh or not (c.static_mesh.get_name() == old_name or
                                             (c.static_mesh == new and a.get_actor_label() in labels and old_mesh)):
                    continue
                oe = (old_mesh or c.static_mesh).get_bounds().box_extent
                olds = [c.get_instance_transform(i, True) for i in range(c.get_instance_count())]
                c.set_static_mesh(new)
                for i, t in enumerate(olds):
                    old_at = unreal.Vector(t.translation.x, t.translation.y, t.translation.z)
                    sc = t.scale3d
                    if mode == 'log':
                        ax = max(range(3), key=lambda k: (oe.x * abs(sc.x), oe.y * abs(sc.y), oe.z * abs(sc.z))[k])
                        length = 2 * (oe.x * abs(sc.x), oe.y * abs(sc.y), oe.z * abs(sc.z))[ax]
                        d = t.rotation.rotate_vector([unreal.Vector(1, 0, 0), unreal.Vector(0, 1, 0), unreal.Vector(0, 0, 1)][ax])
                        k = length / (2 * (ne.x, ne.y, ne.z)[long_axis])
                        yaw = math.degrees(math.atan2(d.y, d.x)) - (90 if long_axis == 1 else 0)
                        rot = unreal.Rotator(roll=rnd.uniform(-180, 180) if long_axis == 0 else 0,
                                             pitch=rnd.uniform(-180, 180) if long_axis == 1 else 0, yaw=yaw)
                        scale = unreal.Vector(k, k, k)
                    elif mode in ('same', 'keep'):   # new mesh built in the old one's frame
                        rot = t.rotation.rotator()
                        scale = unreal.Vector(1, 1, 1)
                    elif mode == 'fit':
                        footprint = 2 * max(oe.x * abs(sc.x), oe.y * abs(sc.y))
                        k = footprint / (2 * max(ne.x, ne.y))
                        rot = unreal.Rotator(roll=0, pitch=0, yaw=t.rotation.rotator().yaw + rnd.uniform(-30, 30))
                        scale = unreal.Vector(k, k, k)
                    else:   # foot: the Godot trail always walks +X (a mirrored instance reads back as yaw+180, so not t)
                        rot = unreal.Rotator(roll=0, pitch=0, yaw=rnd.uniform(-8, 8))
                        scale = unreal.Vector(1, -1 if i % 2 else 1, 1)
                    nt = unreal.Transform(old_at, rot, scale)
                    hit = unreal.SystemLibrary.line_trace_single(world, old_at + unreal.Vector(0, 0, 200), old_at - unreal.Vector(0, 0, 300),
                                                                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a], unreal.DrawDebugTrace.NONE, True)
                    if mode == 'keep':     # stacked or held pieces: the old pivot already sits right
                        hit = None
                    if hit and mode == 'foot':
                        # a flat imprint must follow the sand slope, or its upper half sinks into the beach
                        n = hit.to_tuple()[7]
                        fwd = rot.get_forward_vector()
                        nt = unreal.Transform(old_at, unreal.MathLibrary.make_rot_from_zx(n, fwd), scale)
                    if hit:
                        lo = _bottom(new, nt)[0]
                        nt.translation = unreal.Vector(old_at.x, old_at.y, old_at.z + hit.to_tuple()[5].z - lo - sink)
                    c.update_instance_transform(i, nt, True, True, True)
                    for row in rows_by_mesh.get(old_name, []):
                        rt = transform(row['transform'])
                        if rt is not None and (rt.translation - old_at).length() < 1.0:
                            row['transform'] = _row(nt)
                            break
                    done += 1
        mapping[old_name] = path
        report[old_name] = done
    (DATA / 'world.json').write_text(json.dumps(data, ensure_ascii=False, indent='	'), encoding='utf-8')
    (DATA / 'imported_meshes.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return report


def reimport_props(names):
    """Reimport refined scene meshes into their existing assets (instances update in place)."""
    import mare_hotel_lobby
    mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
    out = []
    for name in names:
        path = mapping[name]
        folder = path.rsplit('/', 1)[0]
        mesh = mare_hotel_lobby._import(ROOT / 'SourceArt/Models' / (name + '.gltf'), folder, name, True)
        mare_hotel_lobby._complex_collision(mesh)
        out.append({'mesh': name, 'triangles': mesh.get_num_triangles(0)})
    return out


BROKEN = ('Maré · Copas', 'Maré · CopasCrista')   # Godot multimesh crowns exported without transforms


def hide_broken():
    """The 'Copas' crowns were exported with every instance at the world origin, which is the
    centre of the pousada pool: a dark bush inside the water. Hide them (reversible, no collision)."""
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label() in BROKEN:
            a.set_actor_hidden_in_game(True)
            a.set_is_temporarily_hidden_in_editor(True)
            a.set_actor_enable_collision(False)
            for c in a.get_components_by_class(unreal.PrimitiveComponent):
                c.set_visibility(False, True)
            a.tags = list(a.tags) + [unreal.Name('MareBrokenExportHidden')]
            out.append(a.get_actor_label())
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return out


def restore_stacked(source):
    """Put the MultiMesh groups removed by remove_stacked() back where Godot draws them, using the
    per-instance transforms from tools/ue58/export_multimesh.gd (Godot run with a window). Groups are
    paired in creation order by instance count (node names shift between runs); low-poly canopy
    blobs (Copas*) stay out because the hills now carry real CC0 trees."""
    import difflib
    import re
    from collections import defaultdict
    from mare_world_builder import transform
    fresh = json.loads(Path(source).read_text(encoding='utf-8'))
    removed_doc = json.loads((DATA / 'stacked_origin_removed.json').read_text(encoding='utf-8'))
    order = lambda n: int(re.sub(r'\D', '', n.split('#')[0]) or 0)
    old = defaultdict(list)
    for r in removed_doc['rows']:
        if r['name'].startswith('@MultiMeshInstance3D@'):
            old[r['name']].append(r)
    old_names = sorted(old, key=order)
    new_names = sorted((n for n in fresh if n.startswith('@MultiMeshInstance3D@')), key=order)
    matcher = difflib.SequenceMatcher(None, [len(old[n]) for n in old_names], [fresh[n]['count'] for n in new_names], autojunk=False)
    # A lone pairing of very common counts (8, 10…) is not evidence; keep runs of 3+ groups.
    pairs = [(old_names[b.a + k], new_names[b.b + k]) for b in matcher.get_matching_blocks() if b.size >= 3 for k in range(b.size)]
    mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
    aliases = json.loads((DATA / 'model_aliases.json').read_text(encoding='utf-8-sig'))
    components = {}
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label().startswith('Maré · '):
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                if c.static_mesh:
                    components.setdefault(c.static_mesh.get_path_name().split('.')[0], c)
    data = json.loads((DATA / 'world.json').read_text(encoding='utf-8-sig'))
    restored, groups, used = 0, {}, set()
    for old_name, new_name in pairs:
        rows = old[old_name]
        if len(rows) < 5:
            continue
        key = aliases.get(f"World_{rows[0]['mesh_index']:04d}", f"World_{rows[0]['mesh_index']:04d}")
        native = mapping.get(key)
        comp = components.get(native.split('.')[0]) if native else None
        if comp is None:
            continue
        xforms = []
        for row, t in zip(rows, fresh[new_name]['transforms']):
            row = dict(row, transform=t)
            ut = transform(t)
            if ut is None:
                continue
            data['instances'].append(row)
            xforms.append(ut)
        comp.add_instances(xforms, False, True)
        restored += len(xforms)
        groups[old_name + ' -> ' + new_name] = len(xforms)
        used.add(old_name)
    data_rows = [r for r in removed_doc['rows'] if r['name'] not in used]
    (DATA / 'world.json').write_text(json.dumps(data, ensure_ascii=False, indent='	'), encoding='utf-8')
    removed_doc['rows'] = data_rows
    removed_doc['restored'] = removed_doc.get('restored', 0) + restored
    (DATA / 'stacked_origin_removed.json').write_text(json.dumps(removed_doc, ensure_ascii=False, indent=1), encoding='utf-8')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'restored': restored, 'groups': len(groups), 'still_removed': len(data_rows), 'detail': groups}


def remove_orphan_accessories():
    """Godot hotel guests are skinned (not exported), but their hair and camera props are static and
    were exported alone, floating over the hotel chairs. Drop them; the UE guests carry their own hair."""
    prefixes = ('Hair_', 'Camera_')
    removed = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if a.get_actor_label().startswith(tuple('Maré · ' + p for p in prefixes)):
            removed += sum(c.get_instance_count() for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent))
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
    data = json.loads((DATA / 'world.json').read_text(encoding='utf-8-sig'))
    before = len(data['instances'])
    data['instances'] = [r for r in data['instances'] if not r['name'].startswith(prefixes)]
    (DATA / 'world.json').write_text(json.dumps(data, ensure_ascii=False, indent='	'), encoding='utf-8')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'level_instances_removed': removed, 'world_rows_removed': before - len(data['instances'])}


def remove_stacked():
    """Godot MultiMesh groups exported without per-instance transforms ended up stacked at the
    world origin (centre of the pousada pool). Remove small props pinned exactly at (0,0,0) from
    the level and from world.json; the removed rows are kept in stacked_origin_removed.json."""
    from mare_world_builder import transform
    removed = {}
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if not a.get_actor_label().startswith('Maré · '):
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            m = c.static_mesh
            if not m:
                continue
            e = m.get_bounds().box_extent
            if max(e.x, e.y, e.z) * 2 > 400:
                continue
            doomed = [i for i in range(c.get_instance_count()) if c.get_instance_transform(i, True).translation.length() < 1.0]
            if doomed:
                c.remove_instances(doomed)
                removed[a.get_actor_label() + ' / ' + m.get_name()] = len(doomed)
    data = json.loads((DATA / 'world.json').read_text(encoding='utf-8-sig'))
    mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
    aliases = json.loads((DATA / 'model_aliases.json').read_text(encoding='utf-8-sig'))
    keep, dropped = [], []
    for r in data['instances']:
        key = aliases.get(f"World_{r['mesh_index']:04d}", f"World_{r['mesh_index']:04d}")
        small = False
        if all(abs(v) < 1e-6 for v in r['transform']['position']) and key in mapping:
            mesh = unreal.load_asset(mapping[key])
            small = mesh is not None and max(mesh.get_bounds().box_extent.x, mesh.get_bounds().box_extent.y, mesh.get_bounds().box_extent.z) * 2 <= 400
        (dropped if small else keep).append(r)
    data['instances'] = keep
    (DATA / 'world.json').write_text(json.dumps(data, ensure_ascii=False, indent='	'), encoding='utf-8')
    (DATA / 'stacked_origin_removed.json').write_text(json.dumps({'reason': 'Godot MultiMesh exported without per-instance transforms; all stacked at origin', 'rows': dropped}, ensure_ascii=False, indent=1), encoding='utf-8')
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {'level_instances_removed': sum(removed.values()), 'groups': removed, 'world_rows_removed': len(dropped)}


def palm_material(names):
    import mare_materials, importlib
    importlib.reload(mare_materials)
    mat = mare_materials.build_palm_frond()
    mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
    out = []
    for name in names:
        mesh = unreal.load_asset(mapping[name])
        for j, slot in enumerate(mesh.static_materials):
            if slot.material_slot_name and 'palm_frond_geo' in str(slot.material_slot_name) or (slot.material_interface and 'palm_frond_geo' in slot.material_interface.get_name()):
                mesh.set_material(j, mat)
                out.append([name, j])
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return out


def run(action, arg=''):
    if action == 'recompile':
        out = {}
        for path in arg.split(','):
            m = unreal.load_asset(path)
            out[m.get_name()] = [str(e) for e in unreal.MaterialEditingLibrary.recompile_material(m)]
        return out
    if action == 'settransform':
        # "name|x0|y0|z0|x|y|z|yaw": move and turn one exported instance (matched by name + pivot within 5 cm),
        # scale kept; level and world.json. For pieces that must change wall (rotation, unlike place).
        from mare_world_builder import transform
        name, x0, y0, z0, x, y, z, yaw = arg.split('|')
        at = unreal.Vector(float(x0), float(y0), float(z0))
        data = json.loads((DATA / 'world.json').read_text(encoding='utf-8-sig'))
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            if a.get_actor_label() != 'Maré · ' + name:
                continue
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                for i in range(c.get_instance_count()):
                    t = c.get_instance_transform(i, True)
                    if (t.translation - at).length() >= 5:
                        continue
                    nt = unreal.Transform(unreal.Vector(float(x), float(y), float(z)), unreal.Rotator(roll=0, pitch=0, yaw=float(yaw)), t.scale3d)
                    c.update_instance_transform(i, nt, True, True, True)
                    for row in data['instances']:
                        rt = transform(row['transform']) if row['name'] == name else None
                        if rt is not None and (rt.translation - at).length() < 1.0:
                            row['transform'] = _row(nt)
                            break
                    (DATA / 'world.json').write_text(json.dumps(data, ensure_ascii=False, indent='	'), encoding='utf-8')
                    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
                    return {'moved': name, 'to': [x, y, z, yaw]}
        return {'error': 'not found'}
    if action == 'rays':
        # "x,y,z": 16 horizontal traces (room layout: distance to the walls and what they hit) + floor/ceiling
        import math
        x, y, z = [float(v) for v in arg.split(',')]
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        o = unreal.Vector(x, y, z)
        out = {}
        dirs = [(f'{k * 22.5:.0f}', unreal.Vector(math.cos(math.radians(k * 22.5)), math.sin(math.radians(k * 22.5)), 0)) for k in range(16)]
        for name, d in dirs + [('down', unreal.Vector(0, 0, -1)), ('up', unreal.Vector(0, 0, 1))]:
            hit = unreal.SystemLibrary.line_trace_single(world, o, o + d * 2000, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
                                                        unreal.DrawDebugTrace.NONE, True)
            if hit:
                t = hit.to_tuple()
                out[name] = [round((t[5] - o).length()), t[9].get_actor_label() if t[9] else '', t[10].static_mesh.get_name() if t[10] and hasattr(t[10], 'static_mesh') and t[10].static_mesh else '']
        return out
    if action == 'nanite':
        # "path,path|1": Nanite on (1) or off (0) for static meshes
        paths, on = arg.split('|')
        out = {}
        for path in paths.split(','):
            m = unreal.load_asset(path)
            st = m.get_editor_property('nanite_settings')
            st.set_editor_property('enabled', on == '1')
            m.set_editor_property('nanite_settings', st)
            unreal.EditorAssetLibrary.save_loaded_asset(m, False)
            out[m.get_name()] = on
        return out
    if action == 'swapfit':
        return swapfit(arg)
    if action == 'primitives':
        return primitives()
    if action == 'lowpoly':
        return lowpoly(int(arg or 600))
    if action == 'bbox':
        out = {}
        for path in arg.split(','):
            b = unreal.load_asset(path).get_bounding_box()
            out[path.split('.')[-1]] = {'min': [round(b.min.x), round(b.min.y), round(b.min.z)], 'max': [round(b.max.x), round(b.max.y), round(b.max.z)]}
        return out
    if action == 'surface':
        # "x,y[,ztop]": first surface hit going down from ztop (default 1500), editor world.
        v = [float(t) for t in arg.split(',')]
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        top = v[2] if len(v) > 2 else 1500
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(v[0], v[1], top), unreal.Vector(v[0], v[1], -2000),
                                                    unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        if not hit:
            return None
        t = hit.to_tuple()
        comp = t[10]
        mat = ''
        if comp and isinstance(comp, unreal.PrimitiveComponent):
            mi = comp.get_material(0)
            mat = mi.get_name() if mi else ''
            if isinstance(comp, unreal.StaticMeshComponent) and comp.static_mesh:
                mat += ' / ' + comp.static_mesh.get_name()
        return {'z': round(t[5].z, 1), 'actor': t[9].get_actor_label() if t[9] else '', 'mat': mat}
    if action == 'near':
        x, y, r = (float(t) for t in arg.split(','))
        return near(x, y, r)
    if action == 'place':
        return place(arg)
    if action == 'palmmat':
        return palm_material(arg.split())
    if action == 'stacked':
        return remove_stacked()
    if action == 'hidebroken':
        return hide_broken()
    if action == 'reimport':
        return reimport_props(arg.split())
    if action == 'bounds':
        mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
        out = {}
        for n in arg.split(','):
            b = unreal.load_asset(mapping[n]).get_bounds()
            out[n] = {'origin': [round(b.origin.x), round(b.origin.y), round(b.origin.z)], 'extent': [round(b.box_extent.x), round(b.box_extent.y), round(b.box_extent.z)]}
        return out
    if action == 'mesh_info':
        out = {}
        for path in arg.split(','):
            m = unreal.load_asset(path)
            out[path] = {'tris': m.get_num_triangles(0), 'nanite': m.get_editor_property('nanite_settings').enabled, 'size': [round(v * 2) for v in (m.get_bounds().box_extent.x, m.get_bounds().box_extent.y, m.get_bounds().box_extent.z)]}
        return out
    if action == 'palmfab':
        import mare_materials, importlib
        importlib.reload(mare_materials)
        mat = mare_materials.build_palm_fab()
        mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
        for name in arg.split():
            mesh = unreal.load_asset(mapping[name])
            mesh.set_material(0, mat)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
        return {'material': mat.get_path_name(), 'meshes': arg.split()}
    if action == 'hptree':
        import mare_materials, importlib
        importlib.reload(mare_materials)
        mats = mare_materials.build_hp_tree()
        mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
        out = []
        for name in arg.split():
            mesh = unreal.load_asset(mapping[name])
            for j, slot in enumerate(mesh.static_materials):
                kind = 'leaf' if 'leaf' in str(slot.material_slot_name).lower() else 'trunk'
                mesh.set_material(j, mats[kind])
                out.append([name, j, kind])
            unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
        return out
    if action == 'lampglow':
        # 'World_1392:1 World_0687:1 ...' -> glass slot of each lamp mesh gets M_LampGlow_PBR.
        import mare_materials, importlib
        importlib.reload(mare_materials)
        mat = mare_materials.build_lamp_glow()
        mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
        out = []
        for spec in arg.split():
            name, slot = spec.split(':')
            mesh = unreal.load_asset(mapping[name])
            mesh.set_material(int(slot), mat)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
            out.append(spec)
        return out
    if action == 'outfitmat':
        import mare_materials, importlib
        importlib.reload(mare_materials)
        return [mare_materials.build_person_outfit().get_path_name(), mare_materials.build_person_body().get_path_name()]
    if action == 'exporttex':
        # 'MaterialPath' -> export every TextureObject/Sample texture of that material to D:/CodexTemp/tex
        m = unreal.load_asset(arg)
        out = []
        Path('D:/CodexTemp/tex').mkdir(parents=True, exist_ok=True)
        for e in unreal.MaterialEditingLibrary.get_material_expressions(m):
            t = e.get_editor_property('texture') if isinstance(e, (unreal.MaterialExpressionTextureObject, unreal.MaterialExpressionTextureSample)) else None
            if t:
                task = unreal.AssetExportTask()
                task.object = t; task.filename = 'D:/CodexTemp/tex/' + t.get_name() + '.png'; task.automated = True; task.replace_identical = True; task.prompt = False
                task.exporter = unreal.TextureExporterPNG()
                unreal.Exporter.run_asset_export_task(task)
                out.append([t.get_name(), t.get_path_name()])
        return out
    if action == 'matinfo':
        out = {}
        for path in arg.split(','):
            m = unreal.load_asset(path)
            info = {'class': m.get_class().get_name()}
            if isinstance(m, unreal.MaterialInstance):
                info['vectors'] = [[str(v.parameter_info.name), [round(v.parameter_value.r, 2), round(v.parameter_value.g, 2), round(v.parameter_value.b, 2)]] for v in m.get_editor_property('vector_parameter_values')]
                info['textures'] = [[str(t.parameter_info.name), t.parameter_value.get_name() if t.parameter_value else None] for t in m.get_editor_property('texture_parameter_values')]
                info['parent'] = m.get_editor_property('parent').get_path_name()
            if isinstance(m, unreal.Material):
                n = unreal.MaterialEditingLibrary.get_material_property_input_node(m, unreal.MaterialProperty.MP_BASE_COLOR)
                info['base'] = n.get_class().get_name() if n else None
                if isinstance(n, unreal.MaterialExpressionConstant3Vector):
                    c = n.get_editor_property('constant'); info['color'] = [round(c.r, 2), round(c.g, 2), round(c.b, 2)]
                if isinstance(n, unreal.MaterialExpressionMaterialFunctionCall):
                    info['function'] = n.get_editor_property('material_function').get_path_name() if n.get_editor_property('material_function') else None
                    exprs = unreal.MaterialEditingLibrary.get_material_expressions(m) if hasattr(unreal.MaterialEditingLibrary, 'get_material_expressions') else []
                    info['nodes'] = sorted({e.get_class().get_name() for e in exprs})
                    info['tex'] = sorted({e.texture.get_name() for e in exprs if isinstance(e, unreal.MaterialExpressionTextureSample) and e.texture})
                    info['consts'] = [[round(e.get_editor_property('constant').r, 2), round(e.get_editor_property('constant').g, 2), round(e.get_editor_property('constant').b, 2)] for e in exprs if isinstance(e, unreal.MaterialExpressionConstant3Vector)][:4]
                    info['vecs'] = [[str(e.get_editor_property('parameter_name')), round(e.get_editor_property('default_value').r, 2), round(e.get_editor_property('default_value').g, 2), round(e.get_editor_property('default_value').b, 2)] for e in exprs if isinstance(e, unreal.MaterialExpressionVectorParameter)][:4]
                if isinstance(n, unreal.MaterialExpressionTextureSample) and n.texture:
                    info['texture'] = n.texture.get_name()
                info['blend'] = str(m.get_editor_property('blend_mode'))
            out[path] = info
        return out
    if action == 'lots':
        out = []
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            tags = [str(t) for t in a.tags if str(t).startswith('Lot_')]
            if tags and 'MareLawn' not in [str(t) for t in a.tags]:
                o, e = a.get_actor_bounds(False)
                meshes = [c.static_mesh.get_name() for c in a.get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh]
                out.append([a.get_actor_label(), tags, meshes[:3], [round(o.x), round(o.y), round(o.z)], [round(e.x * 2), round(e.y * 2), round(e.z * 2)]])
        return out
    if action == 'lights':
        import collections
        out = collections.Counter()
        detail = []
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            for c in a.get_components_by_class(unreal.LightComponentBase):
                k = (c.get_class().get_name(), ','.join(str(t) for t in a.tags if 'Mare' in str(t)))
                out[str(k)] += 1
                if len(detail) < 25 or c.get_class().get_name() in ('SkyLightComponent', 'DirectionalLightComponent'):
                    detail.append([a.get_actor_label(), c.get_class().get_name(), round(c.get_editor_property('intensity'), 2), [round(v) for v in (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z)]])
        return {'counts': dict(out), 'detail': detail}
    if action == 'hillmeshes':
        mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
        inverse = {v.split('.')[0]: k for k, v in mapping.items()}
        out = {}
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            l = a.get_actor_label()
            if l.startswith('Maré · @MeshInstance3D@'):
                try:
                    n = int(l.rsplit('@', 1)[1])
                except ValueError:
                    continue
                if 1869 <= n <= 1938:
                    for c in a.get_components_by_class(unreal.StaticMeshComponent):
                        if c.static_mesh:
                            out[l] = [inverse.get(c.static_mesh.get_path_name().split('.')[0]), c.static_mesh.get_num_triangles(0)]
        return out
    if action == 'hillmat':
        # Godot backdrop hill tiles (labels @MeshInstance3D@1869..1938): textured terrain material.
        import mare_materials, importlib
        importlib.reload(mare_materials)
        mat = mare_materials.build_hill_ground()
        out = []
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            l = a.get_actor_label()
            if not l.startswith('Maré · @MeshInstance3D@'):
                continue
            try:
                n = int(l.rsplit('@', 1)[1])
            except ValueError:
                continue
            if not 1869 <= n <= 1938:
                continue
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                if c.static_mesh:
                    for j in range(len(c.static_mesh.static_materials)):
                        c.set_material(j, mat)
                    out.append(l)
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return {'tiles': len(out)}
    if action == 'coastfill':
        # tools/ue58/coast_fill.py meshes: ground between the resort tile and the hills.
        import mare_hotel_lobby
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for a in actors.get_all_level_actors():
            if a.get_actor_label().startswith('Maré · Preenchimento costeiro'):
                actors.destroy_actor(a)
        ground_mat = unreal.load_asset('/Game/World/Materials/M_CoastGround_PBR')
        out = []
        for side in ('W', 'E'):
            name = 'CoastFill_' + side
            mesh = mare_hotel_lobby._import(ROOT / 'SourceArt/Models' / (name + '.gltf'), '/Game/World/Terrain/' + name, name, True)
            mare_hotel_lobby._complex_collision(mesh)
            mesh.set_material(0, ground_mat)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
            actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector())
            actor.set_actor_label('Maré · Preenchimento costeiro ' + side)
            actor.tags = [unreal.Name('MareGenerated'), unreal.Name('MareCoastFill')]
            actor.static_mesh_component.set_static_mesh(mesh)
            actor.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
            o, e = actor.get_actor_bounds(False)
            out.append({'mesh': name, 'min': [round(o.x - e.x), round(o.y - e.y), round(o.z - e.z)], 'max': [round(o.x + e.x), round(o.y + e.y), round(o.z + e.z)]})
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return out
    if action == 'grid':
        # 'x0,x1,y0,y1,step' -> rows of [x, y, z, label] from downward traces (no actor ignored).
        x0, x1, y0, y1, step = [int(float(v)) for v in arg.split(',')]
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        out = []
        for x in range(x0, x1 + 1, step):
            for y in range(y0, y1 + 1, step):
                hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 40000), unreal.Vector(x, y, -3000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
                if hit:
                    t = hit.to_tuple()
                    out.append([x, y, round(t[4].z), t[9].get_actor_label() if t[9] else ''])
                else:
                    out.append([x, y, None, ''])
        Path('D:/CodexTemp/terrain').mkdir(parents=True, exist_ok=True)
        Path('D:/CodexTemp/terrain/grid_%s.json' % arg.replace(',', '_')).write_text(json.dumps(out), encoding='utf-8')
        return {'samples': len(out)}
    if action == 'hills':
        out = []
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            l = a.get_actor_label()
            if l == 'Maré · Ground' or l.startswith('Maré · @MeshInstance3D') or 'Oceano' in l or 'Ocean' in l:
                o, e = a.get_actor_bounds(False)
                if l == 'Maré · Ground' or 'Ocean' in l or 'Oceano' in l or e.z > 1500 or (e.x > 3000 and e.y > 3000):
                    out.append([l, round(o.x - e.x), round(o.x + e.x), round(o.y - e.y), round(o.y + e.y), round(o.z - e.z), round(o.z + e.z)])
        return out
    if action == 'tall':
        out = {}
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                m = c.static_mesh
                if not m:
                    continue
                e = m.get_bounds().box_extent
                if e.z * 2 < 300 or min(e.x, e.y) * 2 < 200 or max(e.x, e.y) * 2 > 3000:
                    continue
                n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
                k = a.get_actor_label() + ' | ' + m.get_name()
                mats = sorted({s.material_interface.get_name() for s in m.static_materials if s.material_interface})
                out[k] = {'n': out.get(k, {}).get('n', 0) + n, 'size': [round(e.x * 2), round(e.y * 2), round(e.z * 2)], 'tris': m.get_num_triangles(0), 'mats': mats[:4]}
        return out
    if action == 'trace':
        # What does a ray from a camera point toward a target hit first? 'x,y,z;tx,ty,tz'
        (a1, b1) = [[float(v) for v in part.split(',')] for part in arg.split(';')]
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(*a1), unreal.Vector(*b1), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        if not hit:
            return None
        t = hit.to_tuple()
        comp = t[10]
        mesh = comp.static_mesh.get_name() if hasattr(comp, 'static_mesh') and comp.static_mesh else None
        return {'actor': t[9].get_actor_label() if t[9] else None, 'component': comp.get_name() if comp else None, 'class': comp.get_class().get_name() if comp else None, 'mesh': mesh, 'at': [round(v) for v in (t[4].x, t[4].y, t[4].z)]}
    if action == 'coconut_piles':
        # The dry coconuts lie on their side (15 cm tall): the fifth coconut of each Godot pile sat
        # 17 cm up and now floats. Rest it in the hollow between the four below.
        mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
        targets = {mapping[n].split('.')[0] for n in arg.split()}
        moved = 0
        for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                if not c.static_mesh or c.static_mesh.get_path_name().split('.')[0] not in targets:
                    continue
                ts = [c.get_instance_transform(i, True) for i in range(c.get_instance_count())]
                for i, t in enumerate(ts):
                    p = t.translation
                    below = [u.translation for u in ts if (u.translation.x - p.x) ** 2 + (u.translation.y - p.y) ** 2 < 20 * 20 and 10 < p.z - u.translation.z < 25]
                    if len(below) >= 3:
                        base = sum(u.z for u in below) / len(below)
                        nt = unreal.Transform(unreal.Vector(p.x, p.y, base + 8.5), t.rotation.rotator(), t.scale3d)
                        c.update_instance_transform(i, nt, True, True, True)
                        moved += 1
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return {'moved': moved}
    if action == 'coconut':
        import mare_materials, importlib
        importlib.reload(mare_materials)
        mats = mare_materials.build_coconut()
        mapping = json.loads((DATA / 'imported_meshes.json').read_text(encoding='utf-8-sig'))
        out = []
        for name in arg.split():
            mesh = unreal.load_asset(mapping[name])
            for j, slot in enumerate(mesh.static_materials):
                kind = 'husk' if 'husk' in str(slot.material_slot_name).lower() else 'fiber'
                mesh.set_material(j, mats[kind])
                out.append([name, j, kind])
            unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
        return out
    if action == 'mesh_materials':
        out = []
        for slot in unreal.load_asset(arg).static_materials:
            m = slot.material_interface
            info = {'slot': str(slot.material_slot_name), 'material': m.get_path_name() if m else None}
            if m:
                base = m
                while isinstance(base, unreal.MaterialInstance):
                    info.setdefault('textures', [str(t.parameter_value.get_path_name()) if t.parameter_value else None for t in base.get_editor_property('texture_parameter_values')])
                    base = base.get_editor_property('parent')
                info['root'] = base.get_path_name() if base else None
                info['blend'] = str(base.get_editor_property('blend_mode')) if base else None
            out.append(info)
        return out
    if action == 'skel_materials':
        mesh = unreal.load_asset(arg)
        return [{'slot': str(m.material_slot_name), 'material': m.material_interface.get_path_name() if m.material_interface else None} for m in mesh.materials]
    if action == 'remove_orphans':
        return remove_orphan_accessories()
    if action == 'restore_stacked':
        return restore_stacked(arg or 'D:/CodexTemp/multimesh/multimesh.json')
    if action == 'near':
        x, y, r = [float(v) for v in arg.split(',')]
        return near(x, y, r)
    if action == 'sync':
        return sync()
    if action == 'debug':
        return debug(arg)
    if action == 'scan':
        return scan()
    if action == 'fix':
        return fix()
    raise ValueError(action)
