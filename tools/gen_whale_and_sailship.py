"""Detailed authored humpback and Poly Haven CC0 sailing ship, packed sources."""
from pathlib import Path
import bpy,bmesh,math,sys
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gen_coastal_traffic import save
from gen_code_props import mat
ROOT=Path(__file__).resolve().parents[1]

def mesh(name,verts,faces,material):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update()
 o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);m.materials.append(material)
 bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
 for f in m.polygons:f.use_smooth=True
 return o

def whale():
 bpy.ops.wm.read_factory_settings(use_empty=True)
 dark=mat('mottled charcoal skin',(.075,.095,.105),.52)
 pale=mat('ventral pleats',(.57,.60,.57),.7)
 eye=mat('whale eye',(.012,.015,.016),.3)
 # Body runs along X, nose +X. Dense loft with a broad flattened jaw.
 profile=[(-6,.06,.06,0),(-5.4,.22,.22,0),(-4.5,.35,.35,.05),(-3.5,.64,.58,.13),(-2.2,.98,.95,.18),(-.5,1.18,1.25,.14),(1.3,1.15,1.25,.08),(2.9,.99,1.02,.02),(4.2,.85,.70,-.10),(5.0,.62,.40,-.16),(5.45,.10,.16,-.12)]
 verts=[];faces=[];n=64
 for j in range(len(profile)-1):
  for step in range(8):
   t=step/8;a=profile[j];b=profile[j+1];p=[a[k]*(1-t)+b[k]*t for k in range(4)]
   for i in range(n):
    th=math.tau*i/n;rough=1+.012*math.sin(th*9+p[0]*4)*math.sin(p[0]*7)
    verts.append((p[0],math.cos(th)*p[1]*rough,p[3]+math.sin(th)*p[2]*rough))
 rings=len(verts)//n
 for j in range(rings-1):
  for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 faces.extend([tuple(reversed(range(n))),tuple(range((rings-1)*n,rings*n))])
 body=mesh('Humpback body',verts,faces,dark);body.data.materials.append(pale)
 for f in body.data.polygons:
  if f.center.z<-.35 and f.center.x>-.8:f.material_index=1
 # Curved, tapered hydrofoil fins and split flukes, with thickness.
 def fin(name,path,widths,material):
  vs=[];fs=[];segments=24
  for p,w in zip(path,widths):
   for k in range(segments):
    t=math.tau*k/segments;vs.append((p[0]+math.cos(t)*w,p[1],p[2]+math.sin(t)*w*.10))
  for j in range(len(path)-1):
   for k in range(segments):fs.append((j*segments+k,j*segments+(k+1)%segments,(j+1)*segments+(k+1)%segments,(j+1)*segments+k))
  fs.extend([tuple(reversed(range(segments))),tuple(range((len(path)-1)*segments,len(path)*segments))])
  o=mesh(name,vs,fs,material);sub=o.modifiers.new('curved fin','SUBSURF');sub.levels=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=sub.name)
 for side in [-1,1]:
  fin('Long pectoral flipper',[(1,side*.9,-.25),(.8,side*1.6,-.45),(.1,side*2.7,-.55),(-.9,side*3.6,-.37),(-1.3,side*4,-.18)],[.48,.53,.43,.23,.015],pale)
  fin('Tail fluke',[(-5.5,0,0),(-5.8,side*.8,.05),(-5.8,side*1.7,.10),(-5.3,side*2.4,.15)],[.30,.58,.48,.015],dark)
 # Swept dorsal fin, jaw crease, eyes and throat grooves.
 dorsal=mesh('Swept dorsal fin',[(-2,-.10,1),(-2.7,-.08,1),(-2.5,0,1.8),(-1.9,.10,1),(-2.7,.08,1)],[(0,1,2),(3,2,4),(0,2,3),(1,4,2),(0,3,4,1)],dark)
 from gen_coastal_traffic import rail
 for side in [-1,1]:
  rail([(1.4,side*.99,-.1),(3,side*.89,-.18),(4.8,side*.52,-.22)],eye,.025)
  bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=.075,location=(3.15,side*.94,.03));bpy.context.object.data.materials.append(eye)
 for k in range(-7,8):
  y=k*.095
  rail([(-.3,y,-1.05),(1,y,-1.08),(2.5,y*.85,-.89),(4,y*.55,-.64)],dark,.012)
 save('humpback_whale')

def ship():
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/models/ship_pinnace/ship_pinnace.gltf'))
 save('pirate_sailship')
if __name__=='__main__':
 if len(sys.argv)==1 or 'whale' in sys.argv:whale()
 if len(sys.argv)==1 or 'ship' in sys.argv:ship()
