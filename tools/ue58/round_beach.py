"""Round the two square beach corners of the resort ground tile (World_0000).

The Godot ground tile is a rectangle whose beach keeps its height right up to the tile edge, so the
sand ended in square corners sticking into the sea. Near both ends the shore is pulled back along a
smooth curve: every beach vertex takes the height the central beach has SHIFT further seaward, and
only ever goes down (inland ground, paths and buildings untouched). Original copied to
D:/CodexTemp/ground/orig first; materials/images restored from it so the UE material reuse holds.

  blender -b --factory-startup --python tools/ue58/round_beach.py
"""
import json
import math
import shutil
from pathlib import Path

import bpy

MODELS = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models'
BACKUP = Path('D:/CodexTemp/ground/orig')
NAME = 'World_0000'
START, END = 7500, 13000       # |x| (cm) where the shore starts to curve back / tile edge
PULL = 3600                    # how far (cm) the shore recedes at the tile edge
BEACH_Y = 500                  # only vertices south of this UE y (cm) are touched


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    src = MODELS / (NAME + '.gltf')
    if not (BACKUP / src.name).exists():
        shutil.copy2(src, BACKUP / src.name)
        for buf in json.loads(src.read_text(encoding='utf-8')).get('buffers', []):
            shutil.copy2(MODELS / buf['uri'], BACKUP / buf['uri'])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(BACKUP / src.name))
    obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    mw = obj.matrix_world
    inv = mw.inverted()
    world = [mw @ v.co for v in obj.data.vertices]
    # Central beach profile z(y) (UE cm), from the middle third of the tile.
    bins = {}
    for p in world:
        x, y, z = p.x * 100, -p.y * 100, p.z * 100
        if abs(x) < 6000 and y < BEACH_Y + 3000:
            bins.setdefault(int(y // 100), []).append(z)
    profile = {k: sorted(v)[len(v) // 2] for k, v in bins.items()}
    keys = sorted(profile)

    def z_mid(y):
        k = int(y // 100)
        if k <= keys[0]:
            return profile[keys[0]] - (keys[0] - k) * 2      # keeps sloping down offshore
        if k >= keys[-1]:
            return profile[keys[-1]]
        while k not in profile:
            k -= 1
        return profile[k]

    moved = 0
    for v, p in zip(obj.data.vertices, world):
        x, y, z = p.x * 100, -p.y * 100, p.z * 100
        if y > BEACH_Y:
            continue
        # Outside the curved ends only stray sand bars below the shore are trimmed to the profile.
        if abs(x) < START and y > -1500:
            continue
        u = min(1, max(0, (abs(x) - START) / (END - START)))
        shift = PULL * (1 - math.sqrt(max(0, 1 - u * u)))   # circular arc: tangent to the straight shore
        target = z_mid(y - shift)
        if target < z - 1:
            p.z = target / 100
            v.co = inv @ p
            moved += 1
    obj.data.update()
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(src), export_format='GLTF_SEPARATE', use_selection=True, export_yup=True,
                              export_apply=True, export_image_format='NONE')
    old = json.loads((BACKUP / src.name).read_text(encoding='utf-8'))
    new = json.loads(src.read_text(encoding='utf-8'))
    by_name = {m['name']: m for m in old.get('materials', [])}
    new['materials'] = [by_name.get(m['name'], m) for m in new.get('materials', [])]
    for key in ('images', 'textures', 'samplers'):
        if key in old:
            new[key] = old[key]
    src.write_text(json.dumps(new), encoding='utf-8')
    print('ROUND_BEACH', json.dumps({'vertices': len(world), 'lowered': moved}))


if __name__ == '__main__':
    main()
