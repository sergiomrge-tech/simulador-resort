"""Adapt original Quaternius rigged cloth; never transfer weights from a different body."""
from pathlib import Path
import bpy, bmesh, shutil, math
from mathutils import Vector
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
        if part=='Legs':
            bm=bmesh.new();bm.from_mesh(ob.data)
            bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,0,.62),plane_no=(0,0,1),clear_inner=True)
            bm.to_mesh(ob.data);bm.free()
        if part=='Body':
            # Flatten small decorative fastenings into the fabric for a casual shirt.
            for v in ob.data.vertices:
                if abs(v.co.x)<.10 and 1.025<v.co.z<1.45:
                    v.co.y=max(v.co.y,-.128)
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
    # Fit to THIS outfit's front surface instead of hanging a flat panel in front.
    fit_v=[]
    for ob in keep:
        if ob.name not in ['shirt','trousers']:continue
        fit_v.extend(v.co.copy() for v in ob.data.vertices)
    profile=[]
    for k in range(81):
        z=.75+k*.01
        hits=[v.y for v in fit_v if abs(v.z-z)<.025 and abs(v.x)<.11]
        profile.append(min(hits) if hits else -.08)
    # Smooth the garment silhouette, rather than reproducing every button and
    # individual trouser leg as a sharp crease in a continuous piece of cloth.
    profile=[sum(profile[max(0,min(80,k+d))] for d in range(-3,4))/7 for k in range(81)]
    def front(x,z):
        t=max(0,min(79.999,(z-.75)*100));i=int(t)
        center=profile[i]*(1-(t-i))+profile[i+1]*(t-i)
        return center+.035*(x/.21)**2
    def width_at(z):
        if z<1.075:return .158+.050*((1.075-z)/.295)**.7
        t=min(1,(z-1.075)/.335)
        return .158-.056*math.sin(t*math.pi*.5)
    def cloth(x,z):
        # Gather at the waist; longer vertical folds soften toward the bib.
        skirt=max(0,min(1,(1.12-z)/.34))
        fold=(.003+.008*skirt)*math.cos(x*65+z*3)
        # Sample a little above/below to smooth the underlying shirt fastenings.
        y=sum(front(x,z+d) for d in [-.008,0,.008])/3
        ease=.035*max(0,min(1,(1.10-z)/.10))
        return (x,y-.010-abs(fold)-.006*skirt-ease,z)
    verts=[];faces=[];uvs=[];tones=[];nx=32;nz=48
    def patch(rows,tone=1):
        start=len(verts);ny=len(rows)-1;nr=len(rows[0])-1
        for j,row in enumerate(rows):
            for i,p in enumerate(row):
                verts.append(p);uvs.append((i/nr,j/ny));tones.append(tone)
        for j in range(ny):
            for i in range(nr):
                a=start+j*(nr+1)+i;faces.append((a,a+1,a+nr+2,a+nr+1))
    rows=[]
    for j in range(nz+1):
        z=.78+j/nz*.63;width=width_at(z)
        row=[]
        for i in range(nx+1):
            u=i/nx*2-1;x=u*width
            # Rounded hem corners, with a small sag between the supporting ties.
            zz=z+.018*abs(u)**8*(1-j/nz)**12-.006*(1-u*u)*(1-j/nz)**8
            row.append(cloth(x,zz))
        rows.append(row)
    patch(rows)
    # A curved double pocket follows the apron, with an open rolled upper lip.
    pocket=[]
    for j in range(13):
        z=.945+j/12*.11
        pocket.append([(x,cloth(x,z)[1]-.006-.008*math.sin(j/12*math.pi),z)
                       for x in [-.115+i/24*.23 for i in range(25)]])
    patch(pocket,.94)
    # Sewn ribbons are part of the same skinned mesh, so hiding the apron also
    # hides its neck loop, waist tie and pocket seam.
    def ribbon(points,width,tone=.88):
        rows=[]
        for i,p in enumerate(points):
            p=Vector(p)
            tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
            side=tangent.cross(Vector((0,-1,0))).normalized()*width*.5
            rows.append([p-side,p+side])
        patch(rows,tone)
    ribbon([(0,cloth(0,z)[1]-.016,z) for z in [.948+i/16*.103 for i in range(17)]],.003,.78)
    ribbon([(x,cloth(x,1.055)[1]-.010,1.055) for x in [-.115+i/32*.23 for i in range(33)]],.007,.86)
    for sign in [-1,1]:
        ribbon([(sign*width_at(z),cloth(sign*width_at(z),z)[1]-.001,z)
                for z in [.80+i/48*.61 for i in range(49)]],.006,.86)
    ribbon([(x,cloth(x,.79)[1]-.003,.79) for x in [-.204+i/48*.408 for i in range(49)]],.008,.88)
    # Neck strap around the collar, attached to both corners of the bib.
    neck=[(-.082,cloth(-.082,1.402)[1],1.402),(-.075,cloth(-.075,1.442)[1],1.442),(-.065,-.035,1.475)]
    neck += [(.065*math.cos(t),.025+.065*math.sin(t),1.475)
             for t in [math.pi-i/24*math.pi for i in range(25)]]
    neck += [(.065,-.035,1.475),(.075,cloth(.075,1.442)[1],1.442),(.082,cloth(.082,1.402)[1],1.402)]
    ribbon(neck,.020,.90)
    # Waist ties wrap the hips, not just a line painted on the panel.
    belt=[]
    for i in range(81):
        t=math.pi*2*i/80
        belt.append((.19*math.sin(t),.025-.15*math.cos(t),1.075))
    ribbon(belt,.026,.88)
    mesh=bpy.data.meshes.new('Tailored apron cloth');mesh.from_pydata(verts,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name='Apron sewing UV')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi=mesh.loops[li].vertex_index
            uv.data[li].uv=uvs[vi]
    color=mesh.color_attributes.new(name='Cloth detail',type='FLOAT_COLOR',domain='POINT')
    for i,tone in enumerate(tones):color.data[i].color=(1,tone,1,1)
    apron=bpy.data.objects.new('apron',mesh);bpy.context.scene.collection.objects.link(apron)
    anchors=[(.94,'pelvis'),(1.055,'spine_01'),(1.164,'spine_02'),(1.291,'spine_03'),(1.49,'neck_01')]
    for bone in [b for _,b in anchors]+['thigh_l','thigh_r']:apron.vertex_groups.new(name=bone)
    for v in mesh.vertices:
        z=v.co.z;weights={}
        if z<.94:
            weights={'pelvis':1}
        else:
            for k in range(len(anchors)-1):
                lo,a=anchors[k];hi,b=anchors[k+1]
                if lo<=z<=hi:
                    t=(z-lo)/(hi-lo);weights={a:1-t,b:t};break
            if not weights:weights={anchors[-1][1]:1}
        # Continuous blend across the hips; a threshold at pelvis height makes
        # adjacent rows separate visibly when the idle animation twists a leg.
        leg=max(0,min(.95,(1.035-z)/.24))
        if leg>0:
            weights={b:w*(1-leg) for b,w in weights.items()}
            left=max(0,min(1,.5+v.co.x/.16))
            weights['thigh_l']=leg*left;weights['thigh_r']=leg*(1-left)
        for bone,w in weights.items():
            if w>0:apron.vertex_groups[bone].add([v.index],w,'REPLACE')
    apron.parent=first_rig
    mod=apron.modifiers.new('Original character rig','ARMATURE');mod.object=first_rig
    bpy.context.view_layer.objects.active=apron
    solid=apron.modifiers.new('Sewn cloth thickness','SOLIDIFY');solid.thickness=.002;solid.offset=0
    bpy.ops.object.modifier_apply(modifier=solid.name)
    apron.data.materials.append(keep[0].data.materials[0])
    for polygon in mesh.polygons:polygon.use_smooth=True
    keep.append(apron)
    first_rig.animation_data_clear()
    for action in list(bpy.data.actions):bpy.data.actions.remove(action)
    bpy.ops.file.pack_all()
    source=ROOT/f'art/blender/resort_outfit_{sex.lower()}.blend'
    # Blender's Windows overwrite/rename can fail after reopening the preceding
    # packed source. Save a fresh staging file, then copy to the stable source.
    import tempfile
    staged=Path(tempfile.gettempdir())/f'resort_outfit_{sex.lower()}_source.blend'
    if staged.exists():staged.unlink()
    bpy.ops.wm.save_as_mainfile(filepath=str(staged))
    shutil.copyfile(staged,source)
    staged.unlink()
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
