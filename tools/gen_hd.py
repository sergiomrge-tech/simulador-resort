# Gera versões HD (PC) de reboco branco e pedra clara + texturas de capim/arbusto (alpha) para a vegetação.
import os; ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, os, shutil, random, math
T=os.path.join(ROOT,'assets')+'/'+'tex_hd/'
def recolor(src, base, k, dst):
    g=np.asarray(Image.open(T+src).convert('L')).astype(np.float32); g=(g-g.mean())/(g.std()+1e-3)
    out=np.clip(np.array(base,np.float32)[None,None,:]+g[...,None]*k,0,255).astype(np.uint8)
    Image.fromarray(out).save(T+dst,quality=92)
if os.path.exists(T+'grey_plaster_02_diff.jpg'):
    recolor('grey_plaster_02_diff.jpg',[244,240,232],6,'white_plaster_diff.jpg')
    for s in ('nor','rough'): shutil.move(T+f'grey_plaster_02_{s}.jpg',T+f'white_plaster_{s}.jpg')
    os.remove(T+'grey_plaster_02_diff.jpg')
recolor('patio_tiles_diff.jpg',[196,186,166],18,'light_stone_diff.jpg')
for s in ('nor','rough'): shutil.copy(T+f'patio_tiles_{s}.jpg',T+f'light_stone_{s}.jpg')
random.seed(3)
# capim de restinga: tufo de folhas finas
W,H=512,512; im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
for i in range(140):
    x0=W/2+random.gauss(0,60); h=random.uniform(0.45,0.98)*H; bend=random.uniform(-120,120)
    g=random.randint(90,150); col=(int(g*0.75),g,int(g*0.35),255)
    if random.random()<0.25: col=(int(g*1.1),int(g*0.95),int(g*0.5),255)  # pontas secas
    pts=[]
    for k in range(12):
        t=k/11; pts.append((x0+bend*t*t, H-1-h*t))
    for k in range(11):
        w=max(1,int(6*(1-k/11)))
        d.line([pts[k],pts[k+1]],fill=col,width=w)
im.save(T+'grass_tuft.png')
# arbusto: folhas ovais
im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
for i in range(900):
    a=random.uniform(0,math.tau); r=random.uniform(0,1)**0.6*230
    x=W/2+math.cos(a)*r; y=H*0.55+math.sin(a)*r*0.8
    if y>H-10: continue
    g=random.randint(70,140); col=(int(g*0.55),g,int(g*0.3),255)
    s=random.uniform(9,18); ang=random.uniform(0,180)
    leaf=Image.new('RGBA',(int(s*2),int(s*2)),(0,0,0,0)); ImageDraw.Draw(leaf).ellipse([0,s*0.6,s*2,s*1.4],fill=col)
    leaf=leaf.rotate(ang,expand=True); im.alpha_composite(leaf,(int(x-leaf.width/2),int(y-leaf.height/2)))
for i in range(25):  # flores (bougainville)
    x=random.uniform(120,390); y=random.uniform(100,330)
    d.ellipse([x-6,y-6,x+6,y+6],fill=(220,60,140,255))
im.save(T+'bush.png')
print('ok')
