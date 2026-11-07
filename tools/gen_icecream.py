"""Sorvetes em pote e bandeja de transporte, autoria do projeto (CC0).
Fontes Blender editáveis sem dependências externas. Executar com Python+bpy.
"""
from pathlib import Path
import sys, math, random
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gen_code_props import fresh, mat, lathe, box
ROOT=Path(__file__).resolve().parents[1]
def save(name):
    for ob in bpy.context.scene.objects:
        if ob.type=='MESH':
            for f in ob.data.polygons: f.use_smooth=True
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.file.pack_all()
    target=ROOT/'art/blender'/(name+'.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/models/gen'/(name+'.glb')),export_format='GLB')
    bpy.ops.wm.open_mainfile(filepath=str(target))
    assert any(o.type=='MESH' for o in bpy.context.scene.objects)
    assert all(i.packed_file for i in bpy.data.images if i.source=='FILE')
    print('PORTABLE_ASSET_PASS',name)
def cup(flavor=None):
    fresh()
    paper=mat('papel_creme',(.87,.85,.77),.8)
    accent=mat('faixa_morango' if flavor=='strawberry' else 'faixa_cacau',(.55,.19,.21) if flavor=='strawberry' else (.24,.13,.08),.8)
    lathe([(0,0),(.032,0),(.034,.004),(.049,.075),(.05,.078),(.05,.082),(.046,.084),(.044,.078),(.029,.007),(0,.007)],paper,verts=64)
    lathe([(.039,.033),(.042,.048),(.043,.048),(.040,.033)],accent,verts=64)
    wood=mat('colher_madeira',(.61,.44,.27),.7)
    spoon=box((.010,.003,.10),(.031,0,.085),wood,bevel=.002)
    spoon.rotation_euler.y=-.25
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=(.018,0,.049))
    o=bpy.context.object;o.name='colher_concha';o.scale=(.010,.004,.016);o.data.materials.append(wood)
    if flavor:
        rng=random.Random(244)
        cream=mat('sorvete_'+flavor,(.68,.36,.38) if flavor=='strawberry' else (.25,.12,.055),.88)
        crumb=mat('pedacos_fruta' if flavor=='strawberry' else 'raspas_chocolate',(.38,.055,.045) if flavor=='strawberry' else (.10,.045,.02),.95)
        for x,y,z,r in [(-.016,-.008,.085,.035),(.017,.009,.096,.034),(-.003,.002,.120,.027)]:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,radius=r,location=(x,y,z))
            ob=bpy.context.object;ob.name='bola_cremosa';ob.data.materials.append(cream)
            for v in ob.data.vertices:
                v.co*=1+.035*math.sin(v.co.x*430)*math.cos(v.co.y*390)
        for i in range(32):
            a=rng.random()*math.tau;z=rng.uniform(.09,.14);r=.022
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.0018,location=(math.cos(a)*r,math.sin(a)*r,z))
            bpy.context.object.data.materials.append(crumb)
    save('icecream_'+flavor if flavor else 'used_icecream_cup')
for flavor in ['strawberry','chocolate',None]: cup(flavor)
fresh()
wood=mat('bandeja_madeira_natural',(.28,.18,.10),.7)
box((.40,.27,.012),(0,0,.006),wood,bevel=.012)
for x in [-.196,.196]:box((.008,.25,.023),(x,0,.016),wood,bevel=.003)
for y in [-.131,.131]:box((.38,.008,.023),(0,y,.016),wood,bevel=.003)
save('service_carry_tray')
