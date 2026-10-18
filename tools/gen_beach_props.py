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

towel()
sandcastle()
print("gen_beach_props ok")
