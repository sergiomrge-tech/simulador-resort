"""Village church (11/11, Sergio's photo: "arrume a igreja", then "vidraça de catedral, ornamentada" on both sides).

The Godot scene put five pilasters on each side wall every 2.8 m and three windows every 3.6 m: the middle pilaster
stood right in front of the middle window, and the windows were flat boxes glowing pink / blue / cream.

probe(arg): every mesh part against the two side walls (mesh, actor, instance, centre, size, material).
fix(arg): 'dry' lists, 'apply' shrinks the old window parts and the middle pilaster to nothing, moves the pilasters
next to it to the middle of the bays (y +-180) and places the cathedral windows (mare_church_window); saves the level."""
import json
import unreal

CX, CY = 7500.0, 5000.0     # Godot CHURCH_C (75, 0, 50)
HALF_W = 500.0
WIN_Y = (-360.0, 0.0, 360.0)
TAG = 'MareChurchWindow'


def _world():
    sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if sub.get_game_world():
        raise RuntimeError('Stop PIE first')
    return sub.get_editor_world()


def _parts():
    """(actor, component, instance index or -1, transform, mesh, centre, size) of everything on the side walls."""
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if TAG in [str(t) for t in a.tags]:
            continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.get_editor_property('static_mesh')
            if not m:
                continue
            bb = m.get_bounding_box()
            inst = isinstance(c, unreal.InstancedStaticMeshComponent)
            ts = [(i, c.get_instance_transform(i, True)) for i in range(c.get_instance_count())] if inst else [(-1, c.get_world_transform())]
            for i, t in ts:
                loc = t.translation
                if abs(loc.x - CX) > 900 or abs(loc.y - CY) > 900:
                    continue
                ctr = t.transform_location((bb.min + bb.max) * .5)
                side = abs(ctr.x - CX)
                if not (HALF_W - 30 <= side <= HALF_W + 60) or abs(ctr.y - CY) > 640 or not (0 < ctr.z < 760):
                    continue
                # size in world axes (parts are rotated by multiples of 90 degrees)
                ext = (bb.max - bb.min) * .5
                corners = [t.transform_location((bb.min + bb.max) * .5 + unreal.Vector(sx * ext.x, sy * ext.y, sz * ext.z)) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
                size = [max(getattr(p, ax) for p in corners) - min(getattr(p, ax) for p in corners) for ax in ('x', 'y', 'z')]
                out.append((a, c, i, t, m, ctr, size))
    return out


def probe(arg=''):
    _world()
    rows = []
    for a, c, i, t, m, ctr, size in _parts():
        mats = c.get_materials()
        rows.append({'mesh': m.get_name(), 'actor': a.get_actor_label(), 'i': i, 'c': [round(ctr.x), round(ctr.y), round(ctr.z)], 's': [round(v) for v in size],
                     'mat': mats[0].get_name() if mats and mats[0] else None})
    rows.sort(key=lambda r: (r['c'][0] > CX, r['c'][1], r['c'][2]))
    if arg.strip():   # the full list to a file (the MCP answer is cut at 8000 characters)
        open(arg.strip(), 'w', encoding='utf-8').write(json.dumps(rows, ensure_ascii=False))
    return json.dumps({'n': len(rows)}, ensure_ascii=False)


GLASS = '/Game/World/Materials/M_ChurchStainedGlass'
OLD = ('World_2079', 'World_2080', 'World_2081', 'World_2082', 'World_2083', 'World_2084', 'World_2085', 'World_2086',
       'World_2088', 'World_2089', 'World_2091', 'World_2096', 'World_2098')
PILASTER = 'World_2092'


def _window_mesh():
    from pathlib import Path
    data = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data' / 'custom_assets.json').read_text(encoding='utf-8'))
    return unreal.load_asset(data['mare_church_window'])   # the importer names the asset: never write the path by hand


def build(arg=''):
    """M_ChurchStainedGlass on the window's glass slot: the picture as colour, and as light from inside at night
    (MPC_MareTime.Night); by day a faint glow keeps the colours readable from outside. Opaque (Nanite)."""
    import mare_materials as mm
    MEL = unreal.MaterialEditingLibrary
    mesh = _window_mesh()
    folder = mesh.get_path_name().rsplit('/', 1)[0]
    tex = next(unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True) if p.split('.')[-1].endswith('_Vitral'))
    mat = unreal.load_asset(GLASS)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_ChurchStainedGlass', '/Game/World/Materials', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    sample = mm.expression(mat, unreal.MaterialExpressionTextureSample, texture=tex)
    night = mm.expression(mat, unreal.MaterialExpressionCollectionParameter, collection=mm.time_collection(), parameter_name='Night')
    base = mm.custom(mat, 'return T.rgb*.6;', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'T': sample})
    MEL.connect_material_property(base, '', unreal.MaterialProperty.MP_BASE_COLOR)
    # night exposure is EV100 -1..-2 (torch lesson: 26 burns white, 1 reads brown): the light of the nave through the glass
    glow = mm.custom(mat, 'return T.rgb*T.rgb*lerp(.08,GLOW,smoothstep(.2,.6,N));'.replace('GLOW', arg.strip() or '5.0'),
                     unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'T': sample, 'N': night})
    MEL.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    rough = mm.expression(mat, unreal.MaterialExpressionConstant, r=.22)
    MEL.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    errors = list(MEL.recompile_material(mat))
    if errors:
        raise RuntimeError(str(errors))
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    slots = []
    for i, m in enumerate(mesh.static_materials):
        name = m.material_interface.get_name() if m.material_interface else ''
        if 'Vitral' in name or name == 'M_ChurchStainedGlass':
            mesh.set_material(i, mat)
        slots.append(mesh.static_materials[i].material_interface.get_name())
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    return json.dumps({'material': mat.get_path_name(), 'slots': slots})


def fix(arg='dry'):
    apply = arg.strip() == 'apply'
    _world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    gone, moved, kill, drop = [], [], [], {}
    for a, c, i, t, m, ctr, size in _parts():
        name = m.get_name()
        dy = ctr.y - CY
        if name in OLD and min(abs(dy - w) for w in WIN_Y) < 12:
            gone.append([name, i, round(ctr.x), round(ctr.y), round(ctr.z)])
            if i < 0:
                kill.append(a)
            else:
                drop.setdefault(c, []).append(i)
        elif name == PILASTER and abs(dy) < 12:
            gone.append([name, i, round(ctr.x), round(ctr.y), round(ctr.z)])
            drop.setdefault(c, []).append(i)
        elif name == PILASTER and abs(abs(dy) - 280) < 12:   # to the middle of the bay between two windows
            moved.append([name, i, round(ctr.x), round(ctr.y), '->', round(ctr.y - 100 * (1 if dy > 0 else -1))])
            if apply:
                t.translation = unreal.Vector(t.translation.x, t.translation.y - 100 * (1 if dy > 0 else -1), t.translation.z)
                c.update_instance_transform(i, t, True, True, True)
    placed = []
    if apply:
        for c, idx in drop.items():
            for i in sorted(idx, reverse=True):
                c.remove_instance(i)
        for a in kill:
            actors.destroy_actor(a)
        for a in actors.get_all_level_actors():
            if TAG in [str(t) for t in a.tags]:
                actors.destroy_actor(a)
        mesh = _window_mesh()
        for side, yaw in ((-1, 90.0), (1, -90.0)):     # the model's front (UE +Y) turned out of each side wall
            for k, w in enumerate(WIN_Y):
                if side > 0 and w < -300:   # the bell tower (y 4400-4720) stands on that stretch of the east wall
                    continue
                a = actors.spawn_actor_from_object(mesh, unreal.Vector(CX + side * HALF_W, CY + w, 0), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
                a.set_actor_label('Igreja · Vitral %s %d' % ('oeste' if side < 0 else 'leste', k + 1))
                a.tags = [TAG]
                a.set_folder_path('Vila/Igreja')
                comp = a.static_mesh_component
                comp.set_mobility(unreal.ComponentMobility.STATIC)
                comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                placed.append(a.get_actor_label())
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'applied': apply, 'gone': len(gone), 'moved': moved, 'placed': placed, 'gone_rows': gone[:60]}, ensure_ascii=False)
