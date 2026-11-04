"""Short wordless voices (murmurs) for the people of the island (PENDENCIAS P2 "vozes curtas sem diálogo falado").

    python tools/ue58/fetch_murmurs.py

Sources (CC0 on OpenGameArt, "credit appreciated, not required"; listed in CREDITS.md):
  cicifyre "Free Voice Clips Pack - Mature Female" and "- Bright Female": laughs, a sigh, an annoyed grumble, "ah/eh/uh";
  Happii Gamer Studio "Shop Owner Voice": a male "hmm".
Only non-word sounds are kept (no spoken lines). The male versions of the female clips are made here with the WORLD
vocoder (pyworld): pitch x0.58 and the spectral envelope warped by 0.84 (shorter vocal tract), so a laugh or a
grumble keeps its timing and breath but sounds like a man. Everything is quiet and soft (the game's gentle audio
rule): 120 Hz high-pass, a short fade in/out and a peak of -9 dBFS.

Downloads go to D:/CodexTemp/voices_dl (untrusted data: only unzipped in memory and decoded as audio).
Output: unreal/MareAlta/SourceArt/Audio/Voices/<mood>_<f|m>_<n>.wav (48 kHz mono 16-bit) + manifest.json.
Moods: happy (served, a deal closed), annoyed (a counter-offer, leaving the desk), hmm (thinking, reading the menu).
"""
import io
import json
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pyworld
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfiltfilt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'unreal/MareAlta/SourceArt/Audio/Voices'
DL = Path('D:/CodexTemp/voices_dl')
RATE = 48000
UA = 'Mozilla/5.0 (MareAltaResort asset fetch)'
PACKS = {
    'mature': 'Free%20Voice%20Clips%20Pack%20-%20Mature%20Female.zip',
    'bright': 'Free%20Voice%20Clips%20Pack%20-%20Bright%20Female_0.zip',
    'shop': 'shop_owner_rpg.zip',
}
# mood -> [(pack, clip name without extension, voice)]: 'f' = keep, 'fm' = female and a male conversion, 'm' = male.
PICKS = {
    'happy': [('mature', 'small_single_laugh', 'fm'), ('mature', 'laugh', 'fm'), ('bright', '01-laughter', 'f'), ('bright', '02-laughter', 'f')],
    'annoyed': [('mature', 'annoyed_grumble', 'fm'), ('mature', 'sigh1', 'fm'), ('mature', 'sigh2', 'f')],
    'hmm': [('mature', 'anime_uh', 'fm'), ('mature', 'anime_eh', 'f'), ('shop', 'hmm', 'm')],
}


def pack(name):
    path = DL / PACKS[name].replace('%20', '_')
    if not path.exists():
        DL.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request('https://opengameart.org/sites/default/files/' + PACKS[name], headers={'User-Agent': UA})
        path.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    return zipfile.ZipFile(path)


def clip(zf, base):
    member = next(n for n in zf.namelist() if n.split('/')[-1].rsplit('.', 1)[0] == base)
    data, rate = sf.read(io.BytesIO(zf.read(member)), always_2d=True)
    mono = data.mean(axis=1)
    if rate != RATE:
        mono = resample_poly(mono, RATE, rate)
    return mono.astype(np.float64)


def to_male(x):
    """WORLD analysis/resynthesis: lower pitch and a longer vocal tract (envelope stretched towards low frequencies)."""
    f0, t = pyworld.harvest(x, RATE, f0_floor=60.0, f0_ceil=900.0)
    sp = pyworld.cheaptrick(x, f0, t, RATE)
    ap = pyworld.d4c(x, f0, t, RATE)
    bins = sp.shape[1]
    src = np.clip(np.arange(bins) / .84, 0, bins - 1)   # output bin k takes the envelope at k/0.84: formants x0.84
    warped = np.stack([np.interp(src, np.arange(bins), row) for row in sp])
    apw = np.stack([np.interp(src, np.arange(bins), row) for row in ap])
    return pyworld.synthesize(f0 * .58, warped, apw, RATE)


def soften(x):
    x = sosfiltfilt(butter(2, 120, 'highpass', fs=RATE, output='sos'), x)
    nz = np.flatnonzero(np.abs(x) > np.abs(x).max() * .02)
    x = x[max(0, nz[0] - 480):nz[-1] + 2400] if len(nz) else x
    fade = min(len(x) // 4, int(.03 * RATE))
    ramp = np.linspace(0, 1, fade)
    x[:fade] *= ramp
    x[-fade:] *= ramp[::-1]
    return x / (np.abs(x).max() + 1e-9) * 10 ** (-9 / 20)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for mood, rows in PICKS.items():
        count = {'f': 0, 'm': 0}
        for name, base, voices in rows:
            x = clip(pack(name), base)
            outs = []
            if 'f' in voices and name != 'shop':
                outs.append(('f', x))
            if voices == 'fm':
                outs.append(('m', to_male(x)))
            if voices == 'm':
                outs.append(('m', x))
            for sex, y in outs:
                count[sex] += 1
                key = f'{mood}_{sex}_{count[sex]}'
                y = soften(y)
                sf.write(OUT / f'{key}.wav', (y * 32767).astype(np.int16), RATE, subtype='PCM_16')
                manifest[key] = {'source': f'{name}:{base}', 'converted': sex == 'm' and voices == 'fm', 'seconds': round(len(y) / RATE, 2)}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=1))


if __name__ == '__main__':
    main()
