"""Detailed original countertop set, in the existing kiosk coordinate system."""
from pathlib import Path
ROOT_PATH=Path(__file__).resolve().parents[1]
exec((ROOT_PATH/'tools/gen_kiosk_facade.py').read_text(encoding='utf-8').split('# Balcão:')[0])
paper=material('counter_warm_paper',(.88,.85,.73),.9)
steel=material('counter_brushed_steel',(.20,.26,.25),.42)
# Menu stand, brass hinges and inset printed card.
for y,angle in [(-1.98,-.12),(-1.80,.12)]:
    box('Menu wood stand',(.39,.028,.40),(-.90,y,.205),wood,.012,(angle,0,0))
box('Menu inset paper',(.34,.008,.32),(-.90,-2.017,.218),paper,.006)
box('Menu back inset paper',(.34,.008,.32),(-.90,-1.763,.218),paper,.006)
path('Menu brass top hinge',[(-1.07,-1.89,.40),(-.73,-1.89,.40)],.009,brass)
# Serving tray with a recessed base and raised rounded perimeter.
box('Serving tray inset base',(.65,.38,.025),(.20,-1.98,.016),wood,.018)
for z in [.034,.052]:
    coords=[]
    for cx,cy,start in [(-.08,-2.10,math.pi),(.48,-2.10,-math.pi/2),(.48,-1.86,0),(-.08,-1.86,math.pi/2)]:
        coords += [(cx+.045*math.cos(start+i*math.pi/16),cy+.045*math.sin(start+i*math.pi/16),z) for i in range(9)]
    path('Serving tray carved rim',coords,.014,wood,True)
for x in [-.15,.55]:
    path('Tray brass carry handle',[(x,-2.06,.045),(x,-2.06,.085),(x,-1.90,.085),(x,-1.90,.045)],.007,brass)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.convert(target='MESH')
os.makedirs(SOURCE,exist_ok=True)
source=os.path.join(SOURCE,'kiosk_counter_details.blend')
bpy.ops.wm.save_as_mainfile(filepath=source)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'kiosk_counter_details.glb'),export_format='GLB',export_apply=True)
bpy.ops.wm.open_mainfile(filepath=source)
assert all(i.packed_file for i in bpy.data.images if i.source=='FILE')
print('COUNTER_DETAILS_PORTABLE PASS')
