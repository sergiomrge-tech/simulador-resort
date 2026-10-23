"""Fachada autoral do Maré Alta. Blender Z-up, frente -Y; unidades em metros.

Gera GLB com peças agrupadas por acabamento e fonte .blend editável/portável.
Não altera arquivos de artistas nem depende de uma sessão aberta do Blender.
Uso: build/python/Scripts/python tools/gen_kiosk_facade.py
"""
import math
import os
import random
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets/models/gen')
SOURCE = os.path.join(ROOT, 'art/blender')
random.seed(221026)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0


def material(name, color, rough=.65, texture=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    if texture:
        node = m.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(os.path.join(ROOT, 'assets/tex', texture))
        node.image.pack()
        # glTF export preserves image + base-color multiplier.
        tint = m.node_tree.nodes.new('ShaderNodeMixRGB')
        tint.blend_type = 'MULTIPLY'
        tint.inputs[0].default_value = 1
        tint.inputs[2].default_value = (*color, 1)
        m.node_tree.links.new(node.outputs['Color'], tint.inputs[1])
        m.node_tree.links.new(tint.outputs[0], p.inputs['Base Color'])
    return m


wood = material('facade_teak', (.90, .67, .40), texture='oak_wood_planks_diff.jpg')
dark = material('facade_shadow_wood', (.19, .09, .035))
paint = material('facade_paint', (.045, .34, .34))
brass = material('facade_brass', (.70, .46, .19), .34)
rope = material('facade_rope', (.66, .46, .25))
ivory = material('facade_ivory', (.92, .85, .65))
board = material('facade_board', (.025, .15, .16))
glow = material('glow_facade_warm', (1, .69, .31), .35)
leaves = material('facade_leaf', (.12, .32, .12))


def finish(ob, m):
    ob.data.materials.append(m)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def box(name, size, loc, m, bevel=.015, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    ob.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=.7)
    bpy.ops.object.mode_set(mode='OBJECT')
    mod = ob.modifiers.new('Soft crafted edges', 'BEVEL')
    mod.width = min(bevel, min(size) * .4)
    mod.segments = 3
    bpy.ops.object.modifier_apply(modifier=mod.name)
    # Weighted normals retain flat broad faces and soft edge highlights.
    mod = ob.modifiers.new('Surface normals', 'WEIGHTED_NORMAL')
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return finish(ob, m)


def path(name, coords, radius, m, closed=False):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.resolution_u = 2
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    sp = cu.splines.new('POLY')
    sp.points.add(len(coords) - 1)
    for pt, co in zip(sp.points, coords):
        pt.co = (*co, 1)
    sp.use_cyclic_u = closed
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(m)
    return ob


def ring(name, x, y, z, radius, tube, m):
    return path(name, [(x + radius * math.cos(t), y + radius * math.sin(t), z)
                      for t in [i * math.tau / 64 for i in range(64)]], tube, m, True)


def lathe(name, profile, loc, m, sides=48):
    verts, faces = [], []
    for r, z in profile:
        verts.extend([(loc[0] + r * math.cos(i * math.tau / sides),
                       loc[1] + r * math.sin(i * math.tau / sides), loc[2] + z)
                      for i in range(sides)])
    for j in range(len(profile) - 1):
        for i in range(sides):
            a = j * sides + i
            b = j * sides + (i + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces.extend([tuple(reversed(range(sides))), tuple(range((len(profile)-1)*sides, len(verts)))])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    return finish(ob, m)


# Balcão: ripas chanfradas, rodapé, caixilhos, tampo com borda e filetes.
for side in [0, -1, 1]:
    w = 4.64 if side == 0 else 2.42
    y = -2.335 if side == 0 else -.95
    x = 0 if side == 0 else side * 2.335
    def local(u, depth, z):
        return (u, y-depth, z-.1) if side == 0 else (x+side*depth, y+u, z-.1)
    def panel(name, size, pos, mat, bevel=.012):
        return box(name, size, pos, mat, bevel, (0, 0, 0 if side == 0 else math.pi/2))
    panel('Painted backing', (w, .065, 1.08), local(0, 0, .65), paint)
    count = round(w / .115)
    for i in range(count):
        u = -w/2 + (i+.5)*w/count
        panel('Individual teak flute', (w/count-.027, .055, .87), local(u, .052, .65), wood)
    for z in [.19, 1.11]:
        panel('Teal rail', (w+.07, .10, .13), local(0, .047, z), paint)
        panel('Fine brass inlay', (w, .018, .015), local(0, .105, z+.032), brass, .003)
    for u in [-w/2, 0, w/2]:
        panel('Frame upright', (.08, .09, .95), local(u, .06, .65), paint)
    # Raised corner rivets, genuinely rounded and recessed in the rails.
    for u in [-w/2+.12, w/2-.12]:
        for z in [.19, 1.11]:
            p = local(u, .11, z)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=.014, location=p)
            finish(bpy.context.object, brass)

# Front slab remains at the existing serving height (1.28).
for j in range(4):
    box('Solid teak counter plank', (4.98, .224, .065), (0, -1.65-j*.225, 1.1475), wood, .018)
box('Rounded brass counter lip', (5.02, .038, .045), (0, -2.465, 1.135), brass)
box('Counter fascia shadow', (4.92, .07, .07), (0, -2.40, 1.065), dark)
for x in [-2.0,2.0]:
    box('Side counter solid slab',(.68,2.45,.08),(x,-.95,1.14),wood)

# Turned support posts and rope collars replace octagonal cylinders.
for x in [-2.4, 2.4]:
    for y in [-2.4, 2.4]:
        lathe('Turned teak column', [(.19,0),(.19,.09),(.15,.14),(.13,.22),(.125,.42),
              (.12,2.38),(.15,2.46),(.18,2.50),(.18,2.60),(.15,2.66),(.15,2.8)], (x,y,0), wood)
        for z in [.14, 2.48]:
            ring('Brass column collar', x,y,z,.154,.014,brass)
        for base in [.30,2.18]:
            path('Helical rope binding', [(x+.137*math.cos(t), y+.137*math.sin(t),
                 base+.008*t/math.tau) for t in [i*math.tau/24 for i in range(24*9)]], .009, rope)
        for direction in [-1, 1]:
            # Shaped knee braces meet both post and eave beam.
            path('Curved timber knee brace', [(x+direction*.60*t, y, 2.76-.55*(1-t)**2)
                 for t in [i/20 for i in range(21)]], .055, wood)

# Strong eave line, inlaid geometric fretwork, scalloped edge.
for front in [True, False]:
    for s in [-1, 1]:
        loc = (0,s*2.43,2.71) if front else (s*2.43,0,2.71)
        box('Eave timber beam', (5.08,.16,.19), loc, wood, rot=(0,0,0 if front else math.pi/2))
for s in [-1,1]:
    for i in range(25):
        x=-3.12+i*.26
        path('Scalloped eave valance', [(x+.125*math.cos(t),s*3.24,2.88-.15*math.sin(t))
             for t in [j*math.pi/16 for j in range(17)]], .023, ivory)
    box('Front fascia band', (6.5,.10,.11), (0,s*3.23,2.97), paint)
    box('Fascia brass piping', (6.52,.025,.025), (0,s*3.295,3.015), brass)
for s in [-1,1]:
    box('Side fascia band', (.10,6.5,.11), (s*3.23,0,2.97), paint)

# Sculpted sign frame sits around the existing configurable text and hitbox.
for x in [-2.04,2.04]:
    box('Sign carved upright', (.15,.16,.76), (x,-3.405,2.25), wood, .035)
    for z in [1.99,2.51]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=.032, location=(x,-3.50,z))
        finish(bpy.context.object, brass)
for z in [1.90,2.60]:
    box('Sign crown moulding', (4.25,.18,.115), (0,-3.40,z), wood, .035)
    box('Sign brass inset', (4.11,.025,.018), (0,-3.50,z), brass, .004)
for x in [-1.55,1.55]:
    for y in [-3.38]:
        for z in [2.69,2.77,2.85]:
            ring('Sign suspension chain',x,y,z,.027,.009,brass)

# Front centre seal: carved waves and sun, below serving surface.
lathe('Seal rim', [(.24,0),(.25,.012),(.25,.03),(.23,.045)], (0,0,0), brass)
seal = bpy.context.scene.objects.get('Seal rim')
seal.rotation_euler=(math.pi/2,0,0)
seal.location=(0,-2.475,.65)
lathe('Seal face', [(.222,0),(.222,.022)], (0,0,0), paint)
seal=bpy.context.scene.objects.get('Seal face')
seal.rotation_euler=(math.pi/2,0,0)
seal.location=(0,-2.51,.65)
for z in [.58,.65,.72]:
    path('Wave engraving', [(x,-2.54,z+.018*math.sin(x*26)) for x in [i*.01-.17 for i in range(35)]], .009, ivory)

# Woven pendants: curved ribs and horizontal weft, cap, cable and bulb.
for x in [-2.68, 2.68]:
    y=-3.0
    z=1.95
    profile=[(.14,0),(.23,.08),(.29,.20),(.26,.34),(.16,.43),(.065,.49)]
    for i in range(32):
        a=i*math.tau/32
        path('Rattan pendant rib', [(x+r*math.cos(a), y+r*math.sin(a),z+h) for r,h in profile], .008, rope)
    for i in range(17):
        h=.03+i*.026
        j=next((j for j in range(len(profile)-1) if profile[j][1]<=h<=profile[j+1][1]),len(profile)-2)
        r0,h0=profile[j]; r1,h1=profile[j+1]
        r=r0+(r1-r0)*(h-h0)/(h1-h0)
        ring('Woven horizontal weft',x,y,z+h,r,.0065,ivory)
    lathe('Pendant socket',[(.05,0),(.05,.10),(.025,.13)],(x,y,z+.38),brass)
    path('Pendant cable',[(x,y,z+.50),(x,y,2.79)],.012,dark)
    box('Pendant bracket',(.50,.09,.09),(math.copysign(2.48,x),y,2.78),wood)
    box('Pendant bracket return',(.09,.72,.09),(x,-2.68,2.78),wood)
    lathe('Warm lamp bulb',[(.025,0),(.06,.04),(.065,.10),(.05,.16),(.02,.18)],(x,y,z+.16),glow)

# Full rear wall behind the working stations. Blender +Y faces Godot -Z.
box('Rear wall backing', (4.65, .12, 2.64), (0, 2.40, 1.32), dark)
for i in range(31):
    box('Rear teak wall plank', (.146, .055, 2.61), (-2.25+i*.15, 2.31, 1.32), wood, .008)
for z in [.10, 1.94, 2.56]:
    box('Rear wall horizontal rail', (4.70, .085, .10), (0, 2.26, z), paint)
for x in [-2.30, 0, 2.30]:
    box('Rear wall stile', (.085, .085, 2.65), (x, 2.26, 1.325), paint)

# Join by material, keeping paint and sign independently customizable.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.convert(target='MESH')
for m in list(bpy.data.materials):
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH' and len(o.data.materials)==1 and o.data.materials[0]==m]
    if not obs:
        continue
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs: ob.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.object.join()
    ob=bpy.context.object
    ob.name=m.name
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

os.makedirs(OUT,exist_ok=True)
os.makedirs(SOURCE,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SOURCE,'kiosk_facade.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'kiosk_facade.glb'),export_format='GLB',export_apply=True)
print('KIOSK_FACADE',len(bpy.context.scene.objects),'meshes',sum(len(o.data.polygons) for o in bpy.context.scene.objects),'faces')
# Verify the saved, packed source can be reopened.
bpy.ops.wm.open_mainfile(filepath=os.path.join(SOURCE,'kiosk_facade.blend'))
assert all(i.packed_file for i in bpy.data.images if i.source=='FILE'), 'Unpacked external texture'
print('KIOSK_BLEND_PORTABLE PASS')

# Separate upgrade model: neat continuous neon around the single main sign.
bpy.ops.wm.read_factory_settings(use_empty=True)
neon = material('glow_neon_turquoise', (.15,.85,.78), .3)
corners=[(-1.94,-3.515,1.965),(1.94,-3.515,1.965),(2.0,-3.515,2.025),
         (2.0,-3.515,2.475),(1.94,-3.515,2.535),(-1.94,-3.515,2.535),
         (-2.0,-3.515,2.475),(-2.0,-3.515,2.025)]
path('Continuous neon sign border',corners,.013,neon,True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.convert(target='MESH')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SOURCE,'kiosk_neon_trim.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'kiosk_neon_trim.glb'),export_format='GLB',export_apply=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(SOURCE,'kiosk_neon_trim.blend'))
assert len(bpy.context.scene.objects) == 1
print('KIOSK_NEON_BLEND_PORTABLE PASS')

# Cobertura em fiadas sobrepostas: cada feixe tem caneluras, borda e espessura.
# A cobertura estrutural do cenário continua por baixo, fechando o forro.
bpy.ops.wm.read_factory_settings(use_empty=True)
# glTF colors are linear; leave headroom for the game's Toon.toonify lift.
straw = [material('roof_straw_%d' % i, (.32+i*.018,.195+i*.014,.075+i*.008)) for i in range(5)]
cap = material('roof_bound_reed',(.26,.14,.055))
verts, faces, slots = [], [], []
def vertex(u,r,h,angle):
    return (u*math.cos(angle)+r*math.sin(angle),u*math.sin(angle)-r*math.cos(angle),h)
for side in range(4):
    angle=side*math.pi/2
    for row in range(12):
        r0=3.34*(1-row/12)
        r1=max(.015,3.34*(1-(row+1.18)/12))
        count=max(1,round(r0*2/.24))
        for col in range(count):
            a=-r0+col*2*r0/count
            b=a+2*r0/count
            start=len(verts)
            slot=random.randrange(len(straw))
            for j in range(4):
                t=j/3
                r=r0*(1-t)+r1*t
                for i in range(9):
                    u=(a+(b-a)*i/8)*r/r0
                    h=2.8+(1-r/3.34)*1.8+.04+.04*(1-t)**2
                    h+=.012*math.sin(i*math.pi/2)**2
                    verts.append(vertex(u,r,h,angle))
            for j in range(3):
                for i in range(8):
                    q=start+j*9+i
                    faces.append((q,q+1,q+10,q+9))
                    slots.append(slot)
            # Thatch bundle lip: not a zero-thickness card.
            for i in range(9):
                v=verts[start+i]
                verts.append((v[0],v[1],v[2]-.04))
            for i in range(8):
                faces.append((start+i,start+36+i,start+37+i,start+i+1))
                slots.append(slot)
mesh=bpy.data.meshes.new('Overlapping grooved thatch bundles')
mesh.from_pydata(verts,[],faces)
mesh.update()
roof=bpy.data.objects.new('Twelve thatch courses',mesh)
bpy.context.scene.collection.objects.link(roof)
for m in straw: mesh.materials.append(m)
for p,slot in zip(mesh.polygons,slots): p.material_index=slot; p.use_smooth=True
# Bind the four hips with bundles of reeds rather than giant round beams.
for angle in [math.pi/4+i*math.pi/2 for i in range(4)]:
    for offset in [-.037,0,.037]:
        path('Bound reed hip seam',[(r*math.cos(angle)+offset,r*math.sin(angle)-offset,
             2.88+(1-r/(3.34*math.sqrt(2)))*1.8) for r in [3.34*math.sqrt(2)*(1-i/40) for i in range(41)]],.028,cap)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.convert(target='MESH')
bpy.context.view_layer.objects.active=roof
bpy.ops.object.join()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SOURCE,'kiosk_roof.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'kiosk_roof.glb'),export_format='GLB',export_apply=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(SOURCE,'kiosk_roof.blend'))
print('KIOSK_ROOF_BLEND_PORTABLE PASS')

# Cozinha compacta: portas com puxadores, chapa e tábua no mesmo móvel.
bpy.ops.wm.read_factory_settings(use_empty=True)
steel=material('workbench_brushed_steel',(.34,.40,.41),.3)
enamel=material('workbench_teal',(.035,.21,.22))
black=material('workbench_cast_iron',(.025,.03,.03),.7)
wood=material('workbench_cutting_board',(.43,.22,.08))
for x in [-.46,.46]:
    for y in [-.25,.25]:
        lathe('Adjustable kitchen foot',[(.035,0),(.035,.09),(.025,.12)],(x,y,0),steel)
box('Enamel cabinet carcass',(1.1,.60,.73),(0,0,.47),enamel)
for x in [-.27,.27]:
    box('Inset cabinet door',(.51,.035,.61),(x,-.318,.47),enamel,.018)
    path('Cabinet handle',[(x-.09,-.35,.66),(x-.09,-.39,.66),(x+.09,-.39,.66),(x+.09,-.35,.66)],.012,steel)
box('Stainless kitchen worktop',(1.14,.66,.065),(0,0,.865),steel)
box('Cast iron griddle',(.53,.46,.025),(.27,0,.91),black)
for x in [.07,.47]:
    for y in [-.21,.21]: box('Griddle rim',(.02,.44,.05),(x,0,.93),steel)
for i in range(12): box('Griddle rib',(.40,.012,.012),(.27,-.19+i*.034,.93),black,.004)
box('Cutting board',(.43,.34,.03),(-.29,-.07,.918),wood,.03)
for y in [-.29,.29]: box('Counter rounded edge',(1.10,.025,.035),(0,y,.91),steel)
for x in [-.20,0,.20]:
    ring('Control dial',x,-.34,.77,.025,.008,steel)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.convert(target='MESH')
os.makedirs(SOURCE,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SOURCE,'kiosk_workbench.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'kiosk_workbench.glb'),export_format='GLB',export_apply=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(SOURCE,'kiosk_workbench.blend'))
print('KIOSK_WORKBENCH_BLEND_PORTABLE PASS')

bpy.ops.wm.read_factory_settings(use_empty=True)
enamel=material('blender_teal_base',(.025,.20,.21),.4)
steel=material('blender_steel',(.38,.43,.44),.3)
rubber=material('blender_rubber',(.025,.025,.027))
glass=material('blender_clear_glass',(.8,.8,.8),.16)
shader=next(n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
shader.inputs['Alpha'].default_value=.22
box('Weighted motor base',(.24,.23,.14),(0,0,.08),enamel,.035)
box('Rubber base pad',(.22,.21,.02),(0,0,.01),rubber)
lathe('Glass graduated jug',[(.07,0),(.08,.02),(.10,.24),(.105,.25),(.09,.25),(.065,.025)],(0,0,.15),glass)
lathe('Rubber lid',[(.106,0),(.106,.025),(.045,.04),(.045,.06)],(0,0,.40),rubber)
path('Jug handle',[(.09,0,.20),(.15,0,.22),(.16,0,.36),(.105,0,.38)],.014,steel)
for z in [.22,.27,.32,.37]: path('Measurement mark',[(-.025,-.092,z),(.025,-.092,z)],.002,steel)
box('Power switch',(.055,.015,.026),(0,-.12,.08),rubber,.006)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.convert(target='MESH')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SOURCE,'kiosk_blender.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'kiosk_blender.glb'),export_format='GLB',export_apply=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(SOURCE,'kiosk_blender.blend'))
print('KIOSK_BLENDER_PORTABLE PASS')
