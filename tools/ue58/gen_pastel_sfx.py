"""Food truck sounds (CHECKLIST_EXPANSOES 3.2), synthesized like the other synth actions of fetch_action_sfx.py (no
CC0 recording of oil frying or a sugar-cane mill crank was found in the packs it uses):
  pastel_fry_1/2   oil sizzle with crackles as the pastel goes into the oil (played every couple of seconds)
  pastel_ready_1   soft ding: the pastel reached the golden point
  cana_crank_1/2   one turn of the sugar-cane mill crank: wooden creak, gear rumble, cane crushing
Writes SourceArt/Audio/Actions/<name>.wav (48 kHz mono PCM16) and adds them to manifest.json; the editor import is
mare_hud.import_sfx_only('pastel_fry,pastel_ready,cana_crank').
Run: python tools/ue58/gen_pastel_sfx.py"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_action_sfx as F  # noqa: E402

RNG = np.random.default_rng(3232)
RATE = F.RATE


def sizzle(sec=2.2, seed=0):
    r = np.random.default_rng(100 + seed)
    t = F.t_axis(sec)
    hiss = F._filt(r.normal(0, 1, len(t)), "bandpass", [2200, 9000]) * (0.55 + 0.25 * np.sin(2 * np.pi * 0.7 * t + seed))
    pops = np.zeros_like(t)
    for c in r.uniform(0, sec, int(60 * sec)):
        i = int(c * RATE)
        n = int(r.uniform(0.002, 0.008) * RATE)
        k = F._filt(r.normal(0, 1, n), "highpass", 1800) * np.exp(-np.arange(n) / (0.0015 * RATE))
        pops[i:i + n] += k[: len(pops[i:i + n])] * r.uniform(0.3, 1.4)
    bubbles = F._filt(r.normal(0, 1, len(t)), "bandpass", [300, 900]) * 0.12
    env = np.clip(t / 0.05, 0, 1) * np.clip((sec - t) / 0.4, 0, 1)
    return (hiss * 0.35 + pops * 0.5 + bubbles) * env


def crank(sec=0.75, seed=0):
    r = np.random.default_rng(200 + seed)
    t = F.t_axis(sec)
    turn = np.sin(np.pi * t / sec)
    # Creak: a resonant squeak gliding up and down with the turn.
    f = 380 + 160 * np.sin(2 * np.pi * t / sec + seed) + 25 * np.sin(2 * np.pi * 31 * t)
    creak = np.sin(2 * np.pi * np.cumsum(f) / RATE) * (0.5 + 0.5 * np.sin(2 * np.pi * 47 * t) ** 2) * 0.12
    creak = F._filt(creak, "bandpass", [250, 2400])
    rumble = F._filt(r.normal(0, 1, len(t)), "lowpass", 180) * 0.9
    crush = F._filt(r.normal(0, 1, len(t)), "bandpass", [600, 2600]) * (0.4 + 0.6 * (np.sin(2 * np.pi * 9 * t) > 0.6)) * 0.25
    return (creak + rumble + crush) * turn


def main():
    out = F.OUT
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actions = manifest.get("actions", manifest)
    new = {
        "pastel_fry": ([F.finish(sizzle(2.2, 0), lowpass=11000), F.finish(sizzle(2.0, 1), lowpass=11000)], 0.2, "Óleo chiando com o pastel (síntese)."),
        "pastel_ready": ([F.finish(F.synth_counter_bell(f0=1760.0, decay=0.6, strike=0.7), lowpass=7000)], 0.2, "Ding suave: pastel no ponto (síntese)."),
        "cana_crank": ([F.finish(crank(0.75, 0), lowpass=6000), F.finish(crank(0.7, 1), lowpass=6000)], 0.22, "Volta da manivela da moenda de cana (síntese)."),
    }
    for action, (sigs, volume, desc) in new.items():
        files = []
        for n, sig in enumerate(sigs, 1):
            name = f"{action}_{n}.wav"
            # Loudness like the other actions (fetch_action_sfx TARGET_DB default), never above the -3 dBFS peak.
            gain = 10 ** ((F.TARGET_DB["default"] - F.active_loudness(sig)) / 20)
            sig = sig * min(gain, 10 ** (F.PEAK_DB / 20) / max(1e-9, np.abs(sig).max()))
            sf.write(str(out / name), np.clip(sig, -1, 1), RATE, subtype="PCM_16")
            files.append({"file": name, "sources": [{"synth": action, "license": F.SYNTH_LICENSE}]})
        actions[action] = {"description": desc, "volume": volume, "files": files}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("ok", list(new))


if __name__ == "__main__":
    main()
