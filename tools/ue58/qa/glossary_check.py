"""Glossário obrigatório dos 12 idiomas, sem Unreal. Saída não zero reprova o lint."""
import argparse
import json
import re
import tempfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
GLOSSARY=ROOT/'docs/ue58/GLOSSARIO.json'
LOCALE=ROOT/'unreal/MareAlta/Content/Localization/Mare'


def check(glossary=GLOSSARY,locale=LOCALE):
    errors=[]
    def fail(file,key,msg):errors.append({'arquivo':file,'campo':key,'problema':msg})
    try:g=json.loads(Path(glossary).read_text());source=json.loads((Path(locale)/'source.json').read_text())
    except (OSError,ValueError) as e:return [{'arquivo':str(glossary),'campo':'/','problema':str(e)}]
    for lang in g['languages']:
        p=Path(locale)/f'{lang}.json'
        try:catalog=json.loads(p.read_text())
        except (OSError,ValueError) as e:fail(p.name,'/',str(e));continue
        for section in ['strings','loctext']:
            src={k:k for k in source['strings']} if section=='strings' else source['loctext']
            values=catalog.get(section,{})
            if set(src)!=set(values):fail(p.name,section,'chaves diferentes do source.json')
            for key,pt in src.items():
                value=values.get(key)
                if not isinstance(value,str) or not value:fail(p.name,key,'tradução ausente');continue
                if Counter(re.findall(r'\{\d+\}|<br>|R\$',pt))!=Counter(re.findall(r'\{\d+\}|<br>|R\$',value)):fail(p.name,key,'marcador, <br> ou R$ alterado')
                # Espaços de montagem são parte da chave (sem normalizar o conteúdo).
                if re.match(r'^\s*',pt)[0]!=re.match(r'^\s*',value)[0] or re.search(r'\s*$',pt)[0]!=re.search(r'\s*$',value)[0]:fail(p.name,key,'espaço inicial/final alterado')
                for term in g['terms']:
                    if pt not in term.get('source_exceptions',[]) and re.search(term['source_pattern'],pt) and not re.search(term['accepted_patterns'][lang],value):
                        fail(p.name,key,'glossário '+term['term']+': obrigatório '+term['forms'][lang])
    return errors


def main():
    p=argparse.ArgumentParser();p.add_argument('--json',action='store_true');p.add_argument('--self-test',action='store_true');a=p.parse_args()
    if a.self_test:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);g=json.loads(GLOSSARY.read_text())
            (root/'g.json').write_text(json.dumps(g))
            source={'loctext':{},'strings':['Maré Alta R$ {0}<br>']}
            (root/'source.json').write_text(json.dumps(source))
            for lang in g['languages']:(root/f'{lang}.json').write_text(json.dumps({'loctext':{},'strings':{'Maré Alta R$ {0}<br>':'Maré Alta R$ {0}<br>'}}))
            assert not check(root/'g.json',root)
            for value in ['High Tide R$ {0}<br>','Maré Alta $ {0}<br>','Maré Alta R$ {1}<br>','Maré Alta R$ {0}']:
                (root/'en.json').write_text(json.dumps({'loctext':{},'strings':{'Maré Alta R$ {0}<br>':value}}))
                assert check(root/'g.json',root),value
            (root/'en.json').write_text('{}');assert check(root/'g.json',root)
        print('PASS: nome incorreto, moeda, marcador, quebra e catálogo ausente são reprovados')
        return False
    errors=check()
    if a.json:print(json.dumps(errors,ensure_ascii=False,indent=2))
    else:
        for e in errors:print(e['arquivo'],repr(e['campo']),e['problema'])
        print(f'{"FAIL" if errors else "PASS"}: glossário, 12 idiomas, {len(errors)} erro(s)')
    return bool(errors)
if __name__=='__main__':raise SystemExit(main())
