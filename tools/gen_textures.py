# Procedural textures: palm frond (alpha), white plaster albedo, app icon.
import os; ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np, math, random
T=os.path.join(ROOT,'assets')+'/'+'tex/'
random.seed(7)
# --- palm frond: x = along rachis (base->tip), y = across
W,H=1024,256
im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
cy=H//2
for i in range(0,W-20,7):
    t=i/W
    L=(H*0.48)*math.sin(math.pi*min(1,t*1.05+0.05))**0.7*(1-0.15*t)
    for s in (-1,1):
        ang=math.radians(55+random.uniform(-8,8))
        ex=i+L*math.cos(ang)*0.9; ey=cy+s*L*math.sin(ang)
        g=random.randint(95,140); col=(int(g*0.45),g,int(g*0.25),255)
        # tapered leaflet polygon
        wdt=3.2*(1-0.5*t)
        nx,ny=-(ey-cy),(ex-i); n=math.hypot(nx,ny) or 1; nx,ny=nx/n*wdt,ny/n*wdt
        d.polygon([(i-nx,cy-ny),(i+nx,cy+ny),(ex,ey)],fill=col)
        d.line([(i,cy),(ex,ey)],fill=(int(g*0.6),int(g*1.15),int(g*0.35),255),width=1)
d.line([(0,cy),(W-10,cy)],fill=(150,135,70,255),width=5)
im=im.filter(ImageFilter.SMOOTH)
im.save(T+'palm_frond.png')
# --- white plaster from grey plaster (keep detail, push to warm white)
import os
srcp=T+'grey_plaster_02_diff.jpg'
if not os.path.exists(srcp):
    srcp=T+'white_plaster_diff.jpg'
g=Image.open(srcp).convert('L')
a=np.asarray(g).astype(np.float32); a=(a-a.mean())/ (a.std()+1e-3)
base=np.array([244,240,232],np.float32)
out=np.clip(base[None,None,:]+a[...,None]*6,0,255).astype(np.uint8)
Image.fromarray(out).save(T+'white_plaster_diff.jpg',quality=90)
# --- app icon 512
S=512; ic=Image.new('RGB',(S,S)); p=ic.load()
for y in range(S):
    for x in range(S):
        t=y/S
        if y<S*0.62: c=(int(255-80*t),int(170+40*t),int(90+120*t))
        else: c=(20,int(120+60*(t-0.62)),int(170+40*(t-0.62)))
        p[x,y]=c
d=ImageDraw.Draw(ic)
d.ellipse([300,150,420,270],fill=(255,226,120))
d.rectangle([0,int(S*0.80),S,S],fill=(236,210,150))
for k in range(5):
    d.line([(150+k*3,440-k*60),(160+k*6,380-k*60)],fill=(110,80,50),width=22)
d.line([(140,450),(180,140)],fill=(120,88,55),width=26)
for a_ in range(0,360,40):
    r=math.radians(a_); d.line([(180,140),(180+130*math.cos(r),140+70*math.sin(r)+30)],fill=(40,130,60),width=24)
d.rounded_rectangle([40,30,472,110],radius=24,fill=(255,255,255))
try:
    from PIL import ImageFont
    f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',52)
    d.text((256,70),'MARÉ ALTA',fill=(10,110,140),font=f,anchor='mm')
except Exception as e: print(e)
ic.save(os.path.join(ROOT,'icon.png'))
print('ok')
# --- pedra clara (deck da piscina) a partir de patio_tiles: dessatura e clareia
from PIL import ImageOps
pt=Image.open(T+'patio_tiles_diff.jpg').convert('RGB')
g=np.asarray(pt.convert('L')).astype(np.float32)
g=(g-g.mean())/(g.std()+1e-3)
base=np.array([196,186,166],np.float32)
out=np.clip(base[None,None,:]+g[...,None]*18,0,255).astype(np.uint8)
Image.fromarray(out).save(T+'light_stone_diff.jpg',quality=90)
import shutil; shutil.copy(T+'patio_tiles_nor.jpg',T+'light_stone_nor.jpg')
