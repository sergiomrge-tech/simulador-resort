"""v1.0 — modelos dos novos negócios, feitos no Blender (bpy) com malha detalhada (sem primitivas cruas):
  biz_gelato      carrinho de sorvete com vitrine curva, 6 cubas com sorvete em ondas, pilha de casquinhas, guarda-sol e rodas
  biz_booth       quiosque de madeira (balcão, tábuas, telhado de zinco ondulado com beiral, painéis 'tint' para colorir no jogo)
  biz_kayak_rack  cavalete de madeira com 3 caiaques (casco em loft, cockpit com aro, assento) e 2 remos
  biz_board_rack  suporte de pranchas em A (as pranchas são g:surfboard, colocadas no Godot nos encaixes)
  biz_canopy      tenda de praia 3x3 com mastros, cobertura em gomos e babado recortado ('tint')
  biz_food_truck  food truck: carroceria arredondada em loft, cabine com vidros, janela de serviço com toldo levantado,
                  balcão, faróis, para-choques, rodas com pneu e calota, escapamento, cardápio e botijão
  biz_souvenir    expositores da lojinha: giratório de cartões-postais, prateleira em degraus com conchas/potes,
                  colares pendurados e cabideiro de cangas
  biz_barrier     cavalete de obra: tábuas listradas (vermelho/branco), pés abertos com travessa e placa "EM OBRAS"
Frente de todos = -Y do Blender (+Z no Godot). Base em z=0. Saída: assets/models/gen/<nome>.glb
Uso: python3 tools/gen_business.py [nome ...]"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_code_props import *
from gen_code_props import _torus, _wheel, _loft, _mesh_obj
import bpy, bmesh


def rbox(size, loc, m, rot, bevel=0.01):
    """Caixa girada em torno do PRÓPRIO centro. (box() do gen_code_props aplica a localização na malha, então a origem fica em (0,0,0)
    e rotation_euler giraria em volta da origem do mundo.)"""
    o = box(size, (0, 0, 0), m, bevel=bevel)
    o.location = loc
    o.rotation_euler = rot
    return o


def _glass(name="vidro", alpha=0.3):
    g = mat(name, (0.85, 0.95, 1.0), 0.05)
    g.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = alpha
    try:
        g.surface_render_method = "BLENDED"
    except Exception:
        g.blend_method = "BLEND"
    return g


def _umbrella(parts, z_top, R, mats, nseg=16, drop=0.32, name="guarda_sol"):
    """Guarda-sol em gomos alternados (mats[0]/mats[1]) com borda recortada entre as varetas."""
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    nr = 6
    rows = [[bm.verts.new((0, 0, z_top))]]
    nk = nseg * 3
    for i in range(1, nr + 1):
        rr = R * i / nr
        ring = []
        for k in range(nk):
            a = 2 * math.pi * k / nk
            scal = 1.0 - (0.07 * abs(math.sin(a * nseg / 2)) if i == nr else 0)
            ring.append(bm.verts.new((rr * scal * math.cos(a), rr * scal * math.sin(a), z_top - drop * (i / nr) ** 1.4)))
        rows.append(ring)
    for k in range(nk):
        f = bm.faces.new((rows[0][0], rows[1][k], rows[1][(k + 1) % nk]))
        f.material_index = (k // 3) % 2
    for i in range(1, nr):
        for k in range(nk):
            f = bm.faces.new((rows[i][k], rows[i + 1][k], rows[i + 1][(k + 1) % nk], rows[i][(k + 1) % nk]))
            f.material_index = (k // 3) % 2
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    parts.append(_mesh_obj(bm, name, mats, 0.012, 1))


def _scoop_tub(parts, loc, r, cream, metal, seed):
    """Cuba de inox com sorvete: superfície em ondas de espátula (sulcos em espiral), borda dobrada."""
    parts.append(lathe([(0.0, 0.0), (r * 0.92, 0.0), (r, 0.12), (r + 0.012, 0.125), (r + 0.012, 0.135), (0.0, 0.135)], metal, loc=loc, verts=28))
    rnd = random.Random(seed)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    nr, nk = 8, 36
    ph = rnd.uniform(0, 6.28)
    rows = []
    for i in range(nr + 1):
        t = i / nr
        rr = r * 0.97 * t
        ring = []
        for k in range(nk):
            a = 2 * math.pi * k / nk
            # monte baixo + ondas da espátula em espiral (dá o aspecto de sorvete servido, não de bola)
            z = 0.13 + 0.05 * (1 - t ** 1.6) + 0.012 * math.sin(3 * a + 9 * t + ph) * math.sin(math.pi * t) + 0.006 * math.sin(7 * a - 5 * t)
            ring.append(bm.verts.new((loc[0] + rr * math.cos(a), loc[1] + rr * math.sin(a), loc[2] + z)))
        rows.append(ring)
    for i in range(nr):
        for k in range(nk):
            f = bm.faces.new((rows[i][k], rows[i + 1][k], rows[i + 1][(k + 1) % nk], rows[i][(k + 1) % nk]))
            for lp in f.loops:
                lp[uvl].uv = (lp.vert.co.x * 4, lp.vert.co.y * 4)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    parts.append(_mesh_obj(bm, "sorvete", [cream], 0.0, 1))


def _cone(parts, loc, waffle, tilt=0.0):
    """Casquinha de biscoito: cone com sulcos em losango (anéis alternados de raio) e borda grossa."""
    prof = [(0.0, 0.0)]
    n = 10
    for i in range(1, n + 1):
        z = 0.13 * i / n
        rr = 0.028 * i / n + (0.0015 if i % 2 else 0.0)
        prof.append((rr, z))
    prof += [(0.031, 0.132), (0.031, 0.145), (0.024, 0.145), (0.024, 0.14)]
    o = lathe(prof, waffle, loc=loc, verts=20)
    o.rotation_euler = (tilt, 0, 0)
    parts.append(o)


# ---------------------------------------------------------------- sorveteria
def biz_gelato():
    fresh()
    body = mat("tint_corpo", (1.0, 0.75, 0.82), 0.45)
    white = mat("branco", (0.97, 0.96, 0.93), 0.5)
    chrome = mat("inox", (0.82, 0.84, 0.86), 0.3, metal=0.0)
    tire = mat("pneu", (0.08, 0.08, 0.09), 0.8)
    waffle = mat("biscoito", (0.85, 0.6, 0.3), 0.8)
    glass = _glass()
    creams = [mat("sorvete%d" % i, c, 0.6) for i, c in enumerate([(0.98, 0.93, 0.8), (0.45, 0.25, 0.15), (0.95, 0.5, 0.6), (0.6, 0.85, 0.45), (0.98, 0.85, 0.3), (0.6, 0.45, 0.85)])]
    parts = [anchor(body)]
    # gabinete com cantos boleados e friso
    parts.append(box((1.6, 0.8, 0.82), (0, 0, 0.55), body, bevel=0.06))
    parts.append(box((1.64, 0.84, 0.05), (0, 0, 0.98), white, bevel=0.02))
    parts.append(box((1.64, 0.84, 0.04), (0, 0, 0.14), chrome, bevel=0.015))
    for k in range(7):   # listras verticais pintadas na frente
        parts.append(box((0.07, 0.012, 0.7), (-0.6 + k * 0.2, -0.405, 0.56), white, bevel=0.01))
    # tampo com 6 cubas
    for i in range(6):
        x = -0.55 + (i % 3) * 0.37 + (0.0 if i < 3 else 0.0)
        y = -0.15 if i < 3 else 0.17
        _scoop_tub(parts, (x, y, 0.995), 0.13, creams[i], chrome, i * 7 + 3)
    # vitrine curva (vidro + perfis)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    nx, na = 2, 10
    rows = []
    for j in range(na + 1):
        a = math.pi * 0.5 * j / na
        rows.append([bm.verts.new((x, -0.38 + 0.38 * (1 - math.cos(a)) * 0.9, 1.0 + 0.42 * math.sin(a))) for x in (-0.78, 0.0, 0.78)])
    for j in range(na):
        for i in range(nx):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    parts.append(_mesh_obj(bm, "vitrine", [glass], 0.006, 0))
    for x in (-0.79, 0.0, 0.79):
        pts = []
        for j in range(na + 1):
            a = math.pi * 0.5 * j / na
            pts.append((x, -0.38 + 0.38 * (1 - math.cos(a)) * 0.9, 1.0 + 0.42 * math.sin(a)))
        pts.append((x, 0.3, 1.42))
        parts.append(sweep(pts, 0.012, chrome, 8, "perfil"))
    parts.append(tube((-0.8, 0.3, 1.42), (0.8, 0.3, 1.42), 0.014, chrome, verts=10))
    # pilha de casquinhas em suporte
    parts.append(lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.02), (0.012, 0.03), (0.012, 0.3), (0.0, 0.3)], chrome, loc=(0.92, 0.25, 1.0), verts=16))
    for k in range(6):
        _cone(parts, (0.92, 0.25, 1.06 + k * 0.035), waffle)
    # rodas, pés e puxador
    for sx in (-0.65, 0.65):
        _wheel(parts, (sx * 1.2, 0.2, 0.24), 0.24, tire, chrome, 12, True, 0.06)
    parts.append(sweep([(-0.5, 0.4, 0.85), (-0.5, 0.62, 0.9), (0.5, 0.62, 0.9), (0.5, 0.4, 0.85)], 0.016, chrome, 10, "puxador"))
    for sx in (-0.7, 0.7):
        parts.append(tube((sx, -0.32, 0.15), (sx, -0.32, 0.0), 0.025, chrome, verts=12))
    # mastro e guarda-sol listrado
    parts.append(tube((0.0, 0.3, 1.0), (0.0, 0.3, 2.65), 0.022, chrome, verts=12))
    um = []
    _umbrella(um, 2.75, 1.05, [white, body])
    for o in um:
        o.location.y += 0.3
    parts += um
    join(parts, "biz_gelato")
    export("biz_gelato")


# ---------------------------------------------------------------- quiosque de madeira genérico
def biz_booth():
    """2,4 x 1,6 m, 2,7 m de altura. Painéis 'tint' (frente do balcão, testeira) recebem a cor do negócio no Godot."""
    fresh()
    wood = mat("madeira", (0.62, 0.42, 0.25), 0.8, tex("weathered_planks_diff.jpg") if os.path.exists(tex("weathered_planks_diff.jpg")) else tex("oak_wood_planks_diff.jpg"))
    dark = mat("madeira_escura", (0.35, 0.22, 0.13), 0.8, tex("oak_wood_planks_diff.jpg"))
    tint = mat("tint_painel", (0.9, 0.9, 0.9), 0.6)
    zinc = mat("zinco", (0.7, 0.73, 0.75), 0.45)
    parts = [anchor(wood)]
    W, D = 2.4, 1.6
    # 4 esteios com sapata e mão-francesa
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (W / 2 - 0.08), sy * (D / 2 - 0.08)
            parts.append(box((0.11, 0.11, 2.42 if sy < 0 else 2.2), (x, y, (2.42 if sy < 0 else 2.2) / 2), dark, bevel=0.015))
            parts.append(box((0.16, 0.16, 0.06), (x, y, 0.03), dark, bevel=0.012))
    # paredes de tábuas (fundo e laterais) até o balcão, tábuas com fresta
    for k in range(12):
        x = -W / 2 + 0.12 + k * 0.198
        parts.append(box((0.185, 0.035, 2.1), (x, D / 2 - 0.06, 1.05), wood, bevel=0.008))
    for sx in (-1, 1):
        for k in range(7):
            y = -D / 2 + 0.15 + k * 0.2
            parts.append(box((0.035, 0.185, 1.05), (sx * (W / 2 - 0.06), y, 0.525), wood, bevel=0.008))
    # balcão: frente em tábuas pintadas (tint) + tampo grosso com borda
    for k in range(12):
        x = -W / 2 + 0.12 + k * 0.198
        parts.append(box((0.185, 0.035, 0.98), (x, -D / 2 + 0.04, 0.5), tint, bevel=0.008))
    parts.append(box((W + 0.1, 0.5, 0.06), (0, -D / 2 + 0.12, 1.04), dark, bevel=0.015))
    parts.append(box((W - 0.2, 0.35, 0.035), (0, 0.1, 0.85), wood, bevel=0.01))   # bancada interna
    # testeira (placa com o nome vai por Label3D) e caibros
    parts.append(box((W + 0.1, 0.05, 0.42), (0, -D / 2 - 0.0, 2.25), tint, bevel=0.015))
    parts.append(box((W + 0.18, 0.07, 0.05), (0, -D / 2 - 0.01, 2.48), dark, bevel=0.01))
    parts.append(box((W + 0.18, 0.07, 0.05), (0, -D / 2 - 0.01, 2.03), dark, bevel=0.01))
    for k in range(6):
        x = -W / 2 + k * W / 5
        o = rbox((0.06, D + 0.6, 0.09), (x, 0.0, 2.33), dark, (math.radians(-8), 0, 0), bevel=0.01)
        parts.append(o)
    # telha de zinco ondulada (malha com ondas senoidais) inclinada para trás
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    nx, ny = 96, 4
    L = D + 0.7
    rows = []
    for j in range(ny + 1):
        yy = -L / 2 + L * j / ny
        row = []
        for i in range(nx + 1):
            x = -(W + 0.4) / 2 + (W + 0.4) * i / nx
            z = 0.025 * math.sin(i * math.pi / 2)
            ang = math.radians(-8)
            row.append(bm.verts.new((x, yy * math.cos(ang), 2.42 + yy * math.sin(ang) + z)))
        rows.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
            for lp in f.loops:
                lp[uvl].uv = (lp.vert.co.x, lp.vert.co.y)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    parts.append(_mesh_obj(bm, "zinco", [zinc], 0.008, 0))
    # prateleiras internas com mãos-francesas
    for z in (1.45, 1.85):
        parts.append(box((W - 0.3, 0.28, 0.03), (0, D / 2 - 0.22, z), wood, bevel=0.008))
    join(parts, "biz_booth")
    export("biz_booth")


# ---------------------------------------------------------------- caiaque e cavalete
def _kayak(parts, cx, cy, cz, hull, rim, seat, L=2.8):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    secs = []
    n = 26
    for i in range(n + 1):
        t = i / n
        x = -L / 2 + L * t
        w = 0.34 * math.sin(math.pi * t) ** 0.65 + 0.004
        h = 0.17 * math.sin(math.pi * t) ** 0.5 + 0.004
        secs.append((x, w, h, 0.0))
    rings = []
    rn = 24
    for (x, ry, rz, cyy) in secs:
        ring = []
        for k in range(rn):
            a = 2 * math.pi * k / rn
            s = math.sin(a)
            # casco: fundo em V suave (abaixo) e convés mais chato (acima)
            z = rz * (s * 0.7 if s > 0 else s * (1.0 + 0.15 * abs(math.cos(a))))
            ring.append(bm.verts.new((cx + x, cy + ry * math.cos(a), cz + z + 0.17 * (2 * (x / L)) ** 4)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(rn):
            k2 = (k + 1) % rn
            f = bm.faces.new((rings[i][k], rings[i + 1][k], rings[i + 1][k2], rings[i][k2]))
            for lp in f.loops:
                lp[uvl].uv = (lp.vert.co.x * 2, lp.vert.co.y * 2)
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    parts.append(_mesh_obj(bm, "casco", [hull], 0.0, 1))
    # aro do cockpit (elipse) e assento
    pts = []
    for k in range(33):
        a = 2 * math.pi * k / 32
        pts.append((cx + 0.05 + 0.42 * math.cos(a), cy + 0.2 * math.sin(a), cz + 0.125))
    parts.append(sweep(pts, 0.022, rim, 8, "aro"))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    ring = [bm.verts.new((cx + 0.05 + 0.4 * math.cos(2 * math.pi * k / 32), cy + 0.18 * math.sin(2 * math.pi * k / 32), cz + 0.1)) for k in range(32)]
    bm.faces.new(ring)
    parts.append(_mesh_obj(bm, "cockpit", [rim], 0.01, 0))
    parts.append(box((0.32, 0.26, 0.05), (cx - 0.05, cy, cz + 0.14), seat, bevel=0.02))
    # alças de ponta (corda)
    for sx in (-1, 1):
        x = cx + sx * (L / 2 - 0.08)
        z = cz + 0.17 + 0.02
        parts.append(sweep([(x, cy - 0.04, z - 0.02), (x + sx * 0.05, cy - 0.04, z + 0.03), (x + sx * 0.05, cy + 0.04, z + 0.03), (x, cy + 0.04, z - 0.02)], 0.008, rim, 6, "alca"))


def _paddle(parts, a, b, shaft, blade):
    parts.append(tube(a, b, 0.016, shaft, verts=10))
    import mathutils
    V = mathutils.Vector
    d = (V(b) - V(a)).normalized()
    for p, s in ((V(a), -1), (V(b), 1)):
        c = p + d * s * 0.2
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        side = d.cross(V((0, 0, 1))).normalized()
        pts = []
        for k in range(20):
            t = k / 19
            w = 0.09 * math.sin(math.pi * (0.15 + 0.85 * t)) + 0.02
            pts.append(c + d * s * (t - 0.5) * 0.44 + side * w)
        for k in range(19, -1, -1):
            t = k / 19
            w = 0.09 * math.sin(math.pi * (0.15 + 0.85 * t)) + 0.02
            pts.append(c + d * s * (t - 0.5) * 0.44 - side * w)
        bm.faces.new([bm.verts.new(q) for q in pts])
        parts.append(_mesh_obj(bm, "pa", [blade], 0.012, 0))


def biz_kayak_rack():
    """Cavalete de 2 andares (3,2 m) com 3 caiaques e 2 remos apoiados. 1,3 m de fundo."""
    fresh()
    wood = mat("madeira", (0.55, 0.36, 0.2), 0.8, tex("oak_wood_planks_diff.jpg"))
    hulls = [mat("casco%d" % i, c, 0.35) for i, c in enumerate([(0.95, 0.75, 0.1), (0.95, 0.35, 0.15), (0.15, 0.55, 0.85)])]
    rim = mat("aro", (0.12, 0.12, 0.14), 0.6)
    seat = mat("assento", (0.2, 0.22, 0.25), 0.7)
    shaft = mat("cabo", (0.75, 0.77, 0.8), 0.4)
    blade = mat("pa", (0.1, 0.1, 0.12), 0.5)
    parts = [anchor(wood)]
    for sx in (-1.15, 1.15):
        for sy in (-0.55, 0.55):
            parts.append(box((0.1, 0.1, 1.55), (sx, sy, 0.775), wood, bevel=0.012))
        for z in (0.5, 1.15):
            parts.append(box((0.1, 1.3, 0.09), (sx, 0, z), wood, bevel=0.012))
            # berço acolchoado em curva onde o casco apoia
            parts.append(sweep([(sx, -0.42, z + 0.07), (sx, -0.2, z + 0.03), (sx, 0.0, z + 0.025), (sx, 0.2, z + 0.03), (sx, 0.42, z + 0.07)], 0.03, rim, 8, "berco"))
        parts.append(box((0.22, 1.4, 0.06), (sx, 0, 0.03), wood, bevel=0.012))
    parts.append(box((2.4, 0.08, 0.08), (0, 0.55, 1.5), wood, bevel=0.01))
    parts.append(box((2.4, 0.08, 0.08), (0, -0.55, 1.5), wood, bevel=0.01))
    _kayak(parts, 0, -0.25, 0.75, hulls[0], rim, seat)
    _kayak(parts, 0, 0.3, 0.75, hulls[1], rim, seat)
    _kayak(parts, 0, 0.0, 1.4, hulls[2], rim, seat)
    _paddle(parts, (1.45, -0.6, 0.0), (1.55, -0.62, 2.1), shaft, blade)
    _paddle(parts, (1.6, -0.4, 0.0), (1.66, -0.45, 2.1), shaft, blade)
    join(parts, "biz_kayak_rack")
    export("biz_kayak_rack")


def biz_board_rack():
    """Suporte em A de 2 m com 5 encaixes por lado (pranchas g:surfboard são postas no Godot a cada 0,36 m em x, inclinadas 15°)."""
    fresh()
    wood = mat("madeira", (0.6, 0.4, 0.22), 0.8, tex("oak_wood_planks_diff.jpg"))
    pad = mat("espuma", (0.15, 0.4, 0.6), 0.8)
    rope = mat("corda", (0.8, 0.7, 0.5), 0.9)
    parts = [anchor(wood)]
    for sx in (-1.0, 1.0):
        for sy in (-1, 1):
            ang = math.atan2(0.4, 1.38)
            parts.append(rbox((0.08, 0.08, math.hypot(0.4, 1.38) + 0.04), (sx, sy * 0.25, 0.69), wood, (sy * ang, 0, 0), bevel=0.012))
        parts.append(box((0.08, 0.9, 0.07), (sx, 0, 0.2), wood, bevel=0.01))
    parts.append(box((2.1, 0.09, 0.09), (0, 0, 1.38), wood, bevel=0.012))
    for sy in (-1, 1):
        parts.append(box((2.1, 0.08, 0.12), (sy * 0 + 0, sy * 0.38, 0.3), wood, bevel=0.012))
        parts.append(box((2.1, 0.1, 0.05), (0, sy * 0.38, 0.38), pad, bevel=0.02))
        for k in range(6):   # pinos separadores
            x = -0.9 + k * 0.36
            parts.append(lathe([(0.0, 0.0), (0.018, 0.0), (0.018, 0.14), (0.024, 0.15), (0.0, 0.16)], wood, loc=(x, sy * 0.38, 0.4), verts=12))
    for sx in (-1.0, 1.0):
        parts.append(sweep([(sx - 0.05, -0.1, 1.3), (sx, -0.12, 1.26), (sx + 0.05, -0.1, 1.3), (sx + 0.05, 0.1, 1.3), (sx, 0.12, 1.26), (sx - 0.05, 0.1, 1.3), (sx - 0.05, -0.1, 1.3)], 0.012, rope, 6, "amarra"))
    join(parts, "biz_board_rack")
    export("biz_board_rack")


# ---------------------------------------------------------------- tenda
def biz_canopy():
    """Tenda 3 x 3 m: 4 mastros de alumínio com sapatas e estais, teto em pirâmide com costuras e babado recortado. 'tint' = lona."""
    fresh()
    canvas = mat("tint_lona", (0.95, 0.95, 0.92), 0.7, tex("rough_linen_diff.jpg"))
    white = mat("branco", (0.97, 0.97, 0.95), 0.7, tex("rough_linen_diff.jpg"))
    alu = mat("aluminio", (0.78, 0.8, 0.82), 0.35)
    rope = mat("corda", (0.85, 0.8, 0.65), 0.9)
    parts = [anchor(alu)]
    S = 1.5
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(tube((sx * S, sy * S, 0.0), (sx * S, sy * S, 2.3), 0.025, alu, verts=12))
            parts.append(box((0.2, 0.2, 0.03), (sx * S, sy * S, 0.015), alu, bevel=0.01))
            parts.append(sweep([(sx * S, sy * S, 2.2), (sx * (S + 0.45), sy * (S + 0.45), 1.1), (sx * (S + 0.9), sy * (S + 0.9), 0.0)], 0.012, rope, 8, "estai"))
    for (a, b) in (((-S, -S), (S, -S)), ((S, -S), (S, S)), ((S, S), (-S, S)), ((-S, S), (-S, -S))):
        parts.append(tube((a[0], a[1], 2.3), (b[0], b[1], 2.3), 0.02, alu, verts=10))
    # teto: pirâmide com leve barriga entre as costuras
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    apex = bm.verts.new((0, 0, 3.0))
    n = 12
    nr = 6
    corners = [(-S, -S), (S, -S), (S, S), (-S, S)]
    for side in range(4):
        a, b = corners[side], corners[(side + 1) % 4]
        grid = []
        for i in range(nr + 1):
            t = i / nr
            row = []
            for j in range(n + 1):
                u = j / n
                ex = a[0] + (b[0] - a[0]) * u
                ey = a[1] + (b[1] - a[1]) * u
                sag = 0.08 * math.sin(math.pi * u) * math.sin(math.pi * t)
                row.append((ex * t, ey * t, 3.0 - 0.7 * t - sag))
            grid.append(row)
        vs = [[apex] * (n + 1)] + [[bm.verts.new(p) for p in grid[i]] for i in range(1, nr + 1)]
        for i in range(nr):
            for j in range(n):
                q = [vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]]
                q2 = []
                for v in q:
                    if v not in q2:
                        q2.append(v)
                if len(q2) >= 3:
                    f = bm.faces.new(q2)
                    for lp in f.loops:
                        lp[uvl].uv = (lp.vert.co.x * 0.5, lp.vert.co.y * 0.5)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    parts.append(_mesh_obj(bm, "teto", [canvas], 0.01, 0))
    # babado recortado (meias-luas) em volta, alternando lona/branco
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    for side in range(4):
        a, b = corners[side], corners[(side + 1) % 4]
        m = 8
        for k in range(m):
            top = []
            bot = []
            for j in range(7):
                u = (k + j / 6) / m
                x = a[0] + (b[0] - a[0]) * u
                y = a[1] + (b[1] - a[1]) * u
                top.append(bm.verts.new((x * 1.01, y * 1.01, 2.31)))
                bot.append(bm.verts.new((x * 1.01, y * 1.01, 2.31 - 0.08 - 0.16 * math.sin(math.pi * j / 6))))
            for j in range(6):
                f = bm.faces.new((top[j], top[j + 1], bot[j + 1], bot[j]))
                f.material_index = k % 2
    parts.append(_mesh_obj(bm, "babado", [canvas, white], 0.006, 0))
    join(parts, "biz_canopy")
    export("biz_canopy")


# ---------------------------------------------------------------- food truck
def biz_food_truck():
    """Food truck de 5,2 m: carroceria em loft com cantos boleados, cabine com para-brisa e portas, janela de serviço (lado -Y) com
    toldo levantado por 2 hastes, balcão, rodas 4x (pneu + calota + para-lama), faróis, grade, para-choques, escada e botijão. 'tint' = pintura."""
    fresh()
    paint = mat("tint_pintura", (0.95, 0.4, 0.3), 0.35)
    white = mat("branco", (0.96, 0.95, 0.92), 0.4)
    chrome = mat("cromado", (0.82, 0.84, 0.86), 0.25)
    tire = mat("pneu", (0.06, 0.06, 0.07), 0.85)
    glass = _glass("vidro", 0.45)
    dark = mat("interior", (0.12, 0.12, 0.14), 0.7)
    light = mat("glow_farol", (1.0, 0.95, 0.75), 0.2)
    awn = mat("toldo", (0.95, 0.85, 0.3), 0.7, tex("rough_linen_diff.jpg"))
    gas = mat("botijao", (0.15, 0.35, 0.75), 0.4)
    wood = mat("balcao", (0.55, 0.36, 0.2), 0.7, tex("oak_wood_planks_diff.jpg"))
    parts = [anchor(paint)]
    # carroceria (baú) e cabine como loft de seções retangulares boleadas ao longo de X
    def rbox_section(x, w, h, z0, r):
        pts = []
        for (cx, cz, a0) in ((w / 2 - r, z0 + h - r, 0), (-w / 2 + r, z0 + h - r, 90), (-w / 2 + r, z0 + r, 180), (w / 2 - r, z0 + r, 270)):
            for k in range(5):
                a = math.radians(a0 + 90 * k / 4)
                pts.append((x, cx + r * math.cos(a), cz + r * math.sin(a)))
        return pts
    def loft_rbox(secs, m, name):
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        rings = [[bm.verts.new(p) for p in rbox_section(*s)] for s in secs]
        n = len(rings[0])
        for i in range(len(rings) - 1):
            for k in range(n):
                f = bm.faces.new((rings[i][k], rings[i + 1][k], rings[i + 1][(k + 1) % n], rings[i][(k + 1) % n]))
                for lp in f.loops:
                    lp[uvl].uv = (lp.vert.co.x * 0.5, lp.vert.co.z * 0.5)
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        return _mesh_obj(bm, name, [m], 0.0, 0)
    # baú: x de -2.6 a 1.1 ; cabine: 1.1 a 2.6
    parts.append(loft_rbox([(-2.6, 2.1, 2.2, 0.55, 0.12), (-2.55, 2.2, 2.3, 0.5, 0.18), (1.1, 2.2, 2.3, 0.5, 0.18), (1.12, 2.12, 2.22, 0.54, 0.14)], paint, "bau"))
    parts.append(loft_rbox([(1.1, 2.1, 1.7, 0.5, 0.2), (2.1, 2.1, 1.55, 0.5, 0.25), (2.5, 2.05, 0.95, 0.5, 0.25), (2.62, 1.95, 0.75, 0.52, 0.2)], paint, "cabine"))
    # faixa branca e frisos
    parts.append(box((3.75, 2.24, 0.18), (-0.75, 0, 1.0), white, bevel=0.03))
    parts.append(box((3.7, 2.22, 0.05), (-0.75, 0, 2.62), white, bevel=0.02))
    # para-brisa e vidros laterais da cabine
    o = rbox((0.03, 1.8, 0.6), (2.28, 0, 1.68), glass, (0, math.radians(-28), 0), bevel=0.01)
    parts.append(o)
    for sy in (-1, 1):
        parts.append(box((0.7, 0.02, 0.5), (1.65, sy * 1.06, 1.65), glass, bevel=0.01))
        parts.append(box((0.9, 0.012, 1.05), (1.6, sy * 1.065, 1.05), paint, bevel=0.005))   # porta (relevo)
        parts.append(box((0.12, 0.03, 0.03), (1.3, sy * 1.08, 1.25), chrome, bevel=0.01))   # maçaneta
        parts.append(box((0.08, 0.16, 0.12), (2.05, sy * 1.18, 1.75), dark, bevel=0.02))   # retrovisor
    # janela de serviço (-Y): vão escuro, moldura, balcão de madeira e toldo levantado
    parts.append(box((2.2, 0.02, 1.0), (-0.8, -1.105, 1.75), dark, bevel=0.0))
    for (sz, loc) in (((2.3, 0.06, 0.06), (-0.8, -1.12, 2.28)), ((2.3, 0.06, 0.06), (-0.8, -1.12, 1.22)), ((0.06, 0.06, 1.1), (-1.95, -1.12, 1.75)), ((0.06, 0.06, 1.1), (0.35, -1.12, 1.75))):
        parts.append(box(sz, loc, chrome, bevel=0.01))
    parts.append(box((2.4, 0.42, 0.05), (-0.8, -1.3, 1.24), wood, bevel=0.015))
    for sx in (-1.8, 0.2):
        parts.append(tube((sx, -1.13, 1.0), (sx, -1.45, 1.22), 0.012, chrome, verts=8))
    # toldo: lona com caimento e borda recortada, do alto da janela até as hastes
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    nx, ny = 24, 6
    grid = []
    for j in range(ny + 1):
        tj = j / ny
        row = []
        for i in range(nx + 1):
            x = -2.0 + 2.4 * i / nx
            y = -1.13 - 0.8 * tj
            z = 2.32 + 0.42 * tj - 0.05 * math.sin(math.pi * tj)
            if j == ny:
                z -= 0.06 * abs(math.sin(i * math.pi / 2))
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            f.material_index = (i // 3) % 2
            for lp in f.loops:
                lp[uvl].uv = (lp.vert.co.x, lp.vert.co.y)
    parts.append(_mesh_obj(bm, "toldo", [awn, white], 0.012, 0))
    for sx in (-1.9, 0.3):
        parts.append(tube((sx, -1.12, 1.95), (sx, -1.9, 2.7), 0.012, chrome, verts=8))
    # chapa, panelas e potes visíveis pela janela
    parts.append(box((1.0, 0.4, 0.06), (-1.2, -0.75, 1.32), chrome, bevel=0.01))
    parts.append(lathe([(0.0, 0.0), (0.16, 0.0), (0.17, 0.02), (0.17, 0.2), (0.18, 0.21), (0.0, 0.21)], chrome, loc=(-0.2, -0.75, 1.32), verts=24))
    # quadro de cardápio ao lado da janela
    parts.append(box((0.55, 0.03, 0.75), (0.85, -1.11, 1.75), dark, bevel=0.01))
    parts.append(box((0.6, 0.035, 0.8), (0.85, -1.105, 1.75), wood, bevel=0.01))
    # frente: grade, faróis, para-choque
    parts.append(box((0.04, 1.2, 0.35), (2.64, 0, 0.92), chrome, bevel=0.01))
    for k in range(5):
        parts.append(box((0.05, 1.15, 0.025), (2.66, 0, 0.8 + k * 0.06), dark, bevel=0.005))
    for sy in (-0.78, 0.78):
        parts.append(lathe([(0.0, 0.0), (0.12, 0.0), (0.13, 0.03), (0.13, 0.06), (0.0, 0.06)], chrome, loc=(2.6, sy, 0.95), verts=24))
        parts[-1].rotation_euler = (0, math.radians(90), 0)
        parts.append(lathe([(0.0, 0.055), (0.11, 0.055), (0.1, 0.075), (0.0, 0.08)], light, loc=(2.6, sy, 0.95), verts=24))
        parts[-1].rotation_euler = (0, math.radians(90), 0)
    parts.append(box((0.14, 2.25, 0.16), (2.7, 0, 0.6), chrome, bevel=0.04))
    parts.append(box((0.14, 2.25, 0.16), (-2.68, 0, 0.6), chrome, bevel=0.04))
    # lanternas traseiras
    for sy in (-0.9, 0.9):
        parts.append(box((0.04, 0.12, 0.25), (-2.66, sy, 1.0), mat("lanterna", (0.9, 0.15, 0.1), 0.3), bevel=0.01))
    # rodas, para-lamas, chassi
    for wx in (-1.6, 1.75):
        for sy in (-1, 1):
            loc = (wx, sy * 0.98, 0.42)
            parts.append(_torus(0.32, 0.12, loc, False, tire, 40, 14))
            parts[-1].rotation_euler = (math.radians(90), 0, 0)
            parts.append(lathe([(0.0, 0.0), (0.22, 0.0), (0.24, 0.03), (0.18, 0.07), (0.06, 0.09), (0.0, 0.1)], chrome, loc=(wx, sy * (0.98 + 0.08), 0.42), verts=28))
            parts[-1].rotation_euler = (math.radians(-90 * sy), 0, 0)
            pts = [(wx + 0.55 * math.cos(math.radians(a)), sy * 1.1, 0.42 + 0.55 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
            parts.append(sweep(pts, 0.04, paint, 8, "paralama"))
    parts.append(box((4.6, 1.4, 0.18), (0, 0, 0.45), dark, bevel=0.02))
    # escada lateral, escapamento e botijão
    parts.append(box((0.5, 0.3, 0.04), (-2.1, -1.25, 0.45), chrome, bevel=0.01))
    parts.append(box((0.5, 0.3, 0.04), (-2.1, -1.25, 0.2), chrome, bevel=0.01))
    for sx in (-2.33, -1.87):
        parts.append(tube((sx, -1.25, 0.15), (sx, -1.25, 0.5), 0.015, chrome, verts=8))
    parts.append(sweep([(-2.0, 0.6, 0.38), (-2.5, 0.6, 0.36), (-2.75, 0.6, 0.38)], 0.04, chrome, 10, "escape"))
    parts.append(lathe([(0.0, 0.0), (0.16, 0.0), (0.18, 0.04), (0.18, 0.45), (0.14, 0.53), (0.05, 0.56), (0.05, 0.62), (0.0, 0.62)], gas, loc=(-2.85, -0.75, 0.0), verts=24))
    parts.append(_torus(0.08, 0.012, (-2.85, -0.75, 0.66), False, chrome, 24, 8))
    join(parts, "biz_food_truck")
    export("biz_food_truck")


# ---------------------------------------------------------------- lojinha de souvenires
def biz_souvenir():
    """Expositores: giratório de cartões-postais (1,7 m), prateleira em 3 degraus com potes de conchas e barquinhos de madeira,
    varal de colares de conchas e cabideiro com 3 cangas listradas. Ocupa 2,2 x 0,8 m. Frente = -Y."""
    fresh()
    rnd = random.Random(31)
    wire = mat("arame", (0.2, 0.2, 0.22), 0.5)
    wood = mat("madeira", (0.6, 0.4, 0.22), 0.8, tex("oak_wood_planks_diff.jpg"))
    cards = [mat("postal%d" % i, c, 0.5) for i, c in enumerate([(0.2, 0.6, 0.9), (0.95, 0.6, 0.2), (0.3, 0.75, 0.5), (0.95, 0.85, 0.4), (0.9, 0.35, 0.45)])]
    shellm = mat("concha", (1.0, 0.9, 0.82), 0.6)
    glass = _glass("vidro", 0.35)
    linen = [mat("canga%d" % i, c, 0.8, tex("rough_linen_diff.jpg")) for i, c in enumerate([(0.95, 0.45, 0.25), (0.2, 0.6, 0.85), (0.95, 0.8, 0.3)])]
    boatm = mat("barquinho", (0.85, 0.3, 0.25), 0.6)
    parts = [anchor(wood)]
    # giratório de postais em x=-0.8
    cx = -0.8
    parts.append(lathe([(0.0, 0.0), (0.25, 0.0), (0.26, 0.02), (0.05, 0.05), (0.02, 0.07), (0.02, 1.7), (0.035, 1.72), (0.0, 1.76)], wire, loc=(cx, 0, 0), verts=24))
    for tier in range(4):
        z = 0.55 + tier * 0.3
        for k in range(8):
            a = 2 * math.pi * k / 8 + tier * 0.4
            px, py = cx + 0.18 * math.cos(a), 0.18 * math.sin(a)
            parts.append(tube((cx, 0, z), (px, py, z - 0.02), 0.004, wire, verts=6))
            c = rbox((0.15, 0.008, 0.105), (px, py, z + 0.03), cards[(k + tier) % 5], (math.radians(-8), 0, a + math.pi / 2), bevel=0.002)
            parts.append(c)
    # prateleira em degraus (x de -0.4 a 0.6)
    for k in range(3):
        parts.append(box((1.0, 0.25, 0.04), (0.1, -0.2 + k * 0.22, 0.45 + k * 0.33), wood, bevel=0.01))
    for sx in (-0.4, 0.6):   # laterais em degrau: 3 tábuas verticais de alturas crescentes para trás
        for k, (yc, h) in enumerate(((0.22, 0.49), (0.0, 0.82), (-0.22, 1.15))):
            parts.append(box((0.03, 0.22, h), (sx, -yc, h / 2), wood, bevel=0.006))
    # potes de vidro com conchinhas (conchas = leque de gomos achatados, não esferas)
    for k in range(4):
        x = -0.25 + k * 0.23
        parts.append(lathe([(0.0, 0.0), (0.06, 0.0), (0.065, 0.02), (0.065, 0.16), (0.05, 0.18), (0.05, 0.2), (0.0, 0.2)], glass, loc=(x, -0.2, 0.47), verts=20))
        for j in range(5):
            a = rnd.uniform(0, 6.28)
            bm = bmesh.new()
            bm.loops.layers.uv.new("UVMap")
            ctr = bm.verts.new((0, 0, 0))
            rim = []
            for q in range(9):
                t = -0.9 + 1.8 * q / 8
                rr = 0.022 * (1 + 0.12 * (q % 2))
                rim.append(bm.verts.new((rr * math.sin(t), rr * math.cos(t), 0.004 * (q % 2))))
            for q in range(8):
                bm.faces.new((ctr, rim[q], rim[q + 1]))
            o = _mesh_obj(bm, "conchinha", [shellm], 0.004, 0)
            o.location = (x + 0.03 * math.cos(a), -0.2 + 0.03 * math.sin(a), 0.5 + j * 0.022)
            o.rotation_euler = (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), a)
            parts.append(o)
    # barquinhos de madeira no 2º e 3º degraus
    for k in range(3):
        x = -0.2 + k * 0.32
        z = 0.805 + (k % 2) * 0.33
        y = 0.02 + (k % 2) * 0.22
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        secs = [(xx, 0.045 * math.sin(math.pi * (xx + 0.12) / 0.24) ** 0.7 + 0.003, 0.035 * math.sin(math.pi * (xx + 0.12) / 0.24) ** 0.5 + 0.003, 0.03) for xx in [(-0.12 + 0.24 * i / 10) for i in range(11)]]
        _loft(bm, uvl, secs, 14, True)
        o = _mesh_obj(bm, "barco", [boatm], 0.0, 1)
        o.location = (x, y, z)
        parts.append(o)
        parts.append(tube((x, y, z + 0.05), (x, y, z + 0.2), 0.003, wood, verts=6))
        bm = bmesh.new()
        bm.loops.layers.uv.new("UVMap")
        bm.faces.new([bm.verts.new(p) for p in ((x + 0.005, y, z + 0.07), (x + 0.005, y, z + 0.19), (x + 0.09, y, z + 0.08))])
        parts.append(_mesh_obj(bm, "vela", [shellm], 0.003, 0))
    # varal de colares de conchas (barra em x 0.75..1.05, z 1.55)
    parts.append(tube((0.7, -0.1, 0.0), (0.7, -0.1, 1.65), 0.018, wood, verts=10))
    parts.append(tube((0.7, -0.1, 1.6), (1.1, -0.1, 1.6), 0.012, wood, verts=8))
    for k in range(4):
        x = 0.78 + k * 0.09
        pts = [(x - 0.03 + 0.03 * math.cos(math.radians(a)), -0.1, 1.58 - 0.22 * math.sin(math.radians(a))) for a in range(180, 361, 15)]
        pts = [(x - 0.03, -0.1, 1.6)] + [(x + 0.035 * math.cos(math.radians(a)), -0.1, 1.38 + 0.2 * (1 + math.sin(math.radians(a))) / 2) for a in range(-180, 1, 15)] + [(x + 0.035, -0.1, 1.6)]
        parts.append(sweep(pts, 0.003, wire, 6, "fio"))
        for j in range(5):
            a = math.radians(-180 + 45 * j)
            o = lathe([(0.0, 0.0), (0.008, 0.002), (0.006, 0.014), (0.0, 0.02)], cards[(k + j) % 5] if j == 2 else shellm, loc=(x + 0.035 * math.cos(a), -0.1, 1.38 + 0.2 * (1 + math.sin(a)) / 2 - 0.01), verts=10)
            parts.append(o)
    # cabideiro de cangas em x=1.0 (cangas = pano com caimento e franja)
    parts.append(lathe([(0.0, 0.0), (0.2, 0.0), (0.22, 0.02), (0.03, 0.05), (0.02, 0.07), (0.02, 1.6), (0.03, 1.62), (0.0, 1.65)], wire, loc=(1.25, 0.15, 0), verts=20))
    for k in range(3):
        a = math.radians(90 + k * 120)
        ex, ey = 1.25 + 0.3 * math.cos(a), 0.15 + 0.3 * math.sin(a)
        parts.append(tube((1.25, 0.15, 1.55), (ex, ey, 1.5), 0.01, wire, verts=6))
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        nx, nz = 8, 10
        grid = []
        for iz in range(nz + 1):
            tz = iz / nz
            row = []
            for ix in range(nx + 1):
                tx = ix / nx
                off = 0.025 * math.sin(tx * math.pi * 3) * (0.3 + tz)
                row.append(bm.verts.new((ex + (tx - 0.5) * 0.28 * math.cos(a + math.pi / 2), ey + (tx - 0.5) * 0.28 * math.sin(a + math.pi / 2) + off, 1.5 - tz * 0.9)))
            grid.append(row)
        for iz in range(nz):
            for ix in range(nx):
                f = bm.faces.new((grid[iz][ix], grid[iz][ix + 1], grid[iz + 1][ix + 1], grid[iz + 1][ix]))
                for lp in f.loops:
                    lp[uvl].uv = (ix / nx, iz / nz)
        parts.append(_mesh_obj(bm, "canga", [linen[k]], 0.006, 0))
    join(parts, "biz_souvenir")
    export("biz_souvenir")


# ---------------------------------------------------------------- cavalete de obra
def biz_barrier():
    """Cavalete de obra 1,8 m: 2 tábuas com listras diagonais vermelho/branco (faces alternadas), pés em A com travessa,
    lanterna laranja no topo e placa "EM OBRAS" (texto no Godot). Frente = -Y."""
    fresh()
    red = mat("listra_verm", (0.85, 0.15, 0.1), 0.6)
    white = mat("listra_branca", (0.96, 0.95, 0.92), 0.6)
    wood = mat("madeira", (0.6, 0.42, 0.25), 0.8, tex("oak_wood_planks_diff.jpg"))
    yel = mat("placa", (0.98, 0.78, 0.1), 0.5)
    lamp = mat("glow_lanterna", (1.0, 0.55, 0.1), 0.3)
    parts = [anchor(wood)]
    for z in (0.55, 0.95):
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        n = 18
        for k in range(n):
            x0 = -0.9 + 1.8 * k / n
            x1 = -0.9 + 1.8 * (k + 1) / n
            sl = 0.1
            q = [bm.verts.new(p) for p in ((x0, -0.0, z - 0.09), (x1, 0.0, z - 0.09), (x1 + sl, 0.0, z + 0.09), (x0 + sl, 0.0, z + 0.09))]
            f = bm.faces.new(q)
            f.material_index = k % 2
        o = _mesh_obj(bm, "tabua", [red, white], 0.03, 0)
        parts.append(o)
    for sx in (-0.75, 0.75):
        for sy in (-1, 1):
            o = rbox((0.06, 0.06, 1.15), (sx, sy * 0.18, 0.55), wood, (math.radians(sy * 14), 0, 0), bevel=0.01)
            parts.append(o)
        parts.append(box((0.06, 0.5, 0.05), (sx, 0, 0.25), wood, bevel=0.01))
    parts.append(box((0.6, 0.02, 0.4), (0, -0.04, 1.35), yel, bevel=0.01))
    parts.append(tube((-0.25, -0.02, 1.0), (-0.25, -0.02, 1.2), 0.015, wood, verts=8))
    parts.append(tube((0.25, -0.02, 1.0), (0.25, -0.02, 1.2), 0.015, wood, verts=8))
    parts.append(lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.03), (0.045, 0.04), (0.06, 0.12), (0.03, 0.15), (0.0, 0.15)], lamp, loc=(0.82, 0.0, 1.04), verts=18))
    join(parts, "biz_barrier")
    export("biz_barrier")


ALL = {"biz_gelato": biz_gelato, "biz_booth": biz_booth, "biz_kayak_rack": biz_kayak_rack, "biz_board_rack": biz_board_rack,
       "biz_canopy": biz_canopy, "biz_food_truck": biz_food_truck, "biz_souvenir": biz_souvenir, "biz_barrier": biz_barrier}

if __name__ == "__main__":
    for n in (sys.argv[1:] or list(ALL)):
        ALL[n]()
    print("gen_business ok")
