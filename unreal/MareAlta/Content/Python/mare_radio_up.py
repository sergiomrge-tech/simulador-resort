"""Livelier radio (07/11, Sergio: "as músicas precisam ser mais animadas, procure na web músicas grátis"): CC0 tracks
from OpenGameArt (tropical, reggae, bossa, ukulele, summer funk), loudness-matched to -18 LUFS like the Open Lo-Fi ones
(D:/Assets/Audio/radio/wav/radio_up_NN.wav, list with author/page in D:/Assets/Audio/radio_upbeat/tracks.json), imported
as looping SoundWaves into /Game/Audio/Radio. audio.json and radio.json list them; credits in CREDITS.md.
Editor, PIE stopped: mare_hud module "mare_radio_up.run|"."""
import json
from pathlib import Path
import unreal

WAV = Path('D:/Assets/Audio/radio/wav')


def run(_=''):
    out = {}
    for source in sorted(WAV.glob('radio_up_*.wav')):
        path = '/Game/Audio/Radio/' + source.stem
        task = unreal.AssetImportTask()
        task.filename = str(source)
        task.destination_path = '/Game/Audio/Radio'
        task.destination_name = source.stem
        task.automated = True
        task.save = True
        task.replace_existing = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        wave = unreal.load_asset(path)
        if not isinstance(wave, unreal.SoundWave):
            raise RuntimeError('Radio import failed: ' + source.stem)
        wave.set_editor_property('looping', True)
        wave.set_editor_property('virtualization_mode', unreal.VirtualizationMode.PLAY_WHEN_SILENT)
        unreal.EditorAssetLibrary.save_loaded_asset(wave, False)
        out[source.stem] = round(wave.get_editor_property('duration'), 1)
    return json.dumps(out)
