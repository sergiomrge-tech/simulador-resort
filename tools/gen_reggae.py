"""Reggae instrumental original CC0, 80 BPM, 16 compassos; sem samples ou vozes."""
from pathlib import Path
import numpy as np,wave
def write_wav(path,data,sr):
 data=np.asarray(data)
 with wave.open(str(path),"wb") as out:
  out.setnchannels(1 if data.ndim==1 else data.shape[1]);out.setsampwidth(2);out.setframerate(sr);out.writeframes((np.clip(data,-1,1)*32767).astype("<i2").tobytes())
root=Path(__file__).resolve().parents[1];sr=44100;bpm=80;beat=60/bpm;duration=beat*64
rng=np.random.default_rng(261026);mix=np.zeros((round(sr*duration),2),np.float64)
def add(sig,start,gain=1,pan=0):
 at=round(start*sr)%len(mix);values=sig*gain
 for side,g in enumerate([np.sqrt((1-pan)/2),np.sqrt((1+pan)/2)]):
  for offset in [0,len(mix)]:
   begin=max(0,offset-at);end=min(len(values),len(mix)+offset-at)
   if end>begin:mix[(at+begin-offset):(at+end-offset),side]+=values[begin:end]*g
freq=lambda note:440*2**((note-69)/12)
def tone(note,length,kind='bass'):
 t=np.arange(round(sr*length))/sr;f=freq(note)
 if kind=='bass':x=np.sin(2*np.pi*f*t)+.16*np.sin(4*np.pi*f*t);env=(1-np.exp(-t*90))*np.exp(-t*4.0)
 elif kind=='guitar':x=sum(np.sin(2*np.pi*f*j*t+rng.uniform(-.1,.1))/j**1.6 for j in range(1,8));env=(1-np.exp(-t*180))*np.exp(-t*20)
 else:x=np.sin(2*np.pi*f*t)+.16*np.sin(6*np.pi*f*t);env=(1-np.exp(-t*12))*np.exp(-t*1.2)
 return x*env*np.clip((length-t)*35,0,1)
def drum(kind):
 t=np.arange(round(sr*.28))/sr;noise=rng.normal(0,1,len(t))
 if kind=='kick':return .8*np.sin(2*np.pi*(48*t+6*(1-np.exp(-t*30))))*np.exp(-t*20)
 if kind=='rim':return (.4*noise+.6*np.sin(2*np.pi*1850*t))*np.exp(-t*95)
 return (noise-np.roll(noise,1))*.2*np.exp(-t*65)
chords=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]]
for bar in range(16):
 chord=chords[bar%4];base=[33,29,36,31][bar%4]
 for i in range(4):
  start=(bar*4+i)*beat
  for note in chord:add(tone(note,.25,'guitar'),start+beat*.5,.075,-.25)
  add(drum('hat'),start,.07,.35);add(drum('hat'),start+beat*.5,.045,.35)
  if i in [0,2]:add(drum('kick'),start,.28)
  if i in [1,3]:add(drum('rim'),start,.11,-.1)
 for when,n in [(0,base),(.75,base),(1.5,base+7),(2.5,base+12),(3.25,base+7)]:add(tone(n,.40),bar*4*beat+when*beat,.27)
 if bar%2==0:
  for j,n in enumerate([chord[2]+12,chord[1]+12,chord[0]+12]):add(tone(n,.70,'organ'),(bar*4+j+1)*beat,.025,.3)
# Delay circular discreto: início/fim musicalmente contínuos, com headroom real.
mix+=np.roll(mix,round(beat*.75*sr),axis=0)*.13
mix=np.tanh(mix*1.15);mix*=.55/max(.55,np.abs(mix).max())
write_wav(root/'assets/audio/reggae_praia.wav',mix,sr)
# Folhas com envelope suave e espectro filtrado, localizadas nas árvores.
noise=rng.normal(0,1,sr*4);smooth=np.convolve(noise,np.ones(17)/17,mode='same');t=np.arange(len(noise))/sr
leaves=smooth*(np.sin(np.pi*t/4)**2)*.18
write_wav(root/'assets/audio/leaves_soft.wav',leaves,sr)
print('REGGAE_OK',duration,'seconds peak',np.abs(mix).max())
