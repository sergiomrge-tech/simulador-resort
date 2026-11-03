"""Suitcases for the pousada luggage cart (replace the Godot export boxes World_0065/0066, plain yellow/blue cubes).
Poly Haven "Vintage Suitcase" (CC0, Maximilian Schuster) holds two suitcases side by side, already upright (width on
X, thickness on Y, handle up). Each one becomes its own GLB centred on the origin and scaled uniformly to the height
of the box it replaces (40 / 30 cm), so it drops into the old mesh's frame.
D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/prep_luggage.py
Output: D:/Assets/Mare/luggage_big/luggage_big.glb, D:/Assets/Mare/luggage_small/luggage_small.glb."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from gen_custom_furniture import export, reset  # noqa: E402

SRC = Path('D:/Assets/PolyHaven/vintage_suitcase/vintage_suitcase_2k.gltf')
JOBS = [('luggage_big', 'vintage_suitcase_01', .40), ('luggage_small', 'vintage_suitcase_02', .30)]


def one(slug, prefix, height):
    reset()
    bpy.ops.import_scene.gltf(filepath=str(SRC))
    for o in list(bpy.context.scene.objects):
        if o.type == 'MESH' and not o.name.startswith(prefix):
            bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:                      # bake the parent transforms before joining
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    for o in [o for o in bpy.context.scene.objects if o.type != 'MESH']:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    ob = bpy.context.active_object
    pts = [v.co for v in ob.data.vertices]      # vertex bounds (bound_box is stale after the join)
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    k = height / (hi.z - lo.z)
    centre = (lo + hi) / 2
    for v in ob.data.vertices:
        v.co = (v.co - centre) * k
    ob.matrix_world.identity()
    ob.name = ob.data.name = slug
    size = (hi - lo) * k
    print(slug, 'size', [round(v, 3) for v in size])
    export(slug, f'Pousada luggage ({prefix}, Poly Haven CC0)')


if __name__ == '__main__':
    for slug, prefix, h in JOBS:
        one(slug, prefix, h)
