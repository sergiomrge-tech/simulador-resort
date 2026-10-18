"""Gera uma prancha de surfe de verdade (perfil de largura/espessura/rocker + quilha) no Blender e grava assets/models/gen/surfboard.glb.
Não existe prancha CC0 decente nos pacotes gratuitos; esta é modelada, com malha lisa (subdivisão) — não é esfera achatada."""
import bpy, bmesh, math, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "models", "gen")
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
L, N, M = 2.0, 40, 20  # comprimento (m), seções, pontos por seção

def width(t):   # t 0..1 do rabo ao bico
    nose = max(0.0, 1.0 - t) if t > 0.72 else 1.0
    tail = 1.0 if t > 0.12 else (t / 0.12) ** 0.6
    w = 0.30 * math.sin(math.pi * min(1.0, 0.18 + 0.82 * t)) ** 0.55
    if t > 0.7:
        w *= max(0.0, (1.0 - (t - 0.7) / 0.3)) ** 0.5
    return max(0.012, w * (0.6 + 0.4 * tail))

def thick(t):
    return 0.03 * (0.35 + 0.65 * math.sin(math.pi * min(1.0, t * 0.9 + 0.05)) ** 0.5)

def rocker(t):
    return 0.12 * max(0.0, (t - 0.65) / 0.35) ** 2 + 0.03 * max(0.0, (0.25 - t) / 0.25) ** 2

bm = bmesh.new()
rings = []
for i in range(N + 1):
    t = i / N
    y = (t - 0.5) * L
    w, h, r = width(t), thick(t), rocker(t)
    ring = []
    for j in range(M):
        a = 2 * math.pi * j / M
        x = math.cos(a) * w
        z = math.sin(a) * h * (1.0 if math.sin(a) > 0 else 0.7) + r
        ring.append(bm.verts.new((x, y, z)))
    rings.append(ring)
for i in range(N):
    for j in range(M):
        bm.faces.new((rings[i][j], rings[i][(j + 1) % M], rings[i + 1][(j + 1) % M], rings[i + 1][j]))
for end, flip in ((rings[0], False), (rings[-1], True)):
    f = bm.faces.new(end[::-1] if flip else end)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("board"); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("surfboard", me); bpy.context.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob
ob.modifiers.new("s", "SUBSURF").levels = 1
bpy.ops.object.modifier_apply(modifier="s")
bpy.ops.object.shade_smooth()
mat = bpy.data.materials.new("board"); mat.diffuse_color = (1, 1, 1, 1); mat.use_nodes = True
ob.data.materials.append(mat)
# quilhas (3 barbatanas) como lâminas finas suavizadas
def fin(x, y, hgt, ln):
    f = bpy.data.meshes.new("fin")
    b = bmesh.new()
    v = [b.verts.new(p) for p in [(x - 0.008, y, 0.0), (x + 0.008, y, 0.0), (x + 0.004, y - ln, 0.0), (x - 0.004, y - ln, 0.0),
                                  (x, y - ln * 0.35, -hgt), (x, y - ln * 0.55, -hgt)]]
    b.faces.new((v[0], v[1], v[5], v[4])); b.faces.new((v[1], v[2], v[5])); b.faces.new((v[3], v[0], v[4])); b.faces.new((v[2], v[3], v[4], v[5]))
    b.faces.new((v[0], v[3], v[2], v[1]))
    b.to_mesh(f); b.free()
    o = bpy.data.objects.new("fin", f); bpy.context.collection.objects.link(o)
    o.data.materials.append(mat)
    return o
objs = [ob, fin(0.0, -0.78, 0.09, 0.2), fin(0.09, -0.62, 0.07, 0.16), fin(-0.09, -0.62, 0.07, 0.16)]
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.join()
# em pé (bico para cima, +Y do modelo -> +Y do glTF)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "surfboard.glb"), export_format="GLB")
print("ok")
