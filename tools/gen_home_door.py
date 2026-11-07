"""Panelled wooden house door with brass hardware, hinge at origin."""
from pathlib import Path
import bpy
from gen_coastal_traffic import box,save
root=Path(__file__).resolve().parents[1]
exec((root/'tools/gen_kiosk_facade.py').read_text(encoding='utf-8').split('# Balcão:')[0])
doorwood=material('home_door_oak',(.58,.43,.29),texture='oak_wood_planks_diff.jpg')
for x in [-1.095,-.055]:box('Door stile',(.11,.065,2.2),(x,0,1.1),doorwood,.008)
for z in [.065,.74,1.47,2.135]:box('Door rail',(1.04,.065,.13),(-.575,0,z),doorwood,.008)
for z in [.40,1.10,1.80]:
    box('Recessed door panel',(.93,.035,.57),(-.575,0,z),doorwood,.008)
    for face in [-1,1]:
        for x in [-1.035,-.115]:box('Panel moulding',(.025,.025,.57),(x,face*.023,z),doorwood,.007)
        for zz in [z-.285,z+.285]:box('Panel moulding',(.94,.025,.025),(-.575,face*.023,zz),doorwood,.007)
for face in [-1,1]:
    box('Handle escutcheon',(.035,.018,.16),(-.99,face*.046,1.0),brass,.008)
    path('Brass handle',[(-.99,face*.055,1.03),(-.99,face*.10,1.03),(-.87,face*.10,1.03)],.014,brass)
for z in [.25,1.1,1.95]:lathe('Door hinge',[(.017,0),(.017,.10)],(-.005,0,z),brass)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.convert(target='MESH')
save('player_home_door')
