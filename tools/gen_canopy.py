#!/usr/bin/env python3
"""Copa de Mata Atlântica vista de cima (CC0, gerada aqui).

Albedo em sRGB na faixa #2a4028–#4d6b3a, com cúpulas arredondadas, AO nas frestas
e um normal map de relevo. O jogo amostra isso no plano XZ da encosta.
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 1024
# sRGB
PAL = np.array([
    [42, 61, 28],
    [58, 82, 31],
    [77, 104, 40],
    [49, 68, 36],
    [61, 74, 32],
    [36, 52, 24],
    [70, 90, 38],
], dtype=np.float32)


def main() -> None:
    rng = np.random.default_rng(63)
    yy, xx = np.mgrid[0:N, 0:N]
    height = np.zeros((N, N), np.float32)
    col = np.zeros((N, N, 3), np.float32)
    weight = np.full((N, N), 0.15, np.float32)
    col[:] = PAL[5]
    crowns = []
    for i in range(86):
        rad = float(rng.uniform(58, 148))
        crowns.append((
            float(rng.uniform(0, N)),
            float(rng.uniform(0, N)),
            rad,
            PAL[int(rng.integers(0, len(PAL)))],
            rad * float(rng.uniform(0.42, 0.72)),
        ))
    for cx, cy, rad, color, amp in crowns:
        dx = xx - cx
        dy = yy - cy
        dx = np.minimum(np.abs(dx), N - np.abs(dx))
        dy = np.minimum(np.abs(dy), N - np.abs(dy))
        d = np.sqrt(dx * dx + dy * dy) / rad
        inside = d < 1.0
        if not np.any(inside):
            continue
        dome = np.zeros_like(d)
        dome[inside] = np.power(np.clip(1.0 - d[inside] * d[inside], 0.0, 1.0), 0.85) * amp
        w = dome / max(amp, 1.0)
        taller = dome > height
        height = np.maximum(height, dome)
        add = w * 0.85
        col = (col * weight[:, :, None] + color * add[:, :, None]) / (weight + add)[:, :, None]
        weight = weight + add
        # centro um pouco mais claro, ainda dentro da faixa
        lift = (w ** 2)[:, :, None] * 10.0
        col = np.clip(col + lift, 0, 255)
    # AO: fresta escura, topo da cúpula só um pouco mais claro
    hmax = max(float(height.max()), 1.0)
    ao = 0.58 + 0.42 * (height / hmax)
    col *= ao[:, :, None]
    grain = rng.normal(0.0, 2.2, size=col.shape).astype(np.float32)
    col = np.clip(col + grain, 28, 118)
    # normal: altura em pixels, R = +X, G = +Z, B = cima
    hx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5
    hz = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5
    nx = -hx
    nz = -hz
    ny = np.ones_like(height) * 0.95
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nmap = np.stack(((nx / ln) * 0.5 + 0.5, (nz / ln) * 0.5 + 0.5, (ny / ln) * 0.5 + 0.5), axis=-1)
    nmap = np.clip(nmap * 255.0, 0, 255).astype(np.uint8)
    rgb = np.clip(col, 0, 255).astype(np.uint8)
    out = os.path.join(ROOT, "assets", "tex")
    os.makedirs(out, exist_ok=True)
    Image.fromarray(rgb, "RGB").save(os.path.join(out, "canopy_diff.jpg"), quality=92, subsampling=0)
    Image.fromarray(nmap, "RGB").save(os.path.join(out, "canopy_nor.jpg"), quality=92, subsampling=0)
    print("canopy", rgb.shape, "mean", rgb.mean(axis=(0, 1)).round(1))


if __name__ == "__main__":
    main()
