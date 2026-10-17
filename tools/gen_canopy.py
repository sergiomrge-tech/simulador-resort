#!/usr/bin/env python3
"""Copa de Mata Atlântica vista de cima (CC0, gerada aqui).

Albedo em sRGB, oliva/verde-azulado, nunca abaixo de #1e2b16. O relevo das
cúpulas é suave: AO fraco e normal quase plano, para o tile não desenhar
meias-luas pretas. O shader ainda mistura duas escalas de UV.
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 1024
# sRGB, um pouco mais azul que o oliva amarelo — o sol clareia por cima
PAL = np.array([
    [42, 58, 38],
    [54, 74, 46],
    [68, 90, 54],
    [48, 66, 44],
    [58, 74, 46],
    [34, 50, 34],
    [62, 82, 50],
], dtype=np.float32)
FLOOR = np.array([30, 43, 22], dtype=np.float32)


def blur_wrap(a: np.ndarray, r: int) -> np.ndarray:
    k = 2 * r + 1
    acc = np.zeros_like(a)
    for d in range(-r, r + 1):
        acc += np.roll(a, d, axis=0)
    tmp = acc / k
    acc = np.zeros_like(a)
    for d in range(-r, r + 1):
        acc += np.roll(tmp, d, axis=1)
    return acc / k


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
    # AO fraco: a fresta fica oliva, não preta
    soft = blur_wrap(height, 6)
    hmax = max(float(soft.max()), 1.0)
    ao = 0.86 + 0.14 * (soft / hmax)
    col *= ao[:, :, None]
    grain = rng.normal(0.0, 1.6, size=col.shape).astype(np.float32)
    col = np.clip(col + grain, 0, 112)
    col = np.maximum(col, FLOOR)
    # normal suave. A borda da cúpula não pode virar um terminador preto.
    hx = (np.roll(soft, -1, axis=1) - np.roll(soft, 1, axis=1)) * 0.5
    hz = (np.roll(soft, -1, axis=0) - np.roll(soft, 1, axis=0)) * 0.5
    nx = -hx * 0.22
    nz = -hz * 0.22
    ny = np.ones_like(height) * 4.0
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
