"""Title QA (08/11): texture sizes as the game sees them and the geometry of the title widgets."""
import json
import unreal


def run(_=''):
    out = {}
    for name in ['T_TitleArt', 'T_TitleLogo']:
        t = unreal.load_asset('/Game/UI/Title/' + name)
        out[name] = {'size': [t.blueprint_get_size_x(), t.blueprint_get_size_y()],
                     'pow2': str(t.get_editor_property('power_of_two_mode')),
                     'max': t.get_editor_property('max_texture_size')}
    vp = unreal.WidgetLayoutLibrary.get_viewport_size(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world())
    scale = unreal.WidgetLayoutLibrary.get_viewport_scale(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world())
    out['viewport'] = [vp.x, vp.y, scale]
    return json.dumps(out, default=str)
