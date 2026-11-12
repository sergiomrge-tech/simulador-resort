"""Source-art audit render, explicitly not a game screenshot. Uses CPU Cycles."""
from pathlib import Path
import bpy,sys
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=Path('D:/CodexTemp/ue58-animal-source-review');OUT.mkdir(exist_ok=True)
candidates='--candidates' in sys.argv
for name in (('labrador','tabby') if candidates else ('dog','cat')):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source=Path('D:/CodexTemp/ue58-animal-candidates')/(name+'.glb') if candidates else ROOT/'assets/models/gen'/(name+'.glb')
    bpy.ops.import_scene.gltf(filepath=str(source))
    points=[o.matrix_world@Vector(v) for o in bpy.context.scene.objects if o.type=='MESH' for v in o.bound_box]
    lo=Vector(tuple(min(v[i] for v in points) for i in range(3)));hi=Vector(tuple(max(v[i] for v in points) for i in range(3)))
    center=(lo+hi)/2;size=max(hi-lo)
    bpy.ops.object.camera_add(location=center+Vector((size*1.7,-size*1.5,size*.75)));cam=bpy.context.object
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=size*1.35
    scene=bpy.context.scene;scene.camera=cam;scene.world=bpy.data.worlds.new('Neutral studio');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.3,.3,.3,1)
    for delta,power in [((1,-2,2),400),((-1,1,1.5),250)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(delta)*size);light=bpy.context.object;light.data.energy=power*size*size;light.data.shape='DISK';light.data.size=size*2
        light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
    scene.render.resolution_x=900;scene.render.resolution_y=700;scene.render.resolution_percentage=100
    scene.render.filepath=str(OUT/(name+'.png'));scene.render.image_settings.file_format='PNG';bpy.ops.render.render(write_still=True)
