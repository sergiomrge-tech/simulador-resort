"""Adapt original Quaternius rigged cloth; never transfer weights from a different body."""
from pathlib import Path
import bpy, bmesh, shutil
ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'art/vendor/quaternius_outfits/Modular Character Outfits - Fantasy[Standard]/Exports/glTF (Godot-Unreal)/Modular Parts'
OUT=ROOT/'assets/models/clothing'
OUT.mkdir(parents=True,exist_ok=True)
for image in (ROOT/'art/vendor/quaternius_outfits/Modular Character Outfits - Fantasy[Standard]/Textures/Base').glob('*.png'):
    shutil.copyfile(image,FOLDER/image.name)
for female in [False,True]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0
    sex='Female' if female else 'Male'
    keep=[];first_rig=None
    for part,name in [('Body','shirt'),('Legs','trousers'),('Arms','shirt_sleeves'),('Feet','shoes')]:
        before=set(bpy.context.scene.objects)
        bpy.ops.import_scene.gltf(filepath=str(FOLDER/f'{sex}_Peasant_{part}.gltf'))
        added=set(bpy.context.scene.objects)-before
        ob=next(o for o in added if o.type=='MESH' and 'Peasant' in o.name)
        rig=next(o for o in added if o.type=='ARMATURE')
        ob.name=name
        if first_rig is None:first_rig=rig
        else:
            for mod in ob.modifiers:
                if mod.type=='ARMATURE':mod.object=first_rig
            ob.parent=first_rig
        if part in ['Body','Feet']:
            # Straight shirt hem removes the medieval belt/tails. Low shoes
            # replace the tall boot silhouette while retaining original weights.
            bm=bmesh.new();bm.from_mesh(ob.data)
            height=1.025 if part=='Body' else .15
            bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,0,height),plane_no=(0,0,1),clear_inner=part=='Body',clear_outer=part=='Feet')
            bm.to_mesh(ob.data);bm.free()
        # A little ease over the muscular base; preserve original topology and weights.
        for v in ob.data.vertices:
            if part!='Arms':v.co+=v.normal*.004
        if part=='Arms':
            # Keep the matching forearms/hands from the garment's own body family.
            # Split them from fabric while preserving the original rig weights.
            skin=ob.copy();skin.data=ob.data.copy();skin.name='skin_arms'
            bpy.context.scene.collection.objects.link(skin)
            for mesh_object,skin_faces in [(ob,False),(skin,True)]:
                bm=bmesh.new();bm.from_mesh(mesh_object.data)
                remove=[f for f in bm.faces if (abs(f.calc_center_median().x)>.38)!=skin_faces]
                bmesh.ops.delete(bm,geom=remove,context='FACES')
                bm.to_mesh(mesh_object.data);bm.free()
            keep.append(skin)
        bpy.context.view_layer.objects.active=ob
        sub=ob.modifiers.new('Soft tailored cloth','SUBSURF');sub.levels=1
        bpy.ops.object.modifier_apply(modifier=sub.name)
        solid=ob.modifiers.new('Finished cloth edge','SOLIDIFY');solid.thickness=.003;solid.offset=0
        bpy.ops.object.modifier_apply(modifier=solid.name)
        for polygon in ob.data.polygons:polygon.use_smooth=True
        keep.append(ob)
        for other in added:
            if other not in keep and other!=first_rig:bpy.data.objects.remove(other,do_unlink=True)
    first_rig.animation_data_clear()
    for action in list(bpy.data.actions):bpy.data.actions.remove(action)
    bpy.ops.file.pack_all()
    source=ROOT/f'art/blender/resort_outfit_{sex.lower()}.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    # Runtime needs the cloth colour atlas only. Keep the original detailed
    # materials packed in the editable .blend, and export a compact 1K atlas.
    fabric=None
    for ob in keep:
        original=ob.data.materials[0]
        if fabric is None:
            image=next(n.image for n in original.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'BaseColor' in n.image.name)
            image=image.copy();image.name='resort_fabric_cc0';image.scale(1024,1024)
            fabric=bpy.data.materials.new('Resort woven fabric');fabric.use_nodes=True
            shader=next(n for n in fabric.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
            shader.inputs['Roughness'].default_value=.9
            tex=fabric.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
            fabric.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color'])
        ob.data.materials.clear();ob.data.materials.append(fabric)
        for polygon in ob.data.polygons:polygon.material_index=0
    bpy.ops.export_scene.gltf(filepath=str(OUT/f'outfit_{sex.lower()}.glb'),export_format='GLB',export_animations=False)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    assert all(i.packed_file for i in bpy.data.images if i.source=='FILE')
    print('COMPATIBLE_OUTFIT',sex,'PASS',flush=True)
