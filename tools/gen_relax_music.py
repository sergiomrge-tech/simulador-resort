"""Trilha original tranquila, sem vozes/samples, em loop estéreo de 64 BPM."""
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
SR = 32000
BEAT = 60 / 64
LENGTH = 8 * 4 * BEAT
N = round(LENGTH * SR)


def note(midi, duration, pad=False):
    t = np.arange(round(duration * SR)) / SR
    f = 440 * 2 ** ((midi - 69) / 12)
    if pad:
        env = np.sin(np.pi * t / duration) ** 2
        tone = np.sin(2 * np.pi * f * t) + 0.12 * np.sin(2 * np.pi * f * 2 * t)
    else:
        env = (1 - np.exp(-t / 0.045)) * np.exp(-t / 1.6)
        env *= np.clip((duration - t) / 0.6, 0, 1)
        tone = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 2)
    return tone * env


def generate():
    mix = np.zeros((N, 2), dtype=np.float64)

    def put(signal, at, gain, pan=0):
        indices = (round(at * SR) + np.arange(len(signal))) % N
        np.add.at(mix[:, 0], indices, signal * gain * np.sqrt((1 - pan) / 2))
        np.add.at(mix[:, 1], indices, signal * gain * np.sqrt((1 + pan) / 2))

    # Cmaj9, Am9, Fmaj9, G6: acordes abertos, sem bateria ou agudos incisivos.
    chords = [(48, 55, 59, 62, 64), (45, 52, 55, 59, 60),
              (41, 48, 52, 55, 57), (43, 50, 55, 57, 59)] * 2
    melody = [(76, 74), (71, 72), (69, 67), (71, 74),
              (76, 79), (76, 72), (69, 72), (71, 74)]
    for bar, chord in enumerate(chords):
        at = bar * 4 * BEAT
        for i, pitch in enumerate(chord):
            put(note(pitch + 12, 5 * BEAT, pad=True), at - 0.5 * BEAT, 0.024, (i - 2) * 0.25)
        for i, pitch in enumerate(chord[1:]):
            put(note(pitch + 12, 3.5 * BEAT), at + i * 0.20 * BEAT, 0.05, (i - 1.5) * 0.18)
        for i, pitch in enumerate(melody[bar]):
            put(note(pitch, 3 * BEAT), at + (1.5 + i * 1.5) * BEAT, 0.042, -0.15 if i else 0.15)
        put(note(chord[0], 4 * BEAT), at, 0.045)

    # Ecos circulares: a cauda do último compasso continua no primeiro sem corte.
    dry = mix.copy()
    for delay, gain in [(0.19, 0.13), (0.37, 0.09), (0.61, 0.05)]:
        mix += np.roll(dry[:, ::-1], round(delay * SR), axis=0) * gain
    frequencies = np.fft.rfftfreq(N, 1 / SR)
    lowpass = 1 / (1 + (frequencies / 2400) ** 6)
    mix = np.fft.irfft(np.fft.rfft(mix, axis=0) * lowpass[:, None], n=N, axis=0)
    mix *= 0.45 / max(1e-9, np.max(np.abs(mix)))
    path = ROOT / 'assets/audio/music_relax.ogg'
    with sf.SoundFile(path, 'w', samplerate=SR, channels=2, format='OGG', subtype='VORBIS') as stream:
        for start in range(0, N, 4096):
            stream.write(mix[start:start + 4096])
    print(f'{path.name}: {LENGTH:.1f}s, estéreo, pico={np.max(np.abs(mix)):.3f}, RMS={np.sqrt(np.mean(mix ** 2)):.3f}')


if __name__ == '__main__':
    generate()
