"""Validate recordings of the actual UE master output, including mute and pause."""
import sys,json
from pathlib import Path
sys.path.insert(0,'D:/CodexTemp/audio-pylibs')
import numpy as np
import soundfile as sf
root=Path(sys.argv[1])
result={}
for name in ['audible','muted','paused']:
    data,rate=sf.read(root/f'mix_{name}.wav',always_2d=True)
    if len(data)<rate:raise SystemExit('Recording too short: '+name)
    # UE records the master submix before its output gain. Allow source/reverb
    # buffers to settle, then require sustained silence; output mute also gates
    # the final master gain, which the runtime regression checks separately.
    body=data[int(rate*(1.0 if name=='muted' else .35)):-int(rate*.1)]
    rms=float(np.sqrt(np.mean(body*body)));peak=float(abs(body).max())
    result[name]=dict(seconds=len(data)/rate,rms=rms,peak=peak,
                      pass_=bool(rms>.0002 and peak<.98) if name=='audible' else bool(rms<.0001))
passed=all(row['pass_'] for row in result.values())
result['passed']=passed
(root/'audio-mix-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
if not passed:raise SystemExit(1)
