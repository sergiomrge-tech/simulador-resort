"""Converte crab.blend (OpenGameArt, 'methodical pixel', CC0) em assets/models/gen/crab.glb (sombreamento suave por ângulo, sem animação).
uso: python3 tools/convert_crab.py <crab.blend> <saida.glb>"""
import sys, math
import bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
for ob in bpy.context.scene.objects:
    if ob.type == "MESH":
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
        ob.select_set(False)
bpy.ops.export_scene.gltf(filepath=sys.argv[2], export_format="GLB", export_animations=False, export_skins=False)
