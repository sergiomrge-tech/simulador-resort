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
    if action == 'palmmat':
        return palm_material(arg.split())
    if action == 'stacked':
        return remove_stacked()
    if action == 'hidebroken':
        return hide_broken()
    if action == 'reimport':
        return reimport_props(arg.split())
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
