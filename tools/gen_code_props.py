"""Gera no Blender (bpy) os props que antes eram montados por código com cilindros e caixas:
tocha tiki, poste e placa de direção, placa ABERTO, rede de vôlei, poste de luz da vila, caixa de correio, estrela-do-mar e ventilador de teto.
Tudo com chanfro, torneado (lathe), anéis de bambu, parafusos e textura de madeira do projeto. Saída: assets/models/gen/*.glb
Uso: python3 tools/gen_code_props.py [nome ...]   (sem argumentos gera todos)"""
import bpy, bmesh, math, os, sys, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "models", "gen")
TEX = os.path.join(ROOT, "assets", "tex")
os.makedirs(OUT, exist_ok=True)

def tex(n):
    p = os.path.join(TEX, n)
    return p if os.path.exists(p) else os.path.join(ROOT, "assets", "tex_hd", n)

def mat(name, rgb, rough=0.8, img=None, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if img and os.path.exists(img):
        t = m.node_tree.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(img)
        # mistura a textura com a cor-base, para dar para tingir sem perder o veio
        mix = m.node_tree.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 1.0
        mix.inputs[7].default_value = (*rgb, 1)
        m.node_tree.links.new(t.outputs["Color"], mix.inputs[6])
        m.node_tree.links.new(mix.outputs[2], b.inputs["Base Color"])
    return m

def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def export(name):
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, name + ".glb"), export_format="GLB", export_apply=True)
    print("ok", name)

def smooth(ob, levels=0):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    if levels:
        m = ob.modifiers.new("sub", "SUBSURF")
        m.levels = levels
        bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.shade_smooth()
    ob.select_set(False)

def box(size, loc, m, bevel=0.01, rot=(0, 0, 0), sub=0, uv=0.5):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.scale = size
    bpy.ops.object.transform_apply(scale=True, rotation=False)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=uv)
    bpy.ops.object.mode_set(mode="OBJECT")
    bv = ob.modifiers.new("bv", "BEVEL")
    bv.width = bevel
    bv.segments = 3
    bpy.ops.object.modifier_apply(modifier=bv.name)
    smooth(ob, sub)
    ob.data.materials.append(m)
    return ob

def lathe(profile, m, loc=(0, 0, 0), verts=40, uvscale=1.0, tilt=None):
    """Sólido de revolução: profile = [(raio, z), ...] de baixo para cima. Raio 0 fecha o topo/base."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rings = []
    for (r, z) in profile:
        if r <= 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / verts), r * math.sin(2 * math.pi * k / verts), z)) for k in range(verts)])
    for a in range(len(rings) - 1):
        ra, rb = rings[a], rings[a + 1]
        for k in range(verts):
            k2 = (k + 1) % verts
            if len(ra) == 1 and len(rb) == 1:
                continue
            if len(ra) == 1:
                f = bm.faces.new((ra[0], rb[k2], rb[k]))
            elif len(rb) == 1:
                f = bm.faces.new((ra[k], ra[k2], rb[0]))
            else:
                f = bm.faces.new((ra[k], ra[k2], rb[k2], rb[k]))
            for lp in f.loops:
                u = (lp.vert.co.x * 0 + math.atan2(lp.vert.co.y, lp.vert.co.x) / (2 * math.pi)) * uvscale * 2.0
                lp[uvl].uv = (u % 1.0 if False else u, lp.vert.co.z * uvscale * 2.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("lathe")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("lathe", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.shade_smooth()
    ob.select_set(False)
    me.materials.append(m)
    return ob

def tube(a, b, r, m, verts=24):
    """Cilindro entre dois pontos (extremos arredondados por chanfro)."""
    ax, ay, az = a
    bx, by, bz = b
    d = math.sqrt((bx - ax) ** 2 + (by - ay) ** 2 + (bz - az) ** 2)
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, vertices=verts, location=((ax + bx) / 2, (ay + by) / 2, (az + bz) / 2))
    ob = bpy.context.active_object
    dx, dy, dz = bx - ax, by - ay, bz - az
    ob.rotation_euler = (0, math.acos(dz / d), math.atan2(dy, dx))
    bv = ob.modifiers.new("bv", "BEVEL")
    bv.width = r * 0.35
    bv.segments = 3
    bpy.ops.object.modifier_apply(modifier=bv.name)
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(m)
    return ob

def join(parts, name):
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name
    ob.select_set(False)
    return ob

# ---------------------------------------------------------------- tocha tiki
def tiki_torch():
    """Haste de bambu com nós e anéis de corda, copo de barro torneado e pavio. Altura do copo: 1,80 m."""
    fresh()
    bamboo = mat("bambu", (0.9, 0.75, 0.42), 0.55, tex("bamboo_wall_diff.jpg"))
    rope = mat("corda", (0.62, 0.48, 0.3), 0.95)
    clay = mat("barro", (0.55, 0.3, 0.18), 0.8)
    soot = mat("fuligem", (0.1, 0.07, 0.05), 0.9)
    parts = []
    # haste com nós (cada gomo é um tubo com bojo suave)
    z = 0.0
    prof = []
    for g in range(6):
        h = 0.3
        for k in range(7):
            t = k / 6
            r = 0.05 - 0.004 * (z / 1.8) + 0.004 * math.sin(math.pi * t)
            prof.append((r, z + t * h))
        # nó
        prof.append((0.0575 - 0.004 * (z / 1.8), z + h + 0.006))
        z += h
    prof = [(0.0, 0.0)] + prof + [(0.0, z + 0.006)]
    parts.append(lathe(prof, bamboo, verts=28, uvscale=1.0))
    # cordas amarradas nos nós
    for zz in (0.3, 0.9, 1.5):
        parts.append(lathe([(0.0, zz - 0.04), (0.066, zz - 0.04), (0.071, zz - 0.02), (0.071, zz + 0.02), (0.066, zz + 0.04), (0.0, zz + 0.04)], rope, verts=24, uvscale=0.5))
    # copo de barro torneado
    parts.append(lathe([(0.0, 1.66), (0.05, 1.66), (0.075, 1.7), (0.11, 1.8), (0.125, 1.84), (0.118, 1.85), (0.1, 1.8), (0.07, 1.75), (0.0, 1.74)], clay, verts=36, uvscale=0.6))
    # miolo escuro e pavio
    parts.append(lathe([(0.0, 1.76), (0.095, 1.82), (0.0, 1.8)], soot, verts=28))
    parts.append(lathe([(0.0, 1.78), (0.018, 1.78), (0.018, 1.9), (0.0, 1.92)], rope, verts=12))
    join(parts, "tiki")
    export("tiki_torch")

# ---------------------------------------------------------------- poste de direção
def signpost_post():
    """Poste grosso de madeira com topo chanfrado, base em pedras e braçadeira de ferro. Altura 2,6 m."""
    fresh()
    wood = mat("madeira", (0.78, 0.55, 0.34), 0.8, tex("oak_wood_planks_diff.jpg"))
    stone = mat("pedra", (0.75, 0.73, 0.68), 0.9, tex("light_stone_diff.jpg"))
    iron = mat("ferro", (0.16, 0.16, 0.18), 0.55, metal=0.6)
    parts = []
    parts.append(lathe([(0.0, 0.0), (0.075, 0.0), (0.07, 1.2), (0.062, 2.5), (0.05, 2.6), (0.0, 2.64)], wood, verts=24, uvscale=0.8))
    rnd = random.Random(3)
    for k in range(7):
        a = k * 2 * math.pi / 7
        s = 0.1 + rnd.random() * 0.05
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=s, location=(math.cos(a) * 0.17, math.sin(a) * 0.17, 0.05 + rnd.random() * 0.03))
        o = bpy.context.active_object
        o.scale = (1.0, 1.0, 0.7)
        bpy.ops.object.shade_smooth()
        o.data.materials.append(stone)
        parts.append(o)
    for zz in (0.5, 2.0):
        parts.append(lathe([(0.0, zz - 0.03), (0.082, zz - 0.03), (0.082, zz + 0.03), (0.0, zz + 0.03)], iron, verts=24))
    join(parts, "poste")
    export("signpost_post")

def sign_arrow():
    """Tábua de direção com ponta de seta, 1,3 m + ponta (a ponta fica em +X), pintura clara para tingir; pregos e furos."""
    fresh()
    paint = mat("tinta", (1, 1, 1), 0.7, tex("oak_wood_planks_diff.jpg"))
    nail = mat("prego", (0.2, 0.2, 0.22), 0.5, metal=0.7)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    pts = [(-0.05, -0.15), (1.3, -0.15), (1.52, 0.0), (1.3, 0.15), (-0.05, 0.15)]
    t = 0.05
    top = [bm.verts.new((x, y, t / 2)) for x, y in pts]
    bot = [bm.verts.new((x, y, -t / 2)) for x, y in pts]
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((top[i], bot[i], bot[j], top[j]))
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x * 0.8, lp.vert.co.y * 0.8 + lp.vert.co.z)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("seta")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("seta", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bv = ob.modifiers.new("bv", "BEVEL")
    bv.width = 0.012
    bv.segments = 3
    bpy.ops.object.modifier_apply(modifier=bv.name)
    bpy.ops.object.shade_smooth()
    me.materials.append(paint)
    parts = [ob]
    for x in (0.03, 1.15):
        for s in (1, -1):
            parts.append(lathe([(0.0, 0.0), (0.02, 0.0), (0.016, 0.012), (0.0, 0.014)], nail, loc=(x, 0.0, s * 0.027), verts=14))
            if s < 0:
                parts[-1].rotation_euler = (math.pi, 0, 0)
    join(parts, "seta")
    # a tábua está no plano XY; em pé ela precisa ficar no plano XZ-> gira 90° em X
    ob = bpy.context.active_object
    ob.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    export("sign_arrow")

# ---------------------------------------------------------------- placa ABERTO
def open_sign():
    """Placa de balcão: tábua com moldura, dois pezinhos e corrente. Largura 0,7 m, altura 0,26 m (centro em z=0)."""
    fresh()
    wood = mat("madeira", (0.55, 0.38, 0.22), 0.75, tex("dark_wooden_planks_diff.jpg"))
    face = mat("cartaz", (0.99, 0.96, 0.86), 0.85)
    chain = mat("corrente", (0.7, 0.7, 0.72), 0.35, metal=0.9)
    parts = []
    parts.append(box((0.7, 0.04, 0.26), (0, 0, 0), wood, 0.015))
    parts.append(box((0.62, 0.012, 0.19), (0, -0.0225, 0), face, 0.008))
    parts.append(box((0.62, 0.012, 0.19), (0, 0.0225, 0), face, 0.008))
    for sx in (-1, 1):
        parts.append(tube((sx * 0.25, 0, 0.12), (sx * 0.25, 0, 0.3), 0.007, chain))
        parts.append(tube((sx * 0.25, 0, 0.3), (sx * 0.2, 0, 0.36), 0.005, chain))
    join(parts, "aberto")
    export("open_sign")

# ---------------------------------------------------------------- rede de vôlei
def volley_net():
    """Rede de vôlei de praia: 2 postes de alumínio com tampa, faixa superior, rede de malha (wireframe) e cabos. Vão de 8 m."""
    fresh()
    alu = mat("aluminio", (0.88, 0.9, 0.93), 0.35, metal=0.7)
    band = mat("faixa", (0.95, 0.95, 0.95), 0.8)
    mesh_m = mat("malha", (0.93, 0.93, 0.95), 0.9)
    pad = mat("espuma", (0.15, 0.45, 0.85), 0.9)
    parts = []
    for sx in (-4.0, 4.0):
        parts.append(lathe([(0.0, 0.0), (0.06, 0.0), (0.05, 0.05), (0.04, 2.4), (0.05, 2.45), (0.0, 2.5)], alu, loc=(sx, 0, 0), verts=24))
        parts.append(lathe([(0.0, 1.55), (0.065, 1.55), (0.065, 2.0), (0.0, 2.0)], pad, loc=(sx, 0, 0), verts=24))
        # cabos de sustentação em ângulo
        parts.append(tube((sx, 0, 2.2), (sx + (0.9 if sx > 0 else -0.9), 1.1, 0.0), 0.006, alu, verts=10))
        parts.append(tube((sx, 0, 2.2), (sx + (0.9 if sx > 0 else -0.9), -1.1, 0.0), 0.006, alu, verts=10))
    parts.append(box((8.0, 0.02, 0.08), (0, 0, 2.42), band, 0.01, uv=1.0))
    parts.append(box((8.0, 0.02, 0.05), (0, 0, 1.62), band, 0.01, uv=1.0))
    # malha: barras finas verticais e horizontais (cada barra = prisma de 1,4 cm), células de 10 cm
    bm = bmesh.new()
    t = 0.007
    for i in range(81):
        x = -4.0 + i * 0.1
        bmesh.ops.create_cube(bm, size=1.0, matrix=__import__("mathutils").Matrix.LocRotScale((x, 0, 2.0), None, (2 * t, 2 * t, 0.8)))
    for k in range(9):
        z = 1.6 + k * 0.1
        bmesh.ops.create_cube(bm, size=1.0, matrix=__import__("mathutils").Matrix.LocRotScale((0, 0, z), None, (8.0, 2 * t, 2 * t)))
    me = bpy.data.meshes.new("malha")
    bm.to_mesh(me)
    bm.free()
    net = bpy.data.objects.new("Net", me)
    bpy.context.scene.collection.objects.link(net)
    bpy.context.view_layer.objects.active = net
    net.data.materials.append(mesh_m)
    parts.append(net)
    join(parts, "rede")
    export("volley_net")

# ---------------------------------------------------------------- poste da rede elétrica
def power_pole():
    """Poste de madeira (7 m) com travessa, mãos-francesas, 3 isoladores de porcelana empilhados e transformador cinza."""
    fresh()
    wood = mat("poste", (0.52, 0.38, 0.27), 0.9, tex("weathered_planks_diff.jpg") if os.path.exists(tex("weathered_planks_diff.jpg")) else tex("oak_wood_planks_diff.jpg"))
    porc = mat("porcelana", (0.93, 0.95, 0.98), 0.25)
    iron = mat("ferro", (0.25, 0.26, 0.28), 0.5, metal=0.6)
    gray = mat("transformador", (0.5, 0.55, 0.58), 0.55, metal=0.4)
    parts = []
    parts.append(lathe([(0.0, 0.0), (0.145, 0.0), (0.13, 1.0), (0.11, 3.5), (0.095, 6.8), (0.07, 6.95), (0.0, 6.98)], wood, verts=28, uvscale=0.5))
    parts.append(box((1.5, 0.1, 0.1), (0, 0, 6.6), wood, 0.012))
    for sx in (-1, 1):
        parts.append(tube((sx * 0.1, 0.0, 6.1), (sx * 0.62, 0.0, 6.55), 0.025, iron, verts=12))
        for x in (sx * 0.6, sx * 0.0 if False else 0):
            pass
    for sx in (-0.6, 0.0, 0.6):
        parts.append(tube((sx, 0, 6.6), (sx, 0, 6.68), 0.012, iron, verts=10))
        parts.append(lathe([(0.0, 6.66), (0.03, 6.66), (0.05, 6.7), (0.03, 6.73), (0.05, 6.77), (0.03, 6.8), (0.045, 6.84), (0.0, 6.86)], porc, loc=(sx, 0, 0), verts=24))
    # transformador
    parts.append(lathe([(0.0, 5.5), (0.2, 5.5), (0.21, 5.55), (0.21, 6.05), (0.2, 6.1), (0.0, 6.1)], gray, loc=(0.32, 0.0, 0.0), verts=28))
    parts.append(tube((0.14, 0, 5.8), (0.2, 0, 5.8), 0.03, iron, verts=10))
    # degraus de subida
    for z in (2.2, 2.6, 3.0, 3.4):
        parts.append(tube((0.0, 0.11, z), (0.0, 0.22, z), 0.012, iron, verts=8))
    join(parts, "poste_luz")
    export("power_pole")

# ---------------------------------------------------------------- caixa de correio
def mailbox():
    """Caixa de correio com teto arredondado (frente = -Y), bandeirinha, porta com trinco e poste torneado. Caixa em z=1.1."""
    fresh()
    paint = mat("amarelo", (1.0, 0.82, 0.18), 0.5)
    red = mat("bandeira", (0.85, 0.15, 0.1), 0.6)
    wood = mat("poste", (0.48, 0.34, 0.22), 0.8, tex("oak_wood_planks_diff.jpg"))
    iron = mat("ferro", (0.2, 0.2, 0.22), 0.5, metal=0.7)
    parts = []
    parts.append(lathe([(0.0, 0.0), (0.06, 0.0), (0.045, 0.05), (0.04, 0.9), (0.055, 0.96), (0.0, 0.98)], wood, verts=20, uvscale=0.8))
    parts.append(box((0.22, 0.2, 0.05), (0, 0, 0.98), wood, 0.012))
    # corpo: seção em arco (meia-lua em cima)
    bm = bmesh.new()
    prof = [(-0.15, 0.0)] + [(0.15 * math.cos(math.pi - k * math.pi / 12), 0.12 + 0.15 * math.sin(k * math.pi / 12)) for k in range(13)] + [(0.15, 0.0)]
    L = 0.42
    f0 = [bm.verts.new((x, -L / 2, z)) for x, z in prof]
    f1 = [bm.verts.new((x, L / 2, z)) for x, z in prof]
    bm.faces.new(f0)
    bm.faces.new(list(reversed(f1)))
    for i in range(len(prof)):
        j = (i + 1) % len(prof)
        bm.faces.new((f0[i], f0[j], f1[j], f1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("corpo")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("corpo", me)
    ob.location = (0, 0, 1.0)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bv = ob.modifiers.new("bv", "BEVEL")
    bv.width = 0.012
    bv.segments = 3
    bpy.ops.object.modifier_apply(modifier=bv.name)
    bpy.ops.object.shade_smooth()
    me.materials.append(paint)
    parts.append(ob)
    parts.append(box((0.01, 0.1, 0.07), (0.158, 0.1, 1.2), red, 0.004))
    parts.append(tube((0.158, 0.1, 1.17), (0.158, 0.1, 1.1), 0.006, iron, verts=8))
    parts.append(lathe([(0.0, 0.0), (0.02, 0.0), (0.02, 0.012), (0.0, 0.012)], iron, loc=(0.0, -0.215, 1.1), verts=12))
    parts[-1].rotation_euler = (math.radians(90), 0, 0)
    join(parts, "caixa_correio")
    export("mailbox")

# ---------------------------------------------------------------- estrela-do-mar
def starfish():
    """Estrela-do-mar de 5 braços afilados, com relevo de pontinhos. Diâmetro 0,26 m (tingível)."""
    fresh()
    m = mat("estrela", (1, 1, 1), 0.7, tex("coast_sand_01_diff.jpg"))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    n_arm, rings, seg = 5, 14, 5
    verts = []
    for ri in range(rings + 1):
        row = []
        for a in range(n_arm * seg * 2):
            ang = a / (n_arm * seg * 2) * 2 * math.pi
            # raio de contorno em estrela: braço longo entre os vértices
            arm = 0.5 + 0.5 * math.cos(ang * n_arm)
            rad = (0.045 + 0.085 * arm ** 1.7) * (ri / rings)
            z = 0.03 * math.sin(math.pi * 0.5 * (1 - ri / rings)) * (0.6 + 0.4 * arm) + 0.004
            # relevo de pontinhos nos braços
            z += 0.004 * math.sin(rad * 160) * math.cos(ang * n_arm) ** 2 * (ri / rings)
            row.append(bm.verts.new((rad * math.cos(ang), rad * math.sin(ang), z)))
        verts.append(row)
    N = n_arm * seg * 2
    for ri in range(rings):
        for a in range(N):
            b = (a + 1) % N
            f = bm.faces.new((verts[ri][a], verts[ri][b], verts[ri + 1][b], verts[ri + 1][a])) if ri > 0 else None
            if ri == 0:
                f = bm.faces.new((verts[0][a], verts[1][a], verts[1][b])) if False else bm.faces.new((verts[1][a], verts[1][b], verts[0][a]))
    # base plana
    bot = [bm.verts.new((v.co.x, v.co.y, 0.0)) for v in verts[rings]]
    for a in range(N):
        b = (a + 1) % N
        bm.faces.new((verts[rings][b], verts[rings][a], bot[a], bot[b]))
    bm.faces.new(list(reversed(bot)))
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x * 3.5 + 0.5, lp.vert.co.y * 3.5 + 0.5)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("estrela")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("estrela", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    sm = ob.modifiers.new("sub", "SUBSURF")
    sm.levels = 1
    bpy.ops.object.modifier_apply(modifier=sm.name)
    bpy.ops.object.shade_smooth()
    me.materials.append(m)
    export("starfish")

# ---------------------------------------------------------------- ventilador de teto
def ceiling_fan():
    """Ventilador de teto de 4 pás largas de madeira, cubo torneado, haste e luminária de vidro fosco. Topo (teto) em z=0, pás em z≈-0.32, diâmetro 1,1 m.
    Pivô no eixo, para girar em torno de Y no jogo."""
    fresh()
    wood = mat("pas", (0.82, 0.6, 0.38), 0.65, tex("oak_wood_planks_diff.jpg"))
    brass = mat("latao", (0.78, 0.6, 0.3), 0.35, metal=0.85)
    glass = mat("vidro", (1.0, 0.95, 0.8), 0.25)
    parts = []
    parts.append(lathe([(0.0, 0.0), (0.07, 0.0), (0.075, -0.02), (0.04, -0.05), (0.0, -0.05)], brass, verts=28))
    parts.append(tube((0, 0, -0.04), (0, 0, -0.22), 0.012, brass, verts=14))
    parts.append(lathe([(0.0, -0.2), (0.06, -0.2), (0.085, -0.24), (0.085, -0.3), (0.06, -0.34), (0.0, -0.34)], brass, verts=32))
    def spin(ob, a):
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        ob.rotation_euler = (0, 0, a)
        bpy.ops.object.transform_apply(rotation=True)
        ob.select_set(False)
        return ob
    for k in range(4):
        a = k * math.pi / 2
        arm = box((0.16, 0.035, 0.012), (0.15, 0, -0.3), brass, 0.004)
        parts.append(spin(arm, a))
        # pá: tábua larga e abaulada, inclinada 12 graus em torno do eixo radial
        blade = box((0.44, 0.14, 0.014), (0, 0, 0), wood, 0.006)
        blade.rotation_euler = (math.radians(12), 0, 0)
        bpy.context.view_layer.objects.active = blade
        bpy.ops.object.transform_apply(rotation=True)
        blade.location = (0.37, 0, -0.305)
        parts.append(spin(blade, a))
    parts.append(lathe([(0.0, -0.34), (0.05, -0.34), (0.075, -0.38), (0.07, -0.43), (0.04, -0.46), (0.0, -0.46)], glass, verts=28))
    join(parts, "ventilador")
    export("ceiling_fan")

# ---------------------------------------------------------------- farol
def lighthouse():
    """Farol listrado de 14 m (7 faixas vermelhas e brancas) com soco de pedra, porta em arco, janelinhas, galeria com guarda-corpo,
    lanterna com 8 montantes e cúpula vermelha com para-raios. Base em z=0 (o soco fica sobre as pedras); topo da torre em z=14.
    O vidro e a luz giratória continuam no código (a luz precisa girar e acender)."""
    fresh()
    stucco = tex("white_stucco_diff.jpg")
    red = mat("faixa_vermelha", (1.0, 0.42, 0.36), 0.75, stucco)
    white = mat("faixa_branca", (1.0, 0.99, 0.96), 0.75, stucco)
    stone = mat("pedra", (0.82, 0.8, 0.76), 0.9, tex("light_stone_diff.jpg"))
    dark = mat("escuro", (0.1, 0.12, 0.16), 0.6)
    wood = mat("madeira", (0.45, 0.3, 0.18), 0.8, tex("dark_wooden_planks_diff.jpg"))
    iron = mat("ferro", (0.16, 0.17, 0.2), 0.5, metal=0.5)
    domemat = mat("cupula", (0.92, 0.2, 0.17), 0.45)
    parts = []
    # soco de pedra com degrau
    parts.append(lathe([(0.0, 0.0), (1.95, 0.0), (1.95, 0.35), (1.82, 0.4), (1.82, 0.65), (1.7, 0.7), (0.0, 0.7)], stone, verts=48, uvscale=0.4))
    # torre em 7 faixas (raio 1,6 -> 1,05) com anel de moldura entre as faixas
    bands = 7
    h = 14.0
    def rad(z):
        return 1.6 + (1.05 - 1.6) * (z / h)
    for i in range(bands):
        z0, z1 = i * h / bands, (i + 1) * h / bands
        m = red if i % 2 == 0 else white
        prof = [(0.0, z0)] + [(rad(z0 + (z1 - z0) * k / 4) + 0.012 * math.sin(math.pi * k / 4), z0 + (z1 - z0) * k / 4) for k in range(5)] + [(0.0, z1)]
        parts.append(lathe(prof, m, verts=48, uvscale=0.35))
        if i < bands - 1:
            r = rad(z1)
            parts.append(lathe([(0.0, z1 - 0.045), (r + 0.045, z1 - 0.045), (r + 0.06, z1 - 0.02), (r + 0.06, z1 + 0.02), (r + 0.045, z1 + 0.045), (0.0, z1 + 0.045)], white, verts=48, uvscale=0.3))
    # porta em arco (frente = -Y) e janelinhas
    bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.2, vertices=24, location=(0, -1.62, 1.55), rotation=(math.radians(90), 0, 0))
    arc = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    arc.data.materials.append(wood)
    parts.append(arc)
    parts.append(box((0.84, 0.2, 0.85), (0, -1.62, 1.05), wood, 0.02))
    for z in (4.0, 7.2, 10.3, 12.4):
        r = rad(z)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=0.12, vertices=20, location=(0, -(r + 0.01), z), rotation=(math.radians(90), 0, 0))
        w = bpy.context.active_object
        w.scale = (1.0, 1.0, 1.0)
        bpy.ops.object.shade_smooth()
        w.data.materials.append(dark)
        parts.append(w)
        parts.append(box((0.5, 0.05, 0.06), (0, -(r + 0.02), z - 0.2), stone, 0.01))
    # galeria (laje) e guarda-corpo
    parts.append(lathe([(0.0, 13.9), (1.62, 13.9), (1.75, 14.0), (1.75, 14.18), (0.0, 14.18)], stone, verts=48, uvscale=0.4))
    parts.append(lathe([(0.0, 14.18), (1.58, 14.18), (1.58, 14.22), (0.0, 14.22)], iron, verts=48))
    n = 24
    for k in range(n):
        a = k * 2 * math.pi / n
        parts.append(tube((math.cos(a) * 1.55, math.sin(a) * 1.55, 14.2), (math.cos(a) * 1.55, math.sin(a) * 1.55, 15.1), 0.022, iron, verts=8))
    bpy.ops.mesh.primitive_torus_add(major_radius=1.55, minor_radius=0.04, major_segments=48, minor_segments=10, location=(0, 0, 15.1))
    t1 = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    t1.data.materials.append(iron)
    parts.append(t1)
    # lanterna: 8 montantes e aros (o vidro fica no código)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        parts.append(tube((math.cos(a) * 0.86, math.sin(a) * 0.86, 14.2), (math.cos(a) * 0.86, math.sin(a) * 0.86, 15.5), 0.035, iron, verts=10))
    for z in (14.2, 15.5):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.86, minor_radius=0.05, major_segments=40, minor_segments=10, location=(0, 0, z))
        tr = bpy.context.active_object
        bpy.ops.object.shade_smooth()
        tr.data.materials.append(iron)
        parts.append(tr)
    # cúpula vermelha com beiral, bola e para-raios
    parts.append(lathe([(0.0, 15.5), (1.12, 15.5), (1.14, 15.56), (1.0, 15.62), (0.85, 15.9), (0.6, 16.2), (0.3, 16.42), (0.12, 16.5), (0.0, 16.52)], domemat, verts=40, uvscale=0.4))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, 0, 16.55))
    ball = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    ball.data.materials.append(iron)
    parts.append(ball)
    parts.append(tube((0, 0, 16.55), (0, 0, 17.4), 0.015, iron, verts=8))
    join(parts, "farol")
    export("lighthouse")

# ---------------------------------------------------------------- píer
def _pier_deck(w, l, y0, planks_mat, post_mat, rope_mat, rail=True, parts=None, post_ys=(0.0,), end_cap=False):
    """Tabuado de tábuas individuais (levemente desiguais) sobre 3 vigas e estacas com corda."""
    rnd = random.Random(11)
    n = max(2, int(round(l / 0.26)))
    pw = l / n
    for i in range(n):
        yc = y0 + (i + 0.5) * pw
        dz = rnd.uniform(-0.004, 0.004)
        parts.append(box((w, pw - 0.012, 0.075), (0, yc, 3.42 - 0.04 + dz), planks_mat, 0.008, uv=0.6))
    for sx in (-w * 0.5 + 0.12, 0.0, w * 0.5 - 0.12):
        parts.append(box((0.14, l, 0.14), (sx, y0 + l / 2, 3.25), post_mat, 0.015))

def pier_segment():
    """Módulo de 3 m do píer (frente +Y do Blender = para o mar): deck de tábuas, 2 estacas de 3,4 m com anéis de corda, mourões e corrimão de corda."""
    fresh()
    wood = mat("tabua", (0.9, 0.72, 0.52), 0.85, tex("weathered_planks_diff.jpg") if os.path.exists(tex("weathered_planks_diff.jpg")) else tex("oak_wood_planks_diff.jpg"))
    post = mat("estaca", (0.5, 0.36, 0.25), 0.9, tex("palm_tree_bark_diff.jpg") if os.path.exists(tex("palm_tree_bark_diff.jpg")) else tex("oak_wood_planks_diff.jpg"))
    rope = mat("corda", (0.66, 0.52, 0.32), 0.95)
    parts = []
    W, L = 2.4, 3.0
    _pier_deck(W, L, 0.0, wood, post, rope, parts=parts)
    for sx in (-1, 1):
        x = sx * (W * 0.5 - 0.05)
        # estaca roliça (3,4 m) com topo arredondado e anéis de corda
        parts.append(lathe([(0.0, 0.0), (0.11, 0.0), (0.13, 0.4), (0.125, 3.0), (0.13, 3.4), (0.09, 3.46), (0.0, 3.48)], post, loc=(x, 0.0, 0.0), verts=20, uvscale=0.8))
        for z in (3.1, 3.3):
            parts.append(lathe([(0.0, z - 0.02), (0.14, z - 0.02), (0.15, z), (0.14, z + 0.02), (0.0, z + 0.02)], rope, loc=(x, 0.0, 0.0), verts=20, uvscale=0.4))
        # mourão do corrimão
        parts.append(lathe([(0.0, 3.42), (0.055, 3.42), (0.05, 4.1), (0.065, 4.2), (0.0, 4.24)], post, loc=(x, 0.0, 0.0), verts=14, uvscale=0.8))
        # corrimão: dois cabos de corda ligando ao próximo mourão (+3 m), com caimento
        for zr, sag in ((4.1, 0.18), (3.75, 0.14)):
            prev = (x, 0.0, zr)
            for k in range(1, 9):
                t = k / 8
                nxt = (x, 3.0 * t, zr - sag * 4 * t * (1 - t))
                parts.append(tube(prev, nxt, 0.016, rope, verts=8))
                prev = nxt
    join(parts, "pier_segment")
    export("pier_segment")

def pier_end():
    """Plataforma final do píer (4,4 x 3 m, centrada na origem) com 4 estacas altas, bitas e corda. Deck a 3,42 m do pé das estacas."""
    fresh()
    wood = mat("tabua", (0.9, 0.72, 0.52), 0.85, tex("weathered_planks_diff.jpg") if os.path.exists(tex("weathered_planks_diff.jpg")) else tex("oak_wood_planks_diff.jpg"))
    post = mat("estaca", (0.5, 0.36, 0.25), 0.9, tex("palm_tree_bark_diff.jpg") if os.path.exists(tex("palm_tree_bark_diff.jpg")) else tex("oak_wood_planks_diff.jpg"))
    rope = mat("corda", (0.66, 0.52, 0.32), 0.95)
    iron = mat("ferro", (0.18, 0.18, 0.2), 0.5, metal=0.6)
    parts = []
    W, L = 4.4, 3.0
    _pier_deck(W, L, -L / 2, wood, post, rope, parts=parts)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (W / 2 - 0.12), sy * (L / 2 - 0.12)
            parts.append(lathe([(0.0, 0.0), (0.12, 0.0), (0.14, 0.4), (0.135, 3.0), (0.15, 3.6), (0.1, 3.7), (0.0, 3.72)], post, loc=(x, y, 0.0), verts=20, uvscale=0.8))
            parts.append(lathe([(0.0, 3.1), (0.16, 3.1), (0.17, 3.14), (0.16, 3.18), (0.0, 3.18)], rope, loc=(x, y, 0.0), verts=20, uvscale=0.4))
    # bitas de amarração
    for sx in (-1, 1):
        x = sx * (W / 2 - 0.35)
        parts.append(lathe([(0.0, 3.42), (0.09, 3.42), (0.07, 3.5), (0.06, 3.62), (0.11, 3.7), (0.11, 3.76), (0.0, 3.78)], iron, loc=(x, L / 2 - 0.4, 0.0), verts=20))
    join(parts, "pier_end")
    export("pier_end")

# ---------------------------------------------------------------- bicicleta
BIKE_COLORS = {"red": (0.8, 0.15, 0.15), "blue": (0.1, 0.4, 0.75), "yellow": (0.95, 0.75, 0.1), "green": (0.15, 0.55, 0.3), "white": (0.9, 0.9, 0.9)}

def _torus(major, minor, loc, axis_x=True, m=None, seg=48, rseg=12):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=seg, minor_segments=rseg, location=loc,
                                     rotation=(0, math.radians(90), 0) if axis_x else (0, 0, 0))
    o = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    o.data.materials.append(m)
    return o

def bike(name, rgb):
    """Bicicleta de praia: quadro diamante tubular, rodas com aro, 16 raios, pneu, pedivela com coroa, corrente, selim de couro, guidão com
    manoplas, paralamas e cestinha de vime. Frente = -Y do Blender (vira +Z no glTF), 1,7 m de comprimento, 1,05 m de altura."""
    fresh()
    fr = mat("quadro", rgb, 0.35, metal=0.5)
    rub = mat("borracha", (0.07, 0.07, 0.08), 0.8)
    chrome = mat("cromado", (0.8, 0.82, 0.85), 0.25, metal=0.95)
    leather = mat("couro", (0.35, 0.2, 0.1), 0.6)
    grip = mat("manopla", (0.9, 0.3, 0.25), 0.8)
    rattan = mat("vime", (0.85, 0.65, 0.4), 0.9, os.path.join(ROOT, "assets", "tex_hd", "rattan_diff.jpg"))
    R, F, BB, S, H1, H2 = (0.52, 0.34), (-0.52, 0.34), (0.0, 0.36), (0.22, 0.82), (-0.38, 0.88), (-0.42, 0.74)
    parts = []
    def t(a, b, r, m=fr, x=0.0):
        parts.append(tube((x, a[0], a[1]), (x, b[0], b[1]), r, m, verts=14))
    for pt in (R, F):
        parts.append(_torus(0.315, 0.036, (0, pt[0], pt[1]), True, rub, 56, 14))
        parts.append(_torus(0.275, 0.008, (0, pt[0], pt[1]), True, chrome, 56, 8))
        parts.append(lathe([(0.0, -0.05), (0.03, -0.05), (0.03, 0.05), (0.0, 0.05)], chrome, loc=(0, pt[0], pt[1]), verts=16))
        parts[-1].rotation_euler = (0, math.radians(90), 0)
        for k in range(16):
            a = k * math.pi / 8
            parts.append(tube((0.0, pt[0], pt[1]), (0.0, pt[0] + math.cos(a) * 0.275, pt[1] + math.sin(a) * 0.275), 0.0035, chrome, verts=6))
    # quadro
    for a, b in ((S, H1), (BB, H2), (BB, S), (H2, H1)):
        t(a, b, 0.0185)
    for sx in (-0.045, 0.045):
        t(S, R, 0.0115, x=sx)
        t(BB, R, 0.0115, x=sx)
        t(H2, F, 0.0125, chrome, x=sx)
    parts.append(tube((0, H2[0], H2[1]), (0, -0.40, 1.02), 0.014, chrome, verts=12))
    parts.append(tube((-0.28, -0.40, 1.02), (0.28, -0.40, 1.02), 0.012, chrome, verts=10))
    for sx in (-1, 1):
        parts.append(tube((sx * 0.28, -0.40, 1.02), (sx * 0.31, -0.37, 1.0), 0.024, grip, verts=12))
    # canote e selim
    parts.append(tube((0, S[0], S[1]), (0, S[0] + 0.02, S[1] + 0.12), 0.013, chrome, verts=10))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(0, S[0] + 0.03, S[1] + 0.14), segments=24, ring_count=12)
    sd = bpy.context.active_object
    sd.scale = (0.75, 1.5, 0.38)
    bpy.ops.object.shade_smooth()
    sd.data.materials.append(leather)
    parts.append(sd)
    # pedivela, coroa, pedais e corrente
    parts.append(lathe([(0.0, -0.01), (0.095, -0.01), (0.1, 0.0), (0.095, 0.01), (0.0, 0.01)], chrome, loc=(0.05, BB[0], BB[1]), verts=36))
    parts[-1].rotation_euler = (0, math.radians(90), 0)
    parts.append(tube((0.08, BB[0], BB[1]), (0.1, BB[0] + 0.07, BB[1] - 0.16), 0.011, chrome, verts=8))
    parts.append(tube((-0.08, BB[0], BB[1]), (-0.1, BB[0] - 0.07, BB[1] + 0.16), 0.011, chrome, verts=8))
    parts.append(box((0.1, 0.06, 0.02), (0.15, BB[0] + 0.07, BB[1] - 0.16), rub, 0.006))
    parts.append(box((0.1, 0.06, 0.02), (-0.15, BB[0] - 0.07, BB[1] + 0.16), rub, 0.006))
    parts.append(tube((0.05, BB[0], BB[1] + 0.09), (0.05, R[0], R[1] + 0.05), 0.005, rub, verts=6))
    parts.append(tube((0.05, BB[0], BB[1] - 0.09), (0.05, R[0], R[1] - 0.05), 0.005, rub, verts=6))
    # paralamas: arco de tubos sobre a metade de cima de cada roda
    for pt in (R, F):
        prev = None
        for k in range(0, 15):
            a = math.radians(25 + k * 10)
            q = (0.0, pt[0] + math.cos(a) * 0.37, pt[1] + math.sin(a) * 0.37)
            if prev:
                parts.append(tube(prev, q, 0.02, fr, verts=10))
            prev = q
    # cestinha de vime na frente
    parts.append(lathe([(0.0, 0.0), (0.12, 0.0), (0.15, 0.04), (0.17, 0.2), (0.165, 0.21), (0.0, 0.21)], rattan, loc=(0, -0.62, 0.95), verts=28, uvscale=1.2))
    parts.append(lathe([(0.17, 0.2), (0.175, 0.2), (0.175, 0.22), (0.17, 0.22)], rattan, loc=(0, -0.62, 0.95), verts=28))
    join(parts, "bike_" + name)
    export("bike_" + name)

# ---------------------------------------------------------------- vela do barco de pesca
def boat_mast():
    """Mastro de madeira (2,4 m) com vela latina triangular enfunada, retranca, costuras e cabos. Pé do mastro em z=0. Vela para -Y (popa) do Blender,
    como no código antigo (vela para +Z do glTF = frente)."""
    fresh()
    wood = mat("mastro", (0.5, 0.35, 0.22), 0.8, tex("oak_wood_planks_diff.jpg"))
    linen = mat("vela", (0.97, 0.95, 0.9), 0.95, tex("rough_linen_diff.jpg"))
    rope = mat("corda", (0.65, 0.5, 0.3), 0.95)
    parts = []
    parts.append(lathe([(0.0, 0.0), (0.04, 0.0), (0.035, 1.2), (0.026, 2.4), (0.0, 2.44)], wood, verts=16, uvscale=0.8))
    parts.append(tube((0.0, -0.02, 0.44), (0.0, -1.5, 0.58), 0.02, wood, verts=10))   # retranca
    parts.append(_sail((0, 0, 0.45), (0, 0, 2.3), (0, -1.5, 0.55), 0.22, linen))
    for k in (0.3, 0.6):
        parts.append(tube((0.0, 0.0, 2.3), (0.0, -1.5 * k, 0.55 + 0.2 * k * 0.0), 0.004, rope, verts=6)) if False else None
    parts.append(tube((0.0, 0.0, 2.35), (0.0, 1.1, 0.35), 0.008, rope, verts=8))     # estai para a proa
    parts.append(tube((0.0, 0.0, 2.35), (0.0, -1.7, 0.45), 0.008, rope, verts=8))    # cabo para a popa
    parts = [p for p in parts if p]
    join(parts, "mastro")
    export("boat_mast")

def _sail(a, b, c, billow, m, n=14):
    """Vela triangular enfunada (grade barícêntrica), dupla face, com costuras horizontais em relevo suave."""
    import mathutils
    A, B_, C = mathutils.Vector(a), mathutils.Vector(b), mathutils.Vector(c)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    grid = {}
    for i in range(n + 1):
        for j in range(n + 1 - i):
            u, v = i / n, j / n
            p = A + (B_ - A) * u + (C - A) * v
            # enfunada: bojo perpendicular ao plano (eixo X)
            p.x += billow * math.sin(math.pi * min(1.0, u + v)) * 4 * u * v * 2.2 + billow * 0.5 * math.sin(math.pi * (u + v)) * (1 - u - v) * 0.0
            p.x += 0.012 * math.sin(u * 60.0)
            grid[(i, j)] = bm.verts.new(p)
    for i in range(n):
        for j in range(n - i):
            f = bm.faces.new((grid[(i, j)], grid[(i + 1, j)], grid[(i, j + 1)]))
            if i + j + 1 < n:
                bm.faces.new((grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]))
    for f in bm.faces:
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.y * 0.5, lp.vert.co.z * 0.5)
    me = bpy.data.meshes.new("vela")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("vela", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    so = ob.modifiers.new("sol", "SOLIDIFY")
    so.thickness = 0.012
    bpy.ops.object.modifier_apply(modifier=so.name)
    bpy.ops.object.shade_smooth()
    me.materials.append(m)
    return ob

# ---------------------------------------------------------------- jangada
def jangada():
    """Jangada de pesca: 6 troncos roliços com proa levantada, 3 travessas amarradas com cordas, mastro de 5,5 m, vela grande enfunada, retranca e cabos.
    Proa em -Y do Blender (vira +Z no glTF), comprimento 6 m, largura ~1,7 m. Base (fundo dos troncos) em z=0."""
    fresh()
    log = mat("tronco", (0.62, 0.44, 0.28), 0.9, tex("palm_tree_bark_diff.jpg") if os.path.exists(tex("palm_tree_bark_diff.jpg")) else tex("oak_wood_planks_diff.jpg"))
    wood = mat("madeira", (0.55, 0.38, 0.24), 0.8, tex("oak_wood_planks_diff.jpg"))
    rope = mat("corda", (0.66, 0.5, 0.3), 0.95)
    linen = mat("vela", (1.0, 0.98, 0.94), 0.95, tex("rough_linen_diff.jpg"))
    parts = []
    def zline(y):   # elevação da proa: sobe suave nos últimos 1,2 m
        d = max(0.0, -y - 1.6)
        return 0.12 + 0.55 * (d / 1.4) ** 2 if d > 0 else 0.12
    for k in range(6):
        x = -0.6 + k * 0.24
        prev = None
        for i in range(0, 25):
            y = -3.0 + i * 0.25
            pt = (x, y, zline(y))
            if prev:
                parts.append(tube(prev, pt, 0.12 + (0.01 if k % 2 else 0.0), log, verts=14))
            prev = pt
        # topo do tronco
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(x, 3.0, 0.12), segments=14, ring_count=8)
        e = bpy.context.active_object
        bpy.ops.object.shade_smooth()
        e.data.materials.append(log)
        parts.append(e)
    for y in (-1.2, 0.4, 2.0):
        parts.append(tube((-0.85, y, 0.3), (0.85, y, 0.3), 0.045, wood, verts=12))
        for x in (-0.6 + k * 0.24 for k in range(6)):
            parts.append(lathe([(0.0, -0.035), (0.135, -0.035), (0.145, -0.01), (0.145, 0.01), (0.135, 0.035), (0.0, 0.035)], rope, loc=(x, y, 0.12), verts=16, uvscale=0.4))
            parts[-1].rotation_euler = (math.radians(90), 0, 0)
            parts[-1].location = (x, y, 0.16)
    # mastro, retranca, vela e cabos
    parts.append(lathe([(0.0, 0.2), (0.075, 0.2), (0.065, 2.5), (0.05, 5.5), (0.0, 5.58)], wood, loc=(0, -1.0, 0.0), verts=18, uvscale=0.8))
    parts.append(tube((0, -1.0, 0.7), (0, 2.5, 0.78), 0.035, wood, verts=12))
    parts.append(_sail((0, -1.0, 0.6), (0, -1.0, 5.4), (0, 2.4, 0.7), 0.35, linen, n=18))
    parts.append(tube((0, -1.0, 5.45), (0, -2.9, 0.75), 0.012, rope, verts=8))
    parts.append(tube((0, -1.0, 5.45), (0, 2.8, 0.7), 0.012, rope, verts=8))
    parts.append(tube((0, -1.0, 2.8), (0.8, -0.6, 0.3), 0.01, rope, verts=8))
    parts.append(tube((0, -1.0, 2.8), (-0.8, -0.6, 0.3), 0.01, rope, verts=8))
    join(parts, "jangada")
    export("jangada")

# ---------------------------------------------------------------- buganvília (substitui as "bolas coloridas")
BLOOM_COLORS = {"magenta": (0.86, 0.12, 0.42), "laranja": (0.95, 0.42, 0.12), "roxa": (0.62, 0.18, 0.72), "rosa": (0.96, 0.62, 0.78), "folhas": None}

def _patch(bm, M, L, W, cup, curl, fold, nu, nv, mi, uvl):
    """Folha/pétala: grade nu x nv com contorno ovalado e ponta (sin), cupulada (cup), curvada (curl) e dobrada na nervura (fold). M = matriz de posição."""
    rows = []
    for i in range(nu + 1):
        u = i / nu
        w = W * 0.5 * (math.sin(math.pi * u ** 0.8)) ** 0.85
        row = []
        for j in range(nv + 1):
            v = -1.0 + 2.0 * j / nv
            x = v * w
            y = u * L
            z = cup * (x * x) / (W * 0.5) + curl * u * u * L - fold * abs(x)
            row.append(bm.verts.new(M @ __import__("mathutils").Vector((x, y, z))))
        rows.append(row)
    for i in range(nu):
        for j in range(nv):
            f = bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
            f.material_index = mi
            for lp in f.loops:
                lp[uvl].uv = ((i + (lp.vert is rows[i + 1][j + 1].__class__ and 0)) / nu, j / nv)

def bloom_clump(name, rgb):
    """Ramo de buganvília: 3 galhinhos com espinhos, folhas ovais com nervura e, nas pontas, trios de brácteas de papel (cupuladas, onduladas)
    em volta de florzinhas brancas tubulares. rgb=None -> só folhas. Diâmetro ~0,32 m, centrado na origem. Substitui as bolinhas coloridas."""
    import mathutils
    V, Mx = mathutils.Vector, mathutils.Matrix
    fresh()
    rnd = random.Random(5)
    leaf = mat("folha", (0.2, 0.46, 0.16), 0.7)
    bract = mat("braktea", rgb or (0.8, 0.2, 0.4), 0.55)
    stem = mat("galho", (0.36, 0.24, 0.14), 0.9)
    white = mat("flor", (0.98, 0.97, 0.9), 0.5)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    tubes = []
    for b in range(3):
        a = b * 2 * math.pi / 3 + rnd.uniform(-0.3, 0.3)
        d = V((math.cos(a) * 0.85, math.sin(a) * 0.85, 0.45 + rnd.uniform(-0.15, 0.15))).normalized()
        base = V((0, 0, -0.04))
        tip = base + d * 0.15
        tubes.append((base, tip))
        q = d.to_track_quat("Y", "Z")
        # folhas alternadas ao longo do galho
        for k, t in enumerate((0.3, 0.55, 0.8)):
            for side in (-1, 1):
                if (k + b + (side > 0)) % 3 == 0 and rgb is not None:
                    continue
                pos = base + d * (0.15 * t)
                roll = Mx.Rotation(side * math.radians(70 + rnd.uniform(-12, 12)), 4, "Y")
                tilt = Mx.Rotation(math.radians(-25 + rnd.uniform(-8, 8)), 4, "X")
                M = Mx.Translation(pos) @ q.to_matrix().to_4x4() @ roll @ tilt
                sz = rnd.uniform(0.85, 1.15)
                _patch(bm, M, 0.075 * sz, 0.048 * sz, 0.12, -0.25, 0.35, 7, 4, 0, uvl)
        if rgb is None:
            # clump só de folhas: mais algumas folhas na ponta
            for r in range(3):
                M = Mx.Translation(tip) @ q.to_matrix().to_4x4() @ Mx.Rotation(r * 2.1, 4, "Y") @ Mx.Rotation(math.radians(-35), 4, "X")
                _patch(bm, M, 0.085, 0.055, 0.12, -0.2, 0.35, 7, 4, 0, uvl)
            continue
        # trio de brácteas no ápice
        for r in range(3):
            M = Mx.Translation(tip) @ q.to_matrix().to_4x4() @ Mx.Rotation(r * 2 * math.pi / 3 + rnd.uniform(-0.2, 0.2), 4, "Y") @ Mx.Rotation(math.radians(-48), 4, "X")
            sz = rnd.uniform(0.9, 1.15)
            _patch(bm, M, 0.095 * sz, 0.075 * sz, 0.55, 0.5, 0.0, 8, 6, 1, uvl)
        for r in range(3):
            tubes.append((tip, tip + d * 0.032 + V((math.cos(r * 2.1) * 0.012, math.sin(r * 2.1) * 0.012, 0))))
    me = bpy.data.meshes.new("clump")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("clump", me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(leaf)
    me.materials.append(bract)
    bpy.context.view_layer.objects.active = ob
    so = ob.modifiers.new("sol", "SOLIDIFY")
    so.thickness = 0.0025
    bpy.ops.object.modifier_apply(modifier=so.name)
    bpy.ops.object.shade_smooth()
    parts = [ob]
    for i, (a_, b_) in enumerate(tubes):
        is_flower = i >= 3 and (i - 3) % 4 != 0 and rgb is not None
        parts.append(tube(tuple(a_), tuple(b_), 0.0045 if is_flower else 0.0065, white if is_flower else stem, verts=8))
    join(parts, "buganvilia")
    export("bloom_" + name)

# ---------------------------------------------------------------- vaso pendurado e canteiro de flores
def _finish_patches(bm, mats, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for m in mats:
        me.materials.append(m)
    bpy.context.view_layer.objects.active = ob
    so = ob.modifiers.new("sol", "SOLIDIFY")
    so.thickness = 0.0025
    bpy.ops.object.modifier_apply(modifier=so.name)
    bpy.ops.object.shade_smooth()
    return ob

def _drop_to_zero(ob):
    """Move o objeto para que o ponto mais baixo fique em z=0 (e devolve o deslocamento)."""
    zmin = min((ob.matrix_world @ v.co).z for v in ob.data.vertices)
    ob.location.z -= zmin
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=True)
    ob.select_set(False)
    return -zmin

def hanging_planter():
    """Vaso de barro pendurado por 3 correntes, com folhagem em cascata (hera): 7 ramos caindo com folhas ovais alternadas e um tufo de folhas na boca.
    Pé (ponta do ramo mais longo) em z=0; centro do vaso em z = POT_Z (impresso na geração). Topo das correntes ~0,55 m acima do vaso."""
    import mathutils
    V, Mx = mathutils.Vector, mathutils.Matrix
    fresh()
    rnd = random.Random(21)
    clay = mat("barro", (0.82, 0.42, 0.28), 0.8, tex("terracotta_floor_tiles_diff.jpg") if os.path.exists(tex("terracotta_floor_tiles_diff.jpg")) else None)
    soil = mat("terra", (0.2, 0.13, 0.08), 0.95)
    leaf = mat("folha", (0.24, 0.55, 0.2), 0.7)
    leaf2 = mat("folha2", (0.34, 0.66, 0.26), 0.7)
    stem = mat("ramo", (0.3, 0.38, 0.16), 0.9)
    chain = mat("corrente", (0.3, 0.25, 0.2), 0.9)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    PZ = 1.0
    parts = []
    # tufo na boca do vaso
    for k in range(14):
        a = k * 2 * math.pi / 14 + rnd.uniform(-0.2, 0.2)
        M = Mx.Translation(V((math.cos(a) * 0.06, math.sin(a) * 0.06, PZ + 0.08))) @ Mx.Rotation(a - math.pi / 2, 4, "Z") @ Mx.Rotation(math.radians(-55 + rnd.uniform(-15, 15)), 4, "X")
        _patch(bm, M, 0.14, 0.075, 0.15, 0.25, 0.3, 7, 4, k % 2, uvl)
    # ramos caindo
    for b in range(7):
        a = b * 2 * math.pi / 7 + rnd.uniform(-0.2, 0.2)
        r0 = 0.13
        p0 = V((math.cos(a) * r0, math.sin(a) * r0, PZ + 0.03))
        L = rnd.uniform(0.35, 0.62) if b else 0.9
        prev = p0
        n = 14
        for i in range(1, n + 1):
            t = i / n
            out = r0 + 0.05 * math.sin(t * math.pi)
            q = V((math.cos(a) * out + 0.01 * math.sin(i * 1.7), math.sin(a) * out + 0.01 * math.cos(i * 1.3), PZ + 0.03 - t * (L + 0.1)))
            parts.append((prev, q))
            if i % 2 == 0 and i < n:
                for side in (-1, 1):
                    d = (q - prev).normalized()
                    M = Mx.Translation(q) @ Mx.Rotation(a + side * math.radians(80), 4, "Z") @ Mx.Rotation(math.radians(115 + rnd.uniform(-15, 15)), 4, "X")
                    sz = rnd.uniform(0.85, 1.15) * (1.0 - 0.3 * t)
                    _patch(bm, M, 0.065 * sz, 0.042 * sz, 0.15, 0.3, 0.3, 5, 3, (i + b + side) % 2, uvl)
            prev = q
        # folha-ponta
        M = Mx.Translation(prev) @ Mx.Rotation(a, 4, "Z") @ Mx.Rotation(math.radians(160), 4, "X")
        _patch(bm, M, 0.07, 0.045, 0.15, 0.2, 0.3, 5, 3, 0, uvl)
    ob = _finish_patches(bm, [leaf, leaf2], "folhagem")
    objs = [ob]
    for a_, b_ in parts:
        objs.append(tube(tuple(a_), tuple(b_), 0.0042, stem, verts=6))
    # vaso torneado + terra + correntes
    objs.append(lathe([(0.0, PZ - 0.1), (0.075, PZ - 0.1), (0.1, PZ - 0.07), (0.135, PZ + 0.02), (0.15, PZ + 0.09), (0.155, PZ + 0.1), (0.145, PZ + 0.1), (0.13, PZ + 0.09), (0.0, PZ + 0.07)], clay, verts=40, uvscale=0.9))
    objs.append(lathe([(0.0, PZ + 0.06), (0.13, PZ + 0.07), (0.0, PZ + 0.08)], soil, verts=32))
    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.4
        top = (0, 0, PZ + 0.62)
        objs.append(tube((math.cos(a) * 0.14, math.sin(a) * 0.14, PZ + 0.09), top, 0.006, chain, verts=8))
    objs.append(tube((0, 0, PZ + 0.62), (0, 0, PZ + 0.7), 0.01, chain, verts=8))
    o = join(objs, "vaso_pendurado")
    sh = _drop_to_zero(o)
    print("POT_Z", PZ + sh, "TOP", PZ + 0.7 + sh)
    export("hanging_planter")

def flowerbed():
    """Canteiro florido de 2,0 x 0,6 m: ~16 plantas de margarida/zínia (miolo torneado + 9-10 pétalas cupuladas em 6 cores) com talo curvo e roseta de folhas.
    Base em z=0 (sobre a terra do canteiro); origem no centro."""
    import mathutils
    V, Mx = mathutils.Vector, mathutils.Matrix
    fresh()
    rnd = random.Random(33)
    leaf = mat("folha", (0.2, 0.5, 0.18), 0.7)
    cols = [(0.9, 0.15, 0.2), (1.0, 0.82, 0.12), (0.95, 0.4, 0.62), (0.98, 0.97, 0.94), (1.0, 0.5, 0.1), (0.6, 0.25, 0.8)]
    pet = [mat("petala%d" % i, c, 0.55) for i, c in enumerate(cols)]
    stem = mat("talo", (0.25, 0.42, 0.15), 0.9)
    eye = mat("miolo", (0.45, 0.28, 0.08), 0.8)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    objs_t = []
    centers = []
    n = 0
    for gx in range(8):
        for gy in range(3):
            if (gx + gy) % 2:
                continue
            x = -0.88 + gx * 0.25 + rnd.uniform(-0.05, 0.05)
            y = -0.2 + gy * 0.2 + rnd.uniform(-0.05, 0.05)
            h = rnd.uniform(0.2, 0.36)
            lean = V((rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), 0))
            base = V((x, y, 0.0))
            top = base + V((0, 0, h)) + lean
            objs_t.append((base, top))
            c = n % len(pet)
            n += 1
            centers.append(top)
            # roseta de folhas
            for k in range(6):
                a = k * math.pi / 3 + rnd.uniform(-0.3, 0.3)
                M = Mx.Translation(base + V((0, 0, 0.01))) @ Mx.Rotation(a - math.pi / 2, 4, "Z") @ Mx.Rotation(math.radians(-62 + rnd.uniform(-12, 12)), 4, "X")
                _patch(bm, M, 0.13, 0.05, 0.15, -0.2, 0.3, 5, 3, 0, uvl)
            # pétalas
            npet = 10
            for k in range(npet):
                a = k * 2 * math.pi / npet
                M = Mx.Translation(top + V((0, 0, 0.004))) @ Mx.Rotation(a - math.pi / 2, 4, "Z") @ Mx.Rotation(math.radians(-80 + rnd.uniform(-8, 8)), 4, "X")
                _patch(bm, M, 0.062, 0.03, 0.5, 0.25, 0.0, 5, 3, 1 + c, uvl)
    ob = _finish_patches(bm, [leaf] + pet, "flores")
    objs = [ob]
    for a_, b_ in objs_t:
        objs.append(tube(tuple(a_), tuple(b_), 0.0055, stem, verts=7))
    for c in centers:
        objs.append(lathe([(0.0, 0.0), (0.026, 0.0), (0.03, 0.008), (0.02, 0.022), (0.0, 0.026)], eye, loc=tuple(c + V((0, 0, 0.0))), verts=16))
    join(objs, "canteiro")
    export("flowerbed")

# ---------------------------------------------------------------- bolas de verdade (praia, vôlei), gaivota, salgado, pipoca, rosácea
def _ball(name, colors, seams, radius=0.5, volley=False):
    """Bola gomada: esfera de 64x32 com painéis coloridos por material (gomos de praia ou faixas de vôlei) e costuras fundas. Raio 0,5 (ajuste a escala na engine)."""
    import mathutils
    fresh()
    mats = [mat("p%d" % i, c, 0.45) for i, c in enumerate(colors)]
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, segments=72, ring_count=36, location=(0, 0, radius))
    ob = bpy.context.active_object
    me = ob.data
    for m in mats:
        me.materials.append(m)
    n = len(colors)
    for poly in me.polygons:
        c = sum((me.vertices[i].co for i in poly.vertices), mathutils.Vector()) / len(poly.vertices)
        lon = math.atan2(c.y, c.x) % (2 * math.pi)
        lat = math.asin(max(-1, min(1, c.z / max(c.length, 1e-6))))
        if volley:
            idx = int(math.floor(lon * 6 / (2 * math.pi) * 3 + lat * 1.2)) % 3
            poly.material_index = idx % n
        else:
            if abs(lat) > math.radians(72):
                poly.material_index = 1 % n
            else:
                poly.material_index = int(lon / (2 * math.pi) * seams) % n
    # costuras: afunda os vértices perto das fronteiras dos gomos
    for v in me.vertices:
        lon = math.atan2(v.co.y, v.co.x) % (2 * math.pi)
        f = (lon / (2 * math.pi) * (seams if not volley else 18)) % 1.0
        d = min(f, 1 - f)
        if d < 0.04 and abs(v.co.z - radius) < radius * 0.96:
            v.co = v.co * 0.992
    bpy.ops.object.shade_smooth()
    parts = [ob]
    metal = mat("valvula", (0.9, 0.9, 0.92), 0.4)
    parts.append(lathe([(0.0, 0.0), (0.03, 0.0), (0.03, 0.012), (0.0, 0.012)], metal, loc=(0, 0, 2 * radius - 0.006), verts=16))
    join(parts, name)
    export(name)

def beach_ball():
    _ball("beach_ball", [(0.95, 0.25, 0.2), (0.98, 0.98, 0.96), (0.15, 0.5, 0.95), (0.98, 0.98, 0.96), (1.0, 0.82, 0.15), (0.98, 0.98, 0.96)], 6)

def volleyball():
    _ball("volleyball", [(1.0, 0.88, 0.2), (0.98, 0.98, 0.95), (0.15, 0.4, 0.85)], 18, volley=True)

def seagull(name, flying):
    """Gaivota: corpo torneado (peito cheio, cauda afilada), cabeça com bico amarelo e pinta vermelha, olhos, asas de 0,9 m em arco (ponta preta)
    ou dobradas no corpo (pousada, com pernas laranja). Cabeça para +Z do glTF (-Y do Blender)."""
    import mathutils
    V = mathutils.Vector
    fresh()
    white = mat("branco", (0.97, 0.97, 0.96), 0.8)
    gray = mat("cinza", (0.62, 0.66, 0.72), 0.8)
    black = mat("preto", (0.08, 0.08, 0.1), 0.7)
    yellow = mat("bico", (1.0, 0.75, 0.1), 0.5)
    red = mat("pinta", (0.9, 0.15, 0.1), 0.5)
    orange = mat("pernas", (1.0, 0.55, 0.15), 0.6)
    parts = []
    # corpo (eixo Z do lathe -> -Y do Blender depois de girar)
    body = lathe([(0.0, -0.33), (0.012, -0.3), (0.04, -0.2), (0.075, -0.08), (0.095, 0.03), (0.088, 0.12), (0.06, 0.19), (0.0, 0.215)], white, verts=28)
    head = lathe([(0.0, 0.14), (0.04, 0.16), (0.05, 0.2), (0.046, 0.25), (0.03, 0.285), (0.0, 0.295)], white, verts=24)
    beak = lathe([(0.0, 0.27), (0.022, 0.27), (0.016, 0.31), (0.0, 0.345)], yellow, verts=14)
    dot = lathe([(0.0, 0.318), (0.011, 0.318), (0.0, 0.33)], red, verts=10)
    dot.location.x = 0.0
    for o in (body, head, beak, dot):
        o.rotation_euler = (math.radians(90), 0, 0)
        o.rotation_euler = (math.radians(-90), 0, 0)
    objs = [body, head, beak, dot]
    # após girar -90 em X: +Z do lathe vira +Y; queremos a frente em -Y -> gira 180 em Z
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.009, segments=10, ring_count=6, location=(sx * 0.038, 0.225, 0.03))
        e = bpy.context.active_object
        e.data.materials.append(black)
        objs.append(e)
    # cauda: leque de penas
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    for k in range(5):
        a = (k - 2) * math.radians(9)
        M = mathutils.Matrix.Translation(V((0, 0.2, 0.01))) @ mathutils.Matrix.Rotation(a, 4, "Z") @ mathutils.Matrix.Rotation(math.radians(-90), 4, "Z")
        # pena: patch ao longo de +Y local; gira para apontar para +Y do corpo (cauda)
        M = mathutils.Matrix.Translation(V((0, 0.2, 0.0))) @ mathutils.Matrix.Rotation(-a, 4, "Z")
        _patch(bm, M, 0.16, 0.05, 0.1, 0.0, 0.0, 4, 2, 0, uvl)
    # asas
    def wing(sx):
        rows = []
        nu, nv = 10, 4
        span = 0.46 if flying else 0.2
        for i in range(nu + 1):
            u = i / nu
            chord = 0.17 * (1 - 0.45 * u) if flying else 0.22 * (1 - 0.5 * u)
            for_row = []
            for j in range(nv + 1):
                v = j / nv
                if flying:
                    x = sx * (0.07 + u * span)
                    zc = 0.05 + 0.1 * math.sin(u * math.pi * 0.9) - 0.06 * u * u    # arco em M
                    y = -0.02 + (0.5 - v) * chord + 0.2 * u * u * 0.5 + 0.07 * u
                    z = zc - 0.01 * v
                else:
                    x = sx * (0.085 + 0.012 * math.sin(u * 3))
                    z = 0.0 - 0.03 * u + 0.05 * (1 - v) * 0.2 + 0.05
                    y = 0.02 + u * 0.3 - v * 0.0
                    y = -0.05 + u * 0.33
                    x = sx * (0.09 + 0.02 * (v - 0.5) * 2 * 0.5)
                    z = 0.03 + (0.5 - v) * 0.1 - 0.015 * u
                for_row.append(bm.verts.new((x, y, z)))
            rows.append(for_row)
        for i in range(nu):
            for j in range(nv):
                f = bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
                f.material_index = 2 if (i >= nu - 2) else 1
                for lp in f.loops:
                    lp[uvl].uv = (0, 0)
    wing(-1)
    wing(1)
    me = bpy.data.meshes.new("asas")
    bm.to_mesh(me)
    bm.free()
    wo = bpy.data.objects.new("asas", me)
    bpy.context.scene.collection.objects.link(wo)
    for m in (white, gray, black):
        me.materials.append(m)
    bpy.context.view_layer.objects.active = wo
    so = wo.modifiers.new("sol", "SOLIDIFY")
    so.thickness = 0.008
    bpy.ops.object.modifier_apply(modifier=so.name)
    bpy.ops.object.shade_smooth()
    objs.append(wo)
    if not flying:
        for sx in (-1, 1):
            objs.append(tube((sx * 0.03, 0.0, -0.01), (sx * 0.03, 0.01, -0.12), 0.006, orange, verts=8))
            objs.append(tube((sx * 0.03, 0.01, -0.12), (sx * 0.03, -0.04, -0.125), 0.005, orange, verts=8))
    o = join(objs, name)
    # a frente (bico) está em +Y: gira 180 em Z para ficar em -Y (glTF +Z)
    o.rotation_euler = (0, 0, math.pi)
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    bpy.ops.object.transform_apply(rotation=True)
    o.select_set(False)
    if not flying:
        _drop_to_zero(o)
    export(name)

def coxinha():
    """Coxinha de frango: gota dourada (corpo largo e ponta torcida), com crosta irregular. Deitada, 9 cm."""
    fresh()
    gold = mat("crosta", (0.88, 0.58, 0.18), 0.55)
    prof = [(0.0, 0.0), (0.018, 0.002), (0.034, 0.012), (0.044, 0.03), (0.046, 0.05), (0.04, 0.07), (0.03, 0.088), (0.02, 0.102), (0.012, 0.114), (0.006, 0.122), (0.0, 0.126)]
    ob = lathe(prof, gold, verts=36)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    sm = ob.modifiers.new("sub", "SUBSURF")
    sm.levels = 2
    bpy.ops.object.modifier_apply(modifier=sm.name)
    tex_ = bpy.data.textures.new("crosta", "CLOUDS")
    tex_.noise_scale = 0.03
    d = ob.modifiers.new("dis", "DISPLACE")
    d.texture = tex_
    d.strength = 0.006
    bpy.ops.object.modifier_apply(modifier=d.name)
    bpy.ops.object.shade_smooth()
    ob.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    _drop_to_zero(ob)
    export("coxinha")

def popcorn():
    """Monte de pipoca (38 grãos irregulares) de 0,5 m para a carrocinha. Base em z=0."""
    fresh()
    rnd = random.Random(8)
    cream = mat("pipoca", (1.0, 0.96, 0.8), 0.8)
    gold = mat("casca", (0.95, 0.75, 0.25), 0.7)
    tex_ = bpy.data.textures.new("lumps", "CLOUDS")
    tex_.noise_scale = 0.35
    objs = []
    for k in range(38):
        r = 0.2 * math.sqrt(rnd.random())
        a = rnd.random() * 2 * math.pi
        x, y = math.cos(a) * r, math.sin(a) * r * 0.6
        z = 0.03 + 0.07 * (1 - r / 0.2) + rnd.random() * 0.02
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.028 * rnd.uniform(0.85, 1.25), location=(x, y, z), rotation=(rnd.random() * 3, rnd.random() * 3, rnd.random() * 3))
        o = bpy.context.active_object
        o.scale = (1, rnd.uniform(0.8, 1.1), rnd.uniform(0.75, 1.0))
        dd = o.modifiers.new("d", "DISPLACE")
        dd.texture = tex_
        dd.strength = 0.03
        bpy.ops.object.modifier_apply(modifier=dd.name)
        bpy.ops.object.shade_smooth()
        o.data.materials.append(cream if k % 5 else gold)
        objs.append(o)
    join(objs, "pipoca")
    export("popcorn")

def rose_window():
    """Rosácea de igreja de 1,2 m: aro de pedra, 8 raios, vitral azul com pétalas coloridas e miolo. Simétrica nos dois lados; eixo = Y do Blender (Z do glTF). Centro em z = 0,64."""
    fresh()
    stone = mat("pedra", (0.85, 0.83, 0.78), 0.85, tex("light_stone_diff.jpg"))
    glass = mat("vitral", (0.2, 0.42, 0.8), 0.25)
    cols = [mat("v%d" % i, c, 0.25) for i, c in enumerate([(0.9, 0.2, 0.2), (0.98, 0.8, 0.15), (0.2, 0.7, 0.4), (0.7, 0.3, 0.8)])]
    parts = []
    Zc = 0.64
    bpy.ops.mesh.primitive_torus_add(major_radius=0.58, minor_radius=0.045, major_segments=64, minor_segments=14, location=(0, 0, Zc), rotation=(math.radians(90), 0, 0))
    t = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    t.data.materials.append(stone)
    parts.append(t)
    parts.append(lathe([(0.0, -0.012), (0.55, -0.012), (0.55, 0.012), (0.0, 0.012)], glass, loc=(0, 0, Zc), verts=64))
    parts[-1].rotation_euler = (math.radians(90), 0, 0)
    for k in range(8):
        a = k * math.pi / 4
        parts.append(tube((0, 0, Zc), (math.cos(a) * 0.56, 0, Zc + math.sin(a) * 0.56), 0.016, stone, verts=10))
        b = a + math.pi / 8
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, segments=20, ring_count=10, location=(math.cos(b) * 0.33, 0, Zc + math.sin(b) * 0.33))
        pe = bpy.context.active_object
        pe.scale = (1.0, 0.12, 1.5)
        pe.rotation_euler = (0, -b + math.pi / 2, 0)
        bpy.ops.object.shade_smooth()
        pe.data.materials.append(cols[k % 4])
        parts.append(pe)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.15, minor_radius=0.025, major_segments=36, minor_segments=10, location=(0, 0, Zc), rotation=(math.radians(90), 0, 0))
    t2 = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    t2.data.materials.append(stone)
    parts.append(t2)
    join(parts, "rosacea")
    export("rose_window")

ALL = {"tiki_torch": tiki_torch, "signpost_post": signpost_post, "sign_arrow": sign_arrow, "open_sign": open_sign,
       "volley_net": volley_net, "power_pole": power_pole, "mailbox": mailbox, "starfish": starfish, "ceiling_fan": ceiling_fan,
       "lighthouse": lighthouse, "pier_segment": pier_segment, "pier_end": pier_end, "boat_mast": boat_mast, "jangada": jangada, "beach_ball": beach_ball, "volleyball": volleyball, "seagull_fly": lambda: seagull("seagull_fly", True), "seagull_perch": lambda: seagull("seagull_perch", False), "coxinha": coxinha, "popcorn": popcorn, "rose_window": rose_window, "hanging_planter": hanging_planter, "flowerbed": flowerbed,
       **{"bloom_" + k: (lambda k=k, v=v: bloom_clump(k, v)) for k, v in BLOOM_COLORS.items()},
       **{"bike_" + k: (lambda k=k, v=v: bike(k, v)) for k, v in BIKE_COLORS.items()}}
if __name__ == "__main__":
    names = sys.argv[1:] or list(ALL)
    for n in names:
        ALL[n]()
    print("gen_code_props ok")
