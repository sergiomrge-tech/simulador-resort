"""Replace the exported palm variants with the Fab "Coconut Tree" (Darmawan Pujisetyadi, CC BY 4.0).

For each variant the new tree is fitted to the original Godot palm (backup in D:/CodexTemp/palms/orig):
same trunk base, same height and the same lean direction, so the 171 level instances keep their
transforms. Diffuse + alpha are merged into one RGBA texture for an alpha-clipped, two-sided glTF.

  blender -b --factory-startup --python tools/ue58/fab_palms.py -- World_0507 World_0508 World_0509 World_0510
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

MODELS = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models'
ORIG = Path('D:/CodexTemp/palms/orig')
SRC = Path('D:/Assets/Fab/coconut_tree')
TRUNK_MAT = 'MA_bc468080f'   # trunk material prefix of the exported Godot palms
TEX = 'palm_fab_basecolor.png'   # built by the caller with PIL (diffuse RGB + alpha mask)


def old_palm(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(ORIG / (name + '.gltf')))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    trunk_idx = {}
    for o in meshes:
        trunk_idx[o.name] = {i for i, m in enumerate(o.data.materials) if m and m.name.startswith(TRUNK_MAT)}
    pts = []
    for o in meshes:
        for p in o.data.polygons:
            if p.material_index in trunk_idx[o.name]:
                pts += [o.matrix_world @ o.data.vertices[i].co for i in p.vertices]
    zmin, zmax = min(p.z for p in pts), max(p.z for p in pts)
    c = lambda s: sum(s, Vector()) / len(s)
    base = c([p for p in pts if p.z < zmin + 0.3])
    top = c([p for p in pts if p.z > zmax - 0.3])
    allz = [(o.matrix_world @ v.co).z for o in meshes for v in o.data.vertices]
    return base, top, max(allz) - min(allz)


def build(name):
    base_o, top_o, height_o = old_palm(name)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(SRC / 'source/PohonKelapa.fbx'))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bark = next(o for o in meshes if o.name == 'Bark')
    pts = [bark.matrix_world @ v.co for v in bark.data.vertices]
    zmin, zmax = min(p.z for p in pts), max(p.z for p in pts)
    c = lambda s: sum(s, Vector()) / len(s)
    base_n = c([p for p in pts if p.z < zmin + (zmax - zmin) * .03])
    top_n = c([p for p in pts if p.z > zmax - (zmax - zmin) * .03])
    allz = [(o.matrix_world @ v.co).z for o in meshes for v in o.data.vertices]
    height_n = max(allz) - min(allz)
    # Bake world transforms, join into one mesh.
    for o in meshes:
        o.data.transform(o.matrix_world)
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
    for o in [o for o in bpy.context.scene.objects if o.type != 'MESH']:
        bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    tree = bpy.context.view_layer.objects.active
    # Fit: scale to the old height, turn the lean onto the old lean, move the trunk base onto the old base.
    s = height_o / height_n
    lean_o, lean_n = (top_o - base_o).to_2d(), (top_n - base_n).to_2d()
    yaw = math.atan2(lean_o.y, lean_o.x) - math.atan2(lean_n.y, lean_n.x) if lean_o.length > .05 and lean_n.length > .05 else 0
    m = (Matrix.Translation(base_o) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Scale(s, 4) @ Matrix.Translation(-base_n))
    tree.data.transform(m)
    tree.name = name
    tree.data.name = name
    # Single alpha-clipped, two-sided material from the merged RGBA texture.
    mat = bpy.data.materials.new('MA_palm_fab')
    mat.use_nodes = True
    mat.use_backface_culling = False
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    img = nt.nodes.new('ShaderNodeTexImage')
    img.image = bpy.data.images.load(str(MODELS / TEX))
    nt.links.new(img.outputs['Color'], bsdf.inputs['Base Color'])
    rnd = nt.nodes.new('ShaderNodeMath')
    rnd.operation = 'ROUND'
    nt.links.new(img.outputs['Alpha'], rnd.inputs[0])
    nt.links.new(rnd.outputs[0], bsdf.inputs['Alpha'])
    nrm_img = nt.nodes.new('ShaderNodeTexImage')
    nrm_img.image = bpy.data.images.load(str(MODELS / 'palm_fab_normal.jpg'))
    nrm_img.image.colorspace_settings.name = 'Non-Color'
    nrm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(nrm_img.outputs['Color'], nrm.inputs['Color'])
    nt.links.new(nrm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = .7
    tree.data.materials.clear()
    tree.data.materials.append(mat)
    for p in tree.data.polygons:
        p.use_smooth = True
    bpy.ops.object.select_all(action='DESELECT')
    tree.select_set(True)
    out = MODELS / (name + '.gltf')
    bpy.ops.export_scene.gltf(filepath=str(out), export_format='GLTF_SEPARATE', use_selection=True, export_yup=True,
                              export_apply=True, export_image_format='AUTO', export_keep_originals=True)
    dims = [round(v, 2) for v in tree.dimensions]
    return {'mesh': name, 'faces': len(tree.data.polygons), 'scale': round(s, 3), 'yaw_deg': round(math.degrees(yaw), 1),
            'height_m': round(height_o, 2), 'dims_m': dims}


if __name__ == '__main__':
    names = sys.argv[sys.argv.index('--') + 1:]
    report = [build(n) for n in names]
    print('FAB_PALMS', json.dumps(report))
