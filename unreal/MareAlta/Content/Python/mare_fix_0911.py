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
