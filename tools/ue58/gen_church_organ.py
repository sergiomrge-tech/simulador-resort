"""Church organ for the mass (11/11, open item "som da igreja: eco, órgão"). Original, synthesised here (no samples):
a slow hymn in C major on a pipe organ (additive: principal 8', octave 4', a soft fifth and a 16' pedal), four voices
moving by step, each note with a slow speech and release, under the long echo of a stone nave (Schroeder reverb:
four combs and two all-passes, ~3.5 s). 48 s, seamless loop (the tail of the echo wraps onto the start).
  python tools/ue58/gen_church_organ.py  ->  unreal/MareAlta/SourceArt/Audio/church_organ.wav (mono, 44.1 kHz)
Loudness is set by RMS (-23 dBFS) like the other music tracks; the game plays it spatialised from the altar."""
import wave
from pathlib import Path
import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Audio/church_organ.wav'
BEAT = 1.5                      # seconds per chord
# soprano, alto, tenor, bass (MIDI), one chord per beat: I IV I V | vi IV V I | I vi ii V | IV I V I  (twice, the
# second time with the melody a third higher where it fits)
HYMN = [(72, 67, 64, 48), (72, 69, 65, 53), (72, 67, 64, 52), (71, 67, 62, 55),
        (72, 69, 64, 57), (69, 65, 60, 53), (71, 67, 62, 55), (72, 67, 64, 48),
        (76, 72, 67, 48), (76, 72, 69, 57), (74, 69, 65, 50), (74, 71, 67, 55),
        (77, 72, 69, 53), (76, 72, 67, 55), (74, 71, 67, 43), (72, 67, 64, 48)]
HYMN = HYMN + [(s, a, t, b) for s, a, t, b in HYMN[:8]] + [(79, 72, 67, 48), (77, 72, 69, 53), (76, 72, 67, 55), (74, 71, 65, 55),
                                                             (72, 69, 65, 53), (72, 67, 64, 55), (71, 67, 62, 43), (72, 67, 64, 36)]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pipe(freq, dur, pedal=False):
    n = int(dur * SR)
    t = np.arange(n) / SR
    stops = ((.5, .9), (1, .25)) if pedal else ((1, 1.0), (2, .5), (3, .16), (4, .22), (6, .06), (8, .05))
    x = np.zeros(n)
    for mult, gain in stops:
        f = freq * mult
        if f < SR * .45:
            x += gain * np.sin(2 * np.pi * f * t + mult)
    x *= 1 + .004 * np.sin(2 * np.pi * 5.1 * t)                      # the wind is never perfectly steady
    att, rel = int(.09 * SR), int(.16 * SR)
    env = np.ones(n)
    env[:att] = np.linspace(0, 1, att) ** 1.5
    env[-rel:] = np.linspace(1, 0, rel)
    return x * env


def reverb(x):
    out = np.zeros(len(x))
    for delay, fb in ((.0437, .86), (.0511, .85), (.0617, .84), (.0733, .83)):
        d = int(delay * SR)
        y = x.copy()
        for i in range(d, len(y), d):                               # block feedback: fast enough in numpy
            seg = min(d, len(y) - i)
            y[i:i + seg] += fb * y[i - d:i - d + seg]
        out += y
    out /= 4
    for delay, g in ((.0051, .7), (.0017, .7)):
        d = int(delay * SR)
        y = np.zeros(len(out))
        buf = np.zeros(len(out) + d)
        for i in range(0, len(out), d):
            seg = min(d, len(out) - i)
            vin = out[i:i + seg] + g * buf[i:i + seg]
            buf[i + d:i + d + seg] = vin
            y[i:i + seg] = -g * vin + buf[i:i + seg]
        out = y
    return out


def main():
    total = len(HYMN) * BEAT
    tail = 4.0
    n = int((total + tail) * SR)
    dry = np.zeros(n)
    for voice in range(4):
        k = 0
        while k < len(HYMN):                                         # repeated notes are held (a real organist ties them)
            j = k
            while j + 1 < len(HYMN) and HYMN[j + 1][voice] == HYMN[k][voice]:
                j += 1
            note = pipe(hz(HYMN[k][voice]), (j - k + 1) * BEAT + .08, pedal=voice == 3)
            a = int(k * BEAT * SR)
            dry[a:a + len(note)] += note * (.9, .6, .6, 1.0)[voice]
            k = j + 1
    wet = reverb(dry)
    mix = .45 * dry + .75 * wet
    loop = mix[:int(total * SR)].copy()
    t = mix[int(total * SR):]
    loop[:len(t)] += t                                               # the echo of the last chord rings over the first
    loop -= loop.mean()
    rms = np.sqrt((loop ** 2).mean())
    loop *= 10 ** (-23 / 20) / rms
    peak = np.abs(loop).max()
    if peak > .95:
        loop *= .95 / peak
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((loop * 32767).astype(np.int16).tobytes())
    print('ok', round(total, 1), 's rms dBFS', round(20 * np.log10(np.sqrt((loop ** 2).mean())), 1), 'peak', round(float(np.abs(loop).max()), 3))


if __name__ == '__main__':
    main()
