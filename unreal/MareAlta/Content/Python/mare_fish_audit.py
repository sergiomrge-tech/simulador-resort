"""Inspection of fish assets before restoring underwater movement."""
import json
from collections import Counter
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
def inspect():
 data=ROOT/'Content/Data'; world=json.loads((data/'world.json').read_text(encoding='utf-8-sig'))
 mapping=json.loads((data/'imported_meshes.json').read_text(encoding='utf-8-sig'));aliases=json.loads((data/'model_aliases.json').read_text(encoding='utf-8-sig'))
 rows=[r for r in world['instances'] if r['name'] in ('Body','Tail') and r['transform']['position'][2]<-40]
 out=[]
 for i in sorted({r['mesh_index'] for r in rows}):
  key=f'World_{i:04d}';path=mapping[aliases.get(key,key)];mesh=unreal.load_asset(path);b=mesh.get_bounds()
  matches=[r for r in rows if r['mesh_index']==i];out.append({'index':i,'name':matches[0]['name'],'mesh':path,'count':len(matches),'extent':str(b.box_extent),'origin':str(b.origin),'first':matches[0]['transform']})
 return out
