"""Replace the faceted village almond trees with the Fab "HighPoly Tree Model" (Next Spring, CC BY 4.0).

Each variant keeps the original trunk base (0,0,0 in the exported glTF) and gets the new tree scaled
to the original height times GROW, turned by a per-variant yaw so the 16 instances do not repeat.
Textures are copied next to the glTFs as hp_tree_*.png.

  blender -b --factory-startup --python tools/ue58/fab_trees.py -- World_0504 World_0505 World_1206
"""
import json
import math
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

MODELS = Path(__file__).resolve().parents[2] / 'unreal/MareAlta/SourceArt/Models'
SRC = Path('D:/Assets/Fab/highpoly_tree/HighPoly Tree Model')
BACKUP = Path('D:/CodexTemp/trees/orig')
GROW = 1.35            # the Godot almonds were short (6 m); real shade trees stand a little taller
YAW = {'World_0504': 0, 'World_0505': 125, 'World_1206': 245}
TEXTURES = {'hp_tree_leaf.png': 'T_HP_Tree_Leaf.PNG', 'hp_tree_trunk.png': 'T_HP_Tree_Trunk.PNG',
            'hp_tree_trunk_normal.png': 'T_HP_Tree_Trunk_normal.PNG'}


def backup(name):
    BACKUP.mkdir(parents=True, exist_ok=True)
    src = MODELS / (name + '.gltf')
    if not (BACKUP / src.name).exists():
        shutil.copy2(src, BACKUP / src.name)
        for buf in json.loads(src.read_text(encoding='utf-8')).get('buffers', []):
            shutil.copy2(MODELS / buf['uri'], BACKUP / buf['uri'])
    return BACKUP / src.name


def old_height(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    zs = [(o.matrix_world @ v.co).z for o in bpy.context.scene.objects if o.type == 'MESH' for v in o.data.vertices]
    return max(zs) - min(zs), min(zs)


def image_node(nt, file, non_color=False):
    node = nt.nodes.new('ShaderNodeTexImage')
    node.image = bpy.data.images.load(str(MODELS / file))
    if non_color:
        node.image.colorspace_settings.name = 'Non-Color'
    return node


def build(name):
    height_o, base_z = old_height(backup(name))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(SRC / 'Model/SM_HP_Tree.FBX'))
    for o in [o for o in bpy.context.scene.objects if o.name.startswith('UCX_') or o.type != 'MESH']:
        bpy.data.objects.remove(o)
    tree = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    tree.data.transform(tree.matrix_world)
    tree.matrix_world = Matrix.Identity(4)
    pts = [v.co for v in tree.data.vertices]
    zmin = min(p.z for p in pts)
    zmax = max(p.z for p in pts)
    foot = [p for p in pts if p.z < zmin + (zmax - zmin) * .02]
    base = sum(foot, Vector()) / len(foot)
    s = height_o * GROW / (zmax - zmin)
    tree.data.transform(Matrix.Translation((0, 0, base_z)) @ Matrix.Rotation(math.radians(YAW[name]), 4, 'Z') @ Matrix.Scale(s, 4)
                        @ Matrix.Translation((-base.x, -base.y, -zmin)))
    tree.name = tree.data.name = name
    for mat in tree.data.materials:
        mat.use_nodes = True
        nt = mat.node_tree
        for n in list(nt.nodes):
            if n.type != 'OUTPUT_MATERIAL':
                nt.nodes.remove(n)
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        nt.links.new(bsdf.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
        bsdf.inputs['Roughness'].default_value = .75
        if 'Leaf' in mat.name:
            mat.name = 'MA_hp_tree_leaf'
            mat.use_backface_culling = False
            img = image_node(nt, 'hp_tree_leaf.png')
            nt.links.new(img.outputs['Color'], bsdf.inputs['Base Color'])
            rnd = nt.nodes.new('ShaderNodeMath')
            rnd.operation = 'ROUND'
            nt.links.new(img.outputs['Alpha'], rnd.inputs[0])
            nt.links.new(rnd.outputs[0], bsdf.inputs['Alpha'])
        else:
            mat.name = 'MA_hp_tree_trunk'
            img = image_node(nt, 'hp_tree_trunk.png')
            nt.links.new(img.outputs['Color'], bsdf.inputs['Base Color'])
            nimg = image_node(nt, 'hp_tree_trunk_normal.png', True)
            nrm = nt.nodes.new('ShaderNodeNormalMap')
            nt.links.new(nimg.outputs['Color'], nrm.inputs['Color'])
            nt.links.new(nrm.outputs['Normal'], bsdf.inputs['Normal'])
    bpy.ops.object.select_all(action='DESELECT')
    tree.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(MODELS / (name + '.gltf')), export_format='GLTF_SEPARATE', use_selection=True,
                              export_yup=True, export_apply=True, export_image_format='AUTO', export_keep_originals=True)
    return {'mesh': name, 'faces': len(tree.data.polygons), 'scale': round(s, 4), 'height_m': round(height_o * GROW, 2),
            'dims_m': [round(v, 2) for v in tree.dimensions]}


if __name__ == '__main__':
    for out, src in TEXTURES.items():
        shutil.copy2(SRC / 'Textures' / src, MODELS / out)
    report = [build(n) for n in sys.argv[sys.argv.index('--') + 1:]]
    print('FAB_TREES', json.dumps(report))
