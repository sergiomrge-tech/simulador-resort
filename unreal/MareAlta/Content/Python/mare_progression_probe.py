"""Drive the village chapter and day close in a QA PIE profile; never touches player saves."""
import json
import unreal


def _world():
    if '-MareSaveRoot=D:/CodexTemp/' not in unreal.SystemLibrary.get_command_line():
        raise RuntimeError('QA profile required')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:
        raise RuntimeError('Start PIE first')
    return world


def _target(world, action, owner_name=None):
    for t in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.MareServiceTarget):
        if str(t.action) != action:
            continue
        if owner_name is None or (t.get_owner() and t.get_owner().get_editor_property('person_name') == owner_name):
            return t
    raise RuntimeError('Target not found: ' + action + ' ' + str(owner_name))


def _face(world, hero, pc, location, offset):
    hero.set_actor_location(location + offset, False, True)
    # The camera component only updates on the next tick; use its fixed eye offset.
    eye = hero.get_actor_location() + unreal.Vector(0, 0, 74)
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, location))


def run(action, arg=''):
    arg, _, arg2 = arg.partition('|')
    world = _world()
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    hero = unreal.GameplayStatics.get_player_pawn(world, 0)
    sim = pc.get_simulation()
    result = {'action': action}
    if action == 'talk':
        resident = _target(world, 'Resident', arg)
        person = resident.get_owner()
        _face(world, hero, pc, resident.get_actor_location(), unreal.Vector(float(arg2 or 200), 0, 0))
        focused = unreal.MareServiceTarget.find_focused(pc)
        result['focused'] = focused == resident
        if focused == resident:
            focused.use(pc)
        result['person'] = person.get_editor_property('person_name')
    elif action == 'use':
        # Separate call: the player camera manager must tick after positioning.
        focused = unreal.MareServiceTarget.find_focused(pc)
        result['focused'] = str(focused.label) if focused else None
        if focused:
            focused.use(pc)
    elif action == 'face':
        # "Action|dx,dy,dz": stand at the target plus an offset, looking at it (any MareServiceTarget action).
        target = _target(world, arg)
        dx, dy, dz = (float(v) for v in (arg2 or '200,0,0').split(','))
        _face(world, hero, pc, target.get_actor_location(), unreal.Vector(dx, dy, dz))
        result['target'] = [target.get_actor_location().x, target.get_actor_location().y, target.get_actor_location().z]
    elif action == 'buy':
        result['ok'] = sim.buy_supply('peixe', int(arg or 4))
    elif action == 'advance':
        result['ok'] = sim.advance_chapter(arg or 'pier')
    elif action == 'close':
        pc.toggle_pause_menu()
    elif action == 'bed':
        bed = _target(world, 'Bed')
        _face(world, hero, pc, bed.get_actor_location(), unreal.Vector(0, 160, 40))
        focused = unreal.MareServiceTarget.find_focused(pc)
        result['focused'] = focused == bed
        if focused == bed:
            focused.use(pc)
    elif action == 'capture':
        path = 'D:/CodexTemp/claude-qa-20261101/shots/' + arg + '.png'
        unreal.SystemLibrary.execute_console_command(world, 'HighResShot 1280x720 filename=' + path)
        result['capture'] = path
    elif action == 'capture-ui':
        # Includes Slate viewport widgets (dialogue, phone); saved under Saved/Screenshots.
        unreal.SystemLibrary.execute_console_command(world, 'Shot showui')
    elif action != 'state':
        raise ValueError(action)
    result.update({'money': sim.money(), 'phone_open': pc.get_editor_property('phone_open'), 'move_ignored': pc.is_move_input_ignored(),
                   'hero': [round(v) for v in (hero.get_actor_location().x, hero.get_actor_location().y, hero.get_actor_location().z)]})
    return result
