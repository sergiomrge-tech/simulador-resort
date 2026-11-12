"""Textures for the weather (drawn in code, CC0):
- T_RainStreaks.png: falling-rain streaks, tileable in both directions (the curtain pans it downwards); alpha = streak.
- T_PuddleMask.png: four puddle shapes in a 2x2 atlas, soft rim; alpha = water.
  python tools/ue58/gen_weather_textures.py  ->  unreal/MareAlta/SourceArt/Textures/Custom/"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Textures/Custom'


def rain(size=512, drops=900, seed=4):
    rnd = random.Random(seed)
    a = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(a)
    for _ in range(drops):
        x, y = rnd.uniform(0, size), rnd.uniform(0, size)
        length = rnd.uniform(18, 70)
        value = int(rnd.uniform(60, 200))
        for dx in (-size, 0, size):              # draw wrapped copies so the tile has no seams
            for dy in (-size, 0, size):
                d.line([x + dx, y + dy, x + dx + length * .06, y + dy + length], fill=value, width=1)
    a = a.filter(ImageFilter.GaussianBlur(.6))
    rgb = Image.new('RGB', (size, size), (210, 220, 228))
    rgb.putalpha(a)
    rgb.save(OUT / 'T_RainStreaks.png')


def puddles(size=1024, seed=8):
    rnd = random.Random(seed)
    a = np.zeros((size, size), np.float32)
    cell = size // 2
    yy, xx = np.mgrid[0:cell, 0:cell].astype(np.float32)
    for k in range(4):
        cx, cy = cell / 2, cell / 2
        ang = np.arctan2(yy - cy, xx - cx)
        r = np.hypot(xx - cx, yy - cy) / (cell * .42)
        # irregular rim: sum of a few angular harmonics
        rim = 1 + sum(rnd.uniform(.03, .1) / h ** .5 * np.sin(ang * h + rnd.uniform(0, 6.28)) for h in (1, 2, 3, 4))
        stretch = rnd.uniform(.55, .9)
        r = np.hypot((xx - cx) / 1.0, (yy - cy) / stretch) / (cell * .42) / rim
        m = np.clip((1 - r) / .12, 0, 1)
        y0, x0 = (k // 2) * cell, (k % 2) * cell
        a[y0:y0 + cell, x0:x0 + cell] = m
    img = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))
    rgb = Image.new('RGB', (size, size), (255, 255, 255))
    rgb.putalpha(img)
    rgb.save(OUT / 'T_PuddleMask.png')


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    rain()
    puddles()
    print('ok')
