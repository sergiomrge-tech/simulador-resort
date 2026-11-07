"""Preserve downloaded detailed furniture in packed Blender sources + runtime GLB.

Geometry/UVs/materials are retained; runtime images limited to 1K. No decimation.
"""
from pathlib import Path
import sys, tempfile, shutil, json
import bpy, bmesh
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from fetch_home_assets import HOME_ASSETS
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/models/gen'
for slug, name in HOME_ASSETS.items():
    if len(sys.argv)>1 and slug not in sys.argv[1:]:continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.import_scene.gltf(filepath=str(ROOT/f'assets/models/{slug}/{slug}.gltf'))
    if slug == 'television_02':
        # Reuse the actual curved CRT surface, never place a flat screen over it.
        original=next(o for o in bpy.context.scene.objects if o.type=='MESH')
        screen=original.copy();screen.data=original.data.copy();screen.name='HomeTVScreen'
        bpy.context.collection.objects.link(screen)
        bm=bmesh.new();bm.from_mesh(screen.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00005)
        unseen=set(bm.verts);glass=None
        while unseen:
            seed=unseen.pop();group={seed};todo=[seed]
            while todo:
                v=todo.pop()
                for e in v.link_edges:
                    w=e.other_vert(v)
                    if w in unseen:unseen.remove(w);group.add(w);todo.append(w)
            if len(group)>200 and max(v.co.y for v in group)<-.085:
                glass=group
        assert glass is not None, 'CRT connected glass component missing'
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if v not in glass],context='VERTS')
        bm.to_mesh(screen.data);bm.free()
        assert len(screen.data.polygons)>10, 'CRT front selection is empty'
        # Separate powered-off glass and remove its copy from the TV body.
        # A millimetric overlay z-fights against the original CRT under Vulkan.
        off=screen.copy();off.data=screen.data.copy();off.name='HomeTVGlassOff'
        bpy.context.collection.objects.link(off)
        body=bmesh.new();body.from_mesh(original.data)
        bmesh.ops.remove_doubles(body,verts=list(body.verts),dist=.00005)
        glass_coords={tuple(round(float(c),5) for c in v.co) for v in screen.data.vertices}
        bmesh.ops.delete(body,geom=[v for v in body.verts if tuple(round(float(c),5) for c in v.co) in glass_coords],context='VERTS')
        body.to_mesh(original.data);body.free()
        for uv in screen.data.uv_layers:
            for loop in screen.data.loops:
                v=screen.data.vertices[loop.vertex_index].co
                uv.data[loop.index].uv=((v.x+.1601)/.3165,(v.z-.1402)/.2372)
        screen.data.materials.clear()
        mat=bpy.data.materials.new('home_screen');mat.diffuse_color=(.01,.015,.02,1)
        screen.data.materials.append(mat)
        for f in screen.data.polygons:f.material_index=0
    if slug == 'painted_wooden_cabinet_02':
        # Retain worn paint/wood detail but replace blue paint with warm neutral.
        images={n.image for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes
                if n.type=='TEX_IMAGE' and n.image and 'diff' in n.image.name.lower()}
        for image in images:
            pixels=np.array(image.pixels[:],dtype=np.float32).reshape((-1,4))
            rgb=pixels[:,:3];blue=(rgb[:,2]>rgb[:,0]*1.10)&(rgb[:,2]>rgb[:,1]*.98)
            luminance=rgb@np.array([.30,.59,.11],dtype=np.float32)
            pixels[blue,:3]=np.minimum(1,luminance[blue,None]*np.array([1.10,1.03,.90]))
            image.pixels.foreach_set(pixels.ravel());image.update()
    for image in bpy.data.images:
        if image.source=='FILE' and max(image.size)>1024:
            factor=1024/max(image.size);image.scale(round(image.size[0]*factor),round(image.size[1]*factor))
    verts=[o.matrix_world@Vector(c) for o in bpy.context.scene.objects if o.type=='MESH' for c in o.bound_box]
    bounds=[[min(v[i] for v in verts),max(v[i] for v in verts)] for i in range(3)]
    print('HOME_ASSET_INFO',slug,json.dumps({'bounds_blender':bounds,'materials':[m.name for m in bpy.data.materials]}),flush=True)
    bpy.ops.file.pack_all()
    source=ROOT/f'art/blender/{name}.blend'
    stage=Path(tempfile.gettempdir())/f'{name}_source.blend'
    if stage.exists():stage.unlink()
    bpy.ops.wm.save_as_mainfile(filepath=str(stage));shutil.copyfile(stage,source);stage.unlink()
    bpy.ops.export_scene.gltf(filepath=str(OUT/f'{name}.glb'),export_format='GLB',export_apply=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    assert all(i.packed_file for i in bpy.data.images if i.source=='FILE')
    print('HOME_ASSET_PORTABLE',name,'PASS',flush=True)
