"""Original soft distant-water impact; no samples or voices."""
from pathlib import Path
import random,math,wave,struct
r=random.Random(173);rate=22050;samples=[];low=0.0
for i in range(rate*3):
 t=i/rate;white=r.uniform(-1,1);low=.94*low+.06*white
 envelope=(1-math.exp(-t*24))*math.exp(-t*1.8)
 value=(low*1.8+white*.08)*envelope*.7
 samples.append(struct.pack('<h',int(max(-1,min(1,value))*32767)))
path=Path(__file__).resolve().parents[1]/'assets/audio/whale_splash.wav'
with wave.open(str(path),'wb') as f:
 f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(b''.join(samples))
