"""Porções prontas originais CC0. Fonte Blender editável; nenhuma textura externa."""
from pathlib import Path
import sys, math, random
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gen_code_props import fresh, mat, box
from gen_dishes import extruded_outline,pebble
ROOT=Path(__file__).resolve().parents[1]
def save(name):
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.file.pack_all()
 p=ROOT/'art/blender'/(name+'.blend')
 bpy.ops.wm.save_as_mainfile(filepath=str(p))
 bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/models/gen'/(name+'.glb')),export_format='GLB')
 bpy.ops.wm.open_mainfile(filepath=str(p))
 assert any(o.type=='MESH' for o in bpy.context.scene.objects)
 print('PORTION_ASSET_PASS',name)
fresh();rng=random.Random(2610)
gold=mat('batata_dourada',(.74,.49,.18),.85)
edge=mat('pontas_crocantes',(.42,.23,.065),.92)
salt=mat('sal_fino',(.93,.91,.83),.9)
for i in range(34):
 x,y=rng.uniform(-.08,.08),rng.uniform(-.055,.055)
 length=rng.uniform(.048,.092);angle=rng.uniform(-1.3,1.3)
 ob=box((length,.009,.010),(x,y,.009+(i//12)*.012),gold,bevel=.0025)
 ob.rotation_euler.z=angle
 for sign in [-1,1]:
  end=box((.006,.0095,.0105),(x+sign*(length*.5-.003)*math.cos(angle),y+sign*(length*.5-.003)*math.sin(angle),ob.location.z),edge,bevel=.002)
  end.rotation_euler.z=angle
 for j in range(2):pebble((x+rng.uniform(-.01,.01),y,.016+(i//12)*.012),(.0007,.0007,.0004),salt,'cristal_sal')
save('dish_fries')
fresh();rng=random.Random(2611)
crust=mat('crosta_peixe',(.59,.34,.11),.9)
crumb=mat('farinha_dourada',(.81,.58,.26),.92)
flesh=mat('lasca_peixe_branco',(.88,.85,.76),.85)
herb=mat('salsinha',(.16,.27,.065),.9)
lemon=mat('limao_polpa',(.74,.76,.29),.75)
peel=mat('casca_limao',(.23,.35,.075),.85)
for i in range(3):
 points=[(-.048,-.019),(-.030,-.026),(.031,-.021),(.053,-.006),(.032,.017),(-.025,.021),(-.052,.009)]
 ob=extruded_outline(points,.021,crust,'file_peixe',.005)
 ob.location=(0,-.047+i*.043,.006+i*.002)
 ob.rotation_euler.z=(i-1)*.16
 for j in range(45):
  x,y=rng.uniform(-.04,.04),rng.uniform(-.015,.015)
  pebble((x,-.047+i*.043+y,.03+i*.002),(.0018,.0014,.0011),crumb,'crocante')
 pebble((.042,-.047+i*.043,.022),(.011,.010,.004),flesh,'carne_em_lascas')
for i in range(2):
 ob=extruded_outline([(-.023,-.014),(.023,-.014),(.014,.017),(-.014,.017)],.013,lemon,'gomo_limao',.002)
 ob.location=(-.061+i*.12,.067,.004)
 ob=box((.046,.004,.014),(-.061+i*.12,.053,.010),peel,bevel=.002)
for i in range(18):pebble((rng.uniform(-.07,.07),rng.uniform(-.06,.05),.035),(.003,.0016,.0005),herb,'salsa')
save('dish_fish_portion')
