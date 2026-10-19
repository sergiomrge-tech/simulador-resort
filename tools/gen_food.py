"""v1.0.1 — frutas e bebidas do quiosque modeladas no Blender (bpy), substituindo os Kenney low-poly que viravam "bolas de círculos"
depois de suavizados (coco, abacaxi, laranja, frappé). Malha densa com relevo de verdade:
  coconut_green   coco verde inteiro (forma ovoide com 3 quinas suaves, base achatada, coroa com sépalas marrons e cabinho)
  coconut_open    coco verde aberto como no quiosque: topo cortado em tronco de cone, casca branca, furo e canudo listrado
  pineapple       abacaxi: corpo com ~110 frutilhos hexagonais em espiral (cada um com bico), coroa de 26 folhas em roseta
  orange          laranja: casca com milhares de poros (relevo), umbigo e cálice verde com cabinho
  frappe          copo plástico cônico com café gelado, chantilly em espiral, calda e canudo
Base em z=0 (Blender) = y=0 no Godot. Uso: python3 tools/gen_food.py [nome ...]"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_code_props import *
from gen_code_props import _torus, _loft, _mesh_obj


def rbox(size, loc, m, rot, bevel=0.01):
    o = box(size, (0, 0, 0), m, bevel=bevel)
    o.location = loc
    o.rotation_euler = rot
    return o
import bpy, bmesh
from mathutils import Vector, noise


def _surface(fn, nu, nv, m, name, mi_fn=None, mats=None, sub=0):
    """Superfície de revolução genérica: fn(u, v) -> (x, y, z), u em [0,1) volta, v em [0,1] de baixo para cima (polos fechados)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    bot = bm.verts.new(fn(0.0, 0.0))
    top = bm.verts.new(fn(0.0, 1.0))
    rings = []
    for j in range(1, nv):
        v = j / nv
        rings.append([bm.verts.new(fn(i / nu, v)) for i in range(nu)])
    for i in range(nu):
        i2 = (i + 1) % nu
        f = bm.faces.new((bot, rings[0][i2], rings[0][i]))
        if mi_fn:
            f.material_index = mi_fn(i / nu, 0.0)
        f = bm.faces.new((top, rings[-1][i], rings[-1][i2]))
        if mi_fn:
            f.material_index = mi_fn(i / nu, 1.0)
    for j in range(len(rings) - 1):
        for i in range(nu):
            i2 = (i + 1) % nu
            f = bm.faces.new((rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i]))
            if mi_fn:
                f.material_index = mi_fn(i / nu, (j + 1) / nv)
            for lp in f.loops:
                lp[uvl].uv = (i / nu, j / nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _mesh_obj(bm, name, mats or [m], 0.0, sub)


# ---------------------------------------------------------------- coco verde
def _coco_shape(u, v, H=0.25, R=0.115, cut=None):
    a = 2 * math.pi * u
    # perfil ovoide: mais largo um pouco abaixo do meio, ponta arredondada no topo, base achatada
    t = v
    prof = math.sin(math.pi * min(t, 0.999)) ** 0.62 * (1.0 - 0.18 * t) + 0.02
    if t < 0.08:
        prof *= 0.75 + 0.25 * (t / 0.08)
    tri = 1.0 + 0.06 * math.cos(3 * a) * math.sin(math.pi * t)      # 3 quinas suaves do coco
    r = R * prof * tri
    z = H * (t if t > 0.02 else 0.02 * (t / 0.02))
    n = noise.noise(Vector((math.cos(a) * 3.0, math.sin(a) * 3.0, z * 12.0))) * 0.0025
    r += n
    return (r * math.cos(a), r * math.sin(a), z)


def _coco_mats():
    green = mat("casca_verde", (0.28, 0.55, 0.14), 0.55)
    yellow = mat("casca_amarelada", (0.62, 0.66, 0.22), 0.6)
    brown = mat("sepala", (0.38, 0.24, 0.12), 0.8)
    return green, yellow, brown


def _sepals(parts, ztop, brown, rad=0.035, n=6, lift=0.0):
    """Coroa (cálice) no topo do coco: sépalas triangulares curvas + cabinho."""
    for k in range(n):
        a = 2 * math.pi * k / n
        bm = bmesh.new()
        bm.loops.layers.uv.new("UVMap")
        pts = []
        for q in range(7):
            t = q / 6
            w = 0.018 * (1 - t) ** 0.8 + 0.002
            rr = rad * t
            z = ztop + lift - 0.012 * t * t
            pts.append((rr, w, z))
        left = [bm.verts.new(Vector((p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a), p[2]))) for p in pts]
        right = [bm.verts.new(Vector((p[0] * math.cos(a) + p[1] * math.sin(a), p[0] * math.sin(a) - p[1] * math.cos(a), p[2]))) for p in pts]
        for q in range(6):
            bm.faces.new((left[q], left[q + 1], right[q + 1], right[q]))
        parts.append(_mesh_obj(bm, "sepala", [brown], 0.004, 1))
    parts.append(lathe([(0.0, 0.0), (0.008, 0.0), (0.007, 0.02), (0.009, 0.026), (0.0, 0.028)], brown, loc=(0, 0, ztop + lift - 0.004), verts=12))


def coconut_green():
    fresh()
    green, yellow, brown = _coco_mats()
    parts = [anchor(green)]
    parts.append(_surface(lambda u, v: _coco_shape(u, v), 64, 48, green, "coco",
                          mi_fn=lambda u, v: 1 if v > 0.86 or v < 0.06 else 0, mats=[green, yellow], sub=1))
    _sepals(parts, 0.248, brown)
    join(parts, "coconut_green")
    export("coconut_green")


def coconut_open():
    """Coco verde servido: a parte de cima é desbastada a facão (facetas) e cortada reto, mostrando a casca branca e o furo; canudo."""
    fresh()
    green, yellow, brown = _coco_mats()
    white = mat("polpa_branca", (0.93, 0.9, 0.8), 0.7)
    dark = mat("furo", (0.15, 0.12, 0.08), 0.8)
    red = mat("canudo_verm", (0.9, 0.15, 0.15), 0.4)
    wht = mat("canudo_branco", (0.97, 0.97, 0.97), 0.4)
    parts = [anchor(green)]
    # corpo até 75% da altura, depois facetas brancas (desbaste) até o corte
    zc = 0.185
    def shape(u, v):
        x, y, z = _coco_shape(u, v * 0.75)
        return (x, y, z)
    parts.append(_surface(shape, 64, 40, green, "coco", mi_fn=lambda u, v: 1 if v < 0.06 else 0, mats=[green, yellow], sub=1))
    # anel de transição verde->branco e cone facetado (8 cortes de facão)
    x0, y0, z0 = _coco_shape(0.0, 0.75)
    r0 = math.hypot(x0, y0)
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    nf = 8
    sub = 6
    rings = []
    for j in range(sub + 1):
        t = j / sub
        z = z0 + (zc - z0) * t
        ring = []
        for i in range(nf * 4):
            a = 2 * math.pi * i / (nf * 4)
            # facetas planas: raio do polígono de 8 lados
            seg = math.cos(math.pi / nf) / math.cos(((a + math.pi / nf) % (2 * math.pi / nf)) - math.pi / nf)
            r = (r0 * (1 - t) + 0.045 * t) * (1.0 * (1 - t) + seg * t)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    nr = nf * 4
    for j in range(sub):
        for i in range(nr):
            bm.faces.new((rings[j][i], rings[j][(i + 1) % nr], rings[j + 1][(i + 1) % nr], rings[j + 1][i]))
    # tampa cortada com o furo no meio
    ctr = [bm.verts.new((0.012 * math.cos(2 * math.pi * i / nr), 0.012 * math.sin(2 * math.pi * i / nr), zc)) for i in range(nr)]
    for i in range(nr):
        bm.faces.new((rings[-1][i], rings[-1][(i + 1) % nr], ctr[(i + 1) % nr], ctr[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    parts.append(_mesh_obj(bm, "desbaste", [white], 0.0, 0))
    parts.append(lathe([(0.0, zc - 0.03), (0.012, zc - 0.03), (0.012, zc + 0.001), (0.0, zc + 0.001)], dark, verts=24))
    # canudo listrado (anéis alternados) inclinado
    import mathutils
    base = Vector((0.004, 0.0, zc - 0.02))
    d = Vector((0.25, 0.0, 1.0)).normalized()
    nseg = 20
    for k in range(nseg):
        a = base + d * (0.012 * k)
        b = base + d * (0.012 * (k + 1))
        parts.append(tube(tuple(a), tuple(b), 0.0035, red if (k // 2) % 2 == 0 else wht, verts=12))
    join(parts, "coconut_open")
    export("coconut_open")


# ---------------------------------------------------------------- abacaxi
def pineapple():
    fresh()
    skin = mat("casca", (0.72, 0.5, 0.16), 0.7)
    dark = mat("vinco", (0.35, 0.22, 0.07), 0.8)
    leaf = mat("folha", (0.22, 0.48, 0.2), 0.6)
    leaf2 = mat("folha_clara", (0.36, 0.6, 0.28), 0.6)
    parts = [anchor(skin)]
    H, R = 0.2, 0.072
    # corpo: superfície com frutilhos (cada um é um "domo" hexagonal com bico) gerados por função de relevo em espiral
    rows, per = 11, 10
    def body(u, v):
        a = 2 * math.pi * u
        prof = math.sin(math.pi * (0.06 + 0.88 * v)) ** 0.55
        z = H * v
        # coordenadas da grade espiral de frutilhos (filotaxia 8/13 aproximada por grade inclinada)
        gu = u * per + v * rows * 0.5
        gv = v * rows
        fu = gu - math.floor(gu) - 0.5
        fv = gv - math.floor(gv) - 0.5
        dome = max(0.0, 1.0 - (fu * fu + fv * fv) * 3.2)
        spike = max(0.0, 1.0 - (fu * fu + (fv - 0.25) ** 2) * 60.0)
        r = R * prof * (1.0 + 0.07 * dome + 0.05 * spike)
        return (r * math.cos(a), r * math.sin(a), z)
    def mi(u, v):
        gu = u * per + v * rows * 0.5
        gv = v * rows
        fu = gu - math.floor(gu) - 0.5
        fv = gv - math.floor(gv) - 0.5
        return 1 if (fu * fu + fv * fv) > 0.2 else 0
    parts.append(_surface(body, 160, 120, skin, "corpo", mi_fn=mi, mats=[skin, dark], sub=0))
    # coroa: 3 andares de folhas em roseta, compridas e curvadas para fora
    rnd = random.Random(5)
    for layer, (n, L, tilt) in enumerate(((7, 0.11, 0.55), (9, 0.15, 0.35), (10, 0.13, 0.15))):
        for k in range(n):
            a = 2 * math.pi * (k + layer * 0.37) / n
            bm = bmesh.new()
            bm.loops.layers.uv.new("UVMap")
            seg = 10
            left, right = [], []
            for q in range(seg + 1):
                t = q / seg
                w = 0.012 * (1 - t) ** 0.7 + 0.0008
                out = L * t * math.sin(tilt + 0.6 * t * t)
                up = L * t * math.cos(tilt + 0.6 * t * t)
                c = Vector((out * math.cos(a), out * math.sin(a), H + 0.004 + up))
                side = Vector((-math.sin(a), math.cos(a), 0)) * w
                fold = Vector((0, 0, -0.004 * (1 - t)))
                left.append(bm.verts.new(c + side + fold))
                right.append(bm.verts.new(c - side + fold))
            mid = []
            for q in range(seg + 1):
                mid.append(bm.verts.new((left[q].co + right[q].co) / 2 + Vector((0, 0, 0.002))))
            for q in range(seg):
                bm.faces.new((left[q], left[q + 1], mid[q + 1], mid[q]))
                bm.faces.new((mid[q], mid[q + 1], right[q + 1], right[q]))
            o = _mesh_obj(bm, "folha", [leaf if (k + layer) % 3 else leaf2], 0.0015, 0)
            parts.append(o)
    join(parts, "pineapple")
    export("pineapple")


# ---------------------------------------------------------------- laranja
def orange():
    fresh()
    peel = mat("casca", (0.95, 0.4, 0.04), 0.5)
    calyx = mat("calice", (0.3, 0.42, 0.15), 0.7)
    parts = [anchor(peel)]
    R = 0.04
    def shape(u, v):
        a = 2 * math.pi * u
        th = math.pi * v
        p = Vector((math.sin(th) * math.cos(a), math.sin(th) * math.sin(a), -math.cos(th)))
        # poros da casca: ruído de alta frequência (afunda), leve achatamento nos polos
        pore = noise.noise(p * 16.0) * 0.0035 + noise.noise(p * 5.0) * 0.004
        r = R * (1.0 + pore) * (1.0 - 0.06 * abs(math.cos(th)))
        return (p.x * r, p.y * r, R * 0.96 + p.z * r)
    parts.append(_surface(shape, 96, 64, peel, "laranja", sub=1))
    ztop = R * 0.96 + R * 0.94
    _sepals_small = 5
    for k in range(_sepals_small):
        a = 2 * math.pi * k / _sepals_small
        bm = bmesh.new()
        bm.loops.layers.uv.new("UVMap")
        p0 = Vector((0, 0, ztop + 0.001))
        p1 = Vector((0.009 * math.cos(a - 0.35), 0.009 * math.sin(a - 0.35), ztop - 0.0005))
        p2 = Vector((0.012 * math.cos(a), 0.012 * math.sin(a), ztop - 0.0015))
        p3 = Vector((0.009 * math.cos(a + 0.35), 0.009 * math.sin(a + 0.35), ztop - 0.0005))
        bm.faces.new([bm.verts.new(p) for p in (p0, p1, p2, p3)])
        parts.append(_mesh_obj(bm, "calice", [calyx], 0.0015, 0))
    parts.append(lathe([(0.0, 0.0), (0.0022, 0.0), (0.0018, 0.008), (0.0025, 0.0095), (0.0, 0.01)], calyx, loc=(0, 0, ztop - 0.001), verts=10))
    join(parts, "orange")
    export("orange")


# ---------------------------------------------------------------- frappé
def frappe():
    fresh()
    import mathutils
    cup = mat("copo", (0.92, 0.96, 1.0), 0.1)
    cup.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.35
    try:
        cup.surface_render_method = "BLENDED"
    except Exception:
        cup.blend_method = "BLEND"
    coffee = mat("cafe_gelado", (0.55, 0.36, 0.22), 0.5)
    cream = mat("chantilly", (0.98, 0.96, 0.92), 0.7)
    syrup = mat("calda", (0.35, 0.18, 0.08), 0.3)
    straw = mat("canudo", (0.15, 0.55, 0.85), 0.4)
    parts = [anchor(cup)]
    H = 0.15
    parts.append(lathe([(0.0, 0.0), (0.03, 0.0), (0.031, 0.003), (0.042, H), (0.044, H + 0.002), (0.041, H + 0.002), (0.039, H - 0.002), (0.028, 0.004), (0.0, 0.004)], cup, verts=40))
    parts.append(lathe([(0.0, 0.005), (0.0275, 0.005), (0.0385, H - 0.012), (0.0, H - 0.012)], coffee, verts=40))
    # chantilly: tubo em espiral cônica (bico de confeiteiro com estrias)
    pts = []
    turns = 3.2
    for i in range(140):
        t = i / 139
        a = 2 * math.pi * turns * t
        r = 0.032 * (1 - t) + 0.003
        pts.append((r * math.cos(a), r * math.sin(a), H - 0.008 + 0.045 * t))
    parts.append(sweep(pts, 0.011, cream, 10, "chantilly", taper=lambda t: 1.0 - 0.6 * t))
    # calda escorrendo por cima
    pts2 = [(0.02 * math.cos(a * 0.4), 0.02 * math.sin(a * 0.4), H + 0.035 - 0.006 * math.sin(a)) for a in [i * 0.35 for i in range(18)]]
    parts.append(sweep(pts2, 0.0025, syrup, 8, "calda"))
    parts.append(tube((0.012, 0.0, 0.02), (0.022, 0.006, H + 0.09), 0.0035, straw, verts=12))
    join(parts, "frappe")
    export("frappe")


# ---------------------------------------------------------------- copos e drinks
def _glass_mat(name="vidro", alpha=0.3):
    g = mat(name, (0.9, 0.96, 1.0), 0.05)
    g.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = alpha
    try:
        g.surface_render_method = "BLENDED"
    except Exception:
        g.blend_method = "BLEND"
    return g


def cup_plastic():
    """Copo plástico descartável (tinge-se no jogo: material tint), borda enrolada e frisos verticais."""
    fresh()
    pl = mat("tint_copo", (0.95, 0.95, 0.95), 0.4)
    parts = [anchor(pl)]
    prof = [(0.0, 0.0), (0.026, 0.0), (0.027, 0.002), (0.036, 0.11), (0.038, 0.111), (0.0385, 0.114), (0.0365, 0.115), (0.0345, 0.109), (0.025, 0.003), (0.0, 0.003)]
    o = lathe(prof, pl, verts=48)
    parts.append(o)
    for k in range(16):
        a = 2 * math.pi * k / 16
        parts.append(tube((0.0268 * math.cos(a), 0.0268 * math.sin(a), 0.004), (0.0362 * math.cos(a), 0.0362 * math.sin(a), 0.105), 0.0011, pl, verts=6))
    join(parts, "cup_plastic")
    export("cup_plastic")


def glass_juice():
    """Copo long drink de vidro com suco, gelo (cubos com cantos arredondados), rodela de laranja na borda e canudo."""
    fresh()
    gl = _glass_mat()
    juice = mat("tint_suco", (1.0, 0.7, 0.2), 0.3)
    ice = _glass_mat("gelo", 0.55)
    peel = mat("casca", (0.95, 0.55, 0.1), 0.5)
    pulp = mat("polpa", (1.0, 0.75, 0.3), 0.5)
    straw = mat("canudo", (0.95, 0.3, 0.4), 0.4)
    parts = [anchor(gl)]
    parts.append(lathe([(0.0, 0.0), (0.03, 0.0), (0.031, 0.004), (0.033, 0.14), (0.0315, 0.14), (0.0295, 0.012), (0.0, 0.012)], gl, verts=40))
    parts.append(lathe([(0.0, 0.012), (0.0294, 0.012), (0.0312, 0.11), (0.0, 0.11)], juice, verts=40))
    rnd = random.Random(3)
    for k in range(4):
        parts.append(rbox((0.022, 0.022, 0.02), (rnd.uniform(-0.01, 0.01), rnd.uniform(-0.01, 0.01), 0.09 + k * 0.012), ice, (rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(0, 1)), bevel=0.005))
    sl = lathe([(0.0, -0.004), (0.028, -0.004), (0.03, 0.0), (0.028, 0.004), (0.0, 0.004)], peel, verts=32)
    sl.location = (0.034, 0.0, 0.135)
    sl.rotation_euler = (math.radians(90), 0, 0)
    parts.append(sl)
    sl2 = lathe([(0.0, -0.0045), (0.025, -0.0045), (0.025, 0.0045), (0.0, 0.0045)], pulp, verts=32)
    sl2.location = (0.034, 0.0, 0.135)
    sl2.rotation_euler = (math.radians(90), 0, 0)
    parts.append(sl2)
    parts.append(tube((-0.008, 0.004, 0.02), (-0.02, 0.01, 0.19), 0.0032, straw, verts=12))
    join(parts, "glass_juice")
    export("glass_juice")


def cocktail():
    """Taça de drink (caipirinha/batida) com bebida, guarda-chuvinha de papel e rodela de limão."""
    fresh()
    gl = _glass_mat()
    drink = mat("tint_drink", (0.95, 0.85, 0.5), 0.3)
    lime = mat("limao", (0.45, 0.75, 0.2), 0.5)
    pulp = mat("polpa", (0.8, 0.95, 0.5), 0.5)
    paper = mat("papel", (0.95, 0.3, 0.45), 0.6)
    paper2 = mat("papel2", (0.98, 0.85, 0.3), 0.6)
    wood = mat("palito", (0.85, 0.7, 0.45), 0.7)
    parts = [anchor(gl)]
    prof = [(0.0, 0.0), (0.035, 0.0), (0.036, 0.004), (0.006, 0.01), (0.004, 0.09), (0.02, 0.105), (0.045, 0.15), (0.046, 0.152), (0.043, 0.151), (0.018, 0.11), (0.0, 0.104)]
    parts.append(lathe(prof, gl, verts=40))
    parts.append(lathe([(0.0, 0.106), (0.018, 0.112), (0.039, 0.142), (0.0, 0.142)], drink, verts=40))
    sl = lathe([(0.0, -0.004), (0.022, -0.004), (0.024, 0.0), (0.022, 0.004), (0.0, 0.004)], lime, verts=28)
    sl.location = (0.044, 0.0, 0.147)
    sl.rotation_euler = (math.radians(90), 0, 0)
    parts.append(sl)
    sl2 = lathe([(0.0, -0.0045), (0.019, -0.0045), (0.019, 0.0045), (0.0, 0.0045)], pulp, verts=28)
    sl2.location = (0.044, 0.0, 0.147)
    sl2.rotation_euler = (math.radians(90), 0, 0)
    parts.append(sl2)
    # guarda-chuvinha: palito + cúpula em gomos alternados
    top = Vector((-0.02, 0.01, 0.23))
    parts.append(tube((0.0, 0.0, 0.12), tuple(top), 0.0015, wood, verts=6))
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    n = 16
    apex = bm.verts.new(top + Vector((0, 0, 0.008)))
    rim = [bm.verts.new(top + Vector((0.035 * math.cos(2 * math.pi * k / n), 0.035 * math.sin(2 * math.pi * k / n), -0.012))) for k in range(n)]
    for k in range(n):
        f = bm.faces.new((apex, rim[k], rim[(k + 1) % n]))
        f.material_index = k % 2
    parts.append(_mesh_obj(bm, "sombrinha", [paper, paper2], 0.0015, 0))
    join(parts, "cocktail")
    export("cocktail")


def campfire_logs():
    """Lenha da fogueira: 6 toras com casca (seção irregular), pontas cortadas claras, apoiadas em pirâmide. Diâmetro ~1 m."""
    fresh()
    bark = mat("casca", (0.35, 0.24, 0.15), 0.9, tex("palm_tree_bark_diff.jpg") if os.path.exists(tex("palm_tree_bark_diff.jpg")) else None)
    cut = mat("corte", (0.82, 0.66, 0.45), 0.8)
    char = mat("carvao", (0.08, 0.07, 0.06), 0.9)
    parts = [anchor(bark)]
    rnd = random.Random(9)
    for k in range(6):
        a = 2 * math.pi * k / 6 + rnd.uniform(-0.1, 0.1)
        base = Vector((0.42 * math.cos(a), 0.42 * math.sin(a), 0.05))
        tip = Vector((0.04 * math.cos(a + 0.3), 0.04 * math.sin(a + 0.3), 0.42))
        r = rnd.uniform(0.045, 0.06)
        d = (tip - base)
        L = d.length
        bm = bmesh.new()
        bm.loops.layers.uv.new("UVMap")
        ax = d.normalized()
        sd = ax.cross(Vector((0, 0, 1))).normalized()
        up = sd.cross(ax).normalized()
        rings = []
        for i in range(9):
            t = i / 8
            ring = []
            for j in range(14):
                ang = 2 * math.pi * j / 14
                rr = r * (1.0 + 0.12 * noise.noise(Vector((t * 4.0, ang, k))))
                ring.append(bm.verts.new(base + ax * (L * t) + (sd * math.cos(ang) + up * math.sin(ang)) * rr))
            rings.append(ring)
        for i in range(8):
            for j in range(14):
                f = bm.faces.new((rings[i][j], rings[i][(j + 1) % 14], rings[i + 1][(j + 1) % 14], rings[i + 1][j]))
                f.material_index = 2 if i >= 6 else 0
        f = bm.faces.new(rings[0][::-1])
        f.material_index = 1
        f = bm.faces.new(rings[-1])
        f.material_index = 2
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        parts.append(_mesh_obj(bm, "tora", [bark, cut, char], 0.0, 0))
    join(parts, "campfire_logs")
    export("campfire_logs")


def beach_flag():
    """Bandeirinha do castelo de areia: palito de madeira e flâmula de pano ondulada (material tint)."""
    fresh()
    wood = mat("palito", (0.85, 0.7, 0.45), 0.7)
    cloth = mat("tint_flamula", (0.95, 0.3, 0.25), 0.7)
    parts = [anchor(wood)]
    parts.append(lathe([(0.0, 0.0), (0.004, 0.0), (0.003, 0.33), (0.0045, 0.335), (0.0, 0.342)], wood, verts=10))
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    n = 10
    up = []
    lo = []
    for i in range(n + 1):
        t = i / n
        x = 0.003 + 0.12 * t
        wv = 0.008 * math.sin(t * 6.0)
        up.append(bm.verts.new((x, wv, 0.33)))
        lo.append(bm.verts.new((x, wv, 0.33 - 0.07 * (1 - t))))
    for i in range(n):
        q = [up[i], up[i + 1], lo[i + 1], lo[i]]
        uq = []
        for v in q:
            if v not in uq:
                uq.append(v)
        bm.faces.new(uq)
    parts.append(_mesh_obj(bm, "flamula", [cloth], 0.002, 0))
    join(parts, "beach_flag")
    export("beach_flag")


def beach_spade():
    """Pazinha de praia de plástico: cabo com empunhadura em T e pá côncava (material tint)."""
    fresh()
    pl = mat("tint_pa", (0.3, 0.7, 1.0), 0.4)
    parts = [anchor(pl)]
    parts.append(tube((0, 0, 0.12), (0, 0, 0.36), 0.009, pl, verts=14))
    parts.append(tube((-0.04, 0, 0.36), (0.04, 0, 0.36), 0.011, pl, verts=14))
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    nu, nv = 10, 8
    grid = []
    for j in range(nv + 1):
        v = j / nv
        row = []
        for i in range(nu + 1):
            u = i / nu - 0.5
            w = 0.07 * (1 - 0.45 * v * v)
            x = u * w * 2
            z = 0.13 * (1 - v)
            y = 0.012 * (1 - (2 * u) ** 2)
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    parts.append(_mesh_obj(bm, "pa", [pl], 0.004, 1))
    join(parts, "beach_spade")
    export("beach_spade")


def boat_hull():
    """Casco de barco de pesca de madeira (4,6 m): costado de tábuas sobrepostas (trincado), proa alta, popa reta (espelho),
    borda (alcatrate) com reforço, 3 bancadas, cavernas internas e quilha. Fundo interno a 0,40 m. Material 'tint' = pintura do costado.
    Proa em +Y do Blender (-Z no Godot)."""
    fresh()
    paint = mat("tint_costado", (0.95, 0.95, 0.95), 0.5)
    trim = mat("friso", (0.15, 0.25, 0.45), 0.5)
    wood = mat("madeira", (0.6, 0.42, 0.25), 0.7, tex("oak_wood_planks_diff.jpg"))
    inner = mat("interno", (0.5, 0.34, 0.2), 0.8, tex("weathered_planks_diff.jpg") if os.path.exists(tex("weathered_planks_diff.jpg")) else tex("oak_wood_planks_diff.jpg"))
    parts = [anchor(paint)]
    L, B, D = 4.6, 1.5, 0.75
    ns, nr = 40, 14
    def sec(t):
        # t de -1 (popa) a 1 (proa)
        w = B / 2 * (1 - (max(t, 0) ** 2.2)) * (1 - 0.12 * max(-t, 0) ** 2)
        sheer = D + 0.25 * max(t, 0) ** 2 + 0.05 * max(-t, 0)
        return w, sheer
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rings = []
    for i in range(ns + 1):
        t = -1 + 2 * i / ns
        w, sh = sec(t)
        ring = []
        for j in range(nr + 1):
            s = j / nr   # 0 = quilha, 1 = borda
            ang = math.pi / 2 * s
            # seção em "V" arredondado com degraus de tábua (trincado)
            step = 0.012 * ((s * 7) % 1.0)
            x = (w * math.sin(ang) ** 0.8) + step
            z = 0.1 + (sh - 0.1) * (1 - math.cos(ang)) ** 0.9
            ring.append((x, L / 2 * t, z))
        rings.append(ring)
    vs = []
    for side in (1, -1):
        grid = [[bm.verts.new((side * p[0], p[1], p[2])) for p in ring] for ring in rings]
        for i in range(ns):
            for j in range(nr):
                q = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]) if side > 0 else (grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j])
                f = bm.faces.new(q)
                f.material_index = 1 if j >= nr - 1 else 0
                for lp in f.loops:
                    lp[uvl].uv = (lp.vert.co.y, lp.vert.co.z)
        vs.append(grid)
    # espelho de popa
    pr, pl = vs[0][0], vs[1][0]
    for j in range(nr):
        f = bm.faces.new((pr[j], pr[j + 1], pl[j + 1], pl[j]))
        f.material_index = 2
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    parts.append(_mesh_obj(bm, "casco", [paint, trim, wood], 0.035, 0))
    # fundo interno (assoalho) a 0,40 m, bancadas, alcatrate e quilha
    parts.append(box((0.7, 3.4, 0.03), (0, -0.15, 0.4), inner, bevel=0.01))
    for y in (-1.3, 0.0, 1.0):
        w, sh = sec(2 * y / L)
        parts.append(box((2 * w * 0.93, 0.22, 0.04), (0, y, sh - 0.12), wood, bevel=0.012))
    for i in range(8):
        y = -1.9 + i * 0.5
        w, sh = sec(2 * y / L)
        pts = []
        for j in range(9):
            s = j / 8
            ang = math.pi / 2 * s
            x = w * math.sin(ang) ** 0.8 - 0.05
            z = 0.12 + (sh - 0.15) * (1 - math.cos(ang)) ** 0.9
            pts.append((x, y, z))
        parts.append(sweep(pts, 0.022, wood, 6, "caverna"))
        parts.append(sweep([(-p[0], p[1], p[2]) for p in pts], 0.022, wood, 6, "caverna"))
    for side in (1, -1):
        pts = []
        for i in range(ns + 1):
            t = -1 + 2 * i / ns
            w, sh = sec(t)
            pts.append((side * (w + 0.02), L / 2 * t, sh + 0.02))
        parts.append(sweep(pts, 0.035, wood, 8, "alcatrate"))
    pts = [(0.0, L / 2 * (-1 + 2 * i / ns), 0.06 + (0.25 * max(-1 + 2 * i / ns, 0) ** 2) * (3.0 if i > ns * 0.85 else 0.0)) for i in range(ns + 1)]
    parts.append(sweep(pts, 0.05, wood, 8, "quilha"))
    join(parts, "boat_hull")
    export("boat_hull")


ALL = {"coconut_green": coconut_green, "coconut_open": coconut_open, "pineapple": pineapple, "orange": orange, "frappe": frappe,
       "cup_plastic": cup_plastic, "glass_juice": glass_juice, "cocktail": cocktail, "campfire_logs": campfire_logs,
       "beach_flag": beach_flag, "beach_spade": beach_spade, "boat_hull": boat_hull}
if __name__ == "__main__":
    for n in (sys.argv[1:] or list(ALL)):
        ALL[n]()
    print("gen_food ok")
