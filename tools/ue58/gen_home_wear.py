"""Wear masks for the player's house plaster (11/11, Sergio: "sem textura de desgaste, quero mais realista").
One 2048 x 2048 tiling picture, four masks (linear):
  R  blotches: large soft stains (dirt, sun fading), 0 clean .. 1 stained
  G  streaks: vertical runs of rain water, thin and long, denser in bands
  B  cracks: hairline cracks, a sparse net with a few long ones (1 on the crack)
  A  peel: patches where the paint has come off (hard-edged islands), with a soft rim
The material (mare_home.plaster) reads it world-aligned, 4 m per tile, and combines the masks with the height on the
wall (damp rises from the ground, streaks hang from the eaves).
  python tools/ue58/gen_home_wear.py  ->  D:/Assets/Mare/home_wear/T_HomeWear.png (+ a preview .jpg)"""
from pathlib import Path
import numpy as np
from PIL import Image

OUT = Path('D:/Assets/Mare/home_wear')
N = 2048


def fft_noise(beta, seed, sx=1.0, sy=1.0):
    rng = np.random.default_rng(seed)
    fx = np.fft.fftfreq(N)[:, None] * sy
    fy = np.fft.rfftfreq(N)[None, :] * sx
    f = np.hypot(fx, fy)
    f[0, 0] = 1
    spec = (rng.normal(size=f.shape) + 1j * rng.normal(size=f.shape)) / f ** beta
    spec[0, 0] = 0
    out = np.fft.irfft2(spec, s=(N, N))
    return out / np.abs(out).max()


def unit(a, lo, hi):
    return np.clip((a - np.percentile(a, lo)) / (np.percentile(a, hi) - np.percentile(a, lo)), 0, 1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ii, jj = np.meshgrid(np.arange(N), np.arange(N), indexing='ij')
    blot = unit(fft_noise(1.7, 1) + .5 * fft_noise(1.1, 2), 40, 97) ** 1.3
    # streaks: noise stretched 14x along the wall's height, gated by a slow horizontal band noise (they come in groups)
    run = fft_noise(.75, 3, sx=1.0, sy=22.0)
    group = unit(fft_noise(1.6, 4, sx=1.0, sy=6.0), 45, 90)
    streak = unit(run, 70, 99.5) ** 1.4 * (.2 + .8 * group)
    # cracks: zero lines of a warped field, kept only where a second field allows (sparse)
    wx, wy = fft_noise(2.2, 5), fft_noise(2.2, 6)
    f = fft_noise(1.8, 7)[(ii + (wx * 120).astype(int)) % N, (jj + (wy * 120).astype(int)) % N]
    allow = unit(fft_noise(2.0, 8), 40, 65)
    crack = np.clip(1 - np.abs(f) / .009, 0, 1) * allow
    fine = np.clip(1 - np.abs(fft_noise(1.3, 9)) / .004, 0, 1) * unit(fft_noise(2.6, 10), 70, 90) * .5
    crack = np.clip(crack + fine, 0, 1)
    # peel: islands of a ridged noise, hard edge, more of them near cracks
    p = fft_noise(1.5, 11) + .6 * fft_noise(.9, 12) + .25 * crack
    peel = np.clip((p - np.percentile(p, 90)) / .02, 0, 1)
    img = np.stack((blot, streak, crack, peel), 2)
    Image.fromarray((img * 255).astype(np.uint8), 'RGBA').save(OUT / 'T_HomeWear.png')
    prev = np.concatenate([np.repeat(img[::4, ::4, k:k + 1], 3, 2) for k in range(4)], 1)
    Image.fromarray((prev * 255).astype(np.uint8)).save(OUT / 'preview.jpg', quality=88)
    print('ok', [round(float(img[:, :, k].mean()), 3) for k in range(4)])


if __name__ == '__main__':
    main()
