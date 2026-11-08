"""Audio probe (08/11, Sergio: "a música de fundo" did not turn off with the Music slider at 0 in the demo): sets a bus
volume on the PIE world's UMareAudioWorld and lists every playing sound with its volume (au.DumpActiveSounds goes to
the log). Entry: mare_hud module "mare_audio_probe.run|Music=0"."""
import json
import unreal


def _pie_world():
    for w in unreal.EditorLevelLibrary.get_pie_worlds(False) if hasattr(unreal.EditorLevelLibrary, 'get_pie_worlds') else []:
        return w
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()


def run(arg=''):
    world = _pie_world()
    if not world:
        return 'no PIE world'
    audio = None
    for obj in unreal.ObjectIterator(unreal.MareAudioWorld):
        if 'UEDPIE' in obj.get_path_name():
            audio = obj
    if audio is None:
        return 'no audio subsystem'
    out = {}
    for pair in [p for p in arg.split(',') if '=' in p]:
        bus, value = pair.split('=')
        audio.set_volume(bus.strip(), float(value))
    for bus in ['Master', 'Music', 'Effects', 'Ambient']:
        out[bus] = round(audio.get_volume(bus), 3)
    out['station'] = str(audio.get_radio_station())
    playing = []
    for comp in unreal.ObjectIterator(unreal.AudioComponent):
        if 'UEDPIE' not in comp.get_path_name() or not comp.is_playing():
            continue
        vol = comp.get_editor_property('volume_multiplier')
        if vol > 0.0005:
            playing.append([comp.sound.get_name() if comp.sound else '?', round(vol, 4)])
    out['playing'] = sorted(playing, key=lambda r: -r[1])
    return json.dumps(out)
