"""Blender: preserve the CC0 bus, add an opening, interior and editable door.
Run with Blender --background --factory-startup --python this_file.py.
"""
from pathlib import Path
import json,math
import bpy,bmesh
from mathutils import Vector,Matrix

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'unreal/MareAlta/SourceArt/Intro/Refined'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'unreal/MareAlta/SourceArt/Intro/bus-original.blend'))


def mat(name,color,metal=0,rough=.5,alpha=1,emission=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True;m.node_tree.nodes.clear()
    p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Alpha'].default_value=alpha
    if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    if alpha<1:m.surface_render_method='DITHERED'
    return m


paint=mat('Body',(.62,.66,.63),.35,.4)
trim=mat('karmi',(.055,.07,.07),.5,.35)
glass=mat('Windows',(.12,.16,.16),.05,.12,.18)
mat('RearLights',(.4,.025,.01),.1,.3,emission=.6)
mat('FrontLights',(.8,.78,.64),.2,.18,emission=2)
mat('Indicators',(.7,.24,.015),.1,.25,emission=.6)
mat('Metal',(.3,.34,.34),.85,.3);mat('Tire',(.018,.022,.021),0,.87);mat('Bolt',(.25,.28,.27),.9,.3)
stripe=mat('Livery slate teal',(.055,.15,.16),.25,.43)
steel=mat('Interior stainless',(.32,.36,.36),.85,.28)
rubber=mat('Safety rubber',(.025,.032,.031),0,.92)
seatmat=mat('Woven teal upholstery',(.035,.12,.13),0,.92)
yellow=mat('Step safety edging',(.65,.47,.07),.1,.65)
white=mat('Route lettering',(.85,.87,.81),0,.65)


def bevel(ob,width=.012):
    bpy.context.view_layer.objects.active=ob
    m=ob.modifiers.new('Manufactured rounded edges','BEVEL');m.width=width;m.segments=3
    bpy.ops.object.modifier_apply(modifier=m.name)
    for p in ob.data.polygons:p.use_smooth=True
    n=ob.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');n.keep_sharp=True
    bpy.ops.object.modifier_apply(modifier=n.name)
    return ob


def box(name,at,size,material,rounding=.012):
    bpy.ops.mesh.primitive_cube_add(size=1,location=at);ob=bpy.context.object;ob.name=name
    ob.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(material)
    return bevel(ob,rounding) if rounding else ob


def bar(name,a,b,r=.012):
    a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=(b-a).length,location=(a+b)/2)
    ob=bpy.context.object;ob.name=name;ob.rotation_mode='QUATERNION';ob.rotation_quaternion=(b-a).to_track_quat('Z','Y');ob.data.materials.append(steel)
    for p in ob.data.polygons:p.use_smooth=True
    return ob


def cut(ob,at,size):
    cutter=box('Boolean tool only',at,size,rubber,0)
    bpy.context.view_layer.objects.active=ob;m=ob.modifiers.new('Real passenger doorway','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter
    bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cutter,do_unlink=True)


original=[o for o in bpy.context.scene.objects if o.type=='MESH']
points=[o.matrix_world@Vector(v) for o in original for v in o.bound_box]
origin=Vector(((min(p.x for p in points)+max(p.x for p in points))/2,(min(p.y for p in points)+max(p.y for p in points))/2,min(p.z for p in points)))
for ob in original:
    matrix=ob.matrix_world.copy();ob.parent=None;ob.data.transform(matrix);ob.matrix_world=Matrix.Identity(4)
    ob.data.transform(Matrix.Translation(-origin));ob.data.update()
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
body=bpy.data.objects['Bus_Body'];body.data.materials.append(stripe)
for p in body.data.polygons:
    if body.data.materials[p.material_index].name=='Body' and p.center.z<.93:p.material_index=len(body.data.materials)-1
cut(body,(3.55,-1.03,1.18),(.88,.60,1.98))
if len(body.data.polygons)<900:raise RuntimeError('Doorway damaged source body')
bevel(body,.004)
interior=[]
floor=box('Non-slip interior floor',(0,0,.52),(8.75,1.87,.08),rubber)
cut(floor,(3.55,-.76,.52),(.90,.70,.2));interior.append(floor)
for i in range(3):
    z=.20+i*.17;y=-1.02+i*.19
    interior.append(box('Entry step '+str(i),(3.55,y,z),(.83,.22,.06),rubber))
    interior.append(box('Step contrasting edge '+str(i),(3.55,y-.105,z+.03),(.81,.018,.012),yellow,.004))
for row in range(8):
    x=2.18-row*.78
    for side in (-1,1):
        for offset in (.40,.77):
            y=side*offset
            interior.append(box('Seat cushion',(x,y,.97),(.52,.32,.12),seatmat,.035))
            back=box('Padded seat back',(x-.25,y,1.30),(.11,.33,.62),seatmat,.035);back.rotation_euler.y=-.10;interior.append(back)
            interior.append(bar('Seat leg',(x-.10,y,.57),(x-.10,y,.90),.018))
        interior.append(bar('Seat support',(x,-.22*side,.85),(x,.94*side,.85),.018))
        interior.append(bar('Aisle handhold',(x-.26,side*.245,1.1),(x-.26,side*.245,1.53),.012))
interior.append(box('Driver seat',(3.90,.53,.98),(.53,.47,.16),seatmat,.04))
interior.append(box('Driver seat back',(3.62,.53,1.34),(.12,.49,.66),seatmat,.04))
interior.append(box('Instrument console',(4.28,.38,1.19),(.43,1.12,.36),trim,.035))
bpy.ops.mesh.primitive_torus_add(major_radius=.17,minor_radius=.014,major_segments=48,minor_segments=12,location=(4.02,.53,1.39),rotation=(0,math.pi/2,0))
wheel=bpy.context.object;wheel.name='Steering wheel';wheel.data.materials.append(rubber);interior.append(wheel)
for angle in (0,2.0944,4.1888):interior.append(bar('Steering spoke',(4.02,.53,1.39),(4.02,.53+math.cos(angle)*.16,1.39+math.sin(angle)*.16),.01))
for y in (-.30,.30):interior.append(bar('Overhead aisle rail',(-3.6,y,1.94),(2.7,y,1.94),.014))
interior.append(bar('Door safety pole',(3.04,-.64,.58),(3.04,-.64,1.95),.016))
interior.append(box('Destination panel',(4.67,0,1.93),(.025,1.25,.20),trim,.01))
bpy.ops.object.text_add(location=(4.69,-.53,1.88),rotation=(math.pi/2,0,math.pi/2));text=bpy.context.object;text.name='Vila da Mare route';text.data.body='VILA DA MARE';text.data.size=.14;text.data.extrude=.0005;text.data.materials.append(white)
bpy.context.view_layer.objects.active=text;bpy.ops.object.convert(target='MESH');interior.append(bpy.context.object)

door=[];pivot=Vector((3.985,-1.075,.20))
for x in (3.145,3.985):door.append(box('Door upright',(x,-1.075,1.175),(.035,.045,1.95),trim,.008))
for z in (.20,1.12,2.15):door.append(box('Door cross rail',(3.565,-1.075,z),(.87,.045,.045),trim,.008))
for z,h in ((.66,.84),(1.635,.94)):door.append(box('Door clear glazing',(3.565,-1.075,z),(.79,.012,h),glass,.006))
door.append(bar('Door pull',(3.25,-1.115,.84),(3.25,-1.115,1.12),.012))
for z in (.38,1.83):door.append(bar('Door hinge',(3.985,-1.075,z-.045),(3.985,-1.075,z+.045),.021))


def join(items,name,pivot=Vector((0,0,0))):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in items:ob.select_set(True)
    bpy.context.view_layer.objects.active=items[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=name
    world=ob.matrix_world.copy();ob.data.transform(world);ob.matrix_world=Matrix.Identity(4)
    ob.data.transform(Matrix.Translation(-pivot));ob.location=pivot
    return ob


chassis=join([body]+interior,'Bus_Cabin')
leaf=join(door,'Bus_Door',pivot)
parts={'Bus_Cabin':chassis,'Bus_Door':leaf};wheel_points={}
for ob in original:
    if not ob.name.startswith('wheel'):continue
    center=sum((Vector(v) for v in ob.bound_box),Vector())/8
    ob.data.transform(Matrix.Translation(-center));ob.location=center
    parts[ob.name]=ob;wheel_points[ob.name]=list(center)
manifest={'source':'ajanhallinta CC0 bus-original.blend','has_interior':True,'seat_count':32,'door_pivot_blender':list(pivot),'wheels_blender':wheel_points,'steps_blender':[[3.55,-.35,.56],[3.55,-.68,.38],[3.55,-.96,.20],[3.55,-1.30,0],[3.55,-2.25,0]]}
for name,ob in parts.items():
    position=ob.location.copy();ob.location=(0,0,0)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_apply=True)
    ob.location=position
# Small, editor-only axis probe establishes the actual Blender -> UE conversion.
probe=box('AxisProbe',(1,2,3),(.1,.1,.1),trim,0);probe.data.transform(probe.matrix_world);probe.matrix_world=Matrix.Identity(4)
bpy.ops.object.select_all(action='DESELECT');probe.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'AxisProbe.glb'),export_format='GLB',use_selection=True)
bpy.data.objects.remove(probe,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'bus_refined.blend'))
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('BUS_REFINED '+json.dumps(manifest))
