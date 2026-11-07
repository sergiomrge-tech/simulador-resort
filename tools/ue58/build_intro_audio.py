"""Original, quiet mono engine and pneumatic brake Foley; no voices or recordings."""
from pathlib import Path
import sys,json
sys.path.insert(0,'D:/CodexTemp/audio-pylibs')
import numpy as np
import soundfile as sf
OUT=Path(__file__).resolve().parents[2]/'unreal/MareAlta/SourceArt/Audio'
rate=32000;rng=np.random.default_rng(580329)
def write(name,x):
    x-=x.mean();fade=min(len(x)//10,rate//25)
    x[:fade]*=np.linspace(0,1,fade);x[-fade:]*=np.linspace(1,0,fade)
    x*=.35/max(abs(x).max(),1e-8);sf.write(OUT/(name+'.wav'),x,rate,subtype='PCM_16')
t=np.arange(rate*28)/rate
rpm=np.where(t<8,36-1.5*t,np.where(t<16,24,24+np.minimum(t-16,7)*3))
phase=2*np.pi*np.cumsum(rpm)/rate
noise=rng.normal(size=len(t));spec=np.fft.rfft(noise);freq=np.fft.rfftfreq(len(t),1/rate)
low=np.fft.irfft(spec/(1+(freq/220)**4),n=len(t))
engine=(.38*np.sin(phase)+.2*np.sin(phase*2)+.10*np.sin(phase*4)+.09*low)*(1+.12*np.sin(phase*.5))
write('bus_engine',engine)
t=np.arange(int(rate*1.4))/rate
noise=rng.normal(size=len(t));spec=np.fft.rfft(noise);freq=np.fft.rfftfreq(len(t),1/rate)
hiss=np.fft.irfft(spec*(freq/(freq+500))/(1+(freq/4500)**4),n=len(t))*np.exp(-t*3)
write('bus_brake',hiss+.07*np.sin(2*np.pi*180*t)*np.exp(-t*9))
print(json.dumps({'original_sounds':['bus_engine','bus_brake'],'rate':rate,'channels':1}))
