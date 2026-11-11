"""Level fixes of 10/11/2026 (demo simulation and Sergio's photos).

bar_front(arg): the Grand Hotel pool terrace has three parasol sets (canopy, pole, two loungers, towels, flip-flops) at
x -3200, -2600 and -2000; the middle one stood right in front of the pool bar's counter: the canopy over the heads of
the guests talking to the barman, the lounger backs against their legs. The middle set goes. arg 'dry' lists, 'apply'
removes and saves the level (PIE stopped)."""
import json
import unreal

BOX = (-2840, -2360, 4220, 4470, 100, 340)   # x0, x1, y0, y1, z0, z1 around the middle set
MESHES = ('World_0115', 'World_0101', 'World_0097', 'World_0087', 'World_0448', 'World_0094', 'World_0089')


def _inside(v):
    return BOX[0] <= v.x <= BOX[1] and BOX[2] <= v.y <= BOX[3] and BOX[4] <= v.z <= BOX[5]


def bar_front(arg='dry'):
    apply = arg.strip() == 'apply'
    sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if sub.get_game_world():
        raise RuntimeError('Stop PIE first')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    removed, kill = [], []
    for a in actors.get_all_level_actors():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.get_editor_property('static_mesh')
            if not m or m.get_name() not in MESHES:
                continue
            bb = m.get_bounding_box()
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                idx = [i for i in range(c.get_instance_count()) if _inside(c.get_instance_transform(i, True).transform_location((bb.min + bb.max) * .5))]
                for i in idx:
                    t = c.get_instance_transform(i, True).translation
                    removed.append([m.get_name(), a.get_actor_label(), round(t.x), round(t.y), round(t.z), 'instance'])
                if apply:
                    for i in sorted(idx, reverse=True):
                        c.remove_instance(i)
            elif _inside(c.get_world_transform().transform_location((bb.min + bb.max) * .5)):
                t = a.get_actor_location()
                removed.append([m.get_name(), a.get_actor_label(), round(t.x), round(t.y), round(t.z), 'actor'])
                kill.append(a)
    if apply:
        for a in kill:
            actors.destroy_actor(a)
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'applied': apply, 'count': len(removed), 'removed': removed}, ensure_ascii=False)


TRUCK_TAG = 'Region_Biz_food_truck'


def truck_probe(arg=''):
    """What the food truck region holds: actors (label, class, mesh, bounds) and the text signs."""
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rows = []
    for a in actors.get_all_level_actors():
        tags = [str(t) for t in a.tags]
        text = None
        if isinstance(a, unreal.TextRenderActor):
            text = str(a.text_render.get_editor_property('text'))
        if TRUCK_TAG not in tags and not (text and 'pastel' in text.lower()):
            continue
        o, e = a.get_actor_bounds(False)
        meshes = []
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.get_editor_property('static_mesh')
            n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
            meshes.append('%s x%d' % (m.get_name() if m else None, n))
        t = a.get_actor_transform()
        rows.append({'label': a.get_actor_label(), 'class': a.get_class().get_name(), 'tags': tags, 'text': text, 'meshes': meshes,
                     'loc': [round(t.translation.x), round(t.translation.y), round(t.translation.z)], 'yaw': round(t.rotation.rotator().yaw),
                     'centre': [round(o.x), round(o.y), round(o.z)], 'half': [round(e.x), round(e.y), round(e.z)]})
    return json.dumps(rows, ensure_ascii=False)


STALL_AT = (2620.0, 3101.0, 5.0)   # the truck's place: its serving side was y 3183; the stall's +Y counter front is y 3215
STALL_LABEL = 'Vila · barraca do pastel'


def _asset(slug):
    table = json.load(open(unreal.Paths.project_content_dir() + 'Data/custom_assets.json', encoding='utf-8'))
    return unreal.load_asset(table[slug])


def _spawn(mesh, label, bottom_centre, yaw=0.0, scale=1.0, collide=False):
    """A static mesh actor placed by the bottom centre of its bounds (the pivot of a downloaded model is anywhere)."""
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    bb = mesh.get_bounding_box()
    local = unreal.Vector((bb.min.x + bb.max.x) * .5, (bb.min.y + bb.max.y) * .5, bb.min.z) * scale
    offset = unreal.Rotator(roll=0, pitch=0, yaw=yaw).rotate_vector(local) if hasattr(unreal.Rotator, 'rotate_vector') else unreal.MathLibrary.greater_greater_vector_rotator(local, unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    a.set_actor_location(unreal.Vector(bottom_centre[0] - offset.x, bottom_centre[1] - offset.y, bottom_centre[2] - offset.z), False, False)
    a.set_actor_label(label)
    a.tags = [unreal.Name('MareGenerated'), unreal.Name(TRUCK_TAG)]
    a.set_folder_path('Village/PastelStall')
    c.set_mobility(unreal.ComponentMobility.STATIC)
    if not collide:
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return a


def pastel_stall(arg='apply'):
    """10/11 (Sergio: "excluir esse food truck"; chosen: the pastel business becomes a street stall). The red truck
    (World_2362) and its rear leave; `mare_stall_pastel` (tools/ue58/gen_landmarks.py) stands in its place with the
    counter on the same side as the truck's window (business_games.json counter/guest spots unchanged), the frying pan
    on its burner, a jug and a cutting board on the counter and the gas bottle beside it (Poly Haven, CC0). The two
    'Food truck do Pastel' signs become 'Barraca do Pastel' on the stall's sign boards. Region tag kept: everything
    shows only when the business is owned. Re-runnable. PIE stopped; saves the level."""
    sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if sub.get_game_world():
        raise RuntimeError('Stop PIE first')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    gone = []
    for a in actors.get_all_level_actors():
        lab = a.get_actor_label()
        if lab in ('Maré · biz_food_truck', 'Vila · traseira do food truck') or lab.startswith(STALL_LABEL):
            gone.append(lab)
            actors.destroy_actor(a)
    x, y, z = STALL_AT
    made = []
    stall = _spawn(_asset('mare_stall_pastel'), STALL_LABEL, (x, y, z), 0.0, 1.0, True)
    made.append(stall.get_actor_label())
    for slug, name, local, yaw, scale in (
            ('brass_pan_01', 'tacho', (65, 0, 109.5), 90.0, 2.0),
            ('jug_01', 'jarra', (-88, 92, 108), 20.0, 1.0),
            ('wooden_cutting_board', 'tábua', (40, 94, 108), 0.0, 1.0),
            ('propane_tank', 'botijão', (182, -50, 0), 0.0, 1.0)):
        a = _spawn(_asset(slug), f'{STALL_LABEL} · {name}', (x + local[0], y + local[1], z + local[2]), yaw, scale)
        made.append(a.get_actor_label())
    signs = []
    k = 0
    for a in actors.get_all_level_actors():
        if isinstance(a, unreal.TextRenderActor) and TRUCK_TAG in [str(t) for t in a.tags]:
            side = 1 if k == 0 else -1
            a.text_render.set_editor_property('text', 'Barraca do Pastel')
            a.text_render.set_editor_property('horizontal_alignment', unreal.HorizTextAligment.EHTA_CENTER)
            a.text_render.set_editor_property('vertical_alignment', unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
            a.text_render.set_editor_property('world_size', 26.0)
            a.set_actor_location_and_rotation(unreal.Vector(x, y + side * 150.5, z + 298), unreal.Rotator(roll=0, pitch=0, yaw=90.0 * side), False, False)
            a.set_actor_label('Letreiro · Barraca do Pastel')
            signs.append([round(a.get_actor_location().y), a.get_actor_rotation().yaw])
            k += 1
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return json.dumps({'removed': gone, 'placed': made, 'signs': signs}, ensure_ascii=False)
