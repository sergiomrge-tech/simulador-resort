"""Download, choose and convert the CC0 action sound effects (P1, PENDENCIAS_100 sec. 7).

Reproducible from scratch:
    python tools/ue58/fetch_action_sfx.py            # download (if missing) + convert
    python tools/ue58/fetch_action_sfx.py --list     # list the files of every downloaded pack
    python tools/ue58/fetch_action_sfx.py --redownload

Downloads go to D:/CodexTemp/sfx_dl/<pack>/ (one fresh folder per pack). The archives are
treated as untrusted data: they are only unzipped (with path checks) and decoded as audio,
nothing inside them is executed. Output: WAV PCM 16-bit, 48 kHz, mono, peak about -3 dBFS,
in unreal/MareAlta/SourceArt/Audio/Actions/<action>_<n>.wav plus manifest.json.
Nothing is imported into Unreal here.

All sources are CC0 (Kenney packs and OpenGameArt entries whose license field is CC0).
A few sounds with no good CC0 recording are synthesized with numpy (marked "synth").
"""
import argparse
import http.cookiejar
import io
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfilt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unreal/MareAlta/SourceArt/Audio/Actions"
DL = Path("D:/CodexTemp/sfx_dl")
RATE = 48000
PEAK_DB = -3.0
UA = "Mozilla/5.0 (MareAltaResort asset fetch)"

# pack -> (kind, page, download id/url). Kenney needs a signed link requested with the page cookie.
PACKS = {
    "kenney_impact": ("kenney", "https://kenney.nl/assets/impact-sounds", "assets/impact-sounds"),
    "kenney_interface": ("kenney", "https://kenney.nl/assets/interface-sounds", "assets/interface-sounds"),
    "kenney_casino": ("kenney", "https://kenney.nl/assets/casino-audio", "assets/casino-audio"),
    "kenney_rpg": ("kenney", "https://kenney.nl/assets/rpg-audio", "assets/rpg-audio"),
    "oga_100sfx": ("direct", "https://opengameart.org/content/100-cc0-sfx",
                   "https://opengameart.org/sites/default/files/100-CC0-SFX_0.zip"),
    "oga_100sfx2": ("direct", "https://opengameart.org/content/100-cc0-sfx-2",
                    "https://opengameart.org/sites/default/files/sfx_100_v2.zip"),
    "oga_metal_wood": ("direct", "https://opengameart.org/content/100-cc0-metal-and-wood-sfx",
                       "https://opengameart.org/sites/default/files/100-CC0-wood-metal-SFX.zip"),
    "oga_80rpg": ("direct", "https://opengameart.org/content/80-cc0-rpg-sfx",
                  "https://opengameart.org/sites/default/files/80-CC0-RPG-SFX_0.zip"),
}


def _opener():
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders = [("User-Agent", UA)]
    return op


def _zip_url(kind, page, ref, op):
    if kind == "direct":
        return ref
    op.open(page, timeout=60).read()  # session cookie
    req = urllib.request.Request("https://kenney.nl/download-link/" + ref.encode().hex(),
                                 headers={"Referer": page})
    data = json.loads(op.open(req, timeout=60).read().decode("utf-8"))
    if not data.get("url"):
        raise RuntimeError(f"Kenney: no signed link for {page}: {data}")
    return data["url"]


def _safe_extract(blob, dest):
    dest = dest.resolve()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            target = (dest / info.filename).resolve()
            if dest not in target.parents:
                raise RuntimeError(f"unsafe path in archive: {info.filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(info))


def download(redownload=False):
    op = _opener()
    for pack, (kind, page, ref) in PACKS.items():
        dest = DL / pack
        if dest.exists() and any(dest.rglob("*")) and not redownload:
            continue
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        url = _zip_url(kind, page, ref, op)
        blob = op.open(url, timeout=300).read()
        _safe_extract(blob, dest)
        print(f"[dl] {pack}: {len(blob) / 1e6:.1f} MB")


def find(pack, name):
    """Find an audio file by (case-insensitive) file name inside a pack folder."""
    hits = [p for p in (DL / pack).rglob("*") if p.is_file() and p.name.lower() == name.lower()]
    if not hits:
        raise FileNotFoundError(f"{pack}: {name}")
    return sorted(hits, key=lambda p: len(str(p)))[0]


# ----------------------------------------------------------------------------- processing
def load(path):
    data, rate = sf.read(str(path), always_2d=True, dtype="float64")
    data = data.mean(axis=1)
    if rate != RATE:
        g = np.gcd(int(rate), RATE)
        data = resample_poly(data, RATE // g, int(rate) // g)
    return data


def _filt(x, kind, freq, order=2):
    return sosfilt(butter(order, freq, btype=kind, fs=RATE, output="sos"), x)


def finish(x, lowpass=None, highpass=None, max_len=None, gain_db=0.0, fade_out=0.02):
    """DC removal, optional softening filters, trim silence to <=15 ms lead, fades, peak -3 dBFS."""
    x = np.asarray(x, dtype=np.float64)
    x = x - x.mean()
    if highpass:
        x = _filt(x, "highpass", highpass)
    if lowpass:
        x = _filt(x, "lowpass", lowpass)
    env = np.abs(x)
    thr = env.max() * 10 ** (-40 / 20)
    idx = np.nonzero(env > thr)[0]
    start = max(0, idx[0] - int(0.015 * RATE))
    end = min(len(x), idx[-1] + int(0.05 * RATE))
    x = x[start:end]
    if max_len and len(x) > max_len * RATE:
        x = x[: int(max_len * RATE)]
        fo = int(0.12 * RATE)
        x[-fo:] *= np.linspace(1, 0, fo) ** 2
    fi = min(int(0.003 * RATE), len(x) // 4)
    x[:fi] *= np.linspace(0, 1, fi)
    fo = min(int(fade_out * RATE), len(x) // 3)
    x[-fo:] *= np.linspace(1, 0, fo) ** 2
    x = x / max(np.abs(x).max(), 1e-9) * 10 ** ((PEAK_DB + gain_db) / 20)
    return x


def from_file(pack, name, **kw):
    return finish(load(find(pack, name)), **kw)


def concat(parts, gaps):
    """Join decoded clips with gaps (seconds) before each part after the first."""
    out = [parts[0]]
    for p, g in zip(parts[1:], gaps):
        out.append(np.zeros(int(g * RATE)))
        out.append(p)
    return np.concatenate(out)


def mix(parts):
    """parts: list of (offset_seconds, signal, gain)."""
    n = max(int(o * RATE) + len(s) for o, s, _ in parts)
    y = np.zeros(n)
    for o, s, g in parts:
        i = int(o * RATE)
        y[i:i + len(s)] += s * g
    return y


# ----------------------------------------------------------------------------- synthesis
RNG = np.random.default_rng(5802)


def t_axis(sec):
    return np.arange(int(sec * RATE)) / RATE


def synth_counter_bell(f0=2380.0, decay=1.1, strike=1.0):
    """Hotel desk bell: struck thin brass dome, inharmonic partials, soft hammer."""
    t = t_axis(max(1.2, decay * 3.2))
    ratios = [1.0, 1.506, 2.0, 2.74, 3.98]
    amps = [1.0, 0.45, 0.22, 0.18, 0.07]
    decs = [decay, decay * 0.7, decay * 0.45, decay * 0.3, decay * 0.18]
    y = np.zeros_like(t)
    for r, a, d in zip(ratios, amps, decs):
        for split, share in ((1.0, 0.6), (1.0012, 0.4)):  # dome modes come in close pairs -> slow natural beating
            y += share * a * np.sin(2 * np.pi * f0 * r * split * t + RNG.uniform(0, 6.28)) * np.exp(-t / d)
    click = _filt(RNG.normal(0, 1, len(t)), "bandpass", [1500, 6000]) * np.exp(-t / 0.002) * 0.35 * strike
    return y + click


def synth_blender(sec=1.8):
    """Short blender pulse: motor whine with spin-up/down, blade-and-ice rattle, glass jar body."""
    t = t_axis(sec)
    env = np.clip(t / 0.12, 0, 1) * np.clip((sec - t) / 0.3, 0, 1) ** 1.5
    spin = np.clip(t / 0.3, 0, 1) ** 0.7 * np.clip((sec - t) / 0.35, 0.35, 1)
    fmot = 110 + 230 * spin + 6 * np.sin(2 * np.pi * 7 * t)  # universal motor whine, rises with speed
    ph = 2 * np.pi * np.cumsum(fmot) / RATE
    motor = sum((1.0 if k % 2 else 0.55) * np.sin(k * ph + 0.3 * k) / k ** 0.9 for k in range(1, 16))
    motor = _filt(motor, "lowpass", 3200)
    load = 1 + 0.35 * np.sin(ph * 0.5) ** 2  # blades through ice/fruit load the motor once per turn
    grind = _filt(RNG.normal(0, 1, len(t)), "bandpass", [700, 2600]) * load * 0.18
    chunks = np.zeros_like(t)
    for c in np.sort(RNG.uniform(0.08, sec * 0.6, 34)):  # ice chunks knocking the jar, fewer as they crush
        i = int(c * RATE)
        n = int(0.03 * RATE)
        k = _filt(RNG.normal(0, 1, n), "bandpass", [1500, 4200]) * np.exp(-np.arange(n) / (0.005 * RATE))
        chunks[i:i + n] += k[: len(chunks[i:i + n])] * RNG.uniform(0.3, 1)
    chunks *= np.exp(-t / (sec * 0.35))
    y = (motor * 0.55 * load + grind + chunks * 0.45) * env
    return _filt(y, "lowpass", 5000)


def synth_shaker(sec=1.6, rate_hz=6.2):
    """Cocktail shaker: ice cubes thrown against steel walls in a back-and-forth rhythm."""
    t = t_axis(sec)
    y = np.zeros_like(t)
    period = 1 / rate_hz
    k = 0
    tt = 0.05
    while tt < sec - 0.12:
        burst_n = RNG.integers(6, 11)
        for _ in range(burst_n):  # several cubes hit per throw
            i = int((tt + RNG.uniform(0, 0.035)) * RATE)
            n = int(0.05 * RATE)
            hit = _filt(RNG.normal(0, 1, n), "bandpass", [RNG.uniform(1800, 2600), RNG.uniform(6000, 8000)])
            ring = np.sin(2 * np.pi * RNG.uniform(3100, 4200) * np.arange(n) / RATE) * 0.25
            seg = (hit + ring) * np.exp(-np.arange(n) / (RNG.uniform(0.004, 0.009) * RATE)) * RNG.uniform(0.35, 1.0)
            y[i:i + n] += seg[: len(y[i:i + n])]
        k += 1
        tt += period * RNG.uniform(0.92, 1.08)
    slosh = _filt(RNG.normal(0, 1, len(t)), "bandpass", [300, 1200]) * (0.5 + 0.5 * np.sin(2 * np.pi * rate_hz * t)) * 0.12
    env = np.clip(t / 0.05, 0, 1) * np.clip((sec - t) / 0.1, 0, 1)
    return (y + slosh) * env


def synth_ice_in_glass(n_cubes=3):
    """Ice cubes dropped into an empty glass: glass tink + cube clacks, small resonant tail."""
    t = t_axis(0.9)
    y = np.zeros_like(t)
    when = 0.0
    for c in range(n_cubes):
        when += RNG.uniform(0.06, 0.14) if c else 0.0
        i = int(when * RATE)
        n = int(0.4 * RATE)
        tn = np.arange(n) / RATE
        hit = _filt(RNG.normal(0, 1, n), "bandpass", [2500, 9000]) * np.exp(-tn / 0.004)
        f = RNG.uniform(2700, 3300)
        ring = (np.sin(2 * np.pi * f * tn) + 0.5 * np.sin(2 * np.pi * f * 2.32 * tn)) * np.exp(-tn / 0.12) * 0.18
        bounce = np.zeros(n)
        for b in range(RNG.integers(1, 3)):
            j = int(RNG.uniform(0.03, 0.08) * (b + 1) * RATE)
            m = int(0.02 * RATE)
            bounce[j:j + m] += _filt(RNG.normal(0, 1, m), "bandpass", [2000, 7000]) * np.exp(-np.arange(m) / (0.003 * RATE)) * 0.35
        seg = (hit + ring + bounce) * RNG.uniform(0.7, 1.0)
        y[i:i + n] += seg[: len(y) - i]
    return y


def synth_pour(sec=1.5):
    """Liquid poured into a glass: bubbly gurgle whose resonance rises as the glass fills."""
    t = t_axis(sec)
    # Stream noise through the glass cavity resonance, whose pitch rises as the glass fills (overlap-add blocks).
    stream = np.zeros_like(t)
    blk = int(0.04 * RATE)
    win = np.hanning(2 * blk)
    for i in range(0, len(t) - 2 * blk, blk):
        c = 520 + 1150 * (i / len(t))
        seg = _filt(RNG.normal(0, 1, 2 * blk + 2000), "bandpass", [c * 0.82, c * 1.22])[2000:]
        stream[i:i + 2 * blk] += seg * win
    stream *= 0.35
    bub = np.zeros_like(t)
    tt = 0.03
    while tt < sec - 0.1:
        i = int(tt * RATE)
        n = int(0.025 * RATE)
        tn = np.arange(n) / RATE
        f0 = 480 + 1000 * (tt / sec) + RNG.uniform(-140, 180)
        f = f0 * (1 + 1.8 * tn / 0.025)  # Minnaert bubble chirp
        attack = np.clip(tn / 0.0015, 0, 1)  # no click at the bubble onset
        bub[i:i + n] += np.sin(2 * np.pi * np.cumsum(f) / RATE) * attack * np.exp(-tn / 0.006) * RNG.uniform(0.25, 0.8)
        tt += RNG.uniform(0.006, 0.022)
    env = np.clip(t / 0.06, 0, 1) * np.clip((sec - t) / 0.18, 0, 1)
    return _filt((stream + bub) * env, "lowpass", 4500)


def synth_trash_bag(sec=0.9):
    """Plastic garbage bag being tied/lifted: crinkly bursts of filtered crackle."""
    t = t_axis(sec)
    y = np.zeros_like(t)
    for c in RNG.uniform(0.0, sec - 0.05, 160):
        i = int(c * RATE)
        n = int(RNG.uniform(0.002, 0.008) * RATE)
        y[i:i + n] += RNG.normal(0, 1, n) * RNG.uniform(0.1, 1.0) ** 2
    rustle = RNG.normal(0, 1, len(t)) * 0.06
    env = np.sin(np.pi * np.clip(t / sec, 0, 1)) ** 0.6
    return _filt(_filt((y + rustle) * env, "highpass", 900), "lowpass", 7500)


def synth_roll(sec=0.75, rate_hz=13.0):
    """Ball rolling down the pocket return channel: low rumble with rotation flutter and tiny knocks."""
    t = t_axis(sec)
    rumble = _filt(RNG.normal(0, 1, len(t)), "bandpass", [120, 900])
    flutter = 0.6 + 0.4 * np.sin(2 * np.pi * rate_hz * t * (1 - 0.25 * t / sec)) ** 2
    y = rumble * flutter * np.exp(-t / (sec * 0.45))
    for c in (0.12, 0.31, 0.47):
        i = int(c * RATE)
        n = int(0.03 * RATE)
        knock = _filt(RNG.normal(0, 1, n), "bandpass", [400, 1600]) * np.exp(-np.arange(n) / (0.004 * RATE))
        y[i:i + n] += knock[: len(y[i:i + n])] * np.exp(-c * 3) * 1.4
    return y


# ----------------------------------------------------------------------------- the selection
def raw(pack, name, lowpass=None, highpass=None, start=0.0, dur=None):
    """Decoded clip, filtered, leading silence trimmed, peak 1 (for layering)."""
    x = load(find(pack, name))
    x = x[int(start * RATE): int((start + dur) * RATE) if dur else None]
    x = x - x.mean()
    if highpass:
        x = _filt(x, "highpass", highpass)
    if lowpass:
        x = _filt(x, "lowpass", lowpass)
    env = np.abs(x)
    i0 = max(0, np.nonzero(env > env.max() * 0.01)[0][0] - int(0.005 * RATE))
    x = x[i0:]
    if start or dur:
        f = min(int(0.03 * RATE), len(x) // 4)
        x[:f] *= np.linspace(0, 1, f)
        x[-f:] *= np.linspace(1, 0, f)
    return x / max(np.abs(x).max(), 1e-9)


def src(pack, name):
    return f"{pack}/{name}"


def build():
    """action -> list of (signal, [sources]). 'synth:<what>' marks numpy synthesis in this script."""
    A = {}
    # Reception ---------------------------------------------------------------------------------
    A["reception_bell"] = [
        (finish(raw("oga_100sfx", "bell_01.ogg"), lowpass=6500, max_len=1.3, fade_out=0.2), [src("oga_100sfx", "bell_01.ogg")]),
        (finish(synth_counter_bell(2380, 0.7), lowpass=8000, fade_out=0.3), ["synth:counter_bell"]),
        (finish(synth_counter_bell(2210, 0.6, 0.8), lowpass=7500, fade_out=0.3), ["synth:counter_bell"]),
    ]
    A["reception_keys"] = [
        (finish(raw("oga_metal_wood", "keys_03.ogg"), lowpass=8500), [src("oga_metal_wood", "keys_03.ogg")]),
        (finish(raw("oga_metal_wood", "keys_02.ogg"), lowpass=8500), [src("oga_metal_wood", "keys_02.ogg")]),
        (finish(raw("oga_metal_wood", "keys_01.ogg"), lowpass=8500), [src("oga_metal_wood", "keys_01.ogg")]),
    ]
    A["reception_checkin"] = [  # paper slid over the desk then the stamp; stamp alone; pen signature
        (finish(mix([(0.0, raw("oga_100sfx", "paper_02.ogg"), 0.55),
                     (0.40, raw("kenney_rpg", "bookPlace1.ogg", lowpass=5000), 1.0)]), lowpass=7500),
         [src("oga_100sfx", "paper_02.ogg"), src("kenney_rpg", "bookPlace1.ogg")]),
        (finish(raw("kenney_rpg", "bookPlace3.ogg", lowpass=5000)), [src("kenney_rpg", "bookPlace3.ogg")]),
        (finish(concat([raw("kenney_interface", "scratch_004.ogg", lowpass=6000),
                        raw("kenney_interface", "scratch_005.ogg", lowpass=6000)], [0.06]), lowpass=6500, fade_out=0.06),
         [src("kenney_interface", "scratch_004.ogg"), src("kenney_interface", "scratch_005.ogg")]),
    ]
    # Room cleaning -----------------------------------------------------------------------------
    A["cleaning_bed"] = [
        (finish(raw("kenney_rpg", "cloth1.ogg")), [src("kenney_rpg", "cloth1.ogg")]),
        (finish(raw("kenney_rpg", "cloth3.ogg")), [src("kenney_rpg", "cloth3.ogg")]),
        (finish(mix([(0.0, raw("kenney_rpg", "cloth2.ogg"), 0.8), (0.22, raw("kenney_rpg", "cloth1.ogg"), 1.0)])),
         [src("kenney_rpg", "cloth2.ogg"), src("kenney_rpg", "cloth1.ogg")]),
    ]
    A["cleaning_towels"] = [
        (finish(mix([(0.0, raw("kenney_rpg", "cloth2.ogg"), 1.0),
                     (0.30, raw("kenney_rpg", "dropLeather.ogg", lowpass=4000), 0.8)])),
         [src("kenney_rpg", "cloth2.ogg"), src("kenney_rpg", "dropLeather.ogg")]),
        (finish(mix([(0.0, raw("kenney_rpg", "cloth4.ogg"), 1.0),
                     (0.26, raw("kenney_rpg", "dropLeather.ogg", lowpass=3500), 0.7)])),
         [src("kenney_rpg", "cloth4.ogg"), src("kenney_rpg", "dropLeather.ogg")]),
    ]
    A["cleaning_trash"] = [  # bag rustle, then the bag set down
        (finish(mix([(0.0, raw("oga_100sfx", "paper_01.ogg", lowpass=7000), 1.0),
                     (0.38, raw("kenney_rpg", "dropLeather.ogg", lowpass=3000), 0.75)])),
         [src("oga_100sfx", "paper_01.ogg"), src("kenney_rpg", "dropLeather.ogg")]),
        (finish(mix([(0.0, _filt(synth_trash_bag(0.8), "lowpass", 5500), 1.0),
                     (0.62, raw("kenney_rpg", "dropLeather.ogg", lowpass=3000), 0.6)])),
         ["synth:trash_bag", src("kenney_rpg", "dropLeather.ogg")]),
    ]
    # Pool / snooker ----------------------------------------------------------------------------
    A["pool_cue_hit"] = [
        (finish(mix([(0.0, raw("kenney_impact", "impactGeneric_light_001.ogg"), 1.0),
                     (0.0, raw("oga_80rpg", "item_stone_02.ogg", lowpass=6000), 0.3)])),
         [src("kenney_impact", "impactGeneric_light_001.ogg"), src("oga_80rpg", "item_stone_02.ogg")]),
        (finish(mix([(0.0, raw("kenney_impact", "impactGeneric_light_003.ogg"), 1.0),
                     (0.0, raw("oga_80rpg", "item_stone_04.ogg", lowpass=6000), 0.25)])),
         [src("kenney_impact", "impactGeneric_light_003.ogg"), src("oga_80rpg", "item_stone_04.ogg")]),
    ]
    A["pool_ball_clack"] = [
        (finish(raw("oga_80rpg", "item_stone_02.ogg"), lowpass=7500), [src("oga_80rpg", "item_stone_02.ogg")]),
        (finish(raw("oga_80rpg", "item_stone_04.ogg"), lowpass=7500), [src("oga_80rpg", "item_stone_04.ogg")]),
        (finish(raw("oga_100sfx2", "sfx100v2_stones_02.ogg"), lowpass=7500),
         [src("oga_100sfx2", "sfx100v2_stones_02.ogg")]),
    ]
    A["pool_pocket"] = [  # knock on the pocket jaw, drop, roll down the return channel
        (finish(mix([(0.0, raw("kenney_impact", "impactWood_light_000.ogg"), 0.8),
                     (0.05, raw("kenney_impact", "impactSoft_medium_001.ogg"), 0.6),
                     (0.12, synth_roll(0.75), 0.35)])),
         [src("kenney_impact", "impactWood_light_000.ogg"), src("kenney_impact", "impactSoft_medium_001.ogg"),
          "synth:ball_roll"]),
        (finish(mix([(0.0, raw("kenney_impact", "impactWood_light_002.ogg"), 0.7),
                     (0.06, raw("kenney_impact", "impactSoft_medium_003.ogg"), 0.65),
                     (0.14, synth_roll(0.6, 15.0), 0.3)])),
         [src("kenney_impact", "impactWood_light_002.ogg"), src("kenney_impact", "impactSoft_medium_003.ogg"),
          "synth:ball_roll"]),
    ]
    A["pool_rail_bounce"] = [  # rubber cushion thump + a little ball click
        (finish(mix([(0.0, raw("kenney_impact", "impactSoft_medium_000.ogg"), 1.0),
                     (0.0, raw("kenney_impact", "impactGeneric_light_002.ogg"), 0.45)]), lowpass=5000),
         [src("kenney_impact", "impactSoft_medium_000.ogg"), src("kenney_impact", "impactGeneric_light_002.ogg")]),
        (finish(mix([(0.0, raw("kenney_impact", "impactSoft_medium_002.ogg"), 1.0),
                     (0.0, raw("kenney_impact", "impactGeneric_light_004.ogg"), 0.4)]), lowpass=5000),
         [src("kenney_impact", "impactSoft_medium_002.ogg"), src("kenney_impact", "impactGeneric_light_004.ogg")]),
    ]
    # Bar ---------------------------------------------------------------------------------------
    A["bar_blender"] = [
        (finish(synth_blender(1.8), fade_out=0.2), ["synth:blender"]),
        (finish(synth_blender(1.2), fade_out=0.2), ["synth:blender"]),
    ]
    A["bar_shaker"] = [
        (finish(raw("kenney_casino", "dice-shake-3.ogg"), lowpass=7000), [src("kenney_casino", "dice-shake-3.ogg")]),
        (finish(raw("kenney_casino", "dice-shake-1.ogg"), lowpass=7000), [src("kenney_casino", "dice-shake-1.ogg")]),
        (finish(synth_shaker(1.5), fade_out=0.15), ["synth:shaker"]),
    ]
    A["bar_ice_glass"] = [
        (finish(raw("oga_100sfx2", "sfx100v2_glass_05.ogg"), lowpass=8000), [src("oga_100sfx2", "sfx100v2_glass_05.ogg")]),
        (finish(raw("oga_100sfx2", "sfx100v2_glass_02.ogg"), lowpass=8000), [src("oga_100sfx2", "sfx100v2_glass_02.ogg")]),
        (finish(synth_ice_in_glass(3), lowpass=8000), ["synth:ice_in_glass"]),
    ]
    A["bar_pour"] = [
        (finish(synth_pour(1.5), fade_out=0.2), ["synth:pour"]),
        (finish(mix([(0.0, raw("oga_100sfx2", "sfx100v2_loop_water_01.ogg", start=1.0, dur=1.3, highpass=250), 0.7),
                     (0.0, synth_pour(1.3), 0.6)]), lowpass=6000, fade_out=0.25),
         [src("oga_100sfx2", "sfx100v2_loop_water_01.ogg"), "synth:pour"]),
    ]
    # Money / negotiation -----------------------------------------------------------------------
    A["money_coins"] = [
        (finish(raw("kenney_rpg", "handleCoins.ogg"), lowpass=8000), [src("kenney_rpg", "handleCoins.ogg")]),
        (finish(raw("oga_80rpg", "item_coins_03.ogg"), lowpass=8000), [src("oga_80rpg", "item_coins_03.ogg")]),
    ]
    A["money_register"] = [  # small register bell, drawer latch, coins
        (finish(mix([(0.0, synth_counter_bell(3150, 0.45, 0.6), 0.35),
                     (0.06, raw("kenney_rpg", "metalLatch.ogg", lowpass=6000), 0.7),
                     (0.20, raw("kenney_rpg", "handleCoins.ogg", lowpass=7500), 0.8)]), lowpass=8000),
         ["synth:register_bell", src("kenney_rpg", "metalLatch.ogg"), src("kenney_rpg", "handleCoins.ogg")]),
    ]
    A["deal_accept"] = [
        (finish(raw("kenney_interface", "confirmation_001.ogg"), lowpass=6000),
         [src("kenney_interface", "confirmation_001.ogg")]),
        (finish(raw("kenney_interface", "confirmation_004.ogg"), lowpass=6000),
         [src("kenney_interface", "confirmation_004.ogg")]),
    ]
    A["deal_decline"] = [
        (finish(raw("kenney_interface", "question_004.ogg"), lowpass=5000), [src("kenney_interface", "question_004.ogg")]),
        (finish(raw("kenney_interface", "question_002.ogg"), lowpass=5000), [src("kenney_interface", "question_002.ogg")]),
    ]
    return A


# Suggested PlayCue volume = 10^((target - loudness)/20), clamped to [0.03, 0.45]. Loudness is the RMS of the
# active part of the sound (20 ms frames within 30 dB of the loudest one). Existing cues land around
# -30..-45 dB effective (bell .2 -> -32, click .16 -> -44, kiosk_cash .3 -> -45, door .27 -> -34),
# so new actions aim at -36 dB (interface -41, sustained machine/liquid -39). Soft, never strident.
TARGET_DB = {"default": -36.0, "deal_accept": -41.0, "deal_decline": -42.0, "bar_blender": -40.0,
             "bar_pour": -39.0, "bar_shaker": -38.0, "reception_bell": -37.0, "pool_ball_clack": -37.0}
MAX_TRIM_DB = 8.0  # within an action, louder variants are trimmed toward the softest one (at most this much)


def active_loudness(x):
    w = int(0.02 * RATE)
    fr = np.sqrt(np.array([np.mean(x[i:i + w] ** 2) for i in range(0, max(1, len(x) - w + 1), w)]))
    act = fr[fr > fr.max() * 10 ** (-30 / 20)]
    return float(20 * np.log10(np.sqrt(np.mean(act ** 2)) + 1e-12))


DESCRIPTION = {
    "reception_bell": "Campainha de balcão da recepção (ding).",
    "reception_keys": "Chaves entregues/colocadas no balcão.",
    "reception_checkin": "Check-in: papel e carimbo, carimbo sozinho, assinatura com caneta.",
    "cleaning_bed": "Arrumar a cama (lençol/tecido).",
    "cleaning_towels": "Recolher toalhas e colocá-las no cesto.",
    "cleaning_trash": "Fechar e largar o saco de lixo.",
    "pool_cue_hit": "Tacada: ponta do taco na bola branca.",
    "pool_ball_clack": "Bola contra bola.",
    "pool_pocket": "Bola entrando na caçapa e rolando na canaleta.",
    "pool_rail_bounce": "Bola batendo na tabela.",
    "bar_blender": "Liquidificador curto (pulso com gelo).",
    "bar_shaker": "Coqueteleira com gelo.",
    "bar_ice_glass": "Gelo caindo no copo.",
    "bar_pour": "Servir líquido no copo.",
    "money_coins": "Moedas ao receber pagamento.",
    "money_register": "Caixa registradora (sininho, gaveta, moedas).",
    "deal_accept": "Negociação aceita (interface suave, ascendente).",
    "deal_decline": "Negociação recusada (interface suave, descendente).",
}

LICENSE = {
    "kenney_impact": "CC0 1.0 (Kenney, Impact Sounds)",
    "kenney_interface": "CC0 1.0 (Kenney, Interface Sounds)",
    "kenney_casino": "CC0 1.0 (Kenney, Casino Audio)",
    "kenney_rpg": "CC0 1.0 (Kenney, RPG Audio)",
    "oga_100sfx": "CC0 (OpenGameArt, 100 CC0 SFX)",
    "oga_100sfx2": "CC0 (OpenGameArt, 100 CC0 SFX #2)",
    "oga_metal_wood": "CC0 (OpenGameArt, 100 CC0 metal and wood SFX)",
    "oga_80rpg": "CC0 (OpenGameArt, 80 CC0 RPG SFX)",
}
SYNTH_LICENSE = "CC0 (original numpy synthesis, tools/ue58/fetch_action_sfx.py)"


def _source_info(s):
    if s.startswith("synth:"):
        return {"synth": s[6:], "license": SYNTH_LICENSE}
    pack, name = s.split("/", 1)
    return {"pack": pack, "file": name, "page": PACKS[pack][1], "license": LICENSE[pack]}


def write_all():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.wav"):
        old.unlink()
    actions = {}
    total = 0
    for action, items in build().items():
        loud = [active_loudness(sig) for sig, _ in items]
        ref = min(loud)
        trims = [-min(MAX_TRIM_DB, max(0.0, l - ref - 1.0)) for l in loud]
        files = []
        for n, ((sig, sources), trim) in enumerate(zip(items, trims), 1):
            name = f"{action}_{n}.wav"
            pcm = np.clip(sig * 10 ** (trim / 20), -1, 1)
            sf.write(str(OUT / name), pcm, RATE, subtype="PCM_16")
            total += (OUT / name).stat().st_size
            peak = float(np.abs(pcm).max())
            lead = np.nonzero(np.abs(pcm) > peak * 0.01)[0][0] / RATE
            files.append({
                "file": name,
                "seconds": round(len(pcm) / RATE, 3),
                "peak_dbfs": round(20 * np.log10(peak), 2),
                "loudness_db": round(active_loudness(pcm), 1),
                "lead_ms": round(lead * 1000, 1),
                "sources": [_source_info(s) for s in sources],
            })
        mean_loud = 20 * np.log10(np.mean([10 ** (f["loudness_db"] / 20) for f in files]))
        target = TARGET_DB.get(action, TARGET_DB["default"])
        volume = round(float(np.clip(10 ** ((target - mean_loud) / 20), 0.03, 0.45)), 2)
        actions[action] = {"description": DESCRIPTION[action], "volume": volume,
                           "ue_folder": "/Game/Audio/Actions", "files": files}
    manifest = {
        "generator": "tools/ue58/fetch_action_sfx.py",
        "format": "WAV PCM 16-bit, 48000 Hz, mono, peak -3 dBFS (variants of one action level-matched, so some peak lower)",
        "note": ("Not imported into Unreal yet. 'volume' is the suggested PlayCue volume (0-1), applied before "
                 "the Effects/Master buses; pick one file at random per play."),
        "actions": actions,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"actions": len(actions), "files": sum(len(a["files"]) for a in actions.values()),
                      "bytes": total, "output": str(OUT)}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="list the audio files of every downloaded pack")
    ap.add_argument("--redownload", action="store_true", help="wipe and download every pack again")
    ap.add_argument("--no-download", action="store_true", help="use what is already in D:/CodexTemp/sfx_dl")
    a = ap.parse_args()
    if not a.no_download:
        download(a.redownload)
    if a.list:
        for pack in PACKS:
            files = sorted(p.relative_to(DL / pack).as_posix() for p in (DL / pack).rglob("*")
                           if p.suffix.lower() in (".ogg", ".wav", ".mp3", ".flac"))
            print(f"== {pack} ({len(files)})")
            print("  " + "\n  ".join(files))
        return
    write_all()


if __name__ == "__main__":
    main()


