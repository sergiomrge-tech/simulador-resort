"""Short original quiet kiosk sounds; no voices or external samples."""
from pathlib import Path
import wave, math, random
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/audio';SR=32000
random.seed(23)
for name,duration in [('fridge',.22),('pickup',.18),('prepare',.48),('ready',.35),('cash',.32)]:
    samples=[];low=0
    for i in range(int(duration*SR)):
        t=i/SR;low=.87*low+.13*random.uniform(-1,1)
        env=math.sin(math.pi*min(1,t/.012)/2)*math.exp(-t*(13 if name!='prepare' else 5))
        if name=='fridge':value=(math.sin(2*math.pi*90*t)*.35+low*.7)*env
        elif name=='pickup':value=(math.sin(2*math.pi*260*t)*.16+low*.5)*env
        elif name=='prepare':value=low*.6*env
        else:
            freq=660 if name=='ready' else 520
            value=(math.sin(2*math.pi*freq*t)*.16+math.sin(2*math.pi*freq*1.5*t)*.08)*env
        samples.append(int(max(-1,min(1,value))*.42*32767))
    import struct
    with wave.open(str(OUT/f'kiosk_{name}.wav'),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR)
        f.writeframes(struct.pack('<'+'h'*len(samples),*samples))
    print(name,len(samples)/SR)
