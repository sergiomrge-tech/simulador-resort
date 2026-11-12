"""Coastal home fitted joinery and sewn curtains; metres, Blender front -Y."""
from pathlib import Path
ROOT_PATH=Path(__file__).resolve().parents[1]
exec((ROOT_PATH/'tools/gen_kiosk_facade.py').read_text(encoding='utf-8').split('# Balcão:')[0])
chalk=material('home_chalk_joinery',(.76,.79,.75),.8)
sage=material('home_sage_cabinets',(.25,.42,.39),.75)
stone=material('home_pale_worktop',(.78,.79,.73),.7,texture='light_stone_diff.jpg') if os.path.exists(os.path.join(ROOT,'assets/tex/light_stone_diff.jpg')) else material('home_pale_worktop',(.78,.79,.73))
linen=material('home_linen',(.85,.85,.77),.98)
metal=material('home_dark_hardware',(.12,.18,.18),.4)
ceramic=material('home_ceramic',(.88,.90,.87),.3)
# Fitted kitchen: recessed door panels, face frames, kickboard and stone edge.
box('Kitchen recessed plinth',(.56,2.18,.10),(3.08,.80,.05),metal)
box('Kitchen carcass',(.62,2.25,.76),(3.06,.80,.48),chalk)
for y in [-.025,.525,1.075,1.625]:
    box('Sage framed door',(.045,.53,.65),(2.728,y,.49),sage,.008)
    box('Recessed centre panel',(.018,.43,.54),(2.699,y,.49),sage,.008)
    for yy in [y-.235,y+.235]:box('Door frame stile',(.024,.025,.61),(2.680,yy,.49),chalk,.004)
    path('Brushed door pull',[(2.669,y-.07,.72),(2.645,y-.07,.72),(2.645,y+.07,.72),(2.669,y+.07,.72)],.006,metal)
box('Stone eased worktop',(.72,2.35,.055),(3.04,.80,.915),stone,.018)
# Recessed sink with rolled rim and a real curved basin, above a dark inset.
box('Sink dark recess',(.44,.54,.008),(3.04,.25,.947),metal,.06)
lathe('Glazed sink basin',[(.0,-.105),(.10,-.10),(.18,-.05),(.23,.0),(.245,.015),(.225,.023),(.205,.007),(.14,-.055),(.0,-.065)],(3.04,.25,.957),ceramic)
path('Gooseneck faucet',[(3.29,.25,.95),(3.29,.25,1.16),(3.27,.25,1.23),(3.21,.25,1.27),(3.14,.25,1.25),(3.11,.25,1.19)],.012,metal)
path('Tap control',[(3.29,.36,.96),(3.29,.36,1.03),(3.25,.36,1.04)],.008,metal)
for y in [i*.205-.30 for i in range(12)]:
    for z in [1.10,1.27,1.44]:box('Glazed backsplash tile',(.018,.197,.16),(3.335,y,z),ceramic,.005)
for y in [.28,1.35]:
    box('Floating kitchen shelf',(.28,.90,.045),(3.19,y,1.91),chalk)
    for yy in [y-.32,y+.32]:path('Shelf iron bracket',[(3.32,yy,1.69),(3.05,yy,1.87),(3.32,yy,1.87)],.009,metal)
# Architectural skirting and upper mouldings, with relieved profiles.
for z,thick in [(.10,.12),(2.99,.10),(3.10,.06)]:
    for x in [-3.32,3.32]:box('Side wall moulding',(thick,6.7,.11),(x,0,z),chalk)
    box('Back wall moulding',(6.7,thick,.11),(0,3.32,z),chalk)
    for x,width in [(-1.2,4.2),(2.85,1.0)]:box('Front split moulding',(width,thick,.11),(x,-3.32,z),chalk)
def curtains(cx,cy,width):
    path('Curtain rod',[(cx-width/2-.13,cy,2.45),(cx+width/2+.13,cy,2.45)],.014,metal)
    for sign in [-1,1]:
        verts=[];faces=[]
        for j in range(29):
            v=j/28;z=1.0+v*1.39
            for i in range(25):
                u=i/24
                x=cx+sign*(width/2-.12)+(u-.5)*(.30+.08*(1-v))
                y=cy+.034*math.cos(u*math.tau*4)+.015*math.sin(v*math.pi)
                verts.append((x,y,z+.008*math.cos(u*math.tau*4)*(1-v)))
        for j in range(28):
            for i in range(24):
                a=j*25+i;faces.append((a,a+1,a+26,a+25))
        me=bpy.data.meshes.new('Sewn curtain folds');me.from_pydata(verts,[],faces);me.update()
        ob=bpy.data.objects.new('Linen gathered curtain',me);bpy.context.collection.objects.link(ob);finish(ob,linen)
        sol=ob.modifiers.new('Fabric thickness','SOLIDIFY');sol.thickness=.002
        for i in range(6):
            x=cx+sign*(width/2-.12)+(i/5-.5)*.30
            # Real sewn hanging loops rather than floating cloth.
            path('Curtain hanging tab',[(x,cy,2.38),(x,cy-.025,2.47),(x,cy+.025,2.47),(x,cy,2.38)],.008,linen)
curtains(-1.7,-3.27,1.4)
curtains(-1.4,3.27,2.4)
# Shutter frames and individual angled louvers outside the front window.
for x in [-2.65,-.75]:
    for xx in [x-.19,x+.19]:box('Shutter stile',(.045,.075,1.45),(xx,-3.72,1.66),sage)
    for z in [1.0,2.32]:box('Shutter rail',(.38,.075,.055),(x,-3.72,z),sage)
    for i in range(13):box('Angled shutter louver',(.34,.075,.07),(x,-3.72,1.06+i*.095),sage,.008,(.32,0,0))
box('Front window sill',(1.70,.40,.085),(-1.7,-3.57,.96),stone)
# Save portable art source and verify by reopening, then export runtime geometry.
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.convert(target='MESH')
bpy.ops.file.pack_all()
source=os.path.join(SOURCE,'player_home_details.blend')
import tempfile,shutil
stage=os.path.join(tempfile.gettempdir(),'player_home_source.blend')
if os.path.exists(stage):os.remove(stage)
bpy.ops.wm.save_as_mainfile(filepath=stage);shutil.copyfile(stage,source);os.remove(stage)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'player_home_details.glb'),export_format='GLB',export_apply=True)
bpy.ops.wm.open_mainfile(filepath=source)
assert all(i.packed_file for i in bpy.data.images if i.source=='FILE')
print('PLAYER_HOME_PORTABLE PASS')
