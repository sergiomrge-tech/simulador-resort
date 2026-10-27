"""Detect byte-identical geometry/material payloads independent of generated node names.
No source files are removed. Aliases allow Unreal to reuse a single native asset.
"""
import argparse,hashlib,json,struct
from pathlib import Path

def semantic_hash(path):
    raw=path.read_bytes()
    if len(raw)<20 or raw[:4]!=b'glTF' or struct.unpack_from('<I',raw,8)[0]!=len(raw):return None
    pos=12;parts=[]
    def clean(v):
        if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in ('name','generator')}
        if isinstance(v,list):return [clean(x) for x in v]
        return v
    while pos<len(raw):
        size,kind=struct.unpack_from('<II',raw,pos);pos+=8;data=raw[pos:pos+size];pos+=size
        if kind==0x4e4f534a:data=json.dumps(clean(json.loads(data)),sort_keys=True,separators=(',',':')).encode()
        parts.append(data)
    digest=hashlib.sha256()
    for part in parts:digest.update(part)
    return digest.hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',default=str(Path(__file__).resolve().parents[2]/'unreal'/'MareAlta'));args=parser.parse_args()
    root=Path(args.project);hashes={};aliases={};sizes={}
    for p in sorted((root/'SourceArt'/'World').glob('World_*.glb')):
        key=semantic_hash(p)
        if key is None:continue
        canonical=hashes.setdefault(key,p.stem);aliases[p.stem]=canonical;sizes[p.stem]=p.stat().st_size
    (root/'Content'/'Data'/'model_aliases.json').write_text(json.dumps(aliases,indent=2),encoding='utf-8')
    report={'exported':len(aliases),'unique':len(hashes),'bytes_before':sum(sizes.values()),'bytes_after':sum(sizes[k] for k in hashes.values())}
    (root/'Content'/'Data'/'deduplication.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
