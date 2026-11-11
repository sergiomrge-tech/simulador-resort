"""Brazilian street newsstand (banca de jornal) of painted ribbed sheet steel, modelled with bpy.

Replaces the old green box (tools/gen_code_props.py newsstand()). Real-world metres, origin at the centre of the
2.2 x 1.6 m footprint, base at z=0, service side (front) at -Y. Nothing reaches beyond x = +-1.35.
Body: stamped ribbed steel walls (real relief), plinth, corner angles, rivets, roof with skirt, gutter and downspout,
plain sign fascia (z 2.21-2.53, no text: the game writes it), roll-up shutter box with a corrugated curtain,
wooden counter with folded newspaper stacks, a gum display and a postcard spinner, striped canvas awning with a
scalloped valance and tube frame, a lamp under the awning (material 'glow'), two open side doors carrying magazines,
a tilted magazine rack under the counter and shelves with magazines on the back wall inside.
Covers, newspaper front pages, postcards and gum packs are drawn in code (PIL); paint and wood use Poly Haven CC0.
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_newsstand.py
Output: D:/Assets/Mare/mare_newsstand/mare_newsstand.glb"""
import math
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter, ImageFont  # noqa: E402
from gen_custom_furniture import box, box_uv, export, finish, lathe, material, mesh_obj, reset, tube  # noqa: E402

SLUG = 'mare_newsstand'
OUT = Path('D:/Assets/Mare') / SLUG
FONTS = 'C:/Windows/Fonts/'

# ------------------------------------------------------------------ main dimensions
HW, HD = 1.10, 0.80            # half width / half depth of the body
Z0 = 0.14                      # plinth top = interior floor
ZC = 0.90                      # underside of the counter
ZCT = 0.95                     # counter top
WALL_T = 0.04
WALL_TOP = 2.26                # walls end inside the roof skirt
RIB = 0.012


# ------------------------------------------------------------------ textures drawn in code
def font(size, name='arialbd.ttf'):
    try:
        return ImageFont.truetype(FONTS + name, size)
    except Exception:
        return ImageFont.load_default()


CW, CH, ATLAS = 256, 340, 2048          # magazine cell and atlas size (8 x 6 cells)
TITLES = ['VIVA+', 'FOCO', 'AGORA', 'GOLAÇO', 'SABOR', 'ZENIT', 'CASA&LAR', 'MOTOR', 'TECNO', 'FÉRIAS', 'SAÚDE', 'NOVA ERA',
          'HQ KIDS', 'CINEMA', 'MODA', 'JARDIM', 'PESCA', 'VIAGEM', 'CIÊNCIA', 'DICAS', 'FAMA', 'PRAIA', 'BRASA', 'OBRAS']
PALETTE = [(196, 74, 62), (46, 112, 150), (222, 176, 60), (60, 130, 88), (150, 70, 120), (230, 120, 60), (40, 70, 110), (190, 190, 180),
           (170, 60, 90), (70, 150, 160), (120, 100, 70), (210, 90, 100), (90, 80, 150), (60, 60, 64), (225, 150, 160), (110, 150, 70),
           (50, 110, 120), (200, 130, 50), (80, 110, 170), (176, 160, 120), (200, 60, 60), (60, 160, 190), (150, 50, 40), (130, 130, 100)]
LINES = ['ESPECIAL', 'DICAS', 'EXCLUSIVO', 'GRÁTIS', '+ 50 FOTOS', 'SEGREDOS', 'NOVIDADE', 'PASSO A PASSO']
CELL_EDGE, CELL_BACK, CELL_GUM, CELL_POST = 34, 35, 30, 24


def cell_xy(i):
    return (i % 8) * CW, (i // 8) * CH


def px_uv(x0, y0, x1, y1, size=ATLAS):
    return (x0 / size, 1 - y1 / size, x1 / size, 1 - y0 / size)       # (u0, v0 bottom, u1, v1 top)


def cell_uv(i):
    x, y = cell_xy(i)
    return px_uv(x, y, x + CW, y + CH)


def post_uv(k):
    x, y = cell_xy(CELL_POST + k // 2)
    y += (k % 2) * 170
    return px_uv(x, y, x + CW, y + 170)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_cover(im, i):
    rnd = random.Random(100 + i)
    x0, y0 = cell_xy(i)
    d = ImageDraw.Draw(im)
    bg = PALETTE[i]
    dark = mix(bg, (10, 10, 20), .55)
    for yy in range(CH):
        d.line([(x0, y0 + yy), (x0 + CW - 1, y0 + yy)], fill=mix(bg, dark, yy / CH))
    title = TITLES[i]
    f = font(52)
    while d.textlength(title, font=f) > CW - 22:
        f = font(f.size - 3)
    d.text((x0 + CW / 2 + 2, y0 + 10 + 2), title, font=f, fill=(0, 0, 0), anchor='ma')
    d.text((x0 + CW / 2, y0 + 10), title, font=f, fill=(250, 244, 230) if sum(bg) < 500 else (30, 30, 40), anchor='ma')
    bx0, by0, bx1, by1 = x0 + 14, y0 + 78, x0 + CW - 14, y0 + 256
    kind = i % 6
    if kind == 0:                                           # bust of a person
        d.rectangle([bx0, by0, bx1, by1], fill=mix((200, 210, 220), bg, .35))
        skin = [(232, 190, 160), (190, 140, 105), (120, 80, 58), (245, 205, 175)][rnd.randrange(4)]
        hair = [(40, 28, 20), (180, 130, 60), (20, 20, 22), (120, 50, 30)][rnd.randrange(4)]
        cx = (bx0 + bx1) // 2
        d.ellipse([cx - 62, by1 - 70, cx + 62, by1 + 90], fill=mix(bg, (255, 255, 255), .35))
        d.ellipse([cx - 40, by0 + 20, cx + 40, by0 + 118], fill=hair)
        d.ellipse([cx - 33, by0 + 34, cx + 33, by0 + 116], fill=skin)
        d.pieslice([cx - 40, by0 + 14, cx + 40, by0 + 90], 180, 360, fill=hair)
        d.rectangle([cx - 10, by0 + 108, cx + 10, by0 + 130], fill=skin)
    elif kind == 1:                                         # landscape
        d.rectangle([bx0, by0, bx1, by1], fill=(150, 200, 230))
        d.ellipse([bx1 - 70, by0 + 12, bx1 - 24, by0 + 58], fill=(255, 226, 130))
        d.polygon([(bx0, by1), (bx0 + 70, by0 + 90), (bx0 + 140, by1)], fill=(70, 110, 80))
        d.polygon([(bx0 + 80, by1), (bx0 + 150, by0 + 70), (bx1, by1)], fill=(50, 90, 70))
        d.rectangle([bx0, by1 - 30, bx1, by1], fill=(40, 120, 150))
    elif kind == 2:                                         # ball on grass
        d.rectangle([bx0, by0, bx1, by1], fill=(54, 130, 66))
        for k in range(0, bx1 - bx0, 30):
            d.rectangle([bx0 + k, by0, bx0 + k + 15, by1], fill=(62, 146, 74))
        cx, cy = (bx0 + bx1) // 2, (by0 + by1) // 2
        d.ellipse([cx - 44, cy - 44, cx + 44, cy + 44], fill=(245, 245, 240), outline=(30, 30, 30), width=3)
        d.regular_polygon((cx, cy, 15), 5, fill=(30, 30, 30))
        for a in range(5):
            d.line([cx + 15 * math.cos(a * 1.2566), cy + 15 * math.sin(a * 1.2566), cx + 40 * math.cos(a * 1.2566), cy + 40 * math.sin(a * 1.2566)], fill=(30, 30, 30), width=3)
    elif kind == 3:                                         # house
        d.rectangle([bx0, by0, bx1, by1], fill=(170, 205, 225))
        d.rectangle([bx0 + 40, by0 + 80, bx1 - 40, by1 - 14], fill=(236, 224, 196))
        d.polygon([(bx0 + 28, by0 + 82), ((bx0 + bx1) // 2, by0 + 22), (bx1 - 28, by0 + 82)], fill=(160, 70, 50))
        d.rectangle([bx0 + 100, by0 + 120, bx0 + 130, by1 - 14], fill=(110, 70, 44))
        d.rectangle([bx0 + 56, by0 + 108, bx0 + 86, by0 + 136], fill=(120, 170, 200))
        d.rectangle([bx1 - 86, by0 + 108, bx1 - 56, by0 + 136], fill=(120, 170, 200))
        d.rectangle([bx0, by1 - 14, bx1, by1], fill=(86, 150, 80))
    elif kind == 4:                                         # food
        d.rectangle([bx0, by0, bx1, by1], fill=(120, 84, 56))
        cx, cy = (bx0 + bx1) // 2, (by0 + by1) // 2
        d.ellipse([cx - 68, cy - 68, cx + 68, cy + 68], fill=(240, 238, 230))
        d.ellipse([cx - 48, cy - 48, cx + 48, cy + 48], fill=(214, 150, 70))
        for _ in range(9):
            ax, ay = cx + rnd.randint(-34, 34), cy + rnd.randint(-34, 34)
            d.ellipse([ax - 8, ay - 8, ax + 8, ay + 8], fill=rnd.choice([(80, 150, 60), (190, 50, 40), (240, 220, 120)]))
    else:                                                   # abstract
        d.rectangle([bx0, by0, bx1, by1], fill=mix(bg, (255, 255, 255), .5))
        for _ in range(7):
            cx, cy, r = rnd.randint(bx0, bx1), rnd.randint(by0, by1), rnd.randint(18, 52)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=mix(PALETTE[rnd.randrange(24)], (255, 255, 255), .15))
    d.rectangle([bx0, by0, bx1, by1], outline=(250, 250, 245), width=2)
    # cover lines
    ty = by1 + 6
    for k in range(3):
        txt = rnd.choice(LINES)
        d.text((x0 + 16 + 1, ty + 1), txt, font=font(17), fill=(0, 0, 0))
        d.text((x0 + 16, ty), txt, font=font(17), fill=(255, 236, 120) if k % 2 == 0 else (255, 255, 255))
        ty += 20
    # barcode and price
    d.rectangle([x0 + CW - 74, y0 + CH - 44, x0 + CW - 12, y0 + CH - 10], fill=(250, 250, 248))
    xx = x0 + CW - 70
    while xx < x0 + CW - 16:
        d.line([(xx, y0 + CH - 40), (xx, y0 + CH - 14)], fill=(20, 20, 20), width=rnd.choice([1, 1, 2, 3]))
        xx += rnd.choice([3, 4, 5])
    d.text((x0 + 16, y0 + CH - 30), 'R$ %d,90' % rnd.randint(8, 29), font=font(18), fill=(250, 250, 245))


def draw_postcard(im, k):
    rnd = random.Random(500 + k)
    x, y = cell_xy(CELL_POST + k // 2)
    y += (k % 2) * 170
    d = ImageDraw.Draw(im)
    d.rectangle([x, y, x + CW - 1, y + 169], fill=(250, 248, 240))
    skies = [((120, 190, 235), (255, 255, 255)), ((250, 190, 120), (255, 230, 170)), ((40, 50, 100), (200, 120, 90)), ((150, 200, 225), (250, 250, 250))]
    top, bot = skies[k % 4]
    for yy in range(8, 100):
        d.line([(x + 8, y + yy), (x + CW - 9, y + yy)], fill=mix(top, bot, yy / 100))
    d.rectangle([x + 8, y + 98, x + CW - 9, y + 124], fill=(30 + rnd.randint(0, 20), 130 + rnd.randint(0, 30), 165))
    d.rectangle([x + 8, y + 124, x + CW - 9, y + 160], fill=(232, 206, 150))
    sx = rnd.randint(40, 210)
    d.ellipse([sx - 14, y + 30, sx + 14, y + 58], fill=(255, 232, 130))
    if k % 3 == 0:
        px = rnd.randint(50, 200)
        d.line([px, y + 150, px + 10, y + 70], fill=(110, 75, 40), width=6)
        for a in range(-60, 61, 30):
            d.line([px + 10, y + 70, px + 10 + a, y + 60 + abs(a) // 3], fill=(40, 120, 50), width=5)
    elif k % 3 == 1:
        d.polygon([(x + 90, y + 110), (x + 150, y + 112), (x + 135, y + 124), (x + 100, y + 124)], fill=(150, 60, 50))
        d.polygon([(x + 120, y + 108), (x + 120, y + 70), (x + 148, y + 108)], fill=(245, 245, 240))
    else:
        d.polygon([(x + 8, y + 124), (x + 70, y + 84), (x + 140, y + 124)], fill=(80, 120, 90))
        d.polygon([(x + 100, y + 124), (x + 170, y + 78), (x + CW - 9, y + 124)], fill=(66, 100, 80))


def draw_gum(im, k):
    x, y = cell_xy(CELL_GUM + k)
    d = ImageDraw.Draw(im)
    cols = [((60, 170, 110), (240, 250, 245)), ((200, 50, 60), (250, 230, 230)), ((60, 120, 200), (235, 240, 250)), ((240, 190, 50), (80, 60, 30))][k]
    d.rectangle([x, y, x + CW - 1, y + CH - 1], fill=cols[0])
    d.polygon([(x, y + 130), (x + CW, y + 70), (x + CW, y + 220), (x, y + 280)], fill=cols[1])
    d.text((x + CW / 2, y + 150), ['MINT', 'MORANGO', 'ICE', 'TUTTI'][k], font=font(42), fill=cols[0], anchor='mm')
    d.ellipse([x + 70, y + 20, x + 190, y + 90], fill=mix(cols[0], (255, 255, 255), .4))


def atlas_png(path):
    im = Image.new('RGB', (ATLAS, ATLAS), (236, 232, 220))
    for i in range(24):
        draw_cover(im, i)
    for k in range(12):
        draw_postcard(im, k)
    for k in range(4):
        draw_gum(im, k)
    rnd = np.random.default_rng(7)
    d = ImageDraw.Draw(im)
    x, y = cell_xy(CELL_EDGE)                              # paper edge: many fine cream/grey lines
    d.rectangle([x, y, x + CW, y + CH], fill=(238, 233, 218))
    for yy in range(y, y + CH, 3):
        g = int(rnd.integers(205, 240))
        d.line([(x, yy), (x + CW, yy)], fill=(g, g - 3, g - 14))
    x, y = cell_xy(CELL_BACK)                               # back cover: pale with faint text lines
    d.rectangle([x, y, x + CW, y + CH], fill=(232, 228, 216))
    for yy in range(y + 30, y + CH - 30, 11):
        d.line([(x + 24, yy), (x + 24 + int(rnd.integers(90, 200)), yy)], fill=(190, 186, 176), width=3)
    im.save(path)


def news_png(path):
    W, H = 2048, 1024
    im = Image.new('RGB', (W, H), (236, 230, 210))
    d = ImageDraw.Draw(im)
    heads = [('O MAREIRO', 'MAR AGITADO\nNO LITORAL'), ('A GAZETA', 'FESTA LOTA\nO PÍER')]
    rnd = random.Random(11)
    for v in range(2):
        ox, oy, w, h = v * 1024, 0, 1024, 752
        d.rectangle([ox, oy, ox + w, oy + h], fill=(234, 228, 208))
        d.text((ox + w / 2, oy + 22), heads[v][0], font=font(118, 'georgiab.ttf'), fill=(28, 28, 28), anchor='ma')
        d.line([(ox + 30, oy + 160), (ox + w - 30, oy + 160)], fill=(28, 28, 28), width=6)
        d.text((ox + 40, oy + 170), 'EDIÇÃO DE SÁBADO  -  R$ 4,50', font=font(26), fill=(60, 60, 60))
        d.line([(ox + 30, oy + 208), (ox + w - 30, oy + 208)], fill=(28, 28, 28), width=2)
        d.multiline_text((ox + 40, oy + 222), heads[v][1], font=font(78, 'timesbd.ttf'), fill=(20, 20, 20), spacing=4)
        px0, py0, px1, py1 = ox + 40, oy + 410, ox + 470, oy + 700           # photo block
        for yy in range(py0, py1):
            g = int(90 + 80 * (1 - (yy - py0) / (py1 - py0)))
            d.line([(px0, yy), (px1, yy)], fill=(g, g, g))
        d.ellipse([px0 + 150, py0 + 40, px0 + 290, py0 + 180], fill=(70, 70, 70))
        d.rectangle([px0 + 110, py0 + 160, px0 + 330, py1], fill=(55, 55, 55))
        d.rectangle([px0, py1 + 2, px1, py1 + 14], fill=(120, 120, 120))
        for col in range(3):                                                 # text columns
            cx = ox + 500 + col * 170 if col < 3 else 0
            for ly in range(oy + 222, oy + 730, 15):
                if rnd.random() < .08:
                    continue
                d.line([(cx, ly), (cx + rnd.randint(110, 150), ly)], fill=(96, 94, 88), width=6)
        for ly in range(py1 + 24, oy + 735, 15):
            d.line([(px0, ly), (px0 + rnd.randint(260, 430), ly)], fill=(96, 94, 88), width=6)
    arr = np.asarray(im).astype(np.float32)
    n = np.random.default_rng(3).normal(0, 4, arr.shape[:2])[..., None]
    arr = np.clip(arr * np.array([1.0, .98, .9]) + n, 0, 255)
    im = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(im)
    for yy in range(760, H, 3):                                               # paper edge: stacked sheets
        g = int(np.random.default_rng(yy).integers(196, 238))
        d.line([(0, yy), (W, yy)], fill=(g, g - 4, g - 18))
    im.save(path)


def canvas_png(path):
    n = 512
    img = np.zeros((n, n, 3), np.float32)
    cream, red = np.array([214, 206, 184], np.float32), np.array([112, 62, 56], np.float32)
    stripe = (np.arange(n) // 64) % 2
    img[:] = np.where(stripe[None, :, None] == 0, cream, red)
    yy, xx = np.mgrid[0:n, 0:n]
    weave = 1 + .045 * np.sin(xx * 1.6) * np.sin(yy * 1.6)
    noise = np.random.default_rng(5).normal(0, .025, (n, n))
    img *= (weave + noise)[..., None]
    img *= (.92 + .08 * np.linspace(1, 0, n))[:, None, None]                  # soft dirt toward the hem
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path)


# ------------------------------------------------------------------ accumulated small geometry (magazines, papers, rivets)
class Acc:
    def __init__(self):
        self.bm = {}

    def get(self, name):
        if name not in self.bm:
            bm = bmesh.new()
            bm.loops.layers.uv.verify()
            self.bm[name] = bm
        return self.bm[name]


ACC = Acc()


def face(bm, items):
    """items = [(Vector or BMVert, (u, v)), ...] -> one face with explicit UVs."""
    uvl = bm.loops.layers.uv.active
    vs = [it[0] if hasattr(it[0], 'co') else bm.verts.new(it[0]) for it in items]
    try:
        f = bm.faces.new(vs)
    except ValueError:
        return None
    for lp, it in zip(f.loops, items):
        lp[uvl].uv = it[1]
    return f


def mag(M, cell, W=.21, H=.28, T=.004, bow=.005, nu=3, nv=4, rect=None):
    """Magazine / card: slightly bowed sheet with thickness. Local: x width, y thickness (front at y=0, normal -y), z up."""
    bm = ACC.get('mags')
    uvl = bm.loops.layers.uv.active
    u0, v0, u1, v1 = rect or cell_uv(cell)
    bu0, bv0, bu1, bv1 = cell_uv(CELL_BACK)
    eu, ev = (cell_uv(CELL_EDGE)[0] + cell_uv(CELL_EDGE)[2]) / 2, (cell_uv(CELL_EDGE)[1] + cell_uv(CELL_EDGE)[3]) / 2
    fr, bk = [], []
    for j in range(nv + 1):
        s = j / nv
        rf, rb = [], []
        for i in range(nu + 1):
            t = i / nu
            y = -bow * math.sin(math.pi * s) * (1 - .5 * (2 * t - 1) ** 2)
            rf.append(bm.verts.new(M @ Vector(((t - .5) * W, y, H * s))))
            rb.append(bm.verts.new(M @ Vector(((t - .5) * W, y + T, H * s))))
        fr.append(rf)
        bk.append(rb)
    for j in range(nv):
        for i in range(nu):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            f = bm.faces.new([fr[b][a] for a, b in q])
            for lp, (a, b) in zip(f.loops, q):
                lp[uvl].uv = (u0 + (u1 - u0) * a / nu, v0 + (v1 - v0) * b / nv)
            f = bm.faces.new([bk[b][a] for a, b in reversed(q)])
            for lp, (a, b) in zip(f.loops, reversed(q)):
                lp[uvl].uv = (bu0 + (bu1 - bu0) * a / nu, bv0 + (bv1 - bv0) * b / nv)

    def edge(a, b, c, d):
        f = bm.faces.new([a, b, c, d])
        for lp in f.loops:
            lp[uvl].uv = (eu, ev)
    for i in range(nu):
        edge(fr[0][i], bk[0][i], bk[0][i + 1], fr[0][i + 1])
        edge(fr[nv][i], fr[nv][i + 1], bk[nv][i + 1], bk[nv][i])
    for j in range(nv):
        edge(fr[j][0], fr[j + 1][0], bk[j + 1][0], bk[j][0])
        edge(fr[j][nu], bk[j][nu], bk[j + 1][nu], fr[j + 1][nu])


def mag_frame(pos, face_dir, tilt_deg=0.0, yaw_deg=0.0):
    """Matrix for a mag whose front faces face_dir (horizontal), bottom-centre at pos, leaning back by tilt."""
    f = Vector(face_dir).normalized()
    y = -f
    z = Vector((0, 0, 1))
    x = y.cross(z)
    base = Matrix((x, y, z)).transposed().to_4x4()
    base.translation = Vector(pos)
    return base @ Euler((-math.radians(tilt_deg), 0, math.radians(yaw_deg)), 'XYZ').to_matrix().to_4x4()


def ubox(name_acc, M, size, rect_top, rect_side, rect_front=None):
    """Closed box (centre-based, local transform M) with explicit UV rects for the top face and the four sides."""
    bm = ACC.get(name_acc)
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    v = [bm.verts.new(M @ Vector(c)) for c in ((-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
                                              (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz))]
    uvl = bm.loops.layers.uv.active

    def quad(idx, rect):
        f = bm.faces.new([v[k] for k in idx])
        r = rect
        for lp, (a, b) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            lp[uvl].uv = (r[0] + (r[2] - r[0]) * a, r[1] + (r[3] - r[1]) * b)
    quad((4, 5, 6, 7), rect_top)
    quad((0, 3, 2, 1), rect_side)
    quad((0, 1, 5, 4), rect_front or rect_side)
    for idx in ((2, 3, 7, 6), (3, 0, 4, 7), (1, 2, 6, 5)):
        quad(idx, rect_side)


def rivet(p, n, r=.0075):
    bm = ACC.get('paint')
    uvl = bm.loops.layers.uv.active
    p, n = Vector(p), Vector(n).normalized()
    t = n.cross(Vector((0, 0, 1)))
    if t.length < .1:
        t = n.cross(Vector((1, 0, 0)))
    t.normalize()
    b = n.cross(t)
    ring = lambda rr, h: [bm.verts.new(p + n * h + (t * math.cos(a) + b * math.sin(a)) * rr) for a in [2 * math.pi * k / 8 for k in range(8)]]
    r0, r1, apex = ring(r, 0), ring(r * .74, r * .5), bm.verts.new(p + n * r * .72)
    for i in range(8):
        j = (i + 1) % 8
        for vs in ((r0[i], r0[j], r1[j], r1[i]), (r1[i], r1[j], apex)):
            f = bm.faces.new(vs)
            for lp in f.loops:
                lp[uvl].uv = (.5, .5)


# ------------------------------------------------------------------ structural helpers
def slab(name, O, U, N, W, z0, z1, t, mats, pitch=.12, rd=RIB, ribs=True, tile=1.4):
    """Panel with stamped vertical ribs on the outer face (+N), flat inner face. Closed solid, mats = (outer, inner)."""
    O, U, N = Vector(O), Vector(U).normalized(), Vector(N).normalized()
    Zh = Vector((0, 0, 1))
    if ribs:
        n = int((W - .08) / pitch)
        m = (W - n * pitch) / 2
        us, ds = [0.0, m], [0.0, 0.0]
        for k in range(n):
            u0 = m + k * pitch
            us += [u0 + .045, u0 + .06, u0 + .105, u0 + .12]
            ds += [0.0, rd, rd, 0.0]
        us.append(W)
        ds.append(0.0)
        pad = min(.10, (z1 - z0) / 4)
        zs = [z0, z0 + pad, z0 + pad + .035, z1 - pad - .035, z1 - pad, z1]
        env = [0, 0, 1, 1, 0, 0]
    else:
        us, ds, zs, env = [0.0, W], [0.0, 0.0], [z0, z1], [0, 0]
    bm = bmesh.new()
    o = [[bm.verts.new(O + us[i] * U + ds[i] * env[j] * N + zs[j] * Zh) for j in range(len(zs))] for i in range(len(us))]
    ii = [[bm.verts.new(O + us[i] * U - t * N + zs[j] * Zh) for j in range(len(zs))] for i in range(len(us))]
    nj = len(zs) - 1
    fo = []
    for i in range(len(us) - 1):
        for j in range(nj):
            fo.append((bm.faces.new((o[i][j], o[i + 1][j], o[i + 1][j + 1], o[i][j + 1])), 0))
            fo.append((bm.faces.new((ii[i][j], ii[i][j + 1], ii[i + 1][j + 1], ii[i + 1][j])), 1))
    last = len(us) - 1
    for j in range(nj):
        fo.append((bm.faces.new((o[0][j], o[0][j + 1], ii[0][j + 1], ii[0][j])), 0))
        fo.append((bm.faces.new((o[last][j + 1], o[last][j], ii[last][j], ii[last][j + 1])), 0))
    for i in range(len(us) - 1):
        fo.append((bm.faces.new((o[i][0], ii[i][0], ii[i + 1][0], o[i + 1][0])), 0))
        fo.append((bm.faces.new((o[i + 1][nj], ii[i + 1][nj], ii[i][nj], o[i][nj])), 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    box_uv(bm, tile)
    for f, k in fo:
        f.material_index = k
    ob = mesh_obj(name, bm)
    for m_ in mats:
        ob.data.materials.append(m_)
    return ob


def prism_x(name, poly, x0, x1, mat, uv=1.0, smooth=False):
    """Solid extruded along X from a closed polygon given as (y, z) points."""
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for y, z in poly]
    b = [bm.verts.new((x1, y, z)) for y, z in poly]
    n = len(poly)
    for i in range(n):
        bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    ob = mesh_obj(name, bm)
    return finish(ob, mat, uv, 0, smooth=smooth)


def fbox(name, size, centre, mat, xaxis, zaxis=(0, 0, 1), bevel=.004, uv=1.0):
    x, z = Vector(xaxis).normalized(), Vector(zaxis).normalized()
    y = z.cross(x)
    eu = Matrix((x, y, z)).transposed().to_euler()
    return box(name, size, tuple(centre), mat, rot=tuple(eu), bevel=bevel, uv=uv)


def plain(name, colour, rough=.6, metal=0.0, glow=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*colour, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if glow:
        p.inputs['Emission Color'].default_value = (*glow, 1)
        p.inputs['Emission Strength'].default_value = .9
    return m


def image_mat(name, path, rough=.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    t = m.node_tree.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(str(path))
    p = m.node_tree.nodes['Principled BSDF']
    m.node_tree.links.new(t.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    return m


# ------------------------------------------------------------------ the model
def build():
    reset()
    OUT.mkdir(parents=True, exist_ok=True)
    atlas_png(OUT / f'{SLUG}_atlas.png')
    news_png(OUT / f'{SLUG}_news.png')
    canvas_png(OUT / f'{SLUG}_canvas.png')
    paint = material('paint', 'distressed_painted_planks', tint=(.33, .43, .37), rough=.55, out=OUT)
    wood = material('wood', 'teak_veneer', tint=(.42, .26, .15), rough=.5, out=OUT)
    steel = plain('steel', (.10, .13, .12), .5)
    inner = plain('inner', (.80, .78, .68), .8)
    glow = plain('glow', (1, .9, .65), .3, glow=(1, .78, .45))
    mags_m = image_mat('mags', OUT / f'{SLUG}_atlas.png', .55)
    news_m = image_mat('news', OUT / f'{SLUG}_news.png', .9)
    canvas = image_mat('canvas', OUT / f'{SLUG}_canvas.png', .85)
    rnd = random.Random(21)

    # ---- plinth and corner angles
    box('plinth', (2.24, 1.64, Z0), (0, 0, Z0 / 2), steel, bevel=.012, uv=1.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f'angle{sx}{sy}', (.05, .05, WALL_TOP - Z0), (sx * (HW - .005), sy * (HD - .005), (WALL_TOP + Z0) / 2), steel, bevel=.008)

    # ---- ribbed walls (outer paint, inner cream)
    slab('wall_back', (HW - .02, HD, 0), (-1, 0, 0), (0, 1, 0), 2 * HW - .04, Z0, WALL_TOP, WALL_T, (paint, inner))
    slab('wall_right', (HW, -HD + .02, 0), (0, 1, 0), (1, 0, 0), 2 * HD - .04, Z0, WALL_TOP, WALL_T, (paint, inner))
    slab('wall_left', (-HW, HD - .02, 0), (0, -1, 0), (-1, 0, 0), 2 * HD - .04, Z0, WALL_TOP, WALL_T, (paint, inner))
    slab('front_lower', (-HW + .12, -HD, 0), (1, 0, 0), (0, -1, 0), 2 * HW - .24, Z0, ZC, WALL_T, (paint, inner))
    for sx in (-1, 1):                                       # front posts
        box(f'post{sx}', (.12, .12, 2.21 - Z0), (sx * (HW - .06), -HD - .005, (2.21 + Z0) / 2), paint, bevel=.01, uv=1.4)
        for z in np.arange(.3, 2.15, .22):
            rivet((sx * (HW - .06), -HD - .065, z), (0, -1, 0))
    for sx in (-1, 1):                                       # rivets along the rear/side corner angles
        for sy in (-1, 1):
            for z in np.arange(.3, 2.2, .26):
                rivet((sx * (HW + .026), sy * (HD - .02), z), (1 if sx > 0 else -1, 0, 0))

    # ---- roof: slab with slope, skirt all round, seams, gutter, downspout, vent
    roof_f, roof_b = 2.40, 2.33
    ang = math.atan2(roof_f - roof_b, 1.72)
    box('roof', (2.30, 1.74, .045), (0, .04, (roof_f + roof_b) / 2 - .022), paint, rot=(-ang, 0, 0), bevel=.01, uv=1.4)
    for sx in (-1, 1):
        prism_x(f'skirt_s{sx}', [(-.84, 2.20), (-.84, roof_f - .02), (.88, roof_b - .02), (.88, 2.20)], sx * 1.135 - .008, sx * 1.135 + .008, paint, 1.4)
    box('skirt_back', (2.30, .016, .15), (0, .88, 2.26), paint, bevel=.005, uv=1.4)
    for k in range(-4, 5):                                   # standing seams on the roof
        zc = roof_f - (k * 0 + 0) * 0
        y0, y1 = -.74, .80
        zz0 = roof_f + .022 - (roof_f - roof_b) * ((y0 + .84) / 1.72)
        zz1 = roof_f + .022 - (roof_f - roof_b) * ((y1 + .84) / 1.72)
        prism_x(f'seam{k}', [(y0, zz0 - .01), (y0, zz0 + .016), (y1, zz1 + .016), (y1, zz1 - .01)], k * .25 - .012, k * .25 + .012, paint, 1.4)
    gp = [(.935 + .04 * math.cos(math.radians(a)), 2.215 + .04 * math.sin(math.radians(a))) for a in range(180, 361, 15)]
    gp += [(.935 + .036 * math.cos(math.radians(a)), 2.215 + .036 * math.sin(math.radians(a))) for a in range(360, 179, -15)]
    prism_x('gutter', gp, -1.14, 1.14, steel, 1.0, smooth=True)
    tube('downspout', (1.0, .955, 2.2), (1.0, .955, .25), .02, steel, sides=14)
    for z in (2.0, 1.4, .8, .35):
        tube(f'clamp{z}', (1.0, .955, z), (1.0, .955, z + .03), .026, steel, sides=14)
        box(f'clampstrap{z}', (.02, .08, .03), (1.0, .915, z + .015), steel, bevel=.004)
    tube('spout_foot', (1.0, .955, .25), (1.0, 1.0, .2), .02, steel, sides=14)
    lathe('roof_vent', [(.0, 0), (.09, 0), (.095, .02), (.07, .05), (.02, .075), (.0, .08)], (-.6, .3, 2.37), steel, sides=20)

    # ---- fascia (plain sign face, no text), roll-up shutter box, curtain, guides
    box('fascia', (2.28, .07, .32), (0, -.84, 2.37), steel, bevel=.012, uv=1.0)
    box('fascia_cap', (2.30, .09, .02), (0, -.835, 2.535), paint, bevel=.006, uv=1.4)
    box('fascia_foot', (2.30, .09, .02), (0, -.835, 2.205), paint, bevel=.006, uv=1.4)
    for sx in (-1, 1):
        for z in (2.255, 2.485):
            rivet((sx * 1.08, -.875, z), (0, -1, 0))
    box('roller_box', (2.0 - .04, .2, .17), (0, -.70, 2.125), paint, bevel=.012, uv=1.4)
    lam = []
    for k in range(0, 31):
        z = 2.04 - k * .004
        lam.append((-.775 - .006 * math.sin(2 * math.pi * (2.04 - z) / .036), z))
    poly = lam + [(y + .006, z) for y, z in reversed(lam)]
    prism_x('shutter_curtain', poly, -.97, .97, paint, 1.4)
    box('shutter_bar', (1.96, .045, .03), (0, -.775, 1.918), steel, bevel=.008)
    for sx in (-1, 1):
        box(f'guide{sx}', (.035, .06, 2.04 - ZCT), (sx * .98, -.775, (2.04 + ZCT) / 2), steel, bevel=.006)
    box('shutter_handle', (.12, .02, .02), (.3, -.805, 1.918), steel, bevel=.004)

    # ---- counter
    box('counter', (2.14, .38, .05), (0, -.77, ZC + .025), wood, bevel=.01, uv=1.2)
    box('counter_trim', (2.14, .016, .06), (0, -.964, ZC + .02), steel, bevel=.004)
    for sx in (-1, 1):
        box(f'counter_leg{sx}', (.05, .3, ZC - Z0), (sx * 1.0, -.76, (ZC + Z0) / 2), steel, bevel=.006)

    # ---- tilted magazine rack under the counter
    B = Vector((0, -.99, .18))
    T = Vector((0, -.82, .88))
    L = (T - B).length
    Tg = (T - B).normalized()
    alpha = math.atan2(Tg.y, Tg.z)
    Nb = Vector((0, -math.cos(alpha), math.sin(alpha)))
    rack_pt = lambda s, off: B + Tg * s + Nb * off
    box('rack_board', (1.92, .014, L), tuple(rack_pt(L / 2, -.007)), paint, rot=(-alpha, 0, 0), bevel=.004, uv=1.4)
    for s in (.0, .335):
        box(f'rack_lip{s}', (1.92, .036, .014), tuple(rack_pt(s + .004, .012)), steel, rot=(-alpha, 0, 0), bevel=.003)
    for sx in (-1, 1):
        prism_x(f'rack_cheek{sx}', [(-.99, .18), (-.99, .2), (-.82, .88), (-.815, .88), (-.815, .18)], sx * .975 - .01, sx * .975 + .01, paint, 1.4)
    cells = list(range(24))
    rnd.shuffle(cells)
    ci = 0
    for row, s0 in enumerate((.014, .349)):
        for k in range(8):
            cx = -.80 + k * .228 + rnd.uniform(-.006, .006)
            base = rack_pt(s0 + .004, .0065)
            base.x = cx
            mag(mag_frame(base, (0, -math.cos(alpha), 0), math.degrees(alpha) + rnd.uniform(-1.2, 1.2), rnd.uniform(-2, 2)), cells[ci % 24])
            ci += 1

    # ---- interior: shelves, dividers, magazines
    for z in (1.12, 1.42, 1.72):
        box(f'shelf{z}', (2.08, .21, .02), (0, .655, z - .01), wood, bevel=.004, uv=1.2)
        box(f'shelf_lip{z}', (2.08, .012, .035), (0, .555, z + .004), steel, bevel=.003)
    for sx in (-1, 1):
        box(f'divider{sx}', (.014, .21, .93), (sx * .345, .655, 1.58), wood, bevel=.003, uv=1.2)
    bays = [(-1.04, -.352), (-.338, .338), (.352, 1.04)]
    for z in (1.12, 1.42, 1.72):
        for (a, b) in bays:
            n = int((b - a - .04) // .225)
            for k in range(n):
                cx = (a + b) / 2 + (k - (n - 1) / 2) * .225 + rnd.uniform(-.008, .008)
                mag(mag_frame((cx, .655, z + .005), (0, -1, 0), 15 + rnd.uniform(-2, 2), rnd.uniform(-3, 3)), cells[ci % 24])
                ci += 1

    # ---- open side doors with magazines on the inner face
    leaf_w, lz0, lz1, lt = .5, .97, 1.90, .035
    for sx in (1, -1):
        ang_l = math.radians(105)
        Ud = Vector((sx * math.cos(math.pi - ang_l) * -1 * -1, -math.sin(ang_l), 0))
        Ud = Vector((-sx * math.cos(ang_l) * -1, -math.sin(ang_l), 0))
        Ud = Vector((sx * -math.cos(ang_l), -math.sin(ang_l), 0))        # leaves point forward and slightly outward
        Nout = Vector((0, 0, 1)).cross(Ud) * -sx                          # outward normal of the leaf
        if Nout.x * sx < 0:
            Nout = -Nout
        Oh = Vector((sx * 1.0, -.835, 0))
        slab(f'leaf{sx}', Oh, Ud, Nout, leaf_w, lz0, lz1, lt, (paint, inner), pitch=.12, rd=.009)
        xa = Nout.cross(Vector((0, 0, 1)))
        for z in (lz0 + .015, lz1 - .015):                                # frame strips on the inner face
            fbox(f'leaf_rail{sx}{z}', (leaf_w, .012, .03), Oh + Ud * leaf_w / 2 - Nout * (lt + .006) + Vector((0, 0, z)), steel, xa if xa.dot(Ud) > 0 else -xa)
        for u in (.015, leaf_w - .015):
            fbox(f'leaf_stile{sx}{u}', (.03, .012, lz1 - lz0), Oh + Ud * u - Nout * (lt + .006) + Vector((0, 0, (lz0 + lz1) / 2)), steel, xa if xa.dot(Ud) > 0 else -xa)
        for z in (1.0, 1.31, 1.62):
            fbox(f'leaf_ledge{sx}{z}', (leaf_w - .06, .07, .012), Oh + Ud * leaf_w / 2 - Nout * (lt + .035) + Vector((0, 0, z)), steel, xa if xa.dot(Ud) > 0 else -xa, bevel=.003)
            for u in (.145, .355):
                th = 11.0
                d_off = lt + .004 + .004 + .28 * math.sin(math.radians(th))
                base = Oh + Ud * u - Nout * d_off + Vector((0, 0, z + .006))
                fdir = -Nout
                mag(mag_frame(base, (fdir.x, fdir.y, 0), th + rnd.uniform(-1, 1), rnd.uniform(-2, 2)), cells[ci % 24])
                ci += 1
        for z in (1.04, 1.45, 1.8):                                        # hinges
            tube(f'hinge{sx}{z}', (sx * 1.0, -.835, z), (sx * 1.0, -.835, z + .07), .014, steel, sides=12)
        for z in (lz0 + .03, lz1 - .03):
            rivet(Oh + Ud * (leaf_w - .03) + Vector((0, 0, z)) + Nout * .0, Nout)

    # ---- counter items: newspaper stacks, gum display, postcard spinner
    nb = news_m
    rt = px_uv(0, 0, 1024, 752, 2048)
    rt = (rt[0], 1 - 752 / 1024, rt[2], 1.0)                                # front page A1 region of the 2048 x 1024 sheet
    rect_pages = [(0.0, 1 - 752 / 1024, .5, 1.0), (.5, 1 - 752 / 1024, 1.0, 1.0)]
    rect_edge = (0.0, 0.0, 1.0, 1 - 760 / 1024)
    for (cx, cy, n, var, yaw) in ((-.62, -.77, 17, 0, 4), (-.18, -.76, 11, 1, -6)):
        for k in range(n):
            j = Vector((rnd.uniform(-.004, .004), rnd.uniform(-.004, .004), 0))
            M = Matrix.Translation((cx + j.x, cy + j.y, ZCT + .0035 + k * .0065)) @ Euler((0, 0, math.radians(yaw + rnd.uniform(-1.4, 1.4)))).to_matrix().to_4x4()
            ubox('news', M, (.38, .27, .006), rect_pages[var if k >= n - 1 else rnd.randrange(2)], rect_edge)
        # string tie around the stack
        for off in (-.09, .09):
            M = Matrix.Translation((cx + off, cy, ZCT + .0065 * n / 2 + .003)) @ Euler((0, 0, math.radians(yaw))).to_matrix().to_4x4()
            ubox('news', M, (.004, .272, .0065 * n + .004), rect_edge, rect_edge)
    gx, gy = .27, -.78                                                      # gum display
    box('gum_tray', (.23, .13, .03), (gx, gy, ZCT + .015), steel, bevel=.004)
    box('gum_header', (.23, .01, .1), (gx, gy + .06, ZCT + .08), steel, rot=(-.15, 0, 0), bevel=.003)
    for r_ in range(3):
        for c_ in range(7):
            k = (r_ + c_) % 4
            M = Matrix.Translation((gx - .092 + c_ * .0306, gy - .042 + r_ * .042, ZCT + .03 + .0375)) @ Euler((0, 0, math.radians(rnd.uniform(-5, 5)))).to_matrix().to_4x4()
            g = cell_uv(CELL_GUM + k)
            ubox('mags', M, (.028, .012, .075), cell_uv(CELL_EDGE), cell_uv(CELL_EDGE), g)
    px, py = .75, -.78                                                      # postcard spinner
    lathe('spinner_base', [(.0, 0), (.13, 0), (.135, .006), (.12, .018), (.03, .026), (.0, .03)], (px, py, ZCT), steel, sides=24)
    box('spinner_tower', (.11, .11, .5), (px, py, ZCT + .27), steel, bevel=.008)
    lathe('spinner_cap', [(.0, 0), (.07, 0), (.06, .02), (.012, .06), (.0, .075)], (px, py, ZCT + .52), steel, sides=16)
    for k_ in range(4):
        z = ZCT + .06 + k_ * .115
        for f_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            fx, fy = f_
            ledge_c = Vector((px + fx * .075, py + fy * .075, z + .0))
            fbox(f'sp_ledge{k_}{fx}{fy}', (.13, .05, .006), ledge_c, steel, (1, 0, 0) if fy else (0, 1, 0), bevel=.002)
            base = (px + fx * .092, py + fy * .092, z + .004)
            pk = (k_ * 4 + (fx + 2 * fy) % 4 + 12) % 12
            mag(mag_frame(base, (fx, fy, 0), 12 + rnd.uniform(-1, 1), rnd.uniform(-2, 2)), 0, W=.13, H=.09, T=.0015, bow=.002, nu=2, nv=2, rect=post_uv(pk))

    # ---- awning: canvas top, scalloped valance, tube frame, lamps
    ax0, ax1, ay0, ay1 = -1.14, 1.14, -.88, -1.50
    az0, az1 = 2.205, 2.08
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.verify()
    nxs, nys = 24, 4
    grid = []
    for j in range(nys + 1):
        s = j / nys
        row = []
        for i in range(nxs + 1):
            t = i / nxs
            x = ax0 + (ax1 - ax0) * t
            y = ay0 + (ay1 - ay0) * s
            z = az0 + (az1 - az0) * s - .014 * math.sin(math.pi * s)
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for j in range(nys):
        for i in range(nxs):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for lp in f.loops:
                lp[uvl].uv = (lp.vert.co.x / .46, lp.vert.co.y / .46)
    ob = mesh_obj('awning_top', bm)
    ob.data.materials.append(canvas)
    sol = ob.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = .006
    sol.offset = -1
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.verify()
    nsc = 40
    top, bot = [], []
    for i in range(nsc + 1):
        t = i / nsc
        x = ax0 + (ax1 - ax0) * t
        fsc = (t * 10) % 1.0                                                  # ten scallops
        hh = .07 + .055 * math.sqrt(max(0, 1 - (2 * fsc - 1) ** 2))
        top.append(bm.verts.new((x, ay1, az1 - .006 * 0)))
        bot.append(bm.verts.new((x, ay1 - .003, az1 - hh)))
    for i in range(nsc):
        f = bm.faces.new((top[i], top[i + 1], bot[i + 1], bot[i]))
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x / .46, lp.vert.co.z / .46)
    ob = mesh_obj('awning_valance', bm)
    ob.data.materials.append(canvas)
    sol = ob.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = .006
    sol.offset = 0
    tube('awning_front_bar', (ax0 + .02, ay1 + .004, az1 + .008), (ax1 - .02, ay1 + .004, az1 + .008), .013, steel, sides=12)
    for x in (-1.12, -.56, 0.0, .56, 1.12):
        tube(f'awning_arm{x}', (x, ay0 + .01, az0 - .012), (x, ay1 + .004, az1 + .008), .011, steel, sides=10)
        box(f'awning_bracket{x}', (.06, .02, .05), (x, ay0 + .015, az0 - .03), steel, bevel=.004)
    for x in (-.56, .56):
        box(f'lamp_plate{x}', (.06, .04, .012), (x, -.92, 2.19), steel, bevel=.003)
        tube(f'lamp_stem{x}', (x, -.92, 2.19), (x, -.92, 2.135), .006, steel, sides=8)
        lathe(f'lamp_cap{x}', [(.0005, 0), (.03, 0), (.032, .012), (.024, .02), (.0005, .02)], (x, -.92, 2.12), steel, sides=16)
        prof = [(math.sin(a) * .034, -math.cos(a) * .034) for a in [math.radians(k) for k in range(0, 181, 20)]]
        lathe(f'lamp_globe{x}', [(max(r, 0.0005), z) for r, z in prof], (x, -.92, 2.083), glow, sides=18)

    # ---- left wall louvers (ventilation)
    for k in range(8):
        box(f'louver{k}', (.03, .3, .014), (-HW - RIB - .015, .0, 1.1 + k * .045), steel, rot=(0, math.radians(-28), 0), bevel=.003)
    box('louver_frame_t', (.03, .34, .02), (-HW - RIB - .013, 0, 1.48), steel, bevel=.004)
    box('louver_frame_b', (.03, .34, .02), (-HW - RIB - .013, 0, 1.06), steel, bevel=.004)
    for sy in (-1, 1):
        box(f'louver_frame_s{sy}', (.03, .02, .44), (-HW - RIB - .013, sy * .16, 1.27), steel, bevel=.004)
    # right side hasp and padlock
    box('hasp', (.02, .07, .12), (HW + RIB + .01, -.5, 1.1), steel, bevel=.004)
    box('padlock', (.03, .04, .05), (HW + RIB + .03, -.5, 1.04), steel, bevel=.007)

    # ---- flush the accumulated geometry into objects
    for name, bm in ACC.bm.items():
        if name in ('mags', 'news'):
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        ob = mesh_obj(f'acc_{name}', bm)
        ob.data.materials.append({'mags': mags_m, 'news': news_m, 'paint': paint}[name])
        for p in ob.data.polygons:
            p.use_smooth = False


def main():
    build()
    for o in list(bpy.context.scene.objects):
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        for mod in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    tri = 0
    for o in objs:
        o.data.calc_loop_triangles()
        tri += len(o.data.loop_triangles)
    bpy.context.view_layer.objects.active = objs[0]
    for o in bpy.context.scene.objects:
        o.select_set(o.type == 'MESH')
    bpy.ops.object.join()
    bpy.context.active_object.name = SLUG
    ob = bpy.context.active_object
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    print('TRIS', tri, 'BOUNDS x', min(xs), max(xs), 'y', min(ys), max(ys), 'z', min(zs), max(zs), 'materials', [m.name for m in ob.data.materials])
    export(SLUG, 'Banca de jornal (bpy)')


if __name__ == '__main__':
    main()
