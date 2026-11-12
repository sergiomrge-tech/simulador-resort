"""Poly Haven Classic Laptop (CC0), packed editable source and GLB export."""
from pathlib import Path
import requests,bpy,shutil,tempfile,json
root=Path(__file__).resolve().parents[1]
cache=root/'art/vendor/counter/classic_laptop';cache.mkdir(parents=True,exist_ok=True)
data=requests.get('https://api.polyhaven.com/files/classic_laptop',timeout=40).json()['blend']['1k']['blend']
for relative,info in [('classic_laptop.blend',data),*data.get('include',{}).items()]:
    target=cache/relative;target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        response=requests.get(info['url'],timeout=90);response.raise_for_status();target.write_bytes(response.content)
bpy.ops.wm.open_mainfile(filepath=str(cache/'classic_laptop.blend'))
for image in bpy.data.images:
    if image.source=='FILE' and not image.packed_file:
        candidate=cache/'textures'/Path(bpy.path.abspath(image.filepath)).name
        if candidate.exists():image.filepath=str(candidate);image.reload()
bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
stage=Path(tempfile.gettempdir())/'kiosk_laptop_packed.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(stage))
source=root/'art/blender/kiosk_laptop.blend';shutil.copyfile(stage,source)
bpy.ops.export_scene.gltf(filepath=str(root/'assets/models/gen/kiosk_laptop.glb'),export_format='GLB',export_apply=True)
bpy.ops.wm.open_mainfile(filepath=str(source))
assert all(im.packed_file for im in bpy.data.images if im.source=='FILE')
print('LAPTOP_PORTABLE PASS',[(o.name,[m.name for m in o.data.materials]) for o in bpy.context.scene.objects if o.type=='MESH'])
