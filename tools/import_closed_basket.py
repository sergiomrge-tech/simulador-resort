"""Close the Poly Haven wicker_basket_02 lid; retain scanned mesh and texture.

Original CC0 source: https://polyhaven.com/a/wicker_basket_02
Uses the existing fetch_assets.py download. Outputs packed editable .blend/GLB.
"""
from pathlib import Path
import sys
import bpy
from mathutils import Matrix, Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_coastal_traffic import save

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'assets/models/wicker_basket_02/wicker_basket_02.gltf'))
base = bpy.data.objects['wicker_basket_02_base']
lid = bpy.data.objects['wicker_basket_02_lid']
base_center = sum((base.matrix_world @ Vector(v) for v in base.bound_box), Vector()) / 8
lid_center = sum((Vector(v) for v in lid.bound_box), Vector()) / 8
top = max((base.matrix_world @ Vector(v)).z for v in base.bound_box)
bottom = min(v[2] for v in lid.bound_box)
# The source deliberately leans the separate lid against an open basket.
# Reset its imported rotation, then fit the cap over the existing rim.
lid.matrix_world = Matrix.Translation((base_center.x-lid_center.x,
                                     base_center.y-lid_center.y,
                                     top-bottom-.018))
for material in bpy.data.materials:
    material.use_backface_culling = False
bpy.context.view_layer.update()
assert abs(lid.matrix_world.to_euler().x) < .001
save('wicker_basket_closed')
