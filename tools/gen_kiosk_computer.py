"""Original desktop terminal: bevelled monitor, stand, keyboard and mouse."""
import bpy
from gen_coastal_traffic import box,save
from gen_code_props import mat
bpy.ops.wm.read_factory_settings(use_empty=True)
case=mat('terminal graphite',(.055,.065,.063));edge=mat('terminal aluminium',(.32,.34,.33))
glass=mat('terminal glass',(.025,.055,.05));screen=mat('terminal screen',(.12,.24,.20))
paper=mat('terminal dashboard',(.68,.72,.65));key=mat('terminal keys',(.10,.12,.11))
box((.24,.15,.018),(0,0,.009),edge)
box((.045,.04,.16),(0,.015,.092),edge)
box((.44,.045,.285),(0,0,.31),case,.018)
box((.409,.009,.252),(0,-.025,.31),glass)
box((.391,.006,.235),(0,-.031,.31),screen)
for row in range(2):
    for col in range(3):box((.102,.003,.075),(-.123+col*.123,-.036,.26+row*.1),paper,.005)
box((.32,.115,.015),(0,-.18,.010),case)
for row in range(4):
    for col in range(12):box((.020,.017,.008),(-.14+col*.025,-.22+row*.025,.021),key,.003)
box((.065,.10,.025),(.235,-.18,.017),case,.012)
box((.008,.022,.008),(.235,-.19,.033),edge,.003)
save('kiosk_computer')
