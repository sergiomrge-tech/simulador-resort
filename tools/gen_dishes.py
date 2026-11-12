"""Pratos brasileiros originais para o quiosque; GLB detalhado, base Z=0.
Utensílios são Kenney Food Kit CC0; estes recheios são autoria do projeto.
A semente fixa mantém o mesmo alimento em todos os builds.
"""
import math, random
import bpy, bmesh
from gen_code_props import fresh, mat, box, lathe, tube, join, export
from gen_food import _mesh_obj, _glass_mat, sweep


def pebble(pos, scale, material, name='ingrediente'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1, location=pos)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(material)
    for face in ob.data.polygons:
        face.use_smooth = True
    return ob


def extruded_outline(points, height, material, name, bevel=0.003):
    bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')
    low = [bm.verts.new((x, y, 0)) for x, y in points]
    high = [bm.verts.new((x, y, height)) for x, y in points]
    bm.faces.new(list(reversed(low)))
    bm.faces.new(high)
    for i in range(len(points)):
        j = (i + 1) % len(points)
        bm.faces.new((low[i], low[j], high[j], high[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = _mesh_obj(bm, name, [material], 0.0, 0)
    bv = ob.modifiers.new('borda_suave', 'BEVEL')
    bv.width = bevel
    bv.segments = 3
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=bv.name)
    return ob


def finish(parts, name):
    join(parts, name)
    export(name)


def petiscos():
    fresh()
    rng = random.Random(4101)
    gold = mat('empanado_dourado', (0.72, 0.39, 0.11), 0.92)
    crumb = mat('farelo_crocante', (0.94, 0.66, 0.26), 0.95)
    lemon = mat('limao_polpa', (0.76, 0.89, 0.25), 0.7)
    parts = []
    for i in range(7):
        a = i * math.tau / 7
        x, y = math.cos(a)*0.051, math.sin(a)*0.045
        o = box((0.057, 0.024, 0.019), (x, y, 0.016), gold, bevel=0.008)
        o.rotation_euler.z = a + 0.4
        parts.append(o)
        for _ in range(9):
            parts.append(pebble((x+rng.uniform(-0.021,0.021), y+rng.uniform(-0.009,0.009), 0.026), (0.002,0.002,0.0014), crumb))
    parts.append(extruded_outline([(-0.025,-0.025),(0.025,-0.025),(0,0.017)],0.016,lemon,'gomo_limao'))
    finish(parts,'dish_petiscos')


def tapioca():
    fresh()
    white = mat('goma_branca', (0.96,0.93,0.83), 0.94)
    grain = mat('graos_tapioca', (1.0,0.98,0.91), 0.96)
    cheese = mat('queijo_derretido', (0.94,0.76,0.34), 0.55)
    pts = [(0.103*math.cos(i*math.pi/40),0.103*math.sin(i*math.pi/40)-0.045) for i in range(41)]
    parts=[extruded_outline(pts,0.022,white,'meia_lua_tapioca',0.003)]
    rng=random.Random(4102)
    for _ in range(95):
        x,y=rng.uniform(-0.096,0.096),rng.uniform(-0.038,0.05)
        if x*x+(y+0.045)**2<0.098**2:
            parts.append(pebble((x,y,0.022),(0.0021,0.0021,0.0009),grain))
    for i in range(6):
        parts.append(box((0.022,0.007,0.007),(-0.065+i*0.025,-0.045,0.01),cheese,bevel=0.002))
    finish(parts,'dish_tapioca')


def pastel():
    fresh()
    gold=mat('massa_frita',(0.87,0.52,0.15),0.88)
    rim=mat('borda_prensada',(0.64,0.31,0.075),0.91)
    bubbles=mat('bolhas_douradas',(0.98,0.69,0.28),0.88)
    parts=[box((0.182,0.105,0.027),(0,0,0.016),gold,bevel=0.012)]
    for side in [-1,1]:
        for i in range(13):
            parts.append(box((0.007,0.008,0.004),(-0.077+i*0.0128,side*0.049,0.019),rim,bevel=0.001))
        for i in range(6):
            parts.append(box((0.008,0.007,0.004),(side*0.086,-0.034+i*0.0135,0.019),rim,bevel=0.001))
    rng=random.Random(4103)
    for _ in range(24):
        parts.append(pebble((rng.uniform(-0.069,0.069),rng.uniform(-0.032,0.032),0.029),(0.0038,0.0038,0.0015),bubbles))
    finish(parts,'dish_pastel')


def acai():
    fresh()
    purple=mat('creme_acai',(0.24,0.055,0.19),0.55)
    banana=mat('banana_clara',(0.97,0.87,0.56),0.72)
    seed=mat('centro_banana',(0.51,0.32,0.15),0.8)
    granola=mat('granola',(0.68,0.39,0.13),0.94)
    parts=[lathe([(0,0),(0.08,0),(0.092,0.012),(0.09,0.019),(0,0.019)],purple,verts=48)]
    for i in range(6):
        x=-0.06+i*0.022
        parts.append(lathe([(0,0),(0.014,0),(0.014,0.006),(0,0.006)],banana,(x,0.025,0.02),verts=24))
        parts.append(pebble((x,0.025,0.027),(0.0025,0.0015,0.0007),seed))
    rng=random.Random(4104)
    for _ in range(38):
        parts.append(pebble((rng.uniform(-0.06,0.06),rng.uniform(-0.04,-0.006),0.022),(0.0035,0.0024,0.0022),granola))
    finish(parts,'dish_acai')


def moqueca():
    fresh()
    broth=mat('caldo_dende',(0.91,0.37,0.085),0.48)
    fish=mat('posta_peixe',(0.94,0.85,0.65),0.72)
    shrimp=mat('camarao_cozido',(1.0,0.53,0.31),0.63)
    tomato=mat('tomate',(0.76,0.12,0.05),0.58)
    herb=mat('coentro',(0.12,0.36,0.095),0.82)
    parts=[lathe([(0,0),(0.084,0),(0.094,0.014),(0.091,0.02),(0,0.02)],broth,verts=48)]
    for x,y,a in [(-0.035,0.018,0.4),(0.03,0.025,-0.4),(0,-0.035,0.1)]:
        o=pebble((x,y,0.026),(0.024,0.031,0.009),fish,'posta_peixe');o.rotation_euler.z=a;parts.append(o)
    for x,y in [(-0.047,-0.024),(0.048,-0.015)]:
        pts=[(x+0.015*math.cos(0.4+i*4.8/15), y+0.015*math.sin(0.4+i*4.8/15), 0.03) for i in range(16)]
        parts.append(sweep(pts,0.005,shrimp,10,'camarao'))
    for i in range(8):
        a=i*math.tau/8
        parts.append(pebble((math.cos(a)*0.069,math.sin(a)*0.066,0.026),(0.009,0.005,0.002),tomato))
        parts.append(pebble((math.cos(a+0.3)*0.055,math.sin(a+0.3)*0.057,0.034),(0.007,0.003,0.0008),herb))
    finish(parts,'dish_moqueca')


def batida():
    fresh()
    glass=_glass_mat("vidro_batida",0.28)
    milk=mat('batida_de_coco',(0.95,0.93,0.82),0.4)
    foam=mat('espuma_coco',(1.0,0.98,0.91),0.68)
    straw=mat('canudo_turquesa',(0.06,0.52,0.53),0.7)
    parts=[lathe([(0,0),(0.029,0),(0.034,0.005),(0.042,0.145),(0.039,0.145),(0.031,0.008),(0,0.008)],glass,verts=40)]
    parts.append(lathe([(0,0.009),(0.03,0.009),(0.037,0.125),(0,0.125)],milk,verts=40))
    parts.append(lathe([(0,0.126),(0.037,0.126),(0.036,0.133),(0,0.133)],foam,verts=40))
    parts.append(tube((-0.012,0,0.05),(-0.025,0.01,0.2),0.003,straw,12))
    finish(parts,'dish_batida')


if __name__=='__main__':
    for fn in [petiscos,tapioca,pastel,acai,moqueca,batida]:fn()
    print('gen_dishes ok')
