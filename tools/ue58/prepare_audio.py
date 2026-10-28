"""Convert the licensed/original existing game audio into portable PCM sources for UE."""
import sys,json
from pathlib import Path
sys.path.insert(0,'D:/CodexTemp/audio-pylibs')
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'unreal/MareAlta/SourceArt/Audio'
OUT.mkdir(parents=True,exist_ok=True)
names=['reggae_praia','ocean_loop','wind_loop','rain_loop','crickets_loop','leaves_soft',
       'bird1','bird2','seagull1','seagull2','dog','bell','door','glass','clean','click',
       'coin','swoosh','kiosk_pickup','kiosk_fridge','kiosk_cash','thunder','whale_splash']
names += [f'footstep_{surface}_{i:03}' for surface in ['wood','concrete','carpet'] for i in range(5)]
report=[]
for name in names:
    source=next(p for p in (ROOT/'assets/audio').glob(name+'.*') if p.suffix in ('.wav','.ogg'))
    data,rate=sf.read(source,always_2d=True,dtype='float32')
    if name!='reggae_praia':data=data.mean(axis=1,keepdims=True)
    peak=float(np.max(np.abs(data)))
    if peak>.97:data*=.97/peak
    # Remove DC and a click at the seam without changing the composition or adding voices.
    data-=data.mean(axis=0)
    fade=min(len(data)//10,int(rate*.006))
    data[:fade]*=np.linspace(0,1,fade)[:,None];data[-fade:]*=np.linspace(1,0,fade)[:,None]
    sf.write(OUT/(name+'.wav'),np.clip(data,-.98,.98),rate,subtype='PCM_16')
    report.append(dict(id=name,seconds=len(data)/rate,channels=data.shape[1],peak=float(abs(data).max()),
                       rms=float(np.sqrt(np.mean(data*data))),source=source.relative_to(ROOT).as_posix()))
rng=np.random.default_rng(58)
for name,seconds in [('swim_splash',.65),('swim_stroke',.45),('underwater_loop',8.)]:
    rate=32000;t=np.arange(int(rate*seconds))/rate
    noise=rng.normal(0,1,len(t));spectrum=np.fft.rfft(noise);freq=np.fft.rfftfreq(len(t),1/rate)
    spectrum*=np.exp(-(freq/(550 if name=='underwater_loop' else 2000))**2)
    data=np.fft.irfft(spectrum,n=len(t))
    if name!='underwater_loop':data*=np.sin(np.pi*t/seconds)**2*np.exp(-t*2)
    else:
        for moment in np.arange(.4,seconds,.65):
            age=t-moment;data+=np.where(age>=0,np.sin(2*np.pi*(170*age+100*age**2))*np.exp(-np.maximum(age,0)*18),0)*.07
    data=data/max(abs(data).max(),1e-6)*(.18 if name=='underwater_loop' else .6)
    fade=320;data[:fade]*=np.linspace(0,1,fade);data[-fade:]*=np.linspace(1,0,fade)
    sf.write(OUT/(name+'.wav'),data,rate,subtype='PCM_16')
    report.append(dict(id=name,seconds=seconds,channels=1,peak=float(abs(data).max()),rms=float(np.sqrt(np.mean(data*data))),source='original procedural synthesis: tools/ue58/prepare_audio.py'))
(OUT/'catalog.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'sounds':len(report),'seconds':sum(x['seconds'] for x in report),'output':str(OUT)}))
