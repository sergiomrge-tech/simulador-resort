"""Suaviza animais Quaternius (Animal Pack Vol.2, CC0) a partir dos .blend (o OBJ perde as cores): remove esqueleto/animação,
Catmull-Clark nível 2 e sombreamento suave. Saída <saida>/<nome minúsculo>.glb (chave "g:cat", "g:dog", "g:eagle").
uso: python3 tools/smooth_animals.py <pasta_Blends> <saida> Cat Dog Eagle
"""
import sys, os
import bpy

def to_principled():
    """O pacote usa nós Diffuse (o exportador glTF não vê a cor): troca por Principled com a mesma cor."""
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        col = None
        for nd in m.node_tree.nodes:
            if nd.type == "BSDF_DIFFUSE":
                col = tuple(nd.inputs["Color"].default_value)
        if col is None:
            continue
        m.node_tree.nodes.clear()
        bs = m.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        bs.inputs["Base Color"].default_value = col
        bs.inputs["Roughness"].default_value = 0.85
        out = m.node_tree.nodes.new("ShaderNodeOutputMaterial")
        m.node_tree.links.new(bs.outputs["BSDF"], out.inputs["Surface"])

def process(src, out, name):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(src, name + ".blend"))
    to_principled()
    for ob in list(bpy.context.scene.objects):
        if ob.type == "MESH":
            for md in list(ob.modifiers):
                if md.type == "ARMATURE":
                    ob.modifiers.remove(md)
            ob.parent = None
            bpy.context.view_layer.objects.active = ob
            ob.select_set(True)
            m = ob.modifiers.new("sub", "SUBSURF")
            m.levels = 2
            m.render_levels = 2
            bpy.ops.object.modifier_apply(modifier=m.name)
            bpy.ops.object.shade_smooth()
            ob.select_set(False)
        elif ob.type == "ARMATURE":
            bpy.data.objects.remove(ob, do_unlink=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, name.lower() + ".glb"), export_format="GLB", export_animations=False, export_skins=False)

if __name__ == "__main__":
    a = sys.argv[1:]
    src, out, names = a[0], a[1], a[2:]
    os.makedirs(out, exist_ok=True)
    for n in names:
        process(src, out, n)
        print("suavizado", n)
