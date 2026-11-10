"""Visual fixes from the 09/11 map and detail survey (docs/ue58/CHECKLIST_VISUAL_2026-11-09.md).

Editor, PIE stopped: mare_hud module "mare_fix_0911.run|". Reexecutable: every step looks its target up by label and
sets an absolute state (hidden, material, transform from a stored original), so a second run changes nothing."""
import json
import unreal

MEL = unreal.MaterialEditingLibrary


def _world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def _actors(label):
    return [a for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.Actor) if a.get_actor_label() == label]


def hide(labels):
    """Hide in game and drop collision."""
    n = []
    for label in labels:
        for a in _actors(label):
            a.set_actor_hidden_in_game(True)
            a.set_actor_enable_collision(False)
            n.append(label)
    return n


def material_of(fragment):
    hits = [p for p in unreal.EditorAssetLibrary.list_assets('/Game', recursive=True) if fragment in p]
    return unreal.load_asset(hits[0]) if hits else None


def kiosk_block(_=None):
    """Cube_003 is three ISM groups of the kiosk's pastry shelf (boards, top, trays), not a block of the counter: seen
    from behind it reads as a cream box, from the front it is a cream shelf unit. A first pass gave it the counter's
    wood and left it two-toned (dark boards, cream sides): the overrides are cleared, back to the mesh materials."""
    out = []
    for a in _actors('Maré · Cube_003'):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            for i in range(c.get_num_materials()):
                c.set_material(i, None)
            out.append(c.get_name())
    return out


def kiosk_fix(_=''):
    out = kiosk_block()
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out)


def towel(_=None):
    """House bathroom: the towel (Cube_018) and its bar sat across the door frame; 35 cm away from the door (-X)."""
    out = []
    for label, mesh in (('Maré · Cube_018', 'World_1154'), ('Maré · @MeshInstance3D@2829', 'World_0900')):
        for a in _actors(label):
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                if not c.static_mesh or c.static_mesh.get_name() != mesh:
                    continue
                for i in range(c.get_instance_count()):
                    t = c.get_instance_transform(i, True)
                    p = t.translation
                    if abs(p.y - 1730) > 40 or not (4600 < p.x < 4760) or p.z < 60:
                        continue
                    box = c.static_mesh.get_bounding_box()
                    if label.endswith('2829') and (box.max.z - box.min.z) > 30:
                        continue   # only the thin bar, not a wall piece
                    t.translation = unreal.Vector(4660 if label.endswith('018') else 4649, p.y, p.z)
                    c.update_instance_transform(i, t, True, True, True)
                    out.append([label, i, round(p.x), '->', round(t.translation.x)])
    return out


def suite_stone(_=None):
    """Suite: the 'Stone' slot (TV wall, vanity top, basins, tub, shower tray) used Poly Haven plaster_stone_wall_01, a
    white plaster with grey stones that read as spots; a smooth warm white stone with a faint veining instead."""
    path = '/Game/World/Materials/M_SuiteStone'
    mat = unreal.load_asset(path)
    if not mat:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_SuiteStone', '/Game/World/Materials', unreal.Material, unreal.MaterialFactoryNew())
    for old in list(MEL.get_material_expressions(mat)):
        MEL.delete_material_expression(mat, old)
    wp = MEL.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -700, 0)
    node = MEL.create_material_expression(mat, unreal.MaterialExpressionCustom, -350, 0)
    node.set_editor_property('code', 'float2 p = P.xy * 0.004 + P.z * 0.003; float v = sin(p.x * 3.1 + sin(p.y * 2.3) * 2.0) * 0.5 + 0.5; '
                                     'return lerp(float3(0.80, 0.78, 0.74), float3(0.70, 0.68, 0.64), smoothstep(0.85, 1.0, v) * 0.6);')
    node.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ci = unreal.CustomInput()
    ci.set_editor_property('input_name', 'P')
    node.set_editor_property('inputs', [ci])
    MEL.connect_material_expressions(wp, '', node, 'P')
    MEL.connect_material_property(node, '', unreal.MaterialProperty.MP_BASE_COLOR)
    rough = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 200)
    rough.set_editor_property('r', 0.32)
    MEL.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mat.set_editor_property('used_with_nanite', True)
    mat.set_editor_property('used_with_instanced_static_meshes', True)
    MEL.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    out = []
    for a in _actors('Hotel · suíte'):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            names = [str(n) for n in c.get_material_slot_names()]
            for i, n in enumerate(names):
                if n.endswith('Stone'):
                    c.set_material(i, mat)
                    out.append(n)
    return out


def run(_=''):
    import mare_probe_near
    res = {'hide': hide(['Maré · @MeshInstance3D@315', 'Maré · @MeshInstance3D@316']),   # pousada: blank blue sign and its post
           'kiosk_block': kiosk_block(), 'towel': towel(), 'suite_stone': suite_stone()}
    res['coast_rocks'] = json.loads(mare_probe_near.coast_rocks('apply'))[-1]
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(res, ensure_ascii=False)


def coast_rock_mesh(_=''):
    """The 9 'coast_line_01' scans (flat slab with straight cut faces: a brown box on the beach even sunk and tilted)
    become Poly Haven rock_07 boulders, ~2.6 m across, random yaw, on the ground under them and 15 % sunk."""
    import math
    # rock_07 (Poly Haven, 32 x 17 x 14 cm) scaled ~5x: a chunky boulder (rock_09 is a flat pebble)
    rock = unreal.load_asset(_ or '/Game/Custom/Beach/rock_07/rock_071')
    box = rock.get_bounding_box()
    size = max(box.max.x - box.min.x, box.max.y - box.min.y)
    h = box.max.z - box.min.z
    s = 260.0 / size
    out = []
    for a in _actors('Ilha · rochas da costa'):
        if 'MareRockSwap' in [str(t) for t in a.tags] and not _:
            return json.dumps(['already swapped'])
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if not c.static_mesh or c.get_name() != 'HISM_coast_coast_line_01':
                continue
            ts = [c.get_instance_transform(i, True) for i in range(c.get_instance_count())]
            c.set_static_mesh(rock)
            for i, t in enumerate(ts):
                k = s * (0.8 + 0.4 * abs(math.sin(i * 7.3)))
                t.scale3d = unreal.Vector(k, k, k * 0.9)
                t.rotation = unreal.Rotator(roll=4 * math.sin(i), pitch=4 * math.cos(i * 1.3), yaw=(i * 73) % 360).quaternion()
                # the ground under it (terrain, sand or sea floor; the rocks themselves ignored), then 15 % sunk
                x, y = t.translation.x, t.translation.y
                hit = unreal.SystemLibrary.line_trace_single(_world(), unreal.Vector(x, y, 3000), unreal.Vector(x, y, -3000),
                                                             unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a], unreal.DrawDebugTrace.NONE, True)
                gz = hit.to_tuple()[4].z if hit else t.translation.z
                t.translation = unreal.Vector(x, y, gz - box.min.z * k * 0.9 - h * k * 0.9 * 0.15)
                c.update_instance_transform(i, t, True, True, True)
            out.append([c.get_name(), len(ts), round(size), round(h)])
        if 'MareRockSwap' not in [str(t) for t in a.tags]:
            a.tags = list(a.tags) + ['MareRockSwap']
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out)


def fix2(_=''):
    """Second pass: the pousada's blank sign hidden at component level (the expansion refresh shows the actors again
    when the pousada is bought); the towel bar off the bathroom door frame too."""
    out = []
    for label in ('Maré · @MeshInstance3D@315', 'Maré · @MeshInstance3D@316'):
        for a in _actors(label):
            for c in a.get_components_by_class(unreal.PrimitiveComponent):
                c.set_visibility(False, True)
                c.set_hidden_in_game(True)
                c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            out.append(label)
    for a in _actors('Maré · @MeshInstance3D@2829'):
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                p = t.translation
                if abs(p.y - 1750) < 5 and abs(p.z - 129) < 5 and 4600 < p.x < 4710:
                    t.translation = unreal.Vector(4649, p.y, p.z)
                    c.update_instance_transform(i, t, True, True, True)
                    out.append(['bar', i])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out, ensure_ascii=False)


def hide_coast_slabs(_=''):
    """09/11: no replacement for the 9 'coast_line_01' slabs read well (flat cut slab; a pebble scaled up; a cluster
    that floats); the group is hidden: the coast has its other sandstone rocks."""
    out = []
    for a in _actors('Ilha · rochas da costa'):
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if c.get_name() == 'HISM_coast_coast_line_01':
                c.set_visibility(False)
                c.set_hidden_in_game(True)
                c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                out.append(c.get_name())
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out)


def label_info(arg='Maré · Cube_003'):
    """Every static mesh component of the actors with this label: class, mesh, mesh default materials, override
    materials, instance count and the first instances."""
    out = []
    for a in _actors(arg):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            row = {'comp': c.get_name(), 'cls': type(c).__name__, 'mesh': m.get_name() if m else None,
                   'default': [s.material_interface.get_name() if s.material_interface else None for s in m.get_editor_property('static_materials')] if m else [],
                   'now': [c.get_material(i).get_name() if c.get_material(i) else None for i in range(c.get_num_materials())]}
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                row['n'] = c.get_instance_count()
                row['inst'] = []
                for i in range(min(12, c.get_instance_count())):
                    t = c.get_instance_transform(i, True)
                    row['inst'].append([round(t.translation.x), round(t.translation.y), round(t.translation.z)])
            else:
                l = c.get_world_location()
                row['at'] = [round(l.x), round(l.y), round(l.z)]
            out.append(row)
    return json.dumps(out, ensure_ascii=False)


TRUCK_MATS = {}   # slot suffix of mare_truck_rear -> material of the truck mesh (World_2362), filled by truck_rear


def truck_rear(arg=''):
    """Village food truck: from the main street its back was a plain red cap. `mare_truck_rear`
    (tools/ue58/gen_truck_rear.py: doors, lock bars, lamp clusters, plate, step) goes over the cap, in the truck's own
    frame, as an actor of the same region (Region_Biz_food_truck: shown only when the business is owned).
    arg 'Paint=MA_x,Stripe=MA_y,Chrome=MA_z' re-points those slots to the truck's own materials."""
    truck = _actors('Maré · biz_food_truck')[0]
    inst = truck.get_components_by_class(unreal.InstancedStaticMeshComponent)[0]
    t = inst.get_instance_transform(0, True)
    mesh = unreal.load_asset(json.load(open(unreal.Paths.project_content_dir() + 'Data/custom_assets.json', encoding='utf-8'))['mare_truck_rear'])
    label = 'Vila · traseira do food truck'
    old = _actors(label)
    a = old[0] if old else unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.StaticMeshActor, t.translation)
    a.set_actor_label(label)
    a.set_actor_transform(t, False, True)
    a.set_folder_path(truck.get_folder_path())
    a.tags = [tag for tag in truck.tags]
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    c.set_mobility(unreal.ComponentMobility.STATIC)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)   # the navigation is static: nothing new to bump into
    c.set_editor_property('generate_overlap_events', False)
    want = dict(TRUCK_MATS)
    for pair in [p for p in arg.split(',') if '=' in p]:
        k, v = pair.split('=')
        want[k.strip()] = v.strip()
    done = []
    for i, n in enumerate(str(s) for s in c.get_material_slot_names()):
        key = n.split('_')[-1]
        if key in want:
            m = unreal.load_asset('/Game/World/Models/World_2362/' + want[key])
            if m:
                c.set_material(i, m)
                done.append([key, want[key]])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    l = a.get_actor_location()
    return json.dumps({'at': [round(l.x), round(l.y), round(l.z)], 'tags': [str(x) for x in a.tags], 'slots': [str(s) for s in c.get_material_slot_names()], 'mats': done}, ensure_ascii=False)


SEA_Z = -30.0   # Godot WATER_Y -0.3 m


def _hill_instances():
    """(actor, component, index, world transform, mesh box) of every ISM instance whose material is the hill ground."""
    world = _world()
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            m = c.static_mesh
            if not m or c.get_num_materials() == 0:
                continue
            mat = c.get_material(0)
            if not mat or 'HillGround' not in mat.get_name():
                continue
            box = m.get_bounding_box()
            for i in range(c.get_instance_count()):
                yield a, c, i, c.get_instance_transform(i, True), box


def _corners(t, box, inset=0.0):
    """World XY of the footprint corners and centre of an instance (mesh box through the instance transform)."""
    pts = []
    for fx, fy in ((0, 0), (1, 0), (1, 1), (0, 1), (.5, .5), (.5, 0), (1, .5), (.5, 1), (0, .5)):
        x = box.min.x + (box.max.x - box.min.x) * (inset + fx * (1 - 2 * inset))
        y = box.min.y + (box.max.y - box.min.y) * (inset + fy * (1 - 2 * inset))
        for z in (box.min.z, box.max.z):
            pts.append(unreal.MathLibrary.transform_location(t, unreal.Vector(x, y, z)))
    return pts


def hill_blocks(arg='list'):
    """09/11 checklist: flat rectangles under the shallow water of the west cove and the south-west coast are the
    straight bases of the Godot hill blocks (hill ground material) running into the sea. 'list': every hill block
    instance with its world box and, traced with the hill actors ignored, how many of its 9 footprint samples have the
    island ground below sea level (those parts show through the water)."""
    world = _world()
    rows = list(_hill_instances())
    ignore = list({r[0] for r in rows})
    out = []
    for a, c, i, t, box in rows:
        pts = _corners(t, box)
        xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
        wet = 0
        low = []
        for p in pts[::2]:
            hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(p.x, p.y, 30000), unreal.Vector(p.x, p.y, -3000),
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
                                                         unreal.DrawDebugTrace.NONE, True)
            tt = hit.to_tuple() if hit else None
            z = tt[4].z if tt else -9999
            low.append(round(z))
            if z < SEA_Z:
                wet += 1
        if arg == 'list' and wet == 0 and min(zs) > SEA_Z:
            continue
        out.append({'actor': a.get_actor_label(), 'comp': c.get_name(), 'mesh': c.static_mesh.get_name(), 'i': i,
                    'x': [round(min(xs)), round(max(xs))], 'y': [round(min(ys)), round(max(ys))],
                    'z': [round(min(zs)), round(max(zs))], 'wet': wet, 'ground': low})
    return json.dumps({'total': len(rows), 'hits': len(out), 'rows': out[:120]}, ensure_ascii=False)


def hill_cut(arg=''):
    """09/11 checklist (west cove: pale stair-step rectangles under the shallow water): rebuilds M_HillGround_PBR: under the
    water the hill tiles turn to the island floor's sand and are lifted (their -2.2 m skirt to about -1.15 m), and
    gen_island_terrain.py no longer lays new sea floor over them. PIE stopped."""
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    mat = mare_materials.build_hill_ground()
    return json.dumps({'material': mat.get_path_name(), 'blend': str(mat.get_editor_property('blend_mode'))})


def seabed_mat(arg=''):
    """09/11: rebuilds M_IslandSeabed_PBR (the sea floor all round the island is the lit sand bed with caustics). PIE stopped."""
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    mat = mare_materials.build_ground(seabed=True)
    return mat.get_path_name()


def lobby_panels(arg=''):
    """Grand Hotel lobby, west wall: the hotel_tower mesh carries three flat brown slabs (0.83 x 2.07 m, 0.6 m off the
    floor) that read as fake doors. A slatted oak panel (tools/ue58/gen_lobby_slat_panel.py) goes over each, with the
    lobby's own tags (shown only with the hotel). Centres measured on the wall (pie_pick on the slab edges)."""
    mesh = unreal.load_asset(json.load(open(unreal.Paths.project_content_dir() + 'Data/custom_assets.json', encoding='utf-8'))['mare_lobby_slat_panel'])
    ref = _actors('Hotel lobby · hanging_picture_frame_03')[0]
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    out = []
    # (centre y, slab width cm): four slabs symmetric about the lobby axis (y 6342), measured with pie_pick from the
    # player's own view (09/11); 0.6 m off the floor (z 103..307). Each panel is 3 cm wider than its slab on both sides.
    slabs = ((6731.0, 114.0), (6481.0, 92.0), (6203.0, 92.0), (5951.5, 117.0))
    for old in _actors('Hotel lobby · painel ripado'):
        if not any(old.get_actor_label() == f'Hotel lobby · painel ripado {k + 1}' for k in range(len(slabs))):
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(old)
    for i, (y, width) in enumerate(slabs):
        label = f'Hotel lobby · painel ripado {i + 1}'
        old = _actors(label)
        a = old[0] if old else actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
        a.set_actor_label(label)
        # front of the panel is its local +Y: yaw -90 turns it to +X, into the lobby; back against the wall (x -3645)
        a.set_actor_location_and_rotation(unreal.Vector(-3645.0, y, 100.0), unreal.Rotator(roll=0, pitch=0, yaw=-90), False, True)
        a.set_actor_scale3d(unreal.Vector((width + 6.0) / 90.0, 1.0, 1.0))
        a.set_folder_path(ref.get_folder_path())
        a.tags = [t for t in ref.tags]
        c = a.static_mesh_component
        c.set_static_mesh(mesh)
        c.set_mobility(unreal.ComponentMobility.STATIC)
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        c.set_editor_property('generate_overlap_events', False)
        o, e = a.get_actor_bounds(False)
        out.append([label, [round(o.x), round(o.y), round(o.z)], [round(e.x), round(e.y), round(e.z)]])
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'tags': [str(t) for t in ref.tags], 'panels': out}, ensure_ascii=False)


SUITE_O = (-2800.0, 6342.0, 854.0)   # suite origin on the floor boards (mare_beach.SUITE_ORIGIN + 3 cm)
# (slug, x, y, facing (world dx, dy), base z m above the floor). Poly Haven models face their local +Y.
SUITE_EXTRA = [
    # living: rattan sofa facing the TV wall (replaces the carved sofa_03, side-on; Sofa_01 was carved too), side tables
    ('fab_rattan_sofa', -.5, 1.65, (0, -1), 0), ('side_table_01', -1.75, 1.65, (0, -1), 0), ('side_table_01', .75, 1.65, (0, -1), 0),
    # south-east corner (was bare floor): dining table for six, sideboard with a vase on the east wall, plant
    ('dining_table', 5.8, -2.9, (0, 1), 0),
    ('dining_chair_02', 5.25, -2.05, (0, -1), 0), ('dining_chair_02', 6.35, -2.05, (0, -1), 0),
    ('dining_chair_02', 5.25, -3.75, (0, 1), 0), ('dining_chair_02', 6.35, -3.75, (0, 1), 0),
    ('dining_chair_02', 4.45, -2.9, (1, 0), 0), ('dining_chair_02', 7.15, -2.9, (-1, 0), 0),
    ('modern_wooden_cabinet', 8.37, -2.9, (-1, 0), 0), ('ceramic_vase_03', 8.3, -2.3, (-1, 0), .64),
    ('potted_plant_02', 8.0, -.6, (-1, 0), 0),
    # bedroom: ottoman at the foot of the bed, reading corner by the south window
    # (clear of the big potted plant fab:145 at -7.8, -4.9)
    ('Ottoman_01', -5.75, -.55, (1, 0), 0), ('mid_century_lounge_chair', -6.6, -3.7, (.7, .7), 0),
    ('side_table_01', -5.75, -4.35, (0, 1), 0),
]


def suite_extra(arg=''):
    """09/11 checklist (suite almost empty, carved old sofa side-on to the TV): adds furniture to the suite (tags of the
    suite, so place_suite's clean-up removes it too) and hides sofa_03. Re-runnable."""
    import math
    import mare_hotel_rooms
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in _actors_prefix('Hotel suíte · extra '):
        actors.destroy_actor(a)
    for a in _actors('Hotel suíte · sofa_03'):
        a.set_actor_hidden_in_game(True)
        a.set_is_temporarily_hidden_in_editor(True)
        a.static_mesh_component.set_visibility(False)
        a.set_actor_enable_collision(False)
    tags = [unreal.Name('MareGenerated'), unreal.Name('Region_grand_hotel'), unreal.Name('MareSuitePart')]
    ox, oy, oz = SUITE_O
    out = []
    for i, (slug, x, y, face, z) in enumerate(SUITE_EXTRA):
        mesh = mare_hotel_rooms._mesh(slug)   # catalogue (custom_assets.json) or library model
        b = mesh.get_bounds()
        base = oz + z * 100.0 - (b.origin.z - b.box_extent.z)
        yaw = math.degrees(math.atan2(face[1], face[0])) - 90.0
        a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(ox + x * 100, oy + y * 100, base), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
        a.static_mesh_component.set_static_mesh(mesh)
        a.set_actor_label(f'Hotel suíte · extra {i:02d} {slug}')
        a.tags = tags
        a.set_folder_path('Hotel/Suite')
        out.append(slug)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'placed': out})


def _actors_prefix(prefix):
    return [a for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.Actor) if a.get_actor_label().startswith(prefix)]


def annex_dress(arg=''):
    """Hero house bathroom annex (09/11 checklist: plain wall, no window): window and base band
    (tools/ue58/gen_annex_dress.py) in the annex frame, origin UE (4775, 1418, 0). Same tags as the annex mesh."""
    mesh = unreal.load_asset(json.load(open(unreal.Paths.project_content_dir() + 'Data/custom_assets.json', encoding='utf-8'))['mare_annex_dress'])
    ref = _actors('Maré · @MeshInstance3D@2930')[0]
    label = 'Casa do herói · janela e barrado do anexo'
    old = _actors(label)
    a = old[0] if old else unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
    a.set_actor_label(label)
    a.set_actor_location_and_rotation(unreal.Vector(4775.0, 1418.0, 0.0), unreal.Rotator(roll=0, pitch=0, yaw=0), False, True)
    a.set_folder_path(ref.get_folder_path())
    a.tags = [t for t in ref.tags]
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    c.set_mobility(unreal.ComponentMobility.STATIC)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    o, e = a.get_actor_bounds(False)
    return json.dumps({'tags': [str(t) for t in a.tags], 'bounds': [round(o.x), round(o.y), round(o.z), round(e.x), round(e.y), round(e.z)]})


def manholes(arg=''):
    """Village manhole covers (09/11 checklist: plain round discs): the 24 instances of 'Maré · Bueiro' get the cast-iron
    cover (tools/ue58/gen_manhole.py), same transforms. arg 'revert' puts the Godot cylinder back."""
    actor = _actors('Maré · Bueiro')[0]
    comp = actor.get_components_by_class(unreal.InstancedStaticMeshComponent)[0]
    if arg == 'revert':
        mesh = unreal.load_asset('/Game/World/Models/World_2263/World_2263')
    else:
        mesh = unreal.load_asset(json.load(open(unreal.Paths.project_content_dir() + 'Data/custom_assets.json', encoding='utf-8'))['mare_manhole'])
    comp.set_static_mesh(mesh)
    for i in range(comp.get_num_materials()):
        comp.set_material(i, None)   # the mesh's own materials
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'mesh': mesh.get_path_name(), 'instances': comp.get_instance_count()})


def floor_mats(arg=''):
    """Rebuilds the three sea-floor materials that share the caustics (island ground, island seabed, hill ground).
    PIE stopped."""
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    out = [mare_materials.build_ground(island=True).get_path_name(), mare_materials.build_ground(seabed=True).get_path_name(),
           mare_materials.build_hill_ground().get_path_name()]
    return json.dumps(out)


BUNGALOW_LOOKS = {
    # actor label: (painting texture file, wainscot texture file) in SourceArt/Textures/Custom
    'Bangalô 2': ('bungalow_art_pier.png', 'bungalow_wainscot_sand.png'),
    'Bangalô 3': ('bungalow_art_kiosk.png', 'bungalow_wainscot_sky.png'),
}


def _material_variant(src_path, name, old_fragment, new_tex):
    """Copy of an imported glTF material with one colour texture swapped."""
    MEL = unreal.MaterialEditingLibrary
    dst = src_path.rsplit('/', 1)[0] + '/' + name
    if not unreal.EditorAssetLibrary.does_asset_exist(dst):
        unreal.EditorAssetLibrary.duplicate_asset(src_path, dst)
    mat = unreal.load_asset(dst)
    swapped = 0
    for e in MEL.get_material_expressions(mat) if hasattr(MEL, 'get_material_expressions') else []:
        try:
            tex = e.get_editor_property('texture')
        except Exception:
            continue
        if tex and (old_fragment in tex.get_name() or tex.get_name().startswith('bungalow_')):
            e.set_editor_property('texture', new_tex)
            swapped += 1
    errors = list(MEL.recompile_material(mat))
    if errors or not swapped:
        raise RuntimeError(f'{name}: swapped {swapped}, {errors}')
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def bungalow_variety(arg=''):
    """09/11 checklist ("os três bangalôs são idênticos por dentro"): bungalows 2 and 3 get their own painting
    (watercolours made from photos of the game: the pier, the kiosk) and their own wainscot colour (sand, sky blue);
    bungalow 1 keeps the beach watercolour and the sage. Material overrides on the level actors; PIE stopped."""
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    base = '/Game/Custom/mare_bungalow_m5/mare_bungalow_'
    out = {}
    for label, (art, wain) in BUNGALOW_LOOKS.items():
        actor = _actors(label)[0]
        comp = actor.static_mesh_component
        tag = art.split('_')[-1].split('.')[0]
        looks = {
            'mare_bungalow_Painting': _material_variant(base + 'Painting', 'mare_bungalow_Painting_' + tag, 'beach_watercolor', mare_materials._custom_texture(art)),
            'mare_bungalow_Wainscot': _material_variant(base + 'Wainscot', 'mare_bungalow_Wainscot_' + wain.split('_')[-1].split('.')[0],
                                                        'distressed_painted_planks_153', mare_materials._custom_texture(wain)),
        }
        names = [str(n) for n in comp.get_material_slot_names()]
        for slot, mat in looks.items():
            comp.set_material(names.index(slot), mat)
        out[label] = [m.get_name() for m in looks.values()]
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out, ensure_ascii=False)


ROCK_ACTORS = ('Mare · Vegetação das montanhas', 'Ilha · rochas da costa')


def _rock_instances():
    """(actor, component, index, world transform, mesh box) of every rock instance of the two generated rock actors."""
    for label in ROCK_ACTORS:
        for a in _actors(label):
            for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
                m = c.static_mesh
                if not m or 'rock' not in m.get_name().lower():
                    continue
                box = m.get_bounding_box()
                for i in range(c.get_instance_count()):
                    yield a, c, i, c.get_instance_transform(i, True), box


def _ground_under(world, x, y, ignore):
    """(z, normal, label) of the ground under a point, rock actors ignored."""
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 30000), unreal.Vector(x, y, -4000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore,
                                                 unreal.DrawDebugTrace.NONE, True)
    t = hit.to_tuple() if hit else None
    if not t or not t[0]:
        return None
    return t[4].z, t[7], (t[9].get_actor_label() if t[9] else '')


def rocks_float(arg='list'):
    """09/11, Sergio: "rochas flutuando" on the west slope. 'list' or 'list:x0,x1,y0,y1' (cm): every rock instance
    with its size, tilt and the gap between the bottom of its box (centre and the four corners, inset 20%) and the
    ground traced with the rock actors ignored. Positive gap = air under the rock."""
    world = _world()
    region = [float(v) for v in arg.split(':')[1].split(',')] if ':' in arg else None
    ignore = [a for label in ROCK_ACTORS for a in _actors(label)]
    per = {}
    worst = []
    for a, c, i, t, box in _rock_instances():
        loc = t.translation
        if region and not (region[0] <= loc.x <= region[1] and region[2] <= loc.y <= region[3]):
            continue
        gaps = []
        for fx, fy in ((.5, .5), (.2, .2), (.8, .2), (.8, .8), (.2, .8)):
            p = unreal.MathLibrary.transform_location(t, unreal.Vector(box.min.x + (box.max.x - box.min.x) * fx,
                                                                         box.min.y + (box.max.y - box.min.y) * fy, box.min.z))
            g = _ground_under(world, p.x, p.y, ignore)
            gaps.append(round(p.z - g[0]) if g else None)
        g = _ground_under(world, loc.x, loc.y, ignore)
        s = t.scale3d
        size = [round((box.max.x - box.min.x) * s.x), round((box.max.y - box.min.y) * s.y), round((box.max.z - box.min.z) * s.z)]
        real = [v for v in gaps if v is not None]
        key = a.get_actor_label()[:4] + ' ' + c.static_mesh.get_name()
        d = per.setdefault(key, {'n': 0, 'centre': [], 'max': [], 'size_z': []})
        d['n'] += 1
        if real:
            d['centre'].append(gaps[0] if gaps[0] is not None else real[0])
            d['max'].append(max(real))
        d['size_z'].append(size[2])
        rot = t.rotation.rotator()
        worst.append({'k': key, 'i': i, 'at': [round(loc.x), round(loc.y), round(loc.z)], 'size': size,
                      'rot': [round(rot.pitch), round(rot.yaw), round(rot.roll)], 'gaps': gaps,
                      'ground': [round(g[0]), round(g[1].z, 2), g[2]] if g else None})
    summary = {}
    for k, d in per.items():
        def med(v):
            v = sorted(v)
            return v[len(v) // 2] if v else None
        summary[k] = {'n': d['n'], 'centre_med': med(d['centre']), 'centre_max': max(d['centre']) if d['centre'] else None,
                      'corner_max_med': med(d['max']), 'floating>30': sum(1 for v in d['max'] if v > 30), 'height_med': med(d['size_z'])}
    worst.sort(key=lambda r: -max([v for v in r['gaps'] if v is not None] or [0]))
    import pathlib
    pathlib.Path('D:/CodexTemp/rocks_float.json').write_text(json.dumps({'summary': summary, 'rows': worst}, ensure_ascii=False, indent=0), encoding='utf-8')
    return json.dumps({'summary': summary, 'worst': worst[:12]}, ensure_ascii=False)


ROCK_WORDS = ('rock', 'boulder', 'stone', 'coast_land', 'cliff')


def _all_rocks(region):
    """(actor, component, index or -1, world transform, mesh box) of every rock-like mesh in region [x0, x1, y0, y1],
    any actor (the Godot export groups too: coast_rocks_05, coast_land_rocks_02, sand_rocks...), at least 25 cm tall."""
    for a in unreal.GameplayStatics.get_all_actors_of_class(_world(), unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if not m or not any(w in m.get_name().lower() or w in a.get_actor_label().lower() for w in ROCK_WORDS):
                continue
            box = m.get_bounding_box()
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                items = [(i, c.get_instance_transform(i, True)) for i in range(c.get_instance_count())]
            else:
                items = [(-1, c.get_world_transform())]
            for i, t in items:
                l = t.translation
                if not (region[0] <= l.x <= region[1] and region[2] <= l.y <= region[3]):
                    continue
                if (box.max.z - box.min.z) * t.scale3d.z < 25:
                    continue
                yield a, c, i, t, box


def rocks_anywhere(arg='list:8000,13500,-7500,-1500'):
    """10/11, Sergio: "corrigiu as rochas flutuando perto do farol?". The 09/11 fix only measured the two generated rock
    actors; the lighthouse point has the Godot export rocks. 'list:x0,x1,y0,y1' measures every rock-like mesh there:
    gap between the bottom of its box (centre and four corners inset 20%) and the ground under it, every rock actor
    ignored (a rock on a rock is not ground). 'apply:...' lowers each rock whose WHOLE bottom is in the air (smallest gap
    > 6 cm) by that gap + 6 cm, so it sits in the sand. PIE stopped for apply (saves the level)."""
    mode, _, rest = arg.partition(':')
    region = [float(v) for v in rest.split(',')]
    world = _world()
    rocks = list(_all_rocks(region))
    rows, moved = [], 0
    hidden = [x for x in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
              if x.get_editor_property('hidden') or not x.static_mesh_component.is_visible()]
    for a, c, i, t, box in rocks:
        # 10/11: only the rock's own group is ignored; a rock resting on a visible slab of another group is seated
        # (ignoring every rock group called the pier-point stones 'floating' 3 m over the sea floor under the slab).
        ignore = [a] + hidden
        gaps = []
        for fx, fy in ((.5, .5), (.2, .2), (.8, .2), (.8, .8), (.2, .8)):
            p = unreal.MathLibrary.transform_location(t, unreal.Vector(box.min.x + (box.max.x - box.min.x) * fx,
                                                                         box.min.y + (box.max.y - box.min.y) * fy, box.min.z))
            g = _ground_under(world, p.x, p.y, ignore)
            gaps.append(round(p.z - g[0]) if g else None)
        real = [v for v in gaps if v is not None]
        low = min(real) if real else None
        l = t.translation
        row = {'label': a.get_actor_label()[:36], 'mesh': c.static_mesh.get_name()[:28], 'i': i,
               'at': [round(l.x), round(l.y), round(l.z)], 'h': round((box.max.z - box.min.z) * t.scale3d.z), 'gaps': gaps, 'min': low}
        rows.append(row)
        if mode == 'apply' and low is not None and low > 6:
            t.translation = unreal.Vector(l.x, l.y, l.z - (low + 6))
            if i >= 0:
                c.update_instance_transform(i, t, True, True, True)
            else:
                c.set_world_location(t.translation, False, False)
            row['lowered'] = low + 6
            moved += 1
    if mode == 'apply' and moved:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    rows.sort(key=lambda r: -(r['min'] if r['min'] is not None else -999))
    import pathlib
    pathlib.Path('D:/CodexTemp/rocks_anywhere.json').write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding='utf-8')
    return json.dumps({'rocks': len(rows), 'floating>6': sum(1 for r in rows if (r['min'] or 0) > 6),
                       'floating>20': sum(1 for r in rows if (r['min'] or 0) > 20), 'moved': moved, 'worst': rows[:10]}, ensure_ascii=False)


def farol_slab_base(arg=''):
    """10/11, Sergio: "rochas flutuando perto do farol". The rocks there rest on the big slab 'Maré · coast_rocks_02'
    (a 30 x 21 m platform); its edges hang over clear water with ~2 m of air down to the sand floor, so from the sea the
    slab and its rocks read as floating. A second copy of the slab, turned 180 degrees and 6% wider, goes under it with
    its top 15 cm under the water (-45), its sides reaching the sea floor: the slab now rises out of the sea. No
    collision (static navigation; it is under water). The pier-point stone that hung 2 m past the edge (x 8634) moves
    120 cm towards the middle of the slab and is seated again. 'revert' removes the base. PIE stopped; saves the level."""
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    label = 'Ilha · base submersa da laje do farol'
    for a in _actors(label):
        actors.destroy_actor(a)
    if arg == 'revert':
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        return 'reverted'
    slab = _actors('Maré · coast_rocks_02')[0]
    comp = slab.get_components_by_class(unreal.InstancedStaticMeshComponent)[0]
    t = comp.get_instance_transform(0, True)
    rot = t.rotation.rotator()
    # 10/11 (second photo from Sergio, "flutuando": an arm of the slab lying over the beach sand with a dark gap under
    # it): the base is now the slab itself, same place and turn, 2% narrower and twice as thick downwards, its top 40 cm
    # under the slab's top. Doubling the thickness doubles the relief of its top downwards only, so it never shows
    # above the slab; under every edge and arm of the slab there is rock down to the sand or the sea floor.
    base = actors.spawn_actor_from_class(unreal.StaticMeshActor, t.translation, rot)
    base.set_actor_label(label)
    base.set_folder_path(slab.get_folder_path())
    base.tags = [x for x in slab.tags]
    c = base.static_mesh_component
    c.set_static_mesh(comp.static_mesh)
    for k in range(comp.get_num_materials()):
        c.set_material(k, comp.get_material(k))
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    s = t.scale3d
    so, se = slab.get_actor_bounds(False)
    slab_top = so.z + se.z
    base.set_actor_scale3d(unreal.Vector(s.x * .98, s.y * .98, s.z * 2.0))
    o, e = base.get_actor_bounds(False)
    base.add_actor_world_offset(unreal.Vector(0, 0, slab_top - 40 - (o.z + e.z)), False, False)
    o2, e2 = base.get_actor_bounds(False)
    out = {'slab': [round(t.translation.x), round(t.translation.y), round(t.translation.z)], 'base_top': round(o2.z + e2.z),
           'base_bottom': round(o2.z - e2.z), 'base_extent': [round(e2.x), round(e2.y)]}
    # the stone hanging past the edge
    centre = t.translation
    for a, cc, i, rt, box in _all_rocks([8604, 8664, -4788, -4728]):   # its old place only: running again moves nothing
        if 'ponta do p' not in a.get_actor_label() or i < 0:
            continue
        l = rt.translation
        d = unreal.Vector(centre.x - l.x, centre.y - l.y, 0)
        n = (d.x ** 2 + d.y ** 2) ** .5 or 1
        rt.translation = unreal.Vector(l.x + d.x / n * 120, l.y + d.y / n * 120, l.z)
        cc.update_instance_transform(i, rt, True, True, True)
        out['moved'] = [round(l.x), round(l.y), '->', round(rt.translation.x), round(rt.translation.y)]
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps(out)


def waterline_ground(arg='list:7500,12500,-7000,-1000'):
    """10/11 checklist (lighthouse cove: pale flat patches with straight edges on the sand). The old Godot ground
    'Maré · Ground' (ISM tiles) lies flat at -21..-31 cm there, right at the sea level (-30), over the island terrain
    (-56..-68): the water shows and vanishes on it in straight-edged patches. 'list:x0,x1,y0,y1' reports the tiles in
    the region (top, bottom, size); 'apply:...' shrinks to epsilon (keeps the bounds, lesson of 27/10) every tile whose
    top is under -5 cm, i.e. at or under the waterline, where the island terrain and the sea floor already are."""
    mode, _, rest = arg.partition(':')
    x0, x1, y0, y1 = (float(v) for v in rest.split(','))
    out, hidden = [], 0
    for a in _actors('Maré · Ground'):
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            b = c.static_mesh.get_bounding_box()
            for i in range(c.get_instance_count()):
                t = c.get_instance_transform(i, True)
                l, s = t.translation, t.scale3d
                if s.z < .01:
                    continue
                lo = unreal.MathLibrary.transform_location(t, b.min)
                hi = unreal.MathLibrary.transform_location(t, b.max)
                bx0, bx1, by0, by1 = min(lo.x, hi.x), max(lo.x, hi.x), min(lo.y, hi.y), max(lo.y, hi.y)
                if bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1:
                    continue
                top, bottom = max(lo.z, hi.z), min(lo.z, hi.z)
                row = [i, round(l.x), round(l.y), round(top), round(bottom), round(bx1 - bx0), round(by1 - by0)]
                if mode == 'apply' and top < -5:
                    t.scale3d = unreal.Vector(.001, .001, .001)
                    c.update_instance_transform(i, t, True, True, True)
                    row.append('hidden')
                    hidden += 1
                out.append(row)
    if hidden:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'tiles': len(out), 'hidden': hidden, 'rows': out[:40]})


def slab_gap(arg='8600,10200,-4300,-3100,50'):
    """'x0,x1,y0,y1,step': under the big lighthouse slab, the air between its underside and the ground below (points where
    the slab covers the ground): x, y, ground z, slab underside z, gap (cm). Written to D:/CodexTemp/slab_gap.json."""
    x0, x1, y0, y1, step = (float(v) for v in arg.split(','))
    world = _world()
    slab = _actors('Maré · coast_rocks_02')
    rocks = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
             if 'rocha' in a.get_actor_label() or 'rock' in a.get_actor_label().lower() or a.get_actor_label() == 'Maré · farol']
    out = []
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            g = _ground_under(world, x, y, rocks)
            if g:
                up = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, g[0] - 2), unreal.Vector(x, y, g[0] + 400),
                                                            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [a for a in rocks if a not in slab],
                                                            unreal.DrawDebugTrace.NONE, False)
                t = up.to_tuple() if up else None
                if t and t[0] and t[9] in slab:
                    out.append([round(x), round(y), round(g[0]), round(t[4].z), round(t[4].z - g[0]), g[2][:20]])
            x += step
        y += step
    import pathlib
    pathlib.Path('D:/CodexTemp/slab_gap.json').write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
    gaps = [r[4] for r in out]
    return json.dumps({'points': len(out), 'gap>15': sum(1 for v in gaps if v > 15), 'max': max(gaps) if gaps else None,
                       'worst': sorted(out, key=lambda r: -r[4])[:15]}, ensure_ascii=False)


def coast_ground(arg=''):
    """10/11 (maré alta photos): rebuilds M_CoastGround_PBR, whose underwater plate now sinks under the island floor (see
    mare_materials.build_ground). PIE stopped."""
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    return mare_materials.build_ground().get_path_name()


def sea_water(arg=''):
    """10/11 ('erro na agua'): rebuilds M_CoastalWater_PBR with the lower shore swell (AMarePerson::SeaHeight matches).
    PIE stopped."""
    import importlib
    import mare_materials
    importlib.reload(mare_materials)
    return mare_materials.build_water().get_path_name()
