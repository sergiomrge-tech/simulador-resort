# Pedra portuguesa (calçadão em ondas preto/branco) procedural e tileável: albedo, normal, rugosidade.
import os; os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, random, math
random.seed(11)
S=2048; cell=44
alb=Image.new("RGB",(S,S),(140,132,118)); hgt=Image.new('L',(S,S),0)
da=ImageDraw.Draw(alb); dh=ImageDraw.Draw(hgt)
def is_black(x,y):
    # ondas de Copacabana: faixas deslocadas por um seno (período = S/2 em y, S em x -> tileável)
    v=(y + 120*math.sin(2*math.pi*x/S*2)) % (S/2)
    return v < S/4
n=S//cell
for gy in range(n):
    for gx in range(n):
        cx=gx*cell+cell/2+random.uniform(-6,6); cy=gy*cell+cell/2+random.uniform(-6,6)
        r=cell*0.6; pts=[]
        a0=random.uniform(0,math.pi/2)
        for k in range(random.choice([4,5,5,6])):
            a=a0+k*2*math.pi/len(range(5))+random.uniform(-0.25,0.25)
            rr=r*random.uniform(0.8,1.15); pts.append((cx+math.cos(a)*rr, cy+math.sin(a)*rr))
        b=is_black(cx,cy)
        base=random.randint(28,48) if b else random.randint(205,238)
        col=(base,base-2,base-6) if not b else (base,base,base+3)
        for ox in (-S,0,S):
            for oy in (-S,0,S):
                pp=[(x+ox,y+oy) for x,y in pts]
                da.polygon(pp,fill=col); dh.polygon(pp,fill=random.randint(170,255))
a=np.asarray(alb).astype(np.float32)
noise=np.random.default_rng(1).normal(0,6,(S,S,1)); a=np.clip(a+noise,0,255).astype(np.uint8)
Image.fromarray(a).save('assets/tex_hd/calcada_diff.jpg',quality=92)
h=np.asarray(hgt.filter(ImageFilter.GaussianBlur(3))).astype(np.float32)/255.0
gx=np.roll(h,-1,1)-np.roll(h,1,1); gy=np.roll(h,-1,0)-np.roll(h,1,0)
nz=np.ones_like(h)*0.25; nrm=np.stack([-gx,gy,nz],-1); nrm/=np.linalg.norm(nrm,axis=-1,keepdims=True)
Image.fromarray(((nrm*0.5+0.5)*255).astype(np.uint8)).save('assets/tex_hd/calcada_nor.jpg',quality=92)
rough=np.clip(0.95-h*0.3,0,1)*255
Image.fromarray(rough.astype(np.uint8)).resize((1024,1024)).save('assets/tex_hd/calcada_rough.jpg',quality=90)
Image.open('assets/tex_hd/calcada_diff.jpg').resize((1024,1024),Image.LANCZOS).save('assets/tex/calcada_diff.jpg',quality=88)
Image.open('assets/tex_hd/calcada_nor.jpg').resize((512,512),Image.LANCZOS).save('assets/tex/calcada_nor.jpg',quality=88)
print('ok')
