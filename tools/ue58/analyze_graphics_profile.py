"""Summarize native UE CSV profiler output; durations are milliseconds unless memory fields."""
import csv,json,statistics,sys
from pathlib import Path
root=Path(sys.argv[1]);r=json.loads((root/'graphics-qa.json').read_text(encoding='utf-8-sig'));out=[]
for c in r['captures']:
 rows=list(csv.reader(Path(c['csv']).open(encoding='utf-8-sig')));h=rows[0];metrics={}
 for n in ['FrameTime','GPUTime','GameThreadTime','RenderThreadTime','RHIThreadTime','GPUMem/LocalUsedMB','MemoryFreeMB','GPU/NaniteVisBuffer','GPU/NaniteBasePass','GPU/LumenSceneUpdate','GPU/LumenScreenProbeGather','GPU/LumenReflections','GPU/ShadowDepths']:
  if n not in h:continue
  i=h.index(n);v=[]
  for row in rows[1:]:
   try:v.append(float(row[i]))
   except (ValueError,IndexError):pass
  if v:metrics[n]={'mean':statistics.mean(v),'p95':sorted(v)[int((len(v)-1)*.95)],'samples':len(v)}
 out.append({**c,'metrics':metrics});print(c['variant'],c['screen_percentage'],round(1000/metrics['FrameTime']['mean'],1),'FPS',round(metrics['FrameTime']['p95'],3),'ms P95',round(metrics['GPUTime']['mean'],3),'ms GPU')
(root/'summary.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
