"""The player's house (11/11, Sergio: "analise você mesmo a casa do jogador e refaça, está muito simples, sem textura de
desgaste, quero mais realista"). parts(): every mesh component inside the house's footprint with its world bounds and
materials (D:/CodexTemp/home_parts.json), to plan the new shell. Read-only."""
import json
import unreal

BOX = (4150.0, 5300.0, 1300.0, 2800.0)       # x0, x1, y0, y1 of the lot


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def parts(_=''):
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if not m:
                continue
            mb = m.get_bounds()
            n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
            for i in range(min(n, 3000)):
                t = c.get_instance_transform(i, True) if isinstance(c, unreal.InstancedStaticMeshComponent) else c.get_world_transform()
                l = t.translation
                if not (BOX[0] < l.x < BOX[1] and BOX[2] < l.y < BOX[3]):
                    continue
                s = t.scale3d
                e = mb.box_extent
                size = [round(e.x * 2 * s.x), round(e.y * 2 * s.y), round(e.z * 2 * s.z)]
                if max(size) < 150:
                    continue
                o = t.transform_location(mb.origin)
                out.append({'label': a.get_actor_label(), 'mesh': m.get_name(), 'inst': i, 'centre': [round(o.x), round(o.y), round(o.z)], 'size': size,
                            'yaw': round(t.rotation.rotator().yaw), 'mats': [c.get_material(k).get_name() if c.get_material(k) else None for k in range(c.get_num_materials())][:3]})
    open('D:/CodexTemp/home_parts.json', 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=0))
    return len(out)


HOME = '/Game/World/Home'
WALLS = ('MA_d5aa8476b035d43f6597d9bf', 'MA_208a2d180e9261505efda2d4')     # main house, bathroom annex
DADO = ('MA_b463dde89848b43e054ad6c0',)


def _tex(name, file, srgb, normal=False):
    path = f'{HOME}/{name}'
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        task = unreal.AssetImportTask()
        task.filename = file
        task.destination_path = HOME
        task.destination_name = name
        task.automated = True
        task.replace_existing = True
        task.save = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    t = unreal.load_asset(path)
    t.set_editor_property('srgb', srgb)
    if normal:
        t.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
    elif not srgb:
        t.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
    unreal.EditorAssetLibrary.save_loaded_asset(t, False)
    return t


def plaster(arg='dry'):
    """M_HomePlasterWorn: aged painted plaster for the house walls, world-aligned (the wall slabs are stretched boxes:
    their own UVs would stretch any picture). Poly Haven painted_plaster_wall (CC0) for the paint, the four wear
    masks of tools/ue58/gen_home_wear.py, and the height on the wall:
      - large blotches of dirt and fading;
      - damp rising from the ground: darker and greenish up to 0.7-1.6 m, its edge broken by the blotch mask;
      - rain streaks hanging from the eaves, strongest in the top 80 cm;
      - paint peeled to the cement render, mostly inside the damp zone and next to cracks;
      - hairline cracks.
    Inside the rooms (the two boxes Room1 / Room2, world cm) the wear is a third as strong: a lived-in wall, not a
    ruin. Instances: MI_HomePlaster_Wall (cream) and MI_HomePlaster_Dado (grey cement, more wear). 'apply' puts them
    on the wall and dado components of the house and saves."""
    apply = arg.strip() == 'apply'
    mel = unreal.MaterialEditingLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    lib = 'D:/Assets/PolyHaven/painted_plaster_wall/painted_plaster_wall_%s_1k.jpg'
    diff = _tex('T_HomePlaster_D', lib % 'diff', True)
    nor = _tex('T_HomePlaster_N', lib % 'nor', False, True)
    wear = _tex('T_HomeWear', 'D:/Assets/Mare/home_wear/T_HomeWear.png', False)
    path = f'{HOME}/M_HomePlasterWorn'
    mat = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else tools.create_asset('M_HomePlasterWorn', HOME, unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)

    def custom(code, out, names, x, y):
        e = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, x, y)
        e.set_editor_property('output_type', out)
        e.set_editor_property('code', code)
        ins = []
        for name in names:
            i = unreal.CustomInput()
            i.set_editor_property('input_name', name)
            ins.append(i)
        e.set_editor_property('inputs', ins)
        return e

    def vec(name, v, y):
        e = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -1500, y)
        e.set_editor_property('parameter_name', name)
        e.set_editor_property('default_value', unreal.LinearColor(*v))
        return e

    def scalar(name, v, y):
        e = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1500, y)
        e.set_editor_property('parameter_name', name)
        e.set_editor_property('default_value', v)
        return e
    pos = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -1500, -400)
    nrm = mel.create_material_expression(mat, unreal.MaterialExpressionVertexNormalWS, -1500, -250)
    uv = custom('float3 a = abs(N); return (a.x > a.y ? P.yz : P.xz) * float2(1, -1);', unreal.CustomMaterialOutputType.CMOT_FLOAT2, ('P', 'N'), -1200, -350)
    mel.connect_material_expressions(pos, '', uv, 'P')
    mel.connect_material_expressions(nrm, '', uv, 'N')

    def sample(t, scale, y, sampler):
        m = custom(f'return U / {scale:.1f};', unreal.CustomMaterialOutputType.CMOT_FLOAT2, ('U',), -1000, y)
        mel.connect_material_expressions(uv, '', m, 'U')
        e = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -800, y)
        e.set_editor_property('texture', t)
        e.set_editor_property('sampler_type', sampler)
        mel.connect_material_expressions(m, '', e, 'UVs')
        return e
    d = sample(diff, 220.0, -400, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    n = sample(nor, 220.0, -150, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    w = sample(wear, 430.0, 100, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    w2 = sample(wear, 173.0, 350, unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)      # a second, finer reading: no visible repeat
    tint = vec('Tint', (.62, .54, .40, 1), 600)
    r1 = vec('Room1', (4257, 1757, 4943, 2443), 760)       # x0, y0, x1, y1: 6 cm outside the inner faces (4263..4937), inside the outer ones
    r2 = vec('Room2', (4622, 1427, 4928, 1757), 920)       # the bathroom annex (inner faces 4627..4923, 1432..1737)
    amount = scalar('Wear', 1.0, 1080)
    base_z = scalar('GroundZ', 12.0, 1180)
    top_z = scalar('EavesZ', 342.0, 1280)
    code = (
        'float inside = max(step(R1.x, P.x) * step(P.x, R1.z) * step(R1.y, P.y) * step(P.y, R1.w),'
        '                   step(R2.x, P.x) * step(P.x, R2.z) * step(R2.y, P.y) * step(P.y, R2.w));\n'
        'float k = K * lerp(1.0, .33, inside);\n'
        'float h = P.z - Z0;\n'
        'float blot = saturate(W.r * .7 + V.r * .5);\n'
        'float paint = dot(D, float3(.33, .34, .33));\n'
        'float3 col = T * (.55 + paint * .75);\n'
        'col *= lerp(1.0, .74, blot * k);\n'
        'float reach = 70.0 + 95.0 * W.r + 25.0 * V.r;\n'
        'float damp = saturate(1.0 - h / reach) * saturate(k);\n'
        'damp = saturate(damp * 1.6);\n'
        'col = lerp(col, col * float3(.50, .55, .40), damp * .8);\n'
        'float top = saturate((h - (Z1 - Z0) + 110.0) / 110.0);\n'
        'float streak = saturate(W.g * 1.6 + V.g * .9) * (.25 + .75 * top);\n'
        'col = lerp(col, col * .52, saturate(streak * k * 1.5));\n'
        'float peel = saturate((WA * .7 + VA * .6) * (.25 + damp * 1.6 + blot * .5) * k * 1.4 - .35) * 3.0;\n'
        'peel = saturate(peel);\n'
        'float3 render = float3(.50, .48, .44) * (.75 + paint * .5) * lerp(1.0, .7, damp);\n'
        'col = lerp(col, render, peel);\n'
        'float crack = saturate(W.b * 1.4 + V.b) * saturate(k + .2);\n'
        'col *= 1.0 - .65 * crack;\n'
        'return float4(col, lerp(.86, .96, peel) - damp * .12);')
    c = custom(code, unreal.CustomMaterialOutputType.CMOT_FLOAT4, ('P', 'D', 'W', 'WA', 'V', 'VA', 'T', 'R1', 'R2', 'K', 'Z0', 'Z1'), -350, 0)
    mel.connect_material_expressions(pos, '', c, 'P')
    mel.connect_material_expressions(d, 'RGB', c, 'D')
    mel.connect_material_expressions(w, 'RGB', c, 'W')
    mel.connect_material_expressions(w, 'A', c, 'WA')
    mel.connect_material_expressions(w2, 'RGB', c, 'V')
    mel.connect_material_expressions(w2, 'A', c, 'VA')
    mel.connect_material_expressions(tint, '', c, 'T')
    # vector parameters reach a Custom node as RGB: the 4th value needs its own mask
    for name, node in (('R1', r1), ('R2', r2)):
        ap = mel.create_material_expression(mat, unreal.MaterialExpressionAppendVector, -900, 760 if name == 'R1' else 920)
        mel.connect_material_expressions(node, '', ap, 'A')
        mel.connect_material_expressions(node, 'A', ap, 'B')
        mel.connect_material_expressions(ap, '', c, name)
    mel.connect_material_expressions(amount, '', c, 'K')
    mel.connect_material_expressions(base_z, '', c, 'Z0')
    mel.connect_material_expressions(top_z, '', c, 'Z1')
    rgb = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -100, 0)
    rgb.set_editor_property('r', True); rgb.set_editor_property('g', True); rgb.set_editor_property('b', True); rgb.set_editor_property('a', False)
    al = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -100, 150)
    al.set_editor_property('r', False); al.set_editor_property('g', False); al.set_editor_property('b', False); al.set_editor_property('a', True)
    mel.connect_material_expressions(c, '', rgb, '')
    mel.connect_material_expressions(c, '', al, '')
    mel.connect_material_property(rgb, '', unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(al, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(n, 'RGB', unreal.MaterialProperty.MP_NORMAL)
    for flag in ('used_with_instanced_static_meshes', 'used_with_nanite'):
        mat.set_editor_property(flag, True)
    errors = mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    out = {'errors': [str(e) for e in errors] if errors else []}

    def instance(name, tint_v, wear_v):
        ipath = f'{HOME}/{name}'
        mi = unreal.load_asset(ipath) if unreal.EditorAssetLibrary.does_asset_exist(ipath) else \
            tools.create_asset(name, HOME, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, mat)
        mel.set_material_instance_vector_parameter_value(mi, 'Tint', unreal.LinearColor(*tint_v))
        mel.set_material_instance_scalar_parameter_value(mi, 'Wear', wear_v)
        mel.update_material_instance(mi)
        unreal.EditorAssetLibrary.save_loaded_asset(mi, False)
        return mi
    wall = instance('MI_HomePlaster_Wall', (.62, .54, .40, 1), 1.0)
    dado = instance('MI_HomePlaster_Dado', (.34, .32, .29, 1), 1.5)
    done = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.Actor):
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            if not comp.static_mesh:
                continue
            n_inst = comp.get_instance_count() if isinstance(comp, unreal.InstancedStaticMeshComponent) else 1
            locs = [(comp.get_instance_transform(i, True) if isinstance(comp, unreal.InstancedStaticMeshComponent) else comp.get_world_transform()).translation for i in range(n_inst)]
            if not locs or not all(BOX[0] < l.x < BOX[1] and BOX[2] < l.y < BOX[3] for l in locs):
                continue
            for k in range(comp.get_num_materials()):
                m = comp.get_material(k)
                name = m.get_name() if m else ''
                new = wall if name in WALLS else dado if name in DADO else None
                if new:
                    done.append([a.get_actor_label()[-22:], comp.static_mesh.get_name(), n_inst, name[:12]])
                    if apply:
                        comp.set_material(k, new)
    out['components'] = len(done)
    out['list'] = done[:30]
    if apply:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out, ensure_ascii=False)


def openings(_=''):
    """Sill and lintel heights of the wall openings: vertical traces inside each opening, on the wall's mid plane."""
    w = _world()
    out = {}
    for name, (x, y) in {'west': (4250, 2100), 'south_win': (4460, 1750), 'south_door': (4770, 1750), 'north_win': (4430, 2450), 'north_door': (4770, 2450)}.items():
        row = []
        for a, b in ((175, 0), (175, 345)):
            hit = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x, y, a), unreal.Vector(x, y, b), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                         True, [], unreal.DrawDebugTrace.NONE, True)
            row.append(round(hit.to_tuple()[4].z) if hit else None)
        # width: horizontal traces along the wall at mid height
        mid = (row[0] + row[1]) / 2 if None not in row else 175
        side = []
        for d in (-1, 1):
            e = (x, y + d * 400) if name == 'west' else (x + d * 400, y)
            hit = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x, y, mid), unreal.Vector(e[0], e[1], mid), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                         True, [], unreal.DrawDebugTrace.NONE, True)
            p = hit.to_tuple()[4] if hit else None
            side.append(round(p.y if name == 'west' else p.x) if p else None)
        out[name] = {'sill_lintel': row, 'sides': side}
    hit = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(4000, 2100, 300), unreal.Vector(4000, 2100, -100), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    out['ground_west'] = round(hit.to_tuple()[4].z, 1) if hit else None
    for nm, (x, y) in {'eave_w': (4200, 2100), 'eave_s': (4600, 1700), 'eave_w_out': (4170, 2100), 'annex_eave_s': (4775, 1410)}.items():
        hit = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x, y, 200), unreal.Vector(x, y, 600), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        out[nm] = round(hit.to_tuple()[4].z, 1) if hit else None
    return json.dumps(out)


def dress(arg='dry'):
    """Step 2: places the volumes model (tools/ue58/gen_home_dress.py) at the house's centre; no collision. Re-runnable."""
    from pathlib import Path
    data = json.loads((Path(unreal.Paths.project_content_dir()) / 'Data' / 'custom_assets.json').read_text(encoding='utf-8'))
    mesh = unreal.load_asset(data.get('mare_home_dress', ''))
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mine = [a for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.StaticMeshActor) if 'MareHomeDress' in [str(t) for t in a.tags]]
    if arg.strip() != 'apply' or not mesh:
        return json.dumps({'mesh': bool(mesh), 'mine': len(mine)})
    for a in mine:
        actors.destroy_actor(a)
    a = actors.spawn_actor_from_object(mesh, unreal.Vector(4600, 2100, 0), unreal.Rotator(roll=0, pitch=0, yaw=0))
    a.set_actor_label('Casa · beiral, calhas e janelas')
    a.tags = [unreal.Name('MareGenerated'), unreal.Name('MareHomeDress')]
    a.set_folder_path('Vila/Casa')
    c = a.static_mesh_component
    c.set_mobility(unreal.ComponentMobility.STATIC)
    c.set_collision_profile_name('NoCollision')
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'placed': True})
