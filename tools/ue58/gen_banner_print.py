"""Printed face of the party banner (festa_banner, tools/ue58/gen_festival.py): canvas with a woven texture, a border of
little flags, "Festa na Praia" in Patrick Hand (OFL, the game's title font) and a hand-drawn sun and waves.
    python tools/ue58/gen_banner_print.py
Output: unreal/MareAlta/SourceArt/Models/Festival/festa_banner_print.png (2048 x 512, sRGB) and festa_dj_print.png
(1024 x 256, front of the DJ desk)."""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / 'unreal/MareAlta/Content/UI/Fonts/PatrickHand-Regular.ttf'
OUT = ROOT / 'unreal/MareAlta/SourceArt/Models/Festival/festa_banner_print.png'
W, H = 2048, 512
INK = (38, 70, 92)        # deep sea blue
CORAL = (196, 92, 64)
FLAGS = [(176, 58, 52), (214, 168, 58), (52, 104, 150), (62, 128, 86), (200, 116, 56), (128, 72, 120)]


def canvas():
    rng = np.random.default_rng(7)
    base = np.array([238, 226, 198], np.float32)
    img = np.tile(base, (H, W, 1))
    # Plain weave: alternating warp/weft threads, a little uneven, plus soft blotches of dye.
    y, x = np.mgrid[0:H, 0:W]
    weave = (np.sin(x * math.pi / 2.0) * np.sin(y * math.pi / 2.0)) * 6
    img += weave[..., None]
    img += rng.normal(0, 3.5, (H, W, 1))
    blot = Image.fromarray(rng.normal(0, 1, (H // 32, W // 32)).astype(np.float32), 'F').resize((W, H), Image.BICUBIC)
    img += np.asarray(blot)[..., None] * 4
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB')


def flags(draw, top):
    step = 64
    for i, x in enumerate(range(0, W, step)):
        y0 = 26 if top else H - 26
        tip = y0 + (34 if top else -34)
        draw.polygon([(x + 6, y0), (x + step - 6, y0), (x + step / 2, tip)], fill=FLAGS[i % len(FLAGS)])
    y0 = 26 if top else H - 26
    draw.line([(0, y0), (W, y0)], fill=(120, 96, 70), width=4)


def sun(draw, cx, cy, r):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=CORAL, width=9)
    for k in range(12):
        a = k * math.pi / 6
        draw.line([(cx + math.cos(a) * (r + 16), cy + math.sin(a) * (r + 16)),
                   (cx + math.cos(a) * (r + 44), cy + math.sin(a) * (r + 44))], fill=CORAL, width=8)


def waves(draw, x0, y, w):
    for row in range(3):
        pts = [(x0 + t, y + row * 26 + 10 * math.sin(t / 28)) for t in range(0, w, 4)]
        draw.line(pts, fill=INK, width=7, joint='curve')


def main():
    img = canvas()
    draw = ImageDraw.Draw(img)
    flags(draw, True)
    flags(draw, False)
    big = ImageFont.truetype(str(FONT), 210)
    small = ImageFont.truetype(str(FONT), 70)
    text = 'Festa na Praia'
    tw = draw.textlength(text, font=big)
    draw.text(((W - tw) / 2 + 5, 96 + 6), text, font=big, fill=(150, 130, 100))    # soft print shadow
    draw.text(((W - tw) / 2, 96), text, font=big, fill=INK)
    sub = 'Maré Alta Resort'
    sw = draw.textlength(sub, font=small)
    draw.text(((W - sw) / 2, 330), sub, font=small, fill=CORAL)
    sun(draw, 190, 250, 62)
    waves(draw, 1740, 220, 230)
    # Printed ink soaks into the canvas: a slight blur and the weave showing through.
    img = img.filter(ImageFilter.GaussianBlur(.7))
    weave = canvas().convert('L')
    img = Image.blend(img, Image.merge('RGB', [weave] * 3), .06)
    random.seed(1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print('WROTE', OUT)


def dj_panel():
    """Front of the DJ desk (festa_dj): dark lacquered panel, "Maré Alta" and "DJ" in soft neon colours, 1024 x 256."""
    w, h = 1024, 256
    img = Image.new('RGB', (w, h), (22, 24, 30))
    draw = ImageDraw.Draw(img)
    for y in range(h):   # slight vertical sheen of a lacquered panel
        draw.line([(0, y), (w, y)], fill=(22 + int(10 * math.sin(math.pi * y / h)), 24 + int(10 * math.sin(math.pi * y / h)), 32))
    big = ImageFont.truetype(str(FONT), 150)
    small = ImageFont.truetype(str(FONT), 96)
    glow = Image.new('RGB', (w, h), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.text((60, 40), 'Maré Alta', font=big, fill=(70, 200, 210))
    gd.text((760, 70), 'DJ', font=small, fill=(230, 110, 170))
    img = Image.blend(img, Image.fromarray(np.maximum(np.asarray(img), np.asarray(glow.filter(ImageFilter.GaussianBlur(9))))), 1.0)
    draw = ImageDraw.Draw(img)
    draw.text((60, 40), 'Maré Alta', font=big, fill=(150, 235, 238))
    draw.text((760, 70), 'DJ', font=small, fill=(250, 170, 210))
    out = OUT.parent / 'festa_dj_print.png'
    img.save(out)
    print('WROTE', out)


if __name__ == '__main__':
    main()
    dj_panel()
