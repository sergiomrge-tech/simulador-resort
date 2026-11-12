"""White HUD icons with alpha (tinted in Slate): star, bed, person. python tools/ue58/gen_hud_icons.py"""
import math
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/UI/Icons'
S, K = 128, 4            # drawn 4x and downsampled for smooth edges
W = (255, 255, 255, 255)


def canvas():
    im = Image.new('RGBA', (S * K, S * K), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def save(im, name):
    OUT.mkdir(parents=True, exist_ok=True)
    im.resize((S, S), Image.LANCZOS).save(OUT / f'T_Icon_{name}.png')


def star():
    im, d = canvas()
    c, r1, r2 = S * K / 2, S * K * .48, S * K * .2
    pts = [(c + (r1 if i % 2 == 0 else r2) * math.sin(math.pi * i / 5), c * 1.04 - (r1 if i % 2 == 0 else r2) * math.cos(math.pi * i / 5)) for i in range(10)]
    d.polygon(pts, fill=W)
    save(im, 'Star')


def bed():
    im, d = canvas()
    u = S * K / 32
    d.rounded_rectangle((3 * u, 8 * u, 6 * u, 27 * u), u, fill=W)          # headboard
    d.rounded_rectangle((3 * u, 17 * u, 29 * u, 23 * u), u, fill=W)         # mattress
    d.rounded_rectangle((8 * u, 13 * u, 14 * u, 17 * u), 1.5 * u, fill=W)   # pillow
    d.rounded_rectangle((14 * u, 14 * u, 29 * u, 18 * u), 1.5 * u, fill=W)  # blanket
    d.rectangle((26 * u, 22 * u, 29 * u, 27 * u), fill=W)                   # foot
    save(im, 'Bed')


def person():
    im, d = canvas()
    u = S * K / 32
    d.ellipse((11 * u, 3 * u, 21 * u, 13 * u), fill=W)
    d.rounded_rectangle((7 * u, 15 * u, 25 * u, 31 * u), 7 * u, fill=W)
    save(im, 'Person')


star(); bed(); person()
print('icons in', OUT)
