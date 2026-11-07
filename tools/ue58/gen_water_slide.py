"""UE water slide: the Grand Hotel slide of tools/gen_hotel.py with a 4.5 m run-out (instead of 3 m) so the chute ends
about 2 m over the pool (Sergio, 07/11: "a saída precisa ser na água"). Materials and images get the model's own prefix
(the importer reuses same-named assets from the whole project) and the image is packed (glTF uses the file name).
Output: D:/Assets/Mare/mare_water_slide/mare_water_slide.glb + info.json (import: mare_custom one/import).
Run: D:/CodexTemp/claude/bpy-env/Scripts/python.exe -I tools/ue58/gen_water_slide.py"""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import bpy  # noqa: E402  (bpy before bmesh/mathutils in this package)
import gen_hotel  # noqa: E402

SLUG = 'mare_water_slide'
DEST = f'D:/Assets/Mare/{SLUG}'
RUN = 4.5


def export(_name):
    for m in bpy.data.materials:
        if not m.name.startswith(SLUG):
            m.name = f'{SLUG}_{m.name}'
    for img in bpy.data.images:
        if img.type == 'IMAGE' and img.size[0] > 0:
            img.pack()
            img.name = f'{SLUG}_{os.path.splitext(img.name)[0]}'
            img.filepath = ''
    os.makedirs(DEST, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=f'{DEST}/{SLUG}.glb', export_format='GLB', export_apply=True)


gen_hotel.SLIDE_RUN = RUN
# The deck's oak planks (Poly Haven CC0): the Godot asset folders are not on this disk, the library copy is.
_tex = gen_hotel.tex
gen_hotel.tex = lambda n: 'D:/Assets/PolyHaven/oak_wood_planks/oak_wood_planks_diff_1k.jpg' if n.startswith('oak_wood_planks_diff') else _tex(n)
gen_hotel.export = export
gen_hotel.water_slide()
json.dump({'slug': SLUG, 'name': 'Tobogã do Grand Hotel', 'gltf': f'{SLUG}.glb', 'authors': {'Maré Alta (bpy)': 'model'},
           'license': 'Original model; textures CC0 1.0 Poly Haven', 'source': 'tools/ue58/gen_water_slide.py'},
          open(f'{DEST}/info.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', RUN)
