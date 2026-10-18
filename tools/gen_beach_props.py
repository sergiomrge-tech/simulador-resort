"""Gera no Blender o que não existe pronto de graça: toalha de praia (pano ondulado com listras e barra) e castelo de areia
(torres com ameias fundidas por remesh voxel + relevo de areia). Grava assets/models/gen/towel.glb e sandcastle.glb.
Não são caixas/cilindros crus: malha densa, relevo e (no castelo) textura de areia do projeto, se baixada."""
import bpy, bmesh, math, os, random
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "models", "gen")
SAND = os.path.join(ROOT, "assets", "tex", "coast_sand_01_diff.jpg")
os.makedirs(OUT, exist_ok=True)

def mat(name, rgb, rough=0.9, img=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if img and os.path.exists(img):
        t = m.node_tree.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(img)
        m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
    return m

def export(name):
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, name + ".glb"), export_format="GLB", export_apply=True)

def towel():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    W, L, NX, NY = 0.9, 1.9, 24, 56
    bm = bmesh.new()
    rnd = random.Random(7)
    vs = []
    for j in range(NY + 1):
        row = []
        for i in range(NX + 1):
            x = (i / NX - 0.5) * W
            y = (j / NY - 0.5) * L
            # ondulação suave do pano + leve elevação no meio (cai nas bordas)
            z = 0.012 + 0.010 * math.sin(y * 5.3 + x * 3.1) + 0.006 * math.sin(x * 11.0 + 1.3) + 0.012 * (1 - (2 * i / NX - 1) ** 2) * 0.4
            row.append(bm.verts.new((x, y, z)))
        vs.append(row)
    for j in range(NY):
        for i in range(NX):
            f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            yc = (j + 0.5) / NY
            band = (yc < 0.06 or 0.09 < yc < 0.115 or 0.885 < yc < 0.91 or yc > 0.94)
            f.material_index = 1 if band else 0
    me = bpy.data.meshes.new("towel")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("towel", me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat("pano", (0.97, 0.97, 0.97)))
    me.materials.append(mat("listra", (0.62, 0.62, 0.62)))
    bpy.context.view_layer.objects.active = ob
    s = ob.modifiers.new("sol", "SOLIDIFY")
    s.thickness = 0.014
    s.offset = -1.0
    bpy.ops.object.modifier_apply(modifier=s.name)
    bpy.ops.object.shade_smooth()
    export("towel")

def sandcastle():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    parts = []
    def add(op, **kw):
        op(**kw)
        o = bpy.context.active_object
        parts.append(o)
        return o
    # morro e muralha
    add(bpy.ops.mesh.primitive_cone_add, vertices=48, radius1=0.62, radius2=0.5, depth=0.34, location=(0, 0, 0.17))
    add(bpy.ops.mesh.primitive_cylinder_add, vertices=48, radius=0.4, depth=0.34, location=(0, 0, 0.5))
    # torre central
    add(bpy.ops.mesh.primitive_cylinder_add, vertices=40, radius=0.2, depth=0.6, location=(0, 0, 0.7))
    # torres de canto com topo cônico
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, y = math.cos(a) * 0.44, math.sin(a) * 0.44
        add(bpy.ops.mesh.primitive_cylinder_add, vertices=32, radius=0.13, depth=0.62, location=(x, y, 0.62))
        add(bpy.ops.mesh.primitive_cone_add, vertices=32, radius1=0.16, radius2=0.0, depth=0.24, location=(x, y, 1.05))
    # ameias na muralha
    for k in range(16):
        a = k * math.pi / 8
        if k % 4 == 2:
            continue
        add(bpy.ops.mesh.primitive_cube_add, size=0.09, location=(math.cos(a) * 0.4, math.sin(a) * 0.4, 0.72))
        parts[-1].rotation_euler.z = a
    # ameias na torre central
    for k in range(8):
        a = k * math.pi / 4
        add(bpy.ops.mesh.primitive_cube_add, size=0.07, location=(math.cos(a) * 0.2, math.sin(a) * 0.2, 1.03))
        parts[-1].rotation_euler.z = a
    # portão
    add(bpy.ops.mesh.primitive_cube_add, size=0.16, location=(0.4, 0, 0.55), scale=(0.5, 0.7, 1.0))
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    # funde tudo numa massa de areia contínua (remesh voxel) e dá relevo
    r = ob.modifiers.new("rem", "REMESH")
    r.mode = "VOXEL"
    r.voxel_size = 0.018
    bpy.ops.object.modifier_apply(modifier=r.name)
    tex = bpy.data.textures.new("areia", "CLOUDS")
    tex.noise_scale = 0.05
    d = ob.modifiers.new("dis", "DISPLACE")
    d.texture = tex
    d.strength = 0.012
    d.mid_level = 0.5
    bpy.ops.object.modifier_apply(modifier=d.name)
    bpy.ops.object.shade_smooth()
    # UV por projeção de cubo e material de areia
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=0.6)
    bpy.ops.object.mode_set(mode="OBJECT")
    ob.data.materials.clear()
    ob.data.materials.append(mat("areia", (0.93, 0.78, 0.52), 0.95, SAND))
    ob.location.z = 0.0
    export("sandcastle")

def _fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def _smooth(ob, levels=1):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    if levels:
        m = ob.modifiers.new("sub", "SUBSURF")
        m.levels = levels
        bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.shade_smooth()
    ob.select_set(False)

def strawhat(name, ribbon_rgb):
    """Chapéu de palha: copa abaulada + aba larga ondulada + fita colorida. Frente = -Y no Blender (+Z no glTF)."""
    _fresh()
    RAT = os.path.join(ROOT, "assets", "tex", "rattan_diff.jpg")
    # copa: esfera UV cortada embaixo, achatada
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.15, location=(0, 0, 0.0))
    crown = bpy.context.active_object
    crown.scale = (1.0, 1.1, 0.8)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new()
    bm.from_mesh(crown.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 0.0], context="VERTS")
    bm.to_mesh(crown.data)
    bm.free()
    crown.location.z = 0.0
    # aba: disco com anel, ondulação suave e espessura
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=0.27, fill_type="NGON", location=(0, 0, 0))
    brim = bpy.context.active_object
    bpy.context.view_layer.objects.active = brim
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=6)
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in brim.data.vertices:
        r = math.hypot(v.co.x, v.co.y)
        a = math.atan2(v.co.y, v.co.x)
        v.co.z = 0.0 + 0.045 * max(0.0, (r - 0.15) / 0.12) ** 1.6 * (1.0 + 0.35 * math.sin(a * 5.0))
        if r < 0.15:
            v.co.z = 0.0
    sol = brim.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.012
    bpy.ops.object.modifier_apply(modifier=sol.name)
    # fita: anel baixo em volta da copa
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.1535, depth=0.032, location=(0, 0, 0.028))
    rib = bpy.context.active_object
    rib.scale = (1.0, 1.1, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    for o in (crown, brim, rib):
        _smooth(o, 0)
    crown.data.materials.append(mat("palha", (0.98, 0.84, 0.5), 0.9, RAT))
    brim.data.materials.append(mat("palha_aba", (0.98, 0.84, 0.5), 0.9, RAT))
    rib.data.materials.append(mat("fita", ribbon_rgb, 0.6))
    for o in (crown, brim, rib):
        o.select_set(True)
    bpy.context.view_layer.objects.active = crown
    bpy.ops.object.join()
    export(name)

def cap():
    """Boné: copa em gomos + aba curva na frente (-Y). Cor = branco (o jogo tinge)."""
    _fresh()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.14, location=(0, 0, 0))
    dome = bpy.context.active_object
    dome.scale = (1.0, 1.08, 0.75)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new()
    bm.from_mesh(dome.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.005], context="VERTS")
    bm.to_mesh(dome.data)
    bm.free()
    # aba: setor de disco, curvada para baixo
    bpy.ops.mesh.primitive_circle_add(vertices=40, radius=0.17, fill_type="NGON", location=(0, -0.07, -0.005))
    vis = bpy.context.active_object
    bpy.context.view_layer.objects.active = vis
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=5)
    bpy.ops.object.mode_set(mode="OBJECT")
    bm = bmesh.new()
    bm.from_mesh(vis.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y > -0.07 + 0.0], context="VERTS")
    bm.to_mesh(vis.data)
    bm.free()
    for v in vis.data.vertices:
        v.co.z = -0.005 - 0.35 * (v.co.x ** 2) - 0.12 * max(0.0, -v.co.y - 0.07)
    sol = vis.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.01
    bpy.ops.object.modifier_apply(modifier=sol.name)
    for o in (dome, vis):
        _smooth(o, 0)
        o.data.materials.append(mat("pano_bone", (0.97, 0.97, 0.97), 0.85))
        o.select_set(True)
    bpy.context.view_layer.objects.active = dome
    bpy.ops.object.join()
    export("cap")

def sunglasses():
    """Óculos de sol: duas lentes escuras com aro e ponte. Frente = -Y."""
    _fresh()
    parts = []
    for sx in (-0.045, 0.045):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.036, depth=0.008, location=(sx, 0, 0))
        o = bpy.context.active_object
        o.rotation_euler.x = math.pi * 0.5
        o.scale = (1.15, 1.0, 1.0)
        bpy.ops.object.transform_apply(rotation=True, scale=True)
        o.data.materials.append(mat("lente", (0.05, 0.05, 0.08), 0.15))
        parts.append(o)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.038, minor_radius=0.004, major_segments=32, minor_segments=8, location=(sx, 0, 0))
        t = bpy.context.active_object
        t.rotation_euler.x = math.pi * 0.5
        t.scale = (1.15, 1.0, 1.0)
        bpy.ops.object.transform_apply(rotation=True, scale=True)
        t.data.materials.append(mat("aro", (0.95, 0.95, 0.95), 0.4))
        parts.append(t)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.004, depth=0.03, location=(0, 0, 0.012))
    br = bpy.context.active_object
    br.rotation_euler.y = math.pi * 0.5
    bpy.ops.object.transform_apply(rotation=True)
    br.data.materials.append(mat("aro2", (0.95, 0.95, 0.95), 0.4))
    parts.append(br)
    for sx in (-0.085, 0.085):
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.0035, depth=0.11, location=(sx, 0.055, 0))
        a = bpy.context.active_object
        a.rotation_euler.x = math.pi * 0.5
        bpy.ops.object.transform_apply(rotation=True)
        a.data.materials.append(mat("aro3", (0.95, 0.95, 0.95), 0.4))
        parts.append(a)
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    export("sunglasses")

towel()
sandcastle()
strawhat("strawhat_red", (0.9, 0.2, 0.2))
strawhat("strawhat_blue", (0.12, 0.5, 0.75))
strawhat("strawhat_dark", (0.18, 0.18, 0.22))
cap()
sunglasses()
print("gen_beach_props ok")
