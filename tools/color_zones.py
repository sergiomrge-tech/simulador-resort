# Adds COLOR_0 zone ids to the Quaternius mannequin so one shader can paint clothes/skin/hair.
# zone (R channel *255/32): 0 skin, 1 shirt, 2 shorts, 3 hair, 4 sandals
import json,struct,numpy as np,sys
src,dst=sys.argv[1],sys.argv[2]
b=open(src,'rb').read(); l=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+l])
binlen=struct.unpack('<I',b[20+l:24+l])[0]; bin_=bytearray(b[28+l:28+l+binlen])
def acc(i):
    a=j['accessors'][i]; bv=j['bufferViews'][a['bufferView']]
    off=bv.get('byteOffset',0)+a.get('byteOffset',0); n=a['count']
    return np.frombuffer(bytes(bin_[off:off+n*12]),np.float32).reshape(n,3)
for m in j['meshes']:
  for p in m['primitives']:
    P=acc(p['attributes']['POSITION']); x,y,z=np.abs(P[:,0]),P[:,1],P[:,2]
    zone=np.zeros(len(P),np.uint8)
    torso=(y>0.93)&(y<1.50)&(x<0.24); zone[torso]=1
    sleeve=(y>1.2)&(x>=0.24)&(x<0.50); zone[sleeve]=1
    shorts=(y>0.52)&(y<=0.97)&(x<0.26); zone[shorts]=2
    hair=((y>1.70)|((y>1.56)&(z<-0.04)))&(x<0.13); zone[hair]=3
    feet=y<0.085; zone[feet]=4
    col=np.zeros((len(P),4),np.uint8); col[:,0]=zone*32; col[:,3]=255
    while len(bin_)%4: bin_.append(0)
    off=len(bin_); bin_+=col.tobytes()
    j['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':col.nbytes,'target':34962})
    j['accessors'].append({'bufferView':len(j['bufferViews'])-1,'componentType':5121,'normalized':True,'count':len(P),'type':'VEC4'})
    p['attributes']['COLOR_0']=len(j['accessors'])-1
    print('zones',np.bincount(zone,minlength=5))
while len(bin_)%4: bin_.append(0)
j['buffers'][0]['byteLength']=len(bin_)
js=json.dumps(j,separators=(',',':')).encode()
while len(js)%4: js+=b' '
out=struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(bin_))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(bin_),0x004E4942)+bin_
open(dst,'wb').write(out)
