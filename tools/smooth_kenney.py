"""Suaviza os modelos Kenney (CC0) no Blender: Catmull-Clark nas peças orgânicas, sombreamento suave por ângulo nas duras,
e grava GLB com a textura embutida (o original aponta para Textures/colormap.png externo).
uso: python3 tools/smooth_kenney.py <pasta_do_pack/GLB format> <saida> nome1 nome2 ...
"""
import sys, os, math
import bpy

HARD = ("plate", "bowl", "utensil", "cooking", "barrel", "crate", "boat", "ship", "flag", "paddle", "palm", "structure")

def process(src, out, name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(src, name + ".glb"))
    hard = name.startswith(HARD)
    for ob in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        if not hard:
            m = ob.modifiers.new("sub", "SUBSURF")
            m.levels = 2
            m.render_levels = 2
            m.subdivision_type = "CATMULL_CLARK"
            bpy.ops.object.modifier_apply(modifier=m.name)
            bpy.ops.object.shade_smooth()
        else:
            m = ob.modifiers.new("sub", "SUBSURF")
            m.levels = 1
            m.render_levels = 1
            bpy.ops.object.modifier_apply(modifier=m.name)
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        ob.select_set(False)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, name + ".glb"), export_format="GLB", export_image_format="AUTO")

if __name__ == "__main__":
    a = sys.argv[1:]
    src, out, names = a[0], a[1], a[2:]
    os.makedirs(out, exist_ok=True)
    for n in names:
        process(src, out, n)
        print("suavizado", n)
