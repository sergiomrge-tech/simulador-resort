"""Valida artefatos do pacote 4, sem editor e sem alterar dados."""
import csv,hashlib,json,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
total=0
for folder in ['baseline','results','demo']:
 p=HERE/'pacote4'/folder;conf=json.loads((p/'configuracao.json').read_text());summary=json.loads((p/'summary.json').read_text())
 assert conf['sementes']==list(range(30))
 for path,digest in json.loads((p/'inputs_sha256.json').read_text()).items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
 for scenario in ['atual','proposto']:
  for profile in ['casual','medio','dedicado']:
   q=summary[scenario][profile];assert q['sementes']==30
   seeds=list(csv.DictReader((p/f'{scenario}_{profile}_sementes.csv').open()));assert len(seeds)==30;total+=30
   if folder=='results':assert q['marcos']['divida_quitada']['concluidos']==30 and q['censurados_divida']==0
   rows=list(csv.DictReader((p/f'{scenario}_{profile}_diario_seed0.csv').open()));prev=0
   for row in rows:
    paid=float(row['divida_paga']);assert prev<=paid<=1000000;prev=paid
    assert abs(paid+float(row['divida_saldo'])-1000000)<.001
    assert abs(float(row['caixa_inicial'])+float(row['renda_total'])-float(row['despesas_total'])-float(row['caixa']))<.04
   if folder=='demo':
    assert all(not s['divida_quitada'] for s in seeds)
    assert all(float(s['divida_paga'])<=250000 for s in seeds)
    assert all('grand_hotel' not in row['compras'].split('; ') and 'salao_jogos' not in row['compras'].split('; ') for row in rows)
assert total==540
loc=ROOT/'unreal/MareAlta/Content/Localization/Mare';src=json.loads((loc/'source.json').read_text())
for lang in ['en','es','de','fr','zh-Hans','ja','ru','ko','it','pl','nl','pt-PT']:
 tr=json.loads((loc/(lang+'.json')).read_text())
 for group,items in [('strings',[(s,s) for s in src['strings']]),('loctext',src['loctext'].items())]:
  for key,source in items:
   target=tr[group][key];assert target,(lang,key)
   assert Counter(re.findall(r'\{\d+\}|<br>',source))==Counter(re.findall(r'\{\d+\}|<br>',target)),(lang,key)
   assert source.count('R$')==target.count('R$'),(lang,key)
assert not list(loc.glob('todo_*.json'))
spec=json.loads((ROOT/'docs/steam/conquistas.json').read_text());a=spec['achievements'];assert len(a)==36 and len({x['id'] for x in a})==36
assert sum(x['field_status']=='proposto neste pacote' for x in a)==5
defs=json.loads((ROOT/'unreal/MareAlta/Content/Data/definitions.json').read_text());tours=json.loads((ROOT/'unreal/MareAlta/Content/Data/customization.json').read_text())['operations']['tours']
for x in a:
 assert all(x[k][lang] for k in ['name','description'] for lang in ['pt-BR','en'])
 c=x['condition'];path=c['path']
 if path.startswith('/unlocked/'):assert path.split('/')[-1] in defs['expansions']
 if path.startswith('/prog/ch/'):assert path.split('/')[-1] in {c['id'] for c in defs['chapters']}
 if c['op']=='any_tour':assert c['value']['id'] in {t['id'] for t in tours}
 if c['op']=='all_businesses':assert set(c['value']['ids'])==set(defs['businesses'])
assert len(spec['rich_presence'])==10
print('PASS: 540 trajetórias, hashes, caixa/dívida, demo, 12 idiomas e 36 conquistas/10 presenças.')
