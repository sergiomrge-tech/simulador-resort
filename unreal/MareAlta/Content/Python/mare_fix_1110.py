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
