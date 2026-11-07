"""Original editable folded envelope and letter; never a runtime placeholder plane."""
from pathlib import Path
import bpy,math
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'unreal/MareAlta/SourceArt/Intro/Refined'
bpy.ops.wm.read_factory_settings(use_empty=True)
def material(name,color,rough=.8):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    return m
paper=material('Warm cotton paper',(.77,.72,.61));ink=material('Faded blue handwriting',(.045,.07,.09))
envelope=material('Kraft envelope',(.39,.27,.15));seal=material('Blue coastal seal',(.045,.12,.15))
def sheet(name,x,y,z,w,h,mat):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=14,y_subdivisions=14,size=1,location=(x,y,z));o=bpy.context.object;o.name=name
    for v in o.data.vertices:v.co.x*=w;v.co.y*=h;v.co.z+=.00025*math.sin(v.co.x*70)*math.sin(v.co.y*45)
    o.data.materials.append(mat);s=o.modifiers.new('Paper thickness','SOLIDIFY');s.thickness=.0004;bpy.ops.object.modifier_apply(modifier=s.name)
    return o
sheet('Envelope back',.012,.008,.001,.25,.172,envelope)
sheet('Letter cotton sheet',0,0,.003,.23,.16,paper)
def text(body,at,size):
    curve=bpy.data.curves.new('Letter ink','FONT');curve.body=body;curve.size=size;curve.extrude=0;curve.resolution_u=6
    o=bpy.data.objects.new(body,curve);bpy.context.collection.objects.link(o);o.location=at;o.data.materials.append(ink)
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
text('Para o meu neto',(-.098,.054,.0038),.012)
for i,line in enumerate(['O mar tem cheiro de aventura,','mas tambem tem cheiro de casa.','','O quiosque agora e seu.','Cuide das pessoas da nossa vila.','Nosso sonho continua com voce.']):
    text(line,(-.097,.031-i*.014,.0038),.0064)
text('Com amor, Vo',(.035,-.065,.0038),.008)
# Folded triangular envelope flap, visible beyond the cotton sheet.
mesh=bpy.data.meshes.new('Folded flap');mesh.from_pydata([(-.113,.094,.001),(.137,.094,.001),(.012,.031,.0018)],[],[(0,1,2)])
ob=bpy.data.objects.new('Envelope folded flap',mesh);bpy.context.collection.objects.link(ob);mesh.materials.append(envelope)
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=next(o for o in bpy.context.scene.objects if o.type=='MESH');bpy.ops.object.join();bpy.context.object.name='Letter_Home'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'letter_home.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'Letter_Home.glb'),export_format='GLB',use_selection=True,export_yup=True)
