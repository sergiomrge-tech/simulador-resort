"""Intro checks for the QA gate (06/11/2026, CHECKLIST 0 A4).

driver(arg) - what the bus driver wears during the arrival: {'driver': bool, 'meshes': [...], 'swim': bool}. With no role he
              took the beach roster and drove the bus in a bikini; he is a seated villager now (MareIntro.cpp).
"""
import json
import unreal


def driver(arg=''):
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return json.dumps({'driver': False, 'pie': False})
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if a.get_class().get_name() != 'MarePerson' or not a.get_attach_parent_actor():
            continue
        names = []
        actors = [a] + list(a.get_attached_actors() or [])
        for actor in actors:
            for c in actor.get_components_by_class(unreal.SkeletalMeshComponent):
                m = c.get_skeletal_mesh_asset()
                if m and c.is_visible():
                    names.append(m.get_name())
        swim = any(k in n.lower() for n in names for k in ('swim', 'bikini', 'trunks', 'boardshorts'))
        return json.dumps({'driver': True, 'meshes': names, 'swim': swim})
    return json.dumps({'driver': False, 'pie': True})
