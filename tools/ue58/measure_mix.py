"""Loudness audit of the game mix (PENDENCIAS P1 "mixagem final"): each sound's loudness as the player hears it.

  python tools/ue58/measure_mix.py            -> table by category + outliers, D:/CodexTemp/mix_audit.json

Level heard = file loudness (integrated LUFS, ITU-R BS.1770 via pyloudnorm; short clips < 0.4 s use their RMS in dBFS)
+ 20 log10(gain): the gain in the code or the catalogue (Content/Data/audio.json group volume, PlayCue gains, the loop
targets of UMareAudioWorld) times the default bus volumes (UMareAudioWorld::DefaultVolume: master .85, music .3,
effects .75, ambient .7 on top of effects). Within a category the sounds should sit within a few dB of each other.
"""
import json
import math
from pathlib import Path

import numpy as np
import pyloudnorm
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
AUDIO = ROOT / 'unreal/MareAlta/SourceArt/Audio'
MASTER, MUSIC, EFFECTS, AMBIENT = .85, .3, .75, .7

# Gains set in the code (MareAudioWorld/MareGame/... PlayCue and the loop targets, daytime outdoors).
CUES = {'swim_splash': .22, 'swim_stroke': .18, 'kiosk_pickup': .6, 'kiosk_cash': .8, 'glass': .15, 'swoosh': .14,
        'thunder': .25, 'bell': .2, 'click': .3, 'clean': .3, 'bus_engine': .2, 'bus_brake': .17, 'kiosk_fridge': .3,
        'door': .3, 'whale_splash': .3}
LOOPS = {'ocean_loop': .4, 'rain_loop': .08, 'wind_loop': .055, 'crickets_loop': .22, 'leaves_soft': .2, 'underwater_loop': .28}
RADIO = .32
STATION_TRIM = {'reggae_praia': 1.5}
STEP = .18
STEP_TRIM = {'concrete': 2.0, 'wood': 1.25}
ONESHOT = {'bird1': .035, 'bird2': .035, 'seagull1': .3, 'seagull2': .75}


def loudness(path):
    data, rate = sf.read(path, always_2d=True)
    if len(data) < .4 * rate:
        rms = math.sqrt(float(np.mean(data ** 2)) + 1e-12)
        return 20 * math.log10(rms), True
    meter = pyloudnorm.Meter(rate)
    return float(meter.integrated_loudness(data)), False


def main():
    catalog = json.loads((ROOT / 'unreal/MareAlta/Content/Data/audio.json').read_text(encoding='utf-8-sig'))
    stations = [r['id'] for r in catalog if r['id'].startswith(('radio_', 'music_', 'reggae_'))]
    rows = []
    for r in catalog:
        name = r['id']
        files = list(AUDIO.rglob(f'{name}.wav'))
        if not files:
            continue
        lufs, short = loudness(files[0])
        if r.get('group'):
            group = r['group']
            cat = 'voices' if group.startswith('voice_') else 'actions'
            gain = r['volume'] * MASTER * EFFECTS
        elif name in stations:
            cat, gain = 'music', RADIO * STATION_TRIM.get(name, 1.0) * MASTER * MUSIC
        elif name in LOOPS:
            cat, gain = 'ambient', LOOPS[name] * MASTER * EFFECTS * AMBIENT
        elif name.startswith('footstep'):
            cat, gain = 'footsteps', STEP * STEP_TRIM.get(name.split('_')[1], 1.0) * MASTER * EFFECTS
        elif name in CUES:
            cat, gain = 'cues', CUES[name] * MASTER * EFFECTS
        elif name in ONESHOT:
            cat, gain = 'ambient_oneshot', ONESHOT[name] * MASTER * EFFECTS * AMBIENT
        else:
            continue
        heard = lufs + 20 * math.log10(max(gain, 1e-6))
        rows.append({'id': name, 'group': r.get('group', ''), 'cat': cat, 'file_lufs': round(lufs, 1), 'short': short,
                     'gain': round(gain, 3), 'heard': round(heard, 1)})
    by = {}
    for row in rows:
        by.setdefault(row['cat'], []).append(row)
    for cat, items in sorted(by.items()):
        values = [i['heard'] for i in items]
        med = float(np.median(values))
        print(f'== {cat}: {len(items)} sounds, median {med:.1f}, range {min(values):.1f}..{max(values):.1f}')
        for i in sorted(items, key=lambda x: x['heard']):
            flag = '  <-- ' + ('alto' if i['heard'] > med + 6 else 'baixo') if abs(i['heard'] - med) > 6 else ''
            print(f"   {i['heard']:6.1f}  file {i['file_lufs']:6.1f}{'*' if i['short'] else ' '} gain {i['gain']:.3f}  {i['id']}{flag}")
    Path('D:/CodexTemp/mix_audit.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
