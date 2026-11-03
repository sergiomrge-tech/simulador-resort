"""Original instrumental beach radio (CC0, no voices, no third-party samples).

Three ~2-minute stations with verse/chorus/bridge sections so the radio does not feel like a
short loop: roots reggae (one drop, skank, organ bubble, melodica), Caribbean calypso (steel
pan, congas, shaker) and beach pop (plucked ukulele, cajon, soft lead), the Hawaiian
station Aloha FM (ukulele, lap steel slides, ipu) and the Mare Alta theme. Every sound is
synthesised here (Karplus-Strong strings, modal steel pan, noise/sine drums).

  python tools/ue58/gen_radio_music.py   -> unreal/MareAlta/SourceArt/Audio/radio_*.wav
"""
import json
import wave
from pathlib import Path

import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Audio'
NOTE = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def chord_notes(name, octave=4):
    """'Am', 'G', 'F7', 'Cmaj7' -> MIDI notes (root position, close voicing)."""
    root = name[:2] if len(name) > 1 and name[1] in '#b' else name[:1]
    rest = name[len(root):]
    base = 12 * (octave + 1) + NOTE[root]
    third = 3 if rest.startswith('m') and not rest.startswith('maj') else 4
    notes = [base, base + third, base + 7]
    if rest.endswith('maj7'):
        notes.append(base + 11)
    elif rest.endswith('7'):
        notes.append(base + 10)
    return notes, base


class Track:
    def __init__(self, bpm, bars, seed):
        self.beat = 60.0 / bpm
        self.length = int(SR * self.beat * 4 * bars)
        self.mix = np.zeros((self.length, 2))
        self.rng = np.random.default_rng(seed)

    def add(self, sig, start, gain=1.0, pan=0.0):
        at = int(start * SR)
        if at >= self.length:
            return
        n = min(len(sig), self.length - at)
        left, right = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
        self.mix[at:at + n, 0] += sig[:n] * gain * left
        self.mix[at:at + n, 1] += sig[:n] * gain * right

    # ---------------------------------------------------------------- instruments
    def pluck(self, midi, dur, bright=0.5, decay=0.996):
        """Karplus-Strong string (ukulele/guitar); identical notes are rendered once."""
        key = (midi, round(dur, 4), bright, decay)
        cache = self.__dict__.setdefault('_plucks', {})
        if key not in cache:
            cache[key] = self._pluck(midi, dur, bright, decay)
        return cache[key]

    def _pluck(self, midi, dur, bright, decay):
        f = hz(midi)
        period = max(2, int(SR / f))
        n = int(SR * dur)
        buf = self.rng.uniform(-1, 1, period)
        buf = np.convolve(buf, np.ones(3) / 3, mode='same') * (0.6 + bright * 0.4)
        out = np.empty(n)
        for i in range(n):
            j = i % period
            out[i] = buf[j]
            buf[j] = decay * 0.5 * (buf[j] + buf[(j + 1) % period])
        t = np.arange(n) / SR
        return out * np.clip((dur - t) * 30, 0, 1)

    def steel_pan(self, midi, dur):
        """Modal steel drum: fundamental, octave and slightly inharmonic overtones."""
        f, t = hz(midi), np.arange(int(SR * dur)) / SR
        partials = [(1.0, 1.0, 3.0), (2.0, .55, 4.5), (3.01, .25, 6.0), (4.02, .12, 8.0), (5.6, .05, 11.0)]
        sig = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * d) for k, a, d in partials)
        return sig * (1 - np.exp(-t * 400)) * np.clip((dur - t) * 20, 0, 1)

    def organ(self, midi, dur):
        f, t = hz(midi), np.arange(int(SR * dur)) / SR
        sig = np.sin(2 * np.pi * f * t) + .5 * np.sin(4 * np.pi * f * t) + .25 * np.sin(6 * np.pi * f * t)
        return sig * (1 - np.exp(-t * 60)) * np.exp(-t * 6) * np.clip((dur - t) * 40, 0, 1)

    def reed(self, midi, dur, vibrato=5.0):
        """Melodica/soft lead: odd-harmonic reed with gentle vibrato and breath."""
        t = np.arange(int(SR * dur)) / SR
        f = hz(midi) * (1 + .006 * np.sin(2 * np.pi * vibrato * t) * np.clip(t * 3, 0, 1))
        ph = 2 * np.pi * np.cumsum(f) / SR
        sig = np.sin(ph) + .33 * np.sin(3 * ph) + .14 * np.sin(5 * ph) + .02 * self.rng.normal(0, 1, len(t))
        env = (1 - np.exp(-t * 25)) * np.clip((dur - t) * 12, 0, 1)
        return sig * env

    def steel(self, midi, dur, slide_from=None, slide=0.14, vibrato=5.2):
        """Hawaiian lap steel: glides from the previous note, slow vibrato after the attack, warm partials."""
        t = np.arange(int(SR * dur)) / SR
        target = hz(midi)
        f = np.full(len(t), target)
        if slide_from is not None:
            start = hz(slide_from)
            k = np.clip(t / slide, 0, 1)
            f = start * (target / start) ** (k * k * (3 - 2 * k))
        f = f * (1 + .0045 * np.sin(2 * np.pi * vibrato * t) * np.clip((t - .22) * 2.5, 0, 1))
        ph = 2 * np.pi * np.cumsum(f) / SR
        sig = np.sin(ph) + .45 * np.sin(2 * ph) + .22 * np.sin(3 * ph) + .08 * np.sin(4 * ph) + .03 * np.sin(5 * ph)
        env = (1 - np.exp(-t * 180)) * np.exp(-t * .9) * np.clip((dur - t) * 14, 0, 1)
        return sig * env

    def ipu(self, low=True):
        """Hawaiian gourd drum: a soft low thump (palm) or a higher slap."""
        t = np.arange(int(SR * .5)) / SR
        f = 78 if low else 160
        body = np.sin(2 * np.pi * f * t * (1 + .25 * np.exp(-t * 30))) * np.exp(-t * (9 if low else 18))
        return body + .12 * self.rng.normal(0, 1, len(t)) * np.exp(-t * 80)

    def bass(self, midi, dur, tone=0.15):
        f, t = hz(midi), np.arange(int(SR * dur)) / SR
        sig = np.sin(2 * np.pi * f * t) + tone * np.sin(4 * np.pi * f * t)
        return sig * (1 - np.exp(-t * 120)) * np.exp(-t * 2.5) * np.clip((dur - t) * 25, 0, 1)

    def drum(self, kind):
        t = np.arange(int(SR * .45)) / SR
        noise = self.rng.normal(0, 1, len(t))
        if kind == 'kick':
            return np.sin(2 * np.pi * (50 * t + 9 * (1 - np.exp(-t * 28)))) * np.exp(-t * 14)
        if kind == 'rim':
            return (.5 * noise + .7 * np.sin(2 * np.pi * 1700 * t)) * np.exp(-t * 90)
        if kind == 'snare':
            return (.8 * noise + .4 * np.sin(2 * np.pi * 190 * t)) * np.exp(-t * 22)
        if kind == 'hat':
            return np.diff(noise, prepend=0) * .35 * np.exp(-t * 70)
        if kind == 'shaker':
            return np.diff(noise, prepend=0) * .25 * np.exp(-((t - .03) / .025) ** 2)
        if kind in ('conga_hi', 'conga_lo'):
            f = 330 if kind == 'conga_hi' else 220
            return (np.sin(2 * np.pi * f * t * (1 + .3 * np.exp(-t * 40))) + .2 * noise * np.exp(-t * 60)) * np.exp(-t * 16)
        if kind == 'cajon':
            return (np.sin(2 * np.pi * 95 * t) * np.exp(-t * 18) + .35 * noise * np.exp(-t * 35))
        raise ValueError(kind)

    # ---------------------------------------------------------------- finishing
    def master(self, room=0.18):
        """Short plate-like reverb, gentle bus compression and limiter with headroom."""
        ir_t = np.arange(int(SR * 1.3)) / SR
        ir = self.rng.normal(0, 1, (len(ir_t), 2)) * np.exp(-ir_t * 4.2)[:, None]
        ir[:int(SR * .012)] = 0
        size = 1 << int(np.ceil(np.log2(self.length + len(ir))))
        wet = np.stack([np.fft.irfft(np.fft.rfft(self.mix[:, c], size) * np.fft.rfft(ir[:, c], size), size)[:self.length] for c in range(2)], axis=1)
        wet *= room * np.abs(self.mix).max() / max(1e-9, np.abs(wet).max())
        out = self.mix + wet
        # Loop seam: fold the reverb tail of the end into the beginning so the radio loops cleanly.
        fade = int(SR * .02)
        out[:fade] *= np.linspace(0, 1, fade)[:, None]
        out[-fade:] *= np.linspace(1, 0, fade)[:, None]
        out = np.tanh(out / (np.abs(out).max() * 0.9) * 1.25)
        # Match the loudness of the existing stations (RMS ~0.09) so switching does not jump.
        out *= 0.09 / max(1e-9, float(np.sqrt(np.mean(out ** 2))))
        return out * min(1.0, 0.9 / np.abs(out).max())

    def section_bars(self, form):
        bar = 0
        for name, chords, count in form:
            for i in range(count):
                yield bar, name, chords[i % len(chords)]
                bar += 1


def write(path, data):
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(data, -1, 1) * 32767).astype('<i2').tobytes())


def reggae():
    form = [('intro', ['Am', 'G'], 4), ('verse', ['Am', 'Dm', 'G', 'Am'], 8), ('chorus', ['F', 'G', 'C', 'Am'], 8),
            ('verse', ['Am', 'Dm', 'G', 'Am'], 8), ('bridge', ['Dm', 'Em', 'F', 'G'], 4), ('chorus', ['F', 'G', 'C', 'Am'], 8), ('outro', ['Am', 'G'], 4)]
    bars = sum(c for _, _, c in form)
    tr = Track(76, bars, 20261101)
    b = tr.beat
    melody = {'verse': [(0, 76, 1.5), (1.5, 74, .5), (2, 72, 1), (3, 69, 1)], 'chorus': [(0, 72, 1), (1, 74, .5), (1.5, 76, 1.5), (3, 79, 1)],
              'bridge': [(0, 74, 2), (2, 72, 2)]}
    for bar, name, chord in tr.section_bars(form):
        notes, root = chord_notes(chord, 4)
        t0 = bar * 4 * b
        for i in range(4):
            # Skank on the off-beats, organ bubble on the "e" and "a".
            if name != 'intro' or bar >= 2:
                for n in notes[:3]:
                    tr.add(tr.pluck(n, .18, .8, .985), t0 + (i + .5) * b, .10, -.3)
            for n in notes[:3]:
                tr.add(tr.organ(n + 12, .14), t0 + (i + .25) * b, .025, .35)
                tr.add(tr.organ(n + 12, .14), t0 + (i + .75) * b, .02, .35)
            tr.add(tr.drum('hat'), t0 + i * b, .05, .3)
            tr.add(tr.drum('hat'), t0 + (i + .5) * b, .035, .3)
            tr.add(tr.drum('shaker'), t0 + (i + .75) * b, .03, -.4)
        # One drop: kick + rim on beat 3.
        if name != 'intro':
            tr.add(tr.drum('kick'), t0 + 2 * b, .45)
            tr.add(tr.drum('rim'), t0 + 2 * b, .16, -.1)
        line = [(0, 0, .75), (1, 0, .5), (1.5, 7, .5), (2.5, 12, .5), (3, 10 if 'm' in chord else 11, .5), (3.5, 7, .5)]
        for when, step, dur in line:
            tr.add(tr.bass(root - 24 + step, dur * b * 1.6), t0 + when * b, .34)
        if name in melody and bar % 2 == 0:
            for when, note, dur in melody[name]:
                shift = 0 if chord in ('Am', 'F', 'C') else (-2 if chord == 'G' else 0)
                tr.add(tr.reed(note + shift, dur * b), t0 + when * b, .10, .15)
    return tr.master(.16)


def calypso():
    form = [('intro', ['C', 'G7'], 4), ('verse', ['C', 'F', 'G7', 'C'], 8), ('chorus', ['F', 'C', 'G7', 'C'], 8),
            ('verse', ['C', 'F', 'G7', 'C'], 8), ('bridge', ['Am', 'Dm', 'G7', 'G7'], 4), ('chorus', ['F', 'C', 'G7', 'C'], 8), ('outro', ['C', 'G7'], 4)]
    bars = sum(c for _, _, c in form)
    tr = Track(112, bars, 20261102)
    b = tr.beat
    scale = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76]
    for bar, name, chord in tr.section_bars(form):
        notes, root = chord_notes(chord, 4)
        t0 = bar * 4 * b
        # Steel pan strum on the calypso pattern (1, 2&, 3, 4&) and a lead phrase.
        for when in (0, 1.5, 2, 3.5):
            for k, n in enumerate(notes[:3]):
                tr.add(tr.steel_pan(n, .5), t0 + when * b + k * .012, .08, -.2 + k * .2)
        if name in ('verse', 'chorus', 'bridge'):
            phrase = tr.rng.choice(len(scale) - 4, 1)[0]
            for k, when in enumerate((0, .5, 1, 2, 2.5, 3)):
                n = scale[(phrase + [0, 2, 4, 2, 1, 0][k]) % len(scale)] + 12
                tr.add(tr.steel_pan(n, .35), t0 + when * b, .12, .25)
        for i in range(8):
            tr.add(tr.drum('shaker'), t0 + i * b / 2, .045 if i % 2 else .03, .4)
        for when, kind in ((0, 'conga_lo'), (1.5, 'conga_hi'), (2, 'conga_lo'), (2.75, 'conga_hi'), (3.5, 'conga_hi')):
            tr.add(tr.drum(kind), t0 + when * b, .14, -.35)
        if name != 'intro':
            for when in (0, 2):
                tr.add(tr.drum('kick'), t0 + when * b, .35)
            tr.add(tr.drum('snare'), t0 + 3 * b, .09)
        for when, step in ((0, 0), (1.5, 7), (2, 12), (3, 7), (3.5, 4)):
            tr.add(tr.bass(root - 24 + step, .45 * b * 1.5, .25), t0 + when * b, .3)
    return tr.master(.2)


def beach_pop():
    form = [('intro', ['C', 'Am', 'F', 'G'], 4), ('verse', ['C', 'G', 'Am', 'F'], 8), ('chorus', ['F', 'G', 'C', 'Am'], 8),
            ('verse', ['C', 'G', 'Am', 'F'], 8), ('bridge', ['Dm', 'G', 'Em', 'Am'], 4), ('chorus', ['F', 'G', 'C', 'Am'], 8), ('outro', ['C', 'G', 'C', 'C'], 4)]
    bars = sum(c for _, _, c in form)
    tr = Track(96, bars, 20261103)
    b = tr.beat
    for bar, name, chord in tr.section_bars(form):
        notes, root = chord_notes(chord, 4)
        t0 = bar * 4 * b
        # Ukulele island strum: D, D-U, U-D-U.
        for when, up in ((0, 0), (1, 0), (1.5, 1), (2.5, 1), (3, 0), (3.5, 1)):
            order = notes[::-1] if up else notes
            for k, n in enumerate(order[:3] + [order[0] + 12]):
                tr.add(tr.pluck(n + 12, .5, .55, .994), t0 + when * b + k * .009, .055 if up else .075, -.25 + k * .15)
        tr.add(tr.drum('cajon'), t0, .28)
        tr.add(tr.drum('cajon'), t0 + 2.5 * b, .2)
        tr.add(tr.drum('rim'), t0 + b, .07, .2)
        tr.add(tr.drum('rim'), t0 + 3 * b, .07, .2)
        for i in range(8):
            tr.add(tr.drum('shaker'), t0 + i * b / 2, .035, .45)
        if name != 'intro':
            for when, step in ((0, 0), (1.5, 7), (2, 0), (3, 7)):
                tr.add(tr.bass(root - 24 + step, .9 * b, .1), t0 + when * b, .26)
        if name == 'chorus':
            top = notes[2] + 12
            for when, d in ((0, 1.5), (1.5, .5), (2, 2)):
                tr.add(tr.reed(top + (2 if when == 1.5 else 0), d * b, 4.5), t0 + when * b, .07, .1)
    return tr.master(.22)


def havaiana():
    """Aloha FM: a slow Hawaiian sway (80 BPM) on the island vamp II7-V7-I, ukulele strums and picked arpeggios,
    a lap steel singing the melody with slides, upright-style bass and the ipu. Original composition."""
    vamp = ['A7', 'D7', 'G', 'G']
    form = [('intro', vamp, 4), ('verse', ['G', 'G', 'C', 'G', 'D7', 'D7', 'G', 'G'], 8),
            ('bridge', ['C', 'C', 'G', 'G', 'A7', 'A7', 'D7', 'D7'], 8), ('verse', ['G', 'G', 'C', 'G', 'D7', 'D7', 'G', 'G'], 8),
            ('solo', ['C', 'C', 'G', 'Em', 'A7', 'D7', 'G', 'G'], 8), ('outro', vamp, 4)]
    bars = sum(c for _, _, c in form)
    tr = Track(80, bars, 1959)
    b = tr.beat
    swing = .58   # the "and" comes late: a lazy island lilt
    # Melody per section: (beat in the 8-bar phrase, length in beats, MIDI note); close notes slide.
    verse_tune = [(0, 1.5, 71), (1.5, .5, 74), (2, 2, 76), (4, 1, 74), (5, 1, 72), (6, 2, 71), (8, 1.5, 72), (9.5, .5, 71), (10, 2, 69),
                  (12, 1, 67), (13, 1, 69), (14, 2, 71), (16, 1.5, 69), (17.5, .5, 71), (18, 2, 74), (20, 2, 72), (22, 2, 69),
                  (24, 3, 67), (27, 1, 71), (28, 4, 67)]
    bridge_tune = [(0, 2, 76), (2, 1, 79), (3, 1, 76), (4, 3, 74), (8, 1.5, 71), (9.5, .5, 74), (10, 2, 71), (12, 3, 67),
                   (16, 2, 73), (18, 1, 76), (19, 1, 73), (20, 2, 69), (24, 2, 72), (26, 1, 74), (27, 1, 72), (28, 4, 66)]
    solo_tune = [(0, 1, 76), (1, .5, 79), (1.5, .5, 76), (2, 2, 74), (4, 2, 72), (6, 2, 76), (8, 3, 74), (11, 1, 71),
                 (12, 2, 76), (14, 2, 71), (16, 1.5, 73), (17.5, .5, 76), (18, 2, 79), (20, 2, 78), (22, 2, 74),
                 (24, 2, 71), (26, 2, 74), (28, 4, 79)]
    tunes = {'verse': verse_tune, 'bridge': bridge_tune, 'solo': solo_tune}
    section_start, prev_name, prev_note = 0, None, None
    for bar, name, chord in tr.section_bars(form):
        notes, root = chord_notes(chord, 4)
        t0 = bar * 4 * b
        if name != prev_name:
            section_start, prev_name = bar, name
            for when, dur, note in tunes.get(name, []):
                glide = prev_note if prev_note is not None and abs(prev_note - note) <= 5 else None
                tr.add(tr.steel(note, dur * b + .25, glide), section_start * 4 * b + when * b, .085 if name != 'solo' else .095, .2)
                prev_note = note
        # Ukulele: strums in the vamp and the solo, a gentle picked arpeggio in verses and bridge.
        if name in ('intro', 'outro', 'solo'):
            for when, up in ((0, 0), (1, 0), (1 + swing, 1), (2 + swing, 1), (3, 0), (3 + swing, 1)):
                order = notes[::-1] if up else notes
                for k, n in enumerate(order[:3] + [order[0] + 12]):
                    tr.add(tr.pluck(n + 12, .55, .5, .9945), t0 + when * b + k * .011, .05 if up else .066, -.3 + k * .14)
        else:
            pattern = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[1] + 24]
            for i in range(8):
                when = i // 2 + (swing if i % 2 else 0)
                tr.add(tr.pluck(pattern[i % 4], .7, .45, .9955), t0 + when * b, .06, -.35 + (i % 4) * .2)
        # Bass on 1 and 3 (root, fifth); the ipu on 1, the late "and" of 2, and 3.
        if name != 'intro':
            tr.add(tr.bass(root - 24, 1.6 * b, .12), t0, .3)
            tr.add(tr.bass(root - 24 + 7, 1.6 * b, .12), t0 + 2 * b, .25)
        tr.add(tr.ipu(True), t0, .2)
        tr.add(tr.ipu(False), t0 + (1 + swing) * b, .09, -.2)
        tr.add(tr.ipu(True), t0 + 2 * b, .14)
        for i in range(4):
            tr.add(tr.drum('shaker'), t0 + (i + swing) * b, .028, .45)
    return tr.master(.26)


def tema():
    """Mare Alta theme (92 BPM, C major): ukulele, lap steel melody and a soft bass. Original motif."""
    form = [('a', ['C', 'Am', 'F', 'G7'], 8), ('b', ['F', 'C', 'Dm', 'G7'], 8), ('a2', ['C', 'Am', 'F', 'G7'], 8), ('end', ['F', 'G7', 'C', 'C'], 4)]
    bars = sum(c for _, _, c in form)
    tr = Track(92, bars, 2026)
    b = tr.beat
    a_tune = [(0, .5, 67), (.5, .5, 69), (1, 1, 72), (2, 2, 76), (4, 1, 74), (5, 1, 72), (6, 2, 69), (8, 1, 69), (9, 1, 72),
              (10, 2, 77), (12, 1, 76), (13, .5, 74), (13.5, .5, 72), (14, 2, 74), (16, 1, 72), (17, 1, 74), (18, 2, 76),
              (20, 1, 79), (21, 1, 76), (22, 2, 72), (24, 1.5, 77), (25.5, .5, 76), (26, 2, 74), (28, 4, 79)]
    b_tune = [(0, 2, 81), (2, 1, 79), (3, 1, 77), (4, 3, 76), (7, 1, 72), (8, 2, 74), (10, 1, 76), (11, 1, 77), (12, 4, 74),
              (16, 2, 77), (18, 1, 76), (19, 1, 74), (20, 3, 72), (23, 1, 69), (24, 2, 71), (26, 2, 74), (28, 4, 79)]
    end_tune = [(0, 2, 77), (2, 2, 74), (4, 2, 76), (6, 2, 74), (8, 8, 72)]
    tunes = {'a': a_tune, 'b': b_tune, 'a2': a_tune, 'end': end_tune}
    section_start, prev_name, prev_note = 0, None, None
    for bar, name, chord in tr.section_bars(form):
        notes, root = chord_notes(chord, 4)
        t0 = bar * 4 * b
        if name != prev_name:
            section_start, prev_name = bar, name
            for when, dur, note in tunes[name]:
                glide = prev_note if prev_note is not None and abs(prev_note - note) <= 4 else None
                tr.add(tr.steel(note, dur * b + .2, glide, .1), section_start * 4 * b + when * b, .09, .15)
                prev_note = note
        for when, up in ((0, 0), (1, 0), (1.5, 1), (2.5, 1), (3, 0), (3.5, 1)):
            order = notes[::-1] if up else notes
            for k, n in enumerate(order[:3] + [order[0] + 12]):
                tr.add(tr.pluck(n + 12, .5, .55, .994), t0 + when * b + k * .009, .05 if up else .068, -.25 + k * .15)
        tr.add(tr.bass(root - 24, 1.7 * b, .1), t0, .27)
        tr.add(tr.bass(root - 24 + 7, 1.7 * b, .1), t0 + 2 * b, .22)
        tr.add(tr.ipu(True), t0, .16)
        tr.add(tr.drum('rim'), t0 + b, .05, .2)
        tr.add(tr.drum('rim'), t0 + 3 * b, .05, .2)
        for i in range(8):
            tr.add(tr.drum('shaker'), t0 + i * b / 2, .025, .45)
    return tr.master(.24)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    import sys
    pick = set(sys.argv[1:])
    for name, fn in (('radio_reggae_roots', reggae), ('radio_calypso', calypso), ('radio_beach_pop', beach_pop),
                     ('radio_havaiana', havaiana), ('music_tema', tema)):
        if pick and name not in pick:
            continue
        data = fn()
        write(OUT / (name + '.wav'), data)
        report[name] = {'seconds': round(len(data) / SR, 1), 'peak': round(float(np.abs(data).max()), 3),
                        'rms': round(float(np.sqrt(np.mean(data ** 2))), 4)}
        print(name, report[name], flush=True)
    index = OUT / 'radio_music.json'
    tracks = json.loads(index.read_text(encoding='utf-8')).get('tracks', {}) if index.exists() else {}
    tracks.update(report)
    index.write_text(json.dumps({'license': 'CC0 (original, synthesised by tools/ue58/gen_radio_music.py)', 'tracks': tracks}, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
