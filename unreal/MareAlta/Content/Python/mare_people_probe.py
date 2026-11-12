"""PIE probe of people (07/11, Sergio: "clientes travados"): every AMarePerson with name, stage, kiosk counter/table,
position and speed, so stuck walkers (wanting to move, speed 0) show up. mare_hud module "mare_people_probe.people|<radius cm around the kiosk or 0>"."""
import json
import unreal

KIOSK = unreal.Vector(3800, -1200, 0)


def people(arg=''):
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:
        return 'no PIE'
    radius = float(arg or 0)
    out = []
    for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MarePerson):
        loc = p.get_actor_location()
        if radius and (unreal.Vector(loc.x, loc.y, 0) - KIOSK).length() > radius:
            continue
        move = p.get_component_by_class(unreal.CharacterMovementComponent)
        out.append({'n': str(p.get_editor_property('person_name')), 'id': str(p.get_editor_property('save_id')),
                    'stage': str(p.get_editor_property('stage')).split('.')[-1].split(':')[0],
                    'c': p.get_editor_property('counter_index'), 't': p.get_editor_property('table_index'),
                    'emp': p.get_editor_property('employee'), 'amb': p.get_editor_property('ambient'),
                    'at': [round(loc.x), round(loc.y), round(loc.z)], 'v': round(p.get_velocity().length()),
                    'mode': str(move.movement_mode).split('.')[-1].split(':')[0] if move else ''})
    return json.dumps(out, ensure_ascii=False)
