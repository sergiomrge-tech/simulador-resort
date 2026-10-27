from pathlib import Path
import re,random
out=Path('assets/ui/products');out.mkdir(parents=True,exist_ok=True)
s=Path('scripts/economy.gd').read_text(encoding='utf-8').split('const DISHES: = {')[1].split('\n}')[0]
for name in re.findall(r'^\t"([\w_]+)"',s,re.M):
 parts=['<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96"><rect x="1" y="1" width="94" height="94" rx="16" fill="#e9e5d7"/>']
 if name=='coco_gelado':parts+=['<path d="M48 24 C14 23 16 80 47 82 C81 83 84 24 48 24" fill="#8ea34d" stroke="#637531" stroke-width="3"/><ellipse cx="48" cy="28" rx="20" ry="7" fill="#e9ead0"/><path d="M51 29L63 9" stroke="#86644c" stroke-width="4"/>']
 elif name.startswith('sorvete'):
  col='#dc9c99' if name.endswith('morango') else '#79543c'
  parts += ['<path d="M22 48H74L65 81H31Z" fill="#f8f3e5" stroke="#c8bfa9" stroke-width="2"/>',f'<circle cx="48" cy="39" r="23" fill="{col}"/>','<path d="M71 38L79 15" stroke="#876d4a" stroke-width="5"/>']
 elif name in ['suco','caipirinha','batida']:
  col={'suco':'#e3a436','caipirinha':'#c7d17b','batida':'#eee5c7'}[name]
  parts += [f'<path d="M25 27H71L64 81H32Z" fill="{col}" stroke="#93aba9" stroke-width="3"/>','<path d="M36 32L40 72" stroke="white" stroke-width="4" opacity=".6"/><path d="M55 48L66 10" stroke="#795940" stroke-width="3"/><circle cx="25" cy="27" r="12" fill="#e4d989" stroke="#b1b45f" stroke-width="3"/>']
 else:
  parts += ['<ellipse cx="48" cy="56" rx="39" ry="26" fill="#faf8ef" stroke="#c1bdaf" stroke-width="3"/>']
  if name=='batata_frita':
   rng=random.Random(17)
   for i in range(22):parts += [f'<rect x="{rng.randrange(25,65)}" y="{rng.randrange(33,64)}" width="5" height="20" rx="2" fill="#d6a34d" transform="rotate({rng.randrange(-35,35)} 48 50)"/>']
  elif name in ['porcao_peixe','petiscos']:
   for x in [27,44,61]:parts += [f'<ellipse cx="{x}" cy="52" rx="9" ry="20" fill="#c08f42" transform="rotate(22 {x} 52)"/>']
   parts+=['<path d="M66 66L78 54L81 70Z" fill="#b4bf56"/>']
  elif name=='acai':parts+=['<ellipse cx="48" cy="52" rx="30" ry="18" fill="#65415e"/><path d="M29 45L65 57" stroke="#e5c770" stroke-width="7"/>']
  else:parts+=['<path d="M24 53Q48 19 73 53Q49 76 24 53" fill="#d4ab66" stroke="#b38b4b" stroke-width="2"/>']
 parts+=['</svg>'];(out/(name+'.svg')).write_text(''.join(parts),encoding='utf-8')
