"""Bar do Coqueiro physical prep (CHECKLIST_EXPANSOES 1.1): editor helpers to measure the counter, import the prep
props (tools/ue58/gen_bar_prep.py) and clear the shrub growing through the bar floor."""
import json

import unreal


def _game_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()


def _editor_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def probe(arg=''):
    """Downward traces over a grid 'x0,x1,y0,y1,step' in the running PIE world: [x, y, top z, actor]."""
    v = [float(a) for a in (arg or "950,1550,-1700,-900,50,600").split(",")]
    x0, x1, y0, y1, step = v[:5]
    top = v[5] if len(v) > 5 else 600
    world = _game_world() or _editor_world()
    out = []
    x = x0
    while x <= x1:
        y = y0
        while y <= y1:
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, top), unreal.Vector(x, y, -100),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
                                                         unreal.DrawDebugTrace.NONE, True)
            if hit:
                t = hit.to_tuple()
                actor = t[9]
                out.append([round(x), round(y), round(t[4].z), actor.get_actor_label() if actor else ''])
            y += step
        x += step
    return json.dumps(out)


def side(arg=''):
    """Horizontal trace 'x,y,z,dx,dy' (direction) in the PIE world: hit point and actor."""
    x, y, z, dx, dy = [float(v) for v in arg.split(',')]
    world = _game_world() or _editor_world()
    a = unreal.Vector(x, y, z)
    hit = unreal.SystemLibrary.line_trace_single(world, a, a + unreal.Vector(dx, dy, 0) * 1000,
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
                                                 unreal.DrawDebugTrace.NONE, True)
    if not hit:
        return 'none'
    t = hit.to_tuple()
    return json.dumps([round(t[4].x), round(t[4].y), round(t[4].z), t[9].get_actor_label() if t[9] else ''])


def import_props(arg=''):
    """Import tools/ue58/gen_bar_prep.py output (SourceArt/Models/BarPrep) to /Game/Custom/BarPrep/<name>; each in a
    fresh folder (a reimport keeps old materials). arg: comma list of names, empty = all. PIE must be stopped."""
    import mare_hotel_lobby as hl
    from pathlib import Path
    if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():
        raise RuntimeError('Stop PIE first')
    src = Path(unreal.Paths.project_dir()) / 'SourceArt/Models/BarPrep'
    names = [n for n in arg.split(',') if n] or sorted(p.stem for p in src.glob('*.glb'))
    out = {}
    for name in names:
        # The clear work glass is translucent (no Nanite); the bench gets exact collision (the player walks round it).
        folder = f'/Game/Custom/BarPrep/{name}'
        # A reimport keeps the old materials: start from an empty folder.
        if unreal.EditorAssetLibrary.does_directory_exist(folder):
            unreal.EditorAssetLibrary.delete_directory(folder)
        # Translucent meshes (the clear glass, the drink) cannot be Nanite.
        mesh = hl._import(src / f'{name}.glb', folder, name, name not in ('BarPrep_glass', 'BarPrep_layer_liquid'), search=False)
        if name == 'BarPrep_bench':
            hl._complex_collision(mesh)
        b = mesh.get_bounds()
        out[name] = [round(b.box_extent.x * 2, 1), round(b.box_extent.y * 2, 1), round(b.box_extent.z * 2, 1)]
    return json.dumps(out)


def mat_params(arg='BarPrep_layer_liquid'):
    mesh = unreal.load_asset(f'/Game/Custom/BarPrep/{arg}/{arg}')
    out = []
    for sm in mesh.get_editor_property('static_materials'):
        mi = sm.get_editor_property('material_interface')
        names = []
        if isinstance(mi, unreal.MaterialInstance):
            for p in mi.get_editor_property('vector_parameter_values'):
                names.append(str(p.get_editor_property('parameter_info').get_editor_property('name')))
            names.append('parent=' + mi.get_editor_property('parent').get_path_name())
        out.append([mi.get_path_name() if mi else None, type(mi).__name__, names])
    return json.dumps(out)


def _tint_material(name, translucent):
    lib = unreal.MaterialEditingLibrary
    path = f'/Game/Custom/BarPrep/{name}'
    m = unreal.load_asset(path)
    if not m:
        m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, '/Game/Custom/BarPrep', unreal.Material, unreal.MaterialFactoryNew())
    lib.delete_all_material_expressions(m)
    tint = lib.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -400, 0)
    tint.set_editor_property('parameter_name', 'Tint')
    tint.set_editor_property('default_value', unreal.LinearColor(.9, .85, .6, 1))
    rough = lib.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, 200)
    rough.set_editor_property('parameter_name', 'Roughness')
    rough.set_editor_property('default_value', .08 if translucent else .45)
    lib.connect_material_property(tint, '', unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    if translucent:
        op = lib.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, 400)
        op.set_editor_property('parameter_name', 'Opacity')
        op.set_editor_property('default_value', .55)
        lib.connect_material_property(op, '', unreal.MaterialProperty.MP_OPACITY)
        m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_TRANSLUCENT)
        m.set_editor_property('translucency_lighting_mode', unreal.TranslucencyLightingMode.TLM_SURFACE)
        m.set_editor_property('used_with_nanite', False)
    else:
        m.set_editor_property('blend_mode', unreal.BlendMode.BLEND_OPAQUE)
        m.set_editor_property('used_with_nanite', True)
    errors = lib.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, False)
    return m, [str(e) for e in errors or []]


def drink_material(arg=''):
    """M_BarDrink (translucent drink, Tint + Opacity) on the liquid layer and M_BarFruit (opaque, Tint) on the fruit
    pieces: the game sets their colours per mix. PIE must be stopped."""
    drink, e1 = _tint_material('M_BarDrink', True)
    fruit, e2 = _tint_material('M_BarFruit', False)
    for name, m in (('BarPrep_layer_liquid', drink), ('BarPrep_layer_fruit', fruit)):
        mesh = unreal.load_asset(f'/Game/Custom/BarPrep/{name}/{name}')
        mesh.set_material(0, m)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    g = unreal.load_asset('/Game/Custom/BarPrep/BarPrep_glass/BarPrep_glass_Clear')
    return json.dumps({'errors': e1 + e2, 'glass_blend': str(g.get_editor_property('blend_mode'))})

def clear_floor(arg=''):
    """Remove plants whose bounds poke into the bar floor (x 1100..1540, y -1510..-1090); arg 'dry' only lists."""
    world = _editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        o, e = a.get_actor_bounds(False)
        if 1100 < o.x < 1540 and -1510 < o.y < -1090 and o.z < 150:
            label = a.get_actor_label()
            if any(k in label.lower() for k in ('fern', 'plant', 'shrub', 'bush', 'palm')):
                out.append([label, round(o.x), round(o.y), round(o.z)])
                if arg != 'dry':
                    a.destroy_actor()
    if out and arg != 'dry':
        unreal.EditorLevelLibrary.save_current_level()
    return json.dumps(out)


def find_label(arg='Fern'):
    world = _editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if arg.lower() in a.get_actor_label().lower():
            o, e = a.get_actor_bounds(False)
            out.append([a.get_actor_label(), a.get_class().get_name(), round(o.x), round(o.y), round(o.z), round(e.x), round(e.y)])
    return json.dumps(out[:40])


def clear_instances(arg='Fern_1'):
    """Remove the instances of an instanced actor (label contains arg; '|dry' only lists) inside the bar floor."""
    name, _, dry = arg.partition('|')
    world = _editor_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if name.lower() not in a.get_actor_label().lower():
            continue
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            hits = []
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True).translation
                if 1100 < t.x < 1540 and -1510 < t.y < -1090:
                    hits.append(i)
                    out.append([c.get_name(), i, round(t.x), round(t.y), round(t.z)])
            if not dry:
                for i in sorted(hits, reverse=True):
                    c.remove_instance(i)
    if out and not dry:
        unreal.EditorLevelLibrary.save_current_level()
    return json.dumps(out)


def qa(arg=''):
    """PIE: run 'pick:id;pour;step:socar=1;discard;use' on the bar prep and report hand/glass/next step."""
    world = _game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    sim = pc.get_simulation()
    log = []
    for cmd in [c for c in arg.split(';') if c]:
        if cmd.startswith('pick:'):
            log.append([cmd, sim.bar_pick(cmd[5:])])
        elif cmd == 'pour':
            log.append([cmd, sim.bar_pour()])
        elif cmd.startswith('step:'):
            k, v = cmd[5:].split('=')
            log.append([cmd, sim.bar_prep_step(k, float(v))])
        elif cmd == 'restock':
            log.append([cmd, sim.restock_bar()])
        elif cmd == 'discard':
            log.append([cmd, sim.bar_discard()])
        elif cmd == 'use':
            pc.use_bar_glass()
            log.append([cmd, 'ok'])
        elif cmd.startswith('game:'):
            pc.start_bar_prep(cmd[5:])
            log.append([cmd, 'ok'])
    return json.dumps(log)


def state(arg=''):
    world = _game_world()
    sim = unreal.GameplayStatics.get_player_controller(world, 0).get_simulation()
    return json.dumps({'msg': sim.get_editor_property('last_message'), 'hand': sim.bar_hand() if hasattr(sim, 'bar_hand') else '?'})


def glass_info(arg=''):
    world = _game_world()
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        l = a.get_actor_location()
        if abs(l.x - 1478) < 5 and abs(l.y + 1300) < 5:
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                m = c.get_editor_property('static_mesh')
                out.append([m.get_name() if m else None, c.is_visible(), round(c.get_editor_property('relative_scale3d').z, 2),
                            [round(x) for x in (c.get_world_location().x, c.get_world_location().y, c.get_world_location().z)]])
    return json.dumps(out)



def cam(arg=''):
    """PIE: 'x,y,z,pitch,yaw' puts a camera there as the view target; 'off' gives the view back to the hero."""
    world = _game_world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    if arg == 'off':
        pc.set_view_target_with_blend(pc.get_controlled_pawn())
        return 'off'
    x, y, z, p, yw = [float(v) for v in arg.split(',')]
    # Any camera actor of the running level (Python cannot spawn into the PIE world here).
    found = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.CameraActor)
    if not found:
        return 'no camera actor'
    c = found[0]
    c.set_actor_location_and_rotation(unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=p, yaw=yw), False, False)
    c.camera_component.set_editor_property('field_of_view', 50)
    pc.set_view_target_with_blend(c)
    return 'cam'


def phone(arg='7'):
    """PIE: open the phone on a tab (7 = Drinks once the bar is bought)."""
    pc = unreal.GameplayStatics.get_player_controller(_game_world(), 0)
    pc.open_phone(int(arg))
    return 'ok'


def upgrades(arg='neon,chopeira,freezer'):
    """PIE: buy one level of each upgrade listed."""
    sim = unreal.GameplayStatics.get_player_controller(_game_world(), 0).get_simulation()
    return json.dumps([[u, sim.buy_bar_upgrade(u)] for u in arg.split(',') if u])


def hero_parts(arg=''):
    """PIE: the hero's skeletal mesh components, whether the owner sees them and the arm bones' hidden state."""
    pawn = unreal.GameplayStatics.get_player_controller(_game_world(), 0).get_controlled_pawn()
    out = []
    for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent):
        m = c.get_editor_property('skeletal_mesh_asset') if hasattr(c, 'skeletal_mesh_asset') else None
        try:
            m = c.get_skinned_asset()
        except Exception:
            pass
        out.append([c.get_name(), m.get_name() if m else None, c.is_visible(), c.get_editor_property('only_owner_see'), c.get_editor_property('owner_no_see'),
                    c.is_bone_hidden_by_name('upperarm_r'), str(c.get_attach_parent().get_name()) if c.get_attach_parent() else None,
                    str(c.get_editor_property('leader_pose_component').get_name()) if c.get_editor_property('leader_pose_component') else None])
    return json.dumps(out)


def fix_usage(arg=''):
    """Every opaque material under /Game/Custom/BarPrep gets the Nanite (and ISM) usage flags; PIE must be stopped."""
    if _game_world():
        raise RuntimeError('Stop PIE first')
    fixed = []
    for p in unreal.EditorAssetLibrary.list_assets('/Game/Custom/BarPrep', recursive=True):
        a = unreal.load_asset(p)
        if not isinstance(a, unreal.Material):
            continue
        if a.get_editor_property('blend_mode') != unreal.BlendMode.BLEND_OPAQUE:
            continue
        changed = False
        for flag in ('used_with_nanite', 'used_with_instanced_static_meshes'):
            if not a.get_editor_property(flag):
                a.set_editor_property(flag, True)
                changed = True
        if changed:
            unreal.MaterialEditingLibrary.recompile_material(a)
            unreal.EditorAssetLibrary.save_loaded_asset(a, False)
            fixed.append(a.get_name())
    return json.dumps(fixed)


def neon_material(arg=''):
    """M_BarNeonPink / M_BarNeonCyan: emissive tubes for the neon sign (Interchange drops the glTF emission); assigned
    to the sign's Glow slots. PIE must be stopped."""
    lib = unreal.MaterialEditingLibrary
    out = {}
    made = {}
    for name, col in (('M_BarNeonPink', (1, .25, .65)), ('M_BarNeonCyan', (.25, 1, .9))):
        m = unreal.load_asset(f'/Game/Custom/BarPrep/{name}')
        if not m:
            m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, '/Game/Custom/BarPrep', unreal.Material, unreal.MaterialFactoryNew())
        lib.delete_all_material_expressions(m)
        c = lib.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -600, 0)
        c.set_editor_property('parameter_name', 'Color')
        c.set_editor_property('default_value', unreal.LinearColor(*col, 1))
        k = lib.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, 200)
        k.set_editor_property('parameter_name', 'Strength')
        k.set_editor_property('default_value', 18)
        mul = lib.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, 100)
        lib.connect_material_expressions(c, '', mul, 'A')
        lib.connect_material_expressions(k, '', mul, 'B')
        lib.connect_material_property(c, '', unreal.MaterialProperty.MP_BASE_COLOR)
        lib.connect_material_property(mul, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        m.set_editor_property('used_with_nanite', True)
        out[name] = [str(e) for e in lib.recompile_material(m) or []]
        unreal.EditorAssetLibrary.save_loaded_asset(m, False)
        made[name] = m
    mesh = unreal.load_asset('/Game/Custom/BarPrep/BarPrep_neon/BarPrep_neon')
    slots = mesh.get_editor_property('static_materials')
    for i, sm in enumerate(slots):
        n = sm.get_editor_property('material_interface').get_name()
        if n.endswith('GlowCyan'):
            mesh.set_material(i, made['M_BarNeonCyan'])
            out['slot%d' % i] = 'cyan'
        elif n.endswith('Glow'):
            mesh.set_material(i, made['M_BarNeonPink'])
            out['slot%d' % i] = 'pink'
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    return json.dumps(out)
