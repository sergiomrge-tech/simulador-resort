"""Art of the two playable arcade games of the Grand Hotel game room (5.4): sprites for the Slate game screens, the
cabinet title screens, marquees and side art. python tools/ue58/gen_arcade_art.py

Output: unreal/MareAlta/SourceArt/UI/Arcade/T_Arc_*.png (imported by Content/Python/mare_arcade.py into /Game/UI/Arcade).

"Corrida de Jangada" (top-down, flat vector look of the Kenney Pirate/Fish packs, CC0): water and sand tiles, rocks,
fishing boats (Kenney hull + crew), fish to catch and the jangada drawn here in the same style.
"Pinball do Farol" (P_*, drawn here; replaced Pega-Siri on 06/11) and the older "Pega-Siri" (pixel art, 160x120 board scaled x4 with nearest filter): beach with 9 crab holes drawn here, the crab
of OpenGameArt "Crab" by malekith97 (CC0), a golden siri recoloured from it, the jellyfish and the net drawn here.
Virtual screen of both games: 320 x 240 (MareArcade.h).
"""
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'unreal/MareAlta/SourceArt/UI/Arcade'
KP = Path('D:/Assets/Kenney/kenney_piratepack/PNG/Retina')
KF = Path('D:/Assets/Kenney/kenney_fish-pack_2.0/PNG/Double')
CRAB = Path('D:/Assets/OGA/crab/Crab_Walk.png')
FONT = ROOT / 'unreal/MareAlta/Content/UI/Fonts/PressStart2P-Regular.ttf'
OUTLINE = (77, 58, 46, 255)
HOLES = [(80 + 80 * c, 100 + 52 * r) for r in range(3) for c in range(3)]   # board pixels x2 (virtual 320x240)


def save(im, name):
    OUT.mkdir(parents=True, exist_ok=True)
    im.save(OUT / f'T_Arc_{name}.png')
    return im


def crop(im):
    return im.crop(im.getbbox())


def font(size):
    return ImageFont.truetype(str(FONT), size)


def pow2(im):
    """UE wants power-of-two textures: pad (centred, transparent) to the next power of two."""
    w, h = im.size
    W, H = 1 << (w - 1).bit_length(), 1 << (h - 1).bit_length()
    if (W, H) == (w, h):
        return im
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(im, ((W - w) // 2, (H - h) // 2))
    return out


# ------------------------------------------------------------------ Corrida de Jangada
def raft(scale=4):
    """Top-down jangada: six logs with lashings, the mast with a cream sail swung to one side, the fisherman."""
    W, H = 24 * scale, 36 * scale
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = scale
    for i in range(6):
        x0 = 1 * u + i * 3.6 * u
        top = (4 if i in (0, 5) else 2 if i in (1, 4) else 0) * u
        d.rounded_rectangle((x0, top + 2 * u, x0 + 3.6 * u, H - 1 * u), radius=1.6 * u, fill=(196, 140, 78, 255), outline=OUTLINE, width=u)
        d.line((x0 + 1.2 * u, top + 5 * u, x0 + 1.2 * u, H - 5 * u), fill=(170, 117, 62, 255), width=max(1, u // 2))
    for y in (9, 27):
        d.rectangle((1 * u, y * u, W - 1 * u, y * u + 1.2 * u), fill=(120, 84, 50, 255))
    # sail seen from above: a curved cream blade from the mast toward the stern, with its boom
    d.polygon([(12 * u, 12 * u), (23 * u, 30 * u), (13 * u, 33 * u), (10 * u, 15 * u)], fill=(246, 236, 210, 255), outline=OUTLINE, width=u)
    d.line((12 * u, 13 * u, 17.5 * u, 31.5 * u), fill=(222, 206, 172, 255), width=max(1, u // 2))
    d.line((12 * u, 13 * u, 23 * u, 30 * u), fill=OUTLINE, width=int(1.2 * u))
    d.ellipse((10.5 * u, 11.5 * u, 13.5 * u, 14.5 * u), fill=(120, 84, 50, 255), outline=OUTLINE, width=max(1, u // 2))
    # fisherman (Kenney crew, top view) at the stern
    crew = Image.open(KP / 'Ship parts/crew (2).png').convert('RGBA')
    crew = crew.resize((int(crew.width * u / 2.6), int(crew.height * u / 2.6)), Image.LANCZOS)
    im.alpha_composite(crew, (int(5 * u), int(25 * u)))
    return im.resize((W // 2, H // 2), Image.LANCZOS)


def boat():
    """Fishing boat crossing the river: Kenney small hull with two crew."""
    hull = Image.open(KP / 'Ship parts/hullSmall (2).png').convert('RGBA')
    for k, y in ((1, 24), (3, 62)):
        c = Image.open(KP / f'Ship parts/crew ({k}).png').convert('RGBA')
        hull.alpha_composite(c, ((hull.width - c.width) // 2, y))
    return hull.rotate(90, expand=True)   # sideways: it crosses the river


def recolour(im, f):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (*f(r, g, b), a)
    return im


def gold(r, g, b):
    l = (r * .3 + g * .59 + b * .11) / 255
    return (min(255, int(110 + 260 * l)), min(255, int(70 + 220 * l)), int(8 + 50 * l))


def jangada_title(raft_im, rocks, fish):
    W, H = 512, 384
    im = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    water = Image.open(KP / 'Tiles/tile_73.png').convert('RGBA')
    sand = Image.open(KP / 'Tiles/tile_68.png').convert('RGBA')
    for x in range(0, W, 128):
        for y in range(0, H, 128):
            im.alpha_composite(water, (x, y))
    d = ImageDraw.Draw(im)
    for y in range(0, H, 2):
        left = 70 + 28 * math.sin(y / 47)
        right = W - 70 - 28 * math.sin(y / 39 + 1)
        for x0, x1 in ((0, left), (right, W)):
            d.rectangle((x0, y, x1, y + 2), fill=(240, 222, 178, 255))
        d.rectangle((left - 3, y, left, y + 2), fill=(255, 255, 255, 255))
        d.rectangle((right, y, right + 3, y + 2), fill=(255, 255, 255, 255))
    big = raft_im.resize((raft_im.width * 2, raft_im.height * 2), Image.LANCZOS)
    im.alpha_composite(big, (W // 2 - big.width // 2, 220))
    im.alpha_composite(rocks[0].resize((70, 60)), (150, 150))
    im.alpha_composite(rocks[1].resize((60, 52)), (320, 110))
    f = fish.resize((48, 48))
    im.alpha_composite(f, (300, 250))
    panel = Image.new('RGBA', (W, 110), (20, 40, 90, 215))
    im.alpha_composite(panel, (0, 22))
    d = ImageDraw.Draw(im)
    for txt, y, size, col in (('CORRIDA DE', 34, 26, (255, 214, 92)), ('JANGADA', 70, 44, (255, 255, 255))):
        w = d.textlength(txt, font=font(size))
        d.text(((W - w) / 2 + 3, y + 3), txt, font=font(size), fill=(10, 20, 50))
        d.text(((W - w) / 2, y), txt, font=font(size), fill=col)
    txt = 'APERTE E PARA JOGAR'
    w = d.textlength(txt, font=font(14))
    d.rectangle((W / 2 - w / 2 - 10, 340, W / 2 + w / 2 + 10, 366), fill=(20, 40, 90, 215))
    d.text(((W - w) / 2, 346), txt, font=font(14), fill=(255, 255, 255))
    return im


# ------------------------------------------------------------------ Pega-Siri (pixel art)
SAND = [(236, 205, 140), (226, 192, 124), (244, 216, 158), (214, 178, 110)]


def siri_board():
    """160x120 beach: a strip of sea with foam on top, sand dithered from 4 tones, shells and 9 holes (lower lip is
    drawn as a separate layer so a crab comes out of the hole)."""
    rnd = random.Random(7)
    W, H = 160, 120
    im = Image.new('RGBA', (W, H))
    px = im.load()
    for y in range(H):
        for x in range(W):
            if y < 14 + 2 * math.sin(x / 9):
                px[x, y] = (40, 120, 170, 255) if (x + y) % 7 else (70, 150, 200, 255)
            elif y < 17 + 2 * math.sin(x / 9):
                px[x, y] = (250, 250, 245, 255)
            elif y < 22 + 2 * math.sin(x / 9 + 1):
                px[x, y] = (200, 170, 112, 255) if (x * 3 + y) % 5 else (214, 186, 128, 255)   # wet sand
            else:
                v = rnd.random()
                px[x, y] = (*SAND[0 if v < .55 else 1 if v < .8 else 2 if v < .95 else 3], 255)
    d = ImageDraw.Draw(im)
    for _ in range(14):   # shells and pebbles
        x, y = rnd.randrange(4, W - 4), rnd.randrange(26, H - 4)
        if any(abs(x - hx / 2) < 18 and abs(y - hy / 2) < 9 for hx, hy in HOLES):
            continue
        c = rnd.choice([(255, 240, 230), (240, 170, 160), (160, 140, 120)])
        d.point([(x, y), (x + 1, y), (x, y + 1)], fill=c)
    for hx, hy in HOLES:
        cx, cy = hx // 2, hy // 2
        d.ellipse((cx - 14, cy - 5, cx + 14, cy + 5), fill=(170, 132, 80, 255))      # rim
        d.ellipse((cx - 12, cy - 4, cx + 12, cy + 4), fill=(52, 36, 22, 255))        # hole
        d.ellipse((cx - 10, cy - 3, cx + 8, cy + 1), fill=(30, 20, 12, 255))
    return im


def hole_lips():
    """The front half of each hole rim (drawn over a crab coming out)."""
    im = Image.new('RGBA', (160, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for hx, hy in HOLES:
        cx, cy = hx // 2, hy // 2
        d.chord((cx - 14, cy - 5, cx + 14, cy + 5), 0, 180, fill=(170, 132, 80, 255))
        d.chord((cx - 12, cy - 4, cx + 12, cy + 4), 0, 180, fill=(196, 160, 100, 255))
    return im


def crab_frames():
    sheet = Image.open(CRAB).convert('RGBA')
    frames = [sheet.crop((64 * i, 0, 64 * i + 64, 64)) for i in (0, 1)]
    golden = [recolour(f.copy(), gold) for f in frames]
    return frames, golden


def jellyfish():
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.pieslice((4, 3, 28, 25), 180, 360, fill=(214, 120, 220, 220))
    d.pieslice((7, 5, 25, 21), 180, 360, fill=(240, 170, 245, 230))
    d.rectangle((4, 13, 28, 15), fill=(190, 90, 200, 230))
    for i, x in enumerate(range(7, 27, 4)):
        for y in range(16, 29):
            d.point((x + (1 if (y // 3 + i) % 2 else 0), y), fill=(230, 150, 235, 200))
    d.point([(11, 8), (12, 8), (11, 9)], fill=(255, 255, 255, 255))
    return im


def net():
    """Puçá (crab net) cursor: wooden handle and a ring with a mesh, 32x32."""
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line((20, 20, 30, 30), fill=(120, 80, 40, 255), width=3)
    d.ellipse((2, 2, 22, 22), outline=(60, 60, 60, 255), width=2)
    for k in range(5, 21, 4):
        d.line((k, 4, k, 20), fill=(235, 235, 235, 150))
        d.line((4, k, 20, k), fill=(235, 235, 235, 150))
    d.ellipse((2, 2, 22, 22), outline=(80, 80, 80, 255), width=2)
    return im


def up(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def siri_title(board, crab, golden):
    im = up(board, 4)
    im = im.resize((512, 384), Image.NEAREST) if im.size != (512, 384) else im
    big = up(crab, 3)
    im.alpha_composite(big, (60, 190))
    im.alpha_composite(up(golden, 3), (300, 200))
    d = ImageDraw.Draw(im)
    W = 512
    for txt, y, size, col in (('PEGA-SIRI', 40, 46, (255, 120, 60)),):
        w = d.textlength(txt, font=font(size))
        d.text(((W - w) / 2 + 4, y + 4), txt, font=font(size), fill=(60, 20, 10))
        d.text(((W - w) / 2, y), txt, font=font(size), fill=col)
    txt = 'APERTE E PARA JOGAR'
    w = d.textlength(txt, font=font(14))
    d.rectangle((W / 2 - w / 2 - 10, 340, W / 2 + w / 2 + 10, 366), fill=(60, 20, 10))
    d.text(((W - w) / 2, 346), txt, font=font(14), fill=(255, 255, 255))
    return im


# ------------------------------------------------------------------ cabinet art
def marquee(title, sub, bg, fg, art):
    W, H = 1024, 256
    im = Image.new('RGBA', (W, H), (*bg, 255))
    d = ImageDraw.Draw(im)
    for i in range(0, W, 32):   # sun rays
        d.polygon([(W / 2, H + 60), (i, 0), (i + 16, 0)], fill=tuple(min(255, c + 22) for c in bg) + (255,))
    for a in art:
        im.alpha_composite(*a)
    d = ImageDraw.Draw(im)
    w = d.textlength(title, font=font(64))
    d.text(((W - w) / 2 + 6, 70 + 6), title, font=font(64), fill=(20, 20, 30))
    d.text(((W - w) / 2, 70), title, font=font(64), fill=fg)
    w = d.textlength(sub, font=font(22))
    d.text(((W - w) / 2, 180), sub, font=font(22), fill=(255, 255, 255))
    return im


def side_art(bg, accent, sprite, flip=False):
    """Side panel decal (the whole side, 1024x2048): a big diagonal stripe and the game's hero sprite."""
    W, H = 1024, 2048
    im = Image.new('RGBA', (W, H), (*bg, 255))
    d = ImageDraw.Draw(im)
    d.polygon([(0, 1500), (W, 900), (W, 1250), (0, 1850)], fill=(*accent, 255))
    d.polygon([(0, 1880), (W, 1280), (W, 1330), (0, 1930)], fill=(255, 255, 255, 255))
    # u = 0 is the cabinet's front edge on both sides (gen_arcade_cabinet.py): the sprite sits in the back half, clear of
    # the screen and control-panel cut-outs of the profile, between the top and the stripe.
    s = sprite.resize((sprite.width * 420 // max(sprite.size), sprite.height * 420 // max(sprite.size)),
                      Image.NEAREST if max(sprite.size) <= 64 else Image.LANCZOS)
    if flip:
        s = s.transpose(Image.FLIP_LEFT_RIGHT)
    im.alpha_composite(s, (int(W * .64) - s.width // 2, 470 - s.height // 2 + 140))
    return im


# ------------------------------------------------------------------ Pinball do Farol (06/11, Sergio: "fliperama de pinball e corrida")
# Table geometry in virtual screen px (320x240), the same numbers as FMarePinball in Source/MareAlta/MareArcade.h:
PB_WALLS = [((84, 232), (84, 40)), ((84, 40), (116, 8)), ((116, 8), (204, 8)), ((204, 8), (236, 40)), ((236, 40), (236, 232)),
            ((220, 232), (220, 64)), ((220, 232), (236, 232)), ((84, 170), (124, 204)), ((220, 170), (180, 204))]
PB_BUMPERS = [(130, 80), (176, 80), (153, 118)]
PB_BUMPER_R = 11
PB_LANES = [128, 153, 178]          # rollover lanes at the top, y 22..40
PB_PIVOTS = [(126, 206), (178, 206)]   # flipper pivots, 22 px long (FMarePinball::FlipLen)


def pinball_table():
    """Playfield at 2x (640x480): night beach with the lighthouse beam painted on the wood, chrome walls, the plunger lane
    on the right, three rollover lanes and the inlanes; the bumpers, flippers and ball are sprites."""
    S = 2
    im = Image.new('RGBA', (320 * S, 240 * S), (14, 18, 40, 255))
    d = ImageDraw.Draw(im)
    for x in range(0, 320 * S, 6):   # cabinet sides: dark blue with stars
        for y in range(0, 240 * S, 6):
            if (x * 7 + y * 13) % 97 == 0:
                d.point((x, y), fill=(220, 230, 255, 255))
    table = [(84, 232), (84, 40), (116, 8), (204, 8), (236, 40), (236, 232)]
    d.polygon([(x * S, y * S) for x, y in table], fill=(22, 60, 110, 255))
    for i in range(14):   # sea gradient bands toward the bottom
        y0 = 120 + i * 8
        d.rectangle((85 * S, y0 * S, 235 * S, (y0 + 8) * S), fill=(22 + i * 3, 70 + i * 5, 120 + i * 4, 255))
    # lighthouse and its beam on the playfield
    d.polygon([(150 * S, 180 * S), (156 * S, 180 * S), (155 * S, 140 * S), (151 * S, 140 * S)], fill=(240, 240, 235, 255))
    for k in range(4):
        d.rectangle((150 * S, (148 + k * 9) * S, 156 * S, (152 + k * 9) * S), fill=(200, 40, 40, 255))
    d.polygon([(153 * S, 136 * S), (92 * S, 100 * S), (92 * S, 124 * S)], fill=(255, 236, 140, 90))
    d.ellipse((149 * S, 132 * S, 157 * S, 140 * S), fill=(255, 230, 120, 255))
    d.polygon([(140 * S, 182 * S), (166 * S, 182 * S), (172 * S, 192 * S), (134 * S, 192 * S)], fill=(90, 70, 50, 255))   # rock
    # lanes
    for x in PB_LANES:
        d.line(((x - 12) * S, 22 * S, (x - 12) * S, 40 * S), fill=(200, 210, 230, 255), width=S)
        d.line(((x + 12) * S, 22 * S, (x + 12) * S, 40 * S), fill=(200, 210, 230, 255), width=S)
        d.ellipse(((x - 4) * S, 30 * S, (x + 4) * S, 38 * S), outline=(255, 200, 60, 255), width=S)
    # plunger lane and its arrow
    d.rectangle((221 * S, 64 * S, 235 * S, 231 * S), fill=(30, 40, 70, 255))
    for k in range(3):
        d.polygon([(228 * S, (120 - k * 18) * S), (224 * S, (128 - k * 18) * S), (232 * S, (128 - k * 18) * S)], fill=(255, 200, 60, 255))
    # chrome walls
    for (a, b) in PB_WALLS:
        d.line((a[0] * S, a[1] * S, b[0] * S, b[1] * S), fill=(205, 215, 230, 255), width=3 * S)
        d.line((a[0] * S, a[1] * S, b[0] * S, b[1] * S), fill=(120, 130, 150, 255), width=S)
    d.text((96 * S, 214 * S), 'FAROL', font=font(8 * S), fill=(255, 220, 120, 255))
    return im


def pinball_bumper():
    im = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((2, 2, 62, 62), fill=(200, 30, 40, 255), outline=(255, 255, 255, 255), width=4)
    d.ellipse((14, 14, 50, 50), fill=(255, 210, 60, 255))
    d.ellipse((22, 18, 36, 30), fill=(255, 250, 220, 255))
    return im


def pinball_ball():
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((1, 1, 31, 31), fill=(150, 155, 165, 255))
    d.ellipse((4, 4, 26, 26), fill=(205, 210, 220, 255))
    d.ellipse((8, 6, 16, 13), fill=(255, 255, 255, 255))
    return im


def pinball_flipper():
    """Flipper seen from above, 128x32: the round pivot at the left (x 16), the tip at the right; rotated by the game."""
    im = Image.new('RGBA', (128, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(16, 2), (120, 12), (120, 20), (16, 30)], fill=(250, 250, 245, 255), outline=(40, 40, 50, 255))
    d.ellipse((2, 2, 30, 30), fill=(250, 250, 245, 255), outline=(40, 40, 50, 255), width=2)
    d.ellipse((114, 11, 124, 21), fill=(250, 250, 245, 255))
    d.line((24, 16, 112, 16), fill=(220, 40, 40, 255), width=3)
    d.ellipse((11, 11, 21, 21), fill=(220, 40, 40, 255))
    return im


def pinball_title(table, bumper):
    im = table.resize((512, 384))
    d = ImageDraw.Draw(im)
    W = 512
    for txt, y, size, col in (('PINBALL', 40, 50, (255, 214, 92)), ('DO FAROL', 104, 26, (255, 255, 255))):
        w = d.textlength(txt, font=font(size))
        d.text(((W - w) / 2 + 4, y + 4), txt, font=font(size), fill=(20, 20, 40))
        d.text(((W - w) / 2, y), txt, font=font(size), fill=col)
    im.alpha_composite(bumper.resize((96, 96)), (60, 200))
    im.alpha_composite(bumper.resize((96, 96)), (356, 200))
    txt = 'APERTE E PARA JOGAR'
    w = d.textlength(txt, font=font(14))
    d.rectangle((W / 2 - w / 2 - 10, 340, W / 2 + w / 2 + 10, 366), fill=(20, 20, 40))
    d.text(((W - w) / 2, 346), txt, font=font(14), fill=(255, 255, 255))
    return im


def main_pinball():
    table = pinball_table()
    save(pow2(table), 'P_Table')
    bumper = save(pinball_bumper(), 'P_Bumper')
    save(pinball_ball(), 'P_Ball')
    save(pinball_flipper(), 'P_Flipper')
    save(pinball_title(table, bumper).resize((512, 512)), 'P_Title')
    save(marquee('PINBALL', 'DO FAROL', (30, 40, 110), (255, 214, 92),
                 [(bumper.resize((120, 120)), (40, 64)), (bumper.resize((120, 120)), (864, 64))]), 'P_Marquee')
    save(side_art((30, 40, 110), (230, 60, 60), bumper), 'P_Side')


# ------------------------------------------------------------------ bitmap font
def font_atlas():
    """Press Start 2P (SIL OFL 1.1) ASCII 32..127 as a 16 x 6 grid of 16 px cells (the font's 8 px design at 2x),
    white on transparent: UMareArcade draws the arcade text from it (no font asset, pixel exact)."""
    im = Image.new('RGBA', (256, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font(16)
    for code in range(32, 128):
        i = code - 32
        d.text(((i % 16) * 16, (i // 16) * 16), chr(code), font=f, fill=(255, 255, 255, 255))
    return im


def main():
    save(font_atlas(), 'Font')
    rocks = [crop(Image.open(KP / f'Tiles/tile_{n}.png').convert('RGBA')) for n in (49, 50, 51, 66)]
    for i, r in enumerate(rocks):
        save(pow2(r), f'J_Rock{i + 1}')
    save(Image.open(KP / 'Tiles/tile_73.png').convert('RGBA'), 'J_Water')
    save(Image.open(KP / 'Tiles/tile_68.png').convert('RGBA'), 'J_Sand')
    r = save(pow2(raft()), 'J_Raft')
    save(pow2(boat()), 'J_Boat')
    fish = crop(Image.open(KF / 'fish_orange.png').convert('RGBA'))
    save(pow2(fish), 'J_Fish')
    save(pow2(crop(Image.open(KF / 'fish_blue.png').convert('RGBA'))), 'J_FishBlue')
    save(pow2(recolour(fish.copy(), gold)), 'J_FishGold')
    save(pow2(crop(Image.open(KF / 'bubble_a.png').convert('RGBA'))), 'J_Bubble')
    title = jangada_title(raft(), rocks, fish)
    save(title.resize((512, 512)), 'J_Title')   # the screen UVs stretch it back to 4:3
    save(marquee('JANGADA', 'CORRIDA NO MAR', (24, 92, 160), (255, 214, 92),
                 [(raft().resize((96, 144)), (60, 56)), (raft().resize((96, 144)).transpose(Image.FLIP_LEFT_RIGHT), (868, 56))]), 'J_Marquee')
    save(side_art((24, 92, 160), (88, 196, 220), raft(20)), 'J_Side')

    board = siri_board()
    save(up(board, 4), 'S_Board')
    save(pow2(up(hole_lips(), 4)), 'S_Lips')
    frames, golden = crab_frames()
    for i, f in enumerate(frames):
        save(up(f, 2), f'S_Crab{i + 1}')
    for i, f in enumerate(golden):
        save(up(f, 2), f'S_Gold{i + 1}')
    save(up(jellyfish(), 4), 'S_Jelly')
    save(up(net(), 4), 'S_Net')
    t = siri_title(board, frames[0], golden[1])
    save(t.resize((512, 512), Image.NEAREST), 'S_Title')
    save(marquee('PEGA-SIRI', 'NA AREIA DA PRAIA', (200, 70, 40), (255, 236, 120),
                 [(up(frames[0], 2), (40, 64)), (up(golden[1], 2), (856, 64))]), 'S_Marquee')
    save(side_art((200, 70, 40), (250, 160, 60), frames[0], flip=False), 'S_Side')
    main_pinball()
    print('arcade art in', OUT, len(list(OUT.glob('*.png'))), 'files')


main()
