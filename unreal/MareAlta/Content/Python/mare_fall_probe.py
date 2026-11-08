"""QA: drop the hero under the beach and read where he is (07/11, void_recovery). mare_hud module "mare_fall_probe.drop|" then ".where|"."""
import json
import unreal


def _hero():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    return unreal.GameplayStatics.get_player_pawn(world, 0)


def drop(_=''):
    h = _hero()
    move = h.get_component_by_class(unreal.CharacterMovementComponent)
    move.set_movement_mode(unreal.MovementMode.MOVE_WALKING)
    h.set_actor_location(unreal.Vector(3800, -2900, -6000), False, True)
    return 'dropped'


def where(_=''):
    h = _hero()
    l = h.get_actor_location()
    move = h.get_component_by_class(unreal.CharacterMovementComponent)
    return json.dumps({'at': [round(l.x), round(l.y), round(l.z)], 'mode': str(move.movement_mode)})
