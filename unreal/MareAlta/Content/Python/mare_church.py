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


def survey(arg=''):
    """Everything inside the church's footprint and up to its roof (the nave work of 11/11): mesh, actor, instance,
    centre, world size, material, collision; plus lights, texts and other actors. Written to the file `arg`."""
    _world()
    rows = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        loc = a.get_actor_location()
        comps = a.get_components_by_class(unreal.StaticMeshComponent)
        if not comps:
            if abs(loc.x - CX - 80) < 760 and abs(loc.y - CY) < 760 and loc.z < 2000:
                rows.append({'actor': a.get_actor_label(), 'class': a.get_class().get_name(), 'c': [round(loc.x), round(loc.y), round(loc.z)], 'tags': [str(t) for t in a.tags]})
            continue
        for c in comps:
            m = c.get_editor_property('static_mesh')
            if not m:
                continue
            name = m.get_name()
            if 'rass' in name or 'PCG' in a.get_actor_label():
                continue
            bb = m.get_bounding_box()
            inst = isinstance(c, unreal.InstancedStaticMeshComponent)
            ts = [(i, c.get_instance_transform(i, True)) for i in range(c.get_instance_count())] if inst else [(-1, c.get_world_transform())]
            for i, t in ts:
                if abs(t.translation.x - CX - 80) > 1500 or abs(t.translation.y - CY) > 1500:
                    continue
                ctr = t.transform_location((bb.min + bb.max) * .5)
                if abs(ctr.x - CX - 80) > 760 or abs(ctr.y - CY) > 760:
                    continue
                ext = (bb.max - bb.min) * .5
                corners = [t.transform_location((bb.min + bb.max) * .5 + unreal.Vector(sx * ext.x, sy * ext.y, sz * ext.z)) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
                size = [round(max(getattr(p, ax) for p in corners) - min(getattr(p, ax) for p in corners)) for ax in ('x', 'y', 'z')]
                mats = c.get_materials()
                rows.append({'mesh': name, 'actor': a.get_actor_label(), 'i': i, 'c': [round(ctr.x), round(ctr.y), round(ctr.z)], 's': size,
                             'mat': mats[0].get_name() if mats and mats[0] else None, 'col': str(c.get_collision_enabled()).split('.')[-1].rstrip('>'),
                             'tags': [str(t) for t in a.tags][:3]})
    open(arg.strip(), 'w', encoding='utf-8').write(json.dumps(rows, ensure_ascii=False))
    return json.dumps({'n': len(rows)})


# ---------------------------------------------------------------- the interior (11/11, references: the Sé cathedral)
IN_TAG = 'MareChurchInterior'
BOX, BAND = 'World_1176', 'World_1177'            # the solid body (1000 x 1200 x 700) and its blue base band
DOOR_PARTS = (('World_1186', 7500, 4392), ('World_1189', 7500, 4394), ('World_2105', 7500, 4394), ('World_0683', 7502, 4361))
FLOOR = 20.0


def _asset(slug):
    from pathlib import Path
    data = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data' / 'custom_assets.json').read_text(encoding='utf-8'))
    return unreal.load_asset(data[slug])


def glass_day(arg='3.0'):
    """Glass seen from inside: the picture lit by the day behind it (MPC_MareTime.Night low), almost dark at night.
    M_ChurchStainedGlassDay (the windows' picture) and M_ChurchRoseGlass (the rose's, set on the rose mesh)."""
    import mare_materials as mm
    MEL = unreal.MaterialEditingLibrary
    out = {}
    for name, slug, suffix in (('M_ChurchStainedGlassDay', 'mare_church_window', '_Vitral'), ('M_ChurchRoseGlass', 'mare_church_rose', '_Rosacea')):
        mesh = _asset(slug)
        folder = mesh.get_path_name().rsplit('/', 1)[0]
        tex = next(t for t in (unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True)) if isinstance(t, unreal.Texture2D) and t.get_name().endswith(suffix))
        mat = unreal.load_asset('/Game/World/Materials/' + name)
        if not mat:
            mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, '/Game/World/Materials', unreal.Material, unreal.MaterialFactoryNew())
        for old in list(MEL.get_material_expressions(mat)):
            MEL.delete_material_expression(mat, old)
        mat.set_editor_property('used_with_nanite', True)
        sample = mm.expression(mat, unreal.MaterialExpressionTextureSample, texture=tex)
        night = mm.expression(mat, unreal.MaterialExpressionCollectionParameter, collection=mm.time_collection(), parameter_name='Night')
        base = mm.custom(mat, 'return T.rgb*.35;', unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'T': sample})
        MEL.connect_material_property(base, '', unreal.MaterialProperty.MP_BASE_COLOR)
        glow = mm.custom(mat, 'return T.rgb*lerp(GLOW,.04,smoothstep(.15,.6,N));'.replace('GLOW', arg.strip() or '3.0'),
                         unreal.CustomMaterialOutputType.CMOT_FLOAT3, {'T': sample, 'N': night})
        MEL.connect_material_property(glow, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        rough = mm.expression(mat, unreal.MaterialExpressionConstant, r=.25)
        MEL.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
        errors = list(MEL.recompile_material(mat))
        if errors:
            raise RuntimeError(str(errors))
        unreal.EditorAssetLibrary.save_loaded_asset(mat)
        out[name] = mat.get_path_name()
    rose = _asset('mare_church_rose')
    for i, m in enumerate(rose.static_materials):
        n = m.material_interface.get_name() if m.material_interface else ''
        if 'Rosacea' in n or n == 'M_ChurchRoseGlass':
            rose.set_material(i, unreal.load_asset('/Game/World/Materials/M_ChurchRoseGlass'))
    unreal.EditorAssetLibrary.save_loaded_asset(rose)
    return json.dumps(out)


def _slab(actors, mesh, mats, tags, label, lo, hi):
    """A static mesh actor of `mesh` (a box) stretched to fill lo..hi."""
    bb = mesh.get_bounding_box()
    size, ctr = bb.max - bb.min, (bb.min + bb.max) * .5
    s = unreal.Vector((hi[0] - lo[0]) / size.x, (hi[1] - lo[1]) / size.y, (hi[2] - lo[2]) / size.z)
    loc = unreal.Vector((lo[0] + hi[0]) / 2 - ctr.x * s.x, (lo[1] + hi[1]) / 2 - ctr.y * s.y, (lo[2] + hi[2]) / 2 - ctr.z * s.z)
    a = actors.spawn_actor_from_object(mesh, loc, unreal.Rotator(roll=0, pitch=0, yaw=0))
    a.set_actor_scale3d(s)
    a.set_actor_label(label)
    a.tags = [IN_TAG] + tags
    a.set_folder_path('Vila/Igreja')
    c = a.static_mesh_component
    c.set_mobility(unreal.ComponentMobility.STATIC)
    for i, m in enumerate(mats):
        if m:
            c.set_material(i, m)
    return a


def _place(actors, mesh, label, loc, yaw=0.0, scale=1.0, collide=False, tags=()):
    a = actors.spawn_actor_from_object(mesh, unreal.Vector(*loc), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.set_actor_label(label)
    a.tags = [IN_TAG] + list(tags)
    a.set_folder_path('Vila/Igreja')
    c = a.static_mesh_component
    c.set_mobility(unreal.ComponentMobility.STATIC)
    if not collide:
        c.set_collision_profile_name('NoCollision')   # set_collision_enabled alone left the editor's sweeps hitting it
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return a


def interior(arg='dry'):
    """The church becomes a building you walk into: the solid box and its base band are rebuilt as wall slabs that
    leave the door open (x 7400..7600 up to 4.62 m), the old door parts go, and the nave model, the rose, the windows
    seen from inside (5 on the sides at 90%, 3 on the back wall, which also gets them outside), three chandeliers,
    candle stands, day fill lights (MareBareLight) and the interior volume are placed. 'dry' lists, 'apply' does it
    and saves (PIE stopped). Re-runnable."""
    apply = arg.strip() == 'apply'
    _world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    found, old_shell, template = {}, [], None
    for a in actors.get_all_level_actors():
        tags = [str(t) for t in a.tags]
        if IN_TAG in tags:
            old_shell.append(a)
            continue
        if isinstance(a, unreal.PostProcessVolume) and a.get_actor_label() == 'Interior · lobby':
            template = a
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            m = c.get_editor_property('static_mesh')
            if not m:
                continue
            name = m.get_name()
            bb = m.get_bounding_box()
            for i in range(c.get_instance_count()):
                ctr = c.get_instance_transform(i, True).transform_location((bb.min + bb.max) * .5)
                if name in (BOX, BAND) and abs(ctr.x - CX) < 5 and abs(ctr.y - CY) < 5:
                    found[name] = (a, c, i, m)
                for part, px, py in DOOR_PARTS:
                    if name == part and abs(ctr.x - px) < 8 and abs(ctr.y - py) < 8:
                        found[part] = (a, c, i, m)
    report = {'applied': apply, 'found': sorted(found), 'old_parts': len(old_shell), 'volume_template': bool(template)}
    if not apply:
        return json.dumps(report, ensure_ascii=False)
    # the box and band meshes survive in the slabs of an earlier run
    keep = {}
    for a in old_shell:
        m = a.static_mesh_component.static_mesh if isinstance(a, unreal.StaticMeshActor) else None
        if m and m.get_name() in (BOX, BAND):
            keep[m.get_name()] = (m, list(a.static_mesh_component.get_materials()), [str(t) for t in a.tags if str(t) != IN_TAG])
    for name in (BOX, BAND):
        if name in found:
            a, c, i, m = found[name]
            keep[name] = (m, list(c.get_materials()), [str(t) for t in a.tags])
    for a in old_shell:
        actors.destroy_actor(a)
    drop = {}
    for name, (a, c, i, m) in found.items():
        drop.setdefault(c, []).append(i)
    for a in actors.get_all_level_actors():   # the old door's knob was left hanging in the doorway
        if 'macaneta' in a.get_actor_label():
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                for i in range(c.get_instance_count()):
                    p = c.get_instance_transform(i, True).translation
                    if abs(p.x - CX) < 120 and abs(p.y - (CY - 600)) < 60:
                        drop.setdefault(c, []).append(i)
    for c, idx in drop.items():
        for i in sorted(idx, reverse=True):
            c.remove_instance(i)
    x0, x1, y0, y1, t = CX - 500, CX + 500, CY - 600, CY + 600, 30
    m, mats, tags = keep[BOX]
    for label, lo, hi in (('oeste', (x0, y0, 0), (x0 + t, y1, 700)), ('leste', (x1 - t, y0, 0), (x1, y1, 700)), ('fundo', (x0 + t, y1 - t, 0), (x1 - t, y1, 700)),
                          ('frente esq', (x0 + t, y0, 0), (CX - 100, y0 + t, 700)), ('frente dir', (CX + 100, y0, 0), (x1 - t, y0 + t, 700)),
                          ('frente verga', (CX - 100, y0, 462), (CX + 100, y0 + t, 700))):
        _slab(actors, m, mats, tags, 'Igreja · parede ' + label, lo, hi)
    m, mats, tags = keep[BAND]
    for label, lo, hi in (('oeste', (x0 - 3, y0 - 3, 0), (x0 + t, y1 + 3, 80)), ('leste', (x1 - t, y0 - 3, 0), (x1 + 3, y1 + 3, 80)), ('fundo', (x0 + t, y1 - t, 0), (x1 - t, y1 + 3, 80)),
                          ('frente esq', (x0 + t, y0 - 3, 0), (CX - 100, y0 + t, 80)), ('frente dir', (CX + 100, y0 - 3, 0), (x1 - t, y0 + t, 80))):
        _slab(actors, m, mats, tags, 'Igreja · barrado ' + label, lo, hi)
    import mare_hotel_lobby
    nave = _asset('mare_church_nave')
    mare_hotel_lobby._complex_collision(nave)
    unreal.EditorAssetLibrary.save_loaded_asset(nave)
    _place(actors, nave, 'Igreja · nave', (CX, CY, 0), collide=True, tags=tags)
    _place(actors, _asset('mare_church_rose'), 'Igreja · rosácea interna', (CX, y0 + 37, 468), 0.0, .9, tags=tags)
    win = _asset('mare_church_window')
    day = unreal.load_asset('/Game/World/Materials/M_ChurchStainedGlassDay')
    slot = next(i for i, sm in enumerate(win.static_materials) if sm.material_interface and sm.material_interface.get_name() == 'M_ChurchStainedGlass')
    inner = []
    for k, w in enumerate(WIN_Y):
        inner.append(('oeste %d' % (k + 1), (x0 + 36, CY + w, 15), -90.0, .9))
        if w > -300:
            inner.append(('leste %d' % (k + 1), (x1 - 36, CY + w, 15), 90.0, .9))
    for k, dx in enumerate((-341, 0, 341)):
        inner.append(('fundo %d' % (k + 1), (CX + dx, y1 - 36, 50 if dx == 0 else 15), 180.0, .9))
        _place(actors, win, 'Igreja · Vitral fundo %d' % (k + 1), (CX + dx, y1, 0), 0.0, 1.0, tags=tags)   # the same three outside
    for label, loc, yaw, sc in inner:
        a = _place(actors, win, 'Igreja · vitral interno ' + label, loc, yaw, sc, tags=tags)
        a.static_mesh_component.set_material(slot, day)
    lamp = _asset('Chandelier_03')
    for k, w in enumerate(WIN_Y):
        a = _place(actors, lamp, 'Igreja · lustre %d' % (k + 1), (CX, CY + w, 495), 30.0 * k, 1.3, tags=tags)
        a.static_mesh_component.set_cast_shadow(False)   # its own light sits among the arms
    candles = _asset('brass_candleholders')
    _place(actors, candles, 'Igreja · castiçais esq', (CX - 215, CY + 455, FLOOR + 30), 20.0, 1.0, tags=tags)
    _place(actors, candles, 'Igreja · castiçais dir', (CX + 215, CY + 455, FLOOR + 30), 160.0, 1.0, tags=tags)
    for k, w in enumerate((-240.0, 240.0)):   # daylight fill (UMareVisualWorld drives MareBareLight: on by day, off at night)
        light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(CX, CY + w, 400))
        light.set_actor_label('Igreja · luz do dia %d' % (k + 1))
        light.tags = [IN_TAG, 'MareBareLight'] + tags
        light.set_folder_path('Vila/Igreja')
        lc = light.light_component
        lc.set_mobility(unreal.ComponentMobility.MOVABLE)
        lc.set_editor_property('intensity_units', unreal.LightUnits.CANDELAS)
        lc.set_intensity(0.0)
        lc.set_attenuation_radius(1100.0)
        lc.set_cast_shadows(False)
        lc.set_editor_property('use_temperature', True)
        lc.set_editor_property('temperature', 5200.0)
    if template:
        lo, hi = unreal.Vector(x0 + t, y0 + t, FLOOR), unreal.Vector(x1 - t, y1 - t, 662)
        centre, ext = (lo + hi) * .5, (hi - lo) * .5
        v = actors.duplicate_actor(template)
        v.set_actor_label('Interior · igreja')
        v.tags = [unreal.Name('MareInterior'), unreal.Name(IN_TAG)]
        o, e = template.get_actor_bounds(False)
        s = template.get_actor_scale3d()
        v.set_actor_scale3d(unreal.Vector(s.x * ext.x / e.x, s.y * ext.y / e.y, s.z * ext.z / e.z))
        v.set_actor_location(centre, False, False)
        o2, e2 = v.get_actor_bounds(False)
        v.set_actor_location(centre + (centre - o2), False, False)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report['placed'] = len([a for a in actors.get_all_level_actors() if IN_TAG in [str(t) for t in a.tags]])
    return json.dumps(report, ensure_ascii=False)


def walk(arg=''):
    """Can the hero get around? Sweeps a capsule of the hero's size (radius 34, 176 tall, 25 cm off the floor so a
    step does not count) along the ways in: porch -> nave -> chancel, door -> both side aisles -> beside the altar.
    Complex collision; every leg must come back clear."""
    sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = sub.get_game_world() or sub.get_editor_world()
    legs = [('porta', (7500, 4290, 30), (7500, 4480, 30)), ('nave', (7500, 4480, 20), (7500, 5210, 20)), ('altar', (7500, 5215, 50), (7500, 5340, 50)),
            ('cruzar oeste', (7500, 4538, 20), (7100, 4538, 20)), ('lateral oeste', (7100, 4538, 20), (7100, 5215, 20)), ('presbitério oeste', (7100, 5215, 50), (7100, 5450, 50)),
            ('cruzar leste', (7500, 4538, 20), (7900, 4538, 20)), ('lateral leste', (7900, 4538, 20), (7900, 5215, 20)), ('presbitério leste', (7900, 5215, 50), (7900, 5450, 50)),
            ('presbitério de lado a lado', (7100, 5265, 50), (7900, 5265, 50))]
    rows = []
    for name, a, b in legs:
        za, zb = a[2] + 25 + 88, b[2] + 25 + 88
        hit = unreal.SystemLibrary.capsule_trace_single(world, unreal.Vector(a[0], a[1], za), unreal.Vector(b[0], b[1], zb), 34.0, 88.0,
                                                        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        if hit:
            t = hit.to_tuple()
            loc, actor = t[4], t[9]
            rows.append({'leg': name, 'clear': False, 'at': [round(loc.x), round(loc.y), round(loc.z)], 'actor': actor.get_actor_label() if actor else None})
        else:
            rows.append({'leg': name, 'clear': True})
    return json.dumps(rows, ensure_ascii=False)


def faithful(arg=''):
    """PIE: the people seated in the pews against Content/Data/church.json: pelvis and head relative to the seat point
    (forward = towards the altar, +y), feet height over the floor."""
    from pathlib import Path
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:
        return json.dumps({'pie': False})
    seats = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data' / 'church.json').read_text(encoding='utf-8'))['seats']
    rows = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
        if not str(p.get_editor_property('save_id')).startswith('church_'):
            continue
        loc = p.get_actor_location()
        s = min(seats, key=lambda k: (k[0] - loc.x) ** 2 + (k[1] - loc.y) ** 2)
        mesh = p.get_component_by_class(unreal.SkeletalMeshComponent)
        head, pel = mesh.get_socket_location('head'), mesh.get_socket_location('pelvis')
        fl, fr = mesh.get_socket_location('foot_l'), mesh.get_socket_location('foot_r')
        rows.append({'id': str(p.get_editor_property('save_id')), 'seat': s[:3], 'actor': [round(loc.x), round(loc.y), round(loc.z)], 'yaw': round(p.get_actor_rotation().yaw),
                     'pelvis_side_fwd_up': [round(pel.x - s[0]), round(pel.y - s[1]), round(pel.z - s[2])],
                     'head_side_fwd_up': [round(head.x - s[0]), round(head.y - s[1]), round(head.z - s[2])],
                     'feet_fwd_up': [round((fl.y + fr.y) / 2 - s[1]), round(min(fl.z, fr.z) - FLOOR)]})
    return json.dumps(rows, ensure_ascii=False)


def lamps_nanite(arg=''):
    """The chandelier's glass and the candle flames are translucent: Nanite draws only opaque or masked (the log said
    'Invalid material ... used on Nanite static mesh' and the parts vanish in the game). Both small meshes go non-Nanite."""
    _world()
    sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    out = {}
    for slug in ('Chandelier_03', 'brass_candleholders'):
        mesh = _asset(slug)
        settings = sub.get_nanite_settings(mesh)
        settings.enabled = False
        sub.set_nanite_settings(mesh, settings, True)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        out[slug] = sub.get_nanite_settings(mesh).enabled
    return json.dumps(out)
