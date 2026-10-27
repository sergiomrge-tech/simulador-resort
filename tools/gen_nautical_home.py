"""Assets originais CC0: banheiro claro e detalhes náuticos. Fontes editáveis portáveis."""
from pathlib import Path
import sys,math,random,bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gen_code_props import fresh,mat,box
ROOT=Path(__file__).resolve().parents[1]
def cyl(name,at,radius,depth,material,rot=None):
 bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=radius,depth=depth,location=at)
 ob=bpy.context.object;ob.name=name;ob.data.materials.append(material)
 if rot:ob.rotation_euler=rot
 bevel=ob.modifiers.new('bordas','BEVEL');bevel.width=.012;bevel.segments=3
 bpy.ops.object.modifier_apply(modifier=bevel.name)
 for face in ob.data.polygons:face.use_smooth=True
 return ob
def uv(name,at,scale,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=at)
 ob=bpy.context.object;ob.name=name;ob.scale=scale;ob.data.materials.append(material)
 for face in ob.data.polygons:face.use_smooth=True
 return ob
def tube(name,pts,radius,material):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=radius;c.bevel_resolution=3
 sp=c.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 ob=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(ob);ob.data.materials.append(material)
 return ob
def materials():
 global white,wood,metal,linen,sea,sand
 white=mat('ceramica_marfin',(.91,.90,.85),.28)
 wood=mat('madeira_natural',(.49,.33,.18),.72,img=str(ROOT/'assets/tex/brown_planks_05_diff.jpg'))
 metal=mat('metal_escovado',(.48,.49,.47),.23,metal=.8)
 linen=mat('toalha_algodao',(.85,.83,.74),.98)
 sea=mat('verde_salvia',(.38,.53,.49),.85)
 sand=mat('areia',(.72,.63,.46),.9)
def save(name):
 bpy.context.preferences.filepaths.save_version=0
 for ob in bpy.context.scene.objects:
  if ob.type=='CURVE':
   bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False)
 # Agrupar por material mantém malha detalhada com poucas chamadas de desenho.
 groups={}
 for ob in list(bpy.context.scene.objects):
  if ob.type=='MESH' and len(ob.data.materials)==1:groups.setdefault(ob.data.materials[0].name,[]).append(ob)
 for objects in groups.values():
  if len(objects)<2:continue
  bpy.ops.object.select_all(action='DESELECT')
  for ob in objects:ob.select_set(True)
  bpy.context.view_layer.objects.active=objects[0]
  bpy.ops.object.join()
 bpy.ops.file.pack_all()
 dst=ROOT/'art/blender'/(name+'.blend')
 bpy.ops.wm.save_as_mainfile(filepath=str(dst))
 bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/models/gen'/(name+'.glb')),export_format='GLB')
 bpy.ops.wm.open_mainfile(filepath=str(dst))
 assert any(o.type=='MESH' for o in bpy.context.scene.objects)
 assert all(i.packed_file or i.source not in ['FILE'] for i in bpy.data.images)
 print('NAUTICAL_ASSET_OK',name)
fresh();materials()
# Louça cerâmica: bacia arredondada com cavidade real e assento separado.
uv('base_vaso',(.85,.65,.20),(.17,.23,.20),white)
cyl('pescoço_vaso',(.85,.64,.27),.13,.28,white)
# Anel elíptico aberto com malha contínua.
bpy.ops.mesh.primitive_torus_add(major_segments=64,minor_segments=16,location=(.85,.59,.43),major_radius=.19,minor_radius=.045)
ob=bpy.context.object;ob.name='assento_vaso';ob.scale=(.85,1.30,.55);ob.data.materials.append(white)
uv('agua_bacia',(.85,.59,.355),(.12,.18,.025),mat('agua_vaso',(.55,.65,.63),.15))
box((.36,.19,.42),(.85,.99,.55),white,bevel=.045)
box((.39,.22,.045),(.85,.99,.78),white,bevel=.018)
cyl('acionamento',(.85,.99,.808),.025,.008,metal)
# Armário de madeira, portas, pés, pia com bordas e torneira curvada.
box((1.10,.48,.60),(-.48,1.12,.43),wood,bevel=.025)
for x in [-.75,-.21]:
 box((.50,.035,.48),(x,.86,.43),wood,bevel=.01)
 box((.13,.035,.02),(x,.832,.59),metal,bevel=.006)
for x in [-.95,0]:box((.05,.05,.16),(x,1.12,.10),wood,bevel=.008)
box((1.18,.56,.07),(-.48,1.10,.78),white,bevel=.035)
# Cuba em anel oval, escurecida no fundo para mostrar profundidade.
uv('cuba_fundo',(-.48,1.05,.81),(.36,.18,.035),white)
for j in range(64):
 a=j*math.tau/64
 uv('borda_cuba',(-.48+.36*math.cos(a),1.05+.19*math.sin(a),.84),(.041,.035,.035),white)
tube('torneira',[(-.48,1.29,.82),(-.48,1.29,1.07),(-.48,1.05,1.07),(-.48,1.03,1.00)],.017,metal)
# Espelho, moldura e dois frascos.
mirror=mat('espelho_prata',(.67,.72,.72),.08,metal=.95)
box((1.05,.045,.87),(-.48,1.44,1.58),wood,bevel=.025)
box((.95,.015,.77),(-.48,1.41,1.58),mirror,bevel=.015)
for x in [-.95,.05]:
 cyl('frasco_sabonete',(x,1.15,.90),.04,.17,sea)
 cyl('tampa_sabonete',(x,1.15,1.0),.022,.03,metal)
# Box com soleira, ralo e vidro incolor em painel lateral.
box((1.18,1.24,.10),(.83,-.78,.05),white,bevel=.035)
for x in [.25,1.41]:box((.05,1.23,.065),(x,-.78,.13),white,bevel=.015)
cyl('ralo',(.85,-.85,.11),.065,.008,metal)
glass=mat('vidro_incolor',(.94,.97,.96),.1)
bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Transmission Weight'].default_value=.85;bs.inputs['Alpha'].default_value=.18
glass.surface_render_method='DITHERED'
box((.012,1.12,1.95),(.25,-.79,1.12),glass,bevel=.004)
for y in [-1.36,-.23]:box((.025,.025,1.98),(.25,y,1.12),metal,bevel=.004)
tube('chuveiro_cano',[(.90,-1.44,.95),(.90,-1.44,2.17),(.90,-1.10,2.23)],.018,metal)
cyl('ducha',(.90,-1.07,2.21),.12,.035,metal)
for j in range(16):
 a=j*math.tau/16;cyl('saida_agua',(.90+.08*math.cos(a),-1.07+.08*math.sin(a),2.186),.004,.008,white)
for x in [.75,1.05]:cyl('registro',(x,-1.44,1.04),.045,.05,metal,(math.pi/2,0,0))
tube('toalheiro',[(-1.27,.9,1.2),(-1.27,.30,1.2)],.015,metal)
box((.03,.45,.65),(-1.26,.60,.88),linen,bevel=.02)
for j in range(8):box((.034,.045,.60),(-1.26,.41+j*.054,.88),linen,bevel=.01)
save('home_bathroom_fixtures')
fresh();materials()
# Quadro de madeira com entalhe: ondas, veleiro, sol e corda em volta.
box((1.05,.07,.73),(0,0,.7),wood,bevel=.025)
box((.91,.014,.59),(0,-.045,.7),mat('fundo_quadro',(.87,.85,.75),.94),bevel=.012)
for z in [.47,.53,.59]:
 tube('onda_entalhada',[(x,-.063,z+.025*math.sin(x*14)) for x in [-.40+i*.025 for i in range(33)]],.012,sea)
box((.012,.012,.32),(.10,-.068,.78),wood,bevel=.003)
# Velas com topologia triangular real, sem caixas substituindo o objeto.
for sign in [-1,1]:
 mesh=bpy.data.meshes.new('vela');mesh.from_pydata([(.10,-.07,.92),(.10,-.07,.64),(.10+sign*.24,-.07,.65)],[],[(0,1,2)]);mesh.update()
 ob=bpy.data.objects.new('vela',mesh);bpy.context.collection.objects.link(ob);ob.data.materials.append(linen)
 sol=ob.modifiers.new('espessura','SOLIDIFY');sol.thickness=.006
uv('sol',(-.27,-.071,.86),(.065,.012,.065),sand)
for i in range(48):
 a=i*math.tau/48;uv('trama_corda',(.52*math.cos(a),-.047,.7+.36*math.sin(a)),(.016,.015,.018),sand)
save('nautical_wall_set')
fresh();materials()
for x in [-1.8+i*.12 for i in range(31)]:
 z=-.16*(1-(x/1.8)**2)
 # Native z=0 pivot, Godot offset handles hanging below eave.
 if abs(round(x/.12))%3==0:
  uv('lampada',(x,0,z-.08),(.036,.036,.055),mat('luz_quente',(.96,.83,.52),.25))
tube('fio',[(-1.9,0,0),(0,0,-.16),(1.9,0,0)],.008,wood)
save('nautical_string_lights')
fresh();materials()
box((.65,.36,.045),(0,0,.023),wood,bevel=.025)
for x in [-.31,.31]:box((.025,.36,.065),(x,0,.065),wood,bevel=.01)
for y in [-.17,.17]:box((.65,.025,.065),(0,y,.065),wood,bevel=.01)
for i in range(3):
 cyl('vaso_ceramico',(-.19+i*.19,0,.15),.065,.17,white if i%2 else sea)
 for j in range(9):tube('ranhura',[( -.19+i*.19+.066*math.cos(j*math.tau/9),.066*math.sin(j*math.tau/9),z) for z in [.075,.13,.22]],.002,linen)
save('nautical_counter_set')

