"""Confere os glifos CJK dos catálogos contra os recortes carregados pelo MareNotebookStyle.
Uso: python tools/ue58/qa/font_coverage_check.py [--json]
Requer fontTools (mesma dependência do i18n_fonts.py). Não abre Unreal nem prova a seleção Slate de fallback.
"""
import argparse
import hashlib
import json
from pathlib import Path
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[3]
FONTS=ROOT/'unreal/MareAlta/Content/UI/Fonts'
LOC=ROOT/'unreal/MareAlta/Content/Localization/Mare'


def family(lang,point):
    # Intervalos de MareNotebookStyle.h:40–45; Hangul/Kana usam o fallback próprio.
    if 0x1100<=point<=0x11ff or 0x3130<=point<=0x318f or 0xac00<=point<=0xd7af:return 'NotoSansKR'
    if 0x3040<=point<=0x30ff or 0x31f0<=point<=0x31ff:return 'NotoSansJP'
    if 0x2e80<=point<=0x9fff or 0xf900<=point<=0xfaff or 0xff00<=point<=0xffef:return 'NotoSansJP' if lang=='ja' else 'NotoSansSC'
    return None


def check():
    names=['NotoSansSC','NotoSansJP','NotoSansKR'];cmap={};used={n:set() for n in names};missing=[];hashes={}
    for n in names:
        path=FONTS/f'{n}-Mare.ttf'
        with TTFont(path) as f:cmap[n]=set(f.getBestCmap())
        hashes[n]=hashlib.sha256(path.read_bytes()).hexdigest()
    for p in sorted(LOC.glob('*.json')):
        if p.stem=='source' or p.stem.startswith('todo_'):continue
        d=json.loads(p.read_text())
        for section in ['loctext','strings']:
            for key,text in d[section].items():
                for char in set(text):
                    n=family(p.stem,ord(char))
                    if n:
                        used[n].add(ord(char))
                        if ord(char) not in cmap[n]:missing.append({'language':p.stem,'section':section,'key':key,'font':n,'character':char,'codepoint':f'U+{ord(char):04X}'})
    return {'scope':'Cobertura dos intervalos CJK segundo MareNotebookStyle.h; não é renderização Slate ou prova de todas as fontes do motor.','font_sha256':hashes,'required_codepoints':{n:len(v) for n,v in used.items()},'missing':missing}


def main():
    p=argparse.ArgumentParser();p.add_argument('--json',action='store_true');a=p.parse_args();result=check()
    if a.json:print(json.dumps(result,ensure_ascii=False,indent=1))
    else:print(f'{"FAIL" if result["missing"] else "PASS"}: fontes CJK, {len(result["missing"])} glifos ausentes; {result["required_codepoints"]}')
    return bool(result['missing'])
if __name__=='__main__':raise SystemExit(main())
