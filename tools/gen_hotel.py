"""v1.0 — fase final: Grand Hotel Maré Alta 5★. Modelos no Blender (bpy), malha detalhada:
  hotel_tower      prédio de 5 andares (32 x 13 m, 19 m): térreo com pele de vidro e colunas torneadas, 4 andares com 8 varandas cada
                   (laje em balanço, guarda-corpo de vidro com corrimão e montantes, porta de correr com vidro 'glow', brise de madeira,
                   floreira), faixas de laje, laterais com ripado, fundos com janelas, platibanda e casa de máquinas, marquise de entrada.
  hotel_restaurant pavilhão do restaurante 14 x 9 m: piso de pedra, 10 colunas, vigas, telhado de 4 águas com telhas e beiral, buffet.
  hotel_gym        academia: caixa de vidro 10 x 7 m (caixilhos, porta, platibanda) — os aparelhos vêm separados:
  gym_treadmill, gym_bike, gym_bench, gym_dumbbells
  water_slide      tobogã: torre de 6,5 m (4 pilares, plataforma com guarda-corpo, escada com corrimão) e calha em hélice
                   (seção em U, listras) até a borda da piscina, com pilares de apoio.
Frente = -Y do Blender (+Z no Godot). Base em z=0. Uso: python3 tools/gen_hotel.py [nome ...]"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_code_props import *
from gen_code_props import _torus, _wheel, _loft, _mesh_obj
import bpy, bmesh


def rbox(size, loc, m, rot, bevel=0.01):
    o = box(size, (0, 0, 0), m, bevel=bevel)
    o.location = loc
    o.rotation_euler = rot
    return o


def glass_mat(name="vidro", rgb=(0.7, 0.85, 0.95), alpha=0.35):
    g = mat(name, rgb, 0.05)
    g.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = alpha
    try:
        g.surface_render_method = "BLENDED"
    except Exception:
        g.blend_method = "BLEND"
    return g


def _col(parts, x, y, z0, h, r, m):
    """Coluna torneada: base com toro, fuste com leve êntase, capitel com ábaco."""
    parts.append(lathe([(0.0, 0.0), (r * 1.45, 0.0), (r * 1.45, 0.08), (r * 1.25, 0.12), (r * 1.18, 0.2), (r, 0.26),
                        (r * 1.03, h * 0.35), (r * 0.96, h - 0.3), (r * 1.15, h - 0.2), (r * 1.3, h - 0.12), (r * 1.45, h - 0.1),
                        (r * 1.45, h), (0.0, h)], m, loc=(x, y, z0), verts=28))


def hotel_tower():
    fresh()
    plaster = mat("reboco", (0.97, 0.96, 0.93), 0.75, tex("white_plaster_diff.jpg"))
    sand = mat("reboco_areia", (0.93, 0.85, 0.72), 0.75, tex("white_plaster_diff.jpg"))
    stone = mat("pedra", (0.85, 0.82, 0.76), 0.7, tex("light_stone_diff.jpg"))
    wood = mat("madeira", (0.62, 0.42, 0.26), 0.7, tex("oak_wood_planks_diff.jpg"))
    metal = mat("metal", (0.18, 0.19, 0.21), 0.4)
    glass = glass_mat("vidro", (0.6, 0.8, 0.92), 0.4)
    lobby = mat("glow_lobby", (0.95, 0.85, 0.6), 0.3)          # interior do lobby (acende à noite)
    room = mat("glow_quarto", (0.85, 0.82, 0.7), 0.3)          # cortina/interior dos quartos (acende à noite)
    plant = mat("planta", (0.25, 0.55, 0.25), 0.8)
    parts = [anchor(plaster)]
    W, D = 32.0, 13.0
    G = 4.5          # pé-direito do térreo
    F = 3.4          # andares
    N = 4            # andares de quartos
    top = G + N * F
    # embasamento de pedra
    parts.append(box((W + 0.6, D + 0.6, 0.45), (0, 0, 0.225), stone, bevel=0.04))
    # térreo: núcleo recuado + pele de vidro na frente com montantes
    parts.append(box((W - 0.4, D - 2.6, G), (0, 1.0, G / 2 + 0.45), sand, bevel=0.04))
    parts.append(box((W - 1.0, 0.05, G - 0.6), (0, -D / 2 + 1.35, (G - 0.6) / 2 + 0.5), lobby, bevel=0.0))
    parts.append(box((W - 0.9, 0.04, G - 0.5), (0, -D / 2 + 1.25, (G - 0.5) / 2 + 0.45), glass, bevel=0.0))
    for k in range(22):
        x = -W / 2 + 0.6 + k * (W - 1.2) / 21
        parts.append(box((0.08, 0.14, G - 0.5), (x, -D / 2 + 1.2, (G - 0.5) / 2 + 0.45), metal, bevel=0.01))
    parts.append(box((W - 0.9, 0.16, 0.1), (0, -D / 2 + 1.2, 2.9), metal, bevel=0.01))
    # colunas da galeria do térreo
    for k in range(9):
        x = -W / 2 + 1.0 + k * (W - 2.0) / 8
        _col(parts, x, -D / 2 + 0.35, 0.45, G - 0.05, 0.22, plaster)
    # lajes e faixas (cada andar), com pingadeira
    for f in range(N + 1):
        z = G + f * F + 0.45
        parts.append(box((W + 0.4, D + 0.4, 0.32), (0, 0, z), plaster, bevel=0.05))
        parts.append(box((W + 0.5, 0.08, 0.06), (0, -D / 2 - 0.22, z - 0.18), sand, bevel=0.01))
    # paredes dos andares: fundos com janelas, laterais com ripado de madeira
    for f in range(N):
        z0 = G + f * F + 0.61
        zc = z0 + (F - 0.32) / 2
        parts.append(box((W, 0.3, F - 0.32), (0, D / 2 - 0.15, zc), plaster, bevel=0.02))
        parts.append(box((W - 0.8, 0.3, F - 0.32), (0, -D / 2 + 1.0, zc), plaster, bevel=0.02))   # fachada dos quartos (recuada 1 m)
        for sx in (-1, 1):
            parts.append(box((0.3, D, F - 0.32), (sx * (W / 2 - 0.15), 0, zc), plaster, bevel=0.02))
            for k in range(14):
                y = -D / 2 + 1.6 + k * 0.72
                parts.append(box((0.06, 0.09, F - 0.5), (sx * (W / 2 + 0.03), y, zc), wood, bevel=0.01))
        for k in range(10):   # janelas dos fundos (corredor)
            x = -W / 2 + 2.0 + k * (W - 4.0) / 9
            parts.append(box((1.3, 0.06, 1.3), (x, D / 2 + 0.01, zc + 0.15), room, bevel=0.0))
            parts.append(box((1.45, 0.12, 0.08), (x, D / 2 + 0.03, zc + 0.85), metal, bevel=0.01))
            parts.append(box((1.45, 0.12, 0.08), (x, D / 2 + 0.03, zc - 0.55), metal, bevel=0.01))
            parts.append(box((1.6, 0.25, 0.07), (x, D / 2 + 0.1, zc - 0.62), plaster, bevel=0.01))   # peitoril
            for sx in (-0.69, 0.0, 0.69):
                parts.append(box((0.07, 0.12, 1.45), (x + sx, D / 2 + 0.03, zc + 0.15), metal, bevel=0.01))
        # varandas da frente
        for r in range(8):
            x = -W / 2 + 2.0 + r * 4.0
            fy = -D / 2 + 0.85
            # porta de correr: interior (glow), vidro, caixilho com 3 folhas
            parts.append(box((2.4, 0.05, 2.3), (x - 0.35, fy - 0.02, z0 + 1.15), room, bevel=0.0))
            parts.append(box((2.45, 0.03, 2.35), (x - 0.35, fy - 0.07, z0 + 1.17), glass, bevel=0.0))
            for dx in (-1.55, -0.75, 0.05, 0.85):
                parts.append(box((0.06, 0.1, 2.35), (x + dx, fy - 0.08, z0 + 1.17), metal, bevel=0.008))
            for dz in (0.02, 2.33):
                parts.append(box((2.5, 0.1, 0.06), (x - 0.35, fy - 0.08, z0 + dz), metal, bevel=0.008))
            # brise de madeira ao lado da porta
            for k in range(7):
                parts.append(box((0.1, 0.06, 2.6), (x + 1.15 + k * 0.12, fy - 0.1, z0 + 1.3), wood, bevel=0.01))
            # laje da varanda em balanço (1,6 m) com testeira
            parts.append(box((3.9, 1.9, 0.22), (x, -D / 2 - 0.15, z0 - 0.05), plaster, bevel=0.03))
            # aletas separando as varandas
            parts.append(box((0.18, 1.9, F - 0.3), (x + 2.0, -D / 2 - 0.15, zc), sand, bevel=0.03))
            # guarda-corpo de vidro: painéis, montantes e corrimão de madeira
            yy = -D / 2 - 1.0
            parts.append(box((3.6, 0.03, 0.95), (x, yy, z0 + 0.6), glass, bevel=0.0))
            for k in range(5):
                parts.append(box((0.05, 0.05, 1.05), (x - 1.8 + k * 0.9, yy - 0.02, z0 + 0.58), metal, bevel=0.01))
            parts.append(box((3.75, 0.1, 0.06), (x, yy - 0.01, z0 + 1.1), wood, bevel=0.015))
            # floreira com folhagem de folhas (lâminas), não bolas
            parts.append(box((0.9, 0.3, 0.32), (x + 1.2, yy + 0.25, z0 + 0.22), stone, bevel=0.02))
            rnd = random.Random(r * 13 + f)
            for q in range(9):
                a = rnd.uniform(0, 6.28)
                bm = bmesh.new()
                bm.loops.layers.uv.new("UVMap")
                L = rnd.uniform(0.28, 0.45)
                pts = []
                for t in range(7):
                    u = t / 6
                    w = 0.035 * math.sin(math.pi * u)
                    pts.append((u * L * 0.6, w, u * L - 0.2 * (u * L) ** 2 * 3))
                vs1 = [bm.verts.new((p[0], p[1], p[2])) for p in pts]
                vs2 = [bm.verts.new((p[0], -p[1], p[2])) for p in pts]
                for t in range(6):
                    f2 = [vs1[t], vs1[t + 1], vs2[t + 1], vs2[t]]
                    uniq = []
                    for v in f2:
                        if v not in uniq:
                            uniq.append(v)
                    if len(uniq) >= 3:
                        bm.faces.new(uniq)
                o = _mesh_obj(bm, "folha", [plant], 0.004, 0)
                o.location = (x + 1.2 + rnd.uniform(-0.35, 0.35), yy + 0.25 + rnd.uniform(-0.08, 0.08), z0 + 0.38)
                o.rotation_euler = (0, 0, a)
                parts.append(o)
    # platibanda, casa de máquinas e moldura do letreiro no topo
    zt = top + 0.61
    parts.append(box((W + 0.4, 0.25, 1.1), (0, -D / 2 - 0.08, zt + 0.55), plaster, bevel=0.03))
    parts.append(box((W + 0.4, 0.25, 1.1), (0, D / 2 + 0.08, zt + 0.55), plaster, bevel=0.03))
    for sx in (-1, 1):
        parts.append(box((0.25, D + 0.4, 1.1), (sx * (W / 2 + 0.08), 0, zt + 0.55), plaster, bevel=0.03))
    parts.append(box((8.0, 5.0, 2.6), (4.0, 2.0, zt + 1.3), sand, bevel=0.05))
    parts.append(box((8.4, 5.4, 0.18), (4.0, 2.0, zt + 2.7), plaster, bevel=0.03))
    parts.append(box((14.0, 0.3, 2.0), (0, -D / 2 + 0.6, zt + 2.0), wood, bevel=0.03))     # painel do letreiro (texto no Godot)
    for sx in (-6.5, 0.0, 6.5):
        parts.append(tube((sx, -D / 2 + 0.8, zt), (sx, -D / 2 + 0.8, zt + 1.2), 0.06, metal, verts=12))
    # marquise de entrada (porte-cochère) no centro da frente
    parts.append(box((10.0, 7.0, 0.45), (0, -D / 2 - 3.2, G + 0.2), plaster, bevel=0.06))
    parts.append(box((10.2, 7.2, 0.08), (0, -D / 2 - 3.2, G - 0.06), wood, bevel=0.02))
    for sx in (-4.4, 4.4):
        _col(parts, sx, -D / 2 - 6.0, 0.0, G - 0.03, 0.28, plaster)
    # degraus de entrada
    for k in range(3):
        parts.append(box((8.0 - k * 0.6, 0.45, 0.15), (0, -D / 2 + 0.4 - 0.45 * (2 - k) - 0.2, 0.075 + 0.15 * k), stone, bevel=0.02))
    join(parts, "hotel_tower")
    export("hotel_tower")


def hotel_restaurant():
    fresh()
    stone = mat("piso", (0.85, 0.8, 0.72), 0.7, tex("light_stone_diff.jpg"))
    plaster = mat("reboco", (0.97, 0.96, 0.93), 0.75, tex("white_plaster_diff.jpg"))
    wood = mat("madeira", (0.55, 0.36, 0.22), 0.7, tex("oak_wood_planks_diff.jpg"))
    tile = mat("telha", (0.75, 0.42, 0.3), 0.8, tex("clay_roof_tiles_02_diff.jpg"))
    steel = mat("inox", (0.8, 0.82, 0.84), 0.3)
    glass = glass_mat("vidro", (0.85, 0.95, 1.0), 0.3)
    foods = [mat("comida%d" % i, c, 0.6) for i, c in enumerate([(0.95, 0.75, 0.3), (0.85, 0.3, 0.2), (0.4, 0.7, 0.3), (0.98, 0.95, 0.85)])]
    parts = [anchor(stone)]
    W, D, H = 14.0, 9.0, 3.4
    parts.append(box((W + 0.6, D + 0.6, 0.35), (0, 0, 0.175), stone, bevel=0.03))
    for k in range(3):
        parts.append(box((3.0, 0.4, 0.12), (0, -D / 2 - 0.5 - 0.4 * (2 - k) + 0.4, 0.06 + 0.115 * k), stone, bevel=0.02))
    for i in range(5):
        x = -W / 2 + 0.4 + i * (W - 0.8) / 4
        for y in (-D / 2 + 0.4, D / 2 - 0.4):
            _col(parts, x, y, 0.35, H, 0.17, plaster)
    for y in (-D / 2 + 0.4, D / 2 - 0.4):
        parts.append(box((W, 0.3, 0.4), (0, y, H + 0.55), wood, bevel=0.03))
    for x in (-W / 2 + 0.4, W / 2 - 0.4):
        parts.append(box((0.3, D, 0.4), (x, 0, H + 0.55), wood, bevel=0.03))
    for k in range(8):
        x = -W / 2 + 1.2 + k * (W - 2.4) / 7
        parts.append(box((0.18, D - 0.4, 0.28), (x, 0, H + 0.85), wood, bevel=0.02))
    # telhado de 4 águas com telhas (faces texturizadas) e beiral de 0,8 m
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    e = 0.8
    z0 = H + 0.95
    zr = z0 + 2.4
    a = [bm.verts.new(p) for p in ((-W / 2 - e, -D / 2 - e, z0), (W / 2 + e, -D / 2 - e, z0), (W / 2 + e, D / 2 + e, z0), (-W / 2 - e, D / 2 + e, z0))]
    r1 = bm.verts.new((-W / 2 + D / 2, 0, zr))
    r2 = bm.verts.new((W / 2 - D / 2, 0, zr))
    for f in ((a[0], a[1], r2, r1), (a[1], a[2], r2), (a[2], a[3], r1, r2), (a[3], a[0], r1)):
        face = bm.faces.new(f)
        for lp in face.loops:
            lp[uvl].uv = (lp.vert.co.x * 0.4 + lp.vert.co.y * 0.0, lp.vert.co.z * 0.6 + lp.vert.co.y * 0.4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    parts.append(_mesh_obj(bm, "telhado", [tile], 0.12, 0))
    parts.append(tube((-W / 2 + D / 2, 0, zr + 0.08), (W / 2 - D / 2, 0, zr + 0.08), 0.12, tile, verts=14))   # cumeeira
    # forro de madeira sob o beiral (frente)
    parts.append(box((W + 2 * e, 0.8, 0.04), (0, -D / 2 - e / 2, z0 - 0.03), wood, bevel=0.01))
    # buffet no fundo: balcão, cubas, protetor de vidro
    parts.append(box((5.0, 0.9, 0.9), (0, D / 2 - 1.4, 0.8), wood, bevel=0.03))
    parts.append(box((5.1, 1.0, 0.05), (0, D / 2 - 1.4, 1.27), stone, bevel=0.01))
    for k in range(6):
        x = -2.0 + k * 0.8
        parts.append(box((0.6, 0.45, 0.1), (x, D / 2 - 1.4, 1.33), steel, bevel=0.02))
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        n = 10
        grid = [[bm.verts.new((x - 0.27 + 0.54 * i / n, D / 2 - 1.4 - 0.2 + 0.4 * j / n, 1.385 + 0.03 * math.sin(math.pi * i / n) * math.sin(math.pi * j / n) + 0.006 * math.sin(i * 2.1 + j * 1.3 + k))) for i in range(n + 1)] for j in range(n + 1)]
        for j in range(n):
            for i in range(n):
                bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
        parts.append(_mesh_obj(bm, "comida", [foods[k % 4]], 0.0, 0))
    o = rbox((5.0, 0.02, 0.45), (0, D / 2 - 1.75, 1.65), glass, (math.radians(-25), 0, 0), bevel=0.0)
    parts.append(o)
    for x in (-2.5, 2.5):
        parts.append(tube((x, D / 2 - 1.4, 1.3), (x, D / 2 - 1.8, 1.85), 0.015, steel, verts=8))
    join(parts, "hotel_restaurant")
    export("hotel_restaurant")


def hotel_gym():
    fresh()
    floor = mat("piso", (0.35, 0.36, 0.4), 0.8)
    rubber = mat("borracha", (0.2, 0.22, 0.25), 0.9)
    frame = mat("caixilho", (0.15, 0.16, 0.18), 0.4)
    glass = glass_mat("vidro", (0.65, 0.85, 0.95), 0.3)
    plaster = mat("reboco", (0.97, 0.96, 0.93), 0.75, tex("white_plaster_diff.jpg"))
    wood = mat("madeira", (0.62, 0.42, 0.26), 0.7, tex("oak_wood_planks_diff.jpg"))
    parts = [anchor(floor)]
    W, D, H = 10.0, 7.0, 3.5
    parts.append(box((W + 0.4, D + 0.4, 0.25), (0, 0, 0.125), plaster, bevel=0.03))
    parts.append(box((W - 0.2, D - 0.2, 0.03), (0, 0, 0.265), rubber, bevel=0.005))
    # parede de fundo maciça com ripado de madeira e espelho
    parts.append(box((W, 0.3, H), (0, D / 2 - 0.15, H / 2 + 0.25), plaster, bevel=0.02))
    for k in range(30):
        parts.append(box((0.08, 0.05, H - 0.4), (-W / 2 + 0.4 + k * 0.32, D / 2 - 0.33, H / 2 + 0.25), wood, bevel=0.008))
    parts.append(box((4.0, 0.02, 1.8), (-2.0, D / 2 - 0.37, 1.6), glass_mat("espelho", (0.85, 0.9, 0.95), 0.75), bevel=0.0))
    # 3 lados de vidro com caixilhos
    for side in ("front", "left", "right"):
        if side == "front":
            L, cx, cy, horiz = W, 0.0, -D / 2, True
        else:
            L, cx, cy, horiz = D, (-W / 2 if side == "left" else W / 2), 0.0, False
        nseg = int(L / 1.25)
        sz = (L, 0.03, H - 0.1) if horiz else (0.03, L, H - 0.1)
        parts.append(box(sz, (cx, cy, H / 2 + 0.25), glass, bevel=0.0))
        for k in range(nseg + 1):
            t = -L / 2 + L * k / nseg
            pos = (cx + t, cy, H / 2 + 0.25) if horiz else (cx, cy + t, H / 2 + 0.25)
            parts.append(box((0.07, 0.1, H) if horiz else (0.1, 0.07, H), pos, frame, bevel=0.008))
        for z in (0.3, 1.1, H + 0.2):
            parts.append(box((L, 0.1, 0.07) if horiz else (0.1, L, 0.07), (cx, cy, z), frame, bevel=0.008))
    # porta (folha com puxador) na frente
    parts.append(box((0.04, 0.05, 1.2), (0.55, -D / 2 - 0.06, 1.3), frame, bevel=0.01))
    # laje e platibanda
    parts.append(box((W + 0.6, D + 0.6, 0.3), (0, 0, H + 0.4), plaster, bevel=0.04))
    parts.append(box((W + 0.6, 0.15, 0.4), (0, -D / 2 - 0.22, H + 0.75), plaster, bevel=0.02))
    join(parts, "hotel_gym")
    export("hotel_gym")


def gym_treadmill():
    fresh()
    body = mat("corpo", (0.15, 0.16, 0.18), 0.4)
    belt = mat("esteira", (0.08, 0.08, 0.09), 0.9)
    alu = mat("aluminio", (0.75, 0.77, 0.8), 0.35)
    screen = mat("glow_tela", (0.3, 0.7, 1.0), 0.2)
    accent = mat("detalhe", (0.95, 0.35, 0.2), 0.5)
    parts = [anchor(body)]
    parts.append(box((0.8, 1.9, 0.16), (0, 0.1, 0.15), body, bevel=0.04))
    parts.append(box((0.52, 1.6, 0.03), (0, 0.15, 0.245), belt, bevel=0.01))
    for sx in (-0.33, 0.33):
        parts.append(box((0.12, 1.75, 0.05), (sx, 0.12, 0.25), alu, bevel=0.015))
    parts.append(lathe([(0.0, -0.3), (0.06, -0.3), (0.065, -0.27), (0.065, 0.27), (0.06, 0.3), (0.0, 0.3)], alu, loc=(0, -0.75, 0.16), verts=20))
    parts[-1].rotation_euler = (0, math.radians(90), 0)
    for sx in (-0.33, 0.33):
        parts.append(sweep([(sx, -0.65, 0.2), (sx, -0.78, 0.8), (sx, -0.82, 1.25)], 0.035, body, 12, "coluna"))
        parts.append(sweep([(sx, -0.82, 1.05), (sx, -0.55, 1.05), (sx, -0.3, 1.02)], 0.022, alu, 10, "corrimao"))
    parts.append(box((0.75, 0.25, 0.32), (0, -0.85, 1.35), body, bevel=0.05))
    o = rbox((0.45, 0.02, 0.2), (0, -0.74, 1.38), screen, (math.radians(-25), 0, 0), bevel=0.0)
    parts.append(o)
    parts.append(box((0.8, 0.03, 0.06), (0, -0.72, 1.18), accent, bevel=0.01))
    join(parts, "gym_treadmill")
    export("gym_treadmill")


def gym_bike():
    fresh()
    body = mat("corpo", (0.15, 0.16, 0.18), 0.4)
    alu = mat("aluminio", (0.75, 0.77, 0.8), 0.35)
    seat = mat("selim", (0.1, 0.1, 0.11), 0.6)
    accent = mat("detalhe", (0.95, 0.35, 0.2), 0.5)
    screen = mat("glow_tela", (0.3, 0.7, 1.0), 0.2)
    parts = [anchor(body)]
    for y in (-0.45, 0.45):
        parts.append(sweep([(-0.28, y, 0.04), (0, y, 0.07), (0.28, y, 0.04)], 0.035, body, 10, "pe"))
    parts.append(sweep([(0, 0.45, 0.07), (0, 0.2, 0.45), (0, 0.05, 0.75)], 0.045, body, 12, "quadro"))
    parts.append(sweep([(0, -0.45, 0.07), (0, -0.3, 0.6), (0, -0.38, 1.0)], 0.045, body, 12, "guidao_col"))
    parts.append(lathe([(0.0, -0.06), (0.24, -0.06), (0.26, -0.03), (0.26, 0.03), (0.24, 0.06), (0.0, 0.06)], accent, loc=(0, -0.15, 0.38), verts=36))
    parts[-1].rotation_euler = (0, math.radians(90), 0)
    for sx in (-1, 1):
        parts.append(tube((0, -0.05, 0.38), (sx * 0.12, -0.05 + 0.1 * sx, 0.38 - 0.15 * sx), 0.015, alu, verts=8))
        parts.append(box((0.1, 0.05, 0.03), (sx * 0.17, -0.05 + 0.1 * sx, 0.38 - 0.15 * sx), body, bevel=0.01))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    secs = [(-0.12 + 0.3 * i / 8, 0.05 + 0.08 * math.sin(math.pi * (0.2 + 0.8 * i / 8)) * (1.0 if i > 3 else 0.6), 0.035, 0.0) for i in range(9)]
    _loft(bm, uvl, secs, 16, True)
    o = _mesh_obj(bm, "selim", [seat], 0.0, 1)
    o.location = (0, 0.05, 0.8)
    o.rotation_euler = (0, 0, math.radians(90))
    parts.append(o)
    parts.append(sweep([(-0.25, -0.3, 1.02), (-0.2, -0.45, 1.05), (0.2, -0.45, 1.05), (0.25, -0.3, 1.02)], 0.018, alu, 10, "guidao"))
    o = rbox((0.22, 0.03, 0.14), (0, -0.42, 1.12), screen, (math.radians(-30), 0, 0), bevel=0.0)
    parts.append(o)
    join(parts, "gym_bike")
    export("gym_bike")


def _plate(parts, loc, r, m, axis_x=True):
    o = lathe([(0.025, -0.02), (r, -0.02), (r + 0.006, -0.012), (r + 0.006, 0.012), (r, 0.02), (0.025, 0.02), (0.025, 0.012), (r * 0.6, 0.008), (r * 0.6, -0.008), (0.025, -0.012)], m, loc=loc, verts=32)
    if axis_x:
        o.rotation_euler = (0, math.radians(90), 0)
    parts.append(o)


def gym_bench():
    """Supino: banco estofado, suportes da barra, barra com anilhas."""
    fresh()
    body = mat("corpo", (0.15, 0.16, 0.18), 0.4)
    pad = mat("estofado", (0.75, 0.15, 0.12), 0.6)
    chrome = mat("cromado", (0.82, 0.84, 0.86), 0.25)
    plate = mat("anilha", (0.1, 0.1, 0.11), 0.6)
    parts = [anchor(body)]
    parts.append(box((0.32, 1.25, 0.1), (0, 0.15, 0.45), pad, bevel=0.04))
    for y in (-0.3, 0.6):
        parts.append(sweep([(-0.22, y, 0.02), (0, y, 0.38), (0.22, y, 0.02)], 0.03, body, 10, "pe"))
    parts.append(tube((0, -0.3, 0.38), (0, 0.6, 0.38), 0.035, body, verts=12))
    for sx in (-0.5, 0.5):
        parts.append(tube((sx, -0.55, 0.0), (sx, -0.55, 1.15), 0.035, body, verts=12))
        parts.append(box((0.12, 0.3, 0.04), (sx, -0.55, 0.02), body, bevel=0.01))
        parts.append(sweep([(sx, -0.55, 1.02), (sx, -0.45, 1.0), (sx, -0.42, 1.06)], 0.02, chrome, 8, "gancho"))
    parts.append(tube((-1.05, -0.48, 1.04), (1.05, -0.48, 1.04), 0.014, chrome, verts=12))
    for sx in (-1, 1):
        for k in range(2):
            _plate(parts, (sx * (0.72 + k * 0.05), -0.48, 1.04), 0.22 - k * 0.04, plate)
        parts.append(lathe([(0.0, -0.03), (0.03, -0.03), (0.03, 0.03), (0.0, 0.03)], chrome, loc=(sx * 0.82, -0.48, 1.04), verts=16))
        parts[-1].rotation_euler = (0, math.radians(90), 0)
    join(parts, "gym_bench")
    export("gym_bench")


def gym_dumbbells():
    """Suporte de 2 andares com 6 pares de halteres (cabeças torneadas de 12 faces com borracha, pegada recartilhada)."""
    fresh()
    body = mat("corpo", (0.15, 0.16, 0.18), 0.4)
    head = mat("cabeca", (0.12, 0.12, 0.13), 0.6)
    chrome = mat("cromado", (0.82, 0.84, 0.86), 0.25)
    accent = mat("numero", (0.95, 0.75, 0.2), 0.5)
    parts = [anchor(body)]
    for sx in (-0.75, 0.75):
        parts.append(sweep([(sx, 0.25, 0.0), (sx, 0.18, 0.5), (sx, 0.1, 0.85)], 0.035, body, 10, "lado"))
        parts.append(sweep([(sx, -0.25, 0.0), (sx, -0.18, 0.4), (sx, -0.12, 0.55)], 0.035, body, 10, "lado2"))
        parts.append(box((0.08, 0.6, 0.04), (sx, 0, 0.02), body, bevel=0.01))
    for (z, y) in ((0.55, -0.12), (0.85, 0.1)):
        for yy in (y - 0.08, y + 0.08):
            parts.append(tube((-0.78, yy, z), (0.78, yy, z), 0.025, body, verts=10))
        for k in range(6 if z < 0.7 else 5):
            x = -0.62 + k * 0.25
            r = 0.05 + 0.006 * k
            for sx in (-0.09, 0.09):
                o = lathe([(0.0, -0.045), (r * 0.9, -0.045), (r, -0.035), (r, 0.035), (r * 0.9, 0.045), (0.0, 0.045)], head, loc=(x, y, z + r), verts=12)
                o.rotation_euler = (math.radians(90), 0, 0)
                o.location = (x, y + sx, z + r)
                parts.append(o)
                parts.append(_torus(r * 0.6, 0.006, (x, y + sx * 1.55, z + r), False, accent, 20, 6))
                parts[-1].rotation_euler = (math.radians(90), 0, 0)
            parts.append(tube((x, y - 0.05, z + r), (x, y + 0.05, z + r), 0.016, chrome, verts=12))
    join(parts, "gym_dumbbells")
    export("gym_dumbbells")


def water_slide():
    """Tobogã: torre de 6,5 m em (0,0) e calha helicoidal (2 voltas, raio 3 m) que termina na borda da piscina em +X (Blender),
    a 0,35 m de altura. A piscina fica do lado +X; a saída da calha está em x≈6,6, y≈0."""
    fresh()
    steel = mat("aco", (0.85, 0.87, 0.9), 0.35)
    tint = mat("tint_calha", (0.15, 0.55, 0.95), 0.25)
    stripe = mat("listra", (0.98, 0.85, 0.2), 0.3)
    deck = mat("plataforma", (0.6, 0.42, 0.28), 0.7, tex("oak_wood_planks_diff.jpg"))
    parts = [anchor(steel)]
    Ht = 6.5
    # 4 pilares, travamentos em X e plataforma
    P = 0.9
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(tube((sx * P, sy * P, 0.0), (sx * P, sy * P, Ht + 1.1), 0.07, steel, verts=16))
            parts.append(lathe([(0.0, 0.0), (0.2, 0.0), (0.2, 0.06), (0.09, 0.1), (0.0, 0.1)], steel, loc=(sx * P, sy * P, 0), verts=16))
    for z0, z1 in ((0.3, 2.3), (2.3, 4.3), (4.3, Ht)):
        for (a, b) in (((-P, -P), (P, -P)), ((P, -P), (P, P)), ((P, P), (-P, P)), ((-P, P), (-P, -P))):
            parts.append(tube((a[0], a[1], z0), (b[0], b[1], z1), 0.03, steel, verts=8))
            parts.append(tube((b[0], b[1], z0), (a[0], a[1], z1), 0.03, steel, verts=8))
    parts.append(box((2.2, 2.2, 0.12), (0, 0, Ht), deck, bevel=0.02))
    for (a, b) in (((-P, -P), (P, -P)), ((P, P), (-P, P)), ((-P, P), (-P, -P))):
        for z in (Ht + 0.55, Ht + 1.05):
            parts.append(tube((a[0], a[1], z), (b[0], b[1], z), 0.03, steel, verts=10))
    # cobertura (lona em 4 gomos) no topo
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    ap = bm.verts.new((0, 0, Ht + 2.1))
    cs = [bm.verts.new((sx * 1.2, sy * 1.2, Ht + 1.3)) for (sx, sy) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for k in range(4):
        f = bm.faces.new((ap, cs[k], cs[(k + 1) % 4]))
        f.material_index = k % 2
    parts.append(_mesh_obj(bm, "cobertura", [tint, stripe], 0.02, 0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(tube((sx * P, sy * P, Ht + 1.1), (sx * 1.2, sy * 1.2, Ht + 1.3), 0.03, steel, verts=8))
    # escada reta do chão até a plataforma, do lado -Y, com degraus, longarinas e corrimão
    n = 22
    for k in range(n):
        z = Ht * (k + 1) / (n + 1)
        y = -P - 0.3 - (n - k) * 0.27
        parts.append(box((0.9, 0.26, 0.05), (0, y, z), deck, bevel=0.01))
    for sx in (-0.48, 0.48):
        parts.append(tube((sx, -P - 0.3 - n * 0.27 - 0.2, 0.0), (sx, -P - 0.2, Ht), 0.04, steel, verts=10))
        parts.append(tube((sx, -P - 0.3 - n * 0.27 - 0.2, 0.95), (sx, -P - 0.2, Ht + 0.95), 0.025, steel, verts=10))
        for k in range(0, n + 1, 4):
            y = -P - 0.3 - (n - k) * 0.27
            z = Ht * k / (n + 1)
            parts.append(tube((sx, y, z), (sx, y, z + 0.95), 0.02, steel, verts=8))
    # calha: seção em U varrida numa hélice que desce da plataforma até a piscina
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    R = 2.6
    steps = 140
    turns = 1.75
    cx0 = 3.2
    ring_n = 13
    rings = []
    import mathutils
    V = mathutils.Vector
    path = []
    for i in range(steps + 1):
        t = i / steps
        if t < 0.9:
            tt = t / 0.9
            a = math.pi + 2 * math.pi * turns * tt
            p = V((cx0 + R * math.cos(a), R * math.sin(a), Ht + 0.15 - (Ht - 0.9) * tt))
        else:
            tt = (t - 0.9) / 0.1
            a = math.pi + 2 * math.pi * turns
            base = V((cx0 + R * math.cos(a), R * math.sin(a), 1.05))
            p = base + V((tt * 3.0, 0, -0.7 * tt))
        path.append(p)
    for i, p in enumerate(path):
        tg = (path[min(i + 1, steps)] - path[max(i - 1, 0)]).normalized()
        side = tg.cross(V((0, 0, 1))).normalized()
        up = side.cross(tg).normalized()
        ring = []
        for k in range(ring_n):
            ang = math.pi * k / (ring_n - 1)   # meia-volta: U aberto para cima
            off = side * math.cos(ang) * 0.42 + up * (-math.sin(ang) * 0.42 + 0.12)
            ring.append(bm.verts.new(p + off))
        rings.append(ring)
    for i in range(steps):
        for k in range(ring_n - 1):
            f = bm.faces.new((rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]))
            f.material_index = 1 if (i // 6) % 4 == 0 and k in (0, 1, ring_n - 2, ring_n - 1) else 0
            for lp in f.loops:
                lp[uvl].uv = (k / ring_n, i / 10)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    parts.append(_mesh_obj(bm, "calha", [tint, stripe], 0.04, 0))
    # bordas arredondadas (tubos ao longo das duas abas)
    for k in (0, ring_n - 1):
        pts = [tuple(rings[i][k].co) for i in range(0, steps + 1, 2)] if False else None
    edge_a, edge_b = [], []
    for i, p in enumerate(path):
        tg = (path[min(i + 1, steps)] - path[max(i - 1, 0)]).normalized()
        side = tg.cross(V((0, 0, 1))).normalized()
        up = side.cross(tg).normalized()
        edge_a.append(tuple(p + side * 0.42 + up * 0.12))
        edge_b.append(tuple(p - side * 0.42 + up * 0.12))
    parts.append(sweep(edge_a[::2], 0.035, tint, 8, "borda_a"))
    parts.append(sweep(edge_b[::2], 0.035, tint, 8, "borda_b"))
    # pilares de apoio da hélice
    for i in range(10, int(steps * 0.9), 14):
        p = path[i]
        if p.z > 0.6 and (abs(p.x) > 1.2 or abs(p.y) > 1.2):
            parts.append(tube((p.x, p.y, 0.0), (p.x, p.y, p.z - 0.32), 0.06, steel, verts=12))
            parts.append(lathe([(0.0, 0.0), (0.16, 0.0), (0.16, 0.05), (0.08, 0.08), (0.0, 0.08)], steel, loc=(p.x, p.y, 0), verts=14))
    join(parts, "water_slide")
    export("water_slide")


ALL = {"hotel_tower": hotel_tower, "hotel_restaurant": hotel_restaurant, "hotel_gym": hotel_gym, "gym_treadmill": gym_treadmill,
       "gym_bike": gym_bike, "gym_bench": gym_bench, "gym_dumbbells": gym_dumbbells, "water_slide": water_slide}

if __name__ == "__main__":
    for n in (sys.argv[1:] or list(ALL)):
        ALL[n]()
    print("gen_hotel ok")
