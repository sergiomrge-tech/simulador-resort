"""Preserve Quaternius CC0 rigs/clips; refine mesh and add rigged facial features."""
from pathlib import Path
import bpy,math,shutil,tempfile
from mathutils import Vector,Matrix
from smooth_animals import to_principled
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'art/vendor/animals'
if not any(SOURCE.rglob('Dog.blend')):
    import requests,zipfile,io
    response=requests.get('https://opengameart.org/sites/default/files/Animal%20Pack%20Vol.2%20by%20%40Quaternius.zip',timeout=90)
    response.raise_for_status();SOURCE.mkdir(parents=True,exist_ok=True)
    zipfile.ZipFile(io.BytesIO(response.content)).extractall(SOURCE)


def material(name,color,rough=.65):
    m=bpy.data.materials.new(name);m.use_nodes=True
    node=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    node.inputs['Base Color'].default_value=(*color,1)
    node.inputs['Roughness'].default_value=rough
    return m

def bind(obj,arm,mat):
    obj.data.materials.append(mat)
    for face in obj.data.polygons:face.use_smooth=True
    # Features are authored in armature rest coordinates, following the head.
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    obj.parent=arm;obj.matrix_parent_inverse=Matrix.Identity(4);obj.matrix_basis=Matrix.Identity(4)
    group=obj.vertex_groups.new(name='Bone.003');group.add(list(range(len(obj.data.vertices))),1.0,'REPLACE')
    mod=obj.modifiers.new('Facial skin','ARMATURE');mod.object=arm

def oval(name,center,scale,arm,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,radius=1,location=center)
    obj=bpy.context.object;obj.name=name;obj.scale=scale;bind(obj,arm,mat)

def curve(name,points,radius,arm,mat):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=3
    spline=data.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
    for point,co in zip(spline.bezier_points,points):point.co=co;point.handle_left_type='AUTO';point.handle_right_type='AUTO'
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.object.convert(target='MESH');bind(bpy.context.object,arm,mat)

def build(kind):
    bpy.ops.wm.open_mainfile(filepath=str(next(SOURCE.rglob(kind+'.blend'))))
    bpy.context.preferences.filepaths.save_version=0
    to_principled()
    arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    arm.data.pose_position='REST'
    for ob in list(bpy.context.scene.objects):
        if ob.type!='MESH':continue
        bpy.context.view_layer.objects.active=ob
        sub=ob.modifiers.new('Refined rounded skin','SUBSURF');sub.levels=2
        ob.modifiers.move(len(ob.modifiers)-1,0)
        bpy.ops.object.modifier_apply(modifier=sub.name)
        for face in ob.data.polygons:face.use_smooth=True
    dark=material(kind+' eyes and mouth',(.012,.009,.007),.32)
    iris=material(kind+' amber iris',(.28,.16,.035),.3)
    glint=material(kind+' eye highlights',(.95,.96,.91),.16)
    nose=material(kind+' nose',(.29,.10,.10) if kind=='Cat' else (.035,.023,.018),.5)
    # +X is forward in both original armatures.
    x,z,y=(2.88,2.94,.38) if kind=='Cat' else (2.14,3.30,.30)
    for side in [-1,1]:
        eye_scale=.8 if kind=='Cat' else .60
        oval('Eye socket',(x,side*y,z),tuple(t*eye_scale for t in (.15,.13,.15)),arm,dark)
        oval('Amber iris',(x+.12*eye_scale,side*y,z),tuple(t*eye_scale for t in (.052,.085,.10)),arm,iris)
        oval('Pupil',(x+.159*eye_scale,side*y,z),tuple(t*eye_scale for t in (.025,.032 if kind=='Cat' else .055,.085)),arm,dark)
        oval('Eye glint',(x+.177*eye_scale,side*y-.021*eye_scale,z+.041*eye_scale),tuple(t*eye_scale for t in (.018,.019,.023)),arm,glint)
    front,height=(3.17,2.57) if kind=='Cat' else (2.85,3.01)
    oval('Detailed nose',(front,0,height),(.105,.15,.085),arm,nose)
    for side in [-1,1]:
        oval('Nostril',(front+.085,side*.066,height),(.025,.030,.024),arm,dark)
        curve('Mouth crease',[(front+.035,0,height-.07),(front+.015,side*.09,height-.15),(front-.03,side*.24,height-.13)],.014,arm,dark)
        if kind=='Cat':
            for i in range(3):
                curve('Tapered whisker',[(front-.06,side*.16,height-.04-i*.035),(front-.10,side*.40,height+.04-i*.06),(front-.20,side*.70,height+.10-i*.10)],.007,arm,glint)
    arm.data.pose_position='POSE'
    bpy.ops.file.pack_all()
    stage=Path(tempfile.gettempdir())/(kind+'_living.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(stage))
    target=ROOT/'art/blender'/(kind.lower()+'_living.blend');shutil.copyfile(stage,target)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/models/gen'/(kind.lower()+'.glb')),export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_skins=True)
    bpy.ops.wm.open_mainfile(filepath=str(target))
    assert any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
    assert all(im.packed_file for im in bpy.data.images if im.source=='FILE')
    print('LIVING_ANIMAL_PORTABLE PASS',kind,[a.name for a in bpy.data.actions])

if __name__=='__main__':
    for name in ['Cat','Dog']:build(name)
