"""Radio tracks (tools/ue58/radio_tracks.json, downloaded by fetch_radio.py into D:/Assets/Audio/radio): decode the MP3s,
normalise each to the same integrated loudness (LUFS, like measure_mix.py: equal by loudness, not by peak) and write
16-bit WAVs to D:/Assets/Audio/radio/wav/<id>.wav for the UE import (mare_hud / claude import: /Game/Audio/Radio).
Prints the audio.json rows. Usage: python tools/ue58/radio_prepare.py [target_lufs=-18]"""
import json
import sys
from pathlib import Path

import numpy as np
import pyloudnorm
import soundfile

ROOT = Path(__file__).resolve().parents[2]
SRC = Path('D:/Assets/Audio/radio')
OUT = SRC / 'wav'
TARGET = float(sys.argv[1]) if len(sys.argv) > 1 else -18.0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads((ROOT / 'tools/ue58/radio_tracks.json').read_text(encoding='utf-8'))
    tracks = data.get('tracks', data)
    rows = []
    for t in tracks:
        audio, rate = soundfile.read(str(SRC / t['filename']), always_2d=True)
        meter = pyloudnorm.Meter(rate)
        level = meter.integrated_loudness(audio)
        out = pyloudnorm.normalize.loudness(audio, level, TARGET)
        peak = float(np.max(np.abs(out)))
        if peak > 0.98:
            out = out * (0.98 / peak)
        soundfile.write(str(OUT / f"{t['id']}.wav"), out, rate, subtype='PCM_16')
        rows.append({'id': t['id'], 'path': f"/Game/Audio/Radio/{t['id']}.{t['id']}", 'duration': round(len(out) / rate),
                     'loop': True, 'group': 'radio', 'name': f"{t['title']} · {t['author'].split(' (')[0]}", 'lufs_in': round(level, 1)})
    print(json.dumps(rows, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
