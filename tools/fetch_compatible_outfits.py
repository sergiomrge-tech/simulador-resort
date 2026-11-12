"""Download official Quaternius CC0 outfits with the existing character rig."""
from pathlib import Path
import subprocess, json, re, zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art/vendor/quaternius_outfits'
OUT.mkdir(parents=True,exist_ok=True)
BASE='https://quaternius.itch.io/modular-character-outfits-fantasy'
def call(url,data=None):
    args=['curl.exe','-sSL','--fail','--max-time','120','-b',str(OUT/'cookies.txt'),'-c',str(OUT/'cookies.txt'),url]
    if data: args+=['--data-urlencode','csrf_token='+data]
    return subprocess.check_output(args)
def token(page): return re.search(r'csrf_token" value="([^"]+)',page.decode()).group(1)
archive=OUT/'standard.zip'
if not zipfile.is_zipfile(archive):
    page=call(BASE)
    download=json.loads(call(BASE+'/download_url',token(page)))['url']
    page=call(download)
    upload=re.search(r'data-upload_id="(\d+)"',page.decode()).group(1)
    url=json.loads(call(BASE+'/file/'+upload+'?source=view_game&as_props=1&after_download_lightbox=true',token(page)))['url']
    subprocess.run(['curl.exe','-L','--fail','--max-time','180','-o',str(archive),url],check=True)
with zipfile.ZipFile(archive) as z:
    selected=[n for n in z.namelist() if ('peasant' in n.lower() or 'texture' in n.lower()) and ('gltf' in n.lower() or n.lower().endswith('.png'))]
    for n in selected:
        target=(OUT/n).resolve()
        if not target.is_relative_to(OUT.resolve()):raise ValueError(n)
        z.extract(n,OUT)
    print('\n'.join(selected[:60]))

