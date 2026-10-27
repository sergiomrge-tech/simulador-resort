"""Prepare portable glTF with content-addressed PBR images and reusable material names.
Raw GLB exports remain untouched; only generated Models/Textures are written.
"""
import hashlib,json,struct
from pathlib import Path
from deduplicate_models import main as deduplicate

def chunks(raw):
    pos=12;result={}
    while pos<len(raw):
        size,kind=struct.unpack_from('<II',raw,pos);pos+=8;result[kind]=raw[pos:pos+size];pos+=size
    return json.loads(result[0x4e4f534a]),result.get(0x004e4942,b'')

def normalize(root,name):
    doc,binary=chunks((root/'SourceArt'/'World'/(name+'.glb')).read_bytes())
    views=doc.get('bufferViews',[]);image_views=set();image_hashes={}
    for index,img in enumerate(doc.get('images',[])):
        if 'bufferView' not in img:continue
        vi=img.pop('bufferView');image_views.add(vi);view=views[vi];start=view.get('byteOffset',0);data=binary[start:start+view['byteLength']]
        digest=hashlib.sha256(data).hexdigest();ext='.jpg' if img.get('mimeType')=='image/jpeg' else '.png'
        filename='T_'+digest+ext;path=root/'SourceArt'/'Textures'/filename
        if not path.exists():path.write_bytes(data)
        img['uri']='../Textures/'+filename;img['name']='T_'+digest[:24];image_hashes[index]=digest
    rebuilt=[];mapping={};new_binary=bytearray()
    for old,view in enumerate(views):
        if old in image_views:continue
        start=view.get('byteOffset',0);payload=binary[start:start+view['byteLength']]
        while len(new_binary)%4:new_binary.append(0)
        view['byteOffset']=len(new_binary);view['buffer']=0;new_binary.extend(payload);mapping[old]=len(rebuilt);rebuilt.append(view)
    for accessor in doc.get('accessors',[]):
        if 'bufferView' in accessor:accessor['bufferView']=mapping[accessor['bufferView']]
        for entry in accessor.get('sparse',{}).values():
            if isinstance(entry,dict) and 'bufferView' in entry:entry['bufferView']=mapping[entry['bufferView']]
    doc['bufferViews']=rebuilt
    doc['buffers']=[{'uri':name+'.bin','byteLength':len(new_binary)}]
    textures=doc.get('textures',[])
    for texture in textures:
        if texture.get('source') in image_hashes:texture['name']='T_'+image_hashes[texture['source']][:24]
    def material_signature(v):
        if isinstance(v,list):return [material_signature(x) for x in v]
        if not isinstance(v,dict):return v
        out={k:material_signature(x) for k,x in v.items() if k!='name'}
        if 'index' in v and isinstance(v['index'],int) and v['index']<len(textures):
            tex=textures[v['index']];out['index']=image_hashes.get(tex.get('source'),tex.get('source'))
        return out
    for material in doc.get('materials',[]):
        key=json.dumps(material_signature(material),sort_keys=True,separators=(',',':')).encode()
        material['name']='MA_'+hashlib.sha256(key).hexdigest()[:24]
    folder=root/'SourceArt'/'Models'
    (folder/(name+'.bin')).write_bytes(new_binary)
    (folder/(name+'.gltf')).write_text(json.dumps(doc,separators=(',',':')),encoding='utf-8')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--project',default=str(Path(__file__).resolve().parents[2]/'unreal'/'MareAlta'));args=p.parse_args();root=Path(args.project)
    aliases=json.loads((root/'Content'/'Data'/'model_aliases.json').read_text())
    (root/'SourceArt'/'Models').mkdir(parents=True,exist_ok=True);(root/'SourceArt'/'Textures').mkdir(parents=True,exist_ok=True)
    names=sorted(set(aliases.values()))
    for i,name in enumerate(names):
        normalize(root,name)
        if i%100==0:print('PREPARED',i,len(names),flush=True)
    files=[p for d in ('Models','Textures') for p in (root/'SourceArt'/d).iterdir()]
    print(json.dumps({'models':len(names),'files':len(files),'bytes':sum(p.stat().st_size for p in files)}))
