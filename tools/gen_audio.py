"""Gera por síntese (numpy, sem samples de terceiros) os sons de eventos: trovão, chuva, vento, forró (festa junina) e batida do DJ.
Saída: assets/audio/*.ogg (via ffmpeg). Uso: python3 tools/gen_audio.py"""
import numpy as np, os, subprocess, wave
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "audio")
SR = 32000
rng = np.random.default_rng(42)

def save(name, x):
    x = np.clip(x / max(1e-6, np.max(np.abs(x))) * 0.9, -1, 1)
    tmp = f"/tmp/{name}.wav"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libvorbis", "-q:a", "3", os.path.join(OUT, name + ".ogg")], check=True)
    os.remove(tmp)
    print("ok", name)

def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.zeros_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s; y[i] = s
    return y

def lp_fast(x, fc):
    from scipy.signal import butter, lfilter
    b, a = butter(2, fc / (SR / 2)); return lfilter(b, a, x)

def hp_fast(x, fc):
    from scipy.signal import butter, lfilter
    b, a = butter(2, fc / (SR / 2), "high"); return lfilter(b, a, x)

def t(n): return np.arange(int(n * SR)) / SR

def loopfade(x, f=0.5):
    n = int(f * SR)
    y = x.copy(); w = np.linspace(0, 1, n)
    y[:n] = x[:n] * w + x[-n:] * (1 - w)
    return y[:-n]

# trovão: estalo seco + rumores com ecos
d = 5.0; tt = t(d)
n = rng.standard_normal(len(tt))
crack = lp_fast(hp_fast(n, 500), 6000) * np.exp(-tt * 18) * 1.0
rumble = lp_fast(n, 140) * (np.exp(-tt * 0.9) * (1 - np.exp(-tt * 8)))
for k, (dl, g) in enumerate([(0.7, 0.7), (1.5, 0.5), (2.3, 0.4)]):
    i = int(dl * SR)
    rumble[i:] += lp_fast(rng.standard_normal(len(tt) - i), 110) * np.exp(-tt[: len(tt) - i] * 1.2) * g * 0.8
save("thunder", crack * 0.7 + rumble * 3.0)

# chuva: ruído rosa-ish com chiado, 8 s em laço
tt = t(9.0)
n = rng.standard_normal(len(tt))
rain = hp_fast(lp_fast(n, 9000), 900) * (0.8 + 0.2 * np.sin(tt * 0.9))
drops = np.zeros(len(tt))
for i in rng.integers(0, len(tt), 900): 
    drops[i] = rng.uniform(0.3, 1.0)
drops = lp_fast(drops, 7000) * 6
save("rain_loop", loopfade(rain + drops * 0.5))

# vento: ruído passa-baixa com varredura lenta, 10 s
tt = t(11.0)
n = rng.standard_normal(len(tt))
w = lp_fast(n, 600)
mod = 0.55 + 0.45 * np.sin(tt * 2 * np.pi / 5.0) * np.sin(tt * 2 * np.pi / 3.1 + 1)
w2 = lp_fast(n[::-1].copy(), 1500) * 0.3
save("wind_loop", loopfade((w * 3.0 + w2) * mod))

# instrumentos
def kick(dur=0.35, f0=130, f1=42):
    x = t(dur); f = f1 + (f0 - f1) * np.exp(-x * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9)
def hat(dur=0.08): 
    x = t(dur); return hp_fast(rng.standard_normal(len(x)), 7000) * np.exp(-x * 55) * 0.4
def zabumba(f=75, dur=0.3):
    x = t(dur); return np.sin(2 * np.pi * f * x * (1 + 0.5 * np.exp(-x * 30))) * np.exp(-x * 11)
def triangle(dur=0.5):
    x = t(dur); s = np.zeros(len(x))
    for h, g in ((1, 1.0), (2.76, 0.6), (5.4, 0.4), (8.9, 0.25)):
        s += g * np.sin(2 * np.pi * 3100 * h * 0.35 * x)
    return s * np.exp(-x * 14) * 0.25
def accordion(freq, dur, vib=5.5):
    x = t(dur); f = freq * (1 + 0.004 * np.sin(2 * np.pi * vib * x))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.35 * np.sin(3 * ph) + 0.2 * np.sin(5 * ph)
    s += 0.6 * np.sin(2 * np.pi * np.cumsum(f * 1.004) / SR)   # segunda palheta levemente desafinada
    env = np.minimum(1, x * 40) * np.minimum(1, (dur - x) * 25)
    return s * env * 0.25
def bass(freq, dur):
    x = t(dur); ph = 2 * np.pi * freq * x
    s = np.sign(np.sin(ph)) * 0.5 + np.sin(ph)
    return lp_fast(s, 500) * np.exp(-x * 4) * np.minimum(1, x * 100)
def put(buf, snd, at):
    i = int(at * SR); n = min(len(snd), len(buf) - i)
    if n > 0: buf[i:i + n] += snd[:n]
def mtof(m): return 440 * 2 ** ((m - 69) / 12)

# forró (baião) 100 bpm, 8 compassos em Sol maior: G - C - D - G
bpm = 100; beat = 60 / bpm; bars = 8
buf = np.zeros(int(bars * 4 * beat * SR) + SR)
prog = [(55, [67, 71, 74]), (60, [67, 72, 76]), (62, [66, 69, 74]), (55, [67, 71, 74])] * 2
for b in range(bars):
    root, ch = prog[b]; o = b * 4 * beat
    for k in (0, 1.5, 2, 3.5):           # baião: zabumba 1 . . e 3 .
        put(buf, zabumba(), o + k * beat * 1.0 * 0.5 * 2 / 2)
    for k in range(8):
        put(buf, triangle(), o + k * beat / 2 + (0.0 if k % 2 == 0 else 0.0))
    put(buf, bass(mtof(root), beat * 1.4), o); put(buf, bass(mtof(root + 7), beat), o + 2 * beat)
    melody = [(0, 1.5), (1.5, 0.5), (2, 1.0), (3, 1.0)] if b % 2 == 0 else [(0, 1.0), (1, 0.5), (1.5, 1.5), (3, 1.0)]
    for i, (st, ln) in enumerate(melody):
        note = ch[(i + b) % 3] + (12 if i % 2 else 0)
        put(buf, accordion(mtof(note), ln * beat * 0.95), o + st * beat)
    for n_ in ch:
        put(buf, accordion(mtof(n_ - 12), 4 * beat * 0.97) * 0.5, o)
save("forro_loop", buf[: int(bars * 4 * beat * SR)])

# DJ: 124 bpm, 8 compassos, Lá menor
bpm = 124; beat = 60 / bpm; bars = 8
buf = np.zeros(int(bars * 4 * beat * SR) + SR)
roots = [57, 53, 48, 55] * 2
for b in range(bars):
    o = b * 4 * beat; r = roots[b]
    for k in range(4):
        put(buf, kick(), o + k * beat)
        put(buf, hat(), o + k * beat + beat / 2)
        put(buf, hat(0.05) * 0.5, o + k * beat + beat * 0.25)
        put(buf, bass(mtof(r - 12), beat * 0.45), o + k * beat + beat / 2)
    if b % 2 == 1:
        n = rng.standard_normal(int(beat * SR)); clap = hp_fast(n, 1200) * np.exp(-t(beat) * 25)
        put(buf, clap, o + beat); put(buf, clap, o + 3 * beat)
    arp = [r, r + 7, r + 12, r + 15] if b % 2 == 0 else [r + 3, r + 10, r + 12, r + 19]
    for k in range(16):
        x = t(beat / 4 * 0.9); n_ = arp[k % 4] + 12
        s = np.sign(np.sin(2 * np.pi * mtof(n_) * x)) * 0.5 + np.sin(2 * np.pi * mtof(n_) * x)
        put(buf, lp_fast(s, 3500) * np.exp(-x * 9) * 0.22, o + k * beat / 4)
save("dj_loop", buf[: int(bars * 4 * beat * SR)])
